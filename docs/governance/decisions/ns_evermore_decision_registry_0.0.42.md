# ns_evermore Decision Registry — Current Revision

- Version: `0.0.42`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.41`

All accepted normative decisions and baselines in Decision Registry `0.0.41` remain in force unless explicitly refined below.

---

# Runtime / Domain Stable Contract Design — Batch 2 Acceptance

Global Acceptance evidence:

`docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_2_global_acceptance_0.0.1.md`

Accepted producing evidence:

```text
Candidate 0.0.1
→ d81977670880630196b65a0a20d0a5dd4267f724

DAD Evidence 0.0.1
→ f23b08729598b503a865bb42a216af9cae29b113

Review / Audit 0.0.1
→ e8c03a136a8e8d9020c2dfc8d7b727f04fd88090

Handoff 0.0.1 / Producing Final HEAD
→ f4b79e43ceae0647db1123b650f2f4196e8ae670
```

```text
Runtime / Domain Stable Contract Design / Batch 2
→ GLOBAL_ACCEPTED

Accepted Batch-2 Stable Contracts
→ 6

RCP-05 — Dispatch Evidence
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-07 — Node Attempt
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-08 — Node Effect Evidence
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-09 — Agent Runtime
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-10 — Provider Mediation
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL

RCP-23 — Server-native Runtime Evidence
→ GLOBAL_ACCEPTED / FULL CROSS-BOUNDARY STABLE CONTRACT CLOSED AT CURRENT CONTRACT-DESIGN LEVEL
```

Combined accepted Stable Contract count after Batch 2:

```text
12 / 24
```

Remaining RCP stable-contract design remains downstream through Batches 3-5. This revision does not declare `RCP-01..24` Full Cross-component Closure or Stable Contract Design Exhaustion.

---

# Accepted Batch-2 Dependency Baseline

Only `CSDD` participates in hard semantic-definition cycle analysis.

Accepted intra-Batch hard CSDD:

```text
RCP-08 → RCP-07
RCP-10 → RCP-09
```

Accepted Dispatch/Attempt classification:

```text
RCP-07 ↔ RCP-05
→ CACD / CEL / CXAR where Dispatch is applicable
→ NOT mandatory CSDD
```

Permanent:

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

Runtime flow, evidence-return direction, history and re-observation do not create reverse semantic-definition authority.

---

# Accepted Batch-2 Authority / SoT / Final-owner Baseline

```text
RCP-05 Dispatch coordination
→ ns_runtime / R2 / RT-R02

RCP-07 Node Attempt
→ ns_node / N2 / ND-R02

RCP-08 genuine Node-origin protected Effect / local source facts
→ ns_node / N3 / ND-R03

RCP-09 Agent Runtime source facts
→ ns_agent / A2 / AG-R01

RCP-10 Provider Mediation bounded observations
→ ns_agent / A3 / AG-R02

RCP-23 server-native producer partitions
→ S5 / SV-R01
→ S7 / SV-R03
→ S10 / SV-R06
```

Preserved external authorities include:

```text
Formal Execution Admission
→ S8 / SV-R04

Presence / Reachability
→ R1 / RT-R01

Node Readiness
→ N1 / ND-R01

Canonical Managed Desired
→ S9 / SV-R05

Agent Definition / canonical revision
→ A1 / ns_agent

External/customer factual SoT
→ applicable original source owner

IAM / Policy / Trust
→ accepted ns_server governance authorities
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

# Dispatch / Attempt / Effect Non-collapse

Permanent accepted contract law:

```text
Admission != Scheduling != Routing != Dispatch != Attempt != Effect
Dispatch Received != Attempt Originated
Dispatch Handoff != Attempt Started
Dispatch Success != Execution Started
Attempt != Protected Effect
Attempt Success != Protected Effect automatically
Protected Effect != Business Semantic Success automatically
Retry != prior Attempt mutation
```

RCP-07 does not require a universal RT-R02 Dispatch origin. When Dispatch participates, exact correlation is mandatory through typed CACD/CEL/CXAR relationships.

RCP-08 depends semantically on RCP-07 for Attempt-to-Effect correlation. Effect evidence returning to Attempt history remains CEL/CHPL.

External factual boundary:

```text
ND-R03 local observation/evidence/reference/provenance
!= external factual SoT
```

Observation or copy does not transfer factual authority.

---

# Agent Runtime / Provider Mediation Non-collapse

Permanent:

```text
Agent Definition != Agent Operation
Agent Operation != Agent Runtime Attempt / Continuation Episode
Agent Runtime Attempt != Harness Invocation
Harness Invocation != Provider Mediation Interaction
Provider / Model != Agent
Provider Output != Agent Decision
Agent Decision != Admission
Provider Success != Agent Semantic Success automatically
Provider Observation != Agent Authority
Provider Replacement != Agent Definition Rewrite
```

Accepted dependency:

```text
RCP-10 → RCP-09
→ CSDD

Provider evidence return to Agent Runtime
→ CEL / CACD
→ NOT reverse CSDD
```

`ns_evermore Harness / NSH` remains only an accepted internal `ns_agent` architecture concept. It is not a Product Component, Runtime Role, Shared Foundation capability, SDK authority or new final Actual-state partition.

No concrete provider/vendor/SDK, model-routing algorithm or fallback-priority law is selected.

---

# RCP-23 Server-native Producer Partition Baseline

Accepted current producer topology:

```text
S5 / SV-R01
→ Business Application semantic Runtime Evidence

S7 / SV-R03
→ Data / Knowledge / ETL semantic Runtime Evidence

S10 / SV-R06
→ Server-local Background Runtime Evidence
```

Permanent:

```text
SV-R01 != SV-R03 != SV-R06
Common Contract != Common Authority
Common Contract != Common Actual-state Owner
Universal Server Runtime Actual-state SoT → NOT CREATED
Universal Server Operation → NOT CREATED
Universal Server Attempt → NOT CREATED
Universal Server Runtime Status / State Machine → NOT CREATED
```

Common evidence obligations preserve partition identity and source-specific lifecycle/outcome. S10 Attempt semantics do not create S5/S7 Attempt semantics.

No generic fourth producer is pre-authorized.

---

# Security / Privacy / Offline / Recovery Baseline

Protected subject existence may itself require authorization. Permanent:

```text
Reference Possession != Permission
Diagnostic Visibility != Disclosure Authority
Redacted Evidence != Unredacted Authority
Observed Evidence != Source Authority
Secret Reference != Secret Material
```

Authorization-filtered absence/redaction must not be reinterpreted as source `FALSE`, `NOT_FOUND`, `NO_ATTEMPT`, `NO_EFFECT` or provider-unavailable truth.

Private/offline operation remains valid without mandatory public SaaS, public Internet or hosted control plane.

```text
Reconnect != Reconciled
Recovery != SoT Transfer
Re-observation != Canonicalization
Replay != Retroactive Authorization
Latest Timestamp / Arrival != Canonical Winner
Later Success != prior Failure deletion
```

RCP-20 remains downstream and is not designed by this Registry revision.

---

# Shared Foundation / Technology Boundary

```text
Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Parallel Batch-2 Foundation
→ 0
```

Accepted Foundation remains the reusable source for temporal/freshness, technical uncertainty, correlation/provenance, governed context, semantic representation mechanics, network mechanics where applicable, Secret Reference, redaction, diagnostics and compatibility/conformance.

Stable Contract semantics remain representation-neutral. No concrete REST/gRPC/WebSocket/API/DTO/schema, broker/queue/scheduler, persistence/event-store schema, physical identifier scheme, Agent framework, Provider SDK, model-routing algorithm, process/worker/deployment topology or implementation design is accepted.

---

# Stable Contract Program Position

```text
Batch 1
→ RCP-01 / 02 / 03 / 04 / 19 / 24
→ GLOBAL_ACCEPTED

Batch 2
→ RCP-05 / 07 / 08 / 09 / 10 / 23
→ GLOBAL_ACCEPTED

Accepted Stable Contracts
→ 12 / 24

Batch 3
→ RCP-06 / 11 / 12 / 13 / 14 / 15
→ NOT YET ASSESSED FOR ENTRY AFTER BATCH-2 ACCEPTANCE

Batch 4
→ RCP-16 / 17 / 18 / 20 / 21
→ BLOCKED ON PRIOR BATCH ACCEPTANCE

Batch 5
→ RCP-22
→ BLOCKED ON PRIOR BATCH ACCEPTANCE
```

Batch-2 Global Acceptance satisfies one sequencing prerequisite for a separate Batch-3 entry-readiness assessment. It does not infer Batch-3 readiness or authorization.

---

# Explicit Non-authorization

```text
Runtime / Domain Stable Contract Design Exhaustion
→ NOT DECLARED

RCP-01..24 Full Cross-component Closure
→ NOT DECLARED

Runtime / Domain Stable Contract Design / Batch 3 producing
→ NOT AUTHORIZED BY THIS REGISTRY REVISION

Batch 4 / Batch 5 producing
→ NOT AUTHORIZED

System-level SDK Detailed Design Readiness
→ NOT_SATISFIED

System-level SDK Detailed Design
→ NOT AUTHORIZED

Design-to-Implementation Readiness
→ NOT AUTHORIZED

Implementation Planning / IWP / Coding
→ NOT AUTHORIZED
```

The next legal material action after governance persistence is a separate GAC Runtime / Domain Stable Contract Design / Batch-3 entry-readiness assessment.