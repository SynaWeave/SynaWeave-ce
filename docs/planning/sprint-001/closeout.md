# 🧾 Sprint 1 — D2 Runtime and D3 Closeout

## 1. 🧭 TL;DR

Sprint 1 now proves one truthful local runtime slice across web, extension, API, ingest, and a shared sqlite-backed runtime store.

This closeout records one bounded local Sprint 1 runtime and quality baseline after the current backend and browser fixes. It describes what this branch proves locally, what has repo-hosted evidence, and what still remains outside the bounded Sprint 1 proof surface.

## 2. ✅ What this branch proves

### 2.1 ⚙️ D2 runtime proof

The repo now proves one real bounded runtime path across:

- `apps/extension/`
- `apps/web/`
- `apps/api/`
- `apps/ingest/`
- `python/common/`
- `python/evaluation/runtime_eval.py`

The path proves:

- browser-safe email session bootstrap through `/v1/auth/link`
- shared identity resolution through `/v1/identity`
- workspace bootstrap through `/v1/workspace/bootstrap`
- durable workspace action writes through `/v1/workspace/action`
- separate background job execution through `apps.ingest.main`
- metrics export through `/metrics`

### 2.2 👀 Repo-local D3 proof baseline

The repo now contains bounded D3 evidence inputs and local reproduction paths for the runtime slice:

- durable telemetry rows and trace-like JSONL output generated under `build/runtime/` after running the local runtime slice
- collector-routed OpenTelemetry trace exports for API and ingest generated under `build/observability/collector-traces.json` when the local compose stack is running
- baseline metrics snapshots generated under `build/runtime/baseline.json` and `build/runtime/metrics.json` after exercising the runtime path and calling `/metrics` or `/v1/baseline`
- durable backend correlation logs and measurement history generated under `build/runtime/backend-logs.jsonl` and `build/runtime/measurements.jsonl` for replay-to-replay comparison of the API and job critical path
- automated browser accessibility proof under `testing/accessibility/` plus enforced Playwright coverage for the web shell and packaged extension panel document within the bounded local browser slice
- versioned synthetic eval fixture under `testing/evals/fixtures/runtime-digest-density.v1.json`
- versioned repo-local eval proof under `testing/evals/artifacts/runtime-digest-density.local-proof.v1.json`, generated from the runtime-eval harness rather than the collector path
- versioned repo-local MLflow proof, verified through the local tracking path after `python3 -m python.evaluation.runtime_eval` and `python3 -m python.evaluation.verify_mlflow_run`
- versioned self-hosted local Langfuse proof under `testing/evals/artifacts/runtime-digest-density.langfuse-local-proof.v1.json`, generated only after writing and querying a local Langfuse service
- versioned repo-local performance proof under `testing/performance/runtime-baseline.local-proof.v1.json`, generated from the same runtime-eval harness and runtime-store telemetry
- runtime baseline targets under `testing/performance/runtime-baseline.md`, now paired with generated runtime evidence
- versioned Prometheus alert rules plus Grafana provisioning and dashboard artifacts under `infra/docker/`
- reproducible local trace and metrics replay through `python3 -m tools.observability.critical_path_probe`
- runtime-focused unit proof under `testing/unit/`
- hosted proof for ruleset-required checks, CodeQL, secret scanning, and push protection belongs on real pull-request and platform enforcement paths rather than in the repo-local replay alone

## 3. 🚫 What this file does not claim

This file does **not** claim more than the evidence supports:

- repo-local proof covers browser automation enforcement, collector-routed local observability, local metrics and baseline artifacts, repo-local MLflow proof, and bounded self-hosted local Langfuse proof
- this file does not treat repo-local replay as proof of hosted ruleset-required checks, CodeQL, secret scanning, or push protection
- managed Langfuse or managed MLflow operations remain later deployment choices rather than current Sprint 1 proof
- edge, CDN, and API gateway providers remain intentionally undecided behind adapters
- this file does not upgrade repo-local Langfuse or MLflow evidence into hosted/team-shared durability claims
- this file does not claim managed Cloud Run deployment proof

## 4. ▶️ Local replay

```bash
bun run deps:app
docker compose -f infra/docker/docker-compose.yml up -d
docker compose -f infra/docker/langfuse-compose.yml up -d
python3 -m python.evaluation.runtime_eval --mlflow-tracking-uri http://127.0.0.1:5001
python3 -m python.evaluation.langfuse_local_proof
python3 -m python.evaluation.verify_mlflow_run --tracking-uri http://127.0.0.1:5001
python3 -m tools.observability.critical_path_probe
python3 -m tools.verify.main
bun run verify
```

## 5. 🔍 Manual smoke path

1. open the web shell and sign in with a test email
2. confirm workspace bootstrap succeeds
3. write a durable note and run the digest job
4. load the unpacked extension and sign in with the same email
5. pull a page selection, write a durable action, and run the digest job
6. confirm the same bridge code, workspace id, digest, and eval appear across both surfaces

## 6. 📌 Handoff note

Sprint 2 can build against a real local runtime baseline plus enforced browser automation, tracked repo-local eval and performance artifacts, self-hosted local MLflow proof, self-hosted local Langfuse proof, and collector-routed observability proof. Hosted required checks and platform enforcement remain PR-path and GitHub-platform evidence rather than repo-local closeout proof, while managed observability backends and concrete edge-routing providers remain follow-on work behind the Sprint 1 adapter and evidence boundaries.
