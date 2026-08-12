# ns_evermore Decision Registry — Current Revision

- **Version:** `0.0.5`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `0.0.4` as current working-tree registry

## 1. Registry Semantics

This is the current compact decision-classification index. Historical decisions and superseded registry revisions remain recoverable from Git history.

Current Architecture Constraint authority is defined by the current Constraint Index and Global Architecture State. Current Project Architecture authority is defined by the current Global Architecture State and applicable Global Acceptance evidence.

## 2. Root Inherited Facts

`ROOT-FACT-001..017` remain globally accepted and are consumed through the Genesis Constitution/current governance baseline.

Key current root facts include:

```text
ROOT-FACT-001  Five Product Components are fixed: ns_server, ns_runtime, ns_node, ns_agent, ns_web
ROOT-FACT-006  Native Multi-tenancy is mandatory
ROOT-FACT-007  Tenant != Organization
ROOT-FACT-008  Complex/extensible Organization is mandatory
ROOT-FACT-010  Shared Foundation is outside the five Product Components and is not a sixth Product Component
ROOT-FACT-011  Complete private/offline correctness is mandatory
ROOT-FACT-012  Stable cross-boundary contracts are language-neutral and versioned
ROOT-FACT-013  Definition / Artifact / Runtime are distinct governance states
ROOT-FACT-014  Source-level extension, customer secondary development, and re-delivery are product requirements
ROOT-FACT-015  Repository evidence is persistent project memory; chat/model memory is non-authoritative
ROOT-FACT-016  Independent Global Acceptance is mandatory
ROOT-FACT-017  Accepted design must be implementation-derivable before implementation planning
```

## 3. Historical DAD Context

`Z0-DAD-001..010` remain historical accepted evidence. Current governance implementation details are governed by Unified Governance/current Global State where they supersede historical mechanisms.

Project Architecture candidate `0.0.2` contains `Z2-DAD-001..026` as bounded-session architecture decisions inside the accepted Z2 Batch 1 scope. Their normative status follows the Z2 Batch 1 Global Acceptance evidence and current Global State.

## 4. Current Decision Authority Model

Authority is defined by:

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

## 5. Current Accepted Architecture Constraint Context

Current accepted Architecture Constraints:

```text
NSE-001..017
```

Current normative Constraint Index:

`docs/ns_evermore_nse_constraints_index_0.0.5.md`

## 6. Current Z2 Project Owner MDE Baseline

All following decisions are `OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED` and are normative inputs to the accepted Z2 Batch 1 Project Architecture:

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

Detailed A/B/C alternatives, rationale, consequences and revalidation triggers remain in the individual decision evidence files under `docs/governance/decisions/`.

## 7. Open Decision State

```text
Open MDE
0

Unpersisted Owner Decision
0

Owner-reserved unresolved decision
0
```

## 8. Consumption Rule

Future Architecture / Design / Implementation Planning / IWP / Codex sessions consume current Unified Governance, Global State, current Constraint Index, this Registry, and the current accepted Project Architecture rather than relying on prior chat context or superseded files.

No session may infer Architecture authority from directory structure, framework placement, provider/library choice, data placement, transport representation, runtime placement, UI state, extension origin, commercial state or implementation convenience.
