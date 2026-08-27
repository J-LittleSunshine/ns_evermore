# NGRP-001 — ns_agent Component Internal Design / Batch 1 DAD Evidence

## Authority Metadata

- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Producing Entry HEAD:** `6b4f71eb1531a91df1ad7c24ef59d0c9f1613354`
- **Candidate Commit:** `3690a4e007b5879790364657b465253349576993`
- **Recovered GAC Epoch:** `GAC-EPOCH-0089`
- **Authorization Scope:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_AGENT / BATCH_1 / AGENT_DEFINITION_HARNESS_RUNTIME_PROVIDER_TOOL_KNOWLEDGE_EXECUTION_BOUNDARY_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **DAD Namespace:** `CID-AG-B1-DAD-*`
- **DAD Count:** `22`
- **Owner MDE Created:** `0`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`

This file records only Component Internal Design decisions derivable inside the accepted A1-A4 / AG-R01-02 scope. No DAD below changes Product Capability, Authority, SoT, final Actual-state ownership, Trust boundary, accepted Runtime Role topology or the count of cross-component RCPs.

---

# CID-AG-B1-DAD-001 — A1-A4 Internal Responsibility Decomposition

## Decision / Issue
How should the four authorized Agent boundaries be decomposed deeply enough that later implementation cannot invent missing architecture?

## Context
A1-A4 are accepted responsibility boundaries, not modules. The Batch must cover Definition/SoT, Agent runtime/NSH, provider mediation, Tool/Knowledge consumption and their stable contracts.

## Alternatives Considered
A. Keep A1-A4 undecomposed and defer details to implementation.
B. Create one large Harness responsibility spanning all Agent facts.
C. Decompose each accepted boundary into bounded architecture-semantic responsibilities while retaining the original four boundaries.

## Selected Design-semantic Result
**C.** The Candidate defines:

```text
A1 → 7 responsibilities
A2 → 13 responsibilities
A3 → 7 responsibilities
A4 → 8 responsibilities
Total → 35
```

## Rationale
This closes semantic ownership and lifecycle pressure without inventing A7 or implementation modules.

## Responsibility Consequence
Every material Batch-1 Agent responsibility has one principal internal owner.

## Dependency Consequence
Dependencies are expressed through SDD/ACD/EL/HPL/XED rather than module calls.

## Authority / SoT / Actual-state Consequence
No accepted authority partition changes.

## RCP Consequence
RCP-09/10 and authorized refinements gain named internal producers/consumers.

## Failure / Offline Consequence
Uncertainty, history and recovery responsibilities are explicit rather than implementation-defined.

## Explicit Non-implications
Responsibility count does not imply package/service/process count.

## Deferred Implementation Mechanics
Module grouping, classes, functions, processes, storage.

## Revalidation Trigger
Any proposal that requires a seventh Agent boundary or moves final ownership.

---

# CID-AG-B1-DAD-002 — NSH Is a Named Internal Architecture, Not a New Boundary

## Decision / Issue
How should `ns_evermore Harness / NSH` be represented after GAC classified it as a named internal concept?

## Context
NSH spans Definition input, runtime/context, provider mediation and Tool/Knowledge consumption but must not become a sixth Product Component, A7 or AG-R05.

## Alternatives Considered
A. Add A7 Harness boundary.
B. Make NSH a Shared Foundation/runtime service.
C. Model NSH as an internal topology across A2/A3/A4 consuming A1.

## Selected Design-semantic Result
**C.**

```text
A1 → normative Definition/Revision upstream
A2 → primary NSH runtime core
A3 → provider/model capability mediation lane
A4 → Tool/Knowledge consumption/reintegration lane
A5/A6 → future opaque extension seams only
```

## Rationale
All Product capability and final-owner partitions already exist; NSH is a cohesion construct, not a missing authority partition.

## Responsibility Consequence
No separate NSH owner replaces A1-A4 owners.

## Dependency Consequence
NSH stable seams are internal semantic contracts, not new RCPs.

## Authority / SoT / Actual-state Consequence
`NO_CHANGE`.

## RCP Consequence
Existing RCP-09/10/16/17/19/20/22/24 are reused.

## Failure / Offline Consequence
NSH failure remains attributable to the underlying A2/A3/A4 fact owner.

## Explicit Non-implications
`NSH != Product Component != Runtime Role != process != framework`.

## Deferred Implementation Mechanics
Harness package layout, runtime framework, adapter interfaces.

## Revalidation Trigger
Any proposal to give NSH independent Authority/SoT/Actual-state ownership.

---

# CID-AG-B1-DAD-003 — Durable Agent Semantics vs Adaptive Harness Strategy

## Decision / Issue
Where is the boundary between canonical Agent semantics and model-adaptive runtime strategy?

## Context
The Owner requires NSH not to fossilize current-generation model limitations into Product Architecture.

## Alternatives Considered
A. Encode current reasoning scaffold/provider workarounds in A1 Definition.
B. Let each provider define Agent behavior.
C. Keep durable semantic intent/requirements in A1 and transient strategy decisions in A2 using A3/A4 capability evidence.

## Selected Design-semantic Result
**C.**

```text
A1 → durable Agent semantic intent / capability requirements
A3/A4 → observed capability/applicability evidence
A2 → operation-scoped Harness Strategy decision
```

## Rationale
This preserves Agent identity across model/provider evolution.

## Responsibility Consequence
A1-R02/R03 define durable requirements; A2-R07 owns runtime adaptation.

## Dependency Consequence
A3/A4 feedback to A2 is `ACD/EL`, not reverse SDD.

## Authority / SoT / Actual-state Consequence
Strategy decisions are A2 runtime facts, not canonical Definition state.

## RCP Consequence
RCP-09 carries strategy-related runtime evidence; RCP-10 carries capability observations.

## Failure / Offline Consequence
Unsupported/unknown capability remains explicit rather than silently rewriting the definition.

## Explicit Non-implications
No fixed planner, fixed N-step loop, provider ranking or fallback law.

## Deferred Implementation Mechanics
Strategy algorithm, model router, prompt scaffold, token budgeting.

## Revalidation Trigger
A proposal to make provider-specific behavior canonical Agent semantics.

---

# CID-AG-B1-DAD-004 — Agent Operation / Runtime Attempt / Harness Invocation Identity Separation

## Decision / Issue
What identity layers are required for durable Agent execution and non-destructive history?

## Context
RCP-09 requires Agent revision/operation/attempt; NSH pressure requires invocation lineage and cross-session continuation.

## Alternatives Considered
A. One identifier for all Agent runtime activity.
B. Provider/tool request IDs as Agent operation identity.
C. Separate durable Operation, A2 Runtime Attempt and sub-level Harness Invocation identities.

## Selected Design-semantic Result
**C.**

```text
Agent Operation Identity
→ durable across legitimate cross-session continuation

Agent Runtime Attempt Identity
→ one bounded A2 execution episode

Harness Invocation Identity
→ one model/tool/knowledge contribution request
```

Owner-specific provider/tool/Node attempts remain separate.

## Rationale
A single ID would collapse retry, recovery and effect evidence.

## Responsibility Consequence
A2-R01/R03/R08 own the three semantic levels.

## Dependency Consequence
A3/A4 evidence depends on A2 Invocation identity but retains owner-local identity.

## Authority / SoT / Actual-state Consequence
No identity layer changes final fact ownership.

## RCP Consequence
RCP-09 gains stable operation/attempt lineage; RCP-10/07/08 are correlated without identity collapse.

## Failure / Offline Consequence
Retry/recovery can create new attempts/invocations while preserving prior evidence.

## Explicit Non-implications
No UUID/global namespace/database key format.

## Deferred Implementation Mechanics
Identifier encoding/generation/storage.

## Revalidation Trigger
Any need for a universal cross-product identity namespace.

---

# CID-AG-B1-DAD-005 — Context Contribution vs Context Projection vs Source Fact

## Decision / Issue
Who owns runtime context and what does inclusion of external facts mean?

## Context
A2 owns Agent context Actual-state, while Knowledge/Tool/Node/external facts retain original owners.

## Alternatives Considered
A. Treat assembled context as a new canonical Knowledge SoT.
B. Treat every source as owning the final prompt/context object.
C. Treat source items as attributed contributions and A2 Context Projection as a derived Agent-runtime fact.

## Selected Design-semantic Result
**C.**

```text
Source Fact / Definition / Human / Model / Tool / Knowledge evidence
→ Context Contribution reference
→ A2 Context Projection
```

## Rationale
Context assembly is an Agent-runtime transformation, not authority transfer.

## Responsibility Consequence
A2-R05/R06 own contribution intake and projection; A4 preserves Knowledge/source attribution.

## Dependency Consequence
Source evidence links by `XED/EL`; projection lineage is `HPL`.

## Authority / SoT / Actual-state Consequence
A2 owns only the derived Context Projection.

## RCP Consequence
RCP-09/22 carry projection provenance; Knowledge SoT remains external.

## Failure / Offline Consequence
Stale/partial/unavailable contributions remain explicit.

## Explicit Non-implications
`Context Cache != Knowledge SoT`; `Agent Memory != External Data SoT`.

## Deferred Implementation Mechanics
Context store, cache, retrieval/storage engine.

## Revalidation Trigger
Any proposal to promote Agent context/memory to external factual authority.

---

# CID-AG-B1-DAD-006 — Context Transformation / Compaction Is Revision-producing and Provenance-preserving

## Decision / Issue
How can context selection/compaction evolve without rewriting history or source truth?

## Context
Context engineering is material NSH pressure but concrete compaction algorithms are forbidden in this phase.

## Alternatives Considered
A. Mutate one current context object in place.
B. Require lossless verbatim retention in every invocation context.
C. Treat materially distinct transformation as a new Context Projection revision with preserved source/transformation provenance.

## Selected Design-semantic Result
**C.**

Required semantic obligations:

```text
new materially distinct projection → new revision/lineage
source attribution retained
known material omission/partiality represented
uncertainty retained
sensitivity/redaction retained
historical projection not rewritten
```

## Rationale
This supports compaction while preserving auditability and model evolution.

## Responsibility Consequence
A2-R06 owns projection revision semantics.

## Dependency Consequence
Transformations are HPL-linked to prior projections/contributions.

## Authority / SoT / Actual-state Consequence
Transformed context remains A2-derived runtime state.

## RCP Consequence
RCP-09/22 gain context revision/provenance stability.

## Failure / Offline Consequence
Partial/unknown compaction outcome can be represented without fabricating source completeness.

## Explicit Non-implications
No lossless round-trip, token budget, summarizer or ranking algorithm selected.

## Deferred Implementation Mechanics
Compaction/ranking/tokenization/storage.

## Revalidation Trigger
Any product guarantee of lossless context reconstruction or universal compaction behavior.

---

# CID-AG-B1-DAD-007 — Provider Capability Profile Is Bounded Observation, Not Agent Authority

## Decision / Issue
How should model/provider capabilities influence NSH without controlling Agent semantics?

## Context
A3/AG-R02 owns bounded provider mediation observations; A1 owns Agent semantics.

## Alternatives Considered
A. Provider capability becomes canonical Agent capability truth.
B. A1 hardcodes provider-specific capabilities.
C. A3 records versioned/currentness-qualified capability observations and compatibility assertions consumed by A2/A1 as evidence.

## Selected Design-semantic Result
**C.**

## Rationale
Provider capability changes more rapidly than Agent semantic identity.

## Responsibility Consequence
A3-R02/R03 own capability/compatibility evidence.

## Dependency Consequence
A1 requirements → A3 compatibility by SDD; runtime feedback → A2 by EL/ACD.

## Authority / SoT / Actual-state Consequence
No Provider Authority transfer.

## RCP Consequence
RCP-10 owner-side semantics are closed at current design level.

## Failure / Offline Consequence
`UNSUPPORTED/UNKNOWN/STALE/CONFLICTING` are explicit.

## Explicit Non-implications
No provider priority or selection winner.

## Deferred Implementation Mechanics
Capability discovery protocol/provider API.

## Revalidation Trigger
Provider state proposed as canonical Agent Definition authority.

---

# CID-AG-B1-DAD-008 — Provider Mediation Interaction Is Distinct from Agent Runtime Outcome

## Decision / Issue
Who owns the facts of model/provider interaction versus Agent interpretation?

## Context
A3 is a runtime role with bounded observations; A2 is final owner for Agent runtime facts.

## Alternatives Considered
A. A3/provider response directly becomes Agent result.
B. A2 owns all provider mediation details.
C. A3 owns Provider Mediation Interaction/response observations; A2 owns model contribution interpretation/Agent decision.

## Selected Design-semantic Result
**C.**

```text
A2 Harness Invocation
!= A3 Provider Mediation Interaction

A3 Output Observation
→ A2 Model Contribution / interpretation
```

## Rationale
Provider success/failure and Agent semantic success/failure are different assertions.

## Responsibility Consequence
A3-R04/R05 vs A2-R09.

## Dependency Consequence
A3→A2 result flow is EL/ACD, not ownership transfer.

## Authority / SoT / Actual-state Consequence
A3 owns mediation observations only.

## RCP Consequence
RCP-10 remains separate from RCP-09.

## Failure / Offline Consequence
Provider failure may be recoverable/alternative input without automatically failing the Agent operation.

## Explicit Non-implications
No provider retry/fallback algorithm.

## Deferred Implementation Mechanics
Provider client/request/streaming protocol.

## Revalidation Trigger
Any attempt to make provider response the final Agent semantic outcome automatically.

---

# CID-AG-B1-DAD-009 — Tool / Knowledge Consumption Preserves Source and Effect Ownership

## Decision / Issue
How should A4 consume tools/knowledge without becoming Tool/Knowledge/Node authority?

## Context
A4 owns Agent consumption semantics; N1/N2/N3 and Knowledge/external owners are globally accepted upstream.

## Alternatives Considered
A. A4 owns results/effects because it invoked them.
B. Collapse Tool/Knowledge into A2 Context ownership.
C. A4 owns binding/intention/correlation/reintegration semantics while source facts/effects remain original-owner evidence.

## Selected Design-semantic Result
**C.**

## Rationale
Invocation is not authority transfer.

## Responsibility Consequence
A4-R01..R08 define Agent-side consumption responsibilities.

## Dependency Consequence
RCP-04/07/08 are XED/EL consume-only upstream.

## Authority / SoT / Actual-state Consequence
Node Attempt/Effect and Knowledge SoT unchanged.

## RCP Consequence
Node RCP internals are not reopened; RCP-22 Agent contribution retains source references.

## Failure / Offline Consequence
Unavailable/stale/partial Tool/Knowledge evidence remains explicit.

## Explicit Non-implications
No vector DB, Tool Provider authority or local-effect authority.

## Deferred Implementation Mechanics
Tool adapters, RAG retrieval, vector/index storage.

## Revalidation Trigger
Any authority movement from source owner to A4.

---

# CID-AG-B1-DAD-010 — Model Output / Agent Decision / Action Proposal / Authorized Execution Separation

## Decision / Issue
How should a model-generated tool/action suggestion become a governed enterprise action?

## Context
The Owner specifically requires Model Tool Call not to equal real enterprise execution.

## Alternatives Considered
A. Native model tool call directly executes.
B. Provider mediation owns action authorization.
C. Model output is evidence; A2 interprets to Agent decision/proposal; A4/future A6 forms governed intent; external Admission/runtime/executor authorities remain mandatory where applicable.

## Selected Design-semantic Result
**C.**

```text
Provider Output
→ A2 Model Contribution
→ A2 Agent Decision
→ optional Action Proposal
→ A4 Tool Intent or future A6 seam
→ Admission/coordination/executor
→ Attempt
→ Effect
```

## Rationale
This is the core NSH enterprise-governance boundary.

## Responsibility Consequence
A2-R09 and A4-R04 own the internal proposal/intention split.

## Dependency Consequence
Cross-domain execution remains external dependencies.

## Authority / SoT / Actual-state Consequence
No Admission/Effect authority transfer.

## RCP Consequence
RCP-24 and future RCP-12 correlations remain bounded.

## Failure / Offline Consequence
An unavailable governance/execution path leaves proposal/intention unresolved; success is not fabricated.

## Explicit Non-implications
No direct provider tool execution guarantee.

## Deferred Implementation Mechanics
Tool-call parser, execution adapter, request schemas.

## Revalidation Trigger
Any bypass of S8 or source executor authority.

---

# CID-AG-B1-DAD-011 — Harness Loop Is Not Automation Workflow Semantics

## Decision / Issue
How to prevent Agent loop control from becoming a second Automation engine?

## Context
NSH may internally branch/loop/wait, while S6 is the accepted Automation Definition/Workflow Authority.

## Alternatives Considered
A. Treat Harness steps as reusable workflow definitions.
B. Put all Agent reasoning into S6 Automation.
C. Keep Harness local reasoning/execution sequencing operation-scoped and non-canonical as Automation semantics.

## Selected Design-semantic Result
**C.**

## Rationale
The same syntactic constructs can have different semantic ownership; reusable business workflow meaning belongs S6.

## Responsibility Consequence
A2-R04 owns local loop coordination only.

## Dependency Consequence
Automation invocation/authoring remains future A6/S6.

## Authority / SoT / Actual-state Consequence
Automation Authority/SoT unchanged.

## RCP Consequence
No new workflow RCP.

## Failure / Offline Consequence
Local loop failure remains Agent runtime fact, not Automation state.

## Explicit Non-implications
No graph/DAG/workflow engine selected.

## Deferred Implementation Mechanics
Agent loop framework/graph/state machine.

## Revalidation Trigger
Harness steps proposed as reusable governed workflow definitions.

---

# CID-AG-B1-DAD-012 — Harness-local Continuation Is Not Runtime Scheduling/Dispatch

## Decision / Issue
How much sequencing can NSH own without becoming a second Runtime Scheduler?

## Context
A2 must progress one Agent operation; R2/RT-R02 owns cross-component scheduling/routing/dispatch.

## Alternatives Considered
A. NSH owns universal scheduling.
B. Every local model/context step goes through RT-R02.
C. A2 owns Agent-local continuation/next-activity decisions; RT roles remain owner for cross-component coordination.

## Selected Design-semantic Result
**C.**

## Rationale
This preserves both Agent autonomy and Runtime coordination authority.

## Responsibility Consequence
A2-R04/R07 own local decisions.

## Dependency Consequence
Cross-component continuation uses RT-R03/RT-R02 as applicable.

## Authority / SoT / Actual-state Consequence
No scheduler authority transfer.

## RCP Consequence
No new scheduler contract; RCP-06 remains external coordination where applicable.

## Failure / Offline Consequence
Local wait/readiness can be represented without claiming route/dispatch success.

## Explicit Non-implications
No priority/fairness/timer/queue/scheduler algorithm.

## Deferred Implementation Mechanics
Execution loop/event loop/timer implementation.

## Revalidation Trigger
Cross-component work ordering proposed as A2 final authority.

---

# CID-AG-B1-DAD-013 — HITL Submission / Routing / Applicability / Application Separation

## Decision / Issue
Who owns the stages of Agent Human-in-the-loop response?

## Context
RCP-16 spans A2, S11 and future W3.

## Alternatives Considered
A. Inbox/submission determines Agent continuation automatically.
B. A2 owns human submission occurrence.
C. WB future owns submission occurrence, S11 routing/projection, A2 source wait/applicability/application result.

## Selected Design-semantic Result
**C.**

## Rationale
This preserves source-domain semantic ownership.

## Responsibility Consequence
A2-R10 owns Agent-side wait/applicability.

## Dependency Consequence
S11/WB links are external evidence/correlation.

## Authority / SoT / Actual-state Consequence
No Human Task universal SoT created.

## RCP Consequence
RCP-16 AG-R01 contribution closes at current design level; full closure not claimed.

## Failure / Offline Consequence
Stale/wrong-context/unauthorized/indeterminate responses remain explicit.

## Explicit Non-implications
No assignment/timeout/first/latest response winner law.

## Deferred Implementation Mechanics
Human task schema/API/UI.

## Revalidation Trigger
Any universal response winner/assignment policy required.

---

# CID-AG-B1-DAD-014 — Harness Checkpoint Is Source Evidence, Not Canonical Product State

## Decision / Issue
What is a checkpoint architecturally?

## Context
Long-running/cross-session continuity needs durable evidence, but persistence/SoT must not be inferred.

## Alternatives Considered
A. Checkpoint is canonical complete Agent/Product state.
B. Checkpoint is implementation-only and carries no stable semantics.
C. Checkpoint is A2 source-owned continuation evidence referencing operation/context/invocation/governance facts, subject to requalification.

## Selected Design-semantic Result
**C.**

## Rationale
This supports restart tolerance without creating a new SoT.

## Responsibility Consequence
A2-R11 owns checkpoint semantics.

## Dependency Consequence
Checkpoint links by HPL/EL to source facts; recovery coordination through RCP-20.

## Authority / SoT / Actual-state Consequence
Checkpoint does not become A1 SoT or external SoT.

## RCP Consequence
RCP-09/20/22 carry checkpoint references/provenance.

## Failure / Offline Consequence
Checkpoint can be stale/partial/conflicting/unavailable; resume is not assumed.

## Explicit Non-implications
No deterministic replay, checkpoint store or snapshot format.

## Deferred Implementation Mechanics
Persistence, serialization, compaction, storage location.

## Revalidation Trigger
Any claim of checkpoint as canonical cross-domain state or deterministic replay guarantee.

---

# CID-AG-B1-DAD-015 — Agent-side Recovery/Reconciliation Remains Source-owner Participation

## Decision / Issue
How does A2 participate in RCP-20 without replacing RT-R04 or external source owners?

## Context
Targeted authorization explicitly added Agent-side RCP-20.

## Alternatives Considered
A. A2 becomes recovery coordinator/conflict winner.
B. RT-R04 reconstructs Agent source truth.
C. A2 re-observes/re-qualifies its own source facts; RT-R04 coordinates evidence exchange/reconciliation stages.

## Selected Design-semantic Result
**C.**

## Rationale
Matches governed per-partition Actual-state ownership.

## Responsibility Consequence
A2-R11 is principal RCP-20 Agent source owner.

## Dependency Consequence
RT-R04 is XED/ACD; A3/A4/external source evidence remains owner-specific.

## Authority / SoT / Actual-state Consequence
No recovery authority transfer.

## RCP Consequence
Agent source-owner contribution closes at current design level; full RCP-20 not claimed.

## Failure / Offline Consequence
Conflicts remain explicit; no latest/local/central winner.

## Explicit Non-implications
No reconciliation/replay engine or authoritative synchronization direction.

## Deferred Implementation Mechanics
Recovery transport, persistence, conflict-resolution mechanism.

## Revalidation Trigger
Need for a conflict winner, fail-open/closed law or source rewrite.

---

# CID-AG-B1-DAD-016 — Trial Runtime Is Separate from Production Acceptance/Admission

## Decision / Issue
How are Agent trial semantics partitioned?

## Context
A1 is trial semantic owner; A2 is Agent trial runtime participant; external effects retain source owners.

## Alternatives Considered
A. Trial success automatically promotes production.
B. Treat trial as ordinary production runtime.
C. A1 Trial Intent references definition revision; A2 owns trial Agent runtime facts; acceptance/admission remain external/separate.

## Selected Design-semantic Result
**C.**

## Rationale
Preserves accepted lifecycle separation.

## Responsibility Consequence
A1-R06 and A2-R12 split semantic intent/runtime facts.

## Dependency Consequence
A3/A4/Node contributions are correlated external facts.

## Authority / SoT / Actual-state Consequence
Trial does not transfer Artifact/Admission authority.

## RCP Consequence
RCP-17 Agent side closes at current design level only.

## Failure / Offline Consequence
Trial may be partial/indeterminate and may have real effects if executor semantics permit.

## Explicit Non-implications
Dry-run is not guaranteed effect-free.

## Deferred Implementation Mechanics
Sandbox/test runner/simulation environment.

## Revalidation Trigger
Product-wide fully isolated trial guarantee or automatic promotion.

---

# CID-AG-B1-DAD-017 — Definition / Desired / Applied / Observed Configuration Separation

## Decision / Issue
How should Agent definition configuration and managed runtime configuration coexist?

## Context
A1 owns definition semantics; S9 owns managed desired state; runtime owners own Applied facts.

## Alternatives Considered
A. Treat A1 Definition as runtime Applied config.
B. Let S9 own Agent semantic item meaning.
C. Preserve item semantic ownership in A1/A2/A3/A4, Desired in S9, Applied in actual applying boundary, Observed as projection.

## Selected Design-semantic Result
**C.**

## Rationale
Matches accepted configuration topology.

## Responsibility Consequence
A2/A3/A4 may produce Applied evidence where genuinely applicable; A1 remains definition owner.

## Dependency Consequence
RCP-19 links S9 desired to local applied owners.

## Authority / SoT / Actual-state Consequence
`Desired != Applied`; no config authority transfer.

## RCP Consequence
Agent Applied contribution closes at current design level.

## Failure / Offline Consequence
Stale/partial/non-applied conditions remain explicit.

## Explicit Non-implications
Configuration is not Secret; no rollout policy.

## Deferred Implementation Mechanics
Config files/watch/push/pull/storage.

## Revalidation Trigger
Any proposal to move configuration item semantics or desired SoT.

---

# CID-AG-B1-DAD-018 — Diagnostics/Provenance Are Federated by Original Fact Ownership

## Decision / Issue
Should NSH create one canonical Agent diagnostics state?

## Context
RCP-22 requires all fact owners to provide diagnostics/provenance.

## Alternatives Considered
A. NSH owns a universal Agent diagnostic SoT.
B. Only raw logs are diagnostics.
C. A1-A4 each own diagnostics for their own source facts; NSH correlates without canonicalizing.

## Selected Design-semantic Result
**C.**

## Rationale
Aggregation must not transfer Actual-state ownership.

## Responsibility Consequence
A1-R07, A2-R13, A3-R07, A4-R08 are source producers.

## Dependency Consequence
Cross-fact correlation uses EL/HPL.

## Authority / SoT / Actual-state Consequence
No universal Diagnostic SoT.

## RCP Consequence
A1-A4 RCP-22 contribution is complete at current Batch design level; full closure downstream.

## Failure / Offline Consequence
Diagnostics can be stale/partial while source facts remain valid at owner.

## Explicit Non-implications
Provider-private hidden reasoning is not required diagnostic payload.

## Deferred Implementation Mechanics
Log/trace storage/UI/telemetry backend.

## Revalidation Trigger
Diagnostic aggregation proposed as canonical source truth.

---

# CID-AG-B1-DAD-019 — Private/Offline Core Correctness Does Not Depend on Public Provider

## Decision / Issue
What provider dependency can core Agent correctness assume?

## Context
Constitution/capability baseline require local/private/Internet providers and private deployment.

## Alternatives Considered
A. Public SaaS provider mandatory for core Agent correctness.
B. Offline mode has separate weaker Agent semantics.
C. Agent semantics remain provider-neutral; public provider unavailability is a capability/availability condition, not an authority change.

## Selected Design-semantic Result
**C.**

## Rationale
Preserves private deployment and provider replaceability.

## Responsibility Consequence
A3 models unavailable/unknown capability; A2 adapts only within A1 semantics.

## Dependency Consequence
No mandatory public external dependency.

## Authority / SoT / Actual-state Consequence
Offline does not transfer authority.

## RCP Consequence
RCP-09/10/20/22 include private/offline qualification.

## Failure / Offline Consequence
Provider unavailable may yield unsupported/unknown/alternative compatible strategy; no fabricated success.

## Explicit Non-implications
No guarantee every Agent revision is runnable on every offline provider.

## Deferred Implementation Mechanics
Local provider products, network failover, packaging.

## Revalidation Trigger
Mandatory public control plane/provider proposal.

---

# CID-AG-B1-DAD-020 — Hard SDD Topology Is Directed from Definition/Identity Semantics to Typed Evidence

## Decision / Issue
How to prevent A2↔A3↔A4 feedback from becoming a semantic-definition cycle?

## Context
A2 consumes A3/A4 evidence, while A3/A4 correlate to A2 operation/invocation identities.

## Alternatives Considered
A. Treat all bidirectional runtime exchange as SDD.
B. Ignore dependency taxonomy.
C. Define generic operation/context/invocation semantics upstream in A2; typed A3/A4 evidence depends on them by SDD; runtime feedback is ACD/EL.

## Selected Design-semantic Result
**C.**

## Rationale
Evidence application does not redefine the identity semantics it references.

## Responsibility Consequence
A2-R01/R03/R08 are generic identity definers; A3/A4 refine typed evidence.

## Dependency Consequence
Hard SDD graph is acyclic; A3/A4→A2 runtime feedback is ACD/EL.

## Authority / SoT / Actual-state Consequence
No circular ownership.

## RCP Consequence
RCP-09/10 remain distinct but correlatable.

## Failure / Offline Consequence
Stale evidence can be applied without redefining identity.

## Explicit Non-implications
Does not prohibit runtime feedback loops; it classifies them correctly.

## Deferred Implementation Mechanics
Module dependency graph/import direction.

## Revalidation Trigger
A later semantic definition requires reverse ownership/definition dependency.

---

# CID-AG-B1-DAD-021 — A5/A6 Extension Seams Are Preserved Without Internal-design Preemption

## Decision / Issue
How should Batch 1 remain future-proof for Multi-Agent and cross-domain delegation?

## Context
NSH is expected eventually to participate in A5/A6, but those boundaries are not authorized.

## Alternatives Considered
A. Design A5/A6 now to complete Harness.
B. Ignore future seams and risk Batch-1 dead ends.
C. Preserve opaque representation-neutral correlation/target seams only; defer all A5/A6 semantics.

## Selected Design-semantic Result
**C.**

## Rationale
Future-proofing does not require unauthorized semantic invention.

## Responsibility Consequence
A2/A4 may carry opaque future composition/delegation correlation references only.

## Dependency Consequence
RCP-11 remains future A5; RCP-12 owner/source side remains future A6.

## Authority / SoT / Actual-state Consequence
No AG-R03/AG-R04 ownership preemption.

## RCP Consequence
Only bounded RCP-12 consumer/correlation expectation is recorded.

## Failure / Offline Consequence
Unknown/unavailable future targets remain opaque; no policy inferred.

## Explicit Non-implications
No supervisor/graph/handoff/shared-memory/Automation invocation semantics.

## Deferred Implementation Mechanics
All A5/A6 internal design.

## Revalidation Trigger
Need to make a current Batch-1 decision that determines A5/A6 semantics materially.

---

# CID-AG-B1-DAD-022 — MDE / Implementation Stop Boundary for NSH

## Decision / Issue
What must this producing session refuse to decide?

## Context
Harness architectures commonly absorb scheduler/workflow/retry/storage/provider/framework commitments if not explicitly bounded.

## Alternatives Considered
A. Allow implementation convenience to choose these matters.
B. Freeze common industry choices now.
C. Explicitly classify Owner/MDE and implementation mechanics as stop/defer boundaries.

## Selected Design-semantic Result
**C.**

MDE STOP if materially required:

```text
new Product Capability
new Authority / SoT / Actual-state owner
new Trust/security boundary
universal scheduler/routing/dispatch authority
new Workflow/Automation Authority
universal retry/cancel/rollback/compensation/once guarantee
material fail-open/fail-closed law
conflict winner / merge / authoritative synchronization law
major universal identity namespace
mandatory public SaaS/broker/workflow/recovery dependency
provider/framework/protocol/storage lock-in or other high-migration commitment
```

Implementation deferrals include all concrete framework/provider/API/schema/storage/process/deployment choices.

## Rationale
Prevents NSH from becoming a vehicle for hidden architecture migration.

## Responsibility Consequence
All A1-A4 responsibilities include revalidation boundaries.

## Dependency Consequence
No dependency on concrete technology is architecture-defining.

## Authority / SoT / Actual-state Consequence
Accepted topology remains fixed.

## RCP Consequence
No RCP is implemented by technology selection at this phase.

## Failure / Offline Consequence
No implicit fail policy/retry guarantee.

## Explicit Non-implications
Technology neutrality does not mean later implementation is unconstrained; it must conform to these semantics.

## Deferred Implementation Mechanics
All items explicitly excluded by authorization.

## Revalidation Trigger
Any material pressure listed above.

---

# DAD Summary

```text
DAD Set
→ CID-AG-B1-DAD-001..022

DAD Count
→ 22

New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Owner-reserved MDE Disguised as DAD
→ NONE_FOUND

Product Capability Change
→ 0

Authority / SoT / Final Actual-state Transfer
→ 0

New Agent Boundary
→ 0

New Runtime Role
→ 0

New Cross-component RCP
→ 0

Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND
```

The DAD set is evidence for independent GAC review only. It is not Global Acceptance.