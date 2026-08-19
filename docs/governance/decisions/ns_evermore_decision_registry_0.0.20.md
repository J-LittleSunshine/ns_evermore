# ns_evermore Decision Registry — Current Revision

- Version: `0.0.20`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.19`

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
Accepted DAD → CID-SV-B3-DAD-001..012
RCP-17 Business Application side → CLOSED AT CURRENT DESIGN LEVEL
RCP-23 S5 / SV-R01 contribution → CLOSED AT CURRENT DESIGN LEVEL

Batch 4 → GLOBAL_ACCEPTED
Boundary → S7 Enterprise Data / Knowledge / Foundational ETL Governance
Runtime Role Input → SV-R03 Data / Knowledge / ETL Runtime Participant
Accepted DAD → CID-SV-B4-DAD-001..015
RCP-17 S7 Data / Knowledge / ETL side → CLOSED AT CURRENT DESIGN LEVEL
RCP-23 S7 / SV-R03 contribution → CLOSED AT CURRENT DESIGN LEVEL
```

Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_4_global_acceptance_0.0.1.md`

Full RCP-16 / RCP-17 / RCP-23 closure remains downstream where not explicitly globally accepted. Full RCP-23 still requires the S10 / SV-R06 contribution.

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

1. Native S7 Definition & Canonical Revision Governance
2. Authoring Intake & Semantic Interoperability
3. Definition Validation & Semantic Certification Evidence
4. Factual Partition & Source Authority Binding Governance
5. External Source Schema Reference & Mapping Governance
6. ETL Definition & Transformation / Derivation Governance
7. Knowledge Definition & Derived Knowledge Governance
8. Query & Aggregation Semantic Governance
9. S7 Runtime Operation & Semantic Result
10. S7 Trial Semantics & Runtime Evidence

`DK01..DK10` are document-local labels only and are not Django Apps, packages, classes, services, processes, workers, tables, schemas, databases or deployment units.

### Definition / Factual Authority Separation

```text
Native S7 Definition Identity
→ stable representation-neutral semantic subject

Semantic Modification
→ new Canonical Definition Revision

Historical Canonical Revision
→ not silently mutated in place

Mutable Source/Visual Authoring Candidate
!= Canonical Native S7 Definition Revision

External Source Schema
!= Native S7 Definition automatically

Mapping Definition
!= Source Fact

ETL Definition
!= Runtime Operation
!= ETL Output Fact

Derived / Aggregated Fact
!= Upstream Source Fact
```

No physical identity format, DSL, AST/IR, canonical source format, visual schema or query language is accepted.

### Dual Authoring

```text
Complete Source / SDK Authoring → REQUIRED
Complete ns_web Visual Authoring → REQUIRED
Both → same governed S7 semantic domain
Bidirectional Semantic Interoperability → REQUIRED
Silent Semantic Loss / Destruction → PROHIBITED
Lossless Representation Round-trip → NOT REQUIRED
```

### Knowledge / Retrieval Separation

```text
Native Knowledge Definition
!= factual/derived Knowledge assertion automatically
!= Index
!= Vector Representation
!= Embedding
!= Retrieval Result
!= RAG Consumption

Index / Vector / Embedding / Retrieval
→ do not become Canonical Knowledge or S7 Authority automatically
```

### Query / Aggregation Boundary

```text
One-off Query/Aggregation Intent
!= Canonical Native Definition automatically

Query Result
!= Source Fact automatically

Aggregation Result
!= Upstream Fact

Dashboard / Visualization
!= Data SoT
```

No universal query language or BI/semantic-layer implementation is accepted.

## Accepted SV-R03 Actual-state Partition

```text
S7 production semantic Runtime Operation/state/result/history
→ S7 / SV-R03

S7 Trial semantic state/result/history
→ S7 / SV-R03
```

S7 does not absorb:

```text
Formal Admission → S8 / SV-R04
Scheduling / Routing / Dispatch → RT-R02
Cross-component continuation-stage facts → RT-R03
Business Application runtime → S5 / SV-R01
Automation runtime → S6 / SV-R02
Server-local generic background runtime → S10 / SV-R06 later design
Node Attempt / Effect → ND-R02 / ND-R03
Agent Runtime → applicable ns_agent role
Human Task Aggregation → S11 / SV-R07
Notification Lifecycle → S12 / SV-R08
Discovery Projection → S13 / SV-R09
External factual assertions → declared final factual SoT
```

Exactly one final owner per same bounded runtime assertion remains normative.

## Accepted S7 Stable-contract Closure

```text
RCP-17 S7 Data / Knowledge / ETL side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-17 Full Cross-domain Closure
→ NOT CLAIMED / REMAINS DOWNSTREAM

RCP-23 S7 / SV-R03 Contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-23 S5 / SV-R01 Contribution
→ PRESERVED

RCP-23 Full Server-native Runtime Evidence Closure
→ NOT CLAIMED
→ S10 / SV-R06 remains required
```

## Accepted Historical / Offline Interpretation

```text
Current Definition != Historical Runtime Definition automatically
Current Mapping != Historical Mapping automatically
Current External Schema != Historical Schema Evidence automatically
Current SoT Binding != Historical Binding automatically
Current Source Fact != Historical Source Evidence automatically
Current Index/Embedding != Historical Knowledge Evidence automatically

Offline != Local Authority Transfer
Offline != Local Definition SoT Transfer
Local Replica != Factual SoT automatically
Reconnect != Reconciled
Sync != Authority Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
ETL Arrival Order != Conflict Winner
```

No global fail-open/fail-closed, latest-wins, local-wins, central-wins or external-wins policy is accepted.

## Accepted Dependency / Foundation / Discovery Boundary

Accepted hard SDD graph is acyclic. Foundation consumption remains authority-neutral through the accepted Stable Entry → Contract → Module → Provider path where applicable. Deferred Foundation candidates `Cryptographic / Evidence-verification Helpers` and `Database Utility Primitives` remain deferred.

S7 may supply S7-owned resource identity/revision/provenance inputs to later S13; S13 internal design is not part of Batch 4 and Discovery Projection does not become S7 Definition SoT or factual/resource SoT.

## Current Governance Boundary After Batch 4 Acceptance

```text
Remaining accepted ns_server boundaries without Component Internal Design
→ S10 / S11 / S12 / S13

ns_server Component Internal Design Global Closure
→ NOT DECLARED

ns_server Internal Design Exhaustion
→ NOT YET REASSESSED AFTER BATCH 4 ACCEPTANCE

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
→ perform ns_server Component Internal Design remaining-pressure / exhaustion / batching assessment
→ no downstream producing session is authorized automatically
```
