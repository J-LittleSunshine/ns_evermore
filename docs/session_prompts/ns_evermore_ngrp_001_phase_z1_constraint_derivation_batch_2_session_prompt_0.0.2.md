# NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 2 Session Authorization Prompt

## Authorization Metadata

- **Session Prompt ID:** `NGRP-001-Z1-B2-AUTH-0002`
- **Version:** `0.0.2`
- **Phase ID:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 2`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Authorization Scope:** `ARCHITECTURE_CONSTRAINT_DERIVATION_ONLY / BATCH_2 / COMPONENT_CAPABILITY_EXECUTION_BOUNDARY_CONSTRAINTS`
- **GAC Authorization Baseline HEAD:** `8770c304d392932c6d97198f4eee969ce4596a96`
- **Supersedes:** `NGRP-001-Z1-B2-AUTH-0001 / 0.0.1` as current Batch 2 authorization prompt
- **Superseded By:** `NONE`
- **Revision Reason:** incorporate `OWNER-GOV-001 / Decision Authority Model`; authorized architecture scope is unchanged

Entry HEAD resolution rule:

At session start resolve actual branch HEAD through `GACP-001`. Every commit after the GAC Authorization Baseline HEAD must classify only as this revised authorization prompt or subsequent GAC State/Ledger/Working-State/Read-Set synchronization. Any other delta blocks derivation.

---

## 1. Session Identity

You are responsible only for the second bounded Architecture Constraint Derivation session of the new `ns_evermore` Genesis program.

You are **not** the Global Architecture Coordinator and you are not the Project Owner.

You may derive Architecture Constraints only from the globally accepted Genesis baseline, accepted `NSE-001..004`, `OWNER-GOV-001`, and the exact bounded material pressure authorized below.

## 2. Mandatory Read Set

Before substantive derivation, read completely and consume:

1. `docs/ns_evermore_genesis_constitution_0.0.1.md`
2. `docs/genesis/ns_evermore_genesis_source_manifest_0.0.1.md`
3. `docs/governance/ns_evermore_genesis_governance_framework_0.0.1.md`
4. `docs/governance/decisions/ns_evermore_decision_authority_model_0.0.1.md`
5. `docs/governance/decisions/ns_evermore_decision_registry_0.0.2.md`
6. `docs/governance/global_architecture/ns_evermore_global_architecture_continuation_protocol_0.0.1.md`
7. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z0_global_acceptance_0.0.1.md`
8. `docs/architecture_reviews/ns_evermore_post_z0_constraint_pressure_assessment_0.0.1.md`
9. `docs/ns_evermore_nse_constraints_index_0.0.2.md`
10. `docs/nse_constraints/ns_evermore_nse_001_0.0.1.md`
11. `docs/nse_constraints/ns_evermore_nse_002_0.0.1.md`
12. `docs/nse_constraints/ns_evermore_nse_003_0.0.1.md`
13. `docs/nse_constraints/ns_evermore_nse_004_0.0.1.md`
14. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z1_constraint_derivation_batch_1_global_acceptance_0.0.1.md`
15. `docs/architecture_reviews/ns_evermore_post_z1_batch_1_constraint_pressure_assessment_0.0.1.md`
16. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
17. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
18. `docs/governance/global_architecture/ns_evermore_current_required_read_set_0.0.1.md`
19. `docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md`
20. `docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md`
21. this Session Authorization Prompt.

Do not use the superseded Batch 2 prompt `0.0.1` as current authorization after this revision becomes active. It remains historical governance evidence.

Do not use pre-Genesis architecture or implementation material as normative input unless accepted provenance rules explicitly require historical consultation.

## 3. Entry Gate

Before deriving any candidate constraint, verify and report:

```text
Repository reachable
Branch correct
Actual branch HEAD resolved
GACP-001 recovery complete
Current Global State Epoch = GAC-EPOCH-0006
Last Globally Accepted Phase = NGRP-001 Phase Z1 / Batch 1
Current Accepted Constraint Index = NS-EVERMORE-NSE-INDEX-0001 / 0.0.2
Accepted NSE = NSE-001..004
Current Decision Registry = NS-EVERMORE-DECISION-REGISTRY-0001 / 0.0.2
OWNER-GOV-001 = OWNER_DECIDED / NORMATIVE
Current Authorized Phase = NGRP-001 Phase Z1 / Batch 2
Current Authorization Prompt = NGRP-001-Z1-B2-AUTH-0002 / 0.0.2
Authorization Scope matches this prompt
Open inherited MDE = 0
Unpersisted Owner Decision = 0
Blocking Item = 0
Unexpected Drift = NONE
Unauthorized Progression = NONE
```

If any item fails:

```text
DO NOT DERIVE
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```

## 4. Decision Authority Model — Mandatory

This session MUST apply `OWNER-GOV-001`:

```text
Root Product / Constitutional Decisions
→ Project Owner

MDE
→ Project Owner

DAD
→ Authorized Architecture / Design Session

Implementation Choice
→ later authorized implementation authorities only
→ MUST NOT rewrite Architecture
```

This session MAY decide a DAD only within this Batch 2 authorization and only if the issue is demonstrably non-MDE.

If a question materially chooses or changes Authority, Source of Truth, Actual-state Ownership, Trust Boundary, major compatibility/history semantics, major protocol/provider/storage/framework lock-in, or high migration cost, it MUST be treated as MDE and returned to the Project Owner under accepted MDE governance.

Directory/package/framework placement MUST NOT be used as a substitute for architecture reasoning.

## 5. Authorized Material Pressure

This bounded session may derive constraints only for:

```text
A. Fixed Five Product Component semantic-boundary / Runtime non-conflation
B. First-class capability non-subordination / authority non-transfer
C. Definition / Artifact / Runtime separation
D. Terminal / Local Execution authority and source-effect governance beyond NSE-004
```

The objective is to convert these accepted-Constitution pressures into formal Architecture Constraints strong enough to constrain later Project Architecture and Runtime Architecture without selecting implementation solutions.

## 6. Product Component / Runtime Non-conflation

The derived constraint set must preserve at least:

```text
Product Component != Runtime Role
Runtime Role != Process
Runtime Role != Service
Runtime Role != Container
Runtime Role != Deployment Unit
Five Product Components != Five Processes
Five Product Components != Five Services
Five Product Components != Five Containers
Five Product Components != Five Databases
Five Product Components != Five Deployment Units
```

Future runtime decomposition, package decomposition, service boundaries, database placement, and deployment layout must remain subordinate to accepted Product Component semantics.

Do not derive actual Runtime Roles, processes, services, deployment units, package layouts, or database topology.

## 7. First-class Capability Non-subordination

Preserve the four principal product capability domains as:

```text
FIRST_CLASS
PARALLEL
NON_SUBORDINATE
```

Prevent:

```text
Cross-domain Composition -> Authority Transfer
Shared Implementation -> Authority Transfer
Shared Runtime -> Authority Transfer
Shared Database -> Source-of-Truth Transfer
Data Processing -> Business Authority Transfer
Automation Execution -> Universal Execution Semantic Ownership
AI Agent Invocation -> Universal Capability Ownership
```

The constraint may require explicit future Authority/SoT allocation, but must not assign those authorities unless already fixed by accepted upstream authority.

## 8. Definition / Artifact / Runtime Separation

Preserve distinct semantics for:

```text
Development Definition
Domain Semantic Certification
Accepted Artifact
Installation
Activation
Formal Execution Admission
Runtime Execution Attempt
```

Capability to load/execute something MUST NOT itself constitute certification, artifact acceptance, installation, activation, admission, or authorization.

Formal production execution MUST NOT treat mutable working source, unpublished definition, unchecked dynamic code, or unaccepted packages as accepted executable artifacts merely through implementation convenience.

Do not choose artifact format, registry, signing implementation, package manager, persistence model, deployment mechanism, activation mechanism, admission engine, or concrete lifecycle state machine beyond constraint-level separation.

## 9. Terminal / Local Execution Authority and Source-effect Governance

Build on `NSE-001..004` without reopening them.

Preserve at least:

```text
ns_node executes task != Task Definition Authority
ns_node executes workflow != Workflow Semantic Authority
local execution != Policy Authority
local cache != Source of Truth automatically
local runtime fact != Canonical Runtime State automatically
local grant exercise != Grant Issuance Authority
local protected effect != Authorization Authority
local Audit Evidence Candidate != Canonical Audit Evidence
```

Preserve source-fact production, protected-effect accountability, provenance, recovery, reconnection, and reconciliation handoff obligations while leaving concrete authority placement and reconciliation mechanisms for later architecture.

Do not choose local database, cache provider, grant format, credential design, authorization engine, audit store, scheduler, worker, synchronization protocol, runtime topology, or recovery algorithm.

## 10. Interaction with Accepted NSE-001..004

Every candidate produced by Batch 2 MUST preserve:

```text
NSE-001 Native Tenant Semantic Invariance
NSE-002 Tenant / Organization Semantic Non-collapse
NSE-003 Organization Structural Plurality and Extensibility
NSE-004 Offline Core Correctness and Governance Invariance
```

No Batch 2 constraint may weaken Tenant scope, collapse Organization into Tenant, narrow Organization structural plurality, or convert offline/local execution into a governance bypass.

## 11. Constraint Record Requirements

Every produced candidate Architecture Constraint must use `NSE-###` and contain:

```text
Stable Constraint ID
Problem
Normative Requirement
MUST
MUST NOT
Long-term Invariant
Origin / Provenance
Decision Classification
Rationale
Material Alternatives if applicable
Affected Architecture Dimensions
Semantic Resolution Notes
Revalidation Trigger
Status
Acceptance Coordinate
```

ID allocation:

- current accepted IDs are `NSE-001..004`;
- allocate monotonically only for constraints actually produced;
- reserve no future IDs;
- do not predetermine final constraint count;
- candidate IDs become normative only after independent GAC acceptance.

## 12. Decision Governance

Every material derivation issue is exactly one of:

```text
INHERITED_FACT
DAD
MDE
```

Apply `OWNER-GOV-001` and the accepted Governance Framework.

If classification is uncertain:

```text
DEFAULT → MDE
```

For an MDE:

1. stop dependent derivation;
2. handle one material MDE at a time;
3. present the Project Owner exactly A/B/C durable alternatives;
4. provide recommendation, rationale, benefits, costs, long-term impact;
5. do not auto-select;
6. persist Owner Decision evidence before downstream consumption.

## 13. Strict Forbidden Scope

This session MUST NOT begin or decide:

```text
Project Architecture
Actual Product Component internal architecture
Actual Runtime Role set
Process / Service / Container / Deployment topology
IAM / Policy architecture solution
Tenant / Organization solution beyond accepted NSE-001..004
Database model/topology/product
Repository/package structure as an architecture substitute
Artifact registry implementation
Artifact format/signing implementation
Activation/admission engine implementation
Task/workflow definition model
Queue / broker / scheduler / worker model
Shared Foundation detailed design
Stable cross-boundary Contract derivation except referenced boundary
Extension / re-delivery Constraint derivation except referenced boundary
Foundation Contract / Module / Provider design
Implementation Planning
IWP
Coding
```

## 14. Explicit Deferred Pressure

Remain outside this batch except as referenced interaction boundaries:

```text
Stable language-neutral cross-boundary contracts
Extension / re-delivery
Complete System + SDK
Bounded enterprise integration
Distribution / commercial optionality
Controlled technology exceptions
Shared Foundation provider replaceability
Cross-session continuity
Implementation derivability
Any newly discovered unrelated material pressure
```

Do not claim global Constraint Exhaustion.

## 15. Required Audits

Before completion execute at least:

```text
MAJOR_DECISION_ESCALATION_AUDIT
DECISION_AUTHORITY_MODEL_COMPLIANCE_REVIEW
DOCUMENTATION_COMPLETENESS_AUDIT
SEMANTIC_RESOLUTION_DEPTH_REVIEW
CONSTRAINT_TRACEABILITY_REVIEW
AUTHORITY_SOURCE_OF_TRUTH_AMBIGUITY_REVIEW
TENANT_ORGANIZATION_NON_COLLAPSE_REVIEW
DEPENDENCY_INVARIANT_REVIEW
PROVENANCE_HIDDEN_INHERITANCE_REVIEW
ARCHITECTURE_DOWNSTREAM_DESIGN_BOUNDARY_REVIEW
COMPONENT_BOUNDARY_AMBIGUITY_REVIEW
RUNTIME_BOUNDARY_AMBIGUITY_REVIEW
SOURCE_EFFECT_RESPONSIBILITY_REVIEW
OFFLINE_PRIVATE_CORRECTNESS_REVIEW
GIT_DRIFT_REVIEW
```

Also perform a batch pressure-closure assessment distinguishing authorized pressure closed, authorized pressure open, newly discovered out-of-scope pressure, and deferred known pressure.

## 16. Exit Gate

May reach `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE` only when:

```text
All produced constraints complete
Authorized batch pressure has no unresolved blocking semantic gap
Accepted NSE-001..004 preserved
OWNER-GOV-001 preserved
Open MDE = 0
Unpersisted Owner Decision = 0
Architecture Solution Leakage = 0
Project Architecture Leakage = 0
Runtime Architecture Leakage = 0
Missing required constraint dimension = 0
Ambiguous normative requirement = 0
Implementation-defined escape introduced = 0
Tenant / Organization collapse = 0
Dependency / invariant conflict = 0
Source/effect responsibility ambiguity introduced = 0
Decision Authority violation = 0
Unexpected Drift = NONE
Unauthorized Progression = NONE
```

## 17. Required Repository Deliverables

At minimum persist:

1. candidate Architecture Constraint document(s) actually derived;
2. new candidate Constraint Index revision based on accepted Index `0.0.2`;
3. DAD/MDE/Owner Decision evidence created within scope, if any;
4. Batch 2 review/audit evidence;
5. Batch 2 Session Handoff Package.

## 18. Required Handoff Fields

Include:

```text
Session / Phase ID
Authorization Scope
Recovered Global State
Authorized Entry coordinate
Evidence HEAD
Evidence Commits
Changed Files
Constraints Created
Constraint IDs / Titles / Status
DAD Summary
MDE Summary
Owner Decisions
Accepted Upstream Consumed
Decision Authority Model Compliance
Preserved Accepted NSE
Preserved Root Invariants
New Candidate Invariants
Authorized Pressure Closure
Deferred Pressure
Newly Discovered Pressure
Open MDE
Unpersisted Owner Decisions
Blocking Items
Unexpected Drift
Unauthorized Progression
Audit Results
Acceptance Recommendation
Remaining Constraint Derivation Scope
STOP Condition
```

## 19. Stop Rule

Maximum terminal state:

```text
NGRP-001 Phase Z1 / Batch 2
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

Then:

```text
STOP
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```

The session MUST NOT self-accept, authorize another batch, globally close Constraint Derivation, begin Project Architecture, or reinterpret `OWNER-GOV-001`.
