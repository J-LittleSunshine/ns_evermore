# NSE-011 — External Source-of-Truth Preservation under Bounded Enterprise Integration

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-011`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-011`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 3`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; accepted `NSE-001..008`; Unified Governance 0.0.2; GAC-EPOCH-0010 Batch 3 authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

`ns_evermore` must integrate with enterprise systems such as ERP, CRM, MES, HIS, HR, OA, financial systems, and other authoritative applications. Once external data is synchronized, imported, transformed, stored, indexed, cached, projected, replicated, aggregated, or used by AI/automation inside `ns_evermore`, implementation placement can mistakenly be interpreted as a transfer of Source-of-Truth or source-fact authority.

That mistake would silently convert a bounded integration/data/knowledge platform into a universal enterprise-core replacement, erase provenance about where a fact originated, and make stale, conflicting, missing, unknown, indeterminate, or unmapped external facts appear canonical merely because they were processed locally.

## 2. Normative Requirement

External enterprise systems MAY remain authoritative Sources of Truth or source-fact authorities for their bounded domains even when their facts are synchronized, imported, transformed, indexed, cached, projected, replicated, aggregated, or otherwise processed by `ns_evermore`.

Synchronization, ingestion, ETL, local storage, indexing, caching, projection, replication, aggregation, and derivation SHALL NOT automatically transfer semantic authority, Source-of-Truth ownership, Actual-state Ownership, or canonical status to `ns_evermore`.

Future architecture MUST preserve enough source identity, provenance, mapping state, freshness/revision context where applicable, and source-versus-derived distinction to keep stale, conflicting, missing, unknown, indeterminate, or unmapped facts explicit rather than silently canonicalizing them through ingestion or processing placement.

This constraint does not choose an external-system Authority owner, conflict winner, canonicalization winner, connector protocol, integration middleware, external schema, CDC/event technology, synchronization algorithm, database, queue, or external-system-specific implementation.

## 3. MUST

Future architecture and design MUST:

1. preserve the possibility that an external system remains the authoritative Source of Truth or source-fact authority for its bounded domain after synchronization into `ns_evermore`;
2. preserve source identity and provenance sufficient to distinguish externally sourced facts from locally authored, transformed, derived, aggregated, projected, indexed, cached, or replicated material where that distinction is semantically relevant;
3. distinguish a source fact from a local copy, materialized representation, index, cache entry, projection, analytical/AI derivation, aggregation, or transformed fact without assuming those representations have equal authority;
4. preserve explicit mapping semantics between external identities and `ns_evermore` identities rather than treating ingestion as identity equality or canonicalization;
5. preserve stale, conflicting, missing, unknown, indeterminate, and unmapped conditions explicitly when they occur instead of selecting a winner by processing order, local storage presence, freshness guess, or implementation convention;
6. require later architecture to make any material Authority, Source-of-Truth, Actual-state Ownership, conflict-winner, or canonicalization-winner decision explicit and MDE-governed where applicable;
7. preserve provenance of transformations and derivations sufficiently for later architecture to distinguish an upstream source assertion from a `ns_evermore`-derived assertion without treating derived/aggregated facts as upstream source facts automatically;
8. preserve applicable Tenant semantics when external facts enter the platform; ingestion or external organization identity cannot create a Tenant bypass or redefine Tenant identity;
9. preserve Organization plurality and explicit external Organization mapping under `NSE-002/003`, including the rule that one external organization model is not globally canonical automatically;
10. ensure local replica, cache, index, projection, or offline copy does not become canonical merely because the external system is temporarily unavailable or connectivity is lost;
11. preserve enough source/revision/freshness/temporal context where applicable for later recovery and reconciliation to evaluate facts without assuming `local wins`, `external wins`, `latest write wins`, or another universal rule;
12. preserve bounded product scope: synchronization of data from ERP/CRM/MES/HIS/HR/OA/financial or other systems does not by itself redefine `ns_evermore` as the universal replacement Authority for those systems;
13. require later conformance evidence to demonstrate that ingestion, ETL, indexing, caching, projection, replication, aggregation, or local storage cannot silently create Source-of-Truth authority;
14. preserve private/offline correctness: temporary disconnection from an external authority is an explicit availability/freshness condition, not an automatic authority transfer to a local replica.

## 4. MUST NOT

Future architecture and design MUST NOT:

1. define `Synchronization = Authority Transfer`;
2. define `Import = Authority Transfer`;
3. define `ETL Output = Upstream Source Fact` automatically;
4. define `Index = Source of Truth` automatically;
5. define `Cache = Source of Truth` automatically;
6. define `Projection = Source of Truth` automatically;
7. define `Local Replica = External Authority Replacement` automatically;
8. define `Derived / Aggregated Fact = Source Fact` automatically;
9. treat local database/storage possession, processing placement, runtime location, pipeline ownership, index ownership, or data-consumer popularity as proof of semantic authority or canonical status;
10. silently collapse unresolved external identity/organization mappings into local identity equality;
11. silently choose a conflict or reconciliation winner because one version arrived later, is locally available, was transformed most recently, or resides in a preferred store;
12. interpret external-system unavailability, offline operation, cache presence, or local replica freshness as automatic transfer of Source-of-Truth ownership;
13. infer that synchronized enterprise data makes `ns_evermore` the universal ERP, CRM, MES, HIS, HR, OA, financial-system, or other enterprise-core replacement;
14. select connector protocol, integration middleware, external schema, CDC technology, event technology, synchronization algorithm, conflict winner, canonicalization winner, database, queue, broker, or external-system-specific implementation within this constraint.

## 5. Long-term Invariant

```text
Synchronization != Authority Transfer
Import != Authority Transfer
ETL Output != Upstream Source Fact automatically
Index / Cache / Projection != Source of Truth automatically
Local Replica != External Authority Replacement automatically
Derived / Aggregated Fact != Source Fact automatically
Processing Placement != Canonicalization
External Unavailability != Local Authority Transfer
Mapping != Identity Equality automatically
```

Bounded integration MUST preserve external source authority where applicable without preventing `ns_evermore` from creating explicitly governed local or derived semantics in domains later assigned to it.

## 6. Origin / Provenance

This constraint is derived only from current accepted Repository authority:

- Genesis Constitution §10–12 where external Organization mapping must not collapse Tenant/Organization semantics;
- Genesis Constitution §13 `Knowledge and Enterprise Data Foundation`, including `ETL Output ≠ Upstream Source Fact`, `Data Storage ≠ Business Authority`, `Knowledge Index ≠ Knowledge Source of Truth automatically`, and preservation of external HIS/ERP/CRM/MES/OA/HR/financial source status;
- Genesis Constitution §21 `Product Non-goals and Bounded Enterprise Integration`;
- Genesis Constitution §24 `Semantic Authority before Database` and `Source of Truth before Persistence`;
- accepted `NSE-001..008`, especially Tenant/Organization non-collapse, offline governance invariance, first-class domain authority non-transfer, and locality/source-effect non-canonicalization;
- GAC-EPOCH-0010 Batch 3 authorization.

No pre-Genesis connector, integration middleware, ETL pipeline, external schema, CDC/event system, database, conflict-resolution algorithm, or customer-specific system mapping is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

This constraint does not decide which specific system owns Authority/SoT for a particular business entity, whether a local domain may become authoritative, how conflicts are resolved, how identities are mapped, or which synchronization/integration technology is used. Those remain downstream decisions; material Authority/SoT/conflict/canonicalization choices are MDE-class under Unified Governance.

## 8. Rationale

Enterprise integration is useful only if the platform can combine external and local capabilities without corrupting the authority model of the source systems. Local processing, indexing, ETL, AI enrichment, automation, and visualization are roles, not automatic ownership claims.

The constraint therefore preserves external source authority, mapping/provenance, explicit uncertainty, and bounded product scope while leaving real authority allocation and integration mechanisms for later authorized architecture.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **All ingested data becomes locally canonical:** rejected because synchronization does not imply authority transfer and would turn the platform into an implicit enterprise-core replacement.
- **External system always wins universally:** not selected because some future bounded domains may legitimately assign authority to `ns_evermore`; choosing a universal winner would be an MDE-level semantic decision beyond this scope.
- **Preserve source authority/provenance and require explicit later authority/conflict decisions:** required.

Connector protocols, schemas, CDC/events, synchronization algorithms, conflict rules, persistence, and queues remain explicitly deferred.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- external source identity / mapping / provenance;
- Authority / Semantic Ownership / Source of Truth / Actual-state Ownership;
- Enterprise Data / Knowledge / ETL;
- Organization external mapping;
- data lifecycle / temporal/freshness semantics;
- failure / unknown / indeterminate / conflict handling;
- cache/index/projection/replica semantics;
- recovery / reconciliation;
- Tenant / Organization / Security / Data / Privacy governance;
- compatibility / migration / conformance;
- offline/degraded enterprise integration.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** external identity and local identity remain explicitly distinguishable unless later accepted mapping semantics establish a relationship; identifier formats are deferred.
- **Revision / Evolution:** source/mapping revisions and relevant freshness context must remain representable; concrete versioning is deferred.
- **Authority / Semantic Ownership:** automatic transfer is prohibited; concrete authority allocations remain downstream/MDE-governed.
- **Source of Truth / Actual-state Ownership:** external SoT preservation is closed as a constraint; specific domain owners remain undecided.
- **State / Lifecycle / Temporal:** source versus copy/derived state and relevant stale/fresh conditions must remain explicit; concrete lifecycle/clock mechanisms are deferred.
- **Failure / Unknown / Indeterminate:** stale/conflicting/missing/unknown/indeterminate/unmapped conditions cannot be silently canonicalized.
- **Tenant / Organization:** `NSE-001..003` remain controlling; external identities/mappings cannot redefine Tenant or force one Organization system globally canonical.
- **Principal / Authentication / Authorization / Policy:** imported identity or organization facts do not create authorization authority automatically; downstream policy semantics are deferred.
- **Security / Data / Privacy / Trust:** source provenance and applicable governance remain required; mechanisms are deferred.
- **Serialization / Representation:** no connector/external schema/wire format is selected.
- **Offline / Degraded:** `NSE-004` applies; external unavailability does not transfer authority to local replicas.
- **Recovery / Reconciliation:** explicit source/provenance/conflict state is required; no winner or algorithm is selected.
- **Compatibility / Migration:** integration evolution cannot silently reinterpret local copies as source facts.
- **Conformance:** later tests must prove no automatic authority transfer through ingestion/processing/storage.
- **Cross-boundary Dependency:** external systems may remain authoritative dependencies while local processing remains bounded; protocols are deferred.
- **Invariant / Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner changes the bounded-enterprise-integration product non-goal, permits synchronization/ingestion to transfer Source-of-Truth authority automatically, or explicitly redefines `ns_evermore` as a universal replacement authority for external enterprise-core systems.

Changing connector products, middleware, ETL frameworks, CDC/event technology, external schemas, databases, caches, queues, indexing technology, or synchronization algorithms is not by itself a revalidation trigger.

## 13. Status

```text
NSE-011
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```
