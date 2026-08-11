# ns_evermore Decision Registry — Genesis Bootstrap

## Authority Metadata

- **Document ID:** `NS-EVERMORE-DECISION-REGISTRY-0001`
- **Version:** `0.0.1`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `DECISION_REGISTRY_CANDIDATE`
- **Program / Phase:** `NGRP-001 / Z0`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`

---

## 1. Registry Rules

This registry indexes durable decisions. It is not a substitute for decision evidence.

Accepted owner decisions and accepted architecture decisions must always have an exact repository coordinate. Downstream sessions may consume only decisions whose authority and acceptance status permit consumption.

## 2. Root Inherited Facts

The following Project Owner facts are recorded as inherited and non-votable:

```text
ROOT-FACT-001  Five Product Components are fixed: ns_server, ns_runtime, ns_node, ns_agent, ns_web
ROOT-FACT-002  Python-first delivery direction
ROOT-FACT-003  Django is the root server framework fact for ns_server
ROOT-FACT-004  WebSocket-centered communication is a root fact for ns_runtime
ROOT-FACT-005  Vue 3 + TypeScript is the root fact for ns_web
ROOT-FACT-006  Native Multi-tenancy is mandatory
ROOT-FACT-007  Tenant ≠ Organization
ROOT-FACT-008  Complex/extensible Organization architecture is mandatory
ROOT-FACT-009  Knowledge/Data Foundation is located inside ns_server
ROOT-FACT-010  Shared Foundation exists outside the five Product Components and is not a sixth Product Component
ROOT-FACT-011  Complete private/offline delivery correctness is mandatory
ROOT-FACT-012  Stable cross-boundary contracts are language-neutral and versioned
ROOT-FACT-013  Definition / Artifact / Runtime are distinct governance states
ROOT-FACT-014  Source-level extension, customer secondary development, and re-delivery are product requirements
ROOT-FACT-015  Repository evidence is persistent project memory; chat/model memory is non-authoritative
ROOT-FACT-016  Independent Global Acceptance is mandatory
ROOT-FACT-017  Accepted design must be implementation-derivable before implementation planning
```

These facts are normalized in the Genesis Constitution and remain candidate until Z0 Global Acceptance promotes the Constitution.

## 3. Z0 Delegated Architecture Decisions

### Z0-DAD-001 — Governance document hierarchy

- **Question:** How shall Genesis governance artifacts be organized without changing product semantics?
- **Decision:** Use stable `docs/` roots for Constitution/indexes, with bounded subtrees for `genesis`, `governance`, `session_prompts`, `session_handoffs`, and `architecture_reviews`.
- **Classification:** `DAD`
- **Rationale:** Separates normative state, evidence, session authorization, and review artifacts while remaining repository-native.
- **Alternatives:** flat `docs/`; numeric top-level hierarchy; separate governance repository.
- **Affected Scope:** documentation navigation only.
- **Compatibility Impact:** none on runtime/product contracts.
- **Invariant Impact:** supports repository-backed continuity.
- **Revalidation Trigger:** material repository restructuring.
- **Escalation Audit:** `DAD_CONFIRMED / NO_ROOT_SEMANTIC_CHANGE`.

### Z0-DAD-002 — Governance version format

- **Decision:** Governance/design document revisions use explicit `0.0.x` version suffixes during Genesis pre-1.0 evolution; identity is Document ID + version, never filename alone.
- **Classification:** `DAD`
- **Alternatives:** dates; monotonic integers; Git SHA only.
- **Rationale:** readable revisions plus immutable Git evidence.
- **Revalidation Trigger:** project-wide release/versioning policy is later accepted.
- **Escalation Audit:** `DAD_CONFIRMED`.

### Z0-DAD-003 — Stable governance namespaces

- **Decision:** Use `GAC-EPOCH-####` for global epochs, `GAC-TR-####` for ledger transitions, `NSE-###` for architecture constraints, `Zx-DAD-###` for phase-scoped DADs, and `Zx-MDE-###` for phase-scoped MDEs unless a later accepted governance revision supersedes the namespace.
- **Classification:** `DAD`.
- **Rationale:** stable, human-auditable coordinates.
- **Escalation Audit:** `DAD_CONFIRMED`.

### Z0-DAD-004 — Current-state versus historical-ledger split

- **Decision:** Maintain a small current Global Architecture State and separate append-oriented Global Architecture Ledger; historical narrative MUST NOT accumulate in the current-state file.
- **Classification:** `DAD`, directly implementing a root governance requirement.
- **Alternatives:** single monolithic history/state document; Git history only.
- **Escalation Audit:** `DAD_CONFIRMED`.

### Z0-DAD-005 — Explicit Current Required Read Set artifact

- **Decision:** Persist a dedicated `Current Required Read Set` document and regenerate it at formal state transitions.
- **Classification:** `DAD`.
- **Rationale:** enables minimum-sufficient fresh-session recovery.
- **Alternatives:** implicit links in State; read all docs.
- **Escalation Audit:** `DAD_CONFIRMED`.

### Z0-DAD-006 — Session authorization and handoff as durable artifacts

- **Decision:** Each bounded formal session requires a repository-backed authorization prompt and handoff package. Chat text is delivery only.
- **Classification:** `DAD`, implementing a root governance rule.
- **Escalation Audit:** `DAD_CONFIRMED`.

### Z0-DAD-007 — Constraint index starts empty

- **Decision:** Bootstrap `NSE-###` and record schema in Z0 while keeping `ACTIVE_NSE = NONE` until a separately authorized Constraint Derivation phase.
- **Classification:** `DAD`.
- **Rationale:** satisfies namespace bootstrap without leaking Architecture Constraint design.
- **Escalation Audit:** `DAD_CONFIRMED`.

### Z0-DAD-008 — Working-state reset model

- **Decision:** Global Working State stores provisional context only and is reset/rebased against each new Global State Epoch after formal acceptance/authorization transitions.
- **Classification:** `DAD`.
- **Escalation Audit:** `DAD_CONFIRMED`.

### Z0-DAD-009 — Implementation governance before implementation planning

- **Decision:** Z0 establishes IWP/Codex governance schemas only; it MUST NOT generate an Implementation Master Plan or any IWP.
- **Classification:** `DAD`.
- **Escalation Audit:** `DAD_CONFIRMED`.

### Z0-DAD-010 — Pre-Genesis history is non-normative by default

- **Decision:** Pre-Genesis repository artifacts are historical references only unless explicitly admitted by a later authorized, provenance-aware derivation/review.
- **Classification:** `DAD` implementing the Constitution's no-hidden-inheritance rule.
- **Alternatives:** blanket inheritance; blanket deletion/ignore.
- **Escalation Audit:** `DAD_CONFIRMED / NO_PRODUCT_SEMANTIC_CHANGE`.

## 4. Z0 MDE Register

```text
Open Z0 MDE → 0
Closed Z0 MDE → 0
Unpersisted Owner Decision → 0
```

No Z0 governance implementation decision changed root product meaning, acceptance authority, decision authority, continuity source of truth, or fixed component topology.

## 5. Downstream Consumption Rule

The above DADs may be consumed only after Z0 is globally accepted. Until then their status is:

```text
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```
