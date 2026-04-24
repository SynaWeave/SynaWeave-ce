"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  rerun the bounded browser verification lane multiple times
to classify flake versus deterministic regression

- Later Extension Points:
    --> add artifact collation only when repeated browser triage
        needs more durable evidence capture

- Role:
    --> runs the repo browser verification command repeatedly
    --> stops early on the first failure
    --> prints a compact pass or fail summary for operators

- Exports:
    --> `main()`

- Consumed By:
    --> `bun run triage:browser:repeat`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import subprocess
from typing import Sequence

from tools.dev import js_run

DEFAULT_RUNS = 3


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repeat browser verification for triage")
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_RUNS,
        help="Number of repeated browser verification runs",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    browser_command = js_run.build_command(
        "verify:browser",
        (),
        runner=js_run.resolve_runner(),
    )

    for index in range(1, args.runs + 1):
        print(f"triage browser repeat run {index}/{args.runs}")
        result = subprocess.run(browser_command, check=False)

        if result.returncode != 0:
            print(f"browser triage failed on run {index}/{args.runs}")
            return result.returncode

    print(f"browser triage passed {args.runs}/{args.runs} runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
