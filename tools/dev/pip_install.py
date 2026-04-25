"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  install Python requirements through one repo-owned command that works in
            active virtualenvs repo-owned virtualenvs and system-python setups

- Later Extension Points:
    --> add narrower install modes only when the repo adopts a second durable
    --> Python environment workflow beyond active venv repo `.venv` or system Python

- Role:
    --> resolves the bounded Python install target for package scripts and local helpers
    --> keeps pip install flags valid across virtualenv and system-python environments

- Exports:
    --> `PythonInstallPlan`
    --> `resolve_python_install_plan()`
    --> `build_install_command()`
    --> `main()`

- Consumed By:
    --> `package.json` dependency scripts
    --> local Python helpers that need one governed install contract
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

LOCAL_VENV_PYTHON = Path(".venv") / "bin" / "python3"
SYSTEM_PYTHON = "python3"
SYSTEM_PIP_FLAGS = ("--user", "--break-system-packages")


@dataclass(frozen=True)
class PythonInstallPlan:
    python_executable: str
    source: str
    pip_flags: tuple[str, ...]


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Python requirements with the governed repo command"
    )
    _ = parser.add_argument(
        "-r",
        "--requirements",
        action="append",
        dest="requirements_files",
        required=True,
        help="requirements file to install",
    )
    _ = parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    return parser.parse_args(argv)


def running_in_virtualenv() -> bool:
    return getattr(sys, "base_prefix", sys.prefix) != sys.prefix or hasattr(
        sys, "real_prefix"
    )


def resolve_python_install_plan(
    repo_root: Path,
    *,
    prefer_active_venv: bool = True,
) -> PythonInstallPlan:
    if prefer_active_venv and running_in_virtualenv():
        return PythonInstallPlan(
            python_executable=sys.executable,
            source="active virtualenv",
            pip_flags=(),
        )

    local_python = repo_root / LOCAL_VENV_PYTHON
    if local_python.is_file():
        return PythonInstallPlan(
            python_executable=str(local_python.resolve()),
            source="repo-owned .venv",
            pip_flags=(),
        )

    return PythonInstallPlan(
        python_executable=SYSTEM_PYTHON,
        source="system python",
        pip_flags=SYSTEM_PIP_FLAGS,
    )


def build_install_command(
    plan: PythonInstallPlan,
    requirements_files: Sequence[str],
) -> tuple[str, ...]:
    command: list[str] = [plan.python_executable, "-m", "pip", "install", *plan.pip_flags]
    for requirements_file in requirements_files:
        command.extend(["-r", requirements_file])
    return tuple(command)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(cast(str, args.root)).resolve()
    plan = resolve_python_install_plan(repo_root)
    command = build_install_command(plan, tuple(cast(Sequence[str], args.requirements_files)))

    print(f"Python dependency install using {plan.source}")
    print(f"$ {' '.join(command)}")
    result = subprocess.run(command, cwd=repo_root, check=False)
    return int(result.returncode)


if __name__ == "__main__":
    sys.exit(main())
