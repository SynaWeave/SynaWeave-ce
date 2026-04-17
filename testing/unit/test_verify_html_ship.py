"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify ship-facing HTML rules for source comments and stripped extension artifacts

- Later Extension Points:
    --> add more client artifact fixtures only when new governed HTML ship surfaces become real

- Role:
    --> checks that HTML source comments stay non-sensitive
    --> checks that built extension HTML drops all source comments before shipping

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.verify.html_ship import check_html_ship


def make_html_ship_tree(repo_root: Path) -> None:
    source = repo_root / "apps" / "extension"
    source.mkdir(parents=True)
    (source / "popup.html").write_text(
        '<!DOCTYPE html>\n<!-- source note for reviewers -->\n<html><body>popup</body></html>\n'
    )
    (source / "options.html").write_text(
        '<!DOCTYPE html>\n<!-- placeholder note -->\n<html><body>options</body></html>\n'
    )
    (source / "manifest.json").write_text('{"name": "sample"}\n')
    (source / "background.js").write_text('console.log("x")\n')
    (source / "styles.css").write_text('body { color: black; }\n')


class TestVerifyHtmlShip(unittest.TestCase):
    def test_html_ship_passes_when_source_comments_are_safe(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_html_ship_tree(repo_root)
            self.assertEqual(check_html_ship(repo_root), [])

    def test_html_ship_rejects_sensitive_source_comment(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_html_ship_tree(repo_root)
            (repo_root / "apps" / "extension" / "popup.html").write_text(
                '<!DOCTYPE html>\n<!-- internal-only token rotation note -->\n<html></html>\n'
            )
            issues = check_html_ship(repo_root)
            self.assertTrue(any("sensitive ship-facing theory" in issue for issue in issues))
