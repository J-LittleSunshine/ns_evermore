# NGRP-001 — Component Internal Design / ns_runtime / Batch 1 Candidate

## Authority Metadata

- **Program / Phase:** `NGRP-001 — Component Internal Design / ns_runtime / Batch 1`
- **Authorization Scope:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_RUNTIME / BATCH_1 / PRESENCE_AND_GOVERNED_DISPATCH_COORDINATION_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Producing Entry HEAD:** `a4f538f803abd8d3f6135908f80529ccd40b42b7`
- **Recovered Global State:** `GAC-EPOCH-0070`
- **State Verified Through HEAD:** `7412b644a07ec55350ddde3616a930db99027432`
- **Decision Registry:** `0.0.25 / CURRENT / NORMATIVE`
- **Authorization Transition:** `GAC-TR-0080`
- **Authorized Boundaries:** `R1 / R2`
- **Inherited Runtime Roles:** `RT-R01 / RT-R02`
- **Candidate Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Global Acceptance Authority:** `NOT HELD`
- **Next Batch / Component Authorization:** `NONE`

This Candidate performs only architecture-semantic internal design for `ns_runtime` boundaries R1 and R2. It does not design R3/R4, any other Product Component, System-level SDK Detailed Design, process/service/worker/deployment topology, implementation planning, IWP or code.

---

# 1. Fresh Repository Recovery

## 1.1 Recovery result

```text
Actual remote Branch HEAD at producing entry
→ a4f538f803abd8d3f6135908f80529ccd40b42b7

Current GAC Epoch
→ GAC-EPOCH-0070

State Verified Through HEAD
→ 7412b644a07ec55350ddde3616a930db99027432

State-to-HEAD Delta
→ exactly 1 commit
→ only docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md changed
→ authorization seal for ns_runtime Component Internal Design / Batch 1

Delta Classification
→ EXPECTED_GOVERNANCE

Decision Registry
→ 0.0.25 / CURRENT / NORMATIVE

Current Authorized Phase
→ NGRP-001 — Component Internal Design / ns_runtime / Batch 1

Authorization Scope
→ COMPONENT_INTERNAL_DESIGN_ONLY
  / NS_RUNTIME
  / BATCH_1
  / PRESENCE_AND_GOVERNED_DISPATCH_COORDINATION_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Item
→ NONE

Known Drift
→ NONE

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE

Recovery Result
→ PASS
```

The recovered Ledger tail establishes:

```text
GAC-TR-0078
→ ns_server Component Internal Design GLOBAL_CLOSED / COMPLETE
→ ns_server Internal Design Exhaustion SATISFIED

GAC-TR-0079
→ ns_runtime selected as next Product Component
→ ns_runtime Entry Readiness SATISFIED
→ R1 + R2 proposed as Batch 1

GAC-TR-0080
→ explicit ns_runtime Batch 1 authorization
→ exact R1/R2 and RCP scope below
```

The Decision Registry `0.0.25` predates the later sequencing/authorization transitions and therefore retains a historical `Current Authorized Phase → NONE` statement inside that registry revision. Current Global State, Working State and Ledger establish the later lawful authorization; this is not a Registry/State contradiction and does not alter the Registry's accepted architectural decision content.

## 1.2 Required-read recovery

The current Global State Required Read Set was consumed, including Constitution, Unified Governance, current Global State and Working State, Decision Registry `0.0.25`, NSE index, Project Architecture `0.0.3`, accepted Five-component Internal Architecture Boundary evidence, accepted Runtime Responsibility Architecture, Foundation Provider Exhaustion / Component Internal Design readiness, all `ns_server` Batch 1..8 Global Acceptance evidence, post-`ns_server` sequencing / `ns_runtime` entry-readiness evidence, and the Ledger through `GAC-TR-0080`.

Applicable accepted Shared Foundation Contract/Module evidence was additionally consumed for:

```text
Bootstrap Configuration Acquisition
Diagnostic Occurrence & Delivery Evidence
Technical Observation & Health Evidence
Temporal & Freshness
Operation Correlation & Provenance Context
Semantic Representation & Serialization
Network Invocation Mechanics
Technical Status & Uncertainty
Governed Context Propagation
Secret Reference
Sensitive-data Redaction
Compatibility & Conformance
```

No missing mandatory Shared Foundation semantic was found.

---

# 2. Accepted Upstream Baseline Preserved

```text
Architecture Constraint Derivation
→ GLOBAL_CLOSED / COMPLETE

Project Architecture
→ 0.0.3 / GLOBAL_ACCEPTED / CURRENT

Five-component Capability Exhaustion
→ SATISFIED

Five-component Internal-boundary Exhaustion
→ SATISFIED

Accepted Internal Boundaries
→ 34

Runtime Responsibility Architecture
→ GLOBAL_CLOSED / COMPLETE

Accepted Runtime Roles
→ 22

Shared Foundation Architecture / Contract / Module / Provider
→ GLOBAL_CLOSED / COMPLETE

Component Internal Design Readiness
→ SATISFIED

ns_server Component Internal Design
→ GLOBAL_CLOSED / COMPLETE

ns_server Internal Design Exhaustion
→ SATISFIED

ns_server accepted boundary coverage
→ 13 / 13 / 100%
```

The following accepted authority topology is inherited without reopening:

```text
Formal Artifact Acceptance Authority
→ ns_server / S8

Formal Execution Admission Authority
→ ns_server / S8 / SV-R04

Platform Security / Trust Semantic Authority
→ ns_server

Managed Runtime Configuration Desired-state Authority / SoT
→ ns_server / S9

Runtime Actual-state
→ exactly one final owner per same bounded assertion

Node capability/readiness Actual-state
→ ns_node / N1 / ND-R01 downstream

Node execution Attempt Actual-state
→ ns_node / N2 / ND-R02 downstream

Node protected local Effect / source fact
→ ns_node / N3 / ND-R03 downstream

Agent semantic/runtime facts
→ applicable ns_agent owners

Automation semantic continuation
→ ns_server / S6 / SV-R02

server-local background runtime facts
→ ns_server / S10 / SV-R06
```

Permanent non-collapse for this Candidate:

```text
Authority != Coordination
Coordination != Execution Authority
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Dispatch != Attempt
Dispatch Success != Execution Started
Execution Started != Protected Effect
Connected != Trusted != Admitted
Reachable != Ready
Route Candidate != Ready Executor
Reconnect != Reconciled
Recovery != SoT Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
```

---

# 3. Authorized Boundary and RCP Scope

## 3.1 Authorized Internal Boundaries

```text
R1
→ Connection / Participant Presence Coordination
→ RT-R01 Participant Presence Coordinator

R2
→ Governed Routing / Scheduling / Dispatch Coordination
→ RT-R02 Governed Routing / Scheduling / Dispatch Coordinator
```

Not authorized:

```text
R3 / RT-R03
→ Operation Continuation / Delegation / Intervention Coordination

R4 / RT-R04
→ Coordination Recovery / Reconciliation / Diagnostics
```

R3/R4 appear only as future compatibility constraints. No internal decomposition, lifecycle design or stable-contract owner-side closure for R3/R4 is performed.

## 3.2 Authorized Stable-contract Pressure

```text
RCP-03 Presence
→ RT-R01 owner/coordinator-side semantic closure
→ stable contract synthesis
→ Full Cross-component Closure NOT CLAIMED

RCP-05 Dispatch Evidence
→ RT-R02 producer/coordinator-side semantic closure
→ stable contract synthesis
→ Full Cross-component Closure NOT CLAIMED

RCP-02 Admission Evidence
→ runtime consumer-side applicability/refinement only
→ accepted ns_server producer semantics preserved

RCP-04 Node Readiness
→ runtime consumer expectation/refinement only
→ ND-R01 owner-side semantics remain downstream
→ Full RCP-04 Closure NOT CLAIMED
```

No additional RCP full closure is claimed by this Candidate.

---

# 4. Internal Architecture Overview

The internal decomposition is architecture-semantic only. Labels below are document-local navigation labels and are not packages, classes, services, processes, workers, database objects, queues, endpoints or deployment units.

## 4.1 R1 internal responsibilities

```text
P01 Participant Reference & Coordination-context Binding
P02 Connection Observation & Presence-evidence Intake
P03 Presence Currentness & Freshness Qualification
P04 Reachability Qualification & Uncertainty Custody
P05 Presence History, Projection & RCP-03 Contract Governance
```

## 4.2 R2 internal responsibilities

```text
D01 Admitted-work Intake & Admission-evidence Applicability
D02 Work Requirement & Target Correlation
D03 Routing Candidate Qualification
D04 Scheduling Coordination & Bounded Ordering
D05 Dispatch Decision, Handoff & Evidence Custody
D06 Dispatch Lineage, History & Later-attempt Correlation
```

```text
Authorized Boundary Coverage
→ R1 / R2
→ 2 / 2 / 100%

Internal Responsibility Count
→ 11

Unowned Material R1/R2 Responsibility
→ 0

Duplicate Final Responsibility
→ 0

R1/R2 Collapse Into Universal Runtime Authority
→ NO
```

---

# 5. R1 — Presence Coordination Internal Architecture

## P01 — Participant Reference & Coordination-context Binding

**Purpose.** Establish the representation-neutral reference and applicable coordination context needed for R1 to reason about one runtime participant without inventing participant semantic authority.

P01 preserves distinct references where applicable to:

```text
Participant Identity / Reference
Participant Type / Role Context
Tenant Context
Organization Context where applicable
Principal / IAM Context reference
Policy Context reference
Trust Context reference
Correlation / provenance context
Applicable compatibility revision
```

The Participant Reference is a reference to identity owned by the applicable participant/identity authority. P01 does not create a universal runtime participant registry or a new cross-product identity namespace.

Permanent:

```text
Participant Reference != Connection Identity
Participant Reference != Presence Observation Identity
Participant Reference != Operation Identity
Participant Reference != Trust Decision
Participant Reference != Admission Decision
Participant Reference != Node Readiness
```

Identity physical format, UUID scheme, database key, hostname, process identity, socket identity, session identifier and wire encoding are deferred.

## P02 — Connection Observation & Presence-evidence Intake

**Purpose.** Establish R1-owned bounded observations produced by `ns_runtime` coordination activity about whether a participant connection relationship is currently evidenced, lost, absent from admissible observation, or otherwise uncertain.

P02 may form a scoped **Presence Observation Identity / Reference** where multiple observations/history must remain distinguishable. This identity is an R1 evidence subject only and is not a major universal product namespace.

P02 owns only runtime coordination observations such as:

```text
connection relationship evidenced
connection relationship known lost / disconnected
observation unavailable
observation unknown
observation indeterminate
```

A transport-level signal is evidence only. P02 must not elevate it to Trust, Admission, Readiness or canonical participant truth.

```text
Transport Signal != Presence Truth automatically
Connection Established != Trusted
Connection Established != Admitted
Connection Established != Ready
Connection Lost != Revoked
Connection Lost != Admission Revoked
```

No heartbeat, handshake, socket lifecycle, session store, WebSocket frame, timeout or connection database is designed.

## P03 — Presence Currentness & Freshness Qualification

**Purpose.** Qualify whether R1's own connection/presence evidence is sufficiently current to support a present coordination assertion, while preserving uncertainty.

Presence is modeled as evidence-qualified semantics rather than one universal boolean. At minimum the following dimensions remain distinguishable:

```text
Connection Qualification
→ CONNECTED / DISCONNECTED / UNKNOWN

Currentness / Freshness Qualification
→ CURRENT / STALE / UNKNOWN / INDETERMINATE

Evidence Availability
→ available / missing / unavailable / unverified where applicable
```

The words above identify semantic distinctions, not a mandatory enum/schema.

Permanent:

```text
STALE != FALSE
UNKNOWN != DISCONNECTED
MISSING != DISCONNECTED
UNAVAILABLE != REVOKED
Current connection evidence != permanent participant presence
```

Freshness judgement consumes the accepted Foundation Temporal & Freshness semantics. It does not select a TTL algorithm, timeout duration, clock source or expiry encoding.

P03 owns the qualification of **R1's coordination evidence currentness**, not freshness of Node readiness, source facts, Admission evidence or business state.

## P04 — Reachability Qualification & Uncertainty Custody

**Purpose.** Form the bounded runtime coordination assertion about whether a participant is currently reachable for applicable coordination, independently from Node capability/readiness.

Reachability remains an orthogonal R1 fact:

```text
Reachability Qualification
→ REACHABLE / UNREACHABLE / UNKNOWN

Reachability Currentness
→ CURRENT / STALE / UNKNOWN / INDETERMINATE
```

No particular transport probe, ping, frame exchange, path-selection algorithm or network topology is implied.

Permanent:

```text
REACHABLE != READY
REACHABLE != TRUSTED
REACHABLE != ADMITTED
UNREACHABLE != NOT_READY
UNREACHABLE != REVOKED
UNREACHABLE != FAILED EXECUTION
```

A participant may have locally established readiness while centrally observed reachability is stale/unknown. Conversely, a participant may be reachable while not ready for the requested capability. R1 never collapses those states.

## P05 — Presence History, Projection & RCP-03 Contract Governance

**Purpose.** Preserve R1-owned history/provenance and publish the stable semantic evidence required by RCP-03 without making projection/history a universal Participant SoT.

P05 preserves where applicable:

```text
Participant Reference
Presence Observation Reference
Connection qualification
Reachability qualification
Freshness/currentness qualification
observation / qualification temporal context
producer = RT-R01 / R1
provenance / correlation context
applicable Tenant / governed-context references
uncertainty reason/evidence
compatibility/conformance revision context
prior-related observation reference where history requires it
```

Historical R1 evidence is not silently rewritten by later reconnect, later connection loss or later reachability changes.

```text
Later Connection != Historical Connection State Rewrite
Reconnect != Reconciled
Projection of Presence != Participant-local SoT
```

P05 does not perform R4 recovery/reconciliation. It only preserves evidence sufficient for future R4 to operate without overwriting source authority.

---

# 6. R1 Bounded Actual-state Ownership

Final R1 / RT-R01 ownership is exactly limited to facts genuinely originating from runtime coordination activity:

```text
runtime-observed connection relationship state
runtime-owned Presence Observation evidence
runtime-owned presence currentness/freshness qualification
runtime-owned reachability coordination qualification
R1 evidence history / provenance / uncertainty
```

Explicit non-ownership:

```text
Participant business/domain identity Authority
Tenant / IAM / Policy / Trust Authority
Formal Artifact Acceptance
Formal Execution Admission
Node capability / readiness
Node local session/readiness fact
Node execution Attempt
Node protected local Effect
Agent runtime Actual-state
Automation semantic continuation
Source facts outside R1
```

```text
R1 Actual-state Owner
!= Universal Participant Truth Store
!= Universal Runtime SoT
```

---

# 7. RCP-03 — RT-R01 Presence Contribution

## 7.1 Stable semantic subject

RCP-03 is the representation-neutral cross-boundary semantic subject by which runtime participants and consumers correlate participant presence/connectivity/reachability evidence with R1-owned coordination facts.

RT-R01 producer/coordinator-side contribution requires stable meaning for:

```text
Participant Reference
Presence Observation Reference where materially required
R1 producer/owner identity
connection qualification
presence currentness/freshness qualification
reachability qualification
observation and applicability temporal context
provenance / correlation context
governed-context references where applicable
uncertainty / unavailable / stale / indeterminate qualification
compatibility/conformance context
historical lineage where applicable
```

## 7.2 Producer obligations

RT-R01 MUST:

- emit only facts that R1 is authorized to own;
- preserve participant/source provenance;
- distinguish current, stale, unknown and indeterminate evidence;
- keep connection and reachability qualifications separable;
- preserve historical evidence rather than silently overwrite it;
- keep Tenant/Principal/Policy/Trust context as references/consumed context rather than runtime authority;
- never infer Node readiness from reachability;
- never infer Trust or Admission from connection/presence;
- remain usable in private/offline deployments without public service dependence.

## 7.3 Consumer obligations

An RCP-03 consumer MUST NOT interpret R1 evidence as proof of:

```text
Trust
Formal Admission
Node Readiness
execution capability
execution started
protected effect
business/domain success
canonical participant local state
```

Stale or unknown R1 evidence must remain stale/unknown; consumers may not silently coerce it to connected/disconnected or ready/not-ready.

## 7.4 Closure boundary

```text
RCP-03 RT-R01 Owner/Coordinator-side Contribution
→ CLOSED AT CURRENT CANDIDATE DESIGN LEVEL

RCP-03 Full Cross-component Closure
→ NOT CLAIMED
→ NOT AUTHORIZED BY INFERENCE
```

Participant-side downstream Component Internal Design remains outside this Batch.

---

# 8. R2 — Governed Routing / Scheduling / Dispatch Internal Architecture

## D01 — Admitted-work Intake & Admission-evidence Applicability

**Purpose.** Consume already accepted Formal Execution Admission Evidence and determine whether that evidence can be relied on for this bounded coordination action without re-performing Admission.

D01 consumes the globally accepted RCP-02 producer semantics from S8/SV-R04. Required consumer-visible subjects include where applicable:

```text
Admission Evidence Identity / Reference
Target Execution Intent Identity / Reference
Artifact / Definition revision references
Tenant / Principal / Policy / Trust / Acceptance evidence linkage
Admission decision/revision/applicability
applicable temporal / optional expiry context
revocation / stale / unknown / indeterminate qualification
bounded replay/reuse qualification
offline applicability
provenance
compatibility / migration / conformance context
```

D01 may establish an R2-local **consumer applicability assessment** such as applicable, not-applicable, stale, unknown, unverified or indeterminate according to the accepted producer semantics. That assessment is an R2 coordination input only.

Permanent:

```text
Admission Evidence Validation/Applicability Check
!= Formal Execution Admission

Admission Evidence Possession
!= Admission Authority
!= unlimited execution authority

Policy Permit
!= Admission

Accepted Artifact
!= Admission
```

D01 cannot mint, renew, extend, override, reinterpret or retroactively authorize Admission Evidence.

If applicability cannot be established, R2 must preserve uncertainty and withhold a dispatch that requires established applicability; it must not fabricate either a new Admission or a new denial decision.

## D02 — Work Requirement & Target Correlation

**Purpose.** Preserve the admitted work's representation-neutral coordination requirements and correlate them to possible target participants/capabilities without acquiring source-domain semantic authority.

D02 preserves where applicable:

```text
Operation / Work Reference
Execution Intent Reference
Admission Evidence Reference
required capability / execution mode / target-class references supplied by owning semantics
applicable Tenant / Principal / Policy / Trust context references
source semantic owner / Definition revision references
correlation/provenance context
```

R2 does not define the business, Automation or Agent meaning of those requirements; it consumes them.

```text
Work Requirement Interpretation for Coordination
!= Business / Automation / Agent Semantic Authority

Operation Reference
!= Dispatch Identity
!= Attempt Identity
```

No universal job/task/workflow namespace is created.

## D03 — Routing Candidate Qualification

**Purpose.** Determine which candidate participants can currently be considered for R2 coordination based on explicit work requirements plus separate evidence dimensions.

D03 consumes at least the applicable combination of:

```text
R1 / RCP-03 presence and reachability evidence
RCP-04 Node capability/readiness evidence when a Node executor is applicable
other already-authorized capability evidence from the applicable target owner
work requirement / compatibility evidence
Admission applicability from D01
```

These inputs remain independent.

Permanent:

```text
Route Candidate != Ready Executor
Reachable != Ready
Ready != Admitted
Admitted != Reachable
Capability Declared != Capability Ready automatically
Presence Current != Capability Compatible automatically
```

R2 does not create Node Readiness. For RCP-04 it only consumes the downstream owner's evidence.

Candidate qualification may explicitly produce bounded coordination conditions such as:

```text
qualified candidate available
no candidate currently qualified by available evidence
required evidence pending
required evidence stale
required evidence unavailable
unroutable under declared requirements
unknown
indeterminate
```

Those are semantic distinctions, not a fixed wire enum or universal scheduler state machine.

If evidence is incomplete, D03 preserves `UNKNOWN` / `STALE` / `INDETERMINATE` rather than inferring `NOT_READY`, `DENIED` or `FAILED`.

## D04 — Scheduling Coordination & Bounded Ordering

**Purpose.** Apply already-governed scheduling constraints to qualified coordination candidates and produce bounded scheduling decisions without defining a universal scheduling semantic authority.

D04 may consume:

```text
operation-specific timing/deadline constraints
explicit priority/order constraints already owned by the source semantic authority where such constraints exist
managed runtime configuration applicable to R2
qualified candidate evidence
availability / uncertainty evidence
```

D04 does not invent a global priority law, fairness law, retry law or cross-Tenant ordering rule.

Permanent:

```text
Scheduling Coordination
!= Business Priority Authority
!= Automation Semantic Authority
!= Agent Semantic Authority
!= Formal Admission Authority
!= Universal Fairness Authority
```

Where multiple candidates or ordering choices are semantically equivalent under accepted constraints, later realization may use a replaceable selection mechanism provided that it does not surface a new durable product guarantee and preserves the actual selected decision/provenance. Algorithm choice alone is not Contract semantics.

Where a product-semantic decision would require a new global priority/fairness/tie-breaking law, this design does not guess: that would cross the MDE stop boundary.

No queue discipline, weighted policy, fairness formula, priority number system, deadline algorithm or scheduler framework is selected.

## D05 — Dispatch Decision, Handoff & Evidence Custody

**Purpose.** Establish the runtime-owned Dispatch Decision and RCP-05 evidence for one bounded coordination handoff after applicable Admission, route qualification and scheduling coordination.

A **Dispatch Identity / Reference** is required as a scoped R2 semantic identity so that one Operation can have multiple distinct dispatch decisions/hand-offs without collapsing them into the later executor Attempt. It does not create a universal cross-product identity namespace.

D05 preserves where applicable:

```text
Operation / Work Reference
Dispatch Identity / Reference
Admission Evidence Reference
selected target Participant / executor reference
route candidate / route decision context
schedule decision context
R1 Presence / Reachability evidence references
RCP-04 capability/readiness evidence references where applicable
source semantic owner / Definition revision context
Dispatch decision temporal context
Dispatch handoff / delivery-coordination evidence where available
provenance / governed context
uncertainty / unavailable / unroutable / pending qualification
compatibility/conformance context
```

Permanent:

```text
Operation != Dispatch
Dispatch != Attempt
Dispatch Evidence != Attempt Evidence
Dispatch Decision != Effect
Dispatch Handoff Evidenced != Executor Attempt Started
Dispatch Success != Execution Started
Execution Started != Protected Effect
```

A bounded dispatch success may prove only that R2 completed the applicable coordination handoff under R2 semantics. It does not prove executor receipt, acceptance, Attempt creation, Attempt start, effect or business success unless later source-owned evidence explicitly establishes those distinct facts.

No message envelope, endpoint, acknowledgement frame, broker receipt, transport acknowledgement or concrete dispatch protocol is selected.

## D06 — Dispatch Lineage, History & Later-attempt Correlation

**Purpose.** Preserve dispatch history and correlation so retries/re-dispatch/reconnect cannot overwrite prior coordination facts and later executor evidence can be linked without R2 becoming executor Actual-state owner.

One Operation may correlate to zero, one or multiple Dispatch identities over time.

If a later governed action causes a new dispatch, the new dispatch receives a distinct Dispatch identity/reference and lineage to prior related dispatches where applicable.

```text
Re-dispatch
→ new Dispatch identity
→ prior Dispatch history preserved

Retry / Re-dispatch Requested
!= Retry Policy Authority
!= Executor Attempt automatically

Later Attempt Reference
→ may be correlated when produced by the actual executor owner
→ is never minted or inferred by R2
```

D06 does not decide whether a retry/re-dispatch should occur as a universal policy and does not design R3 continuation/intervention semantics. It only preserves R2 history when a legally supplied coordination intent exists.

Historical Dispatch evidence remains attributable to the Admission, Presence/Reachability, Readiness/Capability, Definition and configuration context applicable at that dispatch. Current state does not silently rewrite history.

---

# 9. R2 Bounded Actual-state Ownership

R2 / RT-R02 final ownership is limited to:

```text
Admission-evidence consumer applicability assessment for R2 coordination
work-to-target coordination correlation state
routing candidate qualification state
route decision / route coordination fact
schedule decision / schedule coordination fact
Dispatch Decision / Dispatch identity
bounded dispatch handoff / coordination evidence
Dispatch lineage / history / uncertainty
```

Explicitly non-owned:

```text
Formal Execution Admission
Node capability/readiness source fact
Node execution Attempt
Node protected Effect/source fact
Agent runtime state
Automation semantic continuation/result
Business Application semantic result
server-local background Attempt
source-domain work/operation semantic authority
universal retry/cancellation/rollback semantics
```

No R2 persistence, history store, queue, scheduler or transport placement becomes a universal Runtime SoT.

---

# 10. RCP-02 Runtime Consumer Refinement

The accepted `ns_server` RCP-02 producer semantics remain normative and are not reopened.

RT-R02 consumer obligations are closed at current Candidate level as follows:

1. correlate the exact Admission Evidence to the intended execution/work subject;
2. preserve applicable Artifact/Definition and Governance evidence references;
3. honor producer-defined applicability, temporal, expiry/revocation, replay/reuse and offline constraints;
4. represent stale, missing, unknown, unverified or indeterminate evidence explicitly;
5. never extend or reissue Admission authority;
6. never treat successful routing/dispatch as retroactive proof of Admission;
7. retain the Admission Evidence reference in Dispatch provenance/history;
8. remain compatible with private/offline use of legitimately applicable retained evidence without requiring a synchronous public service.

```text
RCP-02 Accepted Server Producer Semantics
→ PRESERVED / NOT REOPENED

RCP-02 Runtime Consumer-side Refinement
→ CLOSED AT CURRENT CANDIDATE DESIGN LEVEL

New Admission Authority
→ NONE
```

---

# 11. RCP-04 Runtime Consumer Expectation

This Candidate defines only the evidence properties RT-R02 requires from a future Node Readiness producer. It does not define how `ns_node` determines readiness.

R2 consumer expectation requires, where applicable, sufficient representation-neutral evidence to establish:

```text
Node / Participant Reference
capability identity/reference and supported-scope context
readiness assertion reference where materially required
readiness/capability revision context
attended/unattended or other accepted execution-mode context where relevant
applied configuration revision/context relevant to readiness
freshness / currentness / temporal applicability
availability / unsupported / stale / unknown / indeterminate qualification
provenance / source owner
Tenant / governed-context applicability where required
compatibility / conformance context
```

Permanent:

```text
Reachable != Ready
Route Candidate != Ready Executor
Installed != Ready automatically
Activated != Admitted
Ready != Admission
Readiness Evidence Present != R2 Readiness Authority
```

If readiness evidence is stale/unknown/unavailable, R2 records the corresponding coordination uncertainty. It may not infer Node-local `NOT_READY`, revoke Admission or fabricate a capability fact.

```text
RCP-04 Runtime Consumer Expectation / Refinement
→ CLOSED AT CURRENT CANDIDATE DESIGN LEVEL

RCP-04 ND-R01 Owner-side Semantics
→ NOT DESIGNED

RCP-04 Full Cross-component Closure
→ NOT CLAIMED
```

---

# 12. RCP-05 — RT-R02 Dispatch Evidence Contribution

## 12.1 Stable semantic subject

RCP-05 carries R2-owned Dispatch Decision / coordination evidence while preserving the later executor Attempt as a distinct source-owned fact.

Stable RT-R02 producer-side obligations include where applicable:

```text
Operation / Work Reference
Dispatch Identity / Reference
RT-R02 producer identity / partition
Admission Evidence Reference
source Definition / semantic-owner references where applicable
target Participant / executor reference
route decision / route-candidate context
schedule decision context
R1 Presence / Reachability evidence references
RCP-04 capability/readiness evidence references where applicable
Dispatch decision temporal context
bounded handoff / delivery-coordination evidence
status / uncertainty qualification
retry/re-dispatch lineage where applicable
later Attempt reference only when supplied by executor evidence
Tenant / governed-context references
provenance / history
compatibility / migration / conformance context
private/offline qualification
```

## 12.2 Producer obligations

RT-R02 MUST:

- produce only R2-owned coordination facts;
- preserve Admission Evidence linkage without becoming Admission Authority;
- preserve target and evidence provenance;
- keep Dispatch distinct from later Attempt and Effect;
- preserve prior dispatches when a new dispatch occurs;
- express pending/unavailable/unroutable/stale/unknown/indeterminate conditions explicitly;
- avoid claiming delivery/execution guarantees not established by source evidence;
- remain representation-neutral and private/offline capable.

## 12.3 Consumer obligations

An RCP-05 consumer MUST NOT infer from Dispatch Evidence alone that:

```text
Formal Admission was newly granted
executor accepted work
Attempt exists
Attempt started
Attempt succeeded
Effect occurred
business/Automation/Agent semantic success occurred
```

Consumers must preserve Dispatch identity and correlate later executor-owned Attempt evidence explicitly rather than merging the identities.

## 12.4 Closure boundary

```text
RCP-05 RT-R02 Producer/Coordinator-side Contribution
→ CLOSED AT CURRENT CANDIDATE DESIGN LEVEL

RCP-05 Full Cross-component Closure
→ NOT CLAIMED
→ executor/consumer-side downstream contribution remains unavailable
```

---

# 13. Internal Dependency Topology

This Candidate reuses the accepted Component Internal Design dependency taxonomy:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only `SDD` participates in recursive semantic-definition cycle analysis.

## 13.1 Hard internal SDD graph

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

`D01` consumes RCP-02 through XED/ACD rather than importing S8 semantics into R2 ownership.

`D02` consumes source-domain work requirements through ACD/XED and does not define those source semantics.

## 13.2 R1 → R2 dependency

R1 does not depend on R2 for its own semantic definition or Actual-state ownership.

R2 may consume R1 evidence through `EL` when participant reachability is applicable to a routing/dispatch decision:

```text
P03/P04/P05
→ EL
→ D03/D05
```

This is a one-way evidence dependency, not an Authority transfer, process dependency or deployment dependency.

R2 can retain pending/scheduled coordination state while current presence/reachability evidence is unavailable; it must preserve uncertainty rather than forcing R1 availability to become universal liveness truth.

## 13.3 External evidence dependencies

```text
S8 / RCP-02 Admission Evidence
→ XED / ACD
→ D01 / D05

ND-R01 / RCP-04 Readiness Evidence when applicable
→ XED
→ D03 / D05

source-domain Operation / requirements / revision context
→ XED / ACD
→ D02 / D05 / D06

later executor Attempt Evidence
→ EL / HPL only
→ D06
```

No reverse edge grants R2 authority over those producers.

## 13.4 Cycle result

```text
Hard Internal SDD Graph
→ ACYCLIC

Unresolved SDD Cycle
→ 0

Authority Cycle
→ NONE

Circular Actual-state Ownership
→ NONE
```

---

# 14. Identity / Correlation / Provenance Model

The Candidate requires the following representation-neutral distinctions:

```text
Participant Reference
!= Presence Observation Reference
!= Operation / Work Reference
!= Admission Evidence Reference
!= Dispatch Identity / Reference
!= later Attempt Identity / Reference
!= Effect Identity / Reference
```

The following are scoped architecture-semantic subjects, not a newly created universal identity namespace:

```text
Presence Observation Reference
Dispatch Identity / Reference
```

Both may be realized later using accepted Foundation Correlation & Provenance mechanics while preserving the authoritative identity/reference supplied by the owning domain.

No UUID format, key syntax, database primary key, message key, hostname, socket/session key or wire encoding is selected.

Every R1/R2 evidence subject that may be interpreted historically must preserve enough provenance to identify:

```text
producer / final owner of the bounded assertion
subject identity/reference
applicable source/context revisions
correlation/causal relationship
temporal applicability/freshness where relevant
uncertainty qualification
governed context references where relevant
```

---

# 15. Failure / Unknown / Stale / Unavailable Semantics

R1/R2 consume the accepted Foundation Technical Status & Uncertainty meanings and do not create a universal runtime state machine.

Applicable semantic distinctions include:

```text
UNKNOWN
INDETERMINATE
MISSING
UNAVAILABLE
UNREACHABLE
STALE
CONFLICTING
UNSUPPORTED
UNVERIFIED
RECONCILIATION_PENDING only as referenced future/recovery qualification, not R4 design
```

Boundary-specific coordination outcomes may additionally express semantically cohesive conditions such as:

```text
DISCONNECTED
REACHABLE
UNROUTABLE under declared requirements
ROUTING / SCHEDULING / DISPATCH PENDING
```

These conditions must not redefine Foundation common uncertainty meanings.

Permanent:

```text
Unknown != Negative automatically
Unknown != Positive automatically
Disconnected != Revoked
Unreachable != Not Ready
Unavailable != Denied
Stale != False
Unverified != Trusted
Unroutable != Admission Denied
Dispatch Pending != Attempt Pending automatically
```

No universal fail-open/fail-closed policy is introduced.

---

# 16. Offline / Private Deployment Semantics

Core R1/R2 correctness must remain viable without:

```text
public Internet
public SaaS
mandatory cloud broker
mandatory hosted scheduler
mandatory external coordination control plane
```

## 16.1 R1 offline/degraded behavior

Connection loss or lack of observation is represented as disconnected/unreachable/unknown/stale/indeterminate as evidence supports. It is not interpreted as revocation, distrust, non-admission or non-readiness.

A disconnected participant retains only facts owned by its own component; R1 retains only its own historical coordination evidence.

## 16.2 R2 offline/degraded behavior

R2 may consume legitimately applicable retained Admission Evidence only according to the globally accepted RCP-02 producer semantics. R2 may not extend validity, renew evidence or retroactively authorize work because a central producer is unreachable.

If Admission applicability or required readiness/presence evidence cannot be established for the requested dispatch, R2 remains pending/unroutable/unknown/indeterminate as applicable instead of inventing authorization or a source fact.

```text
Offline != Local Admission Authority
Reconnect != Reconciled
Replay != Retroactive Authorization
Re-dispatch != Prior Dispatch Erasure
```

No mandatory public service dependency is created.

---

# 17. Recovery / Reconciliation Compatibility Without R4 Design

R4 / RT-R04 is not authorized. This Candidate therefore does not define reconciliation algorithms, conflict winners, replay rules, rollback, recovery scheduler or latest-wins behavior.

R1/R2 are intentionally shaped so future R4 can operate without semantic repair:

1. Presence and Dispatch evidence retain producer provenance and stable correlation subjects.
2. Currentness/uncertainty is explicit instead of encoded as destructive overwrites.
3. Reconnect is recorded as R1 evidence but is not treated as reconciliation.
4. A new Dispatch does not overwrite a prior Dispatch.
5. Admission Evidence linkage remains historical and cannot be rewritten by a later admission state.
6. Later Attempt/Effect evidence remains source-owned and only correlated.
7. No timestamp is declared a universal conflict winner.
8. No local or central copy becomes SoT by recovery placement.

```text
Reconnect != Reconciled
Recovery != SoT Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
```

---

# 18. Future R3 Compatibility Without R3 Design

R3 / RT-R03 is not authorized. R1/R2 nevertheless preserve the minimum correlation surface required not to block later continuation/delegation/intervention design:

```text
Operation / Work Reference
Dispatch Identity / Reference
source semantic owner / revision references
Admission Evidence Reference
Participant target reference
later Attempt Reference when source evidence supplies it
correlation / provenance lineage
```

This Candidate does **not** define:

```text
continuation state
intervention request lifecycle
cancel/retry/resume applicability
final intervention outcome
HITL resume semantics
Agent delegation semantics
Automation continuation semantics
```

The existence of correlation compatibility is not RCP-06 or RCP-12 closure.

---

# 19. Cross-component Journey Consistency

## 19.1 Presence / participation journey

```text
Participant-side observation/evidence
→ R1 / RT-R01 connection/presence qualification
→ R1 reachability coordination fact
→ authorized consumers may reference bounded evidence
```

Permanent:

```text
Presence != Trust
Presence != Admission
Presence != Node Readiness
Connected != Trusted != Admitted
Reachable != Ready
```

## 19.2 Governed execution dispatch journey

```text
governed work / execution intent
→ applicable governance context
→ S8 / SV-R04 Formal Admission Evidence
→ D01 consumer applicability
→ D02 work/target correlation
→ D03 routing candidate qualification
   + R1 Presence/Reachability where applicable
   + RCP-04 Readiness/Capability evidence where applicable
→ D04 scheduling coordination
→ D05 Dispatch Decision / RCP-05 evidence
→ later executor-owned Attempt
→ later source/effect-owner facts
```

Permanent:

```text
Admission Evidence != Dispatch Evidence
Dispatch Evidence != Attempt Evidence
Attempt Evidence != Protected Effect Evidence
```

## 19.3 Server-local work

Accepted S10 remains unchanged:

```text
server-local asynchronous / delayed / periodic / long-running work
!= automatically ns_runtime work
```

R2 participates only when genuine cross-component routing/scheduling/dispatch coordination is required. `ns_runtime` does not become universal scheduler authority merely because work is asynchronous.

---

# 20. Shared Foundation Consumption

R1/R2 consume accepted Shared Foundation semantics only through accepted Stable Entry → Contract → Module paths where applicable.

Relevant reuse includes:

```text
C01 Bootstrap Configuration Acquisition
→ local ns_runtime bootstrap only
→ does not become Managed Desired-state Authority

C02 Diagnostic Occurrence & Delivery Evidence
C03 Technical Observation & Health Evidence
→ diagnostics/technical evidence only
→ do not become Presence/Dispatch source authority

C04 Temporal & Freshness
→ freshness/currentness/deadline semantics
→ no clock/TTL algorithm selected

C05 Operation Correlation & Provenance Context
→ Operation/Dispatch/Attempt lineage carriage
→ no physical identifier format selected

C06 Semantic Representation & Serialization
→ representation-neutral semantic preservation
→ no JSON/Protobuf/DTO/wire format selected

C07 Network Invocation Mechanics
→ reusable network mechanics where later applicable
→ transport success remains technical evidence only

C10 Technical Status & Uncertainty
→ shared UNKNOWN/STALE/UNAVAILABLE/etc. meanings

C11 Governed Context Propagation
→ Tenant/Org/Principal/Policy/Trust reference carriage
→ Context presence != authority/authorization

C12 Secret Reference
C13 Sensitive-data Redaction
→ reference/material and disclosure separation where runtime connection/config/diagnostic evidence is sensitive

C14 Compatibility & Conformance
→ shared classification/evidence mechanics
→ final R1/R2 semantic conformance remains subject-owner responsibility
```

```text
Missing Mandatory Foundation Semantic
→ NONE FOUND

New Foundation Capability Created
→ 0

Foundation Authority Transfer
→ 0
```

Deferred Foundation candidates `Cryptographic / Evidence-verification Helpers` and `Database Utility Primitives` remain deferred and are not required for current R1/R2 semantic closure.

---

# 21. Configuration / Secret Boundary

Accepted configuration topology remains:

```text
ns_runtime local bootstrap configuration
→ local runtime concern
→ may consume accepted Bootstrap Configuration Foundation semantics

Managed Runtime Desired Configuration
→ S9 / ns_server

R1/R2 intrinsic configuration item meaning
→ ns_runtime for its own coordination semantics

R1/R2 Applied Configuration Actual-state
→ applicable R1/R2 bounded runtime partition

Observed configuration
→ derived projection
```

```text
Desired != Distributed != Applied != Observed
Configuration != Secret Material
Secret Reference != Secret Material
```

No configuration format, push/pull/watch protocol, rollout mechanism, secret store, KMS, provider or credential schema is selected.

---

# 22. Compatibility / Migration / Conformance

R1/R2 stable semantics must remain interpretable across compatible evolution.

Material compatibility obligations include:

- Participant References must remain resolvable without creating a runtime-owned identity authority.
- Presence/Reachability evidence revisions must not silently reinterpret stale/unknown/disconnected history.
- RCP-02 consumer changes must remain conformant to accepted S8 producer semantics.
- RCP-04 consumer evolution must not preempt future Node owner semantics.
- Dispatch Evidence revisions must preserve Operation/Dispatch/Attempt separation and historical lineage.
- Provider/transport/storage/process replacement with unchanged semantics is not architecture change by itself.
- Unsupported contract revisions/cases remain explicit rather than coerced to current/latest meaning.

Migration of a physical transport, scheduler mechanism, storage mechanism or provider is downstream realization work if these semantic obligations remain unchanged.

Any proposal that changes accepted Authority/SoT/Actual-state ownership, makes a new global scheduling law, creates a major identity namespace, or freezes a major protocol/provider/storage commitment requires governance revalidation/MDE classification.

---

# 23. Explicit Implementation Deferrals

This Candidate intentionally does not select or design:

```text
heartbeat implementation
session implementation
socket lifecycle
WebSocket frame / handshake / message envelope
endpoint / API / DTO / wire schema
TTL / timeout value or algorithm
clock source
Redis / RabbitMQ / Kafka / NATS
Celery / Temporal / Airflow / Quartz / APScheduler
queue / broker / topic / subscription
scheduler algorithm / priority/fairness formula
retry cadence / retry count / backoff
exactly-once / at-most-once / at-least-once guarantee
cancellation / rollback / compensation engine
routing algorithm / load-balancing algorithm
process / service / worker / thread / coroutine topology
container / pod / host / deployment topology
database / table / ORM / persistence layout
message key / UUID / primary-key format
public cloud control-plane dependency
```

These deferrals are legal because the Candidate closes the architecture-semantic responsibility, ownership, evidence, uncertainty, correlation and non-guarantee boundaries needed to constrain later realization. No implementation layer is authorized to contradict those semantics.

---

# 24. Explicit Non-closed / Non-authorized Contract Scope

```text
RCP-03 Full Cross-component Closure
→ NOT CLAIMED

RCP-04 Full Cross-component Closure
→ NOT CLAIMED

RCP-05 Full Cross-component Closure
→ NOT CLAIMED

RCP-06 Continuation / Intervention
→ NOT DESIGNED

RCP-12 Agent Delegation
→ NOT DESIGNED

RCP-13 beyond accepted ns_server Automation semantics
→ NOT DESIGNED

RCP-15 beyond accepted ns_server Automation semantics
→ NOT DESIGNED

RCP-16 Full Cross-component Human Task Closure
→ NOT DESIGNED / NOT CLAIMED

RCP-20 Recovery / Reconciliation
→ NOT DESIGNED

RCP-21 Full Cross-component Discovery Closure
→ NOT DESIGNED / NOT CLAIMED
```

Correlation compatibility with a future contract is not owner-side design or full closure.

---

# 25. DAD / MDE Classification Result

The durable architecture-semantic decisions made by this Candidate are recorded separately as:

```text
CID-RT-B1-DAD-001..012
```

The decisions remain within the exact GAC authorization and do not move an accepted Authority/SoT/Actual-state owner, define a new Product capability, choose a universal scheduler/retry/cancellation/conflict law, create a major identity namespace, choose a material offline fail-open/fail-closed policy, or lock a provider/protocol/framework/storage technology.

```text
New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

MDE Stop Boundary Triggered
→ NO
```

---

# 26. Semantic Resolution Matrix

| Dimension | Candidate resolution |
|---|---|
| R1 Responsibility Decomposition | `CLOSED` — P01..P05 |
| R2 Responsibility Decomposition | `CLOSED` — D01..D06 |
| RT-R01 Traceability | `CLOSED` — R1/P01..P05 |
| RT-R02 Traceability | `CLOSED` — R2/D01..D06 |
| Authority / SoT | `CLOSED` — upstream unchanged; no runtime semantic-authority escalation |
| R1 Actual-state | `CLOSED` — connection/presence/freshness/reachability coordination facts only |
| R2 Actual-state | `CLOSED` — routing/scheduling/dispatch coordination facts only |
| Presence vs Trust/Admission | `CLOSED` — explicit non-collapse |
| Reachability vs Readiness | `CLOSED` — explicit non-collapse |
| Admission vs Dispatch | `CLOSED` — RCP-02 consumer only; RCP-05 producer only |
| Dispatch vs Attempt/Effect | `CLOSED` — distinct identities/evidence owners |
| Identity / Correlation | `CLOSED` — scoped representation-neutral subjects; no major universal namespace |
| Temporal / Freshness | `CLOSED` — explicit current/stale/unknown/indeterminate; no TTL/clock selection |
| Failure / Unknown / Unavailable | `CLOSED` — Foundation uncertainty semantics preserved |
| Offline / Private | `CLOSED` — no mandatory public service; no authority escalation |
| Recovery Compatibility | `CLOSED FOR R1/R2 COMPATIBILITY` — no R4 algorithm/design |
| R3 Compatibility | `CLOSED FOR CORRELATION COMPATIBILITY` — no R3 semantics designed |
| RCP-03 | `RT-R01 CONTRIBUTION CLOSED AT CURRENT CANDIDATE DESIGN LEVEL` |
| RCP-02 | `RUNTIME CONSUMER REFINEMENT CLOSED AT CURRENT CANDIDATE DESIGN LEVEL` |
| RCP-04 | `RUNTIME CONSUMER EXPECTATION CLOSED AT CURRENT CANDIDATE DESIGN LEVEL` |
| RCP-05 | `RT-R02 CONTRIBUTION CLOSED AT CURRENT CANDIDATE DESIGN LEVEL` |
| Shared Foundation Consumption | `CLOSED` — accepted contracts reused; no new Foundation requirement |
| Compatibility / Migration / Conformance | `CLOSED AT COMPONENT INTERNAL DESIGN LEVEL` |
| Implementation Mechanics | `EXPLICITLY DEFERRED TO NAMED LATER REALIZATION AUTHORITY` |
| MDE | `NONE REQUIRED` |

```text
Missing/Ambiguous Normative Dimension
→ 0

Implementation-defined Architecture Escape
→ 0

Unmapped Material Decision
→ 0
```

---

# 27. Candidate Result / Maximum Legal State

```text
NGRP-001
Component Internal Design
/ ns_runtime
/ Batch 1
/ R1 + R2

→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This Candidate does not claim Global Acceptance, `ns_runtime` Internal Design Exhaustion, `ns_runtime` Component Internal Design global closure, Batch 2 authorization, R3/R4 authorization, other Product Component authorization or any downstream implementation phase.
