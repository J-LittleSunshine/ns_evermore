# NGRP-001 — Component Internal Design / ns_server / Batch 8 DAD Evidence

## Authority Metadata

- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Scope:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_8 / CROSS_DOMAIN_RESOURCE_DISCOVERY_PROJECTION_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Boundary:** `S13 — Cross-domain Resource Discovery Projection`
- **Runtime Role:** `SV-R09 — Discovery Projection Participant`
- **Recovered Entry HEAD:** `b4edbd3d6f344c875e43ffaa37c08ac910b3bbf8`
- **Candidate Commit:** `d5966b87ce3725b8b192cd1518c3a4d53601d954`
- **DAD Range:** `CID-SV-B8-DAD-001..023`
- **Owner MDE Created:** `0`
- **Global Acceptance:** `NOT CLAIMED`

All decisions below are delegated architecture decisions inside the exact authorized S13 scope. None changes an accepted Owner-reserved Authority/SoT/Actual-state topology, introduces a new Product capability, freezes a material search/index/provider technology, creates cross-Tenant discovery, or claims full RCP-21 closure.

Common upstream traceability for all DADs includes the Genesis Constitution; Unified Governance 0.0.2; accepted `NSE-001..017`; Project Architecture 0.0.3; accepted Five-component Internal Architecture Boundaries; accepted Runtime Responsibility Architecture; accepted Foundation baseline; ns_server Batch 1..7 Global Acceptances; post-Batch-7 remaining-pressure assessment 0.0.7; Unified Governed Cross-domain Resource Discovery Owner capability decision; `Z2-MDE-014`; and `GAC-TR-0076` Batch-8 authorization.

---

# CID-SV-B8-DAD-001 — Nine-responsibility S13 decomposition and acyclic SDD graph

- **Decision:** decompose S13 into `DP01..DP09`: contribution/source binding; contribution identity; eligibility/category qualification; disclosure qualification; projection entry lifecycle/currentness; generation/rebuild coverage; governed query evaluation; result/aggregate/navigation projection; recovery/history/compatibility/conformance. Hard SDD graph is the Candidate §19 graph and is acyclic.
- **Reason:** source authority binding, S13 Actual-state, disclosure, query/result and rebuild have different ownership/failure/compatibility semantics. Combining them creates a God Module; splitting by technical mechanism would overfragment.
- **Alternatives avoided:** one `Search Center`/`Index Service` responsibility; per-resource-category S13 modules; technical modules by index/query/storage process.
- **Constraint traceability:** `NSE-005/006/009/015/017`; accepted S13 boundary; Unified Discovery owner non-authority rule; prior ns_server SDD taxonomy.
- **Authority impact:** none; no source authority transferred.
- **Actual-state impact:** clarifies DP05/DP06 as the only final S13 projection-state owners for their bounded assertions.
- **Security/privacy impact:** disclosure qualification remains independently reviewable in DP04/DP08.
- **Offline/private impact:** recovery/reconciliation remains explicit without promoting local projection.
- **Compatibility impact:** responsibility meanings, not process/package layout, become compatibility boundaries.
- **Migration impact:** internal realization may migrate if semantic responsibilities and DAG remain preserved.
- **Cross-component impact:** only stable producer/consumer obligations; no other component internals designed.
- **Downstream implications:** later detailed design may map responsibilities to realizations only after preserving this semantic graph.
- **Non-implications:** no package/service/process/index topology.

# CID-SV-B8-DAD-002 — Source Authority Binding precedes projection interpretation

- **Decision:** every usable Discovery Contribution must bind to an identifiable source Resource Owner and preserve source Resource Identity/Reference, Origin Domain and Resource Type before S13 may treat it as projection input.
- **Reason:** projection without source authority binding risks turning ingestion/storage placement into implicit authority.
- **Alternatives avoided:** infer authority from index namespace, producer transport, database ownership, latest arrival or S13 category.
- **Constraint traceability:** `Z2-MDE-014`; source/SoT non-transfer; Owner decision `Discovery Projection != Resource SoT`.
- **Authority impact:** explicitly preserves originating owner.
- **Actual-state impact:** DP01 owns only intake qualification evidence.
- **Security/privacy impact:** Tenant/governance context is preserved before disclosure evaluation.
- **Offline/private impact:** retained binding may remain historical while source reachability becomes unknown.
- **Compatibility impact:** source-owner binding is compatibility-sensitive.
- **Migration impact:** projection migration must not silently rebind authority.
- **Cross-component impact:** all future producers remain resource authorities.
- **Downstream implications:** physical identifiers/transports must carry enough semantics to realize this binding.
- **Non-implications:** S13 does not validate/canonicalize source-resource semantics.

# CID-SV-B8-DAD-003 — Discovery Contribution Identity is distinct from Source Resource Identity

- **Decision:** establish a representation-neutral `Discovery Contribution Identity / Reference` for one S13 contribution lineage, distinct from the source Resource Identity.
- **Reason:** contribution withdrawal, supersession, producer re-observation and historical provenance can evolve independently of the source resource identity/lifecycle.
- **Alternatives avoided:** reuse source ID automatically; use index-document ID; use database PK; create one universal Resource UUID.
- **Constraint traceability:** Global State identity pressure; Unified Discovery domain-identity preservation; `NSE-009/015`.
- **Authority impact:** none; contribution identity creates no resource authority.
- **Actual-state impact:** DP02 owns contribution-lineage facts only.
- **Security/privacy impact:** contribution identity existence is itself disclosure-sensitive.
- **Offline/private impact:** retained contribution lineage remains interpretable offline with explicit currentness uncertainty.
- **Compatibility impact:** lineage continuity must survive compatible evolution.
- **Migration impact:** migration preserves contribution/source correlation.
- **Cross-component impact:** producers need only provide/conform to representation-neutral lineage semantics.
- **Downstream implications:** physical representation remains open.
- **Non-implications:** no universal identifier format/namespace.

# CID-SV-B8-DAD-004 — Preserve source identity/domain/type; no universal Resource namespace

- **Decision:** S13 preserves source Resource Identity/Reference together with Source Owner Reference, Origin Domain and Resource Type/Category; it does not normalize all platform resources into a new authoritative identifier namespace.
- **Reason:** domain identity preservation is Owner-selected and universal identity would be a material cross-domain authority/compatibility commitment.
- **Alternatives avoided:** global Resource UUID, global slug/path, S13 canonical ID, cross-domain registry key authority.
- **Constraint traceability:** Owner decision; State MDE stop boundary; `NSE-006/009/015`.
- **Authority impact:** preserves source domain authority.
- **Actual-state impact:** none beyond correlation.
- **Security/privacy impact:** identity metadata remains qualified before disclosure.
- **Offline/private impact:** source identity is interpretable without public/global registry dependence.
- **Compatibility impact:** source identity changes follow source owner compatibility; S13 correlation must preserve history.
- **Migration impact:** mapping old/new source references must be lineage-preserving, never latest-copy-wins.
- **Cross-component impact:** avoids imposing one identifier regime on Agent/Node/Runtime/Web.
- **Downstream implications:** representation can vary by source domain.
- **Non-implications:** no universal category/resource registry authority.

# CID-SV-B8-DAD-005 — Projection Entry Identity is a distinct S13 concept where lifecycle/history requires it

- **Decision:** define `Discovery Projection Entry Identity` as an S13-owned representation-neutral projection-lineage identity where distinct entry lifecycle/history is materially required; it is not automatically the source Resource ID or Contribution ID.
- **Reason:** a projected representation can be rebuilt, superseded, stale or historically interpreted independently from source identity and contribution lineage.
- **Alternatives avoided:** identify entries solely by source ID, contribution ID, index document ID or database PK.
- **Constraint traceability:** State identity pressure; SV-R09 projection-state ownership; `NSE-009/015`.
- **Authority impact:** projection identity never grants resource authority.
- **Actual-state impact:** DP05 owns entry existence/currentness within S13 only.
- **Security/privacy impact:** technical entry existence does not imply disclosability.
- **Offline/private impact:** retained entry lineage can be qualified stale/unknown offline.
- **Compatibility impact:** entry/source correlation is stable while storage/index technology is replaceable.
- **Migration impact:** reindexing may change physical IDs without changing architecture identity semantics.
- **Cross-component impact:** no source producer changes its Resource Identity.
- **Downstream implications:** physical identity format deferred.
- **Non-implications:** entry identity is not a canonical Resource registry identity.

# CID-SV-B8-DAD-006 — Projection Generation/Rebuild Evidence Identity is distinct from Resource Revision

- **Decision:** where rebuild/history interpretation requires it, one bounded projection generation/rebuild has a representation-neutral Generation/Rebuild Evidence Identity/Reference distinct from resource revisions, contributions and projection entries.
- **Reason:** completeness/coverage and historical rebuild interpretation need a generation subject without pretending the projection generation is a source revision.
- **Alternatives avoided:** infer generation from timestamp, index name, deployment version, source revision or latest rebuild job.
- **Constraint traceability:** Global State rebuild boundary; `Z2-MDE-014`; `NSE-009/015`.
- **Authority impact:** none over source resources.
- **Actual-state impact:** DP06 owns generation/rebuild evidence only.
- **Security/privacy impact:** generation/coverage metadata remains a disclosure surface when exposed.
- **Offline/private impact:** a local generation can remain interpretable without source availability.
- **Compatibility impact:** generation semantics survive provider/index replacement.
- **Migration impact:** migration can create a new projection generation without changing source revision.
- **Cross-component impact:** no producer replay authority created.
- **Downstream implications:** generation mechanics remain detailed-design work.
- **Non-implications:** no blue/green/alias/checkpoint mechanism.

# CID-SV-B8-DAD-007 — SV-R09 owns only bounded projection Actual-state

- **Decision:** final S13/SV-R09 ownership is limited to projection entry lifecycle/currentness, freshness/staleness, bounded completeness/partiality, generation/rebuild state/coverage, projection availability/uncertainty and S13 reconciliation qualification.
- **Reason:** `Z2-MDE-014` requires exactly one final owner per bounded assertion and prohibits aggregation/placement from becoming universal Actual-state authority.
- **Alternatives avoided:** S13 owns source currentness; central discovery owns global resource actual-state; storage/index owns truth.
- **Constraint traceability:** `Z2-MDE-014`; accepted RRA `SV-R09`; accepted S13 boundary.
- **Authority impact:** source semantic authority/SoT unchanged.
- **Actual-state impact:** closes ambiguity for all S13-owned assertions; source assertions remain originating-owner-owned.
- **Security/privacy impact:** query/result visibility does not become authorization authority.
- **Offline/private impact:** local projection can be observed without authority escalation.
- **Compatibility impact:** final-owner semantics cannot change silently under implementation migration.
- **Migration impact:** copied projection data remains projection data.
- **Cross-component impact:** non-server owners remain final owners of their facts.
- **Downstream implications:** telemetry/storage may observe but not own these assertions.
- **Non-implications:** no universal Runtime SoT.

# CID-SV-B8-DAD-008 — Freshness is projection-relative, not source-currentness

- **Decision:** S13 freshness/currentness is qualified relative to explicit accepted contribution/source-observation evidence and S13 projection semantics; `CURRENT` never guarantees current source truth.
- **Reason:** source may change after last observation or be temporarily unreachable.
- **Alternatives avoided:** projection timestamp equals source freshness; successful rebuild equals source freshness; latest observation wins.
- **Constraint traceability:** Owner decision; State freshness non-collapse; Project Architecture temporal/unknown semantics.
- **Authority impact:** preserves source currentness authority.
- **Actual-state impact:** DP05 owns projection freshness only.
- **Security/privacy impact:** stale/unknown qualification cannot be used to infer protected source transitions.
- **Offline/private impact:** stale/unknown local projection remains legitimate if clearly qualified.
- **Compatibility impact:** freshness meaning is stable; numeric TTL is not frozen.
- **Migration impact:** provider replacement must preserve freshness evidence semantics.
- **Cross-component impact:** producer freshness/source facts remain source-owned.
- **Downstream implications:** concrete observation intervals/TTLs deferred.
- **Non-implications:** no universal freshness duration.

# CID-SV-B8-DAD-009 — Completeness is always bounded; partiality is first-class

- **Decision:** only `COMPLETE_FOR_SCOPE` is meaningful, with explicit applicable Tenant, supported category set, known producer set, projection generation, contribution snapshot/source-observation frontier or equivalent declared scope; `PARTIAL/UNKNOWN/INDETERMINATE` remain explicit.
- **Reason:** a universal completeness claim cannot be proven by S13 and would silently turn projection coverage into world-state authority.
- **Alternatives avoided:** global `complete=true`; empty/rebuilt index equals complete platform; missing producer treated as zero resources.
- **Constraint traceability:** State Completeness Scope; Owner partiality requirement; `NSE-004/006`.
- **Authority impact:** no global resource-universe authority.
- **Actual-state impact:** DP06 owns bounded coverage assertions.
- **Security/privacy impact:** consumer-visible coverage metadata is disclosure-qualified.
- **Offline/private impact:** disconnected producers yield partial/unknown rather than false complete.
- **Compatibility impact:** scope dimensions are semantic commitments; exact representation remains open.
- **Migration impact:** a migrated generation must re-establish coverage evidence.
- **Cross-component impact:** absence of future producer contribution does not mean producer has no resources.
- **Downstream implications:** concrete coverage computation deferred.
- **Non-implications:** no exhaustive eternal resource/category catalog.

# CID-SV-B8-DAD-010 — No-result and missing-projection evidence do not prove resource non-existence

- **Decision:** a no-result response means only that no disclosure-qualified matching projection result was established under the stated query/context/coverage/currentness; missing contribution/entry/result never automatically asserts source-resource absence.
- **Reason:** source may be unindexed, stale, unsupported, offline, unauthorized or outside known producer coverage.
- **Alternatives avoided:** zero result = resource absent; missing entry = deleted resource; unknown = absent.
- **Constraint traceability:** Owner decision; Global State query/result and completeness non-collapse.
- **Authority impact:** resource existence remains source-owned.
- **Actual-state impact:** no new source assertion is synthesized.
- **Security/privacy impact:** unauthorized vs absent can remain intentionally non-distinguishable to prevent existence leakage.
- **Offline/private impact:** disconnected/partial projections do not fabricate absence.
- **Compatibility impact:** consumers must preserve no-result semantics across versions.
- **Migration impact:** reindex gaps cannot be interpreted as source deletion.
- **Cross-component impact:** future consumers cannot treat S13 as existence oracle.
- **Downstream implications:** error/result representation deferred.
- **Non-implications:** no source deletion lifecycle.

# CID-SV-B8-DAD-011 — Contribution withdrawal/supersession/revision changes preserve source authority and history

- **Decision:** contribution withdrawal/supersession changes S13 projection participation/lineage only; source revision changes are observed from source-owned evidence; ambiguous continuity remains explicit and S13 never chooses the canonical source revision.
- **Reason:** contribution lifecycle and resource lifecycle are different semantic subjects.
- **Alternatives avoided:** withdrawal=resource delete; newest contribution=canonical revision; S13 resolves source conflicts by timestamp.
- **Constraint traceability:** source-authority preservation; Project Architecture historical interpretation; State contribution/source separation.
- **Authority impact:** no resource lifecycle authority transferred.
- **Actual-state impact:** DP02/DP05 own only contribution/projection lineage/currentness.
- **Security/privacy impact:** historical withdrawn contributions remain protected by disclosure rules.
- **Offline/private impact:** supersession can remain pending/indeterminate until source evidence is available.
- **Compatibility impact:** lineage semantics must survive compatible evolution.
- **Migration impact:** migrations preserve prior contribution history.
- **Cross-component impact:** each producer retains source-revision authority.
- **Downstream implications:** no transport/event semantics selected.
- **Non-implications:** no latest-wins policy.

# CID-SV-B8-DAD-012 — Rebuild/generation state is projection state only

- **Decision:** rebuild has explicit bounded initiation/scope/coverage/failure/supersession/reconciliation evidence; rebuild start does not invalidate prior projection automatically; rebuild finish does not prove source truth fresh or synchronized; active generation is explicit S13 state, not inferred from timestamp/storage placement.
- **Reason:** rebuild is a projection maintenance act, not source replay/migration authority.
- **Alternatives avoided:** latest rebuild wins; rebuild complete = source complete/current; index alias/storage location defines authority.
- **Constraint traceability:** Global State rebuild boundary; `Z2-MDE-014`; MDE stop boundary for global conflict winner.
- **Authority impact:** source authority unchanged.
- **Actual-state impact:** DP06 owns rebuild/generation assertions.
- **Security/privacy impact:** rebuild metadata is disclosure-sensitive when exposed.
- **Offline/private impact:** partial rebuild is validly qualified in isolated deployments.
- **Compatibility impact:** generation semantics remain stable across technology swaps.
- **Migration impact:** reindex/migration establishes new projection evidence, not resource migration authority.
- **Cross-component impact:** producers are not forced into a replay engine.
- **Downstream implications:** full/incremental/cutover/checkpoint algorithms deferred.
- **Non-implications:** no global cutover winner policy is selected; if materially needed later it returns to GAC/MDE classification.

# CID-SV-B8-DAD-013 — Query has its own correlation/context identity and carries governance context

- **Decision:** define a representation-neutral Query Correlation Identity/Reference and architecture-level query context including Tenant, Principal, applicable Organization, Policy/Trust/privacy and bounded scope/category intent where applicable.
- **Reason:** query provenance/history and disclosure qualification require a query subject distinct from a resource identity.
- **Alternatives avoided:** query ID=resource ID; browser/session ID as durable query identity; query syntax defines semantics.
- **Constraint traceability:** RCP-21; Owner auth/Tenant requirements; `NSE-009`.
- **Authority impact:** query handling grants no resource authority.
- **Actual-state impact:** DP07 owns only query/evaluation evidence it originates.
- **Security/privacy impact:** governance context is mandatory for protected discovery.
- **Offline/private impact:** local query evaluation may consume locally available qualified projection.
- **Compatibility impact:** semantic query intent remains stable independent of syntax.
- **Migration impact:** wire/API changes need not alter query semantics.
- **Cross-component impact:** future WB/SDK consumer obligation only; no web internals.
- **Downstream implications:** DSL/API/pagination/sort syntax deferred.
- **Non-implications:** no query language selection.

# CID-SV-B8-DAD-014 — Result is a projection reference with source navigation, not source authority

- **Decision:** define Result Correlation Identity/Reference and require each result to preserve source Resource/Owner/Origin Domain/Type plus projection freshness/coverage/uncertainty and source navigation/correlation where applicable.
- **Reason:** consumers need governed navigation without mistaking result payload for canonical source representation/current state.
- **Alternatives avoided:** result object becomes universal resource DTO/registry; navigation implies operation authorization.
- **Constraint traceability:** Owner decision; Global State query/result non-collapse; RCP-21.
- **Authority impact:** source owner remains final authority.
- **Actual-state impact:** result is derived evidence, not source Actual-state.
- **Security/privacy impact:** result projection is disclosure-qualified.
- **Offline/private impact:** stale/partial results remain usable only with explicit qualification.
- **Compatibility impact:** result/source correlation is stable; wire representation replaceable.
- **Migration impact:** physical index/result schema migration cannot rewrite source identity/provenance.
- **Cross-component impact:** future consumers re-read/navigate source under applicable authorization.
- **Downstream implications:** result cards/API schemas deferred.
- **Non-implications:** navigation target != authorization grant.

# CID-SV-B8-DAD-015 — Rank/score/snippet are optional non-authoritative projection metadata

- **Decision:** ordered results, rank/score or snippets may exist, but they are derived projection metadata with applicable provenance/uncertainty and never semantic authority or canonical source representation; no universal relevance law is created.
- **Reason:** ranking/display convenience must not create durable cross-domain semantic priority or AI authority.
- **Alternatives avoided:** global relevance score, latest-wins rank, business/admin priority law, AI ranking authority, snippet as canonical representation.
- **Constraint traceability:** State ranking stop boundary; Owner AI non-implication; `NSE-015`.
- **Authority impact:** none.
- **Actual-state impact:** none beyond result projection evidence.
- **Security/privacy impact:** snippets and scoring signals are disclosure-qualified.
- **Offline/private impact:** no public AI/reranker dependency.
- **Compatibility impact:** ranking algorithm can evolve unless a future material product commitment is explicitly governed.
- **Migration impact:** projection technology may change ranking realization without changing source semantics.
- **Cross-component impact:** no domain priority semantics imposed.
- **Downstream implications:** algorithm/model/syntax deferred.
- **Non-implications:** no mandatory AI/semantic search.

# CID-SV-B8-DAD-016 — Positive discovery disclosure requires admissible Tenant/Principal/Policy/Trust/privacy qualification

- **Decision:** S13 must not emit positive protected resource-existence-bearing output without admissible disclosure qualification; cross-Tenant discovery is prohibited; unavailable/indeterminate disclosure evidence yields a non-leaking degraded/uncertain outcome rather than protected existence disclosure or false global absence.
- **Reason:** Owner decision explicitly prohibits unauthorized existence leakage and requires Tenant/authorization awareness.
- **Alternatives avoided:** filter only after result production; indexability=visibility; cached authorization forever; fail-open discovery; reveal unauthorized vs absent through error semantics.
- **Constraint traceability:** Owner decision normative consequences; S1-S4 accepted authority; Global State security boundary.
- **Authority impact:** S13 consumes, never replaces IAM/Policy/Trust authorities.
- **Actual-state impact:** DP04 owns disclosure qualification evidence only.
- **Security/privacy impact:** primary security invariant of S13; includes redaction/minimization.
- **Offline/private impact:** cached evidence is bounded by its applicability/freshness; no perpetual authorization.
- **Compatibility impact:** disclosure semantics are security-critical and compatibility-sensitive.
- **Migration impact:** migration/rebuild cannot retroactively authorize disclosure.
- **Cross-component impact:** future producers/consumers must preserve governance context without internal redesign here.
- **Downstream implications:** authorization algorithms/protocols remain S1-S4/later realization.
- **Non-implications:** this is not a new universal Policy engine or global operation fail-open/fail-closed decision.

# CID-SV-B8-DAD-017 — Counts/facets/categories/relationships are sensitive disclosure surfaces

- **Decision:** count/facet/category totals/relationship hints/navigation hints and equivalent aggregate discovery metadata are subject to the same Tenant/Principal/Policy/privacy qualification as result rows; aggregates are scoped to the disclosure-qualified information universe.
- **Reason:** even a count/category/relationship can reveal protected resource existence.
- **Alternatives avoided:** treat aggregates as harmless metadata; zero means no resources; cross-Tenant totals; universal relationship graph.
- **Constraint traceability:** Owner decision explicitly names counts/relationship hints; Global State aggregate/relationship non-leakage boundary.
- **Authority impact:** projected relation is not source relationship authority.
- **Actual-state impact:** aggregate is derived projection state only.
- **Security/privacy impact:** prevents side-channel semantic leakage.
- **Offline/private impact:** stale/partial aggregate must carry projection qualification and cannot overclaim completeness.
- **Compatibility impact:** aggregate safety semantics remain stable independent of query engine.
- **Migration impact:** new index/provider must preserve disclosure scope.
- **Cross-component impact:** source-provided relation hints remain source-owned.
- **Downstream implications:** facet/aggregation syntax/implementation deferred.
- **Non-implications:** no Universal Resource Graph/Knowledge Graph Authority.

# CID-SV-B8-DAD-018 — Historical query/result provenance is immutable in interpretation

- **Decision:** historical discovery evidence preserves the applicable source identity/owner/revision reference, contribution lineage, projection entry/generation, observation/currentness, query/result correlation and governance/disclosure context; current source/policy/projection state does not silently rewrite historical provenance.
- **Reason:** historical troubleshooting/audit must remain interpretable after resource, policy or projection evolution.
- **Alternatives avoided:** always render history through current resource state; current revision replaces historical reference; latest timestamp becomes historical truth.
- **Constraint traceability:** Project Architecture temporal/history rules; State history/provenance requirements.
- **Authority impact:** history does not create new source authority.
- **Actual-state impact:** historical projection evidence remains distinct from current projection Actual-state.
- **Security/privacy impact:** historical evidence remains governed; replay is not retroactive authorization.
- **Offline/private impact:** retained local history remains interpretable while source is unavailable.
- **Compatibility impact:** provenance semantics are compatibility-sensitive.
- **Migration impact:** migrations preserve lineage or explicitly mark unavailable/unknown evidence.
- **Cross-component impact:** each source owner remains authoritative for source history it owns.
- **Downstream implications:** storage/audit implementation deferred.
- **Non-implications:** no immutable-event-store technology requirement.

# CID-SV-B8-DAD-019 — Offline/reconnect/recovery never transfers authority or chooses a conflict winner

- **Decision:** local projection may serve explicitly stale/partial/unknown qualified discovery; reconnect triggers source re-observation and S13 requalification/reconciliation; no local-wins, central-wins, last-write-wins, latest-timestamp-wins or retroactive authorization rule is created.
- **Reason:** private/offline core correctness is mandatory while source owners remain final authorities.
- **Alternatives avoided:** offline projection becomes local source SoT; reconnect=resolved; rebuild/replay authorizes previous visibility; latest timestamp wins.
- **Constraint traceability:** `NSE-004`; `Z2-MDE-014`; Project Architecture recovery rules; Owner private/offline requirement.
- **Authority impact:** no authority transfer.
- **Actual-state impact:** DP09 owns only S13 reconciliation qualification.
- **Security/privacy impact:** retained data remains disclosure-governed after reconnect.
- **Offline/private impact:** directly establishes correct degraded behavior without public service dependency.
- **Compatibility impact:** recovery semantics remain stable across providers.
- **Migration impact:** migration/reconciliation cannot select source winners.
- **Cross-component impact:** source owners re-observe their own partitions.
- **Downstream implications:** sync/conflict algorithms deferred.
- **Non-implications:** no global fail-open/fail-closed policy.

# CID-SV-B8-DAD-020 — Consume S11/S12 contributions without reopening their internals

- **Decision:** S13 consumes accepted Human Task projection identity/source/freshness/privacy/navigation semantics and Notification identity/history/source/audience/privacy/provenance semantics only as governed discovery contributions; S11/S12 lifecycle/Actual-state remains unchanged.
- **Reason:** Batch 7/6 intentionally stabilized these categories before S13 entry.
- **Alternatives avoided:** redefine Human Task identity/lifecycle in S13; redefine Notification lifecycle/delivery in S13; canonicalize either through discovery.
- **Constraint traceability:** Batch 6/7 Global Acceptances; post-Batch-7 assessment; `GAC-TR-0076`.
- **Authority impact:** zero; S11/S12 accepted ownership preserved.
- **Actual-state impact:** Discovery of a task/notification does not change its Actual-state owner.
- **Security/privacy impact:** accepted source privacy/audience/applicability is preserved and further disclosure-qualified by S13.
- **Offline/private impact:** source-category stale/unknown remains explicit.
- **Compatibility impact:** S13 contribution contract consumes accepted source semantics, not new parallel semantics.
- **Migration impact:** projection migration does not migrate source lifecycle authority.
- **Cross-component impact:** none beyond accepted source-to-S13 contribution.
- **Downstream implications:** no S11/S12 implementation details.
- **Non-implications:** Human Task != Notification remains preserved.

# CID-SV-B8-DAD-021 — Non-server producers and WB-R01 are constrained only by representation-neutral stable obligations

- **Decision:** future `ns_runtime/ns_node/ns_agent` producers and `WB-R01/ns_web` consumer are constrained only by RCP-21 producer/consumer semantic obligations; their internal architecture, metadata models, indexing/query mechanisms and UI are not designed here.
- **Reason:** those Product Component Internal Design scopes are not authorized, but S13 requires a stable contract edge that does not preempt them.
- **Alternatives avoided:** reverse-design their internals; invent per-component discovery modules; claim full RCP-21 closure.
- **Constraint traceability:** exact Batch-8 forbidden scope; remaining-pressure assessment; RCP-21 topology.
- **Authority impact:** all future source owners remain authorities.
- **Actual-state impact:** no foreign Actual-state partition defined.
- **Security/privacy impact:** future participants must preserve Tenant/governance/privacy context.
- **Offline/private impact:** obligations preserve private/offline compatibility without dictating mechanics.
- **Compatibility impact:** stable semantic contract allows independent implementations.
- **Migration impact:** other components can evolve without adopting S13 physical identity/storage.
- **Cross-component impact:** establishes non-preemptive contract boundary only.
- **Downstream implications:** each component must later prove conformance under its own authorization.
- **Non-implications:** no Agent/Node/Runtime/Web internal design.

# CID-SV-B8-DAD-022 — Foundation consumption and AI/search/index technology remain authority-neutral/non-preemptive

- **Decision:** S13 consumes only accepted Foundation semantics through the Stable Entry→Foundation Contract→Module→Provider path; no new Foundation capability is required. Unified Discovery does not require AI semantic search, embeddings, vector retrieval, LLM answer synthesis, a public SaaS, or any concrete search/index/storage technology.
- **Reason:** accepted Foundation is sufficient for authority-neutral context/time/correlation/status/redaction/representation/conformance mechanics; technology selection would create unnecessary lock-in and may violate private/offline baseline.
- **Alternatives avoided:** new Search Foundation, mandatory vector Foundation, Elastic/OpenSearch/etc selection, public embedding/AI provider, S13-specific common capability bypass.
- **Constraint traceability:** accepted Foundation readiness; Owner AI/public-SaaS non-implication; Global State Foundation and technology non-preemption.
- **Authority impact:** Foundation/provider/storage/index gains no authority.
- **Actual-state impact:** telemetry/storage never becomes SV-R09 owner.
- **Security/privacy impact:** privacy/redaction remains Product semantic responsibility even when Foundation mechanics are used.
- **Offline/private impact:** no mandatory public Internet/SaaS dependency.
- **Compatibility impact:** realization/provider remains replaceable.
- **Migration impact:** technology migration is conformance-only/compatible if semantics remain preserved.
- **Cross-component impact:** no new shared dependency imposed.
- **Downstream implications:** future semantic retrieval may consume RCP-21 only after separate authorization/design.
- **Non-implications:** no embedding/vector/search-provider product guarantee.

# CID-SV-B8-DAD-023 — Close only the RCP-21 S13/SV-R09 contribution at current design level

- **Decision:** `RCP-21 S13 / SV-R09 Contribution → CLOSED AT CURRENT DESIGN LEVEL`; full RCP-21 cross-component closure remains explicitly not claimed/not authorized. Stable obligations are divided among future resource-owner producers, S13 projector and future consumers as recorded in Candidate §18.
- **Reason:** S13 can close its projector semantics and representation-neutral contract obligations now, while non-server producer Component Internal Design and WB-R01 consumer Component Internal Design are still unavailable.
- **Alternatives avoided:** leave S13 obligations implementation-defined; claim full RCP-21 prematurely; design non-server/Web internals to force closure.
- **Constraint traceability:** `GAC-TR-0076`; Global State RCP-21 authorization; remaining-pressure assessment; RRA RCP-21 topology.
- **Authority impact:** resource owner + S13 projection ownership split preserved; no shared authority created.
- **Actual-state impact:** S13 owns only its projection partition; producers own source facts; future consumers own only their interaction facts when later accepted.
- **Security/privacy impact:** RCP-21 includes Tenant/Principal/Policy/Trust/privacy/non-leakage obligations.
- **Offline/private impact:** stable obligations explicitly permit stale/partial/unknown private/offline projection without authority transfer.
- **Compatibility impact:** source identity/domain/type, projection uncertainty and disclosure semantics become stable cross-boundary requirements.
- **Migration impact:** producer/projector/consumer implementations may migrate while preserving these semantics.
- **Cross-component impact:** creates an explicit later conformance target without preempting other components.
- **Downstream implications:** GAC must later determine full RCP-21 closure eligibility after required producer/consumer Component Internal Design contributions exist.
- **Non-implications:** `RCP-21 FULL CLOSED` is not claimed; no next phase/component is authorized.

---

# DAD Classification Audit

```text
DAD Count
→ 23

MDE Dimension Changed
→ 0

New Product Capability
→ 0

Resource Authority / SoT Transfer
→ 0

Projection Actual-state Owner Transfer
→ 0

Universal Resource Identity / Registry / Category Authority Commitment
→ 0

Cross-Tenant Discovery Commitment
→ 0

Authorization Bypass Commitment
→ 0

Material Global Ranking / Relevance Law
→ 0

Mandatory AI / Semantic Search / Embedding / Vector Commitment
→ 0

Mandatory Search/Index/Provider/Protocol/Storage Lock-in
→ 0

Material Global Offline Fail / Conflict-winner Policy
→ 0

High-migration-cost Owner-reserved Commitment Added
→ 0

Misclassified MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

All `CID-SV-B8-DAD-001..023` remain bounded delegated architecture decisions pending independent GAC review. They do not self-authorize Global Acceptance or downstream progression.
