# ns_evermore Decision Registry — Current Revision

- Version: `0.0.41`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.40`

All accepted normative decisions and baselines in Decision Registry `0.0.40` remain in force unless explicitly refined below.

---

# Runtime / Domain Stable Contract Design — Batch 1 Acceptance

Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_1_global_acceptance_0.0.1.md`

Accepted normative correction evidence:

```text
Candidate 0.0.2
→ b728069a4f1855e9ebccdffe957c070986d79655

DAD 0.0.2
→ c60cc6645384b4162d2b0bbcc3bb6d7b107ede61

Review / Audit 0.0.2
→ cb773428ccbfd274ae8d1c244af129c323bff080

Handoff 0.0.2 / Correction Final HEAD
→ 8a83248c7ddb20a6ed11bcdc375162188d90ceeb
```

```text
Runtime / Domain Stable Contract Design / Batch 1
→ GLOBAL_ACCEPTED

Accepted Batch-1 Stable Contracts
→ 6

RCP-01 — Governance Context
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-02 — Admission Evidence
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-03 — Presence
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-04 — Node Readiness
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-19 — Desired / Applied Config
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-24 — Human / SDK Intent
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL
```

Remaining RCP stable-contract design remains downstream through Batches 2-5. This revision does not declare `RCP-01..24` full closure or Stable Contract Design exhaustion.

---

# Accepted Batch-1 Hard Contract Dependency Baseline

Notation:

```text
A → B
→ Contract A's semantic definition depends on Contract B's semantic definition
```

Accepted CSDD graph:

```text
RCP-02 → RCP-01
RCP-03 → RCP-01
RCP-19 → RCP-01
RCP-24 → RCP-01
RCP-04 → RCP-01, RCP-19
```

```text
Hard Contract CSDD Graph
→ ACYCLIC

Authority Cycle
→ NONE

SoT Cycle
→ NONE

Final Actual-state Ownership Cycle
→ NONE
```

Presence may participate in readiness application/evidence context but does not semantically define RCP-04.

---

# Accepted Authority / SoT / Final-owner Baseline

```text
RCP-01 constituent governance authorities
→ accepted ns_server Tenant / IAM / Organization / Policy / Trust authorities

RCP-02 Formal Execution Admission
→ ns_server / S8 / SV-R04

RCP-03 Presence / Reachability coordination facts
→ ns_runtime / R1 / RT-R01

RCP-19 Canonical Managed Desired
→ ns_server / S9 / SV-R05

RCP-19 Applied Configuration Actual-state
→ applicable runtime Actual-state owner

RCP-24 current Web Intent / submission occurrences
→ ns_web / WB-R01 under accepted W1/W2/W5 responsibilities where applicable

RCP-24 applicability / authoritative semantic outcome
→ receiving semantic authority

RCP-04 Node Readiness
→ ns_node / N1 / ND-R01
```

```text
Authority Transfer
→ 0

SoT Transfer
→ 0

Final Actual-state Ownership Transfer
→ 0
```

---

# RCP-24 Corrected Producer Topology

Current Product-side producer:

```text
ns_web / WB-R01
```

Accepted current Web source contributions:

```text
W1
→ administration / governed command Intent

W2
→ authoring / governed edit/change Intent

W5
→ applicable Trial/intervention/cancel/retry/resume/recovery request Intent
```

Only genuine Web-origin Intent/submission occurrence facts are Web-owned.

Future source seam:

```text
System-level SDK
→ FUTURE ONLY
→ separate SDK design / authorization required
```

```text
Additional Generic Source-surface Producer Class
→ NOT CREATED
```

RCP-12 remains separate:

```text
Agent Delegation / Agent cross-domain invocation / Agent→Node / Agent→Automation
→ RCP-12
→ NOT RCP-24 producers
```

Permanent:

```text
Intent != Permit != Acceptance != Admission != Outcome
Local Possession != Submission != Receipt != Applicability != Application != Authoritative Outcome
RCP-24 Configuration-change Intent != RCP-19 Canonical Desired-state
```

---

# Historical Batch-1 Evidence Classification

```text
Original Batch-1 0.0.1 producing chain
→ AUTHORIZED
→ COMPLETED
→ CORRECTION_REQUIRED
→ NOT GLOBALLY ACCEPTED
→ HISTORICAL / PRESERVED

Authorized Batch-1 correction reissuance 0.0.2
→ GLOBAL_ACCEPTED
→ NORMATIVE
```

No history rewrite or retroactive mutation is implied.

---

# Cross-cutting Contract Baseline

Accepted Batch-1 contracts preserve:

```text
Tenant != Organization
Principal != Authentication
Authenticated != Authorized
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Connected != Trusted != Admitted
Reachable != Ready
Desired != Distributed != Applied != Observed
Secret Reference != Secret Material
Reconnect != Reconciled
Re-observation != Canonicalization
Replay / resubmission != Retroactive Authorization
Latest Timestamp / Arrival != Canonical Winner
```

```text
Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

Stable Contract semantics remain representation-neutral. This Registry revision selects no concrete REST/gRPC/WebSocket/API/DTO/schema, broker, database/event-store schema, physical identifier format, SDK API/package shape, provider/framework or implementation topology.

---

# Downstream Boundary

```text
Runtime / Domain Stable Contract Design Exhaustion
→ NOT DECLARED

RCP-01..24 Full Cross-component Closure
→ NOT DECLARED

Runtime / Domain Stable Contract Design / Batch 2 producing
→ NOT AUTHORIZED BY THIS REGISTRY REVISION

System-level SDK Detailed Design Readiness
→ NOT_SATISFIED

System-level SDK Detailed Design
→ NOT AUTHORIZED

Design-to-Implementation Readiness
→ NOT AUTHORIZED

Implementation Planning / IWP / Coding
→ NOT AUTHORIZED
```

Batch-1 Global Acceptance satisfies the dependency prerequisite for a separate GAC Batch-2 entry-readiness assessment. That assessment must occur before any Batch-2 producing authorization.
