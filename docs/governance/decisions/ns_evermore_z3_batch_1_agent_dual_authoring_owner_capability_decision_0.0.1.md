# NGRP-001 Phase Z3 / Batch 1 — AI Agent Dual Authoring Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should Native AI Agent Definition support complete source-code / System-level SDK authoring in addition to `ns_web` visual construction, or should complete Agent construction remain primarily visual with source development limited to extensions?

This is product-significant because it determines whether Native Agent development is fully available to source-controlled, reviewable, automatable, customer-secondary-development and re-delivery workflows, rather than making the visual Builder the only complete authoring path.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

This decision changes a product/developer-experience capability boundary but does not move accepted Semantic Authority, Source of Truth, Actual-state Ownership, Trust, Tenant, IAM, Policy, Artifact Acceptance or Execution Admission ownership. Any later proposal that changes those dimensions remains separately MDE-governed.

## 3. Durable Mutually-exclusive Alternatives

### A — Visual-only complete Native Agent authoring

`ns_web` is the only complete Native Agent Definition authoring surface. The System-level SDK may support integrations/extensions/tools/providers but not complete Native Agent Definition source authoring.

### B — Complete dual authoring

Native Agent Definition supports both complete System-level SDK/source-code authoring and complete `ns_web` visual authoring. Both surfaces target the same governed Native Agent semantic domain.

### C — Visual complete composition + source-level extension authoring

Complete Native Agent composition remains visual. Source development is supported for reusable Agent extensions/tools/providers/capabilities, but not for complete Native Agent Definition authoring.

## 4. Recommendation Presented

```text
Recommendation
→ B — Complete dual authoring
```

### Recommendation Rationale

AI Agent is a first-class principal capability domain; the complete product already requires a System-level SDK, source-level extension, customer secondary development and re-delivery. Option B preserves a low-code visual path while preventing advanced development from being structurally locked to the Builder. It also avoids treating the Agent domain differently from other first-class authorable domains without changing Agent Authority or SoT.

## 5. Tradeoffs and Impact

**Benefits**
- complete Git/source-control, review, CI/CD, automated testing and headless Agent-definition workflows;
- complete visual authoring remains available to delivery/business/low-code users;
- supports customer secondary development and repeatable private/offline re-delivery;
- permits a two-layer product mental model while retaining an advanced source-only path.

**Costs**
- two complete authoring surfaces must remain semantically conformant across evolution;
- compatibility validation and product documentation must account for source and visual entry paths.

**Risks / Complexity**
- source and visual feature sets can drift if conformance is weak;
- users may infer unsupported round-trip guarantees unless those guarantees are explicitly defined later;
- advanced source constructs may create representation pressure for the visual surface.

**Long-term Impact**
- `ns_agent` remains a Pro-code + Low-code Agent platform rather than a visual-only platform;
- the visual Builder is a first-class authoring surface, not the sole legal definition entry point.

**Compatibility / Migration Impact**
- both surfaces must continue to target one governed Agent semantic domain;
- lossless source↔visual round-trip, one physical representation, and exact migration guarantees are not established here.

**Offline / Private Deployment Impact**
- complete source authoring and visual authoring must remain compatible with private/offline lifecycle correctness;
- no mandatory public SaaS control plane, public registry, Internet-only Builder, or public model provider may be required for core correctness.

**Cross-component Impact**
- System-level SDK and `ns_web` participate as authoring surfaces;
- `ns_agent` remains AI Agent Semantic Authority and Canonical Definition SoT;
- `ns_server` Tenant/IAM/Policy/Trust/Artifact/Admission authority remains unchanged.

## 6. Project Owner Selected Result

```text
Selected Option
→ B

Native AI Agent Definition Authoring Capability
→ COMPLETE_DUAL_AUTHORING_REQUIRED

Required Authoring Surfaces
→ System-level SDK / Source-code Authoring
→ ns_web Visual Authoring

Same Governed Agent Semantics
→ REQUIRED

AI Agent Semantic Authority
→ ns_agent / UNCHANGED

AI Agent Canonical Definition SoT
→ ns_agent / UNCHANGED
```

## 7. Normative Capability Consequence

```text
ns_agent
→ MUST support Native Agent semantics authorable through both complete source/SDK and complete visual surfaces

System-level SDK / Development Surface
→ MUST support complete Native Agent Definition source authoring

ns_web
→ MUST support complete Native Agent Definition visual construction / management
```

Different authoring surfaces do not create different Agent semantic authorities.

## 8. Authority / SoT / Actual-state Preservation

```text
AI Agent Semantic Authority
→ ns_agent

AI Agent Canonical Definition SoT
→ ns_agent

Runtime Actual-state Ownership
→ remains governed per accepted bounded runtime semantic partition

Artifact Acceptance / Execution Admission
→ remain accepted ns_server authorities
```

## 9. Explicit Non-implications

```text
Source Authoring != separate Agent Authority
Visual Authoring != ns_web Agent Authority
Source Authoring != Artifact / Admission bypass
Visual Editing != Canonical Agent Definition SoT
Dual Authoring != lossless bidirectional round-trip
Dual Authoring != one mandatory physical representation
```

## 10. Deferred Mechanics / Named Later Authority

Not decided here: SDK API, Agent DSL, visual schema, JSON/YAML/TOML/Python representation, internal representation, source-to-visual conversion, visual-to-source generation, round-trip guarantees, package/artifact format, build/generation pipeline, Agent runtime representation, cross-component API/protocol/message schema, runtime routing, provider/framework/storage technology.

Named later authorities remain separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture where applicable, Component Internal Design, and later Contract/Foundation/Provider authorities only if admitted. Material Authority/SoT/Trust/major compatibility/stable-identity/high-lock-in changes return to Project Owner/MDE governance.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes complete source authoring support, complete visual authoring support, the one-governed-Agent-semantic-domain requirement, AI Agent Semantic Authority/Canonical Definition SoT, or the system-level SDK/development-surface product requirement.

Concrete SDK syntax, schema, framework, provider, package, code generator, storage, runtime process or deployment topology do not by themselves trigger revalidation.

## 12. Bounded-session Authority Limit

This evidence correction records the already selected Owner result only. It does not constitute GAC Global Acceptance, advance a GAC Epoch, authorize any later Z3 Batch, begin Five-component Internal Architecture Boundary synthesis, Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Architecture, Foundation Contract/Module/Provider Design, Implementation Planning, IWP, or coding.
