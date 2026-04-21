"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify governed GitHub workflows through parsed structure instead of brittle text checks

- Later Extension Points:
    --> add workflow-specific structural assertions only when new hosted controls join the baseline

- Role:
    --> parses required workflow files and validates triggers permissions jobs and bounded commands
    --> blocks protected-path drift and branch-specific residue through semantic workflow inspection

- Exports:
    --> `check_workflows()`

- Consumed By:
    --> `tools.verify.main` during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from tools.verify.policy import PROTECTED_WORKFLOW_PATHS

REQUIRED_WORKFLOW_FILES = {
    "dependency-installability.yml",
    "repo-verify.yml",
    "docs-guard.yml",
    "protected-paths.yml",
    "governance-guard.yml",
    "pr-quality.yml",
    "cla-check.yml",
    "codeql.yml",
    "dependency-review.yml",
    "secret-scan-fast.yml",
    "secret-scan-deep.yml",
}

DEPENDENCY_INSTALL_REPO_DIR = '"$RUNNER_TEMP/dependency-installability/repo"'
DEPENDENCY_INSTALL_VENV_DIR = '"$RUNNER_TEMP/dependency-installability/venv"'
DEPENDENCY_INSTALL_VENV_PYTHON = (
    '"$RUNNER_TEMP/dependency-installability/venv/bin/python"'
)
DEPENDENCY_INSTALL_REQUIREMENTS = (
    '"$RUNNER_TEMP/dependency-installability/repo/requirements-dev.txt"'
)
DEPENDENCY_INSTALL_MKDIR_COMMAND = (
    "perl -MFile::Path=make_path -e 'make_path(@ARGV)' " f"{DEPENDENCY_INSTALL_REPO_DIR}"
)
DEPENDENCY_INSTALL_GIT_ARCHIVE_COMMAND = (
    f"git archive --format=tar HEAD | tar -xf - -C {DEPENDENCY_INSTALL_REPO_DIR}"
)
DEPENDENCY_INSTALL_VENV_COMMAND = f"python3 -m venv {DEPENDENCY_INSTALL_VENV_DIR}"
DEPENDENCY_INSTALL_PIP_INSTALL_COMMAND = (
    f"{DEPENDENCY_INSTALL_VENV_PYTHON} -m pip install -r {DEPENDENCY_INSTALL_REQUIREMENTS}"
)
DEPENDENCY_INSTALL_PIP_FREEZE_COMMAND = (
    f"{DEPENDENCY_INSTALL_VENV_PYTHON} -m pip freeze | perl -ne "
    "'BEGIN { %expected = map { chomp; split /==/, $_, 2 } <>; %seen = (); "
    "$status = 0; } chomp; my ($name, $version) = split /==/, $_, 2; "
    "$seen{$name} = $version if defined $version && exists $expected{$name}; "
    "END { for my $name (sort keys %expected) { if (!exists $seen{$name}) { "
    'print STDERR \"missing expected Python tool $name\\n\"; '
    "$status = 1; next; } if ($seen{$name} ne $expected{$name}) { "
    'print STDERR \"expected $name==$expected{$name} but saw $seen{$name}\\n\"; '
    "$status = 1; } } exit $status; }' "
    f"{DEPENDENCY_INSTALL_REQUIREMENTS}"
)
DEPENDENCY_INSTALL_CLEAN_CHECK_COMMAND = (
    "perl -e 'my @lines = qx/git status --porcelain/; if (@lines) { print STDERR @lines; "
    'exit 1; } print "Repository checkout remained clean.\\n";\''
)

WORKFLOW_RUN_COMMANDS = {
    "dependency-installability.yml": (
        DEPENDENCY_INSTALL_MKDIR_COMMAND,
        DEPENDENCY_INSTALL_GIT_ARCHIVE_COMMAND,
        DEPENDENCY_INSTALL_VENV_COMMAND,
        DEPENDENCY_INSTALL_PIP_INSTALL_COMMAND,
        DEPENDENCY_INSTALL_PIP_FREEZE_COMMAND,
        "bun install --frozen-lockfile",
        DEPENDENCY_INSTALL_CLEAN_CHECK_COMMAND,
    ),
    "repo-verify.yml": (
        "python3 -m pip install -r requirements-dev.txt",
        "bun install --frozen-lockfile",
        "bun run verify",
    ),
    "docs-guard.yml": (
        "python3 -m pip install -r requirements-dev.txt",
        "bun install --frozen-lockfile",
        "bun run verify:docs",
    ),
    "protected-paths.yml": (
        "python3 -m pip install -r requirements-dev.txt",
        "bun install --frozen-lockfile",
        "bun run verify:protected-pr",
    ),
    "governance-guard.yml": (
        "python3 -m pip install -r requirements-dev.txt",
        "bun install --frozen-lockfile",
        "bun run verify:governance",
    ),
    "pr-quality.yml": ("python3 -m tools.verify.pr_quality",),
    "secret-scan-fast.yml": (
        "python3 -m tools.extension.build --output build/extension",
        "docker run --rm -v \"$PWD:/repo\" -w /repo ghcr.io/betterleaks/betterleaks:latest "
        "dir --config /repo/.betterleaks.toml --no-banner --no-color --redact=100 "
        "--max-archive-depth 2 "
        "--exit-code 1 $(git ls-files) build/extension",
    ),
    "secret-scan-deep.yml": (
        "python3 -m tools.extension.build --output build/extension",
        "docker run --rm -v \"$PWD:/repo\" trufflesecurity/trufflehog:latest git file:///repo "
        "--results=verified,unknown --fail",
        "docker run --rm -v \"$PWD:/repo\" trufflesecurity/trufflehog:latest filesystem "
        "/repo/build/extension --results=verified,unknown --fail",
    ),
}

WORKFLOW_USES = {
    "dependency-review.yml": ("actions/dependency-review-action@v4",),
    "dependency-installability.yml": (
        "actions/checkout@v4",
        "actions/setup-python@v5",
        "oven-sh/setup-bun@v2",
    ),
    "repo-verify.yml": ("actions/checkout@v4",),
    "docs-guard.yml": ("actions/checkout@v4",),
    "protected-paths.yml": ("actions/checkout@v4",),
    "governance-guard.yml": ("actions/checkout@v4",),
    "pr-quality.yml": ("actions/checkout@v4",),
    "cla-check.yml": ("actions/checkout@v4",),
    "secret-scan-fast.yml": ("actions/checkout@v4",),
    "secret-scan-deep.yml": ("actions/checkout@v4",),
    "codeql.yml": (
        "actions/checkout@v4",
        "github/codeql-action/init@v3",
        "github/codeql-action/analyze@v3",
    ),
}

EXPECTED_WORKFLOW_NAMES = {
    "dependency-installability.yml": "dependency-installability",
    "repo-verify.yml": "repo-verify",
    "dependency-review.yml": "dependency-review",
    "codeql.yml": "codeql",
}

EXPECTED_JOB_NAMES = {
    "dependency-installability.yml": {
        "dependency-installability": "dependency-installability"
    },
    "repo-verify.yml": {"verify": "repo-verify"},
    "dependency-review.yml": {"dependency-review": "dependency-review"},
    "codeql.yml": {"analyze": "codeql-${{ matrix.language }}"},
}

REPO_VERIFY_COMMIT_BASE = "${{ github.event.pull_request.base.sha || github.event.before }}"
REPO_VERIFY_COMMIT_HEAD = "${{ github.event.pull_request.head.sha || github.sha }}"

ADR_ENFORCING_PR_ONLY_WORKFLOWS = {
    "docs-guard.yml",
    "protected-paths.yml",
}


def _add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def _strip_comment_lines(text: str) -> list[tuple[int, str]]:
    parsed_lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        # Ignore blank rows and pure comments so the parser only sees structural YAML tokens
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        parsed_lines.append((indent, raw_line.strip()))
    return parsed_lines


def _parse_scalar(value: str) -> Any:
    # Keep scalar parsing intentionally narrow
    # Workflow fixtures only need strings and inline lists
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_block_scalar(
    lines: list[tuple[int, str]],
    index: int,
    parent_indent: int,
    *,
    folded: bool,
) -> tuple[str, int]:
    block_lines: list[str] = []
    # Treat deeper indentation as block-scalar content so multiline run scripts stay parseable
    while index < len(lines) and lines[index][0] > parent_indent:
        block_lines.append(lines[index][1])
        index += 1
    joiner = " " if folded else "\n"
    return (joiner.join(block_lines), index)


def _parse_list_item(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[Any, int]:
    _, content = lines[index]
    item_body = content[2:]
    index += 1
    # List items can open nested mappings in workflow steps so parse the first key eagerly
    if not item_body:
        return _parse_block(lines, index, indent + 2)
    if ":" in item_body:
        key, raw_value = item_body.split(":", 1)
        item: dict[str, Any] = {}
        key = key.strip()
        value = raw_value.strip()
        if value in {"|", ">"}:
            block_value, index = _parse_block_scalar(
                lines,
                index,
                indent,
                folded=value == ">",
            )
            item[key] = block_value
        elif value:
            item[key] = _parse_scalar(value)
        elif index < len(lines) and lines[index][0] > indent:
            nested, index = _parse_block(lines, index, lines[index][0])
            item[key] = nested
        else:
            item[key] = {}
        if index < len(lines) and lines[index][0] > indent:
            nested, index = _parse_block(lines, index, lines[index][0])
            if isinstance(nested, dict):
                item.update(nested)
        return (item, index)
    return (_parse_scalar(item_body), index)


def _parse_block(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[Any, int]:
    if index >= len(lines):
        return ({}, index)

    # Switch on list syntax first because workflow steps are list-heavy and indentation-driven
    if lines[index][1].startswith("- "):
        items: list[Any] = []
        while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
            item, index = _parse_list_item(lines, index, indent)
            items.append(item)
        return (items, index)

    mapping: dict[str, Any] = {}
    # Keep mapping parsing strict
    # Malformed workflow fixtures should fail loudly instead of silently drifting
    while index < len(lines) and lines[index][0] == indent and not lines[index][1].startswith("- "):
        _, content = lines[index]
        if ":" not in content:
            raise ValueError(f"unable to parse YAML line: {content}")
        key, raw_value = content.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        index += 1
        if value in {"|", ">"}:
            block_value, index = _parse_block_scalar(
                lines,
                index,
                indent,
                folded=value == ">",
            )
            mapping[key] = block_value
            continue
        if value:
            mapping[key] = _parse_scalar(value)
            continue
        if index < len(lines) and lines[index][0] > indent:
            nested, index = _parse_block(lines, index, lines[index][0])
            mapping[key] = nested
            continue
        mapping[key] = {}
    return (mapping, index)


def _load_workflow(path: Path, issues: List[str]) -> dict[str, Any] | None:
    try:
        # Parse the repo's bounded YAML subset locally so workflow verification stays repo-owned
        parsed_lines = _strip_comment_lines(path.read_text())
        parsed, index = _parse_block(parsed_lines, 0, parsed_lines[0][0])
        if index != len(parsed_lines):
            raise ValueError("unparsed trailing YAML content")
    except (IndexError, ValueError) as exc:
        _add_issue(issues, f"workflow is not valid YAML: {path.name}: {exc}")
        return None

    if not isinstance(parsed, dict):
        _add_issue(issues, f"workflow must parse to a mapping: {path.name}")
        return None
    return parsed


def _coerce_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _coerce_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _job_steps(document: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for job in _coerce_mapping(document.get("jobs")).values():
        for step in _coerce_list(_coerce_mapping(job).get("steps")):
            if isinstance(step, dict):
                steps.append(step)
    return steps


def _step_run_commands(document: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    for step in _job_steps(document):
        run = step.get("run")
        if isinstance(run, str):
            commands.append(run)
    return commands


def _step_uses(document: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    for step in _job_steps(document):
        uses = step.get("uses")
        if isinstance(uses, str):
            actions.append(uses)
    return actions


def _has_top_level_shape(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    if "on" not in document:
        _add_issue(issues, f"workflow missing on trigger: {path.name}")
    if not _coerce_mapping(document.get("jobs")):
        _add_issue(issues, f"workflow missing jobs block: {path.name}")
    if not _coerce_mapping(document.get("permissions")):
        _add_issue(issues, f"workflow missing permissions block: {path.name}")


def _require_run_commands(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    expected_commands = WORKFLOW_RUN_COMMANDS.get(path.name, ())
    runs = _step_run_commands(document)
    for command in expected_commands:
        # Match exact script lines so `echo "bun run verify"` cannot fake a real gate
        if not any(command == line.strip() for run in runs for line in run.splitlines()):
            _add_issue(issues, f"workflow missing required command '{command}': {path.name}")


def _require_uses(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    expected_uses = WORKFLOW_USES.get(path.name, ())
    uses = _step_uses(document)
    for action in expected_uses:
        if action not in uses:
            _add_issue(issues, f"workflow missing required action '{action}': {path.name}")


def _check_protected_paths_filter(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    if path.name != "protected-paths.yml":
        return

    on_block = _coerce_mapping(document.get("on"))
    pull_request = _coerce_mapping(on_block.get("pull_request"))
    paths = {value for value in _coerce_list(pull_request.get("paths")) if isinstance(value, str)}
    for protected_path in PROTECTED_WORKFLOW_PATHS:
        if protected_path not in paths:
            _add_issue(
                issues,
                f"workflow missing protected-path trigger '{protected_path}': {path.name}",
            )


def _check_adr_enforcement_scope(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    on_block = _coerce_mapping(document.get("on"))
    if path.name in ADR_ENFORCING_PR_ONLY_WORKFLOWS and "push" in on_block:
        _add_issue(
            issues,
            "workflow must keep ADR-enforcing checks off push triggers: "
            f"{path.name}",
        )


def _check_codeql_branches(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    if path.name != "codeql.yml":
        return

    on_block = _coerce_mapping(document.get("on"))
    push = _coerce_mapping(on_block.get("push"))
    branches = [value for value in _coerce_list(push.get("branches")) if isinstance(value, str)]
    if branches != ["main"]:
        _add_issue(issues, f"workflow must limit CodeQL push branches to ['main']: {path.name}")

    jobs = _coerce_mapping(document.get("jobs"))
    analyze = _coerce_mapping(jobs.get("analyze"))
    strategy = _coerce_mapping(analyze.get("strategy"))
    matrix = _coerce_mapping(strategy.get("matrix"))
    include = _coerce_list(matrix.get("include"))
    expected_matrix = [
        {"language": "javascript-typescript", "build-mode": "none"},
        {"language": "python", "build-mode": "none"},
    ]
    if include != expected_matrix:
        _add_issue(
            issues,
            "workflow must keep CodeQL language matrix on build-mode none for "
            "javascript-typescript and python: "
            f"{path.name}",
        )

    for step in _job_steps(document):
        uses = step.get("uses")
        if uses == "github/codeql-action/autobuild@v3":
            _add_issue(
                issues,
                "workflow must not use CodeQL autobuild when build-mode is none: "
                f"{path.name}",
            )
            break


def _check_dependency_review(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    if path.name != "dependency-review.yml":
        return

    steps = _job_steps(document)
    runs = _step_run_commands(document)
    detect_step = next((step for step in steps if step.get("id") == "dependency-graph"), None)
    if detect_step is None:
        _add_issue(issues, f"workflow missing dependency-graph support probe: {path.name}")

    review_step = next(
        (step for step in steps if step.get("uses") == "actions/dependency-review-action@v4"),
        None,
    )
    if (
        review_step is not None
        and review_step.get("if") != "steps.dependency-graph.outputs.enabled == 'true'"
    ):
        _add_issue(
            issues,
            "workflow must gate hosted dependency review on dependency-graph support: "
            f"{path.name}",
        )

    fallback_step = next(
        (
            step
            for step in steps
            if isinstance(step.get("run"), str)
            and "skipping dependency review" in step["run"].lower()
        ),
        None,
    )
    if (
        fallback_step is not None
        and fallback_step.get("if") != "steps.dependency-graph.outputs.enabled != 'true'"
    ):
        _add_issue(
            issues,
            "workflow must gate dependency-review fallback note on missing dependency-graph "
            f"support: {path.name}",
        )

    # Keep the fallback note explicit
    # Reviewers should see when hosted dependency review is unavailable
    if not any("skipping dependency review" in run.lower() for run in runs):
        _add_issue(issues, f"workflow missing bounded dependency-review fallback note: {path.name}")


def _check_secret_scan_depth(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    if path.name != "secret-scan-deep.yml":
        return

    for step in _job_steps(document):
        if step.get("uses") != "actions/checkout@v4":
            continue
        with_block = _coerce_mapping(step.get("with"))
        if with_block.get("fetch-depth") != "0":
            _add_issue(issues, "workflow must fetch full git history for TruffleHog deep scan")
        return
    _add_issue(issues, "workflow missing checkout step for TruffleHog deep scan")


def _check_repo_verify_commit_range(
    document: dict[str, Any],
    path: Path,
    issues: List[str],
) -> None:
    if path.name != "repo-verify.yml":
        return

    checkout_seen = False
    for step in _job_steps(document):
        if step.get("uses") == "actions/checkout@v4":
            checkout_seen = True
            with_block = _coerce_mapping(step.get("with"))
            if with_block.get("fetch-depth") != "0":
                _add_issue(
                    issues,
                    "workflow must fetch full history for repo commit-range validation",
                )
            if "ref" in with_block:
                _add_issue(
                    issues,
                    "workflow must keep the default checkout ref so pull_request verification "
                    "runs on the synthetic merge result",
                )
        if step.get("run") == "bun run verify":
            env_block = _coerce_mapping(step.get("env"))
            if env_block.get("VERIFY_COMMIT_BASE") != REPO_VERIFY_COMMIT_BASE:
                _add_issue(
                    issues,
                    "workflow must provide VERIFY_COMMIT_BASE for commit-range validation",
                )
            if env_block.get("VERIFY_COMMIT_HEAD") != REPO_VERIFY_COMMIT_HEAD:
                _add_issue(
                    issues,
                    "workflow must provide VERIFY_COMMIT_HEAD for authored commit validation",
                )
    if not checkout_seen:
        _add_issue(issues, "workflow missing checkout step for repo verification")


def _check_hosted_check_names(document: dict[str, Any], path: Path, issues: List[str]) -> None:
    expected_workflow_name = EXPECTED_WORKFLOW_NAMES.get(path.name)
    if expected_workflow_name is not None and document.get("name") != expected_workflow_name:
        _add_issue(
            issues,
            f"workflow must keep hosted workflow name '{expected_workflow_name}': {path.name}",
        )

    expected_job_names = EXPECTED_JOB_NAMES.get(path.name, {})
    jobs = _coerce_mapping(document.get("jobs"))
    for job_id, expected_job_name in expected_job_names.items():
        job = _coerce_mapping(jobs.get(job_id))
        if job.get("name") != expected_job_name:
            _add_issue(
                issues,
                "workflow must keep hosted job name "
                f"'{expected_job_name}' for '{job_id}': {path.name}",
            )


def check_workflows(repo_root: Path) -> List[str]:
    issues: List[str] = []
    workflows_dir = repo_root / ".github" / "workflows"

    if not workflows_dir.exists():
        _add_issue(issues, ".github/workflows directory must exist")
        return issues

    for name in sorted(REQUIRED_WORKFLOW_FILES):
        path = workflows_dir / name
        if not path.exists():
            _add_issue(issues, f"missing required workflow: {name}")
            continue

        document = _load_workflow(path, issues)
        if document is None:
            continue

        _has_top_level_shape(document, path, issues)
        _require_run_commands(document, path, issues)
        _require_uses(document, path, issues)
        _check_protected_paths_filter(document, path, issues)
        _check_adr_enforcement_scope(document, path, issues)
        _check_codeql_branches(document, path, issues)
        _check_dependency_review(document, path, issues)
        _check_secret_scan_depth(document, path, issues)
        _check_repo_verify_commit_range(document, path, issues)
        _check_hosted_check_names(document, path, issues)

    return issues
