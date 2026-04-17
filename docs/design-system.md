# 🎨 Design System

## 🧩 Purpose

This document defines the shared design-language contract for all user-facing and shared UI surfaces.

Design is owned once and consumed by runtime surfaces:

- token definitions in `packages/tokens`
- reusable primitives in `packages/ui`
- product presentation in `apps/extension` and `apps/web`

This document is the source of truth for:

- source of design-system ownership
- token-first implementation policy
- shared UI component expectations
- cross-surface style and accessibility rules

This document does **not** replace:

- runtime architecture (`docs/architecture.md`)
- package ownership (`docs/packages.md`)
- user journey planning (`docs/operations.md`)

---

## 🧱 Core design thesis

The design system is token-first and shared.

- one visual vocabulary for both shell surfaces
- no duplicate token systems
- no app-local token definitions for global semantics

Every shared visual layer must consume tokens rather than literals.

---

## 🗂️ Package responsibilities

### 🧩 `packages/tokens`

Responsibility:

- define design tokens in layer files
- define semantic layers where product semantics matter (`semantic`, `component`, `state`)
- provide generated artifact types when needed

Prohibited:

- app-only ad hoc color definitions
- one-off typography literals in app-only CSS or style modules

### 🧩 `packages/ui`

Responsibility:

- render primitives that consume tokens
- provide accessible defaults and semantics
- keep presentation reusable across app surfaces

Prohibited:

- business logic embedding
- direct API calls
- direct browser extension dependencies

### 🧩 `apps/extension` and `apps/web`

Responsibility:

- consume token and component contracts
- provide context-specific composition only where necessary

Prohibited:

- define global tokens used by both surfaces
- own token names that should live in shared packages

---

## 🎯 Required design layers

All shared visual design must use these layers in order:

1. base tokens: spacing, color families, typography scales, z-order
2. semantic tokens: interactive state, surface emphasis, status, warning, error
3. component tokens: buttons, cards, inputs, panel shells, command rows

Layer rules:

- layer boundaries are explicit and documented
- semantic tokens map to product meaning, not file-level usage
- component tokens never bypass semantic mappings

---

## ♿ Accessibility baseline

The design system must preserve accessibility in shared primitives and shell surfaces:

- keyboard-first navigation for focus transitions
- visible focus state in all interactive components
- role and aria semantics for reusable primitives
- color contrast checks as part of package and UI test updates

Any design primitive that changes semantics must include accessibility impact notes and tests.

---

## 🚀 Change process

When design tokens or shared component behavior change:

1. update `packages/tokens` or `packages/ui`
2. update affected docs references in `docs/design-system.md` and dependent docs
3. update at least one shared test layer:
   - `testing/component`
   - `testing/ui`
   - `testing/accessibility`

Only package-level shared updates are allowed to alter cross-surface appearance globally.

---

## 🧭 Relationship to quality

Design changes are test obligations when they affect user-visible behavior.
Minimum quality scope:

- component-level behavior: `testing/component`
- shell-level behavior: `testing/ui`
- semantic regressions: `testing/accessibility`

No design-system change is complete until these are in the verification path for the changed scope.
