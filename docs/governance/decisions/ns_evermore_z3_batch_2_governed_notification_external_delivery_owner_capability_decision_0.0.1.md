# NGRP-001 Phase Z3 / Batch 2 — Governed Notification and External Delivery Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 2`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_2 / USER_OPERATOR_DEVELOPER_INTERACTION_EXPERIENCE_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **MDE Classification:** `YES`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Recovered Batch Entry HEAD:** `e1fdd822fcfae2827ea93cf859c405db9faf7d7d`
- **Decision Predecessor HEAD:** `01c008ed6078bfae59fef3fb133d54421d61fdbb`
- **Current Global State at Decision:** `GAC-EPOCH-0022`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

What product-level awareness and notification capability SHALL ns_evermore provide for important governed events and state transitions that a user or operator should know about but that do not necessarily require an immediate Human Task action?

This decision also determines whether external notification delivery is merely an unspecified future possibility, a required channel-neutral extensibility capability, or a mandatory fixed omnichannel product commitment.

Representative awareness pressure includes:

```text
Long-running operation completion/failure
Agent completion/failure
Automation completion/failure
Trial completion/warnings
Node unreachable/recovered
Desired / Applied configuration divergence
PARTIALLY_APPLIED configuration
Provider unavailable/recovered
Recovery outcome
Reconciliation pending/completed
Compatibility/conformance condition changes
```

This capability MUST remain distinct from the already-selected Unified Governed Human Task Inbox:

```text
Human Task Inbox
→ What needs my action?

Notification / Awareness
→ What happened that I should know about?
```

---

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ YES
```

### Why Product-significant

The choice materially affects:

```text
End-user awareness model
Operator workflow
Background/unattended execution experience
Cross-domain notification consistency
Historical awareness behavior
External delivery integration expectations
Customer private-deployment integration
Delivery/re-delivery extensibility
Offline/degraded delivery semantics
```

### Why MDE

This decision establishes a long-lived cross-domain compatibility commitment around notification identity/correlation/history and external delivery extensibility. If external delivery semantics or providers were bound directly into core semantics, migration and compatibility cost could be high. Under Unified Governance, major compatibility and high-migration-cost commitments are Owner-reserved; uncertainty therefore defaults to MDE.

---

## 3. Options Considered

### Option A — Pull-only Awareness

No unified notification capability. Users and operators discover events only by opening applicable operation history, Agent/Automation history, diagnostics, Node status, configuration status, audit/provenance, or other domain surfaces.

**Benefits:** lowest product and architecture scope; minimal delivery semantics.

**Costs:** poor unattended/background awareness; repeated notification implementations in Business Applications and delivery projects are likely.

**Risks / Long-term Impact:** domain-specific notification fragmentation; later unification would require migration of already-divergent notification semantics.

**Offline / Private:** simplest.

**Cross-component:** lowest pressure.

### Option B — Unified Governed Notification Capability with Channel-neutral Core and Pluggable External Delivery

Provide a formal governed Notification / Awareness capability with in-product discoverability/history and stable correlation to underlying governed facts, while keeping notification semantics independent from any particular delivery platform.

External delivery SHALL be supported through pluggable/adaptable channels rather than becoming a correctness dependency of core notification semantics.

**Benefits:** consistent background/unattended awareness; Human Task and Notification remain separate; private deployments can choose applicable channels; external platform integration does not become semantic authority.

**Costs:** later architecture must define notification identity, audience/principal and Tenant binding, source correlation, occurrence time, classification/severity, history, read/acknowledgement semantics, delivery-attempt state, authorization/redaction, and channel failure semantics.

**Risks / Complexity:** notification projections could be mistaken for current-state truth; channel delivery could be mistaken for user observation; external adapter ecosystem requires governance.

**Long-term Impact:** stable platform-level awareness primitive plus extensible external delivery.

**Compatibility / Migration:** notification semantic classes/identity/correlation/history become compatibility-sensitive; transport/provider details do not become core semantic contracts merely by being supported.

**Offline / Private:** core notification capability MUST function fully in private/offline deployment. External channel unavailability MUST be represented without losing the underlying notification.

**Cross-component:** governed awareness pressure may originate from multiple bounded semantic/runtime owners and be projected to human-facing surfaces without authority transfer.

### Option C — Mandatory Enterprise Omnichannel Notification Hub

Require a fixed broad set of native external delivery channels as a core product commitment, making ns_evermore an enterprise omnichannel notification hub.

**Benefits:** strongest out-of-product reach.

**Costs / Risks:** provider integration, credentials, retry/rate-limit, templating, recipient addressing, delivery receipts, privacy, and provider-specific semantics become large permanent product obligations; high risk of provider/protocol lock-in and expanding beyond the platform's primary architecture purpose.

**Offline / Private:** most difficult because some channels inherently require external connectivity.

**Cross-component:** largest cross-cutting pressure.

---

## 4. Recommendation Presented

```text
Recommendation
→ B — Unified Governed Notification Capability
     with channel-neutral core semantics
     and pluggable external delivery
```

Rationale:

```text
Human Task
→ actionable human work

Notification
→ awareness/history

Operational / Domain Views
→ current governed state and diagnostics
```

These concepts should remain separate. A channel-neutral governed notification model supports unattended Agent/Automation/Node/configuration/recovery use cases without turning SMTP, SMS, Feishu, WeCom, or any SaaS provider into a core system dependency.

---

## 5. Project Owner Selection

The Project Owner selected:

```text
B
```

The Project Owner additionally clarified:

> External message push is an intended product capability. The platform should support delivery to external platforms such as Feishu, WeCom, and SMS.

---

## 6. Explicit Selected Result

```text
UNIFIED_GOVERNED_NOTIFICATION_CAPABILITY
→ REQUIRED

IN_PRODUCT_NOTIFICATION_DISCOVERY_AND_HISTORY
→ REQUIRED

CHANNEL_NEUTRAL_CORE_NOTIFICATION_SEMANTICS
→ REQUIRED

PLUGGABLE_EXTERNAL_NOTIFICATION_DELIVERY_CAPABILITY
→ REQUIRED

EXTERNAL_PLATFORM_PUSH
→ REQUIRED AS A PRODUCT CAPABILITY

REPRESENTATIVE / INITIAL TARGET CHANNEL DIRECTIONS
→ FEISHU
→ WECOM / ENTERPRISE WECHAT
→ SMS

MANDATORY FIXED OMNICHANNEL PROVIDER SET
→ NOT REQUIRED BY THIS DECISION

PUBLIC INTERNET / PUBLIC SAAS DEPENDENCY FOR CORE CORRECTNESS
→ PROHIBITED
```

The named external channels are explicit product integration targets/directions, but their existence MUST NOT make those providers semantic authorities or mandatory dependencies for core notification correctness.

---

## 7. Normative Consequences

### 7.1 Human Task and Notification remain distinct

```text
Needs Human Action
!= Needs Human Awareness

Human Task Inbox
!= Notification Center

Notification
!= Human Task automatically
```

A notification may correlate to a Human Task, but the two MUST retain distinct meaning and lifecycle.

### 7.2 Notification is a governed awareness projection, not Source of Truth

```text
Notification
!= Source Fact

Notification Center
!= Runtime Actual-state Owner

Notification History
!= Current State

Notification Delivered
!= Underlying Condition Still True

Notification Read
!= Problem Resolved

Notification Acknowledged
!= Policy Approved
```

Example:

```text
Node becomes UNREACHABLE
→ governed notification may be created

Node later reconnects
→ bounded runtime actual-state owner establishes new current state

Historical unreachable notification
→ remains awareness/history evidence
→ does not remain canonical current Node state
```

### 7.3 External delivery is required capability, but channel-neutral

The product SHALL support external push through governed pluggable delivery adapters/channels.

The explicitly stated target directions include:

```text
Feishu
Enterprise WeChat / WeCom
SMS
```

However:

```text
Feishu transport/protocol
!= Core Notification Semantics

WeCom transport/protocol
!= Core Notification Semantics

SMS provider/protocol
!= Core Notification Semantics
```

The core notification model MUST be able to support future channels without rewriting the semantic meaning of a Notification.

### 7.4 Delivery state is separate from notification existence

```text
Notification Created
!= External Delivery Succeeded

Delivery Attempt Accepted
!= Recipient Observed Message

Delivery Failed
!= Underlying Operation Failed

External Channel Unreachable
!= Notification Lost
```

In private/offline/degraded environments, a Notification may validly exist while one or more configured external delivery channels are:

```text
UNAVAILABLE
UNREACHABLE
UNSUPPORTED
FAILED
PENDING
INDETERMINATE
```

The final vocabulary/mechanics remain downstream design work, but semantic collapse is prohibited.

### 7.5 Authorization and privacy are preserved across external delivery

External delivery MUST NOT bypass applicable Principal, Tenant, authorization, privacy, redaction, secret, or policy boundaries.

A delivery adapter MUST consume only the information it is authorized to receive for the intended audience/channel context.

---

## 8. Authority / SoT Preservation

This decision does NOT change any accepted Authority or SoT topology.

In particular:

```text
Tenant Semantic Authority
→ ns_server

IAM Semantic Authority
→ ns_server

Policy Semantic Authority
→ ns_server

Formal Artifact Acceptance Authority
→ ns_server

Formal Execution Admission Authority
→ ns_server

Platform Security / Trust Semantic Authority
→ ns_server

Business Application Definition SoT
→ ns_server

Automation Definition SoT
→ ns_server

Native Agent Definition SoT
→ ns_agent

Runtime Actual-state
→ remains owned per bounded runtime semantic partition

Notification Surface / Delivery Adapter
→ NOT an Authority or canonical SoT merely because it presents or delivers a notification
```

No notification channel acquires authority over the underlying source fact, current state, policy, admission, acceptance, principal, Tenant, or trust semantics.

---

## 9. Non-implications

This Owner decision does NOT imply:

```text
Notification == Human Task
Notification == Runtime Actual-state
Notification == Audit Record
Notification == Diagnostic Finding
Notification == Policy Decision
Notification == Execution Admission
Notification == Artifact Acceptance
Delivery success == human observation
Read == resolution
Acknowledgement == approval
Every event == notification
Every notification == external push
Every deployment must configure an external channel
Every external channel must be reachable offline
Feishu/WeCom/SMS are mandatory semantic dependencies
A single provider/protocol/SDK is frozen
A universal template language is frozen
A universal retry policy is frozen
```

It also does NOT declare a universal Enterprise Attention Center.

---

## 10. Named Deferrals

The following are explicitly deferred to separately authorized downstream work:

```text
Notification component/internal owner allocation
Notification schema/API/contract
Notification persistence mechanism
Notification routing architecture
Notification preference model
Notification severity taxonomy
Read/unread/acknowledgement exact state machine
Recipient/group addressing model
Template/rendering model
Delivery retry/backoff policy
Delivery queue mechanism
Provider credential storage mechanism
Adapter/plugin architecture details
Feishu API integration details
WeCom API integration details
SMS provider selection and integration details
Webhook/email/other future channel details
Rate-limit handling
Delivery receipt normalization
Offline queue/reconciliation mechanics
UI page/layout/detail design
Implementation technology
Implementation planning / IWP / coding
```

The exact set of adapters shipped in a particular release is not frozen by this capability decision. What is frozen at this checkpoint is the product requirement that governed external notification delivery be supportable and that Feishu, WeCom, and SMS are explicit target integration directions.

---

## 11. Revalidation Triggers

This decision MUST be revalidated if any later work proposes to change:

```text
Human Task vs Notification separation
Notification as projection vs authority/SoT
Channel-neutral core semantics
Required external-delivery extensibility
Private/offline core correctness
Feishu / WeCom / SMS target integration intent
Principal/Tenant/privacy boundaries for notification delivery
Historical notification compatibility commitments
```

A proposal to make one external provider/protocol mandatory for core correctness, or to promote Notification into a current-state authority, SHALL require explicit governance re-entry.

---

## 12. Bounded Authority Statement

This evidence records only the Project Owner's Batch 2 product capability decision.

It does NOT:

```text
claim Global Acceptance
advance GAC Epoch
authorize Z3 Batch 3
declare Z3 capability exhaustion
declare Five-component Internal Architecture readiness
enter Five-component Internal Boundary Synthesis
allocate component-internal modules/providers
enter Runtime Responsibility Architecture
enter Shared Foundation Architecture
select Foundation Contracts/Modules/Providers
enter Implementation Planning / IWP / Coding
```

The producing session remains bounded to the authorized Z3 Batch 2 interaction-experience capability discovery checkpoint.
