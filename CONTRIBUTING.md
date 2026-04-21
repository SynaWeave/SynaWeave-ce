# Contributing to SynaWave

## Quick start

1. Read repository rules in `AGENTS.md`, workflow expectations in `docs/workflow.md`, onboarding context in `docs/onboarding.md`, and planning context in `docs/planning/MASTER.md`.
2. Confirm your change scope in the relevant planning file.
3. Check `docs/templates/` before creating any recurring planning, ADR, spec, or verification doc.
4. Install the local git hooks for your clone:

```bash
bun run hooks:install
```

This step is manual. The repository does not auto-install hooks for contributors or AI-agent operators.

After the one-time `bun run hooks:install` wrapper install, the local `.git/hooks/*` entries are thin wrappers that delegate to the current repo-owned files under `tools/hooks/`, so content updates to existing repo hook files are picked up automatically without reinstalling copied hook bodies. Re-run `bun run hooks:install` when repo hook filenames are added, removed, or renamed, or when local wrappers are missing or damaged, so the local wrapper set stays aligned. Hook-triggered Python sync prefers the repo-owned `.venv` when present and otherwise falls back to `python3 -m pip` automatically. Run `bun run sync` only when a hook reports a real sync failure and you need to rerun it directly.

5. Make targeted edits and keep architecture changes ADR-backed.
6. Run local verification:

```bash
python3 -m tools.verify.main
```

Substantial work should map to an explicit sprint, deliverable, and task target before implementation begins.
If your change updates a recurring document shape, update the owning template instead of copying structure into a new one-off format.

## Commit format (required)

This repository uses Conventional Commits with scope and a minimum 16-word commit subject.

Pattern:

```
<type>(<scope>): <description of at least 16 words>
```

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `deploy`.

Allowed scopes: `adr`, `docs`, `infra`, `apps`, `packages`, `python`, `testing`, `hooks`, `tools`, `governance`, `security`.

Umbrella type-scope pairs are rejected when they collapse the change into the same broad bucket twice.
Use a narrower owned scope instead, so `docs(docs)` and `test(testing)` fail while `docs(adr)`, `docs(governance)`, `test(hooks)`, and `test(tools)` pass.

Examples:

- `docs(adr): align the sprint decision record guidance with governed platform reset evidence and reviewable verification expectations for maintainers`
- `docs(governance): tighten contributor and maintainer rules around protected paths, ownership checks, and verification evidence across review lanes`
- `test(hooks): cover commit-message hook validation through the shared verifier path so repo controls reject broad history scopes early`
- `fix(tools): include commit message validation in the default verifier and improve workflow contract failures across protected control surfaces`

The commit subject must be **at least 16 words** after the colon.
Do not repeat the conventional commit type or scope as standalone words in the subject text.
Hyphenated forms such as `pre-commit` and `pre-push` count as one word.
Do not game the minimum. Prefer subjects that clearly exceed it with concrete, specific rationale instead of the easiest possible pass.

Prefer plain English in commit subjects and ADR prose.
Avoid raw variable names, function names, workflow labels, or code-only shorthand unless a folder path or external standard name is required for precision.
Remove banned filler words, phrases, and prefixes because they dilute shared theory.
The shared ban list is enforced consistently for commit subjects, PR title subjects, and ADR prose.
The shared ban list includes filler wording such as `again`, `clearly`, `now`, `today`, `review flow`, `phase-...`, and `safely`.
Keep same-session commits materially unique so history does not repeat the same rationale in different wrappers.
Use `docs/legend.md` as the only shared abbreviation registry for reused short forms.

## Pull request rules

- Keep PRs scoped to a single objective.
- Use a conventional commit title with scope and at least 8 words after the colon.
- The same umbrella-scope rule applies to PR titles, so `docs(docs)` and `test(testing)` are rejected there too.
- Do not repeat the conventional commit type or scope as standalone words in the PR title subject.
- Name the exact sprint, deliverable, and task target for substantial work.
- Include explicit links to:
  - planning file references
  - ADR references
  - verification output
- Explain any contract or boundary changes and affected consumers.
- Mention what changed in `docs/operations.md` when runtime reality changes.
- Acknowledge protected-path edits explicitly when they occur.
- State whether admin bypass was used or requested when GitHub rulesets required it.

## Local validation expectations

Before opening PR:

- run `bun run hooks:install` after cloning; after that one-time wrapper install, content updates to existing repo hook files apply automatically, and you only need to rerun it when repo hook filenames are added, removed, or renamed, or when local `.git/hooks` wrappers are missing or damaged
- expect local hooks to stay manual until an owner doc says otherwise
- run `bun run sync` only when hooks report a real sync failure or when you want to rerun the sync command directly
- expect `commit-msg` to enforce the commit subject contract before commits land
- expect `post-checkout`, `post-merge`, and `post-rewrite` to auto-run environment sync when `package.json`, `bun.lock`, or `requirements-dev.txt` change; they prefer the repo-owned `.venv/bin/python3` and otherwise fall back to the system `python3 -m pip` command automatically
- expect `pre-commit` to warn on stale local environment state before staged Betterleaks scanning plus `bun run verify:protected`
- expect `pre-push` to run tracked-file Betterleaks first, then retry hook-safe environment sync, then run `bun run verify:push`, and to fail if local tooling still cannot be synced safely
- treat the hook set as local churn reduction: it catches commit, secret, and repo-control issues before PR review
- run `python3 -m tools.verify.main`
- run `bun run verify` when code, hooks, workflows, or repo controls changed
- expect ADR format enforcement in PR-oriented docs and protected-path checks, not local commit or push hooks
- run the required root lint, typecheck, and test commands for changed languages once they exist
- ensure all affected root docs remain aligned
- include screenshot or logs for evidence when adding workflows/verification files

## Code and doc hygiene

- start covered comment-capable files with the governed TL;DR block and keep local comments one line per intent
- fix warnings and type issues at the source instead of adding suppressions or ignore directives
- do not commit `noqa`, `type: ignore`, `@ts-ignore`, `eslint-disable`, `biome-ignore`, `skipLibCheck`, or similar suppression escapes
- keep local comments brief note-taking style: what this group does, why this strategy stays, no filler prose
- remove commented-out code instead of leaving dead experiments in place as pseudo-documentation
- keep HTML comments source-only and non-sensitive because shipped HTML comments are stripped at build time
- install local hooks before relying on commit, push, and Betterleaks feedback in this clone
- keep naming consistent with `docs/planning/MASTER.md` and shared short forms consistent with `docs/legend.md`
- use short root aliases where they improve local command speed: `bun run api`, `bun run web`, `bun run ext`, `bun run check`, and `bun run hooks`
- avoid changing existing conventions without an ADR-backed reason
- update the owner doc or owning template instead of duplicating the same rule in multiple docs

## Security expectations

- never commit `.env` or secrets
- classify new config in `docs/infra.md`
- route schema and dependency changes through required checks in PR review

## Local verification workflow

Choose the narrowest command that still proves your change.

### Fast local commands
- `python3 -m tools.verify.main`
- `bun run check:py:fast`
- `bun run check:browser`
- `bun run check:fast`

### Browser triage helpers
- `bun run triage:ports`
- `bun run triage:browser`
- `bun run triage:browser:repeat`

### Before push
Run:

```bash
bun run ready:push
```

This runs the push-safe verification lane and refreshes the local environment sync stamp so the pre-push hook does not reject an otherwise green change after `package.json`, `bun.lock`, or `requirements-dev.txt` edits.
