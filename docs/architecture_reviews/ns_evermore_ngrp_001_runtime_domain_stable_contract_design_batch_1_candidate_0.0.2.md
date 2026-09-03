# NGRP-001 — Runtime / Domain Stable Contract Design / Batch 1 — Candidate 0.0.2

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Runtime / Domain Stable Contract Design / Batch 1 / Correction Reissuance`
- Session Type: `BOUNDED CORRECTION-REISSUANCE SESSION`
- Authorization Scope: `RUNTIME_DOMAIN_STABLE_CONTRACT_DESIGN_ONLY / BATCH_1 / CORRECTION_REISSUANCE / RCP24_PRODUCER_TOPOLOGY_SCOPE_RECONCILIATION_ONLY`
- Authorized RCP Baseline: `RCP-01 / RCP-02 / RCP-03 / RCP-04 / RCP-19 / RCP-24`
- Correction Authorization Seal / Producing Entry HEAD: `c2495faefaf09c38d07b559b6d58fda73038da95`
- Entry Global State: `GAC-EPOCH-0114`
- State Verified Through HEAD: `5d05cc9560e200300a77c6dba08e10070d36f7d0`
- Entry Transition: `GAC-TR-0125`
- Decision Registry: `0.0.40 / GLOBAL_CURRENT / NORMATIVE`
- Frozen Original Candidate: `0.0.1 / f9966824b12f43c5043440a231b4cc9adf55d2cc / HISTORICAL / CORRECTION_REQUIRED INPUT`
- Global Acceptance Authority: `NONE`
- Candidate Status: `CORRECTION REISSUED / AWAITING DAD 0.0.2`

This document is the authorized correction reissuance of the complete Batch-1 Stable Contract baseline. The only substantive correction is `RCP-24 Producer Topology Scope Reconciliation`, plus directly affected consistency text. `RCP-01`, `RCP-02`, `RCP-03`, `RCP-19` and `RCP-04` are reissued as non-regression baseline and are not substantively redesigned.

The original `0.0.1` producing evidence remains immutable historical evidence and is not modified by this correction.

---

# 1. Fresh Repository Recovery

Fresh Repository recovery before the first correction write established:

```text
Actual remote Branch HEAD
→ c2495faefaf09c38d07b559b6d58fda73038da95

Correction Authorization Seal parent
→ 5d05cc9560e200300a77c6dba08e10070d36f7d0

Current Global State Epoch
→ GAC-EPOCH-0114

State Verified Through HEAD
→ 5d05cc9560e200300a77c6dba08e10070d36f7d0

Current Transition
→ GAC-TR-0125

Current Authorized Phase
→ NGRP-001 — Runtime / Domain Stable Contract Design / Batch 1 Correction Reissuance

Authorization Scope
→ RUNTIME_DOMAIN_STABLE_CONTRACT_DESIGN_ONLY
  / BATCH_1
  / CORRECTION_REISSUANCE
  / RCP24_PRODUCER_TOPOLOGY_SCOPE_RECONCILIATION_ONLY

Decision Registry
→ 0.0.40 / GLOBAL_CURRENT / NORMATIVE

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Semantic Gap
→ RCP-24 PRODUCER TOPOLOGY SCOPE AMBIGUITY / CORRECTION AUTHORIZED

Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE

Recovery Gate
→ PASS
```

The four authorized correction paths were verified absent immediately before the first write:

```text
candidate_0.0.2.md → NOT FOUND

dad_evidence_0.0.2.md → NOT FOUND

review_audit_0.0.2.md → NOT FOUND

handoff_0.0.2.md → NOT FOUND
```

## 1.1 GAC correction evidence consumed

Direct correction authority:

```text
docs/architecture_reviews/
ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_1_global_review_correction_required_0.0.1.md

GAC result
→ CORRECTION_REQUIRED

Unique blocker
→ RCP-24 PRODUCER TOPOLOGY SCOPE AMBIGUITY
```

Current ledger authority:

```text
docs/governance/global_architecture/
ns_evermore_global_architecture_ledger_continuation_0.0.26.md

GAC-TR-0125
→ authorize correction reissuance only
```

The correction evidence independently accepted the non-regression baseline:

```text
RCP-01 → PASS
RCP-02 → PASS
RCP-03 → PASS
RCP-19 → PASS
RCP-04 → PASS
Hard Contract CSDD → ACYCLIC / PASS
Authority Transfer → 0
SoT Transfer → 0
Final Actual-state Ownership Transfer → 0
Mandatory Missing Shared Foundation Semantic → NONE_FOUND
Security / Privacy / Secret Reference → PASS
Offline / Private → PASS
Recovery / Re-observation → PASS
Compatibility / Migration / Conformance → PASS
Technology / Representation Leakage → 0
Implementation Leakage → 0
```

## 1.2 Frozen original producing chain

```text
d6b12f1d9901d810a61943c0c84b058db61746b2
→ f9966824b12f43c5043440a231b4cc9adf55d2cc  Candidate 0.0.1
→ a2929f986e753136fa2ae114125f3efd0a4ce02b  DAD 0.0.1
→ 9e583c101d8cd028c11c2acda94efbbe9c069ff2  Review / Audit 0.0.1
→ 9c0393942402af9454622be5e07fb70165215e6c  Handoff 0.0.1
```

```text
Original 0.0.1 Evidence
→ AUTHORIZED HISTORICAL PRODUCING EVIDENCE
→ CORRECTION_REQUIRED INPUT
→ READ ONLY
```

---

# 2. Correction Boundary

The correction may change only:

```text
RCP-24 producer-topology wording and closure
Candidate consistency directly affected by that topology
RDSC-B1-DAD-006 consistency
Producer / Consumer audit consistency
RCP Scope audit consistency
SDK premature-design audit consistency
Handoff consistency
```

Not reopened:

```text
RCP-01 semantic design
RCP-02 semantic design
RCP-03 semantic design
RCP-19 semantic design
RCP-04 semantic design
RCP-12 Agent Delegation design
Runtime Responsibility Architecture
Component Internal Design
Shared Foundation design
```

No new Product Component, Runtime Role, RCP, Authority, SoT, final Actual-state owner, universal identity namespace, conflict-winner law, fail law, once/retry/cancel/reversal law or technology commitment is introduced.

---

# 3. Contract Synthesis Discipline

## 3.1 Stable Contract is semantic, not representational

The Stable Contract baseline remains representation-neutral. It does not select:

```text
REST / GraphQL / gRPC
WebSocket / SSE
Kafka / RabbitMQ / Redis Stream
JSON Schema / Protobuf / Avro
Pydantic DTO / TypeScript Interface
UUID format / database PK / ORM model
endpoint / queue / topic / table / index / cache
process / service / worker / thread / coroutine / deployment topology
```

Any later representation must conform to these semantics rather than define them.

## 3.2 Contract relationship taxonomy

```text
CSDD
→ Contract Semantic-definition Dependency
→ only relation participating in hard semantic-definition cycle analysis

CACD
→ Application-context Dependency

CEL
→ Contract Evidence Linkage

CHPL
→ Contract Historical / Provenance Linkage

CXAR
→ Cross-authority Reference
```

Response evidence, callbacks, history, re-observation, diagnostics and projections do not create reverse CSDD edges.

## 3.3 Hard CSDD graph — unchanged

```text
RCP-02 → RCP-01
RCP-03 → RCP-01
RCP-19 → RCP-01
RCP-24 → RCP-01
RCP-04 → RCP-01, RCP-19
```

Dependency-first order:

```text
Stage 0 → RCP-01
Stage 1 → RCP-02 / RCP-03 / RCP-19 / RCP-24
Stage 2 → RCP-04
```

No CSDD edge exists from RCP-04 to RCP-03. Presence can be application/evidence context for readiness consumers without defining readiness semantics.

---

# 4. Shared Cross-contract Semantic Discipline — Non-regression

## 4.1 Semantic subject identity

```text
Semantic Subject Identity
!= universal physical identifier namespace
!= database key
!= transport request ID
!= provider-native identifier automatically
```

Correlation remains distinct from ownership. RCP-24 Web-origin Intent identity is scoped to genuine `WB-R01` source occurrences and does not become a universal command identity namespace.

## 4.2 Temporal / currentness / uncertainty

Applicable Shared Foundation semantics remain reused for:

```text
observation/effective/applicability time
currentness / freshness
UNKNOWN
UNAVAILABLE
STALE
PARTIAL
CONFLICTING
INDETERMINATE
```

Permanent:

```text
UNKNOWN != FALSE / FAILED
UNAVAILABLE != DENIED
STALE != CURRENT / FALSE
PARTIAL != COMPLETE
CONFLICTING != winner selected
INDETERMINATE != REJECTED
Timestamp != Authority
Latest Timestamp != Canonical Winner
```

## 4.3 Governance context

All contracts consume RCP-01 rather than inventing local governance authority.

```text
Tenant != Organization
Principal != Authentication
Authenticated != Authorized
Policy != Trust
Reference != Authority
Context Propagation != Governance Authority
```

## 4.4 Security / privacy / Secret Reference

```text
Secret Reference != Secret Material
Reference Possession != Permission to Resolve
Redacted Evidence != Unredacted Authority
Diagnostic Visibility != Disclosure Authorization
```

Minimum disclosure, authorization-aware disclosure and redaction remain mandatory.

## 4.5 History / provenance / recovery

```text
Correlation != Ownership
Provenance != Authority Transfer
Recovery != SoT Transfer
Re-observation != Canonicalization
Reconnect != Reconciled
Replay / resubmission != Retroactive Authorization
Latest Timestamp / Arrival != Canonical Winner
```

History remains non-destructive.

## 4.6 Offline / private

All six contracts remain valid for private/offline-capable deployment without mandatory public Internet, public SaaS or mandatory online control plane. Offline possession may retain evidence but cannot mint or extend external authority.

## 4.7 Compatibility / migration / conformance

Semantic contract revision remains distinct from wire/provider revision. Unsupported/incompatible/unknown semantics must be explicit rather than silently coerced. Migration cannot change Authority, SoT, final Actual-state ownership or historical source fact ownership without separately accepted architecture action.

---

# 5. Stage 0 — RCP-01 Governance Context Stable Contract — NON-REGRESSION

## 5.1 Contract subject

`Governance Context` is a cross-boundary, representation-neutral set of qualified references needed to interpret an interaction, decision, observation, Intent, configuration state or readiness fact under applicable governance.

It is not:

```text
Universal Governance Object
Universal Mutable Session SoT
IAM Authority
Policy Authority
Trust Authority
Organization Authority
Tenant SoT
```

## 5.2 Semantic dimensions

Where applicable:

```text
Tenant Context
Organization Context
Principal Context
Authentication Evidence Reference
Authorization / Policy Context Reference
Trust Context Reference
applicable semantic / policy / trust revisions
temporal applicability / effective context
currentness / freshness
provenance / source authority references
privacy / disclosure / redaction qualification
compatibility / conformance qualification
unknown / stale / unverifiable qualification
offline retained-context applicability
```

Absence/unavailability of one dimension cannot be converted into another.

## 5.3 Producer topology

```text
Tenant semantics / canonical authority → ns_server / S1
Principal / native IAM semantics → accepted ns_server IAM partition
Organization semantics / factual bindings → ns_server / S2
Authorization / Policy semantics → ns_server / S3
Platform Trust / Security semantics → ns_server / S4
Governance Context composition → accepted ns_server composition responsibility
```

Composition/propagation does not transfer constituent authority.

## 5.4 Consumer obligations

Consumers may include runtime, node, agent, web, governed server boundaries and future separately authorized SDK surfaces. They must preserve Tenant/Organization and Principal/AuthN/AuthZ/Policy/Trust distinctions, source revisions/currentness/provenance, disclosure qualification and explicit uncertainty; propagated context never becomes governance SoT.

## 5.5 Failure / offline / history

`UNKNOWN`, `UNAVAILABLE`, `STALE`, `UNVERIFIABLE`, `INDETERMINATE` remain qualifications, not authorization outcomes. Historical occurrences retain applicable governance revisions. Offline possession does not extend Policy or Trust validity.

## 5.6 NOT OWNED

| Dimension | Result | Actual owner |
|---|---|---|
| Tenant semantic authority / canonical Tenant SoT | `NOT OWNED` | accepted ns_server Tenant authority |
| Organization semantic authority / factual bindings | `NOT OWNED` | accepted ns_server Organization authority |
| Principal/IAM authority | `NOT OWNED` | accepted ns_server IAM authority |
| Policy / Authorization authority | `NOT OWNED` | `ns_server / S3` |
| Trust authority | `NOT OWNED` | `ns_server / S4` |
| Mutable universal session state | `NOT OWNED / NOT CREATED` | none created |

## 5.7 Dependency / guarantee / revalidation

```text
Hard CSDD → NONE inside Batch 1
CACD/CEL/CHPL/CXAR → applicable governance authorities/evidence
```

Guarantee: dimensions remain distinct and source-qualified. Non-guarantee: no universal token/session/authentication/cache law.

```text
RCP-01 Correction Delta
→ NONE
```

---

# 6. Stage 1 — RCP-02 Admission Evidence Stable Contract — NON-REGRESSION

## 6.1 Authority

```text
Formal Execution Admission Authority
→ ns_server / S8 / SV-R04

Admission Evidence != Admission Authority Transfer
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Receipt / Transport / Dispatch Success != Admission
```

## 6.2 Contract subject

Admission Evidence remains evidence of an authoritative S8 Admission determination for a specifically correlated governed subject, including where applicable:

```text
Admission Evidence Identity / Reference
Admission Decision Reference
admitted Work / Artifact / Definition / Revision reference
RCP-01 Governance Context binding
applicability scope
currentness/freshness
effective/decision/observation time
expiry/revocation only where S8 defines it
producer provenance
history/lineage
compatibility/conformance
```

## 6.3 Producer obligations

S8/SV-R04 binds evidence to the authoritative Admission decision, exact subject/revision and governance context, exposes enough applicability/currentness to prevent stale historical evidence being treated as current, preserves provenance/history, and never equates transport/dispatch with Admission.

## 6.4 Consumer obligations

Runtime/execution/projection consumers correlate exact subject/context, evaluate source-defined applicability, do not mint/renew/extend/override Admission, do not infer rejection from unavailable/stale evidence unless source evidence establishes it, and do not infer Admission from connection/readiness/dispatch/attempt/effect.

## 6.5 Failure / offline / security

`UNKNOWN`, `UNAVAILABLE`, `STALE`, `INDETERMINATE` remain source-qualified. Retained evidence is usable only within source-defined applicability; local possession cannot extend validity. Disclosure is minimized and Secret Material is excluded.

## 6.6 NOT OWNED

| Dimension | Result | Actual owner |
|---|---|---|
| Formal Execution Admission | `NOT OWNED by carrier/consumer` | `ns_server / S8 / SV-R04` |
| Scheduling/Routing/Dispatch | `NOT OWNED` | `ns_runtime / RT-R02` |
| Node Readiness | `NOT OWNED` | `ns_node / N1 / ND-R01` |
| Attempt / Effect | `NOT OWNED` | applicable source owners |

## 6.7 Dependency / guarantee

```text
CSDD → RCP-01
CEL/CHPL → admitted subject and downstream correlation evidence
CXAR → S8 authority / source subject owner
```

```text
RCP-02 Correction Delta
→ NONE
```

---

# 7. Stage 1 — RCP-03 Presence Stable Contract — NON-REGRESSION

## 7.1 Authority

```text
Presence / Reachability coordination owner
→ ns_runtime / R1 / RT-R01
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

## 7.2 Subject / dimensions

A Presence Observation preserves:

```text
Participant Reference
Presence Observation Identity / Reference
Connection qualification
Reachability qualification
Currentness qualification
observation time / scope
producer provenance
RCP-01 context reference
historical lineage
compatibility/conformance
```

## 7.3 Producer obligations

RT-R01 emits only runtime coordination facts it can establish, preserves participant/source provenance, separates connection/reachability/currentness, exposes observation time and uncertainty, preserves history across disconnect/reconnect, and never infers Trust/Admission/Readiness.

## 7.4 Consumer obligations

Consumers do not infer Participant Identity Authority, Trust, Admission, Readiness, revocation or permanent absence from Presence evidence. `UNKNOWN`/`STALE` are not coerced into `DISCONNECTED`.

## 7.5 Offline / security / NOT OWNED

Last-known observations may become stale/unknown. Later reconnect creates new evidence rather than rewriting history. Presence existence/activity is disclosure-sensitive.

| Dimension | Result | Actual owner |
|---|---|---|
| Participant identity authority / universal registry | `NOT OWNED / NOT CREATED` | applicable identity authority |
| Trust | `NOT OWNED` | `ns_server / S4` |
| Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |
| Node Readiness | `NOT OWNED` | `ns_node / N1 / ND-R01` |
| Dispatch | `NOT OWNED` | `ns_runtime / RT-R02` |

## 7.6 Dependency / guarantee

```text
CSDD → RCP-01
CACD/CEL → routing/diagnostics where applied
CHPL → disconnect/reconnect/re-observation history
```

```text
RCP-03 Correction Delta
→ NONE
```

---

# 8. Stage 1 — RCP-19 Desired / Applied Config Stable Contract — NON-REGRESSION

## 8.1 Authority topology

```text
Canonical Managed Desired state
→ ns_server / S9 / SV-R05

Applied Configuration Actual-state
→ applicable runtime Actual-state owner

Observed Configuration
→ projection / observation evidence

Desired != Distributed != Applied != Observed
```

## 8.2 Subject

Where applicable:

```text
Configuration Subject Reference
Configuration Semantic-owner Reference
RCP-01 Governance Context
Desired Revision / applicability
Distribution correlation/evidence
Applied Revision / applicability
application evidence/provenance
Observed evidence/provenance
per-plane currentness/freshness
partial/failure/unknown/conflict qualification
recovery/reconciliation correlation
history/lineage
Secret Reference
compatibility/migration/conformance
```

## 8.3 Producer topology

### Desired producer

`ns_server / S9 / SV-R05` owns canonical managed Desired semantics/revision/history.

### Distribution evidence producer

A distributing/coordinating participant may emit delivery/correlation evidence only; distribution does not become Desired or Applied authority.

### Applied producer

Each applicable runtime Actual-state owner emits only Applied facts it genuinely owns, including N1 for Node-local Applied configuration and applicable Agent/runtime partitions for their own applied state.

### Observed producer

Observers/projectors expose source-qualified observation evidence only; Observed is not Applied SoT.

## 8.4 Consumer obligations / conflict

Consumers preserve all four planes, revisions/currentness/provenance, do not equate distribution with application, do not promote Web/projection to SoT, surface partiality/uncertainty, preserve history and do not select a generic conflict winner.

```text
latest wins → NOT A CONTRACT LAW
central wins → NOT A CONTRACT LAW
local wins → NOT A CONTRACT LAW
```

## 8.5 Offline / secret / NOT OWNED

Offline participants may retain Desired references and their own Applied facts. Retention does not move Desired SoT. Reconnect/re-observation does not canonicalize. Secret Reference may be carried; Secret Material is not ordinary config evidence.

| Dimension | Result | Actual owner |
|---|---|---|
| Canonical Desired-state | `NOT OWNED by consumers/applied producers` | `ns_server / S9 / SV-R05` |
| Applied Actual-state | `NOT OWNED by S9/Web/projection` | applicable runtime owner |
| Observed source fact authority | `NOT OWNED by observation` | source owner; observer owns observation only |
| Conflict winner | `NOT UNIVERSALLY DEFINED` | applicable semantic authority when lawfully determined |

## 8.6 Dependency / guarantee

```text
CSDD → RCP-01
CEL/CHPL → distribution/application/observation/reconciliation
CXAR → S9 Desired + applicable Applied owners
```

```text
RCP-19 Correction Delta
→ NONE
```

---

# 9. Stage 1 — RCP-24 Human / SDK Intent Stable Contract — CORRECTED

## 9.1 Contract purpose and permanent non-collapse

RCP-24 is the representation-neutral stable semantic boundary from the accepted Web Intent source role and a separately authorized future System-level SDK source seam to governed targets whose receiving semantic authority remains the owner of applicability and authoritative outcome.

Permanent:

```text
Intent
!= Permit
!= Acceptance
!= Admission
!= Outcome

Local Possession
!= Submission
!= Receipt
!= Applicability
!= Application
!= Authoritative Outcome
```

Web and future SDK are source surfaces only; neither is a Universal Command Authority.

## 9.2 Contract subject / identity

An Intent occurrence has stable semantics for:

```text
Intent Identity / Reference
Intent Semantic Category / Subject
Target Reference
Origin Source Responsibility
Origin Surface Context
Origin Principal / RCP-01 Governance Context
Local Possession / Draft provenance where applicable
Submission Occurrence
Receiving Authority Reference
Receipt Correlation
Applicability Evidence Correlation
Authoritative Outcome Correlation
History / provenance
Retry / resubmission lineage
Offline possession qualification
Reconnect / re-observation correlation
Privacy / redaction qualification
Compatibility / conformance qualification
```

For the current Product-side producer, Intent occurrence identity is scoped to genuine `ns_web / WB-R01` source facts. Browser request IDs or local UI identifiers are not automatically the semantic Intent identity. A future SDK realization must preserve the same semantic distinction after separate authorization, but no SDK physical identity or object model is designed here.

## 9.3 Corrected producer topology — closed and explicit

### Current Product-side source producer

```text
Current Product-side Source Producer
→ ns_web / WB-R01
```

Within `WB-R01`, the current RCP-24 producer contribution is restricted to accepted Web responsibilities that genuinely originate RCP-24 Intent/submission facts. The accepted current contribution set is:

```text
W1 — Governed Administration & Control Interaction
→ administration / governed command Intent
→ Web-origin Intent and submission occurrence facts only

W2 — Cross-domain Authoring & Semantic Interoperability
→ authoring / governed edit/change Intent
→ authoring submission occurrence facts only

W5 — Operational Observation, Trial, Intervention & Diagnostics
→ applicable Trial/intervention request Intent
→ cancel / retry / resume / recovery request Intent where accepted W5 semantics apply
→ Web-origin request/submission occurrence facts only
```

These contributions share the same architecture-level Web role `WB-R01`; they do not create separate Web authorities.

Permanent:

```text
WB-R01 source fact ownership
→ genuine Web-origin Intent/submission occurrence only

WB-R01
!= receiving applicability authority
!= target semantic outcome authority
!= Policy authority
!= Artifact Acceptance authority
!= Execution Admission authority
```

### Future source producer seam

```text
Future Source Producer
→ System-level SDK
→ FUTURE ONLY
→ active only after separate System-level SDK design / authorization
```

This Contract states only the future semantic source seam already present in accepted Runtime Responsibility pressure. It does not define SDK API, object model, command classes, transport, package, language binding, auth mechanism, retry/idempotency mechanism or lifecycle.

### No generic producer expansion

```text
Additional Generic Source-surface Producer Class
→ NOT CREATED
```

There is no open-ended `other human/source surface` producer category in this Contract. If a future architecture proposes another RCP-24 Intent source producer outside the accepted `ns_web/WB-R01` plus separately authorized System-level SDK topology, normal GAC revalidation is required before that producer is admitted.

## 9.4 RCP-12 non-overlap

Permanent:

```text
Agent Delegation
Agent cross-domain invocation
Agent→Node
Agent→Automation
→ RCP-12
→ NOT RCP-24 producers
```

RCP-24 does not absorb Agent intent/delegation merely because an Agent can cause downstream action. `RCP-12 Agent Delegation` remains a distinct accepted contract and is not redesigned by this correction.

```text
RCP-12 overlap introduced by correction
→ NONE
```

## 9.5 Source producer obligations

For W1/W2/W5 RCP-24 source occurrences, `ns_web / WB-R01` must:

1. establish a distinct Web-origin Intent occurrence and authoritative Target Reference;
2. identify the accepted source responsibility (`W1`, `W2` or `W5`) under which the occurrence genuinely originated;
3. bind the applicable Principal and RCP-01 Governance Context;
4. distinguish local possession/draft from actual submission;
5. preserve each submission occurrence and retry/resubmission lineage without historical mutation;
6. retain receipt/applicability/outcome only as externally correlated evidence rather than Web-owned authority;
7. preserve privacy, redaction and minimum disclosure;
8. preserve offline possession without implying successful submission, receipt, application or outcome;
9. never treat UI affordance, request construction or transport success as authorization/applicability/outcome.

A future authorized SDK source producer must satisfy equivalent semantic obligations for the SDK-origin occurrence, without changing the receiving authority boundary.

## 9.6 Receiving authority topology and obligations

The receiving semantic authority varies by governed target domain and remains the accepted owner of:

```text
Target-domain applicability
Authoritative semantic application/outcome
```

Where corresponding evidence exists, the receiving authority must:

- correlate receipt/applicability/outcome to the originating Intent and Target Reference;
- preserve its own authoritative lifecycle and decision semantics;
- not treat Web/SDK possession or transport success as Permit/Acceptance/Admission/Application;
- expose rejection/failure/pending/unknown/supersession only with source-qualified meaning;
- preserve RCP-01 context, provenance and history.

No universal receiving authority or Universal Command State Machine is created.

## 9.7 Status / failure / resubmission

```text
PENDING
→ applicability/outcome not yet established where target semantics support pending

REJECTED
→ authoritative only when receiving semantic authority establishes rejection

FAILED
→ stage-qualified; submission/transport failure != target semantic failure

SUPERSEDED
→ only when applicable semantic owner establishes supersession
→ not latest-wins

UNKNOWN / UNAVAILABLE / STALE / INDETERMINATE
→ explicit uncertainty/currentness
→ not implicit success/failure
```

No universal exactly-once, retry, deduplication, cancellation, reversal or delivery guarantee is created. Each actual submission occurrence remains distinguishable in lineage.

## 9.8 Intent versus RCP-19 Desired-state

A W1/W2/W5 or future SDK Intent may request a configuration change where the target semantics permit it, but:

```text
RCP-24 Configuration-change Intent
!= RCP-19 Canonical Desired-state
```

Only `ns_server / S9 / SV-R05` can establish canonical managed Desired state. Web/SDK source possession, submission or receipt does not become Desired SoT.

## 9.9 Offline / reconnect / history

Offline local possession is a source-surface fact only. It does not mean submission, receipt, applicability or application. Reconnect may enable a new submission or re-observation but cannot auto-apply an Intent or choose a winner among competing intents.

Historical lineage preserves the accepted source responsibility, originating Intent content/category/target context, each submission occurrence and subsequent authoritative evidence. Later source edits, latest browser state or a future SDK state cannot rewrite prior Web submissions.

## 9.10 Security / privacy / Secret Reference

Intent submission carries only governance/context/target information needed by the receiving authority. `Visible/constructible/submittable` is not `Authorized`. Sensitive values are minimized/redacted. Secret Reference may be carried when target semantics require it; the RCP-24 Stable Contract does not require Secret Material transport.

## 9.11 NOT OWNED

| Dimension | RCP-24 result | Actual owner |
|---|---|---|
| Policy permit | `NOT OWNED` | accepted Policy authority |
| Artifact Acceptance | `NOT OWNED` | applicable accepted acceptance authority |
| Formal Execution Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |
| Target applicability | `NOT OWNED by WB-R01 / future SDK` | receiving semantic authority |
| Authoritative target outcome | `NOT OWNED by WB-R01 / future SDK` | receiving/source owner |
| Canonical Desired configuration | `NOT OWNED` | `ns_server / S9 / SV-R05` |
| Agent Delegation | `NOT OWNED` | RCP-12 applicable Agent source owner |
| Universal command authority/state machine | `NOT OWNED / NOT CREATED` | none |
| Exactly-once / universal retry semantics | `NOT OWNED / NOT CREATED` | domain-specific only if separately accepted |
| Additional generic source producer class | `NOT OWNED / NOT CREATED` | none |

## 9.12 Dependency / guarantee / revalidation

```text
CSDD → RCP-01
CEL/CHPL → receipt/applicability/outcome/submission lineage
CXAR → receiving semantic authority / target owner
```

Guarantee: the current Product-side producer set is closed to `ns_web / WB-R01` genuine W1/W2/W5 Intent/submission contributions, while future SDK remains a separately authorized source seam; source occurrence and receiving applicability/outcome remain correlatable without authority collapse.

Non-guarantee: local possession, submission or receipt does not guarantee Permit, Acceptance, Admission, Application or Outcome.

Revalidate/STOP if future design requires:

```text
new RCP-24 producer outside accepted ns_web/WB-R01 + separately authorized SDK topology
Universal Command Authority / state machine
universal exactly-once / retry / cancel / reversal law
source-side applicability/outcome authority
cross-Tenant intent law
System-level SDK Detailed Design inside this phase
RCP-12 absorption into RCP-24
```

---

# 10. Stage 2 — RCP-04 Node Readiness Stable Contract — NON-REGRESSION

## 10.1 Authority / dependencies

```text
Final Node Readiness owner
→ ns_node / N1 / ND-R01

Hard CSDD
→ RCP-04 → RCP-01, RCP-19

RCP-03 relation
→ CACD/CEL where reachability context is applied
→ NOT hard CSDD
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

## 10.2 Bounded subject

Where applicable:

```text
Node / Participant Reference
Capability Reference / Revision
RCP-01 Governance Context
RCP-19 Applied Configuration correlation
Execution Mode Context → ATTENDED / UNATTENDED
local prerequisite context
Readiness Observation / Evidence Identity
currentness/freshness
history/provenance
compatibility/conformance
```

The same Node can be READY for one bounded capability/config/mode/context and NOT_READY/UNKNOWN/INDETERMINATE for another.

## 10.3 Qualifications

```text
READY
→ N1 positively establishes bounded technical prerequisites

NOT_READY
→ N1 positively establishes unmet bounded technical prerequisites

UNKNOWN
→ required evidence missing/unknown

INDETERMINATE
→ evidence exists but cannot yield a determinate result

STALE
→ orthogonal currentness qualification
```

## 10.4 Producer / consumer obligations

ND-R01 binds readiness to exact bounded subject, uses N1-owned actual state, preserves RCP-19 Applied evidence, separates capability existence from readiness, exposes currentness/provenance/compatibility, preserves uncertainty/history and mode context.

Consumers such as RT-R02/projections/diagnostics correlate exact scope/currentness and do not infer universal readiness, Trust, Admission, Presence, Attempt or Effect.

## 10.5 Offline / security / NOT OWNED

N1 can establish locally authoritative bounded readiness while disconnected when sufficient local evidence and retained applicable context/configuration exist. Offline READY does not imply reachability, Admission or Trust. Readiness/capability/configuration posture is disclosure-sensitive and subject to minimization/redaction.

| Dimension | Result | Actual owner |
|---|---|---|
| Presence / reachability | `NOT OWNED` | `ns_runtime / R1 / RT-R01` |
| Trust | `NOT OWNED` | `ns_server / S4` |
| Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |
| Canonical Desired | `NOT OWNED` | `ns_server / S9 / SV-R05` |
| Applied Config | `REFERENCED / not transferred` | applicable runtime owner; N1 owns Node-applied facts |
| Dispatch | `NOT OWNED` | `ns_runtime / RT-R02` |
| Attempt / Effect | `NOT OWNED` | applicable owners |

## 10.6 Dependency / guarantee

```text
CSDD → RCP-01, RCP-19
CEL/CACD → RCP-03 where reachability is applied
CHPL → readiness/config/mode/re-observation history
CXAR → N1 / S9 / governance authorities
```

```text
RCP-04 Correction Delta
→ NONE
```

---

# 11. Producer / Consumer Closure Matrix — Corrected

| RCP | Producer topology | Consumer topology | Producer obligation result | Consumer obligation result |
|---|---|---|---|---|
| RCP-01 | accepted `ns_server` governance authorities + context composition | runtime/node/agent/web/server/future authorized SDK contexts | qualified context references, revision/currentness/provenance/disclosure without authority transfer | preserve distinctions/applicability/source authority |
| RCP-02 | `ns_server / S8 / SV-R04` | runtime dispatch, execution participants, projections | authoritative Admission evidence bound to subject/context/applicability | verify applicability; never infer/extend Admission |
| RCP-03 | `ns_runtime / R1 / RT-R01` | RT-R02, projections, diagnostics, qualified consumers | connection/reachability/currentness observation + provenance | no Trust/Admission/Readiness inference |
| RCP-19 | S9 Desired + applicable runtime Applied + qualified distribution/observation evidence | runtime, readiness, reconciliation, Web/admin/diagnostics | distinct Desired/Distributed/Applied/Observed evidence | preserve planes/revisions/currentness; no winner inference |
| RCP-24 | **current:** `ns_web / WB-R01` genuine W1/W2/W5 source contributions; **future:** System-level SDK only after separate authorization; **generic additional producer:** none | governed receiving targets + source-side re-observation/history consumers | Intent/submission occurrence + source responsibility/context + external receipt/applicability/outcome correlation | receiving authority owns applicability/outcome; no Permit/Admission/Outcome inference from source/transport |
| RCP-04 | `ns_node / N1 / ND-R01` | RT-R02, projections, diagnostics, qualified consumers | bounded Node/Capability/AppliedConfig/Mode readiness evidence | no Presence/Trust/Admission/Attempt/Effect inference |

Result after correction:

```text
Producer topology ambiguity
→ 0

RCP-24 Web producer under-specification
→ 0

RCP-24 open-ended generic producer expansion
→ 0

Consumer topology ambiguity
→ 0

Producer obligation gap
→ 0

Consumer obligation gap
→ 0
```

---

# 12. RCP-24 Web Contribution Reconciliation

Accepted Web evidence is reconciled as follows:

```text
W1 / WB-R01
→ governed administration / command Intent
→ RCP-24 CURRENT SOURCE CONTRIBUTION

W2 / WB-R01
→ Web authoring / change Intent
→ RCP-24 CURRENT SOURCE CONTRIBUTION

W5 / WB-R01
→ Trial/intervention/cancel/retry/resume/recovery request Intent where applicable
→ RCP-24 CURRENT SOURCE CONTRIBUTION
```

These are responsibility-scoped producer contributions within one current Product-side source producer role:

```text
ns_web / WB-R01
```

They do not imply:

```text
W1 == W2 == W5 semantic responsibility
Web == receiving target authority
Web == universal command authority
```

Other Web boundaries remain governed by their accepted contracts/responsibilities and are not admitted as a generic RCP-24 producer category merely because they are human-facing.

---

# 13. RCP-12 / RCP-24 Separation

```text
RCP-12
→ Agent Delegation / cross-domain Agent participation

RCP-24
→ Human/Web and separately authorized future SDK Intent
```

Permanent:

```text
Agent Delegation != Human / SDK Intent producer class
Agent→Node != RCP-24 source producer
Agent→Automation != RCP-24 source producer
Agent cross-domain invocation != RCP-24 source producer
```

```text
RCP-12 redesign
→ NONE

RCP-12 overlap
→ NONE
```

---

# 14. Cross-RCP Invariant Review — Non-regression

```text
RCP-01 Governance Context
!= RCP-02 Admission Evidence
!= RCP-03 Presence
!= RCP-04 Node Readiness
!= RCP-19 Desired / Applied Config
!= RCP-24 Human / SDK Intent
```

Critical separations:

```text
Governance Context != Admission Evidence
Presence != Readiness
Desired != Applied != Observed
Intent != Admission
Intent != Canonical Desired-state
Presence != Trust
Readiness != Admission
Agent Delegation / RCP-12 != Human / SDK Intent / RCP-24
```

## 14.1 Authority / SoT / final-owner cycles

```text
Authority Cycle
→ NONE

SoT Cycle
→ NONE

Final Actual-state Ownership Cycle
→ NONE
```

The producer topology correction changes no authority owner.

## 14.2 Hard CSDD acyclic proof

```text
rank 0 → RCP-01
rank 1 → RCP-02 / RCP-03 / RCP-19 / RCP-24
rank 2 → RCP-04
```

All hard CSDD edges descend in rank.

```text
Hard Contract CSDD Graph
→ ACYCLIC
```

---

# 15. Shared Foundation Reuse — Non-regression

| Foundation semantic | RCP-01 | RCP-02 | RCP-03 | RCP-19 | RCP-24 | RCP-04 |
|---|---:|---:|---:|---:|---:|---:|
| Temporal / Freshness | M | M | M | M | M | M |
| Technical Status / Uncertainty | M | M | M | M | M | M |
| Correlation / Provenance | M | M | M | M | M | M |
| Governed Context Propagation | principal basis | consume | consume | consume | consume | consume |
| Semantic Representation | A | A | A | A | A | A |
| Secret Reference | A | A | A | M where applicable | A | A |
| Sensitive-data Redaction | M | M | M | M | M | M |
| Compatibility / Conformance | M | M | M | M | M | M |
| Diagnostics | A | A | A | A | A | A |

```text
MANDATORY_MISSING_SHARED_FOUNDATION_SEMANTIC
→ NONE_FOUND
```

---

# 16. Security / Privacy / Non-leak Synthesis — Non-regression

1. Contract references do not grant disclosure authority.
2. Protected existence/state must not leak via status, counts, errors or diagnostics.
3. Tenant, Organization, Principal, Authentication, Policy/Authorization and Trust remain distinct.
4. Stale/unknown authorization evidence is not Permit.
5. Secret Material is outside ordinary Stable Contract evidence.
6. Redaction survives history, diagnostics, offline retention and re-observation.
7. No cross-Tenant producer or correlation law is introduced.
8. RCP-24 producer correction does not authorize any new source surface.
9. Future SDK existence as a semantic seam does not create current disclosure or action authority.

```text
Security / Privacy Authority Transfer
→ 0

New Trust Boundary
→ 0

Mandatory Public SaaS
→ 0
```

---

# 17. Recovery / Re-observation / Historical Correctness — Non-regression

Across all six RCPs:

```text
Recovery != SoT Transfer
Re-observation != Canonicalization
Reconnect != Reconciled
Replay / resubmission != Retroactive Authorization
Latest timestamp / arrival != Canonical Winner
```

RCP-24 additionally preserves the exact accepted Web source responsibility and submission occurrence in historical lineage. Re-observation cannot reinterpret a prior W1/W2/W5 source occurrence as originating from another producer.

---

# 18. Compatibility / Migration / Conformance — Non-regression

Conformance preserves:

```text
semantic subject identity / correlation
source producer responsibility
source authority / SoT / final-owner
revision / applicability / currentness
uncertainty
history / provenance
Tenant/security/privacy/redaction
Secret Reference boundary
cross-RCP non-collapse invariants
```

For RCP-24, conforming representations must preserve whether an occurrence is a current Web/WB-R01 source fact or a future separately authorized SDK source fact. A representation must not synthesize an unaccepted generic producer class.

No common wire schema is required.

---

# 19. Explicit Batch-1 Guarantees / Non-guarantees

Guarantees:

- representation-neutral Contract subjects;
- explicit producer/consumer obligations;
- Authority/SoT/final-owner preservation;
- explicit currentness/uncertainty;
- private/offline historical interpretability without authority creation;
- privacy/redaction/Secret Reference preservation;
- non-canonicalizing recovery/re-observation;
- semantic compatibility/conformance;
- acyclic Hard CSDD;
- **closed RCP-24 current producer topology: `ns_web/WB-R01` W1/W2/W5 contributions only, plus future SDK after separate authorization; no generic additional producer class.**

Not guaranteed / not created:

```text
universal exactly-once delivery/application
universal retry/cancel/rollback/reversal
universal fail-open/fail-closed
universal latest/central/local winner
universal identity namespace
universal mutable session SoT
universal participant registry
universal command state machine
universal readiness boolean
mandatory online control plane
mandatory public SaaS
provider/framework/protocol/storage lock-in
current SDK implementation/API/object model
additional generic RCP-24 producer class
```

---

# 20. MDE / Revalidation Stop Boundary

STOP and RETURN TO GAC/Owner if further design requires:

```text
new Product Component
new Runtime Role
new RCP
Authority transfer
SoT transfer
Final Actual-state Ownership transfer
universal identity namespace
universal latest/central/local winner
universal fail-open/fail-closed
universal exactly-once / retry / cancel / reversal / rollback
new product-significant cross-Tenant law
mandatory public SaaS
mandatory online control plane
mandatory provider/framework/protocol/storage lock-in
accepted upstream architecture modification
hard Contract CSDD cycle
new mandatory Shared Foundation semantic
new RCP-24 producer outside accepted ns_web/WB-R01 + separately authorized future SDK topology
RCP-12 absorption into RCP-24
System-level SDK Detailed Design
```

Current correction result:

```text
Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Blocking Semantic Gap after Candidate correction
→ NONE FOUND AT CANDIDATE LEVEL
```

---

# 21. Candidate 0.0.2 Exit State

```text
RCP-01 Stable Contract
→ REISSUED / NON-REGRESSION PASS

RCP-02 Stable Contract
→ REISSUED / NON-REGRESSION PASS

RCP-03 Stable Contract
→ REISSUED / NON-REGRESSION PASS

RCP-19 Stable Contract
→ REISSUED / NON-REGRESSION PASS

RCP-24 Stable Contract
→ CORRECTED / PRODUCER TOPOLOGY RECONCILED

RCP-04 Stable Contract
→ REISSUED / NON-REGRESSION PASS

RCP-24 Current Product-side Source Producer
→ ns_web / WB-R01

W1/W2/W5 current Web source contributions
→ EXPLICIT / CLOSED

Future SDK
→ SEMANTIC SOURCE SEAM ONLY / FUTURE / REQUIRES SEPARATE AUTHORIZATION

Additional Generic Source-surface Producer Class
→ NOT CREATED

RCP-12 overlap
→ NONE

Producer / Consumer closure
→ CLOSED AT CANDIDATE CORRECTION LEVEL

Authority Transfer
→ 0

SoT Transfer
→ 0

Final Actual-state Ownership Transfer
→ 0

Hard Contract CSDD Graph
→ ACYCLIC

Unexpected Drift
→ NONE AT FIRST WRITE

Unauthorized Progression
→ NONE

Global Acceptance
→ NOT CLAIMED

Batch 2 Authorization
→ NONE

System-level SDK Detailed Design
→ NOT AUTHORIZED
```

The only legal next producing action is `DAD Evidence 0.0.2`, after a fresh Git drift gate. No other Batch-1 semantics are reopened.