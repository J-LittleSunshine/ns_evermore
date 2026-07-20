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
- 后果：P02-W06 可以在这一生命周期基础上增加信号驱动的进程关闭、实际资源关闭编排和超时观测，但不得重新把 `STOPPED` 后 stop 改为错误，也不得禁止 `FAILED` 后显式清理或重试。后续 RuntimeContext、HTTP owner、sink、TaskSupervisor 和 transport 资源必须通过 stop hook 遵守相同的一次性启动、失败保留所有权和成功后才进入 `STOPPED` 的边界。
- 关联阶段/工作包：`P02-W02`、`P02-FIX-01`、`P02-W06`。

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
- 决策（P02-FIX-03 校准）：composition root 不得用 `NsConfig.load(config_path=None)` 加载启动快照，因为 CFG-1 的兼容语义会在配置、依赖和 TLS 门禁前调用 `ensure_runtime_dirs()`。`main()` 必须先严格解析环境，再显式解析默认配置文件路径，并将该非空路径交给 `RuntimeStartupPreflight.load_config_snapshot()`；后者与 preflight 的配置二次验证共用唯一 field/reason 归一化函数。生产明文、关闭 `require_tls_in_prod`、非生产禁止明文、生产非 Redis/Valkey StateStore 都归一为 `RUNTIME_STARTUP_SECURITY_ERROR`，普通 `NsConfigError` 保持原类型、code 与 details。不得为此修改 `CFG-1` 的全局 facade、默认路径、无路径目录准备或既有 `NsConfig.load()` 兼容语义。
- 决策：startup 环境不采用未知值静默回退；非法环境返回稳定 `RUNTIME_CONFIG_INVALID`。生产环境中任一启用入站 transport 必须配置 TLS，StateStore backend 只能为 Redis/Valkey；非生产明文继续受 `allow_plaintext_non_prod` 控制。上述安全违规统一为稳定 `RUNTIME_STARTUP_SECURITY_ERROR`，不复制 URL、路径、credential、底层异常文本或 cause。TLS 前置检查在本阶段只证明 Python 运行时能够创建服务端 TLS context；证书、私钥、CA、最小版本、cipher 与 reload 属于 P20，不得由本结果推断为已验证。
- 决策：当前 transport 准入表只允许设计基线 `websocket_tcp`，并在其配置启用时检查 runtime 生产依赖 `websockets`；该准入只表示配置可进入后续 P04 实现，不表示 listener 或 adapter 已存在。`websocket_http3`、`webtransport_http3` 和 `quic_native` 在对应阶段前一旦启用即返回稳定 `RUNTIME_TRANSPORT_DISABLED`。Redis/Valkey Python driver 仍按 `DEP-1` 留在测试层，P08 冻结 StateStore 生产合同前 preflight 只执行生产 backend 配置限制，不探测、连接或宣称 StateStore 可用。
- 决策：目录接线是冻结、显式路径集合，默认覆盖仓库 data/etc/log/tmp；SQLite 开发配置还准备其显式文件 parent。目录错误只公开稳定目录角色与失败类别，不公开真实路径或底层错误。preflight 结果冻结且只包含环境、event-loop 选择、是否安装 policy、配置化 transport/TLS adapter 名、StateStore backend、已检查固定依赖和已准备目录角色；它不是 capability registry、健康证明或资源 owner。
- 决策：唯一 `main.py` 继续通过函数内延迟 import 保持 package 与入口模块冷导入无配置、policy 和资源副作用。实际调用 `main()` 时按显式路径加载并归一化配置，构造最小显式 `RuntimeContext`，执行 `prepare()`，然后才导入、构造并通过新 policy 运行一次无监听 `RuntimeService` start/stop 生命周期。配置、transport、依赖或 TLS 失败均不得准备 preflight 目录、安装 policy 或构造 service。runtime 依赖缺失时进程稳定失败；按 `DEP-1` 不安装 runtime 包的 backend 环境只验证该 fail-closed 分支，不得为让 backend 回归成功而混装 runtime 生产依赖。P02-W06 将在相同 composition root 上增加信号等待和资源关闭，不得把 preflight 移入已运行的 loop 或 listener 之后。
- 后果：P04 创建首个 listener 时必须以成功的 `RSP-1` preflight 为前置，并继续独立完成 adapter/conformance；P08、P20 分别补齐真实 StateStore 与完整 TLS 生产校验。W04/FIX-03 不改变 `CFG-1`、`RSL-1` 或 `RTC-1`，不向 context 增加未冻结依赖槽位，也不宣称角色、信号关闭、loop lag、IAM、WebSocket、Redis/Valkey 或 TLS 证书能力完成。composition root 当前注入普通 `logging.Logger`；W05 开始实际使用 runtime logger 前必须完成生产安全日志接线。
- 关联阶段/工作包：`P02-W04`、`P02-FIX-03`、`P02-W05`、`P02-W06`、`P04`、`P08`、`P20`。
