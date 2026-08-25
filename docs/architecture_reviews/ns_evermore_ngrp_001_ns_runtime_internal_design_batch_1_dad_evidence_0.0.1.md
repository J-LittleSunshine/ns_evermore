# NGRP-001 — Component Internal Design / ns_runtime / Batch 1 DAD Evidence

## Authority Metadata

- **Program / Phase:** `NGRP-001 — Component Internal Design / ns_runtime / Batch 1`
- **Scope:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_RUNTIME / BATCH_1 / PRESENCE_AND_GOVERNED_DISPATCH_COORDINATION_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Producing Entry HEAD:** `a4f538f803abd8d3f6135908f80529ccd40b42b7`
- **Candidate Commit:** `4151771af4262aa26f3242c168e41e839e5792b0`
- **Recovered GAC Epoch:** `GAC-EPOCH-0070`
- **Decision Registry:** `0.0.25 / CURRENT / NORMATIVE`
- **DAD Authority:** bounded Component Internal Design only
- **Owner/MDE Authority:** `NOT HELD`

All decisions below refine accepted R1/R2 and RT-R01/RT-R02 semantics only. No DAD moves accepted Authority, SoT or final Actual-state ownership to another Product Component and no DAD selects implementation technology.

---

# CID-RT-B1-DAD-001 — R1/R2 internal decomposition remains semantically distinct

## Decision / Issue

How should authorized R1 and R2 be decomposed internally without collapsing participant presence and governed dispatch into a universal runtime manager?

## Context

Accepted upstream already defines R1 and R2 as distinct Product Component internal boundaries and RT-R01/RT-R02 as distinct Runtime Roles. Component Internal Design must provide sufficient internal responsibility decomposition while preserving that separation.

## Alternatives Considered

- **A — One generic Runtime Coordination responsibility:** compact, but collapses presence, routing, scheduling and dispatch ownership and invites universal-runtime Authority.
- **B — Split every status or evidence kind into many micro-responsibilities:** explicit, but overfragments architecture and turns semantic distinctions into pseudo-services.
- **C — Two cohesive boundary-local decompositions with evidence links between them:** R1 `P01..P05`, R2 `D01..D06`.

## Selected Design-semantic Result

**C selected.**

```text
R1
→ P01 Participant Reference & Coordination-context Binding
→ P02 Connection Observation & Presence-evidence Intake
→ P03 Presence Currentness & Freshness Qualification
→ P04 Reachability Qualification & Uncertainty Custody
→ P05 Presence History, Projection & RCP-03 Contract Governance

R2
→ D01 Admitted-work Intake & Admission-evidence Applicability
→ D02 Work Requirement & Target Correlation
→ D03 Routing Candidate Qualification
→ D04 Scheduling Coordination & Bounded Ordering
→ D05 Dispatch Decision, Handoff & Evidence Custody
→ D06 Dispatch Lineage, History & Later-attempt Correlation
```

## Rationale

The split follows accepted semantic ownership: R1 owns connection/presence/reachability coordination facts; R2 owns route/schedule/dispatch coordination facts. It provides enough internal structure to prevent implementation teams from inventing authority or state ownership while avoiding physical/module/process preemption.

## Responsibility Consequence

Every material R1/R2 semantic obligation has a named architecture responsibility. No generic “runtime manager” owns unrelated source or execution facts.

## Dependency Consequence

R1 is semantically independent of R2. R2 may consume R1 evidence through typed evidence linkage, not mutual semantic-definition dependency.

## Authority / SoT / Actual-state Consequence

```text
Authority Transfer → 0
SoT Transfer → 0
Actual-state Ownership Transfer → 0
Universal Runtime SoT → NOT CREATED
```

## RCP Consequence

P05 is the RCP-03 RT-R01 producer/coordinator responsibility; D05/D06 are the RCP-05 RT-R02 producer/coordinator responsibilities; D01 and D03 host RCP-02/RCP-04 consumer refinements respectively.

## Failure / Offline Consequence

Unknown/stale/disconnected/unroutable/indeterminate states remain boundary-local and explicit; no generic runtime failure state is created.

## Explicit Non-implications

No package/service/process/worker count, API, DB, queue, scheduler or deployment topology is implied.

## Deferred Implementation Mechanics

Physical code/module layout, process topology, storage and transport.

## Revalidation Trigger

Any proposal to merge R1/R2 into one final universal state/authority, or to move either boundary's accepted ownership.

---

# CID-RT-B1-DAD-002 — Presence is multi-dimensional evidence, not a transport boolean

## Decision / Issue

Should R1 treat one transport signal as canonical participant presence?

## Context

Accepted architecture permanently requires `Connected != Trusted != Admitted` and `Reachable != Ready`. Offline/degraded semantics require explicit stale/unknown/indeterminate conditions.

## Alternatives Considered

- **A — Boolean online/offline:** simple but collapses stale, unknown, disconnected and reachability semantics.
- **B — Transport session state as canonical presence:** easy to implement but promotes transport placement into Product truth.
- **C — Evidence-qualified connection/currentness/reachability dimensions:** representation-neutral and ownership-correct.

## Selected Design-semantic Result

**C selected.** R1 preserves separate connection qualification, currentness/freshness qualification and reachability qualification.

```text
Connection → CONNECTED / DISCONNECTED / UNKNOWN
Currentness → CURRENT / STALE / UNKNOWN / INDETERMINATE
Reachability → REACHABLE / UNREACHABLE / UNKNOWN
```

The terms establish distinctions, not a mandatory enum/schema.

## Rationale

A participant may be reachable but not ready, locally ready but centrally stale, or disconnected without being revoked/untrusted. A single boolean cannot preserve accepted semantics.

## Responsibility Consequence

P02 forms observations; P03 qualifies currentness; P04 qualifies reachability. No one transport observation acquires Trust/Admission/Readiness meaning.

## Dependency Consequence

P03/P04 depend on P01/P02 semantics; temporal/freshness uses accepted Foundation C04, uncertainty uses C10.

## Authority / SoT / Actual-state Consequence

R1 owns only its bounded coordination assertion; participant-local state and governance authorities remain external.

## RCP Consequence

RCP-03 must expose sufficient semantic distinction for consumers not to infer Trust/Admission/Readiness from presence.

## Failure / Offline Consequence

`STALE != FALSE`, `UNKNOWN != DISCONNECTED`, `UNREACHABLE != NOT_READY`, and connection loss does not erase source facts.

## Explicit Non-implications

No heartbeat, TTL, timeout, ping, handshake, WebSocket frame or session table is chosen.

## Deferred Implementation Mechanics

Observation mechanism, timers, connection/session realization and physical evidence representation.

## Revalidation Trigger

Any proposal that makes transport connectivity Trust/Admission/Readiness authority or removes explicit uncertainty semantics.

---

# CID-RT-B1-DAD-003 — R1 owns coordination presence/reachability only

## Decision / Issue

What is the exact R1 final Actual-state partition?

## Context

Project Architecture and Runtime Responsibility Architecture require exactly one final owner for the same bounded runtime assertion while forbidding a universal runtime SoT.

## Alternatives Considered

- **A — R1 becomes canonical participant status store:** violates local/source ownership.
- **B — R1 owns nothing and is only transport plumbing:** leaves accepted R1 Actual-state owner undefined.
- **C — R1 owns only runtime-originated connection/presence/currentness/reachability coordination facts.**

## Selected Design-semantic Result

**C selected.**

R1 final ownership:

```text
runtime-observed connection relationship state
Presence Observation evidence
presence currentness/freshness qualification
reachability coordination qualification
R1 evidence history/provenance/uncertainty
```

Explicit non-ownership includes Trust, Admission, Node readiness, Node Attempt/Effect, Agent/Automation facts and participant business state.

## Rationale

This exactly realizes accepted Z3/RRA ownership without making ns_runtime merely passive or universally authoritative.

## Responsibility Consequence

P02-P05 are allowed to persist/emit their own bounded facts; consumers cannot promote those facts into source truth.

## Dependency Consequence

R1 can consume governed context and participant evidence without becoming their authority.

## Authority / SoT / Actual-state Consequence

```text
Duplicate Final Owner → 0
Universal Participant Truth Store → NOT CREATED
```

## RCP Consequence

RCP-03 producer evidence is explicitly R1 coordination evidence, not participant-local state evidence.

## Failure / Offline Consequence

Central absence/unknown never proves participant local nonexistence or non-readiness.

## Explicit Non-implications

Persistence placement, cache, database or telemetry aggregation does not define R1 ownership.

## Deferred Implementation Mechanics

Storage/history realization and observation plumbing.

## Revalidation Trigger

Any proposal to make R1 final owner of Node readiness, Trust, Admission or participant-local execution state.

---

# CID-RT-B1-DAD-004 — RCP-02 is consumed, never re-admitted by R2

## Decision / Issue

What may R2 do with Formal Execution Admission Evidence?

## Context

RCP-02 producer semantics are already globally accepted under S8/SV-R04. R2 must coordinate only already-admitted work and may refine consumer applicability but cannot reopen server Admission Authority.

## Alternatives Considered

- **A — R2 re-evaluates admission locally:** violates S8 authority.
- **B — R2 blindly accepts any evidence reference:** unsafe and ignores expiry/revocation/stale/unknown applicability.
- **C — R2 validates/correlates consumer applicability under producer-defined semantics only.**

## Selected Design-semantic Result

**C selected.** D01 correlates the exact Admission Evidence to the work/execution intent and honors producer-defined applicability, temporal, revocation, replay/reuse, offline, provenance and compatibility semantics.

## Rationale

Consumers must verify they are using applicable evidence without turning verification into a new Admission decision.

## Responsibility Consequence

D01 may own an R2-local consumer applicability assessment, but never an Admission decision/evidence revision.

## Dependency Consequence

S8/RCP-02 is an external evidence/application-context dependency. No reverse semantic-definition edge exists.

## Authority / SoT / Actual-state Consequence

```text
Formal Admission Authority → S8 / unchanged
R2 Admission Authority → NONE
```

## RCP Consequence

`RCP-02 runtime consumer-side refinement → CLOSED AT CURRENT CANDIDATE DESIGN LEVEL`; server producer closure is preserved, not re-claimed.

## Failure / Offline Consequence

If applicability cannot be established, R2 preserves stale/unknown/unverified/indeterminate and withholds dispatch requiring established applicability. It does not fabricate admission or denial.

## Explicit Non-implications

Possession of evidence is not unlimited authority; successful dispatch does not retroactively prove Admission.

## Deferred Implementation Mechanics

Evidence representation, cryptographic verification mechanics if later required, cache/storage and protocol.

## Revalidation Trigger

Any proposal for runtime-minted/renewed Admission, retroactive admission or new fail-open/fail-closed Admission policy.

---

# CID-RT-B1-DAD-005 — Routing consumes presence and readiness as separate evidence dimensions

## Decision / Issue

How should R2 combine R1 reachability with future Node readiness/capability evidence?

## Context

Accepted architecture requires `Reachable != Ready`; RCP-04 owner-side semantics belong to `ns_node`/ND-R01 and are not authorized in this Batch.

## Alternatives Considered

- **A — Treat reachability as readiness:** collapses R1 and N1 ownership.
- **B — Treat readiness as proof of reachability:** also incorrect under disconnection/staleness.
- **C — Consume R1 presence/reachability and RCP-04 readiness/capability as independent evidence dimensions.**

## Selected Design-semantic Result

**C selected.** D03 qualifies routing candidates from declared work requirements plus independent presence/reachability, readiness/capability, compatibility and Admission-applicability evidence.

## Rationale

A target can be reachable but incapable/not-ready, or locally ready while runtime reachability is stale/unknown. Correct routing must preserve both dimensions.

## Responsibility Consequence

D03 owns only route-candidate qualification. It does not own R1 evidence or Node readiness.

## Dependency Consequence

R1 → R2 is typed `EL`; future ND-R01/RCP-04 → R2 is `XED`. There is no R2 → R1/ND-R01 authority edge.

## Authority / SoT / Actual-state Consequence

```text
R1 Reachability owner → R1
Node Readiness owner → ND-R01 downstream
Route Candidate qualification → R2
```

## RCP Consequence

RCP-04 runtime consumer expectation is closed only to the properties R2 needs; owner-side/full closure remains downstream.

## Failure / Offline Consequence

Stale/unknown readiness or reachability remains explicit; R2 does not infer `NOT_READY`, `DENIED` or `FAILED` from missing evidence.

## Explicit Non-implications

`Route Candidate != Ready Executor`; no Node readiness algorithm, inventory model or capability realization is designed.

## Deferred Implementation Mechanics

Readiness representation and Node internals; route-selection algorithm.

## Revalidation Trigger

Any proposal to transfer readiness ownership to runtime or to make presence/readiness one semantic state.

---

# CID-RT-B1-DAD-006 — Scheduling is bounded coordination, not a global priority/fairness law

## Decision / Issue

What scheduling semantics can R2 own without triggering Owner/MDE decisions for universal priority/fairness?

## Context

GAC explicitly marks universal scheduling semantics, global priority/fairness laws and cross-Tenant coordination semantics as MDE stop boundaries.

## Alternatives Considered

- **A — Define one global priority/fairness/tie-break model now:** out of scope and high migration cost.
- **B — Leave scheduling meaning entirely to implementation:** creates an implementation-defined semantic escape.
- **C — Define bounded scheduling coordination semantics while treating candidate-selection algorithms as replaceable realization absent a product-level guarantee.**

## Selected Design-semantic Result

**C selected.** D04 applies only constraints already supplied by authoritative work semantics, applicable configuration and current coordination evidence. It records the actual scheduling decision/provenance but creates no universal business priority, fairness or cross-Tenant law.

If semantically equivalent choices remain, later realization may choose among them only as a non-normative mechanism so long as no new durable product guarantee is exposed. A proposal to make such behavior a stable global guarantee requires MDE/revalidation.

## Rationale

This closes what scheduling coordination means while deliberately not making an unauthorized strategic scheduler policy decision.

## Responsibility Consequence

D04 owns bounded schedule coordination decisions, not source priority semantics or retry/cancellation policy.

## Dependency Consequence

D04 depends semantically on D02/D03 and consumes applicable configuration/context as ACD/XED.

## Authority / SoT / Actual-state Consequence

```text
Scheduling Coordination Actual-state → R2
Business/Automation/Agent priority semantics → source owner
Universal Scheduler Semantic Authority → NOT CREATED
```

## RCP Consequence

RCP-05 may reference the actual schedule decision/context but does not promise fairness/determinism.

## Failure / Offline Consequence

Insufficient evidence may yield pending/unknown/indeterminate scheduling state rather than an invented global rule.

## Explicit Non-implications

No weighted/fair queue, numeric priority scheme, deadline algorithm, deterministic tie-break guarantee or starvation guarantee is accepted.

## Deferred Implementation Mechanics

Scheduling algorithms and runtime data structures under later realization/conformance.

## Revalidation Trigger

Any externally durable priority/fairness/order guarantee, cross-Tenant scheduling semantics or universal scheduler authority.

---

# CID-RT-B1-DAD-007 — Dispatch has its own scoped identity and remains distinct from Attempt/Effect

## Decision / Issue

Is a distinct Dispatch semantic identity required, and what does Dispatch success mean?

## Context

Accepted architecture permanently requires `Operation != Dispatch != Attempt != Effect`, while RCP-05 requires operation/dispatch correlation and `dispatch != started`.

## Alternatives Considered

- **A — Reuse Operation identity as Dispatch identity:** cannot represent multiple dispatches for one Operation.
- **B — Reuse future Attempt identity:** transfers executor identity/ownership into runtime and assumes an Attempt exists.
- **C — Define a scoped representation-neutral Dispatch Identity / Reference owned by R2.**

## Selected Design-semantic Result

**C selected.** Each bounded dispatch decision/handoff that must be historically distinguishable has its own Dispatch identity/reference correlated to the Operation and later, if available, to executor-produced Attempt evidence.

A bounded Dispatch success proves only completion of R2's applicable coordination handoff. It never proves Attempt creation/start, effect or semantic success.

## Rationale

Identity separation is necessary for history, retries/re-dispatch and correct cross-component evidence correlation.

## Responsibility Consequence

D05 owns Dispatch decision/identity/handoff evidence; D06 owns lineage/history and passive later-attempt correlation.

## Dependency Consequence

Dispatch retains references to D01-D04 evidence; future Attempt is EL/HPL only.

## Authority / SoT / Actual-state Consequence

```text
Dispatch Actual-state → R2
Attempt Actual-state → executor owner
Effect/source fact → effect/source owner
Major universal identity namespace → NOT CREATED
```

## RCP Consequence

RCP-05 RT-R02 producer-side stable subject is closed around Dispatch identity/evidence and Operation/Attempt non-collapse.

## Failure / Offline Consequence

Missing delivery/Attempt evidence remains unknown/indeterminate; it does not rewrite Dispatch history into success/failure claims outside R2.

## Explicit Non-implications

No queue-message ID, broker receipt, socket acknowledgement, HTTP response or database key defines Dispatch identity.

## Deferred Implementation Mechanics

ID format, handoff protocol, acknowledgement mechanics and persistence.

## Revalidation Trigger

Any proposal to merge Dispatch with Operation/Attempt/Effect or expose a major permanent cross-product Dispatch identity namespace.

---

# CID-RT-B1-DAD-008 — Re-dispatch creates new dispatch history; no retry/delivery guarantee is invented

## Decision / Issue

How should R2 preserve repeated dispatch activity without defining universal retry semantics?

## Context

Accepted architecture requires history preservation and explicitly reserves global retry policy and delivery guarantees to MDE if made durable commitments.

## Alternatives Considered

- **A — Mutate one Dispatch record until success:** destroys history and conflates attempts at coordination.
- **B — Define universal automatic retry/backoff/delivery guarantee:** out of scope/MDE.
- **C — Every materially new dispatch gets a new Dispatch identity and lineage; the decision to retry/re-dispatch remains outside universal R2 policy.**

## Selected Design-semantic Result

**C selected.** Prior Dispatch evidence is immutable in semantic history. A later legally supplied coordination intent may create a new Dispatch identity with lineage to prior related dispatches.

## Rationale

This preserves causality and supports future recovery/diagnostics without choosing retry policy or delivery guarantee.

## Responsibility Consequence

D06 preserves lineage/history; it does not decide universal retry applicability.

## Dependency Consequence

D06 depends on D05 and receives later source evidence only through EL/HPL.

## Authority / SoT / Actual-state Consequence

No executor Attempt ownership or universal operation ownership transfers to R2.

## RCP Consequence

RCP-05 includes retry/re-dispatch lineage where applicable but no exactly-once/at-most-once/at-least-once promise.

## Failure / Offline Consequence

Reconnect/retry does not erase prior dispatch evidence or retroactively authorize prior/new work.

## Explicit Non-implications

No retry count, cadence, backoff, dead-letter, dedup winner or final-latest dispatch policy.

## Deferred Implementation Mechanics

Retry triggers/policy only if later explicitly authorized; physical history persistence.

## Revalidation Trigger

Any universal retry or delivery guarantee, latest-dispatch-wins rule or silent history overwrite.

---

# CID-RT-B1-DAD-009 — R1→R2 is one-way typed evidence dependency and hard SDD remains acyclic

## Decision / Issue

What internal dependency semantics prevent R1/R2 from becoming circular or physically coupled?

## Context

Current Component Internal Design convention distinguishes SDD, ACD, EL, HPL and XED. Only SDD participates in semantic-definition cycle analysis.

## Alternatives Considered

- **A — Untyped “depends on” graph:** ambiguous about authority, runtime calls and semantic definition.
- **B — Make R1 and R2 mutually hard-dependent:** creates unnecessary semantic coupling.
- **C — Reuse typed dependency taxonomy; keep R1 semantic definition independent and use one-way R1 evidence linkage into R2.**

## Selected Design-semantic Result

**C selected.** Hard SDD:

```text
P02 → P01
P03 → P01, P02
P04 → P01, P02
P05 → P01, P03, P04
D03 → D02
D04 → D02, D03
D05 → D01, D02, D03, D04
D06 → D05
```

Cross-boundary:

```text
P03/P04/P05 → EL → D03/D05
S8/RCP-02 → XED/ACD → D01/D05
ND-R01/RCP-04 → XED → D03/D05
later Attempt → EL/HPL → D06
```

## Rationale

Typed dependencies preserve semantic ownership and allow later physical realization to vary without turning runtime call graphs into architecture authority.

## Responsibility Consequence

No R2 feedback is required to define R1 presence/reachability; R2 can become pending when R1 evidence is unavailable.

## Dependency Consequence

```text
Hard SDD Graph → ACYCLIC
Unresolved Cycle → 0
Authority Cycle → NONE
```

## Authority / SoT / Actual-state Consequence

Evidence consumption does not transfer source ownership.

## RCP Consequence

RCP-03 and RCP-04 inputs remain distinct external/internal evidence relationships feeding RCP-05 production.

## Failure / Offline Consequence

Missing an evidence producer can yield bounded unknown/pending states rather than structural architecture failure.

## Explicit Non-implications

No service call direction, synchronous dependency, process placement or network topology is implied.

## Deferred Implementation Mechanics

Physical call/event/storage dependencies.

## Revalidation Trigger

Any hard circular semantic dependency or placement-based authority implication.

---

# CID-RT-B1-DAD-010 — Offline/private coordination preserves Admission authority and explicit uncertainty

## Decision / Issue

How should R1/R2 behave under disconnection/private deployment without creating local authority escalation?

## Context

NSE-004 and accepted Project Architecture require private/offline core correctness. RCP-02 allows bounded retained evidence under producer-defined applicability but not local reauthorization.

## Alternatives Considered

- **A — Require synchronous central/public service for every presence/dispatch action:** violates private/offline baseline.
- **B — Fail open and let runtime self-authorize while disconnected:** violates Admission Authority.
- **C — Preserve bounded local coordination evidence and applicable retained Admission evidence, with explicit uncertainty when applicability cannot be established.**

## Selected Design-semantic Result

**C selected.** R1 may preserve its own local coordination history; R2 may consume legitimately applicable retained Admission evidence according to S8 semantics, never extend it. Missing/uncertain evidence yields pending/unroutable/unknown/indeterminate as applicable.

## Rationale

This preserves both offline operability and governance invariance.

## Responsibility Consequence

R1 owns only local coordination facts; D01 remains strict consumer; D03-D05 do not bypass missing governance/readiness evidence.

## Dependency Consequence

No mandatory public SaaS/control-plane dependency is created.

## Authority / SoT / Actual-state Consequence

```text
Offline Authority Transfer → 0
Runtime Admission Authority → NONE
```

## RCP Consequence

RCP-02/RCP-03/RCP-05 include offline qualification and explicit uncertainty; RCP-04 consumer expectation preserves stale/unknown readiness.

## Failure / Offline Consequence

```text
Disconnected != Revoked
Unknown != Denied
Reconnect != Reconciled
Replay != Retroactive Authorization
```

## Explicit Non-implications

No material global fail-open/fail-closed rule is introduced.

## Deferred Implementation Mechanics

Local retention, transport reconnection, caches, persistence and verification mechanisms.

## Revalidation Trigger

Mandatory public dependency, local admission minting or material fail-open/fail-closed guarantee.

---

# CID-RT-B1-DAD-011 — R1/R2 reuse accepted Shared Foundation without creating new Foundation semantics

## Decision / Issue

Which reusable semantics are consumed by R1/R2, and does current design require Foundation revalidation?

## Context

Shared Foundation Architecture, Contract, Module and Provider design are globally closed. A mandatory missing cross-component reusable semantic would require STOP and GAC Foundation revalidation.

## Alternatives Considered

- **A — Recreate time/correlation/status/context primitives inside ns_runtime:** duplicates Foundation and risks semantic forks.
- **B — Treat Foundation as Product Authority:** violates authority neutrality.
- **C — Consume accepted Foundation stable semantics only where applicable, retaining R1/R2 ownership.**

## Selected Design-semantic Result

**C selected.** Applicable reuse includes C01, C02, C03, C04, C05, C06, C07, C10, C11, C12, C13 and C14 as described in the Candidate.

## Rationale

The accepted Foundation already covers temporal/freshness, correlation/provenance, representation, uncertainty, governed context, diagnostics and security-neutral reusable mechanics required by R1/R2.

## Responsibility Consequence

R1/R2 define product-specific presence/dispatch semantics; Foundation supplies reusable mechanical semantics only.

## Dependency Consequence

Foundation Stable Entry/Contract/Module consumption is not a Product authority edge.

## Authority / SoT / Actual-state Consequence

```text
Foundation Authority Transfer → 0
Missing Mandatory Foundation Semantic → NONE
New Foundation Capability → 0
```

## RCP Consequence

RCP-03/RCP-05 can reuse Foundation correlation/time/status/representation semantics without becoming Foundation contracts.

## Failure / Offline Consequence

Foundation common uncertainty and offline/private obligations remain controlling.

## Explicit Non-implications

Deferred Crypto/Evidence-verification and Database Utility candidates remain deferred; no provider/vendor/library is selected.

## Deferred Implementation Mechanics

Concrete Foundation module/provider bindings and code imports.

## Revalidation Trigger

Discovery of a truly mandatory reusable cross-component semantic absent from accepted Foundation, or proposal to make Foundation a Product authority.

---

# CID-RT-B1-DAD-012 — R1/R2 preserve future R3/R4 compatibility without designing them

## Decision / Issue

What minimum R1/R2 semantics must be stable now so later continuation/recovery design is not locked out, without preempting R3/R4?

## Context

R3 and R4 are accepted boundaries but explicitly not authorized in Batch 1. R1/R2 must not create destructive state/history assumptions that make later coordination continuation/reconciliation impossible.

## Alternatives Considered

- **A — Design R3/R4 now:** unauthorized progression.
- **B — Ignore future compatibility and allow destructive overwrite:** creates avoidable downstream semantic gap.
- **C — Preserve correlation/provenance/history/uncertainty extension points while making no R3/R4 lifecycle/algorithm decisions.**

## Selected Design-semantic Result

**C selected.** R1/R2 preserve Operation, Participant, Admission, Dispatch and later Attempt references; evidence history is non-destructive; stale/unknown/indeterminate is explicit; reconnect is not reconciliation; new dispatch does not overwrite prior dispatch.

## Rationale

These are obligations intrinsic to correct R1/R2 history and correlation, not unauthorized R3/R4 design.

## Responsibility Consequence

P05 and D06 provide traceable inputs a future R3/R4 design may consume. They do not own continuation/recovery outcomes.

## Dependency Consequence

No R1/R2 semantic definition depends on future R3/R4. Future roles may consume existing evidence through later authorized contracts.

## Authority / SoT / Actual-state Consequence

Source owners remain source owners through reconnect/recovery. No conflict-winner authority is created.

## RCP Consequence

```text
RCP-06 → NOT DESIGNED
RCP-20 → NOT DESIGNED
correlation compatibility → PRESERVED ONLY
```

## Failure / Offline Consequence

```text
Reconnect != Reconciled
Recovery != SoT Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
```

## Explicit Non-implications

No reconciliation algorithm, replay policy, recovery state machine, conflict winner, intervention lifecycle, retry/cancel/resume semantics or rollback mechanism.

## Deferred Implementation Mechanics

All R3/R4 Component Internal Design and later realization.

## Revalidation Trigger

Any requirement to decide R3/R4 owner-side semantics in order to make R1/R2 correct; such a finding would require returning to GAC rather than expanding this Batch.

---

# DAD Set Summary

```text
CID-RT-B1-DAD-001
→ R1/R2 internal decomposition and non-collapse

CID-RT-B1-DAD-002
→ multi-dimensional Presence / Reachability evidence semantics

CID-RT-B1-DAD-003
→ bounded R1 Actual-state ownership

CID-RT-B1-DAD-004
→ RCP-02 consumer-only Admission applicability

CID-RT-B1-DAD-005
→ Presence/Reachability vs Readiness evidence separation

CID-RT-B1-DAD-006
→ bounded Scheduling without global priority/fairness law

CID-RT-B1-DAD-007
→ Dispatch identity / Attempt / Effect non-collapse

CID-RT-B1-DAD-008
→ re-dispatch history without retry/delivery guarantee

CID-RT-B1-DAD-009
→ typed dependency topology / acyclic SDD

CID-RT-B1-DAD-010
→ offline/private governance invariance

CID-RT-B1-DAD-011
→ accepted Shared Foundation consumption

CID-RT-B1-DAD-012
→ future R3/R4 compatibility without unauthorized design
```

## MDE Audit

```text
New Product Capability → 0
Authority / SoT / final Actual-state topology change → 0
Universal scheduling semantics → NOT CREATED
Global priority / fairness law → NOT CREATED
Global retry / cancellation / rollback policy → NOT CREATED
Exactly-once / at-most-once / at-least-once universal guarantee → NOT CREATED
Global conflict-winner / latest-wins law → NOT CREATED
Universal routing / operation ownership → NOT CREATED
Cross-Tenant coordination semantics → NOT CREATED
Major new identity namespace → NOT CREATED
Mandatory broker / queue / scheduler technology → NOT CREATED
Mandatory public service dependency → NOT CREATED
Provider / protocol / framework / storage lock-in → NOT CREATED
Material fail-open/fail-closed policy → NOT CREATED

Misclassified MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

MDE Escalation Required
→ NO
```

Maximum legal producing state remains:

```text
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```
