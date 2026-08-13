# NGRP-001 Phase Z3 / Batch 1 — Governed Human-in-the-loop Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should Automation and AI Agent execution both natively support governed Human-in-the-loop participation, or should human participation remain outside one or both domains and be composed through Business Application or other external workflow logic?

This is product-significant because it determines whether execution may natively request and consume governed human input/review/choice/confirmation/correction before continuing, rather than forcing each application to recreate human-intervention lifecycle semantics.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

The capability is material, but the selected semantics do not move or merge Policy Authority, Formal Artifact Acceptance Authority, Formal Execution Admission Authority, Automation Semantic Authority, Agent Semantic Authority, Source of Truth, Actual-state Ownership or Platform Trust Authority. Human action remains participation evidence, not automatic governance authority.

## 3. Durable Mutually-exclusive Alternatives

### A — No native HITL

Automation and Agent execution remain machine-only. Human participation is implemented externally through Business Application or other composition.

### B — Native governed HITL in both Automation and Agent

Both domains support native product semantics for applicable human input, review, choice, confirmation or correction and may later wait/continue/branch/terminate under separately designed governed lifecycle semantics.

### C — Native HITL only in Automation

Automation owns native human-intervention capability; Agent requires Automation or Business Application composition for human participation.

## 4. Recommendation Presented

```text
Recommendation
→ B — Native governed HITL in both Automation and Agent
```

### Recommendation Rationale

Enterprise Automation and Agent workflows commonly need human review, input, exception handling and risk confirmation. Accepted `UNKNOWN / INDETERMINATE / CONFLICTING` conditions require a legitimate human-handoff path in addition to automatic continuation or failure. Option B preserves both Automation and Agent as first-class domains and avoids subordinating all Agent human interaction to Automation.

## 5. Tradeoffs and Impact

**Benefits**
- native human review/input/correction/exception handling in both first-class execution domains;
- supports safer handling of uncertain or high-context execution states;
- avoids repeated application-specific human-intervention lifecycle glue.

**Costs**
- later architecture must define provenance, principal binding, lifecycle/resume and recovery semantics for human participation;
- operational and UI surfaces must expose enough execution context for meaningful human action.

**Risks / Complexity**
- stale, conflicting or mis-bound human responses could be misapplied without strong provenance;
- timeout, session loss and offline/degraded recovery create lifecycle complexity;
- human confirmation could be incorrectly conflated with Policy, Artifact Acceptance or Execution Admission if boundaries are not preserved.

**Long-term Impact**
- `ns_evermore` supports a native human-machine execution model rather than machine-only workflows;
- Agent remains independently capable of human interaction rather than being structurally subordinate to Automation.

**Compatibility / Migration Impact**
- future lifecycle revisions must preserve which human response applies to which execution/revision context;
- missing/stale/conflicting/unverifiable responses remain explicit rather than silently interpreted as approval or denial.

**Offline / Private Deployment Impact**
- applicable HITL must remain usable in private/offline scenarios without mandatory public approval/identity SaaS or vendor control plane;
- offline human participation does not create local Policy/Admission/Artifact/Trust authority.

**Cross-component Impact**
- Automation semantics remain under `ns_server`; Agent semantics remain under `ns_agent`;
- `ns_web` may provide human-facing interaction surfaces under later authorized design;
- `ns_runtime`/`ns_node` may later participate in wait/resume/local-attended execution mechanics without acquiring semantic authority.

## 6. Project Owner Selected Result

```text
Selected Option
→ B

Automation Governed Human-in-the-loop
→ REQUIRED

AI Agent Governed Human-in-the-loop
→ REQUIRED
```

## 7. Normative Capability Consequence

Automation and Agent execution may require governed human input/review/choice/confirmation/correction and may continue, branch or terminate after a governed human response according to later-designed lifecycle semantics.

## 8. Authority / SoT / Actual-state Preservation

```text
Automation Semantic Authority
→ ns_server / UNCHANGED

AI Agent Semantic Authority
→ ns_agent / UNCHANGED

Artifact Acceptance Authority
→ ns_server / UNCHANGED

Execution Admission Authority
→ ns_server / UNCHANGED

Runtime Actual-state Ownership
→ unchanged per bounded semantic partition
```

## 9. Explicit Non-implications

```text
Human Approval != Unified Policy Authority
Human Confirmation != Execution Admission Authority
Human Review != Artifact Acceptance Authority
Human Input != Semantic Authority Transfer
Operator UI != Human-task SoT automatically
Successful human interaction != retroactive proof of authorization
```

## 10. Deferred Mechanics / Named Later Authority

Not decided here: human-task identity/schema, assignment/approval model, principal binding, response representation, wait/suspend/resume state machine, timeout/escalation, notifications, offline synchronization, recovery algorithm, runtime role/process/worker topology, API/message/transport or storage model.

These remain for separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture, Component Internal Design and later Contract/Foundation/Provider work if admitted. Material Authority/Trust/Security/fail-open-fail-closed changes return to Project Owner/MDE.

## 11. Revalidation Trigger

Revalidate if the Project Owner removes native HITL from Automation or Agent, makes one domain dependent on the other for all human participation, or materially changes accepted Authority/Trust/Admission relationships through human-action semantics.

## 12. Bounded-session Authority Limit

This evidence correction preserves the already selected Owner result only. It does not claim Global Acceptance, advance GAC state, authorize later batches or enter downstream architecture/design/implementation work.
