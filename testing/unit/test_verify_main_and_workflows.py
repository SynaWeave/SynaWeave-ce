"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify main verifier wiring and hosted workflow expectation checks with unit coverage

- Later Extension Points:
    --> add more workflow fixtures only when new hosted controls join the repository baseline

- Role:
    --> tests verifier check selection and workflow expectation failure paths
    --> covers protected-path and hosted workflow drift inside isolated temporary repos

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

from tools.verify.main import _parse_check_names, run_verification
from tools.verify.policy import PROTECTED_WORKFLOW_PATHS
from tools.verify.workflows import REPO_VERIFY_COMMIT_BASE, REPO_VERIFY_COMMIT_HEAD, check_workflows

REPO_ROOT = Path(__file__).resolve().parents[2]

FAST_SECRET_SCAN_COMMAND = (
    'docker run --rm -v "$PWD:/repo" -w /repo ghcr.io/betterleaks/betterleaks:latest '
    'dir --config /repo/.betterleaks.toml --no-banner --no-color --redact=100 '
    '--max-archive-depth 2 '
    '--exit-code 1 $(git ls-files) build/extension'
)

TRUFFLEHOG_GIT_COMMAND = (
    'docker run --rm -v "$PWD:/repo" trufflesecurity/trufflehog:latest git file:///repo '
    '--results=verified,unknown --fail'
)

TRUFFLEHOG_ARTIFACT_COMMAND = (
    'docker run --rm -v "$PWD:/repo" trufflesecurity/trufflehog:latest filesystem '
    '/repo/build/extension --results=verified,unknown --fail'
)

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
DEPENDENCY_INSTALL_ARCHIVE_COMMAND = (
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


def make_workflow_tree(repo_root: Path) -> None:
    workflows_dir = repo_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    protected_paths = "\n".join(f'      - "{path}"' for path in PROTECTED_WORKFLOW_PATHS)
    workflow_bodies = {
        "dependency-installability.yml": (
            "name: dependency-installability\n"
            "on:\n"
            "  push:\n"
            "    branches:\n"
            "      - \"**\"\n"
            "  pull_request:\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  dependency-installability:\n"
            "    name: dependency-installability\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: actions/setup-python@v5\n"
            "      - uses: oven-sh/setup-bun@v2\n"
            f"      - run: {DEPENDENCY_INSTALL_MKDIR_COMMAND}\n"
            f"      - run: {DEPENDENCY_INSTALL_ARCHIVE_COMMAND}\n"
            f"      - run: {DEPENDENCY_INSTALL_VENV_COMMAND}\n"
            "      - run: |\n"
            f"          {DEPENDENCY_INSTALL_PIP_INSTALL_COMMAND}\n"
            "      - run: |\n"
            f"          {DEPENDENCY_INSTALL_PIP_FREEZE_COMMAND}\n"
            "      - run: bun install --frozen-lockfile\n"
            f"      - run: {DEPENDENCY_INSTALL_CLEAN_CHECK_COMMAND}\n"
        ),
        "repo-verify.yml": (
            "name: repo-verify\n"
            "on:\n"
            "  push:\n"
            "    branches:\n"
            "      - \"**\"\n"
            "  pull_request:\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  verify:\n"
            "    name: repo-verify\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "        with:\n"
            "          fetch-depth: 0\n"
            "      - run: python3 -m pip install -r requirements-dev.txt\n"
            "      - run: bun install --frozen-lockfile\n"
            "      - run: bun run verify\n"
            "        env:\n"
            f"          VERIFY_COMMIT_BASE: {REPO_VERIFY_COMMIT_BASE}\n"
            f"          VERIFY_COMMIT_HEAD: {REPO_VERIFY_COMMIT_HEAD}\n"
        ),
        "docs-guard.yml": (
            "on:\n"
            "  pull_request:\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  docs:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - run: python3 -m pip install -r requirements-dev.txt\n"
            "      - run: bun install --frozen-lockfile\n"
            "      - run: bun run verify:docs\n"
        ),
        "protected-paths.yml": (
            "on:\n"
            "  pull_request:\n"
            "    paths:\n"
            f"{protected_paths}\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  protected:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - run: python3 -m pip install -r requirements-dev.txt\n"
            "      - run: bun install --frozen-lockfile\n"
            "      - run: bun run verify:protected-pr\n"
        ),
        "governance-guard.yml": (
            "on:\n"
            "  pull_request:\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  governance:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - run: python3 -m pip install -r requirements-dev.txt\n"
            "      - run: bun install --frozen-lockfile\n"
            "      - run: bun run verify:governance\n"
        ),
        "pr-quality.yml": (
            "on:\n"
            "  pull_request:\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  pr-quality:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - run: python3 -m tools.verify.pr_quality\n"
        ),
        "cla-check.yml": (
            "on:\n"
            "  pull_request:\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  cla-check:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - run: python3 -c \"print('CLA')\"\n"
        ),
        "codeql.yml": (
            "name: codeql\n"
            "on:\n"
            "  push:\n"
            "    branches:\n"
            "      - main\n"
            "  pull_request:\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  analyze:\n"
            "    name: codeql-${{ matrix.language }}\n"
            "    runs-on: ubuntu-latest\n"
            "    strategy:\n"
            "      fail-fast: false\n"
            "      matrix:\n"
            "        include:\n"
            "          - language: javascript-typescript\n"
            "            build-mode: none\n"
            "          - language: python\n"
            "            build-mode: none\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: github/codeql-action/init@v3\n"
            "        with:\n"
            "          languages: \"${{ matrix.language }}\"\n"
            "          build-mode: \"${{ matrix.build-mode }}\"\n"
            "      - uses: github/codeql-action/analyze@v3\n"
        ),
        "dependency-review.yml": (
            "name: dependency-review\n"
            "on:\n"
            "  pull_request:\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  dependency-review:\n"
            "    name: dependency-review\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - id: dependency-graph\n"
            "        run: python3 -c \"print('probe')\"\n"
            "      - if: steps.dependency-graph.outputs.enabled == 'true'\n"
            "        uses: actions/dependency-review-action@v4\n"
            "      - if: steps.dependency-graph.outputs.enabled != 'true'\n"
            "        run: echo \"Dependency graph is not enabled for this repository yet; "
            "skipping dependency review.\"\n"
        ),
    }
    for name, body in workflow_bodies.items():
        (workflows_dir / name).write_text(body)
    for name in ("secret-scan-fast.yml", "secret-scan-deep.yml"):
        source = REPO_ROOT / ".github" / "workflows" / name
        (workflows_dir / name).write_text(source.read_text())


class TestVerifyMainAndWorkflows(unittest.TestCase):
    def test_parse_check_names_rejects_unknown_check(self):
        with self.assertRaises(ValueError):
            _parse_check_names("shape,unknown")

    def test_run_verification_collects_checker_output(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            issues = run_verification(repo_root, ["shape"])
            self.assertTrue(any(name == "shape" for name, _ in issues))

    def test_verify_main_runs_as_python_module(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "tools.verify.main",
                    "--checks",
                    "shape",
                    "--root",
                    str(repo_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing required top-level directory", result.stdout)

    def test_workflows_require_expected_commands(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)

            issues = check_workflows(repo_root)
            self.assertEqual(issues, [])

    def test_workflows_require_dependency_installability_pin_check(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "dependency-installability.yml").write_text(
                "name: dependency-installability\n"
                "on:\n"
                "  push:\n"
                "    branches:\n"
                "      - \"**\"\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  dependency-installability:\n"
                "    name: dependency-installability\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - uses: actions/setup-python@v5\n"
                "      - uses: oven-sh/setup-bun@v2\n"
                f"      - run: {DEPENDENCY_INSTALL_MKDIR_COMMAND}\n"
                f"      - run: {DEPENDENCY_INSTALL_ARCHIVE_COMMAND}\n"
                f"      - run: {DEPENDENCY_INSTALL_VENV_COMMAND}\n"
                f"      - run: {DEPENDENCY_INSTALL_PIP_INSTALL_COMMAND}\n"
                "      - run: bun install --frozen-lockfile\n"
                f"      - run: {DEPENDENCY_INSTALL_CLEAN_CHECK_COMMAND}\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("pip freeze" in issue for issue in issues))

    def test_workflows_reject_missing_protected_path_trigger(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "protected-paths.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "    paths:\n"
                "      - \"AGENTS.md\"\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  protected:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - run: python3 -m pip install -r requirements-dev.txt\n"
                "      - run: bun install --frozen-lockfile\n"
                "      - run: bun run verify:protected-pr\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("protected-path trigger" in issue for issue in issues))

    def test_workflows_reject_run_blocks_that_only_echo_required_commands(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "repo-verify.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  verify:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - run: echo \"python3 -m pip install -r requirements-dev.txt\"\n"
                "      - run: echo \"bun install --frozen-lockfile\"\n"
                "      - run: echo \"bun run verify\"\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("missing required command" in issue for issue in issues))

    def test_workflows_reject_branch_specific_codeql_configuration(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "codeql.yml").write_text(
                "on:\n"
                "  push:\n"
                "    branches:\n"
                "      - main\n"
                "      - s001/d1-foundation\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  analyze:\n"
                "    runs-on: ubuntu-latest\n"
                "    strategy:\n"
                "      matrix:\n"
                "        include:\n"
                "          - language: javascript-typescript\n"
                "            build-mode: none\n"
                "          - language: python\n"
                "            build-mode: none\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - uses: github/codeql-action/init@v3\n"
                "        with:\n"
                "          languages: \"${{ matrix.language }}\"\n"
                "          build-mode: \"${{ matrix.build-mode }}\"\n"
                "      - uses: github/codeql-action/analyze@v3\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("CodeQL push branches" in issue for issue in issues))

    def test_workflows_require_repo_verify_commit_range_inputs(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "repo-verify.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  verify:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "        with:\n"
                "          fetch-depth: 0\n"
                "      - run: python3 -m pip install -r requirements-dev.txt\n"
                "      - run: bun install --frozen-lockfile\n"
                "      - run: bun run verify\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("commit-range validation" in issue for issue in issues))

    def test_workflows_reject_repo_verify_checkout_ref_override(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "repo-verify.yml").write_text(
                "name: repo-verify\n"
                "on:\n"
                "  push:\n"
                "    branches:\n"
                "      - \"**\"\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  verify:\n"
                "    name: repo-verify\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "        with:\n"
                "          fetch-depth: 0\n"
                f"          ref: {REPO_VERIFY_COMMIT_HEAD}\n"
                "      - run: python3 -m pip install -r requirements-dev.txt\n"
                "      - run: bun install --frozen-lockfile\n"
                "      - run: bun run verify\n"
                "        env:\n"
                f"          VERIFY_COMMIT_BASE: {REPO_VERIFY_COMMIT_BASE}\n"
                f"          VERIFY_COMMIT_HEAD: {REPO_VERIFY_COMMIT_HEAD}\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("synthetic merge result" in issue for issue in issues))

    def test_workflows_reject_hosted_check_name_drift(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "codeql.yml").write_text(
                "name: codeql\n"
                "on:\n"
                "  push:\n"
                "    branches:\n"
                "      - main\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  analyze:\n"
                "    name: Analyze\n"
                "    runs-on: ubuntu-latest\n"
                "    strategy:\n"
                "      matrix:\n"
                "        include:\n"
                "          - language: javascript-typescript\n"
                "            build-mode: none\n"
                "          - language: python\n"
                "            build-mode: none\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - uses: github/codeql-action/init@v3\n"
                "        with:\n"
                "          languages: \"${{ matrix.language }}\"\n"
                "          build-mode: \"${{ matrix.build-mode }}\"\n"
                "      - uses: github/codeql-action/analyze@v3\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(
                any(
                    "hosted job name 'codeql-${{ matrix.language }}'" in issue
                    for issue in issues
                )
            )

    def test_workflows_reject_codeql_autobuild_usage(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "codeql.yml").write_text(
                "name: codeql\n"
                "on:\n"
                "  push:\n"
                "    branches:\n"
                "      - main\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  analyze:\n"
                "    name: codeql-${{ matrix.language }}\n"
                "    runs-on: ubuntu-latest\n"
                "    strategy:\n"
                "      matrix:\n"
                "        include:\n"
                "          - language: javascript-typescript\n"
                "            build-mode: none\n"
                "          - language: python\n"
                "            build-mode: none\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - uses: github/codeql-action/init@v3\n"
                "        with:\n"
                "          languages: \"${{ matrix.language }}\"\n"
                "          build-mode: \"${{ matrix.build-mode }}\"\n"
                "      - uses: github/codeql-action/autobuild@v3\n"
                "      - uses: github/codeql-action/analyze@v3\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("must not use CodeQL autobuild" in issue for issue in issues))

    def test_workflows_require_codeql_none_build_matrix(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "codeql.yml").write_text(
                "name: codeql\n"
                "on:\n"
                "  push:\n"
                "    branches:\n"
                "      - main\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  analyze:\n"
                "    name: codeql-${{ matrix.language }}\n"
                "    runs-on: ubuntu-latest\n"
                "    strategy:\n"
                "      matrix:\n"
                "        include:\n"
                "          - language: javascript-typescript\n"
                "            build-mode: autobuild\n"
                "          - language: python\n"
                "            build-mode: none\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - uses: github/codeql-action/init@v3\n"
                "        with:\n"
                "          languages: \"${{ matrix.language }}\"\n"
                "          build-mode: \"${{ matrix.build-mode }}\"\n"
                "      - uses: github/codeql-action/analyze@v3\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("build-mode none" in issue for issue in issues))

    def test_workflows_reject_push_trigger_on_docs_guard(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "docs-guard.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "  push:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  docs:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - run: python3 -m pip install -r requirements-dev.txt\n"
                "      - run: bun install --frozen-lockfile\n"
                "      - run: bun run verify:docs\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("off push triggers" in issue for issue in issues))

    def test_workflows_reject_push_trigger_on_protected_paths(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            protected_paths = "\n".join(
                f'      - "{path}"' for path in PROTECTED_WORKFLOW_PATHS
            )
            (repo_root / ".github" / "workflows" / "protected-paths.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "    paths:\n"
                f"{protected_paths}\n"
                "  push:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  protected:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - run: python3 -m pip install -r requirements-dev.txt\n"
                "      - run: bun install --frozen-lockfile\n"
                "      - run: bun run verify:protected-pr\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("protected-paths.yml" in issue for issue in issues))
            self.assertTrue(any("off push triggers" in issue for issue in issues))

    def test_workflows_require_full_history_for_trufflehog(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "secret-scan-deep.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  trufflehog:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - run: python3 -m tools.extension.build --output build/extension\n"
                f"      - run: {TRUFFLEHOG_GIT_COMMAND}\n"
                f"      - run: {TRUFFLEHOG_ARTIFACT_COMMAND}\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("full git history" in issue for issue in issues))

    def test_workflows_require_dependency_review_support_gating(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_workflow_tree(repo_root)
            (repo_root / ".github" / "workflows" / "dependency-review.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  dependency-review:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - id: dependency-graph\n"
                "        run: python3 -c \"print('probe')\"\n"
                "      - uses: actions/dependency-review-action@v4\n"
                "      - run: echo \"Dependency graph is not enabled for this repository yet; "
                "skipping dependency review.\"\n"
            )
            issues = check_workflows(repo_root)
            self.assertTrue(any("gate hosted dependency review" in issue for issue in issues))
            self.assertTrue(
                any("gate dependency-review fallback note" in issue for issue in issues)
            )


if __name__ == "__main__":
    unittest.main()
