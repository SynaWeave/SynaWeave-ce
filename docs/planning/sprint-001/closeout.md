# 🧾 Sprint 1 — D2 Runtime and D3 Closeout

## 1. 🧭 TL;DR

Sprint 1 now proves one truthful local runtime slice across web, extension, API, ingest, and a shared sqlite-backed runtime store.

This closeout records that D2 runtime proof is in place and that the repo-local D3 stack is substantively complete. The strongest honest remaining gap is **one external GitHub-hosted proof point**: showing that dependency-review executes on a real pull-request path instead of skipping. Everything else claimed here is explicitly labeled as either repo-local proof or already-proven GitHub-hosted enforcement.

## 2. ✅ What closed

### 2.1 ⚙️ D2 runtime proof

The repo now contains a real bounded runtime path across:

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

The repo now contains D3 evidence inputs and local reproduction paths for the runtime slice:

- durable telemetry rows and trace-like JSONL output generated under `build/runtime/` after running the local runtime slice
- collector-routed OpenTelemetry trace exports for API and ingest generated under `build/observability/collector-traces.json` when the local compose stack is running
- baseline metrics snapshots generated under `build/runtime/baseline.json` and `build/runtime/metrics.json` after exercising the runtime path and calling `/metrics` or `/v1/baseline`
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
- GitHub-hosted proof already established in this session for ruleset-required checks, CodeQL, secret scanning, and push protection

## 3. 🚫 What this file does not claim

This file does **not** claim more than the evidence supports:

- repo-local proof covers browser automation enforcement, collector-routed local observability, local metrics and baseline artifacts, repo-local MLflow proof, and bounded self-hosted local Langfuse proof
- GitHub-hosted proof is already established in this session for ruleset-required checks, CodeQL, secret scanning, and push protection
- full D3 closeout still depends on exactly one external GitHub-hosted proof point: a real PR-path `dependency-review` execution that does not skip
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

Sprint 2 can build against a real local runtime baseline plus enforced browser automation, tracked repo-local eval and performance artifacts, local MLflow proof, self-hosted local Langfuse proof, collector-routed observability proof, and already-proven GitHub-hosted ruleset and scanning enforcement. The strongest remaining D3 blocker is narrow and external: prove one non-skipped `dependency-review` run on a real GitHub pull-request path, then update closeout language from “earned except for one external PR-path proof” to fully closed.
