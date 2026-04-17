"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the governed repository verification stack and emit human or JSON results

- Later Extension Points:
    --> register new verifier lanes only when they become durable default repo-control checks

- Role:
    --> parses verification arguments and dispatches the active verifier checks
    --> collects issues into one summary path for local and CI-safe repository verification

- Exports:
    --> `run_verification()`
    --> `main()`

- Consumed By:
    --> local operators hooks and CI workflows running repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.verify.adr import check_adrs
from tools.verify.commentary import check_commentary
from tools.verify.commit import check_commit_head
from tools.verify.docs import check_docs
from tools.verify.governance import check_governance
from tools.verify.headers import check_headers
from tools.verify.html_ship import check_html_ship
from tools.verify.security import check_security
from tools.verify.shape import check_shape
from tools.verify.suppressions import check_suppressions
from tools.verify.tldr import summarize_issues
from tools.verify.workflows import check_workflows

AVAILABLE_CHECKS = {
    "shape": check_shape,
    "docs": check_docs,
    "commentary": check_commentary,
    "governance": check_governance,
    "headers": check_headers,
    "security": check_security,
    "html_ship": check_html_ship,
    "adr": check_adrs,
    "workflows": check_workflows,
    "suppressions": check_suppressions,
    "commit": check_commit_head,
}

DEFAULT_CHECKS = [
    "shape",
    "docs",
    "commentary",
    "governance",
    "headers",
    "security",
    "html_ship",
    "adr",
    "workflows",
    "suppressions",
    "commit",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run repository verification checks")
    parser.add_argument(
        "--checks",
        default=",".join(DEFAULT_CHECKS),
        help="Comma-separated check names",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable output",
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    return parser.parse_args()


def _parse_check_names(raw: str):
    requested = [name.strip() for name in raw.split(",") if name.strip()]
    if not requested:
        return list(AVAILABLE_CHECKS.keys())

    unknown = [name for name in requested if name not in AVAILABLE_CHECKS]
    if unknown:
        raise ValueError(f"unknown checks: {', '.join(unknown)}")
    return requested


def run_verification(repo_root: Path, checks):
    issues = []
    for name in checks:
        checker = AVAILABLE_CHECKS[name]
        for message in checker(repo_root):
            issues.append((name, message))
    return issues


def main() -> int:
    args = _parse_args()
    repo_root = Path(args.root).resolve()

    try:
        requested = _parse_check_names(args.checks)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    issues = run_verification(repo_root, requested)
    summary = summarize_issues(issues)

    if args.json:
        payload = {
            "root": str(repo_root),
            "checks": [
                {"name": name, "message": message} for name, message in issues
            ],
            "status": "PASS" if not issues else "FAIL",
        }
        print(json.dumps(payload, indent=2))
        return 0 if not issues else 1

    for line in summary:
        print(line)

    if not issues:
        return 0

    print(f"Total failures: {len(issues)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
