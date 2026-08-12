# ns_evermore Decision Registry — Current Revision

- **Version:** `0.0.6`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `0.0.5` as current working-tree registry

## 1. Registry Semantics

This is the current compact decision-classification index. Historical decisions and superseded registry revisions remain recoverable from Git history.

Current Architecture Constraint authority is defined by the current Constraint Index and Global Architecture State. Current Project Architecture authority is defined by the current Global Architecture State and applicable Global Acceptance evidence.

## 2. Root / Constraint Baseline

```text
ROOT-FACT-001..017
→ accepted through the Genesis Constitution

NSE-001..017
→ GLOBAL_ACCEPTED / NORMATIVE

Current Constraint Index
→ docs/ns_evermore_nse_constraints_index_0.0.5.md
```

## 3. Current Decision Authority Model

Current authority is defined by:

`docs/governance/ns_evermore_governance_0.0.2.md`

```text
Root Product / Constitutional Decision → Project Owner
MDE → Project Owner
DAD → authorized Architecture / Design Session
Implementation Choice → authorized downstream implementation authority inside Accepted Design freedom
GAC → classification / escalation / independent acceptance / phase authorization / continuity / drift
Codex → no Architecture authority
```

If classification is uncertain for a material architecture matter:

```text
DEFAULT → MDE
```

## 4. Current Accepted Project Architecture

```text
Path
→ docs/ns_evermore_project_architecture_0.0.3.md

Status
→ GLOBAL_ACCEPTED / NORMATIVE / CURRENT

Accepted through
→ NGRP-001 Phase Z2 / Project Architecture Synthesis / Batch 2 Global Acceptance
```

Project Architecture `0.0.3` cumulatively contains the accepted Batch 1 and Batch 2 Project Architecture DAD baseline.

## 5. Accepted Project Architecture DAD Baseline

Historical/accepted Project Architecture decisions:

```text
Z2-DAD-001..026
→ accepted through Z2 Batch 1 Global Acceptance

Z2-DAD-027 — Lifecycle-state separation and evidence non-escalation
Z2-DAD-028 — No implicit temporal winner; historical interpretation is context-bound
Z2-DAD-029 — Unknown / Indeterminate / Failure conditions are first-class
Z2-DAD-030 — Principal contexts and identity evidence remain distinct
Z2-DAD-031 — Authentication / IAM / Policy / Trust / evidence / enforcement separation
Z2-DAD-032 — Security / Trust boundary crossing does not transfer trust automatically
Z2-DAD-033 — Data use/storage/derivation/export does not transfer semantic ownership
Z2-DAD-034 — Secret material remains separate from Configuration and Foundation Trust Authority
Z2-DAD-035 — Recovery/Reconciliation preserves authority and performs evidence handoff
Z2-DAD-036 — Offline continuity is governed evidence consumption, not governance bypass
Z2-DAD-037 — Semantic compatibility precedes representation compatibility
Z2-DAD-038 — Migration completion is semantic, not mere data/representation copy
Z2-DAD-039 — Downstream architecture/design must prove Project Architecture conformance
Z2-DAD-040 — Material changes trigger explicit revalidation authority
Z2-DAD-041 — Project-level Semantic Resolution Matrix closure is distinct from mechanism design
→ accepted through Z2 Batch 2 Global Acceptance
```

These DADs are normative only inside the accepted Project Architecture scope and do not authorize downstream phases.

## 6. Current Z2 Project Owner MDE Baseline

All following decisions remain `OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED`:

```text
Z2-MDE-001  Tenant Semantic Authority → ns_server
Z2-MDE-002  Tenant Canonical SoT → ns_server
Z2-MDE-003  Native IAM Semantic Authority → ns_server
Z2-MDE-004  Unified Policy Semantic Authority → ns_server
Z2-MDE-005  Native Organization Semantic Authority → ns_server
Z2-MDE-006  Organization factual SoT → governed per bounded Organization semantic partition; exactly one final SoT per same assertion
Z2-MDE-007  Formal Artifact Acceptance Authority → ns_server
Z2-MDE-008  Formal Execution Admission Authority → ns_server
Z2-MDE-009  Automation Definition / Workflow Semantic Authority → ns_server
Z2-MDE-010  AI Agent Definition / Semantic Authority → ns_agent
Z2-MDE-011  Native Business Application Definition / Platform Semantic Authority → ns_server
Z2-MDE-012  Native Enterprise Data / Knowledge / Foundational ETL Semantic Authority → ns_server
Z2-MDE-013  Data / Knowledge factual SoT → governed per bounded semantic partition; exactly one final SoT per same assertion
Z2-MDE-014  Runtime Actual-state Ownership → governed per bounded runtime semantic partition; exactly one final owner per same assertion
Z2-MDE-015  Platform Security / Trust Semantic Authority → ns_server
Z2-MDE-016  Configuration topology → local bootstrap + authority-neutral shared loader + centrally managed desired state in ns_server; item semantics follow capability owner; applied state follows runtime actual-state owner
Z2-MDE-017  Native Product Definition canonical SoT → Business App ns_server / Automation ns_server / AI Agent ns_agent
```

Detailed alternatives, rationale, consequences and revalidation triggers remain in the individual decision evidence files.

## 7. Current Project-level Semantic Closure Context

Accepted Project Architecture `0.0.3` establishes Project-level closure for all 26 Unified Governance semantic dimensions, including lifecycle/temporal/failure semantics, Principal/Auth/Policy/Trust separation, Data/Privacy/Secret boundaries, recovery/reconciliation/offline behavior, compatibility/evolution/migration/conformance/revalidation, and named downstream deferrals.

Concrete downstream mechanisms remain subject to explicit later authorization and their own DAD/MDE classification.

## 8. Open Decision State

```text
Open MDE
0

Unpersisted Owner Decision
0

Owner-reserved unresolved decision
0
```

## 9. Owner Capability Checkpoint Reminder

Before any Product Component enters Component Internal Design:

```text
Component Responsibility Boundary
→ Component Capability Inventory
→ OWNER_DECISION_REQUIRED items return to Project Owner
→ Accepted Component Capability Baseline
→ Component Internal Architecture
```

Capabilities already required by Constitution/accepted Project Architecture are `INHERITED_REQUIRED` and are not re-voted.

## 10. Consumption Rule

Future Architecture / Design / Implementation Planning / IWP / Codex sessions consume current Unified Governance, Global State, current Constraint Index, this Registry, and the current accepted Project Architecture rather than relying on prior chat context or superseded files.

No session may infer Architecture authority from directory structure, framework placement, provider/library choice, data placement, transport representation, runtime placement, UI state, extension origin, commercial state or implementation convenience.
