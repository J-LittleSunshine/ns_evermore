# NGRP-001 — Component Internal Design / ns_server / Batch 5 Candidate

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Component Internal Design / ns_server / Batch 5`
- Authorization Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_5 / SERVER_LOCAL_BACKGROUND_WORK_AND_ACTUAL_STATE_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Recovered Entry HEAD: `35db20dfe1b5363e6b091dc407a4cff322958c80`
- Recovered Global State: `GAC-EPOCH-0057`
- State Verified Through HEAD: `906cdcd0faebe512f2036fce99ae78fb0a7468f1`
- Decision Registry at entry: `0.0.20 / CURRENT / NORMATIVE`
- Authorized Boundary: `S10 — Server-local Background Work & Server Actual-state`
- Inherited Runtime Role: `SV-R06 — Server-local Background Execution Participant`
- Producing-session authority: bounded Component Internal Design DAD only; no Global Acceptance authority.
- Candidate Status: `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`

This artifact refines only accepted `S10` responsibility and the accepted `SV-R06` runtime Actual-state/source-fact partition. It also synthesizes the authorized S10 contribution to `RCP-23 — Server-native Runtime Evidence` and, using already globally accepted S5/SV-R01 and S7/SV-R03 producer semantics as normative upstream, closes the full RCP-23 contract at the current design-semantic level without reopening S5 or S7 internals.

It does not define or select Django Apps, Python packages/classes, ORM models, tables, database schemas, REST/RPC/gRPC/WebSocket APIs, message envelopes, Celery, APScheduler, cron, systemd timers, Redis Queue, RabbitMQ, Kafka, worker pools, daemons, processes, threads, asyncio task topology, queue/broker topology, exactly-once processing, deterministic replay, rollback, universal retry/cancellation engines, concrete Providers/vendors/libraries, repository layout, Implementation Planning, IWP or code.

---

# 1. Fresh Repository Recovery

Fresh Repository Recovery was completed before any S10 synthesis.

```text
Actual Branch HEAD at recovery
→ 35db20dfe1b5363e6b091dc407a4cff322958c80

Current Global State
→ GAC-EPOCH-0057

State Verified Through HEAD
→ 906cdcd0faebe512f2036fce99ae78fb0a7468f1

State-to-HEAD
→ ahead by exactly 1 commit

Changed file
→ docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md only

Delta meaning
→ GAC-EPOCH-0057 / ns_server Batch 5 S10 authorization seal

Delta Classification
→ EXPECTED_GOVERNANCE

UNAUTHORIZED_PROGRESSION
→ NONE

UNEXPLAINED_DRIFT
→ NONE
```

The complete Current Required Read Set embedded in the actual Global State was consumed, including Constitution, Unified Governance 0.0.2, Global State, Working State, Decision Registry `0.0.20`, NSE index, Project Architecture, accepted five-component internal boundaries, Runtime Responsibility Architecture, Foundation readiness, accepted ns_server Batch 1/2/3/4 Global Acceptance evidence, post-Batch-4 remaining-pressure assessment `0.0.4`, `Z2-MDE-014 Runtime Actual-state Ownership Topology`, and the relevant Global Architecture Ledger tail.

Exact upstream evidence additionally consumed for this synthesis includes:

```text
S5 / SV-R01 RCP-23 contribution
→ GLOBAL_ACCEPTED / NORMATIVE UPSTREAM

S7 / SV-R03 RCP-23 contribution
→ GLOBAL_ACCEPTED / NORMATIVE UPSTREAM

RCP-01 Governance Context
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-02 Admission Evidence
→ CLOSED AT DESIGN-SEMANTIC LEVEL

RCP-19 Desired / Applied Configuration
→ CLOSED AT DESIGN-SEMANTIC LEVEL

Shared Foundation Architecture
→ GLOBAL_CLOSED / COMPLETE

Foundation Contract Design
→ GLOBAL_CLOSED / COMPLETE

Foundation Module Design
→ GLOBAL_CLOSED / COMPLETE

Foundation Provider Design
→ GLOBAL_CLOSED / COMPLETE
```

Recovery reconstruction:

```text
Open MDE required for current S10 Batch
→ 0

Unpersisted Owner Decision required for current S10 Batch
→ 0

Blocking Item
→ NONE

Known Working-branch Drift
→ NONE

Current Authorized Phase
→ ns_server Component Internal Design / Batch 5 / S10

Recovery Gate
→ PASS
```

No State / Working State / Decision Registry / Ledger contradiction remains.

---

# 2. Accepted S10 / SV-R06 Baseline

## 2.1 Exact S10 responsibility

```text
S10 Purpose
→ continuously available server-local long-running / time-triggered / background responsibilities intrinsic to ns_server

Owned Product Semantic Authority
→ NONE NEW

SV-R06 Actual-state / Source-fact Ownership
→ server-local Attempt
→ server-local Progress
→ server-local Outcome
→ genuine server-local Source Facts

Same bounded runtime assertion
→ exactly one final Actual-state Owner
```

S10 is therefore a bounded runtime Actual-state/source-fact owner under already accepted `Z2-MDE-014`; this Batch does not decide Runtime Actual-state ownership topology.

## 2.2 Permanent non-collapse

```text
Background Operation
!= Attempt

Operation Identity
!= Attempt Identity

Attempt
!= Progress

Progress
!= Outcome

Retry
!= historical Attempt mutation

Retry / Re-entry
!= same Attempt automatically

S10 Attempt
!= Business Application semantic Runtime state
!= Automation semantic Runtime state
!= Data / Knowledge / ETL semantic Runtime state
!= Node Attempt / Effect
!= Agent Runtime
!= RT Scheduling / Routing / Dispatch

Attempt Success
!= Business / Domain Semantic Success automatically

Provider / Scheduler / Worker technical success
!= S10 semantic success automatically
```

## 2.3 Server-local is a Product Component responsibility property

Work is `server-local` when the bounded execution responsibility required to establish the S10-owned Attempt/progress/outcome assertions remains inside accepted `ns_server` responsibility. It is not defined by process, host, thread, queue, scheduler, database or network locality.

Therefore:

```text
async / delayed / periodic / long-running / continuous
→ does not imply ns_runtime

Foundation network/storage/cache/provider use
→ does not automatically make work cross-component

external source/provider interaction
→ does not transfer external source facts into S10 ownership
```

If another Product Component becomes an actual executor for a bounded part of the work, that part is cross-component and its accepted Runtime Role retains its own Attempt/effect/source-fact ownership.

---

# 3. Accepted RCP-23 Producer Baseline

`RCP-23 — Server-native Runtime Evidence` has exactly the currently accepted server-native producer partitions:

```text
S5 / SV-R01
→ Business Application semantic Runtime Evidence
→ contribution GLOBAL_ACCEPTED

S7 / SV-R03
→ Data / Knowledge / ETL semantic Runtime Evidence
→ contribution GLOBAL_ACCEPTED

S10 / SV-R06
→ server-local Background Attempt / Runtime Evidence
→ contribution AUTHORIZED IN THIS BATCH
```

The first two are normative upstream and are not reopened.

Permanent producer partition non-collapse:

```text
SV-R01 evidence
!= SV-R03 evidence
!= SV-R06 evidence

Server-native Runtime Evidence
!= one universal ns_server Runtime Actual-state

Common evidence semantics
!= common semantic owner
```

The full RCP-23 closure in this Candidate standardizes only the contract-level semantic obligations necessary for consumers to identify, correlate, interpret, qualify and preserve evidence from these separate owners.

---

# 4. S10 Design Principles

1. **Logical work identity precedes technical execution identity.** A Background Operation is a logical server-local work subject. An Attempt is one bounded execution try for that Operation.
2. **Attempt history is append-only in semantic meaning.** Retry, re-entry, recovery and supersession create explicit lineage; they do not rewrite prior Attempt meaning.
3. **Progress and outcome remain source-owned assertions.** Scheduler/worker/provider status is input evidence only and cannot replace SV-R06 interpretation.
4. **Time-trigger semantics are source/temporal semantics, not scheduler identity.** Due/eligible/observed/initiation evidence is representation-neutral and provider-neutral.
5. **Long-running means lifetime independence, not process topology.** Work may outlive the initiating request/session and must retain durable semantic identity/history without requiring a particular daemon/worker model.
6. **Continuous availability is a responsibility requirement, not an exactly-once promise.** Restart, re-entry and reconciliation must preserve history and uncertainty without selecting a universal execution guarantee.
7. **Intervention is three-stage or more.** Requested, accepted/applicable, and achieved outcome remain distinct.
8. **Governance remains applicable to background work.** Server-local, scheduled, automatic or internal execution never bypasses Tenant/Principal/Policy/Trust/Artifact/Admission requirements where they apply.
9. **Desired/Applied/Observed remains permanent.** S9 owns desired state; S10 owns only S10-applied evidence where applicable; projections remain derived.
10. **Unknown and conflict are valid states of knowledge.** Locality, timestamps, restart order and persistence placement never become conflict-winner rules.
11. **Foundation consumption is authority-neutral.** Foundation Contract/Module/Provider semantics supply mechanics only; none becomes S10 Actual-state owner.
12. **RCP-23 unifies evidence obligations, not producer authority.** Full closure must retain three final producer partitions.
13. **Internal Module is architecture-semantic.** Module != Django App != Python package != class != service != process != worker != scheduler != queue != table != database schema != deployment unit.

---

# 5. S10 Internal Responsibility Pressure Map

| Pressure | Stable responsibility required | Principal owner |
|---|---|---|
| Background Operation identity | representation-neutral logical server-local work subject independent of Attempt/process/session | BG01 |
| Source semantic/Definition reference | exact semantic owner/Definition/revision reference where applicable | BG01 |
| Initiation origin | manual/time-triggered/other authorized origin evidence without scheduler identity | BG01/BG02 |
| Operation correlation | operation identity distinct from correlation/trace identity | BG01 |
| Time-trigger due/eligibility semantics | temporal applicability, occurrence/observation/initiation distinction | BG02 |
| Continuous-availability pressure | work identity/history survives caller/session/process lifetime boundaries | BG02/BG06 |
| Long-running semantics | duration/lifetime independence without worker/process topology | BG02 |
| Attempt identity | one bounded semantic execution try independent of worker/job/process IDs | BG03 |
| Operation ↔ Attempt | one Operation may own zero or more Attempts | BG03 |
| Parent/child Attempt | explicit lineage where separately meaningful subordinate execution occurs | BG03 |
| Retry/re-entry/supersession lineage | new Attempt vs same Attempt continuity and explicit relation | BG03/BG05 |
| Duplicate technical invocation | no automatic semantic collapse or exactly-once assumption | BG03/BG05 |
| Pending/running/terminal Attempt state | S10-owned attempt Actual-state meaning | BG03/BG04 |
| Progress | S10-owned bounded progress assertion with temporal/provenance qualification | BG04 |
| Outcome | S10-owned terminal/non-terminal outcome evidence distinct from domain success | BG04 |
| Genuine server-local source facts | exact source-fact producer responsibility and evidence | BG04 |
| Intervention request/applicability | cancel/retry/pause/resume support and request decision where genuinely supported | BG05 |
| Intervention achieved outcome | actual S10 result distinct from request/acceptance | BG05/BG04 |
| Recovery/restart history | operation/attempt identity preservation and re-observation | BG06 |
| UNKNOWN/STALE/PARTIAL/INDETERMINATE/CONFLICTING | first-class qualification, no silent winner | BG06/BG04 |
| RECONCILIATION_PENDING/RECOVERING | explicit recovery state of knowledge/process | BG06 |
| Governance context | Tenant/Principal/Policy/Trust/Artifact/Admission references where applicable | BG07 |
| Applied S10 configuration | exact applied revision/evidence separate from S9 Desired and Observed projection | BG07 |
| Secret reference/redaction boundary | runtime may consume governed reference/material only through accepted custody semantics | BG07/BG04 |
| RCP-23 S10 producer evidence | operation + attempt + lineage + state/outcome + revisions/context/provenance/history | BG01..BG07 |
| Full RCP-23 contract | common consumer/producer obligations across SV-R01/SV-R03/SV-R06 without ownership collapse | stable contract synthesis |

---

# 6. Derived Internal Module Inventory

`BG01..BG07` are document-local navigation labels only. Their stable architecture identity is the responsibility name and semantic meaning.

| Local | Internal Architecture Module | Primary stable responsibility |
|---|---|---|
| BG01 | Background Operation Identity & Initiation Context | logical Operation identity, source semantic/Definition reference, initiation origin, correlation/provenance root |
| BG02 | Time-trigger & Continuous-availability Semantics | time-trigger due/eligibility/origin semantics, long-running and independent-lifetime obligations without scheduler/worker topology |
| BG03 | Attempt Lifecycle & Lineage Custody | Attempt identity, Operation↔Attempt cardinality, parent/child, retry/re-entry/supersession and duplicate-execution lineage |
| BG04 | Progress, Outcome & Server-local Source-fact Custody | S10-owned progress/outcome/source-fact Actual-state, terminal qualification and semantic-success separation |
| BG05 | Intervention & Retry/Re-entry Applicability | cancel/retry/pause/resume request applicability/acceptance, intervention correlation and actual-result separation |
| BG06 | Recovery, Reconciliation & Historical Qualification | restart/recovery/re-entry interpretation, retained history, uncertainty/conflict/reconciliation qualification |
| BG07 | Runtime Governance & Applied Configuration Binding | applicable Tenant/Principal/Policy/Trust/Artifact/Admission/source/config references and S10 Applied evidence |

```text
Derived Internal Module Count
→ 7

Authorized Boundary Coverage
→ S10 / 1 OF 1 / 100%

Unowned S10 Responsibility
→ 0

Duplicate Final Responsibility
→ 0

God Module
→ NONE_FOUND

Overfragmentation
→ NONE_FOUND
```

No internal module is created for a scheduler, worker, queue, broker, daemon, process, thread, timer, database, storage engine, retry engine, cancellation engine, telemetry system or logging subsystem. Those would be physical/provider concerns or accepted Foundation consumption, not S10 semantic responsibility identities.

---

# 7. BG01 — Background Operation Identity & Initiation Context

## 7.1 Background Operation identity

A `Server-local Background Operation` is a stable representation-neutral logical work subject inside S10. It represents one bounded server-local work objective/occurrence whose semantic identity survives technical invocations, process lifetimes and web/SDK sessions.

```text
Background Operation Identity
!= Attempt Identity
!= Correlation / Trace Identity
!= Scheduler Job Identity
!= Queue Message Identity
!= Process / Thread / Worker Identity
!= Database Primary Key automatically
!= Source Definition Identity
```

The physical identifier format is not selected.

## 7.2 Operation semantic context

An Operation preserves, where applicable:

```text
Operation Identity
Source semantic owner reference
Exact source Definition / semantic revision reference
Initiation origin evidence
Initiation applicability context
Tenant / Organization / Principal context as applicable
Policy / Trust evidence references as applicable
Artifact / Admission evidence references where applicable
Managed Desired Configuration revision reference where applicable
Correlation / provenance root
Temporal applicability
Parent Operation / triggering source relationship where applicable
```

The existence of an Operation means only that S10 recognizes a bounded logical server-local work subject. It does not prove Admission, Attempt start, effect or semantic success.

```text
Operation Exists
!= Execution Admitted
!= Attempt Pending automatically
!= Attempt Running
!= Effect
!= Domain Success
```

## 7.3 Operation ↔ Attempt cardinality

```text
One Background Operation
→ MAY have zero Attempts
→ MAY have one Attempt
→ MAY have multiple Attempts
```

Zero Attempts is valid when an Operation is known but no execution try has been established, for example because applicability is not yet satisfied, a retry request is accepted but no retry Attempt has started, or execution becomes unsupported/unavailable before an Attempt is registered.

## 7.4 Operation supersession

Supersession is an explicit semantic relationship, never an implicit latest-wins rule.

```text
Newer Operation
!= older Operation superseded automatically

Latest Timestamp
!= supersession
```

When source semantics or an explicit governed decision establishes supersession, both historical Operations remain interpretable and the superseding relationship is preserved without mutating old Attempt history.

---

# 8. BG02 — Time-trigger & Continuous-availability Semantics

## 8.1 Time-triggered initiation

A time-triggered origin records the semantic reason an initiation became due/eligible; it does not identify a scheduler implementation.

Where applicable, evidence preserves distinctions among:

```text
source schedule / timing semantic revision
intended due / eligibility context
occurrence or eligibility observation time
actual Operation initiation time
Attempt registration/start time
```

```text
Due
!= Operation Initiated

Operation Initiated
!= Attempt Started

Late Observation
!= Late Source Occurrence automatically

Time-triggered
!= Cron
!= APScheduler
!= Celery Beat
!= systemd timer
!= universal Scheduler Authority
```

Manual-triggered and time-triggered origins are distinct provenance categories. Their exact representation is downstream.

A repeated time condition does not itself decide whether a newly observed due occurrence creates a new Operation, correlates to an existing Operation, or is inapplicable. That semantic formation rule follows the applicable source semantic/Definition owner and exact revision.

## 8.2 Long-running semantics

An S10 Operation/Attempt is long-running when its semantic lifetime may exceed the initiating request/session and requires identity, progress/history and recovery semantics independent of that caller lifetime.

```text
Long-running
!= one long-lived process
!= daemon
!= worker pool
!= thread
!= asyncio task
```

## 8.3 Continuous availability

S10 is continuously available as a Product Component responsibility in the sense that background work must remain discoverable/interpretable and capable of recovery/re-entry across ordinary runtime lifecycle boundaries of `ns_server`.

This requirement does not promise:

```text
zero downtime
exactly-once execution
no duplicate technical invocation
no restart
no lost external connectivity
continuous process identity
```

It requires explicit evidence/uncertainty when continuity cannot be established.

---

# 9. BG03 — Attempt Lifecycle & Lineage Custody

## 9.1 Attempt identity

A `Server-local Attempt` is one bounded semantic execution try owned by SV-R06 for one Background Operation.

```text
Attempt Identity
!= Operation Identity
!= Scheduler/Worker/Process/Thread/Queue ID
!= Provider invocation ID
!= Correlation identity
```

The physical identifier representation is not selected.

An Attempt may be established in a pending state before active execution is proven. This preserves:

```text
Retry Accepted
!= Retry Attempt Started

Attempt Registered / Pending
!= Running
```

## 9.2 Attempt state meaning

S10 owns the semantic meaning of its own Attempt assertions. Architecture-level state classes include, where applicable:

```text
PENDING
→ distinct Attempt exists but active execution is not yet established

RUNNING
→ admissible S10-owned evidence establishes active execution

COMPLETED
→ execution try reached a terminal completion boundary with outcome evidence

FAILED
→ execution try reached a terminal failure boundary under S10 semantics
```

Additional terminal/intervention states such as cancelled may exist only where the relevant operation supports them. Pause/resume is not universally assumed.

These state meanings are not a universal physical state machine and do not freeze transition tables or implementation enums.

## 9.3 Retry semantics

```text
Retry Intent
!= Retry Accepted
!= Retry Attempt Registered
!= Retry Attempt Started
!= Retry Attempt Outcome
```

For an S10 semantic retry of an existing Operation:

- prior Attempt history is immutable in semantic meaning;
- an accepted retry never converts the prior Attempt back to pending/running;
- when a retry execution try is established, it receives a new Attempt identity;
- the new Attempt preserves an explicit `retry-of` lineage to the applicable prior Attempt(s);
- retry does not create exactly-once or latest-attempt-wins semantics.

## 9.4 Re-entry semantics

Re-entry means execution participation returns after interruption, restart, disconnection or another lifecycle boundary. It does not automatically mean either same Attempt or new Attempt.

```text
Re-entry
→ same Attempt ONLY when continuity evidence proves the same bounded execution try remains valid

Re-entry with a new execution try
→ new Attempt identity + explicit re-entry lineage

Continuity not provable
→ UNKNOWN / INDETERMINATE / RECONCILIATION_PENDING as applicable
```

## 9.5 Parent / child Attempt relationship

Where a single Background Operation contains separately stateful subordinate server-local execution tries, child Attempts receive independent Attempt identity and an explicit parent-Attempt relationship.

If subordinate work is independently meaningful as a separate logical work objective, it is a separate Background Operation and may carry an Operation-parent/correlation relation rather than being forced into an Attempt-only hierarchy.

## 9.6 Duplicate technical invocation

```text
Duplicate technical invocation
!= same semantic Attempt automatically
!= new semantic Attempt automatically
```

A technical invocation may be associated with an existing Attempt only when admissible identity/lineage evidence establishes that it is part of the same bounded execution try. If an independent execution try was established, it is a new Attempt. If evidence is insufficient or contradictory, S10 preserves `INDETERMINATE`/`CONFLICTING` qualification instead of silently collapsing records.

No exactly-once, at-most-once or at-least-once execution guarantee is established.

---

# 10. BG04 — Progress, Outcome & Server-local Source-fact Custody

## 10.1 Progress

Progress is an S10-owned bounded assertion about advancement of an S10 Attempt. It is always scoped to an Attempt and may include structured or coarse progress semantics defined by the applicable Operation class/source semantics.

```text
Progress
!= Attempt Identity
!= Provider heartbeat
!= Scheduler state
!= Business / Domain semantic result
```

Progress evidence preserves provenance and temporal qualification. Missing recent progress may mean `STALE`, `UNKNOWN` or `UNAVAILABLE`; it is not automatically Attempt failure.

## 10.2 Outcome

Outcome is S10's semantic conclusion for its own bounded Attempt assertion.

```text
Attempt Completed
!= Attempt Succeeded automatically

Attempt Success
!= Business Application Success
!= Automation Success
!= Data / ETL Semantic Success
!= Agent Success
!= Notification Success
```

Where S10 can establish success/failure/partial/cancelled or another supported outcome, it owns only that server-local Attempt interpretation.

## 10.3 Genuine server-local source facts

S10 final source-fact ownership is restricted to facts genuinely originating inside its accepted responsibility, including where applicable:

```text
Attempt registered / running / terminal state
S10-owned progress observation
S10-owned intervention achievement
S10-owned applied configuration evidence for its runtime partition
S10-owned local outcome/result evidence
S10 recovery/re-entry/reconciliation facts for its own partition
```

External enterprise source facts, provider-native facts, S5/S7 semantic results, Node effects and RT coordination facts remain with their accepted owners.

## 10.4 Provider/worker/scheduler evidence boundary

Technical evidence may be consumed as input, but:

```text
Provider invocation success
!= S10 Attempt semantic success automatically

Worker technical completion
!= S10 semantic completion automatically

Scheduler dispatch/due evidence
!= Attempt started automatically

Storage persistence success
!= Attempt semantic success automatically
```

The BG04 interpretation is bounded to S10 and cannot elevate an underlying external/provider assertion into another domain's truth.

---

# 11. BG05 — Intervention & Retry/Re-entry Applicability

S10 supports architecture semantics for governed intervention requests only when the specific Operation/Attempt declares the capability as supported/applicable.

Possible intervention classes include:

```text
cancel
retry
pause
resume
recovery / re-entry request
```

No class is universally supported merely because this contract can describe it.

Permanent distinction:

```text
Intervention Requested
!= Intervention Applicable
!= Intervention Accepted
!= Intervention Action Started
!= Intervention Achieved
!= Effects Reversed
```

## 11.1 Cancel

A cancel request is correlated to the exact Operation/Attempt target and evaluated for support/applicability. If accepted, actual cancellation is established only by S10-owned outcome evidence.

```text
Cancel Accepted
!= Cancelled

Cancelled
!= Rollback
!= Compensation
!= prior effects reversed
```

## 11.2 Retry

Retry applicability is evaluated against exact historical Attempt and current Operation context. Acceptance creates no retroactive mutation. A retry Attempt is new when registered/started, with explicit lineage.

## 11.3 Pause / resume

Pause/resume semantics exist only for Operation classes that explicitly support them. A request against an unsupported or inapplicable Attempt remains `UNSUPPORTED` or applicable qualified status; no universal pausing mechanism is invented.

## 11.4 Cross-component intervention

If intervention affects only server-local S10 work, S10 handles and owns its own intervention outcome without requiring RT-R03.

If intervention must cross Product Components:

```text
request intent
→ RT-R03 coordination where applicable
→ remote actual owner determines its own final reaction/outcome
```

RT-R03 coordination-stage state never replaces S10 or remote source-owner final outcome.

---

# 12. BG06 — Recovery, Reconciliation & Historical Qualification

## 12.1 History survives technical lifecycle boundaries

Operation and Attempt semantic identity/history must remain interpretable across restart/recovery. No persistence technology is selected; semantic retention is the requirement.

Historical evidence preserves where applicable:

```text
Operation Identity
Attempt Identity
parent/child/retry/re-entry/supersession lineage
source semantic / Definition revision
Governance / Admission references
Applied configuration revision(s)
progress/outcome evidence
intervention request/decision/outcome evidence
correlation/provenance
temporal qualification
```

Current state never silently rewrites historical state.

## 12.2 Recovery state

After restart or loss of reliable observation, an active/non-terminal Attempt may be qualified as:

```text
RECOVERING
UNKNOWN
STALE
INDETERMINATE
CONFLICTING
RECONCILIATION_PENDING
UNAVAILABLE
```

as the evidence requires.

`RECOVERING` indicates active recovery/re-observation effort for the S10 partition; it is not proof that the prior Attempt is still running or that reconciliation succeeded.

## 12.3 Reconnect / reconciliation

```text
Reconnect
!= Reconciled

Recovery
!= Authority Transfer

Replay
!= Retroactive Authorization

Local Persistence
!= Actual-state Ownership by placement

Latest Timestamp
!= Canonical Winner
```

Reconciliation determines the best currently admissible interpretation under existing ownership and source evidence. If evidence remains contradictory or incomplete, the result remains explicit `CONFLICTING`/`INDETERMINATE`/`RECONCILIATION_PENDING` rather than selecting local-wins, central-wins or latest-wins.

## 12.4 Same Attempt after restart

The same Attempt identity may continue after restart only when retained/recovered evidence can establish continuity of the same bounded execution try. Otherwise a newly established execution try receives a new Attempt identity and explicit re-entry/recovery lineage.

---

# 13. Failure / Unknown / Partial Semantic Model

S10 applies the accepted project-wide uncertainty vocabulary to its own bounded subjects.

| Condition | S10 interpretation |
|---|---|
| `UNKNOWN` | admissible evidence cannot currently establish the required S10 assertion |
| `UNAVAILABLE` | required local/provider/source capability or evidence path cannot currently serve the S10 operation |
| `STALE` | known S10 evidence is not known to satisfy applicable freshness requirements |
| `PARTIAL` | only a subset of expected progress/result/evidence is established; not equivalent to success or failure |
| `INDETERMINATE` | evidence is insufficient/ambiguous/context-incomplete for a required S10 conclusion |
| `CONFLICTING` | relevant S10 observations/evidence cannot be simultaneously accepted under current interpretation |
| `RECONCILIATION_PENDING` | recovery/reconnect evidence exists but final S10 reconciliation is incomplete |
| `RECOVERING` | S10 is actively recovering/re-observing its own partition; final current-state interpretation not yet established |

These conditions may qualify Operation, Attempt, progress/outcome, intervention or applied-configuration evidence as appropriate. They are not a universal domain state machine.

No fail-open/fail-closed default is selected.

---

# 14. BG07 — Runtime Governance & Applied Configuration Binding

## 14.1 Governance applicability

Background work does not bypass governance because it is internal, automatic, scheduled or server-local.

Where the source Operation class requires them, S10 preserves references/applicability for:

```text
Tenant
Organization
Principal / IAM
Policy
Trust
Artifact Acceptance
Execution Admission
Source semantic / Definition revision
Managed Configuration revision
```

Permanent lifecycle separation:

```text
Authentication
!= Policy Permit

Policy Permit
!= Execution Admission

Admission
!= Attempt Registered
!= Attempt Started
!= Effect

Attempt Success
!= domain semantic success
```

Whether Formal Admission is required for a specific server-local Operation follows accepted source lifecycle/governance semantics; S10 neither bypasses Admission nor invents universal Admission for cases already defined as not applicable.

## 14.2 Desired / Applied / Observed

```text
Managed Desired Configuration
→ S9 / ns_server

Configuration item semantic meaning
→ applicable configured-capability owner

S10 Applied Runtime Evidence
→ S10 / SV-R06 for its bounded partition where applicable

Observed projection
→ derived consumer/UI state
```

```text
Desired
!= Distributed
!= Applied
!= Observed
```

An Operation/Attempt retains exact applied configuration revision/evidence needed to interpret its historical behavior. Current Desired state does not rewrite historical Applied evidence.

If configuration changes while an Attempt is active, the design does not assume atomic rollout or automatic mid-Attempt adoption. The S10 evidence must preserve what applicability/revision can actually be established; partial/unknown/conflicting application remains explicit.

## 14.3 Secret boundary

```text
Configuration
!= Secret Material

Secret Reference
!= Secret Material
```

S10 may consume Secret References/material only under already accepted custody, Policy/Trust and redaction semantics. Diagnostic/progress/outcome evidence must not disclose protected material merely because it is S10-owned evidence.

---

# 15. Server-local vs Cross-component Execution Boundary

## 15.1 Pure server-local path

```text
S10 source intent / Operation
→ applicable S8 / SV-R04 Admission where required
→ S10 Attempt
→ S10 progress / outcome / source facts
```

`ns_runtime` is not inserted merely because work is delayed, asynchronous, periodic, long-running or continuously available.

## 15.2 Cross-component path

When actual execution responsibility crosses another Product Component:

```text
applicable source intent
→ S8 / SV-R04 Admission where required
→ RT-R02 Scheduling / Routing / Dispatch where applicable
→ RT-R03 continuation/intervention coordination where applicable
→ remote executor owns its Attempt / Effect / source facts
→ S10 retains only its own source/coordination relationship facts
```

S10 may correlate remote evidence to a server-local Operation but cannot absorb the remote owner's Actual-state by aggregation.

## 15.3 Exact RT-R02 / RT-R03 need

`RT-R02` is required only when cross-component scheduling/routing/dispatch coordination is genuinely required.

`RT-R03` is required only when a cross-component continuation/delegation/intervention coordination stage is genuinely required.

Neither is a mandatory dependency for pure server-local S10 work.

---

# 16. RCP-23 S10 / SV-R06 Producer Contribution

This Candidate closes the S10 producer contribution at the current design-semantic level.

## 16.1 Required S10 evidence semantics

An S10/SV-R06 producer can provide, where applicable:

```text
Producer partition identity / responsibility reference
Background Operation identity
Attempt identity
Operation ↔ Attempt relationship
parent/child Attempt relationship
retry/re-entry/supersession lineage
source semantic owner / exact Definition revision reference
manual/time-triggered/other initiation origin evidence
Governance / Admission evidence references
Managed Desired configuration reference
S10 Applied configuration evidence/revision
S10 progress
S10 outcome
S10 genuine source facts
intervention request / applicability / acceptance / outcome evidence
correlation / provenance
occurrence / observation / applicability temporal evidence
history
UNKNOWN / STALE / PARTIAL / INDETERMINATE / CONFLICTING / RECONCILIATION_PENDING / RECOVERING qualification
private/offline qualification
compatibility/conformance evidence
```

No physical field/schema/envelope is selected.

## 16.2 Producer obligations

S10 producer MUST:

- identify its own semantic partition and bounded assertion;
- keep Operation and Attempt identity distinct;
- preserve attempt lineage rather than mutating history;
- preserve exact source semantic/Definition and governance/config applicability where required;
- distinguish progress from outcome and technical evidence from S10 semantic result;
- qualify uncertainty/freshness/recovery explicitly;
- preserve private/offline usability without requiring public SaaS;
- avoid representing RT/Node/Agent/S5/S7 facts as S10-owned assertions.

S10 producer MUST NOT:

- infer success from worker/scheduler/provider completion alone;
- silently collapse duplicate technical invocations;
- create an exactly-once implication;
- use latest timestamp as conflict winner;
- treat persistence placement as Actual-state ownership;
- convert cross-component evidence into universal server Actual-state.

## 16.3 Consumer obligations

Consumers MUST preserve S10 producer partition, Operation/Attempt lineage, source revision/governance/config references and uncertainty qualifications. Consumers may project or aggregate S10 evidence but do not become its final Actual-state owner.

---

# 17. Full RCP-23 Server-native Runtime Evidence Closure

The full RCP-23 contract is closed at the current design-semantic level using the three accepted producer partitions.

## 17.1 Stable semantic subject

`Server-native Runtime Evidence` is the stable cross-consumer semantic contract for evidence produced by native `ns_server` runtime participants whose bounded Actual-state is owned by `SV-R01`, `SV-R03` or `SV-R06`.

It is not a universal server runtime state object and not a single owner.

## 17.2 Common evidence obligations

Every producer partition preserves the following common categories as applicable:

```text
Producer Partition / Semantic Owner Reference
Operation Identity
Exact producer-specific source semantic / Definition revision references
Owned Runtime State / Result / Outcome assertion
Governance / Admission references where applicable
Configuration applicability references where applicable
Correlation / Provenance
Temporal applicability / observation / freshness
Historical references / lineage
Unknown / Stale / Partial / Indeterminate / Conflicting / Reconciliation qualification
Compatibility / Conformance qualification
Private / Offline qualification
```

Producer-specific additions remain separate:

```text
SV-R01 / S5
→ Business Application semantic runtime state/result
→ exact Business Application Definition revision
→ resolved dependency evidence

SV-R03 / S7
→ S7 semantic runtime state/result
→ exact Native S7 Definition / factual-SoT-binding / Mapping / ETL / Knowledge / Query revisions as applicable
→ source/source-owner/freshness/derived-output lineage

SV-R06 / S10
→ Background Operation + Attempt identity
→ retry/re-entry/parent-child/supersession lineage
→ S10 progress/outcome/source facts
→ S10 intervention/recovery/applied-config evidence
```

## 17.3 Attempt is not universalized

RCP-23 does not force S5/SV-R01 or S7/SV-R03 to adopt S10 Attempt semantics.

```text
Operation Identity
→ common contract pressure

Attempt Identity
→ mandatory for S10/SV-R06
→ other producer-specific attempt/source evidence only where already accepted by that producer
```

This preserves accepted S5/S7 internal models rather than reopening them.

## 17.4 Common identity / correlation rule

Operation identity is scoped by the originating producer semantic partition unless explicit cross-partition correlation evidence relates separate operations.

```text
Operation Identity
!= Correlation Identity

Same correlation
!= same Operation automatically

Same Operation-looking value across producer partitions
!= semantic identity equality automatically
```

No UUID/global numeric namespace is selected.

## 17.5 Common consumer non-collapse

A consumer of RCP-23 MUST NOT:

```text
merge SV-R01/SV-R03/SV-R06 into one final Runtime Actual-state owner
infer Business/Data/S10 semantic success from another partition's success
infer source truth from projection/aggregation
replace historical revisions with current revisions
select latest timestamp as conflict winner
convert UNKNOWN/STALE/PARTIAL into success/failure without owner semantics
infer Admission from Attempt evidence
infer Attempt from Dispatch evidence
infer effect from Attempt success
```

## 17.6 Closure result

```text
RCP-23 S5 / SV-R01 contribution
→ CONSUMED AS GLOBAL_ACCEPTED NORMATIVE UPSTREAM

RCP-23 S7 / SV-R03 contribution
→ CONSUMED AS GLOBAL_ACCEPTED NORMATIVE UPSTREAM

RCP-23 S10 / SV-R06 contribution
→ CLOSED AT CURRENT DESIGN LEVEL BY THIS CANDIDATE

RCP-23 Full Server-native Runtime Evidence
→ CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL BY THIS CANDIDATE

Universal Server Runtime Actual-state Owner Created
→ NO

S5 Internals Reopened
→ NO

S7 Internals Reopened
→ NO
```

This closure remains candidate evidence until independent GAC acceptance.

---

# 18. Internal Dependency Semantics

The accepted ns_server Component Internal Design dependency taxonomy is reused unchanged:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only `SDD` participates in recursive hard semantic-definition cycle analysis.

Hard SDD graph:

```text
BG02 → BG01
BG07 → BG01
BG03 → BG01, BG07
BG04 → BG03
BG05 → BG01, BG03, BG04
BG06 → BG01, BG03, BG04, BG05, BG07
```

Time-trigger evidence into BG03/BG04 is application/evidence linkage where applicable rather than a universal hard dependency on BG02. Governance/Admission decisions are ACD/EL to accepted S1-S4/S8 semantics, not internal S10 Authority edges. Historical references are HPL. Provider/source technical evidence is XED where the producer is external to S10 ownership.

```text
Hard Internal SDD Graph
→ ACYCLIC

Unresolved Hard Semantic-definition Cycle
→ 0

Authority Cycle
→ NONE
```

This graph is not a process graph, scheduler graph, queue graph, call graph, import graph or runtime DAG.

---

# 19. Shared Foundation Consumption

S10 consumes only accepted Foundation semantics through:

```text
Product Component Internal Responsibility
→ Stable Entry
→ Foundation Contract
→ Foundation Module
→ Provider Family where provider-bearing
→ replaceable realization
```

Applicable accepted Foundation contracts include, only where their subjects apply:

| Foundation semantic | S10 use | Authority-neutrality rule |
|---|---|---|
| C01 Bootstrap Configuration Acquisition | component-local bootstrap acquisition where needed | loader/source never becomes S9 desired-state Authority or S10 Actual-state owner |
| C02 Diagnostic Occurrence & Delivery Evidence | S10 diagnostics with provenance/correlation/redaction | log/sink success != Attempt success; logs != source truth automatically |
| C03 Technical Observation & Health Evidence | technical health/observation evidence | telemetry/collector != Runtime Actual-state owner |
| C04 Temporal & Freshness | due/eligibility/deadline/freshness/staleness/clock uncertainty | time source != scheduler/authority/conflict winner |
| C05 Operation Correlation & Provenance Context | Operation/Attempt/intervention/recovery lineage | correlation possession != operation ownership or Authority |
| C06 Representation & Serialization | representation-neutral contract realization | representation != semantic identity |
| C09 Durable Storage Access Mechanics | durable evidence/history mechanics where realization requires it | storage placement != SoT/Actual-state ownership; persistence success != semantic success |
| C10 Technical Status & Uncertainty | common technical uncertainty vocabulary | common status != universal S10/domain state machine |
| C11 Governed Context Propagation | Tenant/Org/Principal/Policy/Trust reference carriage | context presence != auth/authz/trust |
| C12/C13 Secret Reference / Redaction | reference/material separation and protected evidence disclosure | Foundation != Trust/Policy/secret Authority |
| C14 Compatibility & Conformance | reusable comparison/evidence mechanics | final semantic compatibility judgement remains S10/source owner |

Provider-bearing paths may use already accepted Provider Families such as configuration source, diagnostic sink, observation sink, temporal source, durable storage backend or secret-material resolution only when the chosen realization actually needs them. No Provider is mandatory by architecture identity and no public SaaS/provider is a core-correctness dependency.

```text
Foundation != S10 Authority
Provider != S10 Authority
Scheduler / Queue / Storage Provider != Runtime Actual-state Owner
Provider Success != S10 Semantic Success automatically
```

Deferred Foundation candidates remain deferred. This Batch establishes no missing new Foundation capability.

---

# 20. Offline / Private Correctness

S10 core correctness remains valid in private, isolated and fully offline deployments.

It does not require:

```text
public scheduler SaaS
public queue/broker
public control plane
public monitoring service
public registry
public time SaaS
```

Retained offline evidence preserves exact Operation/Attempt identity, provenance, source revision and governance/config applicability available at the time.

```text
Offline retained evidence
!= new Authority
!= retroactive Admission
!= automatic reconciliation
```

A private authoritative `ns_server` deployment may exercise S10 normally. Disconnection from optional external systems/providers does not transfer their factual authority into S10.

No material offline fail-open/fail-closed policy is created.

---

# 21. Compatibility / Migration / Conformance

## 21.1 Compatibility

S10 semantic compatibility considers, where applicable:

```text
Operation identity meaning
Attempt identity/lineage meaning
state/progress/outcome meaning
intervention semantics
source semantic/Definition references
governance/admission applicability
configuration applicability
uncertainty meanings
historical interpretation
RCP-23 producer obligations
```

```text
Version bump
!= compatibility automatically

Schema readability
!= semantic compatibility

Provider replacement
!= semantic change automatically
```

Unsupported/incompatible producer semantics remain explicit rather than silently coerced.

## 21.2 Migration

Migration of S10 evidence must preserve Operation/Attempt identity and lineage or explicitly map old/new semantic identity. Copying rows/files/records is not semantic migration completion.

A provider/storage/process replacement does not create new Operation/Attempt identities merely because implementation changes, unless the semantic execution lifecycle actually establishes a new Attempt.

Any migration that changes Actual-state ownership, stable identity semantics materially or major historical interpretation returns to GAC/MDE classification.

## 21.3 Conformance

Conformance must prove at least:

- Operation/Attempt non-collapse;
- one final owner for same S10 bounded assertion;
- history immutability in semantic meaning;
- retry/re-entry lineage;
- request/accepted/achieved intervention separation;
- explicit uncertainty/recovery semantics;
- Desired/Applied/Observed separation;
- server-local vs cross-component boundary;
- RCP-23 producer partition preservation;
- private/offline correctness;
- Foundation/provider authority neutrality.

No conformance tooling is selected.

---

# 22. Semantic Resolution Matrix

| Dimension | S10 / RCP-23 resolution | Status |
|---|---|---|
| Identity / Namespace | Operation and Attempt are distinct representation-neutral semantic identities; correlation and technical IDs remain separate | `CLOSED` |
| Revision / Evolution | exact source Definition/semantic/config revisions preserved where applicable; history not rewritten by current state | `CLOSED` |
| Authority | no new Product semantic Authority; existing Tenant/IAM/Policy/Trust/Artifact/Admission authorities preserved | `CLOSED` |
| Semantic Ownership | S10 owns only server-local background Actual-state/source facts; domain semantic success remains owner-specific | `CLOSED` |
| Source of Truth | persistence/provider placement creates no new SoT; external/source facts retain accepted owners | `CLOSED` |
| Actual-state Ownership | SV-R06 final owner for S10 bounded Attempt/progress/outcome/source facts; one final owner per assertion | `CLOSED` |
| State / Lifecycle | Operation != Attempt != progress != outcome; pending/running/terminal semantics bounded to S10 | `CLOSED` |
| Temporal Semantics | due/eligibility/observation/initiation/attempt times distinct; latest timestamp not winner | `CLOSED` |
| Failure / Unknown / Indeterminate | UNKNOWN/UNAVAILABLE/STALE/PARTIAL/INDETERMINATE/CONFLICTING/RECONCILIATION_PENDING/RECOVERING explicit | `CLOSED` |
| Tenant | governed context consumed where applicable; server-local never means Tenant bypass | `CLOSED` |
| Organization | preserved distinct from Tenant; propagated where applicable | `CLOSED` |
| Principal / IAM | consumed from accepted governance; internal/background execution does not create Principal Authority | `CLOSED` |
| Authentication | authentication evidence remains distinct from authorization/admission | `CLOSED` |
| Authorization / Policy | Policy Permit != Admission != Attempt; S10 consumes applicable decisions | `CLOSED` |
| Security / Trust | Trust remains S4/ns_server authority; provider/local success never becomes Trust | `CLOSED` |
| Data / Privacy / Trust | evidence disclosure/redaction and external source ownership preserved | `CLOSED` |
| Configuration | S9 Desired; S10 Applied for its partition; Observed derived | `CLOSED` |
| Secret Reference / Material | separated; accepted Foundation/custody semantics consumed | `CLOSED / NAMED FOUNDATION` |
| Serialization / Representation | stable semantics representation-neutral; no API/message/schema frozen | `CLOSED / DOWNSTREAM REALIZATION` |
| Offline / Degraded | private/offline core correctness; retained evidence no authority escalation | `CLOSED` |
| Recovery / Reconciliation | restart/re-entry history, explicit recovery qualification; no authority transfer/winner rule | `CLOSED` |
| Compatibility | semantic-first; unsupported/incompatible explicit | `CLOSED` |
| Migration | identity/lineage/history-preserving; ownership changes revalidate | `CLOSED` |
| Conformance | producer/consumer and non-collapse obligations explicit | `CLOSED` |
| Cross-boundary Dependency | pure S10 local path vs S8/RT/remote executor path explicit | `CLOSED` |
| Invariant | actual-state ownership, governance, offline, RCP-23 partition non-collapse preserved | `CLOSED` |
| Decision Traceability | derived from GAC-EPOCH-0057 + accepted S5/S7/Runtime/Foundation evidence | `CLOSED` |
| Revalidation Trigger | MDE/authority/identity/compatibility/provider-lock-in triggers named | `CLOSED` |

```text
Missing/Ambiguous Normative Dimension
→ 0

Unnamed Deferral
→ 0

Implementation-defined Semantic Escape
→ 0
```

---

# 23. Explicit Non-goals / Named Downstream Deferrals

This Candidate does not design or select:

```text
S11 / S12 / S13 internals
ns_runtime / ns_node / ns_agent / ns_web internals
full RCP-16
full RCP-17
RCP-18
RCP-21
System-level SDK Detailed Design

Celery / APScheduler / cron / systemd timer
worker / daemon / process / thread / coroutine topology
queue / broker / topic / message bus
exactly-once / at-most-once / at-least-once execution guarantee
universal retry / cancellation / pause/resume / rollback / compensation engine
reconciliation conflict-winner algorithm
local-wins / central-wins / latest-wins

REST / RPC / gRPC / WebSocket API
message envelope / DTO / schema
UUID / numeric PK / task ID / queue ID / PID / worker ID / scheduler-job ID format
database / table / ORM / storage layout
Provider / Vendor / Library selection
Django App / Python package / class / repository layout
Implementation Planning / IWP / Coding
```

Named downstream realization freedom remains only for physical identifier representation, persistence technology/schema, execution/scheduler/worker/process realization, concurrency/backpressure mechanics, concrete API/serialization, Provider binding and implementation layout, all constrained by this accepted-semantic candidate if globally accepted.

---

# 24. Revalidation / MDE Stop Triggers

This Candidate requires return to GAC / Project Owner before any later design materially changes or establishes:

```text
Runtime Actual-state ownership topology
S10 / SV-R06 source-fact ownership
Product Component topology
Admission / Policy / IAM / Trust / Tenant Authority
universal Scheduler or Worker semantic Authority
exactly-once / deterministic replay / rollback guarantee
material global retry or cancellation policy
material fail-open / fail-closed policy
conflict-winner rule
major stable Operation/Attempt identity commitment beyond representation-neutral semantics
major externally observable compatibility/history guarantee
provider/protocol/framework/storage lock-in
high migration-cost commitment
new Product capability
```

If classification is uncertain:

```text
DEFAULT
→ MDE
```

---

# 25. Candidate Completion State

```text
Fresh Repository Recovery
→ PASS

Authorized Boundary Coverage
→ S10 / 1 OF 1 / 100%

Derived Internal Modules
→ 7

Unowned S10 Responsibility
→ 0

Duplicate Final Responsibility
→ 0

Hard Internal SDD Graph
→ ACYCLIC

Actual-state Ownership Ambiguity
→ 0

Operation / Attempt Collapse
→ 0

Retry / Re-entry Historical Mutation
→ 0

Scheduler / Worker Authority Conflation
→ 0

Server-local / ns_runtime Conflation
→ 0

Intervention Request / Outcome Collapse
→ 0

RCP-23 S10 / SV-R06 Contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-23 Full Server-native Runtime Evidence
→ CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL

S5 Internals Reopened
→ 0

S7 Internals Reopened
→ 0

Universal Server Runtime Actual-state Owner Created
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Missing/Ambiguous Normative Dimension
→ 0

Implementation-defined Escape
→ 0

Unauthorized Downstream Design Leakage
→ 0
```

Candidate state:

```text
NGRP-001
Component Internal Design
/ ns_server
/ Batch 5
/ S10 Server-local Background Work & Server Actual-state

→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This Candidate does not self-accept, does not advance GAC Epoch, does not declare `ns_server` Internal Design Exhaustion/global completion, does not authorize S11/S12/S13 or another Product Component, and does not authorize SDK Detailed Design, Design-to-Implementation Readiness, Implementation Planning, IWP or coding.
