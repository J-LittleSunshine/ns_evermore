# NGRP-001 Phase Z0 — Genesis Governance Bootstrap Session Authorization Prompt

## Authorization Metadata

```text
Session Prompt ID
NGRP-001-Z0-AUTH-0001

Phase ID
NGRP-001 / Z0

Repository
J-LittleSunshine/ns_evermore

Branch
architecture/ns-evermore-genesis-0.0.1

Authorization Scope
GENESIS_GOVERNANCE_BOOTSTRAP_ONLY

Authorized Entry HEAD
d981da571a8b7260b35fe2aed17f390ac2abbf9c
```

## Mandatory Inputs

1. Project Owner Root Prompt supplied 2026-08-11.
2. `docs/ns_evermore_genesis_constitution_0.0.1.md` as the durable normalization target during Z0.
3. Genesis Source / Provenance Manifest.
4. Governance Framework.
5. Current repository state at the authorized branch.

## Entry Gate

Before substantive Z0 work:

```text
Repository reachable → REQUIRED
Visibility/current metadata verified → REQUIRED
Default branch resolved → REQUIRED
Genesis branch absent or safely resolvable → REQUIRED
Entry HEAD resolved → REQUIRED
Unexpected drift at entry → 0
```

Resolved Z0 entry:

```text
Repository visibility → public
Default branch → main
Entry HEAD → d981da571a8b7260b35fe2aed17f390ac2abbf9c
Genesis branch created from main → YES
Initial compare → identical / ahead 0 / behind 0
```

## Allowed Work

Z0 may establish only the governance baseline required to make future work repository-resumable:

```text
Project Constitution
Source / Provenance Manifest
Architecture Constraint Namespace / Index Bootstrap
Decision Governance
Quality Governance
Derivation Governance
Continuity Governance
Global Architecture Continuation Protocol
Global Architecture State
Global Architecture Working State
Global Architecture Ledger
Current Required Read Set
Session Authorization Standard
Session Handoff Standard
Document Status / Authority / Supersession Standard
Decision Registry mechanism
Architecture-to-Implementation Traceability Standard
Implementation Planning Governance
IWP Standard
Codex Session Governance
Z0 Review Evidence
Z0 Handoff Package
```

Z0 may use DADs for governance implementation matters that do not alter root semantics.

## Strict Forbidden Scope

```text
Concrete Architecture Constraint Derivation beyond bootstrap necessity
Project Architecture
IAM Architecture
Organization Model Solution
Policy Architecture
Data Architecture
Knowledge Architecture
Runtime Architecture
Component Internal Design
Shared Foundation Detailed Design
Foundation Contract Design
Foundation Module Design
Provider Selection
Database Design
Queue / Scheduler / Worker Selection
Implementation Master Plan
IWP generation
Coding
Automatic next-phase authorization
```

## Decision Governance

Every material matter is classified as `INHERITED_FACT`, `DAD`, or `MDE`.

Any question changing root product meaning, decision authority, acceptance authority, continuity source of truth, or five-component root topology is an MDE and requires Project Owner choice before persistence/consumption.

## Required Z0 Audits

```text
MAJOR_DECISION_ESCALATION_AUDIT
DOCUMENTATION_COMPLETENESS_AUDIT
SEMANTIC_RESOLUTION_DEPTH_REVIEW
CONSTRAINT_TRACEABILITY_REVIEW
AUTHORITY_SOURCE_OF_TRUTH_AMBIGUITY_REVIEW
TENANT_ORGANIZATION_NON_COLLAPSE_REVIEW
DEPENDENCY_INVARIANT_REVIEW
PROVENANCE_HIDDEN_INHERITANCE_REVIEW
ARCHITECTURE_DOWNSTREAM_DESIGN_BOUNDARY_REVIEW
OFFLINE_PRIVATE_CORRECTNESS_REVIEW
FRESH_SESSION_RECOVERY_TEST
GIT_DRIFT_REVIEW
```

## Exit Gate

Z0 may complete only when:

```text
Root Product Semantics → CLOSED / RECORDED
Five-component Root Topology → RECORDED
Native Multi-tenancy → RECORDED
Tenant / Organization Non-collapse → RECORDED
Complex Organization Extensibility → RECORDED
Python-first Direction → RECORDED
Shared Foundation Requirement → RECORDED
Offline / Private Requirement → RECORDED
Decision Governance → CLOSED
Quality Governance → CLOSED
Derivation Governance → CLOSED
Continuity Governance → CLOSED
Implementation Governance → ESTABLISHED
Current Required Read Set → ESTABLISHED
Session Handoff Schema → ESTABLISHED
Supersession Rule → ESTABLISHED
Decision Traceability → ESTABLISHED
Design-to-Implementation Traceability → ESTABLISHED
Fresh-session Recovery Test → PASS
Architecture Solution Leakage → 0
Open MDE → 0
Unpersisted Owner Decision → 0
Missing Normative Dimension → 0
Blocking Item → 0
```

## Required Handoff Fields

The final Z0 handoff must contain Repository, Branch, Entry HEAD, Final Evidence HEAD, created governance artifacts, Constitution/State/Working State/Ledger/Continuation Protocol coordinates, Current Required Read Set, decision governance result, recovery-test result, drift result, Open MDE, Blocking Item, acceptance recommendation, unique next legal governance action, complete decision/audit summaries, and stop condition.

## Stop Rule

Maximum Z0 session state:

```text
GENESIS GOVERNANCE BOOTSTRAP
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

Then:

```text
STOP
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```

Architecture Constraint Derivation is not authorized by this prompt.