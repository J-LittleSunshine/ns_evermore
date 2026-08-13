# NGRP-001 Phase Z3 / Batch 2 — Interaction Experience Capability Discovery Candidate

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Global State at Entry:** `GAC-EPOCH-0022`
- **Candidate Status:** `CANDIDATE / PRODUCING_SESSION_COMPLETE / AWAITING_GLOBAL_ACCEPTANCE`
- **Global Acceptance:** `NOT CLAIMED`
- **Open MDE:** `0`
- **Unpersisted Owner Decision:** `0`

---

## 1. Purpose and Bounded Authority

This candidate records the interaction-experience capability pressure discovered for:

```text
End User
Operator / Administrator
Developer / Delivery / Integrator
Human-in-the-loop participant
```

across the accepted five-component project architecture and accepted Z3 Batch 1 capability baseline.

It is limited to capability discovery and classification. It does **not** perform Five-component Internal Boundary Synthesis, Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Architecture, Foundation Contract/Module/Provider Design, Implementation Planning, IWP or Coding.

This candidate SHALL NOT be interpreted as Global Acceptance, GAC Epoch advancement, authorization of Z3 Batch 3, or a producing-session claim that Five-component capability discovery is globally exhaustive/readiness-complete.

---

## 2. Authority Preservation Rules

All interaction capabilities in this candidate preserve the accepted authority topology.

In particular:

```text
ns_web
→ human-facing projection / interaction surface
→ NOT canonical Product Definition SoT
→ NOT Runtime Actual-state Authority
→ NOT Policy Authority
→ NOT Artifact Acceptance Authority
→ NOT Execution Admission Authority

System-level SDK / source tooling
→ authoring / validation / trial / discovery consumer surface
→ NOT Product Definition Authority by virtue of authoring

Human Task Inbox
→ human-work discovery / interaction projection
→ NOT Policy Authority
→ NOT Artifact Acceptance Authority
→ NOT Execution Admission Authority

Notification Center / external push
→ awareness projection / delivery capability
→ NOT source fact
→ NOT current-state SoT

Cross-domain Discovery
→ governed discovery projection
→ NOT Universal Resource SoT

Accessibility / Localization
→ presentation and interaction capabilities
→ NOT semantic authority
```

Accepted canonical authority/SoT remains unchanged, including:

```text
Tenant Semantic Authority / Tenant Canonical SoT
→ ns_server

IAM Semantic Authority
→ ns_server

Policy Semantic Authority
→ ns_server

Business Application Definition Canonical SoT
→ ns_server

Automation Definition / Workflow Semantic Authority and Canonical SoT
→ ns_server

Native AI Agent Definition / Semantic Authority and Canonical SoT
→ ns_agent

Data / Knowledge / ETL Semantic Authority
→ ns_server

Formal Artifact Acceptance Authority
→ ns_server

Formal Execution Admission Authority
→ ns_server

Runtime Actual-state
→ exactly one final owner for the same bounded runtime assertion
→ system-level views remain derived projections
```

---

## 3. Classification Vocabulary

Each capability pressure below is classified exactly once as one of:

```text
INHERITED_REQUIRED
DERIVED_REQUIRED
OWNER_DECISION_REQUIRED
DEFERRED
NON_GOAL
```

`OWNER_DECISION_REQUIRED` entries in this candidate are already resolved and persisted; none remains open.

---

# 4. Owner Decisions Consumed by This Candidate

## Z3-B2-OD-001 — Source / Visual Authoring Interoperability

- **Classification:** `OWNER_DECISION_REQUIRED`
- **MDE:** `YES`
- **Selected:** `B`
- **Result:** `BIDIRECTIONAL_SEMANTIC_INTEROPERABILITY_WITHOUT_LOSSLESS_REPRESENTATION_ROUNDTRIP_REQUIRED`
- **Evidence:** `docs/governance/decisions/ns_evermore_z3_batch_2_source_visual_interoperability_owner_capability_decision_0.0.1.md`

Normative product boundary:

```text
Source-authored Definition
↔ governed domain semantics
↔ Visual-authored Definition

Bidirectional Semantic Interoperability
→ REQUIRED

Semantic Loss / Silent Information Destruction
→ PROHIBITED

Source formatting/comments/code organization
→ NOT guaranteed round-tripped

Visual layout/surface-local editor metadata
→ NOT guaranteed round-tripped

Lossless representation round-trip
→ NOT REQUIRED
```

Unsupported cross-surface representation SHALL be explicit as `UNSUPPORTED`, `NON_EDITABLE`, `REPRESENTATION_LIMITATION` or equivalent governed semantics rather than silently dropping meaning.

## Z3-B2-OD-002 — Unified Governed Human Task Inbox

- **Classification:** `OWNER_DECISION_REQUIRED`
- **MDE:** `NO`
- **Selected:** `B`
- **Result:** `UNIFIED_GOVERNED_HUMAN_TASK_INBOX_REQUIRED`
- **Evidence:** `docs/governance/decisions/ns_evermore_z3_batch_2_unified_human_task_inbox_owner_capability_decision_0.0.1.md`

Normative product boundary:

```text
What needs my action?
→ unified Human Task capability

Human Task Inbox
!= Generic Notification Center
!= System Alert Center
!= Policy Authority
!= Artifact Acceptance Authority
!= Execution Admission Authority
```

## Z3-B2-OD-003 — Governed Operation Intervention

- **Classification:** `OWNER_DECISION_REQUIRED`
- **MDE:** `NO`
- **Selected:** `B`
- **Result:** `UNIFIED_GOVERNED_OPERATION_INTERVENTION_WITH_CAPABILITY_SPECIFIC_SUPPORT_REQUIRED`
- **Evidence:** `docs/governance/decisions/ns_evermore_z3_batch_2_governed_operation_intervention_owner_capability_decision_0.0.1.md`

Normative product boundary:

```text
Possible intervention classes
→ Cancel Request
→ Retry Request
→ Resume Request
→ Recovery Request

Support
→ capability-specific

Cancel Requested != Cancelled
Retry Requested != Retry Started
Retry != Prior Attempt Erased
Recovery Requested != State Restored
Reconnect != Reconciled
```

## Z3-B2-OD-004 — Governed Pre-production Trial

- **Classification:** `OWNER_DECISION_REQUIRED`
- **MDE:** `NO`
- **Selected:** `B`
- **Result:** `GOVERNED_PRE_PRODUCTION_TRIAL_WITH_DOMAIN_APPROPRIATE_BOUNDED_MODES_REQUIRED`
- **Evidence:** `docs/governance/decisions/ns_evermore_z3_batch_2_governed_pre_production_trial_owner_capability_decision_0.0.1.md`

Applies to all four complete authoring domains:

```text
Business Application
Automation
Native AI Agent
Data / Knowledge / Foundational ETL
```

Core separation:

```text
Definition Valid != Trial Successful
Trial Successful != Artifact Accepted
Trial Successful != Production Execution Admitted
Trial Execution != Production Execution automatically
```

Universal fully isolated simulation is not required.

## Z3-B2-OD-005 — Governed Notification + External Delivery

- **Classification:** `OWNER_DECISION_REQUIRED`
- **MDE:** `YES`
- **Selected:** `B`, with explicit Owner supplement
- **Result:** `CHANNEL_NEUTRAL_GOVERNED_NOTIFICATION_WITH_REQUIRED_PLUGGABLE_EXTERNAL_DELIVERY`
- **Evidence:** `docs/governance/decisions/ns_evermore_z3_batch_2_governed_notification_external_delivery_owner_capability_decision_0.0.1.md`

Normative product boundary:

```text
What happened that I should know about?
→ governed Notification / Awareness capability

Notification != Human Task
Notification != Source Fact
Notification Center != Runtime Actual-state Owner
Notification Read != Problem Resolved
Delivery Success != User Actually Observed
```

External push capability is REQUIRED through pluggable/adaptable channels. Explicit target integration directions include:

```text
Feishu / 飞书
WeCom / 企业微信
SMS / 短信
```

Exact provider API, vendor, credential protocol and adapter implementation remain deferred. No external notification provider becomes a core-correctness dependency.

## Z3-B2-OD-006 — Unified Governed Cross-domain Resource Discovery

- **Classification:** `OWNER_DECISION_REQUIRED`
- **MDE:** `NO`
- **Selected:** `B`
- **Result:** `UNIFIED_GOVERNED_CROSS_DOMAIN_RESOURCE_DISCOVERY_REQUIRED`
- **Evidence:** `docs/governance/decisions/ns_evermore_z3_batch_2_unified_resource_discovery_owner_capability_decision_0.0.1.md`

Core boundary:

```text
Unified Discovery → REQUIRED
Authorization-aware → REQUIRED
Tenant-aware → REQUIRED
Private / Offline → REQUIRED

Discovery Result != Resource SoT
Discovery Index != Canonical Registry
Search Result Freshness != Guaranteed Current Actual-state
Universal AI Semantic Search != implied
```

## Z3-B2-OD-007 — Internationalization and Localization

- **Classification:** `OWNER_DECISION_REQUIRED`
- **MDE:** `NO`
- **Selected:** `B`
- **Result:** `FIRST_CLASS_INTERNATIONALIZATION_AND_PLUGGABLE_MULTI_LANGUAGE_LOCALIZATION_REQUIRED`
- **Evidence:** `docs/governance/decisions/ns_evermore_z3_batch_2_internationalization_localization_owner_capability_decision_0.0.1.md`

Core boundary:

```text
Stable product semantics → LANGUAGE_NEUTRAL
Product-owned human-facing messages → LOCALIZABLE
Multiple locales → SUPPORTED
Exact initial language set → DEFERRED
User business content auto-translation → NOT IMPLIED
Online translation SaaS → NOT CORE DEPENDENCY
Locale != Tenant != Principal Identity != Timezone
```

## Z3-B2-OD-008 — Accessibility Baseline

- **Classification:** `OWNER_DECISION_REQUIRED`
- **MDE:** `NO`
- **Selected:** `B`
- **Result:** `FIRST_CLASS_ACCESSIBILITY_AND_ACCESSIBLE_CRITICAL_WORKFLOW_COMPLETION_PATH_REQUIRED`
- **Evidence:** `docs/governance/decisions/ns_evermore_z3_batch_2_accessibility_owner_capability_decision_0.0.1.md`

Core boundary:

```text
Critical Human-facing Workflow
→ accessible semantic completion path REQUIRED

Semantic Interaction Parity
→ REQUIRED

Visual Presentation / Gesture Parity
→ NOT REQUIRED

Pointer-only Critical Operation
→ PROHIBITED

Color-only Critical Meaning
→ PROHIBITED
```

---

# 5. End-user Interaction Capability Inventory

| Capability | Classification | Capability Boundary |
|---|---|---|
| Governed operation identity and correlation | `DERIVED_REQUIRED` | A user-visible asynchronous/long-running action must remain referable across acknowledgement, observation, intervention, result and history. |
| Submission acknowledgement distinct from execution outcome | `DERIVED_REQUIRED` | Request received/created/accepted/admitted/started/completed remain semantically distinct where applicable. |
| Return-later / cross-session re-observation | `DERIVED_REQUIRED` | Closing browser/session does not cancel durable work; applicable operations/tasks/results can be re-observed later. |
| Operation history and result retrieval | `DERIVED_REQUIRED` | Completed/failed/partial/unknown outcomes remain discoverable according to retention/authorization. |
| Lifecycle and uncertainty presentation | `DERIVED_REQUIRED` | `UNKNOWN`, `INDETERMINATE`, `UNAVAILABLE`, `UNREACHABLE`, `STALE`, `CONFLICTING`, `PARTIALLY_APPLIED`, `RECONCILIATION_PENDING` and applicable vocabulary cannot be collapsed to false success/failure certainty. |
| Unified Human Task Inbox | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-002. |
| Unified Notification / Awareness | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-005. |
| External notification push | `OWNER_DECISION_REQUIRED` | REQUIRED pluggable delivery; Feishu/WeCom/SMS explicit targets. |
| Cross-domain Resource Discovery | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-006. |
| Timezone-aware temporal presentation | `DERIVED_REQUIRED` | Historical/current time-bearing interaction must identify/retain enough temporal context to avoid timezone ambiguity. |
| Internationalization/localization | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-007. |
| Accessibility for critical workflows | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-008. |
| Authorization/privacy-aware projection | `DERIVED_REQUIRED` | Human-facing surfaces may reveal only data/resources/diagnostics permitted by Tenant/Principal/Policy context. |
| Cross-surface semantic consistency | `DERIVED_REQUIRED` | State/error/revision/operation identity/compatibility/governance meaning cannot change merely because the user changes UI/SDK/CLI surface. |

---

# 6. Operator / Administrator Interaction Capability Inventory

| Capability | Classification | Capability Boundary |
|---|---|---|
| Component / Node / provider health and reachability visibility | `INHERITED_REQUIRED` | Consumes governed health/readiness/evidence without becoming Actual-state Authority. |
| Desired / Applied / Observed configuration interaction | `DERIVED_REQUIRED` | The UI/operator surface must preserve `Desired != Applied != Observed`; partial application and unknown actual state remain explicit. |
| Configuration rollout/history visibility | `DERIVED_REQUIRED` | Operators can inspect intent, applicable applied evidence and observation/history without canonicalizing by newest timestamp. |
| Layered diagnostics | `DERIVED_REQUIRED` | End-user explanation, operator diagnostic detail and developer correlation/trace may expose different authorized depth over the same governed evidence. |
| Recovery/reconciliation visibility | `DERIVED_REQUIRED` | Reconnect, recovery evidence, reconciliation pending/conflict/staleness and final outcome remain distinct. |
| Governed operation intervention | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-003; support is capability-specific. |
| Audit/provenance navigation | `DERIVED_REQUIRED` | Applicable operation/task/notification/trial/configuration events retain principal/Tenant/revision/correlation provenance where required. |
| Governance interaction surfaces | `DERIVED_REQUIRED` | Human-facing governance interaction can request/observe accepted lifecycle actions but does not become the underlying authority. |
| Operational awareness notification | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-005. |
| Cross-domain operational discovery | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-006. |
| Sensitive diagnostic redaction | `DERIVED_REQUIRED` | Secrets, protected credentials and unauthorized sensitive content are not exposed merely for diagnostic convenience. |

---

# 7. Developer / Delivery / Integrator Capability Inventory

| Capability | Classification | Capability Boundary |
|---|---|---|
| Complete source/SDK authoring for four domains | `INHERITED_REQUIRED` | Accepted Z3 Batch 1 baseline. |
| Complete visual authoring for four domains | `INHERITED_REQUIRED` | Accepted Z3 Batch 1 baseline through `ns_web`. |
| Source↔Visual semantic interoperability | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-001; semantic loss prohibited, representation losslessness not guaranteed. |
| Validation / conformance / compatibility feedback | `INHERITED_REQUIRED` | SDK/visual authoring must surface applicable validation, conformance and compatibility results. |
| Governed pre-production trial | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-004. |
| Revision identity/history | `DERIVED_REQUIRED` | Authoring and execution interaction must preserve the revision actually authored/accepted/trialed/executed where applicable. |
| Revision comparison / semantic diff capability | `DERIVED_REQUIRED` | Users/developers must be able to compare revisions at a semantic level sufficient to understand governed change; exact diff algorithm/representation is deferred. |
| Historical execution-to-revision navigation | `DERIVED_REQUIRED` | Current definition does not rewrite historical execution meaning. |
| Source-controlled lifecycle participation | `INHERITED_REQUIRED` | System-level SDK/source workflow remains compatible with repository/source-controlled customer development and re-delivery. |
| Offline/private authoring and validation | `INHERITED_REQUIRED` | Core development flow may not require public SaaS/registry/Internet. |
| Offline/private trial where applicable | `OWNER_DECISION_REQUIRED` | Required by Z3-B2-OD-004; mode remains domain-appropriate. |
| Cross-domain discovery for definitions/revisions/trials/executions | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-006. |
| Localizable developer-facing messages | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-007; machine semantics must not depend on localized text. |
| Accessible visual authoring critical operations | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-008. |
| Re-delivery compatibility diagnostics | `DERIVED_REQUIRED` | Unsupported/unmapped/incompatible semantics must be explicit rather than silently degraded. |

---

# 8. Human-in-the-loop Capability Inventory

| Capability | Classification | Capability Boundary |
|---|---|---|
| Native governed HITL for Automation + Agent | `INHERITED_REQUIRED` | Accepted Z3 Batch 1 Owner decision. |
| Human input/review/choice/confirmation/correction | `INHERITED_REQUIRED` | Applicable Human participation is first-class but not semantic authority by itself. |
| Unified Human Task discovery/re-observation | `OWNER_DECISION_REQUIRED` | Resolved by Z3-B2-OD-002. |
| Principal/Tenant/context binding visibility | `DERIVED_REQUIRED` | The actor must know enough context to avoid answering the wrong task/tenant/revision/execution. |
| Human response provenance | `DERIVED_REQUIRED` | Submitted response remains attributable to applicable principal/task/execution context. |
| Stale/conflicting/expired/wrong-context response handling visibility | `DERIVED_REQUIRED` | Human response is not silently accepted when its governing context is no longer valid. |
| Human Task assignment model details | `DEFERRED` | Exact assignment/claim/delegation model requires later authorized design. |
| Human Task state-machine schema | `DEFERRED` | Exact state set/storage/API remains later design. |
| Timeout/escalation mechanics | `DEFERRED` | Product capability pressure acknowledged; exact policies/mechanisms not frozen here. |
| Offline Human Task response synchronization mechanism | `DEFERRED` | Must preserve submitted/accepted/stale/conflicting/reconciliation semantics if later supported; exact mechanism not fixed. |
| Generic notification as Human Task | `NON_GOAL` | Awareness does not automatically become actionable work. |

---

# 9. Agent Interaction Capability Inventory

| Capability | Classification | Capability Boundary |
|---|---|---|
| Agent activity/operation observation | `DERIVED_REQUIRED` | Users/operators can observe governed status/progress/result without treating UI projection as Agent/Runtime Authority. |
| Agent→Node delegation visibility | `DERIVED_REQUIRED` | Applicable journey can expose proposed/selected delegation, capability/reachability/readiness, execution/local-effect status, HITL wait and returned result as governed projections. |
| Delegation authority preservation | `INHERITED_REQUIRED` | Agent→Node delegation does not transfer Policy/Admission/Trust/actual-state authority. |
| Multi-Agent composition lineage/provenance | `DERIVED_REQUIRED` | Applicable composed runs expose enough specialist/handoff/sub-operation provenance to diagnose partial failure and outcomes. |
| Agent→Automation candidate lifecycle visibility | `DERIVED_REQUIRED` | Candidate Automation authored from intent remains distinguishable from accepted artifact/admitted execution. |
| Agent trial/evaluation interaction | `OWNER_DECISION_REQUIRED` | Covered by Z3-B2-OD-004. |
| Agent operation intervention | `OWNER_DECISION_REQUIRED` | Covered by Z3-B2-OD-003 where intervention is supported. |
| Agent Human Task integration | `OWNER_DECISION_REQUIRED` | Unified Inbox covered by Z3-B2-OD-002. |
| Raw hidden chain-of-thought exposure as product explainability | `NON_GOAL` | Explainability is satisfied through governed outcome, provenance, tool/delegation/activity evidence and diagnostics; raw private reasoning is not required. |
| Agent-native proactive scheduler beyond accepted trigger/time semantics | `DEFERRED` | Preserves Batch 1 deferral; not introduced by interaction UX. |

---

# 10. Automation Interaction Capability Inventory

| Capability | Classification | Capability Boundary |
|---|---|---|
| Automation execution observation/history | `DERIVED_REQUIRED` | Long-running/background Automation remains re-observable with revision/result/provenance. |
| Event-trigger context visibility | `DERIVED_REQUIRED` | Event occurrence and trigger evaluation can be correlated without equating event receipt with execution admission. |
| Reusable Automation composition visibility | `DERIVED_REQUIRED` | Parent/child/subflow relationships and partial failures remain diagnosable where applicable. |
| Human Task integration | `OWNER_DECISION_REQUIRED` | Unified Inbox covered by Z3-B2-OD-002. |
| Notification integration | `OWNER_DECISION_REQUIRED` | Awareness + external delivery covered by Z3-B2-OD-005. |
| Governed intervention | `OWNER_DECISION_REQUIRED` | Covered by Z3-B2-OD-003. |
| Governed trial | `OWNER_DECISION_REQUIRED` | Covered by Z3-B2-OD-004. |
| Revision/history/diff | `DERIVED_REQUIRED` | Historical runs retain the applicable definition revision; current edits do not rewrite historical meaning. |
| Universal reversible cancellation | `NON_GOAL` | Stop/cancel does not imply reversal of already-produced external/local effects. |
| Generic cross-platform scheduler utility | `NON_GOAL` | Preserves Batch 1 common-capability non-goal; Automation scheduling semantics do not imply a universal shared scheduler module. |

---

# 11. Operation and Long-running Interaction Semantics

The following are `DERIVED_REQUIRED` unless separately Owner-decided above:

```text
Operation identity
Request / acknowledgement correlation
Attempt identity / lineage
Historical observation
Return-later observation
Result retrieval
Authorized diagnostics
Uncertainty/degraded-state presentation
Temporal context
Revision context
Principal/Tenant context
```

The following separation is mandatory:

```text
Request Created
!= Request Accepted
!= Execution Admitted
!= Execution Started
!= Execution Completed

Cancel Requested
!= Cancelled

Retry Requested
!= Retried Attempt Started

Recovery Requested
!= Recovered

Reconnect
!= Reconciled

Notification Delivered
!= Operation Succeeded
```

The UI/SDK SHALL not infer canonical actual state from a locally optimistic interaction transition.

---

# 12. Diagnostics / Explainability Capability Boundary

## 12.1 Classification

```text
Layered Diagnostic Presentation → DERIVED_REQUIRED
Cross-operation Correlation → DERIVED_REQUIRED
Authorized Provenance Navigation → DERIVED_REQUIRED
Secret / sensitive-data redaction → DERIVED_REQUIRED
Raw hidden reasoning exposure → NON_GOAL
```

## 12.2 Layering Principle

The same governed evidence may produce different authorized presentation depth:

```text
End User
→ outcome + understandable reason + actionable next context

Operator / Admin
→ component/reachability/configuration/reconciliation/provenance detail

Developer / Delivery
→ operation/revision/correlation/compatibility/trace detail
```

Layering SHALL NOT manufacture different semantic truth for different audiences. It changes authorized detail and presentation only.

## 12.3 Explainability for Agent / Multi-Agent / Automation

Explainability pressure is satisfied through applicable structured evidence such as:

```text
operation identity
selected Definition revision
trigger/delegation/composition lineage
tool/provider/capability participation where permitted
Node delegation and result correlation
Human Task waits/responses
trial context
failure/degraded/unknown states
provenance and diagnostics
```

This candidate does not require disclosure of private chain-of-thought or unstructured internal reasoning.

---

# 13. Desired / Applied / Observed Interaction Boundary

Classification:

```text
Desired/Applied/Observed distinction in human-facing configuration → DERIVED_REQUIRED
Partial application visibility → DERIVED_REQUIRED
Per-runtime actual-state evidence visibility → DERIVED_REQUIRED
Global latest-wins configuration interpretation → NON_GOAL
```

Mandatory semantic preservation:

```text
Desired != Applied != Observed

Configuration Management SoT
!= Applied Runtime Actual-state Owner

Newest Timestamp
!= Canonical Winner by itself
```

Applicable UI/SDK interaction SHALL expose inability to observe or reconcile rather than inventing a converged state.

---

# 14. Revision / History / Diff Boundary

Classification:

```text
Revision identity → DERIVED_REQUIRED
Revision history → DERIVED_REQUIRED
Historical execution revision binding → DERIVED_REQUIRED
Semantic revision comparison/diff → DERIVED_REQUIRED
Byte-for-byte cross-surface round-trip diff → NON_GOAL
Exact diff algorithm/UI → DEFERRED
```

Historical correctness requirement:

```text
Current Definition / Policy / Trust / Mapping
→ SHALL NOT rewrite historical state
```

If historical governing context is unavailable, presentation SHALL preserve applicable `UNKNOWN`, `INDETERMINATE`, `MISSING`, `UNAVAILABLE`, `UNVERIFIED` or equivalent semantics rather than fabricate certainty.

---

# 15. Context Continuity Boundary

Classification:

```text
Cross-session operation continuity → DERIVED_REQUIRED
Cross-session Human Task rediscovery → DERIVED_REQUIRED
Cross-session notification/history rediscovery → DERIVED_REQUIRED
Definition/revision context continuity → DERIVED_REQUIRED
Principal/Tenant context preservation → DERIVED_REQUIRED
Browser-session-as-operation-owner → NON_GOAL
```

A durable operation, task, notification or trial SHALL NOT be semantically owned by one browser/session instance merely because that instance initiated it.

The exact client session/cache/state-restoration mechanism is deferred.

---

# 16. Security / Privacy Interaction Boundary

Classification:

```text
Tenant-aware interaction → INHERITED_REQUIRED
Principal-aware interaction → INHERITED_REQUIRED
Authorization-aware resource discovery → OWNER_DECISION_REQUIRED / resolved
Authorization-aware diagnostics/provenance → DERIVED_REQUIRED
Sensitive-data / secret redaction → DERIVED_REQUIRED
Cross-Tenant search leakage → NON_GOAL / PROHIBITED
UI possession as authorization evidence → NON_GOAL / PROHIBITED
```

Mandatory principles:

```text
Search Visibility != Authorization Grant
UI Action Availability != Policy Approval
Human Confirmation != Execution Admission
Boundary Crossing != Trust Transfer
Notification Audience != Data Disclosure Authority
```

Human-facing projections must not leak resource existence, metadata, diagnostic detail, secrets or protected content across unauthorized Principal/Tenant boundaries.

---

# 17. Offline / Private / Degraded Interaction Boundary

Classification:

```text
Core private/offline interaction correctness → INHERITED_REQUIRED
Explicit disconnected/degraded state → DERIVED_REQUIRED
Local operation/history re-observation where evidence exists → DERIVED_REQUIRED
External notification delivery failure visibility → OWNER_DECISION_REQUIRED / resolved
Public SaaS dependency for core UX → NON_GOAL
```

Examples:

```text
External channel unavailable
→ Notification may still exist in-product
→ external delivery = UNREACHABLE / FAILED / PENDING / UNSUPPORTED as applicable

Node unreachable
→ intervention request may be PENDING / UNREACHABLE / INDETERMINATE
→ NOT falsely shown as completed

Discovery index stale/partial
→ freshness limitation explicit
→ NOT treated as complete canonical inventory
```

---

# 18. Cross-surface Semantic Consistency

Classification:

```text
Stable cross-surface semantic meaning → DERIVED_REQUIRED
One mandatory physical representation → NON_GOAL
Surface-local presentation metadata as semantic authority → NON_GOAL
```

The following semantic categories SHALL retain stable meaning across applicable `ns_web`, SDK/CLI and extension surfaces:

```text
Tenant / Principal context
Operation identity
Lifecycle state
Uncertainty/degraded state
Intervention request/result
Definition/revision identity
Compatibility/conformance result
Trial vs Production distinction
Human Task identity/context
Notification/source correlation
Desired/Applied/Observed
Governance state
Diagnostic correlation/provenance
```

Presentation, layout, localization and interaction modality may differ without changing these meanings.

---

# 19. Explicit Deferrals

The following remain `DEFERRED` and are **not** silently designed by this Batch:

```text
Concrete UI/page/navigation layout
Frontend framework/design system
Concrete SDK/CLI API shape
Concrete network/API protocol
Concrete persistence schema
Concrete operation state machine implementation
Concrete Human Task state machine
Human Task assignment/claim/delegation mechanics
Human Task timeout/escalation policy
Offline Human Task sync algorithm
Notification transport/provider adapter implementation
Feishu API binding
WeCom API binding
SMS vendor/protocol binding
Notification template engine details
Notification routing/preference schema
Canonical internal authoring representation / IR
Source DSL/language choice
Visual definition schema
Source↔Visual conversion pipeline implementation
Opaque-preservation mechanism
Exact revision diff algorithm/UI
Trial runtime/environment mechanics
Trial effect-profile taxonomy details
Universal deterministic simulation
Discovery index/search engine technology
AI semantic search
Exact initial localization language set
Localization resource/package mechanism
Online automatic business-content translation
Concrete accessibility framework/library
Formal accessibility certification target/version
Accessible canvas/graph implementation mechanics
Browser/client session/cache mechanism
Retry/backoff algorithm/policy
Detailed diagnostics/trace transport/storage
Shared Foundation contract/module/provider allocation
Component Internal Design
```

---

# 20. Explicit Non-goals

The following are `NON_GOAL` for this candidate/baseline:

```text
ns_web as Canonical Product Definition SoT
ns_web as Runtime Actual-state Authority
Human Task Inbox as Policy/Acceptance/Admission Authority
Notification Center as current-state SoT
Discovery index as Universal Resource SoT
Universal AI semantic search as baseline requirement
Lossless source↔visual representation round-trip
One mandatory physical authoring representation
Universal cancellation/reversibility guarantee
Cancellation as reversal of already-produced effects
Universal fully isolated simulation for every definition
Browser session as durable operation owner
Generic notification automatically becoming Human Task
Localized natural-language text as protocol/state identity
Automatic translation of arbitrary customer/business content
Mandatory public SaaS for localization/search/notification/accessibility
Pointer-only critical workflow
Color-only critical meaning
Raw hidden chain-of-thought disclosure as explainability requirement
Global latest-wins reconciliation/canonicalization
Generic shared scheduler inferred solely from Automation scheduling pressure
```

---

# 21. Actor-level Capability Summary

## End User

Required interaction baseline includes:

```text
clear operation acknowledgement/status/history
return-later observation
Human Task Inbox
Notification / Awareness
cross-domain discovery
timezone-aware presentation
localized presentation
accessible critical workflows
uncertainty/degraded-state explanation
privacy/authorization-aware visibility
```

## Operator / Admin

Required interaction baseline includes:

```text
health/readiness/reachability views
Desired/Applied/Observed configuration distinction
layered diagnostics
operation intervention where supported
recovery/reconciliation visibility
audit/provenance navigation
notification/awareness
cross-domain discovery
sensitive-data redaction
```

## Developer / Delivery / Integrator

Required interaction baseline includes:

```text
complete source + visual authoring
bidirectional semantic interoperability
validation/conformance/compatibility feedback
governed pre-production trial
revision/history/semantic diff
execution-to-revision traceability
offline/private authoring flow
cross-domain discovery
structured/localizable machine-independent semantics
accessible critical visual-authoring operations
re-delivery diagnostics
```

## HITL Participant

Required interaction baseline includes:

```text
unified Human Task rediscovery
correct Principal/Tenant/execution context
human response provenance
stale/conflict/wrong-context visibility
return-later handling
separation from Policy/Acceptance/Admission authority
```

---

# 22. Interaction Pressure Scan Result

Within the explicitly authorized Z3 Batch 2 interaction-experience scan set:

```text
End User pressure → classified
Operator / Admin pressure → classified
Developer / Delivery / Integrator pressure → classified
HITL pressure → classified
Async / long-running pressure → classified
Cancellation / retry / resume / recovery pressure → classified
Agent pressure → classified
Agent→Node delegation pressure → classified
Multi-Agent pressure → classified
Automation pressure → classified
Offline / degraded / unknown pressure → classified
Diagnostics / explainability pressure → classified
Layered diagnostics pressure → classified
Notification / attention pressure → classified
Governance interaction pressure → classified
Desired / Applied / Observed pressure → classified
Developer authoring pressure → classified
Four-domain dual-authoring pressure → classified
Source↔Visual interoperability pressure → classified
Validation / preview / test / dry-run pressure → classified
Revision / history / diff pressure → classified
Context continuity pressure → classified
Discovery / search pressure → classified
Accessibility pressure → classified
Localization pressure → classified
Timezone pressure → classified
Security / privacy interaction pressure → classified
Cross-surface semantic pressure → classified
```

All discovered capability pressures are assigned exactly one classification. All `OWNER_DECISION_REQUIRED` items discovered by this producing session have been resolved and persisted.

This statement is a bounded Batch 2 scan result only. It SHALL NOT be interpreted as a Global Architecture Coordinator declaration of project-wide capability exhaustion, Five-component Internal Architecture readiness, or authorization to enter Batch 3/Internal Boundary Synthesis.

---

# 23. Revalidation Triggers

This candidate requires revalidation if later work proposes to change any of the following:

1. Any accepted Authority/SoT topology.
2. Complete source + visual authoring for any of the four domains.
3. The selected semantic interoperability guarantee.
4. Unified Human Task capability scope.
5. Operation intervention request/result separation.
6. Governed pre-production trial separation from Production Acceptance/Admission.
7. Notification external-delivery requirement or channel-neutral core semantics.
8. Tenant/authorization-aware discovery.
9. Language-neutral semantic identity/localization boundary.
10. Accessibility as a first-class critical-workflow capability.
11. `Desired != Applied != Observed` configuration semantics.
12. Offline/private core correctness.
13. Historical revision applicability / temporal semantics.
14. Any proposal to make a human-facing aggregation surface a new global authority.

---

# 24. Producing-session Exit Position

At candidate completion:

```text
Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Owner-reserved unresolved interaction capability
→ 0

Known unauthorized Authority / SoT reassignment
→ NONE

Known Runtime/Internal/Foundation implementation leakage
→ NONE
```

Maximum producing-session status remains:

```text
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

The Global Architecture Coordinator retains exclusive authority to independently review/accept/reject/correct this candidate, update Global Governance State, advance GAC Epoch, determine any broader readiness/exhaustion conclusion, and separately authorize any subsequent Z3 Batch.