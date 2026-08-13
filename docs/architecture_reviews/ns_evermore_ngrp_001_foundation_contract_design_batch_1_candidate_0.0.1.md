# NGRP-001 — Foundation Contract Design / Batch 1 Candidate

## Authority Metadata

- **Program / Phase:** `NGRP-001 — Foundation Contract Design / Batch 1`
- **Authorization Scope:** `FOUNDATION_CONTRACT_DESIGN_ONLY / BATCH_1 / FOUNDATION_STABLE_ENTRY_AND_REUSABLE_CONTRACT_SEMANTICS_SYNTHESIS`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `e36d4c8cb48234983d4acca8ef6674025f711ded`
- **Recovered Global State:** `GAC-EPOCH-0033`
- **Producing-session Authority:** bounded Foundation Contract semantic design only
- **Global Acceptance Authority:** `NOT HELD`
- **Candidate Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`

This artifact defines language-neutral Stable Entry semantics and reusable Foundation Contract semantics for the 14 globally accepted Shared Foundation capabilities. It does **not** define Foundation Modules, Provider interfaces, Provider selection, APIs, schemas, classes, packages, processes, services, deployment topology or implementation.

---

# 1. Repository Recovery

## 1.1 Recovery Coordinates

```text
Actual Branch HEAD at fresh recovery
→ e36d4c8cb48234983d4acca8ef6674025f711ded

Current Global State
→ GAC-EPOCH-0033

State Verified Through HEAD
→ 4b889719b26571c1935bdf3f9944e4e89214505f

State-to-HEAD Delta
→ exactly 1 commit
→ e36d4c8cb48234983d4acca8ef6674025f711ded
→ docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md only

Delta purpose
→ recovery-authority repair after GAC-EPOCH-0032 omitted mandatory Current Required Read Set

Delta classification
→ EXPECTED_GOVERNANCE

Architecture semantic change
→ NONE

Unexpected working-branch drift
→ NONE

Unauthorized progression
→ NONE
```

`GAC-TR-0043` confirms that the prior stopped Foundation Contract session made no producing mutation and that the same Contract Design authorization resumes unchanged.

## 1.2 Recovery Gate

```text
Architecture Constraint Derivation
→ GLOBAL_CLOSED / COMPLETE

Project Architecture
→ 0.0.3 / GLOBAL_ACCEPTED / NORMATIVE / CURRENT
→ GLOBAL_CLOSED / COMPLETE

Five-component Internal Architecture Boundaries
→ GLOBAL_ACCEPTED / NORMATIVE

Runtime Responsibility Architecture
→ GLOBAL_CLOSED / COMPLETE

Shared Foundation Architecture
→ GLOBAL_CLOSED / COMPLETE

Shared Foundation Architecture Exhaustion
→ SATISFIED

Foundation Contract Design Readiness
→ SATISFIED

Accepted Foundation Capabilities
→ 14 / NORMATIVE

Accepted Foundation DAD
→ SFA-B1-DAD-001..010 / GLOBAL_ACCEPTED

Decision Registry
→ 0.0.12 / CURRENT / NORMATIVE

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Owner-reserved Unresolved Decision
→ 0

Blocking Item
→ NONE

Known Drift
→ NONE

Current Authorized Phase
→ Foundation Contract Design / Batch 1

Recovery Gate
→ PASS
```

## 1.3 Current Required Read Set Consumed

The complete Repository-backed Current Required Read Set embedded in `GAC-EPOCH-0033` was consumed before design:

1. `docs/ns_evermore_genesis_constitution_0.0.1.md`
2. `docs/governance/ns_evermore_governance_0.0.2.md`
3. `docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md`
4. `docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md`
5. `docs/governance/decisions/ns_evermore_decision_registry_0.0.12.md`
6. `docs/ns_evermore_nse_constraints_index_0.0.5.md`
7. `docs/nse_constraints/ns_evermore_nse_012_0.0.1.md`
8. `docs/ns_evermore_project_architecture_0.0.3.md`
9. `docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_five_component_internal_architecture_boundaries_candidate_0.0.1.md`
10. `docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_candidate_0.0.1.md`
11. `docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_global_acceptance_0.0.1.md`
12. `docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_exhaustion_shared_foundation_readiness_assessment_0.0.1.md`
13. `docs/architecture_reviews/ns_evermore_ngrp_001_shared_foundation_architecture_batch_1_candidate_0.0.1.md`
14. `docs/architecture_reviews/ns_evermore_ngrp_001_shared_foundation_architecture_batch_1_dad_evidence_0.0.1.md`
15. `docs/architecture_reviews/ns_evermore_ngrp_001_shared_foundation_architecture_batch_1_global_acceptance_0.0.1.md`
16. `docs/architecture_reviews/ns_evermore_ngrp_001_shared_foundation_architecture_exhaustion_foundation_contract_readiness_assessment_0.0.1.md`
17. `docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md`

High-sensitivity exact evidence was additionally consumed for Tenant Authority/SoT, IAM, Policy, Organization Authority/SoT, Runtime Actual-state, Platform Trust, Configuration, Z3 configuration/Actual-state/SDK DAD, Runtime correlation DAD and the Internationalization/Localization Owner capability decision.

---

# 2. Accepted Upstream That This Design Preserves

```text
Shared Foundation != sixth Product Component
Foundation Contract != Product Authority
Foundation Contract != Product SoT
Foundation Contract != Runtime Actual-state Owner
Provider API != Foundation Contract
Physical Representation != Semantic Contract
Context Consumption != Context Authority
Provider Replacement != Semantic Change automatically

Tenant Authority / native Tenant SoT → ns_server
IAM / Principal Semantic Authority → ns_server
Policy Semantic Authority → ns_server
Organization Semantic Authority → ns_server
Organization factual SoT → one final SoT per bounded semantic partition
Platform Security / Trust Semantic Authority → ns_server
Managed Runtime Configuration Authority / Desired-state SoT → ns_server
Configuration item meaning → configured capability owner
Applied Configuration Actual-state → applicable bounded runtime owner
Runtime Actual-state → one final owner per bounded runtime assertion
```

The 24 accepted Runtime Stable Contract pressures remain runtime/domain contracts. Foundation Contract semantics may be consumed by them but do not absorb them.

---

# 3. Foundation Contract Design Principles

1. **Semantic subject before representation.** Contract identity is the reusable meaning consumers depend on, never a Python/TypeScript type, JSON/Protobuf shape, database object, endpoint or provider API.
2. **Stable Entry before realization.** Stable Entry identifies the authority-neutral capability entrance and consumer dependency, never an import path/function/class/service.
3. **Contract stability does not create authority.** A stable reusable semantic boundary remains mechanically authoritative only for its own Foundation semantics.
4. **Failure is bounded to the Foundation operation.** Technical failure/uncertainty does not automatically become business, Trust, Policy, Admission or domain failure.
5. **Evidence preserves provenance without canonicalization.** Collection, transport, cache, storage or observation does not elevate evidence to Product truth.
6. **Provider conformance is semantic.** Providers conform to the Contract; the Contract never inherits provider-specific optional behavior by default.
7. **Offline/private is a Contract property.** Core semantics cannot require public Internet, public SaaS, public registries, cloud telemetry or public secret management.
8. **Cross-contract reuse is explicit.** One Contract consumes another Contract's semantics instead of duplicating definitions.
9. **Domain/runtime contracts stay external.** Foundation mechanics may support Admission, HITL, Notification, Trial, Node Effect, Discovery and other domain contracts without acquiring their meaning.
10. **No implementation-defined escape.** Every material semantic question is closed here or delegated to a named downstream authority that is legally allowed to decide realization rather than semantics.

---

# 4. Contract Identity / Decomposition Method

A material Foundation Contract exists when a reusable semantic subject has a distinct consumer dependency, obligations, guarantees/non-guarantees, failure model, evolution/conformance boundary and enough cohesion to evolve independently without becoming a Provider or Module concern.

The design deliberately does **not** force `14 capabilities = 14 contracts`.

Result:

```text
Accepted Foundation Capabilities
→ 14

Derived Material Foundation Contracts
→ 15

Reason for difference
→ Capability 12 contains two cohesive but independently evolvable Contract subjects:
   Secret Reference semantics
   Sensitive-data Redaction semantics

New Foundation Capability
→ 0

Removed Foundation Capability
→ 0

Orphan Contract
→ 0
```

`Secret Reference` and `Sensitive-data Redaction` remain one accepted Foundation capability and one capability-level Stable Entry pressure. The split is Contract semantic decomposition only.

Telemetry and Health Observation remain one Contract because accepted SFA architecture already establishes one cohesive technical-observation purpose. Temporal, Correlation, Status and Governed Context remain distinct because accepted `SFA-B1-DAD-005` explicitly prevents their collapse. Diagnostics remains distinct from Telemetry to avoid a universal Observability/Runtime-state contract.

Document-local labels `C01..C15` below are navigation labels only and are **not** a new stable identifier namespace. Stable Contract identity is the semantic Contract name + semantic subject + owning accepted Foundation capability; no external identifier/version syntax is selected.

---

# 5. Contract Inventory

| Local | Contract Name / Stable Semantic Identity | Owning Accepted Foundation Capability | Semantic Subject |
|---|---|---|---|
| C01 | **Bootstrap Configuration Acquisition Contract** | Bootstrap Configuration Loading | source-neutral bootstrap configuration acquisition, validation and load evidence |
| C02 | **Diagnostic Occurrence & Delivery Evidence Contract** | Structured Diagnostics & Logging | producer-originated diagnostic occurrence and bounded delivery evidence |
| C03 | **Technical Observation & Health Evidence Contract** | Technical Telemetry & Health Observation | source-originated technical observation/health evidence, freshness and sink-neutral delivery |
| C04 | **Temporal & Freshness Contract** | Temporal & Freshness Primitives | temporal quantities, deadlines/expiry/freshness/staleness and clock uncertainty |
| C05 | **Operation Correlation & Provenance Context Contract** | Operation / Correlation / Provenance Context | operation/attempt/dispatch/effect/delegation/composition/recovery lineage carriage |
| C06 | **Semantic Representation & Serialization Contract** | Language-neutral Representation & Serialization Mechanics | semantic-preserving encode/decode/representation capability and explicit unsupported/unmapped state |
| C07 | **Network Invocation Mechanics Contract** | Network Client Mechanics | provider-neutral transport/client invocation and bounded transport evidence |
| C08 | **Cache Access Mechanics Contract** | Cache Client Mechanics | hit/miss/stale/unavailable cache access mechanics without source-truth inference |
| C09 | **Durable Storage Access Mechanics Contract** | Storage Client Mechanics | provider-neutral durable access/persistence evidence without domain repository semantics |
| C10 | **Technical Status & Uncertainty Contract** | Error / Status / Uncertainty Primitives | common technical uncertainty vocabulary and extension/non-collapse rules |
| C11 | **Governed Context Propagation Contract** | Governed Context Propagation | carriage/provenance/applicability of Tenant/Organization/Principal/Policy/Trust context references |
| C12 | **Secret Reference Contract** | Secret Reference / Sensitive-data Redaction | reference-vs-material distinction, resolution applicability/evidence and provider-neutral reference semantics |
| C13 | **Sensitive-data Redaction Contract** | Secret Reference / Sensitive-data Redaction | sensitivity marking and disclosure/redaction semantics independent of sink/provider |
| C14 | **Compatibility & Conformance Contract** | Compatibility & Conformance Mechanics | shared classification/evidence/comparison mechanics while final judgement remains subject owner |
| C15 | **Localization Presentation Contract** | Internationalization / Localization Presentation Mechanics | language-neutral presentation identity, locale application/resource lookup and explicit missing/unsupported behavior |

---

# 6. 14 Capability → Contract Coverage Matrix

| Accepted Foundation Capability | Covering Contract(s) | Coverage |
|---|---|---|
| Bootstrap Configuration Loading | C01 | COVERED |
| Structured Diagnostics & Logging | C02 | COVERED |
| Technical Telemetry & Health Observation | C03 | COVERED |
| Temporal & Freshness Primitives | C04 | COVERED |
| Operation / Correlation / Provenance Context | C05 | COVERED |
| Language-neutral Representation & Serialization Mechanics | C06 | COVERED |
| Network Client Mechanics | C07 | COVERED |
| Cache Client Mechanics | C08 | COVERED |
| Storage Client Mechanics | C09 | COVERED |
| Error / Status / Uncertainty Primitives | C10 | COVERED |
| Governed Context Propagation | C11 | COVERED |
| Secret Reference / Sensitive-data Redaction | C12 + C13 | COVERED |
| Compatibility & Conformance Mechanics | C14 | COVERED |
| Internationalization / Localization Presentation Mechanics | C15 | COVERED |

```text
Capability Contract Coverage
→ 14 / 14 / 100%

Uncovered Capability
→ 0

Orphan Contract
→ 0
```

---

# 7. Stable Entry Semantic Coverage

Stable Entry is the semantic point from which a consumer may rely on an accepted capability. It is not a class, method, package, endpoint, registry or process.

| Capability | Contract-level Stable Entry Semantics |
|---|---|
| Bootstrap Configuration Loading | consumer requests source-neutral acquisition/validation of bootstrap configuration and receives bounded load/evidence semantics without depending on source format/provider |
| Diagnostics & Logging | producer records a diagnostic occurrence with provenance/correlation/sensitivity semantics and treats delivery evidence separately from the source operation outcome |
| Telemetry & Health | producer records a technical observation/health evidence under explicit provenance/freshness and receives bounded sink/delivery semantics without transferring source ownership |
| Temporal & Freshness | consumer obtains/interprets temporal quantities, deadline/expiry/freshness/staleness and uncertainty independent of clock provider/format |
| Correlation / Provenance | consumer establishes/propagates lineage relationships among accepted operation/attempt/delegation/etc. subjects without assuming a physical identifier format |
| Representation & Serialization | consumer requests semantic-preserving representation transformation under an explicitly supported representation capability and receives explicit unsupported/unmapped evidence where preservation cannot be established |
| Network Client | consumer expresses a bounded transport/client invocation intent to an abstract destination/provider reference with applicable deadline/security context and receives transport-level evidence only |
| Cache Client | consumer performs acceleration-store access and receives HIT/MISS/STALE/UNAVAILABLE or applicable bounded evidence without inferring source existence/currentness |
| Storage Client | consumer performs durable-access intent and receives persistence/access evidence without inferring business/domain success or Source-of-Truth ownership |
| Status / Uncertainty | consumer constructs/interprets common technical uncertainty semantics without converting them into a universal domain state machine |
| Governed Context | consumer attaches/propagates distinct governance contexts with provenance/applicability; context presence never constitutes authentication/authorization/trust |
| Secret Reference / Redaction | consumer manipulates governed secret references and disclosure-managed sensitive output through one capability-level semantic entry; material custody and disclosure authority remain outside |
| Compatibility / Conformance | consumer applies common classification/comparison/evidence mechanics to owner-defined semantic subjects without Foundation becoming final compatibility authority |
| Localization | consumer resolves product-owned presentation from language-neutral semantic/presentation identity plus locale context and receives explicit effective/missing/unsupported resource semantics |

```text
Stable Entry Semantic Coverage
→ 14 / 14 / 100%
```

---

# 8. Common Contract Semantics

## 8.1 Stable Identity and Revision

A Foundation Contract's stable identity is its semantic subject and accepted ownership relationship, not a file name, class name, package, provider, schema or wire shape.

A **Contract Revision** is a change to semantics under the same stable Contract identity. No SemVer scheme, revision syntax, field or package version is selected.

Change classification uses the accepted five classes:

- `CONFORMANCE_ONLY_IMPLEMENTATION_CHANGE`: implementation/provider/layout changes with no Contract semantic change.
- `COMPATIBLE_EVOLUTION`: Contract semantics evolve while all previously supported identity, obligations, guarantees, non-guarantees and interpretation remain valid.
- `EXPLICIT_MIGRATION_REQUIRED`: consumer/provider/persisted/external state or interpretation must transition explicitly while no higher Authority boundary changes.
- `ARCHITECTURE_REVALIDATION_REQUIRED`: stable Contract subject, guarantees/non-guarantees, authority-neutrality, core offline behavior or cross-component semantic meaning changes.
- `OWNER_MDE_REQUIRED`: change moves Authority/SoT/Actual-state, materially changes Principal/Trust/Security/offline fail policy, creates a major permanent identity/external compatibility commitment or high-lock-in commitment.

Unsupported/unknown revisions are explicit; no nearest/current coercion is permitted.

## 8.2 Consumer-visible Operation / Result / Evidence Pattern

This is a semantic pattern, **not** a universal request/response DTO.

Where a Contract represents an operation/query it closes, as applicable:

```text
Intent
Accepted Input semantics
Result semantics
Technical Evidence
Failure Evidence
Uncertainty
Provenance
Freshness / temporal applicability
Partial Result semantics where legitimately meaningful
```

A successful Foundation operation proves only the bounded reusable mechanical result. It does not automatically prove Product/domain success.

## 8.3 Common Technical Status Extension Rule

C10 defines common meanings for:

`UNKNOWN`, `INDETERMINATE`, `MISSING`, `UNAVAILABLE`, `UNREACHABLE`, `STALE`, `CONFLICTING`, `UNSUPPORTED`, `UNMAPPED`, `UNVERIFIED`, `PARTIALLY_APPLIED`, `RECONCILIATION_PENDING`, `PROJECTION_STALE`.

Other Contracts may define cohesive contract-local outcomes such as Cache `HIT/MISS`, but MUST NOT redefine a C10 meaning. A contract-local failure/outcome is not automatically a new universal status.

Permanent non-collapse:

```text
UNKNOWN != FAILED != SUCCESS
UNAVAILABLE != DENIED
UNREACHABLE != UNAUTHORIZED
STALE != CURRENT
MISSING != Empty Domain Value automatically
UNVERIFIED != Trusted
```

## 8.4 Conformance Status

At material Contract level:

- `CONFORMING IMPLEMENTATION`: satisfies every applicable mandatory semantic obligation for its declared supported Contract scope and does not violate a non-goal/non-absorption rule.
- `NON_CONFORMING IMPLEMENTATION`: violates a mandatory semantic, silently collapses required uncertainty, leaks provider-specific meaning through the stable boundary, breaks authority-neutrality/offline/security requirements or claims support it cannot semantically preserve.
- `UNKNOWN CONFORMANCE`: available evidence is insufficient to establish conforming/non-conforming status.
- `UNSUPPORTED CAPABILITY/CASE`: a bounded operation/revision/representation case is outside the declared supported scope where the Contract permits bounded support; it must be explicit and cannot masquerade as conformance.

`PARTIAL_CONFORMANCE` is **not** a final conformance state for one material Contract. A realization either conforms for a clearly declared supported Contract scope or it does not; incomplete verification is `UNKNOWN CONFORMANCE`. Aggregate capability reports may state partial coverage across multiple Contracts without redefining per-Contract conformance.

## 8.5 Common Authority / SoT / Actual-state Non-guarantee

No Contract in this artifact guarantees or acquires:

- Tenant/IAM/Policy/Trust/Organization/Product semantic authority;
- Product/domain Source of Truth;
- Runtime final Actual-state ownership;
- Artifact Acceptance or Execution Admission;
- business success;
- source-fact canonicalization.

---

# 9. Per-Contract Semantic Definitions

## C01 — Bootstrap Configuration Acquisition Contract

- **Semantic Subject / Purpose:** reusable acquisition, loading and bounded validation evidence for component-local bootstrap configuration.
- **Owning Capability / Consumers:** Bootstrap Configuration Loading; mandatory `ns_server/ns_runtime/ns_node/ns_agent`, applicable `ns_web/SDK` where bootstrap acquisition exists.
- **Stable Identity:** source-neutral bootstrap configuration acquisition semantics; source format/provider is outside identity.
- **Consumer MUST:** identify the bounded bootstrap purpose and applicable source/context; treat loaded material as component-local bootstrap input; preserve config-item semantic ownership; handle load/validation/uncertainty evidence explicitly; keep Secret Reference distinct from material.
- **Consumer MUST NOT:** treat loader success as Managed Desired state, Applied state, Config Authority or domain validation success; require managed runtime configuration to become alive enough to obtain managed configuration.
- **Foundation Guarantees:** source/provider-neutral acquisition; explicit source provenance; bounded validation/load evidence; no silent unsupported/stale coercion; locally realizable acquisition path.
- **Non-guarantees:** managed configuration lifecycle/rollout, Desired/Applied/Observed reconciliation, config-item semantics, secret-material custody, business correctness.
- **Result/Evidence:** acquired/not-acquired semantic result, source provenance, validation/load evidence and applicable temporal/support evidence.
- **Failure/Unknown:** `MISSING`, `UNAVAILABLE`, `UNREACHABLE`, `STALE`, `UNSUPPORTED`, `INDETERMINATE`, `UNVERIFIED` as applicable; validation failure is bounded Contract failure evidence, not a domain state.
- **Context/Security:** Tenant/Principal/Policy/Trust may govern source access but are consumed, not owned; cross-Tenant source confusion prohibited; sensitive load evidence uses C13.
- **Offline/Private:** a local/private source path must be possible; mandatory central/public configuration service is prohibited for bootstrap correctness.
- **Compatibility/Migration/Conformance:** source/provider replacement is conformance-only when stable semantics remain; source interpretation/state migration is explicit where required.
- **Provider Pressure:** configuration acquisition/source provider must preserve provenance, support/failure mapping and offline path; no provider API selected.
- **Dependencies:** C04 temporal where freshness applies; C05 provenance/correlation where an operation exists; C10 status; C11 governed context; C12 secret-reference carriage; C13 redaction.
- **Representation Independence:** no YAML/TOML/INI/.env/schema/library is Contract identity.
- **Non-goals / Downstream:** push/pull/watch/rollout/module/provider API → Foundation Module/Provider Design or component config authorities as applicable.
- **Revalidation:** Foundation becomes Config Authority/Desired SoT, bootstrap independence is removed or a public-only source becomes mandatory.

## C02 — Diagnostic Occurrence & Delivery Evidence Contract

- **Semantic Subject / Purpose:** producer-originated technical diagnostic occurrence with stable provenance/correlation/sensitivity semantics and separate delivery evidence.
- **Owning Capability / Consumers:** Structured Diagnostics & Logging; all five components, SDK where diagnostics are emitted.
- **Consumer MUST:** preserve producer provenance, applicable operation correlation and sensitivity; distinguish occurrence production from sink delivery; interpret technical severity/category only within documented technical meaning.
- **Consumer MUST NOT:** treat a log as Audit Truth/source fact automatically, sink success as source-operation success, sink failure as source-operation failure, or technical severity as business severity automatically.
- **Guarantees:** stable occurrence meaning, provenance attachment, redaction-aware handling and bounded sink-delivery evidence independent of backend.
- **Non-guarantees:** business audit semantics, canonical source facts, runtime SoT, domain error meaning, notification semantics.
- **Result/Evidence:** diagnostic occurrence acceptance/production evidence plus separately bounded delivery evidence when delivery is observable.
- **Failure/Unknown:** sink `UNAVAILABLE`, `UNREACHABLE`, `INDETERMINATE`, `UNSUPPORTED` as applicable; missing delivery evidence never erases the source occurrence.
- **Context/Security:** Tenant/Principal/governance context is disclosure-sensitive; C13 applies before ordinary sink disclosure; cross-Tenant correlation/leakage prohibited.
- **Offline/Private:** local diagnostic path required; cloud logging optional only.
- **Compatibility/Conformance:** category/provenance/correlation/redaction meaning must remain interpretable across sink/provider replacement.
- **Provider Pressure:** diagnostic sink/provider conforms to occurrence/delivery separation and redaction; no logger/backend API selected.
- **Dependencies:** C04, C05, C10, C11, C13.
- **Representation Independence:** no log line/JSON/logger class/backend format is Contract identity.
- **Downstream/Revalidation:** Module/Provider Design handles sink bindings; revalidate if diagnostics become Audit/source-fact/runtime authority.

## C03 — Technical Observation & Health Evidence Contract

- **Semantic Subject / Purpose:** technical observation/health evidence emission, provenance, freshness and sink-neutral delivery without making aggregation the source owner.
- **Owning Capability / Consumers:** Technical Telemetry & Health Observation; all five, SDK applicable.
- **Consumer MUST:** identify producer/source, preserve freshness/provenance, distinguish observation from source Actual-state and distinguish missing telemetry from source absence.
- **Consumer MUST NOT:** treat metric/trace/health observation as business truth, universal health authority, Admission/readiness decision or Runtime SoT.
- **Guarantees:** source-attributable technical observation semantics, explicit freshness/staleness, bounded availability/delivery evidence, sink neutrality.
- **Non-guarantees:** component health final Actual-state, business status, policy/trust/admission outcome.
- **Result/Evidence:** observation accepted/recorded semantics, producer provenance, freshness and bounded delivery/collection evidence.
- **Failure/Unknown:** `UNAVAILABLE`, `UNREACHABLE`, `STALE`, `INDETERMINATE`, `UNVERIFIED`; partial observation evidence must remain explicit and cannot imply source completeness.
- **Context/Security:** Tenant/privacy/redaction mandatory; sensitive telemetry follows C13; collection never authorizes disclosure.
- **Offline/Private:** locally operable/private sink path; mandatory cloud telemetry prohibited.
- **Compatibility/Conformance:** observation/health categories and provenance/freshness interpretation survive provider changes.
- **Provider Pressure:** telemetry/health sink/collector must not canonicalize source state and must preserve evidence/failure semantics.
- **Dependencies:** C04, C05, C10, C11, C13.
- **Representation Independence:** no OTel/metrics/trace SDK/schema is Contract identity.
- **Revalidation:** collector/aggregator proposed as final component/runtime Actual-state owner.

## C04 — Temporal & Freshness Contract

- **Semantic Subject / Purpose:** instant/occurrence-time pressure, duration, deadline, expiry, freshness, staleness, temporal comparison and clock uncertainty.
- **Consumers:** all five + SDK.
- **Consumer MUST:** preserve distinction between source time, observation time and local acquisition time where applicable; propagate uncertainty; use owner-defined freshness/deadline policy rather than inventing domain policy.
- **Consumer MUST NOT:** use latest/highest timestamp as conflict winner automatically; infer source-time authority from local clock; infer timezone from locale.
- **Guarantees:** stable temporal quantity/comparison semantics and explicit clock/freshness uncertainty independent of time provider/format.
- **Non-guarantees:** scheduling/business deadline policy, reconciliation winner, source event authority, truth ordering.
- **Result/Evidence:** temporal quantity/comparison result plus uncertainty/source/freshness evidence where applicable.
- **Failure/Unknown:** `UNKNOWN`, `INDETERMINATE`, `UNAVAILABLE`, `STALE`, `CONFLICTING`, `UNSUPPORTED` where temporal evidence cannot establish the requested interpretation.
- **Context/Security:** temporal evidence may be consumed by Trust/Admission but never decides them.
- **Offline/Private:** local/private time source path; public NTP/cloud time not mandatory.
- **Compatibility:** semantic units/relationships/freshness meaning remain stable; physical timestamp/timezone representation may evolve.
- **Provider Pressure:** time-source provider must expose uncertainty/availability needed by the semantic Contract and cannot become source-time authority.
- **Dependencies:** C10 only for common status semantics; other Contracts depend on C04, not vice versa.
- **Representation Independence:** no timestamp format/time library/NTP/database-clock choice.
- **Revalidation:** time becomes conflict/authority winner or public time service becomes correctness dependency.

## C05 — Operation Correlation & Provenance Context Contract

- **Semantic Subject / Purpose:** stable lineage/correlation relationships among Role/Role Instance where applicable, operation, attempt, dispatch/effect, Agent delegation, Multi-Agent composition, Automation parent/callee, HITL response, intervention, trial, Notification delivery and recovery/reconciliation.
- **Consumers:** all five + SDK.
- **Consumer MUST:** keep operation and attempt distinct; preserve parent/callee/delegation/effect relationships where applicable; preserve producer/source ownership; treat missing/unmapped lineage explicitly.
- **Consumer MUST NOT:** equate trace/correlation identity with Product semantic identity, Principal identity or operation ownership; infer authority from correlation possession.
- **Guarantees:** representation-neutral lineage relationship semantics and provenance carriage; locally generatable/propagatable semantics.
- **Non-guarantees:** operation lifecycle/outcome, domain meaning, identity namespace format, uniqueness algorithm, Human Task/Notification/Trial semantics.
- **Result/Evidence:** established/carried relationship evidence and provenance; no universal event envelope.
- **Failure/Unknown:** `MISSING`, `UNMAPPED`, `UNVERIFIED`, `CONFLICTING`, `UNKNOWN`, `INDETERMINATE` as applicable.
- **Security:** correlation is Tenant/disclosure-sensitive; cross-Tenant joining prohibited absent applicable authorization.
- **Offline/Private:** no public identity/correlation service requirement.
- **Compatibility/Migration:** lineage meaning is compatibility-sensitive; physical ID replacement is conformance-only only when identity relationships remain interpretable; major permanent namespace commitment requires revalidation/MDE.
- **Provider Pressure:** no external provider required; replaceable implementation seam only.
- **Dependencies:** C04 where temporal evidence applies; C10; C11 for governance context separation.
- **Representation Independence:** no UUID/Snowflake/database ID/PID/host/URL/trace format.
- **Revalidation:** Foundation becomes operation owner or a major external identity namespace is frozen.

## C06 — Semantic Representation & Serialization Contract

- **Semantic Subject / Purpose:** encode/decode/representation mechanics that preserve an owning semantic contract without making serialized form canonical truth.
- **Consumers:** all five + SDK.
- **Consumer MUST:** identify the semantic subject/revision it is representing; treat representation support separately from semantic compatibility; preserve required context/provenance/sensitivity; handle unsupported/unmapped transformation explicitly.
- **Consumer MUST NOT:** treat serializer/codec/schema as Semantic Authority, silently destroy/coerce unsupported meaning or infer that representational round-trip implies semantic validity.
- **Guarantees:** explicit representation capability/support evidence; semantic-preservation expectation for declared supported mappings; no silent unsupported/unmapped coercion.
- **Non-guarantees:** domain semantic correctness, canonical Product representation, source↔visual Authority, universal lossless physical round-trip.
- **Result/Evidence:** encoded/decoded/represented result plus support/mapping/conformance evidence; if semantic preservation cannot be established, no success may be claimed.
- **Failure/Unknown:** `UNSUPPORTED`, `UNMAPPED`, `INDETERMINATE`, `UNVERIFIED`; a silently partial semantic conversion is non-conforming unless the owning domain contract explicitly defines a bounded partial semantic result.
- **Security:** sensitivity/redaction remains independent of codec; C13 applies to disclosure-bound representations.
- **Offline/Private:** required representations/codecs locally usable; no online conversion service.
- **Compatibility/Migration:** semantic compatibility precedes representation compatibility; persisted/external representation transitions may require explicit migration.
- **Provider Pressure:** codec/representation provider must preserve declared semantics and explicit support/failure evidence.
- **Dependencies:** C10, C13; may carry C05/C11 semantics but does not redefine them.
- **Representation Independence:** no JSON/Protobuf/MessagePack/Avro/Pydantic/dataclass/schema technology selected.
- **Revalidation:** one physical form becomes canonical Product semantics or major irreversible format commitment is introduced.

## C07 — Network Invocation Mechanics Contract

- **Semantic Subject / Purpose:** provider-neutral client/transport invocation, destination reference, deadline interaction and transport failure evidence.
- **Consumers:** all components/SDK when a bounded responsibility needs network mechanics; use is not forced.
- **Consumer MUST:** provide destination/invocation intent and applicable deadline/security/governance context; interpret result only as transport/client evidence; own retry/business interpretation externally.
- **Consumer MUST NOT:** treat network success as Trust, authorization, Admission, external business success or SoT transfer; treat `UNREACHABLE` as unauthorized/denied.
- **Guarantees:** bounded invocation/result evidence, deadline relationship, provider-neutral failure semantics and private/local networking support.
- **Non-guarantees:** integration-specific protocol/business semantics, remote authority, retry policy, trust/policy/admission decision.
- **Result/Evidence:** transport invocation outcome, response-availability evidence where applicable, destination/provider provenance and deadline/failure evidence.
- **Failure/Unknown:** `UNREACHABLE`, `UNAVAILABLE`, `INDETERMINATE`, `UNSUPPORTED`; deadline expiry is bounded technical failure evidence, not domain failure.
- **Security:** governed context/secret handling must be preserved; connection/secure-transport success does not establish Product Trust; diagnostic disclosure uses C13.
- **Offline/Private:** private/local targets/providers first-class; public Internet optional by domain only.
- **Compatibility:** provider/transport change is conformance-only only if stable client semantics remain; domain protocol changes remain owner-governed.
- **Provider Pressure:** network/transport provider must map its failures/support to Contract semantics without leaking provider API identity.
- **Dependencies:** C04, C05, C10, C11, C13.
- **Representation Independence:** no HTTP method/REST/gRPC/WebSocket/httpx/aiohttp/requests selection.
- **Revalidation:** provider/transport becomes semantic authority or mandatory public connectivity enters core correctness.

## C08 — Cache Access Mechanics Contract

- **Semantic Subject / Purpose:** acceleration-store access with explicit `HIT`, `MISS`, freshness/staleness and provider availability while preserving source authority.
- **Consumers:** applicable components/SDK only when caching is used.
- **Consumer MUST:** retain source authority/freshness policy; distinguish cache outcome from source/domain existence; preserve Tenant/sensitive boundaries.
- **Consumer MUST NOT:** interpret `HIT` as source-current automatically, `MISS` as source `MISSING`, cache placement as SoT or provider TTL as domain policy automatically.
- **Guarantees:** stable cache access outcomes, freshness evidence where available and provider-neutral unavailability semantics.
- **Non-guarantees:** source currentness/existence, business cache policy/TTL, conflict winner, domain consistency model.
- **Result/Evidence:** `HIT/MISS` contract-local outcome plus cached-value/freshness/provider evidence where applicable; known invalidation may be evidence but does not create a universal domain state.
- **Failure/Unknown:** `STALE`, `UNAVAILABLE`, `UNREACHABLE`, `INDETERMINATE`, `UNSUPPORTED`; `MISS` remains distinct from C10 `MISSING` source evidence.
- **Security:** strict Tenant isolation; cross-Tenant key/content correlation leakage prohibited; C13 applies to diagnostic/output disclosure.
- **Offline/Private:** local/private cache backend possible; cloud cache not mandatory.
- **Compatibility/Migration:** provider replacement may discard/rebuild cache if owner policy permits; any data transition is explicit; source semantics never migrate into cache authority.
- **Provider Pressure:** backend must preserve HIT/MISS/stale/unavailable distinctions and isolation semantics.
- **Dependencies:** C04, C10, C11, C13; C05 where operation correlation is used.
- **Representation Independence:** no Redis/Valkey/Memcached/key/value/schema design.
- **Revalidation:** cache becomes correctness SoT/current-truth authority or public cache becomes mandatory.

## C09 — Durable Storage Access Mechanics Contract

- **Semantic Subject / Purpose:** provider-neutral durable-access/persistence mechanics and technical evidence.
- **Consumers:** `ns_server/ns_node/ns_agent` where applicable; other consumers only when later accepted responsibility requires it.
- **Consumer MUST:** define domain data/SoT/repository semantics outside Foundation; preserve Tenant/security/provenance; distinguish persistence evidence from domain transaction/business success.
- **Consumer MUST NOT:** treat storage placement as Data Authority/SoT/Actual-state owner, persistence success as business success or Storage Contract as repository/ORM/transaction semantics.
- **Guarantees:** bounded durable-access result/evidence, provider availability/failure semantics and explicit indeterminate/partial persistence evidence where the provider cannot prove all requested effects.
- **Non-guarantees:** domain transactions, business consistency, schema/model, retention policy, repository semantics, canonical truth.
- **Result/Evidence:** access/read/write/delete-or-equivalent durable intent is described only semantically; result carries persistence/access evidence and provider provenance without fixing methods.
- **Failure/Unknown:** `MISSING` may describe absence in the bounded storage namespace but is not domain-resource absence; `UNAVAILABLE`, `UNREACHABLE`, `INDETERMINATE`, `PARTIALLY_APPLIED`, `UNSUPPORTED` as applicable.
- **Security:** Tenant isolation/access governance and sensitive data remain owner-governed; Foundation never grants storage authorization.
- **Offline/Private:** locally deployable provider required; public cloud object/database service optional.
- **Compatibility/Migration:** provider/data migration explicit when durable state cannot transparently move; migration must preserve original semantic authority/provenance.
- **Provider Pressure:** backend must expose enough evidence to distinguish success, absence, partial/indeterminate and availability states without imposing provider transaction semantics.
- **Dependencies:** C04 where temporal, C05 where correlation, C10, C11, C13.
- **Representation Independence:** no ORM/SQL/table/object-key/filesystem-path/S3/MinIO/transaction model.
- **Revalidation:** persistence placement is used to claim Product authority or material storage lock-in becomes Contract identity.

## C10 — Technical Status & Uncertainty Contract

- **Semantic Subject / Purpose:** common cross-component technical uncertainty meanings and rules for safe domain extension.
- **Consumers:** all five + SDK.
- **Consumer MUST:** preserve exact common meanings; qualify status to the bounded subject/evidence; translate into domain state only under the domain owner's semantics.
- **Consumer MUST NOT:** build a universal domain state machine from common status; redefine a common status locally; convert UNKNOWN to failure/success or UNAVAILABLE to denied.
- **Guarantees:** stable common vocabulary and non-collapse semantics across implementations/languages.
- **Non-guarantees:** business/domain error taxonomy, authorization/trust decisions, execution outcome, exception/protocol mapping.
- **Result/Evidence:** status itself is evidence about a bounded semantic condition, not resolution of the underlying unknown.
- **Failure/Unknown:** this Contract defines the common vocabulary; contract-local states remain allowed only when they do not redefine common meanings.
- **Security:** status detail disclosure is authorization/redaction-sensitive; an implementation may minimize detail without falsifying the status meaning.
- **Offline/Private:** fully local semantics.
- **Compatibility:** existing common meanings cannot be narrowed/reinterpreted by compatible evolution; adding a new universal status requires Contract revision review and may require architecture revalidation if it changes cross-domain interpretation.
- **Provider Pressure:** none external; replaceable implementation only.
- **Dependencies:** no semantic dependency on another Foundation Contract; other Contracts depend on C10.
- **Representation Independence:** no exception hierarchy/numeric code/HTTP status mapping.
- **Revalidation:** common status is promoted into domain/authorization/trust authority or an existing meaning is changed incompatibly.

## C11 — Governed Context Propagation Contract

- **Semantic Subject / Purpose:** portable carriage of distinct Tenant, Organization, Principal and applicable Policy/Trust context/evidence references with provenance/scope/applicability.
- **Consumers:** all five + SDK.
- **Consumer MUST:** preserve subject separation, provenance, scope and temporal/applicability evidence; validate/interpret context only through owning authorities; treat missing/stale/unverified/unmapped context explicitly.
- **Consumer MUST NOT:** treat presence as authentication/authorization/trust, infer Tenant from Organization, make carried values self-authenticating or allow cross-Tenant leakage.
- **Guarantees:** representation-neutral carriage, subject non-collapse, provenance/applicability preservation and bounded uncertainty semantics.
- **Non-guarantees:** Tenant/Principal registry, IAM, Policy evaluation, Trust decision, Organization meaning, credential/session semantics.
- **Result/Evidence:** propagated/accessed context remains attributable to its source/authority context; carrier success is not semantic validation success.
- **Failure/Unknown:** `MISSING`, `STALE`, `UNVERIFIED`, `UNMAPPED`, `CONFLICTING`, `UNKNOWN`, `INDETERMINATE` as applicable.
- **Security:** strict Tenant isolation and disclosure minimization; Policy/Trust references are evidence references, not grants.
- **Offline/Private:** locally usable carriage and locally verifiable evidence only where upstream owner semantics permit; no public IdP dependency is introduced.
- **Compatibility/Migration:** governance subject meaning/revision provenance preserved; major identity namespace changes follow owner/MDE/revalidation paths.
- **Provider Pressure:** no external provider required.
- **Dependencies:** C04 for applicability/freshness, C10; C13 for disclosure. C05 remains separate and must not become governance identity.
- **Representation Independence:** no JWT/OAuth/OIDC/session cookie/token/credential schema.
- **Revalidation:** carried context becomes Authority/self-authenticating truth or Tenant/Principal/Policy/Trust ownership moves.

## C12 — Secret Reference Contract

- **Semantic Subject / Purpose:** stable distinction and handling of a reference to secret material, including reference scope/provenance, bounded resolution applicability and material-source evidence without making the reference material itself.
- **Owning Capability / Consumers:** capability 12; all five + SDK where secret-reference metadata is used.
- **Consumer MUST:** keep reference and material distinct; supply/apply applicable Tenant/Principal/Policy/Trust context externally; treat resolution permission and material validity as separate owner decisions; prevent reference handling from leaking material.
- **Consumer MUST NOT:** treat possession of a reference as permission to resolve, successful resolution as Trust, reference text as material, or Foundation as secret lifecycle/custody authority.
- **Guarantees:** stable reference-vs-material semantics, provider-neutral unresolved/unavailable evidence and preservation of scope/provenance needed for governed resolution.
- **Non-guarantees:** secret material custody/lifecycle, credential format, encryption, rotation, Trust decision, authorization to resolve/use material.
- **Result/Evidence:** reference handling and optional resolution-request/result evidence are bounded technical evidence; resolved material itself is outside the Contract's stable exposed semantics and must not become ordinary result evidence.
- **Failure/Unknown:** `MISSING`, `UNMAPPED`, `UNAVAILABLE`, `UNREACHABLE`, `UNVERIFIED`, `UNSUPPORTED`, `INDETERMINATE` as applicable; these do not equal Trust/Policy denial automatically.
- **Security:** references may themselves be sensitive; C13 applies to disclosure; cross-Tenant reference confusion prohibited.
- **Offline/Private:** a future local/private material-source path must be possible; public secret manager cannot be mandatory.
- **Compatibility/Migration:** reference semantics remain stable while material provider/credential technology changes; provider/credential migration is explicit where state transitions.
- **Provider Pressure:** conditional secret-material source/resolution provider must preserve reference scope/provenance and bounded failure semantics; no provider interface/store selected.
- **Dependencies:** C04, C10, C11, C13.
- **Representation Independence:** no Vault/KMS/HSM URI/credential/reference format.
- **Revalidation:** Foundation acquires Trust/secret-material lifecycle authority or reference is collapsed into material.

## C13 — Sensitive-data Redaction Contract

- **Semantic Subject / Purpose:** stable sensitivity marking and disclosure/redaction behavior for diagnostics, telemetry, UI/integration evidence and other applicable Foundation outputs.
- **Consumers:** all five + SDK where sensitive output can be exposed.
- **Consumer MUST:** preserve owner-provided sensitivity/disclosure constraints; apply mandatory non-disclosure to explicitly secret material; keep redaction separate from authorization and classification authority; retain enough semantic identity/provenance to avoid misleading output when content is redacted.
- **Consumer MUST NOT:** treat redaction as authorization, remove Tenant/privacy boundaries, expose explicitly secret material through ordinary config/log/telemetry/UI or infer that provider/sink success permits disclosure.
- **Guarantees:** explicitly marked secret/sensitive content is handled without provider-specific disclosure semantics; redaction does not silently change the underlying source fact/semantic identity.
- **Non-guarantees:** universal data-classification authority, Policy/Trust decision, authorization, encryption, DLP system or business privacy policy.
- **Result/Evidence:** redacted/presentation-safe output may carry bounded evidence that disclosure was suppressed/limited without exposing protected material; exact mask/token/string is representation design.
- **Failure/Unknown:** `UNVERIFIED`, `UNSUPPORTED`, `INDETERMINATE` where sensitivity/redaction semantics cannot be established. Unknown generic sensitivity does not grant disclosure; the owning Policy/Privacy authority decides admissible disclosure. Explicit secret material remains non-disclosable through ordinary Foundation output under accepted upstream security rules.
- **Security/Privacy:** cross-Tenant disclosure prohibited; redaction must occur before an ordinary sink/presentation boundary can receive protected content where the Contract applies.
- **Offline/Private:** fully local redaction semantics; no public DLP/classification SaaS dependency.
- **Compatibility:** exact wording/mask may evolve; sensitivity meaning and non-disclosure obligations cannot be weakened by compatible evolution.
- **Provider Pressure:** no external redaction provider required by architecture; sinks/providers must receive only Contract-permitted disclosure.
- **Dependencies:** C10, C11; C12 distinction when secret references/material are involved; C04/C05 only when preserving temporal/provenance evidence.
- **Representation Independence:** no masking syntax/logger filter/UI component selected.
- **Revalidation:** redaction layer becomes Policy/Privacy/Trust Authority or accepted non-disclosure baseline changes.

## C14 — Compatibility & Conformance Contract

- **Semantic Subject / Purpose:** reusable mechanics for comparing revisions/applying accepted change classes and representing conformance evidence without becoming final semantic compatibility authority.
- **Consumers:** all five + SDK.
- **Consumer MUST:** provide the owner-defined semantic subject/revisions/invariants; apply the highest governing class that fits; preserve unknown/unsupported/conflicting evidence; treat migration authorization and MDE as external authority.
- **Consumer MUST NOT:** infer compatibility from version syntax, schema readability, provider identity, compilation or transport success; authorize migration/revalidation/MDE.
- **Guarantees:** stable meanings of the five accepted change classes, revision comparison/evidence mechanics, explicit unsupported/unmapped/unknown outcomes and offline-verifiable conformance semantics.
- **Non-guarantees:** domain compatibility rules, migration approval, architecture acceptance, Owner decision, SemVer/version namespace.
- **Result/Evidence:** classification/evidence result qualified by the semantic owner/subject and available evidence; helper result is not final owner judgement unless the owning domain explicitly adopts it under its authority.
- **Failure/Unknown:** `UNSUPPORTED`, `UNMAPPED`, `UNKNOWN`, `INDETERMINATE`, `CONFLICTING`, `UNVERIFIED` as applicable.
- **Security:** evidence may be sensitive; provenance and C13 disclosure apply.
- **Offline/Private:** core conformance/compatibility evaluation cannot require public registry/service.
- **Migration:** represents owner-established migration requirement; never authorizes execution of migration.
- **Provider Pressure:** no external provider required; replaceable implementation only.
- **Dependencies:** C10, C13; may consume C04/C05 for evidence provenance/applicability.
- **Representation Independence:** no SemVer/package/tag/schema-version field/migration engine.
- **Revalidation:** Foundation becomes universal compatibility authority or creates a major permanent external version commitment.

## C15 — Localization Presentation Contract

- **Semantic Subject / Purpose:** language-neutral product-owned presentation identity, locale application/localized resource lookup and explicit supported/missing behavior while keeping machine semantics independent of text.
- **Consumers:** mandatory `ns_web` + SDK; other components applicable when producing product-owned human-facing messages.
- **Consumer MUST:** retain machine semantic identity separately from localized presentation; provide/derive locale context through an owning presentation policy; keep locale distinct from Tenant/Principal/timezone; preserve redaction/authorization.
- **Consumer MUST NOT:** use localized text as protocol/state/authority/authorization identity, infer timezone/Tenant/Principal from locale or expand this Contract into arbitrary business-content translation.
- **Guarantees:** language-neutral presentation identity, locale-aware resource/presentation mechanics, explicit effective/missing/unsupported resource evidence and local/private resource usability.
- **Non-guarantees:** initial language set, locale identifier standard, tenant-locale policy, automatic translation, business-content translation authority, timezone semantics.
- **Result/Evidence:** localized presentation when an admissible supported resource is available plus effective presentation context; otherwise explicit missing/unsupported/unavailable evidence without erasing the underlying semantic message.
- **Failure/Unknown:** `MISSING`, `UNSUPPORTED`, `UNAVAILABLE`, `UNMAPPED`, `INDETERMINATE`. A fallback locale/resource is **not guaranteed** by the Contract. If an owning presentation policy supplies fallback, the mechanism must preserve the same machine semantic identity and make the effective presentation context distinguishable; no fallback hierarchy is frozen here.
- **Security:** C13 redaction/authorization applies before presentation; localization cannot reveal hidden content.
- **Offline/Private:** supported resources locally deployable; online translation SaaS is not core correctness.
- **Compatibility/Migration:** machine semantic identity is stable; exact wording/translation/resources may evolve compatibly; resource/provider migration must not redefine semantic identity.
- **Provider Pressure:** localization resource/provider must preserve identity/effective-context/missing-support semantics; no gettext/resource format/provider selected.
- **Dependencies:** C10, C13; C04 is independent for timezone/temporal presentation and must not be inferred from locale.
- **Representation Independence:** no locale code format/resource/template/pluralization engine selected.
- **Revalidation:** localized text becomes machine semantic identity, public translation becomes mandatory or localization becomes domain-message authority.

---

# 10. Consumer Obligation Matrix

| Contract group | Consumer-side invariant |
|---|---|
| Config | loader success != Desired/Applied/domain success; bootstrap remains component-local |
| Diagnostics | occurrence != Audit Truth; sink failure != source-operation failure automatically |
| Telemetry | missing/late telemetry != source fact absent/failed |
| Temporal | latest timestamp != winner; uncertainty must remain explicit |
| Correlation | correlation identity != operation owner/Principal identity |
| Representation | representable != semantically valid; unsupported/unmapped cannot be coerced |
| Network | transport success != Trust/Policy/Admission/business success |
| Cache | HIT != source current; MISS != source missing |
| Storage | persistence success != business/domain success/SoT |
| Status | common uncertainty != universal domain state machine |
| Governed Context | presence != authentication/authorization/trust; Tenant != Organization |
| Secret Reference | reference != material; possession != resolution permission |
| Redaction | provider/sink success != disclosure permission |
| Compatibility | version/schema/provider similarity != semantic compatibility |
| Localization | localized text != machine identity; locale != Tenant/Principal/timezone |

---

# 11. Guarantee / Non-guarantee Matrix

All Contracts guarantee only their bounded reusable semantic mechanics, explicit support/failure evidence, representation/provider neutrality where applicable and private/offline correctness path.

They explicitly do **not** guarantee Product Authority, Product SoT, Runtime final ownership, Trust/Policy/Admission, business success or domain lifecycle semantics.

Specific non-guarantees are closed in each C01-C15 section and are normative constraints on downstream Module/Provider design.

---

# 12. Failure / Unknown Semantics Matrix

| Contract | Primary applicable common uncertainty | Important contract-local outcome / non-collapse |
|---|---|---|
| C01 Config | MISSING, UNAVAILABLE, UNREACHABLE, STALE, UNSUPPORTED, INDETERMINATE, UNVERIFIED | validation/load failure remains technical evidence |
| C02 Diagnostics | UNAVAILABLE, UNREACHABLE, INDETERMINATE, UNSUPPORTED | sink failure != source failure |
| C03 Telemetry | UNAVAILABLE, UNREACHABLE, STALE, INDETERMINATE, UNVERIFIED | missing telemetry != source missing |
| C04 Temporal | UNKNOWN, INDETERMINATE, UNAVAILABLE, STALE, CONFLICTING, UNSUPPORTED | no latest/highest-time winner |
| C05 Correlation | MISSING, UNMAPPED, UNVERIFIED, CONFLICTING, UNKNOWN, INDETERMINATE | missing correlation != operation nonexistent |
| C06 Representation | UNSUPPORTED, UNMAPPED, INDETERMINATE, UNVERIFIED | silent semantic loss prohibited |
| C07 Network | UNREACHABLE, UNAVAILABLE, INDETERMINATE, UNSUPPORTED | unreachable != unauthorized |
| C08 Cache | STALE, UNAVAILABLE, UNREACHABLE, INDETERMINATE, UNSUPPORTED | HIT/MISS local; MISS != source MISSING |
| C09 Storage | MISSING, UNAVAILABLE, UNREACHABLE, INDETERMINATE, PARTIALLY_APPLIED, UNSUPPORTED | storage MISSING != domain absence automatically |
| C10 Status | defines common vocabulary | UNKNOWN != FAILED/SUCCESS |
| C11 Context | MISSING, STALE, UNVERIFIED, UNMAPPED, CONFLICTING, UNKNOWN, INDETERMINATE | context presence != authorization |
| C12 Secret Ref | MISSING, UNMAPPED, UNAVAILABLE, UNREACHABLE, UNVERIFIED, UNSUPPORTED, INDETERMINATE | unavailable material != Trust denial automatically |
| C13 Redaction | UNVERIFIED, UNSUPPORTED, INDETERMINATE | unknown classification never creates Foundation disclosure authority |
| C14 Compatibility | UNSUPPORTED, UNMAPPED, UNKNOWN, INDETERMINATE, CONFLICTING, UNVERIFIED | helper cannot invent compatibility |
| C15 Localization | MISSING, UNSUPPORTED, UNAVAILABLE, UNMAPPED, INDETERMINATE | localization missing != semantic message missing |

---

# 13. Context Handling Matrix

| Context | Foundation Contract rule |
|---|---|
| Tenant | carried/consumed where applicable; Authority/SoT remain ns_server; cross-Tenant leakage prohibited |
| Organization | distinct from Tenant; carrier never defines Organization semantics or mapping truth |
| Principal | carried/consumed; native IAM meaning remains ns_server; possession is not authentication |
| Authentication | evidence may be carried but no Foundation Contract authenticates by mere context presence |
| Policy | policy context/evidence reference may be carried; Policy Authority remains ns_server |
| Trust | trust evidence/reference may be carried; Trust Authority remains ns_server; crypto/provider success not Trust |
| Operation/Correlation | C05 lineage is distinct from C11 governance identity |
| Locale | presentation context only; not Tenant/Principal/timezone |

---

# 14. Security / Privacy / Secret Review

Permanent Contract-level rules:

```text
Cross-Tenant leakage → PROHIBITED
Secret Reference != Secret Material
Secret Reference possession != Permission to resolve
Provider success != Permission to disclose
Network success != Trust
Context presence != Authorization
Diagnostic/Telemetry collection != Disclosure permission
Localized presentation != Authorization evidence
Cache/Storage placement != Data Authority
```

C12 and C13 are separate Contracts under one accepted capability so that secret-reference/provider semantics can evolve without turning redaction into secret custody, and redaction/disclosure semantics can evolve without making a secret provider the Privacy/Policy authority.

Generic cryptographic/evidence-verification helpers remain `DEFERRED_FOR_LATER_FOUNDATION_ASSESSMENT`; no cryptographic Contract is created by this Batch.

---

# 15. Offline / Private Contract Review

All 15 Contracts preserve a locally realizable/private semantic path. No Contract requires:

```text
Public Internet
Public SaaS Control Plane
Public Registry
Cloud Telemetry
Public Secret Manager
Online Translation Service
Public Identity / Correlation Service
```

Provider/capability unavailability is explicit and never relaxes Tenant, Policy, Trust, Admission, source-fact or Actual-state semantics.

```text
Offline / Private Contract Review
→ PASS
```

---

# 16. Version / Evolution / Compatibility / Migration Model

## Compatible evolution requires preservation of all of:

- stable semantic subject and Contract identity;
- current Authority/SoT/Actual-state neutrality;
- existing consumer obligations and guarantees/non-guarantees;
- existing status meanings and non-collapse rules;
- Tenant/security/privacy invariants;
- offline/private correctness;
- provider/representation independence.

## Explicit migration is required when:

- persisted/external representation must be transformed;
- provider replacement requires durable state transfer;
- secret-reference/provider metadata changes require governed transition;
- localization resources/identity mapping require transition while machine semantics remain stable;
- consumer interpretation cannot remain transparent even though Architecture authority boundaries remain unchanged.

Architecture revalidation or Owner MDE applies according to §8.1. No version-number syntax is selected.

---

# 17. Provider Conformance Pressure

| Provider-bearing Contract | Future provider semantic obligations |
|---|---|
| C01 Config source | preserve source provenance, bounded validation/load evidence, explicit support/failure, local/private path |
| C02 Diagnostic sink | preserve occurrence-vs-delivery separation, provenance/redaction and sink-failure semantics |
| C03 Telemetry/health sink | preserve producer/freshness semantics; aggregation never becomes source owner |
| C04 Time source | expose sufficient availability/uncertainty; never become source-time/truth authority |
| C06 Codec/representation | preserve declared semantic mappings; explicit unsupported/unmapped; no silent coercion |
| C07 Network transport/client | preserve bounded transport evidence/failure semantics; no domain/trust authority |
| C08 Cache backend | preserve HIT/MISS/stale/unavailable distinctions and Tenant isolation |
| C09 Storage backend | preserve persistence/partial/indeterminate evidence and isolation without repository/transaction semantic takeover |
| C12 Secret material source (conditional) | preserve reference scope/provenance/failure; no Trust/Policy authority or secret lifecycle Contract takeover |
| C15 Localization resource/provider | preserve machine identity, locale/effective-context and missing/unsupported semantics; offline resources possible |

C05, C10, C11, C13 and C14 require replaceable implementation conformance but no named external provider at this architecture level.

Provider API design, registry, selection, fallback, factory, lifecycle and default provider are **not** designed.

---

# 18. Cross-Contract Dependency Graph

Semantic dependency direction:

```text
C10 Technical Status & Uncertainty
  ↑
C04 Temporal & Freshness
  ↑
C05 Correlation/Provenance       C11 Governed Context
  ↑                               ↑
C12 Secret Reference → C13 Sensitive-data Redaction

C01 Config ─────────────┐
C02 Diagnostics ────────┤
C03 Telemetry/Health ───┤
C06 Representation ─────┤ consume applicable lower-level semantics
C07 Network ────────────┤
C08 Cache ──────────────┤
C09 Storage ────────────┤
C14 Compatibility ──────┤
C15 Localization ───────┘
```

The diagram is semantic, not Module dependency architecture. Precise dependencies are listed per Contract.

Rules:

- C10 is the single common definition of common uncertainty; other Contracts do not redefine it.
- C04 is the single temporal/freshness semantic definition where applicable.
- C05 operation lineage and C11 governance context stay separate.
- C12 does not depend on C13 for secret identity; C13 may consume C12's reference/material distinction.
- C02/C03 consume C13 rather than redefining redaction.
- C15 remains independent of C04 for locale/timezone identity even when temporal presentation later consumes time semantics.

```text
Semantic Dependency Cycle Creating Ambiguity
→ 0

God Contract
→ NONE_FOUND
```

---

# 19. Domain / Runtime Contract Non-absorption Review

The following remain explicitly outside Foundation Contracts:

```text
Tenant / IAM / Policy / Trust authority contracts
Business Application / Automation / Agent / Data-Knowledge-ETL semantics
Artifact Acceptance
Execution Admission
Runtime Participant Presence
Node Readiness / Attempt / Effect
Automation Continuation / Event / Composition
Agent Runtime / Provider / Multi-Agent / Delegation
Human Task
Trial
Notification lifecycle/delivery semantics
Managed Desired / Applied configuration domain contract
Recovery/Reconciliation owner semantics
Discovery resource/projection domain semantics
Human/SDK Intent semantics
```

The 24 accepted RCP subjects remain owner-bound runtime/domain contracts. They may consume C04/C05/C06/C10/C11/C12/C13/C14/C15 and client mechanics where applicable, but Foundation does not absorb their semantic ownership.

```text
Domain Contract Absorption
→ 0

Runtime Contract Absorption
→ 0
```

---

# 20. SDK Relationship

The System-level SDK is outside the five Product Components and is neither Product Authority nor Runtime Role. It may consume applicable Foundation Contracts, especially C04, C05, C06, C10-C15, and applicable client mechanics.

```text
SDK Binding != Foundation Contract
SDK Type != Semantic Contract
SDK Request != Admission
SDK Local State != Runtime SoT
```

Concrete SDK language binding/package/API/CLI shape remains later authorized design.

---

# 21. Contract Cohesion / Overfragmentation / God Contract Review

- Diagnostics and Telemetry remain separate: occurrence/evidence vs technical observation/health semantics have different authority risks.
- Telemetry and Health remain combined per accepted SFA cohesion.
- Temporal, Correlation, Status and Governed Context remain separate per accepted DAD.
- Representation/Serialization stays one Contract because encode/decode support and semantic preservation share one consumer purpose.
- Network/Cache/Storage remain independent client-mechanics Contracts because their result/failure/SoT non-guarantees differ materially.
- Secret Reference and Redaction split at Contract level because provider/custody pressure belongs only to the reference/material side, while disclosure/redaction obligations have a distinct consumer/sink security boundary. They remain one capability and share one Stable Entry pressure.
- Compatibility/Conformance remains one mechanics Contract; final domain judgement stays external.
- Localization remains presentation-only and does not merge with Representation or Temporal.

```text
Contract Overfragmentation
→ NONE_FOUND

Duplicate Contract Semantics
→ NONE_FOUND

God Contract
→ NONE_FOUND
```

---

# 22. Named Downstream Module / Provider Pressure

Foundation Module Design later receives realization pressure for all 15 Contract subjects but is not required to map one Contract to one module.

Foundation Provider Design later receives explicit pressure only for the provider-bearing subjects listed in §17. It must derive interfaces/selection/lifecycle from accepted Contract semantics and may not reverse the dependency.

No package/module/class/facade/manager/registry/factory/adapter structure is selected here.

---

# 23. DAD / MDE Summary

Material delegated design decisions are persisted separately as `FCD-B1-DAD-001..008`.

```text
Producing-session DAD
→ 8

New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Missing Foundation Architecture
→ 0
```

No Contract moves Product Authority/SoT/Actual-state ownership, changes Tenant/Principal/Policy/Trust semantics, chooses a material provider/protocol/storage/format lock-in, selects a material offline fail-open/fail-closed policy or creates a major external identity/version commitment.

---

# 24. Foundation Contract Semantic Resolution Matrix

| Dimension | Resolution | Status |
|---|---|---|
| Contract Identity | 15 stable semantic Contract subjects; names/subjects not physical namespace | CLOSED |
| Owning Capability | every Contract traces to one accepted capability | CLOSED |
| Consumer Scope | accepted component/SDK applicability preserved | CLOSED |
| Stable Entry | 14/14 capability-level semantic entries | CLOSED |
| Version / Evolution | five-class model; no version syntax | CLOSED |
| Authority Neutrality | no Product Authority gained | CLOSED / PASS |
| SoT Neutrality | no Product SoT gained | CLOSED / PASS |
| Actual-state Neutrality | no final runtime owner gained | CLOSED / PASS |
| Consumer Obligations | per Contract + matrix | CLOSED |
| Guarantees | bounded reusable semantics only | CLOSED |
| Non-guarantees | authority/domain/business boundaries explicit | CLOSED |
| Result / Evidence | per applicable operation Contract; no universal DTO | CLOSED |
| Failure / Unknown | C10 reuse + contract-local outcomes; no collapse | CLOSED |
| Temporal | C04 single semantic definition; consumed as applicable | CLOSED |
| Tenant | carried/isolated only; Authority remains ns_server | CLOSED |
| Organization | distinct context; Foundation no Organization Authority | CLOSED |
| Principal / Authentication | context/evidence only; IAM Authority remains ns_server | CLOSED |
| Policy | evidence/reference carriage only; no Policy Authority | CLOSED |
| Trust | evidence/reference only; Trust Authority remains ns_server | CLOSED |
| Security / Privacy | isolation/redaction/disclosure boundaries explicit | CLOSED |
| Secret Reference / Material | C12; Ref != Material; material custody outside | CLOSED |
| Serialization / Representation | C06; semantic-before-physical | CLOSED |
| Offline / Degraded | local/private path for all Contracts | CLOSED / PASS |
| Recovery / Reconciliation | Foundation evidence does not own reconciliation outcome | CLOSED |
| Compatibility | C14 + five classes | CLOSED |
| Migration | explicit triggers and owner preservation | CLOSED |
| Conformance | conforming/non-conforming/unknown model | CLOSED |
| Provider Conformance | 10 provider-bearing pressures mapped to Contract subjects | CLOSED |
| Cross-Contract Dependency | explicit acyclic semantic graph | CLOSED |
| Domain Contract Relationship | consumption only; no absorption | CLOSED |
| Runtime Contract Relationship | 24 RCP preserved external | CLOSED |
| SDK Relationship | consumer/binding only; no authority | CLOSED |
| Decision Traceability | NSE/Z2/Z3/RRA/SFA + FCD DAD evidence | CLOSED |
| Revalidation Trigger | common + per-Contract triggers | CLOSED |

```text
Unnamed Deferral
→ 0

Implementation-defined Escape
→ 0
```

---

# 25. Candidate Audit Summary

Detailed audits are persisted separately. Candidate-level result:

```text
Contract Inventory → COMPLETE
Derived Contract Count → 15
14-capability Contract Coverage → 100%
Uncovered Capability → 0
Orphan Contract → 0
Stable Entry Semantic Coverage → 14 / 14
Contract Identity → CLOSED
Consumer Obligations → CLOSED
Guarantees / Non-guarantees → CLOSED
Result / Evidence Semantics → CLOSED where applicable
Failure / Unknown Semantics → CLOSED
Tenant / Principal / Policy / Trust Context → CLOSED where applicable
Security / Privacy / Redaction → CLOSED
Secret Reference / Material Boundary → CLOSED
Offline / Private → PASS
Representation Independence → PASS
Version / Evolution → CLOSED
Compatibility / Migration / Conformance → CLOSED
Provider Conformance Pressure → CLOSED
Provider API Absorption → 0
Domain Contract Absorption → 0
Runtime Contract Absorption → 0
Cross-Contract Dependency → CLOSED
Semantic Dependency Cycle → 0
Contract Overfragmentation → NONE_FOUND
God Contract → NONE_FOUND
Authority Transfer → 0
SoT Transfer → 0
Actual-state Ownership Transfer → 0
Open MDE → 0
Unpersisted Owner Decision → 0
Missing Foundation Architecture → 0
Unnamed Deferral → 0
Implementation-defined Escape → 0
Foundation Module Design Leakage → 0
Foundation Provider Design Leakage → 0
Component Internal Design Leakage → 0
Implementation Planning Leakage → 0
```

---

# 26. Candidate Status / Stop Rule

```text
NGRP-001 Foundation Contract Design / Batch 1
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE

Global Acceptance
→ NOT CLAIMED

Foundation Contract Design Global Closure / Exhaustion
→ NOT CLAIMED

Foundation Module Design Authorization
→ NONE

Foundation Provider Design Authorization
→ NONE

Component Internal Design Authorization
→ NONE

Implementation Authorization
→ NONE
```

After Candidate, DAD evidence, Review/Audit evidence and Handoff evidence are persisted, this producing session stops and returns to the Global Architecture Coordinator.