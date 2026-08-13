# NGRP-001 Phase Z3 / Batch 2 — Governed Pre-production Trial Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **MDE Classification:** `NO`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Decision Predecessor HEAD:** `29a89efa593c35d3aa8be6c9ab5f1d60dcab2aa4`
- **Current Global State at Decision:** `GAC-EPOCH-0022`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

For the four already-required complete authoring domains:

```text
Business Application
Automation
Native AI Agent
Data / Knowledge / Foundational ETL
```

what product-level pre-production interaction capability SHALL exist beyond semantic validation, conformance checking and compatibility checking?

The unresolved choice is whether ns_evermore provides validation only, provides a governed pre-production trial capability with domain-appropriate bounded trial modes, or promises a universal fully isolated simulation/sandbox for every production-capable definition.

---

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

### Why Product-significant

The choice materially affects:

```text
Developer feedback loop
Delivery workflow
Customer secondary development
Low-code / Pro-code authoring
Debuggability
Pre-production safety expectations
Production promotion workflow
Offline/private delivery
Cross-domain authoring consistency
```

Static validation answers whether a definition is semantically or contractually acceptable. It does not by itself answer how the authored behavior operates against representative inputs, providers, tools, data, integrations or execution context.

### Why Not MDE

The decision establishes a product capability and interaction contract but does not move or redefine:

```text
Definition Semantic Authority
Canonical Definition SoT
Policy Semantic Authority
Artifact Acceptance Authority
Execution Admission Authority
Runtime Actual-state Ownership
Trust Authority
Tenant Authority
```

No universal offline fail-open/fail-closed policy, stable protocol/format choice, or authority transfer is introduced by selecting the capability. Therefore the capability decision is material but not MDE-class under the current governance baseline.

---

## 3. Accepted Upstream Preserved

This decision consumes without reopening:

```text
Complete source / SDK authoring
→ REQUIRED for all four authoring domains

Complete visual authoring
→ REQUIRED for all four authoring domains

Bidirectional semantic interoperability between source and visual authoring
→ REQUIRED

Lossless representation round-trip
→ NOT REQUIRED

Validation / conformance / compatibility feedback
→ REQUIRED

Definition
!= Artifact Acceptance
!= Execution Admission
!= Runtime Attempt
```

The decision also preserves offline/private correctness and the existing authority topology.

---

## 4. Options Considered

### Option A — Validation Only

Product-level guarantee stops at semantic validation, conformance and compatibility checking. Preview, test execution, dry-run, trial execution and simulation remain domain-local future choices.

#### Benefits

- Lowest immediate product and architecture complexity.
- No shared trial lifecycle commitment.
- No requirement to characterize trial effects across domains.

#### Costs

- Incomplete authoring feedback loop.
- Delivery and customer secondary development are likely to create domain-specific test runners and test semantics.
- Agent, Automation, Business Application and ETL trial behavior may diverge materially.

#### Risks / Complexity

Long-term semantic fragmentation is likely, especially around what `test`, `dry-run`, `preview` and `simulation` mean and whether they can create effects.

#### Long-term Impact

Authoring is first-class but pre-production behavioral trial is not a coherent product capability.

#### Compatibility / Migration

A later unified trial model would need to absorb existing domain-local semantics and compatibility expectations.

#### Offline / Private

Lowest additional pressure.

#### Cross-component Impact

Lowest cross-component pressure.

---

### Option B — Governed Pre-production Trial with Domain-appropriate Bounded Trial Modes

Establish a product-level `GOVERNED_PRE_PRODUCTION_TRIAL` capability. Every complete authoring domain SHALL support an applicable governed pre-production behavioral trial path, but the product does not require the same physical execution mechanism or trial mode for every domain.

Illustrative domain-appropriate forms MAY include:

```text
Business Application
→ preview / bounded test interaction

Automation
→ test execution / dry-run where semantically supportable

Native AI Agent
→ governed test interaction / evaluation run

Data / Knowledge / Foundational ETL
→ sample-data test / bounded trial execution
```

These examples do not freeze terminology, UI design, runtime placement, schema or implementation.

#### Required Semantic Separation

```text
Definition Valid
!= Trial Successful

Trial Successful
!= Artifact Accepted

Trial Successful
!= Production Execution Admitted

Trial Execution
!= Production Execution

Trial Success
!= Production Success Guarantee

Dry-run
!= No Effect unless the applicable domain explicitly guarantees that property
```

A trial capability SHALL make its applicable execution/effect boundary explicit enough that users, operators and developers are not led to infer stronger isolation or reversibility than actually exists.

#### Benefits

- Creates a complete authoring feedback loop across all four first-class domains.
- Supports both source/SDK and visual authoring without creating separate testing semantics.
- Improves debugging and delivery safety before production governance/admission.
- Reduces pressure for customer projects to invent inconsistent test lifecycle concepts.
- Fits the already-selected semantic interoperability model between authoring surfaces.

#### Costs

Later architecture/design must establish stable semantics for matters such as:

```text
trial identity
definition revision under trial
trial context/environment identity
effect boundary
test input provenance
trial result provenance
trial-vs-production distinction
diagnostics and trace correlation
```

This decision does not define their concrete representation.

#### Risks / Complexity

Primary risks are semantic overclaiming:

```text
"Test"
→ incorrectly interpreted as effect-free

Trial Success
→ incorrectly interpreted as production acceptance or production success
```

Conformance must preserve those separations.

#### Long-term Impact

The platform gains a coherent lifecycle:

```text
Author
→ Validate
→ Trial
→ Inspect Result / Diagnostics
→ Revise
→ Govern
→ Accepted Artifact
→ Admission
→ Production Runtime Attempt
```

without promising deterministic or fully isolated simulation.

#### Compatibility / Migration

Trial records and results should remain attributable to the applicable definition revision and trial context. This decision does not require historical trials to remain forever replayable and does not create deterministic replay as a compatibility promise.

#### Offline / Private

Applicable trial capability SHALL remain available in private/offline deployments without requiring mandatory public SaaS, public model providers, public sandbox infrastructure or cloud test runners as core correctness dependencies.

Where a trial depends on a currently unavailable capability/provider/node, the system must expose the applicable bounded uncertainty/unavailability rather than fabricate success.

#### Cross-component Impact

The capability creates later boundary pressure across applicable combinations of:

```text
ns_web
System-level SDK
ns_server-owned authoring domains
ns_agent-owned Agent domain
ns_node where local execution/effect access is applicable
ns_runtime where later architecture assigns relevant coordination
```

No component allocation is decided here.

---

### Option C — Universal Fully Isolated Simulation / Sandbox

Every production-capable definition in all four authoring domains would be guaranteed an isolated simulation/sandbox with no real local/external effects and sufficiently representative behavior.

#### Benefits

- Strongest apparent safety and user confidence.
- Highly uniform testing mental model.

#### Costs

Extremely high for external APIs, desktop/browser automation, file/device operations, live enterprise systems, AI providers and other effect-bearing integrations.

#### Risks / Complexity

Creates an unsound equivalence pressure:

```text
Sandbox Success
→ Production Will Behave The Same
```

which cannot generally be guaranteed for real providers, desktops, devices, networks or external Systems of Record.

#### Long-term Impact

Would permanently bind future capability evolution to simulation, mocking, isolation and environmental equivalence requirements.

#### Compatibility / Migration

Every future production capability would need a compliant sandbox equivalent or become an exception.

#### Offline / Private

The entire simulation infrastructure would itself need private/offline realizability.

#### Cross-component Impact

Highest cross-component and future implementation pressure.

---

## 5. Recommendation Presented to Project Owner

```text
Recommendation
→ Option B
→ Governed Pre-production Trial with domain-appropriate, explicitly bounded trial modes
```

### Recommendation Rationale

The product already requires complete source and visual authoring, validation/conformance/compatibility feedback, customer secondary development and offline/private operation. A governed trial capability completes that authoring workflow without making the false promise that every real-world integration can be simulated safely and equivalently.

The recommended durable rule is:

> A complete authoring domain SHALL provide an applicable governed pre-production behavioral trial path with explicit context and effect semantics, while trial success remains separate from formal acceptance, production admission and production outcome.

---

## 6. Project Owner Selection

Project Owner selected:

```text
B
```

Selected Result:

```text
GOVERNED_PRE_PRODUCTION_TRIAL
→ REQUIRED

APPLICABILITY
→ ALL FOUR COMPLETE AUTHORING DOMAINS

TRIAL MODE
→ DOMAIN_APPROPRIATE / EXPLICITLY_BOUNDED

UNIVERSAL_FULLY_ISOLATED_SIMULATION
→ NOT REQUIRED
```

---

## 7. Normative Capability Consequences

For subsequent authorized Z3 capability discovery and later boundary synthesis, the following SHALL be treated as the selected Owner capability baseline:

1. Each of the four complete authoring domains SHALL expose an applicable governed pre-production behavioral trial capability.
2. Source/SDK and visual authoring surfaces SHALL consume semantically consistent trial capability for the same governed domain; they SHALL NOT invent conflicting lifecycle meaning.
3. Trial mode MAY legitimately differ by domain and by capability/effect boundary.
4. Trial activity SHALL be distinguishable from production activity.
5. Trial SHALL remain attributable to the relevant definition revision and applicable trial context.
6. Trial effects, isolation guarantees and limitations SHALL be represented explicitly enough to prevent silent semantic escalation.
7. `dry-run`, `preview`, `test`, `evaluation`, `sandbox` or similar labels SHALL NOT acquire stronger semantics merely from presentation terminology; any no-effect/isolation guarantee must be explicitly supported by the applicable capability.
8. Trial success SHALL NOT imply Artifact Acceptance, Execution Admission, Policy authorization, production readiness or production success.
9. Applicable diagnostics/provenance for trial activity SHALL remain distinguishable from production evidence while preserving correlation to the tested definition/context.
10. The capability SHALL remain realizable under private/offline deployment constraints without mandatory public infrastructure.

---

## 8. Authority / SoT Preservation

This decision SHALL NOT alter accepted authority or SoT topology.

Preserved explicitly:

```text
Business Application Definition Semantic Authority / Canonical Definition SoT
→ ns_server

Automation Definition / Workflow Semantic Authority / Canonical Definition SoT
→ ns_server

Native AI Agent Definition / Semantic Authority / Canonical Definition SoT
→ ns_agent

Data / Knowledge / Foundational ETL semantic authority
→ remains under its already accepted bounded authority topology

Formal Artifact Acceptance Authority
→ ns_server

Formal Execution Admission Authority
→ ns_server

Runtime Actual-state
→ remains owned per accepted bounded runtime semantic partition

ns_web
→ human-facing authoring / trial interaction projection, not canonical authority

System-level SDK
→ programmatic authoring / trial interaction surface, not canonical authority
```

A trial runner, preview surface, evaluator or test interaction MUST NOT become a competing Definition SoT, Policy Authority, Trust Authority, Artifact Acceptance Authority, Execution Admission Authority or universal Runtime Actual-state Owner.

---

## 9. Explicit Non-implications

This decision does **not** imply:

```text
one universal trial engine
one universal trial runtime
one physical representation for all domains
one universal sandbox
full isolation for every trial
no-effect execution by default
deterministic simulation
deterministic replay
historical trial replay forever
production-equivalent environment
production acceptance based on trial success
execution admission based on trial success
automatic artifact acceptance
one mandatory test DSL
one mandatory test data model
one mandatory provider
one mandatory node topology
one mandatory UI/page design
```

It also does not imply that every capability can support every trial style.

---

## 10. Named Deferrals

The following remain deliberately deferred to separately authorized later work:

```text
trial API / protocol / schema
trial state machine
trial identity representation
trial storage model
trial scheduling/execution topology
trial environment model
sample-data representation
provider/tool mocking strategy
sandbox technology
isolation technology
side-effect interception/virtualization
trial result persistence details
trial diagnostics schema
trial provenance schema
trial retention policy
historical replay mechanics
exact visual UX/page structure
exact SDK methods
exact source language/DSL conventions
component-internal module allocation
runtime responsibility allocation
Shared Foundation contracts/modules/providers
implementation planning
IWP
coding
```

No provider, protocol, transport, format, framework or implementation mechanism is selected by this decision.

---

## 11. Revalidation Triggers

This Owner capability decision SHALL be revalidated if a later accepted authority changes any of the following materially:

```text
complete authoring-domain set
complete dual-authoring commitment
source↔visual semantic interoperability commitment
formal Artifact Acceptance topology
formal Execution Admission topology
runtime Actual-state ownership topology
offline/private correctness requirements
product promise regarding effect-free testing
product promise regarding deterministic simulation/replay
```

A later proposal to require universal isolated simulation or to remove pre-production trial from one of the four complete authoring domains is not a mechanical implementation change and requires explicit governance revalidation.

---

## 12. Bounded Authority / Session Limit

This evidence records only the Project Owner capability decision needed by the authorized Z3 Batch 2 checkpoint.

This document does **not**:

```text
claim Global Acceptance
advance GAC Epoch
authorize Z3 Batch 3
claim capability exhaustion
claim Five-component Internal Architecture readiness
perform Five-component Internal Boundary Synthesis
enter Component Internal Design
enter Runtime Responsibility Architecture
enter Shared Foundation Architecture
enter Foundation Contract / Module / Provider Design
enter Implementation Planning
enter IWP
enter Coding
```

Global acceptance and any next-phase authorization remain exclusively with the Global Architecture Coordinator under the repository governance model.
