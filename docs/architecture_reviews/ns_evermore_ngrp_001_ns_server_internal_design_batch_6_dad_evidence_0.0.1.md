# NGRP-001 — Component Internal Design / ns_server / Batch 6 DAD Evidence

## Authority Metadata

- Program: `NGRP-001`
- Phase: `Component Internal Design / ns_server / Batch 6`
- Authorized Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_6 / GOVERNED_NOTIFICATION_AND_EXTERNAL_DELIVERY_LIFECYCLE_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Recovered Entry HEAD: `0f38d0123824025d7517e1e29ebac406fd675edc`
- Candidate Commit: `5e7c924c6043e4d7cf44a11af15a4d7472a2f062`
- Authorized Boundary: `S12`
- Inherited Runtime Role: `SV-R08`
- DAD Range: `CID-SV-B6-DAD-001..019`
- New Owner MDE: `0`
- Global Acceptance: `NOT CLAIMED`

These DADs are delegated architecture decisions within the exact GAC-EPOCH-0060 authorization. They refine S12/SV-R08 semantics without changing accepted Product capability, Authority/SoT/Actual-state ownership, Human Task separation, channel-neutral external-delivery commitment, offline/private correctness or target integration directions.

---

# Decision Classification Baseline

The following are inherited and are not reopened:

```text
Unified Governed Notification Capability
→ REQUIRED

Channel-neutral Core Notification Semantics
→ REQUIRED

Pluggable External Notification Delivery
→ REQUIRED

External Platform Push
→ REQUIRED AS PRODUCT CAPABILITY

Feishu / WeCom / SMS
→ representative / initial target directions

Public SaaS dependency for core correctness
→ PROHIBITED

S12 Product Authority over source condition
→ NONE

SV-R08 final Actual-state owner
→ Notification lifecycle/history
→ applicable Delivery Attempt facts

Human Task
!= Notification
```

MDE escalation would be required for any material change to those inherited facts, a major stable physical identity namespace, a universal delivery/retry/fallback guarantee, material conflict-winner/fail policy, provider/protocol/storage lock-in, or high-migration compatibility commitment. None is selected below.

---

# CID-SV-B6-DAD-001 — Eight-responsibility S12 internal decomposition

**Decision**

S12 is decomposed into:

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

**Reason**

The decomposition separates source intake, authorization/privacy, Notification Actual-state, external-delivery intent, delivery Actual-state, provider evidence, awareness interaction and recovery. These concerns have materially different authority/evidence relationships and must not collapse into a generic Notification Manager.

**Alternatives avoided**

- one `Notification Core` God responsibility owning all subjects;
- provider/channel-specific modules for Feishu/WeCom/SMS;
- one module per lifecycle flag/status;
- implementation-shaped worker/queue/adapter/database decomposition.

**Constraint traceability**

Preserves Z3 S12 boundary, SV-R08, `Z2-MDE-014`, channel-neutral Owner decision, NSE-004/009/012/017 and GAC-EPOCH-0060.

**Authority impact**

No new Authority/SoT/Actual-state owner is created. NT03/NT05 refine already accepted SV-R08 ownership only.

**Offline/private impact**

Core responsibilities are provider-independent and can operate with zero usable public channel.

**Compatibility impact**

Internal responsibility meanings are semantic; physical realization may change without architecture change when semantics remain conformant.

**Downstream implications**

Detailed design must map implementation units to these responsibilities without merging authorities or requiring one-to-one physical mapping.

**Non-implications**

No Django App, package, class, service, process, queue, table or provider adapter topology is selected.

---

# CID-SV-B6-DAD-002 — Notification Identity is durable and representation-neutral

**Decision**

`Notification Identity` is a durable S12 semantic identity for one governed awareness record and remains distinct from source identity, Creation Intent, Delivery Intent, Delivery Attempt, provider IDs, correlation IDs and persistence keys.

**Reason**

Stable in-product history and external-delivery correlation require semantic identity independent of representation/provider/storage.

**Alternatives avoided**

- reuse source event/fact ID as Notification ID automatically;
- provider message ID as Notification ID;
- database primary key or transport token as architecture identity.

**Constraint traceability**

NSE-009 representation independence; Owner decision explicitly identified notification identity/history as compatibility-sensitive; RCP-18 authorization.

**Authority impact**

Identity creation does not create source-fact Authority.

**Offline/private impact**

Notification identity remains meaningful without external providers.

**Compatibility impact**

Identity continuity is stable; physical ID formats remain replaceable.

**Downstream implications**

Implementations must preserve semantic identity across storage/provider migration.

**Non-implications**

No UUID/integer/hash/ULID/database key is selected.

---

# CID-SV-B6-DAD-003 — Notification Occurrence Identity is historical-occurrence identity, not a second resource identity

**Decision**

A material S12-owned Notification lifecycle/history occurrence has a distinct `Notification Occurrence Identity` correlated to the durable Notification Identity. Historical Notification reference uses the same Notification Identity plus applicable occurrence/revision/temporal context; no separate Historical Notification resource namespace is created.

**Reason**

Historical explainability requires individual occurrence identity without multiplying canonical Notification resource identities.

**Alternatives avoided**

- treating every historical occurrence as a new Notification;
- storing history only as mutable current state;
- creating a separate `HistoricalNotification` authority/SoT.

**Constraint traceability**

Project temporal/history rules, no current-state rewrite, RCP-18 occurrence/history closure.

**Authority impact**

No source or provider authority change.

**Offline/private impact**

Historical occurrences remain interpretable locally/private.

**Compatibility impact**

Occurrence semantics are stable; physical event-log technology is not.

**Downstream implications**

Detailed design must preserve occurrence provenance/history if representation changes.

**Non-implications**

No event sourcing or immutable database technology mandate.

---

# CID-SV-B6-DAD-004 — Source Owner / Source Correlation never collapse into Notification identity or authority

**Decision**

RCP-18 requires explicit Source Owner Reference and source correlation/provenance. Source correlation is a relationship, not identity equality. S12 never canonicalizes the source assertion.

**Reason**

A Notification is an awareness record about a source-owned condition and cannot become the current source truth by correlation or persistence.

**Alternatives avoided**

- Notification store as source SoT;
- source event ID automatically becoming Notification identity;
- current Notification state used to infer current source condition.

**Constraint traceability**

NSE-011, Z3 S12 boundary, Owner decision, Z2-MDE-014.

**Authority impact**

Source authority remains unchanged.

**Offline/private impact**

Local Notification history may exist even when source is unreachable; unreachable does not transfer authority.

**Compatibility impact**

Source identity/reference mapping must remain historically interpretable.

**Downstream implications**

Consumers must resolve current source state from the source owner, not Notification history.

**Non-implications**

No universal source registry/event bus is created.

---

# CID-SV-B6-DAD-005 — Creation Intent / Creation Applicability / Notification Exists are distinct

**Decision**

The creation lifecycle is:

```text
source-owned fact/event/condition
→ Notification Creation Intent
→ S12 Creation Applicability
→ Notification Created / Exists
```

Creation Intent identity is required. Source occurrence does not automatically create a Notification; S12 existence is established only after governed applicability.

**Reason**

This prevents every event/failure/state transition from becoming a Notification and prevents provider/storage/UI mechanics from creating canonical Notification state.

**Alternatives avoided**

- every source event automatically materializes a Notification;
- provider send request creates Notification existence;
- S12 becomes Universal Alert Policy Authority.

**Constraint traceability**

Owner decision non-implications; GAC-EPOCH-0060 creation-lifecycle authorization.

**Authority impact**

Source domain remains responsible for deciding/expressing awareness intent under source semantics; S12 decides only S12-level applicability/existence.

**Offline/private impact**

Creation can remain correct without an external delivery channel.

**Compatibility impact**

Creation-intent and Notification identity histories remain separately migratable.

**Downstream implications**

Duplicate/replay handling must preserve Creation Intent identity without promising exactly-once creation.

**Non-implications**

No idempotency protocol, event envelope, broker or alert policy language.

---

# CID-SV-B6-DAD-006 — Audience applicability and disclosure are an S12 decision boundary consuming S1–S4 authority

**Decision**

S12 has a dedicated audience/applicability/disclosure responsibility that evaluates Tenant, Organization where relevant, Principal/intended audience, Policy, Trust, source sensitivity, privacy/redaction and external-disclosure context. It owns only S12 applicability evidence, not upstream IAM/Policy/Trust authority.

**Reason**

Notification existence and technical recipient address must never imply universal visibility or permission to disclose externally.

**Alternatives avoided**

- provider address implies authorization;
- Notification existence implies visibility to all Principals;
- provider adapter decides privacy policy independently;
- audience semantics hidden in recipient schema.

**Constraint traceability**

Owner notification decision §7.5, accepted S1–S4 governance baseline, NSE-001/002/004/011.

**Authority impact**

No IAM/Policy/Trust Authority transfer.

**Offline/private impact**

Unavailable current evidence remains explicit; no generic fail-open/fail-closed policy is added.

**Compatibility impact**

Audience/disclosure history is compatibility-sensitive and must preserve historical applicability.

**Downstream implications**

External delivery must consume only authorized/redacted information.

**Non-implications**

No recipient directory, group model, address schema or policy engine.

---

# CID-SV-B6-DAD-007 — Notification lifecycle is multi-dimensional history, not one mandatory ordered enum

**Decision**

S12 Notification lifecycle is modeled as independently attributable dimensions: existence/history, audience applicability, external delivery histories and awareness-interaction evidence. Source resolution remains source-owned. No universal ordered Notification state-machine progression is established.

**Reason**

`Projected`, `Observed`, `Read`, `Acknowledged`, external delivery and source resolution have different evidence owners and do not form one universally valid sequence.

**Alternatives avoided**

- CREATED→DELIVERED→READ→ACKNOWLEDGED→RESOLVED mandatory ladder;
- latest state overwrites history;
- external provider enum imported as Notification lifecycle.

**Constraint traceability**

GAC-EPOCH-0060 non-collapse requirements and Owner decision named deferral for exact read/ack state machine.

**Authority impact**

NT03 owns Notification existence/history only; no source-resolution authority is acquired.

**Offline/private impact**

Notification history remains meaningful with no external delivery/interaction evidence.

**Compatibility impact**

Stable commitment is non-collapse/provenance, not a fixed enum. Future dimensions can evolve under compatibility rules.

**Downstream implications**

Implementations may choose representations but cannot infer invalid transitions/equivalences.

**Non-implications**

No retention/deletion/archive policy or UI unread-counter semantics.

---

# CID-SV-B6-DAD-008 — Delivery Intent is a distinct bounded external-delivery objective

**Decision**

A Notification may have zero/one/multiple Delivery Intents. Each Delivery Intent has its own identity and represents one bounded delivery objective under one channel-class/target-applicability context. External delivery requested does not imply an Attempt exists.

**Reason**

This preserves Notification existence independent of delivery and provides stable correlation for channel/provider replacement and re-delivery.

**Alternatives avoided**

- one implicit delivery flag on Notification;
- provider request as Delivery Intent;
- one mutable intent silently switching channels/targets.

**Constraint traceability**

RCP-18 and Owner channel-neutral/pluggable delivery baseline.

**Authority impact**

No provider or audience authority transfer.

**Offline/private impact**

Intent may exist as pending/unavailable/unsupported/indeterminate while channel is offline.

**Compatibility impact**

Intent identity/objective remains stable across provider implementations.

**Downstream implications**

Cross-channel or materially changed target re-delivery uses a new correlated Intent.

**Non-implications**

No fixed channel set, routing/fallback tree or target schema.

---

# CID-SV-B6-DAD-009 — Delivery Attempt is one bounded semantic delivery try and SV-R08 owns its Actual-state

**Decision**

A Delivery Intent may have zero/one/multiple Delivery Attempts. Each Attempt has a distinct identity and represents exactly one bounded semantic delivery try. NT05/SV-R08 is the final Product Actual-state owner for that Attempt.

**Reason**

Provider requests/retries and delivery histories require explicit attempt identity while preserving one-final-owner runtime topology.

**Alternatives avoided**

- provider request ID equals Attempt identity automatically;
- provider owns Product attempt state;
- one mutable delivery status replaces attempt history.

**Constraint traceability**

Z2-MDE-014, RRA SV-R08, RCP-18 authorization.

**Authority impact**

Refines accepted SV-R08 ownership only; provider remains evidence source.

**Offline/private impact**

Attempt may be pending/unreachable/indeterminate without affecting Notification existence.

**Compatibility impact**

Attempt identity/lineage must survive provider/storage migration.

**Downstream implications**

Physical provider requests may be one-to-one or otherwise related according to implementation/provider semantics, but identity equality is not architectural.

**Non-implications**

No worker/process/queue/provider protocol.

---

# CID-SV-B6-DAD-010 — Retry and re-delivery create new historical identities; no universal delivery guarantee

**Decision**

```text
retry
→ new Delivery Attempt
→ same Delivery Intent
→ explicit retry-of lineage

re-delivery with renewed/changed objective/channel/target applicability
→ new Delivery Intent
→ explicit re-delivery-of relationship where applicable
→ new Attempts belong to new Intent
```

Prior history is never mutated. Optional explicit replacement/supersession is relation evidence only; later timestamps never imply supersession.

**Reason**

This gives deterministic historical interpretation without selecting execution guarantees or retry policy.

**Alternatives avoided**

- reuse same Attempt identity for retry;
- mutate failed attempt into success after retry;
- latest-attempt-wins;
- global exactly-once/at-most-once/at-least-once semantics.

**Constraint traceability**

GAC-EPOCH-0060 explicit retry/re-delivery non-preemption; Batch-5 accepted identity/history precedent without importing its runtime policy.

**Authority impact**

No owner change.

**Offline/private impact**

Retry after reconnect remains newly governed; it is not retroactive authorization.

**Compatibility impact**

Lineage is stable; count/cadence/backoff policy remains replaceable/downstream.

**Downstream implications**

Any future global guarantee/fallback policy requires MDE/GAC re-entry.

**Non-implications**

No retry count/cadence/backoff/dead-letter/fallback policy.

---

# CID-SV-B6-DAD-011 — Provider evidence is normalized evidence; provider-native state never becomes core state machine

**Decision**

NT06 preserves provider provenance, observation/freshness, provider request/message references and provider capability context, then produces channel-neutral evidence for NT05. `Provider Accepted`/`Provider Success`/`Provider Failed` remain provider-local evidence meanings until S12 interpretation.

**Reason**

Provider replaceability and channel-neutral semantics require a normalization boundary and explicit uncertainty.

**Alternatives avoided**

- direct mapping of provider enum into core Notification state;
- provider success as Product Authority;
- missing receipt as definite failure;
- latest provider callback wins.

**Constraint traceability**

NSE-012 provider replaceability; Owner decision; RRA SV-R08; GAC-EPOCH-0060 Provider Evidence requirements.

**Authority impact**

NT05 remains final Delivery Attempt owner; provider gains no Product Authority.

**Offline/private impact**

No provider evidence is required for Notification existence.

**Compatibility impact**

Provider-specific historical IDs/statuses remain provenance-bearing references across provider replacement.

**Downstream implications**

Detailed provider adapters must conform to channel-neutral evidence semantics.

**Non-implications**

No Feishu/WeCom/SMS callback/API/SDK/auth protocol.

---

# CID-SV-B6-DAD-012 — Product Delivery Success requires sufficient admissible evidence and never implies recipient observation

**Decision**

`Delivery Succeeded` is an NT05/SV-R08 semantic outcome only when admissible evidence is sufficient for the bounded Delivery Intent/Attempt objective under declared channel capability semantics. `Provider Accepted` alone is not universally sufficient. `Delivery Succeeded != Recipient Observed` permanently.

**Reason**

Different channels expose different evidence capability; equating technical acceptance with observation would collapse semantics and provider authority.

**Alternatives avoided**

- provider accepted = delivery succeeded globally;
- provider message ID = observed;
- no receipt = failure;
- delivered = read/ack.

**Constraint traceability**

Owner decision and GAC-EPOCH-0060 delivery/provider non-collapse.

**Authority impact**

Attempt outcome remains S12; observation remains separate evidence.

**Offline/private impact**

Insufficient evidence becomes `INDETERMINATE`/other qualified condition, not fabricated success/failure.

**Compatibility impact**

Channel/provider capability changes cannot silently reinterpret old attempts.

**Downstream implications**

Provider adapters must declare/map evidentiary capability without changing Product semantics.

**Non-implications**

No fixed receipt protocol or evidence threshold algorithm.

---

# CID-SV-B6-DAD-013 — Projected / Observed / Read / Acknowledged / Resolved / Approved are independent semantic dimensions

**Decision**

```text
Projected != Observed
Observed != Read automatically
Read != Acknowledged automatically
Acknowledged != Resolved
Acknowledged != Policy Approved
Read != Source Condition Resolved
Delivery Success != User Observed
```

WB-R01 owns projection/session facts. NT07 interprets admissible Notification awareness-interaction evidence. `Resolved` remains source-domain/source-condition semantics; `Approved` remains applicable policy/business/Human Task/governance semantics.

**Reason**

A single ordered state machine would falsely merge presentation, human cognition/action and underlying source truth.

**Alternatives avoided**

- auto-mark read on projection;
- auto-ack on read;
- acknowledgement closes source problem;
- acknowledgement grants approval.

**Constraint traceability**

Owner decision, Human Task decision, GAC-EPOCH-0060 §13.

**Authority impact**

No WB/source/Policy/Human Task authority transfer.

**Offline/private impact**

Delayed interaction evidence may reconcile later without retroactive permission.

**Compatibility impact**

Non-collapse is stable; no universal exact read/ack state machine is frozen.

**Downstream implications**

UI/provider interactions must report evidence without inventing source resolution/approval.

**Non-implications**

No unread-counter, auto-read, UI event or acknowledgment side-effect policy.

---

# CID-SV-B6-DAD-014 — Human Task and Notification remain separately governed resources/lifecycles

**Decision**

S12 may carry a governed reference/correlation to a Human Task but cannot absorb Human Task identity, assignment, response applicability, source wait/resume state or S11/SV-R07 ownership.

**Reason**

The Owner selected separate product questions: `needs my action` versus `happened that I should know`.

**Alternatives avoided**

- universal attention-center resource;
- Human Task automatically created for each Notification;
- Notification acknowledgement treated as Human Task response.

**Constraint traceability**

Persisted Human Task and Notification Owner capability decisions; GAC-EPOCH-0060 explicit non-collapse.

**Authority impact**

No S11/Automation/Agent/WB ownership change.

**Offline/private impact**

Each lifecycle reconciles under its own owner; one being unavailable does not rewrite the other.

**Compatibility impact**

Cross-resource correlation remains reference-based and evolution-safe.

**Downstream implications**

Future S11/Agent/Web design may consume correlation but cannot rely on merged state.

**Non-implications**

No S11 internals, assignment, task lifecycle or HITL response routing design.

---

# CID-SV-B6-DAD-015 — Channel-neutral core uses channel capability/applicability semantics, not provider semantics

**Decision**

RCP-18 core delivery expresses channel class/capability/applicability and target applicability independently of provider-specific API/state. Feishu, WeCom and SMS remain target directions realized behind replaceable channel/provider boundaries.

**Reason**

This is the Owner-selected product commitment and minimizes migration/provider lock-in.

**Alternatives avoided**

- one mandatory provider/channel model;
- Feishu/WeCom/SMS fields in core semantic identity;
- public SaaS as correctness dependency.

**Constraint traceability**

Owner Option B, NSE-004/012, GAC-EPOCH-0060.

**Authority impact**

Provider/channel gains no Product Authority.

**Offline/private impact**

Core Notification works without external connectivity.

**Compatibility impact**

Provider replacement is compatible when stable channel-neutral semantics are preserved.

**Downstream implications**

Concrete provider adapters are downstream realization choices.

**Non-implications**

No API, SDK, webhook, SMS vendor, gateway, auth, template or target schema.

---

# CID-SV-B6-DAD-016 — Offline/failure/recovery preserves S12 ownership and uncertainty; no conflict winner

**Decision**

S12 preserves explicit applicable conditions including:

```text
UNKNOWN
UNAVAILABLE
UNREACHABLE
UNSUPPORTED
STALE
PARTIAL
FAILED
PENDING
INDETERMINATE
CONFLICTING
RECONCILIATION_PENDING
RECOVERING
```

and permanent rules:

```text
External Channel unavailable != Notification Lost
Reconnect != Reconciled
Retry after reconnect != Retroactive Authorization
Replay != historical permission proof
Latest Timestamp != winner
Local possession != Source Authority
```

**Reason**

Offline/private correctness and provider failures must never force fabricated success/failure or authority transfer.

**Alternatives avoided**

- local wins;
- central wins;
- latest provider callback wins;
- generic fail-open/fail-closed;
- reconnect automatically retries/authorizes.

**Constraint traceability**

NSE-004, Z2-DAD-029/035/036, Z2-MDE-014, GAC-EPOCH-0060.

**Authority impact**

No owner changes.

**Offline/private impact**

Core lifecycle remains correct in isolated deployment.

**Compatibility impact**

Failure/uncertainty meanings are stable and cannot be silently coerced by provider replacement.

**Downstream implications**

Recovery mechanisms must preserve provenance/history and return evidence to NT03/NT05 owners.

**Non-implications**

No replay engine, reconciliation algorithm, durable queue or retry scheduler.

---

# CID-SV-B6-DAD-017 — Desired / Applied / Observed configuration and Secret Reference remain separated

**Decision**

```text
Managed Desired Configuration
→ S9

S12-specific item meaning
→ applicable S12 responsibility

Applied S12 runtime evidence
→ S12/SV-R08 where applicable

Observed
→ derived
```

```text
Desired != Distributed != Applied != Observed
Configuration != Secret Material
Secret Reference != Secret Material
Provider Credential != Notification Semantic State
Delivery Credential != Authority
```

**Reason**

Delivery channel/provider configuration and credentials must not rewrite accepted config/secret/authority topology.

**Alternatives avoided**

- provider credential stored as Notification state;
- delivery adapter owns desired configuration;
- observed provider config treated as canonical desired state.

**Constraint traceability**

Z2-MDE-016, Batch-1 RCP-19, GAC-EPOCH-0060.

**Authority impact**

No S9/config item authority changes.

**Offline/private impact**

Desired state may exist while applied/channel state is unavailable/stale/partial.

**Compatibility impact**

Config semantics/version history remain explicit; secret store replacement is non-semantic if contracts remain preserved.

**Downstream implications**

Detailed design must consume accepted Secret Reference/redaction paths and keep material out of ordinary history/diagnostics.

**Non-implications**

No KMS/Vault/secret DB/token format/encryption provider.

---

# CID-SV-B6-DAD-018 — RCP-18 full closure uses stable producer/consumer/source-owner obligations without wire/schema lock-in

**Decision**

RCP-18 is closed at current design-semantic level with stable obligations for source owner/correlation, Notification identity/occurrence/lifecycle/history, Tenant/Organization/Principal/audience, creation intent/applicability/existence, Delivery Intent/Attempt identities and lineage, provider evidence interpretation, channel neutrality, awareness interaction non-collapse, privacy/redaction, config/secret boundaries, offline/failure/history/compatibility/migration/conformance and producer/consumer/source-owner behavior.

**Reason**

GAC-EPOCH-0060 explicitly authorizes full RCP-18 closure and all controlling ownership/product choices are already accepted.

**Alternatives avoided**

- leave architecture-critical semantics to implementation;
- freeze REST/RPC/message/database/provider representation;
- create universal source/provider authority.

**Constraint traceability**

NSE-009/012/017, RRA RCP-18 pressure, remaining-pressure assessment, GAC-EPOCH-0060.

**Authority impact**

Source owner remains source owner; NT03/NT05 refine SV-R08; provider/WB remain evidence/projection participants.

**Offline/private impact**

Contract is valid with no public provider.

**Compatibility impact**

Semantic identity/history/non-collapse and failure meanings are stable; physical representations remain evolvable.

**Downstream implications**

Later detailed design must derive API/schema/provider realizations from this closure rather than invent semantics.

**Non-implications**

No transport, DTO, envelope, queue, DB, provider protocol or SDK is selected.

---

# CID-SV-B6-DAD-019 — S13 contribution + typed internal dependency/Foundation consumption do not transfer authority

**Decision**

S12 may later contribute authorized projection-eligible Notification resource metadata to S13 using Notification identity, Tenant/audience applicability, source correlation, history/provenance/freshness/uncertainty and redacted metadata, while S13 remains a projection. Internally, S12 reuses the accepted `SDD/ACD/EL/HPL/XED` taxonomy with the hard SDD graph:

```text
NT02 → NT01
NT03 → NT01, NT02
NT04 → NT02, NT03
NT05 → NT04
NT06 → NT05
NT07 → NT02, NT03
NT08 → NT03, NT04, NT05, NT06, NT07
```

Shared Foundation is consumed only through accepted Stable Entry→Contract→Module→Provider paths.

**Reason**

S13 requires a future stable Notification contribution identity, while this Batch must not design Discovery. Typed dependencies also prevent evidence feedback from being mistaken for circular semantic definition or ownership.

**Alternatives avoided**

- S13 index as Notification SoT;
- extra `Discovery Adapter` module inside S12;
- shared database/event bus as hidden dependency/authority;
- new Foundation capability invented by S12.

**Constraint traceability**

Z3 S13 projection boundary, GAC-EPOCH-0060 S13 non-preemption, Batch-1 dependency taxonomy, Foundation exhaustion/readiness.

**Authority impact**

No S13/Foundation/provider authority transfer. Hard SDD is acyclic.

**Offline/private impact**

S12 remains independently correct when S13/provider/Foundation realizations are unavailable.

**Compatibility impact**

Contribution semantics preserve source/Notification identity and authorization; implementation/Foundation providers remain replaceable.

**Downstream implications**

S13 later consumes contributions under its own authorized design. Detailed implementations must distinguish SDD from EL/HPL/XED feedback.

**Non-implications**

No S13 index/query/ranking/search/storage/UX, no new Foundation module/provider, no implementation event bus/DB/callback dependency.

---

# DAD Traceability Matrix

| DAD | Primary subject | Upstream controlling evidence | MDE impact |
|---|---|---|---|
| 001 | S12 decomposition | Z3 S12 + GAC-0060 | none |
| 002 | Notification Identity | Owner notification + NSE-009 | none; physical namespace unfrozen |
| 003 | Occurrence/history identity | Project temporal/history + RCP-18 | none |
| 004 | source correlation/authority | NSE-011 + S12 boundary | none |
| 005 | creation lifecycle | Owner notification + GAC-0060 | none |
| 006 | audience/privacy | S1–S4 + Owner decision | none |
| 007 | multi-dimensional lifecycle | Owner/GAC non-collapse | none; exact state machine unfrozen |
| 008 | Delivery Intent | Owner channel-neutral delivery | none |
| 009 | Delivery Attempt | Z2-MDE-014 + SV-R08 | none |
| 010 | retry/re-delivery lineage | GAC non-preemption | none; no policy/guarantee |
| 011 | provider evidence | NSE-012 + SV-R08 | none |
| 012 | delivery success evidence | Provider non-authority | none |
| 013 | observed/read/ack/resolved | Owner/GAC non-collapse | none; exact lifecycle unfrozen |
| 014 | Human Task separation | persisted Owner decisions | none |
| 015 | channel-neutral core | Owner Option B | none |
| 016 | offline/recovery | NSE-004 + Z2 recovery | none; no winner/fail policy |
| 017 | config/secret | Z2-MDE-016 + RCP-19 | none |
| 018 | RCP-18 closure | explicit GAC-0060 authorization | none |
| 019 | S13/dependency/Foundation | Z3/Foundation/GAC-0060 | none |

---

# MDE Escalation Audit

The DAD set does not decide or change:

```text
Human Task vs Notification separation
→ unchanged

Notification projection vs source/current-state Authority
→ unchanged

S12 / SV-R08 Actual-state ownership
→ refined only, not moved

Channel-neutral core guarantee
→ inherited

Pluggable external delivery
→ inherited

Private/offline correctness
→ inherited

Feishu / WeCom / SMS target intent
→ inherited

Tenant / Principal / privacy boundary
→ preserved

Major physical Notification identity namespace
→ not selected

Major Notification history commitment beyond inherited durable history/non-collapse
→ not added

Universal delivery guarantee
→ none

Global retry/re-delivery policy
→ none

Global fallback-channel policy
→ none

Fail-open / fail-closed policy
→ none

Conflict winner
→ none

Provider/protocol/framework/storage lock-in
→ none

High migration-cost physical commitment
→ none

New Product capability
→ none
```

```text
Misclassified MDE Found
→ 0

New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

If later design proposes any of the material changes above, affected work must stop and return to GAC/Project Owner under Unified Governance.

---

# DAD Candidate Status

```text
CID-SV-B6-DAD-001..019
→ PRODUCED / AWAITING_GLOBAL_ACCEPTANCE

Global Acceptance
→ NOT CLAIMED

GAC Epoch Advance
→ NOT CLAIMED
```
