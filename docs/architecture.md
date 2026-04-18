# 📜 Architecture

## 🧩 Purpose

This document defines the shared technical architecture of the repository.
It is the canonical read for how runtime surfaces, shared packages, and Python modules fit together.

This file is the source of truth for:

- the repository-wide platform shape and runtime map
- how user flows move from client to durable state
- how cross-surface contracts are versioned and enforced
- how observability and security boundaries are attached

This file does **not** define:

- sprint execution details (`docs/planning/MASTER.md`)
- governance details (`AGENTS.md`, `CONTRIBUTING.md`)
- operational readiness status (`docs/operations.md`)

---

## 🧭 Architecture thesis

SynaWeave is a shallow, multi-surface architecture with one shared contract layer.

The platform shape is intentionally strict:

- one extension runtime (`apps/extension`)
- one web control plane (`apps/web`)
- one request-serving API boundary (`apps/api`)
- one first job runtime (`apps/ingest`)
- reserved future runtime homes for MCP, ML, and evaluation (`apps/mcp`, `apps/ml`, `apps/eval`)
- shared TypeScript packages under `packages/`
- reusable Python intelligence modules under `python/`

Provider selection is intentionally adapter-first:

- domain and contract layers stay provider-neutral, while provider-specific behavior lives behind owned adapters
- Sprint 1 may name default adapter targets where the branch already proves one concrete path, but those defaults are not permanent lock-in
- edge, CDN, and API gateway choices stay deferred until adapters need a concrete external platform decision

No second documentation runtime exists in `apps/`, and no other top-level app runtime is part of Sprint 1.

---

## 🧱 Topology

### 🪟 User-facing runtimes

- `apps/extension`: in-context capture and quick study shell
- `apps/web`: authenticated workspace control plane

### ⚙️ Runtime boundaries

- `apps/api`: request-serving boundary and first durable write path
- `apps/ingest`: job boundary for asynchronous operations

### 🧪 Reserved later runtimes

- `apps/mcp`: standardized tool interface surface
- `apps/ml`: online and offline ML-serving or orchestration surface when separated from the API
- `apps/eval`: evaluation and benchmark surface when separated from jobs or ML tooling

### 🧩 Shared runtime surfaces

- `packages/contracts`: typed shape contracts for all cross-surface payloads
- `packages/config`: shared configuration contract and loading helpers for TypeScript runtimes
- `packages/tokens`: visual and theme tokens
- `packages/ui`: shared UI primitives
- `python/common`: cross-cutting Python primitives (retry, errors, typing, telemetry helpers)
- `python/data`: ingestion and data-prep primitives
- `python/evaluation`: reusable evaluation utilities and offline scoring support
- `python/graph`: graph modeling and relationship-oriented helpers
- `python/models`: model-facing integration seams and shared model contracts
- `python/retrieval`: retrieval utilities and retrieval-adjacent contracts
- `python/training`: training and experiment-prep support kept outside app entrypoints

---

## 🌐 Runtime and data flow

The platform data path is explicit and short:

```text
User action
  -> apps/extension or apps/web
  -> apps/api (public contract only)
  -> Python/JS service modules
  -> infra stores/services
  -> response with stable contract + event telemetry
```

Rules in this flow:

- every public payload crosses `packages/contracts`
- every durable write passes through `apps/api`
- job work can read and enrich durable state but does not own the primary user-facing contract
- provider-specific stores, auth systems, and telemetry backends stay behind adapter seams instead of leaking into product contracts

## 🔌 Adapter-first provider posture

The rebuild keeps provider choices behind adapters from the start.

- Sprint 1 treats Supabase as the default adapter target for auth, operational Postgres, and storage-facing contracts because that target fits the current branch shape
- that default target does not make Supabase part of the domain contract, and later replacements must preserve the same contract boundaries
- edge routing, CDN placement, and API gateway insertion remain intentionally undecided until runtime scale or operations needs force a concrete adapter-backed choice

---

## 🔐 Security and trust boundaries

Security is split by boundary class:

### Browser boundaries

- `apps/extension` and `apps/web` can only use browser-safe config values
- no privileged credentials are allowed in browser bundles

### Server boundaries

- `apps/api` and `apps/ingest` can use server-only credentials through environment/classified config
- all privileged operations must be auditable and isolated

### Contract boundaries

- only serialized, versioned payloads may cross runtime classes
- contract evolution is backwards-compatible by default
- every contract shift records migration or breakage context

---

## 🧠 Repository-level domain split

This architecture intentionally keeps shared responsibilities separated:

- `apps/`: executable surfaces and integration shells
- `packages/`: shared TypeScript boundaries and contracts
- `python/`: shared intelligence modules and reusable domain logic
- `infra/`: deployment, policy, and operations envelopes
- `tools/verify`: executable repository assertions
- `testing/`: quality signal taxonomy and guardrails

No folder should hide mixed concerns across these lines.

---

## 🧪 Observability and evidence model

The observability model follows a single event model:

- traces, metrics, and logs are emitted by runtime surfaces
- runtime exports route through OpenTelemetry collector pipelines
- product-facing AI traces and online scores route through Langfuse adapters
- offline experiment and offline evaluation evidence route through MLflow adapters

Evidence obligations:

- one reproducible trace for the critical path
- one reproducible failure path with clear error metadata
- one reproducible baseline metric per core runtime path
- durable metric, trace, dashboard, and evaluation records must be preserved in versioned config, machine-readable artifacts, or replayable local stores

Sprint 1 observability posture stays bounded and honest:

- self-hosted Langfuse and MLflow are the current local proof backends, because the branch proves those paths without claiming managed service durability
- managed Langfuse and managed MLflow remain valid later deployment targets as long as they stay behind the same adapters and evidence rules
- collector routing, Prometheus metrics, Grafana dashboards, and versioned proof artifacts remain the durable review surface even when backend hosting changes later

---

## 🧭 Governance-aligned design implications

Sprint 1 architecture decisions are intentionally conservative:

- no second docs runtime in `apps/`
- one repository-wide documentation root (`docs/`)
- root `docs/` may be published statically, but remains the only canonical documentation source
- no app-specific contracts outside the shared contract package
- token-first UI language and shared design primitives
- verified contracts and folders before feature expansion

The next sprints may refine depth but may not discard these boundaries without a new ADR entry.
