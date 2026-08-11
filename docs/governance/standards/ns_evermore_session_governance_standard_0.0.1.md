# ns_evermore Session Governance Standard

## Authority Metadata

- **Document ID:** `NS-EVERMORE-SESSION-GOV-STANDARD-0001`
- **Version:** `0.0.1`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `SESSION_GOVERNANCE_STANDARD_CANDIDATE`
- **Program / Phase:** `NGRP-001 / Z0`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`

---

## 1. Rule

Every formal design, review, correction, planning, or implementation session must be bounded by durable repository evidence. Chat prompts are delivery mechanisms only.

## 2. Session Authorization Prompt Standard

Every formal session authorization prompt MUST record:

```text
Session Prompt ID
Program / Phase ID
Repository
Branch
Authorization Scope
Mandatory Read Set
Entry Gate
Authorized Entry HEAD or resolution rule
Allowed Work
Forbidden Work
Decision Governance
Required Audits
Exit Gate
Required Handoff Fields
Stop Rule
```

### 2.1 Entry Gate

A session MUST NOT begin substantive work until it can establish:

- actual branch HEAD;
- recovered Global State;
- verified authorization;
- no blocking unexplained drift;
- required read set consumed;
- open MDE/pending owner-decision status known.

### 2.2 Scope Rule

Authorization must be bounded. A session may not infer adjacent scope merely because it appears logically next.

### 2.3 Forbidden Progression

A session must stop rather than enter a later phase, even if the current phase appears complete.

## 3. Session Handoff Package Standard

Every bounded session MUST persist a handoff package before stopping.

Required fields:

```text
Session / Phase ID
Authorization Scope
Recovered Global State
Authorized Entry HEAD
Evidence HEAD
Evidence Commits
Changed Files
Decisions Created
DAD Summary
MDE Summary
Owner Decisions
Accepted Upstream Consumed
Candidate Artifacts
Preserved Invariants
New Provisional Invariants
Open MDE
Unpersisted Owner Decisions
Blocking Items
Unexpected Drift
Unauthorized Progression
Audit Results
Deferred Scope
Acceptance Recommendation
Remaining Scope
STOP Condition
```

The handoff is evidence, not acceptance.

## 4. Review / Acceptance Separation

The producing design session MUST NOT mark its own design `GLOBAL_ACCEPTED / NORMATIVE`.

The Global Architecture Coordinator must independently recover repository state and inspect the handoff, Git deltas, decision registry, and substantive artifacts.

## 5. Correction Session Rule

When GAC returns `CORRECTION_REQUIRED`, a correction session must have its own repository-backed authorization prompt, exact correction scope, entry coordinate, required evidence, and stop rule. It MUST NOT silently expand into a new design batch.

## 6. Owner Decision Session Rule

An MDE session processes one material decision at a time. The decision is not consumable downstream until a durable repository decision record exists.

## 7. Required Git Evidence

A handoff must identify exact commit coordinates sufficient to reconstruct:

```text
entry baseline
session evidence
post-session governance updates
```

Any difference between declared and actual repository state triggers drift reconciliation.

## 8. Fresh-session Principle

A brand-new session with no prior chat history is considered valid only if it can recover its full authorized responsibility from Repository artifacts alone.