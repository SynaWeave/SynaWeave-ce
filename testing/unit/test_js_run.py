"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify governed JS runner selection keeps Bun first and npm as the bounded fallback

- Later Extension Points:
    --> add more runner coverage only when another durable JS runner is adopted

- Role:
    --> checks runner resolution behavior and package-script command assembly
    --> keeps npm fallback intentional instead of accidental drift

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import unittest
from unittest.mock import patch

from tools.dev import js_run


def bun_and_npm_paths(name: str) -> str | None:
    return {
        "bun": "/usr/bin/bun",
        "npm": "/usr/bin/npm",
    }.get(name)


def npm_path_only(name: str) -> str | None:
    return {"npm": "/usr/bin/npm"}.get(name)


class TestJsRun(unittest.TestCase):
    def test_resolve_runner_prefers_bun_when_available(self):
        with patch("tools.dev.js_run.shutil.which") as mock_which:
            mock_which.side_effect = bun_and_npm_paths

            runner = js_run.resolve_runner()

        self.assertEqual(runner.name, "bun")
        self.assertEqual(runner.command_prefix, ("bun", "run"))

    def test_resolve_runner_falls_back_to_npm_when_bun_missing(self):
        with patch("tools.dev.js_run.shutil.which") as mock_which:
            mock_which.side_effect = npm_path_only

            runner = js_run.resolve_runner()

        self.assertEqual(runner.name, "npm")
        self.assertEqual(runner.command_prefix, ("npm", "run"))

    def test_resolve_runner_honors_explicit_runner_override(self):
        with patch("tools.dev.js_run.shutil.which", return_value="/usr/bin/npm"):
            runner = js_run.resolve_runner(environ={js_run.ENV_RUNNER_NAME: "npm"})

        self.assertEqual(runner.name, "npm")

    def test_build_command_uses_npm_argument_separator_for_script_args(self):
        runner = js_run.RunnerChoice(name="npm", command_prefix=("npm", "run"))

        command = js_run.build_command("test:e2e", ("--grep", "web shell"), runner=runner)

        self.assertEqual(command, ("npm", "run", "test:e2e", "--", "--grep", "web shell"))


if __name__ == "__main__":
    _ = unittest.main()
