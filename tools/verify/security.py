"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  enforce repo-owned secret boundary rules that generic scanners cannot safely model alone

- Later Extension Points:
    --> widen tracked-file and client-boundary rules only when new governed secret surfaces appear

- Role:
    --> rejects tracked secret-bearing file types and unsafe runtime boundary leaks
    --> keeps example env values synthetic so scanner allowlists do not become blind spots

- Exports:
    --> `check_security()`

- Consumed By:
    --> `tools.verify.main` and repo security verification scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import fnmatch
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Mapping

FORBIDDEN_TRACKED_EXACT_NAMES = {
    "id_rsa",
    "id_dsa",
    "id_ed25519",
    "credentials.json",
}

FORBIDDEN_TRACKED_SUFFIXES = (
    ".pem",
    ".key",
    ".p8",
    ".p12",
    ".pkcs12",
    ".pfx",
    ".jks",
    ".keystore",
    ".kdbx",
)

SENSITIVE_ENV_KEYS = (
    "KEY",
    "TOKEN",
    "PASSWORD",
    "SECRET",
    "CREDENTIAL",
)

PLACEHOLDER_MARKERS = (
    "example",
    "local",
    "placeholder",
    "redacted",
    "dummy",
    "sample",
)

CLIENT_LEAK_MARKERS = (
    "SUPABASE_SERVICE_ROLE_KEY",
    "DATABASE_URL",
    "PRIVATE KEY",
    "AUTH_SERVICE_ROLE_ENV",
)

CLIENT_PATTERNS = (
    "apps/**/*.js",
    "apps/**/*.ts",
    "apps/**/*.tsx",
    "apps/**/*.jsx",
    "apps/**/*.html",
    "apps/**/*.css",
    "apps/**/*.json",
)

REQUIRED_GITIGNORE_ENV_RULES = (
    "**/*.env*",
    "!**/*.env.example",
)


@dataclass(frozen=True)
class GitIgnoreRuleSet:
    ignored_env_patterns: tuple[str, ...]
    allowed_env_patterns: tuple[str, ...]


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _manifest_mapping(
    manifest: Mapping[str, Any],
    issues: List[str],
    field_name: str,
) -> Mapping[str, Any]:
    field_value = manifest.get(field_name)
    if field_value is None:
        return {}
    if isinstance(field_value, dict):
        return field_value
    _add_issue(
        issues,
        "extension manifest field must stay mapping-shaped for governed verification: "
        f"{field_name}",
    )
    return {}


def _tracked_files(repo_root: Path) -> list[Path]:
    try:
        output = subprocess.check_output(["git", "ls-files"], cwd=repo_root, text=True)
    except subprocess.CalledProcessError:
        return []
    return [repo_root / line for line in output.splitlines() if line.strip()]


def _iter_paths(repo_root: Path, patterns: Iterable[str]) -> list[Path]:
    paths = {path for pattern in patterns for path in repo_root.glob(pattern) if path.is_file()}
    return sorted(paths)


def _parse_gitignore(repo_root: Path) -> GitIgnoreRuleSet:
    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.exists():
        return GitIgnoreRuleSet(ignored_env_patterns=(), allowed_env_patterns=())

    ignored_env_patterns: list[str] = []
    allowed_env_patterns: list[str] = []
    for raw_line in gitignore_path.read_text().splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        is_allow = stripped.startswith("!")
        pattern = stripped[1:] if is_allow else stripped
        if ".env" not in pattern:
            continue
        if is_allow:
            allowed_env_patterns.append(pattern)
            continue
        ignored_env_patterns.append(pattern)

    return GitIgnoreRuleSet(
        ignored_env_patterns=tuple(ignored_env_patterns),
        allowed_env_patterns=tuple(allowed_env_patterns),
    )


def _matches_gitignore_pattern(relative_path: str, pattern: str) -> bool:
    normalized_pattern = pattern.lstrip("/")
    candidates = {normalized_pattern}
    if normalized_pattern.startswith("**/"):
        candidates.add(normalized_pattern[3:])
    return any(fnmatch.fnmatch(relative_path, candidate) for candidate in candidates)


def _is_forbidden_env_path(relative_path: str, rules: GitIgnoreRuleSet) -> bool:
    ignored = any(
        _matches_gitignore_pattern(relative_path, pattern)
        for pattern in rules.ignored_env_patterns
    )
    if not ignored:
        return False
    allowed = any(
        _matches_gitignore_pattern(relative_path, pattern)
        for pattern in rules.allowed_env_patterns
    )
    return not allowed


def _check_gitignore_env_policy(repo_root: Path, issues: List[str]) -> GitIgnoreRuleSet:
    gitignore_path = repo_root / ".gitignore"
    rules = _parse_gitignore(repo_root)
    if not gitignore_path.exists():
        _add_issue(issues, ".gitignore must exist for the governed env ignore policy")
        return rules
    gitignore_text = gitignore_path.read_text()
    missing = [rule for rule in REQUIRED_GITIGNORE_ENV_RULES if rule not in gitignore_text]
    for rule in missing:
        _add_issue(issues, f".gitignore must declare the governed env ignore rule: {rule}")
    if not rules.ignored_env_patterns:
        _add_issue(issues, ".gitignore must define ignored env patterns for repo security")
    if not rules.allowed_env_patterns:
        _add_issue(issues, ".gitignore must define the tracked env example exception")
    return rules


def _check_forbidden_tracked_files(
    repo_root: Path,
    issues: List[str],
    *,
    gitignore_rules: GitIgnoreRuleSet,
) -> None:
    for path in _tracked_files(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        lower_name = path.name.lower()
        if _is_forbidden_env_path(relative, gitignore_rules):
            _add_issue(
                issues,
                f"tracked env file violates the governed gitignore policy: {relative}",
            )
            continue
        if (
            lower_name in FORBIDDEN_TRACKED_EXACT_NAMES
            or lower_name.endswith(FORBIDDEN_TRACKED_SUFFIXES)
        ):
            _add_issue(issues, f"tracked file is forbidden for repo security: {relative}")


def _check_env_example(repo_root: Path, issues: List[str]) -> None:
    env_path = repo_root / ".env.example"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if any(marker in key for marker in SENSITIVE_ENV_KEYS):
            normalized = value.lower()
            if not any(marker in normalized for marker in PLACEHOLDER_MARKERS):
                _add_issue(
                    issues,
                    ".env.example sensitive value must stay synthetic and placeholder-shaped: "
                    f"{key}",
                )


def _check_client_boundaries(repo_root: Path, issues: List[str]) -> None:
    for path in _iter_paths(repo_root, CLIENT_PATTERNS):
        text = path.read_text()
        for marker in CLIENT_LEAK_MARKERS:
            if marker in text:
                _add_issue(
                    issues,
                    "client-facing app surface must not mention server-only secret marker "
                    f"'{marker}': {path.relative_to(repo_root)}",
                )


def _check_manifest_html_paths(repo_root: Path, issues: List[str]) -> None:
    manifest_path = repo_root / "apps" / "extension" / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text())
    options_page = manifest.get("options_page", "")
    side_panel = _manifest_mapping(manifest, issues, "side_panel").get("default_path", "")
    if options_page != "./options.html":
        _add_issue(
            issues,
            "extension options page path must stay on the governed HTML source surface",
        )
    if side_panel != "./popup.html":
        _add_issue(
            issues,
            "extension side-panel path must stay on the governed HTML source surface",
        )


def _iter_manifest_icon_entries(icon_value: Any) -> Iterable[tuple[str, str]]:
    if isinstance(icon_value, str):
        yield ("icon", icon_value)
        return
    if not isinstance(icon_value, dict):
        return
    for size, icon_path in sorted(icon_value.items()):
        if isinstance(icon_path, str):
            yield (str(size), icon_path)


def _check_manifest_icon_paths(repo_root: Path, issues: List[str]) -> None:
    manifest_path = repo_root / "apps" / "extension" / "manifest.json"
    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text())
    extension_root = manifest_path.parent
    governed_icon_surfaces = (
        ("icons", manifest.get("icons")),
        ("action.default_icon", _manifest_mapping(manifest, issues, "action").get("default_icon")),
    )

    for surface_name, icon_value in governed_icon_surfaces:
        for icon_size, relative_icon_path in _iter_manifest_icon_entries(icon_value):
            icon_path = Path(relative_icon_path)
            path_parts = icon_path.parts
            if (
                not relative_icon_path
                or icon_path.is_absolute()
                or ".." in path_parts
                or path_parts[:1] == ("assets",)
            ):
                _add_issue(
                    issues,
                    "extension manifest icon path must stay on the governed extension asset "
                    f"surface for {surface_name}.{icon_size}: {relative_icon_path}",
                )
                continue

            resolved_icon_path = extension_root / icon_path
            if not resolved_icon_path.is_file():
                _add_issue(
                    issues,
                    f"extension manifest icon asset must exist for {surface_name}.{icon_size}: "
                    f"{relative_icon_path}",
                )


def check_security(repo_root: Path) -> List[str]:
    issues: List[str] = []
    gitignore_rules = _check_gitignore_env_policy(repo_root, issues)
    _check_forbidden_tracked_files(repo_root, issues, gitignore_rules=gitignore_rules)
    _check_env_example(repo_root, issues)
    _check_client_boundaries(repo_root, issues)
    _check_manifest_html_paths(repo_root, issues)
    _check_manifest_icon_paths(repo_root, issues)
    return issues
