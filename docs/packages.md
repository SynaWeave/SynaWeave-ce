# 📜 Packages

## 🧩 Purpose

This document defines the ownership boundaries, allowed consumers, dependency rules, and maturity expectations for every shared package under `packages/`.

This file is the source of truth for:
- what each shared package is responsible for
- which apps and runtimes may consume each package
- which dependency directions are allowed
- what must never be placed in a shared package
- how shared package changes must be tested and documented

This file does **not** define app runtime behavior, deployment topology, or sprint execution details. Those belong in:
- `docs/apps.md`
- `docs/infra.md`
- `docs/planning/MASTER.md`
- sprint planning files under `docs/planning/`

---

## 🧭 Package maturity labels

Every package described here must use one of these states only:

- **planned** — specified but not yet scaffolded
- **scaffolded** — folder and baseline structure exist, but not yet meaningfully used
- **bootable** — package builds and can be consumed, but integration is minimal
- **integrated** — consumed in real application flows
- **production-ready** — safe for live-user scope
- **hardened** — stable, tested, documented, observable where relevant, and operationally mature

No other maturity labels should be used in package documentation.

---

## 📦 Package inventory

The `packages/` folder contains these shared boundaries:

- `packages/ui`
- `packages/tokens`
- `packages/contracts`
- `packages/prompts`
- `packages/config`

Each shared package must own one coherent concern. If a package starts mixing unrelated responsibilities, it must be split rather than allowed to drift into a catch-all.

---

## 🧱 Shared-package rules

These rules apply to every package under `packages/`.

### ✅ Required rules
- package names must be semantic only
- package responsibilities must be narrow and explicit
- public exports must be intentional
- every package must have a clear consumer list
- every package must have tests appropriate to its role
- every package must be documented in this file
- every package must avoid provider-specific naming in its public contract

### 🚫 Forbidden rules
- no app-specific business logic in shared packages
- no direct runtime secrets in shared packages
- no hidden side effects at package import time
- no browser-only assumptions in packages used by multiple runtimes
- no provider SDK coupling in contracts package
- no duplicate design-token definitions outside `packages/tokens`

---

## 🎨 `packages/ui`

### 🧩 Purpose
`packages/ui` contains shared presentational primitives and UI composition helpers used by multiple frontend surfaces.

### 🎯 Responsibilities
- primitive UI components
- token-consuming UI building blocks
- accessible presentational wrappers
- layout helpers
- reusable visual states and shell patterns

### 🚫 Non-responsibilities
- product-specific flashcard components
- feature-specific business workflows
- direct data fetching
- auth/session logic
- provider SDK usage
- ad hoc token definitions

### ✅ Allowed consumers
- `apps/web`
- `apps/extension`

### ⛔ Forbidden consumers
- backend Python services
- job runtimes
- any app that needs business logic rather than presentation

### 🔗 Allowed dependencies
- `packages/tokens`
- `packages/contracts` only for narrow presentational typing if absolutely necessary

### ⛔ Forbidden dependencies
- runtime-specific app code
- direct browser-extension APIs
- direct backend SDKs
- provider clients
- app-local state stores

### 📏 Package rules
- components must consume tokens, not raw literals
- components must be keyboard-accessible by default
- components must support shared theme behavior
- no component may fetch data directly
- no component may hardcode product-specific copy that belongs in a feature surface

### ✅ Testing expectations
Changes to `packages/ui` must update:
- `testing/component/`
- `testing/ui/` when behavior affects full journeys
- `testing/accessibility/` when semantics or structure change

### 📚 Current target maturity
Sprint 1 target: **bootable**  
Sprint 2 target: **integrated**  
Sprint 5 target: **production-ready**

---

## 🌓 `packages/tokens`

### 🧩 Purpose
`packages/tokens` is the single source of truth for design tokens across the entire product.

### 🎯 Responsibilities
- token source files
- token layer definitions
- token transforms
- compiled token outputs
- theme mappings
- token documentation inputs

### 🚫 Non-responsibilities
- component implementation
- feature-specific styling logic
- ad hoc CSS patches
- app-only theme systems
- business logic

### ✅ Allowed consumers
- `packages/ui`
- `apps/web`
- `apps/extension`

### 🔗 Allowed dependencies
- token build tooling only
- no product-runtime dependencies

### ⛔ Forbidden dependencies
- `packages/ui`
- app-local feature code
- provider SDKs
- runtime-specific auth/config logic

### 📏 Token rules
- token-first design is mandatory
- no competing token system may exist in any app
- token layers are fixed to:
  - base
  - semantic
  - component
- outputs must include:
  - CSS variables
  - TypeScript types/maps
  - JSON output for documentation

### ✅ Testing expectations
Changes to `packages/tokens` must update:
- token build tests
- relevant unit tests
- `testing/component/` if token semantics affect primitives
- `testing/accessibility/` if contrast or state visibility changes
- docs examples in `docs/design-system.md`

### 📚 Current target maturity
Sprint 1 target: **bootable**  
Sprint 2 target: **integrated**  
Sprint 5 target: **hardened**

---

## 🧾 `packages/contracts`

### 🧩 Purpose
`packages/contracts` contains shared serializable contracts for cross-surface data exchange.

### 🎯 Responsibilities
- request and response schemas
- runtime message schemas
- API envelope shapes
- versioned payload contracts
- event contract shapes
- adapter-facing public contract definitions on the TypeScript side
- normalized auth, identity, and session contracts that stay provider-neutral in shared code

### 🚫 Non-responsibilities
- provider implementations
- business logic
- transport-specific logic
- UI rendering logic
- secret handling
- Python-only internal model code
- provider-branded auth method names or raw vendor claim shapes in public exports

### ✅ Allowed consumers
- `apps/extension`
- `apps/web`
- `apps/api`
- future TS-based tooling or helpers
- documentation and contract tests

### 🔗 Allowed dependencies
- schema/validation tooling only
- no provider SDKs
- no app-local runtime code

### ⛔ Forbidden dependencies
- `packages/ui`
- app-specific feature code
- direct provider SDKs
- direct browser APIs
- hardcoded vendor response shapes in public contracts

### 📏 Contract rules
- all public API payloads must be versionable
- all extension runtime messages must be versionable
- all contract changes must be explicit and documented
- envelope structure must stay stable unless changed by ADR-backed decision
- contracts must describe serializable shapes only
- provider-specific error shapes must be normalized before reaching public contracts
- auth contracts must prefer method, session, identity, connection, issuer, and adapter vocabulary over provider brands
- federated sign-in contracts must normalize OAuth 2.0 / OIDC providers behind shared method and connection shapes

### ✅ Testing expectations
Changes to `packages/contracts` must update:
- `testing/contract/`
- any affected API or message smoke tests
- relevant integration or e2e tests
- any docs sections describing affected public shapes
- auth contract scaffolds must verify that provider names stay out of shared exports

### 📚 Current target maturity
Sprint 1 target: **bootable**  
Sprint 2 target: **integrated**  
Sprint 5 target: **hardened**

### 🔐 Current auth scaffold note
Sprint 1 now reserves provider-neutral auth scaffolds under `packages/contracts/auth/` and `packages/config/auth/`.

Those scaffolds intentionally model:
- `federated_oidc` for Google, Apple, LinkedIn, GitHub, and future OIDC-compatible providers
- `email_link` for magic-link sign-in
- `passkey` for WebAuthn-backed sign-in

Shared contracts must not expose provider brands directly. Provider-specific mapping belongs in future runtime adapters under the app boundaries.

---

## 🧠 `packages/prompts`

### 🧩 Purpose
`packages/prompts` contains reusable prompt assets, prompt metadata, and prompt organization primitives for AI-facing workflows.

### 🎯 Responsibilities
- prompt text assets
- prompt templates
- prompt metadata
- prompt naming conventions
- prompt-version references
- shared reusable non-provider-specific prompt building blocks

### 🚫 Non-responsibilities
- model invocation logic
- retrieval execution logic
- provider SDK logic
- evaluation execution
- hidden prompt strings embedded inside app code

### ✅ Allowed consumers
- `apps/api`
- `apps/mcp`
- `apps/ml`
- `apps/eval`
- documentation surfaces when appropriate

### 🔗 Allowed dependencies
- `packages/contracts` only if prompt metadata needs typed cross-surface structures
- static assets and safe formatting utilities only

### ⛔ Forbidden dependencies
- provider SDKs
- direct secrets/config reads
- UI packages
- business logic that belongs in services

### 📏 Prompt rules
- prompts must have stable names
- prompt namespaces must be documented
- prompt changes must be traceable
- prompt text may not be hidden inside unrelated service files if it belongs in the shared prompt library
- provider-specific formatting must happen at the adapter edge, not in the package core

### ✅ Testing expectations
Changes to `packages/prompts` must update:
- `testing/evals/`
- any synthetic prompt smoke checks
- docs or naming references if prompt namespaces change

### 📚 Current target maturity
Sprint 1 target: **scaffolded**  
Sprint 4 target: **integrated**  
Sprint 5 target: **production-ready**

---

## ⚙️ `packages/config`

### 🧩 Purpose
`packages/config` contains the TypeScript-side configuration contract and runtime config-loading utilities.

### 🎯 Responsibilities
- validated config loading
- typed config accessors
- environment separation
- config categorization
- browser-safe versus server-only key separation for TS runtimes

### 🚫 Non-responsibilities
- secret storage
- direct deployment logic
- Python runtime config ownership
- provider business logic
- app-specific feature flags hardcoded outside the shared config model

### ✅ Allowed consumers
- `apps/extension`
- `apps/web`
- TS-based support tooling if added later

### 🔗 Allowed dependencies
- validation tooling
- environment parsing helpers

### ⛔ Forbidden dependencies
- UI packages
- provider SDKs
- direct browser-extension API logic
- direct backend transport code

### 📏 Config rules
- no TS runtime reads raw environment variables outside this package
- keys must be classified by:
  - purpose
  - required or optional
  - secret or non-secret
  - local/staging/prod scope
- browser-safe config must be explicitly separated from server-only config
- `.env.example` must stay in sync with the config surface
- auth config must keep browser-safe connection hints and redirect settings separate from privileged issuer-verification settings

### ✅ Testing expectations
Changes to `packages/config` must update:
- unit tests
- config validation tests
- security smoke checks if secret boundaries change
- `docs/operations.md` and `CONTRIBUTING.md` if setup changes

### 📚 Current target maturity
Sprint 1 target: **bootable**  
Sprint 2 target: **integrated**  
Sprint 5 target: **hardened**

---

## 🔄 Allowed dependency directions

This section defines which package-to-package imports are allowed.

### ✅ Allowed directions
- `packages/ui` → `packages/tokens`
- `packages/ui` → `packages/contracts` only when strictly needed for presentational typing
- `packages/prompts` → `packages/contracts` if shared metadata typing is required
- apps may depend on any approved shared package appropriate to their runtime

### 🚫 Forbidden directions
- `packages/tokens` → `packages/ui`
- `packages/contracts` → `packages/ui`
- `packages/contracts` → provider SDKs
- `packages/config` → app-local code
- any shared package → sibling app internals
- any shared package → provider-specific implementation modules

### 📏 Dependency rule of thumb
Shared packages may depend “down” into more primitive shared concerns, but never “up” into app-specific or provider-specific code.

---

## 🧠 Type ownership rules

Type ownership must remain clear.

### ✅ Type ownership
- visual values and theming types belong in `packages/tokens`
- primitive component props belong in `packages/ui`
- serializable cross-surface contracts belong in `packages/contracts`
- prompt metadata belongs in `packages/prompts`
- TypeScript runtime config types belong in `packages/config`

### 🚫 Forbidden type duplication
- no duplicate API envelope types in app-local folders
- no duplicate token types in app-local styling files
- no duplicate config schemas scattered through apps
- no provider response types leaking into public contract types

---

## 🔐 Security and provider-boundary rules

Shared packages must preserve provider optionality and safe secret handling.

### 🔐 Rules
- no secret values stored in shared packages
- no provider-specific names in public shared-package contracts
- no service-role or privileged runtime assumptions in packages consumed by browser surfaces
- any package that influences config or contracts must be reviewed for secret-boundary impact

If a package change risks exposing provider details into the core domain, the change must be rejected or moved to an adapter boundary.

---

## 👀 Observability and testing implications

Shared packages still affect quality systems even when they do not emit runtime telemetry themselves.

### 👀 Observability implications
- `packages/contracts` changes affect trace and log payload interpretation
- `packages/prompts` changes affect Langfuse trace and eval semantics
- `packages/config` changes affect runtime observability configuration
- `packages/tokens` and `packages/ui` changes affect accessibility and UI smoke baselines

### ✅ Testing implications
A package change is incomplete unless:
- relevant package-level tests are updated
- relevant root test layers are updated
- docs are updated if public package behavior changed
- sprint plan is updated if the package change alters deliverable scope or verification

---

## 📏 Package-level definition of done

A shared-package change is incomplete unless all of the following are true:

- package responsibility remains clear
- allowed dependency rules are still respected
- public exports are intentional and documented
- tests cover the changed behavior
- affected docs are updated
- affected apps still consume the package through approved boundaries
- no provider-specific coupling leaked into the package contract

---

## 📜 Relationship to other root docs

This file works with:

- `docs/apps.md` for app ownership
- `docs/python.md` for Python shared-module boundaries
- `docs/testing.md` for test-layer expectations
- `docs/design-system.md` for token and UI-system rules
- `docs/architecture.md` for platform-wide boundary design
- `docs/operations.md` for current maturity truth

This file should stay focused on **shared package ownership and dependency rules**.
