# 🚚 Sprint 1 — Deliverable 1 — Foundation

## 1. 🧭 TL;DR

This deliverable finishes the repository reset from prototype-era extension roots into an enforceable governed monorepo foundation.

The repo is no longer only a flat extension prototype. The governed root shape, root `docs/` spine, root `testing/` taxonomy, repo verifier, hooks, workflows, and protected-path surfaces already exist on this branch. Foundation now means tightening those surfaces until the documented contract, the working tree, and the automated checks all agree.

This deliverable is complete only when:

- the repo reads as a governed platform from the root
- root `docs/` is the only canonical technical documentation surface
- planning authority is singular and DRY
- repo controls and CI checks enforce the documented baseline
- reserved runtime and shared-module homes are present and accurate
- Sprint 1 runtime and quality work can proceed without redefining structure

---

## 2. 📌 Deliverable outcome

Foundation establishes one durable answer for:

- where code lives
- where docs live
- where planning lives
- how changes are reviewed
- how protected paths are enforced
- how build agents get exact targets before implementation expands

This deliverable does not ship product features. It freezes the repository contract that later deliverables must inherit.

---

## 3. 🔍 Current repo baseline

### 3.1 ✅ Shape already established

The current branch already contains the intended top-level domains:

- `apps/`
- `packages/`
- `python/`
- `infra/`
- `testing/`
- `tools/`
- `docs/`
- `.github/`

It also already includes reserved homes for the first planned runtime map:

- `apps/extension`
- `apps/web`
- `apps/api`
- `apps/ingest`
- `apps/mcp`
- `apps/ml`
- `apps/eval`

The reserved homes for web, API, ingest, MCP, ML, and evaluation are Deliverable 1 scaffold placeholders only.
They establish governed runtime boundaries without claiming bootable runtimes yet.

### 3.2 ✅ Control surfaces already present

The current branch already includes the core repo-control surfaces:

- `AGENTS.md`
- `GOVERNANCE.md`
- `CONTRIBUTING.md`
- `.github/CODEOWNERS`
- `.github/pull_request_template.md`
- `.github/workflows/`
- `tools/verify/`
- `tools/hooks/`

### 3.3 ⚠️ Closeout-sensitive truth gaps

Foundation closeout must stay honest about two different kinds of evidence:

- repo-contained controls can be closed only when docs, CODEOWNERS, hooks, workflows, templates, and verifier behavior agree and pass local verification
- GitHub-hosted settings such as rulesets, branch protection, required checks, and secret-scanning posture can be documented here, but not claimed as enforced unless the GitHub-side configuration is separately confirmed
- planning and owner-doc language must describe the current branch reality instead of preserving stale prototype-era drift

Foundation closes the repo-contained drift and records any still-external hosting confirmation as an explicit dependency rather than hiding it inside inflated status language.

---

## 4. 🎯 Success definition

Foundation succeeds only if a reviewer can answer all of the following from the repo itself without chat archaeology:

- what the canonical docs surface is
- what the canonical planning surface is
- what top-level domains are mandatory
- which files are protected
- which checks must pass before merge
- which runtime homes are reserved now
- which docs own which kinds of truth
- what Sprint 1 runtime work is allowed to assume

If those answers still require inference from stale planning text or unwritten convention, Foundation is incomplete.

---

## 5. 📏 Frozen decisions

### 5.1 📚 Canonical docs surface

- root `docs/` is the only canonical technical documentation surface
- GitHub Pages may publish static output from root `docs/`, but does not create a second docs runtime
- no app-local docs home may compete with root `docs/`

### 5.2 🛣️ Canonical planning surface

- `docs/planning/MASTER.md` is the only canonical planning-rules owner
- `docs/planning/sprint-###/` holds sprint execution files
- `docs/planning.md` may exist only as a pointer, not as a second planning authority

### 5.3 🧱 Repository topology

- the repo stays shallow and semantic
- top-level domains correspond to durable responsibilities
- no deep nesting past three sub-folder levels is introduced without justification
- reusable logic belongs in `packages/` or `python/`, not app entrypoints

### 5.4 🔐 Governance and merge controls

- governance is complete in Sprint 1
- protected paths are enforced in repo-contained surfaces through docs, CODEOWNERS, workflows, hooks, and verifier rules
- PRs must call out sprint, deliverable, task, verification, and protected-path impact
- admin bypass remains an explicit GitHub-side posture, not an undocumented habit
- GitHub-hosted enforcement remains an expected posture until the hosted settings themselves are confirmed

### 5.5 🧾 Template system

- `docs/templates/` is the only reusable template home for recurring planning, ADR, spec, and verification artifacts
- templates must point to owner docs instead of duplicating policy prose
- template changes are protected-path changes because they reshape future governed artifacts

### 5.6 ✏️ Naming and legend

- identifiers stay semantic and minimal
- shared abbreviations are tracked only in `docs/legend.md`
- commit messages and ADR prose prefer plain English over raw identifiers
- provider names do not become core domain concepts

### 5.7 ✅ Quality baseline

- repo-wide linting, typechecking, and tests are mandatory for non-generated code
- `python3 -m tools.verify.main` is the baseline repo-control gate
- matching CI workflows must run the same repo-control expectations
- test and workflow enforcement must expand before feature scope expands

---

## 6. 🗂️ Target structure

### 6.1 🧱 Top-level target

```text
repo/
├─ apps/
├─ packages/
├─ python/
├─ infra/
├─ docs/
├─ testing/
├─ tools/
├─ .github/
├─ README.md
├─ LICENSE
├─ .env.example
├─ package.json
└─ pyproject.toml
```

### 6.2 📚 Canonical docs target

```text
docs/
├─ adrs/
├─ planning/
│  ├─ MASTER.md
│  └─ sprint-###/
├─ templates/
├─ architecture.md
├─ apps.md
├─ packages.md
├─ python.md
├─ infra.md
├─ testing.md
├─ operations.md
├─ legend.md
├─ adrs.md
├─ design-system.md
└─ planning.md
```

`docs/planning.md` remains a pointer only.
`docs/templates/` remains the only reusable template home.

### 6.3 🧪 Testing target

```text
testing/
├─ unit/
├─ component/
├─ integration/
├─ contract/
├─ ui/
├─ e2e/
├─ security/
├─ performance/
├─ accessibility/
└─ evals/
```

---

## 7. 🎟️ Task breakdown

### S1-D1-T1 — truth alignment

- align repo verification with the current documented governance baseline
- remove stale assumptions that block local verification for non-structural reasons
- keep governance checks strict, but grounded in current repo reality

### S1-D1-T2 — planning authority cleanup

- reduce `docs/planning.md` to a pointer
- point owner docs to `docs/planning/MASTER.md`
- remove dual-source planning drift

### S1-D1-T3 — docs spine cleanup

- remove stale references to a docs app or second docs runtime
- keep all canonical docs authority rooted under `docs/`
- keep GitHub Pages framed as publication only

### S1-D1-T4 — control-surface alignment

- align governance docs, PR template, CODEOWNERS, hooks, and workflows around one repo-control contract
- confirm protected-path ownership is explicit
- keep admin bypass documented as a GitHub-side control

### S1-D1-T5 — template system hardening

- add reusable planning, ADR, spec, and verification templates under `docs/templates/`
- keep template sections technical and handoff-oriented
- point templates back to owner docs instead of cloning repo rules

### S1-D1-T6 — verifier and test hardening

- expand repo-control tests as rules tighten
- keep verifier expectations paired with unit tests
- ensure CI and local commands stay meaningfully aligned

### S1-D1-T7 — D2 handoff readiness

- leave runtime homes and owner docs ready for web, API, ingest, and extension implementation
- leave the quality taxonomy ready for D3 expansion
- document only what D2 and D3 need, without duplicating owner docs

---

## 8. ✅ Verification gates

Foundation cannot close unless all of the following are true:

- `python3 -m tools.verify.main` passes
- root governance docs agree on canonical planning and docs ownership
- owner docs point to `docs/planning/MASTER.md` instead of treating `docs/planning.md` as a second authority
- no root doc implies a docs app or second canonical docs runtime
- protected-path controls remain present, aligned, and readable in repo-contained surfaces
- repo-control test coverage exists for tightened verifier behavior
- D1 closeout text distinguishes locally verified repo controls from GitHub-hosted enforcement that still requires platform-side confirmation

---

## 9. 🚫 Non-goals

This deliverable does not:

- implement feature-complete product runtimes
- ship web or API user flows
- add a second docs runtime
- turn provider choices into domain concepts
- duplicate technical truth across multiple root docs

---

## 10. 📂 Governed files

This deliverable primarily governs:

- `AGENTS.md`
- `GOVERNANCE.md`
- `CONTRIBUTING.md`
- `.github/CODEOWNERS`
- `.github/pull_request_template.md`
- `.github/workflows/**`
- `tools/verify/**`
- `tools/hooks/**`
- `docs/templates/**`
- `docs/planning/MASTER.md`
- `docs/planning/sprint-001/d1-foundation.md`
- root owner docs under `docs/`
