# NGRP-001 — Component Internal Design / ns_server / Batch 6 Candidate

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Component Internal Design / ns_server / Batch 6`
- Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_6 / GOVERNED_NOTIFICATION_AND_EXTERNAL_DELIVERY_LIFECYCLE_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Recovered Entry HEAD: `0f38d0123824025d7517e1e29ebac406fd675edc`
- Recovered Global State: `GAC-EPOCH-0060`
- State Verified Through HEAD: `a965d1ab28d8fbb10ad0707a2110b46a3c650229`
- Decision Registry: `0.0.21 / CURRENT / NORMATIVE`
- Authorized Boundary: `S12 — Governed Notification & External Delivery Lifecycle`
- Inherited Runtime Role: `SV-R08 — Notification Lifecycle & External Delivery Participant`
- Producing-session status: `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE` only when all companion evidence and Git verification complete
- Global Acceptance: `NOT CLAIMED`

This document is a bounded Component Internal Design candidate. It defines architecture-semantic internal responsibilities, dependencies, identities, lifecycle and stable RCP-18 obligations. It does not define a Django App, Python package, class, service, process, worker, queue, broker, database, table, API, message envelope, provider SDK, provider protocol, template language, recipient schema or deployment topology.

---

# 1. Fresh Repository Recovery

```text
Actual Branch HEAD at producing entry
→ 0f38d0123824025d7517e1e29ebac406fd675edc

Current GAC Epoch
→ GAC-EPOCH-0060

State Verified Through HEAD
→ a965d1ab28d8fbb10ad0707a2110b46a3c650229

State-to-HEAD Delta
→ exactly one commit
→ 0f38d0123824025d7517e1e29ebac406fd675edc
→ Global Architecture State only
→ GAC-EPOCH-0060 / Batch-6 authorization seal

Delta Classification
→ EXPECTED_GOVERNANCE

Unauthorized Progression
→ NONE

Unexplained Drift
→ NONE

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Item
→ NONE

Recovery Result
→ PASS
```

The current State, Working State, Decision Registry, GAC Ledger relevant tail, Batch 1–5 Global Acceptance baselines, S12 Owner capability decision, Human Task Owner capability decision, `Z2-MDE-014`, accepted Z3 boundary/runtime evidence and Foundation readiness evidence were consumed before synthesis.

---

# 2. Exact Authorized Object and Inherited Baseline

```text
S12
→ Governed Notification & External Delivery Lifecycle

SV-R08
→ Notification Lifecycle & External Delivery Participant
```

Inherited Owner capability result:

```text
Unified Governed Notification Capability
→ REQUIRED

In-product Notification Discovery / History
→ REQUIRED

Channel-neutral Core Notification Semantics
→ REQUIRED

Pluggable External Notification Delivery
→ REQUIRED

External Platform Push
→ REQUIRED AS PRODUCT CAPABILITY

Representative / Initial Target Directions
→ Feishu
→ WeCom / Enterprise WeChat
→ SMS

Mandatory Fixed Omnichannel Provider Set
→ NOT REQUIRED

Public Internet / Public SaaS Dependency for Core Correctness
→ PROHIBITED
```

Inherited Actual-state topology:

```text
S12 Product Authority over underlying source condition
→ NONE

SV-R08 final Actual-state owner
→ Notification existence
→ Notification lifecycle
→ Notification history
→ applicable Delivery Attempt facts

Underlying Source Fact / Source Condition
→ originating source owner

WB-R01
→ awareness / history projection only

External Provider
→ delivery evidence source only
→ NOT Product Authority
```

Permanent non-collapse:

```text
Notification != Source Fact
Notification != Runtime Current State
Notification != Human Task
Notification History != Current Source State
Notification Projection != Actual-state Owner
Notification persistence location != Authority
```

---

# 3. S12 Internal Architecture Decomposition

S12 is decomposed into eight architecture-semantic responsibilities.

```text
NT01 Notification Creation Intent & Source Correlation Intake
NT02 Audience Applicability, Authorization & Disclosure Governance
NT03 Notification Identity, Existence & Lifecycle History Custody
NT04 Delivery Intent & Channel Applicability Governance
NT05 Delivery Attempt Lifecycle & Lineage Custody
NT06 Provider Evidence Interpretation & Channel-neutral Normalization
NT07 Awareness Interaction Evidence & Notification History Interpretation
NT08 Recovery, Reconciliation & Historical Qualification
```

`NT01..NT08` are document-local architecture-semantic labels only.

```text
Internal Module Count
→ 8

Django App / Python package / class mapping
→ NOT DEFINED

Service / worker / process / queue mapping
→ NOT DEFINED

Database / table / storage mapping
→ NOT DEFINED
```

## 3.1 Why this is not a God Module

The design separates four materially different ownership/evidence concerns:

1. source-originated creation intent/correlation;
2. S12-owned Notification existence/history and audience/disclosure applicability;
3. external delivery intent/attempt/provider-evidence lifecycle;
4. human-awareness interaction and recovery/reconciliation qualification.

No single responsibility owns source facts, audience authorization, Notification existence, Delivery Attempt history, provider interpretation and interaction history simultaneously.

## 3.2 Why this is not overfragmented

The decomposition does not create separate modules for every status, channel, provider, lifecycle transition, retry type, UI surface, Tenant/Principal dimension or RCP-18 field. Compatibility, migration, conformance, temporal/provenance and S13 contribution obligations remain cross-cutting responsibilities of the modules that own the corresponding subject rather than becoming miscellaneous modules.

---

# 4. Internal Responsibility Profiles

## NT01 — Notification Creation Intent & Source Correlation Intake

**Purpose**

Establish representation-neutral intake semantics for a source-owned subject that requests governed Notification creation, while preserving source owner, source fact identity/correlation and creation-intent provenance.

**Owned responsibility**

- Notification Creation Intent identity and intake history;
- source-owner reference;
- source correlation references;
- source evidence provenance and observation context carried into S12;
- creation-intent replay/duplicate/conflict qualification without silently deciding Notification existence.

**Explicitly non-owned**

- source fact/current source condition;
- universal event taxonomy or event bus authority;
- universal alert policy;
- Notification existence;
- audience authorization decision;
- Delivery Intent/Attempt.

**Authority / Actual-state relationship**

NT01 gains no authority over the source. It owns only S12 intake evidence for a creation request. Source owner remains authoritative for source facts.

**Inputs**

Source Owner Reference, Source Fact/Event/Condition reference, Creation Intent identity, Tenant context, intended audience reference where supplied, source sensitivity provenance, correlation/provenance/temporal evidence.

**Outputs / evidence**

Qualified creation-intent evidence usable by NT02/NT03, with explicit `UNKNOWN`, `STALE`, `PARTIAL`, `CONFLICTING`, `INDETERMINATE` qualification where applicable.

**Identity responsibility**

Creation Intent Identity is required and distinct from Notification Identity and source identity. Source Correlation is a reference relationship, not automatic identity equality.

**Lifecycle responsibility**

Creation Intent may be received, qualified, rejected as malformed/unsupported/inapplicable at intake boundary, or remain uncertain; these are intake-evidence meanings, not a universal Notification lifecycle state machine.

**Dependencies**

Consumes S1–S4 governed context and source-owner evidence as ACD/XED. No hard SDD predecessor.

**Offline / failure semantics**

Offline/private source intent can be retained as provenance-bearing evidence where authorized. Missing source context does not fabricate source truth or Notification existence.

**History / provenance**

Intent identity, originating owner, source references, observation time and governing context remain historically interpretable.

**Compatibility / migration**

Creation-intent semantic revisions must preserve identity/correlation meaning. Representation migration cannot rewrite source ownership.

**Stable Contract participation**

RCP-18 producer/source-owner side.

**Foundation consumption**

Accepted authority-neutral context, correlation/provenance, temporal/freshness, representation, status/uncertainty and diagnostics semantics only.

**Explicit non-goals**

No broker/topic/event envelope, idempotency protocol, REST/RPC, UUID format or universal event policy.

## NT02 — Audience Applicability, Authorization & Disclosure Governance

**Purpose**

Determine S12-level applicability of intended audience/recipient exposure and external disclosure under inherited Tenant/Organization/Principal/Policy/Trust/privacy semantics.

**Owned responsibility**

- intended Audience Reference interpretation for S12;
- Tenant applicability;
- Organization applicability where relevant;
- Principal/recipient applicability;
- authorization applicability evidence;
- privacy/redaction/disclosure qualification;
- external-delivery disclosure boundary.

**Explicitly non-owned**

- Tenant/IAM/Policy/Trust semantic authority;
- source sensitivity authority;
- universal recipient directory;
- provider address authority;
- Human Task assignment;
- Notification existence by itself.

**Authority / Actual-state relationship**

NT02 owns the S12 applicability decision/evidence only. It consumes S1/S2/S3/S4 authority and source sensitivity provenance; it does not replace them.

**Inputs**

NT01 intent/source correlation, intended audience reference, Tenant/Organization/Principal context, Policy/Trust evidence, source sensitivity provenance, channel disclosure capability context.

**Outputs / evidence**

Audience applicability and disclosure/redaction constraints for NT03/NT04/NT05/NT07.

**Identity responsibility**

Audience Applicability Reference is required. Delivery Target identity/reference remains separate and cannot become semantic audience authority.

**Lifecycle responsibility**

Applicability may change over time; historical Notification/Delivery interpretation retains the applicable decision/context rather than substituting current policy.

**Dependencies**

Hard SDD: `NT02 → NT01`. S1–S4 are ACD/XED, not internal SDD.

**Offline / failure semantics**

Unavailable current authorization/privacy evidence remains `UNKNOWN`/`STALE`/`INDETERMINATE`; no generic fail-open/fail-closed policy is introduced.

**History / provenance**

Preserves decision provenance, source sensitivity context, redaction/disclosure context and temporal applicability.

**Compatibility / migration**

Audience semantics may evolve compatibly only if historical interpretation and Tenant/Principal/privacy boundaries remain preserved.

**Stable Contract participation**

RCP-18 audience/privacy obligations.

**Foundation consumption**

Governed context propagation, Secret Reference/redaction, temporal/provenance, status/uncertainty and conformance.

**Explicit non-goals**

No recipient schema, group model, address book, external directory, policy engine or privacy rule language.

## NT03 — Notification Identity, Existence & Lifecycle History Custody

**Purpose**

Own the S12/SV-R08 semantic identity, creation/existence determination, durable lifecycle history and historical interpretation of a governed Notification.

**Owned responsibility**

- Notification Identity;
- Notification existence establishment;
- Notification Occurrence Identity for S12-owned historical lifecycle occurrences;
- immutable historical occurrence/provenance relationships;
- current Notification lifecycle qualification as a multi-dimensional awareness record;
- source-change historical interpretation;
- S12-owned resource identity/revision metadata eligible for future S13 contribution.

**Explicitly non-owned**

- underlying source truth/current state;
- Delivery Intent/Attempt facts;
- provider evidence;
- WB projection state;
- source resolution;
- Human Task lifecycle.

**Authority / Actual-state relationship**

NT03 is the principal S12/SV-R08 owner for Notification existence/lifecycle/history. It never becomes source-fact owner.

**Inputs**

NT01 qualified Creation Intent/source correlation plus NT02 applicability evidence.

**Outputs / evidence**

Notification Identity, creation/existence evidence, Notification occurrence/history evidence, source-owner/correlation links, resource metadata for in-product history and future S13 contribution.

**Identity responsibility**

```text
Notification Identity
!= Source Fact Identity automatically
!= Creation Intent Identity
!= Delivery Intent Identity
!= Delivery Attempt Identity
!= Provider Request/Message ID
!= Correlation Identity
!= Database PK automatically
```

Notification Occurrence Identity identifies a material S12-owned historical lifecycle occurrence for one Notification; it is not a second canonical Notification resource identity.

Historical Notification reference uses the same Notification Identity plus the applicable occurrence/revision/temporal context; no separate `Historical Notification ID` namespace is created.

**Lifecycle responsibility**

Notification existence is established only when S12 accepts an applicable creation intent into the Notification lifecycle. The lifecycle is intentionally multi-dimensional rather than one mandatory ordered enum: existence/history, audience applicability, delivery histories and awareness-interaction evidence remain distinct.

**Dependencies**

Hard SDD: `NT03 → NT01, NT02`.

**Offline / failure semantics**

A Notification remains validly existent while external channels are unavailable/unreachable/unsupported/failed/pending/indeterminate. Uncertainty about a source's current condition does not erase historical Notification existence.

**History / provenance**

Source Owner Reference, source correlation, Creation Intent, applicable audience/governance context and occurrence chronology remain interpretable without replacing them with current source state.

**Compatibility / migration**

Notification Identity/history is compatibility-sensitive. Migration must preserve identity lineage and historical interpretation, without requiring a physical ID/storage format.

**Stable Contract participation**

RCP-18 Notification identity/lifecycle/history producer.

**Foundation consumption**

Temporal/history, correlation/provenance, representation, status/uncertainty, diagnostics, compatibility/conformance.

**Explicit non-goals**

No event store, notification table, UUID/sequence format, archive/delete policy or universal lifecycle enum.

## NT04 — Delivery Intent & Channel Applicability Governance

**Purpose**

Represent a governed intent to externally deliver a Notification without equating Notification creation with external delivery and without binding core semantics to provider-specific models.

**Owned responsibility**

- Delivery Intent Identity;
- Notification→Delivery Intent relationship;
- intended delivery objective;
- bounded channel class/category applicability;
- target applicability reference;
- intent history, replacement/re-delivery relationship where explicitly established;
- provider-independent channel capability requirements.

**Explicitly non-owned**

- Delivery Attempt lifecycle;
- provider request/message identity;
- universal fallback policy;
- provider selection technology;
- audience semantic authority.

**Authority / Actual-state relationship**

NT04 owns delivery-intent semantic state only. Notification existence remains NT03; provider/executor cannot create Delivery Intent authority by technical reachability.

**Inputs**

NT03 Notification Identity/existence, NT02 audience/disclosure applicability, configured channel capability context and applicable S9 desired configuration reference.

**Outputs / evidence**

Delivery Intent identity/context usable by NT05, including explicit unsupported/unavailable/pending/indeterminate applicability.

**Identity responsibility**

Delivery Intent Identity is required and distinct from Notification/Attempt/provider IDs. A Notification may have zero, one or multiple Delivery Intents.

For architecture clarity, one Delivery Intent represents one bounded delivery objective with one channel-class/target applicability context. A cross-channel or materially changed target objective is represented as a distinct correlated Delivery Intent rather than silently mutating the existing intent.

**Lifecycle responsibility**

Intent existence does not imply an Attempt exists or can be created. An intent may remain pending, unsupported, unavailable, inapplicable or indeterminate without losing the Notification.

**Dependencies**

Hard SDD: `NT04 → NT02, NT03`.

**Offline / failure semantics**

Offline channel unavailability leaves the intent/history intact and cannot transfer source/Notification authority.

**History / provenance**

Preserves Notification link, audience/disclosure context, channel-class context, configuration applicability, temporal and re-delivery/replacement lineage.

**Compatibility / migration**

Provider replacement is compatible when channel-neutral intent meaning is preserved. Channel-class semantic changes require explicit compatibility/migration classification.

**Stable Contract participation**

RCP-18 Delivery Intent obligations.

**Foundation consumption**

Configuration reference, status/uncertainty, temporal/provenance, representation and conformance.

**Explicit non-goals**

No fixed channel provider set, fallback tree, recipient schema, template language, routing engine or provider API.

## NT05 — Delivery Attempt Lifecycle & Lineage Custody

**Purpose**

Own S12/SV-R08 Actual-state for each bounded semantic external-delivery try and preserve retry/re-delivery lineage without creating a global delivery guarantee.

**Owned responsibility**

- Delivery Attempt Identity;
- Delivery Intent→Attempt relationship;
- bounded Attempt lifecycle and semantic outcome qualification;
- retry-of lineage between Attempts under the same Intent;
- Attempt history and provider-evidence linkage;
- S12 Applied delivery-runtime evidence where applicable.

**Explicitly non-owned**

- source operation success/failure;
- Notification source condition;
- recipient observation/read;
- provider authority;
- global retry count/cadence/backoff/fallback.

**Authority / Actual-state relationship**

NT05 is the final owner of Delivery Attempt Actual-state under SV-R08. Provider evidence is input; provider does not own the Product attempt state.

**Inputs**

NT04 Delivery Intent, current applicable audience/disclosure context, configured/applied channel capability evidence, NT06 normalized provider evidence via evidence linkage.

**Outputs / evidence**

Delivery Attempt lifecycle/history/outcome evidence with provenance and uncertainty.

**Identity responsibility**

Delivery Attempt Identity is required. One Delivery Intent may result in zero, one or multiple Attempts. Attempt Identity is never automatically the provider request/message ID.

**Lifecycle responsibility**

An Attempt is one bounded semantic delivery try. Architecture-level outcome qualifications may include pending/succeeded/failed/unavailable/unreachable/unsupported/indeterminate/conflicting/reconciliation-pending as applicable, but these terms do not freeze a provider enum or implementation state-machine representation.

`DELIVERY_SUCCEEDED` may be established only when admissible channel-neutral evidence is sufficient for the bounded delivery objective; `PROVIDER_ACCEPTED` alone is not universally sufficient. Recipient observation remains separate.

**Retry / re-delivery lineage**

```text
retry
→ a new Delivery Attempt under the same Delivery Intent
→ new Attempt Identity
→ explicit retry-of lineage
→ prior Attempt history never mutated

re-delivery
→ a new Delivery Intent for the same Notification when the delivery objective/channel/target applicability is intentionally renewed or changed
→ explicit re-delivery-of relationship to prior Intent where applicable
→ new Attempts belong to the new Intent
```

An optional explicit replacement/supersession relationship may be carried where source semantics establish it, but later timestamps do not imply supersession and there is no latest-attempt-wins rule.

**Dependencies**

Hard SDD: `NT05 → NT04`.

**Offline / failure semantics**

Disconnected/unreachable providers produce explicit uncertainty/failure qualification. Missing receipt is not definite failure. Reconnect does not retroactively authorize an Attempt.

**History / provenance**

Attempt identity, Intent identity, provider evidence references, configuration applicability, authorization/disclosure context, retry lineage and temporal history remain interpretable.

**Compatibility / migration**

Attempt/history interpretation must survive provider replacement. Migration cannot collapse multiple historical Attempts into one current state.

**Stable Contract participation**

RCP-18 Delivery Attempt producer.

**Foundation consumption**

Network-client mechanics, temporal/correlation/provenance, status/uncertainty, configuration reference, diagnostics/telemetry and conformance through accepted Foundation paths only.

**Explicit non-goals**

No exactly-once/at-most-once/at-least-once guarantee, retry engine, queue, dead-letter policy, backoff algorithm or worker topology.

## NT06 — Provider Evidence Interpretation & Channel-neutral Normalization

**Purpose**

Interpret provider-local evidence into channel-neutral evidence suitable for NT05 without elevating provider-native states or identifiers into Product semantics.

**Owned responsibility**

- provider evidence provenance;
- provider observation time/freshness;
- provider request/message identifier references;
- capability-aware evidence normalization;
- partial/unknown/conflicting evidence qualification;
- provider replacement compatibility evidence.

**Explicitly non-owned**

- Delivery Attempt final Actual-state;
- Notification lifecycle;
- recipient semantic observation authority;
- provider API/SDK/authentication protocol;
- provider-native enum as core state machine.

**Authority / Actual-state relationship**

NT06 owns S12 interpretation evidence only; NT05 remains final Delivery Attempt Actual-state owner. External provider remains an evidence source.

**Inputs**

NT05 Attempt Identity/context, provider-local evidence, provider capability semantics, provider observation time/provenance and authorized technical metadata.

**Outputs / evidence**

Normalized, provenance-bearing evidence statements consumed by NT05 through evidence linkage.

**Identity responsibility**

```text
Provider Request ID != Delivery Attempt Identity automatically
Provider Message ID != Notification Identity automatically
Provider Message ID != Delivery Intent Identity automatically
```

Provider identifiers are external references associated with an Attempt/Intent/Notification context where evidence establishes the relationship.

**Lifecycle responsibility**

Provider evidence may evolve and conflict. New evidence does not erase old evidence and latest timestamp is not a canonical winner.

**Dependencies**

Hard SDD: `NT06 → NT05`. NT05 consuming NT06 evidence is `EL`, not reverse SDD, so the semantic-definition graph remains acyclic.

**Offline / failure semantics**

No provider observation is required for core Notification existence. Provider unavailable/unreachable/partial evidence remains explicit.

**History / provenance**

Raw/provider-local meaning must remain traceable enough to explain normalized interpretation without making the raw enum the Product contract.

**Compatibility / migration**

Provider replacement must preserve channel-neutral meaning and historical evidence interpretation. Provider-specific IDs may remain historical references after replacement.

**Stable Contract participation**

RCP-18 provider-evidence interpretation obligations.

**Foundation consumption**

Network client, temporal/freshness, correlation/provenance, technical status/uncertainty, representation and Secret Reference/redaction through accepted paths.

**Explicit non-goals**

No Feishu/WeCom/SMS API, callback schema, SDK, webhook, gateway or authentication protocol.

## NT07 — Awareness Interaction Evidence & Notification History Interpretation

**Purpose**

Interpret authorized human-awareness interaction evidence for a Notification while preserving projection, observation, read, acknowledgement and source resolution as separate concepts.

**Owned responsibility**

- S12 correlation/interpretation of admissible awareness-interaction evidence;
- Notification-level observed/read/acknowledged history facts where evidence establishes them;
- principal/interaction provenance and temporal history;
- in-product history semantics consumed by awareness surfaces.

**Explicitly non-owned**

- WB-R01 projection/session state;
- Human Task response semantics;
- source condition resolution;
- Policy approval;
- external provider delivery state.

**Authority / Actual-state relationship**

WB-R01 may produce projection/interaction evidence; NT07 owns only S12 Notification interaction-history interpretation. It does not become source owner or Human Task owner.

**Inputs**

NT03 Notification identity/history, NT02 Principal/audience applicability, WB-R01 or other admissible observation/read/ack evidence, provider evidence only where it actually proves the corresponding interaction fact.

**Outputs / evidence**

Provenance-bearing Notification interaction-history facts.

**Identity responsibility**

Interaction occurrences correlate to Notification Identity + Principal/applicable audience context; no physical session/click/message ID becomes Notification Identity.

**Lifecycle responsibility**

The following are independent semantic predicates/evidence dimensions, not one mandatory ordered state machine:

```text
Projected / Visible
!= Observed

Observed
!= Read automatically

Read
!= Acknowledged automatically

Acknowledged
!= Resolved

Acknowledged
!= Policy Approved

Delivery Succeeded
!= Recipient Observed
```

`Resolved` belongs to the underlying source owner's condition where such a concept exists; S12 may correlate source resolution evidence historically but does not own it.

No universal monotonic sequence, auto-transition, auto-ack or acknowledgement side effect is accepted.

**Dependencies**

Hard SDD: `NT07 → NT02, NT03`.

**Offline / failure semantics**

Interaction evidence may be delayed, stale, conflicting or reconciliation-pending. Local possession/read evidence does not retroactively authorize disclosure.

**History / provenance**

Principal applicability, occurrence time, observation time and evidence source remain preserved.

**Compatibility / migration**

Future evolution must preserve the non-collapse meanings; adding a new interaction dimension must not reinterpret historical Read/Acknowledged as Source Resolved.

**Stable Contract participation**

RCP-18 in-product awareness/history consumer/producer obligations.

**Foundation consumption**

Governed context, temporal/provenance, correlation, status/uncertainty, redaction and compatibility/conformance.

**Explicit non-goals**

No UI page/state model, browser event schema, notification preference system, Human Task response lifecycle or approval semantics.

## NT08 — Recovery, Reconciliation & Historical Qualification

**Purpose**

Preserve S12-owned Notification/Delivery/interaction history and ownership across restart, reconnect, delayed provider evidence and reconciliation without choosing a universal conflict winner.

**Owned responsibility**

- reconciliation qualification for NT03/NT04/NT05/NT06/NT07 evidence;
- recovery state/history for S12-owned subjects;
- explicit stale/partial/conflicting/indeterminate/reconciliation-pending/recovering qualification;
- historical evidence re-association without mutation;
- compatibility/migration recovery evidence.

**Explicitly non-owned**

- source-fact reconciliation authority;
- provider authority;
- latest-wins/local-wins/central-wins decision;
- replay authorization;
- universal retry policy.

**Authority / Actual-state relationship**

Recovery does not transfer ownership. NT03/NT05 retain their final Actual-state responsibilities for Notification and Delivery Attempts; NT08 qualifies recovery/reconciliation evidence rather than becoming a universal state owner.

**Inputs**

NT03–NT07 historical/provenance evidence and source/provider observations as applicable.

**Outputs / evidence**

Qualified recovery/reconciliation evidence returned to the owning S12 responsibilities and exposed for authorized history/diagnostics.

**Identity responsibility**

Preserves original Notification/Intent/Attempt/Occurrence identities and lineage; restart/reconnect does not generate identity equivalence by itself.

**Lifecycle responsibility**

```text
Reconnect != Reconciled
Recovery != Authority Transfer
Retry after reconnect != Retroactive Authorization
Replay != proof of historical permission
Latest Timestamp != Canonical Winner
```

**Dependencies**

Hard SDD: `NT08 → NT03, NT04, NT05, NT06, NT07`.

**Offline / failure semantics**

Supports `UNKNOWN`, `UNAVAILABLE`, `UNREACHABLE`, `UNSUPPORTED`, `STALE`, `PARTIAL`, `FAILED`, `PENDING`, `INDETERMINATE`, `CONFLICTING`, `RECONCILIATION_PENDING`, `RECOVERING` as applicable semantic qualifications without making them one provider enum.

**History / provenance**

Preserves provenance, observation time, freshness and prior interpretations; recovery never deletes failed/partial attempts from history.

**Compatibility / migration**

Migration must preserve subject identities, lineage, source/provider evidence provenance and uncertainty. Physical migration does not complete semantic reconciliation automatically.

**Stable Contract participation**

RCP-18 recovery/history/compatibility obligations.

**Foundation consumption**

Temporal/freshness, status/uncertainty, correlation/provenance, diagnostics/telemetry and conformance.

**Explicit non-goals**

No replay engine, conflict-resolution algorithm, durable queue, provider retry scheduler, transaction/rollback mechanism or event sourcing mandate.

---

# 5. Hard Internal Dependency Graph

The accepted Batch-1 dependency taxonomy is reused:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only SDD participates in hard semantic-definition cycle analysis.

Hard SDD graph:

```text
NT02 → NT01
NT03 → NT01, NT02
NT04 → NT02, NT03
NT05 → NT04
NT06 → NT05
NT07 → NT02, NT03
NT08 → NT03, NT04, NT05, NT06, NT07
```

Topological order exists:

```text
NT01
→ NT02
→ NT03
→ NT04 / NT07
→ NT05
→ NT06
→ NT08
```

```text
Hard Internal SDD Graph
→ ACYCLIC

Unresolved SDD Cycle
→ 0

Circular Ownership
→ 0

Hidden Authority Transfer
→ 0
```

Provider evidence flowing from NT06 back to NT05 is Evidence Linkage and lifecycle evidence, not a reverse semantic-definition dependency. Interaction feedback into NT03 history is HPL/EL, not reverse SDD.

---

# 6. Notification Identity Model

Required semantic identities/references:

| Subject | Required? | Meaning | Explicit non-equivalence |
|---|---|---|---|
| Notification Identity | YES | durable S12 semantic identity of one governed Notification awareness record | source fact / intent / attempt / provider ID / DB PK |
| Notification Occurrence Identity | YES | identity of a material S12-owned lifecycle/history occurrence for that Notification | not a second Notification resource identity |
| Source Correlation Identity / Reference | YES | provenance-bearing link to source-owned subject/event/condition | not Notification Identity automatically |
| Source Owner Reference | YES | identifies authority/source owner of underlying source assertion | not S12 authority transfer |
| Notification Creation Intent Identity | YES | identifies one governed request/intention to create a Notification | not Notification existence |
| Delivery Intent Identity | YES | identifies one bounded external-delivery objective | not Notification/Attempt identity |
| Delivery Attempt Identity | YES | identifies one bounded semantic delivery try | not provider request ID |
| Provider Request / Message Identity | REFERENCE WHEN AVAILABLE | provider-local evidence identifiers | never core architecture identity automatically |
| Audience Applicability Reference | YES | binds intended audience/recipient applicability evidence | not delivery target authority |
| Tenant Applicability | YES | preserves Tenant scope | Tenant != Organization |
| Organization Applicability | WHERE RELEVANT | preserves Organization context without requiring it universally | Organization != Tenant |
| Principal Applicability | WHERE RELEVANT | binds authorized human/service recipient context | address != Principal authority |
| Cross-channel Correlation | YES VIA EXISTING IDENTITIES/RELATIONSHIPS | Notification + Intent/lineage links correlate channels | no extra universal correlation namespace required |
| Retry / Re-delivery Lineage | YES | explicit relationship among Attempts/Intents | no policy/guarantee implied |
| Historical Notification Identity | SAME NOTIFICATION IDENTITY + HISTORY CONTEXT | preserves continuity of the same semantic Notification through history | no separate ID class required |

No UUID, integer ID, database key, hash, provider ID or protocol field is frozen.

---

# 7. Notification Creation Lifecycle

The architecture distinguishes:

```text
Source Fact / Source Event / Source Condition
→ source-owned factual subject

Notification Creation Intent
→ S12 intake request associated with source provenance

Notification Creation Applicability
→ S12 determination using NT01 + NT02 evidence

Notification Created / Exists
→ established only by NT03 after applicable governed creation

Notification Lifecycle Actual-state
→ S12 / SV-R08

Notification Historical State
→ preserved occurrence/provenance history
```

Permanent:

```text
Source Event != Notification automatically
Every Event != Notification
Every Failure != Notification
Every State Transition != Notification
Every Notification != External Push
```

## 7.1 Who may produce creation intent

Any accepted source owner/authorized participant may produce an RCP-18 Creation Intent only for a source subject it can identify with sufficient provenance and under applicable governance. Producing an intent does not transfer source authority and does not guarantee creation.

S12 does not create a Universal Event Bus Authority or Universal Alert Policy Authority. The source/domain decides that an awareness creation intent is warranted under its own semantics; S12 decides whether the request is valid/applicable for S12 Notification semantics.

## 7.2 What establishes Notification existence

NT03 establishes Notification existence only when:

- Creation Intent identity/provenance is interpretable;
- source owner/correlation is preserved;
- Tenant/audience/applicability/privacy requirements are sufficiently established under NT02;
- no required semantic condition is unresolved in a way that makes creation inapplicable/indeterminate under accepted rules.

No persistence/provider/UI technical success establishes Notification existence by itself.

## 7.3 Source revision/state later changes

A later source change does not mutate the historical Notification into the new source state. The Notification keeps the source reference and applicable historical evidence. A new source condition may generate another Creation Intent/Notification if the source semantics require it. Source resolution may be correlated to the prior Notification but remains source-owned.

---

# 8. Delivery Intent / Attempt / Provider Evidence

```text
Notification
→ 0..N Delivery Intents

Delivery Intent
→ 0..N Delivery Attempts

Delivery Attempt
→ exactly one bounded semantic delivery try
```

Permanent:

```text
Notification Created != External Delivery Requested
External Delivery Requested != Delivery Attempt Created
Delivery Attempt Created != Provider Accepted
Provider Accepted != Delivery Succeeded automatically
Delivery Succeeded != Recipient Observed
Delivery Failed != Underlying Operation Failed
External Channel Unreachable != Notification Lost
```

No exactly-once, at-most-once, at-least-once, global retry count/cadence/backoff, dead-letter, fallback or latest-attempt-wins commitment exists.

---

# 9. Provider Evidence Semantics

Provider evidence must preserve:

```text
provider identity/reference
provider-local request/message identifier where available
Delivery Attempt linkage
provider observation time
provider evidence time where distinguishable
provenance
freshness
capability/semantic context
partial/unknown/conflicting qualification
normalization interpretation
```

Provider-native values are evidence, not the core state machine.

```text
Provider Accepted
→ evidence that the provider accepted a bounded provider request
→ not universal proof of terminal Delivery Success

Provider Success
→ provider-local evidence
→ NT06 interprets under declared channel capability semantics
→ NT05 owns final Product Delivery Attempt state

Provider Failed
→ evidence about provider request/attempt
→ not Notification failure
→ not underlying source operation failure

Missing Receipt
→ not definite failure

Conflicting Provider Evidence
→ CONFLICTING / INDETERMINATE until governed interpretation/reconciliation
→ latest timestamp does not automatically win
```

Provider replacement is compatible when RCP-18 channel-neutral meanings, history, identity relationships and failure semantics remain preserved.

---

# 10. Projected / Observed / Read / Acknowledged / Resolved / Approved

These are not a single lifecycle ladder.

```text
Projected / Visible
→ a presentation/projection fact
→ WB-R01 owns its projection/session facts

Observed
→ evidence that the intended recipient/principal actually observed the Notification under an admissible semantic context

Read
→ evidence that the Notification was read under the applicable interaction semantics

Acknowledged
→ explicit awareness acknowledgement evidence
→ no automatic source/business/policy side effect

Resolved
→ source-domain/source-condition semantic fact where that concept exists
→ originating source owner

Approved
→ policy/business/Human Task/governance concept where applicable
→ never implied by Notification acknowledgement
```

Permanent:

```text
Projected != Observed
Observed != Read automatically
Read != Acknowledged automatically
Acknowledged != Resolved
Acknowledged != Policy Approved
Read != Source Condition Resolved
Delivery Success != User Observed
```

This Batch intentionally does not freeze a single read/ack ordered state machine, auto-transition rule, retention rule, monotonicity rule or side effect. The stable compatibility commitment is the non-collapse and provenance-bearing interpretation of each dimension.

---

# 11. Notification vs Human Task

The accepted product distinction remains normative:

```text
Human Task Inbox
→ What needs my action?

Notification / Awareness
→ What happened that I should know about?
```

```text
Needs Human Action != Needs Human Awareness
Human Task Inbox != Notification Center
Notification != Human Task automatically
Human Response != Notification Acknowledgement
Notification Acknowledgement != Human Task Response
```

A Notification may carry a governed correlation/reference to a Human Task only where an upstream source establishes the relationship. It cannot absorb Human Task identity, assignment, response applicability, source wait/resume lifecycle or S11/SV-R07 ownership.

---

# 12. Tenant / Audience / Privacy / Redaction

S12 is Tenant-aware and Principal-aware; Organization context is preserved where relevant.

External delivery requires a disclosure decision/context that preserves:

```text
Tenant applicability
Organization applicability where relevant
Principal / intended audience applicability
Policy / authorization evidence
Trust / security evidence
source sensitivity provenance
privacy classification/context
redaction/minimization requirements
channel capability context
Secret Reference separation
```

Permanent:

```text
Provider can technically send != provider may receive arbitrary data
Recipient address exists != delivery authorized
Notification exists != every Principal may discover it
Notification projection != authorization grant
Delivery target != semantic audience authority
```

Attempt-time delivery must re-establish sufficient applicable authorization/privacy/disclosure evidence rather than assuming historical creation permission automatically authorizes later external disclosure. This is an applicability rule, not a universal fail-open/fail-closed policy.

---

# 13. Channel-neutral Core and Target Directions

Core semantics are independent from Feishu, WeCom and SMS.

```text
Core Notification Semantics
!= Feishu Semantics
!= WeCom Semantics
!= SMS Semantics
```

The architecture supports:

- channel capability semantics;
- channel-class/category references;
- channel applicability;
- delivery-target applicability;
- provider-evidence normalization;
- unsupported/unavailable channel semantics;
- provider replacement.

It does not select Feishu/WeCom/SMS APIs, SDKs, webhooks, callback schemas, SMS vendor/gateway/protocol or provider-specific retry/authentication algorithms.

---

# 14. Offline / Private / Failure / Recovery

Core Notification lifecycle is correct with zero usable public external channels.

A Notification may exist while a channel is:

```text
UNAVAILABLE
UNREACHABLE
UNSUPPORTED
FAILED
PENDING
INDETERMINATE
```

Other applicable qualification semantics include:

```text
UNKNOWN
STALE
PARTIAL
CONFLICTING
RECONCILIATION_PENDING
RECOVERING
```

Permanent:

```text
Offline != Authority Transfer
External Channel unavailable != Notification Lost
Reconnect != Reconciled
Retry after reconnect != Retroactive Authorization
Replay != proof of historical permission
Local possession != Source Authority
Latest timestamp != conflict winner
```

No public SaaS channel, public notification hub or external provider is a core-correctness dependency.

---

# 15. Configuration / Secrets

```text
Managed Desired Configuration
→ S9

S12-specific configuration item meaning
→ S12 owning responsibility where genuinely S12-specific

Applied S12 runtime evidence
→ S12 / SV-R08 applicable partition

Observed
→ derived projection
```

```text
Desired != Distributed != Applied != Observed
Configuration != Secret Material
Secret Reference != Secret Material
Provider Credential != Notification Semantic State
Delivery Credential != Authority
```

S12 may consume Secret References and authorized runtime secret material through accepted boundaries but does not select a secret store, KMS, credential database, token layout or encryption provider.

---

# 16. RCP-18 Full Design-semantic Closure

```text
RCP-18 Notification / Delivery
→ CLOSED AT CURRENT DESIGN-SEMANTIC LEVEL BY THIS CANDIDATE
→ AWAITING GLOBAL ACCEPTANCE
```

No REST/RPC/gRPC/WebSocket, DTO, JSON/Protobuf schema, queue, broker, topic, table or provider protocol is frozen.

## 16.1 Stable semantic subject set

RCP-18 carries, where applicable:

```text
Source Owner Reference
Source Correlation Reference
Source semantic/revision/provenance context
Notification Creation Intent Identity
Notification Identity
Notification Occurrence Identity / history context
Tenant applicability
Organization applicability where relevant
Principal / intended audience applicability
Creation applicability evidence
Notification existence/lifecycle/history
privacy/redaction/disclosure context
Delivery Intent Identity
Delivery Intent objective/channel-class/target applicability
Delivery Attempt Identity
Intent↔Attempt relationship
retry-of / re-delivery-of / explicit replacement lineage
provider evidence provenance
provider request/message references
Delivery Attempt semantic outcome/uncertainty
Projected/Observed/Read/Acknowledged evidence where applicable
source Resolved correlation where applicable
configuration applicability
history/temporal/freshness/correlation/provenance
compatibility/migration/conformance qualification
private/offline/recovery qualification
```

## 16.2 Source-owner obligations

A source owner producing Notification creation intent MUST, where applicable:

- preserve source owner identity;
- identify the source subject/event/condition sufficiently for governed correlation;
- preserve source revision/occurrence/provenance/temporal context needed for interpretation;
- preserve Tenant/Organization and sensitivity context needed by S12;
- never treat Notification creation as transfer of source authority;
- expose later source-state/resolution evidence only as source-owned evidence, not by mutating Notification history.

## 16.3 Producer obligations — S12/SV-R08

S12 MUST:

- establish Notification existence only through governed creation applicability;
- assign/preserve representation-neutral Notification identity/history;
- preserve source owner/correlation;
- enforce Tenant/audience/authorization/privacy/redaction applicability;
- keep Notification separate from Delivery Intent/Attempt;
- create each Delivery Attempt as a distinct semantic try with explicit lineage;
- interpret provider evidence without provider authority escalation;
- preserve uncertainty/failure/recovery/history;
- never infer source resolution, user observation or Policy approval from delivery success;
- preserve compatibility/migration/conformance and private/offline correctness.

## 16.4 Consumer obligations

Consumers including WB-R01, future SDK surfaces and source/domain consumers MUST:

- preserve Notification/source identity separation;
- apply Tenant/Principal/authorization/privacy rules before discovery/presentation;
- display/consume freshness/provenance/uncertainty rather than silently coercing state;
- never treat projection/read/ack/delivery as current source truth;
- never treat provider identifiers as Product identity;
- preserve history/lineage and unsupported/incompatible conditions;
- return interaction evidence with sufficient Notification/Principal/correlation context where such evidence is produced.

## 16.5 External-provider obligations

A provider integration participates only as an evidence-producing delivery realization. It must be replaceable under the channel-neutral contract and must not receive data beyond the authorized disclosure boundary.

## 16.6 Why RCP-18 creates no source-fact Authority

RCP-18 carries source references/provenance but never canonicalizes the source assertion. Source state changes remain source-owned and are correlated rather than rewritten into Notification state.

## 16.7 Why RCP-18 creates no provider Authority

Provider-local IDs/status/receipts are interpreted as evidence by NT06; final Delivery Attempt Actual-state remains NT05/SV-R08. Provider reachability or success cannot establish Notification/source/Policy/Tenant/Principal truth.

---

# 17. Future S13 Contribution without S13 Preemption

S12 may expose projection-eligible contribution semantics consisting of:

```text
Notification Identity
Notification resource/type semantics
Tenant applicability
Organization applicability where relevant
Principal/audience applicability metadata
source-owner/source-correlation reference
history/provenance
applicable freshness/uncertainty qualification
non-sensitive projection metadata subject to authorization/redaction
```

Permanent:

```text
S13 Projection != Notification Actual-state Owner
Discovery Index != Notification SoT
Discovery Result != Source Fact
```

This Candidate does not define S13 internal modules, indexing, ranking, query, search engine, schema, storage or UX.

---

# 18. Shared Foundation Consumption

S12 consumes only accepted Shared Foundation semantics through:

```text
Product Component Internal Responsibility
→ Stable Entry
→ Foundation Contract
→ Foundation Module
→ Provider Family where provider-bearing
→ replaceable realization
```

Applicable authority-neutral mechanics include accepted configuration loading, diagnostics/logging, telemetry/health, temporal/freshness, correlation/provenance, representation/serialization, network-client mechanics, technical status/uncertainty, governed context propagation, Secret Reference/redaction and compatibility/conformance.

```text
Foundation != S12 Authority
Provider Family != Notification Authority
Network Client != Delivery Authority
Storage Placement != Actual-state Ownership
Provider Success != SV-R08 Semantic Success automatically
```

No missing mandatory Foundation semantic was found and no new Foundation capability is created.

---

# 19. Compatibility / Migration / Conformance

RCP-18 changes are classified under the accepted compatibility model.

**Compatible evolution** may add representational/provider realizations or optional evidence dimensions when Notification/Intent/Attempt identities, authority, history, Tenant/audience/privacy and failure meanings remain preserved.

**Explicit migration** is required when stored/transported Notification/Delivery evidence changes representation in a way requiring semantic reinterpretation. Migration must preserve identity lineage, source references, attempt lineage, historical provider evidence and uncertainty.

**Architecture revalidation / MDE** is required for material changes to S12/SV-R08 ownership, Human Task separation, channel-neutral core, offline/private correctness, major stable identity/history commitment, universal delivery/retry/fallback guarantee, conflict winner, privacy/Tenant/Principal boundary or provider/protocol/storage lock-in.

Conformance requires implementations/providers/consumers to preserve all RCP-18 non-collapse, identity, provenance, authorization, history, uncertainty and offline semantics. Successful API calls or schema compatibility alone do not prove semantic conformance.

---

# 20. Candidate Required Question Closure

1. **S12 internal responsibilities?** `NT01..NT08` as defined above.
2. **No God Module?** Source intake, audience/privacy, Notification state, delivery intent, attempts, provider evidence, interaction evidence and recovery are independently owned.
3. **No overfragmentation?** No channel/provider/status/UI-specific module proliferation; cross-cutting compatibility remains with subject owners.
4. **Hard dependency graph?** §5.
5. **Acyclic?** YES; topological order exists.
6. **Notification identity?** Durable representation-neutral S12 identity of one governed awareness record.
7. **Notification vs Source Fact?** Source stays source-owned; Notification is separate S12 awareness history.
8. **Creation Intent vs Exists?** Intent is request evidence; only NT03 governed creation establishes existence.
9. **Occurrence/history?** Notification Occurrence Identity records S12-owned historical lifecycle occurrences without becoming a second resource identity.
10. **Delivery Intent?** A bounded external-delivery objective for one Notification/channel-target applicability context.
11. **Delivery Attempt?** One bounded semantic delivery try under one Intent.
12. **Intent↔Attempt?** One Intent may have zero/one/multiple Attempts; every Attempt references exactly one Intent in current semantics.
13. **Multiple Attempts?** YES.
14. **Retry/re-delivery lineage?** Retry creates new Attempt under same Intent; re-delivery creates new correlated Intent; prior history preserved.
15. **Provider Request ID vs Attempt?** External evidence reference only; no automatic identity equality.
16. **Provider Message ID vs Notification?** External evidence reference only; no automatic identity equality.
17. **Provider evidence interpretation?** NT06 normalizes/provenances; NT05 remains final Attempt Actual-state owner.
18. **Provider success vs observed?** Provider result concerns delivery evidence; recipient observation is independent interaction evidence.
19. **Delivery failed vs source operation failed?** Different semantic owners/subjects; no implication.
20. **Delivered/Observed/Read/Ack/Resolved?** Independent evidence dimensions; source Resolved remains source-owned.
21. **Notification vs Human Task?** Permanent product non-collapse; governed correlation only.
22. **Tenant/Organization/Principal/audience?** NT02 applicability with S1–S4 authoritative context; Tenant required, Organization where relevant, Principal/audience authorized.
23. **Privacy/redaction external delivery?** Attempt-time disclosure applicability and minimization/redaction under source sensitivity and governance evidence.
24. **Channel-neutral Feishu/WeCom/SMS?** Channel capability semantics + replaceable provider evidence boundary; no provider API semantics in core.
25. **Channel unavailable?** Notification remains existent; intent/attempt receives explicit unavailable/unreachable/indeterminate qualification.
26. **Offline/reconnect/reconciliation?** Authority retained; reconnect != reconciled; no retroactive authorization/latest-wins.
27. **UNKNOWN/PARTIAL/FAILED/PENDING/INDETERMINATE?** First-class semantic qualifications with provenance and no silent coercion.
28. **Desired/Applied/Observed config?** S9 Desired; S12/SV-R08 applicable Applied; Observed derived.
29. **Secret Reference vs Material?** Separate; provider credential is not Notification state/authority; material custody technology not selected.
30. **RCP-18 producer obligations?** §16.3.
31. **RCP-18 consumer obligations?** §16.4.
32. **RCP-18 source-owner obligations?** §16.2.
33. **Why no source-fact Authority?** Source reference/provenance is carried, never canonicalized by S12.
34. **Why no provider Authority?** Provider produces evidence; NT05 owns Product Attempt state.
35. **Future S13?** S12 exports authorized projection-eligible metadata only; no S13 internals.
36. **Deferred to Detailed Design / Implementation?** Physical ID formats; storage/schema/ORM; REST/RPC/gRPC/WebSocket; DTO/envelope; queues/brokers/topics; retry/backoff/dead-letter/fallback algorithms; provider SDK/API/auth protocols; Feishu/WeCom/SMS concrete integration; template/rendering language; recipient/group schema; notification preference product model; exact UI; process/worker/container topology; secret store/KMS; repository/package/class layout; concrete conformance tooling.

---

# 21. Semantic Resolution Matrix

| Dimension | Resolution | Status |
|---|---|---|
| Identity / Namespace | Notification/Occurrence/Creation Intent/Delivery Intent/Attempt/provider refs separated; physical IDs deferred by name | CLOSED |
| Revision / Evolution | history/provenance/semantic compatibility preserved; no current-state rewrite | CLOSED |
| Authority | source owner, S12/SV-R08, WB projection, provider evidence roles explicit | CLOSED |
| Semantic Ownership | NT01..NT08 responsibilities explicit | CLOSED |
| Source of Truth | source facts remain source-owned; persistence/provider/index do not become SoT | CLOSED |
| Actual-state Ownership | NT03 Notification + NT05 Attempt under SV-R08; one final owner per assertion | CLOSED |
| State / Lifecycle | creation/existence, intent/attempt, interaction/source resolution non-collapse | CLOSED |
| Temporal Semantics | occurrence/observation/freshness/history preserved; no latest-wins | CLOSED |
| Failure / Unknown / Indeterminate | explicit qualification vocabulary and provenance | CLOSED |
| Tenant | mandatory applicability | CLOSED |
| Organization | preserved where relevant and non-collapsed with Tenant | CLOSED |
| Principal | audience/recipient applicability preserved | CLOSED |
| Authentication | consumed from accepted IAM context; not S12 authority | CLOSED |
| Authorization / Policy | NT02 consumes authoritative decisions; no Policy authority transfer | CLOSED |
| Security / Trust | inherited S4 context; provider/transport success not Trust | CLOSED |
| Data / Privacy / Trust | sensitivity provenance, disclosure/redaction boundary explicit | CLOSED |
| Serialization / Representation | semantic-before-representation; physical schema deferred by name | CLOSED / NAMED DOWNSTREAM |
| Configuration | S9 Desired, S12 applicable Applied, derived Observed | CLOSED |
| Secret Reference / Material | strict separation; store/provider not selected | CLOSED / NAMED DOWNSTREAM |
| Offline / Degraded | core Notification works without public channels | CLOSED |
| Recovery / Reconciliation | NT08; no authority transfer/conflict winner | CLOSED |
| Compatibility | stable identity/non-collapse/provider replaceability rules | CLOSED |
| Migration | history/identity/provenance preserving semantic migration obligations | CLOSED |
| Conformance | producer/consumer/provider obligations explicit | CLOSED |
| Cross-boundary Dependency | source→S12→provider/WB topology explicit | CLOSED |
| Invariant | source/Notification/Human Task/provider/Projection non-collapse | CLOSED |
| Decision Traceability | inherited Owner/Z2/Z3/RRA + Batch-6 DAD evidence | CLOSED |
| Revalidation Trigger | MDE/architecture triggers explicit | CLOSED |

```text
Missing/Ambiguous Normative Dimension
→ 0

Implementation-defined Escape
→ 0

Actual-state Ownership Ambiguity
→ 0

Source-fact Ownership Ambiguity
→ 0
```

---

# 22. Explicit Non-goals / Forbidden Interpretation

This Candidate does not design or select:

```text
S11 internals
S13 internals
ns_runtime/ns_node/ns_agent/ns_web Internal Design
full RCP-16
full RCP-17
RCP-21
System-level SDK Detailed Design
Feishu API/SDK/webhook
WeCom API/SDK/callback
SMS provider/gateway/protocol
fixed provider set
provider authentication protocol
queue/broker/topic/dead-letter
retry/backoff/count/fallback engine
exactly-once/at-most-once/at-least-once guarantee
template language
recipient/group schema
notification preference product model
REST/RPC/gRPC/WebSocket
DTO/JSON/Protobuf/message envelope
database/table/ORM/storage schema
Django App/Python package/class
service/process/worker/container/deployment topology
Secret store/KMS/credential database
global conflict winner
global fail-open/fail-closed policy
Implementation Planning/IWP/Coding
```

---

# 23. DAD / MDE Candidate Result

Material decisions are recorded separately in:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_6_dad_evidence_0.0.1.md`

Candidate DAD range:

```text
CID-SV-B6-DAD-001..019
```

```text
New Owner MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

No DAD changes the Owner-decided Notification capability, Human Task separation, S12/SV-R08 Actual-state ownership, channel-neutral/offline commitments, Tenant/Principal/privacy boundary or Feishu/WeCom/SMS target intent.

---

# 24. Candidate Status

Subject to companion DAD/Audit/Handoff persistence and final Git verification:

```text
NGRP-001
Component Internal Design
/ ns_server
/ Batch 6
/ S12

→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This Candidate does not claim Global Acceptance, advance GAC Epoch, modify Global State/Working State/Ledger/Decision Registry, declare ns_server Internal Design Exhaustion/global closure, authorize Batch 7, enter S11/S13, enter another Product Component, enter SDK Detailed Design, Design-to-Implementation Readiness, Implementation Planning, IWP or Coding.
