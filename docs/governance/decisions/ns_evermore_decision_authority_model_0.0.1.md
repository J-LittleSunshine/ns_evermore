# ns_evermore Decision Authority Model

## Authority Metadata

- **Document ID:** `NS-EVERMORE-DECISION-AUTHORITY-MODEL-0001`
- **Version:** `0.0.1`
- **Status:** `OWNER_DECIDED / NORMATIVE`
- **Authority Level:** `PROJECT_OWNER_GOVERNANCE_DECISION`
- **Program:** `NGRP-001`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Owner Decision Date:** `2026-08-12`
- **Upstream Normative Inputs:** `NS-EVERMORE-CONSTITUTION-0001 / 0.0.1`; `NS-EVERMORE-GOV-FRAMEWORK-0001 / 0.0.1`; `Z0-DAD-001..010`
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `OWNER_DECIDED / GAC_RECOGNIZED / NORMATIVE`
- **Applicable Scope:** all architecture, detailed design, implementation planning, IWP, Codex, and governance sessions

---

## 1. Purpose

This document makes the project's decision-delegation model explicit so that significant product and architecture decisions remain under Project Owner control while routine engineering decisions do not consume Owner decision bandwidth.

This is a governance clarification of the already accepted `INHERITED_FACT / DAD / MDE` model. It does not change accepted Product Component topology, Architecture Constraints, Authority allocation, Source of Truth, or any other product architecture semantic.

## 2. Core Decision Authority Model

```text
Project Owner
│
├── Root Product / Constitutional Decisions
│   → Project Owner decides
│
├── Major Decision Escalation / MDE
│   → Project Owner decides
│
├── Delegated Architecture Decision / DAD
│   → authorized Architecture / Design session decides
│   → Repository evidence required
│
└── Implementation Choice
    → authorized Detailed Design / Implementation Planning / IWP / Codex scope decides
    → MUST conform to Accepted Design
    → MUST NOT create or rewrite Architecture
```

Decision delegation changes **who decides**; it does not reduce required semantic depth, documentation, traceability, conformance, or review quality.

## 3. Project Owner Reserved Authority

The Project Owner is the final authority for:

- Root Product Intent and Product Non-goals;
- constitutional/root constraints;
- fixed Product Component topology changes;
- every MDE-class matter;
- major capability boundary changes;
- Semantic Ownership;
- Source of Truth and Actual-state Ownership where materially architecture-significant;
- Acceptance / Admission / Selection / Execution / Business Authority where materially architecture-significant;
- Tenant / Organization / Principal / IAM / Policy / Security / Trust authority changes;
- major stable identity commitments;
- major externally observable compatibility commitments;
- major historical-interpretation commitments;
- capability-specific offline fail-open/fail-closed policy when material;
- major vendor/provider/language/framework/protocol/storage/artifact-format lock-in;
- high-migration-cost long-term technology commitments;
- any issue classified as MDE by accepted governance.

The Project Owner may explicitly reserve an **unresolved** DAD or implementation-level decision before it is finalized. Such reservation MUST be persisted as Repository-backed Owner Decision evidence.

An already accepted Architecture / Contract / Module / DAD MUST NOT be silently overridden by a later chat instruction. A change to accepted authority requires the applicable reopen/supersession/impact-analysis/revalidation governance.

## 4. Global Architecture Coordinator Authority

The Global Architecture Coordinator is responsible for:

- recovering the current Repository-backed global state;
- decision classification quality and escalation enforcement;
- independent acceptance of bounded architecture/design sessions;
- architecture constraint exhaustion assessment;
- phase authorization and stop boundaries;
- continuity, State, Ledger, Required Read Set, and drift governance;
- checking whether a proposed DAD is actually MDE-class;
- preventing implementation or downstream design from inventing Architecture.

The GAC MUST NOT decide an Owner-reserved MDE on behalf of the Project Owner.

The GAC may reject or return a producing-session decision when it is misclassified, insufficiently resolved, inconsistent with accepted upstream authority, or outside scope.

## 5. Architecture / Design Session Delegated Authority

A bounded Architecture or Design session may autonomously decide a DAD only when all of the following are true:

1. the question is inside the exact authorized session scope;
2. accepted upstream constraints provide sufficient derivation authority;
3. the decision does not change an MDE-class dimension;
4. material alternatives and tradeoffs are evaluated where applicable;
5. the decision is persisted with required traceability;
6. the session stops for independent acceptance where governance requires it.

Typical delegated matters may include:

- non-material internal module decomposition;
- architecture-document organization;
- replaceable internal abstraction structure;
- package boundaries that do not redefine Product Components or semantic authority;
- detailed internal responsibilities already fully constrained by accepted architecture;
- replaceable provider/module design choices that do not create material lock-in.

## 6. Component Internal Design Authority

Component Internal Design is delegated by default, but the classification depends on what the design changes.

### 6.1 Owner / MDE required

A component-internal question MUST return to the Project Owner when it materially determines or changes:

```text
Authority
Semantic Ownership
Source of Truth
Actual-state Ownership
Trust Boundary
Tenant / Organization semantics
major lifecycle semantics
major compatibility commitments
major provider/framework/storage/protocol lock-in
high migration cost
```

### 6.2 DAD permitted

A component-internal design session may decide, within accepted boundaries:

```text
internal module decomposition
non-semantic service/class organization
internal interface decomposition
replaceable adapter arrangement
package grouping
implementation-neutral dependency direction
```

provided those decisions do not redefine accepted architecture.

## 7. Repository / Directory / Package Structure Authority

Repository and source-directory layout is **not** automatically an Architecture decision.

Typical matters such as:

```text
src layout
tests layout
Python package layout
frontend folder layout
contract file placement
tooling folder placement
internal module file organization
```

are normally delegated DAD or Implementation Planning decisions.

However:

```text
Directory Placement != Architecture Boundary
Python Package != Product Component
Django App != Architecture Authority
Vue Component != Product Component
```

If a proposed directory/package structure changes or implicitly redefines Product Component boundaries, Authority, Semantic Ownership, Source of Truth, Trust Boundary, Runtime Responsibility, or stable cross-boundary Contracts, the question is no longer a directory-layout choice and MUST be reclassified under Architecture governance, including MDE where applicable.

## 8. Technology Stack Decision Authority

Technology decisions use the following classification.

### 8.1 Already frozen technology facts

The following are inherited root facts and are not open to ordinary downstream redesign:

```text
Project delivery direction → PYTHON-FIRST
ns_server → Python + Django
ns_runtime → Python + WebSocket-centered communication
ns_node → Python
ns_agent → Python
ns_web → Vue 3 + TypeScript
```

Changing these root facts requires explicit Project Owner constitutional change and impact/revalidation governance.

### 8.2 Delegated technology decisions

A replaceable technology/library choice may be decided as DAD or implementation choice when it:

- conforms to an accepted Contract/Module/Provider boundary;
- does not become Architecture identity;
- does not change Authority or Source of Truth;
- does not create a major externally observable commitment;
- does not impose material long-term lock-in or high migration cost;
- preserves offline/private deployment, supply-chain, security, compatibility, and conformance requirements.

Examples may include ordinary test/lint tooling, an internal utility library, or a replaceable provider implementation where the accepted provider abstraction already exists.

### 8.3 Owner / MDE technology decisions

A technology choice MUST be escalated to the Project Owner when it materially creates or changes:

```text
Vendor lock-in
Provider lock-in
Language lock-in
Framework lock-in
Protocol lock-in
Storage-format lock-in
Artifact-format lock-in
Security / Trust model
Authority / Source of Truth
major compatibility surface
major operational dependency
high migration cost
```

Technology is not downgraded to an implementation choice merely because it is convenient to code.

## 9. Implementation Planning Authority

Implementation Planning consumes accepted design and may decide implementation organization only where accepted design leaves genuine implementation freedom.

Implementation Planning MUST stop and return to the correct design authority if a choice would change:

- Authority;
- Source of Truth;
- Product Component boundary;
- Runtime responsibility boundary;
- Security / Trust;
- Tenant / Organization semantics;
- Contract semantics;
- major long-term lock-in.

## 10. Codex / Implementation Session Authority

Codex implements accepted design inside an authorized IWP.

Codex may make local coding choices that do not alter architecture, including ordinary naming, local helper decomposition, mechanically necessary implementation details, and equivalent implementation techniques permitted by the IWP.

Codex MUST NOT independently decide or modify:

```text
Architecture Authority
Source of Truth
Tenant / Organization semantics
Product Component boundaries
Runtime architecture
Contract semantics
Security / Policy bypasses
major technology commitments
```

When implementation requires such a decision:

```text
STOP IMPLEMENTATION
→ RAISE DESIGN GAP
→ RETURN TO CORRECT DESIGN AUTHORITY
```

## 11. Classification Examples

| Question | Default Classification / Decider |
|---|---|
| Change the five Product Components | Root / Owner |
| Choose Organization final Authority | MDE / Owner |
| Choose canonical Source of Truth for material runtime state | MDE / Owner |
| Decide whether a capability-specific offline path fails open or closed where security is material | MDE / Owner |
| Choose a major core database/storage/protocol with durable lock-in | MDE / Owner |
| Split an accepted component-internal responsibility into non-semantic modules | DAD / Design Session |
| Choose repository `src/` and test layout without architecture impact | DAD or Implementation Planning |
| Choose a replaceable HTTP provider after Foundation Contract/Provider boundary is accepted | DAD / Provider Design or implementation choice, subject to lock-in audit |
| Choose test/lint helper tooling | Implementation Choice |
| Add a helper class during an IWP without semantic effect | Implementation Choice / Codex |

## 12. Owner Intervention Rule

The Project Owner may:

1. amend Root Product / Constitutional facts through explicit Owner Decision evidence;
2. decide every MDE;
3. explicitly reserve a currently unresolved delegated decision before finalization;
4. request reopening of accepted material through formal governance.

The Project Owner's authority does not eliminate Repository traceability. Architecture-critical Owner decisions MUST be persisted before downstream consumption.

## 13. Long-term Governance Invariant

```text
Project Owner decides product-defining and MDE-class choices.
GAC protects classification, acceptance, continuity, and phase boundaries.
Authorized Design Sessions decide DADs.
Implementation Planning / Codex decide only non-architecture implementation freedom.

Delegation != Loss of Owner Authority
Delegation != Reduced Design Depth
Implementation Freedom != Architecture Authority
Directory Layout != Architecture Boundary
Library Choice != Architecture Identity automatically
Accepted Architecture != Silently Overridable
```

## 14. Revalidation Trigger

Revalidate this governance model if the Project Owner changes:

- decision authority allocation;
- MDE/DAD classification semantics;
- GAC acceptance authority;
- implementation/Codex architecture authority;
- Owner reserved-decision semantics.
