# NGRP-001 — Runtime / Domain Stable Contract Design / Batch 1 — DAD Evidence 0.0.2

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Runtime / Domain Stable Contract Design / Batch 1 / Correction Reissuance`
- Scope: `RUNTIME_DOMAIN_STABLE_CONTRACT_DESIGN_ONLY / BATCH_1 / CORRECTION_REISSUANCE / RCP24_PRODUCER_TOPOLOGY_SCOPE_RECONCILIATION_ONLY`
- Correction Authorization Seal / Producing Entry HEAD: `c2495faefaf09c38d07b559b6d58fda73038da95`
- Candidate 0.0.2 Commit: `b728069a4f1855e9ebccdffe957c070986d79655`
- Frozen Original DAD: `0.0.1 / a2929f986e753136fa2ae114125f3efd0a4ce02b / HISTORICAL / READ ONLY`
- Decision Set: `RDSC-B1-DAD-001..012 / unchanged`
- MDE Authority: `NONE`
- Global Acceptance Authority: `NONE`
- Evidence Status: `CORRECTION REISSUED / AWAITING REVIEW 0.0.2`

This reissuance preserves exactly the original twelve DAD identities. It adds no DAD and removes none. The only substantive correction is the producer-topology qualification inside `RDSC-B1-DAD-006`; all other decisions are revalidated as non-regression baseline, with only consistency wording where the corrected RCP-24 producer scope is referenced.

---

# 1. DAD-entry Recovery / Git Gate

Immediately before persistence:

```text
Expected remote HEAD
→ b728069a4f1855e9ebccdffe957c070986d79655

Actual remote HEAD
→ b728069a4f1855e9ebccdffe957c070986d79655

Correction Authorization Seal → Candidate compare
→ ahead 1 / behind 0 / total commits 1

Changed files
→ exactly Candidate 0.0.2 only

DAD 0.0.2 target existed
→ NO

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

DAD/MDE boundary remains:

```text
Product Component count → unchanged
Runtime Role count → unchanged
RCP count → unchanged
Authority topology → unchanged
SoT topology → unchanged
Final Actual-state ownership topology → unchanged
Trust boundary → unchanged
Cross-Tenant law → unchanged
Universal fail/winner/once/retry/cancel/reversal law → not created
Mandatory public/online dependency → not created
Provider/framework/protocol/storage lock-in → not created
Accepted upstream architecture → not modified
Hard Contract CSDD cycle → not created
```

No MDE is required by this correction.

---

# 2. Decision Summary — IDs Preserved

```text
RDSC-B1-DAD-001
→ bounded semantic Contract subject identity; no universal physical namespace

RDSC-B1-DAD-002
→ RCP-01 qualified Governance Context; not governance Authority/SoT object

RDSC-B1-DAD-003
→ RCP-02 authoritative Admission Evidence + consumer applicability; transport/dispatch != Admission

RDSC-B1-DAD-004
→ RCP-03 multi-dimensional Presence/currentness/reachability; not identity/trust/readiness

RDSC-B1-DAD-005
→ RCP-19 Desired/Distributed/Applied/Observed separation; no generic conflict winner

RDSC-B1-DAD-006
→ RCP-24 Intent/submission/applicability/outcome separation + corrected closed producer topology

RDSC-B1-DAD-007
→ RCP-04 bounded Node/Capability/AppliedConfig/ExecutionMode readiness; non-boolean uncertainty

RDSC-B1-DAD-008
→ currentness/uncertainty/history reuse Shared Foundation and remain orthogonal/non-canonicalizing

RDSC-B1-DAD-009
→ offline retention/reconnect/recovery/re-observation preserve source authority/history

RDSC-B1-DAD-010
→ security/privacy minimization/redaction/Secret Reference boundary across all six Contracts

RDSC-B1-DAD-011
→ compatibility/migration/conformance semantic and representation-neutral

RDSC-B1-DAD-012
→ CSDD/CACD/CEL/CHPL/CXAR taxonomy + acyclic Batch-1 Contract dependency graph
```

```text
New DAD because of correction
→ 0

Removed DAD
→ 0
```

---

# 3. RDSC-B1-DAD-001 — Bounded Semantic Contract Subject Identity

## Decision

Stable Contract subjects use representation-neutral bounded semantic identities/references. No transport, database or provider identifier is automatically Contract identity.

```text
Semantic Subject Identity
!= universal UUID namespace
!= database PK
!= transport request/message ID
!= provider-native ID automatically
```

Correlation remains distinct from ownership.

For RCP-24 specifically, a current Web Intent occurrence is scoped to a genuine `ns_web / WB-R01` source occurrence under the accepted originating responsibility. This does not create a Product-wide Command ID. Future SDK identity semantics remain future and must preserve the same distinction after separate authorization.

## Authority / SoT / final-owner consequence

```text
Authority Transfer → 0
SoT Transfer → 0
Final Actual-state Ownership Transfer → 0
```

## Correction status

```text
Decision semantic result
→ UNCHANGED

Consistency refinement
→ RCP-24 current Web Intent occurrence explicitly WB-R01 scoped
```

## Revalidation

STOP if a universal physical identity namespace or identity-possession-as-authority is required.

---

# 4. RDSC-B1-DAD-002 — RCP-01 Qualified Governance Context

## Decision

RCP-01 is a qualified cross-boundary context/reference Contract preserving distinct Tenant, Organization, Principal, Authentication Evidence, Policy/Authorization and Trust semantics.

Permanent:

```text
Tenant != Organization
Principal != Authentication
Authenticated != Authorized
Policy != Trust
Reference != Authority
Context Propagation != Governance Authority
```

RCP-01 does not create a universal mutable Governance/session SoT and does not absorb constituent `ns_server` authorities.

## Offline / failure / privacy

Retained context cannot extend authority. Missing/stale/unverifiable remains explicit. Minimum disclosure/redaction remains mandatory.

## Correction status

```text
RCP-01 substantive change
→ NONE

GAC non-regression
→ PASS BASELINE PRESERVED
```

---

# 5. RDSC-B1-DAD-003 — RCP-02 Admission Evidence / Consumer Applicability

## Decision

```text
Formal Execution Admission Authority
→ ns_server / S8 / SV-R04

Admission Evidence != Admission Authority Transfer
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Receipt/Transport/Dispatch Success != Admission
```

Consumers correlate authoritative evidence and establish only consumer applicability under S8 semantics; they do not mint, extend, renew or reinterpret Admission.

`UNKNOWN`, `UNAVAILABLE`, `STALE`, `INDETERMINATE` are not implicit permit/reject decisions.

## Correction status

```text
RCP-02 substantive change
→ NONE

GAC non-regression
→ PASS BASELINE PRESERVED
```

---

# 6. RDSC-B1-DAD-004 — RCP-03 Multi-dimensional Presence

## Decision

RCP-03 preserves distinct Participant Reference, Presence Observation, connection qualification, reachability qualification and currentness.

```text
Connected != Trusted
Connected != Admitted
Reachable != Ready
Disconnected != Revoked
STALE != FALSE
UNKNOWN != DISCONNECTED
```

RT-R01 remains owner of runtime-originated presence/reachability coordination facts only.

## Correction status

```text
RCP-03 substantive change
→ NONE

GAC non-regression
→ PASS BASELINE PRESERVED
```

---

# 7. RDSC-B1-DAD-005 — RCP-19 Four-plane Configuration Semantics

## Decision

```text
Canonical Managed Desired
→ ns_server / S9 / SV-R05

Applied Actual-state
→ applicable runtime Actual-state owner

Observed
→ qualified projection / observation

Desired != Distributed != Applied != Observed
```

No generic winner:

```text
latest wins → NOT A CONTRACT LAW
central wins → NOT A CONTRACT LAW
local wins → NOT A CONTRACT LAW
```

Partial/failure/unknown/conflicting evidence remains explicit. Secret Reference may be used; ordinary config evidence does not require Secret Material.

## Correction status

```text
RCP-19 substantive change
→ NONE

GAC non-regression
→ PASS BASELINE PRESERVED
```

---

# 8. RDSC-B1-DAD-006 — RCP-24 Intent / Submission / Applicability / Outcome + Corrected Producer Topology

## Decision / issue

The original DAD correctly selected the source-Intent versus receiving-authority separation, but its generic `Human/Web/future SDK` wording did not fully reconcile the exact current producer topology required by GAC review. The corrected decision preserves the same lifecycle decision while making the producer set explicit and closed.

## Preserved lifecycle decision

Select the original option 3:

```text
Source Intent Identity
+ Local Possession qualification
+ Submission Occurrence
+ Receipt Correlation
+ Receiving-authority Applicability Evidence
+ Authoritative Outcome Correlation
```

Permanent:

```text
Intent != Permit != Acceptance != Admission != Outcome
Local Possession != Submission != Receipt != Applicability != Application != Authoritative Outcome
```

No Universal Command Authority or Universal Command State Machine is created.

## Corrected current Product-side producer topology

```text
Current Product-side Source Producer
→ ns_web / WB-R01
```

Only accepted Web responsibilities that genuinely originate RCP-24 Intent/submission facts participate. The current accepted contribution set is explicitly:

```text
W1 / WB-R01
→ administration / governed command Intent
→ source Intent + submission occurrence

W2 / WB-R01
→ authoring / governed edit/change Intent
→ source Intent + authoring submission occurrence

W5 / WB-R01
→ applicable Trial/intervention Intent
→ cancel / retry / resume / recovery request Intent where W5 semantics apply
→ source request Intent + submission occurrence
```

These are responsibility-scoped contributions under one Web runtime-facing role. `WB-R01` owns only genuine Web-origin Intent/submission facts.

## Future source seam

```text
Future Source Producer
→ System-level SDK
→ FUTURE ONLY
→ requires separate SDK design / authorization
```

This decision does not define an SDK API, object model, transport, package, language binding, authentication mechanism, request identifier, retry/idempotency mechanism or lifecycle.

## No producer expansion

```text
Additional Generic Source-surface Producer Class
→ NOT CREATED
```

No open-ended `other human/source surface` producer category exists in the corrected Contract. A future producer outside `ns_web/WB-R01` plus separately authorized System-level SDK requires normal GAC revalidation.

## Receiving authority

The target-domain receiving semantic authority remains owner of:

```text
Intent applicability
Authoritative semantic application/outcome
```

Web/SDK possession/submission/transport success does not establish any of these.

## RCP-12 boundary

```text
Agent Delegation
Agent cross-domain invocation
Agent→Node
Agent→Automation
→ RCP-12
→ NOT RCP-24 source producers
```

```text
RCP-12 redesign
→ NONE

RCP-12 overlap introduced
→ NONE
```

## Configuration boundary

```text
RCP-24 Configuration-change Intent
!= RCP-19 Canonical Desired-state
```

S9 alone establishes canonical managed Desired revisions.

## Retry / failure / offline

Each actual submission occurrence remains distinguishable in lineage. No universal exactly-once, retry, deduplication, cancel, rollback, reversal or delivery guarantee is created.

`REJECTED` and authoritative semantic failure require receiving-owner evidence. Submission/transport `FAILED` is distinct from target semantic failure. Offline possession remains pre-submission; reconnect does not auto-apply or choose a winner.

## Authority / SoT / final-owner consequence

```text
Authority Transfer → 0
SoT Transfer → 0
Final Actual-state Ownership Transfer → 0
```

## Correction determination

```text
Original lifecycle decision
→ PRESERVED

Producer topology
→ CORRECTED

W1-only under-specification
→ REMOVED

Open-ended producer over-expansion
→ REMOVED

W1/W2/W5 consistency
→ ESTABLISHED

Future SDK qualification
→ EXPLICIT / FUTURE ONLY

Additional Generic Producer
→ NONE
```

## Revalidation

STOP on new RCP-24 producer outside accepted topology, source-side applicability/outcome authority, Universal Command Authority/state machine, universal retry/once/cancel/reversal law, cross-Tenant intent law, RCP-12 absorption or SDK Detailed Design leakage.

---

# 9. RDSC-B1-DAD-007 — RCP-04 Bounded Node Readiness

## Decision

Readiness is bounded by Node/Capability/Capability Revision/Applied Config/Execution Mode/Governance context/currentness/local prerequisites and owned by `ns_node / N1 / ND-R01`.

```text
READY / NOT_READY / UNKNOWN / INDETERMINATE
→ semantic qualifications where evidence supports them

STALE
→ orthogonal currentness qualification
```

Permanent:

```text
Reachable != Ready
Connected != Ready
Ready != Trusted
Ready != Admitted
Capability Present != Ready automatically
Installed != Accepted
Available != Admitted
Activated != Authorized
```

Hard dependencies remain:

```text
RCP-04 → RCP-01, RCP-19
RCP-03 relation → CACD/CEL, not CSDD
```

## Correction status

```text
RCP-04 substantive change
→ NONE

GAC non-regression
→ PASS BASELINE PRESERVED
```

---

# 10. RDSC-B1-DAD-008 — Orthogonal Currentness / Uncertainty / History

## Decision

All six domain Contracts reuse accepted Shared Foundation Temporal/Freshness and Technical Status/Uncertainty semantics while keeping domain-specific state separate.

```text
UNKNOWN != FAILED
STALE != FALSE
UNAVAILABLE != DENIED
CONFLICTING != winner selected
```

History/provenance are non-destructive. Time/arrival order does not create authority.

RCP-24 producer correction does not introduce a new status model; W1/W2/W5 occurrences use the same stage-qualified uncertainty rules already accepted.

## Correction status

```text
Substantive semantic change
→ NONE
```

---

# 11. RDSC-B1-DAD-009 — Offline / Reconnect / Recovery / Re-observation

## Decision

```text
Offline != Authority Transfer
Reconnect != Reconciled
Recovery != SoT Transfer
Re-observation != Canonicalization
Replay / resubmission != Retroactive Authorization
Latest Timestamp / Arrival != Canonical Winner
```

For RCP-24, offline Web possession remains bound to the actual W1/W2/W5 source occurrence and cannot become submission/application or be reclassified as another producer on reconnect.

## Correction status

```text
Substantive semantic change
→ NONE

RCP-24 producer-lineage consistency
→ REVALIDATED
```

---

# 12. RDSC-B1-DAD-010 — Security / Privacy / Secret Reference

## Decision

All Contracts preserve Tenant/Principal/Policy/Trust disclosure scope, minimum disclosure, redaction and Secret Reference separation.

```text
Secret Reference != Secret Material
Reference Possession != Permission to Resolve
```

RCP-24 source topology correction does not widen disclosure rights. W1/W2/W5 source contribution existence does not grant the right to submit, view target state or observe authoritative outcomes without applicable authorization.

Future SDK seam creates no current disclosure surface.

## Correction status

```text
New Trust/Security Authority
→ 0

Substantive semantic change
→ NONE
```

---

# 13. RDSC-B1-DAD-011 — Compatibility / Migration / Conformance

## Decision

Conformance is semantic, representation-neutral and owner-preserving. A representation that cannot preserve mandatory semantics reports unsupported/incompatible/unknown rather than silently coercing meaning.

Migration preserves:

```text
subject/correlation identity
source producer responsibility
Authority/SoT/final-owner
revision/applicability/currentness
uncertainty
history/provenance
Tenant/privacy/redaction
Secret Reference boundary
non-collapse invariants
```

For RCP-24, conformance requires preserving whether a current occurrence originated from accepted `WB-R01` W1/W2/W5 semantics or from a future separately authorized SDK source. A generic producer classification not accepted by Repository authority is non-conforming.

## Correction status

```text
Substantive semantic change
→ NONE

RCP-24 producer conformance criterion
→ MADE EXPLICIT
```

---

# 14. RDSC-B1-DAD-012 — Typed Dependency Taxonomy / Acyclic CSDD

## Decision

```text
CSDD → Contract Semantic-definition Dependency
CACD → Application-context Dependency
CEL → Evidence Linkage
CHPL → Historical / Provenance Linkage
CXAR → Cross-authority Reference
```

Only CSDD participates in hard semantic-definition cycle analysis.

Hard graph remains:

```text
RCP-02 → RCP-01
RCP-03 → RCP-01
RCP-19 → RCP-01
RCP-24 → RCP-01
RCP-04 → RCP-01, RCP-19
```

Rank proof:

```text
rank 0 → RCP-01
rank 1 → RCP-02 / RCP-03 / RCP-19 / RCP-24
rank 2 → RCP-04
```

Producer-topology correction changes no edge.

```text
Hard Contract CSDD Graph
→ ACYCLIC

Authority Cycle
→ NONE

SoT Cycle
→ NONE

Final Actual-state Ownership Cycle
→ NONE
```

## Correction status

```text
Dependency change
→ NONE
```

---

# 15. DAD 0.0.2 Non-regression / Correction Summary

```text
RDSC-B1-DAD-001 → REISSUED / semantic result preserved
RDSC-B1-DAD-002 → REISSUED / unchanged
RDSC-B1-DAD-003 → REISSUED / unchanged
RDSC-B1-DAD-004 → REISSUED / unchanged
RDSC-B1-DAD-005 → REISSUED / unchanged
RDSC-B1-DAD-006 → REISSUED / producer topology corrected
RDSC-B1-DAD-007 → REISSUED / unchanged
RDSC-B1-DAD-008 → REISSUED / unchanged
RDSC-B1-DAD-009 → REISSUED / unchanged
RDSC-B1-DAD-010 → REISSUED / unchanged
RDSC-B1-DAD-011 → REISSUED / unchanged
RDSC-B1-DAD-012 → REISSUED / unchanged
```

RCP-24 corrected topology:

```text
Current Product-side Source Producer
→ ns_web / WB-R01

Current responsibility contributions
→ W1 / W2 / W5 only where their accepted semantics genuinely originate RCP-24 Intent/submission facts

Future Source Producer
→ System-level SDK
→ future only / separate design & authorization required

Additional Generic Source-surface Producer Class
→ NOT CREATED

RCP-12 overlap
→ NONE
```

```text
Decision Set Count
→ 12 / unchanged

New DAD
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Authority Transfer
→ 0

SoT Transfer
→ 0

Final Actual-state Ownership Transfer
→ 0

Hard CSDD
→ ACYCLIC

Unexpected Drift at DAD entry
→ NONE

Unauthorized Progression
→ NONE

Global Acceptance
→ NOT CLAIMED

Batch 2 Authorization
→ NONE

System-level SDK Detailed Design
→ NOT AUTHORIZED
```

The only legal next producing action is `Review / Audit 0.0.2`, after a fresh Git drift gate and complete re-run of all 27 Batch-1 reviews.