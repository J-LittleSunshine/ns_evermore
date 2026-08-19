# ns_evermore Decision Registry — Current Revision

- Version: `0.0.21`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.20`

## Current Accepted Baseline

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

## Accepted ns_server Component Internal Design

```text
Batch 1 → GLOBAL_ACCEPTED
Boundaries → S1 / S2 / S3 / S4 / S8 / S9
Accepted DAD → CID-SV-B1-DAD-001..013
RCP-01 / RCP-02 / RCP-19 → CLOSED AT DESIGN-SEMANTIC LEVEL
S8 Artifact Identity / Acceptance Evidence → CLOSED AT DESIGN-SEMANTIC LEVEL

Batch 2 → GLOBAL_ACCEPTED
Boundary → S6 Automation Definition, Trigger & Composition Lifecycle
Accepted DAD → CID-SV-B2-DAD-001..014
Recognized Owner MDE → CID-SV-B2-MDE-001
RCP-13 / RCP-14 / RCP-15 → CLOSED AT DESIGN-SEMANTIC LEVEL
RCP-16 Automation Source-side → CLOSED AT CURRENT DESIGN LEVEL
RCP-17 Automation side → CLOSED AT CURRENT DESIGN LEVEL

Batch 3 → GLOBAL_ACCEPTED
Boundary → S5 Business Application Definition Lifecycle
Runtime Role Input → SV-R01 Business Application Runtime Participant
Accepted DAD → CID-SV-B3-DAD-001..012
RCP-17 Business Application side → CLOSED AT CURRENT DESIGN LEVEL
RCP-23 S5 / SV-R01 contribution → CLOSED AT CURRENT DESIGN LEVEL

Batch 4 → GLOBAL_ACCEPTED
Boundary → S7 Enterprise Data / Knowledge / Foundational ETL Governance
Runtime Role Input → SV-R03 Data / Knowledge / ETL Runtime Participant
Accepted DAD → CID-SV-B4-DAD-001..015
Recognized Owner MDE → CID-SV-B4-MDE-001
RCP-17 S7 Data / Knowledge / ETL side → CLOSED AT CURRENT DESIGN LEVEL
RCP-23 S7 / SV-R03 contribution → CLOSED AT CURRENT DESIGN LEVEL

Batch 5 → GLOBAL_ACCEPTED
Boundary → S10 Server-local Background Work & Server Actual-state
Runtime Role Input → SV-R06 Server-local Background Execution Participant
Accepted Internal Module Count → 7
Accepted DAD → CID-SV-B5-DAD-001..015
RCP-23 S10 / SV-R06 contribution → CLOSED AT CURRENT DESIGN LEVEL
RCP-23 Full Server-native Runtime Evidence → CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL
```

Batch-5 Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_5_global_acceptance_0.0.1.md`

Full RCP-16 and full RCP-17 remain downstream where not explicitly globally accepted. RCP-23 is now fully closed at the current design-semantic level.

## Recognized Owner Decisions Relevant to Current ns_server Baseline

### CID-SV-B2-MDE-001 — Automation Recursive Invocation

```text
Native Automation-to-Automation Recursive Invocation
→ NOT SUPPORTED

Reusable Automation-to-Automation Composition
→ REQUIRED / PRESERVED

Canonical Automation Composition Dependency
→ ACYCLIC
```

Permanent qualification:

```text
Recursive Automation-to-Automation Invocation NOT SUPPORTED
!= generic Automation loop / iteration prohibited
!= repeated non-recursive invocation prohibited
!= retry / re-entry prohibited
```

### CID-SV-B4-MDE-001 — S7 Native Definition Canonical SoT Topology

```text
Selected Option
→ A

Native Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server

Native S7 Canonical Definition SoT
→ ns_server

Semantic Authority
!= Canonical Definition SoT

Native S7 Definition SoT
!= Factual Data / Knowledge SoT

Factual Data / Knowledge SoT
→ exactly one final SoT per bounded semantic partition
→ different partitions may have different final SoTs
→ external enterprise systems may remain final factual SoTs
```

No storage, database, schema, ETL engine, connector, source format, visual schema, provider, runtime topology or implementation layout is selected by this MDE.

## Accepted S7 Internal Architecture Baseline

Accepted architecture-semantic responsibilities:

```text
DK01 Native S7 Definition & Canonical Revision Governance
DK02 Authoring Intake & Semantic Interoperability
DK03 Definition Validation & Semantic Certification Evidence
DK04 Factual Partition & Source Authority Binding Governance
DK05 External Source Schema Reference & Mapping Governance
DK06 ETL Definition & Transformation / Derivation Governance
DK07 Knowledge Definition & Derived Knowledge Governance
DK08 Query & Aggregation Semantic Governance
DK09 S7 Runtime Operation & Semantic Result
DK10 S7 Trial Semantics & Runtime Evidence
```

Definition/factual/runtime non-collapse remains normative:

```text
Native S7 Definition SoT != Factual Data / Knowledge SoT
External Source Schema != Native S7 Definition automatically
Mapping Definition != Source Fact
ETL Definition != Runtime Operation != ETL Output Fact
Derived / Aggregated Fact != Upstream Source Fact
Native Knowledge Definition != Index / Vector / Embedding / Retrieval Result
Query Result != Source Fact automatically
```

## Accepted S10 Internal Architecture Baseline

Accepted architecture-semantic responsibilities:

```text
BG01 Background Operation Identity & Initiation Context
BG02 Time-trigger & Continuous-availability Semantics
BG03 Attempt Lifecycle & Lineage Custody
BG04 Progress, Outcome & Server-local Source-fact Custody
BG05 Intervention & Retry/Re-entry Applicability
BG06 Recovery, Reconciliation & Historical Qualification
BG07 Runtime Governance & Applied Configuration Binding
```

`BG01..BG07` are architecture-semantic responsibility labels only and are not Django Apps, packages, classes, services, processes, workers, schedulers, queues, tables, schemas, databases or deployment units.

### S10 / SV-R06 Actual-state Partition

```text
S10 Product Semantic Authority Added
→ NONE

SV-R06 final Actual-state/source-fact owner
→ server-local Attempt
→ server-local progress
→ server-local outcome
→ genuine server-local source facts

Same bounded runtime assertion
→ exactly one final Actual-state owner
```

Permanent non-collapse:

```text
S10 Attempt
!= Business Application semantic Runtime state
!= Automation semantic Runtime state
!= Data / Knowledge / ETL semantic Runtime state
!= Node Attempt / Effect
!= Agent Runtime
!= RT Scheduling / Routing / Dispatch
```

### Operation / Attempt / Retry Semantics

```text
Background Operation
→ representation-neutral logical server-local work subject

Operation Identity
!= Attempt Identity
!= Correlation Identity
!= Scheduler / Queue / Worker / Process identity

Operation → Attempts
→ 0..N

Attempt
→ one bounded semantic execution try

Attempt != Progress != Outcome
```

```text
Retry Intent
!= Retry Accepted
!= Retry Attempt Registered
!= Retry Attempt Started
!= Retry Attempt Outcome

new retry execution try
→ new Attempt identity + retry lineage

Re-entry
→ same Attempt only when continuity is proven
→ otherwise new Attempt + re-entry lineage
```

No exactly-once, at-most-once, at-least-once, deterministic replay, rollback or latest-attempt-wins guarantee is accepted.

### Time-trigger / Long-running / Intervention

```text
Due != Operation Initiated != Attempt Started
Time-triggered != Scheduler Authority
Long-running != Worker / Daemon / Process / Thread topology
Continuous Availability != Zero-downtime Guarantee
```

```text
Intervention Requested
!= Applicable
!= Accepted
!= Action Started
!= Achieved
!= Effects Reversed
```

No universal retry/cancellation/pause/resume/rollback engine or policy is accepted.

### Server-local vs Cross-component

```text
Pure server-local S10 work
→ does not require ns_runtime merely because async / delayed / periodic / long-running

Cross-component execution
→ applicable Admission
→ RT-R02 / RT-R03 where genuinely required
→ remote executor retains its Attempt / Effect / source facts
```

S10 may correlate remote evidence but does not absorb remote Actual-state.

### Recovery / Configuration / Offline

```text
Reconnect != Reconciled
Recovery != Authority Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
Local Persistence != Actual-state Ownership
Restart != Same Attempt automatically
Restart != New Attempt automatically
```

```text
Managed Desired Configuration → S9
S10 Applied Runtime Evidence → S10 / SV-R06 where applicable
Observed Projection → derived
Desired != Distributed != Applied != Observed
```

No global fail-open/fail-closed, local-wins, central-wins or latest-wins policy is accepted.

## RCP-23 — Full Server-native Runtime Evidence Closure

Accepted producer partitions:

```text
S5 / SV-R01
→ Business Application semantic Runtime Evidence

S7 / SV-R03
→ Data / Knowledge / ETL semantic Runtime Evidence

S10 / SV-R06
→ Server-local Background Runtime Evidence
```

```text
RCP-23 S5 / SV-R01 contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-23 S7 / SV-R03 contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-23 S10 / SV-R06 contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-23 Full Server-native Runtime Evidence
→ CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL
```

Common contract semantics preserve producer-partition identity, Operation identity, producer-specific revision references, owned state/result/outcome, governance/config applicability, correlation/provenance, temporal/history/uncertainty, compatibility/conformance and private/offline qualification.

Permanent:

```text
SV-R01 != SV-R03 != SV-R06
Common Contract != Common Authority != Common Actual-state Owner
Universal Server Runtime Actual-state SoT → NOT CREATED
```

Attempt identity remains S10-specific unless independently established by another producer's accepted semantics. Batch 5 does not reopen accepted S5 or S7 internals.

## Foundation / Provider Neutrality

S10 consumes only accepted Foundation semantics through the accepted Stable Entry → Contract → Module → Provider path where applicable.

```text
Foundation != S10 Authority
Provider != S10 Authority
Time Source != Scheduler Authority
Storage Placement != Actual-state Ownership
Telemetry Aggregation != Runtime SoT
Provider Success != S10 Semantic Success
```

No new Foundation capability or Provider family is created by Batch 5.

## Current Governance Boundary After Batch 5 Acceptance

```text
Remaining accepted ns_server boundaries without Component Internal Design
→ S11 / S12 / S13

ns_server Component Internal Design Global Closure
→ NOT DECLARED

ns_server Internal Design Exhaustion
→ NOT YET REASSESSED AFTER BATCH 5 ACCEPTANCE

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Current Authorized Phase
→ NONE

Another ns_server Batch
→ NOT AUTHORIZED

Other Product Component Internal Design
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
→ perform ns_server Component Internal Design remaining-pressure / exhaustion / batching assessment after Batch 5 acceptance
→ no downstream producing session is authorized automatically
```
