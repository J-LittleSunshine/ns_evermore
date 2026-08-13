# NGRP-001 Phase Z3 / Batch 1 — Reusable Automation Composition Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should a Native Automation Definition be able to natively reference, invoke and reuse another Native Automation Definition as a governed product capability, or should Automation Definitions remain independent execution units whose composition is performed only by external Business Application / Agent / integration logic?

This is product-significant because it determines whether Automation can become a reusable composable enterprise asset model rather than encouraging copied workflow logic or glue orchestration outside the Automation domain.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

The capability materially expands Automation composition but does not move Authority, SoT, Actual-state Ownership, Trust, Artifact Acceptance, Execution Admission, Tenant, IAM, Policy or runtime ownership.

## 3. Durable Mutually-exclusive Alternatives

### A — Independent Automation Definitions

Native Automation Definitions remain independent. Reuse/composition is performed by Business Application, Agent, integration code or another external caller.

### B — Native Reusable Automation Composition

A Native Automation Definition may, under governed semantics, reference, invoke and reuse another Native Automation Definition.

### C — Strict Hierarchical Subflow Only

Native Automation supports only a permanently hierarchical Parent Automation → Child/Subflow model rather than general reusable Automation-to-Automation composition.

## 4. Recommendation Presented

```text
Recommendation
→ B — Native Reusable Automation Composition
```

### Recommendation Rationale

Option B avoids workflow copying/divergence, allows reusable enterprise Automation assets and layered decomposition, and keeps Automation composition inside its own first-class domain instead of forcing Business Application or glue code to own it. It does so without selecting a DAG/subflow/runtime realization.

## 5. Tradeoffs and Impact

**Benefits**
- reusable Automation assets reduce duplicated workflow logic and version divergence;
- improves modular testing, customer secondary development and re-delivery;
- supports larger Automation definitions through governed composition.

**Costs**
- later design must manage dependency/revision compatibility and composed lifecycle visibility;
- testing, diagnostics and provenance must account for caller/callee Automation relationships.

**Risks / Complexity**
- cycles/recursive composition, binding ambiguity and failure propagation require later explicit treatment;
- silent latest-version binding or implicit lifecycle sharing could create unsafe compatibility behavior;
- composition must not become an Artifact/Admission bypass.

**Long-term Impact**
- Automation becomes a composable enterprise Automation asset platform rather than a set of isolated workflows;
- general reuse is not permanently constrained to a strict parent-child hierarchy.

**Compatibility / Migration Impact**
- caller and referenced Automation revisions may evolve independently and require explicit supported/unsupported/incompatible semantics;
- exact binding/version-range/migration rules remain deferred.

**Offline / Private Deployment Impact**
- reusable composition must remain resolvable under private/offline correctness without mandatory public registries or SaaS orchestration;
- disconnected composition cannot bypass Tenant/IAM/Policy/Trust/Artifact/Admission governance.

**Cross-component Impact**
- `ns_server` remains Automation Semantic Authority and Definition SoT;
- SDK and `ns_web` must later be able to express the accepted composition semantics;
- `ns_runtime` may later coordinate runtime execution and `ns_node` may execute applicable work, without either gaining Automation authority.

## 6. Project Owner Selected Result

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

## 7. Normative Capability Consequence

Automation must support governed reusable Automation-to-Automation composition. Complete source and visual authoring surfaces must later be capable of expressing applicable accepted composition semantics.

## 8. Authority / SoT / Actual-state Preservation

Automation Semantic Authority/Definition SoT remain `ns_server`; Artifact Acceptance and Execution Admission remain distinct accepted authorities; runtime actual-state remains partitioned; `ns_runtime` coordination and `ns_node` execution do not gain Automation authority.

## 9. Explicit Non-implications

```text
Automation A invokes Automation B != Authority transfer
Composition != Artifact Acceptance bypass
Composition != Execution Admission bypass
Referenced Automation exists != automatically executable
Reuse != same lifecycle state
Composition != Business Application Authority
Composition != ns_runtime Automation Authority
```

## 10. Deferred Mechanics / Named Later Authority

Not decided here: subflow schema, DAG/graph representation, recursion, cycle policy, parameter binding, sync/async invocation, call-stack semantics, transaction model, failure propagation/retry, runtime routing/process topology, artifact/package format or cross-component protocol.

These remain for separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture, Component Internal Design and later Contract/Foundation work if admitted. MDE-class changes return to Project Owner.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes reusable Automation composition, Automation Authority/SoT, or the requirement that composition cannot bypass Artifact/Admission governance.

## 12. Bounded-session Authority Limit

This evidence correction preserves the already selected result and does not claim Global Acceptance, advance GAC state, authorize later batches or enter downstream architecture/design/implementation work.
