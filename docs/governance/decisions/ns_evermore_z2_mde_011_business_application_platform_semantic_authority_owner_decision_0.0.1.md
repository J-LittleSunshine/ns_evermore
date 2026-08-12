# NGRP-001 Z2 MDE-011 — Business Application Platform Semantic Authority Owner Decision

- **Decision ID:** `Z2-MDE-011`
- **Program / Phase:** `NGRP-001 Phase Z2 — Project Architecture Synthesis / Batch 1`
- **Scope:** `PROJECT_ARCHITECTURE_SYNTHESIS_ONLY / BATCH_1 / SYSTEM_BOUNDARY_COMPONENT_RESPONSIBILITY_TOPOLOGY`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / MDE`
- **Decision Entry HEAD:** `2ecbf5ab4a3af6f7af8ad1438ca02c20b849edac`
- **Current Global State at Decision:** `GAC-EPOCH-0014`
- **Upstream Normative Inputs:** Genesis Constitution; Unified Governance 0.0.2; Decision Registry 0.0.4; accepted `NSE-001..017`; current Z2 Batch 1 authorization; Owner-decided `Z2-MDE-001..010`
- **Global Acceptance:** `NOT CLAIMED BY THIS BOUNDED SESSION`

---

## 1. Material Question

Which Product Architecture boundary owns final native **Business Application Definition / Platform Semantic Authority** for `ns_evermore`?

This decision concerns the platform-level meaning of Business Application definition, revision, composition, governed configuration meaning, application semantic lifecycle, and application runtime semantic identity.

It does **not** assign Source-of-Truth or semantic authority for customer-specific business-domain facts such as patient, order, appointment, medical record, ERP transaction, CRM account, or other external/business entities. Those remain independently governed by their applicable business domain and bounded external Source-of-Truth relationships.

It also does not decide persistence, database topology, builder implementation, API/schema, package layout, runtime process topology, or detailed Business Application internal architecture.

## 2. Classification

```text
Classification
MDE

Reason
Business Application Definition / platform semantic ownership is a major cross-component Semantic Ownership decision for one of the four principal first-class capability domains. Unified Governance reserves material Semantic Ownership to Project Owner authority.
```

## 3. Alternatives Presented to Project Owner

### A — `ns_server` owns native Business Application Definition / Platform Semantic Authority

`ns_server` is the final semantic authority for platform-level Business Application definition, revision, composition, governed configuration meaning, application lifecycle meaning, and application runtime semantic identity. `ns_web` provides Builder/UI interaction but does not gain authority by editing. Other Product Components may participate in execution or provide composed first-class capabilities without acquiring Business Application semantic ownership.

### B — `ns_web` owns Business Application Definition Authority

The Builder/UI side becomes authoritative for application definitions while `ns_server` acts as backend realization/runtime consumer. This risks converting frontend/browser state or UI implementation into canonical architecture authority.

### C — Per-Application / Artifact-owned Semantic Authority

Each Business Application becomes its own authoritative semantic island and `ns_server` acts as a generic host. This materially increases federation, lifecycle, compatibility, and Definition/Artifact/Runtime conflation risk.

## 4. Recommendation Presented

`A — ns_server owns native Business Application Definition / Platform Semantic Authority`.

Rationale: the Constitution places Business Application Construction / Runtime backend responsibility in `ns_server` and Business Application Builder/UI responsibility in `ns_web`, while explicitly forbidding frontend state, UI routing, framework placement, and physical placement from becoming canonical architecture authority. Selecting `ns_server` establishes one stable platform-semantic authority without making the UI, runtime coordination, local execution, Agent execution, persistence, or Artifact placement authoritative.

This does not subordinate Automation, AI Agent, or Enterprise Data / Knowledge to the Business Application domain. The four principal capability domains remain `FIRST_CLASS / PARALLEL / NON_SUBORDINATE`.

## 5. Project Owner Decision

```text
Selected Option
A

Native Business Application Definition / Platform Semantic Authority
→ ns_server
```

The Project Owner explicitly selected Option `A` in the authorized bounded Z2 Batch 1 session.

## 6. Normative Consequences for Current Batch

The current Project Architecture candidate MAY consume the following Owner-decided facts:

```text
ns_server
→ owns native Business Application Definition / Platform Semantic Authority

ns_web
→ owns Business Application Builder / UI interaction responsibility
→ does not gain Business Application semantic authority through editing, browser state, frontend cache, routing, or presentation

ns_runtime
→ may coordinate applicable runtime activity
→ does not gain Business Application semantic authority through routing, scheduling, dispatch, communication, or runtime observation

ns_node
→ may execute Automation/local/tool capabilities used by a Business Application
→ does not gain Business Application authority through execution or local effects

ns_agent
→ may provide AI Agent capabilities invoked by a Business Application
→ does not gain Business Application authority through invocation or reasoning execution
```

## 7. First-class Capability Non-subordination

This decision MUST preserve:

```text
Business Application Construction / Runtime
Automation Construction / Execution
AI Agent Runtime / Tooling
Enterprise Data / Knowledge / foundational ETL
→ FIRST_CLASS / PARALLEL / NON_SUBORDINATE
```

Therefore:

```text
Business Application invokes Automation
!= Automation authority transfer

Business Application invokes AI Agent
!= Agent authority transfer

Business Application consumes Enterprise Data / Knowledge
!= Data / Knowledge authority or SoT transfer

Same ns_server placement for multiple authority domains
!= domain subordination
!= common semantic ownership
!= common Source of Truth
```

## 8. Explicit Non-Implications

This decision MUST NOT be interpreted as establishing any of the following automatically:

```text
Business Application Platform Authority = Customer Business Domain Authority
Business Application Platform Authority = Business Data SoT
Business Application Platform Authority = Automation Authority
Business Application Platform Authority = AI Agent Authority
Business Application Platform Authority = Data / Knowledge Authority
Business Application Platform Authority = Policy Authority
Business Application Platform Authority = Artifact Acceptance Authority
Business Application Platform Authority = Execution Admission Authority
Business Application Platform Authority = Runtime Coordination Authority
Business Application Platform Authority = Database Ownership
Business Application Platform Authority = Universal ns_server Authority
```

## 9. Relation to Prior Owner Decisions

The following remain distinct authority domains even where physically placed in `ns_server`:

```text
Tenant Semantic Authority
→ ns_server

Tenant Canonical SoT
→ ns_server

Native IAM Semantic Authority
→ ns_server

Unified Policy Semantic Authority
→ ns_server

Native Organization Semantic Authority
→ ns_server

Formal Artifact Acceptance Authority
→ ns_server

Formal Execution Admission Authority
→ ns_server

Automation Definition / Workflow Semantic Authority
→ ns_server

AI Agent Definition / Semantic Authority
→ ns_agent

Business Application Definition / Platform Semantic Authority
→ ns_server
```

Co-location does not merge their semantics or authority boundaries.

## 10. Constraint Preservation

This decision preserves:

- `NSE-001..004` Tenant/Organization/offline invariants;
- `NSE-005` Product Component / Runtime non-conflation;
- `NSE-006` first-class capability non-subordination and authority non-transfer;
- `NSE-007` Definition / Artifact / Runtime separation;
- `NSE-009` stable language-neutral contract independence;
- `NSE-010` extension/re-delivery governance;
- `NSE-011` external Source-of-Truth preservation;
- `NSE-013` complete-system semantic integrity;
- `NSE-016` Repository-backed continuity;
- `NSE-017` downstream architecture non-invention.

## 11. Downstream Consumers

This Owner decision is an authorized input to:

- the current Z2 Batch 1 Project Architecture Candidate;
- the Batch 1 Responsibility / Authority / SoT Matrix;
- later Business Application Component capability inventory and internal architecture;
- later Contract and Runtime responsibility design where Business Application semantics are consumed;
- future Business Application Builder design, without making the Builder authoritative.

No downstream phase is authorized by this evidence.

## 12. Revalidation Trigger

Revalidation is required if the Project Owner later changes native Business Application platform semantic ownership away from `ns_server`, changes the fixed Product Component topology, changes Business Application from a first-class principal capability domain, or explicitly changes the non-subordination relationship among principal domains.

Changes in Vue/Django implementation, Builder UX, database, process/service/container topology, package layout, runtime scheduler, provider, transport, or persistence placement do not by themselves revalidate this decision.

## 13. Bounded-session Authority Limit

This evidence records a Project Owner MDE decision. It does not constitute Global Acceptance, does not advance the GAC Epoch, does not authorize Z2 Batch 2, and does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation Detailed Design, Implementation Planning, IWP, or coding.
