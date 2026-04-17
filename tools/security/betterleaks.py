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
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Sequence

from tools.extension.build import build_extension

BETTERLEAKS_INSTALL_HINT = (
    "betterleaks is required for this security gate; install it with "
    "`brew install betterleaks/tap/betterleaks` or place the binary on PATH"
)

SCAN_BATCH_SIZE = 200


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


def _scan_targets(mode: str, repo_root: Path) -> list[Path]:
    if mode == "staged":
        return _git_paths(repo_root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return _git_paths(repo_root, ["ls-files"])


def _betterleaks_binary() -> str:
    binary = shutil.which("betterleaks")
    if binary is None:
        raise SystemExit(BETTERLEAKS_INSTALL_HINT)
    return binary


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
    if not targets:
        print(f"No {mode} files to scan with Betterleaks")
        return 0

    binary = _betterleaks_binary()
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
