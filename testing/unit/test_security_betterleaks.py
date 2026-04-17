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

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.security.betterleaks import run_betterleaks


class TestSecurityBetterleaks(unittest.TestCase):
    @patch("tools.security.betterleaks._betterleaks_binary", return_value="betterleaks")
    @patch("tools.security.betterleaks.subprocess.run")
    @patch("tools.security.betterleaks._scan_targets", return_value=[])
    def test_run_betterleaks_skips_when_no_targets(self, _scan_targets, run_mock, _binary):
        self.assertEqual(run_betterleaks("staged", include_built_extension=False), 0)
        run_mock.assert_not_called()

    @patch("tools.security.betterleaks._betterleaks_binary", return_value="betterleaks")
    @patch("tools.security.betterleaks.build_extension")
    @patch("tools.security.betterleaks.subprocess.run")
    @patch("tools.security.betterleaks._scan_targets")
    @patch("tools.security.betterleaks._repo_root")
    def test_run_betterleaks_scans_repo_and_artifact(
        self,
        repo_root_mock,
        scan_targets_mock,
        run_mock,
        build_extension_mock,
        _binary,
    ):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            repo_root_mock.return_value = repo_root
            scan_targets_mock.return_value = [repo_root]
            self.assertEqual(run_betterleaks("tracked", include_built_extension=True), 0)
            self.assertEqual(run_mock.call_count, 2)
            build_extension_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
