# 👋 Onboarding

## Purpose

This document tells a new developer how to enter the SynaWeave CE repo without creating parallel decisions.

Read in this order:
1. `docs/infra.md`
2. `docs/architecture.md`
3. `docs/legend.md`
4. `docs/apps.md`
5. `docs/packages.md`
6. `docs/python.md`
7. `docs/testing.md`
8. `docs/planning/MASTER.md`

## First things to understand

### 1) This is an intentionally overbuilt monorepo

Do not “simplify” away future seams just because a feature is not active yet.
The repo is meant to prove:
- product thinking
- platform thinking
- pedagogy thinking
- data and ML thinking
- operational thinking

### 2) `docs/infra.md` is the locked choices document

If you want to know:
- what is locked
- what is generic vs provider-specific
- how names should be shortened
- how hosting should scale
- what fail-open means here

start there first.

### 3) The repo prefers short generic names

Examples:
- `DB_URL`
- `OBJ_BUCKET`
- `GRAPH_URL`
- `LF_URL`
- `GCP_PROJECT_ID`

Do not introduce long raw identifiers unless a tool truly forces them.

### 4) The product is a pedagogy engine, not just AI chat

The tutor must orchestrate mode selection.
It must not collapse every learning event into “answer the question in a paragraph.”

## Practical starting steps

```bash
cp .env.example .env
bun run hooks:install
bun run deps:app
bun run verify:docs
```

Then inspect:
- `apps/`
- `packages/contracts/`
- `python/`
- `infra/`

## Working rule

Before adding a new file, ask:
- is there already an owner doc for this concern?
- can this name survive a provider swap?
- can this identifier be shortened?
- does this belong in the core domain or only in an adapter?
