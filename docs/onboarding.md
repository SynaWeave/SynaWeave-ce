# 📜 Onboarding

## 🧩 Purpose

This document is the source of truth for ramping a new developer into the SynaWave product, repo, and working model.

This file defines:

- what the product is
- what the repo already proves today
- how the system is shaped
- what a new developer should read first
- what a new developer should do on day 1 and week 1
- what understanding is required before owning Sprint 2 work

This file does **not** replace architecture, governance, or planning owner docs.
It is the guided entry point into them.

---

## 🧭 Product thesis

SynaWave is a study intelligence platform.

The product is not just a note app or flashcard app.
The goal is to help users:

- capture information
- organize it
- connect it
- retrieve it
- practice it
- understand it
- retain it better over time

The long-term product direction combines:

- spaced repetition
- Zettelkasten-style linking
- Feynman-style mini quizzes
- second-brain capture
- source-grounded tutoring
- recommendation loops
- progressive knowledge-building workflows

---

## 🧱 What is real in the repo today

The repo already proves one bounded multi-surface runtime slice.

### Real today

- browser extension shell
- web control-plane shell
- FastAPI request boundary
- separate ingest job path
- shared contracts
- shared Python runtime helpers
- local metrics and proof artifacts
- contract tests
- browser e2e tests
- accessibility tests
- repo verification and hosted checks

### Reserved for later

- broader ML runtime depth
- broader evaluation runtime depth
- MCP expansion
- managed cloud deployment proof
- broader graph, retrieval, and recommendation depth

A new developer should not overclaim the repo. Build from the current truth.

---

## 🏗️ System shape in plain English

Think of the system as four active surfaces plus shared building blocks.

### 🪟 Extension

Thin in-context browser client for capture and quick interaction.

### 🌐 Web

Control plane for the broader authenticated workspace.

### ⚙️ API

Public request boundary and durable-write owner.

### 📥 Ingest

Async follow-up worker for background jobs and derived outputs.

### 🧩 Shared layers

- `packages/*` for shared TypeScript contracts and UI/config primitives
- `python/*` for shared runtime and intelligence helpers
- `docs/*` for the canonical technical story
- `tools/*` for repo controls and local automation

---

## 🔄 Current runtime proof path

Every new developer should understand this before taking system-sensitive work.

1. sign in from `apps/web` or `apps/extension`
2. resolve one shared user identity across both surfaces
3. bootstrap a server-owned workspace through `apps/api`
4. write one durable action through the API
5. trigger one separate ingest job through `apps/ingest`
6. read the updated workspace state back in the browser surface
7. inspect metrics and local proof artifacts

If a developer cannot explain that path, they are not fully ramped yet.

---

## 🗺️ Repo map

### Top-level folders

- `apps/` — executable runtime surfaces
- `packages/` — shared TypeScript packages and contracts
- `python/` — shared Python modules
- `infra/` — deployment, observability, and policy envelopes
- `testing/` — tests and proof artifacts
- `tools/` — hooks, verifiers, and local automation
- `docs/` — canonical documentation and planning

### Key app homes

- `apps/extension`
- `apps/web`
- `apps/api`
- `apps/ingest`
- `apps/mcp`
- `apps/ml`
- `apps/eval`

### Shared TypeScript homes

- `packages/contracts`
- `packages/config`
- `packages/tokens`
- `packages/ui`

### Shared Python homes

- `python/common`
- `python/data`
- `python/evaluation`
- `python/graph`
- `python/models`
- `python/retrieval`
- `python/training`

---

## 📚 Read in this order

### First pass

1. `README.md`
2. `docs/onboarding.md`
3. `docs/workflow.md`
4. `GOVERNANCE.md`
5. `CONTRIBUTING.md`

### Second pass

6. `docs/architecture.md`
7. `docs/apps.md`
8. `docs/packages.md`
9. `docs/python.md`
10. `docs/operations.md`
11. `docs/testing.md`
12. `docs/infra.md`

### Execution context

13. `docs/planning/MASTER.md`
14. `docs/planning/sprint-001/overview.md`
15. your assigned Sprint 2 planning packet
16. the current sprint ADR file

---

## 🛠️ Day 1 checklist

### Tooling setup

```bash
cp .env.example .env
bun run hooks:install
bun run deps:app
bun run deps:browser
```

After the one-time `bun run hooks:install` wrapper install, the local `.git/hooks/*` entries become wrappers that delegate to the current repo-owned files in `tools/hooks/`, so content updates to existing repo hook files are picked up automatically without reinstalling copied hook bodies. Re-run `bun run hooks:install` when repo hook filenames are added, removed, or renamed, or when local wrappers are missing or damaged, so the local wrapper set stays aligned. That reinstall also removes stale repo-managed hook names from older clones, including legacy copied hook bodies that predate the wrapper upgrade, while leaving unrelated local custom hooks alone. Those repo-owned hooks handle the normal environment-sync path for dependency-changing checkout, merge, rewrite, and push flows. Use `bun run sync` only when a hook reports a real sync failure and you need to rerun the sync command directly.

### First proof run

```bash
python3 -m tools.verify.main
PLAYWRIGHT_HEADLESS=true bun run verify
```

### Local runtime boot

```bash
bun run dev:api
bun run dev:web
bun run build:extension
```

Short root aliases are also available for the common runtime commands: `bun run api`, `bun run web`, `bun run ext`, and `bun run check`.

### Local endpoints

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:3000`
- Metrics: `http://127.0.0.1:8000/metrics`

---

## ✅ What a new developer must be able to explain

Before they start meaningful Sprint 2 work, they should be able to explain:

- what the product is trying to become
- what the repo proves today
- what is active now versus reserved for later
- the role of extension, web, API, and ingest
- why durable writes go through the API
- where shared contracts live
- where shared Python runtime logic lives
- where canonical docs live
- how local verification works
- what makes a change “done” in this repo

---

## 🔐 Non-negotiable repo rules

### One docs home

- root `docs/` is the only canonical technical docs surface

### One durable-write owner

- durable writes go through the API

### Shared logic belongs in shared homes

- reusable TS logic belongs in `packages/*`
- reusable Python logic belongs in `python/*`

### Browser/server boundary stays explicit

- browser surfaces only use browser-safe config
- server runtimes own privileged credentials

### Docs, tests, and proof move with code

- no behavior change is complete without matching docs and verification

---

## 🤖 How AI tools fit into developer work

AI tools are allowed and useful in this repo, but they must follow the repo instead of redefining it.

### Good uses

- code explanation
- focused refactors
- missing test suggestions
- architecture drift spotting
- PR review support
- local pre-PR review

### Bad uses

- inventing a second source of truth
- making architecture claims not backed by docs
- hiding smoke seams behind confident prose
- adding provider-specific shortcuts across boundaries
- treating AI review comments as merge authority

Qodo belongs in the semantic review layer described in `docs/workflow.md`.

---

## 🧪 Day 2 to week 1 expectations

### Day 2

- trace the current runtime path end-to-end
- inspect shared contracts used by the browser and API surfaces
- inspect the tests that prove the current path
- inspect `docs/operations.md` for present-state truth

### Day 3 to day 5

- take one small scoped task in an owned surface
- run verification locally without help
- explain the PR in sprint/deliverable language

### By end of week 1

A new developer should be able to:

- boot the repo
- run verification
- explain the bounded Sprint 1 runtime slice
- explain their owned Sprint 2 surface
- open one reviewable PR that fits repo governance

---

## 🎯 Good first tasks

Good onboarding tasks are:

- small docs truth-alignment fixes
- narrow API improvements within existing contracts
- test additions for already-real behavior
- UI changes inside the current token and package system
- observability or verification improvements that stay inside current architecture boundaries

Bad onboarding tasks are:

- architecture rewrites before reading ADRs
- provider-specific shortcuts
- new docs systems
- new shared abstractions without checking owner docs
- cross-surface refactors before understanding the runtime path

---

## 🧠 Team lead explanation for kickoff

Use this summary with new developers:

“SynaWave is a governed multi-surface study intelligence platform. Sprint 1 is closed, which means the repo foundation, first runtime slice, and first quality system are already in place. Your job in Sprint 2 is not to renegotiate the repo shape. Your job is to extend product value inside the current architecture, contracts, docs spine, and verification model. Before you take work, you need to understand the extension → web → API → ingest flow, know where shared contracts and shared runtime logic live, and know what proof is required for a real change.”

---

## 🌱 Onboarding outcome

A developer is fully ramped when they can:

- describe the product thesis clearly
- describe the current runtime proof path clearly
- locate the correct repo home for a given change
- run the local verification commands successfully
- explain the difference between deterministic gates and semantic review
- take a Sprint 2 task without violating repo governance

That is the onboarding standard for this repo.

## Local commands new developers should learn first

### Core commands
- `python3 -m tools.verify.main`
- `bun run verify`
- `bun run ready:push`

### Fast day-to-day commands
- `bun run check:py:fast`
- `bun run check:browser`
- `bun run check:fast`

### Browser triage commands
- `bun run triage:ports`
- `bun run triage:browser`
- `bun run triage:browser:repeat`

A new developer should understand that `verify` and `sync_environment` are separate concerns:
- `verify` proves code and repo correctness
- `sync_environment` refreshes the local tool stamp used by hooks
