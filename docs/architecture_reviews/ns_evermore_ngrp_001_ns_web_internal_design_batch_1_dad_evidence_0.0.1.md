# NGRP-001 — Component Internal Design / ns_web / Batch 1 — DAD Evidence

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Component Internal Design / ns_web / Batch 1`
- Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_WEB / BATCH_1 / GOVERNED_ADMINISTRATION_CONTROL_EXPERIENCE_SEMANTICS_ACCESSIBILITY_DEGRADED_INTERACTION_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Authorized Boundaries: `W1 + W7`
- Runtime-facing Role: `WB-R01`
- Producing Entry HEAD: `392d817c60c2b69bf5367a6224dbb5b701c12fcf`
- Candidate Commit: `c4a83ff19311d5c330ca9f7b0d015bc958a586e5`
- Decision Registry: `0.0.35 / CURRENT / NORMATIVE`
- DAD Count: `15`
- MDE Authority: `NONE`
- Global Acceptance Authority: `NONE`

All decisions below are bounded architecture-semantic choices that refine already accepted W1/W7 capability and responsibility. None changes Product capability, Authority, Source of Truth, final Actual-state ownership, Trust boundary, material fail law, conflict-winner/merge law, major universal identity namespace, public dependency, or high-migration technology lock-in.

---

# CID-WB-B1-DAD-001 — W1/W7 Internal Responsibility Decomposition and WB-R01 Ownership Boundary

**Decision / Issue**

How should W1 and W7 be decomposed at Component Internal Design level while keeping WB-R01 facts distinct from domain/source facts?

**Context**

The accepted boundary baseline defines W1 and W7 as architecture-level responsibilities, not implementation modules. W1 owns only bounded frontend interaction/session facts; W7 owns presentation semantics. Neither may absorb governance/config/runtime authorities.

**Alternatives Considered**

1. One monolithic `Web Governance/Experience` internal responsibility.
2. One internal responsibility per future page/widget/interaction surface.
3. Decompose by semantic lifecycle and ownership pressure while keeping labels document-local.

**Selected Design-semantic Result**

Select option 3: `11` W1 responsibilities and `9` W7 responsibilities, `20` total. W1 separates projection, intent, applicability, outcome, config, history and offline semantics; W7 separates presentation vocabulary, locale, time, accessibility, status/error, degraded state, disclosure, cross-surface conformance and presentation provenance.

**Rationale**

The decomposition follows distinct semantic ownership, temporal/failure behavior and dependency boundaries without converting architecture concepts into frontend packages or pages.

**Responsibility Consequence**

WB-R01 owns only interaction/session/intent-submission/provenance facts genuinely originating in Web. W7 owns presentation transformation semantics only.

**Dependency Consequence**

Internal dependencies are typed using SDD/ACD/EL/HPL/XED; no view/component import graph is implied.

**Authority / SoT / Actual-state Consequence**

No Product/domain Authority or SoT moves to Web. No runtime/source Actual-state moves to Web. Local presentation state remains non-canonical.

**RCP Consequence**

Provides responsibility homes for bounded RCP-01/19/22/24 Web contributions without adding an RCP.

**Failure / Offline Consequence**

Failure/offline semantics remain responsibility-specific and do not create a universal Web lifecycle or fail law.

**Explicit Non-implications**

Does not define Vue/React components, pages, stores, routes, processes, services, package hierarchy or deployment units.

**Deferred Implementation Mechanics**

Frontend component/package structure, state management, routing, rendering and process topology.

**Revalidation Trigger**

Any proposal to make a Web internal responsibility a new Product authority/SoT, add a new Web Product boundary, or collapse W1/W7 into a universal control-plane authority.

---

# CID-WB-B1-DAD-002 — Source-preserving Administration Projection Qualification

**Decision / Issue**

How should W1 represent governance/configuration/acceptance/admission state without making a Web projection authoritative?

**Context**

W1 must display authoritative/derived state with freshness/provenance. `Web Projection != Source Actual-state` and `Frontend Cache != SoT` are permanent.

**Alternatives Considered**

1. Flatten source state into a frontend-owned current-state model and treat it as operational truth.
2. Mirror source payloads verbatim without source/currentness/disclosure qualification.
3. Define a representation-neutral qualified projection that always preserves source owner/reference/revision/currentness/provenance/disclosure semantics.

**Selected Design-semantic Result**

Select option 3. Every material administration projection preserves projected-subject reference, applicable source/authority owner, source/evidence revision where applicable, governance context references, currentness/uncertainty, provenance/correlation, sensitive-disclosure qualification and compatibility/conformance qualification where material.

**Rationale**

A projection can remain useful under stale/degraded conditions only if it explicitly preserves what is source-owned and what is presentation qualification.

**Responsibility Consequence**

W1-R02 owns projection qualification, not source lifecycle. W1-R07/R08/R09 consume it.

**Dependency Consequence**

Hard SDD from W1-R02 to W7-R01; ACD/EL/XED to source contracts/evidence. No reverse SDD from sources to a Web-owned canonical model is created.

**Authority / SoT / Actual-state Consequence**

Source authorities and Actual-state owners remain unchanged; cache/projection cannot become canonical by retention or display.

**RCP Consequence**

Refines Web consumption of RCP-01/RCP-19 and presentation expectation for RCP-22.

**Failure / Offline Consequence**

Stale/unknown/unreachable/partial state remains explicit. Offline snapshot possession never promotes currentness or authority.

**Explicit Non-implications**

No frontend store schema, cache technology, data-fetching policy or API response shape is selected.

**Deferred Implementation Mechanics**

Cache invalidation, query mechanisms, UI update strategy, store/view-model implementation.

**Revalidation Trigger**

Any proposal that lets Web projection/cache choose canonical source state or suppress material uncertainty.

---

# CID-WB-B1-DAD-003 — Authoritative Target Reference, Intent Identity and Correlation Semantics

**Decision / Issue**

How should Web-origin command intent be identified and correlated without freezing a major physical identity namespace or equating browser requests with semantic intent?

**Context**

RCP-24 requires human/Web intent source-side semantics. Operation identity must remain independent of browser session. Physical UUID/request/header/DTO formats are downstream.

**Alternatives Considered**

1. Treat browser session + request ID as semantic intent identity.
2. Freeze one universal Product-wide physical intent/target identifier format.
3. Define representation-neutral semantic concepts for intent identity, authoritative target reference and lineage correlation while deferring physical representation.

**Selected Design-semantic Result**

Select option 3. A governed intent has its own semantic identity; it references an authoritative target using source-preserving identity; it carries originating interaction/session provenance and correlation lineage independent of browser/session lifetime.

**Rationale**

Semantic identity stability is required for return-later observation, retries/re-submissions, history and authoritative outcome correlation, but the architecture does not need a Product-wide physical namespace.

**Responsibility Consequence**

W1-R03 is the internal owner of Web intent/target correlation semantics; W1-R04/R05/R06 depend on it.

**Dependency Consequence**

SDD `W1-R03 → W1-R01`; EL/XED to authoritative target/source identity.

**Authority / SoT / Actual-state Consequence**

Target Authority remains with the target domain. Correlation is not ownership. Browser/session identity does not become operation owner.

**RCP Consequence**

Closes the identity/correlation portion of W1's RCP-24 source-side contribution.

**Failure / Offline Consequence**

The same semantic intent lineage can remain traceable across disconnect/re-observation without selecting latest-client state as winner.

**Explicit Non-implications**

No UUID format, database key, URL, header, request ID, event ID or universal Operation ID representation is selected.

**Deferred Implementation Mechanics**

Physical identifier generation/storage, request correlation propagation and transport encoding.

**Revalidation Trigger**

A proposal for a mandatory universal physical identity namespace, target identity takeover by Web, or correlation-as-ownership semantics.

---

# CID-WB-B1-DAD-004 — Local Possession / Submission / Applicability / Outcome Non-collapse

**Decision / Issue**

What semantic stages must W1 distinguish for governed human/admin command intent?

**Context**

Permanent rules require `Intent != Permit/Acceptance/Admission/Outcome`, `Submitted != Applicable`, and transport success must not become semantic success. Offline intent possession must remain non-authoritative.

**Alternatives Considered**

1. Optimistic success: button/request success is immediately shown as authoritative success unless later contradicted.
2. Two-stage submitted/succeeded model.
3. Four-layer semantic separation: local intent possession, submission occurrence, receiving-authority applicability observation, authoritative outcome correlation.

**Selected Design-semantic Result**

Select option 3.

```text
Local / Offline Intent Possession
!= Intent Submission Occurrence
!= Intent Applicability Observation
!= Authoritative Outcome
```

W1 owns the Web-origin intent and submission occurrence facts only. Applicability and authoritative outcome remain externally owned.

**Rationale**

This separation is the minimum stable architecture needed to avoid optimistic-authority collapse across policy, governance, config, acceptance/admission and long-running operations.

**Responsibility Consequence**

W1-R04 owns intent/submission; W1-R05 observes applicability; W1-R06 correlates outcome.

**Dependency Consequence**

SDD flow `W1-R04 → W1-R03`, `W1-R05 → W1-R03,W1-R04`, `W1-R06 → W1-R03,W1-R05`; outcome linkage is EL/XED/HPL, not reverse SDD.

**Authority / SoT / Actual-state Consequence**

No receiving authority, source SoT or final Actual-state is moved to Web. Submission possession never establishes authorization/application.

**RCP Consequence**

Primary W1 refinement of RCP-24; also constrains how W1 sends administration intents affecting RCP-01/RCP-19 subjects.

**Failure / Offline Consequence**

Offline possession is allowed as a local interaction fact; inability to submit/observe remains explicit. Reconnect does not infer previous success.

**Explicit Non-implications**

No optimistic UI algorithm, retry/backoff policy, deduplication guarantee, delivery guarantee or idempotency mechanism is selected.

**Deferred Implementation Mechanics**

Queueing, retransmission, retry, deduplication, transport acknowledgement, UI animation and local persistence.

**Revalidation Trigger**

Universal optimistic-success semantics, automatic application on reconnect, or any Web-side applicability/outcome authority.

---

# CID-WB-B1-DAD-005 — Governance / Policy / Trust / Acceptance / Admission Administration Non-collapse

**Decision / Issue**

How should W1 administer and present governance-related subjects without collapsing adjacent authorities?

**Context**

S1-S4/S8 are globally accepted, with permanent separation of Tenant, Organization, Principal/AuthN, Policy, Trust, Artifact Acceptance and Execution Admission.

**Alternatives Considered**

1. One generic frontend `authorized/allowed` state controlling all governance actions.
2. UI-specific merged governance state optimized for convenience.
3. Preserve each source semantic identity/revision/evidence and compose only for presentation/action context.

**Selected Design-semantic Result**

Select option 3. W1-R07 presents each constituent separately and treats enablement/visibility as a projection of currently known affordance only.

**Rationale**

Merging these states would silently create Web-defined authorization semantics and destroy historical/provenance interpretation.

**Responsibility Consequence**

W1-R07 consumes RCP-01 plus S8 Acceptance/Admission evidence; W7 renders without semantic mutation.

**Dependency Consequence**

SDD `W1-R07 → W1-R02`; ACD/EL to RCP-01/S8 source evidence.

**Authority / SoT / Actual-state Consequence**

All source authorities stay with S1-S4/S8. `UI Affordance Available != Permission Granted` remains permanent.

**RCP Consequence**

Closes W1's RCP-01 presentation/consumption refinement; RCP-02 is only consumed as upstream Admission evidence and is not independently redesigned.

**Failure / Offline Consequence**

Stale/unknown/unavailable governance evidence cannot be converted into authorization. This DAD introduces no global fail-open/closed law.

**Explicit Non-implications**

No RBAC/ABAC/ReBAC model, policy engine, trust engine, IAM provider, artifact registry, admission endpoint or UI permission algorithm is selected.

**Deferred Implementation Mechanics**

Concrete enforcement call path, policy-query API, controls/widgets and state-store realization.

**Revalidation Trigger**

Any proposal to let UI state/affordance grant permission, merge Policy/Trust/Acceptance/Admission, or shift their Authority/SoT to Web.

---

# CID-WB-B1-DAD-006 — Desired / Distributed / Applied / Observed Configuration Presentation Separation

**Decision / Issue**

How should W1 support managed configuration administration while preserving RCP-19 ownership?

**Context**

S9/G13/SV-R05 owns canonical Desired state; applicable runtime owner owns Applied; Observed is projection. W1 may originate human Desired-state administration intent.

**Alternatives Considered**

1. Treat submitted UI configuration as the canonical Desired state.
2. Show a single `current configuration` state collapsing Desired/Applied/Observed.
3. Preserve Desired/Distributed/Applied/Observed and their independent revisions/evidence while letting W1 own only human administration intent.

**Selected Design-semantic Result**

Select option 3. W1-R08 explicitly distinguishes Desired, Distributed, Applied, Observed, plus partial/failure/unknown/stale/conflicting/reconciliation-pending qualifications where evidenced.

**Rationale**

Managed configuration is a high-risk control-plane surface; a single current-value model would obscure drift and transfer Source-of-Truth semantics to Web.

**Responsibility Consequence**

W1-R08 is the config administration projection responsibility; W1-R04 supplies change intent; W7 supplies presentation/currentness semantics.

**Dependency Consequence**

SDD `W1-R08 → W1-R02,W1-R03`; EL/HPL/XED to RCP-19 source evidence.

**Authority / SoT / Actual-state Consequence**

Desired SoT remains S9/G13; Applied remains runtime owner; Observed remains derived; Web gains no config SoT.

**RCP Consequence**

Closes the authorized W1/W7 Web-side RCP-19 contribution at current Batch design level; no Full Cross-component Closure is claimed.

**Failure / Offline Consequence**

Offline last-known Desired and Applied evidence remain separately qualified. No local/central/latest winner or automatic merge is introduced.

**Explicit Non-implications**

No config push/pull/watch/rollout protocol, storage, local cache, synchronization or merge algorithm is selected.

**Deferred Implementation Mechanics**

Config editor UI, transport, rollout engine, reconciliation job, caching and persistence.

**Revalidation Trigger**

Web/local cache promoted to Desired/Applied SoT, automatic conflict winner/merge, or a new fail-open/closed config law.

---

# CID-WB-B1-DAD-007 — Orthogonal Status / Error / Currentness Qualification Without Universal Web Lifecycle

**Decision / Issue**

Should W1/W7 define one common Web lifecycle state machine for UNKNOWN/STALE/UNAVAILABLE/etc., or preserve orthogonal source/projection/interaction qualifications?

**Context**

Repository authority explicitly states these terms are qualifications applied where semantically appropriate, not one universal Web lifecycle.

**Alternatives Considered**

1. One universal frontend enum/state machine for every resource/operation.
2. Per-screen ad hoc labels with no common semantic discipline.
3. A common presentation qualification discipline over distinct source lifecycle, projection currentness, reachability, interaction progress and reconciliation evidence.

**Selected Design-semantic Result**

Select option 3. W7-R01/R05/R06 define semantic-preserving presentation qualification. Required terms may be used only where supporting source/projection/interaction evidence establishes them:

`UNKNOWN`, `STALE`, `UNAVAILABLE`, `UNREACHABLE`, `PARTIAL`, `INDETERMINATE`, `CONFLICTING`, `PENDING`, `SUPERSEDED`, `RECONCILIATION_PENDING`.

**Rationale**

A universal state machine would rewrite domain lifecycle semantics; ad hoc labels would destroy cross-surface consistency.

**Responsibility Consequence**

W7-R05 owns status/error/currentness presentation; W7-R06 owns degraded qualification composition.

**Dependency Consequence**

SDD `W7-R05 → W7-R01`; `W7-R06 → W7-R01,W7-R05`; EL to source/Foundation evidence.

**Authority / SoT / Actual-state Consequence**

Presentation vocabulary does not become a domain status authority or universal Runtime SoT.

**RCP Consequence**

Supports RCP-01/19/22/24 presentation without changing their source semantics.

**Failure / Offline Consequence**

Permanent: `UNKNOWN != FAILED`, `STALE != CURRENT`, `UNAVAILABLE != DENIED`, `CONFLICTING != winner selected`, `PENDING != accepted`, `RECONCILIATION_PENDING != reconciled`.

**Explicit Non-implications**

No state-management library, frontend enum representation, transition table, polling policy or error-code schema is selected.

**Deferred Implementation Mechanics**

Concrete status model representation, rendering components, polling/subscription and animations.

**Revalidation Trigger**

A universal lifecycle that overrides source semantics, implicit failure from unknown, or currentness derived solely from client state/clock.

---

# CID-WB-B1-DAD-008 — Offline Intent Possession, Reconnect, Re-observation and Reconciliation Semantics

**Decision / Issue**

What can Web own while offline, and what does reconnect mean?

**Context**

Offline client possession cannot transfer Authority; RT-R04/source owners retain recovery/reconciliation roles. No local/central/latest conflict winner is accepted.

**Alternatives Considered**

1. Local-first winner: offline Web state becomes canonical until synchronized.
2. Server/central/latest-wins reconciliation law.
3. Retain local projection/intent evidence with explicit qualification; reconnect enables re-observation/re-submission but not automatic reconciliation or winner selection.

**Selected Design-semantic Result**

Select option 3.

```text
Offline Intent Possession != Submission
Offline Projection != Source Truth
Reconnect != Reconciled
Re-observation != Canonicalization
Conflict Detected != Conflict Resolved
```

**Rationale**

This preserves private/offline usability without inventing a Product-wide synchronization authority or conflict law.

**Responsibility Consequence**

W1-R10 owns Web-local offline/re-observation semantics; W7-R06 renders degraded qualification.

**Dependency Consequence**

SDD `W1-R10 → W1-R02,W1-R03,W1-R04`; EL to RT-R04/source recovery evidence where applicable; no reverse authority dependency.

**Authority / SoT / Actual-state Consequence**

No local cache/state becomes Product SoT; no source recovery authority moves to Web.

**RCP Consequence**

Constrains RCP-19/RCP-24 presentation/intent and RCP-22 provenance; does not claim RCP-20 design/closure.

**Failure / Offline Consequence**

Conflict/unknown/reconciliation-pending remain explicit. No retry, merge, authoritative sync direction or fail-open/closed law is created.

**Explicit Non-implications**

No PWA/service worker/IndexedDB, offline queue, retry/backoff, sync engine, CRDT, LWW or cache invalidation algorithm is selected.

**Deferred Implementation Mechanics**

Persistence, retransmission, connection detection, refresh, deduplication and reconciliation UI mechanics.

**Revalidation Trigger**

Any local-vs-central winner/merge law, authoritative synchronization direction, universal offline fail law or browser-local canonical Product state.

---

# CID-WB-B1-DAD-009 — Locale / Localization Semantic Neutrality

**Decision / Issue**

How should W7 localize product presentation without letting language become semantic or governance identity?

**Context**

Owner-selected first-class internationalization requires language-neutral semantics and pluggable localization; locale is distinct from Tenant/Principal/timezone.

**Alternatives Considered**

1. Localized strings are the primary status/error/action identifiers.
2. One locale is bound to each Tenant.
3. Locale is explicit presentation context over language-neutral source semantics; localization resources affect wording only.

**Selected Design-semantic Result**

Select option 3.

```text
Semantic Identity != Display Language
Locale != Tenant != Organization != Principal != Timezone
Localized Text != Authorization / State / Protocol Identity
```

**Rationale**

This preserves private/multinational/re-delivery compatibility and avoids machine logic depending on translated text.

**Responsibility Consequence**

W7-R02 owns locale/localization presentation semantics; W7-R01 owns semantic vocabulary; W7-R07 preserves disclosure.

**Dependency Consequence**

SDD `W7-R02 → W7-R01`; consumes accepted Localization Presentation Foundation mechanics.

**Authority / SoT / Actual-state Consequence**

Localization resources and selected locale own no Product/domain state or governance authority.

**RCP Consequence**

All authorized RCP presentation remains language-neutral under localized rendering; no RCP semantics change.

**Failure / Offline Consequence**

Missing/unsupported localization is a presentation degradation, not a domain failure. Supported resources required for core use must be locally deployable.

**Explicit Non-implications**

No locale identifier standard, language set, fallback hierarchy, translation file format, template engine, AI translation or online translation service is selected.

**Deferred Implementation Mechanics**

Locale resolution, resource packaging, interpolation/pluralization and fallback behavior.

**Revalidation Trigger**

Localized text promoted to machine identity, locale coupled to Tenant/timezone, or mandatory public translation service.

---

# CID-WB-B1-DAD-010 — Source-time / Presentation-timezone / Client-clock Separation

**Decision / Issue**

How should W7 render time without changing source occurrence semantics or using client time as canonical ordering/conflict authority?

**Context**

Client clock is not source-time authority; timezone presentation must preserve source timestamp and occurrence ordering.

**Alternatives Considered**

1. Convert source timestamps on ingestion and retain only localized/display time.
2. Use browser/client timestamps as common ordering/currentness authority.
3. Preserve source temporal evidence and separately derive display time under an explicit presentation timezone.

**Selected Design-semantic Result**

Select option 3.

```text
Source Time Evidence
→ preserved

Presentation Timezone
→ display context only

Client Clock
→ non-authoritative local rendering/observation input only
```

**Rationale**

Historical audit, cross-session consistency and conflict safety require source time/provenance to survive presentation transformations.

**Responsibility Consequence**

W7-R03 owns display transformation semantics; W7-R09 may preserve transformation provenance for diagnostics.

**Dependency Consequence**

SDD `W7-R03 → W7-R01`; EL/HPL to source temporal evidence; consumes Temporal & Freshness Foundation semantics.

**Authority / SoT / Actual-state Consequence**

Source owner remains temporal authority for its fact. Client clock never becomes canonical winner or source timestamp authority.

**RCP Consequence**

Preserves temporal/provenance interpretation of RCP-01/19/22/24 evidence.

**Failure / Offline Consequence**

Offline retained source time can be rendered; inability to establish freshness remains explicit and cannot be repaired by client clock alone.

**Explicit Non-implications**

No timezone/date library, clock synchronization protocol, timestamp format or ordering algorithm is selected.

**Deferred Implementation Mechanics**

Date/time formatting, locale formatting, clock APIs and refresh scheduling.

**Revalidation Trigger**

Client/highest/latest timestamp used as canonical conflict winner, source timestamps discarded, or locale/timezone conflation.

---

# CID-WB-B1-DAD-011 — Critical-workflow Accessibility Semantic Parity Without Additional Authority

**Decision / Issue**

How should W7 realize the accepted first-class accessibility capability at architecture-semantic level?

**Context**

Owner decision requires accessible critical-workflow completion paths, semantic interaction parity, non-pointer-only critical operations and non-color-only critical meaning; exact framework/certification remains deferred.

**Alternatives Considered**

1. Treat accessibility as implementation-only best effort.
2. Require identical visual/gesture parity for every modality.
3. Require semantically equivalent accessible completion/perception for critical workflows while allowing different presentation/interaction modalities.

**Selected Design-semantic Result**

Select option 3. Critical actions/status/errors expose structured semantic purpose/state and an accessible completion/perception path. Accessible confirmation confirms only the human interaction occurrence and adds no Policy/Trust/Acceptance/Admission authority.

**Rationale**

This exactly realizes the accepted Owner capability without expanding it into a new Product-wide certification commitment.

**Responsibility Consequence**

W7-R04 owns accessibility-preserving presentation/interaction semantics. W1 critical administration interactions consume it.

**Dependency Consequence**

SDD `W7-R04 → W7-R01`; ACD to W1 critical interactions; no Shared Foundation accessibility module is created.

**Authority / SoT / Actual-state Consequence**

Accessibility behavior owns no source authority/SoT/Actual-state. Accessible confirmation never creates authorization or semantic outcome.

**RCP Consequence**

Authorized RCP interactions/presentations must remain semantically perceivable/operable where they form critical human workflows; source RCP semantics unchanged.

**Failure / Offline Consequence**

Accessibility remains required for locally usable critical workflows in private/offline deployment; inaccessible modality cannot be treated as successful semantic parity.

**Explicit Non-implications**

No accessibility library, design system, assistive technology, formal certification, exact external standard/version or universal visual parity is selected.

**Deferred Implementation Mechanics**

Focus management, keyboard maps, screen-reader announcements, component semantics, testing tools and conformance automation.

**Revalidation Trigger**

A critical workflow becomes pointer/color/animation-only, accessibility depends on mandatory public SaaS, or a new Product-wide compliance/certification commitment is proposed.

---

# CID-WB-B1-DAD-012 — Redaction / Non-leak Invariance Across Locale, Accessibility and Degraded Modes

**Decision / Issue**

How should alternate presentation modes preserve security/privacy and avoid unauthorized resource-existence leakage?

**Context**

W1/W7 must be authorization/privacy-aware; possessing cached/source data does not establish disclosure permission. Locale/accessibility/error/degraded presentations must not leak additional data.

**Alternatives Considered**

1. Apply redaction only in the normal visual presentation path.
2. Allow accessibility/localization/diagnostics fallbacks to expose richer raw source information for usability.
3. Make disclosure/redaction invariants apply across every presentation mode, with intentional non-distinguishing presentation when existence/state disclosure is not authorized.

**Selected Design-semantic Result**

Select option 3. W7-R07 preserves minimization/redaction and `Secret Reference != Secret Material` across normal, localized, accessible, error/degraded, offline, history and diagnostic presentation.

A non-distinguishing user-visible experience may withhold whether the hidden source fact is denied/nonexistent/unavailable/etc.; it does not semantically rewrite those source states into one domain status.

**Rationale**

Alternate rendering must not become an accidental bypass of Policy/privacy/existence-disclosure semantics.

**Responsibility Consequence**

W7-R07 composes with W1-R02/R07/R09 and W7-R02/R04/R05/R06.

**Dependency Consequence**

Consumes Governed Context, Secret Reference and Sensitive-data Redaction Foundation semantics; presentation-mode relationships are ACD, not hard local SDD.

**Authority / SoT / Actual-state Consequence**

No new Policy/Privacy/Trust authority; source disclosure authority remains external.

**RCP Consequence**

Constrains RCP-01/19/22/24 presentation and history without altering source semantics.

**Failure / Offline Consequence**

Offline possession never implies disclosure authorization. Missing fresh disclosure evidence cannot be treated as permission.

**Explicit Non-implications**

No new source status such as a universal `NOT_DISCLOSED`, no secret store, encryption mechanism or policy engine is created.

**Deferred Implementation Mechanics**

Field-level masking, UI copy, diagnostic access controls and localization/accessibility rendering implementation.

**Revalidation Trigger**

New disclosure/trust boundary, cross-Tenant leakage, Secret Material in ordinary Web state, or alternate modes bypassing redaction.

---

# CID-WB-B1-DAD-013 — Web Interaction Provenance + Source Provenance Correlation

**Decision / Issue**

How should W1/W7 support history/audit/diagnostics without making Web an audit/source-fact authority?

**Context**

RCP-22 is federated by original fact ownership. WB-R01 genuinely originates bounded interaction/session/intent-submission facts, while source results/diagnostics remain source-owned.

**Alternatives Considered**

1. Create a Web-owned universal audit/history SoT from aggregated facts.
2. Show only current state and discard interaction/source lineage.
3. Preserve federated provenance: Web owns its own interaction facts, correlates source-owned evidence, and presents authorized history without canonicalizing sources.

**Selected Design-semantic Result**

Select option 3. W1-R09 owns Web interaction-history projection; W7-R09 owns presentation-transformation provenance sufficient for explainability. Original source facts retain original owners.

**Rationale**

Cross-session administration and degraded recovery require durable correlation, but aggregation must not transfer source authority.

**Responsibility Consequence**

Interaction/session/intent/submission lineage is first-class WB-R01 evidence; source outcome/provenance is linked, not copied into a new final fact owner.

**Dependency Consequence**

EL/HPL to all displayed source evidence; consumes Diagnostic Occurrence and Correlation/Provenance Foundation semantics.

**Authority / SoT / Actual-state Consequence**

No universal Web audit SoT, source diagnostic SoT or operation ownership is created.

**RCP Consequence**

Defines the authorized Batch-1 RCP-22 Web contribution; Full Cross-component RCP-22 Closure remains unclaimed.

**Failure / Offline Consequence**

History may be partial/stale/unavailable; missing source evidence remains missing rather than filled from presentation state. Recovery may add new evidence without rewriting prior provenance.

**Explicit Non-implications**

No audit database, event store, log aggregator, telemetry backend, retention duration or immutable-ledger implementation is selected.

**Deferred Implementation Mechanics**

Storage/indexing/querying/retention, log/trace propagation and audit UI.

**Revalidation Trigger**

Web aggregation promoted to universal source-of-truth, source provenance discarded, or historical facts rewritten by current projection.

---

# CID-WB-B1-DAD-014 — W1↔W7 Stable Semantic Contract Family, Typed Dependency Topology and Future Seam

**Decision / Issue**

What stable architecture-semantic subjects must W1/W7 expose internally/cross-boundary, and how should dependency cycles be prevented while leaving W2-W6 opaque?

**Context**

The Batch must synthesize representation-neutral stable contracts and prove hard SDD acyclicity. It may not design REST/DTO/props/store/routes or future W2-W6 internals.

**Alternatives Considered**

1. Define concrete frontend/API contract schemas now.
2. Leave W1/W7 semantics implicit for later implementation.
3. Define eight representation-neutral semantic subjects plus typed SDD/ACD/EL/HPL/XED dependencies and a future-consumption seam.

**Selected Design-semantic Result**

Select option 3. Stable subjects:

1. Administration / Governance Projection;
2. Governed Command Intent;
3. Authoritative Outcome Correlation;
4. Status / Error / Currentness Presentation;
5. Experience / Locale / Timezone Semantic Presentation;
6. Accessibility-preserving Critical Interaction;
7. Degraded / Offline Interaction Qualification;
8. Web Interaction Provenance.

Hard internal SDD is one-way from specialized presentation/interaction semantics toward their prerequisite definitions; W7 never semantically depends on W1 becoming canonical. W7 may consume W1 facts by ACD/EL.

**Rationale**

This is enough semantic stability for later Web batches and cross-surface Contract design without prematurely fixing representation or implementation topology.

**Responsibility Consequence**

All 20 Candidate responsibilities map to at least one stable subject or bounded internal-only semantic responsibility.

**Dependency Consequence**

Hard SDD graph is acyclic. Authority Cycle `NONE`; Circular Actual-state Ownership `NONE`.

**Authority / SoT / Actual-state Consequence**

Stable contracts preserve source owners; contract identity does not create Product authority.

**RCP Consequence**

Provides the architecture-semantic carrier for RCP-01/19/22/24 Web contributions; RCP count remains `24`.

**Failure / Offline Consequence**

Contract subjects preserve explicit uncertainty/degraded/history semantics; they contain no universal retry/merge/fail law.

**Explicit Non-implications**

No REST/GraphQL/gRPC/WebSocket wire protocol, DTO, JSON Schema, OpenAPI, props, store schema, route, browser event or canonical IR is selected. W2-W6 internals remain undesigned.

**Deferred Implementation Mechanics**

Physical schema/API/protocol, frontend type model, serialization encoding and integration mechanism.

**Revalidation Trigger**

Hard SDD cycle, new cross-component RCP, mandatory canonical representation/IR/DSL, or future seam that preempts W2-W6 authority.

---

# CID-WB-B1-DAD-015 — Accepted Shared Foundation Consumption Without Parallel Web Foundation

**Decision / Issue**

Which reusable mechanics should W1/W7 consume, and should Web create local equivalents for status/time/provenance/localization/accessibility?

**Context**

Shared Foundation Architecture/Contract/Module/Provider are globally closed. Applicable mechanics exist for time/freshness, status/uncertainty, provenance, governed context, secrets/redaction, compatibility and localization. Accessibility Helpers are explicitly not Foundation-eligible.

**Alternatives Considered**

1. Reimplement independent Web-local time/status/context/redaction/localization semantics.
2. Promote accessibility into a new parallel/shared Foundation subsystem.
3. Consume accepted Foundation semantics for eligible mechanics while keeping W7 accessibility as Web presentation semantics and creating no parallel Foundation.

**Selected Design-semantic Result**

Select option 3.

Applicable Foundation semantics are consumed through accepted boundaries; reuse never transfers Authority/SoT/Actual-state. Accessibility remains W7-owned semantic interaction/presentation behavior.

**Rationale**

This preserves cross-component semantic consistency and the accepted Foundation eligibility boundary while avoiding duplicated infrastructure semantics.

**Responsibility Consequence**

All W1/W7 responsibilities use accepted Foundation mechanics where applicable; none becomes a Foundation authority.

**Dependency Consequence**

Foundation dependencies are external accepted semantic dependencies; no new internal Web hard cycle and no Foundation capability is added.

**Authority / SoT / Actual-state Consequence**

Foundation provider/module placement remains authority-neutral. W7 accessibility remains non-authoritative.

**RCP Consequence**

Supports all four authorized RCP contributions without changing RCP identities/count or source owners.

**Failure / Offline Consequence**

Foundation unavailable/provider failure maps into accepted technical failure/uncertainty semantics; it does not relax governance or create public-service dependence.

**Explicit Non-implications**

No new Foundation capability/module/provider, no accessibility Foundation, no concrete provider/library/vendor and no mandatory public SaaS.

**Deferred Implementation Mechanics**

Concrete Foundation consumer wiring and replaceable provider/library realization.

**Revalidation Trigger**

A genuinely missing mandatory cross-component Foundation semantic, Web-local parallel Foundation, or Foundation/provider placement promoted to Product authority.

---

# DAD Set Audit

```text
Material DAD
→ CID-WB-B1-DAD-001..015

DAD Count
→ 15

Candidate Material Responsibility Coverage by DAD
→ 20 / 20

W1↔W7 Stable Semantic Subject Coverage
→ 8 / 8

RCP-01 Web-side bounded contribution
→ COVERED

RCP-19 Web-side bounded contribution
→ COVERED

RCP-22 Batch-1 Web contribution
→ COVERED

RCP-24 W1 source-side contribution
→ COVERED

New RCP
→ 0

RCP Count
→ 24 / unchanged

Misclassified MDE Found
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

New Product Capability
→ 0

Authority / SoT / Final Actual-state change
→ 0

New Trust Boundary
→ 0

Material fail-open / fail-closed law
→ 0

Conflict winner / merge / authoritative sync law
→ 0

Major universal physical identity namespace
→ 0

Mandatory public dependency
→ 0

Technology / framework / protocol / storage lock-in
→ 0

Implementation-defined Architecture Escape
→ 0
```

This DAD evidence does not claim Global Acceptance, any Full Cross-component RCP Closure, `ns_web` Component Internal Design completion/exhaustion/global closure, future Web Batch authorization, System-level SDK Detailed Design readiness, Design-to-Implementation Readiness, Implementation Planning, IWP or Coding authority.
