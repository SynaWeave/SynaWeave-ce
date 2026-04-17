# Runtime performance baseline

This file records the human-readable baseline targets that can be compared against the generated JSON baseline snapshot under `build/runtime/baseline.json` after a local runtime run.

Current local baseline scope:

- workspace entry timing target: 200 ms or less
- side-panel open timing target: 200 ms or less
- API p95 latency target: 500 ms or less for the critical path
- job p95 duration target: 1000 ms or less for the first digest proof

This file is a bounded local baseline, not proof that broader D3 performance automation or hosted performance budgets are complete.
