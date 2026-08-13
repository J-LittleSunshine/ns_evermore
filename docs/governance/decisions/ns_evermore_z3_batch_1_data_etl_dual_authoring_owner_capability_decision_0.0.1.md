# NGRP-001 Phase Z3 / Batch 1 — Data / Knowledge / Foundational ETL Dual Authoring Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `f4df0cdbbb1430ed16de0522a01198c264754d29`
- **Decision-predecessor HEAD:** `f4c5916f723b7389228a8bc9e081c642ab1e7f1f`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should native Enterprise Data / Knowledge / Foundational ETL definitions support complete source-code / System-level SDK authoring in addition to `ns_web` visual construction, or should complete Data/ETL authoring be limited to one surface or a deliberately bounded visual subset?

This is product-significant because it determines whether the first-class Data / Knowledge / Foundational ETL domain supports complete Pro-code and Low-code authoring, affecting enterprise delivery, customer secondary development, source-controlled change, repeatable re-delivery and long-term product positioning.

Accepted ownership remains unchanged:

```text
Enterprise Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server

Data / Knowledge factual SoT
→ governed per bounded semantic partition

Data / Knowledge UI
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
→ This is a material product capability / developer-and-delivery-experience boundary not explicitly fixed upstream.
→ It does not move Authority, Source of Truth, Actual-state Ownership, Tenant, IAM, Policy, Trust, Artifact Acceptance or Execution Admission ownership.
```

## 3. Durable Alternatives Presented

### Option A — Source-first complete Data / ETL authoring

System-level SDK / source authoring provides complete native Data/ETL definition authoring. `ns_web` provides management, configuration, monitoring, visualization and related UI but not complete visual Data/ETL authoring.

### Option B — Complete dual authoring

Native Data / Knowledge / Foundational ETL definitions support both:

```text
System-level SDK / Source-code Authoring
AND
ns_web Visual Data / ETL Authoring
```

Both authoring surfaces converge on the same governed native Data / Knowledge / Foundational ETL semantic domain under `ns_server` authority.

### Option C — Bounded visual subset + complete source authoring

Common delivery-oriented Data/ETL cases are visually authorable, while advanced/unrestricted Data/ETL definitions remain source-only. Visual and source capability profiles are intentionally not complete peers.

## 4. Recommendation Presented

`B — Complete dual authoring`.

Rationale:

- Enterprise Data / Knowledge / Foundational ETL is a first-class / parallel / non-subordinate product domain;
- the complete product already includes a System-level SDK / Development Surface;
- source-level extension, customer secondary development and customer re-delivery are accepted requirements;
- private enterprise delivery benefits materially from visual composition for common integration/mapping/transformation work while advanced developers need full source-control and automation capability;
- the same product may expose a practical two-layer mental model without making the visual Builder the only complete development route.

## 5. Project Owner Decision

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

## 6. Normative Capability Consequences for Z3 Batch 1

The Z3 Batch 1 capability baseline may consume:

```text
ns_server
→ MUST support native Data / Knowledge / Foundational ETL semantics that can be authored through both source-code/System-level SDK and ns_web visual authoring surfaces

System-level SDK / Development Surface
→ MUST support complete native Data / Knowledge / Foundational ETL source authoring

ns_web
→ MUST support complete native Data / Knowledge / Foundational ETL visual authoring / construction capability
```

Applicable product semantics may include, at capability level, authoring of source/ingestion intent, mapping, transformation, filtering, derivation, foundational ETL flow and dataset/knowledge-construction relationships where later accepted detailed semantics define them.

```text
Source Authoring
!= separate Data / ETL Semantic Authority

Visual Authoring
!= ns_web Data Authority

Authoring / Processing
!= factual Source-of-Truth transfer

ETL output
!= upstream source fact automatically
```

## 7. Explicit Non-implications / Deferred Mechanics

This decision does **not** decide:

```text
ETL DSL
visual node taxonomy
pipeline engine
connector API
SDK API
visual schema
source representation
source-to-visual conversion
visual-to-source generation
lossless bidirectional round-trip
whether every advanced source construct must be visually representable
physical pipeline representation
artifact/package format
execution representation
scheduler / worker / queue topology
transport / protocol / schema
specific database / warehouse / cache / vector / ETL / CDC technology
```

Named later authority:

```text
Five-component Internal Architecture Boundary Synthesis
→ only after separate GAC authorization

Runtime Responsibility Architecture
→ runtime scheduling/execution partition semantics where applicable

Component Internal Design
→ component-local realization after explicit authorization

Shared Foundation / Contract / Provider authorities
→ only for later-admitted reusable stable boundaries

Project Owner / MDE
→ any later proposal materially changing accepted Authority / SoT / Trust / major compatibility / stable identity / high-lock-in commitments
```

## 8. Offline / Private Deployment Consequence

Both complete authoring paths must remain compatible with accepted private/offline product lifecycle requirements and must not require mandatory public SaaS, public registry or Internet-only authoring/control-plane dependencies for core correctness.

## 9. Compatibility / Evolution Consequence

Both authoring surfaces target the same governed Data / Knowledge / Foundational ETL semantic domain across compatible evolution.

```text
Different Authoring Surface
!= Different Final Data / ETL Semantics automatically
```

Concrete cross-surface compatibility, migration and round-trip guarantees remain for later named design authority and may require GAC/MDE revalidation if material externally observable commitments are proposed.

## 10. Preserved Invariants

This decision preserves:

- exactly five Product Components;
- Data / Knowledge / Foundational ETL as a first-class / parallel / non-subordinate domain;
- `Data / Knowledge / ETL Semantic Authority → ns_server`;
- governed bounded factual SoT federation;
- `ns_web` editing/presentation not becoming Data Authority or factual SoT;
- System-level SDK not becoming a sixth Product Component or universal Authority;
- external bounded Source-of-Truth preservation;
- Definition / Artifact / Admission / Runtime separation where applicable;
- Tenant / IAM / Policy / Trust governance;
- offline/private correctness;
- extension/re-delivery governance;
- no premature internal architecture, runtime architecture, Shared Foundation, Contract, Module, Provider or implementation design.

## 11. Revalidation Trigger

Revalidate if the Project Owner later changes one or more of:

- complete native Data / Knowledge / Foundational ETL source authoring support;
- complete visual authoring support;
- the requirement that both surfaces converge on the same governed semantic domain;
- Data / Knowledge / ETL Semantic Authority;
- factual SoT topology;
- the System-level SDK/development-surface product requirement.

Changes in concrete SDK syntax, visual schema, ETL engine, connector implementation, database, provider, package, code generator, runtime process or deployment topology do not by themselves revalidate this capability decision.

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
