# Governance

## Purpose

This document defines how repository authority, review posture, merge control, and protected-path policy work in SynaWeave.

## Governance model

- Root `docs/` is the only canonical technical documentation surface.
- Planning intent is governed by `docs/planning/MASTER.md`, sprint planning files, and `docs/adrs/`.
- Repository controls are implemented through `tools/verify/main.py`, `tools/hooks/`, `.github/workflows/`, `.github/pull_request_template.md`, `docs/templates/`, `docs/workflow.md`, and protected-path ownership.

## Project roles

### Project owner

- Holds final authority over roadmap, releases, repo policy, exceptions, trademarks, and maintainer appointments.
- May approve or reject policy exceptions, including protected-path changes and GitHub-side admin bypass decisions.

### Maintainers

- Review and merge changes on behalf of the project.
- Enforce planning, ADR, verification, and protected-path policy.
- May require narrower scopes, stronger verification, or additional documentation before merge.

### Contributors

- May propose code, docs, tests, workflows, and planning changes.
- Do not gain roadmap or merge authority automatically by contributing.

## Decision authority

- Durable architecture, runtime, contract, observability, and hosting changes require ADR-backed documentation updates.
- Repository process and policy changes require updates to the matching governance and owner docs.
- Human-readable policy lives in `GOVERNANCE.md`, `CONTRIBUTING.md`, and `AGENTS.md`; executable enforcement lives in the verifier, hooks, and workflows.
- Commit and PR title policy must reject broad umbrella pairs like `docs(docs)` and `test(testing)` in favor of narrower owned scopes.
- Reusable documentation structure lives in `docs/templates/`; templates must reduce duplication rather than create a second policy surface.

## Required repository control surface

- one canonical `README.md` at root
- one canonical docs spine under `docs/`
- one ADR file per sprint under `docs/adrs/sprint-###.md`
- reproducible verification via `tools/verify/main.py`
- local hook entrypoints under `tools/hooks/`
- protected merge posture through `.github/workflows/` and `.github/CODEOWNERS`
- reusable repo-owned templates under `docs/templates/` for recurring planning, ADR, spec, and verification artifacts

## Protected paths

Protected paths require narrower diffs, explicit rationale, and matching doc updates when shared understanding changes.

Protected paths include:

- `AGENTS.md`
- `GOVERNANCE.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `CLA.md`
- `NOTICE`
- `TRADEMARKS.md`
- `.env.example`
- `.github/pull_request_template.md`
- `.github/workflows/**`
- `.github/CODEOWNERS`
- `tools/verify/**`
- `tools/hooks/**`
- `docs/planning/**`
- `docs/adrs/**`
- `docs/templates/**`
- root owner docs under `docs/*.md`

## Merge and review posture

- Maintainers may reject or defer changes that create policy drift, architecture drift, or excess maintenance burden.
- PRs that change protected paths or shared contracts must call out the affected paths and why the change is safe.
- PRs that change templates must explain which recurring artifact becomes more accurate or more reviewable.
- Significant work should map to an explicit sprint, deliverable, and task target before merge.
- When shared understanding changes, the matching owner docs and ADR or planning records must change with the implementation.
- ADR structure enforcement belongs to pull-request and merge-oriented verification lanes, not commit or push automation.

## Review and escalation

Security vulnerabilities, dependency incidents, contract breaks, and workflow-control failures are escalated before merge and must update the relevant durable docs, including:

- `SECURITY.md`
- `docs/operations.md` when operational truth changes
- impacted planning and ADR records

## Runtime boundary governance

- browser surfaces consume only browser-safe config
- API and job runtimes own privileged operations and durable writes
- cross-surface contracts go through shared contract layers unless a superseding ADR states otherwise

## Admin bypass posture

Admin bypass, required checks, stale approvals, and CODEOWNERS review behavior are GitHub-side controls owned by the project owner and maintainers. This repository documents the expected posture, but GitHub rulesets remain the enforcement home for those merge-control decisions.

Expected default-branch ruleset posture:

- GitHub rulesets are the first enforcement home for pull-request requirements, required statuses, stale-approval dismissal, and any merge-blocking CODEOWNERS review requirement.
- pull requests required for protected branches
- direct pushes blocked for non-admin contributors
- required checks should include at least these repo-defined hosted check names when GitHub rulesets are configured to require them:
  - `repo-verify / repo-verify` (from `.github/workflows/repo-verify.yml`; runs `bun run verify:push` on pushes and `bun run verify` on pull requests, with ADR validation staying in the pull-request lane)
  - `dependency-installability / dependency-installability` (from `.github/workflows/dependency-installability.yml`; proves clean Bun installs and direct Python dev-tool pins stay installable without mutating the checked-out repository)
  - `dependency-review / dependency-review` (the PR status stays required even when hosted review can only report that dependency graph support is unavailable)
  - `codeql / codeql-javascript-typescript`
  - `codeql / codeql-python`
  - `CodeQL` when GitHub also reports the aggregate summary status alongside the per-language lanes
  - `secret-scan-fast`
  - `secret-scan-deep`
  - `cla-check`
  - `pr-quality`
- CODEOWNERS file assigns platform-admin and core-maintainer owners for protected-path changes; merge-blocking CODEOWNERS review depends on GitHub rulesets enabling that requirement
- stale approvals dismissed when protected-path diffs change materially
- secret scanning and push protection enabled where the repository tier supports them

Focused supplemental workflows may also run on matching pull-request paths:

- `docs-guard` for canonical docs changes
- `governance-guard` for governance-surface changes
- `protected-paths` for shared protected-path changes

These supplemental workflows are repository-defined review aids. They should be described as focused hosted checks for matching changes, not as confirmed GitHub ruleset-required statuses unless that hosted enforcement is separately verified.

Dependency update posture should stay low-noise and reviewable:

- Renovate is configured in-repo to group routine Bun or npm workspace updates, Python dev requirements, and GitHub Actions updates into separate lanes
- major dependency updates require explicit dependency dashboard approval before PR creation
- grouped update posture reduces review churn but does not replace the hosted dependency-review or dependency-installability lanes

Admin bypass is optional and must stay explicit:

- use it only for urgent governance, security, or repo-recovery cases
- record its use in the pull request template field and review notes
- treat bypass as an exception, not the normal merge path

## Scope in this repository

This governance applies immediately to all top-level surfaces and all future domain additions unless superseded by later ADR entries.
