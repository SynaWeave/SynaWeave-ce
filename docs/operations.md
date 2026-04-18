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
* active runtime homes for extension, web, API, and ingest
* shared runtime helpers under `python/common/`
* a local runtime proof store under `build/runtime/`

What it does **not** yet prove as operational truth:

* cloud deployment proof
* integrated graph, retrieval, or AI product flows
* managed observability backends, deployed edge routing, or GitHub-side branch controls beyond the repo-local and documented hosted evidence already established

## 📦 Current surface status

### 🪟 Extension

Current status: **integrated**

Operational notes:

* `apps/extension` now provides a real side-panel shell for sign-in, capture, durable actions, and digest replay
* the extension shares identity continuity with the web shell through the API runtime
* extension host access is now limited to the local API origins; broad page matching remains only for the bounded selection-capture content script path used in Sprint 1

### 🌐 Web

Current status: **integrated**

Operational notes:

* `apps/web` now provides a bootable static control-plane shell
* the web shell signs in, writes one durable action, runs the digest job, and reloads workspace truth

### ⚙️ API

Current status: **integrated**

Operational notes:

* `apps/api` now provides liveness, readiness, auth, identity, workspace, job, telemetry, baseline, and metrics routes
* readiness only reports ready when the sqlite boundary and runtime artifact directory are available

### 📥 Ingest

Current status: **integrated**

Operational notes:

* `apps/ingest` now runs as a separate Python process
* the worker turns recent workspace actions into a digest and evaluation record

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

* root `docs/` remains the canonical documentation system
* there is still no separate documentation runtime in the repo

## 👀 Current quality posture

Current status: **integrated**

Operational notes:

* the repo already contains governance docs, workflows, hooks, and verifier code
* runtime-focused unit tests now cover the API path and sqlite-backed runtime store
* local git hooks exist under `tools/hooks/` and can be installed manually with `bun run hooks:install` for each clone
* local environment sync is tracked by a git-local stamp under `.git/synaweave/environment-sync.json`
* `post-checkout`, `post-merge`, and `post-rewrite` auto-sync Bun tooling when `package.json`, `bun.lock`, or `requirements-dev.txt` change, but they only auto-install Python dependencies when the repo owns `.venv/bin/python3`; otherwise they warn operators to run the canonical sync command manually
* `pre-commit` warns when the local environment stamp is stale, while `pre-push` blocks stale state before the full verification lane runs
* `python3 -m tools.verify.main` is the repo-contained proof point for the D1 control baseline, so this section should not stay at **scaffolded** once those controls are aligned and passing locally
* the hosted `repo-verify` workflow runs `bun run verify`, and that root script now includes ADR validation alongside the other repo-level checks
* the hosted `dependency-installability` workflow verifies clean Bun installs and direct Python dev-tool pins from the checked-in manifests without mutating the checked-out repository
* local runtime metrics snapshots, measurement-history JSONL, backend correlation JSONL, traces, and sqlite-backed telemetry rows are generated under `build/runtime/` after exercising the runtime path or calling `/metrics`; they are local build artifacts, not tracked repo evidence
* `python3 -m python.evaluation.runtime_eval` now regenerates versioned repo-local proof under `testing/evals/artifacts/runtime-digest-density.local-proof.v1.json` and `testing/performance/runtime-baseline.local-proof.v1.json`
* the tracked proof artifacts are derived from actual runtime-store telemetry and eval writes, not from manual target notes alone
* those repo-local eval and performance artifacts do not by themselves prove collector export; collector-routed trace proof is a separate local compose-backed path
* `infra/docker/` contains local Prometheus, collector, and Grafana scaffolds for the runtime slice
* hosted merge enforcement such as GitHub rulesets, required checks, and secret-scanning posture still requires GitHub-side confirmation before this file claims platform-enforced protection
* automated browser smoke and accessibility checks now cover the local web shell plus the packaged extension panel document
* Playwright now uses the packaged extension options harness to issue a real `chrome.sidePanel.open()` request and confirm that the side-panel runtime booted `popup.html`
* the repo still does not claim direct DOM inspection of the browser-owned side-panel container itself because Chromium does not expose that chrome to Playwright here
* collector-routed API and ingest telemetry is locally reproducible through the optional compose-backed observability stack, but fuller browser-native and hosted deployment proof remain incomplete

## ☁️ Current runtime model

The locked target model is documented in `docs/architecture.md` and `docs/infra.md`, but it is **not** yet operational truth.

Today, the rebuild is best described as a governed platform with one local runtime proof slice, not as a deployed multi-runtime product.

## 🔐 Current auth and identity status

Current status: **integrated**

Operational notes:

* a user can sign in from web or extension with an email-shaped local session flow
* session state persists in browser storage across refresh or panel reopen within the bounded local proof path
* backend identity verification succeeds through bearer-token lookup at the API boundary
* browser bundles contain no privileged credentials in the current runtime slice
* this remains an adapter-first Sprint 1 proof path, with Supabase-compatible auth as the default target rather than a permanent provider lock-in

## 🗃️ Current data-plane status

### 🗃️ Operational relational data

Current status: **integrated**

Operational notes:

* local sqlite stores users, sessions, workspaces, actions, jobs, evals, and telemetry
* the durable local state lives under `build/runtime/synaweave.sqlite3`

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

Current status: **integrated**

Operational notes:

* `infra/docker/docker-compose.yml` now runs the local API, collector, Prometheus, Grafana, and MLflow stack together
* `infra/docker/langfuse-compose.yml` now offers a separate bounded self-hosted Langfuse proof stack for one local trace-plus-score path
* API and ingest export OpenTelemetry traces through the local collector when the compose stack or matching env is enabled
* web and extension requests send W3C `traceparent` headers for request continuity, but they do not yet run full browser OTel SDK instrumentation
* local metrics remain queryable through `/metrics`, Prometheus, and the versioned Grafana dashboard plus alert rules under `infra/docker/`
* API middleware and ingest now write structured backend correlation logs under `build/runtime/backend-logs.jsonl` so request ids, trace ids, and job ids can be compared across the critical path
* `/metrics` and `/v1/baseline` now append durable measurement history under `build/runtime/measurements.jsonl`, including hotspot summaries and failure or degraded-state counts that the dashboard and alerts expose where the current architecture supports them
* the reproducible critical-path probe lives at `python3 -m tools.observability.critical_path_probe`
* `python3 -m python.evaluation.runtime_eval` now writes repo-local telemetry-derived eval and performance artifacts plus one self-hosted local MLflow run, but not collector export by itself
* `python3 -m python.evaluation.langfuse_local_proof` proves one self-hosted local Langfuse trace and score write plus query path from the Sprint 1 dataset
* `python3 -m python.evaluation.verify_mlflow_run` verifies that the latest self-hosted local MLflow run exists with the expected metrics and artifacts
* managed Langfuse operations, managed or team-shared MLflow durability, and fuller browser-native observability proof remain later follow-on work rather than current runtime truth
* critical-path observability claims are only durable when the branch records them through versioned dashboards or alerts, machine-readable proof artifacts, or replayable local stores

## ✅ Current testing status

Current status: **integrated**

Operational notes:

* unit tests now cover the runtime store and API critical path
* manual accessibility notes still exist under `testing/` for checks beyond current automation coverage
* Playwright now proves the web-shell sign-in, workspace bootstrap, durable write, and digest smoke path against the local runtime
* Playwright also drives the packaged extension options harness to open the real side-panel runtime and records side-panel boot timing evidence under test output artifacts
* Playwright plus Axe now scan the signed-in web shell and the packaged extension panel document
* the current extension proof still stops short of direct side-panel container DOM inspection because Chromium does not expose that browser chrome to Playwright here
* `testing/evals/fixtures/runtime-digest-density.v1.json` is the versioned Sprint 1 synthetic eval dataset
* `testing/evals/artifacts/` and `testing/performance/runtime-baseline.local-proof.v1.json` now hold tracked repo-local machine-readable proof generated from the eval harness
* those tracked artifacts prove the runtime-eval harness path, while compose-backed collector exports remain a separate observability proof path

## 🔌 Current edge and gateway posture

Current status: **planned**

Operational notes:

* edge, CDN, and API gateway providers remain intentionally undecided in Sprint 1
* the current branch preserves those seams behind adapters and contract-stable public boundaries
* later activation must update this file when a concrete provider becomes bootable or integrated

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
