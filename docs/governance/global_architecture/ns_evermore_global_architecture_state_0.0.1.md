# ns_evermore Global Architecture State

- **Status:** `CURRENT / GAC-EPOCH-0019`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`

# WHAT IS TRUE NOW

```text
Current Global State Epoch
GAC-EPOCH-0019

Current Branch
architecture/ns-evermore-genesis-0.0.1

State Verified Through HEAD
36fe390c9cce7ee1b0434be0bfc683f20d5b4ea2

Genesis Constitution
docs/ns_evermore_genesis_constitution_0.0.1.md
→ GLOBAL_ACCEPTED / NORMATIVE

Current Unified Governance
docs/governance/ns_evermore_governance_0.0.2.md
→ OWNER_DECIDED / GAC_RECOGNIZED / NORMATIVE

Current Decision Registry
docs/governance/decisions/ns_evermore_decision_registry_0.0.7.md
→ CURRENT / NORMATIVE

Current Constraint Index
docs/ns_evermore_nse_constraints_index_0.0.5.md
→ CURRENT / NORMATIVE

Accepted NSE
NSE-001..017

Architecture Constraint Derivation
GLOBAL_CLOSED / COMPLETE

Project Architecture Synthesis
GLOBAL_CLOSED / COMPLETE

Current Project Architecture
docs/ns_evermore_project_architecture_0.0.3.md
→ GLOBAL_ACCEPTED / NORMATIVE / CURRENT

Accepted Project Architecture DAD Baseline
Z2-DAD-001..041

Owner MDE Baseline
Z2-MDE-001..017
→ OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED

Current Project Owner Capability Clarifications
→ Agent-to-Node governed delegation REQUIRED
→ ns_server server-local long-running/time-triggered background work REQUIRED
→ Automation dual authoring via SDK source + ns_web visual drag-and-drop REQUIRED
→ OWNER_CAPABILITY_DECIDED / PERSISTED / GAC_RECOGNIZED

Current Authorized Phase
NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1

Authorization Scope
FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT

Open MDE
0

Unpersisted Owner Decision
0

Owner-reserved unresolved decision
0

Blocking Item
NONE

Known Drift
NONE
```

---

# Current Accepted Project Architecture Baseline

Project Architecture `0.0.3` is complete and globally closed at Project Architecture level.

It establishes the current five-component responsibility/Authority/SoT/Actual-state/lifecycle/Trust/recovery/evolution baseline and MUST NOT be silently reopened by Z3.

Exactly five Product Components remain:

```text
ns_server
ns_runtime
ns_node
ns_agent
ns_web
```

Shared Foundation remains outside the five and is not a sixth Product Component.

The four principal capability domains remain:

```text
Business Application Construction / Runtime
Automation Construction / Execution
AI Agent Runtime / Tooling
Enterprise Data / Knowledge / Foundational ETL

→ FIRST_CLASS / PARALLEL / NON_SUBORDINATE
```

---

# Current Z3 Project Owner Capability Clarifications

These are accepted Owner capability requirements and must be consumed by Batch 1 without re-asking the Owner.

## 1. `ns_agent` → `ns_node` governed delegation

```text
ns_agent
→ MUST be capable of delegating applicable executable work / task intent to ns_node

ns_node
→ MUST be capable of receiving and executing applicable delegated work inside its accepted local-execution responsibility
```

Permanent non-transfer rules:

```text
Agent Delegation != Automation Definition Authority Transfer
Agent Delegation != Policy Authority Transfer
Agent Delegation != Artifact Acceptance Authority Transfer
Agent Delegation != Execution Admission Authority Transfer
Agent Delegation != ns_node becoming Agent Semantic Authority
Agent Delegation != ns_agent becoming local protected-effect authority
```

Concrete delegation contract, routing, evidence, runtime coordination and transport are later design questions.

## 2. `ns_server` server-local background work

Required capability:

```text
ns_server
→ bounded continuously available server-local background work execution capability
→ supports long-running work belonging to ns_server responsibility
→ supports time-triggered / scheduled work belonging to ns_server responsibility
```

Project Owner intent includes a resident background execution facility.

At current Z3 Batch 1 scope:

```text
Capability requirement
→ NORMATIVE OWNER REQUIREMENT

Concrete process pool / worker / scheduler / queue / supervision topology
→ NOT YET FROZEN
```

Permanent boundary:

```text
ns_server server-local background work
!= ns_runtime cross-component scheduling / dispatch responsibility replacement
```

## 3. Automation dual authoring surfaces

Automation Definitions / Flow Packages intended for applicable `ns_node` execution must support both:

```text
Source-code / System-level SDK authoring
AND
Visual Web drag-and-drop authoring
```

Accepted architecture placement remains:

```text
Automation Definition / Workflow Semantic Authority
→ ns_server

Automation Canonical Definition SoT
→ ns_server

Visual Builder / Management UI
→ ns_web

Source Development Surface
→ System-level SDK / Development Surface

Applicable Local Execution
→ ns_node
```

Therefore:

```text
Different Authoring Surfaces
→ converge on same governed Automation semantics

SDK Source Authoring
!= Artifact / Admission bypass

Web Drag-and-drop Authoring
!= ns_web becomes canonical Definition SoT

ns_node Execution
!= ns_node becomes Workflow Semantic Authority
```

Concrete SDK API, visual DSL/schema, build/generation mechanism, package format and execution representation remain later design.

---

# Current Authorization — Z3 / Batch 1

## Purpose

Z3 Batch 1 is a **capability-discovery and Owner Capability Checkpoint session before normative Five-component Internal Architecture Boundary synthesis**.

It must not merely repeat known capabilities. It must actively derive what Product Component and cross-component common capabilities are plausibly required by the accepted product/system semantics, including capabilities the Project Owner has not yet explicitly identified.

Authorization Scope:

```text
FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY
/ BATCH_1
/ COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT
```

## A. Five-component Capability Pressure Scan

For every Product Component:

```text
ns_server
ns_runtime
ns_node
ns_agent
ns_web
```

construct a broad product-capability inventory from current Repository authority.

The scan must consider, where applicable:

```text
definition / authoring
runtime / execution
administration / operations
offline / degraded
recovery / reconciliation
security / trust / principal
configuration / lifecycle
extension / re-delivery
compatibility / migration / conformance
observability / diagnostics
integration / external systems
SDK / development experience
```

The purpose is to find product-capability gaps and overlaps before internal-boundary design.

Do not convert internal implementation conveniences into product capabilities.

## B. Mandatory Capability Classification

Every capability item must be exactly one of:

```text
INHERITED_REQUIRED
DERIVED_REQUIRED
OWNER_DECISION_REQUIRED
DEFERRED
NON_GOAL
```

Interpretation:

```text
INHERITED_REQUIRED
→ required by Constitution / NSE / accepted Project Architecture / accepted Owner decision / current Owner capability clarification
→ do not ask Owner again

DERIVED_REQUIRED
→ necessary supporting capability implied by accepted semantics
→ may be derived if not a material product-scope expansion and not MDE-class

OWNER_DECISION_REQUIRED
→ product-significant function not yet frozen
→ return to Project Owner one material question at a time

DEFERRED
→ intentionally not decided here; material deferral names later authority

NON_GOAL
→ explicitly outside component/product capability scope
```

## C. Cross-component Common Capability Discovery

Batch 1 may discover and classify common capability candidates needed by multiple Product Components.

This is capability pressure discovery only:

```text
NOT Shared Foundation Architecture
NOT Foundation capability acceptance
NOT Contract / Module / Provider Design
```

Known inherited/common pressure includes at least:

```text
HTTP / client capability
cache / client capability
storage / client capability
configuration loading capability
```

The session must also assess real cross-component need for candidate pressure areas such as:

```text
logging / structured diagnostics
telemetry / observability primitives
time / temporal primitives
serialization / representation primitives
cryptography / secret-reference primitives
database utility primitives
event / notification utility primitives
health / lifecycle reporting primitives
operation / correlation / trace context primitives
conformance / compatibility support primitives
```

This list is not pre-accepted capability scope.

For each candidate determine:

```text
actual consumers
reusability evidence
stable-boundary plausibility
provider-neutrality need
Authority / SoT implications
whether component-local ownership is more correct
whether it should be carried as a candidate into later Shared Foundation Architecture
whether Project Owner capability input is required
```

No common capability gains Product Authority merely because it is reused across components.

## D. Owner Capability Checkpoint

The producing session should first build a candidate capability inventory, then ask the Project Owner only about genuinely material missing product functions.

For each `OWNER_DECISION_REQUIRED` capability:

```text
one material question at a time
A / B / C durable options
recommendation
rationale
benefits
costs
long-term impact
```

Persist each Owner result before dependent synthesis continues.

Do not re-ask the three Owner clarifications above.

## E. Candidate Capability Baseline

Batch 1 must produce one coherent candidate baseline covering:

```text
five Product Component capability inventories
capability classification
cross-component capability dependencies
common capability candidates
capability overlap / gap findings
Owner capability decisions made during the Batch
explicit DEFERRED / NON_GOAL items
```

This candidate, if independently accepted by GAC, becomes the upstream input to a later explicitly authorized Z3 Batch 2 internal-boundary synthesis.

---

# Important Boundary: Batch 1 vs Batch 2

Project Owner planning intent is:

```text
Z3 Batch 1
→ discover / decide capability scope first

Z3 Batch 2
→ continue Five-component Internal Architecture Boundary synthesis
```

However:

```text
Z3 Batch 2
→ NOT CURRENTLY AUTHORIZED
```

Batch 1 acceptance does not automatically authorize Batch 2.

---

# Decision Authority

```text
Root Product / Constitutional Decision → Project Owner
MDE → Project Owner
Product-significant new capability → Project Owner Capability Checkpoint
DAD → authorized Architecture / Design Session inside exact scope
GAC → classification / escalation / independent acceptance / phase authorization / continuity
Implementation / Codex → no Architecture authority
```

Material changes involving Authority, SoT, Actual-state Ownership, Trust, stable identity, major compatibility, material offline fail policy, major protocol/provider/framework/storage lock-in or high migration cost remain MDE-class.

If uncertain:

```text
DEFAULT → MDE
```

---

# Strict Forbidden Scope

Z3 Batch 1 MUST NOT begin or decide:

```text
normative Five-component Internal Architecture Boundary decomposition
Component Internal Design
internal module decomposition
Django app / Python package / Vue internal decomposition
class/service/repository/adapter design
Runtime Responsibility Architecture
Runtime Role taxonomy
process/service/worker/container/deployment topology
concrete ns_server process-pool / worker realization
actual Agent→Node delegation Contract/API/schema/wire/message design
concrete Automation SDK API / visual DSL / package representation
database/storage topology
Shared Foundation Architecture or detailed Foundation capability baseline
Foundation Contract / Module / Provider Design
SDK package/generator realization
Repository/package structure
Implementation Planning
IWP
Coding
```

Batch 1 may identify future design pressure in these areas, but cannot solve it.

---

# Entry Gate

Before work:

```text
Repository / branch / actual HEAD resolved
Recovery complete under Unified Governance
Current Global State Epoch = GAC-EPOCH-0019
Architecture Constraint Derivation = GLOBAL_CLOSED / COMPLETE
Project Architecture Synthesis = GLOBAL_CLOSED / COMPLETE
Current Project Architecture = 0.0.3 / GLOBAL_ACCEPTED / NORMATIVE / CURRENT
Current Decision Registry = 0.0.7
Accepted Constraint Index = 0.0.5
Accepted NSE = NSE-001..017
Accepted Project Architecture DAD Baseline = Z2-DAD-001..041
Accepted Owner MDE Baseline = Z2-MDE-001..017
Current Owner Capability Clarifications = PRESENT / PERSISTED
Open inherited MDE = 0
Unpersisted Owner Decision = 0
Blocking Item = NONE
Unexpected Drift = NONE
Unauthorized Progression = NONE
```

If recovery fails:

```text
DO NOT DESIGN
→ RETURN TO GAC
```

---

# Required Reviews / Exit Gate

Apply relevant Unified Governance reviews including at least:

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
COMPONENT_BOUNDARY_AMBIGUITY_REVIEW
OWNER_CAPABILITY_SCOPE_ESCALATION_REVIEW
CAPABILITY_OVERLAP_GAP_REVIEW
COMMON_CAPABILITY_REUSE_PRESSURE_REVIEW
GIT_DRIFT_REVIEW
```

Completion requires:

```text
Five Product Component capability inventories → COMPLETE
Cross-component common capability scan → COMPLETE
All capability items → CLASSIFIED
Persisted Owner capability clarifications → CONSUMED
OWNER_DECISION_REQUIRED items → RESOLVED / PERSISTED or 0
Unclassified product-significant capability → 0
Capability gap blocking later boundary design → 0
Capability overlap ambiguity → 0
Common capability candidate status → explicit
Open MDE → 0
Unpersisted Owner Decision → 0
Authority/SoT ambiguity introduced → 0
Accepted Project Architecture violation → 0
Internal-boundary design leakage → 0
Runtime Architecture leakage → 0
Shared Foundation detailed-design leakage → 0
Implementation-defined Escape → 0
Unexpected Drift → NONE
Unauthorized Progression → NONE
```

Producing-session maximum:

```text
NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
→ STOP
→ RETURN TO GAC
```

---

# Current Required Read Set

Minimum sufficient context for a fresh Z3 Batch 1 session:

```text
1. docs/ns_evermore_genesis_constitution_0.0.1.md
2. docs/governance/ns_evermore_governance_0.0.2.md
3. docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md
4. docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md
5. docs/governance/decisions/ns_evermore_decision_registry_0.0.7.md
6. docs/ns_evermore_nse_constraints_index_0.0.5.md
7. docs/nse_constraints/ns_evermore_nse_001_0.0.1.md through ns_evermore_nse_017_0.0.1.md
8. docs/ns_evermore_project_architecture_0.0.3.md
9. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z2_project_architecture_synthesis_batch_2_global_acceptance_0.0.1.md
10. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z2_project_architecture_remaining_pressure_assessment_0.0.1.md
11. docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md
    → relevant tail only unless deeper history is required
```

Read individual `Z2-MDE-001..017` evidence when capability classification/revalidation depends on precise Owner decision semantics.

---

# Unique Next Legal Action

```text
Start one bounded NGRP-001 Phase Z3 / Five-component Internal Architecture Boundaries / Batch 1 session under:

COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT

Derive broad five-component and common-capability inventories,
actively discover missing product functions,
perform Owner Capability Checkpoint for material new capabilities,
and stop before normative internal-boundary synthesis.
```
