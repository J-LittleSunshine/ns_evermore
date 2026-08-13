# ns_evermore Decision Registry — Current Revision

- **Version:** `0.0.9`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `0.0.8` as current working-tree registry

## 1. Registry Semantics

This is the current compact decision-classification index. Historical decisions and superseded registry revisions remain recoverable from Git history.

Current authority is resolved through the current Global Architecture State, Unified Governance, current Constraint Index, accepted Project Architecture and applicable Z3 Global Acceptance evidence.

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

Accepted Z2 Owner MDE
→ Z2-MDE-001..017
→ OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED
```

## 3. Decision Authority

Governed by `docs/governance/ns_evermore_governance_0.0.2.md`:

```text
Root Product / Constitutional Decision → Project Owner
MDE → Project Owner
Product-significant Capability Decision → Project Owner Capability Checkpoint
DAD → authorized Architecture / Design Session inside exact scope
GAC → classification / independent acceptance / phase authorization / continuity / drift
Implementation / Codex → no Architecture authority
```

If classification is uncertain for a material architecture matter: `DEFAULT → MDE`.

## 4. Accepted Z3 Batch 1 Capability Baseline

```text
docs/architecture_reviews/
ns_evermore_ngrp_001_phase_z3_batch_1_capability_discovery_candidate_0.0.1.md
→ GLOBAL_ACCEPTED / NORMATIVE Z3 UPSTREAM
```

Global Acceptance:
`docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_1_global_acceptance_0.0.1.md`

The accepted baseline covers `ns_server`, `ns_runtime`, `ns_node`, `ns_agent`, `ns_web`, System-level SDK/Development Surface and the Common Capability Candidate pressure inventory.

## 5. Accepted Z3 Owner Capability Baseline before Batch 2

The following 13 capability requirements remain normative and GAC-recognized:

```text
1. Agent → Node governed executable-work/task-intent delegation
2. ns_server bounded continuously available server-local long-running/time-triggered background work
3. Automation complete SDK/source + ns_web visual dual authoring
4. Native Agent complete dual authoring
5. Native Business Application complete dual authoring
6. Native Data/Knowledge/Foundational ETL complete dual authoring
7. Native general Multi-Agent composition
8. Native Multimodal Agent semantics
9. Governed HITL for Automation and Agent
10. Governed event-driven Automation triggering
11. Reusable Automation-to-Automation composition
12. Agent dynamic authoring of candidate Automation Definitions under normal Automation governance
13. ns_node attended + unattended local execution
```

Detailed evidence remains in the individual Z3 Batch 1 Owner capability decision files.

## 6. Accepted Z3 Batch 2 Interaction Experience Baseline

Accepted artifact:

```text
docs/architecture_reviews/
ns_evermore_ngrp_001_phase_z3_batch_2_interaction_experience_capability_discovery_candidate_0.0.1.md
→ GLOBAL_ACCEPTED / NORMATIVE Z3 INTERACTION-EXPERIENCE BASELINE
```

Global Acceptance:

`docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_2_global_acceptance_0.0.1.md`

The baseline covers End User, Operator/Admin, Developer/Delivery/Integrator and HITL interaction capability pressure, including long-running/async operations, Agent/Automation/HITL, offline/degraded/unknown, diagnostics/explainability, authoring, governance, operational awareness, discovery, accessibility/localization and cross-surface semantic consistency.

## 7. Accepted Z3 Batch 2 Owner Decisions

All decisions below are `OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED` through Z3 Batch 2 Global Acceptance.

### 7.1 Source / Visual Authoring Interoperability

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_2_source_visual_interoperability_owner_capability_decision_0.0.1.md`

```text
MDE → YES
Selected Option → B
Bidirectional semantic interoperability → REQUIRED
Silent semantic loss/destruction → PROHIBITED
Lossless representation round-trip → NOT REQUIRED
One mandatory physical representation → NOT REQUIRED
```

This is MDE-class because it creates a major externally observable compatibility/migration commitment across the four complete authoring domains.

### 7.2 Unified Governed Human Task Inbox

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_2_unified_human_task_inbox_owner_capability_decision_0.0.1.md`

```text
MDE → NO
Selected Option → B
Result → UNIFIED_GOVERNED_HUMAN_TASK_INBOX_REQUIRED
Human Task != Notification
Human Task != Policy / Artifact Acceptance / Execution Admission Authority
```

### 7.3 Governed Operation Intervention

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_2_governed_operation_intervention_owner_capability_decision_0.0.1.md`

```text
MDE → NO
Selected Option → B
Result → UNIFIED_GOVERNED_OPERATION_INTERVENTION_WITH_CAPABILITY_SPECIFIC_SUPPORT_REQUIRED
Cancel Requested != Cancelled
Retry Requested != Retry Started
Recovery Requested != Recovered
Reconnect != Reconciled
```

Universal reversibility/cancellation/retry/idempotency/checkpoint guarantees are not accepted.

### 7.4 Governed Pre-production Trial

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_2_governed_pre_production_trial_owner_capability_decision_0.0.1.md`

```text
MDE → NO
Selected Option → B
Result → GOVERNED_PRE_PRODUCTION_TRIAL_WITH_DOMAIN_APPROPRIATE_BOUNDED_MODES_REQUIRED
Applies → Business Application / Automation / Native Agent / Data-Knowledge-ETL
Trial Success != Artifact Acceptance / Production Admission / Production Success
Universal fully isolated simulation → NOT REQUIRED
```

### 7.5 Governed Notification + External Delivery

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_2_governed_notification_external_delivery_owner_capability_decision_0.0.1.md`

```text
MDE → YES
Selected Option → B + explicit Owner supplement
Unified governed Notification/Awareness → REQUIRED
Channel-neutral core semantics → REQUIRED
Pluggable external notification delivery → REQUIRED
Explicit target integration directions → Feishu / WeCom / SMS
Fixed mandatory omnichannel provider set → NOT REQUIRED
```

This is MDE-class because it creates a durable cross-domain compatibility/integration commitment with material migration/provider-channel implications. Provider APIs/adapters/credentials remain later design and no external provider becomes a semantic authority or core-correctness dependency.

### 7.6 Unified Governed Cross-domain Resource Discovery

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_2_unified_resource_discovery_owner_capability_decision_0.0.1.md`

```text
MDE → NO
Selected Option → B
Unified governed discovery → REQUIRED
Tenant-aware / Authorization-aware / Private-offline → REQUIRED
Discovery Index != Universal Resource SoT
Universal AI/Semantic Search → NOT IMPLIED
```

### 7.7 Internationalization / Localization

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_2_internationalization_localization_owner_capability_decision_0.0.1.md`

```text
MDE → NO
Selected Option → B
First-class internationalization + pluggable multi-language localization → REQUIRED
Stable machine semantics → LANGUAGE_NEUTRAL
Multiple locales → SUPPORTED
Exact initial language set → DEFERRED
Automatic arbitrary business-content translation → NOT IMPLIED
```

### 7.8 Accessibility Baseline

Evidence:
`docs/governance/decisions/ns_evermore_z3_batch_2_accessibility_owner_capability_decision_0.0.1.md`

```text
MDE → NO
Selected Option → B
First-class accessibility → REQUIRED
Accessible critical-workflow completion path → REQUIRED
Semantic interaction parity → REQUIRED
Visual/gesture parity → NOT REQUIRED
Pointer-only critical operation → PROHIBITED
Color-only critical meaning → PROHIBITED
```

## 8. Key Accepted Interaction Invariants

```text
Frontend/UI MUST NOT invent semantic truth
Projection != Authority / SoT
Request != outcome
Human Task != Notification
Desired != Applied != Observed
Validation != Trial != Artifact Acceptance != Production Admission
Current Definition != Historical Execution Context
Locale != Tenant != Principal != Timezone
Notification != current Runtime Actual-state
Discovery index != Universal Resource SoT
```

Cross-surface interaction semantics must preserve stable meaning across applicable Web, SDK/CLI and extension surfaces without requiring one physical representation.

## 9. Common Capability / Shared Foundation Boundary

The Batch 1 Common Capability inventory remains accepted only as discovery/classification/pressure evidence. Batch 2 interaction capabilities do not promote any candidate into Shared Foundation Architecture, Contract, Module or Provider.

```text
Reuse != Product Authority
Notification utility != Notification semantic authority automatically
Discovery/index utility != Universal Resource SoT
Human Task projection != Governance Authority
```

## 10. Open Decision State

```text
Open MDE → 0
Unpersisted Owner Decision → 0
Owner-reserved unresolved capability blocker → 0
```

## 11. Consumption Rule

Future Architecture/Design/Implementation sessions consume current Unified Governance, Global State, current Constraint Index, this Registry, accepted Project Architecture, accepted Z3 Batch 1 capability baseline and accepted Z3 Batch 2 Interaction Experience baseline.

No downstream session may infer Authority/SoT from UI placement, notification delivery, search/index placement, authoring surface, provider choice, runtime placement, storage, transport or implementation convenience.
