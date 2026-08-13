# NGRP-001 — Runtime Responsibility Architecture / Batch 1 DAD Evidence

## Metadata

- Scope: `RUNTIME_RESPONSIBILITY_ARCHITECTURE_ONLY / BATCH_1 / RUNTIME_ROLE_INTERACTION_TOPOLOGY_AND_EXECUTION_RESPONSIBILITY_SYNTHESIS`
- Repository/Branch: `J-LittleSunshine/ns_evermore` / `architecture/ns-evermore-genesis-0.0.1`
- Entry HEAD: `6d370927bbc65245bf62c72e220b2030812b83ce`
- Primary Candidate Commit: `2060382e403cee66f428834bfc9f34f876089579`
- Authority: producing-session DAD only; Global Acceptance not claimed.

All decisions below are direct refinements of accepted Product Architecture, Owner/MDE semantics and the 34 accepted boundaries. They do not move Authority/SoT to another component, change Tenant/Organization/Principal/Trust semantics, select a material offline fail policy, or freeze a provider/protocol/storage/physical identity format.

---

## RRA-B1-DAD-001 — 22-role Runtime Taxonomy

**Decision:** derive 22 behavioral Runtime Roles: `ns_server 9 / ns_runtime 4 / ns_node 4 / ns_agent 4 / ns_web 1`. Runtime Role is distinct from Product Component, Internal Boundary, Runtime Role Instance, process/service/worker/thread/coroutine/container/deployment.

**Basis / Why DAD:** exact Runtime Responsibility Architecture scope plus fixed five-component and 34-boundary baseline; no MDE dimension changes.

**Preservation:** each role stays inside an accepted hosting component/boundary responsibility; same bounded Actual-state assertion keeps one final owner.

**Non-implication / Deferral:** no role-per-process or deployment mapping; realization → later Component Internal Design.

**Revalidate:** role becomes a sixth component or physical placement is used as semantic authority.

---

## RRA-B1-DAD-002 — ns_server Runtime Partition Refinement

**Decision:** `SV-R01 S5 Business Application Runtime`, `SV-R02 S6 Automation Runtime Semantic`, `SV-R03 S7 Data/ETL Runtime`, `SV-R04 S8 Admission`, `SV-R05 S9 Managed Desired Config`, `SV-R06 S10 Server-local Background`, `SV-R07 S11 Human Task Aggregation/Response Routing`, `SV-R08 S12 Notification/Delivery`, `SV-R09 S13 Discovery Projection`. S1-S4 remain governance context authorities without independent runtime roles.

**Basis / Why DAD:** Project Architecture already places Business Application runtime/Data backend in `ns_server`; Z3-DAD-009 explicitly leaves applicable trial facts to `S10/N2-N3/A2/later runtime partition`; S6/S11 accepted HITL semantics require an Automation runtime source. This closes those role-level partitions without moving component ownership.

**Preservation:** Definition SoT stays S5/S6/A1 as accepted; external Data facts retain external owners; Admission stays S8; Desired stays S9; Notification/Discovery remain derived partitions.

**Non-implication / Deferral:** no backend/workflow/ETL/task/notification/search engine or process design; mechanics → later Component/Contract/Provider authority.

**Revalidate:** any accepted domain Authority/SoT/Actual-state owner moves.

---

## RRA-B1-DAD-003 — Four Distinct ns_runtime Roles

**Decision:** keep `RT-R01 Presence`, `RT-R02 Scheduling/Routing/Dispatch`, `RT-R03 Continuation/Delegation/Intervention`, `RT-R04 Recovery/Reconciliation` as four distinct roles.

**Basis / Why DAD:** R1-R4 own different bounded coordination facts and lifecycles; combining them would create an unnecessary universal runtime-manager responsibility.

**Preservation:** connection != Trust/Admission; dispatch != attempt; intervention request != outcome; recovery coordination != source fact/conflict winner.

**Non-implication / Deferral:** four roles do not mean four processes/services/endpoints; algorithms/transport/process mapping later.

**Revalidate:** any R role becomes Product Authority, universal Runtime SoT or executor/effect owner.

---

## RRA-B1-DAD-004 — Node Role Split; Attended/Unattended as Modes

**Decision:** `ND-R01 N1 Readiness`, `ND-R02 N2 Governed Local Execution`, `ND-R03 N3 Protected Effect`, `ND-R04 N4 Offline/Recovery`. `ATTENDED` and `UNATTENDED` are governed modes of ND-R02, not different roles. N2 attempt and N3 effect are never merged.

**Basis / Why DAD:** Owner evidence explicitly selected both modes under one local-execution responsibility model; Z3-DAD-003/013 fixes N1-N4 ownership.

**Preservation:** user presence is not IAM/Policy/Trust/Admission bypass; unattended is not unrestricted authority; stop != effect reversal.

**Non-implication / Deferral:** no session/process/browser-profile/concurrency/persistence model.

**Revalidate:** mode product decision changes, N2/N3 collapse, or material offline authority policy changes.

---

## RRA-B1-DAD-005 — Agent Runtime Decomposition

**Decision:** `AG-R01 A2 Agent Runtime + A4 consumption`, `AG-R02 A3 Provider Mediation`, `AG-R03 A5 Multi-Agent Composition`, `AG-R04 A6 Cross-domain Delegation/Automation Participation`. A1 remains definition authority without an independent runtime role.

**Basis / Why DAD:** accepted A1-A6 responsibilities and native Multi-Agent/Agent→Node/Agent→Automation capabilities directly require these cohesive runtime responsibilities.

**Preservation:** each Agent keeps its own A2 facts; AG-R03 owns only composition coordination; AG-R04 never owns Node effects or Automation state; provider/tool never gains Agent authority.

**Non-implication / Deferral:** no Agent framework/supervisor/graph/actor/shared-memory/provider-routing design.

**Revalidate:** Agent Authority moves or ephemeral Agent Automation bypass is introduced.

---

## RRA-B1-DAD-006 — One ns_web Interaction/Projection Role

**Decision:** W1-W7 are runtime-facing through one `WB-R01 Governed Human Interaction & Projection Participant`; this is not a backend/process claim.

**Basis / Why DAD:** every W boundary shares the invariant that UI submits intent/projects facts but does not own the underlying semantic/runtime state; W3 additionally owns only Human Response submission occurrence.

**Preservation:** UI command != outcome; dashboard != Runtime SoT; browser session != operation owner; task UI != HITL state owner.

**Non-implication / Deferral:** no frontend framework/state-manager/API/process topology; internal design later.

**Revalidate:** ns_web gains underlying Product/Runtime authority.

---

## RRA-B1-DAD-007 — HITL Runtime Topology

**Decision:** Automation wait/applicability/resume is owned by SV-R02; Agent wait/applicability/resume by AG-R01; SV-R07 owns unified aggregation/projection/routing; WB-R01 owns response-submission occurrence; RT-R03 only coordinates cross-component resume where needed.

**Basis / Why DAD:** accepted HITL, Human Task Inbox, S6/A2/S11/W3/R3 and Z3-DAD-006 explicitly defer runtime wait/resume closure to this phase.

**Preservation:** submitted != applied; Human Response != Policy Permit/Artifact Acceptance/Admission; Inbox != Runtime SoT.

**Non-implication / Deferral:** no task schema/assignment/timeout/state-machine/queue/resume protocol.

**Revalidate:** projection becomes source authority or human response becomes governance authority.

---

## RRA-B1-DAD-008 — Governed Trial Uses Existing Domain/Runtime Owners

**Decision:** no universal Trial Role/Engine. Business App trial uses S5/SV-R01; Automation uses S6/SV-R02 plus actual executor; Agent uses A1/AG-R01; Data/ETL uses S7/SV-R03. Actual effects remain with their normal source owner.

**Basis / Why DAD:** Owner-selected Governed Pre-production Trial covers all four domains but rejects universal fully isolated simulation; Z3-DAD-009 already fixes semantic-owner vs actual-executor separation.

**Preservation:** Validation != Trial; Trial success != Artifact Acceptance/Production Admission; Trial != Production; dry-run != effect-free automatically.

**Non-implication / Deferral:** no sandbox/VM/container/mock/universal test runner/deterministic replay guarantee.

**Revalidate:** Trial becomes universally effect-free/deterministic or success becomes acceptance/admission.

---

## RRA-B1-DAD-009 — Intervention and Recovery Separation

**Decision:** preserve `request intent → coordination-stage request state → final actual-owner outcome`. WB/SDK may request; RT-R03 owns coordination-stage facts; actual operation/executor owns final intervention outcome; RT-R04 owns only coordination recovery/reconciliation facts; source owners retain facts through reconnect.

**Basis / Why DAD:** Governed Operation Intervention Owner decision, Z3-DAD-010 and R3/R4/N4 semantics.

**Preservation:** Cancel Requested != Cancelled; Retry Requested != Retry Started; Resume Requested != Resumed; Recovery Requested != Recovered; reconnect != reconciled; stopped != effects reversed; latest timestamp != canonical winner.

**Non-implication / Deferral:** no universal cancel/retry/resume/rollback/exactly-once/reconciliation engine.

**Revalidate:** universal reversal guarantee, material offline fail policy or recovery-based authority transfer.

---

## RRA-B1-DAD-010 — Runtime Identity/Correlation and Contract Pressure

**Decision:** distinguish Role vs Role Instance, participant/participation where needed, operation vs attempt, dispatch/effect correlation, Agent delegation/Multi-Agent lineage, Automation parent/callee lineage, Human Task response, intervention, trial, Notification delivery and recovery correlation. Record 24 stable runtime contract pressures. No physical identifier or wire representation is selected.

**Basis / Why DAD:** accepted language-neutral cross-boundary, history/provenance, operation intervention, HITL, trial, notification, recovery and offline semantics require stable correlation.

**Preservation:** identity/correlation carrier never becomes operation owner/Authority; consumer never gains producer authority.

**Non-implication / Deferral:** no UUID/database key/Snowflake ID/hostname/PID/URL/REST/gRPC/WebSocket/JSON/Protobuf/event-envelope choice; representation → later Runtime/Contract Design.

**Revalidate:** a major externally permanent identity namespace/format or incompatible migration commitment is proposed.

---

## Audit Summary

```text
RRA-B1-DAD-001..010 → PERSISTED BY PRODUCING SESSION
DAD Count → 10
New MDE → 0
Open MDE → 0
Unpersisted Owner Decision → 0
Authority / SoT movement → 0
Same-assertion multiple final owners → 0
Provider / protocol / storage lock-in → 0
Material offline fail policy selection → 0
Implementation-defined architecture escape → 0
Global Acceptance → NOT CLAIMED
```
