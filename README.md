# SynaWeave

SynaWeave is a governed, multi-surface repository for a knowledge-weaving learning platform. The platform combines the following under a shared architecture and contract model: 
- browser extension capture
- a web control plane
- API services
- background jobs
- graph-aware retrieval 
- AI/ML workflows 


## What this repo contains

- `apps/` — runtime homes reserved for `extension`, `web`, `api`, `ingest`, `ml`, `mcp`, and `eval`
- `packages/` — shared TypeScript primitives and contracts
- `python/` — shared intelligence modules and data-processing foundations
- `infra/` — deployment, policy, and observability envelopes
- `testing/` — quality taxonomy and verification layers
- `tools/` — local checks and governance automation
- `docs/` — canonical technical docs, planning, ADRs, and governance-linked specifications

## Current repo posture

- monorepo topology: enabled
- root docs contract: enabled
- governance artifacts: enabled
- repo-control baseline: locally verifiable
- hosted merge enforcement: requires GitHub-side confirmation
- reserved runtime homes: scaffold placeholders present
- runtime proof paths: planned for later Sprint 1 deliverables and later sprints

The reserved homes for web, API, ingest, MCP, ML, and evaluation exist as empty scaffold placeholders in Deliverable 1.
Their presence preserves governed runtime boundaries without claiming bootable application maturity.

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
python3 -m tools.verify.main
bun run verify
```

`bun run hooks:install` installs the repo-owned local git hooks into `.git/hooks` for this clone. The install is manual, so run it after cloning or when hook files change.
`python3 -m tools.dev.sync_environment sync` refreshes the local Bun toolchain plus Python dependencies from `package.json`, `bun.lock`, and `requirements-dev.txt`, then records a git-local sync stamp under `.git/`. When the repo owns `.venv/bin/python3`, the sync command installs Python dependencies there before falling back to the invoking `python3`.
`python3 -m tools.verify.main` is the baseline repository-control gate.
`bun run verify` is the full local gate for linting, typechecking, tests, and repo-control verification.

The local hook set keeps contributor feedback close to the workstation:

- `commit-msg` enforces the governed commit-message contract before a commit lands
- `post-checkout`, `post-merge`, and `post-rewrite` auto-sync Bun tooling and only auto-install Python dependencies when the repo owns `.venv/bin/python3`; otherwise they warn to run the canonical sync command manually
- `pre-commit` warns on stale local environment state, then runs staged Betterleaks scanning plus the protected-surface verification lane
- `pre-push` blocks stale local environment state before tracked-file Betterleaks scanning and the full verification gate

Installing the hooks reduces PR churn by catching commit, security, and repo-control issues before review.

Create any app-level dependencies only after checks pass and the owner docs are aligned.

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
