# 📜 Auth

## 🧩 Purpose

This document defines the shared authentication, session, identity, and sign-in boundary for the platform.

This file is the source of truth for:

- the sign-in methods the product supports
- how provider-specific auth stays behind unbranded adapters
- how browser-safe auth differs from server-only identity verification
- how session continuity must work across extension and web surfaces
- why password management is intentionally out of scope for the platform

This file does **not** define sprint execution sequencing, deploy topology, or provider-specific runtime implementation details. Those belong in:

- `docs/planning/MASTER.md`
- `docs/planning/sprint-001/d2-runtime.md`
- `docs/infra.md`
- `docs/packages.md`

---

## 🧭 Auth thesis

SynaWeave should not manage user passwords directly.

The platform auth model is intentionally passwordless and adapter-first:

- browser-safe sign-in only in `apps/web` and `apps/extension`
- server-side session verification only in `apps/api` and `apps/ingest`
- provider-specific wiring isolated at runtime adapter edges
- shared contracts and config remain provider-neutral

This reduces password-handling breach exposure, keeps the auth seam replaceable, and preserves flexibility as the product scales.

---

## 🔐 Supported sign-in methods

The current planned sign-in methods are:

- federated sign-in through OAuth 2.0 / OpenID Connect
- passwordless email magic link
- passkey sign-in through WebAuthn

Current target social and ecosystem providers behind the federated adapter seam:

- Google
- Apple
- LinkedIn
- GitHub

These provider names are runtime concerns only. Shared contracts must model them as normalized methods and connection aliases rather than domain-level provider types.

---

## 🌐 OAuth 2.0 and OIDC policy

Yes, the federated sign-in path is planned around OAuth 2.0 and OpenID Connect.

Rules:

- browser sign-in flows must use PKCE where applicable
- OAuth/OIDC claims must be normalized before they reach shared contracts
- provider-specific token or claim shapes must not leak into `packages/contracts`
- the API must verify identity through a server-side adapter boundary, not by trusting browser UI state alone
- the same verified user identity must be visible across extension and web surfaces

The shared auth method vocabulary remains:

- `federated_oidc`
- `email_link`
- `passkey`

---

## 🧱 Adapter boundary rules

Provider implementations must stay behind unbranded adapters.

Shared vocabulary should use:

- method
- session
- identity
- connection
- issuer
- adapter
- verification

Shared vocabulary must not use:

- provider-branded method names
- vendor SDK response types
- raw OAuth claim bags as public contract types

That means shared code can describe a connection or federated method without hardcoding Google, Apple, LinkedIn, GitHub, or any future provider into the domain boundary.

---

## 🪟 Browser and server auth split

### 🪟 Browser-safe boundary

Allowed in browser surfaces:

- public auth base URL
- redirect base URL
- allowed auth methods
- connection hints or aliases that are safe to expose
- publishable auth keys only when the runtime requires them

Forbidden in browser surfaces:

- service-role keys
- signing secrets
- admin keys
- provider client secrets
- privileged issuer-verification credentials

### ⚙️ Server-only boundary

Allowed in backend surfaces:

- issuer-verification settings
- JWKS lookup configuration
- audience checks
- privileged service credentials where required
- adapter-side provider secret material

---

## 🔁 Session continuity contract

The minimum honest runtime proof is:

1. a user signs in
2. the web shell resolves that identity
3. the extension resolves that same identity
4. the API verifies that identity independently
5. one durable user-scoped action succeeds

If any surface uses local-only identity state without server verification, the auth system is not complete enough for D2.

---

## 📦 Shared code ownership

The shared auth seam is split like this:

- `packages/contracts/auth/` owns provider-neutral auth contracts
- `packages/config/auth/` owns browser-safe versus server-only TypeScript config types
- app-local runtime folders own real provider adapters later

This keeps the repo ready for provider swaps without redesigning the shared contract layer.

---

## ✅ Implementation implications

Before real runtime code lands, the repo should at minimum keep these truths in place:

- shared auth contracts are provider-neutral
- browser-safe config is separated from server-only config
- no password-management path is introduced
- OAuth 2.0 / OIDC remains normalized behind the federated adapter seam
- magic link and passkey remain first-class methods in the shared contract vocabulary
