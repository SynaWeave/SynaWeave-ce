# 🛣️ Sprint <n> — Overview

## 1. 🧭 TL;DR

State the sprint objective in 3-5 sentences.
Name the repo reality this sprint starts from, the risk it removes, and the proof it must leave behind.

## 2. 📌 Sprint purpose

- primary program objective
- main delivery risk being removed
- what later work is unblocked by this sprint

## 3. 🔍 Repo-grounded starting point

- current branch truth
- existing runtime, docs, and control surfaces relevant to the sprint
- gaps that still prevent honest completion claims

Do not describe historical or public-main state as current branch truth without labeling it explicitly as historical context.

## 4. 🎯 Sprint-wide success definition

- required outcomes by boundary or quality dimension
- measurable proof that the sprint changed repo or runtime truth
- explicit incomplete conditions

## 5. 🏗️ Sprint architecture objective

- runtime surfaces affected
- data or contract surfaces affected
- proof and observability surfaces affected
- boundaries that must remain frozen

## 6. 🧱 Sprint-wide frozen decisions

Link back to the owning ADR or root owner doc instead of re-copying policy text.

- docs and planning invariants
- runtime invariants
- quality and security invariants
- naming or template invariants when relevant

## 7. 🔄 Sprint dependency model

- serial truths that must be locked first
- downstream deliverables that depend on them
- known blockers and stop conditions

## 8. 🔀 Safe parallelism

- workstreams safe to split
- why the split is safe
- shared files or boundaries that remain serialized

## 9. ✅ Exit criteria

- exact commands
- exact docs or ADR updates required
- exact runtime or proof outputs required

## 10. 📂 Governed files

List the planning packets, owner docs, templates, verifier files, and runtime boundaries the sprint governs directly.

## 11. 🧩 Handoff note

- next bounded starting point
- assumptions later work may inherit without reopening this sprint
- unresolved items that are intentionally deferred
