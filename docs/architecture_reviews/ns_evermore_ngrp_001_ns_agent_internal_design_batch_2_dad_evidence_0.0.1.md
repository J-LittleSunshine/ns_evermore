# NGRP-001 — Component Internal Design / ns_agent / Batch 2 — DAD Evidence

- Session Type: `BOUNDED PRODUCING SESSION`
- Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_AGENT / BATCH_2 / HARNESS_NATIVE_MULTI_AGENT_COMPOSITION_GOVERNED_CROSS_DOMAIN_DELEGATION_AUTOMATION_PARTICIPATION_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Producing Entry HEAD: `3623f90e3a1ea01f23c6ebf9fbd6d8e33a57e3b3`
- Candidate Commit: `3fe9145bdfbc9d7325cac501072687cf439741e5`
- Candidate Delta: `1 commit / 1 added Candidate file / unexpected drift NONE`
- DAD Set: `CID-AG-B2-DAD-001..022`
- Open MDE at DAD entry: `0`
- Evidence Status: `COMPLETED / AWAITING_REVIEW`

---

# 1. Purpose and DAD Boundary

This document records Component-level Detailed Architecture Decisions made inside the already accepted A5/A6 boundaries. It does not create Owner authority and does not promote a DAD into an MDE merely because the decision is important to internal coherence.

A decision remains a DAD here only when all of the following hold:

```text
existing Product capability is unchanged
existing five-component topology is unchanged
existing A5/A6 boundaries are unchanged
existing AG-R03/AG-R04 Runtime Roles are unchanged
Authority / SoT / final Actual-state topology is unchanged
no new trust/security boundary is introduced
no Product-wide fail-open/fail-closed or winner/merge law is introduced
no universal scheduling/retry/rollback/once semantics are introduced
no mandatory provider/framework/protocol/storage lock-in is introduced
no major recursive/cyclic Multi-Agent Product semantic is selected
```

If any decision had crossed those conditions, producing work would have stopped for Owner/GAC MDE. None did.

---

# 2. Decision Summary

```text
CID-AG-B2-DAD-001 → 19-responsibility A5/A6 decomposition
CID-AG-B2-DAD-002 → bounded Composition Operation / participant-correlation identity model
CID-AG-B2-DAD-003 → effective participant revision binding + no silent historical rebind
CID-AG-B2-DAD-004 → operation-scoped membership/relationship; no universal supervisor/team topology
CID-AG-B2-DAD-005 → source-attributed Composition Context Contribution; no shared factual SoT
CID-AG-B2-DAD-006 → participant Actual-state preservation + A5-only coordination projection
CID-AG-B2-DAD-007 → composition partiality/outcome qualification without universal winner law
CID-AG-B2-DAD-008 → NSH A5/A6 extension seams; no new Harness authority
CID-AG-B2-DAD-009 → bounded A6 cross-domain participation identity model
CID-AG-B2-DAD-010 → governed target effective revision/capability qualification
CID-AG-B2-DAD-011 → governance/Admission/runtime handoff correlation without authority collapse
CID-AG-B2-DAD-012 → Agent→Node delegation journey and Attempt/Effect preservation
CID-AG-B2-DAD-013 → existing Automation invocation participation with S6/S8 preservation
CID-AG-B2-DAD-014 → Agent candidate-authoring contribution → normal S6/S8 lifecycle
CID-AG-B2-DAD-015 → source-attributed cross-domain result contribution → A2 reintegration handoff
CID-AG-B2-DAD-016 → explicit failure/currentness/unknown semantics; no implicit fallback/winner
CID-AG-B2-DAD-017 → A5/A6 own-fact recovery/reconciliation participation under RT-R04
CID-AG-B2-DAD-018 → RCP-11 representation-neutral stable contract synthesis
CID-AG-B2-DAD-019 → RCP-12 representation-neutral stable contract synthesis
CID-AG-B2-DAD-020 → bounded RCP-16/17/19/20/22/24 refinement without overclaim
CID-AG-B2-DAD-021 → SDD/ACD/EL/HPL/XED taxonomy + hard SDD acyclic topology
CID-AG-B2-DAD-022 → Shared Foundation reuse / private-offline / technology-neutral boundary
```

---

# 3. CID-AG-B2-DAD-001 — A5/A6 Responsibility Decomposition

## Decision

```text
A5 → 9 responsibilities
A6 → 10 responsibilities
Total → 19
```

A5:

```text
A5-R01 Composition Operation Identity & Definition-context Binding
A5-R02 Participant Reference, Effective Revision & Compatibility Binding
A5-R03 Operation-scoped Participation Membership & Relationship Correlation
A5-R04 Agent-to-Agent Invocation / Delegation Coordination
A5-R05 Composition Context-contribution & Source-attribution Coordination
A5-R06 Participant Runtime-evidence Correlation & Actual-state Preservation
A5-R07 Composition Outcome, Partiality & Uncertainty Qualification
A5-R08 Composition Recovery / Reconciliation Participation
A5-R09 Composition History, Provenance, Diagnostics & RCP-11 Governance
```

A6:

```text
A6-R01 Cross-domain Intent / Participation Identity & Agent-context Binding
A6-R02 Governed Target Reference, Revision/Capability & Applicability Qualification
A6-R03 Governance / Admission / Runtime Handoff Correlation
A6-R04 Agent→Node Delegation Participation
A6-R05 Existing Automation Selection / Invocation Participation
A6-R06 Candidate Automation Authoring Contribution & S6 Intake Correlation
A6-R07 External Attempt / Effect / Automation Evidence Intake & Qualification
A6-R08 Cross-domain Result Contribution & A2 Reintegration Handoff
A6-R09 Cross-domain Recovery / Reconciliation Participation
A6-R10 History, Provenance, Diagnostics & RCP-12 Governance
```

## Alternatives considered

- **A — one monolithic A5 and one monolithic A6 responsibility:** rejected because identity, evidence, recovery and stable-contract governance would collapse and obscure ownership.
- **B — one responsibility per every event/reference/status:** rejected as overfragmentation and likely implementation-shaped architecture.
- **C — cohesive semantic clusters with explicit identity/source/recovery/contract partitions:** selected.

## Rationale

The selected decomposition separates facts that genuinely originate in AG-R03/AG-R04 from facts merely referenced from A2, S6/S8, Runtime or Node. It is large enough to make ownership reviewable while remaining representation-neutral.

## Benefits

- explicit owner boundaries;
- easier RCP-11/RCP-12 conformance review;
- no “god Harness” responsibility;
- recovery/diagnostic responsibilities cannot silently absorb semantic owners.

## Costs / tradeoffs

- more architecture concepts must be carried through later detailed design;
- implementation may realize multiple responsibilities together and must maintain semantic separation.

## Long-term impact

Stable semantic separation permits future provider/framework replacement and Multi-Agent realization changes without changing Product authority.

## Classification

`DAD`. No new boundary, role, capability, authority or Product-wide semantic law is created.

---

# 4. CID-AG-B2-DAD-002 — Composition Operation and Participant-correlation Identity Model

## Decision

A5 uses bounded semantic identities for:

```text
Multi-Agent Composition Operation
Composition Participant Correlation
```

They remain distinct from Agent Operation, Agent Runtime Attempt, Harness Invocation and source participant facts.

## Alternatives considered

- **A — reuse initiating Agent Operation identity for the whole composition:** rejected; it cannot distinguish the coordinator occurrence from participant operations and destroys one-to-many lineage.
- **B — use each participant Agent Operation as the composition identity:** rejected; no single participant may own the composition coordination fact.
- **C — bounded A5 Composition Operation plus participant correlations:** selected.

## Rationale

AG-R03 is already accepted as a per-composition-operation coordinator. A distinct bounded identity is therefore derivable and necessary to preserve `composition coordination != participant Actual-state`.

## Benefits

- unambiguous lineage;
- supports partial participation and multiple participant operations;
- supports non-destructive recovery/history;
- avoids universal identifier namespace.

## Costs / tradeoffs

- later representations need correlation across more than one identity;
- consumers cannot assume one Agent Operation equals one composition occurrence.

## Long-term impact

Supports future changes in Multi-Agent realization without binding architecture to graph node IDs, actor IDs or provider-native team IDs.

## Classification

`DAD`. Identity scope is strictly A5-bounded; no major universal identity namespace.

---

# 5. CID-AG-B2-DAD-003 — Effective Participant Revision Binding

## Decision

Every established participant correlation preserves the effective Agent Definition Revision actually used for historical interpretation. A5 consumes A1 revision semantics and does not define a universal selector.

```text
latest/current revision
!= historical effective participant revision automatically
```

## Alternatives considered

- **A — always resolve latest revision at read/runtime time:** rejected because it rewrites historical meaning and risks silent incompatibility.
- **B — freeze a universal exact-version selector syntax in A5:** rejected because it duplicates A1 and creates representation/compatibility commitments.
- **C — require effective revision identifiability while leaving selection syntax/algorithm to existing A1/later realization:** selected.

## Rationale

History and provenance require deterministic interpretation of what participated, while A1 remains revision authority.

## Benefits

- historical stability;
- migration/conformance diagnosability;
- no duplicate Agent-definition authority.

## Costs / tradeoffs

- later realizations must retain effective revision evidence;
- dynamic resolution must still materialize an effective historical binding.

## Long-term impact

Provider/framework evolution cannot silently alter past compositions.

## Classification

`DAD`; no new versioning Product law or selector syntax.

---

# 6. CID-AG-B2-DAD-004 — Operation-scoped Membership and Relationship Semantics

## Decision

A5 owns operation-scoped participant membership/correlation and contextual caller/callee/peer relationships. It does not introduce a universal persistent team, supervisor or graph topology.

## Alternatives considered

- **A — universal persistent Team entity:** rejected as a new durable Product semantic and potential authority/SoT pressure not required by upstream.
- **B — universal supervisor hierarchy:** rejected; Owner explicitly reserved universal supervisor/team topology and hierarchy would risk authority collapse.
- **C — record only the participant correlations and contextual relationships relevant to each Composition Operation:** selected.

## Rationale

The accepted capability requires general Multi-Agent composition, not one mandatory team model.

## Benefits

- supports caller/callee/peer composition;
- remains framework-neutral;
- no hidden trust/authority inheritance;
- permits later topologies as realization choices when semantically compatible.

## Costs / tradeoffs

- no universal team-management Product semantics are supplied by this Batch;
- a future durable team capability would require separate revalidation.

## Long-term impact

Avoids locking the Product to supervisor/swarm/graph paradigms.

## Classification

`DAD`. A future proposal for durable universal team semantics is an explicit GAC/Owner revalidation trigger.

---

# 7. CID-AG-B2-DAD-005 — Composition Context Contribution Instead of Shared Factual SoT

## Decision

A5 represents cross-participant context movement as a source-attributed **Composition Context Contribution** consumed by each participant's accepted A2 context lifecycle.

```text
Shared Context
!= shared factual SoT
```

## Alternatives considered

- **A — global composition shared-memory SoT:** rejected; creates merged Actual-state/factual authority and a new storage/consistency authority.
- **B — copy all initiating Agent context into every participant:** rejected; privacy, source authority and disclosure boundaries collapse.
- **C — provenance-bearing context contributions with each A2 deciding/qualifying its own context projection:** selected.

## Rationale

A2 already owns participant runtime context. A5 only needs correlation and source attribution.

## Benefits

- preserves factual authority;
- supports privacy minimization;
- works with local/provider-specific context strategies;
- enables history and diagnostics.

## Costs / tradeoffs

- participants may see different qualified context projections;
- no universal consistency guarantee for “shared memory”.

## Long-term impact

Keeps future memory/context technologies replaceable and prevents storage placement from becoming Product SoT.

## Classification

`DAD`; no new SoT or trust boundary.

---

# 8. CID-AG-B2-DAD-006 — Participant Actual-state Preservation

## Decision

A5 composition projections contain only A5 coordination/provenance facts plus source-attributed references. Each participant's Agent runtime Actual-state remains A2/AG-R01.

## Alternatives considered

- **A — merge all participant state into AG-R03:** rejected by accepted Runtime Responsibility Architecture.
- **B — nominate a supervisor Agent's A2 state as canonical composition state:** rejected; it creates winner/authority transfer not accepted upstream.
- **C — federated participant state + A5 coordination projection:** selected.

## Rationale

This directly enforces accepted `AG-R03 Composition Coordination != merged AG-R01 Actual-state`.

## Benefits

- no circular ownership;
- partial failure remains visible;
- individual Agent histories remain correct;
- composition views can be rebuilt from source evidence.

## Costs / tradeoffs

- consumers must correlate multiple source partitions;
- no single universal composition-state record can claim all participant truth.

## Long-term impact

Supports distributed/private/offline participants without centralizing semantic authority.

## Classification

`DAD`; inherited owner topology is preserved.

---

# 9. CID-AG-B2-DAD-007 — Composition Outcome and Partiality Qualification

## Decision

A5 may produce composition-level outcome/partiality qualifications only by applying applicable A1 semantics to source-owned participant evidence. It introduces no universal success, winner or merge rule.

## Alternatives considered

- **A — all-success universal rule:** rejected; not all valid compositions require all participants.
- **B — first/latest/supervisor/majority result wins:** rejected; each is a new universal conflict/winner law.
- **C — preserve participant evidence and qualify composition outcome according to effective A1 semantics; otherwise remain partial/unknown/indeterminate:** selected.

## Rationale

The semantic definition, not coordinator convenience, must determine success.

## Benefits

- domain-correct outcome interpretation;
- partial failure visibility;
- no hidden conflict resolution;
- future composition patterns remain possible.

## Costs / tradeoffs

- some operations legitimately remain indeterminate;
- implementations cannot use a simplistic universal “one result = done” rule.

## Long-term impact

Avoids hard-coding current orchestration patterns into Product architecture.

## Classification

`DAD`; no Product-wide winner/fail law.

---

# 10. CID-AG-B2-DAD-008 — NSH A5/A6 Extension Seams

## Decision

The accepted NSH core is extended by two bounded seams:

```text
A2 ↔ A5 Composition Extension
A2 ↔ A6 Cross-domain Action Extension
```

A1/A3/A4 remain normative inputs as applicable. NSH gains no new authority or SoT.

## Alternatives considered

- **A — introduce A7 Harness boundary/AG-R05:** rejected by explicit upstream classification.
- **B — redefine A2 as owner of all Multi-Agent and cross-domain facts:** rejected because A5/A6 and AG-R03/04 are accepted partitions.
- **C — extend the same named NSH concept through A5/A6 while facts retain their boundary owner:** selected.

## Rationale

This follows the GAC NSH insertion assessment and Batch-1 extension seam exactly.

## Benefits

- coherent Harness internal model across all six Agent boundaries;
- no sixth component or fifth Agent runtime owner;
- provider-adaptive strategy remains possible.

## Costs / tradeoffs

- NSH cannot be treated as a simple independent service/module authority in later implementation.

## Long-term impact

Protects architectural stability while allowing Harness realization to evolve.

## Classification

`DAD`; explicit GAC classification already fixes NSH as named internal concept.

---

# 11. CID-AG-B2-DAD-009 — A6 Cross-domain Participation Identity

## Decision

A6 uses one bounded Cross-domain Participation identity/reference per actual Agent-side delegation/invocation participation occurrence, separate from Agent Decision, Admission, Dispatch, Attempt, Effect and Automation Operation.

## Alternatives considered

- **A — use Agent Operation identity as delegation identity:** rejected; one Agent Operation may produce multiple distinct cross-domain actions.
- **B — use downstream Dispatch/Attempt identity as A6 identity:** rejected; transfers source identity to runtime/executor and fails pre-dispatch/candidate cases.
- **C — bounded A6 participation identity correlated to external evidence:** selected.

## Rationale

AG-R04 owns Agent-side delegation/invocation provenance before and after downstream execution.

## Benefits

- supports multiple actions per Agent Operation;
- candidate authoring can be represented without fake Dispatch/Attempt;
- recovery can correlate missing/late evidence.

## Costs / tradeoffs

- additional correlation identity is required in later representations.

## Long-term impact

Prevents transport/executor identifiers from becoming Agent semantics.

## Classification

`DAD`; bounded A6 identity only.

---

# 12. CID-AG-B2-DAD-010 — Governed Target Effective Revision / Capability Qualification

## Decision

A6 records the target selected by the Agent-side decision together with source-provided effective revision/capability/compatibility qualification where applicable. It does not define the selection algorithm.

## Alternatives considered

- **A — target by free-form name with no revision/capability evidence:** rejected; cannot support compatibility/history.
- **B — A6 owns a universal target registry/router:** rejected; would absorb S6/N1/R2 responsibilities.
- **C — source-domain target reference + effective qualification + A6 correlation:** selected.

## Rationale

A6 must explain what the Agent attempted to delegate to while preserving target-domain authority.

## Benefits

- compatibility and migration visibility;
- historical target interpretation;
- no universal router/registry.

## Costs / tradeoffs

- A6 depends on source-domain evidence availability and may report unknown/stale.

## Long-term impact

Target systems/providers can evolve without rewriting Agent provenance.

## Classification

`DAD`; no target-selection algorithm, routing authority or universal identity namespace.

---

# 13. CID-AG-B2-DAD-011 — Governance / Admission / Runtime Handoff Correlation

## Decision

A6 correlates applicable Governance Context, Formal Admission and Runtime coordination evidence but does not issue or substitute any of them.

## Alternatives considered

- **A — Agent Decision directly authorizes execution:** rejected by Project Architecture and S8.
- **B — Runtime Dispatch implicitly proves Admission:** rejected by accepted Runtime architecture.
- **C — explicit evidence/correlation chain with separate final owners:** selected.

## Rationale

Cross-domain actions must remain governed without making Agent/NSH a policy or execution gate.

## Benefits

- auditability;
- no hidden bypass;
- offline/stale evidence can remain explicit;
- consumers can distinguish why an action did or did not progress.

## Costs / tradeoffs

- longer evidence chain;
- “intent accepted” cannot be simplified to “execution allowed”.

## Long-term impact

Preserves enterprise governance across changing runtime mechanisms.

## Classification

`DAD`; all authorities are accepted upstream.

---

# 14. CID-AG-B2-DAD-012 — Agent→Node Delegation Journey

## Decision

Adopt the accepted cross-component journey:

```text
A2 Agent Decision
→ A6 delegation participation
→ S8 Admission
→ R1/N1 evidence as applicable
→ R2 Dispatch
→ N2 Attempt
→ N3 Effect/source fact
→ R3 correlation where applicable
→ A6 result correlation
→ A2 continuation
```

## Alternatives considered

- **A — A6 calls Node and treats response as Agent result:** rejected; collapses Admission/Dispatch/Attempt/Effect.
- **B — A6 owns Node Attempt/Effect proxy state:** rejected; duplicates N2/N3 owners.
- **C — explicit federated evidence journey:** selected.

## Rationale

The Runtime Responsibility Architecture and ns_node Global Closure already establish these partitions.

## Benefits

- exact source/effect responsibility;
- robust partial/unknown handling;
- no second scheduler/executor.

## Costs / tradeoffs

- correlation must tolerate evidence arriving from multiple owners.

## Long-term impact

Node execution technology can change without changing Agent delegation semantics.

## Classification

`DAD`; consumes accepted cross-component topology.

---

# 15. CID-AG-B2-DAD-013 — Existing Automation Invocation Participation

## Decision

A6 records Agent-side invocation participation while S6 retains Automation definition/semantic runtime authority and S8 retains Artifact Acceptance/Admission.

## Alternatives considered

- **A — execute Automation as Harness-native subflow:** rejected; creates second Automation engine and bypasses S6/S8.
- **B — translate Automation into Agent-internal composition graph:** rejected; collapses Multi-Agent and Automation semantics.
- **C — invoke the governed S6 Automation through accepted lifecycle/runtime topology and correlate results:** selected.

## Rationale

`Multi-Agent != Automation Workflow Authority` is permanent.

## Benefits

- one Automation semantic authority;
- existing governance and runtime evidence reused;
- no duplicate workflow implementation requirement.

## Costs / tradeoffs

- Agent cannot bypass Automation lifecycle for convenience.

## Long-term impact

Automation language/engine can evolve independently from Agent Harness realization.

## Classification

`DAD`; no Automation authority movement.

---

# 16. CID-AG-B2-DAD-014 — Agent Candidate-authoring Contribution and S6 Intake

## Decision

Agent-authored Automation is represented as A6 source-side authoring contribution/provenance, then enters normal S6 intake, validation/canonical lifecycle, S8 Acceptance and later Admission.

## Alternatives considered

- **A — ephemeral Agent-owned executable workflow:** rejected by Owner decision.
- **B — Agent candidate automatically becomes canonical Automation:** rejected; transfers S6 Authority/SoT.
- **C — candidate contribution + normal S6/S8 lifecycle:** selected.

## Rationale

This is the exact Owner-selected Dynamic Automation Authoring model.

## Benefits

- safe AI-assisted authoring;
- canonical governance remains consistent;
- provenance of Agent authorship is retained.

## Costs / tradeoffs

- candidate execution is not immediate merely because the Agent generated it.

## Long-term impact

Supports more capable Agents without weakening enterprise Automation governance.

## Classification

`DAD`; Owner MDE is already settled upstream and is only consumed here.

---

# 17. CID-AG-B2-DAD-015 — Cross-domain Result Contribution and A2 Reintegration Handoff

## Decision

A6 converts correlated external evidence into a source-attributed Cross-domain Result Contribution for A2. A2 retains context reintegration, Agent Decision and Agent outcome ownership.

## Alternatives considered

- **A — A6 writes participant Agent context/state directly:** rejected; absorbs A2 Actual-state.
- **B — source result automatically becomes final Agent result:** rejected; `Effect != Business/Agent Semantic Success automatically`.
- **C — qualified, source-attributed result contribution handed to A2:** selected.

## Rationale

It extends the accepted Batch-1 Tool/Knowledge result reintegration pattern without reopening A2.

## Benefits

- clean A6/A2 boundary;
- source facts preserved;
- Agent semantics can independently interpret external outcomes.

## Costs / tradeoffs

- result correlation and Agent semantic interpretation remain separate steps.

## Long-term impact

Supports new target domains without moving Agent Actual-state ownership.

## Classification

`DAD`.

---

# 18. CID-AG-B2-DAD-016 — Failure, Currentness and Unknown Semantics

## Decision

A5/A6 preserve explicit orthogonal qualifications including, where applicable:

```text
PENDING / PARTIAL / UNKNOWN / STALE / UNREACHABLE / UNAVAILABLE /
INCOMPATIBLE / UNSUPPORTED / INDETERMINATE / CONFLICTING / SUPERSEDED
```

No implicit fallback, retry, participant substitution or winner rule is inferred.

## Alternatives considered

- **A — collapse unknown/unreachable into failure:** rejected; destroys observability and can create incorrect business semantics.
- **B — automatically retry/fallback to another target/participant:** rejected; universal retry/selection policy is Owner-reserved and may change effects.
- **C — explicit uncertainty/currentness with policy/semantic decisions left to accepted owners:** selected.

## Rationale

Offline/private and distributed evidence requires epistemic states to remain distinguishable.

## Benefits

- no false success/failure;
- safe recovery/reconciliation;
- diagnostics preserve causality.

## Costs / tradeoffs

- consumers must handle indeterminate states explicitly.

## Long-term impact

Avoids embedding transient infrastructure limitations into Product semantics.

## Classification

`DAD`; no fail-open/fail-closed or universal retry law.

---

# 19. CID-AG-B2-DAD-017 — A5/A6 Recovery/Reconciliation Participation

## Decision

A5/A6 own recovery participation only for their own facts; RT-R04 remains cross-component recovery/reconciliation coordinator and original source owners re-observe/reassert their facts.

## Alternatives considered

- **A — Harness central recovery SoT:** rejected; new authority/SoT and recovery engine.
- **B — local latest-wins reconciliation:** rejected; conflict-winner law prohibited.
- **C — federated source recovery + RT-R04 coordination + A5/A6 re-correlation:** selected.

## Rationale

Directly inherits globally accepted R4 semantics.

## Benefits

- no authority transfer;
- offline/private recovery compatible;
- conflicts remain visible;
- history stays non-destructive.

## Costs / tradeoffs

- recovery may finish with unresolved conflict/unknown states;
- no universal deterministic replay guarantee.

## Long-term impact

Supports heterogeneous Agent/Node/Automation persistence strategies without centralizing truth.

## Classification

`DAD`; no new recovery authority/winner/synchronization law.

---

# 20. CID-AG-B2-DAD-018 — RCP-11 Stable Contract

## Decision

Synthesize RCP-11 as a representation-neutral contract between A5/AG-R03 composition coordination and A2/AG-R01 participant facts, covering composition identity, participant effective revisions, correlation/relationship, context-contribution provenance, source evidence/currentness, partiality/outcome, governance, history/recovery and conformance.

## Alternatives considered

- **A — add a new Multi-Agent RCP:** rejected; RCP-11 already exists and count must remain 24.
- **B — make RCP-11 a merged composition state contract:** rejected; violates participant Actual-state ownership.
- **C — federated coordination/source-evidence contract:** selected.

## Rationale

Matches Runtime Responsibility Architecture pressure exactly.

## Benefits

- stable A5↔A2 contract independent of representation;
- explicit source ownership;
- future SDK/Web diagnostics can consume provenance later without redefining Agent internals.

## Costs / tradeoffs

- full cross-component closure cannot be claimed solely here.

## Long-term impact

Provides stable semantic seam for future Multi-Agent implementations.

## Classification

`DAD`; RCP-11 owner-side/current `ns_agent` semantic closure only.

---

# 21. CID-AG-B2-DAD-019 — RCP-12 Stable Contract

## Decision

Synthesize RCP-12 as the representation-neutral AG-R04 source/participant contract covering Agent-side intent/participation, target references/revisions/capabilities, governance/Admission/Runtime correlation, Node Attempt/Effect and Automation result references, candidate-authoring provenance, result contribution, currentness/recovery/history and conformance.

## Alternatives considered

- **A — separate new RCPs for Node, Automation and candidate authoring:** rejected; duplicates existing cross-domain pressure and fragments one accepted AG-R04 responsibility.
- **B — use only runtime Dispatch contract RCP-05:** rejected; cannot represent pre-Admission intent, candidate authoring or Agent-side provenance.
- **C — one RCP-12 with typed semantic participation branches and source ownership preservation:** selected.

## Rationale

RCP-12 was explicitly reserved for AG-R04 owner/source side in Batch 2.

## Benefits

- consistent Agent cross-domain provenance;
- no duplicate runtime/Node/Automation contract authority;
- supports candidate authoring and actual execution without collapse.

## Costs / tradeoffs

- RCP-12 must correlate several external source contracts;
- it cannot simplify all targets into one execution semantics.

## Long-term impact

Cross-domain Agent capabilities can expand without inventing a new Agent-owned workflow/execution engine.

## Classification

`DAD`; no new RCP and no full cross-component closure claim.

---

# 22. CID-AG-B2-DAD-020 — Bounded Refinement of RCP-16/17/19/20/22/24

## Decision

A5/A6 contribute only facts materially originating in their boundaries:

```text
RCP-16 → composition/delegation correlation only; A2 source-wait preserved
RCP-17 → A5/A6 Trial participation facts only
RCP-19 → A5/A6 Applied config facts only where genuinely applied
RCP-20 → A5/A6 own-fact recovery/reconciliation participation
RCP-22 → A5/A6 fact-owner diagnostics/provenance
RCP-24 → receiving/applicability/correlation only where material
```

## Alternatives considered

- **A — claim full closure when Agent side is complete:** rejected; external contributors remain downstream/multi-party.
- **B — omit A5/A6 contribution entirely:** rejected; would leave diagnostics/recovery/trial/applicability gaps.
- **C — close only bounded source/participant contribution:** selected.

## Rationale

Component closure and RCP full cross-component closure are different dimensions.

## Benefits

- exact progress accounting;
- no reverse-design of ns_web/SDK/other domains;
- six-boundary Agent provenance can become complete at current design level.

## Costs / tradeoffs

- GAC must later assess full RCP closure independently.

## Long-term impact

Prevents false readiness while preserving incremental contract convergence.

## Classification

`DAD`.

---

# 23. CID-AG-B2-DAD-021 — Dependency Taxonomy and Acyclic Hard SDD Graph

## Decision

Reuse accepted dependency classes:

```text
SDD / ACD / EL / HPL / XED
```

Only SDD participates in hard semantic-definition cycle analysis. A5/A6 hard SDD graphs are directed from derived responsibilities to identity/context foundations and are acyclic.

## Alternatives considered

- **A — treat every runtime feedback/correlation as dependency:** rejected; creates false semantic cycles.
- **B — no explicit dependency types:** rejected; hides circular definition/ownership risks.
- **C — accepted typed taxonomy with SDD-only cycle check:** selected.

## Rationale

Already accepted by server/runtime/node/Agent Batch 1 and exactly suited to distinguish runtime feedback from semantic definition.

## Benefits

- auditable cycle analysis;
- no accidental authority cycle;
- history/evidence links can be bidirectional without semantic-definition ambiguity.

## Costs / tradeoffs

- later design must classify edges instead of using one generic dependency relation.

## Long-term impact

Keeps architecture composable as more contract consumers are added.

## Classification

`DAD`; reuses accepted taxonomy.

---

# 24. CID-AG-B2-DAD-022 — Shared Foundation Reuse / Private-offline / Technology-neutral Boundary

## Decision

A5/A6 consume accepted Foundation capabilities/contracts/modules/providers for mechanics only and introduce no parallel Agent-local Foundation or mandatory technology/provider.

Relevant Foundation subjects include:

```text
Temporal / Freshness
Correlation / Provenance
Technical Status / Uncertainty
Governed Context
Representation mechanics
Network mechanics
Diagnostics / Redaction
Secret Reference
Compatibility / Conformance
Bootstrap Configuration
```

## Alternatives considered

- **A — Harness-specific generic scheduler/retry/workflow foundation:** rejected; these capabilities are explicitly non-Foundation and would create authority pressure.
- **B — mandate public provider/broker/workflow service for Multi-Agent correctness:** rejected; violates private/offline baseline and lock-in rules.
- **C — reuse authority-neutral Foundation mechanics and leave concrete realization downstream:** selected.

## Rationale

Current Foundation is globally closed and sufficient; no mandatory missing semantic emerged.

## Benefits

- private/offline correctness;
- replaceable provider/framework/storage;
- no duplicate foundational utilities as semantic authorities.

## Costs / tradeoffs

- later implementation must choose technologies within these boundaries rather than receive a predefined stack here.

## Long-term impact

Preserves platform portability and model/provider evolution.

## Classification

`DAD`; no Foundation change or technology lock-in.

---

# 25. Cross-DAD Consistency Review

The DAD set is mutually consistent:

```text
DAD-002/003/004
→ define bounded composition identity/revision/relationship without universal topology

DAD-005/006/007
→ preserve source context/Actual-state and partiality without merged truth/winner law

DAD-008
→ places those facts inside accepted NSH/A5/A6 seams without new Harness authority

DAD-009/010/011
→ define A6 participation/target/governance correlation before execution

DAD-012/013/014
→ preserve Node/Automation/Acceptance authority in each authorized A6 use case

DAD-015/016/017
→ reintegrate qualified source evidence and recover without source rewrite

DAD-018/019/020
→ stabilize RCP contributions without duplicate RCP or overclaim

DAD-021/022
→ keep dependency and Foundation/technology boundaries stable
```

No decision requires another decision to reverse accepted Authority/SoT/Actual-state ownership.

---

# 26. Major Decision Escalation Audit

Each DAD was checked against Owner-reserved triggers.

| MDE trigger | Result | Evidence / reason |
|---|---|---|
| new Product capability | NO | A5/A6 capabilities already Owner-accepted |
| new Authority | NO | A1/S6/S8/runtime/node authorities preserved |
| new SoT | NO | no shared-memory, Harness, composition or delegation SoT created |
| new final Actual-state owner | NO | only accepted AG-R03/04 bounded facts refined |
| new trust/security boundary | NO | existing governed context/trust topology consumed |
| major Tenant/Organization change | NO | Tenant != Organization preserved; no new federation law |
| major universal identity namespace | NO | identities are boundary-scoped and representation-neutral |
| universal scheduling/fairness law | NO | RT-R02 remains scheduler/dispatcher; no algorithm selected |
| universal retry/cancel/rollback/compensation/once law | NO | explicitly absent |
| conflict winner/merge law | NO | conflicting/unknown may remain unresolved |
| authoritative sync direction | NO | RT-R04/source-owner federation preserved |
| material fail-open/fail-closed law | NO | uncertainty preserved; no Product-wide policy selected |
| new Automation/Workflow Authority | NO | S6 preserved |
| universal Multi-Agent Authority | NO | A5 coordination only |
| merged participant Actual-state SoT | NO | explicitly prohibited |
| major recursive/cyclic Product semantics | NO | not decided; Owner/GAC reserved if material need appears |
| mandatory public SaaS/broker/workflow/recovery dependency | NO | private/offline baseline preserved |
| framework/provider/protocol/storage lock-in | NO | no concrete selection |
| other high-migration commitment | NO | representation-neutral semantics only |

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

---

# 27. Named Revalidation Triggers

The DAD set remains valid only while accepted upstream remains valid. Return to GAC/Owner if later work materially requires:

```text
new Product capability / sixth component / A7 / AG-R05
new Agent/Harness/Composition authority or global SoT
persistent universal team/supervisor hierarchy as Product semantics
major recursive/cyclic Multi-Agent Product semantics
universal shared-memory factual authority
universal participant winner/merge law
universal Multi-Agent scheduling/fairness/parallelism Product law
Agent-owned Automation/workflow execution authority
Admission bypass or Agent-generated self-admission
Node Attempt/Effect ownership transfer to Agent
universal retry/cancel/rollback/compensation/once guarantee
material offline fail-open/fail-closed policy
new trust/security/Tenant federation boundary
mandatory public provider/broker/workflow/recovery service
major provider/framework/protocol/storage lock-in
new stable cross-component pressure not representable by RCP-01..24
```

Where such a need appears, DAD authority is insufficient.

---

# 28. DAD Exit Gate

```text
Candidate Commit Verified
→ 3fe9145bdfbc9d7325cac501072687cf439741e5
→ exactly 1 Candidate file added from Producing Entry HEAD

DAD Count
→ 22

Misclassified MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Unmapped Material Decision
→ 0

Authority / SoT / Actual-state Transfer
→ 0 / 0 / 0

New RCP
→ 0

RCP Count
→ 24 / unchanged

Implementation-defined Escape
→ 0

Implementation Leakage
→ 0

DAD Evidence Status
→ COMPLETED / AWAITING_REVIEW
```

This DAD Evidence does not declare Global Acceptance, `ns_agent` Internal Design Exhaustion, `ns_agent` Global Closure or any RCP Full Cross-component Closure.

The next producing artifact is Review / Audit Evidence only, after validating this DAD commit delta.