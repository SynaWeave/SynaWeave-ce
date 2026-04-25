# 📖 Legend

## 🧩 Purpose

This file is the single registry for:
- approved short forms
- naming rules
- env prefix rules
- provider-vs-generic naming boundaries

Read this file before adding new raw identifiers.

---

## 🔒 Locked naming rules

### 1) Prefer generic names first

If the contract can survive a provider swap, the name should stay generic.

Use:
- `DB_URL`
- `OBJ_BUCKET`
- `AUTH_URL`
- `GRAPH_URL`
- `TRACE_OTLP_URL`
- `EVAL_URL`
- `EXP_URL`

Avoid:
- `SUPABASE_DB_URL`
- `BACKBLAZE_OBJECT_BUCKET`

### 2) Use provider names only at the adapter edge

Provider names are allowed when the config, deploy target, or adapter is truly provider-owned.

Allowed examples:
- `SB_URL`
- `B2_BUCKET`
- `LF_URL`
- `MLF_URL`
- `GCP_PROJECT_ID`
- `ZP_KEY`
- `N4J_URI`

Canonical cross-provider examples:
- `EVAL_URL`
- `EVAL_PK`
- `EXP_URL`
- `EXP_NAME`

### 3) Keep raw identifiers short

- hard cap: **5 words or fewer**
- preferred: **1–2 words**
- group related values instead of making one huge identifier

Prefer:
- `DB_POOL_URL`
- `AUTH_JWKS_URL`
- `OIDC_GOOGLE_ID`
- `JOB_INGEST_NAME`

Avoid:
- `THE_PRIMARY_DATABASE_CONNECTION_POOLING_URL`
- `THE_GOOGLE_OAUTH_CLIENT_ID_FOR_MAIN_PRODUCTION_SIGNIN`

### 4) Use stable prefixes by concern

Use the prefix that matches the concern, not the current vendor.

Generic prefixes:
- `SW_` — product-wide config
- `APP_` — app shell or browser-safe app config
- `API_` — API runtime config
- `AUTH_` — auth/session config
- `DB_` — operational database config
- `OBJ_` — object/blob storage config
- `CACHE_` — cache config
- `QUEUE_` — queue config
- `GRAPH_` — graph config
- `VEC_` — vector index config
- `MODEL_` — model serving config
- `EMB_` — embedding config
- `TRACE_` — tracing config
- `METRIC_` — metrics config
- `LOG_` — log config
- `EVAL_` — evaluation config
- `EXP_` — experiment tracking config
- `JOB_` — job runtime config
- `EMAIL_` — outbound mail config
- `OIDC_` — OIDC provider config

Provider prefixes:
- `GCP_` — Google Cloud Platform
- `GW_` — Google Workspace
- `GH_` — GitHub
- `SB_` — Supabase
- `B2_` — Backblaze B2
- `ZP_` — Zuplo
- `N4J_` — Neo4j
- `LF_` — Langfuse
- `MLF_` — MLflow
- `MF_` — Metaflow
- `LC_` — LangChain
- `LG_` — LangGraph

### 5) Backward-compatible env aliasing is allowed during migration

When the repo is moving from long or provider-heavy names to shorter generic names, the runtime loader may temporarily read both.
The short generic name is the canonical contract. The older alias exists only to avoid a flag day.

Prefer:
- `AUTH_AUD` with fallback to `AUTH_AUDIENCE`
- `TRACE_OTLP_URL` with fallback to `OTEL_EXPORTER_OTLP_ENDPOINT`
- `APP_URL` with fallback to `SYNAWAVE_WEB_BASE_URL`
- `SW_RUN_DIR` with fallback to `SYNAWAVE_RUNTIME_DIR`
- `DB_PATH` with fallback to `SYNAWAVE_RUNTIME_DB_PATH`
- `EVAL_URL` with fallback to `LF_URL` or `LANGFUSE_BASE_URL`
- `EXP_URL` with fallback to `MLFLOW_TRACKING_URI` or `MLF_URL`

### 6) Framework-required names do not own the repo contract

If a framework requires a special env prefix, keep that requirement in the app-local loader when possible.

Examples:
- canonical repo contract: `APP_URL`
- app-local alias only if needed: `NEXT_PUBLIC_APP_URL`

The repo contract should stay framework-light unless the framework requirement is unavoidable.

---

## 🏷️ Core short forms

- **SW** — SynaWeave
- **ADR** — Architectural Decision Record
- **API** — request boundary
- **MCP** — Model Context Protocol
- **ML** — machine learning
- **DS** — data science
- **MLE** — machine learning engineering
- **RAG** — retrieval-augmented generation
- **OTel** — OpenTelemetry
- **RLS** — row-level security
- **OIDC** — OpenID Connect
- **OTP** — one-time passcode
- **SRS** — spaced repetition system

---

## 🧱 Storage and platform short forms

- **DB** — operational database
- **PG** — PostgreSQL
- **OBJ** — object storage
- **VEC** — vector index or vector search layer
- **GRAPH** — graph store or graph service
- **CACHE** — cache layer
- **QUEUE** — async queue layer
- **EXP** — experiment tracking
- **EVAL** — evaluation pipeline or result set

---

## ☁️ Provider short forms

- **GCP** — Google Cloud Platform
- **GW** — Google Workspace
- **GH** — GitHub
- **SB** — Supabase platform
- **SBDB** — Supabase-hosted Postgres when that distinction matters
- **B2** — Backblaze B2
- **ZP** — Zuplo
- **N4J** — Neo4j
- **LF** — Langfuse
- **MLF** — MLflow
- **MF** — Metaflow
- **LC** — LangChain
- **LG** — LangGraph
- **PT** — PyTorch

---

## 🧭 File and module examples

Prefer generic file names in the core domain:
- `db_store.py`
- `auth_port.ts`
- `graph_rank.py`
- `trace_emit.ts`
- `eval_score.py`

Use provider names only in adapters or deploy files:
- `adapters/db/sb.py`
- `adapters/obj/b2.py`
- `adapters/graph/n4j.py`
- `infra/gcp/cloudrun/api.yaml`

---

## 📏 Status labels

Use only these in root docs:
- planned
- scaffolded
- bootable
- integrated
- production-ready
- hardened
