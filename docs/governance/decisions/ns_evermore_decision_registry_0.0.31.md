# ns_evermore Decision Registry — Current Revision

- Version: `0.0.31`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.30`

All accepted normative decisions and baselines in Decision Registry `0.0.30` remain in force unless explicitly refined below.

## Current Accepted Global Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
Unified Governance → 0.0.2 / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Product Capability Exhaustion → SATISFIED
Five-component Internal Architecture Boundaries → GLOBAL_ACCEPTED / NORMATIVE
Five-component Internal-boundary Exhaustion → SATISFIED
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

ns_node Component Internal Design / Batch 1 → GLOBAL_ACCEPTED
ns_node Component Internal Design / Batch 2 / N4 → GLOBAL_ACCEPTED
Accepted ns_node Boundaries → N1 / N2 / N3 / N4
Accepted ns_node Boundary Coverage → 4 / 4 / 100%
Remaining accepted ns_node boundary without Component Internal Design → NONE
ns_node Internal Design Exhaustion → NOT YET REASSESSED AFTER BATCH 2 ACCEPTANCE
ns_node Component Internal Design Global Closure → NOT DECLARED
```

Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_node_internal_design_batch_2_global_acceptance_0.0.1.md`

## Accepted N4 / ND-R04 Internal Architecture

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
Accepted N4 Internal Responsibility Count → 10
Accepted ns_node Internal Responsibility Count → 33
Missing accepted ns_node Runtime-role source-boundary design → 0
Hard N4 Internal SDD Graph → ACYCLIC
Unresolved Semantic-definition Cycle → 0
Authority Cycle → NONE
Circular Actual-state Ownership → NONE
```

## N4 Authority / SoT / Actual-state Partition

N4 owns only Node-local facts genuinely originating in its offline/recovery/diagnostic participation boundary:

```text
N4 recovery-participation scope binding
retained-evidence availability / source-attribution / N4 custody qualification
Node-local offline / degraded continuity qualification
N4 evidence-exchange participation / handoff / receipt / correlation
N4 re-observation request / handoff / receipt / result-reference correlation
N4 reconciliation-stage participation
N4 recovery / health / lifecycle diagnostics
N4 currentness / availability / uncertainty / conflict / partiality
N4 non-destructive recovery / diagnostic history / lineage / provenance
```

Preserved final owners:

```text
N1 Readiness / Applied Configuration → N1 / ND-R01
N2 Attempt → N2 / ND-R02
N3 Effect / genuine Node-origin source fact → N3 / ND-R03
R4 Recovery Scope / evidence exchange / re-observation / reconciliation coordination → R4 / RT-R04
source-domain recovery outcome → original applicable source owner
Formal Admission → S8 / SV-R04
Dispatch → R2 / RT-R02
Managed Desired Configuration → S9 / SV-R05
external factual SoTs → applicable source owner
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

## Stable Contract Qualification

```text
RCP-20 ND-R04 Node-local participant-side contribution → CLOSED AT CURRENT DESIGN LEVEL
RCP-20 Full Cross-component Closure → NOT CLOSED

RCP-22 N4 recovery/health/lifecycle/offline diagnostic contribution → CLOSED AT CURRENT DESIGN LEVEL
RCP-22 complete ns_node-side contribution → COMPLETE AT CURRENT DESIGN LEVEL / FEDERATED BY ORIGINAL FACT OWNERSHIP
RCP-22 Full Cross-component Closure → NOT CLOSED
```

Accepted Batch-1 contracts remain normative upstream and are not reopened:

```text
RCP-04 / N1 Readiness
RCP-07 / N2 Attempt
RCP-08 / N3 Effect Evidence
RCP-19 / N1 Applied Configuration
```

Bounded correlation remains:

```text
RCP-03 → reconnect / Participant references only / RT-R01 authority preserved
RCP-06 → recovery/resume/intervention coordination correlation only / RT-R03 + final source owner preserved
RCP-24 → targeted Human/SDK recovery/resume intent receiving correlation only / source side downstream
```

No full cross-component closure is inferred from Batch-2 acceptance.

## Identity / History / Diagnostics Baseline

Accepted bounded identities:

```text
N4 Recovery Participation Scope Identity / Reference
N4 Recovery / Diagnostic Evidence Identity / Reference
```

They are representation-neutral, Node/N4-bounded and distinct from R4 scope/evidence plus N1/N2/N3 source identities. No universal recovery identity namespace or physical identifier format is accepted.

History remains non-destructive. Re-observation, recovery success or current projection cannot rewrite prior source evidence, failures, conflicts or uncertainty.

The complete ns_node-side RCP-22 contribution remains federated by original fact ownership; N4 does not become a universal Node diagnostic SoT.

## Failure / Offline / Replay Baseline

Applicable explicit qualifications include `UNKNOWN`, `STALE`, `UNAVAILABLE`, `UNREACHABLE`, `INDETERMINATE`, `CONFLICTING`, `PARTIAL`, `RECOVERY_PENDING`, `RECONCILIATION_PENDING` and `RECOVERING` where evidenced.

```text
Product-wide Fail-open Policy → NOT SELECTED
Product-wide Fail-closed Policy → NOT SELECTED
Universal RECOVERED State → NOT CREATED
Universal Replay Semantics → NOT CREATED
Deterministic Replay Guarantee → NOT CREATED
Conflict Winner / Merge Law / Authoritative Sync Direction → NOT CREATED
```

Private/offline correctness does not depend on public Internet, public SaaS, hosted recovery control plane or cloud recovery authority.

## DAD / MDE / Foundation / Technology Qualification

```text
Accepted DAD → CID-ND-B2-DAD-001..015
Owner-reserved MDE disguised as DAD → 0
New MDE → 0
Open MDE → 0
Unpersisted Owner Decision → 0
Mandatory Missing Shared Foundation Semantic → NONE_FOUND
Implementation Leakage → 0
```

No universal retry/cancellation/rollback/compensation/protected-effect reversal law, exactly-/at-most-/at-least-once guarantee, cross-Tenant recovery law, mandatory persistence/recovery engine, provider/protocol/framework/storage lock-in, major universal identity namespace or new Product capability is accepted.

## Current Governance Boundary

```text
Current Authorized Phase → NONE
Authorization Scope → NONE

Open MDE → 0
Unpersisted Owner Decision → 0
Blocking Item → NONE

ns_node Internal Design Exhaustion → NOT YET REASSESSED AFTER BATCH 2 ACCEPTANCE
ns_node Component Internal Design Global Closure → NOT DECLARED

ns_agent Component Internal Design → NOT AUTHORIZED
ns_web Component Internal Design → NOT AUTHORIZED
System-level SDK Detailed Design → NOT AUTHORIZED
Design-to-Implementation Readiness → NOT AUTHORIZED
Implementation Planning / IWP / Coding → NOT AUTHORIZED
```

Unique next legal action after the Batch-2 acceptance governance seal:

```text
Fresh Repository recovery
→ perform post-Batch-2 ns_node Component Internal Design remaining-pressure / exhaustion / global-closure assessment
→ do not infer ns_node closure or authorize another Product Component automatically from this acceptance
```
