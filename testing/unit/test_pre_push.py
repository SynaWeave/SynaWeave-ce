"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify pre-push keeps existing gate order while switching default
            operator output to labeled compact phases

- Later Extension Points:
    --> add more branch cases only when the governed pre-push flow grows

- Role:
    --> covers output mode selection and failure messaging for the pre-push
        orchestration module
    --> verifies default compact mode and full-mode override use the same gate
        sequence

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.dev import pre_push
from tools.dev.phase_runner import PhaseResult


class TestPrePush(unittest.TestCase):
    def test_default_mode_is_compact(self):
        phases: list[tuple[str, str]] = []

        def fake_run_gated_phase(*, phase, repo_root, output_mode):
            phases.append((phase.label, output_mode))
            return PhaseResult(phase=phase, returncode=0)

        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch("tools.dev.pre_push._run_gated_phase", side_effect=fake_run_gated_phase):
                exit_code = pre_push.main(["--root", str(Path(raw_tmp))])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            phases,
            [
                ("betterleaks", "compact"),
                ("environment-sync", "compact"),
                ("environment-check", "compact"),
                ("verify", "compact"),
            ],
        )

    def test_full_mode_env_var_switches_all_phases(self):
        phases: list[tuple[str, str]] = []

        def fake_run_gated_phase(*, phase, repo_root, output_mode):
            phases.append((phase.label, output_mode))
            return PhaseResult(phase=phase, returncode=0)

        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch.dict(os.environ, {pre_push.FULL_OUTPUT_ENV_VAR: "full"}, clear=False):
                with patch("tools.dev.pre_push._run_gated_phase", side_effect=fake_run_gated_phase):
                    exit_code = pre_push.main(["--root", str(Path(raw_tmp))])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            phases,
            [
                ("betterleaks", "full"),
                ("environment-sync", "full"),
                ("environment-check", "full"),
                ("verify", "full"),
            ],
        )

    def test_sync_failure_keeps_existing_guidance(self):
        stream = io.StringIO()
        betterleaks_phase = PhaseResult(
            phase=pre_push.Phase(
                label="betterleaks",
                command=("python3",),
                success_summary="ok",
            ),
            returncode=0,
        )
        sync_phase = PhaseResult(
            phase=pre_push.Phase(
                label="environment-sync",
                command=("python3",),
                success_summary="ok",
            ),
            returncode=3,
        )

        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch(
                "tools.dev.pre_push._run_gated_phase",
                side_effect=[betterleaks_phase, sync_phase],
            ):
                with redirect_stdout(stream):
                    exit_code = pre_push.main(["--root", str(Path(raw_tmp))])

        output = stream.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "pre-push: hook-safe environment sync failed; resolve the error above before push",
            output,
        )

    def test_environment_check_incomplete_keeps_existing_guidance(self):
        stream = io.StringIO()
        phase_results = [
            PhaseResult(
                phase=pre_push.Phase(
                    label="betterleaks",
                    command=("python3",),
                    success_summary="ok",
                ),
                returncode=0,
            ),
            PhaseResult(
                phase=pre_push.Phase(
                    label="environment-sync",
                    command=("python3",),
                    success_summary="ok",
                ),
                returncode=0,
            ),
            PhaseResult(
                phase=pre_push.Phase(
                    label="environment-check",
                    command=("python3",),
                    success_summary="ok",
                ),
                returncode=1,
            ),
        ]

        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch("tools.dev.pre_push._run_gated_phase", side_effect=phase_results):
                with redirect_stdout(stream):
                    exit_code = pre_push.main(["--root", str(Path(raw_tmp))])

        output = stream.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "pre-push: automatic retry left local tooling incomplete; rerun python3 -m "
            "tools.dev.sync_environment sync to inspect the remaining issue before push",
            output,
        )
