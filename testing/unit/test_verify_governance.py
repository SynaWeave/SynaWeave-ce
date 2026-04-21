"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify governed file ownership and pull-request template rules with unit coverage

- Later Extension Points:
    --> add more governance fixtures only when protected repo-control surfaces expand

- Role:
    --> builds temporary governance trees for governance verifier coverage
    --> checks required governance files ownership lines and pull-request template fields

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.verify.governance import check_governance
from tools.verify.policy import (
    GOVERNED_GITHUB_POSTURE_PHRASES,
    GOVERNED_REQUIRED_STATUS_CHECKS,
    MIN_SUBJECT_WORDS,
    PR_TEMPLATE_REQUIRED_FIELDS,
    REQUIRED_DEV_DEPENDENCIES,
    REQUIRED_PACKAGE_SCRIPTS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def read_canonical_requirements_dev() -> str:
    return (REPO_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")


def make_governance_tree(repo_root: Path) -> None:
    (repo_root / ".github").mkdir(parents=True)
    for name in [
        "AGENTS.md",
        "GOVERNANCE.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "CLA.md",
        "NOTICE",
        "TRADEMARKS.md",
        "LICENSE",
        ".env.example",
        ".betterleaks.toml",
    ]:
        (repo_root / name).write_text("ok\n")
    (repo_root / "LICENSE").write_text("GNU GENERAL PUBLIC LICENSE\n")
    (repo_root / ".github" / "CODEOWNERS").write_text("* @owner\n")
    (repo_root / ".github" / "CODEOWNERS").write_text(
        "\n".join(
            [
                "* @SynaWave/core-maintainers",
                ".github/ @SynaWave/core-maintainers",
                "apps/ @SynaWave/core-maintainers",
                "docs/ @SynaWave/core-maintainers",
                "tools/ @SynaWave/core-maintainers",
                "packages/ @SynaWave/core-maintainers",
                "python/ @SynaWave/core-maintainers",
                "infra/ @SynaWave/core-maintainers",
                "infra/docker/ @SynaWave/platform-admins @SynaWave/core-maintainers",
                "infra/github/ @SynaWave/platform-admins @SynaWave/core-maintainers",
                "infra/policies/ @SynaWave/platform-admins @SynaWave/core-maintainers",
                "testing/ @SynaWave/core-maintainers",
                "AGENTS.md @SynaWave/platform-admins",
                "GOVERNANCE.md @SynaWave/platform-admins",
                "CONTRIBUTING.md @SynaWave/platform-admins",
                "CODE_OF_CONDUCT.md @SynaWave/platform-admins",
                "SECURITY.md @SynaWave/platform-admins",
                "CLA.md @SynaWave/platform-admins",
                "NOTICE @SynaWave/platform-admins",
                "TRADEMARKS.md @SynaWave/platform-admins",
                ".env.example @SynaWave/platform-admins",
                ".github/CODEOWNERS @SynaWave/platform-admins",
                ".github/pull_request_template.md @SynaWave/platform-admins",
                ".github/workflows/ @SynaWave/platform-admins",
                "tools/verify/ @SynaWave/platform-admins",
                "tools/hooks/ @SynaWave/platform-admins",
                "docs/planning/ @SynaWave/platform-admins @SynaWave/core-maintainers",
                "docs/adrs/ @SynaWave/platform-admins @SynaWave/core-maintainers",
                "docs/templates/ @SynaWave/platform-admins @SynaWave/core-maintainers",
                "docs/*.md @SynaWave/core-maintainers",
                "",
            ]
        )
    )
    (repo_root / "CONTRIBUTING.md").write_text(
        "Conventional Commits\n"
        f"minimum {MIN_SUBJECT_WORDS}\n"
        "plain English\n"
        "shared ban list\n"
        "docs(docs)\n"
        "test(testing)\n"
        "docs(adr)\n"
        "test(hooks)\n"
        "sprint, deliverable, and task\n"
    )
    (repo_root / "GOVERNANCE.md").write_text(
        "# Governance\n\n"
        "Expected default-branch ruleset posture:\n\n"
        + "\n".join(f"- {phrase}" for phrase in GOVERNED_GITHUB_POSTURE_PHRASES[1:])
        + "\n"
        + "\n".join(f"- `{status_check}`" for status_check in GOVERNED_REQUIRED_STATUS_CHECKS)
        + "\n"
    )
    (repo_root / ".github" / "pull_request_template.md").write_text(
        "\n".join(PR_TEMPLATE_REQUIRED_FIELDS) + "\n"
    )
    (repo_root / "package.json").write_text(
        json.dumps(
            {
                "scripts": REQUIRED_PACKAGE_SCRIPTS,
                "devDependencies": REQUIRED_DEV_DEPENDENCIES,
            },
            indent=2,
        )
        + "\n"
    )
    (repo_root / "tsconfig.json").write_text(
        '{\n'
        '  "compilerOptions": {\n'
        '    "target": "ES2022"\n'
        '  }\n'
        '}\n'
    )
    (repo_root / "requirements-dev.txt").write_text(
        read_canonical_requirements_dev(),
        encoding="utf-8",
    )
    (repo_root / "tools" / "verify").mkdir(parents=True)
    (repo_root / "tools" / "verify" / "main.py").write_text(
        "from tools.verify.docs import check_docs\n"
    )


class TestVerifyGovernance(unittest.TestCase):
    def test_governance_pins_verify_script_with_adr_enforcement(self):
        verify_script = REQUIRED_PACKAGE_SCRIPTS["verify"]
        self.assertIn("verify:browser", verify_script)
        self.assertIn("adr", verify_script)
        self.assertIn("commit", verify_script)

    def test_governance_pins_browser_verification_scripts(self):
        self.assertEqual(
            REQUIRED_PACKAGE_SCRIPTS["deps:browser"],
            "playwright install chromium",
        )
        self.assertIn("build:extension", REQUIRED_PACKAGE_SCRIPTS["test:e2e"])
        self.assertIn("playwright test", REQUIRED_PACKAGE_SCRIPTS["test:e2e"])
        self.assertIn(
            "testing/accessibility",
            REQUIRED_PACKAGE_SCRIPTS["test:accessibility"],
        )
        self.assertEqual(
            REQUIRED_DEV_DEPENDENCIES["@playwright/test"],
            "1.59.1",
        )
        self.assertEqual(
            REQUIRED_DEV_DEPENDENCIES["@axe-core/playwright"],
            "4.11.2",
        )

    def test_governance_passes_with_required_files_and_fields(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            self.assertEqual(check_governance(repo_root), [])

    def test_governance_requires_codeowners(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / ".github" / "CODEOWNERS").unlink()
            issues = check_governance(repo_root)
            self.assertTrue(any("CODEOWNERS" in issue for issue in issues))

    def test_governance_requires_dependency_installability_status_check_note(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / "GOVERNANCE.md").write_text(
                (repo_root / "GOVERNANCE.md")
                .read_text()
                .replace("- `dependency-installability / dependency-installability`\n", "")
            )
            issues = check_governance(repo_root)
            self.assertTrue(any("dependency-installability" in issue for issue in issues))

    def test_governance_requires_rulesets_first_wording(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / "GOVERNANCE.md").write_text(
                (repo_root / "GOVERNANCE.md")
                .read_text()
                .replace(
                    "Expected default-branch ruleset posture:\n\n",
                    "Expected default-branch posture:\n\n",
                )
            )
            issues = check_governance(repo_root)
            self.assertTrue(any("ruleset posture" in issue for issue in issues))

    def test_governance_requires_codeowners_posture_note(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / "GOVERNANCE.md").write_text(
                (repo_root / "GOVERNANCE.md")
                .read_text()
                .replace(
                    "- CODEOWNERS file assigns platform-admin and core-maintainer "
                    "owners for protected-path changes\n",
                    "",
                )
            )
            issues = check_governance(repo_root)
            self.assertTrue(any("CODEOWNERS file assigns" in issue for issue in issues))

    def test_governance_requires_platform_admin_owners_for_infra_docker(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / ".github" / "CODEOWNERS").write_text(
                (repo_root / ".github" / "CODEOWNERS")
                .read_text()
                .replace(
                    "infra/docker/ @SynaWave/platform-admins @SynaWave/core-maintainers\n",
                    "",
                )
            )
            issues = check_governance(repo_root)
            self.assertTrue(any("infra/docker/" in issue for issue in issues))

    def test_governance_requires_pr_template_admin_bypass_field(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / ".github" / "pull_request_template.md").write_text(
                "## TL;DR\n"
                "## Summary\n"
                "### Why this change\n"
                "### Files and boundaries\n"
                "### Protected-path and hotspot notes\n"
                "## Verification\n"
                "### Checklist\n"
                "### Docs and ADR delta\n"
                "### Scope\n"
                "### Tests\n"
                "## CLA\n"
                "I agree to the CLA in CLA.md\n"
            )
            issues = check_governance(repo_root)
            self.assertTrue(any("Admin bypass used or requested" in issue for issue in issues))

    def test_governance_requires_pinned_package_controls(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / "package.json").write_text('{"scripts": {}, "devDependencies": {}}\n')
            issues = check_governance(repo_root)
            self.assertTrue(
                any("package.json script must match governed value" in issue for issue in issues)
            )
            self.assertTrue(any("package.json devDependency must pin" in issue for issue in issues))

    def test_governance_requires_shared_ban_model_in_contributing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / "CONTRIBUTING.md").write_text(
                "Conventional Commits\n"
                f"minimum {MIN_SUBJECT_WORDS}\n"
                "plain English\n"
                "sprint, deliverable, and task\n"
            )
            issues = check_governance(repo_root)
            self.assertTrue(any("shared banned-word model" in issue for issue in issues))

    def test_governance_requires_umbrella_scope_examples_in_contributing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / "CONTRIBUTING.md").write_text(
                "Conventional Commits\n"
                f"minimum {MIN_SUBJECT_WORDS}\n"
                "plain English\n"
                "shared ban list\n"
                "docs(adr)\n"
                "test(hooks)\n"
                "sprint, deliverable, and task\n"
            )
            issues = check_governance(repo_root)
            self.assertTrue(any("rejected umbrella" in issue for issue in issues))

    def test_governance_requires_narrower_scope_examples_in_contributing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / "CONTRIBUTING.md").write_text(
                "Conventional Commits\n"
                f"minimum {MIN_SUBJECT_WORDS}\n"
                "plain English\n"
                "shared ban list\n"
                "docs(docs)\n"
                "test(testing)\n"
                "sprint, deliverable, and task\n"
            )
            issues = check_governance(repo_root)
            self.assertTrue(any("supported narrower scope examples" in issue for issue in issues))

    def test_governance_requires_exact_python_dev_requirement_pins(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_governance_tree(repo_root)
            (repo_root / "requirements-dev.txt").write_text("ruff>=0.8.6\n")
            issues = check_governance(repo_root)
            self.assertTrue(
                any("requirements-dev.txt must use exact" in issue for issue in issues)
            )


if __name__ == "__main__":
    unittest.main()
