# NGRP-001 Z2 MDE-005 — Organization Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-005`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Immediate Pre-decision HEAD:** `9eaafb7c4864bd968462acfaf09221d1575a3709`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-001..004`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final native **Organization Semantic Authority** for `ns_evermore`?

This decision concerns the authority that defines the platform meaning and authoritative semantic governance of Organization concepts, including Organization System, Organization Identity, Organization Type, Relationship Type, Organization Dimension, Membership, Mapping, Alias, and historical Organization semantics.

It does **not** by itself decide Organization canonical Source of Truth, bounded external Organization Sources of Truth, persistence, tree/graph/relational representation, membership storage, historical storage, external mapping algorithms, Tenant Authority, IAM Authority, Policy Authority, or runtime/deployment placement.

## 2. Classification

```text
Classification
MDE

Reason
Organization Authority is explicitly Project-Owner-reserved under Unified Governance.
Genesis Constitution freezes Organization capability placement inside ns_server while explicitly prohibiting placement from deciding Authority.
Accepted NSE-002 / NSE-003 require Organization to remain distinct from Tenant, structurally plural/extensible, and later architecture to resolve Organization Authority / Source of Truth explicitly.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` owns native Organization Semantic Authority

`ns_server` is the final Product Component semantic authority for native `ns_evermore` Organization semantics. Other Product Components may consume, carry, execute under, administer, visualize, cache, or project Organization context without acquiring Organization Authority. External enterprise systems may remain authoritative for bounded external Organization facts without thereby defining native platform Organization semantics.

### B — Federated Organization Semantic Authorities

Multiple Organization systems or Product Component boundaries hold independent final semantic authority partitions. This would require durable authority partitioning, cross-system identity, mapping, conflict, historical interpretation, and reconciliation semantics.

### C — External Enterprise Organization Master owns Organization Authority

An external HR, AD, ERP, OA, HIS or another enterprise system becomes final Organization semantic authority, while `ns_server` acts primarily as a synchronized representation/integration boundary.

## 4. Recommendation Presented

`A — ns_server owns native Organization Semantic Authority`.

Rationale: the Constitution requires a native, structurally plural and extensible Organization capability inside `ns_server`, explicitly rejects one universal external Organization tree/model, and requires explicit external mapping. Selecting `ns_server` as native Organization semantic authority preserves one platform semantic model while still allowing bounded external systems to retain their own Sources of Truth and source-fact authority under `NSE-011`.

## 5. Project Owner Decision

```text
Selected Option
A

Native Organization Semantic Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY now consume the following Owner-decided fact:

```text
ns_server
→ owns native Organization Semantic Authority

ns_runtime
→ does not gain Organization Authority through transport, routing, coordination, scheduling, dispatch, or runtime observation

ns_node
→ does not gain Organization Authority through local execution, offline operation, local caching, local source-fact production, recovery, reconnection, or reconciliation handoff

ns_agent
→ does not gain Organization Authority through Agent execution, tool invocation, model/provider mediation, memory, context, or RAG consumption

ns_web
→ does not gain Organization Authority through administration, visualization, editing, browser state, or control-plane interaction

Shared Foundation
→ does not gain Organization Authority through reusable capability mediation, storage, cache, transport, provider abstraction, or shared implementation

External HR / AD / ERP / HIS / OA / other enterprise systems
→ MAY remain authoritative for their bounded external Organization facts
→ do not become native ns_evermore Organization Semantic Authority merely through synchronization or integration
```

## 7. Explicit Non-Implications

This decision MUST NOT be interpreted as establishing any of the following automatically:

```text
Organization Authority = Tenant Authority
Organization Authority = IAM Authority
Organization Authority = Policy Authority
Organization Authority = Organization Canonical Source of Truth
Organization Authority = Every Organization Fact Source of Truth
Organization Authority = External Organization Source of Truth
Organization Authority = Database Ownership
Organization Authority = Runtime State Ownership
External Organization Mapping = Identity Equality
ns_server Placement = Universal Authority
```

Each material Source-of-Truth / Actual-state / external-authority question remains separately classified under Unified Governance.

## 8. Constraint Preservation

This decision preserves:

- `NSE-001` native Tenant semantic invariance;
- `NSE-002` Tenant / Organization semantic non-collapse;
- `NSE-003` Organization structural plurality and extensibility;
- `NSE-004` offline governance invariance;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` authority non-transfer through composition;
- `NSE-011` bounded external Source-of-Truth preservation;
- `NSE-012` Shared Foundation authority neutrality;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 9. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- later IAM / Policy / Organization architecture where Organization context is consumed;
- later external enterprise integration design;
- later Component and Runtime responsibility design, without authorizing those phases.

## 10. Revalidation Trigger

Revalidation is required if the Project Owner later changes native Organization Semantic Authority away from `ns_server`, changes the fixed Product Component topology, changes Tenant / Organization non-collapse, changes Organization structural plurality/extensibility, or explicitly makes an external Organization system the platform-wide semantic authority.

Changes in database, tree/graph representation, process, service, container, deployment, package, Django app, cache, transport, external HR/AD provider, or mapping implementation do not by themselves revalidate this decision.

## 11. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
