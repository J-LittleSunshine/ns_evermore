# NSE-007 — Definition, Artifact, and Runtime Governance State Separation

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-007`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-007`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 2`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; `ROOT-FACT-013`; accepted `NSE-001..004`; Unified Governance 0.0.2; Post-Z1-Batch-1 Constraint Pressure Assessment; GAC-EPOCH-0008 Batch 2 authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

A runtime may technically be able to load or execute mutable source, a definition, a package, dynamic code, or locally installed material. If technical executability is allowed to stand in for semantic certification, artifact acceptance, activation, execution admission, or authorization, formal production execution can bypass the governance states required by the Constitution.

This risk is amplified by extension, automation, local execution, recovery, and offline/private deployment because the same material may exist simultaneously as working definition, accepted release material, installed content, activated content, and attempted runtime execution.

## 2. Normative Requirement

`ns_evermore` SHALL preserve distinct governance semantics for:

```text
Development Definition
!= Domain Semantic Certification
!= Accepted Artifact
!= Installation
!= Activation
!= Formal Execution Admission
!= Runtime Execution Attempt
```

Technical loadability or executability is not evidence of certification, acceptance, activation, admission, or authorization.

Formal production execution MUST NOT directly execute mutable working source, unpublished definitions, unchecked dynamic code, or unaccepted packages merely because a runtime can access or execute them.

This constraint freezes semantic separation only; it does not choose an artifact format, registry, signing mechanism, package manager, persistence model, lifecycle engine, activation engine, admission engine, or concrete lifecycle state machine.

## 3. MUST

Future architecture and design MUST:

1. represent Development Definition, Domain Semantic Certification, Accepted Artifact, Installation, Activation, Formal Execution Admission, and Runtime Execution Attempt as distinct semantic states/decisions wherever those concepts apply;
2. preserve provenance linking an execution attempt to the relevant definition/artifact revision and the governance evidence required by later accepted architecture;
3. ensure `Can Load` is not interpreted as `Accepted`;
4. ensure `Can Execute` is not interpreted as `Certified`;
5. ensure `Installed` is not interpreted as `Activated`;
6. ensure `Activated` is not interpreted as `Execution Admitted`;
7. ensure an `Execution Attempt` is not interpreted as `Authorization`;
8. ensure `Mutable Working Source` is not interpreted as an `Accepted Production Artifact`;
9. require later architecture to explicitly resolve the authorities and Sources of Truth for certification, artifact acceptance, installation/activation state, execution admission, and applicable runtime actual state without deriving them solely from runtime possession or filesystem/database presence;
10. treat missing, stale, conflicting, or unverifiable governance evidence as an explicit unknown/indeterminate condition rather than silently reclassifying material as accepted/admitted; capability-specific handling remains for later authorized design;
11. preserve the separation through install, activation, execution, upgrade, rollback, recovery, reconnection, and offline/degraded operation;
12. require formal production execution paths to be demonstrably bounded by accepted artifact/admission governance rather than raw runtime capability.

## 4. MUST NOT

Future architecture and design MUST NOT:

1. collapse definition authoring and production artifact acceptance into one implicit state;
2. collapse semantic certification and technical executability;
3. treat package/file/database presence as artifact acceptance;
4. treat installation as activation;
5. treat activation as execution admission;
6. treat execution scheduling/dispatch/attempt as authorization;
7. allow a runtime loader, interpreter, plugin mechanism, automation executor, Agent tool runner, or local executor to create acceptance/admission authority merely because it can execute material;
8. allow mutable working source, unpublished definitions, unchecked dynamic code, or unaccepted packages to become formal production executable material by implementation convention;
9. infer Artifact Authority, Admission Authority, or Source of Truth from repository, filesystem, package, database, process, or deployment placement;
10. select artifact format, artifact registry, signing implementation, package manager, database model, deployment mechanism, activation/admission engine, or concrete lifecycle state machine within this constraint.

## 5. Long-term Invariant

```text
Can Load != Accepted
Can Execute != Certified
Installed != Activated
Activated != Execution Admitted
Execution Attempt != Authorization
Mutable Working Source != Accepted Production Artifact
Runtime Technical Capability != Governance Authority
```

Implementation convenience MUST NOT collapse governance states.

## 6. Origin / Provenance

This constraint is derived only from accepted Genesis authority:

- Genesis Constitution §19 `Definition / Artifact / Runtime Separation`;
- Genesis Constitution §20 where extension surfaces remain subject to Artifact Governance;
- Genesis Constitution §24 architecture-before-implementation ordering;
- `ROOT-FACT-013 — Definition / Artifact / Runtime are distinct governance states`;
- accepted `NSE-004` where offline/local operation cannot bypass Artifact or governance obligations;
- Post-Z1-Batch-1 Constraint Pressure Assessment §4C and §5;
- GAC-EPOCH-0008 Batch 2 authorization.

No pre-Genesis package system, plugin loader, artifact registry, deployment implementation, signing system, or runtime loader is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

The constraint does not select Artifact Authority, Certification Authority, Admission Authority, authorization owner, lifecycle state machine, artifact format, registry, signing mechanism, package manager, or persistence topology. Those remain explicit later architecture decisions and may require MDE classification where material.

## 8. Rationale

Production governance becomes ineffective if possession or executability of material is enough to promote it into production. Separating definition, certification, artifact acceptance, installation, activation, admission, and execution allows later architecture to establish verifiable control points without binding the project to a particular packaging or deployment technology.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **Runtime-can-execute implies production-executable:** prohibited by accepted root semantics.
- **Installation/activation used as a single acceptance state:** rejected because it collapses governance decisions.
- **Distinct governance states with concrete mechanisms deferred:** required.

Artifact formats, registries, signing, package managers, lifecycle engines, and state-machine design remain downstream.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- definition identity/revision and semantic certification;
- Artifact Authority / acceptance;
- installation and activation state;
- formal execution admission;
- runtime execution and authorization interactions;
- extension/plugin/automation/Agent/local execution;
- provenance, audit, recovery, rollback, compatibility, migration, and conformance;
- offline/private operation and supply-chain governance.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** definition/artifact revision identity must be traceable; concrete identifier format is deferred.
- **Revision / Evolution:** definition and artifact revisions cannot be conflated; versioning mechanisms are deferred.
- **Authority / Semantic Ownership:** required authority classes remain distinct; concrete owners are deferred/MDE-governed where material.
- **Source of Truth / Actual-state Ownership:** possession or installation cannot decide canonical state; allocation is deferred.
- **State / Lifecycle:** semantic stages are distinct; no concrete lifecycle state machine is selected.
- **Temporal Semantics:** execution evidence must be relatable to the governance state/revision applicable to that attempt; timestamp/clock mechanism is deferred.
- **Failure / Unknown / Indeterminate:** unverifiable acceptance/admission is not silently equivalent to accepted/admitted.
- **Tenant / Organization:** accepted `NSE-001..003` continue to govern artifact/execution context where applicable.
- **Principal / Authentication / Authorization / Policy:** execution attempt does not imply authorization; concrete engines/credentials are deferred.
- **Security / Data / Privacy / Trust:** formal production execution cannot bypass later-established trust and artifact controls.
- **Serialization / Representation:** no artifact or metadata format is selected.
- **Offline / Degraded:** `NSE-004` applies; absence of connectivity cannot collapse governance states.
- **Recovery / Reconciliation:** recovery must preserve state/provenance distinctions; algorithms are deferred.
- **Compatibility / Migration:** upgrades/rollbacks cannot silently reinterpret unaccepted material as accepted.
- **Conformance:** later architecture must demonstrate that technical executability cannot bypass acceptance/admission semantics.
- **Cross-boundary Dependency:** cross-boundary execution must preserve governance-state meaning; contract representation is deferred.
- **Invariant / Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner changes the constitutional requirement that Definition, Artifact, and Runtime governance states remain distinct, or permits formal production execution directly from unaccepted/mutable material.

Changing package systems, registries, signing technology, runtime languages, deployment engines, databases, or plugin frameworks is not by itself a revalidation trigger.

## 13. Status

```text
NSE-007
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```
