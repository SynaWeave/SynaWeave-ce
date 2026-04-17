# 📜 Apps

## 🧩 Purpose

This document defines the ownership boundaries, runtime responsibilities, allowed dependencies, and maturity expectations for every application under `apps/`.

This file is the source of truth for:
- what each app is responsible for
- what each app is allowed to import
- what each app is allowed to call
- which runtime category each app belongs to
- how app boundaries relate to the wider platform

This file does **not** define package internals, infrastructure details, or sprint execution plans. Those belong in:
- `docs/packages.md`
- `docs/infra.md`
- `docs/planning/MASTER.md`
- sprint planning files under `docs/planning/`

---

## 🧭 App maturity labels

Every app described here must use one of these states only:

- **planned** — specified but no reserved app home exists yet
- **scaffolded** — reserved app home exists, but the runtime is not bootable
- **bootable** — starts successfully, but not yet integrated into real user flows
- **integrated** — participates in at least one real end-to-end flow
- **production-ready** — safe for live users within current scope
- **hardened** — instrumented, tested, documented, and operationally mature

No other maturity labels should be used in app-level documentation.

---

## 📦 App inventory

The `apps/` folder contains these application boundaries:

- `apps/extension`
- `apps/web`
- `apps/api`
- `apps/mcp`
- `apps/ingest`
- `apps/ml`
- `apps/eval`

Each app must own one runtime concern only. If an app begins to own multiple unrelated concerns, the architecture should split it rather than let the boundary blur.

In Deliverable 1, the reserved homes for web, API, ingest, MCP, ML, and evaluation are scaffold placeholders only.
Ownership stays centralized in this document until later deliverables add runnable app internals.

---

## 🪟 `apps/extension`

### 🧩 Purpose
The browser extension is the thin MV3 client for in-context user workflows.

### 🎯 Responsibilities
- selection and page-context capture
- side-panel study experience
- lightweight account/session-aware user shell
- local transient state and retry queue
- browser-native UX hooks
- secure delegation of backend work to APIs

### 🚫 Non-responsibilities
- long-term source of truth
- privileged backend operations
- direct ownership of business logic
- model inference orchestration
- graph traversal and retrieval logic
- premium/open-core monetization logic

### 🔗 Allowed dependencies
- `packages/ui`
- `packages/tokens`
- `packages/contracts`
- `packages/config`

### ⛔ Forbidden dependencies
- direct imports from Python modules
- direct provider SDK usage in domain logic
- direct privileged database or storage access
- direct coupling to unrelated app internals outside shared contracts

### 🔄 Inbound interfaces
- browser actions
- content-script events
- side-panel user actions
- runtime messages

### 🔄 Outbound interfaces
- API calls through shared contracts
- extension runtime messages
- local extension storage through approved adapter layer

### 📏 Runtime rules
- MV3 service worker is the event coordinator
- side panel is the primary persistent UI surface
- content scripts are page-context bridges only
- all cross-surface messages must be versionable and schema-validated

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 2 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🌐 `apps/web`

### 🧩 Purpose
The web app is the authenticated control plane for the product.

### 🎯 Responsibilities
- sign-in and account recovery flows
- workspace shell
- source, card, and deck management views
- settings and profile management
- analytics, admin, and labeling surfaces
- future internal operator tooling

### 🚫 Non-responsibilities
- static public documentation
- extension-specific browser API ownership
- background job execution
- direct model training orchestration

### 🔗 Allowed dependencies
- `packages/ui`
- `packages/tokens`
- `packages/contracts`
- `packages/config`
- approved browser-safe auth client

### ⛔ Forbidden dependencies
- direct imports from extension runtime
- direct imports from Python modules
- direct use of privileged credentials
- undocumented cross-app coupling

### 🔄 Inbound interfaces
- browser navigation
- authenticated user actions
- shared API contracts

### 🔄 Outbound interfaces
- request-serving API
- approved browser-safe auth/session boundary

### 📏 Runtime rules
- authenticated routes must fail closed
- server state uses TanStack Query
- local UI state uses Zustand only when needed
- web must be the canonical fallback surface for account recovery and session repair

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 2 target: **integrated**  
Sprint 5 target: **production-ready**

---

## ⚙️ `apps/api`

### 🧩 Purpose
The API is the first request-serving backend boundary.

### 🎯 Responsibilities
- authenticated request handling
- normalized public HTTP contracts
- runtime status endpoints
- workspace bootstrap and identity-normalization paths
- future source, card, retrieval, and recommendation APIs
- backend-side policy enforcement through approved adapters

### 🚫 Non-responsibilities
- static-site rendering
- browser-specific UX state
- long-running job execution
- direct ownership of UI primitives

### 🔗 Allowed dependencies
- `packages/contracts` via generated or mirrored schemas
- `packages/config` concepts mirrored in Python
- approved Python shared modules under `python/`
- provider adapters at the edge

### ⛔ Forbidden dependencies
- direct UI concerns
- direct dependency on extension or web internals
- ad hoc response shapes outside shared API contracts

### 🔄 Inbound interfaces
- HTTP JSON requests
- authenticated browser calls
- future internal service calls through explicit contracts only

### 🔄 Outbound interfaces
- `database_store`
- `blob_store`
- `identity_provider`
- future `vector_store`, `graph_store`, `model_provider`, and `queue_provider`

### 📏 Runtime rules
- request-serving service only
- health, readiness, identity, and bootstrap routes are mandatory from Sprint 1
- all public responses use one envelope shape
- request ID and version metadata are mandatory

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 2 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🧰 `apps/mcp`

### 🧩 Purpose
The MCP app is the reusable tool surface for AI-facing interactions with the platform.

### 🎯 Responsibilities
- expose approved study-platform tools through MCP
- normalize tool interfaces across extension, web, and future native surfaces
- isolate MCP transport concerns from core domain logic

### 🚫 Non-responsibilities
- primary product API
- browser auth UI
- direct ownership of datasets or storage

### 🔗 Allowed dependencies
- Python shared modules under `python/`
- mirrored shared schemas/contracts
- approved adapters

### ⛔ Forbidden dependencies
- direct UI ownership
- provider-specific logic in tool definitions
- product-only route coupling

### 🔄 Inbound interfaces
- MCP client requests
- future internal AI workflows

### 🔄 Outbound interfaces
- approved backend services and adapters

### 📏 Runtime rules
- MCP is a protocol surface, not a product surface
- tool names must remain generic and stable
- all tool calls must be observable and testable

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 📥 `apps/ingest`

### 🧩 Purpose
The ingest app is the background execution boundary for deterministic ingestion and preprocessing work.

### 🎯 Responsibilities
- background jobs
- source normalization
- artifact seeding and validation
- future scraping, cleaning, chunking, embedding kickoff, and graph-extraction kickoff

### 🚫 Non-responsibilities
- request-serving APIs
- direct browser interactions
- UI ownership

### 🔗 Allowed dependencies
- Python shared modules under `python/`
- approved adapters
- mirrored schema contracts where needed

### ⛔ Forbidden dependencies
- direct UI dependencies
- undocumented runtime coupling to `apps/api`
- direct provider logic outside adapter boundaries

### 🔄 Inbound interfaces
- job invocation
- future queue-triggered work
- explicit internal execution parameters

### 🔄 Outbound interfaces
- `blob_store`
- `database_store`
- future `queue_provider`, `vector_store`, and `graph_store`

### 📏 Runtime rules
- run-to-completion only
- idempotent job behavior
- structured logs are mandatory
- every job must have explicit success, failure, and retry semantics

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🔬 `apps/ml`

### 🧩 Purpose
The ML app is the runtime boundary for model-serving and ML-specific application logic that should not live inside the request-serving API or generic ingest jobs.

### 🎯 Responsibilities
- future model inference serving
- ranking and difficulty prediction endpoints
- feature-to-model application paths
- model-router boundary
- future compact tutoring-model inference

### 🚫 Non-responsibilities
- full offline training pipeline ownership
- static documentation
- extension or web UI concerns

### 🔗 Allowed dependencies
- Python shared modules under `python/`
- approved model and embedding adapters
- approved storage and metrics adapters

### ⛔ Forbidden dependencies
- direct UI imports
- direct provider coupling in domain logic
- training-only workflows that should live in batch/eval paths

### 🔄 Inbound interfaces
- internal service requests
- future explicit API delegation
- batch feature payloads

### 🔄 Outbound interfaces
- `model_provider`
- `embedding_provider`
- `trace_sink`
- `feature_flag_provider`

### 📏 Runtime rules
- any online inference path must be observable and cost-aware
- model invocations must be measurable by latency and error rate
- output contracts must remain versioned and typed

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 📏 `apps/eval`

### 🧩 Purpose
The eval app is the execution boundary for evaluation and regression workflows.

### 🎯 Responsibilities
- offline and batch eval execution
- retrieval evals
- answer-quality evals
- ranking evals
- cost and latency eval collection
- future benchmark scheduling

### 🚫 Non-responsibilities
- request-serving user API
- primary user-facing UI
- direct browser interaction

### 🔗 Allowed dependencies
- Python shared modules under `python/`
- eval datasets and schemas
- Langfuse and MLflow-facing adapters
- approved storage and trace adapters

### ⛔ Forbidden dependencies
- direct UI ownership
- product-side route ownership
- provider-specific logic outside adapters

### 🔄 Inbound interfaces
- scheduled runs
- manual evaluation triggers
- experiment comparison inputs

### 🔄 Outbound interfaces
- `trace_sink`
- `blob_store`
- `database_store`
- future experiment-tracking adapters

### 📏 Runtime rules
- eval outputs must be reproducible
- datasets must be versionable
- regression outcomes must be machine-readable
- no hidden eval logic outside `testing/evals/` and documented eval runtimes

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🔗 Cross-app dependency rules

### ✅ Allowed app dependency direction

Apps may depend on:
- shared packages
- shared Python modules where appropriate
- approved API contracts
- provider adapters at the app edge

### 🚫 Forbidden app dependency direction

Apps may **not**:
- import implementation internals from sibling apps
- bypass shared contracts for cross-surface serialization
- embed provider-specific logic into domain-level interfaces
- couple UI apps directly to backend implementation details

### 📏 Rule of thumb

If two apps need to share:
- types → use `packages/contracts`
- tokens → use `packages/tokens`
- UI primitives → use `packages/ui`
- config shape → use `packages/config` plus Python mirror
- domain behavior → move it to an approved shared boundary, not a sibling-app import

---

## ☁️ Runtime-class rules

Every app must fit one of these runtime classes:

- **browser client**
- **web client**
- **request-serving backend**
- **job runtime**
- **evaluation runtime**
- **protocol surface**

The current app-to-runtime map is:

- `apps/extension` → browser client
- `apps/web` → web client
- `apps/api` → request-serving backend
- `apps/mcp` → protocol surface
- `apps/ingest` → job runtime
- `apps/ml` → request-serving backend or job runtime depending on workload
- `apps/eval` → evaluation runtime

No app should blur runtime classes without an ADR-backed reason.

---

## 👀 Observability ownership by app

Every app must own its own instrumentation boundary.

- `apps/extension` owns side-panel, worker, and messaging spans
- `apps/web` owns browser and route-level spans
- `apps/api` owns request, route, dependency, and business-operation spans
- `apps/ingest` owns job lifecycle spans
- `apps/ml` owns inference and model-operation spans
- `apps/eval` owns eval-run and benchmark spans
- `apps/mcp` owns tool invocation and protocol spans

No app may rely on another app to describe its runtime health.

---

## 🔐 Security ownership by app

Each app must explicitly own its own security boundaries.

- `apps/extension` owns browser-safe storage and browser-safe auth handling
- `apps/web` owns authenticated route discipline and browser-safe session handling
- `apps/api` owns token verification, policy enforcement, and normalized backend access
- `apps/ingest` owns privileged job execution boundaries
- `apps/ml` owns model/provider secret usage where applicable
- `apps/eval` owns safe dataset and benchmark access
- `apps/mcp` owns protocol-safe tool exposure

Any security boundary change must update:
- `docs/operations.md`
- `docs/architecture.md`
- relevant sprint planning file
- `testing/security/`

---

## 📏 App-level definition of done

An app-level change is incomplete unless:

- the app’s ownership boundary remains clear
- docs are updated if the app’s responsibilities changed
- tests cover the changed behavior
- telemetry covers the changed behavior
- config docs are updated if config changed
- contracts are updated if cross-surface data changed
- forbidden dependency rules are still respected

---

## 📜 Relationship to other root docs

This file works with:

- `docs/packages.md` for shared-package boundaries
- `docs/python.md` for Python module boundaries
- `docs/infra.md` for deployment topology
- `docs/architecture.md` for system-wide design
- `docs/operations.md` for current app maturity and runtime truth
- `docs/testing.md` for app-to-test-layer expectations

This file should not duplicate those documents. It should stay focused on **app ownership and boundaries**.
