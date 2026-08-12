# NGRP-001 Z2 MDE-014 — Runtime Actual-state Ownership Topology Owner Decision

- **Decision ID:** `Z2-MDE-014`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Decision Entry HEAD:** `89bffadb0fa21616804dde1f46cfe51d4eeac15a`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-001..013`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

What Project-level ownership topology governs **Runtime Actual-state** across the five Product Components without turning runtime coordination, local execution, aggregation, persistence, or observation into universal factual authority?

This decision concerns ownership of facts about what is actually occurring or has actually occurred within bounded runtime responsibility. It does **not** design Runtime Roles, processes, services, workers, schedulers, queues, WebSocket messages, runtime state machines, persistence, protocols, heartbeat mechanisms, recovery algorithms, or deployment topology.

This decision is distinct from desired/configured state, definition state, Artifact state, Execution Admission state, UI projection, and aggregated system views.

## 2. Classification

```text
Classification
MDE

Reason
Actual-state Ownership and major runtime factual authority topology are Project-Owner-reserved under Unified Governance.
The Genesis Constitution and accepted NSE baseline explicitly reject automatic inference that Communication Hub, observed runtime state, local execution facts, local cache/state, process placement, database placement, or connectivity creates canonical Runtime Actual-state ownership.
```

## 3. Alternatives Presented to Project Owner

### A — One global canonical Runtime Actual-state owned by `ns_runtime`

`ns_runtime` owns the complete-system canonical Runtime Actual-state. Other Product Components produce or report observations/source facts, which `ns_runtime` canonicalizes.

### B — Governed Per-Runtime-Semantic-Partition Actual-state Ownership

Each bounded runtime semantic partition has exactly one explicitly established Actual-state Owner. Runtime facts remain owned by the Product Component responsibility in which those facts genuinely originate, while system-level runtime views are coordinated/derived projections and do not gain universal factual authority by aggregation.

### C — One global canonical Runtime Actual-state owned by `ns_server`

`ns_server` becomes the system control-plane Runtime Actual-state owner, while `ns_runtime`, `ns_node`, `ns_agent`, and other components report runtime facts into that canonical state.

## 4. Recommendation Presented

`B — Governed Per-Runtime-Semantic-Partition Actual-state Ownership`.

Rationale: this preserves real source/effect facts under offline/degraded execution, prevents `ns_runtime` from becoming Universal SoT merely because it coordinates communication/scheduling/dispatch, prevents `ns_server` governance ownership from becoming physical actuality ownership, and preserves explicit factual responsibility for locally or component-originated runtime effects.

## 5. Project Owner Decision

```text
Selected Option
B

Runtime Actual-state Ownership Topology
→ GOVERNED_PER_RUNTIME_SEMANTIC_PARTITION_ACTUAL_STATE_OWNERSHIP
```

The Project Owner explicitly selected Option `B` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY consume the following Owner-decided facts:

```text
Runtime Actual-state
→ partitioned by bounded runtime semantic responsibility

Each bounded runtime semantic assertion / partition
→ exactly one final Actual-state Owner

Different runtime semantic partitions
→ MAY have different Actual-state Owners

Multiple final Actual-state Owners for the same semantic assertion
→ PROHIBITED

System-level Runtime View
→ coordinated / derived projection
→ NOT universal factual authority by aggregation
```

At Project-architecture level, responsibility implications include:

```text
ns_runtime
→ owns actual-state facts genuinely originating from its accepted coordination responsibility,
  such as connection-management, runtime-routing, scheduling/dispatch coordination,
  and runtime-coordination facts where those facts are semantically defined as its own responsibility

ns_node
→ owns bounded local source facts genuinely originating from Terminal / Local Execution responsibility,
  including actual local execution attempts, locally observed execution state,
  local protected effects, local resource/device effects, and reconciliation-relevant local facts

ns_agent
→ owns bounded Agent-runtime facts genuinely originating from Agent execution/runtime responsibility,
  without gaining the semantic authority of capabilities, data, knowledge, or tools it consumes/invokes

ns_server / ns_web / other Product Component responsibilities
→ may own only runtime facts genuinely originating inside their accepted semantic responsibility;
  hosting, observing, persisting, presenting, aggregating, or receiving another component's facts does not transfer Actual-state Ownership
```

These statements establish Project-level ownership topology only. They do not define Runtime Roles, concrete fact schemas, message types, APIs, storage, lifecycle state machines, or process mappings.

## 7. Permanent Non-transfer Rules

```text
Communication Hub != Universal Runtime SoT
Scheduling / Dispatch != Universal Runtime Actual-state Ownership
Runtime Observation != Canonicalization automatically
System-level Aggregation != Universal Factual Authority
Local Execution != Broader Semantic Authority
Local Runtime Fact != Global Canonical Runtime State automatically
Local Cache / Database != Source of Truth automatically
Process / Service / Container Placement != Actual-state Ownership
Persistence Placement != Actual-state Ownership
UI Projection != Actual-state Ownership
Recovery / Reconnection != Authority Transfer
```

## 8. Distinction from Existing Authority Decisions

Runtime Actual-state Ownership is distinct from all of the following:

```text
Tenant Semantic Authority
Tenant Canonical SoT
IAM Semantic Authority
Policy Semantic Authority
Organization Semantic Authority / Organization factual SoT
Formal Artifact Acceptance Authority
Formal Execution Admission Authority
Automation Definition / Workflow Semantic Authority
AI Agent Definition / Semantic Authority
Business Application Definition / Platform Semantic Authority
Data / Knowledge / ETL Semantic Authority
Data / Knowledge factual SoT
```

A Product Component may hold one of those authorities and still not own runtime facts that originate in another component's bounded runtime responsibility.

## 9. Failure / Unknown / Temporal Obligations

Later authorized Runtime Responsibility Architecture and related Contracts MUST preserve explicit semantics for at least:

```text
fact origin
owner identity
observation vs owned fact
source revision where applicable
temporal applicability
fresh
stale
missing
unknown
indeterminate
conflicting
unreachable / disconnected
recovered
reconnected
reconciliation pending
reconciled
projection freshness
```

If a central projection has not yet observed a locally originated execution/effect fact, the local fact does not become nonexistent merely because aggregation is stale. Conversely, local origin does not make that fact the canonical owner of a broader semantic assertion that belongs to another partition.

## 10. Same-assertion Rule

A later architecture MUST be able to determine whether two apparently conflicting runtime observations describe:

```text
the same semantic assertion
or
different semantic perspectives / partitions
```

If they describe the same semantic assertion:

```text
exactly one final Actual-state Owner
→ REQUIRED
```

If they describe different perspectives, they MUST remain explicitly distinct rather than being silently collapsed into one state value.

## 11. Offline / Degraded Consequences

This decision preserves offline/degraded correctness without converting disconnection into authority escalation.

```text
ns_node offline local execution fact
→ remains provenance-bearing source/effect fact
→ does not gain Task / Workflow / Policy / Admission / Business Authority

ns_runtime unavailable or disconnected from a node
→ does not erase local actual facts
→ does not transfer its coordination authority to the node

central projection stale/unavailable
→ explicit unknown/stale condition
→ not permission to fabricate canonical state
```

Any material future offline fail-open/fail-closed, pre-authorization, grant validity, canonicalization, or conflict-winner policy remains separately MDE-governed where applicable.

## 12. Constraint Preservation

This decision preserves:

- `NSE-001` native Tenant semantic invariance;
- `NSE-004` offline core correctness and governance invariance;
- `NSE-005` Product Component semantic topology / Runtime non-conflation;
- `NSE-006` authority non-transfer through composition/coordination;
- `NSE-007` Definition / Artifact / Runtime governance-state separation;
- `NSE-008` local execution source/effect accountability without locality-based universal canonicalization;
- `NSE-009` representation independence;
- `NSE-011` source/provenance and bounded SoT preservation principles where runtime integrates external facts;
- `NSE-012` Shared Foundation authority neutrality;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 13. Explicit Non-implications

This decision does NOT establish:

```text
Runtime Role set
Product Component = Runtime Role
Process / Service / Container topology
Worker or scheduler topology
ns_runtime = universal Runtime SoT
ns_server = universal Runtime SoT
local executor = universal Runtime SoT
latest observation wins
latest timestamp wins
local wins
central wins
one database = one runtime semantic partition
one connection = one authority partition
one status field = complete runtime truth
system-level projection = final authority
```

It also does not select transport, schema, message, queue, broker, storage, database, cache, clock, heartbeat, synchronization, recovery, reconciliation, or deployment technology.

## 14. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- Cross-component Semantic Dependency Topology;
- later Five-component Internal Architecture Boundaries;
- later Runtime Responsibility Architecture;
- later offline/recovery/reconciliation architecture;
- later runtime Contracts and conformance design.

No later phase is authorized by this decision.

## 15. Revalidation Trigger

Revalidation is required if the Project Owner later changes one or more of:

- per-runtime-semantic-partition Actual-state ownership;
- the one-final-owner rule for the same runtime semantic assertion;
- `ns_node` source/effect accountability semantics;
- `ns_runtime`'s non-universal-SoT relationship;
- the fixed Product Component topology;
- offline/degraded governance invariance.

Changes in processes, services, containers, schedulers, workers, databases, caches, WebSocket handling, deployment topology, or runtime libraries do not by themselves revalidate this decision.

## 16. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Foundation Contract/Module/Provider Design, Implementation Planning, IWP, or coding.
