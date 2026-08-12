# NGRP-001 Z2 MDE-001 — Tenant Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-001`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final **Tenant Semantic Authority** for `ns_evermore`?

This decision concerns the authority that defines the meaning and authoritative semantic governance of Tenant identity and Tenant lifecycle meaning. It does **not** by itself decide Tenant persistence, Tenant database topology, Tenant Source of Truth, Tenant Actual-state Ownership, IAM Authority, Policy Authority, Organization Authority, or runtime/deployment placement.

## 2. Classification

```text
Classification
MDE

Reason
Tenant Authority is explicitly Project-Owner-reserved under Unified Governance.
Accepted NSE-001 requires later Project Architecture to identify Tenant semantic authority and prohibits deriving that authority from deployment, Organization, persistence, framework, or physical placement.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` owns Tenant Semantic Authority

`ns_server` is the final Product Component semantic authority for Tenant identity and Tenant lifecycle meaning. Other Product Components consume, carry, enforce, observe, or execute under Tenant context without acquiring Tenant Authority by execution, mediation, hosting, storage, caching, or communication.

### B — Shared Foundation owns Tenant Semantic Authority

Shared Foundation becomes the final Tenant semantic authority used by all Product Components. This would materially increase Foundation semantic responsibility beyond provider-neutral reusable capability mediation.

### C — Federated Tenant Authority

Multiple Product Components own authoritative Tenant semantic partitions under an explicit federated authority model. This would require durable authority partition, conflict, reconciliation, temporal, and historical interpretation semantics.

## 4. Recommendation Presented

`A — ns_server owns Tenant Semantic Authority`.

Rationale: Tenant is a customer/security/resource/governance boundary. `ns_server` already contains the constitutionally placed IAM, Policy Center, Organization, Knowledge/Data governance-facing backend capabilities, while placement of those capabilities does not imply common authority. Selecting `ns_server` gives Tenant one explicit Product Component semantic authority without turning Shared Foundation, runtime mediation, local execution, UI state, or persistence placement into authority.

## 5. Project Owner Decision

```text
Selected Option
A

Tenant Semantic Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY now consume the following Owner-decided fact:

```text
ns_server
→ owns Tenant Semantic Authority

ns_runtime
→ does not gain Tenant Authority through communication, coordination, scheduling, dispatch, routing, or runtime observation

ns_node
→ does not gain Tenant Authority through local execution, offline operation, local source-fact production, caching, recovery, reconnection, or reconciliation handoff

ns_agent
→ does not gain Tenant Authority through Agent execution, tool invocation, model/provider mediation, context, memory, or RAG consumption

ns_web
→ does not gain Tenant Authority through UI editing, browser state, administrative surfaces, or human-facing control-plane interaction

Shared Foundation
→ does not gain Tenant Authority through reusable capability mediation, storage, cache, transport, or provider placement
```

## 7. Explicit Non-Implications

This decision MUST NOT be interpreted as establishing any of the following automatically:

```text
Tenant Authority = IAM Authority
Tenant Authority = Policy Authority
Tenant Authority = Organization Authority
Tenant Authority = Knowledge/Data Authority
Tenant Authority = Artifact Authority
Tenant Authority = Execution Admission Authority
Tenant Authority = Tenant Source of Truth
Tenant Authority = Tenant Actual-state Ownership
Tenant Authority = Database Ownership
Tenant Authority = Runtime State Ownership
ns_server Placement = Universal Authority
```

Each material Authority / SoT / Actual-state question remains separately classified under Unified Governance.

## 8. Constraint Preservation

This decision preserves:

- `NSE-001` native Tenant semantic invariance;
- `NSE-002` Tenant / Organization non-collapse;
- `NSE-004` offline governance invariance;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` authority non-transfer through composition;
- `NSE-008` local execution authority separation;
- `NSE-012` Shared Foundation authority neutrality;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 9. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- later IAM / Policy / Organization architecture where Tenant Authority is a dependency;
- later Component and Runtime responsibility design, without authorizing those phases.

## 10. Revalidation Trigger

Revalidation is required if the Project Owner later changes Tenant Semantic Authority away from `ns_server`, changes the fixed Product Component topology, changes native Tenant semantics, or explicitly changes the authority relationship between Tenant and another governance domain.

Changes in database, process, service, container, deployment, package, Django app, cache, transport, or provider placement do not by themselves revalidate this decision.

## 11. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
