# NGRP-001 — Component Internal Design / ns_server / Batch 1 — Global Acceptance

- Authority: `GLOBAL ARCHITECTURE COORDINATOR`
- Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_1 / GOVERNANCE_CORE_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Producing Entry HEAD: `9dccb5dbad14b664f052790c276be0d644b64b7e`
- Frozen Producing Final HEAD: `4457a1e69688eac4c845562437ca6712e3b54987`
- Entry Global State: `GAC-EPOCH-0043`
- Result: `GLOBAL_ACCEPT`

## 1. Independent Recovery / Delta Review

Fresh GAC recovery resolved the actual branch at the frozen producing final HEAD and reconstructed the current Repository authority from Constitution, Unified Governance, Global State, Working State, Decision Registry, relevant Ledger tail, accepted Project/Z3/Runtime/Foundation evidence, and exact Owner/MDE evidence required by the current scope.

```text
Producing Delta
→ 4 commits
→ exactly 4 new ns_server Component Internal Design / Batch 1 evidence files

Files
→ Candidate
→ DAD Evidence
→ Review/Audit Evidence
→ Handoff

Accepted upstream normative/governance file modified by producing range
→ 0

Implementation/source file modified by producing range
→ 0

Delta Classification
→ EXPECTED_PHASE_EVIDENCE

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE
```

## 2. Accepted Boundary / Module Baseline

The Batch is accepted for exactly these previously accepted `ns_server` boundaries:

```text
S1 Tenant & Principal Identity Governance
S2 Organization Semantics & External Mapping Governance
S3 Policy & Authorization Governance
S4 Platform Trust & Security Governance
S8 Artifact Acceptance & Execution Admission Governance
S9 Managed Runtime Configuration Governance
```

Accepted internal architecture Modules:

```text
G01 Tenant Canonical Governance
G02 Principal & Native IAM Governance
G03 Authentication Evidence & External Identity Binding
G04 Organization Semantic Governance
G05 Organization Mapping & Reconciliation
G06 Policy Definition & Revision Governance
G07 Authorization Decision & Policy Evidence
G08 Trust State & Relationship Governance
G09 Trust Evidence Interpretation & Revocation Evidence
G10 Governance Context Composition
G11 Artifact Identity & Formal Acceptance Governance
G12 Execution Admission Decision & Evidence Governance
G13 Managed Configuration Desired-state Governance
G14 Configuration Application Evidence & Reconciliation
```

`G01..G14` remain document-local navigation labels. Their accepted architecture identity is the responsibility name/meaning; this acceptance does not make them Django Apps, Python packages/classes, services, processes, tables, deployment units or physical namespaces.

```text
Authorized Boundary Coverage
→ 6 / 6 / 100%

Unowned Internal Responsibility
→ 0

Duplicate Final Responsibility
→ 0

God Module
→ NONE_FOUND

Overfragmentation
→ NONE_FOUND
```

## 3. Accepted Internal Dependency Semantics

The following dependency taxonomy is accepted for this Batch:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only `SDD` participates in recursive semantic-definition cycle analysis.

Accepted hard SDD graph:

```text
G02 → G01
G03 → G01, G02
G04 → G01
G05 → G04
G06 → G01
G07 → G06
G08 → G01
G09 → G08
G10 → G01, G02, G03, G04, G05, G07, G08, G09
G12 → G11
G14 → G13
```

Application-time Policy/Trust/admin relationships, evidence references and historical provenance do not become reverse semantic-definition edges.

```text
Hard SDD Graph
→ ACYCLIC

Unresolved Internal Dependency Cycle
→ 0

Authority Cycle
→ NONE
```

## 4. Authority / SoT / Actual-state Acceptance

The accepted Owner topology remains unchanged:

```text
Tenant Semantic Authority
→ ns_server

Native Tenant Canonical SoT
→ ns_server

Native IAM Semantic Authority
→ ns_server

Native Organization Semantic Authority
→ ns_server

Organization factual SoT
→ exactly one final SoT per bounded semantic partition / Organization System
→ external final SoT remains permitted

Unified Policy Semantic Authority
→ ns_server

Platform Security / Trust Semantic Authority
→ ns_server

Formal Artifact Acceptance Authority
→ ns_server

Formal Execution Admission Authority
→ ns_server

Managed Runtime Configuration Authority
→ ns_server

Managed Runtime Configuration Desired-state SoT
→ ns_server

Configuration Item Semantic Authority
→ configured capability semantic owner

Applied Runtime Configuration Actual-state
→ applicable runtime Actual-state owner
```

`G03`, `G05`, `G09`, `G10` and `G14` remain evidence/mapping/composition/reconciliation responsibilities and gain no hidden final Authority, SoT or Runtime Actual-state ownership.

```text
Authority Transfer
→ 0

SoT Transfer
→ 0

Actual-state Ownership Transfer
→ 0
```

### Persistence-custody interpretation

The producing artifacts use phrases such as `authoritative persistence responsibility`, `authoritative governance state` and `authoritative decision/evidence history` for state/evidence produced or governed by accepted semantic authorities.

For Global Acceptance these phrases are normatively interpreted as:

```text
semantic state / decision-evidence persistence custody
inside an already accepted authority boundary

!= new Project-level Source-of-Truth topology
!= storage/database placement becoming SoT
!= external factual-source authority transfer
```

In particular, the accepted Batch does **not** create a new independent Project-level IAM, Policy or Trust SoT decision. External identity/trust/Organization facts retain their bounded source ownership; Organization SoT remains governed by the accepted per-partition topology; Applied Configuration remains owned by the applicable runtime Actual-state owner.

Any later proposal that promotes an internal persistence location, database, cache, provider or one of these Modules into a new final SoT not already accepted is an MDE/revalidation matter and is not authorized by this acceptance.

## 5. Accepted Stable Contract Closure

The following current-scope pressure subjects are accepted as `CLOSED AT DESIGN-SEMANTIC LEVEL`:

```text
RCP-01 Governance Context
RCP-02 Admission Evidence
RCP-19 Desired / Applied Config
S8 Artifact Identity / Acceptance Evidence
```

### RCP-01 Governance Context

Accepted closure includes semantic identity/revision, separate Tenant/Organization/Principal/authentication/Policy/Trust constituent identities, constituent provenance/freshness/applicability, explicit missing/stale/unknown/unverified/indeterminate handling, producer/consumer obligations, bounded offline use, historical revision pinning, representation-neutral serialization obligations, compatibility/migration/conformance, disclosure minimization and Secret-Material exclusion.

Permanent rules include:

```text
Context Present != Authorized
Principal Present != Authenticated automatically
Authenticated != Policy Permit
Policy Permit != Admission
Trust Evidence Present != Trusted automatically
Tenant != Organization
```

### S8 Artifact Identity / Acceptance Evidence

Accepted closure includes candidate/artifact/revision/domain identity, certification-evidence reference, Formal Acceptance decision/evidence identity, accepted/rejected/revoked/unknown/unverified/stale applicability, provenance, historical interpretation, compatibility/migration/conformance and relationship to Admission.

```text
Definition != Certification
Certification != Formal Acceptance
Cryptographically Valid != Formal Acceptance
Signature Valid != Formal Acceptance
Registry Present / Installed / Loadable != Formal Acceptance
Accepted Artifact != Execution Admitted
```

### RCP-02 Admission Evidence

Accepted closure includes Admission Evidence identity, target Execution Intent identity, Artifact/Definition revision references where applicable, Tenant/Principal/Policy/Trust/Acceptance evidence linkage, Admission revision/decision/applicability, effective temporal semantics, optional explicit expiry, revocation/stale/unknown/indeterminate conditions, bounded replay/reuse, offline applicability, provenance, compatibility/migration/conformance and consumer obligations.

```text
Policy Permit != Admission
Accepted Artifact != Admission
Admission != Scheduling / Routing / Dispatch / Attempt / Effect
Admission Evidence Possession != Admission Authority
Admission Evidence Possession != unlimited execution authority
```

### RCP-19 Desired / Applied Config

Accepted closure includes Configuration Subject identity, configured capability semantic-owner reference, Desired/Applied revisions, Desired applicability/value semantic boundary, distribution intent/evidence, source-owned Applied evidence, partial/failure/unknown/stale/conflict semantics, reconciliation, Observed projection relationship, Secret Reference separation, temporal/provenance/history, offline behavior and compatibility/migration/conformance.

```text
Desired != Distributed
Distributed != Applied
Applied != Observed
Observed != Applied SoT
Configuration != Secret Material
```

The four contracts remain architecture-semantic and representation-neutral; no HTTP/RPC/WebSocket/JWT/JSON/Protobuf/DTO/SQL/Python interface is accepted by this Batch.

## 6. Historical / Offline / Recovery Acceptance

The accepted design preserves revision-pinned historical interpretation. Current Policy, Trust, Organization mapping, Acceptance/Admission state or Desired Config does not automatically rewrite the meaning of historical operations or evidence.

```text
Offline / Disconnected != Local Authority Transfer
Reconnect != Reconciled
Sync != Authority Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
```

No material global fail-open or fail-closed policy is created by this Batch. Bounded retained evidence may be consumed only according to already accepted applicability/freshness/revocation semantics; otherwise uncertainty remains explicit.

## 7. Security / Secret / Foundation Acceptance

The Batch preserves:

```text
Authentication != IAM Authority
IAM != Policy
Policy != Trust
Cryptographically Valid != Trusted
Connected != Trusted != Admitted
Configuration != Secret
Secret Reference != Secret Material
```

Accepted Shared Foundation consumption remains:

```text
Stable Entry
→ Foundation Contract
→ Foundation Module
→ Provider Family where provider-bearing
→ replaceable downstream realization
```

Concrete Provider/vendor/library identity is not a Product architecture dependency. Provider/storage/cache/secret-material realization does not gain Product Authority/SoT/Actual-state ownership.

Deferred `Cryptographic / Evidence-verification Helpers` and `Database Utility Primitives` remain outside the accepted Foundation baseline; this Batch does not create them.

## 8. DAD / MDE Determination

The following producing decisions are globally accepted as DADs inside the exact authorized scope:

```text
CID-SV-B1-DAD-001..013
```

Independent MDE review found no decision that materially determines or changes an Owner-reserved Authority/SoT/Actual-state topology, major physical identity namespace, material offline fail-open/fail-closed policy, major external compatibility commitment, concrete provider/protocol/framework/storage/artifact-format lock-in, high migration-cost commitment or new Product capability.

```text
Misclassified MDE Found
→ 0

New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

## 9. Non-preemption / Leakage Review

```text
Other RCP complete design leakage
→ 0

Other ns_server boundary internal-design leakage
→ 0

ns_runtime / ns_node / ns_agent / ns_web internal-design leakage
→ 0

System-level SDK Detailed Design leakage
→ 0

Concrete auth/policy/PKI/KMS/artifact/config protocol/provider selection
→ 0

Concrete database/storage/cache/broker selection
→ 0

Concrete DB schema/table/ORM design
→ 0

Concrete REST/RPC/WebSocket/wire/DTO design
→ 0

Normative Django App/package/class/file layout
→ 0

Implementation Planning / IWP / Coding leakage
→ 0

Unnamed Deferral
→ 0

Implementation-defined Semantic Escape
→ 0
```

## 10. Global Acceptance Result / Boundary

```text
NGRP-001
Component Internal Design
/ ns_server
/ Batch 1

→ GLOBAL_ACCEPTED
```

This acceptance does **not** imply or authorize:

```text
ns_server Component Internal Design → globally complete
ns_server Internal Design Exhaustion → satisfied
ns_server Batch 2 → authorized
ns_runtime Internal Design → authorized
ns_node Internal Design → authorized
ns_agent Internal Design → authorized
ns_web Internal Design → authorized
System-level SDK Detailed Design → authorized
Design-to-Implementation Readiness → authorized
Implementation Planning → authorized
IWP → authorized
Coding → authorized
```

A separate GAC remaining-pressure / batching / authorization action is required before any downstream producing session begins.

`refs/heads/temp-never-create` remains `NONAUTHORITATIVE / NON_SEMANTIC / CLEANUP_ONLY` and is not an architecture blocker.
