# NSE-010 — Extension and Re-delivery Governance Preservation and Authority Non-escalation

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-010`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-010`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 3`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; `ROOT-FACT-014`; accepted `NSE-001..008`; Unified Governance 0.0.2; GAC-EPOCH-0010 Batch 3 authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

`ns_evermore` is constitutionally required to support first-party, third-party, customer-private, plugin, source-level customization, customer secondary development, and customer re-delivery. Those extension modes create a durable risk that technical extensibility becomes a governance escape: loadable code may be treated as accepted, executable material as admitted, hosted material as trusted, extension placement as semantic authority, or customer-modified/re-delivered code as exempt from Tenant, Organization, IAM, Policy, Security, Artifact, Audit, Data/Privacy, or supply-chain obligations.

A second failure mode is to preserve governance only for centrally distributed extensions while weakening it for offline/private, customer-owned, source-level, or re-delivered variants. That would contradict both extension optionality and offline/private correctness.

## 2. Normative Requirement

`ns_evermore` SHALL preserve governed extension and re-delivery semantics across all constitutionally required extension classes without allowing technical extensibility, hosting, source possession, customer modification, installation, loadability, or executability to create trust, acceptance, execution admission, semantic authority, Source-of-Truth ownership, or canonical state automatically.

All extensions SHALL remain subject to every applicable Tenant, Organization, IAM/Policy, Security/Trust, Artifact Governance, Execution Admission, Audit, Data/Privacy Governance, and supply-chain governance obligation.

Extension provenance, compatibility, and governed capability scope SHALL remain explicit enough for later architecture to verify what extension/revision is present, what it is compatible with, and what capability surface it is permitted to exercise without this constraint selecting a plugin API, manifest, package format, registry, marketplace, signing mechanism, sandbox, loader, SDK, or concrete extension lifecycle.

## 3. MUST

Future architecture and design MUST:

1. preserve first-party, third-party, customer-private, plugin, source-level customization, customer secondary development, and customer re-delivery as supported extension classes without creating a privileged governance-bypass class;
2. preserve provenance sufficient to distinguish extension origin, revision/evolution, modification/re-delivery lineage, and relevant acceptance evidence where applicable, while leaving concrete provenance representation downstream;
3. make extension compatibility explicit enough to distinguish supported, unsupported, unknown, indeterminate, stale, or unverifiable compatibility conditions where applicable;
4. preserve an explicit governed capability scope for extensions so technical reachability or implementation access does not automatically enlarge permitted product capability or authority;
5. preserve `Loadable != Accepted`, `Executable != Admitted`, and `Hosted != Trusted`, and keep extension installation/activation/runtime possession distinct from Artifact acceptance, execution admission, authorization, and trust decisions;
6. preserve applicable Tenant context for extension definition, artifact, installation, execution, data access, effects, and audit; private/single-customer deployment cannot remove Tenant governance;
7. preserve Tenant/Organization non-collapse and Organization plurality when extensions consume or extend organization-aware behavior;
8. ensure extension invocation, execution, hosting, runtime placement, shared persistence, or shared infrastructure does not automatically transfer Semantic Ownership, Authority, Source of Truth, or Actual-state Ownership;
9. preserve accepted `NSE-007` Definition/Artifact/Runtime separation for extension material and accepted `NSE-008` source-effect accountability for locally executed extension behavior where applicable;
10. preserve extension governance and verifiability in fully private/offline delivery without requiring a public marketplace, mandatory public registry, mandatory vendor control plane, or mandatory online trust/acceptance service on a core correctness path;
11. surface missing, stale, conflicting, unverifiable, or indeterminate provenance, compatibility, admission, trust, or governance evidence as an explicit condition rather than silently treating the extension as accepted/trusted/admitted;
12. require any later material choice of extension trust/security model, major extension authority ownership, major externally observable compatibility commitment, stable artifact/protocol format, or major provider/vendor lock-in to follow Unified Governance and MDE escalation where applicable;
13. preserve audit/provenance sufficient to attribute extension-originated protected effects and source facts without treating successful execution as proof of authorization, trust, or canonical status;
14. require customer re-delivery and source-level customization to preserve the same architecture invariants rather than allowing a downstream distributor or customer fork to erase them by packaging or source possession.

## 4. MUST NOT

Future architecture and design MUST NOT:

1. define `First-party Extension = Trusted automatically`;
2. define `Hosted Extension = Trusted`;
3. define `Loadable Extension = Accepted`;
4. define `Executable Extension = Execution Admitted`;
5. define `Installed / Activated Extension = Authorized`;
6. define `Extension Placement = Semantic Authority`;
7. define `Extension Runtime Fact = Canonical State` automatically;
8. allow third-party, customer-private, source-level, secondary-development, or re-delivered extensions to bypass applicable Tenant, Organization, IAM/Policy, Security/Trust, Artifact, Admission, Audit, Data/Privacy, or supply-chain governance;
9. treat possession of source code, package ownership, customer authorship, filesystem/database presence, loader access, or runtime co-location as proof of trust, acceptance, authority, or Source-of-Truth ownership;
10. allow an extension to self-expand its governed capability scope merely because an API, runtime, library, file, network endpoint, database object, or provider is technically reachable;
11. treat successful extension execution or a produced effect as proof that authorization/admission/trust existed;
12. treat an extension-local cache, store, index, projection, or runtime observation as canonical merely by extension ownership or locality;
13. choose a Plugin API, Extension Manifest, package format, registry, marketplace, signing mechanism, sandbox, loader, SDK, concrete extension lifecycle, trust model, or capability-grant mechanism within this constraint.

## 5. Long-term Invariant

```text
Extension Class != Governance Exemption
Loadable != Accepted
Executable != Admitted
Hosted != Trusted
Installed / Activated != Authorized automatically
Extension Placement != Authority
Extension Runtime Fact != Canonical State automatically
Technical Reachability != Governed Capability Scope
Source Possession / Re-delivery != Governance Erasure
```

Extension freedom and customer re-delivery MUST coexist with the same core governance invariants that protect the base product.

## 6. Origin / Provenance

This constraint is derived only from current accepted Repository authority:

- Genesis Constitution §2 `Product Identity`, which requires Source-level Extension, Customer Secondary Development, and Customer Re-delivery;
- Genesis Constitution §6 `ns_node` plugin/local execution capability;
- Genesis Constitution §7 `ns_agent` provider/tool extension capability;
- Genesis Constitution §20 `Extension / Plugin / Re-delivery`;
- Genesis Constitution §18 `Offline / Private Deployment Correctness`;
- Genesis Constitution §19 `Definition / Artifact / Runtime Separation`;
- Genesis Constitution §23 `Supply-chain Evidence` where applicable to extension delivery evidence;
- `ROOT-FACT-014 — Source-level extension, customer secondary development, and re-delivery are product requirements`;
- accepted `NSE-001..008`, especially Tenant/Organization invariants, offline governance invariance, authority non-transfer, artifact/admission separation, and local source-effect accountability;
- GAC-EPOCH-0010 Batch 3 authorization.

No pre-Genesis plugin framework, extension package, registry, marketplace, loader, signing system, sandbox, SDK, or customer-specific implementation is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

This constraint does not choose an extension trust/security model, Artifact Authority, Admission Authority, capability-grant owner, canonical-state owner, provider, registry, package format, signing mechanism, sandbox model, protocol, SDK, or conflict/canonicalization winner. Those remain downstream decisions and are MDE-governed where material.

## 8. Rationale

Extensibility is only durable if customers and third parties can extend or re-deliver the platform without forcing the architecture to trust code by origin, hosting location, or technical executability. Conversely, governance is only durable if it applies equally to first-party and customer-owned material rather than becoming a vendor-controlled central-service requirement.

The constraint therefore freezes governance preservation, provenance, compatibility, capability-scope explicitness, and authority non-escalation while leaving all concrete extension mechanisms downstream.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **First-party trusted / third-party governed split:** rejected because origin alone cannot be an architecture trust proof and customer re-delivery would become semantically inconsistent.
- **Runtime-can-load implies accepted extension:** prohibited by accepted `NSE-007`.
- **Customer source/re-delivery exempt from central governance semantics:** rejected because it would erase Tenant, security, artifact, admission, audit, data/privacy, and supply-chain obligations.
- **Uniform governance invariants with explicit provenance/compatibility/capability scope across all extension classes:** required.

Concrete plugin APIs, manifests, registries, package/signing/sandbox mechanisms, loaders, SDKs, and lifecycle engines remain deferred.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- Extension identity / provenance / revision;
- compatibility / migration;
- governed capability scope;
- Artifact acceptance / installation / activation / execution admission;
- Tenant / Organization / Principal / IAM / Policy;
- Security / Trust / Data / Privacy;
- Audit / source-effect accountability;
- Authority / Semantic Ownership / Source of Truth / Actual-state Ownership;
- supply-chain and private/offline delivery;
- cross-boundary contracts and provider extensions;
- conformance and re-delivery verification.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** extension origin/revision/lineage must remain distinguishable; concrete identifier and manifest formats are deferred.
- **Revision / Evolution:** compatibility and re-delivery lineage are explicit requirements; concrete version syntax/migration is deferred.
- **Authority / Semantic Ownership:** extension placement/execution cannot create authority; concrete owners remain downstream/MDE-governed where material.
- **Source of Truth / Actual-state Ownership:** extension-local possession/state does not decide canonical ownership; allocation is deferred.
- **State / Lifecycle / Temporal:** load/accept/install/activate/admit/attempt distinctions are preserved through `NSE-007`; no concrete extension lifecycle state machine is selected.
- **Failure / Unknown / Indeterminate:** missing/stale/conflicting/unverifiable provenance, compatibility, trust, or admission evidence remains explicit.
- **Tenant / Organization:** `NSE-001..003` remain controlling and cannot be bypassed by extension class or deployment mode.
- **Principal / Authentication / Authorization / Policy:** technical reachability and successful execution cannot establish authorization or expand capability scope.
- **Security / Data / Privacy / Trust:** applicable obligations remain invariant across extension classes; concrete trust/security model is deferred and may be MDE-class.
- **Serialization / Representation:** no manifest/package/signature/API representation is selected.
- **Offline / Degraded:** `NSE-004` remains controlling; governance cannot depend on mandatory public extension infrastructure.
- **Recovery / Reconciliation:** extension provenance and source/effect evidence must survive recovery; algorithms are deferred.
- **Compatibility / Migration:** supported/unsupported/unknown compatibility must be explicit; concrete rules are deferred.
- **Conformance:** future architecture must prove no extension class creates a governance bypass or automatic authority escalation.
- **Cross-boundary Dependency:** extensions remain bounded consumers/providers under later accepted contracts; actual APIs are deferred.
- **Invariant / Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner changes the requirement to support source-level extension, customer secondary development, customer re-delivery, or other constitutionally required extension classes, or explicitly permits an extension class to bypass the listed core governance obligations.

Changing plugin frameworks, package formats, registries, signing technology, sandboxes, loaders, SDKs, provider implementations, or repository/package layout is not by itself a revalidation trigger.

## 13. Status

```text
NSE-010
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```
