# ns_evermore Decision Registry — Current Revision

- Version: `0.0.37`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.36`

All accepted normative decisions and baselines in Decision Registry `0.0.36` remain in force unless explicitly refined below.

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
ns_web Component Internal Design / Batch 2 → GLOBAL_ACCEPTED
Accepted ns_web Boundaries with Component Internal Design → W1 / W2 / W7
Accepted ns_web Boundary Coverage → 3 / 7 / 42.86%
Accepted ns_web Internal Responsibility Count → 37
Remaining accepted ns_web boundaries without Component Internal Design → W3 / W4 / W5 / W6
ns_web Internal Design Exhaustion → NOT YET REASSESSED AFTER BATCH 2 ACCEPTANCE
ns_web Component Internal Design Global Closure → NOT DECLARED
```

Batch-2 Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_web_internal_design_batch_2_global_acceptance_0.0.1.md`

## Accepted W2 — Cross-domain Authoring & Semantic Interoperability

Accepted responsibilities:

```text
W2-R01 Authoring Context & Session Provenance
W2-R02 Authoritative Definition Reference & Domain Qualification
W2-R03 Authoring Projection & Projection Revision
W2-R04 Local Draft Identity, Evolution & Revision-base Binding
W2-R05 Governed Edit Intent & Governed Change Intent
W2-R06 Authoring Submission Occurrence & Receiving Authority Correlation
W2-R07 Domain Validation Request / Feedback Correlation
W2-R08 Conformance, Compatibility & Migration Feedback Correlation
W2-R09 Representation Capability & Limitation Qualification
W2-R10 Source ↔ Visual Semantic Interoperability
W2-R11 Semantic Diff Projection
W2-R12 Authoritative Revision History Projection
W2-R13 Base Staleness, Conflict & Reconciliation Observation
W2-R14 Cross-session / Offline / Private Draft Continuity
W2-R15 Secret-reference & Sensitive Authoring Boundary
W2-R16 Authoritative Accepted Revision Outcome Correlation
W2-R17 Cross-domain Authoring Consistency & Future SDK Semantic Compatibility Seam
```

```text
W2 Internal Responsibility Count → 17
Cumulative ns_web Internal Responsibility Count → 37
```

## Definition Authority / SoT Preservation

```text
Business Application Definition Authority / Canonical Definition SoT → S5 / ns_server
Automation Definition Authority / Canonical Definition SoT → S6 / ns_server
Native Data / Knowledge / ETL Definition Authority / Canonical Definition SoT → S7 / ns_server
Agent Definition Authority / Canonical Definition SoT → A1 / ns_agent
```

Permanent:

```text
Visual Builder != Semantic Authority
Visual Edit State != Canonical Definition SoT
Visual Representation != Canonical Definition automatically
Source Representation != separate source-only semantic class
Projection != Source Actual-state
Correlation != Ownership
```

W2 owns only bounded Web-origin authoring-session/projection/draft/intent/submission/presentation/provenance facts genuinely originating in WB-R01.

## Authoring Lifecycle Non-collapse

```text
Authoritative Definition Revision
!= Authoring Projection
!= Draft Base Revision
!= Local Draft
!= Edit Intent
!= Change Intent
!= Submission Occurrence
!= Validation Feedback
!= Compatibility / Conformance Feedback
!= Accepted Definition Revision
!= Formal Artifact Acceptance
!= Formal Execution Admission
!= Runtime Outcome
```

Permanent:

```text
Local Draft != Canonical Revision
Draft Base Revision != Current Canonical Revision automatically
Submission != Acceptance
Validation Passed != Accepted Definition Revision
Definition Accepted != Formal Artifact Acceptance automatically
Formal Artifact Acceptance != Formal Execution Admission
Reconnect != Reconciled
```

## Source ↔ Visual Semantic Interoperability

```text
Bidirectional Semantic Interoperability → REQUIRED
Silent Semantic Loss / Destruction → PROHIBITED
Lossless Physical Representation Round-trip → NOT REQUIRED
```

No mandatory common AST, IR, DSL, compiler, transpiler, code generator, round-trip parser, source normalizer or syntax/format-preserving Product guarantee is accepted.

Legal semantics that are not safely expressible/editable visually must preserve semantic identity/reference and authoritative revision correlation, expose representation limitation explicitly, and must not be silently deleted, rewritten or normalized.

## Representation / Compatibility Qualification

Accepted composable qualifications include where applicable:

```text
SUPPORTED
NON_EDITABLE
REPRESENTATION_LIMITED
UNSUPPORTED
UNKNOWN_COMPATIBILITY
INCOMPATIBLE
STALE_BASE
CONFLICTING
SUPERSEDED
VALIDATION_PENDING
SUBMISSION_PENDING
ACCEPTANCE_UNKNOWN
RECONCILIATION_PENDING
```

They are not a universal authoring lifecycle.

Permanent:

```text
UNSUPPORTED != INVALID automatically
NON_EDITABLE != INVALID
REPRESENTATION_LIMITED != Semantic Loss Permission
UNKNOWN_COMPATIBILITY != COMPATIBLE
STALE_BASE != Automatic Failure
CONFLICTING != Winner Selected
ACCEPTANCE_UNKNOWN != Rejected
VALIDATION_PASSED != Accepted Revision
```

## Conflict / Reconciliation Boundary

No accepted W2 decision establishes:

```text
latest wins
browser wins
server wins
source wins
visual wins
last-write wins
first-write wins
automatic merge
automatic overwrite
automatic rebase success
authoritative synchronization direction
universal revision-selection law
```

Conflict winner / merge / sync law remains a future GAC / Owner revalidation trigger if materially required.

## Validation / Acceptance / Admission Preservation

```text
Editor-local Feedback != Domain Validation
W2 != Domain Validator Authority
Validation Feedback != Canonical Revision
Compatibility Feedback != Definition Acceptance
Conformance Feedback != Formal Artifact Acceptance
Formal Artifact Acceptance != Formal Execution Admission
```

Domain validation/compatibility/conformance evidence remains source-owned by S5/S6/S7/A1 as applicable.

## W1 / W7 / SDK Boundary

W1 and W7 remain accepted normative upstream and are not reopened by Batch 2.

System-level SDK remains outside the five Product Components.

```text
W2 != SDK
SDK != Product Authority
W2 visual model != universal SDK semantic model automatically
```

Only semantic compatibility expectation is accepted: future Web/SDK authoring surfaces consume the same authoritative domain semantics, revision meaning, compatibility/conformance meaning and acceptance boundary.

## Offline / Private / Security

```text
Offline Draft Possession != Canonical Revision
Offline Draft Possession != Accepted Revision
Offline Validation != authoritative Domain Validation automatically
Local Success != Authoritative Success
Secret Reference != Secret Material
Authorized to view != Authorized to edit automatically
Authorized to edit != Definition Accepted
Editor Affordance != Permission
```

Core correctness requires no mandatory public registry/SaaS/hosted visual builder/source-conversion/compiler/validation/diff/collaboration service.

## Stable-contract Qualification

Runtime / Domain Stable Contract Pressure count remains `24`.

```text
S5 Business Application Definition Lifecycle ↔ W2 → ACCEPTED AT CURRENT W2 DESIGN LEVEL
S6 Automation Definition Lifecycle ↔ W2 → ACCEPTED AT CURRENT W2 DESIGN LEVEL
S7 Data / Knowledge / ETL Definition Lifecycle ↔ W2 → ACCEPTED AT CURRENT W2 DESIGN LEVEL
A1 Agent Definition Lifecycle ↔ W2 → ACCEPTED AT CURRENT W2 DESIGN LEVEL

RCP-22 W2 authoring/provenance/diagnostics contribution
→ CLOSED AT CURRENT BATCH DESIGN LEVEL
→ original source owners preserved
→ Full Cross-component Closure NOT CLOSED BY INFERENCE

RCP-24 W2 Web authoring/change-intent source-side contribution
→ CLOSED AT CURRENT BATCH DESIGN LEVEL
→ receiving Definition Authority owns semantic intake/applicability/canonical outcome
→ Full Closure NOT CLOSED BY INFERENCE

RCP-01 → CONSUME ONLY / S1-S4 preserved
```

No new RCP is created.

## Dependency / Cycle

```text
Hard Internal SDD Graph → ACYCLIC
Authority Cycle → NONE
Circular Actual-state Ownership → NONE
Mandatory Missing Shared Foundation Semantic → NONE_FOUND
```

## Accepted DAD

```text
CID-WB-B2-DAD-001..020 → GLOBAL_ACCEPTED
DAD Count → 20
Misclassified MDE → 0
New MDE Candidate → 0
Open MDE → 0
Unpersisted Owner Decision → 0
```

## Technology-neutrality

```text
Implementation Leakage → 0
W1/W7 Redesign → 0
W3-W6 Preemption → 0
SDK Detailed-design Preemption → 0
```

No frontend/editor framework, visual canvas library, state store, parser/compiler, AST/IR/DSL, code generator, merge engine, protocol/API/schema, browser persistence, DB/event-store/cache, build/deployment topology or physical identifier format is accepted.

## Remaining Web Pressure / Current Governance Boundary

```text
W3 — Human Task Interaction → NOT INTERNALLY DESIGNED
W4 — Notification & Awareness Interaction → NOT INTERNALLY DESIGNED
W5 — Operational Observation, Trial, Intervention & Diagnostics → NOT INTERNALLY DESIGNED
W6 — Cross-domain Discovery & Governed Navigation → NOT INTERNALLY DESIGNED

ns_web Internal Design Exhaustion SATISFIED → NOT DECLARED
ns_web Component Internal Design Global Closure → NOT DECLARED
ns_web Batch 3 → NOT AUTHORIZED
ns_web Batch 4 → NOT AUTHORIZED
System-level SDK Detailed Design → NOT AUTHORIZED
Design-to-Implementation Readiness → NOT AUTHORIZED
Implementation Planning / IWP / Coding → NOT AUTHORIZED
```

Unique next legal action after the Batch-2 Global Acceptance State seal:

```text
Fresh Repository recovery
→ perform post-Batch-2 ns_web remaining-pressure / Batch-3 entry-readiness assessment
→ determine whether W5 remains the immediate next material pressure under the accepted 4-batch shape
→ do not authorize Batch 3 automatically from Batch-2 acceptance
```