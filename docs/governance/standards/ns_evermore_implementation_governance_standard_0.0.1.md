# ns_evermore Implementation Planning / IWP / Codex Governance Standard

## Authority Metadata

- **Document ID:** `NS-EVERMORE-IMPLEMENTATION-GOV-STANDARD-0001`
- **Version:** `0.0.1`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `IMPLEMENTATION_GOVERNANCE_STANDARD_CANDIDATE`
- **Program / Phase:** `NGRP-001 / Z0`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`

---

## 1. Boundary

This document establishes future implementation governance only. It does **not** create an Implementation Master Plan, an Implementation Work Package, or implementation authorization.

## 2. Entry Gate to Implementation Planning

Formal Implementation Planning is forbidden until the Global Architecture Coordinator has issued:

```text
DESIGN_TO_IMPLEMENTATION_READY
```

The readiness assessment must confirm all required architecture, component/runtime/foundation design, contracts, module/provider boundaries, state/failure/Tenant/Organization/security/migration semantics are complete, with no architecture-defined escape, open architecture MDE, or unpersisted Owner decision.

## 3. Implementation Planning Rule

Implementation Planning consumes accepted design and MUST NOT create new Architecture Authority.

If planning discovers multiple implementation paths whose choice changes authority, source of truth, Product Component boundary, Runtime boundary, Security, Tenant, Organization, Contract semantics, or major long-term lock-in:

```text
STOP
→ RETURN TO CORRECT DESIGN AUTHORITY
```

## 4. Implementation Master Plan Standard

The future `NS_EVERMORE_IMPLEMENTATION_MASTER_PLAN` must include at least:

```text
Implementation Baseline
Accepted Design Revisions
Architecture-to-code Traceability
Repository / Package Structure
Dependency Graph
Implementation Order
Bootstrap Sequence
Migration Strategy
Test Strategy
Conformance Strategy
Offline Build Strategy
Release Strategy
Rollback Strategy
Verification Gates
Implementation Work Package Index
```

It must be specific enough that implementation sessions do not need to redesign architecture.

## 5. Implementation Work Package Standard

Each future IWP must be small enough for one bounded Codex session and large enough to produce one coherent verified increment.

Stable namespace:

```text
IWP-###
```

Required IWP fields:

```text
IWP ID
Title
Objective
Design Authority
Accepted Upstream Documents
Exact Scope
Allowed Files / Modules
Forbidden Files / Areas
Dependencies
Preconditions
Functional Requirements
Non-functional Requirements
Contract Requirements
State Requirements
Persistence Requirements
Migration Requirements
Failure Behavior
Security Requirements
Tenant Requirements
Organization Requirements
Offline Requirements
Observability Requirements
Tests Required
Conformance Checks
Acceptance Criteria
Expected Deliverables
Required Git Evidence
Stop Rule
```

## 6. IWP Dependency Ordering

IWP ordering must follow the real dependency graph, including where applicable:

```text
Foundation before Consumer
Contract before Implementation
State Model before Transition Logic
Provider Interface before Provider Implementation
Core Governance before Bypass-sensitive Consumer
Migration before Dependent Runtime Change
```

Folder order, component number, or developer preference are insufficient ordering criteria.

## 7. Codex Rule

```text
CODEX IMPLEMENTS ACCEPTED DESIGN
CODEX DOES NOT REDESIGN ACCEPTED ARCHITECTURE
```

Codex MUST stop and raise a design gap if it encounters insufficient accepted design, architecture/contract ambiguity, missing state semantics, unexpected dependency conflict, missing provider capability, or a requirement to change authority, source of truth, Product Component boundary, Tenant/Organization semantics, Security/Policy/Audit, or contract semantics.

## 8. Codex Session Prompt Standard

Each authorized IWP must generate a repository-backed prompt containing:

```text
Repository
Branch
IWP ID
Exact Design Baseline
Required Read Set
Current Entry HEAD
Allowed Scope
Forbidden Scope
Required Implementation
Required Tests
Required Verification
Architecture Invariants
Git Change Boundary
Stop Conditions
Required Final Handoff
```

A vague request such as `implement ns_node`, `write cache_client`, or `implement IAM` is invalid implementation authorization.

## 9. Incremental Implementation Principle

Every implementation increment must be:

```text
SMALL
BOUNDED
VERIFIABLE
REVERSIBLE
```

Each IWP must independently support build, test, diff review, architecture traceability verification, commit, and accept/reject.

## 10. IWP Acceptance Gate

Each completed IWP is independently reviewed for:

```text
Scope Compliance
Design Compliance
Contract Compliance
Architecture Invariant Preservation
Security
Tenant
Organization
Offline Correctness
Tests
Migration
Dependency Closure
Unexpected Drift
```

Allowed outcomes:

```text
ACCEPT
ACCEPT_WITH_CORRECTION
REJECT
```

Dependent IWPs do not automatically start while an upstream IWP remains unaccepted.

## 11. Implementation Continuity

The implementation program must later maintain:

```text
Implementation Global State
Implementation Working State
Implementation Ledger
Implementation Work Package Index
```

This standard defines the schema obligation only; none of those implementation-phase state artifacts are instantiated in Z0 because Implementation Planning is not authorized.

## 12. Z0 Confirmation

```text
Implementation Master Plan created → NO
IWP created → 0
Code changes authorized → NO
Codex implementation authorized → NO
Implementation governance schema established → YES
```
