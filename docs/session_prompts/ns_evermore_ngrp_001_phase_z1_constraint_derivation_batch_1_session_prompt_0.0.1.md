# NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 1 Session Authorization Prompt

## Authorization Metadata

```text
Session Prompt ID
NGRP-001-Z1-B1-AUTH-0001

Phase ID
NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 1

Repository
J-LittleSunshine/ns_evermore

Branch
architecture/ns-evermore-genesis-0.0.1

Authorization Scope
ARCHITECTURE_CONSTRAINT_DERIVATION_ONLY / BATCH_1 / TENANT_ORGANIZATION_OFFLINE_CORE_CONSTRAINTS

GAC Authorization Baseline HEAD
74fe0995cad29313ee01619be267a43db8f2b856

Entry HEAD Resolution Rule
At session start resolve actual branch HEAD through GACP-001. Every commit after the GAC Authorization Baseline HEAD must classify only as this authorization prompt or subsequent GAC state/ledger/read-set synchronization. Any other delta blocks design.
```

---

## 1. Session Identity

You are responsible only for the first bounded Architecture Constraint Derivation session of the new `ns_evermore` Genesis program.

You are **not** the Global Architecture Coordinator.

You may derive Architecture Constraints only from the accepted Genesis baseline and only inside the bounded pressure scope authorized below.

## 2. Mandatory Read Set

Before substantive derivation, read completely and consume exactly:

1. `docs/ns_evermore_genesis_constitution_0.0.1.md`
2. `docs/genesis/ns_evermore_genesis_source_manifest_0.0.1.md`
3. `docs/governance/ns_evermore_genesis_governance_framework_0.0.1.md`
4. `docs/ns_evermore_nse_constraints_index_0.0.1.md`
5. `docs/governance/decisions/ns_evermore_decision_registry_0.0.1.md`
6. `docs/governance/global_architecture/ns_evermore_global_architecture_continuation_protocol_0.0.1.md`
7. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z0_global_acceptance_0.0.1.md`
8. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
9. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
10. `docs/governance/global_architecture/ns_evermore_current_required_read_set_0.0.1.md`
11. `docs/architecture_reviews/ns_evermore_post_z0_constraint_pressure_assessment_0.0.1.md`
12. this Session Authorization Prompt.

Do not use pre-Genesis architecture documents as normative inputs. Historical material may be consulted only if the accepted provenance rules explicitly justify doing so, and it must remain clearly classified.

## 3. Entry Gate

Before deriving any constraint, verify and report:

```text
Repository reachable
Branch correct
Actual branch HEAD resolved
GACP-001 recovery complete
Current Global State Epoch = GAC-EPOCH-0003
Last Globally Accepted Phase = NGRP-001 Phase Z0
Current Authorized Phase = NGRP-001 Phase Z1 / Batch 1
Authorization Scope matches this prompt
Current accepted Constraint Baseline = BOOTSTRAP / ACTIVE_NSE NONE
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

This session may derive constraints only for the following root pressure cluster:

```text
A. Native Multi-tenancy
B. Tenant / Organization Non-collapse
C. Complex Extensible Organization
D. Offline Core Correctness
```

The objective is to convert these Project Owner / accepted-Constitution pressures into formal Architecture Constraints with sufficient semantic depth to constrain future Project Architecture without selecting implementation solutions.

## 5. Required Semantic Questions — Native Multi-tenancy

The derived constraint set must close, at constraint level rather than solution level, the material invariants needed to ensure:

- one core Tenant semantic model applies to single-customer private deployment and multi-customer deployment;
- Tenant Identity and Tenant boundary remain explicit even in single-tenant/private deployments;
- Tenant Authority, isolation, resource/data/secret/policy/audit/artifact/runtime scope cannot be bypassed by deployment mode;
- tenant-scoped semantics remain valid in fully intranet and fully offline operation;
- implementation convenience cannot introduce a non-Tenant special core path.

Do not choose database-per-tenant, schema-per-tenant, row-level tenant keys, namespace format, persistence topology, or concrete IAM/policy implementation.

## 6. Required Semantic Questions — Tenant / Organization Non-collapse

The derived constraint set must close the material invariants that preserve:

```text
Tenant != Organization
Tenant Boundary != Organization Boundary
Tenant Identity != Organization Identity
Tenant Membership != Organization Membership
Tenant Role != Organization Role automatically
```

It must constrain future IAM, Policy, Business Application, Automation, Agent, Data, Audit, and Runtime design so Organization context can be referenced without redefining Tenant security/resource boundaries.

Do not choose role tables, organization tables, permission schema, authorization engine, or database model.

## 7. Required Semantic Questions — Complex Extensible Organization

The derived constraint set must preserve the ability for one Tenant to contain multiple independent or related Organization systems and for later architecture to support, where applicable:

- parallel Organization structures;
- multi-level and multi-dimensional Organization;
- extensible Organization Type;
- extensible Relationship / Hierarchy / Dimension semantics;
- multiple membership;
- cross-organization mapping;
- external Organization identity/mapping;
- aliasing;
- historical Organization evolution.

The constraints must prevent future architecture from assuming one Tenant equals one Organization tree, one Person equals one Department, or one external system's hierarchy is globally canonical.

Do not choose tree, graph, adjacency, closure table, materialized path, graph database, relational schema, or a canonical organization persistence implementation.

## 8. Required Semantic Questions — Offline Core Correctness

The derived constraint set must close root correctness invariants for core operation without:

```text
Public Internet
Vendor SaaS control plane
Mandatory public registry
Mandatory online license authority
```

It must constrain later design so core build/test/package/install/run/upgrade/rollback/recovery remains possible offline and so optional Internet connectivity is never a correctness requirement.

It must also establish constraint-level invariants preventing local/offline/degraded execution from bypassing Tenant, Organization, Policy, Security, Artifact, Audit, or reconciliation obligations.

Do not choose concrete offline synchronization protocols, queues, local databases, certificate systems, license technology, package registries, or reconciliation algorithms.

## 9. Constraint Record Requirements

Every derived Architecture Constraint must use the accepted `NSE-###` namespace and contain at least:

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
Revalidation Trigger
Status
Acceptance Coordinate
```

ID allocation rules:

- allocate IDs monotonically from the current empty namespace only for constraints actually produced;
- do not reserve IDs for future batches;
- do not infer a predetermined final constraint count;
- candidate IDs become normative only after independent GAC acceptance.

## 10. Decision Governance

Every material derivation issue must be classified as exactly one of:

```text
INHERITED_FACT
DAD
MDE
```

A DAD may resolve only a derivation-structuring matter that does not alter material semantic authority, Source of Truth, major identity commitment, security/trust policy, externally visible commitment, high-cost lock-in, or other MDE category.

If uncertain:

```text
DEFAULT → MDE
```

If an MDE arises:

1. stop downstream derivation that depends on it;
2. handle only one material MDE at a time;
3. present Project Owner three mutually exclusive long-term-valid options A/B/C;
4. provide recommendation, rationale, benefits, costs, and long-term impact;
5. do not auto-select;
6. persist the Owner decision before consumption.

## 11. Strict Forbidden Scope

This session MUST NOT begin or decide:

```text
Project Architecture
IAM architecture solution
Policy architecture solution
Organization persistence/model solution
Data / Knowledge architecture solution
Runtime Architecture
Component internal architecture
Shared Foundation detailed design
Foundation Contracts
Foundation Modules
Provider selection
Database topology/schema
Queue / broker / scheduler / worker model
API endpoints
Django app/model decomposition
Frontend architecture
Implementation Planning
IWP
Coding
```

It also must not derive unrelated deferred constraint families except to record newly discovered pressure for GAC follow-up.

## 12. Explicit Deferred Constraint Pressure

The following remains outside this batch unless needed only as a referenced upstream/downstream interaction boundary:

```text
Definition / Artifact / Runtime separation
Stable language-neutral contracts
Extension / re-delivery
Fixed five-component topology implications beyond direct Tenant/Organization/offline interaction
First-class capability non-subordination
Terminal / local execution governance beyond offline-core invariants
Complete System + SDK
Bounded enterprise integration
Distribution / commercial optionality
Controlled technology exceptions
Shared Foundation provider replaceability
Cross-session continuity
Implementation derivability
Any newly discovered unrelated material pressure
```

Do not mark global Constraint Derivation complete in this batch.

## 13. Required Audits

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

## 14. Exit Gate

The session may reach `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE` only when:

```text
All produced constraints have complete required records
Authorized batch pressure has no unresolved blocking semantic gap
Open MDE = 0
Unpersisted Owner Decision = 0
Architecture Solution Leakage = 0
Project Architecture Leakage = 0
Missing required constraint dimension = 0
Ambiguous normative requirement = 0
Implementation-defined escape introduced by constraints = 0
Tenant / Organization collapse = 0
Dependency / invariant conflict = 0
Unexpected Drift = NONE
Unauthorized Progression = NONE
```

If the authorized cluster cannot be completely closed without an MDE or upstream clarification, stop with the exact blocking condition instead of claiming completion.

## 15. Required Repository Deliverables

At minimum persist:

1. candidate Architecture Constraint document(s) for this batch;
2. updated candidate Constraint Index reflecting only produced constraints and their candidate state;
3. any DAD/MDE/Owner Decision evidence created within scope;
4. Batch 1 review/audit evidence;
5. Batch 1 Session Handoff Package.

Do not rewrite accepted Z0 documents merely to restate them.

## 16. Required Handoff Fields

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
Preserved Invariants
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

## 17. Stop Rule

Maximum terminal state of this bounded session:

```text
NGRP-001 Phase Z1 / Batch 1
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

Then:

```text
STOP
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```

The session MUST NOT self-accept, authorize another batch, globally close Constraint Derivation, or begin Project Architecture.
