# NGRP-001 Z2 MDE-008 — Formal Execution Admission Authority Owner Decision

- **Decision ID:** `Z2-MDE-008`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Decision Entry HEAD:** `70fb3863356ff795017e168db1d08b1a0f72cb05`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; accepted `NSE-001..017`; `Z2-MDE-001..007`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final **Formal Execution Admission Authority** for `ns_evermore`?

Formal Execution Admission is the governed decision that a specific execution intent/request, under its applicable Tenant, Principal, Policy, Artifact revision, and other required context, is formally permitted to enter the execution lifecycle.

This decision does not select an admission schema, grant/token format, protocol, scheduler, worker, queue, runtime role, fail-open/fail-closed rule, online/offline mechanism, cache, persistence model, or deployment topology.

## 2. Classification

```text
Classification
MDE

Reason
Formal Execution Admission is a major execution/governance authority explicitly reserved to the Project Owner by Unified Governance.
NSE-007 requires Formal Execution Admission to remain distinct from Artifact Acceptance, Installation, Activation and Runtime Execution Attempt.
The Constitution explicitly forbids deriving Admission Authority automatically from task dispatch.
```

## 3. Alternatives Presented

### A — `ns_server` owns unified Formal Execution Admission Authority

`ns_server` is the final Product Component authority for formal admission into governed execution. `ns_runtime` consumes admission outcome/evidence for scheduling, routing, coordination and dispatch. `ns_node` and `ns_agent` exercise admitted execution without gaining Admission Authority by locality or execution capability.

### B — `ns_runtime` owns Formal Execution Admission Authority

`ns_runtime` combines runtime readiness/coordination information with upstream governance facts and becomes the final admission decision boundary before scheduling/dispatch.

### C — Federated Execution Admission Authorities

Different capability domains own separate final admission authorities for their own execution classes, requiring composition, precedence, delegation and cross-domain admission semantics.

## 4. Recommendation Presented

`A — ns_server owns unified Formal Execution Admission Authority`.

Rationale: this preserves the constitutional identity of `ns_runtime` as Communication / Runtime Coordination / Scheduling / Dispatch Hub without converting operational executability into governance admission. It also preserves NSE-007 state separation and NSE-008 local-execution authority separation while allowing later offline/degraded designs to use bounded, pre-issued admission evidence without granting local admission authority.

## 5. Project Owner Decision

```text
Selected Option
A

Formal Execution Admission Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

```text
ns_server
→ owns final Formal Execution Admission Authority

ns_runtime
→ may consume admission outcomes/evidence
→ may coordinate, schedule, route and dispatch admitted execution
→ does not gain Admission Authority through scheduling, dispatch, connectivity, routing or runtime readiness

ns_node
→ may execute an admitted operation and later consume bounded pre-issued admission evidence where authorized
→ does not gain Admission Authority through local possession, local execution, offline operation, source-fact production, grant exercise, recovery or reconciliation handoff

ns_agent
→ may execute Agent/reasoning/tool activity under applicable admission
→ does not gain Admission Authority through AI execution or tool invocation

ns_web
→ may initiate/administer execution-related human-facing workflows
→ does not gain Admission Authority through UI interaction

Shared Foundation
→ may later mediate reusable technical capabilities
→ does not gain Admission Authority by mediation, transport, storage or provider placement
```

## 7. Mandatory Semantic Separations

```text
Policy Permit
!= Formal Execution Admission

Formal Artifact Acceptance
!= Formal Execution Admission

Installation
!= Activation
!= Formal Execution Admission

Scheduling
!= Formal Execution Admission

Dispatch
!= Formal Execution Admission

Runtime Readiness
!= Formal Execution Admission

Runtime Execution Attempt
!= Formal Execution Admission

Grant Exercise
!= Grant Issuance / Admission Authority
```

The fact that Policy Authority, Artifact Acceptance Authority and Execution Admission Authority are all currently allocated to `ns_server` does not merge those semantic authority domains.

## 8. Offline / Degraded Non-Implication

This decision does **not** require every execution attempt to synchronously contact `ns_server`.

Later authorized architecture may define bounded, traceable, revision-aware, capability-specific pre-authorization/admission evidence for offline or degraded execution, subject to accepted Tenant, IAM, Policy, Security, Artifact, Audit and reconciliation invariants.

```text
Offline / Disconnected
!= Local Admission Authority

Possession of Admission Evidence
!= Authority to Issue or Redefine Admission
```

Any material offline fail-open/fail-closed policy remains a separate MDE when actually required.

## 9. Explicit Non-Implications

This decision MUST NOT be interpreted as deciding:

```text
Admission protocol / schema / token / grant format
Admission persistence
Admission cache
Admission lifecycle state machine
Runtime Role set
Scheduler / worker / queue technology
Online-only admission
Offline fail-open / fail-closed behavior
Execution placement
Policy evaluation implementation
Artifact format or registry
```

It also does not make `ns_server` a Universal Authority.

## 10. Constraint Preservation

This decision preserves:

- `NSE-004` offline core correctness and governance invariance;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` authority non-transfer through invocation/execution;
- `NSE-007` Definition / Artifact / Runtime governance-state separation;
- `NSE-008` local execution authority and source-effect accountability separation;
- `NSE-009` representation-independent later contract semantics;
- `NSE-010` extension/re-delivery authority non-escalation;
- `NSE-012` Shared Foundation authority neutrality;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 11. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Responsibility / Authority / SoT Matrix;
- later Runtime Responsibility Architecture and Component design where admission evidence is consumed;
- later offline/degraded execution and reconciliation design;
- later contract design, without authorizing any of those phases.

## 12. Revalidation Trigger

Revalidation is required if the Project Owner changes Formal Execution Admission Authority away from `ns_server`, merges Admission with Policy/Artifact/Dispatch semantics, or changes the constitutional requirement that dispatch does not automatically imply admission authority.

Changes to scheduler, worker, queue, transport, process, service, container, database, cache, package or provider placement do not by themselves revalidate this decision.

## 13. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
