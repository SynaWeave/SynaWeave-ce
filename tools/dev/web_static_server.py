"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  serve the static web shell from already-built browser assets

- Later Extension Points:
    --> add bounded static-server behavior only when more repo-owned
        browser assets need proof-serving support

- Role:
    --> serves generated web artifacts for local runtime proof and browser automation
    --> relies on the owned web build flow to emit browser-ready JavaScript before static serving

- Exports:
    --> CLI module entry only

- Consumed By:
    --> `package.json` dev web script, `playwright.config.ts`, and `tools.verify_browser`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(args.directory),
    )
    with socketserver.TCPServer((args.host, args.port), handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
