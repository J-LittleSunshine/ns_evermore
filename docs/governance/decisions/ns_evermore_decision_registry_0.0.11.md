# ns_evermore Decision Registry — Current Revision

- **Version:** `0.0.11`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `0.0.10`

## 1. Current Authority Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Constraint Index → docs/ns_evermore_nse_constraints_index_0.0.5.md
Project Architecture → docs/ns_evermore_project_architecture_0.0.3.md / GLOBAL_ACCEPTED / NORMATIVE / CURRENT
Accepted Z2 DAD → Z2-DAD-001..041
Accepted Z2 Owner MDE → Z2-MDE-001..017
Unified Governance → docs/governance/ns_evermore_governance_0.0.2.md
```

## 2. Accepted Z3 Baselines

```text
Z3 Batch 1 Capability Baseline → GLOBAL_ACCEPTED / NORMATIVE
Z3 Batch 2 Interaction Experience Baseline → GLOBAL_ACCEPTED / NORMATIVE
Z3 Batch 3 Five-component Internal Architecture Boundary Baseline → GLOBAL_ACCEPTED / NORMATIVE
Accepted Z3 DAD → Z3-DAD-001..014
Five-component Internal Architecture Boundaries → 34 total
```

Normative artifacts remain the accepted Z3 Candidate / Global Acceptance / DAD evidence files under `docs/architecture_reviews/`.

## 3. Accepted Runtime Responsibility Architecture / Batch 1

Candidate:

`docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_candidate_0.0.1.md`

Global Acceptance:

`docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_global_acceptance_0.0.1.md`

Status:

```text
Runtime Responsibility Architecture / Batch 1 → GLOBAL_ACCEPTED / NORMATIVE RUNTIME UPSTREAM
Runtime Role Count → 22
Role Count → ns_server 9 / ns_runtime 4 / ns_node 4 / ns_agent 4 / ns_web 1
34 Internal Boundary Runtime Coverage → 34 / 34 / 100%
Mandatory Runtime Journeys A-U → CLOSED
Runtime Stable Contract Pressure → 24
```

Accepted Runtime Roles:

```text
ns_server
→ SV-R01 Business Application Runtime Participant
→ SV-R02 Automation Runtime Semantic Participant
→ SV-R03 Data / Knowledge / ETL Runtime Participant
→ SV-R04 Execution Admission Gate Participant
→ SV-R05 Managed Configuration Desired-state Participant
→ SV-R06 Server-local Background Execution Participant
→ SV-R07 Human Task Aggregation & Response Routing Participant
→ SV-R08 Notification Lifecycle & External Delivery Participant
→ SV-R09 Discovery Projection Participant

ns_runtime
→ RT-R01 Participant Presence Coordinator
→ RT-R02 Governed Routing / Scheduling / Dispatch Coordinator
→ RT-R03 Operation Continuation / Delegation / Intervention Coordinator
→ RT-R04 Coordination Recovery / Reconciliation Participant

ns_node
→ ND-R01 Node Capability & Readiness Participant
→ ND-R02 Governed Local Execution Participant
→ ND-R03 Protected Local Effect Custodian
→ ND-R04 Node Offline Continuity & Recovery Participant

ns_agent
→ AG-R01 Agent Runtime Participant
→ AG-R02 Model / Provider Mediation Participant
→ AG-R03 Native Multi-Agent Composition Coordinator
→ AG-R04 Cross-domain Delegation & Automation Participant

ns_web
→ WB-R01 Governed Human Interaction & Projection Participant
```

## 4. Accepted Runtime DAD

Evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_dad_evidence_0.0.1.md`

```text
RRA-B1-DAD-001..010 → GLOBAL_ACCEPTED
```

Subjects:

```text
001 22-role Runtime taxonomy and non-conflation
002 ns_server runtime partition refinement
003 four distinct ns_runtime coordination roles
004 Node N1-N4 role split; attended/unattended as ND-R02 modes
005 Agent runtime decomposition
006 one ns_web human interaction/projection role
007 HITL runtime topology
008 governed Trial uses existing domain/runtime owners
009 intervention/recovery request-coordination-outcome separation
010 runtime identity/correlation pressure + 24 stable Runtime contract pressures
```

## 5. Permanent Runtime Invariants

```text
Runtime Role != Product Component
Runtime Role != Internal Architecture Boundary
Runtime Role != Process / Service / Worker / Deployment Unit automatically
Runtime placement != Semantic Authority
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Node Attempt != Protected Local Effect / Source Fact
same bounded Actual-state assertion → exactly one final owner
ns_runtime coordination != Automation semantic ownership
Agent composition coordination != participant Agent Actual-state ownership
Human Task wait/applicability/submission/continuation remain distinct
Notification lifecycle/delivery-attempt != underlying source/current condition
Desired != Applied != Observed
Configuration != Secret
Secret Reference != Secret Material
Reconnect != Reconciled
Replay != Retroactive Authorization
```

No universal Runtime SoT, Runtime Manager, Trial Engine, Cancellation Engine, Retry Engine, Rollback Engine or Scheduler Authority is accepted.

## 6. Runtime Multiplicity / Physical Non-implication

Accepted multiplicity is semantic only, including `PER_NODE`, `PER_ATTEMPT`, per-Agent, per-composition and per-delegation pressure where applicable.

```text
Process count / worker pool / daemon / replica / thread / coroutine / container / host mapping → NOT ACCEPTED BY RUNTIME BATCH 1
```

## 7. Open Decision State

```text
Open MDE → 0
Unpersisted Owner Decision → 0
Owner-reserved unresolved decision → 0
Missing Product Capability → 0
Missing Internal Boundary → 0
Authority / SoT / Actual-state / Source-effect Ambiguity → 0
```

## 8. Consumption Rule

Future sessions consume current Global State, Unified Governance, this Registry, current Constraint Index, accepted Project Architecture, accepted Z3 baselines and accepted Runtime Responsibility Architecture evidence.

No downstream session may infer Authority/SoT from Runtime Role placement, process/service placement, UI, aggregation, storage, transport, provider, code-module placement or implementation convenience.
