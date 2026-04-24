# SynaWeave

SynaWeave is a knowledge-weaving learning OS. The product thesis is a pedagogy engine that uses agentic mentoring to orchestrate adaptive tutoring so users can explore deeper, learn faster, and retain more.

## What this repo is building

SynaWeave CE is the AGPL core for:
- capture for text, notes, transcripts, and scraped sources
- a knowledge engine for cleaning, chunking, embedding, graph linking, and indexing
- a study engine for markdown-first cards, recommendations, and progress tracking
- an adaptive tutor that chooses the right instructional mode instead of only answering questions
- a visible data and ML platform for ingestion, evals, experiments, and observability

The current product posture is:
- **Sprint 1:** publicly visible progress product
- **Sprint 2:** ready to accept real public traffic
- **later sprints:** deeper pedagogy, graph, eval, and monetization depth without changing the core contract

## Repo shape

- `apps/` — runtime surfaces
- `packages/` — shared TypeScript contracts and packages
- `python/` — shared Python intelligence and data modules
- `infra/` — deploy, runtime, policy, and ops envelopes
- `testing/` — contract, unit, browser, eval, and performance proof
- `tools/` — repo verification and local automation
- `docs/` — canonical technical docs

## Canonical docs

Start here in this order:
- [Infra](docs/infra.md) — locked choices, hosting posture, config contract, provider seams
- [Architecture](docs/architecture.md) — system map, flow diagrams, pedagogy engine, open-core split
- [Legend](docs/legend.md) — approved short forms, naming rules, prefix rules
- [Onboarding](docs/onboarding.md) — how a new dev should read and work in the repo
- [Apps](docs/apps.md)
- [Packages](docs/packages.md)
- [Python](docs/python.md)
- [Testing](docs/testing.md)
- [Operations](docs/operations.md)
- [Planning](docs/planning/MASTER.md)

## Current platform thesis

The repo is intentionally shaped for:
- MLE, DS, SWE, and staff-level interview signaling
- startup technical diligence and funding pitches
- cheap early hosting with a clean scale path
- provider swap flexibility at the adapter edge
- visible eval and observability as product assets

The locked runtime posture is:
- thin extension client
- web app as control plane
- FastAPI as the main backend boundary
- Bun as repo-wide package manager and task runner
- Docker-first local and hosted packaging
- Cloud Run first, with a fast later pivot path to GKE
- Postgres as operational truth
- object storage behind an S3-compatible seam
- graph retrieval behind a graph adapter seam
- evals and traces visible in product and ops workflows

## Naming posture

The repo now prefers short raw identifiers.
Use generic names where the contract is provider-neutral, and provider names only where the adapter is truly provider-specific.
See [docs/legend.md](docs/legend.md) for the approved registry.

Examples:
- `DB_URL`, not `SUPABASE_DATABASE_URL`
- `OBJ_BUCKET`, not `BACKBLAZE_B2_OBJECT_STORAGE_BUCKET_NAME`
- `LF_URL` for Langfuse adapter config
- `SB_URL` only inside Supabase-specific adapter or deploy config
- `GCP_PROJECT_ID` where the provider is actually the point

## Local setup

```bash
cp .env.example .env
bun run hooks:install
bun run deps:app
bun run verify:docs
```

Use the lightest verification lane that matches the work you changed.

## License

This project currently uses an AGPL-oriented open-core posture for the community repo.
See `LICENSE` for the exact license text in the current branch.

## Migration note

The repo is moving from older branding and long provider-heavy env names to `SynaWeave` plus shorter generic env contracts. During this transition, loaders may accept a small set of legacy aliases, but the canonical naming lives in `docs/legend.md` and `.env.example`.
