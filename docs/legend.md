# 📖 Legend

## 🧩 Purpose

This file standardizes short terms used across `docs/` and planning artifacts.

Use this legend before adding new abbreviations.

---

## 🏷️ Top-level terms

- **SW** — SynaWave, used only where the shorter form materially improves readability
- **ADR** — Architectural Decision Record, stored in `docs/adrs/`
- **D1 / D2 / D3** — Foundation, Runtime, and Quality deliverables in a sprint
- **SLO** — Service-level objective
- **SLA** — Service-level agreement
- **IDP** — Identity platform boundary (auth + sessions)
- **API** — Request-serving backend boundary
- **MCP** — Model Context Protocol tool surface
- **ML** — Machine learning
- **OTel** — OpenTelemetry
- **RLS** — Row-level security

This file is the single durable registry for shared abbreviations used across root docs and sprint-planning surfaces.

## 🧭 Planning terms

- **Sprint** — top-level program timebox in `docs/planning/sprint-###/`
- **Deliverable** — concrete work package inside one sprint (`d#-name.md`)
- **Task** — implementation item (`- [ ]`/`- [x]` entries in deliverable scope)
- **Frozen decision** — accepted decision that should hold across later sprints until a superseding ADR

## 🧠 Architecture terms

- **App** — runtime under `apps/`
- **Package** — shared TypeScript reusable boundary under `packages/`
- **Shared module** — reusable Python component under `python/`
- **Contract** — public data shape or message schema under `packages/contracts`
- **Runtime** — execute-capable process or service under `apps/`
- **Job runtime** — run-to-completion task boundary (typically `apps/ingest` initially)

## 🌐 Quality terms

- **Traceability** — ability to follow a request across runtime boundaries with shared identifiers
- **Telemetry** — traces, metrics, logs, and labels emitted by runtime boundaries
- **Supply-chain control** — checks for dependency integrity and policy at dependency change points
- **Commit gate** — local and PR-level checks that can block unsafe changes before merge
- **Protected branch** — enforced merge policy on default branch

## 📏 Status labels

Use only these values in root docs:

- planned
- scaffolded
- bootable
- integrated
- production-ready
- hardened
