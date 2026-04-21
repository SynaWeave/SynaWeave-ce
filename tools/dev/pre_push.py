"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the governed pre-push gates with compact phase labels by
            default while keeping a raw-output escape hatch

- Later Extension Points:
    --> add more push-time phases only when they become durable default gates

- Role:
    --> preserves existing pre-push verification order and blocking semantics
    --> switches default operator output from raw command noise to compact
        phase summaries

- Exports:
    --> `main()`

- Consumed By:
    --> `tools/hooks/pre-push`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence, cast

from tools.dev.phase_runner import OutputMode, Phase, PhaseResult, run_phase

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_MODE: OutputMode = "compact"
FULL_OUTPUT_ENV_VAR = "SYNAWAVE_PRE_PUSH_OUTPUT"


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run governed pre-push verification")
    parser.add_argument(
        "--output",
        choices=("compact", "full"),
        help="Override the pre-push output mode",
    )
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT),
        help="Repository root path",
    )
    return parser.parse_args(argv)


def _resolve_output_mode(explicit_mode: str | None) -> OutputMode:
    if explicit_mode is not None:
        return cast(OutputMode, explicit_mode)
    if os.environ.get(FULL_OUTPUT_ENV_VAR) == "full":
        return "full"
    return DEFAULT_OUTPUT_MODE


def _environment_sync_summary(output: str) -> str:
    for line in reversed([line.strip() for line in output.splitlines() if line.strip()]):
        if line.startswith("Environment "):
            return line
    return "environment sync complete"


def _environment_check_summary(output: str) -> str:
    for line in reversed([line.strip() for line in output.splitlines() if line.strip()]):
        if line.startswith("Environment "):
            return line
    return "environment stamp is current"


def _run_gated_phase(
    *,
    phase: Phase,
    repo_root: Path,
    output_mode: OutputMode,
) -> PhaseResult:
    result = run_phase(phase=phase, repo_root=repo_root, output_mode=output_mode)
    print()
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(args.root).resolve()
    output_mode = _resolve_output_mode(args.output)

    betterleaks = _run_gated_phase(
        phase=Phase(
            label="betterleaks",
            command=(
                "python3",
                "-m",
                "tools.security.betterleaks",
                "--mode",
                "tracked",
                "--include-built-extension",
            ),
            success_summary="tracked-file secret scan passed",
        ),
        repo_root=repo_root,
        output_mode=output_mode,
    )
    if not betterleaks.succeeded:
        return betterleaks.returncode

    sync_result = _run_gated_phase(
        phase=Phase(
            label="environment-sync",
            command=(
                "python3",
                "-m",
                "tools.dev.sync_environment",
                "sync",
                "--mode",
                "hook",
            ),
            success_summary=_environment_sync_summary,
        ),
        repo_root=repo_root,
        output_mode=output_mode,
    )
    if not sync_result.succeeded:
        print("pre-push: hook-safe environment sync failed; resolve the error above before push")
        return 1

    check_result = _run_gated_phase(
        phase=Phase(
            label="environment-check",
            command=("python3", "-m", "tools.dev.sync_environment", "check"),
            success_summary=_environment_check_summary,
        ),
        repo_root=repo_root,
        output_mode=output_mode,
    )
    if check_result.returncode == 1:
        print(
            "pre-push: automatic retry left local tooling incomplete; rerun python3 -m "
            "tools.dev.sync_environment sync to inspect the remaining issue before push"
        )
        return 1
    if check_result.returncode == 2:
        print("pre-push: environment check failed; fix repo state before push")
        return 1
    if not check_result.succeeded:
        return check_result.returncode

    verify_result = _run_gated_phase(
        phase=Phase(
            label="verify",
            command=("bun", "run", "verify"),
            success_summary="full verification lane passed",
        ),
        repo_root=repo_root,
        output_mode=output_mode,
    )
    return verify_result.returncode


if __name__ == "__main__":
    sys.exit(main())
