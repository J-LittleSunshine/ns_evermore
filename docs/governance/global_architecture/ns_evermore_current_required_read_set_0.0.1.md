# ns_evermore Current Required Read Set

## Authority Metadata

- **Document ID:** `NS-EVERMORE-CRRS-0001`
- **Version:** `0.0.1`
- **Status:** `CURRENT / GAC-EPOCH-0004`
- **Authority Level:** `GLOBAL_CONTINUITY_READ_SET`
- **Program:** `NGRP-001`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Acceptance Basis:** `NS-EVERMORE-Z1-B1-GLOBAL-ACCEPTANCE-0001`

---

## 1. Purpose

This document defines the minimum sufficient Repository context with no semantic loss for the post-Z1-Batch-1 Global Architecture Coordinator state.

## 2. Required Read Set — GAC-EPOCH-0004

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
14. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
15. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
16. `docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md`
17. `docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md`

## 3. Historical Deep-read Rule

Do not read pre-Genesis or superseded/historical artifacts by default.

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

`NS-EVERMORE-NSE-INDEX-0001 / 0.0.1` remains historical accepted Genesis bootstrap evidence and is not the current constraint index after Batch 1 acceptance.

## 4. Recovery Target

A fresh GAC session must recover without material ambiguity:

```text
Project identity
Accepted Genesis Constitution
Accepted Governance Framework
Current Accepted Constraint Index = 0.0.2
Accepted NSE = NSE-001..004
Current Global State Epoch = GAC-EPOCH-0004
Last Globally Accepted Phase = Z1 Batch 1
Current Authorized Design Phase = NONE
Open MDE
Pending Owner Decisions
Blocking Items
Known Drift
Remaining Material Constraint Pressure
Unique next legal governance action
```

## 5. Current State Summary

```text
Current Global State Epoch
GAC-EPOCH-0004

Last Globally Accepted Phase
NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 1

Current Constraint Baseline
NS-EVERMORE-NSE-INDEX-0001 / 0.0.2

Accepted NSE
NSE-001
NSE-002
NSE-003
NSE-004

Current Authorized Design Phase
NONE

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
Global Architecture Coordinator
→ perform post-Batch-1 Remaining Material Constraint Pressure Reassessment
→ select exactly one bounded next legal phase if warranted
→ persist a separate authorization transition
```

No later Z1 batch and no Project Architecture phase is authorized by this read set.
