"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify sprint ADR files against the governed Sprint 1 ledger structure and writing rules

- Later Extension Points:
    --> widen entry-level ADR checks only when the canonical sprint ADR template grows further

- Role:
    --> validates sprint ADR filenames sections question order and answer density
        against the canonical ledger
    --> blocks raw identifiers filler wording and status drift inside governed sprint ADR records

- Exports:
    --> `check_adrs()`

- Consumed By:
    --> `tools.verify.main` during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from tools.verify.policy import (
    SHARED_BANNED_PHRASES,
    SHARED_BANNED_PREFIXES,
    SHARED_BANNED_WORDS,
    build_shared_phrase_pattern,
    build_shared_prefix_pattern,
)

ADR_FILENAME_RE = re.compile(r"^sprint-\d{3}\.md$")
ADR_ENTRY_HEADING_RE = re.compile(
    r"^###\s+(?P<identifier>D\d+(?:-T\d+)?)\s+-\s+(?P<title>.+)$",
    re.MULTILINE,
)
ADR_STATUS_SECTION_RE = re.compile(
    r"^## Current Status\n(?P<body>.*?)(?:\n---\n|\n##\s)",
    re.MULTILINE | re.DOTALL,
)
ADR_ENTRY_SECTION_RE = re.compile(
    r"^###\s+(?P<identifier>D\d+(?:-T\d+)?)\s+-\s+(?P<title>.+)$",
    re.MULTILINE,
)
ADR_QUESTION_LINE_RE = re.compile(r"^- \*\*\*(?P<question>.+?)\*\*\*$")
ADR_DECISION_INDEX_HEADER_RE = re.compile(r"^\|\s*Decision\s*\|\s*Status\s*\|$", re.IGNORECASE)
ADR_DECISION_INDEX_SEPARATOR_RE = re.compile(r"^\|\s*-+\s*\|\s*-+\s*\|$")
ADR_DECISION_INDEX_ROW_RE = re.compile(
    r"^\|\s*(?P<identifier>D\d+(?:-T\d+)?)\s+-\s+(?P<title>.+?)\s*\|\s*(?P<status>.+?)\s*\|$"
)
RAW_IDENTIFIER_RE = re.compile(r"\b[a-z]+_[a-z0-9_]+\b|\b[a-z]+[A-Z][A-Za-z0-9]*\b")
FLUFF_WORD_RE = build_shared_phrase_pattern(SHARED_BANNED_WORDS)
FLUFF_PHRASE_RE = build_shared_phrase_pattern(SHARED_BANNED_PHRASES)
FLUFF_PREFIX_RE = build_shared_prefix_pattern(SHARED_BANNED_PREFIXES)
MIN_ANSWER_BULLETS = 3
MIN_ANSWER_WORDS = 14

REQUIRED_ADR_SECTIONS = (
    "## TL;DR",
    "## ADR Guide",
    "### How To Use This File (Rules)",
    "### Decision Entry Template",
    "## Current Status",
    "## Entries",
)

REQUIRED_ADR_QUESTIONS = (
    "What was built?",
    "Why was it chosen?",
    "What boundaries does it own?",
    "What breaks if it changes?",
    "What known edge cases or failure modes matter here?",
    "Why does this work matter?",
    "What capability does it unlock?",
    "Why is the chosen design safer or more scalable?",
    "What trade-off did the team accept?",
)


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _is_expected_filename(path: Path) -> bool:
    return bool(ADR_FILENAME_RE.match(path.name))


def _check_plain_english(text: str, relative_path: str, issues: List[str]) -> None:
    cleaned = _strip_code_fences(text)
    cleaned = re.sub(r"`[^`/]+/[^`]+`", "", cleaned)
    if RAW_IDENTIFIER_RE.search(cleaned):
        _add_issue(issues, f"ADR should prefer plain English over raw identifiers: {relative_path}")
    if (
        FLUFF_WORD_RE.search(cleaned)
        or FLUFF_PHRASE_RE.search(cleaned)
        or FLUFF_PREFIX_RE.search(cleaned)
    ):
        _add_issue(issues, f"ADR must remove fluff and filler wording: {relative_path}")


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'/-]+\b", text))


def _split_entry_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(ADR_ENTRY_SECTION_RE.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group("identifier"), text[start:end]))
    return blocks


def _parse_decision_index(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    entries_start = next(
        (index for index, line in enumerate(lines) if line.strip() == "## Entries"),
        None,
    )
    if entries_start is None:
        return []

    for index in range(entries_start + 1, len(lines)):
        line = lines[index].strip()
        if not line or line == "---":
            continue
        if not ADR_DECISION_INDEX_HEADER_RE.match(line):
            return []
        if index + 1 >= len(lines) or not ADR_DECISION_INDEX_SEPARATOR_RE.match(
            lines[index + 1].strip()
        ):
            return []

        rows: list[tuple[str, str]] = []
        row_index = index + 2
        while row_index < len(lines):
            row_line = lines[row_index].strip()
            if not row_line:
                row_index += 1
                continue
            if row_line == "---":
                break
            match = ADR_DECISION_INDEX_ROW_RE.match(row_line)
            if match is None:
                return []
            rows.append((match.group("identifier"), match.group("title").strip()))
            row_index += 1
        return rows

    return []


def _check_decision_index(text: str, relative_path: str, issues: List[str]) -> None:
    index_entries = _parse_decision_index(text)
    if not index_entries:
        _add_issue(issues, f"ADR must include a parseable decision index table: {relative_path}")
        return

    heading_entries = [
        (match.group("identifier"), match.group("title").strip())
        for match in ADR_ENTRY_HEADING_RE.finditer(text)
    ]
    if index_entries != heading_entries:
        _add_issue(
            issues,
            "ADR decision index rows must match decision headings exactly: "
            f"{relative_path}",
        )


def _check_current_status(text: str, relative_path: str, issues: List[str]) -> None:
    match = ADR_STATUS_SECTION_RE.search(text + "\n## sentinel\n")
    if match is None:
        _add_issue(issues, f"ADR missing parseable Current Status section: {relative_path}")
        return

    status_lines = [line.strip() for line in match.group("body").splitlines()]
    status_bullets = [line for line in status_lines if line.startswith("- ")]
    if not status_bullets:
        _add_issue(issues, f"ADR Current Status must include at least one bullet: {relative_path}")
    if len(status_bullets) > 10:
        _add_issue(issues, f"ADR Current Status must stay at 10 bullets or fewer: {relative_path}")


def _check_entry_questions(entry_text: str, relative_path: str, issues: List[str]) -> None:
    lines = [line.rstrip() for line in entry_text.splitlines()]
    question_positions: list[int] = []
    seen_questions: list[str] = []
    for index, line in enumerate(lines):
        match = ADR_QUESTION_LINE_RE.match(line.strip())
        if match:
            question_positions.append(index)
            seen_questions.append(match.group("question"))

    if seen_questions != list(REQUIRED_ADR_QUESTIONS):
        _add_issue(
            issues,
            f"ADR decision entries must keep the governed question set and order: {relative_path}",
        )
        return

    for index, question in enumerate(seen_questions):
        start = question_positions[index] + 1
        end = question_positions[index + 1] if index + 1 < len(question_positions) else len(lines)
        answer_bullets = [
            line.strip()[2:].strip()
            for line in lines[start:end]
            if line.startswith("  - ")
        ]
        if len(answer_bullets) < MIN_ANSWER_BULLETS:
            _add_issue(
                issues,
                "ADR question "
                f"'{question}' needs at least {MIN_ANSWER_BULLETS} answer bullets: "
                f"{relative_path}",
            )
            continue
        for answer in answer_bullets:
            if _word_count(answer) < MIN_ANSWER_WORDS:
                _add_issue(
                    issues,
                    "ADR answer bullets must use at least "
                    f"{MIN_ANSWER_WORDS} words: {relative_path}",
                )
                break


def _check_entries(text: str, relative_path: str, issues: List[str]) -> None:
    entry_blocks = _split_entry_blocks(text)
    if not entry_blocks:
        _add_issue(
            issues,
            f"ADR must include at least one governed decision entry: {relative_path}",
        )
        return

    for _, entry_text in entry_blocks:
        _check_entry_questions(entry_text, relative_path, issues)


def check_adrs(repo_root: Path) -> List[str]:
    issues: List[str] = []
    adrs_dir = repo_root / "docs" / "adrs"
    if not adrs_dir.exists():
        return ["docs/adrs directory is required for ADR records"]

    adr_files = sorted([path for path in adrs_dir.glob("*.md") if path.is_file()])
    if not adr_files:
        return ["at least one ADR file is required in docs/adrs"]

    for path in adr_files:
        relative_path = f"docs/adrs/{path.name}"
        if not _is_expected_filename(path):
            _add_issue(
                issues,
                f"ADR filename does not follow sprint pattern sprint-###.md: {relative_path}",
            )
            continue

        text = path.read_text()
        for section in REQUIRED_ADR_SECTIONS:
            if section not in text:
                _add_issue(issues, f"ADR missing required section '{section}': {relative_path}")
        _check_current_status(text, relative_path, issues)
        _check_decision_index(text, relative_path, issues)
        _check_entries(text, relative_path, issues)
        _check_plain_english(text, relative_path, issues)

    if not (adrs_dir / "sprint-001.md").exists():
        _add_issue(issues, "docs/adrs must include sprint-001.md for Foundation")

    return issues
