# NGRP-001 Phase Z3 / Batch 2 — Unified Governed Human Task Inbox Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **MDE Classification:** `NO`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Decision Predecessor HEAD:** `83edcb7ec03772acdcb76c7246b03a1ffe291b78`
- **Current Global State at Decision:** `GAC-EPOCH-0022`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Given that governed Human-in-the-loop capability is already required for both Native Automation and Native AI Agent execution, what product-level interaction model SHALL govern discovery and handling of outstanding human actions?

The accepted upstream requires applicable human input, review, choice, confirmation and correction without transferring Policy, Artifact Acceptance, Execution Admission, semantic or runtime authority to the human-facing surface. The unresolved question is whether such human actions remain discoverable only inside their originating execution contexts, become a unified governed Human Task capability, or expand into a broader universal enterprise attention capability.

---

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

### Why Product-significant

The choice materially affects:

```text
End-user work model
Operator observability
Return-later / cross-session interaction
Agent / Automation human handoff
Delivery workflow
Business Application composition pressure
Product complexity
```

### Why not MDE

The selected capability does not move or merge:

```text
Policy Authority
Artifact Acceptance Authority
Execution Admission Authority
Automation Semantic Authority
Agent Semantic Authority
Runtime Actual-state Ownership
Tenant / IAM / Trust Authority
```

It establishes a product interaction capability and a unified human-work projection/interaction entry point only. Concrete stable Human Task identity, ownership, storage, protocol, assignment authority, runtime-state ownership, or cross-boundary schema is not decided here. Any later proposal that changes those material dimensions remains subject to Unified Governance and MDE escalation where applicable.

---

## 3. Durable Mutually-exclusive Alternatives

### A — Contextual HITL Only

Human action requests remain discoverable and actionable only in their originating Agent or Automation execution context. No unified product-level Human Task work capability is required.

### B — Unified Governed Human Task Inbox

The product provides a unified Human Task / Work Inbox capability for outstanding governed human actions originating from accepted Agent and Automation HITL semantics. It supports discovery, re-observation and governed response participation across applicable execution contexts and sessions.

The unified Human Task capability is specifically for items requiring human action. It is not a generic Notification Center, operational alert center or universal governance attention center.

### C — Unified Enterprise Attention Center

The product provides one broad attention capability covering Human Tasks together with operational alerts, governance attention, configuration/reconciliation problems and other actionable system conditions.

---

## 4. Recommendation Presented

```text
Recommendation
→ B — Unified Governed Human Task Inbox
```

### Recommendation Rationale

Accepted Agent and Automation HITL plus long-running/background execution, return-later observation and cross-session continuity create a durable need for users to answer `what requires my action?` without returning manually to every originating execution. A unified Human Task capability closes that human-work gap while avoiding the substantially broader product commitment and semantic-collapse risk of turning all notifications, diagnostics, governance states and operational alerts into one universal attention model.

---

## 5. Tradeoffs and Impact

### Benefits

- gives human participants a stable product-level way to discover outstanding HITL work;
- supports browser/session loss and later return without relying on UI session state;
- prevents Agent, Automation and Business Application surfaces from repeatedly inventing incompatible `my tasks` semantics;
- improves operator ability to distinguish machine failure from an execution legitimately waiting for human input;
- supports consistent response provenance and execution association pressure across Agent and Automation.

### Costs

- later architecture/design must explicitly resolve Human Task identity, lifecycle projection, principal association, response provenance, staleness/conflict handling and re-observation semantics;
- ns_web and other applicable interaction surfaces must preserve authorization-scoped visibility without becoming the Human Task semantic authority by presentation;
- diagnostics and lifecycle semantics must distinguish waiting-for-human from generic waiting/failure.

### Risks / Complexity

- an Inbox may be incorrectly treated as the canonical task or execution state owner;
- a human-facing `approved` or `completed` presentation may be incorrectly conflated with Policy Permit, Artifact Acceptance or Execution Admission;
- stale, expired, wrong-context, conflicting or unverified responses can be misapplied unless later provenance/context semantics are explicit;
- a future implementation may try to broaden Human Task into a generic notification/alert bucket without separate product governance.

### Long-term Impact

`ns_evermore` adopts a native governed human-machine work capability across Agent and Automation HITL while retaining separate semantics for notification, operational alerting, governance state, diagnostics and runtime actual-state.

### Compatibility / Migration Impact

Future Human Task evolution must preserve enough semantic continuity to associate a human action with the applicable execution, participant/principal context and revision/provenance. This decision does not freeze a task identifier format, persistence representation, assignment schema or concrete lifecycle state machine.

### Offline / Private Deployment Impact

The capability must remain compatible with private/offline deployment. If later authorized design permits offline/degraded human response submission, response submission, governed acceptance/interpretation, execution resume and reconciliation must remain distinguishable. Offline response possession must not imply immediate reconciliation or authority transfer.

### Cross-component Impact

```text
Automation / Agent
→ may produce governed human-action requirements within their accepted semantics

ns_web
→ must support an authorized human-facing unified Human Task interaction capability

Applicable semantic / runtime Actual-state owners
→ remain authoritative for underlying execution/task meaning and actual state

System-level SDK / other future surfaces where authorized
→ may expose the same governed Human Task semantics without becoming Authority
```

No component-internal boundary, runtime role, API, schema, transport or storage topology is selected.

---

## 6. Project Owner Selected Result

```text
Selected Option
→ B

Unified Governed Human Task Inbox
→ REQUIRED

Applicable Sources
→ Agent HITL
→ Automation HITL

Cross-session Re-discovery / Re-observation
→ REQUIRED where applicable

Generic Notification Center
→ NOT IMPLIED

Universal Enterprise Attention Center
→ NOT IMPLIED
```

The Project Owner explicitly selected Option `B` in the authorized Z3 Batch 2 bounded session.

---

## 7. Explicit Selected Semantic Result

The product SHALL provide a unified governed Human Task interaction capability sufficient for authorized human participants to discover and act on applicable outstanding Agent/Automation HITL work independently of the originating browser/UI session.

The capability SHALL preserve the originating semantic and execution context and SHALL represent human participation without silently promoting presentation or response state into Policy, Artifact, Admission, Trust or runtime factual authority.

At product-capability level the following pressure is now accepted:

```text
Outstanding governed Human Action
→ discoverable through unified Human Task capability

Human Task
→ associated with applicable originating Agent / Automation execution context

Human Response Submitted
!= Response semantically accepted/usable automatically

Human Response Accepted/Applied
!= Policy Permit automatically
!= Artifact Acceptance
!= Execution Admission

Human Task Projection
!= Runtime Actual-state Owner
```

---

## 8. Normative Consequences

1. `ns_web` must provide a human-facing interaction capability for unified discovery and handling of applicable outstanding Human Tasks.
2. Agent and Automation interaction semantics must expose sufficient governed information for a Human Task projection without transferring Agent/Automation authority to the projection.
3. Return-later and cross-session Human Task re-observation must not depend solely on ephemeral browser/session state.
4. Human Task interaction must preserve applicable Tenant, Organization, Principal, Policy, Trust, provenance, revision and execution-context semantics.
5. Wrong-context, stale, expired, conflicting, unverified or unreconciled human responses must remain explicit where applicable rather than being treated as valid approval/input by UI convention.
6. Human Task completion presentation must derive from governed evidence and must not itself canonicalize execution completion.

---

## 9. Authority / SoT / Actual-state Preservation

```text
Human Task Inbox
!= Policy Authority
!= IAM Authority
!= Artifact Acceptance Authority
!= Execution Admission Authority
!= Automation Semantic Authority
!= Agent Semantic Authority
!= Platform Trust Authority
!= Universal Runtime Actual-state Owner
!= Human-response Semantic Authority automatically

ns_web presentation/editing
!= Human Task canonical SoT automatically

Human clicks Approve / Confirm / Submit
!= Policy Permit automatically
!= Artifact Accepted
!= Execution Admitted
```

Accepted Project Architecture and Z2-MDE-001..017 remain unchanged.

---

## 10. Explicit Non-implications

This decision does NOT establish:

```text
one universal notification center
one universal enterprise attention center
one universal operational alert model
Human Task database or storage owner
Human Task API / schema / message representation
Human Task assignment engine
workflow state machine
timeout / escalation policy
notification channel
Email / SMS / WeCom / Slack / Web Push / Mobile Push
mobile/native client expansion
Policy approval semantics
Artifact review authority
Execution Admission approval semantics
runtime wait/resume protocol
```

It also does not make a task visible across Tenant or Principal boundaries without authorization.

---

## 11. Named Deferrals

```text
Human Task stable identity / lifecycle representation / principal binding / assignment mechanics
→ Five-component Internal Architecture Boundaries → Component Internal Design

Human wait / suspend / resume / runtime actual-state mechanics
→ Runtime Responsibility Architecture

Human Task cross-boundary stable contract representation where required
→ later applicable Contract Design authority after explicit authorization

Notification delivery/channel mechanics
→ later Product/Component design authority if corresponding product capability is accepted

Offline human-response synchronization / reconciliation mechanics
→ Runtime Responsibility Architecture / Component Internal Design as applicable

Material Policy / Trust / Security / fail-open-fail-closed changes
→ Project Owner / MDE
```

No item is delegated to implementation to invent architecture semantics.

---

## 12. Revalidation Trigger

Revalidate this capability decision if the Project Owner later:

- removes native HITL from Agent or Automation;
- removes the unified Human Task product capability;
- broadens it into a universal enterprise attention/notification semantic authority;
- makes Human Task response itself a Policy, Artifact Acceptance or Execution Admission authority;
- materially changes task identity/history/compatibility commitments beyond the bounded product capability established here;
- changes the accepted Tenant/Principal/Trust/Runtime Actual-state topology in a way that affects Human Task semantics.

Concrete UI layout, task list presentation, storage, schema, runtime process, transport, notification provider or framework choice does not by itself trigger revalidation when the selected semantics remain preserved.

---

## 13. Bounded-session Authority Limit

This evidence records the Project Owner capability selection only.

It does NOT:

```text
claim GAC Global Acceptance
advance GAC Epoch
update Global Architecture State as acceptance authority
declare Product Capability Exhaustion
declare Five-component Internal Architecture Boundary readiness
authorize Z3 Batch 3
begin Five-component Internal Architecture Boundary Synthesis
begin Component Internal Design
begin Runtime Responsibility Architecture
begin Shared Foundation Architecture
begin Foundation Contract / Module / Provider Design
begin Implementation Planning
begin IWP
begin Coding
```

The current bounded session remains authorized only for Z3 Batch 2 Interaction Experience Capability Discovery / Owner Capability Checkpoint work.