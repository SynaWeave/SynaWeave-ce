"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the repo-owned TypeScript compiler
with the governed JS runner choice

- Later Extension Points:
    --> add more direct JS tool runners only when Python helpers
        need another shared binary invocation contract

- Role:
    --> keeps Bun as the default TypeScript runner path
    --> falls back to npm exec without hardcoding a Node binary path
    --> preserves one shared compiler invocation contract for Python build helpers

- Exports:
    --> `run_tsc()`

- Consumed By:
    --> `tools/web/build.py`
    --> `tools/extension/build.py`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.dev.js_run import resolve_runner


def _repo_tsc_path(repo_root: Path) -> Path:
    return repo_root / "node_modules" / "typescript" / "bin" / "tsc"


def run_tsc(
    *,
    repo_root: Path,
    tsconfig_path: Path,
    output_dir: Path,
    root_dir: Path,
) -> None:
    runner = resolve_runner()
    tsc_path = _repo_tsc_path(repo_root)
    if not tsc_path.is_file():
        raise FileNotFoundError(f"missing TypeScript compiler at {tsc_path}")

    if runner.name == "bun":
        command = ["bun", str(tsc_path)]
    else:
        command = ["npm", "exec", "--", "tsc"]

    command.extend(
        [
            "--project",
            str(tsconfig_path),
            "--outDir",
            str(output_dir),
            "--rootDir",
            str(root_dir),
        ]
    )

    _ = subprocess.run(
        command,
        check=True,
        cwd=repo_root,
    )
