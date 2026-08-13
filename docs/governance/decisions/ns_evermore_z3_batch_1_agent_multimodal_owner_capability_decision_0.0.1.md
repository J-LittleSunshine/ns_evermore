# NGRP-001 Phase Z3 / Batch 1 — Native Agent Multimodal Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Authorization Scope:** `FIVE_COMPONENT_INTERNAL_ARCHITECTURE_BOUNDARIES_ONLY / BATCH_1 / COMPONENT_AND_COMMON_CAPABILITY_DISCOVERY_OWNER_CHECKPOINT`
- **Repository:** `J-LittleSunshine/ns_evermore`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Global Acceptance:** `NOT CLAIMED`

---

## 1. Material Capability Question

Should the native `ns_agent` semantic domain remain text-centric with non-text inputs mediated only through tools/extensions, or should native Agent Definition / Context / Interaction semantics directly support multimodal content?

This is a product-significant capability question. It does not ask whether a particular model provider happens to support images/audio/video; provider capability cannot define Agent product semantics by placement.

Accepted upstream ownership remains unchanged:

```text
AI Agent Definition / Semantic Authority
→ ns_agent

AI Agent Canonical Definition SoT
→ ns_agent

Model / AI Provider
→ bounded provider capability
→ NOT Agent Semantic Authority
```

## 2. Classification

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO

Reason
→ Native multimodal semantics materially affect the Agent product boundary and developer/user experience.
→ The decision does not move Authority, Source of Truth, Actual-state Ownership, Tenant, IAM, Policy, Trust, Artifact Acceptance or Execution Admission ownership.
```

## 3. Durable Alternatives Presented

### Option A — Text-centric Native Agent

Native Agent semantics remain text/structured-data oriented. Image/audio/video/media must first be processed by a Tool, `ns_node`, extension or external capability into text/structured facts before Agent consumption.

### Option B — Native Multimodal Agent Semantics

Native Agent semantics directly permit applicable multimodal content as Agent context / interaction content, including text, image, audio, video/media where later supported, document/media content and structured data.

Provider support remains capability-specific:

```text
Native Agent supports modality X
!= every Model Provider supports modality X
```

### Option C — Multimodal only through Extension / Tool capability

The product formally supports multimodal Agent experiences, but non-text modalities remain represented only through Tool/Extension composition rather than as native Agent semantics.

## 4. Recommendation Presented

`B — Native Multimodal Agent Semantics`.

Rationale:

- AI Agent is a first-class capability domain and should not be permanently constrained by text-centric provider/API assumptions;
- multimodal capability should remain provider-neutral and compatible with local/private/internet model support;
- native multimodal semantics avoid forcing every provider-native image/audio/document capability through an artificial Tool-only abstraction;
- `ns_node` OCR/local execution responsibilities remain independent and are not transferred to `ns_agent`;
- offline/private correctness can still be preserved through local/private multimodal model or tool realizations.

## 5. Project Owner Decision

```text
Selected Option
→ B

Native Agent Multimodal Capability
→ REQUIRED

Native Agent Semantic Domain
→ MUST permit applicable multimodal context / interaction semantics

AI Agent Semantic Authority
→ ns_agent / UNCHANGED

AI Agent Canonical Definition SoT
→ ns_agent / UNCHANGED
```

## 6. Normative Capability Consequences for Z3 Batch 1

The Z3 Batch 1 capability baseline may consume the following Owner-decided capability:

```text
ns_agent
→ MUST support Native Agent definitions/runtime semantics that can operate over applicable multimodal content

Applicable modalities
→ may include text, image, audio, video/media, document/media content and structured data
→ exact supported modality profile is later design/evolution

Model / Provider capability
→ may support a subset of native Agent modalities
→ unsupported combinations must remain explicit
```

Permanent rules:

```text
Provider-native Multimodality
!= Provider becomes Agent Semantic Authority

Native Agent Multimodality
!= ns_agent gains OCR/local-device authority

Multimodal Context
!= Data / Knowledge Source-of-Truth transfer

Multimodal Agent
!= Mandatory Internet Model
```

## 7. Explicit Non-implications / Deferred Mechanics

This capability decision does **not** decide:

```text
image schema
media schema
audio/video codec
streaming model
file representation
media storage
multimodal message format
provider capability-negotiation protocol
context-window strategy
tokenization
modality conversion pipeline
transport
runtime process topology
provider selection
```

Named later authority:

```text
Five-component Internal Architecture Boundary Synthesis
→ only after separate GAC authorization

Runtime Responsibility Architecture
→ runtime actual-state / routing mechanics where applicable

Component Internal Design
→ component-local realization after authorization

Foundation / Contract / Provider authorities
→ reusable/stable cross-boundary semantics only if later admitted

Project Owner / MDE
→ if later design materially changes accepted Authority / SoT / Trust / major compatibility / stable identity / high-lock-in commitments
```

## 8. Offline / Private Deployment Consequence

Native multimodal capability must remain compatible with accepted private/offline correctness.

```text
Multimodal Agent
!= mandatory public Internet
!= mandatory vendor SaaS
!= mandatory Internet AI provider
```

Local/private models and locally available tool chains remain valid realization paths.

## 9. Compatibility / Failure Consequence

Later design must preserve explicit conditions such as:

```text
unsupported modality
unsupported provider/modality combination
unknown provider capability
incompatible Agent/provider combination
unavailable modality processing capability
indeterminate multimodal interpretation where applicable
```

No silent downgrade to text-only semantics is implied by this capability decision.

## 10. Preserved Invariants

This decision preserves:

- exactly five Product Components;
- AI Agent as a first-class / parallel / non-subordinate domain;
- `AI Agent Semantic Authority → ns_agent`;
- `AI Agent Canonical Definition SoT → ns_agent`;
- provider/model/tool non-authority;
- `ns_node` OCR/local execution/source-effect responsibility independence;
- Data/Knowledge factual SoT preservation;
- Tenant/IAM/Policy/Trust/Artifact/Admission governance;
- offline/private correctness;
- extension/re-delivery governance;
- no premature internal architecture, runtime architecture, Shared Foundation, Contract, Module, Provider or implementation design.

## 11. Revalidation Trigger

Revalidate if the Project Owner later changes one or more of:

- native multimodal Agent capability support;
- the rule that multimodal capability is part of the native Agent semantic domain rather than Tool-only mediation;
- AI Agent Semantic Authority or Canonical Definition SoT;
- provider-neutrality of native Agent semantics.

Changes in concrete media formats, model providers, codecs, storage, transport, schema, runtime processes or deployment topology do not by themselves revalidate this capability decision.

## 12. Bounded-session Authority Limit

This evidence records one Project Owner capability decision inside Z3 Batch 1.

It does not:

```text
constitute GAC Global Acceptance
advance GAC Epoch
authorize Z3 Batch 2
complete Z3 Batch 1
start normative Five-component Internal Architecture Boundary synthesis
start Component Internal Design
start Runtime Responsibility Architecture
start Shared Foundation Architecture
start Foundation Contract / Module / Provider Design
start Implementation Planning / IWP / coding
```
