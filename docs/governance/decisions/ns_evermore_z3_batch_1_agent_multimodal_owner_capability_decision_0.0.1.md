# NGRP-001 Phase Z3 / Batch 1 — Native Agent Multimodal Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should the native `ns_agent` semantic domain remain text-centric with non-text inputs mediated only through tools/extensions, or should Native Agent Definition / Context / Interaction semantics directly support multimodal content?

This is product-significant because it determines whether multimodality is a native Agent product semantic or merely an implementation/provider/tool convenience. A model provider's capabilities must not define the Agent architecture boundary by placement.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

Native multimodal semantics materially affect the Agent product boundary and experience, but do not move accepted Authority, SoT, Actual-state Ownership, Tenant, IAM, Policy, Trust, Artifact Acceptance or Execution Admission ownership.

## 3. Durable Mutually-exclusive Alternatives

### A — Text-centric Native Agent

Native Agent semantics remain text/structured-data oriented. Image/audio/video/media must first be processed by a Tool, `ns_node`, extension or external capability into text/structured facts before Agent consumption.

### B — Native Multimodal Agent Semantics

Native Agent semantics directly permit applicable multimodal content as Agent context/interaction content, including text, image, audio, video/media where later supported, document/media content and structured data. Individual providers may support only a subset.

### C — Multimodal only through Extension / Tool capability

The product supports multimodal Agent experiences, but non-text modalities remain represented only through Tool/Extension composition rather than as native Agent semantics.

## 4. Recommendation Presented

```text
Recommendation
→ B — Native Multimodal Agent Semantics
```

### Recommendation Rationale

AI Agent is a first-class domain and should not be permanently constrained by text-centric API/provider assumptions. Option B makes multimodality provider-neutral, preserves direct use of provider-native capabilities where compatible, and avoids forcing all non-text semantics through artificial Tool mediation while leaving `ns_node` OCR/local-execution authority intact.

## 5. Tradeoffs and Impact

**Benefits**
- supports native visual, voice, document and other applicable media Agent experiences;
- preserves provider-neutral Agent semantics across local/private/Internet model providers;
- avoids text-centric architectural lock-in and unnecessary Tool-only indirection.

**Costs**
- later compatibility/conformance must account for modality profiles and provider capability differences;
- privacy, data-size, context and lifecycle concerns become broader than text-only Agent operation.

**Risks / Complexity**
- unsupported provider/modality combinations and unknown capability states must remain explicit;
- fallback or conversion behavior can become ambiguous if later design does not distinguish native modality from mediated conversion;
- media storage/streaming/context handling introduces significant later design pressure without being selected here.

**Long-term Impact**
- `ns_agent` remains a provider-neutral multimodal Agent platform rather than a text-first platform with permanent mediation constraints;
- future provider evolution can add modality support without redefining Agent authority.

**Compatibility / Migration Impact**
- Agent/provider combinations require explicit supported/unsupported/unknown/incompatible semantics;
- no concrete modality representation, negotiation protocol or migration guarantee is selected here.

**Offline / Private Deployment Impact**
- multimodal Agent capability must remain compatible with local/private models and locally available tool chains;
- no mandatory public Internet, vendor SaaS or Internet AI provider is introduced.

**Cross-component Impact**
- `ns_agent` owns Agent semantics only;
- `ns_node` retains OCR/local resource/device/protected-effect responsibility;
- Data/Knowledge factual SoT remains unchanged;
- model/tool providers do not gain Agent Authority.

## 6. Project Owner Selected Result

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

## 7. Normative Capability Consequence

`ns_agent` must support Native Agent definitions/runtime semantics capable of applicable multimodal content. Provider support may be a subset and unsupported combinations must be explicit.

## 8. Authority / SoT / Actual-state Preservation

```text
Provider-native Multimodality != Provider becomes Agent Authority
Native Agent Multimodality != ns_agent gains OCR/local-device authority
Multimodal Context != Data/Knowledge SoT transfer
Runtime Actual-state Ownership != changed by modality
```

## 9. Explicit Non-implications

The decision does not require every provider to support every modality, does not select Internet models, does not transfer `ns_node` responsibility, and does not define media storage, transport, codecs, schema or streaming architecture.

## 10. Deferred Mechanics / Named Later Authority

Not decided here: image/media schema, audio/video codec, streaming model, file representation, media storage, multimodal message format, provider capability-negotiation protocol, context-window strategy, tokenization, conversion pipeline, transport, runtime topology or provider selection.

These remain for separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture where applicable, Component Internal Design and later Contract/Foundation/Provider work if admitted. MDE-class changes return to Project Owner.

## 11. Revalidation Trigger

Revalidate if the Project Owner removes native multimodal Agent support, makes multimodality Tool-only, changes Agent Authority/Definition SoT, or abandons provider-neutrality of Native Agent semantics.

## 12. Bounded-session Authority Limit

This evidence correction preserves the selected result and does not claim Global Acceptance, advance GAC state, authorize later batches or enter downstream architecture/design/implementation work.
