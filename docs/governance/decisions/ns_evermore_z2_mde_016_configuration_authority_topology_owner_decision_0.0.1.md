# NGRP-001 Z2 MDE-016 — Configuration Authority Topology Owner Decision

- **Decision ID:** `Z2-MDE-016`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Decision Entry HEAD:** `68cd36c5c37a5a62c78d7e51b374dd9c07a15aab`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

What Project-level authority topology governs configuration across `ns_evermore` while preserving component-local bootstrap independence, Shared Foundation authority neutrality, centralized runtime configuration governance, component semantic ownership, and runtime actual-state correctness?

The Project Owner clarified that the intended configuration architecture is not a single undifferentiated Configuration Authority. The required distinction is between:

```text
Configuration loading capability
!= Component-local bootstrap configuration
!= Managed runtime configuration governance
!= Configuration item semantic authority
!= Applied runtime configuration actual-state
```

## 2. Classification

```text
Classification
→ MDE

Reason
→ Configuration Authority / Source-of-Truth ownership is a Project-Owner-reserved architectural decision.
→ The choice materially affects all five Product Components, Shared Foundation, offline correctness, runtime governance, future compatibility and migration cost.
```

## 3. Revised Alternatives Presented to Project Owner

### A — Split Bootstrap + Central Managed Runtime Configuration

```text
Shared Foundation
→ common Configuration Loader capability
→ authority-neutral

Component-local Bootstrap Configuration
→ separate per Product Component
→ independently loadable
→ semantic ownership follows applicable component/capability owner

Managed Runtime Configuration Management Authority
→ ns_server

Managed Runtime Configuration Canonical Desired-state SoT
→ ns_server

Runtime Configuration Item Semantic Authority
→ follows semantic owner of configured capability

Applied Runtime Configuration Actual-state
→ owned by applicable runtime semantic partition
```

### B — Fully Centralized Configuration Semantics

All runtime configuration semantics, governance and canonical desired state are owned by `ns_server`; other Product Components are configuration consumers.

### C — Fully Component-owned Configuration

Each Product Component independently owns and manages both bootstrap and runtime configuration, with no unified runtime configuration governance/control plane in `ns_server`.

## 4. Recommendation Presented

`A — Split Bootstrap + Central Managed Runtime Configuration`.

This preserves centralized operational governance without turning `ns_server` into the semantic owner of every component-specific configuration item and without turning Shared Foundation into a semantic authority.

## 5. Project Owner Decision

```text
Selected Option
→ A

Architecture Pattern
→ SPLIT_BOOTSTRAP_AND_CENTRAL_MANAGED_RUNTIME_CONFIGURATION
```

The Project Owner explicitly selected Option `A` after clarifying the intended model.

## 6. Shared Foundation Responsibility

Shared Foundation MAY later provide a reusable configuration loading capability, including implementation-neutral primitives such as:

```text
configuration source abstraction
parsing/loading primitives
validation primitives
common access contract
provider-neutral configuration acquisition support
```

However:

```text
Shared Configuration Loader
!= Configuration Semantic Authority

Shared Configuration Loader
!= Managed Runtime Configuration Authority

Shared Configuration Loader
!= Configuration SoT

Shared Foundation
!= sixth Product Component
```

This preserves Shared Foundation authority neutrality.

## 7. Component-local Bootstrap Configuration

Each Product Component MUST be capable of loading the bootstrap configuration required to establish its local startup context before managed runtime configuration is necessarily available.

Project-level semantics:

```text
ns_server bootstrap configuration
→ local to ns_server bootstrap responsibility

ns_runtime bootstrap configuration
→ local to ns_runtime bootstrap responsibility

ns_node bootstrap configuration
→ local to ns_node bootstrap responsibility

ns_agent bootstrap configuration
→ local to ns_agent bootstrap responsibility

ns_web bootstrap configuration
→ local to applicable frontend bootstrap responsibility where required
```

Bootstrap configuration MAY include categories such as startup mode, local paths, bootstrap discovery information, initial connectivity information, local logging bootstrap or local resource location, but this MDE does not freeze any concrete field, file format or storage mechanism.

Permanent rule:

```text
A Product Component must not require managed runtime configuration to become sufficiently alive to obtain managed runtime configuration.
```

This prevents circular bootstrap dependency and preserves offline/private-deployment correctness.

## 8. Managed Runtime Configuration Governance

The unified runtime configuration control-plane responsibility is assigned as follows:

```text
Managed Runtime Configuration Management Authority
→ ns_server

Managed Runtime Configuration Canonical Desired-state SoT
→ ns_server
```

This means `ns_server` is responsible at Project Architecture level for the authoritative managed desired configuration state and its governed lifecycle.

This decision does NOT select:

```text
push vs pull
watch vs polling
event vs request/response
streaming vs snapshot
specific API
specific transport
specific database
specific configuration service product
specific revision representation
specific rollout algorithm
```

Those belong to later authorized design.

## 9. Configuration Semantic Authority

Centralized runtime configuration management does NOT transfer semantic ownership of every configuration item to `ns_server`.

The normative rule is:

```text
Configuration Item Semantic Authority
→ follows the semantic owner of the capability being configured
```

Examples at Project-level responsibility granularity:

```text
ns_server-owned platform/governance/business/automation/data capability configuration semantics
→ applicable ns_server-owned semantic domain

ns_runtime intrinsic communication/routing/scheduling/coordination configuration semantics
→ ns_runtime responsibility domain

ns_node intrinsic local execution/device-adjacent configuration semantics
→ ns_node responsibility domain

ns_agent intrinsic Agent runtime/tooling/provider-facing Agent configuration semantics
→ ns_agent responsibility domain

ns_web genuinely frontend/presentation-local configuration semantics
→ ns_web responsibility domain
```

Central administration, storage, presentation or distribution of those configuration items through `ns_server` does not transfer their semantic authority.

## 10. Desired State vs Applied State

The following distinction is normative:

```text
Managed Runtime Configuration Desired State
→ canonical in ns_server

Component configuration application attempt/result
→ runtime fact

Applied Runtime Configuration Actual-state
→ owned by applicable runtime semantic partition

System-level observed configuration view
→ derived/coordinated projection
```

Therefore:

```text
Desired Configuration
!= Applied Configuration
!= Observed Configuration
```

A desired value being canonical does not prove that a component has successfully applied it.

A local applied value being observed does not make that value the canonical desired configuration.

This decision consumes and preserves `Z2-MDE-014` runtime actual-state ownership topology.

## 11. Cross-cutting Governance Non-transfer

Tenant, IAM, Policy and Security/Trust semantics MAY govern configuration access, visibility, admissibility or lifecycle, but:

```text
Governance
!= Configuration Semantic Ownership Transfer
```

Likewise:

```text
Policy Authority
!= Configuration Semantic Authority

Security / Trust Authority
!= Configuration Semantic Authority

Runtime Configuration Management Authority
!= configured capability semantic authority
```

## 12. Secret Separation

This decision does not collapse configuration and secrets.

```text
Configuration
!= Secret

Configuration reference to secret material
!= secret material ownership
```

Secret reference semantics, secret material custody, provider selection and secret lifecycle remain subject to later authorized architecture/design.

## 13. Failure / Offline / Unknown Semantics

Later authorized design MUST preserve explicit semantics for states such as:

```text
bootstrap available / unavailable
managed configuration available / unavailable
configuration revision known / unknown
configuration stale
configuration unsupported
configuration validation failure
configuration application failure
configuration application partial/indeterminate
last-known managed desired state
last-known applied state
```

This MDE does not select fail-open/fail-closed behavior for any concrete configuration class.

## 14. Permanent Non-implications

This decision does NOT establish:

```text
ns_server = semantic owner of every configuration item
ns_server desired state = actual applied state
local applied value = canonical desired state
Shared Foundation = Configuration Authority
configuration storage location = configuration authority
configuration UI = configuration authority
configuration distribution channel = configuration authority
one configuration file = one semantic partition
bootstrap configuration = managed runtime configuration
configuration = secret material
```

## 15. Constraint Preservation

This decision preserves, among others:

- fixed five Product Component semantic identities;
- Shared Foundation provider/authority neutrality;
- offline/private deployment correctness;
- definition / accepted artifact / runtime-state separation;
- first-class capability-domain non-subordination;
- runtime actual-state factual ownership separation;
- downstream non-invention and Repository-backed continuity.

## 16. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Responsibility / Authority / SoT Matrix;
- the Cross-component Semantic Dependency Topology;
- later Component Internal Architecture Boundaries;
- later Runtime Responsibility Architecture;
- later Shared Foundation Configuration capability design;
- later configuration contract/module/provider design;
- later offline recovery and runtime reconciliation design.

No later phase is authorized by this decision.

## 17. Revalidation Trigger

Revalidation is required if the Project Owner later changes one or more of:

- centralized managed runtime configuration governance in `ns_server`;
- canonical managed runtime desired-state SoT in `ns_server`;
- component-local bootstrap independence;
- semantic ownership following the configured capability owner;
- Shared Foundation authority neutrality;
- desired-state vs applied-state separation.

Changing YAML/TOML/JSON/INI, a configuration library, database, transport, provider, watch mechanism or deployment topology does not by itself revalidate this MDE.

## 18. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision.

It does NOT:

```text
constitute Global Acceptance
advance GAC Epoch
authorize Z2 Batch 2
authorize Component Internal Design
authorize Runtime Responsibility Architecture
authorize Shared Foundation Detailed Design
authorize Implementation Planning / IWP / coding
```

Current bounded-session maximum remains:

```text
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```
