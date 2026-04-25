"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run repo package scripts with Bun first and npm as the bounded fallback

- Later Extension Points:
    --> add more package-manager backends only when the repo adopts another durable JS runner

- Role:
    --> resolves the governed JS runner for recursive package script execution
    --> keeps Bun as the default path while allowing npm fallback in constrained environments

- Exports:
    --> `resolve_runner()`
    --> `build_command()`
    --> `main()`

- Consumed By:
    --> package scripts and Python helpers that need one bounded JS runner contract
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ALLOWED_RUNNERS = ("bun", "npm")
ENV_RUNNER_NAME = "SW_JS_RUNNER"


@dataclass(frozen=True)
class RunnerChoice:
    name: str
    command_prefix: tuple[str, ...]


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a package.json script with the governed JS runner"
    )
    _ = parser.add_argument("script_name", help="package.json script name")
    _ = parser.add_argument(
        "script_args",
        nargs="*",
        help="extra arguments passed to the script",
    )
    _ = parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    return parser.parse_args(argv)


def _runner_from_name(name: str) -> RunnerChoice:
    if name == "bun":
        return RunnerChoice(name="bun", command_prefix=("bun", "run"))
    if name == "npm":
        return RunnerChoice(name="npm", command_prefix=("npm", "run"))
    raise ValueError(f"unsupported JS runner: {name}")


def resolve_runner(*, environ: dict[str, str] | None = None) -> RunnerChoice:
    environment = environ or os.environ
    requested_runner = environment.get(ENV_RUNNER_NAME)
    if requested_runner is not None:
        if requested_runner not in ALLOWED_RUNNERS:
            allowed_runners = ", ".join(ALLOWED_RUNNERS)
            raise ValueError(
                f"{ENV_RUNNER_NAME} must be one of {allowed_runners}; got {requested_runner}"
            )
        if shutil.which(requested_runner) is None:
            raise FileNotFoundError(
                f"requested JS runner '{requested_runner}' is not available on PATH"
            )
        return _runner_from_name(requested_runner)

    bun_path = shutil.which("bun")
    if bun_path is not None:
        return _runner_from_name("bun")

    npm_path = shutil.which("npm")
    if npm_path is not None:
        return _runner_from_name("npm")

    raise FileNotFoundError("missing both bun and npm on PATH")


def build_command(
    script_name: str,
    script_args: Sequence[str],
    *,
    runner: RunnerChoice,
) -> tuple[str, ...]:
    if runner.name == "npm" and script_args:
        return (*runner.command_prefix, script_name, "--", *script_args)
    return (*runner.command_prefix, script_name, *script_args)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(cast(str, args.root)).resolve()

    try:
        runner = resolve_runner()
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    command = build_command(
        cast(str, args.script_name),
        tuple(cast(Sequence[str], args.script_args)),
        runner=runner,
    )
    print(f"$ {' '.join(command)}")
    result = subprocess.run(command, cwd=repo_root, check=False)
    return int(result.returncode)


if __name__ == "__main__":
    sys.exit(main())
