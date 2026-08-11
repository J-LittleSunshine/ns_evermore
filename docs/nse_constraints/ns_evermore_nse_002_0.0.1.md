# NSE-002 — Tenant / Organization Semantic Non-collapse

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-002`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-002`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 1`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; `ROOT-FACT-007`; `ROOT-FACT-008`; Z0 Global Acceptance; Z1 Batch 1 Authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

Tenant and Organization both participate in identity, membership, authorization context, data scope, governance, and enterprise integration. Without an explicit architecture constraint, implementation convenience can collapse them into one identifier, one hierarchy, one membership model, one role model, or one persistence object.

Such collapse would incorrectly allow mutable enterprise organization structure to redefine the customer security/resource boundary and would make future IAM, Policy, Data, Audit, Runtime, Automation, and Agent semantics ambiguous.

## 2. Normative Requirement

`ns_evermore` SHALL preserve Tenant and Organization as distinct architecture semantics.

Tenant defines a customer/security/resource/governance boundary. Organization expresses enterprise structure, affiliation, business-management relationships, organization authorization context, and external-organization mapping inside the applicable Tenant governance boundary.

Organization context MAY be referenced by IAM, Policy, Business Application, Automation, Agent, Data, Audit, and Runtime semantics, but Organization context MUST NOT redefine, replace, or implicitly create the Tenant security/resource boundary.

## 3. MUST

Future architecture and design MUST:

1. preserve distinct Tenant Identity and Organization Identity semantics;
2. preserve distinct Tenant Boundary and Organization Boundary semantics;
3. preserve distinct Tenant Membership and Organization Membership semantics;
4. preserve distinct Tenant Role and Organization Role semantics unless an explicit later policy mapping is accepted;
5. permit Organization context to participate in authorization and business decisions without becoming Tenant Authority;
6. require later architecture to explicitly resolve Organization Authority, Organization Source of Truth, and Organization Actual-state Ownership rather than inheriting them from Tenant placement, Django placement, persistence placement, or external-system placement;
7. keep Organization creation, evolution, membership, mapping, and historical interpretation subject to applicable Tenant, IAM, Policy, Security, Audit, and Data Governance;
8. preserve the Tenant/Organization distinction in online, offline, local, degraded, recovery, and reconciliation paths;
9. preserve enough semantic separation that changing an Organization structure does not by itself change the Tenant security/resource boundary;
10. require any mapping between Tenant roles/memberships and Organization roles/memberships to be explicit, governed, and non-automatic.

## 4. MUST NOT

Future architecture and design MUST NOT:

1. define `Tenant = Organization`;
2. define `Tenant Boundary = Organization Boundary`;
3. define `Tenant Identity = Organization Identity`;
4. define `Tenant Membership = Organization Membership`;
5. define `Tenant Role = Organization Role` automatically;
6. treat an Organization hierarchy, department, business unit, legal entity, cost center, project group, external directory unit, or similar structure as the Tenant boundary merely because it is convenient;
7. grant Tenant membership, Tenant authority, or Tenant-scoped access solely from Organization membership without an explicit accepted authorization rule;
8. treat an external organization's identifier or hierarchy as the global Tenant identifier or global Tenant boundary;
9. use one table, field, tree, role table, permission schema, or database object as proof that Tenant and Organization are the same architecture concept;
10. select an IAM engine, authorization engine, role schema, Organization table, database model, or persistence topology within this constraint.

## 5. Long-term Invariant

```text
Tenant != Organization
Tenant Boundary != Organization Boundary
Tenant Identity != Organization Identity
Tenant Membership != Organization Membership
Tenant Role != Organization Role automatically
Organization Context MAY influence decisions
Organization Context MUST NOT redefine Tenant Security / Resource Boundary
```

This distinction MUST survive organization restructuring, external-system remapping, offline operation, implementation refactoring, and persistence migration.

## 6. Origin / Provenance

This constraint is derived only from accepted Genesis authority:

- Genesis Constitution §9 `Native Multi-tenancy`;
- Genesis Constitution §10 `Tenant and Organization Non-collapse`;
- Genesis Constitution §11 `Complex Extensible Organization Requirement` where governance interaction is directly relevant;
- Genesis Constitution §12 `IAM / Policy / Organization Explicit Design Requirement`;
- `ROOT-FACT-007 — Tenant != Organization`;
- `ROOT-FACT-008 — Complex/extensible Organization architecture is mandatory`;
- `NS-EVERMORE-Z0-GLOBAL-ACCEPTANCE-0001`;
- `NS-EVERMORE-POST-Z0-CONSTRAINT-PRESSURE-0001`;
- `NGRP-001-Z1-B1-AUTH-0001`.

No pre-Genesis architecture or implementation artifact is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

This record does not choose Organization Authority ownership, an IAM model, an authorization model, a role model, a persistence model, or a canonical Organization source. Those remain later architecture decisions under the accepted MDE/DAD rules where applicable.

## 8. Rationale

Tenant and Organization change for different reasons and operate at different semantic levels. Customer isolation must remain stable even while enterprise structure is reorganized, synchronized from external systems, represented in multiple dimensions, or interpreted historically.

Keeping the concepts separate prevents organization changes from accidentally widening or shrinking the customer security boundary and allows future IAM/Policy design to consume Organization context deliberately rather than treating it as a hidden Tenant surrogate.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **Collapse Organization into Tenant:** prohibited by accepted root semantics.
- **Collapse Tenant into Organization hierarchy:** prohibited by accepted root semantics.
- **Keep separate concepts but automatically equate memberships/roles:** rejected because it reintroduces semantic collapse through authorization.
- **Keep Tenant and Organization distinct and require explicit mappings where needed:** required.

Concrete role models, policy models, persistence models, tables, and engines are outside this phase.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- Identity / Namespace;
- Tenant and Organization authority;
- Principal and membership semantics;
- IAM / Authentication / Authorization / Policy;
- Data / Secret / Audit / Artifact scoping;
- Business Application / Automation / Agent context;
- Runtime context and protected effects;
- external Organization integration;
- historical interpretation;
- offline / degraded operation;
- recovery / reconciliation;
- compatibility / migration / conformance.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** Tenant and Organization identity semantics are distinct; identifier formats are deferred.
- **Revision / Evolution:** Organization may evolve without redefining Tenant identity; versioning mechanics are deferred.
- **Authority / Semantic Ownership:** Tenant and Organization authority concerns are distinct; concrete owners are deferred.
- **Source of Truth / Actual-state Ownership:** explicit future resolution is required independently for Tenant and Organization; no source is selected here.
- **State / Lifecycle / Temporal:** Organization lifecycle and historical meaning must not rewrite Tenant boundary; models are deferred.
- **Failure / Unknown / Indeterminate:** unresolved Organization context cannot be silently substituted with Tenant context or vice versa.
- **Tenant:** closed by explicit non-collapse.
- **Organization:** closed by explicit distinct semantics and governance scope.
- **Principal / Authentication / Authorization / Policy:** Organization context may be referenced but cannot automatically confer Tenant membership/role/authority.
- **Security / Data / Privacy / Trust:** Organization must not weaken Tenant isolation; mechanisms are deferred.
- **Serialization / Representation:** no combined identifier or schema is selected.
- **Offline / Degraded:** distinction remains valid offline.
- **Recovery / Reconciliation:** remapping/recovery must preserve which facts are Tenant facts versus Organization facts; algorithms are deferred.
- **Compatibility / Migration:** migrations cannot silently collapse the concepts.
- **Conformance:** later conformance must test identity/membership/role non-equivalence.
- **Cross-boundary Dependency:** consumers may reference both contexts but must preserve their distinct meaning.
- **Invariant / Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner explicitly changes the constitutional meaning of Tenant, Organization, their boundary relationship, or the requirement that `Tenant != Organization`.

Changes in Organization persistence, IAM technology, role schema, database structure, directory provider, or frontend representation are not by themselves revalidation triggers.

## 13. Status

```text
NSE-002
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```
