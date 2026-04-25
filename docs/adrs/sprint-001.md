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

- Deliverable 3 has five approved decisions covering collector-routed observability, durable evidence recording, self-hosted local AI-quality backends, schema-driven contract testing, and browser proof limits with durable vitals artifacts.
- Deliverable 2 has four approved decisions covering the bounded runtime slice, adapter-first provider posture, Zuplo as the selected unified edge target, and deferred activation of edge or gateway seams.
- Sprint 001 Deliverable 3 has an approved local observability decision for compose-backed collector-routed API and ingest traces plus versioned dashboards and alerts.
- Sprint 001 Deliverable 1 has seven approved decisions, including closeout hardening for pull request verification, secret-scan cleanup, and verifier test isolation.
- Shared contract bundles and schema-driven contract tests anchor Sprint 1 public runtime interfaces across API envelopes and extension message fixtures.
- Browser proof records web-shell Core Web Vitals separately from side-panel open or popup boot timing, with explicit limits on what Playwright can inspect directly.
- Pull request commit verification checks authored pull request commits while hosted workflows still evaluate merge-result repository state for final branch protection evidence.
- Self-hosted local Langfuse and MLflow proof remain bounded Sprint 1 backends, while managed service adoption stays a later adapter-preserving choice.
- Zuplo is the selected Sprint 1 edge target, but local proof remains direct-to-API until that edge path is booted and verified.
- Durable observability claims require versioned dashboards or alerts, machine-readable artifacts, or replayable local telemetry stores, and this ledger keeps those approved choices durable beyond pull request summaries.

---

## Entries

---

| Decision | Status |
| --- | --- |
| D3-T7 - record browser proof with web-shell vitals and explicit side-panel limits | approved |
| D3-T6 - require schema-driven contract tests for Sprint 1 public interfaces | approved |
| D2-T4 - select Zuplo as the unified Sprint 1 edge target behind adapters | approved |
| D3-T5 - keep self-hosted local Langfuse and MLflow as the Sprint 1 proof baseline with managed later options | approved |
| D3-T4 - require durable observability and metrics recording for Sprint 1 quality claims | approved |
| D3-T3 - make compose-backed collector-routed API and ingest traces the local observability baseline | approved |
| D2-T3 - keep edge, CDN, and API gateway choices deferred behind adapters during Sprint 1 | approved |
| D2-T2 - make Supabase the default Sprint 1 adapter target without treating it as permanent lock-in | approved |
| D2-T1 - lock one bounded multi-surface runtime slice before broader platform expansion | approved |
| D1-T8 - closeout hardening for PR verification, secret-scan placeholders, and verifier isolation | approved |
| D1-T7 - Reserve provider-neutral auth contracts and config boundaries | approved |
| D1-T6 - verifier tracks and repo-control test hardening | approved |
| D1-T5 - reusable template system hardening and owner-doc linkage | approved |
| D1-T4 - protected-path control-surface alignment | approved |
| D1-T2 - Make root docs and MASTER the only planning authority | approved |
| D1 - Lock the shallow monorepo topology and reserved runtime homes | approved |

---

### D3-T7 - record browser proof with web-shell vitals and explicit side-panel limits

- ***What was built?***
  - Sprint 001 Deliverable 3 records one tracked browser-proof artifact that separates web-shell Core Web Vitals from extension side-panel open and popup boot timing evidence.
  - The browser artifact states the exact proof limit: Playwright can prove the side-panel open request and runtime boot, but not direct DOM inspection of Chromium-owned side-panel chrome.
  - Root docs and performance baselines point to `testing/performance/browser-shell-baseline.local-proof.v1.json` as the durable browser evidence surface for the bounded Sprint 1 path.
- ***Why was it chosen?***
  - Browser timing claims had become durable enough to deserve a tracked artifact, but extension-side-panel evidence still needed more precise wording than generic “browser vitals” language allowed.
  - Treating web-shell Core Web Vitals and side-panel boot timing as the same proof class would overstate what the current automation stack can inspect or compare.
  - A versioned browser artifact keeps Sprint 1 performance language reviewable without pretending the hidden browser-owned container has become visible to Playwright.
- ***What boundaries does it own?***
  - This decision owns the durable Sprint 1 browser-proof artifact, its scope, and the rule that web-shell vitals and extension boot timing stay labeled as different evidence classes.
  - It owns the explicit limitation language for side-panel proof so root docs and closeout records cannot silently upgrade runtime boot evidence into full container inspection.
  - It does not own service latency metrics, collector exports, or the runtime-eval harness outputs that are covered by adjacent Deliverable 3 decisions.
- ***What breaks if it changes?***
  - Reviewers could misread side-panel timing evidence as direct browser-container verification, which would make Sprint 1 browser claims less trustworthy.
  - Future browser baselines would become harder to compare if web-shell Core Web Vitals and extension boot timing drift into one mixed metric bucket.
  - README, operations, and closeout language would overstate the current browser automation surface the moment the proof boundary becomes vague.
- ***What known edge cases or failure modes matter here?***
  - Chromium still hides the browser-owned side-panel container DOM from Playwright, so tests can confirm open requests and booted runtime documents without exposing every rendered chrome detail.
  - A healthy web-shell LCP, INP, or CLS value says nothing by itself about extension panel boot speed, because those surfaces have different runtime and browser constraints.
  - Playwright output artifacts can capture richer ephemeral timing detail than the tracked artifact, so docs must keep local run outputs distinct from durable checked-in proof.
- ***Why does this work matter?***
  - Sprint 1 needed honest browser-quality evidence for the critical path instead of prose that blurred page vitals, extension boot timing, and unavailable browser chrome inspection.
  - The tracked artifact gives future reviewers one stable browser baseline for later comparison without requiring access to the original Playwright run directory.
  - This work also protects the repo from inflated extension-automation claims that would otherwise outrun what Chromium exposes to test tooling.
- ***What capability does it unlock?***
  - Later sprints can add richer browser timing or interaction proof while still comparing back to one bounded Sprint 1 baseline.
  - Reviewers can ask for narrower browser evidence because the repo names exactly what current automation does and does not prove.
  - Performance discussions can stay grounded in tracked artifacts instead of screenshots, memory, or ambiguous references to “browser tests passed.”
- ***Why is the chosen design safer or more scalable?***
  - Separate browser-proof classes are safer than one blended artifact because they prevent automation limits from being hidden inside attractive aggregate metrics.
  - Versioned browser artifacts scale better than ephemeral local output alone because maintainers can compare runs across branches and time.
  - Explicit proof limits also scale better for review because new browser automation can tighten the boundary later without rewriting Sprint 1 history.
- ***What trade-off did the team accept?***
  - The team chose narrower browser claims in exchange for wording and artifacts that match the real Playwright and Chromium evidence boundary exactly.
  - Contributors maintain one more tracked proof file and must keep its limit language aligned with the automation harness.
  - Future reviewers should preserve that discipline because a simpler but blurrier browser-proof story would be easier to write and harder to trust.

---

### D3-T6 - require schema-driven contract tests for Sprint 1 public interfaces

- ***What was built?***
  - Sprint 001 Deliverable 3 keeps a shared runtime contract bundle under `packages/contracts/runtime/public-interfaces.v1.json` and validates it through schema-driven contract tests.
  - The contract test lane exercises live API responses plus extension selection-message fixtures so both service envelopes and browser-adjacent serialized payloads stay aligned.
  - Package, testing, and root docs treat those contract tests as the owned Sprint 1 surface for public serialized-interface drift.
- ***Why was it chosen?***
  - The bounded runtime slice had become large enough that unit and e2e coverage alone no longer gave reviewers a clean answer for whether public envelopes still matched the documented contract.
  - A shared bundle is clearer than scattered per-test assertions because the repo can review one versioned interface surface instead of re-deriving it from app code.
  - Schema-driven validation fit Sprint 1 better than bringing in heavier contract infrastructure, because the proof needed to stay small, local, and governed.
- ***What boundaries does it own?***
  - This decision owns the Sprint 1 public-interface contract bundle, the schema-driven validation lane, and the rule that live API envelopes match that governed bundle.
  - It owns extension selection-message fixture validation where those messages are part of the same bounded public runtime story.
  - It does not own future generated SDKs, long-term schema-registry tooling, or private internal service payloads that never cross the approved public boundary.
- ***What breaks if it changes?***
  - API and extension payloads could drift silently while still passing unrelated unit or smoke tests, making public-boundary regressions harder to catch early.
  - Reviewers would lose one durable place to inspect what Sprint 1 considers the canonical request and response shapes for the critical path.
  - Docs that promise versioned and testable contracts would become much less trustworthy if the bundle or its validating tests stopped being required.
- ***What known edge cases or failure modes matter here?***
  - A minimal schema subset can still miss future keyword needs, so later expansions should stay deliberate instead of turning the contract lane into a second framework project.
  - Live API tests can pass while extension fixtures drift, or vice versa, unless both stay pinned to the same bundle and naming convention.
  - Schema-driven checks prove payload shape, but they do not replace deeper behavioral or auth-boundary tests for the same endpoints.
- ***Why does this work matter?***
  - Sprint 1 needed one stable answer for where public runtime contracts live once web, API, ingest, and extension paths all started sharing real payloads.
  - This decision makes contract drift reviewable without asking maintainers to manually compare app code, docs, and browser fixtures every time.
  - It also reinforces the governed-monorepo rule that cross-surface contracts belong in shared owned layers instead of app entrypoints.
- ***What capability does it unlock?***
  - Later sprints can extend the same contract bundle for richer workspace, job, or AI interfaces without reinventing contract ownership.
  - Browser, API, and test lanes can all speak about one shared public-interface surface when changes touch serialized payloads.
  - Reviewers gain a smaller and more exact verification lane for interface safety than rerunning every runtime proof path to infer shape stability.
- ***Why is the chosen design safer or more scalable?***
  - Shared schema-driven contracts are safer than ad hoc assertions because they force payload drift through one versioned review surface.
  - The bounded custom schema checker scales better for Sprint 1 than introducing a heavier dependency stack whose maintenance would exceed the current need.
  - Keeping extension fixtures and live API envelopes pinned together also scales better than letting each surface define its own truth separately.
- ***What trade-off did the team accept?***
  - The team chose some manual schema maintenance in exchange for a clearer contract boundary that stays lightweight and repo-local.
  - Contributors must update both the bundle and the tests whenever public serialized interfaces change, which is slower than silent payload drift.
  - Future reviewers should keep that friction because contract discipline is cheaper than debugging mismatched clients after interface changes merge.

---

### D2-T4 - select Zuplo as the unified Sprint 1 edge target behind adapters

- ***What was built?***
  - Sprint 001 Deliverable 2 names Zuplo as the selected unified target for edge routing, CDN, caching, and API gateway concerns in root architecture, infra, operations, and closeout docs.
  - The same docs keep the current runtime proof honest by stating that local Sprint 1 execution still runs direct-to-API unless a Zuplo-backed path is separately booted and verified.
  - Adapter wording remains explicit so Zuplo selection shapes the current implementation target without becoming a domain contract or mandatory permanent vendor lock.
- ***Why was it chosen?***
  - The branch had moved beyond abstract edge seams, and contributors needed one concrete target so docs could stop describing gateway, CDN, and cache concerns as completely undecided.
  - Choosing one unified provider target is simpler than documenting separate speculative vendors for routing, CDN, and caching while none of those paths are yet booted.
  - Zuplo fits the current Sprint 1 need for one adapter-owned edge path without forcing the local proof to overclaim deployed edge behavior prematurely.
- ***What boundaries does it own?***
  - This decision owns the selected Sprint 1 provider target for edge, CDN, caching, and gateway seams across root technical docs and closeout language.
  - It owns the rule that Zuplo remains behind adapter-owned boundaries and must not rewrite public contracts, browser-safe boundaries, or server-only enforcement points directly.
  - It does not own a live deployed edge runtime, final production caching policy, or proof that local replay already traverses the selected provider.
- ***What breaks if it changes?***
  - Root docs would drift back into ambiguity if some files described Zuplo as selected while others kept claiming all edge-provider choices were still fully undecided.
  - Later edge activation work would lose a stable target narrative, making it harder to judge whether follow-on changes preserved adapter boundaries properly.
  - Reviewers could mistake target selection for integrated runtime truth unless the decision keeps both the selection and the current proof limit visible together.
- ***What known edge cases or failure modes matter here?***
  - Teams may read “selected target” as proof that the current local runtime already traverses Zuplo, even though docs intentionally say that path is not yet booted.
  - A unified provider target can still leak vendor concepts into public APIs unless adapter ownership stays explicit during later implementation work.
  - CDN and gateway concerns often feel operational, but they can still backdoor contract drift through headers, cache keys, or auth assumptions if review gets loose.
- ***Why does this work matter?***
  - Sprint 1 needed closeout docs to reflect the real current choice instead of preserving older “undecided” language after the repo had already selected a concrete target.
  - This decision reduces document drift across architecture, infra, operations, and sprint closeout records by giving them one shared edge-provider statement.
  - It also leaves the repo more explainable because future edge work starts from a named target and a named proof limit instead of silent assumptions.
- ***What capability does it unlock?***
  - Later sprints can implement gateway, edge-cache, or CDN behavior against one selected provider target without reopening basic provider selection in every doc.
  - Reviewers can evaluate edge-related changes against an explicit rule: integrate concretely, but keep the contract and adapter seam swappable.
  - Operators gain a clearer path for future bootable edge proof because one provider target already owns the current follow-on conversation.
- ***Why is the chosen design safer or more scalable?***
  - One selected target is safer than indefinite ambiguity because implementation work eventually needs a concrete provider direction to stay coherent.
  - Keeping that target behind adapters is more scalable than direct vendor coupling because later swaps remain operational rather than architectural by default.
  - The decision is also safer than claiming a live edge runtime already exists, because it distinguishes selected intent from verified runtime proof explicitly.
- ***What trade-off did the team accept?***
  - The team chose some provider specificity in docs in exchange for less ambiguity about where future edge work should start.
  - Contributors must keep repeating the difference between selected target and integrated runtime proof, which adds wording overhead to closeout and owner docs.
  - Future reviewers should keep that distinction sharp because convenience claims about an unbooted edge path would weaken Sprint 1 evidence discipline.

---

### D3-T5 - keep self-hosted local Langfuse and MLflow as the Sprint 1 proof baseline with managed later options

- ***What was built?***
  - Sprint 001 Deliverable 3 proves one self-hosted local Langfuse path and one self-hosted local MLflow path instead of claiming managed service operations the branch cannot verify directly.
  - The repo keeps those backends in compose-backed and local-service proof flows so reviewers can reproduce bounded observability and evaluation evidence without external tenant access.
  - Root docs state that managed Langfuse and managed MLflow remain later deployment options as long as adapter boundaries and evidence semantics stay unchanged.
- ***Why was it chosen?***
  - The branch already proves local quality evidence honestly, while managed-service claims would require credentials, tenants, and persistence the repository does not control.
  - Self-hosted local proof gives Sprint 1 a reproducible baseline without pretending that early environment convenience should decide the long-term vendor contract.
  - This approach preserves the option to move toward managed operations later without rewriting the product-facing evaluation and telemetry boundaries immediately afterward.
- ***What boundaries does it own?***
  - This decision owns the current Sprint 1 backend posture for Langfuse and MLflow evidence, including the rule that those proof paths are self-hosted and local.
  - It owns the statement that managed observability backends are future deployment choices rather than current operational truth or required product contracts.
  - It does not own collector routing, Prometheus metrics, Grafana dashboards, or generic runtime telemetry rules that are covered by adjacent Deliverable 3 decisions.
- ***What breaks if it changes?***
  - Reviewers would lose a truthful distinction between local proof the branch can reproduce and managed service behavior the branch cannot currently validate.
  - Future migrations could leak vendor assumptions into product contracts if managed backends were treated as architectural facts instead of replaceable adapter targets.
  - Sprint closeout wording would drift if local evidence were described as managed durability without matching external deployments and retained records.
- ***What known edge cases or failure modes matter here?***
  - A local service can prove API usage and stored records while still failing to match future managed networking, auth, or retention characteristics.
  - Teams may assume a managed vendor upgrade is trivial, even though adapter boundaries still need explicit credential, routing, and data-retention review.
  - Local Langfuse and MLflow success does not prove team-shared durability when storage lives only under local compose volumes or build directories.
- ***Why does this work matter?***
  - Sprint 001 needed honest AI-quality and experiment evidence without waiting for platform accounts or hosted operations to become available.
  - It keeps the repo's observability and evaluation story reviewable because maintainers can reproduce the exact bounded path from checked-in docs and commands.
  - This work also makes later managed adoption safer because the current baseline already distinguishes product contracts from backend hosting choices.
- ***What capability does it unlock?***
  - Sprint 2 can build richer evaluation and observability flows against known adapters instead of reopening where AI-quality evidence belongs.
  - Operators can later swap self-hosted local backends for managed services without changing the user-facing runtime contracts that already exist.
  - Reviewers gain one durable baseline for comparing local proof, managed follow-up work, and future deployment claims with less ambiguity.
- ***Why is the chosen design safer or more scalable?***
  - Self-hosted local proof is safer than premature managed claims because the repository can reproduce and inspect the resulting evidence directly.
  - Adapter-preserving backend swaps scale better than product-contract rewrites because later hosting changes remain operational rather than architectural by default.
  - Keeping managed adoption deferred also reduces lock-in risk while the product and observability surfaces are still settling during the rebuild.
- ***What trade-off did the team accept?***
  - The team chose lower fidelity to future hosted operations in exchange for reproducible local proof that does not depend on external accounts.
  - Contributors must keep local compose and proof commands healthy, which adds setup overhead compared with pointing at a managed service.
  - Future reviewers should preserve this honesty even when managed services arrive, because reproducible proof still matters alongside hosted convenience.

---

### D3-T4 - require durable observability and metrics recording for Sprint 1 quality claims

- ***What was built?***
  - Sprint 001 Deliverable 3 documents that critical-path observability claims need durable recorded evidence rather than screenshots, memory, or prose-only summaries.
  - The root docs align versioned dashboards, alert rules, machine-readable artifacts, and replayable local telemetry stores as the acceptable recording surfaces for those claims.
  - Testing and operations guidance distinguish helper screenshots from the durable evidence that branch reviews and later comparisons depend on.
- ***Why was it chosen?***
  - Sprint 1 quality claims were becoming broad enough that reviewers needed a stable rule for what counts as durable evidence.
  - Metrics and traces lose most of their value when a branch cannot regenerate, inspect, or compare them after the original run is gone.
  - This rule fits the governed monorepo posture better than relying on human interpretation of dashboards that only existed temporarily in local browsers.
- ***What boundaries does it own?***
  - This decision owns the evidence rule for recorded observability, evaluation, and performance claims that appear in root docs or sprint closeout materials.
  - It owns the requirement that durable records live in versioned config, machine-readable artifacts, or replayable stores rather than transient notes alone.
  - It does not define every future metric name, SLO target, or dashboard panel shape for later sprints.
- ***What breaks if it changes?***
  - Reviewers would have no consistent way to tell whether a branch proved a metric trend or merely described one convincingly.
  - Sprint closeout comparisons would become unreliable because recorded evidence could disappear between runs, machines, or review sessions.
  - Future observability work might fork into incompatible evidence styles that are difficult to audit, reproduce, or automate.
- ***What known edge cases or failure modes matter here?***
  - A dashboard screenshot can look authoritative while hiding the exact query, timeframe, or alert definition that produced the visible number.
  - Build-directory stores can be replayable locally while still being unsuitable as long-term team evidence unless docs label them as local proof only.
  - Machine-readable artifacts can still mislead if they are detached from the command, dataset, or collector path that generated them.
- ***Why does this work matter?***
  - It makes Sprint 1 quality work reviewable across time instead of confining confidence to whoever watched one original run.
  - The rule protects the repo from inflated metrics claims that would otherwise outrun the evidence stored alongside the branch.
  - This decision also keeps observability aligned with the broader governance model that favors durable, inspectable, versioned technical truth.
- ***What capability does it unlock?***
  - Later sprints can compare performance, eval, and observability changes against prior recorded evidence without recreating baseline theory first.
  - Reviewers can ask for narrower proofs because they know exactly which recording surfaces should exist when a branch makes quality claims.
  - Automation can evolve around the same evidence surfaces instead of retrofitting structure onto informal screenshots and handwritten notes later.
- ***Why is the chosen design safer or more scalable?***
  - Durable recording is safer than screenshot-only review because exact metrics, queries, and artifacts remain inspectable after the original run ends.
  - Versioned evidence scales better than oral or chat-based reporting because many reviewers can inspect the same proof asynchronously.
  - Replayable local stores also scale better for bounded experiments because they let maintainers confirm claims without reconstructing hidden environment state.
- ***What trade-off did the team accept?***
  - The team chose extra artifact, dashboard, and alert maintenance work in exchange for more trustworthy long-term quality comparisons.
  - Contributors lose some convenience because they must preserve or regenerate evidence instead of relying on one successful local viewing session.
  - Future reviewers should keep that burden, since weak evidence rules would make later performance and observability claims much harder to trust.

---

### D3-T3 - make compose-backed collector-routed API and ingest traces the local observability baseline

- ***What was built?***
  - Sprint 001 Deliverable 3 routes API and ingest OpenTelemetry traces through the local collector instead of leaving collector wiring as dead scaffold text.
  - The local compose stack boots the collector, Prometheus, and Grafana together with versioned dashboard and alert artifacts for the critical runtime path.
  - A reproducible probe replays auth, workspace action, ingest execution, metrics export, and collector evidence capture against the bounded local stack.
  - The tracked eval and performance proof artifacts remain repo-local harness outputs, so the decision keeps collector evidence as a distinct proof path instead of overstating those artifacts.
- ***Why was it chosen?***
  - Deliverable 3 needed honest observability proof, and local files plus custom JSON rows were no longer enough for that standard.
  - Collector-routed traces preserve the OpenTelemetry contract already locked in planning without inventing a second local routing story afterward.
  - Versioned dashboards and alert rules were chosen because manual console setup would drift too easily from governed repository review.
- ***What boundaries does it own?***
  - This decision owns the compose-backed local observability baseline for API and ingest traces, Prometheus metrics, Grafana dashboards, and alert rule artifacts.
  - It owns request-to-job trace continuity as far as the repo can prove locally through browser request headers, API spans, and ingest child spans.
  - It does not claim full browser-native SDK instrumentation, Langfuse AI tracing, hosted deployment evidence, or production retention guarantees.
- ***What breaks if it changes?***
  - Reviewers would lose one reproducible path for proving that API requests and ingest execution still share a real trace lineage.
  - Future observability work could fork into incompatible local topologies if the collector stopped being the enforced routing point.
  - Alert and dashboard expectations for the Sprint 1 critical path would drift back into undocumented manual operator state.
- ***What known edge cases or failure modes matter here?***
  - Browser requests currently seed continuity through W3C trace headers, but full browser OTel SDK coverage remains intentionally partial.
  - The runtime-eval harness generates telemetry-derived proof artifacts without traversing the collector, so docs must keep that evidence distinct from collector-export confirmation.
  - Local compose startup order can briefly race collector readiness, so proof scripts and docs must stay explicit about replay timing.
  - Durable runtime telemetry rows still help local baselines, but they are not a substitute for collector-exported traces across processes.
- ***Why does this work matter?***
  - Sprint 001 needed at least one honest end-to-end observability path before hosted deployment or AI trace claims become credible.
  - It turns the repo from observability intent and scaffolds into a locally runnable trace, metrics, dashboard, and alert baseline.
  - This work also gives maintainers a concrete verification script instead of asking reviewers to trust hand-waved screenshots.
- ***What capability does it unlock?***
  - Sprint 2 can extend the same collector, dashboard, and alert surfaces instead of replacing local proof wiring with a different stack.
  - The critical runtime path can be replayed locally with evidence that spans both the request-serving and background execution boundaries.
  - Operators can inspect Prometheus and Grafana outputs without reconstructing datasource, dashboard, or alert setup by hand.
- ***Why is the chosen design safer or more scalable?***
  - Collector-routed traces are safer than direct backend-specific exporters because they keep the telemetry routing layer provider-neutral from the start.
  - Repo-owned Grafana and Prometheus artifacts scale better than UI-only setup because review and rollback stay versioned together.
  - A bounded API plus ingest implementation was safer than broad platforming because it proves the critical path without overstating unfinished surfaces.
- ***What trade-off did the team accept?***
  - The team kept partial browser instrumentation rather than blocking the whole deliverable on a larger client-side observability project.
  - Local proof writes trace exports to a file-backed collector artifact, which is less rich than a full trace backend but easier to prove.
  - Compose startup remains dependency-heavy because runtime evidence is preferred over a lighter but scaffold-only observability story.

---

### D2-T3 - keep edge, CDN, and API gateway choices deferred behind adapters during Sprint 1

- ***What was built?***
  - Sprint 001 Deliverable 2 keeps edge routing, CDN placement, and API gateway insertion as designed seams without locking a concrete provider into the runtime contracts.
  - Root docs state that those network and delivery choices remain intentionally undecided while the branch proves only the bounded local runtime path.
  - The architecture and infra docs both tie those future choices to adapter-preserving boundaries rather than direct public contract changes.
- ***Why was it chosen?***
  - Sprint 1 needed a real runtime slice sooner than it needed final traffic-routing or asset-delivery infrastructure selections.
  - Locking a gateway or CDN too early would add provider bias before telemetry, scale, or security data justified one concrete option.
  - Deferring the decision fits the repo posture of designing seams early while activating only the smallest honest runtime surface first.
- ***What boundaries does it own?***
  - This decision owns the rule that edge, CDN, and gateway choices are deferred infrastructure seams during Sprint 1.
  - It owns the expectation that later activation happens behind adapters and does not rewrite public API envelopes casually.
  - It does not own lower-level runtime hosting for the local proof slice or the broader Cloud Run target posture already documented elsewhere.
- ***What breaks if it changes?***
  - Premature provider selection could leak edge or gateway assumptions into contracts that should stay stable for clients and services.
  - Reviewers would lose the explicit line between designed seams and truly locked infrastructure choices inside Sprint 1 documentation.
  - Future migration work would become more expensive if runtime code started depending directly on one vendor's routing conventions too early.
- ***What known edge cases or failure modes matter here?***
  - Teams may treat a placeholder reverse proxy or local dev server as proof that the production gateway decision is already made.
  - Asset URLs and caching headers can accidentally encode CDN assumptions even when docs say the provider remains undecided.
  - Security hardening work may pressure the repo toward a gateway prematurely unless adapter boundaries remain explicit in review.
- ***Why does this work matter?***
  - It protects Sprint 1 from expanding into infrastructure selection work that is not required to prove the bounded runtime slice.
  - The decision keeps public contracts cleaner because client-facing shapes do not inherit temporary edge-provider details accidentally.
  - This work also leaves later scale decisions easier to review because the repo already marks them as deferred seams rather than silent assumptions.
- ***What capability does it unlock?***
  - Later sprints can adopt a gateway, CDN, or edge runtime when real latency, security, or cost signals justify that move.
  - Operators can compare provider options against the same stable contracts instead of revisiting the client-facing API design each time.
  - Reviewers gain a durable explanation for why Sprint 1 intentionally stops before broader network-platform commitments are made.
- ***Why is the chosen design safer or more scalable?***
  - Deferral is safer than premature locking because routing and caching vendors often impose subtle contract assumptions that are hard to unwind.
  - Adapter-backed seams scale better because later platform insertions can change traffic flow without forcing product-level rewrites everywhere.
  - This choice also keeps the monorepo more explainable by separating current runtime proof from future infrastructure optimization decisions.
- ***What trade-off did the team accept?***
  - The team chose some continued ambiguity about eventual edge architecture in exchange for tighter Sprint 1 focus and lower lock-in risk.
  - Contributors do not get immediate provider-specific optimization guidance, which can feel slower during early deployment planning.
  - Future reviewers should preserve that patience until concrete operational evidence justifies choosing one gateway, CDN, or edge platform.

---

### D2-T2 - make Supabase the default Sprint 1 adapter target without treating it as permanent lock-in

- ***What was built?***
  - Sprint 001 Deliverable 2 names Supabase as the default adapter target for auth, operational Postgres, and storage-oriented contracts in root docs.
  - The same docs also state that Supabase is a current implementation target rather than a permanent domain commitment or naming authority.
  - Architecture, infrastructure, and operations guidance align on adapter-first wording so provider specifics stay behind owned boundaries.
- ***Why was it chosen?***
  - The branch needed one concrete target for browser-safe auth, relational policy, and storage planning without pretending the vendor decision is irreversible.
  - Supabase fits the current runtime slice well because it combines Postgres, auth, and storage concerns behind one practical integration target.
  - Keeping the target explicit is clearer than vague neutrality, but treating it as an adapter choice preserves flexibility for later replacements.
- ***What boundaries does it own?***
  - This decision owns the default provider-target statement for Sprint 1 auth, relational, and storage adapter planning.
  - It owns the rule that product and contract layers must not depend directly on Supabase-specific naming, SDK shapes, or hosted assumptions.
  - It does not mandate that every local proof path already run on Supabase, nor does it settle future managed deployment posture permanently.
- ***What breaks if it changes?***
  - Root docs would drift into confusion if one file named Supabase as a baseline while another described total provider neutrality without a concrete target.
  - Future provider swaps would become harder if product contracts quietly started depending on Supabase-only concepts during routine runtime work.
  - Reviewers for auth and storage changes would lose a stable baseline for evaluating whether a branch preserved adapter-first behavior.
- ***What known edge cases or failure modes matter here?***
  - Contributors may misread “default target” as permission to import provider SDK assumptions directly into shared contracts or app entrypoints.
  - Local sqlite proof can coexist with Supabase-targeted production adapters, so docs must keep local runtime proof separate from later hosted integration intent.
  - Supabase bundles multiple concerns together, which can obscure the fact that auth, database, and storage adapters may evolve at different speeds.
- ***Why does this work matter?***
  - It gives Sprint 1 a truthful provider direction for current planning while still honoring the governed repo rule against casual lock-in.
  - The decision reduces repeated debate over whether the branch is completely provider-agnostic or already biased toward one practical target.
  - This work also helps later sprint docs speak consistently about auth, data, and storage boundaries across local proof and managed follow-on work.
- ***What capability does it unlock?***
  - Sprint 2 can implement richer auth, database, and storage adapters against one named default target without reopening the provider debate first.
  - Reviewers can judge later provider work against an explicit rule: integrate concretely, but keep the contract and adapter boundary replaceable.
  - Operators can evolve deployment choices gradually because the default target is documented as a baseline, not an irreversible architecture law.
- ***Why is the chosen design safer or more scalable?***
  - A named default target is safer than vague neutrality because implementation work still needs one practical starting point to stay coherent.
  - Adapter-first wording is more scalable than direct vendor coupling because later provider changes remain localized instead of rippling through clients and contracts.
  - This balance also lowers review ambiguity by making both the current target and the anti-lock-in rule visible in the same durable record.
- ***What trade-off did the team accept?***
  - The team chose a little extra wording complexity because the docs must describe both a real target and a non-lock-in rule simultaneously.
  - Contributors need discipline to avoid turning a default target into silent architectural dependence inside shared layers.
  - Future reviewers should keep enforcing that distinction, since convenience coupling would erase the flexibility this decision intentionally preserves.

---

### D2-T1 - lock one bounded multi-surface runtime slice before broader platform expansion

- ***What was built?***
  - Sprint 001 Deliverable 2 proves one bounded runtime slice across web, extension, API, ingest, and a shared local runtime store instead of scattered shell demos.
  - The slice covers sign-in, shared identity resolution, workspace bootstrap, one durable action write, background processing, and baseline metrics export.
  - Closeout guidance describes that slice as the actual Sprint 1 runtime baseline rather than an unfinished precursor blocked by unrelated external follow-up work.
- ***Why was it chosen?***
  - The rebuild needed one real end-to-end path so later features could attach to proven contracts and runtime boundaries.
  - A bounded slice was more valuable than broader but shallower scaffolding because it established truthful runtime behavior under governed repo rules.
  - This choice also kept Sprint 1 focused on proving the platform shape before expanding into richer AI, graph, or scale features.
- ***What boundaries does it own?***
  - This decision owns the definition of the first real runtime slice for Sprint 1 across the active product and service surfaces.
  - It owns the rule that shared identity, durable writes, and background execution must cross the approved runtime boundaries rather than app-local shortcuts.
  - It does not claim full production deployment, broad feature coverage, or final provider-specific infrastructure activation beyond the bounded slice.
- ***What breaks if it changes?***
  - Sprint 2 work would lose the stable baseline that later features and quality systems are supposed to extend.
  - Reviewers could no longer rely on one agreed runtime path when evaluating changes to auth, workspace, jobs, or observability.
  - Closeout language would regress into prototype-style ambiguity if the repo stopped naming which slice is real.
- ***What known edge cases or failure modes matter here?***
  - Local proof can overstate maturity if docs fail to distinguish bounded integration from full managed deployment readiness.
  - A single slice may hide unproven adjacent flows, so later docs must stay precise about what the branch still does not claim.
  - Background execution proof can appear synchronous to users even when the repo correctly maintains a separate ingest runtime boundary.
- ***Why does this work matter?***
  - It turns Sprint 1 from a governance-only reset into a platform rebuild with one honest runtime path.
  - The decision gives quality, testing, and observability work a concrete critical path instead of a theoretical architecture sketch.
  - This baseline also makes the repo easier to review because product, service, and job boundaries have one shared reference example.
- ***What capability does it unlock?***
  - Later deliverables can attach richer auth, capture, retrieval, and tutoring behaviors to the same bounded runtime spine.
  - Observability and evaluation systems can compare future changes against one concrete cross-surface path that already exists.
  - Contributors can reason about where new runtime work belongs because the first integrated slice already demonstrates the intended topology.
- ***Why is the chosen design safer or more scalable?***
  - One bounded slice is safer than many partial shells because it exposes real contract and runtime failures earlier.
  - It scales better as a platform baseline because later features can extend an existing end-to-end path instead of inventing their own.
  - The approach also lowers documentation drift by tying root docs and closeout language to one reproducible runtime reality.
- ***What trade-off did the team accept?***
  - The team chose narrower functional scope in exchange for a more trustworthy integrated baseline during Sprint 1.
  - Some future runtime surfaces remain reserved or scaffolded, which can feel incomplete beside the proven critical path.
  - Future reviewers should preserve that boundedness because over-claiming Sprint 1 would weaken the repo's evidence-first posture.

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
  - Placeholder strings can look fake to humans while still matching database or credential patterns strongly enough to trigger automated secret scanners.
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
  - Synthetic placeholders scale better than realistic-looking examples because security tooling stays high-signal as more example configuration surfaces are added.
  - Test isolation is more scalable than environment-dependent expectations because CI providers and local shells export different commit metadata by default.
- ***What trade-off did the team accept?***
  - The team took slightly more explicit verifier and workflow semantics so contributors must understand why two repository states can both matter.
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
