# NGRP-001 Phase Z3 / Batch 2 — Internationalization and Localization Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **MDE Classification:** `NO`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Decision Predecessor HEAD:** `0c686c34e51667743d6b7c7f6c4c0d70255777be`
- **Current Global State at Decision:** `GAC-EPOCH-0022`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Shall `ns_evermore` treat product internationalization and multi-language localization as a first-class long-term product capability, rather than allowing human-facing UI/messages to depend on one fixed natural language?

The question applies to system-generated human-facing interaction across applicable surfaces, including `ns_web`, SDK/CLI feedback, validation/conformance messages, operation state presentation, Human Task presentation, notifications, governance/configuration interaction, Agent/Automation product chrome and similar product-owned messages.

This question does **not** ask whether the platform must automatically translate arbitrary user business content, Knowledge content, Agent user content, Definition business text, or customer data.

---

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

### Why Product-significant

The choice materially affects:

```text
UI architecture
Error/message semantics
Notification rendering
Human Task rendering
SDK/CLI user-facing feedback
Extension/re-delivery behavior
Enterprise/multinational deployment
Long-term migration cost
```

A single-language assumption can become deeply embedded in UI, error handling, notification templates and extension contracts. Conversely, a language-neutral semantic model with localizable presentation creates a durable compatibility boundary.

### Why not MDE

This decision does not move or redefine Tenant, Principal, IAM, Policy, Product Definition, Artifact Acceptance, Execution Admission, Runtime Actual-state or other existing semantic authorities/SoTs. It defines a human-facing presentation capability and its compatibility discipline.

---

## 3. Options Considered

### Option A — Single-language Product

The product formally guarantees only one primary language. Additional languages may be introduced later, with no architectural localization guarantee.

**Benefits**

- Lowest implementation cost.
- Simplest initial UI/message handling.

**Costs / Risks**

- High risk of natural-language strings becoming embedded in product logic.
- Future localization may require invasive migration across UI, validation, notification and extension surfaces.
- Re-delivery to multilingual/private enterprise environments becomes harder.

**Long-term Impact**

- Product semantics and display language tend to become entangled.

**Compatibility / Migration Impact**

- Later introduction of localization likely requires broad message/error contract cleanup.

**Offline / Private Impact**

- Simple, but no multilingual capability guarantee.

**Cross-component Impact**

- Minimal immediate cross-component pressure.

### Option B — First-class Internationalization + Pluggable Localization

The product SHALL be internationalization-ready and SHALL support multiple localized product presentation locales while preserving language-neutral stable semantics.

Core semantic separation:

```text
Semantic Identity
!= Display Language

Error / State Code
!= Localized Text

Definition Semantics
!= UI Translation

Canonical Data
!= Localized Presentation
```

Applicable system-generated human-facing information SHALL be localizable, including applicable:

```text
ns_web UI
SDK / CLI human-readable feedback
Validation / Conformance / Compatibility feedback
Errors / Warnings
Operation state presentation
Human Task presentation
Notification presentation
Configuration / Governance interaction
Agent / Automation product chrome
```

User-authored business content, Knowledge content, Agent user content, customer data and Definition business text are not automatically translated merely because product localization exists.

Locale is an explicit interaction/presentation context and remains distinct from Tenant, Principal identity and timezone:

```text
Locale != Tenant
Locale != Principal Identity
Locale != Timezone
```

Timezone-aware temporal presentation is independently required by temporal/history semantics and SHALL NOT be inferred from language/locale.

**Benefits**

- Avoids late-stage i18n retrofit.
- Preserves stable language-neutral semantics across UI, SDK and external integrations.
- Supports multinational/private enterprise deployments and re-delivery.
- Prevents localized text from becoming protocol or state identity.

**Costs**

Later detailed design must handle localization resources, fallback, interpolation, formatting, extension localization and missing-translation behavior.

**Risks / Complexity**

The principal prohibited failure is allowing localized strings to become machine-recognizable semantic identity, e.g. using localized status text to drive logic.

**Long-term Impact**

Language-neutral semantics become a durable compatibility rule while presentation locales may evolve independently.

**Compatibility / Migration Impact**

Stable semantic codes/identities and parameterized message context form the compatibility boundary; exact wording/translations do not become semantic identity.

**Offline / Private Impact**

Localization resources required for supported locales SHALL be deployable locally. Core product usability SHALL NOT depend on an online translation SaaS.

**Cross-component Impact**

Applicable human-facing projections from all five components and system-level SDK/CLI must preserve stable semantics and localizable presentation without moving the underlying semantic authority.

### Option C — Full Multilingual Content Translation Platform

In addition to product localization, require native automatic translation/version synchronization for arbitrary user business content, Agent content, Definition text, Knowledge content and similar business data.

**Benefits**

- Strongest multilingual content capability.

**Costs / Risks**

- Introduces translation-provider, translation-memory, terminology, review, privacy and content-revision governance pressure.
- Expands `ns_evermore` into a translation/content-management platform.

**Long-term / Compatibility Impact**

- High continuing product and migration burden.

**Offline / Private Impact**

- Significantly harder without local translation infrastructure.

**Cross-component Impact**

- Broad and disproportionate to this Batch's interaction baseline.

---

## 4. Recommendation

```text
Recommendation
→ B — First-class Internationalization + Pluggable Localization
```

Rationale:

```text
Stable Semantics
→ LANGUAGE_NEUTRAL

Product UI Localization
→ REQUIRED

System-generated Human-facing Messages
→ LOCALIZABLE

Multiple Locales
→ SUPPORTED

Exact Initial Language Set
→ DEFERRED

User Business Content Auto-translation
→ NOT IMPLIED

Online Translation Service
→ NOT CORE DEPENDENCY

Timezone
→ INDEPENDENT FROM LOCALE
```

This provides the durable interaction boundary needed by a private/offline, extensible enterprise platform without turning localization into a new semantic authority or a translation-platform mandate.

---

## 5. Owner Selection

The Project Owner selected:

```text
OPTION B
```

### Explicit Selected Result

```text
FIRST_CLASS_INTERNATIONALIZATION
+ PLUGGABLE_MULTI_LANGUAGE_LOCALIZATION
→ REQUIRED
```

Normative capability consequences:

1. Stable machine-recognizable product semantics SHALL remain language-neutral.
2. Applicable product-owned human-facing UI/messages SHALL be localizable.
3. Multiple locales SHALL be supported as a product capability.
4. Locale SHALL remain separate from Tenant, Principal identity and timezone.
5. Timezone-aware presentation remains independently required and SHALL NOT be inferred from locale.
6. Localized natural-language strings SHALL NOT become semantic identity, protocol identity, state identity, authority evidence or authorization evidence.
7. Applicable localization resources SHALL be usable in private/offline deployments without mandatory online translation services.
8. Automatic translation of arbitrary user/customer business content is not implied.

---

## 6. Authority / Source-of-Truth Preservation

This decision does not alter any existing authority or canonical SoT.

Preserved examples include:

```text
Tenant Semantic Authority / Tenant SoT
→ ns_server

IAM Semantic Authority
→ ns_server

Policy Semantic Authority
→ ns_server

Business Application Definition SoT
→ ns_server

Automation Definition SoT
→ ns_server

Native Agent Definition SoT
→ ns_agent

Artifact Acceptance Authority
→ ns_server

Execution Admission Authority
→ ns_server

Runtime Actual-state
→ existing bounded semantic partitions
```

Localization is presentation. A localized projection does not become the semantic authority for the underlying state/fact/resource.

---

## 7. Non-implications

This decision does **not** imply:

```text
one mandatory UI framework
one mandatory localization library
one mandatory locale identifier representation
one mandatory translation file format
one mandatory message-template engine
automatic translation of user-authored content
AI translation
online translation SaaS dependency
one locale per Tenant
locale inferred from timezone
timezone inferred from locale
localized text as machine semantic identity
```

It also does not authorize Component Internal Design, Runtime Responsibility Architecture, Shared Foundation design, provider selection, contract/schema design or implementation.

---

## 8. Named Deferrals

Deferred to later properly authorized work:

```text
initial supported language set
locale identifier standard
locale preference resolution
fallback hierarchy
translation packaging/resource format
pluralization/interpolation mechanics
date/number/currency formatting mechanics
extension/plugin localization contract
notification template localization mechanics
SDK/CLI localization mechanics
missing-translation behavior
runtime/component responsibility allocation
API/schema/contract realization
implementation technology
```

These deferrals do not weaken the selected product capability requirement.

---

## 9. Revalidation Triggers

This Owner decision SHALL be revalidated if a later proposal would:

- remove first-class product localization capability;
- make localized natural-language text part of stable semantic identity;
- require one locale per Tenant;
- couple locale and timezone as the same semantic concept;
- require public/online translation services for core private/offline product usability;
- expand the selected capability into mandatory automatic translation of arbitrary business content;
- move semantic authority to a localization or presentation subsystem.

---

## 10. Bounded Authority

This evidence records only the Project Owner's Batch 2 product-capability selection.

It does **not**:

```text
claim Global Acceptance
advance GAC Epoch
authorize Z3 Batch 3
declare capability exhaustion
declare Five-component Internal Architecture Boundaries complete
enter Five-component Internal Boundary Synthesis
enter Component Internal Design
enter Runtime Responsibility Architecture
enter Shared Foundation Architecture
enter Foundation Contract / Module / Provider Design
enter Implementation Planning / IWP / Coding
```

The maximum status represented here is:

```text
OWNER_CAPABILITY_DECIDED / PERSISTED
AWAITING LATER BATCH-LEVEL REVIEW AND GLOBAL ACCEPTANCE
```
