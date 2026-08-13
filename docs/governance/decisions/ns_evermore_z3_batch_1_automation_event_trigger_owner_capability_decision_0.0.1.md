# NGRP-001 Phase Z3 / Batch 1 — Automation Event-driven Trigger Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should Native Automation support governed event-driven triggering as a first-class product capability, rather than limiting execution initiation to explicit invocation and time/schedule-driven initiation?

This is product-significant because event-driven initiation materially affects enterprise integration, delivery ergonomics, cross-domain composition and the Automation product boundary.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

Event-driven Automation is a material product capability not explicitly frozen upstream, but the selected semantics do not move Authority, SoT, Actual-state Ownership, Trust, Tenant, IAM, Policy, Artifact Acceptance or Execution Admission ownership.

## 3. Durable Mutually-exclusive Alternatives

### A — No native event-triggered Automation

Automation initiation remains centered on explicit invocation and schedule/time-triggered execution. External/internal events must first be handled by another capability and converted into an explicit execution intent.

### B — Governed native event-driven Automation

Automation Definition natively supports applicable event occurrence → governed trigger evaluation → execution intent, after which the existing Artifact/Admission/Runtime lifecycle remains applicable.

### C — Native-platform events only

Automation supports platform-native event triggering, while external enterprise events must first be normalized by Business Application/Data Integration into a native event domain.

## 4. Recommendation Presented

```text
Recommendation
→ B — Governed native event-driven Automation
```

### Recommendation Rationale

Automation is a first-class principal capability domain and enterprise integration, Data/Knowledge/ETL, local execution and Agent capabilities create durable event-driven composition pressure. Option B avoids repeated glue code whose sole job is to translate events into Automation invocation, while preserving event producers/transports as non-authoritative inputs.

## 5. Tradeoffs and Impact

**Benefits**
- supports enterprise event-driven Automation without repeated glue services;
- enables business/data/integration/local/Agent-originated event composition where later accepted semantics permit;
- complements explicit and scheduled invocation without changing Automation authority.

**Costs**
- later architecture must define event identity, provenance, compatibility and recovery semantics;
- operational/conformance tooling must distinguish event receipt, trigger evaluation, admission and runtime execution.

**Risks / Complexity**
- duplicate/replayed/out-of-order/stale events can produce ambiguous trigger pressure unless later semantics are explicit;
- implementations may incorrectly equate event receipt with permission/admission;
- external event mapping can accidentally imply external SoT transfer if provenance is not preserved.

**Long-term Impact**
- Automation becomes a manual/explicit + scheduled + event-driven enterprise Automation platform rather than only a task/schedule executor;
- event transport remains replaceable and outside Automation Semantic Authority.

**Compatibility / Migration Impact**
- later evolution must preserve event source/identity/revision and supported/unsupported trigger semantics where material;
- no event envelope, delivery guarantee or versioning representation is selected here.

**Offline / Private Deployment Impact**
- event-driven Automation must work with private/local event sources and must not require public brokers, vendor SaaS, public registries or public event services for core correctness.

**Cross-component Impact**
- `ns_server` remains Automation Semantic Authority and Canonical Definition SoT;
- `ns_runtime` may later coordinate delivery/scheduling/dispatch but does not gain Automation authority;
- `ns_node`, Agent, Business/Data or external systems may be event sources/participants without gaining Automation/Policy/Admission authority.

## 6. Project Owner Selected Result

```text
Selected Option
→ B

Native Automation Event-driven Trigger Capability
→ REQUIRED
```

## 7. Normative Capability Consequence

```text
Automation
→ MUST support governed event-driven triggering as a native product capability

Event occurrence
→ MAY form applicable trigger input
→ MUST NOT itself imply Execution Admission

Event-triggered execution
→ remains inside accepted Tenant/IAM/Policy/Trust/Artifact/Admission governance
```

## 8. Authority / SoT / Actual-state Preservation

Automation Authority/Definition SoT remain `ns_server`; runtime actual-state ownership remains partitioned; external factual SoT is not transferred merely by an event; Formal Artifact Acceptance and Execution Admission remain distinct accepted authorities.

## 9. Explicit Non-implications

```text
Event Received != Execution Admitted
Event Source != Automation Authority
Event Producer != Policy Authority
Event Transport != Event Semantic Authority
Event Trigger != Runtime Dispatch Authority
External Event != External SoT Transfer
```

## 10. Deferred Mechanics / Named Later Authority

Not decided here: Event Bus, broker, queue, webhook, WebSocket path, topic/subscription model, event schema/envelope, delivery guarantee, ordering/retry/dedup/replay algorithms, routing, runtime roles/process topology, event storage, connectors or a specific event standard.

These remain for separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture, Component Internal Design, and later Shared Foundation/Contract/Provider work if admitted. MDE-class changes return to Project Owner.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes native event-driven Automation support, Automation Authority/SoT, or the rule that event occurrence/transport does not itself create governance authority or admission.

## 12. Bounded-session Authority Limit

This correction preserves the already selected Owner result and does not claim Global Acceptance, advance GAC state, authorize later batches or enter downstream architecture/design/implementation work.
