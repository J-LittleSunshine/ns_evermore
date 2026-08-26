# NGRP-001 — Component Internal Design / ns_node / Batch 1 DAD Evidence

## Authority Metadata

- **Authorization:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_NODE / BATCH_1 / LOCAL_READINESS_GOVERNED_EXECUTION_PROTECTED_EFFECT_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Producing Entry HEAD:** `70f79436359b03e49f2a31d1a8f5144af52ada34`
- **Candidate Commit:** `a89db26412d143afcfe5735354848ee0a142c360`
- **Recovered GAC Epoch:** `GAC-EPOCH-0081`
- **Decision Registry:** `0.0.29 / CURRENT / NORMATIVE`
- **DAD Authority:** bounded internal architecture refinement only; no Owner-reserved MDE decision may be selected here.

All DADs below refine already accepted N1/N2/N3 boundaries and ND-R01/02/03 roles. They do not alter Product Authority, canonical SoT, final Actual-state ownership, Tenant/Principal/Policy/Trust semantics, material offline fail policy, provider/protocol/storage identity, universal execution guarantee or N4 recovery semantics.

---

# CID-ND-B1-DAD-001 — 23-responsibility N1/N2/N3 decomposition

## Decision / Issue

How should N1/N2/N3 be decomposed deeply enough that readiness, execution Attempt and protected Effect/source-fact responsibilities are implementation-derivable without turning accepted component boundaries into one Node-local God responsibility?

## Context

Accepted upstream fixes three distinct Actual-state/source partitions: N1 readiness/applied config, N2 Attempt, N3 Effect/source fact. The current Batch must close internal responsibility ownership while preserving `Admission != Dispatch != Attempt != Effect` and without designing N4.

## Alternatives Considered

- **A — one responsibility per accepted boundary:** simple but leaves lifecycle/currentness/history/contract duties under-specified.
- **B — one universal Node Execution Core:** rejected because it collapses readiness, Attempt and Effect ownership.
- **C — cohesive architecture-semantic responsibilities inside each accepted boundary:** preserves owner partitions while making inputs/outputs/failure/history explicit.

## Selected Design-semantic Result

Select **C**:

```text
N1 → 7 responsibilities
N2 → 9 responsibilities
N3 → 7 responsibilities
Total → 23
```

Labels are document-local and do not imply modules/processes/classes.

## Rationale

The 23 responsibilities align with distinct semantic lifecycles: context binding, source-owned actual state, qualification/currentness, history/provenance and stable-contract production. They are fine-grained enough to eliminate architecture gaps but coarse enough to avoid implementation topology.

## Responsibility Consequence

Every authorized N1/N2/N3 material pressure has exactly one principal internal responsibility; duplicate final ownership is zero.

## Dependency Consequence

Typed dependencies can be expressed with SDD/ACD/EL/HPL/XED and analyzed without treating runtime evidence feedback as semantic recursion.

## Authority / SoT / Actual-state Consequence

No Authority or SoT moves. N1 remains readiness/applied owner, N2 Attempt owner, N3 protected Effect/local-source owner.

## RCP Consequence

RCP-04 maps principally to N1-R07, RCP-07 to N2-R09 and RCP-08 to N3-R07 after source responsibilities establish their owned evidence.

## Failure / Offline Consequence

Failure/currentness/offline evidence is owned by the same source boundary rather than a new cross-boundary manager. N4 remains future.

## Explicit Non-implications

No package/service/process/session/store/queue/browser topology is selected. `23 responsibilities != 23 runtime units`.

## Deferred Implementation Mechanics

Code/module layout, persistence, concurrency, APIs, schemas and deployment.

## Revalidation Trigger

A proposed new responsibility that changes accepted N1/N2/N3 ownership, creates a fourth current-Batch authority partition, or requires N4 semantics.

---

# CID-ND-B1-DAD-002 — Bounded Node readiness and capability-state non-collapse

## Decision / Issue

What does N1 readiness mean, and how is it separated from capability possession, reachability, Trust and Admission?

## Context

RCP-04 runtime consumer expectations require capability/readiness/mode/Applied/currentness evidence. Upstream permanently requires `Reachable != Ready`, `Installed != Accepted`, `Available != Admitted`, `Activated != Authorized`.

## Alternatives Considered

- **A — one boolean Node ready flag:** rejected because it hides capability/mode/config/currentness distinctions.
- **B — readiness inferred from RT-R01 reachability:** rejected because R1 is coordination evidence, not Node-local readiness.
- **C — bounded readiness scoped to Node + capability + execution mode + relevant Applied config and local prerequisites:** selected.

## Selected Design-semantic Result

N1 separately owns:

```text
capability installed evidence
capability available evidence
capability activated evidence
execution-mode readiness
Applied Configuration evidence
bounded readiness qualification
currentness / availability / uncertainty
```

`READY/NOT_READY/UNKNOWN/INDETERMINATE` are architecture-semantic distinctions where evidence supports them, not a mandatory enum.

## Rationale

Readiness must answer whether this Node can locally establish technical/execution-mode applicability for the bounded execution subject, not whether the system authorizes the operation.

## Responsibility Consequence

N1-R02/R03/R04 produce independent dimensions; N1-R05 owns the bounded readiness assertion; N1-R06 owns its currentness/uncertainty.

## Dependency Consequence

N1-R05 has one-way SDD on capability/config/mode definitions. R1 presence is EL/XED only.

## Authority / SoT / Actual-state Consequence

ND-R01 remains final owner of Node-local readiness. Trust stays S4; Admission stays S8; Presence stays RT-R01.

## RCP Consequence

Closes ND-R01 owner-side semantics needed by accepted RCP-04 consumer expectations.

## Failure / Offline Consequence

Unavailable external evidence is not coerced to `NOT_READY`; locally established readiness may coexist with centrally stale/unreachable presence evidence.

## Explicit Non-implications

No universal health check, TTL, heartbeat, readiness formula, session implementation or routing algorithm.

## Deferred Implementation Mechanics

Capability inventory representation, probe mechanics, timers, health-check mechanism and local storage.

## Revalidation Trigger

Any proposal to make readiness imply Trust/Admission, infer it solely from reachability, or create a universal Product readiness law.

---

# CID-ND-B1-DAD-003 — Node Applied Configuration ownership topology

## Decision / Issue

How should Node-side managed configuration participate without absorbing S9 Desired authority or turning Observed projection into source truth?

## Context

Accepted RCP-19 fixes `Desired != Distributed != Applied != Observed`; Desired is S9/SV-R05, Applied belongs to the applicable runtime owner.

## Alternatives Considered

- **A — Node owns desired + applied:** rejected; transfers S9 authority.
- **B — server owns applied because it distributed config:** rejected; distribution evidence is not application evidence.
- **C — N1 owns only Node-local Applied actual-state and retains Desired/Distribution references:** selected.

## Selected Design-semantic Result

N1-R03 owns:

```text
Applied subject/revision/context
application evidence
partial / failure / unknown / stale qualification
temporal/provenance history
```

S9 Desired and item semantic owner remain external accepted owners; Observed remains derived.

## Rationale

Only the local runtime partition can authoritatively assert what it actually applied. Central desired/reconciliation may consume that evidence but cannot replace the source assertion.

## Responsibility Consequence

Applied Configuration becomes an N1 input to readiness while remaining distinct from capability state.

## Dependency Consequence

RCP-19 enters N1 through XED/ACD. No reverse SDD from S9 to Node internal definition is created beyond accepted contract meaning.

## Authority / SoT / Actual-state Consequence

Desired SoT stays S9; Node Applied Actual-state stays N1; Observed stays projection.

## RCP Consequence

Completes the Node Applied contribution to RCP-19 without claiming universal RCP redesign.

## Failure / Offline Consequence

Partial/failed/unknown/conflicting local application is explicit. Offline Node may retain last-known Desired ref + own Applied evidence; disconnect never transfers Desired authority.

## Explicit Non-implications

No config center, push/pull/watch/rollout mechanism, file format, local DB or merge algorithm.

## Deferred Implementation Mechanics

Acquisition/application mechanism, persistence, distribution transport, physical config schema.

## Revalidation Trigger

Any proposal that makes Node Desired authority, server distribution equal Applied, or latest observation a conflict winner.

---

# CID-ND-B1-DAD-004 — Attempt origination boundary after Dispatch and before Effect

## Decision / Issue

When does a Node-owned Attempt become a distinct semantic subject?

## Context

Upstream fixes `Dispatch != Attempt != Effect`. The design must avoid both premature Attempt creation on dispatch receipt and missing evidence for a local execution that fails before a meaningful start/progress event.

## Alternatives Considered

- **A — Dispatch receipt automatically creates Attempt:** rejected; collapses RCP-05 and RCP-07.
- **B — Attempt exists only after protected Effect:** rejected; erases failed/stopped/no-effect execution history and collapses Attempt into Effect.
- **C — originate Attempt when Node actually establishes one bounded local execution responsibility instance under applicable evidence; start/progress/effect remain later independent facts:** selected.

## Selected Design-semantic Result

```text
Dispatch receipt/correlation → N2-R03
Attempt origination + distinct Attempt identity → N2-R04
Attempt started/progress/waiting/stopped evidence → N2-R05
Attempt completion/failure/uncertainty → N2-R06
Protected Effect/source evidence → N3
```

## Rationale

This places Attempt at the correct execution-source boundary and preserves meaningful failed/aborted/no-effect attempts.

## Responsibility Consequence

N2-R04 is the sole Attempt identity originator. N2-R03 cannot mint Attempt identity; N3 only references it.

## Dependency Consequence

N2-R04 depends on N2 context, Admission applicability and Dispatch correlation where applicable. N3 depends one-way on Attempt identity semantics.

## Authority / SoT / Actual-state Consequence

RT-R02 remains Dispatch owner; ND-R02 becomes Attempt owner; ND-R03 remains Effect owner.

## RCP Consequence

RCP-07 is source-distinct from accepted RCP-05; RCP-08 references RCP-07 Attempt identity without collapse.

## Failure / Offline Consequence

A pre-attempt applicability/context failure need not fabricate an Attempt. Once an Attempt exists, failure/unknown/stopped evidence remains source-owned and non-destructive, including offline.

## Explicit Non-implications

No process start boundary, worker allocation event, browser session start, transaction boundary or delivery guarantee is selected.

## Deferred Implementation Mechanics

Concrete executor lifecycle, process/session creation, concurrency and physical IDs.

## Revalidation Trigger

Any proposal to equate Dispatch receipt with Attempt, Effect with Attempt creation, or define a Product-wide once-delivery guarantee.

---

# CID-ND-B1-DAD-005 — Admission / Dispatch consumer applicability without authority transfer

## Decision / Issue

How does N2 consume Formal Admission and Dispatch evidence while remaining an executor rather than an admission/coordination authority?

## Context

S8 RCP-02 and RT-R02 RCP-05 are already accepted owner-side contracts. Node must establish applicability/correlation before Attempt origination but cannot reinterpret source authority.

## Alternatives Considered

- **A — re-evaluate Admission locally:** rejected; creates duplicate Admission Authority.
- **B — trust any Dispatch as sufficient authority:** rejected; `Dispatch != Admission`.
- **C — maintain separate consumer applicability/correlation responsibilities for RCP-02 and RCP-05:** selected.

## Selected Design-semantic Result

N2-R02 performs RCP-02 consumer applicability; N2-R03 performs RCP-05 receipt/applicability/correlation. Both preserve source identities/revisions/provenance and feed N2-R04 without creating source decisions.

## Rationale

The executor needs enough evidence to determine whether it can act under already-established authority and coordination, but authority remains upstream.

## Responsibility Consequence

Formal Admission, Dispatch, Attempt are represented by separate evidence subjects and internal responsibilities.

## Dependency Consequence

RCP-02/05 are XED/ACD; no reverse semantic ownership edge is introduced.

## Authority / SoT / Actual-state Consequence

Admission remains S8; Dispatch remains R2; Node owns only its consumer assessment and later Attempt.

## RCP Consequence

Current Batch refines only Node consumer sides of RCP-02 and RCP-05.

## Failure / Offline Consequence

Stale/unknown/revoked/inapplicable source evidence remains explicit. Retained offline evidence is usable only under producer-defined applicability; no universal fail-open/fail-closed policy is invented.

## Explicit Non-implications

No local token issuer, admission cache-as-authority, reauthorization engine, dispatch acknowledgement protocol or retry law.

## Deferred Implementation Mechanics

Evidence verification plumbing, transport, cache/persistence and API/wire representation.

## Revalidation Trigger

Any attempt to let Node mint/extend Admission, infer Admission from Dispatch, or convert local evidence possession into unlimited authority.

---

# CID-ND-B1-DAD-006 — Attended / unattended unified governed execution topology

## Decision / Issue

Should attended and unattended Node execution be separate semantic executors or two modes of the same governed authority topology?

## Context

Accepted Runtime Responsibility Architecture states both are modes of ND-R02 and both retain the same governance/admission model.

## Alternatives Considered

- **A — separate attended/unattended executors with separate authority:** rejected; creates semantic duplication and bypass risk.
- **B — treat attended execution as user-authorized and unattended as machine-trusted:** rejected; violates IAM/Trust/Admission boundaries.
- **C — same N1/N2/N3 topology with mode-specific readiness prerequisites:** selected.

## Selected Design-semantic Result

N1-R04 qualifies mode readiness; N2 Attempt semantics are identical in authority regardless of mode. Attended may consume legitimate session-binding evidence as a technical prerequisite; unattended has no active-human requirement but gains no extra authority.

## Rationale

Execution mode changes local readiness conditions, not Product authority topology.

## Responsibility Consequence

No duplicate Attempt or Effect owner is created. Mode is recorded as execution context/provenance.

## Dependency Consequence

Mode readiness depends on capability/config/session-binding evidence where applicable; IAM/Admission remain external evidence dependencies.

## Authority / SoT / Actual-state Consequence

User session remains non-authoritative; Trust/Admission unchanged; N2/N3 final ownership unchanged.

## RCP Consequence

RCP-04/07 can carry execution-mode context without defining separate contract families.

## Failure / Offline Consequence

Missing attended session binding can make that mode locally not-ready/unknown where it is a required prerequisite; unattended execution remains governed when no active human is present.

## Explicit Non-implications

No browser profile, desktop/Windows session, daemon, worker session or process topology.

## Deferred Implementation Mechanics

Session discovery/binding mechanics, process lifetime and UI interaction.

## Revalidation Trigger

Any proposal that attended presence bypasses governance or unattended mode receives automatic Trust/Admission.

---

# CID-ND-B1-DAD-007 — Protected Effect / local source fact vs external SoT partition

## Decision / Issue

How does N3 own protected local Effect/source evidence without claiming external/business final truth?

## Context

N3 is final owner of genuinely Node-origin protected Effect/local source facts, while Project Architecture requires external factual SoTs to remain external where accepted.

## Alternatives Considered

- **A — every locally observed fact becomes Node source truth:** rejected; violates external SoT preservation.
- **B — Node never owns source facts, only observations:** rejected; loses accepted N3 local source-fact custody.
- **C — classify Node-origin protected Effect/local-source assertion separately from local evidence of external source facts:** selected.

## Selected Design-semantic Result

N3 distinguishes:

```text
Node-origin protected Effect assertion → N3 final bounded owner
Node-origin local source fact → N3 final bounded owner where genuinely local
external/other-component fact observed/copied locally → N3 owns only evidence/reference/provenance
```

## Rationale

Final ownership follows factual origin/accepted SoT, not storage/location/availability.

## Responsibility Consequence

N3-R03 owns effect occurrence evidence; N3-R04 owns source-owner/SoT qualification; N3-R07 owns history/provenance.

## Dependency Consequence

External source evidence is XED; availability or central projection cannot become SDD authority.

## Authority / SoT / Actual-state Consequence

Local final ownership exists only for bounded Node-origin assertions. External SoT is preserved without duplication.

## RCP Consequence

RCP-08 explicitly carries source-owner/final-SoT reference and local-vs-external qualification.

## Failure / Offline Consequence

External unavailability does not promote local copy. Conflict/unknown remains explicit; no winner is chosen.

## Explicit Non-implications

No reconciliation/merge law, local-wins/central-wins/latest-wins, external-system adapter or DB design.

## Deferred Implementation Mechanics

Resource APIs, evidence capture, storage and external-source access.

## Revalidation Trigger

Any ambiguous/new source whose final factual SoT cannot be derived from accepted architecture, or proposal to promote local copy based on availability.

---

# CID-ND-B1-DAD-008 — Attempt / Effect / business outcome permanent non-collapse

## Decision / Issue

How should local execution completion, protected Effect and domain semantic success relate?

## Context

Accepted architecture permanently separates Attempt, Effect and broader semantic outcome. Node must report useful evidence without inferring what it does not own.

## Alternatives Considered

- **A — Attempt completed == Effect succeeded == business success:** rejected.
- **B — Effect existence determines Attempt success retroactively:** rejected; rewrites Attempt history and creates reverse semantic dependency.
- **C — independent source-owned assertions with explicit correlation:** selected.

## Selected Design-semantic Result

N2 owns Attempt lifecycle/outcome; N3 owns protected Effect/source evidence; domain owner owns Automation/Agent/Business semantic result. Correlation is EL/HPL, not ownership.

## Rationale

An execution can complete without a protected effect, an effect can be partial/uncertain, and business semantics may depend on external/domain evidence beyond Node.

## Responsibility Consequence

N2-R06 never requires N3 success to define N2 completion; N3-R02 references Attempt but cannot rewrite it.

## Dependency Consequence

No reverse SDD from N3 to N2. Effect feedback is EL/HPL only, preserving hard-graph acyclicity.

## Authority / SoT / Actual-state Consequence

Final owners remain singular and distinct.

## RCP Consequence

RCP-07 and RCP-08 remain separate stable subjects; downstream semantic owners must correlate rather than merge.

## Failure / Offline Consequence

Later Effect evidence never erases earlier Attempt failure/uncertainty; later domain success never rewrites Node evidence.

## Explicit Non-implications

No transaction, saga, compensation, rollback or exactly-once semantic.

## Deferred Implementation Mechanics

Domain-specific result interpretation and physical event/evidence flow.

## Revalidation Trigger

Any proposal to make Node local success authoritative for broader Automation/Agent/Business outcome.

---

# CID-ND-B1-DAD-009 — Bounded identities, correlation and non-destructive history

## Decision / Issue

Which Node-local semantic identities are architecture-material, and how is history preserved without choosing physical namespaces?

## Context

Current scope requires Node readiness evidence, Attempt and Effect/source evidence to remain correlatable across dispatch/retry/offline history, while universal ID formats are prohibited.

## Alternatives Considered

- **A — reuse one global Operation ID for all subjects:** rejected; collapses ownership/lifecycle.
- **B — freeze UUID/database/wire IDs:** rejected as implementation leakage/high-migration commitment.
- **C — require bounded semantic identities/references only where independent lifecycle/history requires them:** selected.

## Selected Design-semantic Result

```text
Node/Participant Reference
Capability Reference
Node Capability/Readiness Evidence Identity or Reference
Operation/Work Reference
Admission Evidence Identity
Dispatch Identity
Attempt Identity
Protected Effect/Source Evidence Identity or Reference
```

remain distinct. Physical formats are deferred.

## Rationale

Semantic identity is necessary for lineage and source attribution; physical representation is not architecture-semantic.

## Responsibility Consequence

N1-R07/N2-R09/N3-R07 govern history for their own evidence; source responsibilities establish scoped identities.

## Dependency Consequence

Correlation links are EL/HPL unless a semantic definition truly depends on another identity definition (e.g., N3 Attempt reference).

## Authority / SoT / Actual-state Consequence

Identity reference never transfers ownership.

## RCP Consequence

RCP-04/07/08 have representation-neutral correlation keys/subjects without wire format.

## Failure / Offline Consequence

History remains retainable and non-destructive through disconnect/re-entry; unknown references remain explicit.

## Explicit Non-implications

No UUID version, primary key, message ID, hostname, PID/session ID or global event namespace.

## Deferred Implementation Mechanics

ID encoding/generation/storage/indexing and wire representation.

## Revalidation Trigger

Need for one universal Product namespace, cross-system canonical ID format or irreversible physical identity commitment.

---

# CID-ND-B1-DAD-010 — Failure/currentness/offline evidence without recovery design

## Decision / Issue

How should N1/N2/N3 represent failure, stale/unknown and offline continuity while N4 recovery/reconciliation is explicitly forbidden?

## Context

N1-N3 must remain correct in private/offline/degraded operation and retain evidence consumable by future N4. The Batch may not define recovery scope, replay or conflict winner.

## Alternatives Considered

- **A — defer all uncertainty/offline semantics to N4:** rejected; N1-N3 evidence would be non-derivable and destructive.
- **B — design a local recovery engine now:** rejected as unauthorized N4 progression.
- **C — define source-owner failure/currentness/history obligations only, with explicit future-consumability:** selected.

## Selected Design-semantic Result

N1/N2/N3 reuse accepted uncertainty semantics (`UNKNOWN`, `STALE`, `UNAVAILABLE`, `INDETERMINATE`, `PARTIAL`, `CONFLICTING`, etc. where applicable), preserve source history/provenance and retain evidence in principle. No reconciliation semantics are selected.

## Rationale

Source evidence can be correct and future-recoverable without defining how a future recovery participant exchanges or reconciles it.

## Responsibility Consequence

Each boundary qualifies its own evidence currentness/uncertainty; no cross-boundary local recovery authority is created.

## Dependency Consequence

Future N4 may depend on N1/N2/N3 evidence; current N1/N2/N3 have no SDD on N4.

## Authority / SoT / Actual-state Consequence

Offline does not transfer authority or promote local copies.

## RCP Consequence

RCP-22 gets bounded producer evidence; RCP-20 remains deferred.

## Failure / Offline Consequence

Reconnect != reconciled; sync != proof; replay != retroactive authorization; latest timestamp != winner.

## Explicit Non-implications

No retention store, replay queue, checkpoint, recovery state machine, conflict resolution or synchronization direction.

## Deferred Implementation Mechanics

All N4 internals and physical retention/recovery mechanics.

## Revalidation Trigger

Any requirement to choose local/central/latest winner, replay law, mandatory fail-open/fail-closed behavior or comprehensive Node recovery flow.

---

# CID-ND-B1-DAD-011 — RCP-04 / RCP-07 / RCP-08 owner-side stable semantic contracts

## Decision / Issue

What contract depth is required in this Batch without leaking into DTO/wire/API design or claiming full cross-component closure?

## Context

The authorization explicitly requires representation-neutral stable-contract synthesis for Node Readiness, Attempt and Effect Evidence owner/source sides.

## Alternatives Considered

- **A — only list RCP names:** rejected as insufficient Component Internal Design depth.
- **B — define concrete schemas/APIs:** rejected as implementation/detailed-contract leakage.
- **C — close semantic subjects, ownership, required evidence dimensions, producer/consumer obligations, history/offline/compatibility and explicit non-implications:** selected.

## Selected Design-semantic Result

RCP-04/07/08 are closed at current Node owner/source-side design level with explicit semantic subjects and obligations. Physical representation remains downstream. Full cross-component closure is not inferred.

## Rationale

This level is sufficient to constrain downstream realization and consumers while respecting current authority.

## Responsibility Consequence

N1-R07/N2-R09/N3-R07 steward stable contracts after source facts are established by their respective responsibilities.

## Dependency Consequence

Accepted external producer contracts remain references; no reverse redesign of ns_server/ns_runtime/agent/web/SDK.

## Authority / SoT / Actual-state Consequence

Each RCP names the original fact owner; transport/representation never becomes authority.

## RCP Consequence

RCP-04, RCP-07, RCP-08 owner/source-side closure complete; broader full closure remains GAC/downstream responsibility.

## Failure / Offline Consequence

Contracts explicitly preserve uncertainty, currentness, provenance, history and private/offline compatibility.

## Explicit Non-implications

No JSON/Protobuf/REST/gRPC/WebSocket envelope/DTO/schema/database contract.

## Deferred Implementation Mechanics

Concrete Contract Design/API/schema/serialization binding after appropriate authorization.

## Revalidation Trigger

Need to change semantic owner, merge RCP identities, or make concrete representation a durable Product semantic commitment.

---

# CID-ND-B1-DAD-012 — Bounded RCP limits and RCP-20 deferral

## Decision / Issue

How should the current Batch participate in multi-party RCPs without reverse-designing downstream components or preempting N4?

## Context

Authorization permits narrow consumer/target/executor contributions for RCP-02/03/05/12/13/15/17/19/22/24 and explicitly prohibits comprehensive RCP-20.

## Alternatives Considered

- **A — claim full closure wherever Node can describe expected peers:** rejected; unauthorized cross-component inference.
- **B — omit all bounded contributions:** rejected; leaves Node obligations undefined.
- **C — define only Node-local applicability/correlation/producer obligations and explicit non-claims:** selected.

## Selected Design-semantic Result

The Candidate contains a bounded RCP matrix. RCP-20 contains only evidence future-consumability obligations and no recovery semantics.

## Rationale

Node internal design must be complete about its own obligations but cannot manufacture Agent/Web/SDK/N4 semantics.

## Responsibility Consequence

Cross-domain refs live in N2-R08; target intervention in N2-R07; config in N1-R03; diagnostics/provenance remain distributed to source owners.

## Dependency Consequence

External RCPs are ACD/XED/EL. No forbidden source-side SDD is created.

## Authority / SoT / Actual-state Consequence

Accepted upstream/downstream owners remain unchanged.

## RCP Consequence

No Full RCP-04/07/08 cross-component closure is claimed; no full RCP-12/17/20/22/24 closure is claimed.

## Failure / Offline Consequence

Missing peer evidence remains explicit; Node does not infer remote state or reconciliation.

## Explicit Non-implications

No Agent delegation internals, Web/SDK intent model, Trial UI, N4 recovery or diagnostics aggregator.

## Deferred Implementation Mechanics

Other Product Component Internal Design and future cross-component Contract/SDK design.

## Revalidation Trigger

Any need to decide a peer owner's semantics to make Node design coherent, or any RCP-20 internal recovery requirement.

---

# CID-ND-B1-DAD-013 — Shared Foundation consumption without Product Authority transfer

## Decision / Issue

Which accepted Shared Foundation semantics should Node reuse, and how is a Node-local parallel Foundation avoided?

## Context

The accepted Foundation stack is globally closed. Current Node design requires temporal/currentness, diagnostics/observation, provenance, representation, context propagation, uncertainty, secrets/redaction, compatibility and bootstrap mechanics.

## Alternatives Considered

- **A — create Node-specific equivalents:** rejected as parallel Foundation duplication.
- **B — make Foundation contracts owners of Node facts:** rejected; Foundation mechanics are authority-neutral.
- **C — consume accepted Foundation contracts as mechanics while keeping N1/N2/N3 semantic ownership local:** selected.

## Selected Design-semantic Result

Applicable consumption includes C01/C02/C03/C04/C05/C06/C07/C10/C11/C12/C13/C14, with C09 conditional for later durable-retention realization where required.

## Rationale

All current reusable semantic pressure already has accepted Foundation coverage; no new capability is necessary.

## Responsibility Consequence

N1/N2/N3 responsibilities define Product facts; Foundation supplies reusable mechanics only.

## Dependency Consequence

Foundation dependencies do not become Product SDD ownership and introduce no cross-component Authority cycle.

## Authority / SoT / Actual-state Consequence

Foundation module/provider/storage/transport placement never becomes Node Product Authority or source-fact owner.

## RCP Consequence

RCP-04/07/08 can remain representation-neutral, temporally/provenance rich, uncertainty preserving and redaction compatible.

## Failure / Offline Consequence

Foundation mechanics preserve explicit failure/unknown/private-deployment semantics; no public dependency is introduced.

## Explicit Non-implications

No Provider/vendor/library, database, network protocol or public SaaS selection.

## Deferred Implementation Mechanics

Concrete Foundation Provider realization and Product binding after implementation readiness.

## Revalidation Trigger

Discovery of a mandatory reusable semantic not covered by accepted Foundation, or pressure to create a Node-local duplicate Foundation capability.

---

# CID-ND-B1-DAD-014 — Typed dependency model and acyclic hard SDD graph

## Decision / Issue

How should internal dependencies be classified so execution/effect feedback does not masquerade as semantic recursion?

## Context

The accepted taxonomy is `SDD / ACD / EL / HPL / XED`; only SDD participates in hard cycle analysis. N2 and N3 naturally exchange runtime evidence, which must not become circular semantic ownership.

## Alternatives Considered

- **A — treat every data/evidence flow as SDD:** rejected; would create false cycles and obscure authority.
- **B — omit dependency classification:** rejected; cannot prove architecture derivability.
- **C — classify only semantic-definition prerequisites as SDD and runtime/current evidence as EL/HPL/XED/ACD:** selected.

## Selected Design-semantic Result

The Candidate records explicit N1/N2/N3 hard SDD edges. The only cross-N2→N3 semantic-definition edge is N3-R02 depending on N2-R04 Attempt identity semantics. N2 consumption of Effect evidence is EL/HPL only.

```text
Hard Internal SDD Graph → ACYCLIC
Unresolved SDD Cycle → 0
Authority Cycle → NONE
Circular Actual-state Ownership → NONE
```

## Rationale

Definition dependency and runtime evidence feedback are fundamentally different architecture relationships. Correct typing preserves source ownership and derivability.

## Responsibility Consequence

N2 completion semantics do not depend on N3 Effect success. N3 can correlate to Attempt without controlling Attempt semantics.

## Dependency Consequence

Hard graph is topologically orderable; external contracts remain XED/ACD.

## Authority / SoT / Actual-state Consequence

No evidence flow transfers final ownership.

## RCP Consequence

RCP-07 and RCP-08 correlate while remaining independently defined stable subjects.

## Failure / Offline Consequence

Delayed/missing Effect evidence does not make N2 semantic definition unavailable; it is represented as missing/unknown evidence linkage.

## Explicit Non-implications

No event bus, transaction graph, workflow DAG, callback mechanism or process dependency is selected.

## Deferred Implementation Mechanics

Physical dependency injection, calls/messages/storage and runtime scheduling.

## Revalidation Trigger

Any proposed semantic dependency that introduces an SDD cycle, duplicate final owner or requires feedback to define the upstream source subject itself.

---

# DAD / MDE Classification Audit

```text
DAD Count
→ 14

DAD IDs
→ CID-ND-B1-DAD-001..014

Owner-reserved MDE disguised as DAD
→ 0

New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

No DAD selects universal retry/cancellation/rollback/compensation semantics, exactly-once/at-most-once/at-least-once, conflict winner, cross-Tenant Node coordination, global priority/fairness, mandatory sandbox/browser framework/queue/broker/scheduler/workflow engine/storage engine/public dependency/provider/protocol/framework lock-in, major universal identity namespace or new Product capability.

```text
DAD Evidence Status
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE WITH CANDIDATE
```
