"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify browser orchestration chooses free localhost ports
and marks Playwright runs as externally managed

- Later Extension Points:
    --> add more server startup coverage only when browser
        orchestration grows beyond the bounded API and web listeners

- Role:
    --> covers dynamic localhost port selection for browser verification
    --> covers Playwright environment wiring for repo-managed server runs

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
from unittest.mock import patch

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
                command=("python3", "-m", "http.server", "3000"),
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
    def test_run_browser_command_marks_playwright_servers_as_managed(self, mock_run):
        mock_run.return_value.returncode = 0

        exit_code = verify_browser._run_browser_command(
            Path.cwd(),
            "test:e2e:prepared",
            api_port=41001,
            web_port=41002,
        )

        self.assertEqual(exit_code, 0)
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["env"]["PLAYWRIGHT_MANAGED_SERVERS"], "1")
        self.assertEqual(kwargs["env"]["PLAYWRIGHT_API_PORT"], "41001")
        self.assertEqual(
            kwargs["env"]["PLAYWRIGHT_API_BASE_URL"],
            "http://127.0.0.1:41001",
        )
        self.assertEqual(kwargs["env"]["PLAYWRIGHT_WEB_PORT"], "41002")
        self.assertEqual(
            kwargs["env"]["PLAYWRIGHT_BASE_URL"],
            "http://127.0.0.1:41002",
        )


if __name__ == "__main__":
    unittest.main()
