"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  block committed suppression directives and config escape hatches in governed files

- Later Extension Points:
    --> add more banned suppression patterns only when new governed toolchains enter baseline

- Role:
    --> scans governed source and config files for banned suppression comments and directives
    --> rejects repo-level config escapes that hide warnings or type issues instead of fixing them

- Exports:
    --> `check_suppressions()`

- Consumed By:
    --> `tools.verify.main` during repository verification and focused suppression unit tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import io
import tokenize
from pathlib import Path
from typing import Iterable, List

BANNED_TEXT_PATTERNS = {
    "python": (
        "# noqa",
        "# ruff: noqa",
        "# type: ignore",
        "# pyright: ignore",
    ),
    "typescript": (
        "@ts-ignore",
        "@ts-expect-error",
        "@ts-nocheck",
        "eslint-disable",
        "biome-ignore",
    ),
}

PATTERN_MAP = {
    "python": ("tools/**/*.py", "testing/**/*.py", "python/**/*.py"),
    "typescript": (
        "apps/**/*.ts",
        "apps/**/*.tsx",
        "apps/**/*.js",
        "apps/**/*.jsx",
        "packages/**/*.ts",
        "packages/**/*.tsx",
        "packages/**/*.js",
        "packages/**/*.jsx",
        "tools/**/*.ts",
    ),
}

BANNED_TSCONFIG_FLAGS = {
    "skipLibCheck",
    "ignoreDeprecations",
}


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _iter_paths(repo_root: Path, patterns: Iterable[str]) -> list[Path]:
    paths = {path for pattern in patterns for path in repo_root.glob(pattern) if path.is_file()}
    return sorted(paths)


def _check_python_suppressions(repo_root: Path, issues: List[str]) -> None:
    for path in _iter_paths(repo_root, PATTERN_MAP["python"]):
        try:
            tokens = tokenize.generate_tokens(io.StringIO(path.read_text()).readline)
            for token in tokens:
                if token.type != tokenize.COMMENT:
                    continue
                for banned in BANNED_TEXT_PATTERNS["python"]:
                    if banned in token.string:
                        _add_issue(
                            issues,
                            "suppression directive "
                            f"'{banned}' is banned in {path.relative_to(repo_root)}",
                        )
        except tokenize.TokenError as exc:
            _add_issue(
                issues,
                "unable to parse Python file while checking suppressions: "
                f"{path.relative_to(repo_root)}: {exc}",
            )


def _check_typescript_suppressions(repo_root: Path, issues: List[str]) -> None:
    for path in _iter_paths(repo_root, PATTERN_MAP["typescript"]):
        text = path.read_text()
        for banned in BANNED_TEXT_PATTERNS["typescript"]:
            if banned in text:
                _add_issue(
                    issues,
                    f"suppression directive '{banned}' is banned in {path.relative_to(repo_root)}",
                )


def _check_tsconfig(repo_root: Path, issues: List[str]) -> None:
    tsconfig_path = repo_root / "tsconfig.json"
    if not tsconfig_path.exists():
        return

    text = tsconfig_path.read_text()
    for flag in BANNED_TSCONFIG_FLAGS:
        if f'"{flag}"' in text:
            _add_issue(issues, f"tsconfig.json must not set suppression flag '{flag}'")


def check_suppressions(repo_root: Path) -> List[str]:
    issues: List[str] = []
    _check_python_suppressions(repo_root, issues)
    _check_typescript_suppressions(repo_root, issues)
    _check_tsconfig(repo_root, issues)
    return issues
