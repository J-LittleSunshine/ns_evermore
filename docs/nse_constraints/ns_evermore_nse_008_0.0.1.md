# NSE-008 — Local Execution Authority and Source-effect Accountability Separation

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-008`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-008`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 2`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; accepted `NSE-001..004`; Unified Governance 0.0.2; Post-Z1-Batch-1 Constraint Pressure Assessment; GAC-EPOCH-0008 Batch 2 authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

`ns_node` is constitutionally required to perform Terminal / Local Execution, including task/workflow execution, automation, local resource access, permitted offline/degraded execution, execution source-fact production, protected effects, recovery, reconnection, and reconciliation handoff.

Because the node directly performs and observes local actions, later architecture could incorrectly convert execution capability into Task/Workflow Definition Authority, Policy/Authorization Authority, grant issuance authority, canonical runtime-state ownership, Source of Truth, or canonical Audit Evidence authority.

The opposite error is also possible: treating local execution facts/effects as disposable because they are not automatically canonical, losing the provenance and accountability required to recover and reconcile what actually happened.

## 2. Normative Requirement

Local execution SHALL preserve a strict separation between execution responsibility, definition/semantic authority, policy/authorization authority, source-fact production, canonical-state ownership, and audit canonicalization.

`ns_node` MAY produce provenance-bearing source facts and evidence candidates about execution attempts, observed local state, and protected effects because those events originate or are observed locally; that production role MUST NOT automatically make the local node the final semantic authority, Source of Truth for broader domain state, canonical Runtime State owner, grant issuer, Policy Authority, Authorization Authority, or canonical Audit Evidence authority.

Future architecture MUST explicitly resolve source-fact production, protected-effect accountability, provenance, recovery, reconnection, and reconciliation handoff without choosing those owners by physical locality alone.

## 3. MUST

Future architecture and design MUST:

1. preserve `ns_node executes task != Task Definition Authority`;
2. preserve `ns_node executes workflow != Workflow Semantic Authority`;
3. preserve `local execution != Policy Authority`;
4. preserve `local grant exercise != Grant Issuance Authority`;
5. preserve `local protected effect != Authorization Authority`;
6. preserve `local cache != Source of Truth automatically`;
7. preserve `local runtime fact != Canonical Runtime State automatically`;
8. preserve `local Audit Evidence Candidate != Canonical Audit Evidence`;
9. preserve provenance for execution attempts, local source-fact production, grant exercise, protected effects, and evidence candidates sufficient for later-defined accountability, recovery, and reconciliation;
10. keep the origin/observation of a local source fact distinguishable from its later canonical interpretation, acceptance, aggregation, or reconciliation;
11. require protected effects to remain attributable to the execution context and applicable authorization/grant provenance without treating successful effect execution as proof that authorization existed;
12. require recovery and reconnection paths to preserve unresolved, conflicting, stale, or indeterminate local facts as explicit conditions rather than silently canonicalizing them by locality or connectivity restoration;
13. require reconciliation handoff to carry enough semantic distinction for later accepted authority to determine canonical outcomes without assuming `local wins` or `remote wins` as a universal rule;
14. preserve Tenant, Organization, Principal, Policy, Security, Artifact, Data/Privacy/Trust, and Audit context through local/offline execution where applicable;
15. require any material capability-specific offline fail-open/fail-closed, pre-authorization, grant issuance, or canonicalization policy to be explicitly decided under Unified Governance rather than inferred from execution capability.

## 4. MUST NOT

Future architecture and design MUST NOT:

1. make task/workflow execution capability the Task/Workflow Definition or Semantic Authority merely by placement in `ns_node`;
2. treat the executor as Policy or Authorization Authority merely because it performs a protected effect;
3. treat possession/exercise of a grant as authority to issue or redefine the grant;
4. treat local success, local observation, local cache presence, or local database presence as automatic canonicalization;
5. treat a locally produced runtime fact as the canonical global runtime state solely because the node directly observed it;
6. treat a locally generated audit/event record as canonical Audit Evidence solely because it originated at the executor;
7. discard locally originated execution/effect facts merely because they are not automatically canonical;
8. erase Tenant/Organization/Principal/provenance context during offline operation, recovery, reconnection, or reconciliation;
9. interpret loss of connectivity as authorization, grant issuance, policy relaxation, or canonical-state ownership;
10. choose a local database, cache provider, grant format, credential format, authorization engine, audit store, scheduler, worker, synchronization protocol, runtime topology, recovery algorithm, or reconciliation algorithm within this constraint.

## 5. Long-term Invariant

```text
Execution != Definition Authority
Observed Effect != Authorization Authority
Grant Exercise != Grant Issuance Authority
Local Fact != Canonical State automatically
Local Cache != Source of Truth automatically
Evidence Candidate != Canonical Audit Evidence automatically
Source-fact Origin != Final Semantic Authority automatically
Offline / Local Execution != Governance Bypass
```

Local execution must remain both governed and accountable without becoming universally authoritative.

## 6. Origin / Provenance

This constraint is derived only from current accepted Genesis authority:

- Genesis Constitution §6 `Root Responsibilities of ns_node`, including execution source-fact production, recovery, reconnection, and reconciliation handoff;
- Genesis Constitution §18 `Offline / Private Deployment Correctness`;
- Genesis Constitution §19 `Definition / Artifact / Runtime Separation` where execution/admission interaction is relevant;
- accepted `NSE-001..003` Tenant/Organization invariants;
- accepted `NSE-004` Offline Core Correctness and Governance Invariance;
- Post-Z1-Batch-1 Constraint Pressure Assessment §4D and §5;
- GAC-EPOCH-0008 Batch 2 authorization.

No pre-Genesis local database, scheduler, worker, grant, credential, audit, synchronization, recovery, or reconciliation implementation is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

The constraint preserves inherited distinctions and accountability obligations but does not select Task/Workflow Definition Authority, Policy/Authorization Authority, grant issuer, Source of Truth, canonical Runtime State owner, canonical Audit Evidence authority, offline fail-open/fail-closed policy, or reconciliation winner. Any later material choice in those categories remains subject to MDE governance.

## 8. Rationale

The executor is uniquely positioned to produce facts about what it attempted, observed, and changed, but execution locality is not a sufficient basis for broader semantic or authorization authority. Correct architecture therefore needs both halves simultaneously: local source/effect evidence must be preserved and accountable, while canonicalization and authority remain explicitly governed.

This prevents two failure modes: unauthorized authority acquisition by the executor and loss of real-world execution evidence during recovery/reconciliation.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **Local executor is canonical authority while disconnected:** rejected by accepted `NSE-004` and constitutional authority distinctions.
- **Central-only truth; local facts are disposable until accepted:** rejected because `ns_node` is required to produce source facts and protected-effect evidence needed for accountability/reconciliation.
- **Preserve local source/effect evidence while keeping final authority/canonicalization explicit and downstream:** required.

Concrete grants, stores, protocols, algorithms, and runtime topology remain deferred.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- Terminal / Local Execution responsibility;
- Task/Workflow definition and semantic ownership interactions;
- Policy / Authorization / grant authority;
- Source of Truth / canonical Runtime State / Actual-state Ownership;
- source-fact production and protected-effect accountability;
- provenance and Audit Evidence;
- offline/degraded execution;
- recovery, reconnection, reconciliation;
- Security / Trust / Data / Privacy;
- runtime coordination, compatibility, migration, and conformance.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** execution/effect/evidence must retain attributable identities/context; formats are deferred.
- **Revision / Evolution:** definition/grant/artifact/runtime revisions must remain distinguishable in provenance; representation is deferred.
- **Authority / Semantic Ownership:** executor role is separated from definition/policy/issuance/final semantic authority; concrete owners are deferred.
- **Source of Truth / Actual-state Ownership:** local facts/caches are non-canonical by default as an inference rule; actual canonical owners remain explicit downstream decisions.
- **State / Lifecycle / Temporal:** execution attempts/effects and later canonicalization/reconciliation are distinct; concrete state machines/clocks are deferred.
- **Failure / Unknown / Indeterminate:** conflicting/stale/unverifiable local state remains explicit rather than silently canonicalized or discarded.
- **Tenant / Organization:** `NSE-001..003` remain mandatory in local/offline execution context.
- **Principal / Authentication / Authorization / Policy:** grant exercise and effect execution cannot create issuance/policy authority; mechanisms are deferred.
- **Security / Data / Privacy / Trust:** protected effects remain accountable and governed; no local bypass is created.
- **Serialization / Representation:** no grant/evidence/sync format is selected.
- **Offline / Degraded:** `NSE-004` remains controlling and is deepened by source/effect accountability.
- **Recovery / Reconciliation:** provenance-preserving handoff is mandatory; winner/algorithm is deferred.
- **Compatibility / Migration:** implementation changes cannot reinterpret source-fact origin as final authority.
- **Conformance:** later architecture must prove both preservation of local evidence and absence of locality-based authority acquisition.
- **Cross-boundary Dependency:** handoff must preserve source/effect distinctions; protocol remains deferred.
- **Invariant / Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner changes `ns_node`'s Terminal / Local Execution/source-fact responsibilities, permits local/offline execution to acquire authority by disconnection/locality, or changes the rule that local facts/evidence are not automatically canonical.

Changing local databases, caches, schedulers, workers, authorization engines, audit stores, protocols, or recovery/reconciliation algorithms is not by itself a revalidation trigger.

## 13. Status

```text
NSE-008
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```
