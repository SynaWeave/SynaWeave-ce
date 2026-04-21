"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify local environment sync planning commands and git-local
            stamp handling stay deterministic

- Later Extension Points:
    --> add more watched toolchain groups only when the canonical local
    --> bootstrap surface grows later

- Role:
    --> covers check and sync outcomes against isolated temporary repositories
    --> verifies command dispatch and stamp writing without invoking real Bun or pip installs

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.dev import sync_environment

REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PYTHON_SYNC_COMMAND = (
    "python3",
    "-m",
    "pip",
    "install",
    "--user",
    "--break-system-packages",
    "-r",
    "requirements-dev.txt",
)


def read_canonical_requirements_dev() -> str:
    return (REPO_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")


class TestSyncEnvironment(unittest.TestCase):
    def make_repo(self, root: Path, *, include_bun_lock: bool = True) -> None:
        (root / ".git").mkdir()
        (root / "package.json").write_text('{"name": "sample"}\n', encoding="utf-8")
        (root / "requirements-dev.txt").write_text(
            read_canonical_requirements_dev(),
            encoding="utf-8",
        )
        if include_bun_lock:
            (root / "bun.lock").write_text("lockfile\n", encoding="utf-8")

    def make_local_venv(self, root: Path) -> Path:
        local_python = root / ".venv" / "bin" / "python3"
        local_python.parent.mkdir(parents=True)
        local_python.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        return local_python

    def capture_main(self, argv: list[str]) -> tuple[int, str]:
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = sync_environment.main(argv)
        return exit_code, stream.getvalue()

    def test_check_reports_sync_needed_when_stamp_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root)

            exit_code, output = self.capture_main(["check", "--root", str(repo_root)])

            self.assertEqual(exit_code, sync_environment.EXIT_SYNC_NEEDED)
            self.assertIn("Environment sync needed", output)
            self.assertIn("stamp: stamp missing", output)
            self.assertIn("js: package.json, bun.lock", output)
            self.assertIn("python: requirements-dev.txt", output)

    def test_sync_writes_stamp_and_skips_repeated_work(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root)

            with patch("tools.dev.sync_environment.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                exit_code, output = self.capture_main(["sync", "--root", str(repo_root)])

            self.assertEqual(exit_code, sync_environment.EXIT_OK)
            self.assertIn("Environment sync complete", output)
            self.assertEqual(mock_run.call_count, 2)
            self.assertEqual(
                mock_run.call_args_list[0].args[0], sync_environment.JS_SYNC_COMMAND
            )
            self.assertEqual(mock_run.call_args_list[1].args[0], SYSTEM_PYTHON_SYNC_COMMAND)

            stamp_path = repo_root / ".git" / "synawave" / "environment-sync.json"
            stamp_payload = json.loads(stamp_path.read_text(encoding="utf-8"))
            self.assertEqual(stamp_payload["version"], sync_environment.STAMP_VERSION)
            self.assertEqual(
                sorted(stamp_payload["files"].keys()),
                ["bun.lock", "package.json", "requirements-dev.txt"],
            )

            exit_code, output = self.capture_main(["check", "--root", str(repo_root)])
            self.assertEqual(exit_code, sync_environment.EXIT_OK)
            self.assertIn("Environment sync not needed", output)

    def test_sync_runs_only_python_command_after_requirements_change(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root)
            current_hashes = sync_environment._collect_current_hashes(repo_root)
            sync_environment._write_stamp(repo_root, current_hashes)
            (repo_root / "requirements-dev.txt").write_text(
                read_canonical_requirements_dev() + "# updated\n", encoding="utf-8"
            )

            with patch("tools.dev.sync_environment.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                exit_code, output = self.capture_main(["sync", "--root", str(repo_root)])

            self.assertEqual(exit_code, sync_environment.EXIT_OK)
            self.assertIn("Environment sync complete", output)
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_run.call_args.args[0], SYSTEM_PYTHON_SYNC_COMMAND)

    def test_manual_sync_prefers_repo_owned_python_environment(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root)
            local_python = self.make_local_venv(repo_root)

            with patch("tools.dev.sync_environment.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                exit_code, output = self.capture_main(["sync", "--root", str(repo_root)])

            self.assertEqual(exit_code, sync_environment.EXIT_OK)
            self.assertIn("Environment sync complete", output)
            self.assertEqual(mock_run.call_count, 2)
            self.assertEqual(
                mock_run.call_args_list[1].args[0],
                (
                    str(local_python.resolve()),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    "requirements-dev.txt",
                ),
            )

    def test_sync_runs_only_bun_command_after_js_change_without_lockfile(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root, include_bun_lock=False)
            current_hashes = sync_environment._collect_current_hashes(repo_root)
            sync_environment._write_stamp(repo_root, current_hashes)
            (repo_root / "package.json").write_text(
                '{"name": "sample", "private": true}\n', encoding="utf-8"
            )

            with patch("tools.dev.sync_environment.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                exit_code, output = self.capture_main(["sync", "--root", str(repo_root)])

            self.assertEqual(exit_code, sync_environment.EXIT_OK)
            self.assertIn("Environment sync complete", output)
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_run.call_args.args[0], sync_environment.JS_SYNC_COMMAND)

    def test_hook_mode_falls_back_to_system_python_without_repo_owned_environment(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root)
            current_hashes = sync_environment._collect_current_hashes(repo_root)
            sync_environment._write_stamp(repo_root, current_hashes)
            (repo_root / "requirements-dev.txt").write_text(
                read_canonical_requirements_dev() + "# updated\n", encoding="utf-8"
            )

            with patch("tools.dev.sync_environment.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                exit_code, output = self.capture_main(
                    ["sync", "--mode", "hook", "--root", str(repo_root)]
                )

            self.assertEqual(exit_code, sync_environment.EXIT_OK)
            self.assertIn("Python dependency sync using system python", output)
            self.assertIn("Environment sync complete", output)
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_run.call_args.args[0], SYSTEM_PYTHON_SYNC_COMMAND)

            exit_code, check_output = self.capture_main(["check", "--root", str(repo_root)])
            self.assertEqual(exit_code, sync_environment.EXIT_OK)
            self.assertIn("Environment sync not needed", check_output)

    def test_hook_mode_installs_python_into_repo_owned_environment(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root)
            local_python = self.make_local_venv(repo_root)
            current_hashes = sync_environment._collect_current_hashes(repo_root)
            sync_environment._write_stamp(repo_root, current_hashes)
            (repo_root / "requirements-dev.txt").write_text(
                read_canonical_requirements_dev() + "# updated\n", encoding="utf-8"
            )

            with patch("tools.dev.sync_environment.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                exit_code, output = self.capture_main(
                    ["sync", "--mode", "hook", "--root", str(repo_root)]
                )

            self.assertEqual(exit_code, sync_environment.EXIT_OK)
            self.assertIn("Python dependency sync using repo-owned .venv", output)
            self.assertIn("Environment sync complete", output)
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(
                mock_run.call_args.args[0],
                (
                    str(local_python.resolve()),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    "requirements-dev.txt",
                ),
            )

    def test_sync_returns_failure_without_writing_stamp_when_command_fails(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root)

            with patch("tools.dev.sync_environment.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 9

                exit_code, output = self.capture_main(["sync", "--root", str(repo_root)])

            self.assertEqual(exit_code, sync_environment.EXIT_SYNC_FAILED)
            self.assertIn("Command failed with exit code 9", output)
            self.assertFalse(
                (repo_root / ".git" / "synawave" / "environment-sync.json").exists()
            )

    def test_check_recovers_from_invalid_stamp_as_sync_needed(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            self.make_repo(repo_root)
            stamp_path = repo_root / ".git" / "synawave"
            stamp_path.mkdir(parents=True)
            (stamp_path / "environment-sync.json").write_text("not json\n", encoding="utf-8")

            exit_code, output = self.capture_main(["check", "--root", str(repo_root)])

            self.assertEqual(exit_code, sync_environment.EXIT_SYNC_NEEDED)
            self.assertIn("stamp: stamp invalid", output)
