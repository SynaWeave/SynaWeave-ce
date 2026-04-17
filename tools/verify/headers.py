"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify canonical TL;DR headers for governed source and config files under policy

- Later Extension Points:
    --> widen covered file patterns only when more governed language families are activated

- Role:
    --> checks top-of-file TL;DR markers for governed source and config families under policy
    --> blocks extra Python docstrings and extra TypeScript or JavaScript block comments

- Exports:
    --> `check_headers()`

- Consumed By:
    --> `tools.verify.main` during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path
from typing import Iterable, List

from tools.verify.policy import CODE_HEADER_TEMPLATE_FILE, HEADER_MARKERS, HEADER_PATTERNS

PY_SHEBANG_RE = re.compile(r"^#!")
PY_ENCODING_RE = re.compile(r"^#.*coding[:=]\s*[-\w.]+")
HASH_SHEBANG_RE = re.compile(r"^#!")
PY_HEADER_RE = re.compile(r'^(?P<quote>"""|\'\'\')(?P<body>.*?)(?P=quote)', re.DOTALL)
TS_HEADER_RE = re.compile(r'^/\*(?P<body>.*?)\*/', re.DOTALL)
TS_EXTRA_BLOCK_RE = re.compile(r'/\*.*?\*/', re.DOTALL)
PY_EXTRA_DOCSTRING_RE = re.compile(r'"""|\'\'\'')


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _read_text(path: Path) -> str:
    return path.read_text()


def _iter_paths(repo_root: Path, patterns: Iterable[str]) -> list[Path]:
    paths = {path for pattern in patterns for path in repo_root.glob(pattern) if path.is_file()}
    return sorted(paths)


def _check_marker_order(text: str, relative_path: Path, issues: List[str]) -> None:
    previous_index = -1
    for marker in HEADER_MARKERS:
        current_index = text.find(marker, previous_index + 1)
        if current_index == -1:
            _add_issue(issues, f"header missing required marker '{marker}': {relative_path}")
            return
        previous_index = current_index


def _check_detail_lines(text: str, relative_path: Path, issues: List[str]) -> None:
    for section in HEADER_MARKERS[1:]:
        next_sections = [marker for marker in HEADER_MARKERS if marker != section]
        start_index = text.find(section)
        end_index = len(text)
        for marker in next_sections:
            marker_index = text.find(marker, start_index + len(section))
            if marker_index != -1:
                end_index = min(end_index, marker_index)
        block = text[start_index:end_index]
        if '-->' not in block:
            _add_issue(
                issues,
                f"header section lacks '-->' detail lines for '{section}': {relative_path}",
            )


def _check_python_header(path: Path, repo_root: Path, issues: List[str]) -> None:
    text = _read_text(path)
    relative_path = path.relative_to(repo_root)
    lines = text.splitlines(keepends=True)
    index = 0
    # Skip interpreter and encoding prologue lines
    # Python allows them before the module docstring
    while index < len(lines) and (
        PY_SHEBANG_RE.match(lines[index]) or PY_ENCODING_RE.match(lines[index])
    ):
        index += 1
    remaining = ''.join(lines[index:])
    match = PY_HEADER_RE.match(remaining)
    if match is None:
        _add_issue(issues, f"python file missing top-of-file TL;DR docstring: {relative_path}")
        return
    header_body = match.group('body')
    _check_marker_order(header_body, relative_path, issues)
    _check_detail_lines(header_body, relative_path, issues)
    trailing = remaining[match.end():]
    # Require a clean break after the header so file theory never bleeds into code on the same line
    if trailing and not trailing.startswith('\n'):
        _add_issue(
            issues,
            f"python header must end before a blank line and code body: {relative_path}",
        )
    # Count later triple-quoted strings
    # The TL;DR block stays the only file-level multiline comment
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    triple_tokens = [
        token
        for token in tokens
        if token.type == tokenize.STRING and PY_EXTRA_DOCSTRING_RE.match(token.string)
    ]
    if len(triple_tokens) > 1:
        _add_issue(
            issues,
            "python file contains extra triple-quoted blocks outside TL;DR header: "
            f"{relative_path}",
        )
def _check_block_comment_header(
    path: Path,
    repo_root: Path,
    issues: List[str],
    *,
    kind: str,
    allow_extra_blocks: bool = False,
) -> None:
    text = _read_text(path)
    relative_path = path.relative_to(repo_root)
    # Match only the leading block comment so the TL;DR contract stays top-of-file
    match = TS_HEADER_RE.match(text)
    if match is None:
        _add_issue(
            issues,
            f"{kind} file missing top-of-file TL;DR block comment: {relative_path}",
        )
        return
    header_body = match.group('body')
    _check_marker_order(header_body, relative_path, issues)
    _check_detail_lines(header_body, relative_path, issues)
    trailing = text[match.end():]
    # Force a clean separator after the header so local theory starts in the body not in the wrapper
    if trailing and not trailing.startswith('\n'):
        _add_issue(
            issues,
            f"{kind} header must end before a blank line and code body: {relative_path}",
        )
    # Wrapped JS or TS families ban later block comments
    # Line comments carry local intent there
    if not allow_extra_blocks and TS_EXTRA_BLOCK_RE.search(trailing):
        _add_issue(
            issues,
            f"{kind} file contains extra block comments outside TL;DR header: {relative_path}",
        )


def _normalize_hash_comment_header(text: str) -> str:
    normalized_lines: list[str] = []
    for line in text.splitlines():
        # Strip the hash prefix
        # Marker checks stay syntax-agnostic across hash-comment families
        if line.startswith('# '):
            normalized_lines.append(line[2:])
            continue
        if line.startswith('#'):
            normalized_lines.append(line[1:])
            continue
        normalized_lines.append(line)
    return '\n'.join(normalized_lines)


def _check_hash_comment_header(
    path: Path,
    repo_root: Path,
    issues: List[str],
    *,
    kind: str,
    allow_shebang: bool = False,
    require_shebang: bool = False,
) -> None:
    text = _read_text(path)
    relative_path = path.relative_to(repo_root)
    lines = text.splitlines()
    comment_lines: list[str] = []
    index = 0
    # Shell keeps the shebang first
    # Treat it as transport metadata rather than part of the TL;DR block
    has_shebang = index < len(lines) and HASH_SHEBANG_RE.match(lines[index]) is not None
    if require_shebang and not has_shebang:
        _add_issue(
            issues,
            f"{kind} file must begin with a shebang before the TL;DR block: {relative_path}",
        )
        return
    if allow_shebang and has_shebang:
        index += 1
    while index < len(lines) and lines[index].startswith('#'):
        comment_lines.append(lines[index])
        index += 1
    if not comment_lines:
        _add_issue(issues, f"{kind} file missing top-of-file TL;DR comment block: {relative_path}")
        return
    # Normalize comment leaders away so one marker order check can cover YAML TOML shell and dotenv
    normalized = _normalize_hash_comment_header('\n'.join(comment_lines))
    _check_marker_order(normalized, relative_path, issues)
    _check_detail_lines(normalized, relative_path, issues)


def check_headers(repo_root: Path) -> List[str]:
    issues: List[str] = []

    template_path = repo_root / 'docs' / 'templates' / CODE_HEADER_TEMPLATE_FILE
    if not template_path.exists():
        _add_issue(
            issues,
            f"missing required code header template: docs/templates/{CODE_HEADER_TEMPLATE_FILE}",
        )

    for path in _iter_paths(repo_root, HEADER_PATTERNS['python']):
        _check_python_header(path, repo_root, issues)
    for path in _iter_paths(repo_root, HEADER_PATTERNS['typescript']):
        _check_block_comment_header(path, repo_root, issues, kind='typescript')
    for path in _iter_paths(repo_root, HEADER_PATTERNS['javascript']):
        _check_block_comment_header(path, repo_root, issues, kind='javascript')
    for path in _iter_paths(repo_root, HEADER_PATTERNS['css']):
        _check_block_comment_header(
            path,
            repo_root,
            issues,
            kind='css',
            allow_extra_blocks=True,
        )
    for path in _iter_paths(repo_root, HEADER_PATTERNS['yaml']):
        _check_hash_comment_header(path, repo_root, issues, kind='yaml')
    for path in _iter_paths(repo_root, HEADER_PATTERNS['toml']):
        _check_hash_comment_header(path, repo_root, issues, kind='toml')
    for path in _iter_paths(repo_root, HEADER_PATTERNS['shell']):
        _check_hash_comment_header(
            path,
            repo_root,
            issues,
            kind='shell',
            allow_shebang=True,
            require_shebang=True,
        )
    for path in _iter_paths(repo_root, HEADER_PATTERNS['dotenv']):
        _check_hash_comment_header(path, repo_root, issues, kind='dotenv')

    return issues
