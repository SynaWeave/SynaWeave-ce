"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run named local command phases with concurrently-style
            compact summaries and buffered failure logs by default

- Later Extension Points:
    --> add richer summary parsing only when more governed hook flows need it

- Role:
    --> gives local hooks and helper scripts one small phase-oriented runner
    --> keeps default output quiet and readable for humans
    --> preserves full logs on demand or on failure

- Exports:
    --> `Phase`
    --> `PhaseResult`
    --> `run_phase()`

- Consumed By:
    --> `tools.dev.pre_push`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

OutputMode = Literal["compact", "full"]
SummaryBuilder = Callable[[str], str]


@dataclass(frozen=True)
class Phase:
    label: str
    command: tuple[str, ...]
    success_summary: str | SummaryBuilder


@dataclass(frozen=True)
class PhaseResult:
    phase: Phase
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def _render_summary(phase: Phase, output: str) -> str:
    if callable(phase.success_summary):
        return phase.success_summary(output)
    return phase.success_summary


def _print_compact_failure_output(result: PhaseResult) -> None:
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        if result.stdout.strip():
            print()
        print(result.stderr.rstrip())


def _format_duration(seconds: float) -> str:
    if seconds < 10:
        return f"{seconds:.1f}s"
    return f"{seconds:.0f}s"


def run_phase(*, phase: Phase, repo_root: Path, output_mode: OutputMode) -> PhaseResult:
    print(f"[{phase.label}] starting")
    started_at = time.monotonic()

    if output_mode == "full":
        completed = subprocess.run(phase.command, cwd=repo_root, check=False)
        result = PhaseResult(phase=phase, returncode=completed.returncode)
    else:
        completed = subprocess.run(
            phase.command,
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        result = PhaseResult(
            phase=phase,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    duration = _format_duration(time.monotonic() - started_at)

    if result.succeeded:
        summary = _render_summary(result.phase, result.stdout.strip())
        print(f"[{phase.label}] done {summary} ({duration})")
        return result

    print(f"[{phase.label}] fail exit {result.returncode} ({duration})")
    if output_mode == "compact":
        _print_compact_failure_output(result)
    return result
