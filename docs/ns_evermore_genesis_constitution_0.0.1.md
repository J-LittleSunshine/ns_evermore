# ns_evermore Genesis Project Constitution

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-CONSTITUTION-0001`
- **Version:** `0.0.1`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `PROJECT_OWNER_ROOT_SEMANTICS_NORMALIZATION / CANDIDATE_NORMATIVE`
- **Program / Phase:** `NGRP-001 / Z0 — Genesis Governance Bootstrap`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** Project Owner Root Prompt supplied 2026-08-11; Owner repository visibility update to `public`
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Applicable Scope:** Entire `ns_evermore` program
- **Downstream Consumers:** Constraint Derivation, Project Architecture, Component/Runtime Architecture, Shared Foundation, Contracts, Detailed Design, Implementation Planning, IWP, Codex implementation

---

## 1. Constitutional Purpose

This Constitution records the Project Owner's root product intent, immutable root topology, delivery constraints, governance assertions, and derivation order for the new Genesis architecture program.

It is intentionally **not** a Project Architecture solution. It does not select database topology, queue technology, scheduler, worker model, organization persistence model, provider implementation, concrete runtime process layout, or internal package decomposition.

The program shall preserve the following ordering:

```text
Product Intent
→ Project Constitution
→ Architecture Constraints
→ Project Architecture
→ Component / Runtime Architecture
→ Shared Foundation
→ Contracts
→ Modules / Providers / Component Internal Design
→ Design-to-Implementation Readiness
→ Implementation Master Plan
→ Implementation Work Packages
→ Codex Incremental Implementation
→ Verification
→ Integrated ns_evermore
```

Implementation convenience MUST NOT rewrite accepted architecture.

---

## 2. Product Identity

`ns_evermore` SHALL be a complete, privately deployable, native multi-tenant enterprise platform supporting all of the following as first-class capabilities:

1. Business Application Construction / Runtime.
2. Automation Construction / Execution.
3. AI Agent Runtime / Tooling.
4. Enterprise Data / Knowledge / foundational ETL.
5. Terminal / Local Execution as a required supporting product capability.
6. Data visualization, large-screen visualization, and Management Cockpit construction/runtime.

The four principal capability domains in items 1–4 are permanently:

```text
FIRST_CLASS
PARALLEL
NON_SUBORDINATE
```

Cross-domain composition, shared implementation, shared runtime infrastructure, shared persistence, data processing, automation execution, and AI invocation MUST NOT silently transfer semantic authority from one domain to another.

The product SHALL support all of:

```text
Complete Deployable System
System-level SDK
Source-level Extension
Customer Secondary Development
Customer Re-delivery
```

The product MUST NOT be silently reduced to a workflow engine, low-code platform, agent framework, ETL tool, RPA product, single data platform, single AI platform, single BI platform, or generic infrastructure hosting platform.

---

## 3. Fixed Root Product Component Topology

The Project Owner has frozen exactly five top-level Product Components:

```text
ns_server
ns_runtime
ns_node
ns_agent
ns_web
```

This five-component topology is an `INHERITED_FACT` and is not open to downstream redesign unless the Project Owner explicitly changes the root constraint.

The following equivalences are prohibited:

```text
Five Product Components ≠ Five Processes
Five Product Components ≠ Five Services
Five Product Components ≠ Five Containers
Five Product Components ≠ Five Databases
Five Product Components ≠ Five Deployment Units
Product Component ≠ Runtime Role
```

Future design SHALL independently derive internal architecture boundaries, authorities, sources of truth, modules, runtime roles, contracts, shared foundation capabilities, providers, processes, services, deployment topology, persistence, storage, and package layout.

---

## 4. Root Responsibilities of `ns_server`

`ns_server` is the core server Product Component, primarily implemented with Python and Django.

Its root product responsibilities include at least:

- Business Application Construction / Runtime backend capability.
- IAM.
- Unified Policy Center.
- Complex Organization Architecture.
- Knowledge Base.
- Enterprise Data Foundation.
- foundational ETL.
- Data / Knowledge Management.
- Data Query / Aggregation capability.
- Data Visualization backend.
- Large-screen Visualization backend.
- Management Cockpit backend.

The following placements are frozen:

```text
IAM → inside ns_server
Policy Center → inside ns_server
Organization capability → inside ns_server
Knowledge Base → inside ns_server
Enterprise Data / Knowledge Foundation → inside ns_server
```

Placement does not imply common semantic authority. A Django app, model, database table, or process boundary MUST NOT automatically become an architecture boundary, source of truth, or authority.

Later architecture MUST independently close IAM Authority, Policy Authority, Organization Authority, Knowledge Authority, Data Authority, Artifact Authority, Configuration Authority, and Actual-state Ownership.

---

## 5. Root Responsibilities of `ns_runtime`

`ns_runtime` is the product's Communication Hub, Runtime Coordination Hub, Task Scheduling Hub, and Task Dispatch Hub. Its primary implementation language is Python and its core communication mechanism is WebSocket.

Root responsibilities include at least:

- component long-lived communication;
- connection management;
- runtime routing;
- task dispatch;
- task scheduling;
- execution coordination;
- runtime coordination;
- applicable runtime-state coordination.

The Constitution permanently rejects the following automatic implications:

```text
WebSocket ≠ Contract Semantic
WebSocket Frame ≠ Architecture Message
Communication Hub ≠ Universal Source of Truth
Scheduler ≠ Business Authority
Task Dispatch ≠ Formal Execution Admission Authority automatically
Observed Runtime State ≠ Canonical Runtime State automatically
```

No queue, broker, scheduler, or worker technology is selected by this Constitution.

---

## 6. Root Responsibilities of `ns_node`

`ns_node` is the Terminal / Local Execution Product Component. Its primary implementation language is Python and it SHALL support a resident runtime.

Root capabilities include at least:

- OCR;
- desktop automation;
- browser automation;
- automation package execution;
- plugin capability;
- local tool execution;
- workflow/orchestration flow execution;
- local resource access;
- device-adjacent integration;
- file operations;
- permitted offline/degraded execution;
- execution source-fact production;
- recovery;
- reconnection;
- reconciliation handoff.

The following invariants are constitutional:

```text
ns_node executes task ≠ Task Definition Authority
ns_node executes workflow ≠ Workflow Semantic Authority
local execution ≠ Policy Authority
local cache ≠ Source of Truth
local runtime fact ≠ Canonical Runtime State
local grant exercise ≠ grant issuance Authority
local protected effect ≠ Authorization Authority
local Audit Evidence Candidate ≠ Canonical Audit Evidence
```

Offline execution MUST NOT become a governance bypass.

---

## 7. Root Responsibilities of `ns_agent`

`ns_agent` is the AI Agent Runtime / Tooling Product Component, primarily implemented in Python.

It SHALL support coexistence of:

- local models;
- privately deployed enterprise models;
- Internet AI providers;
- multiple model providers;
- agent runtime;
- tool invocation;
- agent context;
- memory-related capability;
- RAG / knowledge consumption;
- agent workflow / reasoning execution;
- provider abstraction;
- later-designed model routing.

No vendor or framework, including OpenAI, Anthropic, DeepSeek, Qwen, Ollama, vLLM, LangChain, or future equivalents, may define the architecture identity of `ns_agent`.

Constitutional distinctions include:

```text
AI Provider ≠ AI Agent Authority
Model ≠ Agent
Tool Provider ≠ Agent Semantic Authority
RAG Storage ≠ Knowledge Source of Truth by placement
Model Runtime ≠ Agent Architecture
```

---

## 8. Root Responsibilities of `ns_web`

`ns_web` is the human-facing Web Product Component and is based on Vue 3 + TypeScript.

Root responsibilities include at least:

- Administrative UI;
- Business Application UI;
- Business Application Builder;
- Automation Builder and Management;
- AI Agent Management;
- Data / Knowledge UI;
- Dashboard;
- Large-screen Visualization;
- Management Cockpit;
- Operational UI;
- Governance UI;
- human-facing control-plane surfaces.

Frontend state, browser cache, Vue component structure, and UI routing MUST NOT automatically define canonical project state, source of truth, or architecture boundaries.

---

## 9. Native Multi-tenancy

`ns_evermore` SHALL use one native Tenant semantic model across single-customer private deployment and multi-customer deployment.

The following are prohibited:

```text
single customer → no Tenant
private deployment → Tenant bypass
single tenant → special core architecture
```

Tenant Identity, Tenant Authority, Tenant Isolation, Tenant Data, Tenant Secret, Tenant Policy, Tenant Audit, Tenant Artifact, and Tenant Runtime semantics MUST remain valid in single-customer, multi-customer, fully intranet, and fully offline deployments.

---

## 10. Tenant and Organization Non-collapse

This is a root constitutional invariant:

```text
Tenant ≠ Organization
Tenant Boundary ≠ Organization Boundary
Tenant Identity ≠ Organization Identity
Tenant Membership ≠ Organization Membership
Tenant Role ≠ Organization Role automatically
```

Tenant primarily represents customer identity, security isolation, resource ownership, governance scope, data isolation, and commercial/deployment boundary.

Organization primarily represents internal enterprise structures, business management relationships, personnel affiliation, business scope, organization authorization context, and external-system organization mapping.

The two concepts MUST NOT be collapsed into one field, one tree, or one table merely for implementation convenience.

---

## 11. Complex Extensible Organization Requirement

The platform SHALL natively support multiple independent or related organization systems inside one Tenant, including parallel, multi-level, and multi-dimensional structures.

It SHALL eventually be capable of expressing, as later architecture defines:

- custom Organization Type;
- custom Relationship Type;
- custom Hierarchy;
- custom Organization Dimension;
- Organization Membership and Multiple Membership;
- cross-organization mapping;
- external organization identity and mapping;
- aliases;
- historical organization evolution.

The platform MUST NOT assume one Tenant equals one organization tree, Organization equals department tree, one person belongs to one department, one system's organization model is globally canonical, or all structures must be flattened into a single tree.

The implementation mechanism — tree, graph, adjacency list, closure table, materialized path, graph database, relational model, or other structure — is deliberately unresolved at Z0.

Organization extension MUST remain governed by Tenant, IAM, Policy, Security, Audit, and Data Governance.

---

## 12. IAM / Policy / Organization Explicit Design Requirement

Although IAM, Policy Center, and Organization capabilities are located inside `ns_server`, later design MUST explicitly resolve Principal semantics, human/service/agent/node identity representation, Tenant/Principal relationships, organization memberships, role scoping, policy references, organization authorization context, cross-organization permissions, external organization mapping in authorization, and historical authorization interpretation.

`user.department_id`, `tenant_id + department_id`, or a generic simple RBAC schema are not valid architecture answers by themselves.

---

## 13. Knowledge and Enterprise Data Foundation

Knowledge Base and Enterprise Data Foundation are first-class capabilities inside `ns_server` and SHALL support enterprise data, knowledge, foundational ETL, integration, modeling, knowledge construction, search, retrieval, RAG, query, aggregation, and visualization/cockpit backends.

Constitutional distinctions include:

```text
Data Storage ≠ Business Authority
Knowledge Index ≠ Knowledge Source of Truth automatically
Vector Representation ≠ Canonical Knowledge automatically
Embedding ≠ Canonical Knowledge automatically
ETL Output ≠ Upstream Source Fact
Dashboard Projection ≠ Canonical Business State
```

Facts in external systems such as HIS, ERP, CRM, MES, OA, HR, and financial systems do not automatically lose their source-of-truth status merely because they are synchronized into `ns_evermore`.

---

## 14. Dashboard / Large-screen / Management Cockpit

The product SHALL natively support constructing and operating dashboards, large-screen visualizations, management cockpits, operational/business cockpits, and data-visualization applications.

Root placement is:

```text
ns_server → Data / Knowledge / Query / Aggregation / Configuration Backend
ns_web    → Visualization / Configuration / Interaction / Presentation
```

Metric semantics, dataset model, query contract, aggregation, cache, realtime data, visualization DSL, chart protocol, dashboard definition, and cockpit definition remain downstream design matters. No BI vendor is selected at Z0.

---

## 15. Shared Foundation Outside the Five Product Components

A Shared Foundation / Common Capability Layer SHALL exist outside the five Product Components. It is **not** a sixth Product Component.

It SHALL be derived according to:

```text
Stable Entry
+ Reusable Contract
+ Provider Abstraction
+ Replaceable Implementation
```

At minimum, later foundation design SHALL cover common `http_client`, `cache_client`, and `storage_client` capabilities.

Provider APIs are not foundation contracts. `http_client ≠ httpx API`; `cache_client ≠ Redis API`; `storage_client ≠ MinIO SDK`.

Potential future common capabilities such as configuration, logging, telemetry, time, serialization, cryptography abstraction, database utility, or event utility require proof of cross-component reuse, stable boundary, and implementation/provider independence where applicable.

Shared code MUST NOT automatically become Shared Foundation or semantic authority.

---

## 16. Technology Direction and Controlled Exceptions

The delivery strategy is `PYTHON-FIRST` for `ns_server`, `ns_runtime`, `ns_node`, `ns_agent`, Shared Foundation, SDK, CLI, governance tooling, Data/ETL, and Automation.

`ns_server` uses Django as a root technology fact. `ns_web` uses Vue 3 + TypeScript. `ns_runtime` is WebSocket-centered.

Technology does not define authority:

```text
Python ≠ Architecture Authority
Python Package ≠ Product Component
Django App ≠ Product Component automatically
Python Class ≠ Contract
Vue Component ≠ Architecture Component
```

Non-default technologies may enter core paths only for demonstrable needs such as platform limitation, native driver, hardware, performance, security isolation, third-party provider requirement, or operating-system integration. Any such exception SHALL have minimum necessary scope, isolation, stable language-neutral boundary, offline build/install/run support, dependency lock, SBOM/license/provenance evidence, compatibility evidence, security evidence, and a replacement/exit path.

---

## 17. Stable Language-neutral Contracts

Every stable cross-boundary contract SHALL be language-neutral, versioned, independently verifiable, and conformance-testable where applicable.

A Python class, Pydantic model, Django model, ORM model, TypeScript interface, database table, JSON payload, or WebSocket frame is not automatically an Architecture Contract.

Communication semantics SHALL be designed before WebSocket representation.

---

## 18. Offline / Private Deployment Correctness

All core capabilities SHALL support build, test, package, install, run, upgrade, rollback, and recovery with:

```text
No Public Internet
No Vendor SaaS Control Plane
No Mandatory Public Registry
No Mandatory Online License Authority
```

Optional Internet connectivity MUST NOT be a core-correctness dependency.

`ns_agent` may support Internet model providers but SHALL also support Local Model Only, Private Model Only, and fully offline deployment.

Formal dependency closure SHALL be version-locked, reproducible, and auditable. Runtime public downloads, floating `latest` dependencies, and mandatory online vendor control planes are prohibited on core delivery paths.

---

## 19. Definition / Artifact / Runtime Separation

The platform SHALL preserve:

```text
Development Definition
≠ Domain Semantic Certification
≠ Accepted Artifact
≠ Installation
≠ Activation
≠ Formal Execution Admission
≠ Runtime Execution Attempt
```

Formal production execution MUST NOT directly run mutable working source, unpublished definition, unchecked dynamic code, or unaccepted automation packages.

---

## 20. Extension / Plugin / Re-delivery

The product SHALL support first-party, third-party, customer-private, plugin, source-level, and re-delivery extensions.

Extension surfaces include at least `ns_node` plugins, `ns_agent` tool/model-provider extensions, `ns_server` business/data/knowledge extensions, and later-designed `ns_web` UI extensions.

Extensions MUST NOT bypass Tenant, Organization, IAM, Policy, Security, Artifact Governance, Audit, Data Governance, or Supply-chain Governance.

---

## 21. Product Non-goals and Bounded Enterprise Integration

`ns_evermore` is not intended to replace ERP, CRM, MES, HIS, HR, or OA as a universal enterprise-core replacement platform.

It SHALL act above and across such systems as a platform for business application extension, automation, AI Agent capability, data/knowledge, integration, intelligent orchestration, and visualization/cockpit use cases while preserving bounded external source-of-truth relationships.

---

## 22. Distribution and Commercial Optionality

Architecture SHALL preserve future optionality for closed-source commercial delivery, binary delivery, source delivery, customer-private source delivery, future open-core models, and third-party ecosystems.

Current commercial mode MUST NOT permanently lock the architecture.

---

## 23. Supply-chain Evidence

Formal delivery assets SHALL be capable of producing and validating applicable digest, dependency lock, SBOM, license/NOTICE, provenance, compatibility, and security/vulnerability evidence.

Specific tools are downstream decisions.

---

## 24. Architecture-before-Implementation Invariants

The project permanently requires:

```text
Semantic Authority before Database
Source of Truth before Persistence
Fixed Product Component before Internal Module
Component Responsibility before Runtime Process
Stable Contract before Framework Interface
Runtime Responsibility before Worker / Service Layout
Shared Capability Contract before Provider
Foundation Contract before Foundation Module
Accepted Design before Implementation Planning
Implementation Plan before Codex
```

If implementation convenience conflicts with accepted architecture:

```text
IMPLEMENTATION MUST YIELD
→ RETURN TO ARCHITECTURE
```

---

## 25. Decision Governance Root Rules

Every formal design matter SHALL be classified before freezing as:

```text
INHERITED_FACT
DELEGATED_ARCHITECTURE_DECISION / DAD
MAJOR_DECISION_ESCALATION / MDE
```

Inherited facts are not open to downstream voting or reopening.

Any question affecting major capability boundaries, semantic ownership, source of truth, actual-state ownership, acceptance/admission/selection/execution/business authority, Tenant/Organization/Principal/IAM/Policy/Security/Data/Knowledge authority, lifecycle/resource ownership, stable identity commitments, major externally visible behavior, major backward compatibility/history interpretation, offline fail-open/fail-closed policy, major trust/privacy/security policy, long-term provider/vendor/language/framework/protocol/storage/artifact-format lock-in, high migration cost, or multiple materially valid long-term alternatives SHALL be escalated as MDE.

When classification is uncertain, default to MDE.

Each MDE interaction SHALL handle one material decision at a time, present three mutually exclusive long-term-valid options A/B/C with recommendation, rationale, benefits, costs, and long-term impact, and MUST NOT auto-select for the Project Owner.

Owner decisions SHALL be persisted before downstream consumption.

---

## 26. Mandatory Semantic Resolution Principle

Every applicable later Architecture / Contract / Module shall explicitly close or justify `NOT_APPLICABLE` for:

Identity/Namespace; Revision/Evolution; Authority; Semantic Ownership; Source of Truth; Actual-state Ownership; State/Lifecycle; Temporal Semantics; Failure/Unknown/Indeterminate; Tenant; Organization; Principal; Authentication; Authorization/Policy; Security; Data/Privacy/Trust; Serialization/Representation; Offline/Degraded; Recovery/Reconciliation; Compatibility; Migration; Conformance; Cross-boundary Dependency; Invariant; Decision Traceability; Revalidation Trigger.

Design completeness is judged by semantic resolution depth, not line count, document count, or decision count.

---

## 27. Required Derivation Order

The authorized derivation chain is:

```text
Project Constitution
→ Architecture Constraint Derivation
→ Project Architecture
→ Five-component Internal Architecture Boundaries
→ Runtime Responsibility Architecture
→ Architecture Exhaustion / Readiness
→ Shared Foundation Architecture
→ Foundation Contracts
→ Foundation Modules
→ Provider Design
→ Component Internal Design
→ Design-to-Implementation Readiness
→ Implementation Master Plan
→ Implementation Work Packages
→ Codex Implementation
→ Verification
```

No later phase is automatically authorized by completion of an earlier phase.

---

## 28. Repository-backed Continuity Constitution

The project adopts `DOCUMENT-FIRST CONTINUITY`.

```text
Conversation Context May Disappear
Repository Context Must Not
```

Repository evidence is persistent project memory and governance source of truth. Chat context is temporary. Model memory is non-authoritative.

Architecture-critical context MUST NOT exist only in conversation.

A fresh session with no prior chat history SHALL be able to recover the project, accepted constraints and decisions, current architecture revision, current phase and authorization, open MDEs, blocking items, required read set, drift status, and unique next legal action using Repository evidence alone.

The following root continuity assertions are permanent:

```text
Architecture Must Be Resumable
Design Must Be Traceable
Design Must Be Implementation-derivable
Implementation Must Be Incremental
Every Increment Must Be Verifiable
```

---

## 29. Independent Acceptance and Stop Discipline

Bounded design sessions MUST NOT self-accept. They may reach only:

```text
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

Only the Global Architecture Coordinator may independently issue `GLOBAL_ACCEPT` after reviewing Git evidence, decision classification, owner-decision closure, semantic resolution, constraint preservation, authority/source-of-truth consistency, Tenant/Organization non-collapse, dependency/invariant integrity, provenance, and downstream-boundary compliance.

Completion of one phase never automatically authorizes the next phase.

---

## 30. Genesis Historical Inheritance Rule

The branch `architecture/ns-evermore-genesis-0.0.1` starts from `main` only as a Git ancestry fact.

Pre-Genesis code, documentation, ADRs, runtime implementations, or prior architecture artifacts present in Git history are **not automatically normative inputs** to this Genesis architecture program.

They may be consulted later as historical evidence or implementation reality only when an authorized phase explicitly admits them through provenance-aware derivation or compatibility analysis.

No hidden inheritance is permitted.

---

## 31. Z0 Boundary

Z0 is governance bootstrap only. It may normalize root facts and establish governance mechanisms, but it MUST NOT begin concrete Architecture Constraint derivation beyond namespace/bootstrap necessity, IAM Architecture, Organization solution design, Policy Architecture, Data Architecture, Knowledge Architecture, Runtime Architecture, Component Internal Design, Shared Foundation detailed design, Foundation Contract design, provider selection, database design, Implementation Planning, IWP generation, or coding.

---

## 32. Current Constitutional State

At Z0 completion candidate state:

- Root Product Semantics: `CLOSED / RECORDED`
- Five-component Root Topology: `RECORDED`
- Native Multi-tenancy: `RECORDED`
- Tenant / Organization Non-collapse: `RECORDED`
- Complex Organization Extensibility: `RECORDED`
- Python-first Direction: `RECORDED`
- Shared Foundation Requirement: `RECORDED`
- Offline / Private Correctness: `RECORDED`
- Decision / Quality / Derivation / Continuity Governance: established by companion governance artifacts
- Architecture Solution Leakage: `0`
- Open MDE: `0`
- Unpersisted Owner Decision: `0`

This document remains `AWAITING_GLOBAL_ACCEPTANCE` until independently accepted by the Global Architecture Coordinator.