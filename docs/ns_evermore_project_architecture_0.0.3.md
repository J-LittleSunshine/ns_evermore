# ns_evermore Project Architecture — Candidate Revision 0.0.3

## Authority Metadata

- **Version:** `0.0.3`
- **Status:** `CANDIDATE / COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `BOUNDED_PROJECT_ARCHITECTURE_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 2`
- **Authorized Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_2 / CROSS_CUTTING_LIFECYCLE_TRUST_RECOVERY_EVOLUTION_SEMANTICS`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `6d274d01877b9a2ee7db2301c9937324e8547d52`
- **Current GAC Epoch at Entry:** `GAC-EPOCH-0016`
- **Constraint Baseline:** `NSE-001..017 / GLOBAL_ACCEPTED / NORMATIVE`
- **Constraint Index:** `docs/ns_evermore_nse_constraints_index_0.0.5.md`
- **Accepted Upstream Project Architecture:** `docs/ns_evermore_project_architecture_0.0.2.md / GLOBAL_ACCEPTED / NORMATIVE / CURRENT`
- **Owner Decision Baseline:** `Z2-MDE-001..017 / OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED`
- **Global Acceptance:** `NOT CLAIMED`

Revision `0.0.3` is a bounded candidate evolution of accepted Project Architecture `0.0.2`. It preserves `0.0.2` as the current normative upstream baseline until independent Global Architecture Coordinator acceptance. This producing session does not supersede, delete, or demote `0.0.2`, does not advance the GAC epoch, and does not authorize any downstream architecture or implementation phase.

---

## 1. Scope and Completion Boundary

This revision closes only the Batch 2 Project Architecture pressure authorized by `GAC-EPOCH-0016`:

```text
A. Project-wide Lifecycle / Temporal / Failure Semantics
B. Security / Trust / Principal / Data-Privacy Boundary Topology
C. Recovery / Reconciliation / Offline-Degraded Responsibility Topology
D. Compatibility / Evolution / Migration / Conformance / Revalidation Topology
E. Project Architecture Semantic Resolution Matrix
```

The following accepted Batch 1 architecture remains inherited and is not reopened:

```text
Exactly five Product Components
Batch-1 Product Component responsibility skeleton
Four principal capability domains
Authority / Semantic Ownership / SoT topology
Runtime Actual-state ownership topology
Definition / Artifact / Admission / Runtime separation
Configuration authority topology
Shared Foundation Project-level position
System-level SDK / Development Surface position
Cross-component semantic dependency skeleton
Z2-MDE-001..017
```

This revision does **not** enter:

```text
Five-component Internal Architecture Boundaries
Component Internal Design
Runtime Responsibility Architecture
Runtime Role taxonomy
process / service / worker / container / deployment topology
Concrete API / Contract schema / wire protocol design
Database / storage topology
Shared Foundation Detailed Architecture
Foundation Contract / Module / Provider Design
Authentication provider / protocol selection
Policy engine implementation
PKI / KMS / HSM / TLS / certificate design
Secret-store design
Synchronization or reconciliation algorithm design
SDK binding / package / generator design
Repository/package structure design
Implementation Planning / IWP / coding
```

---

## 2. Repository Recovery and Normative Inputs

### 2.1 Recovery Gate

The bounded session recovered the actual branch before synthesis:

```text
Repository
→ J-LittleSunshine/ns_evermore

Branch
→ architecture/ns-evermore-genesis-0.0.1

State Verified Through HEAD
→ 73a5c33085eda656075611377408d5a1646bb5fa

Recovered Actual Branch HEAD
→ 6d274d01877b9a2ee7db2301c9937324e8547d52

Delta
→ 1 commit
→ docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md only
→ Batch 2 authorization / GAC-EPOCH-0016

Classification
→ EXPECTED_GOVERNANCE

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE

State / Evidence Conflict
→ NONE

Open MDE
→ 0

Blocking Item
→ NONE
```

### 2.2 Consumed Current Authority

The synthesis consumed the current Required Read Set from Global State, including:

- Genesis Constitution `0.0.1`;
- Unified Governance `0.0.2`;
- current Global Architecture State and Working State;
- Decision Registry `0.0.5`;
- Constraint Index `0.0.5`;
- accepted `NSE-001..017`;
- accepted Project Architecture `0.0.2`;
- Batch 1 Global Acceptance evidence;
- current Global Architecture Ledger tail;
- precise Owner Decision evidence for the Batch-2-dependent boundaries, including Tenant, IAM, Policy, Organization SoT, Artifact Acceptance, Execution Admission, Data/Knowledge factual SoT, Runtime Actual-state, Platform Security/Trust, Configuration, and Product Definition SoT.

No prior chat, model memory, pre-Genesis architecture, implementation artifact, provider default, database placement, or obsolete design is used as authority.

---

## 3. Preserved Accepted Project Architecture Baseline

### 3.1 Complete-system topology

The complete `ns_evermore` product semantics continue to consist of exactly:

```text
Product Components
→ ns_server
→ ns_runtime
→ ns_node
→ ns_agent
→ ns_web

Shared Foundation
→ outside the five Product Components
→ not a sixth Product Component

System-level SDK / Development Surface
→ part of complete-system capability closure
→ not a Product Component
→ not a Runtime Role
→ not an independent universal authority
```

A Product Component remains a stable product-semantic boundary and is not equivalent to a process, service, container, host, database, repository directory, package, runtime instance, or deployment unit.

### 3.2 Four principal capability domains

The following remain `FIRST_CLASS / PARALLEL / NON_SUBORDINATE`:

```text
Business Application Construction / Runtime
Automation Construction / Execution
AI Agent Runtime / Tooling
Enterprise Data / Knowledge / Foundational ETL
```

Composition, invocation, scheduling, execution, shared persistence, shared UI, Shared Foundation mediation, provider integration, and runtime co-location do not automatically transfer Semantic Authority, Source of Truth, or Actual-state Ownership.

### 3.3 Accepted Owner Decision baseline

This candidate preserves without reopening:

| Decision | Accepted Owner-decided result |
|---|---|
| `Z2-MDE-001` | Tenant Semantic Authority → `ns_server` |
| `Z2-MDE-002` | Native Tenant canonical SoT → `ns_server` |
| `Z2-MDE-003` | Native IAM Semantic Authority → `ns_server` |
| `Z2-MDE-004` | Unified Policy Semantic Authority → `ns_server` |
| `Z2-MDE-005` | Native Organization Semantic Authority → `ns_server` |
| `Z2-MDE-006` | Organization factual SoT → per bounded Organization semantic partition; exactly one final SoT for the same assertion |
| `Z2-MDE-007` | Formal Artifact Acceptance Authority → `ns_server` |
| `Z2-MDE-008` | Formal Execution Admission Authority → `ns_server` |
| `Z2-MDE-009` | Automation Definition / Workflow Semantic Authority → `ns_server` |
| `Z2-MDE-010` | AI Agent Definition / Semantic Authority → `ns_agent` |
| `Z2-MDE-011` | Business Application Definition / Platform Semantic Authority → `ns_server` |
| `Z2-MDE-012` | Enterprise Data / Knowledge / Foundational ETL Semantic Authority → `ns_server` |
| `Z2-MDE-013` | Data / Knowledge factual SoT → per bounded semantic partition; exactly one final SoT for the same assertion |
| `Z2-MDE-014` | Runtime Actual-state → per bounded runtime semantic partition; exactly one final owner for the same assertion |
| `Z2-MDE-015` | Platform Security / Trust Semantic Authority → `ns_server` |
| `Z2-MDE-016` | Split local bootstrap + centrally managed runtime desired state in `ns_server`; configuration item meaning follows capability owner; applied state follows runtime actual-state owner |
| `Z2-MDE-017` | Canonical native Product Definition SoT → Business Application `ns_server`; Automation `ns_server`; AI Agent `ns_agent` |

### 3.4 Single-final-owner invariant

For any single bounded semantic assertion, the architecture must be able to determine exactly one final authority/SoT/Actual-state owner where such an owner applies.

```text
Federation
!= multiple final authorities for the same assertion

Projection / replica / cache / index / local copy
!= alternate final authority automatically
```

Different non-overlapping semantic partitions may have different owners.

---

## 4. Batch 2 Decision Classification

The cross-cutting rules below are `DAD`-class derivations within the exact Batch 2 authorization. They consume accepted NSE and `Z2-MDE-001..017`; they do not move an accepted Authority/SoT/Actual-state owner, select a material security/privacy policy, choose an operation-specific offline fail-open/fail-closed policy, or lock the project to a protocol/provider/storage/artifact format.

```text
New Project-Owner MDE required by this synthesis
→ NONE FOUND

Owner Decision reopened
→ NONE

Unpersisted Owner Decision
→ 0
```

Any later proposal that crosses those limits remains subject to Unified Governance and defaults to MDE when classification is uncertain.

---

# Part A — Project-wide Lifecycle / Temporal / Failure Semantics

## 5. Project-wide Lifecycle Model

### Z2-DAD-027 — Lifecycle-state separation and evidence non-escalation

The Project Architecture adopts one semantic lifecycle vocabulary across capability domains without defining one universal implementation state machine.

The following distinctions are permanent:

```text
Development / Domain Definition
!= Canonical Product Definition SoT where applicable

Definition
!= Domain Semantic Certification

Certification
!= Candidate Artifact

Candidate Artifact
!= Formal Artifact Acceptance

Artifact Acceptance
!= Installation / Availability

Installation / Availability
!= Activation

Activation
!= Formal Execution Admission

Policy Permit
!= Formal Execution Admission

Formal Execution Admission
!= Scheduling / Routing / Dispatch

Scheduling / Routing / Dispatch
!= Runtime Execution Attempt

Runtime Execution Attempt
!= Successful Effect / Source Fact

Effect / Source Fact
!= Observation / Projection

Managed Desired Configuration
!= Applied Configuration Actual-state

Applied Configuration Actual-state
!= Observed Configuration Projection
```

Technical ability to load, execute, schedule, route, dispatch, store, display, cache, validate a representation, or reach a provider does not promote an object into a higher governance state.

### 5.1 Project-level lifecycle responsibility matrix

| Lifecycle state | Semantic meaning | Authority / canonical state | Actual-state responsibility | Evidence producer / observer | Does **not** gain authority |
|---|---|---|---|---|---|
| Development / Domain Definition | Mutable authoring/work-in-progress material | Meaning governed by the applicable domain Semantic Authority; working material is not canonical merely by existence | Not a runtime actual-state by default | Authorized development surfaces may produce/edit evidence | editor, UI, repository, filesystem, builder |
| Canonical Product Definition SoT | Current canonical native definition revision where `Z2-MDE-017` applies | Business App → `ns_server`; Automation → `ns_server`; AI Agent → `ns_agent` | N/A as runtime state | Applicable definition owner may emit revision/provenance evidence | cache, UI edit state, artifact registry, executor |
| Domain Semantic Certification | Domain-specific determination that a definition satisfies domain semantics | Exact certification authority remains a named downstream design question under the domain Semantic Authority; material authority changes require MDE | N/A | Later-authorized certifier may produce evidence | certification evidence does not become Artifact Acceptance |
| Candidate Artifact | Immutable-or-bounded candidate release material derived from definition/certification context | No Formal Artifact Acceptance until `ns_server` decides acceptance | Availability of a candidate copy is factual only | build/package/supply-chain process may produce candidate evidence later | builder, registry, storage, signature alone |
| Formal Artifact Acceptance | System governance decision that candidate material is an Accepted Artifact | Final authority → `ns_server`; accepted-artifact governance state derives from that decision | Local possession remains separate factual state | `ns_server` decides; other domains may supply certification/provenance evidence | domain certifier, signer, registry, storage, installer |
| Installation / Availability | Material is physically/logically present and usable by a bounded runtime responsibility | No new semantic authority; does not alter acceptance | Applicable runtime actual-state owner for the installation/availability fact, precise partition later | responsible component/runtime may produce local fact | installer, filesystem, cache, runtime possession |
| Activation | Installed material is selected/enabled for applicable runtime use | No Artifact/Admission/Policy authority transfer | Applicable runtime actual-state owner; precise partition later | responsible component/runtime may produce activation fact | activation mechanism, operator UI |
| Formal Execution Admission | Governed decision that a specific execution intent may enter execution lifecycle under applicable context | Final authority → `ns_server` | Admission decision state is governance state, not scheduling/runtime fact | `ns_server` decides; consumers may carry/verify evidence | scheduler, dispatcher, executor, local evidence holder |
| Scheduling / Routing / Dispatch | Runtime-coordination decision/action after applicable admission | No business/domain/admission authority | `ns_runtime` owns bounded coordination facts inside its accepted responsibility | `ns_runtime` may produce coordination evidence | scheduler, route, queue, transport |
| Runtime Execution Attempt | An admitted/intended execution is actually attempted | Does not retrospectively prove acceptance/admission/authorization | Per bounded runtime semantic partition under `Z2-MDE-014`; e.g. local execution facts in `ns_node`, Agent runtime facts in `ns_agent` | originating runtime responsibility produces provenance-bearing source fact | executor, local success, process placement |
| Successful Effect / Source Fact | An actual effect occurred or a source fact was observed/produced | Factual authority follows the accepted bounded source/actual-state topology; effect does not become Policy/Admission proof | Originating bounded actual-state/source-fact owner | originator produces fact; later consumers project/reconcile | central aggregator, observer, downstream consumer |
| Observation / Projection | Derived view of authoritative/source facts | Projection is not Source of Truth by aggregation | Projection responsibility owns its projection freshness/state only; source authority remains upstream | observer/projector | UI, dashboard, cache, index, System Runtime View |
| Managed Desired Configuration | Canonical governed target configuration | management authority and canonical desired-state SoT → `ns_server`; item meaning follows configured capability owner | Not applied actual-state | `ns_server` may produce desired-state revision evidence | distributor, loader, component local state |
| Applied Configuration Actual-state | What configuration a bounded runtime has actually applied | Does not overwrite desired-state SoT | Applicable runtime actual-state owner under `Z2-MDE-014` | applying runtime produces result/evidence | local success, local file, projection |
| Observed Configuration Projection | What an observer believes is applied | Derived projection only | Projector owns projection state/freshness only | observability/UI/control plane may observe | projector does not become desired/applied owner |

The exact lifecycle handlers, persistence models, artifact representations, certification mechanisms, runtime roles, and state-machine implementations are downstream concerns and cannot alter these project-level meanings.

---

## 6. Temporal and Revision Applicability

### Z2-DAD-028 — No implicit temporal winner; historical interpretation is context-bound

Project Architecture requires semantic decisions and factual interpretation to retain enough information to establish, where applicable:

```text
Identity
Revision
Provenance
Applicable Authority Context
Temporal Applicability
```

These are semantic information requirements, not a storage schema, timestamp schema, event format, or clock design.

### 6.1 Revision dimensions remain independent

At minimum, the following revisions/contexts are distinguishable:

```text
Definition Revision
Artifact Revision
Admission Evidence Applicability
Policy Context Revision
Trust Context Revision
Managed Configuration Desired Revision
Applied Configuration Revision
External Source Fact Revision / Freshness Context
Mapping Revision
Observation / Projection Freshness Context
```

A numeric or temporal ordering in one dimension does not automatically determine ordering or validity in another dimension.

### 6.2 Permanent temporal rules

```text
Latest arrival wins automatically
→ PROHIBITED

Latest local write wins automatically
→ PROHIBITED

Highest timestamp wins automatically
→ PROHIBITED

Newer projection automatically means newer source fact
→ PROHIBITED

Current Policy automatically equals historically applied Policy
→ PROHIBITED

Current Trust state automatically equals historically applicable Trust state
→ PROHIBITED

Current Definition automatically equals definition used for historical execution
→ PROHIBITED

Current Mapping automatically rewrites historical mapping interpretation
→ PROHIBITED
```

Historical execution/effect interpretation must remain relatable to the relevant Definition/Artifact/Admission/Policy/Trust/Configuration/Mapping context that was applicable to that execution or fact. If that applicable context cannot be established, the result is `UNKNOWN` or `INDETERMINATE`, not an automatic fallback to the current revision.

### 6.3 Source time versus observation time

Where a fact is observed after it originated, source-fact temporal context and observation/projection temporal context are semantically distinct.

```text
Later Observation Time
!= Later Source Fact automatically

Fresh Projection
!= Fresh Source automatically

Stale Projection
!= Stale Source automatically
```

External-source freshness, mapping freshness, runtime-fact freshness, and projection freshness remain bounded semantic concerns. Concrete clocks, timestamp precision, expiry algorithms, event storage, and freshness thresholds are explicitly deferred.

---

## 7. Failure / Unknown / Indeterminate Semantics

### Z2-DAD-029 — Uncertainty is first-class and cannot be silently collapsed

The following conditions are project-level first-class semantic states/qualifiers where applicable:

| Condition | Project-level meaning |
|---|---|
| `UNKNOWN` | The value/state cannot currently be established from admissible evidence. |
| `INDETERMINATE` | Available evidence is insufficient, ambiguous, contradictory, or context-incomplete such that a required semantic decision cannot be made. |
| `MISSING` | Expected or required evidence/state is absent; absence is not automatically a negative assertion. |
| `UNAVAILABLE` | A required capability/source/resource cannot currently provide service/evidence. |
| `UNREACHABLE` | A communication path to a source/component cannot currently be established; reachability says nothing by itself about authority or revocation. |
| `STALE` | Known evidence/state is not known to satisfy the currently applicable freshness/temporal requirement. |
| `CONFLICTING` | Multiple relevant assertions/evidence items cannot be simultaneously accepted under current semantic interpretation. |
| `UNSUPPORTED` | The capability/revision/semantic case is outside the supported contract or accepted behavior for that consumer. |
| `UNMAPPED` | A required identity/Organization/source mapping relationship has not been established. |
| `UNVERIFIED` | Evidence exists but required verification/interpretation has not been established. |
| `PARTIALLY_APPLIED` | A desired/configured/intended change has been applied only to a subset of its bounded target/result semantics. |
| `RECONCILIATION_PENDING` | Recovery/reconnect evidence is present but final reconciliation under the applicable authority has not completed. |
| `PROJECTION_STALE` | A derived view is known or suspected not to reflect the currently applicable source/actual-state context. |
| `AUTHORITY_BINDING_UNKNOWN` | The final authority/SoT/Actual-state owner applicable to the bounded assertion cannot currently be established. |

Permanent rules:

```text
Unknown != Negative automatically
Unknown != Positive automatically
Unreachable != Revoked automatically
Unreachable != Authorized automatically
Stale != Invalid automatically
Stale != Current automatically
Conflict != Latest Wins automatically
Missing != Empty-domain-value automatically
Unsupported != Best-effort coercion automatically
Unverified != Trusted automatically
Authority Binding Unknown != Local Authority automatically
```

No project-wide fail-open or fail-closed default is selected. A concrete operation-specific fail behavior that creates a material security/trust/privacy/authority commitment is `MDE`-class when reached. Non-material handling remains for the explicitly authorized downstream design authority for that domain.

---

# Part B — Security / Trust / Principal / Data-Privacy Boundary Topology

## 8. Principal Context Topology

### Z2-DAD-030 — Identity evidence, domain identity, and security principal are distinct

Project Architecture distinguishes at least the following identity/principal contexts:

| Context | Project-level semantic rule |
|---|---|
| Human Principal | A native security-principal context, where native, is governed by `ns_server` IAM semantics; a human's external identity is not automatically the native Principal. |
| Service Principal | A non-human service actor may have a native Principal context governed by `ns_server` IAM semantics; service hosting or process identity does not create authorization. |
| Node / Device Principal | A node/device may participate as a security principal under native IAM semantics; Node identity is not Tenant identity and local possession is not trust. |
| Agent Principal | An Agent may act under a security-principal context governed by native IAM semantics, while AI Agent Definition/Semantic Authority remains `ns_agent`; Agent Principal != Human Principal. |
| External Identity | Identity owned/asserted by an external bounded authority; not a native Principal until governed mapping/binding semantics establish that relationship. |
| External Authentication Assertion | Evidence produced by an external authentication boundary; evidence is not native IAM Semantic Authority and does not itself establish authorization. |
| Extension / Plugin Identity | Provenance/identity context for extension material/runtime participation; origin/loadability does not establish trust, acceptance, or authorization. |
| Provider Identity | Identity/provenance for an AI/model/technology/third-party provider; provider identity does not confer native Product Authority or platform Trust Authority. |
| Customer Re-delivery Identity Context | Lineage/provenance context for customer-modified or re-delivered product/extension material; customer ownership/source possession does not bypass governance. |

Permanent non-equivalences:

```text
External Identity != Native Principal
Authenticated != Authorized
Agent Identity != Human Identity
Node Identity != Tenant Identity
Provider Identity != Trusted Principal
Extension Origin != Trust Level
Customer Ownership != Governance Bypass
```

Concrete Principal namespace/cardinality, credentials, account schema, external identity linking mechanics, OIDC/LDAP/AD/SAML integration, and session representation remain downstream.

---

## 9. Authentication / IAM / Policy / Trust Separation

### Z2-DAD-031 — Evidence production, semantic interpretation, decision authority, and enforcement are separate roles

Project Architecture preserves the following separation:

```text
Authentication Evidence
!= Native IAM Semantic Authority

Authenticated
!= Authorized

Authorization / Policy Permit
!= Formal Artifact Acceptance

Authorization / Policy Permit
!= Formal Execution Admission

Trust Evidence
!= Platform Trusted automatically

Cryptographically Valid
!= Semantically Trusted automatically

Artifact Signed
!= Artifact Accepted automatically

Provider TLS / secure transport success
!= Provider Trusted for Product Semantics
```

### 9.1 Project-level decision boundary map

| Concern | Evidence may be produced by | Final semantic decision/authority at Project level | Enforcement/consumption |
|---|---|---|---|
| External authentication fact | Later-authorized external/native authenticator/provider | External evidence remains bounded; native IAM interpretation/binding is governed by `ns_server` IAM semantics | Consumers may use governed Principal context; protocol/provider later |
| Native Principal / IAM meaning | IAM administration, mapping, external assertions may provide inputs | Native IAM Semantic Authority → `ns_server` | Distributed consumers may carry/use context without gaining IAM Authority |
| Unified Policy meaning / permit | Policy inputs/context may be produced across domains | Unified Policy Semantic Authority → `ns_server` | Enforcement may occur at protected boundary under later design; enforcement != Policy Authority |
| Platform Trust meaning | Cryptographic/provider/local/security evidence may be produced across boundaries | Platform Security/Trust Semantic Authority → `ns_server` | Components may enforce/consume trust context; evidence producer != Trust Authority |
| Formal Artifact Acceptance | domain certification, provenance, signature/supply-chain evidence may contribute | Formal Artifact Acceptance Authority → `ns_server` | storage/install/runtime may consume acceptance state; possession != acceptance |
| Formal Execution Admission | Tenant/Principal/Policy/Trust/Artifact/runtime-intent context may contribute | Formal Execution Admission Authority → `ns_server` | `ns_runtime`/executors may consume later-designed evidence; possession != issuance authority |

The concrete authentication authority/provider topology, policy evaluation engine, enforcement-point topology, credential model, and trust mechanism remain explicitly deferred. Any material change to the accepted native IAM/Policy/Trust/Artifact/Admission authority allocation is an Owner MDE.

---

## 10. Security / Trust Boundary Topology

### Z2-DAD-032 — Boundary crossing never transfers trust or semantic authority automatically

The following are distinct trust-boundary participants:

```text
ns_server
ns_runtime
ns_node
ns_agent
ns_web
Shared Foundation
System-level SDK / Development Surface
External Identity / Authentication Systems
External Enterprise Systems
AI / Model Providers
Third-party Providers
Extensions / Plugins
Customer-private Extensions
Customer Re-delivery
Offline / Disconnected Components
```

For any crossing where the semantics are applicable, downstream design must preserve the relevant Tenant, Organization, Principal, IAM, Policy, Trust, Artifact/Admission, Data/Privacy, provenance, revision, and temporal applicability context. The crossing mechanism itself is never the authority proof.

Permanent rules:

```text
Crossing Boundary != Trust Transfer automatically
Provider Integration != Provider Trust Authority
Extension Loadability != Trust
Customer Ownership != Trust Bypass
First-party Origin != Trusted automatically
Offline Possession != Continued Trust automatically
Transport Security Success != Product-semantic Trust automatically
Shared Foundation Mediation != Trust Authority
SDK Binding != Trust Authority
```

No network segmentation, firewall topology, TLS mode, PKI hierarchy, certificate format, KMS, sandbox, or authentication protocol is selected here.

---

## 11. Data / Privacy / Trust Boundary

### Z2-DAD-033 — Data use, storage, derivation, and export do not transfer semantic ownership

Protected-data responsibility follows accepted semantic/SoT ownership plus applicable Tenant/Organization/Principal/Policy/Trust governance. Storage/caching/processing placement is not authority.

| Data class | Project-level authority/privacy rule |
|---|---|
| Tenant-scoped Data | Must preserve native Tenant scope; Tenant identity/authority cannot be inferred from storage or external customer identity. |
| Organization-scoped Data | Must preserve Tenant/Organization non-collapse and applicable Organization System/SoT binding. |
| Principal-associated Data | Native Principal semantics remain under IAM authority; external identity data does not automatically become native Principal truth. |
| Business Application Data | Definition authority/SoT and business factual SoT remain distinct; UI/runtime/storage consumption does not transfer them. |
| Automation Data | Automation Definition semantics remain `ns_server`; execution/output facts follow their own bounded factual owners. |
| Agent Context | `ns_agent` owns Agent-domain semantics, but consumed external/business/data facts retain their original authority/provenance. |
| Agent Memory-related Data | Memory capability is Agent-domain semantics; stored/remembered source material does not become Agent-owned source truth merely by memory placement. |
| Knowledge / RAG Data | RAG consumption, indexing, embedding, vectorization, retrieval, or generation does not transfer Knowledge/Data SoT. |
| External Enterprise Data | Bounded external SoT may remain authoritative; ingestion/ETL/replication/local availability does not transfer SoT. |
| Local Execution Source Facts | Originating `ns_node` bounded source/effect facts remain provenance-bearing; central observation does not erase or universalize authority. |
| Runtime Facts | Follow `Z2-MDE-014` per bounded runtime semantic partition; aggregate views are derived. |
| Audit / Evidence Data | Evidence can support decisions/accountability but storage in an audit/evidence system does not become universal business/runtime truth. |
| Configuration | Desired/applied/observed semantics follow `Z2-MDE-016`; Configuration != Secret. |
| Secret References | References identify governed secret material without becoming the material itself; ordinary configuration storage must not absorb secret material by convenience. |

Permanent rules:

```text
Data Storage Placement != Data Authority
Data Consumption != Data Ownership
RAG Consumption != Knowledge Authority
ETL / Projection != Source Authority Transfer
AI Provider Call != Permission to Export All Data
Extension Reachability != Data Access Authority
Audit Record Presence != Domain Truth automatically
```

Cross-boundary data disclosure, including AI/model/provider calls and extension access, must be governed by the applicable Tenant/Principal/Policy/Trust/Data-Privacy context and explicitly bounded to the data required by the accepted capability semantics. This is a project-level governance requirement, not a concrete data-classification label set, DLP product, encryption algorithm, or privacy-policy implementation.

Material new Security/Trust/Privacy policy commitments remain MDE-class.

---

## 12. Secret versus Configuration Boundary

### Z2-DAD-034 — Secret material remains a separately governed custody domain

Project Architecture preserves:

```text
Configuration != Secret
Secret Reference != Secret Material
Configuration Loader != Secret Authority
Shared Foundation Crypto / Secret Primitive != Platform Trust Authority
```

Project-level obligations:

1. secret material must later have an explicit custody authority/responsibility;
2. secret references must preserve sufficient identity, scope, provenance, and applicability semantics for governed consumption;
3. secret consumption must remain subject to applicable Tenant/Principal/Policy/Trust governance;
4. secret material must not be copied into ordinary configuration merely for implementation convenience;
5. Shared Foundation may later mediate reusable authority-neutral secret/crypto primitives only under accepted stable contracts;
6. provider identity/storage placement cannot become secret or Trust semantic authority automatically.

Named downstream authority:

```text
Five-component Internal Architecture Boundaries
→ allocate component-level custody/consumption responsibility where needed

Shared Foundation Architecture / Foundation Contract Design
→ define authority-neutral reusable secret/crypto semantics if admitted

Provider Design
→ select concrete provider only after stable semantics

Project Owner / MDE
→ any material Trust/Privacy/security policy or high-lock-in custody commitment
```

This revision does not select Vault, KMS, HSM, secret store, key hierarchy, credential format, rotation algorithm, or secret-reference wire schema.

---

# Part C — Recovery / Reconciliation / Offline-Degraded Responsibility Topology

## 13. Project-wide Recovery and Reconciliation Model

### Z2-DAD-035 — Recovery preserves authority and performs evidence handoff, not canonicalization by availability

Every recovery/reconciliation boundary must preserve enough semantic information to determine, where applicable:

```text
Fact Origin
Current Authority / Owner
Provenance
Revision / Temporal Context
Conflict State
Reconciliation Pending State
Evidence Handoff Responsibility
Final Decision Authority / SoT / Actual-state Owner
Resulting Projection Responsibility
```

These are semantic obligations, not a synchronization message schema or reconciliation algorithm.

### 13.1 Reconciliation responsibility matrix

| Recovery/reconciliation pair | Origin / final authority invariant | Handoff responsibility | Final decision / resulting projection rule |
|---|---|---|---|
| External bounded SoT ↔ local replica | Bounded external SoT remains final where assigned; replica does not acquire authority by availability | Native integration/domain responsibility preserves source identity/revision/provenance | Final SoT follows accepted bounded partition; local/central projection remains derived |
| Organization source ↔ native mapping/projection | Native Organization semantics → `ns_server`; factual SoT → per bounded Organization partition | `ns_server`-owned Organization semantics govern mapping interpretation; source supplies bounded facts | same assertion has exactly one final SoT; unresolved mapping/conflict remains explicit |
| Data/Knowledge source ↔ ETL/derived/projection | Source facts keep source authority; derived facts have distinct derivation identity | `ns_server` Data/Knowledge/ETL semantics preserve transformation provenance | ETL/index/cache/vector/projection does not become upstream source; derived SoT must be explicit if material |
| `ns_node` local source/effect fact ↔ central observation | bounded local execution/effect fact originates under `ns_node` actual-state responsibility | `ns_node` preserves provenance and hands off reconciliation evidence | central/system projection is derived; broader domain canonicalization follows applicable authority, not central arrival |
| `ns_agent` runtime fact ↔ system projection | bounded Agent-runtime fact originates under `ns_agent` responsibility | `ns_agent` preserves fact/revision/context evidence | projection does not transfer Agent or consumed-domain authority |
| `ns_runtime` coordination fact ↔ System Runtime View | bounded coordination fact owned by `ns_runtime` | `ns_runtime` exposes/forwards evidence later under stable semantics | System Runtime View remains derived, not universal runtime SoT |
| Managed Desired Configuration ↔ Applied Configuration | desired SoT → `ns_server`; applied fact → applicable runtime actual-state owner | manager distributes desired context; runtime returns application evidence later | partial/failed/unknown application does not overwrite desired; observed view remains projection |
| Artifact Acceptance Evidence ↔ local artifact possession | acceptance decision → `ns_server`; local possession is factual | accepted evidence may be carried/verified later; local runtime reports possession/install state | possession/replay/successful load does not create or retroactively prove acceptance |
| Execution Admission Evidence ↔ local/offline execution | Admission Authority → `ns_server`; execution fact → bounded executor actual-state owner | later-designed evidence can be carried to disconnected consumer; executor preserves use/effect provenance | local possession/exercise does not create Admission Authority; replay does not retroactively authorize |
| Tenant/IAM/Policy/Trust context ↔ offline/local consumption | native authorities remain `ns_server` under accepted decisions | later-designed governed evidence may be cached/pre-issued/locally verifiable | disconnection does not transfer authority; stale/unknown/conflicting evidence stays explicit |
| Extension / Re-delivery state ↔ accepted governance state | origin/lineage does not create Trust/Acceptance/Admission | extension/re-delivery boundary preserves provenance, revision and applicable governance evidence | reconnect/re-delivery does not erase Tenant/Policy/Trust/Artifact/Admission obligations |

Permanent prohibitions:

```text
Reconnect → Authority Transfer
Reconciliation → Authority Transfer
Recovery → SoT Transfer
Local Availability → Canonicalization
Central Availability → Canonicalization
Replay → Retroactive Authorization
Successful Sync → Proof of Original Authority
Local Copy During Offline → External SoT Replacement
Central Projection → Source Fact Authority
```

No `latest-write-wins`, `central-wins`, `local-wins`, universal `source-wins`, vector clock, CRDT, event sourcing, or specific reconciliation engine is selected.

---

## 14. Offline / Degraded Governance Topology

### Z2-DAD-036 — Offline continuity is governed evidence consumption, never governance bypass

Permanent rules:

```text
Offline != No Tenant
Offline != No IAM
Offline != No Policy
Offline != No Trust
Offline != Artifact Accepted
Offline != Execution Admitted
Offline != Local Authority Escalation
Offline != Local SoT Transfer

Central Authority != Synchronous Online Dependency For Every Action
```

Project Architecture explicitly permits later-authorized, bounded cached/pre-issued/locally-verifiable governed evidence to support offline/degraded execution and governance consumption. This permission does **not** select a grant token, admission token, certificate, lease, offline credential, policy bundle, artifact manifest, or other concrete mechanism.

Any such later evidence mechanism must preserve enough semantics to determine its issuing/controlling authority, applicable identity/revision/scope, Tenant/Principal/Policy/Trust/Artifact/Admission context where relevant, temporal applicability, provenance, and the bounded action/capability to which it applies. This is an information-applicability requirement, not a wire-schema definition.

If the applicable evidence cannot establish the required state, the condition remains `UNKNOWN`, `INDETERMINATE`, `STALE`, `UNVERIFIED`, `UNAVAILABLE`, or another explicit state as appropriate. Project Architecture does not convert that condition automatically into allow or deny.

Concrete operation-specific offline fail-open/fail-closed behavior:

```text
if material to Security / Trust / Privacy / Authority / product semantics
→ Project Owner / MDE

otherwise
→ applicable named downstream architecture/design authority inside its authorization
```

---

# Part D — Compatibility / Evolution / Migration / Conformance / Revalidation

## 15. Compatibility and Evolution Classification

### Z2-DAD-037 — Semantic compatibility precedes representation compatibility

The project uses the following primary change classes. A change receives the highest-governance class that applies; a migration obligation may additionally exist beneath that class.

| Primary class | Meaning | Minimum governance consequence |
|---|---|---|
| `CONFORMANCE_ONLY_IMPLEMENTATION_CHANGE` | Implementation/provider/package/layout changes with no accepted semantic effect | No Project Architecture revalidation; prove conformance |
| `COMPATIBLE_EVOLUTION` | Accepted semantics evolve without changing existing identity/authority/state meaning/invariants for supported consumers | Explicit semantic compatibility evidence; downstream version/support handling |
| `EXPLICIT_MIGRATION_REQUIRED` | State/definition/artifact/configuration/representation must transition under explicit interpretation, while no higher-class semantic authority change is introduced | Named migration plan/design and verification before transition |
| `ARCHITECTURE_REVALIDATION_REQUIRED` | Change alters an accepted Project Architecture semantic boundary/invariant or stable contract meaning | Return to GAC for classification/revalidation before downstream reliance |
| `OWNER_MDE_REQUIRED` | Change is Owner-reserved: major Authority/SoT/Actual-state, principal identity, Trust/Privacy/Security policy, offline fail policy, stable compatibility/historical interpretation, major lifecycle authority, high-lock-in protocol/storage/artifact/provider commitment, etc. | Stop affected work; Project Owner decision plus GAC revalidation/continuity as applicable |

### 15.1 Semantic compatibility predicate

Compatibility must be evaluated at the semantic level before representation readability/interoperability. Relevant dimensions include, where applicable:

```text
Identity
Revision
Authority
Semantic Ownership
State Meaning
Failure / Unknown / Unsupported Meaning
Tenant Scope
Organization Semantics
Principal Semantics
Policy / Authorization Semantics
Trust Assumptions
Temporal Applicability
Source-of-Truth Meaning
Actual-state Meaning
Historical Interpretation
Migration Interpretation
```

Permanent rules:

```text
Version Bump != Compatible automatically
Schema Readable != Semantically Compatible
Provider Replacement != Architecture Change automatically
Implementation Refactor != Architecture Change automatically
Database Migration != Semantic Migration automatically
No Compile Error != Compatible
Transport Compatibility != Semantic Compatibility automatically
```

Unsupported, unknown, ambiguous, or incompatible semantic revisions must remain explicit; implementations may not silently coerce them to the nearest/current shape.

### 15.2 Provider and representation evolution

A provider, framework, transport, database, SDK binding, or serialization representation may be replaced without Project Architecture revalidation **only** when accepted semantic identity, authority, failure meaning, temporal applicability, compatibility obligations, offline correctness, and contract semantics remain preserved. If replacement requires semantic change, the change is classified by this section rather than hidden inside implementation substitution.

---

## 16. Migration Classes and Obligations

### Z2-DAD-038 — Copying state is not semantic migration completion

| Migration class | Project-level obligations | Escalation trigger |
|---|---|---|
| Data Migration | Preserve bounded SoT, source identity, provenance, derivation distinction, Tenant/Organization scope, and historical interpretation; copied data is not automatically canonical | Authority/SoT reassignment or material privacy/trust change → MDE/revalidation |
| Definition Migration | Preserve domain Semantic Authority, canonical Definition SoT, definition identity/revision lineage, and historical execution interpretation | Definition Authority/SoT/stable identity change → MDE/revalidation |
| Artifact Migration | Preserve Definition/Certification/Artifact distinction, Artifact Acceptance provenance, compatibility, and applicable Admission relationship | New acceptance semantics/authority, stable artifact-format lock-in, or historical reinterpretation → MDE as applicable |
| Configuration Migration | Preserve bootstrap vs managed desired vs applied vs observed states and configured-capability semantic authority | Change to `Z2-MDE-016` topology → MDE/revalidation |
| Authority / SoT Topology Migration | Explicitly define old/new authority applicability and cutover semantics without leaving multiple final authorities for same assertion | Always material → Owner MDE + architecture revalidation |
| Identity Mapping Migration | Preserve old/new identity/mapping lineage and historical mapping interpretation; unmapped/conflicting states explicit | Material Principal/stable identity commitment or authority relationship change → Owner MDE |
| Runtime Actual-state Transition | Preserve bounded actual-state ownership and source/effect provenance through implementation/runtime transition | Change actual-state ownership partition or one-final-owner rule → Owner MDE/revalidation |
| Provider / Implementation Migration | Preserve stable semantics, failure meaning, conformance, offline/private correctness, and authority neutrality | Semantic contract change/high lock-in → revalidation/MDE as applicable |

Permanent rules:

```text
Data Copied != Migration Complete
Schema Upgraded != Semantic Migration Complete
Provider Swapped != Contract Migration Complete
Artifact Repacked != Artifact Governance Migrated
Configuration File Converted != Desired/Applied Semantics Migrated
```

A migration may temporarily involve old/new physical representations, but semantic applicability must remain unambiguous; physical coexistence cannot create two final authorities for the same assertion.

---

## 17. Project Conformance Topology

### Z2-DAD-039 — Every downstream architecture/design layer must prove conformance to accepted upstream semantics

Accepted Project Architecture requires downstream conformance evidence. The following named authorities have these future obligations when GAC explicitly authorizes them:

| Named downstream authority | Minimum Project Architecture conformance obligation |
|---|---|
| Five-component Internal Architecture Boundaries | Prove internal boundaries do not move accepted Product Component responsibilities, Authority/SoT, lifecycle, trust, data, offline, compatibility or recovery semantics |
| Runtime Responsibility Architecture | Define precise runtime actual-state partitions, freshness/observation/recovery handoffs and runtime roles without changing `Z2-MDE-014` or making coordination/projection universal authority |
| Shared Foundation Architecture | Preserve non-component status, authority neutrality, stable reusable semantics and provider replaceability |
| Foundation Contract Design | Define stable language-neutral semantics before representation; make failure/unknown/version compatibility explicit |
| Foundation Module Design | Realize accepted Foundation contracts without inventing product-domain authority |
| Provider Design | Prove concrete providers conform to stable semantics and do not acquire Authority/SoT by placement |
| Component Internal Design | Realize component responsibility without inventing missing Project Architecture or crossing accepted trust/SoT/lifecycle boundaries |
| Design-to-Implementation Readiness | Verify accepted design is implementation-derivable and all architecture-critical dimensions are resolved or legally delegated |
| Implementation Planning | Consume accepted design only; has no Architecture Authority and must return discovered design gaps upstream |

Conformance is semantic, not implementation identity. Passing compilation/tests, using a reference SDK, matching a schema, or using the same provider does not by itself prove architecture conformance.

This revision does not select conformance tools or test frameworks.

---

## 18. Project Architecture Revalidation Triggers

### Z2-DAD-040 — Material downstream change returns to the correct decision authority

| Proposed change | Required authority/action |
|---|---|
| Change exactly-five Product Component topology | Project Owner / constitutional revalidation + GAC |
| Move accepted Authority / Semantic Owner / SoT / Actual-state owner | Project Owner MDE + architecture revalidation |
| Change four first-class capability-domain non-subordination relationship | Project Owner MDE + material architecture revalidation |
| Change Tenant or Tenant/Organization non-collapse semantics | Project Owner MDE / constitutional revalidation + GAC |
| Change native Principal/IAM authority relationship materially | Project Owner MDE + architecture revalidation |
| Change material Security / Trust / Privacy policy | Project Owner MDE + architecture revalidation |
| Change operation-specific offline fail-open/fail-closed policy materially | Project Owner MDE |
| Change Definition/Artifact/Admission/Runtime separation | Project Owner MDE + architecture revalidation |
| Change stable cross-boundary contract semantics | Compatibility assessment + GAC revalidation; Owner MDE if major externally visible/historical/lock-in commitment |
| Change bounded external SoT preservation or one-final-owner rule | Project Owner MDE + architecture revalidation |
| Change offline/private core-correctness baseline | Project Owner-level revalidation + GAC |
| Replace provider while stable semantics and authority remain preserved | Conformance-only or compatible evolution; Project Architecture revalidation not required solely by replacement |
| Change internal package/directory layout with no semantic effect | No Project Architecture revalidation; conformance still required |
| Change database/storage/transport technology with no accepted semantic effect | No Project Architecture revalidation solely for technology change |

Classification authority remains:

```text
GAC
→ classification / escalation / independent acceptance / revalidation continuity

Project Owner
→ MDE / root decisions

Authorized Architecture / Design Session
→ DAD only inside exact authorized scope

Implementation / Codex
→ no Architecture Authority
```

---

# Part E — Project Architecture Semantic Resolution Matrix

## 19. Semantic Resolution Matrix Interpretation

### Z2-DAD-041 — Project-level semantic closure is distinct from downstream mechanism design

The matrix status applies to the **Project Architecture-level semantic dimension**. A dimension can be `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` while concrete schema, protocol, module, runtime role, algorithm, provider, or internal boundary remains explicitly delegated to a named later authority. Such a delegation is not an unresolved Project Architecture gap because the governing semantics and the legal decision authority are already explicit.

No dimension below uses `TODO`, implementation-default, provider-default, framework-default, or unnamed “later” language.

## 20. Mandatory Project Architecture Semantic Resolution Matrix

| Semantic Dimension | Status | Project Architecture resolution | Named downstream continuation / revalidation authority |
|---|---|---|---|
| Identity / Namespace | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Product Component/domain/principal/source identities remain distinct; external identity != native identity automatically; identity/revision/provenance must remain traceable | Five-component Internal Architecture Boundaries / Component Internal Design for concrete identifiers; Project Owner/MDE for material stable identity commitment |
| Revision / Evolution | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Definition/artifact/admission/policy/trust/config/source/mapping/projection revisions are distinct; no universal latest-wins | Applicable Contract/Component design; material compatibility commitment → MDE as applicable |
| Authority | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | `Z2-MDE-001..017` preserved; no placement/evidence/execution-based authority transfer | GAC classification; Project Owner/MDE for any material reassignment |
| Semantic Ownership | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Four principal domains remain non-subordinate; capability semantic ownership survives composition/mediation | Five-component Internal Architecture Boundaries must conform |
| Source of Truth | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Native Tenant/Definition SoTs and bounded Organization/Data federation established; one final SoT per same assertion | Component/Internal integration design defines concrete partitions; changes → MDE |
| Actual-state Ownership | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Per bounded runtime semantic partition, exactly one final Actual-state Owner; system views are projections | Runtime Responsibility Architecture defines precise partitions/freshness without changing topology |
| State / Lifecycle | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Definition/Certification/Artifact/Install/Activate/Admission/Schedule/Attempt/Effect/Projection and config states remain distinct | Five-component Internal Architecture Boundaries / Component Internal Design for concrete lifecycle handlers |
| Temporal Semantics | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | identity+revision+provenance+authority-context+temporal-applicability required; historical context not replaced by current state | Runtime Responsibility Architecture / applicable Contract Design for clock/freshness representation |
| Failure / Unknown / Indeterminate | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Unknown, indeterminate, missing, unavailable, unreachable, stale, conflicting, unsupported, unmapped, unverified, partially applied, reconciliation pending, projection stale, authority binding unknown are explicit | Applicable downstream design defines operation handling; material fail policy → Project Owner/MDE |
| Tenant | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Native Tenant authority/SoT in `ns_server`; Tenant remains explicit offline and distinct from Organization | Five-component Internal Architecture Boundaries / Component Internal Design must preserve |
| Organization | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Native Organization semantics `ns_server`; factual SoT per bounded Organization partition; mappings do not imply equality | Component Internal Design for concrete Organization/mapping mechanics; ownership change → MDE |
| Principal | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Human/service/node/agent/native/external/extension/provider/re-delivery contexts distinguished; no identity collapse | Five-component Internal Architecture Boundaries / Component Internal Design for concrete Principal model; material identity decision → MDE |
| Authentication | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Authentication evidence != native IAM authority; external assertions are evidence until governed native interpretation/binding | Five-component Internal Architecture Boundaries / Component Internal Design for provider/protocol; material authority/trust change → MDE |
| Authorization / Policy | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Policy Authority `ns_server`; authenticated != authorized; Policy Permit != Artifact Acceptance/Admission; enforcement != authority | Five-component Internal Architecture Boundaries / Component Internal Design for evaluation/enforcement topology; material policy → MDE |
| Security | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Platform Trust Authority `ns_server`; crypto/transport/provider/local success are evidence, not trust authority | Five-component Internal Architecture Boundaries / Shared Foundation Architecture / Provider Design; material security policy → MDE |
| Data / Privacy / Trust | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | storage/consumption/ETL/RAG/provider calls/extensions do not transfer data authority; governed cross-boundary disclosure required | Component Internal Design / Shared Foundation Architecture for mechanics; material privacy/trust policy → MDE |
| Serialization / Representation | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | semantic identity/compatibility precedes representation; representation cannot define authority/state meaning | Applicable later Contract Design; Foundation Contract Design for Foundation; no implementation-defined contract |
| Offline / Degraded | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | governance preserved without synchronous central dependency for every action; bounded governed evidence allowed later; no local authority escalation | Runtime Responsibility Architecture / Component Internal Design for mechanisms; material fail-open/fail-closed → MDE |
| Recovery / Reconciliation | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | provenance-preserving evidence handoff; recovery/reconnect/sync never transfer authority; reconciliation pending/conflict explicit | Runtime Responsibility Architecture / Component Internal Design for algorithms |
| Compatibility | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | semantic compatibility before representation; five governance change classes established; unsupported/unknown explicit | Applicable Contract/Component design proves compatibility; major commitment → GAC/MDE |
| Migration | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Data/Definition/Artifact/Configuration/Authority-SoT/Identity/Runtime/Provider migration classes and obligations established | Component Internal Design / Provider Design / Design-to-Implementation Readiness for mechanics; topology migration → MDE |
| Conformance | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | downstream architecture/design/provider/planning must prove conformance and cannot invent architecture | Named downstream authorities in §17; GAC/Design-to-Implementation Readiness gates |
| Cross-boundary Dependency | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | dependency, invocation, transport, provider and Shared Foundation mediation do not transfer authority; applicable context/provenance preserved | Five-component Internal Architecture Boundaries / applicable Contract Design |
| Invariant | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | NSE-001..017 and accepted `0.0.2`/MDE invariants explicitly preserved across lifecycle/trust/recovery/evolution | All downstream authorities must demonstrate preservation |
| Decision Traceability | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | Batch 2 DADs derive only from Repository current authority; MDE baseline is explicit; no Owner decision invented | Repository-backed continuity + GAC independent acceptance |
| Revalidation Trigger | `CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL` | material trigger classes and responsible authority established in §18 | GAC classifies; Project Owner decides MDE; bounded sessions act only when authorized |

Matrix result:

```text
CLOSED_AT_PROJECT_ARCHITECTURE_LEVEL
→ 26 / 26

DEFERRED_TO_NAMED_LATER_AUTHORITY as unresolved Project-level dimension
→ 0

NOT_APPLICABLE_WITH_RATIONALE
→ 0

MDE_REQUIRED currently open
→ 0

Unnamed Deferral
→ 0

Implementation-defined Escape
→ 0
```

---

## 21. Explicit Named Downstream Deferrals

The following concrete questions are intentionally not designed by Batch 2. Their semantic boundaries are closed above; their mechanisms belong to named later authorities and require explicit GAC authorization before work begins.

| Deferred concrete question | Named later authority |
|---|---|
| Precise runtime semantic-partition taxonomy, runtime freshness/observation/recovery mechanics | `Runtime Responsibility Architecture` |
| Runtime Roles, processes, services, workers, schedulers, dispatch workers, connection workers, heartbeats | `Runtime Responsibility Architecture` |
| Component-internal lifecycle handlers, enforcement boundaries, internal capability decomposition | `Five-component Internal Architecture Boundaries` → `Component Internal Design` |
| Domain Semantic Certification authority/mechanism where still required | `Five-component Internal Architecture Boundaries`; material authority choice → `Project Owner / MDE` |
| IAM factual SoT/federation detail, Principal schema, credentials, authentication provider/protocol, session identity representation | `Five-component Internal Architecture Boundaries` → `Component Internal Design`; material identity/trust decision → `Project Owner / MDE` |
| Policy evaluation engine/topology and concrete enforcement points | `Five-component Internal Architecture Boundaries` → `Component Internal Design`; material Policy commitment → `Project Owner / MDE` |
| PKI/KMS/HSM/TLS/certificate/trust-store/network-security implementation | `Five-component Internal Architecture Boundaries`; reusable primitives, if admitted → `Shared Foundation Architecture` / `Foundation Contract Design`; concrete provider → `Provider Design`; material Trust/lock-in → `Project Owner / MDE` |
| Secret material custody details, secret-reference contract/schema, secret provider/rotation | `Five-component Internal Architecture Boundaries`; reusable semantics, if admitted → `Shared Foundation Architecture` / `Foundation Contract Design`; provider → `Provider Design`; material Trust/Privacy commitment → `Project Owner / MDE` |
| Artifact package/signature/registry/storage representation | `Five-component Internal Architecture Boundaries` and later applicable Contract/Component design; provider realization → `Provider Design`; major stable format lock-in → `Project Owner / MDE` |
| Execution Admission evidence/token/grant representation | `Five-component Internal Architecture Boundaries` + `Runtime Responsibility Architecture` and later applicable Contract Design; material stable/offline commitment → `Project Owner / MDE` |
| Operation-specific offline fail-open/fail-closed behavior | Applicable later architecture/design authority; **material** behavior → `Project Owner / MDE` |
| Offline credential/grant/bundle/lease/certificate/token mechanism | `Five-component Internal Architecture Boundaries` + `Runtime Responsibility Architecture` / applicable Contract Design; material trust/identity commitment → `Project Owner / MDE` |
| Configuration file format, revision representation, push/pull/watch/distribution protocol | `Five-component Internal Architecture Boundaries` + `Runtime Responsibility Architecture`; reusable loader semantics → `Shared Foundation Architecture` / `Foundation Contract Design`; provider → `Provider Design` |
| Organization mapping/synchronization algorithms and concrete external-system mappings | `Component Internal Design`; material SoT/identity relationship change → `Project Owner / MDE` |
| Data/Knowledge synchronization/ETL/reconciliation algorithms and concrete partition inventory | `Component Internal Design`; material SoT change → `Project Owner / MDE` |
| Reconciliation conflict-resolution algorithm, clocks, vector clocks/CRDT/event-store choices if ever proposed | `Runtime Responsibility Architecture` / `Component Internal Design`; material winner/lock-in policy → `Project Owner / MDE` |
| Stable contract concrete wire/schema/REST/RPC/gRPC/WebSocket representation | applicable later Contract Design; Foundation boundaries → `Foundation Contract Design`; major stable protocol commitment → `Project Owner / MDE` |
| Shared Foundation capability inventory, contracts, modules, providers | `Shared Foundation Architecture` → `Foundation Contract Design` → `Foundation Module Design` → `Provider Design` |
| SDK language bindings, package layout, generators and distribution mechanics | semantic ownership first in `Five-component Internal Architecture Boundaries`; implementation readiness via `Design-to-Implementation Readiness`; no Architecture Authority in Implementation Planning |
| Database/storage/cache topology and concrete technology | `Component Internal Design` / `Shared Foundation Architecture` as applicable → `Provider Design`; material storage-format/lock-in commitment → `Project Owner / MDE` |
| Concrete migration tooling, execution sequencing, rollback tooling | `Component Internal Design` / `Provider Design` → `Design-to-Implementation Readiness`; any semantic authority change returns upstream |
| Concrete conformance-test tooling | applicable downstream design → `Design-to-Implementation Readiness`; tools do not define semantics |

No item in this table is delegated to “implementation decides”.

---

## 22. Constraint Traceability

| Constraint | Preservation in Candidate 0.0.3 |
|---|---|
| `NSE-001` | Tenant remains native, explicit, governed through offline/degraded/recovery conditions |
| `NSE-002` | Tenant and Organization remain non-collapsed across Principal/Data/Recovery semantics |
| `NSE-003` | Organization plurality, mappings, temporal/history and bounded SoT federation preserved |
| `NSE-004` | Offline/private lifecycle correctness preserved without governance bypass or mandatory synchronous central dependency for every action |
| `NSE-005` | Product Component semantic identity remains independent of runtime/process/deployment topology |
| `NSE-006` | Four first-class domains remain non-subordinate; composition/mediation does not transfer authority |
| `NSE-007` | Definition/Certification/Artifact/Install/Activate/Admission/Attempt states remain distinct |
| `NSE-008` | Local execution/source-effect facts remain accountable without local authority escalation; reconciliation preserves evidence |
| `NSE-009` | Stable cross-boundary semantics remain language/representation independent; semantic compatibility precedes representation |
| `NSE-010` | Extension/customer re-delivery origin/loadability/ownership never creates Trust/Acceptance/Admission/Authority bypass |
| `NSE-011` | External bounded SoT, mapping, freshness, provenance, stale/conflict/unmapped conditions preserved through recovery/migration |
| `NSE-012` | Shared Foundation remains authority-neutral/provider-neutral; provider replacement cannot silently redefine semantics |
| `NSE-013` | Complete-system semantic identity is unaffected by lifecycle/provider/migration implementation choices |
| `NSE-014` | Commercial/distribution state remains outside core Authority/Trust correctness unless explicitly accepted later |
| `NSE-015` | Technology/provider changes are classified by semantic effect; dependency/provider placement cannot define architecture |
| `NSE-016` | Recovery used actual Git HEAD/current Repository authority; candidate remains non-accepted until independent GAC review |
| `NSE-017` | All project-level dimensions are closed or explicitly assigned to named later authorities; implementation cannot invent missing architecture |

---

## 23. Batch 2 Completion State

Within the bounded Batch 2 authorization:

```text
Repository Recovery
→ PASS

Accepted Project Architecture 0.0.2
→ PRESERVED AS UPSTREAM / CURRENT NORMATIVE BASELINE

Accepted Z2-MDE-001..017
→ PRESERVED / NOT REOPENED

Lifecycle / Temporal Semantics
→ PROJECT-LEVEL CLOSED

Failure / Unknown / Indeterminate
→ PROJECT-LEVEL CLOSED

Principal / Authentication / Authorization Relationship
→ PROJECT-LEVEL CLOSED

Security / Trust Boundary
→ PROJECT-LEVEL CLOSED

Data / Privacy Boundary
→ PROJECT-LEVEL CLOSED

Secret vs Configuration Boundary
→ PROJECT-LEVEL CLOSED

Recovery / Reconciliation Responsibility
→ PROJECT-LEVEL CLOSED

Offline / Degraded Responsibility
→ PROJECT-LEVEL CLOSED

Compatibility / Evolution
→ PROJECT-LEVEL CLOSED

Migration / Conformance / Revalidation
→ PROJECT-LEVEL CLOSED

Semantic Resolution Matrix
→ COMPLETE / 26 OF 26 PROJECT-LEVEL DIMENSIONS CLOSED

Unnamed Deferral
→ 0

Implementation-defined Escape
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Unclassified Material Decision
→ 0

Multiple-final-authority Ambiguity Introduced
→ 0

Source-of-Truth Ambiguity Introduced
→ 0

Actual-state Ownership Ambiguity Introduced
→ 0

Tenant / Organization Collapse
→ 0

Product Component / Runtime Conflation
→ 0

Scope Leakage into downstream detailed design
→ 0
```

Candidate status:

```text
NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 2
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This bounded candidate does **not** declare `PROJECT ARCHITECTURE GLOBAL COMPLETE`. A separate GAC independent acceptance and `PROJECT_ARCHITECTURE_REMAINING_PRESSURE_ASSESSMENT` are required. It does not authorize Five-component Internal Architecture Boundaries or any other later phase.
