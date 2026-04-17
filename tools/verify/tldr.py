"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  format repository verification findings into a compact operator-facing summary

- Later Extension Points:
    --> add richer summary grouping only if verifier output needs more than bounded samples

- Role:
    --> aggregates verification issues by checker name
    --> emits a readable pass or fail summary for repository verification runs

- Exports:
    --> `summarize_issues()`

- Consumed By:
    --> `tools.verify.main` when printing repository verification output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

from collections import Counter
from typing import List, Tuple


def summarize_issues(issues: List[Tuple[str, str]]) -> List[str]:
    if not issues:
        return ["Verification summary: PASS (0 issues)"]

    counts = Counter([name for name, _ in issues])
    lines: List[str] = ["Verification summary:"]
    for name, count in sorted(counts.items()):
        lines.append(f"- {name}: {count} issue(s)")

    lines.append("Sample findings:")
    for name, message in issues[:10]:
        lines.append(f"- {name}: {message}")

    return lines
