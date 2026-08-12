# NGRP-001 Z2 MDE-017 — Native Product Definition Canonical SoT Topology Owner Decision

- **Decision ID:** `Z2-MDE-017`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Decision Entry HEAD:** `44ecf0cf828b6d12b845de8e51a9826496ce4aa3`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance `0.0.2`; Decision Registry `0.0.4`; accepted `NSE-001..017`; `Z2-MDE-009`; `Z2-MDE-010`; `Z2-MDE-011`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

What Project-level canonical Source-of-Truth topology governs native Product Definition state for Business Application, Automation / Workflow, and AI Agent definitions?

This decision is separate from domain Semantic Authority, Formal Artifact Acceptance, Formal Execution Admission, and Runtime Actual-state ownership.

## 2. Classification

```text
Classification
MDE

Reason
Canonical definition Source-of-Truth ownership is a Source-of-Truth decision and therefore Project-Owner-reserved under Unified Governance. It must not be inferred automatically from semantic ownership, physical placement, builder placement, artifact state, registry location, or runtime execution location.
```

## 3. Alternatives Presented to Project Owner

### A — Definition SoT follows each domain's Semantic Authority

```text
Business Application Semantic Authority
→ ns_server
Business Application Canonical Definition SoT
→ ns_server

Automation Semantic Authority
→ ns_server
Automation Canonical Definition SoT
→ ns_server

AI Agent Semantic Authority
→ ns_agent
AI Agent Canonical Definition SoT
→ ns_agent
```

### B — Unified Definition SoT in `ns_server`

All Business Application, Automation and AI Agent canonical definition state is owned by `ns_server`, while Agent Semantic Authority remains in `ns_agent`.

### C — Accepted Artifact becomes Canonical Definition SoT

Formal Accepted Artifact state becomes the canonical Product Definition state.

## 4. Recommendation Presented

`A — Definition SoT follows each domain's Semantic Authority`.

Rationale: it preserves native capability-domain identity, avoids turning `ns_server` into a universal definition control plane, and maintains strict separation between Definition, Artifact Acceptance, Execution Admission and Runtime Actual-state.

## 5. Project Owner Decision

```text
Selected Option
A

Native Product Definition Canonical SoT Topology
→ DEFINITION_SOT_FOLLOWS_DOMAIN_SEMANTIC_AUTHORITY
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The Project Architecture candidate MAY consume the following Owner-decided facts:

```text
Business Application Definition / Platform Semantic Authority
→ ns_server

Business Application Canonical Definition SoT
→ ns_server

Automation Definition / Workflow Semantic Authority
→ ns_server

Automation Canonical Definition SoT
→ ns_server

AI Agent Definition / Semantic Authority
→ ns_agent

AI Agent Canonical Definition SoT
→ ns_agent
```

These assignments are explicit Owner decisions. They MUST NOT be treated as an automatic general rule that Semantic Authority always implies Source-of-Truth ownership in every domain.

## 7. Permanent State Separation

```text
Canonical Definition SoT
!= Domain Semantic Authority

Canonical Definition SoT
!= Domain Semantic Certification

Canonical Definition SoT
!= Candidate Artifact

Canonical Definition SoT
!= Formal Accepted Artifact

Canonical Definition SoT
!= Formal Execution Admission

Canonical Definition SoT
!= Runtime Actual-state
```

The fact that a domain's Semantic Authority and Canonical Definition SoT are co-located in the selected topology does not collapse those semantic responsibilities.

## 8. Component Consequences

### 8.1 `ns_server`

`ns_server` owns canonical native definition state for Business Application and Automation / Workflow definitions because the Project Owner explicitly selected this topology.

This does NOT imply that `ns_server` owns AI Agent definition state, every customer business-domain fact, every external factual SoT, or all runtime state.

### 8.2 `ns_agent`

`ns_agent` owns canonical AI Agent definition state and Agent Semantic Authority.

This preserves `ns_agent` as the native AI Agent Runtime / Tooling Product Component rather than reducing it to a generic inference/execution worker.

This does NOT grant `ns_agent` authority over Knowledge, Data, Automation, Business Application, Policy, Artifact Acceptance, Execution Admission, or any capability merely invoked by an Agent.

### 8.3 `ns_web`

Builder/editor state in `ns_web` is not canonical Product Definition state merely because a definition is being authored there.

```text
UI Edit State
!= Canonical Definition SoT
```

### 8.4 `ns_runtime` / `ns_node`

Scheduling, dispatch, possession, installation or execution of a Product Definition or derived artifact does not transfer Product Definition SoT ownership to `ns_runtime` or `ns_node`.

## 9. Lifecycle Consequence

Project Architecture MUST preserve a lifecycle shape equivalent at the semantic level to:

```text
Domain Semantic Authority
        │
        ▼
Canonical Definition SoT
        │
        ▼
Domain Validation / Certification
        │
        ▼
Candidate Artifact
        │
        ▼
Formal Artifact Acceptance
→ ns_server
        │
        ▼
Formal Execution Admission
→ ns_server
        │
        ▼
Runtime Coordination / Execution
→ applicable Product Components
```

The exact artifact format, certification mechanism, build process, API, storage technology and runtime protocol remain outside this MDE.

## 10. Explicit Non-implications

This decision does NOT establish:

```text
Semantic Authority always implies Source-of-Truth ownership
ns_server = universal Definition SoT
ns_agent = universal AI/data/tool authority
Accepted Artifact = Canonical Definition
Builder State = Canonical Definition
Installed Artifact = Canonical Definition
Runtime Possession = Canonical Definition
Latest Copy = Canonical Definition
Database Location = Definition Authority
```

## 11. Constraint Preservation

This decision preserves:

- `NSE-005` fixed Product Component semantic topology;
- `NSE-006` first-class capability-domain non-subordination and authority non-transfer;
- `NSE-007` Definition / Artifact / Runtime governance-state separation;
- `NSE-008` execution authority separation;
- `NSE-009` representation-independent stable semantics;
- `NSE-012` Shared Foundation authority neutrality;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream non-invention and implementation derivability.

## 12. Downstream Consumers

This Owner decision is an authorized input to:

- the corrected Z2 Batch 1 Project Architecture Candidate;
- the Responsibility / Authority / SoT Matrix;
- Cross-component Semantic Dependency Topology;
- later Business Application Architecture;
- later Automation Architecture;
- later AI Agent Architecture;
- later Artifact lifecycle and execution-governance design.

No later phase is authorized by this decision.

## 13. Revalidation Trigger

Revalidation is required if the Project Owner later changes one or more of:

- Business Application Semantic Authority;
- Automation Semantic Authority;
- AI Agent Semantic Authority;
- Business Application Canonical Definition SoT;
- Automation Canonical Definition SoT;
- AI Agent Canonical Definition SoT;
- the Definition / Artifact / Admission / Runtime state-separation model.

Changing storage, database, builder framework, artifact format, runtime process, transport, provider or deployment technology does not by itself revalidate this decision.

## 14. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Foundation Contract/Module/Provider Design, Implementation Planning, IWP, or coding.
