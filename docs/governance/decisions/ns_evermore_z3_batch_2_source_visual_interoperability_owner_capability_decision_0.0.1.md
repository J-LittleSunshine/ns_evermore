# NGRP-001 Phase Z3 / Batch 2 — Source / Visual Authoring Interoperability Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **MDE Classification:** `YES`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Current Global State at Decision:** `GAC-EPOCH-0022`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

What long-term product guarantee SHALL govern interoperability between the already-required complete System-level SDK/source authoring surface and the already-required complete `ns_web` visual authoring surface for the four first-class authorable domains:

```text
Business Application
Automation
Native AI Agent
Data / Knowledge / Foundational ETL
```

The accepted Z3 Batch 1 capability baseline already requires complete dual authoring for all four domains and requires both surfaces to target the same governed domain semantics. However, the accepted Owner evidence explicitly states that complete dual authoring does **not** automatically imply lossless bidirectional source↔visual round-trip, one mandatory physical representation, or exact source/visual conversion guarantees.

This Batch therefore must decide the product-level interoperability commitment before later internal-boundary work can safely allocate authoring interaction responsibilities.

---

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ YES
```

### Why Product-significant

The decision materially affects:

```text
Developer workflow
Delivery workflow
Customer secondary development
Customer re-delivery
Low-code / Pro-code collaboration
Cross-surface compatibility expectations
Definition evolution
Migration obligations
Long-term product complexity
```

The choice determines whether source-authored and visually-authored definitions are merely two independent entry paths, semantically interoperable authoring surfaces, or fully lossless reversible representations.

### Why MDE

This matter does not move current Product Definition Semantic Authority or Canonical Definition SoT. It is nevertheless MDE-class because it establishes a major externally observable compatibility commitment across four first-class product domains and may create substantial long-term migration and backward-compatibility cost.

Under Unified Governance, major compatibility commitments and high-migration-cost commitments are Project-Owner-reserved. If classification were uncertain, the mandatory default would also be MDE.

---

## 3. Accepted Upstream Preserved

This decision consumes without reopening:

```text
Business Application complete dual authoring
→ REQUIRED

Automation complete dual authoring
→ REQUIRED

Native Agent complete dual authoring
→ REQUIRED

Data / Knowledge / Foundational ETL complete dual authoring
→ REQUIRED

Business Application Semantic Authority / Canonical Definition SoT
→ ns_server

Automation Semantic Authority / Canonical Definition SoT
→ ns_server

Native AI Agent Semantic Authority / Canonical Definition SoT
→ ns_agent

Different Authoring Surface
!= Different Semantic Authority

UI Edit State
!= Canonical Definition SoT

SDK / Source Authoring
!= separate Definition Authority
```

No current Authority / SoT / Actual-state ownership is reopened by this decision.

---

## 4. Durable Mutually-exclusive Alternatives Presented

### A — Independent Complete Authoring Surfaces / No Cross-surface Interoperability Guarantee

Both source/SDK and visual authoring remain complete product capabilities and target the same governed semantic domain, but the product makes no durable guarantee that a definition authored in one surface can be opened, edited, converted, exported, or continued in the other surface.

```text
Source / SDK Authoring
→ COMPLETE

Visual Authoring
→ COMPLETE

Same Governed Semantic Domain
→ REQUIRED

Source → Visual
→ NO PRODUCT GUARANTEE

Visual → Source
→ NO PRODUCT GUARANTEE

Lossless Round-trip
→ NO
```

Cross-surface conversion may exist later as optional tooling but is not part of the stable product capability contract.

### B — Bidirectional Semantic Interoperability without Lossless Representation Round-trip

Both complete authoring surfaces SHALL interoperate bidirectionally through the same governed canonical domain semantics.

```text
Source-authored Definition
↔ Canonical Governed Definition Semantics
↔ Visual-authored Definition

Bidirectional Semantic Interoperability
→ REQUIRED

Semantic Loss
→ PROHIBITED

Silent Information Destruction
→ PROHIBITED

Lossless Authoring-representation Round-trip
→ NOT REQUIRED
```

A definition authored through either surface must remain semantically consumable and evolvable through the other surface to the extent that the other surface supports the same governed product semantics.

However, source-local or editor-local representation details such as comments, formatting, source organization, helper abstractions, visual layout, or other surface-local authoring metadata are not automatically part of the product-level round-trip guarantee.

If a construct cannot be safely represented or edited in the receiving surface, that condition must be explicit — e.g. `UNSUPPORTED`, `NON_EDITABLE`, `REPRESENTATION_LIMITATION`, or another later-defined governed equivalent — rather than silently dropping or rewriting semantic information.

### C — Full Lossless Bidirectional Source↔Visual Round-trip

All formally supported definitions SHALL be fully reversible between source and visual authoring representations.

```text
Source → Visual → Source
→ LOSSLESS

Visual → Source → Visual
→ LOSSLESS

Repeated Cross-surface Editing
→ MUST preserve all product-recognized authoring information
```

Advanced source constructs must either have equivalent visual representation or be losslessly preserved as governed non-visual information. Visual-specific information must likewise survive source conversion where it is part of the supported authoring model.

This option creates the strongest cross-surface compatibility commitment and the highest long-term migration/conformance burden.

---

## 5. Recommendation Presented

```text
Recommendation
→ B — Bidirectional Semantic Interoperability without Lossless Representation Round-trip
```

### Recommendation Rationale

Option B best preserves the already-accepted combination:

```text
Complete Source Authoring
+
Complete Visual Authoring
+
Same Governed Semantic Domain
+
Canonical Definition SoT
+
Representation != Semantics
```

It provides real Pro-code / Low-code collaboration and customer re-delivery interoperability without prematurely locking the architecture to one source DSL, one AST, one visual schema, one physical representation, or a permanent editor-level lossless conversion contract.

It is also consistent with the accepted principle that semantic compatibility precedes representation compatibility.

---

## 6. Tradeoffs and Impact

### 6.1 Option A

**Benefits**
- lowest conversion and compatibility complexity;
- source and visual authoring can evolve independently;
- no permanent cross-surface representation contract.

**Costs**
- source and visual workflows can become isolated ecosystems;
- customer secondary development can make later visual maintenance difficult;
- delivery-to-development and development-to-delivery handoff becomes expensive.

**Risks / Complexity**
- complete dual authoring may be interpreted by users as stronger interoperability than the product actually provides;
- semantic parity may exist while practical authoring collaboration remains weak.

**Long-term Impact**
- accepts durable workflow fragmentation between Pro-code and Low-code users.

**Compatibility / Migration Impact**
- no general cross-surface migration guarantee;
- later conversion tooling would be separately governed.

**Offline / Private Deployment Impact**
- simplest private/offline realization; both authoring paths can operate independently.

**Cross-component Impact**
- minimal authoring-interoperability obligation between `ns_web`, System-level SDK and domain semantic owners.

### 6.2 Option B

**Benefits**
- enables real collaboration across Developer, Delivery and customer-secondary-development workflows;
- preserves one governed domain meaning across both authoring paths;
- avoids silent semantic destruction when switching surfaces;
- does not require preserving editor-local representation details forever;
- supports re-delivery and long-lived maintainability without binding the product to one physical representation.

**Costs**
- canonical semantics must be rich and stable enough for both surfaces;
- both surfaces require compatibility/conformance feedback;
- representation limitations must be surfaced explicitly.

**Risks / Complexity**
- users may incorrectly assume source text / comments / layout are losslessly preserved unless product semantics clearly distinguish semantic interoperability from representation round-trip;
- advanced constructs may require non-editable or partially representable states in one surface.

**Long-term Impact**
- establishes stable cross-surface semantic interoperability as a product capability;
- permits source and visual authoring UX to evolve independently while preventing semantic forks.

**Compatibility / Migration Impact**
- semantic compatibility across authoring surfaces is a durable obligation;
- representation-local information is not automatically a permanent compatibility commitment;
- unsupported/incompatible constructs must be explicit and never silently coerced.

**Offline / Private Deployment Impact**
- interoperability must remain fully usable under accepted private/offline correctness;
- no public SaaS builder, cloud converter, mandatory public registry or Internet-only compiler may be required for core correctness.

**Cross-component Impact**
- System-level SDK and `ns_web` become interoperable authoring surfaces only;
- semantic owners and Definition SoTs remain unchanged;
- later contracts/internal boundaries must preserve semantic interoperability without transferring authority to a converter/editor/projection.

### 6.3 Option C

**Benefits**
- strongest Pro-code / Low-code interchangeability;
- minimal authoring-surface lock-in;
- simplest user mental model for cross-surface editing.

**Costs**
- very high implementation, compatibility and conformance burden across four complex domains;
- source and visual representation evolution become tightly coupled;
- advanced source abstractions may force visual complexity growth.

**Risks / Complexity**
- round-trip preservation can become a de facto architecture identity constraint;
- future evolution may be blocked by historical representation commitments;
- changing or removing the guarantee creates high migration cost.

**Long-term Impact**
- creates a strong and difficult-to-revoke compatibility contract spanning all authoring representations.

**Compatibility / Migration Impact**
- highest historical migration and backward-compatibility burden;
- all supported authoring metadata included in the guarantee must remain representable or losslessly preserved.

**Offline / Private Deployment Impact**
- still must operate offline/private, preventing use of mandatory public conversion services as a correctness dependency.

**Cross-component Impact**
- all four domain owners, `ns_web`, and System-level SDK inherit persistent high-fidelity conversion/conformance obligations.

---

## 7. Project Owner Selected Result

```text
Selected Option
→ B

Source / Visual Authoring Interoperability
→ BIDIRECTIONAL_SEMANTIC_INTEROPERABILITY_REQUIRED

Lossless Authoring-representation Round-trip
→ NOT REQUIRED

Silent Semantic Loss
→ PROHIBITED

Silent Destruction of Semantically Relevant Information
→ PROHIBITED

Unsupported / Non-editable / Representation-limited Construct
→ MUST REMAIN EXPLICIT
```

The Project Owner explicitly selected Option `B` in the authorized Z3 Batch 2 bounded session.

---

## 8. Explicit Selected Semantic Result

For each of the four complete dual-authoring domains:

```text
Business Application
Automation
Native AI Agent
Data / Knowledge / Foundational ETL
```

the product SHALL preserve:

```text
Source / SDK Authoring
→ complete authoring surface

ns_web Visual Authoring
→ complete authoring surface

Both Surfaces
→ target the same governed canonical domain semantics

Definition authored through either surface
→ MUST remain semantically interoperable with the other surface

Cross-surface transition
→ MUST preserve governed product semantics
→ MUST NOT silently discard semantically relevant information
→ MUST NOT silently reinterpret unsupported constructs

Lossless preservation of source formatting/comments/code organization
→ NOT IMPLIED

Lossless preservation of visual layout/surface-local metadata
→ NOT IMPLIED

One mandatory physical representation
→ NOT IMPLIED
```

Semantic interoperability is the product guarantee. Editor/representation fidelity is not automatically part of that guarantee.

---

## 9. Normative Consequences

### 9.1 Authoring Experience

The Developer / Delivery experience SHALL support a coherent cross-surface lifecycle in which source-authored and visually-authored definitions are not separate product classes.

The product must be capable of explaining when a definition or construct is:

```text
semantically supported and editable
semantically supported but not editable in the current surface
unsupported by the current surface/revision
incompatible with the receiving surface/revision
representation-limited
unknown / indeterminate due to missing compatibility evidence
```

Exact status names and UI presentation remain downstream design.

### 9.2 Validation / Compatibility

Cross-surface validation and compatibility feedback are `DERIVED_REQUIRED` consequences of the selected capability.

A receiving authoring surface must not silently apply best-effort conversion that changes accepted semantic meaning.

### 9.3 Revision / History

Revision history and historical interpretation must preserve which semantic definition revision is authoritative and must not use current source/visual representation as a substitute for the historically applicable canonical definition.

### 9.4 Re-delivery

Customer secondary development and re-delivery must not create a separate source-only or visual-only semantic class merely because one surface was used for modification.

---

## 10. Authority / SoT / Actual-state Preservation

This decision does not change accepted semantic authority or Source-of-Truth topology.

```text
Business Application Semantic Authority
→ ns_server / UNCHANGED

Business Application Canonical Definition SoT
→ ns_server / UNCHANGED

Automation Semantic Authority
→ ns_server / UNCHANGED

Automation Canonical Definition SoT
→ ns_server / UNCHANGED

Native AI Agent Semantic Authority
→ ns_agent / UNCHANGED

Native AI Agent Canonical Definition SoT
→ ns_agent / UNCHANGED

Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server / UNCHANGED

Data / Knowledge bounded factual SoT topology
→ UNCHANGED

Formal Artifact Acceptance Authority
→ ns_server / UNCHANGED

Formal Execution Admission Authority
→ ns_server / UNCHANGED

Runtime Actual-state Ownership
→ governed per bounded runtime semantic partition / UNCHANGED
```

Permanent rules:

```text
Source Authoring != Definition Authority
Visual Authoring != Definition Authority
Converter != Definition Authority
Projection != Definition SoT
Generated Source != Canonical by generation alone
Visual Edit State != Canonical Definition SoT
Interoperability Layer != Semantic Authority
```

---

## 11. Tenant / Organization / Principal / Policy / Trust Preservation

Cross-surface authoring does not alter applicable governance context.

```text
Authoring Surface Change
!= Tenant Change
!= Organization Change
!= Principal Change
!= Policy Bypass
!= Trust Bypass
!= Artifact Acceptance
!= Execution Admission
```

Visibility and diagnostic detail about unsupported/incompatible constructs remain subject to applicable Principal authorization, Tenant isolation, data/privacy and secret-disclosure rules.

---

## 12. Offline / Private Deployment Consequences

The selected interoperability capability is a core product authoring capability and therefore SHALL remain compatible with accepted private/offline lifecycle correctness.

```text
No Public Internet
No Mandatory SaaS Builder / Converter
No Mandatory Public Registry
No Mandatory Online Conversion Authority
```

Optional online tooling may exist later but cannot be required for the core correctness of the selected interoperability guarantee.

---

## 13. Explicit Non-implications

This Owner decision MUST NOT be interpreted as establishing:

```text
lossless source↔visual representation round-trip
one mandatory canonical source file format
one mandatory visual schema
one mandatory AST / IR technology
one mandatory DSL
source formatting preservation
source comments preservation
source file organization preservation
visual canvas/layout preservation
one physical storage representation
one editor implementation
one code generator
one conversion engine
one repository layout
one frontend architecture
one SDK API
one Contract schema
```

It also does not imply that every advanced source-local authoring construct must be directly editable in the visual surface. Where direct editing is impossible, the semantic condition must remain explicit and non-destructive.

---

## 14. Named Deferrals

Concrete realization remains outside this Owner decision and outside the current Batch 2 interaction-capability scope.

```text
Canonical internal authoring representation, if any
→ separately authorized Five-component Internal Architecture Boundary / Component Internal Design work

Source authoring DSL / SDK API
→ Component Internal Design / later stable Contract design as applicable

Visual authoring schema / visual DSL / editor representation
→ Component Internal Design; detailed UI/Frontend Architecture remains separately authorized later work

Source↔Visual conversion / projection algorithm
→ Component Internal Design

Surface-local metadata preservation rules
→ Component Internal Design / compatibility design

Concrete compatibility/conformance representation
→ later stable Contract / Component Internal Design as applicable

Physical package / artifact / storage representation
→ later authorized Component / Artifact / Provider design

Implementation tooling / code generator / parser / compiler
→ Implementation Planning only after accepted design/readiness
```

Any later proposal that changes the selected semantic interoperability guarantee, moves an Authority/SoT, introduces a major stable representation commitment, or upgrades the product guarantee to full lossless round-trip returns through GAC classification and Project Owner MDE governance.

---

## 15. Revalidation Trigger

Revalidate this decision if any later proposal:

```text
removes bidirectional semantic interoperability from any of the four complete dual-authoring domains
permits silent semantic loss during cross-surface transition
creates separate source-only and visual-only semantic classes
changes Business Application / Automation / Agent definition Authority or Canonical SoT
requires a mandatory one-representation or one-format architecture commitment
upgrades the product guarantee to full lossless source↔visual round-trip
makes a public/SaaS conversion service mandatory for core private/offline correctness
```

Changing editor framework, code formatting, canvas layout, parser/compiler library, internal package layout, representation technology, or implementation details does not by itself revalidate this decision when the selected semantics remain preserved.

---

## 16. Bounded-session Authority Limit

This evidence records the Project Owner's selected product capability semantics only.

It does **not**:

```text
claim GAC Global Acceptance
advance GAC Epoch
update Global State as acceptance authority
authorize Z3 Batch 3
declare Product Capability Exhaustion
declare Five-component Internal Architecture Boundaries Ready
begin Five-component Internal Architecture Boundary Synthesis
begin Component Internal Design
begin Runtime Responsibility Architecture
begin Shared Foundation Architecture
begin Foundation Contract / Module / Provider Design
begin Implementation Planning
begin IWP
begin Coding
```

The producing session remains bounded to Z3 Batch 2 Interaction Experience Capability Discovery / Owner Checkpoint work.