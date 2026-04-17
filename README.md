# SynaWeave

SynaWeave is a governed, multi-surface repository for a knowledge-weaving learning platform. The current repo now includes a bounded Sprint 1 runtime slice across:
- browser extension capture and workspace bridge
- a web control plane shell
- a FastAPI request boundary
- a separate ingest job path
- shared Python runtime helpers
- locally generated baseline metrics, traces, and proof artifacts

## What this repo contains

- `apps/` — runtime homes for `extension`, `web`, `api`, `ingest`, `ml`, `mcp`, and `eval`
- `packages/` — shared TypeScript primitives and contracts
- `python/` — shared runtime helpers and future intelligence modules
- `infra/` — deployment, policy, and observability envelopes
- `testing/` — quality taxonomy and verification layers
- `tools/` — local checks and governance automation
- `docs/` — canonical technical docs, planning, ADRs, and governance-linked specifications

## Current repo posture

- monorepo topology: enabled
- root docs contract: enabled
- governance artifacts: enabled
- repo-control baseline: locally verifiable
- first runtime proof path: integrated
- first background job proof path: integrated
- local metrics and trace artifacts: reproducible locally after runtime exercise
- D3 closeout: not yet proven
- hosted merge enforcement: still requires GitHub-side confirmation

The current local Sprint 1 proof path is:
1. sign in from `apps/web` or `apps/extension`
2. resolve the same user email and bridge code across both surfaces
3. bootstrap one server-owned workspace through the API
4. write one durable workspace action through the API
5. run one separate ingest job to create a digest and evaluation record
6. read the updated workspace state back through the browser surface
7. inspect metrics at `/metrics` and the generated JSON artifacts under `build/runtime/` after exercising the runtime path

This is a D2 runtime proof with partial D3 evidence. It is not a claim that automated accessibility, full observability routing, Cloud Run deployment, or broader D3 enforcement is complete.

## Repository-first entry points

- [Architecture](docs/architecture.md)
- [Apps](docs/apps.md)
- [Infra](docs/infra.md)
- [Templates](docs/templates.md)
- [Planning](docs/planning/MASTER.md)
- [Testing](docs/testing.md)
- [Operations status](docs/operations.md)
- [Sprint 1 overview](docs/planning/sprint-001/overview.md)
- [ADR index for Sprint 1](docs/adrs/sprint-001.md)

## Local setup

```bash
cp .env.example .env
bun run hooks:install
python3 -m tools.dev.sync_environment sync
bun run deps:app
python3 -m tools.verify.main
bun run verify
```

## Local runtime commands

```bash
bun run dev:api
bun run dev:web
bun run build:extension
```

Open:
- API: `http://127.0.0.1:8000`
- Web shell: `http://127.0.0.1:3000`
- Metrics: `http://127.0.0.1:8000/metrics`

The extension source remains under `apps/extension/` and can be loaded unpacked in Chromium-based browsers for the local proof flow.

## Development expectations

- update docs when behavior or structure changes
- keep package and app boundaries narrow
- keep contracts versioned and testable
- treat GitHub-hosted branch checks and rulesets as external settings until separately confirmed
- treat security and dependency risk as first-class engineering work
- update `docs/templates/` when a recurring doc shape changes across more than one governed artifact

## Contributing quickly

1. Follow commit conventions in `CONTRIBUTING.md`.
2. Keep changes in the governed surface they touch (`docs`, `apps`, `packages`, `testing`, `infra`, `python`).
3. Reuse the owner doc or template for the surface you change instead of creating a parallel format.
4. Install the local hooks for your clone, then run the local verification commands before opening PRs.

## License

This project currently uses a **GNU General Public License family** license as defined by `LICENSE`.
The full license text is in `LICENSE`.

## Governance artifacts

- `AGENTS.md`
- `GOVERNANCE.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `CLA.md`
- `NOTICE`
- `TRADEMARKS.md`
