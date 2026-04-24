"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify browser orchestration chooses free localhost ports
and prepares one governed browser runner environment

- Later Extension Points:
    --> add more server startup coverage only when browser
        orchestration grows beyond the bounded API and web listeners

- Role:
    --> covers dynamic localhost port selection for browser verification
    --> covers Playwright environment wiring and managed Chromium policy detection

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import socket
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

from tools import verify_browser


class TestVerifyBrowser(unittest.TestCase):
    def test_server_specs_choose_distinct_nondefault_ports(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            specs = verify_browser._server_specs(Path(raw_tmp))

        self.assertEqual([spec.name for spec in specs], ["api", "web"])
        self.assertNotEqual(specs[0].port, specs[1].port)
        self.assertNotEqual(specs[0].port, 8000)
        self.assertNotEqual(specs[1].port, 3000)
        self.assertEqual(
            specs[0].env,
            {"SYNAWAVE_WEB_BASE_URL": f"http://127.0.0.1:{specs[1].port}"},
        )
        self.assertEqual(
            specs[0].ready_url,
            f"http://127.0.0.1:{specs[0].port}/health/ready",
        )
        self.assertEqual(specs[1].ready_url, f"http://127.0.0.1:{specs[1].port}")

    def test_start_server_fails_fast_when_port_is_already_occupied(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            log_path = repo_root / "server.log"
            server = verify_browser.ServerSpec(
                name="web",
                command=(
                    "python3",
                    "-m",
                    "tools.dev.web_static_server",
                    "--port",
                    "3000",
                    "--directory",
                    "build/web",
                ),
                port=0,
                ready_url="http://127.0.0.1:3000",
                log_path=log_path,
            )

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", 0))
                sock.listen()
                occupied_server = verify_browser.ServerSpec(
                    name=server.name,
                    command=server.command,
                    port=sock.getsockname()[1],
                    ready_url=server.ready_url,
                    log_path=server.log_path,
                )

                with self.assertRaisesRegex(RuntimeError, "already occupied"):
                    verify_browser._start_server(occupied_server, repo_root)

            self.assertFalse(log_path.exists())

    @patch("tools.verify_browser.subprocess.run")
    @patch("tools.verify_browser.build_command")
    @patch("tools.verify_browser.resolve_runner")
    @patch("tools.verify_browser._prepare_browser_environment")
    def test_run_browser_command_marks_playwright_servers_as_managed(
        self,
        mock_prepare_environment: MagicMock,
        mock_resolve_runner: MagicMock,
        mock_build_command: MagicMock,
        mock_run: MagicMock,
    ):
        mock_prepare_environment.return_value = {
            "PLAYWRIGHT_MANAGED_SERVERS": "1",
            "PLAYWRIGHT_API_PORT": "41001",
            "PLAYWRIGHT_API_BASE_URL": "http://127.0.0.1:41001",
            "PLAYWRIGHT_WEB_PORT": "41002",
            "PLAYWRIGHT_BASE_URL": "http://127.0.0.1:41002",
        }
        mock_resolve_runner.return_value = object()
        mock_build_command.return_value = ("npm", "run", "test:e2e:prepared")
        run_result = mock_run.return_value
        run_result.returncode = 0

        exit_code = verify_browser._run_browser_command(
            Path.cwd(),
            "test:e2e:prepared",
            api_port=41001,
            web_port=41002,
        )

        self.assertEqual(exit_code, 0)
        mock_prepare_environment.assert_called_once_with(api_port=41001, web_port=41002)
        kwargs = cast(dict[str, dict[str, str]], mock_run.call_args.kwargs)
        self.assertEqual(kwargs["env"]["PLAYWRIGHT_MANAGED_SERVERS"], "1")
        self.assertEqual(kwargs["env"]["PLAYWRIGHT_API_PORT"], "41001")
        self.assertEqual(
            kwargs["env"]["PLAYWRIGHT_API_BASE_URL"],
            "http://127.0.0.1:41001",
        )
        self.assertEqual(kwargs["env"]["PLAYWRIGHT_WEB_PORT"], "41002")
        self.assertEqual(kwargs["env"]["PLAYWRIGHT_BASE_URL"], "http://127.0.0.1:41002")

    def test_managed_policy_detection_reports_global_blockers(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            policy_path = Path(raw_tmp) / "managed.json"
            policy_path.write_text(
                '{"URLBlocklist":["*"],"ExtensionInstallBlocklist":["*"]}\n',
                encoding="utf-8",
            )
            with patch(
                "tools.verify_browser._iter_managed_policy_files",
                return_value=(policy_path,),
            ):
                blocked, reasons = verify_browser.managed_policy_blocks_browser()

        self.assertTrue(blocked)
        self.assertEqual(len(reasons), 2)
        self.assertIn("URLBlocklist=*", reasons[0])
        self.assertIn("ExtensionInstallBlocklist=*", reasons[1])

    def test_playwright_browser_detection_uses_platform_cache_locations(self):
        cases = (
            (
                "darwin",
                {},
                lambda home: home / "Library" / "Caches" / "ms-playwright",
                "chrome-mac",
            ),
            (
                "linux",
                {},
                lambda home: home / ".cache" / "ms-playwright",
                "chrome-linux",
            ),
            (
                "win32",
                {"LOCALAPPDATA": "/tmp/local-app-data"},
                lambda _home: Path("/tmp/local-app-data") / "ms-playwright",
                "chrome-win",
            ),
        )

        for platform_name, environ, expected_cache_dir_factory, browser_dir_name in cases:
            with self.subTest(platform=platform_name), tempfile.TemporaryDirectory() as raw_tmp:
                home_dir = Path(raw_tmp)
                cache_dir = expected_cache_dir_factory(home_dir)
                browser_dir = cache_dir / "chromium-1234" / browser_dir_name
                browser_dir.mkdir(parents=True, exist_ok=True)

                with patch("tools.verify_browser.sys.platform", platform_name), patch(
                    "tools.verify_browser.Path.home",
                    return_value=home_dir,
                ), patch.dict("tools.verify_browser.os.environ", environ, clear=True):
                    self.assertEqual(verify_browser._playwright_cache_dir(), cache_dir)
                    self.assertTrue(verify_browser._playwright_browser_installed())

    def test_playwright_browser_detection_respects_configured_cache_dir(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch.dict(
            "tools.verify_browser.os.environ",
            {"PLAYWRIGHT_BROWSERS_PATH": raw_tmp},
            clear=True,
        ):
            browser_dir = Path(raw_tmp) / "chromium-1234" / "chrome-mac-arm64"
            browser_dir.mkdir(parents=True)

            self.assertEqual(verify_browser._playwright_cache_dir(), Path(raw_tmp))
            self.assertTrue(verify_browser._playwright_browser_installed())

    def test_prepare_browser_environment_uses_system_chromium_when_safe(self):
        with patch.dict("tools.verify_browser.os.environ", {}, clear=True), patch(
            "tools.verify_browser._playwright_browser_installed",
            return_value=False,
        ), patch(
            "tools.verify_browser._detect_system_chromium",
            return_value="/usr/bin/chromium",
        ), patch(
            "tools.verify_browser._managed_policy_blocks_browser",
            return_value=(False, []),
        ):
            environment = verify_browser.prepare_browser_environment(
                api_port=41001,
                web_port=41002,
            )

        self.assertEqual(
            environment["PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"],
            "/usr/bin/chromium",
        )
        self.assertEqual(environment["PLAYWRIGHT_BASE_URL"], "http://127.0.0.1:41002")


if __name__ == "__main__":
    _ = unittest.main()
