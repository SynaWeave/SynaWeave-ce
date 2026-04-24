"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify web artifact building keeps source authoritative
while serving generated output

- Later Extension Points:
    --> widen build coverage only when the web shell grows
        beyond plain copied assets plus TypeScript output

- Role:
    --> builds temp web artifacts from sample source files
    --> checks that runtime HTML and CSS copy while TypeScript
        emits JavaScript into the build output

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
from tools.web.build import _compile_typescript_sources, build_web


class TestWebBuild(unittest.TestCase):
    def test_build_web_copies_static_assets_and_calls_typescript_compile(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            source = root / "apps" / "web"
            output = root / "build" / "web"
            index_html = (
                '<!DOCTYPE html>\n<link rel="stylesheet" href="./styles.css">\n'
                '<script src="./app.js"></script>\n'
            )
            source.mkdir(parents=True)
            _ = (source / "index.html").write_text(index_html)
            _ = (source / "styles.css").write_text("body { color: green; }\n")
            _ = (source / "app.ts").write_text("const ready = true;\n")

            with patch("tools.web.build._compile_typescript_sources") as mock_compile:
                build_web(source, output)

            self.assertEqual(
                (output / "index.html").read_text(),
                index_html,
            )
            self.assertEqual(
                (output / "styles.css").read_text(),
                "body { color: green; }\n",
            )
            self.assertFalse((output / "app.ts").exists())
            mock_compile.assert_called_once_with(source, output)

    @patch("tools.dev.typescript.subprocess.run")
    @patch("tools.dev.typescript.resolve_runner")
    @patch("tools.dev.typescript._repo_tsc_path")
    def test_compile_typescript_sources_uses_governed_bun_runner(
        self,
        mock_repo_tsc_path,
        mock_resolve_runner,
        mock_run,
    ):
        mock_resolve_runner.return_value = RunnerChoice(name="bun", command_prefix=("bun", "run"))

        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            source = root / "apps" / "web"
            output = root / "build" / "web"
            source.mkdir(parents=True)
            output.mkdir(parents=True)
            (source / "app.ts").write_text("const ready = true;\n")
            (source / "tsconfig.build.json").write_text("{}\n")
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
                str(source / "tsconfig.build.json"),
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
    def test_compile_typescript_sources_uses_npm_exec_fallback(
        self,
        mock_repo_tsc_path,
        mock_resolve_runner,
        mock_run,
    ):
        mock_resolve_runner.return_value = RunnerChoice(name="npm", command_prefix=("npm", "run"))

        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            source = root / "apps" / "web"
            output = root / "build" / "web"
            source.mkdir(parents=True)
            output.mkdir(parents=True)
            (source / "app.ts").write_text("const ready = true;\n")
            (source / "tsconfig.build.json").write_text("{}\n")
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
                str(source / "tsconfig.build.json"),
                "--outDir",
                str(output),
                "--rootDir",
                str(source),
            ],
            check=True,
            cwd=repo_root,
        )


if __name__ == "__main__":
    _ = unittest.main()
