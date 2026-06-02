# IAM Documentation (Three-Layer Model)

This directory is rebuilt as a three-layer documentation system.

- Master roadmap: `docs/iam_platform_roadmap.md`

## Layer 1: Foundation

Path: `docs/iam/l1-foundation/`

Goal:

- Define immutable architecture constraints.
- Define external API and permission contracts.
- Define canonical governance vocabulary.

Files:

- `architecture-and-constraints.md`
- `api-and-permission-contract.md`

## Layer 2: Capabilities

Path: `docs/iam/l2-capabilities/`

Goal:

- Describe IAM core capability design and behavior.
- Describe ACL, policy, data-scope, and decision-audit implementation contracts.

Files:

- `resource-acl-and-authorize.md`
- `policy-and-decision-audit.md`
- `data-scope-contract.md`

## Layer 3: Integration

Path: `docs/iam/l3-integration/`

Goal:

- Define how business applications integrate with IAM.
- Define acceptance checklists and baseline validation.

Files:

- `knowledge-and-agent-integration.md`
- `module-onboarding.md`
- `acceptance-checklist.md`
- `perf-baseline.md`
- `smoke-requests.http`

