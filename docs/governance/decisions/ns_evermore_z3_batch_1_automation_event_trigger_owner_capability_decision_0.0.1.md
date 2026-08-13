# NGRP-001 Phase Z3 / Batch 1 — Automation Event-driven Trigger Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should native Automation support governed event-driven triggering as a first-class product capability, rather than limiting execution initiation to explicit invocation and time/schedule-driven initiation?

This question is product-significant because event-driven initiation materially affects enterprise integration, delivery ergonomics, cross-domain composition and the product boundary of Automation as a first-class capability domain.

Accepted ownership remains unchanged:

```text
Automation Definition / Workflow Semantic Authority
→ ns_server

Automation Canonical Definition SoT
→ ns_server

ns_runtime
→ applicable scheduling / routing / dispatch / runtime coordination responsibility

ns_node
→ applicable local execution responsibility
```

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO

Reason
→ Event-triggered Automation is a material product capability not explicitly frozen upstream.
→ This decision does not move Authority, Source of Truth, Actual-state Ownership, Trust, Tenant, IAM, Policy, Artifact Acceptance or Execution Admission ownership.
```

## 3. Durable Alternatives Presented

### Option A — No native event-triggered Automation

Automation initiation remains centered on explicit invocation and schedule/time-triggered execution. External/internal events must first be handled by another capability and converted into an explicit execution intent.

### Option B — Governed native event-driven Automation

Automation Definition natively supports applicable event-driven trigger semantics:

```text
event occurrence
→ governed trigger evaluation
→ execution intent
→ existing Artifact / Admission / Runtime lifecycle
```

Event sources may include applicable native business, data/integration, external enterprise-system, node/local, Agent-originated or operational events, subject to later detailed capability and contract design.

### Option C — Native-platform events only

Automation supports platform-native event triggering, while external enterprise events must first be normalized by Business Application / Data Integration into a native event domain.

## 4. Recommendation Presented

`B — Governed native event-driven Automation`.

Rationale:

- Automation is a first-class principal capability domain;
- enterprise integration, Data/Knowledge/ETL, local execution and Agent capabilities create durable event-driven composition pressure;
- without a native event-trigger capability, repeated glue code would be required merely to convert events into Automation execution requests;
- native event triggering preserves the Automation product boundary without assigning Automation authority to event producers or transports;
- offline/private deployment remains possible with private/local event sources.

## 5. Project Owner Decision

```text
Selected Option
→ B

Native Automation Event-driven Trigger Capability
→ REQUIRED
```

## 6. Normative Capability Consequences for Z3 Batch 1

The Z3 Batch 1 capability baseline may consume:

```text
Automation
→ MUST support governed event-driven triggering as a native product capability

Event occurrence
→ MAY form an applicable trigger input
→ MUST NOT itself imply Execution Admission

Event-triggered execution
→ remains inside existing Tenant / IAM / Policy / Trust / Artifact / Admission governance
```

Permanent non-transfer rules:

```text
Event Received != Execution Admitted
Event Source != Automation Semantic Authority
Event Producer != Policy Authority
Event Transport != Event Semantic Authority
Event Trigger != Runtime Dispatch Authority
External Event != External Source-of-Truth Transfer
```

## 7. Explicit Non-implications / Deferred Mechanics

This decision does **not** decide:

```text
Event Bus
Broker
Queue
Webhook
WebSocket event path
Topic / subscription model
Event schema / envelope
Delivery guarantee
Ordering algorithm
Retry algorithm
Deduplication algorithm
Replay algorithm
Routing path
Runtime Role or process topology
Event storage
Concrete source connectors
CloudEvents or another standard
```

Named later authority:

```text
Five-component Internal Architecture Boundary Synthesis
→ capability/component boundary continuation only after separate GAC authorization

Runtime Responsibility Architecture
→ runtime coordination / delivery / recovery semantics where applicable

Component Internal Design
→ bounded component realization after authorization

Shared Foundation / Contract / Provider authorities
→ reusable authority-neutral mechanics only if later admitted

Project Owner / MDE
→ any later material Authority / SoT / Trust / major compatibility / high-lock-in commitment
```

## 8. Offline / Private Deployment Consequence

Event-driven Automation must remain compatible with private/offline operation. It must not require a mandatory public event service, vendor SaaS control plane, public broker or public registry for core correctness.

## 9. Compatibility / Recovery Consequence

Later design must preserve explicit event identity/source/provenance/revision/compatibility and applicable unknown/stale/conflicting/replay conditions where material. No event representation or reconciliation algorithm is frozen here.

## 10. Preserved Invariants

This decision preserves:

- exactly five Product Components;
- Automation as first-class / parallel / non-subordinate capability domain;
- `Automation Semantic Authority / Canonical Definition SoT → ns_server`;
- Formal Artifact Acceptance Authority and Formal Execution Admission Authority remaining `ns_server` and semantically distinct;
- `ns_runtime` scheduling/dispatch responsibility without Automation semantic authority transfer;
- `ns_node` execution without Automation authority transfer;
- external bounded Sources of Truth;
- Tenant / Organization / IAM / Policy / Trust / Artifact / Admission governance;
- offline/private correctness;
- no Runtime Architecture, Shared Foundation detailed design or implementation leakage.

## 11. Revalidation Trigger

Revalidate if the Project Owner later changes native event-driven Automation support, changes Automation semantic authority/SoT, or changes the rule that event occurrence/transport does not itself create governance authority or admission.

## 12. Bounded-session Authority Limit

This evidence records one Project Owner capability decision inside Z3 Batch 1.

It does not:

```text
constitute GAC Global Acceptance
advance GAC Epoch
authorize Z3 Batch 2
complete Z3 Batch 1
start normative Five-component Internal Architecture Boundary synthesis
start Component Internal Design
start Runtime Responsibility Architecture
start Shared Foundation Architecture
start Foundation Contract / Module / Provider Design
start Implementation Planning / IWP / coding
```
