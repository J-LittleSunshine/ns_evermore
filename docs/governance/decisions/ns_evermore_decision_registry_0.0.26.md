# ns_evermore Decision Registry — Current Revision

- Version: `0.0.26`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.25`

All accepted normative decisions and baselines in Decision Registry `0.0.25` remain in force unless explicitly refined below.

## Current Accepted Global Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
Unified Governance → 0.0.2 / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Product Capability Exhaustion → SATISFIED
Five-component Internal Architecture Boundaries → GLOBAL_ACCEPTED / NORMATIVE
Five-component Internal-boundary Exhaustion → SATISFIED
Accepted Internal Boundaries → 34
Runtime Responsibility Architecture → GLOBAL_CLOSED / COMPLETE
Runtime Roles → 22
Runtime / Domain Stable Contract Pressure → 24 / NAMED DOWNSTREAM DESIGN AUTHORITY
Shared Foundation Architecture → GLOBAL_CLOSED / COMPLETE
Foundation Contract Design → GLOBAL_CLOSED / COMPLETE
Foundation Module Design → GLOBAL_CLOSED / COMPLETE
Foundation Provider Design → GLOBAL_CLOSED / COMPLETE
Foundation Provider Design Exhaustion → SATISFIED
Accepted Foundation Capabilities → 14 / NORMATIVE
Accepted Foundation Contracts → 15 / NORMATIVE
Accepted Foundation Modules → 14 / NORMATIVE
Accepted Foundation Provider Families → 10 / NORMATIVE
Component Internal Design Readiness → SATISFIED
```

## ns_server Component Internal Design Baseline Preserved

```text
ns_server Component Internal Design
→ GLOBAL_CLOSED / COMPLETE

ns_server Internal Design Exhaustion
→ SATISFIED

Accepted Boundary Coverage
→ 13 / 13 / 100%

Remaining Material ns_server Component Internal-design Pressure
→ NONE_FOUND
```

All accepted `CID-SV-B1-DAD-*` through `CID-SV-B8-DAD-*`, recognized Owner MDEs, accepted Authority / SoT / Actual-state partitions and stable contract contribution state from Decision Registry `0.0.25` remain normative.

Permanent downstream state remains:

```text
RCP-16 Full Cross-component Closure
→ NOT CLOSED

RCP-21 Full Cross-component Closure
→ NOT CLOSED
```

## ns_runtime Component Internal Design — Batch 1 Global Acceptance

Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_runtime_internal_design_batch_1_global_acceptance_0.0.1.md`

```text
Batch 1
→ GLOBAL_ACCEPTED

Accepted Boundaries
→ R1 Connection / Participant Presence Coordination
→ R2 Governed Routing / Scheduling / Dispatch Coordination

Accepted Runtime Roles
→ RT-R01 Participant Presence Coordinator
→ RT-R02 Governed Routing / Scheduling / Dispatch Coordinator

Accepted Boundary Coverage
→ 2 / 4 / 50%

Accepted Internal Responsibility Count
→ 11

Accepted DAD
→ CID-RT-B1-DAD-001..012

Hard Internal SDD Graph
→ ACYCLIC
```

### Accepted R1 Internal Architecture

```text
P01 Participant Reference & Coordination-context Binding
P02 Connection Observation & Presence-evidence Intake
P03 Presence Currentness & Freshness Qualification
P04 Reachability Qualification & Uncertainty Custody
P05 Presence History, Projection & RCP-03 Contract Governance
```

R1 / RT-R01 owns only bounded runtime-originated connection/presence/currentness/reachability coordination facts and their history/provenance/uncertainty.

Permanent:

```text
Connected != Trusted != Admitted
Reachable != Ready
Disconnected != Revoked
Stale != False
Unknown != Disconnected
Presence Projection != Participant-local SoT
```

```text
Universal Participant Truth Store
→ NOT CREATED

Universal Runtime SoT
→ NOT CREATED
```

### Accepted R2 Internal Architecture

```text
D01 Admitted-work Intake & Admission-evidence Applicability
D02 Work Requirement & Target Correlation
D03 Routing Candidate Qualification
D04 Scheduling Coordination & Bounded Ordering
D05 Dispatch Decision, Handoff & Evidence Custody
D06 Dispatch Lineage, History & Later-attempt Correlation
```

R2 / RT-R02 owns only bounded Admission-evidence consumer applicability and routing/scheduling/dispatch coordination facts.

Permanent:

```text
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Route Candidate != Ready Executor
Dispatch Evidence != Attempt Evidence
Dispatch Handoff Evidenced != Attempt Started
Dispatch Success != Execution Started
Execution Started != Protected Effect
```

```text
Formal Execution Admission Authority
→ ns_server / S8 / SV-R04 / PRESERVED

Node Readiness owner-side semantics
→ ns_node / N1 / ND-R01 / downstream / PRESERVED

Node Attempt
→ ns_node / N2 / ND-R02 / downstream / PRESERVED

Node protected Effect/source fact
→ ns_node / N3 / ND-R03 / downstream / PRESERVED
```

No universal scheduler, workflow, job, retry, cancellation, rollback or operation authority is created.

## ns_runtime Batch 1 Identity / Correlation Baseline

Accepted semantic distinctions:

```text
Participant Reference
!= Presence Observation Reference
!= Operation / Work Reference
!= Admission Evidence Reference
!= Dispatch Identity / Reference
!= later Attempt Identity / Reference
!= Effect Identity / Reference
```

`Presence Observation Reference` and `Dispatch Identity / Reference` are scoped R1/R2 evidence subjects only; no major universal identity namespace or physical identity format is accepted.

Historical evidence preserves producer/final owner, subject identity/reference, applicable source/context revisions, causal/correlation relationship, temporal/freshness qualification and uncertainty where applicable.

## ns_runtime Batch 1 Stable Contract State

```text
RCP-03 RT-R01 owner/coordinator-side contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-03 Full Cross-component Closure
→ NOT CLOSED

RCP-05 RT-R02 producer/coordinator-side contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-05 Full Cross-component Closure
→ NOT CLOSED

RCP-02 accepted ns_server producer semantics
→ PRESERVED / NOT REOPENED

RCP-02 runtime consumer-side applicability/refinement
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-04 runtime consumer expectation/refinement
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-04 ND-R01 owner-side semantics
→ NOT YET INTERNALLY DESIGNED / ACCEPTED

RCP-04 Full Cross-component Closure
→ NOT CLOSED
```

Still explicitly downstream / not closed by Batch 1:

```text
RCP-06 Continuation / Intervention
RCP-12 Agent Delegation
RCP-13 beyond accepted ns_server Automation semantics
RCP-15 beyond accepted ns_server Automation semantics
RCP-16 Full Cross-component Human Task closure
RCP-20 Recovery / Reconciliation
RCP-21 Full Cross-component Discovery closure
```

No additional full cross-component RCP closure is inferred.

## Accepted DAD Baseline — CID-RT-B1

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

No Owner MDE is created or resolved by this Batch.

## Offline / Private / Technology-neutrality Baseline

```text
Mandatory Public Internet / SaaS Dependency
→ NONE

Mandatory Cloud Broker / Hosted Scheduler
→ NONE

Runtime Offline Admission Authority
→ NONE

Universal Scheduling Priority / Fairness Law
→ NOT CREATED

Global Retry / Cancellation / Rollback Law
→ NOT CREATED

Exactly-once / At-most-once / At-least-once Universal Guarantee
→ NOT CREATED

Global Conflict Winner / Latest-wins Law
→ NOT CREATED

Concrete Broker / Queue / Scheduler / DB / API / Wire / Process / Deployment Selection
→ NONE
```

Permanent:

```text
Disconnected != Revoked
Unknown != Denied
Stale != False
Reconnect != Reconciled
Recovery != SoT Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
```

## Current Governance Boundary After ns_runtime Batch 1 Acceptance

```text
ns_runtime Component Internal Design / Batch 1
→ GLOBAL_ACCEPTED

Accepted ns_runtime boundary coverage
→ R1 / R2
→ 2 / 4 / 50%

Remaining accepted ns_runtime boundaries without Component Internal Design
→ R3 / R4

ns_runtime Internal Design Exhaustion
→ NOT YET REASSESSED AFTER BATCH 1 ACCEPTANCE

ns_runtime Component Internal Design Global Closure
→ NOT DECLARED

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Item
→ NONE

Current Authorized Phase
→ NONE

ns_runtime Batch 2 / R3 / R4
→ NOT AUTHORIZED

ns_node Component Internal Design
→ NOT AUTHORIZED

ns_agent Component Internal Design
→ NOT AUTHORIZED

ns_web Component Internal Design
→ NOT AUTHORIZED

System-level SDK Detailed Design
→ NOT AUTHORIZED

Design-to-Implementation Readiness
→ NOT AUTHORIZED

Implementation Planning / IWP / Coding
→ NOT AUTHORIZED
```

Unique next legal action:

```text
Fresh Repository recovery
→ perform post-Batch-1 ns_runtime Component Internal Design remaining-pressure / exhaustion / batching assessment
→ determine immediate next architecture-safe boundary/batch candidate from remaining R3 / R4 pressure
→ do not authorize Batch 2 automatically from this Registry revision
```
