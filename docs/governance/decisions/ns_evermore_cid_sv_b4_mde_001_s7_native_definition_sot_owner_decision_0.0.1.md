# NGRP-001 — CID-SV-B4-MDE-001 — S7 Native Definition Canonical SoT Topology Owner Decision

## Metadata

- Decision ID: `CID-SV-B4-MDE-001`
- Program: `NGRP-001`
- Context: `Component Internal Design / ns_server / prospective Batch 4 / S7 entry gate`
- Decision Authority: `PROJECT OWNER / MDE`
- Classification: `MDE`
- Status: `OWNER_DECIDED / PERSISTED`
- Repository: `J-LittleSunshine/ns_evermore`
- Branch: `architecture/ns-evermore-genesis-0.0.1`
- Decision Entry HEAD: `1b03b7a8b8f525dc5ddf6613d19f9b4025e418b0`
- Entry Global State: `GAC-EPOCH-0051`
- Trigger Assessment: `docs/architecture_reviews/ns_evermore_ngrp_001_ns_server_internal_design_remaining_pressure_batching_assessment_0.0.3.md`
- Batch-4 Authorization: `NOT GRANTED BY THIS DECISION`

---

## 1. Material Question

What canonical Source-of-Truth topology governs **native ns_evermore S7 Data / Knowledge / Foundational ETL Definition state** while preserving the already accepted factual Data / Knowledge Source-of-Truth federation?

This decision concerns native Product Definition state such as governed native Data/Knowledge/ETL semantic definitions, definition revisions, authoring lifecycle, validation/certification target identity, Trial definition binding and historical runtime interpretation.

It does **not** decide factual enterprise Data/Knowledge SoTs, database/storage topology, ETL engine, connector provider, DSL, visual schema, artifact format, process topology or implementation layout.

---

## 2. Accepted Upstream That Is Not Reopened

```text
Native Enterprise Data / Knowledge / Foundational ETL Semantic Authority
→ ns_server

Data / Knowledge Factual SoT
→ exactly one final SoT per bounded semantic partition
→ different partitions may have different final SoTs
→ external enterprise systems may remain final factual SoT

Complete Source / SDK Authoring
→ REQUIRED

Complete ns_web Visual Authoring
→ REQUIRED

Both Surfaces
→ same governed Data / Knowledge / ETL semantics

Bidirectional Source↔Visual Semantic Interoperability
→ REQUIRED

Governed Pre-production Trial
→ REQUIRED

SV-R03
→ Data / Knowledge / ETL Runtime Participant
```

Permanent distinction:

```text
Semantic Authority
!= Canonical Definition SoT automatically

Native Definition SoT
!= Factual Data / Knowledge SoT
```

`Z2-MDE-017` explicitly assigns native canonical Definition SoTs for Business Application, Automation and AI Agent only; it does not establish a general rule for S7.

---

## 3. Alternatives Presented to Project Owner

### A — Unified Native S7 Definition SoT in `ns_server`

```text
Native S7 Data / Knowledge / ETL Semantic Authority
→ ns_server

Native S7 Canonical Definition SoT
→ ns_server

Factual Data / Knowledge SoT
→ unchanged / governed per bounded semantic partition
```

All native S7 definitions use `ns_server` as the canonical Product Definition SoT. External schemas, source facts and enterprise systems remain bounded sources/SoTs and are referenced with provenance rather than becoming native Definition authority automatically.

### B — Governed Per-Definition-Partition SoT Federation

```text
Native S7 Definition SoT
→ assigned per bounded S7 definition semantic partition

Each same definition assertion
→ exactly one final Definition SoT

Different definition partitions
→ may have different final Definition SoTs
→ native ns_server or explicitly governed external definition authority
```

Source/visual authoring remains complete but must converge through each partition's declared Definition SoT.

### C — External / Source-system Definition SoT with `ns_server` Governed Mirror

```text
Native S7 Semantic Authority
→ ns_server

Canonical Definition state
→ designated source/external definition system

ns_server
→ governed semantic interpretation / validation / projection / mirror
→ not final Definition SoT
```

This maximizes source-system definition ownership but couples native authoring, history, Trial and re-delivery to external/source definition authorities.

---

## 4. GAC Recommendation Presented

```text
Recommendation
→ A — Unified Native S7 Definition SoT in ns_server
```

Rationale:

1. `ns_server` is already the Owner-decided native S7 Semantic Authority.
2. S7 is a native first-class authorable Product domain with complete source + visual authoring; one canonical native definition lifecycle gives both surfaces one revision/history target.
3. It cleanly separates **native Product Definition state** from already federated **factual Data/Knowledge SoT** topology.
4. It prevents external enterprise schemas, Git/source placement, Builder state, ETL provider or storage placement from becoming native Product Definition authority by accident.
5. It supplies stable definition identity/revision inputs for governed Trial, `SV-R03` history, Business/Automation/Agent references and S13 discovery contribution semantics.
6. It remains compatible with private/offline deployment without requiring an external definition control plane.

Costs / risks:

- `ns_server` must maintain canonical revision/provenance for native S7 definition families;
- external source definitions/schemas require explicit reference or mapping where they remain externally governed;
- later S7 design must rigorously distinguish native definition semantics from externally authoritative facts/schemas and derived knowledge.

---

## 5. Project Owner Decision

The Project Owner selected:

```text
Selected Option
→ A

Native S7 Data / Knowledge / Foundational ETL Canonical Definition SoT
→ ns_server
```

This Owner selection was made after GAC presented Options A/B/C and recommended A.

---

## 6. Normative Consequences

The following may now be consumed by later authorized S7 Component Internal Design:

```text
Native S7 Semantic Authority
→ ns_server

Native S7 Canonical Definition SoT
→ ns_server

Semantic Authority
!= Canonical Definition SoT
→ distinction remains normative even though co-located
```

Native S7 definition state includes only native Product Definition subjects established by later authorized S7 design. This decision does not predefine concrete definition families, physical namespaces, schemas or representations.

The following remains unchanged:

```text
Factual Data / Knowledge SoT
→ governed per bounded semantic partition

External enterprise factual SoT
→ MAY remain final SoT

ETL / import / synchronization / indexing / caching / projection
→ do not automatically transfer factual SoT
```

---

## 7. Authoring / History Consequences

Later authorized S7 design may now establish, within this SoT topology:

```text
Mutable Source/Visual Authoring Candidate
!= Canonical Native S7 Definition Revision

Semantic modification
→ new canonical Definition Revision

Historical Definition Revision
→ not silently rewritten by current state

Current Definition Revision
!= historical Trial / SV-R03 runtime revision automatically
```

The physical revision identifier, DSL, AST/IR, source file format, visual schema, converter/generator and persistence format remain downstream decisions.

---

## 8. Cross-domain / S13 Consequences

Business Application, Automation, Agent and Discovery may later reference native S7 definitions through stable identity/revision semantics without acquiring S7 Authority or Definition SoT.

```text
Cross-domain reference
!= Authority transfer
!= Definition SoT transfer
!= factual SoT transfer

S13 Discovery Projection
!= S7 Definition SoT
!= factual Data/Knowledge SoT
```

---

## 9. Offline / Recovery Consequences

```text
Private/offline ns_server deployment
→ may host the native S7 Definition SoT under normal governance

Offline copy / editor / cache / local replica
!= Definition SoT by possession

Reconnect
!= Authority Transfer

Latest Timestamp
!= Canonical Winner automatically
```

No material global fail-open/fail-closed or conflict-winner algorithm is selected.

---

## 10. Explicit Non-implications

This decision does **not** establish:

```text
ns_server = universal enterprise factual SoT
Native S7 Definition SoT = factual Data/Knowledge SoT
External schema = native Definition automatically
ETL output = upstream source fact
Database/storage/cache = Definition SoT by placement
One database/schema/table = one semantic partition
One mandatory DSL / AST / IR / visual schema
One connector/provider/ETL engine
One concrete artifact format
One runtime/process/worker topology
S7 Component Internal Design completion
Batch 4 authorization
RCP-23 full closure
S13 internal design
Implementation Planning / IWP / Coding
```

---

## 11. Revalidation Triggers

Revalidation is required if later work proposes to change materially:

- Native S7 Semantic Authority;
- Native S7 Canonical Definition SoT away from `ns_server`;
- factual Data/Knowledge per-partition SoT federation;
- first-class S7 domain non-subordination;
- complete source/visual authoring or interoperability commitments;
- a major stable definition-identity/history commitment beyond accepted semantics;
- a material offline fail-open/fail-closed policy;
- a major provider/protocol/storage/artifact-format lock-in.

---

## 12. Authority Boundary

This evidence records only the Project Owner MDE selection.

```text
Owner Decision
→ PERSISTED

Open MDE represented by GAC-EPOCH-0051 gate
→ ELIGIBLE TO CLOSE AFTER GOVERNANCE SYNCHRONIZATION

ns_server / Batch 4 / S7
→ NOT AUTHORIZED BY THIS DOCUMENT

Next legal GAC action
→ synchronize Registry / Working State / Ledger / Global State
→ fresh recover
→ reassess S7 Batch entry readiness
```
