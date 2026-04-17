# 📜 Infra

## 🧩 Purpose

This document defines the infrastructure, deployment topology, environment model, secret and config flow, runtime hosting strategy, and scale seams for the platform.

This file is the source of truth for:
- where each runtime is deployed
- how environments are separated
- how config and secrets flow
- which infrastructure responsibilities belong to which layer
- which scale seams are designed now but activated later
- how infrastructure choices stay provider-agnostic at the domain boundary

This file does **not** define:
- app ownership boundaries
- shared package boundaries
- Python shared-module boundaries
- sprint execution details

Those belong in:
- `docs/apps.md`
- `docs/packages.md`
- `docs/python.md`
- `docs/planning/MASTER.md`
- sprint planning files under `docs/planning/`

---

## 🧭 Infra maturity labels

Every infra capability described here must use one of these states only:

- **planned** — specified but not yet scaffolded
- **scaffolded** — files and baseline structure exist, but not yet usable
- **bootable** — deployable or runnable, but not yet integrated into real flows
- **integrated** — participates in real end-to-end flows
- **production-ready** — safe for live-user scope
- **hardened** — tested, observable, documented, and operationally mature

No other maturity labels should be used in infrastructure documentation.

---

## ☁️ Infrastructure thesis

The platform is intentionally overbuilt in structure and intentionally lean in initial runtime activation.

That means:
- core seams for future scale are designed in Sprint 1
- only the minimum operational runtime is activated first
- infrastructure choices must support live users early
- provider lock-in must be limited to adapter implementations, not domain contracts
- observability, security, and deployability are mandatory from the beginning

The initial hosting split is:

- Cloud Run for request-serving services and run-to-completion jobs
- Supabase for operational Postgres, Auth, and Storage
- GitHub Pages for public static documentation and marketing
- OpenTelemetry Collector, Prometheus, Grafana, Langfuse, and MLflow for telemetry, AI observability, and offline experiment evidence

---

## 🏗️ Topology summary

The infrastructure is split into four infrastructure planes:

### 🌐 Product plane
User-facing runtime surfaces:
- `apps/extension`
- `apps/web`

### ⚙️ Service plane
Request-serving and background execution surfaces:
- `apps/api`
- `apps/ingest`
- future `apps/ml`
- future `apps/eval`
- future `apps/mcp`

### 🗃️ Data plane
Operational and artifact persistence:
- operational relational store
- object/blob store
- graph store
- future cache and queue seams

### 👀 Observability plane
Telemetry collection, processing, storage, and dashboarding:
- OpenTelemetry SDKs
- OpenTelemetry Collector
- Prometheus
- Grafana
- Langfuse
- MLflow

---

## ☁️ Runtime hosting model

### ⚙️ Request-serving runtimes
These run as managed services:
- `apps/api`
- future online inference service if separated from API

### 📥 Job runtimes
These run as run-to-completion jobs:
- `apps/ingest`
- future backfills
- future batch embedding
- future batch graph extraction
- future eval and benchmark runs
- future offline training jobs if appropriate to the hosting constraints

### 🌐 Static publishing
Public documentation and marketing surfaces are published from root `docs/` via GitHub Pages configuration. No separate docs runtime is part of the Sprint 1 infrastructure baseline.

### 🪟 Browser runtime
This is distributed to the user runtime:
- `apps/extension`

### 🌐 Web runtime
This is hosted as a product-facing web application:
- `apps/web`

---

## 🗃️ Data-plane model

The data plane is deliberately split by responsibility.

### 🗃️ Operational store
Purpose:
- users
- workspaces
- cards
- decks
- annotations
- settings
- study events
- jobs
- operational metadata

Rules:
- this is the source of truth for operational product data
- user-facing relational data belongs here
- row-level access control is mandatory for user-scoped data

### 🪣 Artifact store
Purpose:
- raw captures
- screenshots
- uploaded images
- cleaned source artifacts
- transcripts
- dataset snapshots
- intermediate ML artifacts
- exported files

Rules:
- artifacts are addressable by environment and ownership context
- browser-safe access is always policy-scoped
- long-lived binary or document artifacts belong here, not in relational tables

### 🕸️ Graph store
Purpose:
- topic relationships
- prerequisite edges
- concept links
- graph-enhanced retrieval context
- recommendation enrichment

Rules:
- graph is secondary to operational truth
- graph never becomes the operational system of record
- graph features must degrade gracefully if the graph layer is unavailable

### 🧠 Future cache and queue seams
Purpose:
- response caching
- retrieval caching
- queue-based asynchronous fan-out
- backpressure handling
- rate smoothing

Rules:
- cache and queue are planned seams in Sprint 1
- activation is telemetry-driven, not speculative

---

## 🌍 Environment model

The environment model is fixed to:

- local
- staging
- production

### 💻 Local
Purpose:
- developer setup
- isolated integration testing
- local docs build
- local extension/web/API boot
- local collector and telemetry inspection where feasible

Rules:
- local setup must be reproducible from docs
- local config comes from `.env` derived from `.env.example`
- local data and credentials must never be committed

### 🧪 Staging
Purpose:
- integration verification
- pre-release runtime validation
- smoke and regression verification
- release candidate testing

Rules:
- staging must resemble production in topology as closely as practical
- staging is the first place deployment, auth, and telemetry changes are verified before production

### 🚀 Production
Purpose:
- live users
- stakeholder demos
- public docs
- real telemetry
- resume- and pitch-grade measurements

Rules:
- production config is secret-managed
- production changes require rollback readiness
- production health is measured by agreed SLI/SLO contracts

---

## 🔐 Secret and config model

Configuration and secrets are infrastructure concerns with strict boundaries.

### 🔐 Config classes

Every config value must be classified as one of:
- public runtime config
- internal non-secret config
- secret runtime config
- local-only developer config

### 🔐 Rules
- `.env.example` is committed
- `.env` is ignored
- browser surfaces only receive browser-safe config
- secret config is never bundled into browser or static outputs
- no runtime may read raw environment variables outside its config boundary
- every config key must be documented with scope and purpose

### 🔐 Browser-safe config
Allowed in:
- `apps/extension`
- `apps/web`
- public docs outputs only through GitHub Pages

Examples:
- public base URLs
- publishable auth keys
- public docs config
- non-secret telemetry endpoints if appropriate

### 🔐 Server-only config
Allowed in:
- `apps/api`
- `apps/ingest`
- future backend runtimes

Examples:
- privileged service credentials
- storage-service credentials
- private telemetry sink credentials
- internal service auth secrets

---

## 🔑 Credential-boundary rules

### 🪟 Browser surfaces
Must never receive:
- privileged database credentials
- privileged storage credentials
- admin/service-role credentials
- private observability sink secrets

### ⚙️ Backend surfaces
May receive:
- privileged credentials only when required
- storage or database elevated credentials behind adapters
- private telemetry sink credentials
- service-to-service auth secrets

### 📏 Rule
If a credential can mutate or bypass user-scoped policy, it is backend-only.

---

## 🌐 Network-boundary model

The network architecture is intentionally simple at first.

### 🌐 Public entrypoints
- web app
- docs site
- API public endpoint
- extension-to-API calls

### 🔒 Protected internal boundaries
- privileged adapter operations
- job execution
- future model-provider calls
- future queue or cache layers
- future graph and vector internal calls where not directly public

### 📏 Rules
- every public boundary must be documented
- every internal boundary must be observable
- no hidden service-to-service dependency is allowed
- all cross-boundary payloads must use documented contracts

---

## 📡 API gateway and CDN seams

These seams are designed now, even if not activated in Sprint 1.

### 📡 API gateway seam
Purpose:
- centralized auth enforcement
- rate limiting
- request shaping
- cross-service routing
- future public/private route split

Rules:
- do not couple application contracts to a specific gateway vendor
- gateway insertion must not require changing public API envelopes

### 🚀 CDN seam
Purpose:
- static docs acceleration
- future asset delivery
- future cached public content delivery
- future API-edge optimizations where appropriate

Rules:
- docs and asset URLs should not assume the absence of a CDN
- cache headers and asset naming should allow future CDN adoption

---

## 🗄️ Scaling seams

The platform is intentionally overbuilt in structure so these seams already exist.

### 🗄️ Read-replica seam
Purpose:
- read-heavy product scaling
- analytics or recommendation read offloading
- future dashboard/reporting split

Rule:
- operational truth remains on the primary write path
- replica usage must be isolated behind store abstractions

### 🧱 Sharding seam
Purpose:
- future partitioning for high user growth or hot data domains

Rule:
- do not shard early
- document shard triggers and partition candidates before activation
- ensure identifiers and ownership patterns do not block future partitioning

### 🧠 Cache seam
Purpose:
- hot-path response caching
- retrieval caching
- repeated workspace/session lookups
- cost and latency reduction

Rule:
- cache must always remain a derivative layer
- cache invalidation rules must be explicit before activation

### 🧵 Queue seam
Purpose:
- async work fan-out
- burst smoothing
- backpressure handling
- job decomposition
- future retraining and eval scheduling

Rule:
- queue activation requires telemetry proof of need
- queue boundaries must remain adapter-based

### 🧮 Search seam
Purpose:
- future dedicated search services or indexing acceleration

Rule:
- product contracts must remain generic enough to tolerate a future search backend split

---

## 🛡️ Reliability model

Infrastructure reliability is defined by explicit deploy, rollback, and recovery discipline.

### 🚦 Deploy rules
- each deployable runtime has a clear build artifact
- deployments must be reproducible from code and docs
- every deploy emits version metadata
- every deployable service must have health verification

### ↩️ Rollback rules
- every deployable runtime must have a rollback path
- rollback steps must be documented before runtime changes are considered done
- rollback must be environment-aware

### 💾 Backup and restore rules
- relational data backup policy must be documented
- artifact-store recovery expectations must be documented
- future graph backup and restore policy must be documented once graph is active
- restore drills become mandatory by Sprint 5

---

## 👀 Observability infrastructure

Infrastructure observability is mandatory, not optional.

### 👀 Components
- OpenTelemetry SDKs in runtime surfaces
- OpenTelemetry Collector for ingest, processing, and export
- Prometheus for metrics
- Grafana for dashboards
- Langfuse for AI and LLM observability

### 📏 Rules
- every deployable runtime emits telemetry
- collector configuration is versioned
- dashboards are treated as infrastructure artifacts, not ad hoc console work
- telemetry endpoints and credentials follow the same secret/config classification rules as other infra

### 📊 Baseline dashboard families
At minimum, infrastructure must support dashboards for:
- API health and latency
- job success and duration
- extension and web runtime success signals where available
- error rates
- deploy health
- AI trace completeness and cost signals
- future retrieval and ranking quality signals

---

## 🧪 CI/CD infrastructure model

### 🚦 Workflow location
Workflow definitions live in:
- `.github/workflows/`

Supporting scripts or templates may also live under:
- `infra/github/`

### 🚦 Required workflow categories
- CI
- docs publish
- code scanning
- dependency review
- future nightly evals or maintenance jobs as needed

### 📏 Rules
- CI and local commands must match
- required checks must block merge
- workflows are infrastructure artifacts and must be documented when changed
- branch-protection policy is part of infrastructure policy, not a repo afterthought

---

## 🧳 Artifact model

Artifacts are treated as first-class infrastructure outputs.

### 🧳 Artifact categories
- container images
- static docs builds
- token build outputs
- coverage artifacts
- eval outputs
- benchmark snapshots
- exportable user artifacts
- future model artifacts

### 📏 Rules
- every artifact category must have an owner
- every artifact category must have a retention or lifecycle expectation
- no artifact pipeline may depend on undocumented manual steps

---

## 🌐 GitHub Pages policy

GitHub Pages is used for:
- public technical docs
- architecture pages
- planning visibility if appropriate
- static marketing or project overview pages

GitHub Pages is **not** used for:
- authenticated product workflows
- private operational tools
- server-side business logic

### 📏 Rules
- docs output must be static-host compatible
- publication should be workflow-driven rather than manually pushed
- public docs must never depend on secret runtime config

---

## 🐳 Containerization policy

Containerization is part of the permanent infrastructure contract.

### 🐳 Rules
- every deployable backend runtime gets its own container definition
- service and job images are built separately
- runtime images must be reproducible
- local container usage must be documented if required for developer setup
- Dockerfiles belong under `infra/docker/`

### 📦 Expected image boundaries
- API image
- ingest image
- future ML image if split from API
- future eval image if independently deployable

---

## 🛣️ Future infrastructure expansion seams

These seams are intentionally designed now so later investor-backed growth does not require rewriting the repo shape.

### 🧠 Planned seams
- API gateway insertion
- CDN insertion
- cache layer insertion
- queue layer insertion
- read-replica routing
- shard-aware data partitioning
- model router separation
- premium/open-core operational split
- Rust sidecar or native helper insertion
- future browser-platform transition support

### 📏 Rule
A seam should exist in architecture and file structure before it is activated in runtime.

---

## 🔐 Open-core infrastructure rule

The repo is copyleft open core, so infrastructure must preserve a boundary between:
- the open core platform
- future premium, monetization, advertising, or investor-facing business surfaces

### 📏 Rules
- premium-specific infrastructure must be separable
- no premium-only operational dependency may become required for the core platform to function
- core infra decisions must not assume the existence of closed business modules
- trademark, governance, and deployment boundaries must remain consistent with this rule

---

## ✅ Infra-level definition of done

An infrastructure change is incomplete unless all of the following are true:

- deploy topology is documented
- secret/config implications are documented
- affected runtimes still respect boundary rules
- tests or smoke checks cover the changed behavior where appropriate
- telemetry still covers the changed boundary
- rollback implications are documented
- docs are updated if durable infrastructure truth changed

---

## 📜 Relationship to other root docs

This file works with:
- `docs/apps.md` for runtime ownership
- `docs/packages.md` for shared TS package boundaries
- `docs/python.md` for shared Python module boundaries
- `docs/testing.md` for CI and verification expectations
- `docs/architecture.md` for system-wide design and scale seams
- `docs/operations.md` for current operational truth

This file should stay focused on **infrastructure topology, environment rules, hosting strategy, and scale seams**.
