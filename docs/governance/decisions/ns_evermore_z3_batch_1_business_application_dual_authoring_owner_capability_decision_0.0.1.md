# NGRP-001 Phase Z3 / Batch 1 — Business Application Dual Authoring Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `f4df0cdbbb1430ed16de0522a01198c264754d29`
- **Decision-predecessor HEAD:** `c71c69c997640ecdea36db54a35ab751a0b13aa3`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should native Business Application Definition support complete source-code / System-level SDK authoring in addition to `ns_web` visual Business Application Builder authoring?

This question is product-significant because it determines whether the first-class Business Application capability can participate fully in source-controlled development, review, automated delivery, customer secondary development and re-delivery without making the visual Builder the only complete construction path.

It does not reopen or change accepted Project Architecture ownership:

```text
Business Application Definition / Platform Semantic Authority
→ ns_server

Business Application Canonical Definition SoT
→ ns_server

Business Application visual Builder / UI
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

### Option A — Visual Builder is the complete Business Application authoring surface

`ns_web` provides the complete Native Business Application Definition authoring surface. The System-level SDK may support integrations/extensions/custom capabilities but not complete Native Business Application Definition source authoring.

### Option B — Complete dual authoring

Native Business Application Definition supports both:

```text
System-level SDK / Source-code Authoring
AND
ns_web Visual Builder Authoring
```

Both authoring surfaces converge on the same governed Native Business Application semantic domain. `ns_server` remains the single Business Application Semantic Authority and Canonical Definition SoT.

### Option C — Distinct Visual/Low-code and Source/Pro-code Business Application classes

The product explicitly distinguishes visually authored and source-authored Business Application classes with potentially different capability profiles rather than requiring both surfaces to target one complete semantic capability set.

## 4. Recommendation Presented

`B — Complete dual authoring`.

Rationale:

- Business Application is a first-class principal capability domain;
- the complete product already includes a System-level SDK / Development Surface;
- source-level extension, customer secondary development and customer re-delivery are accepted product requirements;
- complete source authoring supports Git-based review, CI/CD, automated testing, headless development, templating, repeatable customer delivery and private/offline development;
- `ns_web` visual authoring remains appropriate for delivery / business / low-code users;
- dual authoring avoids an unnecessary long-term asymmetry where Automation and AI Agent can be authored completely through source while Business Application cannot;
- no Authority / SoT transfer is required.

The product experience may still present a practical two-layer mental model:

```text
Layer 1
→ source-code development of reusable capabilities / integrations / extensions

Layer 2
→ ns_web visual Business Application composition for delivery / business / low-code users
```

while preserving an advanced source-only path capable of defining a complete Native Business Application.

## 5. Project Owner Decision

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

## 6. Normative Capability Consequences for Z3 Batch 1

The Z3 Batch 1 capability baseline may consume the following Owner-decided product capability:

```text
ns_server Business Application semantic domain
→ MUST support Native Business Application semantics that can be authored through both source-code/System-level SDK and ns_web visual Builder surfaces

System-level SDK / Development Surface
→ MUST support complete Native Business Application Definition source authoring as a product development capability

ns_web
→ MUST support complete Native Business Application visual construction / management as a product capability
```

Both surfaces must converge on the same governed Business Application semantic domain.

```text
Source Authoring
!= separate Business Application Semantic Authority

Visual Authoring
!= ns_web Business Application Semantic Authority

Source Authoring
!= Artifact / Admission bypass

Visual Authoring
!= Canonical Business Application Definition SoT
```

## 7. Explicit Non-implications / Deferred Mechanics

This Owner capability decision does **not** decide:

```text
SDK API
Business Application DSL
visual schema
JSON / YAML / TOML / Python representation
internal Business Application representation
source-to-visual conversion mechanism
visual-to-source generation mechanism
lossless bidirectional round-trip
whether both surfaces use one physical representation
whether every advanced source construct must be visually representable
package / artifact format
build / generation pipeline
Business Application runtime representation
cross-component API / protocol / message schema
repository / package layout
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

Complete dual authoring must remain compatible with accepted private/offline product lifecycle requirements. Complete source authoring must not require a mandatory public SaaS control plane, public registry, online-only Builder, or mandatory Internet provider for core correctness.

This does not require visual and source authoring implementations to be identical.

## 9. Compatibility / Evolution Consequence

Both authoring surfaces must continue to target the same governed Business Application semantic domain across compatible evolution.

```text
Different Authoring Surface
!= Different Final Business Application Semantics automatically
```

Concrete cross-surface compatibility, migration and round-trip guarantees remain deferred to named later design authority and may require GAC/MDE revalidation if a material externally observable compatibility commitment is proposed.

## 10. Preserved Invariants

This decision preserves:

- exactly five Product Components;
- Business Application as a first-class / parallel / non-subordinate domain;
- `Business Application Semantic Authority → ns_server`;
- `Business Application Canonical Definition SoT → ns_server`;
- `ns_web` UI state / editing not becoming Business Application Authority or canonical SoT;
- System-level SDK not becoming a sixth Product Component or universal Authority;
- Definition / Artifact / Admission / Runtime separation;
- Tenant / Organization / IAM / Policy / Trust / Artifact / Admission governance;
- bounded external Source-of-Truth preservation;
- offline/private correctness;
- extension/re-delivery governance;
- no premature internal architecture, runtime architecture, Shared Foundation, Contract, Module, Provider or implementation design.

## 11. Revalidation Trigger

Revalidate this Owner capability decision if the Project Owner later changes one or more of:

- complete Native Business Application Definition source authoring support;
- complete Native Business Application visual authoring support;
- the requirement that both surfaces converge on the same governed Business Application semantic domain;
- Business Application Semantic Authority or Canonical Definition SoT;
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
