"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify shared PR title and body validation rules with isolated unit coverage

- Later Extension Points:
    --> add more PR-quality fixtures only when shared review policy grows later

- Role:
    --> tests PR title grammar and body requirement validation without duplicated workflow fixtures
    --> keeps shared CI review checks aligned with the PR template and policy constants

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import unittest

from tools.verify.policy import BANNED_TYPE_SCOPE_PAIRS
from tools.verify.pr_quality import validate_pr_body, validate_pr_title

VALID_TITLE = (
    "fix(tools): remove brittle suppression paths and harden shared repo verification controls "
    "for maintainers"
)
VALID_BODY = (
    "## TL;DR\n"
    "## Summary\n"
    "### Why this change\n"
    "Business logic alignment note:\n"
    "### Files and boundaries\n"
    "### Protected-path and hotspot notes\n"
    "## Verification\n"
    "### Checklist\n"
    "Code remains readable without hidden workflow or policy drift\n"
    "Proper documentation was updated for any durable behavior or structure change\n"
    "### Docs and ADR delta\n"
    "### Scope\n"
    "### Tests\n"
    "Test coverage remains appropriate for the changed logic path\n"
    "## CLA\n"
    "I agree to the CLA in CLA.md\n"
    "Admin bypass used or requested\n"
)


class TestVerifyPrQuality(unittest.TestCase):
    def test_validate_pr_title_accepts_governed_title(self):
        self.assertEqual(validate_pr_title(VALID_TITLE), [])

    def test_validate_pr_title_rejects_sprint_prefix(self):
        title = f"S001/d1 foundation --> {VALID_TITLE}"
        issues = validate_pr_title(title)
        self.assertTrue(any("must use format" in issue for issue in issues))

    def test_validate_pr_title_rejects_short_subject(self):
        issues = validate_pr_title("fix(tools): short title")
        self.assertTrue(any("at least 8 words" in issue for issue in issues))

    def test_validate_pr_title_rejects_repeated_type_word(self):
        issues = validate_pr_title(
            "docs(tools): docs align the shared review contract with stricter title policy"
        )
        self.assertIn("PR title subject must not repeat change type word: docs", issues)

    def test_validate_pr_title_rejects_repeated_scope_word(self):
        issues = validate_pr_title(
            "fix(adr): align adr review notes with stricter repository title policy"
        )
        self.assertIn("PR title subject must not repeat change scope word: adr", issues)

    def test_validate_pr_title_rejects_shared_banned_word_phrase_and_prefix(self):
        word_issues = validate_pr_title(
            "docs(tools): align contributor guidance clearly with durable protected path "
            "review notes"
        )
        banned_word_issues = validate_pr_title(
            "docs(tools): align contributor guidance again with durable protected path "
            "review notes"
        )
        phrase_issues = validate_pr_title(
            "docs(tools): align contributor guidance with a stricter review flow for "
            "protected paths"
        )
        prefix_issues = validate_pr_title(
            "docs(tools): align contributor guidance with phase-level checkpoints for "
            "protected paths"
        )

        self.assertTrue(any("fluff and filler" in issue for issue in word_issues))
        self.assertTrue(any("fluff and filler" in issue for issue in banned_word_issues))
        self.assertTrue(any("fluff and filler" in issue for issue in phrase_issues))
        self.assertTrue(any("fluff and filler" in issue for issue in prefix_issues))

    def test_validate_pr_title_accepts_docs_adr_scope_when_otherwise_valid(self):
        issues = validate_pr_title(
            "docs(adr): align review notes with pre-commit and pre-push evidence"
        )
        self.assertEqual(issues, [])

    def test_validate_pr_title_rejects_docs_docs_scope_as_too_broad(self):
        issues = validate_pr_title(
            "docs(docs): align owner guidance with durable verifier evidence for maintainers"
        )
        self.assertIn(BANNED_TYPE_SCOPE_PAIRS[("docs", "docs")], issues)

    def test_validate_pr_title_rejects_test_testing_scope_as_too_broad(self):
        issues = validate_pr_title(
            "test(testing): cover shared verifier behavior for maintainers reviewing hooks"
        )
        self.assertIn(BANNED_TYPE_SCOPE_PAIRS[("test", "testing")], issues)

    def test_validate_pr_title_accepts_test_hooks_scope_when_otherwise_valid(self):
        issues = validate_pr_title(
            "test(hooks): cover commit message failures through the shared verifier path"
        )
        self.assertEqual(issues, [])

    def test_validate_pr_title_rejects_raw_identifier_language(self):
        issues = validate_pr_title(
            "fix(tools): keep runtime_source_url validation aligned with durable reviewer wording"
        )
        self.assertTrue(any("raw code identifiers" in issue for issue in issues))

    def test_validate_pr_body_requires_shared_fields(self):
        issues = validate_pr_body("## TL;DR\n")
        self.assertTrue(any("Business logic alignment note:" in issue for issue in issues))

    def test_validate_pr_body_accepts_full_template_shape(self):
        self.assertEqual(validate_pr_body(VALID_BODY), [])


if __name__ == "__main__":
    unittest.main()
