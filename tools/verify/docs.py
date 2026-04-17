"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the governed root docs spine and required template surfaces stay aligned

- Later Extension Points:
    --> widen docs checks only when new root docs or template families become governed

- Role:
    --> checks required root documentation files and directories
    --> blocks docs-runtime drift and nested README duplication in the governed docs spine

- Exports:
    --> `check_docs()`

- Consumed By:
    --> `tools.verify.main` during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List

from tools.verify.policy import REQUIRED_TEMPLATE_FILES, ROOT_DOC_FILES

REQUIRED_DOC_FILES = set(ROOT_DOC_FILES)


REQUIRED_PLANNING_FILES = {
    Path("planning") / "MASTER.md",
    Path("planning") / "sprint-001" / "overview.md",
    Path("planning") / "sprint-001" / "d1-foundation.md",
    Path("planning") / "sprint-001" / "d2-runtime.md",
    Path("planning") / "sprint-001" / "d3-quality.md",
}


REQUIRED_TEMPLATE_DIRS = {
    Path("templates") / "planning",
    Path("templates") / "adrs",
    Path("templates") / "specs",
    Path("templates") / "tests",
}


REQUIRED_ADR_PATTERN = "sprint-###.md"

FORBIDDEN_DOCS_RUNTIME_RE = re.compile(r"\bapps/docs\b")

DOCS_RUNTIME_ALLOWLIST = {
    Path("AGENTS.md"),
    Path(".github/pull_request_template.md"),
    Path("tools/verify/docs.py"),
    Path("testing/unit/test_verify_docs.py"),
}

IGNORED_DOCS_PATH_PARTS = {".git", "node_modules", ".venv", "venv"}


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _check_required_files(
    repo_root: Path,
    files: Iterable[Path],
    issues: List[str],
) -> None:
    for path in files:
        full_path = repo_root / "docs" / path
        if not full_path.exists():
            _add_issue(issues, f"missing required docs file: docs/{path}")


def _check_required_dirs(repo_root: Path, issues: List[str]) -> None:
    docs_dir = repo_root / "docs"
    if not docs_dir.exists() or not docs_dir.is_dir():
        _add_issue(issues, "docs directory is missing")
        return

    required_dirs = {
        docs_dir,
        docs_dir / "adrs",
        docs_dir / "planning",
        docs_dir / "templates",
    }
    for required_dir in required_dirs:
        if not required_dir.exists() or not required_dir.is_dir():
            rel = str(required_dir.relative_to(repo_root))
            _add_issue(issues, f"missing required directory: {rel}")


def _check_forbidden_docs_runtime_mentions(repo_root: Path, issues: List[str]) -> None:
    for path in sorted(repo_root.rglob("*.md")):
        relative_path = path.relative_to(repo_root)
        if any(part in IGNORED_DOCS_PATH_PARTS for part in relative_path.parts):
            continue
        if relative_path in DOCS_RUNTIME_ALLOWLIST:
            continue
        text = path.read_text()
        if FORBIDDEN_DOCS_RUNTIME_RE.search(text):
            _add_issue(
                issues,
                f"human-facing docs must not describe apps/docs as a runtime: {relative_path}",
            )


def _check_planning_pointer(repo_root: Path, issues: List[str]) -> None:
    planning_pointer = repo_root / "docs" / "planning.md"
    if not planning_pointer.exists():
        return
    text = planning_pointer.read_text()
    if "compatibility pointer" not in text:
        _add_issue(issues, "docs/planning.md must remain a compatibility pointer")
    if "docs/planning/MASTER.md" not in text:
        _add_issue(issues, "docs/planning.md must point readers to docs/planning/MASTER.md")


def _check_single_readme(repo_root: Path, issues: List[str]) -> None:
    readme_paths = sorted(
        path.relative_to(repo_root)
        for path in repo_root.rglob("README.md")
        if not any(part in IGNORED_DOCS_PATH_PARTS for part in path.relative_to(repo_root).parts)
    )
    if readme_paths != [Path("README.md")]:
        visible = ", ".join(path.as_posix() for path in readme_paths) or "none"
        _add_issue(
            issues,
            "repository must contain only the root README.md; found: " + visible,
        )


def check_docs(repo_root: Path) -> List[str]:
    issues: List[str] = []
    docs_dir = repo_root / "docs"

    _check_required_files(repo_root, [Path(path) for path in REQUIRED_DOC_FILES], issues)

    _check_required_dirs(repo_root, issues)

    for relative in REQUIRED_PLANNING_FILES:
        planning_file = docs_dir / relative
        if not planning_file.exists():
            _add_issue(issues, f"missing required planning file: docs/{relative}")

    for template_dir in REQUIRED_TEMPLATE_DIRS:
        full_dir = docs_dir / template_dir
        if not full_dir.exists():
            _add_issue(issues, f"missing required docs template dir: docs/{template_dir}")

    for template_file in REQUIRED_TEMPLATE_FILES:
        full_path = docs_dir / "templates" / template_file
        if not full_path.exists():
            _add_issue(issues, f"missing required template file: docs/templates/{template_file}")

    _check_forbidden_docs_runtime_mentions(repo_root, issues)
    _check_planning_pointer(repo_root, issues)
    _check_single_readme(repo_root, issues)

    return issues
