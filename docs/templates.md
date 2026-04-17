# 📜 Templates

## 🧩 Purpose

This document defines the repository template system used to keep recurring documentation DRY, technically precise, and reviewable.

This file is the source of truth for:

- which template families exist
- which template files are required now
- when contributors must reuse a template instead of inventing a new document shape
- how templates relate to owner docs, planning, ADRs, and verification

This file does **not** redefine the technical rules owned by other docs. Templates must point back to those owner docs instead of copying policy prose.

Owner docs remain:

- `docs/planning/MASTER.md` for planning hierarchy and file rules
- `docs/adrs.md` for ADR policy and decision structure
- `docs/testing.md` for testing taxonomy and verification expectations
- `docs/legend.md` for shared abbreviations and approved short forms

---

## 🧭 Template thesis

Templates exist to standardize recurring document mechanics without creating a second governance surface.

Each template must do three jobs only:

1. keep required sections visible
2. keep build-agent handoff targets explicit
3. keep readers pointed at the owning doc for durable rules

Templates must **not**:

- duplicate owner-doc policy text verbatim
- become generic boilerplate for artifacts the repo does not actually use
- hide technical uncertainty behind fixed headings
- create a parallel planning, ADR, or testing standard outside the root docs spine

---

## 📦 Template system contract

The template system lives under:

```text
docs/templates/
```

Required family folders:

```text
docs/templates/
├─ planning/
├─ adrs/
├─ specs/
└─ tests/
```

Required template files in Sprint 1:

```text
docs/templates/code-tldr.md
docs/templates/planning/sprint-overview.md
docs/templates/planning/deliverable.md
docs/templates/adrs/sprint-adr.md
docs/templates/specs/contract-spec.md
docs/templates/tests/verification-plan.md
```

No nested `README.md` files should exist under `docs/` or elsewhere in the repo. Directory-level explanation for templates stays here in the root docs spine so the repository keeps a single top-level README and a DRY canonical documentation surface.

These files are protected because they shape recurring repo artifacts and build-agent handoff expectations.

---

## 📏 Template design rules

- template filenames must stay semantic and concise
- templates must remain markdown unless the artifact family requires another format
- every section in a template must map to a real review or delivery need
- templates must link to owner docs where durable rules live
- template examples may use placeholders, but placeholders must be implementation-facing, not vague prose fillers
- templates must prefer exact targets, invariants, dependencies, and verification over motivational language
- if a recurring artifact needs a new section, update the template and the owning doc together when needed

---

## 🗂️ Active template families

### 🛣️ Planning templates

Purpose:

- standardize sprint and deliverable packets for build-agent execution
- keep outcome, scope, dependency, and verification sections stable across sprints

Required files:

- `docs/templates/planning/sprint-overview.md`
- `docs/templates/planning/deliverable.md`

Planning templates must preserve:

- repo-grounded current state
- explicit outcome and in-scope work
- frozen decisions inherited from owner docs and ADRs
- task breakdown with exact targets
- dependency order and safe parallelism limits
- verification gates and non-goals
- handoff notes for the next implementation lane

### 📜 ADR templates

Purpose:

- standardize sprint-level architectural decision ledgers
- keep decisions readable in plain English without losing technical precision

Required files:

- `docs/templates/adrs/sprint-adr.md`

ADR templates must preserve:

- sprint scope reference
- decision index
- one repeatable decision block shape
- superseded, revised, and deferred decision handling
- direct links back to governed files and affected planning docs

### 🧱 Code-header templates

Purpose:

- standardize mandatory TL;DR file headers for governed Python, TypeScript, JavaScript, YAML, TOML, shell, and dotenv surfaces
- keep implementation intent, exports, and consumer context explicit before code begins

Required files:

- `docs/templates/code-tldr.md`

Code-header templates must preserve:

- `TL;DR  -->` summary line
- later extension notes
- current role notes
- explicit exports section
- explicit consumed-by section
- the wrapper notes required by each language family
- one-line local intent comments outside the TL;DR block

### 🧾 Spec templates

Purpose:

- standardize reusable technical specs for cross-surface contracts before implementation spreads

Required files:

- `docs/templates/specs/contract-spec.md`

Spec templates must preserve:

- boundary owner
- contract inputs, outputs, invariants, and failure modes
- versioning and compatibility expectations
- observability and rollback implications
- links to affected code, tests, and runtime consumers

### ✅ Verification templates

Purpose:

- standardize reusable verification packets for cross-surface readiness, not one-off logs

Required files:

- `docs/templates/tests/verification-plan.md`

Verification templates must preserve:

- objective and scope
- preconditions and fixtures
- execution commands and evidence outputs
- pass, fail, and regression interpretation
- ownership of follow-up work when checks fail

---

## 🎯 When template reuse is mandatory

Reuse a template when creating or materially reshaping:

- a sprint overview
- a deliverable packet
- a sprint ADR ledger
- a reusable contract or boundary spec
- a reusable verification or readiness packet

Do **not** create a new shape first and promise to template it later. If the artifact is clearly recurring, start from the template.

One-off scratch notes, temporary debugging notes, and throwaway local analysis are not template-governed artifacts.

---

## 🔄 Template maintenance rules

Update the owning template when:

- two or more artifacts in the same family need the same new section
- a build-agent handoff repeatedly misses the same category of information
- verification expectations for that artifact family become part of normal review
- a governing owner doc changes the minimum required structure

If a template change alters durable planning, ADR, or verification expectations, update the owner doc in the same change.

---

## 📚 Relationship to verification

`tools/verify/docs.py` enforces the existence of the required template families and required template files.

That enforcement is intentionally structural, not semantic.
Human review and owner docs still decide whether a specific filled-in artifact is technically sound.
