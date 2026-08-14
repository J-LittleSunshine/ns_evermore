# ns_evermore Decision Registry — Current Revision

- Version: `0.0.17`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.16`

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

Authorization Scope
→ COMPONENT_INTERNAL_DESIGN_ONLY
  / NS_SERVER
  / BATCH_2
  / AUTOMATION_DOMAIN_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS

Accepted Boundary
→ S6 Automation Definition, Trigger & Composition Lifecycle

Accepted Internal Module Count
→ 9

Accepted DAD
→ CID-SV-B2-DAD-001..014

Recognized Owner MDE
→ CID-SV-B2-MDE-001
```

Global Acceptance evidence:
`docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_2_global_acceptance_0.0.1.md`

Accepted Batch-2 internal architecture responsibilities:

1. Automation Definition & Canonical Revision Governance
2. Authoring Intake & Semantic Interoperability
3. Definition Validation & Semantic Certification Evidence
4. Initiation & Trigger Definition Governance
5. Event Provenance & Trigger Evaluation
6. Automation Composition & Revision Binding Governance
7. Automation Operation & Semantic Continuation
8. Automation HITL Wait & Response Applicability
9. Automation Trial Semantics & Runtime Evidence

`AU01..AU09` are producing-document navigation labels only and are not physical package/class/service/process/worker/table/deployment identities.

## CID-SV-B2-MDE-001 — Automation Recursive Invocation

```text
Decision Authority
→ PROJECT OWNER / MDE

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

The decision selects no DAG/graph representation, workflow engine, recursion-detection algorithm, call-stack model or state-machine implementation.

## Accepted Automation Authority / SoT / Actual-state Topology

```text
Automation Definition / Workflow Semantic Authority
→ ns_server

Automation Canonical Definition SoT
→ ns_server

Semantic Authority
!= Canonical Definition SoT

Formal Artifact Acceptance Authority
→ S8 / ns_server

Formal Execution Admission Authority
→ S8 / ns_server

Trigger Evaluation Actual-state
→ S6 / SV-R02

Automation Operation / Continuation Actual-state
→ S6 / SV-R02

Automation HITL wait / response applicability / semantic resume
→ S6 / SV-R02

Automation Trial semantic state / result
→ S6 / SV-R02

Scheduling / Routing / Dispatch
→ ns_runtime / R2

Node Attempt
→ N2

Node Protected Effect
→ N3

Human Task Aggregation
→ S11

Human response submission occurrence
→ W3 later design

Agent Runtime
→ ns_agent / A2
```

```text
Authority Transfer → 0
SoT Transfer → 0
Actual-state Ownership Transfer → 0
```

## Accepted Batch-2 Stable Contract Closure

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

RCP-15 accepted interpretation includes stable exact historical callee-revision resolution and prohibition of silent `latest` rebinding. No version-range syntax, lockfile format or universal future binding-mode commitment is established.

## Permanent Automation Non-collapse Rules

```text
Automation Definition
!= Validation
!= Domain Semantic Certification
!= Candidate Artifact
!= Formal Artifact Acceptance
!= Formal Execution Admission
!= Scheduling / Dispatch
!= Runtime Attempt
!= Protected Effect

Event Occurred != Trigger Matched
Trigger Matched != Execution Admitted
Event Producer != Automation / Policy / Admission Authority
Replay != Retroactive Admission

Caller Automation != Callee Automation
Composition != Artifact Acceptance bypass
Composition != Execution Admission bypass

Human Response Submitted != Response Applicable != Response Applied automatically
Human Response != Policy Permit / Artifact Acceptance / Execution Admission

Definition Valid != Trial Successful
Trial Successful != Artifact Accepted / Production Admitted
Trial Execution != Production Execution
Dry-run != No Effect automatically
```

## Source / Visual / Agent Authoring Preservation

```text
Complete Source / SDK Authoring → REQUIRED
Complete ns_web Visual Authoring → REQUIRED
Bidirectional Semantic Interoperability → REQUIRED
Silent Semantic Loss → PROHIBITED
Lossless Representation Round-trip → NOT REQUIRED
Agent Dynamic Candidate Automation Authoring → REQUIRED under normal S6 governance
```

Source/visual/Agent candidate state does not become Automation Authority or Canonical Definition SoT.

## Internal Dependency Semantics

Batch-1 taxonomy remains controlling:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only SDD participates in recursive internal semantic-definition cycle analysis.

```text
Batch-2 Hard Internal SDD Graph → ACYCLIC
Unresolved Hard Internal Semantic-definition Cycle → 0
Canonical Automation Composition Dependency → ACYCLIC by CID-SV-B2-MDE-001
```

## Current Governance Boundary

```text
ns_server Component Internal Design / Batch 1 → GLOBAL_ACCEPTED
ns_server Component Internal Design / Batch 2 → GLOBAL_ACCEPTED

ns_server Component Internal Design Global Closure → NOT DECLARED
ns_server Internal Design Exhaustion → NOT YET REASSESSED AFTER BATCH 2 ACCEPTANCE

Remaining accepted ns_server boundaries not yet internally designed
→ S5 / S7 / S10 / S11 / S12 / S13

Open MDE → 0
Unpersisted Owner Decision → 0

Another ns_server Batch → NOT AUTHORIZED
Other Product Component Internal Design → NOT AUTHORIZED
System-level SDK Detailed Design → NOT AUTHORIZED
Design-to-Implementation Readiness → NOT AUTHORIZED
Implementation Planning / IWP / Coding → NOT AUTHORIZED
```
