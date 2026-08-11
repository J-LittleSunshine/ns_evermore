# ns_evermore Current Required Read Set

## Authority Metadata

- **Document ID:** `NS-EVERMORE-CRRS-0001`
- **Version:** `0.0.1`
- **Status:** `CURRENT / GAC-EPOCH-0002`
- **Authority Level:** `GLOBAL_CONTINUITY_READ_SET`
- **Program:** `NGRP-001`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Acceptance Basis:** `NS-EVERMORE-Z0-GLOBAL-ACCEPTANCE-0001`

---

## 1. Purpose

This document defines the minimum sufficient Repository context with no semantic loss for recovering the project immediately after Z0 Global Acceptance.

## 2. Required Read Set — GAC-EPOCH-0002

Read in this order:

1. `docs/ns_evermore_genesis_constitution_0.0.1.md`
2. `docs/genesis/ns_evermore_genesis_source_manifest_0.0.1.md`
3. `docs/governance/ns_evermore_genesis_governance_framework_0.0.1.md`
4. `docs/ns_evermore_nse_constraints_index_0.0.1.md`
5. `docs/governance/decisions/ns_evermore_decision_registry_0.0.1.md`
6. `docs/governance/global_architecture/ns_evermore_global_architecture_continuation_protocol_0.0.1.md`
7. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z0_global_acceptance_0.0.1.md`
8. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
9. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
10. `docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md`
11. `docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md`

## 3. Historical Evidence Deep-read Rule

The following Z0 producing-session artifacts are accepted historical governance evidence but are not part of the default minimum read set after Global Acceptance:

```text
docs/session_prompts/ns_evermore_ngrp_001_phase_z0_genesis_bootstrap_session_prompt_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_phase_z0_genesis_bootstrap_review_0.0.1.md
docs/session_handoffs/ns_evermore_ngrp_001_phase_z0_genesis_bootstrap_handoff_0.0.1.md
```

Read them when investigating Z0 provenance, acceptance reconstruction, conflict, drift, or historical ambiguity.

Pre-Genesis repository artifacts remain non-normative unless a later authorized phase explicitly admits them.

## 4. Recovery Target

After reading the current set, a fresh Global Architecture Coordinator must recover without material ambiguity:

```text
Project identity
Accepted Genesis Constitution
Accepted root product constraints
Five fixed Product Components
Tenant / Organization non-collapse
Technical root facts
Current Constraint Baseline
Accepted Z0 Decisions
Current Global State Epoch
Current branch and Git coordinate
Last Globally Accepted Phase
Current Authorized Design Phase
Open MDE
Pending Owner Decisions
Blocking Items
Known Drift
Unique Next Legal Action
```

## 5. Current State Summary

```text
Current Global State Epoch
GAC-EPOCH-0002

Last Globally Accepted Phase
NGRP-001 Phase Z0 — Genesis Governance Bootstrap

Current Constraint Baseline
BOOTSTRAP ONLY
ACTIVE_NSE = NONE

Accepted Z0 Decisions
Z0-DAD-001 .. Z0-DAD-010

Current Authorized Design Phase
NONE

Current Session Authorization Prompt
NONE — current activity is Global Architecture Coordinator governance reassessment, not a bounded design session

Open MDE
0

Unpersisted Owner Decision
0

Blocking Item
0
```

## 6. Unique Next Legal Action

```text
Global Architecture Coordinator
→ reassess remaining material Architecture Constraint pressure against the accepted Genesis Constitution
→ determine one bounded next legal phase
→ persist explicit authorization before any Constraint Derivation session starts
```

Architecture Constraint Derivation is not yet authorized by this Read Set.
