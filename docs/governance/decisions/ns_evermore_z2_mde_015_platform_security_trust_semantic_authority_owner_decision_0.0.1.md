# NGRP-001 Z2 MDE-015 — Platform Security / Trust Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-015`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Decision Entry HEAD:** `566432a9a6cc45506419bb268aa7ea1b971ed4a7`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; `Z2-MDE-001..014`; current Z2 Batch 1 authorization
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final platform-level **Security / Trust Semantic Authority** for `ns_evermore`?

This decision concerns the authoritative platform meaning and governance of trust/security states such as trusted, untrusted, revoked, unknown and indeterminate, together with platform interpretation of trust relationships and trust/security evidence.

It does not choose TLS/mTLS, PKI, CA hierarchy, KMS, cryptography libraries, certificate formats, signature algorithms, secret stores, network-security topology, sandbox technology, IAM authentication providers, Policy engines, Artifact signing formats, or concrete trust stores.

## 2. Classification

```text
Classification
MDE

Reason
Security / Trust Authority is explicitly Project-Owner-reserved under Unified Governance.
It materially affects cross-component trust semantics, Artifact/Admission governance, extension/re-delivery, offline/private correctness and security evolution.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` owns unified Platform Security / Trust Semantic Authority

`ns_server` is the final platform semantic authority for Security / Trust meaning and governance. Other components may produce evidence, enforce decisions, consume trust context or mediate technical security capabilities without gaining platform Trust Authority by execution, communication, hosting, provider usage or physical placement.

### B — Federated Security / Trust Authorities

Multiple Product Components or capability domains each own final trust semantics for their bounded areas, requiring explicit cross-authority composition, precedence, revocation and conflict semantics.

### C — Shared Foundation owns Platform Security / Trust Authority

Shared Foundation becomes the final Security / Trust semantic authority consumed by all five Product Components, materially increasing Foundation responsibility beyond provider-neutral reusable capability mediation.

## 4. Recommendation Presented

`A — ns_server owns unified Platform Security / Trust Semantic Authority`.

Rationale: platform trust is a governance semantic that must remain independent from transport, local execution, provider behavior and Shared Foundation mediation. `ns_server` already owns the accepted native Tenant/IAM/Policy/Artifact/Admission governance authorities, while this decision preserves those domains as distinct authorities rather than collapsing them into one concept.

## 5. Project Owner Decision

```text
Selected Option
A

Platform Security / Trust Semantic Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY consume the following Owner-decided facts:

```text
ns_server
→ owns platform Security / Trust Semantic Authority

ns_runtime
→ may enforce/consume applicable trust context in communication and runtime coordination
→ does not gain Security / Trust Authority by transport, routing, connection management or runtime mediation

ns_node
→ may enforce local security decisions, produce local security/effect evidence and exercise accepted trust context
→ does not gain Security / Trust Authority by local execution, locality, possession or offline operation

ns_agent
→ may consume trust/security context for models, providers, tools and Agent runtime
→ does not gain platform Security / Trust Authority by provider interaction or AI execution

ns_web
→ may provide security/governance administration surfaces
→ does not gain Security / Trust Authority by UI editing or presentation

Shared Foundation
→ may later provide reusable cryptographic, secret or security primitives under stable provider-neutral contracts
→ does not gain Security / Trust Authority through reuse, mediation, storage, transport or provider placement
```

## 7. Authority Separation

This decision permanently preserves:

```text
Security / Trust Authority
!= Tenant Authority
!= IAM Authority
!= Policy Authority
!= Artifact Acceptance Authority
!= Execution Admission Authority
!= Runtime Coordination Authority
!= Local Execution Authority
!= Agent Semantic Authority
!= Data / Knowledge Authority
```

These authorities MAY consume evidence or decisions from one another where later accepted architecture defines such dependencies, but invocation/consumption does not transfer semantic ownership.

## 8. Evidence / Decision Separation

The following non-equivalences are mandatory downstream:

```text
Cryptographically Valid != Platform Trusted
Authenticated != Authorized
Policy Allowed != Artifact Accepted
Policy Allowed != Execution Admitted
Signed != Accepted Artifact automatically
Hosted != Trusted
First-party != Trusted automatically
Connection Established != Trust Authority
Local Success != Security Authority
Provider Validation != Platform Trust Decision automatically
```

Technical evidence may support a trust decision, but technical validity or provider placement does not itself become the platform trust decision.

## 9. Offline / Private Implications

Offline, local or degraded operation MUST preserve the same platform Security / Trust semantics.

```text
Loss of Connectivity != Trust Grant
Offline Execution != Trust Authority
Local Cache / Local Trust Evidence != Platform Trust SoT automatically
```

Later authorized design may establish bounded pre-issued trust/security evidence, revocation knowledge, freshness/expiry semantics or degraded handling, but any material fail-open/fail-closed policy remains separately MDE-governed.

## 10. Extension / Provider / Foundation Implications

```text
Extension Origin != Trust
Source Possession != Trust
Provider Identity != Trust Authority
Provider API != Trust Contract
Shared Foundation Mediation != Trust Authority
```

First-party, third-party, customer-private, source-level and re-delivered extensions remain subject to the same accepted trust/security governance. Provider replacement must not silently redefine platform trust meaning.

## 11. Failure / Unknown / Indeterminate Obligations

Later authorized architecture must preserve explicit conditions for:

```text
trusted
untrusted
revoked
unknown
indeterminate
stale trust evidence
missing trust evidence
conflicting trust evidence
unverifiable trust evidence
```

A missing, stale, conflicting or unverifiable condition MUST NOT be silently coerced to trusted merely because execution is local, a connection succeeded, a provider returned success, or an artifact is present.

## 12. Constraint Preservation

This decision preserves:

- `NSE-001..004` Tenant / Organization and offline invariants;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` cross-domain authority non-transfer;
- `NSE-007` Definition / Artifact / Runtime separation;
- `NSE-008` local source/effect accountability without local authority escalation;
- `NSE-009` representation-independent stable contracts;
- `NSE-010` extension / re-delivery governance preservation;
- `NSE-011` bounded external Source-of-Truth preservation;
- `NSE-012` Shared Foundation provider replaceability and authority neutrality;
- `NSE-014` commercial/distribution optionality;
- `NSE-015` controlled technology exception containment;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 13. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Responsibility / Authority / SoT Matrix;
- Cross-component Semantic Dependency Topology;
- later IAM / Policy / Artifact / Admission / Security Architecture;
- later Runtime / Node / Agent trust and enforcement design;
- later Shared Foundation security/cryptographic capability design;
- later extension/re-delivery and offline/private design.

No later phase is authorized by this decision.

## 14. Revalidation Trigger

Revalidation is required if the Project Owner later changes one or more of:

- Platform Security / Trust Semantic Authority away from `ns_server`;
- the separation between Security/Trust and IAM/Policy/Artifact/Admission authorities;
- the rule that provider/transport/locality/hosting does not create trust authority;
- the accepted offline/private governance baseline;
- the role of Shared Foundation as a non-Product-Component reusable capability layer.

Changes in PKI, certificate, KMS, cryptography, secret-store, transport, provider, network, sandbox or deployment technology do not by themselves revalidate this decision.

## 15. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Foundation Contract/Module/Provider Design, Implementation Planning, IWP or coding.
