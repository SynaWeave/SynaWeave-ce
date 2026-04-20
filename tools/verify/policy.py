"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  centralize governed repository policy constants for shared verifier use

- Later Extension Points:
    --> extend policy maps only when new durable repo-control surfaces or header rules are activated

- Role:
    --> holds shared constants for docs governance workflow and header verification
    --> keeps verifier rule inputs aligned across independent verifier modules

- Exports:
    --> governed policy constant sets and pattern maps

- Consumed By:
    --> repository verifier modules that share policy-driven checks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import re
from pathlib import Path

REQUIRED_GOVERNANCE_FILES = {
    "AGENTS.md",
    "GOVERNANCE.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CLA.md",
    "NOTICE",
    "TRADEMARKS.md",
    "LICENSE",
    ".env.example",
    ".betterleaks.toml",
    ".github/CODEOWNERS",
}

GOVERNED_REQUIRED_STATUS_CHECKS = (
    "repo-verify / repo-verify",
    "dependency-installability / dependency-installability",
    "dependency-review / dependency-review",
    "codeql / codeql-javascript-typescript",
    "codeql / codeql-python",
)

GOVERNED_GITHUB_POSTURE_PHRASES = (
    "Expected default-branch ruleset posture:",
    "GitHub rulesets are the first enforcement home",
    "CODEOWNERS file assigns platform-admin and core-maintainer owners for protected-path changes",
)

ROOT_DOC_FILES = (
    "architecture.md",
    "auth.md",
    "apps.md",
    "code-style.md",
    "packages.md",
    "python.md",
    "infra.md",
    "testing.md",
    "operations.md",
    "design-system.md",
    "legend.md",
    "adrs.md",
    "planning.md",
    "templates.md",
)

REQUIRED_TEMPLATE_FILES = (
    Path("code-tldr.md"),
    Path("planning") / "sprint-overview.md",
    Path("planning") / "deliverable.md",
    Path("adrs") / "sprint-adr.md",
    Path("specs") / "contract-spec.md",
    Path("tests") / "verification-plan.md",
)

HEADER_MARKERS = (
    "TL;DR  -->",
    "- Later Extension Points:",
    "- Role:",
    "- Exports:",
    "- Consumed By:",
)

HEADER_PATTERNS = {
    "python": (
        "tools/**/*.py",
        "testing/**/*.py",
        "python/**/*.py",
    ),
    "typescript": (
        "packages/**/*.ts",
        "tools/**/*.ts",
    ),
    "javascript": (
        "apps/**/*.js",
    ),
    "yaml": (
        ".github/workflows/*.yml",
        ".github/workflows/*.yaml",
    ),
    "toml": (
        "pyproject.toml",
    ),
    "shell": (
        "tools/hooks/*",
    ),
    "dotenv": (
        ".env.example",
    ),
    "css": (
        "apps/**/*.css",
    ),
}

CODE_HEADER_TEMPLATE_FILE = REQUIRED_TEMPLATE_FILES[0]

PROTECTED_WORKFLOW_PATHS = (
    "AGENTS.md",
    "GOVERNANCE.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CLA.md",
    "NOTICE",
    "TRADEMARKS.md",
    ".env.example",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/workflows/**",
    "tools/verify/**",
    "tools/hooks/**",
    "docs/planning/**",
    "docs/adrs/**",
    "docs/templates/**",
    "docs/*.md",
)

CODEOWNERS_REQUIRED_LINES = (
    "* @SynaWeave/core-maintainers",
    ".github/ @SynaWeave/core-maintainers",
    "apps/ @SynaWeave/core-maintainers",
    "docs/ @SynaWeave/core-maintainers",
    "tools/ @SynaWeave/core-maintainers",
    "packages/ @SynaWeave/core-maintainers",
    "python/ @SynaWeave/core-maintainers",
    "infra/ @SynaWeave/core-maintainers",
    "infra/docker/ @SynaWeave/platform-admins @SynaWeave/core-maintainers",
    "infra/github/ @SynaWeave/platform-admins @SynaWeave/core-maintainers",
    "infra/policies/ @SynaWeave/platform-admins @SynaWeave/core-maintainers",
    "testing/ @SynaWeave/core-maintainers",
    "AGENTS.md @SynaWeave/platform-admins",
    "GOVERNANCE.md @SynaWeave/platform-admins",
    "CONTRIBUTING.md @SynaWeave/platform-admins",
    "CODE_OF_CONDUCT.md @SynaWeave/platform-admins",
    "SECURITY.md @SynaWeave/platform-admins",
    "CLA.md @SynaWeave/platform-admins",
    "NOTICE @SynaWeave/platform-admins",
    "TRADEMARKS.md @SynaWeave/platform-admins",
    ".env.example @SynaWeave/platform-admins",
    ".github/CODEOWNERS @SynaWeave/platform-admins",
    ".github/pull_request_template.md @SynaWeave/platform-admins",
    ".github/workflows/ @SynaWeave/platform-admins",
    "tools/verify/ @SynaWeave/platform-admins",
    "tools/hooks/ @SynaWeave/platform-admins",
    "docs/planning/ @SynaWeave/platform-admins @SynaWeave/core-maintainers",
    "docs/adrs/ @SynaWeave/platform-admins @SynaWeave/core-maintainers",
    "docs/templates/ @SynaWeave/platform-admins @SynaWeave/core-maintainers",
    "docs/*.md @SynaWeave/core-maintainers",
)

PR_TEMPLATE_REQUIRED_FIELDS = (
    "## TL;DR",
    "## Summary",
    "### Why this change",
    "Business logic alignment note:",
    "### Files and boundaries",
    "### Protected-path and hotspot notes",
    "## Verification",
    "### Checklist",
    "Code remains readable without hidden workflow or policy drift",
    "Proper documentation was updated for any durable behavior or structure change",
    "### Docs and ADR delta",
    "### Scope",
    "### Tests",
    "Test coverage remains appropriate for the changed logic path",
    "## CLA",
    "I agree to the CLA in CLA.md",
    "Admin bypass used or requested",
)

ALLOWED_CHANGE_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
    "deploy",
)

ALLOWED_CHANGE_SCOPES = (
    "adr",
    "docs",
    "infra",
    "apps",
    "packages",
    "python",
    "testing",
    "hooks",
    "tools",
    "governance",
    "security",
)

BANNED_TYPE_SCOPE_PAIRS = {
    ("docs", "docs"): (
        "docs(docs) is too broad; use a narrower docs scope such as docs(adr) or docs(governance)"
    ),
    ("test", "testing"): (
        "test(testing) is too broad; use a narrower test scope such as test(hooks) or test(tools)"
    ),
}

MIN_SUBJECT_WORDS = 16
MIN_PR_TITLE_WORDS = 8

SHARED_BANNED_WORDS = (
    "accepted",
    "again",
    "actually",
    "basically",
    "clear",
    "clearly",
    "hopefully",
    "just",
    "maybe",
    "obviously",
    "perhaps",
    "please",
    "really",
    "simply",
    "thanks",
    "today",
    "very",
    "now",
    "safely",
)

SHARED_BANNED_PHRASES = (
    "aim to",
    "attempt to",
    "i think",
    "policy checks",
    "please note",
    "seek to",
    "thank you",
    "try to",
    "we think",
    "review flow",
)


SHARED_BANNED_PREFIXES = (
    "phase-",
)

REQUIRED_PACKAGE_SCRIPTS = {
    "deps:browser": "playwright install chromium",
    "build:extension": "python3 -m tools.extension.build",
    "security:betterleaks:staged": "python3 -m tools.security.betterleaks --mode staged",
    "security:betterleaks:tracked": (
        "python3 -m tools.security.betterleaks --mode tracked --include-built-extension"
    ),
    "test:browser": "bun run test:e2e && bun run test:accessibility",
    "test:e2e": (
        "bun run build:extension && playwright test --config playwright.config.ts "
        "testing/e2e"
    ),
    "test:accessibility": (
        "bun run build:extension && playwright test --config playwright.config.ts "
        "testing/accessibility"
    ),
    "verify:browser": "bun run test:browser",
    "verify": (
        "bun run lint && bun run typecheck && bun run test && bun run verify:browser && "
        "python3 -m tools.verify.main --checks shape,docs,commentary,governance,"
        "headers,security,html_ship,adr,workflows,suppressions,commit"
    ),
    "verify:docs": "python3 -m tools.verify.main --checks docs,adr",
    "verify:adr": "python3 -m tools.verify.main --checks adr",
    "verify:governance": "python3 -m tools.verify.main --checks governance",
    "verify:html": "python3 -m tools.verify.main --checks commentary,html_ship",
    "verify:protected": (
        "python3 -m tools.verify.main --checks "
        "shape,docs,commentary,governance,headers,security,workflows,suppressions"
    ),
    "verify:protected-pr": (
        "python3 -m tools.verify.main --checks "
        "shape,docs,commentary,governance,headers,security,adr,workflows,suppressions"
    ),
    "lint:ts": (
        "biome check package.json tsconfig.json playwright.config.ts apps packages "
        "tools/ts testing/e2e testing/ui testing/accessibility .github"
    ),
    "typecheck:ts": "tsc --noEmit --project tsconfig.json",
}

REQUIRED_DEV_DEPENDENCIES = {
    "@axe-core/playwright": "4.11.2",
    "@playwright/test": "1.59.1",
    "@types/node": "22.13.4",
    "@biomejs/biome": "1.9.4",
    "typescript": "5.6.3",
}

COMMENT_HEAVY_PATTERNS = {
    "python": HEADER_PATTERNS["python"],
    "typescript": HEADER_PATTERNS["typescript"],
    "javascript": HEADER_PATTERNS["javascript"],
    "yaml": HEADER_PATTERNS["yaml"],
    "toml": HEADER_PATTERNS["toml"],
    "shell": HEADER_PATTERNS["shell"],
    "dotenv": HEADER_PATTERNS["dotenv"],
    "css": HEADER_PATTERNS["css"],
    "html": (
        "apps/**/*.html",
    ),
}


def build_shared_phrase_pattern(parts: tuple[str, ...]) -> re.Pattern[str]:
    escaped_parts = [re.escape(part).replace(r"\ ", r"\s+") for part in parts]
    return re.compile(r"\b(?:" + "|".join(escaped_parts) + r")\b", re.IGNORECASE)


def build_shared_prefix_pattern(prefixes: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile(
        r"\b(?:"
        + "|".join(re.escape(prefix) + r"[a-z0-9-]*" for prefix in prefixes)
        + r")\b",
        re.IGNORECASE,
    )
