# NGRP-001 Z2 MDE-007 — Formal Artifact Acceptance Authority Owner Decision

- **Decision ID:** `Z2-MDE-007`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Decision-predecessor HEAD:** `040226cb0329d04d87786bccf150feb82eb5d79f`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-001..006`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final **Formal Artifact Acceptance Authority** for `ns_evermore`?

This decision concerns the authority that determines whether candidate material has become a formally **Accepted Artifact** within `ns_evermore` governance.

It does **not** by itself decide:

- domain semantic certification authority;
- artifact format or package format;
- registry, object storage, signing, digest, provenance or build technology;
- installation or activation semantics;
- Formal Execution Admission Authority;
- runtime scheduling/dispatch;
- persistence topology, API schema, wire representation, or implementation layout.

The accepted `NSE-007` separation remains controlling:

```text
Development Definition
!= Domain Semantic Certification
!= Accepted Artifact
!= Installation
!= Activation
!= Formal Execution Admission
!= Runtime Execution Attempt
```

## 2. Classification

```text
Classification
MDE

Reason
Artifact Authority is explicitly Project-Owner-reserved under Unified Governance.
NSE-007 requires later Architecture to resolve Artifact Acceptance Authority and prohibits deriving acceptance from runtime possession, file/database presence, installation, activation, loadability, executability, repository placement, registry placement, or technical capability.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` owns unified Formal Artifact Acceptance Authority

`ns_server` is the final platform authority that determines whether candidate material becomes an Accepted Artifact. Applicable Business, Automation, Agent, Data/Knowledge, extension, plugin, or other semantic domains may perform or provide domain-specific semantic certification and evidence, but certification does not itself constitute formal Artifact Acceptance.

Other Product Components may store, transport, install, activate, load, execute, inspect, administer, or observe artifact-related state only within later accepted responsibilities and do not gain Artifact Acceptance Authority through those activities.

### B — Federated domain-specific Artifact Acceptance Authorities

Each principal capability domain independently accepts artifacts for its own domain. This maximizes domain autonomy but requires federated acceptance lifecycle, cross-domain composition, revocation, provenance, historical interpretation, and final-status semantics and risks collapsing Domain Semantic Certification with Formal Artifact Acceptance.

### C — `ns_runtime` owns Formal Artifact Acceptance Authority

`ns_runtime` determines whether material is accepted for the runtime ecosystem. This aligns acceptance close to execution coordination but materially couples a pre-runtime governance decision to the Communication/Scheduling/Dispatch Hub and creates a strong risk that technical loadability/routability/executability becomes acceptance authority.

## 4. Recommendation Presented

`A — ns_server owns unified Formal Artifact Acceptance Authority`.

Rationale:

- it preserves one explicit final Artifact Acceptance Authority;
- it keeps domain semantic certification distinct from system-level Artifact Acceptance;
- it prevents `ns_runtime`, `ns_node`, `ns_agent`, `ns_web`, Shared Foundation, storage/registry placement, or runtime possession from acquiring acceptance authority;
- it remains compatible with Tenant, IAM, Policy and Security governance while not making those authorities identical;
- it preserves offline/private correctness because local possession or disconnection cannot promote material into accepted state;
- provider, registry, storage and signing mechanisms remain replaceable downstream realization concerns.

## 5. Project Owner Decision

```text
Selected Option
A

Formal Artifact Acceptance Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY consume the following Owner-decided fact:

```text
ns_server
→ owns final Formal Artifact Acceptance Authority

Applicable semantic domain
→ may own or participate in Domain Semantic Certification
→ certification does not equal Artifact Acceptance

ns_runtime
→ may transport / coordinate / schedule / dispatch accepted material later
→ does not gain Artifact Acceptance Authority

ns_node
→ may possess / install / activate / execute governed material later
→ local possession / loadability / executability does not create Artifact Acceptance

ns_agent
→ may load/invoke governed Agent/tool/model-related material later
→ does not gain Artifact Acceptance Authority by execution or provider mediation

ns_web
→ may provide human-facing artifact administration/review surfaces
→ UI action does not itself constitute Artifact Acceptance Authority

Shared Foundation
→ may provide reusable transport/storage/security/provenance capabilities later
→ mediation or provider placement does not confer Artifact Acceptance Authority
```

## 7. Explicit Non-Implications

This decision MUST NOT be interpreted as establishing any of the following automatically:

```text
Artifact Acceptance Authority = Domain Semantic Certification Authority
Artifact Acceptance Authority = Tenant Authority
Artifact Acceptance Authority = IAM Authority
Artifact Acceptance Authority = Policy Authority
Artifact Acceptance Authority = Organization Authority
Artifact Acceptance Authority = Security / Trust Authority
Artifact Acceptance Authority = Formal Execution Admission Authority
Artifact Acceptance Authority = Artifact Storage Ownership
Artifact Acceptance Authority = Registry Ownership
Artifact Acceptance Authority = Installation Authority
Artifact Acceptance Authority = Activation Authority
Accepted Artifact = Execution Admitted
Accepted Artifact = Authorized Runtime Attempt
ns_server placement = universal semantic authority
```

Each material Authority / SoT / Actual-state / Admission / Security question remains separately classified under Unified Governance.

## 8. Constraint Preservation

This decision preserves:

- `NSE-001..004` Tenant/Organization/offline governance invariants;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` authority non-transfer through composition or shared implementation;
- `NSE-007` Definition / Certification / Artifact / Installation / Activation / Admission / Runtime separation;
- `NSE-008` local execution and source-effect authority separation;
- `NSE-009` representation-independent stable contract semantics;
- `NSE-010` extension/re-delivery governance preservation;
- `NSE-012` Shared Foundation authority neutrality;
- `NSE-013` complete-system semantic integrity;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 9. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- later Artifact Governance Architecture;
- later Formal Execution Admission design;
- later Component and Runtime responsibility design;
- later extension/re-delivery and supply-chain design;

without authorizing any of those later phases.

## 10. Revalidation Trigger

Revalidation is required if the Project Owner later changes Formal Artifact Acceptance Authority away from `ns_server`, collapses Domain Semantic Certification with Artifact Acceptance, permits technical possession/loadability/executability to establish acceptance, or changes the accepted Definition/Artifact/Runtime separation.

Changes in registry, database, object storage, filesystem, package format, signing technology, digest algorithm, process, service, deployment, package, provider, framework, or runtime placement do not by themselves revalidate this decision.

## 11. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Foundation Contract/Module/Provider Design, Implementation Planning, IWP, or coding.
