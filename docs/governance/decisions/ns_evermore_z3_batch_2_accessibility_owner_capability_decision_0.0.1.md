# NGRP-001 Phase Z3 / Batch 2 — Accessibility Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **MDE Classification:** `NO`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Decision Predecessor HEAD:** `da2665ea16be8b9ad08111e9134c3e128223b7c2`
- **Current Global State at Decision:** `GAC-EPOCH-0022`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Shall Accessibility be a first-class `ns_evermore` product capability that constrains critical human-facing workflows, rather than being treated only as a later UI implementation quality concern?

This decision applies to applicable human-facing interaction including:

```text
Visual Authoring
Human Task Inbox
Notification / Awareness
Governance Interaction
Operation Observation / Intervention
Governed Pre-production Trial
Cross-domain Resource Discovery
Diagnostics / Explainability
Internationalization / Localization
Configuration / Operational Status
```

The question does **not** select a concrete UI framework, accessibility library, certification target, or external standard version, and it does not require all complex visual interaction modalities to use identical gestures or visual presentation.

---

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

### Why Product-significant

The choice materially affects:

```text
Critical workflow usability
Visual Builder interaction design
Human Task handling
Operational control
Diagnostics and status presentation
Extension / re-delivery expectations
Long-term UI migration cost
Enterprise product quality
```

If accessibility is deferred entirely to implementation, critical workflows may become dependent on pointer-only interaction, color-only state, inaccessible dynamic status or visual-only control semantics. Retrofitting such assumptions later can require architectural interaction changes rather than cosmetic adjustment.

### Why not MDE

This decision does not move or redefine Tenant, Principal, IAM, Policy, Product Definition, Artifact Acceptance, Execution Admission, Runtime Actual-state or other existing semantic authorities/SoTs. It establishes a human-interaction capability baseline and conformance expectation.

---

## 3. Options Considered

### Option A — Best-effort Accessibility

Accessibility is not a formal architecture capability. Keyboard support, screen-reader behavior, contrast, focus behavior, non-color signaling and similar concerns are left to later implementation best practice.

**Benefits**

- Maximum implementation freedom.
- Lowest immediate design pressure for complex visual editors.

**Costs / Risks**

- Accessibility may become inconsistent or permanently postponed.
- Critical workflows may become pointer-only, color-only or otherwise inaccessible.
- Later remediation may require significant interaction-model migration.

**Long-term Impact**

- No stable accessibility guarantee across human-facing product surfaces.

**Compatibility / Migration Impact**

- Potentially high retrofit cost if formal accessibility is introduced later.

**Offline / Private Impact**

- No additional core requirement.

**Cross-component Impact**

- Minimal immediate pressure.

### Option B — First-class Accessible Critical Workflows

Accessibility SHALL be a first-class product capability. Every critical human-facing workflow SHALL provide an accessible, semantically equivalent completion path.

Core principles:

```text
Critical Action
→ MUST NOT require pointer-only interaction

Critical State
→ MUST NOT depend on color alone

Interactive Control
→ MUST expose understandable semantic purpose/state

Keyboard Operability
→ REQUIRED where applicable

Focus / Interaction Order
→ MUST remain operable and understandable

Dynamic Status
→ MUST be perceivable without relying only on visual animation

Error / Warning
→ MUST expose semantic information, not visual decoration only
```

For complex visual authoring:

```text
Semantic Interaction Parity
→ REQUIRED

Visual Presentation Parity
→ NOT REQUIRED
```

A graph/canvas interaction may use drag-and-drop visually, but any semantically critical operation SHALL have an accessible equivalent interaction path, which may be structured editing, keyboard/command interaction, or another accessible mechanism.

**Benefits**

- Accessibility becomes part of the product boundary rather than a late retrofit.
- Critical Human Task, Notification, Governance, Configuration, Operation, Trial, Discovery and Diagnostic workflows remain usable without dependence on one visual modality.
- Complements complete Source/SDK + Visual Authoring without forcing all users to manipulate a complex canvas.
- Preserves structured semantics needed for accessible presentation.

**Costs**

Later detailed design must address semantic interaction structure, keyboard operability, focus management, dynamic state announcement, non-color representation and accessible alternatives for complex builders.

**Risks / Complexity**

The principal misunderstanding to avoid is treating semantic accessibility parity as a mandate for two fully separate products or identical visual/gesture parity. The requirement is equivalent critical capability, not identical presentation.

**Long-term Impact**

Accessibility becomes a durable human-interaction quality baseline across enterprise and re-delivery scenarios.

**Compatibility / Migration Impact**

Human-facing extensions SHALL avoid relying on color, pointer-only gesture, localized natural-language strings or screen position as the sole carrier of machine-significant or critical interaction semantics.

**Offline / Private Impact**

Core accessibility SHALL be provided by locally deployable product surfaces and SHALL NOT depend on public cloud accessibility services.

**Cross-component Impact**

`ns_web` and applicable human-facing projections are directly constrained. Five-component state/error/operation semantics must remain sufficiently structured to permit accessible rendering without moving the underlying semantic authority.

### Option C — Universal Accessibility Parity / Formal Compliance Commitment

Every human-facing surface, advanced visual editor, graph/canvas interaction and operational visualization must provide complete accessibility parity from the first formal release and be gated by a strict formal compliance target.

**Benefits**

- Strongest accessibility commitment.

**Costs / Risks**

- Very high constraint on visual-builder evolution, release cadence, testing matrix and extension ecosystem.
- May block otherwise useful advanced/experimental visual interaction until full parity mechanisms are available.

**Long-term / Compatibility Impact**

- Creates a strong permanent compatibility and compliance commitment.

**Offline / Private Impact**

- Must still be fully local/private.

**Cross-component Impact**

- Strongest pressure on `ns_web`, extension surfaces and all human-facing capability contracts.

---

## 4. Recommendation

```text
Recommendation
→ B — First-class Accessible Critical Workflows
```

Rationale:

```text
Accessibility
→ REQUIRED

Critical Human-facing Workflows
→ ACCESSIBLE COMPLETION PATH REQUIRED

Semantic Interaction Parity
→ REQUIRED

Visual Presentation Parity
→ NOT REQUIRED

Pointer-only Critical Operation
→ PROHIBITED

Color-only Critical Meaning
→ PROHIBITED

Structured Machine Semantics
→ REQUIRED ENABLER

Specific UI Framework / Accessibility Library
→ DEFERRED

Formal Certification Target / Exact External Standard Version
→ DEFERRED
```

This preserves a durable enterprise-grade interaction baseline while avoiding an unnecessary requirement that every sophisticated visual interaction have identical modality or presentation.

---

## 5. Owner Selection

The Project Owner selected:

```text
OPTION B
```

### Explicit Selected Result

```text
FIRST_CLASS_ACCESSIBILITY
+ ACCESSIBLE_CRITICAL_WORKFLOW_COMPLETION_PATH
→ REQUIRED
```

Normative capability consequences:

1. Accessibility SHALL be treated as a first-class product capability for critical human-facing workflows.
2. A critical operation SHALL NOT require pointer-only interaction as its sole completion mechanism.
3. Critical meaning/state SHALL NOT depend on color, animation, visual position or other purely visual presentation alone.
4. Applicable interactive controls SHALL expose understandable purpose and state through structured semantics.
5. Applicable critical workflows SHALL be keyboard-operable or SHALL provide another accessible semantic completion path.
6. Dynamic status, warnings and errors SHALL remain perceivable through structured/non-visual semantics.
7. Complex visual authoring SHALL preserve semantic interaction parity; identical visual presentation or identical gesture parity is not required.
8. Accessibility SHALL NOT create or transfer Product Definition, Policy, Artifact Acceptance, Execution Admission, Runtime Actual-state or other semantic authority.
9. Accessibility SHALL remain compatible with complete Source/SDK and Visual authoring and SHALL NOT require a single physical authoring representation.
10. Core accessibility SHALL remain fully usable in private/offline deployment.

---

## 6. Authority / SoT Preservation

This decision preserves all accepted authority topology, including:

```text
Tenant Semantic Authority / Canonical SoT
→ ns_server

IAM Semantic Authority
→ ns_server

Policy Semantic Authority
→ ns_server

Business Application Definition SoT
→ ns_server

Automation Definition / Workflow Authority and SoT
→ ns_server

Native Agent Definition / Semantic Authority and SoT
→ ns_agent

Artifact Acceptance Authority
→ ns_server

Execution Admission Authority
→ ns_server

Runtime Actual-state
→ final owner remains per bounded runtime semantic partition
```

Accessibility is a human-facing interaction requirement only. Accessible presentation, structured controls, keyboard interaction or equivalent interaction paths do not become semantic authority, evidence authority or canonical state.

---

## 7. Non-implications

This decision does **not** imply:

```text
one mandatory UI framework
one mandatory accessibility library
one mandatory design system
one mandatory browser
one mandatory assistive technology
pixel-identical accessible presentation
identical gesture interaction across modalities
full accessibility parity for every experimental visual feature
formal certification against a specific external standard/version
automatic translation of user content
new Product Definition Authority
new Runtime Actual-state Authority
new global UI SoT
```

It also does not authorize Component Internal Design or select any concrete UI implementation mechanism.

---

## 8. Named Deferrals

The following remain explicitly deferred to later properly authorized work:

```text
Concrete UI framework
Accessibility library/tooling
Design-system implementation
Detailed keyboard interaction maps
Focus-management implementation
Screen-reader announcement mechanics
Accessible graph/canvas interaction mechanism
Automated accessibility test tooling
Formal certification target
Exact external accessibility standard/version
Release-gating mechanics
Extension accessibility API/contract details
```

These deferrals SHALL NOT weaken the selected first-class accessibility capability baseline.

---

## 9. Revalidation Triggers

This Owner decision SHALL be revalidated if later work proposes to:

1. Remove accessibility as a first-class capability for critical workflows.
2. Make a critical workflow pointer-only, color-only, animation-only or otherwise dependent on one inaccessible modality.
3. Require visual presentation parity rather than semantic interaction parity.
4. Introduce a new human-facing surface that cannot expose structured semantic purpose/state.
5. Make accessibility depend on mandatory public Internet/SaaS services.
6. Allow accessibility infrastructure to become Product Definition, Policy, Runtime or other semantic authority.
7. Adopt a formal external compliance/certification commitment with material compatibility or delivery consequences.

---

## 10. Bounded Authority

This evidence records only the Project Owner's Z3 Batch 2 interaction-capability decision.

It does **not**:

```text
claim Global Acceptance
advance GAC Epoch
authorize Z3 Batch 3
declare Five-component Internal Architecture Boundaries complete
perform Five-component Internal Boundary Synthesis
enter Component Internal Design
enter Runtime Responsibility Architecture
enter Shared Foundation Architecture
select Foundation Contract / Module / Provider design
enter Implementation Planning / IWP / Coding
```

The maximum authority of this bounded session remains:

```text
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

subject to completion of the remaining authorized Batch 2 discovery, review and handoff evidence.