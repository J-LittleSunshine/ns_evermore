# NGRP-001 Component Internal Design / ns_server / Batch 2 — Automation Recursive Invocation Owner Decision

- **Decision ID:** `CID-SV-B2-MDE-001`
- **Program / Phase:** `NGRP-001 — Component Internal Design / ns_server / Batch 2`
- **Authorization Scope:** `COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_2 / AUTOMATION_DOMAIN_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `a75ffe680ef3200344944ef5e5f2497d746dff09`
- **Recovered Global State:** `GAC-EPOCH-0046`
- **State Verified Through HEAD:** `4197bcd231c7d11e4f655e41c71004a32e8ffe99`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Status:** `OWNER_DECIDED / PERSISTED / AWAITING_GAC_RECOGNITION`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Question

The accepted Product capability already requires governed reusable Automation-to-Automation composition, but upstream evidence deliberately left recursion and cycle policy unresolved.

The current S6 Component Internal Design must close the distinction among:

```text
cyclic Automation definition dependency
!= recursive Automation-to-Automation invocation
!= runtime recursive continuation
```

The material Owner question is therefore:

> Should Native Automation-to-Automation Composition support recursive invocation as a long-term product capability?

This decision is product-significant because it changes the stable Automation composition capability, authoring semantics, compatibility obligations, historical interpretation, runtime continuation semantics, recovery complexity and cross-surface interoperability obligations.

---

## 2. Classification

```text
Classification
→ MDE
```

Reasons:

1. reusable Automation composition is already an accepted first-class Product capability;
2. recursion materially changes the long-term capability surface rather than merely an implementation technique;
3. recursive invocation would introduce durable compatibility, history, runtime continuation, HITL/retry/recovery and authoring obligations;
4. the current authorization explicitly requires Owner escalation where recursive-composition support is product-significant;
5. no accepted upstream evidence already selects recursion support.

No Authority / SoT / Runtime Actual-state owner is moved by the question itself.

---

## 3. Alternatives Presented

### A — No Native Recursive Automation-to-Automation Invocation

Reusable composition remains supported, but composition relationships that form direct or indirect recursive invocation are not supported product semantics.

```text
Automation A → Automation B
→ SUPPORTED when the governed dependency remains acyclic

Automation A → Automation A
→ UNSUPPORTED

Automation A → Automation B → Automation A
→ UNSUPPORTED
```

This does not prohibit ordinary repeated invocation, retry/re-entry, iteration/loop semantics inside an Automation if separately supported by accepted semantics, or multiple sequential invocations of the same non-ancestor callee. It prohibits only recursive Automation-to-Automation invocation through the composition relationship.

### B — Governed Recursive Automation Invocation

Native Automation composition supports direct/indirect recursion under explicit governed semantics. Later design would be required to close recursive invocation identity, ancestor lineage, recursion applicability/boundedness, continuation state, HITL/retry/recovery interaction, partial/unknown propagation, authoring compatibility and history.

### C — Capability-declared Recursion

Automation/composition definitions can explicitly declare whether recursive invocation is supported. This would make recursion capability itself a stable definition/compatibility/runtime dimension and require cross-surface support/feedback.

---

## 4. Recommendation Presented

```text
Recommendation
→ A — No Native Recursive Automation-to-Automation Invocation
```

Rationale:

- accepted reusable composition is fully realizable without recursion;
- recursion is not required by any accepted Product capability;
- prohibiting recursion preserves a simpler acyclic semantic dependency model and deterministic historical dependency interpretation;
- it avoids prematurely committing the product to recursion depth/boundedness, recursive HITL/retry/recovery and cross-surface recursion semantics;
- future recursion can still be introduced through explicit Owner/GAC revalidation if a real Product requirement emerges.

---

## 5. Project Owner Decision

The Project Owner selected:

```text
Selected Option
→ A

Native Automation-to-Automation Recursive Invocation
→ NOT SUPPORTED

Reusable Automation-to-Automation Composition
→ REQUIRED / PRESERVED
```

This decision is now persisted before downstream S6 synthesis consumes it.

---

## 6. Normative Semantic Consequences

### 6.1 Definition dependency

For governed Automation composition at the exact canonical revision/binding level:

```text
Composition semantic dependency graph
→ MUST be acyclic

Direct self-reference creating recursive invocation
→ UNSUPPORTED

Indirect dependency cycle creating recursive invocation
→ UNSUPPORTED
```

A cyclic candidate must fail applicable semantic validation/certification/conformance rather than being silently accepted as a legal recursion construct.

### 6.2 Runtime invocation

```text
Recursive Automation-to-Automation invocation
→ MUST NOT be created by normal governed runtime semantics

Runtime recursive continuation arising from a composition cycle
→ INVALID / UNSUPPORTED semantic condition
```

If incompatible, stale, externally imported or corrupted evidence appears to describe a recursive composition that is not accepted by the canonical definition semantics, the system must preserve explicit `UNSUPPORTED`, `INCOMPATIBLE`, `CONFLICTING`, `UNKNOWN` or `INDETERMINATE` semantics as applicable and must not silently execute it.

### 6.3 Repeated invocation is not recursion automatically

The decision does not prohibit:

```text
caller invokes the same callee multiple times sequentially
retry of a prior callee invocation while preserving attempt lineage
re-entry/resume of the same governed Automation operation
future separately governed iteration/loop semantics inside an Automation
```

The prohibited condition is an invocation ancestry cycle in Automation-to-Automation composition.

---

## 7. Revision / Binding / Historical Consequences

A composition invocation must remain historically interpretable against the exact caller revision, composition binding revision and resolved callee revision used for that invocation.

```text
Latest callee revision
!= historical callee revision automatically

Callee revision change
!= historical binding rewrite
```

A later callee revision cannot make a previously acyclic historical invocation retroactively recursive or otherwise rewrite its historical meaning.

---

## 8. Authority / SoT / Actual-state Preservation

This MDE changes no accepted authority topology:

```text
Automation Definition / Workflow Semantic Authority
→ ns_server / UNCHANGED

Automation Canonical Definition SoT
→ ns_server / UNCHANGED

Formal Artifact Acceptance Authority
→ ns_server / UNCHANGED

Formal Execution Admission Authority
→ ns_server / UNCHANGED

Automation semantic runtime Actual-state
→ S6 / SV-R02 bounded partition / UNCHANGED

Scheduling / Routing / Dispatch
→ ns_runtime / R2 / UNCHANGED

Node Attempt
→ N2 / UNCHANGED

Node Protected Effect
→ N3 / UNCHANGED
```

Reusable composition remains an Automation-domain semantic capability and does not transfer authority to caller, callee, runtime coordinator, executor, storage, authoring surface or provider.

---

## 9. Source / Visual / Agent-authoring Consequences

All complete authoring paths must apply the same recursion rule:

```text
Source-authored candidate
Visual-authored candidate
Agent-authored candidate
→ same S6 governed semantics
→ recursive composition is not silently representable as a supported construct
```

If a source/visual/Agent candidate contains a recursive composition cycle, the receiving S6 path must expose an explicit unsupported/incompatible result. No authoring surface may bypass the rule by using a different representation.

This decision does not require one AST, IR, DSL, visual schema, converter or physical representation.

---

## 10. Offline / Recovery / Replay

```text
Offline copy
!= new recursion authority

Replay
!= permission to create a recursive invocation

Recovery
!= rewriting an acyclic historical composition into a current cyclic graph
```

Historical composition and invocation lineage must remain revision-pinned. Reconciliation preserves the original dependency/binding provenance and does not resolve conflicts by latest timestamp or current definition topology.

No material fail-open/fail-closed rule is selected.

---

## 11. Compatibility / Migration

Existing or imported candidate semantics containing recursive Automation composition are not silently flattened, inlined or rewritten.

Applicable handling is explicit:

```text
SUPPORTED acyclic composition
→ normal governed lifecycle

recursive composition
→ UNSUPPORTED / INCOMPATIBLE under this Product baseline

legacy/imported recursive definition
→ explicit migration required if it is to become a valid native Automation definition
```

The migration mechanism and any future recursion capability expansion remain separately governed.

---

## 12. Explicit Non-implications

This decision does **not** establish:

```text
Automation must be represented as a DAG
one graph representation
one topological-sort algorithm
one workflow engine
one recursion-detection algorithm
one maximum depth
one call-stack implementation
one state-machine implementation
one scheduler/worker model
one queue/broker
exactly-once semantics
universal retry semantics
universal rollback/compensation
```

It also does not prohibit non-recursive cycles in implementation control flow that are invisible to and do not change the accepted Automation semantic model; implementation may not expose such mechanics as recursive Automation composition semantics.

---

## 13. Cross-component Impact

- `S6 / SV-R02` must reject/qualify recursive composition at semantic validation/runtime interpretation boundaries.
- `ns_runtime` must not infer recursion support from dispatch/routing mechanics.
- `ns_node` must not treat executable locality as permission to execute an unsupported recursive Automation dependency.
- `ns_agent` may author Automation candidates, but recursive candidates remain subject to this normal S6 rule.
- `ns_web` and System-level SDK must eventually surface the same unsupported/incompatible semantics without becoming Definition Authority.

No other component internal design is performed by this decision.

---

## 14. Revalidation Trigger

Revalidation is required if a later proposal:

1. enables direct or indirect recursive Automation-to-Automation invocation;
2. treats cyclic composition as a supported recursion construct;
3. permits an authoring surface/runtime engine to bypass the acyclic composition rule;
4. changes Automation Authority/Canonical Definition SoT or composition capability semantics materially.

Ordinary implementation changes in graph representation, storage, validation algorithm, runtime process layout or provider technology do not revalidate the decision if the accepted semantics remain unchanged.

---

## 15. Bounded-session Authority Limit

This document persists one Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not mutate Global State or the current Decision Registry, does not declare S6 or ns_server Internal Design complete, and does not authorize another Batch/component/SDK/implementation phase.

The current producing session may now consume this persisted decision only inside the already authorized S6 Batch 2 synthesis.