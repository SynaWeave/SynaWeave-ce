"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify governed repo-control ownership lines and pull-request template requirements

- Later Extension Points:
    --> add more governance assertions only when protected control surfaces expand

- Role:
    --> checks required governance files exist in the repository root
    --> validates pull-request template fields and CODEOWNERS coverage

- Exports:
    --> `check_governance()`

- Consumed By:
    --> `tools.verify.main` during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

from tools.verify.policy import (
    CODEOWNERS_REQUIRED_LINES,
    GOVERNED_GITHUB_POSTURE_PHRASES,
    GOVERNED_REQUIRED_STATUS_CHECKS,
    MIN_SUBJECT_WORDS,
    PR_TEMPLATE_REQUIRED_FIELDS,
    REQUIRED_DEV_DEPENDENCIES,
    REQUIRED_GOVERNANCE_FILES,
    REQUIRED_PACKAGE_SCRIPTS,
)

REQUIREMENTS_DEV_PIN_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+==[^\s#]+$")


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _read_python_dev_requirements(requirements_path: Path) -> tuple[str, ...]:
    requirements: list[str] = []
    for raw_line in requirements_path.read_text().splitlines():
        requirement = raw_line.strip()
        if not requirement or requirement.startswith("#"):
            continue
        requirements.append(requirement)
    return tuple(requirements)


def _check_package_controls(repo_root: Path, issues: List[str]) -> None:
    package_json_path = repo_root / "package.json"
    if not package_json_path.exists():
        _add_issue(issues, "missing required governance file: package.json")
        return

    package_data = json.loads(package_json_path.read_text())
    scripts = package_data.get("scripts", {})
    for name, expected in REQUIRED_PACKAGE_SCRIPTS.items():
        if scripts.get(name) != expected:
            _add_issue(issues, f"package.json script must match governed value for '{name}'")

    dev_dependencies = package_data.get("devDependencies", {})
    for name, expected in REQUIRED_DEV_DEPENDENCIES.items():
        if dev_dependencies.get(name) != expected:
            _add_issue(
                issues,
                f"package.json devDependency must pin '{name}' to '{expected}'",
            )

    tsconfig_path = repo_root / "tsconfig.json"
    if not tsconfig_path.exists():
        _add_issue(issues, "package.json controls require a root tsconfig.json")
        return

    json.loads(tsconfig_path.read_text())

    requirements_path = repo_root / "requirements-dev.txt"
    if not requirements_path.exists():
        _add_issue(issues, "missing required governance file: requirements-dev.txt")
        return

    requirements = _read_python_dev_requirements(requirements_path)
    if not requirements:
        _add_issue(
            issues,
            "requirements-dev.txt must define at least one exact 'name==version' pin "
            "for governed verification",
        )
        return

    for requirement in requirements:
        if not REQUIREMENTS_DEV_PIN_PATTERN.fullmatch(requirement):
            _add_issue(
                issues,
                "requirements-dev.txt must use exact 'name==version' pins for governed "
                f"verification: '{requirement}'",
            )


def check_governance(repo_root: Path) -> List[str]:
    issues: List[str] = []

    for name in sorted(REQUIRED_GOVERNANCE_FILES):
        path = repo_root / name
        if not path.exists():
            _add_issue(issues, f"missing required governance file: {name}")

    contributing = repo_root / "CONTRIBUTING.md"
    if contributing.exists():
        text = contributing.read_text()
        if "Conventional Commits" not in text and "conventional" not in text.lower():
            _add_issue(issues, "CONTRIBUTING.md must document commit format requirements")
        if f"minimum {MIN_SUBJECT_WORDS}" not in text:
            _add_issue(
                issues,
                "CONTRIBUTING.md must define the "
                f"{MIN_SUBJECT_WORDS}-word minimum subject rule",
            )
        if "plain English" not in text:
            _add_issue(issues, "CONTRIBUTING.md must document plain-English commit guidance")
        if "shared ban list" not in text:
            _add_issue(
                issues,
                "CONTRIBUTING.md must document the shared banned-word model "
                "for commits, PR titles, and ADRs",
            )
        if "docs(docs)" not in text or "test(testing)" not in text:
            _add_issue(
                issues,
                "CONTRIBUTING.md must document rejected umbrella commit and PR title scopes",
            )
        if "docs(adr)" not in text or "test(hooks)" not in text:
            _add_issue(
                issues,
                "CONTRIBUTING.md must document supported narrower scope examples "
                "for docs and tests",
            )
        if "sprint, deliverable, and task" not in text:
            _add_issue(
                issues,
                "CONTRIBUTING.md must require exact sprint, deliverable, and task targets "
                "for substantial work",
            )

    governance = repo_root / "GOVERNANCE.md"
    if governance.exists():
        governance_text = governance.read_text()
        for phrase in GOVERNED_GITHUB_POSTURE_PHRASES:
            if phrase not in governance_text:
                _add_issue(
                    issues,
                    "GOVERNANCE.md must document GitHub posture phrase: "
                    f"{phrase}",
                )
        for status_check in GOVERNED_REQUIRED_STATUS_CHECKS:
            if status_check not in governance_text:
                _add_issue(
                    issues,
                    "GOVERNANCE.md must document required default-branch hosted check: "
                    f"{status_check}",
                )

    pull_request_template = repo_root / ".github" / "pull_request_template.md"
    if pull_request_template.exists():
        template_text = pull_request_template.read_text()
        for field in PR_TEMPLATE_REQUIRED_FIELDS:
            if field not in template_text:
                _add_issue(
                    issues,
                    f".github/pull_request_template.md missing required field: {field}",
                )

    codeowners_path = repo_root / ".github" / "CODEOWNERS"
    if codeowners_path.exists():
        codeowners_text = codeowners_path.read_text()
        for required_line in CODEOWNERS_REQUIRED_LINES:
            if required_line not in codeowners_text:
                _add_issue(
                    issues,
                    f".github/CODEOWNERS missing required ownership line: {required_line}",
                )

    license_path = repo_root / "LICENSE"
    if license_path.exists():
        license_text = license_path.read_text().lower()
        if "gnu" not in license_text or "license" not in license_text:
            _add_issue(issues, "LICENSE must contain a recognizable GNU license text")

    _check_package_controls(repo_root, issues)

    return issues
