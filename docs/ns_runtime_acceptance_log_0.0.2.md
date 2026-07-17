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
