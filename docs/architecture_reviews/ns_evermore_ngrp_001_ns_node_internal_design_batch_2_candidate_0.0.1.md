# NGRP-001 — Component Internal Design / ns_node / Batch 2 Candidate

## Authority Metadata

- **Program / Phase:** `NGRP-001 — Component Internal Design / ns_node / Batch 2`
- **Authorization Scope:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_NODE / BATCH_2 / OFFLINE_CONTINUITY_RECOVERY_AND_LOCAL_DIAGNOSTICS_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Producing Entry HEAD:** `90ab35107627ab021e7eb67ca95593668454d037`
- **Recovered GAC Epoch:** `GAC-EPOCH-0084`
- **State Verified Through HEAD:** `eb1b902abd698636b44f00fd9a2aeaa62a7c5e88`
- **Decision Registry:** `0.0.30 / CURRENT / NORMATIVE`
- **Authorization Transition:** `GAC-TR-0094`
- **Authorized Boundary:** `N4 / Offline Continuity, Recovery & Local Diagnostics`
- **Inherited Runtime Role:** `ND-R04 / Node Offline Continuity & Recovery Participant`
- **Accepted ns_node Upstream:** `N1 / N2 / N3 / ND-R01 / ND-R02 / ND-R03 / NORMATIVE / MUST NOT BE REOPENED`
- **Candidate Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Global Acceptance Authority:** `NOT HELD`

This Candidate performs only architecture-semantic internal design for `N4 / ND-R04`. It does not redesign accepted N1/N2/N3 internals, does not claim `ns_node` Batch-2 Global Acceptance, `ns_node` Internal Design Exhaustion, Component Internal Design Global Closure, `RCP-20` Full Cross-component Closure, `RCP-22` Full Cross-component Closure, another Product Component authorization, System-level SDK Detailed Design, Design-to-Implementation Readiness, Implementation Planning, IWP or coding.

---

# 1. Fresh Repository Recovery

Fresh remote recovery was completed before design.

```text
Actual remote Branch HEAD at producing entry
→ 90ab35107627ab021e7eb67ca95593668454d037

Current GAC Epoch
→ GAC-EPOCH-0084

State Verified Through HEAD
→ eb1b902abd698636b44f00fd9a2aeaa62a7c5e88

State-to-HEAD Delta
→ exactly 1 commit
→ Global Architecture State authorization seal only
→ parent = eb1b902abd698636b44f00fd9a2aeaa62a7c5e88

Delta Classification
→ EXPECTED_GOVERNANCE

Decision Registry
→ 0.0.30 / CURRENT / NORMATIVE

Current Authorized Phase
→ exact ns_node Batch 2 / N4 match

Authorization Scope
→ exact match

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Semantic Gap
→ NONE

Blocking Item
→ NONE

Known Drift
→ NONE

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE

Recovery Result
→ PASS
```

Ledger continuity through `GAC-TR-0092`, `GAC-TR-0093` and `GAC-TR-0094` was consumed. Batch 1 is Global Accepted for N1/N2/N3, the post-Batch-1 assessment established remaining N4 pressure and N4 entry readiness, and `GAC-TR-0094` separately authorized exactly this Batch 2 scope.

The complete Mandatory Read Set named by the authorization was consumed. The accepted `ns_runtime / R4 / RT-R04` Batch-3 Component Internal Design was additionally consumed because it defines the upstream recovery-scope, evidence-exchange, source-owner re-observation and reconciliation-stage coordination semantics that N4 must consume without taking over.

Recovery Gate result: `PASS`.

---

# 2. Preserved Normative Upstream

## 2.1 Accepted ns_node source partitions

```text
N1 / ND-R01
→ Node-local capability / readiness / Applied Configuration Actual-state
→ N1-R01..N1-R07
→ RCP-04 owner/source-side semantics accepted
→ RCP-19 Node Applied contribution accepted

N2 / ND-R02
→ Node-local execution Attempt Actual-state
→ N2-R01..N2-R09
→ RCP-07 owner/source-side semantics accepted

N3 / ND-R03
→ protected local Effect / genuinely Node-origin source facts
→ N3-R01..N3-R07
→ RCP-08 owner/source-side semantics accepted
```

N4 consumes references/evidence from these partitions. It does not redefine their readiness, Attempt, Effect/source-fact identities, lifecycle, currentness semantics, source ownership or history rules.

## 2.2 Accepted runtime coordination upstream

```text
R1 / RT-R01
→ participant presence / reachability coordination

R3 / RT-R03
→ continuation / delegation / intervention coordination-stage facts

R4 / RT-R04
→ recovery scope / recovery coordination-stage facts
→ evidence-exchange coordination
→ source-owner re-observation coordination / result correlation
→ reconciliation-stage participation
→ R4 health / lifecycle / diagnostic evidence
```

Accepted RT-R04 internal responsibilities `RC01..RC09` are normative upstream. In particular:

```text
R4 Recovery Scope Identity / Reference
→ RT-R04-owned coordination subject

R4 Recovery / Reconciliation-stage Evidence Identity / Reference
→ RT-R04-owned evidence subject

Source-domain recovery outcome
→ original source owner

Conflict winner / merged canonical state
→ NOT owned by RT-R04
```

## 2.3 Permanent non-collapse inherited and preserved

```text
Recovery Participation != Source Recovery Authority
Local Evidence Retention != Canonical Global SoT
Evidence Exchange != Source Fact Transfer
Re-observation Coordination != Re-observed Source Fact
N4 Re-observation Request != N1/N2/N3 Source Fact
Source Re-observed != Source Rewritten
Reconnect != Reconciled
Recovery != SoT Transfer
Replay != Retroactive Authorization
Latest Timestamp != Canonical Winner
Latest Arrival != Canonical Winner
Local Copy != Canonical Source automatically
Central Copy != Canonical Source automatically
Conflict Detected != Conflict Resolved
Reconciliation Stage Completed != Source Facts Unified automatically
Recovery Participation Completed != Source Recovery Outcome automatically
Diagnostic Observation != Source Semantic Fact
Diagnostic Aggregation != Canonicalization
```

---

# 3. Authorized Boundary and Stable-contract Scope

## 3.1 Authorized internal boundary

```text
N4 — Offline Continuity, Recovery & Local Diagnostics
→ ND-R04 Node Offline Continuity & Recovery Participant
```

Explicitly not redesigned:

```text
N1 / ND-R01
N2 / ND-R02
N3 / ND-R03
R1..R4 / RT-R01..RT-R04
```

## 3.2 Stable-contract scope

```text
RCP-20 Recovery / Reconciliation
→ ND-R04 Node-local recovery/reconciliation participant-side semantic contribution
→ representation-neutral stable contract synthesis
→ Full Cross-component Closure NOT CLAIMED

RCP-22 Diagnostics / Provenance
→ ND-R04 Node-local recovery / health / lifecycle / offline diagnostic producer contribution
→ complete ns_node-side contribution at current design level by preserving N1/N2/N3 producer ownership and adding N4-owned producer semantics
→ Full Cross-component Closure NOT CLAIMED
```

Bounded correlation only where materially required:

```text
RCP-03
→ reconnect / Participant / Presence references only
→ RT-R01 authority preserved

RCP-06
→ recovery / resume / intervention coordination references only
→ RT-R03 coordination facts and final source owners preserved

RCP-24
→ recovery / resume Human-SDK intent receiving-side correlation only
→ source interaction side remains downstream
```

Accepted `RCP-04 / RCP-07 / RCP-08 / RCP-19` semantics are consumed only and are never reopened.

---

# 4. N4 Internal Architecture Responsibility Inventory

The labels below are architecture-semantic responsibilities only. They are not modules, packages, classes, services, processes, workers, threads, coroutines, queues, stores, schemas, APIs, DTOs or deployment units.

```text
N4-R01 Recovery Participation Scope & Governed-context Binding
N4-R02 Retained Evidence Availability, Source Attribution & Custody Qualification
N4-R03 Offline / Degraded Continuity Qualification
N4-R04 RT-R04 Evidence-exchange Participation & Correlation
N4-R05 Source-owner Re-observation Request / Result Correlation Participation
N4-R06 Reconciliation-stage Participation & Conflict / Partiality Preservation
N4-R07 Node-local Recovery / Health / Lifecycle Diagnostic Evidence Custody
N4-R08 Currentness, Availability, Uncertainty & Conflict Qualification
N4-R09 Non-destructive Recovery / Diagnostic History, Lineage & Provenance
N4-R10 RCP-20 / RCP-22 Stable-contract Governance, Compatibility & Conformance
```

```text
Authorized Boundary Coverage
→ N4 / 1 OF 1 / 100%

Internal Responsibility Count
→ 10

Unowned Material N4 Responsibility
→ 0

Duplicate Final Responsibility
→ 0
```

Two N4-scoped semantic identity subjects are materially required:

```text
N4 Recovery Participation Scope Identity / Reference
N4 Recovery / Diagnostic Evidence Identity / Reference
```

They are representation-neutral, Node/N4-bounded and non-authoritative for N1/N2/N3/R4 source facts. They do not define UUIDs, database keys, message IDs, wire IDs or a universal recovery namespace.

Permanent identity separation:

```text
N4 Recovery Participation Scope Reference
!= R4 Recovery Scope Reference
!= Operation / Work Reference
!= N1 Readiness Evidence Reference
!= N2 Attempt Identity / Reference
!= N3 Effect / Source Evidence Identity / Reference

N4 Recovery / Diagnostic Evidence Reference
!= R4 Recovery / Reconciliation-stage Evidence Reference
!= N1/N2/N3 Source Evidence Identity
```

---

# 5. N4-R01 — Recovery Participation Scope & Governed-context Binding

**Purpose.** Establish one bounded Node-local recovery-participation subject and bind it to the Node, applicable R4 recovery scope, source-owner references and governed context without becoming source recovery authority.

N4-R01 preserves, where applicable:

```text
N4 Recovery Participation Scope Identity / Reference
Node / Participant Reference
R4 Recovery Scope Identity / Reference
Recovery Subject Reference
Source Owner Reference
Source Domain / Runtime-partition Reference
Source Revision / Context Reference
N1 Readiness Evidence Reference
N2 Attempt Identity / Reference
N3 Effect / Source Evidence Identity / Reference
Operation / Work Reference
Admission Evidence Reference where applicable
R1 Presence / reconnect reference where applicable
R3 coordination request / evidence reference where applicable
Tenant Context
Organization Context where applicable
Principal Context
Policy / Trust Context References
Privacy / Sensitivity / Redaction Context
Temporal Context
Compatibility / Conformance Context
Correlation / Provenance Context
```

**Owned facts:** only the N4-local fact that these references are associated with a bounded Node recovery-participation scope under the evidence available to N4.

**Explicitly non-owned:** R4 Recovery Scope authority; N1 Readiness; N2 Attempt; N3 Effect/source facts; source revision authority; Admission; R1/R3 facts; source-domain recovery outcome; conflict winner; canonical merged state.

**Failure / offline:** missing or unverifiable context remains `UNKNOWN`, `UNAVAILABLE` or `INDETERMINATE` as applicable. Offline possession of references does not extend their authority or applicability.

**History:** each participation scope remains historically distinguishable even when correlated to the same R4 recovery scope or source subject.

Permanent:

```text
N4 Participation Scope != R4 Recovery Scope
N4 Participation Scope != Source Fact
Reference != Authority
Correlation != Ownership
```

---

# 6. N4-R02 — Retained Evidence Availability, Source Attribution & Custody Qualification

**Purpose.** Own N4-local facts about whether source-attributable evidence needed for offline continuity/recovery remains locally retainable/available and correctly attributable, without taking ownership of the evidence's source semantics.

N4 may retain or reference already-established evidence from accepted owners, including where applicable:

```text
N1 Readiness / Applied Configuration evidence
N2 Attempt evidence
N3 Effect / local source evidence
R1 reconnect / presence evidence reference
R3 recovery/resume/intervention coordination reference
R4 recovery / evidence-exchange / re-observation / reconciliation-stage references
Admission / Dispatch / source-domain references already attached to accepted source evidence
```

For each retained evidence subject, N4 preserves at minimum where applicable:

```text
Source Owner Reference
Source Boundary / Runtime-role Reference
Source Evidence Identity / Reference
Source Revision / Context Reference
Source-provided temporal context
Source-provided currentness / uncertainty context
Node-local retention availability qualification
N4 observation / receipt temporal context
Governed Tenant / Principal / Policy / Trust context references
privacy / sensitivity / redaction context
compatibility / conformance context
historical provenance / lineage
```

**Owned facts:** N4-local retention availability, retention observation, source-attribution binding and N4-local custody qualification only.

**Explicitly non-owned:** substantive N1/N2/N3 source fact, source currentness as defined by the source owner, source revision authority, canonical status, source recovery outcome.

Permanent:

```text
Retained Evidence != N4 Source Fact automatically
Local Retention != Canonical Global SoT
Local Copy != Source Authority
Evidence Available != Evidence Current automatically
Evidence Unavailable != Source Fact Deleted
```

No persistence engine, database, event store, compaction mechanism or storage topology is selected. `Evidence retention` is an architecture-semantic responsibility only.

---

# 7. N4-R03 — Offline / Degraded Continuity Qualification

**Purpose.** Qualify the Node-local continuity condition under disconnection/degradation using retained evidence and locally observable N4 conditions while preserving all upstream governance/authority boundaries.

N4 may own Node-local continuity qualifications such as, where supported by evidence:

```text
OFFLINE / disconnected context reference
DEGRADED continuity indication
RECOVERY_PENDING
RECOVERING as N4 participation qualification
RECONCILIATION_PENDING
retained-evidence availability / partiality qualification
remote evidence UNAVAILABLE / UNREACHABLE qualification from admissible references
continuity UNKNOWN / INDETERMINATE qualification
```

These qualifications describe N4's Node-local continuity/recovery participation context. They do not define a universal linear recovery state machine and do not decide whether new work may be admitted or executed.

Permanent:

```text
Offline != Authority Transfer
Retained Admission Evidence != New Admission Authority
Central Unavailable != Local Source Invalid
Offline Evidence Possession != Permission to execute automatically
RECOVERING != Source Recovery Success
RECOVERY_PENDING != Source Failure
RECONCILIATION_PENDING != Conflict Resolved
```

No Product-wide fail-open/fail-closed law is selected. If such a law becomes materially required, the design must stop for Owner MDE.

Private/offline correctness requires no mandatory public Internet, public SaaS, hosted recovery control plane or cloud coordination dependency.

---

# 8. N4-R04 — RT-R04 Evidence-exchange Participation & Correlation

**Purpose.** Participate on the Node side of accepted RT-R04 recovery evidence exchange and record Node-local request/handoff/receipt/correlation facts without transferring source authority.

N4 may own facts such as:

```text
R4 Recovery Scope Reference received / correlated
N4 Evidence-exchange Participation Started / Pending / Completed for its bounded role
Evidence-exchange Request Reference received / correlated
Node Evidence Handoff Reference produced / correlated
R4 Receipt / Handoff Evidence Reference received where supplied
Evidence Exchange unavailable / unreachable / partial / indeterminate qualification from N4 perspective
correlation between N4 retained source evidence and R4 exchange-stage evidence
```

N4 preserves source owner, source evidence identity/reference, source revision/context, temporal context, provenance and uncertainty/currentness qualification. N4 never rewrites the underlying N1/N2/N3 evidence when exchanging it.

Permanent:

```text
Evidence Exchange != Source Fact Transfer
Evidence Handoff != Authority Transfer
Evidence Received != Canonical Acceptance
Evidence Exchange Completed != Conflict Resolved
Evidence Exchange Completed != Source Recovery Outcome
RT-R04 Coordination Fact != N4 Source Fact
N4 Participation Fact != RT-R04 Coordination Truth
```

No transport, broker, queue, delivery guarantee, retry algorithm, message envelope or protocol is selected.

---

# 9. N4-R05 — Source-owner Re-observation Request / Result Correlation Participation

**Purpose.** Request/forward/correlate source-owner re-observation for N1/N2/N3 and relate any owner-produced result to the N4 participation scope without recreating source facts.

N4 may own:

```text
N4 Re-observation Request Reference
requested Source Owner Reference
requested Source Evidence / Subject Reference
R4 Re-observation Coordination Reference where applicable
request handoff / receipt / correlation evidence
pending / unavailable / unreachable / indeterminate qualification
owner-produced Re-observation Result / Evidence Reference received where supplied
N4-local receipt/currentness/correlation qualification of that returned reference
```

Source ownership remains:

```text
N1 re-observation result → N1 owns
N2 re-observation result → N2 owns
N3 re-observation result → N3 owns
RT-R04 coordination truth → R4 owns
```

Permanent:

```text
N4 Re-observation Request != Source Fact
Re-observation Performed != Source Changed
Source Re-observed != Source Rewritten
Result Received != Canonical automatically
No Response != Source Fact Deleted
Re-observation Failure != Prior Source Evidence Invalid
```

Replay may appear only as a source-defined reference/correlation pressure. N4 does not define replay semantics, deterministic replay, replay algorithms or authority reconstruction.

---

# 10. N4-R06 — Reconciliation-stage Participation & Conflict / Partiality Preservation

**Purpose.** Represent N4's bounded Node-side participation in reconciliation and preserve unresolved disagreement/partiality without selecting a winner or merged state.

N4 may own facts such as:

```text
N4 Reconciliation Participation Started
N4 Reconciliation Participation Pending
N4 Reconciliation Participation Completed for its bounded Node-side role
R4 Reconciliation-stage Evidence Reference received / correlated
source evidence references participating in the reconciliation context
Conflict Detected from N4-local admissible evidence
Conflict Remains indication where supported
Partial evidence / partial participation qualification
```

A conflict is represented as a relationship among provenance-bearing evidence references, never as permission for N4 to choose one source.

Permanent:

```text
Reconciliation Participation != Source Recovery Authority
Conflict Detected != Conflict Resolved
CONFLICTING != latest wins
CONFLICTING != local wins
CONFLICTING != central wins
CONFLICTING != source-priority winner
CONFLICTING != majority wins
Reconciliation Participation Completed != Source Facts Unified automatically
Reconciliation Participation Completed != Canonical Merged State
N4 Participation Completed != Source Recovery Outcome
```

If a source owner later supplies source-domain recovery/resolution evidence, N4 records the reference/provenance without rewriting earlier conflict evidence.

No cross-source merge law, authoritative synchronization direction, CRDT/event-sourcing law, source-priority hierarchy or winner algorithm is selected.

---

# 11. N4-R07 — Node-local Recovery / Health / Lifecycle Diagnostic Evidence Custody

**Purpose.** Own recovery/continuity/health/lifecycle diagnostic observations genuinely originating in N4 and expose them as source-attributable diagnostic evidence without converting diagnostics into source semantics.

N4-owned diagnostic subjects may include, where applicable:

```text
Node-local recovery participation availability / health observation
retained-evidence availability / custody diagnostic
R4 evidence-exchange participation diagnostic
source-owner re-observation participation diagnostic
reconciliation-stage participation diagnostic
offline / degraded continuity diagnostic
N4 recovery-scope lifecycle diagnostic
N4 currentness / uncertainty / conflict / partiality diagnostic
N4 provenance / correlation diagnostic
```

Diagnostics may correlate accepted N1/N2/N3 provenance by reference but do not re-own those source facts.

Permanent:

```text
Diagnostic Observation != Source Semantic Fact
Diagnostic Success != Source Recovery Success automatically
Diagnostic Aggregation != Canonicalization
Health Evidence != Admission / Trust / Policy
Collected Evidence != Universal Node SoT
```

Diagnostics preserve Tenant/Principal/Policy/Trust/privacy/sensitivity/redaction context where applicable. Secret Material must not appear in ordinary diagnostic evidence; Secret Reference metadata is exposed only when authorized and necessary.

No Web diagnostics UI, SDK diagnostics model, Agent diagnostics model or universal diagnostics store is designed.

---

# 12. N4-R08 — Currentness, Availability, Uncertainty & Conflict Qualification

**Purpose.** Apply accepted temporal/freshness and technical-status semantics to N4-owned facts and N4's view of retained/recovery evidence while clearly distinguishing source-provided semantics from N4 observation semantics.

Applicable architecture-semantic qualifications include where evidenced:

```text
UNKNOWN
STALE
UNAVAILABLE
UNREACHABLE
INDETERMINATE
CONFLICTING
PARTIAL
RECOVERY_PENDING
RECONCILIATION_PENDING
RECOVERING
```

They may be orthogonal and do not form a universal enum or transition graph.

N4 distinguishes at minimum:

```text
Source Evidence temporal / revision context
Source-provided currentness / uncertainty context
N4 retention / receipt / observation temporal context
N4-local currentness / availability qualification
R4 coordination evidence temporal / currentness context
```

Permanent:

```text
UNKNOWN != absent / false / failed
STALE != false
UNAVAILABLE != denied / failed
UNREACHABLE != source invalid
PARTIAL != complete
CONFLICTING != winner selected
RECOVERY_PENDING != source failed
RECONCILIATION_PENDING != resolved
Fresh N4 Observation != Fresh Source automatically
Latest Timestamp != Canonical Winner
Latest Arrival != Canonical Winner
```

No universal TTL, timeout, expiry, clock source, freshness threshold or source ordering law is selected.

---

# 13. N4-R09 — Non-destructive Recovery / Diagnostic History, Lineage & Provenance

**Purpose.** Preserve N4 recovery-participation and diagnostic evidence as non-destructive history while linking it to original source evidence and accepted RT-R04 coordination evidence.

N4-R09 introduces one scoped `N4 Recovery / Diagnostic Evidence Identity / Reference` for material N4-originated evidence occurrences because a single participation scope can produce multiple exchange, re-observation, reconciliation and diagnostic observations.

Mandatory history rules:

```text
one N4 Recovery Participation Scope → multiple evidence-exchange occurrences
one N4 Recovery Participation Scope → multiple re-observation requests/results
one N4 Recovery Participation Scope → multiple reconciliation participation observations
one source assertion → multiple historical observations
one conflict → multiple conflicting evidence references
later re-observation → does not rewrite earlier source evidence
later recovery success evidence → does not erase earlier failure/conflict/uncertainty
later diagnostic success → does not erase prior unavailable/degraded evidence
current projection → does not rewrite history
```

Every material N4 evidence occurrence preserves, where applicable:

```text
N4 Recovery Participation Scope Reference
N4 Recovery / Diagnostic Evidence Reference
Node / Participant Reference
R4 Recovery Scope Reference
R4 Recovery / Reconciliation-stage Evidence Reference
source owner / source boundary reference
source evidence identity/reference
source revision/context reference
N1/N2/N3 correlation references
re-observation request/result references
reconciliation-stage relationship
Tenant / Organization / Principal / Policy / Trust references
privacy / sensitivity / redaction context
temporal / currentness context
uncertainty / conflict / partiality qualification
compatibility / conformance context
causal / correlation provenance
```

Permanent:

```text
History != Current Projection
Later Evidence != Historical Rewrite
Provenance Collection != Authority Transfer
Source Re-observed != Source Rewritten
Replay != Historical Fact Rewrite
```

No event-store architecture, compaction policy, persistence schema or universal event namespace is selected.

---

# 14. N4-R10 — RCP-20 / RCP-22 Stable-contract Governance, Compatibility & Conformance

**Purpose.** Govern N4's representation-neutral stable-contract contributions and ensure evolution retains source ownership, identity distinctions, offline/private correctness and non-destructive history.

N4-R10 does not create a new authority. It consumes N4-R01..R09 and publishes the semantic obligations defined in §§18–19.

Compatibility must preserve, where applicable:

```text
N4 Recovery Participation Scope identity/reference meaning
N4 Recovery / Diagnostic Evidence identity/reference meaning
R4 Recovery Scope / Evidence reference distinction
N1/N2/N3 source identity/reference meaning
source owner / source revision / provenance
re-observation request vs result distinction
reconciliation participation vs source recovery outcome distinction
currentness / availability / uncertainty / conflict / partiality meanings
Tenant / Principal / Policy / Trust / privacy context
non-destructive history
offline/private correctness
Secret Reference vs Secret Material separation
```

Accepted evolution classes remain:

```text
CONFORMANCE_ONLY_IMPLEMENTATION_CHANGE
COMPATIBLE_EVOLUTION
EXPLICIT_MIGRATION_REQUIRED
ARCHITECTURE_REVALIDATION_REQUIRED
OWNER_MDE_REQUIRED
```

Migration must not create two final owners for one source assertion, silently select a winner, rewrite historical evidence, or transform a local/central projection into source SoT.

---

# 15. ND-R04 Complete Traceability

| Accepted ND-R04 / N4 pressure | Internal responsibility |
|---|---|
| Node recovery participation scope / governed-context binding | `N4-R01` |
| local retained-evidence semantics / evidence availability | `N4-R02` |
| source owner / revision / provenance preservation | `N4-R02`, `N4-R09` |
| offline / degraded continuity qualification | `N4-R03`, `N4-R08` |
| RT-R04 recovery scope consumption | `N4-R01`, `N4-R04` |
| RT-R04 evidence-exchange participation | `N4-R04` |
| source-owner N1/N2/N3 re-observation participation | `N4-R05` |
| reconciliation-stage participation | `N4-R06` |
| conflict / partiality preservation | `N4-R06`, `N4-R08`, `N4-R09` |
| recovery / health / lifecycle diagnostics | `N4-R07` |
| currentness / availability / uncertainty | `N4-R08` |
| non-destructive history / lineage / provenance | `N4-R09` |
| RCP-20 Node participant-side stable-contract governance | `N4-R10` across `N4-R01..R09` |
| RCP-22 N4 producer + complete ns_node-side coverage | `N4-R07`, `N4-R08`, `N4-R09`, `N4-R10` |
| compatibility / migration / conformance | `N4-R10` |

```text
ND-R04 Traceability
→ COMPLETE

Unmapped ND-R04 Material Responsibility
→ 0
```

---

# 16. Authority / SoT / Actual-state Map

| Semantic subject | Final owner / authority | N4 relationship |
|---|---|---|
| N4 Recovery Participation Scope binding fact | `N4 / ND-R04` | owned Node-local participation fact |
| retained-evidence availability / N4 custody qualification | `N4 / ND-R04` | owned N4-local availability/custody fact only |
| N4 evidence-exchange participation fact | `N4 / ND-R04` | owned Node-side participation fact |
| N4 re-observation request/handoff/receipt/correlation fact | `N4 / ND-R04` | owned Node-side participation/correlation fact |
| N4 reconciliation-stage participation fact | `N4 / ND-R04` | owned Node-side participation fact |
| N4 offline/degraded continuity qualification | `N4 / ND-R04` | owned N4-local qualification |
| N4 recovery/health/lifecycle diagnostic fact | `N4 / ND-R04` | owned N4 diagnostic Actual-state |
| N4 currentness/availability/uncertainty/conflict qualification | `N4 / ND-R04` | owned only for N4 evidence/view |
| N4 recovery/diagnostic history/provenance | `N4 / ND-R04` | owned N4 evidence; references external/source owners |
| Node Readiness / Applied Config | `N1 / ND-R01` | retained/reference/re-observation target only |
| Node Attempt | `N2 / ND-R02` | retained/reference/re-observation target only |
| Node Effect / local source fact | `N3 / ND-R03` | retained/reference/re-observation target only |
| R1 Presence / reachability / reconnect coordination | `R1 / RT-R01` | reference only |
| R3 continuation/intervention coordination | `R3 / RT-R03` | correlation reference only |
| R4 Recovery Scope / exchange / re-observation / reconciliation coordination facts | `R4 / RT-R04` | consumed/correlated; never re-owned |
| Formal Execution Admission | `S8 / SV-R04` | historical/applicability reference only |
| Managed Desired Configuration | `S9 / SV-R05` | reference only through accepted source evidence |
| source-domain recovery outcome | original applicable source owner | N4 may correlate evidence/reference only |
| conflict winner / merged canonical state | applicable source/domain authority if ever established | NOT owned or selected by N4 |

```text
Authority Transfer
→ 0

SoT Transfer
→ 0

Final Actual-state Ownership Transfer
→ 0

Circular Actual-state Ownership
→ NONE
```

---

# 17. Recovery / Reconciliation / Replay Completion Semantics

The following subjects remain distinct:

```text
Reconnect
N4 Recovery Participation Started / Pending / Completed
RT-R04 Recovery Coordination Started / Pending / Completed
Evidence Exchange Started / Pending / Completed
Re-observation Requested
Re-observation Performed by Source Owner
Re-observation Result produced by Source Owner
N4 Reconciliation Participation Started / Pending / Completed
Conflict Detected
Conflict Resolved by applicable authority if ever established
Source Recovery Outcome
```

There is no universal `RECOVERED` state and no universal recovery-success law.

```text
Reconnect != Reconciled
N4 Recovery Participation Completed != RT-R04 Coordination Completed automatically
N4 Recovery Participation Completed != Source Recovery Outcome
Evidence Exchange Completed != Conflict Resolved
Re-observation Result Received != Canonical automatically
Source Re-observed != Source Rewritten
Reconciliation Participation Completed != Canonical Merged State
```

Replay is allowed only as source-defined reference/correlation pressure where applicable:

```text
Replay Request Reference
Replay Occurrence Reference
Source Evidence Reference produced after replay
Recovery / re-observation correlation after replay
```

N4 does not define replay semantics, replay engine, deterministic replay guarantee, replay-based authority reconstruction or historical rewriting.

---

# 18. RCP-20 — Exact ND-R04 Node-side Stable Contract Contribution

`RCP-20` is stabilized at the ND-R04 Node-local participant side only. It is a semantic information obligation, not a DTO, schema, API, endpoint, protocol or transport envelope.

## 18.1 Recovery participation scope / governed context

Where applicable, preserve:

```text
N4 Recovery Participation Scope Identity / Reference
Node / Participant Reference
R4 Recovery Scope Identity / Reference
Recovery Subject Reference
Source Owner Reference
Source Domain / Runtime-partition Reference
Source Revision / Context Reference
Original Source Evidence Reference
Tenant Context
Organization Context where applicable
Principal Context
Policy / Trust Context References
Privacy / Sensitivity / Redaction Context
Temporal Context
Compatibility / Conformance Context
```

## 18.2 Node source-evidence correlation

Where applicable:

```text
N1 Readiness / Applied Configuration Evidence Reference
N2 Attempt Identity / Evidence Reference
N3 Effect / Source Evidence Identity / Reference
Operation / Work Reference
Admission / Dispatch / R3 references only when already part of accepted provenance
source-provided currentness / uncertainty context
Node-local retention availability qualification
```

N4 never replaces the source identity with an N4 evidence identity.

## 18.3 RT-R04 evidence-exchange correlation

Where applicable:

```text
R4 Recovery / Reconciliation-stage Evidence Identity / Reference
Evidence-exchange Request / Handoff / Receipt Reference
N4 Evidence-exchange Participation Evidence
exchange currentness / availability / partiality qualification
```

## 18.4 Re-observation correlation

Where applicable:

```text
N4 Re-observation Request Reference
Source Owner Reference
Source Subject / Evidence Reference
R4 Re-observation Coordination Reference
Source-owner Re-observation Result / Evidence Reference where supplied
N4 receipt / correlation / currentness qualification
```

## 18.5 Reconciliation participation evidence

Where applicable:

```text
N4 Reconciliation Participation Evidence
R4 Reconciliation-stage Evidence Reference
participating source evidence references
currentness / freshness
availability / reachability
uncertainty / indeterminate qualification
conflict qualification
partiality qualification
temporal context
history / lineage / provenance
```

## 18.6 Producer / consumer obligations

ND-R04 MUST:

1. emit only N4-local participation/diagnostic facts N4 is authorized to own;
2. preserve N1/N2/N3 source identity, owner, revision and provenance;
3. keep N4 scope/evidence identity distinct from R4 and source identities;
4. keep evidence handoff/receipt distinct from canonical acceptance;
5. keep re-observation request/receipt distinct from source result ownership;
6. keep reconciliation participation distinct from conflict resolution/source outcome;
7. preserve currentness, availability, uncertainty, conflict and partiality without a winner law;
8. retain non-destructive history and prior failures/conflicts;
9. remain private/offline capable and Secret-Material safe;
10. remain representation-neutral and compatibility/conformance aware.

A consumer MUST NOT infer from N4 RCP-20 evidence alone:

```text
source fact changed
source recovery succeeded
conflict resolved
canonical winner selected
merged canonical state exists
Admission / Policy / Trust granted
replay reconstructed original authority
```

```text
RCP-20 ND-R04 Node-local participant-side contribution
→ CLOSED AT CURRENT CANDIDATE DESIGN LEVEL

RCP-20 Full Cross-component Closure
→ NOT CLOSED / NOT CLAIMED
```

---

# 19. RCP-22 — Complete ns_node-side Diagnostics / Provenance Contribution at Current Design Level

Accepted Batch-1 producers remain authoritative for their own diagnostic/provenance subjects:

```text
N1 / ND-R01
→ readiness / capability / Applied Configuration provenance and bounded technical diagnostics

N2 / ND-R02
→ Attempt / intervention-target / execution-context provenance and bounded technical diagnostics

N3 / ND-R03
→ protected Effect / source evidence provenance, currentness/uncertainty and disclosure-safe diagnostics
```

N4 adds only:

```text
recovery-participation scope / lifecycle diagnostics
retained-evidence availability / custody diagnostics
offline / degraded continuity diagnostics
RT-R04 evidence-exchange participation diagnostics
source-owner re-observation participation diagnostics
reconciliation-stage participation diagnostics
N4 health / availability / lifecycle evidence
N4 currentness / freshness / uncertainty / conflict / partiality diagnostics
N4 correlation / lineage / provenance evidence
```

The complete ns_node-side RCP-22 contribution is therefore **federated by original fact ownership**. N4 may correlate N1/N2/N3 producer references but does not canonicalize them into one Node diagnostic SoT.

Every Node diagnostic contribution preserves where applicable:

```text
Node / Participant Reference
original producer boundary / runtime-role reference
source evidence identity/reference
source owner / source revision/context
applicable Operation / Attempt / Effect / Recovery Scope correlations
Tenant / Principal / Policy / Trust / privacy context
sensitivity / redaction qualification
temporal / currentness context
availability / uncertainty / conflict / partiality
history / lineage / provenance
compatibility / conformance context
```

Permanent:

```text
Diagnostic Observation != Source Semantic Fact
Diagnostic Aggregation != Canonicalization
Diagnostic Success != Recovery Success automatically
RCP-22 Node contribution != Universal Node Diagnostic SoT
```

```text
RCP-22 ns_node-side contribution
→ COMPLETE AT CURRENT CANDIDATE DESIGN LEVEL

RCP-22 Full Cross-component Closure
→ NOT CLOSED / NOT CLAIMED

WB diagnostics UI / SDK diagnostics model / Agent diagnostics
→ NOT DESIGNED
```

---

# 20. Bounded RCP Correlation Matrix

| RCP | N4 contribution | Preserved owner | Explicit non-claim |
|---|---|---|---|
| `RCP-03` Presence | consume/correlate Participant, Presence/reconnect and currentness refs only | `R1 / RT-R01` | reconnect evidence != reconciled/source recovered |
| `RCP-04` Node Readiness | retain/reference/re-observation target only | `N1 / ND-R01` | no readiness semantic redesign |
| `RCP-06` Continuation / Intervention | correlate recovery/resume/intervention request/evidence refs only | `RT-R03` coordination + final source owner | request/coordination != outcome |
| `RCP-07` Node Attempt | retain/reference/re-observation target only | `N2 / ND-R02` | no Attempt semantic redesign |
| `RCP-08` Node Effect Evidence | retain/reference/re-observation target only | `N3 / ND-R03` | no Effect/source ownership redesign |
| `RCP-19` Applied Configuration | retain/reference N1 Applied and S9 Desired provenance only | `N1` Applied / `S9` Desired | no config authority movement |
| `RCP-20` Recovery/Reconciliation | ND-R04 participant-side contribution | N4 owns only local participation facts; RT-R04 coordination and source owners preserved | Full cross-component closure not claimed |
| `RCP-22` Diagnostics/Provenance | N4 producer + complete ns_node-side producer coverage by original owner | N1/N2/N3/N4 each retain own facts | no universal diagnostic SoT / full closure |
| `RCP-24` Human/SDK Intent | receive/correlate recovery/resume intent reference where targeted | WB/SDK interaction side downstream; receiving semantic outcome owner preserved | intent != applied/outcome |

`RCP-02 / RCP-05 / RCP-13 / RCP-15 / RCP-17` may appear only as historical/provenance context already attached to accepted source evidence; no additional semantics are designed here.

---

# 21. Failure / Unknown / Stale / Conflict / Partial Semantics

| Qualification | N4 meaning | Forbidden inference |
|---|---|---|
| `UNKNOWN` | N4 cannot establish required fact from admissible evidence | absent / false / failed |
| `STALE` | applicable currentness cannot be established for the evidence/view | invalid / false / loser |
| `UNAVAILABLE` | needed evidence/capability cannot currently be obtained | denied / failed / deleted |
| `UNREACHABLE` | applicable participant/source cannot currently be reached | source invalid / revoked |
| `INDETERMINATE` | evidence is insufficient, ambiguous or context-incomplete | fallback to latest/local/central |
| `CONFLICTING` | relevant evidence disagrees under current interpretation | conflict resolved / winner chosen |
| `PARTIAL` | only a bounded subset of evidence/participation is established | complete |
| `RECOVERY_PENDING` | N4 participation is not complete for its bounded scope | source failure / source recovery |
| `RECONCILIATION_PENDING` | N4 reconciliation participation remains incomplete | conflict resolved |
| `RECOVERING` | N4 is actively participating where established | source recovery success |

No universal rule converts uncertainty into allow/deny, success/failure, authoritative state or execution permission.

---

# 22. Shared Foundation Consumption

Accepted Shared Foundation remains authority-neutral and is reused rather than duplicated.

| Accepted Foundation semantic | N4 use | Non-implication |
|---|---|---|
| Bootstrap Configuration Acquisition | N4-local bootstrap acquisition where applicable | loader != Desired Config Authority |
| Diagnostic / Technical Observation | N4 recovery/health/lifecycle diagnostic occurrence | diagnostic primitive != source authority |
| Temporal & Freshness | source-vs-N4 receipt/currentness/history qualification | clock/freshness helper != canonical winner |
| Operation Correlation & Provenance Context | Node/R4/source/re-observation/reconciliation correlation | carrier != operation/source owner |
| Semantic Representation & Serialization | representation-neutral RCP-20/RCP-22 realization | representation != semantic authority |
| Network Invocation Mechanics | reusable mechanics for evidence exchange/re-observation where applicable | transport != recovery authority |
| Technical Status & Uncertainty | UNKNOWN/STALE/UNAVAILABLE/CONFLICTING/PARTIAL etc. | helper != domain outcome authority |
| Governed Context Propagation | Tenant/Principal/Policy/Trust refs through recovery | carrier != governance authority |
| Secret Reference | authorized references only | Secret Reference != Secret Material |
| Sensitive-data Redaction | protected recovery/diagnostic disclosure | redactor != Privacy/Policy Authority |
| Compatibility & Conformance | evidence/contract evolution | helper != universal Compatibility Authority |

Where accepted Foundation supplies diagnostic-delivery or storage-access mechanics, such mechanics remain conditional realization support and never become N4 semantic authority or SoT.

```text
Missing Mandatory Shared Foundation Semantic
→ NONE_FOUND

Node-local Parallel Foundation
→ 0

New Foundation Capability / Contract / Module / Provider Required
→ 0
```

---

# 23. Secret / Privacy / Security Boundary

N4 preserves Tenant/Principal/Policy/Trust/privacy and source sensitivity through retention, exchange, re-observation, reconciliation participation and diagnostics.

```text
Secret Reference
→ may be retained/exposed only as authorized metadata where necessary

Secret Material
→ MUST NOT be placed into ordinary recovery/diagnostic evidence merely for observability

Redacted Projection
→ does not mutate underlying source evidence

Offline / degraded mode
→ does not relax redaction/privacy requirements
```

N4 does not become IAM, Policy, Trust, Privacy or Secret-Material Authority.

---

# 24. Compatibility / Migration / Conformance

N4 evolution must preserve:

```text
N4 scope/evidence identity meanings
R4-vs-N4 scope/evidence identity distinction
N1/N2/N3 source-owner identities
source revision/provenance
re-observation request/result ownership distinction
reconciliation participation/source outcome distinction
currentness/availability/uncertainty/conflict/partiality semantics
Tenant/Principal/Policy/Trust/privacy context
non-destructive history
offline/private correctness
RCP-20/RCP-22 non-collapse rules
```

Migration must never:

```text
promote local/central copy by location
select latest timestamp/arrival as winner
merge source facts without source/domain authority
rewrite historical conflicts/failures
create two final owners for one assertion
convert diagnostics into source truth
```

Any evolution that changes those semantics requires `ARCHITECTURE_REVALIDATION_REQUIRED` or `OWNER_MDE_REQUIRED` according to accepted classification.

---

# 25. Dependency Taxonomy and Hard Internal SDD Graph

Accepted taxonomy:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only SDD enters hard cycle analysis.

Hard N4 SDD edges:

```text
N4-R02 → N4-R01
N4-R08 → N4-R01, N4-R02
N4-R03 → N4-R01, N4-R02, N4-R08
N4-R04 → N4-R01, N4-R02, N4-R08
N4-R05 → N4-R01, N4-R02, N4-R04, N4-R08
N4-R06 → N4-R01, N4-R02, N4-R04, N4-R08
N4-R07 → N4-R01, N4-R03, N4-R04, N4-R05, N4-R06, N4-R08
N4-R09 → N4-R01, N4-R02, N4-R03, N4-R04, N4-R05, N4-R06, N4-R07, N4-R08
N4-R10 → N4-R01, N4-R02, N4-R03, N4-R04, N4-R05, N4-R06, N4-R07, N4-R08, N4-R09
```

One valid topological order:

```text
N4-R01
→ N4-R02
→ N4-R08
→ {N4-R03, N4-R04}
→ {N4-R05, N4-R06}
→ N4-R07
→ N4-R09
→ N4-R10
```

Accepted N1/N2/N3 source evidence enters N4 through `XED / EL / HPL` as applicable, not reverse SDD. RT-R04 coordination evidence is `XED / ACD / EL`; N4 does not define RT-R04. Source-owner re-observation results may inform N4 reconciliation participation through `EL/XED` but are intentionally not reverse SDD.

```text
Hard Internal SDD Graph
→ ACYCLIC

Unresolved Semantic-definition Cycle
→ 0

Authority Cycle
→ NONE

Circular Actual-state Ownership
→ NONE
```

---

# 26. MDE Boundary / Revalidation Triggers

No Owner-reserved durable commitment is required by this synthesis.

```text
New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

Immediate STOP / Owner MDE escalation is required if later design materially requires:

```text
fail-open / fail-closed Product policy
latest-wins / earliest-wins / local-wins / central-wins
source-priority or majority winner
cross-source merge law
authoritative synchronization direction
universal replay semantics / deterministic replay guarantee
universal retry / cancellation semantics
rollback / compensation / protected-effect reversal law
exactly-once / at-most-once / at-least-once
cross-Tenant Node recovery/reconciliation semantics
mandatory database / storage / event store
mandatory queue / broker / scheduler / workflow/recovery/reconciliation/replay engine
mandatory public SaaS / cloud control plane
provider / protocol / framework / storage lock-in
major universal identity namespace
new Product capability
other high-migration durable commitment
```

None is necessary for current N4 closure.

---

# 27. Explicit Implementation Deferrals

This Candidate intentionally does not select or design:

```text
Redis / RabbitMQ / Kafka / NATS
Celery / Temporal / Airflow / Quartz / APScheduler
database / storage engine / event store / table / ORM
queue / broker / scheduler / workflow engine
recovery / reconciliation / replay engine
REST / gRPC / concrete WebSocket frame / handshake / envelope
DTO / wire schema
process / service / worker / thread / coroutine
container / pod / host / deployment topology
UUID / physical key / message ID format
exactly-once / at-most-once / at-least-once
retry / timeout / expiry / backoff / cancellation algorithm
conflict winner / merge / synchronization algorithm
replay algorithm / deterministic replay guarantee
```

No key architecture rule is left for implementation to invent: N4 ownership, source-owner preservation, RT-R04 boundary, recovery/reconciliation non-collapse, identities, retained-evidence semantics, re-observation, conflict/partiality, currentness/uncertainty, history/provenance, RCP-20/RCP-22 obligations, private/offline behavior and MDE triggers are fixed above.

---

# 28. DAD Summary

Material delegated architecture decisions are persisted separately in:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_node_internal_design_batch_2_dad_evidence_0.0.1.md`

Candidate DAD set:

```text
CID-ND-B2-DAD-001 → 10-responsibility N4 decomposition
CID-ND-B2-DAD-002 → N4 scoped recovery-participation / diagnostic identities and R4 identity non-collapse
CID-ND-B2-DAD-003 → retained-evidence availability / source-attribution semantics without storage selection
CID-ND-B2-DAD-004 → offline/degraded continuity qualification without fail-open/fail-closed policy or linear recovery state machine
CID-ND-B2-DAD-005 → RT-R04 evidence-exchange participant boundary
CID-ND-B2-DAD-006 → N1/N2/N3 source-owner re-observation participation boundary
CID-ND-B2-DAD-007 → reconciliation participation / conflict-partiality preservation without winner law
CID-ND-B2-DAD-008 → N4 currentness / availability / uncertainty semantics and source-vs-observation temporal separation
CID-ND-B2-DAD-009 → non-destructive recovery/diagnostic history and replay non-authority boundary
CID-ND-B2-DAD-010 → RCP-20 ND-R04 participant-side stable semantic contract
CID-ND-B2-DAD-011 → RCP-22 complete ns_node-side diagnostics/provenance contribution by federated original ownership
CID-ND-B2-DAD-012 → bounded RCP-03 / RCP-06 / RCP-24 correlation and RCP-04/07/08/19 upstream preservation
CID-ND-B2-DAD-013 → Shared Foundation consumption / secret-redaction / private-offline neutrality
CID-ND-B2-DAD-014 → compatibility / migration / conformance boundaries
CID-ND-B2-DAD-015 → typed dependency model and acyclic hard SDD graph
```

All are within delegated Component Internal Design authority and do not select an Owner-reserved MDE answer.

---

# 29. Candidate Audit Summary

Detailed review evidence is persisted separately. Candidate-level result:

```text
N4 Internal Responsibility Coverage
→ COMPLETE / 10

ND-R04 Traceability
→ COMPLETE

N1/N2/N3 Source-owner Preservation
→ COMPLETE

RT-R04 Coordination Authority Preservation
→ COMPLETE

RCP-20 ND-R04 Contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-20 Full Cross-component Closure
→ NOT CLAIMED

RCP-22 ns_node-side Contribution
→ COMPLETE AT CURRENT DESIGN LEVEL

RCP-22 Full Cross-component Closure
→ NOT CLAIMED

Reconnect / Recovery / Reconciliation Non-collapse
→ PRESERVED

Conflict Winner / Merge Law
→ NOT CREATED

Replay Authority Reconstruction
→ NOT CREATED

Hard Internal SDD Graph
→ ACYCLIC

Unresolved SDD Cycle
→ 0

Mandatory Missing Shared Foundation Semantic
→ 0

New MDE
→ 0

Implementation Leakage
→ 0

Unauthorized Downstream Progression
→ 0
```

---

# 30. Candidate Status / Stop Boundary

```text
NGRP-001 — Component Internal Design / ns_node / Batch 2

N4 / ND-R04 Producing Design
→ COMPLETED

Maximum Legal State
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE

ns_node Batch 2 Global Acceptance
→ NOT CLAIMED

ns_node Internal Design Exhaustion
→ NOT CLAIMED

ns_node Component Internal Design Global Closure
→ NOT CLAIMED

RCP-20 Full Cross-component Closure
→ NOT CLAIMED

RCP-22 Full Cross-component Closure
→ NOT CLAIMED

ns_agent / ns_web / SDK / Implementation
→ NOT AUTHORIZED
```

```text
STOP AFTER PERSISTED HANDOFF
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
→ FOR INDEPENDENT GLOBAL ACCEPTANCE REVIEW
```
