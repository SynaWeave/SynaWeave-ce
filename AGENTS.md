# AGENTS

This repository is intentionally structured as a governed monorepo with strict boundaries.

## Scope and intent

- Keep each top-level domain focused: `apps/`, `packages/`, `python/`, `infra/`, `testing/`, `tools/`, `docs/`, `.github/`.
- Prefer structure-first work during foundation and maintain contract-first execution afterwards.
- Keep decisions durable and traceable through `docs/`, `docs/planning/`, and `docs/adrs/`.
- Treat root `docs/` as the only canonical technical docs surface.
- Reuse `docs/templates/` for recurring planning, ADR, spec, and verification artifacts instead of inventing parallel shapes.

## Boundaries to preserve

- No second documentation runtime in Sprint 1.
- No new architecture decisions that alter root contracts without a matching ADR entry.
- No root-level documentation drift: update only through the docs spine under `docs/`.

## Required local checks

Before merging or marking a task complete:

- run `python3 -m tools.verify.main`
- run `bun run verify` when TypeScript, Python, hooks, workflows, or shared repo controls change
- run the matching language checks for changed Python or TypeScript surfaces
- run focused checks for changed areas in the same domain
- verify commit format and docs alignment for touched surface

## Runtime and domain rules

- browser surfaces must not consume server-only credentials
- reusable logic belongs in `packages/*` or `python/*` rather than app entrypoints
- app folders under `apps/` should remain runtime-first, not library-first

## Security and quality posture

- do not commit `.env` or secret artifacts
- keep secrets at env/runtime boundaries described by `packages/config` and `docs/infra.md`
- avoid schema or contract drift without test updates

## Commit and review behavior

- follow `CONTRIBUTING.md` commit rules
- prefer commit subjects that exceed the minimum with concrete, specific rationale instead of threshold gaming
- include a short operational rationale in PR summary when behavior changes runtime boundaries
- keep PRs linked to sprint and ADR context where possible
- keep substantial work linked to an explicit sprint, deliverable, and task target
- keep recurring doc structure DRY by updating the owning template or owner doc instead of cloning rules into new files

## What this file updates

This file is intentionally short and authoritative for agent-level behavior.
If any rule conflicts with `CONTRIBUTING.md` or `GOVERNANCE.md`, prefer the repo-level governance file.
