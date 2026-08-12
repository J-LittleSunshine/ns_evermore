# NGRP-001 Z2 MDE-006 — Organization Source-of-Truth Topology Owner Decision

- **Decision ID:** `Z2-MDE-006`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Decision Parent HEAD:** `6eb708c8c4814fe80d8c876e57b7adb0ba8a8d60`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-005`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

What Project-level Source-of-Truth topology governs Organization facts when one Tenant may contain multiple native and externally integrated Organization Systems?

This decision does **not** reopen `Z2-MDE-005`. Native Organization Semantic Authority remains owned by `ns_server`.

This decision distinguishes:

```text
Organization Semantic Authority
!=
Organization factual Source of Truth for every bounded Organization semantic partition
```

It does not select persistence, tree/graph representation, synchronization protocol, mapping algorithm, conflict-resolution algorithm, external connector, database, runtime process, transport, or storage technology.

## 2. Classification

```text
Classification
MDE

Reason
Source-of-Truth ownership/topology is Project-Owner-reserved under Unified Governance.
Organization plurality and external integration make a single implicit SoT inference unsafe.
Accepted NSE-003 requires multiple Organization Systems and structural plurality.
Accepted NSE-011 prohibits synchronization, ingestion, replication, caching, or local storage from automatically transferring external Source-of-Truth authority.
```

## 3. Alternatives Presented to Project Owner

### A — Centralized Organization SoT in `ns_server`

All Organization facts ingested into `ns_evermore` become canonical in `ns_server`. External systems provide source inputs but do not retain final bounded SoT after canonicalization.

### B — Governed Per-Organization-System SoT Federation

`ns_server` retains native Organization Semantic Authority, while each bounded Organization semantic partition has exactly one explicitly declared final Source of Truth. Different Organization Systems or bounded semantic partitions MAY therefore have different SoTs, including `ns_server` for platform-native Organization facts and external enterprise authorities for bounded externally mastered facts.

### C — External-master-first Organization SoT

External enterprise systems are presumed to own Organization factual SoT by default, with `ns_server` acting primarily as mapping/cache/projection boundary.

## 4. Recommendation Presented

`B — Governed Per-Organization-System SoT Federation`.

Rationale: this preserves one platform-native Organization semantic authority while respecting the constitutional requirement for multiple Organization Systems and the accepted external-SoT preservation rule. It avoids both universal central canonicalization and an external-master-first product dependency.

## 5. Project Owner Decision

```text
Selected Option
B

Organization Source-of-Truth Topology
→ GOVERNED_PER_ORGANIZATION_SYSTEM_SOT_FEDERATION

Native Organization Semantic Authority
→ ns_server
```

The Project Owner explicitly selected Option `B` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The Project Architecture candidate MAY consume the following Owner-decided facts:

```text
Native Organization Semantic Authority
→ ns_server

Organization factual SoT
→ explicitly bound per bounded Organization semantic partition / Organization System

Each bounded Organization semantic partition
→ exactly one declared final SoT

Different bounded Organization semantic partitions
→ MAY have different final SoTs

Platform-native Organization facts
→ MAY use ns_server as final SoT where later accepted architecture assigns that partition to ns_server

Externally mastered Organization facts
→ MAY retain the applicable external authority as bounded final SoT

Synchronization / ingestion / replication / cache / index / projection / local persistence
→ MUST NOT transfer SoT automatically
```

The following is prohibited:

```text
same bounded semantic partition
→ multiple final SoTs
```

A statement such as `HR and ns_server are both authoritative for the same Organization fact` is invalid unless a later accepted architecture first partitions the semantics into distinct, non-overlapping authority/SoT dimensions.

## 7. Semantic Authority / SoT Separation

This decision permanently preserves the distinction:

```text
ns_server
→ defines native ns_evermore Organization semantics

A declared bounded SoT
→ supplies canonical factual state for its assigned Organization semantic partition
```

Therefore:

```text
External Organization SoT
!= External Organization Semantic Authority for ns_evermore

Organization Semantic Authority in ns_server
!= ns_server SoT for every Organization fact automatically

Mapping
!= Identity Equality

External Organization System
!= Global Canonical Organization automatically
```

## 8. Failure / Unknown / Temporal Obligations

Later authorized Organization / Component / Integration design MUST preserve explicit states for applicable:

```text
source unavailable
source stale
source revision unknown
mapping unresolved
mapping conflicting
historical source interpretation
reconciliation pending
SoT binding unknown / indeterminate
```

None of these conditions may be silently resolved by `local wins`, `external wins`, `latest write wins`, or storage locality unless separately accepted by the proper later authority.

This decision does not define the concrete handling algorithm.

## 9. Offline / Degraded Implication

Private/offline or disconnected operation MUST NOT automatically transfer a bounded external Organization SoT to a local replica or to `ns_server`.

Locally available Organization facts MAY be consumed under later-designed freshness, provenance, policy, and degraded-operation rules, but availability or locality alone does not change their Source-of-Truth ownership.

Any material offline fail-open/fail-closed or canonicalization policy remains separately MDE-governed where applicable.

## 10. Explicit Non-Implications

This decision does not establish:

```text
one concrete Organization System inventory
one external HR/AD/ERP binding
one Organization database
one mapping schema
one synchronization protocol
one reconciliation winner
one freshness algorithm
one temporal storage model
one Organization persistence representation
one runtime topology
one API / Contract schema
```

It also does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Contract Design, Provider Design, Implementation Planning, IWP, or coding.

## 11. Constraint Preservation

This decision preserves:

- `NSE-001` native Tenant semantic invariance;
- `NSE-002` Tenant / Organization non-collapse;
- `NSE-003` Organization structural plurality and extensibility;
- `NSE-004` offline governance invariance;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` authority non-transfer through composition;
- `NSE-011` external Source-of-Truth preservation;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 12. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- later Organization Architecture and Component responsibility refinement;
- later external enterprise integration design;
- later recovery/reconciliation and offline/degraded design;
- later stable Contract design where Organization source identity/provenance crosses boundaries.

No later phase is authorized by this decision itself.

## 13. Revalidation Trigger

Revalidation is required if the Project Owner later changes:

- native Organization Semantic Authority away from `ns_server`;
- the requirement for multiple Organization Systems / structural plurality;
- the per-bounded-partition single-final-SoT rule;
- the rule that external SoT may be preserved after synchronization;
- the bounded enterprise integration product semantics.

Changes in database, connector, protocol, cache, index, process, deployment topology, package structure, framework, or mapping implementation do not by themselves revalidate this decision.

## 14. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, does not declare Project Architecture globally complete, and does not authorize downstream detailed design or implementation work.
