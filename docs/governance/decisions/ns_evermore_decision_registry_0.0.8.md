# ns_evermore Decision Registry — Current Revision

- **Version:** `0.0.8`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `0.0.7` as current working-tree registry

## 1. Registry Semantics

This is the current compact decision-classification index. Historical decisions and superseded registry revisions remain recoverable from Git history.

Current Architecture Constraint authority is defined by the current Constraint Index and Global Architecture State. Current Project Architecture authority is defined by the current Global Architecture State and applicable Global Acceptance evidence. Accepted Product Component capability scope is additionally constrained by the accepted Z3 Batch 1 capability baseline and persisted Project Owner capability decisions.

## 2. Root / Constraint / Project Architecture Baseline

```text
ROOT-FACT-001..017
→ accepted through Genesis Constitution

NSE-001..017
→ GLOBAL_ACCEPTED / NORMATIVE

Current Constraint Index
→ docs/ns_evermore_nse_constraints_index_0.0.5.md

Current Project Architecture
→ docs/ns_evermore_project_architecture_0.0.3.md
→ GLOBAL_ACCEPTED / NORMATIVE / CURRENT

Accepted Project Architecture DAD
→ Z2-DAD-001..041

Accepted Owner MDE
→ Z2-MDE-001..017
→ OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED
```

## 3. Decision Authority Model

Current authority is defined by:

`docs/governance/ns_evermore_governance_0.0.2.md`

```text
Root Product / Constitutional Decision → Project Owner
MDE → Project Owner
Product-significant Capability Decision → Project Owner Capability Checkpoint
DAD → authorized Architecture / Design Session inside exact scope
GAC → classification / escalation / independent acceptance / phase authorization / continuity / drift
Implementation / Codex → no Architecture authority
```

If classification is uncertain for a material architecture matter:

```text
DEFAULT → MDE
```

## 4. Accepted Z3 Batch 1 Capability Baseline

Current accepted capability baseline:

`docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_1_capability_discovery_candidate_0.0.1.md`

Status through Global Acceptance:

```text
GLOBAL_ACCEPTED
NORMATIVE Z3 CAPABILITY BASELINE
CURRENT UPSTREAM FOR LATER Z3 WORK
```

Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_1_global_acceptance_0.0.1.md`

The baseline establishes capability inventories/classification for:

```text
ns_server
ns_runtime
ns_node
ns_agent
ns_web
System-level SDK / Development Surface
Cross-component Common Capability Candidate Inventory
```

It does not establish Five-component Internal Architecture Boundary decomposition.

## 5. Accepted Pre-Batch Z3 Owner Capability Requirements

All following are:

```text
OWNER_CAPABILITY_DECIDED
PERSISTED
GAC_RECOGNIZED
NORMATIVE CAPABILITY INPUT
```

### 5.1 Agent → Node governed delegation

```text
ns_agent
→ MUST support delegation of applicable executable work / task intent to ns_node

ns_node
→ MUST support governed receipt/execution inside accepted local-execution responsibility
```

No Automation/Policy/Artifact/Admission/Agent/local-effect authority transfer is implied.

### 5.2 ns_server server-local background work

```text
ns_server
→ MUST provide bounded continuously available server-local background work capability
→ long-running work belonging to ns_server responsibility
→ time-triggered / scheduled work belonging to ns_server responsibility
```

Concrete process pool / worker / queue / scheduler topology remains later design. This capability does not replace `ns_runtime` cross-component scheduling/dispatch responsibility.

### 5.3 Automation complete dual authoring

```text
Automation
→ complete System-level SDK/source authoring REQUIRED
→ complete ns_web visual drag-and-drop authoring REQUIRED
→ both converge on same ns_server-owned Automation semantic domain
```

## 6. Accepted Z3 Batch 1 Owner Capability Decisions

All following decisions are:

```text
OWNER_CAPABILITY_DECIDED
PERSISTED
GAC_RECOGNIZED THROUGH Z3 BATCH 1 GLOBAL ACCEPTANCE
NORMATIVE CAPABILITY INPUT
```

### 6.1 Native Agent complete dual authoring

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_agent_dual_authoring_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Result → COMPLETE_DUAL_AUTHORING_REQUIRED
Source/SDK + ns_web Visual
Agent Semantic Authority / Canonical Definition SoT → ns_agent / unchanged
```

### 6.2 Native Business Application complete dual authoring

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_business_application_dual_authoring_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Result → COMPLETE_DUAL_AUTHORING_REQUIRED
Source/SDK + ns_web Visual Builder
Business Application Semantic Authority / Canonical Definition SoT → ns_server / unchanged
```

### 6.3 Native Data / Knowledge / Foundational ETL complete dual authoring

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_data_etl_dual_authoring_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Result → COMPLETE_DUAL_AUTHORING_REQUIRED
Source/SDK + ns_web Visual
Data/Knowledge/ETL Semantic Authority → ns_server / unchanged
Bounded factual SoT topology → unchanged
```

### 6.4 Native general Multi-Agent composition

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_multi_agent_composition_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Result → Native general Multi-Agent composition REQUIRED
Agent Semantic Authority / Definition SoT → ns_agent / unchanged
```

### 6.5 Native Multimodal Agent semantics

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_agent_multimodal_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Result → Native Multimodal Agent semantics REQUIRED
Provider capability != Agent Semantic Authority
```

### 6.6 Governed Human-in-the-loop

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_human_in_the_loop_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Automation governed HITL → REQUIRED
Agent governed HITL → REQUIRED
Human action != Policy / Artifact Acceptance / Execution Admission Authority
```

### 6.7 Governed event-driven Automation triggering

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_automation_event_trigger_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Native event-driven Automation trigger capability → REQUIRED
Event occurrence != Execution Admission
Event transport != Automation Authority
```

### 6.8 Reusable Automation-to-Automation composition

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_automation_reusable_composition_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Result → REUSABLE_AUTOMATION_COMPOSITION_REQUIRED
Composition != Artifact / Admission bypass
```

### 6.9 Agent dynamic candidate Automation authoring

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_agent_dynamic_automation_authoring_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Agent may author candidate Automation Definition → REQUIRED
Candidate must enter normal Automation governance
No Ephemeral Automation class
Agent != Automation Authority / Definition SoT / Artifact Acceptance / Execution Admission Authority
```

### 6.10 ns_node attended + unattended execution

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_1_node_attended_unattended_execution_owner_capability_decision_0.0.1.md`

```text
Selected Option → B
Attended Execution → FIRST_CLASS_REQUIRED
Unattended Execution → FIRST_CLASS_REQUIRED
Combined → ATTENDED_AND_UNATTENDED_LOCAL_EXECUTION_REQUIRED
```

## 7. Common Capability Candidate Baseline

Z3 Batch 1 identifies reusable/common pressure but does **not** accept Shared Foundation architecture or modules.

Current status:

```text
Common Capability Inventory
→ GLOBAL_ACCEPTED AS DISCOVERY / CLASSIFICATION / PRESSURE BASELINE ONLY
```

Later Shared Foundation Architecture must independently evaluate candidates such as configuration loading, logging/diagnostics, telemetry, temporal primitives, serialization, crypto/secret-reference primitives, event/notification utilities, health/lifecycle reporting, operation/correlation context, compatibility/conformance support, Tenant/Principal context carriers and error/unknown status primitives.

Permanent rules:

```text
Reuse != Product Authority
Common Code != Shared Foundation automatically
Shared Utility != Shared Semantic Ownership
Generic Scheduler != Common Semantic Authority
Generic Workflow Engine != Common Semantic Authority
Generic IAM / Policy / Trust Authority != Foundation Authority
```

## 8. Open Decision State

```text
Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Owner-reserved unresolved capability blocker
→ 0
```

## 9. Current Z3 Sequencing Intent

Subject to independent GAC authorization for each transition:

```text
Z3 Batch 1
→ GLOBAL_ACCEPTED
→ Five-component + Common Capability Baseline established

Planned Z3 Batch 2
→ User / Operator / Developer Interaction Experience Capability Discovery
→ Interaction-state / feedback / async-operation / HITL / offline-degraded / authoring / governance / operational experience pressure
→ Owner Capability Checkpoint for material new interaction capabilities

Planned Z3 Batch 3
→ Five-component Internal Architecture Boundary Synthesis
```

Planning intent is not authorization. Current Global State controls the active Batch.

## 10. Consumption Rule

Future Architecture / Design / Implementation Planning / IWP / Codex sessions consume current Unified Governance, Global State, current Constraint Index, this Registry, current accepted Project Architecture and accepted Z3 capability baseline rather than prior chat context.

No session may infer Architecture authority from directory structure, framework/provider/library choice, data placement, transport representation, runtime placement, UI state, extension origin or implementation convenience.
