"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  validate governed pull-request titles and bodies through one shared review policy module

- Later Extension Points:
    --> add more PR-quality checks only when shared review policy expands later

- Role:
    --> validates PR titles against the governed change grammar without sprint-style prefixes
    --> checks PR bodies for the required review and CLA content without duplicating CI YAML logic

- Exports:
    --> `validate_pr_title()`
    --> `validate_pr_body()`
    --> `main()`

- Consumed By:
    --> GitHub PR-quality workflow and unit tests that enforce review policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import os
import sys
from typing import List

from tools.verify.commit import validate_pr_title_message
from tools.verify.policy import PR_TEMPLATE_REQUIRED_FIELDS


def validate_pr_title(title: str) -> List[str]:
    normalized_title = title.strip()
    if not normalized_title:
        return ["PR title must not be empty"]
    return [
        issue.replace("commit subject", "PR title subject")
        for issue in validate_pr_title_message(normalized_title)
    ]


def validate_pr_body(body: str) -> List[str]:
    issues: List[str] = []
    for value in PR_TEMPLATE_REQUIRED_FIELDS:
        if value not in body:
            issues.append(f"PR body missing required content: {value}")
    return issues


def main() -> int:
    title = os.environ.get("PR_TITLE", "")
    body = os.environ.get("PR_BODY", "")
    issues = [*validate_pr_title(title), *validate_pr_body(body)]
    if issues:
        for issue in issues:
            print(issue)
        return 1

    print("PR title and description satisfy the repository quality gates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
