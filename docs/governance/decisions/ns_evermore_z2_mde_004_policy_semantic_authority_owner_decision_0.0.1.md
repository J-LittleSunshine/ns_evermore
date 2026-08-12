# NGRP-001 Z2 MDE-004 — Unified Policy Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-004`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-001..003`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final native **Unified Policy Semantic Authority** for `ns_evermore`?

This decision concerns the authority that defines and governs the meaning of formal platform Policy semantics. It does not by itself decide Policy persistence, a Policy engine/provider, RBAC/ABAC/ReBAC representation, Policy evaluation topology, enforcement points, offline grants, fail-open/fail-closed behavior, IAM Authority, Organization Authority, Artifact/Admission Authority, or Runtime Responsibility.

## 2. Classification

```text
Classification
MDE

Reason
Policy Authority is explicitly Project-Owner-reserved under Unified Governance.
The Genesis Constitution places Unified Policy Center inside ns_server while explicitly prohibiting placement from automatically determining semantic authority.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` owns Unified Policy Semantic Authority

`ns_server` is the final native semantic authority for formal platform Policy meaning and governance. Other Product Components may consume, distribute, evaluate, enforce, observe, or execute under Policy context without acquiring Policy Authority by execution, mediation, hosting, storage, caching, UI editing, or communication.

### B — Federated Domain Policy Authorities

Multiple Product Components or capability domains own final Policy authority partitions, requiring explicit authority partition, namespace, precedence, conflict, composition, historical interpretation, offline and reconciliation semantics.

### C — External Enterprise Policy Authority

An external enterprise IAM/PDP/policy system is the final Policy semantic authority while `ns_server` acts as an adapter, projection, or consumer, making native Policy meaning dependent on external authority semantics.

## 4. Recommendation Presented

`A — ns_server owns Unified Policy Semantic Authority`.

Rationale: the Constitution already places Unified Policy Center in `ns_server`; formalizing `ns_server` as the unique native Policy semantic authority preserves one final authority while keeping IAM, Tenant, Organization and business-domain semantics distinct. It also allows distributed policy consumption/enforcement and later replaceable Policy engines without transferring semantic authority to runtime, node execution, Agent invocation, UI surfaces, Shared Foundation, providers, or persistence placement.

## 5. Project Owner Decision

```text
Selected Option
A

Unified Policy Semantic Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

```text
ns_server
→ owns native Unified Policy Semantic Authority

ns_runtime
→ may distribute / coordinate / consume later-defined Policy decisions or context
→ does not gain Policy Authority through communication, routing, scheduling, dispatch or observation

ns_node
→ may later enforce or exercise governed Policy/grant context during local execution
→ does not gain Policy Authority through enforcement, effect execution, locality or offline operation

ns_agent
→ may act under applicable Policy and invoke protected capabilities
→ does not gain Policy Authority through Agent reasoning, tool invocation or provider mediation

ns_web
→ may provide Policy administration/editing/governance surfaces
→ does not gain Policy Authority through UI state or editing

Shared Foundation / Policy engine / provider
→ may later provide reusable or replaceable realization capability
→ does not gain Policy Semantic Authority automatically
```

## 7. Explicit Non-Implications

```text
Policy Authority != Tenant Authority
Policy Authority != IAM Authority
Policy Authority != Organization Authority
Policy Authority != Business-domain Semantic Authority
Policy Authority != Policy Evaluation Placement
Policy Authority != Enforcement Placement
Policy Authority != Grant Exercise
Policy Authority != Database Ownership
Policy Authority != Runtime Actual-state Ownership
Policy Engine / Provider != Policy Semantic Authority automatically
ns_server Placement != Universal Authority
```

The current decision does not require every business rule to become a Unified Policy rule. Business-domain semantics remain owned by their later accepted semantic authorities; only semantics formally admitted into the platform Policy domain fall under Unified Policy Semantic Authority.

## 8. Constraint Preservation

This decision preserves accepted `NSE-001..017`, especially:

- native Tenant semantics and Tenant/Organization non-collapse;
- offline governance invariance;
- first-class capability authority non-transfer;
- Definition/Artifact/Runtime separation;
- local execution / grant exercise authority separation;
- external SoT preservation;
- Shared Foundation/provider authority neutrality;
- Repository-backed continuity and downstream non-invention.

## 9. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- later IAM / Policy / Organization architecture where Policy Authority is a dependency;
- later Component and Runtime responsibility design, without authorizing those phases.

## 10. Revalidation Trigger

Revalidation is required if the Project Owner later changes Unified Policy Semantic Authority away from `ns_server`, changes the placement or constitutional meaning of Unified Policy Center, introduces multiple final native Policy authorities, or explicitly changes the relationship between native Policy semantics and an external authority.

Changes in Policy engine/provider, database, process, service, container, deployment, package, cache, transport, enforcement point, or UI placement do not by themselves revalidate this decision.

## 11. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
