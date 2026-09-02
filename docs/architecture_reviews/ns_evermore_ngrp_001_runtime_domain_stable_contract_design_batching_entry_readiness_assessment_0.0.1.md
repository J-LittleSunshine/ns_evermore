# NGRP-001 — Runtime / Domain Stable Contract Design / RCP-01..24 Batching & Entry-readiness Assessment

- Authority: `GLOBAL ARCHITECTURE COORDINATOR`
- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Input Epoch: `GAC-EPOCH-0111`
- Assessment Type: `RCP_01_24_CONTRACT_SEMANTIC_DEPENDENCY_BATCHING_ENTRY_READINESS`

## Purpose

Derive a lawful bounded Batch sequence for the 24 accepted Runtime / Domain Stable Contract Pressure subjects, using semantic-definition dependency and accepted authority topology rather than RCP numbering or runtime message flow, and determine whether the first Contract Design Batch is ready for a separate producing authorization.

This assessment does not perform Contract Design, does not declare Full Cross-component Closure of any RCP, does not perform System-level SDK Detailed Design, and does not authorize producing.

---

# 1. Fresh Repository Recovery

```text
Assessment Entry HEAD
→ 8c15044b7a36f5318573012445c3235368551535

Current Global State
→ GAC-EPOCH-0111

State Verified Through HEAD
→ 5cacf780ed674200c3b92c75ea89ea524369445d

State-to-Entry Delta
→ exactly 1 commit
→ Global Architecture State stable-contract-readiness seal only
→ EXPECTED_GOVERNANCE

Decision Registry
→ 0.0.40 / GLOBAL_CURRENT / NORMATIVE

Current Authorized Phase
→ NONE

Authorization Scope
→ NONE

Runtime / Domain Stable Contract Design Readiness
→ SATISFIED

System-level SDK Detailed Design Readiness
→ NOT_SATISFIED

RCP Count
→ 24 / RCP-01..RCP-24

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Semantic Gap for Contract Design entry
→ NONE

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE
```

Recovery Gate: `PASS`.

---

# 2. Contract Dependency Taxonomy

The batching model distinguishes semantic-definition prerequisites from runtime/evidence relationships.

```text
CSDD
→ CONTRACT_SEMANTIC_DEFINITION_DEPENDENCY

CACD
→ CONTRACT_APPLICATION_CONTEXT_DEPENDENCY

CEL
→ CONTRACT_EVIDENCE_LINKAGE

CHPL
→ CONTRACT_HISTORICAL_PROVENANCE_LINKAGE

CXAR
→ CROSS_AUTHORITY_REFERENCE
```

Only `CSDD` participates in Contract semantic-definition cycle analysis and determines mandatory cross-Batch ordering.

Notation:

```text
RCP-A → RCP-B
=
RCP-A's Contract semantic definition depends on RCP-B's Contract semantic definition.
```

The arrow does **not** mean:

```text
runtime control flow
request direction
response direction
evidence-return direction
source-to-consumer message flow
Authority direction
SoT direction
Actual-state ownership direction
historical-event order
```

Runtime feedback, re-observation, downstream outcome evidence and historical linkage are classified as `CACD/CEL/CHPL/CXAR` unless the semantic subject itself cannot be defined without another Contract.

---

# 3. RCP Inventory / Named Later Authority

The accepted Runtime Responsibility Architecture defines exactly 24 pressure subjects and a named Later Authority for each:

| RCP | Subject | Named Later Authority |
|---|---|---|
| RCP-01 | Governance Context | Contract Design |
| RCP-02 | Admission Evidence | Runtime Contract Design |
| RCP-03 | Presence | Runtime Contract Design |
| RCP-04 | Node Readiness | Runtime Contract Design |
| RCP-05 | Dispatch Evidence | Runtime Contract Design |
| RCP-06 | Continuation / Intervention | Runtime Contract Design |
| RCP-07 | Node Attempt | Runtime Contract Design |
| RCP-08 | Node Effect Evidence | Runtime Contract Design |
| RCP-09 | Agent Runtime | Agent Runtime Contract Design |
| RCP-10 | Provider Mediation | Agent Contract Design |
| RCP-11 | Multi-Agent Composition | Agent Runtime Contract Design |
| RCP-12 | Agent Delegation | Cross-component Contract Design |
| RCP-13 | Automation Continuation | Automation Runtime Contract Design |
| RCP-14 | Event Trigger Input / Evaluation | Automation Contract Design |
| RCP-15 | Automation Composition | Automation Runtime Contract Design |
| RCP-16 | Human Task | HITL Contract Design |
| RCP-17 | Trial | Trial Contract Design |
| RCP-18 | Notification / Delivery | Notification Contract Design |
| RCP-19 | Desired / Applied Config | Config Contract Design |
| RCP-20 | Recovery / Reconciliation | Recovery Contract Design |
| RCP-21 | Discovery | Discovery Contract Design |
| RCP-22 | Diagnostics / Provenance | Diagnostics Contract Design |
| RCP-23 | Server-native Runtime Evidence | Server Runtime Contract Design |
| RCP-24 | Human / SDK Intent | Cross-surface Contract Design |

The batching below groups these named Contract authorities into bounded producing sessions without collapsing their individual subject authority.

---

# 4. Foundational Dependency Findings

## 4.1 Governance Context is foundational

`RCP-01` supplies stable Tenant/Organization/Principal/Policy/Trust/governed-context propagation semantics consumed throughout Admission, runtime coordination, configuration, Web intent, HITL, Notification, Discovery, diagnostics and other RCPs.

Therefore many Contracts consume RCP-01 either by `CSDD` where governed context is intrinsic to the Contract subject, or by `CACD/CXAR` where the subject can be defined independently but must carry applicable governance references.

No later Contract may become a second Governance Authority.

## 4.2 Desired / Applied Configuration precedes Node Readiness

Accepted Node internal design establishes:

```text
N1 Applied Configuration Actual-state
→ consumes RCP-19 Desired revision/reference

Execution-mode Readiness
→ depends on Applied Configuration semantics

Bounded Node Readiness / RCP-04
→ depends on capability + Applied Configuration + execution-mode readiness
```

Therefore:

```text
RCP-04 → RCP-19
→ CSDD
```

Presence/reachability remains orthogonal:

```text
Reachable != Ready
```

So RCP-04 does not acquire a hard semantic-definition dependency on RCP-03 merely because runtime routing later consumes both.

## 4.3 Generic Human / SDK Intent is foundational cross-surface input

Accepted W1 and W2 semantics require RCP-24 for Web-origin governed command/authoring/change-intent submission semantics:

```text
Intent / Submission
!= applicability
!= authoritative outcome
```

RT-R03 later consumes RCP-24 receiving/correlation/applicability expectations without becoming source intent Authority.

Therefore RCP-24 belongs in the first Contract foundation Batch rather than a final SDK-only Batch.

## 4.4 Admission / Presence / Readiness precede Dispatch

Accepted Runtime R2 semantics consume:

```text
RCP-02 Admission Evidence
RCP-03 Presence / Reachability
RCP-04 Node Readiness
```

when qualifying routing candidates and dispatch.

Thus:

```text
RCP-05 → RCP-02
RCP-05 → RCP-03
RCP-05 → RCP-04
```

are Contract-level semantic prerequisites for full Dispatch Contract closure.

## 4.5 Attempt precedes Effect

Accepted Node semantics permanently preserve:

```text
Admission != Dispatch != Attempt != Effect
Dispatch != Attempt
Attempt != Protected Effect
```

Node Effect Evidence explicitly correlates to the Attempt subject.

Therefore:

```text
RCP-07 → RCP-02, RCP-05
RCP-08 → RCP-07
```

with Node readiness/config correlation available from earlier Contracts where materially required.

---

# 5. Agent Runtime / Provider Mediation Dependency Findings

Accepted Agent design separates:

```text
Agent Operation
!= Agent Runtime Attempt
!= Harness Invocation
!= Provider Mediation Interaction
```

`RCP-09` is the AG-R01 Agent Runtime owner/source-side Contract. `RCP-10` is the AG-R02 Provider Mediation bounded-observation Contract.

Provider mediation consumes/correlates to the Agent runtime invocation/operation context supplied by A2. Provider result/availability evidence returns to Agent runtime through evidence linkage and does not become Agent semantic Authority.

Contract semantic direction:

```text
RCP-10 → RCP-09
→ CSDD for the correlated Agent-runtime invocation subject
```

The runtime evidence returned from RCP-10 to RCP-09 is `CEL`, not reverse semantic-definition authority.

RCP-09 also consumes already-established governance/admission/configuration context as applicable but remains Agent-runtime source authority for its own facts.

---

# 6. Automation / Continuation / Composition Dependency Findings

Accepted S6 internal design establishes:

```text
AU06
→ Automation Composition & Revision Binding Governance
→ principal Contract responsibility for RCP-15

AU07
→ Automation Operation & Semantic Continuation
→ principal Contract responsibility for RCP-13

Internal hard SDD
→ AU07 → AU01, AU06
```

Therefore the stable Automation Continuation subject requires the Composition binding semantics where composition is involved:

```text
RCP-13 → RCP-15
→ CSDD
```

Accepted RT-R03 design states:

```text
Continuation Coordination != Source Semantic Continuation Authority
```

RT-R03 continuation coordination begins only after the applicable source semantic owner supplies continuation intent/requirement/evidence. For Automation this source is S6/SV-R02 / RCP-13.

Therefore:

```text
RCP-06 → RCP-13
→ CSDD
```

RCP-06 may consume RCP-07/08/09 owner evidence and RCP-24 governed intent context, but evidence-return/owner-outcome relationships remain `CEL/CACD`, not reverse SDD.

RCP-14 Event Trigger Input/Evaluation is an Automation source Contract tied to accepted trigger identity/source/evaluation semantics. It does not require Dispatch/Attempt/Effect or RCP-06 to define its own source semantic subject; those later runtime consequences are evidence/application relationships.

---

# 7. Multi-Agent / Delegation Dependency Findings

Accepted Agent Batch-2 design establishes:

```text
RCP-11
→ A5 / AG-R03 Multi-Agent Composition
→ consumes accepted A2 Agent Runtime semantics

RCP-12
→ A6 / AG-R04 Cross-domain Delegation
→ consumes accepted RCP-02/03/04/05/06/07/08/09/10/13/15/19 as applicable
```

Thus:

```text
RCP-11 → RCP-09
→ CSDD for participant Agent Operation/Runtime subject semantics
```

RCP-12 requires already-stable delegation coordination and target/runtime evidence semantics:

```text
RCP-12 → RCP-06
RCP-12 → RCP-09
RCP-12 → RCP-10
RCP-12 → RCP-13
RCP-12 → RCP-15
```

and consumes earlier Admission/Presence/Readiness/Dispatch/Attempt/Effect/Config Contracts.

RCP-12 does not create a reverse dependency that makes RCP-06 or RCP-13 source-defined by Agent delegation. Delegation results/attempt/effect evidence are `CEL/CACD`.

RCP-11 need not be a hard semantic prerequisite of all RCP-12 delegation because cross-domain delegation exists outside native Multi-Agent composition; any A5↔A6 participation correlation is bounded evidence/context rather than universal definition dependency.

---

# 8. Recovery / Reconciliation Dependency Findings

Accepted RT-R04 recovery design explicitly consumes prior coordination/evidence Contracts:

```text
RCP-03 Presence
RCP-05 Dispatch Evidence
RCP-06 Continuation / Intervention
RCP-04 Node Readiness
RCP-07 Node Attempt
RCP-08 Node Effect Evidence
RCP-09 Agent Runtime
RCP-23 Server-native Runtime Evidence
RCP-19 Desired / Applied Config
```

where materially applicable.

RT-R04 preserves:

```text
Recovery != SoT Transfer
Re-observation != Canonicalization
Conflict Detected != Winner Selected
```

Therefore RCP-20 belongs after foundational, execution and coordination Contracts.

Runtime/source re-observation evidence returning from source owners is `CEL/CXAR`; it does not generate reverse Contract-definition dependencies.

---

# 9. HITL / Trial / Notification / Discovery Findings

## RCP-16 Human Task

Full HITL Contract closure requires already-established:

```text
RCP-09 Agent Runtime where Agent HITL participates
RCP-13 Automation Continuation where Automation HITL participates
RCP-06 cross-component continuation/resume coordination
RCP-24 Human/Web submission intent semantics
RCP-01 governance context
```

Source Human-action Requirement/Wait/applicability remains Automation/Agent-owned; Human Response Submission remains Web-owned; S11 remains Task Projection/routing owner.

## RCP-17 Trial

Trial Contract semantics consume already-established governance/admission/runtime/Attempt/Effect/Agent/Automation evidence as applicable while preserving:

```text
Trial != Production
Trial Success != Artifact Acceptance
Trial Success != Formal Execution Admission
```

Trial results do not define the underlying runtime Contracts.

## RCP-18 Notification / Delivery

Notification Contract can be defined from accepted S12/source-owner semantics plus foundational governance/context semantics. Human Task and Notification remain independent:

```text
Human Task != Notification
Task Response != Notification Acknowledgement
```

Any Task/Notification correlation is `CACD/CEL`, not mutual SDD.

## RCP-21 Discovery

Discovery Contract consumes foundational governance/privacy context and accepted S13/original Resource-owner semantics. It preserves:

```text
Result != Resource SoT
No Result != Resource Non-existence
Rank / Score != Authority
```

It has no mandatory SDD on HITL/Notification/Trial/Recovery merely because cross-surface navigation exists.

---

# 10. Diagnostics / Provenance Must Close Last

`RCP-22` aggregates/correlates source-qualified diagnostic/provenance/currentness/history evidence from server/runtime/node/agent/web and recovery/interaction domains while preserving all source owners.

Accepted component designs repeatedly treat RCP-22 as a consumer/producer contribution across nearly every boundary.

A full cross-component Diagnostics/Provenance Contract must therefore consume the final stable identity, correlation, currentness, history and uncertainty semantics of the other RCPs rather than forcing those RCPs to conform to a premature diagnostics envelope.

Thus:

```text
RCP-22 → RCP-01..21, RCP-23, RCP-24 where materially applicable
→ CSDD at the full Contract-closure level
```

This is why RCP-22 is the final Contract Design Batch rather than an early shared schema.

---

# 11. Proposed Contract Design Batch Shape

## Batch 1 — Governance / Intent / Admission / Presence / Configuration / Readiness Foundation

```text
RCP-01 Governance Context
RCP-02 Admission Evidence
RCP-03 Presence
RCP-04 Node Readiness
RCP-19 Desired / Applied Config
RCP-24 Human / SDK Intent
```

Purpose: establish the cross-boundary governed context, generic intent/submission, admission, participant presence/reachability, Desired/Applied configuration and Node readiness semantics required by later execution/coordination Contracts.

Internal hard-SDD graph:

```text
RCP-02 → RCP-01
RCP-03 → RCP-01
RCP-19 → RCP-01
RCP-24 → RCP-01
RCP-04 → RCP-01, RCP-19
```

A valid dependency-first order:

```text
Stage 0 → RCP-01
Stage 1 → RCP-02, RCP-03, RCP-19, RCP-24
Stage 2 → RCP-04
```

Batch-1 hard Contract SDD graph: `ACYCLIC`.

## Batch 2 — Dispatch / Attempt / Effect / Agent Runtime / Provider Mediation / Server Runtime Evidence

```text
RCP-05 Dispatch Evidence
RCP-07 Node Attempt
RCP-08 Node Effect Evidence
RCP-09 Agent Runtime
RCP-10 Provider Mediation
RCP-23 Server-native Runtime Evidence
```

Mandatory prior Batch-1 inputs include governance/admission/presence/readiness/config as applicable.

Internal hard-SDD graph:

```text
RCP-08 → RCP-07
RCP-10 → RCP-09
```

Cross-Batch hard prerequisites:

```text
RCP-05 → RCP-02, RCP-03, RCP-04
RCP-07 → RCP-02, RCP-05
RCP-09 → foundational governed/admission/config context where applicable
RCP-23 → foundational governed/admission context where applicable
```

Batch-2 internal graph: `ACYCLIC`.

## Batch 3 — Continuation / Automation / Multi-Agent / Delegation Composition

```text
RCP-06 Continuation / Intervention
RCP-11 Multi-Agent Composition
RCP-12 Agent Delegation
RCP-13 Automation Continuation
RCP-14 Event Trigger Input / Evaluation
RCP-15 Automation Composition
```

Mandatory prior inputs: Batch 1 + Batch 2.

Internal hard-SDD graph:

```text
RCP-13 → RCP-15
RCP-06 → RCP-13
RCP-12 → RCP-06, RCP-13, RCP-15
```

External prior prerequisite:

```text
RCP-11 → RCP-09
RCP-12 → RCP-09, RCP-10
```

`RCP-14` and `RCP-15` have no required hard dependency on RCP-06.

A valid dependency-first order:

```text
Stage 0 → RCP-11, RCP-14, RCP-15
Stage 1 → RCP-13
Stage 2 → RCP-06
Stage 3 → RCP-12
```

Batch-3 graph: `ACYCLIC`.

## Batch 4 — HITL / Trial / Notification / Recovery / Discovery

```text
RCP-16 Human Task
RCP-17 Trial
RCP-18 Notification / Delivery
RCP-20 Recovery / Reconciliation
RCP-21 Discovery
```

Mandatory prior inputs include the relevant Batch 1-3 Contracts.

There is no required hard SDD among these five Contract subjects merely because their runtime journeys can correlate.

Representative prerequisites:

```text
RCP-16 → RCP-01, RCP-06, RCP-09, RCP-13, RCP-24
RCP-17 → prior governed runtime/Attempt/Effect/Agent/Automation Contracts as applicable
RCP-20 → RCP-03, RCP-04, RCP-05, RCP-06, RCP-07, RCP-08, RCP-09, RCP-19, RCP-23
RCP-18 → RCP-01 plus accepted S12/source-owner semantics
RCP-21 → RCP-01 plus accepted S13/Resource-owner semantics
```

Batch-4 internal hard-SDD graph: `ACYCLIC / no mandatory peer-to-peer hard edge found`.

## Batch 5 — Diagnostics / Provenance Cross-component Closure

```text
RCP-22 Diagnostics / Provenance
```

Mandatory prior input:

```text
all materially applicable stable Contract subjects from Batches 1-4
```

RCP-22 remains source-qualified aggregation/correlation and does not become a universal diagnostic/provenance SoT.

---

# 12. Global Batch Dependency Graph

```text
Batch 1
→ foundational governed context / intent / admission / presence / config / readiness

Batch 2
→ depends on Batch 1

Batch 3
→ depends on Batch 1 + Batch 2

Batch 4
→ depends on Batch 1 + Batch 2 + Batch 3

Batch 5
→ depends on Batch 1 + Batch 2 + Batch 3 + Batch 4
```

```text
Global Contract Batch Hard-SDD Graph
→ ACYCLIC

Authority Cycle
→ NONE_FOUND

SoT Cycle
→ NONE_FOUND

Final Actual-state Ownership Cycle
→ NONE_FOUND
```

The batch sequence is driven by semantic prerequisites, not implementation ordering.

---

# 13. Batch-1 Entry Readiness

Required Batch-1 authoritative upstream is already globally accepted/closed:

```text
Governance / Tenant / IAM / Organization / Policy / Trust
→ ns_server accepted owners

Formal Artifact Acceptance / Execution Admission
→ S8 / SV-R04 accepted

Managed Desired Configuration authority
→ S9 / SV-R05 accepted

Node Applied Configuration / Readiness source semantics
→ N1 / ND-R01 accepted

Runtime Presence source/coordinator semantics
→ R1 / RT-R01 accepted

Web Human/SDK-style governed intent source semantics where applicable
→ W1/W2/W3/W6 accepted Web contributions

Shared Foundation context/freshness/provenance/status/redaction/conformance
→ GLOBAL_CLOSED / COMPLETE
```

```text
Missing Batch-1 RCP identity
→ 0

Missing producer / consumer topology
→ 0

Missing Authority / SoT / final-owner topology
→ 0

Missing accepted component-side semantic contribution
→ 0

Missing Shared Foundation semantic
→ NONE_FOUND

Open MDE blocking Batch-1 entry
→ 0

Unpersisted Owner Decision blocking Batch-1 entry
→ 0

Blocking Semantic Gap
→ NONE

Batch-1 Internal Hard-SDD Cycle
→ NONE

Unexpected Drift
→ NONE
```

Result:

```text
RUNTIME / DOMAIN STABLE CONTRACT DESIGN / BATCH 1 ENTRY READINESS
→ SATISFIED
```

---

# 14. Later Batch Readiness

```text
Batch 2 Entry Readiness
→ CONDITIONALLY BLOCKED ON BATCH-1 GLOBAL ACCEPTANCE

Batch 3 Entry Readiness
→ CONDITIONALLY BLOCKED ON BATCH-1 + BATCH-2 GLOBAL ACCEPTANCE

Batch 4 Entry Readiness
→ CONDITIONALLY BLOCKED ON BATCH-1 + BATCH-2 + BATCH-3 GLOBAL ACCEPTANCE

Batch 5 Entry Readiness
→ CONDITIONALLY BLOCKED ON BATCH-1..4 GLOBAL ACCEPTANCE
```

No later Batch is authorized by this assessment.

---

# 15. Contract Design Semantic Scope

Each Contract Design Batch may establish representation-neutral semantics for its authorized RCPs, including where applicable:

```text
Contract semantic subject / identity
producer obligations
consumer obligations
Authority / Semantic Ownership / SoT / final Actual-state preservation
source/revision/correlation references
applicability/currentness
temporal/freshness/failure/unknown/partiality
history/provenance/replay/supersession
offline/private/degraded behavior
Tenant/Organization/Principal/AuthN/AuthZ/Policy/Trust/privacy/redaction
compatibility/migration/versioning/conformance
guarantees / explicit non-guarantees
cross-component closure criteria
MDE / revalidation triggers
```

The Contract Design phase does **not** automatically select:

```text
REST / GraphQL / gRPC / WebSocket / SSE
JSON / Protobuf / concrete wire envelope
OpenAPI / JSON Schema / DTO structure
HTTP/RPC method names
queue/broker/event transport
physical identifier formats
database/event-store schemas
SDK language/package/API shape
implementation algorithms
process/service/worker/deployment topology
```

---

# 16. MDE / Governance Boundary

```text
New Product capability required merely for Batch-1 entry
→ NO

New Product Component
→ NO

New Internal Boundary
→ NO

New Runtime Role
→ NO

New RCP
→ NO

New universal identity namespace
→ NO

New Authority / SoT / final Actual-state owner
→ NO

Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

If actual Contract Design discovers a true need for an Owner-reserved choice, the bounded session must stop and return one MDE at a time.

---

# 17. Assessment Result

```text
RCP CONTRACT PRESSURE COUNT
→ 24 / unchanged

CONTRACT DESIGN BATCH COUNT
→ 5

GLOBAL CONTRACT BATCH DEPENDENCY GRAPH
→ ACYCLIC

BATCH 1
→ RCP-01 / 02 / 03 / 04 / 19 / 24
→ ENTRY READINESS SATISFIED

BATCH 2
→ RCP-05 / 07 / 08 / 09 / 10 / 23
→ BLOCKED ON BATCH-1 GLOBAL ACCEPTANCE

BATCH 3
→ RCP-06 / 11 / 12 / 13 / 14 / 15
→ BLOCKED ON BATCH-1 + BATCH-2 GLOBAL ACCEPTANCE

BATCH 4
→ RCP-16 / 17 / 18 / 20 / 21
→ BLOCKED ON BATCH-1..3 GLOBAL ACCEPTANCE

BATCH 5
→ RCP-22
→ BLOCKED ON BATCH-1..4 GLOBAL ACCEPTANCE

SYSTEM-LEVEL SDK DETAILED DESIGN READINESS
→ NOT_SATISFIED
```

---

# 18. Explicit Non-authorization

```text
Runtime / Domain Stable Contract Design / Batch 1 producing
→ NOT AUTHORIZED BY THIS ASSESSMENT

Batch 2..5 producing
→ NOT AUTHORIZED

RCP Full Cross-component Closure
→ NOT DECLARED

System-level SDK Detailed Design
→ NOT AUTHORIZED

Design-to-Implementation Readiness
→ NOT AUTHORIZED

Implementation Planning / IWP / Coding
→ NOT AUTHORIZED
```

Current Authorized Phase remains `NONE`.

Repository-hygiene ref `refs/heads/tmp-do-not-create` remains non-authoritative/non-semantic and has no unique commit/content.

---

# 19. Unique Next Legal Action

```text
persist this batching/readiness assessment as a dedicated GAC transition
→ seal an assessment epoch
→ fresh Repository recovery
→ if Batch-1 readiness remains SATISFIED and no drift/MDE/blocker appears,
   perform a separate explicit Runtime / Domain Stable Contract Design / Batch 1 authorization transition
→ only after the authorization State seal may one bounded Batch-1 producing session start
```
