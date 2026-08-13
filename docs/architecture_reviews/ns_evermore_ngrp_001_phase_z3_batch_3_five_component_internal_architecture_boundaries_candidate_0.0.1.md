# ns_evermore NGRP-001 Phase Z3 / Batch 3 — Five-component Internal Architecture Boundaries Candidate

## Authority Metadata

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 3`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_3 / COMPONENT_INTERNAL_BOUNDARY_SYNTHESIS`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `dca0cdcbc59e4d9945f30a1abbf6fcbf732ec551`
- **Recovered Global State:** `GAC-EPOCH-0024`
- **Document Version:** `0.0.1`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `PRODUCING_SESSION_ARCHITECTURE_CANDIDATE`
- **Global Acceptance:** `NOT CLAIMED`
- **Next Phase Authorization:** `NONE`

This document defines architecture-level responsibility / custody / semantic boundaries **inside** the five already-fixed Product Components. It does not define modules, packages, Django Apps, Vue packages, classes, services, processes, workers, containers, deployment units, schemas, APIs, wire formats, runtime-role taxonomy, Shared Foundation modules/providers, or implementation plans.

---

# 1. Repository Recovery

## 1.1 Recovery result

```text
Repository
→ J-LittleSunshine/ns_evermore

Branch
→ architecture/ns-evermore-genesis-0.0.1

Actual Branch HEAD at recovery
→ dca0cdcbc59e4d9945f30a1abbf6fcbf732ec551

Global State
→ GAC-EPOCH-0024

State Verified Through HEAD
→ 8e972b082fc1c8be461a717c8399ecdfeb5bb3a8

Delta
→ 8e972b082fc1c8be461a717c8399ecdfeb5bb3a8
  ..
  dca0cdcbc59e4d9945f30a1abbf6fcbf732ec551

Delta commit count
→ 1

Changed file
→ docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md

Delta classification
→ EXPECTED_GOVERNANCE

UNAUTHORIZED_PROGRESSION
→ NONE

UNEXPLAINED_DRIFT
→ NONE
```

The delta is the GAC transition that records capability-exhaustion/readiness closure and authorizes Z3 Batch 3. No implementation, runtime architecture, Component Internal Design, Shared Foundation Architecture, or other unauthorized progression is present in the recovered delta.

## 1.2 Recovery Gate

| Gate | Recovered result |
|---|---|
| Architecture Constraint Derivation | `GLOBAL_CLOSED / COMPLETE` |
| Project Architecture Synthesis | `GLOBAL_CLOSED / COMPLETE` |
| Current Project Architecture | `0.0.3 / GLOBAL_ACCEPTED / NORMATIVE / CURRENT` |
| Accepted NSE | `NSE-001..017` |
| Accepted Project Architecture DAD | `Z2-DAD-001..041` |
| Accepted Z2 Owner MDE | `Z2-MDE-001..017` |
| Current Decision Registry | `0.0.9 / CURRENT / NORMATIVE` |
| Z3 Batch 1 | `GLOBAL_ACCEPTED` |
| Z3 Batch 1 Capability Baseline | `GLOBAL_ACCEPTED / NORMATIVE` |
| Z3 Batch 2 | `GLOBAL_ACCEPTED` |
| Z3 Batch 2 Interaction Experience Baseline | `GLOBAL_ACCEPTED / NORMATIVE` |
| Z3 Capability Exhaustion | `SATISFIED` |
| Remaining Material Product Capability Pressure | `NONE_FOUND` |
| Five-component Internal-boundary Readiness | `SATISFIED` |
| Open MDE | `0` |
| Unpersisted Owner Decision | `0` |
| Blocking Item | `NONE` |
| Current Authorized Phase | `Z3 / Batch 3` |
| Authorization Scope | `COMPONENT_INTERNAL_BOUNDARY_SYNTHESIS` |

**Recovery Gate Result:** `PASS`.

---

# 2. Accepted Upstream Consumed

This synthesis consumes, without reopening, at minimum:

- `docs/ns_evermore_genesis_constitution_0.0.1.md`;
- `docs/governance/ns_evermore_governance_0.0.2.md`;
- current Global Architecture State and Working State;
- `docs/governance/decisions/ns_evermore_decision_registry_0.0.9.md`;
- `docs/ns_evermore_nse_constraints_index_0.0.5.md` as promoted by current Global State;
- `docs/ns_evermore_project_architecture_0.0.3.md`;
- Z3 Batch 1 capability candidate and Global Acceptance evidence;
- Z3 Batch 2 interaction-experience candidate and Global Acceptance evidence;
- Z3 capability-exhaustion / internal-boundary-readiness assessment;
- relevant Global Architecture Ledger tail;
- exact decision evidence needed for boundary synthesis, including `Z2-MDE-007`, `008`, `009`, `010`, `014`, `015`, `016`, `017`, accepted Z3 Batch 1 Owner capability decisions, and accepted Z3 Batch 2 Owner capability/MDE decisions.

The current accepted Authority / SoT topology is inherited, not re-derived here.

---

# 3. Boundary Synthesis Principles

The following rules are normative for this candidate:

```text
Internal Architecture Boundary
!= Module
!= Package
!= Django App
!= Vue Package
!= Class
!= Service
!= Process
!= Worker
!= Container
!= Database Schema
!= Deployment Unit

Boundary Independence
!= Runtime Isolation

Same Product Component Placement
!= Same Semantic Authority

Projection / Aggregation
!= Source Authority

Coordination
!= Execution Authority

Local Execution
!= Admission Authority

Desired
!= Applied
!= Observed

Secret Reference
!= Secret Material

Reconnect
!= Reconciled

Trial Success
!= Artifact Acceptance
!= Production Admission

Human Response
!= Policy Permit
!= Artifact Acceptance
!= Execution Admission
```

Boundary count is derived from semantic cohesion, accepted authority topology, state ownership, lifecycle responsibility and downstream design value. It is not normalized across Product Components.

---

# 4. Accepted Capability → Component Responsibility Map

| Accepted material capability / pressure | Primary component responsibility | Supporting component responsibility | Authority / ownership preservation |
|---|---|---|---|
| Tenant semantics / canonical Tenant SoT | `ns_server` | all components consume Tenant context | Authority/SoT remain `ns_server` |
| Native IAM / Principal semantics | `ns_server` | all components consume Principal/auth evidence | IAM Authority remains `ns_server` |
| Native Organization semantics | `ns_server` | all components carry Organization context where applicable | Tenant and Organization remain non-collapsed |
| Unified Policy / authorization semantics | `ns_server` | runtime/node/agent/web enforce or project decisions | Policy Authority remains `ns_server` |
| Platform Security / Trust semantics | `ns_server` | runtime/node/agent/web consume/enforce/report evidence | Trust Authority remains `ns_server` |
| Business Application complete source + visual authoring | `ns_server` domain semantics + `ns_web` visual + SDK source | trial/operation participants as applicable | Definition Authority/SoT remain `ns_server` |
| Automation complete source + visual authoring | `ns_server` domain semantics + `ns_web` visual + SDK source | runtime/node/agent execution participation | Automation Authority/SoT remain `ns_server` |
| Agent complete source + visual authoring | `ns_agent` domain semantics + `ns_web` visual + SDK source | server governance dependencies | Agent Authority/SoT remain `ns_agent` |
| Data / Knowledge / ETL complete source + visual authoring | `ns_server` domain semantics + `ns_web` visual + SDK source | external factual owners preserved | semantic authority remains `ns_server`; bounded factual SoT preserved |
| Formal Artifact Acceptance | `ns_server` | web/SDK may initiate/review; domains provide certification evidence | Acceptance Authority remains `ns_server` |
| Formal Execution Admission | `ns_server` | runtime/node/agent consume admission evidence | Admission Authority remains `ns_server` |
| Managed runtime desired configuration | `ns_server` | every component owns applicable bootstrap/applied partition | Desired SoT remains `ns_server`; item semantics follow capability owner |
| `ns_server` server-local background work | `ns_server` | web observes; runtime not required by placement | server-local actual-state remains server-owned partition |
| Agent → Node governed delegation | `ns_agent` delegation semantics + `ns_node` execution | `ns_runtime` may coordinate admitted work | Agent does not gain Node effects; Node does not gain Agent semantics |
| Node attended execution | `ns_node` | web/HITL surfaces where applicable | user presence does not bypass IAM/Policy/Admission |
| Node unattended execution | `ns_node` | runtime coordination where applicable | unattended mode does not create unrestricted authority |
| Native Multi-Agent composition | `ns_agent` | runtime coordination only where later applicable | Agent Authority remains `ns_agent` |
| Native Multimodal Agent semantics | `ns_agent` | model/provider capability mediation | provider/model never becomes Agent Authority |
| Automation + Agent governed HITL | `ns_server` Automation domain + `ns_agent` Agent domain | `ns_web` Human Task interaction; runtime/node continuation participation | human response never becomes Policy/Acceptance/Admission Authority |
| Governed event-driven Automation | `ns_server` Automation domain | runtime/node as execution participants; event producers preserve provenance | event occurrence never implies admission |
| Reusable Automation → Automation composition | `ns_server` Automation domain | runtime/node execute applicable admitted composition | composition does not transfer Automation Authority |
| Agent selects/invokes Automation | `ns_agent` cross-domain participation + `ns_server` Automation semantics | runtime/node later execution | invocation never transfers Automation Authority |
| Agent dynamically authors candidate Automation | `ns_agent` authoring participant → `ns_server` Automation definition lifecycle | web/SDK may observe/edit after canonical intake | candidate must enter normal Automation governance |
| Node local OCR / desktop / browser / tool / plugin / workflow execution | `ns_node` | server/runtimes provide governance/coordination context | local effect/source fact remains node-owned bounded fact |
| Agent context / memory / tools / RAG / provider mediation | `ns_agent` | source domains/providers remain authoritative for their facts | consumption never transfers Knowledge/Tool/Provider Authority |
| Revision / evolution / compatibility / migration / conformance | each semantic owner for owned subject | web/SDK project feedback; runtime/node/agent provide conformance evidence | no universal compatibility authority introduced |
| Audit / provenance / diagnostics | each fact/effect owner produces evidence | web projects; server/runtimes may aggregate only as projection | evidence aggregation never canonicalizes source facts |

**Accepted Capability Coverage:** `100%`.

**Unmapped Accepted Capability:** `0`.

---

# 5. Accepted Interaction Capability → Component Responsibility Map

| Accepted interaction capability | Semantic source / owner | Interaction / projection | Runtime / source-fact participation | Governance / dependency closure |
|---|---|---|---|---|
| Source ↔ Visual bidirectional semantic interoperability | applicable domain owner (`ns_server` or `ns_agent`) | `ns_web`; System-level SDK/source surface | none by authoring placement | unsupported/non-editable/representation-limited state must be explicit; no silent semantic loss |
| Unified Governed Human Task Inbox | originating Automation/Agent HITL semantics | `ns_web` unified Human Task surface | originating runtime partition owns actual wait/resume facts; web owns only interaction submission fact | `ns_server` provides cross-domain governed aggregation/projection custody without becoming task-source authority |
| Governed Operation Intervention | operation-specific semantic/actual owner | `ns_web`/SDK request surface | `ns_runtime` coordinates where applicable; actual executor/owner establishes outcome | requested != achieved; capability-specific support |
| Governed Pre-production Trial | applicable definition domain owner | `ns_web`/SDK trial interaction | applicable runtime/node/agent/server partition produces trial facts/effects | trial remains pre-production and separate from Acceptance/Admission |
| Unified Governed Notification | originating source facts remain with source owner | `ns_web` awareness/history surface | `ns_server` notification lifecycle owns notification/delivery-attempt partition only | Notification != source fact/current state |
| Pluggable external notification delivery | `ns_server` notification lifecycle semantic custody | external channels are delivery endpoints, not Authority | provider delivery attempt facts belong notification delivery partition | Feishu/WeCom/SMS are target directions; no provider is core correctness dependency |
| Unified governed cross-domain discovery | contributing domain owners preserve resource identity | `ns_web`/SDK consume unified discovery | `ns_server` discovery projection owns only projection freshness/completeness state | discovery/index != resource SoT; Tenant/Principal/Policy filtering required |
| Internationalization / localization | underlying product semantics remain language-neutral | `ns_web` experience semantics; SDK surface language-neutral | no runtime authority transfer | locale != Tenant/Principal/timezone |
| Accessibility for critical workflows | underlying workflow semantics unchanged | `ns_web` experience boundary | no runtime authority transfer | accessible path must preserve same governed action meaning |
| Async operation identity / history / return-later | owning operation partition | `ns_web`/SDK project durable operation reference/history | source operation owners produce facts | browser session is never durable operation owner |
| Layered diagnostics / explainability | each source/effect/coordination owner | `ns_web` diagnostic projection | server/runtime/node/agent produce bounded evidence | raw hidden reasoning is not required; redaction/authorization preserved |
| Authorized provenance | source/effect owner | `ns_web`/SDK projection | all execution/governance boundaries produce provenance | provenance presentation does not transfer authority |
| Desired / Applied / Observed | desired=`ns_server`; applied=runtime partition | `ns_web` projection | runtime/node/agent/server partition produces applied evidence | permanent three-way distinction |
| Revision / history / semantic diff | definition semantic owner | `ns_web`/SDK | execution history references applicable revision | current definition never rewrites historical interpretation |
| Offline / degraded / unknown-state interaction | applicable source owner | `ns_web` explicit stale/unknown/degraded projection | node/agent/runtime/server retain bounded evidence locally where authorized | no fail-open/fail-closed decision invented |
| Cross-surface semantic consistency | underlying semantic owner | `ns_web` + SDK | no authority transfer | same action/status/category must retain meaning across surfaces |
| Authorization/privacy-aware projection | Tenant/IAM/Policy/Trust authorities remain `ns_server` | `ns_web`/SDK filter/project only authorized information | source components provide bounded evidence | UI visibility/search result never grants authorization |

**Accepted Interaction Capability Coverage:** `100%`.

**Unmapped Accepted Interaction Capability:** `0`.

---

# 6. Boundary-level Semantic Profile Rules

Every boundary below explicitly resolves the following dimensions at Component-boundary level:

```text
Purpose
Accepted Capability Custody
Owned Semantic Authority
Canonical SoT Responsibility
Consumed Authority / Governance Context
Actual-state Responsibility
Source-fact Responsibility
Human Interaction / Projection Responsibility
Tenant Context
Organization Context
Principal / IAM Context
Policy Context
Trust / Security Context
Configuration Participation
Secret Reference / Secret Material Custody Pressure
Offline / Degraded Responsibility
Failure / Unknown / Indeterminate Responsibility
Recovery / Reconciliation Responsibility
Temporal / Historical Responsibility
Compatibility Responsibility
Migration Responsibility
Conformance Responsibility
Extension / Re-delivery Responsibility
Cross-component Dependencies
Stable Contract Pressure
Shared Foundation Pressure (candidate only)
Explicit Non-goals
Forbidden Authority Escalation
Named Downstream Deferrals
Revalidation Triggers
```

Where a boundary says `NONE` for Owned Semantic Authority, this is deliberate and does not create an implementation-defined gap. Its responsibility is projection, coordination, execution, evidence, or derived-state custody under an already-owned semantic subject.

---

# 7. `ns_server` Internal Architecture Boundaries

`ns_server` contains **13** architecture-level responsibility boundaries.

## S1 — Tenant & Principal Identity Governance

- **Purpose / Capability Custody:** native Tenant semantic lifecycle, canonical Tenant state, native IAM/principal semantics, authentication-context interpretation and governed principal binding.
- **Owned Authority / SoT:** Tenant Semantic Authority, Tenant Canonical SoT, Native IAM Semantic Authority; no Organization collapse.
- **State / Source Facts / Projection:** owns authoritative Tenant/IAM governance state; consumes external identity evidence where mapped; projects authorized identity/tenant administration to `ns_web`/SDK.
- **Governance Context:** Tenant is mandatory; Organization remains a separate semantic dimension; Principal/IAM semantics originate here; Policy and Trust decisions are consumed from S3/S4 rather than merged.
- **Configuration / Secrets:** owns semantics of its own identity/Tenant configuration items; managed desired state is through S9; secret references may be produced/consumed for identity integrations, but secret material custody mechanism is deferred.
- **Offline / Failure / Recovery / Temporal:** supports bounded cached/pre-issued/verifiable identity/governance evidence without local authority transfer; UNKNOWN/STALE/UNVERIFIED remain explicit; reconciliation preserves original authority and historical revision.
- **Compatibility / Migration / Conformance / Extension:** owns identity/Tenant semantic compatibility; external identity mapping evolution is explicit; re-delivery/extensions cannot create alternative Tenant/IAM authority.
- **Dependencies / Contracts / Foundation Pressure:** stable Tenant/Principal/Governance Context contracts to all components; candidate shared primitives for context carrier, time, serialization, correlation, secret-reference handling.
- **Non-goals / Forbidden Escalation:** no Organization SoT takeover; no authentication provider becomes IAM Authority; no UI/cache/database placement becomes SoT.
- **Downstream Deferrals / Revalidation:** identity protocol/provider/storage and detailed mapping mechanics → later Component/Internal/Contract/Provider design; revalidate on Tenant/IAM Authority/SoT movement or Tenant/Organization collapse.

## S2 — Organization Semantics & External Mapping Governance

- **Purpose / Capability Custody:** native Organization semantics, structure plurality/extensibility, bounded external Organization mapping and authoritative/factual partition preservation.
- **Owned Authority / SoT:** Native Organization Semantic Authority; Organization factual SoT remains per accepted bounded partition with exactly one final owner for same assertion.
- **State / Source Facts / Projection:** owns native organization-governance facts; external systems may remain factual SoT for mapped attributes; projects governed organization topology without canonicalizing external facts.
- **Governance Context:** Tenant-scoped but never equivalent to Tenant; Principal/Policy/Trust context applies to access and mapping operations.
- **Configuration / Secrets:** organization integration configuration meaning follows this boundary; connection secrets remain Secret Reference/Material-separated.
- **Offline / Failure / Recovery / Temporal:** local copies may be stale/unknown; reconnect/sync does not transfer external SoT; mapping revisions and historical applicability are preserved.
- **Compatibility / Migration / Conformance / Extension:** mapping and structure evolution are compatibility-sensitive; explicit migration when semantic mapping changes; extension cannot invent a parallel Organization Authority.
- **Dependencies / Contracts / Foundation Pressure:** stable Organization Context/mapping contracts to web/runtime/node/agent where needed; reusable serialization/time/error/correlation pressure only.
- **Non-goals / Forbidden Escalation:** no one mandatory org tree; no Tenant==Organization; no external directory automatically becomes platform Organization Authority.
- **Downstream Deferrals / Revalidation:** mapping schema/protocol/storage → later design; revalidate on Organization Authority/SoT topology or Tenant non-collapse changes.

## S3 — Policy & Authorization Governance

- **Purpose / Capability Custody:** unified Policy semantics, authorization decision meaning, policy revision/evolution and decision evidence.
- **Owned Authority / SoT:** Unified Policy Semantic Authority; does not absorb IAM, Trust, Artifact Acceptance or Admission Authority even when co-located in `ns_server`.
- **State / Source Facts / Projection:** owns policy-definition/decision governance state; consumers enforce outcomes and return evidence; `ns_web` only administers/projects.
- **Governance Context:** Tenant, Organization, Principal/IAM and Trust inputs are explicit; policy decision is distinct from authentication and trust.
- **Configuration / Secrets:** policy configuration semantics belong here; managed desired state still governed by S9; no secret material is policy state merely by reference.
- **Offline / Failure / Recovery / Temporal:** bounded pre-issued/verifiable policy evidence may be consumed; missing/stale/indeterminate evidence remains explicit; no generic fail-open/fail-closed rule is introduced.
- **Compatibility / Migration / Conformance / Extension:** policy semantics and historical decision interpretation are compatibility-sensitive; extensions/re-delivery remain subject to the same authority.
- **Dependencies / Contracts / Foundation Pressure:** stable policy-decision/evidence contracts to runtime/node/agent/web; context carrier, temporal, serialization and evidence-verification primitives are candidate foundation pressure only.
- **Non-goals / Forbidden Escalation:** Policy Permit != Artifact Accepted != Execution Admitted; executor/local presence never becomes Policy Authority.
- **Downstream Deferrals / Revalidation:** policy engine/provider/schema/evaluation algorithm → later design; revalidate on Policy Authority movement or material offline decision-policy change.

## S4 — Platform Trust & Security Governance

- **Purpose / Capability Custody:** platform meaning of trusted/untrusted/revoked/unknown/indeterminate, trust evidence interpretation, security-governance relationships.
- **Owned Authority / SoT:** Platform Security / Trust Semantic Authority.
- **State / Source Facts / Projection:** consumes cryptographic/provider/local evidence but owns platform trust interpretation; projects authorized trust/security state to web/SDK.
- **Governance Context:** Tenant/Principal/Policy/Artifact/Admission remain separate authorities; Trust may be a dependency but not a merger.
- **Configuration / Secrets:** trust/security configuration semantics belong here when platform-governance specific; secret references can be governed without selecting material custody technology.
- **Offline / Failure / Recovery / Temporal:** stale/missing/conflicting/unverifiable trust evidence remains explicit; offline locality or successful connection never grants trust; revocation/freshness evidence remains temporal.
- **Compatibility / Migration / Conformance / Extension:** trust semantics are compatibility-sensitive; provider/crypto replacement must preserve conformance; extension origin never implies trust.
- **Dependencies / Contracts / Foundation Pressure:** stable Trust Context/evidence contracts; candidate cryptographic/secret-reference helper pressure remains authority-neutral.
- **Non-goals / Forbidden Escalation:** cryptographically valid != trusted; authenticated != authorized; provider/Foundation never becomes Trust Authority.
- **Downstream Deferrals / Revalidation:** PKI/KMS/HSM/crypto/secret store/protocol details → later authorized design; revalidate on Trust Authority or security-governance topology change.

## S5 — Business Application Definition Lifecycle

- **Purpose / Capability Custody:** Business Application definition semantics, canonical definition lifecycle, complete dual authoring, validation/certification participation, revisions/history/semantic diff and governed trial intent.
- **Owned Authority / SoT:** Business Application Definition / Platform Semantic Authority and Canonical Definition SoT.
- **State / Source Facts / Projection:** accepts semantically valid source/SDK and visual-authored changes into the same canonical semantics; runtime Business Application facts remain with later bounded execution partitions; web is projection/editor, not SoT.
- **Governance Context:** Tenant/Organization/Principal/Policy/Trust apply to authoring and governance; Artifact Acceptance/Admission are consumed from S8.
- **Configuration / Secrets:** application-definition config semantics belong to this domain; secret references may be embedded/associated only as governed references, never secret material by definition placement.
- **Offline / Failure / Recovery / Temporal:** offline authoring/trial must preserve revision/provenance; unsupported/non-editable/representation-limited constructs are explicit; history references applicable revision rather than latest.
- **Compatibility / Migration / Conformance / Extension:** source/visual semantic interoperability is mandatory; compatible evolution vs explicit migration follows accepted compatibility classes; re-delivery source edits remain same semantic domain.
- **Dependencies / Contracts / Foundation Pressure:** stable Definition Lifecycle/Validation/Trial/Revision contracts with `ns_web`/SDK and later runtime participants; reusable serialization/time/conformance pressure only.
- **Non-goals / Forbidden Escalation:** visual editor/source file/accepted artifact/runtime copy never becomes Definition SoT; no mandatory AST/IR/DSL/representation is selected.
- **Downstream Deferrals / Revalidation:** representation/API/module/trial runtime → later Contract/Component/Runtime design; revalidate if Business Application Authority/SoT or source↔visual guarantee changes.

## S6 — Automation Definition, Trigger & Composition Lifecycle

- **Purpose / Capability Custody:** Automation semantic/definition lifecycle; complete dual authoring; explicit/scheduled/event-driven initiation semantics; reusable Automation composition; Automation HITL semantics; Agent-authored candidate Automation intake; revision/history/semantic diff and trial intent.
- **Owned Authority / SoT:** Automation Definition / Workflow Semantic Authority and Automation Canonical Definition SoT.
- **State / Source Facts / Projection:** owns canonical Automation definition/revision and trigger/composition meaning; execution attempt/effect facts remain runtime/node/server-local partitions as applicable; Agent candidate input is authoring participation only.
- **Governance Context:** Tenant/Principal/Policy/Trust plus S8 Artifact/Admission are mandatory; event producer identity/provenance does not create authority.
- **Configuration / Secrets:** Automation semantic configuration belongs here; managed desired runtime config still S9; referenced credentials remain secret references.
- **Offline / Failure / Recovery / Temporal:** event duplicate/replay/stale/unknown conditions must remain distinguishable downstream; offline candidate possession or event receipt never implies admission; attempt lineage is historical.
- **Compatibility / Migration / Conformance / Extension:** Automation revisions, composition dependencies, event semantics and Agent-authored candidates share one compatibility regime; no ephemeral Agent-owned executable-flow class.
- **Dependencies / Contracts / Foundation Pressure:** stable Definition/Trigger/Composition/HITL/Trial contracts to web/SDK/runtime/node/agent; candidate event/status/temporal/correlation primitives only, no broker decision.
- **Non-goals / Forbidden Escalation:** event received != admitted; Agent authoring != Automation Authority; runtime dispatch/local execution != Automation semantics.
- **Downstream Deferrals / Revalidation:** DSL/schema/event envelope/composition runtime/state machine → later design; revalidate on Automation Authority/SoT or accepted trigger/composition/HITL capability change.

## S7 — Enterprise Data / Knowledge / Foundational ETL Governance

- **Purpose / Capability Custody:** first-class Data/Knowledge/ETL definition semantics, complete dual authoring, bounded factual SoT preservation, source integration, revision/evolution, trial and conformance participation.
- **Owned Authority / SoT:** Data / Knowledge / Foundational ETL Semantic Authority; factual SoT remains exactly one final owner per bounded assertion and may be external where accepted.
- **State / Source Facts / Projection:** canonical semantic definitions are server-governed; imported/derived/external facts preserve source provenance and factual-owner identity; Agent RAG consumption never transfers SoT.
- **Governance Context:** Tenant/Organization/Principal/Policy/Trust/privacy controls apply end-to-end.
- **Configuration / Secrets:** connector/source config meaning follows this domain; credential references remain separate from secret material.
- **Offline / Failure / Recovery / Temporal:** source unreachable/stale/partial/unmapped/conflicting facts remain explicit; local copies never replace external SoT; reconciliation is evidence-preserving.
- **Compatibility / Migration / Conformance / Extension:** schema/semantic evolution and mapping changes require explicit compatibility/migration classification; extensions cannot silently canonicalize external data.
- **Dependencies / Contracts / Foundation Pressure:** stable Data/Knowledge/ETL Definition, factual-source provenance and trial contracts; candidate storage/http/cache/serialization/time helpers only.
- **Non-goals / Forbidden Escalation:** ETL result != universal factual SoT; Knowledge consumption != Agent Authority transfer; discovery/search index != Data SoT.
- **Downstream Deferrals / Revalidation:** connector/provider/storage/query/runtime details → later design; revalidate on semantic/factual SoT topology changes.

## S8 — Artifact Acceptance & Execution Admission Governance

- **Purpose / Capability Custody:** formal candidate-artifact acceptance and formal execution-admission gates while preserving them as distinct lifecycle decisions.
- **Owned Authority / SoT:** Formal Artifact Acceptance Authority and Formal Execution Admission Authority, both `ns_server`, with explicit semantic non-collapse.
- **State / Source Facts / Projection:** owns accepted-artifact governance state and admission decision state; domain certification/runtime readiness/local possession are evidence/inputs only; web/SDK may initiate or project decisions.
- **Governance Context:** Tenant/Principal/Policy/Trust plus applicable definition revision are mandatory context; same component placement does not merge these authorities.
- **Configuration / Secrets:** gate configuration semantics belong to applicable gate/capability; secret material is never an artifact/admission fact merely by presence.
- **Offline / Failure / Recovery / Temporal:** pre-issued/bounded admission or acceptance evidence may later support offline consumption without local authority transfer; stale/revoked/unknown applicability stays explicit.
- **Compatibility / Migration / Conformance / Extension:** artifact/admission evidence is revision- and compatibility-sensitive; extension/re-delivery follows same governance.
- **Dependencies / Contracts / Foundation Pressure:** stable Artifact Identity/Acceptance Evidence and Admission Evidence contracts to runtime/node/agent/web/SDK; cryptographic/evidence/time/serialization pressure only.
- **Non-goals / Forbidden Escalation:** certification != acceptance; acceptance != admission; admission != dispatch/attempt; local loadability != acceptance/admission.
- **Downstream Deferrals / Revalidation:** artifact format/token/grant/schema/storage/signing → later Contract/Component/Foundation/Provider design; revalidate on either Authority movement or lifecycle collapse.

## S9 — Managed Runtime Configuration Governance

- **Purpose / Capability Custody:** centralized managed runtime configuration lifecycle, canonical desired-state, revision/history and governed distribution intent.
- **Owned Authority / SoT:** Managed Runtime Configuration Management Authority and Canonical Desired-state SoT; configuration item semantic authority still follows configured capability owner.
- **State / Source Facts / Projection:** owns desired state only; applied state belongs to relevant runtime partition; observed state is projection; distribution receipt does not imply application.
- **Governance Context:** Tenant/Organization/Principal/Policy/Trust govern visibility/change; capability owner defines item meaning.
- **Configuration / Secrets:** this boundary is configuration governance itself; component-local bootstrap remains local; Configuration != Secret and only secret references may be governed here.
- **Offline / Failure / Recovery / Temporal:** desired revision may be known while applied state is stale/unknown/partial; offline component may use permitted locally available state without becoming desired-state Authority; reconciliation compares evidence without retroactive authorization.
- **Compatibility / Migration / Conformance / Extension:** desired-state and item semantics are versioned/compatibility-sensitive; configuration migration preserves owner semantics; extensions cannot create alternative managed configuration authority.
- **Dependencies / Contracts / Foundation Pressure:** stable Desired Configuration Distribution and Applied-state Evidence contracts; shared configuration loader is candidate authority-neutral Foundation pressure.
- **Non-goals / Forbidden Escalation:** desired != applied != observed; loader/storage/UI/distributor != Configuration Authority.
- **Downstream Deferrals / Revalidation:** push/pull/watch/storage/rollout/provider mechanics → later design; revalidate on MDE-016 topology changes.

## S10 — Server-local Background Work & Server Actual-state

- **Purpose / Capability Custody:** continuously available server-local long-running/time-triggered/background responsibilities intrinsic to `ns_server`, including their bounded operation identity, history, diagnostics and intervention participation.
- **Owned Authority / SoT:** no new Product semantic authority; owns only server-local execution Actual-state partitions and source facts genuinely originating here.
- **State / Source Facts / Projection:** final owner for server-local attempt/progress/outcome/source facts; `ns_web` projects; `ns_runtime` is not automatically required or owner.
- **Governance Context:** consumes Tenant/Principal/Policy/Trust/Artifact/Admission/config as applicable; server locality never bypasses its own governance.
- **Configuration / Secrets:** applied configuration for server-local execution belongs to this runtime partition; secret refs/material may be required at runtime under later explicit custody design.
- **Offline / Failure / Recovery / Temporal:** asynchronous identity/history survive web session loss; unknown/partial/intervention/recovery conditions remain explicit; retry preserves prior attempt lineage.
- **Compatibility / Migration / Conformance / Extension:** operation semantics and evidence evolve under accepted compatibility classes; extension jobs cannot bypass admission/policy/trust.
- **Dependencies / Contracts / Foundation Pressure:** operation-history/intervention/diagnostic projection contracts to web/SDK; temporal/correlation/health/logging/telemetry pressure candidate only.
- **Non-goals / Forbidden Escalation:** not replacement for `ns_runtime`; not universal worker/scheduler boundary; background success != business/acceptance/admission authority.
- **Downstream Deferrals / Revalidation:** process/worker/scheduler/concurrency mechanics → Runtime Responsibility Architecture / Component Internal Design; revalidate if responsibility moves outside `ns_server` or becomes universal runtime authority.

## S11 — Unified Human Task Aggregation & Response Routing

- **Purpose / Capability Custody:** cross-domain governed aggregation/projection support for outstanding Automation/Agent HITL work, cross-session rediscovery and response provenance routing.
- **Owned Authority / SoT:** **no underlying Human Task source authority is created here**; Automation HITL meaning remains S6, Agent HITL meaning remains `ns_agent`; this boundary owns only unified aggregation/projection state and its freshness/correlation responsibility.
- **State / Source Facts / Projection:** source task/wait facts remain with originating semantic/runtime owner; `ns_web` owns human interaction submission fact; this boundary correlates/routes governed responses and exposes aggregated task projection, but does not canonicalize execution outcome.
- **Governance Context:** Tenant/Organization/Principal/Policy/Trust and originating execution revision/context are mandatory; Human Response != Policy Permit/Acceptance/Admission.
- **Configuration / Secrets:** task projection preferences/configuration are governed config, not authority; no secret material may be exposed through task context without authorization/redaction.
- **Offline / Failure / Recovery / Temporal:** stale/expired/wrong-context/conflicting/unverified/unreconciled responses remain explicit; offline response possession does not imply application; cross-session visibility derives from governed source evidence, not browser state.
- **Compatibility / Migration / Conformance / Extension:** task correlation semantics must remain stable enough for evolution; source-domain revisions stay authoritative; extension-produced HITL must conform to same governance if admitted.
- **Dependencies / Contracts / Foundation Pressure:** stable Human Task Projection/Response Provenance contracts among S6, `ns_agent`, `ns_web`, applicable runtime partitions; correlation/time/status/redaction helpers are candidate pressure.
- **Non-goals / Forbidden Escalation:** not Notification; not Policy/Approval engine; not task-execution Actual-state owner; no universal assignment/state-machine design.
- **Downstream Deferrals / Revalidation:** concrete identity/schema/assignment/lifecycle/API → later Contract/Component design; wait/resume mechanics → Runtime Responsibility Architecture; revalidate on source-authority or Human Task/Policy collapse.

## S12 — Governed Notification & External Delivery Lifecycle

- **Purpose / Capability Custody:** unified channel-neutral Notification/Awareness lifecycle, in-product history/discoverability and governed external delivery capability with Feishu/WeCom/SMS target directions.
- **Owned Authority / SoT:** no authority over underlying source condition; owns the bounded **Notification lifecycle Actual-state** (notification existence/history and applicable delivery-attempt facts) as a derived awareness partition under `Z2-MDE-014`.
- **State / Source Facts / Projection:** source facts remain with originating owner; `ns_web` projects Notification history/awareness; external providers produce delivery evidence consumed into this bounded delivery partition.
- **Governance Context:** Tenant/audience/Principal/Policy/Trust/privacy/redaction are mandatory; channel/provider is never Authority.
- **Configuration / Secrets:** delivery channel configuration participates in managed config; provider credentials are secret references/material under later custody design and must never be exposed in diagnostics.
- **Offline / Failure / Recovery / Temporal:** Notification may exist while channel is unavailable/unreachable/failed/pending/indeterminate; external delivery failure never erases Notification; read/delivered never rewrites underlying current state.
- **Compatibility / Migration / Conformance / Extension:** notification identity/correlation/history and channel-neutral semantics are compatibility-sensitive; provider adapters remain replaceable; future channels must conform without semantic rewrite.
- **Dependencies / Contracts / Foundation Pressure:** stable Notification Source Correlation, Notification Projection, External Delivery Attempt/Evidence contracts; HTTP client, retry-neutral status, secret-ref, time, telemetry are candidate pressure only.
- **Non-goals / Forbidden Escalation:** Notification != Human Task != source fact != runtime current state; delivered != observed; read != resolved; provider != Authority.
- **Downstream Deferrals / Revalidation:** adapter/API/template/retry/queue/credential storage/state machine → later design; revalidate on channel-neutral guarantee or projection-vs-authority change.

## S13 — Cross-domain Resource Discovery Projection

- **Purpose / Capability Custody:** unified governed cross-domain resource discovery aggregation and navigation reference projection for applicable platform resources.
- **Owned Authority / SoT:** no resource semantic authority; owns only bounded discovery-projection/index Actual-state such as freshness/completeness/rebuild/staleness state.
- **State / Source Facts / Projection:** every result preserves originating domain/type/identity and navigates back to authoritative resource; `ns_web`/SDK consume; source owners remain final resource authorities.
- **Governance Context:** Tenant, Principal, Policy, privacy/redaction filtering is mandatory; unauthorized existence must not leak via counts/snippets/relations.
- **Configuration / Secrets:** discovery configuration semantics are bounded to discovery; no secret material becomes searchable content absent explicit authorization.
- **Offline / Failure / Recovery / Temporal:** stale/partial/unavailable/rebuilding projection is explicit; offline/private discovery remains viable without public SaaS; refresh/rebuild does not canonicalize resources.
- **Compatibility / Migration / Conformance / Extension:** resource type/identity preservation and discovery semantics are compatibility-sensitive; projection technology can migrate independently.
- **Dependencies / Contracts / Foundation Pressure:** stable Discovery Contribution and Discovery Query/Projection contracts; storage/cache/search mechanics remain later; serialization/time/authorization-context pressure candidate only.
- **Non-goals / Forbidden Escalation:** index != registry SoT; result != authorization; freshness != current actual-state guarantee; no universal AI semantic search commitment.
- **Downstream Deferrals / Revalidation:** discoverable category registry/query/index/ranking/storage technology → later design; revalidate if index becomes authoritative or cross-Tenant discovery is proposed.

---

# 8. `ns_runtime` Internal Architecture Boundaries

`ns_runtime` contains **4** architecture-level responsibility boundaries.

## R1 — Connection & Participant Presence Coordination

- **Purpose / Capability Custody:** long-lived communication coordination, connection management, participant presence/connectivity and reachability coordination.
- **Owned Authority / SoT:** no Product semantic authority; owns connection/presence/coordination Actual-state assertions genuinely originating here.
- **State / Source Facts / Projection:** final owner for connection-established/lost and runtime participant reachability coordination facts as defined by this boundary; Node/Agent local state remains their own; web consumes projection only.
- **Governance Context:** carries Tenant/Organization/Principal/Policy/Trust/correlation context without becoming Authority.
- **Configuration / Secrets:** intrinsic runtime connection configuration semantics belong to `ns_runtime`; managed desired state comes from S9; applied state belongs here; connection credentials may require secret material later.
- **Offline / Failure / Recovery / Temporal:** disconnected/unreachable/unknown/stale are explicit; connection loss does not erase source execution facts; reconnect != reconciled.
- **Compatibility / Migration / Conformance / Extension:** participant/connection semantic evolution requires conformance; extension participants cannot redefine governance context.
- **Dependencies / Contracts / Foundation Pressure:** stable Participant Presence/Connectivity contracts; networking/http/websocket specifics deferred; health/correlation/time/telemetry pressure candidate only.
- **Non-goals / Forbidden Escalation:** connection established != trusted/admitted; Communication Hub != universal runtime SoT.
- **Downstream Deferrals / Revalidation:** transport/session/heartbeat/process topology → Runtime Responsibility Architecture/Component Design; revalidate if connection coordination becomes broader Authority.

## R2 — Governed Routing, Scheduling & Dispatch Coordination

- **Purpose / Capability Custody:** capability/availability-aware routing, scheduling and dispatch coordination of already-governed/admitted work.
- **Owned Authority / SoT:** no Automation/Agent/Artifact/Admission authority; owns scheduling/routing/dispatch coordination Actual-state only.
- **State / Source Facts / Projection:** final owner for its bounded route/schedule/dispatch decisions/facts; execution attempt/outcome remains node/agent/server-local partition.
- **Governance Context:** consumes Tenant/Principal/Policy/Trust/Artifact/Admission and capability/readiness evidence; no decision changes upstream authority.
- **Configuration / Secrets:** routing/scheduling configuration item semantics belong to `ns_runtime`; managed desired via S9; applied here; secret material not implied.
- **Offline / Failure / Recovery / Temporal:** unavailable participant may produce pending/unknown/unroutable/indeterminate coordination; dispatch attempt does not prove execution; replay does not retroactively admit work.
- **Compatibility / Migration / Conformance / Extension:** coordination semantics and capability declarations must remain compatible; extensions cannot gain admission through routability.
- **Dependencies / Contracts / Foundation Pressure:** stable Admitted Work Coordination, Capability/Readiness and Dispatch Evidence contracts with server/node/agent; time/correlation/status/telemetry pressure candidate only.
- **Non-goals / Forbidden Escalation:** schedule/dispatch != admission; runtime readiness != artifact acceptance; no universal scheduler/worker topology selected.
- **Downstream Deferrals / Revalidation:** routing algorithm/queue/broker/process roles → Runtime Responsibility Architecture/Component Design; revalidate on Authority or actual-state ownership movement.

## R3 — Operation Continuation, Delegation & Intervention Coordination

- **Purpose / Capability Custody:** operation/correlation context propagation and cross-component continuation coordination for Automation execution, Agent→Node delegated work, event-triggered work, HITL wait/resume, composed executions and governed intervention requests where runtime coordination is applicable.
- **Owned Authority / SoT:** no source-domain or execution-result authority; owns only coordination-stage Actual-state such as request received/forwarded/coordination pending where genuinely its facts.
- **State / Source Facts / Projection:** Cancel/Retry/Resume/Recovery request coordination is distinct from final outcome; source executor/semantic owner determines actual outcome; web/SDK project request vs outcome separately.
- **Governance Context:** governance/admission context must propagate without mutation or authority transfer.
- **Configuration / Secrets:** continuation/routing configuration semantics belong to runtime; secrets only where transport/runtime needs them under later custody design.
- **Offline / Failure / Recovery / Temporal:** request may be pending/unreachable/indeterminate; reconnect does not prove intervention; retry preserves attempt lineage.
- **Compatibility / Migration / Conformance / Extension:** operation identity/correlation and intervention meaning are stable semantic pressures; extension coordination must conform.
- **Dependencies / Contracts / Foundation Pressure:** stable Operation Correlation/Continuation/Intervention Coordination contracts with server/node/agent/web; correlation/time/status primitives candidate only.
- **Non-goals / Forbidden Escalation:** no universal cancellation/retry/rollback engine; request accepted != outcome achieved; no HITL semantic authority.
- **Downstream Deferrals / Revalidation:** delivery protocol/state machine/retry mechanics/process roles → Runtime Responsibility Architecture; revalidate on operation-control authority or actual-state topology change.

## R4 — Coordination Recovery, Reconciliation & Diagnostics

- **Purpose / Capability Custody:** recovery/reconnect/reconciliation participation for runtime coordination state plus health/lifecycle/diagnostic evidence production.
- **Owned Authority / SoT:** owns only runtime-coordination recovery/health Actual-state; source facts/effects remain source owner.
- **State / Source Facts / Projection:** produces reconnect/reachability/coordination-recovery evidence and participates in reconciliation handoff; web projects layered diagnostics.
- **Governance Context:** preserves Tenant/Principal/Policy/Trust/provenance through recovery; recovery never changes original authority.
- **Configuration / Secrets:** applied runtime config/health evidence is reported without exposing secrets.
- **Offline / Failure / Recovery / Temporal:** UNKNOWN/STALE/CONFLICTING/RECONCILIATION_PENDING remain first-class; reconnect != reconciled; clock/order ambiguity must remain explicit later.
- **Compatibility / Migration / Conformance / Extension:** recovery evidence and diagnostic categories must remain compatible across versions; extensions cannot hide or rewrite source provenance.
- **Dependencies / Contracts / Foundation Pressure:** stable Health/Recovery/Reconciliation Evidence contracts; logging/telemetry/time/correlation/error/status candidate pressure.
- **Non-goals / Forbidden Escalation:** no central conflict-winner algorithm; no latest-timestamp-wins rule; no universal source-of-truth promotion.
- **Downstream Deferrals / Revalidation:** reconciliation algorithm/storage/transport → later Runtime/Component design; revalidate on authority/SoT recovery rule change.

---

# 9. `ns_node` Internal Architecture Boundaries

`ns_node` contains **4** architecture-level responsibility boundaries.

## N1 — Local Capability, Readiness & Applied Configuration

- **Purpose / Capability Custody:** local capability inventory/readiness, installed/available/activated state, attended/unattended mode readiness, health and applied managed configuration.
- **Owned Authority / SoT:** no Product semantic authority; owns bounded Node capability/readiness/applied-config Actual-state facts.
- **State / Source Facts / Projection:** final owner for local installed/available/activated/readiness/applied-state assertions; server desired state and runtime coordination projections remain separate.
- **Governance Context:** capability exposure is Tenant/Principal/Policy/Trust-sensitive; user-session presence never bypasses governance.
- **Configuration / Secrets:** local bootstrap configuration is Node-local; managed desired comes from S9; applied state is owned here; secret material may be required for capabilities but remains separately governed.
- **Offline / Failure / Recovery / Temporal:** offline readiness may be locally known while central projection is stale; UNKNOWN/UNAVAILABLE/UNSUPPORTED/PARTIALLY_APPLIED explicit; reconnect initiates evidence handoff, not authority transfer.
- **Compatibility / Migration / Conformance / Extension:** executable/package/plugin capability compatibility and configuration compatibility are explicit; extension capability advertisement must conform.
- **Dependencies / Contracts / Foundation Pressure:** stable Node Capability/Readiness/Applied Configuration contracts to runtime/server/web; config loader/health/time/status/telemetry candidate pressure.
- **Non-goals / Forbidden Escalation:** installed != accepted; available != admitted; activated != authorized; user session != IAM authority.
- **Downstream Deferrals / Revalidation:** inventory format/package/runtime placement/session mechanics → later Component/Runtime design; revalidate on Node actual-state or authority movement.

## N2 — Governed Local Execution

- **Purpose / Capability Custody:** OCR, desktop/browser automation, tool/plugin/workflow/package execution, attended and unattended execution, Agent-delegated work, Automation execution participation, local trial participation and operation intervention support.
- **Owned Authority / SoT:** no Automation/Agent/Artifact/Admission/Policy authority; owns bounded local execution-attempt Actual-state.
- **State / Source Facts / Projection:** final owner for local attempt running/waiting/stopped/outcome state as locally established; protected effects are further owned by N3; runtime/web projections consume evidence.
- **Governance Context:** consumes Tenant/Organization/Principal/IAM/Policy/Trust/Artifact/Admission/config; attended presence and unattended mode never bypass them.
- **Configuration / Secrets:** local executor config applied via N1; runtime may require secret material for authorized local capability; no secret leakage in diagnostics.
- **Offline / Failure / Recovery / Temporal:** permitted offline execution uses bounded verifiable governance evidence; inability to verify may remain UNKNOWN/INDETERMINATE; intervention request != outcome; retry preserves attempt lineage.
- **Compatibility / Migration / Conformance / Extension:** executable capability compatibility, definition/artifact revision compatibility and attended/unattended capability declarations must conform; extensions remain governed.
- **Dependencies / Contracts / Foundation Pressure:** stable Local Execution Intent/Evidence, Trial Execution and Intervention Outcome contracts with runtime/server/agent/web; temporal/correlation/status/logging pressure candidate only.
- **Non-goals / Forbidden Escalation:** local execution != admission; local success != semantic authority; no universal worker/process/session model.
- **Downstream Deferrals / Revalidation:** process/session/browser/profile/concurrency/sandbox mechanics → Runtime Responsibility Architecture/Component Design; revalidate on local-effect or admission topology changes.

## N3 — Protected Local Effect & Source-fact Custody

- **Purpose / Capability Custody:** local file/device/resource interaction, protected local effects, observable local source facts, effect evidence and provenance.
- **Owned Authority / SoT:** owns bounded local effect/source-fact assertions genuinely originating at Node; does not own broader business/automation/agent semantic truth.
- **State / Source Facts / Projection:** final owner for whether a protected local effect actually occurred and local observation evidence; central projections may lag but cannot rewrite source fact.
- **Governance Context:** effects must be tied to Tenant/Principal/Policy/Trust/admission/attempt provenance where applicable.
- **Configuration / Secrets:** effecting tools may need secret material locally; only authorized runtime custody is allowed, with no material disclosure through source-fact reporting.
- **Offline / Failure / Recovery / Temporal:** local fact survives disconnection; partial/failed/unknown effects remain explicit; stopping execution never implies effect reversal; reconciliation transfers evidence, not authority.
- **Compatibility / Migration / Conformance / Extension:** effect semantics and evidence must remain interpretable across versions; extension/provider execution cannot hide effect provenance.
- **Dependencies / Contracts / Foundation Pressure:** stable Source/Effect Evidence contracts to server/runtime/agent/web diagnostics; time/correlation/serialization/security primitives candidate only.
- **Non-goals / Forbidden Escalation:** local fact != Policy/Admission/Business Authority; local copy != external SoT replacement; no universal rollback layer.
- **Downstream Deferrals / Revalidation:** effect adapters/resource APIs/evidence schema → later Component/Contract design; revalidate on source-effect final ownership change.

## N4 — Offline Continuity, Recovery & Local Diagnostics

- **Purpose / Capability Custody:** local evidence retention pressure, offline/degraded continuity, recovery/resume/reconciliation participation, health/lifecycle and layered diagnostics.
- **Owned Authority / SoT:** no new semantic authority; owns only Node-local recovery/diagnostic facts that originate locally.
- **State / Source Facts / Projection:** records/reports locally verifiable execution/effect/readiness evidence; participates in central reconciliation without canonicalizing broader state.
- **Governance Context:** preserves Tenant/Principal/Policy/Trust/admission provenance across disconnection and replay.
- **Configuration / Secrets:** diagnostics expose secret references/status only as authorized and never secret material; applied config divergence is evidence, not desired-state rewrite.
- **Offline / Failure / Recovery / Temporal:** reconnect != reconciled; replay != retroactive authorization; central stale != local nonexistent; UNKNOWN/CONFLICTING/UNVERIFIED/RECONCILIATION_PENDING explicit.
- **Compatibility / Migration / Conformance / Extension:** recovery evidence remains version/revision interpretable; extension evidence follows same conformance rules.
- **Dependencies / Contracts / Foundation Pressure:** stable Node Recovery/Reconciliation/Diagnostic Evidence contracts; logging/telemetry/health/time/correlation/error-status candidate pressure.
- **Non-goals / Forbidden Escalation:** no fail-open/fail-closed policy selected; no conflict-winner algorithm; no local Authority escalation.
- **Downstream Deferrals / Revalidation:** persistence/replay/reconcile algorithm → later Runtime/Component design; revalidate on offline governance semantics or authority transfer proposal.

---

# 10. `ns_agent` Internal Architecture Boundaries

`ns_agent` contains **6** architecture-level responsibility boundaries.

## A1 — Agent Definition & Evolution

- **Purpose / Capability Custody:** native Agent semantic definition, canonical Definition SoT, complete dual authoring, revision/history/semantic diff, compatibility, conformance and governed trial intent.
- **Owned Authority / SoT:** Native AI Agent Definition / Semantic Authority and Canonical Agent Definition SoT.
- **State / Source Facts / Projection:** accepts source/SDK and visual-authored semantic changes into the same governed Agent semantics; web editor state is not SoT; runtime Agent facts belong A2.
- **Governance Context:** consumes Tenant/Principal/Policy/Trust and server Artifact/Admission governance; provider/model/tool identity never becomes Agent Authority.
- **Configuration / Secrets:** Agent-definition configuration semantics belong here where definition-level; provider/tool credentials remain references, not material.
- **Offline / Failure / Recovery / Temporal:** offline/private authoring preserves revision/provenance; unsupported/non-editable constructs explicit; historical execution references applicable Agent revision.
- **Compatibility / Migration / Conformance / Extension:** bidirectional semantic interoperability required; Multi-Agent dependency evolution and provider capability constraints produce compatibility feedback; re-delivery stays same Agent semantic domain.
- **Dependencies / Contracts / Foundation Pressure:** stable Agent Definition/Revision/Validation/Trial contracts to web/SDK/server; serialization/time/conformance helpers candidate only.
- **Non-goals / Forbidden Escalation:** visual/source/provider/model/runtime copy != Agent SoT; no mandatory AST/IR/DSL selected.
- **Downstream Deferrals / Revalidation:** schema/API/representation/module layout → later design; revalidate on Agent Authority/SoT or source↔visual guarantee change.

## A2 — Agent Runtime Context, HITL & Actual-state

- **Purpose / Capability Custody:** Agent runtime semantics, context/memory-related runtime responsibility, reasoning/execution activity, Agent HITL participation, operation history/provenance, trial/evaluation runtime facts and intervention participation.
- **Owned Authority / SoT:** owns bounded Agent-runtime Actual-state facts genuinely originating from Agent execution; semantic Authority remains A1; consumed capability facts remain external.
- **State / Source Facts / Projection:** final owner for Agent attempt/contextual runtime facts under its semantic partition; Human Task waiting/response applicability belongs Agent semantics/runtime here while unified inbox remains projection; web projects history/diagnostics.
- **Governance Context:** consumes server Tenant/Principal/Policy/Trust/Artifact/Admission; Human Response never substitutes those authorities.
- **Configuration / Secrets:** Agent runtime config semantic authority belongs `ns_agent`; desired from S9, applied runtime state here; runtime may require provider/tool secret material under later custody.
- **Offline / Failure / Recovery / Temporal:** supports return-later/cross-session operation identity; stale/context-loss/provider-unavailable/HITL-wait/unknown explicit; recovery preserves context/provenance without claiming deterministic replay.
- **Compatibility / Migration / Conformance / Extension:** runtime must check definition/provider/tool/capability compatibility; migrations preserve history/revision association; extensions conform to Agent semantics.
- **Dependencies / Contracts / Foundation Pressure:** stable Agent Runtime Evidence/HITL Source/Trial/Intervention Outcome contracts to server/runtime/web/node; correlation/time/telemetry/status candidate pressure.
- **Non-goals / Forbidden Escalation:** reasoning success != admission/acceptance; Human Task UI != Agent runtime owner; model provider != Agent actual-state owner automatically.
- **Downstream Deferrals / Revalidation:** memory/context algorithms/process topology/state machine → Runtime Responsibility Architecture/Component Design; revalidate on Agent runtime actual-state partition or HITL authority change.

## A3 — Model / Provider Mediation & Multimodal Capability

- **Purpose / Capability Custody:** model/provider mediation, provider capability discovery/compatibility, private/offline provider operation and Native Multimodal Agent capability support.
- **Owned Authority / SoT:** no provider/model Product Authority; owns Agent-domain mediation semantics/capability compatibility assertions where genuinely `ns_agent` responsibility.
- **State / Source Facts / Projection:** provider availability/capability observations are bounded facts, not provider authority over Agent definition; runtime outcomes feed A2.
- **Governance Context:** Tenant/Principal/Policy/Trust/privacy applies to provider access and multimodal data; external provider does not become trust or Agent Authority.
- **Configuration / Secrets:** provider configuration semantics belong `ns_agent`; secret references may originate from managed config, while secret material may be needed at runtime and must remain non-observable.
- **Offline / Failure / Recovery / Temporal:** unavailable/unsupported/unknown provider capability is explicit; core Agent capability cannot require a public SaaS provider for private/offline correctness.
- **Compatibility / Migration / Conformance / Extension:** provider capability/version compatibility and replacement are explicit; provider replacement must not rewrite Agent semantics.
- **Dependencies / Contracts / Foundation Pressure:** stable Provider Capability/Mediation contracts and secret-reference pressure; HTTP client/time/telemetry/serialization candidate only.
- **Non-goals / Forbidden Escalation:** model/provider != Agent; provider success != Trust/Policy/Admission; no provider SDK/protocol selected.
- **Downstream Deferrals / Revalidation:** provider adapter/routing/fallback/credential storage → later Component/Foundation/Provider design; revalidate on major provider lock-in or Agent Authority change.

## A4 — Tool & Knowledge Consumption

- **Purpose / Capability Custody:** governed tool use/discovery/binding and RAG/Knowledge/Data consumption while preserving external/domain authority.
- **Owned Authority / SoT:** owns Agent tool-binding/consumption semantics only; does not own Tool Provider, Data or Knowledge SoT by consumption.
- **State / Source Facts / Projection:** tool invocation/runtime facts belong applicable Agent/node/external partition; Knowledge facts preserve their factual owner/provenance; web projects explainability/provenance as authorized.
- **Governance Context:** Tenant/Principal/Policy/Trust/Artifact/Admission/privacy applies to tool/data access.
- **Configuration / Secrets:** tool/provider config semantics follow owning capability; runtime secret material may be needed but is never surfaced as context/provenance payload.
- **Offline / Failure / Recovery / Temporal:** unavailable/stale/unknown knowledge/tool capability explicit; cached knowledge does not become SoT; retry/recovery preserves invocation lineage.
- **Compatibility / Migration / Conformance / Extension:** tool/capability/reference compatibility is explicit; extensions/providers conform without gaining authority.
- **Dependencies / Contracts / Foundation Pressure:** stable Tool Capability/Invocation and Knowledge Consumption/Provenance contracts to node/server/external integrations; HTTP/storage/cache/secret-ref candidate pressure only.
- **Non-goals / Forbidden Escalation:** RAG != Knowledge Authority; tool binding != local-effect authority; no vector DB/embedding/provider decision.
- **Downstream Deferrals / Revalidation:** discovery/invocation schemas/adapters/RAG storage → later design; revalidate on Data/Knowledge/Tool authority movement.

## A5 — Native Multi-Agent Composition

- **Purpose / Capability Custody:** standalone + general Native Multi-Agent definition composition, reference/invocation/delegation semantics, dependency compatibility and composed provenance.
- **Owned Authority / SoT:** Agent composition semantics remain under Agent Authority/SoT in A1; no separate Multi-Agent Authority.
- **State / Source Facts / Projection:** each Agent runtime partition retains bounded facts; composition relationship does not merge actual-state owners; web/SDK project composed history.
- **Governance Context:** Tenant/Principal/Policy/Trust/Artifact/Admission propagate across Agent delegation; no delegation bypass.
- **Configuration / Secrets:** composition config semantics belong Agent domain; no secret duplication implied by composition.
- **Offline / Failure / Recovery / Temporal:** composed Agent availability/compatibility may be unknown/partial; recovery preserves per-Agent attempt/provenance; recursion/cycle mechanics deferred.
- **Compatibility / Migration / Conformance / Extension:** Agent dependency/revision compatibility is mandatory; extensions cannot create ungoverned Agent graph semantics.
- **Dependencies / Contracts / Foundation Pressure:** stable Agent Reference/Delegation/Composition contracts; correlation/time/status primitives candidate only.
- **Non-goals / Forbidden Escalation:** Multi-Agent != Automation Authority; Agent A invocation != Agent B Authority transfer; no supervisor/graph/process topology selected.
- **Downstream Deferrals / Revalidation:** graph/protocol/context-sharing/parallelism mechanics → later Component/Runtime design; revalidate on general Multi-Agent support or Agent Authority changes.

## A6 — Governed Cross-domain Delegation & Automation Participation

- **Purpose / Capability Custody:** Agent→Node governed delegation, Automation selection/invocation, and dynamic candidate Automation authoring from user intent.
- **Owned Authority / SoT:** owns Agent-side intent/delegation/authoring-participant semantics only; Automation Authority/SoT remain server S6; Node effect/attempt ownership remains node.
- **State / Source Facts / Projection:** Agent records delegation/invocation/candidate-authoring provenance; runtime may coordinate; Node produces local attempt/effect facts; server owns Automation candidate canonical intake once accepted into definition lifecycle.
- **Governance Context:** Tenant/Principal/Policy/Trust/Artifact/Admission always applies; candidate generation never bypasses validation/acceptance/admission.
- **Configuration / Secrets:** delegation/tool/automation-selection config semantics belong applicable owner; secret material not transferred merely because Agent delegates.
- **Offline / Failure / Recovery / Temporal:** candidate/offline possession != acceptance; delegated work may be unreachable/unknown; recovery preserves attempt/candidate lineage.
- **Compatibility / Migration / Conformance / Extension:** Agent→Automation and Agent→Node references must be compatibility-checked; authoring participant does not create separate Automation compatibility class.
- **Dependencies / Contracts / Foundation Pressure:** stable Agent Delegation, Automation Candidate Submission, Governed Invocation and provenance contracts with S6/S8/runtime/node; correlation/status/serialization candidate pressure.
- **Non-goals / Forbidden Escalation:** Agent authors candidate != Automation Authority; invokes Automation != acceptance/admission bypass; delegates Node work != local-effect Authority transfer.
- **Downstream Deferrals / Revalidation:** physical path/schema/transport/parameter binding/build/package mechanics → later Contract/Runtime/Component design; revalidate on any accepted Authority move or ephemeral flow class proposal.

---

# 11. `ns_web` Internal Architecture Boundaries

`ns_web` contains **7** architecture-level responsibility boundaries.

## W1 — Governed Administration & Control Interaction

- **Purpose / Capability Custody:** human-facing administration for Tenant/IAM/Organization/Policy/Trust, Artifact/Admission governance and managed configuration desired-state interaction.
- **Owned Authority / SoT:** none of the administered semantic authorities; owns only frontend interaction/session presentation facts.
- **State / Source Facts / Projection:** displays authoritative/derived governance state with freshness/provenance; submits intended changes/actions to authoritative boundaries; local UI state/cache never becomes SoT.
- **Governance Context:** every view/action is Tenant/Organization/Principal/Policy/Trust/privacy-aware; UI affordance never grants authorization.
- **Configuration / Secrets:** may present/edit authorized configuration/reference metadata; Secret Material must not be exposed or cached as ordinary UI state.
- **Offline / Failure / Recovery / Temporal:** stale/unknown/unreachable desired/applied/observed conditions explicit; session loss does not cancel operations or erase authoritative state.
- **Compatibility / Migration / Conformance / Extension:** presentation must conform to authoritative semantics; re-delivered frontends cannot redefine governance meaning.
- **Dependencies / Contracts / Foundation Pressure:** stable Administration/Governance Projection and Command Intent contracts to server boundaries; i18n/status/time/correlation helpers candidate only.
- **Non-goals / Forbidden Escalation:** UI state != canonical state; button click != Policy/Acceptance/Admission; no frontend cache SoT.
- **Downstream Deferrals / Revalidation:** pages/components/state-management/API specifics → Component Internal Design; revalidate if UI becomes authority.

## W2 — Cross-domain Authoring & Semantic Interoperability

- **Purpose / Capability Custody:** complete visual authoring for Business Application, Automation, Agent, Data/Knowledge/ETL plus source↔visual semantic interoperability, validation/conformance/compatibility feedback, revision/history/semantic diff interaction.
- **Owned Authority / SoT:** no Definition Authority/SoT; each domain owner remains authoritative.
- **State / Source Facts / Projection:** visual edit state is transient authoring state; governed change is submitted to applicable domain owner; unsupported/non-editable/representation-limited constructs remain explicit and semantics-preserving.
- **Governance Context:** authoring scoped by Tenant/Principal/Policy/Trust and applicable domain permissions.
- **Configuration / Secrets:** authoring may manipulate secret references only; secret material is not definition/UI state.
- **Offline / Failure / Recovery / Temporal:** offline/private authoring must preserve revision base/provenance/conflict visibility; stale base or unknown compatibility explicit; cross-session history derives from authoritative revisions.
- **Compatibility / Migration / Conformance / Extension:** mandatory bidirectional semantic interoperability, no silent semantic destruction, no lossless representation guarantee; re-delivery/customer source changes remain interoperable.
- **Dependencies / Contracts / Foundation Pressure:** stable Authoring Projection/Edit/Validation/Compatibility/Revision contracts to S5/S6/S7/A1 and SDK semantic counterparts; serialization/time/status candidate pressure.
- **Non-goals / Forbidden Escalation:** Visual Builder != Semantic Authority; no AST/IR/DSL/converter/compiler/code generator selected.
- **Downstream Deferrals / Revalidation:** editor model/representation/conversion algorithm/frontend architecture → later Component Internal Design; revalidate on source↔visual product guarantee or domain Authority change.

## W3 — Human Task Interaction

- **Purpose / Capability Custody:** unified Human Task Inbox interaction, task rediscovery, context/provenance visibility and governed human response submission.
- **Owned Authority / SoT:** no Human Task source/execution/Policy/Acceptance/Admission authority; owns only human interaction occurrence/session facts.
- **State / Source Facts / Projection:** consumes S11 aggregated projection and source-domain context; response submission is an interaction fact and must not be displayed as semantically applied until authoritative evidence confirms it.
- **Governance Context:** Tenant/Organization/Principal/Policy/Trust and response authorization are mandatory; task visibility is authorization-scoped.
- **Configuration / Secrets:** task view preferences may be frontend/local config; sensitive/secret content is redacted and never exposed by task projection.
- **Offline / Failure / Recovery / Temporal:** stale/expired/wrong-context/conflicting/unverified response state explicit; return-later does not depend on browser session.
- **Compatibility / Migration / Conformance / Extension:** task interaction semantics and provenance remain consistent across surfaces/versions; extensions cannot redefine approval meaning.
- **Dependencies / Contracts / Foundation Pressure:** stable Human Task Projection/Response Submission/Outcome Evidence contracts with S11/S6/A2/runtime; correlation/time/status/accessibility pressure only.
- **Non-goals / Forbidden Escalation:** Inbox != Notification; click != Policy Permit/Acceptance/Admission; UI completion != runtime completion.
- **Downstream Deferrals / Revalidation:** task UI/state-management/API details → Component/Contract design; revalidate if Human Task interaction acquires Authority.

## W4 — Notification & Awareness Interaction

- **Purpose / Capability Custody:** in-product Notification discovery/history, awareness presentation, external-delivery status presentation and user-facing correlation to underlying governed resource/fact.
- **Owned Authority / SoT:** none over Notification lifecycle or underlying source facts; S12 owns notification/delivery-attempt partition.
- **State / Source Facts / Projection:** presents notification history with source correlation and freshness; local read UI intent is not source condition resolution; provider delivery evidence remains S12 concern.
- **Governance Context:** audience/Tenant/Principal/Policy/privacy/redaction controls required.
- **Configuration / Secrets:** channel preference/reference administration may be exposed only as authorized; provider secret material must never be shown.
- **Offline / Failure / Recovery / Temporal:** stale notification projection explicit; external channel unreachable does not erase in-product notification; historical notification remains even after source condition changes.
- **Compatibility / Migration / Conformance / Extension:** channel-neutral semantics stable; new delivery channels do not change web meaning.
- **Dependencies / Contracts / Foundation Pressure:** stable Notification Projection/History/Delivery Status contracts with S12; i18n/time/status candidate pressure.
- **Non-goals / Forbidden Escalation:** Notification Center != current-state SoT; read != resolved; delivered != observed; not Human Task.
- **Downstream Deferrals / Revalidation:** page/layout/read-state mechanics → later design; revalidate if awareness surface becomes Authority or Human Task semantics collapse.

## W5 — Operational Observation, Trial, Intervention & Diagnostics

- **Purpose / Capability Custody:** asynchronous operation identity/history/return-later observation, governed pre-production trial interaction, intervention request interaction, desired/applied/observed presentation, layered diagnostics/explainability and authorized provenance.
- **Owned Authority / SoT:** no runtime/source-fact/Trial/Intervention Authority; owns only frontend interaction/projection state.
- **State / Source Facts / Projection:** projections derive from server/runtime/node/agent actual/source facts; Cancel/Retry/Resume/Recovery request shown separately from outcome; trial result distinct from production; diagnostics layered and provenance-bearing.
- **Governance Context:** Tenant/Principal/Policy/Trust/privacy/redaction enforced; sensitive evidence exposure is scoped.
- **Configuration / Secrets:** presents desired/applied/observed without collapse; secret material excluded/redacted.
- **Offline / Failure / Recovery / Temporal:** UNKNOWN/INDETERMINATE/STALE/UNREACHABLE/PARTIALLY_APPLIED/RECONCILIATION_PENDING explicit; browser closed != cancelled; reconnect != recovered.
- **Compatibility / Migration / Conformance / Extension:** operation/trial/intervention/diagnostic semantics remain cross-surface compatible; historical result tied to applicable definition/config/runtime revision.
- **Dependencies / Contracts / Foundation Pressure:** stable Operation Observation, Trial, Intervention, Diagnostics, Provenance and Config Projection contracts with all producing boundaries; correlation/time/status/telemetry helpers candidate only.
- **Non-goals / Forbidden Escalation:** Dashboard != actual-state owner; Trial Success != Acceptance/Admission; request != result; raw hidden reasoning not required.
- **Downstream Deferrals / Revalidation:** UI state model/charts/pages/streaming transport → Component/Runtime/Contract design; revalidate if projection becomes source authority.

## W6 — Cross-domain Discovery & Governed Navigation

- **Purpose / Capability Custody:** unified search/discovery interaction across applicable resources and navigation back to the authoritative domain resource.
- **Owned Authority / SoT:** no resource/discovery semantic Authority beyond frontend query interaction; S13 owns discovery projection state, resource owners own resources.
- **State / Source Facts / Projection:** result preserves domain/type/identity, authorization scope and freshness/completeness uncertainty.
- **Governance Context:** Tenant/Principal/Policy/privacy filtering mandatory; unauthorized existence/snippets/counts cannot leak.
- **Configuration / Secrets:** frontend discovery preferences may be local; secrets are not searchable display data absent explicit authorized semantics.
- **Offline / Failure / Recovery / Temporal:** stale/partial/unavailable/rebuilding projection explicit; offline discovery consumes private/local projection only where available.
- **Compatibility / Migration / Conformance / Extension:** resource-type and navigation semantics stable while index technology is replaceable; extensions contribute only governed discoverable projections.
- **Dependencies / Contracts / Foundation Pressure:** stable Discovery Query/Result/Navigation contracts with S13 and domain resources; no search engine/provider selected.
- **Non-goals / Forbidden Escalation:** search result != authorization; index/result != SoT; no mandatory AI semantic search.
- **Downstream Deferrals / Revalidation:** ranking/query syntax/page design/index provider → later design; revalidate on authority leakage or cross-Tenant discovery.

## W7 — Experience Semantics, Accessibility & Degraded Interaction

- **Purpose / Capability Custody:** internationalization/localization, accessibility for critical workflows, timezone-aware presentation, cross-surface semantic consistency and offline/degraded/unknown-state interaction rules.
- **Owned Authority / SoT:** no domain semantic authority; owns only presentation semantics and accessibility/localization behavior that must faithfully project underlying meaning.
- **State / Source Facts / Projection:** local UI state may represent presentation choices, not product truth; semantic status/action meaning must remain consistent with SDK/other surfaces.
- **Governance Context:** locale/accessibility mode never changes Tenant/Principal/Policy/Trust; privacy/redaction preserved across localized/accessible presentations.
- **Configuration / Secrets:** presentation preferences are local/managed as applicable; localization never exposes hidden secret/sensitive content.
- **Offline / Failure / Recovery / Temporal:** stale/unknown/degraded states remain explicit and accessible; timezone conversion does not change occurrence ordering/authority; offline behavior never fabricates authoritative success.
- **Compatibility / Migration / Conformance / Extension:** interaction vocabulary and critical workflow semantics must remain cross-surface conformant; localization resources may evolve without redefining domain semantics.
- **Dependencies / Contracts / Foundation Pressure:** consumes stable status/error/time/provenance semantics from all domains; i18n/accessibility implementation libraries remain downstream choices.
- **Non-goals / Forbidden Escalation:** locale != Tenant/Principal/timezone; accessible confirmation != additional Authority; client clock != source-time Authority.
- **Downstream Deferrals / Revalidation:** frontend library/component/layout/localization storage → Component Internal Design/Implementation Planning; revalidate on semantic inconsistency or governance-context reinterpretation.

---

# 12. System-level SDK / Development Surface Relationship

The System-level SDK / Development Surface remains **outside the five Product Components** and is not a sixth Product Component, Product Authority, Runtime Actual-state owner or universal SoT.

Architecture-level relationships:

| Development capability | Required component relationship |
|---|---|
| Complete Business Application source authoring | consumes S5 governed semantics and lifecycle |
| Complete Automation source authoring | consumes S6 governed semantics and lifecycle |
| Complete Agent source authoring | consumes A1 governed semantics and lifecycle |
| Complete Data/Knowledge/ETL source authoring | consumes S7 governed semantics and lifecycle |
| Validation / conformance / compatibility | calls/consumes applicable semantic owner results; SDK does not certify by placement |
| Pre-production trial | expresses Trial Intent against applicable domain owner and consumes bounded trial evidence from actual execution participant |
| Revision / history / semantic diff | consumes authoritative definition revision history, never current local source as historical SoT |
| Source ↔ Visual interoperability | shares the same governed semantics with W2; no separate source-only semantic class |
| Extension/provider/tool/connector development | consumes stable contracts and preserves authority, Tenant, Trust, offline and compatibility constraints |
| Re-delivery | preserves original authority topology and semantic compatibility; customer source modification does not create new platform Authority |
| Offline/private development | cannot require public registry/SaaS/control-plane for core correctness |

SDK package/API/CLI shape is not designed here.

---

# 13. Authority / Source-of-Truth Matrix

| Subject | Final Authority / SoT at this boundary level | Non-authoritative participants |
|---|---|---|
| Tenant semantics / canonical Tenant state | S1 / `ns_server` | runtime/node/agent/web/SDK consume context |
| IAM / Principal semantics | S1 / `ns_server` | all others consume/enforce/project |
| Organization semantics | S2 / `ns_server` | external systems may own bounded factual partitions |
| Policy semantics | S3 / `ns_server` | all others consume/enforce/project |
| Platform Trust semantics | S4 / `ns_server` | all others consume evidence/decisions |
| Business Application definition semantics/SoT | S5 / `ns_server` | W2 + SDK authoring surfaces |
| Automation definition semantics/SoT | S6 / `ns_server` | W2 + SDK + Agent candidate authoring participation |
| Data/Knowledge/ETL semantic authority | S7 / `ns_server` | external factual owners preserved |
| Agent definition semantics/SoT | A1 / `ns_agent` | W2 + SDK authoring surfaces |
| Formal Artifact Acceptance | S8 / `ns_server` | domain certification/web/SDK/runtime evidence suppliers |
| Formal Execution Admission | S8 / `ns_server` | runtime/node/agent consume evidence |
| Managed runtime desired configuration | S9 / `ns_server` | applied owners are component runtime partitions |
| Runtime actual state | per bounded partition | no aggregator becomes universal SoT |
| Node protected local effects/source facts | N3 / `ns_node` | runtime/server/web may receive/project |
| Agent runtime facts | A2 / `ns_agent` | runtime/server/web may coordinate/project |
| Runtime coordination facts | R1-R4 / `ns_runtime` per subject | server/node/agent/web consume/project |
| Server-local background actual state | S10 / `ns_server` | web/SDK project |
| Human Task underlying source meaning | S6 Automation HITL or A2 Agent HITL | S11 aggregation + W3 projection |
| Notification underlying condition | originating source owner | S12 derived awareness lifecycle + W4 projection |
| Discovery resource meaning/SoT | originating resource owner | S13 projection + W6 interaction |

**Authority Ambiguity:** `0`.

**SoT Ambiguity:** `0`.

---

# 14. Actual-state / Source-effect Matrix

| Bounded assertion | Final owner | Explicitly not owner |
|---|---|---|
| Managed desired configuration | S9 (`ns_server`) as desired-state SoT, not runtime actual-state | web/runtime/node/agent observation |
| `ns_runtime` connection/presence fact | R1 | server/web/node local state |
| route/schedule/dispatch coordination fact | R2 | node/agent execution outcome |
| intervention/continuation coordination-stage fact | R3 | final executor outcome |
| runtime reconnect/recovery coordination fact | R4 | source-effect reconciliation result outside its partition |
| Node installed/available/activated/readiness/applied config | N1 | server desired state/web projection |
| Node local execution attempt state | N2 | runtime dispatch/web dashboard |
| Node protected local effect/source fact | N3 | server/runtime aggregation |
| Node local recovery/diagnostic fact | N4 | broader business/runtime truth |
| Agent runtime/context/HITL actual fact | A2 | provider/web/runtime projection |
| Agent/provider capability observation | A3 where Agent mediation owns the observation | external provider semantics/Agent definition authority |
| Agent delegation/invocation provenance | A6 | Node effect/Automation definition state |
| Server-local background attempt/state | S10 | `ns_runtime` merely because it is runtime hub |
| Notification lifecycle and external-delivery attempt state | S12 | underlying source condition/current state |
| Discovery projection freshness/completeness state | S13 | discovered resource state |
| Human UI response submission occurrence | W3 local interaction fact; semantic acceptance/application by originating HITL domain | browser UI as final task/execution owner |
| Web projection/cache/session state | applicable W boundary only as client interaction fact | Product definition/runtime/resource SoT |

Permanent rule:

```text
same bounded assertion
→ exactly one final Actual-state Owner
```

**Actual-state Ownership Ambiguity:** `0`.

**Source-effect Ownership Ambiguity:** `0`.

---

# 15. Configuration / Secret Custody Matrix

| Concern | `ns_server` | `ns_runtime` | `ns_node` | `ns_agent` | `ns_web` |
|---|---|---|---|---|---|
| Local bootstrap config | local server concern | local runtime concern | local Node concern | local Agent concern | local frontend bootstrap where required |
| Shared config loader pressure | consumer | consumer | consumer | consumer | consumer where applicable; authority-neutral |
| Managed desired config | S9 final management authority / SoT | consumer | consumer | consumer | admin/projection surface |
| Config item semantic authority | applicable server-owned capability | runtime intrinsic items | node intrinsic items | agent intrinsic items | genuinely presentation-local items |
| Applied config actual state | S10/other applicable server runtime partition | R1-R4 applicable partition | N1 | A2/A3/A4 applicable partition | frontend local applied presentation config only |
| Observed config | projection/aggregation only | reports evidence | reports evidence | reports evidence | W1/W5 projection |
| Secret Reference producer/consumer | may produce/manage references as governed configuration/integration metadata | consumes where runtime connection needs | consumes where local capability needs | consumes for provider/tool needs | may display reference metadata only if authorized |
| Secret Material pressure | may be required for server integrations | may be required at runtime | may be required at local execution | may be required for provider/tool calls | **must not be general material custodian** |
| Secret disclosure rule | never in ordinary config/audit/diagnostics | same | same | same | same; redact in UI |

```text
Configuration != Secret
Desired != Applied != Observed
```

No Vault/KMS/HSM/secret manager/format/encryption library is selected.

---

# 16. Cross-component Dependency Matrix

| Producer boundary | Consumer boundary | Semantic subject | Dependency invariant |
|---|---|---|---|
| S1-S4 | all runtime/interaction boundaries | Tenant/Principal/Policy/Trust context | consumption never transfers Authority |
| S5/S6/S7/A1 | W2/SDK | authoritative definition semantics/revisions | authoring surface never becomes SoT |
| S8 | R2/N2/A2/S10 | accepted artifact/admission evidence | possession/execution never becomes Acceptance/Admission Authority |
| S9 | R*/N1/A2-A4/S10 | managed desired config | consumer owns applied state only |
| S6 | R2/R3/N2 | Automation execution intent/composition/event/HITL | coordination/execution never becomes Automation Authority |
| A6 | R3/N2 | Agent→Node delegated work | Agent keeps delegation provenance; Node owns local effect facts |
| A6 | S6 | Agent-authored Automation candidate | candidate enters normal Automation lifecycle |
| S6/A2 | S11/W3/R3 | Human Task source/context/response | projection/coordination never becomes source execution Authority |
| source owners | S12/W4 | Notification source correlation | notification never becomes source/current-state SoT |
| resource owners | S13/W6 | discovery contribution/navigation | index/result never becomes resource SoT |
| runtime/node/agent/server local owners | W5 | operation/diagnostic/provenance projection | dashboard never becomes actual-state owner |
| S12 | external delivery capability | notification delivery intent/evidence | provider never becomes product Authority |

---

# 17. Stable Contract Pressure Inventory

The following are **stable contract requirements only**. No endpoint, API style, wire representation or schema is designed here.

| Pressure | Producer → Consumer | Semantic subject / why stable | Authority / SoT / Actual-state owner | Required properties | Named later authority |
|---|---|---|---|---|---|
| Governance Context | S1-S4 → runtime/node/agent/web/SDK | Tenant/Org/Principal/Policy/Trust context must not fork | server authorities | language-neutral, versioned, offline-verifiable where applicable, security-sensitive | later Contract Design |
| Definition Lifecycle — Business App | S5 ↔ W2/SDK | same canonical semantics across source/visual | S5 | language-neutral, versioned, compatibility-aware | later Contract Design |
| Definition Lifecycle — Automation | S6 ↔ W2/SDK/A6 | authoring/trigger/composition/HITL semantics | S6 | same | later Contract Design |
| Definition Lifecycle — Data/Knowledge/ETL | S7 ↔ W2/SDK | source/visual + factual provenance | S7 semantic owner; factual owner preserved | same | later Contract Design |
| Agent Definition Lifecycle | A1 ↔ W2/SDK/server governance | Agent semantics/SoT | A1 | same | later Contract Design |
| Artifact Acceptance Evidence | S8 → runtime/node/agent/web/SDK | accepted artifact applicability | S8 | revision-aware, trust/policy-bound | later Contract Design |
| Execution Admission Evidence | S8 → runtime/node/agent | admitted execution context | S8 | language-neutral, versioned, offline implication explicit | later Contract Design |
| Runtime Participant Presence | R1 ↔ node/agent/server | connectivity/presence without universal SoT | R1 for coordination assertion | temporal/freshness semantics | later Runtime Contract Design |
| Dispatch / Coordination | R2 → node/agent/server-local where applicable | admitted work coordination | R2 for coordination state; executor for attempt | request/outcome separation | later Runtime Contract Design |
| Operation Correlation / Intervention | R3 ↔ source operation owners/W5 | durable operation identity and request/outcome distinction | each bounded partition | versioned, history-preserving | later Runtime/Contract Design |
| Node Capability / Readiness | N1 → R2/server/W5 | route only against explicit capability/readiness | N1 | freshness/unknown/security | later Contract Design |
| Node Execution / Effect Evidence | N2/N3 → runtime/server/agent/W5 | source/effect truth and provenance | N2/N3 | immutable-history pressure, temporal/correlation | later Contract Design |
| Agent Runtime / Delegation Evidence | A2/A6 → runtime/server/node/W5 | Agent actual state/delegation lineage | A2/A6 bounded facts | versioned/correlated | later Contract Design |
| Human Task Projection / Response | S6/A2/S11 ↔ W3/R3 | cross-session HITL without authority collapse | source domain + bounded projection states | principal-bound, revision/context-aware | later Contract Design |
| Notification Source / Projection / Delivery | source owner → S12 ↔ W4/external delivery | awareness/history separate from source and provider | S12 notification partition | channel-neutral, tenant/audience-bound | later Contract Design |
| Discovery Contribution / Query Projection | resource owners → S13 ↔ W6/SDK | unified discovery without resource SoT transfer | resource owner; S13 projection state | auth/Tenant/freshness | later Contract Design |
| Trial Intent / Evidence | domain owner ↔ applicable execution owner ↔ W5/SDK | pre-production lifecycle with explicit effect boundary | domain semantics + execution partition | revision/context/provenance | later Contract/Runtime Design |
| Managed Config Desired / Applied Evidence | S9 ↔ runtime partitions ↔ W1/W5 | desired/applied/observed separation | S9 desired; partition applied | versioned, compatibility-aware | later Contract Design |
| Diagnostics / Provenance | all fact owners → W5/SDK | layered explainability without source takeover | original fact owner | redaction, correlation, temporal | later Contract Design |

No stable Contract representation is selected.

---

# 18. Shared Foundation Pressure Inventory

All entries are `SHARED_FOUNDATION_PRESSURE / CANDIDATE_ONLY`.

| Reusable pressure | Candidate consumers | Why reusable | Authority-neutrality requirement |
|---|---|---|---|
| configuration loading | all five | component-local bootstrap and managed-config consumption need common mechanics | loader never becomes Config Authority/SoT |
| logging | all five | consistent local diagnostic evidence | logger never becomes fact authority |
| telemetry | all five | observation/health/diagnostic transport | aggregation never becomes source authority |
| temporal primitives | all five | history, expiry, staleness, correlation | clock helper never determines semantic authority |
| serialization / representation helpers | all five | language-neutral contract realization pressure | representation never defines semantic identity |
| HTTP/network client capability | server/runtime/node/agent as applicable | external/provider/integration access | client never becomes provider/domain authority |
| cache client capability | server/runtime/agent/web where applicable | replaceable acceleration/projection pressure | cache never becomes SoT |
| storage client capability | server/node/agent where applicable | replaceable durable storage access | storage placement never becomes Authority |
| health/lifecycle primitives | all five | consistent health evidence categories | helper never owns component actual state |
| operation/correlation context | all five | end-to-end identity/provenance | carrier never becomes operation owner |
| error/status/uncertainty primitives | all five | UNKNOWN/STALE/INDETERMINATE etc. need semantic consistency | helper cannot collapse domain meaning |
| secret-reference helpers | server/runtime/node/agent/web metadata | separate reference from material and redact consistently | helper/store never becomes Trust/Policy Authority |
| compatibility/conformance helpers | all five + SDK | consistent compatibility-class handling | helper never becomes Universal Compatibility Authority |
| Tenant/Principal context carrier | all five | cross-boundary context propagation | carrier never becomes Tenant/IAM Authority |

No Foundation module name, contract, provider, package, technology or final Foundation membership is selected.

---

# 19. Cross-component Journey Closure

| Journey | Who owns meaning | Canonical state / final fact owner | Projection | Coordination | Source/effect evidence | Future stable contract pressure |
|---|---|---|---|---|---|---|
| A. User/SDK/web → author Definition → lifecycle | S5/S6/S7 or A1 | applicable domain Definition SoT | W2 / SDK | none required by authoring | domain validation/revision evidence | Definition Lifecycle |
| B. Agent → Automation → Node | A6 Agent intent; S6 Automation semantics | S6 definition; S8 acceptance/admission; N2/N3 execution/effect | W5 | R2/R3 where applicable | A6 delegation + N2/N3 facts | Candidate/Invocation/Dispatch/Effect |
| C. Agent → Node delegated work | A6 delegation semantics | A2/A6 Agent facts + N2/N3 local execution/effect facts | W5 | R3 where applicable | Agent and Node each produce bounded evidence | Delegation/Execution Evidence |
| D. Event → Automation Trigger → governance → execution | S6 trigger semantics | event source retains source fact; S8 admission; execution partition final | W5 | R2/R3 where applicable | event provenance + executor evidence | Trigger/Admission/Coordination |
| E. Automation A → Automation B | S6 | S6 canonical definitions; runtime partitions own attempts | W2/W5 | R2/R3 where applicable | execution partitions | Automation Composition |
| F. Multi-Agent composition/delegation | A1/A5 | A1 definitions; A2 per-Agent runtime facts | W2/W5 | runtime only where applicable | A2 per-Agent evidence | Agent Reference/Delegation |
| G. HITL → Human Task → Human Response → continuation | S6 or A2 source meaning | source runtime partition owns wait/resume/outcome; S11 projection only | W3 | R3 where applicable | W3 submission + source acceptance/application evidence | Human Task/Response/Continuation |
| H. Source Fact → Notification → in-product/external | original source owner | source remains owner; S12 owns Notification/delivery-attempt partition | W4 | no mandatory `ns_runtime` path selected | source + S12 provider-delivery evidence | Notification Source/Delivery |
| I. Source/Visual authoring → same semantics | domain owner | domain Definition SoT | W2 + SDK | N/A | compatibility/conformance evidence | Authoring semantic interoperability |
| J. Author → Validation → Trial → Governance → Acceptance → Admission → Production | domain owner + S8 gates | definition owner; trial executor facts; S8 gate state; production executor facts | W2/W5 | runtime as applicable | each stage produces separate evidence | Definition/Trial/Artifact/Admission/Runtime |
| K. Desired Config → distribution → Applied → Observed | S9 desired; configured capability owns item semantics | S9 desired; component runtime partition applied | W1/W5 | distribution mechanics later | component applied evidence | Config Desired/Applied Evidence |
| L. Runtime/Source Fact → Diagnostics → Operational Projection | each source owner | source owner | W5 | R4 for coordination diagnostics | source-owner provenance | Diagnostics/Provenance |
| M. Resource Domain → Discovery → navigation | resource owner | resource owner; S13 projection state only | W6/SDK | N/A | projection freshness evidence | Discovery Contribution/Query |

**Cross-component Responsibility Ambiguity:** `0`.

---

# 20. Source / Visual Interoperability Boundary Closure

For each authorable domain:

```text
Domain Semantic Owner
→ accepts/validates semantic change
→ owns canonical Definition lifecycle

System-level SDK / Source Surface
→ complete source authoring participant
→ no Authority

W2 / ns_web Visual Surface
→ complete visual authoring participant
→ no Authority

Compatibility feedback
→ originates from applicable domain semantic owner/conformance evidence

Unsupported / Non-editable / Representation-limited construct
→ MUST remain explicit
→ MUST NOT be silently destroyed or coerced

Lossless physical representation round-trip
→ NOT REQUIRED

One mandatory AST / IR / DSL / schema / converter
→ NOT SELECTED
```

---

# 21. Human Task Boundary Closure

```text
Automation HITL semantic source
→ S6

Agent HITL semantic source
→ A2 under Agent semantics

Unified cross-domain aggregation/projection
→ S11

Human-facing Inbox / response submission
→ W3

Runtime wait/resume coordination
→ R3 where applicable

Final actual wait/resume/outcome assertion
→ originating runtime semantic partition

Response provenance
→ W3 submission evidence + authoritative source-domain acceptance/application evidence
```

Human Task remains distinct from Notification, Policy Permit, Artifact Acceptance and Execution Admission.

---

# 22. Notification Boundary Closure

```text
Underlying source fact/current condition
→ original source owner

Channel-neutral Notification lifecycle
→ S12

Notification / delivery-attempt Actual-state partition
→ S12

In-product awareness/history interaction
→ W4

External delivery provider
→ downstream replaceable delivery realization
→ not Product Authority

Feishu / WeCom / SMS
→ explicit target integration directions
→ not mandatory core correctness dependencies
```

---

# 23. Cross-domain Resource Discovery Boundary Closure

```text
Resource semantic owner / SoT
→ originating domain owner

Discovery contribution
→ originating domain projects authorized discoverable metadata/reference

Unified aggregation / freshness state
→ S13

Human-facing discovery/navigation
→ W6

SDK/CLI future interaction
→ same governed discovery semantics

Discovery index/projection
!= canonical resource registry
```

---

# 24. Governed Trial Boundary Closure

```text
Authoring Surface
→ W2 or SDK

Domain Semantic Owner
→ S5 / S6 / S7 / A1

Trial Intent semantics
→ applicable domain owner

Trial execution participation
→ applicable S10 / N2 / A2 / later runtime partition as the domain requires

Trial Actual-state / effect facts
→ actual execution/source-effect owner

Trial diagnostics/provenance
→ source owners

Trial result projection
→ W5 / SDK

Artifact Acceptance / Production Admission
→ S8 and remain separate
```

No universal sandbox/trial runner/isolation technology is selected.

---

# 25. Governed Operation Intervention Boundary Closure

```text
Human / SDK intervention request
→ W5 / SDK interaction intent

Coordination-stage request state
→ R3 where runtime coordination participates

Server-local operation request handling
→ S10 for its own operation partition

Node execution request handling/outcome
→ N2 for Node attempt partition

Agent execution request handling/outcome
→ A2 for Agent runtime partition

Final underlying operation outcome
→ applicable actual-state owner
```

Permanent separations:

```text
Cancel Requested != Cancelled
Retry Requested != Retry Started
Retry != Prior Attempt Erased
Resume Requested != Resumed
Recovery Requested != Recovered
Reconnect != Reconciled
Execution Stopped != Effects Reversed
```

No universal control/retry/rollback engine is created.

---

# 26. Offline / Degraded Responsibility Review

| Component | Correct offline/degraded responsibility | Must remain unknown/blocked when evidence insufficient | Reconnect/reconciliation participation | Forbidden escalation |
|---|---|---|---|---|
| `ns_server` | preserve native governance/definitions/server-local work/private deployment; issue/consume bounded evidence according to accepted semantics | external source/provider/revocation/application facts not locally verifiable | reconcile external mappings/config applied evidence/runtime projections | no local cache or server placement becomes universal actual-state SoT |
| `ns_runtime` | coordinate currently reachable/private participants and retain bounded coordination facts | unreachable participant execution/effect facts | report reconnect and coordinate handoff | reconnect != reconciled; no admission/trust authority |
| `ns_node` | execute only where applicable governance evidence and capability permit; retain local source/effect evidence | policy/trust/admission applicability when unverifiable; remote current state | hand off local evidence; participate in recovery | offline/locality != admission/policy/trust authority |
| `ns_agent` | private/offline Agent operation with available governed model/tool/knowledge capabilities | unavailable provider/tool/knowledge/current governance facts | reconcile Agent history/delegation/evidence | local model/provider != Agent/Knowledge/Policy authority |
| `ns_web` | present locally available authoritative/derived data with explicit staleness and allow only actions whose semantics remain valid | unreachable authoritative state/outcome | refresh projections/operation history after reconnect | cached/UI state != canonical state; no fabricated success |

No material fail-open/fail-closed policy is selected by this candidate.

---

# 27. Recovery / Reconciliation Responsibility Review

```text
Evidence production
→ original semantic/runtime/source-effect owner

Evidence handoff
→ stable cross-component contracts later

Coordination of reconnect/recovery
→ R4 where runtime coordination is applicable

Component-local recovery
→ S10 / N4 / A2 as applicable

Projection refresh
→ W1-W7 consume authoritative/derived refreshed evidence

Reconciliation
→ preserves original Authority / SoT / provenance
→ never latest-copy-wins by default
```

Permanent rules preserved:

```text
Reconnect != Authority Transfer
Recovery != SoT Transfer
Replay != Retroactive Authorization
Sync != Proof of Original Authority
Local Copy != External SoT Replacement
Central Projection != Source Authority
```

---

# 28. Compatibility / Migration / Conformance Review

Every boundary classifies change using the accepted classes:

```text
CONFORMANCE_ONLY_IMPLEMENTATION_CHANGE
COMPATIBLE_EVOLUTION
EXPLICIT_MIGRATION_REQUIRED
ARCHITECTURE_REVALIDATION_REQUIRED
OWNER_MDE_REQUIRED
```

Responsibility placement:

- **Definition compatibility:** S5/S6/S7/A1 for owned definitions.
- **Artifact/admission compatibility:** S8 for accepted artifact/admission evidence semantics.
- **Provider compatibility:** A3 and applicable integration/domain boundary, without Universal Provider Authority.
- **Runtime capability compatibility:** R1/R2, N1/N2 and A2-A4 for their bounded capabilities/facts.
- **Configuration compatibility:** S9 desired-state lifecycle; configured capability owner for item meaning; applied-state owner for actual applicability.
- **Identity mapping compatibility:** S1/S2.
- **Migration participation:** owning semantic boundary defines required semantic migration; actual runtime participants provide conformance/evidence.
- **Conformance evidence:** producer boundary supplies evidence; no Universal Compatibility Authority is introduced.

---

# 29. Explicit Non-goals

This candidate does **not** select or design:

- a sixth Product Component;
- Product Component merge/split;
- Shared Foundation Architecture or final Foundation membership;
- runtime roles, processes, services, workers, queues, brokers or schedulers;
- module/package/Django App/Vue package/class decomposition;
- API endpoints or protocol style;
- OpenAPI/JSON/Protobuf/gRPC/REST/WebSocket message schemas;
- databases, tables, search engines, vector databases or storage topology;
- AST, IR, DSL, source language, visual schema, compiler, converter or code generator;
- sandbox/container/VM/trial runner;
- notification adapter/API/template/queue/retry algorithm;
- Human Task table/state machine/assignment/claim/timeout algorithm;
- reconciliation/conflict-winner algorithm;
- Vault/KMS/HSM/secret manager/encryption library/credential format;
- implementation planning, IWP or coding.

---

# 30. Named Downstream Deferrals

| Deferred subject | Named later authority |
|---|---|
| precise runtime-role/process/service/worker mapping | `Runtime Responsibility Architecture` |
| runtime actual-state subpartition mechanics and lifecycle state machines | `Runtime Responsibility Architecture` |
| component modules/classes/repositories/internal services | `Component Internal Design` |
| stable cross-boundary representation/API/schema | later explicitly authorized `Contract Design` |
| reusable authority-neutral common capability architecture | `Shared Foundation Architecture` |
| Foundation Contract/Module/Provider identity and provider selection | later Foundation phases after authorization |
| physical persistence/search/cache/storage | applicable later Component/Foundation/Provider design |
| secret material store/provider/crypto mechanisms | later Security/Foundation/Provider design under separate authorization |
| SDK API/package/CLI shape | later Component/Contract/Development Surface design |
| frontend pages/components/state-management/layout | `Component Internal Design` |
| implementation technology details beyond already frozen upstream facts | `Implementation Planning` only after readiness |

There is no `TBD`, `implementation decides`, `framework handles it`, or unnamed architecture deferral.

---

# 31. DAD Summary

Material delegated architecture choices produced by this synthesis are recorded separately in:

`docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_internal_boundary_dad_evidence_0.0.1.md`

Candidate DAD set:

```text
Z3-DAD-001..014
→ COMPONENT-BOUNDARY-LEVEL ONLY
→ NO MDE DIMENSION CHANGED
→ AWAITING GLOBAL ACCEPTANCE WITH THIS CANDIDATE
```

The DADs cover the five component boundary sets, Human Task aggregation allocation, Notification lifecycle partition allocation, Discovery projection allocation, Trial responsibility split, Intervention responsibility split, Source/Visual responsibility split, Configuration participation mapping, Actual-state/source-effect boundary refinement and System-level SDK relationship.

---

# 32. MDE Summary

```text
New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Missing Product Capability
→ 0
```

No accepted Authority, SoT, Trust, Tenant/Organization, major compatibility commitment or material offline fail-open/fail-closed choice is reopened.

---

# 33. Semantic Resolution Matrix

| Dimension | Component-boundary resolution | Status |
|---|---|---|
| Identity / Namespace | domain identities remain with semantic owners; operation/task/notification/discovery identities create stable-contract pressure without format selection | `CLOSED` |
| Revision / Evolution | definition owners own revisions; runtime/history references applicable revision | `CLOSED` |
| Authority | inherited Authority matrix preserved; projection/coordination boundaries explicitly authority-neutral | `CLOSED` |
| Semantic Ownership | S1-S9/S5-S7/A1 etc. explicit; interaction derived objects never take underlying authority | `CLOSED` |
| Source of Truth | canonical definitions/config desired/resource factual owners explicit | `CLOSED` |
| Actual-state Ownership | per bounded partition matrix with one final owner | `CLOSED` |
| State / Lifecycle | Definition→Trial→Artifact→Admission→Coordination→Attempt→Effect→Projection separation preserved | `CLOSED` |
| Temporal Semantics | history/revision/staleness/correlation required; concrete clock implementation deferred to proper later authority | `CLOSED / NAMED DOWNSTREAM` |
| Failure / Unknown / Indeterminate | explicit first-class uncertainty across all boundaries | `CLOSED` |
| Tenant | S1 Authority; propagated everywhere without transfer | `CLOSED` |
| Organization | S2 separate from Tenant; propagated where applicable | `CLOSED` |
| Principal | S1 IAM; cross-boundary principal context explicit | `CLOSED` |
| Authentication | S1 interprets native IAM/auth evidence; providers not Authority | `CLOSED` |
| Authorization / Policy | S3 Authority; consumers enforce/project only | `CLOSED` |
| Security / Trust | S4 Authority; consumers evidence/enforce only | `CLOSED` |
| Data / Privacy | S7 plus originating source owner; web/discovery/notification redaction obligations explicit | `CLOSED` |
| Trust | S4 final semantic Authority | `CLOSED` |
| Configuration | S9 desired; item meaning by capability owner; applied by runtime partition; bootstrap local | `CLOSED` |
| Secret Reference / Material | separation explicit; material custody mechanism named downstream | `CLOSED / NAMED DOWNSTREAM` |
| Serialization / Representation | language-neutral stable semantics required; physical representation deferred to Contract design | `CLOSED / NAMED DOWNSTREAM` |
| Offline / Degraded | per-component allowed/unknown/reconcile responsibilities explicit; no new fail policy | `CLOSED` |
| Recovery / Reconciliation | evidence-preserving, no Authority/SoT transfer; mechanics named downstream | `CLOSED / NAMED DOWNSTREAM` |
| Compatibility | accepted five-class model applied by semantic owner; provider/runtime/config surfaces explicit | `CLOSED` |
| Migration | semantic owner defines migration participation; actual participants provide conformance evidence | `CLOSED` |
| Conformance | boundary/contract conformance pressure explicit; no universal authority | `CLOSED` |
| Cross-boundary Dependency | dependency matrix explicit | `CLOSED` |
| Invariant | authority non-transfer, single-owner actual state, Tenant/Org non-collapse, offline/private, Definition/Artifact/Runtime separation | `CLOSED` |
| Decision Traceability | accepted Z2/Z3 decisions + `Z3-DAD-001..014` evidence | `CLOSED` |
| Revalidation Trigger | each boundary lists triggers; material Authority/SoT/Trust/compat/offline changes return to governance | `CLOSED` |

**Missing/Ambiguous Normative Dimension:** `0`.

---

# 34. Boundary Cohesion / Overfragmentation / God-boundary Review

```text
ns_server boundaries
→ 13

ns_runtime boundaries
→ 4

ns_node boundaries
→ 4

ns_agent boundaries
→ 6

ns_web boundaries
→ 7

Total
→ 34
```

Rationale:

- `ns_server` has the highest count because it already owns multiple independently accepted semantic authorities and three first-class definition domains; collapsing them into `Platform Core` would destroy architectural derivability.
- `ns_runtime` and `ns_node` deliberately remain coarse at architecture responsibility level to avoid pre-creating future process/worker/module taxonomy.
- `ns_agent` separates Definition, runtime, provider mediation, tool/knowledge consumption, Multi-Agent composition and cross-domain delegation because each has different authority/compatibility/source-fact relationships.
- `ns_web` separates Human Task from Notification and both from Operations/Discovery to preserve accepted non-equivalences while sharing cross-cutting experience semantics in W7.

**Boundary Overfragmentation:** `NONE_FOUND`.

**God Boundary:** `NONE_FOUND`.

---

# 35. Candidate Audit Results

Detailed audit evidence is recorded in:

`docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_internal_boundary_review_audit_0.0.1.md`

Candidate-level summary:

```text
MAJOR_DECISION_ESCALATION_AUDIT
→ PASS

CAPABILITY_BASELINE_CONSUMPTION_REVIEW
→ PASS / 100%

INTERACTION_BASELINE_CONSUMPTION_REVIEW
→ PASS / 100%

AUTHORITY_SOURCE_OF_TRUTH_AMBIGUITY_REVIEW
→ PASS / 0

ACTUAL_STATE_SINGLE_OWNER_REVIEW
→ PASS / 0 AMBIGUITY

SOURCE_EFFECT_RESPONSIBILITY_REVIEW
→ PASS / 0 AMBIGUITY

TENANT_ORGANIZATION_NON_COLLAPSE_REVIEW
→ PASS

CONFIGURATION_BOUNDARY_REVIEW
→ PASS

SECRET_CUSTODY_BOUNDARY_REVIEW
→ PASS / DETAILED MATERIAL MECHANISM DEFERRED BY NAME

OFFLINE_DEGRADED_RESPONSIBILITY_REVIEW
→ PASS

RECOVERY_RECONCILIATION_BOUNDARY_REVIEW
→ PASS

COMPATIBILITY_MIGRATION_CONFORMANCE_BOUNDARY_REVIEW
→ PASS

STABLE_CONTRACT_PRESSURE_REVIEW
→ PASS

SHARED_FOUNDATION_NON_PREEMPTION_REVIEW
→ PASS

UI_PROJECTION_AUTHORITY_NON_ESCALATION_REVIEW
→ PASS

RUNTIME_BOUNDARY_NON_PREEMPTION_REVIEW
→ PASS

COMPONENT_INTERNAL_DESIGN_NON_PREEMPTION_REVIEW
→ PASS

IMPLEMENTATION_DEFINED_ESCAPE_REVIEW
→ PASS / 0
```

---

# 36. Exit Gate

```text
ns_server Internal Architecture Boundaries
→ COMPLETE

ns_runtime Internal Architecture Boundaries
→ COMPLETE

ns_node Internal Architecture Boundaries
→ COMPLETE

ns_agent Internal Architecture Boundaries
→ COMPLETE

ns_web Internal Architecture Boundaries
→ COMPLETE

Accepted Batch 1 Capability Coverage
→ 100%

Accepted Batch 2 Interaction Capability Coverage
→ 100%

Unmapped Accepted Capability
→ 0

Cross-component Responsibility Ambiguity
→ 0

Authority Ambiguity
→ 0

SoT Ambiguity
→ 0

Actual-state Ownership Ambiguity
→ 0

Source-effect Ownership Ambiguity
→ 0

Tenant / Organization Collapse
→ 0

UI / Projection Authority Escalation
→ 0

Boundary Overlap producing duplicate final ownership
→ 0

Missing Product Capability
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Unnamed Deferral
→ 0

Implementation-defined Architecture Escape
→ 0

Runtime Responsibility Architecture Leakage
→ 0

Component Internal Design Leakage
→ 0

Shared Foundation Detailed-design Leakage
→ 0

Foundation Contract/Module/Provider Design Leakage
→ 0

Implementation Planning Leakage
→ 0

Unexpected Drift at recovered entry
→ NONE

Unauthorized Progression at recovered entry
→ NONE
```

---

# 37. Candidate Status and Stop Condition

```text
NGRP-001 Phase Z3
Five-component Internal Architecture Boundaries / Batch 3

→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

Producing-session recommendation:

```text
GAC INDEPENDENT REVIEW
→ RECOMMENDED
```

This candidate does **not** claim Global Acceptance, does not close Z3 globally, does not declare Architecture Exhaustion/Readiness beyond the upstream capability-readiness already accepted, does not authorize Runtime Responsibility Architecture, and does not authorize Component Internal Design, Shared Foundation Architecture, Contract/Module/Provider Design, Implementation Planning, IWP or coding.

```text
STOP
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```
