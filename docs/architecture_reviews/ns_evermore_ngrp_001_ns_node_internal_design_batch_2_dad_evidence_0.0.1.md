# NGRP-001 — Component Internal Design / ns_node / Batch 2 DAD Evidence

## Authority Metadata

- **Authorization:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_NODE / BATCH_2 / OFFLINE_CONTINUITY_RECOVERY_AND_LOCAL_DIAGNOSTICS_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Producing Entry HEAD:** `90ab35107627ab021e7eb67ca95593668454d037`
- **Candidate Commit:** `9339615d310b8976c78db29fa4b7d77972a9af51`
- **Recovered GAC Epoch:** `GAC-EPOCH-0084`
- **Decision Registry:** `0.0.30 / CURRENT / NORMATIVE`
- **DAD Authority:** bounded N4 architecture-semantic refinement only; no Owner-reserved MDE answer may be selected here.

All DADs below refine the already accepted `N4 / ND-R04` responsibility while preserving accepted `N1/N2/N3`, `RT-R04`, Authority/SoT/Actual-state topology, Tenant/Principal/Policy/Trust authority and Shared Foundation neutrality.

---

# CID-ND-B2-DAD-001 — Ten-responsibility N4 decomposition

## Decision / Issue
How should N4 be decomposed deeply enough to make offline continuity, recovery participation, re-observation, reconciliation participation and diagnostics implementation-derivable without creating a Node-local Recovery Manager or reopening N1/N2/N3?

## Context
Accepted N4 owns only Node-local recovery/diagnostic participation facts. Batch 1 already owns readiness, Attempt and Effect/source facts; RT-R04 already owns coordination recovery truth.

## Alternatives Considered
- **A — one monolithic N4 recovery responsibility:** insufficient; hides source ownership, exchange, re-observation, reconciliation and diagnostics boundaries.
- **B — mirror RT-R04 RC01..RC09 one-for-one:** rejected; risks duplicating coordination authority instead of defining the Node participant side.
- **C — ten cohesive Node-local responsibilities aligned to participation scope, retained evidence, continuity, exchange, re-observation, reconciliation, diagnostics, uncertainty, history and contract governance:** selected.

## Selected Design-semantic Result
Select `N4-R01..N4-R10` as defined in the Candidate. Labels are architecture-semantic only.

## Rationale
The decomposition gives every material N4 pressure one principal owner while explicitly separating source facts and RT-R04 coordination facts.

## Responsibility Consequence
N4 has 10 responsibilities; unowned material N4 responsibility = 0; duplicate final responsibility = 0.

## Dependency Consequence
Responsibilities can be typed with SDD/ACD/EL/HPL/XED and topologically ordered without feedback cycles.

## Authority / SoT / Actual-state Consequence
No Authority or source SoT moves to N4. N4 gains only the Node-local actual-state facts explicitly originating in its participation/diagnostic boundary.

## RCP Consequence
RCP-20 maps through N4-R01..R10; RCP-22 N4 producer semantics map through N4-R07..R10.

## Failure / Offline Consequence
Failure/offline evidence is explicit and source-attributable; no universal recovery-success or fail-open/fail-closed policy is created.

## Explicit Non-implications
`10 responsibilities != 10 modules/services/processes/workers/stores`.

## Deferred Implementation Mechanics
Code/package layout, persistence, process topology, transport, concurrency, APIs and physical schemas.

## Revalidation Trigger
Any proposed responsibility that takes N1/N2/N3 source ownership, RT-R04 coordination authority, or requires a new Product capability.

---

# CID-ND-B2-DAD-002 — N4-scoped identities and R4 identity non-collapse

## Decision / Issue
Are new N4 semantic identities required for non-destructive recovery participation history, and how are they separated from accepted R4/source identities?

## Context
One R4 Recovery Scope may involve multiple Node-local participation/evidence occurrences, and one N4 participation scope may contain multiple exchange/re-observation/reconciliation/diagnostic observations. Physical identity formats are prohibited.

## Alternatives Considered
- **A — reuse R4 Recovery Scope and R4 Evidence identities as N4 identities:** rejected; collapses coordinator and participant facts.
- **B — reuse Operation/Attempt/Effect identities:** rejected; collapses independent lifecycles/owners.
- **C — introduce two bounded semantic identities only:** selected.

## Selected Design-semantic Result
```text
N4 Recovery Participation Scope Identity / Reference
N4 Recovery / Diagnostic Evidence Identity / Reference
```
They remain distinct from R4 Recovery Scope/Evidence, N1 readiness evidence, N2 Attempt and N3 Effect/source evidence.

## Rationale
Independent lifecycle and history require distinct correlation subjects, but only at semantic-reference level.

## Responsibility Consequence
N4-R01 originates/binds the participation scope; N4-R09 governs material N4 evidence occurrences.

## Dependency Consequence
Other N4 responsibilities reference these identities through SDD where their semantic definition requires them; source identities enter through EL/XED/HPL.

## Authority / SoT / Actual-state Consequence
Identity never transfers authority. N4 identity identifies N4-owned facts only.

## RCP Consequence
RCP-20 and RCP-22 can preserve N4 evidence separately from R4/source evidence.

## Failure / Offline Consequence
Unknown/missing identity correlation remains explicit; disconnected history remains correlatable without minting source authority.

## Explicit Non-implications
No UUID, database PK, message ID, wire ID, global event namespace or Product-wide recovery namespace.

## Deferred Implementation Mechanics
Generation, encoding, storage/indexing and wire representation.

## Revalidation Trigger
Need for a universal identity namespace, cross-system canonical physical format, or identity collapse with R4/N1/N2/N3.

---

# CID-ND-B2-DAD-003 — Retained-evidence availability and source-attribution semantics

## Decision / Issue
What does N4 own when it retains evidence for offline continuity/recovery?

## Context
N1/N2/N3 produce authoritative Node-local source evidence. N4 must retain/use it without absorbing source semantics or selecting persistence technology.

## Alternatives Considered
- **A — N4 becomes canonical repository of copied source facts:** rejected; storage/location would become authority.
- **B — N4 only stores opaque bytes with no semantic obligations:** rejected; loses source attribution/currentness/history and leaves architecture to implementation.
- **C — N4 owns retention availability/custody/source-attribution facts while the original evidence remains source-owned:** selected.

## Selected Design-semantic Result
N4 preserves source owner, source evidence identity/reference, source revision/context, source temporal/currentness context, N4 retention/receipt context, governed context, privacy/redaction, compatibility and provenance. N4 owns only local retention availability/custody qualification.

## Rationale
Recovery needs durable semantic attribution, not a new source of truth.

## Responsibility Consequence
N4-R02 is principal owner of retained-evidence availability/source-attribution facts; N4-R09 preserves their history.

## Dependency Consequence
N1/N2/N3 evidence is XED/EL/HPL; no reverse SDD or source-definition dependency is created.

## Authority / SoT / Actual-state Consequence
`Local Retention != Canonical Global SoT`; original source owner remains final owner.

## RCP Consequence
RCP-20 carries source attribution and local retention availability; RCP-22 may expose retention diagnostics without canonicalization.

## Failure / Offline Consequence
Unavailable local evidence does not delete/invalidate the source fact; locally available evidence is not automatically current/canonical.

## Explicit Non-implications
No database, event store, file layout, compaction, retention period or storage engine.

## Deferred Implementation Mechanics
Physical persistence, indexing, retention/eviction mechanisms and recovery of stored bytes.

## Revalidation Trigger
Any requirement that a persistence location becomes source authority or that source history must be destructively compacted.

---

# CID-ND-B2-DAD-004 — Offline/degraded continuity qualification without fail policy or linear recovery state machine

## Decision / Issue
How should N4 represent offline/degraded continuity without choosing Product-wide execution/admission policy or a universal recovery state machine?

## Context
Offline/private correctness is first-class, but fail-open/fail-closed is Owner-reserved and N4 cannot grant Admission/Policy/Trust.

## Alternatives Considered
- **A — define one linear OFFLINE→RECOVERING→RECOVERED state machine:** rejected; overstates source recovery semantics.
- **B — define global fail-open/fail-closed behavior:** prohibited MDE decision.
- **C — define orthogonal Node-local continuity/recovery participation qualifications only:** selected.

## Selected Design-semantic Result
N4 may express offline/degraded, `RECOVERY_PENDING`, `RECOVERING`, `RECONCILIATION_PENDING`, availability/partiality/unknown/indeterminate qualifications where evidenced. These are not a universal transition graph.

## Rationale
Continuity must be observable and diagnosable without pretending that N4 decides governance or source recovery success.

## Responsibility Consequence
N4-R03 owns continuity qualification; N4-R08 owns currentness/uncertainty dimensions.

## Dependency Consequence
N4-R03 uses retained-evidence semantics and N4 uncertainty definitions; Admission/Policy/Trust remain external context.

## Authority / SoT / Actual-state Consequence
Offline does not transfer authority; retained Admission does not become new Admission authority.

## RCP Consequence
RCP-20/RCP-22 carry explicit offline/private qualifications without a fail policy.

## Failure / Offline Consequence
Unverifiable remote state stays UNKNOWN/UNAVAILABLE/UNREACHABLE/INDETERMINATE; no automatic allow/deny inference.

## Explicit Non-implications
No universal `RECOVERED`, timeout, escalation, retry, priority or fail policy.

## Deferred Implementation Mechanics
Connectivity detection mechanics, timers, retry/backoff and physical recovery sequencing.

## Revalidation Trigger
Material need for fail-open/fail-closed or universal recovery-success semantics.

---

# CID-ND-B2-DAD-005 — RT-R04 evidence-exchange participant boundary

## Decision / Issue
How does N4 participate in R4 evidence exchange while preserving RT-R04 coordination authority and N1/N2/N3 source ownership?

## Context
RT-R04 RC04 already owns evidence-exchange request/handoff/receipt coordination facts. N4 must provide the Node participant side.

## Alternatives Considered
- **A — N4 mirrors/owns RT-R04 exchange state:** rejected; duplicates R4 coordination truth.
- **B — evidence handoff transfers source ownership to R4/N4:** rejected.
- **C — N4 owns only its local participation/handoff/receipt/correlation facts and references R4/source evidence:** selected.

## Selected Design-semantic Result
N4-R04 records N4 exchange participation, received R4 scope/request refs, local evidence handoff refs, supplied R4 receipt/handoff evidence refs and N4-local availability/partiality/currentness qualifications.

## Rationale
Participant-side evidence is needed to establish what the Node actually handed off/received without turning transport or coordinator state into source truth.

## Responsibility Consequence
N4-R04 is the single principal N4 evidence-exchange participant responsibility.

## Dependency Consequence
RT-R04 evidence is XED/ACD/EL; N4 does not semantically define RT-R04.

## Authority / SoT / Actual-state Consequence
RT-R04 remains coordinator owner; N1/N2/N3 remain source owners; N4 owns only Node participation facts.

## RCP Consequence
Provides the ND-R04 participant-side exchange portion of RCP-20.

## Failure / Offline Consequence
Partial/unavailable/indeterminate exchange is explicit; exchange completion does not imply conflict resolution or source recovery.

## Explicit Non-implications
No broker/queue, transport, delivery guarantee, retry algorithm, acknowledgement protocol or wire schema.

## Deferred Implementation Mechanics
Network invocation, batching, transport, persistence and retry mechanics.

## Revalidation Trigger
Any proposal to make N4 own R4 coordination truth or make handoff/receipt canonicalize source facts.

---

# CID-ND-B2-DAD-006 — Source-owner re-observation participation boundary

## Decision / Issue
How does N4 obtain refreshed N1/N2/N3 evidence during recovery without recreating source facts?

## Context
Accepted RT-R04 coordinates source-owner re-observation. N1/N2/N3 are now accepted source owners and must perform/own their own re-observations.

## Alternatives Considered
- **A — N4 regenerates readiness/Attempt/Effect truth centrally:** rejected; violates source ownership.
- **B — N4 treats no response as deletion/invalidity:** rejected; fabricates source semantics.
- **C — N4 owns only request/handoff/receipt/correlation evidence and references owner-produced results:** selected.

## Selected Design-semantic Result
N4-R05 can originate/correlate a bounded re-observation request reference, target source owner/reference, R4 coordination reference, pending/unavailable qualification and owner-produced result/evidence reference when supplied.

## Rationale
Recovery requires refreshed evidence, but the only valid producer is the original semantic/source owner.

## Responsibility Consequence
N4-R05 owns participant-side re-observation coordination evidence only.

## Dependency Consequence
Owner results are XED/EL; they may inform reconciliation participation but never form reverse SDD.

## Authority / SoT / Actual-state Consequence
N1 owns readiness re-observation; N2 owns Attempt re-observation; N3 owns Effect/source re-observation; R4 owns coordination truth.

## RCP Consequence
RCP-20 preserves request/result correlation and source ownership.

## Failure / Offline Consequence
No response, failure, unreachable or stale result remains explicit and does not erase previous evidence.

## Explicit Non-implications
No source polling algorithm, replay algorithm, freshness SLA or canonical-result selection.

## Deferred Implementation Mechanics
Request transport, scheduling, batching, timeouts and source-specific observation mechanisms.

## Revalidation Trigger
Any requirement for N4 to author source facts, decide source supersession, or treat absence as deletion.

---

# CID-ND-B2-DAD-007 — Reconciliation participation and conflict/partiality preservation without winner law

## Decision / Issue
What may N4 assert during reconciliation when retained/re-observed evidence conflicts?

## Context
N4 must participate in reconciliation but is explicitly prohibited from selecting latest/local/central/source-priority/majority winners or a cross-source merge law.

## Alternatives Considered
- **A — latest timestamp/arrival wins:** prohibited and semantically unsafe.
- **B — local or central copy wins:** prohibited authority transfer.
- **C — preserve conflict/partiality and only own bounded participation-stage facts:** selected.

## Selected Design-semantic Result
N4-R06 may assert participation started/pending/completed for N4's role, correlate R4 reconciliation evidence, preserve participating source refs, and qualify conflict/partiality. Any source/domain resolution remains external owner evidence.

## Rationale
Unresolved disagreement is a first-class state; reconciliation participation is not authority to resolve semantic truth.

## Responsibility Consequence
N4-R06 owns only N4 participation/conflict-observation facts; N4-R08 and R09 qualify/preserve them.

## Dependency Consequence
Re-observation/source-resolution evidence feeds N4 via EL/XED/HPL, not reverse SDD.

## Authority / SoT / Actual-state Consequence
No winner, canonical merged state or synchronization authority is created.

## RCP Consequence
RCP-20 includes reconciliation participation/conflict/partiality evidence and explicit non-implications.

## Failure / Offline Consequence
Conflicts may remain indefinitely explicit; completed N4 participation does not imply source resolution.

## Explicit Non-implications
No CRDT law, source-priority hierarchy, majority rule, merge algorithm or authoritative sync direction.

## Deferred Implementation Mechanics
Conflict presentation, reconciliation orchestration mechanics and source-specific resolution actions.

## Revalidation Trigger
Any Product requirement to choose a canonical winner/merge/sync direction.

---

# CID-ND-B2-DAD-008 — Currentness/availability/uncertainty and source-vs-observation temporal separation

## Decision / Issue
How should N4 qualify freshness/currentness without confusing source time, R4 time and N4 receipt/observation time?

## Context
Recovery evidence can arrive later, out of order, stale or conflict with retained evidence. Timestamp/arrival ordering cannot choose truth.

## Alternatives Considered
- **A — newest timestamp/arrival defines current source fact:** prohibited winner rule.
- **B — one currentness value for source, R4 and N4 views:** rejected; collapses temporal semantics.
- **C — preserve source temporal/currentness context separately from R4/N4 receipt/observation/currentness:** selected.

## Selected Design-semantic Result
N4-R08 uses accepted status semantics and distinguishes source revision/time/currentness, R4 evidence time/currentness and N4 retention/receipt/observation time/currentness.

## Rationale
This prevents projection/transport freshness from masquerading as source freshness or authority.

## Responsibility Consequence
N4-R08 is the principal N4 qualification responsibility used by continuity, exchange, reconciliation and diagnostics.

## Dependency Consequence
Temporal/status Foundation semantics are reusable mechanics; source currentness is external evidence, not redefined by N4.

## Authority / SoT / Actual-state Consequence
Fresh N4 observation never becomes fresh source fact automatically; latest time/arrival never becomes winner.

## RCP Consequence
RCP-20/RCP-22 explicitly carry currentness, availability, uncertainty, conflict and partiality.

## Failure / Offline Consequence
`UNKNOWN`, `STALE`, `UNAVAILABLE`, `UNREACHABLE`, `INDETERMINATE`, `CONFLICTING`, `PARTIAL` remain explicit rather than collapsed.

## Explicit Non-implications
No TTL, clock source, timeout, freshness threshold or ordering algorithm.

## Deferred Implementation Mechanics
Clock implementation, timers, timestamp representation and caching policy.

## Revalidation Trigger
Any design that derives source authority from timestamp, receipt order or observer freshness.

---

# CID-ND-B2-DAD-009 — Non-destructive recovery/diagnostic history and replay non-authority boundary

## Decision / Issue
How is recovery history preserved, and what does replay mean when source domains mention it?

## Context
One recovery scope can have repeated exchanges/re-observations/conflicts and later success. History must survive those changes; N4 is prohibited from defining universal replay.

## Alternatives Considered
- **A — keep only current recovery projection:** rejected; destroys provenance and conflict/failure evidence.
- **B — replay reconstructs original authorization/source state:** prohibited.
- **C — append-oriented/non-destructive semantic history; replay only as source-defined reference/correlation:** selected.

## Selected Design-semantic Result
N4-R09 preserves all material N4 evidence occurrences with source/R4 correlations; later evidence never rewrites prior evidence. Replay references may be retained when supplied, but N4 defines no replay semantics/guarantees.

## Rationale
Recovery correctness and auditability require lineage, especially under offline/conflicting evidence.

## Responsibility Consequence
N4-R09 owns N4 history/provenance, not a universal history store.

## Dependency Consequence
Historical source/R4 evidence enters via HPL/EL/XED; no semantic ownership reversal.

## Authority / SoT / Actual-state Consequence
History collection does not transfer source authority; replay does not reconstruct authority.

## RCP Consequence
RCP-20/RCP-22 require non-destructive history/lineage/provenance.

## Failure / Offline Consequence
Later success does not erase prior failure/conflict/uncertainty; disconnected history remains attributable.

## Explicit Non-implications
No event store, compaction policy, replay engine, deterministic replay or event-sourcing requirement.

## Deferred Implementation Mechanics
Physical append/store/index/retention mechanics and source-specific replay implementation.

## Revalidation Trigger
Any need to rewrite history, lose provenance through compaction, or define replay as Product-wide authority reconstruction.

---

# CID-ND-B2-DAD-010 — RCP-20 ND-R04 participant-side stable semantic contract

## Decision / Issue
What semantic contract depth is required for Node recovery/reconciliation participation without defining DTO/wire/API or claiming full cross-component closure?

## Context
Authorization explicitly requires representation-neutral RCP-20 synthesis on the ND-R04 side. RT-R04 contribution is already accepted.

## Alternatives Considered
- **A — list only an RCP-20 name:** insufficient for downstream derivability.
- **B — define concrete schema/API/protocol:** implementation/detailed-contract leakage.
- **C — close participant-side semantic subjects, ownership, correlations, qualifications, history/offline/compatibility and producer/consumer non-implications:** selected.

## Selected Design-semantic Result
Candidate §18 defines N4 participation scope/context, source-evidence references, RT-R04 exchange correlation, re-observation correlation, reconciliation participation, currentness/availability/uncertainty/conflict/partiality, temporal/history/provenance and compatibility/private-offline obligations.

## Rationale
This is the minimum stable semantic surface sufficient to constrain future representation without preempting peers.

## Responsibility Consequence
N4-R10 governs RCP-20 using facts from N4-R01..R09.

## Dependency Consequence
Peer contracts remain external; no reverse design of RT-R04/N1/N2/N3/Web/SDK/Agent.

## Authority / SoT / Actual-state Consequence
Contract transport/representation never becomes authority; source owners and RT-R04 remain final owners for their partitions.

## RCP Consequence
`RCP-20 ND-R04 contribution → CLOSED AT CURRENT DESIGN LEVEL`; Full Cross-component Closure not claimed.

## Failure / Offline Consequence
Contract explicitly preserves stale/unavailable/conflicting/partial/pending conditions and private/offline operation.

## Explicit Non-implications
No endpoint, DTO, JSON/Protobuf, REST/gRPC/WebSocket envelope, message schema or delivery guarantee.

## Deferred Implementation Mechanics
Concrete cross-component Contract Design and wire/API binding under later authority.

## Revalidation Trigger
Need to change source ownership, merge identities, add winner law or freeze a high-migration representation.

---

# CID-ND-B2-DAD-011 — RCP-22 complete ns_node-side diagnostics/provenance contribution by federated original ownership

## Decision / Issue
How can Batch 2 complete the ns_node-side RCP-22 contribution without moving accepted N1/N2/N3 evidence into N4 or creating a universal Node diagnostic SoT?

## Context
Batch 1 already accepted bounded N1/N2/N3 provenance/technical diagnostics. N4 is the remaining recovery/health/lifecycle/offline diagnostic producer.

## Alternatives Considered
- **A — N4 aggregates and canonicalizes all Node diagnostics:** rejected; aggregation would become source authority.
- **B — duplicate N1/N2/N3 diagnostic facts into N4-owned facts:** rejected; ownership transfer.
- **C — federated producer model: each N1/N2/N3/N4 owner emits its own evidence; N4 may correlate references only:** selected.

## Selected Design-semantic Result
N4 adds its own recovery/continuity/health/lifecycle diagnostic subjects. The complete ns_node-side RCP-22 contribution is defined as the union-by-reference of independently owned producer contributions, not a single canonical store/state.

## Rationale
Diagnostics need broad coverage without changing the source-of-truth topology.

## Responsibility Consequence
N4-R07/08/09 produce N4 diagnostic facts; N4-R10 governs the stable Node-side contribution. N1/N2/N3 responsibilities remain normative upstream.

## Dependency Consequence
N1/N2/N3 diagnostics are XED/EL/HPL when correlated; no N4 SDD over their source fact definitions.

## Authority / SoT / Actual-state Consequence
Original fact owner remains authoritative. Diagnostic aggregation/correlation has no canonicalization effect.

## RCP Consequence
`RCP-22 ns_node-side contribution → COMPLETE AT CURRENT DESIGN LEVEL`; Full Cross-component Closure remains open.

## Failure / Offline Consequence
Diagnostic gaps/staleness/conflicts remain explicit; N4 diagnostic success does not imply source recovery success.

## Explicit Non-implications
No WB diagnostics UI, SDK model, Agent diagnostics, universal diagnostic store/SoT or business-success inference.

## Deferred Implementation Mechanics
Presentation, querying, storage, transport and UI/SDK representation.

## Revalidation Trigger
Any proposal to make N4 or an aggregator final owner of N1/N2/N3 source facts.

---

# CID-ND-B2-DAD-012 — Bounded RCP correlation and accepted upstream preservation

## Decision / Issue
Which non-RCP-20/22 contracts may N4 touch without reopening accepted source semantics or reverse-designing downstream components?

## Context
Authorization permits only narrow RCP-03, RCP-06 and RCP-24 correlation when materially required and requires RCP-04/07/08/19 preservation.

## Alternatives Considered
- **A — expand N4 into general cross-component recovery contract hub:** rejected; scope/authority leakage.
- **B — ignore needed reconnect/intervention/intent correlations:** rejected; recovery provenance would be incomplete.
- **C — bounded reference/correlation only:** selected.

## Selected Design-semantic Result
RCP-03 contributes Participant/Presence/reconnect refs only; RCP-06 contributes recovery/resume/intervention coordination refs only; RCP-24 contributes receiving-side Human/SDK intent correlation only. RCP-04/07/08/19 are reference/re-observation inputs only.

## Rationale
N4 requires correlation context but not ownership of peer semantics.

## Responsibility Consequence
N4-R01/R04/R05/R06/R09 carry bounded references; no new source-side responsibilities are created.

## Dependency Consequence
These contracts are ACD/XED/EL/HPL; no reverse SDD.

## Authority / SoT / Actual-state Consequence
RT-R01, RT-R03, N1, N2, N3, S9 and downstream WB/SDK owners remain unchanged.

## RCP Consequence
No additional full cross-component closure is claimed.

## Failure / Offline Consequence
Missing peer references remain unknown/unavailable; N4 does not infer remote state.

## Explicit Non-implications
No redesign of Presence, intervention semantics, Human/SDK interaction model, readiness, Attempt, Effect or Desired Configuration.

## Deferred Implementation Mechanics
Other component/SDK internal and Contract designs.

## Revalidation Trigger
Any need to decide another owner's source semantics for N4 coherence.

---

# CID-ND-B2-DAD-013 — Shared Foundation consumption, secret/redaction and private/offline neutrality

## Decision / Issue
How should N4 reuse accepted Foundation capabilities and preserve security/privacy without creating a Node-local Foundation or public dependency?

## Context
N4 requires temporal/status/diagnostic/provenance/context/representation/network/secret/redaction/compatibility/bootstrap mechanics, all already present in accepted Shared Foundation.

## Alternatives Considered
- **A — create N4-specific common primitives:** rejected as parallel Foundation duplication.
- **B — make Foundation diagnostic/storage mechanics source authority:** rejected; Foundation is authority-neutral.
- **C — consume accepted Foundation semantics while keeping N4 Product facts local and redacted:** selected.

## Selected Design-semantic Result
N4 consumes accepted Bootstrap Configuration Acquisition, Diagnostic/Technical Observation, Temporal & Freshness, Operation Correlation & Provenance Context, Semantic Representation & Serialization, Network Invocation Mechanics, Technical Status & Uncertainty, Governed Context Propagation, Secret Reference, Sensitive-data Redaction, Compatibility & Conformance and conditional accepted delivery/storage mechanics where applicable.

## Rationale
No new reusable semantic is required; Foundation mechanics already close cross-cutting pressure.

## Responsibility Consequence
N4 responsibilities define Product facts; Foundation only realizes common mechanics.

## Dependency Consequence
Foundation use does not create Product Authority SDD or cycles.

## Authority / SoT / Actual-state Consequence
Foundation transport/storage/diagnostics never become source SoT. Secret Reference remains distinct from Secret Material.

## RCP Consequence
RCP-20/RCP-22 gain consistent temporal/status/provenance/redaction/representation semantics.

## Failure / Offline Consequence
Core semantics work in private/offline deployment without mandatory public Internet/SaaS/cloud control plane; degraded mode never relaxes redaction/privacy.

## Explicit Non-implications
No provider/vendor/library, public service, database, protocol or secret-store selection.

## Deferred Implementation Mechanics
Concrete Foundation provider bindings and local realization after implementation readiness.

## Revalidation Trigger
Discovery of a mandatory reusable semantic missing from accepted Foundation or pressure to duplicate Foundation locally.

---

# CID-ND-B2-DAD-014 — Compatibility, migration and conformance boundaries

## Decision / Issue
What must remain invariant as N4/RCP-20/RCP-22 evolve or migrate?

## Context
Recovery evidence may outlive implementation/provider/representation changes; history/source attribution and non-collapse must survive migration.

## Alternatives Considered
- **A — treat recovery evidence as ephemeral implementation detail:** rejected; violates history/compatibility obligations.
- **B — freeze physical representation/provider:** rejected high-migration lock-in.
- **C — preserve semantic identities/ownership/history/status/context while allowing conformant realization changes:** selected.

## Selected Design-semantic Result
N4 evolution preserves N4/R4/source identity distinctions, source owner/revision/provenance, request/result and participation/outcome distinctions, uncertainty/conflict semantics, governed/privacy context, non-destructive history, offline/private correctness and RCP non-collapse. Accepted five evolution classes apply.

## Rationale
Semantic compatibility, not physical stability, is the architecture requirement.

## Responsibility Consequence
N4-R10 governs compatibility/conformance across all N4 responsibilities.

## Dependency Consequence
Provider/storage/transport changes do not alter semantic dependencies if contracts remain conformant.

## Authority / SoT / Actual-state Consequence
Migration cannot create a new winner, duplicate owner or projection-to-SoT promotion.

## RCP Consequence
RCP-20/RCP-22 carry compatibility/conformance context and revalidation boundaries.

## Failure / Offline Consequence
Unsupported/migration-required historical evidence remains explicit rather than silently coerced or dropped.

## Explicit Non-implications
No mandatory version number, schema migration tool, storage engine or compatibility implementation.

## Deferred Implementation Mechanics
Physical versioning/migration tooling, data conversion and deployment sequencing.

## Revalidation Trigger
Semantic identity/ownership change, historical loss, incompatible status meaning, mandatory lock-in or authority migration.

---

# CID-ND-B2-DAD-015 — Typed dependency model and acyclic hard SDD graph

## Decision / Issue
How should N4 dependencies be classified so source re-observation/reconciliation feedback does not masquerade as semantic-definition recursion?

## Context
N4 consumes N1/N2/N3 and RT-R04 evidence repeatedly. Treating all evidence flows as SDD would create false cycles and obscure source ownership.

## Alternatives Considered
- **A — classify every runtime/evidence flow as SDD:** rejected; false cycles/authority ambiguity.
- **B — omit dependency classification:** rejected; cannot prove derivability.
- **C — SDD only for semantic-definition prerequisites; ACD/EL/HPL/XED for context/evidence/history/external feedback:** selected.

## Selected Design-semantic Result
Candidate §25 defines the N4 hard SDD graph with topological order:
```text
N4-R01
→ N4-R02
→ N4-R08
→ {N4-R03, N4-R04}
→ {N4-R05, N4-R06}
→ N4-R07
→ N4-R09
→ N4-R10
```
Source-owner results and RT-R04 evidence enter through XED/EL/HPL/ACD.

## Rationale
Semantic-definition dependency and runtime evidence feedback are different architecture relations.

## Responsibility Consequence
N4 can react to new source evidence without redefining source semantics or introducing circular ownership.

## Dependency Consequence
```text
Hard Internal SDD Graph → ACYCLIC
Unresolved Semantic-definition Cycle → 0
Authority Cycle → NONE
Circular Actual-state Ownership → NONE
```

## Authority / SoT / Actual-state Consequence
No feedback edge transfers final ownership or makes N4 definition depend on source outcome success.

## RCP Consequence
RCP-20/RCP-22 correlation remains evidence linkage rather than shared source ownership.

## Failure / Offline Consequence
Missing/delayed source evidence affects available observations, not the semantic definition of N4 responsibilities.

## Explicit Non-implications
No event bus, callback topology, workflow DAG, process dependency, storage graph or implementation scheduler.

## Deferred Implementation Mechanics
Physical calls/messages/storage, dependency injection and execution scheduling.

## Revalidation Trigger
Any new SDD edge causing a cycle, duplicate final owner, or requirement that feedback define the upstream source subject itself.

---

# DAD / MDE Classification Audit

```text
DAD Count
→ 15

DAD IDs
→ CID-ND-B2-DAD-001..015

Owner-reserved MDE disguised as DAD
→ 0

New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

No DAD selects fail-open/fail-closed Product policy, latest/local/central/source-priority/majority winner, cross-source merge law, authoritative synchronization direction, universal replay/retry/cancellation/rollback/compensation, protected-effect reversal, exactly-/at-most-/at-least-once, cross-Tenant recovery semantics, mandatory database/storage/event store, queue/broker/scheduler/workflow/recovery/reconciliation/replay engine, public SaaS/cloud control plane, provider/protocol/framework/storage lock-in, major universal identity namespace or new Product capability.

```text
DAD Evidence Status
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE WITH CANDIDATE
```
