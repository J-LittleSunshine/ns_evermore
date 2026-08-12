# ns_evermore Current Required Read Set

## Authority Metadata

- **Document ID:** `NS-EVERMORE-CRRS-0001`
- **Version:** `0.0.1`
- **Status:** `CURRENT / GAC-EPOCH-0005`
- **Authority Level:** `GLOBAL_CONTINUITY_READ_SET`
- **Program:** `NGRP-001`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Acceptance Basis:** `NS-EVERMORE-Z1-B1-GLOBAL-ACCEPTANCE-0001`

---

## 1. Purpose

This document defines the minimum sufficient Repository context with no semantic loss for the currently authorized Z1 Batch 2 Architecture Constraint Derivation session.

## 2. Required Read Set — GAC-EPOCH-0005

Read in this order:

1. `docs/ns_evermore_genesis_constitution_0.0.1.md`
2. `docs/genesis/ns_evermore_genesis_source_manifest_0.0.1.md`
3. `docs/governance/ns_evermore_genesis_governance_framework_0.0.1.md`
4. `docs/governance/decisions/ns_evermore_decision_registry_0.0.1.md`
5. `docs/governance/global_architecture/ns_evermore_global_architecture_continuation_protocol_0.0.1.md`
6. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z0_global_acceptance_0.0.1.md`
7. `docs/architecture_reviews/ns_evermore_post_z0_constraint_pressure_assessment_0.0.1.md`
8. `docs/ns_evermore_nse_constraints_index_0.0.2.md`
9. `docs/nse_constraints/ns_evermore_nse_001_0.0.1.md`
10. `docs/nse_constraints/ns_evermore_nse_002_0.0.1.md`
11. `docs/nse_constraints/ns_evermore_nse_003_0.0.1.md`
12. `docs/nse_constraints/ns_evermore_nse_004_0.0.1.md`
13. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z1_constraint_derivation_batch_1_global_acceptance_0.0.1.md`
14. `docs/architecture_reviews/ns_evermore_post_z1_batch_1_constraint_pressure_assessment_0.0.1.md`
15. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
16. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
17. `docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md`
18. `docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md`
19. `docs/session_prompts/ns_evermore_ngrp_001_phase_z1_constraint_derivation_batch_2_session_prompt_0.0.1.md`

## 3. Historical Deep-read Rule

Do not read pre-Genesis, superseded, or unrelated prior-session artifacts by default.

Expand only for:

```text
Reopen
Conflict
Historical Divergence
Evidence Ambiguity
Cross-phase Collision
Drift Investigation
Explicit Compatibility / Migration analysis
```

The current accepted Constraint Index is `0.0.2`; Index `0.0.1` is historical accepted Genesis bootstrap evidence rather than the current normative index.

## 4. Recovery Target

A fresh bounded Batch 2 session must recover without material ambiguity:

```text
Project identity
Accepted Genesis Constitution and Governance Framework
Accepted NSE = NSE-001..004
Current Constraint Index = 0.0.2
Current Global State Epoch = GAC-EPOCH-0005
Last Globally Accepted Phase = Z1 Batch 1
Current Authorized Phase = Z1 Batch 2
Authorization Scope = COMPONENT_CAPABILITY_EXECUTION_BOUNDARY_CONSTRAINTS
Open MDE
Pending Owner Decisions
Blocking Items
Known Drift
Explicit deferred pressure
Unique next legal action
```

## 5. Current State Summary

```text
Current Global State Epoch
GAC-EPOCH-0005

Last Globally Accepted Phase
NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 1

Current Constraint Baseline
NS-EVERMORE-NSE-INDEX-0001 / 0.0.2

Accepted NSE
NSE-001..004

Current Authorized Phase
NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 2

Authorization Scope
ARCHITECTURE_CONSTRAINT_DERIVATION_ONLY / BATCH_2 / COMPONENT_CAPABILITY_EXECUTION_BOUNDARY_CONSTRAINTS

Current Session Authorization Prompt
docs/session_prompts/ns_evermore_ngrp_001_phase_z1_constraint_derivation_batch_2_session_prompt_0.0.1.md

Open MDE
0

Unpersisted Owner Decision
0

Blocking Item
0

Remaining Material Constraint Pressure
PRESENT

Global Constraint Derivation
INCOMPLETE

Project Architecture Authorization
NONE
```

## 6. Unique Next Legal Action

```text
Start one bounded Z1 Batch 2 Architecture Constraint Derivation session under the exact Repository-backed authorization prompt.
```

The bounded session must stop at `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE` and return to the Global Architecture Coordinator. It may not self-accept, authorize a later batch, globally close Constraint Derivation, or begin Project Architecture.
