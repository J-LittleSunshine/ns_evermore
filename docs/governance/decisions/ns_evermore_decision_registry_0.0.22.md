# ns_evermore Decision Registry — Current Revision

- Version: `0.0.22`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.21`

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

Batch 6 → GLOBAL_ACCEPTED
Boundary → S12 Governed Notification & External Delivery Lifecycle
Runtime Role Input → SV-R08 Notification Lifecycle & External Delivery Participant
Accepted Internal Module Count → 8
Accepted DAD → CID-SV-B6-DAD-001..019
RCP-18 Notification / Delivery → CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL
```

Batch-6 Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_6_global_acceptance_0.0.1.md`

Full RCP-16 and full RCP-17 remain downstream where not explicitly globally accepted. RCP-23 and RCP-18 are fully closed at the current design-semantic level.

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

No storage, database, schema, ETL engine, connector, source format, visual schema, provider, runtime topology or implementation layout is selected by this MDE.

### Governed Notification / External Delivery Owner Capability Decision

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

Permanent:

```text
Notification != Human Task
Notification != Source Fact
Notification != Runtime Current State
Provider != Product Authority
Delivery Success != User Observation
Read != Resolution
Acknowledgement != Policy Approval
```

## Accepted S7 Internal Architecture Baseline

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

Permanent:

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

```text
BG01 Background Operation Identity & Initiation Context
BG02 Time-trigger & Continuous-availability Semantics
BG03 Attempt Lifecycle & Lineage Custody
BG04 Progress, Outcome & Server-local Source-fact Custody
BG05 Intervention & Retry/Re-entry Applicability
BG06 Recovery, Reconciliation & Historical Qualification
BG07 Runtime Governance & Applied Configuration Binding
```

```text
SV-R06 final Actual-state/source-fact owner
→ server-local Attempt
→ server-local progress
→ server-local outcome
→ genuine server-local source facts
```

Permanent:

```text
Operation Identity != Attempt Identity
Attempt != Progress != Outcome
Retry != historical Attempt mutation
Reconnect != Reconciled
Recovery != Authority Transfer
Latest Timestamp != Canonical Winner
Desired != Distributed != Applied != Observed
```

No universal scheduler/worker/retry/cancellation/rollback/conflict-winner policy is accepted.

## RCP-23 — Full Server-native Runtime Evidence Closure

```text
S5 / SV-R01 → Business Application semantic Runtime Evidence
S7 / SV-R03 → Data / Knowledge / ETL semantic Runtime Evidence
S10 / SV-R06 → Server-local Background Runtime Evidence

RCP-23 Full Server-native Runtime Evidence
→ CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL
```

Permanent:

```text
SV-R01 != SV-R03 != SV-R06
Common Contract != Common Authority != Common Actual-state Owner
Universal Server Runtime Actual-state SoT → NOT CREATED
```

## Accepted S12 Internal Architecture Baseline

Accepted architecture-semantic responsibilities:

```text
NT01 Notification Creation Intent & Source Correlation Intake
NT02 Audience Applicability, Authorization & Disclosure Governance
NT03 Notification Identity, Existence & Lifecycle History Custody
NT04 Delivery Intent & Channel Applicability Governance
NT05 Delivery Attempt Lifecycle & Lineage Custody
NT06 Provider Evidence Interpretation & Channel-neutral Normalization
NT07 Awareness Interaction Evidence & Notification History Interpretation
NT08 Recovery, Reconciliation & Historical Qualification
```

Accepted ownership:

```text
Underlying Source Fact / Source Condition → originating source owner
NT03 / SV-R08 → Notification existence / lifecycle / history
NT05 / SV-R08 → Delivery Attempt Actual-state
NT06 → provider evidence interpretation only
External Provider → evidence source only / NOT Product Authority
WB-R01 → awareness projection / interaction evidence only where applicable
```

Accepted identity / lifecycle non-collapse:

```text
Notification Identity != Source Fact Identity automatically
Notification Identity != Creation Intent Identity
Notification Identity != Delivery Intent Identity
Notification Identity != Delivery Attempt Identity
Notification Identity != Provider Request / Message ID
Notification Identity != Database PK automatically

Notification → 0..N Delivery Intents
Delivery Intent → 0..N Delivery Attempts
Delivery Attempt → one bounded semantic delivery try
```

Retry / re-delivery:

```text
retry → new Delivery Attempt under same Delivery Intent + retry-of lineage
re-delivery with renewed/changed objective/channel/target applicability
→ new correlated Delivery Intent + re-delivery-of lineage where applicable
```

Permanent:

```text
Source Event != Notification automatically
Notification Created != External Delivery Requested
External Delivery Requested != Delivery Attempt Created
Delivery Attempt Created != Provider Accepted
Provider Accepted != Delivery Succeeded automatically
Delivery Succeeded != Recipient Observed
Delivery Failed != Underlying Operation Failed
External Channel Unreachable != Notification Lost
Projected != Observed
Observed != Read automatically
Read != Acknowledged automatically
Acknowledged != Resolved
Acknowledged != Policy Approved
Human Task Inbox != Notification Center
```

No universal delivery guarantee, retry/backoff/fallback policy, provider-specific semantic model, public SaaS correctness dependency or concrete provider/API/queue/database/process topology is accepted.

## RCP-18 — Notification / Delivery Closure

```text
RCP-18 Notification / Delivery
→ CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL
```

Stable obligations preserve source ownership/correlation, Notification identity/history, Tenant/audience/privacy, creation lifecycle, Delivery Intent/Attempt identity and lineage, provider evidence interpretation, channel neutrality, awareness non-collapse, Secret Reference separation, offline/failure/recovery semantics, compatibility/migration/conformance and producer/consumer/source-owner obligations.

Permanent:

```text
RCP-18 != Universal Source Fact Authority
RCP-18 != Provider Authority
RCP-18 != Human Task Authority
RCP-18 != wire/schema/provider lock-in
```

## Foundation / Provider Neutrality

All accepted ns_server internal designs consume Shared Foundation only through accepted Stable Entry → Contract → Module → Provider paths where applicable.

```text
Foundation != Product Authority
Provider != Product Authority
Storage Placement != Actual-state Ownership
Telemetry / Network Client / Time / Serialization != domain authority
```

No new Foundation capability or Provider family is created by Batch 6.

## Current Governance Boundary After Batch 6 Acceptance

```text
Remaining accepted ns_server boundaries without Component Internal Design
→ S11 / S13

ns_server Component Internal Design Global Closure
→ NOT DECLARED

ns_server Internal Design Exhaustion
→ NOT YET REASSESSED AFTER BATCH 6 ACCEPTANCE

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
→ perform post-Batch-6 ns_server Component Internal Design remaining-pressure / exhaustion / batching assessment
→ no downstream producing session is authorized automatically
```
