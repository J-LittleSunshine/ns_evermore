# NSE-015 — Controlled Technology Exception Containment and Offline Dependency Provenance Closure

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-015`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-015`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 4`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; `ROOT-FACT-002`; `ROOT-FACT-003`; `ROOT-FACT-004`; `ROOT-FACT-005`; `ROOT-FACT-011`; `ROOT-FACT-012`; accepted `NSE-001..012`; Unified Governance 0.0.2; GAC-EPOCH-0012 Batch 4 authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

The accepted product direction is Python-first, with specific root technology facts for `ns_server`, `ns_runtime`, `ns_node`, `ns_agent`, and `ns_web`. Real delivery may still require bounded exceptions for platform integration, native drivers, hardware, performance, security isolation, operating-system integration, or third-party provider constraints.

Without an Architecture Constraint, a technology exception can expand until language/framework/provider placement becomes Product Component identity, contract semantics, Authority, Source of Truth, security policy, Tenant bypass, or offline-correctness exception. Separately, dependency acquisition can rely on mutable public registries or online resolution without enough evidence to prove what dependency/revision was used, where it came from, whether it is permitted, whether it is available offline, and whether it conforms to accepted architecture requirements.

## 2. Normative Requirement

`ns_evermore` SHALL preserve the accepted `PYTHON-FIRST` direction and all current frozen technology facts while allowing only explicit, bounded, justified, governed, and traceable technology exceptions.

A technology exception SHALL remain an implementation/technology exception rather than an architecture-authority exception. It MUST NOT by technology choice, provider placement, framework capability, library behavior, native integration, or operational convenience redefine accepted Product Component boundaries, Semantic Ownership, Authority, Source of Truth, Actual-state Ownership, stable contract semantics, Tenant/Organization semantics, Security/Trust boundaries, Artifact/Admission semantics, or offline/private correctness.

Formal dependency/supply-chain evidence SHALL be sufficient to establish, for dependencies relevant to formal delivery and core correctness, what dependency is used, which revision/version is used, where it came from, whether its use is permitted, whether it is available through the private/offline lifecycle, and whether it conforms to applicable accepted architecture requirements.

Core build, test, package, install, run, upgrade, rollback, recovery, and governance-verification paths MUST NOT require a public package registry, public schema registry, public artifact store, online-only dependency resolution, mandatory vendor SaaS, or another Internet-only provider as an unavoidable correctness dependency.

This constraint does not choose an exception language, package manager, lockfile technology, SBOM format, scanner, signing product, registry, artifact store, resolver, concrete provider, or concrete supply-chain/security product.

## 3. MUST

Future architecture and design MUST:

1. preserve `PYTHON-FIRST` as the default delivery direction for the scopes frozen by the Genesis Constitution and Decision Registry;
2. keep any non-default technology exception explicit, bounded to the minimum necessary scope, justified by a demonstrable need, governed under current decision authority, and traceable to accepted evidence;
3. preserve stable language-neutral semantics at cross-boundary contracts when a technology exception crosses or realizes such a boundary, in conformance with accepted `NSE-009`;
4. keep exception technology isolated enough that replacement or exit remains architecturally possible without silently redefining accepted semantic boundaries;
5. require later material exception choices that create major language/framework/provider/protocol/storage/artifact-format lock-in, high migration cost, material security/trust changes, or major compatibility commitments to follow MDE governance;
6. preserve `Technology Choice != Product Component Identity`;
7. preserve `Framework / Library != Architecture Contract`;
8. preserve `Provider != Semantic Authority`;
9. preserve `Technology Exception != Governance Exception`;
10. preserve `Technology Exception != Tenant / Organization Bypass`;
11. preserve `Technology Exception != Security / Trust Bypass`;
12. preserve `Technology Exception != Offline Correctness Bypass`;
13. preserve dependency identity, revision/version, origin/provenance, permission/license status where applicable, offline availability, and architecture-conformance evidence sufficient for later delivery verification;
14. make dependency resolution version-bounded, reproducible, auditable, and capable of being satisfied from locally controlled inputs for core private/offline lifecycle operations;
15. preserve applicable compatibility and security/vulnerability evidence for formal dependencies without selecting a particular evidence format or product;
16. keep optional public registries, vendor SaaS, Internet providers, or public artifact sources outside mandatory core correctness paths;
17. preserve enough provenance to distinguish a dependency obtained from an approved mirrored/private source from an arbitrary or unverified runtime download without making source location itself the semantic authority;
18. require future conformance evidence to demonstrate both exception containment and private/offline dependency closure.

## 4. MUST NOT

Future architecture and design MUST NOT:

1. let an exception language or framework redefine a Product Component boundary;
2. let a library API or framework model redefine an accepted Architecture Contract;
3. let a provider implementation become Semantic Authority, Source of Truth, or Actual-state Owner merely by technical placement;
4. let an exception bypass Tenant, Organization, IAM/Policy, Security/Trust, Artifact/Admission, Audit, Data/Privacy, extension/re-delivery, or offline/private requirements;
5. infer Authority, Semantic Ownership, Source of Truth, or Product Component identity from programming language, package, framework, provider, process, directory, repository, database, or deployment placement;
6. require runtime public downloads for core correctness;
7. require a public package registry, public schema registry, public artifact store, mandatory online dependency resolver, or vendor SaaS control plane for the complete core private/offline lifecycle;
8. rely on floating `latest`, unbounded mutable dependency selection, or undocumented online resolution as the only formal dependency path;
9. accept a dependency for formal delivery without enough evidence to determine its identity/revision and provenance or to evaluate applicable permission, offline-availability, compatibility, security, and architecture-conformance obligations;
10. treat an SBOM, scanner result, signature, registry record, lockfile, or other single evidence artifact as universal proof of architecture conformance by itself;
11. select an exception language, package manager, dependency resolver, SBOM format, scanner, signing product, registry, artifact store, concrete provider, concrete security product, or supply-chain product within this constraint.

## 5. Long-term Invariant

```text
Project Direction → PYTHON-FIRST
Technology Choice != Product Component Identity
Framework / Library != Architecture Contract
Provider != Semantic Authority
Technology Exception != Governance Exception
Technology Exception != Tenant / Security / Offline Bypass
Exception Scope → Explicit / Bounded / Justified / Governed / Traceable
Core Dependency Closure → Version-bounded / Reproducible / Auditable / Offline-satisfiable
Public Registry / Vendor SaaS / Online Resolver != Mandatory Core Correctness Dependency
Dependency Presence != Architecture Conformance Evidence by itself
```

Technology may evolve and bounded exceptions may exist, but accepted semantic authority and private/offline correctness MUST remain invariant.

## 6. Origin / Provenance

This constraint is derived only from current accepted Repository authority:

- Genesis Constitution §4–8 root technology facts for the five Product Components;
- Genesis Constitution §16 `Technology Direction and Controlled Exceptions`;
- Genesis Constitution §17 `Stable Language-neutral Contracts`;
- Genesis Constitution §18 `Offline / Private Deployment Correctness`;
- Genesis Constitution §23 `Supply-chain Evidence`;
- Genesis Constitution §24 `Architecture-before-Implementation Invariants`;
- `ROOT-FACT-002..005` current frozen technology direction/facts;
- `ROOT-FACT-011 — Complete private/offline delivery correctness is mandatory`;
- `ROOT-FACT-012 — Stable cross-boundary contracts are language-neutral and versioned`;
- accepted `NSE-001..012`, especially `NSE-004`, `NSE-005`, `NSE-009`, `NSE-010`, and `NSE-012`;
- GAC-EPOCH-0012 Batch 4 authorization.

No pre-Genesis package manager, lockfile, registry, artifact store, SBOM, scanner, signing product, dependency resolver, provider, security tool, or exception language is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

This constraint preserves accepted technology direction and governance boundaries and formalizes dependency-evidence obligations without choosing any exception technology or supply-chain implementation. A later material choice of exception language/framework/provider or another high-lock-in technology remains MDE-governed where applicable.

## 8. Rationale

A technology exception is safe only if it solves a bounded technical problem without acquiring semantic authority or weakening the accepted product invariants. An offline product is reproducible only if its dependencies can be identified, traced, controlled, and made available without relying on mutable public infrastructure.

The constraint therefore binds exceptions to architecture rather than allowing technology to define architecture, and it binds dependency closure to evidence rather than to one specific supply-chain tool.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **No technology exceptions ever:** rejected because the Constitution explicitly allows justified exceptions for real platform/provider needs.
- **Technology exceptions free to define local architecture:** rejected because implementation convenience cannot rewrite accepted semantics.
- **Public-registry-first dependency closure with offline best effort:** rejected because core private/offline lifecycle correctness is mandatory.
- **Controlled exceptions plus tool-neutral provenance/offline dependency evidence:** required.

Actual exception languages, package managers, resolvers, lockfile/SBOM formats, scanners, signing products, registries, artifact stores, and providers remain deferred.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- technology/language/framework/provider governance;
- Product Component and contract boundary preservation;
- supply-chain/dependency closure;
- build/test/package/install/run/upgrade/rollback/recovery lifecycle;
- provenance / license / compatibility / security evidence;
- private/offline deployment;
- extension and re-delivery;
- Shared Foundation/provider replaceability;
- compatibility / migration / conformance;
- implementation planning constraints.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** dependency/exception identity must be traceable; concrete package coordinates/identifier formats are deferred.
- **Revision / Evolution:** dependency revision/version must be bounded and auditable; version syntax/tooling is deferred.
- **Authority / Semantic Ownership:** technology/provider placement creates no semantic authority; concrete owners remain governed downstream.
- **Source of Truth / Actual-state Ownership:** library/provider/dependency presence cannot decide canonical ownership.
- **State / Lifecycle / Temporal:** dependency evidence must support the complete core private/offline lifecycle; concrete supply-chain workflow states are deferred.
- **Failure / Unknown / Indeterminate:** missing/unverifiable provenance, permission, offline availability, compatibility, security, or conformance evidence remains explicit rather than silently accepted.
- **Tenant / Organization:** accepted `NSE-001..003` remain controlling; technology exceptions cannot create bypasses.
- **Principal / Authentication / Authorization / Policy:** exception technology does not create policy authority or authorization bypass.
- **Security / Data / Privacy / Trust:** applicable security/trust evidence and boundaries remain mandatory; concrete tools/models are deferred.
- **Serialization / Representation:** no lockfile, SBOM, signature, evidence, registry, or artifact representation is selected.
- **Offline / Degraded:** accepted `NSE-004` remains controlling; dependency closure must be locally satisfiable on core paths.
- **Recovery / Reconciliation:** rollback/recovery must not require reacquisition from mandatory public infrastructure; concrete mechanisms are deferred.
- **Compatibility / Migration:** exception/provider replacement and dependency evolution must preserve accepted semantics; concrete policies are deferred.
- **Conformance:** future architecture/delivery design must verify exception containment and dependency evidence against accepted requirements.
- **Cross-boundary Dependency:** stable contract semantics precede exception/provider binding; dependency acquisition location does not become semantic authority.
- **Invariant / Decision Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner changes one or more of:

- the `PYTHON-FIRST` direction or frozen root technology facts;
- the constitutional controlled-exception rule;
- stable language-neutral cross-boundary contract requirements;
- complete private/offline lifecycle correctness;
- the requirement for dependency/provenance/license/compatibility/security evidence.

Changing package managers, dependency resolvers, SBOM formats, scanners, signing products, registries, artifact stores, mirror strategy, concrete providers, or bounded implementation libraries is not by itself a revalidation trigger.

## 13. Status

```text
NSE-015
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```