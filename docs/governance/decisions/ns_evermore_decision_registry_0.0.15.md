# ns_evermore Decision Registry — Current Revision

- Version: `0.0.15`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.14`

## Current Accepted Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Internal Architecture Boundaries → GLOBAL_ACCEPTED / NORMATIVE
Runtime Responsibility Architecture → GLOBAL_CLOSED / COMPLETE
Shared Foundation Architecture → GLOBAL_CLOSED / COMPLETE
Accepted Foundation Capabilities → 14 / NORMATIVE
Accepted Foundation DAD → SFA-B1-DAD-001..010
Foundation Contract Design → GLOBAL_CLOSED / COMPLETE
Accepted Foundation Contracts → 15 / NORMATIVE CONTRACT UPSTREAM
Accepted Foundation Contract DAD → FCD-B1-DAD-001..008
Foundation Module Design → GLOBAL_CLOSED / COMPLETE
Accepted Foundation Modules → 14 / NORMATIVE MODULE UPSTREAM
Accepted Foundation Module DAD → FMD-B1-DAD-001..010
Foundation Provider Design / Batch 1 → GLOBAL_ACCEPTED / NORMATIVE PROVIDER UPSTREAM
Accepted Foundation Provider DAD → FPD-B1-DAD-001..011
```

Foundation Provider evidence:
- `docs/architecture_reviews/ns_evermore_ngrp_001_foundation_provider_design_batch_1_candidate_0.0.1.md`
- `docs/architecture_reviews/ns_evermore_ngrp_001_foundation_provider_design_batch_1_global_acceptance_0.0.1.md`

Accepted Provider baseline:

```text
Provider-bearing Pressures → 10
Derived Provider Families → 10
Provider Pressure Coverage → 10 / 10 / 100%
Uncovered Provider Pressure → 0
Duplicate Principal Provider Responsibility → 0
Provider Overfragmentation → NONE_FOUND
God Provider Abstraction → NONE_FOUND
Concrete Provider/Product/Library Selection → 0
Authority / SoT / Actual-state Transfer → 0
```

Accepted Provider families:
1. Bootstrap Configuration Source Provider Family
2. Diagnostic Delivery Sink Provider Family
3. Technical Observation Sink Provider Family
4. Temporal Source Provider Family
5. Semantic Representation Codec Provider Family
6. Network Invocation Transport Provider Family
7. Cache Backend Provider Family
8. Durable Storage Backend Provider Family
9. Secret-material Resolution Source Provider Family
10. Localization Resource Provider Family

Permanent Provider invariants:

```text
Provider != Foundation Contract / Module / Product Component / Runtime Role
Provider Selection / Readiness / Success != Product Authority / Trust / Policy / Admission / Domain Success
Provider PASS != Module Contract PASS
Provider Replacement != Contract Semantic Change automatically
Provider-specific Optional Capability != Universal Foundation Semantics
Provider API != Foundation Contract
```

Provider-less responsibilities remain provider-less: C05, C10, C11, C14 and C13 redaction responsibility.
Deferred Foundation candidates remain outside the accepted baseline: Cryptographic/Evidence-verification Helpers and Database Utility Primitives.

Open MDE: `0`.
Unpersisted Owner Decision: `0`.

Foundation Provider global closure/exhaustion and Component Internal Design readiness require a separate GAC assessment.
