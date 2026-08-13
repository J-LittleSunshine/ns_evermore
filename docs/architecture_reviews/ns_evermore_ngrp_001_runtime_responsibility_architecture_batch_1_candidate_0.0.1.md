# NGRP-001 — Runtime Responsibility Architecture / Batch 1 Candidate

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Runtime Responsibility Architecture / Batch 1`
- Authorization: `RUNTIME_RESPONSIBILITY_ARCHITECTURE_ONLY / BATCH_1 / RUNTIME_ROLE_INTERACTION_TOPOLOGY_AND_EXECUTION_RESPONSIBILITY_SYNTHESIS`
- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Recovered Entry HEAD: `6d370927bbc65245bf62c72e220b2030812b83ce`
- Recovered Global State: `GAC-EPOCH-0026`
- Project Architecture: `docs/ns_evermore_project_architecture_0.0.3.md`
- Decision Registry: `docs/governance/decisions/ns_evermore_decision_registry_0.0.10.md`
- Producing-session authority: bounded candidate production only; no Global Acceptance authority.

Runtime Role is an architecture-level behavioral responsibility. It is not automatically a Product Component, internal boundary, process, service, worker, thread, coroutine, container, pod, host or deployment unit.

---

## Repository Recovery

```text
Actual Branch HEAD
→ 6d370927bbc65245bf62c72e220b2030812b83ce

State Verified Through HEAD
→ e875e58805bddba9c180c41ee2290e6fc9bdbebf

Delta
→ one commit: 6d370927bbc65245bf62c72e220b2030812b83ce
→ EXPECTED_GOVERNANCE
```

The delta only authorizes this exact Batch at `GAC-EPOCH-0026`; it does not modify accepted Project Architecture, Owner/MDE decisions or the 34-boundary baseline.

Recovery Gate:

```text
Architecture Constraint Derivation → GLOBAL_CLOSED / COMPLETE
Project Architecture Synthesis → GLOBAL_CLOSED / COMPLETE
Project Architecture 0.0.3 → GLOBAL_ACCEPTED / NORMATIVE / CURRENT
Accepted NSE → NSE-001..017
Accepted Z2 DAD → Z2-DAD-001..041
Accepted Z2 MDE → Z2-MDE-001..017
Z3 Batch 1/2/3 → GLOBAL_ACCEPTED
Accepted Z3 DAD → Z3-DAD-001..014
Accepted Internal Boundaries → 34 / 34
Internal-boundary Exhaustion → SATISFIED
Runtime Responsibility Architecture Readiness → SATISFIED
Open MDE → 0
Unpersisted Owner Decision → 0
Missing Product Capability → 0
Blocking Item → NONE
Unexpected Drift → NONE
Unauthorized Progression → NONE
Recovery Gate → PASS
```

The Current Required Read Set and precise evidence for Admission, Automation/Agent authority, Runtime Actual-state, Trust, Config Desired/Applied/Observed, Agent→Node, server-local background work, attended/unattended Node, Multi-Agent, HITL, event triggers, Automation composition, Agent candidate Automation authoring, Human Task Inbox, Intervention, Trial, Notification, Source↔Visual interoperability and Discovery were consumed before synthesis.

---

## Runtime Architecture Principles

```text
Authority != Coordination
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Attempt != Protected Effect
Effect != Business Semantic Success automatically
Connected != Trusted != Admitted
Reachable != Ready
Desired != Applied != Observed
Reconnect != Reconciled
Recovery != SoT Transfer
Replay != Retroactive Authorization
```

For the same bounded Actual-state assertion there is exactly one final owner. Projection, aggregation, transport, history, notification, discovery and UI do not transfer ownership.

Runtime Role Identity, Runtime Role Instance Identity, Operation Identity and Attempt Identity are distinct semantic identity pressures. No UUID/database ID/hostname/PID/container ID or other physical format is selected.

---

## 34 Accepted Internal Boundaries → Runtime Responsibility Pressure Map

This map was completed before the role taxonomy was frozen.

| Boundary | Runtime pressure | Result |
|---|---|---|
| S1 Tenant & Principal | governed context propagation | no independent role; consumed by governed roles |
| S2 Organization | org/mapping context + provenance | no independent role; consumed |
| S3 Policy | policy evidence consumption, no Admission collapse | no independent role; consumed |
| S4 Trust | trust evidence consumption; connection/local success not trust | no independent role; consumed |
| S5 Business Application | accepted server backend/runtime + trial requires bounded runtime facts | `SV-R01` |
| S6 Automation | trigger/composition/HITL/semantic continuation runtime responsibility | `SV-R02` |
| S7 Data/Knowledge/ETL | native data/ETL runtime + trial while external SoT preserved | `SV-R03` |
| S8 Artifact/Admission | formal execution-admission producer | `SV-R04` |
| S9 Managed Config | Desired revision/distribution/reconciliation participation | `SV-R05` |
| S10 Server-local Background | local long-running/time-triggered attempt facts | `SV-R06` |
| S11 Human Task | aggregation/freshness/correlation/response routing | `SV-R07` |
| S12 Notification | Notification lifecycle + delivery-attempt owner | `SV-R08` |
| S13 Discovery | projection freshness/completeness/rebuild owner | `SV-R09` |
| R1 Presence | connection/presence/reachability coordination | `RT-R01` |
| R2 Routing/Scheduling/Dispatch | admitted-work coordination | `RT-R02` |
| R3 Continuation/Delegation/Intervention | cross-component continuation/request coordination | `RT-R03` |
| R4 Recovery/Reconciliation | coordination recovery/evidence exchange | `RT-R04` |
| N1 Readiness | capability/readiness/mode readiness/applied config | `ND-R01` |
| N2 Local Execution | governed attended/unattended local attempts | `ND-R02` |
| N3 Protected Effect | protected local effect/source-fact custody | `ND-R03` |
| N4 Offline/Recovery | local evidence retention/recovery/diagnostics | `ND-R04` |
| A1 Agent Definition | runtime consumes authoritative Agent revision | no independent role; consumed by AG roles |
| A2 Agent Runtime | Agent context/HITL/Actual-state/trial/intervention | `AG-R01` |
| A3 Provider Mediation | provider/model/multimodal mediation observations | `AG-R02` |
| A4 Tool/Knowledge | consumption must preserve tool/knowledge/effect owners | consumed by `AG-R01`; no separate role |
| A5 Multi-Agent | composition coordination distinct from each Agent state | `AG-R03` |
| A6 Cross-domain Delegation | Agent→Node/Automation/candidate-authoring provenance | `AG-R04` |
| W1 Administration | governed command intent/projection | `WB-R01` |
| W2 Authoring | runtime-facing trial/authoring interaction; no backend authority | `WB-R01` |
| W3 Human Task UI | response-submission occurrence + task interaction | `WB-R01` |
| W4 Notification UI | awareness projection | `WB-R01` |
| W5 Operations/Trial/Intervention | intent + projection | `WB-R01` |
| W6 Discovery UI | query/navigation interaction | `WB-R01` |
| W7 Degraded Experience | explicit stale/unknown/degraded presentation | `WB-R01` |

```text
Coverage → 34 / 34 = 100%
Unmapped → 0
Forced 1:1 boundary-role mapping → NO
```

---

## Mandatory Runtime Journeys → Responsibility Pressure Map

| Journey | Closed pressure sequence |
|---|---|
| A Presence | participant-side observation → RT-R01 coordination presence; Trust/Admission/Readiness separate |
| B Governed work | SV-R04 Admission → RT-R02 schedule/route/dispatch → executor attempt → effect owner |
| C Server-local background | SV-R06 local attempt; ns_runtime only when cross-component work exists |
| D Node attended | ND-R01 attended readiness/session binding → ND-R02 attempt → ND-R03 effect |
| E Node unattended | ND-R01 unattended readiness → same ND-R02/ND-R03 responsibility model |
| F Agent | AG-R01 runtime + AG-R02 provider mediation + A4 consumption |
| G Multi-Agent | AG-R03 composition + separate AG-R01 facts per Agent |
| H Agent→Node | AG-R04 → SV-R04 → RT-R02/03 → ND-R01/02/03 → AG-R01 continuation |
| I Agent→existing Automation | AG-R04 → SV-R02 → SV-R04 → RT/executor → AG-R01 |
| J Agent→candidate Automation | AG-R04 candidate → normal S6 lifecycle → artifact/admission → runtime |
| K Event→Automation | source fact → SV-R02 trigger evaluation → SV-R04 → RT-R02 → executor/effect |
| L Automation A→B | SV-R02 parent/callee lineage → RT-R03/02 as applicable → callee evidence → caller continuation |
| M Automation→Node | SV-R02 → SV-R04 → RT-R02 → ND-R01/02/03 |
| N Agent HITL | AG-R01 wait → SV-R07 → WB-R01 response → SV-R07 → AG-R01 apply/resume; RT-R03 if applicable |
| O Automation HITL | SV-R02 wait → SV-R07 → WB-R01 response → SV-R07 → SV-R02 apply/resume; RT-R03 if applicable |
| P Intervention | WB/SDK request → RT-R03 coordination → actual owner reaction/outcome |
| Q Trial | domain semantic owner → applicable runtime/executor → bounded effect/result → WB/SDK projection |
| R Notification | source owner → SV-R08 lifecycle/delivery → provider evidence → WB projection |
| S Config | SV-R05 Desired → applicable role Applied → WB Observed projection |
| T Reconnect/Reconcile | local retained evidence → RT-R01 reconnect → RT-R04 exchange → each owner re-observes own partition |
| U History/Diagnostics | fact owner produces provenance → aggregators/projectors consume without authority transfer |

No journey requires a sixth Product Component, missing internal boundary or new Owner decision.

---

## Runtime Role Taxonomy

| ID | Runtime Role | Host | Source boundary |
|---|---|---|---|
| SV-R01 | Business Application Runtime Participant | ns_server | S5 |
| SV-R02 | Automation Runtime Semantic Participant | ns_server | S6 |
| SV-R03 | Data / Knowledge / ETL Runtime Participant | ns_server | S7 |
| SV-R04 | Execution Admission Gate Participant | ns_server | S8 + S1-S4 context |
| SV-R05 | Managed Configuration Desired-state Participant | ns_server | S9 |
| SV-R06 | Server-local Background Execution Participant | ns_server | S10 |
| SV-R07 | Human Task Aggregation & Response Routing Participant | ns_server | S11 |
| SV-R08 | Notification Lifecycle & External Delivery Participant | ns_server | S12 |
| SV-R09 | Discovery Projection Participant | ns_server | S13 |
| RT-R01 | Participant Presence Coordinator | ns_runtime | R1 |
| RT-R02 | Governed Routing / Scheduling / Dispatch Coordinator | ns_runtime | R2 |
| RT-R03 | Operation Continuation / Delegation / Intervention Coordinator | ns_runtime | R3 |
| RT-R04 | Coordination Recovery / Reconciliation Participant | ns_runtime | R4 |
| ND-R01 | Node Capability & Readiness Participant | ns_node | N1 |
| ND-R02 | Governed Local Execution Participant | ns_node | N2 |
| ND-R03 | Protected Local Effect Custodian | ns_node | N3 |
| ND-R04 | Node Offline Continuity & Recovery Participant | ns_node | N4 |
| AG-R01 | Agent Runtime Participant | ns_agent | A2 + A1/A4 consumption |
| AG-R02 | Model / Provider Mediation Participant | ns_agent | A3 |
| AG-R03 | Native Multi-Agent Composition Coordinator | ns_agent | A5 |
| AG-R04 | Cross-domain Delegation & Automation Participant | ns_agent | A6 |
| WB-R01 | Governed Human Interaction & Projection Participant | ns_web | W1-W7 |

```text
ns_server → 9
ns_runtime → 4
ns_node → 4
ns_agent → 4
ns_web → 1
Total → 22
```

---

## Runtime Role Definitions

The fields below collectively record purpose, lifecycle, I/O, authority context, owned/non-owned assertions, coordination/execution, HITL/config/secret pressure, offline/recovery/history/compatibility, dependencies, contract pressure, multiplicity, process non-implications, downstream authority and revalidation.

| Role | Purpose / lifecycle / I-O | Owned Actual-state or source fact | Explicitly non-owned | Runtime pressures / non-implications |
|---|---|---|---|---|
| SV-R01 | native Business Application backend runtime + trial; consumes S5 revision, governance/admission/config; emits operation/result/provenance | bounded Business Application runtime facts genuinely originating in server backend | external/Data/Node/Automation/Agent facts and SoTs | multiple operations; integration-secret pressure possible; private/offline uncertainty explicit; no backend framework/process design; revalidate on Business App runtime/Authority movement |
| SV-R02 | Automation initiation, trigger evaluation, composition, HITL wait/resume, semantic continuation/result correlation | Automation semantic runtime state rooted in S6, including Automation wait/resume and composition relationship | Admission, RT dispatch, Node/server-local attempt/effect, Human Task projection | per Automation operation; history keeps revision/parent-callee/trigger/HITL lineage; no DAG/queue/state-machine/process choice; revalidate on S6 authority/capability change |
| SV-R03 | native Data/Knowledge/ETL runtime + trial; consumes mappings/source provenance | native ETL runtime facts and accepted native-derived factual partitions | upstream external factual SoT; discovery index; Agent RAG authority | per operation/trial; connector-secret pressure; stale/partial/conflicting sources explicit; no pipeline/storage engine choice |
| SV-R04 | formal execution-admission decision participation before coordination | S8 admission decision/evidence | Policy/Trust, schedule, readiness, attempt/effect | semantic authority singular at S8, instance count not fixed; bounded pre-issued evidence may be consumed; no service/token/schema choice |
| SV-R05 | Managed Desired-state revision/distribution/reconciliation participation | canonical Desired state only | item semantic authority where elsewhere; Applied; Observed | config != secret; partially-applied/stale explicit; no push/pull/watch/rollout/provider design |
| SV-R06 | continuously available long-running/time-triggered server-local execution | S10 server-local attempt/progress/outcome/source facts | Automation semantic state; cross-component scheduling; Node/Agent facts | multiple attempts; independent-lifetime/continuous-availability pressure only; retry preserves attempts; no worker/scheduler/process model |
| SV-R07 | unified Human Task aggregation, freshness/correlation, response routing | aggregation/projection/routing state only | Automation/Agent wait state, response applicability, Policy/Admission/outcome | cross-session pressure; Human Task origin/principal/revision correlation; no task DB/assignment/state machine/process |
| SV-R08 | Notification existence/history and external delivery participation | S12 Notification lifecycle and delivery-attempt facts | underlying source condition; user observation/resolution; provider authority | per notification/attempt; provider-secret/failure-isolation pressure; offline channel may be pending/unavailable; no queue/retry/provider API choice |
| SV-R09 | governed cross-domain discovery projection maintenance | S13 freshness/completeness/rebuild/staleness | resource semantics/SoT and authorization grant | projection can be stale/partial; private/offline capable; no search/index/ranking technology |
| RT-R01 | long-lived connection/presence/reachability coordination | R1 connection-established/lost and presence/reachability coordination | Trust, Admission, readiness, local participant state | multiple participants; continuous-availability pressure; connection material may be secret; no heartbeat/session table/transport/process design |
| RT-R02 | schedule/route/dispatch already-admitted work | R2 scheduling/routing/dispatch facts | Admission, started attempt, effect/business outcome | per operation/dispatch; pending/unroutable/unknown explicit; no queue/broker/algorithm/worker topology |
| RT-R03 | operation continuation, delegation, HITL resume and intervention request coordination | R3 received/forwarded/pending coordination-stage facts | final cancel/retry/resume/recovery result; Automation/Agent wait state; executor fact | per operation/correlation; request != outcome; no universal cancellation/retry/rollback engine |
| RT-R04 | coordination recovery, evidence exchange, re-observation and reconciliation participation | R4 coordination recovery/health/reconciliation-stage facts | source facts/effects and conflict winner outside R4 | per recovery scope; UNKNOWN/CONFLICTING/PENDING explicit; no latest-timestamp winner/reconciliation algorithm |
| ND-R01 | Node capability/readiness, attended/unattended mode readiness, applied config, participant-side connectivity evidence | N1 installed/available/activated/readiness/applied-config | Admission, Trust, dispatch, execution/effect | `PER_NODE`; attended session-binding pressure may exist; no inventory/session/process design |
| ND-R02 | OCR/desktop/browser/tool/plugin/workflow/package/Automation/Agent-delegated/trial local execution | N2 local execution-attempt state | N3 protected effects, Admission, Automation/Agent semantic state | `PER_ATTEMPT`; ATTENDED and UNATTENDED are modes of same role; attended != governance bypass; unattended != unrestricted authority; no worker/browser-profile/concurrency model |
| ND-R03 | protected local file/device/resource effect/source-fact custody | N3 protected effect/source facts | N2 attempt, broader business success, Policy/Admission | per effect assertion; survives disconnect; stop != reversal; no rollback/effect-adapter design |
| ND-R04 | local evidence retention, offline continuity, recovery and diagnostics | N4 local recovery/diagnostic facts | N1-N3 source facts, R4 coordination truth, broader system truth | `PER_NODE`; durable-evidence pressure only; replay != retroactive admission; no persistence/replay algorithm |
| AG-R01 | Agent runtime/context/reasoning, A4 tool/knowledge consumption, Agent HITL/trial/intervention | A2 Agent runtime/context/HITL/wait/resume/trial facts | provider authority, Knowledge SoT, Node/tool effects, Automation semantics | per Agent runtime/attempt; long-running/HITL pressure; provider/tool secrets possible; no Agent framework/context store/runner design |
| AG-R02 | model/provider/multimodal mediation | A3 bounded provider capability/availability observations produced by mediation | provider's own semantics, Agent definition/runtime outcome | per provider interaction; provider credentials protected; public provider not core correctness dependency; no adapter/routing algorithm |
| AG-R03 | native Multi-Agent interaction/composition coordination | A5 composition coordination/provenance only | each participant Agent's A2 state; Automation/Node effects | per composition operation; partial failure/delegation lineage preserved; no supervisor/graph/actor/shared-memory/parallelism choice |
| AG-R04 | Agent→Node delegation, existing Automation invocation, candidate Automation authoring participation | A6 delegation/invocation/candidate-authoring provenance | Node attempt/effect, Automation SoT/runtime state, Artifact/Admission | per delegation/invocation; unreachable target explicit; candidate possession != acceptance; no physical path/message schema |
| WB-R01 | human intent submission and projection across W1-W7; not a backend-runtime claim | frontend interaction/session facts, including Human Response submission occurrence | Product authority/SoT, runtime outcome, HITL applicability, Notification lifecycle, discovery resource, Admission/effect | multiple browser sessions; operation identity independent of session; stale/unknown explicit; no frontend framework/process/API design |

Stable cross-role dependencies are the accepted governance/definition/admission/config evidence plus runtime contracts listed later. Every role preserves Tenant/Organization/Principal/Policy/Trust provenance where applicable and never exposes secret material through ordinary diagnostics or UI.

---

## Runtime Actual-state Ownership Matrix

| Assertion | Final owner |
|---|---|
| Business Application runtime operation | SV-R01 / S5 runtime refinement |
| Automation semantic continuation/composition/HITL wait-resume | SV-R02 / S6 |
| native Data/ETL runtime operation | SV-R03 / S7 runtime refinement |
| formal Admission decision | SV-R04 / S8 |
| Managed Desired config | SV-R05 / S9 |
| server-local background attempt | SV-R06 / S10 |
| Human Task aggregate projection/routing | SV-R07 / S11 |
| Notification lifecycle/delivery attempt | SV-R08 / S12 |
| Discovery projection freshness/completeness | SV-R09 / S13 |
| connection/presence | RT-R01 / R1 |
| schedule/route/dispatch | RT-R02 / R2 |
| continuation/intervention coordination stage | RT-R03 / R3 |
| coordination recovery/reconciliation stage | RT-R04 / R4 |
| Node capability/readiness/applied config | ND-R01 / N1 |
| Node local attempt | ND-R02 / N2 |
| Node protected effect/source fact | ND-R03 / N3 |
| Node local recovery/diagnostic fact | ND-R04 / N4 |
| Agent runtime/context/HITL | AG-R01 / A2 |
| provider mediation observation | AG-R02 / A3 where genuinely produced |
| Multi-Agent composition coordination | AG-R03 / A5; each Agent stays AG-R01 |
| Agent delegation/invocation provenance | AG-R04 / A6 |
| Human response submission occurrence/frontend session | WB-R01 / W3/applicable W boundary |

`Same bounded assertion with multiple final owners → 0`.

S5/S6/S7 role partitions close the explicit later-runtime-partition pressure already left by Project Architecture/Z3-DAD-009; they do not move ownership to another Product Component or make runtime state a Definition SoT.

---

## Source-effect Ownership Matrix

```text
Node Attempt → ND-R02
Node Protected Effect / Local Source Fact → ND-R03
Server-local Attempt / genuine server-local source fact → SV-R06
Agent runtime fact → AG-R01
Automation semantic runtime fact → SV-R02
Notification lifecycle/delivery fact → SV-R08
Discovery freshness fact → SV-R09
Coordination fact → applicable RT-R01..04
Human response submission occurrence → WB-R01
External source fact → its accepted external bounded SoT
Data/ETL derived fact → its accepted bounded factual partition; never upstream external SoT automatically
```

Coordination Fact != Execution Fact != Protected Effect != Business Success automatically.

---

## Connection / Presence Topology

Applicable Node/Agent/server runtime participants maintain their participant side. RT-R01 is the connection acceptor/coordinator at architecture level and owns coordination presence. ND-R01 owns Node-side readiness/connectivity facts; AG-R01 owns applicable Agent-side local observation; source server roles own only their local observations.

```text
Connected != Trusted
Connected != Admitted
Reachable != Ready
Presence != Execution Capability
Reconnect != Reconciled
```

No heartbeat interval, WebSocket message schema, connection library or session table is designed.

---

## Scheduling / Routing / Dispatch Topology

```text
Governed Intent
→ SV-R04 Admission
→ RT-R02 Scheduling
→ RT-R02 Routing
→ RT-R02 Dispatch
→ actual executor Attempt
→ source/effect owner
→ originating semantic continuation owner
```

Presence/readiness are evidence inputs, not Admission substitutes.

---

## Server-local Background Runtime Responsibility

Pure server-local background work is owned/executed by SV-R06 and does not require ns_runtime merely because it is scheduled/time-triggered. If work crosses components, the source server role emits governed intent, SV-R04 applies Admission where applicable, RT-R02/03 coordinate, and the remote executor/source owner retains attempt/effect facts.

---

## Node Attended / Unattended Runtime Responsibility

Owner-selected attended and unattended execution are two modes of `ND-R02`, not two semantic executors.

```text
ATTENDED → ND-R01 may require legitimate user/session-binding readiness
UNATTENDED → no interactive-user presence requirement by mode
Both → same governance/Admission model and N2 attempt owner
N3 → protected effect owner remains separate
```

Attended user presence is not IAM/Policy/Trust/Admission bypass. Unattended is not unrestricted machine authority.

---

## Agent / Multi-Agent Runtime Responsibility

AG-R01 owns each Agent's runtime facts; AG-R02 mediates providers; AG-R03 owns only composition coordination; AG-R04 owns cross-domain delegation/invocation provenance. A4 tool/knowledge consumption occurs under AG-R01 while actual tool/Node/external effects retain their own owners.

Partial Agent failure remains visible per participant. Multi-Agent composition never merges all Agent Actual-state into one source.

---

## Agent → Node Journey

```text
AG-R01 intent
→ AG-R04 delegation provenance
→ SV-R04 Admission
→ RT-R01 presence + ND-R01 readiness evidence
→ RT-R02 schedule/route/dispatch
→ ND-R02 attempt
→ ND-R03 effect/source fact
→ RT-R03 continuation correlation where applicable
→ AG-R04 result correlation
→ AG-R01 continuation
→ WB-R01 projection
```

Agent Delegation != Node Effect Authority Transfer; Runtime Dispatch != Admission; Node Execution != Agent Semantic Authority.

---

## Agent → Automation Journey

Existing Automation:

```text
AG-R01 → AG-R04 governed invocation → SV-R02 Automation semantics → SV-R04 Admission
→ RT-R02/03 + applicable executor → SV-R02 result correlation → AG-R01 continuation
```

Candidate Automation:

```text
AG-R04 candidate authoring → normal S6 canonical definition lifecycle
→ applicable Artifact Acceptance → SV-R04 Admission → normal Automation runtime path
```

No ephemeral Agent flow bypass exists.

---

## Automation / Event / Composition Runtime Responsibility

SV-R02 owns Automation semantic runtime continuation; RT-R02 owns schedule/route/dispatch; RT-R03 owns cross-component continuation-stage facts; actual executor owns attempts/effects.

Event journey:

```text
Event source fact owner
→ SV-R02 input/reference + trigger evaluation
→ execution intent
→ SV-R04 Admission
→ RT-R02 coordination
→ executor/effect owner
→ SV-R02 continuation
```

Composition journey:

```text
Automation A SV-R02
→ governed Automation B reference + parent/callee correlation
→ SV-R04/RT-R03/RT-R02 as applicable
→ callee attempt/effect owner
→ callee semantic result
→ caller SV-R02 continuation
```

Event Received != Admitted; Replay != Retroactive Admission. No broker/topic/DAG/transaction/rollback design.

---

## HITL Runtime Responsibility

Automation:
`SV-R02 wait → SV-R07 aggregate → WB-R01 response submission → SV-R07 route → SV-R02 applicability/apply/resume → RT-R03 only when cross-component resume coordination is needed`.

Agent:
`AG-R01 wait → SV-R07 aggregate → WB-R01 response submission → SV-R07 route → AG-R01 applicability/apply/resume → RT-R03 where applicable`.

```text
Human Response Submitted != Response Applied
Human Response != Policy Permit != Artifact Acceptance != Admission
Inbox != Runtime SoT
```

---

## Operation Intervention Runtime Responsibility

WB-R01/SDK submits governed Cancel/Retry/Resume/Recovery intent. RT-R03 owns only cross-component coordination-stage request facts. The actual operation/executor owns the final outcome. Retry preserves prior-attempt lineage.

```text
Cancel Requested != Cancelled
Retry Requested != Retry Started
Resume Requested != Resumed
Recovery Requested != Recovered
Reconnect != Reconciled
Stopped != Effects Reversed
```

No universal cancellation/retry/resume/rollback engine is introduced.

---

## Governed Trial Runtime Responsibility

| Domain | Trial semantic owner | Runtime participant / final facts |
|---|---|---|
| Business Application | S5 | SV-R01 native trial runtime; external/Node effects stay source-owned |
| Automation | S6 | SV-R02 semantic trial state + applicable SV-R06 or ND-R02/N3 attempt/effect |
| Agent | A1 | AG-R01 Agent trial state; AG-R02/AG-R04/downstream owners as applicable |
| Data/Knowledge/ETL | S7 | SV-R03 native runtime/derived facts; external source facts stay external |

Formal Admission is consumed where applicable to the specific trial execution context; trial success never creates production Admission.

Validation != Trial; Trial Success != Artifact Accepted/Production Admitted; Trial != Production; Dry-run != effect-free automatically. No universal sandbox/test runner is selected.

---

## Notification External Delivery Runtime Responsibility

```text
Source fact owner
→ Notification creation intent/correlation
→ SV-R08 Notification lifecycle
→ SV-R08 delivery attempt
→ external provider evidence
→ SV-R08 delivery-attempt state
→ WB-R01 awareness projection
```

Provider != Product Authority. Notification may exist while a channel is unavailable/pending/failed/indeterminate. Delivery Success != User Observed; Read != Resolved. No provider API/queue/retry algorithm is selected.

---

## Desired / Applied / Observed Runtime Flow

```text
SV-R05 Desired
→ applicable Runtime Role receives intent
→ role applies configuration
→ that role owns Applied assertion
→ observation reads evidence
→ WB-R01 projects Observed
```

Representative Applied owners: server runtime role for its intrinsic config; RT-R01..04 for runtime-coordination config; ND-R01 for Node; AG-R01/02/applicable Agent partition for Agent/provider/tooling; WB-R01 only for genuinely presentation-local config.

Config Distributed != Applied; Observed != Applied SoT; Configuration != Secret.

---

## Runtime Secret Pressure

Authorized runtime material may be needed by server integrations, Data/ETL connectors, notification providers, protected runtime connections, Node tools/resources and Agent providers/tools. This establishes custody pressure only.

```text
Secret Reference != Secret Material
Diagnostic Evidence != Permission to disclose material
WB-R01 != general secret-material custodian
```

No secret-store/encryption/provider technology is chosen.

---

## Offline / Degraded and Recovery / Reconciliation

A disconnected role retains only its own locally established evidence. Remote facts may become `UNKNOWN`, `STALE`, `UNREACHABLE`, `INDETERMINATE`, `CONFLICTING` or `RECONCILIATION_PENDING`. No new fail-open/fail-closed policy is selected.

```text
participant-side reconnect detection + RT-R01
→ RT-R04 recovery/evidence-exchange coordination
→ each source owner re-observes its own partition
→ conflicts remain explicit
→ SV-R07/SV-R08/SV-R09/WB-R01 refresh projections as applicable
```

Reconnect != Reconciled; Recovery != SoT Transfer; Sync != proof of original authority; latest timestamp is not a canonical winner.

---

## Runtime History / Provenance

No universal History Runtime Role is introduced. Each fact owner produces provenance for its own bounded facts. Cross-role stability requires correlation of operation, attempt, dispatch, effect, Agent delegation, Multi-Agent composition, Automation parent/callee, Human Task response, intervention, trial, Notification delivery and recovery/reconciliation, together with applicable revision/governance context.

An aggregator/audit/history view does not become source-fact authority by collection.

---

## Runtime Stable Contract Pressure Inventory

No API/wire/schema is designed.

| ID | Producer → Consumer | Subject | Authority / final owner | Required stability / offline-security-compatibility | Later authority |
|---|---|---|---|---|---|
| RCP-01 | S1-S4 → all roles | Governance Context | server authorities | revision/provenance/Tenant/Principal/security | Contract Design |
| RCP-02 | SV-R04 → executors/RT | Admission Evidence | S8/SV-R04 | applicability/revocation/stale/unknown | Runtime Contract Design |
| RCP-03 | participants ↔ RT-R01 | Presence | RT-R01 coordination fact | participant correlation/freshness; connected != trusted | Runtime Contract Design |
| RCP-04 | ND-R01 → RT/SV/WB | Node Readiness | ND-R01 | capability/config revision; stale/unknown | Runtime Contract Design |
| RCP-05 | RT-R02 → executors | Dispatch Evidence | RT-R02 | operation/dispatch correlation; dispatch != started | Runtime Contract Design |
| RCP-06 | RT-R03 ↔ source roles | Continuation/Intervention | R3 coordination + final source owner | operation/request/attempt lineage | Runtime Contract Design |
| RCP-07 | ND-R02 → consumers | Node Attempt | ND-R02 | attempt/revision/provenance/offline retention | Runtime Contract Design |
| RCP-08 | ND-R03 → consumers | Node Effect Evidence | ND-R03 | attempt/effect correlation; sensitive evidence | Runtime Contract Design |
| RCP-09 | AG-R01 ↔ consumers | Agent Runtime | AG-R01 | Agent revision/operation/attempt | Agent Runtime Contract Design |
| RCP-10 | AG-R02 ↔ AG-R01 | Provider Mediation | AG-R02 bounded observation | provider capability revision; credential-sensitive | Agent Contract Design |
| RCP-11 | AG-R03 ↔ AG-R01 | Multi-Agent Composition | AG-R03 coordination; AG-R01 participant facts | delegation/partial failure lineage | Agent Runtime Contract Design |
| RCP-12 | AG-R04 → SV/RT/ND | Agent Delegation | AG-R04 participant facts | target revision/correlation; no authority transfer | Cross-component Contract Design |
| RCP-13 | SV-R02 ↔ RT/executors | Automation Continuation | SV-R02 semantic state | Automation revision/sub-operation/HITL | Automation Runtime Contract Design |
| RCP-14 | event source → SV-R02 | Event Trigger Input/Evaluation | source fact + SV-R02 evaluation | replay/source provenance/admission separation | Automation Contract Design |
| RCP-15 | SV-R02 ↔ SV/RT | Automation Composition | SV-R02 | parent/callee operation/revision | Automation Runtime Contract Design |
| RCP-16 | SV-R02/AG-R01 ↔ SV-R07/WB | Human Task | source wait owner + S11/W3 bounded facts | task/origin/principal/revision; stale context | HITL Contract Design |
| RCP-17 | domain owner ↔ runtime/WB | Trial | domain semantics + actual executor | trial/revision/context/effect boundary | Trial Contract Design |
| RCP-18 | source → SV-R08/provider/WB | Notification/Delivery | SV-R08 lifecycle | source/delivery attempt; audience/redaction/channel-neutral | Notification Contract Design |
| RCP-19 | SV-R05 ↔ runtime owners | Desired/Applied Config | S9 desired + local applied owner | revision/partial/stale/secret-ref separation | Config Contract Design |
| RCP-20 | source owners ↔ RT-R04 | Recovery/Reconciliation | source owner + R4 coordination | provenance/conflict/no timestamp winner | Recovery Contract Design |
| RCP-21 | resource owners → SV-R09/WB | Discovery | resource owner + S13 projection | domain identity/auth/Tenant/freshness | Discovery Contract Design |
| RCP-22 | all fact owners → WB/SDK | Diagnostics/Provenance | original fact owner | correlation/redaction/history compatibility | Diagnostics Contract Design |
| RCP-23 | SV-R01/SV-R03/SV-R06 → consumers | Server-native Runtime Evidence | corresponding server role | operation/revision/private-offline compatibility | Server Runtime Contract Design |
| RCP-24 | WB/SDK → governed targets | Human/SDK Intent | receiving authority owns semantic outcome | intent/result separation and correlation | Cross-surface Contract Design |

`Runtime Stable Contract Pressure Count → 24`.

---

## Logical Multiplicity and Process Relationship Pressure

- ND-R01/ND-R04: `PER_NODE` semantic pressure.
- ND-R02: `PER_ATTEMPT`; ND-R03: per effect assertion.
- AG-R01: per Agent runtime/attempt; AG-R03: per composition operation; AG-R04: per delegation/invocation.
- server and runtime coordination roles allow multiple logical operations/participants while the same bounded assertion has one final owner.
- WB-R01 allows multiple sessions; operation identity is independent of browser session.

Continuous/lifetime pressure exists for RT-R01/02/03, SV-R06, cross-session SV-R07, provider-failure SV-R08, Node ND-R01/04 and long-running/HITL AG-R01. ND-R02 attended mode may have user-session attachment pressure; unattended mode may have independent-lifetime pressure. None of this implies a process count, daemon, worker pool, replica, thread, coroutine, container or host mapping.

---

## ns_web and SDK Runtime Position

WB-R01 is ns_web's only architecture-level runtime-facing role. UI command is Intent, not runtime outcome. Dashboard is not Runtime SoT. Browser session is not operation owner. Human Task UI is not HITL state owner.

The System-level SDK remains outside the five Product Components and is not a Runtime Role. SDK Trial/Execution/Intervention/Observation/Diagnostics requests enter the same governed role topology. `SDK Request != Admission`; `SDK Local State != Runtime SoT`.

---

## Shared Foundation Pressure — Candidate Only

Candidate reusable pressure: config loading, structured logging/diagnostics, telemetry/health, time/freshness, operation/correlation context, language-neutral serialization, network client mechanics, uncertainty/status primitives, Tenant/Principal context carrier, secret-reference/redaction and compatibility/conformance helpers.

No Foundation capability/module/contract/provider/package/technology is accepted here. Reuse never transfers Authority or Actual-state ownership.

---

## DAD / MDE Summary

Persisted separately as DAD evidence:

```text
RRA-B1-DAD-001 → 22-role taxonomy / non-conflation
RRA-B1-DAD-002 → ns_server S5/S6/S7 runtime partition refinement
RRA-B1-DAD-003 → R1-R4 remain four distinct runtime coordination roles
RRA-B1-DAD-004 → N1-N4 split; attended/unattended are ND-R02 modes; N2/N3 separate
RRA-B1-DAD-005 → Agent A2/A3/A5/A6 runtime decomposition; A1/A4 consumption
RRA-B1-DAD-006 → one ns_web interaction/projection role; no backend/process implication
RRA-B1-DAD-007 → HITL wait/aggregate/submission/applicability/resume topology
RRA-B1-DAD-008 → Trial = domain semantic owner + applicable runtime/executor; no universal engine
RRA-B1-DAD-009 → Intervention/recovery request/coordination/outcome/source-owner separation
RRA-B1-DAD-010 → runtime identity/correlation + 24 stable contract pressures without physical format
```

```text
New MDE → 0
Open MDE → 0
Unpersisted Owner Decision → 0
```

These DADs refine accepted responsibilities; they do not move Authority/SoT/final owner to another accepted domain, change Trust/Tenant/Principal, choose a material offline fail policy, or lock provider/protocol/storage/identity format.

---

## Runtime Semantic Resolution Matrix

| Dimension | Resolution |
|---|---|
| Role Identity | CLOSED: 22 behavioral roles |
| Runtime Instance Identity | CLOSED as distinct concept; concrete representation → named Contract/Component authority |
| Operation / Attempt Identity | CLOSED as distinct correlation requirements; format → Runtime Contract Design |
| Connection / Presence | CLOSED: RT-R01 |
| Authority / Semantic Ownership | CLOSED: upstream unchanged |
| Actual-state / Source-effect | CLOSED: exact matrices above |
| Lifecycle | CLOSED: Admission→Coordination→Attempt→Effect→Projection separated |
| Temporal / Failure / UNKNOWN | CLOSED: revision/provenance + explicit stale/unknown/indeterminate/conflict |
| Tenant / Organization / Principal / Auth / Policy / Trust | CLOSED by S1-S4; runtime only consumes/propagates |
| Configuration | CLOSED: SV-R05 Desired; local Applied; derived Observed |
| Secret pressure | CLOSED at custody-pressure level; provider/store → named later authority |
| Offline / Degraded | CLOSED at responsibility/evidence level; no new material fail policy |
| Recovery / Reconciliation | CLOSED: source owners + RT-R04 coordination |
| Intervention | CLOSED: request/coordination/outcome separated |
| HITL | CLOSED: source wait owner + SV-R07 + WB-R01 + RT-R03 where applicable |
| Trial | CLOSED: domain owner + applicable runtime/executor |
| Compatibility / Migration / Conformance | CLOSED at semantic obligation level; concrete mechanism later |
| Cross-role Dependency | CLOSED by topology/journeys |
| Stable Contract Pressure | CLOSED: 24 named pressures |
| History / Provenance | CLOSED: producing owner remains authoritative |
| Revalidation Trigger | CLOSED per role/DAD and upstream governance |

No `TBD`, `framework handles this`, unnamed deferral or implementation-defined architecture escape remains.

---

## Named Downstream Deferrals

- runtime wire/API/message/schema/identity physical representation → later Runtime/Contract Design;
- process/service/worker/thread/coroutine/container/deployment topology → Component Internal Design / Implementation Planning after authorization;
- queue/broker/topic/subscription/retry/backpressure algorithms → later Component/Provider Design;
- Automation DSL/state machine/DAG/subflow mechanics → Component/Contract Design;
- Agent framework/graph/supervisor/context-sharing/parallelism → Component Internal Design;
- Node process/session/browser-profile/concurrency/sandbox → Component Internal Design;
- Human Task schema/assignment/state machine → Contract/Component Design;
- Notification adapter/provider/retry/credential mechanics → Contract/Provider/Component Design;
- config push/pull/watch/rollout/provider → Contract/Provider/Component Design;
- secret storage/encryption/provider → Shared Foundation/Provider Design only if later admitted;
- discovery index/query/ranking/storage → Component/Provider Design;
- shared logging/telemetry/time/correlation/config helpers → Shared Foundation Architecture only if separately authorized.

---

## Explicit Non-goals

No new Product Component; no Component Internal Design; no Shared Foundation Architecture; no Foundation Contract/Module/Provider design; no implementation planning/IWP/coding; no Django/FastAPI/Celery/Redis/RabbitMQ/Kafka choice; no database/ORM/schema; no REST/gRPC/WebSocket message design; no process/worker/replica/thread/coroutine/container topology; no universal rollback/exactly-once/sandbox promise.

---

## Audit Results / Candidate Status

Detailed audit evidence is in `docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_review_audit_0.0.1.md`.

```text
Runtime Role Taxonomy → COMPLETE
Runtime Role Definitions → COMPLETE
34-boundary Coverage → 100%
Unmapped Boundary → 0
Mandatory Journeys A-U → CLOSED
Authority Ambiguity → 0
SoT Ambiguity → 0
Actual-state Ownership Ambiguity → 0
Source-effect Ownership Ambiguity → 0
Open MDE → 0
Unpersisted Owner Decision → 0
Missing Product Capability / Boundary → 0
Unnamed Deferral → 0
Implementation-defined Escape → 0
Component Internal Design Leakage → 0
Shared Foundation Detailed-design Leakage → 0
Implementation Planning Leakage → 0
```

```text
NGRP-001 Runtime Responsibility Architecture / Batch 1
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This producing-session status is not Global Acceptance, does not declare Runtime Responsibility Architecture globally closed/exhausted/ready, does not advance GAC Epoch and does not authorize another Batch, Shared Foundation Architecture, Component Internal Design or implementation.
