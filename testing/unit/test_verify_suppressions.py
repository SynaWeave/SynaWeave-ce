"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify banned suppression detection across governed source and config surfaces

- Later Extension Points:
    --> add more suppression fixtures only when new governed toolchains join the baseline

- Role:
    --> tests banned inline suppression directives and TypeScript config flags in temp repos
    --> keeps the repo-wide no-suppressions policy mechanically enforced instead of review-only

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.verify.suppressions import check_suppressions


def make_suppression_tree(repo_root: Path) -> None:
    (repo_root / "tools").mkdir(parents=True)
    (repo_root / "apps").mkdir(parents=True)
    (repo_root / "packages").mkdir(parents=True)
    (repo_root / "tools" / "ts").mkdir(parents=True)
    (repo_root / "tsconfig.json").write_text(
        '{\n'
        '  "compilerOptions": {\n'
        '    "target": "ES2022"\n'
        '  }\n'
        '}\n'
    )
    (repo_root / "tools" / "sample.py").write_text("from __future__ import annotations\n")
    (repo_root / "packages" / "sample.ts").write_text("export const value = 1\n")


class TestVerifySuppressions(unittest.TestCase):
    def test_suppressions_pass_when_no_banned_patterns_exist(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_suppression_tree(repo_root)
            self.assertEqual(check_suppressions(repo_root), [])

    def test_suppressions_reject_python_noqa(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_suppression_tree(repo_root)
            (repo_root / "tools" / "sample.py").write_text("from x import y  # noqa: F401\n")
            issues = check_suppressions(repo_root)
            self.assertTrue(any("# noqa" in issue for issue in issues))

    def test_suppressions_reject_ts_ignore(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_suppression_tree(repo_root)
            (repo_root / "packages" / "sample.ts").write_text(
                "// @ts-ignore\nexport const value = 1\n"
            )
            issues = check_suppressions(repo_root)
            self.assertTrue(any("@ts-ignore" in issue for issue in issues))

    def test_suppressions_reject_tsconfig_suppression_flags(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_suppression_tree(repo_root)
            (repo_root / "tsconfig.json").write_text(
                '{"compilerOptions": {"skipLibCheck": true, "ignoreDeprecations": "6.0"}}\n'
            )
            issues = check_suppressions(repo_root)
            self.assertTrue(any("skipLibCheck" in issue for issue in issues))
            self.assertTrue(any("ignoreDeprecations" in issue for issue in issues))

    def test_suppressions_report_python_parse_failures_cleanly(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_suppression_tree(repo_root)
            (repo_root / "tools" / "sample.py").write_text("def broken(:\n")
            issues = check_suppressions(repo_root)
            self.assertTrue(any("unable to parse Python file" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
