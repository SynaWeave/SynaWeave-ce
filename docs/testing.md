# 📜 Testing

## 🧩 Purpose

This document defines the test taxonomy, quality-gate rules, coverage expectations, evaluation boundaries, and verification responsibilities for the entire platform.

This file is the source of truth for:

* what kinds of tests exist
* where each kind of test lives
* which changes require which tests
* how AI, retrieval, and model evals fit into the quality system
* which tools are approved for each layer
* what “fully tested” means for a deliverable

This file does **not** define:

* sprint sequencing
* app ownership boundaries
* deployment topology
* root architecture choices

Those belong in:

* `docs/planning/MASTER.md`
* `docs/apps.md`
* `docs/infra.md`
* `docs/architecture.md`

Use `docs/templates/tests/verification-plan.md` when a reusable verification packet is needed outside inline planning sections.

## 🧭 Testing thesis

Testing is part of the product, not a cleanup step.

Every deliverable in this repo must be:

* functionally verified
* contract verified
* user-path verified
* security checked where relevant
* accessibility checked where relevant
* performance checked where relevant
* AI-evaluated where relevant

No deliverable may close with “tests later” debt.

The platform’s baseline tools are locked as:

* **Vitest** for unit and component-adjacent execution
* **Testing Library** for React behavior tests
* **Playwright** for UI, browser, and end-to-end verification
* **Playwright + `@axe-core/playwright`** for automated accessibility checks
* **schema-driven contract tests** for public APIs and serialized interfaces
* **Langfuse-backed online evaluation discipline** for AI-facing behaviors when hosted infra is reachable
* **MLflow-backed offline experiment and evaluation discipline** for repeatable offline proof when hosted infra is reachable
* **harness-backed repo-local eval artifacts** for bounded proof until those hosted systems are confirmed

## 🔄 Verification mapping

Changes in this repository must update the matching test or verification layers.

* planning, ADR, governance, workflow, and hook changes require repo-control tests under `testing/unit/`
* TypeScript code changes require the root TypeScript lint and typecheck gates plus the relevant test layers
* Python code changes require the root Python lint and typecheck gates plus the relevant test layers
* public contract changes require `testing/contract/`
* UI and browser-surface changes require the relevant `testing/component/`, `testing/ui/`, `testing/e2e/`, or `testing/accessibility/` coverage
* governed Python, TypeScript, JavaScript, workflow YAML, TOML, shell hook, dotenv example, and CSS files require canonical TL;DR header verification
* repo-control and language-tooling changes must preserve the no-suppressions verification path for Python, TypeScript, and root config surfaces
* comment-bearing code and config files must preserve the comment-heavy commentary verification path and manual review expectations for HTML notes
* ship-facing HTML changes must preserve source-comment safety and stripped production artifact verification
* secret scanning must preserve the layered split of Betterleaks for fast gates TruffleHog for deep CI and the custom verifier for repo-specific policy checks

## 📦 Root testing taxonomy

All top-level testing folders are mandatory.

```text
testing/
  unit/
  component/
  integration/
  contract/
  ui/
  e2e/
  security/
  performance/
  accessibility/
  evals/
```

Each folder has a distinct role. If a test does not clearly belong to one of these folders, the test design is probably wrong.

## ✅ `testing/unit`

### 🧩 Purpose

Fast, isolated verification of pure logic and small behavior units.

### 🎯 Responsibilities

* pure functions
* utility helpers
* config validation
* token transforms
* deterministic scoring logic
* adapter stub behavior
* serialization helpers
* error normalization

### 🚫 Non-responsibilities

* DOM behavior
* browser runtime behavior
* multi-service orchestration
* real network behavior
* end-to-end user journeys

### 🛠️ Approved tools

* Vitest
* language-native assertion tooling where appropriate

### 📏 Rules

* unit tests must be fast
* unit tests must be deterministic
* unit tests must not depend on external services
* unit tests must isolate logic from framework or runtime complexity whenever practical

## 🧩 `testing/component`

### 🧩 Purpose

Verification of UI primitives and feature-level UI pieces in isolation from full browser journeys.

### 🎯 Responsibilities

* render behavior
* prop-driven state changes
* accessibility semantics at the component level
* token-consumption behavior
* focus and keyboard behavior for shared primitives
* controlled and uncontrolled input behavior

### 🚫 Non-responsibilities

* full routing flows
* real browser extension flows
* full auth journeys
* backend integration behavior

### 🛠️ Approved tools

* Vitest
* Testing Library

### 📏 Rules

* component tests must assert user-observable behavior
* component tests must not test framework internals
* shared UI primitives must be covered here before relying only on UI or e2e tests
* token or primitive changes must update this layer

## 🔗 `testing/integration`

### 🧩 Purpose

Verification that multiple internal pieces work together correctly without requiring a full end-to-end user journey.

### 🎯 Responsibilities

* service and adapter interaction
* config and runtime interaction
* preprocessing pipeline segments
* retrieval pipeline segments
* graph-enrichment integration slices
* storage and database interaction slices in controlled environments
* app-to-shared-package integration checks

### 🚫 Non-responsibilities

* public API contract ownership
* full browser-based journeys
* full production load testing

### 🛠️ Approved tools

* language-native test runners
* controlled runtime fixtures
* local test databases or mocks as appropriate
* Playwright `APIRequestContext` only if the scenario genuinely benefits from it

### 📏 Rules

* integration tests should cover boundary interaction, not every internal branch
* integration tests must be narrower than e2e
* integration tests must remain reproducible
* when a reusable domain workflow spans multiple modules, it should usually have at least one integration test

## 🧾 `testing/contract`

### 🧩 Purpose

Verification that public contracts, serialized payloads, and cross-surface interfaces remain stable and correct.

### 🎯 Responsibilities

* API request and response shapes
* message bus payloads
* envelope structure
* adapter port behavior expectations
* event schemas
* config schema validation where relevant
* compatibility across extension, web, and backend surfaces

### 🚫 Non-responsibilities

* full UI rendering
* performance benchmarking
* freeform exploratory testing

### 🛠️ Approved tools

* schema-driven contract tests
* property-based checks where useful
* explicit contract fixtures
* Schemathesis or equivalent spec-driven contract runner for public APIs

### 📏 Rules

* any public API change must update this layer
* any adapter contract change must update this layer
* any extension runtime message contract change must update this layer
* no undocumented public shape is allowed to exist only in app code
* provider-specific response shapes must not leak past the contract boundary

## 🌐 `testing/ui`

### 🧩 Purpose

Verification of user-visible application behavior in browser contexts without necessarily testing the entire full-stack journey.

### 🎯 Responsibilities

* route rendering
* visible shell behavior
* navigation behavior
* interaction-state changes
* panel and modal behavior
* layout-critical regressions
* view-level accessibility smoke checks where appropriate

### 🚫 Non-responsibilities

* full multi-surface end-to-end orchestration
* long-running job validation
* low-level component semantics already covered in component tests

### 🛠️ Approved tools

* Playwright

### 📏 Rules

* UI tests should focus on visible behavior
* UI tests must use resilient selectors and user-facing semantics
* UI tests should not overfit to implementation details
* route and shell regressions belong here before they become full e2e failures

## 🧭 `testing/e2e`

### 🧩 Purpose

Verification of real user journeys that cross multiple boundaries.

### 🎯 Responsibilities

* sign-in flow
* extension install/load flow
* side-panel open flow
* web + API authenticated flow
* workspace bootstrap flow
* source capture to backend acknowledgment flow
* future study and assistant journeys

### 🚫 Non-responsibilities

* exhaustive branch coverage
* tiny UI details already covered elsewhere
* deeply isolated logic tests

### 🛠️ Approved tools

* Playwright
* Chromium-based extension automation support

### 📏 Rules

* e2e tests must cover only critical user journeys
* e2e tests must remain small in number but high in value
* flaky e2e tests are treated as quality bugs
* extension-critical flows must be represented here, not only in manual testing
* when Chromium hides browser-owned extension chrome from Playwright, the test must state the exact proof limit instead of overstating container coverage

## 🔐 `testing/security`

### 🧩 Purpose

Verification of security-sensitive behavior, secret boundaries, auth boundaries, and abuse-prone flows.

### 🎯 Responsibilities

* auth and session boundary checks
* token handling checks
* config and secret-boundary checks
* RLS or policy smoke verification
* privileged action boundary checks
* log redaction checks
* adapter misuse checks
* exposed-secret regression checks

### 🚫 Non-responsibilities

* full-scale penetration testing
* manual red-team exercises
* long-form compliance audits

### 🛠️ Approved tools

* language-native test runners
* Playwright for auth-boundary flows where needed
* repo security tooling outputs as required checks
* targeted smoke scripts

### 📏 Rules

* every auth change must update this layer
* every secret-boundary change must update this layer
* every permission or policy change must update this layer
* no credential may appear in logs, test artifacts, or browser bundles
* security failures block merge

### 🔒 Repository security integrations

This layer works alongside:

* GitHub CodeQL
* dependency review
* secret scanning
* push protection when available

## ⚡ `testing/performance`

### 🧩 Purpose

Verification of performance baselines, latency regressions, and timing-sensitive behavior at a smoke-test level.

### 🎯 Responsibilities

* API latency smoke checks
* extension panel document and workspace-entry timing within the bounded local proof
* web shell render timing
* bootstrap action latency
* ingest job duration checks
* build-duration checks where tracked in CI
* future retrieval and generation latency checks

### 🚫 Non-responsibilities

* full production load testing
* formal capacity planning
* synthetic benchmarking with no product relevance

### 🛠️ Approved tools

* Playwright timing assertions where appropriate
* lightweight benchmark and timing scripts
* CI timing artifacts
* telemetry-derived baselines from Prometheus, Grafana, or runtime metrics
* versioned repo-local proof artifacts under `testing/performance/` when hosted telemetry is not yet available
* Playwright output artifacts for browser-side web-shell and extension timing evidence

### 📏 Rules

* Sprint 1 performance checks are smoke baselines, not hard SLO gates
* later sprints may tighten thresholds as baselines mature
* performance checks must measure product-relevant operations
* regression thresholds must be documented when introduced

## ♿ `testing/accessibility`

### 🧩 Purpose

Verification of accessibility expectations through automated checks and stable accessibility-oriented assertions.

### 🎯 Responsibilities

* WCAG A and AA automated scans
* keyboard-accessibility smoke checks
* focus-state coverage where practical
* extension side-panel accessibility checks
* web-shell accessibility checks
* primitive-level accessibility regressions when promoted from component tests

### 🚫 Non-responsibilities

* full manual accessibility audit replacement
* every possible assistive-technology scenario
* policy-only discussion with no executable checks

### 🛠️ Approved tools

* Playwright
* `@axe-core/playwright`

### 📏 Rules

* web shell must have automated accessibility checks
* extension side panel must have automated accessibility checks
* temporary accessibility exceptions must be documented with owner and expiry
* accessibility regressions block merge unless explicitly approved and documented

## 🤖 `testing/evals`

### 🧩 Purpose

Verification of AI-, retrieval-, ranking-, and model-related behavior through repeatable evaluation rather than ad hoc judgment.

### 🎯 Responsibilities

* prompt smoke evals
* retrieval evals
* answer-quality evals
* citation-grounding evals
* ranking evals
* clustering-quality evals where applicable
* cost and latency evals
* regression datasets and benchmark outputs

### 🚫 Non-responsibilities

* hidden benchmark notebooks as source of truth
* one-off manual grading with no artifact
* provider-specific experimentation that bypasses documented evaluation pathways

### 🛠️ Approved tools

* Langfuse evaluation workflows when reachable
* reproducible test harnesses
* dataset fixtures
* typed evaluation results

### 📏 Rules

* any prompt change must consider eval impact
* any retrieval change must update relevant evals
* any ranking or model-scoring change must update relevant evals
* evals must be versionable and reproducible
* benchmark datasets must have stable names and ownership
* no AI feature is considered complete without appropriate eval coverage
* repo-local proof must be clearly labeled as local when hosted Langfuse or MLflow confirmation is still pending

## 🛠️ Approved testing tools by layer

### ✅ Core mapping

* `testing/unit/` → Vitest or language-native equivalent
* `testing/component/` → Vitest + Testing Library
* `testing/integration/` → language-native runners and controlled fixtures
* `testing/contract/` → schema-driven contract tooling
* `testing/ui/` → Playwright
* `testing/e2e/` → Playwright
* `testing/security/` → targeted scripts, runtime tests, and repo security integrations
* `testing/performance/` → targeted timing scripts and telemetry-assisted smoke checks
* `testing/accessibility/` → Playwright + `@axe-core/playwright`
* `testing/evals/` → Langfuse-backed when reachable, MLflow-backed for local offline proof, and harness-backed eval workflows

### 🚫 Tooling rule

No new testing framework should be introduced without:

* documented reason
* comparison to the locked default
* ADR update if the change is architectural

## 📏 Coverage expectations

Coverage is defined by **owned scope**, not by vanity percentages alone.

### ✅ General rule

Every deliverable must leave the code it introduces or materially changes fully covered at the appropriate layers.

### 📦 Package and module coverage expectations

* shared contracts require contract tests
* shared tokens require unit tests and downstream verification where affected
* UI primitives require component tests and accessibility implications where relevant
* Python shared logic requires unit and integration coverage where appropriate
* runtime-entrypoint changes require smoke or e2e coverage where relevant

### 🌐 User-path coverage expectations

Any new user-visible capability must usually have:

* at least one component or UI-level assertion
* at least one end-to-end or integrated user-path verification if it crosses boundaries

### 🤖 AI-path coverage expectations

Any AI-related capability must usually have:

* runtime tests
* contract coverage if serialized
* at least one evaluation artifact in `testing/evals/`

## 🚦 Quality-gate rules

Testing is part of merge policy.

### 🚦 Required merge-gate categories

* lint
* typecheck
* unit tests
* component tests
* contract tests
* UI smoke
* e2e smoke
* accessibility checks
* performance smoke
* docs build
* token build
* security scanning and dependency review
* evals where AI-related changes require them

### 📏 Rules

* required checks must block merge
* flaky tests are treated as defects
* tests may not be silently skipped to make a PR merge
* if a check is intentionally relaxed, the change must be documented in sprint planning or ADRs

## 🔄 Change-to-test mapping

This section defines what must be updated when specific types of changes occur.

### ✏️ UI primitive change

Must update:

* `testing/component/`
* `testing/accessibility/`
* `testing/ui/` if visible shell behavior changes

### 🔗 Public API change

Must update:

* `testing/contract/`
* relevant integration tests
* relevant e2e smoke if user-visible

### 🧱 Adapter contract change

Must update:

* `testing/contract/`
* relevant unit tests
* relevant integration tests
* `testing/security/` if auth, storage, or secrets are involved

### 🔐 Auth or permission change

Must update:

* `testing/security/`
* relevant e2e auth flow
* relevant UI or integration tests

### 📥 Ingestion or preprocessing change

Must update:

* `testing/unit/`
* `testing/integration/`
* `testing/evals/` if retrieval or model quality can be affected

### 📎 Retrieval change

Must update:

* `testing/integration/`
* `testing/evals/`
* any relevant latency or performance smoke

### 📈 Ranking or model-scoring change

Must update:

* `testing/unit/`
* `testing/integration/`
* `testing/evals/`

### 🧠 Prompt change

Must update:

* `testing/evals/`
* any relevant integration tests
* Langfuse trace and eval references if naming or behavior changed and the hosted adapter path is in scope

### ⚙️ Config or secret-boundary change

Must update:

* `testing/unit/`
* `testing/security/`
* `.env.example`
* setup and operations docs if developer workflow changed

## 🧪 Evaluation policy

Evaluations are part of the testing system, not a separate optional workflow.

### 🧪 Eval requirements

* datasets must be named
* datasets must be owned
* eval cases must be reproducible
* results must be machine-readable
* regression failures must be explainable
* changes to prompts, retrieval, ranking, or model behavior must reference relevant eval suites

### 📏 Minimum Sprint 1 eval expectations

Sprint 1 must have:

* one synthetic eval dataset
* one synthetic eval run
* one stable naming convention
* one location for future prompt, retrieval, answer, and ranking eval expansion

Current Sprint 1 repo-local proof path:

* fixture: `testing/evals/fixtures/runtime-digest-density.v1.json`
* eval artifact: `testing/evals/artifacts/runtime-digest-density.local-proof.v1.json`
* Langfuse artifact: `testing/evals/artifacts/runtime-digest-density.langfuse-local-proof.v1.json`
* performance artifact: `testing/performance/runtime-baseline.local-proof.v1.json`
* regeneration command: `python3 -m python.evaluation.runtime_eval`
* Langfuse proof command: `python3 -m python.evaluation.langfuse_local_proof`
* MLflow verification probe: `python3 -m python.evaluation.verify_mlflow_run`

These artifacts now prove repo-local runtime evaluation, telemetry-derived performance, one repo-local MLflow offline run, and one bounded self-hosted local Langfuse trace-plus-score path. They do **not** by themselves prove hosted Langfuse operations, hosted or team-shared MLflow durability, or GitHub-hosted merge controls.

## 📊 Test artifacts and retention

Testing produces first-class artifacts.

### 📊 Artifact examples

* coverage reports
* accessibility failure reports
* Playwright traces, screenshots, and videos where configured
* contract-failure reports
* performance timing outputs
* eval results
* benchmark summaries

### 📏 Rules

* artifacts must be attachable in CI where useful
* failures should preserve enough evidence to debug without rerunning blindly
* artifact retention should be documented if CI platform defaults are insufficient

## 👀 Relationship to observability

Testing and observability are linked but not identical.

### 👀 Testing proves

* expected behavior under controlled conditions

### 👀 Observability shows

* actual runtime behavior in real execution

### 📏 Rule

If a workflow is important enough to observe in production, it is usually important enough to test before production.

This is especially true for:

* auth
* workspace bootstrap
* retrieval
* assistant responses
* model scoring
* job execution

## 🔐 Security and privacy testing rule

No test may:

* commit secrets
* rely on real privileged credentials in repo code
* leak sensitive runtime values into logs or artifacts
* bypass documented secret-handling rules

Security-sensitive fixtures must be synthetic or safely provisioned.

## ✅ Testing-level definition of done

A change is not fully tested unless all of the following are true:

* the correct test layers were updated
* tests pass locally and in CI where applicable
* docs are updated if quality expectations changed
* evals are updated when AI-facing behavior changed
* accessibility and security implications were addressed where relevant
* no known flaky or broken tests were knowingly left behind without documented ownership

## 📜 Relationship to other root docs

This file works with:

* `docs/apps.md` for runtime-boundary ownership
* `docs/packages.md` for shared-package coverage implications
* `docs/python.md` for shared Python module coverage implications
* `docs/infra.md` for CI and deployment verification context
* `docs/architecture.md` for system-wide quality boundaries
* `docs/operations.md` for current quality maturity
* sprint planning files for deliverable-specific verification gates

This file should stay focused on **test taxonomy, quality gates, and evaluation rules**.
