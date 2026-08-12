# ns_evermore Historical Current Required Read Set

- **Version:** `0.0.1`
- **Status:** `SUPERSEDED AS ACTIVE MECHANISM / HISTORICAL_CONTINUITY_EVIDENCE`
- **Branch:** `architecture/ns-evermore-genesis-0.0.1`

This file records the former standalone Current Required Read Set mechanism used through `GAC-EPOCH-0006`.

Effective with the governance consolidation after `GAC-EPOCH-0006`:

```text
Current Required Read Set
→ embedded directly in Global Architecture State

Standalone CRRS document
→ no longer required
```

Reason:

- reduce governance-document fragmentation;
- keep current authorization and current read requirements in one current-truth document;
- preserve the root requirement that every fresh session can recover minimum sufficient context without semantic loss.

Historical versions and Git commits remain continuity evidence.

Current sessions MUST read the `Current Required Read Set` section of:

```text
docs/governance/global_architecture/ns_evermore_global_architecture_state_0.0.1.md
```

The unified current governance rules are in:

```text
docs/governance/ns_evermore_governance_0.0.2.md
```
