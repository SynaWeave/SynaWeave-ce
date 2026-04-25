"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify governed docs-spine rules and template requirements with isolated unit coverage

- Later Extension Points:
    --> add more docs-check fixtures only when new root-doc or template rules become verifier-owned

- Role:
    --> builds temporary docs trees for docs verifier coverage
    --> checks canonical docs structure pointer behavior and single-readme enforcement

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.verify.docs import check_docs
from tools.verify.policy import REQUIRED_TEMPLATE_FILES


def make_docs_tree(repo_root: Path) -> None:
    docs_dir = repo_root / "docs"
    (docs_dir / "adrs").mkdir(parents=True)
    (docs_dir / "planning" / "sprint-001").mkdir(parents=True)
    (docs_dir / "templates" / "planning").mkdir(parents=True)
    (docs_dir / "templates" / "adrs").mkdir(parents=True)
    (docs_dir / "templates" / "specs").mkdir(parents=True)
    (docs_dir / "templates" / "tests").mkdir(parents=True)

    for name in [
        "architecture.md",
        "auth.md",
        "code-style.md",
        "design-system.md",
        "legend.md",
        "packages.md",
        "apps.md",
        "infra.md",
        "operations.md",
        "workflow.md",
        "onboarding.md",
        "testing.md",
        "python.md",
        "planning.md",
        "templates.md",
        "adrs.md",
    ]:
        (docs_dir / name).write_text("ok\n")
    (docs_dir / "planning.md").write_text(
        "This file exists only as a compatibility pointer.\n"
        "Use docs/planning/MASTER.md for planning rules.\n"
    )

    (docs_dir / "planning" / "MASTER.md").write_text("ok\n")
    (docs_dir / "planning" / "sprint-001" / "overview.md").write_text("ok\n")
    (docs_dir / "planning" / "sprint-001" / "d1-foundation.md").write_text("ok\n")
    (docs_dir / "planning" / "sprint-001" / "d2-runtime.md").write_text("ok\n")
    (docs_dir / "planning" / "sprint-001" / "d3-quality.md").write_text("ok\n")
    for template_file in REQUIRED_TEMPLATE_FILES:
        full_path = docs_dir / "templates" / template_file
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("ok\n")


class TestVerifyDocs(unittest.TestCase):
    def test_docs_pass_with_required_structure(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_docs_tree(repo_root)
            (repo_root / "README.md").write_text("root readme\n")
            issues = check_docs(repo_root)
            self.assertEqual(issues, [])

    def test_docs_fail_on_narrative_apps_docs_reference(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_docs_tree(repo_root)
            (repo_root / "README.md").write_text("apps/docs is a runtime\n")
            issues = check_docs(repo_root)
            self.assertTrue(
                any(
                    "human-facing docs must not describe apps/docs" in issue
                    for issue in issues
                )
            )

    def test_docs_require_planning_pointer_shape(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_docs_tree(repo_root)
            (repo_root / "docs" / "planning.md").write_text("second planning authority\n")
            issues = check_docs(repo_root)
            self.assertTrue(any("compatibility pointer" in issue for issue in issues))

    def test_docs_reject_nested_readme_files(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_docs_tree(repo_root)
            (repo_root / "README.md").write_text("root readme\n")
            (repo_root / "docs" / "templates" / "README.md").write_text("nested readme\n")
            issues = check_docs(repo_root)
            self.assertTrue(any("only the root README.md" in issue for issue in issues))

    def test_docs_ignore_readmes_in_dependency_directories(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_docs_tree(repo_root)
            (repo_root / "README.md").write_text("root readme\n")
            (repo_root / "node_modules" / "pkg").mkdir(parents=True)
            (repo_root / "node_modules" / "pkg" / "README.md").write_text("dependency readme\n")
            issues = check_docs(repo_root)
            self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
