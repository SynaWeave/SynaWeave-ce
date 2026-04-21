"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the bounded browser verification lane
with deterministic local server startup and teardown

- Later Extension Points:
    --> add more governed local browser surfaces only when
        Sprint verification expands beyond the API and web shell
    --> capture richer failure artifacts only when local browser
        debugging needs more durable evidence

- Role:
    --> reuse already-running local API and web servers when available
    --> start and tear down bounded local servers when browser
        verification needs them
    --> run the prepared Playwright browser and accessibility suites
        against one deterministic local runtime

- Exports:
    --> `main()`

- Consumed By:
    --> `bun run verify:browser`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import subprocess
import time
import urllib.error
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import IO

READY_TIMEOUT_SECONDS = 120.0
READY_POLL_SECONDS = 0.5
LOG_TAIL_BYTES = 4000


@dataclass(frozen=True)
class ServerSpec:
    name: str
    command: tuple[str, ...]
    ready_url: str
    log_path: Path


@dataclass
class StartedServer:
    spec: ServerSpec
    process: subprocess.Popen
    log_handle: IO[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _server_specs(repo_root: Path) -> tuple[ServerSpec, ...]:
    log_dir = repo_root / "build" / "verify-browser"
    log_dir.mkdir(parents=True, exist_ok=True)

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
                "8000",
            ),
            ready_url="http://127.0.0.1:8000/health/ready",
            log_path=log_dir / "api.log",
        ),
        ServerSpec(
            name="web",
            command=("python3", "-m", "http.server", "3000", "--directory", "apps/web"),
            ready_url="http://127.0.0.1:3000",
            log_path=log_dir / "web.log",
        ),
    )


def _is_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.0) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


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


def _start_server(server: ServerSpec, repo_root: Path) -> StartedServer | None:
    if _is_ready(server.ready_url):
        print(f"Reusing existing {server.name} server at {server.ready_url}")
        return None

    log_handle = server.log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        server.command,
        cwd=repo_root,
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


def _run_browser_command(repo_root: Path, script_name: str) -> int:
    command = ("bun", "run", script_name)
    print(f"$ {' '.join(command)}")

    result = subprocess.run(command, cwd=repo_root, check=False)
    return result.returncode


def main() -> int:
    repo_root = _repo_root()
    started_servers: list[StartedServer] = []

    try:
        for server in _server_specs(repo_root):
            started = _start_server(server, repo_root)
            if started is not None:
                started_servers.append(started)

        for script_name in ("test:e2e:prepared", "test:accessibility:prepared"):
            exit_code = _run_browser_command(repo_root, script_name)
            if exit_code != 0:
                for started in started_servers:
                    _print_log_excerpt(started.spec)
                return exit_code

        return 0
    finally:
        _stop_servers(started_servers)


if __name__ == "__main__":
    raise SystemExit(main())
