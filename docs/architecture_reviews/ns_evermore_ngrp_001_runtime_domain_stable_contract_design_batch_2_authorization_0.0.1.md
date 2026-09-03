# NGRP-001 — Runtime / Domain Stable Contract Design / Batch 2 Authorization

Authority: `GLOBAL ARCHITECTURE COORDINATOR`

```text
Input Global State
→ GAC-EPOCH-0116

Input Transition
→ GAC-TR-0127

Authorization Recovery HEAD
→ bd2fff2fb572767a666e89a6486d683a7f6bf374

Decision Registry
→ 0.0.41 / GLOBAL_CURRENT / NORMATIVE

Batch-2 Entry Readiness
→ SATISFIED

Open MDE
→ 0

Unpersisted Owner Decision
→ 0

Blocking Semantic Gap
→ NONE

Unexpected Drift
→ NONE

Unauthorized Progression
→ NONE
```

---

# Authorization Result

```text
NGRP-001
— Runtime / Domain Stable Contract Design
/ Batch 2
/ Dispatch / Attempt / Effect / Agent Runtime / Provider Mediation / Server Runtime Evidence

→ AUTHORIZED FOR ONE BOUNDED PRODUCING SESSION
```

Exact authorized RCPs:

```text
RCP-05 — Dispatch Evidence
RCP-07 — Node Attempt
RCP-08 — Node Effect Evidence
RCP-09 — Agent Runtime
RCP-10 — Provider Mediation
RCP-23 — Server-native Runtime Evidence
```

Authorized RCP Count:

```text
6
```

No other RCP is authorized for substantive Contract Design by this transition.

---

# Accepted Upstream Stable Contract Baseline

The producing session must consume as normative upstream:

```text
RCP-01 Governance Context
RCP-02 Admission Evidence
RCP-03 Presence
RCP-04 Node Readiness
RCP-19 Desired / Applied Config
RCP-24 Human / SDK Intent
→ GLOBAL_ACCEPTED
```

It must preserve all accepted Batch-1 authority, currentness, history, privacy, offline, compatibility and non-collapse semantics.

---

# Batch-2 Producer / Owner Baseline

```text
RCP-05
→ ns_runtime / R2 / RT-R02
→ Dispatch coordination producer

RCP-07
→ ns_node / N2 / ND-R02
→ Node Attempt final Actual-state owner

RCP-08
→ ns_node / N3 / ND-R03
→ protected Node Effect / genuine Node-origin source-fact owner

RCP-09
→ ns_agent / A2 / AG-R01
→ Agent Runtime final Actual-state owner for genuine Agent-runtime facts

RCP-10
→ ns_agent / A3 / AG-R02
→ Provider Mediation bounded-observation owner

RCP-23
→ S5 / SV-R01
→ S7 / SV-R03
→ S10 / SV-R06
→ three separate server-native producer partitions
```

Permanent:

```text
Common Contract != Common Authority
Correlation != Ownership
Projection != Source of Truth
```

---

# Batch-2 Hard Contract Dependency Graph

Accepted for producing entry:

```text
RCP-08 → RCP-07
RCP-10 → RCP-09
```

Notation:

```text
A → B
→ Contract A's semantic definition depends on Contract B's semantic definition
```

Valid dependency-first order:

```text
Stage 0
→ RCP-05
→ RCP-07
→ RCP-09
→ RCP-23

Stage 1
→ RCP-08 after RCP-07
→ RCP-10 after RCP-09
```

Dependency refinement preserved from GAC-EPOCH-0116:

```text
RCP-07 relationship to RCP-05
→ CACD / CEL / CXAR where Dispatch is applicable
→ NOT mandatory CSDD
```

The producing session must not reintroduce a reverse or universal hard dependency merely because Dispatch evidence may participate in a Node Attempt journey.

```text
Batch-2 Hard CSDD Graph
→ ACYCLIC
```

---

# Required Contract-design Closure

For each authorized RCP, the bounded session must synthesize full cross-boundary representation-neutral Stable Contract semantics at the current Contract-design level, including where materially applicable:

```text
Contract semantic subject / identity
producer topology
consumer topology
producer obligations
consumer obligations
Authority preservation
Source of Truth preservation
final Actual-state / source-fact ownership preservation
applicability
currentness / freshness
temporal semantics
failure / unavailable / unknown / stale / partial / conflicting / indeterminate
Tenant / Organization / Principal separation
Authentication / Authorization / Policy / Trust references
security / privacy / minimization / redaction
Secret Reference boundary
offline / private correctness
history / provenance / correlation / lineage
recovery / re-observation compatibility
compatibility / migration / conformance
explicit guarantees
explicit non-guarantees
dependency classification
revalidation triggers
```

If a dimension is not owned by the Contract, the actual owner must be named and the Contract marked `NOT OWNED` for that dimension.

---

# Contract-specific Permanent Boundaries

## RCP-05 Dispatch Evidence

```text
Admission != Dispatch
Dispatch != Attempt
Dispatch Handoff != Attempt Started
Dispatch Success != Execution Started
```

RT-R02 retains only routing/scheduling/dispatch coordination facts. It does not become execution owner.

## RCP-07 Node Attempt

```text
Dispatch Received != Attempt Originated
Attempt != Effect
Retry / Re-entry != prior Attempt rewrite
```

ND-R02 retains Attempt Actual-state.

## RCP-08 Node Effect Evidence

```text
Attempt != Protected Effect
Attempt Success != Protected Effect automatically
Protected Effect != Business Semantic Success automatically
Local Source Fact != broader external/domain truth automatically
```

ND-R03 owns only genuine Node-origin Effect/source facts.

## RCP-09 Agent Runtime

```text
Agent Definition != Agent Operation
Agent Operation != Agent Runtime Attempt
Agent Runtime Attempt != Harness Invocation
Model Output != Agent Decision
Agent Decision != Admission
```

AG-R01 retains genuine Agent-runtime Actual-state.

## RCP-10 Provider Mediation

```text
Provider / Model != Agent
Provider Mediation Interaction != Harness Invocation
Provider success != Agent semantic success automatically
Provider observation != Agent Authority
```

Provider evidence returned to Agent Runtime does not create reverse semantic-definition authority.

## RCP-23 Server-native Runtime Evidence

```text
SV-R01 != SV-R03 != SV-R06
Common RCP-23 Contract != Common Authority
Common RCP-23 Contract != Common Actual-state owner
Universal Server Runtime Actual-state SoT → NOT CREATED
```

---

# Shared Foundation / Representation Boundary

Applicable accepted Shared Foundation semantics must be reused rather than recreated.

```text
Mandatory Missing Shared Foundation Semantic at authorization
→ NONE_FOUND
```

This authorization does not permit selection of:

```text
REST / GraphQL / gRPC / concrete WebSocket message design
DTO / wire schema
JSON Schema / Protobuf / Avro
queue / broker / topic
scheduler / worker / process topology
provider SDK / Agent framework
physical identity format
database / ORM / event-store schema
retry / timeout / backoff algorithm
deployment topology
System-level SDK API / package / language binding
```

Stable Contract Design precedes representation and implementation.

---

# MDE Stop Conditions

The bounded producing session must STOP / RETURN TO GAC if synthesis requires any of:

```text
new Product Component
new Runtime Role
new RCP
Authority transfer
SoT transfer
Final Actual-state Ownership transfer
universal identity namespace
universal latest/central/local winner
universal fail-open/fail-closed
universal exactly-once
universal retry/cancel/rollback/reversal law
new cross-Tenant Product law
mandatory public SaaS / online control plane
mandatory provider/framework/protocol/storage lock-in
accepted upstream architecture modification
hard Contract CSDD cycle
new mandatory Shared Foundation semantic not already accepted
```

Current authorization does not resolve such future decisions.

---

# Producing Evidence Discipline

Expected bounded evidence chain:

```text
Candidate
→ DAD Evidence
→ Review / Audit
→ Handoff
```

Recommended file paths:

```text
docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_2_candidate_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_2_dad_evidence_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_2_review_audit_0.0.1.md

docs/architecture_reviews/ns_evermore_ngrp_001_runtime_domain_stable_contract_design_batch_2_handoff_0.0.1.md
```

Producing session must not mutate Global State, Working State, Ledger or Decision Registry.

---

# Maximum Legal End State

```text
NGRP-001
— Runtime / Domain Stable Contract Design
/ Batch 2
/ RCP-05 + RCP-07 + RCP-08 + RCP-09 + RCP-10 + RCP-23

→ COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
```

Then:

```text
STOP
→ RETURN TO GAC
```

---

# Explicit Non-authorizations

```text
Runtime / Domain Stable Contract Design / Batch 3
→ NOT AUTHORIZED

Batch 4 / Batch 5
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

This authorization becomes operative only after the corresponding GAC Ledger transition and final Global State authorization seal are persisted.
