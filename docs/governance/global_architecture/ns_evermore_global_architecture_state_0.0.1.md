# ns_evermore Global Architecture State

- Status: `CURRENT / GAC-EPOCH-0043`
- Branch: `architecture/ns-evermore-genesis-0.0.1`

# WHAT IS TRUE NOW

```text
Current Global State Epoch → GAC-EPOCH-0043
State Verified Through HEAD → ba664a3e3d03a90e456f8ca72f7c649a69165e42

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
Runtime/Domain Stable Contract Pressure → 24 / NAMED DOWNSTREAM DESIGN AUTHORITY

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

Decision Registry → 0.0.15 / CURRENT / NORMATIVE
Open MDE → 0
Unpersisted Owner Decision → 0
Blocking Item → NONE
Known Working-branch Drift → NONE
Repository Hygiene Item → refs/heads/temp-never-create / NONAUTHORITATIVE / NON_SEMANTIC / CLEANUP_ONLY

Current Authorized Phase → NGRP-001 — Component Internal Design / ns_server / Batch 1
Authorization Scope → COMPONENT_INTERNAL_DESIGN_ONLY / NS_SERVER / BATCH_1 / GOVERNANCE_CORE_INTERNAL_ARCHITECTURE_AND_STABLE_CONTRACT_SYNTHESIS
```

## Initial Component / Batch Selection

The first Component Internal Design Batch is intentionally `ns_server` Governance Core rather than a downstream execution component.

Authorized accepted internal boundaries:

```text
S1 → Tenant & Principal Identity Governance
S2 → Organization Semantics & External Mapping Governance
S3 → Policy & Authorization Governance
S4 → Platform Trust & Security Governance
S8 → Artifact Acceptance & Execution Admission Governance
S9 → Managed Runtime Configuration Governance
```

Selection rationale:

```text
S1-S4
→ produce the governance context consumed by all runtime roles and product components
→ source pressure for RCP-01 Governance Context

S8
→ owns Formal Artifact Acceptance + Formal Execution Admission
→ source pressure for RCP-02 Admission Evidence
→ also owns Artifact Identity / Acceptance Evidence contract pressure

S9
→ owns Managed Runtime Configuration governance + Desired-state SoT
→ source pressure for RCP-19 Desired / Applied Config

Therefore these boundaries are upstream internal-design dependencies for later ns_server domains
and for ns_runtime / ns_node / ns_agent / ns_web detailed design.
```

The batching decision is a GAC sequencing/bounded-scope decision. It does not redefine the six accepted boundaries or their Owner-decided Authority / SoT topology.

## Accepted Owner Authority Baseline For This Batch

The producing session MUST consume without reopening:

```text
Z2-MDE-001 → Tenant Semantic Authority = ns_server
Z2-MDE-002 → Native Tenant Canonical SoT = ns_server
Z2-MDE-003 → Native IAM Semantic Authority = ns_server
Z2-MDE-004 → Unified Policy Semantic Authority = ns_server
Z2-MDE-005 → Native Organization Semantic Authority = ns_server
Z2-MDE-006 → Organization factual SoT = exactly one final SoT per bounded semantic partition / Organization System; may be external
Z2-MDE-007 → Formal Artifact Acceptance Authority = ns_server
Z2-MDE-008 → Formal Execution Admission Authority = ns_server
Z2-MDE-015 → Platform Security / Trust Semantic Authority = ns_server
Z2-MDE-016 → Split bootstrap + central managed runtime configuration; Managed Config Authority + Desired-state SoT = ns_server; item meaning follows semantic owner; Applied state follows runtime actual-state owner
Z2-MDE-014 → Runtime Actual-state = exactly one final owner per bounded runtime semantic assertion
```

Permanent non-collapse rules include:

```text
Tenant != Organization
Authentication != IAM Semantic Authority
IAM != Policy
Policy Permit != Artifact Accepted
Artifact Accepted != Execution Admitted
Execution Admitted != Dispatched / Attempted
Trust != Policy / IAM / Admission / Acceptance
Cryptographically Valid != Trusted
Desired != Applied != Observed
Configuration != Secret
Secret Reference != Secret Material
Same ns_server placement != same semantic authority
```

## Authorized Design Work

The bounded session may derive architecture/internal-design DADs only inside S1-S4/S8/S9 and may define:

```text
internal module / responsibility decomposition inside the six accepted boundaries
internal dependency direction and cohesion
state/lifecycle custody and final-owner preservation
semantic persistence responsibility without selecting physical schema/engine
internal stable interface/contract responsibilities
cross-boundary composition among S1/S2/S3/S4/S8/S9 without authority collapse
governance evidence identity/revision/provenance/freshness obligations
offline/degraded/recovery/reconciliation responsibilities
security/privacy/secret-reference boundaries
compatibility/migration/conformance responsibilities
applicable Shared Foundation Contract/Module/Provider consumption
explicit non-goals and downstream implementation freedom
```

The session MUST explicitly close these downstream stable contract pressures at design-semantic level:

```text
RCP-01 Governance Context
→ S1-S4 → all governed consumers
→ Tenant / Organization / Principal / Policy / Trust separation
→ revision / provenance / freshness / unknown / security semantics

RCP-02 Admission Evidence
→ S8/SV-R04 → ns_runtime / executors / governed consumers
→ admission applicability / revision / revocation / stale / unknown / provenance semantics
→ Admission != Policy Permit / Acceptance / Dispatch / Attempt

RCP-19 Desired / Applied Config
→ S9 Desired → applicable runtime Actual-state owners
→ revision / partial / stale / conflict / secret-reference separation
→ Desired != Applied != Observed

S8 Artifact Identity / Acceptance Evidence pressure
→ candidate identity/revision/provenance
→ semantic certification input != formal acceptance
→ accepted/revoked/stale/unknown applicability semantics
→ Acceptance != Admission
```

The session may create additional internal-only contract subjects only when strictly necessary to realize these six accepted boundaries and when they do not invent new Product Capability, Authority or cross-component semantic pressure. Any new material cross-component stable contract pressure outside the named scope requires stop-and-return to GAC.

## Runtime / Foundation Relationship

Relevant Runtime roles/pressures are inherited, not redesigned:

```text
SV-R04 → Execution Admission Gate Participant
SV-R05 → Managed Configuration Desired-state Participant
RCP-01 / RCP-02 / RCP-19 → in current scope
Other RCP subjects → out of current Batch unless required only as named external dependency
```

Shared Foundation consumption is downstream of accepted Foundation semantics:

```text
Stable Entry
→ Foundation Contract
→ Foundation Module
→ Provider Family where provider-bearing
```

A component internal module may consume these stable Foundation semantics, but MUST NOT expose a concrete Provider identity as Product architecture or transfer Authority/SoT/Actual-state to Foundation/Provider placement.

## Strict Forbidden / Deferred Scope

Not authorized in this Batch:

```text
ns_server S5 Business Application Definition Lifecycle
ns_server S6 Automation Definition / Trigger / Composition Lifecycle
ns_server S7 Data / Knowledge / ETL Governance
ns_server S10 Server-local Background Work
ns_server S11 Human Task Aggregation
ns_server S12 Notification Lifecycle
ns_server S13 Discovery Projection

ns_runtime internal design
ns_node internal design
ns_agent internal design
ns_web internal design
System-level SDK Detailed Design

new Product capability or new Product Component
change to accepted five-component topology or Runtime Role taxonomy
change to Foundation Capability / Contract / Module / Provider semantics

concrete authentication/federation protocol or IdP/provider selection
concrete Policy engine/model/provider
concrete PKI/KMS/HSM/cryptographic algorithm/trust-store selection
concrete Artifact package/signing/digest/registry format
concrete Admission token/grant/schema/protocol
concrete configuration push/pull/watch/rollout protocol
concrete database/storage/cache/broker/provider selection
concrete DB schema / table model
concrete REST/gRPC/WebSocket/wire/schema/DTO design
concrete Django App/package/class/file layout as normative architecture
Implementation Planning
IWP
Coding
```

Concrete replaceable technology/library choices remain later delegated decisions only when they satisfy Unified Governance technology criteria and do not create material lock-in.

## MDE / Stop Boundary

The producing session may decide ordinary internal module decomposition, dependency direction, internal semantic interfaces/contracts and bounded state responsibilities as DAD when fully derivable from accepted upstream.

It MUST stop and return one material question at a time if a proposal changes or materially determines:

```text
Tenant / Organization / Principal / IAM / Policy / Trust Authority
Artifact Acceptance or Execution Admission Authority
Managed Config Authority / Desired-state SoT / Applied-state topology
Runtime Actual-state final ownership
major identity namespace or historical interpretation commitment
material offline fail-open / fail-closed behavior
major protocol/provider/framework/storage/artifact-format lock-in
high migration cost
major externally observable compatibility commitment
new Product capability
```

If classification is uncertain: `DEFAULT → MDE`.

If a missing Product capability, component boundary, Runtime responsibility, Foundation semantic or upstream Contract is discovered: `STOP affected synthesis → RETURN TO GAC`.

## Producing-session Maximum / Stop Condition

```text
NGRP-001 Component Internal Design / ns_server / Batch 1
→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
→ STOP
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```

The producing session cannot self-accept, advance GAC epoch, declare `ns_server` Internal Design complete/exhausted, authorize another ns_server Batch or another Product Component, authorize SDK design, issue `DESIGN_TO_IMPLEMENTATION_READY`, begin Implementation Planning, create IWP or code.

## Current Required Read Set

Minimum sufficient Repository context for this exact bounded session:

```text
1. docs/ns_evermore_genesis_constitution_0.0.1.md
2. docs/governance/ns_evermore_governance_0.0.2.md
3. docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md
4. docs/governance/global_architecture/ns_evermore_global_architecture_working_state_0.0.1.md
5. docs/governance/decisions/ns_evermore_decision_registry_0.0.15.md
6. docs/ns_evermore_nse_constraints_index_0.0.5.md
7. docs/ns_evermore_project_architecture_0.0.3.md
8. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_1_capability_discovery_candidate_0.0.1.md
9. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_2_interaction_experience_capability_discovery_candidate_0.0.1.md
10. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_capability_exhaustion_internal_boundary_readiness_assessment_0.0.1.md
11. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_five_component_internal_architecture_boundaries_candidate_0.0.1.md
12. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_internal_boundary_dad_evidence_0.0.1.md
13. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_batch_3_global_acceptance_0.0.1.md
14. docs/architecture_reviews/ns_evermore_ngrp_001_phase_z3_internal_boundary_exhaustion_runtime_responsibility_readiness_assessment_0.0.1.md
15. docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_candidate_0.0.1.md
16. docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_dad_evidence_0.0.1.md
17. docs/architecture_reviews/ns_evermore_ngrp_001_runtime_responsibility_architecture_batch_1_global_acceptance_0.0.1.md
18. docs/architecture_reviews/ns_evermore_ngrp_001_shared_foundation_architecture_batch_1_global_acceptance_0.0.1.md
19. docs/architecture_reviews/ns_evermore_ngrp_001_foundation_contract_design_batch_1_global_acceptance_0.0.1.md
20. docs/architecture_reviews/ns_evermore_ngrp_001_foundation_module_design_batch_1_global_acceptance_0.0.1.md
21. docs/architecture_reviews/ns_evermore_ngrp_001_foundation_provider_design_batch_1_global_acceptance_0.0.1.md
22. docs/architecture_reviews/ns_evermore_ngrp_001_foundation_provider_exhaustion_component_internal_design_readiness_assessment_0.0.1.md
23. docs/governance/decisions/ns_evermore_z2_mde_001_tenant_semantic_authority_owner_decision_0.0.1.md
24. docs/governance/decisions/ns_evermore_z2_mde_002_tenant_source_of_truth_owner_decision_0.0.1.md
25. docs/governance/decisions/ns_evermore_z2_mde_003_iam_semantic_authority_owner_decision_0.0.1.md
26. docs/governance/decisions/ns_evermore_z2_mde_004_policy_semantic_authority_owner_decision_0.0.1.md
27. docs/governance/decisions/ns_evermore_z2_mde_005_organization_semantic_authority_owner_decision_0.0.1.md
28. docs/governance/decisions/ns_evermore_z2_mde_006_organization_source_of_truth_topology_owner_decision_0.0.1.md
29. docs/governance/decisions/ns_evermore_z2_mde_007_formal_artifact_acceptance_authority_owner_decision_0.0.1.md
30. docs/governance/decisions/ns_evermore_z2_mde_008_formal_execution_admission_authority_owner_decision_0.0.1.md
31. docs/governance/decisions/ns_evermore_z2_mde_014_runtime_actual_state_ownership_topology_owner_decision_0.0.1.md
32. docs/governance/decisions/ns_evermore_z2_mde_015_platform_security_trust_semantic_authority_owner_decision_0.0.1.md
33. docs/governance/decisions/ns_evermore_z2_mde_016_configuration_authority_topology_owner_decision_0.0.1.md
34. docs/governance/global_architecture/ns_evermore_global_architecture_ledger_0.0.1.md → relevant tail
```

Read exact additional NSE/Owner evidence only if the producing design materially touches another reserved dimension.

## Unique Next Legal Action

```text
Start one bounded NGRP-001 Component Internal Design / ns_server / Batch 1 producing session under the exact current scope.
```
