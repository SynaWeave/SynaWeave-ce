"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  enforce the repo's comment-heavy local note style through deterministic structure checks

- Later Extension Points:
    --> add more syntax families only when new governed comment-bearing file types become active

- Role:
    --> checks that governed files keep local intent comments instead of long comment-free stretches
    --> blocks commented-out code and CSS comment shapes that would dilute shared theory in review

- Exports:
    --> `check_commentary()`

- Consumed By:
    --> `tools.verify.main` and hook-driven repo verification feedback loops
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path
from typing import Iterable, List

from tools.verify.policy import COMMENT_HEAVY_PATTERNS

COMMENT_FLOOR = 1
CODE_LINE_FLOOR = 20
COMMENTED_OUT_CODE_RE = re.compile(
    r"(^|\s)(const |let |var |function |return |if \(|for \(|while \(|<\w+|chrome\.|export )"
)
PY_HEADER_RE = re.compile(
    r'^(?:#!.*\n)?(?:#.*coding[:=].*\n)?(?P<header>""".*?"""|\'\'\'.*?\'\'\')',
    re.DOTALL,
)
BLOCK_HEADER_RE = re.compile(r'^/\*.*?\*/', re.DOTALL)
HTML_DOCTYPE_RE = re.compile(r'^<!DOCTYPE html>\s*', re.IGNORECASE)
HTML_COMMENT_RE = re.compile(r'<!--(?P<body>.*?)-->', re.DOTALL)
CSS_COMMENT_RE = re.compile(r'/\*(?P<body>.*?)\*/', re.DOTALL)


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _iter_paths(repo_root: Path, patterns: Iterable[str]) -> list[Path]:
    paths = {path for pattern in patterns for path in repo_root.glob(pattern) if path.is_file()}
    return sorted(paths)


def _code_lines(text: str, *, prefixes: tuple[str, ...]) -> int:
    total = 0
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith(prefixes):
            continue
        total += 1
    return total


def _requires_density(relative_path: Path) -> bool:
    return (
        relative_path.parts[:2] == ("apps", "extension")
        or relative_path == Path("tools/verify/headers.py")
        or relative_path == Path("tools/verify/workflows.py")
        or relative_path == Path(".github/workflows/dependency-review.yml")
    )


def _check_minimum_local_comments(
    text: str,
    relative_path: Path,
    issues: List[str],
    *,
    comment_prefixes: tuple[str, ...],
) -> None:
    if not _requires_density(relative_path):
        return

    code_lines = _code_lines(text, prefixes=comment_prefixes)
    if code_lines < CODE_LINE_FLOOR:
        return

    comment_lines = [
        line for line in text.splitlines() if line.strip().startswith(comment_prefixes)
    ]
    if len(comment_lines) < COMMENT_FLOOR:
        _add_issue(
            issues,
            "file needs more local intent comments for the repo note-taking style: "
            f"{relative_path}",
        )


def _check_python(repo_root: Path, issues: List[str]) -> None:
    for path in _iter_paths(repo_root, COMMENT_HEAVY_PATTERNS["python"]):
        text = path.read_text()
        relative_path = path.relative_to(repo_root)
        match = PY_HEADER_RE.match(text)
        trailing = text[match.end():] if match else text
        _check_minimum_local_comments(trailing, relative_path, issues, comment_prefixes=("#",))
        try:
            tokens = tokenize.generate_tokens(io.StringIO(text).readline)
            for token in tokens:
                if token.type == tokenize.COMMENT and COMMENTED_OUT_CODE_RE.search(token.string):
                    _add_issue(issues, f"commented-out code is banned in {relative_path}")
        except tokenize.TokenError:
            continue


def _check_line_comment_family(
    repo_root: Path,
    issues: List[str],
    *,
    kind: str,
) -> None:
    for path in _iter_paths(repo_root, COMMENT_HEAVY_PATTERNS[kind]):
        text = path.read_text()
        relative_path = path.relative_to(repo_root)
        header_match = BLOCK_HEADER_RE.match(text)
        trailing = text[header_match.end():] if header_match else text
        _check_minimum_local_comments(trailing, relative_path, issues, comment_prefixes=("//",))
        for line in trailing.splitlines():
            stripped = line.strip()
            if stripped.startswith("//") and COMMENTED_OUT_CODE_RE.search(stripped[2:]):
                _add_issue(issues, f"commented-out code is banned in {relative_path}")


def _check_hash_family(repo_root: Path, issues: List[str], *, kind: str) -> None:
    for path in _iter_paths(repo_root, COMMENT_HEAVY_PATTERNS[kind]):
        text = path.read_text()
        relative_path = path.relative_to(repo_root)
        lines = text.splitlines()
        index = 1 if lines and lines[0].startswith("#!") else 0
        while index < len(lines) and lines[index].startswith("#"):
            index += 1
        trailing = "\n".join(lines[index:])
        _check_minimum_local_comments(trailing, relative_path, issues, comment_prefixes=("#",))
        for line in trailing.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") and COMMENTED_OUT_CODE_RE.search(stripped[1:]):
                _add_issue(issues, f"commented-out code is banned in {relative_path}")


def _check_css(repo_root: Path, issues: List[str]) -> None:
    for path in _iter_paths(repo_root, COMMENT_HEAVY_PATTERNS["css"]):
        text = path.read_text()
        relative_path = path.relative_to(repo_root)
        header_match = BLOCK_HEADER_RE.match(text)
        trailing = text[header_match.end():] if header_match else text
        comments = list(CSS_COMMENT_RE.finditer(trailing))
        code_lines = _code_lines(trailing, prefixes=("/*", "*", "*/"))
        if code_lines >= CODE_LINE_FLOOR and len(comments) < COMMENT_FLOOR:
            _add_issue(
                issues,
                "file needs more local intent comments for the repo note-taking style: "
                f"{relative_path}",
            )
        for match in comments:
            body = match.group("body")
            if "\n" in body:
                _add_issue(
                    issues,
                    "css comments must stay one physical line per intent outside the TL;DR block: "
                    f"{relative_path}",
                )
                break
            if re.search(r"[.#]?[A-Za-z0-9_-]+\s*\{|[A-Za-z-]+\s*:\s*[^;]+;", body):
                _add_issue(issues, f"commented-out code is banned in {relative_path}")


def _check_html(repo_root: Path, issues: List[str]) -> None:
    for path in _iter_paths(repo_root, COMMENT_HEAVY_PATTERNS["html"]):
        text = path.read_text()
        relative_path = path.relative_to(repo_root)
        body = HTML_DOCTYPE_RE.sub("", text, count=1)
        comments = list(HTML_COMMENT_RE.finditer(body))
        code_lines = _code_lines(body, prefixes=("<!--",))
        if code_lines >= CODE_LINE_FLOOR and len(comments) < COMMENT_FLOOR:
            _add_issue(
                issues,
                "file needs more local intent comments for the repo note-taking style: "
                f"{relative_path}",
            )
        for match in comments:
            comment_body = match.group("body")
            if re.search(r"^\s*</?\w+", comment_body):
                _add_issue(issues, f"commented-out code is banned in {relative_path}")


def check_commentary(repo_root: Path) -> List[str]:
    issues: List[str] = []
    _check_python(repo_root, issues)
    _check_line_comment_family(repo_root, issues, kind="typescript")
    _check_line_comment_family(repo_root, issues, kind="javascript")
    _check_hash_family(repo_root, issues, kind="yaml")
    _check_hash_family(repo_root, issues, kind="toml")
    _check_hash_family(repo_root, issues, kind="shell")
    _check_hash_family(repo_root, issues, kind="dotenv")
    _check_css(repo_root, issues)
    _check_html(repo_root, issues)
    return issues
