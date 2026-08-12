# NGRP-001 Z2 MDE-002 — Tenant Source of Truth Owner Decision

- **Decision ID:** `Z2-MDE-002`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Decision-predecessor HEAD:** `8832e8d67587966fea54d18c7441960dcf098bd2`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-001`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Project Architecture boundary holds the canonical **Tenant Source of Truth** for native `ns_evermore` Tenant identity and governance lifecycle state?

This decision is distinct from `Z2-MDE-001` Tenant Semantic Authority. Semantic Authority defines the governing meaning of Tenant; Source of Truth identifies the canonical boundary whose accepted Tenant records/state are authoritative for that native semantic domain. This decision does **not** by itself decide Tenant persistence technology, database topology, Tenant Actual-state Ownership, IAM Authority, Policy Authority, Organization Authority, external customer-master authority, or runtime/deployment topology.

## 2. Classification

```text
Classification
MDE

Reason
Source of Truth is explicitly Project-Owner-reserved under Unified Governance.
NSE-001 requires later Project Architecture to resolve Tenant Source of Truth without deriving it from Organization, deployment, persistence, framework, or physical placement.
NSE-011 requires bounded external source-of-truth preservation and prohibits ingestion or synchronization from transferring authority automatically.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` holds the native Tenant canonical Source of Truth

`ns_server` holds canonical native Tenant identity and governance lifecycle state. External customer, commercial, directory, or enterprise systems may retain bounded Source-of-Truth authority for their own facts and may map to Tenant, but do not redefine native Tenant identity or Tenant canonical state automatically.

### B — External enterprise/customer master holds Tenant Source of Truth

A registered external customer/enterprise master controls canonical Tenant identity/lifecycle and `ns_server` maintains a synchronized representation. This couples native Tenant correctness to deployment-specific external authority semantics and requires a distinct standalone/offline fallback model.

### C — Federated / partitioned Tenant Source of Truth

`ns_server` and one or more registered external authorities own different authoritative Tenant semantic partitions under explicit federation. This requires durable partition, conflict, freshness, temporal, offline and reconciliation semantics and materially increases multiple-final-authority risk.

## 4. Recommendation Presented

`A — ns_server holds the native Tenant canonical Source of Truth`.

Rationale: the product requires one native Tenant semantic model across deployment modes. Keeping native Tenant SoT in `ns_server` aligns the canonical boundary with the already Owner-decided Tenant Semantic Authority while preserving the distinction between Authority and SoT. It also preserves `NSE-011`: external systems may remain authoritative for bounded customer/commercial/directory facts, but mapping, synchronization and ingestion do not become Tenant identity equality or automatic Tenant authority transfer.

## 5. Project Owner Decision

```text
Selected Option
A

Tenant Canonical Source of Truth
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY consume the following Owner-decided facts:

```text
Tenant Semantic Authority
→ ns_server                    # Z2-MDE-001

Tenant Canonical Source of Truth
→ ns_server                    # Z2-MDE-002

External customer / commercial / directory / enterprise facts
→ MAY retain bounded external SoT where applicable
→ MUST remain explicitly mapped/provenanced
→ MUST NOT become native Tenant identity or Tenant canonical state automatically

Synchronization / ingestion / mapping
→ does not transfer Tenant Authority or Tenant SoT automatically
```

Other Product Components may consume, cache, carry, observe or act under Tenant context, but such participation does not create Tenant SoT ownership.

## 7. Explicit Non-Implications

This decision MUST NOT be interpreted as establishing any of the following automatically:

```text
Tenant SoT = Tenant Actual-state Ownership
Tenant SoT = IAM Authority
Tenant SoT = Policy Authority
Tenant SoT = Organization Authority
Tenant SoT = Knowledge/Data Authority
Tenant SoT = Artifact Authority
Tenant SoT = Execution Admission Authority
Tenant SoT = Universal Business SoT
Tenant SoT = Database Ownership
ns_server = SoT for every enterprise/customer fact
External mapping = Tenant identity equality
Synchronization = Tenant canonicalization
```

External systems remain eligible to be authoritative Sources of Truth for their bounded domains under `NSE-011`.

## 8. Offline / Private Consequences

Core Tenant correctness must remain valid without a mandatory external customer-master, SaaS control plane or public network dependency. Offline/private operation may use later-designed replicated/cached Tenant evidence where authorized, but local presence or disconnection does not transfer native Tenant SoT away from `ns_server` automatically.

No offline fail-open/fail-closed, replication, caching, synchronization or reconciliation mechanism is selected by this decision.

## 9. Constraint Preservation

This decision preserves:

- `NSE-001` native Tenant semantic invariance;
- `NSE-002` Tenant / Organization non-collapse;
- `NSE-004` offline core correctness and governance invariance;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` authority non-transfer through composition;
- `NSE-008` local fact / canonical-state separation;
- `NSE-011` bounded external Source-of-Truth preservation;
- `NSE-012` Shared Foundation authority neutrality;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 10. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- later IAM / Policy / Organization and enterprise-integration architecture where Tenant SoT is a dependency;
- later Component / Runtime architecture where replicated or observed Tenant state is mapped, without authorizing those phases.

## 11. Revalidation Trigger

Revalidation is required if the Project Owner later moves native Tenant canonical SoT away from `ns_server`, makes an external customer/enterprise system the native Tenant SoT, introduces federated authoritative Tenant partitions, changes native Tenant semantics, or changes bounded external SoT preservation semantics.

Changes in database, storage engine, process, service, container, deployment, package, framework, cache, transport, replication technology or provider placement do not by themselves revalidate this decision.

## 12. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
