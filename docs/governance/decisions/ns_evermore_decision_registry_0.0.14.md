# ns_evermore Decision Registry — Current Revision

- Version: `0.0.14`
- Status: `GLOBAL_CURRENT / NORMATIVE`
- Supersedes: `0.0.13`

## Current Accepted Baseline

```text
Genesis Constitution → GLOBAL_ACCEPTED / NORMATIVE
NSE-001..017 → GLOBAL_ACCEPTED / NORMATIVE
Project Architecture → 0.0.3 / GLOBAL_ACCEPTED / CURRENT
Five-component Internal Architecture Boundaries → GLOBAL_ACCEPTED / NORMATIVE
Runtime Responsibility Architecture → GLOBAL_CLOSED / COMPLETE
Shared Foundation Architecture → GLOBAL_CLOSED / COMPLETE
Accepted Foundation Capabilities → 14
Accepted Foundation DAD → SFA-B1-DAD-001..010
Foundation Contract Design → GLOBAL_CLOSED / COMPLETE
Accepted Foundation Contracts → 15 / NORMATIVE CONTRACT UPSTREAM
Accepted Foundation Contract DAD → FCD-B1-DAD-001..008
Foundation Module Design / Batch 1 → GLOBAL_ACCEPTED / NORMATIVE MODULE UPSTREAM
Accepted Foundation Module DAD → FMD-B1-DAD-001..010
```

Foundation Module evidence:
- `docs/architecture_reviews/ns_evermore_ngrp_001_foundation_module_design_batch_1_candidate_0.0.1.md`
- `docs/architecture_reviews/ns_evermore_ngrp_001_foundation_module_design_batch_1_global_acceptance_0.0.1.md`

Accepted Module baseline:

```text
Foundation Modules → 14
Contract Realization Coverage → 15 / 15 / 100%
Stable Entry Realization Coverage → 14 / 14 / 100%
Principal Contract Realization Owner → exactly 1 per Contract
Hard BRSD Graph → ACYCLIC
Module Dependency Ambiguity → 0
Provider-bearing Pressure Handoff → 10 / 10
Authority / SoT / Actual-state Transfer → 0
```

Accepted Module subjects:
1. Bootstrap Configuration Acquisition Realization Module
2. Diagnostic Evidence Realization Module
3. Technical Observation & Health Realization Module
4. Temporal & Freshness Realization Module
5. Correlation & Provenance Realization Module
6. Semantic Representation Realization Module
7. Network Invocation Realization Module
8. Cache Access Realization Module
9. Durable Storage Access Realization Module
10. Technical Status & Uncertainty Realization Module
11. Governed Context Realization Module
12. Sensitive Reference & Disclosure Protection Realization Module
13. Compatibility & Conformance Realization Module
14. Localization Presentation Realization Module

Permanent Module dependency semantics:

```text
BRSD → hard baseline realization semantic dependency
BCD  → bounded conditional composition
PPH  → provider-pressure handoff; not inter-Module dependency
CSH  → consumer-surface handoff; not inter-Module dependency
Contract dependency != Module dependency automatically
```

Open MDE: `0`.
Unpersisted Owner Decision: `0`.

Foundation Module global closure/exhaustion and Foundation Provider Design readiness require a separate GAC assessment.
