"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify repository topology rules and scaffold-directory requirements with unit coverage

- Later Extension Points:
    --> add more topology fixtures only when new governed repo-shape rules become durable defaults

- Role:
    --> builds temporary repository skeletons for shape verifier coverage
    --> checks forbidden prototype files noise blocking and required testing taxonomy rules

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

from tools.verify.shape import check_shape


def write_package_json(path: Path) -> None:
    package = {
        "name": "synaweave-ce",
        "private": True,
        "workspaces": [
            "apps/*",
            "packages/*",
            "python/*",
            "infra/*",
            "testing/*",
            "tools/*",
        ],
        "scripts": {
            "verify": "python tools/verify/main.py",
        },
    }
    path.write_text(json.dumps(package))


def make_skeleton(repo_root: Path, *, with_forbidden_file: bool = False) -> None:
    for directory in [
        "apps",
        "docs",
        "infra",
        "packages",
        "python",
        "testing",
        "tools",
        ".github",
    ]:
        (repo_root / directory).mkdir(parents=True)

    for directory in ["extension", "web", "api", "ingest", "mcp", "ml", "eval"]:
        (repo_root / "apps" / directory).mkdir(parents=True)
    for directory in [
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
    ]:
        (repo_root / "testing" / directory).mkdir(parents=True)
    write_package_json(repo_root / "package.json")

    if with_forbidden_file:
        (repo_root / "manifest.json").write_text("{\n}")


class TestVerifyShape(unittest.TestCase):
    def test_shape_allows_clean_topology(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_skeleton(repo_root)
            issues = check_shape(repo_root)
            self.assertEqual(issues, [])

    def test_shape_flags_prototype_file_at_root(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_skeleton(repo_root, with_forbidden_file=True)
            issues = check_shape(repo_root)
            self.assertTrue(
                any("forbidden prototype file" in issue for issue in issues)
            )

    def test_shape_requires_full_testing_taxonomy(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_skeleton(repo_root)
            (repo_root / "testing" / "evals").rmdir()
            issues = check_shape(repo_root)
            self.assertTrue(any("testing/evals" in issue for issue in issues))

    def test_shape_requires_reserved_app_homes(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_skeleton(repo_root)
            (repo_root / "apps" / "ml").rmdir()
            issues = check_shape(repo_root)
            self.assertIn("missing required app directory: apps/ml", issues)

    def test_shape_rejects_required_app_home_file(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_skeleton(repo_root)
            app_path = repo_root / "apps" / "ml"
            app_path.rmdir()
            app_path.write_text("placeholder")
            issues = check_shape(repo_root)
            self.assertIn("required app home is not a directory: apps/ml", issues)

    def test_shape_does_not_require_assets_topology(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_skeleton(repo_root)
            issues = check_shape(repo_root)
            self.assertFalse(any("assets" in issue for issue in issues))

    def test_shape_rejects_platform_noise(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_skeleton(repo_root)
            (repo_root / ".DS_Store").write_text("noise")
            issues = check_shape(repo_root)
            self.assertTrue(any("platform-generated repo noise" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
