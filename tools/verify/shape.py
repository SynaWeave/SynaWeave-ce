"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the governed repository topology shape and required scaffold directories

- Later Extension Points:
    --> add more topology assertions only when new top-level surfaces become durable

- Role:
    --> checks required directories workspace patterns and testing taxonomy folders
    --> blocks legacy prototype files and platform-generated noise from returning

- Exports:
    --> `check_shape()`

- Consumed By:
    --> `tools.verify.main` during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
from pathlib import Path
from typing import List

REQUIRED_TOP_LEVEL_DIRS = [
    "apps",
    "docs",
    "infra",
    "packages",
    "python",
    "testing",
    "tools",
    ".github",
]


REQUIRED_APP_DIRS = {
    "extension",
    "web",
    "api",
    "ingest",
    "mcp",
    "ml",
    "eval",
}


REQUIRED_WORKSPACE_PATTERNS = {
    "apps/*",
    "packages/*",
    "python/*",
    "infra/*",
    "testing/*",
    "tools/*",
}


REQUIRED_TESTING_DIRS = {
    "unit",
    "component",
    "integration",
    "contract",
    "ui",
    "e2e",
    "security",
    "performance",
    "accessibility",
    "evals",
}


FORBIDDEN_ROOT_FILES = {
    "manifest.json",
    "background.js",
    "foreground.js",
    "popup.html",
    "popup_script.js",
    "options.html",
    "options_script.js",
    "styles.css",
    "stylez.css",
}


FORBIDDEN_REPO_NOISE = {
    ".DS_Store",
}


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def check_shape(repo_root: Path) -> List[str]:
    issues: List[str] = []

    for directory in REQUIRED_TOP_LEVEL_DIRS:
        path = repo_root / directory
        if not path.exists():
            _add_issue(issues, f"missing required top-level directory: {directory}")
            continue
        if not path.is_dir():
            _add_issue(issues, f"top-level entry is not a directory: {directory}")

    apps_root = repo_root / "apps"
    for name in sorted(REQUIRED_APP_DIRS):
        app_path = apps_root / name
        if not app_path.exists():
            _add_issue(issues, f"missing required app directory: apps/{name}")
            continue
        if not app_path.is_dir():
            _add_issue(issues, f"required app home is not a directory: apps/{name}")

    for name in FORBIDDEN_ROOT_FILES:
        if (repo_root / name).exists():
            _add_issue(
                issues,
                f"forbidden prototype file still at repository root: {name}",
            )

    for noise_name in FORBIDDEN_REPO_NOISE:
        for path in sorted(repo_root.rglob(noise_name)):
            if ".git" in path.parts:
                continue
            _add_issue(
                issues,
                "forbidden platform-generated repo noise present: "
                f"{path.relative_to(repo_root)}",
            )

    if (repo_root / "apps" / "docs").exists():
        _add_issue(issues, "Sprint 1 forbids docs runtime under apps/docs")

    testing_root = repo_root / "testing"
    if testing_root.exists() and testing_root.is_dir():
        missing_testing_dirs = sorted(
            name for name in REQUIRED_TESTING_DIRS if not (testing_root / name).exists()
        )
        for name in missing_testing_dirs:
            _add_issue(issues, f"missing required testing directory: testing/{name}")

    package_path = repo_root / "package.json"
    if not package_path.exists():
        _add_issue(issues, "package.json is required for workspace bootstrap")
    else:
        try:
            package_data = json.loads(package_path.read_text())
        except json.JSONDecodeError as exc:
            _add_issue(issues, f"package.json is not valid JSON: {exc}")
        else:
            workspaces = package_data.get("workspaces", [])
            missing = sorted(REQUIRED_WORKSPACE_PATTERNS.difference(set(workspaces)))
            if missing:
                _add_issue(
                    issues,
                    "package.json workspaces missing required entries: "
                    + ", ".join(missing),
                )

            scripts = package_data.get("scripts", {})
            if "verify" not in scripts:
                _add_issue(issues, "package.json must define a verify script")

    return issues
