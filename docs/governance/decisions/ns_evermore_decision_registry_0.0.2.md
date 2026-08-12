# ns_evermore Decision Registry — Current Revision

## Authority Metadata

- **Document ID:** `NS-EVERMORE-DECISION-REGISTRY-0001`
- **Version:** `0.0.2`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Authority Level:** `DECISION_REGISTRY_CURRENT`
- **Program:** `NGRP-001`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `NS-EVERMORE-DECISION-REGISTRY-0001 / 0.0.1` as current registry only
- **Superseded By:** `NONE`
- **Upstream:** accepted Genesis baseline plus `NS-EVERMORE-DECISION-AUTHORITY-MODEL-0001`

---

## 1. Registry Semantics

This file is the current decision index. Historical decision evidence remains authoritative at its original immutable coordinates.

Superseding the prior registry as **current index** does not invalidate or rewrite the historical Z0 registry evidence.

## 2. Root Inherited Facts

The following remain globally accepted and non-votable unless the Project Owner explicitly changes the constitutional baseline:

```text
ROOT-FACT-001  Five Product Components are fixed: ns_server, ns_runtime, ns_node, ns_agent, ns_web
ROOT-FACT-002  Python-first delivery direction
ROOT-FACT-003  Django is the root server framework fact for ns_server
ROOT-FACT-004  WebSocket-centered communication is a root fact for ns_runtime
ROOT-FACT-005  Vue 3 + TypeScript is the root fact for ns_web
ROOT-FACT-006  Native Multi-tenancy is mandatory
ROOT-FACT-007  Tenant != Organization
ROOT-FACT-008  Complex/extensible Organization architecture is mandatory
ROOT-FACT-009  Knowledge/Data Foundation is located inside ns_server
ROOT-FACT-010  Shared Foundation exists outside the five Product Components and is not a sixth Product Component
ROOT-FACT-011  Complete private/offline delivery correctness is mandatory
ROOT-FACT-012  Stable cross-boundary contracts are language-neutral and versioned
ROOT-FACT-013  Definition / Artifact / Runtime are distinct governance states
ROOT-FACT-014  Source-level extension, customer secondary development, and re-delivery are product requirements
ROOT-FACT-015  Repository evidence is persistent project memory; chat/model memory is non-authoritative
ROOT-FACT-016  Independent Global Acceptance is mandatory
ROOT-FACT-017  Accepted design must be implementation-derivable before implementation planning
```

## 3. Accepted Z0 DADs

```text
Z0-DAD-001  Governance document hierarchy
Z0-DAD-002  Governance version format
Z0-DAD-003  Stable governance namespaces
Z0-DAD-004  Current-state versus historical-ledger split
Z0-DAD-005  Explicit Current Required Read Set artifact
Z0-DAD-006  Session authorization and handoff as durable artifacts
Z0-DAD-007  Constraint index starts empty
Z0-DAD-008  Working-state reset model
Z0-DAD-009  Implementation governance before implementation planning
Z0-DAD-010  Pre-Genesis history is non-normative by default
```

All remain `GLOBAL_ACCEPTED` through Z0 Global Acceptance evidence.

## 4. Project Owner Governance Decisions

### OWNER-GOV-001 — Decision Authority Model

```text
Decision ID
OWNER-GOV-001

Evidence
docs/governance/decisions/ns_evermore_decision_authority_model_0.0.1.md

Status
OWNER_DECIDED / GAC_RECOGNIZED / NORMATIVE
```

Decision summary:

```text
Root Product / Constitutional Decisions
→ Project Owner

MDE
→ Project Owner

DAD
→ Authorized Architecture / Design Session

Implementation Choice
→ Authorized Detailed Design / Implementation Planning / IWP / Codex scope
→ only where Accepted Design leaves implementation freedom

Global Architecture Coordinator
→ classification / escalation / independent acceptance / phase authorization / continuity / drift governance
→ MUST NOT decide Owner-reserved MDE on behalf of Project Owner
```

Additional normative rules:

```text
Component internal design that changes Authority / SoT / Trust / major compatibility / major lock-in
→ MDE / Project Owner

Non-semantic component internal decomposition
→ DAD by authorized design session

Repository / directory / package layout without architecture impact
→ DAD or Implementation Planning

Directory Placement != Architecture Boundary
Python Package != Product Component
Django App != Architecture Authority

Replaceable ordinary technology/library choice
→ DAD or implementation choice subject to accepted boundaries

Major vendor/provider/language/framework/protocol/storage/artifact-format lock-in or high migration cost
→ MDE / Project Owner

Already frozen Python/Django/WebSocket/Vue root technology facts
→ INHERITED_FACT

Codex
→ implementation freedom only
→ no Architecture authority
```

The Project Owner may explicitly reserve an unresolved delegated decision before finalization. Accepted material is not silently overridden; formal reopen/supersession/revalidation applies.

## 5. Accepted Architecture Constraints

Current accepted Architecture Constraints:

```text
NSE-001  Native Tenant Semantic Invariance
NSE-002  Tenant / Organization Semantic Non-collapse
NSE-003  Organization Structural Plurality and Extensibility
NSE-004  Offline Core Correctness and Governance Invariance
```

These are constraints rather than decisions but are included here as decision-classification context for downstream sessions.

## 6. Current Open Decision State

```text
Open MDE
0

Unpersisted Owner Decision
0

Owner-reserved unresolved decision
0
```

## 7. Consumption Rule

Every future Architecture / Design / Implementation Planning / IWP / Codex session MUST consume `OWNER-GOV-001` through the Current Required Read Set or its direct Mandatory Read Set.

If a downstream session is uncertain whether a choice is DAD, MDE, or implementation freedom:

```text
DEFAULT
→ escalate classification upward
→ MDE when material architecture significance cannot be ruled out
```

No session may use directory structure, framework placement, library choice, provider implementation, or code organization to bypass the accepted decision-authority model.
