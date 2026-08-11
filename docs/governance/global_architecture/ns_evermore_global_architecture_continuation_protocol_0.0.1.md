# ns_evermore Global Architecture Continuation Protocol

## Authority Metadata

- **Document ID:** `NS-EVERMORE-GACP-0001`
- **Protocol ID:** `GACP-001`
- **Version:** `0.0.1`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `GLOBAL_CONTINUITY_PROTOCOL_CANDIDATE`
- **Program / Phase:** `NGRP-001 / Z0`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`

---

## 1. Purpose

`GACP-001` defines the mandatory recovery and drift-reconciliation procedure for every fresh Global Architecture Coordinator session.

The protocol exists because chat context and model memory are non-authoritative and may disappear.

## 2. Mandatory Recovery Sequence

Before any design, acceptance, correction, or authorization action, a new Global Architecture Coordinator MUST execute in order:

```text
1. Resolve repository and fetch actual branch HEAD.
2. Read current Constitution.
3. Read this Continuation Protocol.
4. Read current Global Architecture State.
5. Resolve the commit containing the State document.
6. Compare:
   State Verified Through HEAD
   → State Document Commit
   → Actual Branch HEAD.
7. Inspect every commit and changed file after State Verified Through HEAD.
8. Classify every delta as one of:
   EXPECTED_PHASE_EVIDENCE
   EXPECTED_GOVERNANCE
   OWNER_DECISION_EVIDENCE
   WORKING_CHECKPOINT
   UNAUTHORIZED_PROGRESSION
   UNEXPLAINED_DRIFT
9. Read Global Architecture Working State.
10. Read Current Required Read Set.
11. Read any additional artifact required by the read set.
12. Reconstruct:
    Current Baseline
    Current Phase
    Current Authorization
    Open MDE
    Pending Owner Decisions
    Blocking Items
    Known Drift
    Candidate vs Normative artifacts
    Unique Next Legal Action.
13. Report recovered state explicitly.
14. Only then begin authorized work.
```

If recovery is incomplete or inconsistent:

```text
DO NOT DESIGN
→ DRIFT / CONTINUITY RECONCILIATION
```

## 3. State Coordinate Semantics

The Global State file SHALL contain:

- Current Global State Epoch;
- Current Branch;
- `State Verified Through HEAD` — latest repository commit whose state/evidence has been reconciled by the State contents;
- Current Constitution;
- Current Constraint Baseline;
- Current Architecture Revision;
- Current Accepted Decisions;
- Current Registries;
- Last Globally Accepted Phase;
- Current Authorized Phase and Scope;
- Open MDE;
- Unpersisted Owner Decisions;
- Blocking Items;
- Known Drift;
- Current Required Read Set;
- Unique Next Legal Action.

The commit that writes the State file may be newer than `State Verified Through HEAD`. That State-document commit is itself expected governance. A new session must resolve the State document commit and then inspect only later deltas, if any.

## 4. Delta Classification

### EXPECTED_PHASE_EVIDENCE
Artifacts explicitly allowed by the currently authorized bounded session.

### EXPECTED_GOVERNANCE
State, Working State, Ledger, Read Set, review, handoff, authorization, or registry maintenance consistent with the current phase.

### OWNER_DECISION_EVIDENCE
Repository evidence persisting a Project Owner MDE choice.

### WORKING_CHECKPOINT
Explicitly provisional evidence that does not claim acceptance or authorization.

### UNAUTHORIZED_PROGRESSION
Work belonging to a phase not explicitly authorized.

### UNEXPLAINED_DRIFT
Any commit/file modification not reconcilable with current authority or evidence.

Either of the final two classifications blocks further architecture work.

## 5. Current Required Read Set Rule

The Current Required Read Set SHALL contain the minimum sufficient context with no semantic loss. It SHOULD default to current authoritative/candidate documents only and expand into historical evidence only for reopen, conflict, historical divergence, evidence ambiguity, or cross-phase collision.

After every formal State Transition, the read set MUST be re-evaluated and persisted.

## 6. Global Working State Rule

Working State contains only provisional context whose loss could cause continuation error. It MUST distinguish provisional findings from accepted facts. After formal acceptance/authorization, Working State is reset/rebased against the new Global State Epoch.

## 7. Ledger Rule

The Global Architecture Ledger is append-oriented. It records historical transitions and MUST NOT be used as the primary current-truth source.

Each transition records:

```text
Transition ID
Previous State
New State
Evidence File
Evidence Commit
Affected Artifact
Result
```

## 8. Epoch Rule

Formal Acceptance, Authorization, Correction Closure, Repair, Global Closure, or other major governance transition advances a monotonic repository-backed `GAC-EPOCH-####`.

## 9. Independent Acceptance Recovery

When a bounded design session reports `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`, the new Global Coordinator must independently verify:

- Git evidence and branch coordinate;
- authorization scope;
- decision classification;
- owner-decision persistence;
- semantic resolution depth;
- constraint/root-invariant preservation;
- authority/source-of-truth ambiguity;
- Tenant/Organization non-collapse;
- dependency/invariant integrity;
- provenance and hidden inheritance;
- downstream design leakage;
- drift.

Only after this review may the GAC accept, require correction, or reject.

## 10. No Automatic Next Phase

Even after Global Acceptance:

```text
Accepted current phase
≠ next phase authorized
```

The GAC must reassess remaining pressure and explicitly authorize exactly one bounded next phase.

## 11. Fresh-session Recovery Acceptance Criterion

A fresh GAC session passes recovery only when Repository evidence alone identifies without material ambiguity:

```text
Project Identity
Root Product Constraints
Five Product Components
Tenant / Organization Rules
Technical Defaults
Current Program Phase
Current State Epoch
Current Branch / HEAD coordinate
Current Authorization
Current Required Read Set
Blocking Items
Open Decisions
Candidate vs Normative artifacts
Known Drift
Unique Next Legal Action
```

Failure of any material item means continuity is incomplete and design must not proceed.