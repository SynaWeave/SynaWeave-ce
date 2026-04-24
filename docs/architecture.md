# 🏗️ Architecture

## 🧩 Purpose

This file explains the system design for SynaWeave CE.
It is intentionally visual and diagram-heavy so the repo shows the product, platform, and pedagogy shape clearly.

For locked infra choices and naming rules, read:
- `docs/infra.md`
- `docs/legend.md`

---

## 🧠 Architecture thesis

SynaWeave CE is a **knowledge-weaving learning OS**.
It combines:
- a capture engine
- a knowledge engine
- a study engine
- an adaptive tutor
- a visible data and ML platform

The tutor is not just a chatbot.
It is an orchestrator that chooses the right teaching mode for the learner, concept, and study goal.

---

## 🔒 Locked learning-system pillars

These product pillars are non-negotiable inside the core architecture:
- block-based second-brain workspace
- deep-linked source provenance
- spaced repetition and retrieval practice
- Zettelkasten-style concept linking
- Feynman-style explain-back tutoring
- adaptive agentic tutoring
- programming-native pedagogy for SWE, ML, and AI learners
- learner-state modeling and personalization
- graph-grounded retrieval and recommendation
- evaluation and observability that remain visible as product assets

---

## 🔒 Locked tutor contract

The adaptive tutor must choose among multiple modes rather than collapsing every study event into one chat response.

The decision inputs are:
- learner state
- source type
- concept difficulty
- confidence and confusion signals
- forgetting risk
- study goal
- interview readiness
- modality fit for the concept

The first locked mode family is:
- free recall
- fill in the blank
- explain-back
- conversation-style coaching
- refined multiple choice
- matching pairs
- sequencing and ordering
- hotspot and image mapping
- branching scenarios
- interview-style prompts
- Parsons or code-ordering reconstruction
- worked-example completion
- debug-the-mistake
- compare-and-justify
- system-design walkthrough
- experiment-analysis walkthrough

---

## 🌐 System map

```mermaid
flowchart TB
    U[Learner]
    EXT[SW extension
thin capture client]
    WEB[SW web
control plane]
    API[API
FastAPI boundary]
    CAP[Capture layer]
    KN[Knowledge layer]
    ST[Study layer]
    PED[Pedagogy engine]
    LM[Learner model]
    RET[Retrieval + ranking]
    EVAL[Evals + traces]
    DB[(DB / PG)]
    OBJ[(OBJ)]
    GRAPH[(GRAPH)]

    U --> EXT
    U --> WEB
    EXT --> API
    WEB --> API
    API --> CAP
    API --> ST
    API --> PED
    CAP --> KN
    KN --> DB
    KN --> OBJ
    KN --> GRAPH
    PED --> LM
    PED --> RET
    PED --> ST
    PED --> EVAL
    LM --> DB
    RET --> DB
    RET --> GRAPH
    ST --> DB
```

---

## 🧱 Product planes

```mermaid
flowchart LR
    XP[Experience plane
extension + web] --> PROD[Product plane
API + study flows]
    PROD --> DATA[Data plane
ingest + clean + feature + index]
    PROD --> AI[AI plane
retrieval + tutor + eval]
    PROD --> OPS[Ops plane
trace + metric + log + alert]
    DATA --> AI
    AI --> OPS
```

### Experience plane
- extension side panel
- web dashboard
- block-based learning canvas
- recommendations and tutor UI

### Product plane
- API boundary
- auth/session checks
- study state writes
- card editing and study history

### Data plane
- ingest
- clean
- chunk
- label
- embed
- graph link
- index
- feature engineering

### AI plane
- retrieval
- reranking
- pedagogy engine
- learner-state updates
- recommendation logic
- eval feedback loops

### Ops plane
- OTel traces
- metrics
- logs
- eval dashboards
- experiment records

---

## 📝 Capture-to-study flow

```mermaid
sequenceDiagram
    participant L as Learner
    participant X as Extension/Web
    participant A as API
    participant C as Capture
    participant K as Knowledge
    participant S as Study
    participant P as Pedagogy

    L->>X: capture source / ask question / open study deck
    X->>A: send normalized request
    A->>C: persist raw source + metadata
    C->>K: clean + chunk + embed + link
    K-->>A: indexed study artifact
    A->>P: request next learning action
    P->>S: generate or select study block
    S-->>X: card, quiz, hint, or coaching step
    X-->>L: grounded study response
```

---

## 🤖 Pedagogy engine

The pedagogy engine is the tutor’s decision system.
It should select mode based on:
- learner state
- source type
- concept difficulty
- confidence / confusion signal
- forgetting risk
- study goal
- interview readiness
- modality fit

```mermaid
flowchart TD
    IN[Question / study event] --> SIG[Signals
state + risk + goal + source]
    SIG --> SEL{Mode select}
    SEL --> FR[free recall]
    SEL --> FIB[fill in blank]
    SEL --> EXB[explain-back]
    SEL --> COACH[coaching chat]
    SEL --> MCQ[refined MCQ]
    SEL --> MATCH[matching]
    SEL --> ORDER[ordering / sequencing]
    SEL --> HOT[hotspot / image map]
    SEL --> BRANCH[branching scenario]
    SEL --> INT[interview prompt]
    SEL --> PARS[Parsons / code ordering]
    SEL --> WORK[worked example]
    SEL --> DEBUG[debug the mistake]
    SEL --> CJ[compare and justify]
    SEL --> SD[system design walkthrough]
    SEL --> EXP[experiment analysis]
    FR --> OUT[graded response + state update]
    FIB --> OUT
    EXB --> OUT
    COACH --> OUT
    MCQ --> OUT
    MATCH --> OUT
    ORDER --> OUT
    HOT --> OUT
    BRANCH --> OUT
    INT --> OUT
    PARS --> OUT
    WORK --> OUT
    DEBUG --> OUT
    CJ --> OUT
    SD --> OUT
    EXP --> OUT
```

---

## 🧠 Learner-state model

```mermaid
flowchart LR
    HIST[review history] --> LM[Learner model]
    RESP[answer quality] --> LM
    TIME[latency + spacing] --> LM
    SRC[source confidence] --> LM
    LM --> MAST[concept mastery]
    LM --> MIS[misconception clusters]
    LM --> RISK[forgetting risk]
    LM --> READY[interview readiness]
    LM --> MODE[preferred support mode]
```

The learner model should track:
- concept mastery
- misconception clusters
- question intent
- source confidence
- forgetting risk
- interview readiness
- preferred support mode
- review history by concept and artifact type

---

## 👨‍💻 SWE / ML / AI pedagogy layer

This product is programming-native by design.
The tutor must natively support:
- code tracing
- algorithm sequencing
- pipeline ordering
- architecture tradeoff reasoning
- eval design
- debugging and failure analysis
- interview rehearsal
- notebook and experiment interpretation

```mermaid
flowchart LR
    CODE[code / notebook / design input] --> PED[Pedagogy engine]
    PED --> TRACE[code tracing]
    PED --> ORDER[algorithm or pipeline ordering]
    PED --> NEXT[complete next step]
    PED --> LINE[explain line / output]
    PED --> DEBUG[debug mistake]
    PED --> COMP[compare to reference]
    PED --> ARCH[architecture sequencing]
    PED --> EVAL[eval or hyperparam plan]
```

---

## 🔍 Retrieval and recommendation stack

```mermaid
flowchart LR
    SRC[raw sources] --> CLEAN[clean + chunk]
    CLEAN --> EMB[embed]
    CLEAN --> LINK[concept link]
    LINK --> GRAPH[(GRAPH)]
    EMB --> VEC[(VEC in PG)]
    CLEAN --> DB[(DB)]
    Q[study query] --> RET[retrieve]
    RET --> VEC
    RET --> GRAPH
    RET --> DB
    RET --> RANK[rank + fuse]
    RANK --> PED[Pedagogy engine]
```

The first retrieval stack should stay simple where possible:
- DB + pgvector first
- graph augmentation where it materially improves the result
- recommendation logic driven by learner state and study history

---

## 🧪 Evals and observability as product assets

```mermaid
flowchart LR
    API --> TRACE[trace]
    PED --> EVAL[eval]
    JOB --> EXP[experiment]
    TRACE --> LF[LF]
    EVAL --> LF
    EVAL --> MLF[MLF]
    EXP --> MLF
    JOB --> MF[MF]
```

These are not hidden admin leftovers.
They should be visible in:
- internal dashboards
- tutor quality reviews
- experiment comparisons
- ingestion quality checks
- recommendation quality checks

---

## 🔐 Fail-open and fail-closed architecture

```mermaid
flowchart LR
    UX[learner-facing flow] --> OPEN[fail open where safe]
    PRIV[privileged flow] --> CLOSED[fail closed]
```

Fail open examples:
- recommendation refresh
- non-critical graph enrichment
- optional telemetry fan-out
- best-effort tagging or grouping

Fail closed examples:
- auth/session checks
- destructive writes
- admin tools
- billing and entitlements
- policy enforcement

---

## 🧩 Open-core split

```mermaid
flowchart LR
    CORE[AGPL core] --> EXT[extension]
    CORE --> WEB[web app]
    CORE --> API[API]
    CORE --> QUIZ[quizzes]
    CORE --> SRS[spaced repetition]
    CORE --> LM[learner model]
    CORE --> OBS[observability + evals]
    CORE --> OPENAPI[open APIs + adapters]

    PROP[proprietary layer] --> ADS[ads + targeting]
    PROP --> BILL[billing + subscriptions]
    PROP --> ENT[entitlements]
    PROP --> PTS[wallet / rewards]
    PROP --> GROW[growth analytics]
```

The AGPL core owns product learning value.
The proprietary layer owns monetization and growth mechanics.

---

## 🚀 Deployment posture

```mermaid
flowchart LR
    DEV[local docker] --> CR[Cloud Run first]
    CR --> GKE[GKE later if needed]
```

The repo should already have the seams for the GKE pivot, but Cloud Run is still the right first hosted move.
