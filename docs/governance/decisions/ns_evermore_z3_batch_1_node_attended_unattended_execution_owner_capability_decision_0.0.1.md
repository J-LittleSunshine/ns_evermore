# NGRP-001 Phase Z3 / Batch 1 — Node Attended and Unattended Execution Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Pre-decision HEAD:** `4cbe7336c5842cb35bcd91fa9be44f18e33f87da`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should `ns_node` formally support only unattended/managed local execution, only bounded attended execution, or both attended and unattended execution as first-class native product capabilities?

This question is product-significant because `ns_node` already owns applicable local execution, desktop/browser automation, package/plugin/tool/workflow execution, local resource/file/device interaction, offline/degraded continuity, and local protected-effect/source-fact production. The product capability baseline therefore must state whether execution may occur both in managed unattended environments and in a legitimate current-user interactive session.

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

The question does not move Tenant/IAM/Policy/Trust/Artifact Acceptance/Execution Admission Authority, Automation Semantic Authority, or local protected-effect ownership.

## 3. Owner Decision

```text
Selected Option
→ B

ns_node Attended Execution
→ FIRST_CLASS_REQUIRED

ns_node Unattended Execution
→ FIRST_CLASS_REQUIRED

Combined Product Capability
→ ATTENDED_AND_UNATTENDED_LOCAL_EXECUTION_REQUIRED
```

## 4. Normative Capability Consequences for Z3 Batch 1

The Z3 Batch 1 capability baseline may consume the following Owner-decided product capability:

```text
ns_node
→ MUST support applicable governed unattended local execution
→ MUST support applicable governed attended local execution associated with a legitimate user/session context
→ MUST preserve local execution and protected-effect/source-fact responsibility in both modes
```

Representative product-level usage pressure includes:

```text
scheduled / event-driven / otherwise governed Automation
→ unattended execution where applicable

user / Agent initiated Automation
→ attended local execution where applicable

human interaction required during execution
→ may participate in the accepted governed Human-in-the-loop capability
```

These examples do not define concrete runtime routing or execution topology.

## 5. Preserved Governance Boundaries

```text
Attended Execution
!= IAM / Policy bypass

Current User Presence
!= Execution Admission bypass

Unattended Execution
!= unrestricted machine authority

Current Desktop Session
!= Tenant / Principal ambiguity allowed

ns_node Execution
!= Automation Semantic Authority

ns_node Local Possession
!= Artifact Acceptance Authority

ns_node Local Execution
!= Execution Admission Authority
```

All accepted Definition / Artifact / Admission / Runtime separation remains preserved.

## 6. Explicit Deferrals

This decision does **not** decide:

```text
Windows session model
Linux desktop/session model
RDP / VDI behavior
service account model
user-session attachment mechanism
session isolation
process / worker topology
browser profile model
interactive desktop acquisition
concurrency model
lock-screen behavior
logout behavior
session-loss recovery
credential handling mechanism
transport / protocol
runtime routing
container / VM / host topology
```

These remain assigned to later explicitly authorized runtime/component/internal design authorities.

## 7. Offline / Private Deployment Consequence

Both execution modes must remain compatible with accepted private/offline product requirements where applicable. Neither attended nor unattended execution may require mandatory public SaaS, public registry, public control plane, or online-only licensing for core correctness.

## 8. Revalidation Trigger

Revalidate this Owner capability decision if the Project Owner later changes whether attended or unattended local execution is a first-class `ns_node` product capability, or if a later proposal would materially move accepted Authority / SoT / Trust / Admission / protected-effect ownership.

## 9. Bounded-session Authority Limit

This evidence records one Project Owner capability decision inside Z3 Batch 1. It does not constitute GAC Global Acceptance, advance GAC Epoch, authorize Z3 Batch 2, complete Z3 Batch 1, enter Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Architecture, Foundation Contract/Module/Provider Design, Implementation Planning, IWP, or coding.
