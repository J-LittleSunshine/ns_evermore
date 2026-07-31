# ns_vault 长期架构决策

> 文档版本：`0.0.1`
>
> 设计边界：[ns_vault_design_checklist_0.0.1.md](ns_vault_design_checklist_0.0.1.md)
>
> 当前状态与执行入口：[ns_vault_implementation_plan_for_design_0.0.1.md](ns_vault_implementation_plan_for_design_0.0.1.md)
>
> 历史验收证据：[ns_vault_acceptance_log_0.0.1.md](ns_vault_acceptance_log_0.0.1.md)

本文档只记录会长期约束 `ns_vault` 产品、安全、数据、协议、部署与组件协作边界的架构决策，不记录当前实现进度、代码快照、测试数量、性能结果或生产就绪结论。

当本文档与设计边界文档冲突时，以 `ns_vault_design_checklist_0.0.1.md` 为准。实施计划只能把已接受决策拆成工作包，不能用阶段成本、现有实现或临时方案静默改变 ADR。验收日志只能记录已经发生的事实，不能新增、解释或替代架构决策。

本文档中的“关联实施层”只用于说明长期依赖位置，不表示对应能力已经实现或通过验收。

## ADR 状态

| 状态 | 含义 |
|---|---|
| `ACCEPTED` | 已接受并长期约束后续设计、实施和审查；修改时必须新增替代 ADR 或显式更新版本 |
| `PROVISIONAL` | 已冻结禁止自行推断的边界，但最终长期语义尚未完成决策；后续工作包不得自行补全 |
| `SUPERSEDED` | 已被后续 ADR 明确替代；原决策必须保留以维持追溯 |

本版本中的 ADR 均为 `ACCEPTED`。数据库品牌、选主库、表结构、具体 API 字段、Python 包版本、部署脚本和性能数字等尚未锁定事项属于受这些 ADR 约束的实施选择，不构成未决架构语义，也不应伪装成 `PROVISIONAL` 决策。

## 决策索引

| ADR | 标题 | 状态 |
|---|---|---|
| [ADR-001](#adr-001) | 完整企业安全平台范围与明确非目标 | `ACCEPTED` |
| [ADR-002](#adr-002) | ns_backend 控制面与 ns_vault 安全执行权威分离 | `ACCEPTED` |
| [ADR-003](#adr-003) | 优先复用现有公共设施但不共享安全权威 | `ACCEPTED` |
| [ADR-004](#adr-004) | 显式 Composition Root、无全局可变状态与框架隔离 | `ACCEPTED` |
| [ADR-005](#adr-005) | backend 失陷后的独立授权安全目标 | `ACCEPTED` |
| [ADR-006](#adr-006) | 分层 SaaS 账户模型与 Tenant 安全边界 | `ACCEPTED` |
| [ADR-007](#adr-007) | 固定 Tenant/Project/Namespace/Resource 层级 | `ACCEPTED` |
| [ADR-008](#adr-008) | 每租户独立 Tenant Key Domain | `ACCEPTED` |
| [ADR-009](#adr-009) | 联邦身份认证与显式 Principal 类型 | `ACCEPTED` |
| [ADR-010](#adr-010) | 未来 SSO 只提供认证事实 | `ACCEPTED` |
| [ADR-011](#adr-011) | 统一 Workload Identity Federation 与 Attestation Binding | `ACCEPTED` |
| [ADR-012](#adr-012) | Mandatory Guardrail 与 Delegable Grant 分层策略 | `ACCEPTED` |
| [ADR-013](#adr-013) | Policy Intent 与 Vault Policy Artifact 分离 | `ACCEPTED` |
| [ADR-014](#adr-014) | 完整策略决策后签发短期 Scoped Capability | `ACCEPTED` |
| [ADR-015](#adr-015) | 普通控制审批与 Vault Security Approval 分层 | `ACCEPTED` |
| [ADR-016](#adr-016) | 门限式 Break-glass 恢复域 | `ACCEPTED` |
| [ADR-017](#adr-017) | Command、Actual State、Receipt、Event 与 Projection 分离 | `ACCEPTED` |
| [ADR-018](#adr-018) | Event + Reconciliation 的 backend 投影同步 | `ACCEPTED` |
| [ADR-019](#adr-019) | 分级软件、硬件与外部控制信任根 | `ACCEPTED` |
| [ADR-020](#adr-020) | Root Provider 自动解封与独立门限恢复 | `ACCEPTED` |
| [ADR-021](#adr-021) | 能力分类协议与隔离 Provider Host | `ACCEPTED` |
| [ADR-022](#adr-022) | 签名 Provider Manifest 与能力硬上限 | `ACCEPTED` |
| [ADR-023](#adr-023) | Provider 外部副作用的显式对账协议 | `ACCEPTED` |
| [ADR-024](#adr-024) | Key Origin 与 Export Policy 创建时固定 | `ACCEPTED` |
| [ADR-025](#adr-025) | Key Class、算法、用途和 Provider 绑定不可变 | `ACCEPTED` |
| [ADR-026](#adr-026) | Key Version 显式状态机与唯一 Primary | `ACCEPTED` |
| [ADR-027](#adr-027) | Vault 是唯一集中式服务端 Secret 明文权威且默认非明文交付 | `ACCEPTED` |
| [ADR-028](#adr-028) | 每 Secret Version 独立 DEK 的 Envelope Encryption | `ACCEPTED` |
| [ADR-029](#adr-029) | 按保障等级控制 Authority 内 DEK 缓存 | `ACCEPTED` |
| [ADR-030](#adr-030) | Secret Version 显式状态机与唯一 Current | `ACCEPTED` |
| [ADR-031](#adr-031) | Opaque Payload 与有限标准 Secret Type Registry | `ACCEPTED` |
| [ADR-032](#adr-032) | 标准 Secret 的字段级 Action 但字段不是资源 | `ACCEPTED` |
| [ADR-033](#adr-033) | 静态 Secret 轮换是受控外部副作用流程 | `ACCEPTED` |
| [ADR-034](#adr-034) | Transit Canonical Ciphertext Envelope 与受控 Detached Metadata | `ACCEPTED` |
| [ADR-035](#adr-035) | 版本化 Derivation Profile 与分级输出 | `ACCEPTED` |
| [ADR-036](#adr-036) | 版本化 Random 与 Password Generation Profile | `ACCEPTED` |
| [ADR-037](#adr-037) | 确定性变换与 Tokenization 作为独立高风险资源 | `ACCEPTED` |
| [ADR-038](#adr-038) | 统一 CA Resource 与受约束 Trust Domain 树 | `ACCEPTED` |
| [ADR-039](#adr-039) | 证书身份由 Vault 绑定和派生 | `ACCEPTED` |
| [ADR-040](#adr-040) | 按证书用途与保障等级选择私钥生成模式 | `ACCEPTED` |
| [ADR-041](#adr-041) | 证书权威状态与多机制吊销传播 | `ACCEPTED` |
| [ADR-042](#adr-042) | Lease 是 Vault 权威、可续期、可撤销的分层资源 | `ACCEPTED` |
| [ADR-043](#adr-043) | 动态凭证使用 Lease 级临时密封交付包 | `ACCEPTED` |
| [ADR-044](#adr-044) | 按 Provider 能力分级的动态凭证签发模式 | `ACCEPTED` |
| [ADR-045](#adr-045) | 正式但可选的 Vault Delivery Agent 本地交付平面 | `ACCEPTED` |
| [ADR-046](#adr-046) | ns_client 按 Principal 类型提供统一安全 SDK 模式 | `ACCEPTED` |
| [ADR-047](#adr-047) | ns_runtime 经 Authority Broker 获得 Capability 后按策略直连数据面 | `ACCEPTED` |
| [ADR-048](#adr-048) | ns_node 是独立 Node Principal 且只访问 node-scoped Secret | `ACCEPTED` |
| [ADR-049](#adr-049) | Shard 密码学审计链与外部不可变锚定 | `ACCEPTED` |
| [ADR-050](#adr-050) | 敏感观测、诊断、稳定错误与安全告警边界 | `ACCEPTED` |
| [ADR-051](#adr-051) | 墙上时间、单调安全时间与可信时间证明双轨 | `ACCEPTED` |
| [ADR-052](#adr-052) | Tenant Key Domain 分片的单写权威 | `ACCEPTED` |
| [ADR-053](#adr-053) | 数据面按操作风险分类执行 | `ACCEPTED` |
| [ADR-054](#adr-054) | 每 Key Domain 单 Home Region 的多区域热备 | `ACCEPTED` |
| [ADR-055](#adr-055) | 按资源保障等级的灾备恢复与 Provider 重新验证 | `ACCEPTED` |
| [ADR-056](#adr-056) | 加密备份与防历史回滚恢复 | `ACCEPTED` |
| [ADR-057](#adr-057) | 按资源保障等级策略化故障与离线行为 | `ACCEPTED` |
| [ADR-058](#adr-058) | 多阶段删除、墓碑与显式密码学销毁 | `ACCEPTED` |
| [ADR-059](#adr-059) | 分层 Authority Storage | `ACCEPTED` |
| [ADR-060](#adr-060) | 安全域分层进程模型 | `ACCEPTED` |
| [ADR-061](#adr-061) | Django 控制面与 FastAPI/ASGI Vault 服务 | `ACCEPTED` |
| [ADR-062](#adr-062) | 传输无关 Canonical Contract 与多协议适配 | `ACCEPTED` |
| [ADR-063](#adr-063) | Schema Registry 与显式兼容策略 | `ACCEPTED` |
| [ADR-064](#adr-064) | ResourceRef/SecretRef 是定位符而非凭证 | `ACCEPTED` |
| [ADR-065](#adr-065) | Software Provider 可生产使用但明确低保障 | `ACCEPTED` |
| [ADR-066](#adr-066) | 配额、计量、统计与安全裁决分离 | `ACCEPTED` |
| [ADR-067](#adr-067) | 容量模型与实测指标分离 | `ACCEPTED` |
| [ADR-068](#adr-068) | 按资源保障等级的生产启用门禁 | `ACCEPTED` |
| [ADR-069](#adr-069) | 分层实施顺序不改变最终设计 | `ACCEPTED` |
<a id="adr-001"></a>
## ADR-001：完整企业安全平台范围与明确非目标

- ADR 编号：`ADR-001`
- 状态：`ACCEPTED`
- 背景：ns_vault 同时面向内部组件与外部客户，若只以单一 Secret Store 或 KMS 开始并把 PKI、动态凭证、Lease、工作负载身份等留作相互独立的后续系统，会形成多套资源、授权、审计和生命周期语义；反之，若把所有敏感数据、普通配置、文件和人员密码都纳入，又会失去清晰的安全产品边界。
- 决策：ns_vault 的长期产品范围固定为完整企业密钥、秘密、证书、Transit、动态凭证、Lease、工作负载身份、随机数、密码生成、受控派生、Tokenization、Provider 联邦、BYOK/HYOK 和本地交付平台。内部组件和外部客户共享同一资源、身份、授权、策略、版本、审批、审计、配额和计量模型，并具备资源状态、统计、安全告警和组件/集成接入治理。明确排除普通配置中心、Feature Flag、服务发现、人员密码管理器、浏览器自动填充、通用文件/文档保险箱、通用 BPM/工单引擎、任意业务数据存储、通用收敛加密和跨租户去重。
- 约束与后果：后续实施阶段只能安排先后顺序，不能把未实现能力从最终设计中删除。任何新增资源类型都必须证明属于密钥、秘密、凭证、证书、身份或直接密码学安全能力，而不能仅以“数据敏感”作为进入 Vault 的理由。
- 关联设计边界：设计清单 §1、§22
- 关联实施层：全部实施层

<a id="adr-002"></a>
## ADR-002：ns_backend 控制面与 ns_vault 安全执行权威分离

- ADR 编号：`ADR-002`
- 状态：`ACCEPTED`
- 背景：ns_backend 是平台统一控制面，并固定存在 Django 应用 src/ns_backend/vault；若 backend 同时成为 Secret、Key、Lease、Provider 或密码学执行权威，backend 服务身份、ORM 权限或超级管理员失陷将等价于平台根权威失陷。
- 决策：src/ns_backend/vault 只承担控制面、运营、组件/集成登记、审批入口、Policy Intent、Desired State、Command、资源状态/统计 Projection、安全告警编排与通知、审计查询、配额和计量。src/ns_vault 是独立安全服务，拥有 Actual Security State、Key、Secret、Certificate、Lease、Policy Artifact、Capability、Provider 执行结果、Security Event、Security Risk Signal 和 Strong Audit 的最终权威。backend 不得通过 ORM 或共享数据库直接修改 Vault 权威状态，也不得代理 Secret 明文。
- 约束与后果：backend 发出的命令只是请求，返回成功必须以 Vault Execution Receipt 和 Actual State 为准。backend 数据库恢复不能覆盖 Vault 状态，backend 超级管理员不能天然成为 Vault 超级管理员。组件登记、统计、告警 Projection 或通知回执都不能替代 Principal Binding、Vault 授权、Actual State 或安全处置结果。
- 关联设计边界：设计清单 §1.1、§2.1、§5.5、§7、§20.3
- 关联实施层：Foundation Layer、Platform Integration Layer

<a id="adr-003"></a>
## ADR-003：优先复用现有公共设施但不共享安全权威

- ADR 编号：`ADR-003`
- 状态：`ACCEPTED`
- 背景：ns_evermore 已有 ns_common 配置、异常、日志脱敏、HTTP、ID、Clock、StateStore 抽象，以及 ns_runtime Authority Broker/Attestor、显式依赖和 composition root 边界。重复实现会导致语义竞争；直接复用而不校验安全适用性又可能降低 Vault 约束。
- 决策：ns_vault 必须优先复用或扩展真正通用的 ns_common 能力，并延续 ns_runtime 的显式依赖、Authority 隔离、普通进程不持有根材料和受限句柄传递原则。Vault 专属资源、Policy Artifact、Capability、Lease、Provider 协议、密文格式和强审计不得塞入通用层。现有 AesGcmSecretBox、backend 审计、IAM role、StateStore secret reference 等不能直接替代 Vault 的持久化加密、强审计、授权或根信任。
- 约束与后果：公共设施不足时，先判断是否属于跨组件稳定能力；属于则扩展 ns_common，不属于则留在 ns_vault。复用公共设施不改变 Key、Secret、Lease、Certificate、Provider 和 Strong Audit 的 Vault 权威归属。
- 关联设计边界：设计清单 §3
- 关联实施层：Foundation Layer

<a id="adr-004"></a>
## ADR-004：显式 Composition Root、无全局可变状态与框架隔离

- ADR 编号：`ADR-004`
- 状态：`ACCEPTED`
- 背景：Vault 核心链路同时依赖配置、Identity、Policy、Authority Storage、Provider、Clock、Audit 和 Scheduler。深层模块直接实例化全局单例或让 FastAPI/Pydantic 类型渗透领域状态机会造成隐藏权威、循环依赖和难以验证的测试替换。
- 决策：运行期状态必须归属明确的 service、authority、repository、registry、scheduler、worker、provider host 或 context；禁止模块级全局可变状态。核心依赖由 composition root 显式构造和注入。领域合同、状态机和 Policy 输入输出使用类型明确、传输无关的结构。异步生产代码基于标准 asyncio 语义，FastAPI、gRPC、数据库 ORM 和 Provider SDK 只存在于受控适配边界。
- 约束与后果：深层代码不得直接创建数据库、HTTP、IAM、Provider、Clock 或 Audit 全局实例。测试通过显式依赖和受控 Clock/Provider 替换，不使用 monkey patch 建立安全语义。框架升级不能改变领域合同或 Authority 归属。
- 关联设计边界：设计清单 §3.4、§20.2、§20.3、§20.4
- 关联实施层：Foundation Layer

<a id="adr-005"></a>
## ADR-005：backend 失陷后的独立授权安全目标

- ADR 编号：`ADR-005`
- 状态：`ACCEPTED`
- 背景：控制面可能被攻破。若 Vault 只验证 backend 命令格式或完全信任 backend 提供的角色和授权结论，攻击者可以借合法接口读取 Secret、请求解密/签名、签发证书或生成动态凭证。
- 决策：backend 不是 Vault 数据面授权权威。ns_vault 必须独立校验 principal、tenant、resource、action、Mandatory Guardrail、Delegable Grant、policy version、principal-binding version、resource generation、security epoch、审批证据、时间可信状态、撤销状态、调用预算和防重放条件。backend 只能提交受限命令、身份事实或授权证据。普通 ns_backend 应用进程不得持有可为任意 human/workload/node 主体签发受 Vault 信任 assertion 的根签发能力。
- 约束与后果：backend 控制面应用被攻破后，攻击者最多滥用其当前持有的短期、范围受限、可撤销控制能力，不能仅凭 backend 服务身份获得全平台数据面能力。受信任 IdP/issuer 的签发权威若被攻破，属于独立的身份权威失陷事件；Vault 无法把密码学上有效的伪造 assertion 当作普通 backend 请求识别，因此必须依靠 issuer 隔离、Tenant/audience scope、短 TTL、认证强度、紧急 trust revocation、Guardrail 和高风险审批限制影响。任何内部接口也不得因为位于内网而绕过同一授权模型。
- 关联设计边界：设计清单 §2.1、§6
- 关联实施层：Foundation Layer

<a id="adr-006"></a>
## ADR-006：分层 SaaS 账户模型与 Tenant 安全边界

- ADR 编号：`ADR-006`
- 状态：`ACCEPTED`
- 背景：Customer Account 属于产品运营和合同关系，Vault Tenant 属于密码学隔离。如果把二者等同，会让计费、支持、合同和安全销毁生命周期混为一体；若为外部客户另建第二套资源模型，又会破坏统一平台。
- 决策：账户层级固定为 Platform Account → Customer Account → Vault Tenant → Project → Namespace → Resource。Platform Account 和 Customer Account 管理运营、合同、SLA、配额和客户生命周期；Vault Tenant 是资源归属、Policy、审计和密码学隔离边界。内部业务也通过 Internal Customer Account 映射到同一 Vault Tenant 模型。
- 约束与后果：平台或客户管理员不会因运营身份自动获得 Tenant Secret 或私钥权限。Customer Account 的合并、拆分、停用和计费变化不能隐式重写 Tenant Key Domain 或资源授权。
- 关联设计边界：设计清单 §4.1
- 关联实施层：Foundation Layer、Platform Integration Layer

<a id="adr-007"></a>
## ADR-007：固定 Tenant/Project/Namespace/Resource 层级

- ADR 编号：`ADR-007`
- 状态：`ACCEPTED`
- 背景：扁平资源依赖标签建立安全边界会导致大型租户权限和审计混乱；任意文件夹树又会引入策略继承、移动和路径身份歧义。
- 决策：面向租户的 Key、Secret、Transit、PKI、Dynamic Credential、Provider Binding 等普通产品资源统一归属于固定层级 Tenant → Project → Namespace → Resource。各层使用稳定、不透明 ID；名称只用于展示和检索。Tenant Key Domain 是 Tenant 级安全资源；Root/Seal、内部 Authority Key、Backup Protection、Shard/Region、Audit Anchor 和 Trusted Time Connector 等平台内部资源使用明确的 system/deployment/region/shard 或 Tenant scope，不得伪造 Project/Namespace 或通过普通 Tenant Resource API 暴露。资源不得跨 Tenant 移动，标签不得替代层级安全边界。
- 约束与后果：重命名不改变资源身份、审计或密码学绑定。简单场景可以自动创建 default Project/Namespace，但底层合同不得省略层级。跨 Project/Namespace 访问没有隐式继承，只能由同一 Tenant 内显式 Grant/Guardrail 和精确 Resource/Generation Capability 放行。跨 Project 的 Namespace 迁移或资源移动属于 Shard Leader 串行执行的显式安全状态变化，必须重新授权、generation 提升、Capability 撤销、依赖/Lease/Certificate/Provider Operation 检查和 Strong Audit；资源类型或 Provider 不支持安全迁移时拒绝 metadata-only move。历史密文、签名、证书、wrapped DEK 等制品保留创建时 immutable cryptographic scope，移动后的授权使用当前行政层级，新 Version 才绑定新 scope。
- 关联设计边界：设计清单 §4.2
- 关联实施层：Foundation Layer

<a id="adr-008"></a>
## ADR-008：每租户独立 Tenant Key Domain

- ADR 编号：`ADR-008`
- 状态：`ACCEPTED`
- 背景：平台单一包装根会把所有租户置于同一密码学故障域，也难以支持独立 BYOK、HYOK、迁移、冻结和销毁；完全由每租户自建根又会失去平台托管模式。
- 决策：每个 Vault Tenant 必须拥有独立 Tenant Key Domain，并绑定独立 Tenant KEK 或等价 Provider Key 及 generation。Tenant KEK 可由 Software Authority、HSM、Cloud KMS、BYOK 或 HYOK Provider 承载。Project、Namespace 和资源可以具有进一步受约束的包装或派生边界，但只能属于该唯一 Tenant Key Domain，不能形成任意密钥图；不得跨租户共享底层包装密钥。 平台 Root/Seal 只能保护平台 bootstrap、控制关系或明确的平台托管 Key Domain，不得形成可绕过 Tenant Key Domain、Provider 控制和 Vault Policy 的隐藏万能解密根；`external_controlled`/HYOK 资源必须保持客户 Provider 控制。
- 约束与后果：单租户 KEK 泄露原则上不得导致其他租户解密。租户可以独立轮换、rewrap、迁移、冻结和密码学销毁。跨租户协作只能通过显式服务调用或密文交换，不得通过共享根或共享活动 Provider Session 实现。
- 关联设计边界：设计清单 §4.3、§8、§9
- 关联实施层：Foundation Layer、Core Security Layer

<a id="adr-009"></a>
## ADR-009：联邦身份认证与显式 Principal 类型

- ADR 编号：`ADR-009`
- 状态：`ACCEPTED`
- 背景：Vault 自建完整用户目录会与 ns_backend IAM 和未来 SSO 重复；完全实时依赖 backend 背书又会让 backend 成为身份冒充权威和数据面单点依赖。
- 决策：ns_vault 使用联邦身份认证并本地验证受信任 issuer、audience、subject、tenant binding、authentication method、assurance level、expiry 和 revocation。Principal 类型至少区分 human、service、workload、node、device、provider、external_customer、recovery；其中 recovery 只属于门限恢复与 Break-glass 域，不得作为日常管理或数据面主体。Vault 维护 Principal Binding 和最终授权，不维护完整企业用户目录。
- 约束与后果：issuer + subject 才构成身份，不能只按名称或 role claim 映射。人员、服务、工作负载、节点、设备和恢复主体不能隐式相互转换。人员/工作负载 assertion 的签发私钥必须由独立 SSO/IdP、隔离 Identity Authority、HSM/KMS 或等价受保护边界持有，不能与普通 ns_backend Web/API 服务凭证等同；backend 提供的未签名 claim、数据库字段或服务间信任头不能直接建立 Principal。受信任 issuer、验证密钥、trust bundle、Principal Binding 和撤销状态的新增、轮换、停用必须版本化、进入 Strong Audit，并按影响范围使旧认证会话或 Capability 失效。backend 的组件/集成登记只是接入意图，不是凭证或授权；每个集成必须映射明确 principal type、issuer/subject、租户作用域和 assurance，禁止跨组件共享通用高权限身份。ns_frontend 仅是 UI/浏览器接入面，不能用自身部署身份继承终端 human/external_customer 权限，Secret payload 必须通过 Vault 认可的终端直连会话交付。数据面优先本地验证短期凭证，不要求每次在线询问 backend。
- 关联设计边界：设计清单 §5.1、§5.2、§5.5
- 关联实施层：Foundation Layer

<a id="adr-010"></a>
## ADR-010：未来 SSO 只提供认证事实

- ADR 编号：`ADR-010`
- 状态：`ACCEPTED`
- 背景：项目后续会设计独立 SSO 服务。本阶段若提前让 SSO role/group 直接决定 Vault 权限，会把尚未设计的 SSO 内部语义固化为 Vault 授权权威。
- 决策：未来 SSO 仅作为 Identity Provider，向 Vault 提供经过验证的 issuer、subject、会话有效性、认证强度、MFA 状态和必要身份属性。SSO role、group、department 不直接转换为 Vault Grant；Vault 通过 Principal Binding、Guardrail、Grant 和 Capability 独立裁决权限。
- 约束与后果：SSO 可以替换或演进而不改变 Vault 资源授权模型。SSO 禁用、会话失效或认证强度变化可影响 Principal Binding 和访问条件，但不能直接写 Vault Policy。
- 关联设计边界：设计清单 §5.3
- 关联实施层：Foundation Layer、Platform Integration Layer

<a id="adr-011"></a>
## ADR-011：统一 Workload Identity Federation 与 Attestation Binding

- ADR 编号：`ADR-011`
- 状态：`ACCEPTED`
- 背景：工作负载可能来自 Kubernetes、SPIFFE、云实例、裸机、ns_runtime、ns_node、TPM/TEE 或外部客户环境，单一长期 API Key 无法证明当前运行实例并会产生密钥分发问题。
- 决策：Vault 建立统一 Workload Identity Federation，支持 OIDC、SPIFFE/SPIRE、Kubernetes ServiceAccount、云 workload identity、mTLS、TPM/TEE、ns_runtime Authority Attestor、ns_node 节点证明和设备证明。高保障资源可要求代码测量、硬件证明、指定节点或更高 assurance level。长期凭证只用于 bootstrap、恢复或受控初始化。
- 约束与后果：身份验证成功后只获得参与 Vault Policy 决策的 Principal Binding，最终由 Vault 签发短期 Capability。原始可重放 evidence 不进入普通审计或长期存储。
- 关联设计边界：设计清单 §5.4
- 关联实施层：Foundation Layer、Platform Integration Layer

<a id="adr-012"></a>
## ADR-012：Mandatory Guardrail 与 Delegable Grant 分层策略

- ADR 编号：`ADR-012`
- 状态：`ACCEPTED`
- 背景：传统父级 allow 向下继承容易意外扩大权限，子级完整覆盖又会绕过租户合规约束；纯 RBAC 难以表达 Provider、地域、时间、认证强度和不可导出条件。
- 决策：授权模型分为 Mandatory Guardrail 和 Delegable Grant。Guardrail 由上级向下强制生效，子级只能收紧；Grant 明确 principal、action、resource scope、condition、继承、再委派深度、有效期和审批。默认拒绝，explicit deny 和 Guardrail 优先于 allow。
- 约束与后果：委派者不能授予超出委派上限的能力。外部身份 claim 只能参与 Principal Binding，不能直接成为 Grant。每次决策必须可解释匹配的 Grant、Guardrail、deny 和使用的版本。
- 关联设计边界：设计清单 §6.1
- 关联实施层：Foundation Layer

<a id="adr-013"></a>
## ADR-013：Policy Intent 与 Vault Policy Artifact 分离

- ADR 编号：`ADR-013`
- 状态：`ACCEPTED`
- 背景：backend 需要提供策略 UI、审批、运营上下文和版本管理，但若 backend 策略文本被 Vault 直接信任，会让 backend 成为数据面策略权威；双向同步则形成双权威。
- 决策：ns_backend.vault 保存 Policy Intent、管理上下文、审批和 intent version；经版本化 Compiler 生成 Vault Policy Artifact。可执行 Artifact 的接受权必须位于 ns_vault 信任边界：Compiler 可以独立部署，但不能仅因由 backend 调用而被信任，必须具有受验证的实现版本/制品身份或在 Vault 内执行；ns_vault 必须独立校验 Artifact schema、source intent/approval、上级 Guardrail、scope、hash 和非扩权性质后再保存和执行。Artifact 记录 source intent version、compiler version、artifact version、scope、hash 和 effective time。 Artifact 必须是受版本治理、可静态验证的声明式 IR，使 Grant、Deny、Guardrail、Scope、Condition 和 Delegation 的权限上界可被 Vault 机械检查；任意脚本、模板代码、动态导入或无法证明权限上界的表达式不得成为可执行 Artifact。
- 约束与后果：编译不得扩大权限，只能等价转换或收紧；无法证明与已批准 Intent/Guardrail 一致时必须拒绝生效。Policy Artifact 生效、回滚和撤销是 Vault 权威状态变化。Intent 与 Artifact 必须可追溯，不允许 backend 直接写 Vault Policy 表、提交任意可执行策略或把 Compiler 变成 backend 的隐式授权权威。
- 关联设计边界：设计清单 §6.2
- 关联实施层：Foundation Layer、Platform Integration Layer

<a id="adr-014"></a>
## ADR-014：完整策略决策后签发短期 Scoped Capability

- ADR 编号：`ADR-014`
- 状态：`ACCEPTED`
- 背景：每次高频数据面操作都执行完整策略解释会成为瓶颈；长期 role/token 又会扩大泄露和撤销窗口，并无法安全授权 Authority Worker、Agent 和 SDK。
- 决策：Vault 完成身份、Guardrail、Grant、deny、资源状态和审批决策后，签发范围更窄的短期 Capability。Capability 绑定 issuer、principal/type、principal-binding version、tenant/project/namespace、resource ID/generation、actions、shard/authority epoch、policy/artifact version、authentication strength、approval reference、expiry、token ID、预算和必要 channel/workload binding。普通 Capability 默认不可委派。
- 约束与后果：Capability 只能缩小已有权限，不携带 Secret、DEK、私钥或 Provider 主凭证。紧急禁用、冻结、销毁可通过 deny list、revocation 或 epoch 提升立即废止旧 Capability。高风险操作执行时仍重新校验当前状态和一次性消费条件。
- 关联设计边界：设计清单 §6.3
- 关联实施层：Foundation Layer、Core Security Layer

<a id="adr-015"></a>
## ADR-015：普通控制审批与 Vault Security Approval 分层

- ADR 编号：`ADR-015`
- 状态：`ACCEPTED`
- 背景：所有操作都进入 Vault 审批会把 Vault 变成通用工作流系统；只依赖 backend 普通审批又不足以保护 Key 导出、明文读取、Guardrail 修改、Root Provider 更换和销毁等高风险动作。
- 决策：普通运营和一般资源编排由 ns_backend 审批。高风险 Vault 操作必须创建 Vault Security Approval，并绑定 operation、resource/generation、request principal、approval identities、认证强度/MFA、时间窗口、职责分离和一次性消费。
- 约束与后果：backend 普通审批不能替代 Security Approval，backend 管理员身份不能自动通过。资源 generation、policy/security epoch 或审批条件变化后必须重新审批。审批只授权指定操作，不产生通用管理员权限。正常审批链路不可用时，只有 ADR-016 定义的门限 Recovery Evidence 能够替代预先声明的紧急恢复 Action 所需 Security Approval，且不得推广到普通高风险操作。
- 关联设计边界：设计清单 §6.4
- 关联实施层：Foundation Layer、Platform Integration Layer

<a id="adr-016"></a>
## ADR-016：门限式 Break-glass 恢复域

- ADR 编号：`ADR-016`
- 状态：`ACCEPTED`
- 背景：正常 SSO/IAM、审批或 Provider 可能同时不可用；完全没有紧急恢复路径可能导致永久不可操作，单管理员紧急 Token 则形成高价值后门。
- 决策：建立独立于日常账户、backend 管理员和 SSO 的门限式 Break-glass 恢复域。多名 Recovery Custodian 通过独立认证和恢复证据创建时间受限、范围受限的 Emergency Session，只能执行预定义恢复操作；其门限证据是紧急恢复专用的独立授权机制，不是普通 Security Approval 的全局旁路。
- 约束与后果：Break-glass 不能导出 non_exportable Key、关闭或删除审计、绕过 Tenant Guardrail、成为永久管理员或修改一般业务授权。所有动作进入 Strong Audit，并需定期演练；演练结果只能在验收日志中记录。
- 关联设计边界：设计清单 §6.5、§8.3
- 关联实施层：Foundation Layer、Production Assurance Layer

<a id="adr-017"></a>
## ADR-017：Command、Actual State、Receipt、Event 与 Projection 分离

- ADR 编号：`ADR-017`
- 状态：`ACCEPTED`
- 背景：Key 轮换、Secret 激活、PKI 签发、Lease 撤销和 Provider 迁移包含长任务、外部副作用和不确定结果，无法用同步 CRUD 或单一事件概念安全表达。
- 决策：控制面提交 versioned Command；Vault Command Store 和 Shard Executor 改变 Actual Security State；产生 Execution Receipt 与不可变 Security Event；backend 维护 Projection。Command 不是 Event，Event 不是 Current State，Projection 不是 Authority。
- 约束与后果：所有副作用命令支持 command_id、command_version、idempotency_key、expected_generation、policy_version、approval evidence、requester principal 和 trace_id。网络超时不能推断失败，必须查询 Receipt、Actual State 或进入 reconciliation。
- 关联设计边界：设计清单 §7.1、§7.2
- 关联实施层：Foundation Layer

<a id="adr-018"></a>
## ADR-018：Event + Reconciliation 的 backend 投影同步

- ADR 编号：`ADR-018`
- 状态：`ACCEPTED`
- 背景：只靠事件推送会在事件丢失或长期网络分区后永久漂移；只靠 pull 会降低实时性；双向修正会让 backend 覆盖安全状态。
- 决策：backend Projection 同时消费 Vault Event Stream 并周期性执行只读 reconciliation。投影状态明确区分 DESIRED、PENDING、OBSERVED、DRIFTED、UNKNOWN。Vault Actual State 始终是唯一安全事实。
- 约束与后果：发现 drift 时不自动覆盖 Vault；根据策略重新发起命令或进入人工处理。Vault 不可用时 backend 可以保存用户意图，但不得展示虚假成功。Projection 不能写回权威状态。
- 关联设计边界：设计清单 §7.3
- 关联实施层：Platform Integration Layer、Production Assurance Layer

<a id="adr-019"></a>
## ADR-019：分级软件、硬件与外部控制信任根

- ADR 编号：`ADR-019`
- 状态：`ACCEPTED`
- 背景：仅软件隔离无法保护主机 root 读取内存；强制所有部署使用 TEE/HSM 又会排除小型、离线和开发场景。
- 决策：Vault 采用分级 assurance model：software、hardware、external_controlled。软件 Authority 可用于生产但明确为较低保障；HSM、Cloud KMS、TPM/TEE 和 HYOK 可提供更高保障。高保障模式下根密钥、关键 KEK 和不可导出私钥不进入普通主机内存，且禁止静默降级到软件。
- 约束与后果：Resource Guardrail 可强制指定最低 assurance level。产品、审计和元数据必须如实标记执行位置、可导出性和管理员可见风险。软件模式不能声称硬件级不可导出或篡改防护。
- 关联设计边界：设计清单 §8.1、§9、§21.3
- 关联实施层：Foundation Layer、Core Security Layer

<a id="adr-020"></a>
## ADR-020：Root Provider 自动解封与独立门限恢复

- ADR 编号：`ADR-020`
- 状态：`ACCEPTED`
- 背景：本地文件或环境变量自动解封会把根密钥置于主机和容器配置域；每次重启人工门限解封又不适合 HA 和大规模 Shard。
- 决策：所有 Authority/Shard 启动时处于 SEALED。日常通过绑定工作负载身份、部署、区域和可用证明条件的 Root Provider 自动解封；失败时 fail-closed，不回退到明文文件、环境变量或普通容器 Secret。软件保障部署也必须使用明确标识且独立隔离的 Software Root Provider，不能把明文根材料写入普通启动配置。独立门限恢复材料只用于替换 Root Provider、重建信任和灾备接管。
- 约束与后果：SEALED 状态只允许健康、证明、解封和受限恢复接口。明文解封结果只能终止于专用 Root/Seal Authority 或 Crypto Authority 的 bootstrap 边界，不得进入普通 API、Authority Worker、通用 Provider Host、Agent 或 ns_backend；通用 Provider Host 可以传递不透明 handle、wrapped material 或受限调用结果，但不能成为根明文的中转和缓存层。Software Root Provider 的自动解封必须依赖明确记录的主机绑定或操作系统保护的 bootstrap 能力，并如实维持“宿主机 root 在信任边界内”的软件保障声明；如果部署环境没有可批准的受保护 bootstrap，节点必须保持 SEALED 或进入门限恢复，不能退回明文文件/环境变量。Root 恢复或 Provider 更换提升 root_epoch，并使旧 Authority Capability、Shard epoch、DEK cache、Provider session 和数据面 Capability 全部失效。HYOK 租户可选择平台不可恢复。
- 关联设计边界：设计清单 §8.2、§8.3
- 关联实施层：Foundation Layer、Production Assurance Layer

<a id="adr-021"></a>
## ADR-021：能力分类协议与隔离 Provider Host

- ADR 编号：`ADR-021`
- 状态：`ACCEPTED`
- 背景：HSM、KMS、CA、数据库、STS、审计锚点和可信时间的语义差异巨大。万能 execute(action,payload) 会失去类型安全；进程内第三方 SDK 会把供应链和解析漏洞带入 Authority。
- 决策：按 Key Custody、Secret Wrapping、Transit、PKI Issuer、Dynamic Credential、Identity Attestor、Audit Anchor、Trusted Time 等安全能力定义版本化 Provider 协议。Provider 实现在独立 Provider Host 中运行，使用认证 IPC、独立身份、最小网络和资源权限，不拥有 Vault 权威 DB 写权限、Policy 修改权或 Capability 签发权。
- 约束与后果：第三方扩展不得加载到 API、Authority 或 Shard Leader 进程。每次 Provider 调用只授予当前 operation、Tenant/Key Domain、resource、epoch 和时间窗口所需的最小能力，Provider Host 不得因连接某个 Provider 而隐式获得其他租户或整个 Provider 账户的通用根权限。Provider Host 崩溃、阻塞和升级不应破坏 Authority。软件密码学实现也必须遵守明确的安全进程边界。
- 关联设计边界：设计清单 §9.1、§20.2
- 关联实施层：Foundation Layer、Core Security Layer

<a id="adr-022"></a>
## ADR-022：签名 Provider Manifest 与能力硬上限

- ADR 编号：`ADR-022`
- 状态：`ACCEPTED`
- 背景：策略若假设 Provider 支持 fencing、幂等、不可导出或特定算法，而实际实现不具备，会形成虚假安全保证；未绑定制品的声明还可被替换实现绕过。
- 决策：每个 Provider 必须提供经过批准并签名或等价完整性保护的 Manifest，绑定实现制品摘要、协议版本、能力集合、算法、assurance、exportability、cacheability、fencing/idempotency/reconciliation 支持、地域、运行身份、网络目标和 Tenant/Key Domain scope。Manifest 声明是硬上限，Policy 只能进一步收紧。
- 约束与后果：Provider 升级需要兼容检查、灰度、回滚和未完成 operation 恢复。supports_fencing=false 等限制必须进入执行和风险模型，不得隐藏或由控制面伪造。
- 关联设计边界：设计清单 §9.2
- 关联实施层：Foundation Layer、Core Security Layer

<a id="adr-023"></a>
## ADR-023：Provider 外部副作用的显式对账协议

- ADR 编号：`ADR-023`
- 状态：`ACCEPTED`
- 背景：数据库用户、云凭证、证书和 HSM object 可能已在 Provider 创建，但网络响应丢失或 Vault 事务失败；数据库事务无法回滚外部副作用。
- 决策：Provider operation 使用 PREPARE → EXECUTE → CONFIRM/RECONCILE → COMMIT RESULT 语义，携带 operation ID、idempotency key、external object ID、fencing/epoch 和可查询结果。PREPARE 及其 operation identity、预期 generation、调用范围和幂等信息必须在发起外部副作用前可靠持久化；Provider 返回或连接中断后，结果/不确定状态必须先写入可恢复 operation state，再向上层确认。不能确认结果时进入 EXTERNAL_STATE_UNKNOWN 或 RECONCILIATION_REQUIRED，不能猜测成功或失败。
- 约束与后果：无原生 fencing/idempotency 的 Provider 必须经 Shard 串行执行器、操作记录和对账隔离。重启、Leader 切换或网络重试必须复用原 operation ID，不得因没有响应而创建第二个外部对象。原始 Provider 错误映射为稳定错误码，详细原因只留在受保护诊断域。
- 关联设计边界：设计清单 §9.3
- 关联实施层：Core Security Layer、Production Assurance Layer

<a id="adr-024"></a>
## ADR-024：Key Origin 与 Export Policy 创建时固定

- ADR 编号：`ADR-024`
- 状态：`ACCEPTED`
- 背景：若管理员可后续把不可导出 Key 改为可导出，HSM、BYOK、HYOK 和软件托管的保障都会被最低模式拉平；自由导出还会失去副本追踪。
- 决策：Key 创建时固定 key_origin：vault_generated、provider_generated、imported_byok、external_hyok、derived；以及 export_policy：non_exportable、public_only、wrapped_export、plaintext_export_compatibility。origin、export policy、assurance 和私密材料曾进入的安全边界是不可变安全元数据。non_exportable 永久不可放宽。
- 约束与后果：BYOK 通过专用安全导入会话直接进入 Authority/Provider Host；HYOK 不保留隐藏恢复副本。plaintext_export_compatibility 不是 read/manage/admin 权限的隐含部分，只能用于创建时已允许的低保障 Key Class，并通过独立 Action、近期高强度认证、Vault Security Approval、一次性交付、直接 Vault 通道和 Strong Audit 执行。不可导出 Key 跨 Provider 迁移采用新 Key、双读/双验签/重加密、切换和旧 Key 退役，而非临时导出。
- 关联设计边界：设计清单 §9.4
- 关联实施层：Core Security Layer、Advanced Security Layer

<a id="adr-025"></a>
## ADR-025：Key Class、算法、用途和 Provider 绑定不可变

- ADR 编号：`ADR-025`
- 状态：`ACCEPTED`
- 背景：同一密钥跨加密、签名、MAC、包装和派生复用会产生跨协议风险；在同一 Key 版本中改变算法会使 Key ID 不再表示稳定密码学含义。
- 决策：每个 Key Resource 只属于一个明确 key_class，并在创建时固定 algorithm_suite、key_usage、exportability、assurance_requirement、origin 和 provider_binding。轮换只更换密码学材料，不改变安全语义。算法迁移必须创建新 Key Resource，并通过显式 supersedes/migration 关系管理。
- 约束与后果：数据加密、签名、DEK wrapping、Capability signing、PKI CA 和 Audit signing 使用不同 Key。Alias 仅是展示/业务引用，密文、签名、证书、wrapped DEK 和审计必须记录实际 key_id、key_version 和 algorithm suite。
- 关联设计边界：设计清单 §10.1、§10.3
- 关联实施层：Core Security Layer

<a id="adr-026"></a>
## ADR-026：Key Version 显式状态机与唯一 Primary

- ADR 编号：`ADR-026`
- 状态：`ACCEPTED`
- 背景：新 Key 生成后立即切换无法验证 Provider 结果和客户端兼容；允许调用方随意选择旧版本会造成长期降级和多个当前写版本。
- 决策：Key Version 状态机固定为 GENERATING → STAGED → PRIMARY → DECRYPT_ONLY/VERIFY_ONLY/UNWRAP_ONLY → DISABLED → PENDING_DESTRUCTION → CRYPTO_DESTROYED，并允许 EXTERNAL_STATE_UNKNOWN。每个 Key 最多一个 PRIMARY。STAGED→PRIMARY 由 Shard Leader 原子执行，绑定 expected primary、key generation、authority epoch 和 idempotency key。
- 约束与后果：普通数据面不能选择旧版本执行新加密、签名、MAC 生成、包装或新派生。旧 Primary 只保留与 Key Class 对应的历史消费能力：例如解密、验签/MAC 校验、解包，或作为历史解密/验证流程内部固定引用的旧派生父版本；不得把旧版本重新用于产生新的长期业务输出。CA Key/CA Version 在仍承担有效证书的吊销状态义务时，可按 ADR-038/ADR-041 进入专用 `REVOCATION_STATUS_ONLY`，只执行 CRL/状态维护，不得签发新证书。Provider 结果不确定时不得提升。双写、双签名或 Key Set 只能作为显式迁移能力。
- 关联设计边界：设计清单 §10.2
- 关联实施层：Core Security Layer

<a id="adr-027"></a>
## ADR-027：Vault 是唯一集中式服务端 Secret 明文权威且默认非明文交付

- ADR 编号：`ADR-027`
- 状态：`ACCEPTED`
- 背景：若 Secret 创建或读取经过 backend，backend 进程、日志、中间件和管理员成为明文截获点；完全禁止任何人工读取又会限制合法运维和外部客户场景。
- 决策：对 Vault 托管的静态 Secret 和由 Vault 密封交付的凭证，ns_vault 是唯一集中式服务端明文处理与授权权威。Secret payload 只能由用户/SDK/CLI/Agent 通过认证的直连上传或交付会话进入 ns_vault，backend 不接收、代理、缓存或展示。默认交付使用 Agent、本地 Socket、FD、Named Pipe、tmpfs、受控文件或短期数据面响应；获授权的 Agent/SDK/workload 是最终消费端，不因此成为新的平台明文代理。人工明文读取是独立高风险 Action，需策略、强认证、Security Approval、一次性交付和 Strong Audit。
- 约束与后果：Secret 不进入 backend、普通日志、异常和审计内容。普通管理 UI 只管理 metadata、Policy 和 lifecycle。Agent/SDK/CLI 都使用相同 Vault 授权合同，不建立明文旁路。`provider_direct_nonrecoverable` 是唯一明确的 Provider 直交付例外：明文由 Provider 直接交给绑定的最终消费端，Vault 不接触明文，也不允许任何中间平台服务代理；该模式必须满足 ADR-043/ADR-053 的受限 Grant、通道绑定、撤销和审计要求。
- 关联设计边界：设计清单 §11.1、§11.2
- 关联实施层：Core Security Layer、Platform Integration Layer

<a id="adr-028"></a>
## ADR-028：每 Secret Version 独立 DEK 的 Envelope Encryption

- ADR 编号：`ADR-028`
- 状态：`ACCEPTED`
- 背景：Tenant KEK 直接加密全部 Secret 会提高高价值 KEK 的使用频率并使轮换必须重加密全部数据；Provider 原生密文又会割裂统一语义。
- 决策：每个不可变 Secret Version 生成独立随机 DEK，使用 AEAD 加密完整 payload；DEK 由所属 Tenant Key Domain 当前 KEK generation 包装。Vault 存储 ciphertext、wrapped DEK、nonce、algorithm suite、KEK generation、Provider reference 和认证元数据。AAD 至少绑定 tenant、key domain、创建该 Version 时的稳定 project/namespace ID、secret ID/version、algorithm 和 ciphertext format version；KEK generation、Provider binding 和 wrapped DEK 关系必须作为同一认证封装的一部分，不能成为可替换的未认证旁数据。
- 约束与后果：KEK 轮换默认执行渐进式 rewrap，不重新加密业务密文。AAD、wrapped DEK 或包装元数据篡改必须导致解密失败，不允许兼容模式忽略。Secret 内容变化只能创建新 Version。Secret 或 Namespace 在同一 Tenant 内移动时，历史 Version 继续按创建时 cryptographic scope 验证，不能通过修改当前 Project/Namespace 元数据重写历史 AAD；移动后新 Version 才使用新 scope。无法安全保留该关系时必须显式重新加密/迁移或创建新资源。
- 关联设计边界：设计清单 §11.3
- 关联实施层：Core Security Layer

<a id="adr-029"></a>
## ADR-029：按保障等级控制 Authority 内 DEK 缓存

- ADR 编号：`ADR-029`
- 状态：`ACCEPTED`
- 背景：每次 Secret 读取都远程 unwrap 会增加 HSM/KMS/HYOK 延迟、成本和可用性依赖；无限缓存明文 DEK 又扩大 Authority 失陷影响和撤销窗口。
- 决策：解包后的 DEK 只允许在独立 Crypto Authority 内使用短期、有界、非持久化缓存，并按 Key Domain/Secret Policy/Provider assurance 配置 disabled 或 bounded。HYOK、高敏感和 provider cacheable=false 默认禁用。缓存绑定 key domain、secret version、KEK/provider generation 和 security epoch。
- 约束与后果：缓存只优化 unwrap，不缓存最终授权；每次访问重新校验身份、策略、状态和审计。冻结、禁用、轮换、销毁、Provider 撤销或 epoch 变化立即失效；重启全部丢弃，Provider 故障不得延长 TTL。
- 关联设计边界：设计清单 §11.4
- 关联实施层：Core Security Layer

<a id="adr-030"></a>
## ADR-030：Secret Version 显式状态机与唯一 Current

- ADR 编号：`ADR-030`
- 状态：`ACCEPTED`
- 背景：上传即覆盖会把未经验证的新值立即暴露给所有消费者；多个活动版本由客户端选择会形成长期旧值和降级攻击。
- 决策：Secret Version 状态机固定为 UPLOADING → STAGED → CURRENT → PREVIOUS → DISABLED → PENDING_DELETION → CRYPTO_DESTROYED，并允许外部状态风险状态。每个 Secret 最多一个 CURRENT。STAGED→CURRENT 由 Shard Leader 原子执行，绑定 expected current、secret generation、authority epoch 和 idempotency key。
- 约束与后果：普通读取只解析 CURRENT，不能任意请求历史版本。原 Current 进入 PREVIOUS，只能通过限时迁移、回滚或 break-glass Action 访问。回滚是新的权威状态变化并提升 generation，已销毁版本不得恢复。
- 关联设计边界：设计清单 §11.5
- 关联实施层：Core Security Layer

<a id="adr-031"></a>
## ADR-031：Opaque Payload 与有限标准 Secret Type Registry

- ADR 编号：`ADR-031`
- 状态：`ACCEPTED`
- 背景：仅字符串类型无法表达组合凭证和二进制；任意文档、附件和目录模型会把 Vault 变成加密对象存储并引入复杂解析攻击面。
- 决策：Secret 基础 payload 是不可变 opaque bytes，同时提供版本化、有限、确定性的标准 secret_type，例如 key_value、username_password、tls_bundle、ssh_key_pair、docker_registry、cloud_service_account、provider_credential。每个 Version 记录 schema version、content type、length、受保护完整性元数据和 format version；若保存 digest，只能使用 ciphertext/envelope digest 或带域分离的 keyed digest，禁止保存可被离线枚举的低熵 Secret 明文哈希。完整 Version 始终是最小密码学和生命周期单位。
- 约束与后果：解析器禁止任意对象反序列化、代码执行、外部实体、自动网络访问和递归压缩展开。大文件/文档留在对象存储。Secret 有硬大小上限，具体值由实施验证。Secret type、length、schema 和完整性元数据仍按敏感资源 metadata 受权访问，不能默认公开。
- 关联设计边界：设计清单 §11.6
- 关联实施层：Core Security Layer

<a id="adr-032"></a>
## ADR-032：标准 Secret 的字段级 Action 但字段不是资源

- ADR 编号：`ADR-032`
- 状态：`ACCEPTED`
- 背景：组合凭证整体交付可能暴露不需要字段；把每个字段变成独立 DEK、Version 和生命周期又会破坏原子更新和回滚。
- 决策：仅对有确定 schema 的标准 Secret Type 提供 read_secret_fields。字段 Capability 绑定 Secret ID、实际 Version/CURRENT 解析约束、schema version、resource generation、稳定字段 ID、delivery channel 和 expiry。Vault 在受控明文边界解密完整 payload 后只返回获准字段。opaque 不支持字段读取。
- 约束与后果：字段没有独立 DEK、Version、CURRENT 或销毁流程。审计记录字段 ID 不记录值。需要独立轮换或销毁的内容必须拆成独立 Secret。高保障 Guardrail 可禁止字段解析。Agent 若进行模板或格式化，只能获得 Vault 已按字段 Capability 裁剪的字段集合；没有完整 Payload 授权时不得接收全量字段后自行裁剪。
- 关联设计边界：设计清单 §11.7
- 关联实施层：Core Security Layer

<a id="adr-033"></a>
## ADR-033：静态 Secret 轮换是受控外部副作用流程

- ADR 编号：`ADR-033`
- 状态：`ACCEPTED`
- 背景：静态密码、API Key 和外部系统凭证轮换不仅是创建新 Secret Version，还涉及更新外部目标、验证新值、消费者切换和旧凭证撤销。
- 决策：静态 Secret Rotation 采用显式命令和可恢复状态流程。Vault 负责生成或已取得候选值时，必须先把候选材料以 STAGED Version 或专用 sealed rotation record 可靠保存，再修改外部目标；若新值只能由 Provider 在外部变更时产生，Provider 返回的敏感材料必须在继续确认、响应或切换前立即密封到权威 operation record。随后完成外部目标更新、验证、原子激活 CURRENT、通知/协调消费者、停用旧值和对账。外部目标或候选材料状态未知时进入 reconciliation，不能盲目重试生成或切换。
- 约束与后果：轮换策略必须定义 owner、Provider/target、候选值持久保护点、切换窗口、回滚、旧凭证清理和失败语义。只有候选材料可恢复、外部目标已确认且必要消费验证通过后，Shard Leader 才能切换 CURRENT。多实例灰度通过 workload scope 或 rollout command 实现，不允许多个默认 CURRENT。
- 关联设计边界：设计清单 §11.8
- 关联实施层：Core Security Layer、Platform Integration Layer

<a id="adr-034"></a>
## ADR-034：Transit Canonical Ciphertext Envelope 与受控 Detached Metadata

- ADR 编号：`ADR-034`
- 状态：`ACCEPTED`
- 背景：裸密码学参数会导致 Nonce 重用、算法误选和 Key Version 丢失；Provider 原生 blob 会把历史密文锁定在具体 Provider。
- 决策：Transit 默认返回版本化 Canonical Ciphertext Envelope，认证绑定 format version、Tenant Key Domain、Key ID/Version、algorithm suite、operation class、provider binding version、nonce、ciphertext/tag、AAD binding 和 derivation context binding。Nonce 默认由 Vault/Provider 生成。受限兼容场景可使用 detached metadata，但必须与 ciphertext 建立不可伪造绑定。
- 约束与后果：普通调用方不得自行选择或重复使用 AEAD Nonce；自定义 Nonce 只能通过独立高级 Action，在算法允许、Guardrail 放行并完成强审计时使用。调用方不能通过 Alias 或自报算法解密历史密文。签名、MAC 和包装等非密文输出也必须通过版本化 Canonical CryptoResult 或受控 detached metadata 返回实际 key ID/version、algorithm、operation class 和 format version；裸 signature/MAC bytes 只能作为明确兼容字段，不能成为缺失 Key Version 的默认合同。未知格式返回稳定错误，不宽松猜测或降级。Provider native blob 只作为 envelope 内部字段。Transit 不持久化业务明文或完整业务密文；操作关联优先使用 Envelope/ciphertext digest 或带域分离的 keyed digest，禁止记录低熵业务明文的普通哈希。
- 关联设计边界：设计清单 §12.1、§12.2
- 关联实施层：Core Security Layer、Advanced Security Layer

<a id="adr-035"></a>
## ADR-035：版本化 Derivation Profile 与分级输出

- ADR 编号：`ADR-035`
- 状态：`ACCEPTED`
- 背景：自由 KDF 参数和原始派生密钥输出可绕过父 Key 不可导出边界并造成 context 冲突；完全禁止派生又无法支持大规模对象隔离和硬件派生。
- 决策：所有派生通过版本化 Derivation Profile 固定父 Key Class、KDF、长度、context schema、domain、用途、确定性和输出策略：internal_only、wrapped_export、provider_handle_only、plaintext_export_compatibility。internal_only 默认；context 使用无歧义规范编码并绑定 tenant、parent key/version、profile/version 和 operation domain；敏感 context 的审计关联只能使用受保护、带域分离的 digest 或受控引用，不能使用可枚举的无密钥哈希。
- 约束与后果：派生输出不能比父 Key 拥有更宽用途、更弱保障、更强导出或更长寿命。non_exportable 父 Key 禁止明文输出。需要独立轮换/销毁的派生结果必须创建正式 Derived Key Resource。
- 关联设计边界：设计清单 §12.3
- 关联实施层：Core Security Layer、Advanced Security Layer

<a id="adr-036"></a>
## ADR-036：版本化 Random 与 Password Generation Profile

- ADR 编号：`ADR-036`
- 状态：`ACCEPTED`
- 背景：安全随机数和密码生成属于正式产品能力。若允许调用方自由选择 RNG、弱字符集或不可验证参数，会形成低质量秘密；若生成接口自动持久化，又会混淆一次性交付与 Secret/Key 生命周期。
- 决策：Vault 通过版本化 Generation Profile 提供安全随机字节、Token 和密码生成，固定批准的随机源/Provider、长度、字符或字节约束、编码、用途和合规条件。调用方不能提交自定义 RNG 或请求弱随机。生成结果使用与其他敏感交付一致的受保护通道和一次性交付语义，生成接口本身不隐式持久化。
- 约束与后果：生成值不得进入日志、指标、审计值或 backend 中转。需要长期保存、轮换、授权或销毁的结果必须显式创建 Secret 或 Key Resource。Profile 版本和使用目的进入审计，但不记录结果值。
- 关联设计边界：设计清单 §12.4
- 关联实施层：Core Security Layer

<a id="adr-037"></a>
## ADR-037：确定性变换与 Tokenization 作为独立高风险资源

- ADR 编号：`ADR-037`
- 状态：`ACCEPTED`
- 背景：确定性输出泄露相等性和频率，普通 encrypt(deterministic=true) 会让常规 Transit 权限隐式获得高风险关联能力；完全禁止又会促使业务自行实现更弱方案。
- 决策：提供独立 DeterministicTransform 和 TokenizationProfile Resource，创建时固定输入类型、规范化、算法、Parent Key、数据域、可逆性、熵要求、稳定范围、生命周期和迁移策略。可逆确定性变换和不可逆 Tokenization 使用不同 Key Class/Action。禁止通用收敛加密和跨租户去重。
- 约束与后果：Token 默认只在 Tenant 和明确数据域内稳定。跨 Project/Namespace 稳定关联是显式高风险能力。低熵输入必须满足 Profile 的额外域分离、速率限制和风险审批要求；无法安全控制枚举风险时必须拒绝。Profile 轮换使用 PREPARING、DUAL_TRANSFORM、REINDEXING、CUTOVER、RETIRED 流程，并必须公开相等性与频率泄露风险。
- 关联设计边界：设计清单 §12.5
- 关联实施层：Advanced Security Layer

<a id="adr-038"></a>
## ADR-038：统一 CA Resource 与受约束 Trust Domain 树

- ADR 编号：`ADR-038`
- 状态：`ACCEPTED`
- 背景：只代理外部 CA 无法提供完整内建 PKI；只提供自建 CA 又无法兼容企业 CA、Cloud CA 和 HYOK。任意 CA 图会引入跨租户信任和路径歧义。
- 决策：所有内建、HSM、Cloud/Enterprise CA 和 HYOK CA 统一建模为 CA Resource。层级受约束为 Trust Domain → Root CA → Intermediate CA → Issuing CA/Certificate Role。Root 默认离线或高保障托管，不承担日常签发；CA 私钥默认不可导出。交叉签名只允许作为限时、可审计迁移关系。
- 约束与后果：CA Resource 归属于唯一 Tenant/Project/Namespace，租户 CA 不得跨租户签发。每个 CA Version 固定算法、Key Usage、Name Constraints、Path Length、允许身份范围、Provider 和 assurance level；CA Key Version 遵循 STAGED、唯一 PRIMARY、禁止旧版本继续签发新证书和显式销毁原则，证书链迁移必须使用显式双链或验证窗口。旧 Issuing CA 仍有未过期证书或吊销状态义务时，可进入 `REVOCATION_STATUS_ONLY`，优先使用专用 OCSP Signing Key，并由原 Issuer Key 或经批准的间接 CRL 机制维持 CRL；该状态不得签发新的终端或下级 CA 证书。证书序列号在相应 Issuer Authority 范围内唯一；外部 CA 自行分配时保存其权威 serial 和 Provider reference。外部 Provider 身份映射为 Vault CA Version，签发、吊销、Lease 和审计使用统一语义。SSH CA 复用生命周期框架但不与 X.509 共用密钥。
- 关联设计边界：设计清单 §13.1、§13.2
- 关联实施层：Advanced Security Layer

<a id="adr-039"></a>
## ADR-039：证书身份由 Vault 绑定和派生

- ADR 编号：`ADR-039`
- 状态：`ACCEPTED`
- 背景：CSR 签名只证明私钥持有，不能证明申请者有权声明任意 SAN、Subject、SPIFFE ID 或 SSH principal。宽泛 Role 允许列表仍可能冒充同域其他 workload。
- 决策：Certificate Role 绑定 Tenant、Project、Namespace、Trust Domain、证书类型和身份派生规则。Vault 根据 federated principal、workload attestation、Kubernetes ServiceAccount、SPIFFE、已验证 DNS/设备/服务身份重建或严格验证 Subject、SAN 和 SSH principal。附加身份逐项授权，通配符默认禁止。
- 约束与后果：外部 CA 返回后必须验证 Subject、SAN、KU/EKU、有效期、Issuer、公钥和 Role Version 与批准内容完全一致；超范围结果不交付并进入对账。身份映射证据进入 Strong Audit。
- 关联设计边界：设计清单 §13.3
- 关联实施层：Advanced Security Layer

<a id="adr-040"></a>
## ADR-040：按证书用途与保障等级选择私钥生成模式

- ADR 编号：`ADR-040`
- 状态：`ACCEPTED`
- 背景：始终客户端生成会让遗留应用难以安全管理私钥；始终 Vault 生成会让 Vault 接触大量终端私钥并破坏设备/HSM 不可导出场景。
- 决策：Certificate Role 固定允许的 private_key_mode：caller_generated、agent_generated、vault_generated_exportable、provider_generated_non_exportable。默认优先调用方/Agent 本地生成或 Provider 内不可导出生成；Vault 生成并导出只作为显式兼容模式。CA、SSH CA 和高保障签名私钥禁止通过终端交付导出。
- 约束与后果：不可导出模式不能由调用方降级。Vault 生成可导出私钥只允许一次性交付、强审计且不提供普通再次查看；交付未知进入显式恢复/撤销状态。私钥丢失默认重新生成和签发，而非长期备份。证书续期是否复用原私钥由 Certificate Role 固定；高保障策略可以强制每次续期轮换私钥。
- 关联设计边界：设计清单 §13.4
- 关联实施层：Advanced Security Layer、Platform Integration Layer

<a id="adr-041"></a>
## ADR-041：证书权威状态与多机制吊销传播

- ADR 编号：`ADR-041`
- 状态：`ACCEPTED`
- 背景：只依赖短有效期无法处理私钥泄露和较长期证书；只依赖 CRL 或外部 CA 原生状态又无法统一短期 workload、设备和企业 PKI。
- 决策：证书状态由 Vault Authority 维护，区分 PENDING、ACTIVE、SUSPENDED、EXPIRED、REVOCATION_PENDING、REVOKED、EXTERNAL_STATE_UNKNOWN。Certificate Role 声明最大有效期、主动吊销能力、CRL/OCSP/紧急 deny 传播机制、最大陈旧窗口和状态不可用策略。短期证书优先短寿命和停止续签，但保留紧急 deny/吊销。
- 约束与后果：CRL Number 单调，OCSP 使用专用签名 Key。外部 CA 未确认吊销不能标记 REVOKED。状态信息无法满足 Role 的新鲜度要求时按 Trust Domain Guardrail 决定 fail-open/fail-closed，高保障环境默认 fail-closed。Tenant、Namespace、Principal Binding 或父 Lease 失效可级联停止续签和批量吊销。已吊销状态不能因恢复或时钟回拨重新 ACTIVE。CA Version 或状态签名能力在仍有依赖证书、CRL/OCSP 新鲜度义务或未完成 Provider 吊销对账时不得销毁，必须先证明依赖已过期、迁移或由等价状态服务安全接管。
- 关联设计边界：设计清单 §13.5
- 关联实施层：Advanced Security Layer、Production Assurance Layer

<a id="adr-042"></a>
## ADR-042：Lease 是 Vault 权威、可续期、可撤销的分层资源

- ADR 编号：`ADR-042`
- 状态：`ACCEPTED`
- 背景：客户端本地 TTL 或 Provider 原生 expiry 无法统一主动撤销、父子关系、最大总寿命、灾备恢复和对账。
- 决策：Lease 是稳定 ID 的 Vault 权威资源，绑定 tenant/project/namespace、principal/workload、role/resource、Provider、Shard/epoch、Capability、当前 TTL、最大总寿命、renewal budget、parent Lease、external ID 和 generation。状态至少包含 PENDING、ACTIVE、RENEWING、EXPIRED、REVOCATION_PENDING、REVOKING、REVOKED、CLEANED、REVOCATION_FAILED、EXTERNAL_STATE_UNKNOWN。
- 约束与后果：创建、续期、撤销和到期是 Shard Leader 权威写入。Lease 默认不可转让，必须持续绑定原 principal、workload 和交付通道。续期重新检查身份、Guardrail、resource generation、Provider、认证强度和时间，不能突破创建时最大总寿命或后续收紧的 Guardrail；并通过 lease_generation + renewal_id 保证并发续期幂等。EXPIRED 不等于 REVOKED；Provider 撤销未知不能标记安全完成。父 Lease 可级联撤销子 Lease。
- 关联设计边界：设计清单 §14.1
- 关联实施层：Core Security Layer、Advanced Security Layer

<a id="adr-043"></a>
## ADR-043：动态凭证使用 Lease 级临时密封交付包

- ADR 编号：`ADR-043`
- 状态：`ACCEPTED`
- 背景：动态凭证长期保存为普通 Secret 会扩大历史恢复窗口；完全只返回一次又无法处理网络丢包、Leader 切换和 Agent 重连。
- 决策：动态凭证不自动成为普通 Secret Resource，而作为 Lease 的 sealed credential payload，使用独立 Delivery DEK，绑定 Lease/generation、principal/workload、Role Version、Provider external ID、delivery channel、expiry 和交付预算。默认 one_time，可显式允许 bounded_redelivery；部分 Provider 可使用 provider_direct_nonrecoverable。
- 约束与后果：重复交付必须重新认证授权且不改变 Lease 权限和寿命。Lease 失效时销毁 Delivery DEK。仅凭 Lease ID 不能领取。Provider 创建成功但交付未知时先对账或受控重交付，不盲目再创建。provider_direct_nonrecoverable 只能用于 Provider 确实无法恢复返回材料的明确模式，并必须使用 ADR-053 所约束的 Provider-specific 短期派生 Grant、主体/通道绑定和可验证审计；交付失败后撤销并重新创建，不能退回普通可重复读取。
- 关联设计边界：设计清单 §14.2
- 关联实施层：Advanced Security Layer

<a id="adr-044"></a>
## ADR-044：按 Provider 能力分级的动态凭证签发模式

- ADR 编号：`ADR-044`
- 状态：`ACCEPTED`
- 背景：并非所有 Provider 都能为每个 Lease 创建独立身份；隐藏使用共享账号会虚假宣称精确撤销和隔离。
- 决策：Credential Role 显式选择 per_lease_identity、provider_native_session、exclusive_pool、rotated_shared_compatibility。前两者是优先正式动态凭证模式；Pool 成员每次只绑定一个活动 Lease，回收前完成权限、会话、凭证轮换和对账，未知则 QUARANTINED；共享模式仅作明确标识的遗留兼容。
- 约束与后果：Guardrail 可禁止 Pool、共享账号或不支持主动撤销的 Provider。Pool 成员分配、回收和 QUARANTINED 解除必须由所属 Shard Leader 按 pool/member generation 串行裁决；每个外部身份、Session 和 Pool Member 都具有稳定 Provider reference 并进入 Lease 与 Strong Audit。不同 Lease 不得静默共享活动 Session 或凭证值。Pool 回收或 Provider 对象删除无法确认时，成员/对象保持 QUARANTINED、REVOCATION_FAILED 或 EXTERNAL_STATE_UNKNOWN，不能标记安全清理完成；高风险 Provider/Role 应暂停或限制新签发直至完成对账。共享兼容模式必须披露无法单 Lease 精确撤销和更大爆炸半径。
- 关联设计边界：设计清单 §14.3
- 关联实施层：Advanced Security Layer

<a id="adr-045"></a>
## ADR-045：正式但可选的 Vault Delivery Agent 本地交付平面

- ADR 编号：`ADR-045`
- 状态：`ACCEPTED`
- 背景：没有 Agent 会让每个应用重复实现身份、Lease、文件权限和轮换；强制 Agent 又会排除 Serverless、外部 SDK、CLI 和简单环境。
- 决策：提供正式可选 Vault Delivery Agent，形态可为主机级交付服务、Sidecar、CSI 类适配、Windows Service、Unix Socket/Named Pipe 和一次性注入进程。Vault Delivery Agent 是 Vault 本地交付组件，不是项目中的 `ns_node` 或未来 `ns_agent`，不得占用 `src/ns_agent` 产品边界，也不得借用 `ns_node` 的 Node Principal 代表 workload。直接 SDK/API/CLI 仍是一等公民。Delivery Agent 负责 workload 证明、Capability exchange、Secret/证书/凭证交付、Lease 续期请求、原子更新和受控缓存，但不是 Authority。
- 约束与后果：Agent 不签发 Capability、不修改权威状态、不持有 Tenant KEK/根密钥、不跨 workload 转授、不自行延长 Lease。主机级 Agent 必须依据操作系统身份、进程凭证、cgroup/container identity 或等价可信事实隔离调用方，默认只监听受保护本地通道。文件交付必须使用受限临时文件、预设最小权限、必要持久化同步和原子替换，禁止部分写入或跨 workload 可见路径。环境变量注入只作为进程启动兼容方式，不作为动态轮换的默认交付路径。断网只能在原 Capability、Lease 和 cache TTL 剩余范围内服务。本地明文缓存受 Guardrail 控制。
- 关联设计边界：设计清单 §15.1
- 关联实施层：Platform Integration Layer

<a id="adr-046"></a>
## ADR-046：ns_client 按 Principal 类型提供统一安全 SDK 模式

- ADR 编号：`ADR-046`
- 状态：`ACCEPTED`
- 背景：纯薄 SDK 会让各组件重复实现身份、Capability 和 Lease；把 ns_client 变成常驻代理又会与 Agent 边界重叠。
- 决策：ns_client 提供 human、service、workload、node、external 等模式，负责身份适配、Capability 生命周期、Lease、Secret/Certificate 消费、Transit、稳定错误和审计上下文。客户端不是 Authority、不提升权限、不替代 Agent，也不持有根或 Provider 主能力。
- 约束与后果：各语言 SDK 必须遵守 Canonical Contract 和相同安全语义。缓存、离线和凭证存储能力由客户端类型、Guardrail 和资源策略限制。node client 只是 Node Principal 的协议/SDK 模式，仍必须完成 ADR-048 的 Node Authority Broker bootstrap 与 Capability exchange，只能代表 node principal，不能成为绕过 Broker 的直接注册或 workload 代理入口。
- 关联设计边界：设计清单 §15.2
- 关联实施层：Platform Integration Layer

<a id="adr-047"></a>
## ADR-047：ns_runtime 经 Authority Broker 获得 Capability 后按策略直连数据面

- ADR 编号：`ADR-047`
- 状态：`ACCEPTED`
- 背景：runtime 直接持有长期 Vault 凭证会弱化既有 Authority Broker/Attestor 和 root isolation；所有 Secret 经 Broker 代理又会使其成为明文和吞吐瓶颈。
- 决策：ns_runtime 使用现有 Authority Broker 完成 bootstrap、runtime identity verification 和 Vault Capability exchange。Broker 不代理 Secret 明文、不成为 Vault 最终授权者，也不得自行签名或铸造数据面 Vault Capability；Capability 必须由 ns_vault 授权 Authority 在验证 Broker/Attestor 证据后签发。获得短期、resource/action/generation/expiry 绑定 Capability 后，runtime 可按策略直连 ns_vault Data Plane。
- 约束与后果：普通 runtime 进程不能获得 Tenant KEK、根密钥或 Provider 主能力。Vault 仍重新验证 Capability、资源状态和 Policy。该集成不得削弱 ns_runtime Authority Broker、Attestor、FD 传递和显式依赖边界。
- 关联设计边界：设计清单 §15.3
- 关联实施层：Platform Integration Layer

<a id="adr-048"></a>
## ADR-048：ns_node 是独立 Node Principal 且只访问 node-scoped Secret

- ADR 编号：`ADR-048`
- 状态：`ACCEPTED`
- 背景：ns_node 是节点级确定性安全执行基础设施，不是普通 workload 或通用 Vault Agent。若 node identity 可代表承载的任意 workload 获取 Secret，节点失陷会扩散到所有本机业务身份。
- 决策：ns_node 以独立 Node Principal 接入。节点 bootstrap、证明和 Capability exchange 必须经过专用 Node Authority Broker；证据可包括 host/node registration、TPM、节点证书、云实例身份等。node 只能访问明确 node-scoped Secret/Certificate/Lease，不能代表 workload 获取业务 Secret。
- 约束与后果：Node Authority Broker 只验证节点 evidence、建立 bootstrap 信任并参与 Capability exchange，不得自行签发数据面 Vault Capability 或成为 Vault 最终授权者。Node Capability 绑定 node_id、host_id、node role、tenant/environment、resource/action、generation 和期限。一机多节点部署中每个 node 具有独立身份和授权，不能仅因共享主机继承其他 node 或 workload 权限；未来 host-scoped Secret 必须建模为独立 Host Resource/Action，不能从 node scope 隐式扩大。Vault 集成必须复用 `ns_node` 专用通信进程承载全部对外网络通信，并通过受认证本地 IPC/FD 交付；调度主进程、OCR、浏览器/桌面自动化和插件执行进程不得自行连接 Vault、继承 Node Capability 或隐式读取 node-scoped Secret。通信进程只是传输边界，不是 Vault Authority；独立执行进程需要业务 Secret 时必须建立自身 workload/service Principal。
- 关联设计边界：设计清单 §15.4
- 关联实施层：Platform Integration Layer

<a id="adr-049"></a>
## ADR-049：Shard 密码学审计链与外部不可变锚定

- ADR 编号：`ADR-049`
- 状态：`ACCEPTED`
- 背景：backend 审计或普通追加表不能证明数据库管理员未删除、重排或回滚历史；仅在 Vault 域内的哈希链在整个域被控制后也缺少外部证据。
- 决策：每个 Authority Shard 维护单调序号、前序哈希、epoch 和签名 Key generation 绑定的密码学审计链，并周期性生成签名 checkpoint，发送至独立 WORM/Object Lock、SIEM、审计集群、客户端点或透明日志等外部 Anchor。backend 只保存投影和索引。
- 约束与后果：审计只要求每个 Shard 内严格有序，不伪造跨 Shard 全局总序；聚合视图必须保留各 Shard sequence/epoch。任何成功的权威状态变更都必须在提交时建立不可分割、可恢复的本地审计意图或事务 outbox 关联，不能出现“状态已变但无审计事实”的窗口；Audit Writer 可以异步完成链写入和外部锚定，但不能凭普通消息队列最佳努力语义补记。Leader 切换必须记录旧链尾、新 epoch 和接管证明。高风险操作无法写本地强审计时 fail-closed；高频操作可使用有界可靠缓冲但不得静默丢弃。外部锚定超出允许窗口后按 assurance 策略拒绝。外部客户只能获得其 Tenant 范围内的审计事件、checkpoint 或验证证明。任何管理员、审批或 Break-glass 都不能关闭 Strong Audit 或删除既有审计事实。
- 关联设计边界：设计清单 §16.1、§16.2
- 关联实施层：Foundation Layer、Production Assurance Layer

<a id="adr-050"></a>
## ADR-050：敏感观测、诊断、稳定错误与安全告警边界

- ADR 编号：`ADR-050`
- 状态：`ACCEPTED`
- 背景：Secret、私钥、动态凭证、Bearer Token、Provider 错误、CSR 和自由文本可能通过日志、指标、trace、异常、告警、崩溃转储或诊断包泄露；完全关闭观测又会阻碍安全取证和运维。平台还需要把 Provider 未知、时间/审计异常、撤销失败和安全门禁降级转化为可处置告警，但告警系统不能成为安全状态权威。
- 决策：Vault 的日志、指标、trace、错误、告警和诊断只记录完成授权、运维和关联所需的有界结构化元数据，统一复用并扩展 Sanitizer。禁止记录 Secret/字段值、DEK/KEK/私钥、完整动态凭证、可重放 Token、Provider 主凭证、原始敏感 payload 和不受控异常文本。Vault 从权威状态和 Security Event 产生稳定代码、严重级别、受控作用域、关联 Event/Operation 和处置状态组成的 Security Risk Signal；ns_backend.vault 负责告警规则、展示、通知和客户可见范围，但 Projection/通知不是安全权威。Provider 原始错误只进入受保护诊断域，外部返回稳定 Vault Error。崩溃转储和诊断包默认不得包含敏感内存。
- 约束与后果：可关联性通过 event/operation/resource ID、受保护且域分离的 keyed digest 和审计引用实现，不通过明文或无密钥低熵哈希。健康/状态接口可以表达 SEALED、TIME_UNTRUSTED、AUDIT_DEGRADED、PROVIDER_DEGRADED、RECONCILIATION_REQUIRED 及只读/拒绝状态，但不得泄露租户敏感内容。通知失败、告警平台不可用或人员确认不得删除 Risk Signal、把未知状态标记正常或改变 fail-closed/隔离处置；告警确认只表示流程动作，不表示底层风险已修复。观测失败不得覆盖原业务异常；高风险审计写入失败按 Strong Audit 规则 fail-closed。指标只暴露计数、延迟、状态和受控维度，禁止高基数敏感标签。
- 关联设计边界：设计清单 §3.2、§3.3、§16.2、§16.4、§16.5
- 关联实施层：Foundation Layer、Platform Integration Layer、Production Assurance Layer

<a id="adr-051"></a>
## ADR-051：墙上时间、单调安全时间与可信时间证明双轨

- ADR 编号：`ADR-051`
- 状态：`ACCEPTED`
- 背景：Capability、Lease、缓存和一次性授权不能因系统时钟回拨重新生效；证书、OIDC 和合规审计又需要现实 UTC 时间。
- 决策：Vault 同时使用 Wall Time 和 Monotonic Security Time，并维护 TRUSTED、BOUNDED、DEGRADED、UNTRUSTED 等时间可信状态。TTL、预算和本地 deadline 使用不可回退计时；证书、外部 token 和审计记录使用带可信等级/偏差的 Wall Time。高保障部署可使用 NTS、HSM clock、TPM counter、云签名时间或外部时间戳。
- 约束与后果：已过期、撤销或消费对象不能因回拨恢复。Capability 与动态凭证签发至少要求 BOUNDED；证书签发通常要求 TRUSTED 或严格受限的 BOUNDED；销毁、Break-glass 和根恢复要求可信时间或独立门限证据显式覆盖；公开验签和非敏感读取可在策略允许的 DEGRADED 状态继续。检测快照回滚、显著倒退或基线断裂时进入 TIME_UNTRUSTED，禁止新的长期 Capability、证书和动态凭证。Leader 切换必须继承最后可信 Wall Time 下界、已消耗 TTL、审计序号和 Authority epoch。时间恢复进入 Strong Audit 且不补回已消耗寿命。
- 关联设计边界：设计清单 §16.3
- 关联实施层：Foundation Layer、Production Assurance Layer

<a id="adr-052"></a>
## ADR-052：Tenant Key Domain 分片的单写权威

- ADR 编号：`ADR-052`
- 状态：`ACCEPTED`
- 背景：所有节点共享数据库主动写无法覆盖 HSM/KMS 外部副作用和网络分区 fencing；最终一致多写无法安全合并销毁、Lease 撤销、Primary Version 和一次性 Approval。
- 决策：每个 Tenant Key Domain 归属于唯一 Authority Shard；每个 Shard 同时只有一个有效写 Leader。Leader 变更提升 authority_epoch，所有状态变更命令路由到所属 Leader。authority_epoch、resource generation 和 command ID 共同用于 fencing、防重放和幂等。
- 约束与后果：不能为可用性开放双 Leader。跨 Shard 操作拆为可审计、可恢复流程，不提供隐式分布式事务。无法原生 fencing 的 Provider 通过串行执行器和对账隔离。
- 关联设计边界：设计清单 §17.1
- 关联实施层：Foundation Layer、Production Assurance Layer

<a id="adr-053"></a>
## ADR-053：数据面按操作风险分类执行

- ADR 编号：`ADR-053`
- 状态：`ACCEPTED`
- 背景：所有私密操作都由 Leader 执行会限制吞吐；任意副本持有密钥和旧状态又会扩大暴露并产生撤销传播窗口。
- 决策：数据面分三类：公开验证/非敏感查询可由只读副本执行；普通 Secret 消费、Transit、MAC 和部分签名可由受控 Authority Worker 执行；人工明文、一次性消费、证书签发、动态凭证、严格次数签名、轮换、迁移和销毁保持 leader_only。Worker Capability 绑定 shard、epoch、key domain、resource/generation、operations、TTL 和预算。
- 约束与后果：Worker 不是 API 节点，不写 Authority DB、不持有租户根、不缓存最终授权，失联时不能无限继续。HYOK 和其他 Provider 数据面默认由 Vault Authority/Worker 发起；确需客户端直连 Provider 时，只能签发 Provider-specific、短期、范围受限且可审计的派生 Grant，并继续受资源、Policy、generation、撤销和审计约束，不得绕过 Secret 唯一明文边界。资源 Policy 可把并行操作提升为 leader_only，不能反向降低系统或 Provider 强制限制。
- 关联设计边界：设计清单 §17.2
- 关联实施层：Core Security Layer、Production Assurance Layer

<a id="adr-054"></a>
## ADR-054：每 Key Domain 单 Home Region 的多区域热备

- ADR 编号：`ADR-054`
- 状态：`ACCEPTED`
- 背景：单区域 HA 无法满足区域灾难恢复；多区域主动-主动写与单写 Authority、销毁、Lease、PKI 序列和 Provider 副作用冲突。
- 决策：每个 Tenant Key Domain 固定唯一 Home Region 和写 Authority，Home Region 内部必须具备 Shard Leader + Replica 的节点级高可用，其他 Region 保持同步副本或 Standby。区域灾难时通过受控 failover 提升新 epoch 并 fencing 旧 Region，不允许同一 Key Domain 双写。架构目标类别是有界复制滞后和分钟级受控接管，具体 RPO/RTO 只能由实施计划和真实演练确认。
- 约束与后果：多区域设计优先安全单写而非低延迟全球写。计划内 Home Region/Shard 迁移与灾难接管使用同一“暂停/恢复或追平、所有权转移、epoch 提升、旧权威 fencing、缓存与 Capability 失效、审计连续性证明”边界，不能通过后台改字段直接迁移。Provider locality、数据驻留和不可迁移限制必须显式建模。审计链需要证明原 Region 尾部、新 Region 接管和 epoch 连续性。
- 关联设计边界：设计清单 §17.3
- 关联实施层：Production Assurance Layer

<a id="adr-055"></a>
## ADR-055：按资源保障等级的灾备恢复与 Provider 重新验证

- ADR 编号：`ADR-055`
- 状态：`ACCEPTED`
- 背景：数据库复制成功不代表 HSM Key、HYOK、Provider Session、Lease、CA 序列和吊销状态已恢复；直接接管可能重复生效或使用旧能力。
- 决策：恢复状态固定为 BACKUP_AVAILABLE → METADATA_RESTORED → PROVIDER_VERIFIED → AUTHORITY_RESTORED → TRAFFIC_ENABLED。软件托管材料可从受保护备份恢复；HSM/KMS 需重新认证和验证 Key；HYOK 需客户 Provider 重新授权；Lease、动态凭证、CA、CRL/OCSP 和 Audit 分别对账。
- 约束与后果：恢复提升 root_epoch、authority_epoch 和 provider session epoch，清空 DEK cache并重新验证 Capability。未验证资源保持 UNKNOWN/RECONCILIATION_REQUIRED，不提供正常数据面。不得为恢复 HYOK 创建隐藏替代密钥。
- 关联设计边界：设计清单 §17.4
- 关联实施层：Production Assurance Layer

<a id="adr-056"></a>
## ADR-056：加密备份与防历史回滚恢复

- ADR 编号：`ADR-056`
- 状态：`ACCEPTED`
- 背景：备份可能包含密文、wrapped key 和权威元数据；若不绑定 epoch、generation 和审计 Anchor，旧备份可复活已销毁资源、旧 Policy 或已撤销 Capability。
- 决策：备份不得包含明文 Secret、未包装 DEK/KEK 或私钥。备份使用独立 Backup Protection Key/Provider 保护，并绑定 schema、tenant/shard、region、root/authority epoch、resource generation、审计 checkpoint 和创建时间可信状态。恢复必须验证外部 Audit Anchor、tombstone 和 crypto-destroy state。
- 约束与后果：已完成密码学销毁的资源不能因恢复旧 DB/对象存储重新可解。备份恢复只是元数据恢复入口，仍必须执行 Provider、Lease、CA 和审计 reconciliation。
- 关联设计边界：设计清单 §17.5、§19
- 关联实施层：Production Assurance Layer

<a id="adr-057"></a>
## ADR-057：按资源保障等级策略化故障与离线行为

- ADR 编号：`ADR-057`
- 状态：`ACCEPTED`
- 背景：全面 fail-closed 会让普通 workload 在短暂故障中断；自动 fallback 到本地 Key/Secret 会形成不可撤销的隐藏旁路。
- 决策：默认 fail-closed，但 Resource Guardrail 可为普通 workload 显式允许有限缓存继续服务。策略声明 outage mode、max offline duration、cache policy、renewal policy 和 audit requirement。HSM/HYOK、CA、管理员 Secret、高价值签名和高风险动态凭证默认 fail-closed。
- 约束与后果：离线期间不签发新 Capability、不扩大权限、不续 Lease、不轮换、不访问新资源。只能使用已验证、未过期、明确允许缓存的现有材料，且不得延长 TTL。禁止环境变量、配置文件、本地备用 Key 或隐藏 Provider fallback。
- 关联设计边界：设计清单 §18
- 关联实施层：Foundation Layer、Production Assurance Layer

<a id="adr-058"></a>
## ADR-058：多阶段删除、墓碑与显式密码学销毁

- ADR 编号：`ADR-058`
- 状态：`ACCEPTED`
- 背景：简单 deleted 标记不等于销毁，直接删除数据库行也不能处理备份和 Provider；立即硬删除又容易因误操作或 backend 失陷造成永久损失。
- 决策：资源生命周期区分 ACTIVE、DISABLED、PENDING_DELETION、TOMBSTONED、CRYPTO_DESTROYED、METADATA_PURGED。删除与密码学销毁是不同 Action。Version 销毁通过 DEK/Key material 销毁；Tenant KEK generation 销毁前必须证明依赖已 rewrap 或明确接受大范围不可恢复。资源 ID 永不复用。
- 约束与后果：高影响销毁要求职责分离、Security Approval、影响预览、expected generation 和一次性确认。有效 Lease、证书、密文依赖、迁移或恢复任务默认阻止销毁。外部 Provider 销毁结果必须区分 Vault 已完成、Provider 已验证确认、以及外部声明但无法验证；不得声称无法证明的物理擦除。最小 tombstone、销毁事实和 Strong Audit 长期保留。
- 关联设计边界：设计清单 §19
- 关联实施层：Core Security Layer、Production Assurance Layer

<a id="adr-059"></a>
## ADR-059：分层 Authority Storage

- ADR 编号：`ADR-059`
- 状态：`ACCEPTED`
- 背景：单一关系数据库承载全部权威、审计链、Shard 协调和大对象会把不同一致性与容量语义混在一起；自研存储引擎风险过高。
- 决策：采用分层存储：Relational Authority DB 保存资源、版本、Policy Artifact、Command、Lease、Certificate 和 Provider Binding 的 Actual State/权威元数据；Security Event Store 保存 append-only event/audit chain；State Store 保存 Shard coordination、epoch、fencing 和临时协调；Object Storage 保存受控大密文归档、备份和审计归档。具体产品在实施阶段选型。Security Event Store 不通过 replay 单独成为 Current State 权威，State Store 的 leader/lease 记录也不能单独授予安全写权限。
- 约束与后果：威胁模型假设 Vault Authority DB 泄露可能暴露元数据、ciphertext 和 wrapped key，但不得直接获得 Secret 明文、Root Key、Tenant KEK 或私钥明文。backend 与 Vault 使用独立数据库账号、Migration、备份和恢复生命周期。每类数据的权威顺序必须明确，多存储失败不能通过猜测合并。State Store 不是 Key/Secret Authority，Object Storage 不是普通 Secret Store。数据库恢复不等于安全恢复。
- 关联设计边界：设计清单 §20.1
- 关联实施层：Foundation Layer、Production Assurance Layer

<a id="adr-060"></a>
## ADR-060：安全域分层进程模型

- ADR 编号：`ADR-060`
- 状态：`ACCEPTED`
- 背景：单体进程会让 API、Provider SDK、Scheduler 和审计漏洞直接影响根权威；按 KMS/Secret/PKI 拆成独立微服务又会破坏统一资源和事务边界。
- 决策：ns_vault 保持一个统一 Security Authority，但按安全域拆分 API Layer、Vault 内部 Command Intake/Execution Coordination、Root/Seal 与 Crypto Authority/Shard Leader、Authority Worker、Provider Host、Scheduler/Reconciliation 和 Audit Writer。Root/Seal Authority 可以作为 Crypto Authority 的严格 bootstrap 子边界，但不能退化为通用 Provider Host。这里的内部 Command 协调层不是第二产品控制面；平台统一控制面仍是 ns_backend.vault。各进程通过认证、版本化、最小权限 IPC 协作。
- 约束与后果：API 不持有根或 KEK；Provider Host 不写权威状态；Scheduler 不自行绕过 Leader 状态机；Audit Writer 不可被普通业务路径绕过。组件可独立扩缩容，但不能演变成互不协调的产品微服务。
- 关联设计边界：设计清单 §20.2
- 关联实施层：Foundation Layer、Core Security Layer

<a id="adr-061"></a>
## ADR-061：Django 控制面与 FastAPI/ASGI Vault 服务

- ADR 编号：`ADR-061`
- 状态：`ACCEPTED`
- 背景：ns_backend 已使用 Django，适合控制面和运营；将 Vault 实现成 Django App 容易共享 ORM、进程和权限边界。完全换用系统语言会提高当前团队和仓库整合成本。
- 决策：src/ns_backend/vault 保持 Django 控制面。src/ns_vault 使用独立 Python FastAPI/ASGI 服务，拥有独立入口、依赖、配置、数据库 Migration、进程和发布生命周期。FastAPI 只负责服务适配，不定义领域权威合同。
- 约束与后果：Django ORM 不得访问 Vault Authority Storage。两者通过 Canonical Contract、Command、Receipt、Event、Projection 和身份/Capability 协议协作。FastAPI/Pydantic 的具体版本属于实施选择，但框架边界本身是长期决定。
- 关联设计边界：设计清单 §20.3
- 关联实施层：Foundation Layer、Platform Integration Layer

<a id="adr-062"></a>
## ADR-062：传输无关 Canonical Contract 与多协议适配

- ADR 编号：`ADR-062`
- 状态：`ACCEPTED`
- 背景：REST、gRPC、本地 IPC 和内部协议各自独立设计会形成不同 action、错误、幂等和安全旁路；单一 REST 或 gRPC 又不能自然覆盖所有浏览器、流式和本地 FD 场景。
- 决策：先定义传输无关的 Principal、ResourceRef、Action、Command、Query、CryptoOperation、DeliveryOperation、Capability、ApprovalEvidence、ExecutionReceipt、Lease、SecurityEvent 和 StableError 合同，再适配 REST/JSON、gRPC、Unix Socket/Named Pipe、Authority IPC 和 Provider 协议。传输版本与业务合同版本分离。
- 约束与后果：同一 Action 在所有适配器执行相同身份、租户、Policy、generation、Capability 和审计校验。所有可能产生副作用或消费一次性预算的请求必须携带可追踪 request/operation ID，并按类型支持 idempotency key、expected generation、contract version 和 trace ID；传输重试不能改变幂等语义。Provider Host operation 必须可映射回对应 Vault Command/Crypto Operation、Resource 和 Audit Reference。HTTP/gRPC status 只是 StableError 映射。内部接口不能因内网而拥有旁路。
- 关联设计边界：设计清单 §20.4
- 关联实施层：Foundation Layer

<a id="adr-063"></a>
## ADR-063：Schema Registry 与显式兼容策略

- ADR 编号：`ADR-063`
- 状态：`ACCEPTED`
- 背景：Key、Secret、Ciphertext、Certificate、Policy、Event 和 Provider 协议具有长期寿命；只维护最新版本会破坏滚动升级，永久向后兼容又会保留弱算法和错误安全语义。
- 决策：建立治理型 Schema Registry，管理 API、Command、Event、Policy、Resource、Secret Type、Ciphertext、Provider Protocol 和 SDK Contract。每个 schema 声明 version、compatibility mode、migration path、deprecation policy 和 security impact。支持有限 N/N-1 或显式协商窗口。
- 约束与后果：安全语义变化不得静默兼容。旧格式可读取或迁移但禁止继续创建弱资源。迁移记录 source/target version、actor、result 和 Strong Audit。Registry 不是资源 Authority。
- 关联设计边界：设计清单 §20.5
- 关联实施层：Foundation Layer、Production Assurance Layer

<a id="adr-064"></a>
## ADR-064：ResourceRef/SecretRef 是定位符而非凭证

- ADR 编号：`ADR-064`
- 状态：`ACCEPTED`
- 背景：若调用方把 SecretRef、Alias 或路径当作 bearer credential，引用泄露将等价于权限泄露，并可能绕过 CURRENT Version、generation 和 Capability。
- 决策：ResourceRef、SecretRef、KeyRef、Alias 只提供稳定资源定位，永不承载授权。每次使用必须携带有效身份/Capability并解析实际 resource ID、version/generation 和 policy state。SecretRef 默认解析 CURRENT，但执行 Capability 绑定实际 Version 和 generation。跨 Project/Namespace 的 Ref 不产生隐式可见性或授权，只能在同一 Tenant 内经显式 Grant/Guardrail 和目标 Resource/Generation Capability 使用。
- 约束与后果：Alias 重命名、backend Projection、Agent cache 或旧 Ref 不能恢复已禁用/销毁资源权限。Ref 可以出现在经过分类的非敏感控制面和配置中，但不得包含 Secret、可重放 Token 或 Provider 主凭证；对可能暴露租户、环境或高价值资源拓扑的引用，日志、URL 查询参数、指标标签和外部错误仍必须按 Sanitizer/披露策略处理，不能把“不是凭证”误解为“始终可公开”。
- 关联设计边界：设计清单 §20.6
- 关联实施层：Foundation Layer、Platform Integration Layer

<a id="adr-065"></a>
## ADR-065：Software Provider 可生产使用但明确低保障

- ADR 编号：`ADR-065`
- 状态：`ACCEPTED`
- 背景：完全禁止 Software Provider 会使离线、小型和初期生产环境不可用；允许但不标记会让用户误解为 HSM/HYOK 等价保障。
- 决策：Software Provider 可以承载生产资源，但 assurance_level 必须明确为 software。hardware 和 external_controlled 提供更高等级。Provider Manifest、Resource Metadata、Policy 和 Audit 都记录实际保障；Guardrail 可要求特定资源必须 hardware 或 external_controlled。
- 约束与后果：Software Provider 不得声明硬件级不可导出、物理防篡改或管理员不可见。CA、Root、高价值 signing、管理 Secret 等可按生产门禁禁止 software。
- 关联设计边界：设计清单 §9、§21.3
- 关联实施层：Core Security Layer、Production Assurance Layer

<a id="adr-066"></a>
## ADR-066：配额、计量、统计与安全裁决分离

- ADR 编号：`ADR-066`
- 状态：`ACCEPTED`
- 背景：平台需要计费、防滥用和资源/操作统计，但将配额、计量或统计 Projection 交给 backend 最终裁决可能在 backend 失陷或投影滞后时绕过 Provider 限制和资源安全预算；反之，把运营仪表盘放进 Authority 热路径会污染安全执行。
- 决策：Customer/Platform 运营配额和账单由 ns_backend 控制面管理；Vault Authority 执行与安全相关的硬配额、调用预算、Lease 上限、Provider 限流、Key/Secret 资源限制和 Capability budget。计量与统计事实由 Actual State、Execution Receipt 和 Security Event 派生，并按 Tenant/Project/Namespace/Resource Type 投影到 backend 用于仪表盘、趋势和运营查询。
- 约束与后果：backend 展示或合同配额不能提升 Provider 和 Guardrail 的硬上限。租户/资源预算、Provider 限流和审计缓冲压力必须形成明确 backpressure，不得通过跳过授权、审计、generation 或 fencing 维持吞吐。计费失败不得回滚已经发生的密码学操作，但必须形成可对账计量事实。异步、近似或滞后的统计不得参与授权、撤销、硬配额、销毁或 Provider 安全裁决。配额拒绝使用稳定错误并进入审计，统计维度不得泄露高基数敏感 ResourceRef 或 Secret metadata。
- 关联设计边界：设计清单 §21.1
- 关联实施层：Platform Integration Layer、Production Assurance Layer

<a id="adr-067"></a>
## ADR-067：容量模型与实测指标分离

- ADR 编号：`ADR-067`
- 状态：`ACCEPTED`
- 背景：设计需要指导分片和扩展，但在没有实际环境和 Provider 的情况下写具体 QPS/P99 会把目标误当成验收事实。
- 决策：设计边界只定义水平扩展、Shard、Tenant/Resource/Lease 数量级和容量等级模型；实施计划定义 benchmark、压测、P99、吞吐和 Provider 限制目标；Acceptance Log 只记录真实环境和结果。
- 约束与后果：未测试数字不得作为 SLA。容量模型不能成为降低一致性、审计或安全门禁的理由。不同 Provider 和 assurance level 可有独立性能基线。
- 关联设计边界：设计清单 §21.2
- 关联实施层：Production Assurance Layer

<a id="adr-068"></a>
## ADR-068：按资源保障等级的生产启用门禁

- ADR 编号：`ADR-068`
- 状态：`ACCEPTED`
- 背景：整个 Vault 单一“上线/未上线”状态无法同时支持软件内部场景和 HSM/HYOK 高保障场景；功能可用也不等于安全边界已验收。
- 决策：生产准入分级：Level 1 基础内部资源要求身份、授权、加密、审计、生命周期和备份恢复；Level 2 生产敏感资源要求 HSM/KMS 或经验证等价 Provider、强审计、轮换和故障验证；Level 3 高保障资源要求 HSM/HYOK、双人控制、灾备演练、安全测试和 Provider 证明。Resource Guardrail 选择门禁。
- 约束与后果：低等级 Provider 不能承载高等级资源。实施计划记录待验证门禁，Acceptance Log 只记录实际通过。某一等级未完成不能虚构生产就绪，也不删除最终产品能力。
- 关联设计边界：设计清单 §21.3
- 关联实施层：Production Assurance Layer

<a id="adr-069"></a>
## ADR-069：分层实施顺序不改变最终设计

- ADR 编号：`ADR-069`
- 状态：`ACCEPTED`
- 背景：按产品模块垂直交付容易在身份、授权、审计和 Authority 尚未完成时建立临时旁路；按现有组件接入优先又可能让 backend/runtime 现状反向塑造 Vault 核心边界。
- 决策：实施组织固定为 Foundation Layer → Core Security Layer → Platform Integration Layer → Advanced Security Layer → Production Assurance Layer。每层定义前置条件、工作包、安全门禁和出口条件。该顺序只表达依赖和执行游标，不改变设计清单中的最终能力。
- 约束与后果：未实施能力不得标记完成，但也不得从设计中删除。实施计划是唯一当前状态与执行入口；ADR 不记录阶段进度，Acceptance Log 不覆盖实施状态。
- 关联设计边界：设计清单 §0、§23
- 关联实施层：实施治理

## ADR 变更规则

- 修改 `ACCEPTED` 决策时，必须明确说明变更原因、受影响资源和协议、数据兼容、迁移、回滚、安全降级风险以及是否需要提升 schema、policy、security 或 root epoch。
- 小范围文字澄清不得改变原决策的安全含义；如果会改变允许/禁止、Authority 归属、故障语义、身份或密钥边界，必须新增 ADR 或显式标记替代关系。
- `SUPERSEDED` ADR 不得删除。新 ADR 必须指出被替代编号、替代范围和仍然有效的历史约束。
- 具体实施不得通过“暂时”“内部使用”“仅开发环境”“先打通流程”等理由绕过 `ACCEPTED` 决策；确需临时替代时，只能在实施计划中标明限制、阻断条件和退出路径，且不得宣称符合最终边界。
- 任何 ADR 的真实实现和验收证据必须分别进入实施计划和验收日志，本文件不记录完成状态。
