"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  validate commit subjects and local commit ranges for durable plain-English history

- Later Extension Points:
    --> add body-level and cross-branch commit checks only when repo governance expands further

- Role:
    --> validates commit messages against the conventional scoped format and shared-theory wording
    --> checks local commit ranges for duplicate subjects so same-session history stays DRY

- Exports:
    --> `validate_message()`
    --> `check_commit_head()`
    --> `check_commit_message_file()`
    --> `check_commit_range()`

- Consumed By:
    --> git hooks and repository verification checks enforcing commit policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Iterable, List, Tuple

from tools.verify.policy import (
    ALLOWED_CHANGE_SCOPES,
    ALLOWED_CHANGE_TYPES,
    BANNED_TYPE_SCOPE_PAIRS,
    MIN_PR_TITLE_WORDS,
    MIN_SUBJECT_WORDS,
    SHARED_BANNED_PHRASES,
    SHARED_BANNED_PREFIXES,
    SHARED_BANNED_WORDS,
    build_shared_phrase_pattern,
    build_shared_prefix_pattern,
)

COMMIT_PATTERN = re.compile(
    r"^(?P<type>[a-z]+)\((?P<scope>[a-z]+)\):\s+(?P<subject>.+)$"
)
PR_TITLE_PATTERN = re.compile(
    r"^(?:S\d{3}/d\d+(?: [a-z0-9 -]+)? --> )?"
    r"(?P<type>[a-z]+)\((?P<scope>[a-z]+)\):\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
RAW_IDENTIFIER_RE = re.compile(r"\b[a-z]+_[a-z0-9_]+\b|\b[a-z]+[A-Z][A-Za-z0-9]*\b")


FLUFF_WORD_RE = build_shared_phrase_pattern(SHARED_BANNED_WORDS)
FLUFF_PHRASE_RE = build_shared_phrase_pattern(SHARED_BANNED_PHRASES)
FLUFF_PREFIX_RE = build_shared_prefix_pattern(SHARED_BANNED_PREFIXES)
SUBJECT_WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.IGNORECASE)


def _subject_words(subject: str) -> list[str]:
    return [part.lower() for part in SUBJECT_WORD_RE.findall(subject)]


def _subject_word_count(subject: str) -> int:
    return len(_subject_words(subject))


def _normalize_subject(subject: str) -> str:
    lowered = re.sub(r"[^a-z0-9\s]", " ", subject.lower())
    without_phrases = FLUFF_PHRASE_RE.sub(" ", lowered)
    without_words = FLUFF_WORD_RE.sub(" ", without_phrases)
    without_prefixes = FLUFF_PREFIX_RE.sub(" ", without_words)
    return " ".join(without_prefixes.split())


def _validate_subject(subject: str, *, min_words: int, commit_type: str, scope: str) -> List[str]:
    issues: List[str] = []
    subject_words = _subject_words(subject)
    if len(subject_words) < min_words:
        issues.append(f"commit subject must be at least {min_words} words")
    if commit_type in subject_words:
        issues.append(f"commit subject must not repeat change type word: {commit_type}")
    if scope in subject_words:
        issues.append(f"commit subject must not repeat change scope word: {scope}")
    if RAW_IDENTIFIER_RE.search(subject):
        issues.append("commit subject should prefer plain English over raw code identifiers")
    has_fluff = (
        FLUFF_WORD_RE.search(subject)
        or FLUFF_PHRASE_RE.search(subject)
        or FLUFF_PREFIX_RE.search(subject)
    )
    if has_fluff:
        issues.append("commit subject must remove fluff and filler words or phrases")
    return issues


def _validate_match(match: re.Match[str] | None, *, min_words: int) -> List[str]:
    if not match:
        return ["commit message must use format <type>(<scope>): <description>"]

    issues: List[str] = []
    commit_type = match.group("type").lower()
    scope = match.group("scope").lower()
    subject = match.group("subject").strip()
    if commit_type not in ALLOWED_CHANGE_TYPES:
        issues.append(f"unsupported commit type: {commit_type}")
    if scope not in ALLOWED_CHANGE_SCOPES:
        issues.append(f"unsupported commit scope: {scope}")
    banned_pair_message = BANNED_TYPE_SCOPE_PAIRS.get((commit_type, scope))
    if banned_pair_message:
        issues.append(banned_pair_message)
    issues.extend(
        _validate_subject(subject, min_words=min_words, commit_type=commit_type, scope=scope)
    )
    return issues


def validate_message(message: str, *, min_words: int = MIN_SUBJECT_WORDS) -> List[str]:
    first_line = message.strip().splitlines()[0] if message.strip() else ""
    if not first_line:
        return ["commit message must include a subject line"]
    return _validate_match(COMMIT_PATTERN.match(first_line), min_words=min_words)


def _git_output(repo_root: Path, args: Iterable[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=repo_root, text=True).strip()


def _try_git_output(repo_root: Path, args: Iterable[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return None


def _resolve_commit_target(repo_root: Path) -> str | None:
    explicit_head = os.environ.get("VERIFY_COMMIT_HEAD", "").strip()
    target = explicit_head or "HEAD"
    return _try_git_output(repo_root, ["rev-parse", "--verify", f"{target}^{{commit}}"])


def _derive_commit_base(repo_root: Path) -> str | None:
    target_ref = _resolve_commit_target(repo_root)
    if not target_ref:
        return None

    explicit_base = os.environ.get("VERIFY_COMMIT_BASE", "").strip()
    if explicit_base:
        if set(explicit_base) == {"0"}:
            return _try_git_output(repo_root, ["rev-list", "--max-parents=0", "HEAD"])
        return explicit_base

    github_base_ref = os.environ.get("GITHUB_BASE_REF", "").strip()
    if github_base_ref:
        remote_base = f"origin/{github_base_ref}"
        return _try_git_output(repo_root, ["merge-base", target_ref, remote_base])

    return _try_git_output(repo_root, ["merge-base", target_ref, "@{upstream}"])


def _resolve_commit_base(repo_root: Path) -> str | None:
    base = _derive_commit_base(repo_root)
    if not base:
        return None
    return _try_git_output(repo_root, ["rev-parse", "--verify", f"{base}^{{commit}}"])


def check_commit_range(repo_root: Path) -> List[str]:
    issues: List[str] = []
    target_head = _resolve_commit_target(repo_root)
    if not target_head:
        return []

    base = _resolve_commit_base(repo_root)
    if not base:
        return []

    log_output = _try_git_output(repo_root, ["log", "--format=%H%x1f%s", f"{base}..{target_head}"])
    if log_output is None:
        return []

    if not log_output:
        return []

    seen_subjects: dict[str, str] = {}
    for raw_line in log_output.splitlines():
        commit_hash, subject_line = raw_line.split("\x1f", 1)
        subject_issues = validate_message(subject_line)
        for issue in subject_issues:
            issues.append(f"commit {commit_hash[:7]} invalid: {issue}")

        normalized = _normalize_subject(subject_line)
        if normalized in seen_subjects:
            issues.append(
                "commit range must stay DRY and unique; duplicate subject intent found in "
                f"{seen_subjects[normalized]} and {commit_hash[:7]}"
            )
            continue
        seen_subjects[normalized] = commit_hash[:7]

    return issues


def check_commit_head(repo_root: Path) -> List[str]:
    target_head = _resolve_commit_target(repo_root)
    if target_head is None:
        return []

    explicit_head = os.environ.get("VERIFY_COMMIT_HEAD", "").strip()
    base = _resolve_commit_base(repo_root)
    if base is None and not explicit_head and os.environ.get("GITHUB_ACTIONS") != "true":
        return []

    if base is None and not explicit_head:
        return []

    try:
        message = _git_output(repo_root, ["log", "-1", "--pretty=%B", target_head])
    except subprocess.CalledProcessError as exc:
        return [
            "unable to read HEAD commit message from git",
            f"git log failed: {exc}",
        ]

    issues = [f"HEAD commit message invalid: {issue}" for issue in validate_message(message)]
    if base is not None:
        issues.extend(check_commit_range(repo_root))
    return issues


def check_commit_message_file(message_file: Path) -> Tuple[bool, List[str]]:
    message = message_file.read_text().strip()
    issues = validate_message(message)
    return (len(issues) == 0, issues)


def validate_pr_title_message(title: str) -> List[str]:
    normalized_title = title.strip()
    if not normalized_title:
        return ["PR title must not be empty"]
    return [
        issue.replace("commit message", "PR title").replace("commit subject", "PR title subject")
        for issue in _validate_match(
            PR_TITLE_PATTERN.match(normalized_title),
            min_words=MIN_PR_TITLE_WORDS,
        )
    ]
