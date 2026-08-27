# NGRP-001 — Component Internal Design / ns_agent / Batch 2 — Candidate

- Session Type: `BOUNDED PRODUCING SESSION`
- Scope: `COMPONENT_INTERNAL_DESIGN_ONLY / NS_AGENT / BATCH_2 / HARNESS_NATIVE_MULTI_AGENT_COMPOSITION_GOVERNED_CROSS_DOMAIN_DELEGATION_AUTOMATION_PARTICIPATION_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- Authorized Boundaries: `A5 / A6`
- Inherited Runtime Roles: `AG-R03 / AG-R04`
- Producing Entry HEAD: `3623f90e3a1ea01f23c6ebf9fbd6d8e33a57e3b3`
- Entry Global State: `GAC-EPOCH-0092`
- Entry Decision Registry: `0.0.33 / CURRENT / NORMATIVE`
- Runtime / Domain Stable Contract Pressure Count: `24 / unchanged`
- Candidate Status: `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`

---

# 1. Authority, Fresh Recovery and Authorization Gate

This document is producing evidence only. It is not Global Architecture State, is not a GAC transition, and carries no Global Acceptance authority.

Fresh Repository recovery at producing entry established:

```text
Actual Branch HEAD
→ 3623f90e3a1ea01f23c6ebf9fbd6d8e33a57e3b3

HEAD Commit
→ seal ns_agent batch 2 authorization at GAC-EPOCH-0092

Current Global Architecture State
→ GAC-EPOCH-0092

State Verified Through HEAD
→ 60bd4b388eb7c824862bc636e73af55ce06dff6f

State-to-Producing-entry Delta
→ exactly one commit
→ Global Architecture State authorization seal only
→ EXPECTED_GOVERNANCE

Current Authorized Phase
→ NGRP-001 — Component Internal Design / ns_agent / Batch 2

Current Authorization Scope
→ COMPONENT_INTERNAL_DESIGN_ONLY
  / NS_AGENT
  / BATCH_2
  / HARNESS_NATIVE_MULTI_AGENT_COMPOSITION_GOVERNED_CROSS_DOMAIN_DELEGATION_AUTOMATION_PARTICIPATION_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS

Authorized Boundaries
→ A5 — Native Multi-Agent Composition
→ A6 — Governed Cross-domain Delegation & Automation Participation

Inherited Runtime Roles
→ AG-R03 — Native Multi-Agent Composition Coordinator
→ AG-R04 — Cross-domain Delegation & Automation Participant

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Semantic Gap
→ NONE

Unexpected Drift
→ NONE

Authorization Gate
→ PASS
```

The producing session therefore proceeds only inside A5/A6. No Global Architecture governance file is mutated by this Candidate.

---

# 2. Normative Upstream Consumed

The design consumes, rather than redefines, the current Repository authority, including at least:

```text
docs/ns_evermore_genesis_constitution_0.0.1.md
docs/governance/ns_evermore_governance_0.0.2.md
docs/ns_evermore_project_architecture_0.0.3.md

docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_five_component_internal_architecture_boundaries_candidate_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_candidate_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_shared_foundation_architecture_batch_1_global_acceptance_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_foundation_contract_design_batch_1_global_acceptance_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_foundation_module_design_batch_1_global_acceptance_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_foundation_provider_design_batch_1_global_acceptance_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_foundation_provider_exhaustion_component_internal_design_readiness_assessment_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_remaining_pressure_batching_assessment_0.0.8.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_1_global_acceptance_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_2_global_acceptance_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_ns_runtime_component_internal_design_global_closure_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_runtime_internal_design_batch_2_global_acceptance_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_runtime_internal_design_batch_3_global_acceptance_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_ns_node_component_internal_design_global_closure_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_node_internal_design_batch_1_global_acceptance_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_ns_harness_architecture_insertion_impact_authority_sequencing_assessment_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_batch_1_nsh_targeted_authorization_revalidation_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_internal_design_batch_1_candidate_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_internal_design_batch_1_dad_evidence_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_internal_design_batch_1_review_audit_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_internal_design_batch_1_handoff_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_internal_design_batch_1_global_acceptance_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_internal_design_remaining_pressure_batching_assessment_0.0.1.md
docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_batch_2_authorization_0.0.1.md

docs/governance/decisions/ns_evermore_z3_batch_1_multi_agent_composition_owner_capability_decision_0.0.1.md
docs/governance/decisions/ns_evermore_z3_batch_1_agent_dynamic_automation_authoring_owner_capability_decision_0.0.1.md
docs/governance/decisions/ns_evermore_decision_registry_0.0.33.md

docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md
docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md
docs/governance/global_architecture/ns_evermore_global_architecture_ledger_continuation_0.0.4.md
```

Normative conclusions inherited from these artifacts are not reopened by convenience.

---

# 3. Scope and Explicit Non-goals

## 3.1 In scope

```text
A5 / AG-R03
→ Native Multi-Agent composition coordination
→ Agent reference/revision binding in composition context
→ participant relationship and correlation semantics
→ composition provenance
→ partiality/failure/unknown visibility
→ history/recovery/diagnostics contribution
→ RCP-11 stable-contract synthesis
→ A2 participant-integration refinement without reopening A2

A6 / AG-R04
→ Agent-side governed cross-domain delegation participation
→ Agent→Node delegation participation
→ existing Automation invocation participation
→ Agent-authored candidate Automation participation
→ target/result/effect correlation
→ history/recovery/diagnostics contribution
→ RCP-12 stable-contract synthesis
```

## 3.2 Out of scope

This Candidate does not design or select:

```text
A1-A4 redesign
A7 / AG-R05
new Harness authority / SoT / actual-state owner
new Product Component
new Workflow / Automation authority
new Scheduler / Runtime authority
new retry / cancellation / rollback / compensation / once guarantee
universal Multi-Agent supervisor/team/graph topology
universal shared-memory authority
universal parallelism / fairness / scheduling law
major recursive/cyclic Multi-Agent Product semantics
concrete Agent framework or Multi-Agent framework
concrete protocol / DTO / schema / API / wire envelope
concrete database / event store / cache / checkpoint store
concrete process / worker / thread / coroutine / container topology
physical identifier format
implementation planning / IWP / coding
```

No existing accepted Project Architecture, Runtime, Foundation, server, runtime, node or Batch-1 Agent design is modified here.

---

# 4. Permanent Upstream Non-collapse

The following remain normative throughout Batch 2:

```text
Agent Definition Revision
!= Agent Operation

Agent Operation
!= Agent Runtime Attempt

Agent Runtime Attempt
!= Harness Invocation

Harness Invocation
!= Provider Mediation Interaction

Harness Invocation
!= Node Attempt

Node Attempt
!= Node Effect

Model Output
!= Agent Decision

Agent Decision
!= Execution Admission

Harness Action Proposal
!= Execution Admission

Tool Selection
!= Execution Admission

Invocation
!= Attempt

Attempt
!= Effect

Effect
!= Business Semantic Success automatically
```

Batch-2-specific permanent non-collapse:

```text
Multi-Agent Composition
!= Separate Multi-Agent Authority

Composition Coordination
!= merged participant Actual-state

Composition Operation
!= any participant Agent Operation

Composition Participant Correlation
!= participant Agent Runtime Attempt

Agent A invokes Agent B
!= Authority Transfer

Composition Relationship
!= universal hierarchy

Composition Projection
!= participant runtime SoT

Composition Context Contribution
!= shared factual SoT

Native Multi-Agent Composition
!= Automation Workflow Semantics

Agent-to-Agent delegation
!= Runtime Dispatch Authority

Agent cross-domain delegation
!= Node Attempt

Agent cross-domain delegation
!= Node Effect Ownership

Agent invokes Automation
!= Automation Authority

Agent authors candidate Automation
!= Accepted Automation

Candidate possession
!= Artifact Acceptance

Agent Intent
!= Execution Admission

Runtime Dispatch
!= Execution Admission
```

---

# 5. Batch-2 Internal Architecture Overview

The accepted NSH concept is extended, not redefined:

```text
A1 Agent Definition / canonical revision semantics
        │
        ├──────── normative definition/reference semantics ─────────────┐
        │                                                              │
A2 Agent Operation / Attempt / Context / Agent Decision                │
        │                                                              │
        ├──────── accepted NSH core ────────────────────────────────────┤
        │                                                              │
        ├──────── A5 extension → AG-R03 composition coordination       │
        │                    → RCP-11                                  │
        │                                                              │
        └──────── A6 extension → AG-R04 cross-domain participation     │
                             → RCP-12                                  │
                                                                       │
A3 Provider/model mediation → bounded adaptation evidence ─────────────┤
A4 Tool/Knowledge consumption → accepted invocation/evidence seams ────┘
```

NSH remains an internal cohesion concept. Facts produced through the A5 extension are A5/AG-R03 facts only when they genuinely originate as composition-coordination/provenance facts. Facts produced through the A6 extension are A6/AG-R04 facts only when they genuinely originate as Agent-side cross-domain participation/provenance facts.

No “Harness state” becomes a universal owner category.

---

# 6. A5 — Native Multi-Agent Composition Internal Architecture

A5 is decomposed into nine architecture-semantic responsibilities.

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

The labels are document-local architecture navigation constructs. They do not imply packages, classes, services, workers, tables or processes.

## 6.1 A5-R01 — Composition Operation Identity & Definition-context Binding

A **Multi-Agent Composition Operation** is an A5 coordination subject representing one bounded occurrence of coordinating multiple Agent participants under accepted Agent semantics.

Permanent identity distinctions:

```text
Agent Definition Revision
!= Multi-Agent Composition Operation
!= Participant Agent Operation
!= Participant Agent Runtime Attempt
!= Harness Invocation
!= Provider Mediation Interaction
!= Cross-domain Delegation
!= Node Attempt / Effect
```

A Composition Operation binds, by reference and historical provenance, to:

```text
applicable initiating Agent Operation
applicable initiating Agent Definition Revision
applicable A1 composition semantics / references
applicable Tenant / Organization / Principal context
applicable Policy / Trust / governance evidence references
applicable NSH strategy/context lineage
```

The Composition Operation identity is representation-neutral and A5-bounded. No universal UUID/key namespace is created.

A new coordination occurrence is not allowed to rewrite an earlier Composition Operation. Retry/re-entry/recomposition, when it creates a new bounded coordination occurrence, is represented by new lineage rather than historical mutation.

## 6.2 A5-R02 — Participant Reference, Effective Revision & Compatibility Binding

A5 consumes A1 Agent-reference and revision semantics. It does not create a second Agent-definition registry.

For each participant correlation A5 must preserve:

```text
Participant Agent Reference
→ semantic Agent identity/reference governed by A1

Effective Participant Revision
→ the revision actually bound for the historical participation occurrence

Compatibility / Conformance Qualification
→ applicable, incompatible, unsupported, stale, unknown or indeterminate as evidenced
```

The stable rule is:

```text
Current/latest Agent revision
!= historical effective participant revision automatically
```

A5 does not define a universal version selector, latest-binding rule or version-range syntax. It requires the effective historical revision to remain identifiable once participation is established.

Silent rebinding that changes historical interpretation is prohibited.

## 6.3 A5-R03 — Operation-scoped Participation Membership & Relationship Correlation

A5 records **operation-scoped participant correlation**, not a universal persistent team authority.

Participation facts may express contextual relationships such as caller, callee or peer where the accepted Agent semantics require them, but:

```text
Caller != superior Authority automatically
Callee != subordinate Authority automatically
Peer != shared SoT
Participant set != universal Agent team
Relationship != global hierarchy
Membership != merged Actual-state ownership
```

A5 may preserve the participant set and relationship evidence actually relevant to a Composition Operation. It does not prescribe universal supervisor, swarm, team, graph or actor topology.

Dynamic participation, when permitted by applicable A1 semantics, is historical correlation within the Composition Operation; it is not a new universal membership policy.

## 6.4 A5-R04 — Agent-to-Agent Invocation / Delegation Coordination

A5 coordinates Agent-domain invocation/delegation relationships produced under accepted Agent semantics and NSH operation flow.

Representative semantic flow:

```text
A2 Agent Decision / applicable A1 composition semantics
→ A5 coordination intent/correlation
→ participant Agent reference/revision qualification
→ participant A2 Agent Operation origination where actually established
→ participant A2 Runtime Attempt / NSH Invocation as applicable
→ participant source evidence
→ A5 correlation
→ originating A2 continuation
```

Permanent:

```text
Harness proposal to involve another Agent
!= Agent Decision

Agent Decision to involve another Agent
!= participant Agent Operation automatically

A5 coordination
!= participant Agent runtime state

Agent-to-Agent delegation
!= authority transfer

A5 coordination
!= RT-R02 scheduling/routing/dispatch
```

A5 neither schedules arbitrary cross-component work nor becomes a global execution planner.

## 6.5 A5-R05 — Composition Context-contribution & Source-attribution Coordination

A5 may coordinate composition-scoped context contributions between Agent participants only through provenance-preserving A2 context semantics.

A **Composition Context Contribution** is evidence that some context material was offered, referenced or transferred for composition participation. It carries source identity, source revision/currentness where applicable, producer participant correlation and transformation/projection lineage.

Permanent:

```text
Composition Context Contribution
!= participant A2 context Actual-state

Shared visibility
!= shared factual Authority

Copied context
!= copied SoT

Summarized context
!= source fact replacement

Composition context projection
!= universal shared memory
```

Each participant A2 remains responsible for its own runtime context projection, selection, transformation and currentness. External factual authority remains with the original source owner.

No global shared-memory authority or shared-memory algorithm is created.

## 6.6 A5-R06 — Participant Runtime-evidence Correlation & Actual-state Preservation

A5 correlates participant evidence without absorbing it.

For each participant, source facts remain owned by the accepted source partition:

```text
participant Agent Operation / Runtime Attempt / Context / Agent Decision
→ A2 / AG-R01 of that participant

provider mediation observation
→ A3 / AG-R02

Node Attempt / Effect
→ N2 / N3

Automation semantic runtime state
→ S6 / SV-R02

runtime dispatch / continuation coordination
→ R2 / R3
```

A5 owns only composition-specific correlation/provenance facts such as:

```text
participant reference bound to composition
participant engagement correlated
participant evidence reference received
participant relationship recorded
composition-level waiting/partiality/currentness qualification
```

A Composition projection must not become a participant runtime SoT.

## 6.7 A5-R07 — Composition Outcome, Partiality & Uncertainty Qualification

A5 may qualify composition-level coordination outcome only from A1 semantics plus source-owned participant evidence.

No universal “all participants must succeed”, “first result wins”, “majority wins”, “supervisor result wins” or “latest result wins” law is introduced.

Applicable architecture-level qualifications may include:

```text
PENDING
ACTIVE
WAITING
PARTIAL
COMPLETED
FAILED
UNKNOWN
STALE
UNAVAILABLE
INCOMPATIBLE
INDETERMINATE
CONFLICTING
SUPERSEDED
```

These are semantic qualifications, not a mandatory linear state machine.

Permanent:

```text
One participant succeeded
!= composition success automatically

One participant failed
!= composition failure automatically

All known participants responded
!= semantic success automatically

Composition coordination completed
!= all participant facts unified

UNKNOWN
!= FAILED

UNAVAILABLE
!= DENIED

CONFLICTING
!= winner selected
```

Whether a particular composition result satisfies Agent semantics is evaluated against the applicable A1 definition/revision, not a universal Batch-2 winner rule.

## 6.8 A5-R08 — Composition Recovery / Reconciliation Participation

A5 participates in RCP-20 only for facts genuinely owned by A5.

On disconnect, restart, partial evidence loss or re-observation:

```text
A5 retains/reconstructs its own Composition Operation and correlation provenance as available
→ RT-R04 coordinates cross-component recovery/reconciliation where required
→ each participant/source owner re-observes/reasserts its own facts
→ A5 re-correlates source evidence
→ uncertainty/conflict remains explicit
```

Permanent:

```text
A5 recovery participation
!= source recovery authority

A5 retained correlation
!= participant runtime SoT

Reconnect
!= reconciled

Re-observation
!= participant state rewrite

Latest timestamp / arrival
!= canonical winner

Recovery
!= authority transfer
```

No replay guarantee, retry engine, merge law, authoritative synchronization direction or fail-open/fail-closed Product policy is created.

## 6.9 A5-R09 — Composition History, Provenance, Diagnostics & RCP-11 Governance

A5 maintains non-destructive composition provenance for its own facts, including applicable:

```text
Composition Operation lineage
initiating Agent Operation reference
participant Agent/revision references
participant relationship/correlation lineage
A5 coordination occurrences
source evidence references and currentness
context-contribution provenance
partial/failure/unknown history
recovery/reconciliation participation history
compatibility/conformance qualification
```

Diagnostics expose A5 facts with applicable redaction and uncertainty. Diagnostic aggregation does not canonicalize participant source facts.

RCP-11 contract governance is owned here at the A5/AG-R03 source/coordination side, while A2/AG-R01 preserves participant integration semantics.

---

# 7. A6 — Governed Cross-domain Delegation & Automation Participation Internal Architecture

A6 is decomposed into ten architecture-semantic responsibilities.

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

## 7.1 A6-R01 — Cross-domain Intent / Participation Identity & Agent-context Binding

A6 receives an applicable Agent Decision / governed Agent-side intent from A2 and creates a bounded A6 participation/correlation subject.

Permanent identity distinctions:

```text
Agent Operation
!= Agent Decision
!= Cross-domain Delegation / Invocation Participation
!= Admission Decision / Evidence
!= Runtime Dispatch
!= Node Attempt
!= Node Effect
!= Automation Operation
!= Automation Candidate / Canonical Definition
```

A6 binds its participation fact to applicable:

```text
Agent Operation
Agent Definition Revision
Agent Decision / action-proposal lineage
Tenant / Organization / Principal
Policy / Trust / governance evidence references
originating NSH invocation/context lineage
```

Model output or Harness action proposal cannot directly originate authoritative cross-domain execution.

## 7.2 A6-R02 — Governed Target Reference, Revision/Capability & Applicability Qualification

A6 preserves the target actually selected by the Agent-side decision process without defining a universal target-selection algorithm.

Target categories in the accepted boundary are:

```text
Node / Node capability target
existing Automation target
S6 Automation candidate intake target
```

A6 records only representation-neutral target reference and applicable effective revision/capability/compatibility evidence.

Permanent:

```text
Target reference
!= target Authority

Target discoverable
!= target authorized

Target reachable
!= target ready

Target compatible
!= execution admitted

Current target revision
!= historical target revision automatically
```

Target identity and semantic authority remain with the target domain.

## 7.3 A6-R03 — Governance / Admission / Runtime Handoff Correlation

A6 propagates/references applicable governance context and correlates downstream Admission/runtime evidence; it does not issue those decisions.

```text
Agent-side governed intent
→ A6 participation/provenance
→ S8 Formal Execution Admission where applicable
→ R1/N1 evidence as applicable
→ R2 scheduling/routing/dispatch
→ actual target/runtime owner
```

Permanent:

```text
Agent Intent
!= Admission

Admission
!= Scheduling / Routing / Dispatch

Dispatch
!= Attempt

Admission Evidence Possession
!= Admission Authority

Policy Permit
!= Admission

Reachability / Readiness evidence
!= Admission substitute
```

If Admission applicability cannot be established, A6 preserves `UNKNOWN / STALE / INDETERMINATE / NOT_APPLICABLE` as supported by source evidence; it does not infer authorization from absence of evidence.

## 7.4 A6-R04 — Agent→Node Delegation Participation

The stable Agent→Node journey is:

```text
A2 Agent Decision / governed intent
→ A6 Agent-side delegation participation + target correlation
→ S8 / SV-R04 Admission
→ R1 / RT-R01 presence + N1 / ND-R01 readiness evidence where applicable
→ R2 / RT-R02 schedule / route / dispatch
→ N2 / ND-R02 Attempt
→ N3 / ND-R03 Effect / Node-origin source fact where applicable
→ R3 / RT-R03 continuation/delegation coordination where applicable
→ A6 target/result/effect correlation
→ A2 result qualification / continuation
```

A6 never claims Node Attempt or Effect ownership.

```text
Delegation emitted
!= dispatched

Dispatched
!= attempt started

Attempt completed
!= protected effect occurred automatically

Protected effect occurred
!= Agent semantic success automatically
```

## 7.5 A6-R05 — Existing Automation Selection / Invocation Participation

The stable existing-Automation journey is:

```text
A2 Agent Decision
→ A6 existing-Automation invocation participation
→ S6 canonical Automation semantics / effective revision
→ S8 Artifact Acceptance / Admission where applicable
→ S6 / SV-R02 Automation Operation / semantic continuation
→ R2/R3 + applicable executor
→ source-owned attempt/effect evidence
→ S6 Automation semantic result
→ A6 result correlation
→ A2 Agent continuation
```

Permanent:

```text
Agent selected Automation
!= Automation Authority

Automation invocation intent
!= Automation Operation automatically

Automation Operation
!= Node Attempt

Automation semantic result
!= Node Effect

A6 invocation provenance
!= S6 semantic runtime SoT
```

A6 does not redefine RCP-13 or RCP-15.

## 7.6 A6-R06 — Candidate Automation Authoring Contribution & S6 Intake Correlation

Agent-authored Automation creation is represented as **Agent Candidate-authoring Contribution** plus a correlation to normal S6 intake.

```text
A2 Agent Decision / authoring intent
→ A6 Candidate-authoring Contribution + provenance
→ normal S6 Automation authoring intake
→ S6 validation / semantic certification / canonical-definition lifecycle as applicable
→ S8 Formal Artifact Acceptance
→ S8 Formal Execution Admission when execution is later requested
→ normal Automation runtime topology
```

Permanent:

```text
Agent Candidate-authoring Contribution
!= S6 canonical Automation Definition

Candidate content possession
!= canonicalization

Candidate validation
!= Formal Artifact Acceptance

Formal Artifact Acceptance
!= Formal Execution Admission

Candidate authored
!= candidate executed
```

A6 owns only Agent-side authorship/provenance and S6 intake correlation. It does not create an ephemeral Agent-owned Workflow semantic class.

## 7.7 A6-R07 — External Attempt / Effect / Automation Evidence Intake & Qualification

A6 receives or correlates source-owned evidence from Node, Automation, runtime coordination and other accepted owners.

It must preserve:

```text
source owner
source subject identity/reference
source revision/currentness
attempt/effect/semantic-result distinction
temporal qualification
uncertainty / partiality / stale / conflict qualification
correlation to A6 participation identity
```

A6 may qualify evidence for Agent consumption but cannot canonicalize or rewrite the source fact.

Permanent:

```text
Evidence received
!= evidence current

Evidence correlated
!= evidence canonicalized

Node Effect
!= Automation semantic success automatically

Automation semantic success
!= Agent semantic success automatically

Missing evidence
!= failure automatically
```

## 7.8 A6-R08 — Cross-domain Result Contribution & A2 Reintegration Handoff

A6 emits a source-attributed **Cross-domain Result Contribution** to A2 for Agent continuation.

A6 does not own the resulting A2 Context Projection, Agent Decision or Agent final outcome.

```text
External/source evidence
→ A6 correlation + qualification
→ source-attributed result contribution
→ A2 context reintegration / Agent continuation
```

Permanent:

```text
A6 Result Contribution
!= A2 Agent Decision

A6 Result Contribution
!= participant/source fact SoT

Result contribution available
!= Agent operation complete automatically
```

This preserves the accepted Batch-1 NSH reintegration seam.

## 7.9 A6-R09 — Cross-domain Recovery / Reconciliation Participation

A6 participates in RCP-20 only for its own delegation/invocation/candidate-authoring facts.

```text
A6 retained provenance / outstanding correlations
→ RT-R04 recovery coordination when cross-component recovery is required
→ source owners re-observe their own partitions
→ A6 re-correlates returned evidence
→ A2 consumes qualified result/currentness
```

Permanent:

```text
A6 recovery participation
!= R4 coordination authority

A6 correlation copy
!= Node / Automation source SoT

Reconnect
!= execution resumed automatically

Re-observation
!= source rewrite

Conflict detected
!= conflict resolved
```

No universal retry/replay/rollback/compensation or authoritative synchronization law is created.

## 7.10 A6-R10 — History, Provenance, Diagnostics & RCP-12 Governance

A6 maintains non-destructive provenance for its own facts, including applicable:

```text
originating Agent Operation / revision
Agent Decision lineage
A6 participation identity
target reference/revision/capability qualification
governance / Admission / Runtime references
downstream dispatch / attempt / effect / Automation-result references
candidate-authoring contribution and S6 intake correlation
currentness / uncertainty / failure / partiality
recovery/reconciliation participation
compatibility/conformance history
```

Diagnostics expose only A6-owned facts plus source-attributed references. Secret material is not duplicated into ordinary diagnostic payloads.

RCP-12 contract governance is owned here at the AG-R04 source/participant side; external consumers keep their already accepted authority and facts.

---

# 8. NSH Batch-2 Extension Synthesis

NSH remains the same named internal architecture concept accepted in Batch 1.

Batch 2 adds two bounded extension seams:

```text
NSH Composition Extension Seam
→ A2 Agent Decision / operation context
→ A5 composition coordination
→ participant A2 operations
→ A5 source-attributed composition result contribution
→ A2 continuation

NSH Cross-domain Action Extension Seam
→ A2 Agent Decision / action proposal lineage
→ A6 governed participation
→ external accepted Admission / Runtime / Node / Automation topology
→ A6 source-attributed result contribution
→ A2 continuation
```

Neither seam changes the Harness evolution law:

```text
Harness Strategy
→ MUST remain model-adaptive where applicable

Provider / Model Capability Profile
→ MAY inform bounded Harness adaptation

Current-generation model limitation
→ MUST NOT automatically become permanent Product Architecture

Provider/model evolution
→ MUST NOT silently rewrite Agent semantics
```

Provider capability evidence may influence how an NSH realization participates in A5/A6, but provider-native team/tool/delegation features cannot become semantic authority merely because they exist.

```text
Provider-native Multi-Agent feature
!= A5 Authority

Provider-native tool/agent handoff
!= S8 Admission

Provider-native workflow primitive
!= S6 Automation semantics
```

---

# 9. Identity and Namespace Model

Batch 2 introduces only bounded semantic identities/references necessary to prevent collapse.

| Subject | Owner | Distinct from | Physical format |
|---|---|---|---|
| Multi-Agent Composition Operation | A5 / AG-R03 | Agent Operation, Runtime Attempt, Harness Invocation | not selected |
| Composition Participant Correlation | A5 / AG-R03 | participant Agent Operation/Attempt | not selected |
| Composition Context Contribution | A5 / AG-R03 coordination fact; source material retains source owner | A2 Context Projection / external factual SoT | not selected |
| A5 Composition Outcome Qualification | A5 / AG-R03 | participant semantic outcome | not selected |
| A6 Cross-domain Participation | A6 / AG-R04 | Agent Decision, Admission, Dispatch, Attempt, Effect | not selected |
| Agent Candidate-authoring Contribution | A6 / AG-R04 | S6 Automation Candidate/Canonical Definition | not selected |
| Cross-domain Result Contribution | A6 / AG-R04 | source Attempt/Effect/Automation result; A2 Agent Decision | not selected |

No Product-wide identity namespace is created. Every identity is bounded to an already accepted A5/A6 semantic partition.

---

# 10. Revision, Temporal and Historical Semantics

## 10.1 Revision binding

Historical interpretation must preserve the effective revisions actually applicable to a participation occurrence.

```text
latest Agent revision
!= historical participant revision

latest Automation revision
!= historical invoked Automation revision

latest Policy / Trust / configuration
!= historical applicable governance context automatically
```

A5/A6 must retain source revision references/currentness evidence where material. They do not define universal version-resolution algorithms.

## 10.2 Temporal evidence

A5/A6 temporal semantics distinguish, where applicable:

```text
intent formed time/context
coordination/participation occurrence time
source evidence occurrence time
source evidence observation/receipt time
currentness/freshness qualification time
recovery/re-observation time
```

Receipt time is not automatically source occurrence time. Latest timestamp is not a canonical winner.

## 10.3 Non-destructive history

```text
new participant engagement
!= rewrite old engagement

new delegation/invocation
!= rewrite prior delegation/invocation

retry/re-entry
!= erase prior attempt/effect

later success
!= erase earlier failure/unavailability

current projection
!= historical rewrite
```

---

# 11. Authority / SoT / Actual-state Ownership Matrix

| Assertion | Final owner / authority | A5/A6 treatment |
|---|---|---|
| Agent Definition / composition canonical semantics | A1 / ns_agent | consume only |
| Agent canonical definition revision | A1 / ns_agent | consume/reference |
| Participant Agent Operation / Attempt / Context / Agent Decision | A2 / AG-R01 | source evidence only |
| Provider mediation observation | A3 / AG-R02 | consume/reference |
| Tool/Knowledge consumption semantics | A4 + original source owners | consume/reference |
| Multi-Agent composition coordination/provenance | A5 / AG-R03 | owns only this bounded partition |
| Agent cross-domain delegation/invocation/candidate-authoring provenance | A6 / AG-R04 | owns only this bounded partition |
| Automation Definition / canonical Automation SoT | S6 / ns_server | A6 consume/submit candidate only |
| Automation semantic continuation/result | S6 / SV-R02 | A6 correlate only |
| Formal Artifact Acceptance | S8 / ns_server | consume/reference only |
| Formal Execution Admission | S8 / SV-R04 | consume/reference only |
| Presence / reachability | R1 / RT-R01 | consume/reference only |
| Routing / scheduling / dispatch | R2 / RT-R02 | consume/reference only |
| Cross-component continuation/delegation coordination | R3 / RT-R03 | consume/correlate only |
| Recovery/reconciliation coordination | R4 / RT-R04 | participant only |
| Node readiness | N1 / ND-R01 | consume/reference only |
| Node Attempt | N2 / ND-R02 | correlate only |
| Node protected Effect / Node-origin source fact | N3 / ND-R03 | correlate only |
| Human Task aggregation/projection/routing | S11 / SV-R07 | consume where applicable |
| Desired configuration | S9 / SV-R05 | consume where applicable |
| A5/A6 Applied configuration | applicable A5/A6 runtime partition if genuinely applied there | source-owned contribution only |
| Diagnostics/provenance view | federated original fact owners | A5/A6 contribute own facts only |

```text
Multiple Final Authority for Same Bounded Assertion
→ 0

Multiple Final SoT for Same Bounded Assertion
→ 0

Circular Actual-state Ownership
→ NONE
```

---

# 12. Tenant / Organization / Principal / Authentication / Authorization / Trust

A5/A6 propagate governed context without becoming its authority.

Permanent:

```text
Tenant
!= Organization

Principal present
!= authenticated automatically

Authenticated
!= Policy permit

Policy permit
!= Execution Admission

Trust evidence present
!= trusted automatically

Composition participant
!= same Principal automatically

Context propagation
!= privilege propagation automatically

Delegation
!= authority transfer
```

A5/A6 must preserve applicable source identity/revision/currentness for Tenant, Organization, Principal, authentication, Policy and Trust evidence.

Cross-Tenant or cross-Organization semantics are not invented here. If a proposed composition/delegation requires a new cross-Tenant trust or authorization law, the design must stop for GAC/Owner revalidation.

No “caller privilege automatically flows to callee” rule is created.

---

# 13. Data, Privacy and Secret Boundary

## 13.1 Data and privacy

A5/A6 apply minimization and source-attribution requirements to context/result propagation.

```text
Visible to one participant
!= visible to every participant

Composition membership
!= disclosure authorization

Delegation target selected
!= permission to disclose all Agent context

Result received
!= permission to retain all source material indefinitely
```

Privacy-sensitive context must retain source/disclosure qualification and applicable redaction semantics. A5/A6 do not create a global shared data store.

## 13.2 Secret boundary

```text
Secret Reference
!= Secret Material

Reference possession
!= permission to resolve material

Composition provenance
!= secret-material diagnostic channel

Delegation correlation
!= credential forwarding authority
```

A5/A6 may carry/refer to secret references only where accepted governance and Foundation semantics allow. Secret material must not be copied into ordinary composition/delegation history merely for diagnostics.

---

# 14. RCP-11 — Multi-Agent Composition Stable Contract Synthesis

## 14.1 Contract identity and purpose

```text
RCP-11
→ AG-R03 ↔ AG-R01
→ Multi-Agent Composition
→ A5 coordination facts + A2 participant facts
```

This Batch closes the A5 owner/coordinator side and A2 participant-integration refinement at current `ns_agent` design-semantic level. It does not claim Global/Full Cross-component Closure.

## 14.2 Stable semantic subjects

Representation-neutral RCP-11 semantics include, as applicable:

```text
Composition Operation identity/reference
initiating Agent Operation reference
initiating Agent Definition Revision
participant Agent reference
participant effective revision
participant relationship/correlation
participant Agent Operation / Attempt references when source-established
composition context-contribution references and provenance
source evidence references/currentness
A5 coordination-stage evidence
partiality/failure/unknown/compatibility qualifications
composition outcome qualification
Tenant / Organization / Principal context references
Policy / Trust / governance evidence references
history / lineage / recovery / reconciliation references
compatibility / migration / conformance qualification
```

## 14.3 Producer obligations — A5 / AG-R03

A5 must:

```text
preserve composition identity and historical revision binding
preserve participant/source ownership
never flatten participant runtime facts into A5 SoT
surface partial/unknown/stale/incompatible evidence
preserve context-contribution source attribution
preserve non-destructive history
provide source-attributed diagnostic/provenance evidence
avoid inferring authority from caller/callee/peer relationship
```

## 14.4 Participant obligations — A2 / AG-R01

A2 remains responsible for each participant Agent operation/context/runtime fact and must:

```text
maintain its own Agent Operation / Attempt identities
consume A5 correlation without surrendering Actual-state ownership
preserve effective Agent Definition revision
preserve source attribution for received composition context/result contributions
return source-owned participant evidence suitable for correlation
not treat A5 composition projection as participant runtime SoT
```

## 14.5 Failure / offline / compatibility

RCP-11 preserves explicit `PARTIAL / UNKNOWN / STALE / UNAVAILABLE / INCOMPATIBLE / INDETERMINATE / CONFLICTING` semantics where applicable and no universal winner/retry law.

Private/offline correctness requires no mandatory public coordinator, broker or SaaS Agent service.

## 14.6 Contract invariant

```text
RCP-11 Correlation
!= Authority Transfer

RCP-11 Composition Outcome
!= Participant Actual-state Merge

RCP-11 Context Contribution
!= Shared Factual SoT
```

---

# 15. RCP-12 — Agent Delegation Stable Contract Synthesis

## 15.1 Contract identity and purpose

```text
RCP-12
→ AG-R04 → SV / RT / ND and applicable Agent continuation
→ Agent Delegation / Cross-domain Participation
```

This Batch closes the AG-R04 source/participant side at current design-semantic level and aligns it with already accepted server/runtime/node consumer expectations. It does not claim Full Cross-component Closure.

## 15.2 Stable semantic subjects

Representation-neutral RCP-12 semantics include, as applicable:

```text
originating Agent Operation / Agent Definition Revision
Agent Decision / intent lineage reference
A6 Cross-domain Participation identity/reference
participation kind / target domain classification
Target reference
Target effective revision / capability qualification
Tenant / Organization / Principal context
Policy / Trust / governance references
Artifact Acceptance / Admission references where applicable
Presence / readiness references where applicable
Dispatch / R3 coordination references where applicable
Node Attempt / Effect references when source-established
Automation Operation / semantic-result references when source-established
Agent Candidate-authoring Contribution reference
S6 candidate-intake correlation reference
currentness / availability / uncertainty / partiality / conflict qualification
Cross-domain Result Contribution reference
recovery/reconciliation/history/provenance/diagnostic references
compatibility/migration/conformance qualification
```

## 15.3 AG-R04 producer obligations

A6 must:

```text
emit only Agent-side intent/participation/provenance facts it genuinely owns
preserve target-domain Authority and SoT
preserve Admission/Dispatch/Attempt/Effect separation
preserve effective target revision/capability correlation
preserve source attribution for downstream evidence
keep candidate Automation authoring separate from S6 canonicalization and S8 Acceptance
surface unreachable/unavailable/stale/unknown/indeterminate conditions
retain non-destructive history
```

## 15.4 Consumer obligations

Existing accepted consumers retain their authority:

```text
S6
→ treats Agent-authored material as governed candidate intake, not canonical by origin

S8
→ evaluates Artifact Acceptance / Admission independently of Agent intent

R2
→ schedules/routes/dispatches only according to accepted coordination semantics

R3
→ coordinates cross-component delegation/continuation without taking AG-R04 source authority

N1
→ owns Node readiness evidence

N2
→ originates Node Attempt only when actual local execution is established

N3
→ owns protected Node Effect/source facts

A2
→ consumes source-attributed A6 result contribution for Agent continuation
```

## 15.5 Contract invariant

```text
RCP-12 Agent Delegation
!= Admission
!= Dispatch
!= Attempt
!= Effect

RCP-12 Candidate-authoring provenance
!= Automation Authority
```

---

# 16. Bounded Refinement of Other RCPs

No new RCP is created. Count remains `24`.

| RCP | Batch-2 treatment | Preserved authority / qualification |
|---|---|---|
| RCP-02 | consume/applicability/correlation only | S8 / SV-R04 remains final Admission owner |
| RCP-03 | consume/reference where reachability matters | RT-R01 semantics not reopened |
| RCP-04 | consume Node readiness reference | ND-R01 remains source owner |
| RCP-05 | consume Dispatch reference | RT-R02 remains source owner |
| RCP-06 | consume R3 continuation/delegation/intervention coordination evidence | RT-R03 semantics not reopened |
| RCP-07 | consume Node Attempt evidence | ND-R02 remains source owner |
| RCP-08 | consume Node Effect evidence | ND-R03 remains source owner |
| RCP-09 | consume accepted A2 Agent Runtime contract | no A2 redesign |
| RCP-10 | consume accepted A3 Provider Mediation contract | no A3 redesign |
| RCP-13 | consume accepted Automation Continuation semantics | S6/SV-R02 preserved |
| RCP-15 | consume accepted Automation Composition semantics | S6/SV-R02 preserved |
| RCP-16 | refine A5/A6 correlation only where a composition/delegation intersects Agent HITL | A2 source-wait semantics preserved; no full closure claim |
| RCP-17 | A5/A6 Trial contribution only when genuinely participating in an Agent Trial | domain Trial authority preserved; no full closure claim |
| RCP-19 | A5/A6 Applied config fact contribution only when configuration is genuinely applied there | S9 Desired authority preserved |
| RCP-20 | A5/A6 fact-owner recovery/reconciliation participation only | RT-R04 coordination authority preserved; no full closure claim |
| RCP-22 | A5/A6 original-fact diagnostics/provenance contribution | may complete `ns_agent` six-boundary contribution at current design level; no full cross-component closure claim |
| RCP-24 | receiving/applicability/correlation expectation only where material | WB/SDK source interaction remains downstream |

Explicitly not claimed:

```text
RCP-11 Full Cross-component Closure
RCP-12 Full Cross-component Closure
RCP-16 Full Cross-component Closure
RCP-17 Full Closure
RCP-20 Full Cross-component Closure
RCP-22 Full Cross-component Closure
RCP-24 Full Closure
```

---

# 17. Failure, Unknown and Degraded Semantics

A5/A6 distinguish source failure from coordination/participation failure.

Representative qualifications:

```text
PENDING
UNREACHABLE
UNAVAILABLE
UNKNOWN
STALE
INCOMPATIBLE
UNSUPPORTED
INDETERMINATE
CONFLICTING
PARTIAL
SUPERSEDED
```

These are orthogonal semantic qualifications, not one universal state machine.

Permanent:

```text
UNREACHABLE
!= DENIED

UNAVAILABLE
!= FAILED permanently

UNKNOWN
!= SUCCESS
!= FAILURE

STALE
!= CURRENT

INCOMPATIBLE
!= unauthorized automatically

CONFLICTING
!= winner selected

PARTIAL
!= failed automatically
```

No hidden fallback target, implicit local-wins, latest-wins or silent participant substitution is introduced.

---

# 18. Offline / Private Correctness

Core A5/A6 correctness must remain possible in private/offline deployments without mandatory public Internet, public SaaS, public broker, hosted workflow service or provider-owned Multi-Agent control plane.

Offline/degraded behavior preserves:

```text
retained local evidence only for facts actually established locally
remote facts may become UNKNOWN / STALE / UNREACHABLE / UNAVAILABLE
local candidate Automation possession does not create S6 canonicalization / S8 Acceptance
local composition correlation does not become participant Agent SoT
offline delegation does not create retroactive Admission
offline provider capability does not rewrite Agent semantics
```

No Product-wide fail-open/fail-closed law is selected. Where required authority/applicability cannot be established, the uncertainty is preserved rather than silently treating absence as permission.

---

# 19. Recovery / Reconciliation and RCP-20 Contribution

A5 and A6 contribute only their own facts to recovery/reconciliation.

```text
A5 source facts
→ Composition Operation / participant correlation / context-contribution provenance / composition qualification

A6 source facts
→ cross-domain participation / target correlation / candidate-authoring provenance / result-correlation facts

RT-R04
→ cross-component recovery/evidence-exchange/re-observation/reconciliation-stage coordination

Original source owners
→ re-observe / reassert their own facts
```

Permanent:

```text
Recovery coordination
!= source recovery authority

Evidence exchange
!= source fact transfer

Re-observation
!= canonicalization

Reconciliation participation
!= conflict winner authority

Recovery completed at A5/A6
!= all participant/source facts reconciled automatically
```

A5/A6 do not choose merge algorithms, replay algorithms, synchronization direction or conflict precedence.

---

# 20. Compatibility, Migration and Conformance

## 20.1 Composition compatibility

A5 compatibility includes, where applicable:

```text
Agent reference resolvability
Agent effective revision compatibility
required capability/profile compatibility
composition relationship compatibility
context contribution compatibility
RCP-11 conformance
```

A5 does not universalize current provider limitations.

## 20.2 Cross-domain compatibility

A6 compatibility includes, where applicable:

```text
Node target/capability compatibility
Automation target/effective revision compatibility
Admission evidence applicability/currentness
RCP-12 producer/consumer conformance
candidate Automation intake compatibility with S6
```

## 20.3 Migration

Migration must preserve historical identity and lineage. A migration may produce a new effective revision/binding/correlation; it cannot silently reinterpret historical composition/delegation facts.

```text
Migrated target
!= historical target rewritten

Rebound participant
!= old participant history erased

Provider replacement
!= Agent semantic rewrite
```

## 20.4 Conformance

Conformance is separately evaluable for A5/RCP-11 and A6/RCP-12 semantics. Conformance success does not create Admission, Authority or business success.

---

# 21. History, Provenance and RCP-22 Contribution

With A5/A6 now internally designed, the `ns_agent` fact-owner diagnostic/provenance contribution can cover all accepted Agent boundaries at current design level:

```text
A1 → definition/revision provenance
A2 → Agent runtime/context/HITL/decision provenance
A3 → provider mediation observation provenance
A4 → tool/knowledge invocation/evidence provenance
A5 → composition coordination/provenance
A6 → cross-domain delegation/invocation/candidate-authoring provenance
```

Qualification:

```text
ns_agent six-boundary RCP-22 contribution
→ COMPLETE AT CURRENT NS_AGENT DESIGN LEVEL, subject to independent Global Acceptance

RCP-22 Full Cross-component Closure
→ NOT CLAIMED
```

Diagnostics remain federated by original fact ownership.

```text
Diagnostic aggregation
!= canonicalization

Trace completeness
!= source factual completeness automatically

Provenance link
!= ownership transfer
```

Sensitive evidence is redacted/minimized under accepted Foundation and governance semantics.

---

# 22. Applied Configuration / RCP-19 Qualification

A5/A6 may own Applied Configuration actual-state only for configuration genuinely applied to their own runtime behavior.

```text
S9 / SV-R05
→ Desired Configuration authority

A5 / A6 runtime partition
→ bounded Applied evidence only where genuinely applied there
```

Permanent:

```text
Desired
!= Distributed
!= Applied
!= Observed

A5/A6 Applied
!= S9 Desired authority

Configuration
!= Secret Material
```

No configuration schema, rollout algorithm or provider is selected.

---

# 23. Trial / HITL / RCP-16 / RCP-17 Qualification

## 23.1 HITL

If A5/A6 participation encounters Agent HITL:

```text
A2 / AG-R01
→ source wait / response applicability / Agent semantic resume

A5
→ may correlate which composition participant is waiting and composition partiality

A6
→ may correlate cross-domain participation context where materially required

S11 / WB / R3
→ retain accepted aggregation/submission/routing/coordination roles
```

A5/A6 do not become Human Task source-wait authority.

## 23.2 Trial

When A5/A6 are exercised inside an accepted Agent Trial:

```text
A1/A2
→ Agent Trial semantics/runtime state

A5
→ composition-coordination Trial evidence it genuinely owns

A6
→ delegation/invocation/candidate-authoring Trial evidence it genuinely owns

actual executor/source owner
→ Attempt / Effect facts
```

Trial success does not imply production Admission.

---

# 24. Dependency Taxonomy

The Batch uses the accepted taxonomy:

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY
```

Only `SDD` participates in the hard semantic-definition cycle check.

## 24.1 A5 hard SDD graph

```text
A5-R02 → A5-R01
A5-R03 → A5-R01, A5-R02
A5-R04 → A5-R01, A5-R02, A5-R03
A5-R05 → A5-R01, A5-R03
A5-R06 → A5-R01, A5-R02, A5-R03, A5-R04
A5-R07 → A5-R01, A5-R02, A5-R03, A5-R06
A5-R08 → A5-R01, A5-R06, A5-R07
A5-R09 → A5-R01, A5-R02, A5-R03, A5-R04, A5-R05, A5-R06, A5-R07, A5-R08
```

## 24.2 A6 hard SDD graph

```text
A6-R02 → A6-R01
A6-R03 → A6-R01, A6-R02
A6-R04 → A6-R01, A6-R02, A6-R03
A6-R05 → A6-R01, A6-R02, A6-R03
A6-R06 → A6-R01, A6-R02
A6-R07 → A6-R01, A6-R02, A6-R03
A6-R08 → A6-R01, A6-R07
A6-R09 → A6-R01, A6-R07, A6-R08
A6-R10 → A6-R01, A6-R02, A6-R03, A6-R04, A6-R05, A6-R06, A6-R07, A6-R08, A6-R09
```

## 24.3 Cross-boundary dependency classification

```text
A1 → A5/A6 Agent-definition/reference/revision semantics
→ SDD / normative upstream

A2 → A5/A6 Agent Operation/Decision/context semantics
→ SDD / normative upstream

A3 → A5/A6 provider capability observations
→ ACD / XED as applicable

A4 → A5/A6 accepted Tool/Knowledge invocation/evidence semantics
→ ACD / EL as applicable

A5 ↔ participant A2 runtime facts
→ EL / HPL at runtime after semantic subjects are defined

A6 ↔ S6/S8/R1/R2/R3/R4/N1/N2/N3
→ ACD / EL / HPL / XED as applicable
```

No reverse edge makes A1/A2 semantic definitions depend on A5/A6 runtime evidence.

Result:

```text
Hard SDD Graph
→ ACYCLIC

Authority Cycle
→ NONE

Circular Actual-state Ownership
→ NONE

Runtime Feedback Loop
→ may exist as evidence/continuation flow
→ NOT a semantic-definition cycle
```

---

# 25. Mandatory Semantic Resolution Matrix

| Dimension | A5 resolution | A6 resolution |
|---|---|---|
| Identity / Namespace | bounded Composition Operation / participant correlation / context-contribution identities; no universal namespace | bounded cross-domain participation / candidate-authoring contribution / result-contribution identities; no universal namespace |
| Revision / Evolution | consume A1 revisions; preserve effective historical participant revision; no silent rebind | preserve effective Node/Automation target revision/capability evidence; no historical rewrite |
| Authority | A1 remains Agent semantic authority; A5 only composition coordination | external domain authorities preserved; A6 only Agent-side participation/provenance |
| Semantic Ownership | composition coordination semantics only | Agent-side delegation/invocation/candidate-authoring participation only |
| Source of Truth | no new SoT; A1 canonical Agent definitions and original factual owners preserved | no new SoT; S6 Automation SoT, Node/external source owners preserved |
| Actual-state Ownership | A5 coordination/provenance only; each Agent remains A2 | A6 participation/provenance only; target/runtime/attempt/effect owners unchanged |
| State / Lifecycle | operation-scoped coordination facts + explicit partial/unknown qualifications; no universal state machine | intent/handoff/correlation facts + explicit target/source qualifications; no universal state machine |
| Temporal Semantics | occurrence vs receipt/currentness distinguished; historical revisions retained | intent/dispatch/attempt/effect/result times not collapsed; currentness explicit |
| Failure | participant failure remains participant fact; composition partiality separate | delegation/invocation failure separated from Admission/Attempt/Effect/source failure |
| Unknown / Indeterminate | explicit UNKNOWN/STALE/UNAVAILABLE/INCOMPATIBLE/INDETERMINATE | same; absence of evidence does not become authorization or success |
| Tenant | propagated by governed context; no cross-Tenant authority invention | propagated; target domain enforces accepted semantics |
| Organization | distinct from Tenant; source semantics preserved | distinct from Tenant; no new mapping authority |
| Principal | per participant/source attribution; no caller-principal universal inheritance | originating Principal preserved; target-side authority unchanged |
| Authentication | evidence consumed, never inferred from participation | evidence consumed; not equivalent to Admission |
| Authorization / Policy | A5 does not grant permission | A6 cannot bypass S8/target policy; Agent intent != permit |
| Security | trust/policy boundaries preserved; no shared-memory trust shortcut | target trust/admission boundaries preserved |
| Trust | caller/callee/peer relation gives no trust automatically | delegation gives no trust automatically |
| Data / Privacy | source-attributed context contributions; minimum necessary disclosure | source-attributed target/result evidence; disclosure minimized |
| Secret Boundary | Secret Reference only where applicable; diagnostics redact material | no implicit credential forwarding; Secret Reference != material |
| Offline / Degraded | local correlation retained only for established local facts; remote unknown explicit | unreachable/unknown explicit; candidate possession != acceptance; no retroactive Admission |
| Recovery / Reconciliation | A5 own-fact participation; R4 coordinates cross-component recovery | A6 own-fact participation; source owners re-observe; R4 coordinates |
| Compatibility | participant reference/revision/capability conformance | target revision/capability + RCP-12 conformance |
| Migration | new binding/correlation without historical rewrite | target/candidate migration preserves lineage/history |
| Conformance | RCP-11 independently evaluable | RCP-12 independently evaluable |
| Cross-boundary Dependency | A1/A2 semantic upstream; A3/A4 evidence/context dependencies | server/runtime/node accepted contracts consumed, not reopened |
| History / Provenance | non-destructive composition/participant/context lineage | non-destructive intent/target/admission/dispatch/attempt/effect/candidate lineage |
| Diagnostics | A5 facts only + source-attributed refs; no canonicalization | A6 facts only + source-attributed refs; no secret/material authority leak |
| Invariant | composition != merged participant state/Automation/runtime scheduler | delegation != Admission/Dispatch/Attempt/Effect/Automation authority |
| Decision Traceability | CID-AG-B2-DAD set + upstream Owner decisions | CID-AG-B2-DAD set + S6/S8/runtime/node accepted decisions |
| Revalidation Trigger | new universal topology/shared state/cycle product semantics/scheduler/authority | new workflow authority/bypass/fail law/retry law/trust boundary/provider lock-in |

```text
Missing / Ambiguous Normative Dimension
→ 0

Implementation-defined Escape
→ 0
```

---

# 26. Major Decision Escalation / MDE Audit

No current Batch-2 decision requires a new Owner MDE.

```text
New Product Capability
→ 0

New Product Component / Internal Boundary / Runtime Role
→ 0 / 0 / 0

New Authority / SoT / Actual-state Owner
→ 0 / 0 / 0

New Trust / Security Boundary
→ 0

Major Tenant / Organization semantic change
→ 0

Major universal identity namespace
→ 0

Universal scheduling / fairness / parallelism law
→ 0

Universal retry / cancel / rollback / compensation / once guarantee
→ 0

Conflict winner / merge / authoritative synchronization law
→ 0

Material offline fail-open / fail-closed law
→ 0

New Automation / Workflow Authority
→ 0

Universal Multi-Agent Authority
→ 0

Merged participant Actual-state SoT
→ 0

Major recursive/cyclic Multi-Agent Product semantics
→ 0

Mandatory public SaaS / broker / workflow / recovery dependency
→ 0

Framework / provider / protocol / storage lock-in
→ 0

Open MDE
→ 0
```

## 26.1 Named Owner/GAC-reserved deferrals

The following are deliberately not decided by this Batch and are not implementation-defined escapes:

```text
universal supervisor/team/graph topology
→ later authority: only if a material Product need appears, GAC/Owner revalidation; otherwise downstream replaceable realization may vary within this semantic contract

major recursive/cyclic Multi-Agent Product semantics
→ later authority: GAC/Owner MDE if materially required

universal scheduling/fairness/parallelism semantics
→ later authority: GAC/Owner if Product-semantic commitment is proposed; ordinary realization remains downstream

universal retry/cancel/rollback/compensation/once semantics
→ later authority: existing source-domain/Runtime authority or GAC/Owner MDE if a new Product-wide law is proposed

concrete Multi-Agent framework / Agent framework / graph engine / actor system
→ later authority: technology/implementation selection only after Design-to-Implementation readiness and within accepted contracts

concrete storage/protocol/schema/process topology
→ later authority: detailed design / implementation planning as formally authorized
```

For current conformance, where a proposed composition requires semantics that the accepted architecture does not define and cannot safely qualify, A5 reports unsupported/incompatible/indeterminate rather than inventing a universal rule.

---

# 27. Shared Foundation Sufficiency

A5/A6 reuse accepted Foundation semantics for:

```text
Temporal / Freshness
Correlation / Provenance
Technical Status / Uncertainty
Governed Context Propagation
Semantic Representation mechanics
Network mechanics where later realized
Diagnostics / Redaction
Secret Reference
Compatibility / Conformance
Bootstrap Configuration
```

No missing mandatory Foundation semantic was found.

```text
New Foundation Capability Required
→ 0

Parallel Agent-local Foundation
→ 0

Generic Scheduler / Workflow / Retry Foundation reintroduced
→ 0

Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND
```

---

# 28. Stable Invariant Set

The Batch-2 architecture requires at least the following invariants:

```text
INV-01  A1 remains Agent semantic authority and canonical Agent Definition SoT.
INV-02  A5 owns only composition coordination/provenance, never participant Agent Actual-state.
INV-03  A6 owns only Agent-side cross-domain participation/provenance, never target-domain authority.
INV-04  NSH remains a named internal architecture concept, not a new boundary/role/authority.
INV-05  Composition Operation identity remains distinct from participant Agent Operation/Attempt.
INV-06  Effective participant/target revision remains historically identifiable after participation.
INV-07  Composition context contribution preserves source attribution and never becomes universal shared factual SoT.
INV-08  Caller/callee/peer relation does not imply Authority, Trust or Principal inheritance.
INV-09  Partial participant evidence remains visible; no universal winner/merge rule is inferred.
INV-10  Agent-to-Agent composition is not Automation Workflow Authority.
INV-11  Agent cross-domain delegation is not Runtime Dispatch Authority.
INV-12  Agent Intent / Harness Action Proposal is not Formal Execution Admission.
INV-13  Admission, Dispatch, Attempt and Effect remain distinct.
INV-14  Agent→Node delegation never transfers N2/N3 ownership.
INV-15  Agent→Automation invocation never transfers S6 Authority/SoT/runtime semantic ownership.
INV-16  Agent-authored candidate Automation always enters normal S6/S8 governance lifecycle.
INV-17  Candidate possession is not Acceptance or Admission.
INV-18  A5/A6 recovery participation never becomes RT-R04 recovery coordination authority or source recovery authority.
INV-19  Reconnect/replay/re-observation never retroactively authorizes or rewrites history.
INV-20  Diagnostics/provenance remain federated by original fact ownership.
INV-21  Secret Reference is not Secret Material and ordinary diagnostics do not become secret channels.
INV-22  No mandatory public SaaS/provider/broker/workflow/recovery dependency is required for correctness.
INV-23  Harness adaptation may use provider capability observations but provider evolution cannot rewrite Agent semantics.
INV-24  RCP count remains 24; no duplicate stable-contract pressure is created.
```

---

# 29. DAD Summary

The detailed DAD Evidence is persisted separately. Candidate-level decision set:

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

No DAD selects an Owner-reserved universal semantic law.

---

# 30. Review-readiness and Exit Qualification

Candidate self-check:

```text
Authorized Boundary Coverage
→ A5 / A6 → 2 / 2 / 100%

Accepted-upstream Redesign
→ 0

A5 Internal Responsibilities
→ 9

A6 Internal Responsibilities
→ 10

Total Batch-2 Internal Responsibilities
→ 19

Unowned Material Responsibility
→ 0

Duplicate Final Responsibility
→ 0

RCP-11 Owner-side / A2 integration semantic synthesis
→ COMPLETE AT CANDIDATE LEVEL

RCP-12 AG-R04 source/participant-side semantic synthesis
→ COMPLETE AT CANDIDATE LEVEL

New RCP
→ 0

Runtime / Domain Stable Contract Pressure Count
→ 24 / unchanged

Hard SDD Graph
→ ACYCLIC

Authority Cycle
→ NONE

Circular Actual-state Ownership
→ NONE

Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Implementation Leakage
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Implementation-defined Escape
→ 0
```

This Candidate does not declare Global Acceptance, `ns_agent` Internal Design Exhaustion or Component Internal Design Global Closure.

```text
Candidate Status
→ COMPLETED / AWAITING_DAD_REVIEW

Maximum bounded-session status after all producing evidence
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

The next producing artifact is DAD Evidence only, after validating this Candidate commit delta.