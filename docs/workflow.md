# 📜 Workflow

## 🧩 Purpose

This document is the source of truth for how developers move work through the repository.

This file defines:

- how a developer should ramp into the product and repo
- how work should move from planning to implementation to verification
- how local tools, hooks, CI, and AI review should be used together
- what should happen before a branch is opened, before a PR is opened, and before merge
- which rules are canonical versus which tools only enforce or assist those rules

This file does **not** replace:

- architecture ownership in `docs/architecture.md`
- app and package ownership in `docs/apps.md` and `docs/packages.md`
- repo governance in `GOVERNANCE.md`
- contribution policy in `CONTRIBUTING.md`
- sprint execution in `docs/planning/**`

---

## 🧭 Workflow thesis

The repo uses one governed workflow for humans and coding agents.

The workflow is intentionally simple:

1. understand the product and owned surface
2. confirm planning and architecture boundaries
3. make a narrow change in the correct repo surface
4. update docs, tests, and verification with the implementation
5. run local proof
6. open a scoped PR with evidence
7. merge only after hosted checks and reviewer reasoning agree

This means AI tools are support layers, not substitute authority.

- deterministic repo controls remain the hard gate
- human maintainers remain the merge authority
- AI review should add semantic signal, not override repo governance

---

## 🏗️ Product and system reality every contributor must know

SynaWave is a governed, multi-surface study intelligence platform.

The current real Sprint 1 runtime slice spans:

- `apps/extension`
- `apps/web`
- `apps/api`
- `apps/ingest`
- shared contracts under `packages/`
- shared Python runtime helpers under `python/common/`

The bounded runtime proof path is:

1. sign in from the web shell or extension
2. resolve one shared identity across both surfaces
3. bootstrap one server-owned workspace through the API
4. write one durable workspace action through the API
5. run one separate ingest job
6. read the updated workspace state back through the browser surface
7. inspect `/metrics` and local proof artifacts

Contributors must understand that path before changing architecture-sensitive code.

---

## 🧱 Canonical source map

Use these files in this order when you need truth.

### Product and architecture truth

- `README.md`
- `docs/architecture.md`
- `docs/apps.md`
- `docs/packages.md`
- `docs/python.md`
- `docs/infra.md`
- `docs/operations.md`

### Repo policy and change rules

- `AGENTS.md`
- `GOVERNANCE.md`
- `CONTRIBUTING.md`
- `SECURITY.md`

### Planning and execution truth

- `docs/planning/MASTER.md`
- `docs/planning/sprint-###/overview.md`
- `docs/planning/sprint-###/d#-*.md`
- `docs/adrs/sprint-###.md`

### Reusable document structure

- `docs/templates.md`
- `docs/templates/**`

If two files disagree:

- `docs/operations.md` wins for present runtime truth
- `docs/architecture.md` wins for intended system shape
- `GOVERNANCE.md` and `CONTRIBUTING.md` win for repo policy

---

## 👤 Developer lifecycle

### 1. Ramp

Before taking work, a developer should:

- read the canonical source map
- understand the current runtime slice
- install local tooling
- run full verification once
- confirm the owned sprint, deliverable, and task target

### 2. Plan

Before writing code, a developer should:

- identify the owned boundary
- confirm whether the change affects contracts, docs, tests, or ADRs
- confirm whether the change touches protected paths
- decide what evidence will prove the change is real

### 3. Implement

During implementation, a developer should:

- stay inside the owned repo surface
- reuse shared packages or shared Python modules instead of copying logic
- keep browser-safe and server-only boundaries explicit
- keep comments and naming aligned with repo style

### 4. Prove

Before PR, a developer should:

- run local verification
- inspect changed docs for truth drift
- check whether new behavior requires new tests
- make sure the branch is clean and explainable

### 5. Review and merge

At PR time, the developer and reviewers should:

- explain what changed
- explain why the scope is safe
- show proof output
- confirm that deterministic checks and semantic review both make sense

---

## 🛠️ Local setup and daily commands

### Required developer baseline

Every contributor should have:

- GitHub org access
- Bun
- Node 20+
- Python 3
- Docker and Compose
- Playwright Chromium
- `.env` created from `.env.example`
- repo hooks installed

### Clone setup

```bash
cp .env.example .env
bun run hooks:install
bun run deps:app
bun run deps:browser
```

After `bun run hooks:install`, the repo-owned hooks own the normal environment-sync path for dependency-changing checkout, merge, rewrite, and push flows. Use `bun run sync` only when a hook reports a real sync failure and you need to rerun the sync command directly.

### Core verification commands

```bash
python3 -m tools.verify.main
bun run verify
```

### Useful scoped commands

```bash
bun run lint:ts
bun run typecheck:ts
bun run verify:python
bun run verify:browser
bun run test:e2e
bun run test:accessibility
```

### Local runtime commands

```bash
bun run dev:api
bun run dev:web
bun run build:extension
```

Short root aliases are also available for common runtime commands: `bun run api`, `bun run web`, `bun run ext`, and `bun run check`.

---

## 🔐 Security and boundary rules

### Browser-safe versus server-only

- browser surfaces may only use browser-safe config
- privileged credentials stay in server runtimes only
- browser bundles must not directly consume service-role or storage-admin credentials

### Durable-write rule

- durable writes go through `apps/api`
- async follow-up work may happen in `apps/ingest`
- browser surfaces must not invent alternate durable-write paths

### Shared logic rule

- reusable TS logic belongs in `packages/*`
- reusable Python logic belongs in `python/*`
- `apps/*` are runtime homes first, not library homes

### Docs rule

- root `docs/` is the only canonical technical docs surface
- do not create a second docs system inside `apps/` or tool-specific folders

---

## ✅ Definition of done

A change is only done when:

- implementation is correct in the owned surface
- docs are updated when truth changed
- tests are updated when behavior changed
- local verification passes
- hosted checks pass
- the PR summary explains the change in governed repo language

If code changed but docs/tests/proof did not move with it, the change is incomplete.

---

## 🧪 Verification posture

### Deterministic gates

These remain the hard gates:

- `python3 -m tools.verify.main`
- `bun run verify`
- CodeQL
- dependency review
- secret scanning
- protected-path checks
- docs and governance guards

### Semantic review layer

This is where AI review tools belong.

AI review should focus on:

- risky logic changes
- missing tests
- contract drift
- architecture drift
- browser/server boundary mistakes
- behavior changes without matching docs or ADR updates

AI review should **not** replace deterministic repo controls.

---

## 🤖 AI review posture

The repo should treat AI review as an advisory semantic layer on top of the deterministic gates.

### Current target posture

Use Qodo for:

- PR review comments
- cross-file semantic issue finding
- missing test detection
- architecture and workflow drift detection
- local IDE review before PRs

Do **not** use Qodo to replace:

- CodeQL
- secret scanning
- dependency review
- repo verification
- hosted path and governance checks

### Rollout posture

Start with:

- GitHub PR review enabled in advisory mode
- local IDE review optional but recommended
- repo-level configuration checked into the repo root
- organization and repository rules managed in the Qodo portal

Only consider required or blocking status after a short tuning period with measured false-positive rates.

---

## 🤖 Qodo setup strategy for this repo

The repo should use one canonical human-readable policy surface and one tool configuration surface.

### Canonical human-readable policy surface

These files define the real rules:

- `AGENTS.md`
- `GOVERNANCE.md`
- `CONTRIBUTING.md`
- `docs/workflow.md`
- `docs/onboarding.md`
- `docs/architecture.md`
- `docs/operations.md`
- `docs/planning/**`
- `docs/adrs/**`

### Tool configuration surface

- `.pr_agent.toml`

That file should only configure behavior, automation, and bootstrap instructions.
It should not become a second canonical policy system.

### Qodo review priorities for this repo

Qodo should prioritize findings about:

- missing tests for changed behavior
- cross-surface contract drift
- API versus browser responsibility violations
- provider-specific leakage into domain contracts
- architecture changes without matching ADR or planning updates
- behavior changes without `docs/operations.md` or owner-doc updates

### Qodo review de-priorities for this repo

Qodo should treat these as lower-value review targets because deterministic checks already cover much of them:

- routine docs-only changes
- workflow-only formatting fixes
- generated artifacts
- stored proof fixtures unless nearby product logic changed

---

## 🌿 Branch and PR workflow

### Branch expectations

Each meaningful change should map to:

- one sprint
- one deliverable
- one bounded objective

### Before opening a PR

A developer should be able to answer:

- what product or repo truth changed
- which surface owns that change
- what proof shows the change is real
- which docs moved with the change
- whether any protected paths were touched

### PR expectations

Every PR should include:

- the owned sprint and deliverable
- affected repo surfaces
- verification output
- note of any contract or governance changes
- note of any intentional doc consolidation or deletions

---

## 🚨 Review heuristics for maintainers and agents

Reject or narrow a change when:

- it introduces a second source of truth
- it adds reusable logic directly inside an app runtime
- it changes payloads without contract/test alignment
- it changes behavior without docs alignment
- it changes architecture without ADR or planning alignment
- it pushes provider specifics across the wrong boundary
- it relies on smoke seams instead of real runtime proof

---

## 📚 Onboarding relationship

`docs/onboarding.md` is the dedicated ramp guide for developers who are new to the project or product.

Use this file for:

- workflow truth
- repo movement rules
- AI review posture
- pre-PR and pre-merge expectations

Use `docs/onboarding.md` for:

- new-dev ramp sequence
- product and system walkthrough
- day-1, day-2, and week-1 expectations
- first-task guidance

---

## 🎯 Outcome this workflow should produce

A contributor using this repo correctly should be able to:

- understand the current system shape quickly
- make changes in the right place
- prove those changes locally
- open a PR that reviewers can trust
- use AI review as extra signal without letting it replace repo discipline

That is the workflow standard for SynaWave.
