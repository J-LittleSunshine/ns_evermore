# ns_evermore Current Required Read Set

## Authority Metadata

- **Document ID:** `NS-EVERMORE-CRRS-0001`
- **Version:** `0.0.1`
- **Status:** `CURRENT / GAC-EPOCH-0003`
- **Authority Level:** `GLOBAL_CONTINUITY_READ_SET`
- **Program:** `NGRP-001`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Acceptance Basis:** `NS-EVERMORE-Z0-GLOBAL-ACCEPTANCE-0001`

---

## 1. Purpose

This document defines the minimum sufficient Repository context with no semantic loss for recovering the currently authorized Z1 Batch 1 Architecture Constraint Derivation session.

## 2. Required Read Set — GAC-EPOCH-0003

Read in this order:

1. `docs/ns_evermore_genesis_constitution_0.0.1.md`
2. `docs/genesis/ns_evermore_genesis_source_manifest_0.0.1.md`
3. `docs/governance/ns_evermore_genesis_governance_framework_0.0.1.md`
4. `docs/ns_evermore_nse_constraints_index_0.0.1.md`
5. `docs/governance/decisions/ns_evermore_decision_registry_0.0.1.md`
6. `docs/governance/global_architecture/ns_evermore_global_architecture_continuation_protocol_0.0.1.md`
7. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z0_global_acceptance_0.0.1.md`
8. `docs/architecture_reviews/ns_evermore_post_z0_constraint_pressure_assessment_0.0.1.md`
9. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
10. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
11. `docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md`
12. `docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md`
13. `docs/session_prompts/ns_evermore_ngrp_001_phase_z1_constraint_derivation_batch_1_session_prompt_0.0.1.md`

## 3. Historical Deep-read Rule

Do not read all pre-Genesis or prior-session artifacts by default.

Expand into historical evidence only for:

```text
Reopen
Conflict
Historical Divergence
Evidence Ambiguity
Cross-phase Collision
Drift Investigation
Explicit Compatibility / Migration analysis
```

Pre-Genesis repository artifacts remain non-normative unless explicitly admitted under accepted provenance governance.

## 4. Recovery Target

A fresh bounded Z1 Batch 1 session must recover without material ambiguity:

```text
Project identity
Accepted Genesis Constitution
Accepted Governance Framework
Five fixed Product Components
Tenant / Organization root non-collapse
Technical root facts
Current Constraint Baseline = BOOTSTRAP / ACTIVE_NSE NONE
Accepted Z0 Decisions
Current Global State Epoch = GAC-EPOCH-0003
Last Globally Accepted Phase = Z0
Current Authorized Phase = Z1 / Batch 1
Authorization Scope = TENANT_ORGANIZATION_OFFLINE_CORE_CONSTRAINTS
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
GAC-EPOCH-0003

Last Globally Accepted Phase
NGRP-001 Phase Z0 — Genesis Governance Bootstrap

Current Constraint Baseline
BOOTSTRAP ONLY
ACTIVE_NSE = NONE

Current Authorized Phase
NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 1

Authorization Scope
ARCHITECTURE_CONSTRAINT_DERIVATION_ONLY / BATCH_1 / TENANT_ORGANIZATION_OFFLINE_CORE_CONSTRAINTS

Current Session Authorization Prompt
docs/session_prompts/ns_evermore_ngrp_001_phase_z1_constraint_derivation_batch_1_session_prompt_0.0.1.md

Open MDE
0

Unpersisted Owner Decision
0

Blocking Item
0
```

## 6. Unique Next Legal Action

```text
Start one bounded Z1 Batch 1 Architecture Constraint Derivation session under the current Repository-backed authorization prompt.
```

The bounded session may derive only the authorized constraint cluster and must stop at `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`. It may not self-accept, authorize a later batch, globally close Constraint Derivation, or begin Project Architecture.
