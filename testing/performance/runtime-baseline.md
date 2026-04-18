# Runtime performance baseline

This file records the human-readable baseline targets and the tracked repo-local proof artifact generated from actual runtime telemetry.

Tracked repo-local proof:

- fixture: `testing/evals/fixtures/runtime-digest-density.v1.json`
- performance artifact: `testing/performance/runtime-baseline.local-proof.v1.json`
- eval artifact: `testing/evals/artifacts/runtime-digest-density.local-proof.v1.json`
- regeneration command: `python3 -m python.evaluation.runtime_eval`

Current local baseline scope:

- workspace entry timing target: 200 ms or less
- bounded workspace-entry timing target across the web shell and packaged extension panel document: 200 ms or less
- API p95 latency target: 500 ms or less for the critical path
- job p95 duration target: 1000 ms or less for the first digest proof

Current tracked repo-local proof from `runtime-baseline.local-proof.v1.json`:

- workspace entry timing observed: 161.7 ms
- API p95 latency observed: 94.9 ms
- job p95 duration observed: 132.2 ms
- trace events captured during proof run: 6

Additional browser-timing evidence during `bun run test:e2e`:

- Playwright writes `web-shell-timing.json` with browser-side web-shell navigation, workspace-ready, durable-action, and digest timings
- Playwright writes `extension-side-panel-timing.json` with the real `chrome.sidePanel.open()` request timing and the popup runtime boot timing observed from extension storage evidence
- these JSON files are local test artifacts, not tracked repo-local proof, because they depend on the current Chromium test run

This file is a bounded local baseline, not proof that broader D3 performance automation, hosted performance budgets, or production telemetry budgets are complete.
