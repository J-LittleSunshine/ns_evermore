# NGRP-001 — Foundation Contract Design / Batch 1 DAD Evidence

## Authority Metadata

- Original Producing Scope: `FOUNDATION_CONTRACT_DESIGN_ONLY / BATCH_1 / FOUNDATION_STABLE_ENTRY_AND_REUSABLE_CONTRACT_SEMANTICS_SYNTHESIS`
- Current Correction Scope: `FOUNDATION_CONTRACT_DESIGN_ONLY / BATCH_1 / CROSS_CONTRACT_DEPENDENCY_SEMANTICS_CORRECTION_ONLY`
- Repository / Branch: `J-LittleSunshine/ns_evermore` / `architecture/ns-evermore-genesis-0.0.1`
- Original Producing Entry HEAD: `e36d4c8cb48234983d4acca8ef6674025f711ded`
- Correction Entry HEAD: `0ebd6bc613be2278b9f1cc9d15a802bfeefc0ab0`
- Current Global State: `GAC-EPOCH-0034`
- Prior GAC Review Result: `CORRECTION_REQUIRED`
- Original Primary Candidate Commit: `bfc9aa784196b53a28244ae8f78b56d62fad6f61`
- Authority: bounded producing-session DAD/correction only; Global Acceptance not claimed.

All decisions are derived from globally accepted Shared Foundation Architecture, Project Architecture, Z3 boundaries, Runtime Responsibility Architecture, applicable Owner decisions and `NSE-012`. The current correction changes only cross-Contract dependency typing and the proof of semantic-definition acyclicity. It does not move Product Authority, Source of Truth, Runtime Actual-state ownership, Tenant/Principal/Policy/Trust semantics, accepted Foundation capability boundaries, Contract identity, Stable Entry semantics, Provider design or Module design.

---

## FCD-B1-DAD-001 — Contract Identity / Decomposition

**Decision:** the 14 accepted Foundation capabilities resolve into 15 material semantic Contracts. Capability 12 (`Secret Reference / Sensitive-data Redaction`) resolves into two Contract subjects — `Secret Reference Contract` and `Sensitive-data Redaction Contract` — because reference/material handling has conditional material-source conformance pressure while disclosure/redaction has a distinct sink/presentation obligation. They remain one accepted capability and one capability-level Stable Entry pressure.

All other accepted capability cohesion decisions remain unchanged, including Telemetry+Health as one Contract and separate Temporal, Correlation, Status and Governed Context Contracts.

**Why DAD:** Contract semantic decomposition is the exact authorized original scope and changes no MDE dimension.

**Consequence:** `14 capabilities / 15 Contracts / 100% coverage / orphan Contract 0 / new capability 0`.

**Non-implications:** Contract count does not imply module/package/interface/provider count.

**Revalidate:** if a Contract becomes a new Foundation capability, absorbs a non-Foundation domain or requires changing an accepted capability boundary.

---

## FCD-B1-DAD-002 — Fourteen Stable Entry Semantics

**Decision:** all 14 accepted capabilities receive one capability-level Stable Entry semantic boundary. Stable Entry is the authority-neutral consumer dependency point, not an import path, function, class, endpoint, service or provider registry.

Capability 12's one Stable Entry is satisfied by its two cohesive Contract subjects; the Contract split does not create another capability entry.

**Why DAD:** `SFA-B1-DAD-010` accepted 14 Stable Entry pressures and the original Contract Design phase was authorized to close their semantics.

**Result:** `Stable Entry Semantic Coverage → 14 / 14`.

**Revalidate:** if a Stable Entry becomes provider-specific or gains Product authority.

---

## FCD-B1-DAD-003 — Operation / Result / Evidence Semantic Pattern

**Decision:** operation/query-like Contracts close only the applicable semantics among `Intent`, `Accepted Input`, `Result`, `Technical Evidence`, `Failure Evidence`, `Uncertainty`, `Provenance`, `Freshness/temporal applicability` and legitimate `Partial Result` semantics.

This is a review pattern, not a universal request/response DTO, message envelope or schema.

**Preservation:** Foundation success proves only the bounded mechanical result; it never automatically proves business success, Trust, Policy permit, Artifact Acceptance, Admission or canonical Actual-state.

**Why DAD:** Project/SFA/Runtime upstream requires stable result/evidence/failure/provenance semantics without physical representation design.

**Revalidate:** if the pattern is promoted into one universal message Contract or evidence is allowed to create Product authority.

---

## FCD-B1-DAD-004 — Common Status Extension + Contract Conformance

**Decision:** `Technical Status & Uncertainty Contract` is the single semantic definition of the accepted common technical uncertainty vocabulary. Other Contracts may define cohesive local outcomes such as cache `HIT/MISS` but may not redefine common meanings.

Permanent non-collapse includes:

```text
UNKNOWN != FAILED != SUCCESS
UNAVAILABLE != DENIED
UNREACHABLE != UNAUTHORIZED
STALE != CURRENT
UNVERIFIED != Trusted
```

Per material Contract, conformance is `CONFORMING`, `NON_CONFORMING` or `UNKNOWN CONFORMANCE`, with explicit `UNSUPPORTED CAPABILITY/CASE` where bounded support is legitimate. `PARTIAL_CONFORMANCE` is not a final per-Contract status; aggregate reports may describe partial coverage across multiple Contracts without weakening individual Contract conformance.

**Why DAD:** this closes common reusable Contract semantics and independent verification without creating a universal domain state machine.

**Revalidate:** if common status becomes domain/authorization authority or partial conformance masks violation of mandatory semantics.

---

## FCD-B1-DAD-005 — Revision / Evolution / Migration Classification

**Decision:** Contract stable identity is the semantic subject plus its accepted Foundation capability ownership relationship, independent of provider/representation. A Contract Revision is semantic evolution under the same identity; no version syntax is selected.

Changes use the accepted classes:

```text
CONFORMANCE_ONLY_IMPLEMENTATION_CHANGE
COMPATIBLE_EVOLUTION
EXPLICIT_MIGRATION_REQUIRED
ARCHITECTURE_REVALIDATION_REQUIRED
OWNER_MDE_REQUIRED
```

Compatible evolution must preserve existing supported meaning, obligations, guarantees/non-guarantees, status meanings, Authority/SoT/Actual-state neutrality, security/privacy, offline/private correctness and provider/representation independence. State/interpretation transitions that cannot remain transparent require explicit migration. Owner-reserved changes remain MDE.

**Why DAD:** direct derivation from Project Architecture, `NSE-009`, `NSE-012` and accepted SFA replaceability pressure.

**Non-implications:** no SemVer, Git tag, package version or schema-version field.

---

## FCD-B1-DAD-006 — Secret Reference / Redaction Contract Separation

**Decision:** within accepted capability 12:

```text
Secret Reference Contract
→ reference-vs-material distinction
→ scope/provenance and bounded material-resolution evidence

Sensitive-data Redaction Contract
→ sensitivity/disclosure/redaction mechanics
→ ordinary sink/presentation non-disclosure obligations
```

Permanent rules:

```text
Secret Reference != Secret Material
Reference Possession != Permission to Resolve
Successful Resolution != Trust
Redaction != Authorization
Provider/Sink Success != Permission to Disclose
```

Redaction may conditionally consume the reference/material distinction when secret references or secret material are present. This is an application-time semantic use, not a semantic-definition dependency. Secret Reference does not require Redaction to define reference identity, and Redaction does not require Secret Reference to define generic sensitivity/redaction semantics.

**Why DAD:** accepted `Z2-MDE-015`, `Z2-MDE-016` and `SFA-B1-DAD-007` already establish the one capability while leaving material custody and generic cryptography outside Foundation.

**Non-implications:** no material store, credential/reference format, cryptography, rotation or redaction implementation is selected; deferred generic cryptographic/evidence-verification helpers remain deferred.

**Revalidate:** if Foundation gains Trust/Privacy/Policy authority or reference/material semantics collapse.

---

## FCD-B1-DAD-007 — Typed Cross-Contract Dependency Semantics and Acyclic Definition Reuse

### Correction reason

The original Candidate and evidence used the single word `dependency` for materially different relationships. In particular, C11/C12/C13 contained bidirectional application/security relationships while the same evidence claimed an acyclic semantic dependency graph. `GAC-EPOCH-0034` requires those relationships to be typed so recursive semantic definition and ordinary composition are not conflated.

### Dependency taxonomy

Four dependency types are normative at Foundation Contract semantic level:

```text
SEMANTIC_DEFINITION_DEPENDENCY / SDD
→ Contract A imports normative semantic definitions owned by Contract B.
→ A's own semantic definition or baseline conformance cannot be completely evaluated
  without the imported B meaning.
→ ONLY SDD edges participate in recursive semantic-definition cycle analysis.

CONDITIONAL_APPLICATION_SEMANTIC_USE / CASU
→ Contract A may consume Contract B semantics only when a bounded application case contains
  the relevant subject/context.
→ A's stable identity and baseline semantic definition do not require B.
→ The edge is evaluated only for the declared application case.

SECURITY_DISCLOSURE_COMPOSITION_DEPENDENCY / SDCD
→ A bounded output/disclosure path governed by Contract A must compose with Contract B's
  disclosure/redaction semantics before an ordinary sink/presentation boundary receives
  protected content where B applies.
→ This is a semantic composition/order obligation, NOT a Module/import/provider design and
  NOT an SDD edge.

EXTERNAL_AUTHORITY_CONTEXT_DEPENDENCY / EACD
→ Contract A requires authoritative meaning/permission/context from a Product/domain authority
  outside Shared Foundation.
→ Foundation may carry/reference that context but does not create, validate as final authority,
  or absorb the external authority.
→ EACD is not a Foundation Contract semantic-definition edge.
```

### C11 / C12 / C13 closure

```text
C11 Governed Context Propagation
  SDD  → C04 Temporal & Freshness
         C10 Technical Status & Uncertainty
  SDCD → C13 Sensitive-data Redaction
         ONLY when C11-carried context/evidence is sensitive and crosses an ordinary
         disclosure/sink/presentation boundary
  EACD → Tenant / Organization / IAM-Principal / Policy / Trust authorities
  NO SDD → C12 or C13

C12 Secret Reference
  SDD  → C10 Technical Status & Uncertainty
  CASU → C04 Temporal & Freshness
         when temporal applicability/freshness is part of the bounded reference/resolution case
  CASU → C11 Governed Context Propagation
         when applicable governance context is transported through C11 for the bounded case
  SDCD → C13 Sensitive-data Redaction
         before secret-reference metadata/evidence or material-sensitive output crosses an
         ordinary disclosure/sink/presentation boundary where C13 applies
  EACD → applicable Tenant / Principal / Policy / Trust / secret-material custody authorities
         for permission to resolve/use and semantic validity
  NO SDD → C11 or C13

C13 Sensitive-data Redaction
  SDD  → C10 Technical Status & Uncertainty
  CASU → C11 Governed Context Propagation
         when owner-provided disclosure/governance context is supplied through C11
  CASU → C12 Secret Reference
         only when the input case contains secret-reference/material semantics and the
         C12 reference/material distinction is relevant
  CASU → C04 / C05
         only when temporal/provenance evidence must be preserved in redacted output
  EACD → applicable Policy / Privacy / Trust / semantic owner for classification,
         disclosure permission and owner-provided constraints
  NO SDD → C11 or C12
```

C11 and C13 therefore have a bidirectional **composition/use** relationship (`C11 --SDCD→ C13`, `C13 --CASU→ C11`) but no mutual semantic-definition relationship. Likewise, C12 and C13 may interact bidirectionally at application time (`C12 --SDCD→ C13`, `C13 --CASU→ C12`) without either Contract recursively defining the other.

### Semantic-definition DAG proof

The correction-relevant semantic-definition graph is:

```text
C10 Technical Status & Uncertainty
  ↑
C04 Temporal & Freshness
  ↑
C11 Governed Context Propagation

C12 Secret Reference ─────────────→ C10
C13 Sensitive-data Redaction ─────→ C10
```

Arrows mean `SDD consumer → imported semantic definition` conceptually; the vertical layout is only illustrative. There is no `SDD` edge among C11, C12 and C13 themselves.

Therefore:

```text
Recursive Semantic Definition among C11/C12/C13 → NONE
Semantic-definition Cycle Creating Ambiguity → 0
Contract Identity Ambiguity from Dependency Typing → 0
```

### Independent conformance proof

- **C11 base conformance** is evaluated from context-carriage/non-collapse, provenance/scope/applicability, isolation and C04/C10 imported meanings. C13 is required only for a supported disclosure composition case; C11 does not need C13 to define context identity or carriage semantics.
- **C12 base conformance** is evaluated from Reference != Material, scope/provenance, resolution-evidence non-authority, provider neutrality and C10 imported meanings. C11/C13 are only conditional composition/use obligations for bounded cases.
- **C13 base conformance** is evaluated from sensitivity/redaction/non-disclosure semantics plus C10 imported meanings using owner-provided disclosure constraints abstractly. It does not require C11 as the only context carrier and does not require C12 unless the bounded input contains secret-reference/material semantics.
- A realization claiming support for a CASU or SDCD case must additionally prove that composition. Failure of an applicable composition case is non-conformance for that declared supported case; it does not turn the relationship into recursive semantic definition.
- EACD conformance proves that Foundation consumes/preserves external authority context without becoming that authority; it does not require implementing the external authority inside Foundation.

### Preservation and non-implications

Common semantics remain defined once and reused. `Technical Status & Uncertainty` remains the common uncertainty root; `Temporal & Freshness` remains the temporal/freshness definition; `Operation Correlation & Provenance` remains separate from `Governed Context Propagation`.

This typing is semantic only. It does **not** determine:

```text
package imports
Module dependency graph
class/interface dependency
provider graph
registry/factory structure
runtime call order beyond the stated semantic disclosure precondition
process/service topology
deployment topology
```

**Why DAD:** dependency typing and Contract-cohesion proof are directly inside the current correction scope and change no Owner-reserved dimension.

**Revalidate:** if an SDD cycle is introduced, a composition edge is promoted into Contract identity, Foundation absorbs an external Authority, or a generic Foundation Core/God Contract is introduced.

---

## FCD-B1-DAD-008 — Provider Conformance / Replaceability Pressure

**Decision:** future providers for the 10 accepted provider-bearing pressures conform only by preserving the applicable Foundation Contract's consumer-visible semantics, failure/support mapping, Authority/SoT/Actual-state neutrality, security/privacy obligations, offline/private path and migration visibility.

Replacement is classified as:

```text
same Contract semantics and no required state transition
→ CONFORMANCE_ONLY_IMPLEMENTATION_CHANGE

compatible semantic evolution
→ COMPATIBLE_EVOLUTION

explicit provider/data/reference/resource transition required
→ EXPLICIT_MIGRATION_REQUIRED

stable Contract / neutrality / offline baseline changes
→ ARCHITECTURE_REVALIDATION_REQUIRED

Owner-reserved authority/trust/major identity/high-lock-in changes
→ OWNER_MDE_REQUIRED
```

Provider-specific defaults, optional behavior and failure conventions do not become universal Foundation semantics by placement.

**Why DAD:** provider-conformance pressure is required by Contract Design; Provider interface/selection/lifecycle is explicitly forbidden.

**Non-implications:** `Provider API != Foundation Contract`; no provider registry, interface, factory, fallback, selection or default provider is designed.

**Revalidate:** if a provider becomes semantic identity/Authority, mandatory public dependency or major lock-in.

---

# Correction / DAD Audit Summary

```text
Persisted DAD → FCD-B1-DAD-001..008
Corrected DAD → FCD-B1-DAD-007
DAD Count → 8
Dependency Types → SDD / CASU / SDCD / EACD
Recursive Semantic Definition among C11/C12/C13 → NONE
Semantic-definition Cycle Creating Ambiguity → 0
Independent Contract Conformance → PROVEN FOR C11 / C12 / C13
MDE Dimension Changed → 0
New MDE → 0
Open MDE → 0
Unpersisted Owner Decision → 0
Authority Transfer → 0
SoT Transfer → 0
Actual-state Ownership Transfer → 0
New Foundation Capability → 0
Shared Foundation Architecture Reopen → NO
Major Provider/Protocol/Storage/Representation Lock-in → 0
Material Offline Fail-policy Selection → 0
Foundation Module Design Leakage → 0
Foundation Provider Design Leakage → 0
Component Internal Design Leakage → 0
Implementation-defined Architecture Escape → 0
Global Acceptance → NOT CLAIMED
```

## Status / Stop Rule

```text
NGRP-001 Foundation Contract Design / Batch 1 Correction
→ COMPLETED / AWAITING_GLOBAL_REVIEW

Next-phase Authorization
→ NONE

STOP
→ RETURN TO GLOBAL ARCHITECTURE COORDINATOR
```
