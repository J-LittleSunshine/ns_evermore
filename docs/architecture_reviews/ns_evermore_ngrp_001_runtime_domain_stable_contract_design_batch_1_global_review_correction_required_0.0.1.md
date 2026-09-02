# NGRP-001 — Runtime / Domain Stable Contract Design / Batch 1 — GAC Correction Required

Authority: `GLOBAL ARCHITECTURE COORDINATOR`

```text
Input Global State → GAC-EPOCH-0113
Authorization Transition → GAC-TR-0124
Authorization Seal / Producing Entry HEAD → d6b12f1d9901d810a61943c0c84b058db61746b2
Frozen Producing Final HEAD → 9c0393942402af9454622be5e07fb70165215e6c
GAC Result → CORRECTION_REQUIRED
Open MDE → 0
Unpersisted Owner Decision → 0
```

The producing range is Git-clean and lawfully isolated:

```text
d6b12f1d9901d810a61943c0c84b058db61746b2
→ f9966824b12f43c5043440a231b4cc9adf55d2cc  Candidate only
→ a2929f986e753136fa2ae114125f3efd0a4ce02b  DAD only
→ 9e583c101d8cd028c11c2acda94efbbe9c069ff2  Review / Audit only
→ 9c0393942402af9454622be5e07fb70165215e6c  Handoff only
```

```text
Producing commits → 4
Added producing evidence files → 4
Existing-file modification → 0
Deletion → 0
Governance mutation by producing session → 0
Unexpected drift → NONE
Unauthorized progression → NONE
```

## Independent GAC Review Result

The following areas passed independent review at the current design level:

```text
RCP-01 Governance Context semantic synthesis → PASS
RCP-02 Admission Evidence semantic synthesis → PASS
RCP-03 Presence semantic synthesis → PASS
RCP-19 Desired / Applied Config semantic synthesis → PASS
RCP-04 Node Readiness semantic synthesis → PASS
Batch-1 Hard CSDD graph → ACYCLIC / PASS
Authority transfer → 0
SoT transfer → 0
Final Actual-state ownership transfer → 0
Security / privacy / Secret Reference boundary → PASS
Offline / private correctness → PASS
Recovery / re-observation non-canonicalization → PASS
Compatibility / migration / conformance → PASS
Shared Foundation reuse → PASS
Mandatory Missing Shared Foundation Semantic → NONE_FOUND
Technology / representation leakage → 0
Implementation leakage → 0
Open MDE → 0
Unpersisted Owner Decision → 0
```

Global Acceptance is blocked by one bounded RCP-24 producer-topology defect.

---

# Correction Item — RCP-24 Producer Topology Scope

Accepted Runtime Responsibility Architecture defines:

```text
RCP-24
→ WB/SDK → governed targets
→ Human / SDK Intent
→ receiving authority owns semantic outcome
```

The Batch-1 authorization preserves that boundary as:

```text
Web and future SDK are source surfaces
→ not universal action authorities
```

Accepted Web Component Internal Design also contains multiple Web-side RCP-24 source contributions, including at least:

```text
W1 / WB-R01
→ governed administration / command intent source semantics

W2 / WB-R01
→ Web authoring / change-intent source semantics

W5 / WB-R01
→ intervention / cancel / retry / resume / recovery request-intent source semantics
```

The Candidate currently states under RCP-24 producer topology:

```text
Human via ns_web / W1 / WB-R01
future System-level SDK source surfaces when separately designed/authorized
other accepted human/source surfaces where their owner semantics establish an Intent
```

This is not sufficiently precise for Full Cross-boundary Stable Contract closure because it is simultaneously:

1. **too narrow on current Web topology** — it names `W1` as the Web producer locus even though accepted `W2` and `W5` also contribute RCP-24 source-side Intent semantics under the same `WB-R01` role; and
2. **too broad outside the accepted producer set** — `other accepted human/source surfaces` is open-ended and can be read to admit producer domains outside the accepted `WB/SDK` RCP-24 topology, risking overlap with specialized contracts such as Agent Delegation (`RCP-12`) or other domain-specific source semantics.

This creates a producer-topology ambiguity in the exact contract that is supposed to stabilize cross-boundary producer/consumer obligations.

## Evidence inconsistency

The issue is also internally inconsistent across the four producing artifacts:

```text
Candidate
→ W1 / WB-R01 + future SDK + open-ended other source surfaces

RDSC-B1-DAD-006
→ Human / Web / future SDK interactions

Review / Audit
→ RCP scope overclaim reported PASS

Handoff
→ future SDK only as a future intent source surface; Human/Web semantics otherwise preserved
```

Therefore GAC cannot accept the claimed `Producer topology ambiguity → 0` / `RCP_SCOPE_OVERCLAIM_REVIEW → PASS` result as currently written.

---

# Required Correction

Within the already authorized Batch-1 / RCP-24 scope only:

1. Re-state the RCP-24 source producer topology exactly from accepted authority:

```text
Current Product-side source producer
→ ns_web / WB-R01
→ only those accepted Web responsibilities that genuinely originate RCP-24 Intent/submission facts

Future source producer
→ System-level SDK
→ only after separate SDK design/authorization

No additional generic source-surface producer class
→ created by this Contract
```

2. Do not reduce the Web producer topology to W1 only. At minimum, preserve the already accepted W1/W2/W5 RCP-24 Web-side source contributions where materially applicable.

3. Remove or strictly qualify `other accepted human/source surfaces` so it cannot enlarge the current RCP-24 producer set. If a future architecture admits another producer surface, that must enter through normal GAC revalidation rather than being pre-authorized by this Contract.

4. Preserve:

```text
Intent != Permit != Acceptance != Admission != Outcome
Local Possession != Submission != Receipt != Applicability != Application != Authoritative Outcome
RCP-24 Configuration-change Intent != RCP-19 Canonical Desired-state
```

5. Preserve the receiving semantic authority as the owner of applicability and authoritative outcome.

6. Re-run and correct at least:

```text
PRODUCER_CONSUMER_OBLIGATION_REVIEW
RCP_SCOPE_OVERCLAIM_REVIEW
SDK_PREMATURE_DESIGN_REVIEW
CONTRACT_SUBJECT_IDENTITY_REVIEW where producer/source identity wording is affected
GIT_DRIFT_REVIEW
```

7. Revalidate DAD-006 and Handoff for consistency. No substantive redesign is required unless the correction session discovers additional Repository contradiction.

---

# Correction Boundary

```text
New Product Component → PROHIBITED
New Runtime Role → PROHIBITED
New RCP → PROHIBITED
RCP-12 redesign → PROHIBITED
Batch-2..5 design → PROHIBITED
System-level SDK Detailed Design → PROHIBITED
Authority transfer → PROHIBITED
SoT transfer → PROHIBITED
Final Actual-state ownership transfer → PROHIBITED
Implementation Planning / IWP / Coding → PROHIBITED
```

```text
Owner MDE → NOT CURRENTLY REQUIRED
Global Acceptance → NOT GRANTED
Batch 2 Authorization → NONE
System-level SDK Detailed Design Readiness → NOT GRANTED
```

The semantic correction is bounded and does not require reopening RCP-01, RCP-02, RCP-03, RCP-04 or RCP-19 except for consistency references.

---

# GAC Disposition

```text
NGRP-001
— Runtime / Domain Stable Contract Design
/ Batch 1

→ CORRECTION_REQUIRED
→ RCP-24 PRODUCER TOPOLOGY SCOPE RECONCILIATION ONLY

Global Acceptance
→ NOT GRANTED
```

The frozen producing final HEAD remains preserved as historical producing evidence. A correction session must not begin until a Repository-backed correction authorization State seal is persisted.