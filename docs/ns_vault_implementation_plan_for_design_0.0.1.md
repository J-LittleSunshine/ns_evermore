# ns_vault 分阶段实施计划

> 实施文档版本：`0.0.1`
>
> 设计基线：[ns_vault_design_checklist_0.0.1.md](ns_vault_design_checklist_0.0.1.md)
>
> 长期架构决策：[ns_vault_architecture_decisions_0.0.1.md](ns_vault_architecture_decisions_0.0.1.md)
>
> 历史验收证据：[ns_vault_acceptance_log_0.0.1.md](ns_vault_acceptance_log_0.0.1.md)
>
> 当前状态校准时间：`2026-07-31T14:12:00+08:00`
>
> 当前实施结论：`ns_vault` 生产实现尚未开始；设计治理基线已形成，当前唯一执行游标为 `P00-W05`，并在获得明确实施授权与本地工作区基线后方可继续。

本文档是 `ns_vault` 的唯一当前实施状态、阶段计划和执行游标。它只拆解已经冻结的最终设计，不得用阶段成本、现有代码、临时环境或局部实现反向缩小设计清单和 ADR。

文档分工：

- 最终产品、安全和功能边界由设计清单维护。
- 长期架构取舍由 ADR 维护。
- 当前状态、阻塞项、工作包顺序和下一执行入口只由本实施计划维护。
- 已发生的命令、测试、修改、评审和验收事实只追加到 acceptance log。

---

## 0. 文档执行规则

### 0.1 权威顺序

实施和审查发生冲突时，规范性权威按以下顺序裁决：

1. `ns_vault_design_checklist_0.0.1.md`。
2. `ns_vault_architecture_decisions_0.0.1.md` 中状态为 `ACCEPTED` 的长期决策。
3. 本实施计划中的当前阶段状态、阻塞项、工作包出口和唯一执行游标。
4. 当前单次任务说明；任务只能在前三项允许的范围内授权具体操作。
5. `ns_vault_acceptance_log_0.0.1.md` 中的历史证据。

本地工作区中的代码、配置、测试和依赖锁定文件是**实现事实源**，不是能够静默覆盖设计、ADR 或本计划状态的规范性权威。若本地事实与本计划不一致，必须停止当前工作、先把真实差异写入 acceptance log 并重新校准本计划，再移动执行游标；不得让代码现状自行改写阶段状态或长期边界。

远程仓库、PR、Issue、旧分支、历史会话、旧草案和 acceptance log 不能单独证明当前本地实现状态。开始任何实现回合前，必须重新校准本地分支、HEAD、工作树、依赖、测试和已有实现。

### 0.2 状态定义

| 状态 | 含义 |
|---|---|
| `NOT_STARTED` | 工作包尚未开始，未形成可验收实现 |
| `IN_PROGRESS` | 已开始但尚未满足阶段出口 |
| `BLOCKED` | 受前置阶段、授权、环境、外部 Provider 或未决实施输入阻塞 |
| `IMPLEMENTED` | 代码或文档已完成，但尚未获得对应层级的完整验证证据 |
| `VERIFIED` | 已获得计划要求的本地或指定环境验证证据 |
| `PRODUCTION_READY` | 已通过对应保障等级的生产门禁、故障演练和发布检查 |
| `DEFERRED` | 设计中存在，但当前执行游标明确延期；不得被解释为取消 |
| `SUPERSEDED` | 工作包已被后续工作包显式替代，保留追溯 |

### 0.3 完成度等级

| 等级 | 含义 | 最低证据 |
|---|---|---|
| `F0` | 未实现 | 仅有设计、ADR 或任务描述，不得声称可用 |
| `F1` | 合同和治理就绪 | 类型、合同、边界、负向规则、实施入口或文档完成；没有生产能力声明 |
| `F2` | 单进程实现就绪 | 单元、合同、状态机和安全负向测试通过；外部真实依赖或故障恢复仍可未验证 |
| `F3` | 集成与故障验证就绪 | 真实存储/Provider、并发、重启、故障注入和跨组件集成达到阶段要求 |
| `F4` | 作用域内生产保障就绪 | 对该工作包或阶段作用域所需的 HA/DR、性能、安全、运维、发布或门禁证据已经真实完成；全产品只有在 P21/P22 总门禁通过后才能标记 `PRODUCTION_READY` |

`IMPLEMENTED`、`VERIFIED` 与 `F*` 必须同时记录。例如 `IMPLEMENTED / F2` 表示代码已完成且达到 F2 设计深度，但尚缺 F2 所要求的完整验证时，状态仍应保持 `IMPLEMENTED` 而不是 `VERIFIED`。

P21/P22 及其他按 assurance lane 重复执行的阶段必须在状态中写明作用域，例如 `VERIFIED / F4 (Level 1 scope; Level 2/3 BLOCKED)`；不得用某一等级或某一资源集的通过结果覆盖更高等级、其他 Provider 或尚未启用能力的状态。

### 0.4 实施纪律

- 未经用户明确授权，不修改生产代码、配置、依赖、Migration、测试、分支或远程仓库。
- 每次实现只处理当前游标指向的工作包；不得因为相邻工作包方便而扩大修改范围。
- 阶段默认按 `P00 → P22` 的编号顺序推进，并严格对应 `Foundation → Core Security → Platform Integration → Advanced Security → Production Assurance`；“前置阶段”是最低依赖集合，不是跳过中间阶段或跨越实施层的授权。只有本计划显式调整当前游标并记录理由时，才允许同一实施层内并行或经安全审查的跨层提前。
- 分级生产门禁按 **assurance lane** 独立推进：Level 1、Level 2、Level 3 只要求各自启用资源和 Provider 所需的工作包达到对应门禁；不属于较低等级范围的高级能力可以在完成合同、稳定错误、fail-closed Feature Gate 和重新进入条件后显式标记 `DEFERRED`，但不得从最终设计删除，也不得使对应更高等级门禁变为可用。
- `DEFERRED` 不能用于跳过 Root/Seal、身份、授权、Strong Audit、安全时间、SingleWriter Authority、租户隔离、删除/销毁或目标等级自身需要的 HA/DR 等公共安全不变量；每个延期项必须记录 capability disabled 状态、阻塞原因、重入条件和被阻塞的生产等级。
- P21/P22 是 Production Assurance 内的分级门禁与发布通道。某一 Level Gate 达到 `VERIFIED / F4` 后，可执行该等级对应的 P22 发布工作包；更高等级仍可保持 `BLOCKED` 或 `DEFERRED`，但其 Action、Resource Class、Provider 和对外声明必须继续 disabled。
- 同一阶段内的工作包默认按编号顺序执行；只有本计划显式标记为可并行、按 assurance lane 独立执行或因未启用能力而 `DEFERRED` 时才能偏离。当前游标始终指向当前选定 assurance lane 中第一个尚未完成且前置条件成立的工作包。
- 每个工作包必须显式记录状态和 F 等级；没有状态行的任务不得被视为可执行、已开始或已完成。
- `F4` 按工作包/阶段作用域解释，不等于整个 Vault 已可生产；`PRODUCTION_READY` 只能由 P21 的对应保障等级门禁和 P22 发布门禁共同授予。
- 所有工作包开始前必须读取设计清单、相关 ADR、本计划当前状态和 acceptance log 最新记录。
- 工作包完成后，先追加 acceptance log 的真实证据，再更新本计划状态和下一游标。
- 未执行的测试不得写成通过；没有真实 Provider、HSM、KMS、HYOK、跨区域或生产根材料时，必须明确标记 `UNVERIFIED`。
- 设计中的最终能力可以分阶段实现，但禁止临时旁路进入生产，例如 backend 代理 Secret 明文、环境变量根密钥回退、普通 API 进程持有 KEK、内部接口免鉴权、双写 Authority 或 best-effort 强审计。
- 未实现 Action 必须返回稳定的未支持或 feature-disabled 错误，不能返回空成功、模拟成功或弱化安全语义。
- 任何会写外部 Provider 的工作必须先建立可恢复的 operation record，再执行外部副作用。
- 任何安全状态写入必须与本地强审计意图建立不可分割或可恢复关联。

### 0.5 工作包完成记录

每个工作包完成时，acceptance log 至少记录：

- 工作包编号和目标；
- 起始本地分支、HEAD、工作树状态；
- 修改文件和公共契约变化；
- 实际执行的测试命令、结果和环境；
- 安全负向测试和敏感信息扫描；
- 未验证项、外部依赖和已知限制；
- 是否提交、推送或创建 PR；
- 本计划更新后的状态与下一执行游标。

---

## 1. 当前实施状态快照

### 1.1 当前结论

- 设计清单和长期 ADR 已完成并经过双向一致性检查。
- 设计清单固定 `src/ns_vault` 为独立 FastAPI/ASGI 安全服务，`src/ns_backend/vault` 为 Django 控制面应用。
- 当前没有已确认需要迁移的既有生产 Secret、Key 或凭证资产；未来发现真实资产时再启用迁移工作包。
- 本设计会话没有修改生产代码、配置、依赖、Migration 或测试，也没有创建分支、提交、推送或 PR。
- 当前没有任何 `ns_vault` 功能可以被标记为 `IMPLEMENTED`、`VERIFIED` 或 `PRODUCTION_READY`。
- 当前整体实现状态：`NOT_STARTED / F0`。
- 当前治理文档状态：`VERIFIED / F1 (document-only)`。

### 1.2 当前唯一执行游标

```text
P00-W05：本地工作区实现事实盘点与基线校准
状态：BLOCKED / F0
阻塞原因：尚未获得开始实现的明确授权；开始时必须读取用户本地工作区，不能以远程仓库或本设计会话替代。
```

### 1.3 当前禁止推断

- 不得推断 `src/ns_vault` 已存在或已可启动。
- 不得推断 FastAPI、Pydantic、数据库驱动、Migration 工具或密码学库已经加入依赖。
- 不得推断 `src/ns_backend/vault` 已实现控制面模型、命令、投影、审批或计量。
- 不得推断任何 Vault 数据库、Event Store、State Store、Object Storage、HSM、KMS、HYOK、CA、审计锚点或可信时间源已经配置。
- 不得推断现有 `ns_common` 能力已满足 Vault 的全部安全要求；复用前必须逐项做差距分析和合同测试。
- 不得推断现有 `ns_runtime` Authority Broker/Attestor 实现可以被直接复制到 Vault；只能复用经过抽象和评审的公共原语或设计模式。

---

## 2. 全局架构与安全不变量

以下不变量对所有阶段持续生效：

| 编号 | 不变量 | 阶段验证方向 |
|---|---|---|
| `INV-001` | `ns_backend` 是控制面，不是 Vault 数据面最终授权权威 | backend 失陷与伪造命令负向测试 |
| `INV-002` | Secret 明文不得经过普通 backend、Projection、日志、异常、指标或审计 | 全链路敏感数据扫描 |
| `INV-003` | 普通 API、Command、Scheduler、Audit、Provider Host 进程不得持有 Root Key 或 Tenant KEK 明文 | 依赖图、进程边界和内存接口审查 |
| `INV-004` | Tenant Key Domain 是密码学隔离与 Shard 归属边界 | 跨租户替换、解包和路由负向测试 |
| `INV-005` | Vault 资源授权默认拒绝，Grant、Guardrail、Deny、状态和版本必须同时成立 | Policy 解释与决策证明测试 |
| `INV-006` | SSO、IAM、OIDC、SPIFFE 等只提供身份事实，不直接产生 Vault Resource Permission | claim/role/group 越权测试 |
| `INV-007` | 数据面 Capability 只能由 Vault Authorization Authority 签发 | backend/Broker/Agent 伪造测试 |
| `INV-008` | Command、Actual State、Receipt、Security Event 和 Projection 语义分离 | 状态漂移与事件丢失恢复测试 |
| `INV-009` | Provider capability declaration 是硬上限，策略只能收紧 | Manifest 与运行能力不一致测试 |
| `INV-010` | Provider 外部副作用先持久化 PREPARE，再执行并对账 | 崩溃、超时、重复提交测试 |
| `INV-011` | 每个 Key Resource 的算法、用途、来源、导出策略和保障要求创建后不可放宽 | 变更请求负向测试 |
| `INV-012` | 每个 Key 最多一个 Primary Version；历史版本不能产生新业务输出 | 并发轮换和版本降级测试 |
| `INV-013` | 每个 Secret 最多一个 Current Version；Version 内容不可原地修改 | 并发激活、回滚和旧能力测试 |
| `INV-014` | 每个 Secret Version 独立 DEK，DEK 由 Tenant KEK generation 包装 | Envelope/AAD/rewrap 测试 |
| `INV-015` | DEK 缓存只存在于授权 Authority 边界，不能缓存授权决策 | Cache epoch、禁用和销毁测试 |
| `INV-016` | Agent、SDK、runtime、node 不得成为隐藏 Authority | 本地接口和委派越权测试 |
| `INV-017` | `ns_node` 只能代表自身 Node Principal 访问 node-scoped Secret | workload 代理与 host 扩权负向测试 |
| `INV-018` | Lease 的创建、续期、撤销、到期和清理由 Shard Leader 权威写入 | 并发续期、级联撤销与 Provider 对账测试 |
| `INV-019` | 证书身份由 Vault 独立裁决，CSR 不能自行声明未授权身份 | SAN、Subject、EKU 和租户越权测试 |
| `INV-020` | Strong Audit 不能被管理员、审批或 Break-glass 关闭或删除 | 审计旁路、回滚和截断测试 |
| `INV-021` | 安全 TTL 不得因 wall clock 回退、快照恢复或切主重新延长 | 单调时间与 TIME_UNTRUSTED 测试 |
| `INV-022` | 每个 Key Domain 任一时刻只有一个有效写 Authority 和一个 Home Region | split-brain、epoch、fencing 测试 |
| `INV-023` | 数据库恢复不等于安全状态恢复，Provider、Lease、CA 和审计必须重新验证 | DR 分级恢复演练 |
| `INV-024` | 已完成密码学销毁的能力不能由旧备份、旧 Provider session 或旧 Capability 恢复 | anti-rollback 恢复测试 |
| `INV-025` | 内部和外部接口共享 Canonical Contract、安全语义、稳定错误和审计规则 | REST/gRPC/IPC conformance |
| `INV-026` | ResourceRef/SecretRef 是定位符，不是 bearer credential | 引用泄露与重放负向测试 |
| `INV-027` | Software Provider 可以生产使用，但不能声明硬件或外部控制保障 | assurance 与生产门禁测试 |
| `INV-028` | 未完成相应 F 级别的能力不得进入更高生产保障等级 | 生产启用门禁检查 |
| `INV-029` | 公共设施复用不得把 Vault 权威状态放入普通 cache、backend ORM 或 runtime 私有状态 | 依赖和存储访问扫描 |
| `INV-030` | 无法确认安全状态时默认拒绝，不得使用隐藏 fallback Secret/Key/Provider | 故障和降级路径测试 |

---

## 3. 公共设施复用登记表

“现有能力”只表示仓库中存在可复用基础，不表示已经适配 Vault。每项必须通过 Vault-specific 差距分析、负向测试和生命周期验证后才能将“Vault 采用状态”提升。

| 编号 | 现有公共能力 | 预期复用边界 | 现有事实 | Vault 采用状态 | 目标阶段 |
|---|---|---|---|---|---|
| `COM-001` | `ns_common.config` | 配置组、不可变快照、来源、校验和敏感引用 | 已在仓库中存在并完成只读预检 | `NOT_STARTED` | P01/P02 |
| `COM-002` | `ns_common.exceptions` | 稳定错误注册、错误分类与传输映射基础 | 已存在 | `NOT_STARTED` | P01 |
| `COM-003` | `ns_common.security` / Sanitizer | 日志、异常、审计、URL、Token 和密钥字段脱敏 | 已存在 | `NOT_STARTED` | P01/P04/P17 |
| `COM-004` | `AesGcmSecretBox` | 仅作为受限小型内存秘密原语参考；不能直接充当 Vault 存储/IAM | 已存在且边界有限 | `NOT_STARTED` | P04/P08 |
| `COM-005` | `ns_common.http_client` | Provider、IdP、backend、可信时间源和外部锚点的受控 HTTP 生命周期 | 已存在 | `NOT_STARTED` | P02/P04/P17 |
| `COM-006` | `Clock` / UTC / monotonic | 双轨时间和可控测试时钟基础 | 已存在 | `NOT_STARTED` | P01/P04/P17 |
| `COM-007` | Typed ID / identifier 原语 | Vault 不透明稳定 ID 与 ResourceRef 类型基础 | 已存在 | `NOT_STARTED` | P01/P05 |
| `COM-008` | `ns_common.state_store` | Shard coordination、epoch、fencing 与临时协调的候选原语 | 已存在；不得直接假设满足 Vault | `NOT_STARTED` | P03/P18 |
| `COM-009` | logging / observability 基础 | 安全指标、trace、诊断和 backpressure 接口 | 已存在或可扩展 | `NOT_STARTED` | P17 |
| `COM-010` | `ns_common.testing` 与现有测试约定 | 临时资源、可控时钟、契约和故障测试 | 已存在或可扩展 | `NOT_STARTED` | P00/P01 起持续 |
| `COM-011` | `ns_backend.iam` | 人员、组织、角色、资源、ACL、Policy 等身份事实与管理能力 | 已存在；当前不是 Vault 最终授权权威 | `NOT_STARTED` | P05/P10 |
| `COM-012` | `ns_backend` app loader、DB router、ASGI | `src/ns_backend/vault` Django 控制面接入 | 已存在基础框架 | `NOT_STARTED` | P10 |
| `COM-013` | `ns_runtime` Authority Broker/Attestor 模式 | 根能力隔离、显式 Composition Root、FD/IPC、epoch/fencing 设计参考 | 已存在生产设计事实；禁止直接复制私有协议 | `NOT_STARTED` | P02/P04/P12 |
| `COM-014` | `ns_common.async_runtime` / 生命周期原语 | 标准 asyncio、任务监督、有界关闭、资源 owner 与可控测试生命周期 | 可访问远程仓库可见 `src/ns_common/async_runtime.py`；当前本地工作区仍待 P00-W05 验证，且必须重新评估 Vault 多进程与 Authority 适配 | `NOT_STARTED` | P01/P02/P04 |

复用判定规则：

- 通用能力可进入或扩展 `ns_common`，但 Vault 私有资源、Policy Artifact、Capability、Lease、Provider 协议、审计链和 Shard 状态不得放入公共层。
- `ns_backend.iam` 可以提供身份事实、组织关系和 issuer 管理输入，但 Vault Principal Binding 和资源授权仍属于 `ns_vault`。
- `ns_common.state_store` 若无法满足 Vault 的 fencing、revision、故障和 security epoch 语义，应通过兼容扩展或 Vault 私有适配层解决，不能静默弱化不变量。
- 任何公共设施扩展必须确认不会破坏 `ns_runtime`、`ns_node`、`ns_client` 或其他既有使用方。

---

## 4. 测试分层与证据要求

| 层级 | 内容 | 最早阶段 |
|---|---|---|
| `T1 Unit` | 纯类型、校验、序列化、算法选择、状态转换、错误映射 | P01 |
| `T2 Contract` | Canonical Contract、Provider SPI、IdP、Storage、Audit、backend 投影接口 | P01 |
| `T3 State Machine` | Key、Secret、Lease、Certificate、Command、Provider Operation、Deletion | P03 |
| `T4 Integration` | FastAPI、Django、关系库、Event Store、State Store、Object Storage、Provider Host | P02 起 |
| `T5 Concurrency` | 并发 command、activate/promote、renew、revoke、pool allocation、leader switch | P03 起 |
| `T6 Fault Injection` | 进程崩溃、IPC、网络、DB、Provider、Audit Sink、Time Source、Region 故障 | P04 起 |
| `T7 Security` | 越权、重放、跨租户、claim 伪造、nonce、schema、secret leakage、audit tamper | 每阶段 |
| `T8 Recovery` | 重启、备份恢复、anti-rollback、Provider reconciliation、DR 接管 | P03/P19 |
| `T9 Performance` | QPS、P95/P99、资源规模、审计吞吐、Provider rate limit、backlog | P20 |
| `T10 Production Gate` | 保障等级、HSM/HYOK、双人控制、HA/DR、安全审查和运维演练 | P21 |

通用出口规则：

- 单元测试不能替代真实 Provider、真实数据库或多进程故障证据。
- 测试 Provider、测试 root 和内存存储不能被记录为 production-equivalent。
- 所有成功和失败测试输出都必须经过敏感信息检查；不得把 Secret、Key、credential、token、private key、完整 CSR、完整 certificate payload 或 Provider 原始错误写入日志。
- 任何远程 CI 结果只覆盖对应 commit；不得继承其他 commit、旧分支或旧 workflow 的绿色状态。

---

## 5. 实施层、阶段总览与当前状态

实施层顺序固定为：

```text
Foundation Layer
  → Core Security Layer
  → Platform Integration Layer
  → Advanced Security Layer
  → Production Assurance Layer
```

阶段编号与实施层严格对齐；后续不得仅因某个高级功能易于实现而跨越尚未完成的前置实施层。

| 阶段 | 实施层 | 名称 | 当前状态 | 目标完成度 | 前置阶段 |
|---|---|---|---|---|---|
| `P00` | Foundation | 治理基线与本地事实校准 | `BLOCKED / F1` | F1 | 无 |
| `P01` | Foundation | Canonical Contract、Schema Registry 与公共原语 | `BLOCKED / F0` | F2 | P00 |
| `P02` | Foundation | FastAPI 服务骨架、Composition Root 与多协议安全进程 bootstrap | `BLOCKED / F0` | F2 | P01 |
| `P03` | Foundation | 分层存储、Migration、Command/Event/Outbox 与 SingleWriter Authority 底座 | `BLOCKED / F0` | F3 | P01/P02 |
| `P04` | Foundation | Root/Seal Authority、Provider Host、本地 Strong Audit 与安全时间底座 | `BLOCKED / F0` | F3 | P02/P03 |
| `P05` | Foundation | SaaS 引用、Vault 资源层级、Principal 与身份联邦 | `BLOCKED / F0` | F3 | P01/P03/P04 |
| `P06` | Foundation | Guardrail、Grant、Policy Artifact、Approval 与 Capability | `BLOCKED / F0` | F3 | P04/P05 |
| `P07` | Core Security | Key Management、BYOK/HYOK 合同与版本生命周期 | `BLOCKED / F0` | F3 | P04/P05/P06 |
| `P08` | Core Security | Secret Management、Envelope Encryption 与静态轮换 | `BLOCKED / F0` | F3 | P07 |
| `P09` | Core Security | Lease Authority 与调度引擎 | `BLOCKED / F0` | F3 | P03/P04/P05/P06 |
| `P10` | Platform Integration | Django 控制面、命令、投影与 reconciliation | `BLOCKED / F0` | F3 | P03/P05/P06/P07/P08/P09 |
| `P11` | Platform Integration | Vault Delivery Agent、本地交付与 ns_client SDK | `BLOCKED / F0` | F3 | P06/P08/P09 |
| `P12` | Platform Integration | ns_backend、ns_runtime、ns_node、ns_frontend 与 SSO 兼容集成 | `BLOCKED / F0` | F3 | P10/P11 |
| `P13` | Advanced Security | Transit、Derivation、Random/Password 与 Tokenization | `BLOCKED / F0` | F3 | P07/P12 |
| `P14` | Advanced Security | PKI、Certificate Role、CRL/OCSP 与 SSH CA | `BLOCKED / F0` | F3 | P07/P09/P12 |
| `P15` | Advanced Security | Dynamic Credential 与 Provider issuance mode | `BLOCKED / F0` | F3 | P04/P09/P12 |
| `P16` | Advanced Security | HSM/KMS/HYOK、配额、计量、Customer Account 与外部服务治理 | `BLOCKED / F0` | F3 | P10-P15 |
| `P17` | Production Assurance | Strong Audit 外部锚定、可信时间证明、可观测性与安全告警 | `BLOCKED / F0` | F3 | P03/P04/P06；当前 assurance lane 启用 backend 外部通知或客户证明时追加 P10/P16 |
| `P18` | Production Assurance | Shard 单写、Authority Worker、epoch/fencing 与区域内 HA | `BLOCKED / F0` | F3 | P03/P04/P06/P17 |
| `P19` | Production Assurance | 备份、anti-rollback、多区域热备与分级灾备 | `BLOCKED / F0` | F4 | P08/P09/P18；当前 assurance lane 启用 Transit、PKI、Dynamic Credential、HSM/KMS/HYOK 时追加 P13/P14/P15/P16 |
| `P20` | Production Assurance | 容量模型、Benchmark 与性能验收 | `BLOCKED / F0` | F4 | P07-P12/P17-P19；当前 assurance lane 启用高级能力时追加 P13-P16 |
| `P21` | Production Assurance | 安全强化与分级生产门禁 | `BLOCKED / F0` | F4 | P17-P20 的共享保障底座，以及目标 Level 明确列出的资源/Provider 工作包 |
| `P22` | Production Assurance | 发布、运维交接与持续兼容治理 | `BLOCKED / F0` | F4 | P21 中至少一个明确目标 Level Gate 已达到 VERIFIED / F4；发布更高等级时必须等待对应 Gate |

---

## P00 治理基线与本地事实校准

**阶段状态：`BLOCKED / F1`**

**目标完成度：`F1`**

**前置阶段：无**

### 目标

建立四份治理文档、本地工作区事实账本、初始测试基线和唯一执行游标；本阶段不实现任何 Vault 产品功能。

### 工作包

#### P00-W01 设计清单基线

状态：`VERIFIED / F1 (document-only)`。确认最终产品、安全、功能、非目标和组件兼容边界已经形成。

#### P00-W02 长期 ADR 基线

状态：`VERIFIED / F1 (document-only)`。确认 `ADR-001`—`ADR-069` 连续、均为 `ACCEPTED`，且与设计清单双向一致。

#### P00-W03 实施计划基线

状态：`VERIFIED / F1 (document-only)`。建立阶段、工作包、依赖、门禁、状态和当前游标。

#### P00-W04 Acceptance Log 基线

状态：`VERIFIED / F1 (document-only)`。只记录已经发生的设计、预检和文档事实。

#### P00-W05 本地工作区实现事实盘点与基线校准

状态：`BLOCKED / F0`。获得明确实现授权后，记录本地分支、HEAD、工作树、已存在的 `src/ns_vault`/`src/ns_backend/vault` 内容、依赖和测试事实；远程仓库不能替代。

#### P00-W06 初始测试与 CI 基线

状态：`BLOCKED / F0`。等待 P00-W05 完成后，执行不修改代码的现有测试、requirements/documentation gate、compile 和 diff 检查，并记录真实结果。

### 持续冻结边界

- 不得把设计文档存在解释为实现存在。
- 不得在本阶段新增依赖、Migration 或服务骨架。
- 若本地工作区与本计划假设不一致，先更新本计划，不得直接实施。

### 阶段出口

- 四份文档均位于用户本地工作区并可相互链接。
- 本地分支、HEAD、工作树、依赖、测试和现有代码已重新校准。
- P01 的明确实现授权、范围和起始基线已记录。

### 回滚与停止条件

- 发现设计清单与 ADR 冲突时停止实施并先修正文档。
- 发现本地已有实现与冻结边界冲突时记录 drift，不允许静默继承。

### 关联长期决策

ADR-001—ADR-069；重点 ADR-003、ADR-004、ADR-061、ADR-069。

---

## P01 Canonical Contract、Schema Registry 与公共原语

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F2`**

**前置阶段：P00**

### 目标

建立传输无关的 Vault 领域合同、稳定错误、Action Registry、Schema Registry 和可复用公共原语，为后续 FastAPI、gRPC、IPC、Provider 和 backend 适配提供唯一语义来源。

### 工作包

#### P01-W01 领域标识与 ResourceRef

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

定义 Tenant、Project、Namespace、Resource、Key、Secret、Version、Lease、Certificate、Command、Operation、Capability、Event、Provider 等稳定不透明 ID；Ref 只定位、不授权，并按敏感拓扑数据处理。普通 Tenant ResourceRef 与 Root/Seal、内部 Authority Key、Shard/Region、Audit Anchor、Trusted Time 等 system-scoped Internal Authority Ref 必须类型隔离，禁止通过普通 Tenant API 相互解析。`SecretRef` 默认解析 `CURRENT` 时，实际 Capability 和审计仍必须绑定解析后的 Version 与 Resource Generation；跨 Project/Namespace Ref 不产生隐式可见性或权限。

#### P01-W02 Canonical Contract

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

定义 Principal、ResourceRef、Action、Command、Query、CryptoOperation、DeliveryOperation、ApprovalEvidence、ExecutionReceipt、Lease、SecurityEvent、StableError 等领域合同，不绑定 FastAPI/Pydantic/Protobuf。

#### P01-W03 Action 与错误注册表

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立稳定 Action Registry、错误分类、HTTP/gRPC/IPC 映射和敏感错误 details 规则；内部接口不得获得隐式 Action。

#### P01-W04 Schema Registry

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立 API、Command、Event、Policy、Resource、Secret Type、Provider Protocol 和 SDK Schema 的版本、兼容模式、弃用和迁移元数据。

#### P01-W05 公共设施差距分析

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

逐项评审 `ns_common.config`、exceptions、security、time、identifiers、http_client、state_store、async_runtime、observability 和 testing；只扩展真正通用的能力。

#### P01-W06 合同与安全负向测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖未知字段、未知 Action、版本降级、类型混淆、Tenant ResourceRef/Internal Authority Ref 混用、Ref 作为凭证、敏感 details、跨 Tenant 引用、无 Grant 的跨 Project/Namespace 引用和传输映射一致性。

### 持续冻结边界

- Pydantic、Django serializer、Protobuf message 和 ORM model 都不是领域权威。
- 业务合同版本与传输协议版本分别治理。
- 旧弱 Schema 可以读/迁移，但不得继续创建新资源。

### 阶段出口

- 所有核心领域对象具有明确版本、验证和稳定错误。
- REST/gRPC/IPC 适配可以从同一合同生成或映射。
- 公共设施扩展不引用 `ns_vault` 私有模型。
- T1/T2/T7 测试通过且无敏感信息泄露。

### 回滚与停止条件

- 任何合同无法表达已冻结 security epoch、generation、approval、idempotency 或 tenancy 时停止。
- 公共层变更影响既有组件时必须拆成独立兼容工作包。

### 关联长期决策

ADR-003、ADR-004、ADR-050、ADR-062、ADR-063、ADR-064。

---

## P02 FastAPI 服务骨架、Composition Root 与多协议安全进程 bootstrap

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F2`**

**前置阶段：P01**

### 目标

建立 `src/ns_vault` 独立 FastAPI/ASGI 服务、显式 Composition Root、配置、进程生命周期和 REST/gRPC/认证 IPC 适配骨架；此阶段只形成安全骨架，不开放真实 Key/Secret 能力。

### 工作包

#### P02-W01 独立服务目录与入口

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立 `src/ns_vault` 独立进程入口、FastAPI/ASGI adapter、启动配置和健康/证明接口；不把服务实现为 Django App。

#### P02-W02 显式 Composition Root

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

所有配置、Clock、Storage、Policy、Audit、Provider、Scheduler 和 Authority 依赖从启动边界注入；禁止全局可变状态和深层实例化。

#### P02-W03 进程与 IPC 合同骨架

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立 API Layer、Command Coordination、Crypto Authority、Root/Seal Authority、Provider Host、Audit Writer、Scheduler 的最小进程身份和认证 IPC。

#### P02-W04 配置与 Feature Gate

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

基于 `ns_common.config` 建立 Vault 配置组、不可变快照、敏感引用和默认关闭的能力门禁；配置文件不保存明文根密钥。

#### P02-W05 启动、关闭与资源所有权

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

优先复用或兼容扩展 `ns_common.async_runtime` 的标准 asyncio、任务监督和资源 owner 原语，建立可重试、有界、无二次 owner 的生命周期；进程崩溃和启动失败不泄露密钥或底层异常。

#### P02-W06 REST、gRPC 与内部 IPC Adapter 骨架

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

从 Canonical Contract 映射外部/控制面 REST、数据面 gRPC 和 Authority 内部认证 IPC；当前只开放健康、证明、版本协商和稳定的 feature-disabled 响应，不形成传输专属权限旁路。

#### P02-W07 骨架与协议一致性测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

验证 FastAPI 仅是 adapter、Django 不进入 Authority、REST/gRPC/IPC 的身份与 StableError 语义一致、IPC 认证、进程隔离、feature-disabled 和 shutdown 语义。

### 持续冻结边界

- 普通 API 进程不得持有 Root Key、Tenant KEK 或 Provider 主能力。
- 未 Seal/Unseal 完成时只允许受限健康、证明和恢复接口。
- REST、gRPC 与内部 IPC 都不得因协议、本机或内网位置免除身份、版本、范围和审计校验。

### 阶段出口

- 独立 FastAPI/ASGI 服务可以安全启动和关闭。
- 进程身份、IPC、依赖方向和资源 owner 通过合同测试。
- REST/gRPC/IPC 对同一骨架 Action 具有一致的 Canonical Contract、版本协商和 StableError。
- 所有产品 Action 仍保持 feature-disabled。

### 回滚与停止条件

- 若根材料进入普通进程、环境变量、日志或 crash report，立即停止并清理。
- 若 Composition Root 无法证明依赖方向，禁止进入存储和 Authority 实现。
- 若任一传输需要专属授权捷径才能工作，停止并修正 Canonical Contract 或 adapter。

### 关联长期决策

ADR-002、ADR-003、ADR-004、ADR-020、ADR-060、ADR-061、ADR-062。

---

## P03 分层存储、Migration、Command/Event/Outbox 与 SingleWriter Authority 底座

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P01/P02**

### 目标

建立 Vault 独立 Authority DB、Security Event Store、State Store 和 Object Storage 边界，以及 Command、Actual State、Receipt、Event、Projection、强审计 outbox 和稳定的单写 Authority 合同。P18 只把该合同扩展为分片、选主、Replica 和区域内 HA，不得重写资源写入语义。

### 工作包

#### P03-W01 存储技术评估与合同

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

在 ADR 约束下选择关系数据库、Event Store、State Store、Object Storage 的具体实现；明确权威顺序、事务、隔离、备份和故障语义。

#### P03-W02 独立 Migration 基线

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立 `ns_vault` 独立 Migration 生命周期和数据库账号；Django ORM 不得访问 Authority Storage。

#### P03-W03 Command 与 Operation Record

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 command_id、operation_id、idempotency_key、expected_generation、authority_epoch、状态和结果不确定语义。

#### P03-W04 Actual State 与 Generation 原语

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立资源 generation、版本状态机、tombstone、security epoch 和乐观并发原语。

#### P03-W05 删除、墓碑与密码学销毁底座

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立 `DISABLED`、`PENDING_DELETION`、`TOMBSTONED`、`CRYPTO_DESTROYED`、`METADATA_PURGED` 的通用状态和依赖图；ID 不复用，最小墓碑、销毁事实和 Strong Audit 长期保留，数据库记录删除不能冒充密码学销毁。

#### P03-W06 Security Event 与事务 Outbox

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

成功权威写入必须同时产生可恢复审计意图；异步 Writer 不能依赖 best-effort 队列补记。

#### P03-W07 Event Stream 与 Projection Contract

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

定义 backend 可消费的事件/receipt 和 reconciliation query；Projection 不可反写 Actual State。

#### P03-W08 SingleWriter Authority Contract

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

定义 `shard_id`、Authority ownership、`authority_epoch`、fencing assertion、写入路由和 leader-only operation 接口；先提供单节点唯一 owner 实现，所有 Key/Secret/Lease/Certificate/Provider 状态写入必须从首日经过该合同，禁止先直写数据库再等待 P18 重构。

#### P03-W09 存储、Authority 与故障测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖事务冲突、崩溃恢复、重复 command、stale authority epoch、fencing 拒绝、数据库回滚、Event 丢失、State Store 不可用、Object Storage 失败、墓碑 ID 重用和旧备份恢复已销毁能力。

### 持续冻结边界

- 关系数据库保存 Current Actual State；Event Store 不通过 replay 单独成为当前状态权威。
- State Store 的 leader/lease 记录不能单独授予安全写权。
- Object Storage 只保存受控密文归档/备份，不替代普通 Secret Store。
- P03 的单节点 owner 是最终 SingleWriter Authority 合同的首个实现，不是允许其他模块直写的临时模式。

### 阶段出口

- 所有权威状态写入具备 generation、幂等、Authority assertion 和 outbox。
- 进程重启后可区分 success、failure 与 external/commit unknown。
- 真实选择的关系数据库和至少一个 Event/State Store 路径完成 T4/T5/T6 验证。
- 后续资源阶段只能调用 SingleWriter Authority 接口；P18 扩展部署拓扑但不改变调用合同。

### 回滚与停止条件

- 无法保证状态与审计意图关联时不得开放写 Action。
- 发现需要跨存储分布式事务时优先重构流程为显式状态机，禁止隐藏二阶段提交假设。
- 发现任何资源模块绕过 SingleWriter Authority 直接修改 Actual State 时停止。

### 关联长期决策

ADR-017、ADR-018、ADR-023、ADR-049、ADR-052、ADR-059。

---

## P04 Root/Seal Authority、Provider Host、本地 Strong Audit 与安全时间底座

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P02/P03**

### 目标

实现分级信任根、SEALED 状态、Root Provider 自动解封、门限恢复接口、隔离 Provider Host、签名 Manifest、最小 Software Provider，以及所有后续安全资源都必须依赖的本地 Strong Audit 与不可回退安全时间底座。

### 工作包

#### P04-W01 Root/Seal Authority

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 SEALED/UNSEALED 状态、bootstrap、Root Provider handle、root_epoch 和普通进程不可见的专用 Root/Seal Authority 边界；明文解封结果只能终止于该边界或 Crypto Authority 的严格 bootstrap 子边界，不能进入通用 Provider Host。 明确 Software Root Provider、HSM/KMS/TPM 和外部 Root Provider 的保障差异，并验证不存在可绕过 Tenant Key Domain 或客户 HYOK Provider 的隐藏万能根。

#### P04-W02 自动解封与恢复合同

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 Provider 自动解封、fail-closed、门限恢复证据和 root_epoch 提升；恢复份额不成为日常 API credential。

#### P04-W03 Provider Host 协议

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现能力分类、版本化 IPC、最小运行身份、网络 allowlist、租户/Key Domain scope 和稳定错误映射；通用 Provider Host 只能传递 opaque handle、wrapped material 或受限结果，不得承接 Root/Seal 明文输出。

#### P04-W04 Provider Manifest

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现签名/完整性验证、制品摘要、实现/协议版本、能力、算法、assurance、exportability、cacheability、fencing/idempotency/reconciliation 声明，并定义版本兼容、灰度、回滚和未完成 operation 接管门禁。

#### P04-W05 Provider Operation State Machine

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 PREPARE 持久化、EXECUTE、CONFIRM/RECONCILE、COMMIT RESULT 和 EXTERNAL_STATE_UNKNOWN。

#### P04-W06 Software Provider

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现明确 `software` assurance 的最小 Key custody/wrapping 能力；宿主机 root 仍在信任边界内。

#### P04-W07 Internal Authority Key Registry

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立只供 Vault 安全基础设施使用的内部 Key Registry 与 Provider handle 生命周期，至少区分 Root/Seal、Audit Checkpoint、Capability Issuer、Provider Manifest Trust、Authority Session/Delegation 等用途。内部 Key 不通过普通 Tenant Key API 暴露，不与业务 Key、CA、Transit、Backup Protection Key 复用，并支持 generation、staged/active/retired、root/security epoch 绑定和受控轮换；P06、P17 等阶段只能消费窄接口，不能直接取得私钥材料。

#### P04-W08 本地 Strong Audit Authority

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

消费 P03 事务 outbox，建立 Shard-local monotonic sequence、hash link、签名检查点、可靠有界缓冲和 fail-closed 门禁；本阶段先保证本地链与可恢复关联，外部不可变锚定和跨节点接管强化在 P17 完成。

#### P04-W09 安全时间底座

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 wall time + monotonic security time、`TRUSTED/BOUNDED/DEGRADED/UNTRUSTED` 状态、已消耗 TTL、可信时间下界、时钟回退/快照恢复检测和持久化恢复合同；建立 Action 最低时间等级矩阵：公开验证可在受限降级下执行，Capability/动态凭证至少 BOUNDED，证书签发和高风险恢复按 Guardrail 要求 TRUSTED 或严格 BOUNDED。外部可信时间证明与多源仲裁在 P17 完成。

#### P04-W10 安全与故障验证

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 Host crash、重复执行、Manifest 伪造、scope 越权、root mismatch、自动解封失败、恢复门限不足、审计 outbox/chain 故障、clock rollback/snapshot 和明文泄露。

### 持续冻结边界

- 通用 Provider Host 不得中转或缓存 root 明文解封结果。
- Provider Host 不写 Vault Authority DB、不签发 Capability、不修改 Policy。
- Software Provider 不得宣称 HSM/HYOK 保障。
- P05 及后续身份、授权和资源阶段不得绕过本地 Strong Audit 或安全时间底座；缺失时相关 Action 必须保持 disabled。

### 阶段出口

- SEALED 状态严格拒绝数据面能力。
- Software Provider 可在明确低保障模式下完成受控操作。
- Provider 外部副作用在崩溃与网络不确定条件下可对账。
- 门限恢复只允许预定义恢复 Action。
- 本地权威状态、内部 Authority Key、审计意图、签名链和安全时间状态形成可恢复闭环；Capability、审计、Manifest、业务和备份用途不存在密钥复用；后续阶段不需要临时审计、签名或时间实现。

### 回滚与停止条件

- 任何明文 root material 离开专用 Authority 边界时停止。
- Provider 不具备所声明能力或无法对账时保持 disabled，不允许软件静默回退。
- 本地 Strong Audit 或安全时间状态无法恢复时，禁止进入 P05 及后续安全资源实现。

### 关联长期决策

ADR-019—ADR-026、ADR-049、ADR-051、ADR-065。

---

## P05 SaaS 引用、Vault 资源层级、Principal 与身份联邦

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P01/P03/P04**

### 目标

建立 Platform/Customer Account 的非权威引用与映射合同，以及由 Vault 权威管理的 Tenant、Project、Namespace、Resource、Tenant Key Domain、Principal Binding、issuer/trust bundle 和 workload attestation。Platform/Customer 的真实生命周期、合同和运营数据仍由 `ns_backend.vault` 在 P10/P16 管理。

### 工作包

#### P05-W01 Account Mapping 与 Vault 资源层级

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

定义稳定的 Platform/Customer Account Ref 和 Customer→Vault Tenant 映射合同，但这些 Ref 不产生密码学权限；在 Vault Authority 内实现普通租户资源的 Tenant/Project/Namespace/Resource 稳定 ID、唯一归属、重命名不改身份、禁止跨 Tenant 移动和 default Project/Namespace 的显式底层模型。Tenant Key Domain 与平台内部 Root/Seal、Authority Key、Backup、Shard/Region、Audit/Time 等资源使用明确非目录 scope 和独立 Ref 类型，不伪造 Project/Namespace。跨 Project/Namespace 访问默认无隐式继承，只能由同一 Tenant 内显式 Grant/Guardrail 与目标 Resource/Generation Capability 放行。允许范围内的 Namespace/Resource move 必须由 SingleWriter Authority/Shard Leader 作为 expected-generation 安全命令执行，重新计算策略、提升 generation、撤销旧 Capability、处理或拒绝活动 Lease/Certificate/Provider Operation 并写入 Strong Audit；历史密码学制品保留创建时 cryptographic scope，不能通过 metadata-only move 改写 AAD 或认证内容，不支持安全迁移时必须使用显式重加密/迁移或新资源。

#### P05-W02 Tenant Key Domain 元数据

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立每租户独立 Key Domain、home region、assurance、Provider binding、generation 和生命周期。

#### P05-W03 Principal 与 Binding

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 human、service、workload、node、device、provider、external_customer、recovery 类型和 issuer+subject+tenant 绑定。

#### P05-W04 Federated Authentication

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

支持本地验证的 OIDC/mTLS/SPIFFE/Kubernetes/cloud identity/attestation adapter，不把外部 role/group 直接变成 Vault 权限；长期凭证只允许 bootstrap、恢复或受控初始化，正常数据面必须换取短期身份/Capability。受 Vault 信任 assertion 的签发私钥必须位于独立 SSO/IdP、隔离 Identity Authority、HSM/KMS 或等价边界，普通 `ns_backend` Web/API 进程、数据库字段、内部请求头和服务凭证不得成为任意主体 issuer。

#### P05-W05 未来 SSO 兼容合同

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

只定义 Identity Assertion、assurance、MFA、session validity、revocation 和 trust bundle 接口；不设计 SSO 内部账号与会话。

#### P05-W06 Workload/Node Attestation

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立 ns_runtime Authority Attestor、ns_node 节点证明、TPM/TEE/设备证明等可插拔 evidence 绑定。

#### P05-W07 身份安全测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 issuer 混淆、subject 碰撞、audience、tenant、claim 注入、角色越权、撤销、assurance 降级、普通 backend 伪造 assertion、未签名内部头建 Principal 和 issuer signing authority 与普通服务进程共域。

### 持续冻结边界

- Vault 不复制 Platform/Customer 合同、SLA、Billing 或完整客户目录；只保存安全裁决所需的稳定 Account Ref/Tenant 映射和版本。
- Vault 不复制完整 SSO/IAM 用户目录。
- 普通 backend 进程不得持有可为任意主体签发受信任断言的根能力。
- Node、workload、service、human、recovery 不得隐式转换。

### 阶段出口

- Platform/Customer Account Ref 不会直接授予 Tenant 或数据面权限，Customer 生命周期与 Tenant 密码学生命周期保持分离。
- 多 issuer、本地验证和 trust rotation 可用。
- Principal Binding 变更具有版本、撤销和强审计输入。
- 跨 Tenant、role/group 直授和普通 backend 冒充测试全部拒绝。

### 回滚与停止条件

- 若身份事实与 Vault Principal 无法建立稳定不可歧义映射，禁止开放数据面。
- 未来 SSO 细节不足不能由 Vault 工作包自行补全。

### 关联长期决策

ADR-006—ADR-011。

---

## P06 Guardrail、Grant、Policy Artifact、Approval 与 Capability

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P04/P05**

### 目标

实现默认拒绝的 Vault Authorization Authority、Mandatory Guardrail、Delegable Grant、Policy Intent/Artifact 验证、分层审批、Break-glass 和短期 Scoped Capability。

### 工作包

#### P06-W01 Policy Domain Model

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 Guardrail、Grant、explicit deny、scope、condition、inheritance、delegation depth、validity 和 version；RBAC 角色只能作为可复用 Grant 模板，上级 Allow 不默认向下传播，委派者不能授予超过自身 delegation ceiling 的能力。

#### P06-W02 Policy Intent/Artifact

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

定义 backend Intent、编译器制品身份、Approval、Artifact hash/schema/scope/effective time，以及受版本治理、可静态验证的声明式 Policy IR；Vault 机械校验 Grant/Deny/Guardrail/Scope/Condition/Delegation 的权限上界并独立验证非扩权，禁止任意脚本、动态导入或无法证明上界的表达式。

#### P06-W03 Authorization Engine

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

按 identity binding + grant + all guardrails + no deny + resource/security state 计算并生成可解释决策。

#### P06-W04 Security Approval

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现普通 backend Approval 证据与 Vault Security Approval，绑定 operation/resource/generation/authentication/time/dual control。

#### P06-W05 Break-glass

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 recovery principal、门限 evidence、预定义紧急 Action、短期 emergency session；不得关闭审计、导出 non-exportable key、绕过 Tenant Guardrail 或把恢复会话升级为通用管理员。

#### P06-W06 Capability Issuer/Verifier

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

通过 P04 Internal Authority Key Registry 的专用 Capability Issuer Key generation 签发并验证 principal、tenant、resource、action、generation、shard、epoch、policy、approval、expiry、budget、channel/workload binding；建立签发公钥/trust bundle 轮换和旧 token 有界验证窗口。普通 Capability 默认不可委派；确需再委派时必须使用独立 Delegation Capability 类型并受 delegation ceiling/depth/expiry 限制。Capability 不得携带 Secret、DEK、私钥、完整动态凭证或 Provider 主能力。

#### P06-W07 撤销与 Epoch

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 deny list、principal/resource/policy/security epoch、紧急禁用和旧 Capability 立即失效。

#### P06-W08 授权安全矩阵

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 backend 超级管理员、伪造 Artifact、过期审批、delegation 扩权、旧 generation、replay、跨 shard 和 assurance 降级。

### 持续冻结边界

- Capability 只能缩小权限，普通 Capability 不可委派。
- backend、Broker、Agent、SDK 和 Provider Host 都不能签发 Vault 数据面 Capability。
- 高风险执行时必须重新检查当前状态，不只依赖 token 内容。

### 阶段出口

- 决策可解释、可版本化、可审计。
- 紧急禁用能在未到期 token 上立即生效。
- 所有核心越权、重放和编译器失陷场景 fail-closed。

### 回滚与停止条件

- 无法证明 Artifact 非扩权或审批来源时不得应用策略。
- 授权引擎任何异常不得回退 Allow。

### 关联长期决策

ADR-012—ADR-016。

---

## P07 Key Management、BYOK/HYOK 合同与版本生命周期

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P04/P05/P06**

### 目标

实现统一 Key Resource、来源/导出策略、Provider binding、Key Version 状态机、Alias、rotation、promotion、retirement、rewrap 和销毁依赖。

### 工作包

#### P07-W01 Key Resource/Version 模型

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

固定 key_class、algorithm_suite、usage、assurance、provider_binding 和 immutable metadata；`key_origin` 只允许 `vault_generated`、`provider_generated`、`imported_byok`、`external_hyok`、`derived`，`export_policy` 只允许 `non_exportable`、`public_only`、`wrapped_export`、`plaintext_export_compatibility`，创建后不得放宽。

#### P07-W02 Key Generation 与 Staging

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

通过 Software/Provider 生成并执行 `GENERATING → STAGED`；验证能力、算法、公钥/metadata 和自检。Provider 结果未知时进入 `EXTERNAL_STATE_UNKNOWN`，不得直接提升。后续状态只允许 `PRIMARY → DECRYPT_ONLY/VERIFY_ONLY/UNWRAP_ONLY → DISABLED → PENDING_DESTRUCTION → CRYPTO_DESTROYED` 等经 Key Class 许可的迁移。

#### P07-W03 Primary Promotion

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

由当前 SingleWriter Authority owner 以 expected primary/generation/epoch/idempotency 原子切换唯一 Primary；P18 后该 owner 由 Shard Leader 实现。

#### P07-W04 Historical Use

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

旧版本仅允许 decrypt/verify/unwrap 或历史内部引用，不产生新 ciphertext/signature/MAC/wrapped/derived output。

#### P07-W05 Tenant KEK Rotation 与渐进式 Rewrap

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 Tenant Key Domain KEK generation、唯一当前包装版本、旧 generation 的受限 unwrap、批量 DEK rewrap 队列、进度/失败/暂停/恢复、幂等和崩溃恢复。KEK rotation 默认只 rewrap DEK，不重新加密 Secret ciphertext；旧 KEK generation 在全部依赖完成 rewrap 或明确批准大范围销毁前不得销毁，Provider 迁移不得静默降低 assurance。

#### P07-W06 BYOK Import

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现直接进入 Authority/Provider Host 的受保护导入、import token/wrapping、IMPORT_PENDING 和结果未知对账。

#### P07-W07 HYOK 合同与禁用引用

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

定义 `external_hyok` 的不可变 Key Origin、客户控制、平台不可恢复、Provider capability、无隐藏恢复副本和稳定错误合同；本阶段只允许创建经过验证但不可执行的禁用引用，真实 HYOK Provider 认证、数据面调用、reconciliation 和客户接入在 P16 完成前保持 feature-disabled。

#### P07-W08 Export 与 Migration

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现独立高风险 export Action、non_exportable 不可放宽、wrapped/plaintext compatibility 和新 Key 迁移关系；任何明文兼容导出必须创建时已允许、近期强认证、独立审批、一次性交付、禁止 backend 中转并形成 Strong Audit。算法/Provider 迁移必须显式经过 PREPARING、DUAL_READ_OR_VERIFY、CUTOVER、RETIRED 或等价状态，不能通过 Alias 静默切换。

#### P07-W09 Key 删除与密码学销毁

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 Version/Key/Key Domain 的禁用、恢复窗口、墓碑、依赖检查、rewrap 证明、Provider destroy confirmation 和大范围销毁双人门禁；未确认 Provider 销毁不得标记完成。

#### P07-W10 Key Lifecycle 测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖双 Primary、算法/用途变更、旧版本新写、Provider unknown、导出越权、BYOK/HYOK、墓碑、rewrap 依赖和密码学销毁。

### 持续冻结边界

- Alias 不是密码学身份；所有结果记录实际 key_id+version+algorithm。
- 不可导出 Key 不能为了迁移临时变为可导出。
- 不同用途必须使用不同 Key。

### 阶段出口

- Key Resource 与 Version 状态机完整。
- Software Provider 实际路径达到 F3；外部 HSM/KMS 保持按真实环境单独验收，HYOK 此阶段只完成禁用合同与引用，执行能力必须等待 P16。
- Tenant KEK rotation/渐进式 rewrap、Key Version 轮换、并发、崩溃和 Provider 对账测试通过。

### 回滚与停止条件

- Provider 结果未知时保持 EXTERNAL_STATE_UNKNOWN，不得重复盲建。
- 任何修改不可变安全属性的需求必须创建新 Key。

### 关联长期决策

ADR-024—ADR-026、ADR-058。

---

## P08 Secret Management、Envelope Encryption 与静态轮换

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P07**

### 目标

实现 Secret Resource/Version、独立 DEK、Tenant KEK wrapping、标准类型、字段级交付、Current 激活、人工读取和受控静态 Secret 轮换。

### 工作包

#### P08-W01 Secret Upload Session

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立直接到 Vault 的认证上传、大小限制、content/type/schema 校验和 `UPLOADING`/结果未知状态；backend 不代理 payload。成功密封后只能进入 `STAGED`，不能直接成为 `CURRENT`。

#### P08-W02 Envelope Encryption

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

每 Version 随机 DEK，AEAD 加密并认证 Tenant/Key Domain、创建该 Version 时的稳定 Project/Namespace、Secret/Version、format、KEK generation 和 provider binding；历史 Version 在同 Tenant move 后继续以 origin cryptographic scope 验证，新 Version 才使用新 scope。

#### P08-W03 DEK Cache

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

Authority 内短期有界缓存，绑定 Key Domain/Version/KEK/Provider/security epoch；高保障与 HYOK 可禁用。缓存只优化 unwrap，不缓存授权结果，Provider 故障时不得延长 TTL 或把缓存转为无限离线能力。

#### P08-W04 Secret Type Registry

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 opaque、key_value、username_password、tls_bundle、ssh_key_pair、docker_registry、cloud_service_account、provider_credential 的简单版本化 Schema；每类固定硬大小上限、content type 和 payload schema version，解析器禁止任意对象反序列化、代码执行、外部实体、自动网络访问和递归压缩展开。

#### P08-W05 Field Action

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

只对标准类型支持稳定字段标识和字段 Capability；Vault 裁剪后交付，Agent 不先取整包。

#### P08-W06 Version Activate/Rollback

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 `STAGED → CURRENT → PREVIOUS → DISABLED → PENDING_DELETION → CRYPTO_DESTROYED` 状态机、唯一 `CURRENT`、generation、旧 Capability 失效、通知和受控历史读取；回滚是新的权威状态变更，不是数据库指针倒退。

#### P08-W07 Delivery 与人工读取

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

默认文件/FD/socket/tmpfs/受控 response；人工明文读取使用 Vault Security Approval、一次性会话和 Strong Audit。

#### P08-W08 Static Secret Rotation

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

候选值先密封保存，再修改外部目标、验证、激活、通知、清理旧值；崩溃和结果未知可恢复。

#### P08-W09 Secret 删除与密码学销毁

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

单 Version 通过销毁该 Version DEK 实现密码学销毁；整个 Secret 覆盖全部 Version，并保留稳定墓碑、销毁证明和最小审计。已销毁 Version 不能通过数据库或备份恢复重新激活。

#### P08-W10 Secret 安全测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 AAD 替换、wrapped DEK 错配、Current 竞争、跨 Project/Namespace 无 Grant 访问、metadata-only move 改写 AAD、move 后历史 Version 验证/新 Version scope、活动 Lease/Provider Operation 阻塞迁移、schema parser、field 越权、日志/错误泄露、backend 代理、轮换崩溃、墓碑和旧备份复活。

### 持续冻结边界

- 完整 Secret Version 是密码学、版本和生命周期最小单位。
- Secret 内容变化只能创建新 Version。
- 普通读取只解析 Current，不能任意指定历史版本。
- 低熵 Secret 不记录普通明文 hash。

### 阶段出口

- Secret create/read/activate/rollback/destroy 的 Authority 路径完整。
- 所有明文路径经过敏感信息扫描。
- 静态轮换在外部目标更新前后崩溃均可对账或恢复。

### 回滚与停止条件

- 任何明文进入 backend、普通 API 日志、持久化暂存或未批准缓存时停止。
- 外部轮换结果未知时不得激活候选版本或重新生成。

### 关联长期决策

ADR-027—ADR-033、ADR-058。

---

## P09 Lease Authority 与调度引擎

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P03/P04/P05/P06**

### 目标

实现统一 Lease 权威状态机、父子关系、续期、撤销、到期、清理、调度、时间和 Provider 对账，为证书、动态凭证和会话提供统一基础。

### 工作包

#### P09-W01 Lease Domain/State Machine

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 `PENDING`、`ACTIVE`、`RENEWING`、`EXPIRED`、`REVOCATION_PENDING`、`REVOKING`、`REVOKED`、`CLEANED`、`REVOCATION_FAILED`、`EXTERNAL_STATE_UNKNOWN`，禁止用单一布尔值压缩。

#### P09-W02 Lease Binding

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

绑定 tenant/project/namespace/principal/workload/resource/role/provider/shard/epoch/capability/channel/max lifetime。

#### P09-W03 Renew

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

每次重新校验身份、Policy、Guardrail、resource/provider state、time；使用 lease_generation+renewal_id 幂等。

#### P09-W04 Revoke/Expire/Cascade

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

区分自然到期与主动撤销，支持 parent、principal、resource、namespace、tenant 级联。

#### P09-W05 Scheduler

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现高容量到期调度、backpressure、重启恢复和时间异常；所有状态写入经过 P03 SingleWriter Authority，P18 后由 Shard Leader 承载。

#### P09-W06 Provider Reconciliation

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

撤销失败进入 pending/failed/unknown，不标记安全完成，并限制高风险新签发。

#### P09-W07 Lease 测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖并发 renew、超最大寿命、父子级联、时间回退、重启、重复 revoke、Provider 不可用和 Agent 代续期。

### 持续冻结边界

- Lease 默认不可转让，Agent 不能改变主体、范围或最大寿命。
- 离线状态不得续 Lease。
- EXPIRED 与 REVOKED 语义不可混淆。

### 阶段出口

- Lease 状态和 Provider 实际状态可对账。
- 大量 Lease 的调度、重启和并发路径达到 F3。
- 安全时间异常不会使已过期 Lease 复活。

### 回滚与停止条件

- Provider 撤销结果未知时禁止伪造 REVOKED。
- 调度器不能成为第二写 Authority。

### 关联长期决策

ADR-042、ADR-051—ADR-053、ADR-057。

---

## P10 Django 控制面、命令、投影与 reconciliation

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P03/P05/P06/P07/P08/P09**

### 目标

在 `src/ns_backend/vault` 建立统一控制面域，管理 Customer/Tenant、Intent、Approval、Desired State、Command、Projection、Quota/Metering 入口，但不接触 Secret 明文或 Authority DB。

### 工作包

#### P10-W01 Django Vault App 基线

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

以固定路径 `src/ns_backend/vault` 和 App Key `vault` 接入 app loader、URL、权限和数据库路由；所有 Vault 控制面 View 必须显式配置认证与权限，禁止继承当前全局 `AllowAny` 形成匿名入口；建立控制面独立模型与 Migration，不访问 Vault Authority DB。

#### P10-W02 Desired State 与 Command

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现用户操作、Intent、Approval、command idempotency、状态和 receipt 关联。

#### P10-W03 Projection

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 DESIRED、PENDING、OBSERVED、DRIFTED、UNKNOWN，禁止把 submitted 当 completed。

#### P10-W04 Event Consumer

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

消费 Vault Receipt/Event，处理顺序、去重、重放和 gap。

#### P10-W05 Reconciliation

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

周期 Pull Actual State，比对并修复 Projection；发现 drift 不自动覆盖 Vault。

#### P10-W06 Frontend 安全入口

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

ns_frontend 只通过控制面管理 metadata；Secret 上传/读取使用 Vault 一次性直连会话，browser/backend 不代理明文。浏览器 Grant 必须绑定用户 Principal、Tenant、Action、Resource/Generation、Origin/会话、短 TTL 和一次性预算，不进入 URL、Referer、缓存或普通前端日志；CORS/CSRF/replay 策略必须 fail-closed。

#### P10-W07 控制面测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖匿名访问、全局 `AllowAny` 误继承、Event 丢失、重复、乱序、Vault 不可用、pending/unknown、browser Grant replay/origin 错配、backend DB 恢复和超级管理员越权。

### 持续冻结边界

- Projection、Desired State 和管理审计都不是 Vault Actual State。
- backend DB 不保存 Secret ciphertext、wrapped DEK、Lease payload 或 Strong Audit 原始链。
- backend 不得创建通用 Vault 管理 bearer credential。

### 阶段出口

- 控制面能准确展示 pending/unknown/drift，不伪造成功。
- Event 丢失后 reconciliation 可恢复投影。
- Secret 明文和 Key 私密材料未进入 backend。

### 回滚与停止条件

- 发现任何 ORM 访问 Authority Storage 或 backend 代理 Secret payload 时停止。
- Projection 与 Actual State 冲突时保留 Vault 权威，禁止自动反写。

### 关联长期决策

ADR-002、ADR-006、ADR-013、ADR-017、ADR-018、ADR-061、ADR-066。

---

## P11 Vault Delivery Agent、本地交付与 ns_client SDK

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P06/P08/P09**

### 目标

建立正式但可选的 Vault Delivery Agent/Sidecar/CSI/Windows Service 和按 Principal 类型的 ns_client 核心 SDK，先落实 Secret、Lease、Key metadata、本地身份、Capability、原子文件和受控交付；Vault Delivery Agent 明确不等同 `ns_node` 或未来 `ns_agent`，不得占用 `src/ns_agent` 产品边界；Transit、PKI 与 Dynamic Credential 的客户端扩展分别由 P13—P15 完成。

### 工作包

#### P11-W01 Agent Local Identity

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

基于 OS process credential、cgroup/container、service identity、TPM/attestation 识别本地 workload；不信任自报名称。

#### P11-W02 Local Delivery

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 Unix Socket/Named Pipe/FD/file/tmpfs/once injection，最小权限、fsync/等价持久化和原子替换。

#### P11-W03 Lease/Rotation Client

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

Agent 代表原 workload renew，不改变 scope/max lifetime；处理版本通知、文件切换和受控 hook。

#### P11-W04 Offline Policy

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

只在现有 Capability/Lease/cache TTL 剩余范围内服务，不离线签发、续期或扩大权限。

#### P11-W05 ns_client Modes

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 human/service/workload/node/external client 的身份适配、Capability、Lease、Secret 与 Key metadata 核心合同；Transit、Certificate 和 Dynamic Credential Action 此阶段保持明确 feature-disabled，由 P13—P15 在同一 SDK 合同上扩展。

#### P11-W06 SDK 安全存储

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

不保存长期高权限 token，不把 node/workload 模式互换；本地缓存按 Guardrail。

#### P11-W07 官方 CLI

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现基于 `ns_client` 的 human/service/external 管理与数据面入口；Secret、私钥和动态凭证默认不得输出到终端历史或普通 stdout，必须使用显式一次性显示、受限文件、FD、pipe 或 Agent 交付，并复用相同 Capability、Approval、StableError 和审计语义。

#### P11-W08 跨平台测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 Linux/Windows、本地身份欺骗、symlink/权限、部分写入、CLI 输出/历史、crash dump、日志、offline expiry 和多 workload 隔离。

### 持续冻结边界

- Vault Delivery Agent 是交付组件，不是 Authority，也不是 `ns_node` 或未来 `ns_agent`；不得占用 `src/ns_agent` 产品边界。
- 环境变量只作为启动兼容路径，不是动态轮换默认。
- 字段级 Secret 必须由 Vault 裁剪后再交付。

### 阶段出口

- 直接 SDK 和 Agent 路径共享同一身份/授权/审计语义。
- Agent 失陷爆炸半径限制在当前 workload、资源和剩余期限。
- Linux 与 Windows 至少各完成核心本地交付验证。

### 回滚与停止条件

- 无法可信区分本机 workload 时不得部署主机级多租户 Agent。
- 任何本地缓存超出 Vault TTL 或 Guardrail 时停止。

### 关联长期决策

ADR-027、ADR-045、ADR-046、ADR-057。

---

## P12 ns_backend、ns_runtime、ns_node、ns_frontend 与 SSO 兼容集成

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P10/P11**

### 目标

在不改变各组件已冻结权威边界的前提下完成平台集成；SSO 只实现 Vault 所需兼容接口，不设计其内部产品。

### 工作包

#### P12-W01 ns_runtime Capability Exchange

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

Authority Broker 验证 runtime identity 并向 Vault exchange 短期 Capability；Broker 不签发、不中转 Secret 明文。

#### P12-W02 ns_runtime Data Plane

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

runtime 按策略直连 Vault，绑定 runtime/workload/tenant/resource/action/generation/expiry；不持有长期 Token、KEK 或 Provider 主能力。

#### P12-W03 ns_node Node Principal

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

Node Authority Broker 完成 bootstrap/evidence/exchange；`ns_node` 只能读取 node-scoped Secret，不能代表承载 workload。同一 Host 上的多个 node ID 必须拥有独立 Principal Binding 和 Capability，不得因共享 host、进程账户或本地 Agent 共享 node-scoped Secret。 所有 Vault 网络 I/O 必须经 `ns_node` 专用通信进程和受认证本地 IPC/FD 路径；调度主进程、OCR、浏览器自动化、桌面自动化和插件执行进程不得自行连接 Vault、继承 Node Capability 或隐式取得 node-scoped Secret。

#### P12-W04 ns_frontend

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

管理界面只操作 metadata、Intent、Approval、Projection；Secret payload 使用 Vault direct session。

#### P12-W05 未来 SSO 兼容

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

验证 issuer/trust bundle/assertion/assurance/MFA/session revocation 合同；不实现 SSO 用户目录、登录页面或会话体系。

#### P12-W06 组件接入登记

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

为内部/外部组件登记 principal type、trust domain、allowed protocol、assurance、quota 和 owner。

#### P12-W07 集成安全测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 Broker 自签、node 代理 workload、`ns_node` 非通信进程直连 Vault、OCR/浏览器/桌面自动化或插件进程继承 Node Capability、frontend/backend 明文代理、SSO role 直授、跨组件 token 重用和 audience 错配。

### 持续冻结边界

- 不得修改 `ns_runtime` 已有 root/attestor/FD/composition 权威边界。
- host-scoped Secret 如未来需要，必须建立独立 Host Resource，不能从 node scope 推导。
- SSO 失陷与普通 backend 失陷必须作为不同威胁域。

### 阶段出口

- 所有组件使用统一 Principal、Capability、ResourceRef、StableError 和 Strong Audit。
- node/workload/runtime/client 身份不可混淆。
- 控制面不进入 Secret 明文路径。

### 回滚与停止条件

- 任何集成要求弱化 Vault 授权或 runtime/node 既有安全边界时停止并提出新 ADR。

### 关联长期决策

ADR-009—ADR-011、ADR-045—ADR-048。

---

## P13 Transit、Derivation、Random/Password 与 Tokenization

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P07/P12**

### 目标

实现统一 Transit 密码学操作、Canonical CryptoResult、Derivation Profile、随机/密码生成 Profile 和独立 Deterministic Transform/Tokenization 资源。

### 工作包

#### P13-W01 Canonical Ciphertext/CryptoResult

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 version、key/version、algorithm、operation、provider、nonce/tag、AAD/derivation binding 和 detached metadata。

#### P13-W02 Encrypt/Decrypt/Sign/Verify/MAC/Wrap

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

按 Key Class/Version/Policy 执行；普通调用方不能指定 AEAD Nonce 或旧写版本。

#### P13-W03 Derivation Profile

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

固定 KDF、context schema、domain、output length/usage/policy，Output Policy 只允许 `internal_only`、`wrapped_export`、`provider_handle_only`、`plaintext_export_compatibility`，默认 `internal_only`。

#### P13-W04 Random/Password Profile

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

固定受批准 CSPRNG/Provider、字符集、长度、编码、约束、熵和无偏采样规则，不允许调用方绕过 Profile 自选 RNG 或不安全参数；结果按敏感一次性交付处理，接口不隐式持久化，需要长期保存时必须显式创建 Secret 或 Key Resource。

#### P13-W05 Deterministic Transform/Tokenization

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立独立资源、域、规范化、可逆/不可逆 Key Class、风险说明和 PREPARING、DUAL_TRANSFORM、REINDEXING、CUTOVER、RETIRED 迁移状态。

#### P13-W06 ns_client/CLI Transit 扩展

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

在 P11 核心 SDK/CLI 上增加 Transit、Derivation、Random/Password 和 Tokenization Action，复用 Canonical CryptoResult、Capability、StableError 和 Strong Audit；不得创建第二套客户端协议或绕过 Profile/Guardrail。

#### P13-W07 密码学互操作与负向测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 nonce 重用、AAD 错配、format 降级、detached 错配、domain collision、低熵枚举、旧版本新写和 Provider 原生格式泄漏。

### 持续冻结边界

- Transit 不持久化业务明文或完整业务密文。
- 通用收敛加密和跨租户去重不实现。
- 派生输出不能比父 Key 更可导出、更长寿或用途更广。

### 阶段出口

- Canonical Envelope/CryptoResult 跨传输和跨 SDK 一致。
- 历史密文和签名可以按实际 Key Version 解析。
- 所有高级风险能力具有独立 Action、Guardrail 和审计。
- ns_client/CLI 扩展与服务端对 Canonical CryptoResult、Capability 和错误语义保持一致。

### 回滚与停止条件

- 任何需要宽松算法猜测、Provider 原生格式作为默认合同或普通 bool 开启 deterministic 的实现必须拒绝。

### 关联长期决策

ADR-034—ADR-037。

---

## P14 PKI、Certificate Role、CRL/OCSP 与 SSH CA

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P07/P09/P12**

### 目标

实现统一 CA Resource、受约束 Trust Domain、身份绑定 Certificate Role、终端私钥模式、证书 Lease、吊销传播、外部 CA 对账和 SSH CA。

### 工作包

#### P14-W01 CA Resource/Version

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 Root/Intermediate/Issuing、算法/usage/name constraints/path length/provider/assurance 固定和 CA Version 状态机；普通历史 CA 不得继续签发，仍有有效证书吊销义务时只允许专用 `REVOCATION_STATUS_ONLY`。

#### P14-W02 Certificate Role

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

固定证书类型、身份派生、SAN/Subject/EKU、最大寿命、私钥模式、续期是否复用原私钥和吊销机制；workload 身份优先从 attestation 派生，人工 DNS/设备身份必须先登记并验证所有权，Wildcard 默认拒绝且只能由显式 Guardrail 限域、限期放行。

#### P14-W03 CSR 与私钥模式

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

支持 caller/agent/vault exportable/provider non-exportable；CSR 只证明持钥，身份由 Vault 重建/验证。Vault 生成的可导出终端私钥只允许一次性交付、不得普通再次读取；交付结果不确定时进入显式恢复/撤销状态，私钥丢失默认重新生成并重新签发。

#### P14-W04 Issuance

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

当前 SingleWriter Authority owner 分配权威 serial，调用 CA Provider，验证返回证书完全匹配批准内容并创建 Lease；P18 后由 Shard Leader 承载。

#### P14-W05 Revocation/CRL/OCSP

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 Certificate `PENDING`、`ACTIVE`、`SUSPENDED`、`REVOCATION_PENDING`、`REVOKED`、`EXPIRED`、`EXTERNAL_STATE_UNKNOWN` 等权威状态，以及单调 CRL Number、OCSP 专用 Key、紧急 deny、陈旧窗口和外部 CA 对账。

#### P14-W06 CA Rotation/Migration

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现旧 CA 的 REVOCATION_STATUS_ONLY、双链迁移、有效证书依赖和销毁门禁。

#### P14-W07 SSH CA

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

复用资源、身份和生命周期框架，但使用独立 Key/Role/Principal 语义。

#### P14-W08 Agent/ns_client 证书集成

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

在 P11 Agent/ns_client 核心能力上实现 caller/agent/provider 私钥模式、CSR、证书/链交付、Lease 续期、原子证书切换、吊销状态和私钥轮换；不得让 Agent 或客户端自行声明未授权身份。

#### P14-W09 PKI 安全测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖任意 SAN、跨租户签发、外部 CA 返回篡改、serial 冲突、CRL 回退、OCSP key 混用和 CA 过早销毁。

### 持续冻结边界

- Root CA 默认不承担日常在线签发。
- CA/SSH CA 私钥默认不可导出，不与 Transit Key 共用。
- 证书已吊销状态不能因恢复、时钟或 CA 切换重新 Active。

### 阶段出口

- 内建软件 CA 路径达到 F3；真实 HSM/外部 CA 证据按环境单独记录。
- 身份、私钥模式、Lease 和吊销机制形成统一合同。
- CRL/OCSP 连续性和故障语义通过测试。
- Agent/ns_client 的证书私钥模式、续期、轮换和吊销处理与 Certificate Role 一致。

### 回滚与停止条件

- 外部 CA 返回内容与批准内容不一致时不得交付。
- 未完成吊销义务和依赖检查前不得销毁 CA。

### 关联长期决策

ADR-038—ADR-041。

---

## P15 Dynamic Credential 与 Provider issuance mode

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P04/P09/P12**

### 目标

实现 Credential Role、per-lease identity、provider-native session、exclusive pool、shared compatibility、临时密封交付包和 Provider 清理/对账。

### 工作包

#### P15-W01 Credential Role

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

固定 Provider、权限模板、TTL、最大寿命、renew/revoke/redelivery、assurance 和交付模式；`issuance_mode` 只允许 `per_lease_identity`、`provider_native_session`、`exclusive_pool`、`rotated_shared_compatibility`。

#### P15-W02 Per-lease/Native Session

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现独立外部身份或 Provider session、稳定 external reference 和精确撤销。

#### P15-W03 Exclusive Pool

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

当前 SingleWriter Authority owner 串行分配/回收，轮换认证材料、清除权限/会话、隔离期和 QUARANTINED；P18 后由 Shard Leader 承载。

#### P15-W04 Shared Compatibility

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

显式标记静态共享轮换限制，不能宣称单 Lease 精确撤销或高保障动态凭证。

#### P15-W05 Credential Delivery Package

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

每 Lease 独立 Delivery DEK，交付模式只允许 `one_time`、`bounded_redelivery`、`provider_direct_nonrecoverable`，绑定主体、channel、次数和 expiry；默认 `one_time`。Lease 到期、撤销、父 Lease 失效或主体冻结时销毁 Delivery DEK 并清除缓存。`provider_direct_nonrecoverable` 必须直接交付绑定消费端，Vault 不保存隐藏明文副本。

#### P15-W06 Provider Cleanup/Reconciliation

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

创建/撤销/删除/清理未知时保留风险状态，并限制相关 Role 新签发。

#### P15-W07 Agent/ns_client 动态凭证集成

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

在 P11 Agent/ns_client 核心能力上实现 Lease 级临时密封凭证包、one-time/bounded redelivery、provider-direct nonrecoverable、续期/撤销与本地交付；客户端不得仅凭 Lease ID 领取或改变主体、范围和最大寿命。

#### P15-W08 动态凭证测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖响应丢失、重复创建、redelivery 越权、pool 污染、Provider orphan、共享模式风险和级联撤销。

### 持续冻结边界

- 动态凭证不自动转为普通 Secret Resource。
- 不同 Lease 不得静默共享活动 Session 或凭证值。
- 仅凭 Lease ID 不能领取凭证。

### 阶段出口

- 至少一个受控测试 Provider 的完整签发、续期、撤销、交付和清理达到 F3。
- Provider 不确定状态可恢复且不会重复创建。
- Pool member 清理不足不会重新分配。
- Agent/ns_client 的凭证交付、redelivery、续期和撤销遵守原 Lease 主体、范围和寿命约束。

### 回滚与停止条件

- 无法证明 Provider 清理完成时保持 QUARANTINED/UNKNOWN。
- Provider 不支持所声明 issuance mode 时在 Role 创建阶段拒绝。

### 关联长期决策

ADR-042—ADR-044。

---

## P16 HSM/KMS/HYOK、配额、计量、Customer Account 与外部服务治理

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P10-P15**

### 目标

完成真实 HSM/Cloud KMS 与 HYOK Provider 集成及客户控制边界，并实现 Platform Account、Customer Account、Vault Tenant 的运营映射、配额、计量、统计、安全接入和外部客户自助治理，同时保持安全权威在 Vault。

### 工作包

#### P16-W01 HSM 与 Cloud KMS Provider 集成

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

在隔离 Provider Host 中实现至少一种 HSM 或 Cloud KMS 的 Key custody/wrapping/sign/decrypt 能力适配，验证算法、不可导出属性、assurance、region/locality、session、rate limit、fencing/idempotency/reconciliation 和 Provider 原始错误隔离。Provider 能力不足时在资源创建阶段拒绝，禁止回退 Software Provider 冒充同等级保障。

#### P16-W02 HYOK Provider 与客户控制集成

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

将 P07 的禁用 `external_hyok` 合同接入真实隔离 Provider Host，完成客户 Provider 认证/重新授权、Key/operation reference、region/locality、availability、reconciliation、平台不可恢复和无隐藏替代 Key。默认数据面由 Vault Authority/Worker 发起；确需客户端直连时只签发 Provider-specific、短期、范围受限、可撤销且可审计的派生 Grant，不下发通用 Provider 主能力。

#### P16-W03 Customer/Platform Control Model

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现合同/SLA/管理员/tenant mapping，不让 Platform/Customer Account 自动获得 Secret 权限。

#### P16-W04 Quota

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

按 Tenant/Project/Namespace/Resource/Action/Provider/Lease/throughput 定义硬/软配额及权威执行位置。

#### P16-W05 Metering

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

从 Vault Actual Operation/Lease/Provider/Audit 派生计量事实，backend 负责运营汇总。

#### P16-W06 Statistics/Health

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

提供不泄露敏感值的资源、操作、失败、延迟、容量和 assurance 视图。

#### P16-W07 External Customer API 与客户端治理

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

复用 P11 的 `ns_client`/CLI、Canonical Contract、Principal、Policy、Audit 和 quota；只增加外部客户接入、文档、版本与运营约束，不建设第二套 SDK 或外部安全模型。

#### P16-W08 Tenant Lifecycle

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

开通、冻结、迁移、退出、删除和 crypto destroy 与 Customer 生命周期解耦但可编排。

#### P16-W09 多租户测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 HSM/KMS 算法与不可导出能力不匹配、session/region/rate-limit/fencing 故障、HYOK Provider 不可用、客户撤销授权、隐藏 fallback、Provider direct Grant 越权、noisy neighbor、quota bypass、billing drift、Platform admin 越权、tenant delete 和 external customer isolation。

### 持续冻结边界

- 统计、告警、计量和 billing 不得直接放行或拒绝安全 Action，除非通过已批准 Guardrail/Quota Artifact。
- Customer Account 不是密码学隔离边界。

### 阶段出口

- HSM/Cloud KMS Adapter 至少在受控测试或 Provider sandbox 中完成协议、算法、不可导出、故障和对账验证；真实或 production-equivalent 证据由 P21 Level 2 Gate 强制要求。缺少该证据时相应高保障 Provider 和 Level 2/3 资源保持 disabled。
- HYOK Adapter 至少在受控客户模拟域或 Provider sandbox 中完成客户控制、撤销、故障和对账验证；真实客户控制或 production-equivalent 证据由 P21 Level 3 Gate 强制要求。缺少该证据时 HYOK 和 Level 3 资源保持 disabled。
- 对当前 assurance lane 未启用的 Provider-specific 工作包，只能在合同、Feature Gate、稳定错误、重新进入条件和被阻塞等级均已记录后标记 `DEFERRED`；这允许较低等级进入共享 Production Assurance，但不能把 P16 整体标记为完整产品 `VERIFIED / F3`。
- 内部与外部 Tenant 使用同一安全模型。
- 配额和计量不泄露 Secret 内容或跨租户拓扑。
- 控制面运营数据与 Vault Actual State 可对账。

### 回滚与停止条件

- 任何商业管理员默认获得 Tenant Secret 访问权时停止。
- 计量丢失不得回写或篡改安全审计事实。
- 未具备 HSM/KMS/HYOK 真实门禁证据时，不得以 sandbox、模拟 Provider 或合同测试宣传 Level 2/3 已生产就绪。

### 关联长期决策

ADR-006、ADR-008、ADR-019、ADR-021—ADR-024、ADR-054—ADR-057、ADR-065—ADR-067。

---

## P17 Strong Audit 外部锚定、可信时间证明、可观测性与安全告警

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P03/P04/P06；当前 assurance lane 启用 backend 外部通知或客户证明时追加 P10/P16**

### 目标

在 P04 本地 Strong Audit 与安全时间底座之上，为当前 assurance lane 已启用的资源完成外部不可变锚定、审计验证与签名密钥轮换、外部可信时间证明与多源仲裁、稳定脱敏观测和安全风险信号。分布式 Leader 接管与 Replica 审计连续性属于 P18，P17 不提前实现第二套协调路径，也不允许重新定义前序资源的审计或 TTL 语义；后续启用新的高级资源时必须增量补齐其 Audit Coverage 和风险信号再进入相应 Level Gate。

### 工作包

#### P17-W01 Audit Coverage 与 Schema Hardening

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

核对所有 Command、Policy、Capability、Key、Secret、Lease、Certificate、Provider、Recovery、拒绝和高风险允许事件的强审计覆盖，强化版本、禁止字段和租户证明 Schema。

#### P17-W02 Audit Chain Verification 与签名密钥轮换

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

在本地链基础上实现独立验证器、signature key generation 轮换、旧链尾与新签名 generation 连续性、checkpoint 验证和异常新链检测；Leader/Replica 接管由 P18 使用同一合同完成，不伪造跨 Shard 全局总序。

#### P17-W03 External Anchor

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现 WORM/SIEM/audit sink adapter、signed checkpoint、ack、retry、有限 unanchored window 和 tenant proof。

#### P17-W04 Reliable Audit Buffer Hardening

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

验证并强化有界、不可静默丢弃、backpressure、重启恢复和高风险操作 fail-closed；外部 sink 故障不能破坏本地链。

#### P17-W05 External Trusted Time Proof 与仲裁

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

接入 NTS/HSM/TPM/云 Provider/时间戳或审计域时间证明，定义来源能力、偏差界限、冲突仲裁、降级和恢复审计；不得选择最有利于继续服务的时间。

#### P17-W06 Observability

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现安全指标、trace、health、diagnostic 和高基数/敏感标识限制。

#### P17-W07 Security Risk Signal

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

从 Vault 权威事实建立 Security Risk Signal 权威状态，包含稳定代码、severity、Tenant/Resource scope、关联 Event/Operation、first/last seen、dedup 和 disposition；backend 只负责 Projection、展示与通知。告警 acknowledge/suppress/close 不等于修复底层 EXTERNAL_STATE_UNKNOWN、TIME_UNTRUSTED、审计或撤销失败状态，也不反向改变安全状态。

#### P17-W08 Tamper、Time 与 Leak 测试

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖链截断、重排、DB 回滚、异常 key rotation、新链伪造、sink 中断、buffer 满、time proof 冲突、clock rollback、snapshot 和自由文本泄露。

### 持续冻结边界

- 审计合同只保证每个 Shard 内严格顺序，不伪造跨 Shard 全局总序；P17 可在单节点 Shard 上完成，分布式接管证据由 P18 验证。
- 审计不保存 Secret、Key、完整 credential、可重放 token 或 Provider 主凭证。
- 任何审批、管理员或 Break-glass 都不能关闭 Strong Audit。
- P17 只强化 P04 已建立的审计与时间权威，不允许后置功能改变前序资源的既有安全语义。

### 阶段出口

- 审计链、签名密钥轮换、checkpoint 与外部锚点能够独立验证。
- 外部时间证明异常不会复活已过期/已消费对象。
- 所有日志、指标、错误、诊断通过敏感信息门禁。

### 回滚与停止条件

- 无法写本地强审计时高风险 Action 必须拒绝。
- 时间源冲突不得选择最有利于继续服务的结果。
- 外部锚定或可信时间适配失败时必须按资源保障等级降级或拒绝，不能削弱 P04 本地门禁。

### 关联长期决策

ADR-049—ADR-051、ADR-066。

---

## P18 Shard 单写、Authority Worker、epoch/fencing 与区域内 HA

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F3`**

**前置阶段：P03/P04/P06/P17**

### 目标

将 P03 的 SingleWriter Authority 合同扩展为 Tenant Key Domain 分片路由、单 Leader、replica、authority_epoch/fencing、受控 Worker 和区域内自动故障转移；不得改变 Key、Secret、Lease、Certificate 等资源模块的写入接口。

### 工作包

#### P18-W01 Shard Ownership/Router

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立唯一 shard ownership、Tenant Key Domain 路由、home region 和迁移状态。

#### P18-W02 Leader Election 与 Fencing

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

选择具体协调实现，把 P03 单节点唯一 owner 升级为分布式 Leader；绑定 authority_epoch/resource generation，旧 Leader 失效后不能写或调用 Provider。

#### P18-W03 Authority Replica Recovery

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

恢复 Actual State、audit tail、time lower bound、pending operations 和 cache invalidation。

#### P18-W04 Authority Worker

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

按 action risk 签发短期 worker capability，绑定 shard/epoch/domain/resource/generation/ops/budget。

#### P18-W05 Operation Classification

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

public verify、parallel controlled crypto、leader-only state-sensitive 三类形成 registry 和 Guardrail override。

#### P18-W06 Provider Fencing Adapter

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

原生支持则传 token；不支持则通过 Leader 串行 executor、operation record 和 reconciliation。

#### P18-W07 Outage/Degraded Mode Matrix

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

实现并验证按 Resource Assurance 与 Guardrail 裁决的 outage mode、max offline duration、cache/renewal/audit requirement，以及 ns_backend、SSO/IAM/IdP、Vault API、Authority、DB、Provider、Audit Sink、Time Source、State Store 和网络分区的稳定风险状态。默认 fail-closed；已可本地验证的短期身份/Capability 可按策略在 backend/IdP 暂时不可用时继续到原到期点，但有限继续服务不得创建新 Capability、读取新资源、轮换、续 Lease 或延长有效期，禁止隐藏 fallback Secret/Key/Provider。

#### P18-W08 HA/Fault Tests

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 split-brain、network partition、stale cache、old worker、leader crash before/after Provider call、replica lag 和 audit handoff。

### 持续冻结边界

- 同一 Key Domain 不允许两个写 Authority。
- Shard 故障时优先拒绝写入，不以双 Leader 换可用性。
- Worker 不拥有 Authority DB 写权限或 Tenant Root。

### 阶段出口

- 区域内 Leader 故障可在保守恢复流程后接管。
- 旧 Leader/Worker/Capability/Provider session 被 fencing。
- 并发和故障注入达到 F3。

### 回滚与停止条件

- 不能证明旧权威已失效时禁止新 Leader 开写。
- Provider 不支持 fencing 且无法可靠串行/对账时，相关高风险能力必须禁用。

### 关联长期决策

ADR-052、ADR-053、ADR-054。

---

## P19 备份、anti-rollback、多区域热备与分级灾备

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F4`**

**前置阶段：P08/P09/P18；当前 assurance lane 启用 Transit、PKI、Dynamic Credential、HSM/KMS/HYOK 时追加 P13/P14/P15/P16**

### 目标

实现加密备份、独立保护密钥、恢复证明、Provider 分级恢复、每 Key Domain 单 Home Region 的多区域热备和受控灾备接管。阶段先覆盖当前 assurance lane 已启用的资源；任何后续启用的 Transit、PKI、Dynamic Credential、HSM/KMS/HYOK 能力必须在相应 Level Gate 前补齐专项备份、恢复和灾备证据。

### 工作包

#### P19-W01 Backup Format/Protection

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

备份仅含密文、wrapped material、metadata、schema/epoch/generation/audit reference；建立独立 Backup Protection Key/Provider 的生成、托管、轮换、恢复、销毁和职责分离生命周期，并禁止与业务 Key、Capability 或审计签名 Key 复用。

#### P19-W02 Anti-rollback

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

绑定最后可信 audit anchor、root/authority epoch、destroy tombstone 和 provider state，拒绝恢复旧历史。

#### P19-W03 Standby Replication

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

复制 Authority metadata、ciphertext、event/audit、pending operation 和必要 provider reference；不复制明文 cache/session。

#### P19-W04 Tiered Recovery

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

按当前启用范围分别验证 Software Key/Secret、Lease、Audit，以及已启用的 Transit、HSM/KMS、HYOK、CA、Dynamic Credential；不把 DB restore 等同服务恢复，未启用资源不能以“未覆盖”状态进入对应生产等级。

#### P19-W05 Region Failover

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

验证旧 Region fencing、提升 root/authority/provider session epoch、cache 清空、Capability 失效和 audit chain continuity。

#### P19-W06 Normal Region/Shard Migration

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

状态追平、ownership transfer、epoch、old authority fencing、provider locality 和 cutover。

#### P19-W07 DR Drill

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

对目标 assurance lane 执行真实备份、恢复、Provider unknown、Lease rebuild 和流量启用门禁；启用 HYOK 或 PKI 时必须追加 HYOK unavailable、CA/CRL continuity 等专项场景。验证有界复制滞后与分钟级受控接管这一架构目标类别，具体 RPO/RTO 只记录实测值。

### 持续冻结边界

- 每 Tenant Key Domain 始终只有一个 Home Region 写权威。
- HYOK 恢复失败时不创建隐藏替代 Key。
- 已销毁资源不能由任何旧备份恢复解密能力。

### 阶段出口

- 每个准备进入生产的 assurance lane 至少完成一次覆盖其全部启用资源的 DR 演练，达到计划的有界 RPO/RTO 类别，并记录实测值而非设计目标。
- 所有资源按 BACKUP_AVAILABLE→METADATA_RESTORED→PROVIDER_VERIFIED→AUTHORITY_RESTORED→TRAFFIC_ENABLED 迁移。
- 外部审计锚可验证接管连续性。

### 回滚与停止条件

- Provider、Audit、Time 或 Fencing 任一关键验证失败时不得启用流量。
- 恢复尝试不能覆盖原备份或销毁证据。

### 关联长期决策

ADR-054—ADR-056、ADR-058。

---

## P20 容量模型、Benchmark 与性能验收

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F4`**

**前置阶段：P07-P12/P17-P19；当前 assurance lane 启用高级能力时追加 P13-P16**

### 目标

按 assurance lane 验证分片、Key/Secret/Version/Lease、Audit、backend Projection，以及该 lane 实际启用的 Transit、PKI、Dynamic Credential、HSM/KMS/HYOK Provider 的容量与性能边界；设计目标与实测结果严格分离，未启用能力不得用模拟结果冒充生产容量证据。

### 工作包

#### P20-W01 Capacity Profile

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

定义 Small/Medium/Large/Enterprise 或等价部署等级，并为每个 assurance lane 声明启用资源集合、资源数量级、并发、审计、Provider 和 HA/DR 要求。

#### P20-W02 Benchmark Harness

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

建立可重复的环境、数据生成、Provider stub/真实 Provider、敏感数据安全和结果元数据。

#### P20-W03 Data Plane Benchmark

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

测 Secret、Transit、sign/MAC、Capability verify、DEK cache on/off、Provider latency 和 p95/p99。

#### P20-W04 Control/State Benchmark

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

测 command、policy、projection、reconciliation、version activation、Lease renew/revoke、audit chain 和 scheduler。

#### P20-W05 Failure/Backpressure Benchmark

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

测 audit sink down、Provider rate limit、DB slow、replica lag、worker loss、cache miss 和 quota。

#### P20-W06 Scaling Validation

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

验证 Shard 扩展、热点 tenant、dedicated shard、region latency 和容量迁移。

### 持续冻结边界

- 不得为性能跳过授权、审计、generation、epoch、Provider 对账或明文边界。
- 测试数字只进入 acceptance log，不写成未验证 SLA。

### 阶段出口

- 目标容量等级均有真实环境和配置说明。
- 已识别瓶颈、Provider 限制、资源成本和扩展路径。
- 无安全语义回退的性能基线通过。

### 回滚与停止条件

- 发现性能目标只能通过弱化安全边界达到时，停止并重新评估产品目标，不允许静默优化。

### 关联长期决策

ADR-052—ADR-054、ADR-066、ADR-067。

---

## P21 安全强化与分级生产门禁

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F4`**

**前置阶段：P17-P20 的共享保障底座，以及目标 Level 明确列出的资源/Provider 工作包**

### 目标

按 Level 1/2/3 对资源和部署执行安全审查、渗透、故障、DR、Provider、审批、运维和 supply-chain 门禁。

### 工作包

#### P21-W01 Threat Model Review

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

逐条验证 backend/issuer/host/DB/API/Provider/Agent/Worker/insider/region 失陷边界。

#### P21-W02 Security Test Suite

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

跨租户、权限、replay、nonce、format、schema、IPC、audit tamper、backup rollback、secret leakage 和 fuzz。

#### P21-W03 Supply Chain

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

锁定依赖、构建、SBOM、Provider manifest signing、artifact provenance、漏洞扫描和升级策略。

#### P21-W04 Level 1 Gate

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

软件 Provider 基础内部资源：要求 P07-P12、P17-P20 已按 Level 1 启用范围达到相应出口，核心授权、审计、生命周期、备份恢复、HA/DR、容量和故障语义具备真实证据；P13-P16 中未启用的高级能力必须显式 disabled/DEFERRED。

#### P21-W05 Level 2 Gate

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

生产敏感资源：在 Level 1 Gate 基础上，要求目标资源涉及的 P13-P15 能力、P16-W01 HSM/KMS Adapter，以及对应 P17-P20 审计、HA/DR、容量证据完成；必须使用真实或 production-equivalent HSM/KMS 或经验证等价保障，完成 rotation、故障和 Provider 恢复验证。

#### P21-W06 Level 3 Gate

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

高保障资源：在 Level 2 Gate 基础上，要求 P16-W02 HYOK/客户控制路径及目标高级资源全部完成真实或 production-equivalent 证明，并具备双人控制、门限恢复、完整 DR 演练、安全评审和 Provider 证明；不允许未缓解 high 风险。

#### P21-W07 Operational Readiness

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

密钥仪式、恢复 custodian、on-call、incident、backup、audit verification、provider quarantine 和 break-glass drill。

### 持续冻结边界

- 低等级 Provider 不得承载高等级资源。
- 门禁按资源和部署保障等级裁决，不使用单一全局“已上线”标签。
- 外部审计/认证可作为证据，但不能替代内部技术门禁。
- Level 1/2/3 Gate 的状态必须分别维护；通过较低等级后，P21 阶段只能记录对应 scope 的 `VERIFIED / F4`，不得把尚未通过的更高等级合并为阶段完成。

### 阶段出口

- 每个准备启用的等级分别具有完整、真实、可追溯证据；Level 1 通过不暗示 Level 2/3 通过。
- 未达门禁的 Action/Resource/Provider 保持 disabled；高等级 Gate 保持 `BLOCKED` 或显式 `DEFERRED` 不阻止已经通过的较低等级进入其独立发布通道。
- 安全审查不存在未缓解的 critical 风险。任何违反设计清单、ACCEPTED ADR、全局安全不变量、租户隔离、Root/Key 不可导出、Strong Audit、销毁不可复活或单写 Authority 的 high 风险不得通过风险接受上线；Level 3 不得存在未缓解 high。其他 high 仅可在对应较低保障等级通过正式风险接受流程记录补偿控制、责任人、期限和自动失效。

### 回滚与停止条件

- 任何关键门禁未通过时不得标记 PRODUCTION_READY。
- 不能通过文档声明、模拟 Provider 或测试 root 代替生产证据。

### 关联长期决策

ADR-019、ADR-049—ADR-057、ADR-065、ADR-068。

---

## P22 发布、运维交接与持续兼容治理

**阶段状态：`BLOCKED / F0`**

**目标完成度：`F4`**

**前置阶段：P21 中至少一个明确目标 Level Gate 已达到 `VERIFIED / F4`；发布更高等级时必须等待对应 Gate**

### 目标

针对已经通过 P21 门禁的目标 assurance lane，完成发布制品、升级/回滚、Schema/Provider/SDK 兼容、运行手册、治理文档更新和持续验收流程。未通过更高等级门禁的能力必须在制品、配置、文档和营销声明中保持 disabled，不阻止较低等级独立发布。

### 工作包

#### P22-W01 Release Artifact

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

按 `release_id + assurance_level` 生成与目标 assurance lane 对应的可验证服务、Provider Host、Agent、SDK 和 Migration 制品及 provenance；制品必须携带启用能力/Provider/保障等级清单和 fail-closed Feature Gate。该工作包可为后续更高等级或新版本重复执行，每次证据单独进入 acceptance log。

#### P22-W02 Upgrade/Rollback

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

验证滚动升级、Schema N/N-1、Provider protocol/Host 灰度与回滚、升级中未完成 Provider operation 的恢复、Key/Secret format、Shard/region migration，以及可逆回滚或经过验证的 forward-recovery；不得强迫已经发生的密码学销毁或不可逆安全迁移反向恢复。

#### P22-W03 Operational Runbook

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

覆盖 seal/unseal、leader failover、Provider unknown、audit sink、time degraded、backup/restore、break-glass 和 destroy。

#### P22-W04 Compatibility Governance

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

维护 Schema Registry、deprecation、migration、SDK matrix、external customer notice 和弱算法淘汰。

#### P22-W05 Documentation Closure

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

设计清单只在产品边界变化时更新；ADR 用新增/替代记录；实施计划保持当前游标；acceptance log 追加真实证据。

#### P22-W06 Release Gate

状态：`BLOCKED / F0`。前置阶段或同阶段前序工作包尚未完成。

按 `release_id + assurance_level` 确认目标保障等级对应的 CI、签名、SBOM、测试、DR、监控、回滚和已启用能力清单全部具备证据；不得用较低等级证据发布较高等级资源。后续等级或版本必须重新执行，不能继承旧 release 的通过状态。

### 持续冻结边界

- 发布和回滚不能恢复已销毁密钥、旧安全 epoch 或已弃用弱 Schema 的新创建能力。
- 兼容不等于永久支持弱安全语义。
- P22 是可重复的分级发布通道，不是一次性永久完成状态；Implementation Plan 保存当前目标 release/lane，历史发布证据保存在 acceptance log。

### 阶段出口

- 每个已发布 assurance lane 具有独立、完整的 release/rollback/operations/compatibility 证据和版本化能力清单。
- 当前目标 lane 的所有必需工作包状态与 acceptance log 对齐；更高等级未完成工作包继续保留，不得因较低等级发布而标记完成。
- 当前生产门禁、disabled capability、未验证项和可升级路径清晰可见。

### 回滚与停止条件

- 任一制品不可验证，或 Migration 缺少经过验证的安全回滚/forward-recovery 路径，或安全状态无法恢复时停止发布。

### 关联长期决策

ADR-063、ADR-068、ADR-069。

---

## 6. 当前执行入口

当前唯一执行入口保持为：

```text
P00-W05：本地工作区实现事实盘点与基线校准
```

开始该工作包前必须获得用户明确授权。执行时应首先输出并记录：

1. 当前本地分支、HEAD、工作树状态；
2. 四份 `ns_vault` 治理文档的实际路径和内容摘要；
3. `src/ns_vault`、`src/ns_backend/vault`、`ns_common`、`ns_runtime` 相关现状；
4. 当前依赖、Python 版本、测试框架、CI 和数据库/Provider 可用环境；
5. 设计与现有代码的 drift；
6. P01 可安全开始的最小修改范围。

未完成 P00-W05 和 P00-W06 前，不得把 P01 标记为 `IN_PROGRESS`。

## 7. 计划维护规则

- 本计划只保留当前状态、冻结接口、阶段出口、阻塞和下一游标；历史命令与详细通过数量进入 acceptance log。
- 工作包状态变化必须有 acceptance log 证据引用。
- 新增工作包必须放入正确阶段，并说明前置依赖、是否改变 ADR、是否影响当前游标。
- Assurance lane、目标 Level 或 release_id 变化时，必须重新计算必需工作包、`DEFERRED` 能力、P21 Gate 和 P22 Release Gate；不得沿用另一等级或旧 release 的 `VERIFIED/F4`。
- 若实施中发现设计边界缺失，先暂停当前工作包并回到设计/ADR 决策，不允许由 Code Agent 自行补全长期语义。
- 当前不存在迁移资产不是永久架构限制；未来发现真实资产时，应新增显式 migration work package，并记录 owner、source、cutover、rollback 和 retirement。
