# ns_evermore Decision Registry — Current Revision

- Version: `0.0.36`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.35`

All accepted normative decisions and baselines in Decision Registry `0.0.35` remain in force unless explicitly refined below.

## Current Accepted Global Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
Unified Governance → 0.0.2 / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Product Capability Exhaustion → SATISFIED
Five-component Internal Architecture Boundaries → GLOBAL_ACCEPTED / NORMATIVE
Accepted Internal Boundaries → 34
Runtime Responsibility Architecture → GLOBAL_CLOSED / COMPLETE
Runtime Roles → 22
Runtime / Domain Stable Contract Pressure → 24 / NAMED DOWNSTREAM DESIGN AUTHORITY
Shared Foundation Architecture / Contract / Module / Provider → GLOBAL_CLOSED / COMPLETE
Foundation Provider Design Exhaustion → SATISFIED
Component Internal Design Readiness → SATISFIED
```

## Product Component Internal Design State

```text
ns_server Component Internal Design → GLOBAL_CLOSED / COMPLETE
ns_server Internal Design Exhaustion → SATISFIED

ns_runtime Component Internal Design → GLOBAL_CLOSED / COMPLETE
ns_runtime Internal Design Exhaustion → SATISFIED

ns_node Component Internal Design → GLOBAL_CLOSED / COMPLETE
ns_node Internal Design Exhaustion → SATISFIED

ns_agent Component Internal Design → GLOBAL_CLOSED / COMPLETE
ns_agent Internal Design Exhaustion → SATISFIED

ns_web Component Internal Design / Batch 1 → GLOBAL_ACCEPTED
Accepted ns_web Boundaries with Component Internal Design → W1 / W7
Accepted ns_web Boundary Coverage → 2 / 7 / 28.57%
Accepted ns_web Internal Responsibility Count → 20
Remaining accepted ns_web boundaries without Component Internal Design → W2 / W3 / W4 / W5 / W6
ns_web Internal Design Exhaustion → NOT YET REASSESSED AFTER BATCH 1 ACCEPTANCE
ns_web Component Internal Design Global Closure → NOT DECLARED
```

Batch-1 Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_web_internal_design_batch_1_global_acceptance_0.0.1.md`

## Accepted W1 — Governed Administration & Control Interaction

```text
W1-R01 Governed Interaction Context & Session Provenance
W1-R02 Administration Projection Qualification
W1-R03 Authoritative Target & Intent Correlation
W1-R04 Governed Command Intent Origination & Submission Occurrence
W1-R05 Intent Applicability Observation
W1-R06 Authoritative Outcome Correlation
W1-R07 Governance / Acceptance / Admission Administration Projection
W1-R08 Managed Configuration Administration Projection
W1-R09 Web Interaction History / Audit / Diagnostic Projection
W1-R10 Offline / Degraded Intent Possession & Re-observation
W1-R11 Administration Compatibility / Migration / Conformance Interaction
```

## Accepted W7 — Experience Semantics, Accessibility & Degraded Interaction

```text
W7-R01 Semantic Presentation Vocabulary & Qualification
W7-R02 Locale & Localization Context
W7-R03 Timezone & Source-time Presentation
W7-R04 Accessibility-preserving Critical Interaction
W7-R05 Status / Error / Currentness Presentation
W7-R06 Degraded / Unknown / Offline Experience Qualification
W7-R07 Redaction & Sensitive Disclosure Preservation
W7-R08 Cross-surface Semantic Consistency & Future Web Seam
W7-R09 Experience Transformation Provenance & Diagnostics
```

## WB-R01 Accepted Mapping

```text
WB-R01 — Governed Human Interaction & Projection Participant
→ W1 / W7 current accepted internal design contribution
```

WB-R01 owns only bounded Web-origin interaction/session/intent-submission/presentation-provenance facts genuinely originating in Web.

Permanent:

```text
Web Interaction != Domain Authority
Web Projection != Source Actual-state
UI Local State != Canonical Product State
Frontend Cache != Source of Truth
Browser Session != Operation Owner
Correlation != Ownership
```

## Governed Intent Non-collapse

```text
Local / Offline Intent Possession
!= Intent Submission Occurrence
!= Intent Applicability Observation
!= Authoritative Outcome
```

Permanent:

```text
Button Click != Policy Permit
Button Click != Artifact Acceptance
Button Click != Execution Admission
UI Affordance != Permission
Transport / HTTP Success != Domain Semantic Success
Intent != Permit
Intent != Acceptance
Intent != Admission
Intent != Outcome
```

Receiving authority retains applicability and semantic outcome ownership.

## Governance / Acceptance / Admission Preservation

```text
Tenant semantic authority / canonical Tenant SoT → S1 / ns_server
Principal / IAM semantic authority → S1 / ns_server
Organization semantic authority → S2 / ns_server
Policy / Authorization semantic authority → S3 / ns_server
Trust semantic authority → S4 / ns_server
Formal Artifact Acceptance → S8 / ns_server
Formal Execution Admission → S8 / ns_server
```

W1 consumes/projects these semantics and never becomes their authority.

## Managed Configuration Preservation

```text
Managed Desired-state Authority / Canonical Desired SoT
→ S9 / SV-R05

W1
→ Web human Desired-state administration-intent source
→ projection consumer

Applied Configuration Actual-state
→ applicable runtime owner

Observed
→ projection only
```

Permanent:

```text
Desired != Distributed != Applied != Observed
Observed != Applied SoT
Offline Web possession != Desired SoT
Reconnect != Reconciled
Conflict != winner selected
Latest client state != canonical winner
```

## Locale / Localization / Timezone

```text
Semantic Identity != Display Language
Locale != Tenant
Locale != Organization
Locale != Principal
Locale != Timezone
Localized Text != Machine Semantic Identity
Localized Status != New Domain Status
Presentation Timezone != Source-time Authority
Client Clock != Source-time Authority
Client Clock != ordering/conflict winner
```

Localization remains presentation semantics and does not alter machine/domain identity.

## Accessibility

Accepted inherited capability remains:

```text
First-class critical-workflow accessibility → REQUIRED
Semantic interaction parity → REQUIRED
Identical visual / gesture parity → NOT REQUIRED
Pointer-only critical completion → PROHIBITED
Color-only critical meaning → PROHIBITED
```

Permanent:

```text
Accessible Confirmation != Additional Authority
Accessible Confirmation != Policy Permit
Accessible Confirmation != Artifact Acceptance
Accessible Confirmation != Execution Admission
Accessible Confirmation != Authoritative Outcome
```

No Product-wide formal compliance/certification target or exact external standard/version is accepted by Batch 1.

## Degraded / Offline / Status Qualification

Accepted composable qualifications include where evidence supports them:

```text
UNKNOWN
STALE
UNAVAILABLE
UNREACHABLE
PARTIAL
INDETERMINATE
CONFLICTING
PENDING
SUPERSEDED
RECONCILIATION_PENDING
```

They do not form a universal Web lifecycle state machine.

Permanent:

```text
UNKNOWN != FAILED
STALE != CURRENT
UNAVAILABLE != DENIED
UNREACHABLE != REJECTED
CONFLICTING != winner selected
PENDING != accepted
RECONCILIATION_PENDING != reconciled
Offline Client Possession != Authority Transfer
Reconnect != Reconciled
Client Timestamp != Canonical Winner
Latest Client State != Canonical Winner
```

## Security / Privacy / Secret Boundary

```text
Tenant != Organization
Principal Identity != Authentication automatically
Authenticated != Authorized automatically
Authorized != Artifact Accepted
Artifact Accepted != Execution Admitted
Execution Admitted != Runtime Outcome
Secret Reference != Secret Material
```

Redaction/non-leak semantics apply across normal, localized, accessible, degraded, offline, history and diagnostics presentation. Secret Material is not ordinary Web state/cache/history/diagnostic content.

## Accepted W1↔W7 Stable Semantic Subjects

```text
Administration / Governance Projection
Governed Command Intent
Authoritative Outcome Correlation
Status / Error / Currentness Presentation
Experience / Locale / Timezone Semantic Presentation
Accessibility-preserving Critical Interaction
Degraded / Offline Interaction Qualification
Web Interaction Provenance
```

These are representation-neutral semantic subjects only and imply no frontend/API implementation shape.

## Stable-contract Qualification

```text
RCP-01 Web-side Governance Context consume/presentation contribution
→ CLOSED AT CURRENT BATCH DESIGN LEVEL
→ S1-S4 authority preserved
→ Full Cross-component Closure NOT CLOSED BY INFERENCE

RCP-19 W1 human Desired-state administration-intent + W1/W7 Desired/Distributed/Applied/Observed presentation contribution
→ CLOSED AT CURRENT BATCH DESIGN LEVEL
→ S9 Desired + runtime Applied ownership preserved
→ Full Cross-component Closure NOT CLOSED BY INFERENCE

RCP-22 WB-R01 interaction provenance + source diagnostics/provenance presentation expectation
→ ACCEPTED AT CURRENT BATCH DESIGN LEVEL
→ original source fact ownership preserved
→ Full Cross-component Closure NOT CLOSED BY INFERENCE

RCP-24 W1 Web human/admin intent source-side semantics
→ CLOSED AT CURRENT BATCH DESIGN LEVEL
→ receiving authority owns applicability/outcome
→ Full Closure NOT CLOSED BY INFERENCE
```

Runtime / Domain Stable Contract Pressure count remains `24`; no new RCP is created.

## Dependency / Cycle

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY

Hard Internal SDD Graph → ACYCLIC
Authority Cycle → NONE
Circular Actual-state Ownership → NONE
```

## Accepted DAD

```text
CID-WB-B1-DAD-001..015 → GLOBAL_ACCEPTED
```

```text
DAD Count → 15
Misclassified MDE → 0
Open MDE → 0
Unpersisted Owner Decision → 0
```

## Foundation / Technology-neutrality

```text
Mandatory Missing Shared Foundation Semantic → NONE_FOUND
Parallel ns_web-local Foundation → 0
Implementation Leakage → 0
```

No frontend framework, state store, router, UI system, i18n/accessibility/time library, API/wire/schema, browser persistence, PWA/service-worker architecture, offline synchronization/conflict algorithm, database/cache, build system, deployment topology, mobile/native stack or code/package structure is accepted.

## W2-W6 Status

```text
W2 — Cross-domain Authoring & Semantic Interoperability → NOT INTERNALLY DESIGNED
W3 — Human Task Interaction → NOT INTERNALLY DESIGNED
W4 — Notification & Awareness Interaction → NOT INTERNALLY DESIGNED
W5 — Operational Observation, Trial, Intervention & Diagnostics → NOT INTERNALLY DESIGNED
W6 — Cross-domain Discovery & Governed Navigation → NOT INTERNALLY DESIGNED
```

Batch 1 may provide a stable W1/W7 baseline consumed by future batches but does not preempt their design.

## Current Governance Boundary

```text
Current Authorized Phase after Batch-1 acceptance seal → NONE
Authorization Scope → NONE

ns_web Batch 2 → NOT AUTHORIZED
ns_web Batch 3 → NOT AUTHORIZED
ns_web Batch 4 → NOT AUTHORIZED
ns_web Internal Design Exhaustion SATISFIED → NOT DECLARED
ns_web Component Internal Design Global Closure → NOT DECLARED
System-level SDK Detailed Design → NOT AUTHORIZED
Design-to-Implementation Readiness → NOT AUTHORIZED
Implementation Planning / IWP / Coding → NOT AUTHORIZED
```

Unique next legal action after the Batch-1 Global Acceptance State seal:

```text
Fresh Repository recovery
→ perform post-Batch-1 ns_web Component Internal Design remaining-pressure / Batch-2 entry-readiness assessment
→ do not authorize Batch 2 automatically from Batch-1 acceptance
```
