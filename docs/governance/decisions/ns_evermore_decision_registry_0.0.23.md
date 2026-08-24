# ns_evermore Decision Registry — Current Revision

- Version: `0.0.23`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.22`

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

All accepted normative decisions and baselines in Decision Registry `0.0.22` remain in force unless explicitly refined below.

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

Batch 6 → GLOBAL_ACCEPTED
Boundary → S12 Governed Notification & External Delivery Lifecycle
Runtime Role Input → SV-R08 Notification Lifecycle & External Delivery Participant
Accepted Internal Module Count → 8
Accepted DAD → CID-SV-B6-DAD-001..019
RCP-18 Notification / Delivery → CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL

Batch 7 → GLOBAL_ACCEPTED
Boundary → S11 Unified Human Task Aggregation & Response Routing
Runtime Role Input → SV-R07 Human Task Aggregation & Response Routing Participant
Accepted Internal Module Count → 8
Accepted DAD → CID-SV-B7-DAD-001..021
RCP-16 S11 / SV-R07 contribution → CLOSED AT CURRENT DESIGN LEVEL
RCP-16 Full Cross-component Closure → NOT CLOSED / remains downstream
```

Batch-7 Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_7_global_acceptance_0.0.1.md`

## Recognized Owner Decisions Relevant to Current ns_server Baseline

### CID-SV-B2-MDE-001 — Automation Recursive Invocation

```text
Native Automation-to-Automation Recursive Invocation → NOT SUPPORTED
Reusable Automation-to-Automation Composition → REQUIRED / PRESERVED
Canonical Automation Composition Dependency → ACYCLIC
```

### CID-SV-B4-MDE-001 — S7 Native Definition Canonical SoT Topology

```text
Selected Option → A
Native Data / Knowledge / Foundational ETL Semantic Authority → ns_server
Native S7 Canonical Definition SoT → ns_server
Semantic Authority != Canonical Definition SoT
Native S7 Definition SoT != Factual Data / Knowledge SoT
Factual Data / Knowledge SoT
→ exactly one final SoT per bounded semantic partition
→ different partitions may have different final SoTs
→ external enterprise systems may remain final factual SoTs
```

### Unified Governed Human Task Inbox Owner Capability

```text
Unified Governed Human Task Inbox → REQUIRED
Applicable Sources → Automation HITL / Agent HITL
Cross-session Rediscovery / Re-observation → REQUIRED where applicable
Generic Notification Center → NOT IMPLIED
Universal Enterprise Attention Center → NOT IMPLIED
```

Permanent:

```text
Human Task → needs human action
Notification → needs human awareness
Human Task Inbox != Notification Center
Human Response != Notification Acknowledgement
```

### Governed Notification / External Delivery Owner Capability

```text
Unified Governed Notification Capability → REQUIRED
In-product Notification Discovery / History → REQUIRED
Channel-neutral Core Notification Semantics → REQUIRED
Pluggable External Notification Delivery → REQUIRED
External Platform Push → REQUIRED AS PRODUCT CAPABILITY
Representative Target Directions → Feishu / WeCom / SMS
Mandatory Fixed Omnichannel Provider Set → NOT REQUIRED
Public Internet / Public SaaS Dependency for Core Correctness → PROHIBITED
```

## Accepted S11 Internal Architecture Baseline

Accepted architecture-semantic responsibilities:

```text
HT01 Human-action Source Contribution & Authority Binding Intake
HT02 Human Task Projection Identity, Correlation & Historical Lineage Custody
HT03 Participant Applicability, Authorization & Disclosure Qualification
HT04 Projection Freshness, Staleness, Supersession & Re-observation Qualification
HT05 Human Response Submission Correlation & Provenance Qualification
HT06 Response Routing Lifecycle, Attempt & Evidence Custody
HT07 Offline Recovery, Reconciliation & Historical Currentness Qualification
HT08 Stable Contract, Compatibility & Discovery-contribution Governance
```

Accepted ownership:

```text
Automation Human-action Requirement / Wait / response applicability / semantic resume
→ S6 / SV-R02

Agent Human-action Requirement / Wait / response applicability / continuation
→ ns_agent / AG-R01

Human Response Submission occurrence
→ ns_web / WB-R01

S11 / SV-R07
→ Human Task Projection Identity / existence / history
→ projection freshness / staleness / currentness
→ source correlation state
→ response-routing Attempt / state / evidence
→ S11 recovery / reconciliation qualification
```

Permanent:

```text
Human Task Projection != Source Human-action Requirement / Wait State
Human Task Projection != Source semantic applicability
Aggregation != Canonicalization
Projection != Source SoT
Inbox entry != Source state
```

### Projection Identity / History

```text
Human Task Projection Identity
→ durable / session-independent / representation-neutral
→ S11-owned identity for one projection lineage

Projection Identity
!= Source Requirement Identity automatically
!= Execution / Operation Identity
!= Response Submission Identity
!= Routing Attempt Identity
!= Correlation Identity automatically
!= Database PK / Browser Session / Message ID automatically
```

Source revision/context continuity is evidence-driven. No latest-revision or timestamp-based identity rebinding is accepted.

### Freshness / Cross-session

S11 may express orthogonal projection qualifications where applicable:

```text
CURRENT / STALE / UNKNOWN / PARTIAL / UNAVAILABLE
SUPERSEDED / EXPIRED / WITHDRAWN
INDETERMINATE / CONFLICTING
RECONCILIATION_PENDING / RECOVERING
```

These are not a universal source Human Task lifecycle state machine. No universal TTL, timeout or escalation policy is accepted.

Cross-session rediscovery is based on durable Projection Identity + source binding/currentness evidence. Browser/session state is not authoritative.

### Principal / Response Semantics

```text
Task Exists != every Principal may see it
Principal may discover != Principal may submit
Principal may submit != response semantically applicable
UI affordance visible != Policy Permit
source participant display != S11 assignment Authority
```

```text
Human Response Submission occurrence → WB-R01
S11 / HT05 → correlation / provenance / context qualification
Originating source owner → semantic applicability / acceptance / application / continuation
```

Permanent:

```text
Response Submitted
!= Response Valid
!= Response Applicable
!= Response Accepted
!= Response Applied
!= Source Wait Resolved
!= Execution Resumed
!= Policy Permit / Artifact Acceptance / Execution Admission
```

No universal assignment/claim/ownership/delegation strategy, responder winner or dedup rule is accepted.

### Response Routing

```text
Response Routing Attempt Identity
→ one bounded S11 routing try
→ retry creates a new routing Attempt with lineage
```

Permanent:

```text
Response Routed / Delivery Evidenced != Response Applicable
Response Delivered != Source Owner Accepted
Source Owner Received != Response Applied
Response Applied != Source Wait Resolved automatically
```

No exactly-once/at-most-once/at-least-once, universal retry/backoff/dead-letter or workflow/broker guarantee is accepted.

### Offline / Recovery

```text
Offline != Authority Transfer
Local Task Copy != Source Wait Authority
Offline Response Possession != Response Applied
Reconnect != Reconciled
Replay != Retroactive Authorization
Retry != semantic applicability proof
Latest Timestamp != conflict winner
```

## RCP-16 — Human Task Current Closure State

```text
RCP-16 Automation Source-side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-16 S11 / SV-R07 Contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-16 Agent / AG-R01 Contribution
→ NOT YET INTERNALLY DESIGNED

RCP-16 Web / WB-R01 Contribution
→ NOT YET INTERNALLY DESIGNED

RCP-16 Full Cross-component Closure
→ NOT CLOSED
```

Full closure requires later accepted Agent and Web Component Internal Design contributions.

## Human Task / Notification Non-collapse

```text
Human Task Inbox != Notification Center
Task Response != Notification Acknowledgement
Task/source resolution != Notification Read
Notification Delivered != Task Available
```

S11/SV-R07 and S12/SV-R08 remain distinct bounded states/authorities.

## S13 Contribution Boundary

S11 may later contribute only projection-eligible Human Task semantics such as Projection Identity/resource identity, origin/source references, Tenant/Principal applicability, freshness/uncertainty, history/provenance, privacy/redaction and navigation/correlation references.

```text
S13 Discovery Projection != Human Task source Authority
Discovery Result != Human Task Projection SoT
Discovery Index != S11 Actual-state owner
```

S13 internals and RCP-21 remain downstream.

## Foundation / Provider Neutrality

All accepted ns_server internal designs consume Shared Foundation only through accepted Stable Entry → Contract → Module → Provider paths where applicable.

```text
Foundation != Product Authority
Provider != Product Authority
Storage Placement != Actual-state Ownership
Network / Telemetry / Time / Serialization != domain authority
```

## Current Governance Boundary After Batch 7 Acceptance

```text
Remaining accepted ns_server boundaries without Component Internal Design
→ S13

ns_server Component Internal Design Global Closure
→ NOT DECLARED

ns_server Internal Design Exhaustion
→ NOT YET REASSESSED AFTER BATCH 7 ACCEPTANCE

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
→ perform post-Batch-7 ns_server Component Internal Design remaining-pressure / exhaustion / batching assessment
→ determine S13 entry readiness from current Repository authority
→ no downstream producing session is authorized automatically
```
