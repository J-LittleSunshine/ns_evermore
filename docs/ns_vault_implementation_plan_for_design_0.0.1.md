# ns_vault 分阶段实施计划

## 文档职责

本文档是 ns_vault 当前执行游标。

状态仅允许：

- NOT_STARTED
- BLOCKED
- IN_PROGRESS
- IMPLEMENTED
- VERIFIED
- PRODUCTION_READY

未经真实验收不得提升状态。

## 阶段模型

### Foundation Layer

状态：NOT_STARTED

目标：建立公共合同、身份、授权、存储、审计和 Authority 基础。

工作包：

- vault contract
- identity federation
- policy artifact
- authority storage
- audit chain

安全门禁：禁止绕过 IAM、Policy 和 Audit。

---

### Core Security Layer

状态：NOT_STARTED

目标：实现 Key、Secret、Envelope Encryption、Lifecycle、Provider。

---

### Platform Integration Layer

状态：NOT_STARTED

目标：接入：

- ns_backend
- ns_runtime
- ns_node
- ns_client
- Agent

约束：复用现有公共设施。

---

### Advanced Security Layer

状态：NOT_STARTED

目标：

- PKI
- Dynamic Credential
- Advanced Transit
- HYOK
- External Customer

---

### Production Assurance Layer

状态：NOT_STARTED

目标：

- HA
- Disaster Recovery
- Performance
- Security Testing
- Production Gate

## 实施原则

- 设计边界不得因为实施阶段改变。
- 优先复用 ns_common、ns_backend IAM、ns_runtime Authority 能力。
- 不重复建设 IAM、配置、审计基础设施。
- 不在 backend 保存 Secret 明文。
- 不直接访问 Vault Authority Database。

## 初始状态

所有代码工作包均未开始。
