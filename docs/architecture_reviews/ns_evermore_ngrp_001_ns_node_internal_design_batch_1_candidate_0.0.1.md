# NGRP-001 — Component Internal Design / ns_node / Batch 1 Candidate

## Authority Metadata

- **Program / Phase:** `NGRP-001 — Component Internal Design / ns_node / Batch 1`
- **Authorization Scope:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_NODE / BATCH_1 / LOCAL_READINESS_GOVERNED_EXECUTION_PROTECTED_EFFECT_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Producing Entry HEAD:** `70f79436359b03e49f2a31d1a8f5144af52ada34`
- **Recovered GAC Epoch:** `GAC-EPOCH-0081`
- **State Verified Through HEAD:** `de2644d3362602e3df8a7d89a96267dc50c219d2`
- **Decision Registry:** `0.0.29 / CURRENT / NORMATIVE`
- **Authorization Transition:** `GAC-TR-0091`
- **Authorized Boundaries:** `N1 / N2 / N3`
- **Inherited Runtime Roles:** `ND-R01 / ND-R02 / ND-R03`
- **Candidate Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Global Acceptance Authority:** `NOT HELD`
- **N4 / Batch 2 Authorization:** `NONE`

This Candidate performs only architecture-semantic internal design for `ns_node` boundaries N1, N2 and N3. It does not design N4/ND-R04, recovery/reconciliation algorithms, another Product Component, System-level SDK Detailed Design, process/service/worker/session/browser-profile/deployment topology, persistence technology, API/wire representation, implementation planning, IWP or code.

---

# 1. Fresh Repository Recovery

Fresh remote recovery was completed before design.

```text
Actual remote Branch HEAD at producing entry
→ 70f79436359b03e49f2a31d1a8f5144af52ada34

Current GAC Epoch
→ GAC-EPOCH-0081

State Verified Through HEAD
→ de2644d3362602e3df8a7d89a96267dc50c219d2

State-to-HEAD Delta
→ exactly 1 commit
→ Global Architecture State authorization seal only
→ parent = de2644d3362602e3df8a7d89a96267dc50c219d2

Delta Classification
→ EXPECTED_GOVERNANCE

Decision Registry
→ 0.0.29 / CURRENT / NORMATIVE

Current Authorized Phase
→ exact ns_node Batch 1 match

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

Ledger continuity was recovered through:

```text
GAC-TR-0088
→ ns_runtime internal-design exhaustion / global-closure eligibility

GAC-TR-0089
→ ns_runtime Component Internal Design global closure

GAC-TR-0090
→ next-component sequencing / ns_node entry-readiness assessment

GAC-TR-0091
→ separate explicit ns_node Component Internal Design / Batch 1 authorization
```

The complete Mandatory Read Set named by the authorization was consumed. Directly intersecting accepted producer-side contracts were additionally consumed for S8/RCP-02 Admission Evidence, S9/RCP-19 Desired/Applied Configuration, R1/RCP-03 Presence, R2/RCP-05 Dispatch Evidence, R3 intervention/continuation coordination, and S6 Automation continuation/composition semantics. Applicable accepted Shared Foundation semantics were also consumed. No Repository contradiction or MDE stop condition was found.

---

# 2. Preserved Accepted Upstream Baseline

```text
ns_server Component Internal Design
→ GLOBAL_CLOSED / COMPLETE

ns_runtime Component Internal Design
→ GLOBAL_CLOSED / COMPLETE

Shared Foundation Architecture / Contract / Module / Provider
→ GLOBAL_CLOSED / COMPLETE

Runtime Responsibility Architecture
→ GLOBAL_CLOSED / COMPLETE
```

Primary upstream ownership preserved:

```text
Tenant / Principal / Policy / Trust authorities
→ ns_server accepted owners

Formal Artifact Acceptance
→ ns_server / S8

Formal Execution Admission
→ ns_server / S8 / SV-R04

Managed Runtime Desired Configuration
→ ns_server / S9 / SV-R05

Presence / Reachability Coordination
→ ns_runtime / R1 / RT-R01

Routing / Scheduling / Dispatch
→ ns_runtime / R2 / RT-R02

Continuation / Delegation / Intervention Coordination
→ ns_runtime / R3 / RT-R03

Recovery / Reconciliation Coordination
→ ns_runtime / R4 / RT-R04

Automation semantic continuation / composition
→ ns_server / S6 / SV-R02
```

Node ownership remains bounded to:

```text
N1 / ND-R01
→ Node-local capability / readiness / Applied Configuration Actual-state

N2 / ND-R02
→ Node-local execution Attempt Actual-state

N3 / ND-R03
→ protected local Effect / Node-origin source-fact evidence
```

Permanent non-collapse:

```text
Authority != Execution
Connected != Trusted != Admitted
Reachable != Ready
Installed != Accepted
Available != Admitted
Activated != Authorized
User Session != IAM Authority
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Dispatch != Attempt
Attempt != Protected Effect
Attempt Success != Protected Effect automatically
Protected Effect != Business Semantic Success automatically
Stopped != Effects Reversed
Local Source Fact != broader domain truth
Reference != Authority
Correlation != Ownership
Desired != Distributed != Applied != Observed
```

---

# 3. Authorized Boundary and Contract Scope

## 3.1 Authorized internal boundaries

```text
N1 — Local Capability, Readiness & Applied Configuration
→ ND-R01 Node Capability & Readiness Participant

N2 — Governed Local Execution
→ ND-R02 Governed Local Execution Participant

N3 — Protected Local Effect & Source-fact Custody
→ ND-R03 Protected Local Effect Custodian
```

Explicitly not authorized:

```text
N4 — Offline Continuity, Recovery & Local Diagnostics
ND-R04 — Node Offline Continuity & Recovery Participant
```

N4 appears only as a future consumer of non-destructive N1/N2/N3 evidence. No Node recovery decomposition, reconciliation architecture, re-observation algorithm, recovery state machine, conflict winner, replay algorithm or comprehensive Node diagnostics architecture is designed here.

## 3.2 Stable-contract scope

```text
RCP-04 Node Readiness
→ ND-R01 owner/source-side semantic closure + representation-neutral stable contract synthesis
→ Full Cross-component Closure NOT CLAIMED

RCP-07 Node Attempt
→ ND-R02 owner/source-side semantic closure + representation-neutral stable contract synthesis
→ Full Cross-component Closure NOT CLAIMED BY INFERENCE

RCP-08 Node Effect Evidence
→ ND-R03 owner/source-side semantic closure + representation-neutral stable contract synthesis
→ Full Cross-component Closure NOT CLAIMED BY INFERENCE
```

Authorized bounded refinements only:

```text
RCP-02 → Node executor consumer-side Admission-evidence applicability
RCP-03 → Node participant-side readiness/presence correlation contribution where material
RCP-05 → Node executor consumer-side Dispatch-evidence applicability
RCP-12 → Node target/receiving-side delegation expectation only
RCP-13 / RCP-15 → Node executor-side Automation correlation expectation only
RCP-17 → Node trial executor/effect contribution only
RCP-19 → Node Applied Configuration contribution only
RCP-22 → N1/N2/N3 fact-owner provenance / bounded diagnostics only
RCP-24 → Node intervention target/outcome-side expectation only
RCP-20 → DEFERRED TO N4 / FUTURE BATCH 2
```

---

# 4. Internal Architecture Responsibility Inventory

The labels below are document-local navigation labels. They are architecture-semantic responsibilities, not modules, packages, classes, services, processes, workers, threads, coroutines, sessions, database objects or deployment units.

## N1 / ND-R01

```text
N1-R01 Node Scope & Governed-context Binding
N1-R02 Capability Actual-state Evidence Custody
N1-R03 Applied Configuration Actual-state Custody
N1-R04 Execution-mode Readiness Qualification
N1-R05 Bounded Node Readiness Qualification
N1-R06 Currentness, Availability & Uncertainty Qualification
N1-R07 Readiness History, Provenance & RCP-04 Contract Governance
```

## N2 / ND-R02

```text
N2-R01 Work / Execution-context Binding
N2-R02 Admission-evidence Applicability Consumption
N2-R03 Dispatch-evidence Receipt, Applicability & Correlation
N2-R04 Attempt Origination & Attempt Identity
N2-R05 Attempt Stage / Progress Evidence Custody
N2-R06 Attempt Completion, Outcome, Failure & Uncertainty Qualification
N2-R07 Intervention Target & Local Outcome Correlation
N2-R08 Delegation / Automation / Trial Execution-context Correlation
N2-R09 Attempt History, Lineage, Provenance & RCP-07 Contract Governance
```

## N3 / ND-R03

```text
N3-R01 Effect Subject / Target & Source-owner Context Binding
N3-R02 Attempt-to-Effect Correlation
N3-R03 Protected Local Effect Occurrence Assertion Custody
N3-R04 Local Source-fact & External-SoT Boundary Qualification
N3-R05 Effect / Source Evidence Currentness, Uncertainty & Qualification
N3-R06 Protected Evidence Disclosure & Redaction Boundary
N3-R07 Effect / Source History, Provenance & RCP-08 Contract Governance
```

```text
Internal Responsibility Count
→ 23

N1 Coverage
→ COMPLETE AT CURRENT BATCH LEVEL

N2 Coverage
→ COMPLETE AT CURRENT BATCH LEVEL

N3 Coverage
→ COMPLETE AT CURRENT BATCH LEVEL

Unowned Material N1/N2/N3 Responsibility
→ 0

Duplicate Final Responsibility
→ 0

N4 Responsibility Designed
→ 0
```

---

# 5. N1 — Local Capability, Readiness & Applied Configuration

## N1-R01 — Node Scope & Governed-context Binding

- **Purpose:** bind one Node-local readiness subject to representation-neutral Node/Participant, Tenant, Principal and governed-context references without creating identity, IAM, Policy or Trust authority.
- **Owned facts:** N1 fact that the local readiness/capability evidence is associated with the referenced Node and applicable governed context.
- **Explicitly non-owned:** Node Principal/IAM identity authority; Tenant/Policy/Trust decisions; Presence; Admission; Dispatch; Attempt; Effect.
- **Input evidence:** Node/Participant Reference, Tenant Context, Organization Context where applicable, Principal/IAM reference, Policy/Trust context references, compatibility context.
- **Output evidence:** stable context binding referenced by later N1 evidence.
- **Dependencies:** accepted Governance Context semantics; no hard semantic dependency on N2/N3/N4.
- **Failure semantics:** missing/mismatched/unverifiable context remains explicit and cannot be converted into Trust, Admission or readiness success.
- **Offline semantics:** retained references may remain usable only according to their accepted applicability; offline does not transfer authority.
- **History obligations:** preserve exact referenced revisions/context applicable to each readiness assertion.
- **Compatibility obligations:** unsupported context revisions remain explicit rather than coerced.

Permanent:

```text
Node Reference != Participant Presence
Node Reference != Principal Authority
Context Reference != Authority
User Session != Principal Identity
```

## N1-R02 — Capability Actual-state Evidence Custody

- **Purpose:** own factual Node-local evidence for capability support/possession and current local capability condition.
- **Owned facts:** installed evidence, available evidence, activated evidence, unsupported evidence where positively established, capability-local technical condition and applicable revision/provenance.
- **Explicitly non-owned:** Artifact Acceptance, Admission, capability semantic authority, external provider authority, broader business capability success.
- **Input evidence:** capability reference, local inspection/source evidence, compatibility/conformance result, N1-R01 context.
- **Output evidence:** capability-state evidence consumed by N1-R04/R05/R06 and RCP-04.
- **Dependencies:** SDD on N1-R01; Foundation technical observation/status/temporal semantics.
- **Failure semantics:** inability to establish a local capability fact produces `UNKNOWN`, `UNAVAILABLE`, `UNSUPPORTED` or other applicable explicit qualification; it does not fabricate absence or revocation.
- **Offline semantics:** genuinely local capability facts remain locally establishable while disconnected.
- **History obligations:** installation/availability/activation changes create new evidence/history and never rewrite prior state.
- **Compatibility obligations:** capability revision/conformance is explicit; incompatible/unsupported is not silently treated as current.

Permanent:

```text
Installed != Accepted
Available != Admitted
Activated != Authorized
Capability Present != Ready automatically
```

## N1-R03 — Applied Configuration Actual-state Custody

- **Purpose:** own the Node-local assertion of which managed configuration revision/value semantics were actually applied to the Node-local target.
- **Owned facts:** Applied Configuration subject/ref, applied revision/context, application outcome evidence, partial/failure/unknown/stale qualification, temporal/provenance history.
- **Explicitly non-owned:** Managed Desired Configuration Authority/SoT, configuration-item semantic authority where owned elsewhere, Observed projection authority.
- **Input evidence:** RCP-19 Desired revision/reference and distribution evidence where available; configuration item owner reference; local application evidence; bootstrap configuration context where distinct.
- **Output evidence:** source-owned Applied evidence for RCP-19 and readiness correlation.
- **Dependencies:** SDD on N1-R01; accepted RCP-19 semantics; capability-owner semantics by reference.
- **Failure semantics:** `PARTIALLY_APPLIED`, application failure, `UNKNOWN`, `STALE` or `CONFLICTING` remain explicit as applicable; Desired is never rewritten by local failure.
- **Offline semantics:** Node may retain last-known Desired reference and its own Applied evidence; disconnection does not transfer Desired authority.
- **History obligations:** exact Desired/Applied revision relationship and local application evidence remain historically resolvable.
- **Compatibility obligations:** item compatibility remains capability-owner judged; unsupported/migration-required is explicit.

Permanent:

```text
Desired != Distributed != Applied != Observed
Distribution Success != Applied
Observed != Applied SoT
```

## N1-R04 — Execution-mode Readiness Qualification

- **Purpose:** establish Node-owned technical readiness evidence for an accepted execution mode without creating a separate executor or governance model.
- **Owned facts:** bounded mode-readiness qualification for `ATTENDED` and `UNATTENDED` contexts where the Node can locally establish it.
- **Explicitly non-owned:** User Session identity authority, IAM, Policy, Trust, Admission, Dispatch.
- **Input evidence:** N1-R02 capability evidence, N1-R03 applied configuration evidence, accepted mode requirements supplied by the applicable execution capability, user-session binding evidence only where attended execution requires it.
- **Output evidence:** mode-readiness evidence for N1-R05/RCP-04.
- **Dependencies:** SDD on N1-R01/R02/R03.
- **Failure semantics:** missing session binding may make an attended mode locally `NOT_READY` or `UNKNOWN` only where such binding is an accepted prerequisite; it never means the Principal is unauthorized. Unattended mode cannot become unrestricted authority.
- **Offline semantics:** mode readiness may be locally established while central presence projection is stale; no public service is required for the local technical fact itself.
- **History obligations:** mode-readiness evidence retains applicable capability/config/session-binding context.
- **Compatibility obligations:** execution-mode capability evolution remains explicit and representation-neutral.

```text
ATTENDED
→ may require legitimate user/session-binding readiness evidence
→ User Session != IAM Authority
→ Attended != bypass Policy / Trust / Admission

UNATTENDED
→ no active-human-presence requirement by mode
→ Unattended != Trusted automatically
→ Unattended != Admitted automatically
→ Unattended != unrestricted
```

## N1-R05 — Bounded Node Readiness Qualification

- **Purpose:** own the final bounded Node-local readiness assertion for a specific capability/execution-mode/readiness subject.
- **Owned facts:** `READY`, `NOT_READY`, `UNKNOWN`, `INDETERMINATE` or equivalent architecture-semantic qualification only where evidence supports that distinction; exact representation is deferred.
- **Explicitly non-owned:** Trust, Admission, route qualification, Dispatch, Attempt, Effect, business semantic readiness outside Node-local execution capability.
- **Input evidence:** N1-R02 capability state, N1-R03 applied config, N1-R04 mode readiness, N1-R01 context, applicable compatibility/technical-health evidence.
- **Output evidence:** principal Node-owned readiness subject consumed by RCP-04.
- **Dependencies:** SDD on N1-R01/R02/R03/R04.
- **Failure semantics:** `NOT_READY` is asserted only from positively established Node-owned unmet technical prerequisites; unavailable remote/governance evidence is not silently converted to `NOT_READY`.
- **Offline semantics:** locally established readiness can exist while RT-R01 reachability is stale/unknown; `Reachable != Ready` is permanent.
- **History obligations:** each readiness assertion is revision/context/time/provenance bound.
- **Compatibility obligations:** readiness meaning remains capability/mode scoped and must not become one universal product readiness boolean.

## N1-R06 — Currentness, Availability & Uncertainty Qualification

- **Purpose:** qualify the currentness, availability and uncertainty of N1-owned evidence independently from its substantive value.
- **Owned facts:** current/stale/unknown/indeterminate evidence qualification, evidence availability, uncertainty cause/reference for N1 facts.
- **Explicitly non-owned:** RT-R01 presence freshness, Admission revocation semantics, N4 reconciliation state machine.
- **Input evidence:** N1-R02/R03/R04/R05 evidence plus Foundation temporal/status semantics.
- **Output evidence:** currentness/uncertainty dimensions for RCP-04 and bounded diagnostics.
- **Dependencies:** SDD on N1-R02/R03/R04/R05.
- **Failure semantics:** `STALE != FALSE`, `UNKNOWN != NOT_READY`, `UNAVAILABLE != REVOKED`.
- **Offline semantics:** central inability to observe N1 evidence does not erase local evidence; local evidence may itself become stale according to its source semantics.
- **History obligations:** currentness changes are new evidence, not mutation of historical fact meaning.
- **Compatibility obligations:** temporal/status semantics use accepted Foundation definitions.

## N1-R07 — Readiness History, Provenance & RCP-04 Contract Governance

- **Purpose:** preserve non-destructive N1 history/provenance and publish owner-side stable RCP-04 semantics.
- **Owned facts:** readiness/capability/applied-config evidence lineage and producer provenance; no new Product authority.
- **Explicitly non-owned:** universal diagnostics store, N4 recovery history, RT/SV/WB projections.
- **Input evidence:** N1-R01..R06.
- **Output evidence:** RCP-04 Node Readiness evidence and bounded RCP-22 provenance.
- **Dependencies:** SDD on N1-R01..R06.
- **Failure semantics:** incomplete history/provenance becomes explicit unsupported/unknown rather than silently re-created.
- **Offline semantics:** N1 evidence must remain retainable/non-destructive for later N4 consumption without defining how N4 reconciles it.
- **History obligations:** mandatory; current projection never rewrites prior readiness/config/capability evidence.
- **Compatibility obligations:** revisions must remain interpretable or explicitly unsupported/migration-required.

---

# 6. N2 — Governed Local Execution

## N2-R01 — Work / Execution-context Binding

- **Purpose:** bind one prospective Node-local execution subject to Operation/Work, Node, capability/mode, governed context and source-domain references without acquiring their authority.
- **Owned facts:** N2 binding/correlation fact only.
- **Explicitly non-owned:** Operation semantic authority, Automation/Agent semantics, Admission, Dispatch, Effect.
- **Input evidence:** Operation/Work Reference, execution intent reference, Node reference, capability/mode references, Tenant/Principal/Policy/Trust context refs, source definition/runtime revision, N1 readiness reference where supplied.
- **Output evidence:** stable context consumed by N2-R02..R09.
- **Dependencies:** external accepted semantics through ACD/XED; no SDD on N3/N4.
- **Failure semantics:** missing/mismatched context remains explicit and does not create an Attempt.
- **Offline semantics:** retained context may support execution only according to its accepted applicability; offline does not create authority.
- **History obligations:** exact execution context used by each Attempt remains attributable.
- **Compatibility obligations:** incompatible source/work revisions remain explicit.

## N2-R02 — Admission-evidence Applicability Consumption

- **Purpose:** consume accepted RCP-02 Formal Admission Evidence for the exact execution subject without re-performing Admission.
- **Owned facts:** Node-local consumer applicability assessment only.
- **Explicitly non-owned:** Admission decision/issuance/revocation authority, Policy/Trust authority.
- **Input evidence:** Admission Evidence Identity/Reference, target intent, Artifact/Definition revision, Tenant/Principal/Policy/Trust/Acceptance linkage, temporal/revocation/stale/offline applicability and provenance.
- **Output evidence:** applicable/not-applicable/stale/unknown/unverified/indeterminate consumer qualification used before Attempt origination.
- **Dependencies:** SDD on N2-R01; accepted S8/RCP-02 via XED/ACD.
- **Failure semantics:** insufficient applicability cannot be converted into a new Admission or denial; N2 preserves uncertainty and does not originate an Attempt that requires unestablished Admission applicability.
- **Offline semantics:** pre-issued evidence may be consumed only within producer-defined bounded applicability; no global fail-open/fail-closed law is created.
- **History obligations:** Attempt history retains the exact Admission Evidence reference/revision used.
- **Compatibility obligations:** producer-defined evidence revision semantics are preserved.

## N2-R03 — Dispatch-evidence Receipt, Applicability & Correlation

- **Purpose:** consume RCP-05 Dispatch Evidence and establish Node-side receipt/correlation without implying Attempt creation/start.
- **Owned facts:** Node receipt/correlation/applicability evidence for the dispatch reference.
- **Explicitly non-owned:** RT-R02 Dispatch decision/history, Admission, Attempt before N2-R04, Effect.
- **Input evidence:** Operation/Work Reference, Dispatch Identity/Reference, target Node/executor reference, Admission reference, R1/RCP-04 evidence refs where supplied, dispatch temporal/provenance/status context.
- **Output evidence:** dispatch-consumer correlation used by N2-R04 and RCP-07.
- **Dependencies:** SDD on N2-R01; accepted RCP-05 via XED/ACD.
- **Failure semantics:** receipt/identification uncertainty remains explicit; malformed/inapplicable dispatch does not fabricate an Attempt.
- **Offline semantics:** retained dispatch evidence alone does not authorize replay or execution; applicable Admission/governed context must still hold.
- **History obligations:** multiple dispatches remain distinct; dispatch identity is never replaced by Attempt identity.
- **Compatibility obligations:** Dispatch contract evolution must preserve identity/provenance/non-collapse.

Permanent:

```text
Dispatch Received != Attempt Originated
Dispatch Handoff Evidenced != Attempt Started
Dispatch Success != Execution Started
```

## N2-R04 — Attempt Origination & Attempt Identity

- **Purpose:** establish the Node-owned local execution Attempt as a distinct semantic subject only when the Node actually originates a bounded local execution responsibility instance under applicable evidence.
- **Owned facts:** Attempt Identity/Reference, Attempt origination evidence, Node/executor binding, applicable admission/dispatch/readiness/config/context references.
- **Explicitly non-owned:** Dispatch identity, Effect identity, source business outcome.
- **Input evidence:** N2-R01 context, N2-R02 applicability, N2-R03 dispatch correlation where dispatch is applicable, N1 readiness/applied-config evidence through EL/XED.
- **Output evidence:** Attempt identity consumed by N2-R05..R09 and N3.
- **Dependencies:** SDD on N2-R01/R02/R03. N1 evidence is EL/XED, not semantic ownership transfer.
- **Failure semantics:** pre-attempt failure to establish applicable evidence remains pre-attempt evidence; it does not require a synthetic Attempt merely because work was dispatched.
- **Offline semantics:** an offline Attempt may originate only where the already-accepted governed evidence needed by the execution subject is locally applicable; no local authority is minted.
- **History obligations:** every retry/re-entry that forms a new local execution responsibility instance gets a new Attempt identity; prior Attempt history is preserved.
- **Compatibility obligations:** Attempt identity is representation-neutral and scoped, not a global namespace.

```text
Operation Identity
!= Admission Evidence Identity
!= Dispatch Identity
!= Attempt Identity
!= Effect Identity
```

## N2-R05 — Attempt Stage / Progress Evidence Custody

- **Purpose:** own source facts about the locally established Attempt's execution stage/progress where architecture-material.
- **Owned facts:** Attempt started evidence where locally established, running/progress/waiting/stopped technical evidence where applicable, stage temporal/provenance context.
- **Explicitly non-owned:** universal state machine, source-domain semantic continuation, Effect occurrence, business outcome.
- **Input evidence:** N2-R04 Attempt identity plus local execution observations.
- **Output evidence:** stage/progress evidence for RCP-07 and bounded diagnostics.
- **Dependencies:** SDD on N2-R04.
- **Failure semantics:** missing progress evidence is `UNKNOWN`/`UNAVAILABLE` where applicable, not fabricated progress or failure.
- **Offline semantics:** local stage evidence remains locally owned through disconnection.
- **History obligations:** stage/progress evidence is append-oriented/non-destructive.
- **Compatibility obligations:** stage evidence categories are semantic, not a mandatory transition graph or wire enum.

## N2-R06 — Attempt Completion, Outcome, Failure & Uncertainty Qualification

- **Purpose:** qualify the Node-local Attempt's bounded terminal/non-terminal outcome evidence without claiming Effect or business success.
- **Owned facts:** local completion qualification, local execution failure evidence, stopped evidence, indeterminate/unknown outcome where applicable.
- **Explicitly non-owned:** protected Effect occurrence, effect reversal, Automation/Agent/Business semantic result.
- **Input evidence:** N2-R04/R05 and local executor evidence; N3 effect evidence may be linked by EL only when available.
- **Output evidence:** RCP-07 Attempt outcome/failure evidence.
- **Dependencies:** SDD on N2-R04/R05. N3 evidence is EL/HPL, never reverse SDD.
- **Failure semantics:** `Attempt completed` means only the bounded N2 execution-attempt lifecycle is locally established as completed; it does not imply Effect or business success. Uncertain completion remains explicit.
- **Offline semantics:** final local Attempt evidence survives disconnection and later projection lag.
- **History obligations:** later Effect/business evidence never rewrites prior Attempt failure/uncertainty.
- **Compatibility obligations:** outcome semantics remain bounded to N2 and do not become a universal execution-success model.

## N2-R07 — Intervention Target & Local Outcome Correlation

- **Purpose:** receive/correlate already-governed intervention intent to a Node Attempt and report Node-local target/application/outcome evidence where the source-defined capability supports it.
- **Owned facts:** intervention received/correlated fact; local target-side applied/not-applied/unknown evidence where genuinely established; Attempt state consequences owned by N2.
- **Explicitly non-owned:** universal cancel/retry/resume/stop/recovery semantics, request authority, operation semantic outcome, rollback/compensation/effect reversal.
- **Input evidence:** RCP-24 intent/reference, RT-R03 coordination evidence where applicable, Attempt reference, source-defined intervention meaning.
- **Output evidence:** target-side outcome reference for RCP-24/RCP-22.
- **Dependencies:** SDD on N2-R04; RCP-24/R3 are XED/ACD.
- **Failure semantics:** requested/received/forwarded/applied/outcome remain distinct; unsupported/unavailable/indeterminate is explicit.
- **Offline semantics:** offline does not create a universal right to apply intervention; only locally applicable governed intent can be acted upon.
- **History obligations:** each intervention request/outcome remains correlated without rewriting Attempt history.
- **Compatibility obligations:** capability-specific action meaning must be preserved; no universal action set is frozen.

Permanent:

```text
Intervention Requested != Intervention Applied
Cancel Requested != Cancelled
Stop Requested != Stopped
Stopped != Effects Reversed
```

## N2-R08 — Delegation / Automation / Trial Execution-context Correlation

- **Purpose:** preserve cross-domain execution references needed for Node execution without becoming Agent, Automation or Trial semantic authority.
- **Owned facts:** Node-side correlation between Attempt and supplied delegation/Automation/trial references.
- **Explicitly non-owned:** AG-R04 delegation source semantics; S6/SV-R02 Automation semantic continuation/composition; Trial Intent/semantic outcome.
- **Input evidence:** RCP-12 delegation reference where supplied; RCP-13/RCP-15 Automation operation/continuation/composition refs; RCP-17 Trial intent/context/admission/dispatch refs.
- **Output evidence:** Node Attempt reference correlated to those subjects.
- **Dependencies:** SDD on N2-R01/R04; external contracts are XED/ACD.
- **Failure semantics:** missing/incompatible correlation remains explicit; Node does not infer source semantic success from local completion.
- **Offline semantics:** retained cross-domain refs remain references only; offline does not transfer source authority.
- **History obligations:** historical Attempt remains bound to exact source revision/trial/delegation context used.
- **Compatibility obligations:** owner-defined revisions remain authoritative.

## N2-R09 — Attempt History, Lineage, Provenance & RCP-07 Contract Governance

- **Purpose:** preserve non-destructive Attempt history/lineage/provenance and publish owner-side RCP-07 semantics.
- **Owned facts:** Attempt lineage and N2 provenance only.
- **Explicitly non-owned:** Dispatch history ownership, Effect history ownership, universal history service, N4 recovery logic.
- **Input evidence:** N2-R01..R08.
- **Output evidence:** RCP-07 Node Attempt evidence and bounded RCP-22 provenance.
- **Dependencies:** SDD on N2-R04/R05/R06/R07/R08 plus binding context.
- **Failure semantics:** absent lineage/provenance remains explicit; history is never reconstructed by overwriting earlier records.
- **Offline semantics:** Attempt evidence is retainable for later N4 consumption without specifying reconciliation behavior.
- **History obligations:** mandatory; retry/re-entry creates a new Attempt, prior Attempt evidence remains immutable in historical meaning.
- **Compatibility obligations:** lineage semantics must remain interpretable across compatible evolution.

---

# 7. N3 — Protected Local Effect & Source-fact Custody

## N3-R01 — Effect Subject / Target & Source-owner Context Binding

- **Purpose:** bind one protected local Effect/source-evidence subject to its target/resource, source owner, Tenant/governed context and applicable source revision without claiming broader authority.
- **Owned facts:** N3 binding/provenance fact only.
- **Explicitly non-owned:** external resource final SoT, Policy/Trust/Admission, business semantic outcome.
- **Input evidence:** target/resource reference, source-owner reference, Tenant/Principal/privacy context, source revision/context where applicable, compatibility context.
- **Output evidence:** context consumed by N3-R02..R07.
- **Dependencies:** accepted governed-context/provenance semantics.
- **Failure semantics:** unknown source owner/revision becomes explicit and cannot be canonicalized locally.
- **Offline semantics:** local binding evidence survives disconnection; external current state may become unavailable/stale.
- **History obligations:** exact source-owner/revision context remains attributable.
- **Compatibility obligations:** source identity/revision changes require explicit compatibility interpretation.

## N3-R02 — Attempt-to-Effect Correlation

- **Purpose:** correlate an N3 Effect/source-evidence subject to the N2 Attempt that may have produced it without inferring effect occurrence from Attempt state.
- **Owned facts:** correlation evidence only.
- **Explicitly non-owned:** Attempt identity/state, Effect occurrence before N3-R03.
- **Input evidence:** N2 Attempt Reference, optional Dispatch/Operation references, effect target context.
- **Output evidence:** stable Attempt reference used by RCP-08.
- **Dependencies:** SDD on N3-R01 and on N2-R04 Attempt identity semantics; Attempt state feedback is EL/HPL only.
- **Failure semantics:** missing correlation remains explicit; it does not fabricate either an Attempt or Effect.
- **Offline semantics:** correlation remains locally retainable.
- **History obligations:** one Attempt may correlate to zero/one/multiple effect/source evidence subjects without identity collapse.
- **Compatibility obligations:** Attempt and Effect identities remain independently evolvable but correlatable.

## N3-R03 — Protected Local Effect Occurrence Assertion Custody

- **Purpose:** own the bounded Node-local assertion of whether a protected local Effect occurrence is genuinely established by Node-owned evidence.
- **Owned facts:** protected local Effect evidence identity/reference, effect occurrence/assertion evidence, local target/resource context and provenance.
- **Explicitly non-owned:** N2 Attempt completion, external-system final factual SoT, business/Automation/Agent semantic success, effect reversal law.
- **Input evidence:** N3-R01/R02 plus protected local source evidence.
- **Output evidence:** primary protected-effect evidence for RCP-08.
- **Dependencies:** SDD on N3-R01/R02.
- **Failure semantics:** `OCCURRED`, `PARTIAL`, `NOT_ESTABLISHED`, `UNKNOWN`, `INDETERMINATE` or `CONFLICTING` distinctions may be expressed where applicable; they are semantic qualifications, not a universal state machine. `NOT_ESTABLISHED` is not proof that no external effect exists.
- **Offline semantics:** genuinely Node-origin effect evidence survives disconnect and may be more current than a central projection without becoming broader business truth.
- **History obligations:** later success/effect evidence does not erase earlier Attempt failure/uncertainty or prior partial evidence.
- **Compatibility obligations:** Effect evidence meaning remains target/source scoped and representation-neutral.

Permanent:

```text
Attempt != Effect
Attempt Success != Effect automatically
Effect != Business Semantic Outcome automatically
Stopped != Effects Reversed
```

## N3-R04 — Local Source-fact & External-SoT Boundary Qualification

- **Purpose:** distinguish genuinely Node-origin local source facts from local observations/references of an external or other-component final SoT.
- **Owned facts:** Node-origin local source fact where the assertion genuinely originates under Node custody; source-owner/SoT qualification of locally retained evidence.
- **Explicitly non-owned:** external/business-system/other-component final factual SoT when assigned upstream.
- **Input evidence:** source-owner reference, target/resource context, local source evidence, external revision/context where applicable.
- **Output evidence:** source-fact or external-evidence qualification used by RCP-08/provenance.
- **Dependencies:** SDD on N3-R01.
- **Failure semantics:** unknown/conflicting source ownership remains explicit and triggers revalidation if architecture authority cannot be established; local availability never decides the winner.
- **Offline semantics:** a local copy/reference does not replace an external SoT; external currentness may be `UNAVAILABLE`/`STALE`/`UNKNOWN`.
- **History obligations:** preserve original source identity/revision/provenance; central projection never rewrites source history.
- **Compatibility obligations:** external-source evolution retains source identity/SoT mapping semantics.

```text
Node-origin Local Source Fact
→ Node may own the bounded assertion

Observation / Projection of external fact
→ evidence/reference only
→ external/other accepted owner remains final SoT

Local Copy != External SoT Replacement
Observation / Projection != Source Fact
```

## N3-R05 — Effect / Source Evidence Currentness, Uncertainty & Qualification

- **Purpose:** qualify currentness, uncertainty, evidence availability and bounded technical outcome for N3-owned evidence.
- **Owned facts:** N3 evidence current/stale/unknown/indeterminate/partial/conflicting qualification and uncertainty provenance.
- **Explicitly non-owned:** universal conflict resolution, N4 reconciliation, business outcome qualification.
- **Input evidence:** N3-R03/R04 plus Foundation temporal/status semantics.
- **Output evidence:** RCP-08 currentness/uncertainty dimensions and bounded RCP-22 diagnostics.
- **Dependencies:** SDD on N3-R03/R04.
- **Failure semantics:** uncertainty is preserved rather than collapsed to success/failure; latest timestamp cannot choose authority.
- **Offline semantics:** locally current N3 evidence and centrally stale projection may coexist without authority transfer.
- **History obligations:** currentness changes do not rewrite historical evidence meaning.
- **Compatibility obligations:** accepted uncertainty/status semantics are reused.

## N3-R06 — Protected Evidence Disclosure & Redaction Boundary

- **Purpose:** ensure protected effect/source evidence can be exposed only with governed disclosure, privacy and redaction semantics while retaining source identity/provenance.
- **Owned facts:** N3 fact that an evidence projection/output has been bounded/redacted according to applicable accepted context; not Privacy/Policy authority.
- **Explicitly non-owned:** Policy decision, Trust decision, Secret Material authority, Web diagnostics UI.
- **Input evidence:** N3 evidence, Tenant/Principal/Policy/privacy refs, Secret Reference metadata where applicable, sensitive-data classification supplied by owning semantics.
- **Output evidence:** disclosure-safe representation/projection input; source evidence remains unchanged.
- **Dependencies:** SDD on N3-R03/R04/R05; accepted Sensitive-data Redaction and Semantic Representation Foundation semantics.
- **Failure semantics:** inability to establish disclosure applicability yields unavailable/redacted/indeterminate exposure rather than leaking raw evidence.
- **Offline semantics:** offline/private does not relax privacy/redaction boundaries.
- **History obligations:** redaction does not mutate the underlying source evidence history.
- **Compatibility obligations:** representation changes preserve semantic identity/provenance and disclosure constraints.

## N3-R07 — Effect / Source History, Provenance & RCP-08 Contract Governance

- **Purpose:** preserve non-destructive N3 history/provenance and publish owner-side RCP-08 semantics.
- **Owned facts:** Effect/source evidence lineage and N3 producer provenance only.
- **Explicitly non-owned:** universal diagnostics/history store, N4 recovery semantics, external final SoT.
- **Input evidence:** N3-R01..R06.
- **Output evidence:** RCP-08 Node Effect/Source Evidence plus bounded RCP-22 provenance.
- **Dependencies:** SDD on N3-R01..R06.
- **Failure semantics:** absent provenance/currentness remains explicit; later evidence cannot silently canonicalize earlier conflict.
- **Offline semantics:** evidence remains retainable for future N4 without defining replay/reconciliation.
- **History obligations:** mandatory and non-destructive.
- **Compatibility obligations:** historical evidence remains interpretable or explicitly unsupported/migration-required.

---

# 8. Runtime Role Traceability

```text
ND-R01 Node Capability & Readiness Participant
→ N1
→ N1-R01..N1-R07
→ TRACEABILITY COMPLETE

ND-R02 Governed Local Execution Participant
→ N2
→ N2-R01..N2-R09
→ TRACEABILITY COMPLETE

ND-R03 Protected Local Effect Custodian
→ N3
→ N3-R01..N3-R07
→ TRACEABILITY COMPLETE

ND-R04
→ N4 future
→ NOT DESIGNED / NOT AUTHORIZED
```

No new Runtime Role is created.

---

# 9. Authority / SoT / Actual-state Map

| Subject | Final owner at this design level | Node relationship | Explicit non-implication |
|---|---|---|---|
| Tenant / Principal / Policy / Trust | accepted `ns_server` authorities | reference/consume governed context | local execution never becomes authority |
| Artifact Acceptance | S8 | consume reference where applicable | installed/loadable != accepted |
| Execution Admission | S8/SV-R04 | N2 consumes RCP-02 | evidence possession != Admission Authority |
| Presence / Reachability | R1/RT-R01 | N1 may correlate participant-side evidence | reachable != ready |
| Routing / Scheduling / Dispatch | R2/RT-R02 | N2 consumes RCP-05 | dispatch != attempt |
| Managed Desired Configuration | S9/SV-R05 | N1 consumes desired ref | local copy != desired SoT |
| Node capability/install/availability/activation | N1/ND-R01 | final Node-local Actual-state owner | installed/available/activated do not grant authority |
| Node Applied Configuration | N1/ND-R01 | final Node-local Applied assertion owner | applied != desired/observed |
| Node bounded readiness | N1/ND-R01 | final Node-local readiness owner | ready != reachable/trusted/admitted |
| Node Attempt | N2/ND-R02 | final bounded Attempt owner | attempt != effect/business success |
| protected local Effect | N3/ND-R03 | final owner of Node-origin protected-effect assertion | effect != business outcome |
| Node-origin local source fact | N3/ND-R03 where genuinely local | final bounded source owner | local fact != broader domain truth |
| external/business/other-component factual SoT | accepted external/other owner | local evidence/reference only | local copy != external SoT |
| Automation semantic continuation/composition | S6/SV-R02 | executor-side correlation only | local completion != Automation outcome |
| Agent delegation semantics | AG-R04 downstream | target-side expectation only | delegation != attempt/effect |

```text
Authority Ambiguity Introduced
→ 0

SoT Ambiguity Introduced
→ 0

Circular Actual-state Ownership
→ NONE
```

---

# 10. Readiness Semantics

Readiness is a bounded Node-owned technical/execution-mode Actual-state subject. It is not one universal Node boolean and is not an authorization decision.

A readiness assertion is scoped by, where applicable:

```text
Node / Participant Reference
Capability Reference
Capability state evidence
Execution mode
Applied Configuration context
technical health / local prerequisite evidence
Tenant / governed-context references
compatibility/conformance context
currentness / availability / uncertainty
producer provenance
```

Permanent separations:

```text
Connected / Reachable
→ R1 evidence

Ready / Not Ready / Unknown
→ N1 bounded local evidence

Trusted
→ S4 authority

Admitted
→ S8 authority
```

No fixed readiness formula, heartbeat, health-check algorithm, process/session model or universal readiness state machine is selected.

---

# 11. Attempt Semantics

The local execution sequence preserves distinct evidence subjects:

```text
Operation / Work Reference
→ external/source-owned semantic subject

Admission Evidence
→ S8 owner

Dispatch Identity
→ R2 owner

Dispatch received/correlated at Node
→ N2-R03 fact

Attempt Originated
→ N2-R04 creates a distinct Node Attempt identity only when a local execution responsibility instance is actually established

Attempt Started / Progress / Waiting / Stopped
→ N2-R05 where locally established

Attempt Completion / Failure / Uncertainty
→ N2-R06

Protected Effect / Source Fact
→ N3 separate evidence subject
```

A technical retry/re-entry is never modeled as mutation of the prior Attempt. If it establishes a new local execution responsibility instance, it has a new Attempt identity and lineage to earlier context where applicable. This Candidate does not decide when retry should occur.

No exactly-once, at-most-once, at-least-once, universal retry, universal cancellation, rollback or compensation law is created.

---

# 12. Effect / Source-fact Semantics

N3 distinguishes three authority conditions:

```text
1. Node-origin protected Effect assertion
→ N3 owns whether the bounded Node-local effect occurrence is established

2. genuinely Node-origin local source fact
→ N3 may own the bounded local factual assertion

3. local observation/copy/reference of external or other-component fact
→ N3 owns only its local evidence/provenance
→ final factual SoT stays with the accepted external/other owner
```

Permanent:

```text
Attempt != Effect
Attempt Completed != Effect Occurred automatically
Effect Occurred != Business Semantic Success automatically
Local Effect != External-system final SoT automatically
Local Copy != External SoT Replacement
Observation / Projection != Source Fact
```

No universal effect-reversal, rollback or compensation semantics are selected.

---

# 13. Attended / Unattended Semantics

Attended and unattended are two governed execution-mode contexts of the same N1/N2/N3 authority topology.

```text
ATTENDED
→ N1 may require legitimate user-session binding as a readiness prerequisite for the applicable capability
→ N2 still consumes the same governed Admission/Dispatch context
→ User Session != IAM Authority
→ attended presence does not bypass Policy / Trust / Admission

UNATTENDED
→ no active human session required by mode
→ requires already-applicable governed evidence for the execution subject
→ unattended != unrestricted
→ unattended != trusted automatically
→ unattended != admitted automatically
```

No browser profile, desktop session, Windows session, worker session, process, thread or coroutine model is designed.

---

# 14. Desired / Applied / Observed Configuration Topology

```text
Managed Desired Configuration Authority / SoT
→ S9 / SV-R05

Distribution intent / evidence
→ upstream evidence only

Node Applied Configuration Actual-state
→ N1 / ND-R01

Observed Configuration
→ derived projection / observation
```

RCP-19 Node contribution requires, where applicable:

```text
Configuration Subject Reference
Configuration Item Semantic-owner Reference
Desired Revision Reference
Distribution Evidence Reference where supplied
Applied Revision / Context
Applied outcome / partial / failure / unknown qualification
Temporal / currentness context
Node producer provenance
Compatibility / conformance context
Secret Reference only where applicable
```

Secret Material is excluded from ordinary configuration evidence.

---

# 15. RCP-04 — Node Readiness Owner-side Stable Contract

## 15.1 Stable semantic subjects

```text
Node / Participant Reference
Capability Reference
Node Capability / Readiness Evidence Identity or Reference
Capability State Evidence
Execution-mode Readiness Evidence
Applied Configuration Evidence Reference
Bounded Readiness Qualification
Currentness / Freshness Qualification
Availability / Uncertainty Qualification
```

RCP-04 preserves where applicable:

- Node/Participant Reference;
- capability identity/reference and supported-scope context;
- installed/available/activated/unsupported evidence as distinct dimensions where applicable;
- execution-mode readiness (`ATTENDED` / `UNATTENDED` context without separate authority topology);
- Applied Configuration subject/revision/evidence relevant to readiness;
- bounded readiness assertion and readiness subject scope;
- currentness/freshness/availability/uncertainty;
- Tenant/Principal/Policy/Trust context references without authority transfer;
- temporal/applicability context;
- provenance/history/lineage;
- compatibility/conformance context.

## 15.2 ND-R01 producer obligations

ND-R01 MUST:

1. emit only Node-local facts N1 is authorized to own;
2. preserve capability, mode and Applied Configuration dimensions separately;
3. distinguish substantive readiness from evidence currentness/availability;
4. never infer readiness from R1 reachability alone;
5. never infer Trust or Admission from readiness;
6. preserve exact producer/provenance/context and non-destructive history;
7. preserve `UNKNOWN`, `STALE`, `UNAVAILABLE`, `UNSUPPORTED`, `INDETERMINATE` or other accepted uncertainty distinctions where applicable;
8. remain representation-neutral and compatible with private/offline deployment;
9. preserve Secret Reference vs Secret Material separation;
10. keep compatibility/conformance explicit.

## 15.3 Consumer obligations

A consumer MUST NOT infer from RCP-04 evidence alone:

```text
Trust
Formal Admission
Dispatch
Attempt existence/start
Protected Effect
Business / Automation / Agent semantic success
```

```text
RCP-04 ND-R01 Owner/Source-side Semantics
→ CLOSED AT CURRENT CANDIDATE DESIGN LEVEL

RCP-04 Runtime Consumer Expectation
→ preserved from accepted RT-R02 design

RCP-04 Full Cross-component Closure
→ NOT CLAIMED
```

---

# 16. RCP-07 — Node Attempt Owner-side Stable Contract

## 16.1 Stable semantic subjects

```text
Operation / Work Reference
Admission Evidence Reference
Dispatch Identity / Reference
Attempt Identity / Reference
Node / Executor Reference
Attempt Stage Evidence
Attempt Outcome / Failure / Uncertainty Evidence
```

RCP-07 preserves where applicable:

- Operation/Work and source semantic revision references;
- Admission Evidence reference and consumer-applicability context;
- Dispatch Identity/reference and dispatch-consumer correlation;
- Attempt Identity/reference distinct from Operation/Dispatch/Effect;
- Node/executor reference;
- N1 readiness/Applied Configuration references relevant to origination;
- execution-mode context;
- Attempt origination evidence;
- Attempt started/stage/progress/waiting/stopped evidence where architecture-material and locally established;
- completion/outcome/failure/uncertainty qualification;
- intervention request/outcome correlation where applicable;
- delegation/Automation/trial context references where supplied;
- temporal/currentness context;
- history/lineage/provenance;
- compatibility/conformance context.

## 16.2 ND-R02 producer obligations

ND-R02 MUST:

1. never synthesize Attempt existence from Dispatch receipt alone;
2. originate a distinct Attempt identity only for an actual local execution responsibility instance;
3. preserve Admission and Dispatch references without gaining either authority;
4. keep stage/progress/completion evidence source-owned and uncertainty explicit;
5. keep Attempt outcome distinct from N3 Effect and domain semantic outcome;
6. preserve retry/re-entry as new Attempt lineage rather than prior Attempt mutation;
7. preserve intervention requested/applied/outcome distinctions;
8. retain exact source revision/governance/config context historically;
9. remain private/offline compatible without minting authority;
10. remain representation-neutral and compatible/conformant.

## 16.3 Permanent non-collapse

```text
Admission != Dispatch != Attempt != Effect
Dispatch Evidence != Attempt Evidence
Dispatch Received != Attempt Originated
Attempt Started != Effect Occurred
Attempt Completed != Business Success
Stopped != Effects Reversed
```

```text
RCP-07 ND-R02 Owner/Source-side Semantics
→ CLOSED AT CURRENT CANDIDATE DESIGN LEVEL

RCP-07 Full Cross-component Closure
→ NOT CLAIMED BY INFERENCE
```

---

# 17. RCP-08 — Node Effect / Source Evidence Owner-side Stable Contract

## 17.1 Stable semantic subjects

```text
Attempt Reference
Protected Effect / Source Evidence Identity or Reference
Effect Subject / Target Reference
Source-owner Reference
Source Revision / Context where applicable
Effect Occurrence / Source-fact Assertion Evidence
```

RCP-08 preserves where applicable:

- Attempt Reference without identity collapse;
- Effect/source evidence identity/reference;
- effect subject/target/resource reference;
- source owner and final factual SoT reference;
- source revision/context where applicable;
- protected local effect occurrence/assertion evidence;
- protected local source-fact evidence where genuinely Node-origin;
- external-source observation/reference qualification where final SoT is external;
- currentness/uncertainty/partial/conflicting qualification;
- temporal context;
- history/provenance;
- compatibility/conformance;
- Tenant/Principal/privacy context where applicable;
- disclosure/redaction qualification;
- source/business outcome reference only when supplied by the authoritative owner, never synthesized by N3.

## 17.2 ND-R03 producer obligations

ND-R03 MUST:

1. emit only protected local Effect/source evidence N3 can genuinely own;
2. preserve Attempt correlation without deriving Effect from Attempt success;
3. preserve source-owner/final-SoT identity and never promote a local copy by availability;
4. distinguish local source fact from external observation/projection;
5. preserve partial/unknown/indeterminate/conflicting evidence explicitly;
6. retain source/effect history non-destructively;
7. apply governed privacy/redaction semantics before ordinary disclosure without mutating source evidence;
8. remain private/offline capable without public SaaS dependency;
9. preserve Secret Reference vs Secret Material separation;
10. remain representation-neutral and compatibility/conformance aware.

## 17.3 Permanent non-collapse

```text
Attempt != Effect
Effect Evidence != universal Business Result
Effect Evidence != external SoT replacement
Local Source Fact != broader domain truth
Correlation != Ownership
```

```text
RCP-08 ND-R03 Owner/Source-side Semantics
→ CLOSED AT CURRENT CANDIDATE DESIGN LEVEL

RCP-08 Full Cross-component Closure
→ NOT CLAIMED BY INFERENCE
```

---

# 18. Bounded RCP Refinements

| RCP | Current Node contribution | Authority preserved | Explicit non-claim |
|---|---|---|---|
| RCP-02 Admission | N2-R02 consumes exact S8 evidence applicability; retains reference/history | S8/SV-R04 | no Admission issuance/revocation/redefinition |
| RCP-03 Presence | N1 may correlate its Node/readiness evidence to RT-R01 Participant/Presence refs | RT-R01 owns connection/presence/reachability coordination | connected/reachable never becomes ready |
| RCP-05 Dispatch | N2-R03 consumes/correlates Dispatch evidence; N2-R04 later originates Attempt independently | RT-R02 | dispatch != attempt |
| RCP-12 Delegation | N2-R08 target-side references only | AG-R04 source semantics remain downstream | delegation request/accepted != Node Attempt/Effect |
| RCP-13 Automation Continuation | N2-R08 executor-side operation/revision correlation | S6/SV-R02 | Node completion != Automation semantic continuation/result |
| RCP-15 Automation Composition | N2-R08 executor-side parent/callee context correlation | S6/SV-R02 | no composition semantics reopened |
| RCP-17 Trial | N2 produces Trial Attempt evidence; N3 produces Trial Effect evidence where applicable | domain owner retains Trial Intent/semantic outcome | Full Trial closure not claimed; Trial Success != Acceptance/Production Admission |
| RCP-19 Config | N1-R03 produces Node Applied evidence | S9 desired authority; item semantic owner preserved | desired != applied != observed |
| RCP-22 Diagnostics/Provenance | N1/N2/N3 each expose only their own bounded technical/provenance evidence | original fact owner | no N4 comprehensive diagnostics, no Web/SDK model |
| RCP-24 Intervention | N2-R07 receives/correlates intent and produces Node-local target/outcome evidence | source/receiving semantic owner remains applicable | request != applied/outcome; no universal intervention law |
| RCP-20 Recovery | N1/N2/N3 evidence is non-destructive, provenance-rich and future-consumable | future N4 + RT-R04 within accepted owners | no Node recovery/reconciliation design in Batch 1 |

---

# 19. Identity / Correlation / Provenance Model

The Candidate requires representation-neutral distinctions:

```text
Node / Participant Reference
!= Capability Reference
!= Node Capability / Readiness Evidence Identity
!= Operation / Work Reference
!= Admission Evidence Identity
!= Dispatch Identity
!= Attempt Identity
!= Protected Effect / Source Evidence Identity
```

No global event namespace, global Node execution namespace, UUID format, database PK, message key, wire ID, hostname/session/process identifier or serialization format is selected.

Rules:

1. **Reference != Authority.** A reference points to a subject/owner; it does not transfer authority.
2. **Correlation != Ownership.** Linking Dispatch→Attempt→Effect never moves source ownership.
3. **Retry/re-entry creates a new Attempt identity** when a new local execution responsibility instance is formed.
4. **One Attempt may correlate to zero/one/multiple effect evidence subjects.** Attempt and Effect identities never collapse.
5. **Evidence identity is bounded.** N1/N2/N3 evidence identities exist only where history/correlation materially require distinction.
6. **Historical context is revision-pinned.** Applicable Admission, Dispatch, source definition, readiness and Applied Configuration references remain attached to historical evidence.

---

# 20. Failure / Unknown / Stale Semantics

Accepted Technical Status & Uncertainty semantics are reused rather than redefined. Where applicable the Node preserves explicit distinctions including:

```text
UNKNOWN
INDETERMINATE
MISSING
UNAVAILABLE
UNREACHABLE as external R1 evidence, not N1 readiness
STALE
CONFLICTING
UNSUPPORTED
UNVERIFIED
PARTIALLY_APPLIED
```

No universal rule converts uncertainty into allow/deny, success/failure or canonical state.

Examples:

```text
R1 Reachability STALE
!= N1 NOT_READY

Admission evidence UNKNOWN
!= newly NOT_ADMITTED

Dispatch received
!= Attempt created

Attempt completion INDETERMINATE
!= Effect absent

Effect evidence UNKNOWN
!= Business failure

External SoT UNAVAILABLE
!= local copy becomes canonical
```

---

# 21. Non-destructive History / Lineage

Mandatory history rules:

```text
new capability/readiness observation
!= prior evidence rewrite

new Applied Configuration revision/evidence
!= prior applied-history mutation

new Attempt
!= mutate old Attempt

retry/re-entry
!= prior Attempt rewrite

later Effect evidence
!= erase earlier Attempt failure

later success
!= erase prior uncertainty

current projection
!= rewrite source history

central arrival order / latest timestamp
!= conflict winner
```

N1, N2 and N3 each remain the history/provenance producer for their own facts. Aggregation/projection does not become source authority.

---

# 22. Offline / Private / Degraded Boundary

N1-N3 must remain architecture-correct in private/offline/degraded deployment.

Allowed:

- retain Node-owned capability/readiness/Applied/Attempt/Effect/source evidence;
- consume already-applicable retained governed evidence according to accepted producer semantics;
- preserve `UNKNOWN`, `STALE`, `UNAVAILABLE`, `INDETERMINATE`, `PARTIAL`, `CONFLICTING` as applicable;
- continue to produce locally established N1/N2/N3 evidence;
- hand off retained evidence later without implying reconciliation.

Prohibited:

```text
Offline → Authority Transfer
Local Copy → Canonical Global Source
Reconnect → Reconciled
Sync → Proof of Authority
Replay → Retroactive Authorization
Local Availability → Conflict Winner
```

This Candidate does not define N4 retention storage, recovery sequencing, re-observation, replay, conflict resolution or reconciliation state machine.

---

# 23. Shared Foundation Consumption

Accepted Foundation remains authority-neutral. Applicable semantics are reused as follows:

| Accepted Foundation semantic | N1/N2/N3 use | Non-implication |
|---|---|---|
| C01 Bootstrap Configuration Acquisition | Node-local bootstrap acquisition before managed Desired availability where applicable | loader != Desired Config Authority |
| C02 Diagnostic Occurrence & Delivery Evidence | bounded N1/N2/N3 technical diagnostic occurrence/delivery evidence | diagnostics != source authority; no N4 aggregator |
| C03 Technical Observation & Health Evidence | capability/readiness/attempt/effect technical observations | observation != product truth automatically |
| C04 Temporal & Freshness | currentness/stale/applicability/history | clock/TTL mechanics do not define authority |
| C05 Operation Correlation & Provenance Context | Operation/Dispatch/Attempt/Effect correlation and provenance | carrier != operation owner |
| C06 Semantic Representation & Serialization | representation-neutral RCP-04/07/08 realization | representation != semantic authority |
| C07 Network Invocation Mechanics | only where a Node capability requires network invocation | transport/client != provider/domain authority |
| C09 Durable Storage Access Mechanics | conditional downstream realization for retained history if durable mechanics are required | storage placement != evidence authority/SoT |
| C10 Technical Status & Uncertainty | explicit unknown/stale/indeterminate/partial/conflict semantics | status helper != domain result authority |
| C11 Governed Context Propagation | Tenant/Principal/Policy/Trust refs across execution/evidence | carrier != IAM/Policy/Trust Authority |
| C12 Secret Reference | secret references in config/capability context where applicable | reference != Secret Material |
| C13 Sensitive-data Redaction | protected Effect/source evidence disclosure | redactor != Privacy/Policy Authority |
| C14 Compatibility & Conformance | capability/config/contract revision interpretation | helper != universal Compatibility Authority |

No parallel Node-local Foundation is created. No missing mandatory Foundation semantic was discovered. Deferred Foundation candidates are not required for current closure.

---

# 24. Dependency Taxonomy and Hard SDD Graph

Accepted dependency taxonomy:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only SDD enters hard cycle analysis.

## 24.1 N1 SDD

```text
N1-R02 → N1-R01
N1-R03 → N1-R01
N1-R04 → N1-R01, N1-R02, N1-R03
N1-R05 → N1-R01, N1-R02, N1-R03, N1-R04
N1-R06 → N1-R02, N1-R03, N1-R04, N1-R05
N1-R07 → N1-R01, N1-R02, N1-R03, N1-R04, N1-R05, N1-R06
```

## 24.2 N2 SDD

```text
N2-R02 → N2-R01
N2-R03 → N2-R01
N2-R04 → N2-R01, N2-R02, N2-R03
N2-R05 → N2-R04
N2-R06 → N2-R04, N2-R05
N2-R07 → N2-R04
N2-R08 → N2-R01, N2-R04
N2-R09 → N2-R04, N2-R05, N2-R06, N2-R07, N2-R08
```

External N1 readiness / Applied Configuration evidence enters N2 through `EL/XED`, not reverse semantic ownership.

## 24.3 N3 SDD

```text
N3-R02 → N3-R01, N2-R04
N3-R03 → N3-R01, N3-R02
N3-R04 → N3-R01
N3-R05 → N3-R03, N3-R04
N3-R06 → N3-R03, N3-R04, N3-R05
N3-R07 → N3-R01, N3-R02, N3-R03, N3-R04, N3-R05, N3-R06
```

N2 may consume N3 effect evidence for correlation/diagnostics only through `EL/HPL`. There is deliberately no N2 semantic-definition dependency on N3 effect success.

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

# 25. Explicit Implementation Deferrals

This Candidate does not select or design:

```text
Redis / RabbitMQ / Kafka / NATS / Celery / Temporal / Airflow / Quartz / APScheduler
database / storage engine / event store / table / ORM
queue / broker / scheduler / workflow engine
sandbox technology / browser automation framework
REST / gRPC / concrete WebSocket protocol/frame/handshake/envelope
DTO / wire schema
process / service / worker / thread / coroutine
browser profile / desktop session / Windows session / worker session
container / pod / host / deployment topology
UUID / database key / message key / wire key format
universal retry / cancellation / rollback / compensation
exactly-once / at-most-once / at-least-once
local-wins / central-wins / latest-wins
recovery state machine / replay / reconciliation algorithm
```

Implementation or detailed realization must consume this Candidate after independent Global Acceptance; it may not decide the architecture rules left above.

---

# 26. Future N4 Compatibility Without N4 Design

N1/N2/N3 establish only future-consumability obligations:

```text
Evidence
→ source-owner attributable
→ revision/context/provenance bearing
→ non-destructive
→ uncertainty preserving
→ compatibility/conformance identifiable
→ historically correlatable
→ private/offline retainable in principle
```

This permits a later separately authorized N4 design to consume evidence without forcing history reconstruction or authority transfer.

Not defined here:

```text
recovery scope
re-observation algorithm
replay policy
reconciliation state machine
conflict winner
merge law
recovery scheduling
local diagnostics aggregation architecture
RCP-20 comprehensive Node participation
```

```text
N4 Non-preemption
→ PASS BY DESIGN
```

---

# 27. DAD Summary

Material architecture-semantic decisions are persisted separately in:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_node_internal_design_batch_1_dad_evidence_0.0.1.md`

Candidate DAD set:

```text
CID-ND-B1-DAD-001 → 23-responsibility N1/N2/N3 decomposition
CID-ND-B1-DAD-002 → Node bounded readiness model and capability-state non-collapse
CID-ND-B1-DAD-003 → Node Applied Configuration ownership topology
CID-ND-B1-DAD-004 → Attempt origination boundary after Dispatch and before Effect
CID-ND-B1-DAD-005 → Admission/Dispatch consumer applicability without authority transfer
CID-ND-B1-DAD-006 → attended/unattended unified governed execution topology
CID-ND-B1-DAD-007 → protected Effect / local source-fact vs external SoT partition
CID-ND-B1-DAD-008 → Attempt / Effect / Business Outcome permanent non-collapse
CID-ND-B1-DAD-009 → bounded identity/correlation/provenance + non-destructive history
CID-ND-B1-DAD-010 → failure/currentness/offline evidence semantics without recovery design
CID-ND-B1-DAD-011 → RCP-04 / RCP-07 / RCP-08 owner-side stable semantic contracts
CID-ND-B1-DAD-012 → bounded RCP contribution limits and RCP-20 N4 deferral
CID-ND-B1-DAD-013 → Shared Foundation consumption without Product Authority transfer
CID-ND-B1-DAD-014 → typed dependency model and acyclic hard SDD graph
```

All are within current DAD authority and do not alter an Owner-reserved Authority/SoT/Actual-state topology.

---

# 28. MDE Summary

```text
New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Owner-reserved Dimension Changed
→ 0
```

No universal retry/cancellation/rollback/compensation law, once-delivery guarantee, conflict winner, mandatory sandbox/browser framework/queue/broker/scheduler/workflow engine/storage engine/public dependency/provider/protocol/framework lock-in, cross-Tenant Node coordination, global priority/fairness law or major identity namespace is selected.

---

# 29. Candidate Audit Summary

Detailed evidence is persisted separately in the Review / Audit artifact. Candidate-level result:

```text
N1 Internal Responsibility Coverage
→ COMPLETE / 7

N2 Internal Responsibility Coverage
→ COMPLETE / 9

N3 Internal Responsibility Coverage
→ COMPLETE / 7

ND-R01 / ND-R02 / ND-R03 Traceability
→ COMPLETE

Authority / SoT / Actual-state Ambiguity Introduced
→ 0

RCP-04 Owner-side Closure
→ COMPLETE AT CURRENT DESIGN LEVEL / FULL CROSS-COMPONENT NOT CLAIMED

RCP-07 Owner-side Closure
→ COMPLETE AT CURRENT DESIGN LEVEL

RCP-08 Owner-side Closure
→ COMPLETE AT CURRENT DESIGN LEVEL

RCP-20 / N4 Preemption
→ 0

Hard Internal SDD Graph
→ ACYCLIC

Unresolved SDD Cycle
→ 0

Missing Mandatory Shared Foundation Semantic
→ 0

Implementation Leakage
→ 0

Unauthorized Downstream Progression
→ 0

MDE Required
→ 0
```

---

# 30. Candidate Status / Stop Boundary

```text
NGRP-001 — Component Internal Design / ns_node / Batch 1

N1 / N2 / N3 Producing Design
→ COMPLETED

Maximum Legal State
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE

ns_node Batch 1 Global Acceptance
→ NOT CLAIMED

ns_node Component Internal Design Global Closure
→ NOT CLAIMED

ns_node Internal Design Exhaustion
→ NOT CLAIMED

N4 / ND-R04
→ NOT AUTHORIZED / NOT DESIGNED

ns_node Batch 2
→ NOT AUTHORIZED

ns_agent / ns_web / SDK / Implementation
→ NOT AUTHORIZED
```

```text
STOP AFTER PERSISTED HANDOFF
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
→ FOR INDEPENDENT GLOBAL ACCEPTANCE REVIEW
```
