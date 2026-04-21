"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  print whether the bounded local browser verification ports
are already occupied before running Playwright triage flows

- Later Extension Points:
    --> add richer process metadata only when local browser triage
        needs more durable operator hints

- Role:
    --> checks whether ports 8000 and 3000 are already listening
    --> prints a fast operator-facing status summary
    --> exits successfully because this is a triage helper, not a gate

- Exports:
    --> `main()`

- Consumed By:
    --> `bun run triage:ports`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class PortCheck:
    port: int
    label: str


PORTS = (
    PortCheck(port=8000, label="api"),
    PortCheck(port=3000, label="web"),
)


def _is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    print("browser triage port summary")

    for check in PORTS:
        state = "occupied" if _is_port_open(check.port) else "free"
        print(f"- {check.label}: 127.0.0.1:{check.port} -> {state}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
