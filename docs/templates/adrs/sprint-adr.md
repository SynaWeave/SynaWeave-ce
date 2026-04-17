# 🧾 Architecture Decision Record — Sprint <nnn>

## TL;DR

This file is the durable reasoning spine for major repo and runtime decisions in Sprint <nnn>. Keep entries newest first. Extend this ledger instead of scattering rationale across pull requests or side channels.

---

## ADR Guide

### How To Use This File (Rules)

- Treat this file as the sprint-level reasoning ledger whenever `docs/adrs/` changes.
- Add new entries when a durable repo, runtime, testing, or governance decision is locked.
- Use plain English unless a folder path or external standard is required for precision.
- Keep all entries and bullets DRY, non-duplicative, and free of wording blocked by the shared policy.
- Use at least 3 concrete bullets of at least 14 words each for every ADR question.
- Keep `## Current Status` short, grouped by category, and limited to 10 bullets or fewer.
- Keep each decision bounded to one real choice so the ledger stays readable and reviewable.
- Use stable sprint-local identifiers such as `D1`, `D2`, or deliverable-scoped forms like `D1-T2` when one deliverable contains multiple durable decisions.
- Keep the decision index row identifier and title exactly matched to the corresponding decision heading.
- Update related root docs when a decision changes durable system truth.

### Decision Entry Template

- ***What was built?***
- ***Why was it chosen?***
- ***What boundaries does it own?***
- ***What breaks if it changes?***
- ***What known edge cases or failure modes matter here?***
- ***Why does this work matter?***
- ***What capability does it unlock?***
- ***Why is the chosen design safer or more scalable?***
- ***What trade-off did the team accept?***

---

## Current Status

- Sprint <nnn>
  - <one distinct recent status signal>

---

## Entries

---

| Decision | Status |
| --- | --- |
| D1-T2 - <plain-English decision title> | approved |

---

### D1-T2 - <plain-English decision title>

- ***What was built?***
  - <describe the bounded change in plain English with enough detail for cross functional review>
  - <name the important surfaces touched and the durable shape that exists after approval>
  - <state what was added or changed without collapsing the reasoning into a one line summary>
- ***Why was it chosen?***
  - <explain the main constraint that made this choice stronger than the named alternatives considered>
  - <describe the review pressure, delivery need, or safety requirement that shaped the decision>
  - <capture why this path fit the sprint better than the rejected design or tooling options>
- ***What boundaries does it own?***
  - <name the surface this decision owns and one important surface that it intentionally does not own>
  - <describe the contract edge that reviewers must keep stable when later work extends this area>
  - <explain which team or runtime concerns should stay outside this decision to avoid drift>
- ***What breaks if it changes?***
  - <describe the dependent review path, runtime contract, or repo control that would drift first>
  - <explain the rollback, migration, or coordination cost that appears if this choice is replaced>
  - <state who would need to react when this decision changes so reviews stay concrete>
- ***What known edge cases or failure modes matter here?***
  - <name a realistic failure mode that reviewers should keep in mind when extending this decision>
  - <describe one confusing edge case that could make the chosen shape look correct while still drifting>
  - <capture one operational or maintenance risk that should stay visible in later changes>
- ***Why does this work matter?***
  - <explain why the decision improves shared understanding, runtime safety, or review quality>
  - <state what durable confusion, risk, or repeated debate this choice removes from the sprint>
  - <connect the decision to the wider repo theory so later contributors understand its purpose>
- ***What capability does it unlock?***
  - <name a follow on change that becomes safer or easier because this decision is settled>
  - <describe the review or delivery path that benefits from having this durable choice recorded>
  - <capture how this decision reduces future setup cost for adjacent implementation work>
- ***Why is the chosen design safer or more scalable?***
  - <compare the approved shape against one rejected alternative and explain the safety gain in plain terms>
  - <describe the scaling, maintenance, or review benefit that makes this structure easier to extend>
  - <state why the approved design keeps drift lower than the other option by name>
- ***What trade-off did the team accept?***
  - <state the real cost, burden, or lost convenience that came with the chosen path>
  - <explain why the team chose that cost instead of paying the risk carried by alternatives>
  - <capture what future reviewers should remember before trying to remove this trade off>

---
