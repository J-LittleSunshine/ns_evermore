# ns_runtime 长期架构决策

> 文档版本：`0.0.2`
> 设计边界：[ns_runtime_design_checklist_0.0.2.md](ns_runtime_design_checklist_0.0.2.md)
> 当前状态与执行入口：[ns_runtime_implementation_plan_for_design_0.0.2.md](ns_runtime_implementation_plan_for_design_0.0.2.md)
> 历史验收证据：[ns_runtime_acceptance_log_0.0.2.md](ns_runtime_acceptance_log_0.0.2.md)

本文件只记录会影响后续阶段的长期决策，不记录测试通过数量、当前实现进度或工作区快照。设计边界与 ADR 冲突时，以设计边界文档为准；ADR 状态为 `PROVISIONAL` 时，后续工作包不得自行补全未冻结语义。

## ADR 状态

| 状态 | 含义 |
|---|---|
| `ACCEPTED` | 已接受并约束关联阶段；修改时必须显式新增或替代 ADR |
| `PROVISIONAL` | 已冻结当前禁止推断的边界，但最终语义仍需在关联阶段定义 |
| `SUPERSEDED` | 已被后续 ADR 替代；必须保留追溯关系 |

## ADR-001

- ADR 编号：`ADR-001`
- 状态：`ACCEPTED`
- 背景：runtime 配置会来自本地文件、backend 覆盖和运行期已验证快照；隐式可变配置会导致来源、回滚和热更新语义不可追溯。配置模型、编解码、校验和来源解析若长期集中在单一模块，也会放大循环依赖和无关上下文读取。
- 决策：配置加载完成后形成深度不可变快照；来源优先级固定为 `local_file < backend_override < validated_snapshot`；配置组持续携带版本、来源、生效时间、回滚来源和生效模式。`ns_common.config` 以 facade 保持公共导入稳定，内部依赖方向固定为 defaults/primitives/metadata → groups → validation → codec → resolver → model → facade；primitives 和 groups 不依赖根模型，validation 不依赖 resolver 或文件 I/O，codec 不读取全局 `ns_config`。runtime 深层模块只能接收显式配置依赖，不得直接读取全局配置单例或依赖 config 内部子模块。
- 后果：配置变化必须生成新快照并通过完整校验；非法覆盖不得部分生效；运行中不可变更的配置返回 `restart_required`。配置内部文件路径不属于公共契约，生产调用方继续只从 `ns_common.config` 或 `ns_common` facade 导入。
- 关联阶段/工作包：`P01-W01`、`P01-W02`、`P01-W03`、`P01-REF-01`、`P16`。

## ADR-002

- ADR 编号：`ADR-002`
- 状态：`ACCEPTED`
- 背景：静态启动配置与运行期选举、健康和切换状态属于不同生命周期；混用会让配置值被误解为集群权威。
- 决策：`runtime.cluster.role` 只允许 `singleton`、`sub_node`、`standby_master`、`active_master` 四个静态启动角色。`transitioning`、`draining`、`degraded`、`isolated`、`unavailable` 等只能作为运行期角色或健康状态，不能写入静态 role 配置。
- 后果：旧值和运行期状态不得通过别名或静默映射进入配置；P17 必须单独建立角色状态机和迁移规则。
- 关联阶段/工作包：`P01-FIX-01`、`P17`。

## ADR-003

- ADR 编号：`ADR-003`
- 状态：`ACCEPTED`
- 背景：仅凭节点配置或 transport 可达性无法防止 split-brain，也不能证明节点拥有全局协调写权限。
- 决策：配置为 `active_master` 不直接授予权威写权限。执行全局协调写入必须同时满足 backend 控制面授权、有效节点凭证、允许的运行期角色状态、Redis/Valkey leader lease/epoch 获取成功以及当前 fencing token 校验成功。
- 后果：lease 续约失败或 fencing 失效后必须停止权威写入；transport heartbeat、配置值和管理命令都不能单独完成 master 切换。
- 关联阶段/工作包：`P01-FIX-01`、`P06`、`P08`、`P17`、`P18`。

## ADR-004

- ADR 编号：`ADR-004`
- 状态：`PROVISIONAL`
- 背景：`runtime.cluster.active_master_url` 已作为 `sub_node` 的必填 URL 配置存在，但其 transport、发现、重连和授权语义尚未冻结。
- 决策：当前只保留 URL 语法与必填校验；不得把该字段自行解释为旁路 HTTP 控制端点、固定 WebSocket 地址、权威发现来源或 master 授权凭证。最终语义必须在 transport 和集群阶段联合定义。
- 后果：P04/P17 冻结语义前，调用方不得据此启动连接、推导协议或授予权限；未来定义必须兼容统一 Envelope、IAM、lease 和 fencing 边界。
- 关联阶段/工作包：`P01-FIX-01`、`P04`、`P06`、`P17`。

## ADR-005

- ADR 编号：`ADR-005`
- 状态：`ACCEPTED`
- 背景：业务时间戳需要可持久化和跨节点解释，而 deadline 与耗时计算不能受系统时钟校正影响。
- 决策：所有时间依赖通过显式 `Clock` 注入；持久化和跨节点时间使用 timezone-aware UTC wall clock，deadline 与耗时使用 monotonic clock。测试使用可控时钟，不依赖真实 sleep 漂移。
- 后果：禁止使用 naive datetime；UTC deadline 与 monotonic deadline 必须分别保存和校验；系统 wall clock 回退不得使本进程 deadline 回退。
- 关联阶段/工作包：`P01-W06`、`P02`、`P08`、`P11`、`P12`、`P17`、`P19`。

## ADR-006

- ADR 编号：`ADR-006`
- 状态：`ACCEPTED`
- 背景：runtime 多类实体需要可读、可校验且不会跨类型误用的标识符，同时标识符不能承担认证或授权语义。
- 决策：runtime_id、connection_id、session_id、message_id、summary_id、delivery_id、stream_id、plan_id、operation_id 使用各自稳定类型前缀加 32 位小写 RFC 4122 UUIDv4 hex；解析时校验前缀、格式、UUID 版本和期望类型。
- 后果：不接受大写、连字符、空白或隐式规范化；ID 只用于身份区分和引用，不作为凭证、租约或授权证明。
- 关联阶段/工作包：`P01-W07`、`P02` 至 `P19`。

## ADR-007

- ADR 编号：`ADR-007`
- 状态：`ACCEPTED`
- 背景：单个 delivery 的重试序号与 message 级共享自动重试预算描述不同维度；把二者绑定会破坏 fanout、恢复和跨 owner 调度。
- 决策：`retry_number` 是 delivery 自身从 1 开始的尝试序号；`RetryBudget.used_retries` 是 message 级共享预算消耗快照。二者显式传入并独立校验，不通过数值相等隐式关联。
- 后果：共享预算的权威原子消费必须由 StateStore 维护；单进程值类型不提供跨进程原子性；调度策略必须同时接收 delivery 序号和预算快照。
- 关联阶段/工作包：`P01-W08`、`P08`、`P11`、`P12`、`P18`。

## ADR-008

- ADR 编号：`ADR-008`
- 状态：`ACCEPTED`
- 背景：公开 `RetrySchedule` 会被调度、持久化和恢复路径直接构造；无效 deadline 或时间域混用会造成提前/延迟执行。
- 决策：`RetrySchedule` 保持冻结 dataclass，并强制正整数 retry number、有限非负 delay、timezone-aware UTC 时间、有限非负 monotonic 时间、deadline 不早于起点、两种时间差与 delay 在合理浮点误差内一致，且 budget 必须是 `RetryBudget`。
- 后果：直接构造与工厂构造遵守同一不变量；配置输入错误归一化为验证错误，注入策略或 Clock 的非法状态归一化为状态错误。
- 关联阶段/工作包：`P01-W08`、`P01-FIX-02`、`P11`、`P12`、`P19`。

## ADR-009

- ADR 编号：`ADR-009`
- 状态：`ACCEPTED`
- 背景：日志、错误和审计会接收任意嵌套对象、异常和自由文本；字段遗漏、对象异常行为、非标准 JSON 数值或无界摘要序列化都可能导致秘密泄露、覆盖原业务异常或造成 CPU/内存资源消耗。
- 决策：sanitizer 同时使用明确字段、后缀、路径和对象类型规则；对 token、password、secret、private key、authorization、cookie、credential、signature、业务 payload、原始 certificate、签名 URL 和 peer/client/remote IP/address 完全替换。Mapping key 也必须脱敏并保留冲突项。普通对象访问、异常字符串化和摘要规范化失败时 fail-closed，输出必须通过严格 JSON 编码。digest 必须遵守当前深度，并通过有界、确定性的规范化限制遍历节点、单容器项目、字符串、bytes 和规范化结果字节；超限直接返回 `[REDACTED]`，循环引用安全结束，mapping 与 set/frozenset 顺序不影响摘要。限制内 bytes 直接以原始 bytes 计算 SHA-256，不生成 hex 副本。peer/client/remote address 不使用无密钥摘要，直接替换为 `[REDACTED]`。Logger 只拥有或接收显式 `Sanitizer`，在 JSON/text/color 输出前把消息、格式参数、extra、异常对象和不含源码行的 traceback 元数据交给 sanitizer；Logger 不得定义、复制或放宽任何敏感字段、路径、对象、摘要或资源限制规则。Python LogRecord 内建字段与 JSON/text/color 权威输出字段使用独立保留集合；调用方冲突 extra 不得覆盖权威元数据，只能在 sanitizer 处理后进入 `extra_fields`，普通无冲突 extra 继续平铺。
- 后果：依赖方向固定为 Logger 调用 sanitizer，sanitizer 不引用日志类型或 formatter 语义；formatter 不直接字符串化或序列化原始 Envelope/extra/异常对象。`extra_fields` 本身也是权威保留字段，调用方同名值嵌套保留；冲突 key 脱敏碰撞沿用 sanitizer 的稳定后缀且不得丢项；text/color 的核心占位符和 ANSI 颜色继续使用真实 LogRecord level/status。不得对任意对象直接执行无界摘要序列化，不得泄露异常对象的原始失败内容；不得吞掉 `KeyboardInterrupt`、`SystemExit` 等进程级异常；digest 不引入全局状态或硬编码密钥。如未来需要地址跨日志关联，只能设计显式注入密钥的 HMAC，不得使用全局硬编码密钥。任意无标签自由文本仍要求调用方提供结构化字段或路径语义。
- 关联阶段/工作包：`P01-W09`、`P01-FIX-03`、`P01-FIX-04`、`P01-W10`、`P01-FIX-05`、`P03`、`P06`、`P20`。

## ADR-010

- ADR 编号：`ADR-010`
- 状态：`ACCEPTED`
- 背景：transport 写完成、QUIC packet ACK、stream ACK 与 runtime 可靠投递确认处于不同协议层。
- 决策：runtime `delivery.ack` 只表示目标逻辑连接收到了完整 Envelope，不表示业务执行开始或完成。transport write completion、transport ACK、stream ACK 和 path validation 都不能替代 runtime ACK，也不能直接更新 DeliveryRecord。
- 后果：ACK 必须经过统一 Envelope、processor、IAM/tenant/owner/fencing 校验和权威状态提交；业务执行结果需要独立消息类型表达。
- 关联阶段/工作包：`P03`、`P04`、`P05`、`P07`、`P11`、`P12`、`P15`、`P21`。

## ADR-011

- ADR 编号：`ADR-011`
- 状态：`ACCEPTED`
- 背景：DeliveryRecord、ACK/NACK/Defer、leader lease、owner/fencing 和控制审计需要跨进程、跨节点的原子一致性；普通 cache 的 soft-failure 语义不满足要求。
- 决策：生产强一致状态存储只能使用 Redis/Valkey，并通过统一 StateStore、事务/CAS、lease、fencing、Lua 原子迁移和状态日志访问。SQLite WAL 仅允许 local/dev/test，不得替代生产权威。现有通用 cache client 不得承载权威投递或集群状态。
- 后果：Redis/Valkey 不可用时，依赖强一致状态的受理、ACK、控制、lease 和 owner 变更必须失败或进入 degraded/unavailable，不能返回伪成功。
- 关联阶段/工作包：`P01-W03`、`P08` 至 `P19`。

## ADR-012

- ADR 编号：`ADR-012`
- 状态：`ACCEPTED`
- 背景：重试、恢复、owner transfer、master 切换和迟到 ACK 会产生旧 owner 或旧 epoch 的并发写入风险。
- 决策：owner、delivery lease 和 fencing 校验必须先于所有权威状态变更；全局协调写入和 owner 相关写入必须携带并校验当前有效 epoch/term 与 fencing token。关键迁移优先使用 Redis/Valkey Lua 原子完成状态、索引和日志更新。
- 后果：旧 owner、过期 lease、错误 fencing 或终态后的普通事件只能拒绝、审计或走显式管理路径，不能覆盖当前权威状态。
- 关联阶段/工作包：`P08`、`P10` 至 `P13`、`P17`、`P18`、`P19`。

## ADR-013

- ADR 编号：`ADR-013`
- 状态：`ACCEPTED`
- 背景：旁路 HTTP/JSON 管理接口会绕过统一协议版本、IAM、processor、可靠性、审计和状态机约束。
- 决策：查询、replay、cancel、hold、kick connection、drain node、switch master 和配置热更新等管理控制必须使用统一 Envelope、message type 注册和 processor 流水线；管理端是具有 management capability 的 runtime transport 客户端。
- 后果：不得创建私有管理协议或直接修改状态的旁路 API；管理请求仍需读取当前权威状态并执行 IAM、tenant、owner/fencing 和审计校验。
- 关联阶段/工作包：`P03`、`P06`、`P07`、`P08`、`P13`、`P16`、`P17`、`P20`。

## ADR-014

- ADR 编号：`ADR-014`
- 状态：`ACCEPTED`
- 背景：协议解析、身份建立、业务处理和功能开关若能被局部模块绕过，会产生 source/auth_context 伪造和未实现能力伪成功。
- 决策：入站 Envelope 必须先完成 codec 与 schema 校验，拒绝客户端自报的权威 source/auth_context，再经过 IAM、tenant、capability 和 processor 流水线。所有应用行为，包括 ACK/NACK/Defer、健康和管理控制，都必须进入 processor；未启用能力返回稳定错误并审计。
- 后果：transport、router、worker 和插件不得私建控制旁路；扩展 transport 或 message type 不能放宽核心 schema、权限或审计边界。
- 关联阶段/工作包：`P03` 至 `P07`、`P12`、`P16`、`P20`、`P21`。

## ADR-015

- ADR 编号：`ADR-015`
- 状态：`ACCEPTED`
- 背景：公共异常需要稳定的机器可读策略元数据和唯一索引，但自动扫描、装饰器注册或实例构造期间访问全局注册表会产生导入副作用、循环依赖和相互矛盾的错误码来源；把策略元数据直接附加到原错误序列化又会破坏既有响应格式。
- 决策：异常类自身的 `code`、`numeric_code` 和 `default_message` 保持唯一权威来源。各领域模块通过显式、冻结 definition 元组登记 severity、category、retryable、disconnect_required、audit_required、safe_detail 和稳定 action，再由 registry 显式聚合并构建不可变的类/code/numeric_code 索引；三类键必须全局唯一且 definition 必须与类属性一致。通用基础类、中间类或覆盖多种实际场景的宽泛异常采用保守副作用策略：未经精确语义证明时 retryable、disconnect_required、audit_required、safe_detail 均为 false，action 只给出检查、处理、拒绝或报告等不承诺自动副作用的机器提示。retry、disconnect 和 audit 只能由精确异常语义显式开启。processor timeout 只能证明调用未在期限内完成，不证明未产生副作用、已取消、外部调用失败、状态未写入或具备幂等性，因此默认不得提示自动重放 processor 执行。单条 protocol parse error 不等同于必须断开连接；连接级处置必须由更精确错误、策略和连接状态决定。已经确认的 protocol violation 应使用独立叶子错误并默认审计，但不得自动复制 forged identity 或 tenant mismatch 的强制断连语义。NACK reason 应尽量映射已登记的精确叶子 code，不得在已有精确语义时回退到宽泛领域基类。coverage matrix 必须同时受独立、人工冻结的设计场景清单约束，不能只与 registry 相互比较形成自证闭环。禁止 decorator 自动注册、import 副作用、动态模块扫描和 `__subclasses__()` 权威发现。exceptions 基础层不依赖 registry，整个 exceptions 包不依赖 sanitizer、logger 或 config；NACK reason 只可引用已登记 code 并保持稳定顺序。
- 后果：异常实例构造、捕获关系、details 和原四字段 `to_dict()` 不依赖注册表且保持兼容。策略 metadata 是精确异常类型的默认提示，不通过 Python 继承关系自动继承，也不是调用方必须无条件执行的命令；调用方必须使用 `get_error_definition(type(error))` 精确查询，并结合具体上下文、策略配置和阶段状态裁决。当前注册表不做 MRO fallback，精确类型没有可靠 definition 时必须保守处理；不得捕获宽泛基类后读取基类 definition 并自动 retry 或 disconnect。processor timeout 的实际 retry 必须由具体 processor 的幂等性、已知状态和显式策略共同授权。连续畸形消息、超大帧、恶意资源消耗、握手失败、限流、断连或安全升级属于后续策略和连接状态边界，不得从单次 parse failure 或普通 protocol violation 的默认 metadata 自动推导。metadata 序列化不得读取异常 details 或触发异常字符串化。`safe_detail` 不授权直接输出任意 details；实际错误日志、审计和未来错误 Envelope 仍必须经过 sanitizer 和各自输出边界。后续新增错误必须显式加入对应 definition 元组并通过类、code、numeric_code、独立设计场景和 NACK 完整性验证；W12 应通过细粒度叶子错误表达可重试、不可重试和安全处置差异，而不是扩大通用错误策略。
- 关联阶段/工作包：`P01-W11`、`P01-W12`、`P01-FIX-07`、`P03`、`P06`、`P07`、`P20`。
