# NGRP-001 Phase Z3 / Batch 2 — Governed Operation Intervention Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **MDE Classification:** `NO`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Decision Predecessor HEAD:** `b8aac6046ac2d780d2dfab75ff48b408934a88c0`
- **Current Global State at Decision:** `GAC-EPOCH-0022`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

What product-level interaction capability SHALL govern user/operator intervention into asynchronous or long-running work across applicable Agent, Automation, Node, server-local background-work and composed execution journeys?

Accepted upstream semantics already require long-running/asynchronous work, bounded runtime Actual-state ownership, history/provenance preservation, offline/degraded correctness, recovery/reconciliation, Agent and Automation execution, Agent-to-Node delegated work, attended and unattended Node execution, and Human-in-the-loop. However, none of those accepted semantics automatically guarantees that every operation is cancellable, retryable, resumable, or recoverable.

The product therefore needs an explicit capability choice between domain-local ad-hoc intervention, a unified governed intervention model with capability-specific support, or a universal cancel/retry/resume guarantee.

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
End-user control of long-running work
Operator recovery and intervention workflows
Developer / Delivery interaction semantics
Agent execution control
Automation execution control
Node delegated/local work control
Retry and duplicate-effect expectations
Offline / unreachable execution behavior
Historical attempt interpretation
Cross-surface consistency
```

### Why not MDE

The selected capability does not move or redefine:

```text
Formal Execution Admission Authority
Runtime Actual-state Ownership
Policy Authority
Artifact Acceptance Authority
Platform Security / Trust Authority
Tenant / Organization semantics
Product Definition Semantic Authority / Canonical SoT
```

It establishes a product-level interaction contract for requesting and understanding intervention. Any later proposal that changes an Authority/SoT/Actual-state owner, introduces a material offline fail-open/fail-closed rule, or promises universal transactional reversal would require separate MDE classification.

---

## 3. Accepted Upstream Preserved

The decision consumes without reopening:

```text
Formal Execution Admission Authority
→ ns_server

Runtime Actual-state Ownership
→ governed per bounded runtime semantic partition
→ exactly one final Actual-state Owner for the same assertion

System Runtime View
→ derived projection
→ not universal factual authority

Recovery / Reconciliation
→ evidence-preserving handoff
→ no authority transfer by reconnect/recovery

ns_node protected local effects/source facts
→ preserved and provenance-bearing
→ successful local effect != authorization authority

Agent / Automation HITL
→ REQUIRED

ns_node attended + unattended execution
→ REQUIRED

ns_server bounded server-local long-running/background work
→ REQUIRED
```

Permanent upstream separation remains:

```text
Request != Actual Result
Projection != Actual-state Authority
Recovery != State Restored automatically
Reconnect != Reconciled
Retry != Prior Attempt Never Happened
Browser Closed != Operation Cancelled
```

---

## 4. Durable Mutually-exclusive Alternatives Presented

### A — Observation-first; intervention remains domain-specific

The product guarantees submission/observation/history/result retrieval but does not establish one stable product-level intervention model. Individual Agent, Automation, Node or server-local capabilities may later define cancel/retry/resume/recover independently.

Consequences:

```text
Cross-domain intervention semantic consistency
→ NOT REQUIRED

Operation supported-intervention discovery
→ NOT REQUIRED AS A COMMON PRODUCT CAPABILITY
```

### B — Unified Governed Operation Intervention Model with capability-specific support

The product establishes one stable interaction model for governed intervention while allowing each bounded operation type/state to explicitly declare which intervention classes are supported, unsupported, unavailable or indeterminate.

Potential intervention classes include, where applicable:

```text
Cancel Request
Retry Request
Resume Request
Recovery Request
```

The request and its actual outcome remain distinct. No universal guarantee that any particular operation supports every intervention is created.

### C — Universal Cancel / Retry / Resume / Recovery guarantee

Every formal long-running operation must support cancellation, retry and resume/recovery as a uniform capability promise.

This creates a much stronger product commitment and implies substantial effect-reversal, idempotency, checkpointing and offline-reachability obligations across all execution domains.

---

## 5. Recommendation Presented

```text
Recommendation
→ B — Unified Governed Operation Intervention Model with capability-specific support
```

### Recommendation Rationale

Option B preserves cross-domain human-understandable control semantics without pretending that all physical or external effects are reversible, cancellable or resumable. It directly aligns with existing Actual-state ownership, provenance, retry/history, offline/degraded and reconciliation semantics.

Option A would cause semantic fragmentation and encourage Business Applications, delivery projects and extensions to create incompatible meanings for `cancel`, `retry`, `resume` and `recover`.

Option C would overcommit the product because many operations may already have produced irreversible local, device, filesystem, third-party or external-system effects. Stopping further execution cannot safely be represented as undoing prior effects.

---

## 6. Tradeoffs and Impact

### Benefits

- one stable user/operator/developer mental model for intervention across supported operation types;
- capability-specific freedom: not every operation must support every intervention;
- explicit separation of intervention request, processing and actual outcome;
- avoids false claims that stopping an execution reverses existing effects;
- preserves retry attempt lineage and historical evidence;
- works with offline/unreachable Node semantics without fabricating completion;
- enables SDK, `ns_web`, operational surfaces and customer extensions to expose consistent intervention meaning.

### Costs

Later authorized design must define enough stable semantics for:

```text
operation identity
supported-intervention capability declaration
intervention request identity/correlation
request lifecycle visibility
attempt lineage
actual outcome projection
unsupported/unavailable/indeterminate intervention state
```

This decision does not define the concrete contract/schema/API/state machine.

### Risks / Complexity

Primary risks are semantic collapse such as:

```text
Cancel Request Accepted
→ displayed as Cancelled

Retry Requested
→ prior attempt hidden or rewritten

Recovery Started
→ displayed as State Restored

Node Reconnected
→ displayed as Reconciled
```

Those interpretations are prohibited.

### Long-term Impact

The product acquires a stable enterprise asynchronous-operation control capability while preserving bounded operation-specific realizability.

### Compatibility / Migration Impact

Intervention meanings become stable cross-surface product semantics. Concrete mechanisms remain evolvable as long as they preserve request/outcome separation, attempt lineage, Actual-state ownership and supported/unsupported meaning.

Existing or future domain-specific intervention mechanisms must map to the governed product semantics rather than invent incompatible meanings.

### Offline / Private Deployment Impact

The model is explicitly compatible with private/offline operation.

Examples:

```text
Cancel request cannot reach disconnected Node
→ MUST NOT imply Cancelled
→ may be UNREACHABLE / PENDING / INDETERMINATE as later bounded semantics establish

Node reconnects
→ reconnect evidence available
→ does not prove the requested intervention occurred
→ reconciliation may remain pending
```

No mandatory public service or online control plane is introduced.

### Cross-component Impact

The capability may apply, where semantically supported, to:

```text
Agent execution
Multi-Agent composed execution
Automation execution
reusable Automation composition
Agent → Node delegated work
ns_node local execution
ns_server server-local long-running/background work
other later-authorized asynchronous operations
```

Each underlying semantic and Actual-state owner remains unchanged.

---

## 7. Project Owner Selected Result

The Project Owner selected:

```text
Selected Option
→ B

Product Capability
→ UNIFIED_GOVERNED_OPERATION_INTERVENTION_REQUIRED

Support Model
→ CAPABILITY_SPECIFIC

Uniform intervention semantics across applicable surfaces
→ REQUIRED

Every operation supports every intervention
→ NO
```

The product SHALL support explicit operation-level/bounded-operation-level determination of intervention availability without silently treating absence of support as success, failure or permission.

---

## 8. Explicit Selected Semantic Result

For an applicable governed operation:

```text
Operation
→ may expose supported intervention capability

Intervention support
→ may be SUPPORTED / UNSUPPORTED / CURRENTLY_UNAVAILABLE / INDETERMINATE
→ exact later vocabulary may be refined without changing this capability meaning
```

The following semantic separations are mandatory:

```text
Cancel Requested
!= Cancelled

Retry Requested
!= Retry Started

Retry Started
!= Prior Attempt Never Happened

Resume Requested
!= Resumed

Recovery Requested
!= State Restored

Reconnect
!= Reconciled

Execution Stopped
!= Existing Effects Reversed

Browser / UI Session Closed
!= Operation Cancelled
```

A request may be accepted for processing while the actual operation remains running, unreachable, partially completed or indeterminate.

Retry/re-execution must preserve prior-attempt lineage/provenance; the interaction model must not erase evidence of previous execution attempts or effects.

---

## 9. Normative Consequences

### End User / Business User

Where an intervention capability is exposed, the user must be able to distinguish:

```text
whether intervention is supported
whether a request was submitted/accepted for processing
whether the actual operation outcome has changed
whether the operation remains running/waiting/unreachable/unknown
```

### Operator / Administrator

Operational interaction must preserve enough governed state to distinguish request state from actual runtime state and to diagnose unsupported, unavailable, pending, failed or indeterminate intervention.

### Developer / Delivery / Integrator

System-level development surfaces must expose stable intervention semantics rather than forcing domain/application-specific interpretation of generic verbs such as `cancel`, `retry`, `resume` or `recover`.

### Human-in-the-loop

HITL interaction may coexist with operation intervention. Human response submission is not automatically an intervention outcome, and intervention does not erase outstanding human-response provenance.

---

## 10. Authority / SoT / Actual-state Preservation

This decision explicitly preserves:

```text
Formal Execution Admission Authority
→ ns_server / UNCHANGED

Runtime Actual-state Ownership
→ per bounded semantic partition / UNCHANGED

Automation Semantic Authority / Definition SoT
→ ns_server / UNCHANGED

Agent Semantic Authority / Definition SoT
→ ns_agent / UNCHANGED

Platform Security / Trust Semantic Authority
→ ns_server / UNCHANGED

Policy Semantic Authority
→ ns_server / UNCHANGED
```

Permanent rules:

```text
UI intervention command != Actual-state ownership
Intervention aggregator != universal Runtime SoT
Notification of cancellation != canonical cancellation proof
User intent to retry != admission or execution authority
Operation control surface != Policy Authority
```

---

## 11. Explicit Non-implications

This decision does **not** establish:

```text
universal cancellation support
universal rollback/reversal
universal retry safety
universal idempotency
universal checkpoint/resume support
universal transactional semantics
universal compensation semantics
one universal runtime state machine
one universal operation executor
one universal operation owner
one universal scheduler/worker/queue
immediate remote cancellation guarantee
cancel request = undo effects
retry = exactly-once execution
recovery = reconciliation complete
```

It also does not define actual UI buttons, commands, endpoints, schemas, message formats, queue behavior, process roles, worker topology or persistence.

---

## 12. Named Deferrals

Concrete realization remains with later separately authorized authorities:

```text
Five-component Internal Architecture Boundary Synthesis
→ allocate stable cross-component responsibility for intervention semantics without changing accepted Authority/SoT

Runtime Responsibility Architecture
→ precise runtime Actual-state partitions, request delivery/observation, cancellation/retry/resume/recovery runtime mechanics

Component Internal Design
→ bounded component-specific intervention realization and operation-specific support rules

Contract Design where later authorized
→ stable cross-boundary representation of operation/intervention semantics

Project Owner / MDE
→ any material offline fail-open/fail-closed rule, universal reversal guarantee, Authority/SoT move, major stable lock-in or other MDE-class commitment
```

No current item is delegated to implementation to invent architecture semantics.

---

## 13. Revalidation Trigger

Revalidate this Owner capability result if the Project Owner later changes any of:

```text
whether a unified governed operation-intervention product capability exists
whether intervention support is capability-specific
request vs actual-outcome separation
retry attempt lineage preservation
recovery/reconnect/reconciliation distinction
operation-control authority neutrality
```

A concrete transport, API, runtime framework, queue, state-machine implementation, process layout or UI design change is not by itself a revalidation trigger when the selected semantics remain preserved.

---

## 14. Bounded-session Authority Limit

This evidence records the Project Owner selection inside the authorized Z3 Batch 2 interaction-capability checkpoint.

It does not:

```text
claim GAC Global Acceptance
advance the GAC Epoch
update Global State as acceptance authority
authorize Z3 Batch 3
perform Five-component Internal Architecture Boundary Synthesis
perform Runtime Responsibility Architecture
perform Component Internal Design
perform Shared Foundation Architecture
perform Foundation Contract / Module / Provider Design
perform Implementation Planning
perform IWP
perform coding
```

Current bounded producing-session maximum remains:

```text
NGRP-001 Phase Z3 / Batch 2
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

only after all remaining authorized interaction-capability pressure has been classified/resolved and the required reviews/handoff evidence have been produced.
