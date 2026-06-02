# IAM Platform Acceptance Matrix (P3)

## 1. Unified Authorization Model

- [ ] Subject / Resource / Action / Effect model works end-to-end.
- [ ] `deny > allow` is consistent across ACL, Policy, RBAC.

## 2. Data Scope Contract

- [ ] IAM returns standardized `normalized_scope`.
- [ ] Business side consumes IAM filter output instead of local assumptions.

## 3. Knowledge Chain

- [ ] Candidate filtering happens before retriever recall.
- [ ] Unauthorized chunk never enters retrieval context.

## 4. Agent Tool Chain

- [ ] Every tool call passes through IAM guard.
- [ ] Unauthorized tool calls are blocked and auditable.

## 5. Decision Traceability

- [ ] Decision logs can be queried by subject/resource/action.
- [ ] Failed decision can be traced to policy rule level.

## 6. Module Onboarding

- [ ] New module onboarding requires only resource/action registration + policy config.
- [ ] IAM core main flow remains unchanged.

