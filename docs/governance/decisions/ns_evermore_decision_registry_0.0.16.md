# ns_evermore Decision Registry — Current Revision

- Version: `0.0.16`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.15`

## Current Accepted Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
Unified Governance → 0.0.2 / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Product Capability Exhaustion → SATISFIED
Five-component Internal Architecture Boundaries → GLOBAL_ACCEPTED / NORMATIVE
Five-component Internal-boundary Exhaustion → SATISFIED
Accepted Internal Boundaries → 34
Runtime Responsibility Architecture → GLOBAL_CLOSED / COMPLETE
Runtime Roles → 22
Runtime / Domain Stable Contract Pressure → 24 / NAMED DOWNSTREAM DESIGN AUTHORITY
Shared Foundation Architecture → GLOBAL_CLOSED / COMPLETE
Foundation Contract Design → GLOBAL_CLOSED / COMPLETE
Foundation Module Design → GLOBAL_CLOSED / COMPLETE
Foundation Provider Design → GLOBAL_CLOSED / COMPLETE
Foundation Provider Design Exhaustion → SATISFIED
Accepted Foundation Capabilities → 14 / NORMATIVE
Accepted Foundation Contracts → 15 / NORMATIVE CONTRACT UPSTREAM
Accepted Foundation Modules → 14 / NORMATIVE MODULE UPSTREAM
Accepted Foundation Provider Families → 10 / NORMATIVE PROVIDER UPSTREAM
Component Internal Design Readiness → SATISFIED
```

## Accepted ns_server Component Internal Design / Batch 1

```text
NGRP-001 Component Internal Design / ns_server / Batch 1
→ GLOBAL_ACCEPTED / NORMATIVE INTERNAL DESIGN UPSTREAM

Authorization Scope
→ COMPONENT_INTERNAL_DESIGN_ONLY
  / NS_SERVER
  / BATCH_1
  / GOVERNANCE_CORE_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS

Accepted Boundaries in this Batch
→ S1 Tenant & Principal Identity Governance
→ S2 Organization Semantics & External Mapping Governance
→ S3 Policy & Authorization Governance
→ S4 Platform Trust & Security Governance
→ S8 Artifact Acceptance & Execution Admission Governance
→ S9 Managed Runtime Configuration Governance

Accepted Internal Module Count
→ 14

Accepted DAD
→ CID-SV-B1-DAD-001..013

Accepted Stable Contract Closure
→ RCP-01 Governance Context / CLOSED AT DESIGN-SEMANTIC LEVEL
→ RCP-02 Admission Evidence / CLOSED AT DESIGN-SEMANTIC LEVEL
→ RCP-19 Desired / Applied Config / CLOSED AT DESIGN-SEMANTIC LEVEL
→ S8 Artifact Identity / Acceptance Evidence / CLOSED AT DESIGN-SEMANTIC LEVEL
```

Global Acceptance evidence:
- `docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_batch_1_global_acceptance_0.0.1.md`

Accepted internal architecture Modules:

1. Tenant Canonical Governance
2. Principal & Native IAM Governance
3. Authentication Evidence & External Identity Binding
4. Organization Semantic Governance
5. Organization Mapping & Reconciliation
6. Policy Definition & Revision Governance
7. Authorization Decision & Policy Evidence
8. Trust State & Relationship Governance
9. Trust Evidence Interpretation & Revocation Evidence
10. Governance Context Composition
11. Artifact Identity & Formal Acceptance Governance
12. Execution Admission Decision & Evidence Governance
13. Managed Configuration Desired-state Governance
14. Configuration Application Evidence & Reconciliation

`G01..G14` in producing evidence are document-local navigation labels only and are not physical package/class/service/database/deployment identities.

## Accepted Dependency Semantics

```text
SDD → SEMANTIC_DEFINITION_DEPENDENCY
ACD → APPLICATION_CONTEXT_DEPENDENCY
EL  → EVIDENCE_LINKAGE
HPL → HISTORICAL_PROVENANCE_LINKAGE
XED → EXTERNAL_EVIDENCE_DEPENDENCY

Only SDD participates in recursive semantic-definition cycle analysis.
Hard SDD Graph → ACYCLIC
Unresolved Internal Dependency Cycle → 0
```

## Authority / SoT / Actual-state Preservation

```text
Tenant Semantic Authority → ns_server
Native Tenant Canonical SoT → ns_server
Native IAM Semantic Authority → ns_server
Native Organization Semantic Authority → ns_server
Organization factual SoT → exactly one final SoT per bounded semantic partition; external allowed
Unified Policy Semantic Authority → ns_server
Platform Security / Trust Semantic Authority → ns_server
Formal Artifact Acceptance Authority → ns_server
Formal Execution Admission Authority → ns_server
Managed Runtime Configuration Authority → ns_server
Managed Runtime Configuration Desired-state SoT → ns_server
Configuration Item Semantic Authority → configured capability semantic owner
Applied Runtime Configuration Actual-state → applicable runtime Actual-state owner

Authority Transfer → 0
SoT Transfer → 0
Actual-state Ownership Transfer → 0
```

### Persistence-custody clarification

The accepted Batch's internal `authoritative persistence responsibility`, `authoritative governance state`, and `authoritative decision/evidence history` wording means semantic state / decision-evidence persistence custody inside already accepted authority boundaries.

```text
Internal semantic persistence custody
!= new Project-level Source-of-Truth topology
!= storage/database placement becoming SoT
!= external factual-source authority transfer
```

The Batch does not establish a new independent Project-level IAM, Policy or Trust SoT. Any later proposal to make an internal persistence location, database, cache, provider or internal Module a new final SoT not already accepted is subject to MDE / architecture revalidation.

## Permanent Non-collapse / Security Invariants

```text
Tenant != Organization
Authentication != IAM Semantic Authority
IAM != Policy
Policy != Trust
Policy Permit != Artifact Accepted
Artifact Accepted != Execution Admitted
Execution Admitted != Scheduled / Dispatched / Attempted / Effect
Cryptographically Valid != Trusted
Connected != Trusted != Admitted
Desired != Applied != Observed
Configuration != Secret
Secret Reference != Secret Material
Persistence Placement != Authority
Cache / Projection != SoT
Evidence Aggregation != Source Authority
```

## Current Governance Boundary

```text
ns_server Component Internal Design / Batch 1 → GLOBAL_ACCEPTED
ns_server Component Internal Design Global Closure → NOT DECLARED
ns_server Internal Design Exhaustion → NOT ASSESSED
ns_server Batch 2 → NOT AUTHORIZED
Other Product Component Internal Design → NOT AUTHORIZED
System-level SDK Detailed Design → NOT AUTHORIZED
Design-to-Implementation Readiness → NOT AUTHORIZED
Implementation Planning / IWP / Coding → NOT AUTHORIZED

Open MDE → 0
Unpersisted Owner Decision → 0
```
