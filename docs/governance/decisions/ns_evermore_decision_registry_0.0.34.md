# ns_evermore Decision Registry — Current Revision

- Version: `0.0.34`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.33`

All accepted normative decisions and baselines in Decision Registry `0.0.33` remain in force unless explicitly refined below.

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
ns_agent Component Internal Design / Batch 2 → GLOBAL_ACCEPTED
Accepted ns_agent Boundaries → A1 / A2 / A3 / A4 / A5 / A6
Accepted ns_agent Boundary Coverage → 6 / 6 / 100%
Accepted ns_agent Internal Responsibility Count → 54
Remaining accepted ns_agent boundaries without Component Internal Design → NONE
ns_agent Internal Design Exhaustion → NOT YET REASSESSED AFTER BATCH 2 ACCEPTANCE
ns_agent Component Internal Design Global Closure → NOT DECLARED

ns_web Component Internal Design → NOT AUTHORIZED
```

Batch-2 Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_ns_agent_internal_design_batch_2_global_acceptance_0.0.1.md`

## Accepted ns_agent Batch-2 Internal Architecture

### A5 — Native Multi-Agent Composition

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

### A6 — Governed Cross-domain Delegation & Automation Participation

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

## Authority / SoT / Actual-state Preservation

```text
A1 → Agent semantic/canonical definition authority
A2 / AG-R01 → each Agent runtime Actual-state
A3 / AG-R02 → provider/model bounded observations
A4 → Tool/Knowledge consumption semantics
A5 / AG-R03 → composition coordination/provenance only
A6 / AG-R04 → Agent-side cross-domain participation/provenance only
S6 → Automation semantics / canonical definition / applicable runtime semantic state
S8 → Artifact Acceptance / Execution Admission
RT-R02 → Routing / Scheduling / Dispatch
RT-R03 → Cross-component continuation / delegation coordination
RT-R04 → Recovery / Reconciliation Coordination
N1 / N2 / N3 → Node Readiness / Attempt / Effect
```

Permanent:

```text
Multi-Agent Composition != Separate Multi-Agent Authority
AG-R03 Composition Coordination != merged AG-R01 Actual-state
Agent A Invokes Agent B != Authority Transfer
Multi-Agent != Automation Workflow Authority
Composition Context Contribution != shared factual SoT
Agent Delegation != Node Attempt
Agent Delegation != Node Effect Ownership
Agent Invokes Automation != Automation Authority
Agent Authors Candidate Automation != Accepted Automation
Candidate Possession != Artifact Acceptance
Agent Intent != Execution Admission
Dispatch != Attempt
Attempt != Effect
```

## NSH Completion Across A1-A6

```text
NSH → NAMED INTERNAL ARCHITECTURE CONCEPT INSIDE EXISTING ns_agent BOUNDARIES
A1-A4 → accepted NSH core
A5 → accepted Multi-Agent composition extension seam
A6 → accepted governed cross-domain delegation / Automation participation extension seam
A7 / AG-R05 → NOT CREATED
```

Harness evolution law from Registry 0.0.33 remains normative and unchanged.

## Stable-contract Qualification

```text
RCP-11 A5/AG-R03 composition/provenance owner-side + A2/AG-R01 participant integration → COMPLETE AT CURRENT DESIGN LEVEL / Full Cross-component Closure NOT CLAIMED
RCP-12 A6/AG-R04 Agent Delegation owner/source-side → COMPLETE AT CURRENT DESIGN LEVEL / Full Cross-component Closure NOT CLAIMED
RCP-20 A5/A6 own-fact recovery/reconciliation participation → COMPLETE AT CURRENT DESIGN LEVEL / RT-R04 preserved / Full Cross-component Closure NOT CLAIMED
RCP-22 all-six-boundary ns_agent fact-owner diagnostics/provenance contribution → COMPLETE AT CURRENT NS_AGENT DESIGN LEVEL / Full Cross-component Closure NOT CLAIMED
RCP-02 → Admission applicability/reference only / S8 preserved
RCP-03 / RCP-05 / RCP-06 → accepted Runtime semantics consumed only
RCP-04 / RCP-07 / RCP-08 → accepted Node semantics consumed only
RCP-13 / RCP-15 → accepted Automation semantics consumed only
RCP-16 → A5/A6 bounded correlation only / A2 source semantics preserved
RCP-17 → A5/A6 Trial contribution only
RCP-19 → A5/A6 genuinely owned Applied facts only / S9 Desired preserved
RCP-24 → A5/A6 receiving/applicability/correlation only where material
```

No new cross-component RCP is created; total remains `24`.

## Accepted DAD / Review

```text
CID-AG-B2-DAD-001..022 → GLOBAL_ACCEPTED
Review Gates → 31 PASS / 0 FAIL / 0 BLOCKED
Misclassified MDE → 0
New MDE → 0
Open MDE → 0
Unpersisted Owner Decision → 0
Hard Internal SDD Graph → ACYCLIC
Authority Cycle → NONE
Circular Actual-state Ownership → NONE
Mandatory Missing Shared Foundation Semantic → NONE_FOUND
Implementation Leakage → 0
```

## Important Non-implication

```text
6 / 6 / 100% accepted boundary coverage
!= ns_agent Internal Design Exhaustion SATISFIED
!= ns_agent Component Internal Design GLOBAL_CLOSED / COMPLETE
```

A separate post-Batch-2 remaining-pressure / exhaustion / global-closure assessment is required.

## Current Governance Boundary

```text
Current Authorized Phase → NONE
Authorization Scope → NONE
ns_agent Internal Design Exhaustion SATISFIED → NOT DECLARED
ns_agent Component Internal Design Global Closure → NOT DECLARED
ns_web Component Internal Design → NOT AUTHORIZED
System-level SDK Detailed Design → NOT AUTHORIZED
Design-to-Implementation Readiness → NOT AUTHORIZED
Implementation Planning / IWP / Coding → NOT AUTHORIZED
```

Unique next legal action after Batch-2 Global Acceptance seal:

```text
Fresh Repository recovery
→ perform post-Batch-2 ns_agent Component Internal Design remaining-pressure / exhaustion / global-closure assessment
→ do not authorize ns_web automatically from this acceptance
```
