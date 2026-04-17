"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify source HTML comments stay non-sensitive and shipped extension HTML strips them

- Later Extension Points:
    --> widen client-ship checks only when more governed HTML artifact paths become real later

- Role:
    --> scans source HTML comments for sensitive content that must never live in client comments
    --> builds a temp extension artifact and rejects shipped HTML that still contains comments

- Exports:
    --> `check_html_ship()`

- Consumed By:
    --> `tools.verify.main` and repo verification scripts guarding ship-facing HTML surfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import List

from tools.extension.build import HTML_COMMENT_RE, build_extension

SENSITIVE_HTML_COMMENT_RE = re.compile(
    r"secret|token|password|credential|private key|service role|internal-only|admin bypass",
    re.IGNORECASE,
)


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _check_source_comments(repo_root: Path, issues: List[str]) -> None:
    # Check source HTML directly so comment-heavy notes stay allowed but never hold sensitive theory
    for path in sorted((repo_root / "apps" / "extension").glob("*.html")):
        for match in HTML_COMMENT_RE.finditer(path.read_text()):
            if SENSITIVE_HTML_COMMENT_RE.search(match.group(0)):
                _add_issue(
                    issues,
                    "HTML source comments must not contain sensitive ship-facing theory: "
                    f"{path.relative_to(repo_root)}",
                )


def _check_built_artifacts(repo_root: Path, issues: List[str]) -> None:
    # Build into a temp directory during verification
    # CI proves stripping without dirtying the repo
    with tempfile.TemporaryDirectory() as raw_tmp:
        output_dir = Path(raw_tmp) / "extension"
        build_extension(repo_root / "apps" / "extension", output_dir)
        for path in sorted(output_dir.glob("*.html")):
            if HTML_COMMENT_RE.search(path.read_text()):
                _add_issue(
                    issues,
                    f"built extension HTML must strip all comments before shipping: {path.name}",
                )


def check_html_ship(repo_root: Path) -> List[str]:
    issues: List[str] = []
    _check_source_comments(repo_root, issues)
    _check_built_artifacts(repo_root, issues)
    return issues
