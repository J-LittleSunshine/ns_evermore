# ns_vault 历史验收日志

> 文档版本：`0.0.1`
>
> 当前状态与执行入口：[ns_vault_implementation_plan_for_design_0.0.1.md](ns_vault_implementation_plan_for_design_0.0.1.md)
>
> 长期架构决策：[ns_vault_architecture_decisions_0.0.1.md](ns_vault_architecture_decisions_0.0.1.md)
>
> 设计边界：[ns_vault_design_checklist_0.0.1.md](ns_vault_design_checklist_0.0.1.md)

本文件按发生时间升序追加已经完成的设计、实施、测试、审查和生产门禁证据。它不是当前执行游标，也不能覆盖设计清单、ADR 或实施计划中的当前状态。

记录规则：

- 只记录真实发生的事实、命令、结果、环境和限制。
- 未运行的测试、未连接的 Provider、未执行的 DR、未存在的 Migration 和未发生的提交不得写成已通过。
- 历史记录不得因后续失败而删除；应追加新的校准或作废说明。
- 敏感值不得进入本文件。只允许记录脱敏 endpoint、环境变量名、受限文件引用、不可逆摘要和稳定错误码。
- 每个记录必须明确 local-only、remote CI、production-equivalent 或真实生产证据的范围。
- 当前状态只在 implementation plan 中更新；本日志中的“状态”只能表示记录发生时的历史快照。
- 同一日期存在多条记录时，按本文档出现顺序视为发生顺序；需要精确排序的后续实施记录应写入带时区时间。

---

## 2026-07-31 仓库与治理文档只读预检

### 预检范围

- 仓库：`J-LittleSunshine/ns_evermore`。
- GitHub 只读预检基线：默认分支 `main`，当时解析到的远程 commit 为 `73df738eb2e31fb874f9403488d12af78b2a2f14`；该 SHA 只界定本次远程预检，不代表用户实施时本地工作区 HEAD。
- 只读检查了以下 `ns_runtime` 治理文档，用于继承文档权威、状态和验收分工：
  - `docs/ns_runtime_design_checklist_0.0.2.md`；
  - `docs/ns_runtime_architecture_decisions_0.0.2.md`；
  - `docs/ns_runtime_implementation_plan_for_design_0.0.2.md`；
  - `docs/ns_runtime_acceptance_log_0.0.2.md`。
- 只读检查了与 `ns_vault` 边界相关的现有代码事实，范围包括：
  - `src/ns_backend` 的 settings、app loader、URL、ASGI、数据库路由、IAM models/services/repositories/views；
  - `ns_common` 的 config、security、exceptions、HTTP client、typed IDs、Clock、StateStore；
  - `ns_runtime` 的 Authority Broker、Authority Attestor、bootstrap、composition、IAM proxy、credential cache 和启动安全边界；
  - 当前 Python、Django/DRF/ADRF、cryptography、httpx、Redis/Valkey 等依赖与现有测试/CI 结构。

### 已确认事实

- 设计清单是最终产品、安全和功能边界权威。
- ADR 记录长期决策；工作包不得自行补全未冻结语义。
- Implementation plan 是唯一当前状态和执行游标。
- Acceptance log 只保存历史证据。
- `src/ns_backend/vault` 固定为 Django 控制面应用；`src/ns_vault` 设计为独立安全服务。
- 现有 backend 全局 DRF 默认认证/权限配置不能被直接继承为 Vault 数据面安全策略。
- 现有配置中存在多类秘密字段，但用户明确确认当前没有需要纳入本次 `ns_vault` 实施计划的真实迁移资产；未创建假设性迁移清单。
- `ns_common.security.AesGcmSecretBox` 只提供小型内存秘密的 AES-GCM 原语，不定义 Vault 存储、IAM 或完整生命周期。
- `ns_runtime` 已有生产 Authority Broker/Attestor、根信任、受限 IPC、FD bootstrap、显式依赖和普通进程不持有根能力的边界；`ns_vault` 必须兼容且不得弱化这些边界。

### 操作事实

- 本次预检未修改代码、文档、配置、依赖、Migration 或测试。
- 未创建或切换分支。
- 未提交、推送或创建 Pull Request。
- 未运行 `ns_vault` 实现测试，因为实现尚未开始。

---

## 2026-07-31 ns_vault 逐项架构决策冻结

### 决策过程

- 采用逐问逐答方式冻结产品范围、安全边界、资源模型、身份、授权、Key、Secret、Transit、PKI、Lease、Provider、Agent、组件集成、HA/DR、审计、存储、框架、兼容和生产门禁。
- 最终形成 `ADR-001` 至 `ADR-069`，全部状态为 `ACCEPTED`。
- 后续存在独立 SSO 服务；本设计只冻结 Vault 所需的 issuer、Identity Assertion、Principal Binding、audience、assurance、MFA/session validity 和 revocation 兼容边界，不展开 SSO 内部产品设计。

### 关键冻结事实

- `ns_vault` 是完整企业 KMS、Secrets、Transit、PKI、Dynamic Credential、Lease、Workload Identity、Provider、BYOK/HYOK 和 Tokenization 平台。
- `ns_backend` 是统一控制面，但不是 Vault 数据面最终授权权威。
- 每租户拥有独立 Tenant Key Domain；资源层级固定为 Tenant/Project/Namespace/Resource。
- 身份采用 federation + Vault Principal Binding；SSO/IAM role/group 不直接成为 Vault Grant。
- 策略采用 Mandatory Guardrail + Delegable Grant；执行使用 Vault 签发的短期 Scoped Capability。
- Secret 明文不经过普通 backend；默认使用非明文交付，人工读取是高风险操作。
- Key、Secret、Lease、Certificate、Provider Operation 和删除/销毁均使用显式状态机和 generation/epoch/idempotency。
- Provider 运行于隔离 Host；外部副作用必须先持久化 PREPARE 并对账。
- 每 Key Domain 单写 Authority、单 Home Region，多区域只做热备接管，不做主动-主动双写。
- Strong Audit 使用 Shard 密码学链和外部不可变锚定。
- `src/ns_vault` 选择 Python FastAPI/ASGI；`src/ns_backend/vault` 保持 Django 控制面。
- Software Provider 可在生产使用，但只能声明 software assurance；生产门禁按资源保障等级分层。

### 边界检查

- 已确认 `ns_node` 是独立 Node Principal，只能代表自身访问 node-scoped Secret，不能代表承载 workload。
- 已确认 `ns_runtime` 通过 Authority Broker 完成身份和 Capability Exchange，数据面按策略直连 Vault；Broker 不签发 Vault Capability、不代理 Secret 明文。
- 已确认 Agent 是正式但可选的交付组件，不是 Authority，也不是 `ns_node`。
- 已确认未来 SSO 只提供身份事实，不负责 Vault Resource Permission。
- 已确认公共设施优先复用，但 Vault 权威状态不能进入普通 cache、backend ORM 或 runtime 私有状态。

---

## 2026-07-31 设计清单与 ADR 文档生成和最终一致性审查

### 生成文件

- `docs/ns_vault_design_checklist_0.0.1.md`。
- `docs/ns_vault_architecture_decisions_0.0.1.md`。

### 最终结构事实

- 设计清单最终本地制品为 994 行，包含 23 个顶层章节，覆盖产品范围、非目标、安全、公共设施、SaaS/资源层级、身份、授权、控制面、Root/Seal、Provider、Key、Secret、Transit、PKI、Lease、Agent/Client、审计/时间、HA/DR、故障、销毁、存储/进程/框架/合同、配额/容量/生产门禁和最终核对。
- ADR 文档最终本地制品为 865 行。
- ADR 数量为 69，编号从 `ADR-001` 到 `ADR-069` 连续，状态全部为 `ACCEPTED`。
- ADR 索引、正文标题和锚点完成机械一致性检查。
- 未发现重复 ADR 标题、缺失必需字段、无效设计章节引用或未闭合 Markdown code fence。

### 最终语义复核补充

最终双向检查补充或澄清了：

- 状态统计、安全告警和组件接入属于控制面/安全运营能力，但不能成为旁路权威。
- `ns_frontend` 不能继承终端用户 Vault 权限；Secret 使用 Vault 认可的一次性直连会话。
- 旧 CA 在仍有有效证书时可以处于 `REVOCATION_STATUS_ONLY`，但不能继续签发普通证书。
- CA 在 CRL/OCSP 义务和有效证书依赖未清零前不得销毁。
- Break-glass 门限证据只替代预定义紧急恢复动作的普通安全审批，不是通用授权旁路。
- 低熵 Secret、业务输入和派生 Context 不记录普通明文 hash。
- Agent 只能接收 Vault 已按字段 Capability 裁剪后的字段。
- Provider 直交付只允许受控 `provider_direct_nonrecoverable` 例外，不形成普通客户端 Provider 主能力。
- Root/Seal 明文解封结果不能进入通用 Provider Host。
- Provider 外部副作用在调用前必须持久化 PREPARE operation record。
- Strong Audit 与权威状态提交之间必须有事务 outbox 或等价可恢复关联。
- Transit 的 signature、MAC 和 wrapping 结果也使用版本化 Canonical CryptoResult 或受控 detached metadata。

### 验收范围

- 本记录只证明设计文档与 ADR 的结构和语义一致性。
- 不证明任何 `ns_vault` 生产代码、API、数据库、Migration、Provider、密码学操作、HA/DR、性能或生产门禁已经实现。
- 本次文档生成没有运行实现测试，没有真实 HSM/KMS/HYOK/CA/数据库/多区域证据。
- 本会话没有执行 Git commit、push 或 PR；用户在其本地工作区进行的文件放置或提交不属于本会话可验证事实。

---

## 2026-07-31 实施计划与验收日志基线

### 生成文件

- `docs/ns_vault_implementation_plan_for_design_0.0.1.md`。
- `docs/ns_vault_acceptance_log_0.0.1.md`。

### 记录时状态快照

> 以下只表示该记录生成时的历史快照；当前状态以 implementation plan 为准。

- 整体 `ns_vault` 实现状态：`NOT_STARTED / F0`。
- 治理文档状态：`VERIFIED / F1 (document-only)`。
- 当前阶段：`P00 治理基线与本地事实校准`。
- 当前唯一执行游标：`P00-W05 本地工作区实现事实盘点与基线校准`。
- 当前游标状态：`BLOCKED / F0`，等待用户明确授权开始实现并读取实施时本地工作区。

### 明确未完成

- 未创建 `src/ns_vault` FastAPI 服务骨架。
- 未创建 `src/ns_backend/vault` 控制面实现或 Migration。
- 未选择具体 Authority DB、Event Store、State Store、Object Storage、选主或 Provider 技术。
- 未新增 Python 依赖。
- 未实现 Canonical Contract、Policy、Capability、Key、Secret、Lease、PKI、Dynamic Credential、Provider Host、Agent 或 SDK。
- 未运行任何实现、集成、并发、故障、安全、恢复、性能或生产门禁测试。

---

## 2026-07-31 实施计划与验收日志深度复核校准

> 校准时间：`2026-07-31T13:07:00+08:00`

### 复核范围

- 对 `ns_vault_implementation_plan_for_design_0.0.1.md` 执行了阶段、工作包、状态、前置依赖、ADR 承接、当前游标和 Markdown 结构检查。
- 对本验收日志执行了事实范围、历史快照措辞、自相矛盾和未发生事实检查。
- 本轮只修订实施治理文档，没有修改 `src/`、配置、依赖、Migration 或测试。

### 发现并修正的实施顺序问题

- 原计划将完整 Strong Audit 和可信时间放在 `P16`，但 `P04`—`P15` 已包含 Root、Provider、Policy、Key、Secret、Lease、PKI 和动态凭证等安全副作用。现将本地 Strong Audit Authority、事务 outbox 消费、签名链、fail-closed 审计门禁和不可回退安全时间底座前移到 `P04`。
- `P16` 现只负责外部不可变锚定、审计验证与签名密钥轮换、外部可信时间证明、多源仲裁、可观测性和安全告警，不重新定义前序资源的审计或 TTL 语义。
- 原计划在 `P08`—`P13` 要求 Shard Leader 裁决 Key promotion、Lease、证书 serial 和凭证池，但分布式 Shard/Leader 到 `P17` 才实现。现于 `P03` 建立稳定的 `SingleWriter Authority` 合同、单节点唯一 owner、authority epoch 和 fencing assertion；后续资源从首日起只使用该接口，`P17` 仅扩展为分片、选主、Replica、Worker 和区域内 HA。
- `P16` 不再提前实现尚未存在的分布式 Leader handoff；Replica audit tail、time lower bound 和 audit handoff 由 `P17` 统一验证。

### 发现并修正的状态与依赖问题

- 原计划 164 个工作包中，P01—P22 的 158 个没有显式状态。修订后共有 169 个工作包，每个均具有状态和 F 等级。
- 当前 4 个治理工作包为 `VERIFIED / F1 (document-only)`；其余 165 个工作包均为 `BLOCKED / F0`。
- `P00` 阶段由 `IN_PROGRESS / F1` 校准为 `BLOCKED / F1`，因为当前游标 `P00-W05` 尚未获得实施授权；`P00-W06` 同样由 `NOT_STARTED` 校准为受 W05 阻塞。
- 增加规则：阶段默认按 `P00 → P22` 推进，同阶段工作包默认按编号顺序推进；前置阶段只是最低依赖，不构成跳过中间阶段的授权。
- 修正关键前置依赖：
  - `P05` 依赖 `P04` 的本地审计和安全时间底座；
  - `P18` 必须等待 PKI、动态凭证和区域内 HA；
  - `P19` 复用 `P14` 客户端能力；
  - `P20` 必须等待 `P09`—`P19` 的实际能力；
  - `P21` 生产门禁覆盖 `P08`—`P20`，不再遗漏 Key、Secret、Transit 和 Lease。

### 发现并修正的功能承接问题

- 在 `P02` 增加 REST、gRPC 和内部认证 IPC adapter 骨架及协议一致性测试，避免设计中已冻结的数据面 gRPC 只停留在合同描述。
- 在 `P14` 增加官方 CLI 工作包，明确 Secret、私钥和动态凭证默认不得进入终端历史或普通 stdout。
- 外部客户客户端治理改为复用 `P14` 的 `ns_client`/CLI，不建设第二套 SDK。
- 补齐固定 Django App Key `vault`、ResourceRef 敏感拓扑与 `CURRENT` 解析约束、长期凭证仅用于 bootstrap/恢复、Capability 禁止携带敏感材料、DEK 缓存不得延长 Provider 故障窗口、证书私钥一次性交付、同 Host 多 `ns_node` 隔离和分钟级受控区域接管目标。
- 发布阶段将“所有 Migration 必须机械可回滚”修正为“必须具备经过验证的安全回滚或 forward-recovery 路径”，避免要求已完成的密码学销毁或不可逆安全迁移反向恢复。
- 生产安全门禁明确：不得存在未缓解的 critical 风险；high 风险必须修复或通过正式风险接受流程记录补偿控制、责任人和期限。

### 机械校验结果

- 实施阶段：23 个，`P00`—`P22` 连续。
- 工作包：169 个；编号在各阶段内连续，无重复。
- 缺失工作包状态：0。
- 阶段总览与阶段正文的名称、状态、目标完成度和前置依赖不一致：0。
- 阶段依赖环：0。
- 69 条 ADR 均至少被一个阶段的“关联长期决策”承接；无未知 ADR 引用。
- Markdown code fence 数量为偶数，未发现未闭合 fence。
- 当前唯一执行游标仍为 `P00-W05 本地工作区实现事实盘点与基线校准`，状态 `BLOCKED / F0`。

### 证据边界

- 本轮校验只证明两份治理文档的结构、状态和实施顺序得到修正。
- 未读取用户当前本地 Git 工作区，因此不证明治理文档已经提交、当前 HEAD 包含这些修订或 `src/ns_vault` 已存在。
- 未运行任何 `ns_vault` 生产实现测试、真实数据库、Provider、HSM/KMS/HYOK、HA/DR、性能或生产门禁测试。
- 未执行 commit、push 或 Pull Request。

---


## 2026-07-31 实施层顺序与执行可落地性最终校准

> 校准时间：`2026-07-31T13:27:00+08:00`

### 复核发现

- 继续按设计清单与 69 条 ADR 反向审查实施计划时，发现上一版虽然包含全部功能域，但阶段编号默认按 `P00 → P22` 执行时，没有严格遵守 `ADR-069` 已冻结的 `Foundation Layer → Core Security Layer → Platform Integration Layer → Advanced Security Layer → Production Assurance Layer`。
- 上一版中 Django 控制面位于 Key/Secret Core Security 之前，Advanced Transit 位于 Agent/组件 Platform Integration 之前；若按编号推进，会使平台现状或高级能力先于核心安全层塑造实现，与 ADR-069 的实施治理目标不一致。
- 还发现 Key Management 缺少 Tenant Key Domain/资源层级前置依赖，Agent/ns_client 核心阶段同时依赖尚未进入的 PKI 和 Dynamic Credential，完整故障/离线裁决没有独立实施工作包，Backup Protection Key 生命周期只写了使用而未写生成、轮换、恢复和销毁。
- `F4` 的原定义容易被误解为单个 DR 或性能阶段完成后整个 Vault 即可生产，需明确 F 等级按工作包/阶段作用域解释，而全产品 `PRODUCTION_READY` 只能由生产门禁与发布门禁共同授予。
- ADR-069 将 HYOK 列入 Advanced Security；上一版把可执行 HYOK Reference 放在 Core Key 阶段。现 Core 只保留不可变合同和 feature-disabled 引用，真实客户控制 Provider 集成移至 P16。
- 完整产品范围要求 HSM/Cloud KMS，但上一版只有通用 Provider Host 与生产门禁，没有明确的 Provider 实现工作包。现 P16 增加真实 HSM/Cloud KMS Adapter、能力验证和故障对账工作包。
- Strong Audit 和 Capability 在业务 Key Management 之前就必须可用，上一版缺少独立的内部 Authority Key 生命周期。现 P04 增加 Internal Authority Key Registry，明确 Root/Seal、Audit、Capability、Manifest、Session/Delegation 等用途分离且不通过普通 Tenant Key API 暴露。
- Tenant Key Domain 已冻结独立 KEK generation、渐进式 rewrap 和销毁门禁，但上一版 Key 阶段没有独立工作包。现 P07 增加 Tenant KEK Rotation/Rewrap 的队列、幂等、崩溃恢复和依赖证明。

### 实施层和阶段重排

当前计划已按以下顺序重新编号：

- Foundation Layer：`P00`—`P06`；
- Core Security Layer：`P07` Key、`P08` Secret、`P09` Lease；
- Platform Integration Layer：`P10` Django 控制面、`P11` Agent/ns_client 核心、`P12` 平台组件与 SSO 兼容；
- Advanced Security Layer：`P13` Transit/Derivation/Tokenization、`P14` PKI、`P15` Dynamic Credential、`P16` HSM/KMS/HYOK/外部客户/配额/计量；
- Production Assurance Layer：`P17` 外部审计锚定/可信时间/观测、`P18` Shard/HA、`P19` Backup/DR、`P20` Capacity、`P21` Production Gate、`P22` Release。

本次重排只修改实施顺序和工作包编号，不修改设计清单或 ADR 中的产品、安全和长期架构语义。

### 新增和补强的实施工作包

- `P13-W06`：在既有 ns_client/CLI 上扩展 Transit、Derivation、Random/Password 和 Tokenization，不创建第二套客户端协议。
- `P14-W08`：Agent/ns_client 证书私钥模式、CSR、证书交付、Lease 续期、轮换和吊销集成。
- `P15-W07`：Agent/ns_client 动态凭证临时密封交付、redelivery、续期和撤销集成。
- `P18-W07`：统一实现 Resource Assurance + Guardrail 驱动的 outage/degraded mode matrix，覆盖 ns_backend、SSO/IAM/IdP、Vault API、Authority、DB、Provider、Audit Sink、Time Source、State Store 和网络分区。
- `P04-W07`：建立内部 Authority Key Registry，解决 Audit/Capability/Manifest 等基础签名能力早于业务 Key Management 的依赖，并强制用途分离。
- `P07-W05`：实现 Tenant KEK generation、渐进式 DEK rewrap、进度恢复和销毁前依赖证明，默认不重新加密业务密文。
- `P16-W01`：实现真实 HSM/Cloud KMS Provider 适配，验证算法、不可导出属性、session/region、fencing、故障和对账，禁止软件静默降级。
- `P16-W02`：把 Core 阶段仅定义的禁用 HYOK 引用接入真实客户控制 Provider，验证无隐藏替代 Key、撤销、故障、对账和受控 Provider-direct Grant。
- `P19-W01`：补充独立 Backup Protection Key/Provider 的生成、托管、轮换、恢复、销毁和职责分离生命周期。
- 公共设施登记新增 `ns_common.async_runtime`，P01/P02 必须先评估并复用标准 asyncio、任务监督、有界关闭和资源 owner 原语。
- Core Key 阶段增加 Tenant Key Domain/资源层级依赖；Agent/ns_client 核心阶段不再提前依赖 PKI/Dynamic Credential，高级客户端能力由 P13—P15 后续扩展。
- Platform/Customer Account 在 Foundation 中只保留非权威 Ref/Mapping 合同；真实合同、SLA、Billing 和客户生命周期由 backend 控制面与 P16 外部服务治理管理，避免 Vault 复制客户目录或让 Account Ref 成为权限。
- 高级阶段的客户端扩展现先实现后执行该阶段完整互操作/安全测试，避免测试工作包早于 Agent/ns_client 集成。
- 补充 browser direct Grant、Django `AllowAny` 防继承、Delegation Capability、Key export 一次性交付、证书 Wildcard/DNS 所有权、Delivery DEK 销毁、Risk Signal 状态和 IdP/backend outage 语义。
- 为 Key/Secret/Lease/Certificate/Derivation/Dynamic Credential 工作包补入设计清单中的精确状态和枚举值，避免后续实现用近义名称、布尔状态或非规范输出策略造成合同漂移。
- 生产风险接受进一步收紧：违反设计/ADR/全局不变量、租户隔离、不可导出、Strong Audit、销毁不可复活或单写 Authority 的 high 风险不得通过风险接受上线，Level 3 不允许未缓解 high。
- `F4` 明确为作用域内生产保障等级；全产品 `PRODUCTION_READY` 只能由 P21 对应保障等级门禁和 P22 发布门禁共同授予。

### 校准后的机械事实

- 实施阶段仍为 23 个，`P00`—`P22` 连续，且阶段编号与五个实施层严格对齐。
- 工作包由上一版历史快照中的 169 个调整为 177 个；各阶段内编号连续，无重复。
- 每个工作包仍具有显式状态；4 个治理文档工作包为 `VERIFIED / F1 (document-only)`，其余 173 个为 `BLOCKED / F0`。
- 当前唯一执行游标未改变，仍为 `P00-W05 本地工作区实现事实盘点与基线校准`，状态 `BLOCKED / F0`。
- 阶段依赖无环；Key、Secret、Lease、Platform、Advanced、Production Assurance 的执行顺序与 ADR-069 一致。
- 本轮没有修改设计清单或 ADR，没有修改生产代码、配置、依赖、Migration 或测试，没有运行实现测试，也没有执行 commit、push 或 Pull Request。

### 证据边界

- 本记录证明当前两份实施治理文档的阶段层级、依赖和工作包承接得到再次校准。
- 本记录不证明用户本地 Git 工作区已经替换为本轮修订文件，也不证明任何 `ns_vault` 实现能力存在。
- 上一条深度复核记录中的“169 个工作包”保留为当时版本的历史事实；当前工作包数量以 implementation plan 最新状态为准。

---

## 2026-07-31 分级生产门禁与历史工作包编号追溯校准

> 校准时间：`2026-07-31T13:56:20+08:00`

### 复核发现

- 继续从 `ADR-068` 的分级生产启用边界反向检查实施计划时，发现上一版虽然存在 Level 1/2/3 Gate，但 P21/P22 的阶段前置仍要求全部 Advanced Security、HSM/KMS/HYOK、全部 DR 和 Benchmark 完成，实际会把分级门禁退化为“全平台一次性上线”。这与已冻结的“基础内部资源不必等待所有高保障 Provider 能力即可按自身门禁启用”不一致。
- P17、P19、P20 的前置条件也把外部客户、HYOK、PKI、Dynamic Credential 等全部高级能力设为共享 Production Assurance 的硬依赖，使 Software Provider 的 Level 1 路径无法独立完成审计锚定、HA/DR、容量和发布证据。
- P22 以整个 P21 阶段完成为前置，会使 Level 1 Gate 即使已经通过，也必须等待 Level 2/3 Gate 后才能发布，违背按 Resource/Provider Assurance 分级启用的产品语义。
- 历史验收记录保留了阶段重排前的 Pxx 工作包编号。由于 acceptance log 是历史证据而非当前执行游标，这些编号应保持原记录，但必须明确不能再作为当前工作包引用。

### 实施计划修正

- 增加 **assurance lane** 执行规则：Level 1、Level 2、Level 3 分别只要求各自启用资源和 Provider 的工作包达到对应门禁；不属于较低等级范围的高级能力只有在合同、稳定错误、fail-closed Feature Gate、阻塞等级和重入条件完整时才能显式 `DEFERRED`。
- `DEFERRED` 不得用于跳过 Root/Seal、身份、授权、Strong Audit、安全时间、SingleWriter Authority、租户隔离、删除/销毁，以及目标等级自身要求的 HA/DR 等公共不变量。
- P17 改为服务当前 assurance lane 已启用资源的共享外部审计、可信时间、观测和 Risk Signal；后续启用新的高级资源时必须增量补齐覆盖。
- P19 改为先完成当前 assurance lane 全部启用资源的备份、anti-rollback 和 DR，只有启用 Transit、PKI、Dynamic Credential、HSM/KMS/HYOK 时才追加对应资源阶段和专项演练。
- P20 改为按 assurance lane 建立容量 Profile 和 Benchmark；未启用能力不得用模拟结果冒充生产容量证据。
- P21 的 Level Gate 明确独立前置：
  - Level 1 要求 Core Security、Platform Integration 和共享 Production Assurance 对当前软件 Provider 范围完整通过；未启用高级能力保持 disabled。
  - Level 2 在 Level 1 基础上追加目标高级资源、真实或 production-equivalent HSM/KMS、专项 Rotation、HA/DR 和容量证据。
  - Level 3 在 Level 2 基础上追加 HYOK/客户控制、双人控制、门限恢复、完整 DR 和无未缓解 high 风险。
- P22 改为分级发布通道：任一目标 Level Gate 达到 `VERIFIED / F4` 后即可发布该等级的受限能力集合；更高等级仍保持 blocked/deferred，其 Action、Resource Class、Provider、配置和对外声明必须继续 disabled。
- P21/P22 的状态改为显式作用域状态，例如 `VERIFIED / F4 (Level 1 scope; Level 2/3 BLOCKED)`；P22 按 `release_id + assurance_level` 重复执行，每个新等级或新版本必须重新产生发布证据，不能继承旧 release 的通过状态。
- P08 Secret Type Registry 补入每类型硬大小上限及解析器禁令；P13 Random/Password Profile 补入受批准 CSPRNG/Provider、无偏采样、一次性交付和不隐式持久化边界。

### 历史编号追溯规则

- 本记录之前的 acceptance log 中出现的 Pxx/Wxx 编号属于其记录发生时的实施计划版本，只作为历史证据保留。
- 当前工作包编号、名称、状态、前置依赖和执行游标只能以 `ns_vault_implementation_plan_for_design_0.0.1.md` 最新内容为准。
- 典型重排包括但不限于：旧记录中的客户端/CLI、审计强化、Shard/HA、DR、容量和生产门禁阶段，现已分别归入当前 P11、P17、P18、P19、P20、P21/P22；不得仅凭旧编号启动实现。

### 校准后的事实

- 阶段仍为 23 个，`P00`—`P22` 连续；工作包仍为 177 个，编号无重复且每个具有显式状态。
- 当前仍有 4 个治理文档工作包为 `VERIFIED / F1 (document-only)`，其余 173 个为 `BLOCKED / F0`。
- 当前唯一执行游标未改变：`P00-W05 本地工作区实现事实盘点与基线校准`，状态 `BLOCKED / F0`。
- 本轮只修订实施计划和 acceptance log，没有修改设计清单、ADR、生产代码、配置、依赖、Migration 或测试；没有运行实现测试，也没有执行 commit、push 或 Pull Request。

### 证据边界

- 本记录证明实施治理文档已经闭合分级门禁与分级发布语义，不证明任何 Level 已通过。
- HSM/KMS/HYOK sandbox、测试 Provider 或合同测试不能替代 P21 Level 2/3 所需的真实或 production-equivalent 证据。
- 本轮未读取用户当前本地 Git 工作区，因此不证明用户项目中已经采用本轮修订文件。

---

## 2026-07-31 四份治理文档最终全量交叉审查

> 校准时间：`2026-07-31T14:12:00+08:00`

### 审查范围

- 从头到尾复核以下四份 `0.0.1` 治理文档：
  - `ns_vault_design_checklist_0.0.1.md`；
  - `ns_vault_architecture_decisions_0.0.1.md`；
  - `ns_vault_implementation_plan_for_design_0.0.1.md`；
  - `ns_vault_acceptance_log_0.0.1.md`。
- 按“设计边界 → 长期 ADR → 实施计划当前状态与执行游标 → 历史验收证据”的治理权威顺序，执行双向承接、状态逻辑、依赖、引用、边界和 Markdown 结构检查。
- 本轮不新增产品能力，只关闭四份文档之间已经存在的歧义、实施旁路和权威顺序冲突。

### 最终校准内容

- 实施计划的权威顺序调整为：设计清单、已接受 ADR、实施计划当前状态/执行游标、当前工作包、acceptance log 历史证据。本地代码、配置和测试是实现事实来源，但不凌驾于设计与 ADR，也不能绕过实施计划直接推进游标；发现漂移时必须先记录并校准实施计划。
- 资源层级区分：
  - 普通租户产品资源使用 `Tenant → Project → Namespace → Resource`；
  - Tenant Key Domain 属于 Tenant 级密码学域；
  - Root/Seal、Authority 签发密钥、Backup Protection、Shard/Region、审计锚点和可信时间连接等内部安全资源采用显式 system/deployment/region/shard/Tenant scope，不伪造 Project/Namespace，也不通过普通租户资源 API 暴露。
- 默认不因资源引用、名称、Alias、同属 Tenant 或父层级关系获得跨 Project/Namespace 权限；同 Tenant 跨边界访问必须具有显式 Grant、全部 Guardrail 和精确到 Resource/Generation 的 Capability。
- Namespace/Project 移动被定义为 Shard Leader 权威命令，必须绑定 expected generation，重新计算策略，失效旧 Capability，检查 Lease、证书、Provider operation 和依赖，并写入 Strong Audit。历史密文、wrapped DEK、签名、证书和其他密码学制品保留创建时不可变的 cryptographic scope；新版本绑定新 scope。无法安全保持认证绑定时必须使用显式 re-encryption、migration 或新 Resource，禁止只修改元数据。
- 受 Vault 信任的身份断言签发私钥不得位于普通 `ns_backend` Web/API 进程；必须由独立 SSO/IdP、隔离 Identity Authority、HSM/KMS 或等价边界持有。backend 数据库字段、内部请求头和未签名 claim 不能建立 Vault Principal。
- Policy Compiler 不成为隐含授权权威。Vault 必须验证受信任 Compiler 身份/版本、Intent、Approval、上级 Guardrail、Scope、Schema、Hash 和非扩权性质后才接受 Policy Artifact。
- 明文 Root/Seal 解封结果只能终止于专用 Root/Seal Authority 或 Crypto Authority 的严格 bootstrap 边界；通用 Provider Host 只传递 opaque handle、wrapped material 或受限调用结果，不得转运或缓存根明文。
- 主机级本地交付组件统一称为 Vault Delivery Agent，并明确不等同于 `ns_node` 或未来 `ns_agent`，不得占用 `src/ns_agent` 产品边界，也不得借用 Node Principal 代表 workload。
- `ns_node` 兼容边界补充：所有 Vault 网络通信经专用通信进程和受认证本地 IPC/FD 路径；调度主进程、OCR、浏览器/桌面自动化和插件执行进程不得自行连接 Vault或隐式继承 Node Capability。
- Tenant Key Domain 补充禁止隐藏万能根；Policy Artifact 补充受版本治理、可静态验证的声明式 IR；Root Provider 文本明确包含低保障 Software Root Provider，且只有明文解封材料被禁止进入通用 Provider Host。
- Secret 明文边界与 `provider_direct_nonrecoverable` 例外完成一致化；多区域热备补入 Home Region 内 Leader/Replica HA、有界复制滞后和分钟级受控接管目标类别。
- 远程可访问仓库中可确认存在 `src/ns_common/async_runtime.py`；该远程事实只用于说明存在可评估的公共设施，不替代 P00-W05 对用户当前本地工作区的只读校准，也不证明其能够直接满足 Vault 的安全生命周期要求。
- 设计清单最终核对项同步采用 Vault Delivery Agent、Provider 直交付例外、`ns_node` 专用通信进程、隐藏万能根禁令和声明式 Policy IR 术语；§23 同时纠正为：API 字段、数据库品牌、包版本等默认属于实施/工程文档，只有改变长期边界时才新增 ADR。
- acceptance log 的验收记录模板已移至文件末尾，避免模板插在真实历史记录之间。

### 机械与治理检查

- 设计清单、ADR、实施计划和验收日志的 Markdown code fence 均闭合，未保留行尾多余空白。
- ADR 编号、索引和正文保持 `ADR-001`—`ADR-069` 连续，状态均为 `ACCEPTED`；设计章节引用和实施计划 ADR 承接均有效。
- 实施阶段保持 `P00`—`P22` 连续；所有工作包均具有显式状态，阶段依赖无环，当前唯一执行游标保持 `P00-W05`。
- 本轮校准没有把设计目标写成实现或测试事实，没有将任何生产等级、Provider、HA/DR、性能或安全门禁提前标记为通过。

### 证据边界

- 本轮只修订四份本地文档制品，没有读取或修改用户当前本地 Git 工作区中的代码、配置、依赖、Migration 或测试。
- 没有运行 `ns_vault` 实现测试、集成测试、性能测试、HA/DR 演练或生产门禁。
- 没有执行 commit、push 或 Pull Request。
- 当前实现状态和执行游标仍只以 implementation plan 最新内容为准。

---

## 后续验收记录模板

后续每个工作包按以下格式追加，不覆盖历史记录：

```markdown
## YYYY-MM-DD <工作包与简要主题>

### <工作包编号与名称>

- 起始事实：本地分支、HEAD、工作树、基线文档版本。
- 授权范围：本次允许修改和禁止修改的边界。
- 修改文件：实际文件列表。
- 公共契约：新增、修改或无变化。
- 实现事实：能够由代码证明的行为。
- 测试命令：完整可复现命令。
- 测试结果：数量、通过、失败、跳过、耗时和环境。
- 安全检查：越权、重放、敏感信息、依赖方向、旁路和 fail-closed。
- 外部依赖：数据库、Provider、HSM/KMS、Redis/Valkey、对象存储、审计锚点等真实状态。
- 作废证据：失败或被后续发现无效的测试序列，保留原因。
- 未验证项：不得省略。
- 提交事实：commit、push、PR；未发生时明确写未发生。
- 状态更新：本计划中的新状态、F 等级和下一执行游标。
```
