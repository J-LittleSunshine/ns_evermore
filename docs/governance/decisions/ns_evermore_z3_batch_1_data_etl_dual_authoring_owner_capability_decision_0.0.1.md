# NGRP-001 Phase Z3 / Batch 1 — Data / Knowledge / Foundational ETL Dual Authoring Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should Native Enterprise Data / Knowledge / Foundational ETL definitions support complete source-code / System-level SDK authoring in addition to `ns_web` visual construction, or should complete authoring be limited to one surface or a deliberately bounded visual subset?

This is product-significant because it determines whether this first-class domain supports complete Pro-code and Low-code authoring, directly affecting enterprise delivery, customer secondary development, source-controlled change, repeatable re-delivery and long-term product positioning.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

The decision selects a material authoring capability boundary but does not change Enterprise Data/Knowledge/ETL Semantic Authority, bounded factual SoT topology, Actual-state Ownership, Tenant, IAM, Policy, Trust, Artifact Acceptance or Execution Admission ownership.

## 3. Durable Mutually-exclusive Alternatives

### A — Source-first complete Data / ETL authoring

System-level SDK/source authoring provides complete native Data/ETL definition authoring. `ns_web` provides management/configuration/monitoring/visualization but not complete visual Data/ETL authoring.

### B — Complete dual authoring

Native Data / Knowledge / Foundational ETL definitions support complete System-level SDK/source authoring and complete `ns_web` visual authoring, both targeting the same governed native semantic domain.

### C — Bounded visual subset + complete source authoring

Common delivery-oriented Data/ETL cases are visually authorable, while advanced/unrestricted Data/ETL definitions remain source-only. Visual and source capability profiles are intentionally not complete peers.

## 4. Recommendation Presented

```text
Recommendation
→ B — Complete dual authoring
```

### Recommendation Rationale

Data / Knowledge / Foundational ETL is a first-class, parallel, non-subordinate product domain. Enterprise delivery benefits materially from complete visual composition, while advanced developers need complete source-control, automation and re-delivery. Option B preserves both without creating a permanent low-code subset as the only visual product boundary.

## 5. Tradeoffs and Impact

**Benefits**
- complete visual enterprise delivery for ingestion/mapping/transformation/ETL composition where later semantics permit;
- complete source workflows for Git, review, CI/CD, testing, templating and repeatable re-delivery;
- consistent Pro-code + Low-code posture across first-class authorable domains.

**Costs**
- two complete authoring surfaces require conformance and compatibility maintenance;
- complex data/ETL semantics must be communicated consistently to both developer and visual users.

**Risks / Complexity**
- advanced transformations may be difficult to represent visually without later UX/representation pressure;
- source/visual feature skew could create semantic divergence;
- users may assume round-trip guarantees that are not selected here.

**Long-term Impact**
- the Data/Knowledge/ETL domain remains a complete Pro-code + Low-code platform capability rather than source-only or visual-subset-only;
- visual authoring does not become a separate semantic domain.

**Compatibility / Migration Impact**
- both authoring surfaces target one governed semantic domain;
- concrete migration, source↔visual conversion and round-trip guarantees remain deferred.

**Offline / Private Deployment Impact**
- both authoring paths must remain usable under accepted private/offline lifecycle requirements without mandatory public authoring/control-plane services.

**Cross-component Impact**
- `ns_server` remains Data/Knowledge/ETL Semantic Authority;
- Data/Knowledge factual SoT remains governed per bounded semantic partition, including external SoT preservation;
- `ns_web` and SDK are authoring surfaces only.

## 6. Project Owner Selected Result

```text
Selected Option
→ B

Native Data / Knowledge / Foundational ETL Authoring Capability
→ COMPLETE_DUAL_AUTHORING_REQUIRED

Required Authoring Surfaces
→ System-level SDK / Source-code Authoring
→ ns_web Visual Authoring

Same Governed Data / ETL Semantics
→ REQUIRED

Enterprise Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server / UNCHANGED

Data / Knowledge Factual SoT Topology
→ governed per bounded semantic partition / UNCHANGED
```

## 7. Normative Capability Consequence

`ns_server` must support native Data/Knowledge/Foundational ETL semantics authorable through both complete source/SDK and complete visual surfaces; SDK must support complete source authoring; `ns_web` must support complete visual authoring/construction. Authoring or processing does not transfer factual SoT.

## 8. Authority / SoT / Actual-state Preservation

```text
Data / Knowledge / ETL Semantic Authority
→ ns_server

Data / Knowledge factual SoT
→ per accepted bounded semantic partition

ETL Output
!= upstream Source Fact automatically

Runtime Actual-state Ownership
→ unchanged per accepted bounded runtime partition
```

## 9. Explicit Non-implications

```text
Source Authoring != separate Data/ETL Authority
Visual Authoring != ns_web Data Authority
Authoring / Processing != factual SoT transfer
Dual Authoring != lossless round-trip
Dual Authoring != one mandatory physical pipeline representation
```

## 10. Deferred Mechanics / Named Later Authority

Not decided here: ETL DSL, visual node taxonomy, pipeline engine, connector API, SDK API, visual/source representation, conversion/generation, round-trip, package/artifact/execution representation, scheduler/worker/queue topology, transport/protocol/schema, database/warehouse/cache/vector/CDC technology.

These remain for separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture where applicable, Component Internal Design, and later Foundation/Contract/Provider work only if admitted. MDE-class changes return to Project Owner.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes complete source authoring, complete visual authoring, the shared governed semantic-domain rule, Data/Knowledge/ETL Semantic Authority, factual SoT topology, or the System-level SDK requirement.

## 12. Bounded-session Authority Limit

This evidence correction preserves the already selected result and does not claim Global Acceptance, advance GAC state, authorize later Z3 batches, or enter internal/runtime/Foundation/implementation design.
