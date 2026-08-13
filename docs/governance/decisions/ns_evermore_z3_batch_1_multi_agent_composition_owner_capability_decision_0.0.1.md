# NGRP-001 Phase Z3 / Batch 1 — Native Multi-Agent Composition Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `f4df0cdbbb1430ed16de0522a01198c264754d29`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should the native AI Agent capability domain support general multi-Agent composition as a first-class product capability, or should native Agent semantics remain limited to standalone Agents or a narrower hierarchical sub-Agent model?

This question is product-significant because it determines whether `ns_agent` can natively express AI applications whose constituent Native Agents compose, reference, invoke, or delegate applicable work to other Native Agents without forcing AI-native collaboration into another first-class domain such as Automation or Business Application.

It does not reopen or change accepted Project Architecture ownership:

```text
AI Agent Definition / Semantic Authority
→ ns_agent

AI Agent Canonical Definition SoT
→ ns_agent

Tenant / IAM / Policy / Trust / Artifact Acceptance / Execution Admission
→ accepted ns_server authority boundaries / unchanged

Agent → Node governed delegation
→ required / distinct capability
```

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO

Reason
→ Native Multi-Agent composition is a material product-capability boundary not explicitly fixed upstream.
→ It does not move accepted Authority, Source of Truth, Actual-state Ownership, Trust, Tenant, IAM, Policy, Artifact Acceptance or Execution Admission ownership.
```

## 3. Durable Alternatives Presented

### Option A — Standalone Native Agent only

Each Native Agent is an independent Agent-domain unit. Multi-Agent behavior, where required, is composed externally by another capability domain such as Business Application or Automation.

### Option B — Native general Multi-Agent composition

`ns_agent` natively supports Agent definitions that may compose, reference, invoke, or delegate applicable work to other Native Agent definitions.

Single-Agent and Multi-Agent composition are both native Agent-domain product capabilities.

### Option C — Native hierarchical sub-Agent delegation only

Native Agent semantics support a bounded parent/coordinating-Agent to sub-Agent relationship, but do not commit to general peer-to-peer or general Agent-graph composition.

## 4. Recommendation Presented

`B — Native general Multi-Agent composition`.

Rationale:

- AI Agent is a first-class / parallel / non-subordinate principal capability domain;
- native Agent workflow/reasoning, tool invocation and Agent-to-Node delegation do not automatically imply Agent-to-Agent composition;
- a complete Agent platform should be able to express AI-native collaboration without requiring another principal capability domain to own the composition semantics;
- the decision preserves Agent semantic authority and canonical definition ownership in `ns_agent` and does not select a concrete Multi-Agent framework or runtime topology;
- the capability remains compatible with private/offline operation and local/private model deployments.

## 5. Project Owner Decision

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

## 6. Normative Capability Consequences for Z3 Batch 1

The Z3 Batch 1 capability baseline may consume the following Owner-decided product capability:

```text
ns_agent
→ MUST support standalone Native Agents
→ MUST support Native general Multi-Agent composition

Native Multi-Agent composition
→ belongs to the AI Agent capability domain
→ remains governed by ns_agent Agent semantics
```

Permanent non-transfer rules:

```text
Agent A invokes Agent B
!= Agent B Authority transfer

Multi-Agent Composition
!= Automation Definition / Workflow Semantic Authority

Agent-to-Agent Delegation
!= Agent-to-Node Delegation

Agent Collaboration
!= Policy Authority

Agent Collaboration
!= Formal Artifact Acceptance Authority

Agent Collaboration
!= Formal Execution Admission Authority

Agent Collaboration
!= local protected-effect authority
```

Other capability domains invoked by an Agent retain their own semantic authority and factual Source-of-Truth ownership.

## 7. Explicit Non-implications / Deferred Mechanics

This Owner capability decision does **not** decide:

```text
supervisor / coordinator topology
Agent graph representation
parent/child representation
peer-to-peer protocol
handoff schema
Agent-to-Agent message schema
shared-context algorithm
shared-memory algorithm
conversation protocol
routing path
whether ns_runtime participates in routing
retry algorithm
parallelism / concurrency model
recursion / cycle handling algorithm
execution token / admission evidence representation
process / worker / service topology
queue / broker
transport
Agent framework
runtime deployment topology
```

Named later authority:

```text
Five-component Internal Architecture Boundary Synthesis
→ only after separate GAC authorization

Runtime Responsibility Architecture
→ runtime coordination / actual-state / execution mechanics where applicable

Component Internal Design
→ component-local realization after explicit authorization

Stable Contract / Foundation authorities
→ only where later accepted architecture requires them

Project Owner / MDE
→ if a later proposal materially changes Authority / SoT / Trust / major compatibility / stable identity / major lock-in or material offline fail policy
```

## 8. Offline / Private Deployment Consequence

Native Multi-Agent composition must remain compatible with accepted private/offline correctness.

```text
Multi-Agent Capability
!= Mandatory Internet Agent Service
!= Mandatory Public Model Provider
!= Mandatory Vendor SaaS Control Plane
```

Native Agents using local or privately deployed models must remain eligible participants where their accepted capability/configuration permits it.

## 9. Compatibility / Evolution Consequence

Multi-Agent definitions must retain explicit dependency/revision compatibility semantics sufficient for later architecture to distinguish supported, unsupported, unknown and incompatible Agent dependencies without selecting the concrete representation in this Batch.

```text
Agent Composition Dependency
!= Silent Latest-Version Binding automatically
```

Concrete revision constraints, migration, compatibility rules and historical interpretation remain for named later design authority; material externally visible compatibility commitments remain subject to GAC/MDE revalidation.

## 10. Preserved Invariants

This decision preserves:

- exactly five Product Components;
- AI Agent as a first-class / parallel / non-subordinate domain;
- `AI Agent Semantic Authority → ns_agent`;
- `AI Agent Canonical Definition SoT → ns_agent`;
- Agent invocation does not transfer the authority of Business Application, Automation, Data/Knowledge, Policy, Trust or local execution domains;
- Agent-to-Agent composition remains distinct from Agent-to-Node delegation;
- Definition / Artifact / Admission / Runtime separation;
- Tenant / IAM / Policy / Trust / Artifact / Admission governance;
- runtime Actual-state ownership per bounded semantic partition;
- offline/private correctness;
- no premature Runtime Architecture, component internal module design, Shared Foundation design, Contract/Module/Provider design or implementation planning.

## 11. Revalidation Trigger

Revalidate this Owner capability decision if the Project Owner later changes one or more of:

- Native general Multi-Agent composition support;
- the AI Agent capability-domain boundary;
- AI Agent Semantic Authority or Canonical Definition SoT;
- the rule that Agent composition does not transfer invoked-domain authority;
- the distinction between Agent-to-Agent composition/delegation and Agent-to-Node governed delegation.

Changes in concrete Multi-Agent framework, routing, process topology, transport, schema, provider, storage, queue/broker or deployment technology do not by themselves revalidate this capability decision.

## 12. Bounded-session Authority Limit

This evidence records one Project Owner capability decision inside Z3 Batch 1.

It does not:

```text
constitute GAC Global Acceptance
advance GAC Epoch
authorize Z3 Batch 2
complete Z3 Batch 1
start normative Five-component Internal Architecture Boundary synthesis
start Component Internal Design
start Runtime Responsibility Architecture
start Shared Foundation Architecture
start Foundation Contract / Module / Provider Design
start Implementation Planning / IWP / coding
```
