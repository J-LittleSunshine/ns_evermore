# NGRP-001 Phase Z3 / Batch 1 — Business Application Dual Authoring Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should Native Business Application Definition support complete source-code / System-level SDK authoring in addition to `ns_web` visual Business Application Builder authoring?

This is product-significant because it determines whether the first-class Business Application domain can participate fully in source-controlled development, review, automated delivery, customer secondary development and re-delivery without making the visual Builder the only complete construction path.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

This is a material product/developer-experience capability choice not fixed upstream. It does not move accepted Authority, SoT, Actual-state Ownership, Trust, Tenant, IAM, Policy, Artifact Acceptance or Execution Admission ownership.

## 3. Durable Mutually-exclusive Alternatives

### A — Visual Builder is the complete authoring surface

`ns_web` provides complete Native Business Application Definition authoring. The SDK supports integrations/extensions/custom capabilities but not complete Business Application Definition source authoring.

### B — Complete dual authoring

Native Business Application Definition supports complete source/SDK authoring and complete `ns_web` visual Builder authoring, both converging on the same governed Business Application semantic domain.

### C — Distinct Low-code and Pro-code Business Application classes

The product explicitly maintains visual/low-code and source/pro-code Business Application classes with potentially different capability profiles rather than one complete semantic domain exposed through two authoring surfaces.

## 4. Recommendation Presented

```text
Recommendation
→ B — Complete dual authoring
```

### Recommendation Rationale

Business Application is a first-class principal capability domain and the product already requires a complete System-level SDK, source-level extension, customer secondary development and re-delivery. Option B supports both low-code delivery and professional source workflows without creating separate application classes or making visual construction mandatory for advanced developers.

## 5. Tradeoffs and Impact

**Benefits**
- full Git/review/CI/CD/testing/headless/templating workflows for complete Business Applications;
- complete visual Builder remains available for low-code and delivery users;
- supports repeatable customer secondary development and re-delivery;
- avoids permanent asymmetry with other first-class authorable domains.

**Costs**
- source and visual authoring surfaces must remain semantically conformant across evolution;
- lifecycle, compatibility feedback and documentation must serve both authoring paths.

**Risks / Complexity**
- source and visual capability drift can create inconsistent application meaning;
- users may assume lossless round-trip or universal visual representability unless later guarantees are explicit;
- advanced source constructs may pressure Builder usability and representation design.

**Long-term Impact**
- Business Application remains a Pro-code + Low-code platform capability rather than a visual-only low-code domain;
- the product avoids maintaining two semantically divergent application classes by default.

**Compatibility / Migration Impact**
- both surfaces target the same governed Business Application semantic domain;
- exact cross-surface migration, code generation and round-trip guarantees remain deferred.

**Offline / Private Deployment Impact**
- both complete authoring paths must remain compatible with private/offline lifecycle correctness without mandatory public SaaS, public registry or Internet-only Builder dependency.

**Cross-component Impact**
- `ns_server` remains Business Application Semantic Authority and Canonical Definition SoT;
- `ns_web` and the System-level SDK are authoring surfaces only;
- Tenant/IAM/Policy/Trust/Artifact/Admission governance remains unchanged.

## 6. Project Owner Selected Result

```text
Selected Option
→ B

Native Business Application Definition Authoring Capability
→ COMPLETE_DUAL_AUTHORING_REQUIRED

Required Authoring Surfaces
→ System-level SDK / Source-code Authoring
→ ns_web Visual Builder Authoring

Same Governed Business Application Semantics
→ REQUIRED

Business Application Semantic Authority
→ ns_server / UNCHANGED

Business Application Canonical Definition SoT
→ ns_server / UNCHANGED
```

## 7. Normative Capability Consequence

```text
ns_server Business Application semantic domain
→ MUST support Native Business Application semantics authorable through both complete source/SDK and complete visual surfaces

System-level SDK
→ MUST support complete Native Business Application Definition source authoring

ns_web
→ MUST support complete Native Business Application visual construction / management
```

## 8. Authority / SoT / Actual-state Preservation

Business Application Semantic Authority and Canonical Definition SoT remain `ns_server`; UI editing does not become SoT; runtime actual-state remains governed by accepted bounded runtime partitions; Artifact Acceptance and Execution Admission authorities remain unchanged.

## 9. Explicit Non-implications

```text
Source Authoring != separate Business Application Authority
Visual Builder != ns_web Business Application Authority
Source Authoring != Artifact / Admission bypass
Visual Edit State != Canonical Definition SoT
Dual Authoring != lossless bidirectional round-trip
Dual Authoring != one mandatory physical representation
```

## 10. Deferred Mechanics / Named Later Authority

Not decided here: SDK API, Business Application DSL, visual schema, source/internal representation, source↔visual conversion/generation, round-trip guarantees, package/artifact format, build pipeline, runtime representation, cross-component API/protocol/message schema, repository/package layout, framework/provider/storage technology.

These remain for separately authorized Five-component Internal Architecture Boundary work, applicable Runtime Responsibility Architecture, Component Internal Design and later Contract/Foundation/Provider design where admitted. MDE-class changes return to Project Owner.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes complete source authoring, complete visual authoring, the shared governed semantic-domain requirement, Business Application Semantic Authority/Canonical Definition SoT, or the System-level SDK/development-surface requirement.

## 12. Bounded-session Authority Limit

This correction records the already selected Owner result only. It does not claim Global Acceptance, advance GAC state, authorize later batches, enter internal/runtime/Foundation design, or authorize Implementation Planning, IWP or coding.
