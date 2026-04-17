"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  install the governed git hook set into the local repository hook path

- Later Extension Points:
    --> add narrower install filtering only if hook families split further later

- Role:
    --> copies repo-owned hook files into `.git/hooks`
    --> preserves executable permissions for the installed local hook scripts

- Exports:
    --> `main()`

- Consumed By:
    --> local operators running `bun run hooks:install`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import shutil
import stat
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    hooks_dir = repo_root / ".git" / "hooks"
    source_dir = repo_root / "tools" / "hooks"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue
        target_path = hooks_dir / path.name
        shutil.copy2(path, target_path)
        target_path.chmod(target_path.stat().st_mode | stat.S_IXUSR)

    print("Git hooks installed from tools/hooks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
