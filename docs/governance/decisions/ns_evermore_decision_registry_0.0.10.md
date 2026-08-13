# ns_evermore Decision Registry — Current Revision

- **Version:** `0.0.10`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `0.0.9`

## 1. Current Authority Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Constraint Index → docs/ns_evermore_nse_constraints_index_0.0.5.md
Project Architecture → docs/ns_evermore_project_architecture_0.0.3.md / GLOBAL_ACCEPTED / NORMATIVE / CURRENT
Accepted Z2 DAD → Z2-DAD-001..041
Accepted Z2 Owner MDE → Z2-MDE-001..017
Unified Governance → docs/governance/ns_evermore_governance_0.0.2.md
```

## 2. Accepted Z3 Capability / Interaction Baselines

```text
Z3 Batch 1 Capability Baseline
→ docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_1_capability_discovery_candidate_0.0.1.md
→ GLOBAL_ACCEPTED / NORMATIVE

Z3 Batch 2 Interaction Experience Baseline
→ docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_2_interaction_experience_capability_discovery_candidate_0.0.1.md
→ GLOBAL_ACCEPTED / NORMATIVE

Z3 Capability Exhaustion / Internal-boundary Readiness
→ docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_capability_exhaustion_internal_boundary_readiness_assessment_0.0.1.md
→ SATISFIED
```

All previously accepted Z3 Owner capability decisions remain normative. Detailed evidence remains in the individual Batch 1/2 decision files and their Global Acceptance evidence.

## 3. Accepted Z3 Batch 3 Internal Architecture Boundary Baseline

```text
docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_five_component_internal_architecture_boundaries_candidate_0.0.1.md
→ GLOBAL_ACCEPTED / NORMATIVE
```

Global Acceptance:

`docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_global_acceptance_0.0.1.md`

Boundary inventory:

```text
ns_server → 13
ns_runtime → 4
ns_node → 4
ns_agent → 6
ns_web → 7
Total → 34
```

These are architecture-level responsibility/custody/semantic boundaries, not modules, packages, Apps, classes, services, processes, workers, containers, schemas or deployment units.

### `ns_server`

```text
S1 Tenant & Principal Identity Governance
S2 Organization Semantics & External Mapping Governance
S3 Policy & Authorization Governance
S4 Platform Trust & Security Governance
S5 Business Application Definition Lifecycle
S6 Automation Definition, Trigger & Composition Lifecycle
S7 Enterprise Data / Knowledge / Foundational ETL Governance
S8 Artifact Acceptance & Execution Admission Governance
S9 Managed Runtime Configuration Governance
S10 Server-local Background Work & Server Actual-state
S11 Unified Human Task Aggregation & Response Routing
S12 Governed Notification & External Delivery Lifecycle
S13 Cross-domain Resource Discovery Projection
```

### `ns_runtime`

```text
R1 Connection & Participant Presence Coordination
R2 Governed Routing, Scheduling & Dispatch Coordination
R3 Operation Continuation, Delegation & Intervention Coordination
R4 Coordination Recovery, Reconciliation & Diagnostics
```

### `ns_node`

```text
N1 Local Capability, Readiness & Applied Configuration
N2 Governed Local Execution
N3 Protected Local Effect & Source-fact Custody
N4 Offline Continuity, Recovery & Local Diagnostics
```

### `ns_agent`

```text
A1 Agent Definition & Evolution
A2 Agent Runtime Context, HITL & Actual-state
A3 Model / Provider Mediation & Multimodal Capability
A4 Tool & Knowledge Consumption
A5 Native Multi-Agent Composition
A6 Governed Cross-domain Delegation & Automation Participation
```

### `ns_web`

```text
W1 Governed Administration & Control Interaction
W2 Cross-domain Authoring & Semantic Interoperability
W3 Human Task Interaction
W4 Notification & Awareness Interaction
W5 Operational Observation, Trial, Intervention & Diagnostics
W6 Cross-domain Discovery & Governed Navigation
W7 Experience Semantics, Accessibility & Degraded Interaction
```

## 4. Accepted Z3 Batch 3 DAD

Evidence:
`docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_internal_boundary_dad_evidence_0.0.1.md`

```text
Z3-DAD-001..014 → GLOBAL_ACCEPTED
```

Subjects:

```text
001 five ns_server boundaries set
002 ns_runtime boundary set
003 ns_node boundary set
004 ns_agent boundary set
005 ns_web boundary set
006 Human Task responsibility allocation
007 Notification lifecycle partition allocation
008 Cross-domain Discovery projection allocation
009 Governed Trial responsibility split
010 Governed Operation Intervention responsibility split
011 Source↔Visual semantic-interoperability responsibility split
012 Configuration participation mapping
013 Runtime Actual-state / Source-effect refinement
014 System-level SDK / Development Surface relationship
```

## 5. Current Invariants

```text
Exactly five Product Components
Shared Foundation outside five
Boundary != Module / Runtime Role / Deployment Unit automatically
Tenant != Organization
Projection != Authority / SoT
Coordination != Execution Outcome
Dispatch != Admission
Human Task != Notification
Notification != underlying source/current state
Discovery Projection != Resource SoT
Trial != Production Acceptance / Admission
Desired != Applied != Observed
Configuration != Secret
Secret Reference != Secret Material
same bounded Actual-state assertion → exactly one final owner
```

## 6. Open Decision State

```text
Open MDE → 0
Unpersisted Owner Decision → 0
Owner-reserved unresolved decision → 0
Missing Product Capability → 0
```

## 7. Consumption Rule

Future sessions consume current Global State, Unified Governance, this Registry, current Constraint Index, accepted Project Architecture and all accepted Z3 baselines. No downstream session may infer Authority/SoT from UI, aggregation, runtime placement, storage, transport, provider, code-module placement or implementation convenience.
