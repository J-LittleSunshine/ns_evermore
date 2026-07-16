# ns_runtime 设计边界与功能清单

> 文档版本：`0.0.2`
> 本版本正式纳入 `uvloop` 事件循环策略，并为 WebSocket over HTTP/3、WebTransport 和原生 QUIC 的后续接入预留传输抽象、能力协商、路径迁移、安全策略、配置和可观测边界。

> 本文档用于在后续会话、方案讨论和实现过程中保持 `ns_runtime` 的设计边界与功能定义不漂移。
> 每条清单都应表达完整条件、默认行为、例外边界或策略化决策，而不是只写名词摘要。
> 本文档不是实现方案，不展开代码结构、类设计、目录规划或具体编码细节。

## 0. 使用约定

- 当新会话继续讨论 `ns_runtime` 时，应先阅读本文档，并把本文档视为已经确认过的设计边界，而不是重新猜测用户意图。
- 当某个设计点在本文档中写明“必须”“禁止”“默认”时，后续方案不得随意改写；如需变更，应先显式提出变更原因并重新确认。
- 当某个设计点在本文档中写明“由策略配置”“可配置”“按消息类型配置”时，后续方案应保留策略扩展点，而不是在实现层写死单一行为。
- 当本文档中区分“强一致数据”和“异步/可观测数据”时，后续方案必须保留这种可靠性等级差异，不能为了简化把所有状态都当作缓存，也不能把所有观测数据都放进强一致路径。
- 当本文档中提到 `ns_backend`、`ns_frontend`、`ns_client`、`ns_node`、`ns_common` 时，均指 `ns_evermore` 项目内对应组件。
- 本文档直接描述 `ns_runtime` 的完整设计边界、功能范围、默认行为和生产约束，不按研发阶段、版本里程碑、MVP 或单机演示拆分要求。
- 某项能力尚未实现、仅完成局部验证或暂时采用替代实现，不改变本文档中已经确认的边界；实现不得以阶段性目标为由降级为临时协议、弱一致状态或旁路控制链路。
- 本文档不记录【实现进度】、阶段完成度或局部验收结论；实现状态、测试结果和发布进度应在独立的项目计划、任务清单或验收报告中维护。

## 1. 代码样式与实现风格约束

- `ns_runtime` 后续实现应优先使用类来表达职责边界和能力分组，例如 service、processor、registry、store、policy、coordinator、session、transport 等；除非确有必要，不应把主要逻辑散落为模块级全局方法。
- 模块级全局方法只应出现在确有语言、框架或可读性需要的场景，例如进程入口适配、极小且无状态的纯函数、类型转换器、常量构造、测试辅助或第三方库要求的回调；一旦逻辑需要依赖状态、配置、策略、存储、连接或审计，就应收敛到类或对象方法中。
- 模块级全局可变状态默认禁止；运行期状态应归属明确的 service、registry、store、runtime context 或 processor instance，并通过显式依赖注入、构造参数或上下文对象传递。
- 类的职责应按逻辑模块边界拆分，避免出现一个类同时承担连接管理、Envelope 解析、IAM 鉴权、路由、可靠投递和审计等多个核心职责；需要协作时通过明确接口组合，而不是在类内部硬编码跨层访问。
- 类名、函数名和模块名应延续已确认的 `service`、`processor`、`runtime`、`coordinator`、`registry`、`store`、`policy` 等语义；除入口文件必须为 `main.py` 外，后续实现仍应避免 `cli`、`app`、`handler` 作为核心命名语义。
- processor 既可以是某类消息的业务处理单元，也可以是流水线阶段；实现时应通过基类、协议接口或注册元数据区分 processor 的阶段、message.type、权限声明、schema 和运行限制，而不是依赖函数名约定。
- 依赖关系应从外向内显式传入，避免在深层 processor、路由逻辑或可靠投递逻辑里直接 import 并实例化全局单例；这有利于测试、热更新、插件限制和多进程隔离。
- 配置、策略、状态存储、IAM 客户端、事件发布器和审计器应作为明确依赖出现；后续实现不应通过隐藏全局变量、隐式上下文或 monkey patch 访问这些核心基础设施。
- 对外协议模型、状态记录和策略输入输出应优先使用类型明确的结构对象，而不是在核心链路中长期传递未约束的裸 dict；只有在 Envelope 原始解析、插件扩展字段或第三方边界处才保留动态结构。
- 函数、方法和构造器签名默认不换行；除非参数数量超过 6 个、单行超过格式化宽度或类型标注明显影响可读性，否则应保持签名在同一行。
- 定义变量、函数入参、方法入参和构造器入参时必须写类型提示；只有极少数类型无法稳定表达、第三方动态对象边界或测试 mock 场景可以例外，并应尽量在最近边界处收敛为明确类型。
- 注释应解释状态机、可靠性、一致性、安全边界和策略取舍，不应为显而易见的赋值或调用写噪音注释；复杂状态迁移、fencing、ACK/NACK/Defer 原子操作和恢复逻辑应保留简短解释。
- 测试代码可以使用必要的函数式辅助和 fixture，但生产代码的主要执行路径仍应遵守类分组、显式依赖和无全局可变状态的约束。
- `ns_runtime` 的异步生产代码必须基于标准 `asyncio` 接口编写；除进程启动边界和受控适配层外，processor、transport、session、router、delivery worker 和 store 不得直接依赖 `uvloop` 私有类型或专有 API。
- 传输协议差异必须收敛在 transport adapter 和 transport capability 模型中；核心业务代码不得通过散落的 `if transport_type == ...` 分支分别实现 WebSocket、QUIC 或 WebTransport 语义。

## 2. 核心定位与职责边界

- `ns_runtime` 的最终定位是 `ns_evermore` 中超高性能、高可用的实时通信和调度组件，因此设计时必须同时关注低延迟、高吞吐、可靠投递、集群容错和可审计运行控制。
- `ns_runtime` 不是单纯 WebSocket 网关，也不是绑定某一种底层传输的网关；当消息经受支持的 transport adapter 进入 runtime 后，它既要负责实时通信与消息路由，也要负责短生命周期任务投递、投递状态维护、ACK/NACK/Defer 处理、重试、死信、恢复和运行时控制。
- `ns_runtime` 管理的任务语义更接近短生命周期 RPC 投递；runtime 负责把任务 envelope 安全投递给目标连接并等待“已收到 ACK”，但不把业务执行完成作为 delivery 成功条件。
- ACK 的唯一核心语义是“目标连接已经收到 envelope”；目标收到但尚未开始执行任务时也可以 ACK，因此后续任何状态机、审计、重试和统计都不能把 ACK 解释为任务完成。
- 业务任务状态、任务完成状态、业务失败原因和最终业务结果以 `ns_backend` 为准；`ns_runtime` 只维护连接状态、路由状态、投递状态、ACK/NACK/Defer 状态和运行控制状态。
- 当任务执行结果需要实时回传时，可以通过 `ns_runtime` 发送新的 result/callback envelope；当任务执行结果适合直接上报时，客户端或节点也可以直接调用 `ns_backend` API。
- 当任务包包含 callback 钩子时，callback 只描述业务结果或状态回传方式；callback 不参与原 delivery 的 ACK 成功判断，也不能延迟原 DeliveryRecord 进入 `acked`。
- 当 callback 选择通过 runtime 路由时，callback 本身必须作为新的 envelope 进入协议层、鉴权层、processor 流水线、路由调度和可靠投递链路。
- task 类型消息的创建权不能默认开放给所有连接；只有 `ns_backend`、具备管理/调度 capability 的连接，以及经过 IAM 明确授权的 `ns_frontend`、`ns_node`、`ns_client` 才能创建并请求 runtime 调度任务。
- 所有连接方应抽象成统一的 `client identity + tenant + capabilities + component_type + connection_id` 模型；但路由规则中仍必须保留 `frontend`、`client`、`node`、`backend`、`runtime/sub_node` 等明确组件类型差异。
- 多租户隔离不是只在鉴权时校验 tenant 边界；连接池、调度策略、限流、背压、恢复扫描、指标统计和观测推送都必须具备 tenant 维度。
- runtime 的逻辑连接、会话、Envelope、processor、路由和可靠投递语义必须独立于底层 transport；未来增加 WebSocket over HTTP/3、WebTransport 或原生 QUIC 时，不得重新定义 ACK、DeliveryRecord、tenant、IAM、source/auth_context 或 processor 边界。

## 3. 接入、传输与进程边界

- `ns_runtime` 当前正式启用的外部入站 transport 是 WebSocket 长连接，默认生产形态为 WebSocket over TLS/TCP；`ns_frontend`、`ns_client`、`ns_node`、`ns_backend` 管理端以及 runtime 节点均通过已启用的 runtime transport 建立长连接或长期 transport session。
- 设计必须预留 `websocket_http3`、`webtransport_http3` 和 `quic_native` transport adapter；这些 adapter 在未完成协议适配、安全评审、客户端兼容、故障注入和性能验收前默认禁用，不能因存在抽象或配置项就宣称已经支持。
- 所有 transport adapter 必须把入站应用数据归一化为明确消息边界，并交给同一连接与会话层、Envelope 协议层和 processor 流水线；禁止 transport adapter 提供 processor 私有数据通道、私有 ACK 通道或绕过 IAM/tenant 校验的快速路径。
- transport adapter 必须通过统一 capability 模型声明能力，至少能表达 `reliable_ordered_messages`、`reliable_bidirectional_streams`、`reliable_unidirectional_streams`、`unreliable_datagrams`、`stream_multiplexing`、`connection_path_migration`、`transport_flow_control`、`per_stream_flow_control`、`native_keepalive`、`zero_rtt` 和 `transport_resume`。
- 上层模块只能基于已协商且由 runtime 验证的 transport capabilities 做策略判断，不得把客户端自报能力直接视为可信，也不得在 processor、router 或 reliable delivery 中绑定具体 QUIC/WebTransport 库。
- `ns_runtime` 可以主动调用 `ns_backend` 的 HTTP/RPC API 做 IAM 鉴权、权限刷新、节点凭证获取和 payload object reference 校验；该主动调用能力不构成普通客户端入站 transport，也不能作为旁路消息或管理控制通道。
- 健康检查、运行状态查询、配置热更新、节点隔离、消息重投、消息清理、master 切换和限流调整都应通过已启用的 runtime transport 发送管理 envelope 进入 runtime，而不是另开默认 HTTP 管理端口。
- 如果容器、systemd 或运维系统需要进程级 healthcheck，应通过本地命令使用当前启用的本地 transport adapter 建立连接并发送 health envelope，而不是依赖 `/health` HTTP 探针。
- `ns_runtime` 是 `src/ns_runtime` 下的独立组件边界；后续实现可以复用 `ns_common`，但不应把 runtime 的核心进程入口、transport adapter、协议层或可靠投递状态散落到其他组件目录中。
- `ns_runtime` 必须作为独立进程运行，入口文件必须是 `main.py`；后续实现中模块名、类名、函数名都应避免 `cli` 和 `app` 语义，启动相关命名优先使用 `service`。
- 设计和实现时应优先复用 `ns_common` 已有基础设施；如果 runtime 需要通用能力而公共层不存在，可以扩展 `ns_common`，但不应把 runtime 私有协议硬塞进公共层。
- 消息处理语义必须使用 `processor` 而不是 `handler`；后续讨论中“处理某类消息”和“流水线阶段处理”都可以称为 processor，但需要通过上下文区分。
- `ns_runtime` 不强制定义统一客户端 SDK，也不要求 `ns_frontend`、`ns_client`、`ns_node`、`ns_backend` 必须通过同一个 SDK 接入。
- 设计文档只约束连接方必须遵守的应用协议行为，包括 transport/session 建立、`connection.hello`、协议与 capability 协商、heartbeat、ACK/NACK/Defer 语义、message_id/delivery_id 幂等、connection_epoch 校验、错误 envelope 处理、source/auth_context 禁止伪造和安全日志脱敏；具体 transport 握手细节由对应 adapter 负责。

## 4. 运行模式、角色与切换

- `ns_runtime` 必须支持 `master`、`sub_node`、`singleton` 三种模式，并且设计上不能假设启动后模式永远固定，因为 `singleton` 未来允许平滑升级或切换为 `master` 或 `sub_node`。
- `active_master + sub_node` 是生产集群的基准拓扑，必须支持该拓扑下的消息路由、跨节点转发、可靠投递、ACK 回收和集群协调；`singleton` 只作为本地开发、降级或调试模式存在，不能替代生产集群能力。
- 当 runtime 处于 `master` 模式且存在可用 `sub_node` 时，master 接收到消息后应按配置策略通过负载均衡或指定节点转发给 sub_node；此时 master 默认不接受普通客户端连接，只接受 sub_node、runtime 节点和管理类连接。
- 当 runtime 处于 `master` 模式但没有可用 `sub_node` 时，master 允许接受普通客户端接入并在本地处理消息；这个行为是 master 无 sub_node 时的降级/单点处理语义。
- 当 runtime 处于 `sub_node` 模式时，它必须主动接入 active master，并能接收来自 master 的消息在本地处理；同时 sub_node 可以接受任意类型普通客户端连接。
- 当 runtime 处于 `singleton` 模式时，它可以接受任意类型客户端连接，并在本地完成连接管理、路由、投递和处理，不依赖 master/sub_node 拓扑。
- 当 active master 和 standby master 并存时，二者允许使用不同接入策略；standby master 默认只接受 runtime 节点和管理端连接，用于健康、切换和控制，不接受普通客户端连接。
- 当某个 master 已有普通客户端连接而后续出现 sub_node 或角色策略变化时，现有连接是平滑收尾后通知重连、保留到自然断开，还是由策略强制关闭，必须作为配置策略处理；当前 `ns_runtime` 设计边界不包含跨 runtime 节点的透明逻辑连接迁移。QUIC/WebTransport 在同一 runtime、同一逻辑 session 内发生的网络 path migration 不属于跨节点连接迁移，不改变 connection owner。
- Runtime Service 层必须维护角色状态机，至少表达 `singleton`、`sub_node`、`standby_master`、`active_master`、`transitioning`、`draining` 等角色/过渡状态。
- `degraded`、`isolated`、`unavailable` 这类状态应作为角色之外的健康/能力附加状态，因此一个节点可以表达为 `active_master + degraded`、`sub_node + isolated` 或 `singleton + degraded`。
- 当 runtime 进入 `transitioning` 或 `draining` 时，普通业务消息和新任务调度默认返回标准错误 envelope；ACK、NACK、Defer、管理控制、健康检查和集群事件仍允许继续处理。
- 当节点进入 `isolated` 时，隔离程度必须由策略配置；策略可以表达只禁止新普通连接、禁止作为路由目标、禁止参与集群转发、只保留管理健康通道等不同等级。
- `draining` 状态应表达“不再接收新普通连接或新普通业务流量，但尽量完成已有投递、通知客户端重连或由外部发现机制重新接入，并在超时后按策略强制关闭或转移未完成 delivery”的收尾语义。
- standby master 即使维持健康、状态观察和切换准备连接，也不能在未持有有效 leader lease/fencing_token 时执行全局协调写入。

## 5. 逻辑模块分层

- `ns_runtime` 的逻辑分层按职责依赖关系组织，而不是简单按数据流顺序排布；后续方案应保持基础支撑层、运行核心层、消息处理核心层和集群协作层的边界。
- 基础支撑层必须包含配置管理层、状态存储层、事件与观测层、策略引擎层、安全与 IAM 层；这些层为其他模块提供能力，不应被业务 processor 绕过。
- 运行核心层必须包含 Runtime Service 层、传输层、连接与会话层、Envelope 协议层；这四层分别负责进程/角色、transport adapter 与传输能力、逻辑连接/session、协议外壳。
- 传输层负责底层连接或 transport session 的建立与关闭、应用消息边界、收发、传输层流控、stream/datagram/path 状态、transport keepalive、TLS/ALPN 和 transport capability 暴露；它不得负责 IAM 业务权限、tenant 路由、Envelope schema、task 调度、DeliveryRecord、runtime ACK/NACK/Defer、业务 retry 或 dead letter。
- 连接与会话层只面向统一 transport adapter 接口，不得直接依赖 WebSocket、QUIC 或 WebTransport 的具体库对象；上层 processor、路由和可靠投递只能操作 runtime logical connection/session 和标准化 send/receive 结果。
- 消息处理核心层必须包含 Processor 流水线层、路由与调度层、可靠投递层；其中 processor 执行行为，路由决定目标，可靠投递维护 delivery 生命周期。
- 集群协作层必须包含集群协调层；集群协调层依赖状态存储、连接、Envelope、processor 和事件，但不能替代这些层的职责。
- 配置管理层和策略引擎层必须拆开；配置管理层只负责配置来源、版本、热更新、回滚和生效方式，策略引擎层负责基于配置和运行时上下文做决策。
- 安全与 IAM 层作为独立横切层存在，但内部可拆分连接身份认证、runtime 节点凭证认证、IAM 客户端、权限快照缓存、严格消息鉴权、缓存消息鉴权、tenant 边界校验、capability 校验和脱敏审计等子模块。
- Envelope 协议层必须严格独立，只做 JSON envelope 解析、schema 校验、版本校验、基础字段规范化、错误 envelope 构造和序列化；它不处理业务、不调度任务、不决定路由。
- Processor 流水线层负责所有可执行行为，ACK、NACK、Defer、管理控制、健康检查、集群事件、任务调度和业务扩展都必须进入 processor，不允许另开绕过 processor 的控制通道。
- 事件与观测层是旁路通知和扩展机制；核心链路采用显式调用和明确流水线，不能把所有模块之间的主通信都变成事件总线，以免调试和可靠性变得不可控。
- 管理控制不作为独立顶级链路层，而是作为 Processor 流水线层中的特殊 processor 组；健康检查也归入管理控制 processor 组。

## 6. 统一 Envelope 协议模型

- 所有业务消息、任务消息、ACK、NACK、Defer、流式分片、管理控制、健康检查和集群事件都必须使用统一 JSON envelope；当前唯一启用的 wire codec 为 UTF-8 `json.v1`。WebSocket adapter 必须使用 JSON 文本帧；未来 QUIC/WebTransport adapter 默认必须在可靠、有序且具有明确消息边界的 stream/message 上承载完整 `json.v1` 文档，只有策略明确允许的 best-effort 类型可按本文档约束使用 datagram。
- 除 transport 原生控制事件外，例如 WebSocket ping/pong/close、QUIC packet ACK、path validation、stream flow-control 或连接关闭事件，所有已认证 runtime session 上的入站应用数据都必须被解析为合法 envelope 并进入后续层，或返回标准错误 envelope/按严重错误策略关闭；不能允许“裸 JSON 命令”“半协议控制消息”、processor 私有帧、私有 QUIC stream 或私有 datagram 绕过 Envelope 层。
- Envelope 采用分组结构，顶层允许的核心分组包括 `protocol`、`message`、`source`、`target`、`route`、`delivery`、`stream`、`auth_context`、`payload`、`callback`、`trace`、`extensions`；不适用的分组直接省略。
- `tenant_id` 是 runtime 归一化 envelope 的一等安全上下文，必须来自连接 IAM 结果或 runtime 节点凭证上下文；发送方不能通过 envelope 自行声明或覆盖当前 tenant，跨 tenant target 只能作为请求意图并由 IAM/策略显式授权。
- envelope 中用于路由和鉴权的 capabilities 必须以 IAM 返回的连接 capabilities、runtime 注入的 source/auth_context 摘要和 target 请求条件为准；发送方在普通消息中声明 capabilities 只能作为目标筛选条件或请求意图，不能提升自己的权限。
- 不适用的 envelope 分组必须省略，不应使用 `null` 或空对象表达“无语义”；只有某个字段协议明确允许为空时，才能使用空值。
- Envelope 顶层未知字段必须拒绝，核心分组内部未知字段也必须拒绝；扩展字段只能放在 `extensions` 中，并由对应插件 namespace 的 schema 校验。
- `protocol` 分组只表达应用协议版本和兼容性信息；transport 类型、ALPN、网络路径、拥塞状态和 transport capabilities 不放在每条 envelope 的 `protocol` 中，而是在连接建立和 `connection.hello` 阶段协商并写入 session context。当前 wire codec 固定为 `json.v1`，因此 envelope 内不需要逐消息 encoding 字段。
- 协议版本协商必须支持严格拒绝和兼容降级两类策略；当无法满足客户端 version/min_version 与 runtime 支持范围时，必须在 handshake 阶段拒绝并关闭连接。
- `message` 分组必须承载 `message_id`、`type`、`category`、`priority`、`created_at`、`expires_at`、`reliability` 等核心元数据；其中 `priority`、`expires_at`、`reliability` 可以由发送方建议，但最终由 runtime 策略裁决。
- `message.type` 使用点分命名风格，例如 `task.dispatch`、`delivery.ack`、`delivery.nack`、`delivery.defer`、`stream.start`、`stream.chunk`、`stream.end`、`runtime.control.kick_connection`、`cluster.event.node_joined`。
- 入站 envelope 禁止发送方携带 `source`；source 必须由接入 runtime 根据已认证 session 注入，如果入站携带 source，应视为身份伪造或严重协议错误。
- 出站 `source` 至少应能表达原始发送方的 runtime_id、connection_id、identity 摘要、tenant_id、component_type 和 capabilities 摘要；跨节点转发时不能把 relay runtime 误写成原始业务 source。
- 入站 envelope 禁止发送方携带 `auth_context`；auth_context 必须由 runtime 根据连接鉴权结果和权限快照注入，如果入站携带 auth_context，应视为伪造或严重错误。
- 出站 `auth_context` 只允许携带权限快照引用、权限摘要、iam_mode、issued_at、expires_at 等最小必要信息；不得携带原始 token、敏感权限明细或可被接收方复用的凭证。
- 跨节点转发时必须保留原始 source，同时使用独立 `route` 分组记录 root runtime、current runtime、previous runtime、next runtime、route segment、routing_plan_id、hop 和 max_hops 等路由路径信息。
- `route.hop` 和 `route.max_hops` 必须用于防止跨节点转发循环；超过 max_hops 或发现重复 route segment 时，应按路由错误和安全审计策略处理。
- `target` 分组必须包含 `kind` 来避免寻址歧义；`kind` 可以是 `connection`、`identity`、`tenant`、`capability`、`component_type`、`runtime`、`broadcast` 或未来受控扩展类型。
- `target.kind=connection` 时必须提供 connection_id；`target.kind=identity` 时必须提供 identity；`target.kind=capability` 时必须提供 capabilities；`target.kind=component_type` 时必须提供 component_type；`target.kind=runtime` 时必须提供 runtime_id；`target.kind=tenant/broadcast` 时必须声明 tenant 或广播范围与过滤条件。
- 当 target 指向多个连接可能性时，消息必须显式指定多连接策略，或由系统默认策略裁决；后续实现不能在 identity 多连接场景下隐式广播或隐式任选而不留策略痕迹。
- `delivery` 分组只在可靠投递相关消息中出现，包含 `delivery_id`、`summary_id`、`root_delivery_id`、`parent_delivery_id`、`attempt`、`ack_timeout_ms`、`replay_epoch` 等投递维度字段；`message_id` 只从 `message.message_id` 读取，不在 delivery 中重复。
- `payload` 必须支持 inline 小 payload 和 `payload_ref` 对象存储引用两种模式；inline 大小上限完全由 runtime 策略决定，payload_ref 必须实时调用 `ns_backend` 校验。
- 当 inline payload 超过 runtime 策略允许大小、JSON 深度、应用消息大小或当前 transport adapter 的受控承载限制时，应返回错误 envelope 或按严重错误策略断开连接，并且不能为了兼容发送方自动转为 payload_ref。
- 当 payload 使用对象引用时，runtime 只负责路由带对象引用的 envelope，不负责对象上传、对象下载或签名 URL 生成；对象存储层由后续 `ns_backend` 能力提供。
- DeliveryRecord、DeliveryAttempt、MessageDeliverySummary、审计记录和状态变更日志默认只保存 envelope 元数据、payload_ref、payload 摘要、大小、类型、checksum/version 等可追踪信息；除非后续重新确认，不应把完整业务 payload 写入 runtime 强一致状态或审计明文。
- `callback` 分组只描述业务结果或状态回传方式，不参与 delivery ACK 语义；如果 callback 经 runtime 发送，它必须成为新的 envelope 并拥有新的 message/delivery 生命周期。
- `trace` 分组必须支持 `trace_id`、`span_id`、`parent_span_id`、`correlation_id`、`request_id`，以便跨 frontend/client/node/backend/runtime 追踪消息、投递和控制操作。
- `stream` 分组只放流式状态字段，例如 `stream_id`、`sequence`、`ack_sequence`、`ack_ranges`、`missing_sequences`、`received_sequences`、`end_reason`；stream 消息类型由 `message.type` 表达，不再放 `stream.kind`。
- 内部 runtime processing context 中的接收时间、策略版本、校验结果、lease/fencing 细节等不出现在出站 envelope；只有接收方需要理解的协议字段才进入 envelope。
- Envelope schema 校验采用“基础 envelope schema + message.type 专属 schema”的叠加模型；插件 processor 可以注册自己的 message.type schema，但不能放宽核心字段约束。
- 未注册、未授权或被策略禁用的 extension namespace 不得静默进入业务 processor；其处理方式应由策略决定为拒绝、忽略并审计或降级处理。
- 禁止使用临时扁平协议结构，也不得为了快速跑通通信而绕过统一 Envelope 分组模型。
- 所有入站和出站消息必须使用 `protocol / message / source / target / route / delivery / stream / auth_context / payload / callback / trace / extensions` 统一分组结构。
- 不适用的分组应省略，不能用 `null` 或空对象占位。
- 所有功能类型都必须在统一 Envelope 外壳、字段校验、source/auth_context 注入、未知字段拒绝和标准错误 envelope 约束下执行；不得以功能尚未完整实现为由绕过核心协议边界。
- 内置 `message.type` 必须建立完整类型族注册表，不能只覆盖最小通信闭环。
- 内置类型族至少包括连接握手、连接心跳、任务调度、可靠投递、ACK/NACK/Defer、stream、管理控制、集群事件、配置热更新、dead letter、replay、cancel、hold、状态查询和标准错误类型。
- 所有内置 `message.type` 都必须进入统一 Envelope schema 校验、权限声明、processor 注册、审计和错误处理链路。
- 所有内置类型必须提供 schema、权限声明、processor 入口、审计入口和标准错误响应，并遵守各自已定义的功能语义。
- 连接、集群、路由、任务投递、ACK/NACK/Defer 必须端到端可用。
- stream、replay、cancel、hold、dead letter、状态查询、配置热更新等类型必须具备本文档已经明确规定的语义、processor 入口和标准响应；未在本文档中明确规定的扩展语义不属于默认功能边界。可靠 stream 按本清单中明确规定的完整可靠性要求执行。
- QUIC packet ACK、stream-level delivery confirmation、拥塞控制反馈或 WebTransport session 状态都不能直接映射为 `delivery.ack`；runtime ACK 仍必须由目标逻辑连接发送合法 Envelope，并经过 processor 与强一致状态更新。
- WebTransport/QUIC datagram 默认不得承载 task、ACK/NACK/Defer、管理控制、集群协调、配置热更新、replay/cancel/hold、可靠 stream 控制、IAM/reauth 或任何要求 DeliveryRecord 的消息；只有被策略明确标记为 best-effort、loss-tolerant、unordered、非控制且非安全敏感的 message.type 才可在未来启用 datagram，并且仍必须使用统一 Envelope。
- wire codec 必须保留受控扩展接口，但 `0.0.2` 设计边界只允许 `json.v1`；任何二进制 codec、混合编码或按消息类型切换编码都必须重新确认协议版本、兼容矩阵、安全校验和审计边界。
- 协议兼容采用“主版本严格、次版本兼容”策略。
- `protocol.major` 不一致时，runtime 必须在握手阶段拒绝连接，并返回标准 `connection.rejected` 或 `runtime.error` envelope。
- `protocol.minor` / `patch` 可以通过 `min_version`、`supported_versions`、兼容矩阵和能力协商进行降级或兼容处理。
- 兼容协商必须发生在 `connection.hello` 握手阶段，协商结果写入 session context，并在后续 envelope 校验、processor 分发、schema 选择和错误响应中使用。
- processor 不得各自临时判断协议版本差异；协议版本兼容、字段兼容、schema 选择和降级能力必须集中在 Envelope 协议层和协议兼容策略中处理。
- 协议兼容不能放宽核心安全字段约束。即使次版本兼容，也不得允许发送方携带 source、auth_context、伪造 tenant、未知顶层字段或未授权 extension namespace。

## 7. 传输、连接与会话模型

- transport session 建立成功后，runtime logical connection 必须先进入握手阶段；正式接收任何业务、任务、ACK、NACK、Defer、管理控制、集群事件或 stream envelope 前，第一条有效应用消息必须是 `connection.hello`。
- 连接生命周期至少应能表达 `accepted -> handshaking -> authenticated -> active -> draining -> closing -> closed`，并能记录 `rejected`、`auth_failed`、`protocol_failed`、`timeout_closed`、`kicked`、`isolated_closed` 等失败或关闭原因。
- 握手阶段必须有超时保护；如果连接在握手超时前没有发送合法 `connection.hello` 或无法完成 IAM/协议协商，runtime 应返回可行的错误 envelope 后关闭，或在无法发送错误时直接关闭并审计。
- `connection.hello` 直接携带 token、声明 component_type、请求的协议版本和请求启用的 capabilities；token 只允许出现在握手入站 payload 中，不能写入普通审计明文，也不能放入后续 auth_context。
- 客户端可以声明 component_type 和 requested capabilities，但 runtime 必须把 token、component_type、requested capabilities、协议版本和连接来源信息交给 `ns_backend` IAM 校验；最终 identity、tenant、component_type、capabilities、权限快照、权限版本和 TTL 以 IAM 返回为准。
- 如果客户端协议 version/min_version 与 runtime 不能兼容，应在握手阶段返回 `connection.rejected` 并关闭连接；版本兼容是进入 active session 的前置条件。
- 握手成功后 runtime 返回 `connection.accepted`，其中只包含 `connection_id`、`session_id`、协商协议版本、heartbeat 配置、session_expires_at、server_time、runtime_id 和 role 等必要信息，不返回 tenant_id、identity 或完整 capabilities。
- session 必须支持续期；续期可以由 runtime 使用握手 token 或缓存凭证主动刷新，也可以要求客户端发送 `connection.reauth`，还可以配置为到期关闭连接。
- session 续期或权限快照刷新失败时，runtime 不能默认继续无限信任旧权限；应按策略进入降级、限权、要求 reauth 或关闭连接，并记录安全审计摘要。
- 如果使用客户端重新认证，消息类型为 `connection.reauth`，成功响应为 `connection.reauth_accepted`，失败响应为 `connection.reauth_rejected`；重新认证仍禁止客户端携带 source/auth_context。
- 心跳必须支持双层机制：transport adapter 使用其原生存活与路径检测能力，例如 WebSocket ping/pong 或 QUIC idle timeout/path validation；envelope heartbeat 用于 logical session、应用协议和 runtime 健康检查。
- envelope heartbeat 必须走 Envelope 协议层、安全硬校验和轻量 processor，但默认不进入可靠投递，不创建 DeliveryRecord，也不要求 delivery ACK。
- QUIC/WebTransport 的 0-RTT 默认关闭；即使 transport 库完成 0-RTT 握手恢复，也不得在握手确认、`connection.hello`、IAM 和协议/capability 协商完成前提交任何具有 runtime 应用语义的 Envelope。未来如需开放，只能对经过单独重放风险评估且具备明确幂等保护的只读类型按 allowlist 启用。
- transport 原生 ACK、stream write completion 或 packet delivery 回调只能作为 transport health/diagnostic 信号，不能创建 AckRecord、取消 runtime retry 或把 DeliveryRecord 更新为 `acked`。
- 连接层必须维护本地实时索引，包括 `connection_id -> session`、`identity -> connections`、`tenant -> connections`，并可扩展 component_type、capability、session_id 和 transport capability 等索引。
- 内部模型必须明确区分 runtime logical connection、transport session 和 network path：logical connection 至少包含 `connection_id/connection_epoch/session_id`；transport session 至少包含 `transport_type/transport_connection_id/transport_session_id/transport_stream_id`；network path 至少包含 `path_id/path_epoch/local_address/peer_address/validated_at/migration_count`。这些字段属于内部 session context、观测或审计摘要，不进入普通业务 Envelope。
- `connection_id` 表示 runtime 逻辑连接，不等同于 QUIC connection ID、HTTP/3 stream ID 或 WebTransport session ID；一个 runtime 逻辑连接在任一时刻只能绑定一个当前有效的已认证 transport session，但一个底层 transport connection 是否可复用多个 stream/session 由 adapter 明确管理并保留可追踪映射。
- 普通连接索引以内存实时状态为主，会话快照异步持久化和推送；集群拓扑、leader、隔离、暂停等控制状态必须强一致。
- 连接断开后允许短暂 reconnect grace period；在 grace period 内，客户端可以重新握手并复用原 `connection_id`，但每次重连必须增加 `connection_epoch` 来防止旧连接残留。
- 快速重连复用原 `connection_id` 必须满足 grace period 未过期、identity/tenant/component_type 与原 session 匹配、token 或 resume 凭证通过 IAM 校验、旧物理连接已关闭或被 fencing 排除等条件。
- 当前有效 runtime logical connection 必须由 `connection_id + connection_epoch` 标识；旧 epoch 收到消息、ACK、NACK 或 Defer 时必须拒绝或审计，不能更新当前 delivery 或 session 状态。
- 在同一 runtime、同一 transport session 和同一 logical session 内发生的 QUIC/WebTransport network path migration，只更新 `path_id/path_epoch` 和 transport 健康信息，不递增 `connection_epoch`，也不触发 DeliveryRecord owner transfer；只有 transport session 失效并通过 runtime resume/reconnect 建立新的逻辑连接实例时才递增 `connection_epoch`。
- network path migration 不得绕过 IAM、tenant、session TTL、component_type、capability 或安全策略；新路径必须由 transport adapter 完成验证，验证失败时按 transport failure 和 reconnect 策略处理。
- grace period 内该 connection_id 不视为 active target；发往该连接的新 delivery 应返回目标暂时不可用或进入 `retry_scheduled`，重连成功后再通过事件唤醒相关 retry。
- 如果 grace period 到期仍未重连，session 应彻底关闭并清理 connection_id、identity、tenant、capability 等索引；后续 fixed_connection delivery 按策略重试、等待或进入死信。
- 管理端 kick、安全违规断开和协议严重错误断开默认不允许 resume；普通网络断开和异常关闭是否允许进入 grace period 可以按策略配置。
- 管理端 kick 后应将 session 置为不可恢复关闭状态，清理 active 索引并通知相关 delivery 目标不可用；绑定 fixed_connection 的未完成 delivery 后续按策略 retry、dead_letter、cancel 或等待人工处理。
- 传输与连接层是第一道流控门槛，必须负责最大应用消息大小、单连接读队列、单连接写队列、transport/stream flow control、心跳或 idle timeout、慢连接检测、tenant 队列和 runtime 全局水位。
- 当连接读队列满时，具体行为由策略配置；如果发生在原始 transport message/stream 数据尚未形成合法 envelope 的阶段，runtime 只能按连接级策略处理，只有解析 envelope 后才能按 message type 或 priority 细分。
- 当连接写队列满时，连接层不能无限等待；可靠投递层应把对应 delivery 按写失败或背压策略处理，常见结果是进入 `retry_scheduled` 并降低目标健康评分。
- 任意已认证连接可以对自己发送 `connection.drain`，请求 runtime 停止向它分配新 delivery；普通连接不能 drain 其他连接，除非具备管理 capability。
- `connection.drain` 是单向状态变化；连接进入 draining 后不允许取消 drain 恢复 active，若要恢复接收新投递，应关闭后重新连接或重新握手。
- 当前 `ns_runtime` 设计边界不包含跨 runtime 节点的透明 logical session migration，也不通过 redirect envelope 实现无重新认证的跨节点无缝接管；拓扑调整仍通过 drain、close、grace resume、重新握手和外部发现/配置完成。同一 runtime 内由 QUIC/WebTransport 提供的 network path migration 已被允许，但不能被扩展解释为跨 runtime owner migration。
- 连接进入 draining 后，已在 `ack_waiting` 的 delivery 继续等待 ACK 或按策略超时，尚未发送的 queued delivery 应按策略重路由、重试或取消，drain 本身应有超时和最终关闭路径。
- 连接与会话状态应采用当前内存快照加状态变更事件日志模型；普通 open/close/heartbeat/reconnect 可以异步记录，session resume、kick、安全关闭、管理控制关闭等关键事件必须强审计。
- 普通网络断开允许进入 reconnect grace period，默认 `30s`。
- 在 grace period 内，客户端可以重新握手并申请复用原 `connection_id`，但必须重新通过 IAM 校验，并且 `identity`、`tenant`、`component_type` 与原 session 匹配。
- 每次 resume 成功后必须递增 `connection_epoch`，当前有效 runtime logical connection 由 `connection_id + connection_epoch` 唯一标识。
- 管理端 kick、安全违规关闭、协议严重错误、source/auth_context 伪造、tenant 越界、恶意重复 ACK/NACK/Defer 等场景默认禁止 resume。
- grace period 内的 connection_id 不应视为 active target。

## 8. 身份、权限与安全模型

- 连接鉴权和消息鉴权都必须使用 `ns_backend` IAM；连接建立时的 IAM 鉴权结果由 runtime 保存为 session 权限上下文，并由 runtime 注入 source/auth_context。
- 消息级鉴权支持严格模式和缓存模式；严格模式下每条消息实时调用 `ns_backend` IAM 判定，缓存模式下使用连接权限快照并按 TTL、权限版本或失效事件刷新。
- `ns_runtime` 与 `ns_backend` IAM 的通信可以走 HTTP/RPC 主动调用；这条调用链是 runtime 作为服务端的外部依赖，不是普通客户端接入 runtime 的入站 transport 通道。
- runtime 节点之间的连接使用 `ns_backend` 签发的节点凭证；如果启动时暂时无法获取或刷新节点凭证，可以按配置使用本地缓存凭证进入降级模式。
- 节点凭证、IAM 权限快照和其他安全敏感缓存落盘是否加密由配置控制；默认设计必须保留加密存储选项。
- runtime 节点之间的内部集群事件使用统一 envelope 和同一已认证 runtime transport 通道，但在节点互信建立后只做节点级权限校验，不做普通用户 IAM 消息鉴权。
- 入站消息进入 processor 流水线前必须先做硬校验，包括 JSON 可解析、基础 schema 合法、协议版本兼容、tenant 与 session 匹配、禁止伪造 source/auth_context、明显跨 tenant 越界等。
- 具体操作权限在 processor 流水线中通过通用鉴权 processor 判定，例如能否发送该 message.type、能否路由到 target、能否创建 task、能否控制节点、能否跨 tenant 操作。
- 鉴权失败、伪造身份、伪造 tenant、协议版本不兼容、重复恶意 ACK、超限流、非法 schema 都属于严重错误基础集合；最终是否断开、限流、审计或隔离可叠加配置条件。
- 严重错误默认应记录安全审计并关闭或限制连接；如果连接仍处于可安全回写状态且不会泄露敏感信息，应尽量先返回标准错误 envelope，再按 severity 和策略决定是否断开。
- 审计记录中涉及 payload、身份、权限、token 等敏感信息时，默认必须脱敏或摘要化存储，而不是完整明文落库后只依赖 IAM 控制访问。
- runtime 节点启动时应优先向 `ns_backend` 获取节点凭证、角色授权、配置版本、候选 master 信息和集群策略。
- 当 `ns_backend` 暂时不可用时，runtime 可以使用未过期、未撤销且本地校验通过的缓存节点凭证进入降级模式，但降级模式必须受严格限制。
- 降级模式下允许维持已有低风险连接、保持本地 heartbeat、继续处理不需要控制面重新授权的已受理 delivery、执行本地健康检查和有限恢复扫描。
- 降级模式下禁止执行高风险操作，包括 master 切换、force takeover、emergency isolate、跨 tenant 调度、新配置覆盖、节点恢复确认、强制 replay、跨节点全局协调写入和任何依赖 `ns_backend` 最新授权的管理控制。
- 一旦 `ns_backend` 恢复可用，runtime 必须重新校验节点凭证、角色授权、配置版本、leader lease、fencing_token 和当前 role。
- 本地缓存凭证只能用于短时控制面不可用时的受限启动或受限维持服务，不能作为绕过 `ns_backend` 控制面的长期运行凭证。
- 缓存凭证必须有 TTL、签名校验、权限范围、节点 identity、runtime_id、role scope 和脱敏审计记录。
- TLS/QUIC 握手成功、QUIC connection ID 延续、WebTransport session 恢复或 network path validation 成功都不能替代 `ns_backend` IAM 和 runtime session 鉴权，也不能自动继承已过期或已撤销的权限快照。
- transport adapter 暴露的 peer address、QUIC connection ID、path 信息、ALPN、拥塞状态和证书摘要属于安全敏感或高基数诊断数据；日志和审计必须按统一脱敏、采样和访问控制策略处理。

## 9. Processor 与插件模型

- processor 既表示“处理某类消息的业务处理单元”，也表示“完整消息流水线中的一个处理阶段”；后续实现应允许通用阶段 processor 和 message.type 业务 processor 同时存在。
- 一条 envelope 应先经过通用 processor，例如鉴权、限流/背压、幂等检查、审计、路由预处理，再进入按 message.type 分发的业务 processor。
- 管理控制、健康检查、ACK、NACK、Defer、任务调度、流式消息、集群事件和业务扩展都应以 processor 形式存在，不能绕开流水线。
- processor 扩展机制必须支持 `ns_runtime` 内部轻量插件发现，也支持二开通过继承或注册方式直接定义 processor。
- processor 执行必须支持超时、异常隔离、运行时限制和事件发布；某个 processor 或插件异常不能绕过审计，也不能把核心 delivery 状态留在不可解释的中间状态。
- runtime processor 插件体系不要求与整个项目的其他插件体系统一；但插件必须按 namespace、权限声明和 schema 约束接入。
- 默认只加载本地受信任 processor 插件。外部或租户级不受信任扩展不属于当前强制功能边界，但插件模型应保留未来扩展可能性。当前必须具备加载开关、权限声明、可配置 IAM 鉴权和运行时限制，不强制提供进程、容器或 WASM 级隔离。
- processor/plugin 私有状态默认只能访问自己的状态 namespace；如需跨 namespace 访问核心状态、tenant 状态或其他插件状态，必须声明 capability 并经策略/IAM 允许。
- 管理控制 processor 组必须覆盖 runtime health 查询、节点状态查询、连接状态查询、踢连接、重投/清理 delivery、隔离/恢复节点、master 切换、限流调整、配置热更新和状态快照查询。

## 10. 事件与观测模型

- `ns_runtime` 必须定义内部事件总线，用于连接事件、鉴权事件、路由事件、投递事件、ACK/NACK/Defer 事件、控制事件、集群事件、限流背压事件和指标事件。
- 内部事件总线在单个 runtime 进程内提供订阅能力；需要传播到集群时，事件应包装成统一 envelope，通过 master/sub_node/多 master 机制和同一已认证 runtime transport 通道传播。
- processor 和插件可以订阅内部事件，但事件订阅只能作为扩展和观测机制；订阅者不得通过旁路修改核心状态，除非通过状态存储层授权 namespace 和明确 processor 能力完成。
- 事件总线是旁路通知和扩展机制；核心链路仍采用显式调用和明确状态迁移，避免核心行为变成隐式事件驱动。
- 观测数据可以近实时推送给当前 `ns_backend` 和未来指标系统；指标、健康画像和水位数据可以允许丢失或异步补偿，不进入强一致投递主链路。
- target 投递健康画像以内存实时计算为主，异步持久化和推送；健康画像包括 ACK 延迟、NACK 率、Defer 率、timeout 率、transport send failure、连接/stream 写队列压力、重试成功率、stream 窗口表现和最近趋势。
- event loop 观测至少必须覆盖当前实现类型、loop lag、P95/P99 lag、slow callback 数量、pending task 数量、cancelled task 数量和 executor queue depth，以验证 `uvloop` 与标准 `asyncio` 在真实 workload 下的收益和风险；标准指标名至少预留 `runtime_event_loop_implementation`、`runtime_event_loop_lag_ms`、`runtime_event_loop_lag_p95_ms`、`runtime_event_loop_lag_p99_ms`、`runtime_slow_callback_total`、`runtime_pending_task_count`、`runtime_cancelled_task_total` 和 `runtime_executor_queue_depth`。
- transport 通用观测至少必须覆盖 transport/session 连接数、握手耗时、收发字节、收发失败、关闭原因、backpressure duration、读写队列深度、应用消息大小和 transport capability 分布；标准指标名至少预留 `runtime_transport_connections`、`runtime_transport_handshake_duration_ms`、`runtime_transport_bytes_received_total`、`runtime_transport_bytes_sent_total`、`runtime_transport_receive_errors_total`、`runtime_transport_send_errors_total`、`runtime_transport_close_total`、`runtime_transport_backpressure_duration_ms`、`runtime_transport_read_queue_depth` 和 `runtime_transport_write_queue_depth`。
- QUIC/WebTransport 预留观测至少必须覆盖 RTT/smoothed RTT、packet loss、bytes in flight、congestion window、flow-control blocked duration、active/blocked stream、path migration 尝试/成功/失败、path validation duration、datagram 收发/丢弃和 0-RTT 尝试/拒绝；标准指标名至少预留 `runtime_transport_rtt_ms`、`runtime_transport_smoothed_rtt_ms`、`runtime_transport_packet_loss_ratio`、`runtime_transport_bytes_in_flight`、`runtime_transport_congestion_window_bytes`、`runtime_transport_flow_control_blocked_duration_ms`、`runtime_transport_streams_active`、`runtime_transport_streams_blocked`、`runtime_transport_path_migration_total`、`runtime_transport_path_migration_success_total`、`runtime_transport_path_migration_failed_total`、`runtime_transport_path_validation_duration_ms`、`runtime_transport_datagrams_sent_total`、`runtime_transport_datagrams_received_total`、`runtime_transport_datagrams_dropped_total`、`runtime_transport_zero_rtt_attempt_total` 和 `runtime_transport_zero_rtt_rejected_total`。未启用对应 adapter 时这些指标可以为空或不注册，但指标名称、事件模型和采集接口必须预留。
- 时序指标标签必须限制基数，可以使用 runtime_id、role、transport_type、component_type、受控 tenant scope、close_reason 和 error_code；禁止把 connection_id、session_id、transport_connection_id、path_id、message_id 或 delivery_id 直接作为常规时序指标标签，这些标识只进入 trace、脱敏日志或按需诊断快照。
- event loop 与 transport 指标、路径迁移事件和拥塞画像属于异步可观测数据，不得进入 DeliveryRecord、AckRecord 或控制审计的强一致事务。

## 11. 配置与策略模型

- 配置来源优先使用本地配置文件；`ns_backend` 下发配置覆盖配置文件，并且覆盖后的配置需要支持热更新。
- 生效配置必须保留来源、版本、覆盖关系和生效时间；当 `ns_backend` 下发配置覆盖文件配置时，runtime 应能在审计、RoutingPlan、DeliveryAttempt 或控制记录中追踪当时使用的 config_version/policy_version。
- 热更新默认立即生效，但每个配置项可以声明为立即生效、滚动生效或重启生效；后续实现不能把所有配置都假设为启动期常量。
- 配置热更新通过管理控制 envelope 进入 runtime，由管理控制 processor 调用配置管理层执行；配置管理层负责校验、版本写入、生效方式、回滚、审计和事件发布。
- 配置热更新不能隐式改写已经持久化的 RoutingPlan、DeliveryAttempt、AckRecord、NackRecord 或历史审计；新配置默认只影响后续受理、后续 retry/replay、后续路由计算和策略裁决，是否影响已 queued/ack_waiting 的 delivery 必须由配置项生效语义显式声明。
- 策略引擎作为独立逻辑层集中管理接入、路由、调度、可靠性、顺序、限流、背压、错误严重等级、热更新、鉴权、恢复、重试、过载和隔离策略。
- 当消息的低延迟/高吞吐需求与可靠投递/强一致需求冲突时，默认不做全局单一取舍，而是按 message.type、任务类型、tenant、capability 或可靠性等级配置不同优先级。
- 过载行为必须策略化，至少要能表达 reroute、queue、reject、dead_letter、degrade 和 hybrid；路由层负责策略判断，可靠投递层负责最终发送前水位保护。
- 协议兼容策略、连接收尾/重连策略、ACK 到旧 owner 策略、pause 期间计时策略、no target 重试策略、顺序阻塞策略和恢复扫描策略都必须归入策略引擎统一裁决，而不是散落在各模块内部写死。
- ACK timeout、priority、reliability 等可以由发送方建议，但 runtime 策略拥有最终裁决权，包括最小/最大值、覆盖规则、动态调整和安全限制。
- runtime 节点发现采用混合模式：本地配置文件作为启动兜底、最小灾难恢复入口和完全离线启动依据；`ns_backend` 控制面作为运行期权威。
- `ns_backend` 控制面负责下发 master/sub_node 拓扑、节点角色、节点凭证、配置版本、隔离/恢复状态、master 切换信息和策略覆盖。
- 当 `ns_backend` 暂时不可用时，runtime 可以按本地配置和本地缓存凭证进入受限降级模式；但降级模式不得执行需要全局权威确认的高风险操作。
- 配置热更新必须按配置项声明生效方式，每个配置项至少声明为 `immediate`、`rolling` 或 `restart_required`。
- 配置热更新回滚采用“按配置组回滚”模型。
- runtime 配置必须按职责分组，例如 event_loop、transport、wire_codec、protocol、security、state_store、routing、delivery、worker、pool、tenant_quota、observability、logging、debug 等。
- `event_loop` 配置至少支持 `auto`、`asyncio`、`uvloop`：Linux/Ubuntu 生产环境在 `auto` 下优先使用 `uvloop`，不支持或未安装时允许回退标准 `asyncio` 并告警；显式 `uvloop` 模式初始化失败必须启动失败，不能静默回退；Windows 开发环境默认使用标准 `asyncio`。
- event loop implementation 只能在进程启动阶段选择，属于 `restart_required`；debug、slow callback threshold 等相关配置是否立即生效由具体配置项声明，但不得在运行中替换当前 event loop。
- `transport` 配置必须至少表达 enabled adapters、default/preferred adapter、fallback order、capability negotiation、监听地址、队列与水位、path migration、datagram、0-RTT 和 transport-specific 安全限制。`websocket_tcp` 当前默认启用；`websocket_http3`、`webtransport_http3`、`quic_native` 默认禁用。
- 新增或移除监听 transport 通常属于 `rolling` 或 `restart_required`；transport 优先级和 fallback 顺序通常属于 `rolling`；队列水位和受控 message-type allowlist 可以声明为 `immediate`；0-RTT 默认关闭，启用必须至少按 `restart_required` 和安全高风险配置管理。
- `wire_codec` 当前只能启用 `json.v1`；配置中可以保留 supported/preferred codec 结构，但不得通过配置绕过协议确认直接启用二进制或混合编码。
- 每个配置组必须维护独立的 `group_version`、`effective_at`、`rollback_from_version`、`source`、`policy_version` 和审计记录。
- 配置组之间如果存在强依赖关系，不能独立回滚。
- 多节点配置一致性采用混合模式。
- `ns_backend` 是配置版本、配置来源和策略覆盖的最终权威；active master 负责 runtime 集群内配置生效协调、版本兼容检查、sub_node 状态确认和配置漂移检测。
- sub_node 可以直接从 `ns_backend` 拉取配置，也可以接收 active master 的配置协调消息；但无论配置来源如何，sub_node 都必须向 active master 汇报实际生效的 `config_version`、`policy_version`、各 `config_group_version`、生效时间、失败配置组和回滚状态。
- 多节点配置漂移必须按配置组分级处理，不能简单地把所有配置版本不一致都视为致命错误。
- 对于 event_loop、transport、wire_codec、protocol、security、state_store、fencing、delivery_state_machine、routing_critical、payload_ref_validation、cluster_coordination 等关键配置组，如果 sub_node 与 active master 的生效版本不兼容，应立即禁止该节点作为新路由目标，并按策略进入 degraded、isolated 或 draining。
- 对于 logging、observability、debug、低风险采样比例、非关键指标推送等配置组，如果发生版本漂移，可以先记录告警、指标和审计，不必立即隔离节点。
- 配置漂移恢复采用“自动修复 + 管理确认恢复”模型。
- runtime 节点检测到配置漂移后，应自动尝试从 `ns_backend` 拉取权威配置并重新应用。
- 如果节点曾因关键配置组漂移进入 isolated、degraded、draining 或被禁止作为路由目标，即使自动修复成功，也不得立即自动重新参与路由，必须通过管理控制 envelope 执行恢复确认。

## 12. 路由与调度模型

- 路由与调度层只负责回答“发给谁”和“如何选择目标”，不负责实际写底层 transport、不等待 ACK、不做死信状态机。
- 路由与调度层输出 RoutingPlan；可靠投递层消费 RoutingPlan 并生成 DeliveryRecord，因此 RoutingPlan 与 DeliveryRecord 必须保持职责分离。
- 消息 target 可以明确指定路由/调度策略，例如指定节点、负载均衡、粘滞、broadcast、quorum、all_required、weighted subset 或 no_rebind；如果 target 未指定策略，则使用系统默认策略，但 runtime 策略仍保留最终裁决权。
- RoutingPlan 必须记录完整决策痕迹，包括原始 target、候选目标集合、capability 匹配、tenant/component/identity 过滤、每个候选评分、拒绝原因、最终目标、策略版本、本地命中情况和是否需要 master 查询/转发。
- RoutingPlan 是否强一致持久化由消息类型或策略配置；关键消息可以先强一致持久化 RoutingPlan 再投递，普通低延迟消息可以只在内存或摘要中保留 plan。
- RoutingPlan 在逻辑上不可变；每次重试、重路由或策略变化导致重新决策时，都必须生成新的 plan version，并让 DeliveryAttempt 关联对应 plan version。
- RoutingPlan 的候选、评分和过滤原因是审计数据而不是实时路由权威；后续重试必须重新生成 plan version，不能修改旧 plan 来“修正历史”。
- 目标评分优先由策略引擎统一计算；当策略不可用或配置缺失时，路由层可以使用默认 fallback 评分算法，并在 RoutingPlan 中记录 scorer 来源。
- 当 sub_node 本地可以直接路由到目标时，允许本地或已知拓扑内直接路由；只有本地找不到目标时才向 master 查询或转发，避免所有流量中心化。
- 当本地 miss 且 master 不可用时，默认返回 routing unavailable，并由可靠投递层按策略 retry、等待或 dead letter；默认不使用过期拓扑缓存硬投。
- stale routing cache 只在策略显式允许时使用，且必须包含 TTL、topology epoch/version、tenant 摘要和 capability 摘要校验，并在 RoutingPlan 中标记 used_stale_route。
- 管理控制、安全敏感消息、跨 tenant 风险消息和固定 connection 控制消息默认不应使用 stale routing cache；只有明确配置允许且下游 runtime 会再次校验时才可尝试 stale route。
- fixed `connection_id` 路由必须优先精确寻找连接；如果本地找不到，可以向 master 查询所在 runtime/sub_node；如果仍找不到，不得自动降级成 identity 或 capability 路由，除非 target rebinding 策略明确允许。
- target rebinding 策略至少应能表达 fixed_connection、same_identity_rebind、same_capability_rebind、same_tenant_rebind 和 no_rebind_for_control 等形态；控制类消息默认不应随意换目标。
- 如果目标连接断开但同一 identity 仍有其他连接在线，是否允许改投其他连接必须由 target rebinding 策略决定；一旦执行明确的 target rebinding，应保留 target_history、rebind_count 和 rebind_reason。
- 当路由重试前重新计算目标却找不到任何可用目标时，后续行为必须由策略配置；策略可以选择继续 retry、等待目标上线事件、消耗或不消耗重试预算、fallback 到 master、直接 dead letter 或返回 routing unavailable。
- capability 路由默认只选择一个满足能力的目标；只有 target 或策略明确指定 broadcast、quorum、all_required、weighted subset 或 fanout 时，才允许选择多个目标。
- 会话粘滞不是硬编码行为，而是策略配置项；可以按 source identity、tenant、task group、stream_id、conversation/session_id、capability 或 callback group 维度配置。
- 会话粘滞策略应能表达 prefer previous target、require same target、avoid previous failed target、sticky TTL、以及在 NACK/timeout/defer 达到阈值后解除或反向避让粘滞目标。
- 当目标过载时，路由层负责判断是否换目标、排队、拒绝、死信或降级；可靠投递层在实际发送前仍要做最终水位保护。
- target health score 必须采用分层健康画像模型，至少维护 `connection health`、`identity health`、`component_type health`、`runtime node health`、`tenant health` 五类画像。
- 每层画像都应基于滑动窗口与指数衰减计算，包括 ACK P95/P99、NACK 率、Defer 率、ACK timeout 率、transport send failure、连接/stream 写队列压力、flow-control blocked、path migration 失败、retry 成功率、queue backlog、慢连接表现和最近异常趋势等指标。
- 健康画像只能影响评分、限流、避让、重试节奏和背压策略，不能绕过 IAM、tenant 隔离、payload_ref 校验、owner/fencing 校验或 DeliveryRecord 状态机。

## 13. 可靠投递模型

- 可靠投递层负责执行 RoutingPlan，并维护 DeliveryRecord、DeliveryAttempt、AckRecord、NackRecord、DeferRecord、DeadLetterRecord、MessageDeliverySummary 和 StreamDeliveryState 等投递状态。
- 关键控制消息和任务消息默认应使用可靠投递语义，具备 ACK、重试和持久化投递状态；具体 message.type 是否强制可靠、允许降级为 best-effort 或使用异步记录，必须由可靠性策略配置并保留审计痕迹。
- 一个逻辑消息使用一个 `message_id`；广播、多目标、多连接和跨节点场景下，每个目标或每段投递都生成独立 `delivery_id`，但共享同一个 `message_id`。
- 跨节点投递必须采用父子 delivery 模型；每个 runtime 只对自己实际发送的那一段负责，parent delivery 收到下游 runtime ACK 后即算成功，不等待最终 child delivery ACK。
- DeliveryRecord 强一致持久化是可靠投递底线；RoutingPlan、DeliveryAttempt、MessageDeliverySummary 的一致性等级可以按消息类型和策略配置，但关键消息的 summary 与初始 delivery 需要原子写入。
- 普通消息允许异步记录、摘要记录或采样记录时，只能放宽 RoutingPlan、DeliveryAttempt、普通 summary 或观测数据的记录强度；一旦某条消息声明为可靠投递，DeliveryRecord 和合法 ACK/NACK/Defer 相关原子状态仍不能退化为纯内存成功。
- DeliveryAttempt 对关键消息必须强一致记录，以便审计、重试和排障；普通消息的 DeliveryAttempt 可以异步记录、摘要记录或采样记录，但不能影响 DeliveryRecord 强一致状态。
- `prepared` 表示 delivery 已强一致创建但所属 summary 仍在 initializing 或尚未允许发送；`prepared` 不占 active/inflight 配额，不参与优先级、aging 或抢占，但受 expires_at 和管理取消影响。
- 如果消息在受理阶段已经超过 runtime 裁决后的有效期，或剩余有效期低于策略允许的最小投递窗口，应在受理阶段 rejected 或创建 failed summary，而不是创建必然过期的有效 DeliveryRecord；具体是否保留 rejected summary 由受理策略决定。
- `queued` 表示 delivery 已可发送并等待可靠投递调度器选择发送时机；`queued` 不等于已经进入某个 connection 写队列。
- `sending` 表示正在通过当前 transport adapter 写入完整 runtime envelope；进入 `sending` 时开始计算 ACK deadline，并且 `sending` 必须有可配置写超时，避免慢连接、stream flow control 或卡住的写操作拖垮调度器。
- 写入成功后直接进入 `ack_waiting`，不单独保留 `sent` 状态；如果写入完成时 ack_deadline 已过，是立即超时、给最小宽限还是按写延迟补偿，由策略配置。
- ACK deadline 超时不同于 message/delivery expires_at 过期；默认在消息仍有效且重试预算允许时进入 `retry_scheduled`，预算耗尽时进入 `dead_lettered`，业务有效期已过时进入 `expired`，其他异常结果必须由策略显式裁决并审计。
- transport 写入失败、stream reset、session closed 或 flow-control 超时必须交给策略裁决，策略结果可以是 retry_scheduled、reroute、queue、dead_lettered、expired、cancelled、transfer 或 reject；可靠投递层只执行策略结果并记录 attempt/事件。
- `retry_scheduled` 表示等待下一次重试；它不占 active/inflight 配额，到点后重新调用路由与调度层计算目标并重新进入 queued。
- 重试前重新路由不触发 transferred 语义；普通 retry target refresh 只记录 target_history，只有 ownership 变更、责任转移、目标绑定变更或节点级责任迁移等才使用 transferred。
- `transferred` 是旧 owner 视角下的终态记录；新 owner 复用同一个 delivery_id 继续生命周期，但必须更新 owner_runtime_id、owner_epoch 和 fencing_token。
- DeliveryRecord 需要保存 ownership history；全局当前状态看 current_owner/current_state，历史 owner 的结束状态记录为 transferred，并保留 handoff reason、target、epoch、fencing_token 和时间戳。
- 当 runtime 恢复扫描发现某个 delivery 的 current_owner 不是自己时，只能记录本地审计并跳过恢复，不能尝试重投或更新状态。
- 当 ACK 到达旧 owner 时，旧 owner 不能直接改写 delivery 状态；它应按策略转发给 current owner、返回 owner hint 要求重发、在 fencing 仍有效时接受，或拒绝并只写审计。
- DeliveryRecord 必须包含 current owner 和 fencing 信息；只有 current owner 且持有有效 fencing/lease token 的 worker 才能更新发送、ACK、NACK、Defer、重试、死信、取消或转移状态。
- delivery lease 必须通过状态存储层跨进程可见；worker claim queued delivery 前必须获得 lease，lease 过期后旧 worker 的后续状态更新必须被 fencing 拒绝。
- delivery lease 过期后默认进入 `retry_scheduled`，因为发送结果不确定；如果随后目标发来合法 ACK，允许从 `retry_scheduled` 转为 `acked`。
- delivery lease 过期应记录一次 attempt 异常，并由策略决定是否消耗 message 级重试预算；无论是否消耗预算，都不能直接回到 queued 造成立即重复发送。
- delivery lease 默认采用平衡 profile：`lease TTL = 15s`，`renew interval = 5s`。
- 当同一 delivery 的 lease renew 连续失败超过 `2` 次时，应进入 owner 风险状态，允许 RecoveryWorker 或恢复扫描机制在重新校验 owner、fencing、runtime role、delivery state 和当前 lease 后接管。
- lease 过期不等于 delivery 失败，也不等于目标未收到消息；默认应进入可恢复风险路径，由策略决定进入 `retry_scheduled`、等待恢复扫描、转移 owner 或 dead letter。
- lease renew 连续失败达到策略阈值后，当前 worker 不得继续发起新的高风险状态写入动作，例如继续发送新 envelope、触发 retry、提交 dead letter、执行 owner transfer 或修改主 DeliveryRecord 状态。
- delivery 进入 owner 风险状态后，允许一个短暂保护窗口处理已经在途的 ACK/NACK/Defer。
- owner 风险保护窗口默认采用中等窗口，建议 `3～5s`。
- owner 风险保护窗口不是 lease 延期，也不是新的有效 lease，只是在途确认容错窗口；真正写入权威仍然以 Redis/Valkey 中的 current owner、lease 和 fencing_token 为准。
- ACK、NACK 只允许从 `sending`、`ack_waiting`、`retry_scheduled` 生效；`prepared`、`queued`、`replay_requested`、终态或旧 owner 状态收到 ACK/NACK 时必须按异常、重复或迟到事件审计。
- `dead_lettered` 是唯一默认允许管理端显式 replay 恢复的终态；`acked`、`cancelled`、`expired`、旧 owner 的 `transferred` 默认不可恢复。
- 可靠投递层必须维护投递去重登记；同一 tenant 下相同 `message_id + target_fingerprint` 在去重窗口内重复进入时，应按策略拒绝、复用已有 delivery、合并目标或允许重复，并记录幂等命中事件。
- 投递去重窗口 TTL 完全由 runtime 策略决定，发送方不能指定；如果复用已有已 acked delivery，应返回 `delivery.duplicate/already_delivered` 语义，而不是伪装成一次新的投递成功。
- 如果重复消息命中的是 `queued/sending/ack_waiting/retry_scheduled` 中的已有 delivery，应返回 `duplicate.delivery_in_progress` 或等价状态提示；如果命中 `dead_lettered/expired/cancelled`，不得自动重投，必须按对应终态语义返回或等待管理操作。

## 14. ACK、NACK、Defer 与流式可靠性

- ACK 是一等 envelope 消息，必须完整走 Envelope 协议层、安全硬校验和 processor 流水线；可靠投递层只接受 ACK processor 校验后的 ACK 结果，不允许 ACK 快速通道。
- ACK、NACK、Defer 的发送者必须匹配该 delivery 当前期望的确认方；叶子 delivery 通常只能由目标 connection/session/identity 确认，父 delivery 只能由对应下游 runtime 节点确认，target rebinding 或 ownership transfer 后必须按新 owner/target/fencing 重新校验。
- 第一次合法 ACK 必须写 AckRecord，并与 DeliveryRecord 进入 `acked` 在同一事务或原子操作中完成；重复 ACK 不新增 AckRecord，只写审计/安全事件和指标。
- 如果 delivery 处于 `retry_scheduled` 且收到合法 ACK，可靠投递层必须原子写入 AckRecord、进入 `acked` 并取消对应待重试计划；不能让已 ACK 的 delivery 继续被 retry worker 再次发送。
- ACK timeout scanner 必须只处理仍处于 `ack_waiting` 且 `ack_deadline_at` 已过期的 delivery；如果 message/delivery 已超过 `expires_at`，应进入 `expired`，否则应进入 `retry_scheduled` 并等待后续 retry worker 或策略引擎处理。
- Retry scanner 必须只处理仍处于 `retry_scheduled` 的 delivery；如果 delivery 已超过 `expires_at`，应进入 `expired`，否则应按策略重新创建 DeliveryAttempt 并再次投递给当前 target。retry 不能把完整业务 payload 写入强一致 DeliveryRecord，只能使用 payload_ref 或可重建的 envelope 元数据恢复投递内容；单进程 transient cache 只能作为非权威性能优化，不能作为进程重启、owner transfer 或跨节点恢复时的唯一投递内容来源。
- DeadLetterRecord scanner 必须只登记需要管理端处理或审计的异常终态 delivery；默认只扫描 `dead_lettered`，不扫描 `expired`。`expired` 是自然终态，只表示消息或 delivery 已超过有效期，不再有业务意义，应通过 DeliveryRecord、MessageDeliverySummary 和 snapshot 统计体现，而不是写入 DeadLetterRecord。
- stream cumulative ACK 使用单条范围型 AckRecord 覆盖多个 chunk delivery，并在同一事务中批量更新被覆盖 DeliveryRecord 和 StreamDeliveryState。
- NACK 是一等 envelope 消息，必须强一致写 NackRecord，并与 DeliveryRecord 状态变更原子完成；NACK 不算 ACK，NACK reason 决定 retry、reroute、dead_letter 或安全审计。
- 重复 NACK 不应污染 NackRecord 主记录；重复、迟到或非法 NACK 应进入审计/安全事件，并按策略决定是否限流、断连或降低目标健康评分。
- 如果 NACK reason 是 target overloaded、temporarily unavailable、queue full 或 dependency unavailable，应默认倾向 retry/reroute 并降低 target health score；如果 reason 是 permission denied、tenant mismatch、invalid payload reference 等，应默认 dead letter 或安全审计。
- retryable NACK 默认消耗 message 级重试预算；non-retryable NACK 直接进入 dead_lettered 或安全审计，预算耗尽时未完成 delivery 进入 dead_lettered。
- 如果 delivery 因 NACK 进入 `retry_scheduled` 后又收到合法 ACK，可以转为 `acked` 并取消后续重试；如果 NACK 已导致 `dead_lettered`，后续 ACK 按终态迟到 ACK 忽略并审计。
- `delivery.defer` 必须支持，并作为一等 envelope 通过协议层、安全层和 processor；合法 Defer 不新增主状态，而是保持或回到 `ack_waiting` 并延长 ack_deadline。
- DeferRecord 必须强一致写入，并与 ack_deadline 更新原子完成；Defer 允许从 `sending`、`ack_waiting`、`retry_scheduled` 生效，其中 `retry_scheduled` 收到合法 Defer 后直接回到 `ack_waiting`。
- Defer 必须有独立 defer budget，包括最大次数、最大总延长时间和单次最大延长；超过 defer budget 时立即按 ACK timeout 处理，并把频繁 defer 作为目标压力信号反馈给健康画像。
- Defer 默认不释放 inflight，也不算 ACK；它是否消耗 retry budget 由策略决定，但无论是否消耗 retry budget，都必须受独立 defer budget 约束。
- 重复、迟到、旧 owner、旧 connection_epoch 或超过预算的 Defer 不得继续延长 ack_deadline；应按重复/迟到控制消息进入审计、安全计数和目标健康画像，并由策略决定是否限流或断开。
- 当 delivery 或 message 处于 hold 时，ACK/NACK 的处理方式由策略配置，可以缓存为 PendingAckRecord/PendingNackRecord、拒绝并提示稍后重发，或只审计忽略；pending 记录必须强一致持久化。
- 当 delivery 或 message 处于 hold 时，收到合法 ACK/NACK 也不能立即把主 DeliveryRecord 更新为 `acked` 或 retry/dead_letter；只有解除 hold 后按策略重新校验 owner/fencing/current state 才能提交或丢弃 pending 记录。
- PendingAckRecord 或 PendingNackRecord 在解除 hold 后成功提交为正式 AckRecord/NackRecord 时，应删除 pending 记录并写迁移审计；如果因状态已终态、owner 变更或校验失败而丢弃，也应删除 pending 记录并写 discarded 审计。
- PendingAckRecord/PendingNackRecord 必须具备 TTL 或过期策略；解除 hold 后处理 pending 记录时必须再次校验 tenant、source、target、owner、fencing 和当前 DeliveryRecord 状态。
- 可靠流式消息必须支持 stream_start、stream_chunk、stream_end 和分片级 delivery；stream_end 必须作为可靠 envelope 并在 ACK 后 stream 才能进入 closed。
- StreamDeliveryState 至少应能表达 opening、active、closing、closed、failed、cancelled、expired；stream_end 已发送但未 ACK 时处于 closing，只有 stream_end ACK 后才能 closed。
- stream_start 是严格等待 ACK 后再发分片，还是 optimistic start 一边等 start ACK 一边发送窗口内分片，由策略配置；stream_end 不应 optimistic，默认必须 ACK 后 closed。
- reliable stream 必须支持滑动窗口 ACK；每个 chunk 有独立 delivery_id，stream 使用 cumulative ACK，其中 `ack_sequence=100` 表示同一 stream_id 下 sequence <= 100 的分片连续收到。
- stream cumulative ACK 必须按 stream_id 和确认方单调推进；小于或等于已确认 sequence 的 ACK 只作为重复或迟到事件处理，不能回退 StreamDeliveryState，也不能重新打开已关闭或已失败的 stream。
- stream ACK 协议必须支持 `ack_ranges`、`missing_sequences`、`received_sequences` 等 selective ACK 字段，并与 cumulative ACK、乱序恢复和重试状态保持一致。
- stream window 只能由 runtime 策略决定；接收方不能主动通过 extend_window 扩大窗口，但 ACK/NACK/Defer/延迟等信号可以影响后续策略计算。
- 开启强顺序保证时，必须等前一条 delivery ACK 后才发送下一条；如果前序 delivery dead_lettered、expired 或 cancelled，后续是阻塞、跳过、取消还是死信，由顺序策略配置。
- 顺序保证范围必须由策略配置，可以按 stream_id、source-target、connection、tenant、message_type 或其他受控范围设置；严格顺序流如果要求前一分片 ACK 后再发下一分片，stream window 应等价收敛为 1。
- ACK timeout 默认采用平衡 profile：本地 delivery ACK timeout 默认 `5s`，跨节点 delivery ACK timeout 默认 `10s`。
- ACK timeout 到期不等于业务失败，也不等于目标一定未收到 envelope；timeout 只能说明 runtime 未在规定窗口内收到合法 ACK。
- Defer 默认采用平衡限制策略：每个 delivery 默认最多允许 Defer `3` 次；单次 Defer 最多延长 `5s`；总延长时间默认不超过 `15s`。
- Defer 是目标压力信号，频繁 Defer 必须进入 target health profile，用于后续路由评分、限流、背压和是否避让该目标。
- NACK 默认采用平衡策略，NACK reason 必须按语义分为 `retryable`、`reroutable`、`non_retryable`、`security` 四类。
- 对于 `target_overloaded`、`temporarily_unavailable`、`queue_full`、`dependency_unavailable`、`target_draining`、`node_degraded` 等临时性或容量类原因，默认进入 `retry_scheduled`、`reroute` 或降低 target health score。
- 对于 `permission_denied`、`tenant_mismatch`、`invalid_payload_ref`、`payload_ref_denied`、`source_forged`、`auth_context_forged`、`protocol_violation` 等权限、安全或协议类原因，默认进入 `dead_lettered`、`rejected` 或安全审计，不应反复 retry.
- 所有 NACK reason 必须进入细粒度 `RUNTIME_*` 错误码体系，并定义在 `ns_common.exceptions` 中。
- 可靠 stream 必须实现完整可靠语义，而不是只注册协议或基础 processor。
- 必须支持 `stream.start`、`stream.chunk`、`stream.end`、分片级 delivery、滑动窗口、cumulative ACK、selective ACK、`ack_ranges`、`missing_sequences`、乱序恢复、窗口动态调整、stream hold/cancel/replay 链路，并遵守本文档对 hold、cancel、replay、DeliveryRecord 和 StreamDeliveryState 已明确规定的语义；`stream_end` 被 ACK 后 stream 才能进入 `closed`。
- stream 的可靠性必须建立在统一 Envelope、DeliveryRecord、ACK/NACK/Defer、StreamDeliveryState、状态存储层、策略引擎和 processor 流水线之上。
- 不允许为 stream 另开私有传输通道、私有 ACK 通道或绕过可靠投递层。
- stream 可以限制最大窗口、最大分片大小、最大 stream 生命周期、最大乱序缓存范围和最大并发 stream 数，但这些限制必须策略化，不能写死在 processor 或 transport 层。
- stream 的分片 ACK、cumulative ACK 和 selective ACK 不能直接更新内存状态后异步补写 Redis/Valkey。
- 凡是会影响 StreamDeliveryState、chunk DeliveryRecord、ack window、missing ranges、retry、dead letter 或 stream closed 状态的操作，都必须通过状态存储层原子更新，并写入状态变更日志或审计摘要。

## 15. 重试、死信、重投、取消与 hold

- 可靠投递必须支持至少一次投递和尽量接近 exactly-once 两种可靠性目标；接近 exactly-once 必须依赖接入方基于 message_id/delivery_id 实现幂等确认和去重。
- 同一个 message_id 下的多个 delivery 共享 message 级自动重试预算；每个 delivery 仍记录自己的 attempt_count、last_error、next_retry_at 和状态。
- 重试 backoff 必须策略可插拔，至少允许固定间隔、指数退避、带抖动、优先级感知、tenant 负载感知、目标健康感知和 manual-only 等策略形态。
- 自动 retry 是可靠投递层内部的状态迁移和重新调度，不应伪造成发送方重新提交的一条入站 envelope，也不应重新进入普通业务 processor；但 retry 前仍必须按策略重新计算路由、优先级、水位、payload_ref 校验和必要的安全约束。
- 目标上线、connection 恢复、node 恢复、capability 注册、tenant 解除暂停、isolation 解除、存储恢复或 master 切换完成等事件可以提前唤醒 retry_scheduled delivery，但提前唤醒必须受 tenant/global/recovery pool 限制和策略预算控制。
- retry_scheduled 到点或被事件提前唤醒后进入 queued 时，必须重新由策略引擎计算 priority、目标、pool 和水位许可，不能沿用首次投递时的优先级和目标评分。
- 管理端可以临时提升、降低或冻结某个 message 或 tenant 的 retry budget，但预算调整只影响尚未终态的 retry_scheduled/queued/ack_waiting 后续行为，不能自动复活 dead_lettered。
- 当 message 级自动重试预算耗尽时，未完成 delivery 默认进入 `dead_lettered`，而不是 `expired`；`expired` 只表示消息或 delivery 明确过了有效期，不再有业务意义。
- `expired` 是自然终态，不写 DeadLetterRecord；`dead_lettered` 是异常终态，表示消息仍可能有业务意义但自动投递已停止，需要管理端处理或审计。
- 死信是否允许管理端重投必须根据 dead letter reason 判断；ACK 超时、目标暂时离线、节点过载等可以 replay，鉴权失败、tenant/source 伪造、payload 明确无效等不能直接 replay。
- Dead letter reason 至少应区分可重投、不可重投和需要人工确认三类；重复恶意 ACK、跨 tenant 尝试、fencing 异常、ownership 冲突、processor 插件异常等应默认进入人工确认或安全审计路径。
- DeadLetterRecord 应保留 reason、last_error、attempt_count、budget_exhausted、route_segment、last_owner_runtime_id、replayable 和 recommended_action 等摘要，以便管理端判断可重投、不可重投或需要人工确认。
- 管理端重投死信时复用原 message_id 和 delivery_id，但必须创建新的 replay_epoch，记录 replay_count、replay_budget、last_replayed_by、replay_reason 和 previous_dead_letter_reason。
- 自动重试预算和人工 replay 预算必须拆开；replay 不清零历史自动重试消耗，而是在新的 replay_epoch 内使用独立 replay budget。
- 一个 message 同一时间只能创建一个 replay_epoch，但该 epoch 内多个指定 dead_lettered delivery 可以并行进入 `replay_requested -> queued`，并受 recovery pool 和 tenant 限流控制。
- `replay_requested` 是管理端 replay 已受理但尚未重新进入发送调度的中间态；它不发送、不接受 ACK/NACK 生效、不占 active/inflight，必须在重新校验 replayability、payload_ref、owner/fencing、tenant 策略和 recovery pool 后才能进入 `queued`。
- 管理端重投必须显式指定要重投的 dead_lettered delivery，支持批量和 partial success；可重投的继续，不可重投的返回明细，响应包含 accepted_delivery_ids、accepted_count 和 replay_epoch。
- 超过最大 replay_count 后，该 dead_lettered delivery 必须完全禁止重投，即使操作者具备更高管理 capability 也不能强制复活。
- 普通未完成 delivery 不允许管理端手动重投；`ack_waiting`、`queued`、`sending`、`retry_scheduled` 只能等待正常 ACK、timeout、自动 retry、取消或策略处理。
- 管理端可以取消 `prepared`、`queued`、`sending`、`ack_waiting`、`retry_scheduled`、`replay_requested` 的 delivery；不能取消 `acked`、`dead_lettered`、`expired`、`cancelled` 或旧 owner 的 `transferred`。
- 当 `sending` 状态被取消时，只标记 cancel_requested，不强行打断底层 transport 写操作；写操作返回后再根据 cancel_requested 进入 `cancelled` 或按策略处理。
- 取消会释放 active、inflight、queued、recovery pool、stream window 等资源占用，但不会回退 attempt_count、retry_used、total_attempt_count、audit records 等历史消耗。
- `acked`、`expired`、`dead_lettered`、`cancelled` 都必须释放 active、inflight、queued、stream window 等运行时资源占用；`retry_scheduled` 释放 active/inflight 但保留 retry backlog 和 pending 统计。
- `cancelled` 不计入失败类计数；如果一个 message 部分 acked、部分 cancelled 且没有失败类，summary 为 `partial_acked`；如果全部 cancelled，summary 为 `cancelled`。
- 如果一个 message 部分 cancelled、部分 pending，且没有 acked 或失败类，summary 仍应保持 `pending`，因为取消不等于失败也不等于成功。
- delivery hold 必须作为状态字段/标记存在，而不是主状态；hold 只能由管理 capability 发起，可以作用于单个 delivery、批量 delivery 或整个 message summary。
- hold 期间暂停 ACK timeout、expires_at、自动 retry、自动 dead letter、prepared 激活和 queued 发送；解除 message hold 后，pending ACK/NACK 应按 tenant/message 分批处理。
- message 级 hold 默认作用于该 message 下所有未终态 delivery，并且后续同一 message 的 replay_requested、自动恢复、prepared 激活和 queued 发送都必须继承 hold；只有策略明确允许并经管理 capability 授权时，才能对特定 delivery 做例外释放。
- 投递暂停/恢复必须支持；暂停期间新普通消息默认返回错误 envelope，已有 queued delivery 保留但不发送，ACK/NACK/Defer 和管理控制继续处理，计时行为由 pause 策略决定。
- `prepared`、`queued`、`retry_scheduled` 和 `ack_waiting` 在暂停、hold、draining、transitioning、isolation 等运行状态下的计时、激活和重试行为必须由策略或硬规则明确，不能靠实现时的默认队列行为隐式决定。
- retry budget 默认采用平衡预算，每个 message 默认最多自动 retry `5` 次。
- `retryable NACK`、`ACK timeout`、transport 写失败或 stream reset、目标连接写队列满、目标 runtime 暂时不可达等明确投递失败或接收失败场景，默认消耗自动 retry budget。
- 对于 target 暂时离线、master 暂不可用、payload_ref 校验服务暂不可用、tenant 暂停、node transitioning、runtime draining 等基础设施或运行状态类问题，可以按策略进入 wait、retry_scheduled、deferred retry 或 dead letter，不一定立即消耗 retry budget。
- 自动 retry budget 与人工 replay budget 必须拆开。
- retry backoff 默认采用“指数退避 + jitter + 目标健康感知”的混合策略。
- 基础退避曲线采用指数退避，例如 `1s -> 2s -> 4s -> 8s -> 16s`，并加入随机 jitter。
- runtime 必须结合 target health score、tenant backlog、runtime 全局水位、connection 写队列压力、NACK reason、route segment、message priority 和 reliability 等因素动态调整 retry 间隔。
- DeadLetterRecord 必须采用分级 replay 策略，dead letter reason 至少分为 `replayable`、`not_replayable`、`manual_confirm_required` 三类。
- 临时投递失败默认归为 `replayable`；安全、权限、tenant 或 payload 明确无效问题默认归为 `not_replayable`；fencing 冲突、owner 异常、processor 异常、状态机异常默认归为 `manual_confirm_required`。
- 每个 `dead_lettered` delivery 默认最多允许人工 replay `3` 次。
- 每次 replay 都必须创建新的 `replay_epoch`，并记录 `replay_count`、`replay_budget`、`last_replayed_by`、`replay_reason`、`previous_dead_letter_reason`、`policy_version` 和 `replay_started_at`。
- replay 不得清零历史 `attempt_count`、`retry_used`、`dead_letter_reason` 或审计记录。
- dead letter replay 采用 message 内有限并发模型：同一个 `message_id` 同一时间只能存在一个 active `replay_epoch`。
- 在同一个 `replay_epoch` 内，可以允许多个符合 replay 条件的 `dead_lettered` delivery 并行进入 `replay_requested -> queued`，但必须受 recovery pool、tenant 配额、target health score、runtime 全局水位、Redis/Valkey queue backlog、replay budget 和 system pool 保护。
- replay 受理必须支持 partial success。

## 16. MessageDeliverySummary 与受理响应

- MessageDeliverySummary 由可靠投递层维护，用于聚合同一个 message_id 下所有 delivery、rejected target、cancelled、expired、dead_lettered 和 acked 的整体状态。
- MessageDeliverySummary 应保留 target_count、accepted_count、rejected_count、delivery_count、acked_count、dead_lettered_count、expired_count、cancelled_count、pending_count、prepared_count、queued_count 等关键计数，以便管理端无需扫描全部 delivery 也能判断整体状态。
- 受理阶段如果全部目标都 rejected，也必须创建 MessageDeliverySummary，以便管理端能够查询这条 message 为什么没有产生有效 delivery。
- 受理阶段的 `rejected` 不是 DeliveryRecord 状态；如果 payload reference 明确无效、越权或 tenant 不匹配，应直接 rejected、不创建 DeliveryRecord，但写 summary 计数和审计。
- 关键消息的 MessageDeliverySummary 和初始 DeliveryRecord 应尽量原子写入；当目标数量巨大导致单事务过重时，允许 summary 先进入 `initializing`，再分批写入 `prepared` delivery。
- summary `initializing` 期间，已创建的 delivery 不允许发送；必须等所有初始 DeliveryRecord 创建完成后，summary 进入 `pending`，然后再分批激活 `prepared -> queued`。
- `prepared -> queued` 激活必须按 tenant、priority、connection/target 水位、runtime 全局水位和批大小分批执行，避免大规模初始化完成后瞬间打满发送队列。
- 如果 summary 初始化失败，已 `prepared` 的 delivery 直接 `cancelled` 并审计；未创建 delivery 的目标只记录在 summary 的失败或 not_initialized 计数中，不补建无意义 delivery。
- 如果管理端在 initializing 期间取消整条 message，已 prepared delivery 批量取消，未创建目标只记录 `not_initialized_count`，不为了完整记录而补建大量 delivery。
- summary 不单独增加 `activating` 状态；初始化完成后保持 `pending`，通过 prepared_count、queued_count、ack_waiting_count、acked_count 等计数表达激活进度。
- summary 聚合状态保持简洁，支持 `initializing`、`pending`、`partial_acked`、`all_acked`、`partial_failed`、`failed`、`cancelled`；rejected 和 expired 统一归入失败类聚合，不单独增加 `partial_rejected`。
- 如果 message 的所有目标都在受理阶段 rejected，summary 应创建并进入 `failed`；如果部分 rejected 且部分 delivery 后续 acked/failed/cancelled，则按目标策略聚合为 `partial_failed`、`partial_acked` 或其他既定状态。
- Summary 聚合时，全部 acked 才能进入 `all_acked`，全部取消才进入 `cancelled`，全部失败类终态才进入 `failed`，既有成功又有失败类终态时进入 `partial_failed`，既有成功又有 pending/cancelled 且无失败类时进入 `partial_acked`。
- 多目标消息中哪些目标是 required、optional、weighted、quorum、all_required、any_one 或 best_effort 必须由策略配置；summary 聚合时按目标策略决定整体状态。
- 发送方可以收到 best-effort 的 `delivery.accepted`、`delivery.rejected`、`delivery.duplicate` 等受理响应，但这些响应不保证一定到达发送方，也不作为可靠投递成功依据。
- 只要 runtime 已完成受理并创建 summary/delivery 或 rejected summary，发送方连接随后断开不应回滚已受理结果；后续 delivery 生命周期继续由可靠投递层、策略和管理端驱动，受理响应发送失败只写审计或指标。
- `delivery.accepted` 响应只返回 message_id、summary_id、accepted_at、status_query_hint 和 trace 等轻量信息，不返回大量 delivery_id 列表；详细 delivery 信息只能由具备管理 capability 的连接查询。
- 普通发送方或无管理 capability 的连接请求查询 delivery detail、delivery tree、dead letter 或其他管理状态时，必须返回授权失败错误 envelope 并审计，不能泄露目标连接、路由路径、其他 tenant 或内部 owner/fencing 信息。
- MessageDeliverySummary 默认采用单 message 单 bucket 聚合模型；普通 message 的 summary、delivery、ACK/NACK/Defer、retry/timeout 索引和状态日志应尽量落在同一个 `tenant + bucket` 中。
- 只有当 message 的目标数量、fanout 规模、单 bucket 热点风险或单次初始化成本超过策略阈值时，才允许拆分为多个 bucket，并创建 root summary 与 shard summary。
- shard summary 负责 bucket 内 delivery 计数和状态聚合，root summary 负责跨 shard 的整体状态汇总。
- fanout 拆分采用“内置保守默认值 + 配置覆盖”的方式。
- fanout 默认阈值采用平衡 profile：超过 `5,000` 个 targets 时触发 fanout 分片；每个 bucket 最多承载 `1,000` 个 delivery；summary 初始化批次默认为 `500`；`prepared -> queued` 激活批次默认为 `200`。
- fanout 分片阈值、bucket 目标数、summary 初始化批次和 prepared 激活批次必须由策略引擎统一裁决；路由层、可靠投递层、状态存储层不得各自读取不同配置或写死不同默认值。

## 17. Payload Reference 校验

- 首次投递、死信重投、自动恢复重投和 target rebinding 后目标访问权限可能变化时，都必须实时调用 `ns_backend` 校验 payload object reference。
- payload reference 校验必须确认 object 存在、version/checksum 匹配、owner/tenant 匹配、未过期、未撤销、发送方有权引用、目标有权访问，以及 callback 引用仍有效。
- 如果 payload reference 明确无效、tenant 不匹配、checksum/version 不匹配、发送方无权引用、目标无权访问或对象已撤销，应直接 rejected，不创建有效 DeliveryRecord，并写安全审计。
- 如果 payload reference 实时校验因 `ns_backend` 暂时不可用、校验服务超时或依赖异常而无法完成，关键消息应进入 `dead_lettered`，而不是继续投递或依赖缓存。
- 普通消息在 payload reference 校验服务不可用时的处理方式可以策略化，但不能绕过校验后继续当作已安全消息投递；策略只能在 reject、dead_letter、retry/wait 或降级拒绝之间选择。
- payload reference 校验结果可以用于观测或短期诊断缓存，但不能作为后续投递授权依据；每次需要安全确认的投递/重投必须实时校验。
- `payload_ref` 校验必须采用分级策略。
- 当 `payload_ref` 被 `ns_backend` 明确判定为无效、对象不存在、version/checksum 不匹配、tenant 不匹配、owner 不匹配、发送方无权引用、目标无权访问、对象已过期或已撤销时，runtime 必须直接 `rejected` 或进入不可继续投递的 `dead_lettered`，并写入安全审计。
- 当 `payload_ref` 校验服务暂时不可用、超时、`ns_backend` 依赖异常或返回不确定结果时，runtime 不得绕过校验继续投递。
- 关键消息可以按策略进入 `dead_lettered`、`wait` 或 `retry_scheduled`；普通消息可以按策略选择 `reject`、`wait` 或 `dead_letter`。
- 只要 payload_ref 需要安全确认，就不能使用过期缓存、诊断缓存或观测缓存作为投递授权依据。
- payload_ref 校验异常必须进入细粒度 `RUNTIME_*` 错误码体系，例如 `RUNTIME_PAYLOAD_REF_INVALID`、`RUNTIME_PAYLOAD_REF_DENIED`、`RUNTIME_PAYLOAD_REF_EXPIRED`、`RUNTIME_PAYLOAD_REF_CHECKSUM_MISMATCH`、`RUNTIME_PAYLOAD_REF_VALIDATION_UNAVAILABLE`、`RUNTIME_PAYLOAD_REF_VALIDATION_TIMEOUT`。

## 18. 优先级、公平调度与背压

- 可靠投递层必须有优先级调度队列；ACK/控制收尾、管理控制、集群协调、关键任务、普通业务、低优先级观测/流式数据应有不同优先级类别。
- 系统级 ACK、管理控制、集群协调和健康相关消息必须走独立 system pool 或保留容量，不参与普通 tenant pool 的配额竞争。
- 普通业务和任务消息进入 tenant pool，并按 tenant 权重、tenant inflight、tenant 队列、tenant retry budget 和公平调度策略分配发送能力。
- 单连接读/写队列只是第一道本地流控；通过协议和安全硬校验后的消息还必须进入 tenant 级共享队列和 runtime 全局队列/水位体系，才能形成 tenant 隔离、全局背压和系统保留容量的组合约束。
- 自动重试、死信重投和启动恢复重投进入 recovery/retry pool；该 pool 严格固定比例，不能在系统空闲时借用 tenant pool，以免恢复流量吞掉实时业务容量。
- observability pool 用于指标和观测推送，低优先级且可降级；观测推送不能影响 ACK、控制、集群协调和关键业务投递。
- tenant pool 内允许高优先级业务消息抢占低优先级业务消息，但抢占只影响 `queued` 等尚未发送的队列阶段，不打断 `sending`，不取消或暂停 `ack_waiting`。
- priority aging 必须支持，以避免低优先级业务长期饥饿；但 aging 不允许把普通业务提升到 ACK、管理控制或集群协调级别。
- priority aging 是否在 pause、hold、draining 或 retry_scheduled 期间累计等待时间必须由策略配置；`prepared` 默认不参与发送队列 aging，只有进入 `queued` 后才参与。
- tenant 公平调度应允许 weighted round-robin、deficit round-robin、tenant 权重、burst 上限和 reserved capacity 等策略形态，但任何策略都不能突破 system pool 的保留容量。
- 连接、tenant 和 runtime 全局都必须有背压水位；连接层负责实际入队/拒绝/关闭动作，策略引擎负责判断软过载、硬过载和错误等级。
- 队列满或过载时应尽量返回标准错误 envelope；只有内存危险、写队列无法发送错误、帧过大、恶意刷流量或严重安全错误时，才允许直接断开并审计。
- `prepared -> queued` 激活调度采用“优先级 + 水位混合驱动”模型。
- `prepared` delivery 不得一次性全部进入 `queued`，而应按 `message.priority`、tenant fair share、target health score、delivery age、message.type 可靠性等级和策略版本排序，再结合 runtime 全局水位、tenant 水位、target/connection 水位、Redis/Valkey queue backlog、recovery pool 和管理控制优先级分批激活。
- 每一次 `prepared -> queued` 批量迁移都必须记录策略版本、批次大小、候选数量、实际激活数量、跳过原因和水位判断摘要。
- delivery worker 并发模型采用“固定底座 + 动态扩展”。
- runtime 启动时必须按配置创建基础 worker，分别保障 `claim`、`send`、`ACK timeout`、`retry`、`recovery`、`lease renew`、`system pool` 等关键链路的最低处理能力。
- 当 ready queue backlog、ACK timeout 数量、retry backlog、recovery backlog、Redis/Valkey 延迟、连接写队列压力或 system pool backlog 上升时，runtime 可以在配置上限内临时扩展 worker。
- worker 扩缩容只能改变调度并发，不得改变 DeliveryRecord 状态机语义。
- delivery worker 必须按职责拆分，至少拆分为 `ClaimWorker`、`SendWorker`、`AckTimeoutWorker`、`RetryWorker`、`RecoveryWorker`、`LeaseRenewWorker`、`SystemControlWorker`。
- worker 之间通过状态存储层、调度队列、事件总线和明确状态机迁移协作，而不是互相直接调用内部实现。
- worker 协作采用“Redis/Valkey 队列与状态存储为权威，进程内事件总线仅做加速唤醒”的模型。
- 进程内事件总线只作为加速信号，不作为状态权威；事件丢失不得导致状态机不可恢复。
- 每次被事件唤醒后，worker 仍必须重新从 Redis/Valkey 读取当前状态，校验 owner、lease、fencing、connection_epoch、policy_version 和 DeliveryRecord 当前状态。
- worker 唤醒采用“事件唤醒优先，周期扫描兜底”的模型。
- 每类 worker 都必须保留 Redis/Valkey 队列、ZSet deadline、retry index、ack deadline index、recovery index 和状态异常索引的低频周期扫描能力。
- worker 周期扫描频率采用平衡 profile：普通队列兜底扫描 `1～2s`；ACK timeout 扫描 `500ms～1s`；lease renew 检查 `300～500ms`；retry due 扫描 `1s`；recovery 扫描 `5～10s`。
- 扫描频率必须作为策略配置项，并纳入 `config_version/policy_version` 管理，不能在 worker 类中各自写死。
- tenant 公平调度采用“硬配额 + 加权公平队列”的混合模型。
- 每个 tenant 必须具备硬性安全配额，包括 `max_active_delivery`、`max_queued_delivery`、`max_inflight_delivery`、`max_retry_backlog`、`max_activation_per_second`、`max_write_queue_pressure` 等。
- 在未触达硬配额的前提下，tenant pool 内使用 Weighted Fair Queuing 或 Deficit Round Robin 按 tenant weight 分配激活与发送机会。
- 系统级 ACK、管理控制、集群协调和健康相关消息不参与普通 tenant pool 配额竞争，可以使用 system pool 或保留容量，但仍必须受 runtime 全局安全水位保护。
- system pool 采用“固定保留底线 + 动态上浮”的容量策略。
- system pool 默认建议保留 `15%` 的调度能力、发送能力和关键队列预算。
- 当出现 ACK backlog 上升、ACK timeout 增多、cluster heartbeat 延迟、control backlog 堆积、leader lease renew 接近超时、节点切换或恢复扫描压力升高时，system pool 可以按策略临时上浮，最高建议上浮到 `30%`。
- system pool 内部必须采用分级优先级模型：最高级保护 leader lease renew、fencing、节点隔离/切换、安全关闭；第二级保护 ACK/NACK/Defer 和 ACK deadline；第三级用于 health、节点状态、连接状态、delivery 状态查询；第四级用于普通配置热更新、低风险控制命令和低优先级观测。
- recovery pool 采用“固定保留底线 + 动态上浮”的容量策略，默认保留总调度能力的 `10%` 左右，必要时可上浮到 `20%～30%`。
- recovery pool 不得挤占最高优先级 system pool，也不得无限挤压普通 tenant pool。
- recovery pool 内部采用分级优先级模型：最高级处理 lease 失效、owner 风险、旧 owner fencing、current owner 不可用；第二级处理节点恢复后的 delivery recovery scan 和 ack_waiting 风险 delivery；第三级处理人工 replay；第四级处理 dead letter 清理、历史状态归档和低优先级恢复统计。

## 19. 集群协调模型

- 集群采用单 active master、多 standby master；任意时刻只有一个 active master 持有有效 leader lease 并负责全局协调。
- master 选主由 `ns_runtime` 自己完成；sub_node 成员管理由 `ns_backend` 或配置作为控制面决定接入哪个 master。
- 生产选主和集群协调依赖 Redis/Valkey；开发模式必须支持 SQLite WAL，并允许本机多进程模拟集群，但 SQLite WAL 不作为生产分布式协调权威。
- leader 权威来自状态存储层的 lease/lock、epoch/term 和 fencing_token；transport liveness 与 envelope heartbeat 只作为健康和拓扑辅助信号，不能单独决定谁是 active master。
- leader lease 语义至少需要包含 leader_lease key、epoch/term、fencing_token、lease TTL、renewal deadline 和 takeover grace period；所有全局协调写入都必须携带或校验当前有效 fencing_token。
- active master 必须定期续约 leader lease；续约失败后必须立即停止全局协调写入，进入 transitioning、standby 或 degraded 状态，并依赖 fencing 防止 split-brain。
- standby master 不主动抢占正常 active；只有检测到 active lease 过期、管理端发起切换或紧急隔离时，才允许竞争 leader lease。
- 管理端发起 master 切换时可以选择 graceful handoff、force takeover 或 emergency isolate，但最终都必须通过 lease、epoch 和 fencing 保证合法，而不是只依赖控制消息。
- sub_node 只连接 active master；active 不可用时，sub_node 根据配置或 `ns_backend` 控制面重新发现并连接新的 active master，不向 standby 发送普通路由流量。
- runtime 节点间连接也必须使用 `connection.hello`，component_type 为 `runtime`，token 使用 `ns_backend` 签发的节点凭证。
- 集群事件不要求全局有序，只要求同一事件主题、同一 node、同一 delivery tree、同一 stream 或其他策略范围内有序。
- 会改变 leader、节点隔离、成员关系、配置版本、owner/fencing 或 delivery tree 的集群控制消息必须按关键控制消息处理，具备可靠投递、强审计和必要的强一致状态更新；普通健康、观测或拓扑提示类集群事件是否可靠由策略配置。
- 节点健康状态由 transport liveness/path 状态、envelope heartbeat、leader/node lease、NACK/defer/timeout/write failure、管理隔离、存储状态、IAM 凭证状态和版本兼容状态共同计算，由策略引擎输出 healthy、degraded、isolated 或 unavailable。
- 网络分区时，如果父 delivery 已经 ACK 下一跳，父状态不回滚；delivery tree 查询下游 child 状态不可达时显示 unknown/unreachable，并把断点定位在下游 runtime。
- master 选举采用混合模型：`ns_backend` 提供候选 master、节点凭证、节点优先级、切换授权和控制面策略；Redis/Valkey 负责 `leader lease`、`epoch/term`、`fencing_token` 和原子抢占。
- 只有同时满足 `ns_backend` 控制面授权、节点凭证有效、角色状态允许、Redis/Valkey leader lease 抢占成功、持有当前有效 fencing_token 的 runtime 节点，才能进入 `active_master` 状态并执行全局协调写入。
- `ns_backend` 的授权不是 active master 的最终运行期写入权威；Redis/Valkey lease 也不是绕过控制面的选主许可，二者必须同时成立。
- master 切换必须支持 `graceful handoff`、`force takeover`、`emergency isolate` 三种模式，并按风险等级分级授权。
- `graceful handoff` 用于正常维护、滚动发布和计划内主节点切换，可由具备普通集群管理 capability 的管理连接发起。
- `force takeover` 用于 active master 不响应、leader lease 过期、节点健康失败或集群协调中断等场景，必须要求高级管理 capability，并重新校验 active master 状态、leader lease、epoch/term、fencing_token、Redis/Valkey 连通性和 `ns_backend` 授权。
- `emergency isolate` 用于 suspected split-brain、旧 owner 持续写入、关键配置漂移、fencing 异常、跨 tenant 风险或安全事故，只允许最高级安全/运维 capability 发起，并必须强审计。
- master 切换不能只依赖 transport 断开、心跳/path validation 失败或管理端命令；任何 active master 变更都必须通过 Redis/Valkey 的 leader lease、epoch/term 和 fencing_token 原子确认。

## 20. 状态存储与一致性模型

- 状态存储层服务所有核心模块和 processor，但所有访问必须通过 namespace、能力声明和权限控制，不能让 processor 随意读写核心 runtime 状态。
- 状态存储层必须提供统一抽象，把 Redis/Valkey 和 SQLite WAL 映射为事务、CAS/fencing、lease/lock、TTL、ordered queue、priority queue、secondary index、append-only state log、batch write、idempotency registry、namespace isolation 和 retention cleanup 等能力。
- Redis/Valkey 与 SQLite WAL 的能力差异必须在状态存储适配层显式标注；如果某项能力在某个后端只能模拟或语义较弱，不能在上层假装二者完全等价。
- Redis/Valkey 在生产模式下是强依赖；当 Redis/Valkey 不可用时，runtime 必须进入 degraded 或 unavailable，不能进行 leader lease、关键 DeliveryRecord 创建、ACK 强一致更新或控制审计写入。
- 当强一致状态存储不可用时，普通观测、内存健康画像或非关键缓存可以按策略继续本地计算和延迟推送，但任何需要可靠投递、控制审计、配置生效、owner/fencing 或 ACK/NACK/Defer 原子写入的链路都不能伪装成成功。
- SQLite WAL 支持开发模式和本机多进程模拟集群，但必须通过启动校验或文档明确禁止其作为生产分布式协调权威。
- 状态数据必须按 tenant/system/runtime node/processor plugin/audit/delivery/routing 等 namespace 隔离；所有 tenant 数据必须带 tenant 维度，系统级状态使用独立 namespace。
- 强一致状态必须包括投递状态、控制操作审计、配置/策略变更、Ack/Nack/Defer 记录、PendingAck/PendingNack、leader lease、owner/fencing、delivery tree 父子关系和 current owner 索引。
- 状态变更日志强制用于 delivery、config、audit、control、leader ownership/fencing 等核心强一致状态；普通缓存、指标和健康画像不强制追加状态日志。
- 连接会话快照、普通路由索引、拓扑健康视图、权限快照、限流背压状态、普通 DeliveryAttempt、普通 MessageDeliverySummary 和 target health score 可以采用内存实时状态加异步持久化/推送。
- delivery tree 查询必须强实时准确；父子关系、root_delivery_id、current_owner、current_state 等索引不能依赖最终一致异步聚合。
- 状态清理允许在保留期后删除详细 DeliveryRecord，但必须保留 MessageDeliverySummary 和压缩后的状态变更摘要；未处理 dead_lettered 不清理，transferred history 可以压缩但必须保留链路摘要。
- 清理详细 DeliveryRecord、AckRecord、NackRecord、DeferRecord 或 Attempt 记录时，不能破坏 summary、delivery tree、审计链路和压缩状态摘要之间的引用关系；清理必须可 dry-run 并可审计。
- 状态存储必须以 Redis/Valkey 作为生产强一致目标，覆盖 leader lease、fencing_token、DeliveryRecord、ACK/NACK/Defer 原子状态更新、控制审计和 delivery tree 查询。
- SQLite WAL 仅作为开发模式和本机多进程模拟集群使用，必须通过启动校验禁止其作为生产分布式协调权威。
- Redis/Valkey 在开发和测试环境中允许使用 standalone 模式；生产适配层必须支持 Sentinel 或 Cluster 拓扑能力。
- 状态存储层不得在业务代码中直接依赖单个 Redis 实例地址；所有访问必须通过统一 store adapter 进入。
- Redis/Valkey 状态模型采用 `Hash + Sorted Set + Stream/Log` 混合模型。
- DeliveryRecord、MessageDeliverySummary、Session、NodeState、RoutingPlan、Lease/Fencing 等当前权威状态优先使用 Hash 表达。
- 待发送队列、重试队列、ACK deadline、expires_at、恢复扫描索引、priority scheduling 等时间或优先级驱动结构使用 Sorted Set。
- 状态变更日志、审计摘要、恢复事件、控制事件和关键调试轨迹使用 Stream 或 append-only log 表达。
- Redis/Valkey 中的 Hash 保存“当前状态权威”，Sorted Set 保存“可调度/可扫描索引”，Stream/Log 保存“状态变化事实”，三者职责不得混用。
- Redis/Valkey 关键状态迁移必须优先通过 Lua 脚本实现，尤其是 claim delivery、ACK 原子提交、NACK 原子提交、Defer 延期、lease renew、fencing 校验、状态迁移、索引同步和状态变更日志追加。
- Lua 脚本必须保持短小、确定性和可测试，不允许在脚本中承载复杂业务逻辑；业务判断、策略裁决、路由评分、IAM 鉴权、payload_ref 校验仍必须在 runtime 应用层完成。
- 对同一个 DeliveryRecord 的状态变更，不允许出现“先更新 Hash，再由应用层补删 ZSet，再异步写状态日志”的非原子流程。
- Redis/Valkey key 设计必须从 Redis Cluster 兼容角度出发，所有需要在同一个 Lua 脚本内原子更新的 key，必须通过 hash tag 保证落在同一个 hash slot。
- Redis/Valkey key 的 hash tag 粒度采用 `tenant_id + bucket_id` 模型，而不是单纯按 `message_id` 或 `delivery_id` 分槽。
- `bucket_id` 应由稳定哈希算法基于 `message_id` 或 `delivery_id` 计算得到，例如 `bucket_id = hash(message_id) % bucket_count`。
- 同一条 message 下需要原子聚合的关键状态应尽量落在同一 bucket；对超大 fanout、broadcast 或多目标消息，可以按策略拆分到多个 bucket，并通过 MessageDeliverySummary 的分片聚合机制汇总。
- `bucket_count` 必须是配置项，并纳入 `config_version/policy_version` 管理。
- bucket 数量变化不能隐式重写旧 key；如需扩容 bucket，必须通过明确的数据迁移、双读迁移或新旧 bucket 并存策略完成，不能由运行时代码静默改变 hash 结果。

## 21. 管理、审计与查询边界

- `ns_backend` 内的 runtime 管理端应作为 `ns_backend` 内独立应用边界存在，并以具备 management capability 的 runtime transport 客户端接入 runtime；当前默认使用 WebSocket，它不是旁路数据库管理器，也不是独立控制协议客户端。
- 管理控制消息必须使用统一 envelope，走统一协议校验、source/auth_context 注入、IAM/管理 capability 鉴权、processor 流水线、审计、trace 和必要的可靠投递。
- 管理端可以执行踢连接、重投/清理消息、隔离/恢复节点、master 切换、限流策略调整、配置热更新、恢复扫描、状态快照查询和健康查询。
- 管理端执行批量 replay、批量 cancel、批量 hold、批量 release 或批量 cleanup 时，应支持 partial success，并返回 accepted/rejected 计数、可处理对象 ID 列表以及不可处理原因摘要。
- 批量管理操作应支持 dry-run、显式对象 ID 列表和受控条件筛选；真正执行前必须经过管理 capability 鉴权、策略限制、最大数量限制和审计记录。
- 管理端可以查询 message summary、delivery detail、delivery tree、dead letter、stream state、连接状态、节点状态和 runtime health；普通发送方不能直接查询 delivery 状态。
- 控制操作审计必须强一致且不可丢；审计中涉及敏感 payload、token、权限或身份信息时默认脱敏或摘要化。
- 清理策略由管理端通过配置热更新控制，清理动作作为管理控制 processor 执行；清理必须支持 dry-run、按 tenant、按 message_type、按状态、批量执行、暂停和恢复。
- 管理查询采用“摘要优先，必要时 drill-down 到明细”的读取模型。
- 普通管理查询应优先读取 MessageDeliverySummary、NodeState、SessionSnapshot、TargetHealthProfile、RuntimeHealthSummary、QueueWatermarkSummary 等摘要状态。
- 管理端需要排障、重投、取消、hold、状态解释或审计追踪时，才允许 drill-down 读取 DeliveryRecord、RoutingPlan、DeliveryAttempt、AckRecord、NackRecord、DeferRecord、DeadLetterRecord、状态变更 Stream/Log 和脱敏审计记录。
- 管理查询必须采用分级一致性模型。
- 控制类查询、replay/cancel/hold/kick_connection/drain_node/switch_master 等操作前置校验、delivery 明细查询、owner/fencing 状态查询、payload_ref 复验结果查询，必须读取 Redis/Valkey 当前权威状态。
- dashboard、列表页、运行概览、健康画像、队列水位、target health、tenant 级统计、趋势指标等允许读取近实时摘要，但响应中必须包含 `as_of`、`summary_version`、`state_version` 或等价版本字段。
- 管理操作提交采用分级模型。
- 高风险操作必须使用 `precheck + commit` 双阶段提交，包括 replay、cancel、hold、switch_master、node isolate/recover、批量 dead letter 清理、批量 delivery 操作、owner transfer、跨 tenant 管理操作和影响集群权威的控制命令。
- 低风险操作可以使用单阶段强校验，例如普通 kick_connection、低风险 reload_config、普通限流调整、状态快照查询和低风险观测控制。
- 双阶段提交中的 operation token 不能作为绕过权限、状态或 fencing 校验的凭证；commit 时仍必须重新读取权威状态并重新校验。

## 22. 恢复、保留与清理

- 投递状态必须持久化，进程重启后需要恢复未完成 DeliveryRecord；恢复后是自动重投还是等待管理端显式处理，必须由 recovery policy 配置。
- 恢复扫描触发时机必须包括进程启动、角色切换为 active_master、角色切换为 sub_node、从 degraded/isolated 恢复、配置热更新改变 recovery policy、管理端手动触发、owner 转移完成和 Redis/Valkey 存储连接恢复。
- 恢复扫描必须按 tenant 隔离执行，具备 tenant 级扫描游标、tenant 级恢复并发、tenant 级恢复预算、tenant 级恢复限流和全局恢复上限。
- 恢复扫描时，`prepared/queued`、`sending/ack_waiting`、`retry_scheduled`、`dead_lettered`、`acked`、`expired/cancelled/transferred` 等状态必须按各自恢复策略处理，不能统一重投；`created` 只允许作为内存构建期概念，不能作为可恢复持久状态。
- 如果恢复扫描发现 owner/fencing 不匹配、current_owner 不是自己或 message 已过期，应跳过、审计或转终态，不能为了恢复进度强行写状态。
- 状态保留期和清理策略必须按状态、message_type、tenant 和审计要求配置；AckRecord 的保留期通常不应短于相关 DeliveryRecord 的可追踪周期。
- NackRecord、DeferRecord、PendingAckRecord、PendingNackRecord 和 DeadLetterRecord 的保留期不应短于它们解释对应 DeliveryRecord 状态所需的最短审计周期；清理这些记录前必须确保 summary、delivery tree 和状态摘要仍能解释最终状态来源。
- Redis/Valkey 状态清理与归档采用平衡 TTL 策略。
- `acked`、`cancelled`、`expired` 等普通终态 delivery 默认在 Redis/Valkey 中保留 `7 天`。
- `dead_lettered` 默认保留 `30 天`。
- 状态变更日志、ACK/NACK/Defer 摘要、replay 记录、恢复扫描摘要和诊断性事件默认保留 `14～30 天`。
- 超过 TTL 后，状态数据应按策略归档到外部审计库、数据库、对象存储或日志系统，也可以在确认无需追溯后清理。
- 状态清理必须同时处理 DeliveryRecord、MessageDeliverySummary、ACK/NACK/Defer 记录、retry/timeout ZSet 索引、state log、dead letter 索引、stream 状态和相关审计摘要，避免孤儿索引、僵尸 delivery 或 summary 计数不一致。

## 23. 错误处理与状态机不变量

- 不单独设置“错误与异常处理”顶级层；连接层、Envelope 层、安全层、processor 层、路由层、可靠投递层、集群协调层分别处理自身最懂的错误，并使用统一错误模型和策略引擎裁决动作。
- 统一错误模型至少应表达 error_code、severity、category、tenant_id、connection_id、message_id、delivery_id、action、audit_required、disconnect_required、retryable 等信息。
- 原子成功写入的终态不可被普通事件覆盖；如果 delivery 已进入 `acked`、`cancelled`、`expired`、`dead_lettered` 或旧 owner `transferred`，后续 ACK/NACK/timeout/retry 只能审计或按特殊管理路径处理。
- owner/fencing 校验优先于所有状态变更；无 current owner 权限、无有效 fencing token 或无有效 delivery lease token 的 runtime/worker 不能写 DeliveryRecord 状态。
- 没有合法 AckRecord 时 DeliveryRecord 不能进入 `acked`；AckRecord 和 `acked` 状态必须原子写入，防止恢复时出现审计断链或误重试。
- NackRecord/DeferRecord 与对应状态变化必须原子写入；否则不能让 NACK 或 Defer 改变 retry、deadline 或 health 状态。
- 安全事件不能被普通投递策略覆盖；例如跨 tenant ACK、伪造 source、非法 auth_context、payload 明确越权等不能因为“ACK 优先”而把 delivery 改成 `acked`。
- `prepared` 不发送、不占 active 配额；`queued` 才进入发送调度；`retry_scheduled` 到点前不占 active/inflight；`ack_waiting` 持续占 inflight 直到终态或转入 retry。
- 资源占用口径必须稳定：`queued` 占 tenant/global 队列名额但不占连接写队列，`sending` 占 active/write slot 并受写超时保护，`ack_waiting` 占 inflight 和必要顺序窗口，`retry_scheduled` 释放 active/inflight 但保留 retry backlog 统计，终态必须释放所有运行时占用。
- `dead_lettered` 只能由显式 replay 恢复；`expired`、`cancelled`、`acked`、旧 owner `transferred` 默认不可恢复。
- 必须建立独立的 `RUNTIME_*` 错误码体系，但错误码、异常基类、错误元数据结构和标准错误映射应定义在 `ns_common.exceptions` 中。
- `RUNTIME_*` 错误码采用细粒度设计，不能只按大类模糊表达。
- 错误码应能直接区分协议解析失败、Envelope schema 失败、source 伪造、auth_context 伪造、IAM 拒绝、tenant 越界、target 不存在、route 不可用、ACK 超时、NACK 不可重试、Defer 超预算、fencing 拒绝、owner 不匹配、payload_ref 无效、leader lease 失效、processor 超时、状态机非法迁移等关键场景。
- 每个错误码必须携带稳定元数据，包括 `severity`、`category`、`retryable`、`disconnect_required`、`audit_required`、`safe_detail` 和可选 `action`。
- 生产审计与普通日志默认严格脱敏，不允许记录 token、payload 明文、完整 auth_context、完整 capabilities、fencing_token 原值、payload_ref 签名 URL、IAM 原始返回体或敏感权限明细。
- debug 模式允许打印经过脱敏处理的完整 envelope 结构，但必须经过统一 redaction/sanitizer 处理，并且默认关闭。
- runtime 中任何日志、异常、审计、事件或错误 envelope 都不得直接序列化原始 envelope 对象；必须先经过统一脱敏器处理。

## 24. TLS、事件循环、传输、部署、质量与性能基线

- 所有生产入站 transport 必须使用加密和服务端身份认证；WebSocket 使用 TLS/WSS，未来 HTTP/3/QUIC/WebTransport adapter 必须使用其安全传输模式。内网或开发环境是否允许明文 WebSocket 必须由配置控制，不能把明文能力扩展到生产安全假设或未来 QUIC/WebTransport adapter。
- 生产多节点协调必须使用 Redis/Valkey；SQLite WAL 只用于开发、本地单机或本机多进程模拟集群，并且需要防止误用为生产分布式协调权威。
- 必须定义单实例连接数、消息 QPS、P99 延迟、ACK timeout 等生产性能基线；这些指标不是固定生产 SLA，但必须作为压测、容量规划、瓶颈记录、风险评审和优化计划的依据。
- 单个 runtime 进程内部并发模型基于标准 `asyncio` API；生产 Linux/Ubuntu 环境默认通过 `event_loop=auto` 优先选择 `uvloop`，标准 `asyncio` 始终作为兼容实现、Windows 开发实现和基准对照保留。水平扩展优先通过多进程部署多个 runtime 实例。当前设计不采用多个进程级 worker 共享同一 runtime 运行状态的模型；如后续引入该模型，必须重新确认状态所有权、连接归属和进程间协调边界。
- `ns_runtime` 的功能完整性不能以通信链路能够跑通作为判断标准；生产可用性必须同时满足功能、可靠性、一致性、安全性、可恢复性和性能要求。
- 生产质量验证范围必须覆盖 `master/sub_node` 集群拓扑、Redis/Valkey 高可用适配、leader lease、fencing、可靠投递、ACK/NACK/Defer、完整 stream、replay、hold、cancel、状态查询、配置热更新、多节点配置一致性、标准 `asyncio`/`uvloop` 双实现、transport adapter conformance、故障注入、压测、审计脱敏、状态清理和恢复扫描。
- 生产性能基线必须明确且不能作为可选参考；未达到基线时必须记录瓶颈、风险、优化计划和是否允许进入生产部署或扩大使用范围的评审结论。
- 故障注入和恢复测试属于生产质量边界，不能只验证正常通信链路。
- 故障注入至少覆盖 Redis/Valkey 短暂不可用、IAM 超时、active master 断开、sub_node 断开、ACK 迟到、ACK 到旧 owner、connection_epoch 不匹配、payload_ref 校验失败、processor 超时、慢连接写队列满、transport handshake 失败、stream reset、flow-control blocked、network path migration 失败和 transport fallback 失败。
- 每个故障注入用例都必须验证四类结果：状态机迁移是否正确、是否产生标准错误或控制响应、是否写入脱敏审计、是否暴露可观测指标。
- 测试必须采用生产级分层，不得只依赖单元测试、简单集成测试或手工联调判断功能完整性。
- 测试范围至少必须覆盖单元测试、状态机测试、Redis/Valkey Lua 原子脚本测试、processor 流水线测试、Envelope 协议兼容测试、event loop compatibility/benchmark、transport adapter conformance、集群切换测试、故障注入测试、stream 可靠性测试、管理控制测试、压测和回归测试。
- 状态机测试必须覆盖 DeliveryRecord、MessageDeliverySummary、StreamDeliveryState、ACK/NACK/Defer、retry、dead letter、replay、cancel、hold、lease/fencing、owner transfer 等核心迁移。
- Redis/Valkey Lua 脚本测试必须覆盖原子提交、索引同步、fencing 拒绝、重复 ACK、迟到 ACK、旧 owner 写入、lease 过期、状态日志追加和异常回滚。
- 集群切换测试必须覆盖 graceful handoff、force takeover、emergency isolate、配置漂移、sub_node 断开、active master 失联、leader lease 过期和 fencing_token 轮换。
- stream 可靠性测试必须覆盖 stream_start、stream_chunk、stream_end、滑动窗口、cumulative ACK、selective ACK、missing ranges、乱序恢复、窗口动态调整、stream replay、stream cancel 和 stream hold。
- `uvloop` 验收必须与标准 `asyncio` 使用相同 workload、连接规模、消息分布、Redis/Valkey 拓扑和策略配置进行对比，至少记录吞吐、P95/P99、event loop lag、CPU、内存、任务堆积、取消行为和异常兼容性；不能仅依据 echo benchmark 决定默认策略。
- transport adapter conformance 必须验证应用消息边界、`connection.hello`、IAM、capability 协商、Envelope schema、ACK/NACK/Defer、backpressure、close/drain、resume、错误映射和脱敏观测在不同 transport 下保持同一语义。
- 当 WebSocket over HTTP/3、WebTransport 或原生 QUIC adapter 启用时，必须新增移动网络切换/NAT rebinding/path validation、stream multiplexing、flow control、UDP 不可用回退、0-RTT 拒绝/重放保护、datagram allowlist 和 QUIC transport ACK 不影响 DeliveryRecord 的专项测试。
- 生产性能参考基线建议如下：当前默认 WebSocket transport 下单 runtime 普通连接数不少于 `5,000`；master 管理/节点连接数不少于 `100`；本地 task dispatch 受理吞吐不少于 `2,000 msg/s`；master/sub_node 转发吞吐不少于 `1,000 msg/s`；本地 ACK P99 不高于 `100ms`；跨节点 ACK P99 不高于 `300ms`；Redis/Valkey 关键状态写入 P99 不高于 `50ms`；delivery recovery scan 速率不少于
  `1,000 records/s`；replayable dead letter 重投成功率不低于 `99%`；安全/管理/状态变更审计覆盖率为 `100%`；token/payload/auth_context/fencing 原值泄露为 `0`；TTL 清理后孤儿索引为 `0`；必选故障场景通过率为 `100%`。
- 性能基线必须与压测报告绑定。压测报告至少应包含测试环境、event loop implementation、transport type/capabilities、runtime 节点数量、Redis/Valkey 拓扑、连接规模、消息类型分布、payload 模式、ACK timeout 配置、worker 配置、pool 配置、P95/P99、event loop lag、transport backpressure/RTT/path migration（适用时）、错误码分布、Redis/Valkey 延迟、CPU/内存占用和瓶颈分析。

## 25. 明确禁止漂移的硬边界

- ACK 只表示收到，不表示执行开始或执行完成；任何后续设计不得改变 ACK 语义。
- 所有可执行行为都必须走 processor；ACK、NACK、Defer、健康检查和管理控制都不能绕开 processor。
- source 和 auth_context 入站禁止携带，必须由 runtime 注入；这不是可配置项。
- DeliveryRecord 强一致持久化是可靠投递底线；不能把 delivery 状态退化为纯内存状态。
- 控制操作审计、投递状态、配置/策略变更必须强一致且不可丢；不能为了性能把这些核心记录改成异步 best-effort。
- Redis/Valkey 生产不可用时关键强一致链路必须停止或降级拒绝；不能在生产多节点场景用 SQLite WAL 替代 Redis/Valkey 做分布式选主权威。
- 管理端是具备 management capability 的 runtime transport 客户端；当前默认使用 WebSocket，管理控制始终使用统一 Envelope 和 processor，不走旁路协议。
- 当前唯一允许的 wire codec 是 UTF-8 `json.v1`；WebSocket 使用 JSON 文本帧，未来 transport adapter 也必须承载完整 JSON Envelope。不能仅通过配置改成二进制协议、混合编码或 processor 私有 framing。
- Runtime 不能负责对象存储上传、下载或签名 URL；payload_ref 只做引用路由和实时校验。
- 多 master 当前采用单 active master、多 standby master 模型；不能默认设计成多 active 分片 master，除非后续重新讨论并确认分片 leader 模型。
- 所有 transport adapter 都必须进入相同的 connection/session、Envelope、IAM、tenant、processor、路由、可靠投递和审计链路；QUIC/WebTransport 不能成为绕过核心状态机的第二套协议。
- QUIC packet ACK、transport write completion、stream ACK 或 path validation 不能替代 runtime `delivery.ack`，也不能直接更新 DeliveryRecord。
- 同一 runtime 内的 QUIC/WebTransport network path migration 可以保持 connection_id、connection_epoch 和 session_id 不变；跨 runtime 节点的透明 logical session migration 仍不属于当前边界。
- `uvloop` 是可配置的事件循环实现，不是业务层依赖；标准 `asyncio` 兼容路径不得删除，event loop 不能在进程运行期间热切换。
- `websocket_http3`、`webtransport_http3` 和 `quic_native` 的配置与观测扩展点必须保留，但在对应 adapter 未完成生产验收前默认禁用且不得宣称可用。
