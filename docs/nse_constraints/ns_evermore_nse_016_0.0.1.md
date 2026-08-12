# NSE-016 — Repository-backed Architecture Continuity and Recoverable Current Authority

## Document Authority Metadata

- **Document ID:** `NS-EVERMORE-NSE-016`
- **Version:** `0.0.1`
- **Stable Constraint ID:** `NSE-016`
- **Status:** `COMPLETED / AWAITING_GLOBAL_ACCEPTANCE`
- **Authority Level:** `ARCHITECTURE_CONSTRAINT_CANDIDATE`
- **Program / Phase:** `NGRP-001 Phase Z1 — Architecture Constraint Derivation / Batch 4`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Upstream Normative Inputs:** accepted Genesis Constitution; `ROOT-FACT-015`; `ROOT-FACT-016`; accepted `NSE-001..012`; Unified Governance 0.0.2; GAC-EPOCH-0012 Batch 4 authorization
- **Supersedes:** `NONE`
- **Superseded By:** `NONE`
- **Acceptance State:** `AWAITING_GLOBAL_ACCEPTANCE`
- **Acceptance Coordinate:** `PENDING / GLOBAL ARCHITECTURE COORDINATOR`

---

## 1. Problem

Architecture work occurs across multiple bounded sessions and may later continue through Implementation Planning, IWP, and Codex sessions whose chat context and model memory are transient. If architecture-critical authority, accepted semantics, pending decisions, current revision status, authorization scope, or drift state exists only in a prior conversation, a fresh session can unknowingly consume stale conclusions, guess missing context, treat candidate evidence as accepted, or continue beyond the legally authorized phase.

Repository storage alone is insufficient if current authority cannot be distinguished from historical, superseded, candidate, working, or non-normative evidence. Continuity therefore requires recoverable current authority, not merely document accumulation.

## 2. Normative Requirement

`ns_evermore` SHALL use current Repository evidence as persistent project memory and recoverable architecture authority. Chat context, model memory, oral recollection, or prior-session familiarity SHALL NOT be project authority.

Architecture-critical context necessary to determine the accepted baseline, current normative revisions, current phase/authorization, open MDEs, unpersisted Owner decisions, blocking items, drift state, required read set, and unique next legal action MUST be recoverable by a fresh authorized session from Repository evidence and the actual branch HEAD.

Current authority SHALL remain distinguishable from candidate, working-checkpoint, superseded, historical, or non-normative evidence. If recovery encounters unresolved conflict, unexplained drift, unauthorized progression, evidence ambiguity, or missing material authority, downstream work SHALL stop rather than reconstructing architecture from memory or implementation convention.

This constraint does not prescribe a repository directory layout, document database, prompt format, branch strategy, file naming scheme, or concrete continuity tool.

## 3. MUST

Future architecture, design, planning, and implementation-governance processes MUST:

1. preserve `Chat / Model Memory != Project Authority`;
2. preserve `Repository Current Authority → Persistent Project Memory`;
3. persist architecture-critical accepted semantics, formal decisions, acceptance coordinates, current normative revision references, authorization state, and material unresolved/blocking state before downstream reliance;
4. make current normative evidence distinguishable from candidate, historical, superseded, working, or non-normative evidence through Repository-backed authority/acceptance coordinates;
5. require a fresh session to resolve repository, branch, and actual HEAD before consuming current-state assumptions;
6. require fresh-session recovery to reconstruct the accepted constraint/design baseline, decision state, current authorization, blocking/drift state, and unique next legal action before material authorized work proceeds;
7. compare Repository state claims such as `State Verified Through HEAD` against the actual branch HEAD and classify intervening delta under the accepted continuity/drift model before proceeding;
8. treat unresolved Repository/evidence conflict, unexpected drift, unauthorized progression, unresolved Owner decision, or blocking item as a stop condition rather than as an invitation to infer missing authority;
9. preserve traceability from accepted architecture semantics and formal decisions to the Repository evidence/acceptance coordinates that make them current;
10. preserve enough current-state information that a session with no prior chat history can recover without requiring the previous model/session to explain what happened;
11. keep disposable user-facing bootstrap prompts non-authoritative unless the Project Owner explicitly changes the governance model; authorization facts must remain Repository-backed;
12. preserve current-tree simplification where practical without allowing removal/cleanup to erase accepted authority or make supersession ambiguous;
13. require later implementation/planning sessions to consume current accepted Repository authority rather than stale local copies or remembered prior chat outcomes;
14. require any material change to accepted authority, acceptance state, phase authorization, or supersession to be explicitly persisted before becoming current project truth.

## 4. MUST NOT

Future architecture, design, planning, or implementation governance MUST NOT:

1. define `Previous Chat = Current Project Authority`;
2. define `Model Memory = Accepted Architecture Evidence`;
3. allow architecture-critical decisions to remain solely in conversation while downstream work depends on them;
4. treat a candidate artifact as globally accepted merely because it exists in the Repository;
5. treat an old/superseded document as current merely because its internal metadata still says `CURRENT`, `NORMATIVE`, or `AWAITING_GLOBAL_ACCEPTANCE` without resolving current Global State/acceptance/supersession evidence;
6. continue material work when actual HEAD diverges from state claims through unexplained or unauthorized changes;
7. guess current authorization from branch name, directory name, file recency, commit message, or prior-session recollection alone;
8. infer missing Owner decisions, MDE outcomes, Authority/SoT choices, or phase authorization from implementation artifacts;
9. require a Repository-backed chat prompt document as the sole source of session authority under the current governance model;
10. select repository/package structure, branch workflow, documentation engine, indexing technology, prompt-generation tooling, or continuity automation within this constraint.

## 5. Long-term Invariant

```text
Chat / Model Memory != Project Authority
Repository Current Authority → Persistent Project Memory
Document Presence != Current Authority automatically
Candidate Evidence != Global Acceptance automatically
Historical Metadata != Current Authority automatically
Actual Branch HEAD → Recovery Coordinate
Unexplained Drift / Unauthorized Progression → STOP
Fresh Session → Recoverable without Prior Chat
Architecture-critical Context → Repository-backed before Downstream Reliance
```

Session boundaries and model-memory loss MUST NOT change the accepted architecture or legal next action.

## 6. Origin / Provenance

This constraint is derived only from current accepted Repository authority:

- Genesis Constitution §24 `Architecture-before-Implementation Invariants`;
- Genesis Constitution §27 `Required Derivation Order`;
- Genesis Constitution §28 `Repository-backed Continuity Constitution`;
- Genesis Constitution §29 `Independent Acceptance and Stop Discipline`;
- Genesis Constitution §30 `Genesis Historical Inheritance Rule`;
- `ROOT-FACT-015 — Repository evidence is persistent project memory; chat/model memory is non-authoritative`;
- `ROOT-FACT-016 — Independent Global Acceptance is mandatory`;
- Unified Governance §§11–16 current Repository recovery, required-read-set, authorization, bounded-session, identifier, and supersession rules;
- accepted `NSE-001..012`, whose semantics must remain recoverable across sessions;
- GAC-EPOCH-0012 Batch 4 authorization.

No prior chat transcript, model memory, obsolete session prompt, or pre-Genesis project state is used as a normative source.

## 7. Decision Classification

```text
Classification
INHERITED_FACT DERIVATION

New DAD
NONE

MDE
NONE
```

This constraint formalizes already accepted document-first continuity and independent acceptance semantics. It does not choose a repository layout, document system, branching strategy, prompt mechanism, automation tool, or governance database.

## 8. Rationale

Architecture continuity fails when project truth depends on who remembers the previous conversation. It also fails when the Repository contains many artifacts but a fresh session cannot determine which one is current. Recoverable current authority therefore requires both persistence and explicit acceptance/supersession/state semantics tied to Git coordinates.

The constraint freezes that recoverability requirement without prescribing a documentation or repository implementation.

## 9. Material Alternatives

Constraint-level alternatives considered:

- **Chat/model-memory continuity:** rejected because conversation/model state is transient and non-authoritative.
- **Repository archive without current-authority resolution:** rejected because document presence alone cannot distinguish accepted/current from candidate/historical evidence.
- **Repository-backed recoverable current authority with explicit drift/stop rules:** required.

Repository layout, branch model, document tooling, indexing, prompt generation, and automation remain deferred.

## 10. Affected Architecture Dimensions

This constraint materially affects future:

- architecture/document authority;
- acceptance and supersession;
- decision traceability;
- phase authorization;
- cross-session recovery;
- drift and conflict handling;
- current normative revision resolution;
- Implementation Planning / IWP / Codex entry recovery;
- compatibility/migration evidence continuity;
- conformance and auditability.

## 11. Semantic Resolution Notes

- **Identity / Namespace:** current authority must identify the relevant project/phase/artifact/decision coordinates; exact document naming conventions are deferred.
- **Revision / Evolution:** current-vs-historical/superseded revision status must be recoverable; versioning mechanics remain governance/document concerns.
- **Authority / Semantic Ownership:** Repository evidence records authority; file placement does not create semantic authority. Decision authority remains defined by Unified Governance.
- **Source of Truth / Actual-state Ownership:** Repository current authority is the source for project governance/design truth, not automatically for runtime/business-domain state.
- **State / Lifecycle / Temporal:** candidate, accepted, working, superseded, blocked, and authorized states must remain distinguishable; no generic document state machine is selected here.
- **Failure / Unknown / Indeterminate:** conflict, ambiguity, unexpected drift, unauthorized progression, unresolved decision, or missing authority is explicit and can require stop/reconciliation.
- **Tenant / Organization:** accepted `NSE-001..003` remain recoverable and cannot be bypassed by session loss.
- **Principal / Authentication / Authorization / Policy:** this constraint governs project-design authority, not runtime authentication; no runtime authority is allocated.
- **Security / Data / Privacy / Trust:** continuity evidence must not erase accepted trust/security constraints; concrete repository security controls are deferred.
- **Serialization / Representation:** no document format, index format, prompt format, or repository representation is selected.
- **Offline / Degraded:** Repository-backed recovery must support the private/offline project lifecycle; no mandatory public continuity service is introduced.
- **Recovery / Reconciliation:** fresh-session and drift recovery are mandatory governance behaviors; tooling is deferred.
- **Compatibility / Migration:** current authority must preserve accepted historical interpretation/compatibility decisions where applicable.
- **Conformance:** a fresh session must be able to reconstruct current legal state without prior chat history.
- **Cross-boundary Dependency:** downstream phases depend on accepted Repository authority, not conversation state.
- **Invariant / Decision Traceability / Revalidation:** defined in this record.

## 12. Revalidation Trigger

Revalidate only if the Project Owner explicitly changes one or more of:

- document-first / Repository-backed continuity;
- the rule that chat/model memory is non-authoritative;
- independent acceptance/current-authority resolution requirements;
- the requirement that fresh sessions recover from Repository evidence and actual Git state.

Changing repository directory layout, branch naming, documentation tooling, prompt generation, file naming, or indexing technology is not by itself a revalidation trigger.

## 13. Status

```text
NSE-016
COMPLETED / AWAITING_GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTED / NORMATIVE
NO
```