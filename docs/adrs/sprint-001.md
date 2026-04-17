# 🧾 Architecture Decision Ledger — Sprint 001

## TL;DR

This file is the durable reasoning spine for Sprint 001 of the governed rebuild. It explains why the repo moved from prototype sprawl toward one bounded multi-surface platform. Keep entries newest first and extend this ledger instead of scattering rationale across pull requests, chat history, or side channels.

---

## ADR Guide

### How To Use This File (Rules)

- Treat this file as the sprint-level reasoning ledger whenever `docs/adrs/` changes. DO NOT treat it as optional reference prose.
- Add new entries when a durable repo, runtime, testing, or governance decision is locked. There should be AT LEAST 3 per deliverable.
- Entries must use plain English over raw identifiers unless a folder path or external standard is required for precision. Reference related repo surfaces and docs when the decision changes shared understanding.
- Keep all entries and bullets DRY and materially non-duplicative. Avoid fluff, filler, pleasantries, and repeated rationale wrappers.
- Use at least 3 concrete bullets of at least 14 words each for every ADR question. Capture why a choice was made, not only what changed. Expand into explicit constraints, benefits, and trade-offs compared to other strategies or tools by name.
- Keep `## Current Status` short, grouped by category, and free of repeated signals. Use at most 10 bullet entries, also most recent first.
- Keep each decision bounded to one real choice so the ledger remains easy to review.
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

- Sprint 001 Deliverable 1 has seven approved decisions, including closeout hardening for pull request verification, secret-scan cleanup, and verifier test isolation.
- Pull request commit verification checks authored pull request commits while hosted workflows still evaluate merge-result repository state for final branch protection evidence.
- Secret-scan-safe placeholder cleanup removes realistic database examples that created false positives without improving repository guidance or safety posture.
- Verifier tests isolate temporary repositories from CI-exported commit metadata so local and hosted runs prove the same intended repo-control behavior.
- All repo-contained verification checks for the branch are passing under the tightened Sprint 001 Deliverable 1 closeout controls.
- Shared contract and configuration surfaces remain reserved in governed package boundaries instead of app-local placeholders.
- Sprint reasoning lives in one ADR ledger so approved choices remain durable beyond pull request summaries.

---

## Entries

---

| Decision | Status |
| --- | --- |
| D1-T8 - closeout hardening for PR verification, secret-scan placeholders, and verifier isolation | approved |
| D1-T7 - Reserve provider-neutral auth contracts and config boundaries | approved |
| D1-T6 - verifier tracks and repo-control test hardening | approved |
| D1-T5 - reusable template system hardening and owner-doc linkage | approved |
| D1-T4 - protected-path control-surface alignment | approved |
| D1-T2 - Make root docs and MASTER the only planning authority | approved |
| D1 - Lock the shallow monorepo topology and reserved runtime homes | approved |

---

### D1-T8 - closeout hardening for PR verification, secret-scan placeholders, and verifier isolation

- ***What was built?***
  - Sprint 001 Deliverable 1 closeout hardened pull request verification so authored pull request commits are validated separately from hosted merge-result repository evaluation.
  - Repo verification workflow and environment semantics were tightened so authored-commit checks and merge-result checks no longer blur into one misleading signal.
  - Secret-scan cleanup replaced Postgres-shaped sample database placeholders with synthetic placeholders, while verifier tests isolate temporary repositories from leaked CI commit metadata.
- ***Why was it chosen?***
  - Sprint 001 needed documented rules, local verification, and hosted checks to agree on what evidence belongs to authored changes versus merge results.
  - False-positive secret scanning around realistic sample placeholders was creating review noise without adding meaningful security coverage for repository-contained examples.
  - Temporary-repository verifier tests had to remain deterministic even when CI exports commit environment variables that do not belong to unit-test fixtures.
- ***What boundaries does it own?***
  - This decision owns Sprint 001 Deliverable 1 closeout semantics for pull request commit validation, hosted merge-result evaluation, and verifier environment separation.
  - It owns repository example placeholder hygiene where sample credential-like values can accidentally trigger security tooling without representing actual supported configuration guidance.
  - It does not replace D1-T6 verifier-lane structure or D1-T4 protected-path alignment, but narrows how those approved controls behave at closeout.
- ***What breaks if it changes?***
  - Reviewers could mistake merge-ref workflow results for authored-commit evidence, making pull request verification conclusions less trustworthy during protected-path review.
  - Secret-scan tooling would keep generating avoidable false positives, which trains contributors to ignore warnings that should remain high-signal.
  - Verifier unit tests could fail only in CI because exported commit metadata leaks into temporary repositories that should behave like isolated fixtures.
- ***What known edge cases or failure modes matter here?***
  - Hosted workflows legitimately run against merge references, so documentation and verifier output must still explain why that differs from authored-commit validation.
  - Placeholder strings can look obviously fake to humans while still matching database or credential patterns strongly enough to trigger automated secret scanners.
  - Temporary git repositories created during tests may inherit CI commit identity variables unless harness setup explicitly resets or ignores those ambient values.
- ***Why does this work matter?***
  - Sprint 001 Deliverable 1 was meant to leave repo-contained controls trustworthy, and closeout hardening removes the last mismatches between policy and enforcement semantics.
  - It keeps security tooling useful by reducing false-positive churn instead of accepting noisy scans as an unavoidable cost of repository examples.
  - It gives maintainers credible passing verification evidence for the branch because local checks and hosted checks fail for understandable reasons.
- ***What capability does it unlock?***
  - Pull request review can distinguish authored-commit correctness from merge-result correctness without collapsing those two repository states into one claim.
  - Future verifier and workflow changes can extend the same semantics instead of rediscovering how commit-scoped and merge-scoped checks should differ.
  - Repository examples can remain instructional without repeatedly tripping security scanners on placeholder values that were never meant to resemble live secrets.
- ***Why is the chosen design safer or more scalable?***
  - Separating authored-commit validation from merge-result evaluation is safer than one blended status because branch protection decisions depend on both contexts.
  - Clearly synthetic placeholders scale better than realistic-looking examples because security tooling stays high-signal as more example configuration surfaces are added.
  - Test isolation is more scalable than environment-dependent expectations because CI providers and local shells export different commit metadata by default.
- ***What trade-off did the team accept?***
  - The team accepted slightly more explicit verifier and workflow semantics so contributors must understand why two repository states can both matter.
  - Example placeholders became less lifelike, which sacrifices some immediacy in favor of clearer safety signaling and quieter automated security tooling.
  - Closeout work added more fixture hygiene and reasoning overhead, but that cost was preferable to leaving Sprint 001 controls ambiguously correct.

---

### D1-T7 - Reserve provider-neutral auth contracts and config boundaries

- ***What was built?***
  - Shared package boundaries reserve auth contracts and configuration surfaces before application runtimes choose any concrete identity provider.
  - The initial work maps browser-safe versus server-only configuration edges so later auth work cannot leak privileged secrets into browser runtimes.
  - Sprint 001 captures provider-neutral auth as a deliberate contract boundary instead of leaving app folders to invent incompatible placeholders.
- ***Why was it chosen?***
  - The team needed Deliverable 2 runtimes to start from stable contract seams without prematurely locking the project into vendor-specific auth assumptions.
  - Reserving the boundary prevents extension, web, API, and background runtimes from drifting into conflicting session and credential patterns.
  - This path fit Sprint 001 better than selecting Clerk, Auth0, Supabase Auth, or custom sessions before product requirements were verified.
- ***What boundaries does it own?***
  - This decision owns shared auth contract and configuration boundaries under governed package surfaces, not final provider implementation details inside apps.
  - It leaves browser-safe config, server-only secrets, and session contract expectations explicit so reviewers can reject cross-runtime leakage early.
  - It does not own user model, permission matrix, billing logic, or operational incident handling beyond the reserved interface edge.
- ***What breaks if it changes?***
  - Future runtime work in extension, web, API, and ingestion surfaces would need coordinated rewrites if auth contracts stop staying provider-neutral.
  - Docs, verifier assumptions, and package ownership guidance would drift quickly if secrets or session semantics move back into app-local code.
  - Reviewers for Sprint 002 authentication and runtime tasks would lose the shared contract baseline that leaves implementation choices comparable.
- ***What known edge cases or failure modes matter here?***
  - A browser runtime can appear correctly wired while still importing server-only config if shared boundaries are documented loosely or enforced inconsistently.
  - Teams may mistake provider-neutral wording as permission to omit concrete session contracts, creating delayed ambiguity rather than useful flexibility.
  - Later provider adapters could smuggle provider naming into core domain language and make open-core separation harder than intended.
- ***Why does this work matter?***
  - It gives later sprint work one durable answer for where auth contracts belong before runtime implementation pressure increases.
  - It removes repeated debate about whether early auth scaffolding should live in app entrypoints, package boundaries, or configuration glue.
  - This decision leaves security posture matched with repo governance by preserving explicit env boundaries before privileged operations are implemented.
- ***What capability does it unlock?***
  - Deliverable 2 can implement web, API, and extension auth flows against shared seams without redefining configuration ownership first.
  - Reviewers can compare competing provider integrations against one approved contract instead of accepting whichever app ships first.
  - Future premium or deployment-specific auth strategies can branch from shared boundaries without rewriting the whole repo topology.
- ***Why is the chosen design safer or more scalable?***
  - A provider-neutral shared contract is safer than app-local auth scaffolding because it limits secret sprawl and reduces review guesswork.
  - Centralized configuration boundaries scale better as more runtimes arrive because new surfaces inherit the same browser versus server rules.
  - This design leaves drift lower than choosing a named provider early, then later extracting abstractions after multiple consumers already depend on it.
- ***What trade-off did the team accept?***
  - The team chose slower immediate auth implementation because the sprint captures boundaries first instead of shipping quick provider-specific setup.
  - Contributors must tolerate some abstraction overhead before runtime code exists, which is less convenient than dropping auth directly into apps.
  - Future reviewers should remember this cost was chosen to avoid lock-in, secret leakage, and inconsistent session semantics across runtimes.

---

### D1-T6 - verifier tracks and repo-control test hardening

- ***What was built?***
  - Repo verification is treated as explicit tracks that cover merge-oriented governance checks and matching repo-control test expectations.
  - The sprint baseline locks verifier behavior together with tests so tightened rules are reviewable instead of living as unchecked script edits.
  - Local and CI verification share the same repo-control intent, even when some enforcement remains correctly scoped to pull-request tracks.
- ***Why was it chosen?***
  - The repository needed executable controls that matched documented governance rules instead of relying on maintainers to spot policy drift manually.
  - Pairing verifier changes with tests reduces the chance that later hardening silently regresses protected-path, ADR, or workflow expectations.
  - This approach fit Sprint 001 better than adding more policy prose without executable checks, or overloading commit hooks with review-time rules.
- ***What boundaries does it own?***
  - This decision owns verifier lane shape, repo-control test coupling, and the documented split between local checks and PR-oriented enforcement.
  - It leaves ADR structure enforcement, workflow expectations, and governance guards in reviewable automation surfaces rather than informal maintainer memory.
  - It does not own language-specific application tests, product correctness, or runtime observability checks outside repo-control enforcement.
- ***What breaks if it changes?***
  - Maintainers would lose confidence that docs, workflows, hooks, and protected-path controls still agree after policy updates land.
  - CI and local commands would drift into different definitions of readiness, making verification evidence harder to trust during review.
  - Contributors would need manual interpretation of governance rules if repo-control tests stop protecting verifier behavior changes.
- ***What known edge cases or failure modes matter here?***
  - A check may pass locally while failing in pull-request tracks if the repo stops describing which rules intentionally apply only during review.
  - Contributors may move ADR or protected-path checks into commit hooks, creating noisy automation and weakening actual merge controls.
  - Tests can become brittle if they validate current file names too literally instead of the durable governance behavior being protected.
- ***Why does this work matter?***
  - It turns governance expectations into executable evidence, which is essential for a repo centered on protected paths and durable contracts.
  - It removes ambiguity about whether verifier changes require matching test updates when repo rules or workflow assumptions tighten.
  - This decision anchors quality posture before feature scope expands, preventing Sprint 002 work from inheriting weak or inconsistent controls.
- ***What capability does it unlock?***
  - Future policy changes can be implemented confidently because maintainers have tests that describe the intended verifier contract.
  - CI workflows can evolve while still proving the same repository controls that local contributors run before opening pull requests.
  - Reviewers can ask for targeted repo-control hardening without reinventing verification strategy for each governance-related change.
- ***Why is the chosen design safer or more scalable?***
  - Lane-based verifier design is safer than one undifferentiated script because it preserves which checks belong to local versus merge contexts.
  - Test-backed repo controls scale better than manual review checklists because new protections can be added without depending on tribal memory.
  - This structure leaves drift lower than hook-only enforcement, which often hides failures locally and leaves pull-request posture underspecified.
- ***What trade-off did the team accept?***
  - The team chose more upfront maintenance in tests and verifier structure to gain durable confidence in repo-control behavior.
  - Contributors may face clearer but stricter failures when governance docs or workflows move, even for changes that seem documentation-only.
  - Future reviewers should remember that this friction was chosen deliberately to keep protected-path policy executable rather than aspirational.

---

### D1-T5 - reusable template system hardening and owner-doc linkage

- ***What was built?***
  - `docs/templates/` is the only reusable template home for recurring planning, ADR, specification, and verification artifacts.
  - Templates point back to owner sources for policy authority so repeated structures can remain matched without cloning full governance prose.
  - Sprint 001 marks template edits as protected-path changes because they reshape how future governed artifacts are authored and reviewed.
- ***Why was it chosen?***
  - The repo needed one durable template surface to prevent each sprint or contributor from inventing competing artifact formats.
  - Owner-doc linkage leaves policy truth centralized while still giving contributors practical scaffolds for recurring artifacts and review evidence.
  - This path was stronger than copying rules into every template because duplication would create hidden drift the moment policy changed.
- ***What boundaries does it own?***
  - This decision owns reusable artifact shape under `docs/templates/` and the rule that templates reference owner docs instead of replacing them.
  - It leaves recurring artifact structure consistent across planning, ADR, spec, and verification work without claiming authority over repo policy itself.
  - It does not own the substantive policy in governance, contributing, or owner docs beyond linking to those canonical sources.
- ***What breaks if it changes?***
  - Contributors would start creating parallel artifact shapes and duplicated policy snippets if templates stop being the single reusable source.
  - Owner docs would need frequent manual cleanup as copied rules drift apart across sprint files, ADRs, and verification artifacts.
  - Reviewers would lose a dependable baseline for whether recurring docs are complete, matched, and safe to extend.
- ***What known edge cases or failure modes matter here?***
  - A template can look helpful while embedding stale policy text that silently conflicts with the owner doc it should reference.
  - Contributors may confuse template guidance with permission to create new template homes inside app or domain folders.
  - Small wording changes in a template can have repo-wide downstream effects because future artifacts will inherit that changed structure.
- ***Why does this work matter?***
  - It leaves recurring artifact work DRY, which is essential in a repo that treats docs as governed technical surfaces.
  - It removes uncertainty about where new planning or verification structures should live when contributors need a reusable starting point.
  - This decision reinforces that durable policy belongs in owner docs while templates exist to improve consistency and handoff quality.
- ***What capability does it unlock?***
  - Future phases can add new governed artifacts quickly by extending one template system instead of re-debating artifact structure each time.
  - Reviewers can request owner-doc updates and template alignment together when shared understanding changes across recurring artifacts.
  - The repo can scale its documentation process without creating a second policy surface hidden inside copied markdown boilerplate.
- ***Why is the chosen design safer or more scalable?***
  - A single template system is safer than ad hoc artifact formats because it narrows where structural drift can start.
  - Owner-doc linkage scales better than self-contained templates because one policy update can propagate through references instead of manual duplication.
  - This design leaves drift lower than one-off sprint-specific formats, which would fragment review expectations as the monorepo expands.
- ***What trade-off did the team accept?***
  - The team chose stricter template governance, which reduces contributor freedom to invent custom artifact structures for convenience.
  - Some templates may feel less self-contained because they intentionally defer policy details to owner docs rather than repeating them inline.
  - Future reviewers should preserve that trade-off because convenience duplication would be more expensive than following linked owner guidance.

---

### D1-T4 - protected-path control-surface alignment

- ***What was built?***
  - Sprint 001 matched governance docs, pull request templates, CODEOWNERS, hooks, workflows, and verifier expectations around one protected-path contract.
  - The repo documents protected paths as a coordinated control surface rather than isolated files with partially overlapping authority.
  - Admin bypass is explicitly framed as a GitHub-side exception path while repo artifacts outline expected merge posture and review evidence.
- ***Why was it chosen?***
  - The initial setup could not be considered complete while protected-path rules disagreed across documentation, automation, and review ownership surfaces.
  - Aligning every control surface reduces the chance that one outdated file silently weakens governance for high-blast-radius changes.
  - This option was safer than tightening only CODEOWNERS or only workflows because policy drift often starts between those boundaries.
- ***What boundaries does it own?***
  - This decision owns the shared contract for protected-path documentation, review ownership, workflow posture, and contributor disclosure expectations.
  - It leaves repo-level control surfaces matched while intentionally leaving GitHub ruleset configuration as an external enforcement home.
  - It does not own product runtime behavior, business authorization rules, or feature-level code review standards outside protected-path governance.
- ***What breaks if it changes?***
  - Protected-path edits could merge under inconsistent review expectations if docs, CODEOWNERS, and workflows stop describing the same boundary.
  - Maintainers would need to reconstruct policy intent manually whenever governance-related pull requests touch multiple control surfaces together.
  - Contributors would receive mixed signals about required rationale, verification, and ownership for the most sensitive repository files.
- ***What known edge cases or failure modes matter here?***
  - A path can be listed as protected in docs but omitted from CODEOWNERS or workflow filters, creating false confidence during review.
  - Admin bypass language can accidentally normalize exceptions if repo text stops emphasizing that bypass remains explicit and rare.
  - Control surfaces may appear matched while using different naming or path globs that capture materially different file sets.
- ***Why does this work matter?***
  - It makes the repository's highest-risk documentation and automation surfaces reviewable through one coherent policy story.
  - It removes hidden governance drift that would otherwise undermine trust in protected-path labels and merge-readiness claims.
  - This decision supports the monorepo's broader theory that durable controls must be both human-friendly and executable.
- ***What capability does it unlock?***
  - Future protected-path additions can be reviewed against one approved contract instead of re-negotiating control semantics every time.
  - Maintainers can tighten workflows or CODEOWNERS with confidence because the matching docs and templates already define expected behavior.
  - Contributors can prepare safer pull requests by understanding exactly which paths require narrow scope and explicit rationale.
- ***Why is the chosen design safer or more scalable?***
  - Coordinated control-surface alignment is safer than isolated policy updates because sensitive path protection fails at the weakest seam.
  - This shape scales better as the repo grows because new protected areas can be added through an existing multi-surface contract.
  - It leaves drift lower than relying on undocumented maintainer habits, which do not survive growth, turnover, or urgent changes.
- ***What trade-off did the team accept?***
  - The team chose extra coordination whenever protected-path policy changes because multiple control surfaces must remain synchronized.
  - Contributors face more explicit documentation and review obligations for sensitive edits than they would in a loosely governed repository.
  - Future reviewers should keep that burden because weakening protected-path alignment would reintroduce silent governance failures.

---

### D1-T2 - Make root docs and MASTER the only planning authority

- ***What was built?***
  - Root `docs/` remains the only canonical technical documentation surface, and `docs/planning/MASTER.md` is the only planning-rules authority.
  - `docs/planning.md` is constrained to a pointer role so it cannot compete with MASTER or create a second planning truth.
  - Sprint 001 captures this as a durable decision so planning, owner docs, and ADR updates all reference the same authority chain.
- ***Why was it chosen?***
  - The repo needed one canonical planning owner to stop prototype-era duplication from confusing current branch reality and sprint execution.
  - A single docs and planning authority reduces review time because contributors no longer need to compare multiple root files for policy truth.
  - This approach was better than maintaining convenience summaries because duplicated planning rules drift quickly under active repo reset work.
- ***What boundaries does it own?***
  - This decision owns canonical planning authority, root documentation authority, and the rule that pointer docs must not become competing sources.
  - It leaves sprint plans, ADRs, and owner docs matched around one planning spine while leaving feature implementation details to their domains.
  - It does not own publication mechanics, static site output, or any second documentation runtime because those remain explicitly out of scope.
- ***What breaks if it changes?***
  - Contributors would start citing conflicting planning texts, which would make task scope and readiness evidence harder to review consistently.
  - Root owner docs could drift away from sprint planning assumptions if a pointer file evolves into a second planning authority.
  - Maintainers would lose a stable place to resolve planning disputes when deliverables, tasks, and non-goals need exact reference points.
- ***What known edge cases or failure modes matter here?***
  - A pointer artifact can slowly accumulate helpful-looking rules until it effectively becomes a second owner source.
  - Historical prototype notes may linger in active planning files and confuse reviewers unless current-branch reality is stated plainly.
  - Contributors may treat published docs output as a separate authority if the repo stops distinguishing publication from canonical source.
- ***Why does this work matter?***
  - It gives the repo one durable answer for where planning truth lives, which reduces scope disputes and documentation archaeology.
  - It removes ambiguity that previously let stale root docs and planning summaries coexist with active sprint files.
  - This decision reinforces the governed monorepo model by making documentation authority as explicit as code ownership authority.
- ***What capability does it unlock?***
  - Later sprint plans can assume one canonical planning spine when they describe deliverables, tasks, and verification expectations.
  - Reviewers can request doc alignment confidently because they know which file owns planning policy and which files are pointers.
  - Contributors can add new owner docs or sprint entries without accidentally creating a parallel source of planning truth.
- ***Why is the chosen design safer or more scalable?***
  - One planning authority is safer than distributed summaries because it limits where stale instructions can mislead implementation work.
  - Root docs as the only canonical technical surface scale better than app-local or duplicate docs homes in a growing monorepo.
  - This structure leaves drift lower than using convenience copies, which inevitably lag once multiple deliverables progress in parallel.
- ***What trade-off did the team accept?***
  - The team chose less convenience for casual readers because some overview files point elsewhere instead of duplicating full guidance.
  - Contributors must follow links into owner docs more often, which is slightly slower than relying on local summaries.
  - Future reviewers should preserve this trade-off because duplicated authority would cost more than a few extra navigation steps.

---

### D1 - Lock the shallow monorepo topology and reserved runtime homes

- ***What was built?***
  - Sprint 001 locks a shallow semantic top-level monorepo split across `apps/`, `packages/`, `python/`, `infra/`, `testing/`, `tools/`, `docs/`, and `.github/`.
  - The repo reserves runtime homes for extension, web, API, ingest, MCP, ML, and evaluation work without treating those folders as finished products.
  - Reusable logic is explicitly steered into shared package or Python domains so app entrypoints remain runtime-first instead of library-first.
- ***Why was it chosen?***
  - The project needed a durable repository shape before product work expanded, otherwise each new runtime would choose its own placement rules.
  - A shallow topology leaves review boundaries visible and prevents prototype-era sprawl from reappearing under deeper nested folder trees.
  - This option fit Sprint 001 better than waiting for runtime implementations to define structure implicitly through first use.
- ***What boundaries does it own?***
  - This decision owns top-level domain placement, reserved runtime homes, and the expectation that shared logic leaves app roots quickly.
  - It leaves the repo shallow and semantic while intentionally avoiding detailed internal architecture for each future application surface.
  - It does not own provider selection, runtime feature scope, or package internals beyond their placement in the governed topology.
- ***What breaks if it changes?***
  - Planning docs, owner docs, and future implementation tasks would all need coordinated updates if top-level domains stopped matching this contract.
  - Shared code would drift back into app folders, making later extraction and ownership review significantly more expensive.
  - Contributors would lose confidence about where new work belongs, which would slow delivery and increase path drift during review.
- ***What known edge cases or failure modes matter here?***
  - Empty reserved runtime homes can be mistaken for permission to drop shared code there unless the runtime-first rule remains explicit.
  - Teams may add convenience nesting that seems harmless locally but gradually obscures ownership seams across the monorepo.
  - Prototype residue can survive under old paths and create duplicate homes if reviewers stop enforcing the locked topology consistently.
- ***Why does this work matter?***
  - It gives every later sprint one stable answer for where code, docs, tests, and repo controls belong.
  - The decision removes structural debate from early feature work so implementation can focus on contracts and behavior instead of path politics.
  - This topology is the initial base that makes the governed monorepo useful to new contributors and maintainers.
- ***What capability does it unlock?***
  - Deliverables for web, API, extension, ingest, and evaluation work can begin without redefining the repo map.
  - Reviewers can distinguish app-specific code from reusable package or Python logic earlier in the change lifecycle.
  - The project can grow additional domains while preserving a predictable shallow structure and clearer ownership boundaries.
- ***Why is the chosen design safer or more scalable?***
  - A shallow semantic topology is safer than ad hoc nested growth because reviewers can see contract boundaries directly from the root.
  - Reserved runtime homes scale better than retrofitting folders after implementation because each new surface starts from known placement rules.
  - This design leaves drift lower than prototype-style sprawl, where shared utilities and runtime code blur together over time.
- ***What trade-off did the team accept?***
  - The team chose some up-front empty structure and stronger placement rules before every runtime had working implementation code.
  - Contributors lose some short-term freedom to place files wherever convenient because the topology favors long-term reviewability.
  - Future reviewers should remember that this discipline was chosen to avoid costly repo reshaping after multiple runtimes already depend on it.

---
