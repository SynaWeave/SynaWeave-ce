"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  detect and sync local Bun and Python tooling state from watched dependency files

- Later Extension Points:
    --> add narrower watched-file groups only when more local toolchains
    --> become durable repo baselines

- Role:
    --> compares watched dependency file hashes against a git-local stamp under `.git`
    --> supports manual and hook-safe sync modes with stable exit codes for operators and hooks

- Exports:
    --> `main()`

- Consumed By:
    --> local operators and hooks checking whether environment sync is required
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

STAMP_VERSION = 1
EXIT_OK = 0
EXIT_SYNC_NEEDED = 1
EXIT_USAGE_ERROR = 2
EXIT_SYNC_FAILED = 3

STAMP_RELATIVE_PATH = Path("synawave") / "environment-sync.json"
JS_SYNC_COMMAND = ("bun", "install", "--frozen-lockfile")
PYTHON_SYNC_COMMAND = (
    "python3",
    "-m",
    "pip",
    "install",
    "--user",
    "--break-system-packages",
    "-r",
    "requirements-dev.txt",
)
LOCAL_VENV_PYTHON = Path(".venv") / "bin" / "python3"
REQUIRED_WATCH_FILES = ("package.json", "requirements-dev.txt")
OPTIONAL_WATCH_FILES = ("bun.lock",)
JS_WATCH_FILES = ("package.json", "bun.lock")
PYTHON_WATCH_FILES = ("requirements-dev.txt",)


@dataclass(frozen=True)
class SyncPlan:
    js_changed: tuple[str, ...]
    python_changed: tuple[str, ...]
    stamp_issue: str | None

    @property
    def sync_needed(self) -> bool:
        return bool(self.js_changed or self.python_changed or self.stamp_issue)


@dataclass(frozen=True)
class PythonSyncDecision:
    command: tuple[str, ...]
    source: str


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check or sync the canonical local environment")
    parser.add_argument(
        "command",
        choices=("check", "sync"),
        help="Whether to report sync status or perform the required sync commands",
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    parser.add_argument(
        "--mode",
        choices=("manual", "hook"),
        default="manual",
        help="Sync behavior for direct operator use or branch-change hooks",
    )
    return parser.parse_args(argv)


def _resolve_git_dir(repo_root: Path) -> Path:
    git_path = repo_root / ".git"
    if git_path.is_dir():
        return git_path

    if git_path.is_file():
        content = git_path.read_text(encoding="utf-8").strip()
        prefix = "gitdir: "
        if content.startswith(prefix):
            return (repo_root / content[len(prefix) :]).resolve()

    raise ValueError(f"missing usable git directory at {git_path}")


def _stamp_path(repo_root: Path) -> Path:
    return _resolve_git_dir(repo_root) / STAMP_RELATIVE_PATH


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _collect_current_hashes(repo_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative_path in REQUIRED_WATCH_FILES:
        file_path = repo_root / relative_path
        if not file_path.is_file():
            raise ValueError(f"missing required watched file: {relative_path}")
        hashes[relative_path] = _hash_file(file_path)

    for relative_path in OPTIONAL_WATCH_FILES:
        file_path = repo_root / relative_path
        if file_path.is_file():
            hashes[relative_path] = _hash_file(file_path)

    return hashes


def _read_stamp(repo_root: Path) -> tuple[dict[str, str] | None, str | None]:
    stamp_path = _stamp_path(repo_root)
    if not stamp_path.is_file():
        return None, "stamp missing"

    try:
        payload = json.loads(stamp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "stamp invalid"

    if payload.get("version") != STAMP_VERSION:
        return None, "stamp version mismatch"

    file_hashes = payload.get("files")
    if not isinstance(file_hashes, dict) or not all(
        isinstance(path, str) and isinstance(digest, str)
        for path, digest in file_hashes.items()
    ):
        return None, "stamp invalid"

    return file_hashes, None


def _build_sync_plan(repo_root: Path) -> tuple[SyncPlan, dict[str, str]]:
    current_hashes = _collect_current_hashes(repo_root)
    stamped_hashes, stamp_issue = _read_stamp(repo_root)
    stamped_hashes = stamped_hashes or {}

    js_changed = tuple(
        relative_path
        for relative_path in JS_WATCH_FILES
        if stamped_hashes.get(relative_path) != current_hashes.get(relative_path)
    )
    python_changed = tuple(
        relative_path
        for relative_path in PYTHON_WATCH_FILES
        if stamped_hashes.get(relative_path) != current_hashes.get(relative_path)
    )

    plan = SyncPlan(
        js_changed=js_changed,
        python_changed=python_changed,
        stamp_issue=stamp_issue,
    )
    return plan, current_hashes


def _write_stamp(repo_root: Path, file_hashes: dict[str, str]) -> None:
    stamp_path = _stamp_path(repo_root)
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(
        json.dumps({"version": STAMP_VERSION, "files": file_hashes}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _build_python_sync_command(python_executable: str | Path) -> tuple[str, ...]:
    return (str(python_executable), "-m", "pip", "install", "-r", "requirements-dev.txt")


def _local_python_sync_command(repo_root: Path) -> tuple[str, ...] | None:
    local_python = repo_root / LOCAL_VENV_PYTHON
    if local_python.is_file():
        return _build_python_sync_command(local_python)
    return None


def _resolve_python_sync(repo_root: Path) -> PythonSyncDecision:
    local_command = _local_python_sync_command(repo_root)
    if local_command is not None:
        return PythonSyncDecision(command=local_command, source="repo-owned .venv")

    return PythonSyncDecision(command=PYTHON_SYNC_COMMAND, source="system python")


def _describe_group(name: str, changed_files: tuple[str, ...]) -> str:
    return f"{name}: {', '.join(changed_files)}"


def _print_plan(plan: SyncPlan) -> None:
    if not plan.sync_needed:
        print("Environment sync not needed")
        return

    print("Environment sync needed")
    if plan.stamp_issue is not None:
        print(f"- stamp: {plan.stamp_issue}")
    if plan.js_changed:
        print(f"- {_describe_group('js', plan.js_changed)}")
    if plan.python_changed:
        print(f"- {_describe_group('python', plan.python_changed)}")


def _run_command(command: Sequence[str], repo_root: Path) -> int:
    print(f"$ {' '.join(command)}")
    result = subprocess.run(command, cwd=repo_root, check=False)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
    return result.returncode


def _run_sync(
    plan: SyncPlan,
    repo_root: Path,
    current_hashes: dict[str, str],
    *,
    mode: str,
) -> int:
    if not plan.sync_needed:
        print("Environment already synced")
        return EXIT_OK

    stamped_hashes, _ = _read_stamp(repo_root)
    synced_hashes = dict(stamped_hashes or {})

    if plan.js_changed and _run_command(JS_SYNC_COMMAND, repo_root) != 0:
        return EXIT_SYNC_FAILED

    if plan.js_changed:
        for relative_path in JS_WATCH_FILES:
            if relative_path in current_hashes:
                synced_hashes[relative_path] = current_hashes[relative_path]

    if plan.python_changed:
        python_sync = _resolve_python_sync(repo_root)
        if mode == "hook":
            print(f"Python dependency sync using {python_sync.source}")
        if _run_command(python_sync.command, repo_root) != 0:
            return EXIT_SYNC_FAILED
        for relative_path in PYTHON_WATCH_FILES:
            if relative_path in current_hashes:
                synced_hashes[relative_path] = current_hashes[relative_path]

    _write_stamp(repo_root, synced_hashes)
    print("Environment sync complete")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(args.root).resolve()

    try:
        plan, current_hashes = _build_sync_plan(repo_root)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return EXIT_USAGE_ERROR

    if args.command == "check":
        _print_plan(plan)
        return EXIT_SYNC_NEEDED if plan.sync_needed else EXIT_OK

    return _run_sync(plan, repo_root, current_hashes, mode=args.mode)


if __name__ == "__main__":
    sys.exit(main())
