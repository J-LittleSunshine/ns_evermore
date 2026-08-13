# NGRP-001 Phase Z3 / Batch 1 — Node Attended and Unattended Execution Owner Capability Decision

- **Program / Phase:** `NGRP-001 Phase Z3 — Five-component Internal Architecture Boundaries / Batch 1`
- **Decision Authority:** `PROJECT_OWNER / PRODUCT_CAPABILITY_CHECKPOINT`
- **Capability Classification:** `OWNER_DECISION_REQUIRED`
- **Status:** `OWNER_CAPABILITY_DECIDED / PERSISTED`
- **Evidence Correction Scope:** `CAPABILITY_DECISION_EVIDENCE_CORRECTION_ONLY`
- **Selected Semantics:** `UNCHANGED`
- **Global Acceptance:** `NOT CLAIMED`

## 1. Material Capability Question

Should `ns_node` formally support only unattended/managed local execution, only bounded attended execution, or both attended and unattended execution as first-class native product capabilities?

This is product-significant because `ns_node` already owns applicable local execution, desktop/browser automation, package/plugin/tool/workflow execution, local resource/file/device interaction, offline/degraded continuity and local protected-effect/source-fact production. The capability baseline therefore must determine whether both managed background execution and legitimate current-user interactive execution are native product modes.

## 2. Classification and MDE Boundary

```text
Capability Classification
→ OWNER_DECISION_REQUIRED

MDE
→ NO
```

The choice materially affects the Node product execution boundary, but it does not move Tenant/IAM/Policy/Trust/Artifact Acceptance/Execution Admission Authority, Automation Semantic Authority, local protected-effect responsibility, broader SoT or Runtime Actual-state ownership. Concrete session/security/runtime architecture remains deferred.

## 3. Durable Mutually-exclusive Alternatives

### A — Unattended-only native Node execution

Formal native `ns_node` execution is centered on managed/background/unattended operation. Current-user interactive/attended desktop execution is not a first-class Native Node product capability.

### B — Attended + Unattended are both first-class native capabilities

`ns_node` natively supports both governed unattended local execution and governed attended local execution associated with a legitimate user/session context. Neither mode is treated as a special authority bypass.

### C — Attended-only / primarily attended bounded native execution

Native Node execution is centered on legitimate current-user interactive/attended sessions. General managed/unattended execution is not a first-class Native Node product capability.

These alternatives describe only the original product-capability choice; they do not select process, session or desktop technology.

## 4. Recommendation Presented

```text
Recommendation
→ B — Attended + Unattended are both first-class native capabilities
```

### Recommendation Rationale

The accepted product already has durable pressure from both sides: scheduled/event-driven/managed Automation requires unattended local execution, while user/Agent-assisted desktop/browser/local-resource work and governed HITL require attended execution. Option B covers both enterprise RPA-style background execution and interactive local assistance without forcing either mode to emulate the other or narrowing `ns_node` into only a worker or only a desktop assistant.

## 5. Tradeoffs and Impact

**Benefits**
- supports scheduled/event-driven/managed unattended Automation and current-user attended Automation under one Node product boundary;
- supports Agent/user-assisted desktop, browser, file/device and HITL scenarios where a legitimate interactive session is required;
- preserves one local-execution responsibility model across both operating modes.

**Costs**
- later architecture must account for principal/session binding, capability/readiness differences and recovery across two execution modes;
- operational diagnostics and scheduling/selection must eventually distinguish whether work requires or permits a particular execution mode.

**Risks / Complexity**
- attended execution can create user/session identity ambiguity if later design fails to bind principal/Tenant/session context explicitly;
- session loss, lock/logout and interactive availability create recovery/readiness complexity;
- unattended execution can be misinterpreted as unrestricted machine authority unless Policy/Admission boundaries remain explicit;
- supporting both modes creates more lifecycle complexity than either single-mode alternative.

**Long-term Impact**
- `ns_node` remains a general enterprise local execution runtime supporting both background automation and interactive local assistance;
- the product is not permanently narrowed to an unattended worker or an attended desktop assistant.

**Compatibility / Migration Impact**
- later package/capability/runtime design may need to represent whether a particular executable capability supports/requires attended, unattended or both modes;
- exact capability declaration, session compatibility and migration representation are deferred and not established here.

**Offline / Private Deployment Impact**
- both modes must remain compatible with private/offline requirements where the underlying scenario is supported;
- neither mode may require mandatory public SaaS, public registry, public control plane or online-only licensing for core correctness;
- offline/local presence does not create authority escalation.

**Cross-component Impact**
- Automation/Agent may request applicable governed work, but `ns_node` remains executor rather than Automation/Agent Authority;
- `ns_runtime` may later coordinate applicable scheduling/dispatch without becoming local-effect or Automation authority;
- `ns_web` may later participate in human-facing attended/HITL interaction without becoming execution/admission authority;
- `ns_server` Tenant/IAM/Policy/Trust/Artifact/Admission authorities remain unchanged.

## 6. Project Owner Selected Result

```text
Selected Option
→ B

ns_node Attended Execution
→ FIRST_CLASS_REQUIRED

ns_node Unattended Execution
→ FIRST_CLASS_REQUIRED

Combined Product Capability
→ ATTENDED_AND_UNATTENDED_LOCAL_EXECUTION_REQUIRED
```

## 7. Normative Capability Consequence

```text
ns_node
→ MUST support applicable governed unattended local execution
→ MUST support applicable governed attended local execution associated with a legitimate user/session context
→ MUST preserve local execution and protected-effect/source-fact responsibility in both modes
```

Representative capability pressure remains:

```text
scheduled / event-driven / otherwise governed Automation
→ unattended execution where applicable

user / Agent initiated governed Automation
→ attended local execution where applicable

human interaction during execution
→ may participate in accepted governed HITL capability
```

These examples do not define concrete runtime routing or topology.

## 8. Authority / SoT / Actual-state Preservation

```text
Attended Execution != IAM / Policy bypass
Current User Presence != Execution Admission bypass
Unattended Execution != unrestricted machine authority
Current Desktop Session != Tenant / Principal ambiguity allowed
ns_node Execution != Automation Semantic Authority
ns_node Local Possession != Artifact Acceptance Authority
ns_node Local Execution != Execution Admission Authority
Local Source/Effect Fact != broader canonical SoT automatically
```

Runtime Actual-state ownership remains governed by the accepted bounded semantic partition model.

## 9. Explicit Non-implications

The selected result does not choose a Windows/Linux session model, does not imply RDP/VDI/service-account semantics, does not define session isolation, does not grant the current user or background worker special authority, and does not make attended presence or unattended execution evidence equivalent to Artifact Acceptance/Admission/Policy permission.

## 10. Deferred Mechanics / Named Later Authority

Not decided here: Windows/Linux session model, RDP/VDI behavior, service-account model, user-session attachment, session isolation, process/worker topology, browser profiles, interactive desktop acquisition, concurrency, lock-screen/logout behavior, session-loss recovery, credential handling, transport/protocol, runtime routing, container/VM/host topology.

These remain for separately authorized Five-component Internal Architecture Boundary work, Runtime Responsibility Architecture and Component Internal Design. Stable cross-boundary contracts or reusable Foundation concerns may be addressed only in their later authorized phases. Material Authority/SoT/Trust/Admission/protected-effect ownership changes return to Project Owner/MDE governance.

## 11. Revalidation Trigger

Revalidate if the Project Owner changes whether attended or unattended execution is a first-class `ns_node` capability, or if a later proposal materially moves accepted Authority, SoT, Trust, Admission or protected-effect ownership.

## 12. Bounded-session Authority Limit

This evidence correction restores the durable mapping `Selected Option B → ATTENDED_AND_UNATTENDED_LOCAL_EXECUTION_REQUIRED` without reopening the choice. It does not claim Global Acceptance, advance GAC state, authorize later Z3 batches, or enter Component Internal Design, Runtime Responsibility Architecture, Shared Foundation/Contract/Module/Provider design, Implementation Planning, IWP or coding.
