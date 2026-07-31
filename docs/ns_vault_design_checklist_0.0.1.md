# ns_vault 设计边界与功能清单

> 文档版本：`0.0.1`
>
> 本文档描述 `ns_vault` 的完整最终产品边界、安全边界、功能范围、默认行为和生产约束，用于在后续架构决策、实施计划、代码审查和验收过程中防止设计漂移。
>
> 本文档不是实现进度报告，不按 MVP、当前阶段、里程碑或临时替代方案缩减最终要求；某项能力尚未实现，不改变其在本文档中的最终边界。

## 0. 使用约定与文档权威

- 后续讨论、实现和审查开始前，必须先阅读本文档，并把其中已经写明的“必须”“禁止”“默认”“仅允许”“由策略决定”等要求视为已冻结设计边界。
- 如需改变本文档中的已冻结边界，必须显式说明变更原因、影响范围、兼容与迁移方式，并在长期架构决策文档中形成新的决策或替代关系；不得通过代码、配置、工作包或验收记录静默改变。
- 文档权威顺序固定为：
  1. `docs/ns_vault_design_checklist_0.0.1.md`：最终产品边界和功能清单；
  2. `docs/ns_vault_architecture_decisions_0.0.1.md`：长期架构决策、取舍和约束；
  3. `docs/ns_vault_implementation_plan_for_design_0.0.1.md`：唯一当前实施状态与执行游标；
  4. `docs/ns_vault_acceptance_log_0.0.1.md`：只记录已经发生的验收事实和历史证据。
- 实施计划、阶段成本、局部验证、当前基础设施限制和临时替代实现都不得反向缩小本文档的最终设计边界。
- 验收日志不能覆盖设计边界或当前实施状态；历史上曾经通过某项验证，不代表当前版本仍然满足，也不代表未验证能力已经实现。
- 本文档只讨论 `ns_vault` 及其与其他组件的必要兼容边界；未来独立 `sso` 服务的账号体系、登录流程、会话、MFA 产品设计和内部架构不在本文档内展开。
- 本文档中的 `ns_backend`、`ns_runtime`、`ns_node`、`ns_client`、`ns_common`、`ns_frontend` 和未来 `sso` 均指 `ns_evermore` 项目内对应组件或规划组件。

## 1. 核心定位、完整产品范围与明确非目标

### 1.1 核心定位

- `ns_vault` 的最终定位是 `ns_evermore` 中独立运行的集中式密钥、秘密、证书、动态凭证、工作负载身份和密码学能力安全服务。
- `ns_vault` 是安全执行权威，不是 `ns_backend` 内的普通业务模块；其正式服务边界位于 `src/ns_vault`。
- `src/ns_backend/vault` 是固定存在的 Django 控制面应用，应用键为 `vault`，但不得因此取得 Vault 根信任、密钥材料、Secret 明文、私钥、Lease、Provider 会话或实际安全状态的权威。
- 内部组件和外部客户必须共享同一套资源、身份、授权、版本、策略、审批、审计、配额、计量和生命周期模型；不得为外部客户另建安全语义较弱或不兼容的第二套 Vault。
- `ns_vault` 必须同时支持软件托管、硬件托管、云 KMS、BYOK 和 HYOK 等不同保障等级，并明确展示各模式的真实安全保证，不得把低保障实现标记为高保障能力。

### 1.2 完整功能范围

`ns_vault` 的最终产品能力必须覆盖：

- KMS 与 Key Management：对称密钥、非对称密钥、包装密钥、签名密钥、MAC 密钥、CA 密钥、Capability 签发密钥、审计签名密钥及其版本、轮换、迁移、停用和销毁。
- Secrets Management：通用 Secret、标准化 Secret 类型、不可变版本、单一当前版本、Envelope Encryption、受控字段读取、本地交付、人工高风险读取和密码学销毁。
- Transit：加密、解密、签名、验签、MAC、校验、包装、解包及规范密文信封。
- PKI：X.509 私有 PKI、Trust Domain、Root/Intermediate/Issuing CA、Certificate Role、短期证书、CRL、OCSP、紧急 deny、外部 CA 联邦和 SSH CA。
- Dynamic Credentials：数据库、云 STS、Kubernetes、外部 API、SSH 或其他 Provider 的临时凭证签发、交付、续期、撤销、清理和对账。
- Lease：Secret、证书、动态凭证、工作负载会话和 Provider 会话的统一权威生命周期。
- Workload Identity：人员、服务、工作负载、节点、设备、Provider 和外部客户的联邦身份绑定与证明。
- Password、Random 与 Derivation：密码生成、安全随机数、受控 KDF、Derivation Profile、内部派生、包装输出和 Provider 内不可导出派生。
- Deterministic Transform 与 Tokenization：在独立高风险资源模型下提供可逆确定性变换和不可逆稳定 Token，不把该能力隐藏为普通加密参数。
- Provider Federation：软件密码学、HSM、云 KMS、外部 KMS、HYOK、外部 CA、数据库、云 STS、审计锚点和可信时间 Provider。
- BYOK/HYOK：安全导入、外部持有、来源证明、不可导出边界、迁移、恢复责任和销毁责任。
- Agent 与交付平面：主机 Agent、Sidecar、CSI 类适配、Windows Service、Unix Socket、Named Pipe、文件、FD、tmpfs 和受控一次性注入。
- SaaS 与平台治理：Customer Account、Vault Tenant、Project、Namespace、配额、计量、审批、强审计和外部客户自助能力。
- 控制面与安全运营：资源状态与健康、统计视图、安全告警、组件/集成接入登记、访问边界管理和事件驱动的运营投影；这些能力不得成为绕过 Vault 权威状态与授权的旁路。

### 1.3 明确非目标

- `ns_vault` 不是通用非敏感配置中心，不负责普通应用配置、Feature Flag、灰度配置发布、服务发现或配置热更新平台。
- `ns_vault` 不是人员个人密码管理器，不提供浏览器自动填充、个人密码库、共享登录项、员工密码继承或个人安全笔记。
- `ns_vault` 不是文件、文档、目录或任意业务数据保险箱；大型文件和文档应由专用对象存储承载，Vault 只管理相关密钥、凭证、策略或受控引用。
- `ns_vault` 不是通用工作流、工单或 BPM 引擎；只实现与安全资源直接相关的审批、职责分离、恢复和销毁语义。
- `ns_vault` 不替代 `ns_backend` IAM，也不替代未来 SSO 的人员目录和登录产品能力。
- `ns_vault` 不成为任意低层密码学工具箱；普通调用方不得自由选择不安全算法、Nonce、KDF 参数或绕过资源用途约束。
- `ns_vault` 不提供通用收敛加密、跨租户密文去重或基于明文内容直接推导业务数据密钥的能力。

## 2. 安全威胁模型与权威边界

### 2.1 backend 失陷后的安全目标

- `ns_backend` 是统一产品控制面，但不是 Vault 数据面最终授权权威。
- backend 提交的是控制命令、策略意图、审批输入、身份事实或授权证据；其普通服务身份不能单独构成任意 Secret 读取、解密、签名、证书签发、动态凭证创建或销毁的授权。
- `ns_vault` 必须独立校验 principal、tenant、resource、action、Guardrail、Grant、policy version、principal-binding version、resource generation、security epoch、审批证据、时间状态、撤销状态和防重放条件。
- backend 超级管理员不得天然成为 Vault 超级管理员，也不得天然绕过租户策略、高风险审批、不可导出边界和密码学销毁门禁。
- backend 被攻破后，攻击者的能力应被限制在其已持有的短期、范围受限、可撤销控制面 capability 内；不能自动获得全租户数据面权限。

### 2.2 数据库、主机和进程失陷边界

- backend 数据库泄露不得直接暴露 Secret ciphertext、wrapped DEK、私钥材料、Lease 交付包或 Vault 强审计原始记录。
- Vault Authority 数据库泄露的设计目标是假设攻击者可以获得密文和元数据，但不能仅凭数据库内容获得 Secret 明文、Tenant KEK 或不可导出私钥。
- 普通 API 进程被攻破时，不应取得根密钥、Tenant KEK、Provider 主凭证或全部租户密码学能力。
- Provider Host 被攻破时，其影响必须限制在被授予的 Provider、租户/Key Domain、操作和短期会话范围内，不能写 Vault 权威状态或签发 Vault Capability。
- Authority Worker 被攻破时，其影响必须限制在当前 shard、epoch、资源、generation、operation 和预算内，不能获得租户根权威。
- Agent 被攻破时，其影响目标必须限制在当前绑定的 workload、已获授权资源和剩余有效期内。
- 软件保障等级下，操作系统 root、内核或宿主机管理员仍可能读取 Authority 当前内存；文档和产品界面必须明确这一风险，不能宣称等同 HSM/HYOK。
- 硬件或外部控制保障等级下，根密钥、关键 KEK 和不可导出私钥应在 HSM、KMS、TPM 或外部 Provider 内执行，普通主机管理员不能直接导出这些材料。
- 任何内存清理、锁页、禁止交换或崩溃转储防护只能作为加固措施，不得作出底层平台无法证明的“绝对安全擦除”承诺。

### 2.3 默认安全原则

- 默认拒绝。
- 无法确认身份、授权、资源状态、Provider 结果、时间可信度或审计落盘时，默认 fail-closed；只有明确策略允许的有限继续服务路径可以例外。
- 不允许以“内网调用”“backend 发起”“平台管理员”“调试模式”或“兼容旧系统”为理由建立隐式安全旁路。
- 不允许通过环境变量、普通配置文件、本地备用 Secret 或隐藏 Provider fallback 绕过 Vault 权威。

## 3. 公共设施复用与工程边界

### 3.1 复用原则

- `ns_vault` 实现必须优先复用 `ns_evermore` 已有公共设施，不得重复建设功能等价但语义竞争的配置、异常、日志、HTTP、ID、时钟、状态存储或依赖注入基础设施。
- 复用公共设施必须以安全语义满足 Vault 要求为前提；公共设施能力不足时，应优先把真正通用的能力扩展到 `ns_common`，而不是在 Vault 内复制一套私有通用框架。
- Vault 专属的资源、策略、Capability、Lease、Provider、密文格式和强审计合同不得硬塞进 `ns_common`；公共层只承载跨组件稳定、无 Vault 私有权威语义的基础能力。
- 复用公共设施不等于共享安全权威；Secret、Key、Lease、Certificate、Policy Artifact、Provider 状态和 Strong Audit 的最终权威仍属于 `ns_vault`。

### 3.2 应优先复用的现有能力

- 配置：优先复用 `ns_common.config` 的配置组、解析、校验、元数据版本和不可变快照能力，用于非秘密运行配置和 Secret Reference；不得把根密钥、Tenant KEK、私钥或生产 Secret 明文放入普通配置快照。
- 异常：复用 `ns_common.exceptions` 的稳定异常体系和错误注册机制，并扩展 Vault 稳定错误分类；传输层状态码不能代替领域错误码。
- 脱敏与日志：复用 `ns_common.security` 中的 Sanitizer 和敏感字段处理能力，并针对 Vault 的 Key、Secret、Credential、Token、Provider、CSR 和 Payload 元数据扩展规则。
- HTTP：复用 `ns_common` 已有异步 HTTP 客户端抽象、超时、重试和脱敏边界；Provider 特有客户端必须置于隔离 Provider Host，不能在 Authority 内随意实例化第三方 SDK。
- ID 与时间：复用现有 typed ID、Clock、SystemClock、ControlledClock 等通用抽象；Vault 在其上增加安全单调时间、可信时间等级和 epoch 语义。
- 状态存储：优先复用现有 StateStore provider 抽象表达协调能力；如果现有语义不足以证明单写、fencing、epoch 和一致性，则必须扩展公共合同或使用满足要求的实现，不能把普通 TTL lock 当成安全共识。
- 依赖边界：延续 `ns_runtime` 已建立的显式依赖注入、composition root、Authority Broker/Attestor、普通进程不持有根材料和 FD/受限句柄传递原则。
- 身份事实：复用 `ns_backend.iam` 的用户、组织、角色、身份状态等事实，但 Vault 必须独立维护 issuer 信任、Principal Binding、Policy Artifact 和最终授权。
- 控制面：复用 `ns_backend` 的 Customer、Tenant 运营、审批入口、配额、计量、投影和审计查询能力，不复制成 Vault 内的第二套平台后台。

### 3.3 禁止误用

- 现有 `AesGcmSecretBox` 只能被视为小型内存秘密保护原语或参考实现，不得直接作为 Vault 持久化 Envelope Encryption、Key 生命周期、Tenant 隔离或授权模型。
- 现有 backend 操作审计只能作为平台审计投影或控制面记录，不能替代 Vault 强审计链。
- 现有 IAM 中的角色、group、department 或 superuser 不能直接成为 Vault Resource Grant。
- 现有 StateStore 中的环境变量或文件密码引用不能成为 Vault Root、Tenant KEK 或 Provider 主凭证的生产明文来源。
- 不得因为复用 Django、FastAPI、数据库 ORM、Redis/Valkey 或其他现有设施而降低 generation、fencing、审计和 fail-closed 要求。

### 3.4 代码与依赖风格

- 运行期状态必须归属明确的 service、authority、repository、registry、scheduler、worker、provider host 或 context；禁止模块级全局可变状态。
- 核心依赖必须从 composition root 显式传入；禁止深层代码直接实例化全局数据库、HTTP 客户端、Provider、IAM 或审计单例。
- 领域合同、状态记录和策略输入输出应使用类型明确的结构，不在核心链路长期传递无约束裸 dict。
- API、Authority、Provider、Scheduler、Audit 等职责必须按安全边界拆分，禁止单个类或进程同时承担所有核心职责。
- Vault 异步生产代码应基于标准 `asyncio` 语义；具体 ASGI 或 RPC 框架不得渗透进领域合同和安全状态机。

## 4. 平台账户、多租户与资源层级

### 4.1 SaaS 与运营层级

最终产品层级固定为：

```text
Platform Account
└── Customer Account
    └── Vault Tenant
        └── Project
            └── Namespace
                └── Resource
```

- Platform Account 表达平台运营、全局配额、SLA、Provider 运营和计量边界，不拥有租户密码学权限。
- Platform、Customer 或 Tenant 管理员身份都不自动获得 Secret 明文、Key 使用或私钥访问权；任何数据面能力仍必须通过对应 Principal Binding、Grant、Guardrail、Approval 和 Capability。
- Customer Account 表达合同、客户生命周期、客户管理员和支持关系，不是密码学隔离边界。
- Vault Tenant 是密码学隔离和安全资源归属边界，拥有独立 Tenant Key Domain。
- 内部系统必须映射为 Internal Customer Account 下的 Vault Tenant，外部客户映射为 External Customer Account 下的 Vault Tenant；二者使用同一安全模型。
- 平台管理员不能因 Platform Account 身份自动读取任何 Tenant Secret 或使用 Tenant Key。

### 4.2 固定资源层级

- 面向租户的 Key、Secret、Transit、PKI、Credential Role、Lease、Provider Binding、Derivation Profile 和 Tokenization Profile 等普通产品资源，必须归属于唯一 Tenant、Project 和 Namespace。
- Tenant 表达客户或内部独立安全主体；Project 表达产品、系统或业务工作区；Namespace 表达授权、环境和运维隔离边界。
- Tenant Key Domain 本身是 Tenant 级安全资源；Root/Seal、Capability/Audit/Manifest 等内部 Authority Key、Backup Protection Key、Shard/Region、外部 Audit Anchor 与 Trusted Time Connector 等平台内部资源必须使用明确的 platform/deployment/region/shard 或 Tenant scope，不得为了套用租户目录而伪造 Project/Namespace，也不得通过普通 Tenant Resource API 暴露。
- 平台内部资源虽不属于普通租户目录，仍必须遵守明确类型、稳定 ID、版本、generation、最小权限、Strong Audit、删除/销毁和兼容治理，不得形成无治理的隐藏全局状态。
- 简单使用场景可以自动创建默认 Project 和 Namespace，但底层模型和审计引用不得省略层级。
- 所有层级使用稳定、不透明 ID；名称只用于展示和检索。
- 重命名不得改变资源 ID、密码学身份、审计关联或 Capability 绑定。
- Resource 名称只需在所属 Namespace 和 Resource Type 内唯一；Alias 不得代替稳定 ID。
- 资源不得跨 Tenant 移动；跨 Tenant 协作只能通过显式授权的服务调用、密文交换或独立导入流程完成，不能共享底层 Tenant KEK。
- 跨 Project 或 Namespace 的读取、密码学操作和交付默认不存在隐式继承；同一 Tenant 内只有显式 Grant、Guardrail 允许且最终 Capability 精确绑定目标 Resource/Generation 时才可访问，Resource 的所有权、上级 Mandatory Guardrail 和 Tenant Key Domain 不因此改变。
- Namespace 或资源在同一 Tenant 的允许范围内移动时，必须通过 Shard Leader 的显式安全命令执行，绑定 expected generation，重新计算策略、提升 generation、撤销旧 Capability、处理或拒绝仍有效的 Lease/Certificate/Provider Operation，并产生 Strong Audit；资源类型、Provider 或依赖关系不能安全迁移时必须拒绝 metadata-only move，改用显式迁移、新资源或重新加密流程。
- 已存在的密文、签名、证书、wrapped DEK 和其他版本化密码学制品必须保留创建时稳定的 cryptographic scope 与 AAD/格式绑定；移动后授权按当前行政层级裁决，但历史制品不得通过改写 Project/Namespace 元数据改变其认证内容。新 Version 使用移动后的当前 scope；无法同时证明历史可验证性和当前授权边界时禁止移动。
- 标签可以用于检索、计量、条件策略和运营视图，但不能替代 Tenant、Project、Namespace 等安全边界。

### 4.3 Tenant Key Domain

- 每个 Vault Tenant 必须拥有独立 Tenant Key Domain。
- 每个 Tenant Key Domain 绑定独立 Tenant KEK 或等价 Provider Key，并对 KEK generation 进行权威版本管理。
- Tenant KEK 可由软件 Authority、HSM、云 KMS、BYOK 或 HYOK Provider 承载。
- Project、Namespace 和 Resource 可以拥有进一步的包装或派生边界，但必须归属于唯一 Tenant Key Domain，不能构建任意跨租户密钥图。
- Tenant Key Domain 必须支持独立冻结、轮换、渐进式 rewrap、Provider 迁移、灾备和密码学销毁。
- 平台可以提供默认托管 Tenant KEK，但必须允许租户升级至 HSM、BYOK 或 HYOK，且不得静默降低保障等级。
- 平台 Root/Seal 只能保护平台 bootstrap、控制关系或明确的平台托管 Tenant Key Domain；不得存在能够绕过 Tenant Key Domain、Provider 控制和 Vault Policy 解密全部租户资源的隐藏万能根。`external_controlled`/HYOK 资源在客户 Provider 不可用或撤销授权时必须保持不可用。

## 5. 身份、Principal 与 SSO 兼容边界

### 5.1 Principal 类型

Vault Principal 至少明确区分：

```text
human
service
workload
node
device
provider
external_customer
recovery
```

- 不同 Principal Type 不得隐式互换或借用身份。
- node principal 不是 workload principal；service principal 不是 human principal；recovery principal 不得成为日常管理员。
- 每个 Principal Binding 必须包含 identity source、issuer、subject、tenant、principal type、workload/node/device class、authentication method、assurance level、有效期和撤销状态。
- `issuer + subject` 组合才构成外部身份唯一性，禁止脱离 issuer 使用裸 subject 作为全局身份。

### 5.2 联邦身份与本地验证

- `ns_vault` 不维护完整企业人员目录，而采用联邦身份认证和 Vault 本地安全绑定。
- 支持的身份来源应包括企业 OIDC、未来 SSO、mTLS、SPIFFE/SPIRE、Kubernetes ServiceAccount、云 workload identity、TPM/TEE、设备证明、`ns_runtime` Authority Attestor、`ns_node` 节点证明及其他受批准 Provider。
- Vault 必须独立维护受信任 issuer、trust bundle、audience、issuer-to-tenant 约束、Principal Binding、撤销状态、认证等级和 attestation policy。
- 能为 human、service、workload、node 或 device 签发受 Vault 信任 assertion 的私钥和根签发能力，必须位于独立 SSO/IdP、隔离 Identity Authority、HSM/KMS 或等价受保护边界；普通 `ns_backend` Web/API 进程、数据库字段、内部请求头或服务凭证不得成为可冒充任意主体的 issuer。
- 数据面优先本地验证短期签名凭证，不应要求每次请求实时向 `ns_backend` 或 SSO introspection；紧急撤销通过短有效期、本地 deny/撤销状态和 epoch 组合实现。
- 外部 token 必须具有明确 Vault audience；面向其他服务的通用 token 不得被接受为 Vault 数据面凭证。
- 外部 token 中的 role、group、department 和 permission claim 只能作为 Principal Binding 输入，不能直接成为 Vault Grant。
- 高风险操作可以要求近期认证、MFA、特定 authentication assurance、设备或工作负载证明。
- Vault 可以保留严格受限的本地恢复身份，但其能力只用于 seal/unseal、信任恢复和预定义 break-glass 操作，不能成为日常 Secret 读取账户。

### 5.3 与未来 SSO 的兼容边界

- 未来 SSO 仅作为 Identity Provider 向 Vault提供经过验证的 identity assertion。
- SSO 可以提供 issuer、subject、认证强度、MFA 状态、会话有效性和基础身份属性，但不拥有 Vault Resource Permission。
- SSO role 和 group 不得直接转换为 Vault Grant；最终 Tenant、Project、Namespace、Resource、Action 和 Capability 由 Vault Policy 决定。
- Vault 不复制 SSO 用户目录，不依赖某个特定 SSO 内部实现；SSO Provider 可替换而不改变 Vault 安全模型。
- SSO 用户禁用、会话失效或认证等级变化必须通过 Principal Binding、撤销状态或短期凭证生命周期影响 Vault，但不能绕过 Vault 权限模型。

### 5.4 Workload Identity Federation

- 工作负载必须通过统一 Workload Identity Federation 与 Attestation Binding 接入 Vault。
- 普通服务可以使用 OIDC、SPIFFE、Kubernetes 或云身份；高保障资源可以要求 TPM、TEE、代码测量、特定节点或部署证明。
- 身份认证成功后，Vault 根据策略签发短期 Capability，而不是直接授予长期 Secret 权限。
- Identity evidence 可以被规范化摘要并进入强审计，但不得保存可重放的原始凭证。
- Issuer rotation、trust bundle 更新、Principal Binding 变更和身份撤销属于 Vault 安全状态变更，必须版本化、审计并触发必要的 Capability 失效。

### 5.5 组件与集成接入

- `ns_backend.vault` 负责 `ns_frontend`、`ns_runtime`、`ns_node`、`ns_client`、Vault Agent、Provider Host、内部服务和外部客户应用的组件/集成登记、运营状态、期望绑定和接入编排。
- 组件登记只是一项控制面事实，不是凭证、Principal Binding、Vault Grant 或数据面 Capability；仅完成登记不得获得任何 Secret、Key、Certificate、Lease 或 Provider 能力。
- 每个集成必须映射为明确的 principal type、issuer/subject、Tenant/Project/Namespace 作用域、允许的认证方式、assurance requirement 和可撤销 Binding；不得使用跨组件、跨 workload 或跨 node 共享的通用高权限凭证。
- Vault 必须独立验证接入证据、接受或拒绝 Principal Binding，并依据 Guardrail/Grant 签发短期 Capability；backend 的“已接入”状态不能替代 Vault 的最终身份与授权判断。
- `ns_frontend` 只是控制面 UI/浏览器客户端，不得以部署身份继承当前 human/external_customer 的 Vault 权限；用户操作必须绑定实际终端 Principal，Secret payload 通过 Vault 签发或认可的短期直连会话交付，不能由 frontend/backend 服务端代持。
- 组件停用、身份轮换、租户解绑或接入撤销必须按影响范围失效 Principal Binding、Capability、Lease、Provider Session 和本地缓存；无法确认外部状态时必须显示风险状态并进入 reconciliation。

## 6. 策略、授权、Capability、审批与恢复权限

### 6.1 Mandatory Guardrail 与 Delegable Grant

- Vault 策略采用 Mandatory Guardrail 与 Delegable Grant 分层模型，所有请求默认拒绝。
- Mandatory Guardrail 定义不可被下级削弱的约束，例如必须使用 HSM、禁止导出、禁止人工明文读取、限制地域、禁止弱算法、强制双人审批、限制 Lease 寿命、强制 leader-only 或禁止 DEK 缓存。
- Guardrail 可以定义在 Tenant、Project、Namespace 或 Resource 层级并向下强制生效；子级只能收紧，不能放宽。
- Delegable Grant 明确 principal、action、resource scope、condition、继承范围、委派上限、委派深度、有效期和审批要求。
- 上级 Grant 不默认无限向下传播；必须显式声明继承和再委派能力。
- 委派者不得授予超出其委派上限的权限，也不得把不可委派 Capability 转换为可委派权限。
- `explicit deny` 和 Mandatory Guardrail 优先于所有 allow。
- 最终授权必须同时满足：身份绑定有效、存在匹配 Grant、全部 Guardrail 满足、无显式 deny、资源和系统安全状态允许。

### 6.2 Policy Intent 与 Policy Artifact

- `ns_backend.vault` 保存 Policy Intent、管理上下文、审批、版本和产品运营信息。
- `ns_vault` 保存并执行经过验证的 Policy Artifact、Policy Version、生效状态和决策引用。
- Policy Artifact 必须包含 source intent version、compiler version、artifact version、tenant/resource scope、hash 和生效时间。
- backend 不直接写 Vault 权威策略表；Vault 只执行自身接受并保存的 Policy Artifact。
- Policy Compiler 的转换结果不得超出已批准 Intent 和上级 Guardrail；编译失败、版本不兼容或 hash 不一致时必须拒绝生效。
- Compiler 即使独立部署或由 backend 调用，也不能因此获得信任；必须具有受验证的实现版本/制品身份或运行于 Vault 信任边界内。Vault 必须独立验证 source Intent、Approval、上级 Guardrail、scope、schema、hash 和非扩权性质，不能接受 backend 提交的任意可执行策略。
- Policy Artifact 必须采用受版本治理、可静态验证的声明式 IR；Grant、Deny、Guardrail、Scope、Condition 和 Delegation 的边界必须可被 Vault 机械检查。禁止把任意脚本、模板代码、动态导入或无法证明权限上界的表达式作为可执行 Policy Artifact。
- Intent、Artifact、Principal Binding、Resource Generation 和 Security Epoch 必须可追溯关联。
- 策略决策必须能够解释匹配的 Grant、Guardrail、deny、身份版本、资源版本和最终结果；所有拒绝及高风险允许应进入可解释审计。

### 6.3 短期 Capability

- Vault 在完成完整身份与策略决策后，可以签发更窄的短期 Capability，供数据面、Authority Worker、Agent、SDK 或特定 Provider 路径使用。
- 数据面 Capability 只能由 `ns_vault` 授权 Authority 签发；`ns_backend`、SSO、Agent、runtime、node 和 Provider Host 均不得自行签发。
- Capability 至少绑定 issuer、principal、principal type、Tenant/Project/Namespace、Resource ID、Resource Generation、Allowed Actions、Shard、Authority Epoch、Policy Version、Authentication Strength、Approval Reference、Expiry、Token ID/Nonce、预算和必要的 workload/channel binding。
- Capability 只能缩小已成立权限，不能扩大；普通 Capability 默认不可再委派，委派必须使用独立 delegation capability 类型。
- Capability 不得携带 Secret、DEK、KEK、私钥或 Provider 主凭证。
- 紧急禁用、租户冻结、资源销毁和安全事件必须通过撤销状态、deny list、resource generation 或 epoch 提升立即使相关 Capability 失效。
- 高风险操作在执行时必须再次校验当前 epoch、generation、撤销状态、审批有效性、时间可信度和一次性消费状态。

### 6.4 分层审批

- 普通控制面操作可以使用 `ns_backend` 的平台审批流程。
- Secret 人工明文读取、允许的 Key 导出、Guardrail 创建/修改/删除、Tenant Key Domain 销毁、Root Provider 更换、unseal/recovery、CA 高风险操作、Provider 迁移和审计保护配置变更必须进入 Vault Security Approval。
- 任何审批、break-glass 或平台管理员权限都不得关闭 Strong Audit、删除既有审计事实，或把审计保护降低到系统强制最低线以下；审计保护配置只能在不破坏最小完整性和外部锚定边界的前提下变更。
- Vault Security Approval 必须绑定操作、Resource、Resource Generation、Requester Principal、Approver Identity、Authentication Assurance、MFA/强认证证据、职责分离规则、时间窗口和一次性消费状态。
- backend 普通审批不能替代 Vault Security Approval；backend 管理员身份不能自动通过安全审批。
- 资源 generation、policy version 或 security epoch 发生变化后，旧审批默认失效，必须重新评估或重新批准。

### 6.5 门限式 Break-glass

- Vault 支持独立的门限式 Break-glass 恢复域，用于正常身份链、审批系统或外部依赖严重故障时的预定义恢复操作。
- Break-glass Principal 不属于普通 SSO 用户、backend 管理员或 Vault 日常管理员。
- Break-glass 必须多方参与、独立认证、明确用途、时间限制、最小操作范围和强审计。
- 当正常 Vault Security Approval 链路不可用时，已消费的门限 Recovery Evidence 只能替代预先声明的紧急恢复 Action 所需审批，且必须形成独立 Emergency Session；这不是对普通高风险操作、Guardrail 或授权模型的通用绕过。
- Break-glass 不得导出 non-exportable Key、关闭审计、绕过 Tenant Guardrail、获取永久管理员身份或建立通用数据面权限。
- 恢复会话必须绑定 Recovery Evidence、资源范围、操作类型、有效期和使用预算，并在完成或超时后立即失效。

## 7. 控制面、命令、事件、状态与投影

### 7.1 控制面与执行权威

- `ns_backend.vault` 是统一产品控制面，负责 Customer Account、Tenant/Project/Namespace 管理、组件/集成接入、Policy Intent、审批入口、Quota、Billing/Metering、Command 编排、Desired State、资源状态与统计 Projection、安全告警编排/通知和 Audit 查询。
- `ns_vault` 负责 Actual Security State、密码学执行、Key、Secret、Lease、Certificate、Provider、Security Event、Security Risk Signal 和 Strong Audit。
- backend 不保存 Secret 明文、DEK、KEK、私钥、Provider 主凭证或 Vault 权威状态。
- Projection 只用于控制面展示、检索和运营，不是安全权威，也不能反向覆盖 Vault Actual State。
- 安全告警和统计必须由 Vault 的 Receipt、Security Event、Risk Signal 或 Actual State 派生；backend 负责展示、路由和通知，但通知失败不得删除安全事实、把未知状态标记为正常，或改变 Vault 已执行的 fail-closed/隔离处置。

### 7.2 Command、State、Receipt 与 Event

- Vault 采用混合 Command + Actual State + Execution Receipt + Security Event 模型，不采用把所有当前状态完全事件溯源化的模型。
- Command 表达请求改变安全状态；Actual State 表达当前权威安全事实；Execution Receipt 表达命令执行结果；Security Event 表达不可变历史事实。
- Command、Event、Current State 和 Projection 必须保持不同语义，禁止把任意一个当作另一个的替代。
- 所有有副作用的 Command 至少包含 command_id、command_version、idempotency_key、expected_generation、policy_version、approval evidence、requester principal、authority/shard binding 和 trace_id。
- Execution Receipt 至少包含 resulting_generation、resulting_state、stable result/error、audit reference 和外部 Provider 对账状态。
- backend 可以保存控制面提交、Desired State 和 Command Projection；Vault 必须保存命令接受和执行的权威状态，二者不是双重安全权威。
- 网络失败、Leader 切换或 Provider 结果未知时，命令必须进入明确状态，不能凭超时猜测成功或失败。

### 7.3 Event + Reconciliation 投影

- backend Projection 同时使用 Vault Event Stream 和周期性 Reconciliation 更新。
- Projection 状态至少区分 `DESIRED`、`PENDING`、`OBSERVED`、`DRIFTED` 和 `UNKNOWN`。
- Event 提供实时更新，Reconciliation 负责事件丢失恢复、投影校验和漂移发现。
- 发现 Drift 时不得自动用 backend 状态覆盖 Vault；应生成漂移事实，并按策略发起新 Command 或进入人工处理。
- Vault 不可用时，backend 可以记录用户意图，但不得展示虚假成功或把 Desired State 标记为 Actual State。

## 8. 根信任、Seal/Unseal 与 Tenant 密钥域

### 8.1 分级信任根

- Vault 采用分级硬件信任根模型，支持软件 Authority、HSM、云 KMS、外部 KMS、TPM 和可选 TEE。
- 每个 Key Domain 和 Key Resource 必须记录 assurance level、实际托管位置、执行位置、可导出性和 Provider 证明。
- 生产允许 Software Provider，但必须明确标记为 `software` 保障等级，不得伪装成 HSM/KMS 的硬件不可导出或硬件审计能力。
- 高保障资源可以通过 Guardrail 强制 `hardware` 或 `external_controlled`，禁止静默回退到软件实现。
- TEE 与远程证明是可选高保障能力，不是所有部署的强制基础。

### 8.2 Seal 与自动解封

- Vault Authority 和 Shard 启动时默认处于 `SEALED`。
- `SEALED` 状态只允许最小健康、证明、unseal 和受限恢复接口，不允许 Secret、Transit、私钥签名、PKI、动态凭证或数据面 Capability 操作。
- 日常自动解封通过独立 Root Provider 完成，Root Provider 可以是明确低保障的 Software Root Provider、HSM、云 KMS、TPM 或受控外部 Provider；解封权限必须绑定工作负载身份、部署、区域和可用时的证明条件。
- 明文解封结果只能终止于专用 `Root/Seal Authority` 或 Crypto Authority 的严格 bootstrap 子边界；通用 Provider Host 只能传递 opaque handle、wrapped material 或受限调用结果，不得成为 root 明文中转、缓存或恢复副本。
- 自动解封失败必须 fail-closed，不得回退到环境变量、普通配置文件或普通容器 Secret 中的明文根密钥。
- 软件保障部署仍必须使用明确标识、独立隔离的 Software Root Provider 完成日常自动解封，不能把明文根材料写入普通启动配置；门限恢复份额属于灾难恢复域，不得退化为日常重启时的常规解封凭证。
- 明文解封材料不得进入普通 API、Authority Worker、通用 Provider Host、Vault Delivery Agent、`ns_agent` 或 `ns_backend`。

### 8.3 独立门限灾难恢复

- 正常运行使用 Root Provider 自动解封，灾难恢复使用独立门限恢复域。
- 恢复份额不等于日常根密钥，不得作为普通 API token 或直接解密 Tenant Secret。
- 单个 Vault 管理员、backend 管理员、数据库管理员、云管理员或恢复保管人均不能独立完成根恢复。
- Root Provider 更换、恢复或灾备接管必须提升全局 `root_epoch`，使旧 Authority Capability、Shard Epoch、DEK Cache、Provider Session 和数据面 Capability 失效。
- HYOK Tenant 可以选择平台不可恢复模式；客户丢失外部根密钥时必须明确视为不可逆数据丢失，禁止隐藏平台后门。

## 9. Provider、BYOK/HYOK 与保障等级

### 9.1 能力分类协议与 Provider Host

- Provider 抽象必须按安全能力分类，至少包括 Key Custody/Wrapping、Transit、PKI Issuer、Dynamic Credential、Identity Attestor、Audit Anchor 和 Trusted Time。
- 禁止使用无类型、无限扩展的万能 `execute(action, payload)` 作为长期 Provider 合同。
- Provider 实现必须运行在独立 Provider Host 中，不得加载到 Authority Shard Leader、Crypto Authority、普通 API 进程或 `ns_backend`。
- Provider Host 不拥有 Vault 权威数据库写权限，不签发 Vault Capability，不修改 Vault Policy，只获得当前操作所需的最小 Provider 能力。
- Provider Host 使用独立进程身份、最小网络访问、资源限制和认证版本化 IPC；第三方 Python 包、脚本或客户自定义代码不得进入 Vault 核心 Authority 进程。

### 9.2 Provider Manifest

- 每个 Provider 必须声明 protocol version、capability set、supported algorithms、assurance level、exportability、cacheability、fencing support、idempotency support、reconciliation support、region/locality、maximum TTL 和 failure semantics。
- Provider Manifest 及其部署绑定必须经过平台批准和签名（或等价密码学完整性）验证，并绑定实现版本/制品摘要、协议版本、能力集合、Provider Host 运行身份、允许的网络目标、地域以及 Tenant/Key Domain 作用域；未经批准、签名无效或绑定不一致的 Provider Host 不得获得执行能力。
- Provider Manifest 是能力硬上限，策略只能进一步收紧，不能声明 Provider 实际不具备的保障能力。
- `supports_fencing=false`、`supports_idempotency=false` 或 `supports_reconciliation=false` 等限制必须进入执行和风险模型，不得隐藏。
- Provider 原始错误必须映射为稳定 Vault 错误；详细诊断仅保留在受保护诊断域，不能直接泄漏给外部调用方。
- Provider 升级必须支持协议兼容检查、灰度、回滚和未完成 operation 恢复。

### 9.3 外部副作用与对账

- Provider 外部副作用采用显式 `PREPARE → EXECUTE → CONFIRM/RECONCILE → COMMIT RESULT` 协议。
- 每个外部操作必须具有 operation ID、idempotency key、expected generation、external object ID 和可查询结果接口；Provider 不支持时必须使用串行执行、隔离和人工对账补足。
- Provider 返回结果不确定时必须进入 `EXTERNAL_STATE_UNKNOWN` 或相应风险状态，不得直接标记成功或失败。
- 数据库事务提交成功不能单独证明 HSM、KMS、CA、数据库账号或外部 Provider 操作成功。

### 9.4 Key Origin 与 Export Policy

每个 Key Resource 创建时必须固定：

```text
key_origin:
  vault_generated
  provider_generated
  imported_byok
  external_hyok
  derived

export_policy:
  non_exportable
  public_only
  wrapped_export
  plaintext_export_compatibility
```

- `key_origin`、`export_policy`、保障等级和私密材料曾进入过的安全边界属于不可变安全元数据。
- `non_exportable` 一经确定，平台管理员、租户管理员和后续策略都不得放宽。
- Provider 的不可导出限制是硬上限，Vault 不得通过软件回退模拟导出。
- BYOK 必须通过专用安全导入会话直接进入 Authority 或 Provider Host，优先使用 Provider 导入 token、临时包装公钥、HSM ceremony 或双重包装；不得经过 backend、普通日志或持久化明文暂存。
- HYOK 私密材料始终保留在客户控制的外部 Provider，Vault 只保存引用、能力、状态和证明，不保存隐藏恢复副本。
- 派生 Key 的保障等级、用途和导出能力不得强于父 Key。
- 不可导出 Key 的 Provider 迁移通常通过创建新 Key、双读/双验签/重新加密、显式切换和旧 Key 退役完成，不能为迁移临时打开明文导出。
- 明文导出兼容模式只适用于创建时已明确允许的低保障 Key Class，并必须经过独立 Action、强认证、Vault Security Approval、一次性交付和强审计。

## 10. Key Management

### 10.1 Key Resource 不可变安全属性

- 每个 Key Resource 只能属于一个明确 `key_class`。
- 创建时必须固定 algorithm suite、key usage、exportability、assurance requirement、origin 和 provider binding；这些安全属性在 Key 生命周期内不得修改或放宽。
- Key Rotation 只更换密码学材料，不改变 Key 的算法、用途和安全语义。
- 算法迁移必须创建新的 Key Resource，并通过显式 supersedes/migration 关系完成，不能在同一 Key 下静默更换算法。
- 不同用途必须使用不同 Key：数据加密与签名、DEK wrapping 与 Capability 签发、PKI CA 与 Transit Signing、审计签名与业务签名不得复用同一密钥材料。
- `encrypt/decrypt`、`sign/verify`、`wrap/unwrap` 等互补操作可以属于同一用途类别，但授权可以只授予其中一侧。
- Provider 必须在创建时满足完整算法、用途和保障要求；不允许运行时静默降级或用低保障软件模拟高保障能力。

### 10.2 Key Version 状态机

Key Version 必须使用显式状态机：

```text
GENERATING
  → STAGED
  → PRIMARY
  → DECRYPT_ONLY / VERIFY_ONLY / UNWRAP_ONLY
  → DISABLED
  → PENDING_DESTRUCTION
  → CRYPTO_DESTROYED
```

- `GENERATING` 表示 Provider 操作未完成或结果待确认；Provider 结果未知时保持 `EXTERNAL_STATE_UNKNOWN`，不得直接进入 STAGED。
- `STAGED` 表示材料已创建并完成算法、用途、Provider 能力、公钥/元数据和必要密码学自检，但尚不用于新写操作。
- 每个 Key Resource 任一时刻最多只有一个 `PRIMARY` Key Version。
- `STAGED → PRIMARY` 必须由所属 Shard Leader 原子执行，并绑定 expected primary version、expected key generation、authority epoch 和 idempotency key。
- 切换后旧 Primary 默认只保留历史消费能力：对称 Key 为 `DECRYPT_ONLY`，签名或 MAC Key 为 `VERIFY_ONLY`，Wrapping Key 为 `UNWRAP_ONLY`；旧派生父版本只能在历史解密/验证流程中按固定版本内部使用，不得产生新的长期派生输出。
- 普通数据面调用方不得指定旧版本执行新的加密、签名、MAC 生成、包装或业务派生；管理迁移工具必须使用专门 Action 和授权。
- CA Key/CA Version 在仍承担未过期证书的吊销状态义务时，可以进入专用 `REVOCATION_STATUS_ONLY` 受限状态，仅执行获准的 CRL/状态维护操作，不允许签发新的终端或下级 CA 证书；该例外由 PKI 生命周期约束，不能扩大普通 Signing Key 的历史权限。
- 双写、双签名或 Key Set 只能作为显式迁移机制存在，不能改变普通 Key 的单一 Primary 原则。

### 10.3 Alias 与密码学身份

- Alias 只用于稳定的人类或业务引用，不是密码学身份。
- Ciphertext、Signature、Certificate、Wrapped DEK 和 Audit Event 必须记录实际 Key ID、Key Version 和 Algorithm Suite，不能只记录 Alias。
- Alias 切换必须是版本化、可审计的安全状态变更，不能影响历史密文解密或历史签名验签。

## 11. Secret Management

### 11.1 明文边界与创建路径

- 对 Vault 托管的静态 Secret 和由 Vault 密封交付的凭证，`ns_vault` 是唯一集中式服务端明文处理与授权边界；`provider_direct_nonrecoverable` 仅作为 §14.2 明确限定的 Provider 直交付例外，明文必须直接进入绑定的最终消费端，不得经过其他平台中间服务。
- Secret 创建、导入和读取明文不得经过 `ns_backend.vault`；backend 只管理 metadata、policy、approval、lifecycle、command 和 projection。
- 创建时，用户浏览器/`ns_frontend`、SDK、CLI、Agent 或批准集成必须使用由 Vault 签发或认可、绑定终端 Principal 与目标 Resource 的一次性上传会话直接向 Vault 交付 payload；frontend/backend 服务端不得中转。
- backend、日志、中间件、异常链、指标、追踪和审计均不得接收或保存 Secret 明文。

### 11.2 默认交付策略

- 默认优先使用非明文 API 展示的受控消费方式，包括文件、FD、Unix Socket、Windows Named Pipe、tmpfs、workload injection 和短期消费会话。
- 普通管理后台不得直接展示 Secret 明文。
- 人工明文读取可以存在，但必须是独立高风险 Action，受到显式权限、Vault Security Approval、强认证、一次性/短期交付和强审计控制；Tenant Guardrail 可以完全禁止。
- 环境变量注入只适用于进程启动兼容场景，不应成为动态轮换的首选交付方式。

### 11.3 Envelope Encryption

- Secret 使用标准 Envelope Encryption。
- 每个不可变 Secret Version 使用独立随机 DEK，并通过受批准 AEAD Algorithm Suite 加密完整 payload。
- DEK 由所属 Tenant Key Domain 当前 KEK generation 包装；Vault Authority Storage 保存 ciphertext、wrapped DEK、nonce、algorithm suite、KEK generation、Provider reference 和密文格式版本。
- Tenant KEK Rotation 默认通过 rewrap DEK 完成，不要求立即重新加密全部 Secret ciphertext。
- AEAD AAD 至少绑定 Tenant、Tenant Key Domain、创建该 Version 时的稳定 Project/Namespace ID、Secret ID、Secret Version、Algorithm Suite 和 Ciphertext Format Version；KEK generation、Provider binding 和 wrapped DEK 关系也必须进入同一认证封装或等价完整性证明。
- Secret/Namespace 在同一 Tenant 内移动时，历史 Version 必须继续以创建时 cryptographic scope 验证，不能通过修改当前 Project/Namespace 元数据重写历史 AAD；移动后新建 Version 使用新的当前 scope。无法安全保留该关系时必须通过显式重新加密/迁移创建新资源或新 Version，禁止 metadata-only move。
- AAD 或包装元数据被篡改时必须导致解密失败，禁止宽松兼容或忽略。

### 11.4 DEK 缓存

- 解包后的 DEK 采用按保障等级配置的缓存策略。
- 只有独立 Crypto Authority 可以缓存明文 DEK；backend、普通 API、Agent、SDK 和持久化存储不得缓存 DEK。
- 缓存必须短期、有界、非持久化，并绑定 Tenant Key Domain、Secret Version、KEK Generation、Provider Generation 和 Security Epoch。
- Provider 可以声明 `cacheable=false`，上层策略不得覆盖；HYOK、高敏感和合规 Key Domain 默认禁用缓存。
- 租户冻结、资源禁用、Key Rotation、销毁、Provider 撤销或 epoch 变化必须立即使相关缓存失效。
- 缓存只优化 unwrap，不缓存最终授权；每次 Secret 访问仍必须重新执行身份、策略、资源状态和审计检查。
- Provider 故障期间不得延长缓存 TTL，也不得把缓存转换为无限离线访问能力。

### 11.5 Secret Version 状态机

Secret Version 必须使用显式状态机：

```text
UPLOADING
  → STAGED
  → CURRENT
  → PREVIOUS
  → DISABLED
  → PENDING_DELETION
  → CRYPTO_DESTROYED
```

- Secret 内容不可原地修改，任何变化都创建新的不可变 Version。
- 每个 Secret Resource 任一时刻最多只有一个 `CURRENT` Version。
- `STAGED` 可执行完整性、schema 和授权测试，但不得向普通 workload 交付。
- `STAGED → CURRENT` 必须由 Shard Leader 原子执行，并绑定 expected current version、expected secret generation、authority epoch 和 idempotency key。
- 激活后原 Current 进入 `PREVIOUS`，Secret Generation 提升，旧默认读取 Capability 失效，并产生版本变更事件和强审计。
- 普通读取只能解析并交付 `CURRENT`；调用方不得任意指定历史版本。
- `PREVIOUS` 只能通过专用、限时的迁移、回滚或 break-glass Action 读取。
- 回滚是新的权威状态变更，必须重新校验当前策略、Guardrail、版本可用性并提升 generation；不是数据库指针回退。
- 已密码学销毁的 Version 不得因数据库恢复重新激活。

### 11.6 Secret Payload 与类型

- Secret 基础 payload 是不可变 opaque bytes；`opaque` 类型必须始终存在。
- Vault 同时提供有限、版本化的标准 Secret Type Registry，可覆盖 `key_value`、`username_password`、`tls_bundle`、`ssh_key_pair`、`docker_registry`、`cloud_service_account` 和 `provider_credential` 等常见类型。
- 每个 Secret Version 必须记录 secret type、payload schema version、content type、payload length、受保护完整性元数据和 ciphertext format version；如保存摘要，只能使用 ciphertext/envelope 摘要或受保护、带域分离的 keyed digest，禁止保存可供离线枚举的低熵 Secret 明文哈希。
- Secret type、payload length、schema 和完整性元数据本身可能泄露敏感结构，必须受资源授权、脱敏和最小披露约束，不能默认公开给未获 Secret metadata 权限的主体。
- 完整 Secret Version 始终是密码学、版本和生命周期的最小单位；标准类型不改变独立 DEK、单一 CURRENT 和整体回滚语义。
- 内置解析器必须确定、受限且无代码执行能力；禁止任意对象反序列化、外部实体、自动网络访问、递归压缩包展开和不受限模板执行。
- Secret payload 必须有硬大小上限，防止 Vault 被当作对象存储；具体限额由产品容量和实施计划验证。

### 11.7 字段级读取

- 只有已注册、具有确定 schema 的标准 Secret Type 支持字段级读取；`opaque` 不支持。
- 字段级 Action 和 Capability 可以绑定规范字段标识集合，但字段不成为独立 Resource，也不拥有独立 DEK、Version、CURRENT 状态或生命周期。
- 字段级 Capability 必须同时绑定 Secret ID、实际 Secret Version 或受约束的 CURRENT 解析、Payload Schema Version、Resource Generation、允许字段集合、交付通道和有效期；Schema 或 Generation 变化后不得继续沿用旧字段授权。
- Vault 在受控明文边界内解密完整 payload，再只交付获准字段。
- 不支持任意 JSONPath、XPath 或用户自定义查询语言。
- 字段重命名或语义变化必须通过显式 Schema Version 演进处理，不能把旧字段授权静默映射到新语义。
- 审计记录实际交付的字段标识，不记录字段值。
- 需要独立轮换、销毁或生命周期的内容必须拆分为不同 Secret Resource。
- 高保障 Guardrail 可以禁用字段级解析，要求完整 Payload 直接交付至受控 workload。Agent 若执行模板或格式化，只能接收 Vault 已按字段 Capability 裁剪后的获准字段；除非 Agent 对完整 Payload 本身已获授权，否则不得先取得全量字段再在本地自行裁剪。


### 11.8 静态 Secret 轮换

- 静态 Secret 轮换必须建模为显式、可恢复、可审计的权威流程，不能原地覆盖 CURRENT Payload，也不能只依赖 Scheduler 定时写入新值。
- Rotation Profile/Role 必须固定 Secret Type、生成或获取方式、外部目标 Provider、验证步骤、最大并行度、切换条件、失败补偿、回滚窗口和消费者通知要求。
- 轮换流程至少区分准备新值、更新外部系统、验证新值、创建 STAGED Version、原子激活 CURRENT、限制旧 Version 和清理旧外部凭证等阶段；任何外部副作用不确定时必须进入 reconciliation，而不是盲目重试或切换。
- 只有在外部目标状态、Vault STAGED Version 和必要消费验证均满足策略后，Shard Leader 才能执行 CURRENT 切换。
- 多实例灰度必须通过 workload scope、受控 rollout command 或外部发布编排完成；不得通过长期存在多个 CURRENT、调用方任意固定历史 Version 或把 Vault 扩张为通用配置发布系统实现。
- 回滚必须同时核对 Vault Version 与外部系统真实状态；不能只回退 Vault 指针而保留已经变化的外部密码、Token 或账号状态。

## 12. Transit、Derivation、Random 与 Tokenization

### 12.1 Canonical Ciphertext Envelope

- Transit 默认返回版本化、可认证的 Canonical Ciphertext Envelope，而不是裸密码学输出或 Provider 原生 blob。
- Envelope 至少绑定 Ciphertext Format Version、Tenant Key Domain、Key ID、Key Version、Algorithm Suite、Operation Class、Provider Binding Version、Nonce、Ciphertext/Tag、AAD Binding 和 Derivation Context Binding。
- 普通调用方不得自由提供 AEAD Nonce；自定义 Nonce 必须是独立高级 Action，且受算法约束和 Mandatory Guardrail 控制。
- 调用方 AAD 与 Vault 系统绑定数据必须域分离，不能覆盖 Tenant、Key、Version、Resource 或 Operation Binding。
- Provider 原生 ciphertext blob 只能作为 Envelope 内部字段或明确 Provider-specific 兼容格式，不作为默认公开合同。
- Alias 变化不得影响历史解密；解密根据经过认证的 Envelope 和 Vault Key Metadata 裁决，不能根据调用方提供的算法猜测。
- 未识别或已停止支持的格式必须返回稳定错误，禁止宽松解析、算法探测和降级。
- Transit 不持久化调用方业务明文或完整业务密文，只记录不含敏感内容的操作事实；确需关联摘要时应优先对 Canonical Envelope/ciphertext 计算，或使用受保护、带域分离的 keyed digest，禁止把低熵业务明文的无密钥哈希当作安全脱敏。

### 12.2 Detached Metadata 模式

- 对字段长度、既有协议或硬件格式确有要求的场景，可以显式启用 detached ciphertext + metadata 模式。
- Detached Metadata 必须与 ciphertext 建立不可伪造的认证绑定，错配必须失败。
- Detached 模式不得成为绕过 Canonical Envelope 语义、Key Version 绑定、AAD 或审计的裸密码学接口。

### 12.3 Derivation Profile

- 受控派生必须通过版本化 Derivation Profile 使用，禁止调用方自由选择 KDF Algorithm、Output Length、Salt 编码或 Domain Separation 参数。
- Profile 必须固定 Parent Key Class、KDF、Output Length、Context Schema、Operation Domain、Allowed Usage、Deterministic 属性、最大派生范围/次数/生命周期和 Output Policy。
- Output Policy 包括 `internal_only`、`wrapped_export`、`provider_handle_only` 和受限 `plaintext_export_compatibility`；默认 `internal_only`。
- 派生域至少绑定 Tenant Key Domain、Parent Key ID/Version、Profile ID/Version、Operation Class 和规范化 Context。
- Context 必须使用确定、无歧义编码，禁止简单字符串拼接；敏感 Context 的审计只能记录受保护、带域分离的关联摘要或不可逆受控引用，不得记录原值，也不得使用可被低熵枚举的无密钥哈希。
- 父 Key 为 non-exportable 时禁止 plaintext output；wrapped export 必须同时满足 Key Policy、Guardrail 和 Provider 能力。
- 派生结果不得获得比父 Key 更广用途、更弱保障、更宽导出能力或更长生命周期。
- 需要独立轮换、销毁或长期引用的派生结果必须成为正式 Derived Key Resource。
- Wrapped Export 必须绑定接收主体、目标包装 Key、交付通道、有效期和使用预算。

### 12.4 Random 与 Password Generation

- Vault 必须提供基于受批准密码学随机源或 Provider 的安全随机数和密码生成能力。
- 生成规则必须通过版本化 Generation Profile 表达，固定长度、字符/字节约束、编码、用途和必要的合规限制；调用方不能请求弱随机或不可验证的自定义 RNG。
- 生成结果属于敏感一次性交付内容，不进入日志、指标、审计值或 backend 中转。
- 需要长期保存的生成结果必须显式创建 Secret 或 Key Resource；生成接口本身不隐式持久化。

### 12.5 Deterministic Transform 与 Tokenization

- 确定性能力必须通过独立 `DeterministicTransform` 或 `TokenizationProfile` Resource 提供，不能作为普通 Transit `deterministic=true` 参数。
- Profile 必须固定输入类型与规范化规则、输出格式、算法、Parent Key、Tenant/Project/Namespace、数据域、可逆性、输入风险、生命周期和迁移策略。
- 可逆确定性变换与不可逆 Tokenization 使用不同 Key Class 和 Action。
- 相同 Key 不得跨不同字段、表、客户或业务语义复用同一确定性域。
- Token 默认只在所属 Tenant 和明确数据域内稳定；跨 Project、Namespace 或业务域关联属于高风险显式能力。
- Profile Rotation 必须使用 `PREPARING → DUAL_TRANSFORM → REINDEXING → CUTOVER → RETIRED` 等显式迁移状态，不能静默改变已有 Token。
- 禁止对密码、短 PIN 等低熵认证秘密直接提供普通确定性加密；低熵输入必须经过专门风险限制、速率限制和审批，无法安全控制时拒绝。
- 不支持通用收敛加密、基于明文内容推导数据密钥或跨 Tenant 去重。
- 产品必须明确披露确定性保护会泄露相等关系、频率和可关联性，不能宣称与随机化 AEAD 相同保密性。

## 13. PKI 与证书生命周期

### 13.1 统一 CA Resource

- 内建 CA、HSM-backed CA、云/私有 CA、企业外部 CA 和 HYOK CA 必须统一建模为 CA Resource。
- CA Resource 属于唯一 Tenant、Project、Namespace 和显式 Trust Domain。
- Trust Domain 采用受约束树形层级：Root CA → Intermediate CA → Issuing CA/Certificate Role；不允许任意 CA 图或跨 Tenant 长期交叉信任。
- Root CA 默认离线或高保障托管，不承担普通在线签发；日常签发由 Intermediate 或 Issuing CA 完成。
- CA 私钥默认不可导出；SSH CA 与 X.509 CA 可以复用生命周期和策略框架，但不得共用同一密钥。
- 交叉签名仅允许作为显式、限时、可审计的迁移关系。

### 13.2 CA Version 与 Provider

- 每个 CA Version 固定算法、Key Usage、Name Constraints、Path Length、允许身份范围、Provider 和 Assurance Level。
- CA Key Version 遵循生成、STAGED、唯一 PRIMARY、禁止旧版本继续签发新证书和显式销毁原则，证书链迁移必须有显式双链或验证窗口。
- 旧 Issuing CA Version 只要仍存在未过期或未完成状态维护的下级证书，就必须保留可验证的吊销状态服务能力：优先使用专用 OCSP Signing Key，CRL 由原 Issuer Key 或经过明确验证的间接 CRL 机制签署；必要时 CA Version 进入 `REVOCATION_STATUS_ONLY`，不得借此继续签发新证书。
- 外部 CA 已签发但 Vault 未确认时必须进入 `EXTERNAL_STATE_UNKNOWN` 并对账，禁止盲目重复签发。
- 证书序列号必须在相应 Issuer Authority 范围内唯一；外部 CA 自行分配时必须保存权威 serial 和 Provider reference。

### 13.3 身份绑定 Certificate Role

- CSR 只证明请求方持有对应私钥，不能证明其有权声明 CSR 中的 Subject、SAN 或 SSH Principal。
- Certificate Role 必须绑定唯一 Tenant、Project、Namespace 和 Trust Domain，并固定证书类型、用途、最大有效期、身份派生规则、允许附加身份、Provider 要求和私钥模式。
- Vault 必须根据联邦 Principal、Principal Binding、Tenant/Project/Namespace、Workload Attestation、Kubernetes ServiceAccount、SPIFFE、已验证 DNS、设备或服务身份派生或严格验证 Subject/SAN/SSH Principal。
- 调用方提交的身份字段必须与 Vault 派生结果完全一致，或属于逐项批准的附加身份集合。
- 通配符、附加 SAN、特殊 EKU 和 SSH Principal 默认拒绝，必须由显式 Guardrail 与 Role 放行。
- 外部 CA 返回后，Vault 必须重新验证 Subject、SAN、KU/EKU、有效期、Issuer、公钥和 Role Version；超出批准内容时不得交付并进入安全对账。

### 13.4 终端私钥模式

Certificate Role 必须固定允许和默认的 `private_key_mode`：

```text
caller_generated
agent_generated
vault_generated_exportable
provider_generated_non_exportable
```

- 默认优先在调用方、Agent、TPM、HSM 或消费边界生成私钥，Vault 默认只处理 CSR/公钥，不接触终端私钥。
- 高保障证书必须允许强制 Provider 内生成且不可导出；调用方不能降级为可导出模式。
- CA、SSH CA、高保障代码签名等权威私钥禁止通过终端私钥交付接口导出。
- Agent 生成私钥时必须绑定具体 workload 和本地交付目标，不能跨 workload 领取或复用。
- Vault 生成可导出终端私钥只作为兼容能力，必须独立 Action、Guardrail 允许、一次性交付、不可普通再次查看、不持久化明文并强审计。交付结果不确定时必须进入显式恢复/撤销状态，不得在无新增审计和授权的情况下重复返回同一私钥。
- 私钥丢失默认通过重新生成和重新签发处理，不以长期备份终端私钥作为默认恢复方式。
- 证书续期是否复用私钥由 Certificate Role 决定；高保障策略可以强制每次轮换私钥。

### 13.5 Certificate Lease 与有效性状态

- 证书状态属于 Vault Authority，CRL、OCSP、Provider 状态和紧急 deny 是传播或外部执行结果。
- 状态至少区分 `PENDING`、`ACTIVE`、`EXPIRED`、`SUSPENDED`、`REVOCATION_PENDING`、`REVOKED` 和 `EXTERNAL_STATE_UNKNOWN`。
- `EXPIRED` 只表示自然到期，`REVOKED` 表示已确认主动吊销，二者不得混淆。
- 短期 workload 证书以短有效期和停止续签为主，但仍必须支持身份冻结、CA 失陷等紧急 deny/吊销能力。
- Server、用户和设备证书支持 CRL、OCSP 或等价状态查询；OCSP 默认使用专用 OCSP Signing Key，不复用 CA 主签名 Key。
- CRL Number 必须单调，旧 Leader 不得在新 epoch 后签发回退编号。
- Certificate Role 必须声明最大有效期、吊销能力、传播机制、最大陈旧窗口、Provider 能力和状态不可用时的 fail-open/fail-closed 策略；高保障环境默认 fail-closed。
- 外部 CA 未确认吊销时不得标记 REVOKED，必须保持 pending/unknown 状态。
- 已吊销证书不得因数据库恢复、时间回拨、CA 切换或 Provider 异常重新变为 ACTIVE。
- CA Version 或其状态签名能力在仍有依赖证书、CRL/OCSP 新鲜度义务或未完成吊销对账时不得销毁；销毁前必须证明所有依赖已过期、迁移或由等价状态服务安全接管。
- Principal Binding、父 Lease、Namespace 或 Tenant 失效时，必须按 Certificate Role/Guardrail 立即停止续签，并可触发可审计的批量紧急 deny 或吊销流程。

## 14. Dynamic Credentials 与 Lease

### 14.1 Lease 是权威资源

- Lease 是 `ns_vault` 的正式权威资源，不是客户端本地 TTL 或 Provider 原生引用的简单投影。
- Lease 使用稳定、不透明 ID，并采用显式状态机：`PENDING → ACTIVE ↔ RENEWING → EXPIRED`，或 `ACTIVE → REVOCATION_PENDING/REVOKING → REVOKED → CLEANED`；Provider 结果不确定时可以进入 `REVOCATION_FAILED` 或 `EXTERNAL_STATE_UNKNOWN`，不得把这些状态压缩成单一布尔值。
- Lease 创建、续期、撤销、到期、级联和清理必须由所属 Authority Shard Leader 权威写入。
- Lease 至少绑定 Tenant/Project/Namespace、principal、workload、Credential Role/Resource、Provider、Shard/Epoch、Capability Reference、issue time、当前 TTL、最大总寿命、renewable、renewal budget、parent Lease、Provider External ID 和 Lease Generation。
- 支持 Workload Session Lease 及其下的 Database Credential、Certificate、Cloud Credential 等父子 Lease；父 Lease、身份绑定、Tenant 或 Namespace 失效时可按策略级联撤销。
- 续期不是简单延长 expires_at；每次续期必须重新校验身份、Policy、Guardrail、Resource Generation、Provider、最大寿命、认证强度、审批和时间可信等级。
- 续期必须使用 lease generation + renewal ID 实现幂等和并发控制。
- `EXPIRED` 表示 Vault 不再承认有效；`REVOKED` 表示主动撤销已经确认；Provider 无法确认时必须进入 `REVOCATION_PENDING`、`REVOCATION_FAILED` 或 `EXTERNAL_STATE_UNKNOWN`。
- Agent 只能代表原绑定 workload 请求续期，不能改变主体、权限范围或最大总寿命。
- Lease Capability 默认不可转让，必须绑定原 principal、workload 和交付通道；仅持有 Lease ID 或 Provider External ID 不构成使用、续期或撤销权限。
- 高风险动态凭证无法确认 Provider 撤销或清理结果时，必须告警，并可按 Guardrail 暂停相应 Credential Role、Provider Binding 或 Tenant Key Domain 的新签发，不能继续累积未知外部身份。

### 14.2 动态凭证交付

- 动态凭证不自动转化为普通 Secret Resource，而作为 Lease 的临时密封交付材料。
- 每次凭证签发使用独立 Delivery DEK 加密，并绑定 Lease ID/Generation、principal、workload、Credential Role Version、Provider External ID、Delivery Channel、Expiration、交付次数和格式版本。
- 默认交付模式为 `one_time`；只有 Role 明确允许时才可 `bounded_redelivery`。
- 重复交付必须重新认证、重新授权、保持原主体/权限/寿命，并产生强审计。
- 仅凭 Lease ID 不足以领取凭证；必须绑定特定 mTLS 会话、Agent 本地通道、一次性 SDK 会话或 workload attestation。
- Lease 到期、撤销、父 Lease 失效或主体冻结后必须销毁 Delivery DEK 并清理相关缓存。
- Provider 创建成功但交付结果不确定时，必须优先对账或受控重交付，不得盲目创建第二份凭证。
- Provider 只支持不可恢复交付时，可以声明 `provider_direct_nonrecoverable`；交付失败后必须撤销并重新创建。

### 14.3 Provider Issuance Mode

Credential Role 必须显式声明：

```text
per_lease_identity
provider_native_session
exclusive_pool
rotated_shared_compatibility
```

- `per_lease_identity` 和 `provider_native_session` 是正式动态凭证优先模式。
- `exclusive_pool` 中每个成员同一时刻最多绑定一个活动 Lease；回收前必须清理权限、终止会话、轮换认证材料、完成 Provider 对账和必要隔离期。
- 无法证明清理完成的池成员必须进入 `QUARANTINED`，不得重新分配。
- `rotated_shared_compatibility` 只用于无法支持临时身份的遗留 Provider，必须明确披露无法单 Lease 精确撤销、共享爆炸半径和 Provider 审计限制；不得宣传为高保障动态凭证。
- Provider Manifest 是 issuance mode 能力上限；Role 不得配置 Provider 不支持的模式。
- 不同 Lease 不得因性能优化而静默共享同一活动 Provider Session 或凭证值。
- Provider 对象清理失败时，Lease 不得标记为安全清理完成。

## 15. Agent、本地交付与客户端集成

### 15.1 正式但可选的 Vault Delivery Agent

- Vault 提供正式但可选的本地交付平面，可部署为主机级 Vault Delivery Agent、应用 Sidecar、Kubernetes CSI 类适配、Windows Service、本地 Unix Socket/Named Pipe 服务或一次性注入进程。
- 本文中的 Vault Delivery Agent 是 Vault 本地秘密交付组件，不是项目中的 `ns_node` 或未来 `ns_agent`，不得占用 `src/ns_agent` 产品边界，也不得借用 Node Principal 代表 workload；SDK、CLI 和直接 API 仍是一等接入方式，Delivery Agent 不是 Vault 正确运行的强制依赖。
- Agent、SDK 和直接 API 必须使用同一身份、Capability、Resource、Policy、Lease 和 Audit 合同，不得形成 Agent 专属安全旁路。
- Agent 可以执行 workload identity 证明、Capability Exchange、Secret/Certificate/Dynamic Credential 交付、Lease 续期、原子文件替换、轮换通知、受控 reload hook、网络重试和策略允许的短期缓存。
- Agent 不是 Authority：不得签发 Vault Capability、执行最终授权、持有 Tenant KEK/Root Key、修改 Vault 权威状态、延长 Lease 或把一个 workload 的权限转给另一个 workload。
- 主机级 Agent 必须依据操作系统身份、进程凭证、cgroup/container identity 或等价可信事实隔离本地调用方，不能只信任调用方自报名称。
- Agent 默认使用受保护本地通道，不公开监听网络接口。
- Vault 不可达时，Agent 只能在原 Capability、Lease 和缓存 TTL 剩余范围内按策略继续服务，不得自行续期或无限离线运行。
- Agent 日志、指标、诊断包和崩溃转储不得包含 Secret、私钥或可重放凭证。
- Agent 文件交付必须使用受限临时文件、预先设置最小权限、必要的持久化同步和原子替换，禁止把部分写入、宽权限临时文件或跨 workload 可见路径暴露为正式 Secret。

### 15.2 `ns_client`

- `ns_client` 是按主体类型提供模式的统一安全客户端体系，至少支持 human、service、workload、node 和 external client。
- `ns_client` 可以负责身份适配、Capability 生命周期、Lease 管理、Secret/Certificate 消费、Transit 调用、错误映射和审计上下文传递。
- `ns_client` 不是 Agent 和 Authority，不保存根密钥、不提升权限、不代表其他 Principal，也不得建立超出 Guardrail 的本地缓存。
- 各语言或运行形态客户端必须遵守同一 canonical contract 和 stable error，不得形成不同授权语义。

### 15.3 `ns_runtime` 集成

- `ns_runtime` 不持有长期 Vault Credential、Tenant KEK、Provider 主能力或生产根材料。
- `ns_runtime` 通过现有 Authority Broker 完成 runtime 身份证明和 Vault Capability Exchange；Broker 是 bootstrap/trust 入口，不是 Secret 明文代理和 Vault 最终授权者。
- 获得短期、范围受限 Capability 后，runtime 数据面可以按策略直接访问 Vault，避免 Broker 成为 Secret/Transit 吞吐代理。
- Runtime Capability 必须绑定 runtime identity、workload、Tenant、Resource、Action、Generation 和 Expiry。
- 该集成不得削弱现有 `ns_runtime` Authority Broker、Authority Attestor、root trust、FD/受限句柄传递、composition root、显式依赖和普通 runtime 不持有根密钥的边界。

### 15.4 `ns_node` 集成

- `ns_node` 在 Vault 中是独立 `node` Principal，不是普通 workload，也不是 Vault Agent。
- `ns_node` 只能代表自身 node identity 获取 node-scoped Secret、Certificate 或 Capability，不能代表其承载的 workload 获取业务 Secret。
- Workload 必须使用自己的 workload identity、Principal Binding 和 Capability；不得借用 node identity。
- Node Capability 必须绑定 node ID、host ID、node role、Tenant/environment、Resource Scope、Generation 和 Time Limit。
- 一台 Host 可以承载多个独立 `ns_node`；不同 node ID 必须具有独立 Principal Binding 和 Capability，不能因共享 host ID、进程账户或本地 Agent 而共享 node-scoped Secret。
- 如未来存在 host-scoped Secret，必须建模为独立 Host Resource/Action，不得通过 node-scoped 授权隐式扩大。
- Node 被攻破后的影响目标必须限制在该节点自身已获授权的 node-scoped 能力，不能扩散到节点上所有 workload 或整个 Tenant。
- `ns_node` 的 bootstrap、节点身份证明与 Vault Capability Exchange 必须通过专用 Node Authority Broker；TPM、节点证书、云实例身份和企业节点登记是 Broker 可验证的 evidence source，而不是绕过 Broker 的平行授权入口。Vault 始终保持最终授权，Broker 不签发数据面 Vault Capability。
- Vault 兼容不得绕过 `ns_node` 已冻结的进程边界：所有对外 Vault 网络通信必须经 `ns_node` 专用通信进程及受认证本地 IPC/FD 路径完成，调度主进程、OCR、浏览器自动化、桌面自动化和插件执行进程不得自行建立 Vault 网络连接、继承 Node Capability 或隐式取得 node-scoped Secret。通信进程只承担传输和受控交付，不成为 Vault Authority；这些独立进程如需业务 Secret，必须使用各自明确的 workload/service Principal。

## 16. 强审计、时间与可观测性

### 16.1 强审计权威

- Vault 强审计原始事实属于 `ns_vault`，不属于 `ns_backend`。
- 每个 Authority Shard 维护独立、单调、密码学链接的审计序列；事件至少绑定前序 hash、当前 hash、Shard ID、Authority Epoch、序号、签名 Key Generation 和时间可信等级。
- Vault 定期生成签名审计 Checkpoint，并发送至独立不可变审计域，例如 WORM/Object Lock、独立 SIEM、独立审计集群、客户审计端点、透明日志或离线锚点。
- 外部 Anchor 至少保存 Shard、Epoch、Sequence Range、Chain Head Hash、Checkpoint Signature、Signing Key Generation、Anchor Time 和 Receipt。
- Leader 切换必须记录旧链尾、新 epoch 和接管证明，不得静默开启新链。
- 验证工具必须能够检测事件缺失、重排、篡改、epoch 断裂、签名 Key 异常轮换、数据库历史回滚和外部 Anchor 不一致。
- backend 只保存审计 Projection 和检索索引，不能覆盖或删除 Vault 原始审计事实。

### 16.2 审计内容与失败语义

- 审计不得包含 Secret 明文、DEK、KEK、私钥、完整动态凭证、可重放 bearer token 或 Provider 主凭证。
- 对敏感标识可以使用受保护、租户/用途域分离的 keyed digest、字段分级或租户脱敏以保留事件关联能力；禁止把低熵 Secret、身份或业务标识的普通无密钥哈希当作安全匿名化。无法安全关联时应完全脱敏。
- 高风险操作无法可靠写入本地强审计时必须 fail-closed。
- 高频数据面可以使用 Authority 控制的可靠、有界审计缓冲或事务 outbox，但不得静默丢弃；缓冲耗尽必须 backpressure 或拒绝。
- 外部 Anchor 短暂不可用时，可以在策略限定的未锚定窗口内继续；超过窗口后按 Assurance/Guardrail 拒绝相关操作。
- 对 Authority State 的成功变更必须与本地持久审计意图建立不可分割关联，不能出现“状态已改但没有任何可恢复审计事实”。

### 16.3 可信时间

- Vault 采用 Wall Time 与 Monotonic Security Time 双轨模型，并支持外部可信时间证明。
- 时间可信状态至少分为 `TRUSTED`、`BOUNDED`、`DEGRADED` 和 `UNTRUSTED`。
- Capability、Lease、DEK Cache、Provider Session、一次性授权和离线预算必须使用不可回退的单调计时或等价安全语义。
- Wall Time 用于证书有效期、外部 token 校验、合规审计、跨系统关联和用户展示，并必须附带可信等级和偏差界限。
- 高保障部署可以使用 NTS、HSM 安全时钟、TPM 单调计数、云 Provider 时间证明、外部时间戳或审计域锚点。
- 已到期、已撤销或已消费对象不得因时钟回拨重新生效。
- 快照回滚、显著时间倒退、单调基线断裂或时间源严重冲突时，Shard 必须进入 `TIME_UNTRUSTED`，禁止签发新的长期 Capability、证书和动态凭证。
- 时间敏感操作必须声明最低时间可信等级：Capability 和动态凭证签发至少要求 `BOUNDED`，证书签发通常要求 `TRUSTED` 或严格受限的 `BOUNDED`，销毁、break-glass 和根恢复必须要求可信时间或由独立门限证据显式覆盖；公开验签和非敏感读取可以在策略允许的 `DEGRADED` 状态继续。
- Leader 切换必须恢复最后可信 Wall Time 下界、已消耗 TTL、审计序号和 Authority Epoch。
- 时间异常与恢复必须进入强审计，恢复不得补回异常期间已经消耗的有效期。

### 16.4 日志、指标与诊断

- 日志、指标、Trace、健康状态和诊断包必须默认脱敏，不能包含 Secret、Key Material、CSR 私密字段、Token、Provider Credential 或完整 Payload。
- 健康和状态接口必须能够表达 SEALED、TIME_UNTRUSTED、AUDIT_DEGRADED、PROVIDER_DEGRADED、RECONCILIATION_REQUIRED 和只读/拒绝状态，但不得泄露租户敏感资源内容。
- 观测数据不能成为权威状态，也不能因为追踪便利把敏感 payload 复制到异步系统。
- 日志、指标、Trace 和统计中的关联摘要必须遵循 §16.2 的 keyed/domain-separated 规则；高基数 ResourceRef、Secret 类型、payload length 和外部对象 ID 只有在明确受控维度中才能暴露。

### 16.5 Security Risk Signal、告警与通知

- Vault 必须从权威状态变化和安全事件产生结构化 `Security Risk Signal`，至少覆盖 Seal/Unseal 异常、时间不可信、审计链/锚定异常、Provider 不确定状态、撤销/清理失败、策略或投影漂移、异常高风险访问、灾备/恢复异常和安全门禁降级。
- Risk Signal 必须包含稳定代码、严重级别、Tenant/Resource 受控作用域、关联 Event/Operation、首次/最近发生时间、当前处置状态和去重关联信息，但不得包含 Secret、可重放凭证或未脱敏 Provider 原始错误。
- `ns_vault` 拥有 Risk Signal 的事实与状态；`ns_backend.vault` 负责告警展示、规则编排、通知渠道、值班流转和外部客户可见范围。告警 Projection 或通知回执不是 Vault 安全权威。
- 通知发送失败、告警平台不可用或人员未确认不得删除原 Risk Signal，也不得使 `EXTERNAL_STATE_UNKNOWN`、`TIME_UNTRUSTED`、审计失败或其他 fail-closed 条件自动恢复正常；安全处置与通知交付必须解耦。
- 告警确认、抑制和关闭必须保留 actor、reason、scope、有效期和审计引用；确认告警不等于修复底层安全状态。

## 17. 一致性、分片、数据面执行与高可用

### 17.1 Tenant Key Domain 分片单写

- Vault 采用按 Tenant Key Domain 分片的单写 Authority 模型。
- 每个 Tenant Key Domain 任一时刻只归属于一个 Authority Shard；每个 Shard 任一时刻只有一个有效写 Leader。
- Key、Secret、Lease、Certificate、Provider Binding、销毁和 Policy Artifact 等权威状态变更必须路由到所属 Shard Leader。
- Leader 切换必须提升 `authority_epoch`，旧 Leader、旧命令、旧缓存和旧 Worker Capability 必须被 fencing。
- `authority_epoch + resource_generation + command_id/idempotency_key` 共同参与防重放、并发控制和外部副作用隔离。
- 无法原生接受 fencing token 的 Provider 必须通过 Shard 内串行执行器、幂等记录和对账隔离。
- 跨 Shard 操作必须拆分为显式、可恢复、可审计命令流程，不提供隐式分布式事务。
- 无法确认单一写权威时优先拒绝写入，禁止以双 Leader 或最终一致多写换取可用性。

### 17.2 数据面操作分类

数据面操作分为三类：

1. 公开验证与非敏感查询：公钥读取、验签、证书链验证、非敏感 Metadata 和不涉及权威状态的 Capability 基本校验，可在只读副本执行。
2. 可并行密码学操作：普通 Secret 消费、Transit Encrypt/Decrypt、MAC 和部分签名可由专用 Authority Worker 执行。
3. 状态敏感或高风险操作：人工明文读取、一次性 Secret 消费、动态凭证创建/续期/撤销、证书签发与序列号分配、严格次数签名、Rotation、Provider Migration 和 Destroy 必须由 Leader 串行执行。

- Authority Worker 必须持有绑定 Shard、Authority Epoch、Tenant Key Domain、Resource ID/Generation、Allowed Operations、有效期和预算的短期执行 Capability。
- Worker 不是普通 API 节点，不拥有权威数据库写权限或租户根权威。
- Worker 每次操作必须验证当前 generation/epoch，并可靠提交强审计；失联时不能无限继续服务。任何离线执行预算都必须短期、有界并写入 Capability/Guardrail，高风险和 leader-only 操作在 Leader 或审计权威不可达时立即 fail-closed。
- Resource Policy 可以把可并行操作提升为 leader-only，但不能反向削弱系统或 Provider 强制限制。
- HYOK Provider 的数据面调用默认由 Vault Authority/Worker 发起，不把通用 Provider 主权限下发给客户端。
- 对确需客户端直连云 KMS、HSM Gateway 或外部 Provider 的场景，只能签发 Provider-specific、短期、范围受限且可审计的派生 Grant；该模式不得成为默认数据面路径，也不得绕过 Vault 的资源、策略、generation、撤销和审计语义。
- Provider 直连不得让 `ns_backend`、Vault Delivery Agent 之外的通用平台中间服务或其他未绑定主体接触明文，也不得扩大 §14.2 `provider_direct_nonrecoverable` 的例外范围；Vault 无法验证操作结果、主体/通道绑定或审计完整性时，必须按资源 Guardrail 拒绝或进入明确风险状态。

### 17.3 多区域热备

- Vault 支持多区域热备，但同一 Tenant Key Domain 只具有一个 Home Region 和唯一写权威。
- Home Region 内必须具备 Shard Leader + Replica 的节点级高可用；Secondary Region 可以维护同步副本或 Standby Authority，但不得与 Home Region 同时写同一 Key Domain。
- 多区域热备的架构目标类别是有界复制滞后与分钟级受控接管；具体 RPO/RTO、硬件规格和实际接管耗时只能由实施计划和真实演练确认。
- 灾备切换必须提升 Authority Epoch，fence 旧 Region，重新验证 Capability，重建 Provider Session 并证明审计链连续。
- Secret、Key、Lease、Certificate、Provider State 和 Strong Audit 必须纳入灾备同步范围。
- Lease 恢复必须重新评估 TTL、时间可信度、撤销状态和 Provider 外部状态。
- Provider 不支持跨区域时必须明确披露恢复限制；不能以隐藏 fallback Key 绕过。

### 17.4 分级灾备恢复

灾备恢复状态至少为：

```text
BACKUP_AVAILABLE
  → METADATA_RESTORED
  → PROVIDER_VERIFIED
  → AUTHORITY_RESTORED
  → TRAFFIC_ENABLED
```

- 数据库恢复成功不等于安全状态恢复成功。
- 软件托管 Key 可以通过加密元数据和 wrapped material 在 Standby 恢复，但仍必须经过 Authority 恢复门禁。
- HSM/KMS Key 必须重新认证 Provider、验证 Key 可用性和重建 Session。
- HYOK 必须由客户 Provider 重新授权；平台不得创建隐藏替代 Key。
- Lease 必须与 Provider 对账，未确认时保持 unknown/reconciliation 状态。
- CA 必须验证 Provider、序列连续性和 CRL/OCSP 连续性。
- Audit 必须验证内部链和外部 Anchor。
- 恢复期间必须清理 DEK Cache、重新验证 Capability、重建 Lease 状态并提升 root/authority/provider-session epoch。
- 未通过 Provider 验证的资源不得进入正常数据面。


### 17.5 备份与防回滚恢复边界

- Vault 备份只能包含密文、wrapped key material、受保护元数据、Schema/Policy Artifact、审计检查点及恢复所需引用；不得包含 Secret 明文、未包装 DEK/KEK、Root Key、可导出私钥明文或可重放 Provider 主凭证。
- 备份必须使用独立用途的 Backup Protection Key 或受批准 Provider 进行认证加密，并绑定 deployment/region、backup generation、root/authority epoch、schema version 和创建时间可信等级；备份保护 Key 不得与业务加密、Capability 或审计签名 Key 复用。
- 恢复必须校验外部 Audit Anchor、最后已知 Epoch、单调 Generation 和销毁 Tombstone，检测数据库/备份历史回滚；较旧备份不得覆盖已经确认的撤销、销毁、审计链头或更高 Epoch。
- Secret/Key/Provider 外部状态、HSM Session、HYOK 控制权和动态凭证不会因为备份存在而被视为已恢复，必须按分级灾备流程重新验证和对账。
- 备份保留与清理不得恢复已完成密码学销毁的解密能力；对历史介质无法立即物理擦除时，应依靠独立包装 Key 销毁、保留策略和可验证 Tombstone 终止恢复能力。
- 备份、恢复和恢复演练必须产生 Strong Audit；实际 RPO/RTO 与演练结果只能记录在实施计划和验收日志，不能在本文档中虚构。

## 18. 故障、离线与降级语义

- 故障行为由 Resource Assurance Level 与 Mandatory Guardrail 决定，默认 fail-closed。
- HSM/HYOK、CA、根信任、高价值签名 Key、管理员高敏感 Secret 和高风险动态凭证默认不得在 Authority/Provider 不可用时使用旧缓存继续执行。
- 普通 workload 资源可以在策略明确允许时使用仍有效的 Capability、Lease、受控 Secret 缓存或已建立安全会话继续有限服务。
- 有限继续服务不得创建新 Capability、扩大权限、轮换 Key、续 Lease、读取新资源或延长原有效期。
- 每个可离线资源必须声明 outage mode、max offline duration、cache policy、renewal policy 和 audit requirement。
- Provider 不可用、Audit Sink 不可用、时间不可信、DB 不可用和网络分区必须进入可观测安全状态，不得被统一映射为普通重试错误。
- 禁止自动降级到本地备用 Key、环境变量 Secret、配置文件 Secret 或未批准 Provider。

## 19. 删除、销毁、墓碑与恢复

- 资源生命周期采用多阶段模型，至少区分 `ACTIVE`、`DISABLED`、`PENDING_DELETION`、`TOMBSTONED`、`CRYPTO_DESTROYED` 和 `METADATA_PURGED`。
- `DISABLED` 拒绝新使用但仍可恢复；`PENDING_DELETION` 具有明确恢复窗口；`TOMBSTONED` 永久保留资源身份且禁止 ID 重用。
- `CRYPTO_DESTROYED` 通过销毁 DEK、KEK Generation 或外部 Provider 使用能力使密文不可恢复；`METADATA_PURGED` 只清理允许删除的非必要 Metadata。
- Strong Audit、销毁事实和最小 Tombstone 不随业务密文一起删除。
- 单个 Secret Version 通过销毁其 DEK 实现密码学销毁；整个 Secret 必须覆盖全部 Version DEK。
- Tenant KEK Generation 销毁前必须证明相关 DEK 已 rewrap，或明确批准大范围不可恢复后果。
- 存在有效 Lease、Certificate、Ciphertext Dependency、Migration 或 Recovery Task 时默认拒绝销毁。
- 高影响销毁必须职责分离、独立审批、影响预览、一次性确认和 expected generation。
- 历史备份不得通过恢复重新获得已密码学销毁资源的解密能力。
- 外部 Provider 的销毁结果必须区分 Vault 已完成、Provider 已验证确认和外部声明但无法验证，不得作无法证明的物理擦除承诺。

## 20. 存储、进程、框架与协议合同

### 20.1 分层存储

- Vault 使用分层存储模型，不自研专用数据库引擎。
- Relational Authority DB 保存 Resource Metadata、Key/Secret/Certificate Version Metadata、Policy Artifact、Command、Lease Metadata 和 Provider Binding。
- Security Event Store 保存 append-only Security Event、Audit Chain、Checkpoint 和 Anchor Reference。
- State Store 保存 Shard Coordination、Authority Epoch、Leader/Fencing 和临时协调状态，但不是 Key/Secret Authority。
- Object Storage 只用于 Vault 自身加密备份、审计归档和批准的内部加密归档，不得成为任意客户文件或普通 Secret payload 存储旁路。
- 多存储之间必须定义权威顺序、事务 outbox/恢复关系和 reconciliation；不能因为某个存储恢复成功就宣称全部安全状态已恢复。
- backend 与 Vault 使用独立数据库账号、migration、backup 和 recovery 生命周期；backend ORM 不得访问 Vault Authority Table。

### 20.2 安全域分层进程模型

- Vault 采用安全域分层进程模型，至少区分 API/Protocol Adapter、身份验证与策略预处理、专用 Root/Seal Authority、Shard Leader/Crypto Authority、Authority Worker、Provider Host、Scheduler/Reconciler 和 Audit Writer/Anchor Connector。
- Root/Seal Authority 可以是 Crypto Authority 的严格 bootstrap 子边界，但不得退化为通用 Provider Host；只有该边界能够接收 root 明文解封结果，普通 API、Worker、Scheduler、Audit Writer 和通用 Provider Host 只能持有最小 handle 或受限 capability。
- 独立身份验证或策略预处理层只能验证凭证、规范化 evidence 和准备决策输入；最终资源授权、Policy Artifact 裁决和 Capability 签发必须由 Vault Authority 完成，不能形成第二授权权威。
- 普通 API Layer 负责 REST/gRPC/IPC 适配、身份凭证接收、输入规范化和路由，不持有 Root Key、Tenant KEK 或 Provider 主能力。
- Crypto Authority 负责 Key、Secret、Lease、Transit、Capability 和权威安全裁决。
- Scheduler/Reconciler 负责 Rotation、Lease Expiry、Provider Reconciliation、Audit Anchor Retry 和恢复任务，但不能绕过 Shard Leader 权威状态机。
- Audit Writer 负责审计链、Checkpoint 和外部 Anchor；普通业务路径不得绕过。
- 不把 KMS、Secret、PKI、Lease 和 Identity 拆成互相独立、各自拥有安全状态的微服务；单一 Vault Security Authority 必须保持。

### 20.3 框架边界

- `ns_backend.vault` 继续使用 Django 控制面。
- `ns_vault` 是独立 Python FastAPI/ASGI 安全服务，具有独立启动、数据库、migration、配置和生命周期。
- FastAPI、Pydantic、Protobuf、ORM 或具体 RPC 库只是适配和实现工具，不是长期领域合同权威。
- 具体数据库品牌、消息系统、共识/选主实现、包版本和部署脚本属于实施计划与 ADR 的工程选择，不得在未验证时写成已完成能力。

### 20.4 Canonical Contract 与多协议适配

- Vault 先定义传输无关的 Canonical Domain Contract，再提供外部/控制面 REST、数据面 gRPC、Agent 本地 Unix Socket/Named Pipe、Authority 内部认证 IPC 和 Provider Host 能力协议。
- Canonical Contract 至少统一 Principal、ResourceRef、Action、Command、Query、CryptoOperation、DeliveryOperation、Capability、ApprovalEvidence、ExecutionReceipt、Lease、SecurityEvent 和 StableError。
- REST、gRPC 和 IPC 对同一 Action 必须执行相同身份、Tenant、Policy、Generation、Capability 和 Audit 语义；内部接口不能因内网位置跳过校验。
- 所有有副作用请求必须支持 request ID、idempotency key、expected generation、contract version、trace ID 和必要 Capability/Approval Reference。
- HTTP/gRPC/IPC 状态码只是 StableError 的传输映射；调用方不能依赖原始 Provider 错误或框架异常作为业务合同。
- Provider Host 协议可以拥有独立 schema，但必须映射回具体 Vault Resource、Command、Operation 和 Audit Fact。
- 传输版本和业务合同版本必须分开治理。

### 20.5 Schema Registry 与兼容策略

- API、Command、Event、Policy、Resource、Secret Type、Ciphertext Format、Provider Protocol 和 SDK Contract 必须显式版本化并进入 Schema Registry。
- 每个 Schema 声明 version、compatibility mode、migration path、deprecation policy 和 security impact。
- 支持有限兼容窗口和能力协商，不依赖永久隐式向后兼容。
- 旧版本可以读取或迁移，但禁止继续创建新的弱格式、弱算法或弱语义资源。
- 安全相关变化必须显式升级和审计，不能通过默认值或宽松解析静默改变。
- Migration 必须记录 source version、target version、actor、result 和安全影响。
- Schema Registry 是治理设施，不是安全状态权威；最终可用性和资源状态由 Vault Authority 决定。


### 20.6 ResourceRef 与 SecretRef

- `ResourceRef`、`SecretRef`、`KeyRef`、`CertificateRef` 和 `LeaseRef` 只表达稳定资源定位与受约束版本解析，不是 bearer credential，也不直接授予任何访问权限。
- Reference 必须至少绑定或可解析至 Tenant、Project、Namespace、Resource Type 和稳定 Resource ID；名称和 Alias 只能作为受控解析入口，不能替代权威 ID。
- SecretRef 默认解析 CURRENT，但 Capability 必须绑定解析时的实际 Secret Version/Generation；需要固定历史 Version 的场景必须使用专用迁移、恢复或验证 Action，普通 workload 不得借 Reference 降级到 PREVIOUS。
- Reference 中不得嵌入 Secret 明文、私钥、可重放 Token、Provider 主凭证或其他敏感 payload；Reference 不得通过 URL 查询参数或日志友好字符串泄露敏感定位信息。
- Reference 解析必须重新执行 Tenant、Policy、Generation、Epoch 和 Resource State 校验；缓存、Alias 变化或 backend Projection 不得把失效 Reference 重新变为可用。

## 21. 配额、计量、容量与生产门禁

### 21.1 配额与计量

- Platform Account、Customer Account、Tenant、Project、Namespace 和 Resource Type 可以具有分级配额和计量规则。
- 产品运营、账单和 SLA 归 `ns_backend.vault` 控制面；Vault 产生不可伪造的资源使用、密码学操作、Lease、Provider 和审计计量事实。
- Vault 必须从 Actual State、Execution Receipt、Security Event 和计量事实产生 Tenant/Project/Namespace/Resource Type 范围的状态与统计投影；`ns_backend.vault` 负责仪表盘、趋势和运营查询。异步或近似统计不得参与授权、撤销、硬配额、销毁或 Provider 安全裁决。
- 配额拒绝不能绕过 Guardrail 或变成隐式授权；计量数据不能包含 Secret 或敏感 payload。
- Provider 原生限流和配额必须纳入 Role/Resource 创建校验、运行时 backpressure 和容量规划。

### 21.2 容量模型与性能验证分离

- 设计必须支持通过 Tenant Key Domain Sharding、Stateless API、Authority Worker、Provider Host 和分层存储水平扩展。
- 容量模型应覆盖 Tenant、Project、Namespace、Key、Secret、Version、Lease、Certificate、Audit Event、Transit QPS 和 Provider 并发的数量级与扩展方向，但不把未验证数字写成 SLA。
- Benchmark、P99、吞吐、Provider 限制、部署规格和压测目标属于实施计划；验收日志只记录实际环境和真实结果。
- 不同 Provider 和保障等级可以具有不同性能上限，但不得通过降低安全校验、审计、generation 或 fencing 获得虚假性能。

### 21.3 分级生产启用门禁

- Vault 采用按资源保障等级的生产准入门禁，不使用“整个 Vault 一次上线即全部能力可生产”的单一开关。
- Level 1 基础内部资源至少要求身份、Vault Policy、核心审计、生命周期和备份恢复；可以使用明确标记的软件 Provider。
- Level 2 生产敏感资源要求 HSM、云 KMS 或经验证的等价高保障 Provider，并完成强审计、Rotation 验证、故障处理和 Provider 健康/恢复验证。
- Level 3 高保障资源要求 HSM/HYOK 或等价能力、双人控制、灾备演练、安全测试和 Provider 证明。
- Resource Guardrail 决定准入等级；低等级 Provider 不得承载高等级 Resource。
- 生产启用门禁的实际完成状态属于实施计划和验收日志；本文档只定义最终门禁边界，不宣称任何级别已通过。

## 22. 最终功能域核对清单（非实现状态）

以下条目用于核对最终设计是否完整，不表示当前实现进度、验收状态或工作包完成度；后续设计、实现和审查不得遗漏：

- 独立 `src/ns_vault` FastAPI/ASGI 服务边界与 `src/ns_backend/vault` Django 控制面边界。
- Platform Account、Customer Account、Vault Tenant、Project、Namespace、Resource 统一层级，以及 Tenant Key Domain/平台内部 Authority Resource 的明确非目录作用域。
- 同一 Tenant 内跨 Project/Namespace 访问只通过显式 Grant/Capability，资源移动保留历史 cryptographic scope 并执行 generation、依赖和 Capability 失效门禁。
- Tenant Key Domain、独立 KEK Generation、软件/HSM/KMS/BYOK/HYOK 保障等级，以及禁止绕过 Tenant/Provider 控制的隐藏万能根。
- Seal、Auto-unseal、Root Provider、Threshold Recovery、Root Epoch 和 Break-glass。
- 联邦 human/service/workload/node/device/provider/external/recovery Principal 与 SSO 兼容接口。
- 组件/集成登记、明确 Principal 映射、接入撤销与 Capability/Lease/Session 失效，且登记本身不构成授权。
- Mandatory Guardrail、Delegable Grant、受版本治理且可静态验证的声明式 Policy Intent/Artifact、决策解释和短期 Capability。
- Command、Actual State、Execution Receipt、Security Event、Projection 和 Reconciliation。
- Key Class、固定 Algorithm/Usage/Export、单一 Primary Version、Alias 和显式算法迁移。
- Secret 直接上传、唯一集中式服务端明文权威、受控 `provider_direct_nonrecoverable` 直交付例外、Envelope Encryption、独立 DEK、KEK Rewrap、单一 CURRENT Version。
- Opaque 与标准 Secret Type、字段级 Capability、Payload Size Limit 和安全解析器。
- 默认非明文交付、人工高风险读取、Vault Delivery Agent/Sidecar/CSI/Windows/IPC/FD/tmpfs 交付，且 Delivery Agent 与 `ns_node`、未来 `ns_agent` 产品边界明确分离。
- Transit Canonical Envelope、Detached Metadata、Nonce/AAD/Domain Separation 和稳定错误。
- Random、Password Generation、Derivation Profile、Wrapped Export、Provider Handle 和 Derived Key。
- Deterministic Transform、Tokenization、显式数据域、迁移和收敛加密禁令。
- 统一 CA Resource、Trust Domain Tree、Root/Intermediate/Issuing CA、外部 CA/HYOK CA。
- 旧 CA Version 的 `REVOCATION_STATUS_ONLY` 边界、CRL/OCSP 连续性和依赖证书清零前禁止销毁。
- 身份绑定 Certificate Role、终端私钥模式、短期证书、CRL、OCSP、Emergency Deny 和 SSH CA。
- 权威 Lease、父子 Lease、续期/撤销/清理、Delivery DEK 和动态凭证交付。
- Per-lease Identity、Provider-native Session、Exclusive Pool 和明确标记的 Shared Compatibility。
- Provider Host、Capability Manifest、Fencing/Idempotency/Reconciliation 和 External State Unknown。
- ns_runtime Authority Broker Capability Exchange，保持现有 root trust 和普通 runtime 无根材料边界。
- ns_node 只使用 node identity 访问 node-scoped Secret，不代表承载 workload；Vault 网络 I/O 复用专用通信进程，调度、OCR、浏览器/桌面自动化和插件执行进程不隐式继承 Node Capability。
- ns_client 多 Principal 模式，与 Agent、Broker 和 Authority 职责分离。
- Shard 单写、Authority Epoch、Fencing、Authority Worker 和跨 Shard 显式流程。
- 多区域热备、分级灾备恢复、Provider 验证、Lease 重建和 Audit Chain 连续性。
- Strong Audit Chain、Signed Checkpoint、External Immutable Anchor 和完整性验证工具。
- Security Risk Signal、租户隔离告警、backend 通知编排、告警确认审计与通知失败不改变安全状态。
- 权威事实派生的资源状态/统计 Projection，且统计不参与授权与硬安全裁决。
- Wall/Monotonic 双轨时间、可信时间等级、时间回退和快照恢复防护。
- 多阶段删除、Tombstone、Crypto Destroy、Backup 不可复活和 Provider 销毁证明等级。
- Relational Authority DB、Security Event Store、Coordination State Store 和受限 Object Archive。
- Canonical Contract、多协议适配、Schema Registry、兼容窗口和安全迁移。
- 配额、计量、容量模型、性能验证工作包和 Level 1/2/3 生产安全门禁。
- 静态 Secret Rotation Profile、外部目标更新/验证、STAGED/CURRENT 切换、受控灰度和外部状态回滚。
- Lease 完整权威状态机、不可转让绑定、Provider 撤销失败风险门禁和新签发限制。
- 签名且绑定运行身份/网络/作用域的 Provider Manifest 与 Provider Host 部署完整性验证。
- ResourceRef/SecretRef 的非凭证语义、CURRENT/Version 解析、Generation 绑定和安全缓存失效。
- 认证加密备份、独立 Backup Protection Key、Audit Anchor 防回滚验证和密码学销毁不可复活。
- 优先复用 `ns_common`、`ns_backend.iam`、`ns_runtime` Authority/Attestation 等现有公共设施，且不共享 Vault 安全权威。

## 23. 边界闭合说明

- 本文档已经描述 `ns_vault` 的完整最终产品、安全、功能、集成、可用性、灾备、兼容与生产门禁边界。
- 具体 API 字段、数据库表、Python 包版本、选主实现、数据库品牌、部署脚本、性能数字、测试工具和工作包内部排序属于实施计划、工作包或后续工程文档；只有这些选择会改变长期权威、安全或兼容边界时才需要新增或替代 ADR，且任何细化都不能反向削弱本文档。
- 当前仓库是否已经实现某项能力、是否存在可迁移秘密、是否通过某项测试或是否可投入生产，不属于本文档的结论；只能由实施计划和验收日志提供真实状态。
