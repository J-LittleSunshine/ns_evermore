# NGRP-001 Phase Z3 / Batch 1 — Agent Dynamic Automation Authoring Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD for this checkpoint:** `f4d818301adfc7b3d568bb028c2d0a809c2a5fba`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

When a Native Agent interprets user intent and determines that an Automation should be executed, may the Agent only select and parameterize an already-existing governed Automation Definition, or may it dynamically author a new candidate Automation Definition which must then enter the normal governed Automation lifecycle before execution?

The Project Owner selected the latter capability.

This checkpoint also corrects an over-broad producing-session inference: no product capability is established here for `Automation -> Agent` scheduling or dispatch. The intended product direction is centered on `User Intent -> Agent -> governed Automation execution -> applicable Node execution`.

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO

Reason
→ This is a material product capability and developer/user interaction boundary.
→ It does not move accepted Authority, Source of Truth, Artifact Acceptance, Execution Admission, Trust, Tenant, IAM, Policy or Runtime Actual-state ownership.
```

## 3. Durable Alternatives Considered

### Option A — Existing Automation selection / parameterization only

The Agent may select and parameterize existing governed Automation Definitions but may not dynamically author a new Automation Definition.

### Option B — Dynamic candidate Automation authoring under normal governance

The Agent may dynamically produce a **candidate Automation Definition** from user intent. That candidate must enter the normal accepted Automation governance lifecycle before execution.

### Option C — Ephemeral Agent-generated executable flow class

The Agent may generate a separate ephemeral executable-flow class outside canonical Automation Definition semantics. This would introduce a parallel governed executable-definition/artifact class.

## 4. Project Owner Decision

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

## 5. Required Product Capability Consequence

The Z3 Batch 1 capability baseline may consume the following Owner-decided product capability:

```text
User Intent
→ ns_agent interprets / reasons
→ ns_agent may dynamically author a candidate Automation Definition
→ candidate enters governed Automation semantics / definition lifecycle
→ accepted artifact / execution admission lifecycle remains applicable
→ applicable executable work may ultimately be delegated for Node execution
```

The exact runtime or transport path is not decided here.

## 6. Preserved Authority and Lifecycle Invariants

```text
Automation Semantic Authority
→ ns_server / UNCHANGED

Automation Canonical Definition SoT
→ ns_server / UNCHANGED

Artifact Acceptance Authority
→ ns_server / UNCHANGED

Execution Admission Authority
→ ns_server / UNCHANGED

AI Agent Semantic Authority
→ ns_agent / UNCHANGED

Applicable Local Execution Responsibility
→ ns_node / UNCHANGED
```

Therefore:

```text
Agent authors Automation candidate
!= Agent owns Automation semantics

Agent selects or composes Automation
!= Artifact Acceptance bypass

Agent requests Automation execution
!= Execution Admission bypass

Agent delegates applicable executable work
!= Node authority transfer

Node executes Automation / Flow Package
!= Node owns Automation Definition semantics
```

## 7. Product Interaction Direction Clarification

This checkpoint does **not** establish a general product requirement that Automation schedules, invokes or dispatches Agent execution.

The intended capability direction established here is:

```text
User Intent
→ Agent reasoning
→ existing or dynamically authored governed Automation capability
→ governed execution lifecycle
→ applicable Node execution
```

Cross-domain composition in any other direction remains subject to independent discovery and, where material, separate Owner/GAC governance.

## 8. Explicit Non-implications / Deferred Mechanics

This Owner capability decision does **not** decide:

```text
Automation DSL
Agent-to-Automation authoring API
candidate-definition physical representation
Flow Package format
package/reference transfer model
whether ns_agent physically sends a package to ns_node
whether ns_runtime is on the runtime path
build pipeline
compilation/generation model
parameter-binding schema
artifact packaging
version-binding strategy
synchronous vs asynchronous invocation
transport protocol
message schema
routing
retry
failure propagation
process topology
storage technology
```

It also does not create an `Ephemeral Automation` or parallel executable-definition class.

## 9. Offline / Private Deployment Consequence

Dynamic Agent-authored Automation must remain compatible with accepted private/offline lifecycle requirements.

Core correctness must not require a public SaaS control plane, public registry, online-only compiler/builder, public model provider, or mandatory Internet connectivity.

The resulting candidate Automation must still satisfy whatever governed evidence is required by the accepted offline execution lifecycle.

## 10. Compatibility / Re-delivery Consequence

Agent-authored candidate Automation Definitions are Automation-domain definitions for governance and compatibility purposes; they are not a separate semantic class merely because the authoring participant is an Agent.

```text
Different Authoring Participant
!= Different Automation Semantic Domain automatically
```

Compatibility/versioning/upgrade/re-delivery mechanics remain deferred to their named later design authority.

## 11. Revalidation Trigger

Revalidate this Owner capability decision if the Project Owner later changes one or more of:

- whether Agent may dynamically author a new candidate Automation Definition;
- whether such a candidate must enter normal Automation governance before execution;
- Automation Semantic Authority or Canonical Definition SoT;
- Artifact Acceptance or Execution Admission Authority;
- whether a separate ephemeral executable-flow semantic class is introduced.

Changes in concrete DSL, package format, transport, runtime routing, storage, framework or provider do not by themselves revalidate this capability decision.

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
