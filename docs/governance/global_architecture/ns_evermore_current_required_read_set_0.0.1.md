# ns_evermore Current Required Read Set

## Authority Metadata

- **Document ID:** `NS-EVERMORE-CRRS-0001`
- **Version:** `0.0.1`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `CONTINUITY_READ_SET_CANDIDATE`
- **Program / Phase:** `NGRP-001 / Z0`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`

---

## 1. Purpose

This document defines the **minimum sufficient context with no semantic loss** for recovering the project at the Z0 completion boundary.

A fresh session MUST read these artifacts before acting on the current governance state.

## 2. Required Read Set — Z0 Completion Boundary

Read in this order:

1. `docs/ns_evermore_genesis_constitution_0.0.1.md`
2. `docs/genesis/ns_evermore_genesis_source_manifest_0.0.1.md`
3. `docs/governance/ns_evermore_genesis_governance_framework_0.0.1.md`
4. `docs/ns_evermore_nse_constraints_index_0.0.1.md`
5. `docs/governance/decisions/ns_evermore_decision_registry_0.0.1.md`
6. `docs/governance/global_architecture/ns_evermore_global_architecture_continuation_protocol_0.0.1.md`
7. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
8. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
9. `docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md`
10. `docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md`
11. `docs/governance/standards/ns_evermore_implementation_governance_standard_0.0.1.md`
12. `docs/session_prompts/ns_evermore_ngrp_001_phase_z0_genesis_bootstrap_session_prompt_0.0.1.md`
13. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z0_genesis_bootstrap_review_0.0.1.md`
14. `docs/session_handoffs/ns_evermore_ngrp_001_phase_z0_genesis_bootstrap_handoff_0.0.1.md`

## 3. Historical Deep-read Rule

Do not read all repository history by default.

Expand beyond this read set only for:

```text
Reopen
Conflict
Historical Divergence
Evidence Ambiguity
Cross-phase Collision
Compatibility / Migration investigation explicitly requiring history
```

Pre-Genesis artifacts remain non-normative unless explicitly admitted.

## 4. Recovery Target

After reading the set, a fresh Global Architecture Coordinator must be able to state without material ambiguity:

```text
Project identity
Root product constraints
Five fixed Product Components
Tenant / Organization non-collapse
Technical root defaults
Current constraint baseline
Current decision registry
Current program phase
Current state epoch
Current branch and verified Git coordinate
Last globally accepted phase
Current authorization scope
Open MDE
Pending Owner decisions
Blocking items
Known drift
Candidate vs normative status
Unique next legal action
```

## 5. Current Unique Next Legal Action

At Z0 bounded-session completion:

```text
Global Architecture Coordinator
→ recover using GACP-001
→ independently review Z0 evidence
→ issue GLOBAL_ACCEPT / CORRECTION_REQUIRED / REJECT
```

Architecture Constraint Derivation is not authorized by this read set.