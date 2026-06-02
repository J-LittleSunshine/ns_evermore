# L1 Foundation: Architecture and Constraints

## 1. Platform Goal

IAM is the unified authorization center for cross-domain applications.

Target domains include:

- Knowledge
- Agent
- Workflow
- CRM
- Contract
- Project
- ERP

## 2. Unified Authorization Model

Fixed model:

- Subject + Resource + Action + Effect

Subject types:

- USER
- ROLE
- DEPARTMENT
- ORGANIZATION
- SUBSIDIARY

Effect values:

- allow
- deny

Global conflict rule:

- deny > allow

## 3. Immutable Capability Constraints

The following constraints must not be changed by business modules:

1. Authorization order must keep deny-first semantics.
2. IAM core flow should remain module-agnostic.
3. New module integration should not require IAM core code rewrite.
4. Decision audit records must be queryable from IAM APIs.

## 4. Data Scope Canonical Vocabulary

Canonical values:

- SELF
- DEPARTMENT
- DEPARTMENT_AND_CHILDREN
- ORGANIZATION
- ALL

Compatibility aliases:

- DEPARTMENT_TREE -> DEPARTMENT_AND_CHILDREN
- COMPANY -> ORGANIZATION

## 5. Integration Hard Requirements

- Knowledge: authorization filtering happens before retriever recall.
- Agent: every tool execution checks IAM before execution.
- Business queries must consume IAM `filters` when returned.

## 6. Implementation Boundary

Current project boundary:

- IAM models are `managed=False`.
- Schema changes are maintained in `sql/create/iam/*.sql` and `src/ns_backend/iam/models.py` only.
- Upgrade scripts are not maintained in current phase.

