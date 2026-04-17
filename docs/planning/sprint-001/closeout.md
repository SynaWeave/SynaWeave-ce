# 🧾 Sprint 1 — D2 Runtime and Partial D3 Closeout

## 1. 🧭 TL;DR

Sprint 1 now proves one truthful local runtime slice across web, extension, API, ingest, and a shared sqlite-backed runtime store.

This closeout does **not** claim full D3 completion. It records that D2 runtime proof is in place and that a partial D3 baseline can be reproduced locally through manual accessibility notes, local performance targets, durable telemetry rows, `/metrics`, and generated baseline JSON artifacts.

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

### 2.2 👀 Partial D3 baseline

The repo now contains partial D3 evidence inputs and local reproduction paths for the runtime slice:

- durable telemetry rows and trace-like JSONL output generated under `build/runtime/` after running the local runtime slice
- baseline metrics snapshots generated under `build/runtime/baseline.json` and `build/runtime/metrics.json` after exercising the runtime path and calling `/metrics` or `/v1/baseline`
- manual accessibility checklist under `testing/accessibility/runtime-a11y.md`
- runtime baseline targets under `testing/performance/runtime-baseline.md`
- local Prometheus, collector, and Grafana scaffolds under `infra/docker/`
- runtime-focused unit proof under `testing/unit/`

## 3. 🚫 What this file does not claim

This file does **not** claim that Sprint 1 D3 is complete or fully proven. The following remain incomplete or only scaffolded:

- automated browser accessibility coverage
- collector-routed OpenTelemetry instrumentation in active runtime use
- managed Cloud Run deployment proof
- GitHub-side confirmation of required checks and rulesets
- broader security and supply-chain automation beyond the current repo controls

## 4. ▶️ Local replay

```bash
bun run deps:app
bun run dev:api
bun run dev:web
bun run build:extension
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

Sprint 2 can build against a real local runtime baseline. Sprint 2 should still treat automated accessibility, fuller observability routing, and hosted deployment proof as follow-up work instead of already-closed D3 scope.
