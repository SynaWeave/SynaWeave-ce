"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify compact and full phase-runner output modes stay readable
            without changing command semantics

- Later Extension Points:
    --> add more phase formatting cases only when more hooks depend on them

- Role:
    --> covers success and failure output behavior for the shared phase helper
    --> verifies compact mode buffers logs while full mode streams raw output

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from tools.dev.phase_runner import Phase, run_phase


class TestPhaseRunner(unittest.TestCase):
    def test_compact_mode_shows_summary_without_raw_success_output(self):
        phase = Phase(
            label="demo",
            command=("python3", "-m", "example"),
            success_summary=lambda output: output.splitlines()[-1] if output else "demo passed",
        )
        stream = io.StringIO()

        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch("tools.dev.phase_runner.subprocess.run") as mock_run:
                mock_run.return_value = CompletedProcess(
                    args=phase.command,
                    returncode=0,
                    stdout="hidden success detail\ncompact summary\n",
                    stderr="",
                )
                with redirect_stdout(stream):
                    result = run_phase(
                        phase=phase,
                        repo_root=Path(raw_tmp),
                        output_mode="compact",
                    )

        output = stream.getvalue()
        self.assertTrue(result.succeeded)
        self.assertIn("[demo] starting", output)
        self.assertIn("[demo] done compact summary", output)
        self.assertNotIn("hidden success detail", output)

    def test_compact_mode_prints_buffered_output_on_failure(self):
        phase = Phase(label="demo", command=("python3", "-m", "example"), success_summary="unused")
        stream = io.StringIO()

        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch("tools.dev.phase_runner.subprocess.run") as mock_run:
                mock_run.return_value = CompletedProcess(
                    args=phase.command,
                    returncode=7,
                    stdout="stdout detail\n",
                    stderr="stderr detail\n",
                )
                with redirect_stdout(stream):
                    result = run_phase(
                        phase=phase,
                        repo_root=Path(raw_tmp),
                        output_mode="compact",
                    )

        output = stream.getvalue()
        self.assertFalse(result.succeeded)
        self.assertIn("[demo] fail exit 7", output)
        self.assertIn("stdout detail", output)
        self.assertIn("stderr detail", output)

    def test_full_mode_streams_without_capture(self):
        phase = Phase(
            label="demo",
            command=("python3", "-m", "example"),
            success_summary="demo passed",
        )
        stream = io.StringIO()

        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch("tools.dev.phase_runner.subprocess.run") as mock_run:
                mock_run.return_value = CompletedProcess(args=phase.command, returncode=0)
                with redirect_stdout(stream):
                    result = run_phase(
                        phase=phase,
                        repo_root=Path(raw_tmp),
                        output_mode="full",
                    )

        output = stream.getvalue()
        self.assertTrue(result.succeeded)
        self.assertIn("[demo] done demo passed", output)
        self.assertEqual(mock_run.call_args.kwargs["cwd"], Path(raw_tmp))
        self.assertFalse(mock_run.call_args.kwargs.get("capture_output", False))
        self.assertNotIn("text", mock_run.call_args.kwargs)
