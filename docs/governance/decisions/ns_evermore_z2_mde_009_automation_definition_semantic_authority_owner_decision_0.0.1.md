# NGRP-001 Z2 MDE-009 — Automation Definition / Workflow Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-009`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Immediate Pre-decision HEAD:** `4b859cca9a648a35f63cb26656fbbb3733683841`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; persisted `Z2-MDE-001..008`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final **Automation Definition / Workflow Semantic Authority** for `ns_evermore`?

This decision concerns the semantic authority that defines the authoritative meaning, revision semantics, lifecycle meaning, and formal interpretation of Automation / Workflow / Orchestration definitions. It does not select a DSL, schema, package format, database, API, orchestration engine, scheduler, worker, Runtime Role, module decomposition, or process topology.

## 2. Classification

```text
Classification
MDE

Reason
Major cross-component Semantic Ownership is Project-Owner-reserved under Unified Governance.
Automation is a constitutionally first-class capability domain spanning ns_web construction, ns_runtime coordination/scheduling/dispatch, and ns_node execution. Accepted NSE-006 requires first-class-domain non-subordination and explicit authority allocation. NSE-008 expressly prohibits deriving Task Definition Authority or Workflow Semantic Authority from ns_node execution locality.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` owns Automation Definition / Workflow Semantic Authority

`ns_server` owns final native Automation / Workflow semantic authority. `ns_web` constructs and manages through UI surfaces, `ns_runtime` schedules/routes/dispatches/coordinates, and `ns_node` executes and produces local source/effect facts. None of those responsibilities gains Automation Definition Authority by editing, transporting, scheduling, dispatching, hosting, caching, or executing.

### B — `ns_runtime` owns Automation Definition / Workflow Semantic Authority

`ns_runtime` owns both Automation/Workflow semantics and runtime scheduling/dispatch/coordination. This would materially couple Automation definition semantics to runtime coordination architecture.

### C — `ns_node` owns Automation Definition / Workflow Semantic Authority

`ns_node` owns Automation/Workflow semantics together with local execution responsibility. This would materially couple semantic definition authority to executor locality and node capability variation.

## 4. Recommendation Presented

`A — ns_server owns Automation Definition / Workflow Semantic Authority`.

Rationale: this establishes a stable control-plane semantic owner while preserving strict separation among construction UI, semantic definition, artifact acceptance, execution admission, runtime coordination, and local execution. It keeps Automation `FIRST_CLASS / PARALLEL / NON_SUBORDINATE`; placement in `ns_server` does not subordinate Automation to Business Application Construction / Runtime.

## 5. Project Owner Decision

```text
Selected Option
A

Automation Definition / Workflow Semantic Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY now consume:

```text
ns_server
→ owns native Automation Definition / Workflow Semantic Authority

ns_web
→ owns human-facing Automation construction / editing / management participation
→ does not gain Automation Semantic Authority through UI authoring or browser state

ns_runtime
→ owns applicable runtime coordination / scheduling / routing / dispatch participation
→ does not gain Automation Definition Authority through scheduling, routing, dispatch, transport, or observation

ns_node
→ owns applicable local / terminal Automation execution participation and local source/effect fact production
→ does not gain Task Definition Authority or Workflow Semantic Authority through execution locality

ns_agent
→ may participate in composed Automation through Agent/tool execution where later architecture permits
→ does not gain Automation Definition Authority by invocation or execution

Shared Foundation
→ may later mediate reusable technical capabilities
→ does not gain Automation semantic ownership by mediation or provider placement
```

## 7. First-class Capability Non-subordination

This decision MUST preserve:

```text
Business Application Construction / Runtime
Automation Construction / Execution
AI Agent Runtime / Tooling
Enterprise Data / Knowledge / foundational ETL
→ FIRST_CLASS / PARALLEL / NON_SUBORDINATE
```

The fact that Automation Definition Authority is placed in `ns_server` MUST NOT be interpreted as:

```text
Automation Domain = Business Application Domain
Automation subordinate to Business Application
ns_server = one universal semantic domain
same Product Component placement = same semantic ownership
```

Automation remains its own first-class capability domain with explicit semantic identity and downstream design obligations.

## 8. Governance-state Separation

This decision preserves the following distinctions:

```text
Automation Definition / Workflow Semantics
!= Domain Semantic Certification automatically
!= Accepted Artifact
!= Formal Execution Admission
!= Scheduling / Dispatch
!= Runtime Execution Attempt
!= Local Protected Effect
```

Persisted prior decisions remain controlling where applicable:

```text
Formal Artifact Acceptance Authority
→ ns_server       # Z2-MDE-007

Formal Execution Admission Authority
→ ns_server       # Z2-MDE-008

Automation Scheduling / Dispatch / Runtime Coordination
→ ns_runtime responsibility boundary

Local / Terminal Automation Execution
→ ns_node responsibility boundary
```

Same component placement for several governance responsibilities does not collapse their semantic meaning.

## 9. Explicit Non-implications

This decision does not establish:

```text
Automation Definition SoT persistence topology
Automation DSL / schema / serialization
Automation package/artifact format
Automation database
Automation API / Contract
Automation scheduler implementation
Runtime Role set
worker/process/service/container topology
ns_server = Automation runtime executor automatically
ns_server = universal product authority
Automation Authority = Policy Authority
Automation Authority = Artifact Acceptance Authority
Automation Authority = Execution Admission Authority
Automation Authority = Business Application Authority
```

Any material downstream choice in those categories remains subject to the later authorized phase and Unified Governance.

## 10. Constraint Preservation

This decision preserves:

- `NSE-005` Product Component semantic topology / Runtime non-conflation;
- `NSE-006` first-class capability non-subordination and authority non-transfer;
- `NSE-007` Definition / Artifact / Runtime governance-state separation;
- `NSE-008` local execution authority and source-effect accountability separation;
- `NSE-009` stable cross-boundary semantic identity before representation;
- `NSE-010` extension / re-delivery authority non-escalation;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 11. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Automation first-class capability placement section;
- the five-component responsibility boundary sections;
- the cross-component semantic dependency topology;
- the Responsibility / Authority / SoT Matrix;
- later Component Internal Architecture and Runtime Responsibility Architecture, without authorizing those phases.

## 12. Revalidation Trigger

Revalidate if the Project Owner later changes Automation Definition / Workflow Semantic Authority away from `ns_server`, changes Automation from a first-class capability domain, changes the fixed five Product Component topology, or explicitly couples Automation semantic authority to runtime/executor authority.

Changes in scheduler, worker, orchestration engine, Automation DSL, persistence, package format, transport, process/service/container topology, or UI framework do not by themselves revalidate this decision.

## 13. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
