# ns_runtime 分阶段实施与验收文档

> 实施文档版本：`0.0.2`  
> 设计基线：`ns_runtime 设计边界与功能清单 0.0.2`  
> 仓库基线：Code Agent 当前会话所处的 `ns_evermore` 本地工作区；远程仓库、远程分支和提交历史不作为实现状态依据  
> 基线日期：由 `P00` 在本地工作区完成基线采集时填写  
> 文档用途：指导人工开发者与 Code Agent 按阶段实施、测试、验收和交接 `ns_runtime`。

---

## 0. 文档执行规则

### 0.1 权威顺序

实施过程中按以下权威顺序处理冲突：

1. `ns_runtime 设计边界与功能清单 0.0.2`。
2. 当前本地工作区中已经通过本地测试验证的代码、配置和接口契约。
3. 本实施文档中与当前本地工作区一致、且已经标记为 `VERIFIED` 的阶段出口和接口契约。
4. 当前阶段任务说明。

远程仓库内容、远程默认分支、GitHub 搜索结果、提交历史、PR、Issue 和发布页面不得用于判断当前工作区已经实现或尚未实现的功能。远程信息与本地工作区不一致时，以本地工作区为唯一实施事实源；本实施账本必须随本地工作区重新校准。

设计文档中的“必须”“禁止”“默认”“由策略配置”不得被阶段实现覆盖。本实施文档只拆分落地顺序，不修改设计边界。

### 0.2 禁止行为

- 禁止在设计文档中记录实现进度。
- 禁止为提前跑通链路创建临时 Envelope、裸 JSON 命令、私有 ACK、私有管理接口或 processor 旁路。
- 禁止在强一致状态存储未完成前把 `task.dispatch` 标记为可用。
- 禁止把 transport 写成功解释为 `delivery.ack`。
- 禁止把 Redis/Valkey 通用缓存客户端作为 DeliveryRecord、leader lease、fencing、ACK/NACK/Defer 的权威状态存储。
- 禁止用 SQLite WAL 替代生产 Redis/Valkey 集群协调权威。
- 禁止在 runtime 深层模块直接读取全局 `ns_config`、全局 HTTP client、全局 cache client 或其他隐式单例。
- 禁止在 processor、router、delivery worker 中直接判断具体 WebSocket、QUIC、WebTransport 库类型。
- 禁止以未完成阶段为理由返回伪成功。未启用能力必须返回稳定的功能禁用错误并审计。
- 禁止修改已验证阶段的公共契约而不重新执行该阶段及所有下游阶段的回归测试。
- 禁止在仓库根目录 `tests/` 之外新增或保留自动化测试文件，尤其禁止把测试文件放入 `src/` 生产源码目录。
- 禁止在仓库目录内创建 `.venv`、`venv` 或其他虚拟环境；Windows 环境依赖只能安装到 `S:\PythonVenv` 下的共享隔离环境，Linux/WSL 环境依赖只能安装到 `/home/ns/.virtualenvs` 下的隔离环境。

### 0.3 状态枚举

阶段、工作包和验收项统一使用以下状态：

| 状态 | 含义 |
|---|---|
| `UNVERIFIED` | 尚未根据当前本地工作区读取源码并执行测试，不得判断实现状态 |
| `NOT_STARTED` | 已确认当前未开始，不得假设任何能力存在 |
| `IN_PROGRESS` | 正在实施，接口和行为尚不稳定 |
| `IMPLEMENTED` | 实现完成，但尚未通过全部阶段验收 |
| `VERIFIED` | 实现、测试、故障验证、文档和证据全部完成 |
| `BLOCKED` | 存在明确阻塞项，必须记录阻塞原因和解除条件 |
| `DEFERRED` | 设计中保留但不属于当前实施阶段，必须保持显式禁用 |
| `FAILED` | 验收失败，阶段不得向后推进 |

### 0.4 功能完成度等级

| 等级 | 含义 |
|---|---|
| `F0` | 无实现 |
| `F1` | 类型、配置、接口契约和错误模型完成 |
| `F2` | 单进程正常路径完成并通过测试 |
| `F3` | 并发、异常、恢复和持久化路径完成 |
| `F4` | 多节点、故障注入、性能与生产安全验收完成 |

任何功能不得仅凭“存在类或方法”提升完成度。完成度必须由对应测试证据决定。

### 0.5 Code Agent 新会话执行流程

每个新会话必须依次完成以下动作：

1. 定位当前会话实际打开的本地 `ns_evermore` 仓库根目录；无法定位时停止实施并把 `P00` 标记为 `BLOCKED`。
2. 读取本地工作区状态，确认当前分支或 detached 状态、未提交修改、未跟踪文件、子模块状态和当前工作目录；不得切换分支、清理文件或覆盖用户修改。
3. 直接读取本地设计文档 `0.0.2`、本实施文档、依赖清单、配置文件、测试入口以及当前阶段涉及的源文件。
4. 检查本实施文档记录的仓库基线是否与当前本地文件一致；不一致时先执行 `P00` 基线重校准，不得直接沿用旧状态。
5. 读取“当前执行游标”“本地仓库现状基线”“全局不变量”和当前阶段全文。
6. 检查当前阶段状态、当前工作包、阻塞项和验收证据；验收证据必须指向当前本地工作区中的测试、报告或文件。
7. 只实施“当前执行游标”指向的工作包；发现前置阶段未达到 `VERIFIED` 时立即停止后续阶段开发。
8. 变更前把对应工作包状态改为 `IN_PROGRESS`。
9. 完成实现后执行工作包测试、阶段回归和安全检查。
10. 仅在全部通过后把工作包标记为 `VERIFIED`，填写本地证据路径、测试结果和已知限制。
11. 更新“当前执行游标”，明确下一工作包。
12. 新增或变更公共契约时更新“公共基础设施登记表”和“接口冻结登记表”。
13. 不得通过提交历史、远程仓库、GitHub Connector 或网页内容推断实现状态；实现状态只由当前本地文件、当前本地测试和本文件状态确定。

### 0.6 本地测试与虚拟环境硬约束

- 所有自动化测试文件、测试辅助模块和测试专用资源统一放在仓库根目录 `tests/` 下；Python 测试文件统一使用 `test_*.py` 命名。
- 生产源码目录 `src/` 只放生产代码，不得放置 `tests.py`、`test_*.py` 或测试专用包。发现旧测试位于 `src/` 时，当前工作包必须先迁移到根 `tests/` 并完成回归。
- Windows 本地开发使用 `S:\PythonVenv` 作为本项目虚拟环境唯一根目录，不得在 `ns_evermore` 仓库内新建虚拟环境。
- runtime 与 `ns_common` 配置测试使用 `S:\PythonVenv\ns_runtime\Scripts\python.exe`；backend、Django 和 cache 兼容回归使用 `S:\PythonVenv\ns_backend\Scripts\python.exe`。
- 若上述环境缺失或损坏，只能在 `S:\PythonVenv` 下修复或重建对应环境，并在实施账本中记录；不得回退到仓库内 `.venv`。
- 工作包需要真实 Linux 环境时允许使用 WSL；若 Linux/WSL 验证需要创建 Python 虚拟环境，必须创建在 `/home/ns/.virtualenvs` 下，并在实施账本中记录发行版、Python 版本、环境路径和验证命令；不得在仓库、`/mnt` 下的工作区或其他 Linux 路径创建虚拟环境。
- Windows PowerShell 标准测试入口如下：
  - runtime 配置测试：`$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config -v`。
  - 根目录全量回归：`$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`。

---

## 1. 当前执行游标

| 字段 | 当前值 |
|---|---|
| 当前阶段 | `P01 ns_common 公共基础设施加固` |
| 当前工作包 | `P01-W10 把 sanitizer 接入 NsLogger` |
| 当前阶段状态 | `IN_PROGRESS` |
| 最近已验证阶段 | `P00 本地仓库基线与实施账本`（2026-07-16） |
| 下一阶段 | `P02 Runtime 进程生命周期与事件循环` |
| 当前阻塞项 | 无；使用 `S:\PythonVenv\ns_runtime` 与 `S:\PythonVenv\ns_backend` 隔离环境 |
| 设计基线版本 | `0.0.2` |
| wire codec | `json.v1` |
| 当前正式 transport | 本地无 transport 实现；设计基线为 `websocket_tcp`，须在 P04 验证前保持禁用 |
| 生产状态存储目标 | Redis/Valkey；本地仅有普通 cache adapter，无强一致 state store |

执行游标只能指向一个未完成工作包。并行开发必须拆成互不修改同一核心契约的独立工作包，并在阶段内记录合并顺序。

---

## 2. 本地仓库现状基线

### 2.1 基线来源

本节只能由实际运行在本地 `ns_evermore` 工作区中的开发者或 Code Agent 填写。基线不得从 GitHub、远程分支、提交记录、PR、Issue、缓存搜索结果或之前会话记忆复制。

P00 必须记录以下事实：

| 基线字段 | 状态 | 本地结果 |
|---|---|---|
| 本地仓库根目录 | `VERIFIED` | `S:\PythonProject\ns\ns_evermore` |
| 当前分支状态 | `VERIFIED` | `main`，本地状态显示跟踪 `origin/main`；未读取远程内容或提交历史 |
| 当前工作区修改 | `VERIFIED` | 会话开始前已有：已暂存删除 `docs/ns_runtime_design_checklist_0.0.1.md`；未跟踪目录 `docs/`（含两份 0.0.2 文档）；无子模块 |
| 设计文档路径与版本 | `VERIFIED` | `docs/ns_runtime_design_checklist_0.0.2.md`，文档头版本 `0.0.2` |
| 实施文档路径与版本 | `VERIFIED` | `docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，实施版本 `0.0.2` |
| Python 版本与虚拟环境 | `VERIFIED` | Python `3.10.11`；runtime 环境为 `S:\PythonVenv\ns_runtime`，backend/cache 回归环境为 `S:\PythonVenv\ns_backend`；仓库内无 `.venv` |
| 测试入口 | `VERIFIED` | 测试统一位于根 `tests/`；全量入口：`python -m unittest discover -s tests -p "test_*.py" -v`；runtime 配置入口：`python -m unittest tests.test_config -v` |
| `src/ns_common` 实际能力 | `VERIFIED` | 存在配置、路径、异步生命周期、UTC/单调/可控时钟、统一标识符、固定/指数/jitter 退避、不可变 retry 预算、统一 sanitizer、日志、HTTP、普通 cache 与部分 runtime 错误类；缺少 P01 要求的 observability、testing 等公共能力 |
| `src/ns_backend/iam` 实际能力 | `VERIFIED` | 存在 token introspection、access/batch access、权限、session、decision/operation audit；缺少 runtime node/service credential、权限失效事件与冻结的 IAM-R1 合同 |
| `src/ns_runtime` 实际能力 | `VERIFIED` | 本地目录不存在，进程、协议、transport、session、processor、路由、delivery、stream、cluster、management 与 observability 均为 F0 |
| 配置示例与依赖清单 | `VERIFIED` | `etc/ns_config.example.json` 已包含 backend/cache/log、完整 runtime 总组及 17 个强类型 runtime 细分组；`requirements-runtime.txt` 与 `requirements-backend.txt` 存在，无独立测试依赖清单 |
| 本地基线测试结果 | `VERIFIED` | 命令可复现；在发现测试前因 `concurrent-log-handler` 未安装而导入失败：0 通过、1 loader error、0 跳过；未触碰真实数据库或远程服务 |
| 基线采集时间 | `VERIFIED` | `2026-07-16T13:55:23+08:00` |

### 2.2 本地代码检查范围

P00 必须直接检查以下内容，并把实际结果写入“本地能力登记表”：

- 仓库根目录中的项目元数据、依赖清单、测试配置、运行配置和文档。
- `src/ns_common` 中配置、路径、日志、异常、HTTP、缓存、状态存储、时间、标识符、退避、脱敏、观测和测试基础设施。
- `src/ns_backend/iam` 中 runtime 可调用的身份解析、权限检查、节点凭证、服务凭证、审计和权限失效能力。
- `src/ns_runtime` 中进程入口、配置、协议、transport、session、IAM client、processor、state store、routing、delivery、stream、cluster、management、observability 和测试。
- `etc`、`sql`、`tests`、运行脚本和依赖文件中与 runtime 有关的内容。
- 本地生成文件只用于测试证据，不作为接口权威；被忽略文件、缓存目录、日志、临时数据库和构建产物不得被登记为正式实现。

### 2.3 本地能力登记表

P00 对每项能力使用以下结构登记。未读取源码并执行对应测试的能力统一为 `UNVERIFIED`，不得直接标记为缺失或完成。

| 能力域 | 本地路径 | 实际接口或行为 | 测试证据 | 功能完成度 | 结论 |
|---|---|---|---|---|---|
| 配置基础设施 | `src/ns_common/config.py` | backend/cache/log/runtime 总组及 17 个强类型 runtime 细分组的深度不可变快照、独立 metadata/生效模式、严格加载/序列化、兼容别名、固定来源优先级、backend 覆盖和已验证快照恢复已完成；runtime 集群静态启动角色固定为 singleton、sub_node、standby_master、active_master | `tests/test_config.py` 40/40；根测试回归 93/93 | `F2` | `VERIFIED`，P01-W01/W02/W03 与 P01-FIX-01 已完成 |
| 路径与生命周期 | `src/ns_common/paths.py`、`src/ns_common/async_runtime.py` | 仓库固定路径常量与目录创建；event loop selector 已支持 auto/asyncio/uvloop、Windows/Linux 策略、可选依赖失败和 restart_required 门禁；TaskSupervisor 已支持命名任务、异常收集、分组有序取消、全局关闭超时和未完成任务报告 | Windows `tests.test_async_runtime` 23/23；WSL 22 通过/1 Windows 专用跳过且真实 uvloop loop 已验证；根测试回归 93/93 | selector、TaskSupervisor `F2` | P01-W04/W05 `VERIFIED` |
| 时间基础设施 | `src/ns_common/time.py` | 显式 Clock 协议；SystemClock 提供 UTC wall clock、monotonic 和异步 sleep；ControlledClock 支持确定性 UTC/单调推进、并发 deadline 唤醒、取消清理和跨 loop 门禁 | Windows `tests/test_time.py` 11/11；WSL 11/11；根测试回归 93/93 | `F2` | `VERIFIED`，P01-W06 已完成 |
| 标识符基础设施 | `src/ns_common/identifiers.py` | 九类带唯一类型前缀的 RFC 4122 UUIDv4 hex ID；显式 factory、严格解析/校验、冻结值对象和便捷生成函数，无全局服务依赖 | Windows `tests/test_identifiers.py` 8/8；WSL 8/8；9000 次并发无冲突；根测试回归 93/93 | `F2` | `VERIFIED`，P01-W07 已完成 |
| 重试与退避基础设施 | `src/ns_common/retry.py` | 可插拔 BackoffStrategy；固定、指数封顶和确定性对称 jitter；默认 5 次的不可变 RetryBudget；显式 Clock 下同时计算 UTC next_retry_at 与 monotonic deadline；delivery retry 序号与 message 共享预算消耗解耦；数值转换异常统一归一化且 RetrySchedule 强制验证冻结构造不变量 | Windows `tests/test_retry.py` 19/19；runtime 联合 101/101；根测试回归 112/112 | `F2` | `VERIFIED`，P01-W08 与 P01-FIX-02 已完成 |
| 日志与脱敏 | `src/ns_common/security.py`、`src/ns_common/logger.py` | sanitizer 已支持字段名/路径规则、嵌套映射、dataclass、普通对象、异常 details、URL/自由文本、循环与深度门禁；logger 仍为 JSON/text/彩色 formatter、轮转与全局 map，尚未接入 sanitizer | Windows/WSL `tests/test_security.py` 各 9/9；runtime 联合 110/110；根测试 121/121 | sanitizer `F2`、logger 接入 `F1` | P01-W09 `VERIFIED`；W10 `NOT_STARTED` |
| HTTP 基础设施 | `src/ns_common/http_client.py` | httpx async client、兼容全局 client map 与 close；错误保留原始 body preview，无显式 factory/owner | 源码审查；依赖未安装 | `F1` | `IN_PROGRESS`，待 P01 |
| 普通缓存 | `src/ns_common/cache` | SQLite/Redis/Valkey/dummy backend，同步/异步 client 与 Django adapter；client 对异常采用 soft failure | `tests/test_cache.py` 11/11，通过 `S:\PythonVenv\ns_backend` 执行 | `F2` | `VERIFIED` |
| 强一致状态存储 | 无 | 不存在 StateStore、CAS、lease、fencing 或 Lua runner；普通 cache 明确不能替代 | 路径与源码扫描 | `F0` | `NOT_STARTED`，目标 P08 |
| 公共异常与错误注册 | `src/ns_common/exceptions.py` | 基类及约 25 个细粒度 runtime 异常类；无结构化元数据注册表和唯一性验证 | 源码审查 | `F1` | `IN_PROGRESS`，目标 P01 |
| backend IAM 合同 | `src/ns_backend/iam` | HTTP 路由提供 token introspection、access check/batch、resource filter、权限/session/审计；无 runtime 节点凭证与失效事件合同 | 路由与 service 源码审查；依赖未安装 | `F1` | `IN_PROGRESS`，冻结目标 P06 |
| runtime 进程与事件循环 | 无 `src/ns_runtime` | 无入口、service、loop selector 或运行上下文 | 路径扫描 | `F0` | `NOT_STARTED` |
| Envelope 与类型注册 | 无 | 无统一 Envelope、schema、版本兼容或 message type 注册表 | 路径扫描 | `F0` | `NOT_STARTED` |
| Transport 与连接 | 无 | 无 adapter、capability、WebSocket listener 或 conformance | 路径扫描 | `F0` | `NOT_STARTED` |
| Session、握手与恢复 | 无 | 无 connection.hello、SessionContext、heartbeat、resume 或 epoch | 路径扫描 | `F0` | `NOT_STARTED` |
| Processor 与插件 | 无 | 无 processor pipeline、registry、plugin、event bus 或审计入口 | 路径扫描 | `F0` | `NOT_STARTED` |
| RoutingPlan 与调度 | 无 | 无 RoutingPlan、策略或本地索引路由 | 路径扫描 | `F0` | `NOT_STARTED` |
| 可靠投递 | 无 | 无 Summary、DeliveryRecord、scheduler、worker 或权威状态 | 路径扫描 | `F0` | `NOT_STARTED` |
| ACK/NACK/Defer | 无 | 仅公共异常类与 NACK reason 映射，无 processor 或状态机 | 源码与路径扫描 | `F0` | `NOT_STARTED` |
| Stream | 无 | 无 stream 模型、窗口或状态机 | 路径扫描 | `F0` | `NOT_STARTED` |
| 集群与 fencing | 无 | 仅公共 cluster/fencing 异常类，无 role、lease、fencing 状态 | 源码与路径扫描 | `F0` | `NOT_STARTED` |
| 管理控制与配置热更新 | 无 runtime 实现 | backend IAM 有普通管理 API；无 runtime transport 管理 Envelope、processor 或配置热更新 | 路径扫描 | `F0` | `NOT_STARTED` |
| 可观测与故障测试 | `src/ns_common/logger.py`；其余无 | 仅日志；无 metrics/trace/snapshot sink、runtime 指标、故障注入或敏感泄露扫描 | 源码与测试扫描 | `F0` | `NOT_STARTED` |

### 2.4 基线判定规则

- 文件存在只证明代码存在，不证明功能完成。
- 单元测试通过只能将对应局部能力提升到其阶段定义允许的完成度。
- 未执行真实依赖集成测试时，不得把 Redis/Valkey、IAM、TLS、WebSocket 或集群能力标记为 `F3` 或 `F4`。
- 本地代码与本实施账本不一致时，先把受影响阶段降级为 `IN_PROGRESS` 或 `FAILED`，完成重新验收后再恢复 `VERIFIED`。
- 本地工作区含有用户未提交修改时，必须保留这些修改，并在交接记录中说明哪些文件在本次会话开始前已存在改动。
- 当前工作区没有 `src/ns_runtime` 或某项能力时，必须在读取本地目录和测试配置后记录为 `F0`；不得因为远程仓库存在同名文件改变结论。
- 当前工作区已经存在 runtime 实现时，P00 必须把代码映射到本实施文档各阶段，逐项验证后设置状态；不得把所有阶段统一重置为 `F0`。

### 2.5 公共基础设施边界

- 能被 backend、runtime、node、client 或未来组件共同复用，且不含 runtime 协议语义的能力统一进入 `ns_common`。
- `ns_common` 可以容纳配置、时钟、ID、退避、脱敏、日志、HTTP、缓存、强一致状态原语、指标接口、任务监督和测试工具。
- runtime 私有 Envelope、message type、SessionContext、RoutingPlan、DeliveryRecord、stream 状态机和 processor 语义保留在 `ns_runtime`。
- `ns_common.cache` 维持普通缓存语义；runtime 权威状态不得通过其软失败接口写入。
- `ns_backend.iam` 保持身份与权限权威；runtime 只保存权限快照、版本和引用。

---

## 3. 全局架构不变量

以下不变量在所有阶段持续生效：

| 编号 | 不变量 | 验证方式 |
|---|---|---|
| `INV-001` | ACK 只表示目标逻辑连接收到完整 Envelope | ACK processor 和端到端测试不得引用业务执行结果 |
| `INV-002` | source 和 auth_context 入站永远拒绝 | 协议负向测试覆盖所有 message.type |
| `INV-003` | 所有应用行为进入 processor | 代码扫描和流水线测试不得存在控制旁路 |
| `INV-004` | transport ACK 不更新 DeliveryRecord | transport conformance 和故障测试验证 |
| `INV-005` | 可靠 DeliveryRecord 强一致持久化 | state store 原子测试和进程重启恢复测试验证 |
| `INV-006` | owner/fencing 校验先于状态变更 | 所有 Lua 脚本和状态迁移测试验证 |
| `INV-007` | RoutingPlan 与 DeliveryRecord 分离 | 类型依赖检查和重路由历史测试验证 |
| `INV-008` | 生产强一致存储只能使用 Redis/Valkey | 启动校验测试验证 prod + sqlite 必须失败 |
| `INV-009` | 管理控制使用统一 Envelope 和 processor | 管理端到端测试验证无旁路 HTTP 控制接口 |
| `INV-010` | runtime 不保存完整业务 payload 明文 | state dump、日志、审计扫描验证 |
| `INV-011` | 当前 wire codec 只有 UTF-8 `json.v1` | 配置校验和 transport conformance 验证 |
| `INV-012` | 标准 asyncio 路径始终可用 | Windows/标准 loop 回归测试验证 |
| `INV-013` | event loop 运行中不得切换 | 配置热更新测试必须返回 restart_required |
| `INV-014` | QUIC/WebTransport 扩展不得绕过核心链路 | capability 和 adapter conformance 验证 |
| `INV-015` | 未实现功能不得返回成功 | feature gate 全量测试验证 |
| `INV-016` | 核心日志和错误必须先脱敏 | token/payload/auth_context/fencing 泄露扫描验证为零 |

---

## 4. 公共基础设施登记表

所有跨组件通用能力统一进入 `ns_common`。每项完成后填写状态、使用方和测试证据。

| 编号 | 公共能力 | 所属边界 | 当前状态 | 目标阶段 |
|---|---|---|---|---|
| `COM-001` | 不可变配置快照、配置来源、组版本元数据和强类型 runtime 细分配置 | `ns_common.config` | `VERIFIED` | P01 |
| `COM-002` | event loop 选择、任务监督和优雅关闭基础 | `ns_common.async_runtime` | `IN_PROGRESS`（selector、TaskSupervisor 已验证；进程信号和资源关闭集成待 P02） | P01-P02 |
| `COM-003` | 单调时钟、UTC 时间和可控测试时钟 | `ns_common.time` | `VERIFIED` | P01 |
| `COM-004` | 标识符生成和格式校验 | `ns_common.identifiers` | `VERIFIED` | P01 |
| `COM-005` | 指数退避、jitter 和预算基础类型 | `ns_common.retry` | `VERIFIED` | P01 |
| `COM-006` | 统一 redaction/sanitizer | `ns_common.security` | `VERIFIED` | P01 |
| `COM-007` | 结构化错误注册表和错误元数据 | `ns_common.exceptions` | `IN_PROGRESS` | P01 |
| `COM-008` | 显式 HTTP client factory 和生命周期管理 | `ns_common.http_client` | `IN_PROGRESS` | P01 |
| `COM-009` | Metrics、trace 和 diagnostic sink 接口 | `ns_common.observability` | `NOT_STARTED` | P01 |
| `COM-010` | 强一致 state store 抽象 | `ns_common.state_store` | `NOT_STARTED` | P08 |
| `COM-011` | Redis/Valkey state store adapter 与 Lua runner | `ns_common.state_store` | `NOT_STARTED` | P08 |
| `COM-012` | SQLite WAL 开发 state store adapter | `ns_common.state_store` | `NOT_STARTED` | P08 |
| `COM-013` | 通用 lease/fencing/CAS 原语 | `ns_common.state_store` | `NOT_STARTED` | P08 |
| `COM-014` | 本地敏感凭证加密存储 | `ns_common.security` | `NOT_STARTED` | P06 |
| `COM-015` | 测试资源工厂、临时配置和真实依赖管理 | `ns_common.testing` | `NOT_STARTED` | P01 |

公共能力不得引用 `ns_runtime`。runtime 私有模型不得反向放入公共层。

---

## 5. 测试分层和验收证据

### 5.1 测试层级

| 层级 | 内容 | 执行时机 |
|---|---|---|
| `T1 Unit` | 单类、纯策略、序列化、校验、错误映射 | 每个工作包 |
| `T2 Contract` | IAM、transport、state store、processor、配置组接口契约 | 接口变更时 |
| `T3 State Machine` | Delivery、Summary、Stream、Session、Role、Lease 状态迁移 | P05 起持续执行 |
| `T4 Integration` | WebSocket、Redis/Valkey、SQLite WAL、backend IAM | 每个阶段出口 |
| `T5 Concurrency` | 多协程 claim、ACK、lease renew、取消、并发 replay | P08 起持续执行 |
| `T6 Fault Injection` | 存储、IAM、连接、master、stream、path、fallback 故障 | P12 起逐步扩展 |
| `T7 Security` | 伪造、越权、重放、敏感信息泄露、错误信息安全 | 每个安全边界阶段 |
| `T8 Performance` | QPS、P95/P99、loop lag、CPU、内存、backlog | P20-P22 |
| `T9 Regression` | 所有已验证阶段 | 每个阶段出口 |

### 5.2 测试运行环境

- Windows：标准 asyncio，SQLite 开发模式，协议、processor、session 和单进程测试。
- Ubuntu/Linux：可使用 WSL；标准 asyncio 与 uvloop 双模式，Redis/Valkey standalone 集成测试；新建 Python 虚拟环境统一位于 `/home/ns/.virtualenvs` 下。
- Linux 多进程：SQLite WAL 本机模拟集群，只验证开发语义。
- Linux 生产等价：Redis/Valkey Sentinel 或 Cluster、TLS、多个 runtime 进程。
- 测试不得依赖开发者真实 `data`、`etc`、`log` 目录；全部使用临时目录和显式配置快照。
- 所有自动化测试文件统一放在仓库根目录 `tests/`，使用 `test_*.py` 命名；生产源码目录不得放置测试文件。
- 真实 Redis/Valkey 测试必须清理独立 namespace，禁止 `FLUSHDB` 影响共享实例。

### 5.3 阶段证据格式

每个阶段完成后必须填写：

- 阶段状态。
- 完成日期。
- 已验证工作包。
- 新增或变更的公共契约。
- 测试入口和通过数量。
- 故障注入结果。
- 性能数据，适用时填写。
- 敏感信息扫描结果。
- 未解决问题及其所属后续阶段。
- 下一执行工作包。

---

# 6. 分阶段实施计划

## P00 本地仓库基线与实施账本

**阶段状态：`VERIFIED`**  
**目标完成度：`F1`**

### 目标

在当前 Code Agent 实际打开的本地工作区中建立不依赖远程仓库和提交历史的代码基线，固定设计版本、测试入口、功能映射、状态枚举、执行游标和公共基础设施登记表。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P00-W01` | `VERIFIED` | 定位本地仓库根目录，记录分支或 detached 状态、工作区修改、未跟踪文件、子模块和解释器环境；全程不得改动用户已有文件 | 本地工作区身份和初始修改清单完整 |
| `P00-W02` | `VERIFIED` | 读取本地设计文档与实施文档，确认设计版本、文件路径和实施账本版本 | 本地设计基线确认为 `0.0.2`；无设计冲突 |
| `P00-W03` | `VERIFIED` | 读取本地项目元数据、依赖、配置、测试入口、`ns_common`、`ns_backend.iam`、`ns_runtime` 和相关测试 | 本地能力登记表已按本地路径、行为、证据和完成度填写 |
| `P00-W04` | `VERIFIED` | 执行不改变数据的本地基线测试；记录通过、失败、跳过、缺失依赖和环境阻塞 | loader error 可复现且已记录，未触碰真实数据 |
| `P00-W05` | `VERIFIED` | 把现有本地实现映射到 P01-P22；已完整实现并通过阶段门禁的工作包可标记为 `VERIFIED`，其余按实际状态登记 | P01 为部分 F1；P02-P22 为 F0 |
| `P00-W06` | `VERIFIED` | 建立 `ns_common` 公共基础设施登记表和接口冻结登记表；识别重复实现和应迁移能力 | 公共能力归属保持在 `ns_common`；runtime 私有能力未混入 cache |
| `P00-W07` | `VERIFIED` | 设置唯一当前执行游标和下一工作包 | 游标已指向 `P01-W01` |

### 实施规则

- 不读取提交历史，不使用提交消息、PR、Issue 或远程代码判断实现状态。
- 不拉取、不切换、不重置、不清理本地工作区。
- 不因实现文件存在而直接标记工作包完成。
- 不因测试文件缺失而自动认定功能错误；必须把“实现存在但缺少测试”记录为 `IMPLEMENTED` 或更低状态。
- 不执行会写入生产数据库、删除数据、迁移真实 schema、修改远程服务或发送真实业务消息的基线测试。
- 发现本实施文档对本地代码的描述错误时，先修正文档基线，再进入功能开发。

### 阶段出口

- 本地仓库根目录、工作区初始状态和环境已记录。
- 设计文档不包含实现进度。
- 本文件成为当前本地工作区的唯一实施状态账本。
- 所有能力都有本地源码与测试证据，或明确标记为 `UNVERIFIED`、`F0`、`BLOCKED`。
- P01-P22 状态已根据本地实现重新校准。
- 下一工作包已固定且其前置条件可验证。

### P00 本地验收证据

- 完成时间：`2026-07-16T13:55:23+08:00`。
- 工作区证据：`git status --short --branch`、`git submodule status`、本地目录与文件读取；未查询远程或提交历史。
- 设计证据：本地两份 0.0.2 文档已直接读取；设计文档未写入实现进度。
- 测试证据：`python -m unittest discover -s src -p tests.py -v`，结果为 `FAILED (errors=1)`；失败原因为活动解释器缺少 `concurrent-log-handler`，尚未进入现有 cache 用例执行。
- 安全边界：基线测试仅加载本地模块，未迁移 schema、未访问真实数据库、未调用远程服务、未发送业务消息。
- 下一工作包：`P01-W01`。

## P01 ns_common 公共基础设施加固

**阶段状态：`IN_PROGRESS`**  
**目标完成度：`F2`**  
**前置阶段：P00 `VERIFIED`**

### 阶段目标

建立 runtime 后续阶段共同依赖的配置、时间、标识符、退避、脱敏、错误、HTTP 生命周期、观测和测试基础。保持 backend 现有接口兼容，禁止 runtime 深层模块依赖公共层全局单例。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P01-W01` | `VERIFIED` | 扩展 `NsConfig`，增加 runtime 配置总组和组级元数据；配置对象加载完成后转为不可变快照；保留 backend/cache/log 兼容字段 | 配置序列化、加载、未知字段、类型、环境和兼容测试通过 |
| `P01-W02` | `VERIFIED` | 定义配置来源优先级：本地文件、backend 覆盖、运行期已验证快照；记录 source、config_version、policy_version、group_version、effective_at、rollback_from_version 和 apply_mode | 同一配置可还原有效来源；非法覆盖无法生效 |
| `P01-W03` | `VERIFIED` | 建立 runtime 配置组：event_loop、transport、wire_codec、protocol、security、iam、state_store、routing、delivery、worker、pool、tenant_quota、cluster、recovery、observability、logging、debug | 示例配置完整；每组有独立校验和生效模式 |
| `P01-W04` | `VERIFIED` | 建立标准 asyncio event loop selector；支持 auto、asyncio、uvloop；auto 在 Linux 优先 uvloop，在 Windows 使用 asyncio；显式 uvloop 不可用时启动失败 | 平台矩阵测试通过；运行中变更被判定为 restart_required |
| `P01-W05` | `VERIFIED` | 建立统一 TaskSupervisor，负责命名任务、异常收集、取消顺序、关闭超时和未完成任务报告 | 任务异常不会静默丢失；关闭后无悬挂任务 |
| `P01-FIX-01` | `VERIFIED` | 修正 `runtime.cluster.role` 静态启动角色语义，仅允许 singleton、sub_node、standby_master、active_master；旧值、运行期状态和健康状态明确拒绝 | 配置、示例、来源合并和拒绝矩阵通过；不提前实现 P17 角色状态机 |
| `P01-W06` | `VERIFIED` | 建立 Clock 接口：UTC wall clock、monotonic clock、测试可控 clock | timeout、lease、retry 测试不依赖 sleep 漂移 |
| `P01-W07` | `VERIFIED` | 建立 ID 生成和校验规则，覆盖 runtime_id、connection_id、session_id、message_id、summary_id、delivery_id、stream_id、plan_id、operation_id | 格式稳定；无空值；并发生成无冲突 |
| `P01-W08` | `VERIFIED` | 建立通用 retry/backoff 类型，覆盖固定、指数、jitter、预算和下一执行时间计算 | 边界值、预算耗尽和确定性测试通过 |
| `P01-FIX-02` | `VERIFIED` | 修复 retry 数值转换原生异常泄露，并为公开 RetrySchedule 增加严格构造不变量 | 超大数值统一归一化；直接构造和注入返回值负向测试通过；W08 与全量回归通过 |
| `P01-W09` | `VERIFIED` | 建立统一 sanitizer，按字段名、路径和对象类型脱敏 token、payload、auth_context、capabilities、fencing_token、签名 URL、peer address 和证书摘要 | 日志、错误和审计输入的敏感值全部替换或摘要化 |
| `P01-W10` | `NOT_STARTED` | 把 sanitizer 接入 `NsLogger` 的 extra 和 exception 输出路径；禁止 formatter 直接序列化原始 Envelope | 泄露扫描为零；普通日志行为保持兼容 |
| `P01-W11` | `NOT_STARTED` | 扩展 `ns_common.exceptions` 为错误注册表；每个错误包含 code、numeric_code、severity、category、retryable、disconnect_required、audit_required、safe_detail、action | 错误码唯一性、序列化和安全明细测试通过 |
| `P01-W12` | `NOT_STARTED` | 完整登记设计文档已明确的 `RUNTIME_*` 错误，包括协议、IAM、tenant、target、route、payload_ref、ACK/NACK/Defer、lease、fencing、owner、processor、配置、transport 和集群错误 | 错误覆盖矩阵无缺项 |
| `P01-W13` | `NOT_STARTED` | 重构 HTTP client 创建方式，保留现有兼容函数，但新增显式 factory 和 owner 生命周期；runtime 只能接收显式实例 | runtime 测试中不存在全局 client 依赖 |
| `P01-W14` | `NOT_STARTED` | HTTP 错误只保留安全 body 摘要；调用方可提供 response sanitizer；IAM token 不进入 URL、日志和错误明细 | IAM 模拟错误响应不泄露敏感字段 |
| `P01-W15` | `NOT_STARTED` | 建立 MetricsSink、TraceSink、DiagnosticSnapshotSink 接口和内存测试实现；接口不得强制 HTTP exporter | runtime 后续模块可显式注入 sink |
| `P01-W16` | `NOT_STARTED` | 建立 `ns_common.testing` 测试工厂，统一临时目录、临时配置、可控 clock、内存 sink、随机端口和真实 Redis namespace | 测试之间无状态污染 |
| `P01-W17` | `NOT_STARTED` | 建立 runtime 独立依赖清单和测试依赖清单；生产依赖与测试/压测依赖分离 | 安装 backend 不隐式安装 QUIC 实验依赖；runtime 安装可独立完成 |

### 配置硬规则

- `wire_codec.preferred` 固定为 `json.v1`。
- `websocket_tcp.enabled` 初始为 true，但在 P04 完成前 runtime 不对外监听。
- `websocket_http3`、`webtransport_http3`、`quic_native` 初始为 false。
- `zero_rtt` 初始为 false。
- `state_store.backend` 在 local/dev/test 允许 sqlite、redis、valkey；prod 只允许 redis 或 valkey。
- `event_loop` 配置生效模式固定为 restart_required。
- 配置未知字段默认拒绝，不静默忽略拼写错误。

### 测试矩阵

- 配置全量 round-trip。
- 配置未知字段拒绝。
- prod + sqlite state store 拒绝。
- prod + 明文 transport 拒绝。
- Windows auto event loop。
- Linux auto event loop，uvloop 存在与不存在两种环境。
- 显式 uvloop 依赖缺失启动失败。
- TaskSupervisor 异常、取消和关闭超时。
- sanitizer 对嵌套 dict、dataclass、异常 details、URL 和字符串的处理。
- 错误码重复检测。
- HTTP client 生命周期与敏感响应测试。
- 所有原有 `ns_common.cache.tests` 回归通过。

### 阶段出口

- 所有 `COM-001` 至 `COM-009`、`COM-015` 达到 `VERIFIED`。
- backend 现有配置和 IAM 测试无回归。
- runtime 后续模块不需要创建自己的时间、退避、脱敏、错误或观测基础。

### 禁止捷径

- 不把 runtime config 直接写成无类型 dict。
- 不删除现有 backend 兼容入口。
- 不允许 runtime 通过 `get_async_http_client()` 在深层模块获取全局实例。
- 不把 runtime state store 塞入现有 cache client。

### P01-W01 本地验收证据

- 完成时间：`2026-07-16T14:24:37+08:00`。
- 实现：`NsConfig`、backend/cache/log 配置组和新增 runtime 总组均为冻结 dataclass；嵌套 mapping/sequence 转换为深度只读快照；提供 `from_dict()`、`to_dict()`、原子 `save()` 与显式环境校验。
- 兼容：保留 `backend`、`cache`、`log` 属性与 `backend_config`、`cache_config`、`log_config` 旧 JSON/属性入口；backend database/router 调用方改为接受只读 `Mapping`。
- 严格性：顶层、配置组和 metadata 未知字段拒绝；preferred/legacy 重复字段拒绝；字段类型、环境名和已有 prod 安全规则统一返回 `NsConfigError`。
- 配置示例：`etc/ns_config.example.json` 已加入各组 metadata 和 runtime 总组，JSON 解析及本地加载通过。
- W01 测试已迁移到 `tests/test_config.py`；原 13 个 W01 用例保留，并在 W02 完成后随配置测试 24/24 重新通过。
- 当前阶段回归：`S:\PythonVenv\ns_backend\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v`，35/35 通过，包含 11 个 cache 用例。
- 其他检查：`S:\PythonVenv\ns_runtime\Scripts\python.exe -m compileall -q src tests`、两个共享环境的 `pip check`、示例 JSON 校验和 `git diff --check` 均通过。
- 隔离边界：配置测试仅使用临时目录和显式配置路径；未迁移 schema、未访问远程服务、未发送业务消息。
- 后续限制：配置来源覆盖优先级和 metadata 生效语义属于 P01-W02；runtime 细分配置组及其独立校验属于 P01-W03。
- 下一工作包：`P01-W02`。

### P01-W02 本地验收证据

- 完成时间：`2026-07-16T14:47:04+08:00`。
- 来源契约：新增 `NsConfigSource` 与不可变 `NS_CONFIG_SOURCE_PRIORITY`，固定 `local_file < backend_override < validated_snapshot`。
- 解析契约：新增 `NsConfigResolver` 和 `NsConfig.resolve()`；本地文件作为基线，backend 按配置组深度覆盖，显式已验证 `NsConfig` 快照拥有最高优先级。
- 元数据：有效配置持续记录 `source`、`config_version`、`policy_version`、`group_version`、标准化 UTC `effective_at`、`rollback_from_version` 和 `apply_mode`；全局 config/policy version 在配置组之间保持一致。
- 非法覆盖门禁：backend 覆盖必须提供完整权威 metadata；来源伪造、未知组/字段、无版本内容变化、跨组版本冲突、错误 rollback 来源、无时区时间和无效最终配置均整体拒绝，既有输入与不可变快照不被修改。
- 快照恢复：`as_validated_snapshot()` 只产生显式 `validated_snapshot` 来源；resolver 拒绝裸 dict 或未标记的本地配置冒充已验证快照。
- 测试布局：`src` 下测试文件已全部迁移至根目录 `tests/test_config.py`、`tests/test_cache.py`，统一入口为 `python -m unittest discover -s tests -p "test_*.py" -v`。
- W02 配置测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config -v`，24/24 通过，其中 11 个为 W02 来源/版本正负向用例。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，35/35 通过。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、示例配置加载、JSON 校验、测试路径扫描和 `git diff --check` 全部通过。
- 隔离边界：测试只使用临时目录、内存配置和 dummy/临时 SQLite cache；未访问 Redis/Valkey、backend 服务或远程资源。
- 后续限制：W02 只定义来源和 metadata 语义；event_loop、transport、state_store 等 runtime 细分配置及其环境硬规则属于 P01-W03。
- 下一工作包：`P01-W03`。

### P01-W03 本地验收证据

- 完成时间：`2026-07-16T15:27:56+08:00`。
- 类型契约：`NsRuntimeConfig` 新增 event_loop、transport、wire_codec、protocol、security、iam、state_store、routing、delivery、worker、pool、tenant_quota、cluster、recovery、observability、logging、debug 共 17 个冻结 dataclass 细分组；transport adapter 也使用强类型配置，未引入无类型 runtime dict。
- metadata 与来源：每个 runtime 细分组均有独立 `NsConfigGroupMetadata` 和固定生效模式；local_file、backend_override、validated_snapshot 三条路径会保留子组来源、版本和生效时间，旧版只提供 `runtime.metadata` 的输入继续兼容并向未显式配置的子组传播全局来源与版本。
- 安全硬规则：`wire_codec` 只允许 `json.v1`；`websocket_tcp` 默认启用但本工作包不创建监听器；`websocket_http3`、`webtransport_http3`、`quic_native` 和 0-RTT 默认禁用；prod 拒绝 SQLite state store 与未启用 TLS 的 transport。
- 独立校验：覆盖 event loop 模式、transport adapter/优先级/fallback/水位/能力开关、协议版本、IAM URL、state store、路由、投递、worker/pool、tenant quota、cluster lease、recovery、observability、logging 和 debug 边界；未知子组及嵌套字段统一拒绝。
- 配置示例：`etc/ns_config.example.json` 已完整登记 17 个子组、四种 transport adapter、默认值和每组 metadata；示例 JSON 解析及 `NsConfig.load()` 通过。
- 公共契约：新增并导出 17 个 runtime 细分配置类型、`NsRuntimeTransportAdapterConfig`、`RUNTIME_CONFIG_GROUP_NAMES` 与不可变 `RUNTIME_CONFIG_APPLY_MODES`；`COM-001` 保持 `VERIFIED`，`CFG-1` 完成冻结。
- W03 配置测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config -v`，35/35 通过，其中 11 个为 W03 配置组、硬规则、来源和示例配置用例。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，46/46 通过，包含 11 个 cache 用例。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、测试路径扫描和 `git diff --check` 全部通过。
- 隔离边界：测试只使用临时目录、内存配置、示例配置和 dummy/临时 SQLite cache；未启动 transport、未访问 Redis/Valkey、backend 服务或远程资源。
- 后续限制：W03 只定义配置契约；event loop 实现选择、uvloop 依赖探测和平台矩阵属于 P01-W04，runtime 对外监听仍须等待 P04。
- 下一工作包：`P01-W04`。

### P01-W04 本地验收证据

- 完成时间：`2026-07-16T15:42:59+08:00`。
- 公共实现：新增 `src/ns_common/async_runtime.py`，提供冻结的 `NsEventLoopSelection`、`NsEventLoopImplementation`、显式 `NsEventLoopSelector` 以及 `select_event_loop()`、`install_event_loop_policy()`；selector 的平台、模块加载、policy factory、运行中 loop 探测、policy 安装和告警均可显式注入，不依赖全局 `ns_config`。
- 选择语义：显式 `asyncio` 始终使用标准 policy；Windows `auto` 使用标准 asyncio 且不导入 uvloop；Linux `auto` 优先 uvloop，导入、API 或 policy 初始化不可用时回退标准 asyncio 并发出 `NsEventLoopFallbackWarning`；其他平台 auto 保持标准 asyncio 兼容路径。
- 失败语义：Windows 显式 uvloop、非 Windows 显式 uvloop 缺失及 uvloop policy 初始化失败统一启动失败并返回 `NsDependencyError`；不存在静默回退。
- 重启门禁：policy 安装前检查当前运行中的 event loop；运行期间的安装或切换返回 `NsStateError`，稳定携带 `apply_mode=restart_required` 和 `action=restart_required`，且不会调用 policy setter。
- 平台矩阵：真实 Windows auto 路径通过；Windows/Linux/其他平台、Linux uvloop 有/无/初始化失败、显式 asyncio、显式 uvloop 缺失/不支持均通过可注入矩阵测试；测试未改变全局 event loop policy。
- 公共契约：`ns_common.__init__` 新增并导出 `NsEventLoopFallbackWarning`、`NsEventLoopImplementation`、`NsEventLoopSelection`、`NsEventLoopSelector`、`select_event_loop()` 和 `install_event_loop_policy()`；`COM-002` 标记为 `IN_PROGRESS`，其 event loop selector 部分已验证，TaskSupervisor 与优雅关闭仍属 W05/P02。
- W04 专项测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_async_runtime -v`，14/14 通过。
- 配置回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config -v`，35/35 通过。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，60/60 通过，包含 11 个 cache 用例。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、公共导出导入、测试路径扫描和 `git diff --check` 全部通过。
- 隔离边界：W04 原验收时未安装 uvloop、未变更依赖清单、未创建 `src/ns_runtime`、未启动 transport 或外部服务；当时 Linux uvloop 分支通过注入的兼容 policy factory 验证，后续真实 Linux 补验见下节，性能比较仍保留至后续阶段。
- 后续限制：W04 不包含任务监督、取消顺序、关闭超时或悬挂任务报告；这些能力属于 P01-W05。
- 下一工作包：`P01-W05`。

### P01-W04 WSL 补充验收证据

- 补验时间：`2026-07-16T16:05:57+08:00`；只补验已完成的 event loop selector，不改变当前 `P01-W06` 执行游标。
- Linux 环境：WSL2 发行版 `NsServer`，Ubuntu `22.04.5 LTS`，kernel `6.18.33.2-microsoft-standard-WSL2`；Python `3.10.12`，使用既有 `/home/ns/.virtualenvs/ns_runtime/bin/python`，未在仓库或 `/mnt` 工作区创建虚拟环境。
- 环境依赖：在上述隔离环境安装 `requirements-runtime.txt` 与可选 `uvloop==0.22.1`；未修改仓库依赖清单，`python -m pip check` 通过。
- Windows 复验：执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_async_runtime.NsEventLoopSelectorTestCase -v`，14/14 通过，包含真实 Windows auto 使用标准 asyncio 的检查。
- WSL selector 矩阵：在仓库 WSL 映射路径执行 `PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest tests.test_async_runtime.NsEventLoopSelectorTestCase -v`，13 个通过、1 个真实 Windows 专用用例按预期跳过；Linux auto 的 uvloop 可用、缺失和初始化失败分支均通过。
- WSL async runtime 回归：执行 `PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest tests.test_async_runtime -v`，22 个通过、1 个真实 Windows 专用用例按预期跳过，无失败。
- 真实 Linux 选择：默认 `NsRuntimeEventLoopConfig` 在真实 `sys.platform=linux` 下返回 `selected=uvloop`、`reason=auto_linux_uvloop`、`fallback=False`；`install_event_loop_policy()` 安装 `uvloop.EventLoopPolicy`，随后 `asyncio.new_event_loop()` 的实际类型为 `uvloop.Loop`。
- 隔离边界：未启动 transport、backend、Redis/Valkey 或其他外部服务；未修改生产源码和测试，仅改变 `/home/ns/.virtualenvs/ns_runtime` 的已安装包。

### P01-W05 本地验收证据

- 完成时间：`2026-07-16T15:56:02+08:00`。
- 公共实现：在 `src/ns_common/async_runtime.py` 建立显式 `TaskSupervisor`（兼容别名 `NsTaskSupervisor`），不使用全局 singleton 或隐式配置；监督器绑定首次使用的运行中 event loop，拒绝跨 loop 复用。
- 任务登记：`create_task()` 要求真实 coroutine、非空且生命周期内唯一的任务名和整数取消顺序；任务使用 event loop 原生命名，关闭中或关闭后拒绝新任务，拒绝路径会关闭未调度 coroutine，避免资源和警告泄漏。
- 异常语义：done callback 主动消费任务异常并仅登记一次 `NsTaskFailure`；失败列表和可选 failure handler 均可读取异常类型与消息，handler 自身失败交给 event loop exception handler，不会覆盖原始任务失败或静默丢失。
- 取消语义：`shutdown()` 按较小 `cancel_order` 优先、同组按创建顺序发出取消；每个顺序组完成后再进入下一组，取消期间抛出的非取消异常登记为失败。正常关闭完成后不存在 pending 监督任务。
- 超时与报告：关闭使用单一全局 deadline；超时返回冻结的 `NsTaskShutdownReport`，包含总数、完成/取消/失败计数、实际取消顺序、失败和 `NsUnfinishedTask` 快照；未完成快照记录任务名、顺序、创建顺序和监督器发出的取消次数，调用方可观测不配合取消的任务。
- 生命周期门禁：关闭幂等并缓存同一报告；监督任务不得从自身调用所属监督器的 `shutdown()`；关闭后状态固定为 `CLOSED` 并拒绝新任务。
- 公共契约：`ns_common.__init__` 新增并导出 `TaskSupervisor`、`NsTaskSupervisor`、`NsTaskSupervisorState`、`NsTaskFailure`、`NsTaskShutdownReport` 和 `NsUnfinishedTask`；`COM-002` 保持 `IN_PROGRESS`，其 selector 与 TaskSupervisor 部分已验证，进程信号和资源关闭集成仍属 P02。
- W05 专项测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_async_runtime -v`，23/23 通过，其中 9 个用例覆盖 TaskSupervisor 的正常、异常、取消、超时、幂等和跨 loop 路径。
- 配置回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config -v`，35/35 通过。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，69/69 通过，包含 11 个 cache 用例。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、公共导出导入、测试路径扫描和 `git diff --check` 全部通过。
- 隔离边界：未增加外部依赖、未创建 `src/ns_runtime`、未启动 transport、未访问 backend/Redis/Valkey 或远程资源；超时测试在返回报告后显式释放测试内不配合取消的任务。
- 后续限制：W05 只提供公共任务监督原语；进程信号顺序、停止接入以及 sink/client 清理属于 P02-W06，Clock、ID、retry 等其余 P01 公共能力尚未实现。
- 下一工作包：`P01-W06`。

### P01-FIX-01 本地验收证据

- 完成时间：`2026-07-16T16:57:06+08:00`；会话开始时 `git status --short --branch` 显示 `main` 工作区干净，无会话前已有修改；未读取远程仓库、提交记录、PR、Issue 或历史 diff。
- 修改文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、`etc/ns_config.example.json`、`tests/test_config.py` 和本实施文档；设计基线未修改。
- 静态启动角色：`NsRuntimeClusterConfig.role` 默认值为 `singleton`，唯一合法值按稳定顺序登记为 `active_master`、`singleton`、`standby_master`、`sub_node`；公共常量 `RUNTIME_CLUSTER_ROLES` 使用同一顺序，不存在旧值别名或静默映射。
- 角色边界：`singleton` 为单节点启动角色；`sub_node` 保留既有 `active_master_url` 必填 URL 校验；`standby_master` 只表达具备后续竞争资格；配置为 `active_master` 不授予权威写入能力，仍须等待 P17 的 leader lease、epoch 和 fencing 验证。
- 明确拒绝：`standalone`、`master`、`transitioning`、`draining`、`degraded`、`isolated`、`unavailable`、空字符串、未知字符串和非字符串值均在配置构造/校验阶段返回 `NsConfigError`；details 稳定包含 `field=runtime.cluster.role`、原始 `value` 和完整 `allowed_values`。
- 配置行为：覆盖默认值、四个显式角色、序列化、JSON round-trip、保存/重新加载、冻结快照、sub-node 必填字段、backend override 和 validated snapshot 最高优先级；示例配置同步为 `singleton`。
- 配置测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config -v`，40 通过、0 跳过、0 失败。
- 异步基础设施回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_async_runtime -v`，23 通过、0 跳过、0 失败。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，74 通过、0 跳过、0 失败。
- 示例独立加载：runtime 环境调用 `NsConfig.load('etc/ns_config.example.json', environment='local', effective_at='2026-07-16T06:00:00Z')`，得到 `runtime.cluster.role=singleton`。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、角色引用扫描和 `git diff --check` 通过；旧角色字符串只保留在拒绝测试中，Redis standalone 与未来 master 拓扑描述不属于静态 `runtime.cluster.role` 合法值。
- 已知限制：本修复仅冻结静态启动配置，不实现 leader election、leader lease、master epoch、fencing、active/standby 自动切换、transitioning/draining 状态机或集群协调写入。
- 后续独立事项：`runtime.cluster.active_master_url` 的 transport 语义尚未处理、未在本修复中改变，须另行定义和排期。
- 游标恢复：`P01-FIX-01` 已完成全部门禁并标记 `VERIFIED`；当前执行游标恢复到 `P01-W06 建立 Clock 接口`，阶段状态保持 `IN_PROGRESS`。

### P01-W06 本地验收证据

- 完成时间：`2026-07-16T17:01:39+08:00`；W06 只在 P01-FIX-01 完成并恢复游标后开始。
- 修改文件：新增 `src/ns_common/time.py` 和 `tests/test_time.py`，修改 `src/ns_common/__init__.py` 与本实施文档；未修改 Runtime Service、transport、IAM、state store、routing 或 delivery。
- 公共接口：新增 runtime-checkable `Clock` Protocol，统一定义 `utc_now()`、`monotonic()` 和异步 `sleep()`；新增无全局状态的 `SystemClock` 与显式注入用 `ControlledClock`。
- UTC wall clock：`SystemClock.utc_now()` 始终返回 timezone-aware UTC datetime；`ControlledClock` 拒绝 naive/非法 datetime，将有效输入标准化到 UTC，并允许单独设置 wall clock 以模拟系统时间校正而不回退 monotonic。
- 单调时间：`SystemClock` 使用标准库 monotonic clock；`ControlledClock.advance()` 只接受有限非负秒数，同时原子推进 UTC 与 monotonic，拒绝负值、bool、NaN/Infinity 和范围溢出，失败时不改变时钟状态。
- 可控 sleep：测试 sleep 不自动推进时间，只登记 monotonic deadline；`advance()` 按 deadline 和登记顺序释放 due waiter，支持并发 sleeper、取消清理、零秒让出控制权、待处理数量观测和跨 event loop 拒绝，测试无需真实等待或依赖 sleep 漂移。
- 公共导出：`ns_common.__init__` 新增并导出 `Clock`、`SystemClock`、`ControlledClock`、`NsClock`、`NsSystemClock`、`NsControlledClock` 和 `UTC_EPOCH`；`COM-003` 标记为 `VERIFIED`。
- W06 专项测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_time -v`，11 通过、0 跳过、0 失败。
- runtime 联合回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config tests.test_async_runtime tests.test_time -v`，74 通过、0 跳过、0 失败。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，85 通过、0 跳过、0 失败。
- WSL 回归：Ubuntu 22.04.5 WSL2 使用既有 `/home/ns/.virtualenvs/ns_runtime/bin/python` 执行 `PYTHONPATH=src python -m unittest tests.test_time -v`，11 通过、0 跳过、0 失败；未创建新虚拟环境。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、公共导出导入、生产源码测试路径扫描、未跟踪文件尾随空白扫描和 `git diff --check` 通过。
- 已知限制：W06 只建立时间依赖契约和测试时钟，不在本工作包重构既有 config/logger/cache/backend 调用，也不实现 W08 retry、P08 lease 或 P02 RuntimeContext 注入。
- 下一工作包：`P01-W07 建立 ID 生成和校验规则`。

### P01-W07 本地验收证据

- 完成时间：`2026-07-16T17:23:24+08:00`；会话开始时 `main` 工作区干净，无会话前已有修改。
- 修改文件：新增 `src/ns_common/identifiers.py` 和 `tests/test_identifiers.py`，修改 `src/ns_common/__init__.py` 与本实施文档；未修改 backend IAM/JWT 既有 UUID、数据库 session ID 或其他组件标识语义。
- 格式契约：九类 ID 统一为 `<类型前缀>_<32 位小写 RFC 4122 UUIDv4 hex>`；前缀分别为 runtime、connection、session、message、summary、delivery、stream、plan、operation，格式不接受大写、连字符、空白或隐式规范化。
- 类型注册：`NsIdentifierKind`、只读 `IDENTIFIER_PREFIXES`、稳定 `IDENTIFIER_KINDS` 与 `IDENTIFIER_FORMAT` 统一登记 runtime_id、connection_id、session_id、message_id、summary_id、delivery_id、stream_id、plan_id、operation_id，所有前缀唯一。
- 生成契约：显式 `IdentifierFactory` 默认使用标准库 `uuid4()`，允许测试注入 UUID factory，不依赖全局服务；提供通用 `generate_identifier()` 和九个类型专用生成函数，注入源返回非 UUIDv4 时稳定拒绝。
- 校验契约：`parse_identifier()` 返回冻结 `NsIdentifier` 值对象并校验 kind/value/UUID 一致性；`validate_identifier()` 与 `is_valid_identifier()` 支持可选期望类型，错误类型、空值、首尾空白、未知前缀、错误长度/字符、非 v4 UUID 和类型不匹配均不被接受。
- 并发验证：Windows 使用同一 `IdentifierFactory`、16 线程混合生成九类共 9000 个 ID，集合大小保持 9000，全部重新解析有效，无空值或冲突。
- W07 专项测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_identifiers -v`，8 通过、0 跳过、0 失败。
- runtime 联合回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config tests.test_async_runtime tests.test_time tests.test_identifiers -v`，82 通过、0 跳过、0 失败。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，93 通过、0 跳过、0 失败。
- WSL 回归：Ubuntu 22.04.5 WSL2 使用既有 `/home/ns/.virtualenvs/ns_runtime/bin/python` 执行 `PYTHONPATH=src python -m unittest tests.test_identifiers -v`，8 通过、0 跳过、0 失败；未创建新虚拟环境。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、公共导出导入、生产源码测试路径扫描、尾随空白扫描和 `git diff --check` 通过。
- 已知限制：W07 只定义 runtime 公共 ID 格式与生成/校验；尚未创建的 Runtime Service、Envelope、delivery、stream、routing 和 management 模型将在对应阶段显式消费该契约；UUIDv4 ID 不作为凭证或授权证明。
- 下一工作包：`P01-W08 建立通用 retry/backoff 类型`。

### P01-W08 本地验收证据

- 完成时间：`2026-07-16T17:39:14+08:00`；会话开始时 `main` 跟踪 `origin/main`，已有未提交的 P01-W07 变更：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`、`src/ns_common/__init__.py`、`src/ns_common/identifiers.py` 和 `tests/test_identifiers.py`；本工作包保留并在其上继续，未读取远程仓库或提交历史。
- 修改文件：新增 `src/ns_common/retry.py` 和 `tests/test_retry.py`，修改 `src/ns_common/__init__.py` 与本实施文档；未修改设计基线、backend IAM retry 实现、Runtime Service、transport、state store、routing 或 delivery。
- 策略契约：新增 runtime-checkable `BackoffStrategy`，`retry_number` 明确定义为从 1 开始；`FixedBackoff` 提供固定间隔，`ExponentialBackoff` 提供 initial/multiplier/maximum 指数曲线并对超大序号安全封顶，`JitterBackoff` 以装饰器形式提供比例对称 jitter 和可注入随机源。
- 预算契约：新增默认最多自动 retry 5 次的冻结 `RetryBudget`，提供 remaining/exhausted、探测式 `try_consume()` 和严格 `consume()`；预算是持久化权威状态的不可变快照，不提供进程间原子性，未来共享 message 预算必须由 P08 StateStore 原子维护。
- 调度契约：`schedule_next_retry()` 显式接收 `Clock`、delivery 自身的一基 `retry_number` 和 message 级预算快照；成功返回冻结 `RetrySchedule`，同时包含持久化用 UTC `next_retry_at` 和本进程调度用 `monotonic_deadline`，预算耗尽稳定返回 `None`。delivery retry 序号不与共享预算 `used_retries` 隐式绑定。
- 公共导出：`ns_common.__init__` 新增并导出 `BackoffStrategy`、`FixedBackoff`、`ExponentialBackoff`、`JitterBackoff`、`RetryBudget`、`RetrySchedule`、`schedule_next_retry`、对应 `Ns*` 别名、`RandomSource` 和 `DEFAULT_MAX_RETRIES`；`COM-005` 与 `RTY-1` 标记为 `VERIFIED`。
- W08 专项测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_retry -v`，14 通过、0 跳过、0 失败；覆盖固定/指数边界、封顶、确定性 jitter、随机源异常、预算不可变与耗尽、共享预算和 delivery 序号解耦、UTC/单调下一执行时间及自定义策略输出门禁。
- runtime 联合回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config tests.test_async_runtime tests.test_time tests.test_identifiers tests.test_retry -v`，96 通过、0 跳过、0 失败。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，107 通过、0 跳过、0 失败，包含 11 个 cache 用例。
- WSL 回归：本机注册发行版名为 `NsServer`，实际为 Ubuntu 22.04.5 LTS；使用既有 `/home/ns/.virtualenvs/ns_runtime`（Python 3.10.12）执行 `env PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest tests.test_retry -v`，14 通过、0 跳过、0 失败；未创建新虚拟环境。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、公共导出完整性、生产源码测试路径扫描、尾随空白和 `git diff --check` 通过。
- 新增错误码、state key 或 Lua script：无；非法调用参数使用 `NsValidationError`，预算严格消费耗尽、注入源或策略返回非法状态使用 `NsStateError`。
- 已知限制：W08 只建立公共纯策略和值类型，不实现异步 retry executor，不迁移 backend IAM 的既有重试器；priority、tenant 负载、目标健康、manual-only 和基础设施延期策略属于 P12/P14，权威预算原子消费属于 P08。
- 下一工作包：`P01-W09 建立统一 sanitizer`。

### P01-FIX-02 本地验收证据

- 完成时间：`2026-07-16T17:57:27+08:00`；会话开始时本地 `main` 工作区干净；本修复只依据当前本地文件和测试，未查询远程仓库、未读取提交记录。
- 修改文件：`src/ns_common/retry.py`、`tests/test_retry.py` 和本实施文档；未开始 P01-W09，未修改 sanitizer/logger、backend IAM retry、Runtime Service、transport、state store、routing 或 delivery。
- 数值异常归一化：`_finite_number()` 捕获 `float(value)` 的 `OverflowError`、`ValueError` 和 `TypeError`；配置、策略构造和公开值对象直接参数统一返回 `NsValidationError`。注入的 `BackoffStrategy`、`Clock` 和 jitter 随机源返回非法或超大数值时，外层统一转换为带稳定 details 的 `NsStateError`，不泄露原生转换异常。
- RetrySchedule 构造不变量：保持冻结 dataclass；直接构造严格验证 retry_number 为非 bool 正整数、delay 为有限非负数、两个 wall-clock 时间为 timezone-aware UTC、两个 monotonic 值为有限非负数、两类 deadline 均不早于起始时间、UTC/monotonic 时间差在浮点容差内与 delay 一致且 budget 必须为 RetryBudget；有效整数数值规范化为 float，UTC 零偏移值规范化为 `timezone.utc`。
- FIX-02 专项测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_retry -v`，19 通过、0 跳过、0 失败；新增覆盖 `FixedBackoff(10**10000)`、Exponential 三类超大参数、超大 jitter ratio、`float()` 的 ValueError/TypeError、自定义 strategy 和 Clock 的超大返回值、RetrySchedule 全字段非法直接构造及有效对象冻结性。
- runtime 联合回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config tests.test_async_runtime tests.test_time tests.test_identifiers tests.test_retry -v`，101 通过、0 跳过、0 失败。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，112 通过、0 跳过、0 失败。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check` 和 `git diff --check` 通过。
- 基线修正：`etc/ns_config.example.json` 的当前描述已修正为包含 backend/cache/log、runtime 总组及 17 个强类型 runtime 细分组，不再沿用“仅含 backend/cache/log”的过期描述。
- 新增错误码、state key 或 Lua script：无；公共类型名称和导出未变化，`COM-005` 与 `RTY-1` 回归后继续保持 `VERIFIED`。
- 最终状态：`P01-FIX-02` 为 `VERIFIED`；唯一当前游标恢复到 `P01-W09 建立统一 sanitizer`，W09 仍为 `NOT_STARTED`，本修复未继续其开发。

### P01-W09 本地验收证据

- 完成时间：`2026-07-16T18:18:58+08:00`；会话开始时本地 `main` 工作区干净；只依据当前本地设计、实施文档、源码和测试确定范围，未读取远程仓库或提交记录。
- 修改文件：新增 `src/ns_common/security.py` 和 `tests/test_security.py`，修改 `src/ns_common/__init__.py` 与本实施文档；未修改 `src/ns_common/logger.py`、HTTP client、异常注册表、Runtime Service 或其他后续层。
- 公共契约：新增无全局状态的 `Sanitizer`/`NsSanitizer`，以及 `sanitize()`、`sanitize_url()`、`sanitize_text()` 便利入口；输出为与输入分离的 JSON-safe 数据，不修改原对象，并对循环引用和最大遍历深度提供稳定占位符。
- 字段与路径规则：token、authorization、password/secret/private key、payload、auth_context、fencing_token 和签名 URL 完全替换为 `[REDACTED]`；capabilities、peer/client/remote address 与证书 digest/fingerprint 使用截断 SHA-256 不可逆摘要；`payload_ref.url`、`peer.address` 和 `certificate.fingerprint` 等组合路径已验证。
- 对象规则：递归处理 mapping、list/tuple/set、dataclass、普通属性对象、Enum、datetime/path、bytes 和异常；异常仅输出类型、安全 message、code/numeric_code 和经过相同规则处理的 details。
- URL 与文本规则：HTTP(S)/WebSocket URL 删除 userinfo，对 token/signature/credential 等敏感 query 值脱敏并替换 fragment；自由文本处理 Bearer token、敏感键值赋值和内嵌 URL，不把原始敏感值带入结果。
- 公共导出：`ns_common.__init__` 新增并导出 sanitizer 类、三个便利函数及 redaction/circular/max-depth 常量；`COM-006` 与 `SEC-1` 标记为 `VERIFIED`。
- W09 专项测试：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_security -v`，9 通过、0 跳过、0 失败；测试内对 token、payload、auth_context、fencing、capability、URL signature、peer address 和证书摘要原值执行零泄露断言。
- runtime 联合回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config tests.test_async_runtime tests.test_time tests.test_identifiers tests.test_retry tests.test_security -v`，110 通过、0 跳过、0 失败。
- 全量回归：PowerShell 执行 `$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_backend\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v`，121 通过、0 跳过、0 失败。
- WSL 回归：Ubuntu 22.04.5 LTS 的既有 `/home/ns/.virtualenvs/ns_runtime` 执行 `env PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest tests.test_security -v`，9 通过、0 跳过、0 失败；未创建新虚拟环境。
- 其他检查：runtime 环境 `compileall -q src tests`、runtime/backend 两个环境 `pip check`、公共导出完整性、生产源码测试路径、尾随空白和 `git diff --check` 通过。
- 新增错误码、state key 或 Lua script：无；非法 sanitizer 参数沿用 `NsValidationError`。
- 已知限制：W09 只提供显式 sanitizer，不修改 logger formatter；任意无字段名、无路径且无敏感键值标记的自由文本不能可靠推断为秘密，调用方必须提供结构化字段/路径。W10 负责把 sanitizer 接入 logger extra 和 exception 路径并执行完整泄露扫描。
- 下一工作包：`P01-W10 把 sanitizer 接入 NsLogger`。

---

## P02 Runtime 进程生命周期与事件循环

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F2`**  
**前置阶段：P01 `VERIFIED`**

### 阶段目标

建立独立 runtime 进程、显式依赖容器、角色初始状态、启动校验、信号关闭和 event loop 观测。此阶段不建立外部 transport，不开放消息处理。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P02-W01` | `NOT_STARTED` | 建立 `src/ns_runtime` 独立组件和唯一进程入口 `main.py` | 可通过模块方式启动和退出 |
| `P02-W02` | `NOT_STARTED` | 建立 RuntimeService 生命周期：created、starting、running、stopping、stopped、failed | 非法迁移返回稳定错误 |
| `P02-W03` | `NOT_STARTED` | 建立显式 RuntimeContext，持有配置快照、clock、logger、metrics、trace、task supervisor 和后续依赖占位 | 深层模块无全局服务定位器 |
| `P02-W04` | `NOT_STARTED` | 启动时执行环境、依赖、目录、event loop、transport 配置、state store 生产限制和 TLS 前置校验 | 配置错误在监听前失败 |
| `P02-W05` | `NOT_STARTED` | 初始角色状态支持 singleton、sub_node、standby_master、active_master 配置值；实际协调能力保持 feature disabled | 角色值可加载，未完成能力不伪装为可用 |
| `P02-W06` | `NOT_STARTED` | 实现 SIGINT/SIGTERM 优雅关闭顺序：停止接入、停止新任务、取消后台任务、关闭 sink/client、输出未完成任务摘要 | 重复关闭幂等；关闭超时可观测 |
| `P02-W07` | `NOT_STARTED` | 建立 event loop lag 采样和 implementation 指标 | asyncio/uvloop 指标可读取 |
| `P02-W08` | `NOT_STARTED` | 建立本地进程诊断命令，只读取启动配置和本地状态，不开 HTTP 管理端口 | 可判断配置是否合法和进程依赖是否齐全 |

### 测试矩阵

- 空配置、非法配置、缺失依赖、prod 安全错误。
- 标准 asyncio 启动/停止。
- uvloop 启动/停止。
- 后台任务异常触发 RuntimeService failed 或受控降级。
- SIGTERM 期间重复调用 stop。
- 关闭过程中 sink 或 client 抛异常仍完成资源清理。
- 未实现 transport、cluster、delivery 功能查询返回 feature disabled。

### 阶段出口

- runtime 独立进程可以无监听启动并完成自检后优雅退出。
- event loop implementation 和 loop lag 可通过内部 snapshot 读取。
- 所有 runtime 核心依赖通过构造注入。

---

## P03 Envelope 协议层与类型注册表

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F2`**  
**前置阶段：P02 `VERIFIED`**

### 阶段目标

一次性建立统一 `json.v1` Envelope、主版本严格/次版本兼容、核心字段拒绝、内置 message type 注册和标准错误 Envelope。未完成业务类型只注册契约并保持 feature disabled。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P03-W01` | `NOT_STARTED` | 定义核心分组 protocol、message、source、target、route、delivery、stream、auth_context、payload、callback、trace、extensions 的类型模型 | 所有分组有严格字段集合 |
| `P03-W02` | `NOT_STARTED` | 建立 inbound raw model 与 normalized model 分离；inbound 不允许 source/auth_context；normalized 由 runtime 注入 | 伪造测试全部拒绝 |
| `P03-W03` | `NOT_STARTED` | 建立 JSON 深度、总大小、字符串长度、数组长度和数字范围限制 | 资源消耗攻击被拒绝 |
| `P03-W04` | `NOT_STARTED` | 建立基础 schema + message.type schema 叠加校验 | 类型专属字段缺失时返回稳定错误 |
| `P03-W05` | `NOT_STARTED` | 建立协议版本模型、兼容矩阵、minor/patch 降级和 schema 选择 | processor 不需要判断协议版本 |
| `P03-W06` | `NOT_STARTED` | 建立内置 message type 全量注册表，覆盖 connection、task、delivery、stream、runtime.control、cluster.event、config、dead_letter、replay、cancel、hold、status、runtime.error | 设计要求的类型族无缺项 |
| `P03-W07` | `NOT_STARTED` | 每个注册项包含 schema、category、默认 reliability、权限声明、processor key、审计级别、feature flag 和响应类型 | 注册完整性测试通过 |
| `P03-W08` | `NOT_STARTED` | 建立 extension namespace 注册和 schema 校验；未注册 namespace 按策略拒绝或审计忽略 | 插件无法放宽核心字段 |
| `P03-W09` | `NOT_STARTED` | 建立标准错误 Envelope，安全 detail 只来自错误注册表和 sanitizer | 错误不携带原始异常或敏感值 |
| `P03-W10` | `NOT_STARTED` | 建立 canonical serialization 规则，用于 checksum、审计摘要和确定性测试 | 相同 normalized Envelope 序列化稳定 |
| `P03-W11` | `NOT_STARTED` | 为未实现 message type 建立统一 FeatureDisabledProcessor 占位行为；该行为只返回错误，不执行功能 | 不存在 stub success |

### 协议测试矩阵

- 所有顶层未知字段拒绝。
- 所有核心分组未知字段拒绝。
- 不适用分组为空对象或 null 时按 schema 拒绝。
- inbound source/auth_context 拒绝并标记严重安全错误。
- tenant 自报和 capability 提权请求不得进入 normalized 权威上下文。
- major 不兼容拒绝。
- minor/patch 兼容矩阵选择正确 schema。
- 未注册 message.type 拒绝。
- 已注册但 feature disabled 返回稳定错误。
- extension namespace 未注册、禁用、schema 失败和已授权四类路径。
- 过深 JSON、过大帧、超长字段和数组爆炸测试。
- 错误 Envelope 本身必须符合 Envelope schema。

### 阶段出口

- 所有后续消息都只能通过 Envelope codec 进入 runtime。
- 内置类型注册完整，但只有协议错误处理功能处于 enabled。
- 协议模型不依赖具体 transport。

---

## P04 Transport 抽象与 WebSocket/TCP Adapter

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F2`**  
**前置阶段：P03 `VERIFIED`**

### 阶段目标

建立 transport adapter 标准契约和当前正式 `websocket_tcp` 实现。adapter 只处理传输连接、消息边界、队列、原生存活检测和标准化错误，不处理 IAM、Envelope 业务、路由或 DeliveryRecord。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P04-W01` | `NOT_STARTED` | 定义 TransportAdapter、TransportSession、TransportMessage、TransportClose、TransportError、TransportCapabilities 契约 | 上层不引用 WebSocket 库对象 |
| `P04-W02` | `NOT_STARTED` | 定义 capability 集合并为 websocket_tcp 声明 reliable_ordered_messages、native_keepalive、transport_flow_control 基础能力 | capability 由 adapter 权威声明 |
| `P04-W03` | `NOT_STARTED` | 实现 WebSocket TLS/TCP 监听、连接接受、文本消息接收、发送、ping/pong、关闭和异常映射 | conformance 正常路径通过 |
| `P04-W04` | `NOT_STARTED` | 强制 WebSocket 只接受文本帧；二进制帧返回协议错误或关闭 | 二进制负向测试通过 |
| `P04-W05` | `NOT_STARTED` | 建立单 transport session 读队列和写队列；限制消息大小和队列容量 | 队列满不无限等待 |
| `P04-W06` | `NOT_STARTED` | 建立 transport_connection_id、transport_session_id、transport_stream_id、peer 摘要和 path 初始模型 | 诊断字段与 logical connection 分离 |
| `P04-W07` | `NOT_STARTED` | 建立 transport error 到 `RUNTIME_TRANSPORT_*` 的映射 | 所有库异常被收敛 |
| `P04-W08` | `NOT_STARTED` | 建立 adapter registry；未启用 adapter 不加载依赖、不监听端口 | QUIC 依赖不会影响当前启动 |
| `P04-W09` | `NOT_STARTED` | 建立 transport conformance 测试套件，未来所有 adapter 必须复用 | WebSocket adapter 全部通过 |
| `P04-W10` | `NOT_STARTED` | 记录通用 transport 指标：连接数、握手耗时、收发字节、队列深度、发送失败、关闭原因、背压时长 | 指标标签不含高基数 ID |

### 测试矩阵

- TLS 和开发明文模式。
- prod 明文监听拒绝。
- 文本帧、二进制帧、过大帧、非法 UTF-8。
- 慢读、慢写、写队列满、读队列满。
- ping/pong 超时和异常关闭。
- adapter close 幂等。
- transport 发送成功不触发任何 runtime AckRecord。
- 未启用的 HTTP/3、WebTransport、QUIC 配置不加载第三方库。

### 阶段出口

- transport 可以建立连接并把完整文本消息交给上层。
- 上层尚不接受业务消息；连接在 P05 握手完成前只能进入 handshaking。
- conformance 契约冻结为 `TC-1`。

---

## P05 逻辑连接、会话、握手、心跳与 Resume

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P04 `VERIFIED`**

### 阶段目标

建立 logical connection、session、握手状态机、本地索引、双层心跳、drain、关闭和 reconnect grace。IAM 先使用 P06 提供的明确测试 adapter；P06 完成前普通生产连接保持禁用。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P05-W01` | `NOT_STARTED` | 建立连接状态机 accepted、handshaking、authenticated、active、draining、closing、closed 和失败原因 | 非法迁移测试覆盖 |
| `P05-W02` | `NOT_STARTED` | 第一条有效应用消息强制为 connection.hello；握手超时后关闭 | 非 hello 消息无法进入 processor |
| `P05-W03` | `NOT_STARTED` | 解析 hello 中 token、component_type、协议版本、requested capabilities 和 resume 请求；token 只保留在握手受控内存 | token 不进入普通日志和 session snapshot |
| `P05-W04` | `NOT_STARTED` | 完成协议版本和 transport capability 协商并写入 SessionContext | 后续 codec 使用协商结果 |
| `P05-W05` | `NOT_STARTED` | 建立 logical connection、transport session、network path 三层映射 | connection_id 不等于 transport ID |
| `P05-W06` | `NOT_STARTED` | 建立 connection_id、identity、tenant、component_type、capability、session_id 本地索引 | 索引增删原子且无悬挂引用 |
| `P05-W07` | `NOT_STARTED` | connection.accepted 只返回规定的最小字段 | 不泄露 tenant、identity 和完整 capabilities |
| `P05-W08` | `NOT_STARTED` | 建立 transport 原生心跳和 envelope heartbeat；envelope heartbeat 经过轻量 processor，不创建 DeliveryRecord | 双层心跳行为可区分 |
| `P05-W09` | `NOT_STARTED` | 建立 connection.drain 单向状态；停止新目标分配，保留 ACK/control/health | drain 不可取消 |
| `P05-W10` | `NOT_STARTED` | 普通网络断开进入默认 30s grace；grace 内 connection 不作为 active target | 路由索引立即移除 active 属性 |
| `P05-W11` | `NOT_STARTED` | resume 必须重新 IAM 校验并匹配 identity、tenant、component_type；成功递增 connection_epoch | 旧 epoch 消息全部拒绝 |
| `P05-W12` | `NOT_STARTED` | kick、安全违规、协议严重错误和恶意重复确认设置不可恢复关闭标志 | resume 请求被拒绝并审计 |
| `P05-W13` | `NOT_STARTED` | 建立 connection.reauth、accepted/rejected 语义和 session 到期策略接口 | 续期失败不会无限信任旧权限 |
| `P05-W14` | `NOT_STARTED` | 会话快照异步输出；resume/kick/security close 强审计接口预留 | 普通 heartbeat 不进入强一致链路 |

### 测试矩阵

- hello 超时、hello 非第一条消息、重复 hello。
- 协议不兼容、capability 不兼容。
- accepted 响应字段白名单。
- identity 多连接索引。
- drain 后新投递目标不可选、已有控制消息仍可处理。
- 网络断开、grace 内 resume、grace 过期。
- 旧 connection_epoch 发送普通消息、ACK、NACK、Defer。
- kick 和安全关闭禁止 resume。
- heartbeat 不创建 DeliveryRecord。
- 同一 runtime path 更新不递增 connection_epoch 的模型测试。

### 阶段出口

- 使用测试 IAM adapter 时，连接生命周期达到 F3。
- 生产 IAM 未完成前，prod 启动只能接受受控 management/runtime 测试身份或直接拒绝普通连接。
- SessionContext 契约冻结为 `SC-1`。

---

## P06 IAM、安全上下文与 backend 合同补齐

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P05 `VERIFIED`**

### 阶段目标

把现有 `ns_backend.iam` 内部接口扩展为 runtime 所需的完整身份、tenant、component_type、capability、权限快照、TTL、节点凭证和失效语义，并在 runtime 中实现严格模式与缓存模式。

### backend 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P06-B01` | `NOT_STARTED` | 扩展 principal 类型：frontend_user、backend_service、client、node、runtime_node、management | introspection contract 覆盖全部组件 |
| `P06-B02` | `NOT_STARTED` | introspection 返回 identity、tenant_id、component_type、capabilities、permission_snapshot_ref、permission_version、issued_at、expires_at、credential status | runtime 无需猜测 tenant 和能力 |
| `P06-B03` | `NOT_STARTED` | 校验客户端声明 component_type 和 requested capabilities；最终值由 IAM 裁决 | 客户端自报不能提权 |
| `P06-B04` | `NOT_STARTED` | 建立 runtime node credential 签发、刷新、撤销和 role scope | 节点凭证独立于用户 access token |
| `P06-B05` | `NOT_STARTED` | 建立 runtime bootstrap 合同，返回角色授权、候选 master、配置版本和策略版本 | runtime 启动可获取控制面信息 |
| `P06-B06` | `NOT_STARTED` | access_check 支持 runtime message.type、target、cross-tenant、management 和 task creation 上下文 | 权限决策可审计和解释 |
| `P06-B07` | `NOT_STARTED` | 建立权限版本失效事件或轮询版本合同 | 缓存模式可感知撤销 |
| `P06-B08` | `NOT_STARTED` | 建立 payload_ref validation 合同，覆盖对象、版本、checksum、tenant、owner、source、target、过期、撤销和 callback | P10 可直接接入 |

### runtime 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P06-R01` | `NOT_STARTED` | 建立显式 IamClient，使用 P01 HTTP factory；所有请求携带 trace 和内部服务凭证 | 无全局 client |
| `P06-R02` | `NOT_STARTED` | 建立 handshake authentication 流程和安全超时 | IAM 不可用按配置拒绝或受限降级 |
| `P06-R03` | `NOT_STARTED` | 建立 PermissionSnapshot，普通 Envelope 只注入最小 auth_context 摘要 | 不保存原始 IAM 返回体 |
| `P06-R04` | `NOT_STARTED` | 严格消息鉴权每条调用 backend；缓存模式按 TTL、version 和失效事件刷新 | 两种模式行为一致可解释 |
| `P06-R05` | `NOT_STARTED` | tenant 硬校验在 processor 前执行；操作权限在通用鉴权 processor 执行 | 安全硬校验与业务权限分层 |
| `P06-R06` | `NOT_STARTED` | 建立本地凭证缓存加密、TTL、签名校验和 role scope 校验 | 明文凭证不落盘 |
| `P06-R07` | `NOT_STARTED` | 建立 backend 不可用降级矩阵，禁止高风险控制、跨 tenant、新配置和全局协调写入 | 降级能力受限且可审计 |
| `P06-R08` | `NOT_STARTED` | backend 恢复后重新验证凭证、角色、配置、lease、fencing 和 session snapshot | 不自动沿用过期授权 |

### 安全测试矩阵

- 每种 principal 的合法和非法 token。
- component_type 冒充、capability 提权和 tenant 篡改。
- 严格模式每条消息调用 IAM。
- 缓存模式 TTL、version 更新、撤销事件和失效回退。
- IAM 超时、5xx、非法响应和响应字段缺失。
- 本地凭证加密、篡改、过期和撤销。
- backend 不可用时高风险管理操作全部拒绝。
- source/auth_context 注入最小化。
- IAM 请求和日志无 token 泄露。

### 阶段出口

- 普通连接生产鉴权可用。
- SessionContext identity/tenant/component/capability 全部来自 IAM。
- runtime 与 backend IAM 合同冻结为 `IAM-R1`。

---

## P07 Processor 流水线、插件、事件与审计

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P06 `VERIFIED`**

### 阶段目标

所有 Envelope 统一进入可追踪、可超时、可审计的 processor pipeline；事件总线只做旁路通知和唤醒，不作为状态权威。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P07-W01` | `NOT_STARTED` | 定义 ProcessorContext，包含 normalized Envelope、session、trace、config/policy version、clock 和显式服务依赖 | context 不含隐藏全局访问 |
| `P07-W02` | `NOT_STARTED` | 定义通用阶段顺序：安全硬校验、权限、限流入口、幂等预检、审计标记、路由预处理、message processor、响应收尾 | 顺序固定并可测试 |
| `P07-W03` | `NOT_STARTED` | processor registry 按 message.type、阶段、协议版本、feature flag 注册 | 重复和冲突注册启动失败 |
| `P07-W04` | `NOT_STARTED` | processor 执行支持 timeout、取消、异常隔离、标准错误映射和最终审计 | 未捕获异常不泄露原始内容 |
| `P07-W05` | `NOT_STARTED` | 审计 sink 记录一次最终处理结果；包含安全摘要、processor、action、error、trace、config/policy version | 每条可执行消息恰好一个最终审计结果 |
| `P07-W06` | `NOT_STARTED` | 高风险控制审计接口标记为强一致，普通 processor 审计先使用显式 sink；P08 后接 state store | 不把强审计误标为 best-effort |
| `P07-W07` | `NOT_STARTED` | 内部 EventBus 支持类型化事件、订阅、超时和异常隔离 | 订阅者失败不影响主链路 |
| `P07-W08` | `NOT_STARTED` | 事件发布只携带安全摘要和对象 ID；禁止携带原始 token/payload | 事件泄露扫描为零 |
| `P07-W09` | `NOT_STARTED` | 插件发现只加载本地受信任插件；插件声明 namespace、schema、权限、timeout、状态 namespace 和 feature flag | 未授权插件无法加载 |
| `P07-W10` | `NOT_STARTED` | health、heartbeat、reauth、drain 和 feature disabled processor 完整接入 pipeline | 不存在直接 transport 回调处理业务 |

### 测试矩阵

- processor 顺序固定。
- 某阶段 reject 后后续 processor 不执行。
- timeout、取消、异常和错误映射。
- 每条消息最终审计恰好一次。
- 审计 sink 失败时高风险和普通消息的差异策略。
- 插件重复类型、未授权 namespace、超时和异常隔离。
- EventBus 丢事件不影响权威状态。
- ACK、管理、health 尚未实现功能仍必须通过 pipeline。

### 阶段出口

- 所有当前启用消息完整经过 pipeline。
- processor 契约冻结为 `PC-1`。
- P08 之后所有状态修改只能由 processor 调用明确 service，再由 state store 原子执行。

---

## P08 强一致 State Store 与原子原语

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P07 `VERIFIED`**

### 阶段目标

在 `ns_common.state_store` 建立严格失败的生产状态存储。Redis/Valkey 提供 Hash、ZSet、Stream/Log、Lua、lease、fencing、CAS 和 namespace。SQLite WAL 只提供开发语义并明确能力差异。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P08-W01` | `NOT_STARTED` | 定义 StateStoreCapabilities，显式声明 transaction、CAS、lease、fencing、ordered queue、priority queue、secondary index、append log、batch、TTL | 上层能拒绝不满足的 backend |
| `P08-W02` | `NOT_STARTED` | 定义严格 StateStore 接口；任何异常向上抛出，不软失败 | 关键写入无法伪成功 |
| `P08-W03` | `NOT_STARTED` | 定义 namespace 和 key builder，强制 tenant/system/runtime/plugin/audit/delivery/routing 维度 | 跨 namespace 访问被拒绝 |
| `P08-W04` | `NOT_STARTED` | 实现 Redis adapter，支持 standalone、Sentinel、Cluster 配置 | 集成测试覆盖三种配置解析 |
| `P08-W05` | `NOT_STARTED` | 实现 Valkey adapter，与 Redis 保持契约但单独验证客户端行为 | conformance 全部通过 |
| `P08-W06` | `NOT_STARTED` | 实现 SQLite WAL adapter；标记不具备生产分布式权威能力 | prod 启动硬拒绝 |
| `P08-W07` | `NOT_STARTED` | 实现 Lua script registry、版本、checksum、预加载、NOSCRIPT 恢复和执行指标 | 脚本版本可追踪 |
| `P08-W08` | `NOT_STARTED` | 实现通用 lease acquire/renew/release、epoch 和 fencing token 原语 | 旧 token 写入被拒绝 |
| `P08-W09` | `NOT_STARTED` | 实现原子 Hash + ZSet + Stream 同槽迁移原语 | 不存在半更新 |
| `P08-W10` | `NOT_STARTED` | 实现 idempotency registry、TTL、批量写和 compare-and-set | 并发请求只有一个获胜 |
| `P08-W11` | `NOT_STARTED` | 固定 Redis Cluster hash tag 为 tenant_id + bucket_id；bucket 使用稳定哈希和配置版本 | bucket_count 变化不修改旧 key |
| `P08-W12` | `NOT_STARTED` | 建立 state store conformance 和 Lua 原子测试套件 | Redis、Valkey、SQLite 按能力分别通过 |
| `P08-W13` | `NOT_STARTED` | 建立存储不可用健康状态和 RuntimeService 降级通知 | 关键链路停止而非软降级 |

### 原子测试矩阵

- 多协程同时 acquire lease 只有一个成功。
- lease renew 后 epoch 不变，重新 acquire 后 fencing 单调增加。
- 旧 fencing、旧 owner、过期 lease 写入拒绝。
- Hash 更新、ZSet 删除、Stream 追加同成同败。
- 脚本执行中参数错误不留下部分状态。
- Redis restart、连接断开、NOSCRIPT 和超时。
- Cluster cross-slot 设计检查。
- SQLite 多进程模拟中的已声明弱语义测试。
- prod + sqlite 启动失败。

### 阶段出口

- `COM-010` 至 `COM-013` 达到 `VERIFIED`。
- cache 与 state store 完全分离。
- 所有后续可靠状态只允许通过 StateStore service 写入。

---

## P09 路由、RoutingPlan 与本地目标选择

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P08 `VERIFIED`**

### 阶段目标

建立 target 解析、候选过滤、策略裁决、评分和不可变 RoutingPlan。此阶段不发送可靠消息。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P09-W01` | `NOT_STARTED` | 实现 connection、identity、tenant、capability、component_type、runtime、broadcast target 校验 | 各 kind 的必填字段严格验证 |
| `P09-W02` | `NOT_STARTED` | 建立候选集合，从本地 session index 读取 active 连接并过滤 tenant、component、capability、draining、epoch | grace/draining 连接不可作为新目标 |
| `P09-W03` | `NOT_STARTED` | 建立 target strategy：single、all、broadcast、quorum、all_required、weighted_subset、no_rebind | 多目标必须有明确策略痕迹 |
| `P09-W04` | `NOT_STARTED` | capability 默认单目标；tenant/broadcast 只在显式策略下多目标 | 防止隐式广播 |
| `P09-W05` | `NOT_STARTED` | 建立 rebinding 策略：fixed_connection、same_identity、same_capability、same_tenant、no_rebind_for_control | fixed connection 不自动降级 |
| `P09-W06` | `NOT_STARTED` | 建立 fallback scorer，使用稳定确定性输入；记录 scorer 来源 | 同一快照决策可复现 |
| `P09-W07` | `NOT_STARTED` | RoutingPlan 记录原始 target、候选、过滤、评分、拒绝、最终目标、策略版本、local hit、stale 标记 | plan 可解释 |
| `P09-W08` | `NOT_STARTED` | RoutingPlan 不可变；重试或策略变化生成新 version | 历史 plan 不被修改 |
| `P09-W09` | `NOT_STARTED` | 关键消息计划强一致存储接口，普通消息摘要接口 | 一致性等级由策略明确 |
| `P09-W10` | `NOT_STARTED` | 本地 miss 返回 routing unavailable；不使用 stale cache | 默认行为符合设计 |

### 测试矩阵

- 每种 target kind 正常和错误输入。
- 多连接 identity 的 single/all 策略。
- fixed_connection miss 不降级。
- tenant 越界和跨 tenant 授权。
- draining、grace、旧 epoch、capability 不匹配过滤。
- RoutingPlan 不可变和 version 递增。
- 评分相同目标的稳定 tie-break。
- 管理控制默认 no_rebind。

### 阶段出口

- 本地目标决策达到 F3。
- 不发生 transport 写入。
- RoutingPlan 契约冻结为 `RP-1`。

---

## P10 受理、Summary、去重与 Payload Reference

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P09 `VERIFIED`**

### 阶段目标

完成可靠消息受理边界：策略裁决、payload 校验、去重、Summary 初始化、prepared DeliveryRecord 原子创建和轻量受理响应。此阶段创建状态但不启用发送 worker。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P10-W01` | `NOT_STARTED` | 定义 MessageDeliverySummary 和 DeliveryRecord 权威字段、状态和版本 | 字段覆盖 owner、fencing、expiry、target、payload 摘要 |
| `P10-W02` | `NOT_STARTED` | 受理时裁决 priority、reliability、expires_at、ack timeout、target strategy 和 policy version | 发送方值只作为请求 |
| `P10-W03` | `NOT_STARTED` | inline payload 执行大小、深度和摘要校验；完整 payload 不写强一致状态 | state dump 无业务明文 |
| `P10-W04` | `NOT_STARTED` | PayloadRefClient 实时调用 backend IAM/object validation 合同 | 明确无效直接 rejected |
| `P10-W05` | `NOT_STARTED` | 校验服务不可用时按消息策略进入 reject、wait 或 dead letter，不允许绕过 | 安全确认无缓存授权 |
| `P10-W06` | `NOT_STARTED` | 建立 `message_id + target_fingerprint` tenant 去重登记 | 并发重复只产生一个受理结果 |
| `P10-W07` | `NOT_STARTED` | 重复命中 acked、in_progress、dead/expired/cancelled 分别返回稳定语义 | 不自动重投终态 |
| `P10-W08` | `NOT_STARTED` | 全部 rejected 仍创建 failed summary，不创建 DeliveryRecord | 管理端可解释失败 |
| `P10-W09` | `NOT_STARTED` | 关键消息 summary + 初始 prepared delivery 原子写入 | 失败不留下孤儿 delivery |
| `P10-W10` | `NOT_STARTED` | 大 fanout 超过 5000 targets 时分片；bucket 1000、初始化批次 500 | root/shard summary 一致 |
| `P10-W11` | `NOT_STARTED` | initializing 期间 delivery 只处于 prepared，禁止发送和占 active/inflight | worker 无法 claim prepared |
| `P10-W12` | `NOT_STARTED` | 初始化失败批量取消已 prepared，记录 not_initialized | summary 可解释 |
| `P10-W13` | `NOT_STARTED` | delivery.accepted 只返回 message_id、summary_id、accepted_at、status_query_hint、trace | 不返回大量 delivery_id |
| `P10-W14` | `NOT_STARTED` | 受理响应发送失败不回滚已受理状态 | 断连后生命周期继续 |

### 测试矩阵

- 已过期和剩余窗口不足。
- inline 超限和 payload_ref 全部失败类别。
- payload_ref 服务超时和依赖异常。
- 并发去重、已 acked 重复、进行中重复和终态重复。
- 全部 rejected、部分 rejected、全部 accepted。
- fanout 分片边界 4999/5000/5001。
- 初始化中取消。
- summary + delivery 原子失败回滚。
- 受理响应写失败。

### 阶段出口

- 可可靠受理但不发送。
- task.dispatch feature 仍不对外启用，直到 P12 完成 ACK 闭环。
- Summary/DeliveryRecord 初始模型冻结为 `DR-1`。

---

## P11 本地可靠投递调度与发送

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P10 `VERIFIED`**

### 阶段目标

建立 prepared 激活、queued claim、delivery lease、sending、transport 写入和 ack_waiting 状态。只支持本地目标和单 runtime owner。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P11-W01` | `NOT_STARTED` | prepared 激活器按批次、priority、tenant 和水位执行 prepared -> queued | 不一次性激活大 fanout |
| `P11-W02` | `NOT_STARTED` | ClaimWorker 从权威队列 claim queued delivery 并获取 15s lease | 多 worker 只有一个 owner |
| `P11-W03` | `NOT_STARTED` | LeaseRenewWorker 每 5s 续约；连续失败超过 2 次进入 owner risk | 风险 worker 停止新高风险写入 |
| `P11-W04` | `NOT_STARTED` | SendWorker 校验 owner、lease、fencing、connection_epoch、target active、payload_ref 和策略版本 | 发送前不使用过期状态 |
| `P11-W05` | `NOT_STARTED` | queued -> sending 原子迁移并创建 DeliveryAttempt | attempt 与状态一致 |
| `P11-W06` | `NOT_STARTED` | sending 开始计算 ack deadline，写操作有超时 | 慢写不拖死 worker |
| `P11-W07` | `NOT_STARTED` | transport 写成功后原子进入 ack_waiting；不保留 sent 状态 | 写成功不等于 acked |
| `P11-W08` | `NOT_STARTED` | 写失败交给策略结果接口，暂只支持 retry_scheduled/dead_lettered/expired/cancelled | 状态迁移可解释 |
| `P11-W09` | `NOT_STARTED` | owner risk 保护窗口使用配置 3-5s，只允许在途确认尝试 | 不形成新 lease |
| `P11-W10` | `NOT_STARTED` | 终态或 retry_scheduled 释放 active/write slot；ack_waiting 占 inflight | 资源计数准确 |
| `P11-W11` | `NOT_STARTED` | 启用本地 task.dispatch feature，但只有完整受理和发送状态；发送方接受不代表 delivery 成功 | ACK 闭环在 P12 前标记为实验禁用生产 |

### 测试矩阵

- 多 worker 并发 claim。
- lease 续约、过期和旧 worker 写入。
- 目标断开、旧 epoch、draining、写队列满。
- 写超时、session close、transport error。
- queued 不等于 connection 写队列。
- 写成功只进入 ack_waiting。
- worker 取消和 runtime 关闭后的状态恢复性。
- prepared 批量激活的水位限制。

### 阶段出口

- 本地可靠消息能到达目标并进入 ack_waiting。
- 不具备 ACK 前不得标记生产可用。

---

## P12 ACK、NACK、Defer、Timeout 与自动 Retry

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P11 `VERIFIED`**

### 阶段目标

完成本地可靠投递闭环和自动恢复路径。ACK/NACK/Defer 全部是 Envelope 和 processor，不存在快速通道。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P12-W01` | `NOT_STARTED` | ACK processor 校验 tenant、sender、target、owner、fencing、delivery state、connection_epoch | 非预期确认方拒绝 |
| `P12-W02` | `NOT_STARTED` | 第一次合法 ACK 原子写 AckRecord、DeliveryRecord acked、删除 timeout/retry index、更新 summary | 不存在无 AckRecord 的 acked |
| `P12-W03` | `NOT_STARTED` | 重复 ACK 只写安全审计和指标，不新增主记录 | AckRecord 唯一 |
| `P12-W04` | `NOT_STARTED` | retry_scheduled 收到合法迟到 ACK 可原子转 acked并取消 retry | 不发生 ACK 后重发 |
| `P12-W05` | `NOT_STARTED` | NACK processor 写 NackRecord 并按 reason 分类执行 retry/reroute/dead/security | NACK 不算 ACK |
| `P12-W06` | `NOT_STARTED` | NACK reason 映射到完整 `RUNTIME_*` 错误和四类语义 | 未知 reason 拒绝 |
| `P12-W07` | `NOT_STARTED` | Defer processor 从 sending、ack_waiting、retry_scheduled 生效，原子写 DeferRecord 和 deadline | retry_scheduled defer 回到 ack_waiting |
| `P12-W08` | `NOT_STARTED` | Defer 默认最多 3 次、单次 5s、总计 15s；超预算按 timeout | 预算无法绕过 |
| `P12-W09` | `NOT_STARTED` | AckTimeoutWorker 只扫描过期 ack_waiting；过期消息进入 expired，否则 retry_scheduled | 不处理其他状态 |
| `P12-W10` | `NOT_STARTED` | RetryWorker 只扫描 due retry_scheduled，重算 RoutingPlan、priority、pool、payload_ref 和水位 | 不伪造成新入站消息 |
| `P12-W11` | `NOT_STARTED` | 自动 retry message 级默认预算 5 次；指数 1/2/4/8/16s + jitter + health 调整 | 预算共享且历史不清零 |
| `P12-W12` | `NOT_STARTED` | target/session 恢复事件仅做提前唤醒，worker 仍重新读权威状态 | EventBus 丢失不影响周期扫描 |
| `P12-W13` | `NOT_STARTED` | 更新 connection/identity/component/runtime/tenant health 基础信号 | 健康只影响评分和节奏 |
| `P12-W14` | `NOT_STARTED` | 本地 task.dispatch 生产 feature 在本阶段出口后启用 | 全链路 ACK 测试通过 |

### 测试矩阵

- 合法 ACK、重复 ACK、迟到 ACK、旧 epoch ACK、错误 target ACK。
- ACK 与 timeout 并发、ACK 与 retry claim 并发。
- 所有 NACK reason 类别。
- NACK 后迟到 ACK。
- Defer 次数、单次和总预算。
- Defer 与 timeout 并发。
- ACK timeout 与 expires_at 区分。
- retry budget 多 delivery 共享。
- retry 前 route 和 payload_ref 复验。
- 进程重启后 retry index 恢复。

### 阶段出口

- 单 runtime、本地目标、可靠 task.dispatch 达到 F3。
- ACK 语义和状态机冻结为 `ACK-1`。

---

## P13 Dead Letter、Replay、Cancel 与 Hold

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P12 `VERIFIED`**

### 阶段目标

建立异常终态、人工恢复、管理取消和冻结语义，保证所有管理操作强鉴权、强审计和原子状态迁移。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P13-W01` | `NOT_STARTED` | retry 预算耗尽进入 dead_lettered；expires_at 到期进入 expired | 两类终态不混淆 |
| `P13-W02` | `NOT_STARTED` | DeadLetterRecord 分为 replayable、not_replayable、manual_confirm_required | reason 完整可解释 |
| `P13-W03` | `NOT_STARTED` | dead letter scanner 只登记 dead_lettered，不登记 expired | 自然终态不进入死信 |
| `P13-W04` | `NOT_STARTED` | replay 使用原 message_id/delivery_id，新 replay_epoch；默认最大 3 次 | 历史 attempt/retry 不清零 |
| `P13-W05` | `NOT_STARTED` | 同 message 同时只有一个 active replay_epoch；epoch 内受 recovery pool 限制 | 并发 replay 被原子拒绝 |
| `P13-W06` | `NOT_STARTED` | replay_requested 不发送、不接收 ACK/NACK、不占 active；复验后进入 queued | 中间态边界明确 |
| `P13-W07` | `NOT_STARTED` | 批量 replay 支持 partial success 和明确 delivery ID | 不允许模糊全量复活 |
| `P13-W08` | `NOT_STARTED` | cancel 支持 prepared、queued、sending、ack_waiting、retry_scheduled、replay_requested | 终态不可取消 |
| `P13-W09` | `NOT_STARTED` | sending cancel 只标 cancel_requested，写返回后裁决 | 不强杀底层写 |
| `P13-W10` | `NOT_STARTED` | hold 作为标记作用于 delivery/message；暂停 timeout、expiry、retry、dead letter、激活和发送 | hold 不增加主状态 |
| `P13-W11` | `NOT_STARTED` | hold 中 ACK/NACK 按策略写 PendingAck/PendingNack；解除后重新校验并迁移或丢弃 | pending 强一致且有 TTL |
| `P13-W12` | `NOT_STARTED` | summary 聚合实现 initializing、pending、partial_acked、all_acked、partial_failed、failed、cancelled | 聚合规则与设计一致 |
| `P13-W13` | `NOT_STARTED` | 所有高风险管理操作使用 precheck + commit operation token；commit 重新校验权威状态 | token 不绕过权限/fencing |

### 测试矩阵

- retry exhausted 与 expired。
- 三类 dead letter reason。
- replay 次数、并发 epoch、partial success。
- replay 前 payload_ref、owner、fencing、tenant 复验。
- cancel 与 send/ACK/timeout 并发。
- hold 与 ACK/NACK/timeout/retry 并发。
- pending record 迁移、过期和 discarded 审计。
- summary 全组合聚合测试。
- precheck 后状态变化导致 commit 拒绝。

### 阶段出口

- 异常处理和人工恢复达到 F3。
- 只有 dead_lettered 可 replay。

---

## P14 优先级、公平调度、背压与 Target Health

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P13 `VERIFIED`**

### 阶段目标

把现有可靠 worker 扩展为 system、tenant、recovery、observability 分池调度，落实硬配额、加权公平、aging、全局水位和分层健康画像。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P14-W01` | `NOT_STARTED` | 建立 system、tenant、recovery、observability pool 和独立统计 | pool 资源口径清晰 |
| `P14-W02` | `NOT_STARTED` | system pool 固定保留 15%，压力时上浮到 30%；最高保护 lease/fencing/security | 普通 tenant 无法耗尽系统保留 |
| `P14-W03` | `NOT_STARTED` | recovery pool 固定约 10%，上浮到 20-30%，不挤占最高 system | replay/recovery 不拖垮实时业务 |
| `P14-W04` | `NOT_STARTED` | tenant 硬配额覆盖 active、queued、inflight、retry backlog、activation rate、write pressure | 超配额稳定拒绝或排队 |
| `P14-W05` | `NOT_STARTED` | tenant pool 使用 Deficit Round Robin 或等价已验证加权公平实现 | 权重和 burst 可验证 |
| `P14-W06` | `NOT_STARTED` | priority aging 只在 queued 生效，不提升到 system 等级 | 低优先级无永久饥饿 |
| `P14-W07` | `NOT_STARTED` | prepared 激活融合 priority、fair share、health、age 和水位 | 激活记录策略版本和跳过原因 |
| `P14-W08` | `NOT_STARTED` | worker 固定底座 + 动态扩展；职责保持 Claim/Send/Timeout/Retry/Recovery/Lease/System 分离 | 扩缩容不改变状态机 |
| `P14-W09` | `NOT_STARTED` | 周期扫描频率全部来自配置：queue 1-2s、timeout 0.5-1s、lease 0.3-0.5s、retry 1s、recovery 5-10s | 类中无硬编码 |
| `P14-W10` | `NOT_STARTED` | 建立五层 health：connection、identity、component_type、runtime node、tenant | 层级更新和衰减可测试 |
| `P14-W11` | `NOT_STARTED` | 指标输入覆盖 ACK P95/P99、NACK、Defer、timeout、send failure、queue、flow-control、path failure、retry | health 只影响策略，不越权 |
| `P14-W12` | `NOT_STARTED` | 建立软过载、硬过载、内存危险三级行为 | 错误、拒绝、关闭边界稳定 |

### 测试矩阵

- 多 tenant 不同权重和 burst。
- system backlog 上升时保留容量。
- recovery storm 不阻塞 ACK/control。
- priority aging 和 prepared 不 aging。
- 动态 worker 扩缩容期间不重复 claim。
- 单慢连接不拖垮 tenant。
- health 指标滑动窗口和指数衰减。
- health 低分目标仍不能绕过 fixed connection/no_rebind。

### 阶段出口

- 单节点在过载、恢复和多租户条件下保持状态机稳定。
- 调度策略版本完整进入 RoutingPlan、Attempt 和激活审计。

---

## P15 可靠 Stream

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P14 `VERIFIED`**

### 阶段目标

在统一 Envelope、DeliveryRecord、ACK/NACK/Defer、state store 和 processor 上实现完整可靠 stream，不创建私有通道。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P15-W01` | `NOT_STARTED` | 定义 StreamDeliveryState：opening、active、closing、closed、failed、cancelled、expired | 非法迁移拒绝 |
| `P15-W02` | `NOT_STARTED` | stream.start、chunk、end 全部创建可靠 delivery；end ACK 后才 closed | transport close 不等于 stream closed |
| `P15-W03` | `NOT_STARTED` | 每个 chunk 独立 delivery_id 和 sequence | chunk 可单独重试 |
| `P15-W04` | `NOT_STARTED` | 实现滑动窗口，窗口完全由策略决定 | 接收方不能自行扩大 |
| `P15-W05` | `NOT_STARTED` | cumulative ACK 单调推进并原子批量更新 chunk DeliveryRecord 和 StreamState | ACK 回退无效 |
| `P15-W06` | `NOT_STARTED` | selective ACK 支持 ack_ranges、missing_sequences、received_sequences | 乱序和缺片可恢复 |
| `P15-W07` | `NOT_STARTED` | missing range 重试与普通 retry budget、health 和水位协作 | 不全量重发 |
| `P15-W08` | `NOT_STARTED` | strict order 范围配置；严格 chunk 顺序时窗口收敛为 1 | 前序终态策略明确 |
| `P15-W09` | `NOT_STARTED` | stream hold、cancel、replay 接入已有管理状态机 | 不另建控制语义 |
| `P15-W10` | `NOT_STARTED` | 最大窗口、分片大小、生命周期、乱序缓存和并发 stream 全部配置化 | 无 processor 硬编码 |
| `P15-W11` | `NOT_STARTED` | stream 指标进入 target health 和 observability | 不进入强一致主事务以外的权威判断 |

### 测试矩阵

- start strict 和 optimistic 策略。
- chunk 正常、丢失、重复、乱序。
- cumulative ACK、selective ACK 和 missing range 组合。
- ACK 与 retry 并发。
- end 未 ACK 保持 closing。
- hold、cancel、replay。
- 进程重启和 owner 恢复后的窗口。
- 大量 stream 的 tenant 配额和背压。
- 任何 stream ACK 更新必须通过 Lua 原子脚本。

### 阶段出口

- 单节点可靠 stream 达到 F3。
- StreamState 和 ACK window 契约冻结为 `ST-1`。

---

## P16 Runtime 管理、查询与配置热更新

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P15 `VERIFIED`**

### 阶段目标

建立 runtime 内管理 processor 和 `ns_backend` runtime 管理应用。所有管理行为通过管理 transport client、统一 Envelope、IAM 和 processor 执行。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P16-W01` | `NOT_STARTED` | backend 新建 runtime 管理应用边界，作为 management capability client | 不直接访问 runtime Redis 状态 |
| `P16-W02` | `NOT_STARTED` | 管理 client 建立、认证、heartbeat、reauth 和重连 | 管理端遵守同一协议 |
| `P16-W03` | `NOT_STARTED` | health、node、connection、summary、delivery、tree、dead letter、stream、queue、target health 查询 processor | 权限和 tenant 范围严格 |
| `P16-W04` | `NOT_STARTED` | dashboard 读取摘要并返回 as_of、summary_version、state_version | 不伪装实时权威 |
| `P16-W05` | `NOT_STARTED` | 控制前置查询、delivery detail、owner/fencing 读取权威 state store | 高风险不读异步摘要 |
| `P16-W06` | `NOT_STARTED` | kick、drain、replay、cancel、hold、release、cleanup、isolate/recover、limit、snapshot processor | 批量操作 partial success |
| `P16-W07` | `NOT_STARTED` | 高风险操作 precheck + commit；低风险操作单阶段强校验 | operation token 有 TTL 且不可提权 |
| `P16-W08` | `NOT_STARTED` | 配置管理服务执行 validate、version、apply mode、audit、rollback 和 event | processor 不直接修改 config object |
| `P16-W09` | `NOT_STARTED` | immediate 配置生成新不可变快照并原子切换；rolling 标记节点重启/滚动；restart_required 拒绝热应用 | 旧快照供在途操作继续引用 |
| `P16-W10` | `NOT_STARTED` | 配置组回滚；强依赖组不可独立回滚 | 版本链可追踪 |
| `P16-W11` | `NOT_STARTED` | 配置变化默认只影响后续受理、retry/replay、路由和策略；已 queued/ack_waiting 只有显式语义才受影响 | 历史记录不被改写 |
| `P16-W12` | `NOT_STARTED` | 管理审计写入 state store 强一致日志 | 控制操作审计不可丢 |

### 测试矩阵

- 普通连接查询 delivery detail 被拒绝。
- 管理权限分级和跨 tenant 管理。
- 批量 partial success、dry-run 和最大数量。
- precheck 后 owner/state 改变。
- immediate/rolling/restart_required。
- 配置 rollback 和依赖组冲突。
- 在途 delivery 保留旧 policy version。
- 管理连接断开不回滚已提交操作。

### 阶段出口

- runtime 可由 backend 管理应用安全操作。
- 无 HTTP 管理旁路。
- 配置单节点热更新达到 F3。

---

## P17 集群协调、角色状态与 Leader Lease

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F3`**  
**前置阶段：P16 `VERIFIED`**

### 阶段目标

实现单 active master、多 standby master、sub_node、singleton、leader lease、epoch、fencing 和角色准入。此阶段先完成集群控制，不开放跨节点业务 delivery。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P17-W01` | `NOT_STARTED` | 建立 role state machine：singleton、sub_node、standby_master、active_master、transitioning、draining | 非法角色迁移拒绝 |
| `P17-W02` | `NOT_STARTED` | 建立 health overlay：healthy、degraded、isolated、unavailable | 与 role 分离 |
| `P17-W03` | `NOT_STARTED` | backend bootstrap 返回候选 master、优先级、角色授权和配置版本 | 控制面授权可验证 |
| `P17-W04` | `NOT_STARTED` | Redis/Valkey leader lease 包含 lease key、term/epoch、fencing、TTL、renewal deadline、takeover grace | 全局写入携带 fencing |
| `P17-W05` | `NOT_STARTED` | active 定期续约；续约失败立即停止全局协调写入并转 transitioning/degraded | split-brain 写入被拒绝 |
| `P17-W06` | `NOT_STARTED` | standby 不抢占正常 active；lease 过期、管理切换或紧急隔离才竞争 | 稳态无抖动 |
| `P17-W07` | `NOT_STARTED` | runtime 节点间 connection.hello 使用 runtime_node credential | 节点连接同样经过协议和 IAM |
| `P17-W08` | `NOT_STARTED` | sub_node 只连接 active master；失联后通过 backend/config 发现新 active | 不向 standby 发普通流量 |
| `P17-W09` | `NOT_STARTED` | master 有 active sub_node 时拒绝新普通连接；无 sub_node 时允许降级接入 | 现有连接按策略收尾 |
| `P17-W10` | `NOT_STARTED` | transitioning/draining 仅允许 ACK/NACK/Defer、管理、health、cluster | 普通 task 被标准拒绝 |
| `P17-W11` | `NOT_STARTED` | graceful handoff、force takeover、emergency isolate 三种管理路径和权限等级 | 最终都由 lease/fencing 确认 |
| `P17-W12` | `NOT_STARTED` | 节点状态融合 transport、heartbeat、lease、delivery health、IAM、storage、config compatibility | 状态可解释 |

### 测试矩阵

- 多 standby 竞争只有一个 active。
- active 正常续约时无抢占。
- lease 过期、Redis 短断、旧 active 恢复。
- fencing token 轮换和旧 token 全局写入。
- graceful/force/emergency 三种切换。
- master 准入策略和 sub_node 数量变化。
- transitioning/draining 消息白名单。
- backend 授权存在但 lease 失败不能 active；lease 成功但 backend 未授权不能 active。

### 阶段出口

- 集群控制达到 F3。
- 业务消息仍只在本地投递。
- leader/role 契约冻结为 `CL-1`。

---

## P18 跨节点路由、父子 Delivery 与 Ownership Transfer

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F4`**  
**前置阶段：P17 `VERIFIED`**

### 阶段目标

实现 master/sub_node 拓扑中的查询、转发、route loop 防护、父子 delivery、ACK 回收、current owner 和 ownership transfer。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P18-W01` | `NOT_STARTED` | route 分组记录 root/current/previous/next runtime、segment、plan_id、hop/max_hops | 原始 source 保留 |
| `P18-W02` | `NOT_STARTED` | 重复 segment 和 max_hops 超限拒绝并安全审计 | 无转发循环 |
| `P18-W03` | `NOT_STARTED` | sub_node 本地命中直接处理；本地 miss 才查询 active master | 不中心化所有流量 |
| `P18-W04` | `NOT_STARTED` | master 返回目标 runtime 或接管转发计划；master 不直接篡改原 source | 路由路径可追踪 |
| `P18-W05` | `NOT_STARTED` | 跨节点每段独立 delivery_id 或按设计父子关系生成；共享 message_id | delivery tree 可实时查询 |
| `P18-W06` | `NOT_STARTED` | parent 只等待下游 runtime ACK；child 等待最终目标 ACK | parent 不等待业务终点 |
| `P18-W07` | `NOT_STARTED` | 父子关系、root、current_owner、current_state 强一致索引 | tree 查询不依赖异步聚合 |
| `P18-W08` | `NOT_STARTED` | ownership transfer 更新 owner_runtime_id、owner_epoch、fencing；旧 owner 记录 transferred | 新 owner 复用 delivery_id |
| `P18-W09` | `NOT_STARTED` | ACK 到旧 owner 执行转发、owner hint 或拒绝策略；不得直接写主状态 | 旧 owner 无权修改 |
| `P18-W10` | `NOT_STARTED` | stale routing cache 默认关闭；启用时检查 TTL、topology version、tenant/capability 摘要 | 控制和安全消息默认禁用 stale |
| `P18-W11` | `NOT_STARTED` | 跨节点 ACK timeout 默认 10s，本地保持 5s | policy version 记录 |
| `P18-W12` | `NOT_STARTED` | stream 跨节点使用同一父子 delivery 和 ACK 规则 | 不建立第二套 stream 转发 |

### 测试矩阵

- sub_node 本地命中和 miss。
- master 不可用时 routing unavailable。
- route loop 和 max hops。
- parent ACK 与 child ACK 时序。
- 下游 runtime ACK 后 child 最终失败，parent 不回滚。
- owner transfer 与旧 worker 并发写。
- ACK 到旧 owner。
- active master 切换期间在途 delivery。
- sub_node 断开、恢复和 child 状态 unknown/unreachable。
- 跨节点 stream 分片和 end ACK。

### 阶段出口

- active master + sub_node 生产基准拓扑完整可用。
- 跨节点 delivery、ACK 和 ownership 达到 F4。

---

## P19 恢复扫描、配置漂移、保留与清理

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F4`**  
**前置阶段：P18 `VERIFIED`**

### 阶段目标

实现进程、角色、存储和节点恢复后的分状态扫描；实现多节点配置漂移检测、自动修复、管理确认恢复；完成 TTL、归档和无孤儿索引清理。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P19-W01` | `NOT_STARTED` | 恢复触发覆盖 startup、角色切换、隔离恢复、policy 变化、管理触发、owner transfer、store 恢复 | 触发记录可追踪 |
| `P19-W02` | `NOT_STARTED` | 每 tenant 独立 cursor、并发、预算、限流和全局上限 | 单 tenant 不阻塞全局 |
| `P19-W03` | `NOT_STARTED` | prepared/queued、sending/ack_waiting、retry_scheduled、dead_lettered、终态分别处理 | 不统一重投 |
| `P19-W04` | `NOT_STARTED` | current_owner 非本节点、fencing 不匹配、message 过期时跳过或终态 | 不为进度强写 |
| `P19-W05` | `NOT_STARTED` | 状态恢复依赖权威 metadata/payload_ref，不依赖单进程 transient cache | 重启后可恢复 |
| `P19-W06` | `NOT_STARTED` | sub_node 上报 config/policy/group version、effective time、失败和 rollback | active 可检测漂移 |
| `P19-W07` | `NOT_STARTED` | 关键组漂移立即停止新路由并进入 degraded/isolated/draining | logging 等低风险只告警 |
| `P19-W08` | `NOT_STARTED` | 自动拉取 backend 权威配置并重新应用 | 修复过程审计 |
| `P19-W09` | `NOT_STARTED` | 因关键漂移隔离的节点修复后必须管理确认才能重入路由 | 不自动恢复生产流量 |
| `P19-W10` | `NOT_STARTED` | acked/cancelled/expired 默认 7 天；dead_lettered 30 天；日志摘要 14-30 天 | TTL 配置可覆盖 |
| `P19-W11` | `NOT_STARTED` | cleanup 同步处理 Hash、ZSet、Stream、Summary、tree、ACK/NACK/Defer、stream 和审计摘要 | 孤儿索引为零 |
| `P19-W12` | `NOT_STARTED` | cleanup 支持 dry-run、tenant、type、state、batch、pause/resume 和强审计 | 批量操作可恢复 |
| `P19-W13` | `NOT_STARTED` | 清理前生成压缩状态摘要，保留 summary/tree 可解释性 | 明细删除后仍可解释终态 |

### 测试矩阵

- 每种未完成状态的进程重启。
- 角色切换和 owner transfer 后恢复。
- Redis/Valkey 断开恢复。
- tenant cursor 中断续扫。
- 关键/非关键配置漂移。
- 自动修复成功但未管理确认。
- TTL 到期和跨对象同步清理。
- dry-run 与执行结果一致。
- 未处理 dead_letter 不清理。
- 清理后 orphan index、summary count、tree reference 全部一致。

### 阶段出口

- 恢复和清理达到 F4。
- 任何 EventBus 丢失均可由周期扫描恢复。

---

## P20 TLS、可观测、故障注入与生产安全

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F4`**  
**前置阶段：P19 `VERIFIED`**

### 阶段目标

完成生产 TLS、证书轮换边界、全量 metrics/trace/snapshot、强审计覆盖和必选故障注入。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P20-W01` | `NOT_STARTED` | WSS 服务端证书、私钥、CA、最小 TLS 版本和 cipher 配置校验 | prod 无 TLS 无法启动 |
| `P20-W02` | `NOT_STARTED` | runtime 节点连接支持双向认证或节点凭证 + TLS 策略 | 节点身份不依赖 IP |
| `P20-W03` | `NOT_STARTED` | 证书 reload 按配置 apply mode 执行；新连接使用新上下文，在途连接按策略收尾 | 不热改现有 transport 内部状态 |
| `P20-W04` | `NOT_STARTED` | 全量 event loop、transport、session、processor、routing、delivery、stream、cluster、store、pool 指标 | 指标名与设计一致 |
| `P20-W05` | `NOT_STARTED` | 指标标签白名单；禁止 connection_id、session_id、message_id、delivery_id 作为时序标签 | 高基数审查通过 |
| `P20-W06` | `NOT_STARTED` | trace 贯穿 backend、runtime、node/client；跨节点保持 correlation | 不记录原始凭证 |
| `P20-W07` | `NOT_STARTED` | diagnostic snapshot 包含版本、水位、角色、store、worker、队列和健康摘要 | 可用于管理 drill-down |
| `P20-W08` | `NOT_STARTED` | 安全/管理/状态变更审计覆盖率 100% | 抽样和自动计数一致 |
| `P20-W09` | `NOT_STARTED` | 建立故障注入控制器，只在 test/debug 受控环境启用 | prod 无法开启 |
| `P20-W10` | `NOT_STARTED` | 覆盖 Redis/Valkey、IAM、active、sub_node、ACK、owner、epoch、payload_ref、processor、slow write、handshake、stream、flow-control、fallback 故障 | 每项验证状态/响应/审计/指标四类结果 |
| `P20-W11` | `NOT_STARTED` | 建立敏感信息自动扫描，检查日志、错误、审计、state dump、snapshot | 泄露计数为零 |

### 阶段出口

- 必选故障场景通过率 100%。
- token/payload/auth_context/fencing 原值泄露为零。
- 生产安全检查全部 `VERIFIED`。

---

## P21 QUIC/WebTransport 扩展点与 Conformance 预验收

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F1`**  
**前置阶段：P20 `VERIFIED`**

### 阶段目标

验证当前 transport 抽象无需修改 Envelope、Session、IAM、RoutingPlan、DeliveryRecord 和 processor 即可容纳未来 `websocket_http3`、`webtransport_http3`、`quic_native`。本阶段不宣称这些 adapter 可用。

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P21-W01` | `NOT_STARTED` | 完成三类 adapter 的 capability manifest、配置 schema、依赖隔离和 feature disabled 响应 | 配置存在但默认禁用 |
| `P21-W02` | `NOT_STARTED` | TransportSession 支持 connection、session、stream 和 network path 映射，不修改 logical connection 契约 | WebSocket conformance 无回归 |
| `P21-W03` | `NOT_STARTED` | path migration 事件只更新 path_id/path_epoch 和健康，不递增 connection_epoch | 模型测试通过 |
| `P21-W04` | `NOT_STARTED` | 0-RTT 永久默认关闭；握手确认、hello、IAM、协议协商前 Envelope 不提交 | replay 安全测试模型通过 |
| `P21-W05` | `NOT_STARTED` | datagram allowlist 只允许 best_effort、loss_tolerant、non_control、non_security 类型 | task/ACK/control 永远拒绝 datagram |
| `P21-W06` | `NOT_STARTED` | 预留 RTT、loss、cwnd、bytes in flight、path migration、streams、datagram、0-RTT、flow-control 指标 | 指标不进入强一致事务 |
| `P21-W07` | `NOT_STARTED` | 使用 fake QUIC/WebTransport adapter 运行完整 conformance，证明上层不依赖具体库 | 核心模块无 transport 类型分支 |
| `P21-W08` | `NOT_STARTED` | UDP 不可用 fallback 顺序由 transport policy 表达；fallback 仍重新建立 transport 和 runtime 握手 | 不透明迁移 session owner |

### 阶段出口

- QUIC/WebTransport 扩展点达到 F1。
- 三类未来 adapter 保持 `DEFERRED` 和 disabled。
- 任何对外说明不得宣称已支持 QUIC/WebTransport。

---

## P22 性能基线与生产发布验收

**阶段状态：`NOT_STARTED`**  
**目标完成度：`F4`**  
**前置阶段：P21 `VERIFIED`**

### 阶段目标

按设计文档固定 workload 完成标准 asyncio/uvloop、单节点、master/sub_node、Redis/Valkey 高可用、恢复、stream 和安全验收，形成生产发布结论。

### 性能验收项

| ID | 状态 | 基线 |
|---|---|---|
| `P22-P01` | `NOT_STARTED` | 单 runtime 普通连接不少于 5000 |
| `P22-P02` | `NOT_STARTED` | master 管理/节点连接不少于 100 |
| `P22-P03` | `NOT_STARTED` | 本地 task dispatch 受理不少于 2000 msg/s |
| `P22-P04` | `NOT_STARTED` | master/sub_node 转发不少于 1000 msg/s |
| `P22-P05` | `NOT_STARTED` | 本地 ACK P99 不高于 100ms |
| `P22-P06` | `NOT_STARTED` | 跨节点 ACK P99 不高于 300ms |
| `P22-P07` | `NOT_STARTED` | Redis/Valkey 关键状态写入 P99 不高于 50ms |
| `P22-P08` | `NOT_STARTED` | recovery scan 不少于 1000 records/s |
| `P22-P09` | `NOT_STARTED` | replayable dead letter 重投成功率不低于 99% |
| `P22-P10` | `NOT_STARTED` | 安全/管理/状态审计覆盖率 100% |
| `P22-P11` | `NOT_STARTED` | 敏感原值泄露 0 |
| `P22-P12` | `NOT_STARTED` | TTL 清理后孤儿索引 0 |
| `P22-P13` | `NOT_STARTED` | 必选故障场景通过率 100% |

### 工作包

| ID | 状态 | 实施内容 | 完成判定 |
|---|---|---|---|
| `P22-W01` | `NOT_STARTED` | 固定压测环境、节点数量、Redis/Valkey 拓扑、消息分布、payload 模式、timeout、worker、pool 和 tenant 配置 | 结果可复现 |
| `P22-W02` | `NOT_STARTED` | asyncio 与 uvloop 使用完全相同 workload 对比吞吐、P95/P99、lag、CPU、内存、任务堆积、取消和异常 | auto 默认有数据依据 |
| `P22-W03` | `NOT_STARTED` | 本地、跨节点、stream、recovery、replay 和管理控制分别压测 | 瓶颈定位到具体层 |
| `P22-W04` | `NOT_STARTED` | 执行 Redis/Valkey standalone、Sentinel/Cluster 和故障切换测试 | 生产拓扑完成 |
| `P22-W05` | `NOT_STARTED` | 执行长稳测试，覆盖连接 churn、resume、retry、清理和配置热更新 | 无持续内存和索引增长 |
| `P22-W06` | `NOT_STARTED` | 生成发布验收报告，记录达到、未达到、风险、限制和生产范围 | 未达到项不得标记 VERIFIED |
| `P22-W07` | `NOT_STARTED` | 冻结协议、state schema、Lua script version、config group version 和管理合同 | 发布版本可升级和回滚 |

### 最终出口

只有以下条件全部成立时，`ns_runtime` 才能标记为生产完成：

- P00-P22 全部 `VERIFIED`。
- 全局不变量自动测试全部通过。
- 设计文档每一条能力均映射到至少一个已验证工作包。
- 所有已启用 message.type 均具备 schema、权限、processor、审计、标准响应和故障测试。
- 生产 Redis/Valkey 高可用拓扑通过。
- master/sub_node 集群、可靠 stream、replay、cancel、hold、配置热更新和恢复扫描全部通过。
- 标准 asyncio 与 uvloop 均通过功能回归。
- 未来 QUIC/WebTransport 配置存在但保持 disabled。
- 发布验收报告完成并记录容量边界。

---

## 7. 设计条款到阶段的覆盖矩阵

| 设计章节 | 主要阶段 |
|---|---|
| 代码风格和依赖注入 | P01-P07，持续回归 |
| 核心定位和职责 | 全阶段不变量 |
| 接入、transport、进程 | P02、P04、P21 |
| 角色和切换 | P17-P18 |
| 逻辑分层 | P01-P09 |
| Envelope | P03 |
| 连接和会话 | P04-P06 |
| IAM 和安全 | P06、P20 |
| Processor 和插件 | P07 |
| 事件和观测 | P07、P14、P20 |
| 配置和策略 | P01、P16、P19 |
| 路由和调度 | P09、P14、P18 |
| 可靠投递 | P08、P10-P13、P18 |
| ACK/NACK/Defer/stream | P12、P15、P18 |
| retry/dead/replay/cancel/hold | P12-P13 |
| Summary 和受理 | P10、P13 |
| payload_ref | P06、P10、P12-P13 |
| priority/backpressure | P14 |
| 集群协调 | P17-P18 |
| 状态存储 | P08，持续使用 |
| 管理和查询 | P16 |
| 恢复、保留、清理 | P19 |
| 错误和不变量 | P01、全阶段测试 |
| TLS、uvloop、质量、性能 | P02、P20-P22 |
| QUIC/WebTransport 预留 | P04、P21 |

---

## 8. 接口冻结登记表

接口达到冻结状态后，任何修改必须重新运行所属阶段及全部下游回归。

| 契约编号 | 契约 | 所属阶段 | 状态 |
|---|---|---|---|
| `CFG-1` | NsConfig 不可变快照、兼容入口、配置组 metadata 与 runtime 细分配置 | P01 | `VERIFIED` |
| `RTY-1` | BackoffStrategy、固定/指数/jitter 退避、RetryBudget 与 RetrySchedule | P01 | `VERIFIED` |
| `SEC-1` | Sanitizer 字段/路径/对象规则、URL/文本脱敏与不可逆摘要 | P01 | `VERIFIED` |
| `TC-1` | Transport adapter conformance | P04 | `NOT_STARTED` |
| `SC-1` | SessionContext 和 logical connection | P05 | `NOT_STARTED` |
| `IAM-R1` | runtime 与 backend IAM 合同 | P06 | `NOT_STARTED` |
| `PC-1` | ProcessorContext 和 pipeline | P07 | `NOT_STARTED` |
| `SS-1` | StateStore conformance | P08 | `NOT_STARTED` |
| `RP-1` | RoutingPlan | P09 | `NOT_STARTED` |
| `DR-1` | Summary 和 DeliveryRecord 初始模型 | P10 | `NOT_STARTED` |
| `ACK-1` | ACK/NACK/Defer 和 retry 状态机 | P12 | `NOT_STARTED` |
| `ST-1` | StreamDeliveryState 和窗口 | P15 | `NOT_STARTED` |
| `MG-1` | 管理控制和状态查询 | P16 | `NOT_STARTED` |
| `CL-1` | role、leader lease、fencing | P17 | `NOT_STARTED` |
| `XD-1` | 跨节点父子 delivery 和 owner transfer | P18 | `NOT_STARTED` |

---

## 9. 阶段状态总表

| 阶段 | 名称 | 状态 | 完成度 | 依赖 |
|---|---|---|---|---|
| P00 | 本地仓库基线与实施账本 | `VERIFIED` | F1 | 无 |
| P01 | ns_common 公共基础设施加固 | `IN_PROGRESS` | F1 | P00 |
| P02 | Runtime 进程生命周期与事件循环 | `NOT_STARTED` | F0 | P01 |
| P03 | Envelope 协议层与类型注册表 | `NOT_STARTED` | F0 | P02 |
| P04 | Transport 抽象与 WebSocket/TCP | `NOT_STARTED` | F0 | P03 |
| P05 | 连接、会话、握手、心跳、Resume | `NOT_STARTED` | F0 | P04 |
| P06 | IAM、安全上下文与 backend 合同 | `NOT_STARTED` | F0 | P05 |
| P07 | Processor、插件、事件与审计 | `NOT_STARTED` | F0 | P06 |
| P08 | 强一致 State Store | `NOT_STARTED` | F0 | P07 |
| P09 | RoutingPlan 与本地路由 | `NOT_STARTED` | F0 | P08 |
| P10 | 受理、Summary、去重、PayloadRef | `NOT_STARTED` | F0 | P09 |
| P11 | 本地可靠投递调度与发送 | `NOT_STARTED` | F0 | P10 |
| P12 | ACK/NACK/Defer/Timeout/Retry | `NOT_STARTED` | F0 | P11 |
| P13 | Dead Letter/Replay/Cancel/Hold | `NOT_STARTED` | F0 | P12 |
| P14 | Priority/Fairness/Backpressure/Health | `NOT_STARTED` | F0 | P13 |
| P15 | 可靠 Stream | `NOT_STARTED` | F0 | P14 |
| P16 | 管理、查询与配置热更新 | `NOT_STARTED` | F0 | P15 |
| P17 | 集群协调与 Leader Lease | `NOT_STARTED` | F0 | P16 |
| P18 | 跨节点路由与 Ownership | `NOT_STARTED` | F0 | P17 |
| P19 | 恢复、漂移、保留与清理 | `NOT_STARTED` | F0 | P18 |
| P20 | TLS、可观测与故障注入 | `NOT_STARTED` | F0 | P19 |
| P21 | QUIC/WebTransport 扩展预验收 | `NOT_STARTED` | F0 | P20 |
| P22 | 性能与生产发布验收 | `NOT_STARTED` | F0 | P21 |

---

## 10. Code Agent 阶段交接记录模板

每次结束开发会话时，在本节顶部追加一条记录。不得删除历史记录。

### 交接记录

#### 2026-07-16 P01-W09

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：本地 `main`；未查询远程仓库或读取提交记录，未切换分支。
- 会话开始前已存在的工作区修改：无。
- 本次新增或修改的文件：新增 `src/ns_common/security.py`、`tests/test_security.py`；修改 `src/ns_common/__init__.py` 和本实施文档；设计文档与 logger 未修改。
- 工作包状态：`VERIFIED`。
- 已完成内容：统一字段/路径/对象 sanitizer，覆盖完全替换、不可逆摘要、异常 details、URL/free text、嵌套对象、循环引用和深度限制；所有输出与输入分离并可 JSON 序列化。
- 修改的公共契约：新增 `Sanitizer`/`NsSanitizer`、三个便利函数和四个稳定常量；`COM-006` 与 `SEC-1` 标记为 `VERIFIED`。
- 新增错误码、state key 或 Lua script：无。
- 测试结果：Windows `tests.test_security` 9/9、runtime 联合 110/110、根测试 121/121；WSL `tests.test_security` 9/9；均为 0 跳过、0 失败；compileall、两个环境 pip check、公共导出和差异检查通过。
- 未完成项：W10 logger extra/exception 接入和全链路泄露扫描尚未开始；无标签自由文本仍要求调用方提供字段或路径语义。
- 明确阻塞项：无。
- 下一工作包：`P01-W10 把 sanitizer 接入 NsLogger`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/security.py`、`src/ns_common/logger.py`、`src/ns_common/exceptions.py`、`src/ns_common/__init__.py`、`tests/test_security.py` 和日志相关测试。

#### 2026-07-16 P01-FIX-02

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：本地 `main`；未查询远程仓库或读取提交记录，未切换分支。
- 会话开始前已存在的工作区修改：无。
- 本次新增或修改的文件：`src/ns_common/retry.py`、`tests/test_retry.py` 和本实施文档；设计文档未修改。
- 工作包状态：`VERIFIED`。
- 已完成内容：关闭超大数值和异常 `__float__` 的原生异常泄露；区分直接调用参数的 `NsValidationError` 与注入依赖非法返回的 `NsStateError`；冻结 `RetrySchedule` 的数值、UTC、deadline、一致性和 budget 构造不变量。
- 修改的公共契约：`RetrySchedule` 从无构造门禁提升为严格冻结值对象；现有类型名、函数签名和公共导出保持不变，`COM-005` 与 `RTY-1` 回归通过。
- 新增错误码、state key 或 Lua script：无。
- 测试结果：Windows `tests.test_retry` 19/19、runtime 联合 101/101、根测试 112/112，均为 0 跳过、0 失败；`compileall`、两个环境 `pip check` 和最终差异检查通过。
- 未完成项：P01-W09 sanitizer 及后续工作包；本修复未开始 W09。
- 明确阻塞项：无。
- 下一工作包：`P01-W09 建立统一 sanitizer`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/retry.py`、`tests/test_retry.py`、`src/ns_common/logger.py` 和日志相关测试。

#### 2026-07-16 P01-W08

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；未读取远程内容或提交历史，未切换分支。
- 会话开始前已存在的工作区修改：P01-W07 的实施文档、公共导出、标识符生产代码和测试；均已保留。
- 本次新增或修改的文件：新增 `src/ns_common/retry.py`、`tests/test_retry.py`；修改 `src/ns_common/__init__.py` 和本实施文档；设计文档未修改。
- 工作包状态：`VERIFIED`。
- 已完成内容：冻结一基可插拔 backoff 策略、固定/指数/确定性 jitter、不可变自动 retry 预算、预算耗尽语义，以及 UTC/单调双时间基准的下一 retry 调度结果。
- 修改的公共契约：新增并导出 `BackoffStrategy`、三种退避实现、`RetryBudget`、`RetrySchedule`、调度函数、别名和相关常量/类型；`COM-005` 与 `RTY-1` 标记为 `VERIFIED`。
- 新增错误码：无；参数校验沿用 `NsValidationError`，预算耗尽和注入依赖非法输出沿用 `NsStateError`。
- 新增或修改的 state key/Lua script：无。
- 测试结果：Windows `tests.test_retry` 14/14、runtime 联合 96/96、根测试 107/107；WSL `tests.test_retry` 14/14；所有结果均为 0 跳过、0 失败；`compileall`、两个 Windows 环境 `pip check`、公共导出、测试路径和差异检查通过。
- 未完成项：sanitizer 属于 W09/W10；权威 retry 状态与原子预算属于 P08/P12；健康/负载感知策略属于 P14；backend IAM 既有 retry 迁移不在 W08 范围。
- 明确阻塞项：无。
- 下一工作包：`P01-W09 建立统一 sanitizer`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/retry.py`、`src/ns_common/time.py`、`src/ns_common/logger.py`、`src/ns_common/exceptions.py`、`src/ns_common/__init__.py`、`tests/test_retry.py` 和日志相关测试。

#### 2026-07-16 P01-W07

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；未读取远程内容或提交历史，未切换分支。
- 会话开始前已存在的工作区修改：无；`git status --short --branch` 显示干净的分支状态。
- 本次会话新增或修改的文件：新增 `src/ns_common/identifiers.py`、`tests/test_identifiers.py`，修改 `src/ns_common/__init__.py` 和本实施文档。
- 本地设计文档路径与版本：`docs/ns_runtime_design_checklist_0.0.2.md`，版本 `0.0.2`；未修改。
- 本地实施文档路径与版本：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，版本 `0.0.2`。
- Python 解释器与虚拟环境：Windows 使用 `S:\PythonVenv\ns_runtime\Scripts\python.exe` 与 `S:\PythonVenv\ns_backend\Scripts\python.exe`；WSL 使用既有 `/home/ns/.virtualenvs/ns_runtime/bin/python`；未新建虚拟环境。
- 日期：`2026-07-16T17:23:24+08:00`。
- 执行阶段：`P01 ns_common 公共基础设施加固`。
- 执行工作包：`P01-W07 建立 ID 生成和校验规则`。
- 工作包状态：`VERIFIED`。
- 已完成内容：建立九类带唯一类型前缀的 UUIDv4 hex ID、显式 factory、通用与类型专用生成函数、严格解析/校验、冻结值对象和并发唯一性验证。
- 修改的公共契约：新增并导出 `NsIdentifierKind`、`NsIdentifier`、`IdentifierFactory`/`NsIdentifierFactory`、三个格式注册常量、生成函数和解析/校验函数；`COM-004` 标记为 `VERIFIED`。
- 新增错误码：无；非法 kind/value/format 使用 `NsValidationError`，无效 UUID factory 输出使用 `NsStateError`。
- 新增或修改的 state key/Lua script：无。
- 测试结果：Windows `tests.test_identifiers` 8/8、runtime 联合 82/82、根测试 93/93；WSL `tests.test_identifiers` 8/8；所有结果均为 0 跳过、0 失败；9000 次并发生成无冲突，`compileall`、两个 Windows 环境 `pip check`、公共导出、测试路径和差异检查通过。
- 未完成项：retry/backoff 属于 W08；各 runtime 模型对统一 ID 契约的消费属于其对应后续阶段。
- 明确阻塞项：无。
- 下一工作包：`P01-W08 建立通用 retry/backoff 类型`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/identifiers.py`、`src/ns_common/time.py`、`src/ns_common/__init__.py`、`tests/test_identifiers.py` 和 `tests/test_time.py`。

#### 2026-07-16 P01-W06

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；未读取远程内容或提交历史，未切换分支。
- 会话开始前已存在的工作区修改：无；本次先完成 P01-FIX-01，再在恢复游标后开始 W06。
- W06 新增或修改的文件：新增 `src/ns_common/time.py`、`tests/test_time.py`，修改 `src/ns_common/__init__.py` 和本实施文档；同会话 P01-FIX-01 文件另见下一条交接记录。
- 本地设计文档路径与版本：`docs/ns_runtime_design_checklist_0.0.2.md`，版本 `0.0.2`；未修改。
- 本地实施文档路径与版本：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，版本 `0.0.2`。
- Python 解释器与虚拟环境：Windows 使用 `S:\PythonVenv\ns_runtime\Scripts\python.exe` 与 `S:\PythonVenv\ns_backend\Scripts\python.exe`；WSL 使用既有 `/home/ns/.virtualenvs/ns_runtime/bin/python`；未新建虚拟环境。
- 日期：`2026-07-16T17:01:39+08:00`。
- 执行阶段：`P01 ns_common 公共基础设施加固`。
- 执行工作包：`P01-W06 建立 Clock 接口`。
- 工作包状态：`VERIFIED`。
- 已完成内容：建立 Clock Protocol、SystemClock 和 ControlledClock，覆盖 timezone-aware UTC、monotonic、可注入异步 sleep、显式推进、并发 deadline、取消清理、范围校验和跨 loop 门禁。
- 修改的公共契约：新增并导出 `Clock`、`SystemClock`、`ControlledClock`、`NsClock`、`NsSystemClock`、`NsControlledClock` 和 `UTC_EPOCH`；`COM-003` 标记为 `VERIFIED`。
- 新增错误码：无；非法时间值使用 `NsValidationError`，跨 loop 或错误推进上下文使用 `NsStateError`。
- 新增或修改的 state key/Lua script：无。
- 测试结果：Windows `tests.test_time` 11/11、runtime 联合 74/74、根测试 85/85；WSL `tests.test_time` 11/11；所有结果均为 0 跳过、0 失败；`compileall`、两个 Windows 环境 `pip check`、公共导出、测试路径和差异检查通过。
- 未完成项：ID 属于 W07，retry/backoff 属于 W08；现有调用方迁移到显式 Clock 由对应后续工作包完成。
- 明确阻塞项：无。
- 下一工作包：`P01-W07 建立 ID 生成和校验规则`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/time.py`、`src/ns_common/config.py`、`src/ns_common/__init__.py`、`tests/test_time.py` 和 `tests/test_config.py`。

#### 2026-07-16 P01-FIX-01

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；本工作包未读取远程内容或提交历史，未切换分支。
- 会话开始前已存在的工作区修改：无；`git status --short --branch` 仅显示干净的分支状态。
- 本次修复新增或修改的文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、`etc/ns_config.example.json`、`tests/test_config.py` 和本实施文档。
- 本地设计文档路径与版本：`docs/ns_runtime_design_checklist_0.0.2.md`，版本 `0.0.2`；未修改。
- 本地实施文档路径与版本：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，版本 `0.0.2`。
- Python 解释器与虚拟环境：`S:\PythonVenv\ns_runtime\Scripts\python.exe` 与 `S:\PythonVenv\ns_backend\Scripts\python.exe`；两个环境 `pip check` 均通过。
- 日期：`2026-07-16T16:57:06+08:00`。
- 执行阶段：`P01 ns_common 公共基础设施加固`。
- 执行工作包：`P01-FIX-01 修正 runtime 集群角色配置语义`。
- 工作包状态：`VERIFIED`。
- 已完成内容：默认角色改为 `singleton`；仅接受 `active_master`、`singleton`、`standby_master`、`sub_node`；旧角色、运行期过渡状态、健康状态、空值、未知值和非字符串稳定拒绝；序列化、重载、不可变快照与配置来源优先级已验证。
- 修改的公共契约：新增并导出 `RUNTIME_CLUSTER_ROLES`；`NsRuntimeClusterConfig.role` 的 Literal 和默认值已冻结为四个明确启动角色；`COM-001` 恢复 `VERIFIED`。
- 新增错误码：无；非法角色使用 `NsConfigError`，details 包含字段、实际值和完整允许值。
- 新增或修改的 state key/Lua script：无。
- 测试结果：`tests.test_config` 40 通过、0 跳过、0 失败；`tests.test_async_runtime` 23 通过、0 跳过、0 失败；根测试 74 通过、0 跳过、0 失败；示例加载、`compileall`、两个环境 `pip check`、引用扫描和 `git diff --check` 通过。
- 明确未实现：未实现 P17 leader election、leader lease、epoch、fencing、自动角色切换、transitioning/draining 状态机或集群协调写入；配置 `active_master` 不代表已取得权威。
- 后续独立事项：`runtime.cluster.active_master_url` transport 语义未处理。
- 明确阻塞项：无。
- 下一工作包：`P01-W06 建立 Clock 接口`。
- 下一工作包开始状态：游标已恢复，W06 尚未修改生产代码。

#### 2026-07-16 P01-W05

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；W05 开始前已将 W03/W04 提交 `eecc755ec99e81b708f9a1a6bb48217836d0eb5b` 推送到 `origin/main`，随后从干净工作区继续。
- 会话开始前已存在的工作区修改：W05 工作开始时无未提交修改；本记录对应的 W05 修改尚未提交。
- 本次会话新增或修改的文件：修改 `src/ns_common/async_runtime.py`、`src/ns_common/__init__.py`、`tests/test_async_runtime.py` 和本实施文档。
- 本地设计文档路径与版本：`docs/ns_runtime_design_checklist_0.0.2.md`，版本 `0.0.2`；未修改。
- 本地实施文档路径与版本：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，版本 `0.0.2`。
- Python 解释器与虚拟环境：`S:\PythonVenv\ns_runtime\Scripts\python.exe` 与 `S:\PythonVenv\ns_backend\Scripts\python.exe`；两个环境 `pip check` 均通过。
- 日期：`2026-07-16T15:56:02+08:00`。
- 执行阶段：`P01 ns_common 公共基础设施加固`。
- 执行工作包：`P01-W05 建立统一 TaskSupervisor`。
- 工作包状态：`VERIFIED`。
- 已完成内容：建立显式 TaskSupervisor、严格任务登记与 loop 绑定、命名任务、异常收集和回调、有序分组取消、全局关闭超时、冻结关闭报告、未完成任务快照以及幂等关闭。
- 修改的公共契约：新增并导出 `TaskSupervisor`、`NsTaskSupervisor`、`NsTaskSupervisorState`、`NsTaskFailure`、`NsTaskShutdownReport` 和 `NsUnfinishedTask`；`COM-002` 继续为 `IN_PROGRESS`，selector 与 TaskSupervisor 已验证。
- 修改的配置组：无；监督器的默认关闭超时可在显式构造时传入，未隐式读取全局配置。
- 新增错误码：无；非法登记、跨 loop 复用和非法生命周期调用使用稳定的 Python `TypeError`、`ValueError` 或 `RuntimeError`。
- 新增或修改的 state key/Lua script：无。
- 执行的单元测试：runtime 环境运行 `tests.test_async_runtime`，23/23 通过；其中 W05 新增 9 个 TaskSupervisor 用例；`tests.test_config`，35/35 通过。
- 执行的集成测试：无真实外部依赖；backend 环境运行根测试发现入口，69/69 通过。
- 执行的故障测试：覆盖任务异常、failure handler 异常、取消期间异常、不配合取消导致关闭超时、重复名称、关闭后登记、跨 loop 复用和监督任务自关闭；超时用例结束前显式清理测试任务。
- 回归测试结果：根 `tests/` 共 69/69 通过；`compileall`、两个环境 `pip check`、公共导出导入、测试路径扫描与 `git diff --check` 通过。
- 敏感信息扫描结果：未执行 P01-W09/W10 自动泄露扫描；本工作包不处理 token、payload、auth_context 或外部响应。
- 未完成项：进程信号、有序停止接入和 sink/client 资源清理属于 P02；P01 的 Clock、ID、retry、sanitizer、异常元数据、HTTP 生命周期、observability 和测试基础设施仍待后续工作包。
- 明确阻塞项：无。
- 下一工作包：`P01-W06 建立 Clock 接口`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/async_runtime.py`、`src/ns_common/__init__.py` 和 `tests/test_async_runtime.py`。

#### 2026-07-16 P01-W04

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；未读取远程内容、提交历史或切换分支。
- 会话开始前已存在的工作区修改：上一工作包 W03 的未提交实现及实施账本修改；均已保留并在其上继续。
- 本次会话新增或修改的文件：新增 `src/ns_common/async_runtime.py`、`tests/test_async_runtime.py`，修改 `src/ns_common/__init__.py` 和本实施文档；W03 的 `src/ns_common/config.py`、`tests/test_config.py`、`etc/ns_config.example.json` 未被本工作包改写。
- 本地设计文档路径与版本：`docs/ns_runtime_design_checklist_0.0.2.md`，版本 `0.0.2`；未修改。
- 本地实施文档路径与版本：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，版本 `0.0.2`。
- Python 解释器与虚拟环境：`S:\PythonVenv\ns_runtime\Scripts\python.exe` 与 `S:\PythonVenv\ns_backend\Scripts\python.exe`；两个环境 `pip check` 均通过。
- 日期：`2026-07-16T15:42:59+08:00`。
- 执行阶段：`P01 ns_common 公共基础设施加固`。
- 执行工作包：`P01-W04 建立标准 asyncio event loop selector`。
- 工作包状态：`VERIFIED`。
- 已完成内容：建立标准 asyncio/uvloop policy selector、可注入平台与依赖探测、Linux auto 优先/fallback 告警、Windows auto 标准 asyncio、显式 uvloop 启动失败和运行中 restart_required 门禁。
- 修改的公共契约：新增并导出 `NsEventLoopFallbackWarning`、`NsEventLoopImplementation`、`NsEventLoopSelection`、`NsEventLoopSelector`、`select_event_loop()` 和 `install_event_loop_policy()`；`COM-002` 进入 `IN_PROGRESS`。
- 修改的配置组：无；消费 W03 已冻结的 `runtime.event_loop` 配置契约。
- 新增错误码：无；缺失/不可用依赖使用 `NsDependencyError`，运行中切换使用 `NsStateError`，配置拒绝使用 `NsConfigError`。
- 新增或修改的 state key/Lua script：无。
- 执行的单元测试：runtime 环境运行 `tests.test_async_runtime`，14/14 通过；`tests.test_config`，35/35 通过。
- 执行的集成测试：无真实外部依赖；backend 环境运行根测试发现入口，60/60 通过。
- 执行的故障测试：覆盖 uvloop 导入失败、API 缺失等价路径、policy 初始化失败、Windows 不支持、运行中切换和错误 apply mode；未进行外部故障注入。
- 回归测试结果：根 `tests/` 共 60/60 通过；`compileall`、两个环境 `pip check`、公共导出导入、测试路径扫描与 `git diff --check` 通过。
- 敏感信息扫描结果：未执行 P01-W09/W10 自动泄露扫描；本工作包不处理 token、payload、auth_context 或外部响应。
- 未完成项：TaskSupervisor、取消顺序、优雅关闭和未完成任务报告属于 W05；真实 Linux/uvloop workload 与性能对比属于后续阶段。
- 明确阻塞项：无。
- 下一工作包：`P01-W05 建立统一 TaskSupervisor`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/async_runtime.py`、`src/ns_common/config.py`、`src/ns_common/__init__.py`、`tests/test_async_runtime.py`、`tests/test_config.py`。

#### 2026-07-16 P01-W03

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；未读取远程内容、提交历史或切换分支。
- 会话开始前已存在的工作区修改：无；本次会话开始时 `git status --short --branch` 仅显示 `main...origin/main`。
- 本次会话新增或修改的文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、`tests/test_config.py`、`etc/ns_config.example.json` 和本实施文档。
- 本地设计文档路径与版本：`docs/ns_runtime_design_checklist_0.0.2.md`，版本 `0.0.2`；未修改。
- 本地实施文档路径与版本：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，版本 `0.0.2`。
- Python 解释器与虚拟环境：`S:\PythonVenv\ns_runtime\Scripts\python.exe` 与 `S:\PythonVenv\ns_backend\Scripts\python.exe`，两个环境 `pip check` 均通过。
- 日期：`2026-07-16T15:27:56+08:00`。
- 执行阶段：`P01 ns_common 公共基础设施加固`。
- 执行工作包：`P01-W03 建立 runtime 细分配置组`。
- 工作包状态：`VERIFIED`。
- 已完成内容：建立 17 个强类型 runtime 细分配置组、四种 transport adapter 配置、子组 metadata/生效模式、递归严格加载、来源传播、快照恢复、独立校验及完整示例配置。
- 修改的公共契约：新增并导出 runtime 细分配置类型、`RUNTIME_CONFIG_GROUP_NAMES` 和 `RUNTIME_CONFIG_APPLY_MODES`；`CFG-1` 标记为 `VERIFIED`。
- 修改的配置组：runtime 下 event_loop、transport、wire_codec、protocol、security、iam、state_store、routing、delivery、worker、pool、tenant_quota、cluster、recovery、observability、logging、debug；backend/cache/log 字段未变。
- 新增错误码：无；配置拒绝继续使用 `NsConfigError`。
- 新增或修改的 state key/Lua script：无。
- 执行的单元测试：runtime 环境运行 `tests.test_config`，35/35 通过。
- 执行的集成测试：无真实外部依赖；backend 环境运行根测试发现入口，46/46 通过。
- 执行的故障测试：覆盖全部 runtime 子组的非法值、未知字段、非法来源/版本、prod 明文 transport、prod SQLite state store、非 json.v1 codec 和缺失子组 metadata；未进行外部故障注入。
- 回归测试结果：根 `tests/` 共 46/46 通过；`compileall`、两个环境 `pip check`、示例配置加载、测试路径扫描与 `git diff --check` 通过。
- 敏感信息扫描结果：未执行 P01-W09/W10 自动泄露扫描；本工作包未引入真实凭证或业务 payload，示例仅含原有占位值和本地地址。
- 未完成项：P01-W04 至 P01-W17；未创建 `src/ns_runtime`，未启动 transport 或实现 state store。
- 明确阻塞项：无。
- 下一工作包：`P01-W04 建立标准 asyncio event loop selector`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/config.py`、`src/ns_common/__init__.py`、`tests/test_config.py`、`etc/ns_config.example.json`。

#### 2026-07-16 P01-W02

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；未读取远程内容、提交历史或切换分支。
- 会话开始前已存在的工作区修改：用户原有的 0.0.1 设计文档暂存删除和两份未跟踪 0.0.2 文档，以及上一工作包 W01 的未提交实现；均已保留。用户已删除仓库内 `.venv`。
- 本次会话新增或修改的文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、`tests/__init__.py`、`tests/test_config.py`、`tests/test_cache.py`、删除测试旧位置 `src/ns_common/tests.py` 与 `src/ns_common/cache/tests.py`、更新本实施文档。
- 本地设计文档路径与版本：`docs/ns_runtime_design_checklist_0.0.2.md`，版本 `0.0.2`；未修改。
- 本地实施文档路径与版本：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，版本 `0.0.2`。
- Python 解释器与虚拟环境：`S:\PythonVenv\ns_runtime\Scripts\python.exe` 与 `S:\PythonVenv\ns_backend\Scripts\python.exe`，均为 Python 3.10.11，两个环境 `pip check` 均通过。
- 日期：`2026-07-16T14:47:04+08:00`。
- 执行阶段：`P01 ns_common 公共基础设施加固`。
- 执行工作包：`P01-W02 配置来源优先级与版本元数据语义`。
- 工作包状态：`VERIFIED`。
- 已完成内容：固定三层配置来源优先级；实现 local 基线、backend 分组深度覆盖和已验证快照恢复；实现有效时间标准化、版本一致性、rollback 来源及非法覆盖原子拒绝。
- 修改的公共契约：新增并导出 `NsConfigSource`、`NS_CONFIG_SOURCE_PRIORITY`、`NsConfigResolver`、`NsConfig.resolve()`、`NsConfig.config_version`、`NsConfig.policy_version` 和 `NsConfig.as_validated_snapshot()`；`COM-001` 标记为 `VERIFIED`，`CFG-1` 因 W03 尚会扩展配置组而保持 `IN_PROGRESS`。
- 修改的配置组：backend/cache/log/runtime 总组 metadata 的来源和版本语义；未增加 W03 runtime 细分配置字段。
- 新增错误码：无；非法来源和覆盖继续使用 `NsConfigError`。
- 新增或修改的 state key/Lua script：无。
- 执行的单元测试：runtime 环境运行 `tests.test_config`，24/24 通过。
- 执行的集成测试：无真实外部依赖；backend 环境运行根测试发现入口，35/35 通过。
- 执行的故障测试：覆盖非法来源、缺失 metadata、版本冲突、rollback 冲突、非法最终配置和伪造快照的内存负向测试；未进行外部故障注入。
- 回归测试结果：根 `tests/` 共 35/35 通过；`compileall`、两个环境 `pip check`、示例配置加载/JSON 校验、测试路径扫描与 `git diff --check` 通过。
- 敏感信息扫描结果：未执行 P01-W09/W10 自动泄露扫描；本工作包未引入真实凭证或业务 payload。
- 未完成项：runtime 细分配置组（W03）及 P01 后续公共基础设施工作包。
- 明确阻塞项：无。
- 下一工作包：`P01-W03 建立 runtime 细分配置组`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/config.py`、`tests/test_config.py`、`etc/ns_config.example.json`。

#### 2026-07-16 P01-W01

- 本地仓库根目录：`S:\PythonProject\ns\ns_evermore`。
- 当前分支或 detached 状态：`main`，跟踪 `origin/main`；本次未读取远程内容、提交历史或切换分支。
- 会话开始前已存在的工作区修改：已暂存删除 `docs/ns_runtime_design_checklist_0.0.1.md`；未跟踪 `docs/` 中已有两份 0.0.2 文档。本次保留这些用户修改，并仅按实施规则更新实施文档。
- 本次会话新增或修改的文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、`src/ns_common/tests.py`、`src/ns_backend/backend/settings.py`、`src/ns_backend/backend/db/routers.py`、`etc/ns_config.example.json`、`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`。
- 本地设计文档路径与版本：`docs/ns_runtime_design_checklist_0.0.2.md`，版本 `0.0.2`；未修改。
- 本地实施文档路径与版本：`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`，版本 `0.0.2`。
- Python 解释器与虚拟环境：`S:\PythonProject\ns\ns_evermore\.venv\Scripts\python.exe`，Python 3.10.11；已顺序安装 `requirements-backend.txt` 和 `requirements-runtime.txt`，`pip check` 通过。
- 日期：`2026-07-16T14:24:37+08:00`。
- 执行阶段：`P01 ns_common 公共基础设施加固`。
- 执行工作包：`P01-W01 扩展 NsConfig 与不可变配置快照`。
- 工作包状态：`VERIFIED`。
- 已完成内容：新增 runtime 配置总组和组 metadata；将配置模型转换为深度不可变快照；实现严格 dict/file 加载、JSON round-trip、同目录原子保存、显式环境校验、未知字段拒绝和 preferred/legacy 冲突拒绝。
- 修改的公共契约：新增并导出 `NsConfig`、`NsConfigGroupMetadata`、`NsRuntimeConfig` 及既有 backend/cache/log 配置类型；新增 `from_dict()`、`to_dict()` 和只读兼容属性；登记 `CFG-1` 为 `IN_PROGRESS`。
- 修改的配置组：backend、cache、log、runtime 总组及其 metadata；未建立 W03 的 runtime 细分组。
- 新增错误码：无；配置错误继续使用 `NsConfigError`。
- 新增或修改的 state key/Lua script：无。
- 执行的单元测试：`PYTHONPATH=src .venv/Scripts/python.exe -m unittest ns_common.tests -v`，13/13 通过。
- 执行的集成测试：无；W01 不涉及真实 Redis/Valkey、IAM、transport 或数据库集成。
- 执行的故障测试：无；故障注入不属于 W01。
- 回归测试结果：`PYTHONPATH=src .venv/Scripts/python.exe -m unittest discover -s src -p tests.py -v`，24/24 通过；`compileall`、`pip check`、示例 JSON 校验和 `git diff --check` 通过。
- 敏感信息扫描结果：未执行 P01-W09/W10 的自动泄露扫描；本工作包仅使用示例占位凭证和测试数据，未引入真实凭证。
- 未完成项：配置来源优先级与版本语义（W02）、runtime 细分配置组（W03）及 P01 其余工作包。
- 明确阻塞项：无。
- 下一工作包：`P01-W02 配置来源优先级与版本元数据语义`。
- 下一会话必须先阅读的本地文件：`docs/ns_runtime_design_checklist_0.0.2.md`、本实施文档、`src/ns_common/config.py`、`src/ns_common/tests.py`、`etc/ns_config.example.json`。

### 空白模板

- 本地仓库根目录：
- 当前分支或 detached 状态：
- 会话开始前已存在的工作区修改：
- 本次会话新增或修改的文件：
- 本地设计文档路径与版本：
- 本地实施文档路径与版本：
- Python 解释器与虚拟环境：
- 日期：
- 执行阶段：
- 执行工作包：
- 工作包状态：
- 已完成内容：
- 修改的公共契约：
- 修改的配置组：
- 新增错误码：
- 新增或修改的 state key/Lua script：
- 执行的单元测试：
- 执行的集成测试：
- 执行的故障测试：
- 回归测试结果：
- 敏感信息扫描结果：
- 未完成项：
- 明确阻塞项：
- 下一工作包：
- 下一会话必须先阅读的本地文件：

---

## 11. 实施文档维护规则

- 每个工作包开始前更新状态为 `IN_PROGRESS`。
- 工作包实现完成但测试未完成时使用 `IMPLEMENTED`。
- 只有全部验收和回归通过后使用 `VERIFIED`。
- 阶段内任何工作包 `FAILED` 或 `BLOCKED` 时，阶段不得标记 `VERIFIED`。
- 阶段出口修改公共契约时，必须更新接口冻结登记表。
- 新增公共基础设施时，必须先登记到 `ns_common` 公共基础设施表。
- runtime 私有协议和状态机不得进入 `ns_common`。
- 所有配置、state schema、Lua script 和协议变更都必须携带版本。
- 实现中发现设计边界冲突时，立即停止该工作包，把状态设为 `BLOCKED`，记录冲突条款；不得在代码中自行选择替代语义。
- 文档中不得用“已存在文件”代替测试证据，不得用“链路跑通”代替可靠性、恢复和安全验收。
- 每次新会话均从当前本地工作区读取事实；不得以远程仓库、之前会话摘要或提交历史覆盖本地状态。
- 本地工作区与账本状态不一致时，先执行 P00 重校准，再继续开发。
