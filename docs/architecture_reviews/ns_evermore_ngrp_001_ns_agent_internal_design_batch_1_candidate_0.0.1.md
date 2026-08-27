# NGRP-001 — ns_agent Component Internal Design / Batch 1 Candidate

## Authority Metadata

- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Producing Session:** `NGRP-001 — Component Internal Design / ns_agent / Batch 1`
- **Producing Entry HEAD:** `6b4f71eb1531a91df1ad7c24ef59d0c9f1613354`
- **Recovered GAC Epoch:** `GAC-EPOCH-0089`
- **Recovered State Verified Through HEAD:** `16bff30f6c0f3490ad64c14649e5e025f9a0c1a1`
- **Decision Registry:** `0.0.32 / CURRENT / NORMATIVE`
- **Authorization Transition:** `GAC-TR-0100 → GAC-EPOCH-0089`
- **Exact Authorization Scope:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_AGENT / BATCH_1 / AGENT_DEFINITION_HARNESS_RUNTIME_PROVIDER_TOOL_KNOWLEDGE_EXECUTION_BOUNDARY_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Authorized Internal Boundaries:** `A1 / A2 / A3 / A4`
- **Inherited Runtime Roles:** `AG-R01 / AG-R02`
- **Named Internal Architecture Concept:** `ns_evermore Harness / NSH`
- **Producing-session Maximum Legal State:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Candidate Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`

---

# 1. Scope and Non-authority Statement

This Candidate performs Component Internal Design only for:

```text
A1 — Agent Definition & Evolution
A2 — Agent Runtime Context, HITL & Actual-state
A3 — Model / Provider Mediation & Multimodal Capability
A4 — Tool & Knowledge Consumption
```

It explicitly synthesizes the authorized named internal architecture pressure:

```text
ns_evermore Harness / NSH
→ named internal architecture concept
→ NOT Product Component
→ NOT A7
→ NOT Runtime Role
→ NOT Shared Foundation
→ NOT SDK authority
```

The Candidate does **not** perform internal design for:

```text
A5 — Native Multi-Agent Composition
A6 — Governed Cross-domain Delegation & Automation Participation
```

A5/A6 appear only as representation-neutral future extension seams where required to prevent a Batch-1 architecture dead end.

This Candidate does not perform:

```text
System-level SDK Detailed Design
Design-to-Implementation Readiness
Implementation Planning
IWP
Coding
package/module/class hierarchy
API / DTO / schema / wire design
persistence/database/event-store design
process/service/worker/thread/coroutine topology
container/deployment topology
framework/provider/library adoption
```

No statement in this Candidate claims Global Acceptance, `ns_agent` Internal Design Exhaustion, `ns_agent` Global Closure, or Full Cross-component Closure of any RCP.

---

# 2. Fresh Repository Recovery Result

At producing-session entry:

```text
Actual Branch HEAD
→ 6b4f71eb1531a91df1ad7c24ef59d0c9f1613354

Current Global State
→ GAC-EPOCH-0089

State Verified Through HEAD
→ 16bff30f6c0f3490ad64c14649e5e025f9a0c1a1

State-to-HEAD Delta
→ exactly 1 commit
→ Global Architecture State authorization seal only

Delta Classification
→ EXPECTED_GOVERNANCE

Current Authorized Phase
→ NGRP-001 — Component Internal Design / ns_agent / Batch 1

Authorization Scope
→ COMPONENT_INTERNAL_DESIGN_ONLY / NS_AGENT / BATCH_1 / AGENT_DEFINITION_HARNESS_RUNTIME_PROVIDER_TOOL_KNOWLEDGE_EXECUTION_BOUNDARY_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Semantic Gap
→ NONE

Blocking Item
→ NONE

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE
```

Recovery Gate: `PASS`.

The mandatory Repository read set identified by `GAC-EPOCH-0089` was consumed, including the Constitution, Unified Governance, current State/Working State/Ledger continuation, Decision Registry, Project Architecture, accepted Five-component capability/boundary evidence, Runtime Responsibility Architecture, Shared Foundation readiness, closed `ns_server/ns_runtime/ns_node` upstream, `ns_agent` entry-readiness assessment, NSH insertion assessment and targeted authorization revalidation.

---

# 3. Inherited Architecture Facts

## 3.1 Product and authority topology

```text
Exactly Five Product Components
→ ns_server
→ ns_runtime
→ ns_node
→ ns_agent
→ ns_web

AI Agent Definition / Semantic Authority
→ ns_agent / A1

AI Agent Canonical Definition SoT
→ ns_agent / A1

Agent Runtime Actual-state
→ A2 / AG-R01 for facts genuinely originating in Agent runtime

Provider Mediation bounded observations
→ A3 / AG-R02 where genuinely originating there

Automation Definition / Workflow Authority
→ ns_server / S6

Formal Artifact Acceptance / Execution Admission
→ ns_server / S8

Routing / Scheduling / Dispatch Coordination
→ ns_runtime / R2 / RT-R02

Continuation / Delegation / Intervention Coordination
→ ns_runtime / R3 / RT-R03

Recovery / Reconciliation Coordination
→ ns_runtime / R4 / RT-R04

Node capability/readiness
→ N1 / ND-R01

Node local execution Attempt
→ N2 / ND-R02

Node protected local Effect / Node-origin source fact
→ N3 / ND-R03

Knowledge / external factual SoT
→ original applicable owner
```

## 3.2 Permanent Agent / NSH non-collapse

```text
Model != Agent
Model Provider != Agent Authority
Tool Provider != Agent Semantic Authority
Agent Consumes Knowledge != Agent Owns Knowledge
RAG Consumption != Knowledge Authority Transfer
Agent Definition SoT != Formal Artifact Acceptance Authority
Agent Definition != Agent Runtime Actual-state
Agent Intent != Formal Execution Admission
Agent Delegation != Node Attempt
Agent Runtime Success != Node Effect automatically
Human Response Submitted != Agent Response Applied
Candidate Automation != Accepted Automation

Harness != Agent Definition Authority automatically
Harness != Policy Authority
Harness != Trust Authority
Harness != Artifact Acceptance Authority
Harness != Execution Admission Authority
Harness Action Proposal != Authorized Execution
Harness Tool Selection != Execution Admission
Harness Invocation != Protected Effect
Harness Tool Result != Business Semantic Success automatically
Harness Delegation != Node Effect Ownership
Harness Automation Invocation != Automation Authority
Harness Multi-Agent Coordination != New Multi-Agent Authority
Harness Context Cache != Knowledge SoT
Harness Memory != External Data SoT
Harness Checkpoint != Canonical Product State automatically
Harness Recovery != SoT Transfer
Harness Retry != Prior Attempt Erasure
Harness Scheduling Convenience != Universal Runtime Scheduling Authority
Harness Agent Loop != Automation Workflow Semantics
Harness-local continuation != ns_runtime cross-component routing/scheduling/dispatch
```

Also permanent:

```text
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Dispatch != Attempt
Attempt != Protected Effect
Reference != Authority
Correlation != Ownership
Observation != Canonicalization
Retry != historical mutation
Recovery != original fact rewrite
Reconnect != Reconciled
Latest Timestamp != Canonical Winner
```

---

# 4. Batch-1 Architecture Result Summary

This Candidate decomposes A1-A4 into **35 architecture-semantic internal responsibilities**:

```text
A1 → 7 responsibilities
A2 → 13 responsibilities
A3 → 7 responsibilities
A4 → 8 responsibilities
Total → 35
```

No new accepted Component Internal Boundary is introduced.

The named NSH concept is synthesized as a cross-boundary internal topology:

```text
A1 Definition / Revision semantics
        │
        ▼
A2 Agent Runtime + NSH Core
   │                │
   │                ├──────── consumes A3 provider/model capability evidence
   │                │
   │                └──────── consumes A4 tool/knowledge consumption evidence
   │
   ├──────── emits Agent-runtime source facts
   └──────── preserves future A5/A6 extension seams only
```

NSH is an internal cohesion construct, not a fifth Agent authority partition.

---

# 5. A1 — Agent Definition & Evolution Internal Architecture

## A1-R01 — Agent Definition Identity & Canonical Revision Custody

Owns the representation-neutral identity and revision semantics of the canonical native Agent Definition.

Required semantics:

```text
Agent Definition Identity
Agent Definition Revision Identity
revision predecessor / successor lineage
canonical revision establishment
historical revision retention
current vs historical qualification
Tenant / governance context association
```

A canonical Agent revision is established only by A1 semantic authority. Source file state, visual editor state, Provider state, Harness runtime state, Artifact state and installed/runtime copies are not canonical Agent Definition SoT by possession.

Permanent:

```text
Agent Definition Identity != Agent Operation Identity
Agent Definition Revision != Runtime Context Revision
Latest Copy != Canonical Definition automatically
```

No UUID/key format or physical persistence model is selected.

## A1-R02 — Durable Agent Semantic Content & Intent Governance

Owns durable Agent semantic meaning contained in or referenced by a canonical Agent revision, including where applicable:

```text
system-prompt / instruction semantics
behavioral intent and durable constraints
runtime capability requirements
permitted/required model capability requirements
permitted/required tool/knowledge bindings by semantic reference
HITL-related durable semantic requirements
multimodal semantic requirements
trial-relevant semantic intent
```

This responsibility deliberately excludes transient Harness strategy.

```text
Durable Agent Semantics
!= current model workaround
!= one reasoning scaffold
!= one context-compaction method
!= provider-specific transient limitation
```

Current-generation model limitations MUST NOT be promoted into canonical Agent semantics merely because a present Provider requires them.

## A1-R03 — Provider / Model / Tool / Knowledge Reference & Requirement Governance

Owns Agent-definition-level reference semantics and capability requirements for model/provider/tool/knowledge dependencies without acquiring the authority of those referenced subjects.

A1 may express:

```text
required / optional capability classes
compatibility constraints
allowed semantic references
required modality classes
required tool/knowledge capability semantics
```

A1 does not own live provider availability, live tool availability, Knowledge factual truth, provider routing outcome or Node execution result.

Permanent:

```text
Definition Reference != Runtime Selection
Definition Requirement != Provider Capability Observation
Tool Reference != Tool Effect
Knowledge Reference != Knowledge SoT Transfer
```

## A1-R04 — Dual-authoring Change Intake & Semantic Convergence

Owns convergence of authorized source/SDK-authored and visual-authored Agent semantic changes into one canonical Agent definition domain.

Required semantics:

```text
change intent/reference
base revision
semantic compatibility/conformance result
conflict/unsupported/non-editable qualification
canonical revision establishment only after A1-owned semantic decision
```

Permanent:

```text
Source Authoring != Separate Agent Semantics
Visual Authoring != Separate Agent Semantics
Different Authoring Surface != Different Definition SoT
```

No AST/IR/DSL/editor model is selected. Lossless representation round-trip is not inferred.

## A1-R05 — Definition Validation, Compatibility & Conformance

Owns Agent-domain validation and conformance of a proposed/canonical Agent revision against accepted Agent semantics and referenced capability requirements.

It consumes, by reference where applicable:

```text
provider/model capability observations from A3
Tool/Knowledge capability compatibility evidence from A4
shared Compatibility & Conformance mechanics
Tenant/Policy/Trust context from accepted server authorities
```

Validation result is distinct from Artifact Acceptance and Execution Admission.

```text
Definition Validated != Artifact Accepted
Definition Compatible != Execution Admitted
Provider Compatible != Provider Selected automatically
```

## A1-R06 — Governed Trial Intent & Runtime Binding Eligibility

Owns Agent-domain trial intent semantics for a specific Agent definition revision and the semantic eligibility of a revision to be bound into an Agent runtime context.

Trial intent preserves:

```text
Agent Definition Identity + Revision
trial purpose/reference
governance context references
capability requirements
expected semantic observation boundary
```

A2 owns actual Agent trial runtime facts. A3/A4/applicable external owners retain their own runtime/effect facts.

Permanent:

```text
Validation != Trial
Trial != Production
Trial Success != Artifact Accepted
Trial Success != Production Admitted
Dry-run != Effect-free automatically
```

## A1-R07 — Definition History, Migration, Provenance & Contract Governance

Owns non-destructive Agent definition history/provenance and migration/conformance semantics across revisions.

Required properties:

```text
historical Agent operations remain bound to the applicable definition revision
later revision does not rewrite earlier runtime interpretation
provider evolution does not rewrite Agent revision meaning
source/visual representation evolution preserves semantic provenance
compatibility/migration uncertainty remains explicit
```

A1-R07 is the A1 contribution to RCP-22 provenance and the upstream definition/revision input to RCP-09, RCP-10, RCP-16, RCP-17, RCP-20 and the Agent Harness Internal Stable Contract Pressure.

---

# 6. A2 — Agent Runtime Context, HITL & Actual-state Internal Architecture

A2 is the primary current runtime locus of NSH and the source owner for Agent-runtime Actual-state facts genuinely originating in `AG-R01`.

## A2-R01 — Agent Operation Origination & Operation Identity

Owns representation-neutral **Agent Operation Identity** for one durable Agent runtime operation.

An Agent Operation may outlive:

```text
one process/runtime instance
one model invocation
one tool invocation
one browser/web session
one HITL wait
one reconnect
one runtime execution episode
```

Agent Operation Identity remains stable across legitimate continuation when the same semantic operation continues.

Permanent:

```text
Agent Operation Identity != Agent Definition Identity
Agent Operation Identity != Agent Runtime Attempt Identity
Agent Operation Identity != Harness Invocation Identity
Agent Operation Identity != Node Attempt Identity
```

No global universal identity namespace or physical format is selected.

## A2-R02 — Runtime Definition / Governance / Admission Context Binding

Owns the runtime binding evidence that associates one Agent Operation with:

```text
Agent Definition Identity + Revision
Tenant / Organization / Principal context as applicable
Policy / Trust evidence references
Artifact/Admission evidence where applicable
Managed runtime configuration references
trial vs production context
correlation/provenance context
```

Binding consumes accepted authority; it does not create it.

```text
Runtime Binding != Definition Authority
Runtime Binding != Artifact Acceptance
Runtime Binding != Admission
```

If required upstream evidence is stale, unavailable or indeterminate, the Agent runtime must preserve that uncertainty; this Candidate selects no universal fail-open/fail-closed policy.

## A2-R03 — Agent Runtime Attempt / Continuation Episode Identity & Lineage

Owns **Agent Runtime Attempt Identity** for one bounded A2 execution episode established inside an Agent Operation.

One Agent Operation may have multiple Agent Runtime Attempts when retry/re-entry/recovery establishes a new bounded Agent-runtime execution responsibility instance.

Required lineage:

```text
Operation → one or more Runtime Attempts
Runtime Attempt → predecessor/re-entry/recovery lineage where applicable
Runtime Attempt → definition revision binding
Runtime Attempt → applicable context revision
```

Permanent:

```text
New Runtime Attempt != prior Attempt rewrite
Retry != same Attempt success mutation
Agent Runtime Attempt != Node Attempt
```

A continuation that does not establish a new execution responsibility instance need not invent a new Attempt; concrete trigger mechanics remain downstream.

## A2-R04 — NSH Local Reasoning / Execution Loop Coordination

Owns Agent-local NSH loop coordination inside one Agent Operation/Attempt.

This responsibility may express local runtime sequencing such as:

```text
prepare context
obtain model contribution
interpret contribution
prepare tool/knowledge invocation
await model/tool/HITL
reintegration
continue / yield / pause
finish Agent-local reasoning activity
```

This is **operation-local Agent runtime coordination**, not a reusable Automation workflow semantic domain and not a cross-component scheduler.

Permanent:

```text
Harness Step != Automation Step
Harness Branch != Automation Branch semantics
Harness Loop != Automation Workflow
Harness Wait != universal scheduler wait
Harness-local sequencing != RT-R02 scheduling/routing/dispatch
```

No state-machine implementation, graph framework, queue, scheduler, coroutine topology or universal step model is selected.

## A2-R05 — Runtime Context Contribution Intake & Source Attribution

Owns intake of context contributions into the Agent runtime while preserving each contribution's original authority/source attribution.

Potential contribution sources include, without creating an exhaustive wire taxonomy:

```text
A1 definition/instruction semantics
prior A2 operation/history evidence
A3 model/provider observations and model contribution evidence
A4 tool-result contributions
A4 Knowledge/RAG contributions
applicable human response evidence
accepted governance/configuration context
other accepted source references
```

For every contribution, A2 must preserve where applicable:

```text
source owner/reference
source revision/evidence reference
temporal applicability
currentness/freshness
uncertainty/partiality
sensitivity/redaction qualification
operation/invocation correlation
```

Permanent:

```text
Context Contribution != Source Fact Ownership Transfer
Context Inclusion != Source Canonicalization
```

## A2-R06 — Runtime Context Projection, Revision, Selection & Transformation

Owns the Agent-runtime **Context Projection** used by NSH for a specific operation/attempt/invocation.

Context Projection is a derived A2 runtime semantic object, not an external factual SoT.

Required semantic properties:

```text
operation/attempt association
Context Projection revision/lineage
selected contribution references
transformation/compaction provenance
known omission/partiality qualification where material
currentness/uncertainty
sensitivity/redaction qualification
invocation applicability
```

Context selection, prioritization and compaction may create a new Context Projection revision. They must not silently rewrite source provenance or turn a transformed summary into the original source fact.

Permanent:

```text
Context Projection != Knowledge SoT
Context Cache != Knowledge SoT
Agent Memory Projection != External Data SoT
Compacted Context != Original Source Fact
Later Context Revision != historical Context rewrite
```

No token budget, ranking algorithm, memory store or compaction algorithm is selected.

## A2-R07 — Model-adaptive Harness Strategy Decision & Applicability

Owns A2 runtime decision evidence for bounded Harness strategy selection/adaptation.

Permitted semantic inputs include:

```text
A1 durable Agent semantics and capability requirements
current A2 operation/context state
A3 provider/model capability-profile evidence
A4 applicable tool/knowledge capability evidence
governance/configuration evidence
runtime uncertainty/currentness
```

The resulting Harness strategy is an A2 runtime decision, not a canonical Agent definition rewrite.

Architecture law:

```text
Harness Strategy
→ MUST remain model-adaptive where applicable

Provider/Model Capability Profile
→ MAY inform bounded strategy adaptation

Current-generation model limitation
→ MUST NOT automatically become permanent Product Architecture
```

If required capabilities are unsupported/unknown/incompatible, that condition remains explicit. The runtime must not silently weaken A1 semantics merely to accommodate a Provider.

No provider ranking, fallback winner, fixed planner, fixed reasoning scaffold or concrete algorithm is selected.

## A2-R08 — Harness Invocation Identity, Target Correlation & Lineage

Owns generic representation-neutral **Harness Invocation Identity** for one Agent-runtime request to obtain a model/tool/knowledge/capability contribution.

Required semantics:

```text
Agent Operation reference
Agent Runtime Attempt reference
Context Projection revision reference
invocation kind / target semantic reference
parent/predecessor invocation lineage where applicable
strategy-decision reference where applicable
result/evidence correlation references
```

The generic identity enables A3/A4 to correlate their own source facts without transferring ownership.

Permanent:

```text
Harness Invocation != Provider Mediation Interaction
Harness Invocation != external Tool Attempt
Harness Invocation != Node Attempt
Harness Invocation != Node Effect
Harness Invocation != Authorized Execution automatically
```

A3/A4 define their own bounded evidence correlated to this identity.

## A2-R09 — Model Contribution Reintegration, Agent Decision & Action Proposal

Owns the Agent-runtime interpretation and reintegration of model/provider evidence into Agent runtime semantics.

Semantic sequence:

```text
A3 Provider/Model Output Observation
→ A2 Model Contribution qualification
→ A2 Agent runtime interpretation/decision
→ optional Harness Action Proposal
→ later applicable governed invocation path
```

A model-native tool call or structured suggestion remains provider/model output evidence until A2 accepts/interprets it as an Agent-runtime proposal.

Permanent:

```text
Model Output != Agent Decision
Model Tool-call Suggestion != Authorized Tool Execution
Harness Action Proposal != Execution Admission
Harness Action Proposal != Node Attempt
Harness Action Proposal != Automation Authority
```

A proposal intended for future A6 cross-domain delegation remains only a proposal/seam in Batch 1; A6 semantics are not designed here.

## A2-R10 — HITL Wait, Human-response Applicability & Continuation

Owns the Agent source-side Human Task wait/applicability semantics required by RCP-16.

A2 owns representation-neutral evidence for:

```text
Agent Human Wait identity/reference
originating Agent Operation / Attempt
Agent Definition revision
wait context/reference
required/expected response semantic applicability
currentness/staleness
response applicability decision
Agent-side application/rejection/indeterminate result
continuation correlation
```

`SV-R07/S11` owns aggregation/routing facts; `WB-R01` owns human response submission occurrence when later designed.

Permanent:

```text
Human Response Submitted != Response Applied
Response Routed != Response Applicable
Response Applicable != Agent Operation Completed
Human Response != Policy Permit
Human Response != Admission
```

No assignment, timeout, first-response-wins, latest-response-wins or conflict-winner policy is selected.

## A2-R11 — Checkpoint, Long-running Continuation & Recovery Participation

Owns A2 source facts needed for durable Agent continuation and the Agent-side RCP-20 source-owner participation.

A **Harness Checkpoint Evidence** is a representation-neutral A2 source assertion that may reference sufficient continuation-relevant evidence, including where applicable:

```text
Agent Operation
Agent Runtime Attempt lineage
Agent Definition revision
Context Projection revision
current wait/continuation condition
in-flight or completed Harness Invocation references
relevant model/tool/knowledge evidence references
governance/admission/configuration references
currentness/uncertainty/partiality
```

Checkpoint semantics are deliberately evidence-oriented.

Permanent:

```text
Checkpoint != Canonical Agent Definition
Checkpoint != Canonical Product State
Checkpoint != external source SoT
Checkpoint Observed != Operation Resumed
Resume Requested != Resumed
Recovery Participation != Recovery Outcome
```

On recovery/re-entry A2 re-observes and re-qualifies **its own** source facts. It may correlate A3/A4/external evidence but cannot rewrite their source facts.

RCP-20 rules:

```text
RT-R04 owns recovery/reconciliation coordination-stage facts
A2 owns Agent-runtime source facts
Latest Timestamp != Canonical Winner
Latest Arrival != Canonical Winner
Conflict Detected != Conflict Resolved
Recovery != Original Fact Rewrite
Replay != Retroactive Authorization
```

No checkpoint storage, deterministic replay, merge law or universal resume algorithm is selected.

## A2-R12 — Trial & Intervention Receiving / Outcome Qualification

Owns A2 Agent-runtime facts for Agent trial execution and Agent-targeted intervention applicability/outcomes.

Trial:

```text
A1 Trial Intent / Definition Revision
→ A2 Trial Agent Operation / Runtime Attempt
→ A3/A4/applicable executor contributions
→ A2 Agent trial semantic/runtime outcome
```

Intervention:

```text
WB/SDK future source intent
→ applicable routing/coordination
→ A2 receipt/applicability
→ A2 Agent-runtime outcome if genuinely A2-owned
```

Permanent:

```text
Trial Success != Production Admission
Cancel Requested != Cancelled
Retry Requested != Retry Started
Resume Requested != Resumed
Recovery Requested != Recovered
Stopped != Effects Reversed
```

RCP-24 source-side interaction semantics remain downstream.

## A2-R13 — Runtime Outcome, Currentness, History, Provenance & Diagnostics

Owns non-destructive A2 history and diagnostics for Agent-runtime facts genuinely originating in A2.

Required dimensions include:

```text
operation / runtime-attempt identity
applicable definition revision
context revision
Harness invocation lineage
HITL wait/applicability evidence
trial/intervention correlation
checkpoint/recovery participation
outcome qualification
currentness/freshness
availability
uncertainty/partiality/conflict qualification
Tenant/Principal/governance provenance
sensitivity/redaction
compatibility/conformance version
```

History is append-preserving at the semantic level:

```text
later success != earlier failure deletion
retry != prior Attempt mutation
recovery != prior uncertainty deletion
new context revision != prior context rewrite
provider replacement != historical provider evidence rewrite
```

RCP-09 and RCP-22 consume these source-owned facts. Diagnostics may expose explicit runtime decisions/evidence but do not require exposure of provider-private hidden reasoning.

---

# 7. A3 — Model / Provider Mediation & Multimodal Capability Internal Architecture

## A3-R01 — Provider / Model Reference & Mediation-context Binding

Owns A3 mediation binding between an A2 Harness Invocation and an applicable provider/model reference under the current governance/configuration context.

Binding records semantic correlation only. It does not make provider selection a Product Authority or rewrite A1 semantics.

```text
Provider Reference != Agent Authority
Provider Binding != Definition Rewrite
Mediation Binding != Trust/Policy Permit
```

No provider SDK/protocol is selected.

## A3-R02 — Provider / Model Capability-profile Observation & Revision

Owns bounded Agent-domain observations of provider/model capabilities and availability required by RCP-10.

Required dimensions where applicable:

```text
provider/model semantic reference
capability subject/reference
observation revision/lineage
observed support / non-support / unknown qualification
availability/currentness/freshness
uncertainty/conflict
observation temporal context
source/provenance
```

These are `AG-R02` bounded observations, not provider Product Authority.

```text
Capability Observation != Provider Canonical Truth automatically
Capability Profile != Agent Definition
Availability != Admission
```

## A3-R03 — Compatibility, Conformance & Multimodal Qualification

Owns Agent-domain compatibility/conformance assertions between A1 capability requirements and observed provider/model capabilities.

Includes representation-neutral multimodal compatibility semantics without choosing media formats or provider APIs.

Outcomes may express supported/unsupported/unknown/stale/conflicting applicability without a universal provider winner.

Permanent:

```text
Compatible != Selected automatically
Unsupported Provider != Agent Definition Rewrite
Provider Limitation != Product Architecture Limitation automatically
```

## A3-R04 — Provider Mediation Interaction & Harness-invocation Correlation

Owns representation-neutral **Provider Mediation Interaction** actual-state for one A3 mediation interaction correlated to an A2 Harness Invocation.

Required distinction:

```text
A2 Harness Invocation
!= A3 Provider Mediation Interaction
```

A Provider Mediation Interaction may record request/interaction/response/failure observation facts genuinely established by A3. It remains subordinate to the Agent Operation correlation but has its own owner partition.

No HTTP/gRPC/provider request schema is selected.

## A3-R05 — Provider Response / Failure / Availability Observation

Owns A3 bounded observations arising from provider/model mediation, including where applicable:

```text
response observed
provider-side refusal/error observation
unavailable/unreachable/timeout-like indeterminate observation
partial/malformed/unsupported result qualification
usage/capability evidence where semantically relevant and permitted
```

A3 does **not** own the Agent semantic interpretation/outcome.

```text
Provider Response Observed != Agent Decision
Provider Success != Agent Success
Provider Failure != Agent Operation Failure automatically
```

A2-R09 owns Agent-runtime reintegration/interpretation.

## A3-R06 — Provider Evolution / Replacement & Harness-adaptation Input

Owns compatibility-sensitive mediation evidence needed when provider/model capability or version changes.

A3 provides bounded adaptation inputs to A2, including:

```text
capability-profile revision
compatibility/conformance result
currentness/uncertainty
provider/model evolution reference
```

A2 owns the Harness Strategy decision.

```text
A3 Capability Evidence != A2 Strategy Decision
Provider Replacement != Agent Semantic Rewrite
```

No automatic fallback order, provider priority or model-routing algorithm is selected.

## A3-R07 — Mediation History, Secret / Privacy Boundary & Diagnostics

Owns non-destructive A3 provenance/diagnostics for provider mediation facts.

Required rules:

```text
secret material is not ordinary mediation evidence
only authorized secret references/status may appear
sensitive multimodal/context payload exposure is minimized/redacted
provider failure history is retained
provider replacement does not rewrite historical evidence
currentness and uncertainty remain explicit
```

A3 contributes RCP-10 and RCP-22 evidence. Shared Foundation logging/telemetry/network/secret-reference mechanics may be consumed but never become A3 Authority.

---

# 8. A4 — Tool & Knowledge Consumption Internal Architecture

## A4-R01 — Tool / Knowledge Capability Reference & Governance Binding

Owns the Agent-side semantic binding of an A2 Harness Invocation/Action Proposal to a Tool/Knowledge capability reference under applicable governance context.

A4 may consume source capability/discovery evidence but does not own the referenced capability merely by binding it.

```text
Tool Reference != Tool Authority
Knowledge Reference != Knowledge SoT Transfer
Capability Visible != Capability Authorized automatically
```

The term “skill” may be consumed later only as an allowed Tool/capability extension representation under accepted semantics; this Candidate does not introduce a separate Product Capability or new Skill Authority.

## A4-R02 — Tool Binding, Compatibility & Applicability Qualification

Owns Agent-domain qualification that a referenced Tool/capability is compatible and applicable to the current Agent definition/runtime context.

Inputs may include:

```text
A1 tool/capability requirement/reference
A2 operation/context/action proposal
source capability/version evidence
Tenant/Principal/Policy/Trust evidence
Admission evidence where execution requires it
```

Permanent:

```text
Tool Compatible != Execution Admitted
Tool Selected != Effect Authorized
Tool Available != Node Ready automatically
```

## A4-R03 — Knowledge / RAG Source Binding & Factual-authority Preservation

Owns Agent-side Knowledge/RAG consumption binding and provenance without absorbing factual authority.

Required dimensions:

```text
Knowledge/source identity/reference
source revision/evidence reference
retrieval/query/context correlation where applicable
currentness/freshness
uncertainty/partiality
Tenant/authorization/privacy context
source attribution
```

Permanent:

```text
RAG Retrieval != Knowledge Authority
Knowledge Projection != Source SoT
Embedding/Index/Cache != SoT automatically
Agent Memory != Knowledge SoT
```

No vector DB/embedding/index/storage provider is selected.

## A4-R04 — Invocation Preparation & Agent-side Tool Intent Qualification

Owns A4 preparation of a representation-neutral Agent-side Tool/Capability Invocation Intent from an A2 Harness Action Proposal or runtime decision.

Preparation includes semantic qualification/correlation, not execution authority.

```text
Model Tool-call Suggestion
→ A2 Action Proposal
→ A4 Tool Invocation Intent qualification
→ applicable governed execution path
```

Permanent:

```text
Tool Invocation Intent != Formal Admission
Tool Invocation Intent != Dispatch
Tool Invocation Intent != Tool/Node Attempt
Tool Invocation Intent != Effect
```

If the target requires A6 cross-domain delegation/Automation participation, this Batch stops at an opaque future seam; A6 internals are not designed.

## A4-R05 — Invocation Correlation & External / Node Evidence Intake

Owns Agent-side correlation of a Tool/Knowledge invocation with evidence returned from applicable source owners.

For Node-executed capabilities A4 consumes, without reopening:

```text
RCP-04 Node Readiness evidence
RCP-07 Node Attempt evidence
RCP-08 Node Effect evidence
```

Permanent sequence distinction:

```text
Node Ready != Attempt Started
Node Attempt != Node Effect
Node Effect != Agent Semantic Success automatically
```

A4 may correlate opaque future `RCP-12 / AG-R04` delegation references but does not define AG-R04 source-side delegation semantics in Batch 1.

## A4-R06 — Result / Knowledge Contribution Qualification & Context Reintegration

Owns Agent-side qualification of Tool results and Knowledge contributions before supplying them as source-attributed contributions to A2 runtime context.

Required semantic output includes where applicable:

```text
Harness Invocation reference
external/tool/Node evidence reference
source owner/reference
result currentness/uncertainty
partial/failure/indeterminate qualification
sensitivity/redaction
context contribution provenance
```

A2 owns Context Projection and Agent interpretation.

Permanent:

```text
Tool Result != Business Semantic Success automatically
Tool Result != Agent Decision
Knowledge Contribution != Knowledge SoT
A4 Reintegration Contribution != A2 Context Projection
```

## A4-R07 — Retry / Re-entry / Uncertainty / Currentness & Non-destructive Lineage

Owns Agent-side invocation lineage/currentness qualification for repeated Tool/Knowledge interactions without introducing universal retry policy.

If a repeated invocation creates a new invocation responsibility instance:

```text
new Harness Invocation Identity
→ predecessor/retry/re-entry lineage
→ prior invocation evidence preserved
```

Permanent:

```text
Retry != prior invocation mutation
Latest result != canonical winner automatically
Repeated retrieval != source rewrite
```

No retry count/backoff/idempotency/exactly-once/at-most-once/at-least-once guarantee is selected.

## A4-R08 — Tool / Knowledge Consumption History, Privacy & Diagnostics

Owns A4 source-owned history/provenance/diagnostics for Tool/Knowledge consumption semantics.

Required properties:

```text
source attribution
Agent Operation / Harness Invocation correlation
compatibility/applicability evidence
external Attempt/Effect references where applicable
currentness/uncertainty
privacy/redaction
secret-reference separation
history compatibility
```

A4 contributes RCP-22 while preserving original source owners.

---

# 9. ns_evermore Harness / NSH Internal Architecture

## 9.1 Architecture identity

```text
NSH
→ named internal architecture concept
→ spans A2/A3/A4
→ consumes A1
→ does not create another authority partition
```

NSH is the coherent Agent-runtime architecture that turns model capability into Agent-runtime behavior under enterprise governance while preserving all accepted authority boundaries.

## 9.2 Current Batch-1 NSH topology

```text
A1 Canonical Agent Definition / Revision
        │
        │ Definition / requirement / compatibility semantics
        ▼
A2-R01..R13  NSH Runtime Core
        │
        ├── capability/profile evidence ───── A3-R01..R07
        │
        ├── tool/knowledge evidence ───────── A4-R01..R08
        │
        ├── recovery coordination reference ─ RT-R04 / RCP-20
        │
        ├── Human Task projection/routing ─── S11 / RCP-16
        │
        └── future seams only ─────────────── A5 / A6
```

## 9.3 NSH internal stable seams

No new RCP ID is created. The **Agent Harness Internal Stable Contract Pressure** is synthesized through these representation-neutral internal seams:

1. **Definition Runtime Binding Seam** — A1 → A2.
2. **Capability-profile Adaptation Seam** — A3 → A2.
3. **Model Mediation Seam** — A2 Harness Invocation ↔ A3 Provider Mediation Interaction.
4. **Tool/Knowledge Invocation & Reintegration Seam** — A2 ↔ A4.
5. **Continuation / Checkpoint Seam** — within A2, exposed through RCP-09/RCP-20 as applicable.
6. **Provenance / Diagnostics Seam** — A1/A2/A3/A4 source facts → RCP-22 consumers.
7. **Future Composition / Delegation Seam** — opaque A5/A6 extension points only.

These seams are semantic relationships, not modules/APIs/processes.

---

# 10. Identity and Lineage Model

The Batch establishes the following representation-neutral identity hierarchy:

```text
Agent Definition Identity
  └─ Agent Definition Revision

Agent Operation Identity
  ├─ Agent Runtime Attempt Identity [0..n]
  │    ├─ Context Projection Revision [0..n]
  │    ├─ Harness Invocation Identity [0..n]
  │    │    ├─ Provider Mediation Interaction reference [A3 when model/provider]
  │    │    └─ external/Node Tool Attempt/Effect references [owner-specific]
  │    ├─ Human Wait reference [0..n]
  │    └─ Checkpoint Evidence reference [0..n]
  └─ non-destructive history / continuation lineage
```

The diagram is cardinality pressure, not a physical data model.

Permanent distinctions:

```text
Definition Revision != Operation
Operation != Runtime Attempt
Runtime Attempt != Harness Invocation
Harness Invocation != Provider Mediation Interaction
Harness Invocation != Node Attempt
Node Attempt != Node Effect
Checkpoint != Operation SoT
Context Revision != Source Revision
```

No global identifier format is selected.

---

# 11. Context Engineering Architecture

## 11.1 Context is a derived Agent-runtime projection

The Agent runtime consumes source-attributed contributions and creates an operation-scoped Context Projection.

```text
Source Evidence / Definition / Human / Model / Tool / Knowledge Contribution
→ contribution reference + provenance
→ A2 Context Projection Revision
→ Harness Invocation applicability
```

A2 owns the Context Projection because it is an Agent-runtime derived fact. It does not own source facts represented inside the projection.

## 11.2 Selection, prioritization and compaction

Context selection/prioritization/compaction are allowed as **strategy-dependent runtime transformations**.

Architecture requirements:

```text
new transformation → new Context Projection revision where materially distinct
source attribution preserved
transformation provenance preserved
known material omission/partiality represented
uncertainty preserved
sensitivity/redaction preserved
historical prior projection not rewritten
```

No particular token strategy, summarizer, ranking model, window size or storage mechanism is chosen.

## 11.3 Memory-related semantics

Agent memory-related capability is represented at this level as retained/cross-session Agent-runtime context/history projections and references.

```text
Agent Memory Projection
→ may retain Agent-derived context/history semantics
→ must preserve source attribution
→ may be used in later Context Projection revisions
→ is not external factual SoT
```

No dedicated memory database, vector store, episodic/semantic memory algorithm or retention policy is selected.

---

# 12. Model-adaptive Harness Architecture

The Harness must adapt to model capability without allowing the model/provider to define Agent semantics.

Semantic flow:

```text
A1 Agent durable semantic requirements
+ A2 current Operation / Context
+ A3 Capability Profile / compatibility evidence
+ A4 applicable Tool/Knowledge evidence
+ governance/config evidence
→ A2 Harness Strategy Decision
→ Harness Invocation(s)
```

The strategy decision is operation-scoped runtime evidence and can evolve as provider capabilities evolve.

Permanent:

```text
Harness Strategy != Agent Definition
Capability Profile != Strategy
Strategy != Provider Authority
Strategy change != Definition revision automatically
```

A provider-specific limitation may cause `UNSUPPORTED`, `INCOMPATIBLE`, `UNKNOWN` or alternative compatible strategy qualification; it may not silently narrow canonical Product semantics.

---

# 13. Model Output, Agent Decision and Governed Action Boundary

The Candidate establishes the following non-collapse chain:

```text
Provider Mediation Interaction
→ Provider/Model Output Observation [A3]
→ Model Contribution qualification [A2]
→ Agent Decision [A2]
→ optional Harness Action Proposal [A2]
→ Tool Invocation Intent qualification [A4] OR future A6 seam
→ applicable Admission / Runtime Coordination / Executor path
→ Attempt
→ Effect
→ source/domain outcome
```

At no point does a model-native tool-call object automatically become an admitted real-world action.

Permanent:

```text
Model Output != Agent Decision
Agent Decision != Admission
Action Proposal != Admission
Tool Selection != Admission
Invocation != Attempt
Attempt != Effect
Effect != Business Semantic Success automatically
```

This is the principal enterprise-governance boundary for NSH.

---

# 14. Harness Loop vs Automation Workflow

The Agent Harness loop is an Agent-runtime mechanism for obtaining/interpreting contributions and deciding the next Agent-local activity.

Automation S6 owns governed reusable Automation / Workflow semantics.

The distinction is semantic, not syntactic:

```text
A Harness may internally branch/loop/wait
→ does not create an Automation Definition

A Harness may produce a proposal for Automation invocation/authoring
→ A6/S6 future governed path
→ does not create Workflow Authority
```

A future proposal to make Harness-local steps a reusable governed business workflow definition, a canonical DAG/flow definition or a second workflow SoT is outside this Batch and requires GAC/Owner reclassification.

---

# 15. Harness-local Continuation vs Runtime Scheduling

A2 may determine Agent-local continuation readiness and local next activity within the semantic Agent Operation.

It does not own:

```text
cross-component route selection
cross-component scheduling
cross-component dispatch
participant presence truth
universal retry scheduling
```

Those remain accepted `ns_runtime` responsibilities where applicable.

```text
A2 Local Continuation Decision
!= RT-R02 Schedule/Route/Dispatch
!= RT-R03 Cross-component Continuation Coordination
```

No queue, timer, scheduler or priority/fairness law is introduced.

---

# 16. HITL Architecture — RCP-16 Agent Source Side

RCP-16 Agent source-side semantics are closed at current Batch design level through A2-R10.

Stable Agent-side pressure includes:

```text
originating Agent Operation / Attempt
Agent Definition revision
Agent Human Wait identity/reference
wait semantic context reference
required Principal/authorization context where applicable
response correlation
response applicability qualification
stale/unknown/conflicting qualification
Agent-side applied/not-applied/indeterminate evidence
continuation reference
history/provenance
```

Ownership remains:

```text
A2 / AG-R01
→ source wait + response applicability + Agent-side application result

S11 / SV-R07
→ aggregation/projection/routing evidence

WB-R01
→ human response submission occurrence when later designed
```

Result:

```text
RCP-16 AG-R01 contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-16 Full Cross-component Closure
→ NOT CLAIMED
```

---

# 17. Trial Architecture — RCP-17 Agent Side

Agent trial semantics preserve:

```text
A1 trial intent / Agent revision
A2 trial Agent Operation / Attempt
A3 provider mediation observations
A4 tool/knowledge consumption evidence
applicable Node/external Attempt/Effect evidence
```

A2 owns Agent trial runtime meaning/outcome only; external effects remain source-owned.

Result:

```text
RCP-17 Agent contribution
→ CLOSED AT CURRENT DESIGN LEVEL

Full Trial Cross-component Closure
→ NOT CLAIMED
```

---

# 18. Desired / Applied Configuration — RCP-19 Agent Contribution

S9 remains the Managed Runtime Desired Configuration authority/SoT.

Agent boundaries own Applied facts only where the configuration item is actually applied inside their bounded runtime partition:

```text
A2 → Agent runtime / Harness applied configuration evidence
A3 → Provider-mediation applied configuration evidence where genuinely A3-owned
A4 → Agent tool/knowledge-consumption applied configuration evidence where genuinely A4-owned
```

A1 definition semantics are canonical Agent definition state and must not be collapsed into managed runtime Applied state.

Permanent:

```text
Desired != Distributed != Applied != Observed
Definition Revision != Applied Configuration
Configuration != Secret
```

Result:

```text
RCP-19 Agent Applied contribution
→ CLOSED AT CURRENT DESIGN LEVEL for A1-A4 scope
→ S9 Desired authority preserved
```

---

# 19. Recovery / Reconciliation — RCP-20 Agent Source-owner Contribution

Batch 1 explicitly closes the A2/AG-R01 source-owner contribution at current design level.

## 19.1 Source-owner facts eligible for re-observation

A2 may re-observe/re-qualify its own:

```text
Agent Operation existence/history
Agent Runtime Attempt lineage
Definition binding evidence
Context Projection revision/history
Human Wait / applicability facts
Harness Invocation lineage
Checkpoint Evidence
Agent trial/intervention facts
Agent outcome/currentness/uncertainty facts
```

A2 may correlate A3/A4/Node/external evidence references but does not re-own those source facts.

## 19.2 Coordination boundary

```text
RT-R04
→ recovery/evidence-exchange/re-observation/reconciliation coordination-stage facts

A2 / AG-R01
→ Agent-runtime source facts
```

Permanent:

```text
R4 Evidence Exchange != Agent Source Fact Transfer
Re-observation Requested != Re-observed Agent Fact
Checkpoint Received != Checkpoint Canonical
Conflict Detected != Conflict Resolved
Reconciliation Stage Complete != Agent Operation Resumed automatically
Recovery Participation Complete != Source Recovery Outcome
```

## 19.3 Conflict and ordering

This Candidate defines no:

```text
latest-wins
earliest-wins
local-wins
central-wins
provider-wins
source-priority winner
majority-wins
cross-source merge law
authoritative synchronization direction
```

Result:

```text
RCP-20 Agent / AG-R01 source-owner contribution
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-20 Full Cross-component Closure
→ NOT CLAIMED
```

---

# 20. Diagnostics / Provenance — RCP-22 Agent Contribution

Agent-side RCP-22 is federated by original fact ownership:

```text
A1 → definition/revision/validation/provenance facts
A2 → operation/context/HITL/checkpoint/recovery/outcome facts
A3 → provider capability/mediation facts
A4 → tool/knowledge consumption/correlation facts
```

NSH may correlate these facts for explainability/diagnostics but the correlation does not create a new Diagnostic SoT.

Required diagnostic qualities:

```text
source owner
identity/revision references
operation/invocation lineage
currentness/freshness
uncertainty/partiality/conflict
privacy/redaction
secret-reference separation
compatibility/conformance version
history preservation
```

Permanent:

```text
Diagnostic Aggregation != Canonicalization
Observability != Authority Transfer
Provider-private hidden reasoning != required diagnostic payload
```

Result:

```text
RCP-22 A1/A2/A3/A4 contribution
→ COMPLETE AT CURRENT BATCH DESIGN LEVEL

RCP-22 Full Cross-component Closure
→ NOT CLAIMED
```

---

# 21. Human / SDK Intent — RCP-24 Receiving Expectation

A2 may receive/interprete governed intervention/continuation intent targeted at an Agent Operation and owns only Agent-side receipt/applicability/outcome facts.

```text
Intent Submitted != Intent Applicable
Intent Applicable != Outcome Achieved
```

WB/SDK source-side interaction semantics are downstream and not designed here.

Result:

```text
RCP-24 Agent receiving expectation
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-24 Full Closure
→ NOT CLAIMED
```

---

# 22. Node Contract Consumption — RCP-04 / RCP-07 / RCP-08

A4 consumes accepted Node source semantics only.

```text
RCP-04 ND-R01 Node Readiness
→ input/reference only

RCP-07 ND-R02 Node Attempt
→ correlation/evidence consumption only

RCP-08 ND-R03 Node Effect
→ correlation/evidence consumption only
```

No Node internals are reopened.

Permanent:

```text
Ready != Admitted
Dispatch != Node Attempt
Node Attempt != Node Effect
Node Effect != Agent Outcome automatically
```

---

# 23. RCP-12 Bounded Future-delegation Correlation Seam

Current Batch may preserve only the target/result correlation expectation required by A4 to consume future delegation evidence.

```text
AG-R04 source-side delegation identity/semantics
→ A6 / Batch 2
→ NOT DESIGNED
```

A4 may carry an opaque delegation/correlation reference where an execution result was produced through a future A6 path.

Result:

```text
RCP-12 Batch-1 contribution
→ BOUNDED CONSUMER/CORRELATION EXPECTATION ONLY

RCP-12 owner/source-side closure
→ NOT CLAIMED
```

---

# 24. A5 / A6 Non-preemption

Batch 1 preserves future extension seams but does not decide:

```text
Multi-Agent supervisor/team/graph topology
Agent-to-Agent handoff protocol
Agent shared-memory/context-sharing semantics
Multi-Agent parallelism
Agent delegation routing semantics
Automation invocation parameter-binding semantics
candidate Automation authoring interface
Agent→Node physical delegation path
```

Future A5/A6 design must consume Batch-1 Agent Definition/Operation/Invocation/Context/Provider/Tool semantics rather than reopen them unless GAC formally revalidates.

---

# 25. Failure / Unknown / Temporal Semantics

The Batch uses explicit uncertainty instead of fabricated success or winner rules.

Applicable semantic qualifications include, without imposing one universal linear state machine:

```text
UNKNOWN
UNAVAILABLE
UNREACHABLE
UNSUPPORTED
INCOMPATIBLE
STALE
PARTIAL
INDETERMINATE
CONFLICTING
WAITING / PENDING where semantically applicable
RECOVERY / RECONCILIATION pending qualification where applicable
```

These are orthogonal qualifications on source-owned facts, not a universal Agent lifecycle state machine.

Time evidence supports temporal interpretation but not conflict winner selection.

```text
Clock != Conflict Winner
Latest Timestamp != Canonical Winner
```

---

# 26. Tenant / Principal / Policy / Trust / Privacy

All A1-A4 semantics consume and preserve applicable governance context.

Requirements:

```text
Tenant context preserved across Definition/Operation/Invocation/Checkpoint lineage
Principal context preserved where user/HITL/tool access is principal-sensitive
Policy/Trust evidence consumed, never recreated by NSH
Context construction excludes unauthorized contributions
Sensitive Tool/Knowledge/Multimodal content carries privacy/redaction qualification
Secret material is not copied into ordinary Context/Checkpoint/Diagnostics
```

Permanent:

```text
Context Availability != Authorization
Model Capability != Trust
Tool Visibility != Permission
Human Response != Policy Permit
```

---

# 27. Private / Offline Correctness

The Agent architecture must remain correct in private deployment without mandatory public SaaS/model/provider dependency.

Permitted degraded conditions include:

```text
public provider unavailable
private provider available
provider capability unknown/stale
Tool/Knowledge source unavailable
central projection unavailable
cross-component coordination temporarily unavailable
```

The system must preserve source facts, provenance, uncertainty and applicable governance semantics under these conditions.

No universal offline fail-open/fail-closed law is selected.

```text
Offline != Authority Transfer
Provider Unavailable != Agent Definition Invalid automatically
Central Projection Stale != Agent Source Fact Nonexistent
Checkpoint Locality != Canonical Authority
```

---

# 28. Shared Foundation Consumption

Batch 1 consumes the accepted Shared Foundation architecture instead of creating Agent-local duplicates.

Applicable capabilities include:

```text
Bootstrap Configuration Loading
Structured Diagnostics & Logging
Technical Telemetry & Health Observation
Temporal & Freshness Primitives
Operation / Correlation / Provenance Context
Language-neutral Representation & Serialization Mechanics
Network Client Mechanics
Cache Client Mechanics
Storage Client Mechanics
Error / Status / Uncertainty Primitives
Governed Context Propagation
Secret Reference / Sensitive-data Redaction
Compatibility & Conformance Mechanics
```

Permanent:

```text
Foundation Mechanics != Agent Authority
Correlation Context != Agent Operation Owner
Cache != Context/Knowledge SoT
Storage Client != Memory SoT
Serializer != Agent Contract Authority
Network Client != Provider/Tool Authority
Compatibility Helper != Agent Compatibility Authority
```

Mandatory Missing Shared Foundation Semantic: `NONE_FOUND`.

No parallel `ns_agent` Foundation is created.

---

# 29. Internal Dependency Taxonomy

This Candidate uses:

```text
SDD — SEMANTIC_DEFINITION_DEPENDENCY
ACD — APPLICATION_CONTEXT_DEPENDENCY
EL  — EVIDENCE_LINKAGE
HPL — HISTORICAL_PROVENANCE_LINKAGE
XED — EXTERNAL_EVIDENCE_DEPENDENCY
```

Only SDD participates in hard semantic-definition cycle analysis.

## 29.1 Hard SDD graph

Key SDD edges:

```text
A1-R01 → A1-R02
A1-R01 → A1-R03
A1-R01 → A1-R04
A1-R02 → A1-R05
A1-R03 → A1-R05
A1-R04 → A1-R05
A1-R05 → A1-R06
A1-R01..R06 → A1-R07

A1-R01/R02/R03 → A2-R02
A2-R01 → A2-R03
A2-R01/R03 → A2-R04
A2-R01/R03 → A2-R05
A2-R05 → A2-R06
A2-R01/R03/R06 → A2-R07
A2-R01/R03/R06 → A2-R08
A2-R08 → A2-R09
A2-R01/R03 → A2-R10
A2-R01/R03/R06/R08 → A2-R11
A1-R06 + A2-R01/R03 → A2-R12
A2-R01..R12 → A2-R13

A2-R08 → A3-R01
A3-R01 → A3-R02
A1-R03 + A3-R02 → A3-R03
A2-R08 + A3-R01 → A3-R04
A3-R04 → A3-R05
A3-R02/R03/R05 → A3-R06
A3-R01..R06 → A3-R07

A2-R08 + A1-R03 → A4-R01
A4-R01 + A1-R03 → A4-R02
A4-R01 → A4-R03
A2-R09 + A4-R01/R02 → A4-R04
A4-R04 → A4-R05
A4-R03/R05 → A4-R06
A4-R04/R05/R06 → A4-R07
A4-R01..R07 → A4-R08
```

Feedback from A3/A4 runtime evidence to A2 strategy/context is classified as `ACD / EL`, not reverse SDD:

```text
A3 capability evidence → A2 Harness Strategy
A3 provider output evidence → A2 Model Contribution
A4 result/knowledge contribution → A2 Context Projection
```

These feedback links apply already-defined semantics; they do not define A2 identity semantics.

Result:

```text
Hard Internal SDD Graph
→ ACYCLIC

Unresolved Semantic-definition Cycle
→ 0

Authority Cycle
→ NONE

Circular Actual-state Ownership
→ NONE
```

---

# 30. RCP Closure Summary

```text
RCP-09 / AG-R01 Agent Runtime owner/source-side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-10 / AG-R02 Provider Mediation bounded-observation owner-side
→ CLOSED AT CURRENT DESIGN LEVEL

RCP-16 / AG-R01 Agent Human Task source wait/applicability side
→ CLOSED AT CURRENT DESIGN LEVEL
→ Full Cross-component Closure NOT CLAIMED

RCP-17 / Agent Trial contribution
→ CLOSED AT CURRENT DESIGN LEVEL
→ Full Cross-component Closure NOT CLAIMED

RCP-19 / Agent Applied configuration contribution
→ CLOSED AT CURRENT DESIGN LEVEL
→ S9 Desired authority preserved

RCP-20 / AG-R01 Agent source-owner recovery/reconciliation participation
→ CLOSED AT CURRENT DESIGN LEVEL
→ Full Cross-component Closure NOT CLAIMED

RCP-22 / A1-A4 Agent fact-owner diagnostics/provenance contribution
→ COMPLETE AT CURRENT BATCH DESIGN LEVEL
→ Full Cross-component Closure NOT CLAIMED

RCP-24 / Agent receiving/applicability expectation
→ CLOSED AT CURRENT DESIGN LEVEL
→ Full Closure NOT CLAIMED

RCP-04 / RCP-07 / RCP-08
→ accepted Node source semantics consumed only / NOT reopened

RCP-12
→ bounded correlation/consumer expectation only
→ AG-R04 owner/source side remains future A6

RCP-11
→ NOT DESIGNED / future A5
```

No new RCP is created. RCP count remains `24`.

---

# 31. DAD / MDE Classification Outcome

This Candidate requires DAD evidence for material design-semantic choices such as:

```text
A1-A4 responsibility decomposition
NSH named internal topology without new boundary
Durable Agent semantics vs adaptive Harness strategy
Operation / Runtime Attempt / Invocation identity separation
Context Contribution vs Context Projection vs source SoT
context revision/compaction provenance law
Provider capability observation vs Agent Authority
Provider mediation interaction vs Agent outcome
Tool/Knowledge consumption vs source/effect authority
Model Output → Agent Decision → Action Proposal separation
Harness Loop vs Automation Workflow
Harness-local continuation vs Runtime Scheduler
HITL submission/applicability separation
Checkpoint evidence vs canonical Product state
Agent-side RCP-20 recovery ownership
Trial / production separation
Desired / Applied / Definition separation
federated diagnostics/provenance
private/offline provider independence
hard SDD acyclic topology
A5/A6 non-preemption
```

No Owner-reserved MDE was discovered.

```text
New MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Misclassified MDE known at Candidate stage
→ 0
```

If later design materially requires a universal scheduling/fairness law, retry/cancel/rollback/compensation/once guarantee, fail-open/fail-closed law, conflict winner/merge law, authoritative synchronization direction, major identity namespace, new Product capability, new Trust/Authority/SoT partition, mandatory public SaaS/broker/workflow/recovery dependency, or provider/framework/protocol/storage lock-in, this producing session must stop and return to GAC/Owner authority.

---

# 32. Explicit Implementation Deferrals

Not selected or designed:

```text
LangGraph
DeepSeek Harness
OpenAI Agents SDK
other Agent framework/runtime library
provider SDK
model-routing algorithm
fallback algorithm
context-selection algorithm
context-compaction algorithm
memory algorithm / memory store
checkpoint storage
recovery/replay engine
vector database / embedding provider
queue / broker / scheduler / workflow engine
Redis / RabbitMQ / Kafka / NATS
Celery / Temporal / Airflow / Quartz / APScheduler
database / event store / storage engine
REST / gRPC / concrete WebSocket protocol/frame/envelope
DTO / JSON schema / wire schema
table / ORM / physical persistence schema
process / service / worker / thread / coroutine topology
container / pod / host / deployment topology
UUID / physical key format
exactly-once / at-most-once / at-least-once
universal retry / cancellation / rollback / compensation policy
```

`Evidence retention`, `Context Projection`, `Checkpoint Evidence`, `Agent Operation`, `Runtime Attempt`, `Harness Invocation` and `Provider Mediation Interaction` are architecture semantics only and do not imply one persistence/process implementation.

---

# 33. Candidate Completion Result

```text
Authorized Boundary Coverage in Candidate
→ A1 / A2 / A3 / A4 = 4 / 4 / 100%

Internal Responsibility Count
→ 35

NSH Internal Architecture Pressure
→ SYNTHESIZED

Agent Harness Internal Stable Contract Pressure
→ SYNTHESIZED

Hard Internal SDD Graph
→ ACYCLIC

Authority / SoT / Final Actual-state Transfer
→ 0

New Product Capability
→ 0

New Internal Boundary
→ 0

New Runtime Role
→ 0

New RCP
→ 0

New MDE
→ 0

Missing Mandatory Shared Foundation Semantic
→ NONE_FOUND

Implementation Leakage
→ 0

A5/A6 Internal-design Preemption
→ 0

Candidate Status
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This Candidate is not self-accepted. It requires DAD evidence, independent Review/Audit evidence and bounded-session Handoff evidence before returning to the Global Architecture Coordinator.