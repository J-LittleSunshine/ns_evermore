# NGRP-001 — Runtime / Domain Stable Contract Design / Batch 3 — Candidate

## 0. Authority Metadata

- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Phase: `NGRP-001 — Runtime / Domain Stable Contract Design / Batch 3`
- Authorization Scope: `RUNTIME_DOMAIN_STABLE_CONTRACT_DESIGN_ONLY / BATCH_3 / CONTINUATION_AUTOMATION_MULTI_AGENT_DELEGATION_COMPOSITION`
- Authorized RCPs: `RCP-06 / RCP-11 / RCP-12 / RCP-13 / RCP-14 / RCP-15`
- Authorization Epoch: `GAC-EPOCH-0120`
- Authorization Transition: `GAC-TR-0131`
- Producing Entry HEAD: `c00e7c5c8859f32f8d88bb140cbd46af19e7767d`
- State Verified Through HEAD: `65bbb74191e6f57444e3cfd26a25b3cddfdce5d8`
- Decision Registry: `0.0.42 / GLOBAL_CURRENT / NORMATIVE`
- Candidate Status: `COMPLETED / AWAITING DAD + REVIEW / NOT GLOBAL ACCEPTANCE`

This artifact is a bounded Stable Contract candidate. It does not exercise Global Acceptance Authority, does not advance the GAC Epoch, does not mutate Global State / Working State / Ledger / Decision Registry, does not authorize Batch 4 or Batch 5, and does not authorize System-level SDK Detailed Design or implementation work.

---

# 1. Fresh Repository Recovery Result

Fresh recovery from the actual remote branch established:

```text
Actual Remote Branch HEAD
→ c00e7c5c8859f32f8d88bb140cbd46af19e7767d

Expected Authorization Seal
→ c00e7c5c8859f32f8d88bb140cbd46af19e7767d

Authorization Seal Parent / State Verified Through HEAD
→ 65bbb74191e6f57444e3cfd26a25b3cddfdce5d8

Current Global State Epoch
→ GAC-EPOCH-0120

Current Authorized Phase
→ NGRP-001 — Runtime / Domain Stable Contract Design / Batch 3

Authorization Scope
→ RCP-06 / RCP-11 / RCP-12 / RCP-13 / RCP-14 / RCP-15 ONLY

Decision Registry
→ 0.0.42 / GLOBAL_CURRENT / NORMATIVE

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Semantic Gap
→ NONE

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE
```

The primary Global Architecture Ledger and every continuation through `0.0.32` were recovered. The older batching-assessment wording that over-hardened some Batch-3 relationships is superseded for Contract semantic-definition analysis by the later accepted RT-R03, A5/A6 and S6 Component Internal Design evidence and the `GAC-EPOCH-0119/0120` readiness/authorization evidence.

No repository contradiction requiring return to GAC was found.

---

# 2. Normative Upstream and Non-redesign Boundary

The following already Global Accepted Stable Contracts are `NORMATIVE UPSTREAM` and are not redesigned here:

```text
RCP-01 / RCP-02 / RCP-03 / RCP-04
RCP-05 / RCP-07 / RCP-08 / RCP-09 / RCP-10
RCP-19 / RCP-23 / RCP-24
```

Accepted Component evidence consumed without reopening internal design:

```text
RCP-06 principal coordination owner
→ ns_runtime / R3 / RT-R03

RCP-11 composition coordination/provenance owner
→ ns_agent / A5 / AG-R03

RCP-11 participant Agent runtime facts
→ ns_agent / A2 / AG-R01 / RCP-09

RCP-12 Agent-side cross-domain participation/provenance owner
→ ns_agent / A6 / AG-R04

RCP-13 Automation Operation / Semantic Continuation
→ ns_server / S6 / AU07 / SV-R02

RCP-14 Event source facts
→ original Event source owner

RCP-14 Trigger Definition / Trigger Evaluation
→ ns_server / S6; AU05 / SV-R02 for evaluation Actual-state

RCP-15 Automation composition binding / invocation semantics
→ ns_server / S6 / AU06 + AU07 / SV-R02
```

Accepted Node facts remain independently owned by `N1/ND-R01`, `N2/ND-R02`, `N3/ND-R03`, and `N4/ND-R04`. Accepted Web surfaces remain interaction/projection consumers and do not acquire upstream Authority, Source of Truth, or final Actual-state ownership.

The persisted Owner Decision `CID-SV-B2-MDE-001` remains normative and is not reopened:

```text
Native recursive Automation-to-Automation invocation
→ NOT SUPPORTED

Reusable Automation-to-Automation Composition
→ REQUIRED / PRESERVED

Canonical Composition Dependency
→ ACYCLIC
```

---

# 3. Shared Contract Discipline

## 3.1 Dependency taxonomy

This Batch uses exactly:

```text
CSDD → Contract Semantic-definition Dependency
CACD → Contract Application-context Dependency
CEL  → Contract Evidence Linkage
CHPL → Contract Historical / Provenance Linkage
CXAR → Cross-authority Reference
```

`A → B` under CSDD means only: A's Contract semantic definition depends on B's Contract semantic definition. Runtime request flow, response flow, evidence return, callbacks, target invocation, recovery flow, history or re-observation do not create CSDD by themselves.

Only CSDD participates in hard dependency ordering and semantic-definition cycle analysis.

## 3.2 Identity discipline

Every identity/reference in this Candidate is semantic and representation-neutral. It establishes the minimum identity needed to preserve source ownership, applicability, correlation, lineage, history and conformance.

It does **not** select UUIDs, database keys, message IDs, wire identifiers, DTOs, schemas or provider-native run identifiers.

Permanent:

```text
Reference != Authority
Correlation != Ownership
Possession != Permission
Projection != Source of Truth
Observation != Canonicalization
```

## 3.3 Common governed-context and security semantics

All six Contracts consume accepted governed context where applicable and preserve:

```text
Tenant != Organization
Principal != Authentication
Authenticated != Authorized
Policy != Trust
Reference Possession != Permission
Diagnostic Visibility != Disclosure Authority
Visible To One Participant != Visible To All Participants
Secret Reference != Secret Material
```

Accepted governance owners remain:

| Dimension | Batch-3 ownership | Accepted owner / authority |
|---|---|---|
| Tenant Semantic Authority | `NOT OWNED` | `ns_server` |
| Native Tenant canonical SoT | `NOT OWNED` | `ns_server`, with bounded external SoTs preserved where applicable |
| Organization Semantic Authority | `NOT OWNED` | `ns_server` |
| Organization factual SoT | `NOT OWNED` | declared per bounded Organization semantic partition / Organization System |
| Native IAM Semantic Authority | `NOT OWNED` | `ns_server` |
| Principal Authentication facts | `NOT OWNED` | applicable accepted authentication/source authority |
| Unified Policy Semantic Authority | `NOT OWNED` | `ns_server` |
| Platform Security / Trust Semantic Authority | `NOT OWNED` | `ns_server` |
| Formal Execution Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |

A Contract producer MUST NOT infer permission from a reference, participant membership, target selection, successful transport, source availability, local possession, or prior disclosure. A consumer MUST validate the applicable authorization/disclosure context for the requested semantic use.

Protected subject existence itself can be sensitive. Errors, counts, diagnostics, history, correlation, target/provider metadata and partial responses MUST NOT reveal a protected participant, target, Automation, Event source, resource, operation or relationship unless that disclosure is authorized.

## 3.4 Common currentness / uncertainty semantics

The accepted Shared Foundation Temporal/Freshness and Technical Status/Uncertainty semantics are reused. The following are orthogonal evidence qualifications, not a universal lifecycle enum or precedence lattice:

```text
UNKNOWN
→ required owner-qualified evidence is not known sufficiently to establish the requested semantic conclusion

UNAVAILABLE
→ required source/evidence/reference cannot currently be obtained or used for the requested semantic evaluation

UNREACHABLE
→ an applicable target/source cannot currently be reached as qualified by the owning coordination/source evidence

STALE
→ evidence exists but no longer satisfies the applicable currentness/freshness requirement

PARTIAL
→ only part of the required source scope/evidence has been established

CONFLICTING
→ source-qualified evidence conflicts and no accepted owner/winner rule has resolved it

INDETERMINATE
→ available evidence and accepted semantics are insufficient to determine the requested conclusion
```

None of these automatically means `FAILED`, `DENIED`, `SUCCEEDED`, `NONEXISTENT` or `CANCELLED`.

## 3.5 Common temporal / history / recovery semantics

Where applicable, Contract evidence preserves source-qualified occurrence/effective time, observation time and re-observation time as distinct concepts. No client clock, latest timestamp or latest arrival becomes a canonical winner.

History is non-destructive:

```text
Later Success != Earlier Failure Deletion
Later Observation != Earlier Observation Rewrite
Re-observation != Canonicalization
Replay != Retroactive Authorization
Recovery != SoT Transfer
Reconnect != Reconciled
Latest Timestamp != Canonical Winner
Latest Arrival != Canonical Winner
```

Batch 3 does not design RCP-20. Current evidence is only required to remain source-attributable, currentness-qualified, uncertainty-preserving and non-destructive so that future authorized RCP-20 semantics can consume it without rewriting its authority history.

## 3.6 Common compatibility / conformance semantics

Each Contract preserves:

- semantic Contract identity/revision where required;
- source Definition/revision or binding revision where semantically relevant;
- compatibility/conformance qualification independent from wire/provider/library versions;
- explicit `INCOMPATIBLE`, `UNKNOWN`, `PARTIAL` or equivalent bounded qualification rather than silent semantic loss;
- historical interpretation under the exact revision/binding that applied to the historical fact.

A newer Definition, Contract realization or provider version MUST NOT silently reinterpret an already-established historical semantic fact.

## 3.7 Shared Foundation reuse

The Candidate reuses accepted Shared Foundation contracts/mechanics for:

```text
Temporal / Freshness
Technical Status / Uncertainty
Operation / Correlation / Provenance Context
Governed Context Propagation
Semantic Representation
Network Invocation Mechanics where applicable
Secret Reference
Sensitive-data Redaction
Compatibility / Conformance
Diagnostics / Technical Observation where applicable
```

No Batch-3-local parallel Foundation capability, Contract, Module or Provider is created.

---

# 4. Stage 0 — RCP-06 Continuation / Intervention Stable Contract

## 4.1 Contract semantic subject and identity

`RCP-06` stabilizes **cross-component continuation / delegation / intervention coordination evidence** produced by `RT-R03` around a source-owned semantic subject. It does not redefine the source continuation, delegation or intervention semantics.

Representation-neutral identities/references include where applicable:

```text
Operation / Work Reference
R3 Coordination Request Identity
Requested Semantic Category / Requested-action Meaning
Source Semantic Owner Reference
Source Semantic Revision
Origin Reference
Target Reference
Governance Context Reference
Admission Reference
Dispatch Reference
Attempt / Effect / Agent Runtime References only when supplied by their source owners
Agent Delegation Reference where applicable
Human Response / HITL Correlation where applicable
R3 Coordination-stage Evidence Identity
Final-owner Outcome Reference where available
History / Provenance / Lineage references
Compatibility / Conformance qualification
```

`R3 Coordination Request Identity` and `R3 Coordination-stage Evidence Identity` are distinct from Operation, Admission, Dispatch, Attempt, Effect, Agent Operation, Automation Operation and source final-outcome identities.

## 4.2 Producer topology

Principal producer/source owner for RCP-06 coordination-stage facts:

```text
ns_runtime / R3 / RT-R03
```

Other source owners contribute only their own source evidence by reference. Examples include S6 for Automation continuation/HITL semantics, AG-R04 for Agent Delegation participation, AG-R01 for Agent runtime facts, S8 for Admission, RT-R02 for Dispatch, N2 for Attempt and N3 for Effect.

## 4.3 Consumer topology

Qualified consumers include where applicable:

1. the originating semantic owner that needs coordination-stage evidence to interpret its own continuation/intervention outcome;
2. target/receiving authorities that need a source-qualified request and governed correlation;
3. `ns_agent / A6 / AG-R04` for Agent cross-domain participation correlation without transferring R3 ownership;
4. `ns_server / S6` for Automation-specific continuation/HITL correlation without transferring S6 semantics to R3;
5. accepted Web interaction/projection consumers for authorized status/history/response correlation;
6. diagnostics/history/recovery consumers that preserve RT-R03 source attribution.

## 4.4 Producer obligations

RT-R03 MUST, when applicable:

- bind the request to the exact source Operation/Work subject and source semantic owner;
- preserve the requested semantic category without asserting that the requested action has been accepted or achieved;
- preserve origin/target and governed-context correlation without inferring permission from target/reference possession;
- record RT-R03-owned receipt, forwarding/handoff, pending, unreachable/unavailable, coordination failure, uncertainty and bounded coordination-completion evidence;
- correlate Admission/Dispatch/Attempt/Effect/Agent evidence only when the corresponding accepted source supplies it;
- preserve request/retry/re-entry lineage and prior evidence non-destructively;
- preserve source revision/currentness and disclose stale/unknown/conflicting/indeterminate states explicitly;
- redact protected target/source/participant details according to the applicable disclosure authority;
- expose compatibility/conformance qualification sufficient to prevent silent semantic reinterpretation.

## 4.5 Consumer obligations

Consumers MUST:

- distinguish the R3 request/stage evidence from the source semantic outcome;
- validate source owner, source revision, request category, governed context and applicable permission;
- preserve source-owned Admission, Dispatch, Attempt, Effect, Agent, Automation and HITL semantics;
- treat missing/stale/unavailable evidence as uncertainty rather than fabricate success/failure/nonexistence;
- preserve historical request and coordination evidence when later source outcomes arrive;
- avoid disclosing a target, participant, intervention subject or protected outcome through unauthorized diagnostics/history/errors.

## 4.6 Lifecycle / temporal / currentness

RCP-06 defines evidence dimensions, not a universal state machine. Depending on the source journey, evidence may establish request origination/correlation, receipt, forwarding/handoff, pending coordination, inability to reach/forward, bounded coordination completion and later final-owner outcome correlation. These dimensions are not required to be one physical sequence.

Currentness applies independently to coordination-stage evidence and any referenced source outcome. A current coordination receipt does not make a referenced source outcome current.

## 4.7 Authority / SoT / final Actual-state owner

| Dimension | RCP-06 result | Accepted owner |
|---|---|---|
| R3 Coordination Request/stage evidence | `OWNED` | `ns_runtime / R3 / RT-R03` |
| Source Semantic Continuation Authority | `NOT OWNED` | applicable source semantic owner |
| Agent Delegation source/participation | `NOT OWNED` | `ns_agent / A6 / AG-R04` |
| Automation continuation/HITL semantic outcome | `NOT OWNED` | `ns_server / S6 / SV-R02` |
| Formal Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |
| Dispatch | `NOT OWNED` | `ns_runtime / R2 / RT-R02` |
| Node Attempt | `NOT OWNED` | `ns_node / N2 / ND-R02` |
| Node Effect | `NOT OWNED` | `ns_node / N3 / ND-R03` |
| Agent Runtime Actual-state | `NOT OWNED` | `ns_agent / A2 / AG-R01` |
| Final source semantic outcome | `NOT OWNED` | applicable final source owner |

Permanent:

```text
Continuation Coordination != Source Semantic Continuation Authority
Delegation Coordination != Agent Delegation Source Authority
Intervention Request Received != Intervention Accepted
Intervention Forwarded != Intervention Applied
Cancel Requested != Cancelled
Retry Requested != Retry Started
Resume Requested != Resumed
Recovery Requested != Recovered
R3 Coordination Completed != Source Semantic Outcome Achieved
```

## 4.8 Dependency classification

```text
RCP-06 ↔ RCP-13
→ CACD / CEL / CXAR where Automation continuation participates
→ NOT CSDD

RCP-06 ↔ RCP-12
→ CACD / CEL / CHPL / CXAR as applicable
→ NOT CSDD
```

No Batch-3 peer semantic definition is a hard prerequisite for RCP-06.

## 4.9 Guarantees / non-guarantees / revalidation

Guarantees:
- RT-R03 coordination evidence remains distinct, attributable and non-authoritative for source outcomes.
- coordination history is non-destructive and currentness-qualified.
- protected source/target existence is disclosure-governed.

Explicit non-guarantees:
- no guarantee that a received/forwarded request is accepted, applied, completed or successful;
- no universal cancel/retry/resume/recovery semantics, once guarantee or rollback/compensation semantics;
- no transport/provider/reachability guarantee.

Revalidate if RT-R03 ownership changes, a source semantic owner changes, RCP-06 is made authoritative for source outcomes, a new universal intervention law is proposed, or accepted shared status/currentness/security semantics materially change.

---

# 5. Stage 0 — RCP-11 Multi-Agent Composition Stable Contract

## 5.1 Contract semantic subject and identity

`RCP-11` stabilizes **Multi-Agent Composition coordination and provenance**. It describes how multiple independently owned Agent runtime subjects participate in one composition context without merging their Actual-state or authority.

Stable identities/references include:

```text
Composition Operation Identity
Initiating Agent Operation Reference
Initiating Agent Definition Revision
Participant Agent Reference
Participant Effective Revision
Participant Membership / Relationship Correlation
Participant Agent Operation Reference
Participant Agent Runtime Attempt Reference where source-established
Composition Context Contribution Reference
Contribution Source Attribution
Composition Coordination-stage Evidence Identity
Participant Evidence Correlation
Composition Outcome Qualification
History / Provenance / Recovery Correlation
```

## 5.2 Producer topology

Principal producer:

```text
ns_agent / A5 / AG-R03
→ composition coordination / provenance facts
```

Participant Agent runtime facts remain produced by:

```text
ns_agent / A2 / AG-R01 / RCP-09
```

Each participant remains independently source-qualified.

## 5.3 Consumer topology

Qualified consumers include:

1. initiating and participant Agent runtime semantics needing composition correlation;
2. AG-R04 when a composed Agent participates cross-domain;
3. RT-R03 when cross-component coordination is required, without absorbing composition authority;
4. source-domain consumers that receive participant contributions/results under their own authority;
5. authorized Web/diagnostic/history consumers that project source-attributed composition evidence.

## 5.4 Producer obligations

AG-R03 MUST:

- establish a bounded Composition Operation identity and source-qualified initiating Agent reference;
- preserve each participant Agent identity, effective revision and relationship/membership correlation;
- preserve participant Agent Operation/Attempt references as participant-owned evidence, not as AG-R03 Actual-state;
- attribute each composition context/result contribution to its source;
- qualify participant coverage, partiality, unknown/unavailable/incompatible evidence and bounded composition outcome explicitly;
- preserve historical membership/revision/contribution provenance across retries/recovery/re-observation;
- apply authorization and redaction independently to participant existence, relationship, contribution and result evidence;
- never infer shared factual truth merely because information was visible inside a composition.

## 5.5 Consumer obligations

Consumers MUST:

- retain participant source attribution and effective revision;
- never interpret composition membership as authority transfer or disclosure authorization;
- never collapse participant Actual-state into a single merged AG-R03 actual state;
- treat missing participants/evidence as source-qualified partiality/uncertainty, not automatic participant failure/nonexistence;
- preserve contribution provenance when projecting or aggregating composition results.

## 5.6 Lifecycle / temporal / currentness

A Composition Operation may correlate changing participant evidence over time, but participant membership, revisions and evidence currentness are evaluated against the composition's applicable historical context. A later participant revision does not rewrite the revision that participated historically.

Composition completion is a bounded AG-R03 qualification over composition coordination evidence. It is not a universal merge of every participant's semantic outcome.

## 5.7 Authority / SoT / final Actual-state owner

| Dimension | RCP-11 result | Accepted owner |
|---|---|---|
| Composition coordination/provenance | `OWNED` | `ns_agent / A5 / AG-R03` |
| Participant Agent Runtime Actual-state | `NOT OWNED` | each applicable `ns_agent / A2 / AG-R01` source subject |
| Participant Agent Definition | `NOT OWNED` | applicable accepted Agent Definition authority |
| Cross-domain target outcome | `NOT OWNED` | applicable target/source owner |
| Automation workflow/composition authority | `NOT OWNED` | `ns_server / S6` where Automation is involved |
| Shared factual SoT | `NOT OWNED / NOT CREATED` | original factual source owners |

Permanent:

```text
Multi-Agent Composition != Separate Agent Authority
AG-R03 Composition Coordination != merged AG-R01 Actual-state
Composition Outcome != participant Actual-state Merge
Composition Context Contribution != shared factual SoT
Agent A invokes Agent B != Authority Transfer
Multi-Agent != Automation Workflow Authority
```

No universal supervisor, majority-wins, first-result-wins, supervisor-wins, shared-memory SoT or universal team state machine is created.

## 5.8 Dependency classification

```text
RCP-11 → RCP-09
→ CSDD / NORMATIVE UPSTREAM

Participant evidence return
→ CEL / CHPL

Cross-domain participation / coordination
→ CACD / CEL / CXAR as applicable
```

## 5.9 Guarantees / non-guarantees / revalidation

Guarantees:
- participant identities/revisions/contributions remain source-attributed;
- composition coordination does not merge participant authority/Actual-state;
- partiality/unknown/incompatible evidence remains explicit.

Non-guarantees:
- no universal participant selection, quorum, voting, winner, supervisor, shared-memory or result-merge algorithm;
- no guarantee that composition completion means every participant succeeded;
- no universal topology or scheduling law.

Revalidate if AG-R03 ceases to own composition coordination/provenance, RCP-09 participant semantics change materially, shared factual SoT is proposed, or any universal Agent-team authority/winner model is introduced.

---

# 6. Stage 0 — RCP-12 Agent Delegation Stable Contract

## 6.1 Contract semantic subject and identity

`RCP-12` stabilizes **Agent-side governed cross-domain participation / delegation / invocation / candidate-authoring provenance**. It does not make the Agent the authority of the target domain.

Stable identities/references include where applicable:

```text
Originating Agent Operation Reference
Agent Definition Revision
Agent Decision / Action-proposal Lineage
Cross-domain Participation Identity
Participation Kind / Target Classification
Target Reference
Target Revision / Capability Qualification
Governance Context
Admission Reference
Presence / Readiness References
Dispatch Correlation
RT-R03 Coordination Reference
Node Attempt / Effect References only when source-established
Automation Operation / Result References only when source-established
Agent Candidate-authoring Contribution
S6 Intake Correlation
Cross-domain Result Contribution
History / Recovery / Reconciliation Participation Correlation
```

## 6.2 Producer topology

Principal RCP-12 producer:

```text
ns_agent / A6 / AG-R04
```

Source-side inputs remain owned by their original authorities: A2/AG-R01 for originating Agent runtime/Decision facts; S8 for Admission; R1/N1 for applicable presence/readiness evidence; R2 for Dispatch; R3 for coordination-stage evidence; N2/N3 for Attempt/Effect; S6 for Automation Definition/runtime/composition/intake semantics; A3/AG-R02 for provider/model observations where relevant.

## 6.3 Consumer topology

Qualified consumers include:

1. originating A2/AG-R01 semantics consuming source-attributed cross-domain result contributions;
2. target domains receiving a governed Agent participation/invocation/candidate contribution;
3. RT-R03 for applicable handoff/coordination only;
4. S6 for Agent candidate-authoring intake or Agent invocation of Automation, without transferring Automation authority;
5. Node execution consumers where the admitted/dispatch journey reaches Node Attempt/Effect;
6. authorized Web/diagnostic/history consumers projecting cross-domain participation evidence.

## 6.4 Producer obligations

AG-R04 MUST:

- bind every participation to the exact originating Agent Operation and Agent Definition revision;
- preserve Agent Decision/action-proposal lineage without equating intent/proposal with target acceptance;
- identify the participation kind and target classification without assuming target authority;
- carry target revision/capability qualification only from target/source-authorized evidence;
- preserve governance, Admission, Presence/Readiness, Dispatch and RT-R03 references where applicable without absorbing their semantics;
- correlate Node Attempt/Effect or Automation Operation/result only when established by those source owners;
- preserve Agent Candidate-authoring provenance separately from canonical Automation Definition/Artifact acceptance;
- preserve S6 intake correlation separately from intake acceptance/canonicalization;
- return cross-domain result contributions to Agent runtime with source attribution/currentness/uncertainty intact;
- enforce minimum-authorized disclosure of target existence, target metadata and protected result evidence;
- preserve non-destructive history across retry/re-entry/recovery/reconciliation participation.

## 6.5 Consumer obligations

Consumers MUST:

- validate the originating Agent, participation kind, target, revisions, governance and permission independently;
- treat Agent intent/candidate/reference possession as non-authoritative for Admission, target acceptance or execution;
- preserve source ownership of Admission/Dispatch/Attempt/Effect/Automation and provider facts;
- return source-attributed result evidence without converting it into Agent-owned target truth;
- preserve stale/partial/unknown/conflicting/incompatible conditions and history.

## 6.6 Lifecycle / temporal / currentness

Participation evidence may cover candidate authoring, target selection/correlation, governed handoff, target-owned execution evidence and result contribution. These are separable evidence dimensions, not a universal delegation state machine.

Target evidence currentness is owned/qualified by the target/source semantics. AG-R04 may record the currentness observed/consumed for its participation, but does not create target currentness authority.

## 6.7 Authority / SoT / final Actual-state owner

| Dimension | RCP-12 result | Accepted owner |
|---|---|---|
| Agent cross-domain participation/provenance | `OWNED` | `ns_agent / A6 / AG-R04` |
| Originating Agent Runtime/Decision facts | `NOT OWNED` | `ns_agent / A2 / AG-R01` |
| Agent Definition | `NOT OWNED` | applicable Agent Definition authority |
| Formal Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |
| Presence / readiness | `NOT OWNED` | accepted R1 / N1 owners as applicable |
| Dispatch | `NOT OWNED` | `ns_runtime / R2 / RT-R02` |
| RT-R03 coordination | `NOT OWNED` | `ns_runtime / R3 / RT-R03` |
| Node Attempt | `NOT OWNED` | `ns_node / N2 / ND-R02` |
| Node Effect | `NOT OWNED` | `ns_node / N3 / ND-R03` |
| Provider/model observations | `NOT OWNED` | `ns_agent / A3 / AG-R02` for its bounded observations |
| Automation canonical Definition/composition/runtime outcome | `NOT OWNED` | `ns_server / S6 / SV-R02` |
| Agent Candidate-authoring contribution | `OWNED as contribution/provenance only` | `ns_agent / A6 / AG-R04` |
| Candidate acceptance/canonicalization | `NOT OWNED` | applicable S6/S8 accepted authority |

Permanent:

```text
Agent Delegation != Admission
Agent Delegation != Dispatch
Agent Delegation != Node Attempt
Agent Delegation != Node Effect
Agent invokes Automation != Automation Authority
Agent Candidate != Automation Canonical Definition
Candidate Possession != Artifact Acceptance
Agent Intent != Execution Admission
```

## 6.8 Dependency classification

```text
RCP-12 → RCP-09
→ CSDD / NORMATIVE UPSTREAM

RCP-12 ↔ RCP-06
→ CACD / CEL / CHPL / CXAR
→ NOT CSDD

RCP-12 ↔ RCP-10
→ CACD / CEL / CXAR
→ NOT CSDD

RCP-12 ↔ RCP-13 / RCP-15
→ CACD / CEL / CHPL / CXAR where Automation participates
→ NOT CSDD
```

## 6.9 Guarantees / non-guarantees / revalidation

Guarantees:
- Agent-side participation identity/provenance remains distinct from target authority and target Actual-state;
- candidate-authoring provenance is preserved without canonicalization by possession;
- cross-domain result contributions preserve original source attribution.

Non-guarantees:
- no target acceptance, Admission, Dispatch, Attempt, Effect or Automation success guarantee;
- no universal delegation retry/cancel/rollback policy;
- no target/provider/framework choice or execution topology.

Revalidate if AG-R04 ownership changes, RCP-09 semantics change materially, target authority is proposed to transfer to Agent delegation, Agent Candidate is proposed as canonical Automation Definition, or any non-hard target relationship is proposed as a new CSDD without new Repository authority.

---

# 7. Stage 0 — RCP-14 Event Trigger Input / Evaluation Stable Contract

## 7.1 Contract semantic subject and identity

RCP-14 contains two deliberately separate authority partitions:

```text
Event source / occurrence facts
→ original Event source owner

Trigger Definition / Trigger Evaluation
→ ns_server / S6; AU05 / SV-R02 for Trigger Evaluation Actual-state
```

Stable identities/references include:

```text
Event Source Identity / Reference
Event Source Bounded-authority Qualification
Event Occurrence Identity
Event Semantic Revision
Event Provenance
Occurrence Time
Observation / Re-observation Time
Trigger Definition Identity / Revision
Trigger Applicability Qualification
Trigger Evaluation Identity
Trigger Evaluation Result
Duplicate / Re-observation Qualification
Replay / Re-evaluation Lineage
Stale / Out-of-order / Conflicting Qualification
History / Compatibility / Conformance references
```

## 7.2 Producer topology

Principal producers are partitioned:

1. original Event source owner produces authoritative facts for its own Event source/occurrence semantic partition;
2. `ns_server / S6 / AU05 / SV-R02` produces Trigger Evaluation identity/result and its own evaluation Actual-state;
3. S6's accepted Automation Definition authority owns Trigger Definition semantics where Trigger Definition is part of Automation semantics.

No transport/broker/provider becomes Event or Trigger Authority by carrying an observation.

## 7.3 Consumer topology

Qualified consumers include:

1. AU05 Trigger Evaluation consuming authorized source Event evidence;
2. AU07 Automation continuation/runtime semantics consuming source-qualified Trigger Evaluation where applicable;
3. S8 Admission semantics when an evaluated trigger leads to a request for execution, without collapsing match into Admission;
4. diagnostics/history/recovery consumers preserving event occurrence/evaluation lineage;
5. authorized Web projection consumers.

## 7.4 Producer obligations

Original Event source owners MUST preserve source identity, occurrence identity, semantic revision, source provenance and occurrence-time semantics for the facts they own.

AU05 MUST:

- bind evaluation to an exact Trigger Definition revision and applicable Event occurrence/source evidence;
- distinguish first observation from re-observation of the same occurrence;
- preserve duplicate qualification without inventing a new occurrence;
- preserve replay/re-evaluation lineage without retroactively creating Admission or rewriting prior evaluation;
- qualify stale/out-of-order/conflicting/partial/unknown source evidence explicitly;
- preserve policy/governance/disclosure context without becoming Policy Authority;
- redact Event source existence/content and Trigger details when disclosure is not authorized;
- preserve compatibility/conformance between Event semantic revision and Trigger evaluation semantics.

## 7.5 Consumer obligations

Consumers MUST:

- preserve the distinction between Event occurrence, observation and Trigger Evaluation;
- never infer execution Admission from Trigger match;
- never infer Event occurrence from a Trigger Evaluation lacking source-qualified occurrence evidence;
- preserve duplicate/re-observation/replay lineage and historical evaluations;
- reject or explicitly qualify incompatible/unknown semantic revisions rather than silently reinterpret them;
- avoid leaking protected Event source/content through trigger errors, counts or diagnostics.

## 7.6 Lifecycle / temporal / currentness

Event occurrence time belongs to the applicable Event source semantics. Observation and re-observation time describe evidence acquisition, not event creation. Trigger evaluation has its own evaluation-time/currentness context.

Permanent:

```text
same Event Occurrence re-observed != new Event Occurrence
Out-of-order Observation != Out-of-order Source Fact automatically
Replay != new Event Occurrence automatically
Replay != Retroactive Admission
```

A Trigger may be re-evaluated under an explicitly identified evaluation lineage where authorized; earlier evaluations remain historical facts.

## 7.7 Authority / SoT / final Actual-state owner

| Dimension | RCP-14 result | Accepted owner |
|---|---|---|
| Event Source semantics/facts | `NOT OWNED by AU05` | original Event source owner |
| Event Occurrence final source fact | `NOT OWNED by AU05` | original Event source owner |
| Trigger Definition semantics | `OWNED within S6 automation semantics` | `ns_server / S6` |
| Trigger Evaluation Actual-state/result | `OWNED` | `ns_server / S6 / AU05 / SV-R02` |
| Policy semantics | `NOT OWNED` | `ns_server` Unified Policy Authority |
| Execution Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |
| Automation Runtime Operation | `NOT OWNED by RCP-14` | `ns_server / S6 / AU07 / SV-R02` |
| Transport/broker delivery truth | `NOT PRODUCT AUTHORITY CREATED` | applicable technical/source evidence only |

Permanent:

```text
Event Occurred != Trigger Matched
Trigger Matched != Execution Admitted
Event Producer != Automation Authority
Event Producer != Policy Authority
Replay != Retroactive Admission
same Event Occurrence re-observed != new Event Occurrence
```

## 7.8 Dependency classification

RCP-14 has no Batch-3 peer hard CSDD. Event source semantics are cross-authority inputs and evidence dependencies, not a reason to transfer Event authority into S6.

```text
Event source → Trigger Evaluation use
→ CACD / CEL / CXAR as applicable

Prior observation / replay lineage
→ CHPL
```

## 7.9 Guarantees / non-guarantees / revalidation

Guarantees:
- occurrence identity and evaluation identity remain distinct;
- duplicate/re-observation/replay history is non-destructive;
- Trigger match does not bypass Admission.

Non-guarantees:
- no broker/topic/webhook provider, transport delivery, exactly-once, at-least-once or ordering guarantee;
- no automatic replay or retroactive execution;
- no universal event schema or event store.

Revalidate if Event source ownership changes, S6 Trigger Evaluation ownership changes, occurrence and observation are proposed to collapse, replay is proposed to create retroactive authorization, or a transport/provider is proposed as semantic authority.

---

# 8. Stage 0 — RCP-15 Automation Composition Stable Contract

## 8.1 Contract semantic subject and identity

`RCP-15` stabilizes **reusable non-recursive Automation-to-Automation composition binding and invocation semantics** under S6 while preserving independent caller and callee lifecycles.

Stable identities/references include:

```text
Caller Automation Definition Identity / Revision
Callee Automation Definition Identity / Revision
Composition Reference Identity
Composition Binding Identity / Revision
Composition Applicability Qualification
Composition Invocation Identity
Parent Caller Automation Operation Reference
Callee Automation Operation Reference
Exact Resolved Binding Provenance
Historical Bound Caller / Binding / Callee Revisions
Admission references for caller/callee where applicable
Caller / Callee result-correlation references
Compatibility / Migration qualification
```

## 8.2 Producer topology

Principal semantic producer:

```text
ns_server / S6 / SV-R02
```

Responsibility partition within accepted S6 evidence:

```text
AU06
→ composition definition/binding/applicability/exact resolved binding provenance

AU07
→ runtime Composition Invocation correlation and caller/callee Automation Operation semantics
```

S8 remains Formal Artifact Acceptance / Execution Admission authority.

## 8.3 Consumer topology

Qualified consumers include:

1. AU07 caller continuation/runtime semantics resolving an applicable composition binding;
2. callee Automation runtime semantics receiving a source-qualified composition invocation under its own operation/admission lifecycle;
3. S8 Admission consumers where caller/callee execution requires separate Admission evidence;
4. Agent/Runtime/Node consumers only through applicable source references, without gaining composition authority;
5. authorized Web/diagnostic/history consumers projecting binding/invocation provenance.

## 8.4 Producer obligations

S6/AU06+AU07 MUST:

- preserve distinct caller and callee Definition identities/revisions;
- preserve a distinct Composition Reference, binding identity/revision and invocation identity;
- resolve composition using an exact compatible binding applicable to the caller's historical semantic context;
- pin exact historical caller/binding/callee revisions for the invocation;
- preserve callee lifecycle and Automation Operation identity independently from the caller;
- require applicable callee Admission rather than inheriting parent Admission automatically;
- preserve caller interpretation of callee result separately from callee semantic result;
- expose unavailable/incompatible/partial/unknown binding/callee conditions explicitly;
- reject native recursive invocation according to `CID-SV-B2-MDE-001` and preserve canonical composition dependency acyclicity;
- preserve history across binding migration/revision changes without rebinding old invocations to latest revisions;
- protect definition/composition dependency details from unauthorized disclosure.

## 8.5 Consumer obligations

Consumers MUST:

- use exact resolved historical binding provenance rather than assume latest callee revision;
- preserve distinct caller and callee Operation identities and Admission semantics;
- never equate Composition Invocation with Dispatch or Node Attempt;
- never treat callee success/failure as caller semantic success/failure without caller-owned interpretation;
- reject/qualify recursive or incompatible evidence without silently executing/rebinding it;
- preserve historical composition lineage during migration/recovery/re-observation.

## 8.6 Lifecycle / temporal / currentness

A Composition Binding has its own semantic revision/applicability history. A Composition Invocation binds one caller runtime context to one exact resolved historical binding/callee revision. The callee then has an independent Automation Operation lifecycle.

Current Definition revision is not retroactively applied to an existing invocation. Migration can establish a new future-compatible binding/revision but cannot rewrite historical binding provenance.

## 8.7 Authority / SoT / final Actual-state owner

| Dimension | RCP-15 result | Accepted owner |
|---|---|---|
| Automation canonical Definition semantics/SoT | `OWNED within S6` | `ns_server / S6 / SV-R02` |
| Composition binding/applicability | `OWNED` | `ns_server / S6 / AU06 / SV-R02` |
| Composition Invocation / caller-callee runtime correlation | `OWNED` | `ns_server / S6 / AU07 / SV-R02` |
| Caller Automation Operation Actual-state | `NOT COLLAPSED` | `ns_server / S6 / AU07 / SV-R02` |
| Callee Automation Operation Actual-state | `NOT COLLAPSED` | `ns_server / S6 / AU07 / SV-R02`, independent operation subject |
| Formal caller/callee Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |
| Dispatch | `NOT OWNED` | `ns_runtime / R2 / RT-R02` |
| Node Attempt / Effect | `NOT OWNED` | `N2 / ND-R02` and `N3 / ND-R03` |

Permanent:

```text
Caller Operation != Callee Operation
Composition Invocation != Dispatch != Attempt
Parent Admission != Callee Admission automatically
Callee Semantic Success != Caller Semantic Success automatically
Latest Callee Revision != Historical Bound Callee Revision
```

Owner Decision preservation:

```text
Native recursive Automation-to-Automation invocation
→ NOT SUPPORTED

Reusable Automation-to-Automation Composition
→ REQUIRED / PRESERVED

Canonical Composition Dependency
→ ACYCLIC
```

## 8.8 Dependency classification

RCP-15 has no Batch-3 peer hard CSDD prerequisite. It is the semantic-definition prerequisite of RCP-13 for composition-aware continuation:

```text
RCP-13 → RCP-15
→ CSDD
```

Runtime invocation/result correlation back to caller is CEL/CHPL and does not create a reverse CSDD.

## 8.9 Guarantees / non-guarantees / revalidation

Guarantees:
- exact historical binding/revision provenance;
- independent caller/callee Operations and Admission boundaries;
- recursion decision and canonical dependency acyclicity preserved.

Non-guarantees:
- no universal workflow/graph engine, scheduler, state machine, rollback/compensation or exactly-once semantics;
- no automatic callee Admission inheritance;
- no latest-revision rebinding.

Revalidate if recursion Owner Decision changes, canonical composition acyclicity changes, S6/S8 ownership changes, historical revision pinning is removed, or a universal workflow authority/engine is proposed.

---

# 9. Stage 1 — RCP-13 Automation Continuation Stable Contract

RCP-13 is synthesized after RCP-15 because its semantic definition must interpret composition binding/invocation when Automation continuation crosses a reusable Automation composition boundary.

## 9.1 Contract semantic subject and identity

`RCP-13` stabilizes **Automation Runtime Operation and semantic continuation** under the exact Automation Definition revision and applicable historical composition context.

Stable identities/references include where applicable:

```text
Automation Definition Identity / Revision
Target Execution Intent Reference
Admission Reference
Automation Runtime Operation Identity
Continuation Identity
Origin / Parent Operation Reference
Composition Invocation Reference
Trigger Evaluation Reference
Human Wait Requirement / Response Correlation
Dispatch Reference
Attempt Reference
Effect Reference
Trial Context Reference
Semantic continuation qualification / wait reason
Semantic outcome identity/reference
Revision-pinning provenance
History / lineage / compatibility / conformance references
```

`Semantic continuation qualification` describes source-owned semantic facts and does not prescribe a universal workflow state machine.

## 9.2 Producer topology

Principal semantic producer / final Actual-state owner:

```text
ns_server / S6 / AU07 / SV-R02
```

Supporting source evidence remains separately owned by AU05 Trigger Evaluation, AU06 composition binding, AU08 HITL semantics, S8 Admission, RT-R02 Dispatch, N2 Attempt, N3 Effect and applicable source/business facts.

## 9.3 Consumer topology

Qualified consumers include:

1. S6 itself across continuation steps and caller/callee boundaries while preserving exact revisions;
2. RT-R03 for continuation/intervention coordination-stage evidence only;
3. S8 Admission where execution/re-entry requires applicable formal Admission;
4. RT-R02 and Node execution consumers receiving applicable admitted work without owning Automation semantic outcome;
5. W3 Human Task interaction surfaces and W5 operational projections, without source-authority transfer;
6. Agent A6 consumers when an Agent invokes/participates in Automation, without giving Agent Automation authority;
7. diagnostics/history/recovery consumers preserving source-qualified continuation evidence.

## 9.4 Producer obligations

S6/AU07 MUST:

- bind each Automation Operation to an exact Automation Definition revision and applicable governance context;
- preserve Target Execution Intent and Admission reference separately from Operation identity;
- establish a distinct Continuation identity/correlation when continuation semantics require it;
- preserve Origin/Parent Operation and Composition Invocation lineage without collapsing caller/callee Operations;
- consume exact RCP-15 resolved historical binding where composition participates;
- preserve Trigger Evaluation and HITL requirement/response/application evidence as separately owned/source-qualified facts;
- correlate Dispatch/Attempt/Effect only when those source owners establish them;
- interpret Attempt/Effect/callee result evidence under Automation semantics rather than automatically converting infrastructure/executor success/failure into Automation success/failure;
- pin historical revisions and prohibit silent live revision rebinding;
- preserve retry/re-entry/HITL continuation lineage without mutating prior operation/evidence;
- expose wait, unavailable, unknown, stale, partial, conflicting, incompatible and indeterminate conditions explicitly;
- preserve authorized disclosure and redaction for Automation Definition/composition/HITL/target details.

## 9.5 Consumer obligations

Consumers MUST:

- preserve S6 as Automation semantic owner and AU07 as runtime continuation Actual-state owner;
- distinguish Admission/Dispatch/Attempt/Effect from Automation semantic outcome;
- preserve exact Definition and composition binding provenance;
- never interpret RT-R03 coordination completion as Automation semantic completion;
- never interpret Web human-response submission as response applicability/application/resume until S6 source evidence establishes it;
- preserve source-qualified failure/uncertainty and non-destructive history;
- prevent unauthorized disclosure of Automation definitions, composition dependencies, HITL context and runtime correlations.

## 9.6 Lifecycle / temporal / currentness

An Automation Operation may semantically continue through source-owned wait/re-entry/callee-result/HITL conditions. The Contract stabilizes identity, source facts, revisions and result interpretation, not a mandatory linear state machine.

Permanent:

```text
Current Definition Revision != Operation Definition Revision automatically
Attempt Failure != Automation Final Semantic Failure automatically
Effect Occurred != Automation Semantic Success automatically
Callee Success != Caller Success automatically
Human Response Submitted != Human Response Applicable / Applied automatically
```

Retry/re-entry that establishes a new source-owned occurrence preserves lineage and does not rewrite prior Attempt, continuation or outcome evidence.

## 9.7 Authority / SoT / final Actual-state owner

| Dimension | RCP-13 result | Accepted owner |
|---|---|---|
| Automation Definition semantic authority / canonical SoT | `OWNED within S6` | `ns_server / S6 / SV-R02` |
| Automation Runtime Operation / semantic continuation Actual-state | `OWNED` | `ns_server / S6 / AU07 / SV-R02` |
| Trigger Evaluation | `NOT OWNED` | `ns_server / S6 / AU05 / SV-R02` |
| Composition binding/applicability | `NOT OWNED by AU07` | `ns_server / S6 / AU06 / SV-R02` |
| HITL requirement/applicability/application semantics | `NOT COLLAPSED` | accepted S6/AU08 semantics |
| Human Response Submission occurrence | `NOT OWNED` | applicable authorized interaction/source producer, e.g. W3 when Web-origin |
| Admission | `NOT OWNED` | `ns_server / S8 / SV-R04` |
| Dispatch | `NOT OWNED` | `ns_runtime / R2 / RT-R02` |
| Node Attempt | `NOT OWNED` | `ns_node / N2 / ND-R02` |
| Node Effect | `NOT OWNED` | `ns_node / N3 / ND-R03` |
| RT-R03 coordination-stage facts | `NOT OWNED` | `ns_runtime / R3 / RT-R03` |

Permanent:

```text
Automation Operation != Admission != Dispatch != Attempt != Effect
Attempt Failure != Automation Final Semantic Failure automatically
Effect Occurred != Automation Semantic Success automatically
Callee Success != Caller Success automatically
Current Definition Revision != Operation Definition Revision automatically
R3 Coordination Completed != Automation Semantic Outcome Achieved
```

## 9.8 Dependency classification

```text
RCP-13 → RCP-15
→ CSDD / hard intra-Batch dependency

RCP-13 ↔ RCP-06
→ CACD / CEL / CXAR
→ NOT CSDD

RCP-13 ↔ RCP-12
→ CACD / CEL / CHPL / CXAR where Agent participation applies
→ NOT CSDD
```

## 9.9 Guarantees / non-guarantees / revalidation

Guarantees:
- exact Definition and composition binding revision provenance;
- source-owned Automation semantic continuation and outcome interpretation;
- Admission/Dispatch/Attempt/Effect remain non-collapsed;
- no silent live revision rebinding.

Non-guarantees:
- no exactly-once, universal retry/backoff/cancel/rollback/compensation semantics;
- no universal workflow state-machine implementation;
- no guarantee that callee/Attempt/Effect success equals caller Automation success.

Revalidate if S6/AU07 ownership changes, RCP-15 composition semantics change materially, revision pinning is removed, Admission is proposed to be inherited/bypassed, or a universal workflow/failure policy is introduced.

---

# 10. Cross-RCP Non-collapse Closure

The Candidate explicitly preserves:

```text
RCP-06 != RCP-13
Coordination != Source Continuation Authority

RCP-11 != RCP-09
Composition Coordination != Participant Agent Runtime Actual-state

RCP-12 != RCP-06
RCP-12 != RCP-09
RCP-12 != RCP-10
RCP-12 != RCP-13
RCP-12 != RCP-15

RCP-13 != RCP-15
Automation Semantic Continuation != Composition Binding Authority

RCP-14 Event Evaluation != Admission != Automation Runtime Operation

Admission != Dispatch != Attempt != Effect
```

No consumer gains producer Authority, Source of Truth, final Actual-state ownership or disclosure authority merely through projection, aggregation, routing, correlation, diagnostics or history.

---

# 11. Producer / Consumer Closure

| RCP | Principal producer/source owner | Producer topology | Consumer topology | Producer obligations | Consumer obligations |
|---|---|---|---|---|---|
| RCP-06 | RT-R03 | `COMPLETE` | `COMPLETE` | `COMPLETE` | `COMPLETE` |
| RCP-11 | A5/AG-R03; participant facts A2/AG-R01 | `COMPLETE` | `COMPLETE` | `COMPLETE` | `COMPLETE` |
| RCP-12 | A6/AG-R04 | `COMPLETE` | `COMPLETE` | `COMPLETE` | `COMPLETE` |
| RCP-13 | S6/AU07/SV-R02 | `COMPLETE` | `COMPLETE` | `COMPLETE` | `COMPLETE` |
| RCP-14 | original Event source + S6/AU05 | `COMPLETE` | `COMPLETE` | `COMPLETE` | `COMPLETE` |
| RCP-15 | S6/AU06+AU07/SV-R02 | `COMPLETE` | `COMPLETE` | `COMPLETE` | `COMPLETE` |

Consumer closure is architecture-semantic rather than an exhaustive list of future implementation call sites. Any later authorized consumer MUST conform to the same source-owner, disclosure, currentness, history and non-collapse obligations and does not become a new producer owner by consumption.

---

# 12. Final Contract Dependency Graph

## 12.1 Hard CSDD graph

```text
Prior accepted prerequisite edges:
RCP-11 → RCP-09
RCP-12 → RCP-09

Batch-3 peer edge:
RCP-13 → RCP-15
```

No other Batch-3 peer CSDD is created.

```text
Hard Contract CSDD Graph
→ ACYCLIC

Hard CSDD Cycle
→ NONE
```

## 12.2 Explicit non-hard classifications

```text
RCP-06 ↔ RCP-13
→ CACD / CEL / CXAR where applicable
→ NOT CSDD

RCP-12 ↔ RCP-06
→ CACD / CEL / CHPL / CXAR
→ NOT CSDD

RCP-12 ↔ RCP-10
→ CACD / CEL / CXAR
→ NOT CSDD

RCP-12 ↔ RCP-13 / RCP-15
→ CACD / CEL / CHPL / CXAR where Automation participates
→ NOT CSDD
```

Request/response direction, runtime invocation, result return, target evidence, history, re-observation and recovery do not alter this classification.

---

# 13. Authority / SoT / Final Actual-state Cycle Review

Across the six Contracts:

```text
Authority Transfer
→ 0

Source-of-Truth Transfer
→ 0

Final Actual-state Ownership Transfer
→ 0

Authority Cycle
→ NONE

Source-of-Truth Cycle
→ NONE

Final Actual-state Ownership Cycle
→ NONE

Multiple-final-owner Ambiguity
→ 0
```

Composition, delegation, continuation and evaluation may correlate evidence from multiple owners, but correlation cannot establish a circular ownership relationship.

---

# 14. Security / Privacy / Disclosure Closure

Protected surfaces include at minimum:

```text
Multi-Agent participant existence and relationship
Composition membership and context contribution
Agent delegation target existence / target details
Node / Automation target metadata
Agent Candidate-authoring provenance
Automation Definition and composition dependencies
Event source existence / event content
Trigger Definition / evaluation details
HITL / continuation context
Runtime correlations / diagnostics / history
```

Required invariant:

```text
Reference Possession != Permission
Diagnostic Visibility != Disclosure Authority
Visible To One Participant != Visible To All Participants
Composition Membership != Disclosure Authorization
Delegation Target Selected != Permission To Disclose All Agent Context
Secret Reference != Secret Material
```

Redaction is semantic-preserving: a consumer may receive a bounded redacted result/qualification while the protected underlying subject remains undisclosed. Redaction MUST NOT fabricate semantic success/failure or transfer source ownership.

No secret material is required in ordinary RCP evidence. Secret References remain governed references and resolution permission remains separately controlled.

---

# 15. Offline / Private / Recovery / Re-observation Closure

Core Contract correctness requires no mandatory public Internet, public SaaS, hosted workflow control plane, public Agent supervisor, public event broker or cloud-only authority.

Offline/private evidence remains subject to the same source ownership, governance, privacy, currentness and provenance rules.

Permanent:

```text
Offline != Authority Transfer
Reconnect != Reconciled
Recovery != SoT Transfer
Re-observation != Canonicalization
Replay != Retroactive Authorization
Local Copy != Source SoT automatically
Central Copy != Source SoT automatically
Latest Timestamp != Canonical Winner
Latest Arrival != Canonical Winner
Later Success != Earlier Failure Deletion
```

No recovery engine, reconciliation winner, replay guarantee, merge algorithm or automatic synchronization direction is defined.

---

# 16. Compatibility / Migration / Conformance Closure

For all six RCPs:

- Contract evolution must preserve semantic subject identity and non-collapse invariants;
- source/binding/definition revisions needed for historical interpretation are retained;
- unknown or incompatible revisions are explicitly qualified rather than silently coerced;
- migration may establish new future-compatible revisions/bindings but does not rewrite historical facts;
- provider, protocol, serialization, persistence or deployment changes do not themselves redefine the Contract;
- a conforming realization must preserve source ownership, currentness/uncertainty, disclosure/redaction, history/provenance and all explicit non-guarantees.

Revalidation is mandatory on any proposed Authority/SoT/final-owner transfer, Owner Decision change, new hard CSDD, new Product capability/component/runtime role/RCP, new universal winner/failure/once/retry law, new mandatory Shared Foundation semantic, or accepted upstream semantic contradiction.

---

# 17. MDE / Shared Foundation / Representation Audit at Candidate Stage

```text
New Product Component
→ 0

New Runtime Role
→ 0

New RCP
→ 0

New Owner-reserved MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Accepted Owner Decision Modified
→ 0

Accepted Upstream Stable Contract Redesigned
→ 0

Concrete API / DTO / Schema Design
→ 0

Concrete Broker / Workflow / Agent Framework Selection
→ 0

Concrete Provider SDK Selection
→ 0

Database / ORM / Event-store Design
→ 0

Physical Identifier Scheme
→ 0

Process / Worker / Thread / Coroutine Topology
→ 0

Implementation Planning / Coding Leakage
→ 0
```

No universal fail-open/fail-closed, exactly-once, retry/cancel/rollback/reversal, conflict-winner, cross-Tenant law, supervisor/team topology or scheduler/workflow authority is introduced.

---

# 18. Candidate Result

```text
RCP-06 Full Cross-boundary Stable Contract Candidate
→ COMPLETE

RCP-11 Full Cross-boundary Stable Contract Candidate
→ COMPLETE

RCP-12 Full Cross-boundary Stable Contract Candidate
→ COMPLETE

RCP-13 Full Cross-boundary Stable Contract Candidate
→ COMPLETE

RCP-14 Full Cross-boundary Stable Contract Candidate
→ COMPLETE

RCP-15 Full Cross-boundary Stable Contract Candidate
→ COMPLETE

Producer / Consumer Closure
→ COMPLETE

Hard Contract CSDD Graph
→ ACYCLIC

Authority / SoT / Final Actual-state Ownership Transfer
→ 0 / 0 / 0

Owner Decision CID-SV-B2-MDE-001
→ PRESERVED

Candidate Scope
→ WITHIN AUTHORIZATION
```

This Candidate does not claim Global Acceptance or Runtime / Domain Stable Contract Design Exhaustion.

```text
Global Acceptance
→ NOT CLAIMED

Batch 4 Authorization
→ NONE

Batch 5 Authorization
→ NONE

Runtime / Domain Stable Contract Design Exhaustion
→ NOT CLAIMED

RCP-01..24 Full Cross-component Closure
→ NOT CLAIMED

System-level SDK Detailed Design
→ NOT AUTHORIZED

Implementation Planning / IWP / Coding
→ NOT AUTHORIZED
```
