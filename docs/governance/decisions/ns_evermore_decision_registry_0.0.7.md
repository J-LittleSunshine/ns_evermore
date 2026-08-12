# ns_evermore Decision Registry — Current Revision

- **Version:** `0.0.7`
- **Status:** `GLOBAL_CURRENT / NORMATIVE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Supersedes:** `0.0.6` as current working-tree registry

## 1. Registry Semantics

This is the current compact decision-classification index. Historical decisions and superseded registry revisions remain recoverable from Git history.

Current Architecture Constraint authority is defined by the current Constraint Index and Global Architecture State. Current Project Architecture authority is defined by the current Global Architecture State and applicable Global Acceptance evidence. Product-capability clarifications made by the Project Owner after Project Architecture closure are recorded here when they do not require reopening accepted Project Architecture semantics.

## 2. Root / Constraint / Project Architecture Baseline

```text
ROOT-FACT-001..017
→ accepted through the Genesis Constitution

NSE-001..017
→ GLOBAL_ACCEPTED / NORMATIVE

Current Constraint Index
→ docs/ns_evermore_nse_constraints_index_0.0.5.md

Current Project Architecture
→ docs/ns_evermore_project_architecture_0.0.3.md
→ GLOBAL_ACCEPTED / NORMATIVE / CURRENT

Accepted Project Architecture DAD Baseline
→ Z2-DAD-001..041

Accepted Owner MDE Baseline
→ Z2-MDE-001..017
→ OWNER_DECIDED / PERSISTED / GAC_RECOGNIZED
```

## 3. Current Decision Authority Model

Current authority is defined by:

`docs/governance/ns_evermore_governance_0.0.2.md`

```text
Root Product / Constitutional Decision → Project Owner
MDE → Project Owner
Product-significant Capability Decision → Project Owner Capability Checkpoint
DAD → authorized Architecture / Design Session
Implementation Choice → authorized downstream implementation authority inside Accepted Design freedom
GAC → classification / escalation / independent acceptance / phase authorization / continuity / drift
Codex → no Architecture authority
```

If classification is uncertain for a material architecture matter:

```text
DEFAULT → MDE
```

## 4. Accepted Project Architecture Context

Project Architecture `0.0.3` cumulatively establishes the complete current project-level system/component responsibility skeleton, Authority / SoT / Actual-state topology, lifecycle / Trust / recovery / compatibility semantics and 26-dimension Project Architecture semantic closure.

The following capability clarifications do not reopen those accepted semantics. They refine what the affected Product Components must be capable of doing before internal-boundary decomposition.

## 5. Current Z3 Project Owner Capability Clarifications

Status for all items in this section:

```text
OWNER_CAPABILITY_DECIDED
PERSISTED
GAC_RECOGNIZED
NO PROJECT_ARCHITECTURE REOPEN REQUIRED
```

No extra capability-ID namespace is introduced; these requirements are consumed by the Z3 capability baseline and remain traceable through this Registry revision and Git history.

### 5.1 `ns_agent` → `ns_node` governed task delegation

Required product capability:

```text
ns_agent
→ MUST be able to delegate applicable executable work / task intent to ns_node

ns_node
→ MUST be able to receive and execute applicable delegated work within its accepted local-execution responsibility
```

Permanent boundaries:

```text
Agent Delegation != Automation Definition Authority Transfer
Agent Delegation != Policy Authority Transfer
Agent Delegation != Artifact Acceptance Authority Transfer
Agent Delegation != Execution Admission Authority Transfer
Agent Delegation != ns_node gaining Agent Semantic Authority
Agent Delegation != ns_agent gaining local protected-effect authority
```

The exact delegation contract, routing path, admission evidence representation, runtime coordination path, retry/recovery mechanics and transport are later authorized design questions. `ns_runtime` may participate in later runtime coordination according to accepted responsibility, but this clarification does not preselect the mechanism.

### 5.2 `ns_server` server-local background work capability

Required capability:

```text
ns_server
→ MUST have a bounded server-local background work execution capability
→ MUST support long-running work belonging to ns_server responsibility
→ MUST support time-triggered / scheduled work belonging to ns_server responsibility
```

Project Owner intent includes a resident background execution facility. At the current capability stage, the normative requirement is the **continuously available server-local background work capability**, not a frozen process/worker topology.

Permanent boundaries:

```text
Server-local Background Work
!= ns_runtime cross-component Scheduling / Dispatch Authority replacement

Internal Time-triggered Work
!= universal task scheduling ownership

Background Execution Placement
!= Business / Policy / Admission Authority
```

Concrete process pool, worker count/model, scheduler implementation, queue/broker choice, lifecycle supervision and deployment topology are deferred to the proper Five-component Internal Architecture / Runtime Responsibility / Component Internal Design authority as applicable.

### 5.3 Automation dual authoring surfaces for node-executable packages/flows

Required product capability:

```text
Automation Definitions / Flow Packages intended for applicable ns_node execution
→ MUST support source-code / SDK-based authoring
→ MUST support visual Web drag-and-drop authoring
```

Accepted authority placement remains unchanged:

```text
Automation Definition / Workflow Semantic Authority
→ ns_server

Automation Canonical Definition SoT
→ ns_server

Visual Builder / Management UI
→ ns_web

System-level SDK / Development Surface
→ source-development surface

Applicable Local Execution
→ ns_node
```

Therefore this requirement means **dual authoring modes converge on the same governed Automation semantic domain**; it does not move Automation Definition authority into `ns_node` or `ns_web`.

Permanent rules:

```text
SDK Source Authoring != bypass Artifact / Admission Governance
Web Drag-and-drop Authoring != UI becomes Definition SoT
ns_node Execution != ns_node becomes Workflow Semantic Authority
Different Authoring Surface != Different Final Automation Semantics automatically
```

Concrete SDK APIs, visual DSL/schema, build/package representation, conversion/generation mechanics and execution representation remain later design matters.

## 6. Z3 Capability Discovery Policy

Z3 Batch 1 is intentionally a capability-discovery and Owner-checkpoint stage before Five-component Internal Architecture boundary decomposition.

For each of:

```text
ns_server
ns_runtime
ns_node
ns_agent
ns_web
```

the session must derive a broad candidate capability inventory from accepted Product Architecture and realistic product-operating scenarios, then classify every item as:

```text
INHERITED_REQUIRED
DERIVED_REQUIRED
OWNER_DECISION_REQUIRED
DEFERRED
NON_GOAL
```

The session must actively search for missing product capabilities instead of limiting itself to capabilities already named by the Project Owner.

Product-significant capabilities not already frozen are returned to the Project Owner one material question at a time. Supporting capabilities necessarily implied by accepted semantics may be classified `DERIVED_REQUIRED` where they do not expand product scope or enter MDE territory.

## 7. Cross-component Common Capability Discovery

Z3 Batch 1 may also identify **cross-component common capability candidates** needed by two or more Product Components. This is discovery/classification only and is not Shared Foundation Architecture.

Known inherited/common pressure includes at least:

```text
HTTP / client capability
Cache / client capability
Storage / client capability
Configuration loading capability
```

The session must also assess whether accepted system semantics create real cross-component need for candidates such as:

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

These names are **candidate pressure areas**, not pre-accepted Shared Foundation modules.

For every common capability candidate, the session must establish:

```text
which Product Components actually need it
whether the semantic boundary is genuinely reusable
whether one stable provider-neutral boundary appears justified
whether it carries Product Authority / SoT (normally it must not by mere reuse)
whether it should remain component-local
whether it should be deferred as a candidate to later Shared Foundation Architecture
whether Project Owner capability input is required
```

Z3 Batch 1 MUST NOT define Foundation Contracts, Modules, Providers, package layout or concrete technology.

## 8. Open Decision State

```text
Open MDE
0

Unpersisted Owner Decision
0

Owner-reserved unresolved decision
0
```

Further capability questions discovered by Z3 Batch 1 may create `OWNER_DECISION_REQUIRED` items and must be resolved/persisted before the accepted capability baseline is considered complete.

## 9. Planned Z3 Sequencing

Current planning intent, subject to independent GAC acceptance and explicit authorization at each transition:

```text
Z3 Batch 1
→ Five-component + Common Capability Discovery
→ Capability Classification
→ Owner Capability Checkpoint
→ Candidate Capability Baseline

then, only after GAC acceptance and separate authorization:

Z3 Batch 2
→ Five-component Internal Architecture Boundary Synthesis
```

This planning statement is not Batch 2 authorization.

## 10. Consumption Rule

Future Architecture / Design / Implementation Planning / IWP / Codex sessions consume current Unified Governance, Global State, current Constraint Index, this Registry, current accepted Project Architecture and the later accepted Z3 capability baseline rather than relying on prior chat context.

No session may infer Architecture authority from directory structure, framework placement, provider/library choice, data placement, transport representation, runtime placement, UI state, extension origin, commercial state or implementation convenience.
