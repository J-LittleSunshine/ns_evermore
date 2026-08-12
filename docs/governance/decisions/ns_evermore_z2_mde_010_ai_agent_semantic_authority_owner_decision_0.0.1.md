# NGRP-001 Z2 MDE-010 — AI Agent Definition / Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-010`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Immediate Decision Entry HEAD:** `71e17fe37e42a36894d426326dc527016a98e1b9`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; current Z2 Batch 1 authorization; persisted `Z2-MDE-001..009`
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final native **AI Agent Definition / Semantic Authority** for `ns_evermore`?

This decision concerns final semantic ownership of native Agent Definition, Agent identity semantics, Agent revision meaning, Agent context semantics, Agent workflow/reasoning semantics, Agent tool-binding semantics, and Agent lifecycle meaning.

It does **not** decide model-provider authority, model routing algorithms, provider selection, memory persistence, RAG storage, Knowledge Source of Truth, prompt representation, Agent schema/API, runtime process topology, package layout, Artifact Acceptance Authority, Execution Admission Authority, or the authority of capabilities invoked by an Agent.

## 2. Classification

```text
Classification
MDE

Reason
AI Agent semantic ownership is a major first-class capability-domain ownership question.
The Genesis Constitution defines ns_agent as the AI Agent Runtime / Tooling Product Component and explicitly distinguishes AI Provider, Model, Tool Provider, RAG storage and Model Runtime from Agent semantic authority/architecture.
NSE-006 requires cross-domain invocation/composition to preserve authority and prohibits automatic authority transfer.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_agent` owns AI Agent Definition / Semantic Authority

`ns_agent` owns final native Agent Definition / Agent semantic authority. `ns_web` provides human-facing Agent management surfaces; `ns_server` supplies platform-wide Tenant/IAM/Policy/Artifact/Admission/Data/Knowledge governance dependencies; `ns_runtime` may participate in applicable runtime coordination; `ns_node` may execute local tools/effects. None gains Agent semantic authority merely through UI editing, governance participation, coordination, hosting, execution, inference, storage or provider mediation.

### B — `ns_server` owns AI Agent Definition / Semantic Authority

`ns_server` owns Agent Definition/control-plane semantics and `ns_agent` is primarily an Agent/model/tool runtime executor. This centralizes governance but risks weakening the inherited Product Component semantic identity of `ns_agent` and making the Agent domain subordinate to server-side control-plane placement.

### C — Split / Federated Agent Semantic Authority

Agent semantic authority is partitioned between `ns_server`, `ns_agent`, or other boundaries. This would require explicit durable partitions for Agent identity, definition, context, memory, workflow/reasoning, tool binding, lifecycle, compatibility and historical interpretation, with significant multiple-final-authority risk.

## 4. Recommendation Presented

`A — ns_agent owns AI Agent Definition / Semantic Authority`.

Rationale: unlike generic runtime or local executor components, `ns_agent` is itself the constitutionally fixed AI Agent Runtime / Tooling Product Component and directly inherits Agent runtime, context, memory-related capability, RAG/knowledge consumption, Agent workflow/reasoning execution, tool invocation, provider abstraction and later-designed model routing. Assigning Agent semantic authority to `ns_agent` preserves the AI Agent capability domain as `FIRST_CLASS / PARALLEL / NON_SUBORDINATE` while keeping provider/model/tool execution from defining Agent identity.

## 5. Project Owner Decision

```text
Selected Option
A

AI Agent Definition / Semantic Authority
→ ns_agent
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY now consume the following Owner-decided facts:

```text
ns_agent
→ owns native AI Agent Definition / Semantic Authority
→ owns the final platform meaning of Agent Definition / Agent semantic lifecycle within the accepted Agent domain

ns_web
→ may provide Agent management / construction / administration surfaces
→ does not gain Agent Authority through UI editing, frontend state, browser cache or routing

ns_server
→ may provide Tenant / IAM / Policy / Artifact / Admission / Data / Knowledge governance dependencies to Agent semantics
→ does not gain Agent Authority through governance participation, storage, persistence, acceptance/admission or placement

ns_runtime
→ may coordinate applicable Agent runtime execution
→ does not gain Agent Definition Authority through routing, communication, scheduling, dispatch or runtime observation

ns_node
→ may execute local tools/protected effects invoked through Agent behavior where applicable
→ does not gain Agent Authority through local execution, source/effect fact production or locality

Model / AI Provider / Model Runtime
→ provides bounded inference/model capability
→ does not gain Agent Semantic Authority by provider identity, hosting, model execution or framework behavior
```

## 7. Cross-domain Authority Preservation

This decision MUST preserve:

```text
Agent invokes Business capability
!= Agent owns Business semantic authority

Agent invokes Automation
!= Agent owns Automation semantic authority

Agent consumes Data / Knowledge
!= Agent owns Data / Knowledge Source of Truth automatically

Agent invokes ns_node tool / protected effect
!= Agent owns local execution or authorization authority

Agent uses model/provider
!= provider/model owns Agent semantics

Agent tool binding
!= invoked Tool Provider owns Agent semantics
```

Invocation, orchestration, reasoning, RAG consumption, provider mediation, shared runtime, shared persistence and shared infrastructure do not transfer the semantic authority of another first-class capability domain to `ns_agent`.

## 8. Explicit Non-Implications

This decision MUST NOT be interpreted as establishing any of the following automatically:

```text
Agent Semantic Authority = Tenant Authority
Agent Semantic Authority = IAM Authority
Agent Semantic Authority = Policy Authority
Agent Semantic Authority = Artifact Acceptance Authority
Agent Semantic Authority = Execution Admission Authority
Agent Semantic Authority = Knowledge Authority / Knowledge SoT
Agent Semantic Authority = Business Application Authority
Agent Semantic Authority = Automation Authority
Agent Semantic Authority = Local Execution Authority
Agent Semantic Authority = Model Provider Authority
Agent Semantic Authority = Tool Provider Authority
Agent Semantic Authority = Agent Runtime Actual-state Ownership
Agent Semantic Authority = Agent Definition Source-of-Truth automatically
```

Material Source-of-Truth, Actual-state Ownership, trust/security, compatibility, model-routing or provider-lock-in decisions remain separately governed.

## 9. Constraint Preservation

This decision preserves:

- `NSE-005` Product Component semantic topology and runtime non-conflation;
- `NSE-006` first-class capability non-subordination and authority non-transfer;
- `NSE-007` Definition / Artifact / Runtime separation;
- `NSE-008` local execution authority/source-effect separation where Agent tools reach local execution;
- `NSE-009` representation-independent stable cross-boundary semantics;
- `NSE-010` extension/re-delivery governance and authority non-escalation;
- `NSE-011` external SoT preservation where Agent consumes external/enterprise facts;
- `NSE-012` Shared Foundation/provider authority neutrality;
- `NSE-015` provider/framework/technology non-authority and replaceability constraints;
- `NSE-017` downstream architecture non-invention.

## 10. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Product Component Responsibility topology;
- the First-class Capability Placement section;
- the Cross-component Semantic Dependency topology;
- the Responsibility / Authority / SoT Matrix;
- later `ns_agent` Component Architecture/Capability Inventory;
- later Runtime Responsibility Architecture and Agent Contract/Module design only after separately authorized phases.

It does not authorize those downstream phases.

## 11. Revalidation Trigger

Revalidation is required if the Project Owner later changes the AI Agent capability-domain boundary, changes `ns_agent`'s root Product Component identity, moves native Agent semantic authority away from `ns_agent`, subordinates the AI Agent domain to another principal capability domain, or changes the rule that provider/model/tool invocation does not transfer semantic authority.

Changes in model/provider, Agent framework, RAG implementation, memory storage, runtime process, database, API representation, package layout, deployment topology or tool implementation do not by themselves revalidate this decision.

## 12. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize another Z2 batch, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Foundation Contract/Module/Provider Design, Implementation Planning, IWP or coding.
