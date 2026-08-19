# NGRP-001 — Component Internal Design / ns_server / Batch 4 Candidate

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Component Internal Design / ns_server / Batch 4`
- Authorization Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_4 / DATA_KNOWLEDGE_ETL_DOMAIN_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Recovered Entry HEAD: `e77b0c9a6e6a6d1bfed59318a6acfdce46bac7db`
- Recovered Global State: `GAC-EPOCH-0054`
- State Verified Through HEAD: `36717c982ce0d30592516dcd11ce07f91b9a75fd`
- Decision Registry at entry: `0.0.19 / CURRENT / NORMATIVE`
- Authorized Boundary: `S7 — Enterprise Data / Knowledge / Foundational ETL Governance`
- Inherited Runtime Role: `SV-R03 — Data / Knowledge / ETL Runtime Participant`
- Mandatory Owner Input: `CID-SV-B4-MDE-001 / Option A / Native S7 Canonical Definition SoT = ns_server`
- Producing-session authority: bounded Component Internal Design DAD only; no Global Acceptance authority.
- Candidate Status: `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`

This artifact refines only accepted `S7` responsibility and the accepted `SV-R03` runtime partition. It defines architecture-level internal responsibilities and stable semantic contracts. It does not define Django Apps, Python packages/classes, ORM models, tables, database schemas, REST/RPC/gRPC/WebSocket APIs, wire envelopes, source/visual DSLs, AST/IR, ETL engines, schedulers, workers, queues, CDC technology, databases, warehouses, lakes, search/vector stores, embedding/model providers, RAG frameworks, connector protocols, concrete query languages, providers, repository layout, implementation planning, IWP or code.

---

# 1. Fresh Repository Recovery

Fresh Repository Recovery was completed before S7 synthesis.

```text
Actual Branch HEAD at recovery
→ e77b0c9a6e6a6d1bfed59318a6acfdce46bac7db

Current Global State
→ GAC-EPOCH-0054

State Verified Through HEAD
→ 36717c982ce0d30592516dcd11ce07f91b9a75fd

State-to-HEAD
→ ahead by exactly 1 commit

Changed file
→ docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md only

Delta meaning
→ GAC-EPOCH-0054 / ns_server Batch 4 S7 authorization seal

Delta Classification
→ EXPECTED_GOVERNANCE

UNAUTHORIZED_PROGRESSION
→ NONE

UNEXPLAINED_DRIFT
→ NONE
```

The complete Current Required Read Set embedded in the actual Global State was consumed, including Constitution, Unified Governance, Global State, Working State, Decision Registry `0.0.19`, NSE index, Project Architecture, accepted five-component boundary evidence, Runtime Responsibility Architecture, Foundation readiness, accepted ns_server Batch 1/2/3 Global Acceptance evidence, S7 remaining-pressure and entry-readiness assessments, exact S7 Owner/MDE decisions, dual-authoring/interoperability/trial Owner capability decisions and the relevant Global Architecture Ledger tail.

Recovery reconstruction:

```text
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Internal Boundaries → GLOBAL_ACCEPTED
Runtime Responsibility Architecture → GLOBAL_CLOSED / COMPLETE
Shared Foundation stack → GLOBAL_CLOSED / COMPLETE
Component Internal Design Readiness → SATISFIED

ns_server Batch 1 → GLOBAL_ACCEPTED
ns_server Batch 2 → GLOBAL_ACCEPTED
ns_server Batch 3 → GLOBAL_ACCEPTED

CID-SV-B4-MDE-001 → OWNER_DECIDED / PERSISTED / Option A
Open MDE → 0
Unpersisted Owner Decision → 0
Blocking Item → NONE
Known Working-branch Drift → NONE
Current Authorized Phase → ns_server Component Internal Design / Batch 4 / S7
Recovery Gate → PASS
```

Ledger continuity is explicit: GAC-EPOCH-0051 raised the S7 Definition-SoT Owner gate, GAC-EPOCH-0052 persisted Option A, GAC-EPOCH-0053 established S7 entry readiness, and GAC-EPOCH-0054 separately authorized this exact Batch. No Registry/State/Ledger contradiction remains.

---

# 2. Accepted Upstream Baseline

## 2.1 First-class Domain / Semantic Authority

```text
Enterprise Data / Knowledge / Foundational ETL
→ FIRST_CLASS / PARALLEL / NON_SUBORDINATE

Native Enterprise Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server
```

S7 may be consumed by Business Application, Automation, Agent and discovery experiences. Consumption does not subordinate S7 or move its semantic authority.

## 2.2 Native S7 Canonical Definition SoT

Owner-decided `CID-SV-B4-MDE-001` establishes:

```text
Native S7 Data / Knowledge / Foundational ETL Canonical Definition SoT
→ ns_server

Semantic Authority
!= Canonical Definition SoT
```

Co-location is an explicit Owner result, not an inference that semantic authority always implies Definition SoT.

## 2.3 Factual Data / Knowledge SoT

Owner-decided `Z2-MDE-013` remains controlling:

```text
Factual Data / Knowledge SoT
→ GOVERNED_PER_SEMANTIC_PARTITION_SOT_FEDERATION

Each bounded factual semantic partition
→ exactly one declared final SoT

Different bounded partitions
→ MAY have different final SoTs

External enterprise systems
→ MAY remain final factual SoTs
```

Permanent non-transfer:

```text
Native Definition SoT != Factual Data / Knowledge SoT
Import != Authority Transfer
Synchronization != Authority Transfer
ETL != Authority Transfer
ETL Output != Upstream Source Fact automatically
Derived / Aggregated Fact != Upstream Source Fact automatically
Index != SoT automatically
Cache != SoT automatically
Projection != SoT automatically
Replica != SoT automatically
Vector Representation != Canonical Knowledge automatically
Embedding != Canonical Knowledge automatically
RAG Consumption != Knowledge Authority Transfer
Storage Placement != SoT assignment
```

## 2.4 Complete Dual Authoring / Interoperability

```text
Complete System-level SDK / Source Authoring
→ REQUIRED

Complete ns_web Visual Authoring
→ REQUIRED

Both
→ same governed S7 semantic domain

Bidirectional Source↔Visual Semantic Interoperability
→ REQUIRED

Silent Semantic Loss
→ PROHIBITED

Silent Destruction of Semantically Relevant Information
→ PROHIBITED

Lossless Representation Round-trip
→ NOT REQUIRED
```

## 2.5 Lifecycle Separation

```text
Mutable Authoring Candidate
!= Canonical Native S7 Definition Revision

Definition Validation
!= Semantic Certification
!= Candidate Artifact
!= Formal Artifact Acceptance
!= Formal Execution Admission
!= Runtime Operation

ETL Definition
!= ETL Runtime Operation
!= ETL Output Fact

Knowledge Definition
!= Indexed / Vector / Embedding Representation
!= Retrieval Result
```

Formal Artifact Acceptance and Formal Execution Admission remain `S8 / ns_server` authorities.

## 2.6 Runtime Actual-state Baseline

```text
SV-R03
→ Data / Knowledge / ETL Runtime Participant

Same bounded runtime assertion
→ exactly one final Actual-state owner
```

S7/SV-R03 must not absorb:

```text
Formal Admission → S8 / SV-R04
Scheduling / Routing / Dispatch → RT-R02
Cross-component coordination-stage continuation → RT-R03 where applicable
Business Application runtime → S5 / SV-R01
Automation runtime → S6 / SV-R02
Server-local generic background runtime → S10 / SV-R06 later design
Node Attempt / Effect → ND-R02 / ND-R03
Agent Runtime → applicable ns_agent runtime role
Human Task Aggregation → S11 / SV-R07
Notification Lifecycle → S12 / SV-R08
Discovery Projection → S13 / SV-R09
External factual assertion → its declared final factual SoT
```

## 2.7 Governed Trial Baseline

```text
Governed Pre-production Trial
→ REQUIRED

Universal Fully Isolated Simulation
→ NOT REQUIRED

Definition Valid != Trial Successful
Trial Successful != Artifact Accepted
Trial Successful != Production Admitted
Trial Execution != Production Execution
Trial Success != Production Success Guarantee
Dry-run / Preview != No Effect automatically
```

## 2.8 Accepted Batch-1/2/3 Contract Inputs

```text
RCP-01 Governance Context
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-02 Admission Evidence
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-19 Desired / Applied Config
→ CLOSED AT DESIGN-SEMANTIC LEVEL

S8 Artifact Identity / Acceptance Evidence
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-17 Automation side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-17 Business Application side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-23 S5 / SV-R01 contribution
→ CLOSED AT CURRENT DESIGN LEVEL
```

Batch 4 may close only the S7 side of RCP-17 and the S7/SV-R03 contribution to RCP-23. Full cross-domain/full server-native closure remains forbidden.

---

# 3. Design Principles

1. **Definition Authority is distinct from factual authority.** Native S7 definitions are canonical in `ns_server`; external and native factual partitions retain independently declared final SoTs.
2. **Representation is not semantic identity.** A Definition identity/revision is independent of source file, visual model, database row, schema object, connector object, index entry or vector record.
3. **Mutable authoring is non-canonical.** Source/visual candidates may evolve; canonical revisions are stable historical semantic snapshots.
4. **External schema is evidence/reference, not native Definition automatically.** Mapping creates governed native interpretation without canonicalizing the source schema or source fact.
5. **Processing does not transfer authority.** Mapping, ETL, transformation, derivation, aggregation, indexing, vectorization and RAG retrieval preserve source/factual-owner provenance.
6. **Runtime success is semantic, not mechanical.** Source/provider/connector/ETL/index success is evidence only; SV-R03 derives S7 semantic result under the exact pinned native Definition revision.
7. **Knowledge semantics are not retrieval infrastructure.** Canonical Knowledge Definition or factual/derived Knowledge state is distinct from index/vector/embedding/retrieval projection.
8. **Query/Aggregation semantics are bounded.** S7 owns semantic interpretation/provenance/completeness/freshness where genuinely in S7 scope, not a universal query language or BI engine.
9. **History is exact-revision/source-evidence pinned.** Current Definition, mapping, source schema, SoT binding or source state never silently rewrites historical interpretation.
10. **Offline evidence is qualified evidence, not authority transfer.** Local copies remain source-qualified; reconnect does not imply reconciliation.
11. **Persistence custody is not Authority/SoT by placement.** Databases, caches, indexes and storage providers remain authority-neutral mechanics.
12. **Foundation consumption is one-way and authority-neutral.** Product responsibility → Stable Entry → Foundation Contract → Foundation Module → Provider Family where applicable → replaceable realization.
13. **Internal Module is semantic architecture, not physical structure.** Module != Django App != Python package != class != service != process != worker != table != database schema != deployment unit.

---

# 4. S7 Internal Responsibility Pressure Map

| Pressure | Stable responsibility required | Principal owner |
|---|---|---|
| Native S7 Definition identity | stable semantic subject independent of representation/revision | DK01 |
| Canonical Definition revision/current/history | stable revision, lineage, applicability, historical interpretation | DK01 |
| Accepted Definition SoT custody | semantic current/history custody inside `ns_server` | DK01 |
| Source/SDK Authoring Candidate intake | mutable candidate, origin/base revision/provenance | DK02 |
| Visual Authoring Candidate intake | same governed candidate semantics | DK02 |
| Source↔Visual interoperability | explicit support/editability/limitation/incompatibility/unknown state | DK02 |
| Definition Validation | exact candidate semantic snapshot validation | DK03 |
| Semantic Certification | exact canonical revision certification evidence | DK03 |
| Candidate Artifact / Acceptance / Admission relationship | evidence handoff without S8 absorption | DK03 |
| Bounded factual semantic partition | representation-neutral factual partition identity | DK04 |
| Final factual SoT binding | exactly one declared final SoT per bounded partition/applicability | DK04 |
| Source identity/owner/freshness/provenance | explicit external/native factual-source reference | DK04 |
| External source schema reference | source-owned schema identity/revision evidence, non-canonical by default | DK05 |
| Mapping Definition | native mapping identity/revision and source→governed semantic interpretation | DK05 |
| Mapping compatibility/reconciliation | schema/mapping evolution and explicit uncertainty | DK05 |
| ETL Definition | exact native ETL semantic definition/revision and required inputs/outputs | DK06 |
| Transformation/derivation definition | governed transformation meaning and lineage requirements | DK06 |
| Derived/aggregated fact semantics | output identity/provenance distinct from upstream facts | DK06 |
| Knowledge Definition / governed Knowledge semantics | native definition lifecycle and factual/derived classification | DK07 |
| Knowledge derivation provenance | source/definition lineage and historical interpretation | DK07 |
| Index/vector/embedding/RAG relationship | projection/representation only; no authority transfer | DK07 |
| Query/Aggregation semantic intent | bounded S7 semantic target/source/qualification | DK08 |
| Query/Aggregation result semantics | derived result provenance, freshness/completeness/partial/unknown | DK08 |
| SV-R03 Runtime Operation | operation identity, exact definitions/bindings/evidence | DK09 |
| S7 semantic runtime Actual-state/result | S7-owned semantic state/result/history only | DK09 |
| RCP-23 S7/SV-R03 evidence | stable runtime evidence contribution | DK09 |
| S7 Trial | trial identity/context/applicability/data-effect boundary/result | DK10 |
| RCP-17 S7 side | S7 Trial semantic contract contribution | DK10 |
| Historical/offline/recovery | exact definition/source/mapping evidence and uncertainty | all |
| Compatibility/migration/conformance | semantic-owner classification without representation lock-in | all |
| Tenant/Org/Principal/Policy/Trust | inherited governed context; no authority merge | all applicable |
| Secret boundary | source/connector credentials referenced only; material custody not invented | DK04/DK05/DK06/DK09/DK10 |

---

# 5. Derived Internal Module Inventory

`DK01..DK10` are document-local navigation labels only. Their stable architecture identity is the responsibility name and meaning.

| Local | Internal Architecture Module | Primary stable responsibility |
|---|---|---|
| DK01 | Native S7 Definition & Canonical Revision Governance | native Definition identity, canonical revision lifecycle, lineage and accepted Definition SoT custody |
| DK02 | Authoring Intake & Semantic Interoperability | source/SDK + visual mutable candidates, provenance and non-destructive semantic interoperability |
| DK03 | Definition Validation & Semantic Certification Evidence | candidate validation, exact-revision certification evidence and S8 lifecycle relationship |
| DK04 | Factual Partition & Source Authority Binding Governance | bounded factual partition identity, final SoT binding semantics, source identity/owner/freshness/provenance |
| DK05 | External Source Schema Reference & Mapping Governance | external schema references, native Mapping Definition/revision, schema-mapping compatibility and reconciliation evidence |
| DK06 | ETL Definition & Transformation / Derivation Governance | ETL Definition/revision, transformation semantics, derived/aggregated output identity and lineage |
| DK07 | Knowledge Definition & Derived Knowledge Governance | Knowledge Definition/asset classification, derivation provenance, index/vector/embedding/RAG non-collapse |
| DK08 | Query & Aggregation Semantic Governance | S7-owned query/aggregation intent/result meaning, provenance, completeness/freshness/uncertainty |
| DK09 | S7 Runtime Operation & Semantic Result | SV-R03 production runtime operation, exact revision/source binding, semantic Actual-state/result/history and RCP-23 S7 contribution |
| DK10 | S7 Trial Semantics & Runtime Evidence | governed S7 Trial identity/context/data-effect boundary and SV-R03 Trial semantic state/result, closing RCP-17 S7 side |

```text
Derived Internal Module Count
→ 10

Authorized Boundary Coverage
→ S7 / 1 OF 1 / 100%

Unowned S7 Responsibility
→ 0

Duplicate Final Responsibility
→ 0

God Module
→ NONE_FOUND

Overfragmentation
→ NONE_FOUND
```

The decomposition deliberately keeps Definition lifecycle, factual authority binding, source mapping, ETL derivation, Knowledge semantics, Query/Aggregation semantics and runtime evidence separate. Combining them into one `Data Platform` module would conflate Definition SoT, factual SoT and runtime Actual-state. Splitting by database/connector/index/provider technology would instead be implementation leakage.

---

# 6. S7 Boundary Coverage Matrix

| S7 responsibility | DK01 | DK02 | DK03 | DK04 | DK05 | DK06 | DK07 | DK08 | DK09 | DK10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Native Definition identity/revision/SoT | P | C | C | C | C | C | C | C | C | C |
| Source/Visual authoring | C | P | C | C | C | C | C | C |  |  |
| Validation/certification | C | C | P | C | C | C | C | C |  | C |
| Factual partition/SoT binding | C | C | C | P | C | C | C | C | C | C |
| External source/schema/mapping | C | C | C | C | P | C | C | C | C | C |
| ETL/transformation/derivation definition | C | C | C | C | C | P | C | C | C | C |
| Knowledge semantics | C | C | C | C | C | C | P | C | C | C |
| Query/Aggregation semantics | C | C | C | C | C | C | C | P | C | C |
| SV-R03 production runtime | C |  |  | C | C | C | C | C | P |  |
| S7 Trial | C |  | C | C | C | C | C | C | C | P |
| History/offline/recovery | P | P | P | P | P | P | P | P | P | P |
| Compatibility/migration/conformance | P | P | P | P | P | P | P | P | P | P |

`P = principal owner`, `C = consumed/contributing responsibility`.

---

# 7. DK01 — Native S7 Definition & Canonical Revision Governance

- **Source Boundary:** S7.
- **Purpose:** realize accepted native S7 Semantic Authority and Canonical Definition SoT as distinct logical responsibilities while owning native Definition identity/revision lifecycle.
- **Owned Responsibility:** Native S7 Definition Identity; canonical Definition Revision; current-vs-historical designation; revision lineage/provenance; applicability/retirement for new governed use; historical resolvability; semantic-diff meaning; semantic persistence custody of accepted native Definition SoT.
- **Explicitly Non-owned:** factual source assertions; external schema authority; source/visual edit representation; Candidate Artifact identity; Formal Acceptance; Formal Admission; runtime operation/attempt/effect; index/vector/embedding state; concrete storage.
- **Definition Identity:** one stable representation-neutral semantic subject across revisions. It is distinct from source file/repository path, visual project, external source schema/object, database key/table, connector identifier, Candidate/Accepted Artifact, runtime operation, factual record and index/vector representation. No UUID/slug/path/key/hash format is selected.
- **Native Definition Subjects:** S7-governed semantic subjects such as native mapping/transformation/ETL definitions, Knowledge Definitions, reusable S7-owned query/aggregation definitions where applicable, and factual-authority binding declarations where they are native governed definitions. This is a semantic classification, not a frozen physical definition-family namespace or artifact format.
- **Revision Rule:** semantic modification creates a new canonical Definition Revision. Historical canonical revisions are never silently mutated in place.
- **Current vs Historical:** current designation may advance; historical Trial/Runtime remains pinned to exact applicable revision.
- **SoT Custody:** `DK01` is the internal semantic custodian of the already Owner-decided native S7 Definition SoT in `ns_server`; this does not create a new Project-level Authority or factual SoT.
- **Persistence:** persistence stores/replicas/caches remain realization mechanics and do not become Definition SoT by placement.
- **Offline:** an authoritative private `ns_server` deployment may exercise the accepted Definition SoT normally; an offline editor/cache/replica does not acquire that SoT by possession.
- **Compatibility:** semantic evolution may be compatible, require explicit migration or require architecture/MDE revalidation according to existing governance classes; physical representation changes alone need not create semantic revision.
- **Revalidation Trigger:** moving Definition SoT, making historical revisions mutable, freezing a major external identifier namespace, or treating representation/storage placement as canonical authority.

---

# 8. DK02 — Authoring Intake & Semantic Interoperability

- **Source Boundary:** S7.
- **Purpose:** provide one mutable authoring lifecycle for complete System-level SDK/source authoring and complete `ns_web` visual authoring.
- **Owned Responsibility:** Authoring Candidate identity; base canonical revision reference where applicable; mutable candidate semantic snapshot; origin surface; author/provenance; candidate reconciliation state; cross-surface semantic interoperability evidence.
- **Non-canonical Rule:** `Authoring Candidate != Canonical Definition Revision`. Neither source repository state nor visual editor state becomes Definition SoT.
- **Candidate Base:** modifications identify the exact canonical base revision or explicitly state that no prior canonical base exists. Candidate divergence from base remains explicit.
- **Validation Target:** validation evidence identifies the exact candidate semantic snapshot evaluated; subsequent semantic modification invalidates silent reuse of older validation applicability.
- **Interoperability Categories:** architecture preserves meanings equivalent to supported+editable, supported+non-editable, representation-limited, unsupported, incompatible, indeterminate and unknown. Exact enum strings are not frozen.
- **Non-destructive Rule:** a receiving surface unable to edit a construct may expose it as non-editable/limited, but cannot silently delete, reinterpret, normalize away or destructively rewrite semantically relevant information.
- **Representation Boundary:** comments, formatting, file organization, visual layout and surface-local metadata are not automatically canonical Product semantics and are not covered by lossless round-trip guarantees unless separately promoted by later governed semantics.
- **Offline/Private:** core authoring/interoperability cannot require mandatory public SaaS Builder, public converter, public registry or Internet-only service. Offline candidate possession remains non-canonical.
- **Reconciliation:** reconnection compares candidate base/provenance with current canonical history; conflict is explicit and never latest-timestamp-wins by default.
- **Revalidation Trigger:** separate source-only/visual-only S7 semantic classes, silent semantic loss, editor/converter becoming Authority/SoT, or upgrade to lossless representation guarantee.

---

# 9. DK03 — Definition Validation & Semantic Certification Evidence

- **Source Boundary:** S7.
- **Purpose:** own S7 semantic validation and certification evidence without absorbing canonicalization, Artifact Acceptance or Execution Admission.
- **Lifecycle Separation:** `Authoring Candidate Validation != Canonical Definition Revision != Domain Semantic Certification Evidence != Candidate Artifact != Formal Artifact Acceptance != Formal Execution Admission`.
- **Validation Target:** an exact Authoring Candidate semantic snapshot plus applicable governance/conformance context.
- **Validation Meaning:** assesses structural/semantic consistency and source/mapping/partition/reference requirements that are statically or semantically provable without claiming runtime truth. Outcomes preserve invalid/unsupported/incompatible/unknown/indeterminate conditions when applicable.
- **Canonicalization Relationship:** successful validation is necessary evidence for governed canonical intake where required by S7 rules but does not itself establish a canonical revision. DK01 owns canonical revision establishment.
- **Certification Target:** Domain Semantic Certification Evidence applies to an exact immutable canonical Definition Revision and records applicable semantic/conformance rule revision, provenance, applicability and diagnostics references.
- **Candidate Artifact Relationship:** when an S7 Candidate Artifact is evaluated, S7 supplies exact Definition identity/revision and applicable Certification Evidence to S8. S8 retains Candidate Artifact identity and Formal Acceptance authority.
- **Admission Relationship:** certification/validation never issues production Admission. S8/SV-R04 remains Formal Execution Admission authority.
- **History:** validation/certification records are history-oriented; later revalidation creates new evidence rather than rewriting prior interpretation.
- **Offline:** unavailable source/conformance evidence remains explicit. Possession of old evidence does not confer authority to issue new certification.
- **Revalidation Trigger:** Certification becoming Formal Acceptance/Admission, independent Certification Authority invention, or major artifact/identity format commitment.

---

# 10. DK04 — Factual Partition & Source Authority Binding Governance

- **Source Boundary:** S7.
- **Purpose:** make the accepted per-semantic-partition factual SoT federation explicit and consumable without centralizing facts in `ns_server`.
- **Owned Responsibility:** bounded factual semantic partition identity; source/final-SoT binding declaration semantics; binding revision/history/applicability; factual source identity/reference; source-owner provenance; freshness/temporal qualification; uncertainty/reconciliation evidence.
- **Partition Identity:** representation-neutral semantic boundary for a class of factual assertions. It is not automatically a table, schema, database, topic, API resource, file, index or Tenant.
- **Exactly-one Rule:** for the same bounded factual assertion and applicable context, exactly one declared final factual SoT is required. Different partitions may legally name different final SoTs.
- **Binding State:** S7 may canonically retain the governed declaration that identifies the final SoT and applicability of a partition; that declaration is Definition/governance state, not the factual assertions themselves.
- **MDE Boundary:** this architecture defines binding semantics only. A strategically material concrete factual-partition assignment with multiple valid long-term alternatives remains Owner/MDE-governed; this Candidate assigns no HIS/ERP/CRM/MES/HR/OA/Finance dataset or other concrete partition.
- **External Preservation:** an external source may remain final factual SoT. A locally stored copy, imported copy, cache, derived projection or indexed representation never replaces it automatically.
- **Freshness:** source evidence may distinguish source-effective/reference time, observed/retrieved time and freshness qualification where available, without selecting clock/token formats.
- **Conflict:** local/newer/more recent arrival/ETL-processed/indexed copies do not win by default. Conflicting evidence remains explicit pending the applicable owner/governance resolution.
- **Tenant/Organization:** factual partition applicability preserves Tenant where required; Organization is a separate semantic dimension and cannot be inferred from Tenant or source-system grouping.
- **Revalidation Trigger:** changing federation topology, assigning a strategic material concrete partition, allowing multiple final SoTs for same assertion, or automatic processing-based authority transfer.

---

# 11. DK05 — External Source Schema Reference & Mapping Governance

- **Source Boundary:** S7.
- **Purpose:** govern external source schema references and native Mapping Definitions without converting external schema or source facts into native Definition state automatically.
- **Owned Responsibility:** external source reference semantics; external schema identity/revision evidence; Mapping Definition identity/revision; mapping applicability; source→native semantic correspondence; compatibility state; reconciliation/provenance history.
- **Schema Boundary:** `External Source Schema != Native S7 Definition automatically`. S7 references source-owned schema identity/revision/provenance as evidence.
- **Mapping Boundary:** `Mapping Definition != Source Fact`. Mapping is native governed semantic interpretation and therefore follows native S7 Definition lifecycle/revision semantics.
- **Revision Pinning:** Mapping revision changes that alter semantic interpretation create a new canonical native revision. Historical runtime/trial retains the exact mapping revision actually applied.
- **Schema Evolution:** source schema changes are evaluated against the applicable Mapping revision. Compatible, representation-limited, incompatible, unsupported, unknown and indeterminate conditions remain explicit; no implicit best-effort coercion may change semantics silently.
- **Source Provenance:** source identity, source authority/SoT binding, schema revision evidence, temporal/freshness qualification and mapping revision are retained sufficiently for historical interpretation.
- **Import/Connector Boundary:** connector/read success is technical evidence only and does not establish mapping semantic success or factual correctness.
- **Offline:** cached schema/mapping/source metadata may become stale. Missing current source evidence remains explicit rather than replaced by local schema assumptions.
- **Secrets:** connector credentials remain Secret References under accepted secret semantics; this module does not select material custody technology.
- **Revalidation Trigger:** external schema becoming native canonical Definition by default, mapping changing factual authority, or concrete protocol/provider/storage lock-in.

---

# 12. DK06 — ETL Definition & Transformation / Derivation Governance

- **Source Boundary:** S7.
- **Purpose:** govern foundational ETL, transformation and derivation semantics independently from runtime attempts and output factual ownership.
- **Owned Responsibility:** ETL Definition identity/revision; transformation/derivation rule identity/revision; input semantic/source requirements; exact mapping references; output semantic partition intent; success/partial semantics; derivation lineage requirements; derived/aggregated factual identity/provenance rules.
- **ETL Definition:** representation-neutral semantic definition of required sources, mappings/transformations, output meaning and S7 semantic success conditions. It does not imply a DAG, workflow engine, scheduler, queue or worker topology.
- **Revision Rule:** semantic change to ETL/transformation meaning creates a new canonical Definition Revision; historical operations retain exact ETL and transformation revisions.
- **Runtime Non-collapse:** `ETL Definition != ETL Runtime Operation != Provider/Engine Attempt != ETL Output Fact`.
- **Derived Fact:** a derived/aggregated fact has its own semantic identity and derivation provenance. It references upstream source facts/evidence and exact mapping/transformation/ETL revisions but is not the upstream fact.
- **Derived SoT:** a derived fact does not become final SoT by production or persistence. Its own bounded factual partition/final SoT must be governed explicitly under DK04 semantics.
- **Semantic Result:** mechanical transformation success is insufficient for S7 semantic success when required source/mapping/quality/semantic conditions are not proven.
- **Partial/Unknown:** missing source evidence, stale input, incompatible mapping, conflicting source assertions or only partially satisfied derivation requirements preserve the strongest provable partial/unknown/indeterminate/conflicting state.
- **Revalidation Trigger:** process engine/scheduler selection becoming architecture authority, output automatically inheriting upstream or local SoT, universal exactly-once/deterministic guarantees, or material conflict-winner policy.

---

# 13. DK07 — Knowledge Definition & Derived Knowledge Governance

- **Source Boundary:** S7.
- **Purpose:** govern native Knowledge Definitions and derived Knowledge semantics while keeping factual/derived knowledge authority distinct from retrieval representations.
- **Owned Responsibility:** native Knowledge Definition identity/revision where applicable; Knowledge semantic classification; knowledge derivation requirements; source/evidence provenance; knowledge revision/history; relationship to indexed/vector/embedding/retrieval projections.
- **Definition vs Factual/Derived State:** a native `Knowledge Definition` follows DK01 canonical Definition SoT. A factual or derived Knowledge assertion/asset instance follows DK04 factual SoT topology. The term `Knowledge Asset` does not by itself determine which category applies.
- **Classification Requirement:** each governed Knowledge subject must remain distinguishable as native Definition state, factual/source-owned Knowledge state, derived Knowledge state, or non-authoritative representation/projection. This Candidate does not globally assign all Knowledge Assets to one SoT class.
- **Derivation Provenance:** derived Knowledge retains source/factual-owner references, exact native Definition/mapping/derivation revisions, temporal qualification and reconciliation state sufficient to explain how the semantic result was established.
- **Index Boundary:** Index is a projection/acceleration representation and not Knowledge SoT automatically.
- **Vector/Embedding Boundary:** Vector representation and embedding are derived representations; provider/model success does not create canonical Knowledge or factual truth.
- **RAG Boundary:** retrieval/RAG consumption is evidence/context consumption. Retrieval success, ranking, chunk match or Agent use does not transfer S7/Knowledge authority.
- **Historical Interpretation:** current embedding/index or current source state cannot be substituted for the historically applicable Knowledge Definition/source/derivation evidence.
- **Offline:** locally available indexes/vectors may be stale/partial and remain qualified projections; they do not become canonical by availability.
- **Revalidation Trigger:** index/vector/embedding becoming canonical Knowledge by default, Agent/RAG consumption transferring authority, or blanket Knowledge-Asset SoT assignment beyond accepted topology.

---

# 14. DK08 — Query & Aggregation Semantic Governance

- **Source Boundary:** S7.
- **Purpose:** own only platform Data/Knowledge query and aggregation semantics that genuinely belong to accepted S7 semantic authority, while leaving syntax/engine/UI technology downstream.
- **Owned Responsibility:** semantic query/aggregation intent identity where needed for runtime/history; target native Definition/factual partition references; applicable source/SoT binding; aggregation interpretation; result semantic qualification; source/derivation provenance; freshness/completeness/partial/unknown semantics.
- **Ad-hoc vs Definition:** one-off Query/Aggregation Intent is runtime input and is not automatically a canonical native Definition. A reusable governed query/aggregation definition, where S7 product semantics establish one, follows DK01 revision lifecycle.
- **Result Boundary:** `Query Result != Source Fact automatically`; `Aggregation Result != Upstream Fact`; dashboard/visualization projection does not become Data SoT.
- **Completeness:** result semantics may distinguish complete/partial/unknown/indeterminate based on explicit evidence about required sources/partitions; no query-engine success implies semantic completeness automatically.
- **Freshness:** result carries temporal/freshness qualification derived from participating source evidence rather than only query execution timestamp.
- **Authority Preservation:** every contributing source/factual owner remains identifiable. Aggregation does not unify factual ownership.
- **No Universal Language:** no SQL-like DSL, GraphQL, semantic-layer language, BI model, search query language or API is selected.
- **Revalidation Trigger:** universal query-language product commitment, result auto-promotion to factual SoT, or query engine becoming Data/Knowledge semantic authority.

---

# 15. DK09 — S7 Runtime Operation & Semantic Result

- **Source Boundary / Runtime Role:** S7 / SV-R03.
- **Purpose:** own the S7-bounded production semantic Runtime Operation Actual-state and result genuinely originating in SV-R03.
- **Operation Identity:** stable representation-neutral S7 Runtime Operation semantic identity, distinct from Definition identity/revision, Trial identity, Admission evidence, dispatch identity, provider/connector attempt, source fact identity, output fact identity and S10 background operation identity.
- **Required Binding:** a production S7 Runtime Operation pins the exact native Definition Revision(s), applicable factual partition/SoT-binding revision(s), mapping/transformation/ETL/Knowledge/query definition revisions as applicable, source evidence references, Governance/Admission references where required and correlation/provenance context.
- **Current-vs-Historical:** current S7 Definition/mapping/source binding never silently rebinds an active/historical Operation.
- **SV-R03-owned Assertions:** S7 semantic Operation existence/identity; exact native revisions used for S7 interpretation; S7 semantic progression/condition; S7 semantic result/outcome; S7 derivation result interpretation; S7-owned history/provenance/correlation; S7 freshness/reconciliation qualification for consumed evidence.
- **Explicitly Non-owned:** external source facts; external source-system runtime facts; RT scheduling/routing/dispatch; RT cross-component coordination facts; Node attempts/effects; provider/connector source facts; S10 generic background attempt facts; Agent/Automation/Business runtime facts; Notification/Human Task/Discovery projection facts.
- **Semantic Success:** provider/source read/connector/ETL engine/index/vectorization success is evidence only. SV-R03 declares S7 semantic success only when the exact pinned Definition semantics and required evidence permit it.
- **Failure Non-equivalence:** an underlying source/provider failure does not automatically imply final S7 semantic failure if the exact pinned Definition semantics permit optional/partial/degraded treatment. Conversely, technical success cannot fabricate semantic success.
- **Uncertainty:** insufficient evidence preserves explicit `UNKNOWN`, `STALE`, `PARTIAL`, `CONFLICTING`, `INDETERMINATE` or `RECONCILIATION_PENDING` semantics as applicable.
- **History:** operation history remains source-qualified and revision-pinned; later current data/definition changes do not rewrite it.
- **Revalidation Trigger:** moving Actual-state ownership, making SV-R03 own external source facts, or creating universal server runtime ownership.

---

# 16. DK10 — S7 Trial Semantics & Runtime Evidence

- **Source Boundary / Runtime Role:** S7 / SV-R03.
- **Purpose:** close the S7 Data/Knowledge/ETL side of RCP-17 at current design level.
- **Owned Responsibility:** S7 Trial Identity; exact native S7 Definition Revision(s) under Trial; Trial Intent; Trial Context; Trial Applicability; Trial Data/Effect Boundary Declaration; resolved source/SoT/mapping evidence; applicable Admission relationship; SV-R03 Trial semantic Actual-state/result; diagnostics/provenance/history/compatibility/conformance.
- **Trial Identity:** distinct from production S7 Runtime Operation identity and from provider/source/Node attempts.
- **Exact Revision:** Trial always identifies exact canonical native Definition revisions under test; `Current Definition Revision != Historical Trial Revision automatically`.
- **Data/Effect Boundary:** declares the intended/allowed data/source/effect scope and known isolation limitations. It is not a universal promise of no external writes, rollback, deterministic simulation or effect virtualization.
- **Source/Output Evidence:** Trial retains references to actual source/effect/output facts and their owners; Trial does not canonicalize them.
- **Admission:** applicable formal Admission may be consumed for the exact Trial execution context when required; Trial success never creates production Admission.
- **Result:** S7 Trial semantic result is derived under the exact trial Definition/context and remains distinct from production outcome.
- **Offline/Private:** Trial remains architecturally realizable in private/offline deployments using available governed capabilities; unavailable source/provider/node evidence remains explicit.
- **RCP-17 Boundary:** `RCP-17 S7 side → CLOSED AT CURRENT DESIGN LEVEL`; `RCP-17 Full Cross-domain Closure → NOT CLAIMED`.
- **Revalidation Trigger:** universal sandbox/no-effect/deterministic replay promise, Trial→Acceptance/Admission collapse, or external factual authority transfer.

---

# 17. Native S7 Definition Identity / Revision Semantics

The architecture-level Definition subject is:

```text
Native S7 Definition Identity
→ stable identity of one governed native S7 semantic subject across canonical revisions
→ independent of source/visual/storage/runtime representation
```

A Canonical Definition Revision is:

```text
one stable governed semantic snapshot
→ immutable in historical meaning
→ successor semantic modification creates a new revision
```

Permanent distinctions:

```text
Definition Identity != Definition Revision
Definition Identity != Source File / Repository Path
Definition Identity != Visual Project
Definition Identity != External Source Schema
Definition Identity != Database Key / Table / Schema
Definition Identity != Candidate Artifact / Accepted Artifact
Definition Identity != Runtime Operation / Trial
Definition Identity != Factual Record
Definition Identity != Index / Vector / Embedding
```

No concrete identity or revision-token format is selected.

Cross-domain references from Business Application, Automation, Agent or later S13 may use the stable S7 Definition identity/revision semantics but do not acquire S7 Authority or Definition SoT.

---

# 18. Factual SoT / Source / Derived Fact Non-collapse

For every bounded factual partition S7 consumes or produces, the architecture retains:

```text
Factual Partition Identity
Declared Final SoT Identity
Binding Revision / Applicability
Source/Factual-owner Provenance
Temporal/Freshness Qualification
Mapping/Transformation/Derivation Revision References where applicable
Reconciliation/Conflict Qualification
```

These semantics do not require a single physical registry or database.

Derived facts preserve:

```text
Derived Fact Identity
!= Upstream Source Fact Identity

Derived Fact Provenance
→ source evidence references
→ source owner / SoT binding
→ exact mapping/transformation/ETL revisions
→ operation/trial correlation
→ temporal/freshness qualification
```

A derived fact may later be declared final SoT for its own distinct bounded semantic partition only through normal factual-SoT governance. Creation, successful ETL or storage is not that declaration.

---

# 19. Source / Visual Authoring Stable Semantics

Both authoring surfaces target the same native S7 canonical semantics.

```text
Source / SDK Candidate
↔ governed S7 semantic candidate
↔ Visual Candidate
```

The stable semantic contract requires:

- exact candidate/base canonical revision identification;
- authoring origin/provenance;
- explicit interoperability condition;
- no silent semantic loss or reinterpretation;
- exact validation target;
- compatibility/conformance feedback;
- preservation of unsupported/non-editable/limited semantic content without destructive conversion;
- no transfer of S7 Authority/Definition SoT to SDK, web editor, converter or generated representation.

Lossless text/layout/source organization round-trip remains outside the product guarantee.

---

# 20. Validation / Certification / Artifact / Admission Relationship

```text
Mutable Authoring Candidate
→ candidate validation by DK03
→ governed canonical revision establishment by DK01
→ semantic certification evidence by DK03 for exact revision
→ Candidate Artifact relationship supplied to S8
→ Formal Artifact Acceptance by S8
→ Formal Execution Admission by S8
→ applicable Runtime/Trial operation
```

No step is collapsed.

```text
Validation Success != Canonicalization automatically
Certification Success != Formal Acceptance
Formal Acceptance != Admission
Admission != Scheduling / Dispatch / Attempt / Effect
```

---

# 21. ETL Runtime / Output / Semantic-result Separation

```text
ETL Definition Revision
→ native S7 Definition state

S7 Runtime Operation
→ SV-R03 semantic runtime state

Provider / Engine Attempt
→ underlying execution/technical evidence owned by applicable source/runtime partition

Output Fact
→ factual/derived assertion with its own provenance/SoT rules

S7 Semantic Result
→ interpretation under exact ETL Definition + required evidence
```

No processing-stage success automatically upgrades any other layer.

---

# 22. Knowledge / Index / Vector / Embedding / RAG Boundary

```text
Knowledge Definition
→ native S7 Definition when product-native

Factual / Derived Knowledge Assertion
→ per bounded factual SoT topology

Index
→ non-authoritative projection/acceleration unless separately and explicitly established otherwise

Vector Representation / Embedding
→ derived representation

Retrieval Result
→ query/projection evidence

Agent RAG Consumption
→ consumer use only
```

No index/vector/embedding/RAG provider or framework becomes S7 semantic authority or canonical Knowledge by successful operation.

---

# 23. Query / Aggregation Boundary

S7 owns semantic interpretation only where the accepted Data/Knowledge domain owns that meaning:

```text
Target semantic subject / partition
Source/factual-owner preservation
Query/Aggregation semantic intent
Applicable definition/revision references
Aggregation/derivation meaning
Result provenance
Freshness / completeness / partial / uncertainty qualification
Historical correlation
```

The following remain explicitly outside this Candidate:

```text
one query language
one SQL-like DSL
GraphQL
one semantic-layer technology
BI engine
search/ranking technology
Dashboard UX
S13 Discovery Query semantics
```

---

# 24. SV-R03 Actual-state Ownership Matrix

| Assertion | Final owner in current architecture | S7 treatment |
|---|---|---|
| S7 semantic Runtime Operation identity/state/result | DK09 / SV-R03 | owns |
| S7 Trial semantic state/result | DK10 / SV-R03 | owns |
| exact S7 Definition revision used | DK01 canonical Definition SoT; DK09/DK10 pin reference | reference + historical binding |
| factual SoT binding declaration | DK04 semantic custody, subject to accepted governance | reference/pin |
| external source fact | declared external/native factual SoT | reference only |
| external source schema fact | external source/schema owner | reference only |
| mapping/ETL Definition | DK01 + DK05/DK06 semantic custody | reference/pin |
| derived output fact | applicable declared factual partition owner | reference/provenance; no automatic ownership |
| RT schedule/route/dispatch | RT-R02 | reference only |
| RT continuation-stage fact | RT-R03 where applicable | reference only |
| Node attempt/effect | ND-R02/ND-R03 | reference only |
| S10 generic background attempt | S10/SV-R06 later | not designed/owned |
| Agent/Automation/Business runtime | applicable accepted source role | reference only |
| Discovery projection | S13/SV-R09 later | contribution only; not owned |

```text
Multiple final owner for same bounded runtime assertion
→ 0
```

---

# 25. S7 Semantic Result vs Source / Provider Fact

S7 semantic result follows a three-layer interpretation discipline:

```text
Layer 1 — Source / Provider / Connector / External technical evidence
→ owned by its legitimate source partition

Layer 2 — Mapping / Transformation / Derivation / Runtime evidence
→ exact operation + definition revisions + evidence linkage

Layer 3 — S7 semantic interpretation
→ DK09/DK10 / SV-R03 only for the S7 semantic assertion
```

Permanent non-equivalences:

```text
Source Read Success != S7 Semantic Success automatically
Connector Success != S7 Semantic Success automatically
ETL Engine Success != S7 Semantic Success automatically
Transformation Success != Factual Correctness automatically
Index Success != Knowledge Semantic Success automatically
Vectorization Success != Knowledge Semantic Success automatically
Retrieval Success != Factual Truth automatically
Provider Failure != final S7 Semantic Failure automatically
```

When evidence is insufficient, the strongest provable uncertainty state is retained rather than guessing success/failure.

---

# 26. RCP-17 — S7 Trial Side Closure

The S7 side is closed at current design-semantic level with stable requirements for:

```text
S7 Trial Identity
exact Native S7 Definition Revision(s) under Trial
Trial Intent / Context / Applicability
Trial Data / Effect Boundary Declaration
Governance / Admission relationship where applicable
Factual source/SoT-binding references
Mapping / transformation / ETL / Knowledge definition revisions
SV-R03 Trial semantic state/result
Underlying source/attempt/effect/output references
Provenance / diagnostics / correlation
History / compatibility / conformance
Offline/private qualification
```

```text
RCP-17 S7 Data / Knowledge / ETL side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-17 Full Cross-domain Closure
→ NOT CLAIMED
```

No universal trial engine or sandbox is introduced.

---

# 27. RCP-23 — S7 / SV-R03 Contribution

The S7 contribution to Server-native Runtime Evidence is closed at current design-semantic level.

Stable producer evidence includes where applicable:

```text
S7 Runtime Operation Identity
exact Native S7 Definition Revision(s)
Factual Partition / SoT Binding Revision(s)
External Source / Source-owner references
Source evidence freshness/temporal qualification
Mapping / transformation / ETL / Knowledge definition revisions
S7 semantic Runtime Actual-state/result
Derived output references and derivation lineage
Governance / Admission evidence references where applicable
Correlation / provenance / historical references
UNKNOWN / STALE / PARTIAL / CONFLICTING / INDETERMINATE / RECONCILIATION qualification
Private/offline compatibility qualification
```

Producer obligations:

- emit only S7/SV-R03-owned semantic assertions as authoritative S7 runtime evidence;
- preserve original owner/provenance for source/effect/output facts;
- pin exact definitions/bindings used;
- never coerce unknown/partial/conflicting evidence into success;
- exclude Secret Material and apply governed redaction;
- preserve historical evidence rather than live-rebinding to current revisions.

Consumer obligations:

- treat SV-R03 evidence as S7 semantic evidence, not as external source fact or universal factual SoT;
- preserve Tenant/Principal/Policy/Trust applicability and source-owner provenance;
- honor exact revision/temporal/uncertainty semantics;
- avoid interpreting missing projection data as nonexistence of source facts.

```text
RCP-23 S7 / SV-R03 Contribution
→ CLOSED AT CURRENT DESIGN LEVEL

Existing S5 / SV-R01 Contribution
→ PRESERVED

RCP-23 Full Server-native Runtime Evidence Closure
→ NOT CLAIMED
→ S10 / SV-R06 contribution remains required
```

No S10 internals are invented.

---

# 28. Historical Interpretation / Source Pinning

Every historical Trial/Runtime interpretation retains sufficient exact references for:

```text
Native S7 Definition Revision(s)
Factual SoT Binding Revision(s)
External Source Identity / Owner
External Source Schema Revision Evidence where available
Mapping / Transformation / ETL Revision(s)
Knowledge Definition / Derivation Revision(s) where applicable
Query/Aggregation semantic intent/revision where applicable
Source evidence temporal/freshness qualification
Governance / Admission references where applicable
Operation / Trial correlation
```

Permanent rules:

```text
Current Definition != Historical Runtime Definition automatically
Current Mapping != Historical Mapping automatically
Current External Schema != Historical Schema Evidence automatically
Current SoT Binding != Historical Binding automatically
Current Source Fact != Historical Source Evidence automatically
Current Index/Embedding != Historical Knowledge Evidence automatically
```

If historical source evidence is unavailable or cannot be verified sufficiently, interpretation remains `UNKNOWN` / `INDETERMINATE` rather than reconstructed from current state.

---

# 29. Offline / Degraded / Recovery / Reconciliation

Offline/degraded correctness preserves:

```text
Offline != Local Authority Transfer
Offline != Local Definition SoT Transfer
Local Replica != Factual SoT automatically
Reconnect != Reconciled
Sync != Authority Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
ETL Arrival Order != Conflict Winner
```

Applicable behavior:

- a disconnected source/visual client may keep mutable Candidate state; it does not canonically commit against an authoritative S7 Definition SoT merely by local mutation;
- an authoritative private `ns_server` deployment may continue normal native Definition governance locally under accepted Product deployment semantics;
- retained canonical revisions/source evidence may be consumed only under their exact applicability/freshness semantics;
- unreachable external source evidence becomes `UNAVAILABLE`, `STALE`, `UNKNOWN`, `PARTIAL`, `CONFLICTING` or `INDETERMINATE` as applicable;
- reconnect initiates re-observation/reconciliation; it does not choose a winner;
- conflict remains explicit until resolved by the legitimate owner/governance rule;
- material fail-open/fail-closed or conflict-winner policy remains an MDE boundary.

---

# 30. Tenant / Organization / Principal / Policy / Trust Boundary

S7 consumes accepted Governance Context and does not redefine it.

```text
Tenant
→ mandatory native governance dimension where applicable

Organization
→ separate semantic dimension
→ never equivalent to Tenant

Principal / IAM
→ S1 authority

Policy
→ S3 authority

Trust
→ S4 authority

Artifact Acceptance / Admission
→ S8 authority
```

Authoring, source binding, mapping, runtime, Trial, query/aggregation and Knowledge consumption preserve applicable governance context. Source-system organization structure or data partitioning never silently becomes Tenant identity.

```text
Authoring Surface Change != Tenant Change
Source System Identity != Tenant automatically
Organization != Tenant
Authentication != Policy Permit != Admission
Provider Success != Trust
```

---

# 31. Configuration / Secret Boundary

S7 owns semantic meaning of its S7-specific configuration items, while managed desired state remains S9 and applied runtime state belongs to the applicable runtime owner.

```text
Configuration Item Semantic Meaning → applicable S7 responsibility
Managed Desired Configuration → S9
Applied S7 Runtime Configuration → applicable SV-R03/S7 runtime partition where genuinely S7-owned
Observed Projection → not Applied SoT
```

Credentials/tokens/keys are referenced through Secret Reference semantics where required.

```text
Configuration != Secret Material
Secret Reference != Secret Material
Diagnostic / Provenance Evidence != Permission to disclose Secret Material
```

No secret store/KMS/HSM/provider/encryption format is selected.

---

# 32. Shared Foundation Consumption

S7 consumes accepted Foundation semantics only through the accepted dependency direction:

```text
Product Component Internal Responsibility
→ Stable Entry
→ Foundation Contract
→ Foundation Module
→ Provider Family where provider-bearing
→ replaceable realization
```

Applicable accepted mechanics include:

- configuration loading;
- structured diagnostics/logging;
- telemetry/health;
- temporal/freshness primitives;
- operation/correlation/provenance context;
- representation/serialization mechanics;
- network client mechanics;
- cache client mechanics;
- storage client mechanics;
- error/status/uncertainty primitives;
- governed context propagation;
- secret-reference/sensitive-data redaction;
- compatibility/conformance mechanics.

```text
Foundation != S7 Authority
Provider != S7 Authority
Storage Provider != Definition/Factual SoT
Provider Success != S7 Semantic Success
```

Deferred Foundation candidates remain deferred:

```text
Cryptographic / Evidence-verification Helpers
Database Utility Primitives
```

No mandatory missing Foundation semantic was discovered by this Batch.

---

# 33. Internal Dependency Taxonomy

Batch-1 accepted dependency taxonomy is reused unchanged:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only `SDD` participates in recursive semantic-definition cycle analysis.

Hard SDD graph:

```text
DK02 → DK01
DK03 → DK01, DK04, DK05, DK06, DK07, DK08
DK04 → DK01
DK05 → DK01, DK04
DK06 → DK01, DK04, DK05
DK07 → DK01, DK04
DK08 → DK01, DK04
DK09 → DK01, DK04, DK05, DK06, DK07, DK08
DK10 → DK01, DK04, DK05, DK06, DK07, DK08, DK09
```

```text
Hard SDD Graph
→ ACYCLIC

Unresolved Semantic-definition Cycle
→ 0

Authority Cycle
→ NONE
```

Important non-SDD relationships:

- DK01 canonicalization consumes DK03 validation evidence through `EL`, not reverse semantic-definition dependency.
- DK07 Knowledge derivation may reference DK05/DK06 evidence through `EL/HPL` without making every Knowledge Definition semantically dependent on every ETL Definition.
- DK08 Query/Aggregation may consume DK05/DK06/DK07 source/result evidence through `EL/HPL/XED` rather than hard SDD unless an exact reusable native Definition explicitly references another definition.
- Governance Context consumption is `ACD`.
- external source/schema/factual evidence is `XED`.
- historical source/definition lineage is `HPL`.

This graph is not a process graph, dataflow graph, ETL DAG, call graph, query plan or database dependency graph.

---

# 34. Stable S7 Contract Subjects

No new `RCP-*` identifiers are invented. The following unnumbered stable semantic subjects are required inside the existing architecture pressure model:

| Subject | Producer / Consumer | Required stable semantics | Authority preservation |
|---|---|---|---|
| Native S7 Definition Lifecycle | DK01/DK02/DK03 ↔ `ns_web`/SDK/cross-domain consumers | Definition identity/revision, candidate/base, validation/certification, history, compatibility | S7 semantic authority + Definition SoT remain `ns_server` |
| Factual Partition / Source Authority Binding | DK04 ↔ S7 runtime/cross-domain consumers | partition identity, final SoT binding, owner/provenance, applicability/freshness/reconciliation | factual SoT remains per declared partition |
| External Schema / Mapping | DK05 ↔ source integrations/S7 runtime | external schema reference, mapping revision, compatibility, provenance | external schema/source authority preserved |
| ETL / Derivation Definition | DK06 ↔ DK09/DK10/authoring consumers | exact definition revisions, source/output meaning, lineage, partial/unknown semantics | runtime/output does not become source authority |
| Knowledge Semantic / Representation Relationship | DK07 ↔ consumers/Agent retrieval paths | Knowledge classification, derivation lineage, projection/reference semantics | index/vector/embedding/RAG no authority transfer |
| Query / Aggregation Semantic Evidence | DK08 ↔ callers/DK09 | target partitions, provenance, completeness/freshness/uncertainty | result not automatically source/factual SoT |
| RCP-17 S7 Trial | DK10/SV-R03 ↔ applicable runtime/web/SDK | exact revision, context, data/effect boundary, result/provenance | partial closure only |
| RCP-23 S7 Runtime Evidence | DK09/SV-R03 → consumers | operation/revision/source/result/history/uncertainty | partial closure only; source owners preserved |

Concrete schema/API/transport/serialization remains downstream.

---

# 35. Compatibility / Migration / Conformance

Compatibility is judged by the semantic owner without freezing representation mechanisms.

Applicable dimensions include:

- Native S7 Definition revision compatibility;
- source↔visual semantic interoperability/conformance;
- external schema↔Mapping compatibility;
- Mapping/Transformation/ETL revision compatibility;
- factual SoT-binding applicability/history;
- Knowledge Definition/derivation compatibility;
- query/aggregation semantic result compatibility;
- SV-R03 runtime evidence consumer compatibility;
- Trial evidence compatibility.

Permanent rules:

```text
Compatible representation change != semantic revision automatically
Semantic modification → new canonical revision
Migration != historical rewrite
Provider replacement != semantic migration automatically
Current mapping/schema != historical interpretation automatically
```

A migration that changes semantics creates an explicit successor revision and lineage. Major externally observable compatibility commitments or high-migration-cost product guarantees remain MDE-governed.

---

# 36. S13 Discovery Contribution Non-preemption

S7 may provide only S7-owned resource identity/revision/provenance evidence for later S13 consumption.

A contribution may identify, where applicable:

```text
S7 Resource / Definition / Knowledge subject identity
exact revision where versioned
resource semantic classification
owning Authority / factual SoT reference where applicable
Tenant/governance applicability
projection-eligible metadata/provenance supplied by S7
```

This Candidate does **not** design:

```text
S13 internal architecture
Discovery Index
Discovery Query semantics
ranking
search UX
navigation
Discovery provider
```

```text
S13 Projection != S7 Definition SoT
S13 Projection != factual/resource SoT
```

---

# 37. Semantic Persistence Custody

Each Module may require durable semantic state/evidence custody for its own accepted responsibility:

```text
DK01 → canonical native Definition current/history/lineage
DK02 → mutable Authoring Candidate/provenance/interoperability evidence
DK03 → Validation/Certification evidence
DK04 → factual partition/SoT-binding declarations and provenance evidence
DK05 → source-schema references/Mapping definitions/compatibility history
DK06 → ETL/transformation/derivation definitions and lineage semantics
DK07 → Knowledge definitions/classification/derivation evidence
DK08 → reusable native query definitions where applicable + query/aggregation semantic evidence/history as required
DK09 → SV-R03 production semantic Operation/history
DK10 → SV-R03 Trial semantic Operation/history
```

Normative interpretation:

```text
Semantic Persistence Custody != new Project-level SoT
Persistence Placement != Authority
Database/Table/Schema != Definition SoT automatically
Storage/Cache/Index != Factual SoT automatically
Stored external evidence != source ownership transfer
```

Physical persistence technology remains downstream.

---

# 38. DAD / MDE Determination

Delegated architecture decisions produced by this Candidate are recorded separately as:

```text
CID-SV-B4-DAD-001..015
```

The DAD set covers:

1. ten-module S7 internal decomposition;
2. native Definition identity/canonical revision/SoT custody;
3. mutable dual-authoring candidate/interoperability;
4. Validation/Certification/S8 lifecycle separation;
5. factual partition/source authority binding;
6. external schema/mapping semantics;
7. ETL/transformation/derived-fact semantics;
8. Knowledge/index/vector/embedding/RAG non-collapse;
9. Query/Aggregation semantic boundary;
10. SV-R03 runtime Actual-state/result ownership;
11. S7 semantic result vs source/provider evidence;
12. RCP-17 S7-side closure;
13. RCP-23 S7/SV-R03 contribution;
14. historical/offline/recovery/compatibility semantics;
15. typed dependency/Foundation/S13 non-preemption boundary.

MDE audit result:

```text
New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

No strategic concrete factual partition is assigned; no new Authority/SoT/Actual-state owner is created; no major physical identity namespace, offline winner policy, provider/protocol/storage lock-in or new Product capability is selected.

---

# 39. Semantic Resolution Matrix

| Dimension | S7 resolution | Status |
|---|---|---|
| Identity | Definition, revision, factual partition, source, mapping, ETL, Knowledge, runtime operation, Trial and output identities remain distinct/representation-neutral | CLOSED |
| Revision | canonical semantic modification creates new revision; historical revisions immutable in meaning | CLOSED |
| Authority | S7 Semantic Authority `ns_server`; cross-domain consumption does not transfer | CLOSED |
| Native Definition SoT | `ns_server` via Owner Option A; internal custody DK01 | CLOSED |
| Factual SoT | per bounded semantic partition, exactly one final declared owner | CLOSED |
| Actual-state | DK09/DK10 own only SV-R03 S7 semantic runtime assertions | CLOSED |
| State/Lifecycle | Candidate→Validation→Canonical Revision→Certification→S8 Acceptance→S8 Admission→Runtime/Trial separated | CLOSED |
| Temporal/Freshness | exact revision/source evidence and freshness qualification | CLOSED |
| Failure/Unknown | explicit unavailable/stale/partial/conflicting/unknown/indeterminate/reconciliation states | CLOSED |
| Tenant | inherited native governance context | CLOSED |
| Organization | separate from Tenant/source grouping | CLOSED |
| Principal/IAM | S1 consumed, not redefined | CLOSED |
| Policy | S3 consumed, not redefined | CLOSED |
| Trust/Security | S4 consumed; provider/crypto success not Trust | CLOSED |
| Artifact Acceptance/Admission | S8 preserved | CLOSED |
| Configuration | S7 item meaning / S9 desired / applicable runtime applied | CLOSED |
| Secret | Reference != Material; no material custody technology | CLOSED |
| External Schema/Source | reference/provenance, not native canonicalization | CLOSED |
| Mapping/ETL/Derived Fact | exact revisions and lineage; output/source non-collapse | CLOSED |
| Knowledge | Definition/factual/derived/projection classification; index/vector/embedding/RAG non-collapse | CLOSED |
| Query/Aggregation | S7 semantic intent/result/provenance only; no universal language | CLOSED |
| Offline/Recovery | no authority transfer; reconnect != reconcile; no winner rule | CLOSED |
| Compatibility/Migration | semantic-owner classification, explicit successor/history | CLOSED |
| Foundation | accepted authority-neutral mechanics only | CLOSED |
| Cross-boundary Dependency | typed SDD/ACD/EL/HPL/XED topology, hard SDD acyclic | CLOSED |
| S13 contribution | S7 identity/revision/provenance input only; S13 internals untouched | CLOSED |
| Decision Traceability | accepted Owner/MDE + CID-SV-B4-DAD-001..015 | CLOSED |
| Revalidation Trigger | MDE boundaries explicit | CLOSED |

```text
Missing/Ambiguous Normative Dimension
→ 0

Implementation-defined Architecture Escape
→ 0
```

---

# 40. Explicit Non-goals / Named Downstream Deferrals

This Candidate deliberately does not select or design:

- S10/S11/S12/S13 internal architecture;
- other Product Component internal architecture;
- full RCP-17 or full RCP-23 closure;
- RCP-18 Notification / Delivery or RCP-21 Discovery;
- System-level SDK Detailed Design;
- Data/ETL DSL, AST, IR, canonical source representation or visual schema;
- source↔visual converter, code generator or SDK API;
- concrete external connector/API/CDC protocol;
- concrete database/warehouse/lake/search/vector/cache/storage topology;
- concrete ETL/pipeline/DAG/scheduler/worker/queue/stream processor;
- concrete query language, semantic-layer engine or BI engine;
- concrete embedding/model/RAG/search provider/framework;
- concrete DB schema/ORM/table layout;
- REST/RPC/gRPC/WebSocket/message envelope;
- provider/vendor/library selection;
- Django App/Python package/class/repository layout;
- universal sandbox, deterministic replay, no-effect Trial, exactly-once or rollback guarantee;
- material global fail-open/fail-closed or conflict-winner rule;
- Design-to-Implementation Readiness, Implementation Planning, IWP or coding.

Named downstream responsibility remains with the separately authorized Component/Contract/Foundation/Provider/SDK/implementation phases under current governance. There is no `TBD`, `implementation decides`, `framework handles this` or unnamed architecture escape.

---

# 41. Candidate Exit Gate

```text
Authorized S7 Boundary Coverage
→ 1 / 1 / 100%

Derived Internal Modules
→ 10

Unowned S7 Responsibility
→ 0

Duplicate Final Responsibility
→ 0

Hard SDD Cycle
→ 0

Authority Ambiguity
→ 0

Native Definition-SoT Ambiguity
→ 0

Factual-SoT Ambiguity
→ 0

Actual-state Ownership Ambiguity
→ 0

Source/Derived Fact Collapse
→ 0

Knowledge/Index/Vector/Embedding Collapse
→ 0

Silent Source↔Visual Semantic Loss
→ 0

RCP-17 S7 side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-17 Full Cross-domain Closure
→ NOT CLAIMED

RCP-23 S7 / SV-R03 contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-23 Full Server-native Runtime Evidence Closure
→ NOT CLAIMED / S10-SV-R06 remains required

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Item
→ NONE

Missing Foundation Semantic
→ 0

Unauthorized Downstream Design Leakage
→ 0

Implementation-defined Escape
→ 0
```

```text
NGRP-001
Component Internal Design
/ ns_server
/ Batch 4
/ S7 Enterprise Data / Knowledge / Foundational ETL

→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This is a producing-session candidate state only. It does not claim Global Acceptance, does not advance GAC Epoch, does not declare ns_server Internal Design Exhaustion or Component Internal Design global completion, does not authorize S10/S11/S12/S13 or any other Product Component, and does not authorize SDK Detailed Design, Design-to-Implementation Readiness, Implementation Planning, IWP or Coding.

```text
NEXT AFTER PRODUCING EVIDENCE COMPLETION
→ STOP
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```