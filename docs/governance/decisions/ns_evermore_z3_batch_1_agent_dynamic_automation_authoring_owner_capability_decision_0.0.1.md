# NGRP-001 Phase Z3 / Batch 1 — Agent Dynamic Automation Authoring Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

When a Native Agent interprets user intent and determines that an Automation should be executed, may the Agent only select and parameterize an already-existing governed Automation Definition, or may it dynamically author a new candidate Automation Definition which must then enter the normal governed Automation lifecycle before execution?

This is product-significant because it determines whether Agent reasoning can translate user intent into a newly authored Automation candidate, rather than being limited to an existing Automation catalog, while preserving the established Automation governance boundary.

The intended product direction is centered on:

```text
User Intent
→ Agent reasoning
→ governed Automation capability
→ applicable governed execution
→ applicable Node execution
```

No general `Automation → Agent` scheduling/dispatch capability is established by this decision.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

This is a material product capability and interaction boundary. The selected semantics do not move accepted Automation Semantic Authority, Automation Canonical Definition SoT, Artifact Acceptance Authority, Execution Admission Authority, AI Agent Semantic Authority, Runtime Actual-state Ownership, Trust, Tenant, IAM or Policy ownership. If any of those were moved, the matter would require separate MDE governance.

## 3. Durable Mutually-exclusive Alternatives

### A — Existing Automation selection / parameterization only

The Agent may select and parameterize existing governed Automation Definitions but may not dynamically author a new Automation Definition.

### B — Dynamic candidate Automation authoring under normal governance

The Agent may dynamically produce a **candidate Automation Definition** from user intent. The candidate remains an Automation-domain definition and must enter the normal accepted Automation governance lifecycle before execution.

### C — Separate ephemeral Agent-generated executable-flow class

The Agent may generate a distinct ephemeral executable-flow class outside canonical Automation Definition semantics, creating a parallel governed executable-definition/artifact class.

## 4. Recommendation Presented

```text
Recommendation
→ B — Dynamic candidate Automation authoring under normal governance
```

### Recommendation Rationale

Option A would limit the Agent to an existing Automation catalog and would not fully realize the intended `user intent → Agent reasoning → dynamically composed Automation` product path. Option C would introduce a parallel ephemeral executable semantic class, duplicating governance, compatibility, recovery and artifact/admission concerns. Option B gives the Agent meaningful dynamic authoring capability while preserving one Automation semantic domain and the existing Definition → Artifact Acceptance → Execution Admission → Runtime separation.

## 5. Tradeoffs and Impact

**Benefits**
- user intent can produce a new governed Automation candidate instead of being limited to pre-authored flows;
- Agent reasoning can compose repeatable Automation-domain definitions while preserving one canonical Automation semantic domain;
- generated candidates can participate in the same lifecycle, compatibility, re-delivery and audit model as other Automation definitions.

**Costs**
- Agent-generated candidates require validation/certification, artifact-governance and execution-admission processing before execution;
- dynamic authoring introduces additional latency and operational complexity compared with selecting an already accepted Automation;
- governance/diagnostic surfaces must explain why a candidate is invalid, unaccepted, incompatible or not admitted.

**Risks / Complexity**
- generated definitions may be invalid, unsafe, incompatible, incomplete or semantically inconsistent with user intent;
- implementations may be tempted to execute generated material directly for convenience, which is explicitly prohibited;
- the Agent/Automation boundary can become ambiguous unless authoring participation is kept distinct from Automation Authority/SoT;
- introducing a shortcut ephemeral flow would fragment lifecycle and recovery semantics, so Option C is not selected.

**Long-term Impact**
- `ns_agent` becomes a governed Automation authoring participant capable of intent-to-Automation generation, not an Automation Semantic Authority;
- Agent-authored and human/SDK/Web-authored Automation candidates remain one Automation semantic class rather than diverging into parallel executable domains.

**Compatibility / Migration Impact**
- Agent-authored candidates use the same Automation revision/evolution/compatibility semantics as other Automation definitions;
- different authoring participant does not create a separate compatibility class;
- concrete version binding, migration and build/package mechanics remain deferred.

**Offline / Private Deployment Impact**
- dynamic authoring, validation and applicable governance must remain compatible with private/offline lifecycle requirements;
- core correctness must not require a public model provider, public compiler/builder, SaaS control plane, public registry or mandatory Internet connectivity;
- offline possession of a candidate does not imply acceptance/admission.

**Cross-component Impact**
- `ns_agent` may author/select a candidate Automation from user intent;
- `ns_server` remains Automation Semantic Authority, Automation Canonical Definition SoT, Formal Artifact Acceptance Authority and Formal Execution Admission Authority;
- `ns_node` may execute applicable governed/admitted work but does not own Automation semantics;
- whether `ns_runtime` participates in the physical runtime path remains deferred.

## 6. Project Owner Selected Result

```text
Selected Option
→ B

Agent Dynamic Automation Authoring Capability
→ REQUIRED

Agent may derive a candidate Automation Definition from user intent
→ YES

Candidate Automation Definition may execute without normal governance
→ NO

Agent becomes Automation Semantic Authority
→ NO

Agent becomes Automation Canonical Definition SoT
→ NO

Agent becomes Artifact Acceptance Authority
→ NO

Agent becomes Execution Admission Authority
→ NO
```

## 7. Normative Capability Consequence

```text
User Intent
→ ns_agent interprets / reasons
→ ns_agent may select an existing Automation OR author a candidate Automation Definition
→ candidate enters the normal Automation semantic/definition governance lifecycle
→ applicable candidate must reach accepted Artifact state where required
→ applicable execution must reach Formal Execution Admission
→ only then may governed runtime execution proceed
→ applicable executable work may ultimately reach ns_node execution
```

The exact runtime/transport path is not decided here.

## 8. Authority / SoT / Actual-state Preservation

```text
Automation Semantic Authority
→ ns_server / UNCHANGED

Automation Canonical Definition SoT
→ ns_server / UNCHANGED

Formal Artifact Acceptance Authority
→ ns_server / UNCHANGED

Formal Execution Admission Authority
→ ns_server / UNCHANGED

AI Agent Semantic Authority
→ ns_agent / UNCHANGED

Applicable Local Execution Responsibility
→ ns_node / UNCHANGED

Runtime Actual-state Ownership
→ unchanged per accepted bounded semantic partition
```

## 9. Explicit Non-implications

```text
Agent authors Automation candidate != Agent owns Automation semantics
Candidate Definition != Accepted Artifact
Candidate Definition != Execution Admitted
Agent request != Artifact Acceptance
Agent request != Execution Admission
Agent delegates applicable work != Node authority transfer
Node executes Flow Package != Node owns Automation Definition semantics
Dynamic Authoring != Ephemeral Automation class
Dynamic Authoring != governance bypass
```

No ungoverned Agent flow, Agent-owned Automation domain, Artifact bypass or Admission bypass is created.

## 10. Deferred Mechanics / Named Later Authority

Not decided here: Automation DSL, Agent-to-Automation authoring API, candidate physical representation, Flow Package format, package/reference transfer, whether `ns_agent` physically sends material to `ns_node`, whether `ns_runtime` is on the runtime path, build/compilation/generation, parameter binding, artifact packaging, version binding, sync/async invocation, transport/message schema, routing, retry, failure propagation, process topology or storage technology.

These remain for separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture, Component Internal Design and later Contract/Foundation/Provider work if admitted. Any later Authority/SoT/Trust/major compatibility/stable-identity/high-lock-in change returns to Project Owner/MDE governance.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes whether Agent may author a new Automation candidate, whether normal Automation governance remains mandatory, Automation Authority/Definition SoT, Artifact Acceptance/Execution Admission Authority, or introduces a separate ephemeral executable-flow semantic class.

## 12. Bounded-session Authority Limit

This evidence correction preserves the already selected Option B and does not claim Global Acceptance, advance GAC state, authorize later Z3 batches, or enter Five-component Internal Architecture Boundary synthesis, Runtime Responsibility Architecture, Component Internal Design, Shared Foundation/Contract/Module/Provider design, Implementation Planning, IWP or coding.
