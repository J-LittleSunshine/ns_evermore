# NGRP-001 Phase Z3 / Batch 1 — AI Agent Dual Authoring Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `f4df0cdbbb1430ed16de0522a01198c264754d29`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should native AI Agent Definition support complete source-code / System-level SDK authoring in addition to `ns_web` visual construction, or should complete Agent construction remain primarily visual with source development limited to extensions?

This question is product-significant because it determines whether native Agent development remains fully available to source-controlled, reviewable, automatable, customer-secondary-development and re-delivery workflows, rather than making the visual Builder the only complete authoring path.

It does not reopen or change accepted Project Architecture ownership:

```text
AI Agent Definition / Semantic Authority
→ ns_agent

AI Agent Canonical Definition SoT
→ ns_agent

Agent visual construction / management UI
→ ns_web

System-level SDK / Development Surface
→ complete-system development surface
```

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO

Reason
→ This is a material product capability / developer-experience boundary not explicitly fixed upstream.
→ It does not move Authority, Source of Truth, Actual-state Ownership, Trust, Tenant, IAM, Policy, Artifact Acceptance or Execution Admission ownership.
```

## 3. Durable Alternatives Presented

### Option A — Visual-only complete Native Agent authoring

`ns_web` provides the complete Native Agent Definition authoring surface. The System-level SDK may support integrations/extensions but not complete Native Agent Definition source authoring.

### Option B — Complete dual authoring

Native Agent Definition supports both:

```text
System-level SDK / Source-code Authoring
AND
ns_web Visual Authoring
```

Both authoring surfaces converge on the same governed Native Agent semantic domain. `ns_agent` remains the single AI Agent Semantic Authority and Canonical Definition SoT.

### Option C — Visual Native Agent composition + source-level extension authoring

Complete Native Agent composition remains visual. Source development is supported for reusable Agent extensions/tools/providers/capabilities but not for complete Native Agent Definition authoring.

## 4. Recommendation Presented

`B — Complete dual authoring`.

Rationale:

- AI Agent is a first-class principal capability domain;
- the complete product already includes a System-level SDK / Development Surface;
- source-level extension, customer secondary development and customer re-delivery are accepted product requirements;
- `ns_web` visual authoring remains appropriate for low-code users, while advanced developers should not be structurally locked to the visual Builder;
- dual authoring supports source control, review, automated delivery, headless development and private/offline re-delivery without changing Agent Authority / SoT.

The recommended product experience may still present a practical two-layer mental model:

```text
Layer 1
→ source-code development of reusable Tool / Extension / Provider / Agent capabilities

Layer 2
→ ns_web visual Agent composition for delivery / business / low-code users
```

while preserving an advanced source-only path capable of defining a complete Native Agent.

## 5. Project Owner Decision

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

## 6. Normative Capability Consequences for Z3 Batch 1

The Z3 Batch 1 capability baseline may consume the following Owner-decided product capability:

```text
ns_agent
→ MUST support Native Agent semantics that can be authored through both source-code/System-level SDK and ns_web visual authoring surfaces

System-level SDK / Development Surface
→ MUST support complete Native Agent Definition source authoring as a product development capability

ns_web
→ MUST support complete Native Agent Definition visual construction / management as a product capability
```

Both surfaces must converge on the same governed Agent semantic domain.

```text
Source Authoring
!= separate Agent Semantic Authority

Visual Authoring
!= ns_web Agent Semantic Authority

Source Authoring
!= Artifact / Admission bypass

Visual Authoring
!= Canonical Agent Definition SoT
```

## 7. Explicit Non-implications / Deferred Mechanics

This Owner capability decision does **not** decide:

```text
SDK API
Agent DSL
visual schema
JSON / YAML / TOML / Python representation
internal Agent representation
source-to-visual conversion mechanism
visual-to-source generation mechanism
lossless bidirectional round-trip
whether both surfaces use one physical representation
whether every advanced source construct must be visually representable
package / artifact format
build / generation pipeline
Agent runtime representation
cross-component API / protocol / message schema
runtime routing
provider / framework / storage technology
```

Named later authority:

```text
Five-component Internal Architecture Boundary Synthesis
→ only after separate GAC authorization

Component Internal Design
→ component-local realization after explicit authorization

Foundation / Contract / Provider authorities
→ only where later accepted architecture places reusable or stable cross-boundary semantics

Project Owner / MDE
→ if a later proposal materially changes accepted Authority / SoT / Trust / major compatibility / major stable identity / high-lock-in commitments
```

## 8. Offline / Private Deployment Consequence

Dual authoring must remain compatible with accepted private/offline product lifecycle requirements. Complete source authoring must not require a mandatory public SaaS control plane, public registry, online-only Builder, or mandatory Internet provider for core correctness.

This does not require the visual and source authoring implementations to be identical.

## 9. Compatibility / Evolution Consequence

Both authoring surfaces must continue to target the same governed Agent semantic domain across compatible evolution.

```text
Different Authoring Surface
!= Different Final Agent Semantics automatically
```

Concrete cross-surface compatibility, migration and round-trip guarantees remain deferred to the named later design authority and may require GAC/MDE revalidation if a material externally observable compatibility commitment is proposed.

## 10. Preserved Invariants

This decision preserves:

- exactly five Product Components;
- AI Agent as a first-class / parallel / non-subordinate domain;
- `AI Agent Semantic Authority → ns_agent`;
- `AI Agent Canonical Definition SoT → ns_agent`;
- `ns_web` UI state / editing not becoming Agent Authority or canonical SoT;
- System-level SDK not becoming a sixth Product Component or universal Authority;
- Definition / Artifact / Admission / Runtime separation;
- Tenant / IAM / Policy / Trust / Artifact / Admission governance;
- offline/private correctness;
- extension/re-delivery governance;
- no premature internal architecture, runtime architecture, Shared Foundation, Contract, Module, Provider or implementation design.

## 11. Revalidation Trigger

Revalidate this Owner capability decision if the Project Owner later changes one or more of:

- complete Native Agent Definition source authoring support;
- complete Native Agent Definition visual authoring support;
- the requirement that both surfaces converge on the same governed Agent semantic domain;
- AI Agent Semantic Authority or Canonical Definition SoT;
- the system-level SDK/development-surface product requirement.

Changes in concrete SDK syntax, visual schema, framework, provider, package, code generator, storage, runtime process or deployment topology do not by themselves revalidate this capability decision.

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
