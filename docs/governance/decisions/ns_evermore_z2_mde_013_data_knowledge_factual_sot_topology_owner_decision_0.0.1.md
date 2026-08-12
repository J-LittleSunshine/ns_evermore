# NGRP-001 Z2 MDE-013 — Data / Knowledge Factual Source-of-Truth Topology Owner Decision

- **Decision ID:** `Z2-MDE-013`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Decision Entry HEAD:** `17d4f8e083e65d53ee328b546c2edd13320dd3bf`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-012`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

What Project-level Source-of-Truth topology governs factual Data / Knowledge assertions across `ns_evermore` and bounded external enterprise systems?

This decision is distinct from `Z2-MDE-012`, which assigns native Enterprise Data / Knowledge / Foundational ETL **Semantic Authority** to `ns_server`.

This decision governs factual canonical ownership. It does not select a database, warehouse, lake, vector store, cache, index, ETL engine, schema, protocol, queue, API, persistence topology, or reconciliation algorithm.

## 2. Classification

```text
Classification
MDE

Reason
Source-of-Truth ownership and major cross-domain factual authority topology are Project-Owner-reserved under Unified Governance.
NSE-011 requires explicit preservation of bounded external Sources of Truth and prohibits synchronization, ETL, storage, indexing, caching, projection, replication or aggregation from automatically transferring Source-of-Truth authority.
```

## 3. Alternatives Presented to Project Owner

### A — Centralized Factual SoT in `ns_server`

All facts formally entering the Data / Knowledge Foundation become canonically owned by `ns_server`, with external systems becoming upstream sources rather than final SoTs.

### B — Governed Per-Semantic-Partition SoT Federation

`ns_server` remains the native Data / Knowledge semantic authority, while each bounded factual semantic partition has exactly one explicitly declared final SoT. Different semantic partitions may have different final SoTs, including external enterprise systems or native `ns_evermore` authorities.

### C — External-master-first SoT

External enterprise systems own factual SoT by default, while `ns_server` primarily provides integration, ETL, derived-data, knowledge and projection semantics except for explicitly native facts.

## 4. Recommendation Presented

`B — Governed Per-Semantic-Partition SoT Federation`.

Rationale: this preserves a real native Data / Knowledge platform semantic layer without silently turning ingestion or ETL into authority transfer. It also preserves bounded external factual authorities such as HIS, ERP, CRM, MES, HR, OA and finance systems while allowing `ns_evermore`-native facts and knowledge assets to have native SoTs where explicitly established.

## 5. Project Owner Decision

```text
Selected Option
B

Data / Knowledge Factual SoT Topology
→ GOVERNED_PER_SEMANTIC_PARTITION_SOT_FEDERATION
```

The Project Owner explicitly selected Option `B` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY consume the following Owner-decided facts:

```text
Enterprise Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server

Factual Source of Truth
→ declared per bounded semantic partition

Each bounded semantic partition
→ exactly one declared final SoT

Different bounded semantic partitions
→ MAY have different final SoTs

Multiple final SoTs for the same semantic assertion
→ PROHIBITED
```

Examples of legally valid topology include, subject to later detailed design:

```text
HIS clinical source facts
→ HIS MAY remain final bounded SoT

ERP financial source facts
→ ERP MAY remain final bounded SoT

HR employee-master facts
→ HR MAY remain final bounded SoT

ns_evermore-native Knowledge Assets
→ native ns_evermore authority MAY be final SoT where explicitly established

ns_evermore-native Application Data
→ applicable accepted native authority MAY be final SoT where explicitly established
```

These examples establish topology semantics only; they do not pre-assign every concrete future entity or dataset to a specific SoT.

## 7. Derived Fact / Processing Rules

The following are permanent non-transfer rules for downstream synthesis:

```text
Synchronization != Authority Transfer
Import != Authority Transfer
ETL Output != Upstream Source Fact automatically
Derived / Aggregated Fact != Source Fact automatically
Index != Source of Truth automatically
Cache != Source of Truth automatically
Projection != Source of Truth automatically
Local Replica != External Authority Replacement automatically
Vector Representation != Canonical Knowledge automatically
Embedding != Canonical Knowledge automatically
RAG Consumption != Knowledge Authority Transfer
Visualization != Data Authority Transfer
Storage Placement != Source of Truth
```

Derived facts MUST retain derivation identity and provenance sufficient to distinguish them from upstream source assertions. Their own bounded semantic authority/SoT, where material, must be explicitly established rather than inherited from the source or processing location.

## 8. Failure / Unknown / Conflict Obligations

Later authorized Data / Knowledge Architecture must preserve explicit semantics for:

```text
source identity
SoT binding
source revision / freshness where applicable
stale
missing
unknown
indeterminate
conflicting
unmapped
transformation / derivation provenance
reconciliation status
```

A conflict MUST NOT be resolved merely because one copy is local, newer by arrival order, present in a preferred database, processed by ETL, indexed, cached, vectorized, or more convenient to consume.

## 9. Cross-domain Non-transfer

```text
Business Application consumes Data / Knowledge
→ no SoT transfer

Automation consumes or produces Data / Knowledge
→ no automatic SoT transfer

AI Agent RAG / tool consumption
→ no Knowledge/Data Authority transfer

ns_node source-fact production
→ no automatic canonicalization

ns_web visualization / management
→ no SoT transfer

ns_runtime transport / coordination
→ no SoT transfer

Shared Foundation storage/cache mediation
→ no SoT transfer
```

## 10. Explicit Non-implications

This decision does NOT establish:

```text
ns_server = universal enterprise factual SoT
External system = always final SoT
Latest write = conflict winner
Local copy = canonical
ETL output = source fact
Data storage location = factual authority
Data / Knowledge Semantic Authority = every factual SoT
One database = one semantic partition
One semantic partition = one table/schema/database
```

It also does not decide persistence, API, wire protocol, schema, CDC/event technology, database topology, query engine, warehouse/lake/vector technology, synchronization algorithm, reconciliation winner, or detailed Data / Knowledge internal architecture.

## 11. Constraint Preservation

This decision preserves:

- `NSE-001` native Tenant semantic invariance;
- `NSE-002/003` Tenant / Organization non-collapse and Organization plurality;
- `NSE-004` offline governance invariance;
- `NSE-006` first-class domain non-subordination and authority non-transfer;
- `NSE-008` local source/effect accountability without locality-based canonicalization;
- `NSE-009` contract representation independence;
- `NSE-011` bounded external Source-of-Truth preservation;
- `NSE-012` Shared Foundation authority neutrality;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 12. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Responsibility / Authority / SoT Matrix;
- Cross-component Semantic Dependency Topology;
- later Data / Knowledge Architecture;
- later external enterprise integration design;
- later Agent/RAG, Automation and Business Application designs where factual authority is consumed;
- later recovery/reconciliation design.

No later phase is authorized by this decision.

## 13. Revalidation Trigger

Revalidation is required if the Project Owner later changes one or more of:

- native Data / Knowledge semantic authority;
- bounded external Source-of-Truth preservation;
- the rule requiring one final SoT per bounded semantic partition;
- the prohibition on processing/placement-based automatic authority transfer;
- the product boundary relative to external enterprise-core systems.

Changing database, ETL, index, cache, vector, RAG, warehouse, transport, provider or deployment technology does not by itself revalidate this decision.

## 14. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
