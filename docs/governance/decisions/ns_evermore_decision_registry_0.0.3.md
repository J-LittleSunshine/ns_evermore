# ns_evermore Decision Registry — Current Revision

- **Version:** `0.0.3`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `0.0.2` as current working-tree registry

## 1. Registry Semantics

This is the current decision-classification index. Historical decisions and superseded registry revisions remain recoverable from Git history.

Current Architecture Constraint authority is defined by the current Constraint Index and Global Architecture State; this Registry carries only compact decision-classification context.

## 2. Root Inherited Facts

```text
ROOT-FACT-001  Five Product Components are fixed: ns_server, ns_runtime, ns_node, ns_agent, ns_web
ROOT-FACT-002  Python-first delivery direction
ROOT-FACT-003  ns_server → Python + Django
ROOT-FACT-004  ns_runtime → Python + WebSocket-centered communication
ROOT-FACT-005  ns_web → Vue 3 + TypeScript
ROOT-FACT-006  Native Multi-tenancy is mandatory
ROOT-FACT-007  Tenant != Organization
ROOT-FACT-008  Complex/extensible Organization is mandatory
ROOT-FACT-009  Knowledge/Data Foundation is located inside ns_server
ROOT-FACT-010  Shared Foundation is outside the five Product Components and is not a sixth Product Component
ROOT-FACT-011  Complete private/offline delivery correctness is mandatory
ROOT-FACT-012  Stable cross-boundary contracts are language-neutral and versioned
ROOT-FACT-013  Definition / Artifact / Runtime are distinct governance states
ROOT-FACT-014  Source-level extension, customer secondary development, and re-delivery are product requirements
ROOT-FACT-015  Repository evidence is persistent project memory; chat/model memory is non-authoritative
ROOT-FACT-016  Independent Global Acceptance is mandatory
ROOT-FACT-017  Accepted design must be implementation-derivable before implementation planning
```

## 3. Accepted Z0 DADs

`Z0-DAD-001..010` remain historically accepted through Z0 Global Acceptance. Some original governance implementation choices have since been superseded by accepted Unified Governance and current Global State; historical DAD evidence remains valid as history but does not override current governance.

## 4. Current Decision Authority Model

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

Product-significant Component capability questions not already inherited/accepted require Project Owner review before Component Internal Design.

If classification is uncertain for a material architecture matter:

```text
DEFAULT → MDE
```

## 5. Current Accepted Architecture Constraint Context

```text
NSE-001  Native Tenant Semantic Invariance
NSE-002  Tenant / Organization Semantic Non-collapse
NSE-003  Organization Structural Plurality and Extensibility
NSE-004  Offline Core Correctness and Governance Invariance
NSE-005  Product Component Semantic Topology and Runtime Non-conflation
NSE-006  First-class Capability Domain Non-subordination and Authority Non-transfer
NSE-007  Definition, Artifact, and Runtime Governance State Separation
NSE-008  Local Execution Authority and Source-effect Accountability Separation
NSE-009  Stable Cross-boundary Contract Semantic Identity and Representation Independence
NSE-010  Extension and Re-delivery Governance Preservation and Authority Non-escalation
NSE-011  External Source-of-Truth Preservation under Bounded Enterprise Integration
NSE-012  Shared Foundation Contract Semantic Stability and Provider Replaceability
```

Current normative constraint index:

`docs/ns_evermore_nse_constraints_index_0.0.4.md`

## 6. Open Decision State

```text
Open MDE
0

Unpersisted Owner Decision
0

Owner-reserved unresolved decision
0
```

## 7. Consumption Rule

Future Architecture / Design / Implementation Planning / IWP / Codex sessions consume the current Unified Governance, Global State, and current Constraint Index rather than relying on obsolete standalone governance artifacts or prior chat context.

No session may use directory structure, framework placement, library choice, provider implementation, transport representation, data ingestion, extension origin, or code organization to bypass the accepted decision-authority model.
