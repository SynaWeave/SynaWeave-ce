"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify Betterleaks wrapper behavior for local hook scan scopes without the binary

- Later Extension Points:
    --> add more wrapper tests only when local scan modes or artifact targets change

- Role:
    --> checks staged-empty handling and tracked artifact scan wiring
    --> keeps hook wrappers deterministic even when the external scanner is mocked in unit tests

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import patch

from tools.security.betterleaks import TRACKED_CACHE_PATH, run_betterleaks


class TestSecurityBetterleaks(unittest.TestCase):
    @staticmethod
    def _write_config(repo_root: Path, *, use_default: bool = True) -> None:
        _ = (repo_root / ".betterleaks.toml").write_text(
            f"[extend]\nuseDefault = {'true' if use_default else 'false'}\n",
            encoding="utf-8",
        )

    @patch("tools.security.betterleaks._betterleaks_binary", return_value="betterleaks")
    @patch("tools.security.betterleaks.subprocess.run")
    @patch("tools.security.betterleaks._scan_targets", return_value=[])
    def test_run_betterleaks_skips_when_no_targets(self, _scan_targets, run_mock, _binary):
        _ = self.assertEqual(run_betterleaks("staged", include_built_extension=False), 0)
        run_mock.assert_not_called()

    def test_initial_tracked_scan_populates_cache(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            git_dir = repo_root / ".git"
            git_dir.mkdir()
            tracked_file = repo_root / "tracked.txt"
            _ = tracked_file.write_text("clean\n", encoding="utf-8")
            self._write_config(repo_root)

            with (
                patch("tools.security.betterleaks._repo_root", return_value=repo_root),
                patch("tools.security.betterleaks._git_dir", return_value=git_dir),
                patch("tools.security.betterleaks._scan_targets", return_value=[tracked_file]),
                patch("tools.security.betterleaks._betterleaks_binary", return_value="betterleaks"),
                patch(
                    "tools.security.betterleaks._betterleaks_version",
                    return_value="betterleaks 1.0.0",
                ),
                patch("tools.security.betterleaks._run_scan") as run_scan_mock,
            ):
                _ = self.assertEqual(run_betterleaks("tracked", include_built_extension=False), 0)

            run_scan_mock.assert_called_once_with("betterleaks", repo_root, [tracked_file])
            cache_payload = cast(
                dict[str, object],
                json.loads((git_dir / TRACKED_CACHE_PATH).read_text(encoding="utf-8")),
            )
            self.assertEqual(cache_payload["betterleaks_version"], "betterleaks 1.0.0")
            self.assertIn("tracked.txt", cast(dict[str, str], cache_payload["files"]))

    def test_second_unchanged_tracked_scan_skips_cached_clean_files(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            git_dir = repo_root / ".git"
            git_dir.mkdir()
            tracked_file = repo_root / "tracked.txt"
            _ = tracked_file.write_text("clean\n", encoding="utf-8")
            self._write_config(repo_root)

            with (
                patch("tools.security.betterleaks._repo_root", return_value=repo_root),
                patch("tools.security.betterleaks._git_dir", return_value=git_dir),
                patch("tools.security.betterleaks._scan_targets", return_value=[tracked_file]),
                patch("tools.security.betterleaks._betterleaks_binary", return_value="betterleaks"),
                patch(
                    "tools.security.betterleaks._betterleaks_version",
                    return_value="betterleaks 1.0.0",
                ),
                patch("tools.security.betterleaks._run_scan") as run_scan_mock,
            ):
                _ = self.assertEqual(run_betterleaks("tracked", include_built_extension=False), 0)
                _ = self.assertEqual(run_betterleaks("tracked", include_built_extension=False), 0)

            self.assertEqual(run_scan_mock.call_count, 1)

    def test_tracked_file_content_change_rescans_that_file(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            git_dir = repo_root / ".git"
            git_dir.mkdir()
            tracked_file = repo_root / "tracked.txt"
            _ = tracked_file.write_text("clean\n", encoding="utf-8")
            self._write_config(repo_root)

            with (
                patch("tools.security.betterleaks._repo_root", return_value=repo_root),
                patch("tools.security.betterleaks._git_dir", return_value=git_dir),
                patch("tools.security.betterleaks._scan_targets", return_value=[tracked_file]),
                patch("tools.security.betterleaks._betterleaks_binary", return_value="betterleaks"),
                patch(
                    "tools.security.betterleaks._betterleaks_version",
                    return_value="betterleaks 1.0.0",
                ),
                patch("tools.security.betterleaks._run_scan") as run_scan_mock,
            ):
                _ = self.assertEqual(run_betterleaks("tracked", include_built_extension=False), 0)
                _ = tracked_file.write_text("changed\n", encoding="utf-8")
                _ = self.assertEqual(run_betterleaks("tracked", include_built_extension=False), 0)

            self.assertEqual(run_scan_mock.call_count, 2)
            self.assertEqual(run_scan_mock.call_args_list[-1].args[2], [tracked_file])

    def test_config_or_version_change_invalidates_cache(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            git_dir = repo_root / ".git"
            git_dir.mkdir()
            tracked_file = repo_root / "tracked.txt"
            _ = tracked_file.write_text("clean\n", encoding="utf-8")
            config_file = repo_root / ".betterleaks.toml"
            self._write_config(repo_root)

            with (
                patch("tools.security.betterleaks._repo_root", return_value=repo_root),
                patch("tools.security.betterleaks._git_dir", return_value=git_dir),
                patch("tools.security.betterleaks._scan_targets", return_value=[tracked_file]),
                patch("tools.security.betterleaks._betterleaks_binary", return_value="betterleaks"),
                patch("tools.security.betterleaks._run_scan") as run_scan_mock,
            ):
                with patch(
                    "tools.security.betterleaks._betterleaks_version",
                    return_value="betterleaks 1.0.0",
                ):
                    result = run_betterleaks("tracked", include_built_extension=False)
                    self.assertEqual(result, 0)
                    _ = config_file.write_text(
                        "[extend]\nuseDefault = false\n",
                        encoding="utf-8",
                    )
                    result = run_betterleaks("tracked", include_built_extension=False)
                    self.assertEqual(result, 0)

                with patch(
                    "tools.security.betterleaks._betterleaks_version",
                    return_value="betterleaks 2.0.0",
                ):
                    result = run_betterleaks("tracked", include_built_extension=False)
                    self.assertEqual(result, 0)

            self.assertEqual(run_scan_mock.call_count, 3)
            for call in run_scan_mock.call_args_list:
                self.assertEqual(call.args[2], [tracked_file])

    def test_built_extension_still_scans_each_tracked_run_when_requested(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            git_dir = repo_root / ".git"
            git_dir.mkdir()
            tracked_file = repo_root / "tracked.txt"
            _ = tracked_file.write_text("clean\n", encoding="utf-8")
            self._write_config(repo_root)

            def fake_build_extension(_source: Path, output_dir: Path) -> None:
                output_dir.mkdir(parents=True, exist_ok=True)
                _ = (output_dir / "bundle.js").write_text("artifact\n", encoding="utf-8")

            with (
                patch("tools.security.betterleaks._repo_root", return_value=repo_root),
                patch("tools.security.betterleaks._git_dir", return_value=git_dir),
                patch("tools.security.betterleaks._scan_targets", return_value=[tracked_file]),
                patch("tools.security.betterleaks._betterleaks_binary", return_value="betterleaks"),
                patch(
                    "tools.security.betterleaks._betterleaks_version",
                    return_value="betterleaks 1.0.0",
                ),
                patch(
                    "tools.security.betterleaks.build_extension",
                    side_effect=fake_build_extension,
                ),
                patch("tools.security.betterleaks._run_scan") as run_scan_mock,
            ):
                _ = self.assertEqual(run_betterleaks("tracked", include_built_extension=True), 0)
                _ = self.assertEqual(run_betterleaks("tracked", include_built_extension=True), 0)

            self.assertEqual(run_scan_mock.call_count, 3)
            self.assertEqual(run_scan_mock.call_args_list[0].args[2], [tracked_file])
            self.assertEqual(len(cast(list[Path], run_scan_mock.call_args_list[1].args[2])), 1)
            self.assertEqual(len(cast(list[Path], run_scan_mock.call_args_list[2].args[2])), 1)
            self.assertNotEqual(run_scan_mock.call_args_list[1].args[2], [tracked_file])
            self.assertNotEqual(run_scan_mock.call_args_list[2].args[2], [tracked_file])


if __name__ == "__main__":
    unittest.main()
