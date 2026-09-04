# NGRP-001 — Runtime / Domain Stable Contract Design / Batch 2 — Global Acceptance

Authority: `GLOBAL ARCHITECTURE COORDINATOR`

```text
Input Global State
→ GAC-EPOCH-0117

Authorization Transition
→ GAC-TR-0128

Authorization Seal / Producing Entry HEAD
→ 4a04475559ac1af15277f813247d2ee3a5d2eef0

Producing Final HEAD
→ f4b79e43ceae0647db1123b650f2f4196e8ae670

GAC Result
→ GLOBAL_ACCEPT
```

---

# 1. Producing-chain Review

The authorized bounded producing chain is:

```text
4a04475559ac1af15277f813247d2ee3a5d2eef0
→ d81977670880630196b65a0a20d0a5dd4267f724  Candidate 0.0.1
→ f23b08729598b503a865bb42a216af9cae29b113  DAD Evidence 0.0.1
→ e8c03a136a8e8d9020c2dfc8d7b727f04fd88090  Review / Audit 0.0.1
→ f4b79e43ceae0647db1123b650f2f4196e8ae670  Handoff 0.0.1
```

Independent Git verification:

```text
Producing commits
→ 4

Added producing evidence files
→ exactly 4

Existing-file modification
→ 0

Deletion
→ 0

Governance mutation by producing session
→ 0

Source / implementation mutation
→ 0

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE
```

The bounded session stopped lawfully at `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE` and did not self-authorize Batch 3, SDK Detailed Design or implementation.

---

# 2. Accepted Stable Contracts

The following six representation-neutral full cross-boundary Stable Contracts are globally accepted at the current Contract-design level:

```text
RCP-05 — Dispatch Evidence
→ GLOBAL_ACCEPTED

RCP-07 — Node Attempt
→ GLOBAL_ACCEPTED

RCP-08 — Node Effect Evidence
→ GLOBAL_ACCEPTED

RCP-09 — Agent Runtime
→ GLOBAL_ACCEPTED

RCP-10 — Provider Mediation
→ GLOBAL_ACCEPTED

RCP-23 — Server-native Runtime Evidence
→ GLOBAL_ACCEPTED
```

Accepted Batch-2 Stable Contract count: `6`.

Combined accepted Stable Contract count after this transition: `12 / 24`.

This does not declare full RCP-01..24 closure or Stable Contract Design exhaustion.

---

# 3. Accepted Dependency Baseline

Only `CSDD` participates in hard semantic-definition cycle analysis.

Accepted Batch-2 intra-Batch hard CSDD:

```text
RCP-08 → RCP-07
RCP-10 → RCP-09
```

Accepted Dispatch/Attempt refinement:

```text
RCP-07 ↔ RCP-05
→ CACD / CEL / CXAR where Dispatch is applicable
→ NOT mandatory CSDD
```

Cross-Batch governed Dispatch semantics consume the already accepted Batch-1 Admission / Presence / Readiness contracts where applicable, without transferring their source authority.

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

---

# 4. Authority / SoT / Final-owner Acceptance

Accepted final ownership remains:

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

RCP-23 producer partitions
→ S5 / SV-R01
→ S7 / SV-R03
→ S10 / SV-R06
```

Preserved external authorities include S8 Formal Execution Admission, RT-R01 Presence/Reachability, ND-R01 Node Readiness, S9 canonical Desired, A1 Agent Definition, applicable external/customer factual SoTs and accepted IAM/Policy/Trust authorities.

```text
Authority Transfer
→ 0

SoT Transfer
→ 0

Final Actual-state Ownership Transfer
→ 0
```

---

# 5. Dispatch / Attempt / Effect Acceptance

Permanent accepted non-collapse:

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

RCP-07 remains semantically definable without a mandatory RT-R02 Dispatch journey. When Dispatch participates, exact correlation is required through typed application/evidence relationships.

RCP-08 depends semantically on RCP-07 for Attempt-to-Effect correlation. Effect evidence returning to Attempt history is evidence/history linkage, not reverse semantic-definition authority.

For externally authoritative facts:

```text
ND-R03 owns
→ local observation / evidence / reference / provenance

External/source-domain final SoT
→ remains external/source-owned
```

Local observation/copy does not replace external factual authority.

---

# 6. Agent Runtime / Provider Mediation Acceptance

Permanent accepted distinctions:

```text
Agent Definition != Agent Operation
Agent Operation != Agent Runtime Attempt / Continuation Episode
Agent Runtime Attempt != Harness Invocation
Harness Invocation != Provider Mediation Interaction
Model / Provider Output != Agent Decision
Agent Decision != Admission
Provider / Model != Agent
Provider Success != Agent Semantic Success automatically
Provider Observation != Agent Authority
Provider Replacement != Agent Definition Rewrite
```

`ns_evermore Harness / NSH` remains a named internal architecture concept inside accepted `ns_agent` boundaries only. It is not a new Product Component, Runtime Role, Shared Foundation capability, SDK authority or final Actual-state partition.

Accepted dependency:

```text
RCP-10 → RCP-09
→ CSDD

Provider evidence return to Agent Runtime
→ CEL / CACD
→ NOT reverse CSDD
```

No provider/vendor/SDK/model-routing/fallback-priority commitment is accepted.

---

# 7. Server-native Runtime Evidence Acceptance

Accepted RCP-23 producer topology is exactly:

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

The common Contract standardizes only cross-boundary evidence/conformance obligations. Producer-specific lifecycle, semantic result and final ownership remain with each accepted partition. S10 Attempt semantics do not create S5/S7 Attempt semantics.

No generic fourth producer is pre-authorized; any future producer requires normal GAC revalidation.

---

# 8. Security / Privacy / Offline / History Acceptance

Accepted evidence disclosure is protected-existence-aware. The existence of Dispatch targets, Node Attempts/Effects, Agent context, Provider/model capability or server runtime subjects may itself be protected.

Permanent:

```text
Reference Possession != Permission
Diagnostic Visibility != Disclosure Authority
Redacted Evidence != Unredacted Authority
Observed Evidence != Source Authority
Secret Reference != Secret Material
```

Authorization-filtered absence/redaction must not silently become source `FALSE`, `NOT_FOUND`, `NO_ATTEMPT`, `NO_EFFECT` or provider-unavailable truth.

Private/offline correctness remains viable without mandatory public SaaS/Internet/control plane.

Recovery compatibility preserves:

```text
Reconnect != Reconciled
Recovery != SoT Transfer
Re-observation != Canonicalization
Replay != Retroactive Authorization
Latest Timestamp / Arrival != Canonical Winner
Later Success != prior Failure deletion
```

RCP-20 Recovery/Reconciliation is not designed by this Batch.

---

# 9. Shared Foundation / Compatibility / Technology Boundary

```text
Mandatory Missing Shared Foundation Semantic
→ NONE_FOUND

Parallel Batch-2 Foundation
→ 0
```

Accepted Foundation semantics are reused for temporal/freshness, technical uncertainty, correlation/provenance, governed context, representation mechanics, network mechanics where applicable, Secret Reference, redaction, diagnostics and compatibility/conformance.

No REST/gRPC/WebSocket message/API/DTO/schema, broker, queue, scheduler algorithm, database/event-store schema, physical identity scheme, Agent framework, provider SDK, model-routing algorithm, process/worker/deployment topology or implementation plan is accepted.

```text
Technology / Representation Leakage
→ 0

Implementation Leakage
→ 0
```

---

# 10. Review / Audit Acceptance

The producing Review/Audit records:

```text
Mandatory Review Gates
→ 31

PASS
→ 31

FAIL
→ 0

BLOCKED
→ 0
```

GAC independently rechecked the material Git, authority, dependency, producer/consumer, Dispatch/Attempt/Effect, external SoT, Agent/Provider, server-native partition, security/privacy, offline/recovery, Foundation, compatibility and scope dimensions and found no correction-required condition.

```text
Missing / Ambiguous Contract Dimension
→ 0

Misclassified MDE
→ 0

Open MDE
→ 0

Unpersisted Owner Decision
→ 0
```

---

# 11. Global Acceptance Result

```text
NGRP-001
— Runtime / Domain Stable Contract Design
/ Batch 2
/ RCP-05 + RCP-07 + RCP-08 + RCP-09 + RCP-10 + RCP-23

→ GLOBAL_ACCEPTED
```

Explicit non-implications:

```text
Runtime / Domain Stable Contract Design / Batch 3 producing
→ NOT AUTHORIZED

Batch 4 / Batch 5 producing
→ NOT AUTHORIZED

Runtime / Domain Stable Contract Design Exhaustion
→ NOT DECLARED

RCP-01..24 Full Cross-component Closure
→ NOT DECLARED

System-level SDK Detailed Design Readiness
→ NOT_SATISFIED

System-level SDK Detailed Design
→ NOT AUTHORIZED

Design-to-Implementation Readiness
→ NOT AUTHORIZED

Implementation Planning / IWP / Coding
→ NOT AUTHORIZED
```

A separate GAC Batch-3 entry-readiness assessment is required before any Batch-3 authorization.