# NGRP-001 Phase Z3 / Batch 2 — Unified Governed Cross-domain Resource Discovery Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **MDE Classification:** `NO`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Decision Predecessor HEAD:** `54655b45e9dad371db5814fb494c8d2f54b2711b`
- **Current Global State at Decision:** `GAC-EPOCH-0022`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

As ns_evermore gains first-class Business Application, Automation, Native Agent, Data / Knowledge / Foundational ETL, Node, Operation / Execution, Trial, Human Task, Notification, Definition Revision, Configuration, Diagnostics and Provenance capabilities, what product-level discovery model SHALL govern how End Users, Operators and Developers locate cross-domain resources?

The question is not whether an individual page may expose a search box. The material issue is whether discovery remains domain-local, becomes a unified governed cross-domain discovery capability, or expands into universal AI / semantic search over every class of platform data.

---

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

### Why Product-significant

The choice materially affects:

```text
End-user navigation
Operator investigation
Developer / Delivery productivity
Cross-domain troubleshooting
Resource discoverability
Customer secondary development
Private / offline usability
Authorization-aware information exposure
```

### Why not MDE

The decision establishes a discovery and navigation capability only. It does not move or create:

```text
Product Definition Semantic Authority
Canonical Definition SoT
Runtime Actual-state Authority
Tenant Semantic Authority
IAM / Policy Authority
Artifact Acceptance Authority
Execution Admission Authority
```

A discovery projection or index is explicitly prohibited from becoming a new global resource authority or canonical resource registry. Therefore the existing authority topology remains unchanged.

---

## 3. Options Considered

### Option A — Domain-local Discovery Only

Each product domain provides its own list / search / navigation capability. No unified cross-domain discovery guarantee exists.

Benefits:

- lowest implementation pressure;
- minimal cross-domain projection requirements;
- domain-specific navigation may evolve independently.

Costs / risks:

- users must know which module owns the object they seek;
- cross-domain troubleshooting requires manual traversal;
- Delivery and customer extensions may repeatedly build their own aggregation/search layers;
- later unification would require migration from multiple domain-specific discovery conventions.

Offline / private impact:

- lowest additional pressure.

Cross-component impact:

- minimal, but cross-component journeys remain fragmented.

### Option B — Unified Governed Cross-domain Resource Discovery

The platform exposes a unified governed discovery capability across applicable resource categories while preserving each result's real domain, type and identity.

Normative principles:

```text
Unified Discovery
→ REQUIRED

Discovery Result
→ references a governed domain resource

Discovery Result
!= Resource SoT

Discovery Index / Projection
!= Canonical Resource Registry

Search Result Freshness
!= Guaranteed Current Actual-state
```

Discovery MUST be authorization-aware and Tenant-aware:

```text
Tenant boundary
Principal context
Authorization
Privacy / redaction
→ REQUIRED
```

The platform MUST NOT reveal the existence, metadata, snippet or relationship of a resource to a principal who is not authorized to discover it.

If a discovery projection is stale, partial, rebuilding, unavailable or otherwise incomplete, the interaction model MUST preserve that uncertainty rather than silently representing the result set as complete.

Applicable discoverable categories may include, subject to later bounded design:

```text
Business Applications
Automations
Agents
Data / Knowledge / ETL Definitions
Nodes
Operations / Executions
Trials
Human Tasks
Notifications
Definition Revisions
Configuration-related resources
Diagnostics / Provenance references
```

Benefits:

- consistent platform-level discoverability;
- better cross-domain navigation and investigation;
- reduced duplication in customer / Delivery projects;
- shared discovery semantics can later be consumed by ns_web and System-level SDK / CLI surfaces;
- resource-specific authority and identity remain intact.

Costs / risks:

- later architecture must define discoverable categories, searchable metadata, identity preservation, authorization filtering, Tenant filtering, freshness, pagination, correlation and stale/partial behavior;
- implementation must avoid accidental creation of a universal resource SoT;
- projection freshness and privacy require explicit handling.

Long-term impact:

- establishes stable enterprise resource discovery capability without forcing one physical representation or one universal resource registry.

Compatibility / migration impact:

- discovery semantics and resource-type preservation become compatibility concerns;
- physical index technology and internal search representation remain replaceable.

Offline / private impact:

- core discovery capability MUST operate in fully private and offline deployments;
- public search SaaS, public embedding service, Algolia, Elastic Cloud or equivalent external service MUST NOT become core-correctness dependencies.

Cross-component impact:

- multiple bounded semantic owners may contribute discoverable projections;
- ns_web and SDK / CLI may consume discovery semantics;
- contributing or consuming discovery information does not transfer semantic or actual-state authority.

### Option C — Universal AI / Semantic Search Across Everything

The platform guarantees AI / semantic search and synthesized answering across definitions, operations, audit, logs, notifications, tasks, knowledge, diagnostics and other data classes.

Benefits:

- strongest user experience and natural-language investigation potential.

Costs / risks:

- large additional retrieval, indexing, embedding, provenance, privacy, redaction and AI-provider pressure;
- significant cross-Tenant information-leak risk;
- synthesized answers may be mistaken for authoritative diagnosis;
- security classifications of logs, business data, audit evidence and knowledge differ materially;
- prematurely commits the project to a broad AI retrieval architecture.

Long-term impact:

- materially expands ns_evermore into an enterprise AI search / operations-assistant product.

Offline / private impact:

- substantially greater burden because all semantic retrieval capability must remain private/offline-correct.

---

## 4. Recommendation Presented to Project Owner

```text
Recommendation
→ B — Unified Governed Cross-domain Resource Discovery
```

Rationale:

The platform already contains enough first-class cross-domain resources that domain-local navigation alone would create durable usability and Delivery fragmentation. A unified discovery projection provides a stable way to locate resources without creating a new semantic authority.

The recommended boundary is:

```text
Unified Discovery
→ YES

Unified Resource Authority
→ NO

Cross-domain Navigation
→ YES

Authorization-aware
→ REQUIRED

Tenant-aware
→ REQUIRED

Offline / Private
→ REQUIRED

Universal AI Semantic Search
→ NOT IMPLIED
```

---

## 5. Project Owner Selection

The Project Owner selected:

```text
B
```

### Explicit Selected Result

```text
UNIFIED_GOVERNED_CROSS_DOMAIN_RESOURCE_DISCOVERY
→ REQUIRED

Authorization-aware Discovery
→ REQUIRED

Tenant-aware Discovery
→ REQUIRED

Private / Offline-capable Core Discovery
→ REQUIRED

Domain Identity Preservation
→ REQUIRED

Discovery Projection / Index as Canonical SoT
→ PROHIBITED

Universal AI / Semantic Search Across Everything
→ NOT IMPLIED / NOT REQUIRED BY THIS DECISION
```

---

## 6. Normative Consequences

1. ns_evermore SHALL provide a product-level unified discovery capability across applicable first-class resource domains.
2. A discovery result SHALL preserve the resource's actual domain/type/identity and SHALL point back to the applicable governed resource.
3. Discovery projection/index state SHALL NOT become canonical semantic or actual-state authority.
4. Searchability SHALL respect Tenant, Principal, authorization, privacy and redaction boundaries.
5. Unauthorized resource existence SHALL NOT be leaked through results, snippets, counts, relation hints or other discovery metadata.
6. Discovery freshness and completeness uncertainty SHALL be represented explicitly when applicable; stale, partial, unavailable or rebuilding projection state SHALL NOT be silently treated as complete/current.
7. The capability SHALL remain fully viable in private and offline deployments without mandatory public search SaaS or public AI/embedding infrastructure.
8. ns_web and System-level SDK / CLI MAY expose different interaction surfaces while conforming to the same governed discovery semantics.
9. This decision does NOT require universal AI search, semantic embeddings, natural-language synthesis or a particular indexing/search engine.

---

## 7. Authority / SoT Preservation

This Owner decision does not modify any accepted authority or SoT placement.

Preserved examples include:

```text
Business Application Definition Authority / SoT
→ ns_server

Automation Definition / Workflow Authority / SoT
→ ns_server

Native AI Agent Definition / Semantic Authority / SoT
→ ns_agent

Data / Knowledge / ETL semantic authority
→ preserved under accepted bounded ownership

Runtime Actual-state
→ preserved per bounded runtime semantic partition

Tenant / IAM / Policy / Trust authorities
→ preserved

Artifact Acceptance / Execution Admission authorities
→ preserved
```

A discovery service, discovery index, search projection, ns_web page, SDK helper or future CLI is never authoritative merely because it can locate or display a resource.

---

## 8. Non-implications

This decision does NOT imply:

```text
one universal resource database
one universal resource schema
one universal physical identifier format
one universal resource registry SoT
one mandatory search engine
one mandatory index technology
one mandatory embedding model
AI semantic search
natural-language diagnosis
cross-Tenant discovery
authorization bypass
search-index canonicalization
current-state truth from stale projection
```

It also does not define page layout, ranking algorithm, relevance scoring, query syntax, API shape, schema, index lifecycle, caching, storage engine or internal component decomposition.

---

## 9. Named Deferrals

The following are explicitly deferred to later separately authorized architecture/design work:

```text
exact discoverable resource category registry
search/index internal topology
query API / contract
index update mechanism
index storage technology
ranking and filtering algorithms
pagination contract
resource metadata schema
staleness representation details
CLI / SDK command design
ns_web search page / UX details
advanced semantic search
embedding / vector indexing
AI-assisted investigation
cross-resource relationship graph design
```

These deferrals do not reopen the selected product-level requirement for unified governed cross-domain discovery.

---

## 10. Revalidation Triggers

This decision SHALL be revalidated if a later proposal would:

- make a search/discovery index authoritative;
- expose resources across Tenant or authorization boundaries;
- require a public/SaaS search dependency for core correctness;
- redefine unified discovery as universal AI semantic search;
- collapse domain-specific resource identities into one new universal authority;
- alter accepted resource semantic authorities or runtime actual-state ownership.

---

## 11. Bounded Authority / Session Limit

This evidence records only the Project Owner's Batch 2 product-capability decision.

It does NOT:

```text
claim Global Acceptance
advance GAC Epoch
authorize Z3 Batch 3
declare capability exhaustion
declare Five-component Internal Architecture readiness
enter Five-component Internal Boundary Synthesis
enter Component Internal Design
enter Runtime Responsibility Architecture
enter Shared Foundation Architecture
enter Foundation Contract / Module / Provider Design
enter Implementation Planning / IWP / Coding
```

Any such progression remains reserved to separately authorized Global Architecture governance.