# NGRP-001 Phase Z3 / Batch 1 — Reusable Automation Composition Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should a Native Automation Definition be able to natively reference, invoke, and reuse another Native Automation Definition as a governed product capability, or should Automation Definitions remain independent execution units whose composition is performed only by external Business Application / Agent / integration logic?

The question is product-significant because it determines whether Automation can become a reusable, composable enterprise automation asset model rather than encouraging copied workflow logic or glue orchestration outside the Automation domain.

It does not reopen accepted ownership:

```text
Automation Definition / Workflow Semantic Authority
→ ns_server

Automation Canonical Definition SoT
→ ns_server

Automation visual authoring
→ ns_web

Automation source authoring
→ System-level SDK / Development Surface

Applicable local execution
→ ns_node
```

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

The capability does not move Authority, SoT, Actual-state Ownership, Trust, Artifact Acceptance, Execution Admission, Tenant, IAM, Policy or runtime ownership.

## 3. Durable Alternatives Presented

### Option A — Independent Automation Definitions

Native Automation Definitions remain independent. Reuse/composition is performed by Business Application, Agent, integration code or another external caller.

### Option B — Native Reusable Automation Composition

A Native Automation Definition may, under governed semantics, reference, invoke and reuse another Native Automation Definition.

### Option C — Strict Hierarchical Subflow Only

Native Automation supports only a permanently hierarchical Parent Automation → Child/Subflow model rather than general reusable Automation-to-Automation composition.

## 4. Recommendation Presented

`B — Native Reusable Automation Composition`.

Rationale:

- avoids workflow copying and divergence;
- enables reusable enterprise Automation assets;
- supports layered decomposition, testing, customer secondary development and re-delivery;
- preserves the Automation domain as first-class instead of moving composition into Business Application or glue code;
- does not require any concrete graph/subflow/runtime realization in this Batch.

## 5. Project Owner Decision

```text
Selected Option
→ B

Native Automation Composition Capability
→ REUSABLE_AUTOMATION_COMPOSITION_REQUIRED

Automation Definition
→ MAY reference / invoke / reuse another governed Automation Definition

Automation Semantic Authority
→ ns_server / UNCHANGED

Automation Canonical Definition SoT
→ ns_server / UNCHANGED
```

## 6. Normative Capability Consequences

The Z3 Batch 1 capability baseline may consume:

```text
Automation
→ MUST support governed reusable Automation-to-Automation composition

System-level SDK / Source Authoring
→ MUST be able to express applicable reusable Automation composition semantics later

ns_web Visual Authoring
→ MUST be able to express applicable reusable Automation composition semantics later
```

Permanent non-transfer rules:

```text
Automation A invokes Automation B
!= Authority Transfer

Composition
!= Artifact Acceptance bypass

Composition
!= Execution Admission bypass

Referenced Automation exists
!= Referenced Automation is automatically executable

Reuse
!= Same lifecycle state

Automation Composition
!= Business Application Authority

Automation Composition
!= ns_runtime Automation Semantic Authority
```

## 7. Explicit Non-implications / Deferred Mechanics

This Owner capability decision does **not** decide:

```text
subflow schema
DAG / graph representation
recursive invocation
cycle policy
parameter binding
sync / async invocation
call-stack semantics
transaction model
failure propagation algorithm
retry algorithm
runtime routing
runtime process topology
artifact/package format
cross-component protocol
```

Named later authority remains the separately authorized Five-component Internal Architecture Boundary / Runtime Responsibility / Component Internal Design / Contract authorities as applicable.

## 8. Offline / Private Deployment Consequence

Reusable Automation composition must remain compatible with private/offline correctness. A composed Automation must not rely on mandatory public registries, SaaS orchestration or online-only resolution as a core correctness dependency.

Composition does not permit bypassing Tenant/IAM/Policy/Trust/Artifact/Admission governance when disconnected.

## 9. Compatibility / Migration Consequence

A caller Automation and a referenced Automation may evolve independently, so later design must provide explicit revision/compatibility/unsupported semantics sufficient to prevent silent reinterpretation.

This decision does not select exact binding or version-range rules.

## 10. Preserved Invariants

This decision preserves:

- exactly five Product Components;
- Automation as a first-class / parallel / non-subordinate domain;
- `Automation Semantic Authority → ns_server`;
- `Automation Canonical Definition SoT → ns_server`;
- Definition / Artifact / Admission / Runtime separation;
- `ns_runtime` scheduling/dispatch not gaining Automation authority;
- `ns_node` execution not gaining Automation authority;
- SDK/Web dual authoring convergence;
- offline/private correctness;
- no premature internal/runtime/Foundation/implementation design.

## 11. Revalidation Trigger

Revalidate if the Project Owner later changes one or more of:

- Native Automation reusable composition support;
- Automation Definition / Semantic Authority;
- Automation Canonical Definition SoT;
- the requirement that composition cannot bypass Artifact/Admission governance.

Changes in graph representation, orchestration library, scheduler, process topology, API, package format or transport do not by themselves revalidate this product capability decision.

## 12. Bounded-session Authority Limit

This evidence does not constitute GAC Global Acceptance, does not advance the GAC Epoch, does not authorize Z3 Batch 2, and does not begin internal architecture, Runtime Responsibility Architecture, Shared Foundation Architecture, Foundation design, Implementation Planning, IWP or coding.
