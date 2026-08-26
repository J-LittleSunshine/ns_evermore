# NGRP-001 — ns_runtime Component Internal Design / Batch 3 DAD Evidence

## 1. Authority and Classification Boundary

- Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_RUNTIME / BATCH_3 / COORDINATION_RECOVERY_RECONCILIATION_DIAGNOSTICS_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Producing Entry HEAD: `62f84a8bd38d6a49240d6b44f5151f88875f3d79`
- Recovered Epoch: `GAC-EPOCH-0076`
- Decision Registry: `0.0.27 / CURRENT / NORMATIVE`
- Candidate: `docs/architecture_reviews/ns_evermore_ngrp_001_ns_runtime_internal_design_batch_3_candidate_0.0.1.md`
- Candidate Commit: `5ec780d0347fa83270a653f1732b7db06c2e20f2`
- Decision class used here: `DAD` only.

The decisions below refine only the globally accepted `R4 / RT-R04` coordination-recovery/reconciliation/diagnostics boundary. None chooses a conflict winner, merge law, authoritative synchronization direction, universal replay/recovery semantics, cross-Tenant behavior, delivery guarantee, global timeout/priority/fairness law, material fail-open/fail-closed policy, provider/protocol/framework/storage lock-in or a major universal identity namespace. If any such commitment becomes materially required, this DAD set is insufficient and the affected work must return to Project Owner / MDE through GAC.

---

## CID-RT-B3-DAD-001 — R4 internal responsibility decomposition

**Decision / Issue.** How to decompose R4 deeply enough that recovery scope, evidence exchange, re-observation, reconciliation participation, diagnostics, uncertainty and history are not left to implementation.

**Context.** R4/RT-R04 is already accepted as coordination recovery/reconciliation participant and diagnostics producer, while source recovery authority remains elsewhere.

**Alternatives Considered.** (A) one undifferentiated recovery coordinator; (B) split by technology/mechanism such as transport, store and worker; (C) decompose by architecture-semantic responsibility.

**Selected Design-semantic Result.** Select (C): `RC01..RC09` for scope/context binding, recovery-stage qualification, R1/R2/R3 evidence correlation, evidence exchange, re-observation, reconciliation participation, health/diagnostics/applied configuration, uncertainty/currentness, and history/stable-contract governance.

**Rationale.** Semantic decomposition gives every material R4 obligation a named custodian while preventing implementation mechanisms from defining authority or lifecycle meaning.

**Responsibility Consequence.** Nine responsibilities collectively cover R4; no label implies a module, service, process, queue or persistence unit.

**Dependency Consequence.** Common scope/qualification semantics precede exchange/re-observation/reconciliation; history depends on produced evidence rather than controlling source owners.

**Authority / SoT / Actual-state Consequence.** R4 remains final owner only of facts genuinely originating in its own coordination/diagnostic partition.

**RCP Consequence.** Provides the internal basis for RCP-20 RT-R04 contribution and RCP-22 producer contribution.

**Failure / Offline Consequence.** Uncertainty/offline behavior becomes explicit and reusable across R4 responsibilities.

**Explicit Non-implications.** No recovery engine, reconciliation engine, replay engine, event log, conflict resolver or source-recovery algorithm.

**Deferred Implementation Mechanics.** Packages/classes, transport binding, storage, concurrency, deployment and provider choices.

**Revalidation Trigger.** Any proposal that merges R4 with source recovery authority, a canonical conflict resolver, or another Product Component boundary.

---

## CID-RT-B3-DAD-002 — Scoped R4 Recovery Scope identity/reference

**Decision / Issue.** Whether a recovery/reconciliation coordination episode requires an identity distinct from Operation, Participant, Dispatch and R3 request identities.

**Context.** The same Operation/participant/source may undergo multiple recovery episodes with different evidence, source revisions and outcomes; history must distinguish them non-destructively.

**Alternatives Considered.** (A) reuse Operation/Participant identity; (B) reuse a transport/message identifier; (C) define a scoped representation-neutral `R4 Recovery Scope Identity / Reference`.

**Selected Design-semantic Result.** Select (C).

**Rationale.** Reusing upstream identity collapses distinct recovery episodes, while transport identity would lock architecture to representation. A bounded R4 scope identity is materially required for correlation/history.

**Responsibility Consequence.** RC01 establishes the scope reference; RC02-RC09 consume it.

**Dependency Consequence.** Recovery-stage evidence depends on scope identity; source facts never depend semantically on R4 identity.

**Authority / SoT / Actual-state Consequence.** Scope identity identifies an R4 coordination object only; it creates no source-fact authority or universal operation ownership.

**RCP Consequence.** RCP-20 can distinguish Recovery Scope from source/operation/dispatch/request/effect subjects.

**Failure / Offline Consequence.** Pending/conflicting/partial evidence stays attributable to the correct recovery episode across disconnect/reconnect.

**Explicit Non-implications.** No UUID, PK, message ID, wire identifier, global recovery namespace or cross-Tenant recovery identity law.

**Deferred Implementation Mechanics.** Physical identifier generation, serialization and persistence.

**Revalidation Trigger.** Any proposal to make the identity universal across Product semantics, cross-Tenant by default, or physically format-bound.

---

## CID-RT-B3-DAD-003 — Scoped R4 Recovery/Reconciliation-stage evidence identity/reference

**Decision / Issue.** How to preserve multiple R4 evidence occurrences for one Recovery Scope without overwriting prior history.

**Context.** A scope can contain repeated exchange, re-observation, unavailable/conflict and later reconciliation-stage evidence.

**Alternatives Considered.** (A) mutate one current recovery record; (B) reuse Recovery Scope identity for every evidence occurrence; (C) define scoped `R4 Recovery / Reconciliation-stage Evidence Identity / Reference`.

**Selected Design-semantic Result.** Select (C).

**Rationale.** A separate bounded evidence identity preserves provenance and allows one scope to retain multiple material observations without imposing event sourcing.

**Responsibility Consequence.** RC09 governs evidence lineage; RC02-RC08 produce R4-bounded evidence semantics.

**Dependency Consequence.** Evidence identity depends on Recovery Scope identity, never vice versa.

**Authority / SoT / Actual-state Consequence.** It identifies R4-owned evidence only; external/source evidence retains its own owner identity and authority.

**RCP Consequence.** RCP-20 and RCP-22 can preserve distinct R4 evidence occurrences and diagnostic provenance.

**Failure / Offline Consequence.** Earlier failed/unavailable/conflicting evidence remains visible after later success or reconnect.

**Explicit Non-implications.** No event-store, event-log, message-envelope, global event namespace, database layout or compaction policy.

**Deferred Implementation Mechanics.** Persistence/indexing/retention representation and physical keys.

**Revalidation Trigger.** Any attempt to canonicalize external source facts through this R4 evidence identity or turn it into universal event identity.

---

## CID-RT-B3-DAD-004 — Bounded R4 Actual-state ownership and source-authority preservation

**Decision / Issue.** Precisely what Actual-state R4 may own during recovery/reconciliation.

**Context.** Recovery collects and correlates evidence from multiple owners, creating high risk that coordination placement becomes de facto source authority.

**Alternatives Considered.** (A) centralize recovered facts in R4; (B) make R4 only transport with no owned state; (C) give R4 final ownership only of its originating coordination/health/currentness/history facts while all source assertions remain source-owned.

**Selected Design-semantic Result.** Select (C).

**Rationale.** R4 needs observable own state for accountability but cannot replace Project Architecture one-final-owner semantics.

**Responsibility Consequence.** RC01-RC09 own only R4 scope/stage/exchange/re-observation/reconciliation-participation/diagnostic/qualification/history facts.

**Dependency Consequence.** Source evidence enters as XED/EL/HPL; it is not reverse SDD ownership.

**Authority / SoT / Actual-state Consequence.** Node/Agent/Automation/Server/R1/R2/R3 source facts, source recovery outcome and conflict winner remain external; Authority/SoT transfer is zero.

**RCP Consequence.** RCP-20 explicitly carries `source owner + R4 coordination`, not `R4 canonical state`.

**Failure / Offline Consequence.** Missing/unreachable source evidence produces R4 uncertainty rather than source-state fabrication.

**Explicit Non-implications.** No central recovery SoT, universal runtime SoT, synchronized canonical store or source-state mirror authority.

**Deferred Implementation Mechanics.** Physical storage/cache/projection design.

**Revalidation Trigger.** Any requirement for R4 to become final owner of an assertion already owned elsewhere.

---

## CID-RT-B3-DAD-005 — R1/R2/R3 evidence correlation preserves accepted identity boundaries

**Decision / Issue.** How R4 consumes R1/R2/R3 evidence without reopening their internal architecture or collapsing identity.

**Context.** R4 is intentionally sequenced after globally accepted R1-R3 and must recover coordination history across those partitions.

**Alternatives Considered.** (A) normalize upstream evidence into one R4 identity; (B) redesign R1-R3 recovery views; (C) preserve all accepted upstream identities and correlate by reference only.

**Selected Design-semantic Result.** Select (C).

**Rationale.** Recovery requires linkage, not authority/identity replacement.

**Responsibility Consequence.** RC03 consumes Participant/Presence Observation, Operation/Admission/Dispatch, R3 Request/R3 Evidence references as distinct semantic subjects.

**Dependency Consequence.** RCP-03/05/06 are upstream XED/EL inputs; no reverse SDD into R1/R2/R3 is introduced.

**Authority / SoT / Actual-state Consequence.** R1/R2/R3 retain their accepted Actual-state ownership; R4 owns only correlation facts.

**RCP Consequence.** RCP-20 preserves exact R1/R2/R3 correlation needed for reconnect/recovery without reopening RCP-03/05/06.

**Failure / Offline Consequence.** Stale/missing upstream evidence is qualified explicitly; it is not rewritten or silently substituted.

**Explicit Non-implications.** No universal operation ID, participant registry, dispatch rewrite or R3 outcome authority.

**Deferred Implementation Mechanics.** Lookup/index/transport mechanisms for correlation.

**Revalidation Trigger.** Any proposal to collapse upstream identities, modify their accepted semantics, or make R4 their canonical registry.

---

## CID-RT-B3-DAD-006 — Evidence exchange is coordination evidence, not source-fact transfer

**Decision / Issue.** What an R4 evidence-exchange request/receipt/handoff means.

**Context.** Recovery must move or make evidence available across participants while original factual authority remains with the producer/source owner.

**Alternatives Considered.** (A) receipt makes R4 copy canonical; (B) treat exchange as opaque transport with no architecture semantics; (C) model request/receipt/handoff as R4 coordination facts while preserving source identity/provenance/currentness.

**Selected Design-semantic Result.** Select (C).

**Rationale.** R4 needs auditable exchange state, but availability at R4 cannot create semantic authority.

**Responsibility Consequence.** RC04 owns exchange request/receipt/handoff/pending/partial/currentness evidence only.

**Dependency Consequence.** RC04 depends on scope/upstream correlation and consumes external evidence by XED.

**Authority / SoT / Actual-state Consequence.** `Evidence Received != Canonical`; source fact ownership does not move.

**RCP Consequence.** RCP-20 stabilizes evidence-exchange references and provenance without schema/protocol selection.

**Failure / Offline Consequence.** No response, partial receipt or unavailable source remains explicit; absence never deletes the source fact.

**Explicit Non-implications.** No delivery guarantee, queue/broker/event log, replication authority, retry algorithm or synchronization winner.

**Deferred Implementation Mechanics.** Invocation/retry/storage/transport realization under later authority.

**Revalidation Trigger.** Any requirement that receipt, replication or synchronization itself changes source authority/canonical status.

---

## CID-RT-B3-DAD-007 — Re-observation is source-owner re-observation, never R4 canonicalization

**Decision / Issue.** How R4 obtains fresher source evidence during recovery.

**Context.** Reconnect alone is insufficient; the original source owner may need to observe its own partition again.

**Alternatives Considered.** (A) R4 reconstructs/re-writes source state; (B) R4 treats reconnect as re-observation; (C) R4 coordinates an explicit source-owner re-observation request and correlates owner-produced evidence.

**Selected Design-semantic Result.** Select (C).

**Rationale.** Only the source owner can authoritatively re-observe its partition; R4 can coordinate but not assume the result.

**Responsibility Consequence.** RC05 owns request/handoff/receipt/correlation facts; source owner owns performed observation and source evidence.

**Dependency Consequence.** Owner result is XED/EL to RC05/RC06, not reverse SDD.

**Authority / SoT / Actual-state Consequence.** `Re-observation Result Received != Canonical automatically`; R4 gets no source authority.

**RCP Consequence.** RCP-20 includes re-observation request and source-supplied result/evidence reference semantics.

**Failure / Offline Consequence.** Re-observation failure/no response means uncertainty/unavailability, not source invalidation or deletion.

**Explicit Non-implications.** No source recovery algorithm, polling protocol, timeout law, forced rewrite or remote observation authority.

**Deferred Implementation Mechanics.** Concrete invocation, scheduling, transport and source adapter mechanics.

**Revalidation Trigger.** Any requirement for R4 to generate, override, rewrite or canonically validate source facts.

---

## CID-RT-B3-DAD-008 — Reconciliation-stage participation does not select conflict winner or merge law

**Decision / Issue.** What R4 reconciliation participation may conclude when evidence conflicts.

**Context.** Project Architecture prohibits latest/local/central winner rules unless Owner decides; R4 must still represent reconciliation progress.

**Alternatives Considered.** (A) choose latest; (B) choose central/local/source priority; (C) preserve conflicting evidence/provenance and own only R4 reconciliation-stage participation facts.

**Selected Design-semantic Result.** Select (C).

**Rationale.** A reconciliation coordinator can track participation and unresolved conflict without owning the domain resolution law.

**Responsibility Consequence.** RC06 owns participation started/pending/completed, conflict/partiality qualifications and references to source outcomes when supplied.

**Dependency Consequence.** Source decisions/outcomes are XED; reconciliation semantics do not induce authority cycles.

**Authority / SoT / Actual-state Consequence.** Conflict winner, merged canonical state and source-domain recovery outcome remain external/not selected.

**RCP Consequence.** RCP-20 closes runtime-side stage semantics while Full Cross-component Closure remains open.

**Failure / Offline Consequence.** Conflicts may remain unresolved across offline periods and later evidence; they are preserved, not discarded.

**Explicit Non-implications.** No latest-wins, local-wins, central-wins, majority-wins, source-priority, CRDT, merge algorithm or authoritative sync direction.

**Deferred Implementation Mechanics.** Any future source-specific reconciliation mechanism under its proper authority.

**Revalidation Trigger.** Any need for Product-wide winner/merge/reconciliation law immediately triggers MDE.

---

## CID-RT-B3-DAD-009 — Recovery/reconciliation completion is multi-stage, not universal RECOVERED

**Decision / Issue.** How to express R4 completion without conflating coordination completion with source recovery success.

**Context.** Recovery includes evidence exchange, possible re-observation, reconciliation participation and source-owned outcomes that may complete independently.

**Alternatives Considered.** (A) universal `RECOVERED`; (B) complete only when every source says success; (C) keep explicit stage facts and source outcome references distinct.

**Selected Design-semantic Result.** Select (C): Recovery Coordination Started, Evidence Exchanged, Re-observation Requested/Completed when established, Reconciliation Participation Completed, Source Re-observed, Source Produced New Evidence, Conflict Remains and Source Recovery Outcome remain separate subjects.

**Rationale.** This permits truthful R4 completion without claiming a universal source state.

**Responsibility Consequence.** RC02 owns bounded recovery-stage completion; RC04/05/06 own their stages; RC09 preserves lineage.

**Dependency Consequence.** Source outcome is external evidence, not hard prerequisite for defining R4 completion semantics.

**Authority / SoT / Actual-state Consequence.** R4 completion never transfers source outcome ownership.

**RCP Consequence.** RCP-20 explicitly encodes stage/outcome non-collapse.

**Failure / Offline Consequence.** R4 can complete its coordination while conflict remains; offline sources may leave broader outcome unknown.

**Explicit Non-implications.** No universal success/failure state machine, global completion barrier, timeout or recovery SLA.

**Deferred Implementation Mechanics.** State representation and orchestration mechanisms.

**Revalidation Trigger.** Any requirement for a Product-wide single recovery-success semantic or global completion law.

---

## CID-RT-B3-DAD-010 — Currentness, availability, uncertainty, conflict and partiality are orthogonal qualifications

**Decision / Issue.** How R4 represents uncertain recovery evidence without collapsing status categories.

**Context.** Recovery commonly observes stale, unreachable, partial and conflicting evidence simultaneously; a single linear state would lose semantics.

**Alternatives Considered.** (A) one linear state enum; (B) coerce everything to success/failure; (C) use orthogonal architecture-semantic qualifications under accepted Foundation status/freshness semantics.

**Selected Design-semantic Result.** Select (C), supporting applicable `RECOVERY_PENDING`, `RECONCILIATION_PENDING`, `RECOVERING`, `UNKNOWN`, `STALE`, `UNAVAILABLE`, `UNREACHABLE`, `INDETERMINATE`, `CONFLICTING`, `PARTIAL`, and source-established `SUPERSEDED`.

**Rationale.** Orthogonal qualifications preserve evidence truth and prevent hidden fail policy/winner assumptions.

**Responsibility Consequence.** RC08 is the shared qualifier semantic custodian; individual responsibilities produce evidence to which it applies.

**Dependency Consequence.** RC08 depends only on scope semantics; no cycle with source feedback.

**Authority / SoT / Actual-state Consequence.** R4 owns qualification of its evidence/view, not source truth implied by those labels.

**RCP Consequence.** RCP-20/RCP-22 carry currentness/uncertainty semantics consistently.

**Failure / Offline Consequence.** Unknown/stale/unreachable remain explicit offline; none automatically means absent/false/failed/denied.

**Explicit Non-implications.** No mandatory enum, transition graph, TTL, timeout, global clock, fail-open/fail-closed rule or winner rule.

**Deferred Implementation Mechanics.** Status encoding, timestamps, clock provider and UI rendering.

**Revalidation Trigger.** Any proposal to turn these qualifications into universal Product lifecycle or authority decisions.

---

## CID-RT-B3-DAD-011 — Non-destructive history and provenance survive later recovery evidence

**Decision / Issue.** Whether later successful/reconciled evidence may replace prior conflict/failure observations.

**Context.** Recovery auditability requires retaining prior evidence and provenance, including mutually conflicting observations.

**Alternatives Considered.** (A) keep latest only; (B) overwrite failures after success; (C) preserve append-like semantic history without mandating event sourcing.

**Selected Design-semantic Result.** Select (C).

**Rationale.** Historical truth cannot be reconstructed if earlier conflict/unavailability is silently erased.

**Responsibility Consequence.** RC09 preserves one scope→many exchanges/re-observations/evidence occurrences and source relationships.

**Dependency Consequence.** HPL connects later evidence to earlier evidence; current projection is not a reverse authority dependency.

**Authority / SoT / Actual-state Consequence.** History preserves producer/source owner and never canonicalizes by arrival order.

**RCP Consequence.** RCP-20/RCP-22 include lineage/provenance/history compatibility.

**Failure / Offline Consequence.** Later reconnect/success does not erase offline failure, conflict or uncertainty evidence.

**Explicit Non-implications.** No event sourcing, immutable storage technology, retention duration, physical append log or lossy compaction policy.

**Deferred Implementation Mechanics.** Storage/retention/indexing/archival implementation.

**Revalidation Trigger.** Any historical rewrite/compaction requirement that loses provenance or changes authoritative interpretation.

---

## CID-RT-B3-DAD-012 — RCP-20 RT-R04 stable contract closes at current design level only

**Decision / Issue.** What exact semantic information RCP-20 must stabilize on the runtime coordinator side.

**Context.** RCP-20 is primary current closure authority, while source-owner contributions remain distributed/downstream.

**Alternatives Considered.** (A) defer contract semantics to implementation; (B) define DTO/schema now; (C) define representation-neutral semantic information obligations and non-implications.

**Selected Design-semantic Result.** Select (C): scope/subject/source owner/revision/original evidence, R1/R2/R3 correlations, exchange/re-observation/reconciliation evidence, currentness/availability/uncertainty/conflict/partiality, governed context, temporal/history/provenance, compatibility/offline qualifications.

**Rationale.** This is sufficient for independent implementations to preserve semantics without representation lock-in.

**Responsibility Consequence.** RC09 governs the contract; RC01-RC08 each contribute bounded semantic evidence.

**Dependency Consequence.** Source-owner evidence remains XED; stable contract does not reverse authority.

**Authority / SoT / Actual-state Consequence.** Contract explicitly preserves source owner + R4 coordination; no canonical merger.

**RCP Consequence.** `RCP-20 RT-R04 contribution → CLOSED AT CURRENT DESIGN LEVEL`; Full Cross-component Closure remains not closed/not claimed.

**Failure / Offline Consequence.** Contract can express stale/unknown/conflicting/partial/private-offline conditions without public dependency.

**Explicit Non-implications.** No API, DTO, wire schema, endpoint, serialization format, broker or delivery guarantee.

**Deferred Implementation Mechanics.** Physical representation and transport under later authorized design.

**Revalidation Trigger.** Any proposed semantic change to source authority, conflict outcome, identity meaning or history compatibility.

---

## CID-RT-B3-DAD-013 — RCP-22 contribution is only RT-R04-originated diagnostics/provenance

**Decision / Issue.** What diagnostics/provenance R4 may produce without becoming universal diagnostic/source-fact authority.

**Context.** RCP-22 spans all fact owners; current authorization is only the RT-R04 producer contribution.

**Alternatives Considered.** (A) centralize all diagnostics in R4; (B) emit only opaque logs; (C) define R4-originated recovery/health/currentness/conflict/provenance observations and preserve source references/authority.

**Selected Design-semantic Result.** Select (C).

**Rationale.** R4 needs actionable diagnostic evidence, but collecting source evidence cannot make R4 its semantic owner.

**Responsibility Consequence.** RC07 owns R4 health/lifecycle/config diagnostics; RC08 qualifies uncertainty; RC09 preserves provenance.

**Dependency Consequence.** External source diagnostics remain XED/EL; WB/SDK projection remains downstream.

**Authority / SoT / Actual-state Consequence.** `Diagnostic Observation != Source Fact`; no universal diagnostic storage authority is created.

**RCP Consequence.** `RCP-22 RT-R04 producer contribution → CLOSED AT CURRENT DESIGN LEVEL`; Full Cross-component Closure remains open.

**Failure / Offline Consequence.** Diagnostics explicitly preserve degraded/unknown/private conditions and redaction obligations.

**Explicit Non-implications.** No diagnostics UI, centralized telemetry database, log format, exporter/provider or hidden-reasoning requirement.

**Deferred Implementation Mechanics.** Logging/telemetry sinks, storage, UI and SDK representation.

**Revalidation Trigger.** Any proposal for R4 diagnostics to override source facts or become a universal system truth store.

---

## CID-RT-B3-DAD-014 — RCP-19 Desired/Applied/Observed topology remains unchanged for R4 configuration

**Decision / Issue.** How recovery-related configuration participates in R4 without moving Desired-state authority.

**Context.** S9 owns managed Desired Configuration; actual runtime partitions own their Applied state; Observed is projection.

**Alternatives Considered.** (A) let R4 own desired recovery configuration; (B) treat observed config as applied truth; (C) preserve S9 desired authority and let R4 own only genuinely applied R4 configuration Actual-state/health evidence.

**Selected Design-semantic Result.** Select (C).

**Rationale.** Recovery cannot become a special path that bypasses accepted configuration topology.

**Responsibility Consequence.** RC07 owns only R4-applied config evidence, application/divergence/unknown health and intrinsic R4 configuration semantics.

**Dependency Consequence.** Desired config is XED/ACD from S9; observation remains projection.

**Authority / SoT / Actual-state Consequence.** `Desired != Distributed != Applied != Observed`; Desired SoT stays S9.

**RCP Consequence.** RCP-19 is preserved, not reopened; only R4-owned applied evidence is refined.

**Failure / Offline Consequence.** Stale/partial/unknown application does not rewrite desired state; offline local application does not create Desired Authority.

**Explicit Non-implications.** No push/pull/watch protocol, rollout engine, config DB, secret store or provider.

**Deferred Implementation Mechanics.** Distribution/application mechanism and persistence.

**Revalidation Trigger.** Any proposal moving Desired-state authority or treating observed state as Applied SoT.

---

## CID-RT-B3-DAD-015 — Offline/private recovery and replay references preserve authority

**Decision / Issue.** How R4 behaves during disconnection and around replay-related evidence without universal replay/recovery law.

**Context.** Core correctness must work in private/offline deployments; local evidence can outlive connectivity.

**Alternatives Considered.** (A) require always-online central recovery; (B) local-wins during offline; (C) preserve locally/source-owned evidence, explicit uncertainty and later evidence exchange/re-observation without authority transfer.

**Selected Design-semantic Result.** Select (C). Replay request/occurrence references may be preserved only when supplied by existing source semantics.

**Rationale.** Offline continuity must not create a hidden conflict winner or retroactive authorization path.

**Responsibility Consequence.** RC04/05/08/09 preserve offline exchange/re-observation status and replay-related provenance references.

**Dependency Consequence.** Public services are not semantic dependencies; source evidence remains XED when available.

**Authority / SoT / Actual-state Consequence.** Local/central copies never become canonical by availability; replay never changes original authority.

**RCP Consequence.** RCP-20 carries offline/private qualification and provenance; no replay contract is created.

**Failure / Offline Consequence.** Unknown/stale/unreachable/conflicting remain explicit until evidence establishes more.

**Explicit Non-implications.** No deterministic replay, replay=original execution, source reconstruction, event log, local-wins/central-wins or global fail policy.

**Deferred Implementation Mechanics.** Local retention, reconnect mechanics and replay implementation where independently authorized.

**Revalidation Trigger.** Any universal replay guarantee, authoritative offline sync direction or fail-open/fail-closed recovery law.

---

## CID-RT-B3-DAD-016 — Downstream source-evidence contracts remain reference/re-observation expectations only

**Decision / Issue.** How R4 can coordinate recovery using Node/Agent/Server evidence whose owner-side internal design is not authorized here.

**Context.** RCP-04/07/08/09/23 source evidence may be needed for correlation/re-observation, but ns_runtime cannot design those components.

**Alternatives Considered.** (A) design source contracts owner-side in R4; (B) ignore source evidence pressure; (C) specify only representation-neutral consumer/reference/re-observation expectations.

**Selected Design-semantic Result.** Select (C): source evidence identity/reference, owner, partition, revision/context, operation/attempt/effect correlation, temporal/status/provenance/governed context/compatibility where applicable.

**Rationale.** R4 becomes design-complete for its consumer needs while preserving downstream owner authority.

**Responsibility Consequence.** RC01/03/04/05/09 consume source references without defining source lifecycle.

**Dependency Consequence.** RCP-04/07/08/09/23 are XED/EL/HPL only, not hard internal SDD.

**Authority / SoT / Actual-state Consequence.** Owner-side source facts remain entirely with ND/AG/SV owners.

**RCP Consequence.** No owner-side closure or full cross-component closure is claimed by inference.

**Failure / Offline Consequence.** Missing downstream evidence is explicit uncertainty; R4 does not fabricate substitutes.

**Explicit Non-implications.** No Node/Agent internal modules, source algorithms, DTOs, lifecycle, retry or recovery semantics.

**Deferred Implementation Mechanics.** Downstream Component Internal Design and later contract representation.

**Revalidation Trigger.** Any consumer expectation that would require changing a downstream source owner's accepted authority/semantics.

---

## CID-RT-B3-DAD-017 — Typed dependency topology with acyclic hard SDD

**Decision / Issue.** How to model R4 dependencies without treating feedback/evidence exchange as a semantic-definition cycle.

**Context.** Recovery is feedback-heavy; naive graphs can incorrectly model source re-observation responses as reverse semantic-definition dependencies.

**Alternatives Considered.** (A) one untyped dependency graph; (B) ignore dependency analysis; (C) retain accepted SDD/ACD/EL/HPL/XED taxonomy and analyze only SDD for hard cycles.

**Selected Design-semantic Result.** Select (C) with SDD: `RC08→RC01`; `RC02→RC01,RC08`; `RC03→RC01,RC08`; `RC04→RC01,RC02,RC03,RC08`; `RC05→RC01,RC02,RC03,RC04,RC08`; `RC06→RC01,RC02,RC03,RC04,RC08`; `RC07→RC01,RC02,RC08`; `RC09→RC01..RC08` as applicable.

**Rationale.** Typed edges distinguish definition from evidence flow and preserve architectural derivability.

**Responsibility Consequence.** Each responsibility has explicit prerequisite semantics and no mutual definition loop.

**Dependency Consequence.** Hard SDD is acyclic; source-owner re-observation feedback enters RC06 through EL/XED, not reverse SDD.

**Authority / SoT / Actual-state Consequence.** No dependency edge changes source or actual-state ownership.

**RCP Consequence.** RCP-20 external evidence relations remain non-authoritative evidence dependencies.

**Failure / Offline Consequence.** Missing external evidence degrades availability/currentness, not semantic-definition completeness.

**Explicit Non-implications.** No call graph, service graph, process graph, deployment graph or transport topology.

**Deferred Implementation Mechanics.** Runtime invocation and concrete dependency injection.

**Revalidation Trigger.** Any newly required hard semantic dependency that creates a cycle or circular Actual-state ownership.

---

## CID-RT-B3-DAD-018 — Shared Foundation consumption, compatibility and implementation deferral

**Decision / Issue.** How R4 reuses accepted Foundation semantics and remains implementation-derivable without creating parallel Foundation or prematurely selecting mechanics.

**Context.** Foundation already provides temporal/freshness, correlation/provenance, uncertainty, diagnostics, governed context, representation, network mechanics, secret reference/redaction, compatibility/conformance and bootstrap acquisition.

**Alternatives Considered.** (A) reimplement local parallel primitives; (B) choose concrete technology now; (C) consume accepted Foundation semantics while leaving concrete replaceable realization downstream.

**Selected Design-semantic Result.** Select (C).

**Rationale.** Reuse avoids semantic drift while preserving `Foundation mechanics != Product Authority` and technology neutrality.

**Responsibility Consequence.** RC01-RC09 map explicitly to applicable Foundation semantics; no missing mandatory Foundation capability was found.

**Dependency Consequence.** Foundation semantics are reusable ACD/semantic primitives, not owners of R4 Product facts.

**Authority / SoT / Actual-state Consequence.** Foundation storage/network/diagnostic placement gains no source or R4 semantic authority.

**RCP Consequence.** RCP-20/RCP-22 semantics remain representation-neutral and compatibility-aware.

**Failure / Offline Consequence.** Private/offline behavior and redaction/status semantics remain preserved across provider/implementation replacement.

**Explicit Non-implications.** No Redis/Kafka/NATS/RabbitMQ/Celery/Temporal/etc.; no DB/event store; no REST/gRPC/concrete WebSocket frames; no process/container topology; no exactly/at-most/at-least-once guarantee.

**Deferred Implementation Mechanics.** All concrete framework/provider/storage/protocol/process/concurrency/deployment selections legally delegated downstream.

**Revalidation Trigger.** Missing mandatory reusable Foundation semantic, semantic incompatibility, provider lock-in that changes architecture, or any proposal that leaves an architecture-critical rule to implementation.

---

# 2. DAD Aggregate Consequences

```text
DAD Set
→ CID-RT-B3-DAD-001..018

R4 Internal Responsibilities
→ RC01..RC09

Scoped R4 Identity Subjects
→ 2

Authority Transfer
→ 0

SoT Transfer
→ 0

Final Actual-state Ownership Transfer
→ 0

Conflict Winner / Merge Law
→ NOT CREATED

Universal Recovery / Replay Semantics
→ NOT CREATED

RCP-20 RT-R04 Contribution
→ CLOSED AT CURRENT DESIGN LEVEL in Candidate

RCP-20 Full Cross-component Closure
→ NOT CLAIMED

RCP-22 RT-R04 Producer Contribution
→ CLOSED AT CURRENT DESIGN LEVEL in Candidate

RCP-22 Full Cross-component Closure
→ NOT CLAIMED

R1/R2/R3 Reopen
→ 0

Downstream Owner-side Internal Design
→ 0

Hard Internal SDD Graph
→ ACYCLIC

New MDE
→ 0

Misclassified MDE
→ 0

Missing Mandatory Shared Foundation Semantic
→ NONE_FOUND

Implementation Technology Selection
→ 0
```

No DAD above resolves an Owner-reserved dimension. Any future durable commitment matching the Batch-3 MDE stop boundary invalidates local DAD authority for that dimension and requires immediate escalation.