# 📜 Operations

## 🧩 Purpose

This document is the source of truth for the **current operational reality** of the repository.

This file defines:

* what exists now
* what is only scaffolded
* what is bootable
* what is integrated
* what is production-ready
* what operational gaps still exist

If this file and the README ever disagree, this file wins for present-state operational truth.

This file does **not** define:

* target architecture
* long-term design rationale
* sprint execution details
* package or app ownership rules

Those belong in:

* `docs/architecture.md`
* `docs/planning/MASTER.md`
* `docs/apps.md`
* `docs/infra.md`

## 🧭 Operations thesis

This file must answer five questions clearly:

* what exists now
* what runs now
* what is only scaffolded
* what is safe for live users
* what operational gaps still exist

Nothing in the repo should be described as operational truth unless it is actually implemented, runnable, and verified here.

## 📏 Status labels

All operational states described here must use one of these labels only:

* **planned**
* **scaffolded**
* **bootable**
* **integrated**
* **production-ready**
* **hardened**

## 📦 Current repository baseline

The repository is no longer only a prototype extension tree. The current repo already contains:

* governed root documentation under `docs/`
* root governance artifacts
* a shallow monorepo layout under `apps/`, `packages/`, `python/`, `infra/`, `testing/`, and `tools/`
* a central repository verifier under `tools/verify/`
* reserved runtime homes for extension, web, API, ingest, MCP, ML, and evaluation work
* empty scaffold placeholders for the reserved web, API, ingest, MCP, ML, and evaluation homes under `apps/`

What it does **not** yet prove as operational truth:

* a bootable web application
* a bootable API service
* a bootable job runtime
* integrated auth across browser and web surfaces
* integrated graph, retrieval, or AI product flows
* production-ready telemetry, dashboards, or experiment evidence

## 📦 Current surface status

### 🪟 Extension

Current status: **scaffolded**

Operational notes:

* the repository reserves `apps/extension` as the browser runtime home
* the old prototype concept is historically validated, but the rebuilt extension is not yet operational truth

### 🌐 Web

Current status: **scaffolded**

Operational notes:

* `apps/web` exists as an empty reserved control-plane placeholder
* no bootable web proof exists yet in the rebuild tree

### ⚙️ API

Current status: **scaffolded**

Operational notes:

* `apps/api` exists as an empty reserved request-serving placeholder
* no bootable service proof exists yet in the rebuild tree

### 📥 Ingest

Current status: **scaffolded**

Operational notes:

* `apps/ingest` exists as an empty reserved run-to-completion placeholder
* no bootable job proof exists yet in the rebuild tree

### 🧰 MCP

Current status: **scaffolded**

Operational notes:

* `apps/mcp` exists as an empty reserved future runtime home
* no MCP runtime proof exists yet

### 📈 ML

Current status: **scaffolded**

Operational notes:

* `apps/ml` exists as an empty reserved future runtime home
* no ML-serving or ML-orchestration proof exists yet

### 🧪 Evaluation

Current status: **scaffolded**

Operational notes:

* `apps/eval` exists as an empty reserved future runtime home
* no evaluation runtime proof exists yet

### 📚 Documentation

Current status: **scaffolded**

Operational notes:

* root `docs/` is the canonical documentation system now
* GitHub Pages is intended to publish static output from that source later
* there is no separate documentation runtime in the repo

## 👀 Current quality posture

Current status: **integrated**

Operational notes:

* the repo already contains governance docs, workflows, hooks, and verifier code
* local git hooks exist under `tools/hooks/` and can be installed manually with `bun run hooks:install` for each clone
* local environment sync is tracked by a git-local stamp under `.git/synaweave/environment-sync.json`
* `post-checkout`, `post-merge`, and `post-rewrite` auto-sync Bun tooling when `package.json`, `bun.lock`, or `requirements-dev.txt` change, but they only auto-install Python dependencies when the repo owns `.venv/bin/python3`; otherwise they warn operators to run the canonical sync command manually
* `pre-commit` warns when the local environment stamp is stale, while `pre-push` blocks stale state before the full verification lane runs
* `python3 -m tools.verify.main` is the repo-contained proof point for the D1 control baseline, so this section should not stay at **scaffolded** once those controls are aligned and passing locally
* the hosted `repo-verify` workflow runs `bun run verify`, and that root script now includes ADR validation alongside the other repo-level checks
* the hosted `dependency-installability` workflow verifies clean Bun installs and direct Python dev-tool pins from the checked-in manifests without mutating the checked-out repository
* hosted merge enforcement such as GitHub rulesets, required checks, and secret-scanning posture still requires GitHub-side confirmation before this file claims platform-enforced protection
* online AI proof and offline experiment proof are planned, not yet operational

## ☁️ Current runtime model

The locked target model is documented in `docs/architecture.md` and `docs/infra.md`, but it is **not** yet operational truth.

Today, the rebuild is best described as a governed platform scaffold with reserved runtime homes and documentation-first controls, not as a deployed multi-runtime product.

## 🔐 Current auth and identity status

Current status: **planned**

Locked intended baseline:

* passwordless email sign-in first
* browser-safe public credentials only in browser surfaces
* privileged credentials only in secure backend runtimes
* PKCE-capable web flow
* extension-safe session persistence

This section must not claim auth is integrated until:

* a user can sign in
* session state persists correctly
* backend identity verification succeeds
* browser bundles contain no privileged credentials

## 🗃️ Current data-plane status

### 🗃️ Operational relational data

Current status: **planned**

Target operational truth:

* user profile and workspace records
* operational study metadata
* user-scoped product state
* backend-owned metadata and runtime records

### 🪣 Artifact storage

Current status: **planned**

Target operational truth:

* screenshots
* raw captures
* cleaned source artifacts
* user uploads
* future export artifacts
* future dataset and evaluation artifacts

### 🕸️ Graph store

Current status: **planned**

Target operational truth:

* prerequisite edges
* concept links
* topic relationships
* graph-enhanced retrieval support

None of these may be treated as operational until the relevant runtime paths and policies are actually in place.

## 👀 Current observability status

Current status: **planned**

The reviewed public repo materials do not currently show an operational observability stack in the rebuild state. The rebuild target is:

* OpenTelemetry instrumentation
* OpenTelemetry Collector
* Prometheus
* Grafana
* Langfuse

Operational truth begins only when:

* traces are emitted
* logs are structured
* metrics are queryable
* dashboards exist
* AI-ready traces appear in Langfuse

Until then, observability remains planned or scaffolded rather than integrated.

## ✅ Current testing status

Current status: **planned**

The rebuild target includes a root `testing/` taxonomy with:

* unit
* component
* integration
* contract
* ui
* e2e
* security
* performance
* accessibility
* evals

This section must remain honest:

* planned if only specified in docs
* scaffolded if folders and baseline harnesses exist
* integrated only when active tests run in CI
* production-ready only when test gates are enforcing real quality expectations

## 🚦 Current CI and governance status

### 🚦 CI

Current status: **scaffolded**

Operational truth begins when:

* workflows exist
* required checks run
* branch protection is enforced
* failures block merge

Current posture:

* workflows exist in the repository and are part of the governed control surface
* `repo-verify` is the full hosted verification path; `dependency-installability` is a separate hosted supply-chain lane for clean dependency install checks; the path-filtered `docs-guard`, `governance-guard`, and `protected-paths` workflows are focused supplemental workflows for matching pull-request changes
* GitHub rulesets, branch protection, and secret-scanning enforcement remain external platform settings
* merge-readiness claims must therefore distinguish local workflow and verifier evidence from hosted enforcement that still depends on those external controls being configured against the documented posture
* this file must not describe the supplemental path-filtered workflows as confirmed GitHub-required ruleset checks unless that hosted enforcement is separately verified

### 📦 Dependency update posture

Current status: **integrated**

Operational notes:

* Renovate configuration exists in-repo for grouped low-noise dependency updates
* patch and minor Bun or npm workspace updates are grouped together
* patch and minor Python dev requirement updates are grouped together
* patch and minor GitHub Actions updates are grouped together
* major dependency updates require explicit dependency dashboard approval before Renovate opens a PR
* hosted dependency enforcement still depends on external GitHub configuration where required checks or rulesets are expected

### 🔐 Governance

Current status: **integrated**

The rebuild requires the following governance surface:

* `LICENSE`
* `CLA.md`
* `CONTRIBUTING.md`
* `CODE_OF_CONDUCT.md`
* `NOTICE`
* `SECURITY.md`
* `TRADEMARKS.md`

Current posture:

* the governance files exist in the repository and document the expected merge posture
* the documented governance surface can be treated as locally integrated when those files stay aligned and local verification passes
* GitHub ruleset, branch-protection, and secret-scanning enforcement still live outside the repository and require separate GitHub-side confirmation before this section claims end-to-end merge blocking

## 📚 Current product gap summary

The rebuild exists because the current prototype leaves major operational gaps. The existing public materials already point to missing capabilities around backend sync, extraction quality, and broader product usability, and the old stretch-goal list is now treated as required scope before native expansion.

The primary gaps still to be closed are:

* platform runtime separation
* authenticated multi-surface user flow
* stable backend contracts
* deployable service and job model
* observability
* testing discipline
* evaluation discipline
* governance
* production hardening
* AI and ML depth

## 📏 Operational reporting rules

Whenever an implementation change affects real runtime truth, this file must be updated.

### ✅ Must update this file when:

* a new runtime becomes bootable
* a runtime becomes integrated
* a deploy path changes
* a config or secret boundary changes
* a surface becomes production-ready
* a testing or observability milestone becomes real
* a major gap is closed
* a previously claimed capability is rolled back or removed

### 🚫 Must not do:

* describe planned work as current reality
* describe scaffolded work as integrated
* describe demos or local one-offs as production-ready
* hide operational regressions

## 🧠 Relationship to README

The README is the outward-facing, high-level, product-oriented description.

This file is the inward-facing, operational truth document.

### 📏 Rule

If the README says the repo is building toward a capability, that is fine.

If this file says the capability is not yet operational, that is the truth the team must use when discussing current status.

## ✅ Operations-level definition of done

An operational update is incomplete unless:

* this file reflects the new runtime truth
* status labels are updated honestly
* related root docs remain aligned
* relevant sprint planning files remain aligned
* the repo’s actual behavior matches what this file claims

## 📜 Relationship to other root docs

This file works with:

* `docs/architecture.md` for target system design
* `docs/apps.md` for app ownership boundaries
* `docs/infra.md` for deployment topology
* `docs/testing.md` for current quality maturity
* `docs/planning/MASTER.md` for planning structure and execution truth
* sprint planning files for deliverable-specific status transitions

This file should stay focused on **current operational truth**, not future design.
