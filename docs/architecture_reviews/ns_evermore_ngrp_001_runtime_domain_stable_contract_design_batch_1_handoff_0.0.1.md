# NGRP-001 — Runtime / Domain Stable Contract Design / Batch 1 — Handoff Evidence

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Runtime / Domain Stable Contract Design / Batch 1`
- Scope: `RUNTIME_DOMAIN_STABLE_CONTRACT_DESIGN_ONLY / BATCH_1 / GOVERNANCE_INTENT_ADMISSION_PRESENCE_CONFIGURATION_READINESS_FOUNDATION`
- Authorized RCPs: `RCP-01 / RCP-02 / RCP-03 / RCP-04 / RCP-19 / RCP-24`
- Producing Entry HEAD: `d6b12f1d9901d810a61943c0c84b058db61746b2`
- Candidate Commit: `f9966824b12f43c5043440a231b4cc9adf55d2cc`
- DAD Commit: `a2929f986e753136fa2ae114125f3efd0a4ce02b`
- Review Commit / Pre-handoff HEAD: `9e583c101d8cd028c11c2acda94efbbe9c069ff2`
- Entry Global State: `GAC-EPOCH-0113`
- Decision Registry: `0.0.40 / GLOBAL_CURRENT / NORMATIVE`
- Handoff Authority: bounded producing-session evidence only
- Global Acceptance Authority: `NONE`
- Disposition: `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`

This is the fourth and final authorized producing artifact. Consistent with existing Repository handoff discipline, the Handoff commit cannot embed its own Git SHA without creating an impossible Git-object self-reference. Therefore this artifact records `Final Producing HEAD → [Handoff persistence commit]`; immediately after persistence the producing session must externally resolve that SHA and verify the exact four-commit/four-file delta before reporting completion to GAC.

---

# 1. Producing Entry HEAD

```text
Producing Entry HEAD
→ d6b12f1d9901d810a61943c0c84b058db61746b2

Entry Commit
→ docs(governance): seal stable contract batch 1 authorization at GAC-EPOCH-0113

Entry Global State
→ GAC-EPOCH-0113

State Verified Through HEAD
→ 5674037c7ca8f35e2d85fc153836998f7aa9a006

Decision Registry
→ 0.0.40 / GLOBAL_CURRENT / NORMATIVE
```

Fresh Repository recovery matched the authorized seal exactly.

---

# 2. Final Producing HEAD

```text
Final Producing HEAD
→ [THIS HANDOFF PERSISTENCE COMMIT]
→ exact SHA MUST be resolved by immediate post-persistence Git verification
```

Pre-handoff HEAD is exactly:

```text
9e583c101d8cd028c11c2acda94efbbe9c069ff2
```

The final SHA is not governance state and does not carry Global Acceptance authority; it is the Git identity of this fourth producing evidence commit.

---

# 3. Exact Commit Chain

Pre-persistence expected chain:

```text
d6b12f1d9901d810a61943c0c84b058db61746b2
→ f9966824b12f43c5043440a231b4cc9adf55d2cc
  Candidate only
→ a2929f986e753136fa2ae114125f3efd0a4ce02b
  DAD Evidence only
→ 9e583c101d8cd028c11c2acda94efbbe9c069ff2
  Review / Audit only
→ [Handoff persistence commit]
  Handoff only
```

Before Handoff persistence:

```text
Producing Entry → Review HEAD
→ ahead 3 / behind 0 / total commits 3

Changed files
→ exactly 3
→ Candidate / DAD / Review only

Unexpected drift
→ NONE
```

Required post-persistence check:

```text
Producing Entry → Final Producing HEAD
→ ahead 4 / behind 0 / total commits 4
→ exactly 4 added evidence files
→ no unrelated commit
```

---

# 4. Changed-file Inventory

The complete producing inventory is intended to be exactly:

```text
1. docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_1_candidate_0.0.1.md

2. docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_1_dad_evidence_0.0.1.md

3. docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_1_review_audit_0.0.1.md

4. docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_1_handoff_0.0.1.md
```

```text
Existing Global State modified
→ 0

Existing Working State modified
→ 0

Ledger modified
→ 0

Decision Registry modified
→ 0

Accepted historical architecture evidence modified
→ 0

Source / implementation file modified
→ 0

Deletion
→ 0
```

---

# 5. Repository Recovery Result

Fresh recovery covered current Repository authority, including:

```text
Constitution
Unified Governance
Global State
Global Working State
Primary Ledger + continuation 0.0.1..0.0.25
Decision Registry 0.0.40
Runtime/Domain Stable Contract batching readiness assessment
Batch-1 authorization
accepted Runtime Responsibility Architecture
accepted Shared Foundation Architecture / Contract / Module / Provider evidence
five Product Component Internal Design closure evidence
accepted component-side Candidate / DAD / Global Acceptance evidence for RCP-01/02/03/04/19/24
```

Recovery result:

```text
Actual remote Branch HEAD at entry
→ d6b12f1d9901d810a61943c0c84b058db61746b2

Current Global State Epoch
→ GAC-EPOCH-0113

State Verified Through HEAD
→ 5674037c7ca8f35e2d85fc153836998f7aa9a006

Current Authorized Phase
→ Runtime / Domain Stable Contract Design / Batch 1

Authorization Scope
→ RUNTIME_DOMAIN_STABLE_CONTRACT_DESIGN_ONLY
  / BATCH_1
  / GOVERNANCE_INTENT_ADMISSION_PRESENCE_CONFIGURATION_READINESS_FOUNDATION

Decision Registry
→ 0.0.40 / GLOBAL_CURRENT / NORMATIVE

Open MDE at entry
→ 0

Unpersisted Owner Decision at entry
→ 0

Blocking Semantic Gap
→ NONE

Unexpected Drift at entry
→ NONE

Unauthorized Progression at entry
→ NONE

Repository Recovery
→ PASS
```

No chat history, memory, implementation convenience or prompt-carried old state was used as architecture authority.

---

# 6. RCP-01 Full Contract Result — Governance Context

```text
RCP-01
→ FULL CROSS-BOUNDARY REPRESENTATION-NEUTRAL STABLE CONTRACT SYNTHESIZED AT BATCH-1 PRODUCING LEVEL
```

Stable subject:

```text
Governance Context
→ qualified cross-boundary context/reference set
→ NOT Universal Governance Object
→ NOT Universal Mutable Session SoT
```

Mandatory preserved distinctions:

```text
Tenant != Organization
Principal != Authentication
Authenticated != Authorized
Policy != Trust
Reference != Authority
Context Propagation != Governance Authority
```

Contract closes:

- Tenant Context;
- Organization Context;
- Principal Context;
- Authentication Evidence Reference;
- Authorization/Policy Context Reference;
- Trust Context Reference;
- applicable revisions and temporal applicability;
- currentness/freshness/provenance;
- unknown/stale/unverifiable/indeterminate qualification;
- privacy/minimization/redaction;
- offline retained-context applicability;
- compatibility/conformance;
- producer/consumer obligations.

Authority result:

```text
Tenant / IAM / Organization / Policy / Trust Authorities
→ PRESERVED with accepted ns_server owners

RCP-01 Context Carrier Authority
→ NONE
```

No JWT/token/session/header/WebSocket envelope is defined.

---

# 7. RCP-02 Full Contract Result — Admission Evidence

```text
RCP-02
→ FULL CROSS-BOUNDARY REPRESENTATION-NEUTRAL STABLE CONTRACT SYNTHESIZED AT BATCH-1 PRODUCING LEVEL
```

Final authority:

```text
Formal Execution Admission
→ ns_server / S8 / SV-R04
```

Permanent:

```text
Admission Evidence != Admission Authority Transfer
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Receipt Success != Admission
Transport Success != Admission
Dispatch Success != Admission
```

Contract closes:

- Admission Evidence identity/reference;
- authoritative decision correlation;
- admitted work/artifact/definition/revision correlation;
- RCP-01 governance-context binding;
- applicability/currentness;
- expiry/revocation only where source semantics actually define them;
- unknown/stale/unavailable/indeterminate semantics;
- producer obligations;
- consumer applicability obligations;
- history/provenance/lineage;
- offline retained evidence;
- security/privacy/redaction;
- compatibility/conformance.

Consumer possession cannot mint, renew, extend or override Admission.

---

# 8. RCP-03 Full Contract Result — Presence

```text
RCP-03
→ FULL CROSS-BOUNDARY REPRESENTATION-NEUTRAL STABLE CONTRACT SYNTHESIZED AT BATCH-1 PRODUCING LEVEL
```

Final bounded fact owner:

```text
ns_runtime / R1 / RT-R01
```

Stable subject:

```text
Participant Reference
+ Presence Observation
+ connection qualification
+ reachability qualification
+ currentness qualification
+ observation time/applicability
+ provenance/history
```

Permanent:

```text
Connected != Trusted
Connected != Admitted
Reachable != Ready
Disconnected != Revoked
STALE != FALSE
UNKNOWN != DISCONNECTED
```

Presence does not become Participant Identity Authority, Trust Authority, Admission Authority, Node Readiness SoT or Universal Participant Registry.

Disconnect/reconnect are distinct observations; loss of observer access does not automatically prove disconnection; stale/unknown remain explicit.

---

# 9. RCP-19 Full Contract Result — Desired / Applied Config

```text
RCP-19
→ FULL CROSS-BOUNDARY REPRESENTATION-NEUTRAL STABLE CONTRACT SYNTHESIZED AT BATCH-1 PRODUCING LEVEL
```

Authority / actual-state topology:

```text
Canonical Managed Desired
→ ns_server / S9 / SV-R05

Applied Actual-state
→ applicable runtime Actual-state owner

Observed
→ projection / observation evidence
```

Permanent:

```text
Desired != Distributed != Applied != Observed
```

Contract closes:

- Configuration Subject Reference / semantic-owner reference;
- Desired revision/applicability;
- distribution correlation/evidence;
- Applied revision/evidence;
- partial application/failure/unknown/stale/conflicting;
- Observed evidence;
- currentness per plane;
- reconciliation compatibility;
- history/provenance/lineage;
- offline retained Desired reference;
- Secret Reference boundary;
- compatibility/migration/conformance;
- producer/consumer obligations.

Universal conflict laws remain absent:

```text
latest wins → NOT CREATED
central wins → NOT CREATED
local wins → NOT CREATED
```

---

# 10. RCP-24 Full Contract Result — Human / SDK Intent

```text
RCP-24
→ FULL CROSS-BOUNDARY REPRESENTATION-NEUTRAL STABLE CONTRACT SYNTHESIZED AT BATCH-1 PRODUCING LEVEL
```

Stable flow preserves:

```text
Intent Identity
Target Reference
Origin Surface
Origin Principal / RCP-01 context
Local possession/draft provenance where applicable
Submission occurrence
Receiving authority
Receipt correlation
Applicability evidence
Authoritative outcome correlation
History / resubmission lineage
Offline possession
Reconnect / re-observation
Privacy / compatibility
```

Permanent:

```text
Intent != Permit != Acceptance != Admission != Outcome
Local Possession != Submission != Receipt != Applicability != Application != Authoritative Outcome
```

Web and future SDK remain source surfaces only. Receiving semantic authority remains the target/domain owner.

Status/failure terms remain stage-qualified; no Universal Command Authority, Universal Command State Machine, universal winner rule or universal exactly-once guarantee is created.

Configuration-specific invariant:

```text
RCP-24 Configuration-change Intent
!= RCP-19 Canonical Desired-state
```

---

# 11. RCP-04 Full Contract Result — Node Readiness

```text
RCP-04
→ FULL CROSS-BOUNDARY REPRESENTATION-NEUTRAL STABLE CONTRACT SYNTHESIZED AT BATCH-1 PRODUCING LEVEL
```

Final owner:

```text
ns_node / N1 / ND-R01
```

Hard semantic definition basis:

```text
RCP-04 → RCP-01 + RCP-19
```

Bounded readiness subject:

```text
Node / Participant Reference
Capability Reference + revision
Applied Configuration correlation
Execution Mode context
→ ATTENDED / UNATTENDED where applicable
RCP-01 Governance Context
local prerequisite context
currentness / provenance / compatibility
```

Readiness values are semantic qualifications, not a universal boolean:

```text
READY
NOT_READY
UNKNOWN
INDETERMINATE
```

`STALE` remains orthogonal currentness qualification.

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

Presence is CACD/CEL where needed by an application, not RCP-04 semantic definition.

---

# 12. Final Contract Dependency Graph

Accepted Batch-1 hard CSDD graph is preserved exactly:

```text
RCP-02 → RCP-01
RCP-03 → RCP-01
RCP-19 → RCP-01
RCP-24 → RCP-01
RCP-04 → RCP-01, RCP-19
```

Dependency-first order:

```text
Stage 0
→ RCP-01

Stage 1
→ RCP-02
→ RCP-03
→ RCP-19
→ RCP-24

Stage 2
→ RCP-04
```

No feedback, response, re-observation, diagnostics, projection or historical edge was promoted into a reverse CSDD.

---

# 13. Acyclic Proof / Dependency-first Interpretation

Rank assignment:

```text
rank 0 → RCP-01
rank 1 → RCP-02 / RCP-03 / RCP-19 / RCP-24
rank 2 → RCP-04
```

Every hard CSDD edge points strictly from a higher rank to a lower rank.

Therefore:

```text
Hard Contract CSDD Graph
→ ACYCLIC
```

Typed non-CSDD relations remain:

```text
CACD → Application-context Dependency
CEL  → Contract Evidence Linkage
CHPL → Historical / Provenance Linkage
CXAR → Cross-authority Reference
```

This preserves evidence/runtime feedback without creating semantic-definition cycles.

---

# 14. Producer / Consumer Closure Result

All six RCPs have explicit producer and consumer obligations.

```text
Producer topology ambiguity
→ 0

Consumer topology ambiguity
→ 0

Producer obligation gap
→ 0

Consumer obligation gap
→ 0

Producer / Consumer Closure
→ PASS AT BATCH-1 PRODUCING LEVEL
```

High-risk preservation:

- RCP-01 carriers do not become governance authorities;
- RCP-02 consumers do not mint Admission;
- RCP-03 consumers do not infer Trust/Admission/Readiness;
- RCP-19 consumers preserve all four configuration planes;
- RCP-24 source surfaces do not own applicability/outcome;
- RCP-04 consumers do not infer Trust/Admission/Attempt/Effect.

---

# 15. Authority Transfer Result

```text
Authority Transfer
→ 0
```

No Governance, Admission, Presence, Configuration Desired, receiving-domain outcome or Node Readiness authority moved to a carrier, projection, consumer, recovery coordinator or future SDK surface.

```text
Authority Cycle
→ NONE
```

---

# 16. Source-of-Truth Transfer Result

```text
SoT Transfer
→ 0
```

Preserved:

```text
Governance constituent SoTs → accepted source authorities
Admission → S8
Desired Configuration → S9
Applied Configuration → applicable runtime owner
Presence observation → RT-R01 bounded fact owner
Node Readiness → N1
Target-domain outcome → receiving/source semantic owner
```

Projections, contexts, correlation evidence, caches and offline copies do not become source SoTs.

```text
SoT Cycle
→ NONE
```

---

# 17. Final Actual-state Ownership Transfer Result

```text
Final Actual-state Ownership Transfer
→ 0
```

Observed evidence, recovery/re-observation, diagnostics, context propagation and intent correlation do not absorb final source facts.

```text
Final Actual-state Ownership Cycle
→ NONE
```

---

# 18. Open MDE

```text
Open MDE
→ 0

Misclassified MDE Found
→ 0
```

The 12 bounded DADs stay below the MDE threshold.

Any later requirement for authority/SoT/final-owner transfer, universal identity/fail/winner/once/retry/cancel/reversal semantics, new cross-Tenant law, new RCP/role/component, mandatory online/public dependency, upstream architecture modification or hard CSDD cycle remains an immediate STOP condition.

---

# 19. Unpersisted Owner Decision

```text
Unpersisted Owner Decision
→ 0
```

No owner decision was invented or assumed by the producing session.

---

# 20. Mandatory Missing Shared Foundation Semantic

Applicable accepted Shared Foundation semantics were reused for:

```text
Temporal / Freshness
Technical Status / Uncertainty
Correlation / Provenance
Governed Context Propagation
Semantic Representation mechanics
Secret Reference
Sensitive-data Redaction
Compatibility / Conformance
Diagnostics
```

Result:

```text
MANDATORY_MISSING_SHARED_FOUNDATION_SEMANTIC
→ NONE_FOUND
```

No new Shared Foundation was created inside this Batch.

---

# 21. Security / Privacy / Non-leak Result

```text
SECURITY_PRIVACY_NON_LEAK_REVIEW
→ PASS

SECRET_REFERENCE_BOUNDARY_REVIEW
→ PASS
```

Preserved:

- Tenant/Organization/Principal/AuthN/AuthZ/Policy/Trust distinctions;
- authorization-aware disclosure;
- protected-existence/state non-leakage;
- sensitive metadata minimization;
- redaction through history/diagnostics/offline/re-observation;
- Secret Reference != Secret Material;
- Reference Possession != Permission to Resolve;
- no new Trust/Security/Privacy authority;
- no cross-Tenant disclosure law.

---

# 22. Offline / Private Result

```text
OFFLINE_PRIVATE_CORRECTNESS_REVIEW
→ PASS
```

Preserved:

```text
RCP-01 retained context → evidence only, no authority extension
RCP-02 retained Admission Evidence → source-bounded applicability only
RCP-03 last-known Presence → may become STALE/UNKNOWN
RCP-19 local Applied → local actual-state owner preserved; Desired stays S9
RCP-24 offline Intent possession → pre-submission fact only
RCP-04 offline-local Readiness → N1 bounded fact where sufficient local evidence exists
```

```text
Mandatory Public SaaS
→ NONE

Mandatory Online Control Plane
→ NONE

Offline Governance Bypass
→ 0
```

---

# 23. Compatibility / Migration / Conformance Result

```text
COMPATIBILITY_MIGRATION_CONFORMANCE_REVIEW
→ PASS
```

Conformance is semantic, not wire-format identity. A representation must preserve applicable subject identity/correlation, source owner, revision/applicability/currentness, uncertainty, provenance/history, security/privacy/redaction, Secret Reference and non-collapse invariants.

Unsupported/incompatible semantics remain explicit rather than silently coerced.

```text
REST/gRPC/WebSocket/JSON/Protobuf/DTO schema commitment
→ NONE

Provider/framework/storage commitment
→ NONE

Authority-changing migration
→ NONE
```

---

# 24. Implementation Leakage Result

```text
TECHNOLOGY_REPRESENTATION_LEAKAGE_REVIEW
→ PASS

SDK_PREMATURE_DESIGN_REVIEW
→ PASS

IMPLEMENTATION_LEAKAGE_REVIEW
→ PASS
```

Not selected/designed:

```text
wire protocol / API / DTO / schema
UUID format / database PK / ORM model
queue/topic/event/table/index/cache layout
process/thread/worker/coroutine/container topology
retry/backoff/idempotency algorithm
TTL / timeout / conflict algorithm
concrete SDK API/object model/client lifecycle
Implementation Planning / IWP / Coding
```

---

# 25. Unexpected Drift Result

At every producing write gate the remote HEAD matched the expected previous producing commit and the target path did not exist.

Pre-Handoff compare:

```text
d6b12f1d9901d810a61943c0c84b058db61746b2
→ 9e583c101d8cd028c11c2acda94efbbe9c069ff2

Ahead By
→ 3

Behind By
→ 0

Changed Files
→ exactly Candidate / DAD / Review

Unexpected Drift
→ NONE
```

Final determination is conditional only on immediate post-Handoff compare confirming exactly four linear commits / four files.

---

# 26. Unauthorized Progression Result

```text
Unauthorized Progression
→ NONE
```

The producing session did not enter or authorize:

```text
Batch 2 / 3 / 4 / 5
RCPs outside 01/02/03/04/19/24
System-level SDK Detailed Design
Design-to-Implementation Readiness
Implementation Planning
Implementation Work Packages
Coding
Global Architecture governance mutation
```

---

# 27. Explicit Global Acceptance Status

```text
Global Acceptance
→ NOT CLAIMED
```

The producing session has no Global Acceptance Authority. Candidate/DAD/Review/Handoff evidence must be returned to GAC for independent acceptance.

---

# 28. Explicit Batch 2 Authorization Status

```text
Batch 2 Authorization
→ NONE
```

No later Runtime / Domain Stable Contract Design Batch is entered or authorized by this Handoff.

---

# 29. Explicit System-level SDK Detailed Design Status

```text
System-level SDK Detailed Design
→ NOT AUTHORIZED
```

RCP-24 references future SDK only as a future intent source surface. No SDK detailed design has been performed.

---

# 30. Required Review / Audit Result

All required producing reviews passed:

```text
REPOSITORY_RECOVERY_AUDIT → PASS
MAJOR_DECISION_ESCALATION_AUDIT → PASS
AUTHORITY_SOURCE_OF_TRUTH_AMBIGUITY_REVIEW → PASS
FINAL_ACTUAL_STATE_OWNERSHIP_REVIEW → PASS
CONTRACT_DEPENDENCY_INVARIANT_REVIEW → PASS
CONTRACT_SUBJECT_IDENTITY_REVIEW → PASS
PRODUCER_CONSUMER_OBLIGATION_REVIEW → PASS
GOVERNANCE_CONTEXT_NON_COLLAPSE_REVIEW → PASS
ADMISSION_DISPATCH_ATTEMPT_EFFECT_NON_COLLAPSE_REVIEW → PASS
PRESENCE_TRUST_ADMISSION_READINESS_NON_COLLAPSE_REVIEW → PASS
DESIRED_APPLIED_OBSERVED_NON_COLLAPSE_REVIEW → PASS
INTENT_APPLICABILITY_OUTCOME_NON_COLLAPSE_REVIEW → PASS
TENANT_ORGANIZATION_NON_COLLAPSE_REVIEW → PASS
PRINCIPAL_AUTHENTICATION_AUTHORIZATION_NON_COLLAPSE_REVIEW → PASS
OFFLINE_PRIVATE_CORRECTNESS_REVIEW → PASS
RECOVERY_REOBSERVATION_NON_CANONICALIZATION_REVIEW → PASS
SECURITY_PRIVACY_NON_LEAK_REVIEW → PASS
SECRET_REFERENCE_BOUNDARY_REVIEW → PASS
FAILURE_UNKNOWN_CURRENTNESS_REVIEW → PASS
HISTORY_PROVENANCE_CORRELATION_REVIEW → PASS
COMPATIBILITY_MIGRATION_CONFORMANCE_REVIEW → PASS
SHARED_FOUNDATION_REUSE_REVIEW → PASS
TECHNOLOGY_REPRESENTATION_LEAKAGE_REVIEW → PASS
RCP_SCOPE_OVERCLAIM_REVIEW → PASS
SDK_PREMATURE_DESIGN_REVIEW → PASS
IMPLEMENTATION_LEAKAGE_REVIEW → PASS
GIT_DRIFT_REVIEW → PASS
```

```text
Review Tally
→ 27 PASS / 0 FAIL / 0 BLOCKED
```

---

# 31. Bounded Producing End State

Subject to successful post-persistence Git verification:

```text
NGRP-001
— Runtime / Domain Stable Contract Design
/ Batch 1
/ RCP-01 + RCP-02 + RCP-03 + RCP-04 + RCP-19 + RCP-24

→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

Explicitly:

```text
RCP-01..24 Full Cross-component Closure
→ NOT CLAIMED

Runtime / Domain Stable Contract Design Exhaustion
→ NOT CLAIMED

Runtime / Domain Stable Contract Design Global Completion
→ NOT CLAIMED

Global Acceptance
→ NOT CLAIMED

Batch 2 Authorization
→ NONE

System-level SDK Detailed Design
→ NOT AUTHORIZED

Design-to-Implementation Readiness
→ NOT CLAIMED

Implementation Planning / IWP / Coding
→ NOT AUTHORIZED
```

---

# 32. STOP / RETURN TO GAC

After this Handoff commit is persisted and externally verified as the fourth and only final producing commit:

```text
STOP
→ RETURN TO GAC
```

The bounded producing session has no legal authority to mutate Global State/Ledger/Decision Registry, declare Global Acceptance, or proceed into Batch 2.