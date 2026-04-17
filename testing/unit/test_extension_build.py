"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify stripped extension artifact building so shipped HTML never keeps source comments

- Later Extension Points:
    --> add more packaging fixtures only when extension release assembly grows later

- Role:
    --> builds temp extension artifacts from sample source files
    --> checks that HTML comments strip while non-HTML assets stay unchanged

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extension.build import build_extension


class TestExtensionBuild(unittest.TestCase):
    def test_build_extension_strips_html_comments(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            source = root / "apps" / "extension"
            output = root / "build" / "extension"
            source.mkdir(parents=True)
            (source / "popup.html").write_text(
                '<!DOCTYPE html>\n<!-- source note -->\n<html><body>popup</body></html>\n'
            )
            (source / "manifest.json").write_text('{"name": "sample"}\n')

            build_extension(source, output)

            self.assertNotIn("<!--", (output / "popup.html").read_text())
            self.assertEqual((output / "manifest.json").read_text(), '{"name": "sample"}\n')
