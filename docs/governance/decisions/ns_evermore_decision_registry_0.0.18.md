# ns_evermore Decision Registry — Current Revision

- Version: `0.0.18`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.17`

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
Accepted Foundation Contracts → 15 / NORMATIVE CONTRACT UPSTREAM
Accepted Foundation Modules → 14 / NORMATIVE MODULE UPSTREAM
Accepted Foundation Provider Families → 10 / NORMATIVE PROVIDER UPSTREAM
Component Internal Design Readiness → SATISFIED
```

## Accepted ns_server Component Internal Design / Batch 1

```text
NGRP-001 Component Internal Design / ns_server / Batch 1
→ GLOBAL_ACCEPTED / NORMATIVE INTERNAL DESIGN UPSTREAM

Accepted Boundaries
→ S1 / S2 / S3 / S4 / S8 / S9

Accepted Internal Modules
→ 14

Accepted DAD
→ CID-SV-B1-DAD-001..013

RCP-01 Governance Context
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-02 Admission Evidence
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-19 Desired / Applied Config
→ CLOSED AT DESIGN-SEMANTIC LEVEL

S8 Artifact Identity / Acceptance Evidence
→ CLOSED AT DESIGN-SEMANTIC LEVEL
```

Batch-1 persistence clarification remains normative:

```text
semantic state / decision-evidence persistence custody
!= new Project-level Source-of-Truth topology
!= storage/database placement becoming Authority / SoT
```

## Accepted ns_server Component Internal Design / Batch 2

```text
NGRP-001 Component Internal Design / ns_server / Batch 2
→ GLOBAL_ACCEPTED / NORMATIVE INTERNAL DESIGN UPSTREAM

Accepted Boundary
→ S6 Automation Definition, Trigger & Composition Lifecycle

Accepted Internal Module Count
→ 9

Accepted DAD
→ CID-SV-B2-DAD-001..014

Recognized Owner MDE
→ CID-SV-B2-MDE-001
```

### CID-SV-B2-MDE-001

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
!= generic Automation loop / iteration semantics prohibited
!= repeated non-recursive callee invocation prohibited
!= retry / re-entry prohibited
```

Accepted Batch-2 stable contract closure:

```text
RCP-13 Automation Continuation
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-14 Event Trigger Input / Evaluation
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-15 Automation Composition
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-16 Automation Source-side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-16 Full Cross-domain Closure
→ NOT CLAIMED / REMAINS DOWNSTREAM

RCP-17 Automation-side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-17 Full Cross-domain Closure
→ NOT CLAIMED / REMAINS DOWNSTREAM
```

## Accepted ns_server Component Internal Design / Batch 3

```text
NGRP-001 Component Internal Design / ns_server / Batch 3
→ GLOBAL_ACCEPTED / NORMATIVE INTERNAL DESIGN UPSTREAM

Accepted Scope
→ COMPONENT_INTERNAL_DESIGN_ONLY
  / NS_SERVER
  / BATCH_3
  / BUSINESS_APPLICATION_DOMAIN_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS

Accepted Boundary
→ S5 Business Application Definition Lifecycle

Accepted Runtime Role Input
→ SV-R01 Business Application Runtime Participant

Accepted Internal Module Count
→ 6

Accepted DAD
→ CID-SV-B3-DAD-001..012
```

Global Acceptance evidence:
`docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_3_global_acceptance_0.0.1.md`

Accepted Batch-3 internal architecture responsibilities:

1. Business Application Definition & Canonical Revision Governance
2. Authoring Intake & Semantic Interoperability
3. Definition Validation & Semantic Certification Evidence
4. Cross-domain Capability Reference & Dependency Governance
5. Business Application Operation & Semantic Result
6. Business Application Trial Semantics & Runtime Evidence

`BA01..BA06` are producing-document navigation labels only and are not Django App/package/class/service/process/worker/table/schema/deployment identities.

### Accepted Business Application Authority / SoT topology

```text
Business Application Definition / Platform Semantic Authority
→ ns_server

Business Application Canonical Definition SoT
→ ns_server

Semantic Authority
!= Canonical Definition SoT

Formal Artifact Acceptance Authority
→ S8 / ns_server

Formal Execution Admission Authority
→ S8 / ns_server
```

```text
Authority Transfer → 0
SoT Transfer → 0
Actual-state Ownership Transfer → 0
```

### Accepted Definition / Authoring semantics

```text
Business Application Definition Identity
→ stable representation-neutral semantic subject

Canonical Definition Revision
→ stable governed semantic snapshot

Semantic Modification
→ new canonical revision

Historical Revision
→ not mutated in place

Mutable Authoring Candidate
!= Canonical Definition Revision
```

```text
Complete Source / SDK Authoring → REQUIRED
Complete ns_web Visual Builder Authoring → REQUIRED
Bidirectional Semantic Interoperability → REQUIRED
Silent Semantic Loss / Silent Semantic Destruction → PROHIBITED
Lossless Representation Round-trip → NOT REQUIRED
```

No physical ID format, DSL, AST, IR, canonical source format, visual schema, converter, generator or SDK API is accepted.

### Accepted lifecycle non-collapse

```text
Authoring Candidate
!= Validation
!= Canonical Definition Revision
!= Domain Semantic Certification Evidence
!= Candidate Artifact
!= Formal Artifact Acceptance
!= Formal Execution Admission
!= Runtime Operation
```

### Accepted cross-domain non-transfer

```text
Business Application consumes Automation
!= Automation Authority / Definition SoT / Runtime Actual-state transfer

Business Application invokes Agent
!= Agent Authority / Definition SoT / Runtime Actual-state transfer

Business Application consumes Data / Knowledge
!= Data/Knowledge Authority transfer
!= factual SoT transfer
!= S7 Native Definition SoT decision
```

`S7 Native Data / Knowledge / ETL Definition SoT` remains explicitly undecided by `Z2-MDE-017` and MUST NOT be inferred from semantic authority or ns_server placement.

### Accepted SV-R01 Actual-state refinement

```text
Business Application production semantic Operation/result/history
→ S5 / SV-R01

Business Application Trial semantic state/result
→ S5 / SV-R01
```

External Admission, coordination, Automation, Data/ETL, S10 background, Node attempt/effect, Agent runtime, Human Task, Notification, Discovery and customer factual partitions retain their accepted final owners.

### Accepted stable-contract closure

```text
RCP-17 Business Application side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-17 Full Cross-domain Closure
→ NOT CLAIMED / REMAINS DOWNSTREAM

RCP-23 S5 / SV-R01 Contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-23 Full Server-native Runtime Evidence Closure
→ NOT CLAIMED / REMAINS DOWNSTREAM
→ requires S7 / SV-R03 + S10 / SV-R06
```

### Accepted internal dependency semantics

Batch-1 dependency taxonomy remains controlling:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Accepted Batch-3 hard SDD graph:

```text
BA02 → BA01, BA04
BA03 → BA01, BA04
BA04 → BA01
BA05 → BA01, BA04
BA06 → BA01, BA04, BA05
```

```text
Hard Internal SDD Graph → ACYCLIC
Unresolved Hard Semantic-definition Cycle → 0
Authority Cycle → NONE
```

### Historical / persistence / offline interpretation

```text
semantic persistence custody
!= new Project-level SoT

Persistence Placement != Authority
Database / Cache != SoT automatically
Stored external evidence != source ownership transfer

Current Definition != historical Operation/Trial revision automatically
Reconnect != Reconciled
Sync != Authority Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
Offline != Local Authority / Definition-SoT transfer
```

No material global fail-open/fail-closed or conflict-winner rule is accepted.

## Current Governance Boundary After Batch 3 Acceptance

```text
ns_server Component Internal Design / Batch 1 → GLOBAL_ACCEPTED
ns_server Component Internal Design / Batch 2 → GLOBAL_ACCEPTED
ns_server Component Internal Design / Batch 3 → GLOBAL_ACCEPTED

Remaining accepted ns_server boundaries not yet internally designed
→ S7 / S10 / S11 / S12 / S13

ns_server Component Internal Design Global Closure
→ NOT DECLARED

ns_server Internal Design Exhaustion
→ NOT YET REASSESSED AFTER BATCH 3 ACCEPTANCE

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

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
