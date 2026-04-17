"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify repo-owned secret boundary rules that generic scanners do not enforce alone

- Later Extension Points:
    --> add more security fixtures only when new governed secret surfaces or client boundaries grow

- Role:
    --> builds temporary repos that model forbidden tracked files and placeholder env requirements
    --> checks client-boundary markers and governed extension manifest HTML paths

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.verify.security import check_security


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)


def make_security_tree(repo_root: Path) -> None:
    (repo_root / "apps" / "extension").mkdir(parents=True)
    (repo_root / ".gitignore").write_text("**/*.env*\n!**/*.env.example\n")
    (repo_root / "apps" / "extension" / "popup.html").write_text("<!DOCTYPE html>\n<html></html>\n")
    (repo_root / "apps" / "extension" / "options.html").write_text(
        "<!DOCTYPE html>\n<html></html>\n"
    )
    (repo_root / "apps" / "extension" / "staticshock_icon.png").write_bytes(b"png")
    (repo_root / "apps" / "extension" / "manifest.json").write_text(
        '{"icons": {"128": "staticshock_icon.png"}, '
        '"action": {"default_icon": {"128": "staticshock_icon.png"}}, '
        '"options_page": "./options.html", '
        '"side_panel": {"default_path": "./popup.html"}}\n'
    )
    (repo_root / "apps" / "extension" / "popup.js").write_text("console.log('safe')\n")
    (repo_root / ".env.example").write_text(
        "PUBLIC_API_BASE_URL=https://api.local.example\n"
        "SUPABASE_SERVICE_ROLE_KEY=example-service-role-key\n"
        "DATABASE_URL=example-database-url-set-in-local-env\n"
    )
    _git(repo_root, "init")
    _git(repo_root, "config", "user.name", "test")
    _git(repo_root, "config", "user.email", "test@example.com")
    _git(repo_root, "add", ".")


class TestVerifySecurity(unittest.TestCase):
    def test_security_passes_with_safe_repo_shapes(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            self.assertEqual(check_security(repo_root), [])

    def test_security_rejects_tracked_env_files(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / ".env.production").write_text("SECRET_KEY=prod\n")
            _git(repo_root, "add", "-f", ".env.production")
            issues = check_security(repo_root)
            self.assertTrue(any("tracked env file violates" in issue for issue in issues))

    def test_security_requires_gitignore_env_rules(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / ".gitignore").write_text("*.log\n")
            issues = check_security(repo_root)
            self.assertTrue(any("governed env ignore rule" in issue for issue in issues))

    def test_security_rejects_tracked_keystore_files(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / "release.jks").write_text("keystore\n")
            _git(repo_root, "add", "release.jks")
            issues = check_security(repo_root)
            self.assertTrue(any("tracked file is forbidden" in issue for issue in issues))

    def test_security_rejects_non_placeholder_env_example_values(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / ".env.example").write_text(
                "SUPABASE_SERVICE_ROLE_KEY=real-looking-value\n"
            )
            issues = check_security(repo_root)
            self.assertTrue(any("must stay synthetic" in issue for issue in issues))

    def test_security_rejects_client_surface_secret_markers(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / "apps" / "extension" / "popup.js").write_text(
                'console.log("SUPABASE_SERVICE_ROLE_KEY")\n'
            )
            issues = check_security(repo_root)
            self.assertTrue(any("client-facing app surface" in issue for issue in issues))

    def test_security_rejects_manifest_path_drift(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / "apps" / "extension" / "manifest.json").write_text(
                '{"icons": {"128": "staticshock_icon.png"}, '
                '"action": {"default_icon": {"128": "staticshock_icon.png"}}, '
                '"options_page": "./dist/options.html", '
                '"side_panel": {"default_path": "./dist/popup.html"}}\n'
            )
            issues = check_security(repo_root)
            self.assertTrue(any("governed HTML source surface" in issue for issue in issues))

    def test_security_rejects_missing_manifest_icon_assets(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / "apps" / "extension" / "staticshock_icon.png").unlink()
            issues = check_security(repo_root)
            self.assertTrue(any("icon asset must exist" in issue for issue in issues))

    def test_security_rejects_manifest_icon_path_drift(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / "apps" / "extension" / "manifest.json").write_text(
                '{"icons": {"128": "assets/staticshock_icon.png"}, '
                '"action": {"default_icon": {"128": "assets/staticshock_icon.png"}}, '
                '"options_page": "./options.html", '
                '"side_panel": {"default_path": "./popup.html"}}\n'
            )
            issues = check_security(repo_root)
            self.assertTrue(any("governed extension asset surface" in issue for issue in issues))

    def test_security_rejects_malformed_manifest_action_shape(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_security_tree(repo_root)
            (repo_root / "apps" / "extension" / "manifest.json").write_text(
                '{"icons": {"128": "staticshock_icon.png"}, '
                '"action": "staticshock_icon.png", '
                '"options_page": "./options.html", '
                '"side_panel": {"default_path": "./popup.html"}}\n'
            )
            issues = check_security(repo_root)
            self.assertTrue(any("must stay mapping-shaped" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
