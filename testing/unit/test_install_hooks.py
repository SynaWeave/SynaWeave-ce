"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify git hook installation writes delegating wrappers so local
            hooks track the current repo-owned hook files

- Later Extension Points:
    --> add more wrapper assertions only when the installer owns more local
    --> hook metadata later

- Role:
    --> covers wrapper generation against isolated temporary repositories
    --> verifies stale copied hook bodies are replaced by executable delegates

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import io
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import install_hooks


class TestInstallHooks(unittest.TestCase):
    @staticmethod
    def build_legacy_repo_hook_copy() -> str:
        return "\n".join(
            (
                "#!/usr/bin/env perl",
                "#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
                "# TL;DR  -->  legacy copied repo hook body",
                "#",
                "# - Consumed By:",
                "#   --> local git hook execution after `python3 tools/install_hooks.py`",
                "# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
                "print \"legacy repo hook\";",
                "",
            )
        )

    def capture_main(self, repo_root: Path) -> tuple[int, str]:
        stream = io.StringIO()
        install_path = repo_root / "tools" / "install_hooks.py"
        with patch.object(install_hooks, "__file__", str(install_path)):
            with redirect_stdout(stream):
                exit_code = install_hooks.main()
        return exit_code, stream.getvalue()

    def test_install_writes_delegating_wrapper_for_each_repo_hook(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            hooks_source_dir = repo_root / "tools" / "hooks"
            hooks_source_dir.mkdir(parents=True)
            (repo_root / ".git").mkdir()
            (hooks_source_dir / "pre-push").write_text("#!/usr/bin/env perl\n", encoding="utf-8")
            (hooks_source_dir / "pre-commit").write_text("#!/usr/bin/env perl\n", encoding="utf-8")

            exit_code, output = self.capture_main(repo_root)

            self.assertEqual(exit_code, 0)
            self.assertIn("Git hooks installed from tools/hooks", output)

            pre_push = (repo_root / ".git" / "hooks" / "pre-push").read_text(
                encoding="utf-8"
            )
            self.assertEqual(
                pre_push,
                install_hooks._build_wrapper("pre-push"),
            )
            self.assertIn('exec "$repo_root/tools/hooks/pre-push" "$@"', pre_push)

            pre_commit_path = repo_root / ".git" / "hooks" / "pre-commit"
            self.assertTrue(pre_commit_path.exists())
            self.assertTrue(pre_commit_path.stat().st_mode & stat.S_IXUSR)

    def test_install_replaces_stale_copied_hook_body_with_wrapper(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            hooks_source_dir = repo_root / "tools" / "hooks"
            hooks_source_dir.mkdir(parents=True)
            (repo_root / ".git" / "hooks").mkdir(parents=True)
            (hooks_source_dir / "pre-push").write_text("#!/usr/bin/env perl\n", encoding="utf-8")
            stale_hook = repo_root / ".git" / "hooks" / "pre-push"
            stale_hook.write_text(
                "#!/usr/bin/env perl\nprint \"old copied hook\";\n", encoding="utf-8"
            )

            exit_code, _ = self.capture_main(repo_root)

            self.assertEqual(exit_code, 0)
            installed_hook = stale_hook.read_text(encoding="utf-8")
            self.assertEqual(installed_hook, install_hooks._build_wrapper("pre-push"))
            self.assertNotIn("old copied hook", installed_hook)

    def test_reinstall_removes_stale_repo_generated_wrapper_for_removed_hook_name(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            hooks_source_dir = repo_root / "tools" / "hooks"
            installed_hooks_dir = repo_root / ".git" / "hooks"
            hooks_source_dir.mkdir(parents=True)
            installed_hooks_dir.mkdir(parents=True)
            (hooks_source_dir / "pre-push").write_text("#!/usr/bin/env perl\n", encoding="utf-8")
            stale_wrapper = installed_hooks_dir / "post-merge"
            stale_wrapper.write_text(
                install_hooks._build_wrapper("post-merge"), encoding="utf-8"
            )
            self.assertTrue(install_hooks._is_repo_wrapper(stale_wrapper))

            exit_code, _ = self.capture_main(repo_root)

            self.assertEqual(exit_code, 0)
            self.assertFalse(stale_wrapper.exists())
            self.assertTrue((installed_hooks_dir / "pre-push").exists())

    def test_reinstall_removes_stale_legacy_repo_hook_copy_for_removed_hook_name(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            hooks_source_dir = repo_root / "tools" / "hooks"
            installed_hooks_dir = repo_root / ".git" / "hooks"
            hooks_source_dir.mkdir(parents=True)
            installed_hooks_dir.mkdir(parents=True)
            (hooks_source_dir / "pre-push").write_text("#!/usr/bin/env perl\n", encoding="utf-8")
            stale_legacy_hook = installed_hooks_dir / "post-merge"
            stale_legacy_hook.write_text(
                self.build_legacy_repo_hook_copy(), encoding="utf-8"
            )
            self.assertTrue(install_hooks._is_legacy_repo_hook_copy(stale_legacy_hook))

            exit_code, _ = self.capture_main(repo_root)

            self.assertEqual(exit_code, 0)
            self.assertFalse(stale_legacy_hook.exists())
            self.assertTrue((installed_hooks_dir / "pre-push").exists())

    def test_reinstall_preserves_non_repo_local_hook_when_name_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            hooks_source_dir = repo_root / "tools" / "hooks"
            installed_hooks_dir = repo_root / ".git" / "hooks"
            hooks_source_dir.mkdir(parents=True)
            installed_hooks_dir.mkdir(parents=True)
            (hooks_source_dir / "pre-push").write_text("#!/usr/bin/env perl\n", encoding="utf-8")
            custom_hook = installed_hooks_dir / "post-merge"
            custom_hook.write_text(
                "#!/bin/sh\n# local custom hook\nexit 0\n", encoding="utf-8"
            )
            self.assertFalse(install_hooks._is_repo_wrapper(custom_hook))

            exit_code, _ = self.capture_main(repo_root)

            self.assertEqual(exit_code, 0)
            self.assertTrue(custom_hook.exists())
            self.assertEqual(
                custom_hook.read_text(encoding="utf-8"),
                "#!/bin/sh\n# local custom hook\nexit 0\n",
            )

    def test_reinstall_preserves_local_hook_without_legacy_repo_copy_signature(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            hooks_source_dir = repo_root / "tools" / "hooks"
            installed_hooks_dir = repo_root / ".git" / "hooks"
            hooks_source_dir.mkdir(parents=True)
            installed_hooks_dir.mkdir(parents=True)
            (hooks_source_dir / "pre-push").write_text("#!/usr/bin/env perl\n", encoding="utf-8")
            custom_hook = installed_hooks_dir / "post-merge"
            custom_hook.write_text(
                "#!/bin/sh\n"
                "# TL;DR  --> local custom hook\n"
                "# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
                "exit 0\n",
                encoding="utf-8",
            )
            self.assertFalse(install_hooks._is_legacy_repo_hook_copy(custom_hook))

            exit_code, _ = self.capture_main(repo_root)

            self.assertEqual(exit_code, 0)
            self.assertTrue(custom_hook.exists())


if __name__ == "__main__":
    unittest.main()
