# NGRP-001 Phase Z3 / Batch 1 — Native Multi-Agent Composition Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should the native AI Agent capability domain support general Multi-Agent composition as a first-class product capability, or should Native Agent semantics remain limited to standalone Agents or a narrower hierarchical sub-Agent model?

This is product-significant because it determines whether `ns_agent` can natively express AI applications whose Native Agents compose, reference, invoke, or delegate applicable Agent-domain work to other Native Agents without forcing AI-native collaboration into another first-class domain.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

Native Multi-Agent composition materially changes what the Agent product domain can do, but the selected capability does not move accepted Authority, SoT, Actual-state Ownership, Trust, Tenant, IAM, Policy, Artifact Acceptance or Execution Admission ownership.

## 3. Durable Mutually-exclusive Alternatives

### A — Standalone Native Agent only

Each Native Agent is an independent Agent-domain unit. Multi-Agent behavior, if needed, is composed externally by another capability domain such as Business Application or Automation.

### B — Native general Multi-Agent composition

`ns_agent` natively supports Agent definitions that may compose, reference, invoke, or delegate applicable Agent-domain work to other Native Agent definitions. Single-Agent and Multi-Agent composition are both native product capabilities.

### C — Native hierarchical sub-Agent delegation only

Native Agent semantics support a bounded parent/coordinating-Agent → sub-Agent relationship but do not commit to general peer-to-peer or general Agent-graph composition.

## 4. Recommendation Presented

```text
Recommendation
→ B — Native general Multi-Agent composition
```

### Recommendation Rationale

AI Agent is a first-class, parallel, non-subordinate domain. A complete Agent platform should be able to express AI-native collaboration without requiring Business Application or Automation to own the composition semantics. Option B preserves Agent semantic authority in `ns_agent` while leaving the concrete Multi-Agent framework/topology entirely deferred.

## 5. Tradeoffs and Impact

**Benefits**
- enables reusable specialist Agents and decomposition of complex Agent applications;
- supports Agent-to-Agent composition without subordinating Agent semantics to another principal domain;
- preserves both standalone and composed Agent use cases.

**Costs**
- later architecture must manage Agent dependency/revision compatibility and runtime coordination semantics;
- conformance, diagnostics and lifecycle evidence become more complex for composed Agent executions.

**Risks / Complexity**
- recursive/cyclic composition, fan-out, failure propagation, context ownership and shared-state semantics require explicit later treatment;
- poorly bounded composition could create hidden cross-domain authority assumptions if later designs do not preserve provenance.

**Long-term Impact**
- `ns_agent` becomes a composable Agent application/runtime platform rather than only a standalone Agent executor;
- general Multi-Agent capability remains an Agent-domain semantic, not an Automation substitute.

**Compatibility / Migration Impact**
- composed Agent dependencies require explicit supported/unsupported/unknown/incompatible revision semantics;
- exact binding, version constraints and migration policies remain deferred.

**Offline / Private Deployment Impact**
- Multi-Agent composition must remain valid with local/private Agent/model deployments and cannot require public Agent services, public model providers or vendor SaaS for core correctness.

**Cross-component Impact**
- other domains invoked by Agents retain their own authority and factual SoT;
- Agent-to-Agent composition remains distinct from Agent→Node governed delegation;
- `ns_server` governance authorities remain unchanged; `ns_runtime` participation, if any, is a later runtime-design matter.

## 6. Project Owner Selected Result

```text
Selected Option
→ B

Native Multi-Agent Composition
→ REQUIRED

Native Agent Definition MAY
→ compose other Native Agent definitions
→ reference other Native Agent definitions
→ invoke other Native Agent definitions
→ delegate applicable Agent-domain work to other Native Agent definitions

AI Agent Semantic Authority
→ ns_agent / UNCHANGED

AI Agent Canonical Definition SoT
→ ns_agent / UNCHANGED
```

## 7. Normative Capability Consequence

```text
ns_agent
→ MUST support standalone Native Agents
→ MUST support Native general Multi-Agent composition

Multi-Agent Composition
→ belongs to AI Agent semantic domain
→ remains governed by ns_agent Agent semantics
```

## 8. Authority / SoT / Actual-state Preservation

AI Agent Semantic Authority and Canonical Definition SoT remain `ns_agent`; invoked Business Application, Automation, Data/Knowledge, Policy, Trust and local-execution domains retain their own accepted authorities/SoTs; runtime actual-state remains partitioned by accepted architecture.

## 9. Explicit Non-implications

```text
Agent A invokes Agent B != Authority transfer
Multi-Agent Composition != Automation Authority
Agent-to-Agent Delegation != Agent-to-Node Delegation
Agent Collaboration != Policy Authority
Agent Collaboration != Artifact Acceptance
Agent Collaboration != Execution Admission
Agent Collaboration != local protected-effect authority
```

## 10. Deferred Mechanics / Named Later Authority

Not decided here: supervisor/coordinator topology, Agent graph, parent/child representation, peer protocol, handoff/message schema, shared context/memory algorithm, conversation protocol, routing, retry, parallelism, recursion/cycle handling, execution/admission evidence representation, process/worker/service topology, queue/broker, transport, Agent framework or deployment topology.

These remain for separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture, Component Internal Design and later stable Contract/Foundation authorities if admitted. MDE-class changes return to Project Owner.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes general Multi-Agent support, the AI Agent capability-domain boundary, Agent Authority/Definition SoT, the non-transfer rule, or the distinction between Agent-to-Agent composition and Agent→Node delegation.

## 12. Bounded-session Authority Limit

This correction preserves the already selected Owner result only. It does not claim Global Acceptance, advance GAC state, authorize later batches or enter internal/runtime/Foundation/implementation design.
