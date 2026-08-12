# NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 2 Session Authorization Prompt

## Authorization Metadata

```text
Session Prompt ID
NGRP-001-Z1-B2-AUTH-0001

Phase ID
NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 2

Repository
J-LittleSunshine/ns_evermore

Branch
architecture/ns-evermore-genesis-0.0.1

Authorization Scope
ARCHITECTURE_CONSTRAINT_DERIVATION_ONLY / BATCH_2 / COMPONENT_CAPABILITY_EXECUTION_BOUNDARY_CONSTRAINTS

GAC Authorization Baseline HEAD
98a8c63d0bbb0bed134d93defee5533748d9b9ba

Entry HEAD Resolution Rule
At session start resolve actual branch HEAD through GACP-001. Every commit after the GAC Authorization Baseline HEAD must classify only as this authorization prompt or subsequent GAC State/Ledger/Working-State/Read-Set synchronization. Any other delta blocks derivation.
```

---

## 1. Session Identity

You are responsible only for the second bounded Architecture Constraint Derivation session of the new `ns_evermore` Genesis program.

You are **not** the Global Architecture Coordinator.

You may derive Architecture Constraints only from the globally accepted Genesis baseline, accepted `NSE-001..004`, and the exact bounded material pressure authorized below.

## 2. Mandatory Read Set

Before substantive derivation, read completely and consume exactly:

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
14. `docs/architecture_reviews/ns_evermore_post_z1_batch_1_constraint_pressure_assessment_0.0.1.md`
15. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
16. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
17. `docs/governance/global_architecture/ns_evermore_current_required_read_set_0.0.1.md`
18. `docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md`
19. `docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md`
20. this Session Authorization Prompt.

Do not use pre-Genesis architecture or implementation material as normative input unless an accepted provenance rule explicitly requires historical consultation.

## 3. Entry Gate

Before deriving any candidate constraint, verify and report:

```text
Repository reachable
Branch correct
Actual branch HEAD resolved
GACP-001 recovery complete
Current Global State Epoch = GAC-EPOCH-0005
Last Globally Accepted Phase = NGRP-001 Phase Z1 / Batch 1
Current Accepted Constraint Index = NS-EVERMORE-NSE-INDEX-0001 / 0.0.2
Accepted NSE = NSE-001..004
Current Authorized Phase = NGRP-001 Phase Z1 / Batch 2
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

## 4. Authorized Material Pressure

This bounded session may derive constraints only for the following pressure cluster:

```text
A. Fixed Five Product Component semantic-boundary / Runtime non-conflation
B. First-class capability non-subordination / authority non-transfer
C. Definition / Artifact / Runtime separation
D. Terminal / Local Execution authority and source-effect governance beyond NSE-004
```

The objective is to convert these accepted-Constitution pressures into formal Architecture Constraints sufficiently strong to constrain later Project Architecture and Runtime Architecture without selecting implementation solutions.

## 5. Required Semantic Questions — Product Component / Runtime Non-conflation

The derived constraint set must preserve the fixed five Product Components while preventing implementation/runtime topology from redefining them.

At constraint level it must preserve at least:

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

Future runtime decomposition, package decomposition, service boundaries, database placement, and deployment layout must remain subordinate to accepted Product Component semantics rather than redefine them.

Do not derive actual Runtime Roles, processes, services, deployment units, package layouts, or database topology.

## 6. Required Semantic Questions — First-class Capability Non-subordination

The derived constraint set must preserve the four principal product capability domains as:

```text
FIRST_CLASS
PARALLEL
NON_SUBORDINATE
```

It must prevent:

```text
Cross-domain Composition -> Authority Transfer
Shared Implementation -> Authority Transfer
Shared Runtime -> Authority Transfer
Shared Database -> Source-of-Truth Transfer
Data Processing -> Business Authority Transfer
Automation Execution -> Universal Execution Semantic Ownership
AI Agent Invocation -> Universal Capability Ownership
```

The constraint may require explicit future authority/SoT allocation, but must not itself assign those authorities to concrete components or domains unless already fixed by the accepted Constitution.

## 7. Required Semantic Questions — Definition / Artifact / Runtime Separation

The derived constraint set must preserve distinct semantic states for:

```text
Development Definition
Domain Semantic Certification
Accepted Artifact
Installation
Activation
Formal Execution Admission
Runtime Execution Attempt
```

It must constrain later architecture so capability to load/execute something does not itself constitute certification, artifact acceptance, installation, activation, admission, or authorization.

It must prevent formal production execution from treating mutable working source, unpublished definition, unchecked dynamic code, or unaccepted packages as accepted executable artifacts merely through implementation convenience.

Do not choose artifact format, registry, signing implementation, package manager, database model, deployment mechanism, activation mechanism, admission engine, or concrete lifecycle state machine beyond the invariant separation required at constraint level.

## 8. Required Semantic Questions — Terminal / Local Execution Authority and Source-effect Governance

Build on accepted `NSE-001..004`, especially `NSE-004`, without reopening them.

The derived constraint set must preserve at least:

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

It must preserve source-fact production, protected-effect accountability, provenance, recovery, reconnection, and reconciliation handoff obligations while leaving concrete authority placement and reconciliation mechanisms for later architecture.

Do not choose local database, cache provider, grant format, credential design, authorization engine, audit store, scheduler, worker, synchronization protocol, runtime topology, or recovery algorithm.

## 9. Interaction with Accepted NSE-001..004

All candidate constraints produced in this batch MUST conform to and preserve:

```text
NSE-001 Native Tenant Semantic Invariance
NSE-002 Tenant / Organization Semantic Non-collapse
NSE-003 Organization Structural Plurality and Extensibility
NSE-004 Offline Core Correctness and Governance Invariance
```

No Batch 2 constraint may weaken Tenant scope, collapse Organization into Tenant, narrow Organization structural plurality, or convert offline/local execution into a governance bypass.

## 10. Constraint Record Requirements

Every produced candidate Architecture Constraint must use the accepted `NSE-###` namespace and include at least:

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

ID allocation rules:

- current globally accepted IDs are `NSE-001..004`;
- allocate monotonically only for constraints actually produced by this session;
- do not reserve unused future IDs;
- do not predetermine the final constraint count;
- candidate IDs become normative only after independent GAC acceptance.

## 11. Decision Governance

Every material derivation issue must be classified as exactly one of:

```text
INHERITED_FACT
DAD
MDE
```

If a derivation issue would choose or materially redefine Semantic Ownership, Source of Truth, Actual-state Ownership, Acceptance/Admission/Selection/Execution Authority, Tenant/Organization/Principal/IAM/Policy/Security Authority, stable identity, major compatibility/history semantics, offline fail-open/fail-closed policy, protocol/storage/provider lock-in, or another high-cost long-term commitment, it is MDE-class.

If uncertain:

```text
DEFAULT → MDE
```

For an MDE:

1. stop dependent derivation;
2. handle only one material MDE at a time;
3. present the Project Owner exactly three mutually exclusive durable options A/B/C;
4. provide recommendation, rationale, benefits, costs, and long-term impact;
5. do not auto-select;
6. persist Owner Decision evidence before downstream consumption.

## 12. Strict Forbidden Scope

This session MUST NOT begin or decide:

```text
Project Architecture
Actual Product Component internal architecture
Actual Runtime Role set
Process / Service / Container / Deployment topology
IAM / Policy architecture solution
Tenant / Organization solution beyond accepted NSE-001..004
Database model/topology/product
Artifact registry implementation
Artifact format/signing implementation
Activation/admission engine implementation
Task/workflow definition model
Queue / broker / scheduler / worker model
Shared Foundation detailed design
Stable cross-boundary Contract derivation except as a referenced boundary
Extension / re-delivery Constraint derivation except as a referenced boundary
Foundation Contract / Module / Provider design
Implementation Planning
IWP
Coding
```

## 13. Explicit Deferred Pressure

The following remains outside this batch unless referenced only as an interaction boundary:

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

Do not claim global Constraint Exhaustion in this session.

## 14. Required Audits

Before completion, execute at least:

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
RUNTIME_BOUNDARY_AMBIGUITY_REVIEW
SOURCE_EFFECT_RESPONSIBILITY_REVIEW
OFFLINE_PRIVATE_CORRECTNESS_REVIEW
GIT_DRIFT_REVIEW
```

Also perform a batch pressure-closure assessment distinguishing:

```text
Authorized pressure closed by candidate constraints
Authorized pressure still open
Newly discovered out-of-scope pressure
Deferred known pressure
```

## 15. Exit Gate

The bounded session may reach `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE` only when:

```text
All produced constraints have complete required records
Authorized batch pressure has no unresolved blocking semantic gap
Accepted NSE-001..004 remain preserved
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
Unexpected Drift = NONE
Unauthorized Progression = NONE
```

If the authorized cluster cannot be closed without an MDE or upstream clarification, stop with the exact blocking condition instead of claiming completion.

## 16. Required Repository Deliverables

At minimum persist:

1. candidate Architecture Constraint document(s) actually derived by this batch;
2. a new candidate Constraint Index revision based on accepted Index `0.0.2`, without rewriting it;
3. any DAD/MDE/Owner Decision evidence created within scope;
4. Batch 2 review/audit evidence;
5. Batch 2 Session Handoff Package.

## 17. Required Handoff Fields

The handoff must include:

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

## 18. Stop Rule

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

The session MUST NOT self-accept, authorize another batch, globally close Constraint Derivation, or begin Project Architecture.
