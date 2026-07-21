# ns_runtime 历史验收日志

> 文档版本：`0.0.2`
> 当前状态与执行入口：[ns_runtime_implementation_plan_for_design_0.0.2.md](ns_runtime_implementation_plan_for_design_0.0.2.md)
> 长期架构决策：[ns_runtime_architecture_decisions_0.0.2.md](ns_runtime_architecture_decisions_0.0.2.md)
> 设计边界：[ns_runtime_design_checklist_0.0.2.md](ns_runtime_design_checklist_0.0.2.md)

本文件按完成时间升序保存历史验收证据，不作为当前执行游标或工作包状态的权威来源。当前状态只在实施计划中维护。原实施计划中的直接验收块与重复交接快照已合并；命令、通过数量、修改文件、隔离边界和仍影响后续工作的限制予以保留。

## P00

- 工作包：`P00 本地仓库基线与实施账本`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T13:55:23+08:00`。
- 修改文件：建立并校准 `docs/ns_runtime_implementation_plan_for_design_0.0.2.md`；只读核对 `docs/ns_runtime_design_checklist_0.0.2.md`、源码、配置、依赖和测试入口。
- 公共契约变化：无；仅建立本地能力、状态枚举、完成度、阶段顺序、测试层级和唯一执行游标的账本规则。
- 测试结果：执行 `python -m unittest discover -s src -p tests.py -v`，结果为 `FAILED (errors=1)`；活动解释器缺少 `concurrent-log-handler`，未进入既有 cache 用例。该失败作为基线环境事实记录，不代表后续共享隔离环境的结果。
- 安全/隔离检查：通过 `git status --short --branch`、`git submodule status` 和本地文件读取采集；未查询远程或提交历史，未迁移 schema、访问真实数据库/远程服务或发送业务消息。
- 已知限制：P00 只登记事实，不实现功能；当时的工作区快照和失败命令不再作为当前状态，当前基线以实施计划为准。
- 下一工作包：`P01-W01`。

## P01-W01

- 工作包：`P01-W01 扩展 NsConfig 与不可变配置快照`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T14:24:37+08:00`。
- 修改文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、当时的 `src/ns_common/tests.py`、`src/ns_backend/backend/settings.py`、`src/ns_backend/backend/db/routers.py`、`etc/ns_config.example.json` 和实施计划；测试后来迁移到 `tests/test_config.py`。
- 公共契约变化：新增并导出 `NsConfig`、`NsConfigGroupMetadata`、`NsRuntimeConfig` 及 backend/cache/log 配置类型；配置模型使用冻结 dataclass 和深度不可变 mapping/sequence，提供严格 `from_dict()`、`to_dict()`、原子 `save()`、显式环境校验和只读兼容属性；`CFG-1` 进入冻结流程。
- 测试结果：原验收执行 `PYTHONPATH=src .venv/Scripts/python.exe -m unittest ns_common.tests -v`，13/13 通过；`python -m unittest discover -s src -p tests.py -v`，24/24 通过。测试迁移后随 W02 重新执行 `tests.test_config` 24/24、根目录全量 35/35；`compileall`、`pip check`、示例 JSON 和 `git diff --check` 通过。
- 安全/隔离检查：配置测试只使用临时目录和显式配置路径；未迁移 schema、访问远程服务或发送业务消息。历史 W01 使用过仓库内 `.venv`，后续已删除并由 `S:\PythonVenv` 共享隔离环境取代。
- 已知限制：配置来源优先级和 metadata 生效语义留给 W02；runtime 细分配置及独立校验留给 W03。
- 下一工作包：`P01-W02`。

## P01-W02

- 工作包：`P01-W02 配置来源优先级与版本元数据语义`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T14:47:04+08:00`。
- 修改文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、`tests/__init__.py`、`tests/test_config.py`、`tests/test_cache.py`，删除旧测试位置 `src/ns_common/tests.py` 与 `src/ns_common/cache/tests.py`，并更新实施计划。
- 公共契约变化：新增 `NsConfigSource`、不可变 `NS_CONFIG_SOURCE_PRIORITY`、`NsConfigResolver`、`NsConfig.resolve()`、全局 config/policy version 和 `as_validated_snapshot()`；固定 `local_file < backend_override < validated_snapshot`，有效配置保存来源、版本、UTC 生效时间、rollback 来源和 apply mode。
- 测试结果：`$env:PYTHONPATH='src'; & 'S:\PythonVenv\ns_runtime\Scripts\python.exe' -m unittest tests.test_config -v`，24/24 通过；backend 环境根目录全量 35/35；`compileall`、两套环境 `pip check`、示例加载/JSON 校验、测试路径扫描和 `git diff --check` 通过。
- 安全/隔离检查：只使用临时目录、内存配置和 dummy/临时 SQLite cache；未访问 Redis/Valkey、backend 服务或远程资源；测试统一迁移到根 `tests/`。
- 已知限制：只冻结来源和 metadata；event loop、transport、state_store 等 runtime 细分组及环境硬规则留给 W03。
- 下一工作包：`P01-W03`。

## P01-W03

- 工作包：`P01-W03 建立 runtime 细分配置组`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T15:27:56+08:00`。
- 修改文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、`tests/test_config.py`、`etc/ns_config.example.json` 和实施计划。
- 公共契约变化：`NsRuntimeConfig` 新增 event_loop、transport、wire_codec、protocol、security、iam、state_store、routing、delivery、worker、pool、tenant_quota、cluster、recovery、observability、logging、debug 共 17 个强类型冻结子组，以及 transport adapter 配置、`RUNTIME_CONFIG_GROUP_NAMES` 和 `RUNTIME_CONFIG_APPLY_MODES`；`CFG-1` 冻结。
- 测试结果：runtime 环境 `tests.test_config` 35/35；backend 环境根目录全量 46/46（含 cache 11）；`compileall`、两套环境 `pip check`、示例配置加载、测试路径扫描和 `git diff --check` 通过。
- 安全/隔离检查：只使用临时目录、内存/示例配置和 dummy/临时 SQLite cache；未启动 transport、访问 Redis/Valkey/backend 或远程资源；prod 明文 transport、prod SQLite、非 `json.v1` 和未知字段均有拒绝验证。
- 已知限制：只定义配置契约；event loop 实现和 uvloop 平台矩阵留给 W04，对外监听仍须等待 P04。
- 下一工作包：`P01-W04`。

## P01-W04

- 工作包：`P01-W04 建立标准 asyncio event loop selector`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T15:42:59+08:00`。
- 修改文件：新增 `src/ns_common/async_runtime.py`、`tests/test_async_runtime.py`，修改 `src/ns_common/__init__.py` 和实施计划。
- 公共契约变化：新增并导出 `NsEventLoopFallbackWarning`、`NsEventLoopImplementation`、冻结 `NsEventLoopSelection`、显式 `NsEventLoopSelector`、`select_event_loop()` 和 `install_event_loop_policy()`；Linux auto 优先 uvloop 并可告警回退，Windows auto 固定标准 asyncio，显式 uvloop 不可用时失败，运行中切换返回 `restart_required`。
- 测试结果：runtime 环境 `tests.test_async_runtime` 14/14、`tests.test_config` 35/35；backend 环境根目录全量 60/60；`compileall`、两套环境 `pip check`、公共导出、测试路径和 `git diff --check` 通过。
- 安全/隔离检查：原验收未安装 uvloop、未修改依赖清单、创建 `src/ns_runtime`、启动 transport 或外部服务；平台和依赖通过显式注入验证，未改变全局 event loop policy。
- 已知限制：TaskSupervisor、取消顺序、关闭超时和悬挂任务报告留给 W05；真实 Linux/uvloop 见后续补验记录。
- 下一工作包：`P01-W05`。

## P01-W05

- 工作包：`P01-W05 建立统一 TaskSupervisor`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T15:56:02+08:00`。
- 修改文件：`src/ns_common/async_runtime.py`、`src/ns_common/__init__.py`、`tests/test_async_runtime.py` 和实施计划。
- 公共契约变化：新增并导出显式 `TaskSupervisor`/`NsTaskSupervisor`、`NsTaskSupervisorState`、`NsTaskFailure`、`NsTaskShutdownReport`、`NsUnfinishedTask`；提供 loop 绑定、唯一命名任务、异常消费/转发、按取消顺序分组关闭、全局 deadline、冻结报告、悬挂快照和幂等关闭，不使用全局 singleton 或隐式配置。
- 测试结果：runtime 环境 `tests.test_async_runtime` 23/23（其中 9 个 TaskSupervisor 用例）、`tests.test_config` 35/35；backend 环境根目录全量 69/69；`compileall`、两套环境 `pip check`、公共导出、测试路径和 `git diff --check` 通过。
- 安全/隔离检查：未增加外部依赖、创建 `src/ns_runtime`、启动 transport 或访问 backend/Redis/Valkey/远程资源；超时用例结束前显式释放测试任务；异常 handler 失败不覆盖原任务异常。
- 已知限制：只提供公共任务监督原语；进程信号、停止接入和 sink/client 清理留给 P02；其余 P01 公共能力仍按后续工作包实施。
- 下一工作包：`P01-W06`。

## P01-W04-WSL

- 工作包：`P01-W04 WSL 补充验收`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T16:05:57+08:00`。
- 修改文件：无仓库文件修改；只在既有 `/home/ns/.virtualenvs/ns_runtime` 安装 runtime 依赖和可选 `uvloop==0.22.1`，未修改仓库依赖清单。
- 公共契约变化：无；补验 W04 已冻结的 selector 契约。真实 Linux auto 选择 `uvloop`，`install_event_loop_policy()` 安装 `uvloop.EventLoopPolicy`，新建 loop 类型为 `uvloop.Loop`。
- 测试结果：Windows selector 14/14；WSL selector 13 通过、1 个 Windows 专用用例跳过；WSL async runtime 22 通过、1 跳过；隔离环境 `pip check` 通过。环境为 WSL2 `NsServer`、Ubuntu 22.04.5、kernel 6.18.33.2、Python 3.10.12。
- 安全/隔离检查：未在仓库或 `/mnt` 创建虚拟环境，未启动 transport、backend、Redis/Valkey 或其他外部服务；生产源码和测试未修改。
- 已知限制：只补验 selector，不改变工作包状态或执行游标；性能比较仍留给后续阶段。
- 下一工作包：`P01-W06`。

## P01-FIX-01

- 工作包：`P01-FIX-01 修正 runtime 集群角色配置语义`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T16:57:06+08:00`。
- 修改文件：`src/ns_common/config.py`、`src/ns_common/__init__.py`、`etc/ns_config.example.json`、`tests/test_config.py` 和实施计划；设计边界未修改。
- 公共契约变化：`NsRuntimeClusterConfig.role` 默认 `singleton`，只允许 `active_master`、`singleton`、`standby_master`、`sub_node`；`RUNTIME_CLUSTER_ROLES` 使用稳定顺序。静态启动角色与运行期角色/健康状态分离；配置为 `active_master` 不授予权威写权限。
- 测试结果：runtime 环境 `tests.test_config` 40/40、`tests.test_async_runtime` 23/23；backend 根目录全量 74/74；示例独立加载得到 `runtime.cluster.role=singleton`；`compileall`、两套环境 `pip check`、角色引用扫描和 `git diff --check` 通过。
- 安全/隔离检查：旧角色、运行期状态和健康状态只保留在拒绝测试中；未实现或调用 leader election、lease、fencing、集群协调写入或远程服务。
- 已知限制：不实现 P17 角色状态机、切换、epoch 或 fencing；`runtime.cluster.active_master_url` transport 语义保持未定义，须单独排期。
- 下一工作包：`P01-W06`。

## P01-W06

- 工作包：`P01-W06 建立 Clock 接口`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T17:01:39+08:00`。
- 修改文件：新增 `src/ns_common/time.py`、`tests/test_time.py`，修改 `src/ns_common/__init__.py` 和实施计划。
- 公共契约变化：新增 runtime-checkable `Clock`、无全局状态 `SystemClock`、显式注入 `ControlledClock` 及 `Ns*` 别名和 `UTC_EPOCH`；UTC wall clock 与 monotonic deadline 分离，可控 sleep 按 deadline/登记顺序唤醒并拒绝跨 loop。
- 测试结果：runtime 环境 `tests.test_time` 11/11；配置+async runtime+time 联合 74/74；backend 根目录全量 85/85；WSL time 11/11；`compileall`、两套环境 `pip check`、公共导出、生产源码测试路径、空白和 `git diff --check` 通过。
- 安全/隔离检查：未修改 Runtime Service、transport、IAM、state store、routing 或 delivery；测试时钟无需真实等待，取消会清理 waiter。
- 已知限制：只建立时间契约，不重构既有 config/logger/cache/backend 调用，也不实现 retry、lease 或 RuntimeContext 注入。
- 下一工作包：`P01-W07`。

## P01-W07

- 工作包：`P01-W07 建立 ID 生成和校验规则`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T17:23:24+08:00`。
- 修改文件：新增 `src/ns_common/identifiers.py`、`tests/test_identifiers.py`，修改 `src/ns_common/__init__.py` 和实施计划。
- 公共契约变化：九类 ID 固定为 `<类型前缀>_<32 位小写 RFC 4122 UUIDv4 hex>`；新增 `NsIdentifierKind`、冻结 `NsIdentifier`、只读注册表、显式 `IdentifierFactory`、通用生成/解析/校验入口和九个便捷生成函数。
- 测试结果：runtime 环境 `tests.test_identifiers` 8/8；配置+async runtime+time+identifiers 联合 82/82；backend 根目录全量 93/93；WSL identifiers 8/8；Windows 16 线程生成九类共 9000 个 ID，无冲突；`compileall`、两套环境 `pip check`、公共导出、路径/空白和 `git diff --check` 通过。
- 安全/隔离检查：未修改 backend IAM/JWT 既有 UUID、数据库 session ID 或其他组件标识语义；factory 显式注入，无全局服务依赖。
- 已知限制：只定义公共 ID；后续 Runtime Service、Envelope、delivery、stream、routing 和 management 显式消费；UUIDv4 ID 不作为凭证或授权证明。
- 下一工作包：`P01-W08`。

## P01-W08

- 工作包：`P01-W08 建立通用 retry/backoff 类型`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T17:39:14+08:00`。
- 修改文件：新增 `src/ns_common/retry.py`、`tests/test_retry.py`，修改 `src/ns_common/__init__.py` 和实施计划；未修改 backend IAM retry、Runtime Service、transport、state store、routing 或 delivery。
- 公共契约变化：新增 runtime-checkable `BackoffStrategy`、Fixed/Exponential/Jitter 策略、可注入 `RandomSource`、默认 5 次的冻结 `RetryBudget`、冻结 `RetrySchedule` 和 `schedule_next_retry()`；retry number 从 1 开始并与共享预算消耗解耦，同时保存 UTC 与 monotonic due time。
- 测试结果：runtime 环境 `tests.test_retry` 14/14；配置、async runtime、time、identifiers、retry 联合 96/96；backend 根目录全量 107/107；WSL retry 14/14；`compileall`、两套环境 `pip check`、公共导出、生产测试路径、空白和 `git diff --check` 通过。
- 安全/隔离检查：纯策略和值类型测试，不调用远程服务或持久化；非法参数使用 `NsValidationError`，注入源/策略非法状态使用 `NsStateError`。
- 已知限制：不实现异步 retry executor，不迁移 backend IAM 重试器；共享预算的权威原子消费属于 P08，priority/tenant/health/manual-only 策略属于 P12/P14。
- 下一工作包：`P01-W09`。

## P01-FIX-02

- 工作包：`P01-FIX-02 修复 retry 数值异常与 RetrySchedule 构造不变量`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T17:57:27+08:00`。
- 修改文件：`src/ns_common/retry.py`、`tests/test_retry.py` 和实施计划；未开始 W09，未修改 sanitizer/logger 或后续 runtime 层。
- 公共契约变化：公共名称不变；`_finite_number()` 的原生转换异常统一归一化；公开冻结 `RetrySchedule` 强制 retry number、delay、UTC/monotonic 时间、deadline 差值和 `RetryBudget` 不变量。直接参数错误为 `NsValidationError`，注入 strategy/Clock/random 源非法返回为 `NsStateError`。
- 测试结果：runtime 环境 `tests.test_retry` 19/19；配置、async runtime、time、identifiers、retry 联合 101/101；backend 根目录全量 112/112；新增覆盖超大 Fixed/Exponential/jitter、strategy/Clock 返回和非法直接构造；`compileall`、两套环境 `pip check` 和 `git diff --check` 通过。
- 安全/隔离检查：不泄露 `OverflowError`、`ValueError`、`TypeError` 等原生转换异常；未修改 backend IAM retry、transport、state store、routing 或 delivery。
- 已知限制：只收紧 W08 公共契约；异步执行、权威预算消费和后续调度语义仍属于后续阶段。
- 下一工作包：`P01-W09`。

## P01-W09

- 工作包：`P01-W09 建立统一 sanitizer`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T18:18:58+08:00`。
- 修改文件：新增 `src/ns_common/security.py`、`tests/test_security.py`，修改 `src/ns_common/__init__.py` 和实施计划；未修改 logger、HTTP client、异常注册表或后续 runtime 层。
- 公共契约变化：新增无全局状态 `Sanitizer`/`NsSanitizer`、`sanitize()`、`sanitize_url()`、`sanitize_text()` 和稳定占位常量；字段、路径和对象规则覆盖嵌套 mapping、dataclass、普通对象、异常 details、URL/文本、循环与深度。P01-FIX-03 后 peer/client/remote address 改为完全替换，capability 与证书摘要不承担不可恢复性保证。
- 测试结果：runtime 环境 `tests.test_security` 9/9；配置、async runtime、time、identifiers、retry、security 联合 110/110；backend 根目录全量 121/121；WSL security 9/9；`compileall`、两套环境 `pip check`、导出/路径/空白和 `git diff --check` 通过。
- 安全/隔离检查：测试对 token、payload、auth_context、fencing、capability、签名 URL、peer address 和证书原值执行零泄露断言；不修改原对象，不记录真实秘密。
- 已知限制：只提供显式 sanitizer，logger formatter 尚未接入；任意无字段名、无路径、无敏感标记的自由文本不能可靠推断为秘密。
- 下一工作包：`P01-W10`。

## P01-FIX-03

- 工作包：`P01-FIX-03 修复 P01-W09 sanitizer 泄露和异常安全问题`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T18:54:52+08:00`。
- 修改文件：`src/ns_common/security.py`、`tests/test_security.py` 和实施计划；未修改或接入 logger，未开始 W10。
- 公共契约变化：公共名称和调用签名不变；补齐 api_key、credential(s)、signature、原始 certificate、payload 后缀和 peer/client/remote IP/address 规则；完整替换 Authorization/Proxy-Authorization/Cookie/Set-Cookie 值；Mapping key 安全化并用稳定后缀保留冲突；对象异常行为 fail-closed；NaN/Infinity/过大整数转为严格 JSON-safe 占位符。地址只做完全替换，不使用无密钥摘要。
- 测试结果：runtime 环境 `tests.test_security` 22/22，每项执行 `json.dumps(result, allow_nan=False)` 和原始秘密零泄露断言；runtime 联合 123/123；backend 根目录全量 134/134；`compileall`、两套环境 `pip check` 和 `git diff --check` 通过。
- 安全/隔离检查：异常 `__str__()`、属性、Mapping `items()`、`vars()` 和 digest callback 的普通异常返回安全占位符；`KeyboardInterrupt`、`SystemExit` 保持穿透；未引入全局密钥、HMAC 系统或跨日志地址关联。
- 已知限制：W10 的 logger extra/exception 接入和完整日志链路泄露扫描仍未开始；无标签自由文本仍要求调用方提供结构化语义。
- 下一工作包：`P01-W10 把 sanitizer 接入 NsLogger`。

## P01-FIX-04

- 工作包：`P01-FIX-04 修复 sanitizer digest 路径资源消耗问题`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T21:32:53+08:00`。
- 修改文件：`src/ns_common/security.py`、`src/ns_common/__init__.py`、`tests/test_security.py`、实施计划、acceptance log 和 architecture decisions；未修改或接入 logger，未开始 W10。
- 公共契约变化：`Sanitizer` 新增可配置 digest 上限及只读属性，默认最大深度 32、遍历节点 4096、单容器项目 256、字符串 4096 字符、bytes 65536 字节、规范化结果 262144 字节；对应默认常量从 `ns_common.security` 和 `ns_common` 导出。digest 改为有界确定性规范化，遵守调用路径当前深度，mapping 与 set/frozenset 顺序稳定，循环安全结束；小型 bytes 直接对原始 bytes 计算 SHA-256，超限统一返回 `[REDACTED]`。
- 测试结果：runtime 环境 `tests.test_security` 30/30，每项新增结果均执行 `json.dumps(result, allow_nan=False)` 和原始秘密零泄露断言；runtime 联合 131/131；backend 根目录全量 142/142；`compileall`、runtime/backend 两套环境 `pip check` 和 `git diff --check` 通过。
- 安全/隔离检查：覆盖超大 bytes、超长字符串、超宽 capabilities/mapping、大型 dataclass/普通对象、深度、循环、容器/节点/规范化字节边界和稳定性；普通异常 fail-closed，`KeyboardInterrupt`、`SystemExit` 保持穿透；未直接无界序列化任意对象，未引入全局状态、硬编码密钥或真实超大内存分配。
- 已知限制：sanitizer 仍需调用方显式使用；W10 的 logger extra/exception 接入和完整日志链路泄露扫描尚未开始。
- 下一工作包：`P01-W10 把 sanitizer 接入 NsLogger`，状态保持 `NOT_STARTED`。

## P01-W10

- 工作包：`P01-W10 把 sanitizer 接入 NsLogger`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T21:50:06+08:00`。
- 修改文件：`src/ns_common/logger.py`、新增 `tests/test_logger.py`、实施计划、acceptance log 和 architecture decisions；`src/ns_common/security.py` 未修改。
- 公共契约变化：`NsLogger` 和 `get_ns_logger()` 新增可选显式 `Sanitizer` 注入，同名 logger 默认保留其拥有的 sanitizer，显式替换时重新配置全部 handler；`NsLogger.sanitizer` 提供只读访问。JSON/text/color formatter 在输出前把字符串消息、安全处理后的格式参数、extra/类 Envelope、异常对象和不含源码行的 traceback 元数据交给现有 sanitizer；JSON 输出改为严格 `allow_nan=False`，不再使用 `default=str` 直接字符串化任意对象。
- 测试结果：runtime 环境 `tests.test_logger` 9/9、logger+sanitizer 专项 39/39、runtime 联合 140/140、backend 根目录全量 151/151；真实 `NsLogger` handler 到临时日志文件的端到端输出通过严格 JSON 与零泄露检查；`compileall`、runtime/backend 两套环境 `pip check` 和 `git diff --check` 通过。
- 安全/隔离检查：消息对象和 `%` 格式参数在调用原始 `__str__()` 前先交给 sanitizer；extra、类 Envelope 和异常不直接序列化；异常 traceback 只保留 filename、lineno、function 元数据；普通对象失败保持 fail-closed，`KeyboardInterrupt`、`SystemExit` 保持穿透。Logger 未新增、复制或放宽任何 sanitizer 字段、路径、对象、摘要或资源限制规则。
- 已知限制：任意无字段名、无路径且无敏感标记的自由文本仍无法可靠推断为秘密；P01-W11 的完整错误注册表尚未开始。
- 下一工作包：`P01-W11 扩展 ns_common.exceptions 为错误注册表`，状态为 `NOT_STARTED`。

## P01-REF-01

- 工作包：`P01-REF-01 将 ns_common.config 从单模块拆分为包`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T22:15:11+08:00`。
- 修改文件：删除原 `src/ns_common/config.py`；新增 `src/ns_common/config/__init__.py`、`defaults.py`、`primitives.py`、`metadata.py`、`model.py`、`codec.py`、`validation.py`、`resolver.py` 以及 `groups/__init__.py`、`backend.py`、`cache.py`、`logging.py`、`runtime.py`；新增 `tests/test_config_package.py`；更新实施计划、acceptance log 和 ADR-001。已验证的 W10 logger 文件未在本工作包中继续修改，设计边界文档未修改。
- 公共契约变化：无。`ns_common.config` 由 module 改为 package，但 facade 保留原 69 个显式公共导出、既有导入路径、顶层 `ns_common` 对象身份、`ns_config` 初始化与访问行为；`NsConfig` 的 JSON、默认值、兼容别名、未知字段拒绝、原子保存、校验错误类型/details、来源优先级、backend override 和 validated snapshot 语义保持不变。内部路径不作为公共契约。
- 测试结果：runtime 环境原 `tests.test_config` 40/40、结构专项 `tests.test_config_package` 8/8、`tests.test_logger` 9/9、P01/runtime 联合 148/148；backend 环境根目录全量 159/159。全树 `compileall`、runtime/backend 两套环境 `pip check`、69 项公共导出完整性、冷启动全部配置子模块导入、backend settings 实际导入、生产源码内部 config 路径扫描和 `git diff --check` 均通过。
- 安全/隔离检查：primitives 不依赖配置组，groups 不依赖根模型，validation 不依赖 resolver 或文件 I/O，codec 不读取全局 `ns_config`，resolver 无注册副作用、全局可变对象、动态模块注入或 import hook；生产调用方继续只依赖 facade。未修改配置默认值、校验分支、错误 message/details、logger/sanitizer 行为、设计边界或后续 runtime 功能。
- 已知限制：pickle 仍不作为兼容承诺；为兼容直接构造 `NsConfigResolver()`，resolver 在未显式提供 `config_type` 时通过带说明的局部导入取得唯一根模型，常规 `NsConfig.resolve()` 始终显式注入类型，且冷启动循环导入检查通过。
- 下一工作包：`P01-W11 扩展 ns_common.exceptions 为错误注册表`，状态为 `NOT_STARTED`。

## P01-FIX-05

- 工作包：`P01-FIX-05 修复 NsLogger extra 覆盖核心日志字段的问题`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T23:32:40+08:00`。
- 修改文件：`src/ns_common/logger.py`、`tests/test_logger.py`、实施计划、acceptance log 和 ADR-009；`src/ns_common/security.py`、exceptions 和设计边界文档未修改。
- 公共契约变化：新增稳定 JSON 权威字段集合，包含 timestamp、level、logger、message、module、filename、lineno、func_name、process、process_name、thread、thread_name、exception、stack 和 `extra_fields`；与 Python LogRecord 内建保留字段分离。普通无冲突 extra 继续平铺；冲突 extra 统一进入 `extra_fields`，调用方同名 `extra_fields` 作为嵌套项保留。text/color 中 JSON 别名和 logging 核心占位符均使用 formatter 权威值。
- 测试结果：runtime 环境 `tests.test_logger` 11/11、logger+sanitizer 41/41、P01/runtime 联合 150/150；backend 根目录全量 161/161；`compileall`、runtime/backend 两套环境 `pip check` 和 `git diff --check` 通过。
- 安全/隔离检查：冲突字段中的 token、payload、Authorization、签名 URL、Cookie 等继续只交给现有 sanitizer；Mapping key 脱敏碰撞保留稳定后缀；JSON 继续严格 `allow_nan=False`；`KeyboardInterrupt`、`SystemExit` 保持穿透。Logger 未增加、复制或放宽 sanitizer 规则，ANSI 颜色仍读取原始 LogRecord level/status。
- 已知限制：Python logging 在 formatter 之前已拒绝直接覆盖 levelname、name、filename 等内建字段；FIX-05 额外隔离可进入 formatter 的 JSON 权威别名和 message/asctime 特例，不改变 logging 自身拒绝语义。
- 下一工作包：`P01-W11 将 ns_common.exceptions 包化并建立结构化错误注册表`，状态为 `NOT_STARTED`。

## P01-W11

- 工作包：`P01-W11 将 ns_common.exceptions 包化并建立结构化错误注册表`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-16T23:46:23+08:00`。
- 修改文件：删除原 `src/ns_common/exceptions.py`；新增 `src/ns_common/exceptions/__init__.py`、`base.py`、`metadata.py`、`registry.py`、`common.py`、`protocol.py`、`payload_ref.py`、`delivery.py`、`cluster.py`、`nack.py` 和 `tests/test_exceptions.py`；更新实施计划、acceptance log 和 architecture decisions。设计边界文档未修改。
- 公共契约变化：`ns_common.exceptions` 由单模块改为 package，facade 保持全部原异常与 `RUNTIME_NACK_REASON_ERROR_CODES` 的导入路径，既有 `ns_common` 顶层对象身份不变。33 个现有异常的构造参数、code、numeric_code、default_message、details 浅拷贝、继承关系、`to_dict()` 和 `__str__()` 保持原语义；新增冻结 `NsErrorDefinition`、稳定 `NsErrorSeverity`/`NsErrorCategory`、五组显式 definition 聚合、不可变 `NsErrorRegistry`、按类/code/numeric_code 查询、完整性验证、元数据 JSON 序列化和 NACK 映射验证。
- 测试结果：runtime 环境 `tests.test_exceptions` 18/18；W11 指定 exceptions/config/config package/logger/security/retry/async runtime 联合 149/149；P01/runtime 联合 168/168；backend 根目录全量 179/179。`compileall`、runtime/backend 两套环境 `pip check`、51 项 exceptions facade 公共导出、33 类对象身份、10 个 exceptions 模块冷启动导入、导入图无环、生产源码无内部 exceptions 路径依赖和 `git diff --check` 均通过。
- 安全/隔离检查：注册表使用显式 definition 元组聚合，不使用 decorator、import 副作用、动态模块扫描或 `__subclasses__()`；definitions、索引和注册表冻结，类/code/numeric_code 均为 33 个且全局唯一。metadata/registry 序列化不读取异常 details，不触发异常实例 `__str__()`；exceptions 不依赖 sanitizer/logger/config，原异常四字段序列化未附加 metadata。未读取远程、提交记录、PR 或 Issue，未开始 W12。
- 已知限制：W11 只登记当前已有 33 个异常；设计文档中的完整 `RUNTIME_*` 覆盖矩阵、错误 Envelope 和 retry/disconnect/audit 执行逻辑分别留给 W12、P03 和后续阶段。`safe_detail` 不代表任意 details 可直接输出。
- 下一工作包：`P01-W12 补齐设计文档已明确的 RUNTIME_* 错误覆盖矩阵`，状态保持 `NOT_STARTED`。

## P01-FIX-06

- 工作包：`P01-FIX-06 校准错误注册表中的通用异常策略语义`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T00:29:45+08:00`。
- 修改文件：`src/ns_common/exceptions/common.py`、`protocol.py`、`cluster.py`、`metadata.py`、`registry.py`、`tests/test_exceptions.py`、实施计划、acceptance log 和 ADR-015；设计边界文档、异常类实现、NACK 映射和 W12 错误矩阵未修改。本地校准会话开始时 `git status --short --branch` 仅显示干净的 `main...origin/main`。
- 公共契约变化：校准五个宽泛 definition 的默认策略提示。`NsDependencyError` 从 `retryable=True/action=retry_dependency` 改为 `retryable=False/action=inspect_dependency`，依据是其实际同时覆盖不受支持或缺失的 uvloop、初始化失败、HTTP 非法 JSON、timeout、请求/状态和客户端状态等不同场景；`NsStateError` 的布尔策略保持全 false，action 从 `stop_and_investigate` 改为 `investigate_state`，依据是其实际覆盖 event-loop 运行态、注入返回值、cache/client 状态等不同上下文，通用类型不能无条件提示停止；`NsHttpClientError` 从 `retryable=True/action=retry_http_request` 改为 `retryable=False/action=handle_http_failure`，依据是通用 HTTP 错误无法区分认证、参数、schema、TLS、DNS、连接和 timeout；`NsRuntimeProtocolError` 从 `disconnect_required=True` 改为 false，action 保持 `reject_protocol_message`，依据是通用协议错误无法区分单消息拒绝和连接级安全攻击；`NsRuntimeClusterCoordinationError` 从 `retryable=True/audit_required=True/action=retry_cluster_coordination` 改为 `retryable=False/audit_required=False/action=investigate_cluster_coordination`，依据是通用协调错误同时可能代表临时不可用、配置、状态、lease、fencing 或不可自动恢复问题。五项的 severity/category 均不变。
- 公共契约变化：其余 28 个 definition 经静态复核未改变。payload_ref validation unavailable/timeout、target unavailable、backpressure 继续可重试；source/auth_context forged、tenant mismatch 和 fencing 继续断连并审计；cluster state、role admission、startup security 保留各自审计/严重级别；协议版本不兼容和 Envelope schema 使用各自精确叶子 definition，不从通用 protocol definition 继承策略。metadata 明确策略只属于精确异常类型、不是无条件执行命令；查询继续使用 `type(error)` 且不做 MRO fallback。
- 测试结果：runtime 环境 `tests.test_exceptions` 23/23；W11 指定 exceptions/async runtime/logger/security/config/config package/retry 联合 154/154；P01/runtime 联合 173/173；backend 根目录全量 184/184。`compileall`、runtime/backend 两套环境 `pip check`、51 项 facade 公共导出、33 类/definition/code/numeric_code 唯一、严格 JSON、精确类型无 MRO fallback、10 个子模块冷启动、导入图无环、生产源码无内部 exceptions 路径依赖和 `git diff --check` 均通过。
- 安全/隔离检查：33 项显式 expected policy 矩阵覆盖 severity、category、retryable、disconnect_required、audit_required、safe_detail 和 action；实际调用场景通过注入模拟，不访问真实网络、uvloop、Redis、Valkey 或 backend。注册表仍显式聚合、冻结且无 decorator、import 副作用、动态扫描或 `__subclasses__()`；exceptions 仍不依赖 sanitizer/logger/config。未读取远程仓库、提交记录、PR 或 Issue，未开始 W12。
- 已知限制：通用 definition 只能提供保守提示；W12 才通过新增细粒度叶子错误表达 dependency/HTTP/protocol/cluster 的可重试、不可重试和安全处置差异。策略执行仍属于后续上下文和状态机，不由 registry 自动完成。
- 下一工作包：`P01-W12 补齐设计文档已明确的 RUNTIME_* 错误覆盖矩阵`，状态保持 `NOT_STARTED`。

## P01-W12

- 工作包：`P01-W12 补齐设计文档已明确的 RUNTIME_* 错误覆盖矩阵`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T01:10:53+08:00`。
- 修改文件：新增 `src/ns_common/exceptions/configuration.py`、`iam.py`、`processor.py`、`routing.py`、`transport.py`；更新 exceptions facade、common/protocol/delivery/cluster/metadata/registry/nack、`tests/test_exceptions.py`、实施计划和 acceptance log。设计边界文档与 ADR-015 未修改，`src/ns_runtime` 未创建。
- 公共契约变化：在保留既有 33 个异常的类名、code、numeric_code、构造、继承、details、`to_dict()` 和 `__str__()` 契约的基础上，新增 38 个细粒度叶子/领域异常和 11 个稳定 category，注册表扩展为 71 个 definition。新增冻结 `RUNTIME_ERROR_COVERAGE_MATRIX` 与完整性验证，覆盖 protocol、IAM、dependency、tenant、target、route、payload_ref、ACK、NACK、Defer、lease、fencing、owner、processor、configuration、transport、cluster、delivery 共 18 域、64 个 `RUNTIME_*` code；类/code/numeric_code 继续全局唯一，精确类型查询继续不做 MRO fallback。
- 公共契约变化：13 个 `RUNTIME_NACK_REASON_ERROR_CODES` reason 的稳定顺序保持不变，所有目标 code 统一收敛为已注册的细粒度 `RUNTIME_*` code；其中 dependency unavailable、node degraded、permission denied、invalid payload_ref 分别改为 `RUNTIME_DEPENDENCY_UNAVAILABLE`、`RUNTIME_CLUSTER_MEMBER_UNAVAILABLE`、`RUNTIME_IAM_DENIED`、`RUNTIME_PAYLOAD_REF_INVALID`。NACK 映射验证新增 `RUNTIME_` 前缀门禁。
- 测试结果：runtime 环境 `tests.test_exceptions` 24/24；W12 指定 exceptions/async runtime/logger/security/config/config package/retry 联合 155/155；P01/runtime 联合 174/174；backend 根目录全量 185/185。`compileall`、runtime/backend 两套环境 `pip check`、96 项 exceptions facade 公共导出、71 类/definition/code/numeric_code 唯一、18 域/64 码覆盖矩阵、13 个 NACK reason、严格 JSON、14 个子模块冷启动、导入图无环、生产源码无内部 exceptions 路径依赖和 `git diff --check` 均通过。
- 安全/隔离检查：新增细粒度错误根据精确语义独立声明 retry/disconnect/audit，新增 definition 的 `safe_detail` 全部保持 false；IAM 拒绝、route loop/hop、lease/fencing/owner、processor、配置和集群漂移等安全或权威状态错误要求审计。覆盖矩阵与 NACK 验证只读取冻结 definition 元数据，不读取异常 details、不触发异常字符串化，也不依赖 sanitizer/logger/config、网络、Redis、Valkey 或 backend。
- 已知限制：W12 只冻结错误类、code、category、策略 metadata、覆盖矩阵和 NACK 映射，不实现错误 Envelope、transport 库异常适配、IAM 调用、状态机副作用或策略执行；这些能力仍由 P03-P21 的对应阶段落地。新增 transport/cluster/lease 等错误不代表相关 runtime 功能已经启用。
- 下一工作包：`P01-W13 重构 HTTP client 创建方式与 owner 生命周期`，状态为 `NOT_STARTED`。

## P01-FIX-07

- 工作包：`P01-FIX-07 校准 W12 协议与 processor 错误策略，并补齐 protocol_violation 细粒度错误码`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T09:10:42+08:00`。
- 修改文件：`src/ns_common/exceptions/processor.py`、`protocol.py`、`nack.py`、`registry.py`、`__init__.py`、`tests/test_exceptions.py`、实施计划、acceptance log 和 ADR-015；未修改设计边界文档、HTTP client 或其他 runtime 功能，未创建 `src/ns_runtime`，未开始 P01-W13。本地校准开始和实施前再次执行 `git status --short --branch`，均只显示干净的 `main...origin/main`；未读取远程仓库、提交记录、PR 或 Issue。
- processor timeout 策略变化：`NsRuntimeProcessorTimeoutError` 从 `retryable=True/action=retry_processor_execution` 改为 `retryable=False/action=isolate_processor_timeout`；severity 继续为 warning，disconnect_required 继续为 false，audit_required 继续为 true，safe_detail 继续为 false。timeout 只证明调用未在期限内完成，不能证明 processor 未产生副作用、已成功取消、外部调用未成功、状态未写入或具备幂等性；未来实际 retry 必须由具体 processor 的幂等、状态和显式策略决定。
- protocol parse 策略变化：`NsRuntimeProtocolParseError` 从 `disconnect_required=True` 改为 false；retryable、audit_required、safe_detail 继续为 false，severity/category 和 `reject_unparseable_message` 保持不变。单条不可解析消息默认拒绝，但不直接等同于连接级攻击；连续畸形消息、超大帧、恶意资源消耗和握手失败仍留给后续精确错误、策略与连接状态处理。Envelope schema、协议版本、source/auth_context forged 和 tenant mismatch 的强制断连策略未削弱，其中 forged identity 与 tenant mismatch 继续审计。
- 新增协议违规错误：确认本地既有最高 numeric code 为 200163 且 200164 未占用后，新增 `NsRuntimeProtocolViolationError`，code 为 `RUNTIME_PROTOCOL_VIOLATION`，numeric code 为 `200164`，继承 `NsRuntimeProtocolError`；默认策略为 error/protocol、不可重试、默认不断连、要求审计、safe_detail=false、action=`reject_protocol_violation`。该叶子只表达已确认协议违规，不复制 forged identity 或 tenant mismatch 的强制断连语义。
- NACK 映射变化：13 个 reason 的顺序和文本均未改变，其他 12 个映射未改变；`protocol_violation` 从 `RUNTIME_PROTOCOL_ERROR` 改为 `RUNTIME_PROTOCOL_VIOLATION`。验证器新增精确叶子门禁，回退到宽泛领域基类会失败，所有 NACK code 继续要求已注册且使用 `RUNTIME_` 前缀。
- 覆盖与兼容性：最终共有 72 个异常类/definition、65 个 `RUNTIME_*` code、18 个 coverage 域、19 个独立人工冻结设计场景和 13 个 NACK reason；facade 有 97 项无重复公共导出。72 个类、code、numeric_code 全局唯一，最高 numeric code 为 200164。除上述两个 definition 的默认策略 metadata 外，既有 71 个异常的类名、模块路径、继承关系、code、numeric_code、default_message、构造签名、details、`to_dict()` 和 `__str__()` 均未改变；查询函数和验证函数调用方式、精确类型查询且无 MRO fallback 的语义均保持不变。新增错误继续使用既有构造和四字段序列化。
- 独立门禁与负向测试：新增不由 registry、coverage matrix、异常类遍历或 Markdown 生成的 `REQUIRED_RUNTIME_ERROR_SCENARIOS`。门禁检查 scenario 名/code 唯一、`RUNTIME_` 前缀、code 已注册且已进入 coverage；负向覆盖 coverage 缺少 violation、scenario 未注册、scenario 未覆盖、scenario 重复 code、NACK 回退宽泛 protocol code、processor timeout 恢复 retryable 和 protocol parse 恢复强制断连。
- 测试结果：runtime 环境 `tests.test_exceptions` 26/26；W12 指定 exceptions/async runtime/logger/security/config/config package/retry 联合 157/157；P01/runtime 联合 176/176；backend 根目录全量 187/187。全树 `compileall`、runtime/backend 两套环境 `pip check`、exceptions facade 公共导出、类/code/numeric_code 唯一性、覆盖矩阵、独立设计场景、NACK 映射、14 个子模块冷启动导入、导入图无环、生产源码内部 exceptions 路径扫描和 `git diff --check` 均通过。
- 安全/隔离检查：注册和覆盖继续使用显式冻结聚合，不使用 decorator、import 副作用、动态扫描或 `__subclasses__()`；exceptions 不依赖 sanitizer/logger/config，metadata 不读取异常 details，新增与校准 definition 的 safe_detail 均为 false。未修改 `NsRuntimeProcessorFailedError`，静态检查未发现其现有保守隔离与审计策略和设计直接冲突。
- 已知限制：本修复只冻结默认策略 metadata、精确协议违规错误、NACK 映射和测试门禁；不实现 processor 幂等判定、取消确认、自动 retry 决策、协议滥用检测、频率计数、限流、断连升级、连接状态机或错误 Envelope。P01-W13 的 HTTP client 生命周期重构保持 `NOT_STARTED`。
- 下一工作包：`P01-W13 重构 HTTP client 创建方式与 owner 生命周期`，状态为 `NOT_STARTED`。

## P01-W13

- 工作包：`P01-W13 重构 HTTP client 创建方式与 owner 生命周期`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T11:36:05+08:00`。
- 修改文件：`src/ns_common/http_client.py`、`src/ns_common/__init__.py`，新增 `tests/test_http_client.py`，更新实施计划、acceptance log 和新增 [ADR-016](ns_runtime_architecture_decisions_0.0.2.md#adr-016)。未修改设计边界文档，未创建 `src/ns_runtime`，未开始 P01-W14。
- 本地基线校准：当前工作区为 Ubuntu 22.04.5 LTS / WSL2 中的 `/mnt/s/PythonProject/ns/ns_evermore`，对应 Windows `S:\PythonProject\ns\ns_evermore`；分支为 `main`，实施前 `git status --short --branch` 仅显示本地跟踪信息且工作树干净，子模块状态无输出。使用 Python `3.10.12`、`/home/ns/.virtualenvs/ns_runtime` 和 `/home/ns/.virtualenvs/ns_backend`；未在仓库或 `/mnt` 下创建虚拟环境。未读取远程仓库、提交历史、PR 或 Issue。
- 公共契约变化：新增 `NsHttpClientFactory.create()`，每次返回不登记全局 map 的独立 caller-owned `NsAsyncHttpClient`；新增 `NsHttpClientOwner`、`NsHttpClientOwnerState.OPEN/CLOSING/CLOSED` 和 `NsAsyncHttpClient.is_closed`。Owner 只管理自己创建的 client，开始关闭后拒绝新建，在同一 event loop 中串行化并发 `aclose()` 并按创建逆序回收。取消或普通关闭异常不丢失未回收 client，后续可重试；单个普通异常不阻断其他 client 关闭，聚合 details 只包含 client 名和异常类型。
- 兼容与依赖边界：`get_async_http_client()` 和 `aclose_http_clients()` 的原按名称缓存/清理入口继续存在，内部创建收敛到 factory；显式 factory/owner 不读写兼容 map，即使 client 同名也与 legacy 实例隔离。`ns_common.http_client` 和 `ns_common` facade 导出权威对象，runtime 后续只允许 composition root 创建 owner/client 并向下注入显式实例。
- 测试结果：`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest tests.test_http_client -v` 通过 7/7；HTTP/exceptions/async runtime/logger/security/config/config package/retry/time/identifiers 指定联合为 `Ran 183, OK (skipped=1)`；`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest discover -s tests -p 'test_*.py' -v` 根目录全量为 `Ran 194, OK (skipped=1)`。两个跳过记录均是 WSL 下的同一 Windows 专用 event-loop 用例。runtime 环境直接 discover 依旧因不安装 Django 无法导入 `tests.test_cache`，因此 cache 及根回归按文档要求使用 backend 隔离环境，未把缺少 Django 解释为 W13 失败。
- 静态与环境检查：全树 `compileall` 通过；runtime/backend 两套虚拟环境 `pip check` 均报告 `No broken requirements found`；HTTP facade 7 项、`ns_common` facade 146 项导出均无重复且权威对象一致；独立解释器冷启动导入通过。生产源码扫描只在兼容函数本身发现 `get_async_http_client(`，`src/ns_runtime` 仍不存在，`src/` 下无 `test_*.py`/`tests.py`，`git diff --check` 通过。
- 安全/隔离检查：专项测试只构造和关闭 httpx client，不发送真实网络请求，不访问 backend、Redis、Valkey 或真实数据目录。关闭失败聚合不包含底层异常文本；`KeyboardInterrupt`/`SystemExit`/cancellation 不被当作普通关闭异常吞掉，取消后仍保留 client 所有权。旧 HTTP response body preview、URL 和 request error 输出未在本工作包中被误标为安全。
- 已知限制：W13 只冻结 client 创建与 owner 生命周期。当前 `NsHttpResponse.json()`、status error、request error 和 completion log 仍可保留原始 body preview、URL 或底层错误文本；可注入 response sanitizer、IAM token URL/日志/错误零泄漏属于 P01-W14。P02 尚未把 owner 接入进程启停，P06 尚未创建 IAM client。
- 下一工作包：`P01-W14 安全化 HTTP 错误响应与 response sanitizer`，状态为 `NOT_STARTED`。

## P01-W14

- 工作包：`P01-W14 安全化 HTTP 错误响应与 response sanitizer`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T13:51:53+08:00`。
- 修改文件：`src/ns_common/http_client.py`、`src/ns_common/__init__.py`、`tests/test_http_client.py`，更新实施计划、acceptance log 并新增 [ADR-017](ns_runtime_architecture_decisions_0.0.2.md#adr-017)。未修改设计边界文档，未创建 `src/ns_runtime`，未开始 P01-W15。
- 公共契约变化：`NsHttpResponse` 新增不参与 repr/equality 的 `safe_url` 与 `safe_body_summary`；HTTP status 和 JSON decode 错误从原始 `body_preview` 改为固定摘要，默认只包含 `present`、`text_length` 和可选的固定 `body_format=json/text/binary/other`。新增公开 `NsHttpResponseSanitizer` 同步回调类型；`NsAsyncHttpClient`、factory、owner、legacy getter 可配置默认回调，request/get/post/put/delete 可逐请求覆盖。回调接收隔离快照，只能返回 mapping 或 `None`，输出再次交给公共 `Sanitizer`；普通失败与非法返回 fail-closed，不改变真实响应状态或泄露失败文本。
- URL、token 与异常边界：`bearer_token` 只写入 Authorization header；params 在检查与发送前冻结，当前 token 若出现在解析后的 base/request URL 或 params 中，会在网络调用前以稳定 `NsValidationError` 拒绝且 details 不含 token。completion log、status/JSON/request error 只使用安全 URL；响应 URL path 若反射当前 bearer token，整条诊断 URL 替换。request failure 不再复制底层异常文本或保留可输出的异常 context，invalid JSON 不再保留含原始 doc 的 `JSONDecodeError` context。成功响应的原始 `text`、`url` 和 `json()` 正常语义保持兼容。
- 测试结果：runtime 环境 `tests.test_http_client` 14/14；HTTP/exceptions 定向联合 40/40；HTTP/exceptions/async runtime/logger/security/config/config package/retry/time/identifiers 的 P01/runtime 联合为 `Ran 190, OK (skipped=1)`；backend 根目录全量为 `Ran 201, OK (skipped=1)`。两个跳过记录均为 WSL 下同一 Windows 专用 event-loop 用例。
- 静态与环境检查：全树 `compileall` 通过；runtime/backend 两套虚拟环境 `pip check` 均报告 `No broken requirements found`；HTTP facade 8 项、`ns_common` facade 147 项导出无重复且 `NsHttpResponseSanitizer` 对象一致；独立解释器冷启动导入通过。生产源码不再包含 `body_preview`、response text slice 或底层异常字符串化，旧全局 getter 只在兼容函数定义中出现；`src/ns_runtime` 仍不存在，`src/` 下无 `test_*.py`/`tests.py`，`git diff --check` 通过。
- 安全/隔离检查：专项测试使用内存 stub response/error，不发送真实网络请求，不访问 backend、Redis、Valkey 或真实数据目录。IAM 401/503 模拟同时放入 bearer token、access/refresh token、client secret、无标签正文 secret、签名 URL token、反射 URL path 和底层 transport/callback failure secret；错误序列化与 logger 入参均逐值验证零泄漏。sanitizer 快照修改不能把 401 改为成功，普通 callback 失败安全关闭；进程级异常继续不被 `Exception` 分支吞掉。
- 已知限制：response sanitizer 是同步、无 I/O、由调用方负责 schema 语义的诊断适配器；公共 sanitizer 无法证明任意无标签字符串安全，因此回调不得返回未经语义筛选的原始正文。token URL guard 保护通过 `bearer_token` 参数提供的当前凭据，不把未来 payload_ref 所需的全部签名 query URL 一律禁止。P02 尚未接入 owner，P06 尚未创建真实 IAM client；P01-W15 至 P01-W17 尚未完成。
- 下一工作包：`P01-W15 建立 MetricsSink、TraceSink、DiagnosticSnapshotSink 接口和内存测试实现`，状态为 `NOT_STARTED`。

## P01-W15

- 工作包：`P01-W15 建立 MetricsSink、TraceSink、DiagnosticSnapshotSink 接口和内存测试实现`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T14:55:21+08:00`。
- 修改文件：新增 `src/ns_common/observability.py` 和 `tests/test_observability.py`，更新 `src/ns_common/__init__.py`、实施计划、acceptance log，并新增 [ADR-018](ns_runtime_architecture_decisions_0.0.2.md#adr-018)。设计边界文档未修改，未创建 `src/ns_runtime`，未开始 P01-W16。
- 公共契约变化：新增 runtime-checkable `MetricsSink`、`TraceSink`、`DiagnosticSnapshotSink`，统一使用同步本地 `record()`、异步 `flush()`/`aclose()` 和显式实例注入，不绑定 HTTP/OTLP exporter 或全局 client。新增 UTC、冻结、严格 JSON-safe 的 `NsMetricRecord`、`NsTraceRecord`、`NsDiagnosticSnapshot`，构造时使用显式或隔离默认 `Sanitizer` 脱敏；新增 metric/trace/sink 状态枚举、plain/`Ns` 兼容别名和安全 `to_dict()`。记录限制为 256 KiB；普通失败记录稳定 fail-closed 状态，进程级异常保持穿透。
- 指标与内存实现：公共常量精确预留设计要求的 8 个 event-loop、10 个通用 transport 和 17 个 QUIC/WebTransport 标准指标名。metric 标签限 32 项且仅接受有限标量，connection/session/transport/path/message/summary/delivery/stream/plan/operation/trace/span/request/correlation/raw tenant ID 等键按大小写和分隔符归一后拒绝，`runtime_id` 与受控 `tenant_scope` 保留。三个内存 sink 使用锁保护、有界 deque、只读 tuple 快照、oldest-drop 计数、测试清理和幂等关闭；关闭后写入返回稳定状态错误，不承担持久化语义。
- 测试结果：runtime 环境 `tests.test_observability` 13/13；observability/HTTP/exceptions/async runtime/logger/security/config/config package/retry/time/identifiers 的 P01/runtime 联合为 `Ran 203, OK (skipped=1)`；backend 环境根目录全量为 `Ran 214, OK (skipped=1)`。两个跳过记录均为 WSL 下同一 Windows 专用 event-loop 用例；backend 全量包含既有 cache 回归。
- 静态与环境检查：全树 `compileall` 通过；runtime/backend 两套虚拟环境 `pip check` 均报告 `No broken requirements found`；`ns_common` 181 项和 observability 34 项 facade 导出无缺失、无重复，35 个标准指标名唯一；独立解释器冷启动导入通过。observability 无 httpx/requests/aiohttp、`ns_runtime`、`ns_config` 或 legacy HTTP getter 依赖；`src/` 下无测试文件，仓库内无虚拟环境，`src/ns_runtime` 仍不存在，`git diff --check` 通过。
- 安全/隔离检查：专项测试覆盖 token、Authorization、Bearer 文本、payload、嵌套对象、输入后续变更、非法/过大记录、普通 sanitizer/Mapping 失败和进程级异常；所有公开序列化均以 `allow_nan=False` 验证且秘密零泄露。测试只使用内存记录、线程池和隔离事件循环，不发起网络请求，不访问 backend、Redis、Valkey 或真实数据目录；观测数据不进入 DeliveryRecord、ACK 或控制审计事务。
- 已知限制：W15 只提供公共记录、sink 协议和内存测试实现；尚未实现 runtime event-loop/transport 采集器、远程 exporter、采样器、聚合器、target health 或 P20 故障注入。公共 sanitizer 仍不能证明任意无标签自由文本安全，调用方必须提供结构化语义；外部 adapter 的非阻塞、丢弃和 exporter conformance 需要在 P20 验证。
- 下一工作包：`P01-W16 建立 ns_common.testing 测试工厂`，状态为 `NOT_STARTED`。

## P01-FIX-08

- 工作包：`P01-FIX-08 加固观测 sink 故障隔离、metric 基数门禁和完整记录大小限制`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T16:44:27+08:00`。
- 修改文件：`src/ns_common/observability.py`、`src/ns_common/__init__.py`、`tests/test_observability.py`、实施计划、acceptance log 和 ADR-018；设计边界文档未修改，`src/ns_runtime` 未创建，P01-W16 未开始。会话开始实时执行 `git status --short --branch`，结果仅为干净的 `main...origin/main`；全过程只使用当前本地文件，不读取远程仓库、提交历史、PR、Issue 或远程分支，不切换、重置或清理工作区。
- 三个修复问题：关闭后的内存 sink 原先抛 `NsStateError`，会把正常关闭竞态扩散到业务主链路；metric attribute 原先只做高基数 key 精确黑名单且允许任意标量值，别名和唯一字符串可绕过；`MAX_OBSERVABILITY_RECORD_BYTES` 原先只检查 attributes/snapshot 子 mapping，完整公开 record 的固定字段开销未计入。FIX-08 分别改为关闭后原子拒绝、显式有限 metric definition/schema 和完整 `to_dict()` 严格 JSON 字节门禁。
- sink 行为与计数：三个内存 sink 在 `OPEN` 且类型正确时继续返回 `True`；`CLOSED` 后类型正确的 `record()` 返回 `False`，不修改 records、不增加 `dropped_count`，并在同一锁内增加只读 `rejected_count`。`dropped_count` 只表示容量已满时 deque 淘汰的最旧记录数量；`rejected_count` 只表示关闭后的拒绝。`clear()` 清空 records 并重置 `dropped_count`，不重置生命周期级 `rejected_count`；`flush()` 关闭前后均为安全 no-op，`aclose()` 继续幂等。类型错误仍抛 `NsValidationError`，进程级异常继续穿透。并发门禁以 8 个写线程共 800 次调用和一个关闭线程验证：每次调用只可能完整接受或完整拒绝，最终 records 数等于 `True` 数、`rejected_count` 等于 `False` 数，且无状态异常或部分写入。
- metric schema 与 cardinality：新增冻结 `NsMetricAttributeValueType`、`NsMetricAttributeDefinition`、`NsMetricDefinition`、`NsMetricTenantScope` 及 plain alias。string 与 integer attribute 必须提供非空不可变有限允许集合，boolean 使用有限布尔值域；float、任意未登记 integer/string、list/tuple/mapping/object 均拒绝。raw schema 通过后交给公共 `Sanitizer`，sanitized key/value 再按同一 definition 复核并深度冻结。非标准 metric attributes 为空时可省略 definition；attributes 非空时必须显式提供同名 definition。标准 metric 不能用显式 definition 覆盖权威 schema。
- 高基数与 tenant 边界：保留 `HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS`，并把 key 规范化为 compact form后对明确 identifier 后缀匹配；除原 key 外，`target_connection_id`、`current_session_id`、`source_message_id`、`original_delivery_id`、`customer_tenant_id`、`worker_trace_id`、`peer_request_id`、`transport.connection.id` 等前缀/大小写/点/横线/下划线别名均拒绝，不因普通单词仅包含 `id` 而误拒绝。`tenant_scope` 最终固定为 `system`、`tenant`、`cross_tenant`、`shared`、`unknown`，原始 tenant ID、邮箱和随机唯一值均拒绝。
- 标准 registry：新增只读 `RUNTIME_STANDARD_METRIC_DEFINITIONS`，与既有 8 个 event-loop、10 个通用 transport、17 个 QUIC/WebTransport 名称一一对应，数量仍为 35、名称全局唯一、key 与 `definition.name` 一致。每项都有显式 schema且不存在 wildcard；明确有限的 event-loop implementation、runtime component、transport type、component type 和 tenant scope 才开放，其余 schema 保守为空。尚未由真实 collector 确认的 kind/unit 保持 `None`，不据名称猜测业务统计语义。
- 完整 record 大小：`MAX_OBSERVABILITY_RECORD_BYTES=262144` 现在表示完整公开 `to_dict()` 使用 `allow_nan=False`、`ensure_ascii=False`、`separators=(",", ":")`、`sort_keys=True` 后的 UTF-8 最大字节数。metric/trace 在规范化、脱敏、冻结后检查完整 record，超限抛稳定 `NsValidationError`，details 只有 `field=record`、`maximum_bytes`、`actual_bytes` 和 `record_type`，不复制内容、秘密或底层 JSON exception context。diagnostic snapshot 先检查完整 record，超限后替换为 `{"observability_status":"size_limit_exceeded"}` 并再次完整编码；占位仍超限则稳定验证失败。代表性完整记录严格编码结果为 metric 220 字节、trace 150225 字节、diagnostic 150098 字节，均不超过 262144；专项另覆盖 mapping 本身低于边界但固定字段使完整 record 超限、多字节 UTF-8 按字节超限和降级占位复检。
- 公共导出：observability facade 从 34 项增至 43 项、`ns_common` facade 从 181 项增至 190 项，共新增 9 个公共名称：四个 `Ns*` 类型、四个对应 plain alias 和标准 definition registry。两个 facade 均无重复/缺失，plain/`Ns` alias、子 facade/顶层 facade 对象身份一致，独立解释器冷启动导入和 observability 依赖图无环。
- 测试结果：observability 专项 `Ran 23, OK`；用户指定的 observability/security/logger/http_client/exceptions/async_runtime/config/config_package/retry/time/identifiers 联合回归 `Ran 213, OK (skipped=1)`；backend 根目录全量回归 `Ran 224, OK (skipped=1)`。两个跳过记录均是 WSL 下同一 Windows 专用 event-loop 用例。全树 `compileall`、runtime/backend 两套 `pip check`、facade/对象身份、35 项 registry、完整 record 字节、独立解释器冷启动、导入循环、禁止 exporter/runtime/global sink 单例依赖、生产源码测试文件、仓库虚拟环境扫描和 `git diff --check` 均通过。
- 已有成功路径：OPEN sink 正确类型记录、容量淘汰、flush/aclose、标准 metric 空 attributes、已登记有限 attributes、trace 高基数 context、diagnostic snapshot 和三类 `to_dict()` schema 保持成功；完整公开字段名称未改变。原先可成功的任意 metric key/value 路径被有意收紧为显式有限 schema，关闭后的状态异常路径被有意改为 `False`，这两项属于 FIX-08 的契约修复而非兼容保留。
- 安全/隔离检查：token、Authorization、Bearer、payload、auth_context、签名 URL、嵌套对象、Mapping 读取失败和普通 sanitizer 失败均通过严格 JSON 与零秘密泄露断言；sanitizer 前后 schema 均验证，`KeyboardInterrupt`/`SystemExit` 穿透。未增加 exporter、采集器、OTLP、Prometheus、runtime event-loop/transport collector、HTTP client、网络 I/O、Redis/Valkey、后台线程/task、全局 mutable sink、DeliveryRecord、ACK、控制审计或任何强一致写入。
- 已知限制：当前只冻结公共记录、definition 与内存 sink；真实 P02/P04 collector 在使用对应 metric 前仍须补齐已确认的 kind/unit 和更具体的有限值域，P20 才负责 exporter、采样/聚合、全量 observability pipeline 与故障注入。`MAX_METRIC_ATTRIBUTE_VALUE_LENGTH` 继续作为 256 字符的额外资源保护；trace 和 diagnostic snapshot 仍可携带高基数 ID，但必须通过脱敏和完整 record 大小门禁。
- 下一工作包：`P01-W16 建立 ns_common.testing 测试工厂`，状态保持 `NOT_STARTED`；唯一执行游标已指向 P01-W16。

## P01-W16

- 工作包：`P01-W16 建立 ns_common.testing 测试工厂`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T17:33:12+08:00`。
- 修改文件：新增 `src/ns_common/testing.py` 和 `tests/test_testing.py`，更新 `src/ns_common/__init__.py`、实施计划、acceptance log，并新增 [ADR-019](ns_runtime_architecture_decisions_0.0.2.md#adr-019)。设计边界文档未修改，`src/ns_runtime` 未创建，P01-W17 未开始。会话开始实时执行 `git status --short --branch`，结果仅为干净的 `main...origin/main`；未读取远程仓库、提交历史、PR、Issue 或远程分支，未切换、重置或清理工作区。
- 公共工厂与目录契约：新增实例级 `NsTestResourceFactory` 及 plain alias。每个 factory 创建唯一临时根目录和 `data/etc/log/tmp` 子目录，context/显式 `close()` 幂等回收仍持有的端口及整个根目录，关闭后拒绝创建资源；不修改 `NS_ENV`、仓库路径常量、全局 `ns_config`、cache/http client 或全局 sink。`NsTemporaryDirectories.contains()` 可验证显式路径边界，factory 并发创建的 400 个 Redis namespace 全部唯一。
- 临时配置契约：`create_temporary_config()` 返回冻结 `NsTemporaryConfig`，同时提供显式配置文件、`NsConfig` 快照、目录和配套 Redis namespace。默认生效时间固定为 UTC epoch；调用方 override 先深复制合并，再强制 cache/runtime SQLite、backend SQLite、日志锁目录和 cache/runtime namespace 回到当前 factory 边界，输入 mapping 不被修改。文件名只允许安全 basename且不覆盖同一 factory 已存在文件；保存/重载保持同一快照，不读取或替换全局 `ns_config`。
- clock、sink 与端口契约：`create_controlled_clock()` 每次返回新的 `ControlledClock`；`create_in_memory_sinks()` 每次返回类型校验的 metrics/trace/diagnostic 有界内存 sink bundle，支持统一 `clear()` 和异步幂等关闭。`reserve_tcp_port()` 使用 IPv4 TCP port 0 让 OS 分配端口并保持 listening socket 绑定，调用方可直接取得 socket，避免“探测后关闭再绑定”的正常竞态；reservation 与 factory 关闭均幂等释放，已释放 socket 不可重新获取。
- Redis namespace 契约：新增冻结 `NsRedisNamespace`，由安全 `key_prefix`、scope 和 UUID 形成唯一 `key_prefix:namespace:`；提供安全 key 构造、所有权判断、同步/异步 `cleanup()` 及进入/退出双清理的 `manage()`/`amanage()`。清理只调用注入 client 的 `scan_iter(match=prefix*)` 与最多 500 项的批量 `delete()`，逐 key 再校验前缀；client 返回外部 key 时停止且不删除该 key。实现不导入 Redis/Valkey 驱动，不调用 `KEYS`、`FLUSHDB`、`FLUSHALL`，也不持有或关闭调用方 client。
- 公共导出：`ns_common.testing` 冻结 14 项唯一导出，包括两个常量、六个 `Ns*` 类型与六个 plain alias；`ns_common` facade 从 190 项增至 204 项。子模块/顶层 facade 和 plain/`Ns` alias 对象身份一致，冷启动可在未安装 `redis`/`valkey` Python 包且不存在 `ns_runtime` 时导入。
- 测试结果：runtime 环境 testing 专项 `Ran 20, OK`；testing/observability/security/logger/http_client/exceptions/async_runtime/config/config_package/retry/time/identifiers 的 P01/runtime 联合为 `Ran 233, OK (skipped=1)`；backend 环境根目录全量为 `Ran 244, OK (skipped=1)`。两个跳过记录均为 WSL 下同一 Windows 专用 event-loop 用例，backend 全量继续包含既有 cache 回归。
- 真实依赖验证：本机 `/usr/bin/redis-server` 以 factory 随机保留端口、临时工作目录、关闭 RDB save 与 AOF 的 standalone 进程启动；真实 RESP `SET/GET/SCAN/DEL` 验证进入时删除 stale key、退出时删除 body key，同时另一唯一 namespace 和无关 `application:shared:*` key 完整保留。测试结束终止进程并删除临时目录；无 Redis 进程或 `ns-test-*` 目录残留。该证据只验证真实 standalone namespace 隔离，不把普通 cache 或测试 namespace 误标为强一致 StateStore。
- 静态与环境检查：全树 `compileall` 通过；runtime/backend 两套虚拟环境 `pip check` 均报告 `No broken requirements found`；testing 14 项和 `ns_common` 204 项 facade 无缺失/重复且对象身份一致；AST/冷启动扫描确认 testing 不依赖 `redis`、`valkey` 或 `ns_runtime`。`src/` 下无 `test_*.py`/`tests.py`，仓库内无虚拟环境，测试后无临时目录/Redis 进程残留，`git diff --check` 通过。
- 安全/隔离检查：专项覆盖两个 factory 目录/clock/sink/namespace 互不共享、并发 namespace 无冲突、配置 override 无法把已知 SQLite/log 路径写回仓库、端口 reservation 在释放前无法重复绑定、同步/异步异常退出后 namespace 被清理、恶意 scan 越界 fail-closed、其他 namespace/共享 key 不删除。测试除临时 loopback Redis 外不访问外部网络、backend、开发者真实数据库或仓库 `data/etc/log/tmp`；未增加后台线程/task、全局 mutable registry、runtime 私有类型、DeliveryRecord、ACK 或任何强一致写入。
- 已知限制：Redis/Valkey Python 驱动及独立测试依赖清单属于 P01-W17，当前公共模块只接受调用方注入的 sync/async compatible client；client 与 server 生命周期仍由调用方拥有。退出清理前必须停止继续写入该 namespace 的 task/process。真实验收只覆盖 Redis standalone，不覆盖 Sentinel/Cluster、多节点、TLS、StateStore Lua/CAS/lease/fencing 或 P20 故障注入。第三方 server 不接受现有 socket 时，reservation 释放到 server 绑定之间仍存在不可消除的交接窗口，调用方不得把曾经探测为空闲解释为持续所有权。
- 下一工作包：`P01-W17 建立 runtime 独立生产/测试依赖清单`，状态为 `NOT_STARTED`。

## P01-W17

- 工作包：`P01-W17 建立 runtime 独立生产/测试依赖清单`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T18:58:08+08:00`。
- 修改文件：新增 `requirements-common.txt`、`requirements-runtime-test.txt`、`requirements-runtime-benchmark.txt` 和 `tests/test_dependency_manifests.py`；重构 `requirements-runtime.txt`、`requirements-backend.txt`；更新 `src/ns_common/logger.py`、`src/ns_common/cache/clients.py`、`tests/test_logger.py`、`tests/test_testing.py`、实施计划、acceptance log，并新增 [ADR-020](ns_runtime_architecture_decisions_0.0.2.md#adr-020)。设计边界文档未修改，`src/ns_runtime` 未创建，P02-W01 未开始。会话开始实时执行 `git status --short --branch`，结果为干净的 `main...origin/main`；未读取远程仓库、提交历史、PR、Issue 或远程分支，未切换、重置或覆盖工作区。
- 依赖分层契约：建立 common、backend 生产、runtime 生产、runtime 测试、runtime 压测五层单向 DAG。backend/runtime 只引用 common，test 只引用 runtime，benchmark 只引用 test；所有显式包使用精确 `==` pin，include 只允许已登记根文件且无循环。common 统一原两套清单重复的 HTTP/日志基础并把 anyio 固定为 `4.14.2`；backend 只保留 Django/IAM 增量，runtime 只保留 `websockets==16.0` 与带 `platform_system != "Windows"` marker 的 `uvloop==0.22.1`。
- 测试与压测边界：runtime test 层新增 `redis==8.0.1`、`valkey==6.1.1`，仅作为真实依赖测试 client，不宣称 P08 StateStore 生产驱动；benchmark 层新增 `pyperf==2.10.0`、`psutil==7.2.2`。候选 Locust 在隔离验收中因 gevent 线程补丁产生解释器退出异常并会污染 asyncio/uvloop 对照，未进入最终清单。aioquic、pylsqpack、qh3 等 QUIC/WebTransport 实验包全部继续留给 P21，backend/runtime 生产和普通测试均不隐式安装。
- 冷导入兼容修复：驱动安装后发现 portalocker 会在 Redis 可用时主动导入其 RedisLock，而既有模块级 cache 多进程 logger 会在 `ns_common` 导入期间提前加载 concurrent-log-handler/portalocker。`NsLogger` 现仅在实际请求 multiprocessing handler 时动态构造并缓存 concurrent handler 类；cache soft-failure logger 也延迟到首次真实失败。已安装 Redis/Valkey 的环境冷导入 `ns_common.testing` 时，`concurrent_log_handler`、`portalocker`、`redis`、`valkey`、`ns_runtime` 均不进入 `sys.modules`；实际多进程 logger 仍能加载 concurrent handler。LOG-1 输出、rotation、sanitizer 与 cache soft-failure 行为未改变。
- 自动化测试结果：依赖清单结构/精确 pin/include DAG/层级严格超集/uvloop marker/生产隔离/QUIC 延后门禁 `Ran 7, OK`；安装 test 清单的持久 runtime 环境执行 dependency/testing/observability/security/logger/http_client/exceptions/async_runtime/config/config_package/retry/time/identifiers 联合回归 `Ran 241, OK (skipped=1)`；backend 环境根目录全量 `Ran 252, OK (skipped=1)`。两个跳过均为 WSL 下同一 Windows 专用 event-loop 用例，backend 全量包含 cache 11 项回归和新增 lazy logger 门禁。
- 全新环境安装验收：在 `/home/ns/.virtualenvs` 下使用四类临时隔离目录分别从 runtime 生产、backend 生产、runtime test、runtime benchmark 清单安装；所有 resolver 与 `pip check` 通过，结束后移入系统回收站。runtime 生产环境可导入 `ns_common/httpx/uvloop/websockets` 且不存在 Django、Redis、Valkey、测试、压测或 QUIC 包；backend 生产环境可导入 Django/DRF/ADRF/JoseRFC/ns_common 且不存在 runtime、测试、压测或 QUIC 包；benchmark 环境可导入 pyperf/psutil 且不存在 Locust/gevent/QUIC。最终干净生产环境回归数量与持久环境一致。
- 真实驱动与 namespace 验收：test 清单的 Redis 与 Valkey 同步、异步 client 共同连接本机临时 Redis standalone；通过 `NsTestResourceFactory` 的唯一 namespace 分别验证 sync `manage()` 和 async `amanage()` 只删除所有者前缀，另一驱动写入的独立 namespace 保持完整。服务关闭前显式关闭四个 client，终止进程并回收临时目录；未调用 `KEYS`、`FLUSHDB` 或 `FLUSHALL`，未触碰共享实例或仓库真实数据目录。
- 静态与环境检查：全树 `compileall`、runtime/backend `pip check`、依赖清单 dry-run resolver、冷启动导入、禁止生产源码测试文件、仓库虚拟环境、临时 W17 环境、Redis 进程与临时测试目录残留、`git diff --check` 均通过。依赖门禁只解析仓库根清单，不执行任意 requirement option、VCS URL、editable 或本地路径；测试未访问 backend 或外部业务网络，只有 pip 包索引解析和 loopback Redis 验收使用外部/本地依赖。
- 安全/隔离检查：backend 清单无法通过 include 获得 runtime/uvloop/websockets、Redis/Valkey、pyperf/psutil 或 QUIC 包；runtime 生产无法获得 Redis/Valkey 和压测包；普通 test 无压测包。测试驱动安装不改变 `ns_common.testing` 的 driver-neutral client 注入与调用方生命周期所有权，不把普通 cache、Redis standalone 或 namespace cleanup 解释为强一致状态存储。依赖安装只发生在 `/home/ns/.virtualenvs`，仓库内未创建 venv；临时环境以可恢复回收站方式清理。
- 已知限制：本次真实安装与回归运行在 WSL2/Python 3.10.12，Windows 只通过精确 marker 门禁确认 uvloop 被排除，未在 Windows 新环境重复安装。依赖文件是当前精确顶层/公共解析基线，不替代未来发布制品的跨平台 lock/hash/SBOM。P08 才能把已选 Redis/Valkey 驱动纳入生产 StateStore 并验证 Sentinel/Cluster/TLS/Lua/CAS/lease/fencing；P21 才能引入 QUIC/WebTransport adapter 依赖；P22 才建立正式负载模型、报告和性能阈值。
- 下一工作包：`P02-W01 建立 src/ns_runtime 独立组件和唯一进程入口 main.py`，状态为 `NOT_STARTED`；唯一执行游标已推进到 P02-W01，P01 阶段标记为 `VERIFIED`。

## P01-FIX-09

- 工作包：`P01-FIX-09 修复测试资源 Factory 的可重试关闭和并发关闭语义`。
- 状态：`VERIFIED`。
- 本轮继续校准开始时间：`2026-07-17T21:28:56+08:00`。
- 本轮继续校准完成时间：`2026-07-17T21:44:08+08:00`。
- 修改文件：本轮更新 `src/ns_common/testing.py`、`tests/test_testing.py`、实施计划、acceptance log 和 [ADR-019](ns_runtime_architecture_decisions_0.0.2.md#adr-019)。P01-FIX-09 累计的上一轮变更还包括 `src/ns_common/__init__.py` 公共导出，以及把 7 项 W17 清单门禁模块原样校准为 `tests/test_requirements.py`；本轮没有再次修改这些文件，断言内容与五份 requirements 清单均未改变。设计边界文档未修改，`src/ns_runtime` 未创建，P02-W01 未开始。会话开始实时记录 `pwd=/mnt/s/PythonProject/ns/ns_evermore`、干净的 `main...origin/main` 和空子模块输出；全过程只读取当前本地工作区，不读取远程仓库、提交历史、PR、Issue、远程分支或提交消息，不切换、重置、清理或覆盖工作区。
- 原缺陷：旧 `NsTestResourceFactory.close()` 在任何实际清理前设置 `_closed=True` 并整体清空 `_ports`。任一 reservation 或临时目录清理失败后，Factory 已被误标为关闭且失败资源所有权丢失，第二次 close 无法重试；并发调用者也会因 `_closed` 提前成功返回，无法把 close 返回解释为真实回收完成。
- 本轮继续校准原因：上一版 Factory 状态机与 Factory close 屏障已经建立，但后续静态复核发现 `NsReservedPort.release()` 仍在实际 `socket.close()` 前将 `_socket` 设为 `None`。底层关闭失败或并发直接释放时，reservation 会提前表现为已释放，Factory 因而无法证明真实 socket 已完成回收；在本轮真实 socket 失败、重试和并发专项以及全部回归通过前，不再保留“端口所有权已经完整解决”的过强结论。
- Factory 状态机与门禁：新增稳定 `NsTestResourceFactoryState(str, Enum)` 及 plain alias，状态只允许 `OPEN -> CLOSING -> CLOSED`；新增线程安全只读 `state`、`is_closing`，并把 `is_closed` 严格冻结为 `state is CLOSED`。首次 close 在锁内进入 `CLOSING`；`directories`、`create_temporary_config()`、`create_controlled_clock()`、`create_in_memory_sinks()`、`reserve_tcp_port()`、`create_redis_namespace()`、`manage_redis_namespace()`、`amanage_redis_namespace()` 从调用入口即拒绝，稳定 details 只有对应 operation 和 state。失败后不回退 OPEN；只有端口与临时目录所有权全部完成转移才进入 CLOSED。
- 关闭屏障与返回保证：Factory 使用现有 `RLock` 配合 `Condition` 和单一 active-attempt 标记，同一时刻只有一个线程执行实际回收。其他 close 调用等待当前尝试结束；成功时全部观察 CLOSED，普通失败时失败执行者收到稳定异常且一个等待者串行接手下一次重试。成功 close 正常返回时 `_ports` 为空、临时目录 cleanup 已成功、Factory 不再持有待清理资源；CLOSED 后重复 close 幂等。并发成功与先失败后接管两种多线程场景均使用 event、明确 5 秒等待上限和线程 join timeout 验证，无提前返回、重复 release、并行 cleanup 或死锁。
- 资源所有权与重试：Factory 每次尝试对当前仍持有的 reservation 按逆创建顺序逐个 release，只有该调用正常返回后才按对象身份从 `_ports` 精确移除；普通失败项保留，其他端口和临时目录仍继续尝试，后续 close 只重试剩余项，已成功端口不重复处理。进一步校准后，`NsReservedPort.release()` 在自身 `RLock` 内执行真实 `socket.close()`，仅在底层调用正常返回后才把 `_socket` 置为 `None`；普通异常或进程级异常时保留同一 socket，`is_released` 仍为 false，下一次调用真正重试。`release() -> False` 只表示进入调用前已经真实释放，因此 Factory 在该正常返回后才能安全移除已由调用方直接释放的 reservation。`TemporaryDirectory` 独立 released 标记仍只在 `cleanup()` 正常返回后置位，失败时对象引用与所有权保留，成功后不重复 cleanup。
- reservation 并发屏障：直接 `release()` 与 Factory `close()` 竞争同一 reservation 时都必须取得 reservation 自身的锁，该锁覆盖完整底层 close。直接释放仍阻塞时，Factory 保持 `CLOSING` 并继续持有 reservation；直接释放成功后 Factory 才观察到 `False` 并移除，直接释放失败后 Factory 获锁并对同一 socket 执行第二次真实 close。多线程直接 release 的底层最大并发数为 1；首次成功时等待者返回 `False`，首次失败时一个等待者可接手重试，不存在两个并行底层 close。
- 异常与 context manager：普通资源异常不直接重抛、不复制 `str(error)` 或异常对象，聚合 `NsStateError` details 只含 `operation=close_test_resources`、`state=closing`、稳定 `failed_resource_types`/数量、剩余端口数、目录 pending 标记，以及 `resource_type/error_type`；直接 close 的底层普通异常不保留 cause/context。`KeyboardInterrupt`、`SystemExit` 原对象穿透；穿透前已成功端口已移出所有权，未执行/失败资源继续保留，状态保持 CLOSING，替换为正常行为后可重试到 CLOSED。`__exit__()` 继续调用 close：主体正常而清理失败返回稳定清理错误；主体失败而清理成功保留主体错误；二者同时失败时稳定清理错误为当前异常，主体错误保留在 Python `__context__`，底层清理文本不进入公开异常。
- 敏感信息边界：专项同时构造端口与目录失败，并检查 `str(error)`、`error.details`、`error.to_dict()`；均不含临时根目录、临时配置路径、host、port、Redis namespace UUID 或 mock 底层秘密文本。创建门禁也不复制路径、端口、URL、namespace 或底层异常。
- sink 同类风险复核：`NsInMemorySinkBundle.aclose()` 仍通过嵌套 `finally` 按 diagnostics、traces、metrics 顺序关闭，当前三个 `_InMemorySink.aclose()` 只在锁内幂等设置 CLOSED，不存在普通异常或资源所有权集合，`clear()` 只在三者关闭后执行；新增重复 aclose 回归后保持原实现，不扩大 FIX 范围。
- 公共导出：`ns_common.testing` 从 14 项增至 16 项，`ns_common` facade 从 204 项增至 206 项；新增 `NsTestResourceFactoryState` 与 `TestResourceFactoryState`。testing/top-level facade 均无重复，子 facade、顶层 facade、plain alias 与 `Ns*` 类型对象身份一致；独立解释器冷导入仍不加载 `redis`、`valkey`、`concurrent_log_handler`、`portalocker` 或 `ns_runtime`。
- W16 专项与原功能回归：runtime 环境 `tests.test_testing` 为 `Ran 35, OK`。新增真实继承 `socket.socket`、真实绑定并监听 `127.0.0.1:0` 的 `_FlakyCloseSocket` 和 `_BlockingCloseSocket`，直接进入 `NsReservedPort.release() -> socket.close()`，覆盖底层首次 OSError 后仍可取得同一 socket/有效 fileno、第二次真实重试、成功后第三次返回 false、并发直接 release 串行化、直接 release 与 Factory close 的成功/失败交接，以及底层 KeyboardInterrupt/SystemExit 后 Factory 重试。底层 close 调用次数、成功次数和最大并发数均被断言；现有状态机、端口/目录重试、敏感信息、Factory 并发 close、CLOSING 全入口门禁、context manager、目录/配置/clock/sink/Redis namespace/SCAN + bounded DELETE/前缀逃逸/同步异步 cleanup/真实 Redis standalone/facade/冷启动回归均保留。
- W17 回归与依赖边界：`tests.test_requirements` 为 `Ran 7, OK`，五层 include 图仍为 common -> backend/runtime、runtime -> test -> benchmark 的单向无环结构；精确 `==` pin、uvloop 非 Windows marker、Redis/Valkey 仅测试层、pyperf/psutil 仅 benchmark 层、backend 不引入 runtime/test/benchmark、QUIC/WebTransport 延迟到 P21 全部保持。`git diff --exit-code` 确认五份清单字节内容未修改，因此未重复四类仓库外全新环境安装；两套持久隔离环境 `pip check` 均通过，W17 既有全新环境证据不被本 FIX 替代或扩大。
- 联合与全量结果：用户指定的 testing/requirements/observability/time/config/config_package/async_runtime/http_client/exceptions/logger/security/retry/identifiers P01/runtime 联合为 `Ran 256, OK (skipped=1)`；backend 环境根目录全量为 `Ran 267, OK (skipped=1)`。两项跳过均是 WSL 下同一真实 Windows event-loop policy 用例，backend 全量继续包含 cache 11 项回归。
- 静态与环境检查：全树 `compileall`、runtime/backend `pip check`、testing 16 项与 `ns_common` 206 项 facade/身份、独立解释器冷启动、requirements 五层 include 图、生产源码测试文件、仓库虚拟环境、`src/ns_runtime` 不存在、临时 `ns-test-*` 和测试 Redis 进程残留、`git diff --check` 均通过。冷启动未加载 `redis`、`valkey`、`concurrent_log_handler`、`portalocker` 或 `ns_runtime`；专项真实 Redis 使用独立随机端口且已终止，未访问或清理系统服务。
- 已知限制：Factory 仍不拥有 Redis/Valkey client 或外部服务进程，调用方必须在 Factory 关闭前停止 namespace 写入者并自行关闭 client/process；真实依赖回归仍只覆盖 standalone，不覆盖 Sentinel/Cluster/TLS/StateStore/Lua/CAS/lease/fencing。同步 close 屏障会等待当前清理调用返回，不提供超时中断底层阻塞 API；底层清理函数自身必须可终止。双异常沿用 Python 3.10 原生 context 语义，未为本 FIX 引入 ExceptionGroup 兼容层。
- 下一工作包：`P02-W01 建立 src/ns_runtime 独立组件和唯一进程入口 main.py`，状态保持 `NOT_STARTED`；P01-FIX-09、P01-W16、P01-W17 与 P01 恢复 `VERIFIED`，唯一执行游标指向 P02-W01，但本工作包未实施 P02。

## P02-W01

- 工作包：`P02-W01 建立 src/ns_runtime 独立组件和唯一进程入口 main.py`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T22:08:57+08:00`。
- 修改文件：新增 `src/ns_runtime/__init__.py`、`src/ns_runtime/main.py` 和 `tests/test_runtime_main.py`；更新实施计划与 acceptance log。未修改设计边界、architecture decisions、`ns_common`、backend、依赖清单或配置，未开始 P02-W02。
- 公共契约变化：新增 `RTE-1`。`src/ns_runtime` 成为独立组件边界，`python -m ns_runtime.main` 是唯一模块进程入口；package facade 保持无启动副作用，入口当前只建立进程边界并确定性返回状态 0。未新增 `__main__.py`、脚本旁路、listener、管理端口、Envelope 或全局可变 service。
- 测试结果：runtime 环境 `tests.test_runtime_main` 为 `Ran 3, OK`；加入该专项后的 P01/runtime 联合回归为 `Ran 259, OK (skipped=1)`；backend 环境根目录全量为 `Ran 270, OK (skipped=1)`。两项跳过均为 WSL 下同一 Windows 专用 event-loop policy 用例。入口在仓库根目录及 `/tmp` 外部工作目录下均通过模块方式以状态 0、空 stdout/stderr 退出；全树 `compileall` 与 runtime/backend 两套环境 `pip check` 通过。
- 安全/隔离检查：独立解释器验证 `import ns_runtime` 不启动服务、不安装或替换 event loop policy；生产 package 不导入配置、logger、HTTP、cache、Redis/Valkey、transport 或 backend，不读取环境变量、全局 `ns_config`、仓库真实目录和外部网络。`src/` 下无测试文件，仓库内无虚拟环境，唯一 `main()`/`__main__` guard 均位于 `src/ns_runtime/main.py`，`git diff --check` 通过。
- 已知限制：本工作包只交付组件与可执行模块边界，不代表 RuntimeService、生命周期状态、RuntimeContext、启动校验、信号关闭、event loop 选择/观测或任何 transport/协议能力可用；这些能力保持 F0，由 P02-W02 至 P02-W08 依序实现。
- 下一工作包：`P02-W02 建立 RuntimeService 生命周期：created、starting、running、stopping、stopped、failed`，状态为 `NOT_STARTED`；P02 阶段保持 `IN_PROGRESS`。

## P02-W02

- 工作包：`P02-W02 建立 RuntimeService 生命周期状态机`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-17T22:58:14+08:00`。
- 修改文件：新增 `src/ns_runtime/service.py` 和 `tests/test_runtime_service.py`；更新实施计划与 acceptance log。未修改 `src/ns_runtime/main.py`、package facade、设计边界、architecture decisions、`ns_common`、backend、配置或依赖清单，未开始 P02-W03。
- 公共契约变化：新增 `RSL-1`。`ns_runtime.service` 提供 `RuntimeServiceState` 六个稳定小写值 created/starting/running/stopping/stopped/failed，以及一次性 `RuntimeService.state/start()/stop()` 生命周期。正常路径为 created → starting → running → stopping → stopped；start/stop hook 的普通异常、取消或其他 `BaseException` 在原对象穿透前分别从 starting/stopping 进入 failed。P02-FIX-01 后最终语义校准为：stopped 禁止 restart，但 stop 幂等；failed 禁止 restart，但允许 stop 执行或重试清理。生命周期操作在 owner event loop 上通过实例级 async lock 串行化，loop owner 的首次原子绑定与失败后清理语义由 P02-FIX-01 补齐；跨 loop 和非法迁移统一返回 `NsStateError`，非法迁移固定使用 `NS_STATE_ERROR`、固定 message，以及仅含 component、operation、current_state、requested_state、allowed_target_states 的结构化 details。
- 测试结果：原 W02 验收时 runtime 环境 `tests.test_runtime_service` 为 `Ran 10, OK`，与 W01 入口联合专项为 `Ran 13, OK`；加入 P02-W01/W02 后的 P01/runtime 联合回归为 `Ran 269, OK (skipped=1)`；backend 环境根目录全量为 `Ran 280, OK (skipped=1)`。两项跳过均为 WSL 下同一 Windows 专用 event-loop policy 用例。原专项覆盖正常过渡态可见性、六值顺序、created stop/stopped start/failed start 非法、启动/停止原异常穿透、取消后 failed 和 lock 释放、并发 start 串行化、start 期间 stop 等待，以及顺序跨 event loop 拒绝；其中原先与 stopped stop、failed stop 冲突的断言已由 P02-FIX-01 新专项替换，旧数量只作为历史 W02 证据保留。
- 安全/隔离检查：RuntimeService 不保存 hook 异常对象或异常文本，稳定迁移错误只含固定机器值；模块没有全局 service、可变 registry、后台 task/thread、I/O、环境变量读取或 service locator，唯一模块级迁移表使用只读 mapping 与 tuple。实现不直接读取全局 `ns_config`、HTTP/cache client、logger/sink，不导入 backend、transport、Redis/Valkey 或 WebSocket，也不创建 listener、Envelope、DeliveryRecord 或管理旁路。W01 冷导入和模块启动专项保持通过；全树 `compileall`、两套环境 `pip check`、生产源码测试文件、仓库虚拟环境和 `git diff --check` 门禁通过。
- 已知限制：`main.py` 尚未构造或运行 RuntimeService；protected start/stop hook 当前为空，RuntimeContext 和实际资源所有权由 P02-W03 引入。启动校验、角色状态、信号驱动的进程级资源关闭编排、后台任务失败联动、event loop 指标和本地诊断分别留给 P02-W04 至 W08；RuntimeService 自身的 stop 幂等与失败后重试语义已由 P02-FIX-01 冻结，不能推迟或留给 W06 推翻。本工作包不把 transport、cluster 或 delivery 标记为可用。
- 下一工作包：`P02-W03 建立显式 RuntimeContext，持有配置快照、clock、logger、metrics、trace、task supervisor 和后续依赖占位`，状态为 `NOT_STARTED`；P02 阶段保持 `IN_PROGRESS`。

## P02-FIX-01

- 工作包：`P02-FIX-01 修复 RuntimeService 关闭幂等、失败后清理与首次 event-loop 绑定竞态`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-18T00:03:05+08:00`。
- 原缺陷：W02 的迁移表让 `STOPPED` 和 `FAILED` 都没有出边，导致重复 stop 抛错、start 部分成功后失败无法清理、stop 普通失败或取消后无法重试；`_loop is None` 的首次绑定也没有线程同步，两个线程中的独立 event loop 可能同时越过检查并把底层 asyncio lock 暴露给跨 loop 竞态。
- 修改文件：更新 `src/ns_runtime/service.py`、`tests/test_runtime_service.py`、实施计划、acceptance log，并新增 [ADR-021](ns_runtime_architecture_decisions_0.0.2.md#adr-021)。`src/ns_runtime/main.py`、`src/ns_runtime/__init__.py`、五份 requirements、`ns_common` 公共契约和设计边界文档均未修改；未创建 RuntimeContext，未开始 P02-W03。
- `RSL-1` 校准：六个公开状态值和顺序不变，RuntimeService 继续是一次性启动且不支持 restart。start 只允许 `CREATED -> STARTING -> RUNNING/FAILED`；`RUNNING`、`STOPPING`、`STOPPED`、`FAILED` 均拒绝再次 start。`STOPPED` 后同 owner loop 的 stop 幂等返回且不重复 hook；`FAILED` 不表示资源已清理，允许 `FAILED -> STOPPING -> STOPPED/FAILED`，因此 start 失败或取消后的部分资源可由显式 stop 回收，stop 失败或取消后也能继续重试。只有 stop hook 成功完成后才进入 `STOPPED`。
- 关闭并发：owner loop 内继续由实例级 asyncio lock 覆盖完整 hook。四个并发 stop 的首个成功尝试只执行一次 hook，其余等待者在 `STOPPED` 下返回；首个尝试失败时原执行者收到原异常，一个等待者从 `FAILED` 接管第二次清理，成功后其余等待者返回。专项确认 hook 最大并发为 1、首次成功总调用 1 次、首次失败后成功总调用 2 次，无并行清理或死锁；重试再次失败时状态仍回到 `FAILED`，后续 stop 仍可继续接管。
- start/stop 协作：并发 start 仍只执行一次 start hook；首个 start 失败后第二个 start 观察 `FAILED` 并得到稳定非法迁移错误。start 执行期间的 stop 等待 lifecycle lock；start 成功后从 `RUNNING` 清理，start 失败后从 `FAILED` 清理，start 与 stop hook 不并行。start hook 获取部分资源后普通失败和取消两类路径均验证可显式 stop 到 `STOPPED`。
- event-loop 原子绑定：新增实例级 `threading.Lock`，只在同步临界区内比较和设置 owner loop；锁内没有 await、hook 或 asyncio lock。`start()`/`stop()` 继续先绑定或校验 owner，再尝试 lifecycle lock。真实两个线程、两个不同 event loop 使用 barrier 同时首次 start，结果严格为一个成功绑定并执行一次 hook，另一个在 lifecycle lock 前收到固定 `NsStateError`；线程均在 timeout 内退出，未出现 `RuntimeError`、lock bound/future attached 等原生 asyncio 错误。该竞态专项额外连续重复 20 次通过。
- 异常与安全：start/stop hook 的普通异常、`asyncio.CancelledError`、`KeyboardInterrupt` 和 `SystemExit` 都在状态先进入 `FAILED` 后保持原类型与原对象穿透；后续 stop 可清理或重试。RuntimeService 不保存 hook 异常对象或文本，也不复制到底层 cause、非法迁移 details 或跨 loop details；含秘密文本的 hook 失败后，后续 `NsStateError` 的字符串、details 和 `to_dict()` 均无该文本。跨 loop details 继续只含 component、operation、current_state 和 `event_loop_mismatch`。
- 测试结果：runtime 环境 `tests.test_runtime_service` 为 `Ran 21, OK`；与 W01 入口联合为 `Ran 24, OK`。用户指定的 testing/requirements/observability/time/config/config_package/async_runtime/http_client/exceptions/logger/security/retry/identifiers 加 P02-W01/W02/FIX-01 联合回归为 `Ran 280, OK (skipped=1)`；backend 环境根目录全量为 `Ran 291, OK (skipped=1)`。两项跳过均是 WSL 下同一 Windows 专用 event-loop policy 用例。
- 静态与隔离检查：全树 `compileall`、runtime/backend 两套 `pip check`、`ns_runtime` 冷导入、无 import-time task/thread、根目录和 `/tmp` 外部工作目录模块启动、跨 loop 稳定错误、生产源码测试文件、仓库虚拟环境、禁止范围源码扫描、临时 Redis/测试线程残留、requirements/入口/设计文档未改和 `git diff --check` 门禁通过。模块入口仍为空 stdout/stderr 并返回 0；没有新增 transport、Envelope、StateStore、配置、信号、角色、观测采集或外部依赖。
- 已知限制：本 FIX 只校准 RuntimeService 的生命周期与 loop owner；没有实现实际资源所有权、关闭顺序、shutdown timeout、后台任务失败联动或进程信号。上述编排仍属于 P02-W03 至 W07，但必须建立在本 FIX 的 stop 幂等、FAILED 可清理/重试和原异常穿透契约之上。
- 下一工作包：`P02-W03 建立显式 RuntimeContext`，状态保持 `NOT_STARTED`；P02 阶段保持 `IN_PROGRESS`。

## P02-W03

- 工作包：`P02-W03 建立显式 RuntimeContext`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T09:07:26+08:00`。
- 修改文件：新增 `src/ns_runtime/context.py` 和 `tests/test_runtime_context.py`，更新 `src/ns_runtime/service.py`、`tests/test_runtime_service.py`、实施计划、acceptance log，并新增 [ADR-022](ns_runtime_architecture_decisions_0.0.2.md#adr-022)。`src/ns_runtime/main.py`、`src/ns_runtime/__init__.py`、设计边界文档、`ns_common`、backend、配置示例和五份 requirements 均未修改；未开始 P02-W04。
- `RTC-1` 公共契约：新增冻结、slots、仅关键字构造的 `RuntimeContext`。`config`、`clock`、`logger`、`metrics`、`traces`、`task_supervisor` 六项必须显式注入并分别满足 `NsConfig`、`Clock`、`logging.Logger`、`MetricsSink`、`TraceSink`、`TaskSupervisor`；context 保留精确对象身份，`config_snapshot`、`metrics_sink`、`trace_sink` 为只读身份别名。字段冻结只禁止替换接线引用，不伪装依赖内部状态为不可变。
- 后续依赖槽位：新增冻结 `RuntimeDependencySlots`，当前只为既有 `DiagnosticSnapshotSink` 和 `NsHttpClientOwner` 提供可选类型化槽位，默认明确为 `None`；RuntimeContext 提供只读对应属性。槽位没有 mapping、字符串 key、`get/register/resolve` 或任意 object bag，尚未冻结的 transport、StateStore、processor、session 等依赖没有提前占位或实现。
- RuntimeService 接入：构造函数改为必须通过关键字接收有效 `RuntimeContext`，`service.context` 始终返回同一对象且无 public setter；无参或错误类型不再产生隐式默认依赖。created/starting/running/stopping/stopped/failed 六态、start/stop 矩阵、loop owner、并发和失败清理语义均未改变。构造 context/service 不调用依赖方法，protected hooks 仍为空；本包没有创建 task/client/listener/exporter，没有 flush/aclose sink/owner，也没有修改 main 运行 service。
- 验证与安全错误：所有 core/optional 字段均在构造时检查公共类型，错误使用固定 `NS_VALIDATION_ERROR` 和固定 message；details 仅含 component、dependency、expected_type、actual_type，不复制对象值、repr、配置、URL、路径或底层文本。含秘密 `__str__`/`__repr__` 的错误依赖专项确认 `str(error)`、details 和 `to_dict()` 均无秘密文本。
- 测试结果：runtime 环境 `tests.test_runtime_context` 为 `Ran 8, OK`；W03 context、W02/FIX 生命周期和 W01 入口联合为 `Ran 32, OK`。testing/requirements/observability/time/config/config_package/async_runtime/http_client/exceptions/logger/security/retry/identifiers 加 P02-W01/W02/FIX-01/W03 的 P01/runtime 联合回归为 `Ran 288, OK (skipped=1)`；backend 环境根目录全量为 `Ran 299, OK (skipped=1)`。两项跳过均为 WSL 下同一 Windows 专用 event-loop policy 用例。
- 静态与隔离检查：原 W03 验收时全树 `compileall`、runtime/backend 两套 `pip check`、package/context 独立解释器导入、无 event loop policy/thread 变化、无模块级 RuntimeContext 或 ambient locator、根目录和 `/tmp` 外部工作目录模块入口、生产源码测试文件、仓库虚拟环境、禁止 transport/Envelope/StateStore/signal/task 创建源码扫描、requirements/入口/package facade/设计边界未改和 `git diff --check` 均通过。入口继续状态 0、空 stdout/stderr；五份 requirements 内容未改变且没有新增依赖。该次 context 导入检查没有隔离并观测 `ns_common.config.model -> ns_config = NsConfig.load()` 的配置与文件系统链，相关过强结论由 P02-FIX-02 校准。
- 已知限制：本包只建立显式依赖接线，不加载或校验启动环境，不构造 composition root，不创建或关闭 HTTP client/sink/TaskSupervisor，不实现 shutdown timeout、信号、角色、event-loop 指标、本地诊断、transport、Envelope 或 StateStore。可选槽位表示未来接线位置，不表示资源已经创建、可用或由 context 自动拥有；实际启动校验与资源关闭必须继续遵守 `RTC-1`、`RSL-1`、`HTTP-1` 和 `OBS-1`。
- 下一工作包：`P02-W04 启动时执行环境、依赖、目录、event loop、transport 配置、state store 生产限制和 TLS 前置校验`，状态为 `NOT_STARTED`；P02 阶段保持 `IN_PROGRESS`，本工作包未实施 W04。

## P02-FIX-02

- 工作包：`P02-FIX-02 修复 RuntimeContext 冷导入及构造期隐式全局配置副作用`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T13:49:45+08:00`。
- 原缺陷：W03 的 `ns_runtime.context` 顶层类型导入会加载 `ns_common` package，并经 `ns_common.config.model -> ns_config = NsConfig.load()` 执行默认路径解析、配置读取和 `ensure_runtime_dirs()`，HTTP owner 类型还会经 HTTP/logger/config 链带入同类隐式依赖。P02-FIX-02 第一轮移除顶层 import 后，`RuntimeContext.__post_init__()` 与非 `None` optional 槽位仍会在构造期重新 import 这些模块；因此非法 `config=object()` 或 `http_client_owner=object()` 仅为类型校验也可能初始化全局配置和文件系统资源。该剩余问题继续在同一 FIX 内修正，没有新增 FIX-03。
- 修改文件：新增仅依赖标准库的内部 `src/_ns_common_error_types.py`；更新 `src/ns_common/exceptions/base.py`、`src/ns_common/exceptions/common.py`、`src/ns_runtime/context.py`、`tests/test_runtime_context.py`、实施计划、acceptance log 和 [ADR-022](ns_runtime_architecture_decisions_0.0.2.md#adr-022)。`src/ns_runtime/main.py`、`src/ns_runtime/__init__.py`、backend、设计边界文档、配置和五份 requirements 均未修改；`ns_common.exceptions` 继续导出同一规范错误类，既有公开继承、构造、code、numeric code、message、details、序列化和注册表合同均未改变；没有实施 P02-W04。
- 导入与构造边界：`context.py` 继续以 postponed annotations 与 `TYPE_CHECKING` 保存 `NsConfig`、Clock、三个 sink、TaskSupervisor 和 `NsHttpClientOwner` 的具体类型合同，运行时不再 import 任何 `ns_common.*` 类型。有限内部验证函数仅从 `sys.modules` 中固定的规范定义模块取得真实类对象并执行 `isinstance`；合法对象的定义模块必然已经由调用方加载，缺失模块或非法对象直接返回稳定错误，不通过 import 补载。该实现不按类名字符串放行，不定位依赖实例、不暴露 registry/get/register/resolve API；同名伪造 `NsConfig` 与 `NsHttpClientOwner` 均被拒绝。
- 稳定错误边界：非法构造必须在 `ns_common` 尚未加载时也返回规范 `NsValidationError`。其既有 `NsEvermoreError` 基类与 `NsValidationError` 实现在标准库-only 内部引导模块中保持唯一类对象，原 `ns_common.exceptions.base/common` 只重导出该对象；公开 module metadata、继承、错误码、默认消息、details 与 `to_dict()` 均保持兼容，完整 exceptions 专项与 registry 门禁通过。
- 保持契约：`RuntimeContext` 与 `RuntimeDependencySlots` 继续 frozen、slots、kw-only，保留注入对象身份、只读别名、有限类型化槽位和稳定错误 details；`RuntimeService` 仍强制注入同一 context。合法 `NsConfig`、Clock、MetricsSink、TraceSink、TaskSupervisor、DiagnosticSnapshotSink 与 `NsHttpClientOwner` 均通过原 `isinstance` / runtime-checkable Protocol 语义并保持对象身份；W02/FIX-01 六态生命周期与 W01 入口行为不变，没有默认依赖、ambient getter、task/client/listener/exporter 或资源生命周期编排。
- 冷导入与构造期专项：三个独立解释器分别执行 context 冷导入、非法 `RuntimeContext(config=object(), ...)` 和非法 `RuntimeDependencySlots(http_client_owner=object())`。每个解释器使用独立临时工作目录，并在操作前监控内建 `open`、`Path.exists/mkdir/open`、环境读取、logger handler/registry、thread/task/event-loop 创建及直接相关模块。三条路径均未产生观测事件，临时目录保持为空，`ns_common`、config/model/paths、logger、http_client 均未加载；未调用 `ensure_runtime_dirs`、未加载全局 `ns_config`、未读取默认配置文件、未创建 data/etc/log、HTTP client、handler、task、thread 或 event loop。两个非法路径均返回固定 message/details 的规范 `NsValidationError`。
- 测试结果：runtime 环境 `tests.test_runtime_context` 为 `Ran 12, OK`；W03/FIX-02 context、W02/FIX-01 lifecycle 和 W01 入口联合为 `Ran 36, OK`；`tests.test_exceptions` 为 `Ran 26, OK`。testing/requirements/observability/time/config/config_package/async_runtime/http_client/exceptions/logger/security/retry/identifiers 加 P02 的 P01/runtime 联合回归为 `Ran 292, OK (skipped=1)`；backend 环境根目录全量为 `Ran 303, OK (skipped=1)`。两项跳过均为 WSL 下同一 Windows 专用 event-loop policy 用例。
- 静态与隔离检查：全树 `compileall`、runtime/backend 两套 `pip check`、冷导入加两个构造期副作用专项、exceptions facade/依赖无环/公开对象身份与注册表门禁、requirements/入口/package facade/设计边界未改、范围扫描和 `git diff --check` 均通过；五份 requirements 内容未改变且没有新增外部依赖。
- 已知限制：本 FIX 只修复 RuntimeContext 的模块导入与构造期类型验证边界。合法依赖仍由 composition root 在构造前显式创建并加载其公共类型；context 不负责导入、创建、启动或关闭依赖。本包不加载启动配置、不建立 composition root，也不实现 W04 的启动前校验及任何 transport、Envelope、StateStore、角色、信号、event-loop lag 或本地诊断能力。
- 下一工作包：`P02-W04 启动时执行环境、依赖、目录、event loop、transport 配置、state store 生产限制和 TLS 前置校验`，状态保持 `NOT_STARTED`；P02 阶段保持 `IN_PROGRESS`，本 FIX 未实施 W04。

## P02-W04

- 工作包：`P02-W04 启动时执行环境、依赖、目录、event loop、transport 配置、state store 生产限制和 TLS 前置校验`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T15:05:49+08:00`。
- 修改文件：新增 `src/ns_runtime/startup.py` 与 `tests/test_runtime_startup.py`；更新 `src/ns_runtime/main.py`、`tests/test_runtime_main.py`、实施计划、acceptance log，并新增 [ADR-023](ns_runtime_architecture_decisions_0.0.2.md#adr-023)。`src/ns_runtime/context.py`、`src/ns_runtime/service.py`、`src/ns_runtime/__init__.py`、`ns_common`、backend、配置模型与示例、五份 requirements 和设计边界文档均未修改。
- `RSP-1` 公共契约：新增冻结、显式路径接线 `RuntimeStartupDirectories`，冻结安全结果 `RuntimeStartupPreflightResult`，以及同步 `RuntimeStartupPreflight.validate()/prepare()`。两条路径都严格解析 local/dev/test/prod，验证既有不可变配置与 startup security，阻断未实现 transport，检查固定 Python 依赖、本机服务端 TLS context 能力和显式目录；`validate()` 只选择、不替换 event-loop policy，`prepare()` 仅在此前检查全部成功后安装 policy。结果只包含环境、event-loop 选择、是否安装 policy、配置化 adapter、StateStore backend、固定依赖和目录角色，不包含 URL、真实路径、配置正文、credential、底层异常或资源对象。
- 启动安全与能力门禁：生产明文 transport、关闭强制 TLS、生产 SQLite 和非生产禁止明文分别归一为稳定 `RUNTIME_STARTUP_SECURITY_ERROR`；无效环境使用 `RUNTIME_CONFIG_INVALID`；缺失 `websockets` 或目录不可访问使用稳定 `NS_DEPENDENCY_ERROR`，不保留 probe/OS 异常文本或 cause。当前只准入 `websocket_tcp` 配置并检查其 runtime 生产依赖，HTTP/3/WebTransport/QUIC 误启用返回 `RUNTIME_TRANSPORT_DISABLED`。Redis/Valkey 生产配置正向通过，SQLite 只允许非生产并准备显式 parent；本包不检查测试层 Redis/Valkey driver、不连接 store。TLS 只验证服务端 `SSLContext` 能力，未验证证书、私钥、CA、版本、cipher 或 reload。
- 入口 composition root：`main.py` 通过函数内延迟 import 保持 `import ns_runtime` 与 `import ns_runtime.main` 不加载 `ns_common`、context/service/startup、uvloop 或 websockets，也不替换 policy。实际 `main()` 加载启动配置，创建显式 config/clock/logger/in-memory metrics/trace/TaskSupervisor context，执行 preflight，再以选定 policy 运行一次无监听 RuntimeService start/stop。runtime 环境依赖齐全时模块入口状态 0 且 stdout/stderr 为空；backend 环境按 `DEP-1` 不安装 `websockets`，同一入口稳定 fail-closed，测试不通过混装 runtime 包伪造成功。
- 测试结果：runtime 环境 `tests.test_runtime_startup` 为 `Ran 14, OK`；W01 main、W02/FIX-01 service、W03/FIX-02 context 与 W04 startup 联合为 `Ran 51, OK`。testing/requirements/observability/time/config/config_package/async_runtime/http_client/exceptions/logger/security/retry/identifiers 加 P02 的 runtime 联合回归为 `Ran 307, OK (skipped=1)`；backend 环境根目录全量为 `Ran 318, OK (skipped=1)`。两项唯一跳过均为 WSL 下同一 Windows 专用 event-loop policy 用例。runtime 环境真实 `python -m ns_runtime.main` 成功，Linux auto 选择并安装 uvloop，随后新 loop 为真实 `uvloop.Loop`；backend 环境入口负向分支稳定返回缺失 `websockets`。
- 静态与隔离检查：全树 `compileall`、runtime/backend 两套 `pip check`、示例 JSON、入口/package/context 冷导入、生产源码测试文件、仓库虚拟环境、五份 requirements 内容、配置/设计文档范围和 `git diff --check` 门禁通过。preflight 负向专项确认环境、配置、安全、feature gate、依赖、TLS 与目录失败均不安装 policy；probe 异常与真实目录不进入错误字符串、details、字典或 cause。新增生产代码没有 socket/listen/server、transport session、Envelope、StateStore、Redis/Valkey、HTTP client、exporter、signal、task/thread 或角色实现；测试只使用显式临时目录和注入 probe，完整回归中的既有端口工厂在获准的本地 loopback 权限下执行。
- 已知限制：`websocket_tcp` 当前只是可接纳配置基线，不是已实现 adapter；P04 前无 listener、收发或 conformance。StateStore 仍为 F0，生产 Redis/Valkey 配置通过不代表 driver、连接、CAS/lease/fencing 或强一致能力可用；P08 冻结生产合同后再增加实际依赖与连通性检查。完整 TLS 材料与策略归 P20。main 当前只运行一次无监听自检生命周期后退出；角色状态、信号等待、资源关闭顺序、后台任务失败联动、event-loop lag/implementation snapshot 和本地诊断分别留给 P02-W05 至 W08。
- 下一工作包：`P02-W05 初始角色状态支持 singleton、sub_node、standby_master、active_master 配置值；实际协调能力保持 feature disabled`，状态为 `NOT_STARTED`；P02 阶段保持 `IN_PROGRESS`。

## P02-FIX-03

- 工作包：`P02-FIX-03 修复真实 main() 配置加载及冷进程 bootstrap import 绕过 RSP-1 的错误归一化与目录副作用`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T17:59:01+08:00`。
- 原缺陷：真实 `main()` 的无路径 `NsConfig.load()` 已在本 FIX 第一轮改为显式路径，但全新解释器首次调用仍会因 `ns_common` package 初始化导入 cache/logger/config facade，再从 model 级 `ns_config = NsConfig.load()` 进入 `ensure_runtime_dirs()`；原 main 测试父进程预先导入 `ns_common`，无法观测这条真实 bootstrap 链。结果是 dependency/TLS/transport/security 失败前仍可能创建仓库 data/etc/log/tmp。
- 修改文件：新增内部 `src/ns_runtime/_bootstrap.py` 与标准库-only `tests/test_runtime_bootstrap.py`；更新 `src/ns_common/__init__.py`、`src/ns_common/config/__init__.py`、`src/ns_common/config/model.py`、cache clients/Django adapter、logger、runtime main/startup、`tests/test_config_package.py`、`tests/test_runtime_main.py`、实施计划、acceptance log 和 [ADR-023](ns_runtime_architecture_decisions_0.0.2.md#adr-023)。没有修改 `NsConfig` 类型定义、配置字段/默认值/校验/错误/序列化、`NsConfig.load()` 无参目录语义、paths、配置示例、五份 requirements、RuntimeContext、RuntimeService、backend 或设计边界文档；没有新增 FIX-04，也没有开始 P02-W05/W06。
- bootstrap 与 CFG-1 兼容：`ns_runtime._bootstrap` 只从权威模块重导出默认配置路径、同一 `NsConfig`、startup 错误类和路径常量，不使用 `spec_from_file_location`、模块别名、重复加载、代理或复制类。model、config facade 与顶层 facade 通过线程安全模块属性，仅在显式请求 `ns_config` 时执行一次原 `NsConfig.load()` 并缓存同一真实实例；cache/logger/Django cache 将该请求延迟到实际使用点。`__all__`、跨 facade 身份与普通 backend import 保持；兼容专项还确认显式无参 `NsConfig.load()` 继续独立调用 `ensure_runtime_dirs()`。配置加载与 preflight 继续共用唯一 `_raise_normalized_startup_config_error()`。
- 独立解释器专项：新增测试模块的父进程只导入标准库；每个场景复制 `src` 到独立临时项目并启动全新 Python，先安装 profile、mkdir、文件写入、event-loop policy 和 dependency probe，再 `import ns_runtime.main` 并调用真实 `main(config_path=..., startup_root=...)`。缺失 `websockets` 稳定返回 `NS_DEPENDENCY_ERROR`，prod 明文稳定返回 `RUNTIME_STARTUP_SECURITY_ERROR`。两条路径都确认 global `ns_config` 未出现在 model/config/top facade、`ensure_runtime_dirs` 零调用、临时仓库 data/etc/log/tmp 与显式 startup root 均不存在、无目录/文件写入、policy 未替换且 `ns_runtime.service` 未加载；bootstrap 的配置/错误类型与公开 facade 身份完全相同。
- 测试结果：runtime 环境 `tests.test_runtime_main tests.test_runtime_startup tests.test_runtime_bootstrap` 为 `Ran 27, OK`；W01 main、W02/FIX-01 service、W03/FIX-02 context 与 W04/FIX-03 startup/bootstrap 联合为 `Ran 60, OK`；config facade/cache/logger/testing 兼容为 `Ran 67, OK`。P01/runtime + P02 非 Django cache 联合回归为 `Ran 317, OK (skipped=1)`；backend 环境根目录全量为 `Ran 328, OK (skipped=1)`。唯一跳过为 WSL 下 Windows 专用 event-loop policy 用例。
- 静态与隔离检查：全树 `compileall`、runtime/backend 两套 `pip check` 和 `git diff --check` 通过。源码未新增 listener/socket/server、transport session、StateStore/Redis/Valkey client、HTTP client/exporter、signal、后台 task/thread 或角色状态；独立测试只操作临时复制和临时路径，不删除或创建仓库真实运行目录。
- 已知限制：composition root 仍注入普通 `logging.Logger`。本 FIX 不扩大为 LOG-1 重构，但 W05 开始实际使用 runtime logger 前必须完成生产安全日志接线。main 仍只运行一次无监听自检生命周期；角色状态、信号关闭、loop lag 与本地诊断仍分别属于 W05 至 W08。
- 下一工作包：`P02-W05 初始角色状态支持 singleton、sub_node、standby_master、active_master 配置值；实际协调能力保持 feature disabled`，状态保持 `NOT_STARTED`；`P02-W04` 与 `P02-FIX-03` 均为 `VERIFIED`，P02 阶段保持 `IN_PROGRESS`，当前执行游标为 `P02-W05`。

## P02-W05

- 工作包：`P02-W05 初始角色状态与未完成能力门禁`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T18:29:15+08:00`。
- 修改文件：新增 `src/ns_runtime/roles.py` 与 `tests/test_runtime_roles.py`；更新 `src/ns_runtime/service.py`、`src/ns_runtime/main.py`、`src/ns_common/logger.py`、exceptions common/facade/registry、`tests/test_runtime_main.py`、`tests/test_logger.py`、`tests/test_exceptions.py`、实施计划、acceptance log，并新增 [ADR-024](ns_runtime_architecture_decisions_0.0.2.md#adr-024)。设计边界文档、配置模型/示例、RuntimeContext、startup preflight、RuntimeService 既有测试、backend 和五份 requirements 未修改。
- `RRS-1` 契约：RuntimeService 构造时从冻结配置快照建立只读本地角色状态，`service.role` 返回冻结 `RuntimeRoleSnapshot`。singleton、sub_node、standby_master、active_master 四个配置值原样保留；transitioning/draining 作为未来角色过渡域登记，healthy/degraded/isolated/unavailable 作为独立健康域登记。本包不暴露角色或健康状态 mutation/transition API，不读取 active_master_url，不连接 master，也不执行选主、leader lease、fencing 或协调写入。
- 未完成能力门禁：新增固定 `RuntimeCapability` 三项 transport、cluster_coordination、delivery，当前全部为 false。`require_capability()` 对每项先写固定结构化审计字段 event/component/capability/role/error_code/reason，再抛新登记的 `RUNTIME_FEATURE_DISABLED`；日志失败也不能把禁用功能变为成功。新错误 numeric code 为 200165、category 为 runtime、audit_required 为 true、action 为 reject_disabled_feature；错误注册表追加为 73 项、19 域/66 个 `RUNTIME_*` code 和 20 个独立场景，既有错误类/code/numeric_code/继承/构造/details/序列化与 13 个 NACK 映射均未改变。
- LOG-1/RSP-1 接线：`NsLogger` 新增可选显式 `config` mapping 与 `log_dir`；提供时深拷贝显式日志配置并只写显式 root，不请求 global `ns_config`，未提供时保持原兼容行为。main 仍先用无 handler bootstrap logger 构造 preflight context；只有 preflight 全部成功并准备显式目录后，才用当前配置快照、runtime level、Sanitizer 和显式 log root 构造生产 NsLogger，再以同一 clock/sink/supervisor 创建最终 context。dependency/security/transport/TLS 失败前的 global config、目录、policy 和 service 零副作用边界保持。
- 测试结果：角色/门禁、service、main、logger、exceptions 专项 `Ran 77, OK`；runtime 环境排除按 DEP-1 不安装的 Django cache 用例后全量 `Ran 324, OK (skipped=1)`；backend 环境根目录全量 `Ran 335, OK (skipped=1)`，包含 cache 11 项。唯一跳过为 WSL 下 Windows 专用 event-loop policy。显式 logger 独立解释器确认 global `ns_config` 未初始化、日志只写临时显式 root、token/payload 原值零泄露；两套 `pip check`、全树 `compileall` 和 `git diff --check` 通过。
- 设计边界 review：实现只新增本地初始角色快照、统一禁用门禁和安全日志接线；源码扫描确认没有 listener/socket/server、transport adapter/session、Envelope、StateStore、Redis/Valkey client、DeliveryRecord、leader election/lease/fencing、角色 mutation、signal handler、后台 task/thread、HTTP client/exporter 或管理旁路。active_master 配置值仍不代表 active authority；standby/sub_node/singleton 也不宣称拓扑或消息能力可用。测试全部位于根 `tests/`，仓库内未创建虚拟环境，设计边界无修改。
- 已知限制：角色与健康状态当前只读且只表示进程启动快照；强一致角色切换、active 权威、审计持久化和恢复分别依赖后续 P17/P08 等阶段。能力门禁的日志审计在 P08 强一致审计路径前仍是 best-effort，但日志失败始终 fail-closed。main 仍只运行一次无监听生命周期，未等待信号，也未编排 sink/logger/supervisor/client 的关闭；这些属于 P02-W06。
- 下一工作包：`P02-W06 SIGINT/SIGTERM 优雅关闭顺序与资源清理编排`，状态为 `NOT_STARTED`；P02 阶段保持 `IN_PROGRESS`，当前执行游标已更新为 P02-W06。

## P02-W06

- 工作包：`P02-W06 SIGINT/SIGTERM 优雅关闭顺序与资源清理编排`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T18:43:02+08:00`。
- 修改文件：新增 `src/ns_runtime/shutdown.py` 与 `tests/test_runtime_shutdown.py`；更新 `src/ns_runtime/service.py`、`src/ns_runtime/main.py`、`src/ns_common/logger.py`、`tests/test_runtime_main.py`、`tests/test_logger.py`、实施计划、acceptance log，并新增 [ADR-025](ns_runtime_architecture_decisions_0.0.2.md#adr-025)。设计边界、配置模型/示例、RuntimeContext 字段、startup preflight、角色/能力门禁、backend、requirements 和既有 observability/TaskSupervisor 公共契约均未扩展。
- `RSD-1` 契约：新增进程私有 `RuntimeShutdownCoordinator`，首次 SIGINT、SIGTERM、service stop、外部请求或无监听自检原因胜出并立即关闭本地 admission gate。实际 shutdown 在实例锁内只执行一次，固定按停止新任务并取消后台任务、flush metrics/traces/可选 diagnostic、close sinks、close 显式 HTTP owner、写结构化摘要、close owned logger 的顺序执行；重复调用返回同一冻结 `RuntimeShutdownReport`。coordinator 与 service 必须持有同一 `RuntimeContext` 身份，避免关闭另一组依赖。
- 失败与安全语义：TaskSupervisor 超时保留冻结未完成任务报告；日志只输出任务数量和 16 字符 SHA-256 digest，不输出原任务名。普通 sink/client/logger/summary 异常只记录固定 phase、resource 和异常类型，绝不复制异常消息、资源 repr 或底层 cause，并继续尝试后续资源；进程级 `BaseException` 保持穿透并由 RuntimeService 进入 failed 后允许显式重试。`NsLogger.close()` 幂等 flush/close 自有 handlers 并清除初始化/进程所有权；全局 `close_ns_loggers()` 复用同一实例入口。
- 进程与信号路径：`RuntimeSignalRegistration` 为当前 event loop 安装 SIGINT/SIGTERM，平台不支持 loop signal handler 时回退到 `signal.signal` + `call_soon_threadsafe`，退出作用域时恢复。`main.py` 保持唯一入口、冷导入与 RSP-1 顺序；preflight 成功后的无 listener 自检通过 `SELF_CHECK_COMPLETE` 请求同一 coordinator 后退出，未来常驻 listener 不得另建第二套关闭路径。
- 测试结果：shutdown/service/main/context/bootstrap/logger 专项在边界修复后为 `Ran 66, OK`；runtime 环境排除按 DEP-1 不安装的 Django cache 用例后全量 `Ran 330, OK (skipped=1)`；backend 环境根目录全量 `Ran 341, OK (skipped=1)`，包含 cache 11 项。唯一跳过为 WSL 下 Windows 专用 event-loop policy。两套 `pip check`、全树 `compileall` 和 `git diff --check` 通过。
- 设计边界 review：首次审查发现 coordinator 可与 service 使用不同 context，已在提交前增加身份校验和负向测试。修复后源码扫描只命中明确的 no-listener/transport 禁止说明；没有新增 socket/listener/server、transport adapter/session、Envelope、StateStore、Redis/Valkey client、DeliveryRecord、leader/lease/fencing、角色迁移、HTTP 管理端口、后台常驻 task/thread 或管理旁路。测试全部位于根 `tests/`，仅使用内存依赖、临时目录与本进程信号，未访问真实远程服务或共享数据，设计边界文档未修改。
- 已知限制：本阶段的“停止接入”仅指关闭进程本地 admission gate，TaskSupervisor shutdown 同时拒绝新任务。P04 创建首个 listener 后必须通过冻结的类型化 admission/drain hook 扩展关闭序列，并独立实现连接 draining、通知重连和 transport close；P10/P18 前不存在 delivery 转移或 owner handoff。本阶段不建立 Envelope、管理通道、StateStore、角色迁移或 loop lag collector。
- 下一工作包：`P02-W07 建立 event loop lag 采样和 implementation 指标`，状态为 `IN_PROGRESS`；P02 阶段保持 `IN_PROGRESS`，当前执行游标已更新为 P02-W07。

## P02-W07

- 工作包：`P02-W07 event loop lag 采样和 implementation 指标`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T18:56:04+08:00`。
- 修改文件：新增 `src/ns_runtime/event_loop_observability.py` 与 `tests/test_runtime_event_loop_observability.py`；更新 `src/ns_common/async_runtime.py`、`src/ns_runtime/context.py`、`src/ns_runtime/service.py`、`src/ns_runtime/main.py`、`tests/test_async_runtime.py`、`tests/test_runtime_main.py`、实施计划、acceptance log，并新增 [ADR-026](ns_runtime_architecture_decisions_0.0.2.md#adr-026)。设计边界、配置 schema/示例、OBS-1 指标名与 definitions、RuntimeContext 字段、startup preflight、shutdown 相位、backend 和 requirements 未修改。
- `RLO-1` 契约：新增 runtime 私有 `RuntimeEventLoopMonitor` 与冻结 `RuntimeEventLoopSnapshot`。composition root 使用 RSP-1 preflight 的权威 `NsEventLoopSelection.selected` 注入实际 asyncio/uvloop 类型；RuntimeService 验证 monitor 与自身 context 身份相同，在 start hook 成功后启动，由同一 TaskSupervisor 监督，RSD-1 在 flush/close sinks 前取消。默认每 1 秒按 loop monotonic deadline 采样，长阻塞只记录一次并从实际观测时间建立下一 deadline，不追赶旧 tick；lag 窗口固定最多 1024 项，P95/P99 使用 nearest-rank。
- snapshot 与指标：snapshot 覆盖 implementation、最新 lag、P95/P99、样本数、slow-threshold observation 总数、pending task、supervisor cancelled task、executor queue depth、probe failure 和 metric rejection。复用 OBS-1 已冻结的 8 个 `runtime_event_loop_*`/task/executor 标准名称与有限 attributes；implementation 只允许 asyncio/uvloop，pending 只使用 `component_type=runtime`，不引入 ID/tenant 等高基数标签。lag current 使用 histogram，P95/P99 与深度使用 gauge，slow/cancelled 使用累计 counter；`metrics_enabled=false` 时仍维护只读内部 snapshot 但不写 sink。
- 失败与测量语义：普通 clock、metric 构造、sink record 或 probe 失败均 fail-soft，不终止 service、不复制异常文本或对象 repr。clock/sink 拒绝累计为 metric rejection；pending/executor 探针失败累计为 probe failure，对应 snapshot 值为 `None` 且省略该次失真 metric，绝不把未知伪装成零。executor 未创建时深度为合法 0；已有 executor 但本机队列无法安全读取时视为未知。slow callback total 的当前可移植定义为 scheduling lag 达到配置 `slow_callback_threshold_ms` 的 observation 数，不解析 asyncio 私有日志文本。
- 测试结果：W07 monitor 专项 6/6；最终 monitor/main/service/shutdown 联合 `Ran 45, OK`。runtime 环境排除 DEP-1 不安装的 Django cache 后全量 `Ran 336, OK (skipped=1)`；backend 环境根目录全量 `Ran 347, OK (skipped=1)`，唯一跳过为 WSL 下 Windows 专用 event-loop policy。runtime 隔离环境还启动真实 `uvloop.Loop`，确认 implementation=`uvloop`、8 个标准指标齐全、monitor 由 shutdown 取消。两套 `pip check`、全树 `compileall` 与 `git diff --check` 通过。
- 设计边界 review：首轮审查修复长阻塞后逐 tick 追赶导致指标突发；第二轮修复 clock 普通失败可终止 monitor；最终审查修复 probe 失败返回 0 导致未知状态伪装健康。源码扫描只命中 no-listener 与明确“不拥有 thread/exporter”的说明；没有新增 listener/socket/server、transport 指标/adapter/session、Envelope、StateStore、Redis/Valkey、DeliveryRecord、leader/fencing、HTTP 管理端口、exporter、后台线程、全局 context 或强一致写入。指标只进入异步 best-effort sink，设计边界文档未修改。
- 已知限制：1 秒采样周期与 1024 项窗口是当前内部实现常量，尚无热更新合同；slow callback 是 lag-threshold observation，而不是对 asyncio 私有日志的解析。executor queue depth 受 Python loop 实现可观察接口限制，未知时明确省略。W08 只能只读现有启动结果与 snapshot，不得启动第二个 monitor、创建 HTTP 管理端口或宣称 transport/cluster/delivery 可用。
- 下一工作包：`P02-W08 建立本地进程诊断命令，只读取启动配置和本地状态，不开 HTTP 管理端口`，状态为 `IN_PROGRESS`；P02 阶段保持 `IN_PROGRESS`，当前执行游标已更新为 P02-W08。按用户校准后的流程，每个 W 工作包 review 通过后均在同一 codex 分支提交并立即推送，不为工作包创建新分支；W07 提交后的首次推送同时补齐此前尚未推送的 W05/W06 本地提交。

## P02-W08

- 工作包：`P02-W08 本地进程诊断命令`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T19:11:35+08:00`。
- 修改文件：新增 `src/ns_runtime/diagnostics.py` 与 `tests/test_runtime_diagnostics.py`；更新 `src/ns_runtime/startup.py`、`src/ns_runtime/main.py`、`tests/test_runtime_startup.py`、实施计划、acceptance log，并新增 [ADR-027](ns_runtime_architecture_decisions_0.0.2.md#adr-027)。设计边界、配置 schema/示例、RuntimeContext、RuntimeService、event-loop monitor、shutdown、backend、requirements 与公共错误注册均未修改。
- `RDI-1` 契约：唯一 `python -m ns_runtime.main` 入口新增 `diagnose` 子命令；程序化 `main()` 与无参数模块自检行为保持不变。`RuntimeStartupPreflight.inspect()` 复用 RSP-1 的环境、配置、安全、transport admission、本地依赖、TLS 与 event-loop selection 校验，只把必需目录检查改为只读四态。冻结 `RuntimeLocalDiagnosticReport` 提供 ready、配置/依赖通过标记、有限 adapter/TLS/state-store/event-loop 事实和不含路径的目录 role/state；ready/not_ready 分别返回 0/1，稳定公共错误返回 2。
- 只读与安全语义：diagnose 不调用 prepare 或 policy install，不创建/修复目录，不运行 service、monitor 或 task，不构造文件 logger/client/exporter，不注册 signal，不访问远端。错误 JSON 只保留 code、numeric code 以及 component/dependency/directory/field/phase/reason 中的标量值；不输出公共错误 message、完整 details、配置路径、异常 repr 或 cause，未知普通异常统一为无细节 `NS_ERROR`，进程级异常不吞并。backend 环境按 DEP-1 缺少 websockets 时稳定返回 `NS_DEPENDENCY_ERROR`，不伪装 ready。
- 测试结果：startup/diagnostic/main 专项 `Ran 35, OK`；runtime 环境排除 DEP-1 不安装的 Django cache 后全量 `Ran 345, OK (skipped=1)`；backend 环境根目录全量 `Ran 356, OK (skipped=1)`，唯一跳过为 WSL 下 Windows 专用 event-loop policy。两套 `pip check`、全树 `compileall` 与 `git diff --check` 通过。真实 `python -m ns_runtime.main diagnose` 与冷子进程还验证唯一模块入口、稳定退出码、不加载 RuntimeService/RuntimeEventLoopMonitor/websockets 模块以及不创建缺失 startup root。
- 设计边界 review：首轮全量矩阵发现 backend 环境缺少 runtime 可选依赖时测试误期待 not_ready，已修正为验证稳定 dependency error；实现语义无需放宽。最终源码与冷进程扫描确认没有新增 cli/app 入口、listener/socket/server、HTTP 管理端口、transport adapter/session、Envelope、StateStore、Redis/Valkey、DeliveryRecord、leader/fencing、exporter、后台线程/任务、全局 context 或远端访问。诊断只读取显式启动配置和本地能力，设计边界文档未修改。
- 已知限制：本地 ready 只证明当前配置、Python 包、TLS/event-loop capability 与目录访问状态，不代表 listener、IAM、运行中 health、角色权威、StateStore、cluster 或 delivery 已可用；诊断不读取 RLO-1 运行中 snapshot。P16 管理查询仍必须使用统一管理 Envelope，P20 exporter/diagnostic snapshot 仍须独立验收。
- 阶段出口：P02 所有工作包和阶段出口均已验证：无监听模块自检可优雅退出、event-loop implementation/lag 有内部 snapshot、核心依赖均为显式构造注入、本地诊断零启动副作用。P02 状态更新为 `VERIFIED/F2`。
- 下一工作包：`P03-W01 定义核心 Envelope 分组类型模型`，状态为 `IN_PROGRESS`；P03 阶段更新为 `IN_PROGRESS`。继续遵守每个 W 在设计边界 review 通过后，于同一 codex 分支提交并立即推送远端。

## P02-FIX-04

- 工作包：`P02-FIX-04 signal handler 精确恢复`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T19:20:15+08:00`。
- 修改文件：更新 `src/ns_runtime/shutdown.py`、`tests/test_runtime_shutdown.py`、实施计划、acceptance log 与 [ADR-025](ns_runtime_architecture_decisions_0.0.2.md#adr-025)。
- 契约校准：RuntimeSignalRegistration 在 asyncio `add_signal_handler()` 与 fallback `signal.signal()` 两条路径修改 SIGINT/SIGTERM 前，均保存 `signal.getsignal()` 返回的原 handler 对象。close 逆序处理注册；asyncio 路径先 remove loop handler，再由 `signal.signal()` 放回保存对象，fallback 路径直接放回；第二次 close 不重复操作。
- 测试与边界：预装两个不同自定义 handler 后分别通过正常 loop 与强制 fallback 的 context manager 进入/退出 registration，均以对象身份断言精确恢复，并覆盖 close 幂等。FIX-04/FIX-05 联合专项与全量结果见下一记录。未新增 signal owner、signal 类型、transport drain、listener 或其他关闭体系。
- 下一工作包：`P02-FIX-05 critical background task 生命周期联动`。

## P02-FIX-05

- 工作包：`P02-FIX-05 critical background task 与 RuntimeService 生命周期联动`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T19:48:39+08:00`。
- 修改文件：更新 `src/ns_runtime/service.py`、`src/ns_runtime/shutdown.py`、`tests/test_runtime_event_loop_observability.py`、实施计划、acceptance log，并校准 [ADR-021](ns_runtime_architecture_decisions_0.0.2.md#adr-021)、[ADR-025](ns_runtime_architecture_decisions_0.0.2.md#adr-025) 与 [ADR-026](ns_runtime_architecture_decisions_0.0.2.md#adr-026)。
- 契约校准：RuntimeService 对唯一 RuntimeEventLoopMonitor supervised task 登记 critical done callback。正常取消直接忽略；非取消异常不保存异常对象或文本，使用固定原因 `critical_task_failure` 请求同一 RuntimeShutdownCoordinator，并把 RUNNING 转为 FAILED。后续显式 stop 严格执行 RSL-1 的 `FAILED -> STOPPING -> STOPPED`：成功后 STOPPED，失败才回 FAILED。critical 原因与 monitor failed task 分别由 shutdown report 的 reason/failed_tasks 保留；第二次 stop 幂等，不重复 stop hook、coordinator 或资源清理。
- fail-soft 保持：pending/executor probe、clock、metric 构造/record 与 sink 普通失败仍由 RLO-1 内部收敛为 probe failure/metric rejection、未知值或省略指标，不终止 monitor 或 service。正常 shutdown 的 CancelledError 仍产生 cancelled task 和 STOPPED。没有新增 TaskSupervisor、signal owner、shutdown owner、清理 task、线程或端口；shutdown report 与日志只含固定 reason、任务名/数量和异常类型边界，不包含 critical 异常 message/repr。
- 测试结果：要求的 shutdown/monitor/service/main 专项 `Ran 49, OK`；runtime 环境排除 DEP-1 不安装的 Django cache 后 P01/runtime + P02 联合 `Ran 349, OK (skipped=1)`；backend 根目录全量 `Ran 360, OK (skipped=1)`，唯一跳过仍为 WSL 下 Windows 专用 event-loop policy。两套 `pip check`、全树 `compileall` 与 `git diff --check` 通过。
- P02 阶段复审：逐项复核唯一 main 入口、六态 lifecycle、显式 context、startup preflight、角色能力门禁、signal/shutdown、event-loop monitor 与只读 diagnose。未发现 listener/socket/server、transport adapter/session、Envelope/processor、StateStore、Redis/Valkey 权威写入、DeliveryRecord、leader/fencing、HTTP 管理端口、exporter、第二 supervisor/signal/shutdown owner 或远端访问。W08 diagnose 专项仍包含在全量回归且保持零启动副作用；P02 所有工作包、FIX 与阶段出口恢复为 `VERIFIED/F2`。
- 下一工作包：`P03-W01 核心 Envelope 分组类型模型`，状态为 `IN_PROGRESS`；只在本提交推送成功后继续 P03。

## P03-W01

- 工作包：`P03-W01 核心 Envelope 分组类型模型`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:08:02+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/models.py`、`src/ns_runtime/protocol/__init__.py` 与 `tests/test_runtime_protocol_models.py`；更新实施计划、acceptance log，并新增 [ADR-028](ns_runtime_architecture_decisions_0.0.2.md#adr-028)。
- 公共契约变化：建立 `ENV-1` 的 12 个固定 Envelope 分组、冻结类型、严格字段集合、protocol/message 必需和不适用分组省略语义；payload/extensions 动态 JSON 在构造时递归冻结。当前只冻结模型，不声明任何 message capability 可执行。
- 测试结果：W01 专项 5/5；与 exceptions/context/service/roles 联合回归 `Ran 69, OK`；protocol 与测试 compileall、`git diff --check` 通过。
- 安全/隔离检查：首轮发现未知字段名会进入公共异常 details，已改为固定 `$unknown` 并补充不回显测试。源码扫描确认没有 listener/socket/server、transport adapter/session、IAM、StateStore、Redis/Valkey、DeliveryRecord、leader/fencing、管理旁路、ACK 执行或成功响应；未修改 P01/P02 公共对象与异常格式。
- 已知限制：尚未建立 inbound raw/normalized 分离、资源限制、message 专属 schema、版本矩阵、类型注册表、extension 策略、错误 Envelope、canonical serialization 或 processor；这些均保持未启用。
- 下一工作包：`P03-W02 inbound raw 与 normalized model 分离`，状态为 `IN_PROGRESS`；P03 保持 `IN_PROGRESS`。

## P03-W02

- 工作包：`P03-W02 inbound raw 与 normalized model 分离`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:10:01+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/inbound.py`；更新 protocol facade、模型测试、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：`InboundEnvelope` 不含 source/auth_context；入站 mapping 在基础 schema 前对二者分别返回既有 `RUNTIME_SOURCE_FORGED`/`RUNTIME_AUTH_CONTEXT_FORGED`。`normalize_inbound()` 只接受显式 `RuntimeAuthority` 并生成权威 Envelope，sender target capability 仍只是请求条件。
- 测试结果：protocol 模型/入站与 ERR-1 联合 `Ran 34, OK`；compileall、`git diff --check` 通过。
- 安全/隔离检查：伪造字段原值不进入异常；目标 capability 请求不会覆盖 source capabilities digest 或 auth permission digest。review 确认没有 token 验证、session 状态、IAM 调用、tenant 授权、transport、route/delivery 执行、ACK、管理旁路或 success 响应，P01/P02 契约不变。
- 已知限制：`RuntimeAuthority` 只定义注入类型边界，真实性与 tenant/capability 一致性必须由 P05/P06 权威连接上下文建立；P03 不提前实现这些能力。
- 下一工作包：`P03-W03 JSON 资源限制`，状态为 `IN_PROGRESS`。

## P03-W03

- 工作包：`P03-W03 JSON 资源限制`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:12:42+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/codec.py` 与 `tests/test_runtime_protocol_codec.py`；更新 protocol facade、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：冻结唯一 `json.v1` codec 及 `JsonResourceLimits`；默认约束 1 MiB 文档、32 层、65536 字符、4096 容器项、100000 节点、signed 64-bit integer 与有限 float 范围，并拒绝重复 object key、非有限数字、非法 UTF-8 和非 text/bytes 输入。
- 测试结果：codec/models/ERR-1 联合 `Ran 40, OK`；compileall 与 `git diff --check` 通过。
- 安全/隔离检查：深度在 json recursive decode 前扫描，超长 integer 在构造大整数前按位数拒绝；所有 parse/limit error 只含固定 reason，负向测试确认不回显 token/payload/parser exception。没有 frame、socket、连接关闭策略、transport/session/IAM/StateStore、ACK 或 processor 行为。
- 已知限制：P03 只定义 application JSON 文档预算；P04 adapter 仍须独立限制 transport frame/queue，连续恶意消息的断连与限流策略属于后续连接/安全阶段。除 max_envelope_bytes 外的预算当前为显式 codec 常量，未来配置化必须维护此安全上限合同。
- 下一工作包：`P03-W04 基础 schema 与 message.type schema 叠加`，状态为 `IN_PROGRESS`。

## P03-W04

- 工作包：`P03-W04 基础 schema 与 message.type schema 叠加校验`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:14:45+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/schema.py` 与 `tests/test_runtime_protocol_schema.py`；更新 protocol facade、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：新增不可绕过的 `EnvelopeSchemaValidator` base 规则，以及冻结 `MessageTypeSchema`/`InlinePayloadSchema` 声明；message 规则只能收紧 required/forbidden group 和 inline payload 字段集合，不能放宽核心模型与 base schema。
- 测试结果：schema/codec/models 专项 `Ran 19, OK`；compileall 与 `git diff --check` 通过。
- 安全/隔离检查：负向覆盖类型专属 group/field 缺失、额外 payload 字段、禁止 group、target 寻址缺失、route loop segment、非法 delivery attempt 与 schema mismatch；错误不回显攻击者 message type 或 payload 字段。实现无 callback、processor 执行、ACK、transport/session/IAM/StateStore 或成功结果。
- 已知限制：W04 只建立声明式字段边界；内置类型到 schema 的完整映射由 W06/W07 注册表冻结，实际业务语义与状态变化仍由后续 processor 阶段实现。
- 下一工作包：`P03-W05 协议版本兼容矩阵`，状态为 `IN_PROGRESS`。

## P03-W05

- 工作包：`P03-W05 协议版本模型、兼容矩阵与 schema 选择`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:16:41+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/versioning.py` 与 `tests/test_runtime_protocol_versioning.py`；更新 protocol facade、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：冻结 `ProtocolVersion`、`ProtocolCompatibilityMatrix`、`NegotiatedProtocol` 与当前 `JSON_V1_PROTOCOL_MATRIX`。major 严格，minor/patch 只向显式支持版本降级并同时选择 schema key；当前仅启用 protocol 1.0 schema。
- 测试结果：version/schema/codec/models 专项 `Ran 25, OK`；compileall 与 `git diff --check` 通过。
- 安全/隔离检查：覆盖不支持 major、非法 minimum、无兼容区间、minor/patch 选择与攻击者版本文本不回显；超长版本组件在 int 转换前拒绝。没有握手/session 状态、capability 协商、transport、processor、StateStore、ACK 或业务成功路径。
- 已知限制：P03 只提供纯协商策略；P05 才能在 connection.hello 中执行协商并把结果写入 session context。当前矩阵没有宣称 1.1+ 兼容。
- 下一工作包：`P03-W06 内置 message type 全量注册表`，状态为 `IN_PROGRESS`。

## P03-W06

- 工作包：`P03-W06 内置 message type 全量注册表`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:19:09+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/registry.py` 与 `tests/test_runtime_protocol_registry.py`；更新 protocol facade、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：显式冻结 50 个 protocol 1.0 内置 message types 和 13 个必需类型族；`MessageTypeRegistry` 提供不可变 exact lookup 与 version-selected schema lookup，未知 type/schema 使用既有稳定 unsupported error。
- 测试结果：registry/schema/version 专项 `Ran 15, OK`；`git diff --check` 通过。
- 安全/隔离检查：独立冻结 expected type tuple 验证无缺项/重复，每项具备 current schema；未知攻击者 type/schema 不回显。注册无 decorator、动态扫描、回调、实例构造副作用、裸 JSON 命令或执行路径；ACK/管理/集群等只登记名字和 schema，全部仍未实现。
- 已知限制：W06 尚未给注册项补齐权限、processor、审计、feature flag、reliability 与响应元数据；W07 完成前 registry 不能用于最终 dispatch 决策。
- 下一工作包：`P03-W07 注册元数据完整性`，状态为 `IN_PROGRESS`。

## P03-W07

- 工作包：`P03-W07 注册元数据完整性`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:21:24+08:00`。
- 修改文件：扩展 `src/ns_runtime/protocol/registry.py`、protocol facade 与 registry tests；更新实施计划、acceptance log 与 ADR-028。
- 公共契约变化：全部 50 个注册项现具备 schema、强类型 category/default reliability/audit level、权限 tuple、processor key、feature flag/enabled 与 response types；registry 统一执行 category/reliability 基础校验。仅 `runtime.error` 协议构造能力 enabled，其余 49 项明确 disabled。
- 测试结果：registry 专项 6/6；前序 registry/schema/version 联合已通过，`git diff --check` 通过。
- 安全/隔离检查：response type 全部回指已注册类型，元数据与 mapping 不可变；权限声明不执行 IAM，processor key 不解析 callback。review 确认无 transport/session/StateStore/delivery/cluster 行为、ACK 快速通道、裸管理命令或 stub success，P01/P02 错误及能力门禁未修改。
- 已知限制：注册的 capability 与 audit level 只是 P06/P07 将消费的静态声明；P03 不宣称权限已校验或审计已持久化。disabled 行为由 W11 统一 processor 固化。
- 下一工作包：`P03-W08 extension namespace 注册与 schema 边界`，状态为 `IN_PROGRESS`。

## P03-W08

- 工作包：`P03-W08 extension namespace 注册与 schema 边界`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:23:56+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/extensions.py` 与 `tests/test_runtime_protocol_extensions.py`；校准 `ExtensionsGroup` 直接 namespace wire 形状并更新 facade/models tests、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：`extensions` 现直接承载 namespace keys；新增显式不可变 `ExtensionNamespaceRegistry`、contract/schema、unknown policy 与 validation result。默认拒绝未知 namespace；可选 ignore 必须返回 `audit_required=true` 且不传播内容。
- 测试结果：extensions/models/registry 专项 `Ran 18, OK`；`git diff --check` 通过。
- 安全/隔离检查：覆盖未注册、disabled、unauthorized、schema missing/unknown 和 authorized 四类路径；错误不回显 namespace/token/payload，ignored namespace 不进入 accepted。review 确认 extension schema 只能收紧自身对象，不能修改核心 group 规则、注入 source/auth_context、注册 callback、执行插件或开放旁路。
- 已知限制：P03 只返回结构化 audit requirement，不提前实现 P07/P08 审计 sink 或持久化；默认 registry 为空，因此没有任何 extension capability 默认可用。
- 下一工作包：`P03-W09 标准错误 Envelope`，状态为 `IN_PROGRESS`。

## P03-W09

- 工作包：`P03-W09 标准错误 Envelope`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:26:41+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/error_envelope.py` 与 `tests/test_runtime_protocol_error_envelope.py`；收紧 runtime.error 专属 schema，更新 protocol facade、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：新增显式 Sanitizer 的 `ErrorEnvelopeBuilder`/`ErrorEnvelopeContext`；标准 payload 完整映射 ERR-1 policy metadata，runtime.error schema 精确限制字段集合。未知普通异常安全映射 `NS_RUNTIME_ERROR`，进程级异常穿透。
- 测试结果：error Envelope/registry/ERR-1 联合 `Ran 36, OK`；`git diff --check` 通过。
- 安全/隔离检查：恶意自定义 error 的 str/repr 从未调用；自定义 message、details 内 token/credential/payload 均未进入输出。安全 error 的 severity/disconnect/audit 保持 ERR-1，错误 Envelope 通过自身注册 schema。没有日志原异常、cause、auth_context、功能 ACK、transport/session/IAM/StateStore 或业务执行。
- 已知限制：P03 只构造错误 Envelope，不负责 transport 写回、连接关闭、审计持久化或重试动作；这些 policy flags 仍只是 ERR-1 提示，后续层必须结合上下文裁决。
- 下一工作包：`P03-W10 canonical serialization`，状态为 `IN_PROGRESS`。

## P03-W10

- 工作包：`P03-W10 canonical serialization`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:28:34+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/canonical.py` 与 `tests/test_runtime_protocol_canonical.py`；公开复用 codec resource validator，更新 protocol facade、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：冻结 `json.v1.canonical` 为递归 key 排序、UTF-8、紧凑、strict number 的确定性 bytes；checksum 固定 SHA-256 前缀格式，并继续受 W03 所有资源上限约束。
- 测试结果：canonical/codec/error 专项初轮 14/14，补充 round-trip 后专项继续通过；`git diff --check` 通过。
- 安全/隔离检查：outbound NaN/Infinity 与超限文档稳定拒绝；输入 mapping 变更不影响冻结 Envelope；canonical decode/rebuild 稳定。实现不记录或审计 raw bytes，不调用 logger/StateStore，不执行 processor/ACK/transport；调用方仍受 SEC-1 禁止记录完整 payload 的边界。
- 已知限制：格式是本项目冻结的 deterministic JSON，不宣称外部 RFC 8785/JCS 互操作；未来若需要跨语言签名规范必须新增版本/ADR，不能静默改变当前 checksum bytes。
- 下一工作包：`P03-W11 FeatureDisabledProcessor`，状态为 `IN_PROGRESS`。

## P03-W11

- 工作包：`P03-W11 FeatureDisabledProcessor`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:31:01+08:00`。
- 修改文件：新增 `src/ns_runtime/protocol/processors.py` 与 `tests/test_runtime_protocol_processors.py`；更新 protocol facade、实施计划、acceptance log 与 ADR-028。
- 公共契约变化：49 个 disabled 内置类型的 processor key 全部映射到同一 `FeatureDisabledProcessor`；正确请求只返回 `RUNTIME_FEATURE_DISABLED` 标准 runtime.error Envelope，并写固定 best-effort audit fields。enabled 的 runtime.error 输出合同不注册为业务 processor。
- 测试结果：processor/error/P02 role gate 联合 `Ran 13, OK`；W11 后 P03 阶段出口全量结果将在 P03 记录追加。
- 安全/隔离检查：代表性 task.dispatch、delivery.ack、runtime.control.switch_master 均只返回 feature disabled，token/credential/payload 不进入错误或日志；logger 普通失败仍拒绝，contract mismatch 不作为 fallback dispatch。没有调用回调、ACK 状态、transport/session/IAM/StateStore/delivery/cluster/管理功能或 stub success，P01/P02 `RUNTIME_FEATURE_DISABLED` 语义保持。
- 已知限制：审计当前沿用显式 Logger 的 best-effort 边界；P07/P08 必须消费同一注册 metadata 建立强流水线/审计，不能把 logger success 当审计持久化证明。
- 下一工作包：P03 阶段出口验收；完成全部专项与联合/全量回归后才可把游标移至 `P04-W01 NOT_STARTED`。

## P03-FIX-01

- 工作包：`P03-FIX-01 阶段出口严格类型与深度口径校准`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-20T21:35:39+08:00`。
- 修改文件：更新 `src/ns_runtime/protocol/models.py`、`codec.py`、models/codec tests、实施计划、acceptance log 与 ADR-028。
- 契约校准：必填 protocol/route/delivery 整数不再通过 optional 检查接受 None；capabilities/route_segment 明确要求 array，未知 direct mapping key 固定拒绝。JSON depth 统一表示 object/array nesting，容器标量不额外增加一层。
- 测试与边界：补充 None、字符串伪数组、非字符串 unknown key 和 depth=1 边界；P03 专项增至 `Ran 49, OK`。校准只收紧 W01/W03，不新增 transport/session/IAM/StateStore/processor success 或任何后续能力。
- 下一工作包：继续 P03 阶段出口全量回归。

## P03

- 阶段：`P03 Envelope 协议层与类型注册表`。
- 状态：`VERIFIED`，目标完成度 `F2`。
- 完成时间：`2026-07-20T21:36:57+08:00`。
- 工作包状态：`P03-W01` 至 `P03-W11` 全部 `VERIFIED`；阶段出口复审校准 `P03-FIX-01` 同为 `VERIFIED`。
- 冻结契约：`ENV-1` 完整覆盖唯一 `json.v1` grouped Envelope、raw/normalized authority、严格字段/资源/schema/version、50 项 registry、extension namespace、标准 error、canonical serialization 与 49 项 unified feature-disabled processor；ADR-028 更新为阶段冻结事实。P01/P02 的 CFG/SEC/LOG/ERR/RTC/RRS/RSD 等合同未修改。
- 最终测试：P03 专项 `Ran 49, OK`；runtime 环境排除按 DEP-1 不安装的 Django cache 后 P01+P02+P03 联合 `Ran 398, OK (skipped=1)`；backend 环境根目录全量 `Ran 409, OK (skipped=1)`。唯一 skip 为 WSL 下 Windows 专用 event-loop policy。runtime/backend 两套全树 `compileall`、两套 `pip check`、`git diff --check` 全部通过。
- 负向/安全/边界：覆盖 source/auth_context 伪造、unknown/null/empty、duplicate key、invalid UTF-8/JSON、depth/size/string/array/object/node/integer/float、major/minor/patch、type/schema/category/reliability、extension 四路径、error secret/exception repr、canonical determinism 及 task/ACK/management disabled。源码边界扫描确认 protocol 包无 socket/websocket/listener、Redis/Valkey/StateStore、SessionContext/IAM、DeliveryRecord 或旁路成功实现。
- 已知限制：仅 runtime.error 构造 enabled；49 个其余内置类型均稳定 feature disabled。extension 默认 registry 为空，audit ignore 只产生待 P07 消费的结构化要求；canonical 是项目 deterministic JSON 而非外部 JCS 声明；P04/P05/P06/P07/P08 及 delivery/cluster 能力均未实现。
- 执行游标：当前阶段 `P04 Transport 抽象与 WebSocket/TCP Adapter`；当前工作包 `P04-W01`；状态 `NOT_STARTED`；最近已验证阶段 `P03 Envelope 协议层与类型注册表`。按停止条件不开始 P04，等待外部 review。

## P03-FIX-02

- 工作包：`P03-FIX-02 StreamGroup 严格数组与 extension namespace wire 语法边界`。
- 状态：`VERIFIED`；P03 已重新达到 `VERIFIED/F2`，P04-W01 保持 `NOT_STARTED`。
- 完成时间：`2026-07-20T23:38:07+08:00`。
- 修改文件：更新 `src/ns_runtime/protocol/models.py`、`extensions.py`、models/codec/extensions tests、实施计划、acceptance log 与 ADR-028；设计边界文档未修改。
- 公共契约校准：missing_sequences/received_sequences/ack_ranges 顶层严格限制为 list/tuple；sequence 元素和 range 两端使用 required non-negative integer，range 项严格为长度 2 的 list/tuple 且 start <= end；合法模型继续冻结为 tuple，wire 输出仍为 JSON array。extension registry 对每个 wire namespace 先执行冻结 dotted-lowercase 语法校验，再 lookup/执行 unknown policy；非法语法固定 `group=extensions, field=$namespace, reason=invalid_namespace` 且不回显输入。
- 测试结果：直接构造、`envelope_from_mapping`、`JsonV1Codec.decode_inbound` 的指定负向及 bool/float/str/其他 iterable 补充边界全部稳定返回 `NsRuntimeEnvelopeSchemaError`；P03 专项 `Ran 52, OK`；runtime 环境排除 DEP-1 不安装的 Django cache 后 P01+P02+P03 联合 `Ran 401, OK (skipped=1)`；backend 根目录全量 `Ran 412, OK (skipped=1)`。唯一 skip 为 WSL 下 Windows 专用 event-loop policy；runtime/backend 两套全树 `compileall`、两套 `pip check`、`git diff --check` 全部通过。
- 安全/隔离检查：非法 namespace 在 REJECT 与 IGNORE_AND_AUDIT 下都先 fail-closed，错误 details 只有固定字段；合法未知 `com.attacker.secret` 在 IGNORE_AND_AUDIT 下仍只增加 ignored_count/audit_required。源码 review 未发现原生 TypeError/ValueError 泄露、输入回显、裸 JSON 管理命令、伪 ACK、stub success，未修改 P01/P02 冻结契约，也未新增 transport/session/IAM/pipeline/StateStore/delivery/cluster 能力。
- 已知限制：extension ignore 仍只产生待 P07 消费的结构化审计要求；49 个未实现内置 message type 继续由 FeatureDisabledProcessor 稳定拒绝，仅 runtime.error 构造 enabled。
- 下一工作包：执行游标恢复为 `P04-W01 NOT_STARTED`；按本次暂停要求不开始 P04，等待外部 review。

## P04-W01

- 工作包：`P04-W01 transport-independent contracts`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:12:04+08:00`。
- 修改文件：新增 `src/ns_runtime/transport/models.py`、`contracts.py`、package facade 与 `tests/test_runtime_transport_contracts.py`；更新实施计划和执行游标。
- 公共契约变化：新增无第三方类型的 `TransportAdapter`、`TransportSession`、`TransportMessage`、`TransportClose`、`TransportError`、`TransportCapabilities`；transport session 在 P05 前只表达 handshaking/closing/closed，不存在 active 或业务消息接受状态。完整文本从 repr 排除，错误 details 仅允许固定低基数字段。
- 测试结果：W01 专项 `Ran 5, OK`；P02 context/service/shutdown 与 P03 models 联合 `Ran 51, OK`；transport package compileall 通过。
- 安全/隔离检查：源码扫描未引入 WebSocket 库对象、listener、Envelope codec、IAM、tenant、processor、ACK/DeliveryRecord、StateStore、管理端口、全局 context 或第二 lifecycle owner；错误模型不保留底层异常、peer/path/session ID 或 payload。
- 已知限制：本包只冻结抽象与值对象，不创建 adapter/listener，不声明 websocket_tcp 能力，不执行收发；这些由 W02-W10 完成。
- 下一工作包：`P04-W02 capability declaration`，状态为 `IN_PROGRESS`。

## P04-W02

- 工作包：`P04-W02 websocket_tcp capability declaration`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:15:00+08:00`。
- 修改文件：新增 `src/ns_runtime/transport/websocket_tcp.py` 的常量声明，更新 transport facade、contract tests、实施计划和执行游标。
- 公共契约变化：`websocket_tcp` 权威声明且仅声明 `reliable_ordered_messages`、`transport_flow_control`、`native_keepalive`；stream/datagram/multiplexing/path migration/per-stream flow control/0-RTT/resume 均明确不支持。
- 测试结果：W01+W02 transport contracts 专项 `Ran 7, OK`；`git diff --check` 通过。
- 安全/隔离检查：fresh-process 冷导入证明 transport facade 与 capability 模块不加载 `websockets`；模块不创建 listener、event loop、task 或全局 adapter，不接受客户端自报 capability。
- 已知限制：capability 是 adapter 固定事实但尚未有运行 listener；W03 将实现唯一正式 adapter 的正常路径。
- 下一工作包：`P04-W03 websocket_tcp operational adapter`，状态为 `IN_PROGRESS`。

## P04-W03

- 工作包：`P04-W03 WebSocket TLS/TCP operational adapter`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:22:00+08:00`。
- 修改文件：实现 `WebSocketTcpAdapterOptions`、`WebSocketTcpAdapter`、`WebSocketTcpSession`，更新 facade，新增 `tests/test_runtime_transport_websocket_tcp.py`，更新实施计划和执行游标。
- 公共契约变化：唯一正式 adapter 延迟加载 websockets 16，在显式 loopback host/port 上建立 TLS/TCP 或显式受控非生产明文 listener；accepted session 仅为 handshaking，完整文本 receive/send、native ping/pong、typed admission/drain、session/adapter close 幂等且有界。公共接口不暴露第三方 connection/server。
- 测试结果：真实 loopback 明文与自签名 TLS、双向完整文本、ping/pong、close 幂等、prod 明文 fail-closed、端口占用 listener 错误归一化；W01-W03 专项 `Ran 11, OK`，startup/shutdown/service/P03 codec 联合 `Ran 53, OK`，`git diff --check` 通过。
- 安全/隔离检查：listener 仅在 `start()` 内延迟加载并创建；端口失败不回显地址/端口/底层异常，close frame reason 固定为空；无 URL/query、peer、payload、connection repr 日志。没有 active 迁移、Envelope/IAM/tenant/processor/ACK/DeliveryRecord/StateStore/管理 HTTP 或第二 signal/event-loop owner。
- 已知限制：W03 验证正常文本路径；binary/invalid UTF-8/oversize 的冻结负向策略由 W04 完成，独立有界读写应用队列与完整背压由 W05 完成。
- 下一工作包：`P04-W04 WebSocket text-only enforcement`，状态为 `IN_PROGRESS`。

## P04-W04

- 工作包：`P04-W04 WebSocket text-only enforcement`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:25:00+08:00`。
- 修改文件：扩展 `tests/test_runtime_transport_websocket_tcp.py` 的 binary、invalid UTF-8 与 oversize 真实 loopback 负向矩阵，更新实施计划和执行游标。
- 公共契约变化：WebSocket application data 只允许完整 UTF-8 text；binary 固定以 1003/protocol_error 关闭并返回标准 transport receive error，非法 UTF-8 由协议层以 1007 关闭，超过 adapter 最大消息边界以 1009 关闭。不得转换 binary 或调用 P03 codec。
- 测试结果：W01-W04 transport 专项 `Ran 14, OK`，并以 DeprecationWarning-as-error 运行；`git diff --check` 通过。
- 安全/隔离检查：负向错误 details 仅含固定 operation/reason/transport_type；不复制 frame、payload、第三方异常 message/repr、close reason 或 WebSocket 对象。源码扫描确认 adapter 不解析 JSON/Envelope，也不产生 runtime ACK。
- 已知限制：底层 websockets frame queue 已受限，但 P04 独立的每-session application read/write queue 和背压语义由 W05 完成。
- 下一工作包：`P04-W05 bounded queues and backpressure`，状态为 `IN_PROGRESS`。

## P04-W05

- 工作包：`P04-W05 bounded per-session queues and backpressure`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:30:00+08:00`。
- 修改文件：重构 `WebSocketTcpSession` 为 TaskSupervisor 所有的 reader/writer pump，扩展 adapter options，新增 `tests/test_runtime_transport_backpressure.py` 并补充 adapter shutdown 测试，更新实施计划和执行游标。
- 公共契约变化：每 session 独立有界 read/write queue；reader 只投递完整 text message，read full 固定 1013 并关闭；writer 串行保持消息顺序，write full 立即返回 `RUNTIME_TRANSPORT_FLOW_CONTROL_BLOCKED`，send timeout 返回 `RUNTIME_TRANSPORT_SEND_FAILED` 并有界关闭。取消 queued send 不写底层，close/adapter drain 并发幂等且拒绝新写入。所有 I/O task 由既有显式 TaskSupervisor 创建，无第二 supervisor/event-loop owner。
- 测试结果：读队列满、慢写/写队列满、并发 send 顺序、取消 queued send、发送超时、10 路并发 close、关闭后写入、adapter shutdown 全部通过；W01-W05 专项 `Ran 20, OK`（warnings-as-errors），P01 async + P02 lifecycle/main + P03 codec 联合 `Ran 91, OK (skipped=1)`，compileall 与 `git diff --check` 通过。
- 安全/隔离检查：所有 queue 均显式 maxsize；send/close/ping/adapter shutdown 均有 wait_for deadline，不存在无限 queue 或 transport wait。pending write repr 排除 text，失败不复制底层 exception；transport send success 只完成局部 future，不产生 ACK/DeliveryRecord/retry 决策。
- 已知限制：session 尚未冻结 transport/path 标识和安全摘要（W06），第三方 close/异常的细分公共映射将在 W07 完成。
- 下一工作包：`P04-W06 transport identities and safe diagnostics`，状态为 `IN_PROGRESS`。

## P04-W06

- 工作包：`P04-W06 transport identity and safe diagnostics`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:35:00+08:00`。
- 修改文件：新增 `src/ns_runtime/transport/identity.py` 与 `tests/test_runtime_transport_identity.py`，扩展 TransportSession contract、websocket adapter/session、facade 和既有 transport tests，更新实施计划和执行游标。
- 公共契约变化：冻结 transport-local `transport_connection_id`、`transport_session_id`、`transport_stream_id`、`TransportPathSnapshot(path_id/path_epoch/validated_at/migration_count)`；标识由显式 factory 创建且全部从 repr 排除。local/peer address 在 adapter 边界只转为 16-hex SHA-256 摘要，公开 `TransportDiagnosticSummary` 只含 transport_type、TLS flag 与受控摘要。
- 测试结果：确定性四类 ID、初始 path、地址不泄露、hostile repr/str 不调用、非法 UUID 安全失败、真实明文/TLS session 摘要通过；transport+P01 identifiers/security/observability 联合 `Ran 84, OK`，compileall 与 `git diff --check` 通过。
- 安全/隔离检查：诊断不保留完整地址、URL/query、证书、payload 或第三方对象；高基数 transport/path ID 只存在本地类型化对象且 repr=false。模型未创建 P05 logical connection_id/connection_epoch/session state，也无 migration/resume 实现。
- 已知限制：websocket_tcp path 固定 epoch=0/migration_count=0 且单受控 message stream；P21 adapter 才能声明 path migration 或 multiplexing。W07 将冻结底层异常的安全分类。
- 下一工作包：`P04-W07 normalized transport errors`，状态为 `IN_PROGRESS`。

## P04-W07

- 工作包：`P04-W07 normalized transport errors`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:40:00+08:00`。
- 修改文件：新增 `src/ns_runtime/transport/errors.py` 与 `tests/test_runtime_transport_errors.py`，接入 websocket listener/reader/writer/keepalive，补充真实 remote/protocol/limit close tests，更新 facade、实施计划和执行游标。
- 公共契约变化：`normalize_transport_exception()` 将第三方 handshake/listener/TLS/protocol/oversize/remote close/send timeout/send failure/keepalive/receive failure 收敛为 `TransportErrorKind`、现有 `RUNTIME_TRANSPORT_*` code 与安全 NsRuntimeTransportError；差异由固定 reason 保留。正常 remote close 与异常 remote close、protocol、limit、adapter shutdown 均可区分；进程级 BaseException 原对象穿透。
- 测试结果：8 类第三方/系统异常映射、hostile exception str/repr 禁止、BaseException 穿透、真实 1000/1007/1009 close 分类通过；W01-W07 transport 专项 `Ran 27, OK`（warnings-as-errors），ERR-1/RSD-1/P03 error Envelope 联合 `Ran 38, OK`，compileall 与 `git diff --check` 通过。
- 安全/隔离检查：mapper 从不复制或调用底层异常 message/repr，不保留 cause，details 只含固定 component/operation/reason/transport_type；remote close reason、证书文本、socket 地址、query、payload 和库对象均未进入错误。BaseException 不被 fail-soft 吞掉。
- 已知限制：错误 code 复用 ERR-1 已冻结 transport 域，不新增或重编号 P01 错误；更细分类由 P04 TransportErrorKind 与低基数 reason 表达。W08 将冻结 adapter registry 和禁用依赖隔离。
- 下一工作包：`P04-W08 adapter registry`，状态为 `IN_PROGRESS`。

## P04-W08

- 工作包：`P04-W08 explicit adapter registry`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:44:00+08:00`。
- 修改文件：新增 `src/ns_runtime/transport/registry.py` 与 `tests/test_runtime_transport_registry.py`，更新 facade、实施计划和执行游标。
- 公共契约变化：不可变 registry 精确登记 `websocket_tcp`、`websocket_http3`、`webtransport_http3`、`quic_native`；仅 websocket_tcp 为 available 且具有 factory/capabilities。未来三项为 `available=False`、空 capabilities、factory=None；`create_enabled` 只构造显式启用 adapter，不启动 listener，禁用/未知项稳定 `RUNTIME_TRANSPORT_DISABLED`。
- 测试结果：登记闭集/不可变性、唯一可用 adapter、构造不监听、禁用与 duplicate 负向、fresh-process 依赖隔离通过；registry/contracts/requirements/startup/bootstrap 联合 `Ran 38, OK`，compileall 与 `git diff --check` 通过。
- 安全/隔离检查：fresh process 证明 registry import/disabled lookup 不加载 websockets/aioquic/webtransport；依赖清单仍只有正式 websockets 16，无 QUIC/WebTransport 包。registry 不拥有 start/close、signal、loop、TaskSupervisor 或 listener 生命周期。
- 已知限制：未来 adapter 名称只是 reserved registration，不表示可用；启用仍在 RSP-1 preflight 和 registry 双层 fail-closed。W09 将把所有 adapter 可复用的测试合同冻结为 TC-1。
- 下一工作包：`P04-W09 transport conformance suite`，状态为 `IN_PROGRESS`。

## P04-W09

- 工作包：`P04-W09 reusable transport conformance / TC-1`。
- 状态：`VERIFIED`；`TC-1` 首次冻结为 `VERIFIED`。
- 完成时间：`2026-07-21T10:49:00+08:00`。
- 修改文件：新增 production `src/ns_runtime/transport/conformance.py` 的 22-case 闭集、测试侧 `tests/transport_conformance.py` 公共 mixin/harness 与 `tests/test_runtime_transport_conformance.py` websocket 实例，更新 facade、实施计划、TC-1 登记和执行游标。
- 公共契约变化：TC-1 精确覆盖 capability、start/close、TLS/plaintext、text/binary/UTF-8/size、read/write queue、backpressure、keepalive、abnormal/remote close、concurrent/cancel/idempotent、shutdown order、disabled dependencies、error/safe diagnostics 和 send-not-ACK。未来 adapter 必须复用公共 harness，并为 raw frame/transport 特有项提供专项证据。
- 测试结果：公共 conformance mixin 6 项全部通过；与 W01-W08 adapter 专项合并为 transport conformance `Ran 38, OK`（warnings-as-errors）。真实 loopback、可控慢 I/O 与 fresh-process dependency tests 均包含在内；compileall 与 `git diff --check` 通过。
- 安全/隔离检查：公共并发 send 明确只返回 None 且 supervisor 中无 ack/delivery task，session 无 ack/DeliveryRecord API；shutdown case 验证 stop_admission 后旧 session 可受控处理、再 drain/close。没有业务 callback 或 stub success。
- 已知限制：TC-1 的低基数 metrics evidence 由 W10 完成后追加阶段记录，不改变现有 22-case 身份；P05 connection.hello/IAM/Envelope business conformance 仍未开始且不属于 P04 transport adapter 自身。
- 下一工作包：`P04-W10 transport metrics and lifecycle integration`，状态为 `IN_PROGRESS`。

## P04-W10

- 工作包：`P04-W10 transport metrics and runtime lifecycle integration`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:53:00+08:00`。
- 修改文件：新增 `transport/metrics.py`、`lifecycle_contracts.py`、`lifecycle.py`、冷导入安全的 `_transport_lifecycle_contract.py`、metrics/lifecycle tests；扩展 OBS-1 有限 close/error attributes、WebSocket instrumentation、registry build context、RSD-1 coordinator phases、main composition root 和相关 tests；更新实施计划与 ADR-029。
- 公共契约变化：既有 10 个 runtime transport 指标全部实际记录，close_reason/error_code 为显式有限闭集且禁止任何 ID/peer/path/message/tenant/exception attribute。`TransportRuntimeService` 复用同一 RuntimeService/context/coordinator/TaskSupervisor/event loop；首次 request 同步 stop admission，异步顺序固定 stop_admission → drain session/I/O → close adapters/listeners → cancel tasks → sinks/clients/logger。main 仅在 RSP-1 成功后构造 registry/manager/listener；TLS 配置无显式 SSLContext 时 fail-closed，完整材料仍属 P20。
- 测试结果：10 指标闭集、属性基数、sink raise/reject fail-soft；真实 adapter+service 建连/文本/metrics/drain；精确 shutdown order、普通 adapter failure 隔离、BaseException 身份、partial-start cleanup、service/main/RSD/OBS 回归通过。W10 专项与关联回归 `Ran 109, OK`；另行冷导入确认 `ns_runtime.service` 不加载 transport package，compileall 与 `git diff --check` 通过。
- 安全/隔离检查：首次发现 service/shutdown/transport facade 冷导入环后，将最小 lifecycle Protocol 下沉内部引导模块并重跑 41 项 P02 context/service/shutdown 回归，问题已消除。metrics 不含 connection/session/transport/path/message/tenant ID、peer 或异常文本；普通 sink/adapter failure 不破坏后续相位，BaseException 原对象穿透。没有第二 lifecycle/signal/supervisor/loop owner，也没有 P05+ 业务能力。
- 已知限制：CFG-1 没有 P20 证书材料字段，composition root 对启用 TLS 但未显式注入 server SSLContext 的情形稳定 fail-closed；真实 TLS loopback 已通过 adapter API。main 仍执行一次 listener self-check 后走统一 shutdown，不承担长期 daemon wait 策略。read queue capacity 暂由现有 write_queue_capacity 显式派生，未修改冻结 CFG-1。
- 下一工作包：P04 阶段出口联合与全量验证，状态为 `IN_PROGRESS`。

## P04-FIX-01

- 工作包：`P04-FIX-01 missing websocket dependency error-normalization isolation`。
- 状态：`VERIFIED`。
- 完成时间：`2026-07-21T10:58:00+08:00`。
- 触发原因：阶段出口 backend 根目录全量在 `normalize_transport_exception(_HostileError)` 发现无条件导入 `websockets.exceptions`，导致按 DEP-1 不安装 runtime driver 的环境出现 ModuleNotFoundError，违反 W08 disabled dependency isolation。
- 修复：第三方 exception class resolver 改为单次 lazy cache；ImportError 时返回四个互不匹配的内部 sentinel exception type，普通未知异常继续映射 `RUNTIME_TRANSPORT_RECEIVE_FAILED/read_failed`，不会伪装 ConnectionClosed/handshake/oversize。启用依赖环境仍使用真实 websockets 类型；BaseException 语义不变。
- 测试结果：backend errors/contracts/registry `Ran 15, OK (skipped=1)`，skip 仅为确需 websockets 的第三方 class matrix；runtime errors/websocket/registry `Ran 17, OK`。fresh-process registry 继续证明未加载 websockets/aioquic/webtransport。
- 安全/隔离检查：fallback 不捕获或保存原异常，不调用 str/repr，不把 ImportError 文本或模块路径复制到错误；sentinel 永不作为 adapter success 或 capability。无新 dependency、listener、global registry 或 stub success。
- 下一工作包：恢复 P04 阶段出口 backend 全量与全部验证。

## P04

- 阶段：`P04 Transport 抽象与 WebSocket/TCP Adapter`。
- 状态：`VERIFIED/F2`；`P04-W01` 至 `P04-W10` 与 `P04-FIX-01` 全部 `VERIFIED`，`TC-1` 与 ADR-029 已冻结。
- 完成时间：`2026-07-21T11:00:00+08:00`。
- 修改范围：新增 transport contracts、capabilities、WebSocket/TCP adapter、有界 session queues、transport-local identity、安全错误归一化、immutable adapter registry、22-case conformance harness、10 项 OBS-1 transport metrics，以及复用既有 RuntimeService/context/coordinator/TaskSupervisor/event loop 的 lifecycle integration；没有实现 P05+ logical connection、IAM、processor、StateStore、delivery 或 cluster 能力。
- 专项与联合测试：P04 最终专项 `Ran 45, OK`；P03+P04 联合矩阵 `Ran 97, OK`；真实 TLS 与受控开发明文 loopback、text-only/close codes、oversize/invalid UTF-8、queue/backpressure/cancellation/concurrent send、registry dependency isolation、metrics cardinality 与 shutdown order 均通过。
- 全量回归：runtime 目标矩阵 `Ran 446, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy；backend 根目录全量 `Ran 457, OK (skipped=23)`，其中 22 项为 DEP-1 未安装 websockets 时明确跳过的真实 driver 操作测试，另 1 项为 Windows policy。runtime/backend 的 `pip check`、`compileall -q src tests` 与 `git diff --check` 全部通过。
- 安全/隔离检查：生产 transport 未引用 JsonV1Codec、processor、DeliveryRecord、AckRecord、StateStore 或业务实现；所有 session application queues 显式有界；未创建第二 signal/lifecycle coordinator/TaskSupervisor/event loop/global context；metrics 不含高基数 ID、peer/path/message/tenant/异常文本；WebSocket 第三方导入保持 lazy，未启用的 HTTP/3、WebTransport、QUIC 无 factory、无依赖加载、无伪成功。
- 提交与推送：同一 `codex/ns-runtime-implementation` 分支逐包提交并推送，实施提交从 `63d34c6`（W01）至 `9f0e824`（P04-FIX-01）；阶段出口文档在本记录对应提交中冻结。
- 已知限制：完整生产证书材料配置仍属 P20；composition root 未显式注入 server SSLContext 时 TLS fail-closed。P04 transport session 只提供底层消息边界，不代表 P05 logical session 已建立或任何业务消息可用。
- 下一工作包：执行游标推进到 `P05-W01 连接状态机`，状态保持 `NOT_STARTED`；本阶段验收未开始 P05。

## P04-FIX-02

- 工作包：`P04-FIX-02 transport terminal outcome 与可重试清理语义`。
- 状态：`VERIFIED`；P04 已恢复 `VERIFIED/F2`，`P05-W01` 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T11:35:47+08:00`。
- 触发原因：阶段后续 review 发现 receive normalized failure 的终态 close 分类被统一覆盖、keepalive failure 未关闭 session、send 存在调用方与 writer 双 deadline、close cancellation 提前发布 CLOSED，以及 composition root 未在后续 start step 失败后显式清理已启动 transport。
- 修改文件：校准 `transport/websocket_tcp.py` reader/keepalive/send/close 终态路径与 `main._run_service_once()` FAILED-start caller cleanup；扩展 WebSocket loopback、backpressure/cancellation、metrics 和 lifecycle tests；更新 implementation plan、TC-1 evidence 与 ADR-029。
- 公共契约变化：normalized receive failure 按 kind 保留 `REMOTE_CLOSED`、`PROTOCOL_ERROR`、`MESSAGE_TOO_LARGE`、`RECEIVE_FAILED` 的 exact close reason/initiator/clean/metric；keepalive timeout/普通失败先记录固定 error metric并以 `KEEPALIVE_FAILED` terminal close 后抛原归一化公共异常，CancelledError 不记失败。send 只由调用方 completion wait 持有一个覆盖 queue+write 的 deadline：queued timeout 永不触发底层 send，active timeout 取消 writer 并在 CLOSED 后返回。close cancellation 只保留原始 pending outcome 与资源所有权，不发布 close_info/event/metric；后续及并发 close waiter 可重试真实清理且最终只发布一次。`_run_service_once()` 在 start 进入 FAILED 后显式 stop；普通 cleanup failure 不覆盖原 start exception，首次进程级 BaseException 优先。
- 测试结果：P04 专项 `Ran 59, OK`；P03+P04 联合 `Ran 111, OK`；九个指定 websocket/backpressure/errors/lifecycle/metrics/conformance/service/shutdown/main 模块 `Ran 85, OK`。真实 loopback 覆盖 1000、1007、1009、abnormal remote close 与注入 generic receive failure，并逐项断言 public reason、close_info reason/initiator/clean 及 close metric 一致且无 reason text 泄露。可控竞态覆盖 queued/active timeout、active timeout 等待 terminal close、ping timeout/普通异常/取消、close cancellation+retry+并发 waiter，以及 monitor start exception/cancellation 后 transport/listener/session/task cleanup 和异常身份优先级。
- 全量回归：runtime 目标矩阵 `Ran 460, OK (skipped=1)`；backend 根目录全量 `Ran 471, OK (skipped=32)`，skip 为 Windows event-loop policy 与 DEP-1 缺少 runtime WebSocket driver 时的明确操作测试。runtime/backend `pip check`、`compileall -q src tests` 与 `git diff --check` 全部通过。
- 安全/隔离检查：未引入 P05 logical connection/hello/resume、IAM、processor、StateStore、DeliveryRecord、ACK 或 cluster；没有第二 coordinator/signal owner/TaskSupervisor/event loop/global context；所有 queue 仍显式有界；异常 message/repr、peer、URL、payload、完整 transport ID 未进入错误、日志或指标，send success 仍不产生 runtime ACK。
- 已知限制：完整生产证书材料仍属 P20；FIX-02 只冻结底层 transport terminal outcome 与可重试清理，不开放 handshaking 之后的业务状态。
- 下一工作包：执行游标恢复到 `P05-W01 连接状态机`，状态保持 `NOT_STARTED`；本 FIX 未开始 P05。

## P05-W01

- 工作包：`P05-W01 logical connection state machine`。
- 状态：`VERIFIED`；P05 阶段进入 `IN_PROGRESS/F1`，下一游标为 P05-W02。
- 完成时间：`2026-07-21T13:49:48+08:00`。
- 修改文件：新增 `src/ns_runtime/connection/state.py` 与 connection facade，新增 `tests/test_runtime_connection_state.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：建立与 P04 `TransportSessionState` 完全分离的 logical connection 七态矩阵 accepted/handshaking/authenticated/active/draining/closing/closed；每次迁移由实例级 asyncio lock 原子串行化。closing 强制选择 13 项固定低基数 close reason，closed 为终态并保留 reason，snapshot 为 frozen/slots/kw_only 且仅含 state、reason、transition sequence。
- 测试结果：W01 专项 `Ran 9, OK`；排除按 DEP-1 不安装 Django 的 `tests.test_cache` 后，P01-P04+P05-W01 runtime 联合 `Ran 469, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy。`compileall -q src tests` 通过。
- 安全/隔离检查：非法/重复/越级迁移不修改任何状态；并发 duplicate hello、hello/close、active/drain/close 均只有线性化结果，不产生双 active，draining 不回退，closed 不可迁移。connection package 不引用 transport ID/WebSocket、token/Envelope/payload、global config/client/context、TaskSupervisor、processor、DeliveryRecord、AckRecord 或 StateStore；不创建 task、thread、loop、queue 或第二生命周期 owner。
- 已知限制：W01 只冻结状态机和关闭分类；尚未绑定 transport、生成 logical ID、读取 Envelope 或建立 handshake deadline。SC-1、IAM、active/index、heartbeat、grace/resume、reauth 和 audit 仍按 W02-W14 保持未完成，生产 ordinary connection 继续 fail-closed。
- 下一工作包：`P05-W02 hello-first 与 handshake deadline`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W02

- 工作包：`P05-W02 hello-first and handshake deadline`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W03。
- 完成时间：`2026-07-21T13:57:58+08:00`。
- 修改文件：新增 `src/ns_runtime/connection/handshake.py` 与 facade 导出，新增 `tests/test_runtime_connection_handshake.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：`ConnectionHelloReceiver` 对每个 transport session 只允许一次 claim，使用既有 TaskSupervisor 创建 receive/deadline 两个具名任务，以显式 Clock 总 deadline 竞速；timeout 与同 tick hello 同时发生时 timeout 稳定胜出。第一条消息仅经 P03 JsonV1Codec、InboundEnvelope 和 exact registry schema 验证；非 hello、malformed、duplicate、timeout、cancel、transport failure 均终止 logical/transport handshake，不进入 processor。
- 测试结果：W01-W02 connection 专项 `Ran 22, OK`，其中 W02 13 项覆盖成功、non-hello、malformed、不读第二条、timeout、deadline 边界、cancel、duplicate/concurrent duplicate、hello/close、transport failure 和 close retry；P01-P04+P05-W01/W02 runtime 联合 `Ran 481, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy。`compileall -q src tests` 与 `git diff --check` 通过。
- 安全/隔离检查：receiver 不保存或复制 hello/payload，仅把 P03 冻结 group 引用装入临时 schema shape；失败不回显 message、payload、transport exception 或 ID。任务名只使用显式本地数值 sequence，不含 logical/transport/path/identity/tenant/message ID。源码不引用 processor callback、IAM/global config/client/context、DeliveryRecord、AckRecord 或 StateStore；native ping/pong 未替代 hello，普通 cleanup failure 不覆盖原错误，CancelledError 原对象语义保持。
- 已知限制：W02 成功只返回待 W03 消费的 InboundEnvelope，logical state 保持 handshaking；尚未读取 token 声明、认证、协商、构造 SessionContext、发送 accepted 或进入 active。生产 ordinary connection 仍 fail-closed。
- 下一工作包：`P05-W03 controlled hello parsing and test IAM boundary`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W03

- 工作包：`P05-W03 controlled hello parsing and test IAM boundary`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W04；P06-B01/P06-R01 仍为 `NOT_STARTED`。
- 完成时间：`2026-07-21T14:10:22+08:00`。
- 修改文件：新增 `connection/hello.py`、`connection/iam.py`、`connection/authentication.py` 与 facade 导出，扩展 hello receiver 的受控终止接口，新增 `tests/test_runtime_connection_authentication.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增单次、repr-redacted `HandshakeCredential`，冻结 `PendingHelloClaims`/`HelloResumeRequest`，使用 P03 extension registry 精确登记 `ns.connection_resume` 而不修改 ENV-1 hello payload schema；新增显式 `HandshakeIamAdapter`、frozen/deep-copied `HandshakeIamAuthority`、offline deterministic test adapter 与 production fail-closed adapter。`ConnectionHandshakeAuthenticator` 以同一显式 Clock/TaskSupervisor 总 deadline 覆盖 receive、parse 和 IAM，并只在 authority 有效且 component_type 一致后进入 authenticated。
- 测试结果：W01-W03 connection 专项 `Ran 35, OK`；W03 13 项覆盖 allow、prod fail-closed、deny、total timeout、cancel、expired、inconsistent identity、resume typed refs、protocol mismatch、unknown extension、hostile adapter、one-shot 和 outcome 闭集。P01-P04+P05-W01-W03 runtime 联合 `Ran 495, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy；`compileall -q src tests` 与 `git diff --check` 通过。
- 安全/隔离检查：token 只存在 P03 inbound payload、受控 parser local 与 single-use credential；adapter take 后立即删除局部引用，coordinator finally clear，普通 operation failure 在 supervised task返回前清除 traceback/context/cause。所有 request/parsed/result sensitive fields 均 repr=false 或固定 redacted repr；authority exact typed 后 detached copy，permissions 深度冻结。源码不导入 HTTP/global config/client/service locator/logger/metrics/audit、WebSocket、processor、DeliveryRecord/AckRecord/StateStore；test adapter不联网、不按 token 猜 authority，production adapter仅拒绝。
- 已知限制：P05 authority 只是 P06 前的注入合同和测试实现，不调用 backend IAM、不缓存、不提供权限失效。AuthenticatedHello 仍是握手临时结果；W04 才协商协议/capability并冻结 SC-1，W05以后才建立 logical/transport/path 映射和索引。
- 下一工作包：`P05-W04 protocol/capability negotiation and SessionContext`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W04

- 工作包：`P05-W04 protocol/capability negotiation and SessionContext`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，SC-1 进入增量冻结，下一游标为 P05-W05；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T14:17:46+08:00`。
- 修改文件：新增 `connection/session.py` 与 facade 导出，将可选 session negotiator 接入同一 handshake total deadline，扩展 fake transport capability 注入，新增 `tests/test_runtime_connection_session.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增 logical `LogicalSessionIdentity`、深度不可变 `SessionContext`、`NegotiatedSession`、immutable `CapabilityPolicy` 和 `HandshakeSessionNegotiator`。协议只由 ENV-1 `ProtocolCompatibilityMatrix` 选择；capability 只接受 requested、IAM authority、显式 P05 policy 以及 P04 adapter 权威 transport capability 的严格交集。SC-1 不含 transport/path ID 或对象、token、完整 hello/Envelope、完整 permissions、task/sink/client/callback；协商结果显式保存 selected protocol/schema/`json.v1` codec，状态只到 authenticated，不提前 active。
- 测试结果：W01-W04 connection 专项 `Ran 45, OK`；W04 10 项覆盖成功协商、IAM 不可提权、adapter transport 权威、P03 matrix 权威、未知 capability、schema binding、SC-1 exact field/frozen/slots/deep immutability、permission 脱离、logical/transport identity 分离和 policy immutability。P01-P04+P05-W01-W04 runtime 联合 `Ran 505, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy；`compileall -q src tests` 与 `git diff --check` 通过。
- 安全/隔离检查：协商失败统一在 active/index 前以 protocol classification 关闭；客户端声明不能增加 IAM/transport/protocol 权威。SessionContext 和 NegotiatedSession repr 不显示 logical ID、identity、tenant、capability、permission ref/digest；完整权限 mapping 不进入 SC-1。源码不按 transport type 分支，不导入 WebSocket driver、global config/client/service locator、processor、DeliveryRecord/AckRecord/StateStore，也未修改 P03/P04 冻结公共合同。
- 已知限制：SC-1 当前只冻结 SessionContext 与协商边界，logical/transport/path 绑定、索引、accepted、active、heartbeat、grace/resume、reauth、snapshot/audit 仍由 W05-W14 完成；普通生产连接仍由 P05 fail-closed adapter 拒绝。
- 下一工作包：`P05-W05 logical connection/transport session/network path mapping`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W05

- 工作包：`P05-W05 logical connection/transport session/network path mapping`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W06；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T14:23:24+08:00`。
- 修改文件：新增 `connection/binding.py` 与 facade 导出，新增 `tests/test_runtime_connection_binding.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增 P01-backed `LogicalSessionIdentityFactory`、冻结 `NetworkPathBinding`/`TransportSessionBinding`/`LogicalTransportMappingSnapshot` 和单 owner `LogicalConnectionTransportMap`。logical model 只复制 P04 frozen identity/capability/path value，不持有 TransportSession/WebSocket；path update、detach、transport replace 全部由实例锁原子化并有固定 fencing reason。path update 不改变 logical epoch；transport replace 保持 connection_id、强制新 session_id 与恰好下一 epoch。
- 测试结果：W05 专项 10 项与 W04 联合 `Ran 20, OK`，覆盖三层 identity、无 transport object、path migration/unsupported/identity substitution、explicit replace、connection/epoch fencing、detach、concurrent replace、peer digest 非 authority 和 P01 ID factory。P01-P04+P05-W01-W05 runtime 联合 `Ran 515, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy；`compileall -q src tests` 与 `git diff --check` 通过。
- 安全/隔离检查：mapping repr 隐藏全部 logical/transport/path ID、identity/tenant 和 address digest；peer/local 只接收 P04 有界摘要且不参与 IAM/authority。源码不导入 WebSocket driver/global config/client/service locator、processor、DeliveryRecord/AckRecord/StateStore，不修改 P03/P04 frozen contract，也未实现 resume authentication 或 active routing。
- 已知限制：W05 只建立 structural mapping 与 replacement fencing；W06 才建立单进程索引，W10/W11 才驱动 disconnect/resume lifecycle 和 IAM revalidation。SC-1 继续为 `IN_PROGRESS`。
- 下一工作包：`P05-W06 local atomic connection indexes`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W06

- 工作包：`P05-W06 local atomic connection indexes`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W07；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T14:28:06+08:00`。
- 修改文件：新增 `connection/index.py` 与 facade 导出，新增 `tests/test_runtime_connection_index.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增单进程 `LocalConnectionIndex`、冻结 `ConnectionIndexEntrySnapshot`/`LocalConnectionIndexSnapshot`。owner 锁内管理 connection/session/identity/tenant/component/capability/active-target 七类索引；每次 mutation 从 candidate entries 完整重建并在验证后一次 commit。duplicate connection/session 稳定拒绝，identity 多连接明确支持；state transition 与 target eligibility 同 owner 更新，closed 清除全部引用，session/authority context replacement 原子重建 secondary indexes。
- 测试结果：W06 专项 11 项，W04-W06 联合 `Ran 31, OK`，覆盖全索引查询、identity 多连接、duplicate/concurrent add、active/drain eligibility、grace-style suspend/restore、inactive restore rejection、closed cleanup、session/authority replace 和 deep immutable snapshot。P01-P04+P05-W01-W06 runtime 联合 `Ran 526, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy；`compileall -q src tests` 与 `git diff --check` 通过。
- 安全/隔离检查：所有公开集合 frozen 且 repr 隐藏 connection/session/identity/tenant/capability；没有 transport/path/peer、token、Envelope、permission mapping、第三方对象或 exception text。索引只存在显式实例，不是 global registry，不导入 StateStore/Redis/cache client/service locator、processor 或 delivery 类型。
- 已知限制：W06 只提供本地索引 owner；W07 accepted 成功后才允许首次 active，W09/W10/W11 分别驱动 drain/grace/resume 的 eligibility 变化。索引不具有跨进程/集群权威，SC-1 继续为 `IN_PROGRESS`。
- 下一工作包：`P05-W07 connection.accepted activation boundary`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W07

- 工作包：`P05-W07 connection.accepted activation boundary`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W08；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T14:32:10+08:00`。
- 修改文件：新增 `connection/accepted.py` 与 facade 导出，新增 `tests/test_runtime_connection_accepted.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增 frozen `AcceptedHeartbeatPolicy`、P03-based `ConnectionAcceptedEnvelopeBuilder` 和 one-shot `ConnectionAdmissionActivator`。accepted payload 精确白名单为 connection_id/session_id/protocol_version/heartbeat/session_expires_at/server_time/runtime_id/role，heartbeat 仅 interval/timeout；使用 SC-1 negotiated schema/codec、P01 message ID、Clock UTC、P03 registry validation 与 canonical serialization。只有 transport send success 后才从 authenticated 进入 active/index target；send failure/cancel 关闭并清理，close failure 保留 closing 可重试 owner。
- 测试结果：W07 专项 9 项，与 W06 联合 `Ran 20, OK`，覆盖 exact whitelist/registry、canonical negotiated codec、send-before-active、secret/authority/transport exclusion、hostile send failure、close retry、cancel rollback、one-shot/index fencing 和 heartbeat policy。P01-P04+P05-W01-W07 runtime 联合 `Ran 535, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy；`compileall -q src tests` 与 `git diff --check` 通过。
- 安全/隔离检查：serialized accepted 不含 token、identity、tenant、capability、permissions/ref/digest、transport/path/peer、server config 或 adapter response；Envelope 无 authority/delivery groups。第三方 send exception 不读取 str/repr/cause；cleanup failure不覆盖原 send/cancel，closed 不在真实 transport close 前发布。未调用 P03 feature-disabled processor，也未创建 ACK/DeliveryRecord/StateStore。
- 已知限制：W07 仅完成 initial admission；W08 提供 heartbeat，W09-W13 完成 drain/grace/resume/reauth。当前 production ordinary connection 仍 fail-closed，SC-1 继续 `IN_PROGRESS`。
- 下一工作包：`P05-W08 native and Envelope heartbeat`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W08

- 工作包：`P05-W08 native and Envelope heartbeat`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W09；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T14:37:46+08:00`。
- 修改文件：新增 `connection/heartbeat.py` 与 facade 导出，新增 `tests/test_runtime_connection_heartbeat.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增 frozen `HeartbeatPolicy`/`HeartbeatSnapshot`、typed outcome 和 `ConnectionHeartbeatService`。native 与 Envelope watchdog 是两个既有 TaskSupervisor 拥有的 Clock loop；native 只 P04 ping，Envelope 只接受 P03 heartbeat lifecycle Envelope，精确校验 connection/session/epoch/sequence并 canonical send heartbeat_ack。duplicate 无 ack/无 liveness refresh，out-of-order/stale fencing拒绝，deadline同 tick timeout 优先；active/draining 允许 health，timeout/native/send/cancel/shutdown 收敛 terminal close并取消另一 loop。
- 测试结果：W08 专项 11 项，与 W07 联合 `Ran 20, OK`，覆盖 exact lightweight ack、duplicate、out-of-order、session/epoch/connection fencing、draining health、native/envelope 分层、timeout task cleanup、native failure、deadline priority、shutdown idempotence 和 malformed/non-heartbeat。P01-P04+P05-W01-W08 runtime 联合 `Ran 546, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy；`compileall -q src tests`、`git diff --check` 与 heartbeat delivery/pipeline boundary scan 通过。
- 安全/隔离检查：heartbeat payload/ack 不含 token、authority、permission、tenant/identity、transport/path/peer 或 exception text；普通 heartbeat不调用 audit sink。源码不引用 processor、DeliveryRecord/AckRecord/StateStore/retry，不创建 thread/loop/supervisor/global service；task name只用本地 sequence且 terminal 后无 Clock waiter。
- 已知限制：W08 不实现普通业务 read loop或 P07 pipeline；W09 drain 只会保留显式 lifecycle/control/health allowlist，W10/W11 才处理 disconnect/resume。SC-1 继续 `IN_PROGRESS`。
- 下一工作包：`P05-W09 one-way bounded connection drain`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W09

- 工作包：`P05-W09 one-way bounded connection drain`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W10；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T14:45:30+08:00`。
- 修改文件：新增 `connection/drain.py` 与 facade 导出，新增 `tests/test_runtime_connection_drain.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增 frozen `DrainPolicy`/`DrainSnapshot`、P03 `ConnectionDrainEnvelopeHandler`、classification-only `DrainingMessageGate` 和 `ConnectionDrainService`。self drain Envelope必须无 target/payload等可变 scope；begin 原子 ACTIVE->DRAINING并摘除 target但不关 transport，重复 begin不延长 deadline且不可回 active。Clock/TaskSupervisor deadline、显式 complete和并发 terminal request first-wins，close failure/cancel保持 closing并可重试。
- 测试结果：W09 专项 12 项，与 W08 联合 `Ran 21, OK`，覆盖 one-way/no-immediate-close、idempotent begin、control/health/existing-response gate、complete、Clock timeout、close failure retry、cancel retry、concurrent terminal reason、non-active rejection、frozen snapshot、P03 self drain和 target/payload/type拒绝。P01-P04+P05-W01-W09 runtime 联合 `Ran 558, OK (skipped=1)`，唯一 skip 为 Windows event-loop policy；`compileall -q src tests`、`git diff --check` 与 delivery/state-store boundary scan通过。
- 安全/隔离检查：drain request不能指定其他 connection或携带 payload；snapshot/task name不含 logical/transport/tenant/identity ID或异常文本。gate只分类 registry message type，不调用 processor，不创建 DeliveryRecord/StateStore/transfer/retry；没有独立 thread/loop/supervisor/global owner。
- 已知限制：ACK/NACK/Defer 在 W09 仅保留 gate 语义，仍由 P12 实现；W09 不转移 pending delivery。W10/W11 才处理 disconnect grace/resume，SC-1 继续 `IN_PROGRESS`。
- 下一工作包：`P05-W10 supervised disconnect grace`，状态为 `IN_PROGRESS`；P06 保持 `NOT_STARTED`。

## P05-W10

- 工作包：`P05-W10 supervised disconnect grace`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W11；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T14:55:52+08:00`。
- 修改文件：新增 `connection/grace.py` 与 facade 导出，新增 `tests/test_runtime_connection_grace.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增 frozen `ReconnectGracePolicy`/`ReconnectGraceClaim`/`ReconnectGraceSnapshot`、phase enum 与 `ReconnectGraceService`。普通 active disconnect 默认30秒；先摘除 active target，再按 transport_session_id detach mapping，logical state/context最小保留但不持有旧 transport。typed resume refs可单次 claim，deadline同 tick expiry胜出；claim不恢复路由，W11必须先发布下一 epoch/index/mapping。expiry或early terminal清空 logical indexes。
- 测试结果：W10 专项 11 项，覆盖 default 30s/detach/non-target、duplicate disconnect、Clock expiry cleanup、single-use claim、deadline priority、reference mismatch、concurrent claim、early shutdown、complete ownership fencing、draining rejection和safe frozen snapshot。P01-P04+P05-W01-W10 runtime 联合 `Ran 569, OK (skipped=1)`，唯一 skip为Windows event-loop policy；`compileall -q src tests`、`git diff --check` 与 transport/global storage/task ownership scan通过。
- 安全/隔离检查：claim/snapshot repr不显示 logical IDs且不含 token/authority/permissions/Envelope/transport/path/peer；task name只用本地 sequence。grace不持有 TransportSession/WebSocket、不使用 real sleep/thread/new loop/new supervisor/global registry/StateStore/Redis/cache，不允许 grace connection继续普通 send。
- 已知限制：W10 只建立 grace与claim fencing；claimed resume的 IAM重验、capability协商、新 transport binding、epoch递增与旧 epoch拒绝由W11完成。claimed后失败/cancel须 fail-close，SC-1继续 `IN_PROGRESS`。
- 下一工作包：`P05-W11 IAM-revalidated resume and epoch fencing`，状态为 `IN_PROGRESS`；P06保持 `NOT_STARTED`。

## P05-W11

- 工作包：`P05-W11 IAM-revalidated resume and epoch fencing`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W12；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T17:18:57+08:00`。
- 修改文件：新增 `connection/resume.py` 与 facade 导出，新增 `tests/test_runtime_connection_resume.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增 frozen `ResumedConnection`/`EpochValidation`、`ConnectionResumeCoordinator` 与 `ConnectionEpochGate`。resume先typed claim grace，再使用显式IAM adapter消费新token并重验旧/new eligibility、TTL、identity、tenant、component_type，重新执行protocol/capability/transport negotiation；保持connection_id，P01新session_id，epoch严格+1。新mapping/index先non-target，canonical accepted send后才restore active；所有失败关闭candidate与claimed logical。
- 测试结果：P05-W01-W11 connection联合 `Ran 120, OK`；W11专项11项覆盖成功全链、identity/tenant/component mismatch、old/new resume eligibility、capability不可提权、total deadline、cancel、accepted send failure、concurrent resume、旧epoch普通/ACK/NACK/Defer fencing、invalid refs不消费grace与token/old transport隔离。P01-P04+P05-W01-W11 runtime联合 `Ran 580, OK (skipped=1)`，唯一skip为Windows event-loop policy；`compileall -q src tests`、`git diff --check`与delivery/processor/storage/network boundary scan通过。
- 安全/隔离检查：resume token沿用single-use credential并在所有路径clear；supervised failure出task前清除traceback/context/cause，repr不含token/logical IDs/authority。candidate loser/timeout/cancel均关闭；旧transport无mapping，旧epoch在任何未来delivery path前拒绝。源码不调用HTTP/global config/service locator、不创建P06 backend或processor/DeliveryRecord/AckRecord/StateStore。
- 已知限制：W11仍使用显式offline test IAM或production fail-closed adapter，不宣称P06真实IAM。不可恢复关闭/audit、reauth与最终safe snapshot分别由W12-W14完成，SC-1继续 `IN_PROGRESS`。
- 下一工作包：`P05-W12 non-resumable security close`，状态为 `IN_PROGRESS`；P06保持 `NOT_STARTED`。

## P05-W12

- 工作包：`P05-W12 non-resumable security close`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W13；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T17:23:52+08:00`。
- 修改文件：新增 `connection/security.py` 与 facade 导出，增强 resume 对 indexed revocation 的权威检查，新增 `tests/test_runtime_connection_security.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增五项 `NonResumableCloseKind`、固定 close/public-error decision、单向 `NonResumableConnectionGuard`、frozen snapshot，以及显式async `ConnectionSecurityAuditSink`/typed event/test sink。guard先原子替换indexed context撤销resume，再执行first-classification-wins close；grace close取消deadline，close failure/cancel保持closing可重试。W11 claim后再次检查indexed current session/epoch/resume eligibility，revocation不可被旧context绕过。
- 测试结果：W12专项9项，W09-W12联合 `Ran 43, OK`，覆盖五类close/public/audit一致映射、close完成前revocation、grace安全关闭、audit failure隔离、重复幂等、cancel+retry、安全event脱敏、普通disconnect不误标和显式sink/frozen snapshot。P01-P04+P05-W01-W12 runtime联合 `Ran 589, OK (skipped=1)`，唯一skip为Windows event-loop policy；`compileall -q src tests`、`git diff --check`与敏感字段/global audit/storage边界scan通过。
- 安全/隔离检查：API根本不接收attacker payload/token/peer/free-text reason；event只保存fixed enum、connection digest、component/epoch/time，不含raw ID/transport/exception。ordinary audit failure不放行安全操作、不阻止close、不覆盖cancel；无global sink、不声称P07/P08 durability。普通network disconnect保持resumable且无security event。
- 已知限制：W12 audit仅为typed注入边界与deterministic test sink，不是强一致持久审计。W13实现reauth/expiry，W14聚合最终safe snapshot/audit接口，SC-1继续 `IN_PROGRESS`。
- 下一工作包：`P05-W13 reauth and session expiry policy`，状态为 `IN_PROGRESS`；P06保持 `NOT_STARTED`。

## P05-W13

- 工作包：`P05-W13 reauth and session expiry policy`。
- 状态：`VERIFIED`；P05 保持 `IN_PROGRESS/F1`，下一游标为 P05-W14；P06 保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T17:34:55+08:00`。
- 修改文件：新增 `connection/reauth.py` 与 facade 导出，收紧 P03 reauth request/response schema，增强 local index authority replacement fencing，新增 `tests/test_runtime_connection_reauth.py`，更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：新增 frozen `SessionExpiryPolicy`/`SessionExpirySnapshot`/`ParsedReauth`/`ReauthenticatedSession`、P03 `ConnectionReauthEnvelopeHandler`/`ReauthEnvelopeBuilder`、one-shot `ConnectionReauthCoordinator` 与 supervised `SessionExpiryController`。reauth保持logical connection/session/epoch，显式IAM重验identity/tenant/component/TTL并重新协商capability；accepted成功后以old context/state CAS发布新不可变authority，draining保持non-target。deny/timeout/mismatch/capability/send/publish/cancel均fail-close；absolute expiry先撤销target再close，close failure可retry。
- 测试结果：W13专项12项，P03 registry/index/session/drain/grace/resume/security/reauth联合 `Ran 82, OK`，覆盖exact Envelope/authority forgery、token脱敏、成功续期、权限收缩与draining、capability越权、identity/tenant/component/expired authority、deny前撤销target、total deadline、cancel、accepted send failure、lead/expiry、generation refresh和close retry。P01-P04+P05-W01-W13 runtime联合 `Ran 601, OK (skipped=1)`，唯一skip为Windows event-loop policy；`compileall -q src/ns_runtime/connection src/ns_runtime/protocol`与`git diff --check`通过。
- 安全/隔离检查：token只进入single-use credential且所有路径clear；request/result/repr/response不含token、identity、tenant、permission snapshot/digest、transport/path/peer或异常文本。rejected发送前index已closing/non-target，权限更新使用expected-old-context fencing；expiry只读取exact indexed context。源码不缓存credential、不访问HTTP/global config/service locator、不创建P06 backend/client、processor/DeliveryRecord/AckRecord/StateStore、thread/new loop/new supervisor或global registry。
- 已知限制：W13复用显式offline test IAM或production fail-closed adapter，不实现后台凭证续期或P06网络IAM。W14仍需聚合最终async safe session snapshot与resume/kick/security close/reauth rejection强审计接口；当前W12 sink不代表durable audit，SC-1继续 `IN_PROGRESS`。
- 下一工作包：`P05-W14 async safe session snapshot and audit aggregation`，状态为 `IN_PROGRESS`；P06保持 `NOT_STARTED`。

## P05-W14

- 工作包：`P05-W14 async safe session snapshot and audit aggregation`。
- 状态：`VERIFIED`；P05-W01至W14全部 `VERIFIED`，P05阶段出口为 `VERIFIED/F3`，`SC-1 VERIFIED`；P06-B01/P06-R01及其余P06工作包保持 `NOT_STARTED`。
- 完成时间：`2026-07-21T17:50:28+08:00`。
- 修改文件：新增 `connection/audit.py`、`connection/snapshot.py` 与 facade 导出；将typed lifecycle audit显式接入resume、reauth rejection和non-resumable guard；新增 `tests/test_runtime_connection_snapshot_audit.py`；更新 implementation plan、acceptance log 与 ADR-030并冻结P05/SC-1。
- 公共契约变化：新增五项有限 `ConnectionCapabilityClass`、frozen `SafeConnectionSnapshot`与async `SafeConnectionSnapshotReader`；reader只输出logical ID摘要、state/close/target、component/epoch/protocol、有限capability classification及heartbeat/grace/drain/reauth/security safe view，并以index mutation sequence进行最多三次有界coherence retry。新增五项`ConnectionAuditKind`、fixed outcome/strong-required marker、frozen typed event/snapshot、显式sink/test sink和`ConnectionLifecycleAuditBoundary`；strong-required只预留P07/P08合同，不声明durability。
- 测试结果：W14专项10项，覆盖exact frozen字段、嵌套lifecycle view、drain/security终态、敏感字段零泄漏、并发authority mutation coherence retry、hostile snapshot source failure、resume success/rejection audit、reauth rejection、kick/security/policy映射、audit failure隔离及ordinary heartbeat零audit。P05 connection联合 `Ran 151, OK`；P01-P05 runtime联合 `Ran 611, OK (skipped=1)`；backend根目录全量 `Ran 622, OK (skipped=32)`；两套`pip check`、`compileall -q src tests`和`git diff --check`通过。
- 安全/隔离检查：snapshot/event字段白名单和repr扫描均不含raw connection/session ID、identity、tenant、完整capability、permission ref/digest/mapping、token/Authorization/credential、Envelope/payload/auth_context、transport/path/peer、WebSocket或异常文本。reader/sink普通失败不读取str/repr；无global sink、StateStore/Redis/cache、HTTP/backend client、processor/DeliveryRecord/AckRecord、thread/new loop/new supervisor。heartbeat服务未注入audit boundary且事件为零。
- 已知限制：safe snapshot是单进程异步observational view，不是P08持久状态或集群权威；coherent只表示读取窗口内local index mutation sequence稳定。typed audit只表达strong-required handoff，deterministic test sink不持久、不证明exactly-once；P07/P08仍须实现processor final audit和durable强一致存储。P06真实IAM client/backend合同未开始，ordinary production connection继续fail-closed。
- 下一工作包：`P06-B01 runtime IAM principal contract`，状态保持 `NOT_STARTED`；本目标在P05阶段出口停止，不开始P06。

## P05-FIX-01

- 工作包：`P05 logical ingress、processor、protocol activation 与 handshake rejection 校准`。
- 状态：`VERIFIED`；P05 阶段出口恢复为 `VERIFIED/F3`，`SC-1 VERIFIED`；P06-B01/P06-R01 保持 `NOT_STARTED`。
- 开始时间：`2026-07-21`。
- 完成时间：`2026-07-21T18:59:32+08:00`。
- 触发原因：P05-W01至W14领域组件已经实现，但 P03 canonical registry 仍将 connection lifecycle contracts 标为 feature disabled；heartbeat/drain/reauth wire validation 和 executable entry 仍散落在 connection handlers，P04 transport listener 尚未通过明确 logical owner 接入 P05 accept/read loop，合法 hello 的安全 rejected response 也未形成统一 canonical builder。
- 历史边界：P03 acceptance 当时记录的 connection feature disabled 是真实历史事实，不回写或改写；本 FIX 只追加 P05 正式激活对应 contracts 的后续阶段事实。P05-W01至W14实现不回滚，P06/P07/P08及 delivery/routing/cluster 边界不启动。
- 修改文件：更新 P03 protocol registry/schema/facade 与 P05 hello/authentication/heartbeat/reauth facade；新增 `connection/processors.py`、`connection/rejected.py`、`connection/lifecycle.py`；将 logical owner 接入 `main.py`、transport lifecycle、RSD-1 shutdown；新增 processor/rejected/真实 composition 测试并校准 protocol/main/shutdown/heartbeat 测试；更新 implementation plan、acceptance log、ADR-028 与 ADR-030。
- canonical feature/disabled matrix：同一 `BUILTIN_MESSAGE_REGISTRY` 正式 enabled `connection.hello/accepted/rejected/reauth/reauth_accepted/reauth_rejected/heartbeat/heartbeat_ack/drain`，并以 direction 明确 inbound/outbound；上述 9 项不再进入 `build_feature_disabled_processors()`，disabled 数量由49降至40。P06+、task、delivery、stream、control、cluster等未实现类型继续统一fail-closed；heartbeat、self drain、reauth的required capabilities为空，不与authenticated-session lifecycle规则冲突。
- exact schema：hello仅允许token/component_type/requested_version、可选min_version/requested_capabilities与exact `ns.connection_resume`；heartbeat精确要求connection_id/session_id/connection_epoch/sequence/sent_at，ack以server_time替代sent_at；drain禁止target/payload/route/delivery/stream/callback与extensions；accepted/rejected/reauth request/response均冻结既有字段白名单。missing/extra payload、非法hello group/extension和带target/payload drain均在`registry.validate_envelope()`失败，领域service不再拥有第二wire schema authority。
- processor合同：不可变`ConnectionLifecycleProcessorRegistry`只按canonical `processor_key`一一调度heartbeat/drain/reauth；processor接收P03 validated Envelope，执行current session/epoch/state/security hard check后调用明确service并构造canonical response。Handler仅保留兼容包装，不是composition执行入口；transport callback没有direct-action bypass，未建立P07 generic pipeline、permission/rate-limit/routing/final audit、DeliveryRecord或ACK状态。
- rejected规则：统一builder只发送reason/server_time/retryable低基数字段。合法hello的protocol/minimum/capability、IAM、authority拒绝在transport和response protocol安全时通过既有Clock/TaskSupervisor有界best-effort先发`connection.rejected`再close；protocol incompatible真实loopback证明客户端先收到rejected再关闭。malformed hello或不安全transport直接close；send失败不覆盖原failure、不发布binding/index/ACTIVE，payload不含token/identity/tenant/capability/IAM/permission/peer/transport ID/异常文本。
- composition与lifecycle：`ConnectionLifecycleManager`显式拥有per-adapter supervised accept loop及ACTIVE read loop，依赖TransportManager、LocalConnectionIndex、Clock、既有TaskSupervisor、IdentifierFactory、IAM、P03 registry/codec、processor factory与policy。initial/resume链完成hello-first、IAM、negotiation、SC-1、binding/index、accepted、ACTIVE；read链完成P03 validation、current session/epoch gate、processor dispatch，disabled类型返回标准runtime.error。RSD-1顺序已校准为stop transport admission、stop logical admission/read、drain/close logical、drain/close transport、TaskSupervisor与下游资源，不新增owner/loop/signal/coordinator/listener。
- IAM与loopback：production composition默认且显式构造`FailClosedHandshakeIamAdapter`；测试必须显式注入`DeterministicTestIamAdapter`，没有token字符串推断或allow-all。真实`WebSocketTcpAdapter` plaintext覆盖hello/accepted/ACTIVE/heartbeat_ack/disabled error/drain/close；TLS覆盖hello/accepted/ACTIVE并以canonical drain完成安全关闭。production hello收到固定IAM denied rejected且从未ACTIVE。
- resume/epoch/reauth：真实loopback覆盖普通断线立即non-target、30秒grace、resume hello、IAM重验、新session与epoch+1、accepted/ACTIVE、旧epoch runtime.error并close；reauth成功保持logical session并原子替换authority/index，拒绝返回`connection.reauth_rejected`后fail-close。取消/失败清理candidate transport、mapping/index与supervised heartbeat/expiry/read/grace任务，无双active或stale session。
- 测试结果：P03 `Ran 54, OK`；P04 `Ran 59, OK`；P05 `Ran 163, OK`；P03+P04+P05联合`Ran 276, OK`；runtime环境按DEP-1排除未安装Django的`test_cache`后P01-P05全量`Ran 626, OK (skipped=1)`；backend根目录全量`Ran 637, OK (skipped=39)`。runtime/backend `pip check`、`compileall -q src tests`、`git diff --check`通过；TLS专项在warnings/tracemalloc模式正常关闭且无unclosed transport warning。
- 安全/隔离检查：canonical rejected/schema/processor路径不读取或记录token、payload、IAM raw或底层异常文本；源码边界扫描未新增backend IAM HTTP/RPC client、permission cache、P07 generic processor pipeline、StateStore、RoutingPlan、DeliveryRecord、Ack/Nack/Defer、retry/dead-letter或cluster coordination。P06仍为`NOT_STARTED`。
- 已知限制：P05 processor只处理connection lifecycle，不是P07通用pipeline；production IAM在P06前必然拒绝ordinary connection；P05 local index/snapshot/audit不是P08 durable或cluster authority。`P06-B01/P06-R01`继续暂停且`NOT_STARTED`。

## P05-FIX-02

- 工作包：`logical composition lifecycle regression hardening`。
- 状态：`VERIFIED`；P05 阶段出口恢复为 `VERIFIED/F3`，`SC-1 VERIFIED`；P06-B01/P06-R01 保持 `NOT_STARTED`。
- 开始时间：`2026-07-21`。
- 完成时间：`2026-07-21`。
- 触发原因：P05-FIX-01 已完成的 registry/schema/processor/rejected/composition 边界保持不变；本 FIX 只校准 composition 暴露的 hello semantic parse cleanup、persistent drain、retryable close ownership、single total handshake deadline 与 IAM supervised outcome/credential traceback 安全。
- 历史边界：不改写 P05-FIX-01 本地验收记录，不启动 P06 IAM HTTP/RPC、P07 generic pipeline、P08 StateStore、RoutingPlan、DeliveryRecord、ACK/NACK/Defer state 或 cluster。
- 修改文件：新增 `connection/deadline.py` 并更新 connection facade、hello receiver、authenticator、drain service、lifecycle manager、processor/rejected best-effort task；扩展 authentication/composition/rejected 测试；更新 implementation plan、acceptance log 与 ADR-030。
- 公共契约变化：`HandshakeDeadlineBudget` 以一次 absolute monotonic deadline 贯穿 hello receive、semantic parse、IAM 与 negotiation。HelloClaimParser semantic failure 保持 credential finally clear，并通过同一 receiver 将 candidate logical state 收敛至 CLOSING，只有 bounded transport close 成功后才发布 CLOSED。`connection.drain` processor 只执行 ACTIVE->DRAINING，立即摘除 target但保留 read loop；heartbeat/reauth及当前允许 control 可继续进入，重复 drain 不重置 deadline，timeout或显式 manager/shutdown completion 才关闭。
- cleanup ownership：manager close 先发布 CLOSING，再等待 P04 transport close；普通 failure 返回 false并保留 index/owner，CancelledError 原样穿透且同样保留，`retry_cleanup()` 或并发 shutdown 后续成功才发布 CLOSED并删除 index/owner。drain timeout 的 successful close 通过 supervised completion watcher通知唯一 manager owner回收；close失败时 watcher保持等待而不伪造 CLOSED。
- IAM/sensitive outcome：composition 的 IAM supervised operation 捕获普通 deny/timeout/unavailable/hostile exception，清除 traceback/context/cause并返回无 credential 的 typed outcome；外层再映射固定错误，CancelledError保持原语义。canonical rejected best-effort send 同样把普通 send failure转为正常 bool outcome，避免 expected handshake rejection污染 TaskSupervisor failures或 shutdown report。
- 新增测试：真实 WebSocket semantic hello matrix覆盖 unsupported component、requested/protocol mismatch、min mismatch、invalid/duplicate capability、invalid resume refs并断言无 transport/task/HANDSHAKING/index/mapping泄漏；真实 plaintext drain验证保持open、DRAINING/non-target、draining heartbeat ack、duplicate deadline不延长及deadline/显式shutdown有界完成；manager级覆盖 close ordinary failure、原 CancelledError穿透、retry cleanup和concurrent shutdown；ControlledClock证明T=10、hello在9.5、IAM需要超过0.5时总时长止于约10；hostile IAM在credential.take前抛错仍清凭证且supervisor/report无token与logical-iam failed task。
- 回归结果：P03 `Ran 54, OK`；P04 `Ran 59, OK`；P05 `Ran 169, OK`；P03+P04+P05联合`Ran 282, OK`；runtime环境按DEP-1排除未安装Django的`test_cache`后P01-P05全量`Ran 632, OK (skipped=1)`；backend根目录全量`Ran 643, OK (skipped=44)`，其中新增5个真实WebSocket composition用例在backend环境按可选依赖边界skip、已在runtime环境真实执行通过。runtime/backend `pip check`、两套`compileall -q src tests`、`git diff --check`通过；TLS专项在ResourceWarning/tracemalloc模式正常关闭。
- 安全/隔离检查：9项P05 connection contracts继续enabled且direction不变，余40项继续由disabled processor matrix fail-closed；P03 exact schema、lightweight processor、canonical rejected、FailClosedHandshakeIamAdapter、plaintext/TLS/resume epoch+1/old epoch fencing/reauth/SC-1均未回退。源码未新增P06 backend IAM client/permission cache、P07 generic pipeline、P08 StateStore、RoutingPlan、DeliveryRecord、ACK/NACK/Defer状态、retry/dead-letter或cluster。
- 已知限制：P05 processor仍仅处理connection lifecycle；production ordinary hello在P06前继续fail-closed；local index/snapshot/audit不宣称durable或cluster authority。
- 下一工作包：`P06-B01/P06-R01`继续暂停且为`NOT_STARTED`，等待新的显式恢复指令。

## P05-FIX-03

- 工作包：`pre-index candidate cleanup ownership + draining terminal convergence`。
- 状态：`VERIFIED`；P05 阶段出口恢复为 `VERIFIED/F3`，`SC-1 VERIFIED`；P06-B01/P06-R01 保持 `NOT_STARTED`。
- 开始时间：`2026-07-21`。
- 完成时间：`2026-07-21`。
- 触发原因：P05-FIX-02 保留了 indexed close retry ownership，但 semantic/pre-index/IAM rejection/unknown resume candidate 的 close ordinary failure仍可能随 admission task结束而丢失 owner；同时heartbeat、reauth、expiry等DRAINING外部终态尚未同步DrainService first-reason、deadline与completion watcher。
- 历史边界：不改写P05-FIX-01/P05-FIX-02本地验收记录，不回滚single handshake budget、IAM typed outcome、persistent drain、registry/schema/processor/composition；不启动P06+能力。
- 修改文件：更新`connection/lifecycle.py`、`handshake.py`、`resume.py`建立manager-owned pre-index candidate cleanup；更新`drain.py`、`heartbeat.py`、`reauth.py`统一external terminal observation/finalization；扩展authentication/handshake/composition/heartbeat/reauth测试；更新implementation plan、acceptance log与ADR-030。
- candidate cleanup owner：每次admission在receive前按manager-local递增sequence登记`_CandidateCleanupOwner`，仅持有candidate transport、logical state machine、fixed terminal reason与cleanup lock，不进入LocalConnectionIndex、不创建mapping/ACTIVE、不暴露transport ID/peer/token。receiver terminal完成后manager核对CLOSED并释放；首次close普通失败保留CLOSING record，CancelledError原对象穿透并同样保留；`retry_pending_candidate_cleanup()`与manager drain再次真实close，成功后才CLOSED并删除record。resume coordinator通过显式注入terminator把candidate close交回同一manager owner，避免内部固定次数retry。
- draining terminal convergence：`ConnectionDrainService.observe_external_terminal()`在外部owner关闭前以单锁冻结first reason、同步DRAINING->CLOSING并取消deadline；`finalize_external_terminal()`只在index已由真实close清除后设置completion signal。heartbeat timeout/native/send terminal、reauth rejection、session expiry和manager protocol/shutdown均复用该边界；close failure/cancel时reason保留且watcher继续持有cleanup，retry成功后立即收敛。后续DRAIN_TIMEOUT/SHUTDOWN不能覆盖DrainSnapshot、state machine或index已发布的首因。
- 新增测试：fake transport覆盖semantic parse、malformed receiver、IAM deny、unknown resume的首次close failure，以及candidate close cancellation原对象与retry/drain释放；resume pre-publish failure验证显式candidate terminator只调用一次且不做固定retry；真实WebSocket覆盖DRAINING+reauth deny的AUTH_FAILED close、close首次失败后owner/watcher保留与retry；ControlledClock覆盖DRAINING+heartbeat timeout和DRAINING+session expiry，均验证deadline取消、首因不被推进时钟后的DRAIN_TIMEOUT覆盖、无`logical-drain-*` stale task。成功admission、production fail-closed与semantic real loopback另断言candidate collection归零。
- 回归结果：P03 `Ran 54, OK`；P04 `Ran 59, OK`；P05 `Ran 179, OK`；P03+P04+P05联合`Ran 292, OK`；runtime环境按DEP-1排除未安装Django的`test_cache`后P01-P05全量`Ran 642, OK (skipped=1)`；backend根目录全量`Ran 653, OK (skipped=46)`，新增2个真实WebSocket交叉用例在backend环境按可选transport依赖边界skip、已在runtime环境真实执行通过。runtime/backend `pip check`、两套`compileall -q src tests`、`git diff --check`通过；TLS专项在ResourceWarning/tracemalloc模式正常关闭。
- 安全/隔离检查：9项P05 lifecycle contract继续enabled，余40项disabled；single HandshakeDeadlineBudget、IAM typed outcome与traceback清理、expected rejected cleanliness、persistent drain、exact P03 schema、lightweight processor、canonical rejected、production fail-closed IAM、SC-1、resume epoch+1/old epoch fencing均未回退。源码边界扫描未新增P06 client/cache、P07 generic pipeline、P08 StateStore、RoutingPlan、DeliveryRecord、ACK/NACK/Defer state或cluster。
- 已知限制：candidate collection仅为单进程pre-index transport cleanup ownership，不是正式connection index、durable state或cluster authority；P05 processor仍仅处理connection lifecycle。
- 下一工作包：`P06-B01/P06-R01`继续暂停且为`NOT_STARTED`，等待新的显式恢复指令。

## P05-FIX-04

- 工作包：`resume post-commit ownership handoff cancellation hardening`。
- 状态：`VERIFIED`；P05 阶段出口恢复为 `VERIFIED/F3`，`SC-1 VERIFIED`；P06-B01/P06-R01 保持 `NOT_STARTED`。
- 开始/完成时间：`2026-07-21`。
- 触发原因：resume coordinator 已经发布新 mapping、SessionContext/index、accepted、ACTIVE target并完成旧 grace，但manager在candidate → logical owner正式交接前仍有旧expiry stop、candidate辅助状态迁移与owner activation等取消点，可能形成ACTIVE index指向已被candidate cleanup关闭的新transport。
- 历史边界：只追加P05-FIX-04，不改写或回滚P05-FIX-01/P05-FIX-02/P05-FIX-03的registry/schema/processor/rejected/composition、indexed/pre-index cleanup与draining terminal验收事实，不启动P06+能力。
- 修改文件：更新`connection/lifecycle.py`建立resume post-commit同步handoff barrier与logical fail-close；扩展真实WebSocket composition竞态测试；更新implementation plan、acceptance log与ADR-030。
- ownership transfer barrier：`ConnectionResumeCoordinator.resume()`成功返回后先同步保存旧expiry，构造新grace，并把新context/transport/grace写入既有`_LogicalOwner`；同一无await段设置`resume_handoff_pending_activation`并删除candidate cleanup record。下一个await发生时新transport已只属于logical owner，candidate state machine不再通过异步辅助迁移参与资源ownership。
- post-commit fail-close：旧expiry stop、heartbeat/expiry/read startup或shutdown的普通失败/取消都按logical owner处理，先使ACTIVE target失效并进入CLOSING，再真实关闭transport。CancelledError保持原对象语义；cleanup期间普通close failure不覆盖原取消，index保持CLOSING、logical owner与handoff marker保留、candidate count保持0，后续`retry_cleanup(connection_id)`成功才发布CLOSED并删除index/owner。
- 新增测试：真实WebSocket确定性事件屏障覆盖coordinator已发送accepted且index epoch+1/ACTIVE后阻塞旧expiry.stop再取消admission；同场景close首次失败验证CLOSING logical-only retry ownership；真实`_activate_owner`完成heartbeat/expiry/read启动后注入failure验证fail-close并无stale task；正常resume继续验证connection_id不变、session_id变化、epoch+1、heartbeat/read owner运行且candidate collection为0。
- 回归结果：指定resume/composition/grace/authentication/drain/reauth/heartbeat联合`Ran 96, OK`；P03 `Ran 54, OK`；P04 `Ran 59, OK`；P05 `Ran 182, OK`；P03+P04+P05联合`Ran 295, OK`；runtime环境按DEP-1排除未安装Django的`test_cache`后P01-P05全量`Ran 645, OK (skipped=1)`；backend根目录全量`Ran 656, OK (skipped=49)`，新增3个真实WebSocket竞态用例在backend环境按可选transport依赖边界skip、已在runtime环境真实执行通过。runtime/backend `pip check`、两套`compileall -q src tests`、`git diff --check`通过；plaintext/TLS real loopback、resume epoch+1/old epoch fencing/reauth继续通过。
- 安全/隔离检查：P05-FIX-03 candidate close retry/cancel与DRAINING first-reason/deadline convergence专项全部通过；9项P05 lifecycle contract、40项disabled、single HandshakeDeadlineBudget、IAM typed outcome/traceback cleanup、exact P03 schema、lightweight processor、canonical rejected、production fail-closed IAM、SC-1均未回退。源码未新增P06 backend IAM client/cache、P07 generic pipeline、P08 StateStore、RoutingPlan、DeliveryRecord、ACK/NACK/Defer state或cluster。
- 已知限制：handoff marker与candidate collection均为单进程P05 cleanup ownership，不是durable/cluster ownership；P05 processor仍仅处理connection lifecycle。
- 下一工作包：`P06-B01/P06-R01`继续暂停且为`NOT_STARTED`，等待新的显式恢复指令。

## 新记录模板

- 工作包：
- 状态：
- 完成时间：
- 修改文件：
- 公共契约变化：
- 测试结果：
- 安全/隔离检查：
- 已知限制：
- 下一工作包：
