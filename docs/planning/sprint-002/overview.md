# 🛣️ Sprint 2 — Overview

## 1. 🧭 TL;DR

Sprint 2 is a **post-Sprint-1 team placeholder**. It is **not** the active execution packet yet.

This file exists so the team has a durable, governed starting structure ready as soon as Sprint 1 closes. Until Sprint 1 exit criteria, ADR updates, and repo reality confirm the next bounded work, this document should be read as **planning scaffolding only**, not as authorization to start implementation.

## 2. 📌 Sprint purpose

- preserve a stable handoff point after Sprint 1 completes
- reserve the governed planning slot for Sprint 2 without inventing work early
- give the team one canonical place to refine Sprint 2 scope once branch truth exists
- prevent parallel planning drift across ad hoc notes, chats, or side documents

## 3. 🔍 Repo-grounded starting point

Sprint 2 planning must start from the **actual closeout state of Sprint 1**, not from assumptions.

At activation time, this overview should be updated to reference:

- Sprint 1 exit evidence
- the current `docs/planning/MASTER.md` sequencing truth
- the matching Sprint 2 ADR in `docs/adrs/sprint-002.md`
- the real runtime, docs, verification, and contract surfaces that Sprint 1 leaves behind

Until then, the only reliable statement is:

- Sprint 1 defines the current active execution packet
- Sprint 2 scope is intentionally deferred
- no Sprint 2 deliverable should claim authority before Sprint 1 closeout

## 4. 🎯 Sprint-wide success definition

Sprint 2 planning is ready to activate only when all of the following are true:

- Sprint 1 is complete by its own sprint and deliverable exit criteria
- any Sprint-2-shaping decisions are recorded in the owning ADR or root docs
- Sprint 2 scope names concrete deliverables instead of placeholder themes
- each planned deliverable has a bounded objective, affected surfaces, and proof expectations
- the overview reflects current branch truth rather than historical intent

## 5. 🏗️ Sprint architecture objective

**Placeholder only.** The architecture objective for Sprint 2 must be written from the repository state that exists after Sprint 1.

When this packet becomes active, replace this section with:

- runtime surfaces affected
- contract or data surfaces affected
- proof and observability surfaces affected
- boundaries that remain frozen from Sprint 1 and governing docs

## 6. 🧱 Sprint-wide frozen decisions

The following remain frozen unless an updated ADR or root owner doc explicitly changes them:

- root `docs/` remains the only canonical technical documentation surface
- recurring planning artifacts continue to reuse `docs/templates/`
- planning authority remains `MASTER.md` → sprint overview → deliverable files
- no side planning system, duplicate checklist set, or second docs runtime is introduced
- Sprint 2 must inherit Sprint 1 contracts unless a durable decision record supersedes them

## 7. 🔄 Sprint dependency model

Sprint 2 depends on Sprint 1 closeout.

Minimum dependency chain:

1. Sprint 1 deliverables complete
2. Sprint 1 ADR and owner docs reflect final shared understanding
3. Sprint 2 ADR captures any new decisions required for execution
4. Sprint 2 overview is upgraded from placeholder to active packet
5. Sprint 2 deliverable files are created or finalized

Stop conditions:

- Sprint 1 is still open
- required architecture decisions are still unresolved
- deliverable boundaries cannot yet be stated honestly
- proof expectations are still speculative

## 8. 🔀 Safe parallelism

Safe to do now:

- reserve the Sprint 2 folder and overview location
- keep this placeholder aligned with repo governance and template shape
- note activation prerequisites

Not safe to do yet:

- treat placeholder content as approved scope
- open implementation work from this file alone
- create detailed deliverable packets that guess at post-S1 reality
- duplicate planning rules already owned by `MASTER.md`, templates, or governance docs

## 9. ✅ Exit criteria

This file stops being a placeholder only when:

- this overview is rewritten against real post-Sprint-1 branch truth
- `docs/adrs/sprint-002.md` exists and matches the execution intent
- Sprint 2 deliverable files exist using the standard planning template shape
- success criteria include exact proof, verification, and docs-update expectations
- any changed shared understanding is reflected in the owning root docs, not repeated here

## 10. 📂 Governed files

This placeholder currently governs only the Sprint 2 planning entry points:

- `docs/planning/sprint-002/overview.md`
- future Sprint 2 deliverable files under `docs/planning/sprint-002/`
- `docs/adrs/sprint-002.md`
- `docs/planning/MASTER.md` for sprint sequencing authority
- `docs/templates/planning/sprint-overview.md`
- `docs/templates/planning/deliverable.md`

## 11. 🧩 Handoff note

When Sprint 1 completes, the team should update this file in one pass:

- restate the actual starting point left by Sprint 1
- name the concrete Sprint 2 objective
- define the deliverables
- lock the success criteria and proof requirements
- remove language that marks this document as a placeholder

Until that handoff occurs, this file is intentionally durable but non-executable.
