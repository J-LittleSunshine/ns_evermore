# NSE-005 — Product Component Semantic Topology and Runtime Non-conflation

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-005`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-005`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 2`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; `ROOT-FACT-001`; accepted `NSE-001..004`; Unified Governance 0.0.2; Post-Z1-Batch-1 Constraint Pressure Assessment; GAC-EPOCH-0008 Batch 2 authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

The Project Owner has frozen exactly five top-level Product Components: `ns_server`, `ns_runtime`, `ns_node`, `ns_agent`, and `ns_web`. Runtime, service, process, container, deployment, package, persistence, or database decomposition can nevertheless become mistaken for that product topology if physical or operational layout is allowed to redefine semantic component identity.

That conflation would make future deployment choices capable of silently changing Product Component boundaries and would invert the required derivation order from semantic responsibility to runtime implementation.

## 2. Normative Requirement

`ns_evermore` SHALL preserve the fixed five Product Components as a semantic product topology independent of runtime and physical decomposition.

A Product Component is not a Runtime Role, process, service, container, database, deployment unit, package, framework module, or other implementation/deployment unit merely because the two are co-located, similarly named, or mapped one-to-one in a particular realization.

Future Runtime Responsibility Architecture, service/process decomposition, deployment topology, package layout, and persistence placement MUST conform to the accepted Product Component semantic topology and MUST NOT redefine it.

## 3. MUST

Future architecture and design MUST:

1. preserve exactly the accepted top-level Product Component identities `ns_server`, `ns_runtime`, `ns_node`, `ns_agent`, and `ns_web` unless the Project Owner explicitly changes the constitutional topology;
2. preserve Product Component semantic boundaries independently from runtime role, process, service, container, database, deployment-unit, package, and framework boundaries;
3. derive Product Component responsibility, authority, semantic ownership, Source-of-Truth obligations, and cross-component dependencies before using runtime or physical placement as an implementation mapping;
4. require later architecture to make Product Component-to-Runtime mappings explicit enough to prove that runtime decomposition has not created, erased, merged, or redefined a top-level Product Component;
5. leave mapping cardinality open to later authorized architecture rather than imposing a mandatory one-to-one relationship between Product Components and runtime/process/service/deployment units;
6. preserve Product Component identity and responsibility if processes, services, containers, packages, databases, or deployment units are split, merged, replicated, co-located, or otherwise changed by later accepted design;
7. require physical co-location or shared implementation to preserve the semantic boundaries and authority distinctions of the Product Components involved;
8. treat database placement, package placement, framework placement, and deployment placement as non-authoritative evidence for Product Component semantic ownership or Source of Truth unless later accepted architecture explicitly establishes the relevant semantics.

## 4. MUST NOT

Future architecture and design MUST NOT:

1. define `Product Component = Runtime Role`;
2. define `Runtime Role = Process`, `Service`, `Container`, or `Deployment Unit` as a universal architecture identity rule;
3. infer that five Product Components require five processes, five services, five containers, five databases, or five deployment units;
4. infer Product Component boundaries from Django apps, Python packages, Vue components, repositories, directories, schemas, databases, processes, service names, container names, or deployment units;
5. allow runtime topology, scaling topology, failover topology, packaging, or persistence placement to create a new top-level Product Component or erase an accepted one;
6. use co-location, shared runtime infrastructure, shared persistence, or shared code as proof that two Product Components have the same semantic authority;
7. select the actual Runtime Role set, process layout, service layout, container layout, deployment layout, package layout, or database topology within this constraint.

## 5. Long-term Invariant

```text
Product Component != Runtime Role
Runtime Role != Process automatically
Runtime Role != Service automatically
Runtime Role != Container automatically
Runtime Role != Deployment Unit automatically
Five Product Components != Five Processes / Services / Containers / Databases / Deployment Units
Physical Placement != Product Component Semantic Authority
Runtime Decomposition MUST conform to Product Component Semantic Topology
```

Changing runtime or deployment shape MUST NOT by itself change Product Component meaning.

## 6. Origin / Provenance

This constraint is derived only from current accepted Genesis authority:

- Genesis Constitution §3 `Fixed Root Product Component Topology`;
- Genesis Constitution §§4–8 root Product Component responsibilities where semantic placement is inherited;
- Genesis Constitution §24 `Architecture-before-Implementation Invariants`;
- `ROOT-FACT-001 — Five Product Components are fixed`;
- accepted `NSE-001..004`, which prevent physical/deployment placement from overriding Tenant/Organization/offline semantics;
- Post-Z1-Batch-1 Constraint Pressure Assessment §4A and §5;
- GAC-EPOCH-0008 Batch 2 authorization.

No pre-Genesis runtime, process, service, container, package, database, or deployment layout is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

The constraint preserves the already-frozen Product Component topology and prevents runtime conflation. It does not choose any Runtime Role, mapping cardinality, process/service/container layout, deployment topology, database topology, Authority owner, Source of Truth, or Actual-state Owner.

## 8. Rationale

Product Components describe product-level semantic responsibility; runtime and deployment units describe how accepted responsibilities are executed and operated. Treating these concepts as equivalent would cause scaling, packaging, availability, or operational refactoring to become unauthorized product-architecture changes.

The constraint therefore fixes the direction of derivation without fixing a runtime realization.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **Mandatory one Product Component = one runtime/service/deployment unit:** rejected because the Constitution explicitly forbids the equivalence.
- **Runtime-first decomposition allowed to define Product Components:** prohibited because it reverses the accepted derivation order.
- **Stable Product Component semantic topology with explicitly derived later runtime mapping:** required.

Actual mapping cardinality and topology remain downstream architecture matters.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- Product Component identity and namespace;
- responsibility and semantic ownership;
- Authority / Source of Truth / Actual-state Ownership analysis;
- Runtime Responsibility Architecture;
- process/service/container/deployment decomposition;
- package/repository/module layout;
- persistence placement;
- scaling, failover, migration, compatibility, and conformance;
- cross-component dependency mapping.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** the five Product Component identities are closed; runtime identities remain downstream.
- **Revision / Evolution:** runtime/deployment evolution cannot silently revise Product Component identity.
- **Authority / Semantic Ownership:** must be resolved semantically before physical placement; concrete owners remain downstream/MDE where applicable.
- **Source of Truth / Actual-state Ownership:** placement cannot decide them; allocation remains downstream.
- **State / Lifecycle / Temporal:** no Product Component lifecycle or Runtime Role lifecycle is selected.
- **Failure / Unknown / Indeterminate:** an unmapped or ambiguous runtime unit cannot be treated as proof of component identity; later mapping/conformance must surface ambiguity.
- **Tenant / Organization:** accepted `NSE-001..003` remain fully applicable and cannot be bypassed by placement.
- **Principal / Authentication / Authorization / Policy:** no authority is created by runtime location.
- **Security / Data / Privacy / Trust:** co-location cannot erase semantic/trust distinctions established later.
- **Serialization / Representation:** not selected.
- **Offline / Degraded:** `NSE-004` remains controlling; offline placement does not redefine components.
- **Recovery / Reconciliation:** runtime recovery cannot rewrite Product Component identity; mechanisms are deferred.
- **Compatibility / Migration:** topology refactoring must preserve the accepted component semantics.
- **Conformance:** later architecture must demonstrate explicit component/runtime mapping without one-to-one assumption.
- **Cross-boundary Dependency:** dependencies are semantic first and runtime-mapped later.
- **Invariant / Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner changes the fixed five Product Component topology or explicitly changes the constitutional distinction between Product Components and runtime/deployment units.

Changes to process count, service count, container technology, deployment topology, database placement, package structure, or scaling strategy are not by themselves revalidation triggers.

## 13. Status

```text
NSE-005
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```
