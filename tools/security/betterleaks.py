"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run Betterleaks across local repo surfaces before code leaves the workstation or fast CI

- Later Extension Points:
    --> add more Betterleaks scan modes only when new repo-owned release or packaging paths appear

- Role:
    --> scans staged files for fast pre-commit leak blocking
    --> scans the working tree and stripped extension artifact before push or fast CI feedback

- Exports:
    --> `run_betterleaks()`
    --> `main()`

- Consumed By:
    --> local hooks package scripts and fast CI secret-scanning flows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict, cast

from tools.extension.build import build_extension

BETTERLEAKS_INSTALL_HINT = (
    "betterleaks is required for this security gate; install it with "
    "`brew install betterleaks/tap/betterleaks` or place the binary on PATH"
)

SCAN_BATCH_SIZE = 200
TRACKED_CACHE_VERSION = 1
TRACKED_CACHE_PATH = Path("sw") / "betterleaks-tracked-cache.json"


class TrackedCachePayload(TypedDict):
    version: int
    betterleaks_version: str
    config_identity: str
    files: dict[str, str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Betterleaks for local repo security gates")
    parser.add_argument(
        "--mode",
        choices=("staged", "tracked"),
        required=True,
        help="Choose the local security scan scope",
    )
    parser.add_argument(
        "--include-built-extension",
        action="store_true",
        help="Build and scan stripped extension artifacts too",
    )
    return parser.parse_args()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git_paths(repo_root: Path, args: Sequence[str]) -> list[Path]:
    output = subprocess.check_output(["git", *args], cwd=repo_root, text=True)
    return [repo_root / line for line in output.splitlines() if line.strip()]


def _git_dir(repo_root: Path) -> Path:
    output = subprocess.check_output(["git", "rev-parse", "--git-dir"], cwd=repo_root, text=True)
    git_dir = Path(output.strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir
    return git_dir.resolve()


def _scan_targets(mode: str, repo_root: Path) -> list[Path]:
    if mode == "staged":
        return _git_paths(repo_root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return _git_paths(repo_root, ["ls-files"])


def _betterleaks_binary() -> str:
    binary = shutil.which("betterleaks")
    if binary is None:
        raise SystemExit(BETTERLEAKS_INSTALL_HINT)
    return binary


def _betterleaks_version(binary: str, repo_root: Path) -> str:
    output = subprocess.check_output([binary, "--version"], cwd=repo_root, text=True)
    return output.strip()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tracked_cache_file(repo_root: Path) -> Path:
    return _git_dir(repo_root) / TRACKED_CACHE_PATH


def _config_identity(repo_root: Path) -> str | None:
    config_path = repo_root / ".betterleaks.toml"
    if not config_path.is_file():
        return "missing"
    try:
        return _hash_file(config_path)
    except OSError:
        return None


def _load_tracked_cache(repo_root: Path) -> TrackedCachePayload | None:
    try:
        cache_path = _tracked_cache_file(repo_root)
    except (OSError, subprocess.SubprocessError):
        return None
    if not cache_path.is_file():
        return None

    try:
        raw_payload = cast(object, json.loads(cache_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(raw_payload, dict):
        return None
    payload = cast(dict[str, object], raw_payload)
    if payload.get("version") != TRACKED_CACHE_VERSION:
        return None
    betterleaks_version = payload.get("betterleaks_version")
    if not isinstance(betterleaks_version, str):
        return None
    config_identity = payload.get("config_identity")
    if not isinstance(config_identity, str):
        return None

    files = payload.get("files")
    if not isinstance(files, dict):
        return None

    typed_files: dict[str, str] = {}
    for relative_path, digest in cast(dict[object, object], files).items():
        if not isinstance(relative_path, str) or not isinstance(digest, str):
            return None
        typed_files[relative_path] = digest

    return TrackedCachePayload(
        version=TRACKED_CACHE_VERSION,
        betterleaks_version=betterleaks_version,
        config_identity=config_identity,
        files=typed_files,
    )


def _write_tracked_cache(
    repo_root: Path,
    *,
    betterleaks_version: str,
    config_identity: str,
    file_digests: dict[str, str],
) -> None:
    try:
        cache_path = _tracked_cache_file(repo_root)
    except (OSError, subprocess.SubprocessError):
        return
    payload: TrackedCachePayload = {
        "version": TRACKED_CACHE_VERSION,
        "betterleaks_version": betterleaks_version,
        "config_identity": config_identity,
        "files": file_digests,
    }

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        _ = cache_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError:
        return


def _tracked_files_to_scan(
    repo_root: Path,
    *,
    targets: Sequence[Path],
    betterleaks_version: str,
) -> tuple[list[Path], dict[str, str], str | None]:
    current_file_digests: dict[str, str] = {}
    current_targets: dict[str, Path] = {}
    forced_scan_targets: list[Path] = []

    for target in targets:
        if not target.is_file():
            continue
        try:
            relative_path = target.relative_to(repo_root).as_posix()
            digest = _hash_file(target)
        except (OSError, ValueError):
            forced_scan_targets.append(target)
            continue
        current_targets[relative_path] = target
        current_file_digests[relative_path] = digest

    config_identity = _config_identity(repo_root)
    if config_identity is None:
        return [*list(current_targets.values()), *forced_scan_targets], {}, None

    cache_payload = _load_tracked_cache(repo_root)
    if cache_payload is None:
        return (
            [*list(current_targets.values()), *forced_scan_targets],
            current_file_digests,
            config_identity,
        )

    if (
        cache_payload["betterleaks_version"] != betterleaks_version
        or cache_payload["config_identity"] != config_identity
    ):
        return (
            [*list(current_targets.values()), *forced_scan_targets],
            current_file_digests,
            config_identity,
        )

    scan_targets: list[Path] = []
    for relative_path, digest in current_file_digests.items():
        if cache_payload["files"].get(relative_path) != digest:
            scan_targets.append(current_targets[relative_path])

    return [*scan_targets, *forced_scan_targets], current_file_digests, config_identity


def _run_scan(binary: str, repo_root: Path, targets: Sequence[Path]) -> None:
    config_path = repo_root / ".betterleaks.toml"
    base_command = [
        binary,
        "dir",
        "--config",
        str(config_path),
        "--no-banner",
        "--no-color",
        "--redact=100",
        "--max-archive-depth",
        "2",
        "--exit-code",
        "1",
    ]
    for start in range(0, len(targets), SCAN_BATCH_SIZE):
        batch = targets[start : start + SCAN_BATCH_SIZE]
        command = [*base_command, *(str(target) for target in batch)]
        subprocess.run(command, cwd=repo_root, check=True)


def run_betterleaks(mode: str, *, include_built_extension: bool) -> int:
    repo_root = _repo_root()
    targets = _scan_targets(mode, repo_root)
    if not targets and not include_built_extension:
        print(f"No {mode} files to scan with Betterleaks")
        return 0

    binary = _betterleaks_binary()
    if mode == "tracked":
        try:
            betterleaks_version = _betterleaks_version(binary, repo_root)
        except (OSError, subprocess.SubprocessError):
            betterleaks_version = ""
        tracked_targets, file_digests, config_identity = _tracked_files_to_scan(
            repo_root,
            targets=targets,
            betterleaks_version=betterleaks_version,
        )
        if tracked_targets:
            _run_scan(binary, repo_root, tracked_targets)
        elif targets:
            print("No changed tracked files to rescan with Betterleaks")
        elif not include_built_extension:
            print("No tracked files to scan with Betterleaks")
        if betterleaks_version and config_identity is not None:
            _write_tracked_cache(
                repo_root,
                betterleaks_version=betterleaks_version,
                config_identity=config_identity,
                file_digests=file_digests,
            )
    else:
        _run_scan(binary, repo_root, targets)

    if not include_built_extension:
        return 0

    with tempfile.TemporaryDirectory() as raw_tmp:
        built_dir = Path(raw_tmp) / "extension"
        build_extension(repo_root / "apps" / "extension", built_dir)
        _run_scan(binary, repo_root, [built_dir])

    return 0


def main() -> int:
    args = _parse_args()
    return run_betterleaks(
        args.mode,
        include_built_extension=args.include_built_extension,
    )


if __name__ == "__main__":
    raise SystemExit(main())
