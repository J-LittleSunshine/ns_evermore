# ns_evermore Unified Governance Baseline

## Current Authority

- **Version:** `0.0.2`
- **Status:** `OWNER_DECIDED / GAC_RECOGNIZED / NORMATIVE`
- **Program:** `NGRP-001`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Effective Governance Transition:** current Global State transition that activates this revision

This document is the **single current governance baseline** for decision authority, design quality, derivation order, session governance, continuity/recovery, document authority, implementation planning, IWP/Codex boundaries, and Product Owner capability review.

It consolidates the current semantics previously distributed across:

- `docs/governance/ns_evermore_genesis_governance_framework_0.0.1.md`;
- `docs/governance/decisions/ns_evermore_decision_authority_model_0.0.1.md`;
- `docs/governance/global_architecture/ns_evermore_global_architecture_continuation_protocol_0.0.1.md`;
- `docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md`;
- `docs/governance/standards/ns_evermore_implementation_governance_standard_0.0.1.md`.

Those files remain historical governance evidence. They are no longer separate current mandatory governance inputs once the Global State activates this revision.

This consolidation does **not** change accepted Product Component topology, accepted `NSE`, accepted architecture semantics, or current Batch 2 scope.

---

# 1. Governance Principle

The project uses:

```text
Product Owner
→ product-defining and MDE-class decisions

Global Architecture Coordinator / GAC
→ classification, escalation enforcement, independent acceptance,
   phase authorization, continuity, drift, exhaustion/readiness gates

Authorized Architecture / Design Session
→ DADs inside exact accepted scope

Implementation Planning / IWP / Codex
→ implementation freedom left by Accepted Design only
```

Permanent invariants:

```text
Delegation != Loss of Owner Authority
Delegation != Reduced Design Depth
Implementation Freedom != Architecture Authority
Directory Layout != Architecture Boundary
Library Choice != Architecture Identity automatically
Accepted Architecture != Silently Overridable
```

---

# 2. Decision Classification

Every material formal design decision is classified before freezing as:

```text
INHERITED_FACT
DAD
MDE
```

## 2.1 INHERITED_FACT

May come only from accepted Project Owner root facts, accepted Constitution, accepted Constraints, accepted Architecture/Contract, accepted Owner decisions, or accepted gates.

```text
NO DOWNSTREAM VOTE
NO SILENT REOPEN
MUST CONSUME EXACTLY
```

## 2.2 DAD

An authorized design session may decide a DAD only when the matter:

- is inside its exact scope;
- is derivable from accepted upstream authority;
- does not materially change an MDE category;
- records relevant alternatives/tradeoffs;
- is persisted with enough traceability for independent review.

Typical DADs include non-semantic internal module decomposition, replaceable abstraction arrangement, package grouping, directory layout without architecture impact, and replaceable provider/module choices that do not create material lock-in.

## 2.3 MDE

The Project Owner decides any material matter involving or changing:

```text
major Product Capability Boundary
Semantic Ownership
Source of Truth
Actual-state Ownership
Acceptance / Admission / Selection / Execution / Business Authority
Tenant / Organization / Principal / IAM / Policy / Security / Trust Authority
major stable identity commitment
major externally observable compatibility commitment
major historical interpretation commitment
material offline fail-open / fail-closed policy
major vendor/provider/language/framework/protocol/storage/artifact-format lock-in
high migration cost
multiple materially valid long-term choices with significant tradeoffs
```

If classification is uncertain:

```text
DEFAULT → MDE
```

For an MDE, process **one material decision at a time**. Present the Project Owner three mutually exclusive durable options `A / B / C` with recommendation, rationale, benefits, costs, and long-term impact. Do not auto-select. Persist the Owner decision before downstream consumption.

The Project Owner may explicitly reserve an unresolved DAD or implementation-level decision before it is finalized. Accepted material cannot be overridden merely by a later chat instruction; formal reopen/supersession/impact/revalidation applies.

---

# 3. Product Capability Authority and Owner Capability Checkpoint

Product capability scope is not treated as an ordinary implementation detail.

Before a Product Component enters **Component Internal Design**, its current Component Architecture/Design artifact MUST contain a capability inventory sufficient to answer what the component is expected to do as a product component.

Use the following statuses; separate numeric capability IDs are optional unless later traceability actually requires stable cross-document identity:

```text
INHERITED_REQUIRED
→ already required by Constitution / accepted upstream design
→ do not ask the Owner again

DERIVED_REQUIRED
→ supporting capability necessarily implied by accepted semantics
→ may be derived by authorized design session as DAD if not MDE-class

OWNER_DECISION_REQUIRED
→ material product function not already fixed upstream
→ Project Owner decides before internal design depends on it

DEFERRED
→ intentionally not decided in current scope

NON_GOAL
→ explicitly excluded from the component/product scope
```

## 3.1 What must return to the Project Owner

Ask the Project Owner when a proposed capability materially changes what the component/product can do, its market/product boundary, a major capability authority, major externally observable behavior, or a major long-term commitment.

Examples include questions such as whether a component supports a new major builder/runtime mode, a new first-class interaction model, a new major Agent capability, a major application-construction capability, or another product-significant feature not already required upstream.

The design session MUST NOT silently infer a product feature merely because a framework/library can implement it.

## 3.2 What is not re-asked

If the accepted Constitution already requires a capability, it is `INHERITED_REQUIRED`.

For example, accepted root capabilities such as `ns_node` OCR/browser/desktop automation/plugin/local execution and `ns_agent` model-provider/tool/context/memory/RAG/agent-runtime capabilities are consumed rather than re-voted.

## 3.3 What design sessions may derive

Supporting functions that are necessary to realize an already accepted capability, but do not materially expand product scope or change MDE dimensions, may be derived as DAD.

## 3.4 Owner Capability Checkpoint

Before internal module decomposition becomes normative:

```text
Component Responsibility Boundary
→ Component Capability Inventory
→ Owner Capability Checkpoint for OWNER_DECISION_REQUIRED items
→ Accepted Component Capability Baseline
→ Component Internal Architecture
→ Modules / Contracts / Detailed Design
```

This checkpoint is mandatory but does not require a separate standalone document or a separate ID namespace. It may live inside the component architecture/design artifact and its acceptance evidence.

---

# 4. Component Internal Design Authority

Component Internal Design is delegated by default **inside accepted Product Component and capability boundaries**.

Return to the Project Owner / MDE when internal design materially determines or changes:

```text
Authority
Semantic Ownership
Source of Truth
Actual-state Ownership
Trust Boundary
Tenant / Organization semantics
major lifecycle semantics
major compatibility
major protocol/provider/framework/storage lock-in
high migration cost
```

An authorized design session may decide ordinary internal module boundaries, non-semantic service/class organization, internal interface decomposition, replaceable adapter arrangements, package grouping, and dependency direction when these do not redefine accepted architecture.

---

# 5. Repository / Directory / Package Structure

Repository structure is normally a DAD or Implementation Planning concern, not a Product Architecture authority.

Typical delegated questions include:

```text
src layout
tests layout
Python package layout
frontend folder layout
contract file placement
tooling folder placement
internal module file organization
```

Permanent rules:

```text
Directory Placement != Architecture Boundary
Python Package != Product Component
Django App != Architecture Authority
Vue Component != Product Component
```

If a layout proposal actually changes Product Component boundaries, Authority, Source of Truth, Trust Boundary, Runtime Responsibility, or stable Contract ownership, reclassify it under Architecture governance and MDE where applicable.

---

# 6. Technology Decision Authority

Already frozen technology facts remain inherited:

```text
Project direction → PYTHON-FIRST
ns_server → Python + Django
ns_runtime → Python + WebSocket-centered communication
ns_node → Python
ns_agent → Python
ns_web → Vue 3 + TypeScript
```

A replaceable library/provider/implementation may be delegated when it:

- conforms to accepted Contract/Module/Provider boundaries;
- does not become architecture identity;
- does not change Authority / SoT;
- does not impose material externally observable commitment;
- does not create major long-term lock-in or high migration cost;
- preserves offline/private, security, supply-chain, compatibility, and conformance requirements.

Escalate to MDE when a technology choice materially creates or changes vendor/provider/language/framework/protocol/storage/artifact-format lock-in, security/trust model, Authority/SoT, major compatibility surface, major operational dependency, or high migration cost.

---

# 7. Mandatory Semantic Resolution

Every applicable Architecture / Constraint / Contract / Module must explicitly close or explicitly defer to the correct later design authority:

```text
Identity / Namespace
Revision / Evolution
Authority
Semantic Ownership
Source of Truth
Actual-state Ownership
State / Lifecycle
Temporal Semantics
Failure / Unknown / Indeterminate
Tenant
Organization
Principal
Authentication
Authorization / Policy
Security
Data / Privacy / Trust
Serialization / Representation
Offline / Degraded
Recovery / Reconciliation
Compatibility
Migration
Conformance
Cross-boundary Dependency
Invariant
Decision Traceability
Revalidation Trigger
```

`NOT_APPLICABLE` requires rationale. `DEFERRED` must identify the later authority/phase and cannot become implementation-defined escape.

Design completeness is judged by semantic resolution depth, not document/line/decision count.

---

# 8. Mandatory Review Gates

Each bounded Architecture/Constraint/Contract/Module session applies the relevant subset of:

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
FORMAL_COMPONENT_TO_RUNTIME_MAPPING_REVIEW
SOURCE_EFFECT_RESPONSIBILITY_REVIEW
OFFLINE_PRIVATE_CORRECTNESS_REVIEW
FAILURE_RECOVERY_RESPONSIBILITY_REVIEW
GIT_DRIFT_REVIEW
```

Exit requires, where applicable:

```text
Open MDE = 0
Unpersisted Owner Decision = 0
Missing/Ambiguous Normative Dimension = 0
Implementation-defined Escape = 0
Unmapped Material Decision = 0
Multiple-final-authority Ambiguity = 0
Source-of-Truth Ambiguity = 0
Tenant / Organization Collapse = 0
Dependency / Invariant Conflict = 0
Unauthorized Downstream Design Leakage = 0
Unexpected Drift = NONE
Unauthorized Progression = NONE
```

---

# 9. Derivation Order

The legal top-level order remains:

```text
Constitution
→ Architecture Constraint Derivation
→ Project Architecture
→ Five-component Internal Architecture Boundaries
→ Runtime Responsibility Architecture
→ Architecture Exhaustion / Readiness
→ Shared Foundation Architecture
→ Foundation Contracts
→ Foundation Modules
→ Provider Design
→ Component Internal Design
→ Design-to-Implementation Readiness
→ Implementation Planning
→ IWP
→ Codex Implementation
→ Verification
```

Completion does not automatically authorize the next phase.

A downstream phase that discovers missing upstream semantics MUST stop and return the gap to the correct authority.

---

# 10. Constraint Governance

Architecture Constraints precede Project Architecture and MUST NOT be architecture solutions.

Use stable `NSE-###` IDs only for constraints actually produced. Do not reserve future IDs, batch count, or total constraint count.

Global Constraint Derivation closes only after GAC runs a Constraint Exhaustion Assessment and finds:

```text
Remaining Material Constraint Pressure = NONE_FOUND
Open MDE = 0
Blocking Semantic Gap = 0
```

---

# 11. Repository Continuity and Recovery

```text
Chat is temporary.
Repository is project memory.
Accepted Repository evidence is authority.
```

Every fresh GAC or bounded session begins by resolving the actual branch HEAD and recovering current state from Repository evidence.

The recovery sequence is:

```text
1. Resolve repository / branch / actual HEAD.
2. Read current Constitution.
3. Read this Unified Governance Baseline.
4. Read current Global Architecture State.
5. Consume the Current Required Read Set embedded in Global State.
6. Read Global Architecture Working State.
7. Read relevant Ledger tail / acceptance / decision evidence required by State.
8. Compare State Verified Through HEAD to actual HEAD.
9. Classify every later delta:
   EXPECTED_PHASE_EVIDENCE
   EXPECTED_GOVERNANCE
   OWNER_DECISION_EVIDENCE
   WORKING_CHECKPOINT
   UNAUTHORIZED_PROGRESSION
   UNEXPLAINED_DRIFT
10. Reconstruct current accepted baseline, current authorization,
    Open MDE, pending Owner decisions, blocking items, drift,
    candidate-vs-normative state, and unique next legal action.
11. Only then perform authorized work.
```

If recovery is inconsistent:

```text
STOP
→ DRIFT / CONTINUITY RECONCILIATION
```

The dedicated historical `GACP-001` file remains evidence of the Genesis bootstrap protocol; this section is the current consolidated recovery rule.

---

# 12. Current Required Read Set Mechanism

A separate Current Required Read Set document is **not required**.

The current Global Architecture State MUST contain a `Current Required Read Set` section listing the minimum sufficient current artifacts for the authorized action.

Historical `ns_evermore_current_required_read_set_*.md` files remain continuity evidence but are not the current mechanism after this governance revision.

Only expand into superseded/pre-Genesis history for reopen, conflict, divergence, evidence ambiguity, cross-phase collision, drift investigation, or explicit compatibility/migration work.

---

# 13. Session Authorization Model — No Repository Prompt Documents Required

Repository-backed **authorization facts are mandatory**; repository-backed chat prompt documents are not.

Current authorization is carried by:

```text
Global Architecture State
+ accepted upstream evidence
+ current pressure/authorization decision evidence where applicable
+ Unified Governance Baseline
```

Global State MUST record at least:

```text
Current Authorized Phase
Authorization Scope
Authorized Material Pressure / Objective
Explicit Deferred / Forbidden Scope
Entry / recovery rule
Open MDE / pending Owner decision / blocking status
Exit / stop condition
Unique Next Legal Action
Current Required Read Set
```

The user-facing/new-chat prompt is:

```text
CHAT BOOTSTRAP TEXT
→ generated from current Repository authority
→ disposable delivery mechanism
→ NOT a normative Repository artifact
→ no Prompt ID required
```

Past `docs/session_prompts/*.md` files remain historical authorization evidence for their prior epochs. No new session prompt document is required under this revision unless the Project Owner explicitly requests one.

---

# 14. Bounded Session and Handoff Model

A producing Architecture/Design session cannot self-accept.

Maximum producing-session state:

```text
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
→ STOP
→ RETURN TO GAC
```

Each bounded session persists enough handoff/review evidence to reconstruct:

```text
Phase / scope
Recovered entry HEAD
Evidence HEAD / commits
Changed files
Decisions / MDE / Owner choices
Created candidate artifacts
Preserved invariants
Audits
Deferred/new pressure
Drift / unauthorized progression
Acceptance recommendation
Stop condition
```

A separate Handoff ID is not required. Phase identity + artifact path + Git coordinate is sufficient unless a later traceability need justifies another stable ID.

GAC independently reviews and issues exactly one of:

```text
GLOBAL_ACCEPT
CORRECTION_REQUIRED
REJECT
```

Acceptance never automatically authorizes the next phase.

---

# 15. Document and Identifier Simplification

Use stable identifiers only when they provide real cross-document traceability value.

Current mandatory stable namespaces are limited to what the project actually needs, such as:

```text
NSE-###
GAC-EPOCH-####
GAC-TR-####        # ledger transition only
DAD / MDE IDs      # only for actual formal architecture decisions
IWP-###            # implementation work packages when implementation begins
```

Do **not** create extra IDs merely for:

```text
chat prompts
handoffs
ordinary review notes
routine governance clarifications
ordinary capability list entries
```

Document version + path + Git commit is normally sufficient for those artifacts.

Historical IDs created before this simplification remain valid evidence and are not renumbered.

---

# 16. Document Status and Supersession

Material accepted evidence is not silently overwritten.

Use new revision + explicit current-state supersession when changing accepted normative meaning.

Historical candidate/accepted snapshots may retain old status metadata; current authority is resolved through current Global State and acceptance/supersession evidence.

The current Global State identifies which revisions are current.

---

# 17. Implementation Planning / IWP / Codex

Formal Implementation Planning is forbidden until GAC issues:

```text
DESIGN_TO_IMPLEMENTATION_READY
```

Implementation Planning consumes Accepted Design and cannot create new Architecture Authority. If planning requires changing Authority, SoT, Product Component/Runtime boundary, Security/Trust, Tenant/Organization semantics, Contract semantics, or major lock-in:

```text
STOP
→ RETURN TO CORRECT DESIGN AUTHORITY
```

The future Implementation Master Plan must include accepted design baseline, repository/package structure, dependency graph/order, migration/testing/conformance/offline-build/release/rollback strategy, verification gates, and IWP index.

Each `IWP-###` must be bounded, verifiable, reversible, and contain exact design authority, scope, allowed/forbidden files, requirements, failure/security/Tenant/Organization/offline/observability/test/conformance requirements, acceptance criteria, Git evidence, and stop rule.

Codex implements Accepted Design. It may make local coding choices with no semantic effect, but MUST NOT decide Architecture, SoT, Tenant/Organization semantics, Product Component/Runtime boundaries, Contracts, Security/Policy bypasses, or major technology commitments.

If implementation exposes a design gap:

```text
STOP IMPLEMENTATION
→ RAISE DESIGN GAP
→ RETURN TO CORRECT DESIGN AUTHORITY
```

---

# 18. Current Governance Supersession

When activated by Global State, this `0.0.2` Unified Governance Baseline becomes the current governance source for the semantics consolidated here.

The following remain historical evidence and are no longer separately required current governance inputs:

```text
docs/governance/ns_evermore_genesis_governance_framework_0.0.1.md
docs/governance/decisions/ns_evermore_decision_authority_model_0.0.1.md
docs/governance/global_architecture/ns_evermore_global_architecture_continuation_protocol_0.0.1.md
docs/governance/standards/ns_evermore_session_governance_standard_0.0.1.md
docs/governance/standards/ns_evermore_implementation_governance_standard_0.0.1.md
```

Current Global State and accepted Architecture Constraints remain separate because they serve different authority functions and change at different cadences.
