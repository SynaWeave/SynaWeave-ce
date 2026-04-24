"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the bounded browser verification lane
with deterministic local server startup and teardown

- Later Extension Points:
    --> add more governed local browser surfaces only when
        Sprint verification expands beyond the API and web shell
    --> capture richer failure artifacts only when local browser
        debugging needs more durable evidence

- Role:
    --> start and tear down bounded repo-owned local servers for browser
        verification
    --> fail fast when the expected browser verification ports are already
        occupied by another listener
    --> run the prepared Playwright browser and accessibility suites
        against one deterministic local runtime

- Exports:
    --> `main()`

- Consumed By:
    --> `bun run verify:browser`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import IO

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from tools.dev.js_run import build_command, resolve_runner

READY_TIMEOUT_SECONDS = 120.0
READY_POLL_SECONDS = 0.5
LOG_TAIL_BYTES = 4000
MANAGED_CHROMIUM_POLICY_DIR = Path("/etc/chromium/policies/managed")
SYSTEM_CHROMIUM_CANDIDATES = ("chromium", "google-chrome", "google-chrome-stable")
PLAYWRIGHT_BROWSER_DIR_NAMES = (
    "chrome-linux",
    "chrome-linux64",
    "chrome-mac",
    "chrome-mac-arm64",
    "chrome-win",
    "chrome-win64",
)


@dataclass(frozen=True)
class ServerSpec:
    name: str
    command: tuple[str, ...]
    port: int
    ready_url: str
    log_path: Path
    env: dict[str, str] | None = None


@dataclass
class StartedServer:
    spec: ServerSpec
    process: subprocess.Popen[str]
    log_handle: IO[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _server_specs(repo_root: Path) -> tuple[ServerSpec, ...]:
    log_dir = repo_root / "build" / "verify-browser"
    log_dir.mkdir(parents=True, exist_ok=True)
    api_port = _pick_free_port()
    web_port = _pick_free_port(excluded_ports={api_port})
    api_base_url = f"http://127.0.0.1:{api_port}"
    web_base_url = f"http://127.0.0.1:{web_port}"

    return (
        ServerSpec(
            name="api",
            command=(
                "python3",
                "-m",
                "uvicorn",
                "apps.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(api_port),
            ),
            port=api_port,
            ready_url=f"{api_base_url}/health/ready",
            log_path=log_dir / "api.log",
            env={"SYNAWAVE_WEB_BASE_URL": web_base_url},
        ),
        ServerSpec(
            name="web",
            command=(
                "python3",
                "-m",
                "tools.dev.web_static_server",
                "--port",
                str(web_port),
                "--directory",
                "build/web",
            ),
            port=web_port,
            ready_url=web_base_url,
            log_path=log_dir / "web.log",
        ),
    )


def _is_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.0) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def _is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _pick_free_port(*, excluded_ports: set[int] | None = None) -> int:
    excluded = excluded_ports or set()

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen()
            port = int(sock.getsockname()[1])
        if port not in excluded:
            return port


def _wait_until_ready(server: ServerSpec) -> None:
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        if _is_ready(server.ready_url):
            return
        time.sleep(READY_POLL_SECONDS)

    raise RuntimeError(
        f"{server.name} server did not become ready at {server.ready_url}",
    )


def _print_log_excerpt(server: ServerSpec) -> None:
    if not server.log_path.is_file():
        return

    content = server.log_path.read_text(encoding="utf-8", errors="replace")
    excerpt = content[-LOG_TAIL_BYTES:]

    print(f"----- {server.name} log tail -----")
    print(excerpt)
    print(f"----- end {server.name} log tail -----")


def _start_server(server: ServerSpec, repo_root: Path) -> StartedServer:
    if _is_port_open(server.port):
        raise RuntimeError(
            f"{server.name} port 127.0.0.1:{server.port} is already occupied; "
            "verify:browser requires repo-owned servers and will not reuse an existing listener",
        )

    log_handle = server.log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        server.command,
        cwd=repo_root,
        env={**os.environ, **(server.env or {})},
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    started = StartedServer(spec=server, process=process, log_handle=log_handle)

    try:
        _wait_until_ready(server)
    except Exception:
        _stop_servers([started])
        _print_log_excerpt(server)
        raise

    print(f"Started {server.name} server at {server.ready_url}")
    return started


def _stop_servers(started_servers: list[StartedServer]) -> None:
    for started in reversed(started_servers):
        process = started.process

        if process.poll() is None:
            with suppress(ProcessLookupError):
                process.terminate()

            with suppress(subprocess.TimeoutExpired):
                process.wait(timeout=5)

            if process.poll() is None:
                with suppress(ProcessLookupError):
                    process.kill()

                with suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=5)

        started.log_handle.close()


def _iter_managed_policy_files() -> Sequence[Path]:
    if not MANAGED_CHROMIUM_POLICY_DIR.is_dir():
        return ()
    return tuple(sorted(MANAGED_CHROMIUM_POLICY_DIR.glob("*.json")))


def _managed_policy_blocks_browser() -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for policy_path in _iter_managed_policy_files():
        try:
            payload_obj: object = json.loads(policy_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload_obj, dict):
            continue
        payload: dict[object, object] = payload_obj
        if payload.get("URLBlocklist") == ["*"]:
            reasons.append(f"{policy_path}: URLBlocklist=*")
        if payload.get("ExtensionInstallBlocklist") == ["*"]:
            reasons.append(f"{policy_path}: ExtensionInstallBlocklist=*")
    return bool(reasons), reasons


def managed_policy_blocks_browser() -> tuple[bool, list[str]]:
    return _managed_policy_blocks_browser()


def _playwright_browser_installed() -> bool:
    cache_dir = _playwright_cache_dir()
    if cache_dir is None or not cache_dir.is_dir():
        return False
    return any(
        path.is_dir()
        for browser_dir in PLAYWRIGHT_BROWSER_DIR_NAMES
        for path in cache_dir.glob(f"**/{browser_dir}")
    )


def _playwright_cache_dir(*, environ: dict[str, str] | None = None) -> Path | None:
    environment = os.environ if environ is None else environ
    configured_path = environment.get("PLAYWRIGHT_BROWSERS_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "ms-playwright"
    if sys.platform == "win32":
        local_app_data = environment.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "ms-playwright"
        return Path.home() / "AppData" / "Local" / "ms-playwright"
    return Path.home() / ".cache" / "ms-playwright"


def _detect_system_chromium() -> str | None:
    for candidate in SYSTEM_CHROMIUM_CANDIDATES:
        path = shutil.which(candidate)
        if path is not None:
            return path
    return None


def _prepare_browser_environment(*, api_port: int, web_port: int) -> dict[str, str]:
    repo_root = _repo_root()
    environment = dict(os.environ)
    environment["PLAYWRIGHT_MANAGED_SERVERS"] = "1"
    environment["PLAYWRIGHT_API_PORT"] = str(api_port)
    environment["PLAYWRIGHT_API_BASE_URL"] = f"http://127.0.0.1:{api_port}"
    environment["PLAYWRIGHT_WEB_PORT"] = str(web_port)
    environment["PLAYWRIGHT_BASE_URL"] = f"http://127.0.0.1:{web_port}"
    output_dir = repo_root / "build" / "verify-browser" / f"playwright-{int(time.time() * 1000)}"
    output_dir.mkdir(parents=True, exist_ok=True)
    environment["PLAYWRIGHT_OUTPUT_DIR"] = str(output_dir)

    if environment.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH") or environment.get("CHROMIUM_BIN"):
        return environment

    if _playwright_browser_installed():
        return environment

    system_chromium = _detect_system_chromium()
    if system_chromium is None:
        message = "".join(
            [
                "No Playwright-managed Chromium install was found and no system Chromium ",
                "binary is available. Run the browser installer in a connected environment ",
                "or set PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH explicitly.",
            ]
        )
        raise RuntimeError(
            message
        )

    blocked, reasons = _managed_policy_blocks_browser()
    if blocked:
        reason_text = "; ".join(reasons)
        message = "".join(
            [
                "System Chromium is present but managed policies block repo browser ",
                f"verification. Detected: {reason_text}. Remove or override those policies ",
                "for this environment, or provide a Playwright-managed Chromium binary.",
            ]
        )
        raise RuntimeError(
            message
        )

    environment["PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"] = system_chromium
    return environment


def prepare_browser_environment(*, api_port: int, web_port: int) -> dict[str, str]:
    return _prepare_browser_environment(api_port=api_port, web_port=web_port)


def _run_browser_command(
    repo_root: Path,
    script_name: str,
    *,
    api_port: int,
    web_port: int,
) -> int:
    runner = resolve_runner()
    command = build_command(script_name, (), runner=runner)
    print(f"$ {' '.join(command)}")

    environment = _prepare_browser_environment(api_port=api_port, web_port=web_port)
    result = subprocess.run(command, cwd=repo_root, check=False, env=environment)
    return result.returncode


def main() -> int:
    repo_root = _repo_root()
    started_servers: list[StartedServer] = []

    try:
        for server in _server_specs(repo_root):
            started = _start_server(server, repo_root)
            started_servers.append(started)

        api_server = next(server for server in started_servers if server.spec.name == "api")
        web_server = next(server for server in started_servers if server.spec.name == "web")

        for script_name in ("test:e2e:prepared", "test:accessibility:prepared"):
            exit_code = _run_browser_command(
                repo_root,
                script_name,
                api_port=api_server.spec.port,
                web_port=web_server.spec.port,
            )
            if exit_code != 0:
                for started in started_servers:
                    _print_log_excerpt(started.spec)
                return exit_code

        return 0
    finally:
        _stop_servers(started_servers)


if __name__ == "__main__":
    raise SystemExit(main())
