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

## ADR-016

- ADR 编号：`ADR-016`
- 状态：`ACCEPTED`
- 背景：既有 `get_async_http_client()` 按名称访问进程全局 client map，可用于保持 backend 旧调用方兼容，但会隐藏创建参数、所有权和关闭边界；如果 runtime 深层模块直接使用该入口，测试隔离、资源回收和进程关闭顺序都无法由 composition root 证明。
- 决策：`NsHttpClientFactory.create()` 每次返回不登记全局状态的独立 `NsAsyncHttpClient`，直接调用方对该实例负责。需要统一生命周期时，composition root 创建局部 `NsHttpClientOwner`，只通过其 `create()` 创建并持有 client，再把显式 client 实例注入 runtime service。Owner 状态固定为 `open -> closing -> closed`，开始关闭后不再接受新 client，在同一 event loop 中串行化并发 `aclose()`，按创建顺序的逆序关闭。正常关闭可幂等重入；取消或普通关闭异常不得丢失尚未成功关闭的所有权，后续 `aclose()` 可继续回收。单个 client 的普通关闭异常不阻断 owner 尝试关闭其他 client，聚合错误只保留 client 名和异常类型。
- 后果：`get_async_http_client()` 和 `aclose_http_clients()` 继续保留原有按名称缓存/关闭兼容语义，但只是 legacy boundary；runtime 生产模块和测试不得调用该全局 getter。相同名称的显式 factory/owner client 与兼容 map 相互隔离。P02 必须在进程 composition root 中创建和关闭 owner；P06 的 IAM client 只接收显式实例。HTTP 错误 body、URL、token 和 response sanitizer 仍由 P01-W14 冻结，本 ADR 不宣称当前错误输出已安全化。
- 关联阶段/工作包：`P01-W13`、`P02`、`P06`。

## ADR-017

- ADR 编号：`ADR-017`
- 状态：`ACCEPTED`
- 背景：HTTP status、JSON decode 和 transport failure 若复制原始 response body、URL、底层异常文本或异常 cause，会把 IAM token、credential 和上游私有错误带入日志与错误明细；另一方面，IAM 等调用方仍需要从已知响应 schema 中提取少量可诊断字段。
- 决策：`NsHttpResponse.text`、`url` 和成功路径 `json()` 保持原始调用语义，但所有 HTTP 诊断只使用 `safe_url` 和 `safe_body_summary`。默认 body 摘要不得复制正文、正文片段、正文 digest 或任意响应头值，只保留 `present`、`text_length`，并把 Content-Type 映射为固定的 `json/text/binary/other` 分类。新增同步 `NsHttpResponseSanitizer`：client、factory、owner、legacy getter 可配置默认回调，单次 request/get/post/put/delete 可覆盖；回调只返回结构化 mapping 或 `None`，接收与真实响应隔离的快照，其修改不得改变真实 status、URL、headers、text 或后续状态判断。回调结果必须再次经过公共 `Sanitizer`；普通异常、非 mapping 或公共 sanitizer 失败时只记录稳定的 fail-closed 状态，不复制失败文本；`KeyboardInterrupt`、`SystemExit` 等进程级异常不得吞掉。`bearer_token` 只写入 Authorization header；请求参数先冻结为 `httpx.QueryParams`，若当前 token 出现在解析后的 base URL、request URL 或 query 参数中，必须在发送前以无 token 的稳定验证错误拒绝。completion log、status error、JSON decode error 和 request failure 只使用安全 URL；异常响应 URL 的 path 若仍反射当前 bearer token，则整条诊断 URL 替换。transport failure 不保留底层异常文本或异常对象，JSON decode failure 不保留含原始 doc 的 decode exception context。
- 后果：业务调用方仍可读取成功响应正文，但不得直接把 `text`、`url` 或原始 response 对象写入日志/错误/审计。response sanitizer 必须是无 I/O 的同步 schema 适配器，并用有语义的字段名返回确有必要的安全诊断值；公共 sanitizer 只能识别已登记字段、路径和文本模式，无法证明无标签任意字符串安全，调用方仍受 ADR-009 约束。未提供回调时错误正文只产生固定元数据，不生成可离线关联的正文 digest。该 token guard 保护通过 `bearer_token` 参数提供的当前凭据，不把所有 query 参数一律禁止；未来 payload_ref 的签名 URL 仍按其专用授权和脱敏边界设计。
- 关联阶段/工作包：`P01-W14`、`P06`、`P10`、`P20`。

## ADR-018

- ADR 编号：`ADR-018`
- 状态：`ACCEPTED`
- 背景：metrics、trace 和 diagnostic snapshot 是允许丢失或异步补偿的旁路观测数据；若公共接口直接绑定 HTTP/OTLP exporter、全局 client、runtime 私有模型或强一致状态写入，后续模块将无法隔离测试、替换 exporter 或证明观测故障不影响可靠投递主链路。常规时序指标还必须防止 connection/message/delivery/trace 等唯一标识造成无界标签基数。
- 决策：公共观测边界由 `MetricsSink`、`TraceSink` 和 `DiagnosticSnapshotSink` 三个可显式注入的结构化协议组成。`record() -> bool` 是同步、本地、不得执行外部 I/O 的 best-effort 接收边界：`True` 表示本地实现接受记录，`False` 表示正常生命周期或容量策略拒绝，二者都不构成持久化或远程导出证明。sink 关闭是正常生命周期状态；内存实现必须在同一临界区内原子裁决写入或关闭，关闭后的正确类型记录返回 `False`，不得用运行状态异常破坏 processor、ACK、控制、集群协调、可靠投递或关闭主链路。`dropped_count` 只累计有界容量淘汰的最旧记录，`rejected_count` 只累计 sink 已关闭后的拒绝；`clear()` 清空记录并重置 `dropped_count`，但保留生命周期级 `rejected_count`。`flush()` 在无 I/O 的内存实现中关闭前后都安全，`aclose()` 幂等；明确的调用方类型错误仍可使用验证错误，进程级异常不得吞掉。
- 决策：metric attribute 采用“显式允许 + 可证明有限值域”，而不是自由标量或仅靠危险 key 黑名单。冻结的 metric definition 必须逐项声明 attribute key、string/integer/boolean 类型和不可变有限允许集合；string 与 integer 必须具有非空有限集合，boolean 的值域固定有限，float 与嵌套结构不得作为 label。35 个标准指标名各自具有显式、不可变 definition；尚未确认需要 label 的指标使用空 schema，尚未确认的 kind/unit 可以保持未冻结，但不得因此开放无界 label。非标准 metric 仅在 attributes 为空时可省略 definition；attributes 非空时必须显式提供同名 definition。高基数 key 的规范化精确/后缀防御继续保留为第二道防线，不能替代 allowlist；connection/session/message/delivery/trace/request/raw tenant ID 等前缀别名同样拒绝。`tenant_scope` 只允许 `system`、`tenant`、`cross_tenant`、`shared`、`unknown` 五种稳定分类，不是 tenant ID、名称、邮箱或调用方自定义 scope 的别名。metric attribute 在公共 `Sanitizer` 处理前后都必须重新满足同一 definition，sanitizer 不得成为 schema 绕过路径。
- 决策：记录对象在进入 sink 前形成 timezone-aware UTC、深度不可变、经公共 `Sanitizer` 处理且可用 `allow_nan=False` 严格编码的快照。`MAX_OBSERVABILITY_RECORD_BYTES` 约束完整公开 `to_dict()` 结果以 `allow_nan=False`、`ensure_ascii=False`、紧凑分隔符和排序 key 编码后的 UTF-8 字节数，不只是 attributes 或 snapshot 子 mapping。metric 与 trace 的完整记录超限时返回不复制记录内容的稳定验证错误；diagnostic snapshot 先检查完整记录，超限后替换为稳定 size-limit 占位并再次检查，连占位也无法满足边界时必须验证失败。普通 sanitizer 失败转为稳定 fail-closed 状态，`KeyboardInterrupt`、`SystemExit` 等进程级异常保持穿透。trace 和按需 diagnostic snapshot 可以携带高基数标识，但仍必须经过脱敏与完整记录大小限制。
- 后果：P02 composition root 必须创建并显式注入 sink，在停止新任务后调用其 `flush()`/`aclose()`；深层 runtime 模块不得获取全局 sink。P02/P04 及后续真实 collector 在使用对应标准 metric 前必须补齐已经确认的 kind/unit 和有限 attribute 语义，不能以 definition 中的未冻结字段推断业务统计含义。P20 可增加 OTLP、Prometheus、backend 推送或其他 adapter，但不得修改公共记录安全边界、在同步 `record()` 中发起网络 I/O，或把 exporter 成功解释为强一致状态提交。未启用 adapter 时标准指标可以不采集，不能因此宣称对应 transport 已实现。
- 关联阶段/工作包：`P01-W15`、`P01-FIX-08`、`P02`、`P04`、`P05`、`P07`、`P14`、`P20`、`P21`。

## ADR-019

- ADR 编号：`ADR-019`
- 状态：`ACCEPTED`
- 背景：后续 runtime 测试会同时使用文件配置、SQLite、可控时间、观测 sink、监听端口和真实 Redis/Valkey。若测试直接读取仓库 `data/etc/log/tmp`、修改全局 `ns_config` 或环境变量、先探测空闲端口再关闭重绑、复用固定 Redis key 前缀，串行和并行测试都会产生跨用例污染；若用 `FLUSHDB`/`FLUSHALL` 清理，则会破坏共享开发实例中的其他数据。把 Redis Python 驱动或服务进程生命周期硬编码进公共工厂，还会提前混合 P01-W17 的依赖分层和调用方所有权。
- 决策：`ns_common.testing` 只提供实例级、显式拥有的测试资源，不建立模块级 mutable registry，也不修改环境变量、仓库路径常量、全局配置/cache/http/sink 单例。`NsTestResourceFactory` 为每个实例创建并回收独立临时根目录及 `data/etc/log/tmp` 子目录；临时配置写入该实例的显式文件，默认使用确定性的 UTC epoch，并强制已知 SQLite、日志锁目录和 Redis namespace 字段落在实例隔离边界。每次请求的 `ControlledClock`、内存 sink bundle、配置 namespace 都是新对象。测试端口必须让操作系统以 port 0 分配并保持 TCP socket 绑定，调用方可以直接把该 socket 交给 server；仅返回一个已经关闭探测 socket 的端口号不构成无竞态 reservation。工厂关闭按所有权释放仍绑定的端口和临时目录，关闭后拒绝创建新资源。
- 决策：`NsReservedPort` 自身也是底层 socket 的显式 owner。`release()` 必须在 reservation 自身的锁内完成真实 `socket.close()`，且只有该调用正常返回后才能清空 socket 引用；普通关闭异常或 `KeyboardInterrupt`、`SystemExit` 等进程级异常穿透时都必须保留同一 socket，供后续调用重试。该锁覆盖真实关闭调用，使调用方直接 `release()` 与 Factory `close()` 共享同一关闭屏障，不会并发执行两个底层 close，也不会在底层关闭仍执行时提前宣称完成。`is_released=True` 严格表示底层 close 已成功完成；`release() -> False` 只表示本次调用开始前已经真实释放，不表示本次关闭失败。Factory 只有在 reservation 的 `release()` 正常返回后才可将其从端口所有权集合移除。
- 决策：`NsTestResourceFactory` 生命周期固定为 `OPEN -> CLOSING -> CLOSED`，状态只能前进。第一次关闭开始即进入 `CLOSING` 并拒绝目录访问、临时配置、clock、sink、端口和 Redis namespace 的全部新建/托管入口；`is_closed` 只在状态为 `CLOSED` 时成立。只有全部仍持有的端口 reservation 已成功释放且 `TemporaryDirectory.cleanup()` 已成功返回后才能进入 `CLOSED`；任一清理失败时保持 `CLOSING`，不得为了重试重新开放资源创建。
- 决策：Factory 关闭是同步并发屏障，同一时刻只能有一个清理执行者；其他 `close()` 调用必须等待当前尝试结束，成功后共同观察 `CLOSED`，失败后由一个调用者串行接手未完成资源的下一次重试。端口继续按逆创建顺序尝试，只有单个 reservation 成功释放后才从所有权集合精确移除；失败 reservation 保留。临时目录只有 cleanup 成功后才转移所有权；已成功释放的端口或目录不再重复清理。`close()` 正常返回保证 Factory 不再持有任何待清理资源。
- 决策：一次关闭尝试必须继续处理所有可安全尝试的资源。普通清理异常聚合为稳定 `NsStateError`，只公开 operation、`closing` 状态、稳定资源类别、数量、剩余端口数、目录待清理标记和底层异常类型名；不得复制路径、host、端口、Redis namespace、异常文本、异常对象或底层 cause/context。`KeyboardInterrupt`、`SystemExit` 等进程级异常保持穿透，穿透前已成功释放的资源仍移出所有权集合，未完成资源继续保留且状态保持 `CLOSING`，后续调用仍可重试。Factory 关闭不拥有或关闭 Redis/Valkey client，也不负责外部服务进程生命周期。
- 决策：真实 Redis/Valkey 由调用方创建并持有 client；工厂只创建由安全 key part 和随机 UUID 组成的唯一 `key_prefix:namespace:`。同步/异步托管上下文在进入和退出时使用注入 client 的 `scan_iter(match=prefix*)` 与有界批量 `delete()` 清理，逐 key 复核所有权；scan 返回前缀外 key 时必须停止且不得删除该 key。公共实现禁止调用 `KEYS`、`FLUSHDB` 或 `FLUSHALL`，不隐式选择 Redis database，也不关闭调用方 client。退出清理前，调用方必须先停止仍会向该 namespace 写入的 task/process；namespace 清理不等于强一致 StateStore、Redis Cluster、lease、fencing 或故障恢复验证。
- 后果：P02 及后续单元、契约和 standalone 集成测试应复用该工厂并显式传递资源，不得自行使用仓库真实目录、固定端口或共享 Redis 前缀。P01-W17 负责提供 Redis/Valkey 等测试驱动和独立测试依赖清单；P08/P17/P20 再分别验证 StateStore、集群协调和故障场景。需要把 reservation 交给不接受现有 socket 的第三方 server 时，调用方只能在启动前最后时刻显式释放并承担交接窗口，不能把“探测到过空闲”当作端口所有权证明。
- 关联阶段/工作包：`P01-W16`、`P01-FIX-09`、`P01-W17`、`P02` 至 `P22`。

## ADR-020

- ADR 编号：`ADR-020`
- 状态：`ACCEPTED`
- 背景：原仓库只有彼此重复 pin 公共依赖的 backend/runtime 两份生产清单；runtime 清单未登记 Linux 优先使用的 uvloop，也没有 Redis/Valkey 测试驱动或独立压测层。若测试驱动、压测工具、未来 QUIC/WebTransport 实验库直接并入生产清单，backend 与 runtime 会获得无关依赖，无法证明组件可独立安装。安装 Redis 驱动还暴露了既有导入耦合：模块级 cache 多进程 logger 会立即加载 concurrent-log-handler 和 portalocker，而 portalocker 会在 Redis 可用时导入驱动，使仅导入公共测试工厂也产生驱动副作用。基于 gevent 的压测工具还会接管线程/协程行为，污染标准 asyncio 与 uvloop 的对照基线。
- 决策：依赖采用单向无环五层结构。`requirements-common.txt` 只承载 backend/runtime 共同生产基础；`requirements-backend.txt` 和 `requirements-runtime.txt` 分别只包含各自生产增量并只引用 common；`requirements-runtime-test.txt` 只引用 runtime 生产层并增加 Redis/Valkey 测试驱动；`requirements-runtime-benchmark.txt` 只引用测试层并增加不接管事件循环的 pyperf 与 psutil。每个显式包必须使用精确 `==` pin，include 只能指向仓库根目录已登记清单，禁止循环、VCS、editable 或本地路径依赖。backend 不得引用任何 runtime、测试或压测清单。
- 决策：uvloop 作为 runtime 生产依赖使用非 Windows environment marker，Windows 继续只使用标准 asyncio；WebSocket 保留在 runtime 生产层。Redis/Valkey Python 驱动在 P08 冻结 StateStore 生产合同前只属于测试层，安装它们不代表生产强一致存储已经实现。aioquic、pylsqpack、qh3 等 QUIC/WebTransport 实验依赖在 P21 前不得进入任何当前清单；P21 必须通过独立 adapter/capability 和依赖隔离验收后再决定清单归属。压测工具不得隐式 monkey-patch 或替换被测 event loop；未来 P22 引入其他负载发生器必须保持显式隔离并重新验收 asyncio/uvloop 可比性。
- 决策：`NsLogger` 的 concurrent-log-handler 子类和 `ns_common.cache` 多进程 logger 延迟到实际使用时加载。普通导入 `ns_common` 或 `ns_common.testing` 不得因为测试环境已安装 Redis/Valkey 而加载 concurrent-log-handler、portalocker、Redis、Valkey 或创建 cache client；真正使用多进程日志时仍按既有配置创建 concurrent handler，缺失依赖继续稳定失败。该调整只改变可选依赖加载时机，不改变 LOG-1 输出、脱敏、rotation、cache soft-failure 或 TST-1 client 所有权契约。
- 后果：P02 生产或最小运行环境只安装 runtime 生产清单；普通 runtime 测试显式安装 test 清单；性能进程才安装 benchmark 清单。清单结构和禁止包由自动化门禁持续验证，真实隔离环境还必须执行 pip resolver、`pip check`、导入与冷启动检查。P08、P21、P22 若新增生产 StateStore、QUIC/WebTransport 或负载工具，必须修改对应最窄层并重新验证 backend/runtime 生产环境没有依赖泄漏。
- 关联阶段/工作包：`P01-W17`、`P02`、`P04`、`P08`、`P20`、`P21`、`P22`。

## ADR-021

- ADR 编号：`ADR-021`
- 状态：`ACCEPTED`
- 背景：RuntimeService 的一次性启动边界需要同时区分“禁止 restart”和“资源已成功清理”。如果把 `STOPPED` 与 `FAILED` 都建模为无条件拒绝 `stop()` 的绝对终态，重复关闭会报错，启动或关闭失败后也无法回收部分资源；如果 event-loop owner 的首次绑定没有同步保护，两个线程中的独立 event loop 还可能同时进入 asyncio lifecycle lock，暴露非确定性的底层 loop mismatch。
- 决策：RuntimeService 的公开状态固定为 `created`、`starting`、`running`、`stopping`、`stopped`、`failed` 六态，并保持一次性启动、不支持 restart。`start()` 只允许 `CREATED -> STARTING -> RUNNING`；start hook 抛任意 `BaseException` 时先进入 `FAILED` 再原对象穿透。`RUNNING`、`STOPPING`、`STOPPED`、`FAILED` 均不得再次 start，start 失败或取消后也不会自动调用 stop hook，资源清理由调用方显式触发 `stop()`。
- 决策：`stop()` 从 `CREATED` 调用时保持稳定非法迁移错误；在 `STARTING` 或 `STOPPING` 期间发起的同 loop 调用等待当前 lifecycle 尝试完成，再根据完成后的权威状态处理。`RUNNING` 和 `FAILED` 都允许进入 `STOPPING` 并执行 stop hook；成功后进入 `STOPPED`，普通异常、取消、`KeyboardInterrupt`、`SystemExit` 或其他 `BaseException` 则先回到 `FAILED` 再原对象穿透。`FAILED` 表示启动、运行或清理失败，不表示资源已经释放；后续 `stop()` 可以继续执行或重试清理。`STOPPED` 禁止 restart，但同一 owner event loop 上的 `stop()` 幂等正常返回且不重复执行 hook；只有 `STOPPED` 才表示 lifecycle cleanup hook 已成功完成。
- 决策：同一 event loop 内的 start/stop 继续由实例级 asyncio lifecycle lock 串行化，hook 在锁内执行。并发 start 中只有首个调用可以执行 start hook；并发 stop 中同一时刻只有一个 stop hook 执行。首个关闭成功后等待者观察 `STOPPED` 并正常返回；首个关闭失败后，一个观察到 `FAILED` 的等待者可以接管下一次清理，成功后其余等待者不再重复 hook。该模型不增加公开 attempt 状态、后台 task 或额外清理报告。
- 决策：event-loop owner 的首次绑定使用独立实例级同步锁，只在锁内比较和设置 loop 引用，不在锁内 await、运行 hook 或获取 asyncio lifecycle lock。只有一个 loop 能成为 owner；其他 loop 必须在尝试获取 lifecycle lock 前收到固定 `NsStateError`。跨 loop 错误只公开 component、operation、current_state 和 `event_loop_mismatch` reason，不公开 loop/task/thread repr、线程标识或底层 asyncio 异常文本。
- 决策：start/stop hook 的普通异常、取消和进程级异常均保持原类型和原对象穿透，状态必须在穿透前进入 `FAILED`。RuntimeService 不保存异常对象、异常文本或底层 cause，不把其内容复制到状态、非法迁移错误或跨 loop 错误；稳定非法迁移错误继续只包含 component、operation、current_state、requested_state 和 allowed_target_states。
- 决策（P02-FIX-05 校准）：RuntimeService 登记的 runtime-owned critical supervised task 出现非取消异常时，必须请求同一 RuntimeShutdownCoordinator 并从 `RUNNING` 进入 `FAILED`；后续显式 `stop()` 严格按既有 RSL-1 执行 `FAILED -> STOPPING -> STOPPED` 统一清理，只有清理失败才回到 `FAILED`。critical 退出原因与失败任务历史由 `RuntimeShutdownReport.reason/failed_tasks` 保留，不新增历史状态或改变六态含义。联动不保存或输出异常对象、message/repr/cause；正常取消不得触发。普通 probe、clock、metric/sink 等已经由所属合同定义为 fail-soft 的失败不属于 critical task terminal failure。
- 后果：P02-W06 可以在这一生命周期基础上增加信号驱动的进程关闭、实际资源关闭编排和超时观测，但不得重新把 `STOPPED` 后 stop 改为错误，也不得禁止 `FAILED` 后显式清理或重试。后续 RuntimeContext、HTTP owner、sink、TaskSupervisor 和 transport 资源必须通过 stop hook 遵守相同的一次性启动、失败保留所有权和成功后才进入 `STOPPED` 的边界。
- 关联阶段/工作包：`P02-W02`、`P02-FIX-01`、`P02-W06`、`P02-W07`、`P02-FIX-05`。

## ADR-022

- ADR 编号：`ADR-022`
- 状态：`ACCEPTED`
- 背景：runtime 后续模块需要共享配置快照、时间、日志、观测和任务监督能力。如果深层模块自行读取全局 `ns_config`、按名称获取 logger/client/sink，或通过模块级 current context、ContextVar、字符串 registry 和 ambient getter 查找依赖，则 composition root 无法证明实例隔离、测试替换、资源所有权和关闭顺序。另一方面，把尚未冻结的 transport、StateStore、processor 等接口提前放进无类型字典，会把显式依赖容器退化为服务定位器。
- 决策：`RuntimeContext` 是冻结、slots、仅关键字构造的进程级接线快照。必需字段固定为 `NsConfig`、`Clock`、`logging.Logger`、`MetricsSink`、`TraceSink` 和 `TaskSupervisor`；context 保留调用方注入对象的身份，不复制配置、不创建默认 logger/sink/supervisor，也不读取环境、文件或全局服务。`config_snapshot`、`metrics_sink` 和 `trace_sink` 只是对应必需字段的只读身份别名。生产接线仍须遵守 `CFG-1`、`LOG-1` 和 `OBS-1` 的安全边界。
- 决策：`RTC-1` 的“显式依赖”同时约束 API、模块导入和 `RuntimeContext` / `RuntimeDependencySlots` 构造期类型验证。冷导入或合法/非法构造均不得仅为判断类型而导入 `ns_common` package，也不得经 `config.model` 的全局 `ns_config` 或 `http_client -> logger` 链读取环境、访问配置文件、创建运行目录、初始化 logger handler、创建 HTTP client、task、thread 或 event loop。类型引用使用 postponed annotations 和 `TYPE_CHECKING` 保留具体公共类型；运行时验证只从有限且固定的已加载规范模块取得实际类对象并执行 `isinstance`，模块未加载即稳定拒绝，不通过 import 补载。该边界不按类名字符串放行、不查找依赖实例，也不提供可扩展 registry 或 service locator。用于拒绝非法依赖的规范 `NsValidationError` 由仅依赖标准库的内部引导边界提供，`ns_common.exceptions` 继续重导出同一类对象，公开继承、code、numeric code、message 和 details 合同不变。`NsConfig`、`NsHttpClientOwner` 等字段不得因此退化为 `Any`、dict 或任意 object；默认 `None` 和非 `None` 的错误 HTTP owner 均不得加载 HTTP/logger/config 链。
- 决策：后续公共依赖使用冻结且有限的 `RuntimeDependencySlots`。当前只为既有公共合同 `DiagnosticSnapshotSink` 与 `NsHttpClientOwner` 提供可选类型化槽位；未注入时明确为 `None`。不得增加按字符串查找的 mapping、`get/register/resolve` API、模块级 context 单例、线程局部变量或 ContextVar。尚未冻结的 runtime 私有依赖必须在其所属工作包明确接口后增加类型化字段或专用子上下文，不能通过任意 object bag 提前绕过契约。
- 决策：所有字段在构造时验证公共类型。错误固定为不含依赖值或 repr 的 `NsValidationError`，details 只含 component、dependency、expected_type 和 actual_type；不得复制配置、路径、URL、credential、对象 repr 或底层异常文本。context 的冻结只保证字段引用不能替换，不声称 logger、sink、TaskSupervisor 或 owner 的内部生命周期不可变。
- 决策：每个 `RuntimeService` 必须通过构造参数接收一个有效 `RuntimeContext`，并通过只读 `context` 属性保持同一对象身份；不提供无参 fallback 或隐式默认 context。W03 只建立接线关系，构造 context/service 时不得创建 task、client、listener 或 exporter，也不得启动、flush、关闭任何依赖。配置加载与启动前校验、composition root、信号和资源关闭顺序仍由后续 P02 工作包负责；只有未来 stop hook 按 `RSL-1` 成功完成资源清理后，service 才能进入 `STOPPED`。
- 后果：深层 runtime 模块可以通过显式构造参数接收所需 context 或其中的具体依赖，不再需要全局服务定位。package facade 和 `main.py` 可以继续保持无启动副作用，直到 composition root 工作包显式接线。后续为 RuntimeContext 增加字段属于 `RTC-1` 变更，必须使用已冻结类型并重新运行 P02 与下游回归；不得借字段扩展提前宣称 transport、StateStore、角色、观测 collector 或关闭编排已经实现。
- 关联阶段/工作包：`P02-W03`、`P02-FIX-02`、`P02-W04`、`P02-W06`、`P04` 至 `P08`。

## ADR-023

- ADR 编号：`ADR-023`
- 状态：`ACCEPTED`
- 背景：`NsConfig` 已冻结字段级与跨组校验，`NsEventLoopSelector` 已冻结平台和可选 uvloop 语义，但进程入口此前没有统一证明执行环境、配置、Python 依赖、目录、transport feature gate、生产 StateStore 限制和 TLS 前置条件均在 event-loop policy 与未来 listener 生效前通过。若这些检查散落到异步 service hook 或各 transport adapter，配置错误可能在部分资源已启动后才暴露，未来 P04 也无法证明 listener 之前存在唯一 fail-closed 边界。另一方面，当前尚无 transport adapter、StateStore 或生产证书合同，preflight 不能把“配置可接纳”伪装成对应能力已实现。
- 决策：新增 `RSP-1` 同步启动边界。`RuntimeStartupPreflight` 必须接收已构造的显式 `RuntimeContext` 和可替换的 `RuntimeStartupDirectories`；`validate()` 执行同一组检查但不替换 event-loop policy，`prepare()` 只有在此前全部检查成功后才调用已冻结的 `NsEventLoopSelector.install()`。固定顺序为严格解析 local/dev/test/prod、验证完整不可变配置与 startup security、执行 transport 配置准入、检查固定 Python 依赖和本机服务端 TLS context 能力、创建并确认显式目录可访问，最后选择或安装 policy。任何失败都不得创建 listener、transport session、StateStore、HTTP client、exporter、task 或线程。
- 决策（P02-FIX-03 校准）：composition root 不得用 `NsConfig.load(config_path=None)` 加载启动快照，因为 CFG-1 的兼容语义会在配置、依赖和 TLS 门禁前调用 `ensure_runtime_dirs()`。`main()` 必须先严格解析环境，再显式解析默认配置文件路径，并将该非空路径交给 `RuntimeStartupPreflight.load_config_snapshot()`；后者与 preflight 的配置二次验证共用唯一 field/reason 归一化函数。生产明文、关闭 `require_tls_in_prod`、非生产禁止明文、生产非 Redis/Valkey StateStore 都归一为 `RUNTIME_STARTUP_SECURITY_ERROR`，普通 `NsConfigError` 保持原类型、code 与 details。
- 决策（P02-FIX-03 冷进程校准）：仅修复显式 load 不足以满足 RSP-1，因为首次 import `ns_common` 会经 cache/logger/config facade 请求 model 级 global `ns_config`。新增内部 `ns_runtime._bootstrap`，只从权威模块重导出默认路径、唯一 `NsConfig` 类型、startup 错误类型和路径常量；禁止另行加载、复制或代理配置类。`ns_common.config.model`、`ns_common.config` 和 `ns_common` 使用线程安全模块属性，仅在调用方显式请求 `ns_config` 时创建一次真实 `NsConfig` 并缓存同一身份；cache client、logger 与 Django cache 也只在实际使用全局配置时请求该属性。裸 package/submodule/bootstrap import 不得创建 global config。CFG-1 的公开名称、`__all__`、真实类型、跨 facade 身份、默认路径、校验、错误、序列化及显式 `NsConfig.load(config_path=None)` 调用 `ensure_runtime_dirs()` 的兼容语义保持不变；变化只限于不再把 package import 等同于显式请求 global config。
- 决策：startup 环境不采用未知值静默回退；非法环境返回稳定 `RUNTIME_CONFIG_INVALID`。生产环境中任一启用入站 transport 必须配置 TLS，StateStore backend 只能为 Redis/Valkey；非生产明文继续受 `allow_plaintext_non_prod` 控制。上述安全违规统一为稳定 `RUNTIME_STARTUP_SECURITY_ERROR`，不复制 URL、路径、credential、底层异常文本或 cause。TLS 前置检查在本阶段只证明 Python 运行时能够创建服务端 TLS context；证书、私钥、CA、最小版本、cipher 与 reload 属于 P20，不得由本结果推断为已验证。
- 决策：当前 transport 准入表只允许设计基线 `websocket_tcp`，并在其配置启用时检查 runtime 生产依赖 `websockets`；该准入只表示配置可进入后续 P04 实现，不表示 listener 或 adapter 已存在。`websocket_http3`、`webtransport_http3` 和 `quic_native` 在对应阶段前一旦启用即返回稳定 `RUNTIME_TRANSPORT_DISABLED`。Redis/Valkey Python driver 仍按 `DEP-1` 留在测试层，P08 冻结 StateStore 生产合同前 preflight 只执行生产 backend 配置限制，不探测、连接或宣称 StateStore 可用。
- 决策：目录接线是冻结、显式路径集合，默认覆盖仓库 data/etc/log/tmp；SQLite 开发配置还准备其显式文件 parent。目录错误只公开稳定目录角色与失败类别，不公开真实路径或底层错误。preflight 结果冻结且只包含环境、event-loop 选择、是否安装 policy、配置化 transport/TLS adapter 名、StateStore backend、已检查固定依赖和已准备目录角色；它不是 capability registry、健康证明或资源 owner。
- 决策：唯一 `main.py` 继续通过函数内延迟 import 保持 package 与入口模块冷导入无配置、policy 和资源副作用。实际冷调用 `main()` 时先进入 `_bootstrap`，按显式路径加载并归一化配置，构造最小显式 `RuntimeContext`，执行 `prepare()`，然后才导入、构造并通过新 policy 运行一次无监听 `RuntimeService` start/stop 生命周期。配置、transport、依赖或 TLS 失败均不得初始化 global `ns_config`、调用 `ensure_runtime_dirs()`、准备仓库或显式 preflight 目录、安装 policy 或构造 service。runtime 依赖缺失时进程稳定失败；按 `DEP-1` 不安装 runtime 包的 backend 环境只验证该 fail-closed 分支。P02-W06 不得把 preflight 移入已运行的 loop 或 listener 之后。
- 后果：P04 创建首个 listener 时必须以成功的 `RSP-1` preflight 为前置，并继续独立完成 adapter/conformance；P08、P20 分别补齐真实 StateStore 与完整 TLS 生产校验。W04/FIX-03 不改变 `CFG-1` 的公共对象和显式加载合同、`RSL-1` 或 `RTC-1`，不向 context 增加未冻结依赖槽位，也不宣称角色、信号关闭、loop lag、IAM、WebSocket、Redis/Valkey 或 TLS 证书能力完成。composition root 当前注入普通 `logging.Logger`；W05 开始实际使用 runtime logger 前必须完成生产安全日志接线。
- 关联阶段/工作包：`P02-W04`、`P02-FIX-03`、`P02-W05`、`P02-W06`、`P04`、`P08`、`P20`。

## ADR-024

- ADR 编号：`ADR-024`
- 状态：`ACCEPTED`
- 背景：设计允许 singleton、sub_node、standby_master、active_master 作为进程初始角色，同时要求角色状态机未来表达 transitioning/draining，并把 degraded/isolated/unavailable 保持为独立健康维度。但 P02 尚无 transport、StateStore、leader lease、fencing、delivery 或集群协调；若仅凭 active_master 配置值开放协调路径，或让未完成接口返回空成功，就会违反 active 权威双重条件与 `INV-015`。角色门禁开始产生审计后，composition root 也不能继续使用无 sanitizer 的普通 Logger，且不能为接日志恢复 RSP-1 已消除的 global config 和提前目录副作用。
- 决策：新增 `RRS-1`。RuntimeRole 明确 singleton、sub_node、standby_master、active_master、transitioning、draining，RuntimeHealth 独立明确 healthy、degraded、isolated、unavailable。P02 只允许四个稳定角色作为配置初值并构造本地只读 RuntimeRoleState/RuntimeRoleSnapshot；不提供角色或健康 mutation/transition API。transitioning/draining 与健康枚举只冻结领域边界，不表示对应切换、drain 或隔离行为已实现。
- 决策：P02 的 transport、cluster_coordination、delivery capability 固定为 false。唯一查询执行入口 `require_capability()` 必须记录固定的 event/component/capability/role/error_code/reason 审计字段并抛 `RUNTIME_FEATURE_DISABLED`，不得返回布尔成功、空结果或 stub success；日志写入普通失败也不得放行功能。错误 details 只含固定 component、capability、role 和 reason，不含 URL、node_id、配置正文、credential、对象 repr 或底层日志异常。
- 决策：`RUNTIME_FEATURE_DISABLED` 作为 audit-required 的公共稳定叶子错误追加到 ERR-1，numeric code 200165，不复用 transport/delivery/cluster 领域错误伪装通用门禁，也不修改任何既有错误编号、继承、策略或 NACK 映射。P03 的 FeatureDisabledProcessor 和后续未启用能力应复用该错误，但仍须遵守各自 Envelope、processor 和强审计边界。
- 决策：生产 runtime logger 只在 RSP-1 preflight 全部成功且显式目录已准备后创建。NsLogger 可接收显式配置 mapping 与显式 log root；显式模式不得读取 global `ns_config`，未提供显式参数时保留原兼容行为。main 的 preflight context 使用无 handler bootstrap Logger，成功后才以当前配置快照、runtime log level、Sanitizer 和 startup log_dir 构造 NsLogger，并复用同一 clock、sink、TaskSupervisor 和 dependency slots 创建最终 context。该两段接线不改变 RTC-1 的冻结身份规则，也不使 context 成为资源 owner。
- 后果：active_master 仅是初始本地角色标签；在同时满足 backend 控制面授权、节点凭证、角色允许、Redis/Valkey leader lease 与有效 fencing_token 前，不得执行全局协调写入。P04/P10/P17/P08 分别实现 transport、delivery、集群角色权威和强一致/审计后，才能按契约有选择地启用对应 capability。P02-W06 负责 logger/sink/supervisor 等资源的关闭编排，不得把当前 main 的一次性自检误当作完整信号生命周期。
- 关联阶段/工作包：`P02-W05`、`P02-W06`、`P03-W11`、`P04`、`P08`、`P10`、`P17`。

## ADR-025

- ADR 编号：`ADR-025`
- 状态：`ACCEPTED`
- 背景：P01 的 TaskSupervisor、observability sinks、HTTP owner 和 logger 已各自具备显式生命周期，P02 的 RuntimeContext 与 RuntimeService 也已冻结依赖身份和一次性状态机，但此前没有进程级所有者统一 SIGINT/SIGTERM、停止新任务、取消后台任务和资源关闭顺序。若各资源自行注册信号或深层模块从全局查找依赖，关闭可能重复、乱序或清理另一组 context；若为满足“停止接入”提前引入 listener/drain stub，又会越过 P04 transport 边界。
- 决策：新增 `RSD-1` 进程私有关闭契约。RuntimeShutdownCoordinator 必须显式接收一个 RuntimeContext，RuntimeService 注入 coordinator 时必须验证双方 context 对象身份相同；coordinator 不创建、查找或替换任何依赖。首次有效关闭原因胜出，并立即把本地 admission gate 置为 closed；后续原因不得覆盖。SIGINT、SIGTERM、service stop、外部调用和当前无 listener 自检均复用同一 request/shutdown 路径，不建立第二套 signal 或 cleanup owner。
- 决策：固定关闭相位为 stop admission、TaskSupervisor shutdown、flush sinks、close sinks、close clients、write summary、close logger。sinks 只包括 context 中已冻结的 metrics、traces 与可选 diagnostic，client 只包括显式 NsHttpClientOwner；logger 只关闭 composition root 明确传入的 owned logger。coordinator 使用实例级异步锁，成功形成报告后重复关闭必须返回同一冻结报告且不重复资源操作。RuntimeService 只在自身 stop hook 成功后执行 coordinator；既有 stopped 幂等、failed 后可显式清理/重试和 event-loop owner 规则保持。
- 决策：普通资源异常按 phase、固定 resource 名和异常类型记录，继续尝试后续资源；不得把异常文本、对象 repr、路径、URL、credential、payload 或底层 cause 写入报告或摘要。进程级异常不吞并，继续按 RSL-1 进入 failed 并允许调用方重试。TaskSupervisor 超时作为可观测结果而非无限等待；本地报告可以保留既有 supervisor 任务名合同，但日志只允许数量和有界 digest，不得输出原始未完成任务名。摘要必须在 logger close 前写入，logger close 自身保持幂等。
- 决策：signal registration 只属于 composition root 当前 event loop；优先使用 add_signal_handler，不支持时才使用 signal.signal 并通过 call_soon_threadsafe 回到 owner loop。P02-FIX-04 校准后，两条安装路径都必须在修改前保存 SIGINT/SIGTERM 的原 handler 对象；close 在 asyncio 路径先 remove loop handler，再通过 signal.signal 精确恢复保存对象，fallback 路径同样恢复，重复 close 不重复操作。当前 main 没有 listener，因此完成 preflight 和 service start 后以 SELF_CHECK_COMPLETE 请求同一关闭路径并退出；这只证明无监听进程自检和资源编排，不表示常驻 transport 生命周期已经实现。
- 决策：P02 的 stop admission 仅为进程本地 gate，TaskSupervisor 进入 closing 后负责拒绝新任务。coordinator 明确不依赖 transport、Envelope、connection/session、DeliveryRecord、StateStore、role transition 或 management processor。P04 创建首个 listener 时必须先冻结类型化 admission/drain hook，再把 transport 停止新连接、已有连接 draining 与最终 close 插入既有相位边界；不得通过任意 callback bag、HTTP 管理端口或私有信号旁路扩展。delivery 转移、owner handoff 和跨节点 draining 继续分别服从 P10/P18 等后续合同。
- 后果：当前进程对 SIGINT/SIGTERM 和显式停止具有一致、幂等、可观测且不泄密的资源释放路径；普通单资源失败不会跳过其他已注入资源。P02-W07 可以在同一显式 context 上增加 event-loop implementation/lag 观测，但不得让 collector 自行拥有信号或重复关闭 sinks。P04 及后续阶段扩展关闭序列时必须保持 RSD-1 的单 owner、同 context、固定相位、安全摘要和失败隔离规则。
- 关联阶段/工作包：`P01-W05`、`P01-W13`、`P01-W15`、`P02-W02`、`P02-W03`、`P02-W06`、`P02-FIX-04`、`P02-W07`、`P02-FIX-05`、`P04`、`P10`、`P18`。

## ADR-026

- ADR 编号：`ADR-026`
- 状态：`ACCEPTED`
- 背景：OBS-1 已冻结 event-loop 的 8 个标准指标名称、有限 attribute schema 和 best-effort sink，RSP-1 已在启动前选择 asyncio/uvloop，RSD-1 也已统一任务与 sink 关闭顺序；但此前 runtime 没有实际采样器或内部 snapshot。若 monitor 根据 loop 类名重新猜实现、自己创建 exporter/thread/sink，或不受 TaskSupervisor 管理，会破坏显式接线和关闭顺序；若探针失败仍报告 0，则会把未知状态伪装为健康。
- 决策：新增 `RLO-1` runtime 私有观测契约。RuntimeEventLoopMonitor 必须显式接收 RuntimeContext 和 RSP-1 的 `NsEventLoopImplementation` 选择结果，RuntimeService 必须验证双方 context 身份相同；不得读取全局配置、重新选择或替换 event-loop policy。monitor 在 service start hook 成功后启动唯一 supervised task，RSD-1 先关闭 TaskSupervisor 再 flush/close sinks，因此 monitor 不拥有独立 stop、signal、thread、executor、exporter 或网络端点。
- 决策：默认采样周期为 1 秒，使用当前 loop 的 monotonic time 计算 scheduling lag；每次 wake 只形成一个样本，下一 deadline 从实际观测时间开始，长阻塞后不得逐个追赶旧 deadline。内存 lag 历史最多 1024 项，P95/P99 使用 nearest-rank，snapshot 为冻结值并同时包含最新 lag、样本数、slow observation、pending/cancelled task、executor queue、probe failure 与 metric rejection。实现常量不属于当前热更新合同，未来若配置化必须进入既有 event_loop/observability 组并按 apply mode 验收。
- 决策：slow callback total 的可移植运行定义固定为 scheduling lag 大于等于 `runtime.event_loop.slow_callback_threshold_ms` 的 observation 累计数；monitor 同时把配置的 debug 和 slow-callback duration 应用到实际 loop，但不得解析 asyncio/uvloop 私有日志文本、安装额外日志 handler 或复制 callback repr。pending task 使用当前 loop 的公开 `all_tasks()` 并排除采样 task 本身；cancelled task 使用同一 TaskSupervisor 已观察的终态计数。executor 未创建时队列深度为 0；已有 executor 的本地队列无法安全探测时为未知。
- 决策：必须复用 OBS-1 的 8 个权威标准 definition，不新增同义指标或高基数 attributes。implementation 以 value=1 gauge 加有限 implementation 标签；lag sample 为 histogram，P95/P99、pending 与 executor 为 gauge，slow/cancelled 为累计 counter。metrics disabled 时 monitor 仍维护内部 snapshot；普通 clock、record、sink 和 probe 异常不得终止 service或复制异常文本。clock/record/sink 失败累计 metric rejection；probe 失败累计 probe failure，对应值使用 `None` 并省略该次 metric，不得输出虚假 0。进程级异常仍按既有公共边界穿透。
- 决策：event-loop 指标是异步可观测数据，不进入 DeliveryRecord、AckRecord、StateStore 或控制审计事务，也不构成 health、角色、transport 或发布性能权威。W08 本地诊断可以只读已经存在的 snapshot 与 startup 结果，但不得启动第二个 monitor、修改 loop 或开放 HTTP 管理端口。P20/P22 的 exporter、故障注入和基准验收必须消费同一 OBS-1/RLO-1 语义，不得改变 ACK/delivery 主链路。
- 决策（P02-FIX-05 校准）：monitor supervised task 的正常 shutdown 取消是预期终态，不触发 service failure；monitor coroutine 的非取消异常是 critical terminal failure，RuntimeService 必须请求同一 RSD-1 shutdown 并先进入 `FAILED`。后续显式 stop 成功后进入 `STOPPED`，coordinator report 继续保留 `CRITICAL_TASK_FAILURE` 和 monitor failed task；重复 stop 按 RSL-1 幂等且不重复资源清理。不得为此创建第二个 TaskSupervisor、shutdown owner、signal owner 或独立清理 task。`_safe_count()`、metric record、clock 与 sink 的普通异常继续只更新既有 failure/rejection counter、使用未知值并保持 service 运行，不得升级为 critical failure。
- 后果：标准 asyncio 与 uvloop 现在具有同一冻结 snapshot 和指标表面，且在 shutdown 时不会向已关闭 sink 写入；长暂停不会造成采样追赶风暴，观测失败也不会伪装正常。未来更精确的 loop-native callback/executor 数据只有在两个实现均完成兼容与失败语义验收后才能替换受限探针，指标名和低基数边界保持。
- 关联阶段/工作包：`P01-W04`、`P01-W05`、`P01-W15`、`P02-W04`、`P02-W06`、`P02-W07`、`P02-FIX-05`、`P02-W08`、`P20`、`P22`。

## ADR-027

- ADR 编号：`ADR-027`
- 状态：`ACCEPTED`
- 背景：P02 阶段出口需要在不启动服务或监听器时判断本地配置与启动依赖是否可用。若为此增加独立入口、HTTP 管理端口、运行中 monitor 或目录准备，会破坏 RTE-1 唯一入口、RSP-1 启动顺序以及 P16/P20 的管理和诊断边界；若直接序列化底层错误，又可能泄露配置路径、异常文本或凭证内容。
- 决策：新增 `RDI-1` runtime 私有本地诊断契约。`python -m ns_runtime.main diagnose` 是 RTE-1 唯一 main 模块入口的子命令，不新增 cli/app 入口模块。诊断必须复用 RSP-1 对环境、显式配置、安全、transport admission、本地 Python 依赖、TLS capability 和 event-loop selection 的权威校验，但只能调用只读 inspection；不得调用目录 prepare、policy install、`asyncio.run()`、RuntimeService、RuntimeEventLoopMonitor、信号注册、文件 logger、HTTP client、sink exporter 或远端探针。
- 决策：目录检查只返回固定 role 和 `accessible`、`access_denied`、`missing`、`not_directory` 四态，不创建、修复或输出实际路径。成功报告是冻结本地事实，包含 config/dependency 通过标记、有限 transport/TLS/state-store 名称和 event-loop 选择；ready 只表示当前启动前本地要求通过，不是运行中 health、角色、IAM、listener、StateStore 或集群权威。目录未就绪返回可机读 not_ready 与非零退出码；配置、依赖或安全失败返回稳定公共 error code/numeric code，仅允许固定标量 detail key，禁止输出 message、完整 details、路径、对象 repr 或 cause；未知普通异常收敛为不带细节的 `NS_ERROR`，进程级异常保持穿透。
- 决策：诊断不得读取或启动 RLO-1 monitor，也不得建立 socket、HTTP 管理端口、Envelope、transport/session、DeliveryRecord 或强一致记录。P16 的管理状态查询仍必须经已启用 runtime transport 的管理 Envelope，P20 的 diagnostic snapshot/exporter 仍使用 OBS-1 并保持显式生命周期；两者不得把本地 diagnose 扩展为旁路控制面。
- 后果：运维和本地开发可以在零启动副作用下区分 ready、目录未就绪和配置/依赖失败，同时 backend 依赖层缺少 runtime 可选包时稳定 fail-closed。后续启动要求变化必须同时扩展 RSP-1 inspection 与 RDI-1 测试，不能在诊断模块建立第二套校验或资源所有权。
- 关联阶段/工作包：`P02-W01`、`P02-W04`、`P02-W07`、`P02-W08`、`P16`、`P20`、`P22`。

## ADR-028

- ADR 编号：`ADR-028`
- 状态：`ACCEPTED`
- 背景：P03 必须一次建立唯一 `json.v1` Envelope 边界；如果各 transport、processor 或插件使用裸 dict、自定义顶层字段、空分组占位或可变嵌套对象，会在 IAM、路由和可靠投递前形成多套协议与检查时差。
- 决策：新增 `ENV-1`。`ns_runtime.protocol` 是 transport-independent 的唯一 Envelope 协议包；固定顶层顺序为 `protocol/message/source/target/route/delivery/stream/auth_context/payload/callback/trace/extensions`，其中 protocol/message 必需，不适用分组必须省略。每个核心分组由冻结类型表达，只接受显式字段集合；顶层与分组未知字段、null/空对象占位、非 JSON 动态值和不满足基本结构的值稳定拒绝。payload 与 extension 动态内容在进入模型时形成递归不可变快照；协议异常 detail 只含固定 group/field/reason 语义，未知输入 key 使用固定占位，不复制输入值或对象 repr。
- 决策：P03-W01 只冻结类型和分组结构，不解析 wire bytes、不建立 transport/session/IAM/route/delivery 状态、不执行 message 行为。source/auth_context 的出站类型存在不代表允许客户端入站携带；该权威注入边界由 P03-W02 在独立 raw/normalized 模型中完成。目标类型条件、message 专属必填、资源限制、版本矩阵、注册表、extension 策略、错误 Envelope、canonical serialization 与 feature-disabled processor 依次由 P03 后续工作包补齐，不得由当前宽松默认推断功能已启用。
- 决策（P03-W02）：`InboundEnvelope` 只保存 sender-controlled group，类型表面根本不包含 source/auth_context；mapping 入口必须在普通 schema 校验前分别以 `RUNTIME_SOURCE_FORGED`、`RUNTIME_AUTH_CONTEXT_FORGED` 拒绝这两个字段。`RuntimeAuthority` 只接收已经由后续 IAM/session 层建立的类型化 SourceGroup/AuthContextGroup，`normalize_inbound()` 只做显式注入，不查询全局、不认证 token，也不把 target capability 请求或 payload 声明复制为权威 capability/tenant。该注入 API 是 runtime 内部信任边界，不宣称 P05/P06 已实现。
- 决策（P03-W03）：唯一 wire codec 常量为 `json.v1`，`JsonV1Codec` 只接受 UTF-8 str/bytes 完整文档。默认限制固定为 1 MiB UTF-8 文档、32 层、65536 字符、单数组/对象 4096 项、总节点 100000、signed 64-bit absolute integer 上限和有限 float `1e308` 上限；构造时可显式收紧或按权威 protocol 配置提供文档大小，但不得从深层模块读取全局配置。解码前扫描 nesting，解析中拒绝重复 key、NaN/Infinity 和超范围数，解析后迭代验证全部字符串/key、容器和节点。错误只输出固定 codec/reason，不复制 JSON、parser exception 或输入 key/value。
- 决策（P03-W04）：schema 校验固定为不可绕过的 base validator 后叠加一个 exact `MessageTypeSchema`。base 负责 target kind 必填寻址字段、route segment 重复与 delivery attempt 正数等跨类型不变量；message schema 只能声明额外 required/forbidden group 和 inline payload 的精确 required/optional 字段集合，不能关闭或覆盖 base 规则。schema/type 不匹配、缺失、额外字段均用固定 group/field/reason 拒绝，不回显 message.type、payload key/value。schema 对象只含声明，不持有或执行 processor callback。
- 决策（P03-W05）：`ProtocolVersion` 与不可变 `ProtocolCompatibilityMatrix` 集中执行版本范围和 schema key 选择。major 必须有显式同 major 支持项且 minimum/requested major 一致；在 `[minimum, requested]` 内选择最高显式支持版本，因此 minor/patch 只能向已登记 schema 降级，不能凭数值自动兼容未知 schema。当前冻结矩阵仅登记 `1.0.0 -> json.v1/protocol-1.0`，接受 `1.0.x` 降级但不宣称 1.1。协商结果同时返回 requested/minimum/selected/schema_key/downgraded，processor 不接收版本分支责任。版本错误只含固定 reason，字符串组件限制 9 位以避免超长整数转换。
- 决策（P03-W06）：内置注册表采用显式冻结 tuple，不使用 decorator、模块扫描、entry point 或 import side effect。当前 protocol 1.0 独立冻结 50 个类型，完整覆盖 connection、task、delivery、stream、runtime.control、cluster.event、config、dead_letter、replay、cancel、hold、status、runtime.error 十三个必需族；每个类型至少绑定 current protocol schema。精确 type/schema 查询失败复用 `RUNTIME_UNSUPPORTED_MESSAGE_TYPE` 且只返回固定 reason，不回显输入。类型存在只代表协议契约存在，不代表 feature enabled 或 processor 成功。
- 决策（P03-W07）：每个 `MessageTypeContract` 必须同时冻结 protocol schema mapping、category、default reliability、required capabilities tuple、processor key、audit level、feature flag、enabled 状态和 response type tuple。category 和 reliability 使用闭集 enum；registry validation 在 W04 schema 前校验注册 category 及允许的 reliability 值。所有 response type 必须回指同一内置 registry。当前只有 `runtime.error` 的 `protocol.error_envelope` 标记 enabled，表示 P03 可构造标准协议错误；其余 49 个业务、连接、delivery、stream、管理与集群类型均 feature disabled。权限只是后续 P06/P07 的声明输入，不执行或替代 IAM。
- 决策（P03-W08）：`extensions` wire group 直接以 dotted lowercase namespace 为 key，不增加私有 `namespaces` wire wrapper。动态 key 只允许存在于该 group；核心顶层与分组仍由 W01/W04 固定。`ExtensionNamespaceRegistry` 只接受显式 contract tuple，每项冻结 exact object schema、required capability 和 enabled flag；不扫描插件或执行 validator callback。未注册 namespace 默认拒绝，显式 `IGNORE_AND_AUDIT` 只返回 ignored count/audit_required 且绝不把内容交给 accepted mapping；disabled、unauthorized、required field missing 和 unknown field 分别稳定失败。所有失败和 ignore 结果不复制 namespace、字段值或 payload，实际审计消费留给 P07。
- 决策（P03-W09）：标准错误固定为已注册 `runtime.error` Envelope，builder 必须显式注入 SEC-1 `Sanitizer` 和类型化 protocol/source/context，不读取全局。对精确 ERR-1 类型只读取 registry definition 与 error class 的冻结 default_message，绝不读取实例 message/details/cause、调用 str/repr 或序列化异常；未登记普通异常保守映射为已登记 `NS_RUNTIME_ERROR`，KeyboardInterrupt/SystemExit 穿透。payload 固定包含 code/numeric/message/severity/category/retryable/disconnect/audit/action 和经 sanitizer 处理、仅由 registry action 形成的 detail，可选引用 ID 也逐字段 sanitizer；错误 Envelope 自身必须通过 current registry schema。source/target/trace 由调用方类型化提供，不生成 session/IAM 状态。
- 决策（P03-W10）：canonical format 名为 `json.v1.canonical`：从冻结 normalized Envelope 的公开 mapping 生成，递归按 Unicode key 排序、UTF-8 原字符、紧凑 `,`/`:` 分隔、禁止 NaN/Infinity，并先复用 W03 全部结构/数字限制、编码后再次执行 byte limit。输出是唯一 bytes；checksum 固定为 `sha256:<lowercase hex>`。相同 normalized 值不受原 mapping 插入顺序影响，decode/rebuild 后 canonical bytes 必须相同。canonical bytes 可以用于 wire/checksum，但日志、审计和状态记录默认只保存 digest/metadata，不得借此绕过 SEC-1 记录完整 Envelope/payload。
- 决策（P03-W11）：`build_feature_disabled_processors()` 必须为每个 `feature_enabled=false` 注册项创建同一 `FeatureDisabledProcessor`，processor key 唯一且 immutable；当前精确覆盖 49 项，不包含 enabled 的 outbound `runtime.error` 合同。processor 只验证自身 contract type、以注册常量写 best-effort 安全审计、构造 `RUNTIME_FEATURE_DISABLED` 并返回 W09 标准错误 Envelope；请求 payload/source/auth/capability 不进入日志或错误 detail，也不调用任何按类型 callback。日志普通失败仍返回错误，进程级异常不吞并；task、delivery.ack、stream、management、cluster 等均不得产生 ACK、状态变化、空结果或 success。实际强审计、pipeline 和 enabled processor 注册属于 P07/P08 以后阶段。
- 决策（P03-FIX-01 校准）：W01 必填 major/minor/patch、route hop/max_hops、delivery attempt 必须使用 required integer 检查，不能复用 optional 检查接受 None；capabilities 和 route_segment 必须先证明为 list/tuple，字符串不得按字符迭代伪装数组。未知直接 mapping key 统一固定拒绝，不排序或回显攻击者 key。W03 depth 明确定义为 JSON object/array nesting 层数，容器中的标量不额外占一层；lexical pre-scan 与解析后迭代验证必须使用同一口径。
- 决策（P03-FIX-02 校准）：StreamGroup 的 missing_sequences、received_sequences 与 ack_ranges 顶层只接受 list/tuple；前两者的每个元素以及 ack_ranges 每个二元 list/tuple 的 start/end 都使用 required non-negative integer 语义，明确拒绝 None、bool、float、str，并在 start <= end 比较前完成类型验证。合法输入继续冻结为 tuple，wire 数组形状不变。extension wire namespace 必须先按 `[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+` 校验语法，再执行 registry lookup；语法非法固定以 group=extensions、field=$namespace、reason=invalid_namespace fail-closed，且不回显 namespace。`IGNORE_AND_AUDIT` 只处理语法合法但未注册的 namespace。
- 决策（P05-FIX-01 后续激活）：P03 阶段冻结 49 项非 error message feature disabled 是当时的真实阶段事实，不回写。P05 完成领域实现后由同一 `BUILTIN_MESSAGE_REGISTRY` 正式激活 `connection.hello/accepted/rejected/reauth/reauth_accepted/reauth_rejected/heartbeat/heartbeat_ack/drain` 九项合同，并冻结 inbound/outbound direction；outbound-only response 拒绝 inbound，但不再把整个 feature 标为未实现。其余 40 项 P06+、task、delivery、stream、control、cluster 等合同继续由同一 disabled processor matrix fail-closed，不建立第二套 feature registry。上述 connection lifecycle 不声明通用 `runtime.connection` capability，已认证 session 的 heartbeat、self drain 与 reauth 权限由 P05 current session/epoch/lifecycle 边界决定。
- 决策（P05-FIX-01 exact schema）：P05 connection message 继续使用 ENV-1 的 base schema 后叠加 exact type schema。hello 精确允许 token/component_type/requested_version、可选 min_version/requested_capabilities 与 canonical `ns.connection_resume` extension；heartbeat/ack 精确冻结 connection_id/session_id/connection_epoch/sequence 与 sent_at/server_time；drain 为无 target/payload/route/delivery/stream/callback/extensions 的 self-scoped Envelope；accepted/rejected/reauth responses 采用各自固定 payload 白名单。非法 group、缺失或额外字段必须在 `registry.validate_envelope()` 阶段失败，connection service 不拥有第二套 wire schema authority。
- 后果：后续 adapter 只能向统一 codec 提交完整应用消息边界，processor 只能接收完成 P03 normalization 的 Envelope；现阶段没有 listener、ACK 快速通道、裸 JSON 管理命令、业务 processor 或伪成功。修改分组字段或允许规则必须重跑 P03 及所有下游协议回归。
- 阶段冻结：P03-W01 至 W11、P03-FIX-01 与 P03-FIX-02 已在 WSL/runtime/backend 联合回归后达到 `VERIFIED/F2`。`ENV-1` 只冻结协议入口、类型/registry/错误/serialization 与 disabled 行为；本 ADR 冻结时 P04-W01 为 `NOT_STARTED`，其后 transport 状态由 P04 与 ADR-029 权威记录，仍不得仅由本 ADR 推断 transport、session、IAM、StateStore、delivery 或 cluster 已开始。
- 关联阶段/工作包：`P03-W01` 至 `P03-W11`、`P04`、`P05`、`P07`、`P10`、`P12`、`P16`、`P21`。

## ADR-029

- ADR 编号：`ADR-029`
- 状态：`ACCEPTED`
- 背景：P04 必须建立当前正式 WebSocket/TCP transport，同时保持 Envelope、logical connection、IAM、delivery 和 cluster 与底层库解耦。若把 WebSocket 对象交给上层、让 write completion 生成 runtime ACK、使用无界队列，或为 listener 新建 shutdown/signal/supervisor owner，会破坏 ENV-1、RSL-1、RTC-1、RSD-1 与后续阶段边界。
- 决策：冻结 `TC-1`。`TransportAdapter`/`TransportSession` 只暴露完整 UTF-8 text message、send、native ping/pong、close、capabilities、transport-local identity 与安全诊断；session 在 P05 前只有 handshaking/closing/closed。WebSocket binary 固定拒绝，invalid UTF-8 与 oversize 由标准 close/error 收敛。`websocket_tcp` 只声明 reliable ordered messages、transport flow control、native keepalive；不声明 stream/datagram/multiplexing/path migration/per-stream flow control/0-RTT/resume。未来三个 adapter 只保留 unavailable registration，不加载依赖或创建 listener。
- 决策：每个 session 独立拥有显式有界 read/write application queue，reader/writer task 由既有 TaskSupervisor 创建。read full 关闭 session，write full 立即返回 flow-control error；send/ping/close/drain 均有 deadline，queued send 取消不写底层，并发 send 保序，close 幂等。transport send success 只完成局部 send future，绝不创建 AckRecord/DeliveryRecord、取消业务 retry 或调用 processor。
- 决策：transport_connection/session/stream/path ID 与 P05 logical identity 严格分离。高基数 ID 只保存在 repr=false 的本地类型化对象；peer/local address 在 adapter 边界立即转为有界 SHA-256 摘要。第三方异常统一映射到现有 `RUNTIME_TRANSPORT_*` 与固定低基数 reason，不复制 message/repr/cause；普通资源和 metrics sink 失败 fail-soft，BaseException 原对象穿透。
- 决策（P04-FIX-01 校准）：第三方 exception class resolution 必须保持 lazy；当 websocket driver 按 DEP-1 未安装或不可导入时，只使用互不匹配的内部 sentinel type 继续处理普通未知异常，不得因 error normalization 自身强制加载依赖、抛 ModuleNotFoundError，或把普通异常误分类为 WebSocket close/handshake/oversize。启用 adapter 的 RSP-1 依赖门禁与真实类型映射保持不变。
- 决策（P04-FIX-02 校准）：normalized receive failure 必须保持 exact terminal close classification，只有真实 peer close 可形成 `REMOTE_CLOSED/REMOTE`；protocol、message-too-large 与 generic read failure 分别形成 `PROTOCOL_ERROR`、`MESSAGE_TOO_LARGE`、`RECEIVE_FAILED` 的 adapter-initiated terminal outcome，public reason、close_info、clean 与 close metric 必须一致。keepalive timeout/普通 failure 是 `KEEPALIVE_FAILED` terminal close，CancelledError 原样穿透且不记失败。每个 send 只能有一个覆盖排队和底层 write 的权威 deadline；queued timeout 永不写底层，active timeout 必须终止 writer 并在返回前关闭 session。close cancellation 不得提前发布 CLOSED、close_info、closed event、close metric 或 connection decrement，原始 pending outcome 与资源所有权保留给后续/并发 close waiter 重试并最终只发布一次。RSL-1 核心语义不变；composition root 在 transport 已启动但后续 start step 失败或取消后负责对 FAILED service 显式 stop，普通 cleanup failure 不覆盖原 start exception，进程级 BaseException 保持优先语义。
- 决策：复用 OBS-1 十个标准 transport metric name。常规 attributes 只允许有限 transport_type，以及按具体指标允许的 component_type/tenant_scope classification、close_reason、error_code；禁止 connection/session/transport/path/message/tenant ID、peer、URL、payload 或异常文本。指标不进入 ACK、DeliveryRecord 或强一致事务。
- 决策：P04 只以一个类型化 `TransportLifecycleOwner` 兼容扩展既有 RSD-1。首次 shutdown request 同步关闭本地与 listener admission gate，随后固定执行 stop admission、drain sessions/I/O、close adapters/listeners，再继续既有 supervisor/sink/client/logger 相位；不创建第二 coordinator、signal owner、TaskSupervisor 或 event loop。`TransportRuntimeService` 仅在 RSP-1 成功后启动 manager。完整生产证书材料仍属 P20；启用 TLS 但 composition root 未显式收到 server SSLContext 时必须 fail-closed。
- 后果：P04 可以真实建立 TLS 或受控非生产明文 loopback WebSocket，把完整 text message 交给上层；上层仍不得接受业务消息，P05 handshake 完成前 session 不进入 active。后续 adapter 必须复用 22-case TC-1 和公共 harness；修改任何冻结接口、capability、queue/error/metric/lifecycle 语义必须重跑 P04 及全部下游阶段。
- 阶段冻结：`P04-W01` 至 `P04-W10`、`P04-FIX-01` 与 `P04-FIX-02` 已在真实 TLS/明文 loopback、terminal outcome/竞态/取消专项、P03+P04 联合矩阵及 runtime/backend 全量回归后达到 `VERIFIED/F2`。冻结范围仅为 transport adapter、底层 session/message boundary、queue/error/registry/metrics/lifecycle 合同；`P05-W01` 保持 `NOT_STARTED`，不得由本 ADR 推断 logical connection、handshake、IAM、processor、StateStore、delivery 或 cluster 已开始。
- 关联阶段/工作包：`P04-W01` 至 `P04-W10`、`P05`、`P11`、`P20`、`P21`、`P22`。

## ADR-030

- ADR 编号：`ADR-030`
- 状态：`ACCEPTED`（P05 阶段已冻结）
- 背景：P05 必须在不改变 P04 transport session 三态、也不提前创建 IAM backend、processor pipeline、StateStore 或 delivery 状态的前提下建立 runtime logical connection。并发 hello、close、drain、disconnect 和后续 resume 若通过散落赋值更新状态，会产生双 active、draining 回退或提前发布 closed。
- 决策（P05-W01）：logical connection 独立使用 `accepted -> handshaking -> authenticated -> active -> draining -> closing -> closed` 七态显式矩阵，绝不复用 `TransportSessionState`。每次迁移由单实例 `asyncio.Lock` 串行化；非法、重复或越级迁移使用固定 current/requested/allowed 分类稳定拒绝且不修改 state、reason 或 sequence。`draining` 只能进入 `closing`，`closed` 为终态。进入 `closing` 必须选择 `LogicalConnectionCloseReason` 闭集之一，reason 只允许固定低基数字段且在 `closed` 保留；任意非 closing 迁移禁止注入 reason。
- 决策（P05-W01）：状态 snapshot 为 frozen、slots、kw_only 的值对象，只含 state、可选 close classification 和本地 transition sequence；不含 logical/transport ID、地址、token、Envelope、异常、callback 或资源 owner。状态机不持有 transport、TaskSupervisor、Clock、signal、sink、client 或全局 context，不创建 task、thread、loop、queue、processor、DeliveryRecord 或 StateStore mutation。
- 决策（P05-W02）：每个新 logical connection 只能由一个 `ConnectionHelloReceiver` claim。receiver 先把 W01 状态原子迁移到 handshaking，再通过既有 `TaskSupervisor` 同时拥有唯一 transport receive task 与显式 `Clock.sleep()` 总 deadline task；调用方为同一 supervisor 提供非敏感本地递增 task sequence，receiver 不从 transport/logical ID 派生 task 名。deadline task 完成或观测到 monotonic deadline 已到时，timeout 优先于同 tick 的 hello arrival。胜出后必须取消并 join 另一 task，不留 pending receive、timer 或 ControlledClock waiter。
- 决策（P05-W02）：第一条完整应用消息只经 P03 `JsonV1Codec -> InboundEnvelope -> BUILTIN_MESSAGE_REGISTRY exact schema` 边界验证；不构造裸 JSON 旁路、不 normalization 权威、不调用 feature-disabled 或临时 processor。非 hello、malformed hello、duplicate receiver、timeout 和普通 transport failure 分别使用固定 reason 与 W01 close classification 收敛，最多读取一次；native ping/pong 不参与。receiver 不复制 payload，只以同一冻结 group 引用构造临时 schema shape，成功后把唯一 `InboundEnvelope` 直接交给 W03。取消会清除 supervised tasks、关闭 transport 并保持原 `CancelledError`；普通 close failure不覆盖原协议/transport错误，并允许同一幂等 transport owner立即或后续重试，closed 不提前发布。
- 决策（P05-W03）：hello payload 只在 `HelloClaimParser` 的受控调用栈读取；token 立即装入 repr 固定脱敏的单次 `HandshakeCredential`，IAM adapter 必须通过 `take()` 转移一次且 coordinator finally 无条件 clear。`ParsedHello`、`HandshakeIamRequest` 均 frozen/slots/kw_only、repr 不显示字段；返回的 `PendingHelloClaims` 只含非权威 component_type、requested/minimum protocol、repr=false requested capabilities 和可选 resume 引用，不含 token 或完整 Envelope。普通失败先从受监督 operation task 内清除 traceback/context/cause，再由外层重新抛出安全类型，避免 TaskSupervisor failure traceback 间接保留 hello/token。
- 决策（P05-W03）：不修改 ENV-1 已冻结的 hello payload schema；resume 请求使用 P03 已冻结 extension 机制中的显式 enabled `ns.connection_resume` contract，精确要求 P01 connection_id、非负 connection_epoch 和可选 P01 session_id。未知/disabled/额外 extension 字段继续由 P03 registry fail-closed。requested_version 必须与 Envelope protocol group 相同，payload/group min_version 同时出现时必须一致；capability 只冻结为请求集合，绝不成为权威值。
- 决策（P05-W03）：P05 IAM 只定义显式注入的 `HandshakeIamAdapter`、单次 request 与 frozen `HandshakeIamAuthority`。authority 包含 identity、tenant、component_type、capability、冻结 permission mapping/ref/digest/version、UTC TTL、resume eligibility 和 iam_mode；coordinator 只接受 exact typed result并再次 detached copy，不保留 adapter 原对象或原始 response。component_type 漂移和过期 authority 拒绝。任意普通 adapter 异常不读取 str/repr/cause，统一收敛为安全 IAM unavailable；CancelledError 原语义保持。
- 决策（P05-W03，P05-FIX-01 校准）：`DeterministicTestIamAdapter` 必须显式构造、离线、按调用顺序消费无 token 的 frozen outcome，覆盖 allow/deny/timeout/cancel/expired/inconsistent；不访问网络、不从 token 字符串推断 identity/tenant/capability，也不保存 token。`FailClosedHandshakeIamAdapter` 是 P06 前 ordinary production connection 的明确拒绝边界；composition root 已启用 logical admission，但必须默认显式注入该 fail-closed adapter，测试必须显式替换为 deterministic adapter，因此不存在 allow-all 或 token 推断的生产默认路径。`ConnectionHandshakeAuthenticator` 的受监督 authentication task 与 total-deadline task 从 coordinator 构造时的 monotonic deadline 竞速，deadline 先关闭为 timeout 再取消 operation，从而覆盖 receive、parse、IAM 和后续可继续扩展的协商阶段。
- 决策（P05-W04）：协议只能由 P03 `ProtocolCompatibilityMatrix` 选择，capability 必须同时存在于客户端 requested set、IAM authority set、P05 显式 capability policy，且 policy 对所选 schema 和 P04 adapter 权威 `TransportCapabilities` 的要求全部满足；任一越权、未登记、协议不兼容或 transport 不支持均在 authenticated 后、active 前以固定安全错误关闭。当前 `json.v1/protocol-1.0` lifecycle capability 只要求 reliable ordered messages，不根据 transport type 或版本数值猜测兼容。
- 决策（P05-W04）：`SessionContext` 采用 frozen/slots/kw_only 深度不可变值对象，包含 logical connection/session/epoch、最小 IAM identity/tenant/component_type 摘要、协商 version/schema/codec/capability、permission ref/digest/version、IAM mode/TTL/resume eligibility 和 authenticated 建立状态。它不包含 transport/path ID、transport/WebSocket 对象、task/sink/client/callback、token、完整 hello/Envelope、完整 permission mapping 或原始 IAM response；敏感及高基数字段均 repr=false。`NegotiatedSession` 同时保留 P03 协商结果，使后续 lifecycle codec/schema 只能复用该结果。
- 决策（P05-W05）：logical/transport/network path 三层只通过冻结值绑定：`LogicalConnectionTransportMap` 保存 SC-1 context 与从 P04 `TransportSession` 当次复制出的 transport type/capability/identity/path snapshot，绝不保存 session 或第三方 driver 对象。P01 `IdentifierFactory` 的显式 wrapper 独立生成 logical connection/session ID；transport/path ID 继续只由 P04 负责且不得相互替代。
- 决策（P05-W05）：同 transport 的 path update 必须保持 transport connection/session/stream identity 与 capability 不变，并由 adapter 声明 `connection_path_migration`；path epoch 和 migration count 严格递增，但 logical connection epoch/session 不变。transport replacement 是锁内显式操作，必须保持 connection_id、提供新 session_id 和恰好下一 connection_epoch，并拒绝复用当前 transport connection/session ID；detach 以当前 transport session ID fencing。并发 replacement 只有一个下一 epoch 可成功。
- 决策（P05-W06）：`LocalConnectionIndex` 是单进程单 owner，实例锁内管理 connection_id、session_id、identity、tenant、component_type、capability 与 active target eligibility。每次 add/remove/context replace 都先从完整 candidate entry set 重建冻结二级索引，全部验证通过后一次替换 owner references；duplicate connection/session ID 稳定拒绝，identity 明确允许多连接。公开 lookup/query/snapshot 只返回 frozen entry、mapping proxy、frozenset 和 tuple。
- 决策（P05-W06）：索引 owner 同时串行调用 W01 state machine 并更新 eligibility；只有 ACTIVE 可成为 target，进入 draining/closing 立即摘除，closed 原子清除全部索引。grace 所需 suspend/restore 与 state 分开，但 restore 仍强制 ACTIVE；session replacement 强制同 connection 与下一 epoch，先摘除 active，再原子替换 session/authority secondary keys。该索引不使用 StateStore、Redis、cache/global registry，不宣称跨进程权威。
- 决策（P05-W07）：`connection.accepted` 只通过 P03 Envelope、built-in registry schema 与 canonical serialization 发送，并显式固定八项 payload 白名单：connection_id、session_id、protocol_version、heartbeat、session_expires_at、server_time、runtime_id、role；heartbeat 内只含 interval_seconds/timeout_seconds。Envelope 不带 source/target/route/delivery/stream/auth_context/callback/trace/extensions，也不返回 tenant、identity、capability、permission、transport/path/peer、配置或 IAM response。
- 决策（P05-W07）：连接必须先以 authenticated/non-target 状态加入本地索引，canonical accepted 的 transport send 完成后才由同一 index owner 转为 ACTIVE/target eligible；底层 send completion 不是 runtime ACK。build/send/activation 普通失败或 cancellation 先进入 fixed closing reason、摘除 target，再关闭 transport；真实 close 成功后才发布 closed 并清空索引，close 普通失败保留 closing ownership并允许显式 retry cleanup。
- 决策（P05-W08）：transport native heartbeat 与 Envelope heartbeat 严格分层。native loop 只按显式 Clock 周期调用 P04 `TransportSession.ping()`，成功只更新本地 native count，失败按 transport-disconnected terminal close，不更新 application state。Envelope heartbeat 只在 P05 lifecycle handler 内经 negotiated JsonV1Codec、P03 registry/schema/canonical Envelope，精确校验 connection_id/session_id/connection_epoch/sequence；ack 是 best-effort connection.heartbeat_ack，不含 delivery/auth groups，不进入未来通用 pipeline、DeliveryRecord/ACK/retry 或强审计。
- 决策（P05-W08）：两个循环均由既有 TaskSupervisor 所有；watchdog 使用 Clock 的 last-received deadline，deadline 同 tick 优先于新 heartbeat。duplicate 不回 ack、不刷新 liveness；out-of-order/stale session/epoch 稳定拒绝；active 与 draining 允许 health heartbeat，其他状态拒绝。timeout、native failure、ack send failure、cancel/shutdown 与 close 在 lifecycle lock 下形成单一 terminal classification，并同步取消另一受监督 loop；transport close 成功后才清理索引/发布 closed。
- 决策（P05-W09）：`connection.drain` 只接受 negotiated JsonV1Codec/P03 registry 验证的 self-scoped empty Envelope，不允许 target/payload/route/delivery/stream/callback/trace/extensions，因此普通连接不能借字段 drain 他人。begin 在 single owner lock 内执行 ACTIVE->DRAINING，并由 LocalConnectionIndex 同步摘除 active target；重复 begin idempotent、不重置 deadline，draining 永不回 active，且 begin 本身不关闭 transport。
- 决策（P05-W09）：drain deadline 使用显式 Clock 与既有 TaskSupervisor 单任务，timeout 收敛 DRAIN_TIMEOUT；显式完成、shutdown、kick、disconnect 等 terminal request 在同一 lock 下 first-reason-wins，再进入 closing/transport close/closed cleanup。close failure/cancel 保留 closing、不可恢复 active，并允许 retry cleanup。draining gate 只分类已登记的 connection health/reauth、runtime health/error 与未来 existing delivery ACK/NACK/Defer；它不处理这些消息、不创建 delivery record或提前实现 P10/P11/P12。
- 决策（P05-W10）：普通 active transport disconnect 使用独立 `ReconnectGracePhase`，不扩张 W01 七态。进入 grace 时先从 W06 active target 摘除，再以当前 transport_session_id fencing解除 W05 transport/path binding；logical context/index保留最小 resume state，旧 transport对象不由 grace service持有且不能继续发送。默认 deadline 精确 30 秒，使用显式 Clock 与既有 TaskSupervisor 单任务，重复 disconnect idempotent且不延长 deadline。
- 决策（P05-W10）：resume request 必须先以 P03 extension 解析出的 typed connection/session/epoch refs claim grace；引用 mismatch 不消费 grace，并发 claim 仅一个成功，deadline同 tick expiry优先。claim只取消 deadline并形成 repr-safe frozen claim，不恢复 transport/index target；W11 完成新 mapping、下一 epoch context、active eligibility 后才能标记 RESUMED。expiry 使用 TRANSPORT_DISCONNECTED 清空全部 logical indexes；shutdown/drain/kick/security terminal可提前结束，claimed后失败/取消必须由 W11 fail-close。
- 决策（P05-W11）：resume coordinator 必须先以 typed refs 单次 claim grace，再通过显式注入的 P05 IAM adapter 重新认证 token；旧/new resume eligibility、当前 session TTL、authority TTL、identity、tenant、component_type 与 client component claim 全部严格匹配。requested capability 重新通过 W04 IAM/protocol/P04 transport 三方求交；connection_id保持，P01生成新session_id，connection_epoch恰好加一。connection_id/resume refs从不单独充当凭证。
- 决策（P05-W11）：新 mapping与context先以non-target发布，P03 canonical connection.accepted发送成功后才恢复active target并完成grace；任何 IAM/negotiation/index/mapping/send/timeout/cancel失败均关闭candidate transport，claimed logical fail-close，且已发布的新binding先detach。并发resume最多一项claim成功，loser candidate也关闭。`ConnectionEpochGate`在未来任何普通、ACK、NACK、Defer处理前校验current connection/session/exact epoch和允许状态，旧epoch稳定拒绝且不调用processor。
- 决策（P05-W12）：non-resumable close使用五项闭集classification：kick、security violation、severe protocol violation、malicious duplicate confirmation、policy non-recoverable；每项冻结映射到一个W01 close reason与一个public error classification。guard首次调用胜出且标志单向，先以same logical identity替换index中的SessionContext使resume_eligible=false，再摘除target并关闭；close failure/cancel保持closing+revoked并可retry，重复调用不改变classification或重复audit。普通disconnect不调用guard且不误标。
- 决策（P05-W12）：安全audit只预留显式注入的async `ConnectionSecurityAuditSink`和frozen typed event；event只含固定classification/close/public error、logical ID的16-hex SHA-256摘要、component_type、epoch与Clock UTC，不接受payload/token/peer/free-text reason/exception。普通sink failure只标记audit失败且不阻止或放行安全close，也不覆盖原transport cancellation；test sink必须显式构造，不存在hidden global/durable audit声明。grace中的guard同步取消deadline并关闭logical，W11 resume还必须读取indexed resume eligibility。
- 决策（P05-W13）：`connection.reauth` 只接受当前 negotiated protocol/schema 下的 P03 inline Envelope；注册表精确冻结 token 必填、requested capabilities 可选及 accepted/rejected response 白名单，并禁止 target/route/delivery/stream/callback/extensions 与客户端 source/auth_context。token沿用single-use credential，typed parsed/request/result均不显示credential或authority，所有完成、失败、timeout与cancel路径无条件clear。
- 决策（P05-W13）：reauth仅允许当前exact SessionContext处于active或draining；使用显式P05 IAM adapter重验TTL、identity、tenant、component_type并重新执行W04 protocol/capability/transport negotiation。成功保持connection_id/session_id/epoch/created_at，更新不可变permission ref/digest/version/TTL/capabilities；accepted发送前后二次读取index，发送成功后以expected old context和allowed state做atomic compare-and-replace，权限收缩同步重建capability index，draining不会恢复target。任意deny、timeout、identity漂移、capability越权、send/publish/cancel失败都fail-close，rejected前先进入closing摘除active target，旧权限不能继续无限有效。
- 决策（P05-W13）：`SessionExpiryController`以显式Clock、既有TaskSupervisor和generation task提供reauth lead与absolute expiry；refresh必须保持logical session/epoch且使用未来TTL，取消旧generation后才安装新deadline。到期再次验证indexed exact context，设置expired并以AUTH_FAILED进入closing；真实transport close成功后清除index，普通close failure保持non-target closing并允许显式retry cleanup。策略当前唯一failure action为close，不创建后台credential refresh、P06 client、thread/loop/supervisor/global owner或强一致记录。
- 决策（P05-W14）：`SafeConnectionSnapshotReader`只从显式local index与可选heartbeat/grace/drain/expiry/security owner的async frozen snapshot读取，使用index mutation sequence做最多三次有界coherence retry并串行保护本地safe projection cache；source普通失败只令complete=false，不读取或输出异常。公开snapshot精确包含logical connection/session的16-hex SHA-256摘要、state/close/target、component/epoch/protocol、五项有限capability classification、既有lifecycle snapshot、UTC observation/index sequence/coherent/complete；不返回raw logical ID、identity/tenant、permission ref/digest/mapping、token/credential、Envelope/payload、transport/path/peer、WebSocket或内部owner。
- 决策（P05-W14）：新增显式注入的`ConnectionLifecycleAuditBoundary`、sink、frozen event与test sink。event仅含resume/kick/security-close/reauth-rejection/non-resumable五项kind、fixed outcome、`STRONG_REQUIRED`需求标记、logical digest、component/epoch、fixed close reason与Clock UTC；它只声明P07/P08未来必须提供的consistency，不含durability成功声明，也不创建global sink或storage。resume成功/拒绝/取消、reauth rejection及W12五类non-resumable close接入同一边界；普通sink failure只累计safe count且不回滚resume、不放行或阻止security close、不覆盖IAM denial。ordinary heartbeat根本不接收该边界且事件数保持零。
- 决策（P05-FIX-01 lightweight processor）：新增不可变 connection lifecycle processor contract/registry，只以 canonical `MessageTypeContract.processor_key` 为 dispatch key，精确覆盖 heartbeat、drain、reauth。processor 接收 P03 validated Envelope，先做 current session/epoch/state hard check，再调用既有领域 service并构造 canonical response；transport callback、Handler compatibility wrapper 与 lifecycle service 都不是 composition executable entry。该 registry 不包含 P07 permission/rate-limit/routing/audit generic pipeline，不创建 DeliveryRecord、ACK state、plugin 或 event bus，未来 P07 可直接接入而不重写领域逻辑。
- 决策（P05-FIX-01 rejected handshake）：`ConnectionRejectedEnvelopeBuilder` 只使用 P03 Envelope、exact schema 与 canonical serialization，payload 固定为 reason/server_time/retryable；reason 是 protocol/minimum/capability incompatible、IAM denied/unavailable、authority invalid、internal failure 的低基数闭集。合法且已解析 hello 在 transport/protocol 仍可安全回复时，先用既有 Clock/TaskSupervisor 有界 best-effort 发送 rejected，再关闭；send failure 不覆盖原握手失败，也不得发布 mapping/index/ACTIVE。malformed hello、transport 已失效或无法安全选择协议时直接关闭；任何 rejected 均不得包含 token、identity、tenant、capability/IAM/permission、peer/transport ID 或异常文本。
- 决策（P05-FIX-01 composition/lifecycle）：`ConnectionLifecycleManager` 是唯一 P05 logical lifecycle owner，显式接收 TransportManager/adapters、LocalConnectionIndex、Clock、既有 TaskSupervisor、IdentifierFactory、HandshakeIamAdapter、protocol registry/codec、processor registry factory 与 policy。每个 enabled adapter 的 supervised accept loop 执行 hello-first、IAM、protocol/capability、SC-1、binding/index、accepted、ACTIVE；ACTIVE 后唯一 read owner 通过 P03 codec/schema、current session/epoch gate 与 P05 processor registry处理已实现 lifecycle message，disabled 类型返回标准 feature-disabled error。ordinary disconnect 立即摘除 target并进入30秒 grace；resume IAM重验后epoch+1；reauth原子更新authority/index或fail-close。RSD-1在transport admission后停止logical admission/read loops，再drain/close logical connection与transport，最终由同一TaskSupervisor收敛任务；不创建第二listener/event loop/signal/shutdown/supervisor owner。
- 决策（P05-FIX-02 handshake budget/safety）：每次 composition admission 在读取 hello 前只创建一个 `HandshakeDeadlineBudget`，以 absolute monotonic deadline 贯穿 receive、semantic parse、IAM、protocol/capability negotiation；后续组件只能消费 remaining budget，不能重新获得完整 timeout。HelloClaimParser semantic failure无条件清理credential并由同一receiver把candidate logical state推进CLOSING，bounded transport close真实成功后才CLOSED。IAM supervised operation不得直接暴露adapter异常：普通deny/timeout/unavailable/hostile exception在operation内部清除traceback/context/cause后返回无credential typed outcome，外层才映射固定拒绝；CancelledError原对象穿透。expected IAM/rejected send failure不得成为TaskSupervisor failure或在shutdown report保留credential frame/token。
- 决策（P05-FIX-02 drain/cleanup ownership）：composition处理`connection.drain`只执行ACTIVE->DRAINING并立即摘除target，不再调用`complete()`；read loop与transport保持，heartbeat/reauth及当前允许lifecycle/control继续处理，重复drain幂等且不延长deadline，只有既有Clock deadline或显式lifecycle/shutdown completion才进入closing。manager close先发布CLOSING，再等待P04 transport close；普通failure保留index/owner与completion watcher并返回retryable false，cancellation原样穿透且同样不清owner，只有retry/concurrent shutdown后的真实close成功才发布CLOSED、删除index/owner。drain timeout successful close通过受监督completion signal回收唯一manager owner，不创建第二shutdown/task owner。
- 决策（P05-FIX-03 pre-index candidate ownership）：`ConnectionLifecycleManager`在每次admission receive前创建内部candidate cleanup record，以本地递增sequence为唯一key，只持有candidate transport、W01 state machine、fixed terminal reason与cleanup lock；它不进入LocalConnectionIndex、不建立mapping/ACTIVE，也不向日志/metric/repr暴露token、peer或transport ID。semantic/malformed handshake、IAM rejection、unknown resume与resume pre-publish failure都把terminal close委托给该owner。真实close成功才CLOSED并删除record；普通failure保留CLOSING ownership，CancelledError原对象穿透且不提前CLOSED；retry API或既有manager drain继续清理，不允许内部固定次数retry、global registry、第二supervisor或shutdown owner。
- 决策（P05-FIX-03 draining terminal convergence）：DrainService是所有DRAINING terminal的first-reason同步点。heartbeat、reauth、expiry及manager protocol/shutdown owner在close前调用external-terminal observation，在同一drain lock内冻结首个LogicalConnectionCloseReason、同步index/state machine为CLOSING并取消drain deadline；close后仅当index因真实close成功删除才finalize completion signal。close failure/cancel时deadline保持取消、reason与owner保持、watcher继续等待retry；后到DRAIN_TIMEOUT、SHUTDOWN或其他terminal request不能覆盖首因。DrainSnapshot、state machine、LocalConnectionIndex与实际terminal service使用同一classification。
- 决策（P05-FIX-04 resume post-commit ownership）：resume coordinator成功返回代表新mapping、SessionContext/index、accepted、ACTIVE target与旧grace已经提交。manager必须在下一个可取消await前，以无await同步段把新context、transport和新grace写入既有logical owner、设置post-commit activation marker并删除candidate cleanup record；candidate辅助状态机不再参与commit后的transport ownership。此后旧expiry stop、heartbeat/expiry/read activation或shutdown的任何失败/取消只能fail-close logical owner，不能回退到candidate cleanup。CancelledError原对象穿透；transport close普通失败保留CLOSING index、logical owner与marker，由retry cleanup继续，candidate owner不得重新出现。
- 后果：并发重复认证最多一个进入 authenticated；active 上的 drain/close 按锁顺序线性化，draining保持非target但可继续health/reauth，close failure/cancel不会伪造closed或遗失indexed/pre-index/post-resume cleanup ownership。resume commit后的每个可观察调度边界只存在candidate XOR logical owner，且commit成功后固定为logical owner；安全关闭一经标记不能被grace或新token恢复。reauth失败、heartbeat terminal或绝对TTL到期会以真实首因立即取消drain deadline并收敛watcher，成功续期只原子替换同一logical session的权限快照。真实 WebSocket/TCP plaintext/TLS listener 已能完成 canonical hello/accepted/ACTIVE与drain/reauth交叉终态，disconnect/resume/old epoch使用同一composition链；未来P07/P08必须消费typed audit requirement而不能把P05 lightweight processor、candidate collection或test sink误作generic/durable实现。
- 阶段状态：`P05-W01` 至 `P05-W14`、`P05-FIX-01`、`P05-FIX-02`、`P05-FIX-03` 与 `P05-FIX-04 VERIFIED`；`SC-1 VERIFIED`，显式测试IAM下完整logical connection lifecycle达到`F3`；ordinary production connection在P06前继续fail-closed，`P06-B01/P06-R01`及其余P06 backend/runtime工作包保持`NOT_STARTED`。
- 关联阶段/工作包：`P05-W01` 至 `P05-W14`、`P05-FIX-01`、`P05-FIX-02`、`P05-FIX-03`、`P05-FIX-04`、`P06`、`P07`、`P09`、`P11`、`P12`、`P16`、`P21`。

## ADR-031

- ADR 编号：`ADR-031`
- 状态：`ACCEPTED`（P06 阶段已冻结）
- 背景：P05 的测试 IAM adapter 与 production fail-closed 占位不能提供普通连接生产鉴权，也不能表达 runtime node credential、权限版本失效、消息级 strict/cache 鉴权或 backend 故障恢复。P06 必须补齐合同，同时不得提前建立 P07 generic processor pipeline、P08 StateStore/lease/fencing、P10 payload storage 或可靠投递状态。
- 决策：冻结 `IAM-R1`。`ns_common.iam` 是 backend/runtime 共享的 transport-neutral 类型边界，principal 闭集为 frontend_user、backend_service、client、node、runtime_node、management。Introspection 精确返回 identity、tenant、principal/component、IAM 裁决后的 capabilities、permission snapshot ref/digest/version、issued/expires、credential status 与 resume eligibility；客户端 component_type/requested capabilities 只作为待校验输入，mismatch 或 capability expansion 必须 fail-closed。
- 决策：runtime composition root 通过既有 `NsHttpClientOwner` 创建唯一显式 IAM HTTP client并注入 `IamClient`；不得调用 legacy/global HTTP getter。每个请求携带显式生成 trace 和 header-only internal service credential；handshake token 继续只由 single-use credential 转移并在调用后释放。生产配置强制 IAM HTTPS、替换 runtime/backend 两端占位凭证并保持 fail-closed，避免 access token 或内部凭证在明文链路上传输。timeout、5xx/transport failure、非法 JSON、wrapper/schema 缺失统一映射稳定 IAM timeout/unavailable，handshake 一律拒绝，不使用缓存权限接纳新连接。
- 决策：`PermissionSnapshot` 只保存 session authority 与最小 permission metadata，生成的 auth_context 精确为 permission ref/digest、iam_mode、issued/expires；不保存 token、credential secret、原始 IAM response 或 permission mapping。消息授权入口只建立 P06 security gate，不是 P07 processor：先校验 session identity/tenant/snapshot/version及 target tenant，后做 permission decision。strict 每条访问 backend；cache 只复用 TTL 内同 snapshot version 的既有 decision，invalidation/version drift 清缓存并刷新，刷新不得增加 capability、延长 credential expiry 或恢复已撤销 resume 权限。
- 决策：runtime node credential 使用与 user access token 不同的 `nsrn1` signed envelope，backend 通过显式 status repository执行 issue/refresh/revoke并限制 role scope。bootstrap 只返回 role authorization、authorized roles、candidate-master classification、server-side config/policy version；candidate master 不授予 leader lease、fencing 或 cluster authority。runtime 本地 credential cache 只保留 AES-GCM authenticated ciphertext，读取时重新校验 issuer HMAC signature、credential TTL、local revocation 与 required role；无明文文件持久化接口。
- 决策：access_check 类型完整携带 message.type、target、cross-tenant、management、task-creation 与 snapshot version；backend 必须由 target tenant 和 message.type 重算安全标志，不能信任调用方布尔声明。backend unavailable 时，high-risk control、cross-tenant、新配置、global coordination write 必须绕过缓存并无条件拒绝；低风险只能复用仍在 TTL/version 内的既有 allow decision。backend recovery 不继承旧授权，必须以新一代 evidence 同时重验 credential、role、config、lease、fencing、session snapshot；重验期间再次失联使当前 recovery generation 作废。lease/fencing 在 P06 只是 validation input，不实现或持有 P08 权威状态。
- 决策：payload_ref validation 冻结 object/version/checksum/tenant/owner/source/target/expiry/revocation/callback 合同；当前 backend endpoint 固定 fail-closed 为 payload storage not implemented，不上传、下载、签发 URL 或保存 payload。cryptography/cffi/pycparser 因 backend 与 runtime 共同使用移入 common 生产依赖层，不改变 DEP-1 无环边界。
- 后果：ordinary production connection 已从 P05 fail-closed adapter 迁移到显式 backend IAM HTTP contract；P05 SC-1、single TaskSupervisor、shutdown owner、event loop、9 enabled/40 disabled message contracts保持不变。P07/P08/P10 只能消费 IAM-R1，不得反向放宽 tenant、credential、snapshot 或 unavailable/recovery 语义。
- 阶段冻结：P06-B01 至 B08、P06-R01 至 R08 经专项、下游联合与全仓回归，以及 compileall、dependency manifest 和禁止边界扫描后达到 `VERIFIED/F3`。payload storage、generic processor pipeline、StateStore、lease/fencing authority、DeliveryRecord/ACK/NACK/Defer/retry/dead-letter 均未实现。
- 关联阶段/工作包：`P06-B01` 至 `P06-B08`、`P06-R01` 至 `P06-R08`、`P07`、`P08`、`P10`、`P17`、`P20`。
