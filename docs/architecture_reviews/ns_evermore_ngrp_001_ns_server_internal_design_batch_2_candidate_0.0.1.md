# NGRP-001 — Component Internal Design / ns_server / Batch 2 Candidate

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Component Internal Design / ns_server / Batch 2`
- Authorization Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_2 / AUTOMATION_DOMAIN_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Recovered Entry HEAD: `a75ffe680ef3200344944ef5e5f2497d746dff09`
- Recovered Global State: `GAC-EPOCH-0046`
- State Verified Through HEAD: `4197bcd231c7d11e4f655e41c71004a32e8ffe99`
- Decision Registry at entry: `0.0.16 / CURRENT / NORMATIVE`
- Authorized Boundary: `S6 — Automation Definition, Trigger & Composition Lifecycle`
- Inherited Runtime Role: `SV-R02 — Automation Runtime Semantic Participant`
- Owner MDE produced in this Batch: `CID-SV-B2-MDE-001`
- Producing-session authority: bounded Component Internal Design DAD/MDE evidence only; no Global Acceptance authority.
- Candidate Status: `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`

This artifact defines architecture-level S6 internal responsibilities and stable semantic contracts. It does not define Django Apps, Python packages/classes, ORM models, tables, APIs, DTOs, wire schemas, event envelopes, brokers, queues, workflow engines, schedulers, processes, workers, containers, concrete DSL/AST/IR, visual schema, providers or implementation plans.

---

# 1. Repository Recovery

Fresh-session Repository Recovery was executed before design.

```text
Actual Branch HEAD at recovery
→ a75ffe680ef3200344944ef5e5f2497d746dff09

State Verified Through HEAD
→ 4197bcd231c7d11e4f655e41c71004a32e8ffe99

State-to-HEAD
→ ahead by 1
→ behind by 0

Changed file in delta
→ docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md only

Delta meaning
→ GAC-EPOCH-0046 / ns_server Batch 2 S6 authorization seal

Delta classification
→ EXPECTED_GOVERNANCE

UNAUTHORIZED_PROGRESSION
→ NONE

UNEXPLAINED_DRIFT
→ NONE
```

Recovery Gate reconstructed from Repository authority:

```text
Architecture Constraint Derivation → GLOBAL_CLOSED / COMPLETE
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Product Capability Exhaustion → SATISFIED
Five-component Internal Architecture Boundaries → GLOBAL_ACCEPTED / NORMATIVE
Five-component Internal-boundary Exhaustion → SATISFIED
Accepted Internal Boundaries → 34
Runtime Responsibility Architecture → GLOBAL_CLOSED / COMPLETE
Runtime Roles → 22
Shared Foundation Architecture → GLOBAL_CLOSED / COMPLETE
Foundation Contract Design → GLOBAL_CLOSED / COMPLETE
Foundation Module Design → GLOBAL_CLOSED / COMPLETE
Foundation Provider Design → GLOBAL_CLOSED / COMPLETE
Foundation Provider Design Exhaustion → SATISFIED
Component Internal Design Readiness → SATISFIED

ns_server Batch 1 → GLOBAL_ACCEPTED
Accepted Batch-1 Boundaries → S1/S2/S3/S4/S8/S9
Accepted Batch-1 Internal Modules → 14
Accepted Batch-1 DAD → CID-SV-B1-DAD-001..013
RCP-01 → CLOSED AT DESIGN-SEMANTIC LEVEL
RCP-02 → CLOSED AT DESIGN-SEMANTIC LEVEL
RCP-19 → CLOSED AT DESIGN-SEMANTIC LEVEL
S8 Artifact Identity / Acceptance Evidence → CLOSED AT DESIGN-SEMANTIC LEVEL

Remaining Material ns_server Internal-design Pressure → PRESENT
ns_server Internal Design Exhaustion → NOT_SATISFIED
ns_server Batch-2 / S6 Readiness → SATISFIED

Open MDE at entry → 0
Unpersisted Owner Decision at entry → 0
Blocking Item → NONE
Known Working-branch Drift → NONE
Recovery Gate → PASS
```

The complete Current Required Read Set from Global State, Working State, Decision Registry, relevant Ledger tail, accepted Z3/Runtime/Foundation/Batch-1 evidence and precise Owner decisions were consumed. No chat summary, framework convention, workflow-engine convention or current code structure is used as authority.

---

# 2. Accepted Upstream Baseline

## 2.1 Permanent Automation Authority / SoT

```text
Automation Definition / Workflow Semantic Authority
→ ns_server

Automation Canonical Definition SoT
→ ns_server

Semantic Authority
!= Canonical Definition SoT
```

Both are co-located in `ns_server`, but remain independent semantic responsibilities.

Automation remains:

```text
FIRST_CLASS
PARALLEL
NON_SUBORDINATE
```

It is not a Business Application submodule, Agent submodule, Runtime implementation detail, Node execution submodule or generic workflow-engine abstraction.

## 2.2 Accepted Product Capabilities

The following are inherited and not reopened:

```text
Governed Event-driven Automation → REQUIRED
Reusable Automation-to-Automation Composition → REQUIRED
Governed Automation Human-in-the-loop → REQUIRED
Agent Dynamic Candidate Automation Authoring → REQUIRED
Complete Source / SDK Authoring → REQUIRED
Complete ns_web Visual Authoring → REQUIRED
Bidirectional Source↔Visual Semantic Interoperability → REQUIRED
Silent Semantic Loss → PROHIBITED
Lossless Representation Round-trip → NOT REQUIRED
Governed Pre-production Trial → REQUIRED
Universal Fully Isolated Simulation → NOT REQUIRED
```

## 2.3 Accepted Lifecycle Separation

```text
Automation Definition
!= Definition Validation
!= Domain Semantic Certification
!= Candidate Artifact
!= Formal Artifact Acceptance
!= Formal Execution Admission
!= Scheduling / Routing / Dispatch
!= Runtime Attempt
!= Protected Effect
!= Business / Automation Semantic Success automatically
```

Batch-1 inputs are consumed exactly:

```text
RCP-01 Governance Context
RCP-02 Admission Evidence
RCP-19 Desired / Applied Config
S8 Artifact Identity / Acceptance Evidence
```

Their identities, authorities, lifecycle and SoT semantics are not modified here.

## 2.4 Runtime Responsibility Baseline

`SV-R02` is accepted as the Automation Runtime Semantic Participant and owns S6-bounded Automation semantic runtime assertions.

S6/SV-R02 does not absorb:

```text
Formal Admission → S8 / G12 / SV-R04
Scheduling / Routing / Dispatch → ns_runtime / R2 / RT-R02
Cross-component continuation coordination → ns_runtime / R3 / RT-R03 only for coordination-stage facts
Node Attempt → N2 / ND-R02
Node Protected Effect → N3 / ND-R03
Agent Runtime → ns_agent / A2 / AG-R01
Human Task aggregation/projection → S11 / SV-R07
Human response submission occurrence → ns_web / W3 / WB-R01
```

Same journey never implies same Actual-state owner.

---

# 3. Owner MDE Produced During This Batch

During RCP-15 closure, recursion support was identified as a product-significant unresolved choice and escalated before dependent synthesis.

Persisted evidence:

`docs/governance/decisions/ns_evermore_cid_sv_b2_mde_001_automation_recursive_invocation_owner_decision_0.0.1.md`

Owner-selected result:

```text
CID-SV-B2-MDE-001
→ Option A

Native Automation-to-Automation Recursive Invocation
→ NOT SUPPORTED

Reusable Automation Composition
→ REQUIRED / PRESERVED

Composition semantic dependency graph
→ ACYCLIC
```

This does not prohibit ordinary retry/re-entry, repeated non-recursive callee invocation or future separately governed loop/iteration semantics inside an Automation. It prohibits invocation ancestry cycles created through Automation-to-Automation composition.

After persistence:

```text
Open MDE → 0
Unpersisted Owner Decision → 0
```

---

# 4. S6 Internal Responsibility Pressure Map

| Pressure | Stable semantic responsibility required | Principal owner in this Batch |
|---|---|---|
| Automation definition identity | definition semantic identity distinct from physical IDs/files/artifacts | AU01 |
| Canonical definition revision | immutable revision semantics, current vs historical, lineage/applicability | AU01 |
| Canonical Definition SoT custody | semantic state/history custody inside accepted ns_server SoT | AU01 |
| Source authoring intake | source-authored candidate enters same governed Automation domain | AU02 |
| Visual authoring intake | visual-authored candidate enters same governed Automation domain | AU02 |
| Agent-authored candidate intake | Agent origin/provenance retained; no Authority transfer | AU02 |
| Source↔Visual interoperability | explicit support/editability/limitation/incompatibility; no silent loss | AU02 |
| Definition validation | candidate semantic validity before canonical revision establishment | AU03 |
| Domain semantic certification participation | certification evidence for exact canonical revision, separate from Acceptance | AU03 |
| Initiation semantics | explicit / temporal-scheduled / event-trigger definition semantics without runtime coordination takeover | AU04 |
| Event source / trigger binding | source identity/provenance/revision/applicability | AU04 |
| Event occurrence / trigger evaluation | evaluation identity/result/evidence, duplicate/replay/order uncertainty | AU05 |
| Composition definition | caller/callee reference, binding identity/revision/applicability | AU06 |
| Composition revision binding | exact historical resolution; no silent latest; acyclic recursion rule | AU06 |
| Runtime operation identity | admitted Automation semantic operation identity | AU07 |
| Continuation | wait/continue/terminal semantic state and downstream evidence interpretation | AU07 |
| Retry / re-entry / intervention | lineage preserved; request != outcome; prior attempts/effects retained | AU07 |
| Automation HITL | Human Action Requirement, Automation Wait Requirement, response applicability, resume/branch/terminate | AU08 |
| Trial | trial subject/context/effect boundary/result distinct from production | AU09 |
| Historical interpretation | exact definition/trigger/composition/governance/admission/effect/HITL/trial context | all, coordinated by owning subject |
| Offline / degraded | bounded retained evidence; no Authority transfer/fail policy invention | all applicable |
| Recovery / reconciliation | re-observation/provenance-preserving reconciliation; no latest-wins | AU05/AU07/AU08/AU09 |
| Compatibility / migration / conformance | semantic owner judgment + accepted Foundation mechanics | all |
| Secret boundary | definitions carry Secret References only where required; ordinary S6 state does not custody material | AU01/AU04/AU06/AU09 |

Mechanical `Definition/Trigger/Composition/Runtime/HITL/Trial = six Modules` was rejected. The pressure map instead separates canonical state, authoring/evidence processing, definition constituents and SV-R02 actual-state partitions by lifecycle cohesion.

---

# 5. Internal Module Derivation Method

Module boundaries are derived using:

```text
semantic authority cohesion
canonical-definition lifecycle cohesion
identity/revision lifecycle
state-transition responsibility
semantic persistence responsibility
cross-boundary Contract responsibility
source-fact vs derived-evidence ownership
runtime Actual-state ownership
history/provenance
source/visual interoperability
event provenance
composition binding
HITL wait/resume
trial semantics
offline/recovery
compatibility/migration/conformance
```

The following were specifically rejected:

```text
S6 = one God Module
RCP-13 = one Module automatically
RCP-14 = one Module automatically
RCP-15 = one Module automatically
one module per noun
Django App boundaries
workflow-engine component taxonomy
state-machine package taxonomy
queue/scheduler/worker topology
```

---

# 6. Derived Internal Module Inventory

`AU01..AU09` are document-local navigation labels only. Their architecture identity is the responsibility name/meaning.

| Local | Internal Architecture Module | Primary stable responsibility |
|---|---|---|
| AU01 | Automation Definition & Canonical Revision Governance | Automation Definition identity, canonical revision lifecycle, lineage and accepted Definition SoT custody |
| AU02 | Authoring Intake & Semantic Interoperability | source/visual/Agent candidate intake, origin provenance and cross-surface semantic interoperability |
| AU03 | Definition Validation & Semantic Certification Evidence | candidate validation and exact canonical-revision certification evidence, separate from Acceptance |
| AU04 | Initiation & Trigger Definition Governance | explicit/temporal/event initiation definition semantics, trigger identity/revision/source binding/applicability |
| AU05 | Event Provenance & Trigger Evaluation | event occurrence evidence intake and SV-R02 trigger-evaluation state/evidence |
| AU06 | Automation Composition & Revision Binding Governance | caller/callee composition reference, binding revision, dependency compatibility and acyclic composition semantics |
| AU07 | Automation Operation & Semantic Continuation | SV-R02 Automation runtime operation/continuation Actual-state and downstream evidence interpretation |
| AU08 | Automation HITL Wait & Response Applicability | Automation Human Action Requirement, wait state, response applicability and semantic resume/branch/terminate consequences |
| AU09 | Automation Trial Semantics & Runtime Evidence | Automation-side governed Trial identity/context/effect-boundary/semantic runtime/result state |

```text
Derived Internal Module Count → 9
Authorized Boundary Coverage → S6 / 1 OF 1
Unowned S6 Responsibility → 0
Duplicate Final Responsibility → 0
God Module → NONE_FOUND
Overfragmentation → NONE_FOUND
```

---

# 7. S6 Boundary Coverage Matrix

| S6 responsibility | AU01 | AU02 | AU03 | AU04 | AU05 | AU06 | AU07 | AU08 | AU09 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Definition identity/revision/SoT | P |  | C | C |  | C | C | C | C |
| Source/Visual intake |  | P | C | C |  | C |  | C |  |
| Agent candidate intake |  | P | C |  |  |  |  |  |  |
| Semantic interoperability |  | P | C | C |  | C |  | C |  |
| Validation/certification | C | C | P | C |  | C |  | C | C |
| Trigger definition | C | C | C | P | C |  |  |  |  |
| Trigger evaluation/event provenance |  |  |  | C | P |  | C |  | C |
| Composition definition/binding | C | C | C |  |  | P | C |  | C |
| Runtime operation/continuation | C |  |  |  | C | C | P | C | C |
| HITL source/wait/resume | C | C | C |  |  |  | C | P | C |
| Trial | C |  | C |  | C | C | C | C | P |
| History/offline/recovery | P | P | P | P | P | P | P | P | P |

`P = principal owner`, `C = consumed/contributing responsibility`.

---

# 8. Per-Module Architecture Definitions

## AU01 — Automation Definition & Canonical Revision Governance

- **Source Boundary:** S6.
- **Purpose:** realize the accepted Automation Semantic Authority and Automation Canonical Definition SoT as distinct logical responsibilities while owning canonical Definition identity/revision lifecycle.
- **Owned Responsibility:** Automation Definition Identity; canonical Definition Revision; revision lineage; one current canonical revision designation per governed Definition identity/Tenant scope; definition applicability; retirement from new governed use; historical resolvability.
- **Explicitly Non-owned:** source file/editor state; semantic validation result; certification evidence; candidate Artifact; Formal Acceptance; Admission; trigger evaluation; composition invocation; runtime attempt/effect; runtime coordination.
- **Automation Semantic Authority Relationship:** AU01 is the principal internal custodian through which S6 exercises accepted Automation semantic authority for canonical definition meaning. It does not create a new authority.
- **Automation Definition SoT Relationship:** AU01 is semantic custodian of accepted Automation Canonical Definition SoT state/history. Semantic Authority and SoT remain distinct even inside AU01.
- **Owned State:** Definition identities; immutable canonical revision snapshots; current-revision designation; lineage/provenance; definition-level applicability/retirement state.
- **Consumed State:** validated candidate semantics from AU02/AU03; trigger/composition/HITL constituent semantics from AU04/AU06/AU08; Governance Context where definition mutation is governed.
- **Runtime Actual-state / Source-fact:** none. Runtime copies/caches do not become SoT.
- **Identity:** Definition Identity and Definition Revision are distinct. No UUID/PK/slug/file/package syntax is selected.
- **Revision:** a canonical revision identity resolves to one fixed semantic snapshot. Semantic modification produces another revision; old revision is not mutated.
- **Lifecycle:** establish Definition identity → validate candidate change → establish new canonical revision → designate current revision → later supersede or retire for new governed use. Retirement does not automatically revoke Accepted Artifacts or Admission evidence.
- **Persistence Semantic Responsibility:** authoritative semantic persistence custody for current/historical canonical Definition state; physical storage deferred.
- **Governance Context:** Tenant mandatory; Organization separate where applicability needs it; Principal author/actor provenance explicit; Policy/Trust govern mutation/use without becoming Automation Authority.
- **Artifact / Acceptance / Admission:** AU03 certification evidence may reference AU01 revision; G11/G12 remain external accepted owners. `Canonical Revision != Accepted Artifact != Admission`.
- **Managed Config:** Automation definition semantics are not Managed Runtime Configuration. Runtime configuration references consume RCP-19 separately.
- **Secret Boundary:** canonical definitions may contain governed Secret References, never ordinary Secret Material.
- **Offline / Degraded:** retained exact revisions may support governed interpretation where authorized, but local copies never become Canonical SoT. No public Internet dependency.
- **Failure / Unknown:** missing revision, ambiguous lineage, unsupported revision, conflicting current designation or unavailable historical evidence remain explicit.
- **Recovery / Reconciliation:** re-observe canonical revision state from S6 authority; no latest local copy/current timestamp wins.
- **Replay:** replay/history lookup never mutates canonical state or reinterprets old revision using current revision.
- **Historical Interpretation:** every operation/trial/certification/binding references exact AU01 revision; current definition never rewrites history.
- **Compatibility / Migration / Conformance:** semantic evolution uses accepted compatibility classes; definition migration creates explicit new revision/lineage; incompatible revisions are not silently coerced.
- **Foundation Consumption:** C02/C03 diagnostics/telemetry; C04 temporal; C05 provenance; C06 representation; C09 durable mechanics; C10 uncertainty; C11 governed context; C12/C13 reference/redaction; C14 compatibility/conformance.
- **Internal Dependencies:** no hard SDD dependency. AU02/AU03/AU04/AU06/AU07/AU08/AU09 depend on AU01 semantics.
- **Cross-boundary Dependencies:** G10 governance context; G11 Artifact Acceptance; G12 Admission; future W2/SDK authoring consumers.
- **External Contract Responsibility:** authoritative Definition identity/revision reference semantics consumed by RCP-13/14/15/16/17.
- **Non-goals:** DSL, AST, IR, source format, visual schema, package/file layout, ORM/table, workflow engine.
- **Named Downstream Deferrals:** physical representation/API/storage/Django realization → later detailed/implementation authorities; System-level SDK methods remain unauthorized.
- **Revalidation Trigger:** Automation Authority/SoT movement, mutable historical revision semantics, source/editor/artifact becoming SoT, major identity-format commitment.

## AU02 — Authoring Intake & Semantic Interoperability

- **Source Boundary:** S6.
- **Purpose:** provide one governed S6 semantic intake for complete source/SDK authoring, complete visual authoring and Agent-authored Automation candidates.
- **Owned Responsibility:** Authoring Submission/Candidate identity; authoring origin/provenance; intended new/existing Definition association; semantic intake normalization responsibility; cross-surface support/editability/representation limitation assessment; candidate handoff to validation/canonical lifecycle.
- **Explicitly Non-owned:** Automation Authority/SoT; SDK API; visual editor internals; parser/compiler; canonical source/IR; final validation/certification; Acceptance/Admission; Agent reasoning.
- **Authority / SoT Relationship:** authority-neutral intake under S6; no source, visual or Agent origin gains Automation Authority or SoT.
- **Owned State:** candidate submission/provenance/history and interoperability assessment evidence; no canonical Definition state.
- **Consumed State:** AU01 base identities/revisions; AU04/AU06/AU08 authorable semantic constructs; AU03 validation results; Agent provenance references where source is Agent-authored.
- **Runtime Actual-state / Source-fact:** none.
- **Identity / Revision:** Authoring Candidate Identity is distinct from Definition Identity/Revision. Candidate may propose a new Definition identity or a new revision of an existing one; AU01 controls canonical establishment.
- **Lifecycle:** receive semantic candidate → preserve origin → assess receiving-surface semantics → hand to AU03 validation → on successful governed canonical intake AU01 establishes revision; failed/unsupported candidates remain candidate evidence only.
- **Persistence Semantic Responsibility:** retain candidate/provenance/interoperability evidence sufficient for history/audit/re-delivery; not SoT.
- **Interoperability Vocabulary:** `SUPPORTED_EDITABLE`, `SUPPORTED_NON_EDITABLE`, `REPRESENTATION_LIMITED`, `UNSUPPORTED`, `INCOMPATIBLE`, `INDETERMINATE` with `UNKNOWN` where evidence itself is unavailable. Exact UI labels may differ while meanings conform.
- **Semantic Loss Rule:** receiving surface may not silently drop/reinterpret governed semantics. A non-editable surface may preserve/observe the semantics but must block destructive edit/save that would lose meaning.
- **Governance Context:** Tenant/Principal required for governed mutation; Organization/Policy/Trust applied as applicable; authoring surface never bypasses governance.
- **Artifact / Admission:** candidate authoring is pre-Artifact and pre-Admission.
- **Managed Config:** none owned.
- **Secret Boundary:** authoring surfaces exchange Secret References only; raw material must not be embedded into ordinary Automation definition intake or diagnostics.
- **Offline / Degraded:** source/visual/Agent candidate authoring and compatibility feedback must remain realizable without public SaaS converter/registry.
- **Failure / Unknown:** invalid/unsupported/incompatible/representation-limited/indeterminate states explicit; no best-effort coercion.
- **Recovery / Replay:** replaying/importing a candidate preserves original origin/revision and does not auto-canonicalize it.
- **Historical Interpretation:** source/visual/Agent origin remains provenance; canonical revision is the historical semantic authority once established.
- **Compatibility / Migration / Conformance:** cross-surface semantics follow Owner-selected interoperability guarantee; representation-local metadata is not automatically a compatibility promise; semantic migration is explicit.
- **Foundation Consumption:** C04/C05/C06/C10/C11/C12/C13/C14; C09 if durable candidate history is retained; C02/C03 for diagnostics.
- **Internal Dependencies:** SDD on AU01/AU04/AU06/AU08 semantic subject definitions; ACD to AU03 for validation.
- **Cross-boundary Dependencies:** W2/`ns_web` visual authoring future consumer; System-level SDK source surface; AG-R04 candidate producer.
- **External Contract Responsibility:** S6 side of stable Automation semantic authoring intake/interoperability obligations; no new wire/API contract is frozen.
- **Non-goals:** SDK methods, decorators, source DSL, visual node schema, AST/IR, converter, code generator.
- **Named Deferrals:** source/visual representations and physical conversion mechanics → later authorized component/SDK detailed design.
- **Revalidation Trigger:** silent semantic loss permitted, separate source-only/visual-only Automation semantic classes, authoring surface becomes SoT/Authority, mandatory physical representation.

## AU03 — Definition Validation & Semantic Certification Evidence

- **Source Boundary:** S6.
- **Purpose:** separate candidate Definition Validation from Domain Semantic Certification evidence and from Formal Artifact Acceptance.
- **Owned Responsibility:** validation attempt identity/result; semantic diagnostic evidence; compatibility/conformance assessment for Automation semantics; certification evidence for an exact canonical revision under the already accepted S6 Automation semantic authority.
- **Explicitly Non-owned:** independent Certification Authority; Canonical Definition SoT; Formal Artifact Acceptance; Admission; Artifact format/signature; runtime trial result.
- **Authority / SoT Relationship:** AU03 does not create a new material Certification Authority. A certification determination is an exercise/evidence of the already accepted Automation Semantic Authority; its evidence does not become Definition SoT.
- **Owned State:** validation/certification evidence identity, revision, result, provenance, applicable semantic rules/definition revision references, history.
- **Consumed State:** AU02 candidate; AU01 canonical revision; AU04 trigger semantics; AU06 composition/binding; AU08 HITL definition semantics; G10 governance context where required.
- **Runtime Actual-state / Source-fact:** none; Trial is AU09 and runtime facts remain source-owned.
- **Identity / Revision:** Validation Evidence Identity and Certification Evidence Identity are distinct from Definition/Artifact identities. Certification always pins an exact canonical Definition Revision.
- **Lifecycle:** pre-canonical candidate validation → canonical revision establishment by AU01 → exact-revision semantic certification/conformance assessment → evidence may accompany candidate Artifact lifecycle.
- **Persistence Semantic Responsibility:** durable evidence/history sufficient for Acceptance linkage and historical interpretation.
- **Governance Context:** Tenant and actor provenance; Policy/Trust may govern certification action but do not define Automation semantics.
- **Artifact Acceptance Relationship:** G11 consumes certification evidence as input; `Certified != Accepted`.
- **Admission Relationship:** no Admission decision; certification may be part of later prerequisites only.
- **Managed Config / Secret:** validation config semantics are S6-owned if any; managed Desired remains S9; Secret Material excluded from evidence/diagnostics.
- **Offline / Degraded:** local/private validation/certification must not require public control plane; unavailable semantic dependency yields explicit state.
- **Failure / Unknown:** `INVALID`, `UNSUPPORTED`, `INCOMPATIBLE`, `INDETERMINATE`, missing dependency/evidence and representation limitation remain distinct from Accepted/Rejected Artifact state.
- **Recovery / Replay:** revalidation produces new evidence identity; previous result is not overwritten; replaying old validation against new revision is not assumed equivalent.
- **Historical Interpretation:** exact rules/revision/provenance used remain resolvable.
- **Compatibility / Migration / Conformance:** AU03 is principal S6 judge for semantic compatibility/conformance; C14 provides mechanics only.
- **Foundation Consumption:** C04/C05/C06/C09/C10/C11/C13/C14 plus diagnostics/telemetry.
- **Internal Dependencies:** SDD on AU01/AU04/AU06/AU08; ACD/EL with AU02 candidate evidence.
- **Cross-boundary Dependencies:** G11 Acceptance consumes certification evidence; W2/SDK consume diagnostics/compatibility feedback.
- **External Contract Responsibility:** producer of Automation domain semantic-certification evidence referenced by S8 Acceptance contract; no Artifact Acceptance contract redefinition.
- **Non-goals:** compiler/parser/test runner/artifact builder/signing/registry.
- **Named Deferrals:** concrete validation language/tool/schema/diagnostic representation.
- **Revalidation Trigger:** certification promoted to Formal Acceptance, new independent certification authority/SoT proposed, major compatibility commitment not derivable upstream.

## AU04 — Initiation & Trigger Definition Governance

- **Source Boundary:** S6.
- **Purpose:** own Automation initiation/trigger definition semantics while preserving runtime scheduling/dispatch ownership elsewhere.
- **Owned Responsibility:** Trigger Definition Identity/Revision; association with exact Automation Definition Revision; initiation class semantics for explicit invocation, temporal/scheduled trigger and governed event trigger; event-source binding/reference; trigger applicability and supported event semantic revision constraints.
- **Explicitly Non-owned:** event occurrence fact; event transport; trigger evaluation result; runtime scheduling/dispatch; cron/expression/schema; event broker.
- **Authority / SoT Relationship:** trigger semantics are a specialized canonical constituent under the accepted S6 Automation Authority/Canonical Definition SoT, not a new SoT.
- **Owned State:** trigger definition/binding revision/history and applicability. Any change to semantically relevant trigger behavior requires a new trigger/binding revision and a new applicable Automation canonical revision association.
- **Consumed State:** AU01 Definition identity/revision; Tenant/Governance Context; bounded source identity references.
- **Runtime Actual-state / Source-fact:** none; event source fact remains source-owned; evaluation Actual-state is AU05.
- **Identity / Revision:** Trigger Definition Identity != Event Source Identity != Event Occurrence Identity != Trigger Evaluation Identity.
- **Lifecycle:** define trigger → validate/certify with owning Automation revision → supersede/retire trigger revision; historical revision remains addressable.
- **Persistence Semantic Responsibility:** canonical trigger constituent state/history inside accepted Automation Definition SoT custody.
- **Governance Context:** Tenant mandatory; source binding cannot establish Tenant/Policy/Trust authority by itself.
- **Artifact / Admission:** trigger validity/certification does not imply Artifact Acceptance/Admission.
- **Managed Config:** operational schedule/runtime config remains separate; definition-level trigger meaning belongs S6.
- **Secret Boundary:** integration/source credentials referenced only by Secret Reference; Secret Material not trigger definition state.
- **Offline / Degraded:** private/local event sources and temporal triggers must remain representable without public broker/SaaS; missing source availability is not Definition SoT transfer.
- **Failure / Unknown:** unknown source, unsupported event revision, unavailable source profile or incompatible trigger semantics explicit.
- **Recovery / Replay:** trigger revision history remains fixed; replay never changes the original trigger revision automatically.
- **Historical Interpretation:** trigger evaluation history references exact Trigger Revision + Automation Revision.
- **Compatibility / Migration / Conformance:** event-source/trigger revisions explicitly compatible/incompatible/unsupported; trigger migration creates new revision and does not rewrite prior evaluations.
- **Foundation Consumption:** C04 temporal/freshness; C05 provenance; C06 representation; C09 durable; C10 uncertainty; C11 governed context; C12/C13 secret ref/redaction; C14 compatibility.
- **Internal Dependencies:** SDD `AU04 → AU01`.
- **Cross-boundary Dependencies:** event sources as bounded external owners; RT-R02 for scheduling/dispatch only after Admission; AU05 evaluator.
- **External Contract Responsibility:** Trigger-definition producer side of RCP-14; temporal/scheduled trigger realization remains runtime-coordination downstream without new RCP design here.
- **Non-goals:** cron syntax, calendar engine, broker/topic/webhook, event envelope, queue delivery guarantee.
- **Named Deferrals:** concrete trigger representation, temporal scheduling mechanics, event connector/transport.
- **Revalidation Trigger:** Event Source becomes Automation/Policy/Admission Authority, trigger semantics move outside S6, major stable event/protocol commitment.

## AU05 — Event Provenance & Trigger Evaluation

- **Source Boundary:** S6 / SV-R02.
- **Purpose:** consume provenance-bearing Event Occurrence evidence and own the Automation Trigger Evaluation semantic Actual-state without taking Event Source authority.
- **Owned Responsibility:** Event Observation correlation; Trigger Evaluation Identity; evaluation against exact Trigger/Automation revisions; result/evidence; duplicate/replay/stale/out-of-order/conflicting-provenance qualification; matched-evaluation-to-execution-intent production.
- **Explicitly Non-owned:** Event Source factual authority; event broker/transport state; Formal Admission; dispatch; executor attempt/effect.
- **Authority / SoT Relationship:** Automation trigger meaning remains S6; occurrence fact remains bounded source-owned; AU05 owns only S6 evaluation state/evidence.
- **Owned State / Actual-state:** final owner for Trigger Evaluation result/evidence and its current/historical evaluation lifecycle inside SV-R02.
- **Consumed State:** AU04 trigger revision/source binding; event source occurrence evidence; AU01 Automation revision; G10 governance context where required.
- **Source-fact Relationship:** `Event Occurred` is source-owned; AU05 stores/references evidence/provenance but does not canonicalize external facts.
- **Identity / Revision:** Event Source Identity, Event Occurrence Identity, Event semantic revision where applicable, Trigger Definition Identity/Revision and Trigger Evaluation Identity remain distinct.
- **Temporal:** source occurrence time/context and platform observation/re-observation time are distinct; later observation does not become later occurrence.
- **Evaluation Results:** at minimum `MATCHED`, `NOT_MATCHED`, `INDETERMINATE`, `UNSUPPORTED/INCOMPATIBLE`, plus explicit `STALE`, `CONFLICTING`, `UNKNOWN/UNVERIFIED` conditions where applicable.
- **Duplicate:** re-observation of the same established Event Occurrence identity is not a new occurrence. It must not silently create a new execution intent.
- **Replay:** original occurrence is immutable; explicit Replay/Re-evaluation Request creates a new Trigger Evaluation Identity against an explicitly identified Trigger Revision. A matched re-evaluation creates a new execution intent and requires applicable new Admission; original Admission is never assumed reusable.
- **Out-of-order:** no global total order. If trigger semantics require ordering/freshness and admissible source evidence cannot establish it, result remains stale/indeterminate rather than guessed.
- **Lifecycle:** occurrence evidence observed → applicability/source verification → trigger evaluation → result/evidence → optional execution-intent creation → history. Evaluation result does not itself become Admission.
- **Persistence Semantic Responsibility:** durable evaluation/provenance/history and duplicate/replay correlation; event source data retained only as required evidence/reference under privacy rules.
- **Governance Context:** Tenant/source mapping, Principal/Policy/Trust when relevant; event producer never grants authorization.
- **Artifact / Admission:** `Trigger Matched != Execution Admitted`; matched result produces intent for G12/RCP-02.
- **Managed Config / Secret:** runtime event integration config via accepted config topology; Secret Material excluded from evaluation evidence.
- **Offline / Degraded:** private/local source evidence may be evaluated where exact trigger/governance state is available; source unavailable remains explicit; no public event service required.
- **Failure / Unknown:** unknown source, unavailable source, unsupported revision, duplicate identity indeterminate, stale/order ambiguity, conflicting provenance all explicit.
- **Recovery / Reconciliation:** re-observe source/evaluation evidence; same occurrence/evaluation history is preserved; no latest timestamp canonicalization.
- **Historical Interpretation:** exact occurrence source/revision + trigger/Automation revision + governance context + resulting intent/admission references retained.
- **Compatibility / Migration / Conformance:** event/trigger version compatibility explicit; source transport migration does not change event authority; old evaluations never reinterpreted using current trigger.
- **Foundation Consumption:** C04/C05/C06/C09/C10/C11/C13/C14; C07/C08 only conditionally as mechanics; diagnostics/telemetry.
- **Internal Dependencies:** SDD `AU05 → AU04`; ACD/EL to AU01/G10; XED to event source authority.
- **Cross-boundary Dependencies:** event producer; G12 Admission; RT/executors only after admitted intent.
- **External Contract Responsibility:** principal S6 producer/consumer side of RCP-14.
- **Non-goals:** exactly-once delivery, global ordering, sequence schema, broker dedup, offset/topic/ack semantics.
- **Named Deferrals:** transport/envelope/connector/dedup algorithm/order mechanism.
- **Revalidation Trigger:** event receipt becomes Admission, transport becomes source authority, global exactly-once/total-order product guarantee proposed.

## AU06 — Automation Composition & Revision Binding Governance

- **Source Boundary:** S6.
- **Purpose:** own reusable Automation-to-Automation composition definition, caller/callee revision relationship, dependency compatibility and Owner-selected acyclic recursion semantics.
- **Owned Responsibility:** Composition Reference Identity; Binding Identity/Revision; caller Definition/Revision; callee Definition/Revision target semantics; binding applicability; composition dependency validation; independent callee lifecycle; historical dependency resolution.
- **Explicitly Non-owned:** callee Automation Authority/SoT transfer; Formal Acceptance/Admission; runtime scheduling/routing/dispatch; executor attempt/effect; graph/DAG representation.
- **Authority / SoT Relationship:** composition is part of S6 Automation semantics and accepted Definition SoT; caller never becomes callee Authority and vice versa.
- **Owned State:** canonical composition binding definitions/revisions/history as specialized constituents under the caller Automation canonical revision.
- **Consumed State:** AU01 caller/callee identities/revisions; AU03 compatibility/certification; Governance Context where applicable.
- **Runtime Actual-state / Source-fact:** definition-side only; runtime Composition Invocation lineage is finalized through AU07 under RCP-15.
- **Identity / Revision:** Caller Definition Identity/Revision, Callee Definition Identity/Revision, Composition Reference Identity and Binding Revision remain distinct.
- **Revision Binding:** baseline composition must support explicit exact callee-revision binding. Additional selector/range modes are not a Product guarantee in this Batch and require later revalidation before changing stable semantics. `silent latest-version binding` is prohibited.
- **Lifecycle:** establish binding in caller revision → validate callee existence/compatibility/acyclicity → certify caller revision → later create new binding/caller revision to change dependency. Callee lifecycle remains independent.
- **Acyclic Rule:** per `CID-SV-B2-MDE-001`, direct/indirect recursive invocation cycles are unsupported. Canonical composition dependency among exact governed revisions must be acyclic.
- **Persistence Semantic Responsibility:** canonical binding current/history state inside accepted Automation SoT; physical graph/storage deferred.
- **Governance Context:** Tenant alignment mandatory; cross-Tenant composition is not introduced; Principal/Policy/Trust apply without authority transfer.
- **Artifact / Admission:** composition never bypasses G11/G12. A callee invocation must be covered by Admission evidence applicable to the exact callee execution intent/revision; parent Admission is not presumed to cover it.
- **Managed Config / Secret:** composition definition may carry governed references, including Secret References only where semantically legitimate; no material custody.
- **Offline / Degraded:** exact callee revision/binding and required governance evidence must be available/applicable; missing dependency is explicit rather than rebound to latest.
- **Failure / Unknown:** missing/unsupported/stale/incompatible/conflicting binding or unavailable callee remains explicit; callee failure does not automatically equal caller failure.
- **Recovery / Replay:** recover historical exact binding; replay/new invocation does not re-resolve to current callee silently.
- **Historical Interpretation:** every invocation records exact caller revision, binding revision and callee revision used.
- **Compatibility / Migration / Conformance:** binding change creates new binding/caller revision; migration must preserve lineage; recursive legacy definitions remain unsupported/incompatible and require explicit migration.
- **Foundation Consumption:** C04/C05/C06/C09/C10/C11/C13/C14 plus diagnostics/telemetry.
- **Internal Dependencies:** SDD `AU06 → AU01`; ACD to AU03.
- **Cross-boundary Dependencies:** G11/G12 governance; RT-R03/RT-R02 coordination; callee AU07 semantic result.
- **External Contract Responsibility:** definition/binding side of RCP-15.
- **Non-goals:** DAG/graph/subflow schema, version-range syntax, lockfile, call stack, sync/async protocol, transaction model.
- **Named Deferrals:** physical representation, dispatch realization, optional future binding selector modes.
- **Revalidation Trigger:** recursion enabled, silent latest binding permitted, caller/callee authority collapse, major binding compatibility commitment beyond baseline.

## AU07 — Automation Operation & Semantic Continuation

- **Source Boundary:** S6 / SV-R02.
- **Purpose:** own Automation semantic Runtime Operation and Continuation Actual-state while interpreting downstream coordination/attempt/effect evidence without acquiring their source-fact authority.
- **Owned Responsibility:** Automation Runtime Operation Identity; Continuation Identity; operation/continuation state/history; origin/parent correlation; definition revision pinning; admission reference; composition invocation lineage; wait/continue/terminal semantic outcome interpretation; retry/re-entry/intervention relationships.
- **Explicitly Non-owned:** target Execution Intent Admission decision; RT scheduling/routing/dispatch facts; Node/server-local attempt/effect; Agent runtime; Human Task aggregation; web submission occurrence.
- **Authority / SoT Relationship:** runtime semantic state is S6/SV-R02 bounded Actual-state, not Canonical Definition SoT and not a new Product Authority.
- **Owned State / Actual-state:** final owner for Automation semantic runtime assertions such as operation established, semantic continuation/wait reason, callee-result relationship, semantic terminal result and reconciliation status.
- **Source-fact Relationship:** attempt/effect/dispatch evidence remains owned by its producer; AU07 records references and derives Automation semantic consequence only.
- **Identity:** Target Execution Intent Identity != Admission Evidence Identity != Automation Runtime Operation Identity != Continuation Identity != Dispatch != Attempt != Effect.
- **Operation Creation:** an Automation Runtime Operation is established only from an applicable formally admitted execution intent; Operation references but does not own Admission.
- **Revision Pinning:** operation pins exact Automation Definition Revision and all applicable Trigger/Composition binding revisions. No silent live rebinding to current revisions.
- **Semantic State Categories:** non-terminal `ADMITTED_AWAITING_COORDINATION`, `ACTIVE/CONTINUING`, `WAITING_HUMAN`, `WAITING_CALLEE`, `WAITING_DOWNSTREAM_EVIDENCE`, `CONTINUATION_ELIGIBLE`; terminal semantic outcomes `SUCCEEDED`, `FAILED`, `TERMINATED`, `PARTIAL`; uncertainty `UNKNOWN`, `INDETERMINATE`, `STALE`, `RECONCILIATION_PENDING` where applicable. These are semantic categories, not a required implementation state-machine layout.
- **Attempt / Effect Interpretation:** Attempt failure does not automatically terminate the Automation; Effect occurrence does not automatically imply Automation success. AU07 applies the pinned Automation semantics to evidence.
- **Retry / Re-entry:** Retry Request != Retry Started; new attempts retain origin/attempt/effect lineage; prior effects are never erased/reversed by retry. Resume/recovery may continue the same operation only when exact continuation/admission applicability remains establishable; a new execution intent requires its own Admission.
- **Intervention:** cancel/retry/resume/recovery requests are intent/evidence; final semantic result is owned by the applicable actual-state owner and interpreted by AU07. Request != outcome.
- **Lifecycle:** admitted intent → operation established → coordination/attempt/evidence cycles → semantic waits/continuations → terminal/partial/indeterminate result; no runtime-process design.
- **Persistence Semantic Responsibility:** authoritative S6 runtime semantic state/history/provenance; not executor fact storage authority.
- **Governance Context:** exact RCP-01 context and RCP-02 admission refs retained; Policy/Trust current state never rewrites historical operation automatically.
- **Artifact / Admission:** consumes G11/G12 evidence; does not issue Acceptance/Admission.
- **Managed Config:** consumes desired/applied config references as applicable; configuration state never replaces operation semantics.
- **Secret Boundary:** operation state stores references/redacted evidence only; no ordinary Secret Material.
- **Offline / Degraded:** downstream facts may become unreachable/stale while operation state remains waiting/unknown; no local authority transfer/fail policy invented.
- **Recovery / Reconciliation:** re-observe dispatch/attempt/effect/HITL/callee evidence; reconnect != reconciled; unresolved conflict remains explicit.
- **Replay:** history replay is observation only. Re-execution is a new execution intent/new Admission unless explicitly a still-applicable retry/re-entry of the same operation.
- **Historical Interpretation:** exact Definition/Trigger/Binding/Governance/Admission/Dispatch/Attempt/Effect/HITL/Trial references retained as applicable.
- **Compatibility / Migration / Conformance:** running operations do not silently migrate to new Definition revisions. Any future live operation migration is not established by this Batch and would require revalidation.
- **Foundation Consumption:** C04/C05/C06/C09/C10/C11/C13/C14 plus diagnostics/telemetry; C08 optional bounded evidence cache only.
- **Internal Dependencies:** SDD `AU07 → AU01, AU06`; EL/ACD from AU05/G12/RT/executors.
- **Cross-boundary Dependencies:** RCP-02 Admission, RCP-05 Dispatch evidence, RCP-06 coordination/intervention, RCP-07/08 attempt/effect, S11/W3 HITL evidence, without redesigning those contracts.
- **External Contract Responsibility:** principal producer/steward of RCP-13 and runtime invocation side of RCP-15.
- **Non-goals:** worker/process/state-machine engine, exactly-once, universal compensation/rollback, dispatch algorithm.
- **Named Deferrals:** physical state storage, runtime coordination protocol, retry algorithms/process topology.
- **Revalidation Trigger:** S6 loses Automation runtime Actual-state, attempt/effect ownership absorbed, live revision rebinding introduced, universal exactly-once/reversal guarantee.

## AU08 — Automation HITL Wait & Response Applicability

- **Source Boundary:** S6 / SV-R02.
- **Purpose:** close the Automation-originated Human Task source semantics and own Automation wait/response-applicability/resume semantic state without designing S11/W3/Agent HITL internals.
- **Owned Responsibility:** Human Action Requirement semantic subject; Automation Wait Requirement Identity; originating Operation/Continuation/Definition Revision; required human context; response applicability criteria; response observed/applicable/stale/conflicting/rejected/applied interpretation; semantic resume/branch/terminate consequence.
- **Explicitly Non-owned:** unified task aggregation/inbox; assignment/claim/delegation; Agent Human Task; web submission fact; Policy approval; Artifact Acceptance; Admission; runtime coordination protocol.
- **Authority / SoT Relationship:** HITL meaning remains Automation S6 semantics; Human response is evidence/input, not Automation Authority.
- **Owned State / Actual-state:** final owner for Automation `WAITING_HUMAN` requirement and response applicability/application/resume semantic state inside SV-R02.
- **Consumed State:** AU01 exact Definition Revision; AU07 Operation/Continuation; G10 governance context; routed response reference/provenance from future S11/W3 path.
- **Identity / Revision:** Human Action Requirement semantic identity (definition-side where applicable) != runtime Automation Wait Requirement Identity != Human response submission identity.
- **Lifecycle:** canonical definition declares human-action semantics → admitted operation reaches wait → wait requirement established → response observed → applicability assessed → rejected/stale/conflicting/indeterminate or applied → new continuation/branch/terminate result. UI submission alone never resumes Automation.
- **Response Applicability:** at minimum distinguish `APPLICABLE`, `STALE`, `CONFLICTING`, `REJECTED`, `UNVERIFIED`, `INDETERMINATE`, with wrong Tenant/Principal/operation/revision treated as non-applicable under governed evidence.
- **Persistence Semantic Responsibility:** authoritative wait/applicability/application/history and response provenance references; source submission remains external fact.
- **Governance Context:** Tenant mandatory; Principal eligibility/provenance explicit; Organization where definition semantics require; Policy/Trust references do not make response a Permit/Admission.
- **Artifact / Admission:** Human response never accepts Artifact or admits execution. Resume continuation remains within applicable admission or requires a new intent/admission when applicability no longer covers continuation.
- **Managed Config / Secret:** no task assignment config designed; sensitive human context/response disclosure must be minimized/redacted; Secret Material excluded.
- **Offline / Degraded:** wait state survives browser/session loss; offline response possession does not imply application; after reconnect response is re-observed and applicability re-evaluated.
- **Failure / Unknown:** stale, conflicting, duplicate, missing, wrong-context, unavailable routing and indeterminate applicability explicit; no latest-response-wins rule.
- **Recovery / Reconciliation:** re-observe routed response and current operation wait state; preserve all submission provenance; reconnect != resumed/reconciled.
- **Replay:** replaying a response record does not apply it again automatically; applicability is evaluated against current pinned wait/operation context.
- **Historical Interpretation:** historical wait/resume references exact Automation revision, operation/continuation, required Principal/context and applied response evidence.
- **Compatibility / Migration / Conformance:** Human Action Requirement evolution must preserve historical wait interpretation; active waits do not silently migrate to new Definition revision.
- **Foundation Consumption:** C04/C05/C06/C09/C10/C11/C13/C14 plus diagnostics/telemetry.
- **Internal Dependencies:** SDD `AU08 → AU01, AU07`.
- **Cross-boundary Dependencies:** future S11/SV-R07 aggregation/routing; W3/WB-R01 submission occurrence; RT-R03 coordination only where cross-component resume coordination is needed.
- **External Contract Responsibility:** S6-owned source/wait/applicability side of RCP-16 only.
- **Non-goals:** full RCP-16 closure, task DB/schema, assignment engine, timeout/escalation model, Inbox internals, web UI.
- **Named Downstream Deferrals:** S11 aggregation/routing internals; ns_web W3; Agent HITL; full response-routing/assignment lifecycle.
- **Revalidation Trigger:** Human response becomes Policy/Acceptance/Admission authority, Inbox becomes source owner, Automation wait ownership moves from S6.

## AU09 — Automation Trial Semantics & Runtime Evidence

- **Source Boundary:** S6 / SV-R02.
- **Purpose:** close Automation-side governed pre-production Trial semantics and S6 Trial Actual-state while preserving executor effects and production governance separation.
- **Owned Responsibility:** Automation Trial Subject/Identity; Definition Revision Under Trial; Trial Intent reference; Trial Context identity; Trial applicability; effect-boundary declaration; Automation semantic trial state/result; trial provenance/history/diagnostics references.
- **Explicitly Non-owned:** Business/Data/Agent Trial semantics; universal Trial engine; executor attempt/effect facts; production Artifact Acceptance/Admission; sandbox/virtualization.
- **Authority / SoT Relationship:** Trial does not become Definition SoT or separate Automation Authority.
- **Owned State / Actual-state:** final owner for S6 Automation semantic Trial state/result; actual Node/server-local attempt/effect remains corresponding owner.
- **Consumed State:** exact AU01 Definition Revision; AU03 validation evidence; AU07 continuation semantics where behavior requires continuation; AU05/AU06/AU08 semantics when trial exercises event/composition/HITL; governance/admission evidence as applicable.
- **Identity / Revision:** Trial Identity != Production Automation Operation Identity != Attempt/Effect Identity. Exact Definition Revision is pinned.
- **Effect Boundary Declaration:** every Trial must explicitly establish whether real effects are permitted within a declared bounded scope, explicitly suppressed by a supporting capability, partially constrained, unsupported, or indeterminate. `Dry-run != No Effect` automatically.
- **Lifecycle:** Trial Intent → applicability/context establishment → optional trial-specific Admission where required → Trial semantic operation → downstream attempts/effects → Trial semantic result/diagnostics → historical retention. Trial success never promotes production state.
- **Trial Result:** distinguish success/failure/partial/unsupported/unavailable/indeterminate semantics as applicable; success means only success under declared Trial context/effect boundary.
- **Persistence Semantic Responsibility:** durable Trial identity/context/result/provenance/effect references; no production Actual-state takeover.
- **Governance Context:** Tenant/Principal/Policy/Trust/privacy apply; Trial does not bypass normal governance merely because it is non-production.
- **Artifact / Admission:** `Trial Successful != Artifact Accepted != Production Admitted`. Trial-specific execution may require applicable Admission, but no production Admission is inferred.
- **Managed Config / Secret:** Trial context may reference governed test/runtime configuration and Secret References; ordinary trial state does not custody Secret Material.
- **Offline / Degraded:** trial remains private/offline capable; unavailable provider/node/source yields explicit unsupported/unavailable/indeterminate result.
- **Failure / Unknown:** effect boundary unknown, dependency unavailable, incompatible revision, partial effects and incomplete diagnostics remain explicit.
- **Recovery / Reconciliation:** re-observe executor/effect evidence and preserve Trial identity; no Trial-to-Production reconciliation collapse.
- **Replay:** Trial history replay is observation; deterministic replay is not promised. A repeated Trial receives a new Trial identity and preserves original evidence.
- **Historical Interpretation:** exact Definition/Trigger/Binding/HITL/Trial context and effect references retained.
- **Compatibility / Migration / Conformance:** trial records remain interpretable against old revisions; new Definition revision requires a new Trial, not mutation of prior Trial result.
- **Foundation Consumption:** C04/C05/C06/C09/C10/C11/C12/C13/C14 plus diagnostics/telemetry.
- **Internal Dependencies:** SDD `AU09 → AU01, AU07`; ACD/EL to AU03/AU05/AU06/AU08 and executor evidence.
- **Cross-boundary Dependencies:** actual executor partitions; W5/SDK future trial interaction; G12 Admission where applicable.
- **External Contract Responsibility:** Automation-side semantic/runtime portion of RCP-17 only.
- **Non-goals:** universal sandbox, deterministic simulation, effect virtualization, trial runner/process, full cross-domain RCP-17 closure.
- **Named Downstream Deferrals:** Business/Data/Agent/Web/SDK Trial internals, concrete environment/isolation/effect implementation.
- **Revalidation Trigger:** universal effect-free/deterministic guarantee, Trial success becomes Acceptance/Production Admission, Trial Actual-state owner moves.

---

# 9. Internal Dependency Taxonomy

Batch 1 accepted dependency meanings are reused unchanged:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only `SDD` participates in internal recursive semantic-definition cycle analysis.

No new dependency kind is required.

---

# 10. Internal Dependency Topology

Hard SDD edges:

```text
AU02 → AU01, AU04, AU06, AU08
AU03 → AU01, AU04, AU06, AU08
AU04 → AU01
AU05 → AU04
AU06 → AU01
AU07 → AU01, AU06
AU08 → AU01, AU07
AU09 → AU01, AU07
```

Application/evidence relationships include:

```text
AU02 ACD/EL → AU03 validation
AU03 EL → G11 certification evidence intake
AU05 XED → bounded Event Source Authority
AU05 ACD/EL → G10 + G12
AU07 EL → G12 / RT dispatch / executor Attempt / Effect evidence
AU07 HPL → exact Definition/Trigger/Binding/Admission/Attempt/Effect lineage
AU08 EL → S11/W3 response submission provenance
AU08 ACD → G10
AU09 EL → executor Attempt/Effect + Trial diagnostics
AU09 ACD → G10/G12 where applicable
```

```text
Hard Internal SDD Graph → ACYCLIC
Unresolved Internal Semantic-definition Cycle → 0
```

Separately, Owner-selected Automation composition dependency semantics require:

```text
Canonical Automation Composition Dependency Graph
→ ACYCLIC

Recursive Automation-to-Automation Invocation
→ NOT SUPPORTED
```

The internal Module SDD graph and the Automation Definition composition graph are distinct cycle domains and are not conflated.

---

# 11. Authority / SoT / Actual-state Matrix

| Module | Automation semantic authority relationship | Canonical Definition SoT relationship | Runtime Actual-state / source relationship |
|---|---|---|---|
| AU01 | principal internal realization/custodian | overall canonical Definition identity/revision/history custodian | none |
| AU02 | authority-neutral authoring participant | candidate/provenance only, never SoT | none |
| AU03 | exercises/evidences S6 semantic conformance; no independent Authority | certification evidence only | none |
| AU04 | specialized trigger semantic custodian under S6 | trigger constituent revision inside Automation SoT | no event occurrence/evaluation ownership |
| AU05 | trigger evaluation semantic responsibility | none | final owner of S6 Trigger Evaluation state; Event occurrence remains source-owned |
| AU06 | specialized composition semantic custodian under S6 | composition/binding constituent revision inside Automation SoT | runtime invocation state external to AU06 |
| AU07 | no new Product Authority | runtime state never Definition SoT | final owner of Automation semantic Operation/Continuation state |
| AU08 | HITL semantics under S6 | definition-side Human Action Requirement constituent where applicable | final owner of Automation wait/response-applicability/resume semantic state |
| AU09 | Trial semantics under S6 | Trial state never Definition SoT | final owner of Automation semantic Trial state/result; executor effects external |

```text
Authority Transfer → 0
SoT Transfer → 0
Actual-state Ownership Transfer → 0
```

---

# 12. State / Lifecycle Ownership Matrix

| Semantic subject | Final current-state/lifecycle custodian | Historical custodian | Explicit non-owner |
|---|---|---|---|
| Automation Definition identity/current revision | AU01 | AU01 | source file/UI/artifact/runtime copy/cache |
| Authoring candidate/intake | AU02 | AU02 | candidate as canonical Definition |
| Validation/certification evidence | AU03 | AU03 | G11 as domain certifier |
| Trigger Definition/revision | AU04 under AU01 SoT | AU04/AU01 | event producer/runtime scheduler |
| Event occurrence fact | bounded event source | source | AU05/broker/transport automatically |
| Trigger Evaluation | AU05 | AU05 | event producer/G12/RT |
| Composition binding/revision | AU06 under AU01 SoT | AU06/AU01 | caller/callee runtime/executor |
| Automation Runtime Operation | AU07/SV-R02 | AU07 | G12/RT/executor |
| Automation Continuation | AU07/SV-R02 | AU07 | RT-R03 coordination projection |
| Automation HITL wait/applicability | AU08/SV-R02 | AU08 | S11/W3/Inbox |
| Human response submission occurrence | W3 future owner | W3/source history | AU08 as submission source owner |
| Automation Trial semantic state | AU09/SV-R02 | AU09 | executor/W5 projection |
| Node Attempt | N2 | N2 | AU07/AU09 |
| Protected Effect | N3 | N3 | AU07/AU09 |
| Admission | G12/S8 | G12 | all AU modules |

---

# 13. Semantic Persistence Responsibility

Persistence means semantic custody, not storage technology.

```text
Authoritative Canonical Definition state/history
→ AU01
→ AU04 trigger constituents within S6 SoT
→ AU06 composition/binding constituents within S6 SoT
→ AU08 definition-side Human Action Requirement constituents where applicable

Authority-neutral durable authoring/validation evidence
→ AU02 candidate/provenance/interoperability assessments
→ AU03 validation/certification evidence

S6 Runtime Actual-state/history
→ AU05 Trigger Evaluation
→ AU07 Operation/Continuation
→ AU08 HITL wait/applicability/application
→ AU09 Trial semantic state/result

External source facts
→ remain with event producer / RT / executor / Node / web submission owner as accepted
```

Foundation C09/M09/PF08 may realize durable access mechanics, but:

```text
Database/Table/Storage Provider
!= Automation Authority
!= Automation Definition SoT
!= Event Source Authority
!= Runtime Actual-state Owner
```

---

# 14. Automation Definition / Revision / Canonical Lifecycle

## 14.1 Identity

```text
Automation Definition Identity
!= Automation Definition Revision
!= Authoring Candidate Identity
!= Artifact Identity
!= Admission Evidence Identity
!= Runtime Operation Identity
```

Physical identifier format remains deferred.

## 14.2 Revision semantics

Each canonical revision resolves to one fixed semantic snapshot. Modification produces another revision linked by provenance/lineage.

At a given governed Definition identity/Tenant scope there is one current canonical revision designation, while multiple immutable historical revisions remain addressable.

Current revision does not become historically applicable automatically.

## 14.3 Canonical intake lifecycle

```text
Source / Visual / Agent Candidate
→ AU02 semantic intake + provenance
→ AU03 candidate validation
→ AU01 canonical revision establishment
→ AU03 exact-revision semantic certification evidence
→ candidate Artifact relationship where applicable
→ G11 Formal Artifact Acceptance
→ G12 Formal Execution Admission
→ runtime
```

Permanent separation:

```text
Valid Candidate != Canonical Revision automatically
Canonical Revision != Certified automatically
Certified != Accepted Artifact
Accepted Artifact != Admitted Execution
```

## 14.4 Applicability and retirement

A canonical Definition may become non-applicable for new governed use/retired while historical revisions remain interpretable. Such a change does not automatically revoke existing Artifact Acceptance or Admission evidence; those authorities retain independent lifecycle.

---

# 15. Source Authoring Intake

Complete System-level SDK/source authoring is an accepted Product capability, but SDK detailed design is outside scope.

S6 stable obligations are:

1. accept a semantic candidate with explicit author/origin/Tenant/target-definition context;
2. preserve candidate provenance and intended revision association;
3. validate all governed Automation semantics without relying on source formatting or repository layout;
4. return explicit unsupported/incompatible/representation-limited diagnostics;
5. route successful candidate semantics into the same AU01 canonical lifecycle as every other authoring surface;
6. never treat source repository/file existence as Definition SoT or Artifact Acceptance;
7. keep source-local comments/formatting/organization outside the guaranteed semantic round-trip unless later separately governed.

No Python API/decorator/DSL/compiler/parser/file format is selected.

---

# 16. Visual Authoring Intake

`ns_web` Internal Design is not authorized. S6 defines only semantic obligations:

1. visual-authored changes target the same AU01 canonical Automation semantics;
2. UI edit state is a candidate state, not SoT;
3. semantic validation/compatibility feedback is returned by S6 responsibilities;
4. unsupported/non-editable/representation-limited constructs are explicit;
5. a visual save/update cannot silently destroy canonical semantics the surface cannot represent;
6. authoring surface change never changes Tenant/Principal/Policy/Trust/Acceptance/Admission context.

No visual node schema/canvas model/frontend store/API payload is selected.

---

# 17. Source ↔ Visual Semantic Interoperability

Owner-selected guarantee is implemented at S6 level as:

```text
Source-authored Candidate
↔ AU02 governed semantic intake
↔ AU01 canonical Automation semantics
↔ AU02 governed semantic projection/intake
↔ Visual-authored Candidate
```

Stable semantic result categories:

```text
SUPPORTED_EDITABLE
SUPPORTED_NON_EDITABLE
REPRESENTATION_LIMITED
UNSUPPORTED
INCOMPATIBLE
INDETERMINATE
UNKNOWN where evidence is unavailable
```

Rules:

- `SUPPORTED_NON_EDITABLE` means semantics may be preserved/observed but cannot be safely modified by the receiving surface.
- `REPRESENTATION_LIMITED` means the surface can expose only a bounded representation while canonical semantics remain intact; destructive re-save is prohibited unless semantic preservation is proven.
- `UNSUPPORTED` means the surface/current revision does not support the construct.
- `INCOMPATIBLE` means semantic evolution requires explicit migration/change rather than best-effort conversion.
- `INDETERMINATE/UNKNOWN` means evidence is insufficient/unavailable; no semantic guess.

Lossless source formatting/comments or visual layout round-trip is not required.

---

# 18. Validation / Certification Participation

Definition Validation and Domain Semantic Certification remain distinct.

```text
Candidate Validation
→ tests whether candidate semantics can form a valid governed Automation revision

Canonical Revision Establishment
→ AU01 Definition SoT action

Domain Semantic Certification Evidence
→ AU03 evidence that an exact canonical revision satisfies the applicable Automation domain semantics/conformance context

Formal Artifact Acceptance
→ G11 / separate Authority
```

No independent new Certification Authority is introduced. Certification is an evidence-producing exercise of the already accepted Automation Semantic Authority.

Validation/certification failure never becomes Formal Artifact rejection automatically; G11 makes its own decision using evidence.

---

# 19. Agent-authored Candidate Automation Intake

Agent-authored candidate semantics enter AU02 with explicit origin/provenance.

Required distinctions:

```text
Agent Candidate Identity
!= Automation Definition Identity automatically

Agent Candidate
!= Canonical Definition Revision
!= Certified
!= Accepted Artifact
!= Admitted Execution
```

A candidate may propose a new Definition identity or a new revision of an existing Definition. AU01/S6 controls canonical establishment.

AU02/AU03 must expose invalid/incompatible/unsupported constructs and preserve Agent origin, originating Agent operation/correlation where available, and Tenant/Principal/governance context.

No Agent reasoning graph, Agent-to-S6 API or RCP-12 complete design is created.

---

# 20. RCP-13 — Automation Continuation

## 20.1 Semantic Subject and Ownership

`RCP-13` carries/relates the stable semantics required for an Automation semantic runtime operation to continue across coordination, executor attempts/effects, composition and HITL without transferring factual ownership.

```text
Principal semantic producer / Actual-state owner
→ AU07 / S6 / SV-R02
```

## 20.2 Identity model

Required distinct semantic identities/references:

```text
Automation Definition Identity
Automation Definition Revision
Target Execution Intent Identity
Admission Evidence Identity
Automation Runtime Operation Identity
Continuation Identity
Origin / Parent Operation correlation
Composition Invocation Identity where applicable
Trigger Evaluation Identity where applicable
Human Wait Requirement Identity where applicable
Dispatch Evidence Identity
Executor Attempt Identity
Protected Effect Evidence Identity
Trial Identity where applicable
```

No generic `task_id` substitutes for all subjects.

## 20.3 Applicability and revision pinning

An Automation Runtime Operation is established from an applicable formally admitted execution intent and pins the exact Automation Definition Revision plus applicable Trigger/Composition/HITL semantics.

```text
Current Definition Revision
!= operation Definition Revision automatically
```

No silent live rebinding is supported.

## 20.4 Semantic continuation state

Semantic categories include:

```text
ADMITTED_AWAITING_COORDINATION
ACTIVE / CONTINUING
WAITING_HUMAN
WAITING_CALLEE
WAITING_DOWNSTREAM_EVIDENCE
CONTINUATION_ELIGIBLE
SUCCEEDED
FAILED
TERMINATED
PARTIAL
UNKNOWN
INDETERMINATE
STALE
RECONCILIATION_PENDING
```

A concrete universal state-machine representation is not selected.

## 20.5 Downstream evidence interpretation

```text
Dispatch != Attempt
Attempt != Effect
Attempt Failed != Automation Final Failure automatically
Effect Occurred != Automation Semantic Success automatically
Callee Success != Caller Success automatically
```

AU07 consumes evidence references and applies pinned Automation semantics to derive the S6 semantic continuation/outcome.

## 20.6 Retry / re-entry / intervention

```text
Retry Request != Retry Started
Retry Started != Prior Attempt Never Happened
Resume Request != Resumed
Recovery Request != Recovered
Cancel Request != Cancelled
```

Retry/re-entry retains prior Attempt/Effect lineage. Existing effects are never erased/reversed by retry. Re-entry to the same operation is valid only when the continuation and admission applicability remain establishable; otherwise a new execution intent and new Admission are required.

## 20.7 Replay

Historical replay is observation. A request to execute again is not retroactive continuation by default.

```text
Replay History != Re-execution
Re-execution Intent != Original Admission automatically
```

## 20.8 Offline / recovery

If downstream evidence is unavailable/unreachable, AU07 preserves waiting/unknown/stale/indeterminate semantics. On recovery it re-observes source evidence and reconciles its own S6 semantic state; source owners remain authoritative.

## 20.9 Producer obligations

AU07/S6 must:

1. preserve operation/continuation identities and exact Definition revision;
2. preserve Admission/Dispatch/Attempt/Effect evidence links without ownership transfer;
3. preserve origin/parent/composition/HITL/retry lineage;
4. emit explicit uncertainty/partial/reconciliation state;
5. keep history interpretable across compatibility/migration;
6. preserve Tenant/Governance Context and redaction obligations.

## 20.10 Consumer obligations

Runtime/executors/UI/SDK consumers must:

1. not interpret RCP-13 as Admission, Dispatch, Attempt or Effect authority;
2. preserve the Operation/Continuation correlation supplied by S6;
3. return/source their own evidence under their own contracts/owners;
4. never overwrite S6 semantic outcome from a local projection/attempt state;
5. retain revision/provenance/uncertainty semantics.

**RCP-13 Status:** `CLOSED AT DESIGN-SEMANTIC LEVEL`.

---

# 21. RCP-14 — Event Trigger Input / Evaluation

## 21.1 Semantic subjects

```text
Event Source Identity
Event Source bounded Authority reference
Event Occurrence Identity
Event semantic revision where applicable
Event provenance
Occurrence temporal context
Observation / re-observation temporal context
Trigger Definition Identity
Trigger Definition Revision
Trigger applicability
Trigger Evaluation Identity
Trigger Evaluation Result
Trigger Evaluation Evidence
```

## 21.2 Authority preservation

```text
Event Occurred != Trigger Matched
Trigger Matched != Execution Admitted
Event Source != Automation Authority
Event Producer != Policy Authority
Event Transport/Broker != Event Source Authority automatically
External Event != external factual SoT transfer
```

Source facts retain their bounded source authority.

## 21.3 Evaluation results

`MATCHED`, `NOT_MATCHED`, `INDETERMINATE`, `UNSUPPORTED/INCOMPATIBLE`, plus explicit stale/conflict/unknown/unverified qualification where applicable.

A `MATCHED` evaluation may produce a new Automation execution intent, not an admitted operation.

## 21.4 Duplicate semantics

When the same Event Occurrence Identity is re-observed:

```text
same occurrence
!= new occurrence
```

The normal path must not silently create a second execution intent merely because transport delivered/replayed the same established occurrence. This is a semantic deduplication obligation, not an exactly-once transport or execution guarantee.

If occurrence identity cannot be established reliably, duplicate status may remain `INDETERMINATE` rather than guessed.

## 21.5 Replay semantics

```text
Original Event Occurrence
!= Event Re-observation
!= Replay Request
!= Trigger Re-evaluation
!= New Execution Intent
!= Original Admission
!= New Admission
```

An explicit replay/re-evaluation identifies the Event Occurrence and the exact Trigger Revision to evaluate. It creates a new Trigger Evaluation Identity. If matched and execution is requested, a new execution intent requires applicable Admission; original Admission is not retroactively reused by assumption.

## 21.6 Ordering / stale semantics

No global total order is established. Occurrence time and observation time remain distinct.

If a trigger depends on ordering/freshness and admissible source evidence cannot establish the necessary ordering, AU05 returns stale/indeterminate/conflicting semantics rather than using arrival order or latest timestamp as canonical truth.

## 21.7 Unknown/unavailable source

Unknown/unverified Event Source identity does not become a matched trigger. Source unavailability means no fresh source evidence is available; it does not rewrite old events as nonexistent.

Unsupported Event revision is explicit and may require trigger/definition migration.

## 21.8 Offline/private

Private/local Event Sources are valid where governed. Core correctness does not require a public broker/webhook service. Offline evaluation requires exact trigger revision and applicable governance evidence; receipt never bypasses Admission.

## 21.9 Producer obligations

Event producers must provide/preserve as applicable source identity, occurrence identity, provenance, semantic revision and temporal/source-authority context sufficient for S6 evaluation. They do not issue Automation Admission.

AU05 must preserve source authority, evaluate exact trigger revision, distinguish duplicate/replay/order uncertainty and produce evaluation evidence.

## 21.10 Consumer obligations

G12/runtime consumers must treat matched evaluation as execution-intent evidence only; they must not infer Admission or source truth beyond the event producer's bounded authority.

**RCP-14 Status:** `CLOSED AT DESIGN-SEMANTIC LEVEL`.

---

# 22. RCP-15 — Automation Composition

## 22.1 Semantic subjects

```text
Caller Automation Definition Identity / Revision
Callee Automation Definition Identity / Revision
Composition Reference Identity
Composition Binding Identity / Revision
Composition applicability
Composition Invocation Identity
Parent Caller Operation Identity
Callee Operation Identity
Exact resolved binding provenance
```

## 22.2 Definition binding

The baseline supports exact callee canonical-revision binding and prohibits silent `latest` rebinding.

```text
Caller revision pins composition binding revision
Binding revision resolves to exact callee revision
Changing callee dependency semantics
→ new binding + caller revision
```

No version-range syntax/lockfile format is selected. Additional future binding resolution modes are not a current Product guarantee and must preserve exact historical resolution if later authorized.

## 22.3 Independent callee lifecycle

Callee Definition lifecycle is independent. Callee revision retirement/removal from new use does not rewrite historical caller executions. New invocation may become unavailable/stale/incompatible if the exact bound revision cannot validly execute.

## 22.4 Acyclic composition / recursion

Per `CID-SV-B2-MDE-001`:

```text
Direct recursive Automation invocation → UNSUPPORTED
Indirect recursive Automation invocation → UNSUPPORTED
Canonical composition dependency cycle → INVALID / UNSUPPORTED
```

Cyclic definition dependency, recursive invocation and runtime recursive continuation remain separately named concepts; all three are prevented from being silently treated as legal recursion.

Repeated non-recursive invocation or retry does not automatically constitute recursion.

## 22.5 Runtime invocation lineage

Each callee invocation receives a Composition Invocation Identity and a distinct callee execution intent/operation lineage. Parent/callee correlation does not merge operations.

```text
Caller Operation != Callee Operation
Composition Invocation != Dispatch != Attempt
```

## 22.6 Admission non-bypass

A callee invocation must be within Formal Admission evidence whose applicability explicitly covers the exact callee execution intent/revision. Parent Admission is never presumed to cover the callee merely because composition exists.

If not covered, a separate applicable Admission decision is required before dispatch.

## 22.7 Failure / partial / unknown

Missing dependency, unsupported/incompatible binding, unavailable exact revision, stale evidence or conflicting binding remain explicit.

```text
Callee Semantic Success != Caller Semantic Success automatically
Callee Attempt Failure != Caller Final Failure automatically
```

Caller AU07 applies caller semantics to callee semantic result/evidence.

## 22.8 Offline / history / migration

Offline/private composition requires exact dependency revision and applicable governance evidence locally available. No public registry is required.

History retains exact caller revision/binding/callee revision. Migration never rewrites historical bindings. Legacy recursive composition is `UNSUPPORTED/INCOMPATIBLE` and must be explicitly migrated rather than silently flattened.

## 22.9 Producer obligations

AU06 must produce stable binding semantics and exact historical resolution. AU07 must produce invocation/parent-callee semantic lineage. Callee AU07 produces its own semantic result.

## 22.10 Consumer obligations

Runtime coordinators must not reinterpret composition binding, choose a different/latest callee, bypass Admission or become Automation Authority. Executors retain attempt/effect ownership.

**RCP-15 Status:** `CLOSED AT DESIGN-SEMANTIC LEVEL`.

---

# 23. RCP-16 — Automation Source-side Human Task Semantics

Current authorized closure is only the S6-owned source side.

Semantic subjects:

```text
Human Action Requirement semantic identity
Automation Wait Requirement Identity
Originating Automation Operation Identity
Originating Definition Revision
Originating Continuation Identity
required human context
Tenant / Principal / Organization where applicable
Policy / Trust references where applicable
response submission reference/provenance
response applicability
response applied semantic consequence
```

Automation-side rules:

```text
Human Response Submitted != Response Applicable
Response Applicable != Response Applied automatically
Human Response != Policy Permit
Human Response != Artifact Acceptance
Human Response != Execution Admission
ns_web click != Automation Resumed
S11 projection != Automation Wait-state SoT
RT continuation request != Automation Resumed
```

S6/AU08 owns final Automation wait/applicability/apply/resume/branch/terminate semantics. Multiple conflicting responses are not latest-wins; stale/wrong-context responses remain explicit.

```text
RCP-16 Automation Source-side → CLOSED AT CURRENT DESIGN LEVEL
RCP-16 Full Cross-domain Closure → NOT CLAIMED
```

Named downstream authorities: S11 aggregation/response routing, Agent HITL, W3 interaction, full assignment/federation/response-routing design.

---

# 24. RCP-17 — Automation Trial Semantics

Current authorized closure is only the Automation side.

Semantic subjects:

```text
Automation Trial Identity
Definition Revision Under Trial
Trial Intent reference
Trial Context Identity
Trial applicability
Trial effect-boundary declaration
Automation Trial semantic runtime state
Trial result
Trial provenance/diagnostics references
```

Permanent rules:

```text
Definition Valid != Trial Successful
Trial Successful != Artifact Accepted
Trial Successful != Production Admitted
Trial Execution != Production Execution
Trial Success != Production Success Guarantee
Dry-run != No Effect automatically
```

AU09 owns Automation semantic Trial state/result; executor attempts/effects remain their normal owners. Trial-specific Admission may be required where effect-bearing execution policy requires it, but no production Admission is inferred.

```text
RCP-17 Automation-side → CLOSED AT CURRENT DESIGN LEVEL
RCP-17 Full Cross-domain Closure → NOT CLAIMED
```

No universal sandbox, deterministic simulation, virtualization or runner is created.

---

# 25. Runtime Actual-state Review

Accepted final-owner partition is preserved:

```text
Automation Trigger Evaluation → AU05 / SV-R02
Automation semantic Operation / Continuation → AU07 / SV-R02
Automation HITL wait/applicability/resume → AU08 / SV-R02
Automation Trial semantic state/result → AU09 / SV-R02

Admission → G12/S8
Scheduling/Routing/Dispatch → RT-R02
Cross-component coordination-stage continuation/intervention → RT-R03
Node Attempt → ND-R02
Node Effect → ND-R03
Human Task aggregation → SV-R07
Human response submission occurrence → WB-R01/W3
```

```text
Same bounded assertion with multiple final owners → 0
Actual-state Ownership Transfer → 0
```

---

# 26. History / Provenance Review

Historical interpretation requires exact references as applicable:

```text
Automation Definition Identity / Revision
Trigger Definition Identity / Revision
Event Source / Occurrence / Evaluation identity
Composition Reference / Binding Revision / exact Callee Revision
Automation Runtime Operation / Continuation identity
Governance Context revision
Artifact Acceptance evidence
Admission evidence
Dispatch / Attempt / Effect lineage
HITL Wait Requirement + response provenance
Trial identity/context/effect boundary
Applied configuration evidence where relevant
```

Current Definition, Trigger, Callee, Policy, Trust or Desired Config never rewrites historical operation meaning.

```text
Historical Interpretation → CLOSED
```

---

# 27. Offline / Replay Review

```text
Offline != Local Authority Transfer
Replay != Retroactive Admission
Reconnect != Reconciled
Sync != Authority Transfer
Latest Timestamp != Canonical Winner
```

- exact canonical Definition/Binding revisions remain the interpretation basis;
- missing composition dependency remains unavailable/indeterminate, never auto-latest;
- duplicate Event observation does not silently create a new intent;
- Event replay produces a new Evaluation and new execution intent/Admission where execution is requested;
- retained Admission/Acceptance/Governance evidence is usable only within Batch-1 applicability semantics;
- HITL response observed offline/reconnected is applied only after AU08 applicability evaluation;
- Trial replay is not deterministic replay guarantee.

No global fail-open/fail-closed policy is selected.

---

# 28. Recovery / Reconciliation Review

Responsibilities:

```text
AU05 → re-observe Event provenance/evaluation correlation
AU07 → re-observe Admission/Dispatch/Attempt/Effect/callee continuation evidence
AU08 → re-observe response provenance vs current wait state
AU09 → re-observe trial executor/effect evidence
AU01/AU04/AU06 → restore exact canonical historical revisions/bindings without current-state rewrite
```

Conflict remains explicit until the final owner can establish its bounded assertion. S6 never canonicalizes an executor/source fact merely because it persisted a copy.

```text
Recovery / Reconciliation → CLOSED AT CURRENT DESIGN LEVEL
```

---

# 29. Security / Tenant / Policy / Trust Review

Permanent S6 requirements:

1. every native Automation Definition/runtime operation is explicitly Tenant-scoped; cross-Tenant semantics are not invented;
2. Organization is an optional separate applicability dimension, never Tenant identity;
3. Principal author/runtime actor provenance remains distinct from Automation Authority;
4. Authentication evidence, Policy and Trust are consumed via accepted governance semantics;
5. Policy Permit does not replace Artifact Acceptance/Admission;
6. Event Source/Agent/authoring surface does not create Trust/Policy/Admission;
7. composition does not propagate caller Authority to callee;
8. Trial/HITL do not bypass production governance;
9. diagnostics/interoperability feedback is authorization/privacy/redaction aware.

```text
Security / Tenant / Policy / Trust → CLOSED AT CURRENT DESIGN LEVEL
Authority Transfer → 0
```

---

# 30. Secret Boundary Review

```text
Configuration != Secret
Secret Reference != Secret Material
```

Automation definitions, triggers, composition/integration subjects and Trial context may contain governed Secret References only when semantic meaning requires them.

Ordinary AU01-AU09 state does not become a general Secret Material custodian.

Actual material resolution, when later legitimately required by an executing integration, follows accepted C12/PF09 semantics and runtime permissions without transferring Automation/Trust/Policy authority.

No Vault/KMS/HSM/credential schema is selected.

```text
Secret Boundary → PRESERVED
```

---

# 31. Shared Foundation Consumption Matrix

| S6 Module | Principal accepted Foundation semantics | Notes |
|---|---|---|
| AU01 | C02/C03/C04/C05/C06/C09/C10/C11/C12/C13/C14 | canonical revision/history mechanics only; storage/provider never SoT |
| AU02 | C02/C03/C04/C05/C06/C10/C11/C12/C13/C14 + C09 where history retained | interoperability/candidate provenance; no converter Authority |
| AU03 | C02/C03/C04/C05/C06/C09/C10/C11/C13/C14 | validation/certification evidence |
| AU04 | C02/C03/C04/C05/C06/C09/C10/C11/C12/C13/C14 | temporal/source binding; no scheduler/broker Foundation |
| AU05 | C02/C03/C04/C05/C06/C09/C10/C11/C13/C14; C07/C08 conditional | Event provenance/evaluation; transport/cache remains mechanics |
| AU06 | C02/C03/C04/C05/C06/C09/C10/C11/C12/C13/C14 | composition history/binding |
| AU07 | C02/C03/C04/C05/C06/C09/C10/C11/C13/C14; C08 optional | runtime semantic state/history |
| AU08 | C02/C03/C04/C05/C06/C09/C10/C11/C13/C14 | HITL correlation/history/redaction |
| AU09 | C02/C03/C04/C05/C06/C09/C10/C11/C12/C13/C14 | Trial context/provenance/effect refs |

Accepted realization chain:

```text
S6
→ Stable Entry
→ Foundation Contract
→ Foundation Module
→ Provider Family where provider-bearing
```

No S6 Module depends on a concrete Provider identity.

Accepted `NOT_FOUNDATION_ELIGIBLE` remains controlling:

```text
Event / Notification utility
Generic Scheduler
Generic Workflow / Automation Engine
```

Deferred Foundation candidates remain deferred:

```text
Cryptographic / Evidence-verification Helpers
Database Utility Primitives
```

No blocking Foundation gap was discovered.

---

# 32. Compatibility / Migration / Conformance Review

Applicable primary classes remain:

```text
CONFORMANCE_ONLY_IMPLEMENTATION_CHANGE
COMPATIBLE_EVOLUTION
EXPLICIT_MIGRATION_REQUIRED
ARCHITECTURE_REVALIDATION_REQUIRED
OWNER_MDE_REQUIRED
```

S6 obligations:

- Definition/Trigger/Binding revisions remain historically resolvable;
- unsupported old revisions are explicit;
- authoring representation migration cannot destroy semantic meaning silently;
- running Operations are revision-pinned and do not silently live-migrate;
- Event/Trigger compatibility precedes transport compatibility;
- callee revision/binding migration requires explicit new binding/caller revision;
- recursive legacy composition is incompatible under current Owner decision;
- Provider/storage/representation replacement may remain conformance-only when semantics are unchanged.

```text
Compatibility / Migration / Conformance → CLOSED AT CURRENT DESIGN LEVEL
```

---

# 33. Other RCP Non-preemption

Fully closed here only:

```text
RCP-13 Automation Continuation
RCP-14 Event Trigger Input / Evaluation
RCP-15 Automation Composition
```

Partially closed only:

```text
RCP-16 Automation source/wait/applicability side
RCP-17 Automation Trial side
```

Other RCPs are referenced only as accepted external dependencies/evidence owners where necessary. No RCP-03..12, RCP-18, RCP-20..24 full design is performed.

```text
Other RCP Complete-design Leakage → 0
```

---

# 34. Other ns_server Boundary Non-preemption

No internal design is created for:

```text
S5 Business Application
S7 Data / Knowledge / ETL
S10 Server Background
S11 Human Task Aggregation
S12 Notification
S13 Discovery
```

They are referenced only as accepted/later semantic owners where S6 contracts interact.

```text
Other ns_server Boundary Internal-design Leakage → 0
```

---

# 35. Other Component / SDK Non-preemption

- `ns_runtime`: only stable obligations to preserve Admission/continuation/dispatch semantics; no internals.
- `ns_node`: only Attempt/Effect producer obligations; no internals.
- `ns_agent`: only Agent-authored candidate provenance obligation; no internals.
- `ns_web`: only source/visual/HITL/trial interaction semantic obligations; no internals.
- System-level SDK: complete source authoring/trial surface acknowledged; package/class/method/CLI/DSL design remains unauthorized.

```text
Other Component Internal-design Leakage → 0
System-level SDK Detailed-design Leakage → 0
```

---

# 36. Technology / Implementation Non-preemption

Inherited technology fact only:

```text
ns_server → Python + Django
```

Not selected:

```text
Django App
Python package/class/Protocol/ABC
ORM Model/table/schema
REST/RPC/gRPC/WebSocket schema
JSON/Protobuf
Celery/Temporal/Airflow/Prefect
BPMN/DAG/state-machine library/workflow engine
Kafka/RabbitMQ/Redis Stream/NATS/Pulsar/MQTT
queue/topic/subscription/ack/delivery guarantee
scheduler/process/worker/container topology
MySQL/PostgreSQL/Redis/storage engine
AST/IR/source DSL/visual schema/code generator
```

```text
Implementation Planning Leakage → 0
```

---

# 37. DAD Summary

Material DADs are persisted separately in Batch-2 DAD Evidence. Candidate set:

```text
CID-SV-B2-DAD-001 → 9-module S6 internal decomposition
CID-SV-B2-DAD-002 → Definition identity/revision/canonical lifecycle custody
CID-SV-B2-DAD-003 → unified source/visual/Agent authoring intake + interoperability responsibility
CID-SV-B2-DAD-004 → validation vs semantic certification evidence separation
CID-SV-B2-DAD-005 → Trigger Definition vs Event Evaluation responsibility split
CID-SV-B2-DAD-006 → Composition definition/binding vs runtime invocation lineage split
CID-SV-B2-DAD-007 → Automation Operation/Continuation SV-R02 Actual-state custody
CID-SV-B2-DAD-008 → Automation HITL source/wait/applicability custody
CID-SV-B2-DAD-009 → Automation Trial semantic/runtime custody
CID-SV-B2-DAD-010 → reuse Batch-1 dependency taxonomy / acyclic internal SDD
CID-SV-B2-DAD-011 → semantic persistence responsibility allocation
CID-SV-B2-DAD-012 → revision-pinned historical interpretation / no silent live rebinding
CID-SV-B2-DAD-013 → Foundation consumption mapping without Provider leakage
CID-SV-B2-DAD-014 → RCP-13/14/15 full semantic closure + bounded RCP-16/17 S6 closure
```

---

# 38. MDE Summary

```text
CID-SV-B2-MDE-001
→ Native Automation-to-Automation Recursive Invocation NOT SUPPORTED
→ Reusable acyclic Composition REQUIRED / PRESERVED
→ OWNER_DECIDED / PERSISTED

New MDE Count → 1
Open MDE → 0
Unpersisted Owner Decision → 0
```

No other Owner-reserved dimension was changed.

---

# 39. Semantic Resolution Matrix

| Dimension | Resolution |
|---|---|
| Identity | CLOSED: Definition/Revision/Candidate/Trigger/Event/Evaluation/Composition/Binding/Operation/Continuation/HITL/Trial/Admission/Dispatch/Attempt/Effect distinct |
| Namespace | CLOSED at semantic level; physical namespace not frozen |
| Revision | CLOSED: immutable canonical revisions + trigger/binding revision + historical exact resolution |
| Authority | CLOSED: accepted Automation/Acceptance/Admission/Policy/Trust authorities preserved |
| Semantic Ownership | CLOSED per AU01-AU09 |
| Source of Truth | CLOSED: Automation canonical Definition SoT preserved; Event/source/effect owners preserved |
| Actual-state Ownership | CLOSED: AU05/AU07/AU08/AU09 S6 partitions; external facts retain owner |
| State / Lifecycle | CLOSED per Definition/Trigger/Evaluation/Composition/Operation/HITL/Trial |
| Temporal | CLOSED: occurrence vs observation, revision applicability, no latest-wins |
| Failure | CLOSED with subject-specific failure/partial/unsupported semantics |
| Unknown / Indeterminate | CLOSED / explicit |
| Tenant | CLOSED / mandatory / no cross-Tenant invention |
| Organization | CLOSED as separate applicability dimension |
| Principal | CLOSED as actor/provenance context, not Automation Authority |
| Authentication | NAMED UPSTREAM via RCP-01/G03; no S6 authority |
| Policy | CLOSED as consumed upstream authority |
| Trust | CLOSED as consumed upstream authority |
| Artifact Acceptance | CLOSED relationship via G11; not redefined |
| Execution Admission | CLOSED relationship via G12/RCP-02; not redefined |
| Configuration | CLOSED relationship via RCP-19; Definition != Managed Config |
| Secret Reference | CLOSED / allowed where semantically required |
| Secret Material | NAMED DOWNSTREAM/runtime/Foundation PF09 conditional; not ordinary S6 custody |
| Security / Privacy | CLOSED / governed disclosure/redaction |
| Serialization / Representation | semantic requirements CLOSED; physical representation NAMED DOWNSTREAM |
| Offline / Degraded | CLOSED at evidence/applicability level; no fail policy invented |
| Replay | CLOSED for Event/Operation/HITL/Trial semantics |
| Recovery / Reconciliation | CLOSED at responsibility/provenance level |
| Historical Interpretation | CLOSED / exact revision-pinned |
| Compatibility | CLOSED at semantic owner/classification level |
| Migration | CLOSED at obligation level; tooling deferred |
| Conformance | CLOSED; C14 mechanics |
| Foundation Dependency | CLOSED / provider-neutral |
| Internal Dependency | CLOSED / SDD acyclic |
| Cross-boundary Dependency | CLOSED for S6 obligations |
| Invariant | CLOSED / explicit |
| Decision Traceability | CLOSED to Z2/Z3/RRA/Foundation/Batch1 + CID-SV-B2-MDE/DAD |
| Explicit Non-goals | CLOSED |
| Named Downstream Deferral | CLOSED / no unnamed deferral |
| Revalidation Trigger | CLOSED per Module/Contract/MDE |

```text
TBD → 0
Implementation decides semantic dimension → 0
Framework/provider/database decides semantic dimension → 0
Unnamed Deferral → 0
Implementation-defined Escape → 0
```

---

# 40. Candidate Audit Result

```text
Authorized Boundary → S6 / 1 OF 1
S6 Internal Design → CLOSED AT CURRENT BATCH LEVEL
Internal Module Inventory → COMPLETE / 9
Unowned S6 Responsibility → 0
Duplicate Final Responsibility → 0
God Module → NONE_FOUND
Overfragmentation → NONE_FOUND
Internal Dependency Topology → CLOSED
Unresolved Hard Internal SDD Cycle → 0
Unresolved Automation Composition Dependency Cycle → 0 by accepted semantics

Automation Semantic Authority → PRESERVED
Automation Canonical Definition SoT → PRESERVED
Authority Transfer → 0
SoT Transfer → 0
Actual-state Ownership Transfer → 0

Definition/Validation/Certification/Acceptance/Admission → NON-COLLAPSED
Source Authoring Intake → CLOSED AT CURRENT DESIGN LEVEL
Visual Authoring Intake → CLOSED AT CURRENT DESIGN LEVEL
Bidirectional Semantic Interoperability → PRESERVED
Silent Semantic Loss → 0
Agent Candidate Intake → CLOSED AT S6 LEVEL
Agent Authority Transfer → 0

RCP-13 → CLOSED AT DESIGN-SEMANTIC LEVEL
RCP-14 → CLOSED AT DESIGN-SEMANTIC LEVEL
RCP-15 → CLOSED AT DESIGN-SEMANTIC LEVEL
RCP-16 Automation Source-side → CLOSED AT CURRENT DESIGN LEVEL
RCP-16 Full Cross-domain Closure → NOT CLAIMED
RCP-17 Automation-side → CLOSED AT CURRENT DESIGN LEVEL
RCP-17 Full Cross-domain Closure → NOT CLAIMED

Event Authority Transfer → 0
Event Received == Admission Collapse → 0
Composition == Admission Bypass → 0
Recursive Automation Invocation → NOT SUPPORTED / Owner-decided

Historical Interpretation → CLOSED
Offline / Degraded → CLOSED
Replay → CLOSED AT SEMANTIC LEVEL
Recovery / Reconciliation → CLOSED
Failure / Unknown → CLOSED
Security / Tenant / Policy / Trust → CLOSED
Secret Boundary → PRESERVED
Compatibility / Migration / Conformance → CLOSED
Foundation Consumption → CLOSED
Provider Identity Leakage → 0

Concrete Automation DSL/AST/IR → 0
Concrete Visual Schema → 0
Concrete Broker/Queue/Topic → 0
Concrete Workflow Engine → 0
Concrete Process/Worker Topology → 0
Concrete DB/ORM/Schema → 0
Concrete REST/RPC/WebSocket Schema → 0

Other RCP Complete-design Leakage → 0
Other ns_server Boundary Internal-design Leakage → 0
Other Component Internal-design Leakage → 0
System-level SDK Detailed-design Leakage → 0

Open MDE → 0
Unpersisted Owner Decision → 0
Missing Product Capability → 0
Missing Component Boundary → 0
Missing Runtime Responsibility → 0
Missing Foundation Semantic → 0
Unnamed Deferral → 0
Implementation-defined Escape → 0
Implementation Planning Leakage → 0
```

---

# 41. Candidate Status / Stop Boundary

```text
NGRP-001
Component Internal Design
/ ns_server
/ Batch 2
/ S6 Automation Domain

→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This candidate does not claim Global Acceptance, does not declare `ns_server` Internal Design complete/exhausted, does not authorize another ns_server Batch or another Product Component, does not claim full RCP-16/RCP-17 closure, does not authorize System-level SDK Detailed Design, Design-to-Implementation Readiness, Implementation Planning, IWP or coding.

After producing DAD/review/handoff evidence, this session must:

```text
STOP
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```