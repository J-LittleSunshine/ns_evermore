# ns_evermore Project Architecture — Candidate Revision 0.0.2

## Authority Metadata

- **Version:** `0.0.2`
- **Status:** `CANDIDATE / COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `BOUNDED_PROJECT_ARCHITECTURE_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Authorized Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Recovered Entry HEAD:** `18bbae478f775d46a0194c09d9cd561e3bc2ea2a`
- **Current GAC Epoch at Entry:** `GAC-EPOCH-0014`
- **Constraint Baseline:** `NSE-001..017`
- **Constraint Index:** `docs/ns_evermore_nse_constraints_index_0.0.5.md`
- **Owner Decision Baseline:** `Z2-MDE-001..017 / OWNER_DECIDED / PERSISTED`
- **Supersedes as current bounded candidate:** `docs/ns_evermore_project_architecture_0.0.1.md`
- **Global Acceptance:** `NOT CLAIMED`

Revision `0.0.1` remains historical working evidence only. Revision `0.0.2` corrects the material Definition-SoT gap discovered after `0.0.1` synthesis and explicitly consumes `Z2-MDE-017` rather than inferring canonical Product Definition SoT from Semantic Authority.

This document is a Project Architecture candidate produced by an authorized bounded session. It is not the Global Architecture Coordinator, does not advance the GAC epoch, does not authorize a later phase, and does not constitute globally accepted Project Architecture until independently accepted by the GAC.

---

## 1. Scope and Completion Boundary

This revision closes only the top-level Project Architecture questions required by Z2 Batch 1:

```text
Complete deployable system semantic boundary
Five Product Component top-level responsibility boundaries
Four principal capability-domain placement and non-subordination
Top-level semantic authority placement
Top-level Product Definition canonical SoT placement
Top-level factual SoT / runtime actual-state ownership topology
Cross-component semantic dependency topology
Project-level Responsibility / Authority / SoT matrix
Shared Foundation boundary at Project Architecture level
System-level SDK / development surface inclusion
```

This revision does NOT enter:

```text
Component Internal Design
Runtime Responsibility Architecture
process / service / container topology
module design
API / protocol / wire schema design
database / storage topology
Shared Foundation Detailed Design
Foundation Contract / Module / Provider Design
implementation planning
IWP
coding
```

---

## 2. Normative Inputs

This candidate consumes only current Repository authority, including:

- `docs/ns_evermore_genesis_constitution_0.0.1.md`;
- `docs/governance/ns_evermore_governance_0.0.2.md`;
- current Global Architecture State and Working State;
- current Decision Registry `0.0.4`;
- current Constraint Index `0.0.5`;
- accepted `NSE-001..017`;
- Z1 Batch 4 Global Acceptance and Constraint Exhaustion Assessment;
- Project Owner decisions `Z2-MDE-001..017` persisted in `docs/governance/decisions/`.

No pre-Genesis architecture solution, superseded project architecture, obsolete branch design, chat memory, or model memory is inherited as authority.

---

## 3. Complete System Semantic Boundary

### Z2-DAD-001 — Complete-system boundary

The complete `ns_evermore` product semantics consist of:

```text
Exactly five Product Components
→ ns_server
→ ns_runtime
→ ns_node
→ ns_agent
→ ns_web

Applicable Shared Foundation
→ outside the five Product Components
→ not a sixth Product Component

System-level SDK / Development Surface
→ part of complete-system capability closure
→ not itself a Product Component
→ not itself a runtime role
→ not itself a universal semantic authority
```

External enterprise systems, AI/model providers, infrastructure providers and commercial/distribution mechanisms remain outside the native Product Component topology unless later explicitly incorporated by an authorized architectural decision.

### Z2-DAD-002 — Product Component semantic identity

A Product Component is a stable product-semantic boundary. It is not equivalent to:

```text
process
service
container
pod
VM
host
database
repository directory
package
runtime instance
deployment unit
```

Future runtime/deployment design MAY realize one Product Component through multiple physical/runtime units or co-locate multiple responsibilities where allowed, but physical placement MUST NOT silently rewrite Product Component identity, Semantic Authority, SoT ownership or runtime actual-state ownership.

---

## 4. Five Product Component Top-level Responsibilities

### 4.1 `ns_server`

#### Z2-DAD-003 — `ns_server` responsibility envelope

`ns_server` is the principal native server-side semantic/governance/control-plane and business/data backend Product Component.

Top-level responsibilities include:

```text
Native Tenant Semantic Authority
Native Tenant canonical identity/governance SoT
Native IAM Semantic Authority
Unified Policy Semantic Authority
Native Organization Semantic Authority and Organization-system governance
Business Application Definition / Platform Semantic Authority
Business Application Canonical Definition SoT
Business Application Construction / Runtime backend responsibility
Automation Definition / Workflow Semantic Authority
Automation Canonical Definition SoT
Knowledge Base semantics
Enterprise Data / Knowledge Foundation semantics
Foundational ETL semantics
Data / Knowledge management, query and aggregation backend responsibility
Visualization / dashboard / large-screen / cockpit backend responsibility
Formal Artifact Acceptance Authority
Formal Execution Admission Authority
Platform Security / Trust Semantic Authority
Managed Runtime Configuration governance
Managed Runtime Configuration canonical desired-state SoT
```

`ns_server` MUST NOT be interpreted as universal authority merely because multiple semantic domains are placed there.

Permanent non-implications include:

```text
same ns_server placement
!= same semantic domain
!= common Source of Truth
!= domain subordination
!= runtime actual-state ownership
!= local execution ownership
!= AI Agent Semantic Authority
!= AI Agent Canonical Definition SoT
!= external enterprise factual authority
```

`ns_server` is not the runtime communication hub and not the local terminal executor.

---

### 4.2 `ns_runtime`

#### Z2-DAD-004 — `ns_runtime` responsibility envelope

`ns_runtime` is the native communication and runtime-coordination Product Component.

Top-level responsibilities include:

```text
long-lived communication coordination
connection management semantics
routing coordination
runtime coordination
scheduling coordination
dispatch coordination
applicable runtime orchestration coordination
bounded coordination actual-state facts
intrinsic runtime-coordination configuration semantics
```

`ns_runtime` MUST NOT automatically own:

```text
Tenant semantics
IAM semantics
Policy semantics
Business Application definitions
Automation definitions
AI Agent definitions
Data / Knowledge semantics
Formal Artifact Acceptance
Formal Execution Admission
local protected-effect facts
all system runtime factual truth
```

Permanent rules:

```text
Communication Hub != Universal SoT
Scheduler != Business Authority
Task Dispatch != Formal Execution Admission Authority
Observed Runtime State != Canonical Runtime State automatically
Runtime Configuration Consumption != Universal Configuration Authority
```

---

### 4.3 `ns_node`

#### Z2-DAD-005 — `ns_node` responsibility envelope

`ns_node` is the native local/terminal execution Product Component.

Top-level responsibilities include:

```text
local execution
OCR execution
desktop automation execution
browser automation execution
package/plugin/tool/workflow local execution
local resource interaction
local file interaction
protected local effects
offline/degraded execution continuity
local source-fact production
reconnect / reconciliation participation
bounded local execution actual-state facts
intrinsic local-execution configuration semantics
```

`ns_node` MUST NOT gain by locality or execution:

```text
Task Definition Authority
Workflow Semantic Authority
Policy Authority
Formal Artifact Acceptance Authority
Formal Execution Admission Authority
canonical business-state authority
universal runtime-state authority
```

Permanent rules:

```text
Execution != Definition
Grant Exercise != Grant Issuance Authority
Local Fact != Broader Canonical State automatically
Protected Effect Fact != Policy Authority
Applied Local Configuration != Canonical Desired Configuration automatically
```

---

### 4.4 `ns_agent`

#### Z2-DAD-006 — `ns_agent` responsibility envelope

`ns_agent` is the native AI Agent Runtime / Tooling Product Component and owns the AI Agent semantic domain.

Top-level responsibilities include:

```text
AI Agent Definition / Semantic Authority
AI Agent Canonical Definition SoT
Agent runtime
Agent identity/revision semantics
Agent context semantics
Agent memory-related capability semantics
Agent workflow / reasoning execution semantics
Tool invocation semantics within the Agent domain
RAG / Knowledge consumption capability
AI/model provider abstraction
later-designed model routing responsibility
bounded Agent-runtime actual-state facts
intrinsic Agent-runtime/tooling configuration semantics
```

`ns_agent` MUST NOT gain authority over a consumed/invoked domain merely by orchestration or consumption.

Permanent rules:

```text
Model Provider != Agent Authority
Model != Agent
Tool Provider != Agent Semantic Authority
Agent consumes Knowledge != Agent owns Knowledge
Agent invokes Business capability != Agent owns Business semantics
Agent invokes Automation != Agent owns Automation semantics
RAG Consumption != Knowledge Authority Transfer
Agent Definition SoT != Formal Artifact Acceptance Authority
```

---

### 4.5 `ns_web`

#### Z2-DAD-007 — `ns_web` responsibility envelope

`ns_web` is the native human-facing web Product Component.

Top-level responsibilities include:

```text
administration UI
Business Application UI
Business Application Builder
Automation Builder / Management UI
AI Agent management / construction UI
Data / Knowledge management UI
visualization / dashboard / large-screen / cockpit UI
operations and governance UI
control-plane interaction UI
genuinely frontend/presentation-local configuration semantics
```

`ns_web` MUST NOT become canonical authority merely because it edits, displays or caches state.

Permanent rules:

```text
UI Editing != Semantic Authority
UI Edit State != Canonical Product Definition SoT
Frontend State != Canonical State automatically
Frontend Cache != SoT
UI Routing != Architecture Boundary
Vue Component != Product Component
Central Configuration UI != Configuration Semantic Authority transfer
```

---

## 5. Shared Foundation Boundary

### Z2-DAD-008 — Shared Foundation role

Shared Foundation is outside the five Product Components and provides reusable, stable, provider-neutral capabilities where cross-component reuse is justified.

Project-level characteristics:

```text
stable reusable entry
provider-neutral contract boundary
replaceable provider implementation
common infrastructure/client capability
no automatic product-domain semantic authority
no automatic Source-of-Truth authority
```

Expected future capability families include, without detailed design here:

```text
HTTP/client capability
cache/client capability
storage/client capability
configuration loading capability
other later accepted reusable cross-cutting primitives
```

Permanent rules:

```text
Shared Foundation != sixth Product Component
Provider Placement != Semantic Authority
Foundation Storage != SoT
Foundation Cache != SoT
Foundation Configuration Loader != Configuration Semantic Authority
Foundation Configuration Loader != Managed Runtime Configuration Authority
Foundation Security/Crypto Primitive != Platform Trust Authority
```

---

## 6. System-level SDK / Development Surface

### Z2-DAD-009 — Development surface inclusion

The complete product includes a system-level SDK / development surface required to make the accepted architecture consumable and extension-capable.

It is a cross-system development contract surface, not a sixth Product Component and not a universal semantic authority.

The SDK / development surface MUST:

```text
expose stable language-neutral/versioned cross-boundary semantics where applicable
preserve underlying Product Component / capability-domain authority
preserve Tenant / Policy / Security / Artifact / Admission governance
support private/offline delivery
support extension and re-delivery without authority escalation
avoid binding architecture identity to one language/framework/provider
```

SDK packaging, language bindings, generator technology, artifact packaging and distribution mechanism are explicitly deferred.

---

## 7. Four Principal Capability Domains

### Z2-DAD-010 — First-class non-subordinate domains

The following remain `FIRST_CLASS / PARALLEL / NON_SUBORDINATE`:

| Principal capability domain | Primary top-level semantic ownership | Canonical native definition ownership | Major execution/interaction placement |
|---|---|---|---|
| Business Application Construction / Runtime | `ns_server` native platform application semantics | `ns_server` | `ns_server` backend + `ns_web` UI/builder; may compose other domains |
| Automation Construction / Execution | `ns_server` Automation Definition / Workflow semantics | `ns_server` | `ns_web` builder; `ns_runtime` scheduling/dispatch; `ns_node` local execution |
| AI Agent Runtime / Tooling | `ns_agent` AI Agent Semantic Authority | `ns_agent` | `ns_agent` runtime/tooling; may consume Knowledge and invoke other domains |
| Enterprise Data / Knowledge / Foundational ETL | `ns_server` native Data/Knowledge/ETL semantics | not generalized as one Product Definition SoT by this Batch; factual SoT follows bounded partitions | `ns_server` data/knowledge/ETL backend; `ns_web` management/visualization; consumed by other domains |

Composition, invocation, shared runtime, shared storage, shared UI or co-location MUST NOT transfer semantic authority between these domains.

---

## 8. Owner-decided Material Architecture Baseline

The following Project Owner decisions are authoritative inputs to this candidate within the bounded session:

```text
Z2-MDE-001  Tenant Semantic Authority
→ ns_server

Z2-MDE-002  Tenant Canonical SoT
→ ns_server

Z2-MDE-003  Native IAM Semantic Authority
→ ns_server

Z2-MDE-004  Unified Policy Semantic Authority
→ ns_server

Z2-MDE-005  Native Organization Semantic Authority
→ ns_server

Z2-MDE-006  Organization factual SoT topology
→ governed per Organization System / bounded semantic partition
→ exactly one final SoT per bounded assertion

Z2-MDE-007  Formal Artifact Acceptance Authority
→ ns_server

Z2-MDE-008  Formal Execution Admission Authority
→ ns_server

Z2-MDE-009  Automation Definition / Workflow Semantic Authority
→ ns_server

Z2-MDE-010  AI Agent Definition / Semantic Authority
→ ns_agent

Z2-MDE-011  Native Business Application Definition / Platform Semantic Authority
→ ns_server

Z2-MDE-012  Native Enterprise Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server

Z2-MDE-013  Data / Knowledge factual SoT topology
→ governed per bounded semantic partition
→ exactly one final SoT per bounded assertion

Z2-MDE-014  Runtime Actual-state Ownership
→ governed per bounded runtime semantic partition
→ exactly one final owner per same runtime assertion

Z2-MDE-015  Platform Security / Trust Semantic Authority
→ ns_server

Z2-MDE-016  Configuration topology
→ split local bootstrap + central managed runtime configuration
→ common Configuration Loader capability may be provided by Shared Foundation
→ managed runtime configuration management authority = ns_server
→ managed runtime configuration canonical desired-state SoT = ns_server
→ configuration item semantic authority follows configured capability owner
→ applied state follows applicable runtime actual-state owner

Z2-MDE-017  Native Product Definition Canonical SoT topology
→ Business Application Canonical Definition SoT = ns_server
→ Automation Canonical Definition SoT = ns_server
→ AI Agent Canonical Definition SoT = ns_agent
```

These decisions are `OWNER_DECIDED / PERSISTED`; this candidate does not claim GAC acceptance for them or for itself.

---

## 9. Semantic Authority and SoT Topology

### Z2-DAD-011 — Authority is semantic, not physical

No authority or SoT may be inferred solely from:

```text
database location
storage location
runtime placement
framework
process ownership
transport mediation
cache
index
ETL
projection
replication
UI ownership
provider
extension origin
package ownership
```

### Z2-DAD-012 — Single-final-authority rule per bounded assertion

For a single bounded semantic assertion, architecture MUST identify exactly one final Semantic Authority / final SoT / final actual-state owner as applicable.

Different semantic partitions MAY have different owners.

```text
Federation
!= multiple final authorities for the same assertion
```

Unknown, stale, conflicting, unmapped or indeterminate states MUST remain explicit rather than being silently resolved by physical proximity, latest arrival, preferred database or implementation convenience.

### Z2-DAD-013 — Co-location does not collapse authority types

Where one Product Component holds multiple authority types, they remain distinct semantic responsibilities.

Examples:

```text
Tenant Semantic Authority
!= Tenant Canonical SoT

Automation Semantic Authority
!= Automation Canonical Definition SoT

Platform Trust Authority
!= Policy Authority

Artifact Acceptance Authority
!= Execution Admission Authority

Managed Runtime Configuration Authority
!= Configuration Item Semantic Authority
```

---

## 10. Definition / Artifact / Admission / Runtime Separation

### Z2-DAD-014 — Governing lifecycle separation

The Project Architecture preserves the following conceptual state sequence:

```text
Domain Semantic Authority
→ Canonical Product Definition SoT where applicable
→ applicable domain semantic validation/certification
→ candidate artifact
→ Formal Artifact Acceptance
→ installation / availability where applicable
→ activation where applicable
→ Formal Execution Admission
→ scheduling / routing / dispatch
→ Runtime Execution Attempt
→ local/Agent/runtime effects and source facts
→ observation / projection / reconciliation
```

For native Product Definition domains explicitly covered by `Z2-MDE-017`:

```text
Business Application Canonical Definition SoT
→ ns_server

Automation Canonical Definition SoT
→ ns_server

AI Agent Canonical Definition SoT
→ ns_agent
```

Permanent non-equivalences:

```text
Semantic Authority != Canonical Definition SoT
Definition != Accepted Artifact
Semantic Certification != Artifact Acceptance
Accepted Artifact != Installed
Installed != Activated
Activated != Execution Admitted
Policy Permit != Execution Admission
Execution Admission != Scheduling
Scheduling / Dispatch != Runtime Attempt
Runtime Attempt != Successful Effect
Observed Projection != Source Fact
```

---

## 11. Cross-component Semantic Dependency Topology

### Z2-DAD-015 — Governance dependencies

Applicable execution-capable domains consume system governance semantics without receiving those authorities:

```text
Tenant context
IAM identity/principal context
Policy decisions
Security / Trust state
Artifact Acceptance state
Execution Admission state
Managed Runtime Configuration desired state
```

Primary governance authority placement is `ns_server`, but consumption does not transfer authority.

### Z2-DAD-016 — Business Application topology

```text
ns_web
→ construct/manage Business Application UI/Builder state

ns_server
→ authoritative Business Application platform semantics
→ canonical Business Application Definition SoT
→ Business Application backend responsibility
→ Formal Artifact Acceptance where applicable
→ Formal Execution Admission where applicable

Automation / Agent / Data / external enterprise domains
→ MAY be composed/consumed
→ retain their own authorities and factual SoTs
```

### Z2-DAD-017 — Automation semantic/execution topology

```text
ns_web
→ construct/manage Automation

ns_server
→ authoritative Automation Definition / Workflow semantics
→ canonical Automation Definition SoT
→ Formal Artifact Acceptance
→ Formal Execution Admission

ns_runtime
→ schedule / route / dispatch / coordinate

ns_node
→ perform applicable local execution
→ own bounded local source/effect facts
```

### Z2-DAD-018 — Agent semantic/execution topology

```text
ns_web
→ construct/manage Agent-facing UI state

ns_agent
→ authoritative Agent Definition / semantics
→ canonical AI Agent Definition SoT
→ Agent runtime/tooling

ns_server
→ applicable Tenant/IAM/Policy/Security governance
→ Formal Artifact Acceptance
→ Formal Execution Admission

ns_runtime
→ applicable cross-component runtime coordination

ns_node / external tools / business/data/automation domains
→ invoked capabilities as applicable
→ retain their own authority
```

### Z2-DAD-019 — Data / Knowledge topology

```text
External bounded SoTs and native ns_evermore SoTs
→ explicit source identity / bounded semantic partition

ns_server Data / Knowledge / ETL semantics
→ mapping / transformation / derived-data / knowledge-platform semantics

Business Application / Automation / Agent / UI consumers
→ consume governed projections/assets
→ no SoT transfer
```

Permanent rules:

```text
Ingestion != Authority Transfer
ETL Output != Upstream Source Fact automatically
Index != SoT
Cache != SoT
Vector != Canonical Knowledge automatically
Embedding != Canonical Knowledge automatically
RAG Consumption != Knowledge Authority Transfer
Visualization != Data Authority Transfer
```

### Z2-DAD-020 — Configuration topology

```text
Component-local bootstrap configuration
→ local per Product Component
→ common Configuration Loader capability MAY come from Shared Foundation

Managed Runtime Configuration
→ management authority = ns_server
→ canonical desired-state SoT = ns_server

Configuration item meaning
→ follows semantic owner of configured capability

Component application result / applied state
→ applicable runtime actual-state owner

System observed configuration view
→ derived projection
```

Permanent rules:

```text
Desired Configuration != Applied Configuration != Observed Configuration
Central Management != Universal Configuration Semantic Authority
Shared Loader != Configuration Authority
Configuration != Secret
```

---

## 12. Runtime Actual-state Topology

### Z2-DAD-021 — Distributed bounded factual ownership

Runtime factual ownership follows the origin and bounded semantic responsibility of the fact.

At Project Architecture level:

```text
ns_runtime
→ authoritative for its own connection/routing/scheduling/dispatch coordination facts

ns_node
→ authoritative source for bounded local execution attempts, local execution observations and protected local effects

ns_agent
→ authoritative source for bounded Agent-runtime facts originating inside Agent execution responsibility

other components
→ authoritative only for runtime facts genuinely originating inside their accepted responsibility

System-level Runtime View
→ coordinated / derived projection
→ not universal factual authority by aggregation
```

For the same runtime semantic assertion, exactly one final actual-state owner is required.

Later Runtime Responsibility Architecture MUST define precise partitions, freshness, observation, stale/unknown/indeterminate semantics and reconciliation without changing this top-level rule unless revalidated through governance.

---

## 13. Organization and Data Federation Rules

### Z2-DAD-022 — Organization factual authority

Native Organization semantics are owned by `ns_server`, while factual SoT is governed per Organization System / bounded semantic partition.

```text
Platform-native Organization System
→ MAY use ns_server as final SoT

Externally mastered Organization System
→ MAY retain bounded external final SoT

Mapping / alias / platform-native relationship semantics
→ governed by native Organization semantics

Mapping != identity equality
Ingestion != authority transfer
```

### Z2-DAD-023 — Data / Knowledge factual authority

Native Data / Knowledge / ETL semantics are owned by `ns_server`, while factual SoT is governed per bounded semantic partition.

```text
HIS / ERP / CRM / MES / HR / OA / Finance facts
→ MAY retain bounded external SoT where explicitly established

ns_evermore-native Data / Knowledge facts
→ MAY have native SoT where explicitly established

Derived facts
→ MUST retain derivation identity/provenance
→ MUST NOT masquerade as upstream source facts
```

---

## 14. Configuration Architecture Boundary

### Z2-DAD-024 — Split bootstrap and managed runtime configuration

The Project Architecture adopts the following configuration layering:

```text
Layer A — Local Bootstrap Configuration
→ component-local
→ independently loadable
→ sufficient to bootstrap the Product Component before managed runtime configuration is available
→ different Product Components MAY load different local configuration sources
→ common configuration-loading capability MAY be supplied by Shared Foundation

Layer B — Managed Runtime Configuration
→ centrally governed by ns_server
→ canonical desired-state SoT in ns_server
→ distributed/consumed by applicable Product Components through later-designed mechanisms
→ configuration item meaning remains owned by the semantic owner of the configured capability

Layer C — Applied Runtime Configuration State
→ factual applied-state belongs to applicable runtime actual-state partition owner
→ does not overwrite desired-state SoT merely because local application succeeds or fails
```

This layering explicitly permits common loading mechanics without turning Shared Foundation into Configuration Authority.

It also permits centralized runtime configuration management without making `ns_server` the semantic owner of every configuration item belonging to `ns_runtime`, `ns_node`, `ns_agent` or genuinely frontend-local `ns_web` responsibilities.

---

## 15. Offline / Degraded Correctness

### Z2-DAD-025 — Offline semantics are first-class

Core architecture correctness MUST NOT depend on public Internet, mandatory vendor SaaS, mandatory public registry or online license authority.

Offline/degraded operation MUST preserve:

```text
Tenant isolation
Policy/security semantics
Artifact/Admission governance semantics
local source/effect accountability
configuration desired/applied distinction
bounded authority ownership
reconnect/reconciliation capability
```

Central authority placement in `ns_server` does NOT by itself require synchronous online contact for every execution. Later design MAY introduce bounded pre-issued evidence, cached governed state or other offline-safe mechanisms, but MUST NOT promote the local executor into the originating semantic authority merely because connectivity is absent.

Bootstrap configuration MUST remain locally loadable enough to avoid a circular dependency in which a Product Component requires managed runtime configuration to establish the very connectivity needed to obtain managed runtime configuration.

---

## 16. Extension / Re-delivery Boundary

### Z2-DAD-026 — Extension does not escalate authority

Source extension, customer secondary development, plugins, tools, packages, custom apps, custom Automations and Agent extensions MAY participate in the product only through accepted governance boundaries.

Permanent rules:

```text
Loadable != Accepted
Hosted != Trusted
First-party != automatically Trusted
Customer-origin != automatically Untrusted
Extension origin != Authority
Installed != Admitted
Executable != Authorized
```

Re-delivery and secondary development MUST preserve native Tenant, Policy, Security, Artifact, Admission and domain-authority semantics.

---

## 17. Responsibility / Authority / SoT Matrix

| Concern | Semantic Authority | Canonical SoT / Actual-state Owner | Major operational responsibility | Notes |
|---|---|---|---|---|
| Native Tenant semantics | `ns_server` | `ns_server` for native canonical Tenant identity/governance state | `ns_server`; consumers across components | Tenant actual runtime observations remain distinct |
| Native IAM semantics | `ns_server` | `EXPLICITLY_DEFERRED_TO_LATER_AUTHORIZED_DESIGN` for native/external factual federation details | `ns_server` governance; external IdP integration later | Authentication provider != IAM Authority |
| Unified Policy semantics | `ns_server` | `EXPLICITLY_DEFERRED_TO_LATER_AUTHORIZED_DESIGN` for persistence/evaluation-state details | `ns_server` governance; enforcement distributed as applicable | Policy Permit != Admission |
| Native Organization semantics | `ns_server` | per Organization System / bounded partition, exactly one final SoT | `ns_server` native governance/integration | Tenant != Organization |
| Business Application platform semantics | `ns_server` | **Canonical Product Definition SoT = `ns_server`**; customer business factual SoTs remain independent | `ns_server` backend + `ns_web` builder/UI | Explicit `Z2-MDE-017`, not inferred from placement |
| Automation Definition / Workflow semantics | `ns_server` | **Canonical Product Definition SoT = `ns_server`** | `ns_web` build; `ns_runtime` coordinate; `ns_node` execute | Explicit `Z2-MDE-017`; execution != definition authority |
| AI Agent semantics | `ns_agent` | **Canonical Product Definition SoT = `ns_agent`**; bounded Agent runtime facts also originate in `ns_agent` responsibility | `ns_agent` runtime/tooling; `ns_web` UI | Explicit `Z2-MDE-017`; Model/provider != Agent Authority |
| Data / Knowledge / ETL semantics | `ns_server` | per bounded factual semantic partition, exactly one final SoT | `ns_server`; consumed by other domains | ETL/index/vector != SoT |
| Formal Artifact Acceptance | `ns_server` | accepted-artifact governance state is issued/decided by the Acceptance Authority; storage realization later | storage/registry implementation later | Semantic certification != acceptance |
| Formal Execution Admission | `ns_server` | admission governance state is issued/decided by the Admission Authority; representation later | `ns_runtime` consumes outcome for coordination | Admission != dispatch |
| Platform Security / Trust semantics | `ns_server` | trust-state representation/details deferred | enforcement/evidence distributed | Crypto valid != platform trusted |
| Managed runtime configuration | item meaning follows configured capability owner | canonical desired-state SoT = `ns_server` | `ns_server` manages; components apply | desired != applied |
| Component bootstrap configuration | configured capability/component semantic owner | local bootstrap source per component | component local startup + Shared Foundation loader capability later | bootstrap != managed runtime config |
| Runtime coordination facts | `ns_runtime` for coordination semantics | `ns_runtime` for bounded coordination actual-state | `ns_runtime` | not universal runtime SoT |
| Local execution/effect facts | applicable execution semantics remain with originating domains | `ns_node` for bounded local source/effect actual facts | `ns_node` | locality != broader authority |
| Agent runtime facts | `ns_agent` Agent domain | `ns_agent` for bounded originating Agent-runtime facts | `ns_agent` | consumed tool/data facts retain original authority |
| System Runtime View | none by aggregation | derived projection only | later coordination/observability design | view != source authority |
| Shared Foundation capability contracts | applicable accepted Foundation contract semantics later | no domain SoT by placement | Shared Foundation | authority-neutral |
| SDK / Development Surface | underlying domain/contract authorities | no independent universal SoT | system-level development surface | not sixth component |

---

## 18. Product Component Responsibility / Authority Summary

| Product Component | Owns at Project Architecture level | Explicitly does not own by implication |
|---|---|---|
| `ns_server` | Tenant, IAM, Policy, Organization native semantics; Business App and Automation platform semantics and their canonical native Product Definition SoTs; Data/Knowledge/ETL semantics; Artifact Acceptance; Admission; Platform Trust; managed runtime-config governance/desired SoT | Agent semantics/Agent Definition SoT; local execution facts; all runtime facts; all external enterprise factual SoTs; universal semantic authority |
| `ns_runtime` | communication/runtime coordination responsibility; bounded coordination actual-state; intrinsic coordination-config semantics | business/domain definitions; Artifact Acceptance; Admission; local protected effects; universal runtime truth |
| `ns_node` | local execution responsibility; bounded local source/effect facts; intrinsic local-execution-config semantics | Task/Workflow definition; Policy; Artifact Acceptance; Admission; universal business/runtime authority |
| `ns_agent` | Agent Semantic Authority; Agent Canonical Definition SoT; Agent runtime/tooling; bounded Agent-runtime facts; intrinsic Agent-config semantics | Knowledge/Data SoT by consumption; invoked Business/Automation authority; Platform Trust/Policy/Admission authority |
| `ns_web` | human-facing UI/builder/management/control-plane interaction responsibility; genuinely frontend-local config semantics | canonical Product Definition SoT for Business App/Automation/Agent; canonical business/config/runtime state; domain Semantic Authority by editing/display |

---

## 19. Explicit Deferred Architecture Questions

The following are intentionally NOT invented in Batch 1 because they are not required to make the top-level Project Architecture skeleton unambiguous:

```text
Native IAM factual SoT / external identity federation topology details
Policy persistence / evaluation-engine / enforcement-point topology
Tenant runtime actual-state partition details
precise Runtime semantic partition taxonomy
runtime roles / processes / services / workers
communication protocol and message schema
Artifact package / signature / registry / storage technology
Execution Admission evidence/token/protocol representation
offline fail-open/fail-closed rules per concrete operation
Security PKI/KMS/certificate/trust-store technology
Secret material custody / secret-reference contract
Configuration file format and runtime distribution protocol
Shared Foundation detailed capability inventory/contracts/modules/providers
SDK language bindings / packaging / code generation / distribution
Component internal modules and package boundaries
database/storage topology
Domain semantic-certification authorities where not yet needed at top-level
Data/Knowledge reconciliation algorithms
Organization mapping algorithms
```

Each future material choice remains subject to Unified Governance classification; uncertainty defaults to MDE.

---

## 20. Constraint Conformance Summary

This candidate is intended to preserve all accepted `NSE-001..017`:

```text
NSE-001  Tenant semantics remain native and explicit
NSE-002  Tenant != Organization
NSE-003  multiple/extensible Organization Systems preserved
NSE-004  offline/private correctness remains architectural
NSE-005  exactly five semantic Product Components preserved
NSE-006  four principal domains remain first-class/non-subordinate
NSE-007  Definition / Artifact / Admission / Runtime remain separated
NSE-008  local execution/source-effect accountability separated from broader authority
NSE-009  stable cross-boundary semantics remain language-neutral/representation-independent
NSE-010  extension/re-delivery cannot escalate authority
NSE-011  bounded external SoTs preserved
NSE-012  Shared Foundation remains provider-neutral/authority-neutral
NSE-013  complete system includes five components + Foundation + SDK/development surface
NSE-014  commercial/distribution optionality does not control core authority
NSE-015  technology exceptions cannot silently redefine architecture/dependency provenance
NSE-016  Repository-backed continuity preserved
NSE-017  downstream design must derive rather than invent architecture
```

---

## 21. Batch 1 Completion State

Within the bounded authorization of Z2 Batch 1:

```text
Complete-system semantic boundary
→ CLOSED IN CANDIDATE

Five Product Component top-level responsibilities
→ CLOSED IN CANDIDATE

Four principal capability domains
→ CLOSED IN CANDIDATE

Major Semantic Authority placement
→ CLOSED IN CANDIDATE

Native Product Definition canonical SoT topology
→ CLOSED IN CANDIDATE THROUGH Z2-MDE-017

Major factual SoT / runtime actual-state topology
→ CLOSED TO REQUIRED PROJECT-LEVEL GRANULARITY

Cross-component semantic dependency topology
→ CLOSED IN CANDIDATE

Responsibility / Authority / SoT Matrix
→ CLOSED IN CANDIDATE

Open Project-Owner MDE required for Batch 1 completion
→ NONE FOUND

Batch 1 candidate status
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

This document does not authorize Z2 Batch 2 or any later design phase.

The bounded session MUST stop at Global Acceptance handoff after review evidence is persisted.
