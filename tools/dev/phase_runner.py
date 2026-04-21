"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run named local command phases with compact success output and
            buffered failure logs by default

- Later Extension Points:
    --> add richer summary parsing only when more governed hook flows need it

- Role:
    --> gives local hooks and helper scripts one small phase-oriented runner
    --> keeps success output readable while preserving full logs on demand or
        on failure

- Exports:
    --> `Phase`
    --> `PhaseResult`
    --> `run_phase()`

- Consumed By:
    --> `tools.dev.pre_push`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import shlex
import subprocess
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


def run_phase(*, phase: Phase, repo_root: Path, output_mode: OutputMode) -> PhaseResult:
    command_display = shlex.join(phase.command)
    print(f"[{phase.label}] {command_display}")

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

    if result.succeeded:
        summary = _render_summary(result.phase, result.stdout.strip())
        print(f"[{phase.label}] ok  {summary}")
        return result

    print(f"[{phase.label}] fail exit {result.returncode}")
    if output_mode == "compact":
        _print_compact_failure_output(result)
    return result
