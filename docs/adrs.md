# 📜 ADRs

## 🧩 Purpose

This document defines how Architectural Decision Records are created, updated, named, scoped, and maintained in this repository.

This file is the source of truth for:

* what an ADR is in this repo
* where ADRs live
* how ADRs are named
* when an ADR is required
* how ADRs relate to sprint plans and root technical docs
* how decisions are revised or superseded

This file does **not** define:

* sprint sequencing
* app ownership boundaries
* infrastructure topology
* runtime implementation details

Those belong in:

* `docs/planning/MASTER.md`
* `docs/apps.md`
* `docs/infra.md`
* `docs/architecture.md`

Use `docs/templates/adrs/sprint-adr.md` when creating or materially reshaping a sprint ADR file.

That template is the visual reference for the ADR presentation layer.

This owner doc remains the policy authority.

## 🧭 ADR thesis

ADRs exist to make major technical decisions explicit, reviewable, and durable.

An ADR should answer:

* what decision was made
* why it was made
* what alternatives were considered
* what consequences follow from it
* what later work depends on it

ADRs are not meeting notes, loose brainstorming, or vague summaries. They are decision records.

## 📦 ADR folder contract

All ADR files live under:

```text id="j1d5nm"
docs/adrs/
```

This repo uses **one ADR file per sprint**.

Examples:

```text id="scg827"
docs/adrs/sprint-001.md
docs/adrs/sprint-002.md
docs/adrs/sprint-003.md
```

The sprint ADR is the decision ledger for that sprint.

## 📏 ADR file rules

* one ADR file per sprint
* file naming must follow `sprint-###.md`
* sprint numbers must be zero-padded to 3 digits
* ADR filenames must be semantic only through the sprint number, not extra titles
* each ADR file may contain multiple decision entries
* each decision entry must be explicitly separated and titled as `### <identifier> - <plain-English title>`
* ADR files must use proper spelling and readable plain English
* ADR entries must not use wording blocked by the shared commit, PR-title, and ADR policy
* ADR entries should prefer plain English over raw code identifiers unless a folder path or external standard name is required for precision
* the decision index and decision headings must match exactly

## 🧱 ADR structure model

Each sprint ADR file must contain:

* TL;DR
* ADR guide
* current status
* decision index
* one section per major decision

### 📜 Minimum section order

A sprint ADR should follow this structure:

1. TL;DR
2. ADR guide
3. current status
4. entries

## 🎯 When an ADR is required

An ADR entry is required when any of the following happens:

* a provider choice is locked
* a runtime boundary is introduced or changed
* a major folder or repo structure rule is locked
* a testing or observability system is locked
* a deployment or hosting choice is locked
* an auth or security boundary is locked
* a major state-management or frontend-system choice is locked
* a scale seam is activated, removed, or materially revised
* a public contract or system invariant changes in a durable way
* a previous architectural decision is reversed or superseded

## 🚫 When an ADR is not required

An ADR entry is usually **not** required for:

* typo fixes
* trivial refactors with no architectural consequence
* one-off local implementation details
* temporary debugging changes
* internal code cleanup with no boundary, runtime, or contract impact
* routine dependency bumps unless they force a meaningful architectural decision

If unsure, prefer recording the decision.

## 🛣️ Relationship to sprint planning

Sprint planning files and ADRs do different jobs.

### 🛣️ Sprint planning files

Sprint planning files describe:

* what will be built
* how it will be built
* what tasks exist
* how completion is verified

### 📜 ADRs

ADRs describe:

* which architectural decisions were made
* why those decisions were chosen
* what alternatives were rejected
* what constraints follow from those decisions

### 📏 Rule

If a sprint plan says **what** and **how**, the ADR says **why**.

Both must remain aligned.

## 📚 Relationship to root technical docs

Root technical docs describe stable system truth.

ADR files describe how that truth came to be.

### 📏 Alignment rule

Whenever an ADR changes durable technical truth, the relevant root docs must also be updated.

Common examples:

* provider decision change → update `docs/architecture.md`, `docs/infra.md`, and possibly `docs/operations.md`
* testing-system decision change → update `docs/testing.md`
* design-system decision change → update `docs/design-system.md`
* app-boundary decision change → update `docs/apps.md`
* package-boundary decision change → update `docs/packages.md`
* Python-boundary decision change → update `docs/python.md`

## 🧾 Decision entry template

Each decision entry inside a sprint ADR must answer these prompts:

* ***What was built?***
* ***Why was it chosen?***
* ***What boundaries does it own?***
* ***What breaks if it changes?***
* ***What known edge cases or failure modes matter here?***
* ***Why does this work matter?***
* ***What capability does it unlock?***
* ***Why is the chosen design safer or more scalable?***
* ***What trade-off did the team accept?***

Use at least 3 concrete bullets for each prompt, and expand beyond that where needed so trade-offs and constraints stay explicit.

## 📋 Decision index rules

Each sprint ADR must begin the entries section with a decision index so readers can skim the file quickly.

The decision index should list:

* decision identifier
* short title
* current status

The index row identifier and title must exactly match the corresponding decision heading.

Example structure:

```md id="g5d8cv"
| Decision | Status |
| --- | --- |
| D1 - repo structure and docs contract | approved |
| D1-T2 - auth and session baseline | approved |
| D2 - observability stack | approved |
| D3 - state management split | approved |
```

### 📏 Identifier rules

* use stable sprint-local identifiers like `D1`, `D2`, `D3`, or deliverable-scoped forms like `D1-T2` when one deliverable contains multiple durable decisions
* do not restart numbering inside subsections
* keep identifiers stable even if a decision is later revised or superseded
* keep entries sorted newest first

## 🔄 Supersession rules

Decisions sometimes change. When they do:

* do not silently delete the old decision
* mark the old decision as `superseded` or `revised`
* add a clear note linking to the newer decision entry
* update affected sprint files and root docs
* explain what changed and why

### 📏 Rule

An ADR is a decision history, not just a snapshot of the newest belief.

## ⏳ Deferred decision rules

Some decisions may be intentionally deferred.

When that happens:

* record that the decision is deferred
* explain why it is deferred
* define what trigger will force the decision later
* link it to the expected sprint or deliverable if known

Deferred decisions should be rare and intentional, not a substitute for planning.

## 🧠 Decision quality bar

A decision entry is acceptable only if it is:

* specific
* scoped
* justified
* reviewable
* tied to consequences
* aligned with repo conventions

Bad ADR writing usually looks like:

* vague language
* no alternatives listed
* no tradeoffs listed
* no consequences listed
* no related files listed
* hidden assumptions left unstated

## 🔐 ADRs and open core

Because the repo is designed around a copyleft open-core strategy, ADRs must explicitly record any decision that affects:

* core versus premium boundaries
* trademark or governance implications
* provider lock-in risk
* monetization surface separation
* deployment separation for future commercial features

Any architectural choice that could make open-core separation harder must be recorded.

## 👀 ADRs and observability

ADRs must explicitly record decisions that affect:

* telemetry stack
* SLI or SLO measurement shape
* tracing boundaries
* eval system boundaries
* logging schema
* dashboard or alerting architecture

This is required because observability is a first-class architecture concern in this repo.

## ✅ ADR-level definition of done

An ADR update is incomplete unless:

* the ADR file is updated
* the decision index is updated
* status is clear
* related sprint planning files remain aligned
* related root technical docs remain aligned
* superseded or revised decisions are explicitly marked when applicable

## 🚫 ADR anti-patterns

ADRs must not become:

* raw identifiers beyond folder paths
* meeting transcripts
* generic brainstorming dumps
* implementation walkthroughs
* duplicate sprint plans
* vague essays with no actual decision
* stale records that no longer match the repo
* fluffy status chatter that adds no durable theory

## 📜 Relationship to other root docs

This file works with:

* `docs/planning/MASTER.md` for sprint and deliverable structure
* `docs/architecture.md` for durable technical truth
* `docs/operations.md` for current-state truth
* all sprint planning files for execution details

This file should stay focused on **ADR workflow, structure, and governance**.
