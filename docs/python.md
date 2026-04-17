# 📜 Python

## 🧩 Purpose

This document defines the ownership boundaries, import rules, shared-module responsibilities, and runtime expectations for everything under `python/`.

This file is the source of truth for:
- what belongs in Python shared modules
- what must remain in Python apps instead of shared modules
- how Python modules relate to the TS apps and packages
- which dependency directions are allowed
- how ML, data, retrieval, graph, training, and evaluation concerns are split

This file does **not** define:
- app runtime ownership for `apps/api`, `apps/ingest`, `apps/ml`, `apps/eval`, or `apps/mcp`
- deployment topology
- sprint execution details

Those belong in:
- `docs/apps.md`
- `docs/infra.md`
- `docs/planning/MASTER.md`
- sprint planning files under `docs/planning/`

---

## 🧭 Python maturity labels

Every Python module area described here must use one of these states only:

- **planned** — specified but not yet scaffolded
- **scaffolded** — folder and baseline structure exist, but not yet meaningfully used
- **bootable** — importable and usable, but integration is minimal
- **integrated** — used in real application or job flows
- **production-ready** — safe for live-user scope
- **hardened** — tested, documented, observable, and operationally mature

No other maturity labels should be used in Python module documentation.

---

## 📦 Python inventory

The `python/` folder contains these shared module boundaries:

- `python/common`
- `python/data`
- `python/retrieval`
- `python/graph`
- `python/models`
- `python/training`
- `python/evaluation`

These are shared Python modules, not deployable apps. Deployable runtimes live under `apps/`. The rule is:

- `apps/*` owns runtime entrypoints
- `python/*` owns reusable Python domain and platform logic

---

## 🏗️ Python role in the platform

Python is the primary language for:

- backend intelligence
- ingestion and data cleaning
- retrieval orchestration
- graph extraction and graph-aware workflows
- NLP and ML feature logic
- model training and evaluation
- MCP tool execution
- batch and job-oriented platform workflows

TypeScript remains primary for:
- browser runtime
- web runtime
- shared frontend contracts and UI primitives

This split is intentional. Python owns the intelligence and data platform. TypeScript owns the product-facing shells and shared frontend infrastructure.

---

## 🔄 Relationship between `apps/` and `python/`

The Python architecture is split into two layers:

### ⚙️ Runtime layer
These are deployable or executable surfaces under `apps/`:
- `apps/api`
- `apps/ingest`
- `apps/ml`
- `apps/eval`
- `apps/mcp`

### 🧱 Shared module layer
These are reusable Python modules under `python/`:
- `python/common`
- `python/data`
- `python/retrieval`
- `python/graph`
- `python/models`
- `python/training`
- `python/evaluation`

### 📏 Rule
`apps/*` may import from `python/*`, but `python/*` may not import from `apps/*`.

This keeps runtime entrypoints thin and reusable logic centralized.

---

## 🧱 Shared Python rules

These rules apply to every module under `python/`.

### ✅ Required rules
- one coherent responsibility per top-level Python module
- semantic names only
- narrow public interfaces
- explicit import boundaries
- reusable logic belongs here, not in app entrypoints
- typed inputs and outputs wherever practical
- all provider integrations happen through adapter-aware boundaries

### 🚫 Forbidden rules
- no HTTP route ownership in `python/*`
- no app-entrypoint concerns in `python/*`
- no direct browser/runtime UI logic
- no hidden provider coupling in public domain contracts
- no dumping-ground folders
- no business logic embedded only in job entrypoints if it is reusable

---

## 🧩 `python/common`

### 🧩 Purpose
`python/common` contains cross-cutting Python foundations shared by multiple Python runtimes and modules.

### 🎯 Responsibilities
- shared config primitives
- shared exceptions and error normalization
- shared telemetry helpers
- shared typing and schema helpers
- shared utility functions that are truly cross-domain
- shared adapter base interfaces or protocol helpers
- shared retry, timeout, or idempotency primitives when generic enough

### 🚫 Non-responsibilities
- domain-specific retrieval logic
- graph-specific logic
- model-specific logic
- training-specific logic
- route or runtime entrypoint logic

### ✅ Allowed consumers
- `apps/api`
- `apps/ingest`
- `apps/ml`
- `apps/eval`
- `apps/mcp`
- all other `python/*` modules

### ⛔ Forbidden contents
- product feature logic
- provider-specific business logic in public interfaces
- request route definitions
- job-main orchestration code
- domain workflows that belong in a more specific module

### 📏 Rules
- keep `common` small
- every addition must justify true cross-domain reuse
- if logic is specific to one domain, it belongs in that domain module instead

### 📚 Current target maturity
Sprint 1 target: **bootable**  
Sprint 2 target: **integrated**  
Sprint 5 target: **hardened**

---

## 📥 `python/data`

### 🧩 Purpose
`python/data` contains data-ingestion, cleaning, normalization, and feature-preparation logic that is reusable across ingestion, training, evaluation, and retrieval workflows.

### 🎯 Responsibilities
- raw source normalization
- HTML/text/markdown cleaning
- deduplication
- metadata extraction
- source versioning helpers
- chunk preparation support
- feature preprocessing support
- dataset shaping for training and evaluation

### 🚫 Non-responsibilities
- request routing
- graph traversal logic
- final retrieval orchestration
- model-serving endpoints
- app-specific UI concerns

### ✅ Allowed consumers
- `apps/ingest`
- `apps/api` only for thin delegated preprocessing if truly needed
- `apps/ml`
- `apps/eval`
- `python/training`
- `python/evaluation`
- `python/retrieval`

### ⛔ Forbidden contents
- provider-specific scraper runtime boot code
- route or job entrypoints
- untyped ad hoc transformation chains hidden in scripts
- frontend-specific formatting behavior

### 📏 Rules
- all cleaning steps must be deterministic where possible
- normalization behavior must be testable
- transformations must be documented if they materially affect model or retrieval quality
- reusable cleaning logic belongs here, not inside one-off jobs

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 📎 `python/retrieval`

### 🧩 Purpose
`python/retrieval` contains reusable retrieval logic for source lookup, citation packing, ranking integration, and grounded-answer assembly support.

### 🎯 Responsibilities
- retrieval pipeline composition
- chunk selection helpers
- citation-pack generation helpers
- hybrid retrieval orchestration
- retrieval-side filtering and ranking interfaces
- future query rewriting or expansion helpers
- future source-grounding support for assistant flows

### 🚫 Non-responsibilities
- HTTP route ownership
- graph store implementation details that belong in adapters
- UI-specific answer rendering
- direct prompt text storage
- end-user session handling

### ✅ Allowed consumers
- `apps/api`
- `apps/mcp`
- `apps/eval`
- `apps/ml`
- `python/evaluation`

### ⛔ Forbidden contents
- app route code
- provider-specific vector database logic in public interfaces
- hardcoded vendor assumptions in retrieval contracts
- direct frontend rendering formats

### 📏 Rules
- retrieval must stay contract-driven
- citation support is mandatory for user-facing assistant flows
- retrieval logic must be observable and evaluation-friendly
- ranking hooks must remain separable from base retrieval logic

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🕸️ `python/graph`

### 🧩 Purpose
`python/graph` contains reusable graph-oriented logic for relationship extraction, topic linking, prerequisite mapping, and graph-aware enrichment.

### 🎯 Responsibilities
- entity and relation extraction support
- prerequisite-link construction helpers
- topic graph shaping
- graph query composition helpers
- graph-enrichment logic for retrieval and recommendations
- GraphRAG-related reusable logic that is not runtime-specific

### 🚫 Non-responsibilities
- graph database provider bootstrapping in public interfaces
- HTTP route ownership
- web or extension state concerns
- direct prompt invocation ownership
- general vector retrieval logic that belongs in `python/retrieval`

### ✅ Allowed consumers
- `apps/api`
- `apps/ingest`
- `apps/eval`
- `apps/ml`
- `python/retrieval`
- `python/evaluation`

### ⛔ Forbidden contents
- provider-specific coupling in public contracts
- app entrypoint logic
- broad “knowledge” dumping grounds that mix unrelated logic

### 📏 Rules
- graph logic must stay secondary to operational truth in Postgres
- graph functions must not assume they are the system of record
- graph enrichment must remain optional at the contract level where practical
- GraphRAG support must remain testable independently of request routing

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🔬 `python/models`

### 🧩 Purpose
`python/models` contains reusable ML and NLP model-facing logic that supports inference-time behavior without owning runtime entrypoints.

### 🎯 Responsibilities
- model-loading helpers
- inference wrappers
- feature-to-model application helpers
- output postprocessing
- ranking and scoring support
- lightweight classifier and predictor support
- future compact tutoring-model support

### 🚫 Non-responsibilities
- training job orchestration
- experiment registry ownership
- request route ownership
- provider-specific secrets handling in public module contracts
- frontend-specific UX behavior

### ✅ Allowed consumers
- `apps/ml`
- `apps/api`
- `apps/eval`
- `python/evaluation`

### ⛔ Forbidden contents
- job entrypoint code
- request handler definitions
- prompt libraries
- dataset-construction pipelines that belong in `python/data` or `python/training`

### 📏 Rules
- model logic must remain observable
- model outputs must remain typed and versionable
- provider/model-specific integration belongs at the adapter edge
- online inference helpers must be measurable by latency, error rate, and cost where applicable

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🧪 `python/training`

### 🧩 Purpose
`python/training` contains reusable logic for training datasets, training workflows, feature pipelines, and model-fitting orchestration that should not live inside runtime entrypoints.

### 🎯 Responsibilities
- dataset assembly helpers
- train/validation/test split helpers
- feature-pipeline logic
- training orchestration utilities
- artifact-shaping helpers
- training metrics collection helpers
- model version metadata preparation

### 🚫 Non-responsibilities
- online inference
- request-serving logic
- static documentation
- product runtime UI behavior

### ✅ Allowed consumers
- `apps/ml`
- `apps/eval`
- future batch training runtimes
- `python/evaluation`

### ⛔ Forbidden contents
- app-main boot logic
- runtime-specific deployment code
- hidden experiment state not represented in docs or tracking tools
- provider-specific coupling in public training interfaces

### 📏 Rules
- training logic must support reproducibility
- dataset shaping must be testable
- output artifacts must be traceable
- training helpers must not silently mutate source datasets without documentation

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 📏 `python/evaluation`

### 🧩 Purpose
`python/evaluation` contains reusable evaluation and regression logic for retrieval, ranking, prompts, answers, and model performance.

### 🎯 Responsibilities
- eval dataset helpers
- benchmark logic
- scoring helpers
- regression gates
- comparison utilities
- latency and cost evaluation helpers
- answer and retrieval quality evaluation support

### 🚫 Non-responsibilities
- online request serving
- UI rendering
- direct product feature routing
- hidden benchmark execution outside documented evaluation paths

### ✅ Allowed consumers
- `apps/eval`
- `apps/api` only for narrowly scoped validation hooks where needed
- `apps/ml`
- `apps/mcp`
- `python/retrieval`
- `python/models`

### ⛔ Forbidden contents
- request route ownership
- random one-off notebook logic treated as source of truth
- provider-specific benchmark assumptions in public contracts

### 📏 Rules
- eval logic must be reproducible
- evaluation outputs must be machine-readable
- regression criteria must be explicit
- shared evaluation logic belongs here, while test harness orchestration lives under `testing/evals/` and evaluation runtimes

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🔄 Allowed dependency directions

This section defines the allowed dependency flow across `python/`.

### ✅ Allowed directions
- `python/data` → `python/common`
- `python/retrieval` → `python/common`
- `python/retrieval` → `python/data` when preprocessing support is required
- `python/graph` → `python/common`
- `python/graph` → `python/data` when extraction preprocessing support is required
- `python/models` → `python/common`
- `python/training` → `python/common`
- `python/training` → `python/data`
- `python/training` → `python/models`
- `python/evaluation` → `python/common`
- `python/evaluation` → `python/data`
- `python/evaluation` → `python/retrieval`
- `python/evaluation` → `python/models`
- `python/evaluation` → `python/graph` when graph-specific scoring is needed

### 🚫 Forbidden directions
- `python/common` → any domain-specific Python module
- any `python/*` module → `apps/*`
- any `python/*` module → frontend packages
- any domain module importing unrelated sibling modules without a clear reason
- cyclic dependencies between domain modules

### 📏 Dependency rule of thumb
Shared Python modules may depend “down” into more general shared foundations, but never “up” into runtime entrypoints or sideways into unrelated concerns without a documented reason.

---

## 🧠 Type and schema ownership

### ✅ Python-side ownership
- shared Python config primitives belong in `python/common`
- reusable preprocessing schemas belong in `python/data`
- retrieval-side internal schemas belong in `python/retrieval`
- graph-side internal schemas belong in `python/graph`
- model-side internal schemas belong in `python/models`
- training-side artifacts and metadata schemas belong in `python/training`
- eval-side scoring and result schemas belong in `python/evaluation`

### 🔗 Relationship to TS contracts
`packages/contracts` owns shared serializable cross-surface contracts for TS-facing boundaries. Python modules may mirror those shapes where necessary, but Python internal schemas must not drift into becoming a second undocumented public contract system.

### 🚫 Forbidden duplication
- no duplicate public API envelopes defined ad hoc across multiple Python apps
- no hidden schema copies in job entrypoints
- no provider response shapes leaking into domain-level public contracts

---

## ⚙️ Config ownership rules

TypeScript and Python both need config discipline, but ownership is split.

### ⚙️ TS side
- `packages/config` owns TypeScript runtime config loading

### 🐍 Python side
- Python mirrored config primitives belong under `python/common`
- Python apps consume the Python config layer, not raw environment variables

### 📏 Rules
- no Python app reads raw environment variables directly outside its config boundary
- config keys must stay documented in `.env.example`
- if a Python config shape changes, update:
  - `docs/operations.md`
  - relevant sprint plan
  - tests
  - local setup docs if developer workflow changed

---

## 🤖 Python and AI/ML ownership rules

Python is the primary owner of:
- ingestion and cleaning logic
- retrieval orchestration
- graph extraction
- recommendation logic
- NLP and classical ML logic
- model training and evaluation
- AI workflow orchestration
- MCP tool execution

### 🚫 Not owned by Python
- browser-runtime interaction logic
- frontend visual state
- UI primitives
- token system

### 📏 Rule
If the logic is primarily about knowledge processing, model behavior, retrieval, graph logic, evaluation, or batch data work, it belongs in Python unless there is a compelling documented reason otherwise.

---

## ✅ Testing expectations by Python module

### ✅ `python/common`
- unit tests
- config tests
- shared utility tests

### ✅ `python/data`
- unit tests
- integration tests for cleaning and transformation chains
- regression tests for deterministic normalization behavior

### ✅ `python/retrieval`
- unit tests
- integration tests
- eval-linked tests when retrieval behavior changes

### ✅ `python/graph`
- unit tests
- integration tests
- graph-enrichment regression tests where appropriate

### ✅ `python/models`
- unit tests
- inference smoke tests
- latency or output-shape checks where appropriate

### ✅ `python/training`
- unit tests
- dataset shaping tests
- pipeline tests where appropriate

### ✅ `python/evaluation`
- unit tests
- benchmark logic tests
- regression tests
- alignment with `testing/evals/`

### 📏 Global rule
A Python shared-module change is incomplete unless the relevant root test layers and evaluation layers are updated.

---

## 👀 Observability implications

Python shared modules do not always emit telemetry directly, but they define the operations that runtime apps must instrument.

### 👀 Required implications
- reusable domain operations must expose clear instrumentation boundaries
- long-running steps must be span-friendly
- model and retrieval flows must remain traceable
- evaluation logic must remain measurable
- job and API runtimes must be able to wrap shared Python operations with spans and logs without invasive rewrites

If a Python shared module becomes difficult to instrument cleanly, its structure is wrong.

---

## 🔐 Security rules

Python shared modules must preserve provider optionality and secure credential boundaries.

### 🔐 Rules
- no secret values committed in Python modules
- no provider-specific names in public domain interfaces
- no service credential assumptions inside reusable domain modules unless passed through a documented adapter boundary
- no hidden privileged behavior inside “helper” utilities
- security-sensitive transformations must be testable

Any Python module change that affects identity, storage, model-provider access, or graph/vector backends must trigger:
- `testing/security/` updates where relevant
- docs updates
- review of adapter boundaries

---

## 📏 Python-level definition of done

A Python shared-module change is incomplete unless:

- the module responsibility remains clear
- import boundaries are still respected
- tests cover the changed behavior
- docs are updated if durable technical truth changed
- observability implications are still workable
- no provider-specific coupling leaked into public domain contracts
- no runtime-entrypoint logic was incorrectly moved into shared modules

---

## 📜 Relationship to other root docs

This file works with:

- `docs/apps.md` for runtime ownership
- `docs/packages.md` for TS shared-package boundaries
- `docs/infra.md` for deployment topology
- `docs/testing.md` for test-layer expectations
- `docs/architecture.md` for system-wide technical design
- `docs/operations.md` for current maturity truth

This file should stay focused on **shared Python module ownership and dependency rules**.
