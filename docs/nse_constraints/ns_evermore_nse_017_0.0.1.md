# NSE-017 — Implementation Derivability and Downstream Architecture Non-invention

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-017`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-017`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 4`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; `ROOT-FACT-017`; accepted `NSE-001..012`; Unified Governance 0.0.2; GAC-EPOCH-0012 Batch 4 authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

An architecture can be formally accepted yet still be too incomplete for safe implementation if downstream planning or coding must invent missing semantic authority, Source-of-Truth ownership, Product Component/runtime boundaries, contract semantics, Tenant/Organization behavior, security/trust boundaries, Artifact/Admission semantics, or major compatibility/migration commitments simply to make code possible.

If those gaps are filled by package layout, framework convention, directory structure, database placement, generated code, or Codex implementation choices, implementation convention becomes architecture by accident. That would bypass the accepted decision-authority model and make implementation artifacts the de facto source of architecture truth.

## 2. Normative Requirement

Accepted design SHALL become implementation-derivable before formal Implementation Planning is authorized.

`Implementation-derivable` means that downstream Implementation Planning, IWP, and Codex work can determine the required implementation behavior from current accepted Repository authority plus explicitly delegated non-architecture implementation freedom without making a new Architecture/MDE-class decision merely to proceed.

Any architecture-critical semantic dimension required by implementation MUST be either explicitly resolved in accepted upstream design or explicitly deferred to a named, legally authorized later design authority before Implementation Planning. It MUST NOT be left as an implicit gap to be resolved by implementation convention.

If downstream planning or implementation discovers missing or contradictory architecture-critical semantics, it SHALL stop the affected downstream work, raise a design gap, and return the issue to the correct Architecture/Design authority. Implementation progress MUST NOT be used as authority to decide the gap retroactively.

This constraint does not design an Implementation Master Plan, IWP schema, Codex workflow, repository/package structure, code-generation system, or implementation detail.

## 3. MUST

Future architecture, design-readiness, planning, IWP, and implementation governance MUST:

1. preserve `Accepted Design → must become implementation-derivable before Implementation Planning`;
2. distinguish architecture/design decisions from delegated implementation freedom explicitly enough that downstream workers know which choices they may make locally;
3. require all implementation-relevant Authority, Semantic Ownership, Source of Truth, Actual-state Ownership, Product Component Boundary, Runtime Responsibility, stable Contract Semantics, Tenant/Organization semantics, Security/Trust boundaries, Artifact/Admission semantics, and material compatibility/migration commitments to be resolved or legally deferred before downstream implementation depends on them;
4. require design-to-implementation readiness to verify that no material implementation path requires an unclassified architecture decision to be invented by planning, IWP, Codex, framework convention, database placement, directory layout, or package structure;
5. require Implementation Planning to consume Accepted Design rather than reinterpret code/repository structure as architecture authority;
6. require each IWP and Codex task to remain inside the implementation freedom left by Accepted Design and current authorization;
7. stop affected downstream work and raise a design gap when implementation reveals missing, ambiguous, conflicting, or materially insufficient upstream semantics;
8. return a design gap to the correct upstream authority rather than selecting the most convenient implementation assumption;
9. require any implementation-discovered change that would materially alter accepted Authority, SoT, Product Component/runtime boundary, contract semantics, Tenant/Organization semantics, security/trust model, Artifact/Admission semantics, major compatibility/migration commitment, or major technology lock-in to follow formal reopen/revalidation/decision governance before implementation continues;
10. keep code structure, directory layout, package structure, framework placement, database placement, service placement, generated types, and local coding conventions non-authoritative unless a later accepted architecture/design decision explicitly gives them semantic meaning;
11. preserve traceability from implementation requirements and verification criteria back to accepted design/constraint authority without requiring implementation to reconstruct missing semantics from prior chat context;
12. preserve implementation reversibility at the architecture boundary: refactoring implementation structure must not silently revise accepted architecture;
13. require unresolved architecture-critical gaps to remain visible as blockers rather than becoming undocumented implementation assumptions;
14. preserve independent GAC/design-readiness authority to decide when the accepted design is sufficiently derivable for Implementation Planning; completion of Architecture/Design documents alone does not automatically authorize implementation.

## 4. MUST NOT

Future architecture, planning, IWP, or implementation governance MUST NOT:

1. define `Implementation Freedom = Architecture Authority`;
2. define `Code Structure = Architecture Authority`;
3. define `Directory Layout = Architecture Boundary`;
4. define `Framework Placement = Semantic Ownership`;
5. define `Database Placement = Source of Truth` automatically;
6. allow Implementation Planning, IWP, Codex, generated code, framework defaults, package structure, or local coding convention to invent missing Authority, Semantic Ownership, Source of Truth, Actual-state Ownership, Product Component Boundary, Runtime Responsibility, Contract Semantics, Tenant/Organization semantics, Security/Trust boundaries, Artifact/Admission semantics, or major compatibility/migration commitments;
7. treat successful compilation, tests, deployment, or runtime behavior as retroactive proof that an undocumented architecture choice was authorized;
8. resolve a design gap by silently encoding one interpretation in implementation and then treating the implementation as normative precedent;
9. allow a downstream implementation choice to reopen or supersede accepted architecture without formal governance;
10. begin formal Implementation Planning merely because the preceding design phase produced documents; explicit readiness/authorization remains required;
11. design an Implementation Master Plan, repository/package structure, IWP contents, Codex workflow, code-generation tooling, or implementation details within this constraint.

## 5. Long-term Invariant

```text
Accepted Design → Implementation-derivable before Implementation Planning
Implementation Freedom != Architecture Authority
Code Structure != Architecture Authority
Directory Layout != Architecture Boundary
Framework Placement != Semantic Ownership
Implementation Convention != Architecture by Accident
Missing Architecture-critical Semantics → STOP DOWNSTREAM WORK
Design Gap → Return to Correct Design Authority
Implementation Success != Retroactive Architecture Authorization
```

Implementation may exercise local freedom only inside the semantic space deliberately left open by accepted design.

## 6. Origin / Provenance

This constraint is derived only from current accepted Repository authority:

- Genesis Constitution §1 `Constitutional Purpose` derivation ordering;
- Genesis Constitution §24 `Architecture-before-Implementation Invariants`;
- Genesis Constitution §25 `Decision Governance Root Rules`;
- Genesis Constitution §26 `Mandatory Semantic Resolution Principle`;
- Genesis Constitution §27 `Required Derivation Order`;
- Genesis Constitution §28 `Repository-backed Continuity Constitution`, including `Design Must Be Implementation-derivable`;
- `ROOT-FACT-017 — Accepted design must be implementation-derivable before implementation planning`;
- Unified Governance §§7–10 mandatory semantic resolution/review/derivation/constraint rules;
- Unified Governance §17 `Implementation Planning / IWP / Codex`;
- accepted `NSE-001..012`, whose semantic invariants cannot become implementation-defined escape hatches;
- GAC-EPOCH-0012 Batch 4 authorization.

No pre-Genesis implementation plan, repository/package structure, generated code, coding convention, framework layout, or Codex workflow is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

This constraint formalizes already accepted architecture-before-implementation and implementation-derivability semantics. It does not choose repository/package layout, implementation strategy, IWP structure, code-generation tooling, implementation technology, or any currently unresolved Authority/SoT owner.

## 8. Rationale

Architecture governance is ineffective if the final unresolved architecture decisions are delegated implicitly to the person or tool writing code. Conversely, implementation cannot be expected to be a mechanical transcription of design; it needs legitimate local freedom for non-semantic choices.

The constraint therefore defines the boundary: accepted design must resolve everything that would otherwise require architecture authority, while implementation remains free to choose among semantically equivalent realizations inside that boundary.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **Implementation fills architecture gaps pragmatically:** rejected because it bypasses decision authority and makes code the de facto architecture source.
- **Architecture specifies every coding detail:** rejected because implementation freedom is legitimate where choices have no architecture semantic effect.
- **Architecture-critical semantics resolved/deferred explicitly, with bounded implementation freedom and stop-on-gap:** required.

Actual Implementation Master Plan structure, IWP schema, code-generation approach, repository/package layout, and coding conventions remain deferred.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- design-to-implementation readiness;
- semantic completeness;
- Authority / Semantic Ownership / SoT / Actual-state ownership;
- Product Component / Runtime Responsibility boundaries;
- cross-boundary contracts;
- Tenant / Organization / IAM / Policy / Security / Trust;
- Artifact / Admission / extension governance;
- compatibility / migration;
- Implementation Planning / IWP / Codex authorization;
- verification and traceability.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** accepted architecture/design and implementation requirements must be traceable to stable Repository authority; concrete IWP/plan identifiers are downstream.
- **Revision / Evolution:** implementation must consume current accepted revisions; design changes discovered later require formal reopen/revalidation rather than silent code drift.
- **Authority / Semantic Ownership:** missing authority/ownership cannot be invented downstream; unresolved material ownership returns to the correct authority.
- **Source of Truth / Actual-state Ownership:** database/process/framework placement cannot supply missing SoT/actual-state semantics.
- **State / Lifecycle / Temporal:** design-readiness and downstream authorization remain explicit gates; no implementation lifecycle is selected here.
- **Failure / Unknown / Indeterminate:** missing/ambiguous/conflicting architecture is an explicit design gap/blocker, not an implementation default.
- **Tenant / Organization:** accepted `NSE-001..003` must be implementation-derivable and cannot be reinterpreted by local coding convention.
- **Principal / Authentication / Authorization / Policy:** downstream work cannot invent missing policy/security authority.
- **Security / Data / Privacy / Trust:** trust/security boundaries must be accepted upstream before implementation depends on them.
- **Serialization / Representation:** accepted `NSE-009` remains controlling; concrete representation may be implementation/design freedom only where legally delegated.
- **Offline / Degraded:** accepted `NSE-004` remains controlling; downstream implementation cannot invent online dependencies or governance bypasses to fill a design gap.
- **Recovery / Reconciliation:** implementation-discovered recovery gaps return upstream if they require semantic authority decisions.
- **Compatibility / Migration:** material compatibility/migration commitments cannot be created by downstream implementation convention.
- **Conformance:** readiness/conformance must show downstream implementation can proceed without unclassified architecture decisions.
- **Cross-boundary Dependency:** dependencies must be sufficiently specified at accepted design level to prevent implementation-created semantic contracts.
- **Invariant / Decision Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner explicitly changes one or more of:

- architecture-before-implementation ordering;
- the requirement that accepted design become implementation-derivable before Implementation Planning;
- the rule that Implementation Planning/IWP/Codex have no Architecture Authority;
- the requirement to stop and return design gaps to the correct authority.

Changing repository/package layout, coding framework, build system, code generator, testing tool, implementation language within an already authorized boundary, or IWP formatting is not by itself a revalidation trigger.

## 13. Status

```text
NSE-017
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```