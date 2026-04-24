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
from unittest.mock import patch

from tools.dev.js_run import RunnerChoice
from tools.extension.build import _compile_typescript_sources, build_extension


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

    def test_build_extension_compiles_typescript_runtime_entrypoints(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            source = root / "apps" / "extension"
            output = root / "build" / "extension"
            source.mkdir(parents=True)
            _ = (source / "popup.html").write_text("<!DOCTYPE html>\n<html></html>\n")
            _ = (source / "manifest.json").write_text('{"name": "sample"}\n')
            _ = (source / "popup_script.ts").write_text("const ready = true;\n")

            with patch("tools.extension.build._compile_typescript_sources") as mock_compile:
                build_extension(source, output)

            self.assertFalse((output / "popup_script.ts").exists())
            mock_compile.assert_called_once_with(source, output)

    @patch("tools.dev.typescript.subprocess.run")
    @patch("tools.dev.typescript.resolve_runner")
    @patch("tools.dev.typescript._repo_tsc_path")
    def test_extension_compile_typescript_sources_uses_governed_bun_runner(
        self,
        mock_repo_tsc_path,
        mock_resolve_runner,
        mock_run,
    ):
        mock_resolve_runner.return_value = RunnerChoice(name="bun", command_prefix=("bun", "run"))

        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            source = root / "apps" / "extension"
            output = root / "build" / "extension"
            source.mkdir(parents=True)
            output.mkdir(parents=True)
            (source / "popup_script.ts").write_text("const ready = true;\n")
            (source / "tsconfig.json").write_text("{}\n")
            repo_root = Path(__file__).resolve().parents[2]
            tsc_path = root / "node_modules" / "typescript" / "bin" / "tsc"
            tsc_path.parent.mkdir(parents=True)
            tsc_path.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            mock_repo_tsc_path.return_value = tsc_path

            _compile_typescript_sources(source, output)

        mock_run.assert_called_once_with(
            [
                "bun",
                str(tsc_path),
                "--project",
                str(source / "tsconfig.json"),
                "--outDir",
                str(output),
                "--rootDir",
                str(source),
            ],
            check=True,
            cwd=repo_root,
        )

    @patch("tools.dev.typescript.subprocess.run")
    @patch("tools.dev.typescript.resolve_runner")
    @patch("tools.dev.typescript._repo_tsc_path")
    def test_extension_compile_typescript_sources_uses_npm_exec_fallback(
        self,
        mock_repo_tsc_path,
        mock_resolve_runner,
        mock_run,
    ):
        mock_resolve_runner.return_value = RunnerChoice(name="npm", command_prefix=("npm", "run"))

        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            source = root / "apps" / "extension"
            output = root / "build" / "extension"
            source.mkdir(parents=True)
            output.mkdir(parents=True)
            (source / "popup_script.ts").write_text("const ready = true;\n")
            (source / "tsconfig.json").write_text("{}\n")
            tsc_path = root / "node_modules" / "typescript" / "bin" / "tsc"
            tsc_path.parent.mkdir(parents=True)
            tsc_path.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            mock_repo_tsc_path.return_value = tsc_path

            _compile_typescript_sources(source, output)

        repo_root = Path(__file__).resolve().parents[2]
        mock_run.assert_called_once_with(
            [
                "npm",
                "exec",
                "--",
                "tsc",
                "--project",
                str(source / "tsconfig.json"),
                "--outDir",
                str(output),
                "--rootDir",
                str(source),
            ],
            check=True,
            cwd=repo_root,
        )
