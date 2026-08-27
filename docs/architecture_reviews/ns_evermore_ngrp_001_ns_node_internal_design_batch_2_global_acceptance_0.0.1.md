# NGRP-001 — Component Internal Design / ns_node / Batch 2 — Global Acceptance

- Authority: `GLOBAL ARCHITECTURE COORDINATOR`
- Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_NODE / BATCH_2 / OFFLINE_CONTINUITY_RECOVERY_AND_LOCAL_DIAGNOSTICS_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Producing Entry HEAD: `90ab35107627ab021e7eb67ca95593668454d037`
- Producing Final HEAD: `5f7a052147be7fcfe6a765f2d185503e7bc8f931`
- Entry Global State: `GAC-EPOCH-0084`
- Result: `GLOBAL_ACCEPT`

## 1. Independent Recovery / Producing Delta Review

Fresh GAC recovery independently resolved the actual branch and compared the Batch-2 authorization seal with the producing final HEAD.

```text
Authorization Seal / Producing Entry HEAD
→ 90ab35107627ab021e7eb67ca95593668454d037

Producing Final HEAD
→ 5f7a052147be7fcfe6a765f2d185503e7bc8f931

Producing Commit Count
→ 4

Candidate Commit
→ 9339615d310b8976c78db29fa4b7d77972a9af51

DAD Commit
→ 3b977bd47b9a5531b7ec34ed24ab9f4364893cf7

Review / Audit Commit
→ 59187870d6954e6c90f0630ac8df41fc4e6eb8f5

Handoff / Producing Final Commit
→ 5f7a052147be7fcfe6a765f2d185503e7bc8f931

Producing Delta
→ exactly 4 newly added Batch-2 architecture-review evidence files

Existing governance / normative file modified by producing range
→ 0

Source / implementation file modified by producing range
→ 0

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE

Producing Delta Classification
→ EXPECTED_PHASE_EVIDENCE
```

The producing chain was independently verified as four one-commit / one-file transitions.

## 2. Accepted N4 / ND-R04 Internal Architecture

```text
N4
→ Offline Continuity, Recovery & Local Diagnostics

ND-R04
→ Node Offline Continuity & Recovery Participant
```

Accepted architecture-semantic responsibilities:

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
Accepted Internal Responsibility Count
→ 10

N4 Boundary Coverage
→ 1 / 1 / 100%

Unowned Material N4 Responsibility
→ 0

Duplicate Final Responsibility
→ 0

Hard Internal SDD Graph
→ ACYCLIC
```

The responsibility labels are architecture-semantic constructs only and imply no module/service/process/store/queue/API/schema/deployment topology.

## 3. Accepted N4 Authority / SoT / Actual-state Partition

N4 owns only facts genuinely originating in the Node-local offline/recovery/diagnostic participation boundary:

```text
N4 Recovery Participation Scope binding facts
retained-evidence availability / source-attribution / N4 custody qualification facts
Node-local offline / degraded continuity qualification
N4 evidence-exchange participation / handoff / receipt / correlation facts
N4 source-owner re-observation request / handoff / receipt / correlation facts
N4 reconciliation-stage participation facts
N4 recovery / health / lifecycle diagnostic facts
N4 currentness / availability / uncertainty / conflict / partiality qualifications
N4 non-destructive recovery / diagnostic history / lineage / provenance
```

Preserved source/coordination ownership:

```text
N1 Readiness / Applied Configuration source facts → N1 / ND-R01
N2 Attempt source facts → N2 / ND-R02
N3 Effect / genuine Node-origin source facts → N3 / ND-R03
R4 Recovery Scope / exchange / re-observation / reconciliation coordination truth → R4 / RT-R04
source-domain recovery outcome → original applicable source owner
Tenant / Principal / IAM / Policy / Trust → accepted ns_server authorities
Formal Admission → S8 / SV-R04
Dispatch → R2 / RT-R02
Automation / Agent / Business semantic outcomes → applicable semantic owner
external factual SoTs → applicable external/source owner
```

Permanent:

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

```text
Authority Transfer → 0
SoT Transfer → 0
Final Actual-state Ownership Transfer → 0
Circular Actual-state Ownership → NONE
```

## 4. Accepted N4 Identity / Correlation Baseline

Accepted scoped N4 evidence subjects:

```text
N4 Recovery Participation Scope Identity / Reference
N4 Recovery / Diagnostic Evidence Identity / Reference
```

They are representation-neutral, Node/N4-bounded and non-authoritative for N1/N2/N3/R4 source facts. They remain distinct from R4 Recovery Scope/Evidence identities, Operation, Admission, Dispatch, Attempt and Effect identities.

```text
Major Universal Recovery Identity Namespace → NOT CREATED
UUID / Database Key / Message ID / Wire Identifier Selection → 0
```

## 5. RCP-20 Acceptance

```text
RCP-20 / Recovery / Reconciliation
→ ND-R04 Node-local participant-side contribution CLOSED AT CURRENT DESIGN LEVEL

RCP-20 Full Cross-component Closure
→ NOT CLOSED / NOT CLAIMED
```

Accepted Node-side stable semantics cover representation-neutral N4 participation scope, Node/Participant, R4 Recovery Scope, source owner/domain/revision/original-evidence references, accepted N1/N2/N3 source-evidence correlation, RT-R04 exchange-stage references, re-observation request/result correlation, reconciliation participation evidence, currentness/freshness/availability/uncertainty/conflict/partiality, governed context, temporal/history/lineage/provenance, compatibility/migration/conformance and private/offline qualification.

No source winner, canonical merge, source-authority rewrite, authoritative synchronization direction, replay/recovery algorithm, API/wire/schema or execution guarantee is implied.

## 6. RCP-22 Acceptance

```text
RCP-22 / Diagnostics / Provenance
→ N4 recovery / health / lifecycle / offline diagnostic producer contribution CLOSED AT CURRENT DESIGN LEVEL

RCP-22 complete ns_node-side contribution
→ COMPLETE AT CURRENT DESIGN LEVEL / FEDERATED BY ORIGINAL FACT OWNERSHIP

RCP-22 Full Cross-component Closure
→ NOT CLOSED / NOT CLAIMED
```

Accepted Batch-1 N1/N2/N3 producer contributions remain authoritative for their own subjects. N4 adds only its own recovery/continuity/retention/health/lifecycle/reconciliation-participation diagnostics and may correlate N1/N2/N3 evidence by reference without canonicalization.

Permanent:

```text
Diagnostic Observation != Source Semantic Fact
Diagnostic Aggregation != Canonicalization
Diagnostic Success != Source Recovery Success automatically
RCP-22 Node contribution != Universal Node Diagnostic SoT
```

WB/SDK diagnostic presentation and Agent-side diagnostic contribution remain downstream.

## 7. Source-owner Re-observation Acceptance

Permanent:

```text
Re-observation Request != Source Fact
Re-observation Performed != Source Changed
Source Re-observed != Source Rewritten
Re-observation Result Received != Result Accepted as Canonical automatically
Re-observation Failure != Source Fact Invalid
No Response != Source Fact Deleted
```

N1/N2/N3 perform and own re-observation results for their respective source partitions. N4 owns only request/handoff/receipt/correlation participation facts and its own qualification of received references. RT-R04 remains the recovery/re-observation coordination owner.

## 8. Recovery / Reconciliation / Conflict Acceptance

The accepted design preserves distinct recovery subjects and stages rather than a universal `RECOVERED` state.

```text
Reconnect
!= N4 Recovery Participation
!= RT-R04 Recovery Coordination
!= Evidence Exchange
!= Re-observation Requested / Performed / Result
!= Reconciliation Participation
!= Conflict Resolution
!= Source Recovery Outcome
```

No latest-wins, earliest-wins, local-wins, central-wins, source-priority, majority-wins, cross-source merge law, authoritative synchronization direction or Product-wide conflict-resolution algorithm is created.

`CONFLICTING` and `PARTIAL` remain explicit provenance-bearing qualifications and may remain unresolved after N4 participation completes.

## 9. Replay / Offline / Failure Acceptance

Replay remains source-defined reference/correlation pressure only where applicable.

```text
Universal Replay Semantics → NOT CREATED
Deterministic Replay Guarantee → NOT CREATED
Replay Algorithm / Engine → NOT SELECTED
Replay-based Authority Reconstruction → NOT CREATED
Replay != Retroactive Authorization
Replay != Historical Fact Rewrite
```

Applicable N4 qualifications include `UNKNOWN`, `STALE`, `UNAVAILABLE`, `UNREACHABLE`, `INDETERMINATE`, `CONFLICTING`, `PARTIAL`, `RECOVERY_PENDING`, `RECONCILIATION_PENDING` and `RECOVERING`. These are orthogonal architecture-semantic qualifications, not a universal linear recovery state machine.

No Product-wide fail-open or fail-closed policy is selected. Core correctness requires no mandatory public Internet, public SaaS, hosted recovery control plane, cloud broker or external recovery authority.

## 10. History / Provenance Acceptance

History is non-destructive:

```text
one participation scope may contain multiple exchange / re-observation / reconciliation / diagnostic occurrences
one source assertion may have multiple historical observations
one conflict may retain multiple conflicting evidence items
later re-observation / recovery success does not rewrite prior evidence
later success does not erase prior failure / conflict / uncertainty
current projection does not rewrite history
```

Source owner, source revision/evidence identity, temporal/currentness context, uncertainty, compatibility and recovery/diagnostic provenance remain historically attributable.

## 11. Shared Foundation / Security / Technology Neutrality

Accepted Shared Foundation semantics are reused for Bootstrap Configuration Acquisition, Diagnostic/Technical Observation, Temporal/Freshness, Correlation/Provenance, Representation/Serialization, Network Mechanics, Technical Status/Uncertainty, Governed Context, Secret Reference, Sensitive-data Redaction and Compatibility/Conformance.

```text
Missing Mandatory Shared Foundation Semantic → NONE_FOUND
New Foundation Capability / Contract / Module / Provider → 0
Node-local Parallel Foundation → 0
Foundation Authority Transfer → 0
```

Secret Material is excluded from ordinary recovery/diagnostic evidence. Privacy/redaction remains mandatory in offline/degraded operation.

No database/event store, queue/broker/scheduler/workflow/recovery/reconciliation/replay engine, REST/gRPC/concrete WebSocket framing, DTO/wire schema, process/service/worker/thread/coroutine/container/deployment topology or physical identity format is accepted.

## 12. DAD / Review Acceptance

```text
Accepted DAD → CID-ND-B2-DAD-001..015
Required Producing Reviews → 33
Producing Review PASS / FAIL / BLOCKED → 33 / 0 / 0
GAC Independent Correction-required Issue → NONE_FOUND
New MDE → 0
Misclassified MDE → 0
Open MDE → 0
Unpersisted Owner Decision → 0
Implementation Leakage → 0
```

No fail policy, conflict winner/merge/sync law, universal replay/retry/cancellation/rollback/compensation/once guarantee, cross-Tenant recovery law, mandatory persistence/recovery technology, provider/protocol/framework/storage lock-in, major universal identity namespace or new Product capability is accepted.

## 13. Batch Result and Non-implications

```text
NGRP-001 — Component Internal Design / ns_node / Batch 2 / N4
→ GLOBAL_ACCEPTED

Accepted ns_node Boundaries
→ N1 / N2 / N3 / N4

Accepted ns_node Boundary Coverage
→ 4 / 4 / 100%

Accepted ns_node Internal Responsibility Count
→ 33
```

This acceptance does **not** by itself establish:

```text
ns_node Internal Design Exhaustion → SATISFIED
ns_node Component Internal Design → GLOBAL_CLOSED / COMPLETE
RCP-20 Full Cross-component Closure
RCP-22 Full Cross-component Closure
ns_agent / ns_web authorization
System-level SDK Detailed Design readiness
Design-to-Implementation Readiness
Implementation Planning / IWP / Coding
```

A separate fresh-recovery GAC post-Batch-2 remaining-pressure / exhaustion / global-closure assessment is mandatory before any ns_node global-closure declaration or subsequent Product Component authorization.
