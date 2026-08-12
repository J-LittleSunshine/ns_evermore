# NGRP-001 Z2 MDE-012 — Enterprise Data / Knowledge / Foundational ETL Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-012`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Decision Parent HEAD:** `f611903e4037643c4c6fcff61298eae1edacdb2f`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; current Z2 Batch 1 authorization; `Z2-MDE-001..011`
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final native semantic authority for the `Enterprise Data / Knowledge / Foundational ETL` first-class capability domain?

This decision concerns the platform meaning and governance of Enterprise Data Foundation, Knowledge Base, platform-managed Data/Knowledge definitions, foundational ETL semantic identity, transformation/derivation semantics, and applicable query/aggregation platform semantics.

It does **not** assign universal factual Source-of-Truth ownership to `ns_server`, does not transfer bounded external source authority, and does not select database, warehouse, search, vector, cache, ETL, schema, model, protocol, provider, or persistence topology.

## 2. Classification

```text
Classification
MDE

Reason
Major cross-domain Semantic Ownership / Data-Knowledge Authority is Project-Owner-reserved under Unified Governance.
```

## 3. Alternatives Presented

### A — `ns_server` owns native Data / Knowledge / ETL Semantic Authority

`ns_server` owns final platform semantics for Enterprise Data Foundation, Knowledge Base, foundational ETL, platform-managed Data/Knowledge definitions, transformation/derivation meaning, and applicable query/aggregation semantics. External systems may retain bounded factual SoT.

### B — External systems collectively own Data / Knowledge Semantic Authority

External enterprise systems define platform Data/Knowledge semantics and `ns_server` acts mainly as integration/ETL/projection/index layer.

### C — Federated Data / Knowledge Semantic Authorities

Multiple internal/external authorities jointly own distinct semantic partitions of the platform Data/Knowledge model.

## 4. Recommendation Presented

`A — ns_server owns native Enterprise Data / Knowledge / Foundational ETL Semantic Authority`.

Rationale: Constitution already places Knowledge Base, Enterprise Data/Knowledge Foundation and foundational ETL in `ns_server`, while accepted `NSE-006` and `NSE-011` prohibit cross-domain authority transfer and preserve bounded external SoT. Option A provides one native platform semantic owner without converting local storage, ETL, indexing, RAG, visualization or ingestion into factual authority.

## 5. Project Owner Decision

```text
Selected Option
A

Native Enterprise Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server
```

## 6. Normative Consequences for Current Batch

```text
ns_server
→ owns native Enterprise Data / Knowledge / Foundational ETL semantic authority

ns_agent
→ may consume Knowledge / RAG and derived context
→ does not gain Knowledge/Data Authority through consumption

ns_web
→ may manage, configure and visualize Data/Knowledge
→ does not gain canonical authority through UI state or editing

ns_runtime
→ may transport/coordinate applicable work
→ does not gain Data/Knowledge Authority through mediation

ns_node
→ may produce local source facts and perform governed local effects
→ does not gain canonical Data Authority through locality

External enterprise systems
→ MAY retain bounded factual Source-of-Truth authority where explicitly declared
→ ingestion/synchronization/ETL/index/cache/projection/replication/aggregation do not automatically transfer that authority
```

## 7. Explicit Non-Implications

```text
Native Data / Knowledge Semantic Authority
!= Every Factual Source of Truth

Data Storage
!= Business Authority

ETL Output
!= Upstream Source Fact automatically

Knowledge Index
!= Knowledge Source of Truth automatically

Vector / Embedding / Projection
!= Canonical Knowledge automatically

Agent RAG Consumption
!= Knowledge Authority Transfer

Visualization
!= Data Authority Transfer

Same ns_server placement
!= first-class capability subordination
!= common semantic domain
!= common Source of Truth
```

## 8. First-class Capability Preservation

The four principal capability domains remain permanently:

```text
Business Application Construction / Runtime
Automation Construction / Execution
AI Agent Runtime / Tooling
Enterprise Data / Knowledge / Foundational ETL
→ FIRST_CLASS / PARALLEL / NON_SUBORDINATE
```

Current semantic-authority placement does not create a parent/child relationship among these domains.

## 9. Constraint Preservation

This decision preserves, in particular:

- `NSE-001..004` Tenant/Organization/offline invariants;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` first-class domain non-subordination and authority non-transfer;
- `NSE-009` representation-independent stable cross-boundary semantics;
- `NSE-011` external Source-of-Truth preservation;
- `NSE-012` Shared Foundation authority neutrality/provider replaceability;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 10. Downstream Consumers

This Owner decision is an authorized input to the current Project Architecture Candidate, the Batch 1 Responsibility / Authority / SoT Matrix, cross-component semantic dependency topology, and later Data/Knowledge/ETL detailed architecture when separately authorized.

Specific factual SoT allocations, derived-fact ownership, canonical knowledge rules, actual-state ownership, data lifecycle, query contracts, storage topology, ETL topology and provider selection remain outside this MDE unless separately resolved by later authorized decisions.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes the native Data/Knowledge/ETL capability boundary, moves its semantic authority away from `ns_server`, changes first-class non-subordination, or permits ingestion/processing/storage placement to transfer factual authority automatically.

Changes in database, warehouse, search, vector, ETL, cache, provider, process, deployment, package or framework technology do not by themselves revalidate this decision.

## 12. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
