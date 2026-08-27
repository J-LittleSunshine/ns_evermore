# ns_evermore Decision Registry — Current Revision

- Version: `0.0.33`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.32`

All accepted normative decisions and baselines in Decision Registry `0.0.32` remain in force unless explicitly refined below.

## Current Accepted Global Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
Unified Governance → 0.0.2 / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Product Capability Exhaustion → SATISFIED
Five-component Internal Architecture Boundaries → GLOBAL_ACCEPTED / NORMATIVE
Five-component Internal-boundary Exhaustion → SATISFIED
Accepted Internal Boundaries → 34
Runtime Responsibility Architecture → GLOBAL_CLOSED / COMPLETE
Runtime Roles → 22
Runtime / Domain Stable Contract Pressure → 24 / NAMED DOWNSTREAM DESIGN AUTHORITY
Shared Foundation Architecture / Contract / Module / Provider → GLOBAL_CLOSED / COMPLETE
Foundation Provider Design Exhaustion → SATISFIED
Component Internal Design Readiness → SATISFIED
```

## Product Component Internal Design State

```text
ns_server Component Internal Design → GLOBAL_CLOSED / COMPLETE
ns_server Internal Design Exhaustion → SATISFIED

ns_runtime Component Internal Design → GLOBAL_CLOSED / COMPLETE
ns_runtime Internal Design Exhaustion → SATISFIED

ns_node Component Internal Design → GLOBAL_CLOSED / COMPLETE
ns_node Internal Design Exhaustion → SATISFIED

ns_agent Component Internal Design / Batch 1 → GLOBAL_ACCEPTED
Accepted ns_agent Boundaries → A1 / A2 / A3 / A4
Accepted ns_agent Boundary Coverage → 4 / 6 / 66.67%
Accepted ns_agent Internal Responsibility Count → 35
Remaining accepted ns_agent boundaries without Component Internal Design → A5 / A6
ns_agent Internal Design Exhaustion → NOT YET REASSESSED AFTER BATCH 1 ACCEPTANCE
ns_agent Component Internal Design Global Closure → NOT DECLARED

ns_web Component Internal Design → NOT AUTHORIZED
```

Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_internal_design_batch_1_global_acceptance_0.0.1.md`

## Accepted ns_agent Batch-1 Internal Architecture

### A1 — Agent Definition & Evolution

```text
A1-R01 Agent Definition Identity & Canonical Revision Custody
A1-R02 Durable Agent Semantic Content & Intent Governance
A1-R03 Provider / Model / Tool / Knowledge Reference & Requirement Governance
A1-R04 Dual-authoring Change Intake & Semantic Convergence
A1-R05 Definition Validation, Compatibility & Conformance
A1-R06 Governed Trial Intent & Runtime Binding Eligibility
A1-R07 Definition History, Migration, Provenance & Contract Governance
```

### A2 — Agent Runtime Context, HITL & Actual-state

```text
A2-R01 Agent Operation Origination & Operation Identity
A2-R02 Runtime Definition / Governance / Admission Context Binding
A2-R03 Agent Runtime Attempt / Continuation Episode Identity & Lineage
A2-R04 NSH Local Reasoning / Execution Loop Coordination
A2-R05 Runtime Context Contribution Intake & Source Attribution
A2-R06 Runtime Context Projection, Revision, Selection & Transformation
A2-R07 Model-adaptive Harness Strategy Decision & Applicability
A2-R08 Harness Invocation Identity, Target Correlation & Lineage
A2-R09 Model Contribution Reintegration, Agent Decision & Action Proposal
A2-R10 HITL Wait, Human-response Applicability & Continuation
A2-R11 Checkpoint, Long-running Continuation & Recovery Participation
A2-R12 Trial & Intervention Receiving / Outcome Qualification
A2-R13 Runtime Outcome, Currentness, History, Provenance & Diagnostics
```

### A3 — Model / Provider Mediation & Multimodal Capability

```text
A3-R01 Provider / Model Reference & Mediation-context Binding
A3-R02 Provider / Model Capability-profile Observation & Revision
A3-R03 Compatibility, Conformance & Multimodal Qualification
A3-R04 Provider Mediation Interaction & Harness-invocation Correlation
A3-R05 Provider Response / Failure / Availability Observation
A3-R06 Provider Evolution / Replacement & Harness-adaptation Input
A3-R07 Mediation History, Secret / Privacy Boundary & Diagnostics
```

### A4 — Tool & Knowledge Consumption

```text
A4-R01 Tool / Knowledge Capability Reference & Governance Binding
A4-R02 Tool Binding, Compatibility & Applicability Qualification
A4-R03 Knowledge / RAG Source Binding & Factual-authority Preservation
A4-R04 Invocation Preparation & Agent-side Tool Intent Qualification
A4-R05 Invocation Correlation & External / Node Evidence Intake
A4-R06 Result / Knowledge Contribution Qualification & Context Reintegration
A4-R07 Retry / Re-entry / Uncertainty / Currentness & Non-destructive Lineage
A4-R08 Tool / Knowledge Consumption History, Privacy & Diagnostics
```

## ns_evermore Harness / NSH

Accepted identity:

```text
NSH → NAMED INTERNAL ARCHITECTURE CONCEPT INSIDE EXISTING ns_agent BOUNDARIES
```

Accepted placement:

```text
A1 → Agent Definition / Revision authority + canonical SoT upstream
A2 → primary NSH runtime/context/continuity/HITL core
A3 → provider/model capability and mediation evidence lane
A4 → Tool/Knowledge/RAG consumption and reintegration lane
A5/A6 → future opaque extension seams only / NOT DESIGNED
```

Not accepted as:

```text
sixth Product Component
A7
AG-R05 Runtime Role
Shared Foundation capability
SDK Runtime Authority
new Product Capability
new final Actual-state owner
```

## Harness Evolution Law

```text
Harness Strategy
→ MUST remain model-adaptive where applicable

Provider / Model Capability Profile
→ MAY inform bounded Harness strategy selection/adaptation

Current-generation model limitation
→ MUST NOT automatically become permanent Product Architecture

Provider/model evolution
→ MUST NOT silently rewrite Agent semantics
```

## Identity / History Baseline

```text
Agent Definition Revision != Agent Operation
Agent Operation != Agent Runtime Attempt
Agent Runtime Attempt != Harness Invocation
Harness Invocation != Provider Mediation Interaction
Harness Invocation != Node Attempt
Node Attempt != Node Effect
```

History remains non-destructive:

```text
Retry / re-entry != prior Attempt mutation
Later success != prior failure deletion
Recovery != historical uncertainty deletion
Later Context Revision != prior Context rewrite
```

No universal physical identity namespace is accepted.

## Context / Memory Baseline

```text
Source-attributed contribution → A2 Context Projection Revision
```

Permanent:

```text
Context Projection != Knowledge SoT
Context Cache != Knowledge SoT
Agent Memory Projection != External Data SoT
Compacted Context != Original Source Fact
```

No context-compaction, ranking, memory or storage algorithm is accepted.

## Governed Action Boundary

```text
Provider / Model Output Observation
→ Model Contribution
→ Agent Decision
→ optional Harness Action Proposal
→ Tool Invocation Intent OR future A6 seam
→ applicable Admission / runtime coordination / executor
→ Attempt
→ Effect
→ source/domain outcome
```

Permanent:

```text
Model Output != Agent Decision
Agent Decision != Admission
Harness Action Proposal != Admission
Tool Selection != Admission
Invocation != Attempt
Attempt != Effect
Effect != Business Semantic Success automatically
```

## Harness / Automation / Runtime Non-collapse

```text
Harness Agent Loop != Automation Workflow Semantics
Harness-local continuation != RT-R02 cross-component scheduling/routing/dispatch
A2 local next-activity decision != RT-R03 cross-component continuation coordination
Harness Scheduling Convenience != Universal Runtime Scheduling Authority
```

## Stable-contract Qualification

```text
RCP-09 AG-R01 owner/source-side contribution → CLOSED AT CURRENT DESIGN LEVEL
RCP-10 AG-R02 bounded-observation owner-side contribution → CLOSED AT CURRENT DESIGN LEVEL
RCP-16 Agent Human Task source wait/applicability side → CLOSED AT CURRENT DESIGN LEVEL / Full Cross-component Closure NOT CLOSED
RCP-17 Agent Trial contribution → CLOSED AT CURRENT DESIGN LEVEL / Full Closure NOT CLOSED
RCP-19 Agent Applied configuration contribution → CLOSED AT CURRENT DESIGN LEVEL / S9 Desired authority preserved
RCP-20 AG-R01 Agent source-owner recovery/reconciliation contribution → CLOSED AT CURRENT DESIGN LEVEL / Full Cross-component Closure NOT CLOSED
RCP-22 A1-A4 diagnostics/provenance contribution → COMPLETE AT CURRENT BATCH DESIGN LEVEL / A5-A6 NOT DESIGNED / Full Cross-component Closure NOT CLOSED
RCP-24 Agent receiving/applicability expectation → CLOSED AT CURRENT DESIGN LEVEL / Full Closure NOT CLOSED
RCP-04 / RCP-07 / RCP-08 → accepted Node source semantics consumed only / NOT reopened
RCP-12 → bounded consumer/correlation expectation only / AG-R04 owner-source side remains A6
RCP-11 → NOT DESIGNED / future A5
```

No new cross-component RCP is created; total remains `24`.

Named intra-component pressure:

```text
Agent Harness Internal Stable Contract Pressure
→ SYNTHESIZED
→ A2 ↔ A3 ↔ A4
→ consumes A1 Definition / Revision semantics
→ no new RCP ID
```

## Recovery / Checkpoint Baseline

```text
Harness Checkpoint Evidence
→ A2 source-owned continuation evidence
```

Permanent:

```text
Checkpoint != Canonical Agent Definition
Checkpoint != Canonical Product State
Checkpoint != external factual SoT
Recovery Participation != Source Recovery Authority
Evidence Exchange != Source Fact Transfer
Latest Timestamp != Canonical Winner
Recovery != Original Fact Rewrite
Replay != Retroactive Authorization
```

RT-R04 retains recovery/reconciliation coordination authority.

## Accepted DAD

```text
CID-AG-B1-DAD-001..022 → GLOBAL_ACCEPTED
```

```text
Misclassified MDE → 0
New MDE → 0
Open MDE → 0
Unpersisted Owner Decision → 0
```

## Foundation / Technology-neutrality

```text
Mandatory Missing Shared Foundation Semantic → NONE_FOUND
Implementation Leakage → 0
```

No Agent framework, provider SDK, routing/fallback algorithm, context/memory algorithm, checkpoint persistence, queue/broker/scheduler/workflow engine, DB/event-store, concrete API/wire/schema, process/thread/coroutine/container/deployment topology or physical identifier format is accepted by Batch 1.

## Current Governance Boundary

```text
Current Authorized Phase → NONE
Authorization Scope → NONE

A5 Internal Design → NOT AUTHORIZED
A6 Internal Design → NOT AUTHORIZED
ns_agent Batch 2 → NOT AUTHORIZED
ns_web Component Internal Design → NOT AUTHORIZED
System-level SDK Detailed Design → NOT AUTHORIZED
Design-to-Implementation Readiness → NOT AUTHORIZED
Implementation Planning / IWP / Coding → NOT AUTHORIZED
```

Unique next legal action after the Batch-1 Global Acceptance State seal:

```text
Fresh Repository recovery
→ perform post-Batch-1 ns_agent Component Internal Design remaining-pressure / exhaustion / Batch-2 entry-readiness assessment
→ do not authorize A5/A6 automatically from this acceptance
```
