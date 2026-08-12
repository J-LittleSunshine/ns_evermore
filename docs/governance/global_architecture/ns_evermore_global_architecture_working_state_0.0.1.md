# ns_evermore Global Architecture Working State

- **Status:** `WORKING_CHECKPOINT / GAC-EPOCH-0019`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Acceptance State:** `NOT_NORMATIVE`

## Current Checkpoint

```text
Current Global State Epoch
GAC-EPOCH-0019

Architecture Constraint Derivation
GLOBAL_CLOSED / COMPLETE

Project Architecture Synthesis
GLOBAL_CLOSED / COMPLETE

Current Project Architecture
docs/ns_evermore_project_architecture_0.0.3.md
→ GLOBAL_ACCEPTED / NORMATIVE / CURRENT

Accepted Constraint Baseline
NSE-001..017 / Index 0.0.5

Current Decision Registry
0.0.7

Accepted Project Architecture DAD Baseline
Z2-DAD-001..041

Owner MDE Baseline
Z2-MDE-001..017 / OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED

Open MDE
0

Unpersisted Owner Decision
0

Blocking Item
NONE

Known Drift
NONE
```

## Current Project Owner Capability Clarifications

The following capability requirements are `OWNER_CAPABILITY_DECIDED / PERSISTED / GAC_RECOGNIZED` through Decision Registry `0.0.7`:

### Agent-to-Node Delegation

```text
ns_agent
→ required to delegate applicable executable work / task intent to ns_node

ns_node
→ required to execute applicable delegated work inside its accepted local-execution responsibility
```

No Automation/Policy/Artifact/Admission/Agent authority transfer is implied. Runtime/contract/transport mechanics remain later design.

### ns_server Server-local Background Work

```text
ns_server
→ required server-local background work capability
→ long-running work
→ time-triggered / scheduled work
→ continuously available background execution facility
```

The Owner's product intent includes resident background execution, but concrete process-pool/worker/scheduler/queue topology is not frozen in this capability-discovery Batch. Server-local work must not replace `ns_runtime` cross-component scheduling/dispatch responsibility.

### Automation Dual Authoring Surfaces

```text
Automation intended for applicable ns_node execution
→ source-code / SDK authoring REQUIRED
→ visual Web drag-and-drop authoring REQUIRED
```

Accepted ownership remains:

```text
Automation Semantic Authority / Canonical Definition SoT → ns_server
Visual Builder / Management → ns_web
Source Development Surface → System-level SDK / Development Surface
Applicable Local Execution → ns_node
```

Different authoring surfaces must converge on the same governed Automation semantics and cannot bypass Artifact / Admission governance.

## Current Authorized Phase

```text
NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1
```

Refined Authorization Scope:

```text
FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY
/ BATCH_1
/ COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT
```

## Batch 1 Purpose

Batch 1 is deliberately a **capability-discovery stage before normative internal-boundary synthesis**.

It must answer:

```text
What capabilities do the five Product Components actually need?
What cross-component common capabilities are probably required?
What capability gaps has the Project Owner not yet explicitly thought of?
Which items are inherited/derivable/Owner decisions/deferred/non-goals?
```

It must actively discover candidate capabilities rather than merely restating the current Project Architecture.

## A. Five-component Capability Pressure Scan

For each:

```text
ns_server
ns_runtime
ns_node
ns_agent
ns_web
```

construct a broad capability inventory grounded in:

```text
Constitution
NSE-001..017
Project Architecture 0.0.3
Z2-DAD-001..041
Z2-MDE-001..017
Decision Registry 0.0.7 Owner Capability Clarifications
```

Pressure-scan the component from multiple operating perspectives, including as applicable:

```text
definition / authoring
runtime / execution
administration / operations
offline / degraded
recovery / reconciliation
security / trust / principal
configuration / lifecycle
extension / re-delivery
compatibility / migration / conformance
observability / diagnostics
integration / external systems
SDK / development experience
```

The output must identify likely missing product capabilities, not internal modules.

## B. Capability Classification

Every item uses exactly:

```text
INHERITED_REQUIRED
DERIVED_REQUIRED
OWNER_DECISION_REQUIRED
DEFERRED
NON_GOAL
```

Rules:

```text
INHERITED_REQUIRED
→ already fixed by accepted Repository authority or persisted Owner capability clarification
→ do not ask Owner again

DERIVED_REQUIRED
→ supporting capability necessarily implied by accepted semantics
→ may be derived when it does not expand material product scope or cross MDE boundaries

OWNER_DECISION_REQUIRED
→ product-significant capability not yet frozen
→ return to Project Owner one material question at a time

DEFERRED
→ intentionally not decided in this scope; named later authority required where material

NON_GOAL
→ explicitly outside component/product capability scope
```

## C. Cross-component Common Capability Discovery

Batch 1 may identify and classify cross-component common capability candidates required by two or more Product Components.

This is **not Shared Foundation Architecture** and does not finalize Foundation capability identity.

Known inherited/common pressure includes:

```text
HTTP/client capability
cache/client capability
storage/client capability
configuration loading capability
```

The Batch must also assess real cross-component need for candidate pressure areas such as:

```text
logging / structured diagnostics
telemetry / observability primitives
time / temporal primitives
serialization / representation primitives
cryptography / secret-reference primitives
database utility primitives
event / notification utility primitives
health / lifecycle reporting primitives
operation / correlation / trace context primitives
conformance / compatibility support primitives
```

These are candidate areas only. Do not assume they belong in Shared Foundation.

For each common candidate determine:

```text
actual consuming Product Components
reusability evidence
stable-boundary plausibility
provider-neutrality requirement
authority / SoT implications
component-local alternative
future Shared Foundation Architecture candidacy
Owner decision need if product-significant
```

## D. Owner Capability Checkpoint

The session should first derive a candidate inventory, then surface only genuinely product-significant missing capabilities to the Project Owner.

For each `OWNER_DECISION_REQUIRED` item:

```text
one material question at a time
A / B / C durable options
recommendation
rationale
benefits
costs
long-term impact
```

Persist the Owner result before dependent capability synthesis proceeds.

Do not ask again about inherited capabilities or the three capability clarifications already persisted in Registry `0.0.7`.

## E. Candidate Capability Baseline

Produce one coherent candidate baseline covering:

```text
all five Product Components
cross-component capability dependencies
common capability candidates
capability overlap/gap analysis
Owner decisions made in this Batch
explicit NON_GOAL / DEFERRED items
```

The candidate baseline is intended to become the normative upstream input to **Z3 Batch 2 internal-boundary synthesis** only after independent GAC acceptance and separate authorization.

## Strict Forbidden Scope

Z3 Batch 1 MUST NOT begin or decide:

```text
normative Five-component Internal Architecture Boundary decomposition
Component Internal Design
internal module decomposition
Django app decomposition
Python package layout
Vue internal component/folder architecture
class/service/repository/adapter design
Runtime Responsibility Architecture
Runtime Role taxonomy
process/service/worker/container/deployment topology
concrete ns_server process-pool / worker implementation
actual delegation Contract/API/schema/wire/message design
concrete Automation SDK API / visual DSL / package representation
database/storage topology
Shared Foundation Architecture or detailed Foundation capability baseline
Foundation Contract / Module / Provider Design
SDK binding/package/generator realization
Implementation Planning
IWP
Coding
```

Capability discovery may identify future pressure for these areas but cannot design them.

## Exit Gate

Completion requires:

```text
Five Product Component inventories → COMPLETE
Cross-component common capability scan → COMPLETE
All capability items → CLASSIFIED
Known Owner capability clarifications → CONSUMED
OWNER_DECISION_REQUIRED items → RESOLVED / PERSISTED or 0
Unclassified product-significant capability → 0
Capability overlap/gap blocking Batch 2 → 0
Common capability candidate ambiguity → explicitly classified/deferred
Open MDE → 0
Unpersisted Owner Decision → 0
Authority/SoT violation introduced → 0
Project Architecture violation → 0
Internal-boundary design leakage → 0
Runtime Architecture leakage → 0
Shared Foundation detailed-design leakage → 0
Implementation-defined Escape → 0
Unexpected Drift → NONE
Unauthorized Progression → NONE
```

Producing-session maximum:

```text
NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
→ STOP
→ RETURN TO GAC
```

## Planned Continuation — NOT AUTHORIZED YET

Project Owner planning intent:

```text
After Z3 Batch 1 capability baseline is independently accepted
→ Z3 Batch 2 should continue Five-component Internal Architecture Boundary synthesis
```

This is planning intent only. Batch 2 requires a separate GAC remaining-pressure/acceptance decision and explicit authorization.

## Unique Next Legal Action

```text
Start one bounded Z3 Batch 1 session for:
COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT

Derive a broad five-component/common-capability inventory,
identify likely missing product functions,
perform Owner Capability Checkpoint where required,
and stop before internal-boundary synthesis.
```
