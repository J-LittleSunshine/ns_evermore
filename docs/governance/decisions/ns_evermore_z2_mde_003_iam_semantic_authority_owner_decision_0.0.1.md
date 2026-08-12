# NGRP-001 Z2 MDE-003 — IAM Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-003`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Decision Predecessor HEAD:** `993bc809bf53aba17433993cd2e970e5e1e51066`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-001`; `Z2-MDE-002`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final native `ns_evermore` **IAM Semantic Authority**?

This decision concerns the final semantic authority for the platform-native IAM domain, including the meaning and governance of native Principal identity and IAM lifecycle semantics.

It does **not** by itself decide authentication provider, credential format, federation protocol, LDAP/AD/OIDC integration, Principal persistence, IAM database topology, IAM Source of Truth, IAM Actual-state Ownership, Policy Authority, Organization Authority, Tenant Authority, external-directory Source of Truth, or runtime/deployment placement.

## 2. Classification

```text
Classification
MDE

Reason
IAM Authority is explicitly Project-Owner-reserved under Unified Governance.
The Genesis Constitution freezes IAM placement inside ns_server but explicitly states that placement does not imply semantic authority or Source of Truth and requires later architecture to resolve IAM Authority independently.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` owns native IAM Semantic Authority

`ns_server` owns final platform-native IAM semantic authority. Other Product Components may consume authenticated/authorized Principal context, host interaction surfaces, execute under identity/grant context, or mediate technical capabilities without acquiring IAM Authority by execution, hosting, communication, caching, or provider placement.

External identity/authentication systems may later remain authoritative for their bounded external identity or authentication facts without automatically becoming the native platform IAM Semantic Authority.

### B — External Identity Authority owns IAM Authority

An external AD/LDAP/IdP or equivalent enterprise identity authority owns final IAM semantics and `ns_server` acts as consumer/adapter/mirror. This would make the core IAM semantic source dependent on deployment-specific external infrastructure and would require separate semantics for standalone/offline environments.

### C — Federated IAM Authority

`ns_server` and one or more external identity authorities jointly own authoritative IAM semantic partitions. This would require explicit Principal namespace partition, identity linking, lifecycle, revocation, conflict, historical interpretation, offline behavior, and reconciliation semantics.

## 4. Recommendation Presented

`A — ns_server owns native IAM Semantic Authority`.

Rationale: IAM is constitutionally placed inside `ns_server`, while placement alone is not authority. Explicitly assigning native IAM semantic authority to `ns_server` creates one stable product-semantic owner without making an authentication provider, external directory, `ns_runtime`, `ns_node`, `ns_agent`, `ns_web`, Shared Foundation, framework, or database the IAM authority by technical placement. It also preserves standalone/private/offline correctness while retaining future external identity federation and provider replaceability.

## 5. Project Owner Decision

```text
Selected Option
A

Native IAM Semantic Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY now consume the following Owner-decided fact:

```text
ns_server
→ owns native ns_evermore IAM Semantic Authority

ns_runtime
→ may transport or consume Principal/authentication/authorization context
→ does not gain IAM Authority through communication, coordination, scheduling, dispatch, routing, connection management, or runtime observation

ns_node
→ may execute under Principal/grant context and may retain bounded local evidence where later authorized
→ does not gain IAM Authority through local execution, offline operation, local possession, caching, grant exercise, recovery, reconnection, or reconciliation handoff

ns_agent
→ may act under Agent/Principal identity and invoke tools/models
→ does not gain IAM Authority through Agent execution, provider mediation, context, memory, RAG, or tool invocation

ns_web
→ may provide IAM administration and human-facing identity interaction surfaces
→ does not gain IAM Authority through UI editing, browser state, session presentation, or control-plane interaction

Shared Foundation
→ may later provide reusable identity/security technical capabilities if authorized
→ does not gain IAM Authority through mediation or provider placement

External Identity / Authentication Provider
→ may retain bounded authority for its own external identity/authentication facts where later accepted architecture establishes that relationship
→ does not become native ns_evermore IAM Semantic Authority merely by integration
```

## 7. Explicit Non-Implications

This decision MUST NOT be interpreted as establishing any of the following automatically:

```text
IAM Authority = Tenant Authority
IAM Authority = Policy Authority
IAM Authority = Organization Authority
IAM Authority = Authentication Provider
IAM Authority = External Directory Authority
IAM Authority = IAM Source of Truth
IAM Authority = IAM Actual-state Ownership
IAM Authority = Credential Authority universally
IAM Authority = Session Runtime Ownership
IAM Authority = Database Ownership
ns_server Placement = Universal Governance Authority
External Authentication = Native IAM Authority Transfer
```

`Z2-MDE-001` and `Z2-MDE-002` remain separate decisions for Tenant Authority and Tenant canonical Source of Truth. Policy, Organization, IAM SoT/Actual-state, security/trust and other material authority questions remain separately classified under Unified Governance.

## 8. Constraint Preservation

This decision preserves:

- `NSE-001` native Tenant semantic invariance and explicit Tenant context;
- `NSE-002` Tenant / Organization non-collapse;
- `NSE-003` Organization plurality/extensibility;
- `NSE-004` private/offline correctness and governance invariance;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` authority non-transfer through composition, invocation, runtime, or shared infrastructure;
- `NSE-008` local execution authority and grant-exercise separation;
- `NSE-009` representation-independent stable cross-boundary semantics;
- `NSE-010` extension governance / authority non-escalation;
- `NSE-011` bounded external Source-of-Truth preservation;
- `NSE-012` Shared Foundation/provider authority neutrality;
- `NSE-013` complete-system semantic integrity;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 9. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- later IAM / Policy / Organization architecture where native IAM Authority is a dependency;
- later Component and Runtime responsibility design;
- later authentication/federation/identity-provider contract design when those phases are explicitly authorized.

It does not authorize those downstream phases.

## 10. Deferred Questions

The following remain unresolved by this decision and MUST be closed by the appropriate later authorized architecture/design authority before implementation depends on them:

```text
IAM Source of Truth
IAM Actual-state Ownership
Principal namespace / identity model
Authentication Authority and provider/federation topology
Credential lifecycle
Session/runtime identity state
Policy Authority and authorization decision topology
Organization Authority and organization-to-Principal semantics
External identity mapping / linking / historical interpretation
Offline authentication/grant semantics
```

Any item that is MDE-class when reached returns to Project Owner under Unified Governance.

## 11. Revalidation Trigger

Revalidation is required if the Project Owner later changes native IAM Semantic Authority away from `ns_server`, changes IAM placement/root product responsibility, changes the fixed Product Component topology, or explicitly changes the authority relationship between native IAM and an external identity authority.

Changes in authentication provider, database, framework, process, service, container, deployment, package, cache, transport, LDAP/AD/OIDC technology, or provider implementation do not by themselves revalidate this decision.

## 12. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Contract/Module/Provider Design, Implementation Planning, IWP, or coding.
