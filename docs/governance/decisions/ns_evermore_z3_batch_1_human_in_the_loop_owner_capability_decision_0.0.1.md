# NGRP-001 Phase Z3 / Batch 1 — Governed Human-in-the-loop Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should Automation and AI Agent execution both natively support governed Human-in-the-loop participation, or should human participation remain outside one or both domains and be composed through Business Application or other external workflow logic?

This is product-significant because it determines whether execution may natively request and consume governed human input/review/choice/confirmation/correction before continuing, rather than forcing each application to recreate human-intervention lifecycle semantics.

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

The decision does not move or merge Policy Authority, Formal Artifact Acceptance Authority, Formal Execution Admission Authority, Automation Semantic Authority, Agent Semantic Authority, Source of Truth, Actual-state Ownership, or Platform Trust Authority.

## 3. Alternatives Presented

### Option A — No native HITL

Automation and Agent execution remain machine-only. Human participation is implemented externally through Business Application or other composition.

### Option B — Native governed HITL in both Automation and Agent

Both domains support native product semantics for applicable human participation, including requesting human input, review, choice, confirmation or correction and then continuing, branching or terminating according to later-designed governed lifecycle semantics.

### Option C — Native HITL only in Automation

Automation owns native human-intervention capability; Agent requires Automation or Business Application composition for human participation.

## 4. Recommendation Presented

`B — Native governed HITL in both Automation and Agent`.

Rationale:

- enterprise Automation and Agent workflows commonly require human review, input, exception handling and risk confirmation;
- `UNKNOWN`, `INDETERMINATE`, `CONFLICTING` and similar accepted system states need a legitimate human-handoff path in addition to automatic continuation or failure;
- keeping native HITL in both first-class domains avoids subordinating Agent execution to Automation merely to interact with a human;
- the capability can remain compatible with offline/private deployment and accepted authority separation.

## 5. Project Owner Decision

```text
Selected Option
→ B

Automation Governed Human-in-the-loop
→ REQUIRED

AI Agent Governed Human-in-the-loop
→ REQUIRED
```

## 6. Normative Capability Consequences

The Z3 Batch 1 capability baseline may consume:

```text
Automation execution
→ MAY require governed human input / review / choice / confirmation / correction
→ MAY pause or wait where later lifecycle design permits
→ MAY continue / branch / terminate after governed human response

AI Agent execution
→ MAY require governed human input / review / choice / confirmation / correction
→ MAY continue / branch / terminate after governed human response
```

Permanent non-equivalences:

```text
Human Approval != Unified Policy Authority
Human Confirmation != Formal Execution Admission Authority
Human Review != Formal Artifact Acceptance Authority
Human Input != Semantic Authority Transfer
Operator UI != Human-task Source of Truth automatically
Successful human interaction != Retroactive proof of prior authorization
```

## 7. Cross-component Non-implications

This capability decision does not freeze internal responsibility decomposition, but preserves the following accepted architecture:

```text
Automation Definition / Workflow Semantic Authority
→ ns_server

AI Agent Definition / Semantic Authority
→ ns_agent

Formal Artifact Acceptance Authority
→ ns_server

Formal Execution Admission Authority
→ ns_server

ns_web
→ human-facing UI / governance / control-plane surfaces
```

Any later participation by `ns_web`, `ns_runtime`, `ns_node`, or other components in assignment, presentation, waiting, resume, local attended execution, notification or recovery must conform to separately authorized Five-component Internal Architecture / Runtime Responsibility / Component Internal Design work.

## 8. Explicit Deferred Mechanics

This Owner capability decision does **not** decide:

```text
human-task identity / schema
assignment model
approval model
principal binding
human-response representation
wait / suspend / resume state machine
timeout semantics
escalation semantics
notification mechanism
offline queueing / synchronization
recovery algorithm
runtime role / process / worker topology
API / message / transport
storage / database model
```

Named later authorities:

```text
Five-component Internal Architecture Boundary Synthesis
Runtime Responsibility Architecture
Component Internal Design
Foundation / Contract / Provider design where later admitted
Project Owner / MDE for any material Authority / Trust / Security / fail-open-fail-closed commitment
```

## 9. Offline / Private Deployment Consequence

Governed HITL must remain compatible with private/offline operation where the underlying execution scenario is supported. No mandatory public SaaS approval service, public identity service or vendor control plane may be required for core correctness.

Offline/degraded human participation does not create local Policy, Admission, Artifact or Trust Authority.

## 10. Compatibility / Recovery Consequence

Future lifecycle design must preserve enough provenance and revision context to determine what human response applied to which bounded execution context. Missing, stale, conflicting or unverifiable human-response state remains explicit and cannot be silently treated as approval or denial by implementation convention.

## 11. Preserved Invariants

This decision preserves:

- exactly five Product Components;
- Business Application / Automation / AI Agent / Data-Knowledge first-class non-subordination;
- Definition / Artifact / Admission / Runtime separation;
- `Automation Semantic Authority → ns_server`;
- `AI Agent Semantic Authority → ns_agent`;
- `Formal Artifact Acceptance Authority → ns_server`;
- `Formal Execution Admission Authority → ns_server`;
- Tenant / Organization / IAM / Policy / Trust invariants;
- Runtime Actual-state per bounded semantic partition;
- offline/private governance invariance;
- no premature Runtime Architecture or Component Internal Design.

## 12. Revalidation Trigger

Revalidate if the Project Owner later removes native HITL from Automation or Agent, makes one domain dependent on the other for all human participation, or materially changes accepted Authority/Trust/Admission relationships through human action semantics.

## 13. Bounded-session Authority Limit

This evidence records one Project Owner capability decision inside Z3 Batch 1.

It does not constitute GAC Global Acceptance, advance GAC Epoch, authorize Z3 Batch 2, start Five-component Internal Architecture Boundary synthesis, start Runtime Responsibility Architecture, start Component Internal Design, start Shared Foundation Architecture, or authorize Implementation Planning / IWP / coding.
