"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify commit-message policy and ADR rule checks with isolated unit coverage

- Later Extension Points:
    --> add more commit-policy fixtures only when the governed commit contract expands

- Role:
    --> tests commit subject validation and ADR naming rules in temporary fixtures
    --> keeps commit-policy regression coverage local and deterministic

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from tools.verify.adr import check_adrs
from tools.verify.commit import check_commit_head, check_commit_range, validate_message
from tools.verify.policy import BANNED_TYPE_SCOPE_PAIRS, MIN_SUBJECT_WORDS

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_ADR = (REPO_ROOT / "docs" / "adrs" / "sprint-001.md").read_text()


@contextmanager
def _patched_env(**updates: str | None):
    prior_values = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
                continue
            os.environ[key] = value
        yield
    finally:
        for key, value in prior_values.items():
            if value is None:
                os.environ.pop(key, None)
                continue
            os.environ[key] = value


def _extract_between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker) + len(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


FIRST_ANSWER_BLOCK = _extract_between(
    VALID_ADR,
    "### D1 - Lock the shallow monorepo topology and reserved runtime homes\n\n"
    "- ***What was built?***\n",
    "- ***Why was it chosen?***",
)
STATUS_BLOCK = _extract_between(VALID_ADR, "## Current Status\n\n", "\n---").rstrip()


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _git_output(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo_root, text=True).strip()


def _init_commit_repo(repo_root: Path) -> None:
    _git(repo_root, "init")
    _git(repo_root, "config", "user.name", "tester")
    _git(repo_root, "config", "user.email", "tester@example.com")


def _commit_file(repo_root: Path, path: str, content: str, message: str) -> str:
    (repo_root / path).write_text(content)
    _git(repo_root, "add", path)
    _git(repo_root, "commit", "-m", message)
    return _git_output(repo_root, "rev-parse", "HEAD")


class TestVerifyCommit(unittest.TestCase):
    def test_valid_commit_message(self):
        issues = validate_message(
            "docs(governance): align the root documentation spine with the governed platform "
            "reset and proof stack for maintainers reviewing durable verification boundaries"
        )
        self.assertEqual(issues, [])

    def test_docs_docs_scope_is_rejected_as_too_broad(self):
        issues = validate_message(
            "docs(docs): align owner guidance with durable verifier evidence for maintainers "
            "reviewing protected repository controls and release boundaries"
        )
        self.assertIn(BANNED_TYPE_SCOPE_PAIRS[("docs", "docs")], issues)

    def test_test_testing_scope_is_rejected_as_too_broad(self):
        issues = validate_message(
            "test(testing): cover shared verifier behavior for maintainers reviewing protected "
            "repository controls and durable release boundaries across hooks and workflows"
        )
        self.assertIn(BANNED_TYPE_SCOPE_PAIRS[("test", "testing")], issues)

    def test_test_hooks_scope_commit_message_passes_when_subject_is_otherwise_valid(self):
        issues = validate_message(
            "test(hooks): cover commit message failures through the shared verifier path for "
            "maintainers reviewing local history controls and protected repository automation"
        )
        self.assertEqual(issues, [])

    def test_allowed_style_and_deploy_types_pass(self):
        style_issues = validate_message(
            "style(docs): remove repeated filler wording and tighten the reader facing summary "
            "language deeply for maintainers reviewing governed contributor guidance updates"
        )
        deploy_issues = validate_message(
            "deploy(infra): publish the reviewed runtime bundle and describe rollback checkpoints "
            "with explicit operator evidence for governed release handoff and recovery readiness"
        )
        self.assertEqual(style_issues, [])
        self.assertEqual(deploy_issues, [])

    def test_short_commit_subject_rejected(self):
        issues = validate_message("feat(apps): add scaffolded app files")
        self.assertIn(f"commit subject must be at least {MIN_SUBJECT_WORDS} words", issues)

    def test_commit_subject_rejects_repeated_type_word(self):
        issues = validate_message(
            "docs(tools): docs align the shared review contract with stricter "
            "history title guidance for contributors using concrete plain-English rationale"
        )
        self.assertIn("commit subject must not repeat change type word: docs", issues)

    def test_commit_subject_rejects_repeated_scope_word(self):
        issues = validate_message(
            "fix(adr): align adr review notes with stricter history title guidance for contributors"
        )
        self.assertIn("commit subject must not repeat change scope word: adr", issues)

    def test_docs_adr_scope_commit_message_passes_when_subject_is_otherwise_valid(self):
        issues = validate_message(
            "docs(adr): align review notes with pre-commit and pre-push evidence "
            "across shared history gates with concrete reviewer context and durable rationale"
        )
        self.assertEqual(issues, [])

    def test_hyphenated_pre_commit_and_pre_push_count_as_one_word(self):
        issues = validate_message(
            "docs(adr): align review notes with pre-commit and pre-push evidence "
            "across shared history"
        )
        self.assertIn(f"commit subject must be at least {MIN_SUBJECT_WORDS} words", issues)

    def test_invalid_commit_format_rejected(self):
        issues = validate_message("invalid subject format")
        self.assertIn("commit message must use format", issues[0])

    def test_raw_identifier_is_rejected(self):
        issues = validate_message(
            "fix(tools): keep runtime_source_url validation aligned with the repo control wording "
            "and current checks"
        )
        self.assertIn(
            "commit subject should prefer plain English over raw code identifiers",
            issues,
        )

    def test_filler_word_is_rejected(self):
        issues = validate_message(
            "docs(governance): explain the governed architecture posture clearly "
            "for later reviewers "
            "and operators"
        )
        self.assertIn("commit subject must remove fluff and filler words or phrases", issues)

    def test_new_banned_filler_words_are_rejected(self):
        issues = validate_message(
            "docs(governance): align durable contributor guidance with concrete "
            "history checkpoints now "
            "for operators and reviewers"
        )
        self.assertIn("commit subject must remove fluff and filler words or phrases", issues)

    def test_again_is_rejected_as_shared_banned_word(self):
        issues = validate_message(
            "docs(governance): align durable contributor guidance with review checkpoints "
            "again for operators and maintainers"
        )
        self.assertIn("commit subject must remove fluff and filler words or phrases", issues)

    def test_filler_phrase_is_rejected(self):
        issues = validate_message(
            "docs(governance): align the root documentation spine with policy checks for later "
            "reviewers and operators"
        )
        self.assertIn("commit subject must remove fluff and filler words or phrases", issues)

    def test_new_banned_filler_phrase_is_rejected(self):
        issues = validate_message(
            "docs(governance): align contributor guidance with a stricter review "
            "flow for reviewers "
            "and operators handling protected paths"
        )
        self.assertIn("commit subject must remove fluff and filler words or phrases", issues)

    def test_banned_hyphenated_prefix_is_rejected(self):
        issues = validate_message(
            "docs(governance): align contributor guidance with phase-level "
            "checkpoints for reviewers "
            "and operators handling protected paths"
        )
        self.assertIn("commit subject must remove fluff and filler words or phrases", issues)

    def test_commit_range_rejects_duplicate_subject_intent(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.name", "tester"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "tester@example.com"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "-m",
                    "chore(tools): establish the local history baseline for later commit range "
                    "validation",
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            (repo_root / "note.txt").write_text("one\n")
            subprocess.run(
                ["git", "add", "note.txt"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "docs(governance): describe the durable architecture posture "
                    "for future reviewers "
                    "and operators carefully",
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            (repo_root / "note.txt").write_text("two\n")
            subprocess.run(
                ["git", "add", "note.txt"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "docs(governance): describe the durable architecture posture "
                    "for future reviewers "
                    "and operators carefully",
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            base_sha = subprocess.check_output(
                ["git", "rev-list", "--max-parents=0", "HEAD"],
                cwd=repo_root,
                text=True,
            ).strip()

            with _patched_env(VERIFY_COMMIT_BASE=base_sha, VERIFY_COMMIT_HEAD=None):
                issues = check_commit_range(repo_root)
            self.assertTrue(any("duplicate subject intent" in issue for issue in issues))

    def test_commit_checks_use_explicit_head_when_merge_ref_is_checked_out(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            _init_commit_repo(repo_root)
            _git(
                repo_root,
                "commit",
                "--allow-empty",
                "-m",
                "chore(tools): establish the governed baseline for pull request history validation "
                "before authored commits diverge",
            )
            base_sha = _git_output(repo_root, "rev-parse", "HEAD")
            head_sha = _commit_file(
                repo_root,
                "note.txt",
                "feature\n",
                "fix(tools): align pull request history validation with authored commit subjects "
                "and ranges while merge refs stay reviewable in hosted checks",
            )
            _git(repo_root, "checkout", "-b", "base-line", base_sha)
            _commit_file(
                repo_root,
                "base.txt",
                "base\n",
                "docs(governance): preserve the governed base branch note for merge ref fixtures "
                "used by hosted verification coverage",
            )
            _git(repo_root, "checkout", "-B", "feature-line", head_sha)
            _git(
                repo_root,
                "merge",
                "--no-ff",
                "base-line",
                "-m",
                "Merge base-line into feature-line",
            )

            with _patched_env(VERIFY_COMMIT_BASE=base_sha, VERIFY_COMMIT_HEAD=head_sha):
                issues = check_commit_head(repo_root)

            self.assertEqual(issues, [])

    def test_commit_head_reports_explicit_head_message_not_merge_message(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            _init_commit_repo(repo_root)
            _git(
                repo_root,
                "commit",
                "--allow-empty",
                "-m",
                "chore(tools): establish the governed baseline for pull request history validation "
                "before authored commits diverge",
            )
            base_sha = _git_output(repo_root, "rev-parse", "HEAD")
            head_sha = _commit_file(repo_root, "note.txt", "feature\n", "bad merge subject")
            _git(repo_root, "checkout", "-b", "base-line", base_sha)
            _commit_file(
                repo_root,
                "base.txt",
                "base\n",
                "docs(governance): preserve the governed base branch note for merge ref fixtures "
                "used by hosted verification coverage",
            )
            _git(repo_root, "checkout", "-B", "feature-line", head_sha)
            _git(
                repo_root,
                "merge",
                "--no-ff",
                "base-line",
                "-m",
                "fix(tools): merge fixture message that stays valid for hosted verification "
                "coverage",
            )

            with _patched_env(VERIFY_COMMIT_BASE=base_sha, VERIFY_COMMIT_HEAD=head_sha):
                issues = check_commit_head(repo_root)

            self.assertTrue(any("must use format" in issue for issue in issues))
            self.assertFalse(any("duplicate subject intent" in issue for issue in issues))

    def test_local_commit_head_check_skips_history_without_explicit_range_context(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.name", "tester"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "tester@example.com"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "-m",
                    "docs(governance): short history title",
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )

            with _patched_env(VERIFY_COMMIT_BASE=None, VERIFY_COMMIT_HEAD=None):
                issues = check_commit_head(repo_root)
            self.assertEqual(issues, [])

    def test_ci_commit_head_check_skips_history_without_origin_base_context(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.name", "tester"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "tester@example.com"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "-m",
                    "docs(governance): short history title",
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )

            with _patched_env(
                GITHUB_ACTIONS="true",
                GITHUB_BASE_REF="main",
                VERIFY_COMMIT_BASE=None,
                VERIFY_COMMIT_HEAD=None,
            ):
                issues = check_commit_head(repo_root)

            self.assertEqual(issues, [])

    def test_commit_range_skips_invalid_explicit_base_for_temporary_repo(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.name", "tester"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "tester@example.com"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "-m",
                    "docs(governance): short history title",
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )

            with _patched_env(VERIFY_COMMIT_BASE="deadbeef", VERIFY_COMMIT_HEAD=None):
                issues = check_commit_range(repo_root)

            self.assertEqual(issues, [])

    def test_commit_head_skips_invalid_explicit_head_for_temporary_repo(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            _init_commit_repo(repo_root)
            _git(
                repo_root,
                "commit",
                "--allow-empty",
                "-m",
                "docs(governance): short history title",
            )

            with _patched_env(VERIFY_COMMIT_BASE="deadbeef", VERIFY_COMMIT_HEAD="deadbeef"):
                issues = check_commit_head(repo_root)

            self.assertEqual(issues, [])

    def test_adr_file_name_rules(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "s001.md").write_text("legacy ADR placeholder")

            issues = check_adrs(base)
            self.assertTrue(any("sprint-###.md" in issue for issue in issues))

    def test_adr_requires_standard_sections(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text("# missing sections\n")

            issues = check_adrs(base)
            self.assertTrue(any("missing required section" in issue for issue in issues))

    def test_adr_accepts_the_updated_sprint_structure(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(VALID_ADR)

            self.assertEqual(check_adrs(base), [])

    def test_adr_accepts_deliverable_scoped_identifiers_in_index_and_heading(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(VALID_ADR)

            issues = check_adrs(base)
            self.assertFalse(any("decision index" in issue for issue in issues))

    def test_adr_requires_new_rules_heading_and_decision_template_section(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(
                VALID_ADR.replace("### How To Use This File (Rules)", "### How To Use This File")
                .replace("### Decision Entry Template\n\n", "")
            )

            issues = check_adrs(base)
            self.assertTrue(any("How To Use This File (Rules)" in issue for issue in issues))
            self.assertTrue(any("Decision Entry Template" in issue for issue in issues))

    def test_adr_requires_three_long_answer_bullets_per_question(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(
                VALID_ADR.replace(FIRST_ANSWER_BLOCK, "  - Too short.\n")
            )

            issues = check_adrs(base)
            self.assertTrue(any("needs at least 3 answer bullets" in issue for issue in issues))

    def test_adr_limits_current_status_bullets(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            status_block = "\n".join(f"- status {index}" for index in range(11))
            (adrs / "sprint-001.md").write_text(VALID_ADR.replace(STATUS_BLOCK, status_block))

            issues = check_adrs(base)
            self.assertTrue(any("10 bullets or fewer" in issue for issue in issues))

    def test_adr_rejects_raw_identifiers(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(
                VALID_ADR.replace(
                    "sprint-level reasoning ledger",
                    "runtime_mode reasoning ledger",
                    1,
                )
            )
            issues = check_adrs(base)
            self.assertTrue(any("plain English" in issue for issue in issues))

    def test_adr_rejects_shared_banned_word_phrase_and_prefix(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(
                VALID_ADR.replace("protected-path contract", "review flow contract", 1)
            )

            issues = check_adrs(base)
            self.assertTrue(any("fluff and filler wording" in issue for issue in issues))

        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(
                VALID_ADR.replace(
                    "reviewable automation surfaces",
                    "phase-level automation surfaces",
                    1,
                )
            )

            issues = check_adrs(base)
            self.assertTrue(any("fluff and filler wording" in issue for issue in issues))

        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(
                VALID_ADR.replace(
                    "shared contract baseline",
                    "shared contract baseline again",
                    1,
                )
            )

            issues = check_adrs(base)
            self.assertTrue(any("fluff and filler wording" in issue for issue in issues))

        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(
                VALID_ADR.replace(
                    "shared contract baseline",
                    "shared contract baseline clearly",
                    1,
                )
            )

            issues = check_adrs(base)
            self.assertTrue(any("fluff and filler wording" in issue for issue in issues))

    def test_adr_rejects_decision_index_heading_drift(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            base = Path(raw_tmp)
            adrs = base / "docs" / "adrs"
            adrs.mkdir(parents=True)
            (adrs / "sprint-001.md").write_text(
                VALID_ADR.replace(
                    "| D1-T4 - protected-path control-surface alignment | approved |",
                    "| D1-T4 - protected-path control-surface agreement | approved |",
                    1,
                )
            )

            issues = check_adrs(base)
            self.assertTrue(
                any("must match decision headings exactly" in issue for issue in issues)
            )


if __name__ == "__main__":
    unittest.main()
