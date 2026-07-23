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

## P06 IAM、安全上下文与 backend 合同验收证据

- 工作包：`P06-B01` 至 `P06-B08`、`P06-R01` 至 `P06-R08`。
- 状态：`VERIFIED`；P06 仅完成既有实现的证据补验，未扩展 P06 范围，未开始 P07/P08/P09/P10。
- 验收目标：补齐认证、授权、权限版本/缓存、backend 不可用降级、恢复重验与敏感信息保护的真实负向/安全证据；本记录不修改生产代码或测试代码。
- 执行日期：`2026-07-22`；完成时间：`2026-07-22T08:09:26+08:00`。
- 执行环境：Ubuntu `22.04.5 LTS`、WSL2 kernel `6.18.33.2-microsoft-standard-WSL2`、`x86_64`；backend/runtime 均为 Python `3.10.12`（GCC `11.4.0`），解释器分别为 `/home/ns/.virtualenvs/ns_backend/bin/python`、`/home/ns/.virtualenvs/ns_runtime/bin/python`。
- 修改文件：仅本验收日志 `docs/ns_runtime_acceptance_log_0.0.2.md`；无公共契约变化，无生产代码/测试代码变化。

### 实际测试命令与结果

1. backend 环境 P06 认证与 client 专项：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest -v tests.test_backend_runtime_iam tests.test_runtime_iam_client
   ```

   结果：`Ran 11 tests in 0.056s`，`OK`；失败 `0`，跳过 `0`。

2. backend 环境 P06 authorization 专项：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest -v tests.test_runtime_iam_authorization
   ```

   结果：`Ran 6 tests in 0.010s`，`OK`；失败 `0`，跳过 `0`。

3. backend 环境 P06 credential/recovery 专项：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest -v tests.test_runtime_iam_credential_recovery
   ```

   结果：`Ran 3 tests in 0.028s`，`OK`；失败 `0`，跳过 `0`。

4. backend 环境 P06 四模块联合：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest -v tests.test_backend_runtime_iam tests.test_runtime_iam_client tests.test_runtime_iam_authorization tests.test_runtime_iam_credential_recovery
   ```

   结果：`Ran 20 tests in 0.074s`，`OK`；失败 `0`，跳过 `0`。

5. runtime 环境初次全量执行：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest discover -s tests -p 'test_*.py'
   ```

   结果：`Ran 666 tests in 23.808s`，`FAILED (errors=3, skipped=1)`。其中一项为 runtime 环境按 DEP-1 不安装 Django 而无法导入 `test_cache`；另两项 P06 credential cache 错误由 runtime 虚拟环境缺少 requirements 已声明的 `cryptography` 引起。记录为 `ENVIRONMENT FIX REQUIRED（已解决）`，不是实现缺陷。

6. runtime 环境依赖纠正：

   ```bash
   /home/ns/.virtualenvs/ns_runtime/bin/python -m pip install -r requirements-runtime.txt
   ```

   结果：安装 `cffi-2.1.0`、`cryptography-49.0.0`、`pycparser-3.0`；其余声明依赖已满足，未修改仓库文件。

7. runtime 环境纠正后 P06 四模块联合：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest -v tests.test_backend_runtime_iam tests.test_runtime_iam_client tests.test_runtime_iam_authorization tests.test_runtime_iam_credential_recovery
   ```

   结果：`Ran 20 tests in 0.063s`，`OK`；失败 `0`，跳过 `0`。

8. backend 根目录全量回归：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest discover -s tests -p 'test_*.py'
   ```

   结果：`Ran 676 tests in 20.228s`，`OK (skipped=49)`；失败 `0`。verbose 复核为 `Ran 676 tests in 19.439s`、`OK (skipped=49)`；49 项中 1 项为 Windows event-loop policy，48 项因 backend 环境按 DEP-1 不安装 runtime transport 可选依赖 `websockets` 而跳过；P06 的 20 项全部真实执行且无跳过。

9. runtime 边界正确的全量回归（按 DEP-1 排除 Django-only `test_cache`）：

   ```bash
   set -o pipefail
   rg --files tests -g 'test_*.py' -g '!test_cache.py' | sort | sed 's#/#.#g; s#\.py$##' | xargs env PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest
   ```

   结果：`Ran 665 tests in 23.474s`，`OK (skipped=1)`；失败 `0`，唯一跳过项为 Windows event-loop policy。被排除的 `test_cache` 共 11 项，已由含 Django 的 backend 全量回归真实执行。

10. 环境与静态有效性复核：

    ```bash
    /home/ns/.virtualenvs/ns_runtime/bin/python -m pip check
    /home/ns/.virtualenvs/ns_backend/bin/python -m pip check
    /home/ns/.virtualenvs/ns_backend/bin/python -m compileall -q src tests
    git diff --check
    ```

    结果：两套环境均为 `No broken requirements found.`；`compileall` 与 `git diff --check` 成功且无输出。

### IAM 负向与安全证据

- A/认证失败：有效 credential 可建立 authority；无效、过期、撤销、签名篡改和密文篡改全部 fail-closed；异常类别稳定为 `RUNTIME_IAM_DENIED`、`RUNTIME_IAM_UNAVAILABLE`、`RUNTIME_IAM_TIMEOUT`。credential 为 single-use，拒绝后已清除。
- B/主体与越权：`frontend_user`、`backend_service`、`client`、`node`、`runtime_node`、`management` 六类主体均覆盖；客户端伪造 `component_type`、请求超出 IAM 裁决的 capability、tenant 不一致及跨 tenant target 均拒绝，客户端自报不能提权。
- C/权限版本：permission version mismatch、stale snapshot、`refresh_required` 与 invalidation 均触发刷新或拒绝，不沿用过期授权；实测 `refresh_required` 固定映射为 `RUNTIME_IAM_DENIED/permission_refresh_required`。
- D/缓存：覆盖 cache hit、TTL 到期、版本失效与 stale snapshot；缓存仅保存最小 `PermissionSnapshot`/decision，不保存原始 IAM 返回体。
- E/backend 不可用：strict 模式对 timeout、5xx、malformed response 与 unavailable 全部 fail-closed；缓存模式仅允许 snapshot current 的低风险操作，高风险控制、跨 tenant、新配置、全局协调写入四类全部固定拒绝。
- F/恢复重验：backend 恢复后对 `credential_valid`、`role_valid`、`config_valid`、`lease_valid`、`fencing_valid`、`session_snapshot_valid` 六项逐项重验，任一为 false 均 `RUNTIME_IAM_DENIED`，不会自动沿用旧授权；该合同不实现 P08 lease/fencing 持久权威。
- 敏感信息：token、内部 service credential 不进入 `repr`、异常文本、日志/audit sink 或返回体；credential cache 只保存 AES-GCM 密文并保持内存边界，无明文落盘路径；普通 Envelope 只注入字段白名单约束的最小 `auth_context` 摘要。

用于汇总稳定错误码、refresh-required、降级矩阵、六项恢复重验和 secret leak 的实际只读验收探针：

```bash
PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python - <<'PY'
import asyncio, json
from ns_common.exceptions import NsRuntimeIamDeniedError, NsRuntimeIamTimeoutError, NsRuntimeIamUnavailableError
from ns_common.iam import IamAccessDecision
from ns_common.time import ControlledClock
from ns_runtime.iam import AuthorizationMode, BackendRecoveryCoordinator, BackendUnavailablePolicy, MessageAuthorizationService, OperationRiskContext, RecoveryRevalidationResult
from tests.test_runtime_iam_authorization import NOW, _Iam, _request, _snapshot
from tests.test_runtime_iam_client import SERVICE, TOKEN, _request as handshake_request, RuntimeIamClientTestCase

class Revalidator:
    def __init__(self, result): self.result = result
    async def revalidate(self): return self.result

async def main():
    clock = ControlledClock(utc_start=NOW)
    evidence = {"stable_codes": [NsRuntimeIamDeniedError.code, NsRuntimeIamUnavailableError.code, NsRuntimeIamTimeoutError.code]}
    refresh = IamAccessDecision(allowed=True, reason="refresh", permission_version="version:1", decided_at=NOW, refresh_required=True)
    try:
        await MessageAuthorizationService(iam_client=_Iam([refresh], clock), clock=clock, mode=AuthorizationMode.STRICT, cache_ttl_seconds=60).authorize(snapshot=_snapshot(), request=_request(), risk=OperationRiskContext())
    except NsRuntimeIamDeniedError as error:
        evidence["refresh_required"] = [error.code, error.details["reason"]]
    try:
        await MessageAuthorizationService(iam_client=_Iam([NsRuntimeIamUnavailableError(details={"reason": "probe"})], clock), clock=clock, mode=AuthorizationMode.STRICT, cache_ttl_seconds=60).authorize(snapshot=_snapshot(), request=_request(), risk=OperationRiskContext())
    except NsRuntimeIamUnavailableError as error:
        evidence["strict_unavailable"] = error.code
    cached = IamAccessDecision(allowed=True, reason="cached", permission_version="version:1", decided_at=NOW)
    policy = BackendUnavailablePolicy()
    evidence["cache_low_risk_allowed"] = policy.decide(cached_decision=cached, snapshot_current=True, risk=OperationRiskContext()).allowed
    evidence["cache_risk_denials"] = {}
    for name, risk in {"high_risk_control": OperationRiskContext(high_risk_control=True), "cross_tenant": OperationRiskContext(cross_tenant=True), "new_configuration": OperationRiskContext(new_configuration=True), "global_coordination_write": OperationRiskContext(global_coordination_write=True)}.items():
        try: policy.decide(cached_decision=cached, snapshot_current=True, risk=risk)
        except NsRuntimeIamDeniedError as error: evidence["cache_risk_denials"][name] = error.code
    fields = ("credential_valid", "role_valid", "config_valid", "lease_valid", "fencing_valid", "session_snapshot_valid")
    evidence["recovery_denials"] = {}
    for field in fields:
        values = {name: True for name in fields}; values[field] = False
        coordinator = BackendRecoveryCoordinator(revalidator=Revalidator(RecoveryRevalidationResult(**values))); coordinator.mark_unavailable()
        try: await coordinator.recover()
        except NsRuntimeIamDeniedError as error: evidence["recovery_denials"][field] = error.code
    client, _ = RuntimeIamClientTestCase()._client([{"active": False, "reason": "TOKEN_INVALID", "authority": None}]); request = handshake_request()
    try: await client.authenticate(request)
    except NsRuntimeIamDeniedError as error:
        public = repr(error) + str(error) + repr(client) + repr(request)
        evidence["secret_leak"] = {"token": TOKEN in public, "service_credential": SERVICE in public, "credential_cleared": not request.credential.available}
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))

asyncio.run(main())
PY
```

实际输出：

```json
{"cache_low_risk_allowed":true,"cache_risk_denials":{"cross_tenant":"RUNTIME_IAM_DENIED","global_coordination_write":"RUNTIME_IAM_DENIED","high_risk_control":"RUNTIME_IAM_DENIED","new_configuration":"RUNTIME_IAM_DENIED"},"recovery_denials":{"config_valid":"RUNTIME_IAM_DENIED","credential_valid":"RUNTIME_IAM_DENIED","fencing_valid":"RUNTIME_IAM_DENIED","lease_valid":"RUNTIME_IAM_DENIED","role_valid":"RUNTIME_IAM_DENIED","session_snapshot_valid":"RUNTIME_IAM_DENIED"},"refresh_required":["RUNTIME_IAM_DENIED","permission_refresh_required"],"secret_leak":{"credential_cleared":true,"service_credential":false,"token":false},"stable_codes":["RUNTIME_IAM_DENIED","RUNTIME_IAM_UNAVAILABLE","RUNTIME_IAM_TIMEOUT"],"strict_unavailable":"RUNTIME_IAM_UNAVAILABLE"}
```

### 静态安全与边界检查

实际命令：

```bash
if rg -n '(logger|audit).*(token|credential|secret)|(token|credential|secret).*(logger|audit)' src/ns_common/iam.py src/ns_backend/iam/runtime_contracts.py src/ns_backend/iam/runtime_django.py src/ns_backend/iam/services/internal.py src/ns_runtime/iam src/ns_runtime/main.py; then exit 11; else echo 'SECURITY_SINK_SCAN=NO_MATCH'; fi
if rg -n 'from pathlib|import pathlib|builtins\.open|os\.open|write_bytes|write_text|pickle|shelve|sqlite|redis|valkey' src/ns_runtime/iam/credential_cache.py; then exit 12; else echo 'CREDENTIAL_CACHE_PERSISTENCE_SCAN=NO_MATCH'; fi
PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python - <<'PY'
import inspect, json
from ns_common.security import AesGcmSecretBox
source = inspect.getsource(AesGcmSecretBox).casefold()
forbidden = ("pathlib", "builtins.open", "os.open", "write_bytes", "write_text", "pickle", "shelve", "sqlite", "redis", "valkey")
print(json.dumps({"AES_GCM_SECRET_BOX_PERSISTENCE_REFERENCES": [item for item in forbidden if item in source]}))
PY
if rg -n 'get_async_http_client|_CLIENT_MAP|from .*state_store|import .*state_store|class (StateStore|DeliveryRecord|AckRecord|NackRecord|DeferRecord)' src/ns_common/iam.py src/ns_backend/iam/runtime_contracts.py src/ns_backend/iam/runtime_django.py src/ns_runtime/iam src/ns_runtime/main.py; then exit 13; else echo 'FORBIDDEN_BOUNDARY_SCAN=NO_MATCH'; fi
```

实际输出：`SECURITY_SINK_SCAN=NO_MATCH`、`CREDENTIAL_CACHE_PERSISTENCE_SCAN=NO_MATCH`、`{"AES_GCM_SECRET_BOX_PERSISTENCE_REFERENCES": []}`、`FORBIDDEN_BOUNDARY_SCAN=NO_MATCH`。

- 安全/隔离结论：未发现 token/credential/secret 写入 logger/audit 的路径；credential cache 与 AES-GCM secret box 无文件、pickle、数据库或外部 cache 持久化引用；P06 代码未跨入 global HTTP client/service locator、P07 delivery/ack/nack/defer pipeline 或 P08 StateStore 边界。
- 已知限制：本验收只证明仓库当前 P06 合同及其单进程本地缓存/恢复重验行为；不声明 durable audit、跨进程缓存一致性、P08 lease/fencing 持久权威或集群协调。首次 runtime 全量的 `ENVIRONMENT FIX REQUIRED` 已通过刷新声明依赖解决，最终实现状态无 `FIX REQUIRED`。
- 下一工作包：`P07-W01` 保持 `NOT_STARTED`；本次验收在 P06 `VERIFIED` 出口停止。

## P07 Processor 流水线、插件、事件与审计验收证据

- 工作包：`P07-W01` 至 `P07-W10`。
- 状态：`VERIFIED / F3`。
- 完成时间：`2026-07-22T09:03:00+08:00`。
- 环境：WSL2，Ubuntu 22.04.5 LTS，kernel `6.18.33.2-microsoft-standard-WSL2`；工作区 `/mnt/s/PythonProject/ns/ns_evermore`；分支 `codex/ns-runtime-implementation`，未新建分支。
- 解释器：runtime `/home/ns/.virtualenvs/ns_runtime/bin/python` 与 backend `/home/ns/.virtualenvs/ns_backend/bin/python` 均为 Python `3.10.12`。
- 修改文件：新增 `src/ns_runtime/processor/{__init__,contracts,registry,pipeline,audit,event_bus,plugins,integration}.py`、`tests/test_runtime_processor_pipeline.py`、`tests/test_runtime_processor_boundaries.py`；修改 `src/ns_runtime/connection/{iam,lifecycle,reauth,resume}.py`、`src/ns_runtime/iam/client.py`、`src/ns_runtime/main.py`、五份 connection/session 测试，以及实施计划、ADR 和本验收日志。

### P07-W01 至 W10 实现证据

- W01：`ProcessorContext` 使用 frozen/slotted/kw-only 类型，精确持有 normalized Envelope、SC-1 session、typed trace、config/policy version、Clock 与有限 `ProcessorDependencies`；normalized context 构造前由 P03 inbound boundary拒绝 forged source/auth_context，再由 runtime authority 注入。context 与 dependency repr 不输出 identity、permission ref、Envelope 或 payload。
- W02：`PROCESSOR_STAGE_ORDER` 冻结为 security validation、authorization、rate-limit entry、idempotency precheck、audit marker、routing preparation、message processor、response finalize；专项验证 exact 顺序及 reject 后 stop。rate limit、idempotency 与 routing 仅有显式 interface-only 实现，没有真实 store 或 target selection。
- W03：`ProcessorRegistry` 是显式实例，支持 `register/resolve/freeze`，registration 维度为 message.type、stage、同 major protocol version range、feature flag 和 enabled state；duplicate exact、overlap version、跨 major range、flag mismatch 均拒绝。
- W04：每次执行只通过既有 TaskSupervisor 创建一个命名 task；timeout 映射 `RUNTIME_PROCESSOR_TIMEOUT`，外部 cancellation 原样穿透，未知普通异常映射不复制原文本的 `RUNTIME_PROCESSOR_FAILED`。error/reject/timeout/cancel 均截断后续 stage；severe protocol violation 保持既有 close policy。
- W05/W06：`ProcessorAuditRecord` 只接受 typed safe summary、processor、闭集 action、稳定 error code、trace、config/policy version、required consistency 与 UTC time；每条执行消息 final sink attempt 恰好一次。ordinary sink failure不覆盖业务结果；`STRONG_REQUIRED` failure不能返回 pipeline success。当前 logging/test sink不声明 durable，P08 后接 authority store。
- W07/W08：`EventBus` 支持 typed subscribe/publish、per-subscriber timeout、exception isolation和有序 report；subscriber task复用同一 TaskSupervisor。`RuntimeEvent` 字段精确为 object_id、safe_summary、trace_reference，不存在 token/credential/payload/IAM response 或状态修改入口。
- W09：本地 trusted plugin metadata 冻结 namespace/schema/permissions/timeout/state namespace/feature flag；duplicate namespace、invalid schema、未授权 permission/namespace/flag均拒绝，批量 registration 冲突时原子失败且不留下部分登记。plugin registration只能进入 message processor stage；无 remote download、plugin runtime、sandbox 或私有 authority store。
- W10：`ConnectionLifecycleManager._read_loop` 在 P03 decode/schema 后对所有已认证入站消息调用 PC-1；heartbeat/drain/reauth 使用既有 P05 领域 processor adapter，health、task 与其余 disabled contract使用 P03 feature-disabled adapter。真实 WebSocket 测试对 heartbeat、task.disabled、health.disabled、drain、duplicate drain、draining heartbeat 共 6 次执行得到 6 次 final audit；transport callback不再按 enabled/disabled直接执行业务。
- IAM-R1 衔接：`HandshakeIamAuthority` 显式保留 `principal_type` 并由 production `IamClient` 从 introspection 传入；resume/reauth 固定校验 principal type 与原 logical owner 一致，漂移时 fail-closed；P07 authorization由 `MessageAuthorizationService` 构造当前 PermissionSnapshot/access request，保留 strict/cache、tenant/risk 和 backend unavailable 语义；SC-1 frozen field set未改变。

### 测试命令与结果

1. P07 pipeline/registry/audit/EventBus/plugin 专项：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest -v tests.test_runtime_processor_pipeline tests.test_runtime_processor_boundaries
   ```

   结果：`Ran 14 tests in 0.124s`，`OK`；失败 `0`，跳过 `0`。

2. P07 与 connection/session composition 联合回归：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest -v tests.test_runtime_processor_pipeline tests.test_runtime_processor_boundaries tests.test_runtime_connection_composition tests.test_runtime_connection_authentication tests.test_runtime_connection_session
   ```

   结果：`Ran 60 tests in 6.376s`，`OK`；失败 `0`，跳过 `0`。

3. runtime 依赖边界全量回归，按 DEP-1 排除 Django-only `test_cache.py`：

   ```bash
   set -o pipefail
   rg --files tests -g 'test_*.py' -g '!test_cache.py' | sort | sed 's#/#.#g; s#\.py$##' | xargs env PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest
   ```

   最终结果：`Ran 679 tests in 23.480s`，`OK (skipped=1)`；失败 `0`，唯一跳过项为 Windows event-loop policy。

4. backend/Django/cache 全量回归：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest discover -s tests -p 'test_*.py'
   ```

   最终结果：`Ran 690 tests in 20.131s`，`OK (skipped=49)`；失败 `0`。49 项为 1 个 Windows event-loop policy 与 backend 环境未安装 runtime transport optional dependency导致的 48 个 transport 跳过；P07 的 14 项专项均真实执行。

5. 环境与静态有效性：

   ```bash
   /home/ns/.virtualenvs/ns_runtime/bin/python -m pip check
   /home/ns/.virtualenvs/ns_backend/bin/python -m pip check
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m compileall -q src tests
   git diff --check
   ```

   结果：两环境均为 `No broken requirements found.`；compileall 和 diff check 成功。

6. 冷导入与敏感字段探针：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python - <<'PY'
   import dataclasses, json
   import ns_runtime.processor
   from ns_runtime.processor.integration import IamProcessorAuthorization
   from ns_runtime.processor import ProcessorAuditRecord, RuntimeEvent
   print("PROCESSOR_IMPORT=OK")
   print("INTEGRATION_IMPORT=OK")
   for value in (ProcessorAuditRecord, RuntimeEvent):
       fields = [item.name for item in dataclasses.fields(value)]
       forbidden = sorted(set(fields) & {"token", "credential", "payload", "iam_response", "raw_envelope", "raw_payload"})
       print(json.dumps({"type": value.__name__, "fields": fields, "forbidden_fields": forbidden}, sort_keys=True))
   PY
   ```

   最终输出包含 `PROCESSOR_IMPORT=OK`、`INTEGRATION_IMPORT=OK`，两类 `forbidden_fields` 均为 `[]`。首次独立 integration 冷导入曾暴露 processor facade/connection lifecycle circular import；修正为 core facade不急加载 integration、SessionContext 构造期惰性类型校验后，上述冷导入和全部回归均通过。

### 故障与安全验证

- Pipeline：exact 8-stage order；authorization reject后仅前两阶段执行；message processor timeout取消 supervised task并映射稳定 timeout；caller cancellation在 final audit 后原样传播；后续 response finalize均未误执行。
- Processor isolation：恶意 `RuntimeError("token=processor-secret")` 只映射 `RUNTIME_PROCESSOR_FAILED`，result、audit和公开异常文本中无 secret；下一条消息不受 subscriber 或 processor 原异常对象污染。
- Audit：success/reject/timeout/cancel/unknown failure均为一次 sink attempt；ordinary sink hostile failure保持原结果，strong-required hostile failure返回 processor failure，sink异常文本不进入 record。
- EventBus：good/bad/slow 三订阅者同时发布得到 succeeded/failed/timed_out，主 publish正常返回且 TaskSupervisor failures为空；bus无权威状态读写 API，丢失/失败不会改变主链路。
- Plugin：duplicate namespace、overlap processor version、invalid schema、missing permission与尝试注册 authorization stage均 fail-closed；同批次后项冲突时 registry 保持零部分写入。
- Integration：真实 WebSocket ingress验证 health和task disabled仍经过 authorization/pipeline/final audit后返回标准 `RUNTIME_FEATURE_DISABLED`；旧 epoch protocol violation经 pipeline安全错误映射后仍按既有 policy关闭；resume/reauth的 principal type漂移均拒绝并关闭 logical connection。

### 静态禁止边界

实际扫描结果：`P08_RELIABLE_BOUNDARY_SCAN=NO_MATCH`、`SECOND_OWNER_SCAN=NO_MATCH`、`PLUGIN_RUNTIME_SCAN=NO_MATCH`、`GLOBAL_RUNTIME_OBJECT_SCAN=NO_MATCH`。

- 未发现 StateStore、Redis/Valkey authority、lease、fencing、CAS、DeliveryRecord/AckRecord/NackRecord/DeferRecord 或 RoutingPlan 类型/import。
- processor package未构造 TaskSupervisor、event loop、asyncio.run或 shutdown coordinator；所有 execution/subscriber task使用 composition传入的同一 supervisor。
- plugin边界无 HTTP/download/subprocess/multiprocessing/WASM/sandbox引用；无 global ProcessorRegistry/EventBus/AuditSink 实例。
- `ProcessorAuditRecord` 和 `RuntimeEvent` 无 token、credential、raw payload、raw IAM response字段；不序列化原始 Envelope。

### 已知限制与下一工作包

- 当前 `STRONG_REQUIRED` 只冻结一致性要求与 fail-closed语义，不声明 durable audit成功；P08未实现前不能把 logging/test sink当作强一致权威。
- rate limiter、idempotency store、routing/target selection仍只有接口；EventBus只做进程内通知；plugin只声明本地可信边界，不执行远程代码或提供 sandbox。
- 不存在可靠投递、ACK/NACK/Defer state、retry/dead letter、RoutingPlan、lease/fencing/CAS；health/task/management等未启用能力继续返回稳定 feature-disabled错误。
- 下一工作包：`P08-W01 StateStoreCapabilities`，保持 `NOT_STARTED`。

## P07 MESSAGE_PROCESSOR 标准阶段 review blocker 关闭证据

- 工作包：`P07-W02`、`P07-W03`、`P07-W04`。
- 状态：blocker 已关闭，P07 重新达到 `VERIFIED / F3`。
- 完成时间：`2026-07-22T09:20:34+08:00`。
- 环境：WSL2，Ubuntu 22.04.5 LTS，kernel `6.18.33.2-microsoft-standard-WSL2`；工作区 `/mnt/s/PythonProject/ns/ns_evermore`；分支 `codex/ns-runtime-implementation`，未新建分支。
- 解释器：runtime `/home/ns/.virtualenvs/ns_runtime/bin/python` 与 backend `/home/ns/.virtualenvs/ns_backend/bin/python` 均为 Python `3.10.12`。

### Blocker 与修复

- 根因：`ProcessorStage` 和 `PROCESSOR_STAGE_ORDER` 虽包含 `MESSAGE_PROCESSOR`，但旧 `build_standard_stage_processors()` 只返回七个通用 processor；production composition 另行补注册具体 handler，因此实际连接路径可运行，但标准阶段 contract 不完整。旧顺序测试又手工注册全部八阶段，没有验证标准构造器，故未暴露缺口。
- W02：`PROCESSOR_STAGE_ORDER` 改为显式八元素 tuple；新增 `MessageProcessor` binding contract 与 `MessageProcessorStageProcessor` execution boundary。`build_standard_stage_processors(message_processor=...)` 现在强制接收 binding，并按固定顺序返回完整八阶段。
- W03：connection composition 不再先注册七个标准阶段再单独补 message handler，而是为每个 message contract 构造完整标准 map，并按 message.type、stage、protocol version、feature flag 注册八阶段。registry 测试覆盖 message processor 正常 resolve、duplicate、version overlap、flag mismatch 和多 flag 同时匹配冲突。
- W04：timeout、caller cancellation、hostile exception 与 error mapping 均通过真实 `MessageProcessorStageProcessor` wrapper 验证。缺失 message processor 时只完成 routing preparation 之前六阶段，不执行 response finalize，不伪成功，返回稳定 `RUNTIME_PROCESSOR_FAILED`，final audit processor 标记为 `message_processor.unresolved`。
- 显式依赖：`ProcessorDependencies.audit_sink` 与 `event_bus` 的声明类型由 `object` 收紧为 `AuditSink` 与 `EventBus`，构造期仍执行明确类型门禁；plugin registration 也必须使用标准 message stage wrapper，不能以任意 processor 绕过该 execution boundary。

### 实际测试命令与结果

1. P07 processor 专项：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest -v tests.test_runtime_processor_pipeline tests.test_runtime_processor_boundaries
   ```

   结果：`Ran 18 tests in 0.146s`，`OK`；失败 `0`，跳过 `0`。

2. P07 与 connection/session 相关联合回归：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest -v tests.test_runtime_processor_pipeline tests.test_runtime_processor_boundaries tests.test_runtime_connection_composition tests.test_runtime_connection_authentication tests.test_runtime_connection_session tests.test_runtime_connection_reauth tests.test_runtime_connection_resume
   ```

   结果：`Ran 89 tests in 7.325s`，`OK`；失败 `0`，跳过 `0`。

3. runtime 依赖边界全量回归，按 DEP-1 排除 Django-only `test_cache.py`：

   ```bash
   set -o pipefail
   rg --files tests -g 'test_*.py' -g '!test_cache.py' | sort | sed 's#/#.#g; s#\.py$##' | xargs env PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest
   ```

   结果：`Ran 683 tests in 23.897s`，`OK (skipped=1)`；失败 `0`。

4. backend/Django/cache 全量回归：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest discover -s tests -p 'test_*.py'
   ```

   结果：`Ran 694 tests in 19.747s`，`OK (skipped=49)`；失败 `0`。

5. 环境、冷导入与边界验证：两环境 `pip check` 均为 `No broken requirements found.`；全树 `compileall`、processor/integration 冷导入与 `git diff --check` 通过。只读标准 contract 探针输出完整相同的 `STAGE_ORDER`/`STANDARD_STAGES`，并输出 `MESSAGE_BOUNDARY=MessageProcessorStageProcessor`、`AUDIT_TYPE=AuditSink`、`EVENT_TYPE=EventBus`。

### 禁止边界复核

- `P08_RELIABLE_BOUNDARY_SCAN=NO_MATCH`：未引入 StateStore、Redis/Valkey authority、lease/fencing/CAS、DeliveryRecord/AckRecord/NackRecord/DeferRecord、retry、dead letter 或 RoutingPlan。
- `SECOND_OWNER_SCAN=NO_MATCH`：processor package 未构造第二 TaskSupervisor、event loop 或 shutdown owner。
- `GLOBAL_PROCESSOR_STATE_SCAN=NO_MATCH`：无 global ProcessorRegistry、EventBus、AuditSink 或 ProcessorPipeline 实例。
- `TRANSPORT_BYPASS_SCAN=NO_MATCH`：标准 contract、pipeline 与 registry 不直接调用 transport；现有 transport response adapter 仍由 composition 显式注入。

## P07 最终风险关闭与 VERIFIED 测试证据

- 工作包：`P07-W01`、`P07-W02`、`P07-W03`、`P07-W04`、`P07-W05`、`P07-W07`、`P07-W08`。
- 状态：`VERIFIED / F3`。
- 完成时间：`2026-07-22T09:30:50+08:00`。
- 环境：WSL2，Ubuntu 22.04.5 LTS，kernel `6.18.33.2-microsoft-standard-WSL2`；工作区 `/mnt/s/PythonProject/ns/ns_evermore`；分支 `codex/ns-runtime-implementation`，未新建分支。
- 解释器：runtime `/home/ns/.virtualenvs/ns_runtime/bin/python` 与 backend `/home/ns/.virtualenvs/ns_backend/bin/python` 均为 Python `3.10.12`。

### Risk-01：ProcessorDependencies 类型契约

- `audit_sink: AuditSink` 与 `event_bus: EventBus` 是 dataclass 的静态显式注解；`TYPE_CHECKING` 避免 core contract 导入 audit/EventBus implementation 时形成循环，runtime local import 仅作为错误 composition 的启动期防御，不是主要类型契约。
- 正确 `DeterministicTestAuditSink/EventBus` 可构造 `ProcessorDependencies`，并保持现有 runtime composition 不变；替换成 `object()` 分别稳定触发 `NsValidationError`。
- processor facade 与 integration 分别冷导入成功，实际输出 `AUDIT_TYPE=AuditSink`、`EVENT_TYPE=EventBus`；没有 global audit sink 或 global EventBus。

### Risk-02：EventBus subscriber 生命周期

- `subscribe` 返回 frozen/slotted `SubscriptionHandle`；handle 由当前 EventBus 实例登记，不能用伪造或另一 EventBus 的同 ID handle删除当前订阅。
- `unsubscribe(handle)` 返回闭集 `UnsubscribeOutcome.REMOVED/NOT_FOUND`；不存在订阅和重复退订均为稳定 `NOT_FOUND`，不抛出状态异常。
- publish 在启动时截取 subscriber snapshot。退订已经进入当前 publish 的订阅不会取消其 supervised task，该次 publish 正常形成 report；后续 publish 不再执行该 subscriber。subscriber timeout/exception 隔离语义保持不变。
- EventBus 仍为 instance-owned best-effort notification；未增加状态修改接口、global registry、authority storage 或新的 supervisor。

### 测试证据

1. Test：P07 processor/pipeline/registry/audit/EventBus/plugin 专项。

   Environment：runtime Python `3.10.12`。

   Command：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest -v tests.test_runtime_processor_pipeline tests.test_runtime_processor_boundaries
   ```

   Result：`Ran 22 tests in 0.183s`，`OK`；失败 `0`，跳过 `0`。实际覆盖固定八阶段、security/authorization reject、message timeout/cancellation/unknown exception、missing processor、registry resolve/duplicate/version/feature conflict、final audit exactly once/failure/sensitive schema、typed event、subscriber timeout/exception/unsubscribe、plugin duplicate namespace/invalid schema/unauthorized registration。

2. Test：P07 与 connection/session 相关联合回归。

   Environment：runtime Python `3.10.12`。

   Command：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest -v tests.test_runtime_processor_pipeline tests.test_runtime_processor_boundaries tests.test_runtime_connection_composition tests.test_runtime_connection_authentication tests.test_runtime_connection_session tests.test_runtime_connection_reauth tests.test_runtime_connection_resume
   ```

   Result：`Ran 93 tests in 7.286s`，`OK`；失败 `0`，跳过 `0`。

3. Test：runtime 依赖边界全量回归，按 DEP-1 排除 Django-only `test_cache.py`。

   Environment：runtime Python `3.10.12`。

   Command：

   ```bash
   set -o pipefail
   rg --files tests -g 'test_*.py' -g '!test_cache.py' | sort | sed 's#/#.#g; s#\.py$##' | xargs env PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest
   ```

   Result：`Ran 687 tests in 24.254s`，`OK (skipped=1)`；失败 `0`。

4. Test：backend/Django/cache 全量回归。

   Environment：backend Python `3.10.12`。

   Command：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest discover -s tests -p 'test_*.py'
   ```

   Result：`Ran 698 tests in 19.869s`，`OK (skipped=49)`；失败 `0`。

5. Test：依赖、导入、编译与禁止边界。

   Environment：runtime/backend Python `3.10.12`，Ubuntu 22.04.5 WSL2。

   Command：两环境 `python -m pip check`、backend `python -m compileall -q src tests`、processor/integration 冷导入探针、`git diff --check`，以及 P08/reliable、第二 owner、global processor state 扫描。

   Result：两环境均为 `No broken requirements found.`；`PROCESSOR_IMPORT=OK`、`INTEGRATION_IMPORT=OK`、`AUDIT_TYPE=AuditSink`、`EVENT_TYPE=EventBus`、`SUBSCRIPTION_HANDLE=SubscriptionHandle`、`UNSUBSCRIBE_OUTCOMES=removed,not_found`；`P08_RELIABLE_BOUNDARY_SCAN=NO_MATCH`、`SECOND_OWNER_SCAN=NO_MATCH`、`GLOBAL_PROCESSOR_STATE_SCAN=NO_MATCH`；compileall 与 diff check 通过。

### 最终判断

- 代码完成：是。
- 测试真实通过：是。
- acceptance evidence 完整：是。
- P07 evidence status：`VERIFIED`。
- 未引入 StateStore、Redis/Valkey authority、DeliveryRecord、ACK/NACK/Defer、retry/dead-letter、RoutingPlan 或 target selection。

## P08 StateStore 抽象契约与 Authority Boundary 最终证据

- 工作包：`P08-W01` 至 `P08-W08`。
- 状态：`VERIFIED / F3`。
- 完成时间：`2026-07-22T10:31:58+08:00`。
- 环境：WSL2，kernel `6.18.33.2-microsoft-standard-WSL2`，`x86_64`；工作区 `/mnt/s/PythonProject/ns/ns_evermore`；分支 `codex/ns-runtime-implementation`，未创建新分支。
- 解释器：runtime `/home/ns/.virtualenvs/ns_runtime/bin/python` 与 backend `/home/ns/.virtualenvs/ns_backend/bin/python` 均为 Python `3.10.12`。

### 实现与契约证据

- W01：`StateAuthorityKind` 与不可变 boundary map 明确 connection/session 为 local、permission snapshot/credential 为 external、processor execution 为 transient、strong audit 为唯一 active StateStore authority、future authority 为 reserved；`StateStoreCapabilities` 与 caller capability 分离，非 Store authority 无法构造 access scope。
- W02：新增 backend-neutral `StateStore`、`StateNamespace`、`StateKey`、`StateDocument`、`StateRevision`、`StateRecord`、`StateAssertion`、`StateMutation`、`StateTransaction`、`StateStoreHealth`，公开操作精确为 `open/close/capabilities/read/compare_and_set/transact/append/health`；无 `put`、`set` 或 last-write-wins。
- W03：tenant/system/runtime/plugin/audit 使用闭集 namespace 类型；所有访问同时绑定 authority、caller capability、atomic scope、namespace/domain/tenant；裸字符串 key 与跨 namespace/domain/tenant 在 provider mutation 前拒绝。
- W04：schema version、state version、opaque provider-issued revision 与 epoch 分离；create 强制 absent assertion，replace/delete 强制 expected revision，可附加 expected state version/epoch；冲突、schema mismatch 和 epoch mismatch 均保持零 mutation；未实现 epoch allocation、lease 或 fencing。
- W05：`RuntimeDependencySlots` 新增显式类型化 StateStore slot；RuntimeService 在 start hook/admission 前验证 injected Store 已 open/ready；既有 RuntimeShutdownCoordinator 在唯一 TaskSupervisor 关闭后、sink flush 前关闭 Store，未新增 owner、supervisor、loop 或 coordinator。
- W06：读取一致性闭集为 LINEARIZABLE、AT_LEAST_REVISION、STALE_ALLOWED；新增 11 个稳定 StateStore 错误并登记到 ERR-1。read timeout 返回 TIMEOUT；任何无法证明未提交的 write timeout/未知异常返回 INDETERMINATE_WRITE，公共层不自动 retry。
- W07：新增 `StrongAuditAuthorityService` 与 provider-neutral StateStore binding，固定 `Processor -> AuditSink -> StrongAuditAuthorityService -> StateStore`；Processor 类型和 package 不导入 StateStore。ordinary logging sink拒绝声称 strong success，strong append失败阻断 pipeline success。
- W08：仅在 `tests/` 建立 deterministic semantic model/conformance subject，覆盖 lifecycle、CAS、并发 CAS、transaction atomicity、minimum revision、namespace、failure/recovery、multiple RuntimeContext isolation、ownership 与 strong audit；生产 `src/` 不包含任何具体 provider subclass。

### 修改文件

- 设计与账本：`docs/ns_runtime_architecture_decisions_0.0.2.md`、`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`、`docs/ns_runtime_acceptance_log_0.0.2.md`。
- 公共契约：`src/ns_common/state_store/__init__.py`、`authority.py`、`model.py`、`store.py`。
- 稳定错误：`src/ns_common/exceptions/state_store.py`、`src/ns_common/exceptions/__init__.py`、`src/ns_common/exceptions/registry.py`。
- runtime composition/authority：`src/ns_runtime/context.py`、`service.py`、`shutdown.py`、`state_authority.py`、`processor/audit.py`。
- 验证：`tests/_state_store_contract_model.py`、`tests/test_state_store.py`、`tests/test_runtime_state_store.py`、`tests/test_exceptions.py`。

### 实际测试命令与结果

1. P08 contract/runtime/audit/错误与既有 lifecycle 联合专项。

   Environment：runtime Python `3.10.12`。

   Command：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest tests.test_state_store tests.test_runtime_state_store tests.test_runtime_processor_pipeline tests.test_runtime_context tests.test_runtime_shutdown tests.test_runtime_service tests.test_exceptions -v
   ```

   Result：最终 `Ran 102 tests in 1.779s`，`OK`；失败 `0`，跳过 `0`。覆盖 close cancellation ownership 与稳定 write-timeout 映射修复后同一组重新执行通过；后续全量回归也包含相同测试。

2. runtime 依赖边界全量回归，按 DEP-1 排除 Django-only `test_cache.py`。

   Environment：runtime Python `3.10.12`。

   Command：

   ```bash
   set -o pipefail
   rg --files tests -g 'test_*.py' -g '!test_cache.py' | sort | sed 's#/#.#g; s#\.py$##' | xargs env PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest
   ```

   Result：`Ran 709 tests in 25.201s`，`OK (skipped=1)`；失败 `0`。唯一跳过项为 real Windows event-loop policy。

3. backend/Django/cache 根目录全量回归。

   Environment：backend Python `3.10.12`。

   Command：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_backend/bin/python -m unittest discover -s tests -p 'test_*.py' -v
   ```

   Result：`Ran 720 tests in 20.711s`，`OK (skipped=49)`；失败 `0`。49 项为 1 个 Windows event-loop policy 与 backend 环境未安装 runtime transport optional dependency导致的 48 个 transport 跳过；P08 测试均真实执行。

4. 环境边界探针。

   Environment：runtime Python `3.10.12`。

   Command：

   ```bash
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m unittest discover -s tests -p 'test_*.py' -v
   ```

   Result：该不符合 DEP-1 的直接 discovery 按预期不能作为 runtime 全量入口：`test_cache.py` import 因 runtime 环境无 Django 产生唯一 loader error；其余已加载测试均通过。改用第 2 项规定入口后 709 项通过。未安装依赖、未修改环境、未把该探针伪记为通过。

5. 依赖、编译、冷导入与 diff 有效性。

   Command：

   ```bash
   /home/ns/.virtualenvs/ns_runtime/bin/python -m pip check
   /home/ns/.virtualenvs/ns_backend/bin/python -m pip check
   PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime/bin/python -m compileall -q src tests
   git diff --check
   ```

   Result：两环境均为 `No broken requirements found.`；compileall 与 diff check 成功。StateStore 冷导入探针输出 `state_store cold import: OK`，并验证无新 thread、event-loop policy变化、Redis/Valkey driver、runtime反向依赖、global getter 或 StateStoreOwner。

### State ownership 与禁止项检查

- connection/session 未迁移，仍由 P05 logical owner 管理；permission snapshot/credential 未迁移，仍由 P06 IAM authority 管理；processor execution state 未迁移，仍由 P07 pipeline/registry实例管理。
- Processor package 对 `StateStore/state_store` 源码扫描为零；strong audit只经 AuditSink 和 authority service访问 Store。
- P08 新增生产源码中无 `StateStore` concrete subclass；具体 Redis、Valkey、SQLite adapter，Lua/Sentinel，lease/fencing、leader/cluster，Delivery/Ack/Nack/Retry/Dead Letter，RoutingPlan/Target Selection扫描均为零。
- 无 StateStore registry/service locator/ambient getter/hidden dependency；无第二 TaskSupervisor、event loop、shutdown coordinator 或 StateStoreOwner。

### 已知限制与下一工作包

- P08 只冻结 contract 和 strong audit authority chain；没有生产 StateStore provider，因此默认 production composition仍不注入 Store。不得把 deterministic test model当作 adapter或生产持久化证据。
- 未执行真实 Redis/Valkey/SQLite/cluster 集成；这些能力及 lease/fencing/reliable delivery/routing均未实现，不能由 P08 VERIFIED 推断完成。
- 下一工作包：`P09-W01`；P09 开始前继续以当前源码、docs 与 ADR重做基线，不从本记录推断实现。

### 最终判断

- 实现完成：是。
- 测试通过：是。
- evidence 完整：是。
- P08 evidence status：`VERIFIED`。

## P09 RoutingPlan 与本地路由验收证据

- 工作包：P09 Phase A跨阶段合同修复与`P09-W01`至`P09-W10`。
- 状态：`VERIFIED/F3`，仅指单进程本地routing。
- 完成时间：`2026-07-22T13:51:02+08:00`。
- 修改文件：扩展`ns_common.config` routing limits与`ns_common.exceptions`精确route reject；更新`ns_runtime.protocol` TargetGroup/registry、`processor` routing propagation与audit-before-send、`connection` lifecycle strong audit/routing eligibility、production composition；新增`src/ns_runtime/routing/{models,authority,router,integration,__init__}.py`和两套routing测试；更新配置示例、既有Phase A回归、实施计划、ADR-036与本日志。design checklist未修改。
- 公共契约变化：ENV-1冻结七种target kind、六种strategy、五种rebind、epoch/count与capability AND矩阵；ERR-1新增唯一`RUNTIME_ROUTE_REJECTED/200177`；SC-1 index snapshot增加五态routing eligibility并保持单mutation发布；PC-1新增`RoutingRequirement`和四态`RoutingPreparationResult`，response finalization变为纯边界且composition emitter只消费final-audit后的成功结果；RP-1冻结单快照本地Router、deterministic fallback.v1、deeply immutable plan/failure/safe projection和接口级consistency boundary。
- W01/W02：TargetGroup到trusted RoutingRequest严格转换；每个决策只读取一次LocalConnectionIndex snapshot，同一mutation sequence收集候选。remote runtime返回typed unavailable/resolution hint，不查询master。
- W03/W04/W05：按tenant boundary、intended universe、static、dynamic、score、select顺序处理；实现single/all/broadcast/quorum/all_required/weighted_subset与fixed/same_identity/same_capability/same_tenant/no_rebind_for_control。无implicit broadcast、same_component或ACK quorum。
- W06/W07/W08：`runtime_fallback/fallback.v1`只使用受信任稳定输入和canonical tie-break；fingerprint排除plan ID/time/message ref。ResolvedRoutingPlan与RoutingFailureReport显式分离、深度不可变、安全repr/projection；version只来自显式previous context。
- W09：只冻结`RoutingConsistencyPolicy`、`RoutingPlanRecorder`和`StrongRoutingPlanAuthority`接口。Router不接收StateStore，ordinary recorder只收safe projection；未激活FUTURE/ROUTING_PLAN authority，默认production strong authority unavailable，不声明durability。
- W10：policy reject、authoritative missing、tenant/IAM与其余unavailable使用稳定精确公共映射；later action为纯数据。候选/选择/证据默认上限10000/10000/20000，超限不截断；5001 selected bindings通过。

### 测试命令与结果

- P09专项：`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09/bin/python -m unittest tests.test_runtime_routing tests.test_runtime_routing_contracts`，最终`Ran 15 tests in 0.412s, OK`；subtest矩阵覆盖全部target/strategy/rebind、determinism、score evidence、immutable/version/security、limit与5001 fanout。同一最终代码在Windows运行`Ran 15 tests in 0.511s, OK`。
- Phase A专项：同一解释器执行`tests.test_runtime_protocol_schema tests.test_runtime_processor_pipeline tests.test_runtime_connection_index tests.test_runtime_connection_resume tests.test_runtime_connection_reauth tests.test_runtime_connection_security tests.test_runtime_connection_snapshot_audit`，`Ran 78 tests in 0.920s, OK`。覆盖stage-six short-circuit、feature-disabled隔离、strong audit send=0、resume/reauth/security unavailable与eligibility原子性。
- P03-P08联合：按`test_runtime_protocol*`、`transport*`、`connection*`、`session*`、`iam*`、`processor*`、`state*`加载41个模块，`Ran 347 tests in 8.714s, OK`。
- Linux runtime标准asyncio：`/home/ns/.virtualenvs/ns_runtime_p09`加载全部`test_*.py`但按DEP-1排除唯一Django专属`test_cache.py`，最终`Ran 731 tests in 20.182s, OK (skipped=2)`。未排除运行实际执行732项，唯一error为该环境按清单不安装Django；没有实现或测试失败。
- Linux runtime uvloop：同一最终731项在`uvloop.EventLoopPolicy()`下，`Ran 731 tests in 19.912s, OK (skipped=2)`。
- Linux backend：`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09/bin/python -m unittest discover -s tests`，最终`Ran 742 tests in 16.981s, OK (skipped=50)`；skips为backend清单不安装的runtime可选依赖路径。
- Windows标准asyncio：`F:\Python310\python.exe -m unittest discover -s tests -p "test_runtime_*.py"`，`Ran 454 tests in 7.125s, OK`。机器PATH无OpenSSL CLI，测试进程临时使用已安装`cryptography`生成等价localhost自签名夹具；临时helper和证书均已删除，仓库无残留。
- 依赖/静态：`/home/ns/.virtualenvs/ns_runtime_p09/bin/python -m pip check`与`/home/ns/.virtualenvs/ns_backend_p09/bin/python -m pip check`均输出`No broken requirements found.`；Windows Python `pip check`同样通过。`python -m compileall -q src tests`与`git diff --check`通过。
- 冷导入/禁止项：cold import `ns_runtime.routing`未加载Django/rest_framework/ns_backend；routing源码扫描无transport/send、DeliveryRecord/worker、ACK、backend/Django、FUTURE authority activation。Router不直接依赖StateStore API，不创建registry、supervisor、loop、shutdown owner、retry/queue/timer/task/subscription。

### 安全、限制与下一工作包

- 原始target、identity、connection/session/tenant与IAM证据仅存在于执行plan且`repr=False`；日志、指标与ordinary recorder只消费SafeRoutingProjection。feature-disabled消息在authorization后直接NO_ROUTING_REQUIRED，不调用Router，不泄露目标存在性。
- strong RoutingPlan persistence未启用；无production StateStore provider、Redis/Valkey/SQLite adapter、Lua、lease/fencing。master query、remote forwarding、stale topology、DeliveryRecord/attempt、ACK/NACK/Defer、retry/queue/timer/dead-letter、delivery quorum和P14 health scoring均未实现。
- 下一工作包：`P10-W01`保持`NOT_STARTED`；P10只能消费ResolvedRoutingPlan并独立冻结受理、Summary、去重与payload reference权威。

## P09 RP-1 post-submit公共契约复核修复验收证据

- 工作包：P09 RP-1 post-submit contract review；复核开始时状态按`IN_PROGRESS`处理，完成源码检查、实现、文档和全部回归后恢复为`VERIFIED/F3 (local only)`。
- 完成时间：`2026-07-22T14:49:31+08:00`。
- 范围：只修复P09。P10 Summary/DeliveryRecord未实施，`P10-W01`保持`BLOCKED`。
- 修改文件：新增`src/ns_runtime/routing/policy.py`；更新routing models/router/integration/exports、processor authorization contract/value propagation/integration、三组runtime测试，以及ADR-036、implementation plan和本日志。ENV-1 TargetGroup、P05 index eligibility、PC-1八阶段顺序、audit-before-send、lifecycle strong audit和W09 interface-only authority均未迁移owner。

### 公共契约修复

- Routing authority：删除`RoutingRequest.from_target()`把wire值直接提升为effective policy的路径，冻结`RequestedRoutingIntent -> RoutingPolicyDecision -> trusted RoutingRequest`。`DefaultLocalRoutingPolicy`对strategy/rebind显式accept/reject/tighten；same-identity、same-capability、same-tenant只有被decision接受后才生效。strategy/rebind reject保留精确reason并映射`RUNTIME_ROUTE_REJECTED`。
- Security override：policy只消费从可信`MessageTypeContract`生成的`RoutingRiskMetadata`；control、management、config、cluster、security audit和management capability强制`no_rebind_for_control`，不再依赖不存在的`security` category字符串。
- Broadcast：wire继续禁止rebind，effective policy固定`fixed_connection`。previous broadcast触发完整新snapshot/新plan ID/version/全量bindings重建，失效旧binding不会通过`same_tenant`局部替换。
- Previous chain：context包含plan ID/version、message reference、decision fingerprint、context-integrity fingerprint和selected bindings。Router在snapshot读取前验证message ownership、typed plan ID、version、fingerprint格式与完整性；跨message和篡改稳定拒绝，不生成plan。new decision fingerprint包含previous decision fingerprint，排除previous/current plan ID、created-at和message reference。
- IAM evidence：PC-1 stage 2返回immutable `AuthorizationDecisionEvidence`，stage 3至5透明保留，stage 6验证message、normalized target、principal/effective tenant、cross-tenant allow与permission snapshot。backend无decision ID时，runtime把access-check输入/allow结果、permission版本、target和message绑定为安全decision reference；RoutingPlan IAM reference/version来自该message decision而不是session snapshot。
- 类型不变量：`StrategyParameters`直接构造强制strategy/count矩阵并拒绝bool；`ResolvedRoutingPlan`强制version/previous、message chain、fingerprint、非空唯一binding和strategy-parameters一致；`RoutingFailureReport`强制outcome/reason一致并携带original-target safe reference、config/policy/index/later-action/resolution/occurred-at。stable reason细分strategy/rebind、三种limit、no-candidate、capability、target、epoch、draining/grace、authority/session suspension、strong authority和remote runtime。

### 测试命令与结果

- P09/PC-1专项：`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -m unittest tests.test_runtime_routing tests.test_runtime_routing_contracts tests.test_runtime_processor_pipeline`，`Ran 38 tests in 0.777s, OK`。覆盖sender不能绕过policy、accept/reject/tighten、安全override、fixed broadcast/rebroadcast、previous ownership/fingerprint/plan-ID independence、authorization evidence正反向、direct invalid construction及原target/strategy/rebind/5001 fanout。
- 既有边界专项：执行`test_runtime_protocol_schema`、`test_runtime_processor_pipeline`、`test_runtime_connection_index`、`test_runtime_connection_resume`、`test_runtime_connection_reauth`、`test_runtime_connection_security`和`test_runtime_connection_snapshot_audit`，`Ran 79 tests in 1.163s, OK`。ENV-1、P05 eligibility、stage-six、audit-before-send和lifecycle audit保持通过。
- P03-P09联合：加载protocol、transport、connection/session、IAM、processor、state和routing模块，`Ran 383 tests in 12.109s, OK`。
- Linux runtime标准asyncio：按DEP-1排除唯一Django-only `test_cache.py`，`Ran 739 tests in 24.722s, OK (skipped=1)`。
- Linux runtime uvloop：同一739项在uvloop下执行，`Ran 739 tests in 25.888s, OK (skipped=1)`。
- Linux backend：`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09_rp1_review/bin/python -m unittest discover -s tests -p 'test_*.py'`，最终顺序执行`Ran 750 tests in 20.980s, OK (skipped=49)`。一次与runtime全量并行的压力运行出现既有SQLite cache TTL timing assertion，单测立即复跑`Ran 1 test in 1.248s, OK`，随后backend全量顺序复跑通过；没有P09实现失败。
- 依赖与静态：两隔离环境`pip check`均为`No broken requirements found.`；runtime `compileall -q src tests`与`git diff --check`通过。
- 冷导入/禁止项：cold import `ns_runtime.routing`未加载Django、rest_framework或ns_backend。routing仍无transport send、DeliveryRecord/DeliveryAttempt/Summary、StateStore直连、TaskSupervisor/EventBus、worker、ACK/NACK/Defer、authority provider、remote forwarding或第二生命周期owner；later action仍只是纯数据。

### 最终判断与限制

- 实现完成：是；测试通过：是；P09 evidence状态：`VERIFIED/F3 (local only)`。
- strong RoutingPlan persistence、remote/master routing、cluster/lease/fencing、Delivery/Summary/ACK/retry仍未实现。P10-W01保持`BLOCKED`，必须等待独立范围授权。

## P09-FIX-02 公共契约缺口修复验收证据

- 工作包：`P09-FIX-02 permission/scoring/fingerprint/plan/failure-hint contract closure`；开始时P09按`IN_PROGRESS`处理，以下证据全部通过后恢复`VERIFIED/F3 (local only)`。
- 完成时间：`2026-07-22T16:02:44+08:00`。
- 范围：只修复P09公共契约。保留显式RoutingPolicy、broadcast fixed binding、previous chain、eligibility、audit-before-send与W09 interface-only边界；未实施P10、P14 health scoring、remote/master routing或strong authority provider。`P10-W01`保持`BLOCKED`。

### Blocker关闭证据

- Permission snapshot binding：`AuthorizationDecisionEvidence`分别记录session/effective snapshot ref/version，并由外层decision reference绑定message、target、tenant/cross-tenant、两组snapshot与底层decision result。production IAM invalidation refresh已验证同ref从旧版本更新到effective新版本；ref/version/effective篡改均在policy与Router前返回`AUTHORIZATION_EVIDENCE_MISMATCH`，policy调用与index snapshot均为零。
- Rebind expansion：`RoutingPolicyDecision`直接构造矩阵覆盖None到三种same-*、三种same-*之间全部横向扩张、合法保持/fixed/no-rebind收紧、broadcast非fixed、security-sensitive非no-rebind和security evidence不一致；非法值均为`NsValidationError`。security-sensitive broadcast因fixed/no-rebind不变量冲突而明确policy reject。
- Scoring authority：新增immutable `RoutingScoringDecision`并由policy decision持有；`RoutingRequest`已删除独立affinity/static-weight字段，未知注入直接拒绝。Router只读取decision，plan/fingerprint记录scorer input version/reference；default为空输入，专项用policy-owned affinity/weight验证选择变化，未引入health/latency/pressure。
- IAM fingerprint：相同routing/IAM evidence跨随机plan ID保持同fingerprint；只改变IAM decision result/reference或permission version均改变fingerprint。payload同时绑定IAM decision ref/version、authorized target、effective snapshot和scorer input，继续排除message reference、created-at和current/previous plan ID，并包含previous decision fingerprint。
- Independent plan invariant：plan保存`repr=False`的typed policy decision与authorization evidence，复验original target、strategy/parameters、rebind、security与policy evidence、config/policy/scorer、IAM/effective snapshot和selected binding。直接构造负向覆盖single到all/broadcast/quorum/all-required/weighted-subset、None到same-*、same-identity到其他same-*、broadcast非fixed、security evidence、parameter expansion、forged effective evidence与binding policy mismatch。
- Failure hint：最终闭集恰为`local/master_query_required/remote_runtime_required/authority_recovery_required`；local miss、remote runtime和strong authority unavailable映射分别验证。master-query只冻结值，不执行查询或创建later-action任务。

### 测试命令与结果

- P09 routing/models/policy/integration与PC-1：`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -m unittest tests.test_runtime_routing tests.test_runtime_routing_contracts tests.test_runtime_processor_pipeline`，`Ran 41 tests in 0.801s, OK`。加入IAM authorization refresh专项的联合为`Ran 47 tests in 2.854s, OK`。
- ENV-1、P05 eligibility、audit-before-send、lifecycle audit：执行`test_runtime_protocol_schema`、`test_runtime_processor_pipeline`、`test_runtime_connection_index`、`test_runtime_connection_resume`、`test_runtime_connection_reauth`、`test_runtime_connection_security`、`test_runtime_connection_snapshot_audit`，`Ran 79 tests in 1.858s, OK`。
- P03-P09联合：加载protocol、transport、connection/session、IAM、processor、state和routing模块，`Ran 373 tests in 21.419s, OK`。
- Linux runtime标准asyncio：按DEP-1排除唯一Django-only `test_cache.py`，`Ran 742 tests in 48.763s, OK (skipped=1)`。
- Linux runtime uvloop：同一742项在`uvloop.EventLoopPolicy()`下执行，`Ran 742 tests in 45.703s, OK (skipped=1)`。
- Linux backend：`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09_rp1_review/bin/python -m unittest discover -s tests -p 'test_*.py'`，`Ran 753 tests in 21.278s, OK (skipped=49)`。
- 依赖与静态：两隔离环境`pip check`均输出`No broken requirements found.`；runtime `compileall -q src tests`与`git diff --check`通过。
- 冷导入/禁止项：cold import `ns_runtime.routing`得到`cold_import_forbidden=[]`，未加载Django、rest_framework或ns_backend。routing扫描确认无transport send、StateStore直连、DeliveryRecord/DeliveryAttempt/MessageDeliverySummary、ACK/NACK/Defer、TaskSupervisor/EventBus/create-task；Request scoring injection扫描为空。

### 最终判断与限制

- 六个P09 blocker均关闭；实现与全部规定回归通过，P09恢复`VERIFIED/F3 (local only)`。
- strong RoutingPlan persistence、remote/master routing、cluster/lease/fencing、P14 health scoring、Delivery/Summary/ACK/retry仍未实现。`P10-W01`保持`BLOCKED`，等待独立授权。

## P09-FIX-03 RP-1 public type trusted-boundary closure验收证据

- 工作包：`P09-FIX-03`；开始时P09按`IN_PROGRESS`处理，以下证据全部通过后恢复`VERIFIED/F3 (local only)`。
- 完成时间：`2026-07-22T16:50:35+08:00`。
- 范围：只关闭P09 RP-1公共类型可信边界；不实施P10、P14 health scoring、remote/master routing或strong authority provider。`P10-W01`保持`BLOCKED`。
- 修改文件：更新processor authorization contract/integration，routing models/policy/integration/router/facade，两组routing测试，以及ADR-036、implementation plan和本日志。

### 三个blocker关闭证据

- Blocker 1，IAM message/semantic boundary：`AuthorizationDecisionEvidence`将当前message防重放binding与可复现semantic decision分开；公共构造即拒绝session/effective ref不同、空ref/version和两种binding伪造，同ref v1到v2 refresh合法。真实两个Envelope仅message ID不同的集成路径得到不同`message_binding_reference`、相同`semantic_decision_reference`与相同decision fingerprint；将第一条evidence跨message复用在policy调用和index snapshot均为零时拒绝。
- Blocker 2，policy/scorer authority：不可变`RoutingPolicyInvocation`绑定可信message type/category/audit/security、contract ref/version/capabilities、config/policy和intent/risk references；stage six重建并比较，message type、risk、config或policy不一致均在Router前拒绝。恶意policy试图用伪造`security_sensitive=false`覆盖真实security-sensitive contract时，结果为`POLICY_DECISION_MISMATCH`且index snapshot为零；类型化security override只允许reject/no-rebind安全结果，scorer身份只接受`runtime_fallback/fallback.v1`。
- Blocker 3，plan/fingerprint self-validation：Router与plan共享唯一canonical fingerprint函数。plan公开构造独立复验candidate/binding精确性、filtered全集、single/quorum/weighted-subset/all-required cardinality及policy/IAM/scoring authority，并重算fingerprint；即使调用方用`dataclasses.replace`同步修改expanded evidence，沿用旧fingerprint仍被拒绝。candidate score、selected顺序、index sequence、previous fingerprint及IAM/scoring/policy语义变化均有负向证据。

### 测试命令与结果

- P09 routing/models/policy/integration与PC-1专项：`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -m unittest tests.test_runtime_routing tests.test_runtime_routing_contracts tests.test_runtime_processor_pipeline`，`Ran 43 tests in 0.926s, OK`。覆盖15项规定矩阵，并额外覆盖typed scorer身份、跨message防重放与恶意policy；加入IAM authorization refresh专项的联合为`Ran 49 tests in 0.936s, OK`。
- ENV-1、P05 eligibility、audit-before-send、lifecycle audit：`Ran 79 tests in 1.268s, OK`。
- P03-P09联合：`Ran 375 tests in 12.182s, OK`。
- Linux runtime标准asyncio：按DEP-1排除Django-only `test_cache.py`，`Ran 744 tests in 25.360s, OK (skipped=1)`。
- Linux runtime uvloop：同一744项在`uvloop.EventLoopPolicy()`下执行，`Ran 744 tests in 26.185s, OK (skipped=1)`。
- Linux backend：`Ran 755 tests in 21.454s, OK (skipped=49)`。
- 依赖与静态：两隔离环境`pip check`均为`No broken requirements found.`；runtime `compileall -q src tests`与`git diff --check`通过。
- 冷导入/禁止项：cold import `ns_runtime.routing`得到`cold_import_forbidden=[]`；routing源码扫描无transport delivery/send、DeliveryRecord/DeliveryAttempt/MessageDeliverySummary、ACK/NACK/Defer、dead letter、Redis/Valkey/SQLite/Lua、lease/fencing、master query/remote forwarding、P14 health/latency/pressure、TaskSupervisor/EventBus/create-task。未新增第二supervisor/event loop/shutdown owner。

### 最终判断与限制

- 三个P09-FIX-03 blocker均关闭；P09恢复`VERIFIED/F3 (local only)`。
- strong RoutingPlan persistence、remote/master routing、cluster/lease/fencing、P14 health scoring、Delivery/Summary/ACK/retry仍未实现。`P10-W01`保持`BLOCKED`，等待独立授权。

## P09-FIX-04 RP-1 selected authority and scorer closure验收证据

- 工作包：`P09-FIX-04`；开始时P09按`IN_PROGRESS`处理，以下证据全部通过后恢复`VERIFIED/F3 (local only)`。
- 完成时间：`2026-07-22T17:36:40+08:00`。
- 范围：只关闭P09公共Plan仍可构造未经policy/IAM/scorer授权selected bindings的问题；不实施P10、P14、remote/master routing或strong provider。`P10-W01`保持`BLOCKED`。
- 修改文件：更新processor contracts/integration/pipeline/facade，routing models/router/integration/facade，routing/processor三组测试，以及ADR-036、implementation plan和本日志。

### 关闭证据

- ALLOW-only authorization：新增唯一`AuthorizationDecisionOutcome.ALLOW`，Evidence公共构造拒绝字符串allow、deny及任意对象；production只在真实IAM allowed后构造ALLOW。AuthorizationProcessor和stage six再次检查；自定义dependency返回`decision_reason=allow`但outcome=deny的deny-like对象时，在stage three前以`NsValidationError`失败。
- Policy target/message与Plan一致：Plan要求invocation完整requested intent和normalized target等于original target，policy message type等于IAM message type，IAM message reference等于plan，并将authorized target reference复算为plan canonical target。负向矩阵覆盖tenant值、target kind、同selector capability constraint、connection epoch、broadcast tenant及quorum count；policy target错误的标准stage-six路径在Router snapshot为零时拒绝。
- Selected满足IAM/target constraint：统一target/filter纯函数由Router与Plan共用；全部candidate冻结并验证primary intended universe、effective tenant、connection/epoch、identity、tenant、capability AND、component、runtime、broadcast tenant/constraint及P05 state/eligibility。filtered必须score=None，ELIGIBLE/SELECTED必须通过target/static/dynamic filter并具有可复算score，selected binding与candidate逐字段一致。
- Scorer前N重算：统一fallback.v1 score与canonical selection纯函数由Router与Plan共用；Plan复算所有通过candidate score，并严格选择single第1名、quorum前fanout_count、weighted_subset前subset_size及all/broadcast/all-required完整canonical顺序。数量正确但错选、跳过高分、低分替换、逆序、少选、多选均失败。
- Fingerprint不能替代语义：所有主要负向测试使用公共构造或`dataclasses.replace()`，先用唯一canonical函数同步生成合法fingerprint，再由Plan target/message/IAM/candidate/filter/score/selection不变量拒绝；同步篡改selected/candidates/score/binding并不能形成语义非法但可消费的Plan。

### 测试命令与结果

- P09 models/policy/router/integration、PC-1与IAM refresh联合：`Ran 55 tests in 1.137s, OK`；26项规定矩阵以测试和subtest覆盖，并回归message-ID independence、previous chain、broadcast fixed、all-required、permission/scoring和5001 fanout。
- ENV-1、P05 eligibility、IAM refresh、audit-before-send与lifecycle strong audit：`Ran 86 tests in 1.504s, OK`。
- P03-P09联合：`Ran 381 tests in 14.025s, OK`。
- Linux runtime标准asyncio：按DEP-1排除Django-only `test_cache.py`，`Ran 750 tests in 28.248s, OK (skipped=1)`。
- Linux runtime uvloop：同一750项在`uvloop.EventLoopPolicy()`下执行，`Ran 750 tests in 28.289s, OK (skipped=1)`。
- Linux backend：`Ran 761 tests in 22.903s, OK (skipped=49)`。
- 依赖与静态：两隔离环境`pip check`均为`No broken requirements found.`；runtime `compileall -q src tests`与`git diff --check`通过。
- 冷导入/禁止项：cold import `ns_runtime.routing`得到`cold_import_forbidden=[]`；routing源码扫描无transport delivery/send、Delivery/Summary、ACK/NACK/Defer、retry/dead letter、Redis/Valkey/SQLite/Lua、lease/fencing、master query/remote forwarding、P14 health/latency/pressure、TaskSupervisor/EventBus/create-task、global registry/service locator，未新增第二supervisor/event loop/shutdown owner。

### 最终判断与限制

- P09-FIX-04全部要求关闭；P09恢复`VERIFIED/F3 (local only)`。
- strong RoutingPlan persistence、remote/master routing、cluster/lease/fencing、P14 health scoring、Delivery/Summary/ACK/retry仍未实现。`P10-W01`保持`BLOCKED`，等待独立授权。

## P10-W01至W14 DR-1 admission、Summary、dedup与Payload Reference验收证据

- 工作包：`P10-W01`至`P10-W14`；用户独立授权解除P10阻塞后连续实施，全部源码、测试、文档和阶段出口证据通过后标记`VERIFIED/F3 (local only)`。
- 完成时间：`2026-07-22T20:31:00+08:00`。
- 基线：开始时worktree clean，分支`codex/ns-runtime-implementation`，HEAD/用户指定P09复核基线均为`2d6e0083c4ce05d81aa612db9c839219aa5c4a57`。
- 修改范围：新增`src/ns_runtime/delivery/`的DR-1 models/policy/store/service/response/PC-1 integration；扩展StateStore delivery authority、IAM payload_ref完整性result与runtime live client；新增/更新P10、IAM/backend测试及ADR-037、implementation plan和本日志。

### W01-W14关闭映射

- W01/DR-1：冻结Summary、prepared/cancelled-initializing DeliveryRecord、payload/dedup evidence、policy/result/response和atomic initialization。公共构造、伪造enum/string、schema/state version、count、fingerprint、`dataclasses.replace()`及跨plan/message/tenant/shard/binding图均同步复验。
- W02：sender priority/reliability/expires/ack timeout/target strategy只进入`AdmissionRequest`；trusted config/policy裁决后由service复验request fingerprint、config/policy版本、RP-1 effective strategy、TTL与资源上限。expired和剩余窗口不足创建failed Summary。
- W03：inline只在内存canonicalize，JSON/bytes类型、depth和policy/application/transport三重size限制全部校验；StateStore只保存size/digest/checksum/schema/fingerprint，无完整业务payload，且不自动转换payload_ref。
- W04-W05：`IamPayloadRefClient -> IamClient -> internal/payload_ref/validate/`逐selected target实时调用；result必须回显object/version/checksum/tenant/size/expiry。invalid/unauthorized/tenant mismatch不建DeliveryRecord；timeout/exception按best-effort/at-least-once/critical分别形成typed reject/wait/dead-letter disposition，不创建P13 record或授权cache。
- W06-W07：tenant + raw message_id + selected target fingerprint形成dedup key；StateStore首个absent transaction给并发请求唯一winner，冲突linearizable读typed evidence。in_progress/acked/dead/expired/cancelled全闭集稳定duplicate，不触发重投。
- W08-W09：all/partial/none accepted的Summary/Delivery计数与脱敏reason准确；all rejected仍原子创建dedup + failed Summary且零DeliveryRecord。真实P08 deterministic StateStore证明dedup、initializing root/shard与首批最多500条prepared同成同败，后续批次用revision/state version CAS推进；malformed store result拒绝，indeterminate write不伪装未提交或成功。
- W10：真实RP-1 plan的4999/5000/5001边界通过；前两者各1 shard，5001为6 shard，bucket固定1000、每个初始化事务最多创建500条DeliveryRecord，root/shard进度与终态逐批CAS一致。
- W11-W12：P10仅有prepared与cancelled_initializing，无queued/claim/send API，active/inflight恒零。真实501-target第二批CAS冲突触发原子取消：500条已创建prepared全部转cancelled_initializing，1条计入not_initialized，dedup转cancelled；重复或一般cancel输入拒绝。
- W13-W14：accepted wire投影exact为message_id、summary_id、accepted_at、status_query_hint、trace，不含delivery_id数组；rejected/duplicate同为typed response。post-commit response发送异常只记录bounded outcome并返回false，没有Store依赖且不回滚已提交authority。

### 实际测试命令与原始结果

- P10 targeted：`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -m unittest tests.test_runtime_delivery_admission -q`，`Ran 17 tests in 3.173s`，`OK`。覆盖正向、16并发、真实Store并发、atomic/indeterminate failure、all/partial/rejected、terminal duplicate、public replace、恶意policy/payload/store、4999/5000/5001分批CAS、501第二批失败原子取消、lightweight response和response send failure。
- P08/P09/PC-1/P10联合：`python -m unittest tests.test_runtime_state_store tests.test_state_store tests.test_runtime_routing tests.test_runtime_routing_contracts tests.test_runtime_processor_pipeline tests.test_runtime_processor_boundaries tests.test_runtime_delivery_admission -q`，`Ran 98 tests in 4.354s`，`OK`。
- P03-P10联合：加载45个`test_runtime_protocol*`、`transport*`、`connection*`、`iam*`、`processor*`、`state*`、`routing*`、`delivery*`模块，`Ran 412 tests in 16.312s`，`OK`。
- Linux runtime标准asyncio：按DEP-1排除Django-only `test_cache.py`，`Ran 768 tests in 27.358s`，`OK (skipped=1)`。
- Linux runtime uvloop：同一768项在显式`uvloop.EventLoopPolicy()`下执行，`Ran 768 tests in 27.951s`，`OK (skipped=1)`。
- Linux backend：`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09_rp1_review/bin/python -m unittest discover -s tests -p 'test_*.py'`，`Ran 779 tests in 25.446s`，`OK (skipped=49)`。
- 静态与依赖：最终`compileall -q src tests`、runtime/backend两环境`pip check`、`git diff --check`与P11+禁止项源码扫描均在本记录后执行；只有最终命令实际成功才保留本阶段`VERIFIED`状态。

### 限制与下一阶段

- 本次只在本地WSL隔离环境验证，无远程CI证据；该时点“仓库没有Redis/Valkey production StateStore provider”的限制已由后续P10-FIX-01关闭。P10仍因证据范围标记`F3 (local only)`，其余P11+限制不变。
- RP-1未修改；P10不从dict/wire/JSON反序列化RoutingPlan、不调用Router、不重选target，也不把routing/response/transport成功解释为delivery success。
- 未实现prepared->queued、send worker、claim/send、DeliveryAttempt、ACK/NACK/Defer、retry/timeout、DeadLetterRecord/replay、一般cancel/hold、lease/fencing、master query/remote forwarding、cluster、P14 health/fairness、第二TaskSupervisor/event loop/shutdown owner。`task.dispatch` production feature仍disabled。
- 下一工作包`P11-W01`保持`BLOCKED`，等待独立授权；P12 ACK闭环完成前不得开启task.dispatch production feature。

## P10-FIX-01 Redis/Valkey StateStore Provider历史验收证据（由P10-FIX-02重新审查）

- 工作包：`P10-FIX-01`；只补齐P08 contract的standalone Redis/Valkey production provider，不改写DR-1，不修改RP-1，不实施P11/P12。
- 完成时间：`2026-07-22T21:55:00+08:00`。
- 基线：开始时worktree clean，分支`codex/ns-runtime-implementation`，本地与upstream HEAD均为用户新增本地Redis环境说明后的`2824c131da947501c62b271e91355a42286d29f3`。
- 修改范围：新增`src/ns_common/state_store/redis_provider.py`与`composition.py`；更新StateStore facade、runtime state_store typed config/validation/example、startup dependency preflight、main composition/lifecycle、runtime production dependency清单及相应测试；新增ADR-038和本记录。`src/ns_runtime/delivery/`与`src/ns_runtime/routing/`零diff。

### Provider architecture与不变量

- `RedisValkeyStateStore`直接实现既有`StateStore` protected hooks：open/close、read、compare_and_set、transact、append、health。Redis与Valkey driver只在open时按backend动态加载；cold import不加载driver或创建client。
- typed config支持redis/valkey backend、credential-free endpoint、username、env/file/none password source、namespace和operation timeout。endpoint userinfo直接拒绝；config/options/provider/password-source repr以及typed异常不含password、endpoint或username，provider无logger/audit输出且不复制driver异常文本。
- record物理key使用provider namespace加typed StateKey canonical SHA-256 digest；revision来自namespace内单调counter并作为opaque token返回。cache namespace、client和soft-failure接口未被复用。
- 固定Lua transaction先验证全部absent/revision/state_version/epoch/schema/next-version assertion，再执行create/replace/delete并分配revision；任一冲突时零mutation落地。append Lua原子校验tail assertion、分配revision、追加entry并更新tail metadata。read支持linearizable、minimum-revision和显式stale语义；write timeout继续映射indeterminate且不retry。
- composition factory只接收typed runtime config和Clock；runtime main创建但不打开provider，既有service运行路径在start前open，既有RuntimeShutdownCoordinator负责close。没有第二TaskSupervisor、event loop、thread、retry worker或shutdown owner。

### 真实Redis环境

- Server：本机`redis-server 6.0.16`。共享`127.0.0.1:6379/0`按最新实施文档使用Redis default user + requirepass（空username）；自动化测试另启动独立standalone子进程，bind `127.0.0.1`、database 0、随机loopback port、同样使用default user + requirepass，并为每次测试生成随机`ns_runtime:test:<uuid>` namespace。
- Driver：redis-py `8.0.1`与valkey-py `6.1.1`；两种backend/driver均对同一Redis协议standalone执行认证与health。没有本机`valkey-server`，因此不声明Valkey server-specific integration。
- Secret：独立测试进程每次随机生成密码且只通过test password source注入；共享实例密码只从实施文档在进程内解析并传给一次性secret source。命令、输出、异常、repr、acceptance log均不记录任何密码。独立测试default user仅允许`ns_runtime:test:*`并显式拒绝FLUSHDB、FLUSHALL和KEYS；清理只SCAN + UNLINK本次namespace。
- 实施文档更新后对共享`127.0.0.1:6379/0`做脱敏复验：直接client `PING=True`、认证身份为`default`；随后Redis与Valkey两个driver分别通过真实`RedisValkeyStateStore`完成open/health/close，health均为`ready`。该共享探针只读，不创建或删除key；完整mutation、并发和失败语义仍由上述隔离进程验证。

### 实际测试命令与原始结果

- Provider专项：`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -m unittest tests.test_redis_state_store_provider tests.test_redis_state_store_integration -q`，`Ran 16 tests in 3.618s`，`OK`。覆盖default-user双driver认证/secret脱敏、config/factory、cold import/cache隔离、namespace隔离、16并发唯一create、CAS/schema/state/minimum-revision、Lua failed-batch rollback、append、timeout/unavailable、真实runtime lifecycle，以及真实P10 8并发dedup与501-target分批初始化。
- P08/P10/provider联合：`python -m unittest tests.test_state_store tests.test_runtime_state_store tests.test_runtime_delivery_admission tests.test_redis_state_store_provider tests.test_redis_state_store_integration -q`，`Ran 55 tests in 7.173s`，`OK`。
- Linux runtime标准asyncio：按DEP-1排除Django-only `test_cache.py`，`Ran 784 tests in 40.015s`，`OK (skipped=1)`。
- Linux runtime uvloop：同一784项在显式`uvloop.EventLoopPolicy()`下执行，`Ran 784 tests in 41.439s`，`OK (skipped=1)`。
- Linux backend：backend-only环境刻意不安装runtime Redis/Valkey driver，真实provider integration整类typed skip；全量`Ran 785 tests in 30.812s`，`OK (skipped=50)`。
- 静态与依赖：最终`compileall -q src tests`、runtime/backend两环境`pip check`、`git diff --check`、provider禁止清库命令扫描、delivery/RP-1零diff和P11+禁止项扫描均在本记录后执行；只有最终命令成功才保留`VERIFIED`。

### 最终判断与限制

- 该次验收当时把P10恢复为`VERIFIED/F3 (local only)`；后续review发现trusted-boundary、BaseException lifecycle、端口竞态与恢复证据blocker，因此该状态曾由P10-FIX-02重新降为`IN_PROGRESS`。下节是关闭blocker后的当前权威证据。
- 未实现或未宣称：Sentinel、Cluster、failover、replica read、lease/fencing、leader election、TLS证书/CA材料验收、跨节点owner、P11 prepared->queued/claim/send、DeliveryAttempt、P12 ACK/NACK/Defer/timeout/retry、P13 dead letter/replay/一般cancel/hold及P14 health/fair scheduling。
- 下一工作包`P11-W01`保持`BLOCKED`，等待独立授权；P12 ACK闭环完成前不得开启task.dispatch production feature。

## P10-FIX-02 Redis StateStore Trusted-Boundary、Lifecycle与Recovery Closure验收证据

- 审查结论：`REVIEW FAILED`。P10-FIX-01与P10从`VERIFIED/F3 (local only)`降为`IN_PROGRESS/F3 (local only)`，直到trusted-boundary、BaseException lifecycle、端口reservation、跨provider recovery与Valkey证据校准全部通过重新验收。
- 工作包：`P10-FIX-02 Redis StateStore trusted-boundary、lifecycle 与 recovery closure`；全部blocker与本地重新验收通过后恢复`VERIFIED/F3 (local only)`。
- 范围边界：不改写P10 DR-1，不修改RP-1，不实施P11/P12；P11-W01继续`BLOCKED`，`task.dispatch`继续关闭。
- 基线：`c5ba5dfc231c2ef7eea12278c1e523a7c9c5a8ba`，开始时本地HEAD、upstream与worktree一致且干净。
- 修改文件：`src/ns_common/state_store/redis_provider.py`、`store.py`、`tests/test_redis_state_store_provider.py`、`tests/test_redis_state_store_integration.py`以及implementation plan、ADR-038和本acceptance log；`src/ns_runtime/delivery/`与`src/ns_runtime/routing/`相对基线零diff。

### Blocker closure

- B1 options trusted boundary：`RedisStateStoreOptions.__post_init__`直接复验exact backend、最长128且无NUL/CR/LF的exact username（允许空串default user）、finite positive exact int/float timeout、exact/credential-free/bounded endpoint、exact namespace与source类型。直接构造和`dataclasses.replace()`对backend/username/bool/NaN/±Inf/0/负数/endpoint/namespace/source及str/float subclass使用同一失败字段。
- B2 custom secret source：provider调用`resolve()`后只接受None或非空exact str；空串、bytes、object、coroutine和str subclass均typed拒绝，不做字符串转换。source异常、非法返回和真实driver认证失败均不输出secret、source repr、endpoint、username或driver文本。
- B3 lifecycle：`StateStore.open()/close()`对KeyboardInterrupt、SystemExit和任意自定义BaseException先恢复NEW/OPEN再原对象穿透；CancelledError与既有typed/timeout/Exception映射保持。timeout子Task只捕获非取消BaseException并把同一对象交回父Task抛出，避免事件循环提前逃逸且不持久保存异常。恶意password source与使用production `_execute`的恶意client `aclose()`矩阵验证失败后状态可解释，close依赖恢复后同一provider可重试关闭。
- B4 port ownership：删除bind-port-0后立即关闭的`_free_port`。集成类通过`NsTestResourceFactory.reserve_tcp_port()`持有reservation到Redis配置写完、`Popen`前最后一刻；PING后读取server INFO并核对`process_id == Popen.pid`。清理仍只SCAN+UNLINK当前随机namespace，production provider无FLUSHDB/FLUSHALL/KEYS。
- B5 recovery：Redis provider A分别完成3-target all accepted和501-target batched initialization，读取root/shard Summary与prepared DeliveryRecord证据后关闭并删除A的provider/service/request/plan/scope/key对象；独立provider B使用全新clock/plan/request/service/scope/key重读相同authority，revision token、state version、document SHA-256与payload evidence digest完全一致。B重复相同message_id+target fingerprint均返回duplicate，前后record key集合不变（分别6与504），没有第二套Summary/DeliveryRecord。
- B6 Valkey校准：真实server为`redis-server 6.0.16`；redis-py `8.0.1`和valkey-py `6.1.1`都对该Redis server完成协议认证/health。结论严格拆分为Redis standalone provider `VERIFIED`、Valkey driver compatibility `IMPLEMENTED`、Valkey server integration `UNVERIFIED`；本机无`valkey-server`。

### 本次实际命令与原始结果

- Provider专项：`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -m unittest tests.test_redis_state_store_provider tests.test_redis_state_store_integration -q`，最终代码复跑`Ran 23 tests in 6.646s`，`OK`。
- P08/P10/provider联合：`python -m unittest tests.test_state_store tests.test_runtime_state_store tests.test_runtime_delivery_admission tests.test_redis_state_store_provider tests.test_redis_state_store_integration -q`，最终代码复跑`Ran 62 tests in 10.577s`，`OK`。
- P03-P10联合：`modules=$(rg --files tests -g 'test_*.py' | sort | sed 's#/#.#g; s#\.py$##' | rg '^(tests\.test_runtime_protocol|tests\.test_.*transport|tests\.test_runtime_connection|tests\.test_runtime_session|tests\.test_.*iam|tests\.test_runtime_processor|tests\.test_.*state|tests\.test_runtime_routing|tests\.test_runtime_delivery)' | rg -v '^tests\.test_redis_'); PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -m unittest -q $modules`，加载46个模块，最终代码复跑`Ran 417 tests in 19.900s`，`OK`。
- Linux runtime标准asyncio：`modules=$(rg --files tests -g 'test_*.py' -g '!test_cache.py' | sort | sed 's#/#.#g; s#\.py$##'); PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -m unittest -q $modules`，最终代码复跑`Ran 791 tests in 42.952s`，`OK (skipped=1)`。
- Linux runtime uvloop：同一modules执行`PYTHONPATH=src /home/ns/.virtualenvs/ns_runtime_p09_rp1_review/bin/python -c 'import asyncio, unittest, uvloop; asyncio.set_event_loop_policy(uvloop.EventLoopPolicy()); unittest.main(module=None, verbosity=0)' $modules`，最终代码复跑`Ran 791 tests in 44.995s`，`OK (skipped=1)`。
- Linux backend：`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09_rp1_review/bin/python -m unittest discover -s tests -p 'test_*.py' -q`，最终代码复跑`Ran 791 tests in 30.577s`，`OK (skipped=50)`；runtime driver缺失使真实provider integration整类typed skip。
- 静态/依赖：`compileall -q src tests`、runtime/backend两环境`pip check`、`git diff --check`、cold import、production provider清库命令扫描、delivery/routing driver import AST扫描及相对基线零diff均通过；仅共享`127.0.0.1:6379` Redis进程在测试后保留。

### 当前结论与剩余限制

- P10-FIX-01、P10-FIX-02与P10恢复`VERIFIED/F3 (local only)`；本地证据随本次提交记录，明确属于`commit-recorded local evidence`，没有远程CI证明。
- 只关闭Redis standalone production provider及本次六项blocker。仍deferred/unverified：Valkey server integration、Sentinel、Cluster、failover、replica read、TLS证书/CA材料、lease/fencing、leader election、跨节点owner、P11 prepared->queued/claim/send、DeliveryAttempt及P12 ACK/NACK/Defer/timeout/retry。
- P11-W01继续`BLOCKED`；`task.dispatch`不在`_ENABLED_MESSAGE_TYPES`且production processor仍未注册，P12 ACK闭环前不得开启。

## P11 本地可靠投递调度与发送验收证据

- 工作包：`P11-W01`至`P11-W11`。
- 状态：`VERIFIED/F3 (local only)`；只完成本地write到`ack_waiting`，不代表ACK闭环或production可靠可用。
- 完成时间：`2026-07-23T00:22:16+08:00`。
- 基线：当前分支`codex/ns-runtime-implementation`的最新P10/P10-FIX VERIFIED基线`c3a74e0`，实施开始时worktree干净且与upstream一致。
- 修改文件：`src/ns_common/state_store/{authority,model,store,redis_provider,__init__}.py`、`src/ns_common/config/groups/runtime.py`、`src/ns_common/config/validation.py`、`etc/ns_config.example.json`、`src/ns_runtime/connection/lifecycle.py`、`src/ns_runtime/processor/integration.py`、`src/ns_runtime/delivery/`下P10 additive model/serde/store integration及P11 scheduling/store/workers/dispatch/local transport模块、`tests/_state_store_contract_model.py`、`tests/test_state_store.py`、`tests/test_redis_state_store_integration.py`、`tests/test_runtime_delivery_scheduling.py`，以及implementation plan、ADR-039和本acceptance log。

### P11-W01至W11完成映射

- W01：activation从StateStore typed scan读取prepared authority，按priority、batch、tenant/target/global queued水位分批转queued；activation evidence记录config/policy version、reason、batch/candidate count与UTC时间。大fanout不会一次全部激活。
- W02：ClaimWorker以revision/state-version CAS claim，DeliveryOwner持有local runtime/worker/token/lease。内存模型8 worker和真实Redis 16 worker并发均仅一个CLAIMED，duplicate claim不触发transport。
- W03：15s lease、5s renew、连续失败超过2次at_risk与4s保护窗口均为typed配置/authority；旧token、过期lease、risk owner停止新write。没有P17 fencing、remote transfer或第二worker lifecycle。
- W04：SendWorker每次重读authority，校验state、owner/lease、active session/connection_epoch/tenant/identity、payload evidence、config/policy version和expires_at；断连、identity mismatch、非法payload_ref、过期及恶意dependency在transport前fail closed。RoutingPlan未修改，Router未调用，target未重选。
- W05：queued -> sending、DeliveryAttempt create和root/shard Summary计数同一StateStore transaction；fake transport在调用点验证authority已是sending且attempt为writing，不能产生sending无attempt。
- W06：sending时记录ack_deadline；write timeout配置必须小于lease TTL。无timeout scanner、ACK timeout状态迁移或retry。
- W07：transport write成功只原子进入ack_waiting并把attempt标记write_succeeded；不存在sent/sent_success，transport success不等于delivery success。
- W08：write exception、timeout和shutdown interruption形成bounded typed failure并原子进入write_failed；异常正文不持久化。retry_scheduled只是拒绝公共构造的placeholder，production path无该迁移；dead letter未实现。
- W09：owner risk停止新write和同轮放大，仅允许已经sending的完成在保护窗口内提交；不形成新lease或ownership transfer。
- W10：prepared/queued/sending/ack_waiting/write_failed在每次原子迁移同步root/shard计数；authority重算与Summary交叉校验。prepared不占active/inflight，sending占active/write，ack_waiting占inflight。
- W11：LocalTaskDispatchExperimentalProcessor与bounded coordinator显式复用P01唯一TaskSupervisor和P05 connection owner；默认配置false、builtin task.dispatch production contract仍disabled，P12前不得production enable。

### 实际测试命令与原始结果

- P11/StateStore/config专项：`PYTHONPATH=src python3 -m unittest tests.test_state_store tests.test_runtime_delivery_scheduling tests.test_config -q`，最终复跑`Ran 67 tests in 0.909s`，`OK`。
- Redis provider/integration专项：`PYTHONPATH=src python3 -m unittest tests.test_redis_state_store_provider tests.test_redis_state_store_integration -q`，`Ran 24 tests in 8.004s`，`OK`。真实`redis-server`覆盖Lua索引、scan、P10 admit -> P11 activate及16 worker原子claim；Valkey仍只表示driver对Redis server的协议兼容，不是valkey-server证据。
- 全树：`python3 -m compileall -q src tests && PYTHONPATH=src python3 -m unittest discover -s tests -t . -q`，最终复跑`Ran 816 tests in 44.814s`，`OK (skipped=1)`；跳过项为既有平台条件，不是P11失败。
- 差异：`git diff --check`成功；行尾只出现Git工作区LF/CRLF转换提示，没有whitespace error。
- 以上全部是当前WSL工作区的local verification；没有远程CI结果，不据此声明远程或生产环境通过。

### 安全、恢复与禁止项结论

- public model直接构造、`dataclasses.replace()`非法状态、reserved retry_scheduled、自定义dependency返回mapping/object、fake transport试图绕过迁移均fail closed。
- runtime shutdown取消发生在write中时，attempt和DeliveryRecord原子落typed`shutdown_interrupted/write_failed`；StateStore冲突发生在transport前不写，transport后authority冲突保持sending歧义供后续阶段处理，不伪造成功。
- 本阶段没有改写RP-1、调用Router、选择新target、绕过IAM/payload evidence、把queued当connection write queue、创建第二TaskSupervisor/event loop/shutdown owner，或开启production task.dispatch。

### 当前限制与下一工作包

- 明确未实现：P12 ACK/NACK/Defer、AckRecord、acked、ACK timeout scanner、自动retry及retry budget；P13 DeadLetterRecord/replay/一般cancel/hold；P14 health scoring/fair scheduling；P17 lease/fencing/leader coordination；master query、remote forwarding、cluster与跨runtime owner。
- P11 local owner lease不允许无fencing的过期owner接管；旧/过期owner只会fail closed。跨shutdown的安全ownership recovery必须等待后续fencing/恢复设计，不能伪造transfer。
- inline payload正文按P10冻结规则不进入StateStore；P11 payload validator/resolver是显式可信依赖，local experiment必须提供能按DeliveryRecord evidence返回内容的authority adapter。本阶段不把内存cache升级为可靠payload authority。
- 下一工作包：`P12-W01`保持`BLOCKED`，等待独立授权。ACK闭环完成并重新验收前，可靠投递只能陈述为“写入目标并进入ack_waiting”，不得陈述为成功送达。

## P10-FIX-03 + P11-FIX-01 联合修复启动记录

- 工作包：`P10-FIX-03 + P11-FIX-01`。
- 状态：`IN_PROGRESS`；既有P10/P11 `VERIFIED`结论在修复及联合复验期间撤回。
- 开始时间：`2026-07-23`（Asia/Shanghai）。
- 基线：分支`codex/ns-runtime-implementation`，启动HEAD `61d7bee21b6589493d1cfae9751feee3e7ba107c`，worktree启动时干净且与upstream一致。
- 复核发现：普通fanout仍强制root+shard、阈值/批量参数分散硬编码；inline请求fingerprint未绑定canonical内容且可靠inline无durable body authority；payload_ref验证未绑定目标；P11仍依赖全scan/app排序、进程known tenants、CAS claim无fencing、调用者布尔renew和raw wire_text信任，未提供Hash+ready/lease/ack ZSet+Summary+append-only log同原子事务。
- 冻结边界：ENV-1、PC-1、IAM-R1、RP-1与P08 authority boundary不改；不调用Router、不重选target、不修改RoutingPlan；production `task.dispatch`保持disabled。
- 明确不实施：P12 ACK/NACK/Defer/timeout/retry、P13 DLQ/replay/cancel/hold、P14健康评分/公平调度、P17 leader/cluster fencing、remote/master/cluster，以及第二TaskSupervisor/event loop/shutdown owner。
- 恢复条件：完成源码与新增测试、真实Redis原子/恢复证据、P03-P11和全树标准asyncio/uvloop/backend回归、compile/pip/diff/cold-import/banned-scan，并更新ADR/plan/acceptance log；任一失败则保持`IN_PROGRESS`。

## P10-FIX-03 + P11-FIX-01 联合修复最终验收证据

- 工作包：`P10-FIX-03 + P11-FIX-01`；状态：`VERIFIED/F3 (local only)`。
- 完成时间：`2026-07-23T01:32:00+08:00`。
- 基线：分支`codex/ns-runtime-implementation`，启动HEAD `61d7bee21b6589493d1cfae9751feee3e7ba107c`，启动worktree干净且与upstream一致。
- 修改文件：`src/ns_common/state_store/{__init__,authority,model,store,redis_provider}.py`；`src/ns_runtime/connection/lifecycle.py`；`src/ns_runtime/delivery/{__init__,dispatch,models,payload_authority,policy,response,scheduling,scheduling_store,serde,service,store,workers}.py`；`tests/{_state_store_contract_model,test_state_store,test_redis_state_store_integration,test_runtime_delivery_admission,test_runtime_delivery_scheduling}.py`；implementation plan、ADR-040和本日志。

### P10-FIX-03关闭映射

- Summary与fanout：合同家族保持DR-1，持久schema显式升级为`dr-2`；legacy `dr-1`读取返回`migration_required`。状态闭集纠正为initializing/pending/ACK后续终态；普通fanout只有一个Summary且DeliveryRecord直接指向root，只有超过每条policy decision冻结阈值的大fanout才产生root+shard。
- typed policy：fanout threshold、shard bucket、initialization batch和activation batch统一由`AdmissionPolicyConfig`裁决并写入`AdmissionPolicyDecision`；公共构造、`dataclasses.replace()`和自定义policy返回的非法组合全部复验。
- payload authority：inline request fingerprint绑定canonical正文、digest、size与policy limits；可靠inline正文独立写入`payload_body` durable authority，record/log/audit只存body_ref与摘要，发送前重读并复验。payload_ref请求/结果绑定request fingerprint和具体target fingerprint，旧result、错target、mapping/object/subclass均fail closed。
- dependency/迁移：dependency outcome闭集为reject、wait_required、dead_letter_required、dependency_unavailable，只表达P10受理裁决，不创建P13 record；serde对dr-2严格重算跨对象authority和payload/target binding。

### P11-FIX-01与P11-W01至W11关闭映射

- W01：prepared activation只分页读StateStore有序索引，按priority、tenant/target/global水位及record policy snapshot分批；无record全scan、known-tenant集合或应用层全量排序。过期prepared原子转expired并移出prepared索引，activation evidence记录版本与原因。
- W02：claim把DeliveryRecord、ready/claimed/lease、target/global索引和transition log放入同一provider-neutral transaction；多worker只有一个owner，duplicate claim不触发transport，owner含单调per-delivery fencing。
- W03：LeaseRenewWorker在既有唯一TaskSupervisor下运行真实Clock续约；旧fencing拒绝。expired queued只允许同local runtime以更高fencing恢复，expired sending转write_uncertain且不重写，ack_waiting只恢复owner、不重发；没有P17 leader fencing或ownership transfer。
- W04：SendWorker每次重读authority并核对status、owner/fencing、active connection/session/epoch/tenant/identity、payload evidence、record config/policy snapshot和expires_at；不修改RoutingPlan、不调用Router、不重选target、不绕过IAM/payload validation。
- W05：queued -> sending、DeliveryAttempt create、Summary计数和索引/log在同一事务；attempt绑定owner fencing、config/policy、target。fake transport只能在权威sending+writing attempt之后被调用，不存在sending无attempt。
- W06-W07：进入sending时只记录ack_deadline；完整typed Envelope由冻结authority重建并canonicalize。transport write success只原子进入ack_waiting/write_succeeded，不产生sent_success，也不解释为delivery success。
- W08：precheck按expired/payload_rejected/target_waiting形成typed权威终态；write error/timeout/shutdown形成typed failure。write后提交冲突转write_uncertain，禁止盲目重写；retry_scheduled无production transition，dead letter/retry均未实现。
- W09：owner risk与保护窗口阻止新write和风险放大；旧per-delivery fencing不能写。它不是P17 lease/fencing，不允许跨runtime transfer。
- W10：prepared/ready+claimed/sending/ack/failed索引与Summary在每次迁移同步；prepared不占active/inflight，sending占active，ack_waiting占inflight。Redis事务冲突验证无record/index/log孤儿。
- W11：local experimental processor仍只接受显式注入并复用P01唯一TaskSupervisor/P05 connection owner；builtin production `task.dispatch`继续disabled，P12完成前不得production enable。

### 实际测试命令与真实结果

- P10/P11定向：`PYTHONPATH=src python3 -m unittest tests.test_runtime_delivery_admission tests.test_runtime_delivery_scheduling -q`，最终`Ran 37 tests in 3.793s`，`OK`。覆盖公共构造/replace、typed policy、dr-1迁移拒绝、请求与target replay、prepared batch/水位/过期终结、并发/duplicate claim、真实renew、fencing恢复、disconnect/payload/expiry/config snapshot、durable inline authority与完整Envelope、write success/failure/uncertain、shutdown与资源计数。
- Redis provider/integration：`PYTHONPATH=src python3 -m unittest tests.test_redis_state_store_provider tests.test_redis_state_store_integration -q`，最终`Ran 25 tests in 7.680s`，`OK`；uvloop同组`Ran 25 tests in 10.254s`，`OK`。真实隔离`redis-server`覆盖原子投影claim、冲突零record/index/log孤儿，以及关闭provider A后由独立provider B重建claim和计数。
- 标准asyncio全树：`python3 -m compileall -q src tests && PYTHONPATH=src python3 -m unittest discover -s tests -t . -q`，最终`Ran 826 tests in 45.750s`，`OK (skipped=1)`。
- runtime uvloop：按DEP-1排除Django-only `test_cache.py`，最终`Ran 815 tests in 44.465s`，`OK (skipped=1)`。首次运行的真实Redis 16-worker压力用例触发测试provider的1s typed timeout；未记为通过。将该测试预算校准为5s后，先复跑Redis 25项通过，再完整复跑通过。
- backend/Django全树：`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09_rp1_review/bin/python -m unittest discover -s tests -p 'test_*.py' -q`，最终`Ran 813 tests in 28.418s`，`OK (skipped=50)`；skips为backend清单未安装runtime可选依赖等既有边界。
- 依赖与静态：runtime/backend两环境`python -m pip check`均输出`No broken requirements found.`；`compileall`通过。最终`git diff --check`、cold-import与禁止项扫描在提交前执行，只有成功才保留本记录的VERIFIED状态。
- 全部证据仅为当前WSL/local verification；没有远程CI，不能据此声明远程环境或production可靠可用。

### 未实现限制

- P11只完成`prepared -> queued -> sending -> ack_waiting`及失败/歧义保护；ACK闭环仍属于P12。未实现ACK/NACK/Defer、AckRecord、ACK timeout scanner、retry worker/budget或delivery success终态。
- 未实现P13 DeadLetterRecord/replay/一般cancel/hold、P14 health scoring/fair scheduling、P17 leader lease/cluster fencing、master query、remote forwarding、cluster/跨runtime ownership，未创建第二TaskSupervisor/event loop/shutdown owner。
- Redis证据只覆盖standalone；Valkey仍只是driver对Redis server兼容，未声明valkey-server、Sentinel、Cluster、failover或replica read。production `task.dispatch`继续disabled。

## P10-FIX-04 + P11-FIX-02 联合修复启动记录

- 工作包：`P10-FIX-04 + P11-FIX-02`。
- 状态：`IN_PROGRESS`；P10/P11既有`VERIFIED/F3 (local only)`结论在修复和联合复验期间撤回，P12继续`BLOCKED`。
- 开始时间：`2026-07-23`（Asia/Shanghai）。
- 基线：分支`codex/ns-runtime-implementation`，启动HEAD与upstream均为`69ae4188dab7277b47775fbb18bd56fbfaff6834`，worktree启动时干净。
- 复核范围：ProcessorContext安全Envelope authority与目标Session协商protocol；tenant+bucket Redis Cluster slot布局及旧key迁移门禁；独立持久fencing/owner epoch；lease/ACK deadline分离；indeterminate reconcile；ordered-index分页和bounded activation；非终态waiting与分类Summary计数；单次bounded inline descriptor；P11 payload实时target access binding。
- 冻结边界：ENV-1、PC-1、IAM-R1、RP-1和P08 StateStore抽象不迁移owner；不调用Router、不重选target、不修改RoutingPlan；production `task.dispatch`继续disabled。
- 明确不实施：P12 ACK/NACK/Defer/timeout/retry、P13 DLQ/replay/cancel/hold、P14健康/公平调度、P17 leader/cluster coordination、remote/master routing，以及第二TaskSupervisor/event loop/shutdown owner。
- 恢复条件：十项源码与指定测试、真实Redis standalone回归、Redis key-slot证明、provider A/B恢复、P03-P11与asyncio/uvloop/backend全量、compileall/pip/diff/cold-import/banned scan全部通过并完成ADR/plan/log；任一证据缺失则保持`IN_PROGRESS`。

## P10-FIX-04 + P11-FIX-02 联合验收记录

- 工作包：`P10-FIX-04 + P11-FIX-02`。
- 状态：`VERIFIED / F3 (local only)`；P10/P11恢复VERIFIED，P12继续`BLOCKED`，production `task.dispatch`继续disabled。
- 完成时间：`2026-07-23`（Asia/Shanghai）。本记录只有local verification，没有远程CI，不声明CI passed或production可靠投递闭环完成。
- Envelope authority：admission从ProcessorContext保存原始typed protocol/message/source/auth_context/trace及安全fingerprint；StateStore不保存raw identity/token。发送原样复用source/auth/message/trace，并与当前P05 target协商protocol/schema做exact compatibility；target runtime不能冒充source，permission snapshot不能由IAM decision字段伪造。
- Cluster-key布局：policy冻结8为默认的配置化bucket count，message稳定派生bucket id；同一Lua KEYS的revision/record/scan/ordered/log全部使用精确`{tenant_id:bucket_id}`，不再写system global ZSet。旧无tag record只返回typed `legacy_physical_key_migration_required`。key-slot证据不代表实现Redis Cluster运行、leader或failover。
- owner/lease/reconcile：DeliveryRecord独立持久化last_fencing/owner_epoch，release、expired reclaim与ACK owner恢复严格递增；lease index与ACK deadline完全分离。transport成功后的indeterminate commit按ACK_WAITING接受、SENDING转WRITE_UNCERTAIN、其他状态typed conflict三分支处理。
- activation/waiting/accounting：ordered index提供typed cursor/start-after；activation在bounded scan budget内跨页清理无效成员并越过blocked候选。TARGET_WAITING拥有独立index/count且不计write failure；expired、payload rejected、write failed、write uncertain分别计数。P12 Summary状态当前拒绝构造。
- payload边界：inline在request边界只生成一次bounded typed descriptor，cycle、超深、NaN/Inf、非法类型与超限稳定rejected/failed。P11 payload validation绑定request、target和当前target access decision，旧结果与跨target replay在transport前拒绝。

### 实际测试命令与真实结果

- P10/P11定向：`PYTHONPATH=src python3 -m unittest tests.test_runtime_delivery_admission tests.test_runtime_delivery_scheduling -q`，最终`Ran 45 tests in 22.580s`，`OK`。覆盖public construct/replace、Envelope字段交换与target冒充、protocol/access replay、prepared batch/watermark/cursor starvation、并发/duplicate claim、fencing复用、lease/ACK分离、indeterminate三分支、waiting/失败分类、shutdown和fake transport门禁。
- 真实Redis standalone：`PYTHONPATH=src python3 -m unittest tests.test_redis_state_store_integration`，最终`Ran 15 tests in 15.119s`，`OK`。覆盖Lua原子冲突零record/index/log孤儿、Cluster key-slot计算、legacy migration门禁、501-target分批初始化，以及关闭provider A后由独立provider B重建authority。
- 标准asyncio全树：`PYTHONPATH=src python3 -m unittest discover -s tests -q`，最终代码复跑`Ran 836 tests in 73.001s`，`OK (skipped=1)`；跳过为既有平台条件。
- runtime uvloop：显式安装`uvloop.EventLoopPolicy()`并按DEP-1排除Django-only `test_cache.py`，最终代码复跑`Ran 825 tests in 74.115s`，`OK (skipped=1)`。
- backend/Django全树：`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09_rp1_review/bin/python -m unittest discover -s tests -p 'test_*.py' -q`，最终代码复跑`Ran 821 tests in 47.236s`，`OK (skipped=50)`；skips为backend清单未安装runtime可选driver等既有边界。
- 依赖与静态：最终`python3 -m compileall -q src tests`、runtime/backend `python -m pip check`、`git diff --check`、cold-import及禁止项扫描在提交前执行；只有成功才保留本记录VERIFIED状态。

### 未实现限制

- P11只完成`prepared -> queued -> sending -> ack_waiting`及typed waiting/failure/uncertain保护；transport write成功不等于delivery success。P12 ACK/NACK/Defer、AckRecord、ACK timeout scanner、retry worker/budget与成功终态均未实现。
- P13 DeadLetterRecord/replay/一般cancel/hold、P14 health scoring/fair scheduling、P17 leader lease/cluster fencing、Redis Cluster运行、master query、remote forwarding、跨runtime ownership均未实现；没有第二TaskSupervisor/event loop/shutdown owner。
- Redis服务证据仍为standalone；Valkey只是driver compatibility，不声明valkey-server、Sentinel、Cluster、failover或replica read。production `task.dispatch`继续disabled。

## P10-FIX-05 + P11-FIX-03 联合修复启动记录

- 工作包：`P10-FIX-05 + P11-FIX-03`。
- 状态：`IN_PROGRESS`；P10/P11既有`VERIFIED/F3 (local only)`结论在修复和联合复验期间撤回，P12继续`BLOCKED`，production `task.dispatch`继续disabled。
- 开始时间：`2026-07-23`（Asia/Shanghai）。
- 基线：分支`codex/ns-runtime-implementation`，启动HEAD与upstream均为`0003eaa495f6045b4b1f10c89f31d4096b925464`，worktree启动时干净。
- 复核范围：可恢复runtime tenant/layout registry和真正global watermark；跨bucket activation/claim/lease recovery公平性；authority layout version/generation与8→16迁移门禁；出站MessageGroup策略字段authority；post-write StateStore冲突统一reconcile；payload_ref实时object access decision绑定。
- 冻结边界：ENV-1、PC-1、IAM-R1、RP-1和P08 StateStore owner保持；不调用Router、不重选target、不修改RoutingPlan；不新增第二TaskSupervisor/event loop/shutdown owner。
- 明确不实施：P12 ACK/NACK/Defer/timeout/retry、P13 DLQ/replay/cancel/hold、P14健康/公平调度、P17 leader/cluster coordination、remote/master routing或production task.dispatch enable。
- 恢复条件：源码和指定竞争/迁移测试、真实Redis standalone与provider A/B恢复、P03-P11、asyncio/uvloop/backend全量、compileall/pip/diff/cold-import/banned scan全部通过并完成ADR/plan/log；任一证据缺失则保持`IN_PROGRESS`。

## P10-FIX-05 + P11-FIX-03 联合验收记录

- 工作包：`P10-FIX-05 + P11-FIX-03`。
- 状态：`VERIFIED / F3 (local only)`；P10/P11恢复VERIFIED，P12继续`BLOCKED`，production `task.dispatch`继续disabled。
- 完成时间：`2026-07-23`（Asia/Shanghai）。启动基线为`0003eaa495f6045b4b1f10c89f31d4096b925464`；本记录只有local verification，没有远程CI，不声明CI passed或ACK可靠投递闭环完成。
- 修改文件：`docs/ns_runtime_architecture_decisions_0.0.2.md`、`docs/ns_runtime_implementation_plan_for_design_0.0.2.md`、`docs/ns_runtime_acceptance_log_0.0.2.md`；`src/ns_common/config/groups/runtime.py`、`validation.py`、`state_store/redis_provider.py`；`src/ns_runtime/delivery/authority_layout.py`、`__init__.py`、`models.py`、`payload_authority.py`、`policy.py`、`scheduling.py`、`scheduling_store.py`、`serde.py`、`service.py`、`store.py`、`workers.py`；三份delivery/Redis测试文件。
- layout与全局authority：新增typed layout version/generation、restart-required配置、持久runtime layout/tenant registry和generation物理partition；admission/scheduler从StateStore权威注册表恢复tenant集合并跨全部tenant/bucket重建runtime-global queued水位。8到16、layout/generation不匹配以及上一代tagged Redis record均typed migration-required，不静默混读。
- activation/claim/recovery：同一local scheduler activation coordinator串行激活，在全局scan budget内给所有bucket有界首页并轮转cursor；claim每次轮转bucket并先处理expired lease，持续ready的低号桶不再遮蔽后桶。没有system global ZSet、跨slot transaction、P14通用公平调度或P17 ownership transfer。
- message/payload/write reconcile：出站MessageGroup保留identity/type/category/created_at，但priority/reliability/expiry从冻结policy重建。payload_ref validation绑定对象/version/checksum/request、target、当前permission snapshot和实际IAM access decision。transport成功后的任何StateStore error统一重读：匹配ACK_WAITING接受、SENDING转WRITE_UNCERTAIN、其他typed conflict；对账读取失败返回WRITE_OUTCOME_UNKNOWN，不盲写或重发。
- P11-W01至W11：既有prepared分批激活、原子claim、local lease/renew、发送前权威校验、queued到sending与attempt一致、ack deadline、write成功只到ack_waiting、typed write failure、owner risk窗口、资源计数和本地实验dispatch全部保持；本修复补齐跨tenant/global、跨bucket/layout、策略消息、payload IAM与写后冲突恢复证据。

### 实际测试命令与真实结果

- P10/P11定向：`PYTHONPATH=src python3 -m unittest -q tests.test_runtime_delivery_admission tests.test_runtime_delivery_scheduling`，`Ran 51 tests in 36.257s`，`OK`。覆盖public直接构造、`dataclasses.replace()`、非法dependency、fake transport、多worker/duplicate claim、prepared批量/水位、跨tenant global watermark、跨bucket激活、target disconnect、payload_ref、expires_at、owner risk、write success/failure/uncertain、shutdown与StateStore冲突。
- 真实Redis standalone：`PYTHONPATH=src python3 -m unittest -q tests.test_redis_state_store_integration`，`Ran 16 tests in 26.546s`，`OK`。覆盖Lua原子冲突、provider A/B恢复、runtime registry重建、8到16门禁及上一代tagged key迁移检测。
- 标准asyncio全树：`PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -q`，`Ran 843 tests in 98.231s`，`OK (skipped=1)`；跳过为既有平台条件。
- runtime uvloop：显式安装`uvloop.EventLoopPolicy()`并按DEP-1排除Django-only `test_cache.py`，`Ran 832 tests in 105.462s`，`OK (skipped=1)`。
- backend/Django全树：`PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09_rp1_review/bin/python -m unittest discover -s tests -p 'test_*.py' -q`，`Ran 827 tests in 60.694s`，`OK (skipped=50)`；skips为backend环境未安装runtime可选依赖等既有边界。
- 依赖与静态：`python3 -m compileall -q src tests`通过；runtime/backend两环境`python -m pip check`均为`No broken requirements found.`；delivery cold import输出`DELIVERY_COLD_IMPORT=OK`；RP-1相对基线零diff；P12+禁止项新增源码扫描为`NO_MATCH`；`git diff --check`通过。

### 未实现限制

- P11只完成`prepared -> queued -> sending -> ack_waiting`及typed waiting/failure/uncertain保护；transport write成功不等于delivery success。P12 ACK/NACK/Defer、AckRecord、ACK timeout scanner、retry worker/budget与成功终态均未实现。
- P13 DeadLetterRecord/replay/一般cancel/hold、P14 health scoring/fair scheduling、P17 leader lease/cluster fencing、Redis Cluster运行、master query、remote forwarding、跨runtime ownership均未实现；没有第二TaskSupervisor/event loop/shutdown owner。
- Redis服务证据仍为standalone；Valkey只是driver compatibility，不声明valkey-server、Sentinel、Cluster、failover或replica read。production `task.dispatch`继续disabled。

## P11-FIX-04 修复启动记录

- 工作包：`P11-FIX-04`。
- 状态：`IN_PROGRESS`；P10保持`VERIFIED/F3 (local only)`，P11既有VERIFIED结论在修复与联合复验期间撤回；P12继续`BLOCKED`，production `task.dispatch`继续disabled。
- 开始时间：`2026-07-23`（Asia/Shanghai）。
- 基线：分支`codex/ns-runtime-implementation`，启动HEAD与upstream均为`3ad2cd5d57d862f2177659e1d336164584b16be7`，worktree启动时干净。
- 复核范围：prepared/ready/lease ordered-index跨调用及跨provider重建进展、同bucket stale投影原子修复与安全日志；transport成功后的completion异常全闭集reconcile；production payload_ref实时IAM access decision evidence及完整绑定。
- 冻结边界：ENV-1、PC-1、IAM-R1、RP-1、P08 StateStore与P10 admission contract保持；不调用Router、不重选target、不修改RoutingPlan；不新增TaskSupervisor、event loop或shutdown owner。
- 明确不实施：P12 ACK/NACK/Defer/timeout/retry、P13 DLQ/replay/cancel/hold、P14健康/公平调度、P17 leader/cluster coordination、remote/master routing或production task.dispatch enable。
- 恢复条件：源码与指定攻击面测试、真实Redis standalone/provider A-B恢复、P03-P11、asyncio/uvloop/backend全量、compileall/pip/diff/cold-import/banned scan全部通过并完成ADR/plan/log；任一证据缺失则保持`IN_PROGRESS`。

## P11-FIX-04 最终验收记录

- 工作包：`P11-FIX-04`。
- 状态：`VERIFIED / F3 (local only)`；P10继续`VERIFIED/F3 (local only)`，P11恢复VERIFIED，P12继续`BLOCKED`，production `task.dispatch`继续disabled。
- 完成时间：`2026-07-23`（Asia/Shanghai）。启动基线为`3ad2cd5d57d862f2177659e1d336164584b16be7`；本记录只有local verification，没有远程CI，不声明CI passed、production可靠可用或ACK可靠投递闭环完成。
- 修改文件：implementation plan、ADR-043、本验收日志；`src/ns_runtime/connection/lifecycle.py`；`src/ns_runtime/delivery/payload_authority.py`、`scheduling.py`、`scheduling_store.py`、`workers.py`；`tests/test_runtime_delivery_scheduling.py`、`tests/test_redis_state_store_integration.py`。
- ordered-index进展与修复：prepared、ready、lease及bucket rotation使用StateStore持久CAS cursor，跨调用、scheduler重建和Redis provider A/B继续推进；cursor失效按权威索引重锚。缺record/malformed、错误状态、owner缺失、foreign owner和旧lease score只在可证明投影分歧时同scope原子remove/repair，风险项写quarantine；安全日志只写member digest、固定reason和布尔元数据。backend unavailable或migration错误不触发误修复。
- 写后对账：transport返回成功后的所有typed completion StateStore/state异常都重读DeliveryRecord与当前DeliveryAttempt，并校验attempt id/count、原claim token、fencing和owner epoch。已提交ACK_WAITING即使lease随后过期仍接受；仍为SENDING即使lease过期或owner被更高fencing替换也只转WRITE_UNCERTAIN；其他状态typed conflict或WRITE_OUTCOME_UNKNOWN，不重发、不伪造成功。
- payload IAM evidence：新增production `IamDeliveryPayloadReferenceValidator`，实时调用`IamClient.validate_payload_ref`与`access_check`；typed `PayloadAccessDecisionEvidence`绑定对象/version/checksum、request、target/session/identity、当前permission snapshot/fingerprint/version、IAM decision/time/expiry。denied、expired、旧version、非法dependency及`dataclasses.replace()`篡改均在transport前fail closed。
- 冻结边界：ENV-1、PC-1、IAM-R1、RP-1、P08 authority owner和P10 DR-1/prepared初始化未改变；没有调用Router、重选target、修改RoutingPlan，也没有新增TaskSupervisor、event loop或shutdown owner。

### 实际测试命令与真实结果

- P10/P11定向：`PYTHONPATH=src python3 -m unittest -q tests.test_runtime_delivery_admission tests.test_runtime_delivery_scheduling`，最终`Ran 56 tests in 43.439s`，`OK`。新增覆盖prepared cursor跨scheduler重建、ready前16条existing wrong-status后第17条claim、lease前16条foreign owner后第17条恢复、stale repair安全日志、lease在transport返回后过期、已提交ACK后lease过期、高fencing replacement、production IAM evidence及公共replace篡改。
- 真实Redis standalone：`PYTHONPATH=src python3 -m unittest -q tests.test_redis_state_store_integration`，`Ran 16 tests in 44.692s`，`OK`；其中provider A/B专项单独复跑`Ran 1 test in 40.504s`，`OK`。关闭provider A后，全新provider B读取持久cursor并继续activation与claim；证据仍只表示Redis standalone。
- 标准asyncio全树：`PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -q`，最终`Ran 848 tests in 128.535s`，`OK (skipped=1)`；跳过为既有平台条件。
- runtime uvloop：按DEP-1排除Django-only `test_cache.py`，显式安装`uvloop.EventLoopPolicy()`后运行同一模块集，最终`Ran 837 tests in 148.447s`，`OK (skipped=1)`。
- backend/Django全树首次运行`Ran 832 tests in 70.756s`，出现既有`test_django_timeout_default_uses_common_default_ttl` SQLite cache TTL时间敏感失败；该用例立即单独复跑`Ran 1 test in 1.273s`，`OK`，随后同一完整命令顺序复跑`Ran 832 tests in 71.132s`，`OK (skipped=50)`。该初次失败不计作通过且在此保留真实记录。
- 依赖与静态：`python3 -m compileall -q src tests`、runtime/backend两个项目隔离环境`python -m pip check`、`git diff --check`均通过；cold import输出`DELIVERY_COLD_IMPORT=OK`，RP-1相对基线为`RP1_ZERO_DIFF=OK`，P12+禁止项新增源码扫描为`NO_MATCH`。未限定的系统`python3 -m pip check`另报告宿主`pygobject`缺少`pycairo`；该解释器不是项目隔离环境，未把此宿主依赖问题记为通过，项目要求的两环境均实际输出`No broken requirements found.`。

### P11-W01至W11完成映射

- W01：持久prepared cursor、bounded scan、跨provider继续推进和stale修复补齐既有分批激活、水位、版本与原因记录。
- W02：ready cursor越过错误状态前缀后仍由权威事务唯一claim；多worker与duplicate claim保持。
- W03：lease cursor越过不可恢复前缀并只恢复同local runtime；没有P17 fencing或伪造transfer。
- W04：发送前继续重读status/owner/session/target/payload/config/expiry；payload_ref增加实时IAM证据完整绑定。
- W05：queued -> sending和DeliveryAttempt继续同一事务；fake transport不能绕过。
- W06-W07：ack deadline只记录；transport success只进入ack_waiting，写后异常按attempt authority对账。
- W08：write failure继续typed一致；没有production retry_scheduled或dead letter。
- W09：risk窗口继续阻止扩大写入；expired/higher-fencing post-write只进入uncertain或接受已提交ACK。
- W10：prepared/queued/active/inflight计数迁移保持原子；新增cursor/repair不伪造资源计数。
- W11：local experimental feature保持显式注入和默认false；P12前禁止production enable。

### 未实现限制

- P11只完成`prepared -> queued -> sending -> ack_waiting`以及typed waiting/failure/uncertain保护；transport write成功不等于delivery success。P12 ACK/NACK/Defer、AckRecord、ACK timeout scanner、retry worker/budget与delivery success终态均未实现。
- P13 DeadLetterRecord/replay/一般cancel/hold、P14 health scoring/fair scheduling、P17 leader lease/cluster fencing、Redis Cluster运行、master query、remote forwarding、跨runtime ownership均未实现；没有第二TaskSupervisor/event loop/shutdown owner。
- Valkey仍只是driver compatibility，不声明valkey-server、Sentinel、Cluster、failover或replica read；production `task.dispatch`继续disabled。

## P11-FIX-05 修复启动记录

- 工作包：`P11-FIX-05`。
- 状态：`IN_PROGRESS`；P10保持`VERIFIED/F3 (local only)`，P11既有VERIFIED结论在修复与联合复验期间撤回；P12继续`BLOCKED`，production `task.dispatch`继续disabled。
- 开始时间：`2026-07-23`（Asia/Shanghai）。
- 基线：分支`codex/ns-runtime-implementation`，启动HEAD与upstream均为`da72879cf365cfae211d13277f519d412207957f`，worktree启动时干净。
- 复核范围：StateTransaction provider-neutral只读前置断言及Redis/model零落地原子性；prepared/ready/lease repair TOCTOU；cursor逻辑身份与旧cursor迁移门禁；LeaseRenewWorker显式stop authority；不可公共伪造的payload IAM evidence和backend对象级ACL/policy判定。
- 冻结边界：ENV-1、PC-1、IAM-R1、RP-1、P08 authority owner和P10 admission语义保持；不调用Router、不重选target、不修改RoutingPlan；不新增TaskSupervisor、event loop或shutdown owner。
- 明确不实施：P12 ACK/NACK/Defer/timeout/retry、P13 DLQ/replay/cancel/hold、P14健康/公平调度、P17 leader/cluster coordination、remote/master routing或production task.dispatch enable。
- 恢复条件：源码与指定竞争/迁移/攻击面测试、P08 conformance、真实Redis standalone/provider A-B恢复、P03-P11、asyncio/uvloop/backend全量、compileall/两项目环境pip/diff/cold-import/banned scan全部通过并完成ADR/plan/log；任一证据缺失则保持`IN_PROGRESS`。

## P11-FIX-05 最终验收记录

- 工作包：`P11-FIX-05`。
- 状态：`VERIFIED / F3 (local only)`；P10保持`VERIFIED/F3 (local only)`，P11恢复VERIFIED，P12继续`BLOCKED`，production `task.dispatch`继续disabled。
- 完成时间：`2026-07-23`（Asia/Shanghai）。启动基线为`da72879cf365cfae211d13277f519d412207957f`；本记录只有local verification，没有远程CI，不声明CI passed、production可靠可用或ACK可靠投递闭环完成。
- 修改文件：implementation plan、ADR-044、本验收日志；backend IAM runtime contract/internal service/URL/view；common IAM及StateStore public model/store/Redis provider；runtime delivery dispatch/payload authority/scheduling/store/workers和IAM client；StateStore contract、backend IAM、Redis integration、delivery scheduling与IAM client测试。
- 原子前置断言与repair：`StateTransaction`新增typed record和ordered-index read assertion；deterministic contract model与Redis Lua都在revision分配及任何record/index/log写入前一次性校验，冲突零落地。prepared/ready/lease repair绑定已观察record revision/state-version与member exact score；missing/malformed在提交前重读并绑定absent或精确record，release、renew、create竞争胜出时不误删、不覆盖、不写错误repair log。
- cursor与renew生命周期：scheduler cursor v2的逻辑StateKey和payload共同绑定layout generation、bucket、operation和index identity；发现旧name-only cursor返回显式migration-reset-required。`LeaseRenewWorker.schedule()`返回supervisor-owned typed handle；precheck/risk/write failure/unknown与异常路径显式stop/join，unknown不继续扩大租约，lease到期后由既有authority恢复为WRITE_UNCERTAIN；ACK_WAITING在P12前仍按既有边界续租。
- payload IAM authority：`PayloadAccessDecisionEvidence`只能由module-private issuer在专用`IamClient.revalidate_payload_ref()`成功返回精确typed backend decision后签发；公共直接构造与`dataclasses.replace()`不能伪造。请求精确绑定对象/version/checksum/size、payload tenant、target principal/fingerprint和permission snapshot/version，不再使用source/owner identity digest。backend先读取live payload provider metadata，再以`payload_ref.read`对精确object id执行Resource ACL/policy；无provider、unavailable、deny、旧snapshot、跨tenant/object/target均在transport前fail closed。
- 冻结边界：ENV-1、PC-1、IAM-R1、RP-1、P08 authority owner和P10 DR-1/tenant dedup/prepared初始化语义未改变；未调用Router、未重选target、未修改RoutingPlan，也未新增TaskSupervisor、event loop或shutdown owner。

### 实际测试命令与真实结果

- P10/P11定向：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_runtime_delivery_admission tests.test_runtime_delivery_scheduling`，`Ran 60 tests in 48.671s`，`OK`。覆盖公共构造/replace、非法dependency、fake transport、多worker/duplicate claim、prepared批量/水位、send前authority、disconnect、payload_ref、expires_at、owner risk、write success/failure/unknown、renew停止与shutdown恢复。
- P08 contract/provider：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_state_store tests.test_runtime_state_store tests.test_redis_state_store_provider`，`Ran 37 tests in 0.862s`，`OK`；另有`tests.test_state_store tests.test_redis_state_store_provider`组合`Ran 28 tests`，`OK`。覆盖公共assertion模型、namespace/capability门禁、deterministic原子冲突和provider投影路径。
- 真实Redis standalone：`PYTHONPATH=src python3 -m unittest -q tests.test_redis_state_store_integration`，`Ran 17 tests in 53.948s`，`OK`；新增真实Lua assertion竞争专项也单独通过。覆盖assertion冲突零record/index/log孤儿、repair竞争、provider A/B恢复和既有布局迁移门禁。
- P03-P11定向模块集合：按protocol/transport/connection/session/IAM/processor/state/routing/delivery模块筛选并排除真实Redis模块，`Ran 465 tests in 51.672s`，`OK`。
- 标准asyncio全树：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -q`，`Ran 856 tests in 140.009s`，`OK (skipped=1)`；跳过为既有平台条件。
- runtime uvloop：按DEP-1排除Django-only `test_cache.py`，显式安装`uvloop.EventLoopPolicy()`运行同一模块集，`Ran 845 tests in 160.576s`，`OK (skipped=1)`。
- backend/Django全树：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src /home/ns/.virtualenvs/ns_backend_p09_rp1_review/bin/python -m unittest discover -s tests -p 'test_*.py' -q`，`Ran 839 tests in 62.718s`，`OK (skipped=50)`；skips为backend环境未安装runtime可选依赖等既有边界。
- 依赖与静态：`python3 -m compileall -q src tests`通过；runtime/backend两个项目隔离环境`python -m pip check`均输出`No broken requirements found.`；delivery cold import为`DELIVERY_COLD_IMPORT_OK`；RP-1相对启动基线为`RP1_ZERO_DIFF_OK`；P12+禁止项新增源码扫描为`P12_PLUS_BANNED_SCAN_NO_MATCH`；最终文档定稿前`git diff --check`为`DIFF_CHECK_OK`，提交前再次执行。

### P11-W01至W11完成映射

- W01：prepared权威分页、tenant/priority/批量/水位和策略版本/原因记录保持；read assertion关闭stale repair与激活竞争。
- W02：queued仍只经StateStore原子claim，多worker与duplicate claim唯一owner；ready repair不再删除并发release的新投影。
- W03：仅local runtime lease/renew abstraction保持；typed renewal handle关闭所有非ACK_WAITING路径，风险不伪造transfer且没有P17 fencing。
- W04：发送前重读status/owner/session/target/payload/config/expiry；专用backend对象级IAM decision关闭payload_ref伪造与跨对象/target replay。
- W05：queued -> sending与DeliveryAttempt继续同一事务，fake transport不能绕过，sending无attempt不可达。
- W06：只创建ack_waiting deadline；未实现timeout scanner或retry。
- W07：transport write成功仍只到ack_waiting，不生成sent_success，不解释为delivery success。
- W08：write error/timeout/unknown保持typed一致；`retry_scheduled`不进入production，未实现dead letter。
- W09：保护窗口与owner risk继续阻止扩大写入；unknown停止renew并等待既有authority恢复。
- W10：prepared/queued/active/inflight及Summary计数随权威状态事务同步；assertion冲突和repair不产生计数孤儿。
- W11：local experimental dispatch只在显式注入时可用、默认false；P12 ACK闭环完成前禁止production enable。

### 未实现限制

- P11只完成`prepared -> queued -> sending -> ack_waiting`以及typed waiting/failure/uncertain保护；transport write成功不等于delivery success。P12 ACK/NACK/Defer、AckRecord、ACK timeout scanner、retry worker/budget与delivery success终态均未实现。
- P13 DeadLetterRecord/replay/一般cancel/hold、P14 health scoring/fair scheduling、P17 leader lease/cluster fencing、Redis Cluster运行、master query、remote forwarding、跨runtime ownership均未实现；没有第二TaskSupervisor/event loop/shutdown owner。
- Valkey仍只是driver compatibility，不声明valkey-server、Sentinel、Cluster、failover或replica read；production `task.dispatch`继续disabled。

## P02/P08/P09/P11 authority、write uncertainty 与默认入口 Blocker 修复

- 工作包：`P02-FIX-06`、`P08-FIX-01`、`P09-FIX-05`、`P11-FIX-06`。
- 状态：`VERIFIED / F3 (local only)`；P12继续`BLOCKED / F0`，production `task.dispatch`继续disabled。
- 完成时间：`2026-07-23`（Asia/Shanghai）。本轮启动分支为`codex/ns-runtime-implementation`，HEAD为`ca439c6424bdafec2badb5887e0260ddf95e30de`，启动worktree干净；只形成未提交的本地工作区修改。
- 修改文件：design checklist、implementation plan、ADR-045及本验收日志；common StateStore authority/model/store/Redis provider；runtime IAM/processor/routing/delivery/transport/connection/main/state authority；对应StateStore、Redis、IAM、routing、delivery、main与transport测试及显式processor contract-test issuer。
- IAM authorization authority：production evidence只由精确、完整初始化且composition-controlled的`MessageAuthorizationService`经`IamProcessorAuthorization`签发。issuer seal绑定message、tenant、target、permission snapshots、policy及decision reference；公开构造、旧factory、replace、字段复制、subclass、fake service/issuer和test realm evidence不能形成production ALLOW authority。SHA-256仅保留内容绑定作用。
- payload IAM authority：production validator只接受精确、完整初始化、未覆写方法且composition-controlled的production `IamClient`；测试替身使用显式contract-test adapter或在真实client以下替换HTTP边界。payload evidence保持private issuer并绑定object/version/checksum/size、tenant、target、permission snapshot、admission authority、decision ref/version/time/expiry；mapping/object/str subclass、未初始化subclass、method override、malformed/wrong provider result均fail closed。
- StateStore authority与provider：每个store拥有唯一production或contract-test issuer realm，scope seal精确绑定caller/domain/namespace/tenant/runtime/plugin/partition/capabilities并在每次操作复验；public/replace/subclass/手工capability/cross-store scope不能扩权。transaction result的records/log_positions必须与mutations/appends精确等长且类型正确。公共record/index read assertion从model与facade一致导出。Redis ordered-index由单个Lua调用原子验证cursor、定位、分页和total，并对cursor删除/score变化返回typed conflict。
- transport与入口：transport write返回`NOT_STARTED`、`UNCERTAIN`或`SUCCEEDED`；只有确定未开始才进入`WRITE_FAILED`，started-write的timeout/cancel/close/unknown exception进入`WRITE_UNCERTAIN`、释放owner并停止renew/重发。默认`python -m ns_runtime.main`启动唯一StateStore和RuntimeService并等待同一shutdown coordinator；SIGINT/SIGTERM、critical task failure和显式shutdown走统一清理，`self-check`/`diagnose`改为显式有界命令，启动原异常保留并best-effort cleanup。

### 实际测试命令与结果

- processor/routing/IAM：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_runtime_processor_boundaries tests.test_runtime_processor_pipeline tests.test_runtime_routing tests.test_runtime_routing_contracts tests.test_runtime_iam_authorization tests.test_runtime_iam_client`，`Ran 76 tests in 2.628s`，`OK`。
- payload authority、delivery admission与scheduling：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_runtime_delivery_admission tests.test_runtime_delivery_scheduling`，`Ran 62 tests in 49.712s`，`OK`。
- StateStore contract/provider：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_state_store tests.test_runtime_state_store tests.test_redis_state_store_provider`，`Ran 39 tests in 0.838s`，`OK`。
- 真实Redis standalone：`PYTHONPATH=src python3 -m unittest tests.test_redis_state_store_provider tests.test_redis_state_store_integration`，`Ran 30 tests in 48.697s`，`OK`。本机实际发现并启动`/usr/bin/redis-server`；结论不覆盖Valkey server、Sentinel、Cluster、replica或failover。
- main、shutdown、critical failure与transport：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_runtime_event_loop_observability tests.test_runtime_shutdown tests.test_runtime_service tests.test_runtime_main tests.test_runtime_transport_metrics tests.test_runtime_transport_lifecycle tests.test_runtime_transport_identity tests.test_runtime_transport_errors tests.test_runtime_transport_contracts tests.test_runtime_transport_conformance tests.test_runtime_transport_backpressure tests.test_runtime_transport_websocket_tcp tests.test_runtime_transport_registry`，最终`Ran 110 tests in 7.493s`，`OK`。
- import/dependency boundary：`tests.test_requirements tests.test_runtime_bootstrap tests.test_runtime_processor_boundaries`为`Ran 19 tests in 2.980s, OK`；六个修改边界模块独立子进程冷导入输出`COLD_IMPORT_BOUNDARIES_OK`；runtime/backend项目虚拟环境`pip check`均输出`No broken requirements found.`。未隔离系统Python的`pip check`报告宿主`pygobject 3.42.1 requires pycairo`，因此该宿主环境不记为通过。
- 全仓可执行测试集：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -q`，`Ran 865 tests in 133.895s`，`OK (skipped=1)`；唯一skip为既有平台条件。
- 静态与边界：`python3 -m compileall -q src tests`、公共assertion/transport type import、`git diff --check`、P12+新增源码扫描和scope issuer调用点白名单均通过；输出分别为`PUBLIC_IMPORTS_OK`、`P12_PLUS_ADDED_SOURCE_SCAN_OK`和`STATE_SCOPE_ISSUER_BOUNDARY_OK`。Git仅提示仓库既有autocrlf行尾转换告警，不是diff whitespace错误。

### 已知限制与冻结范围

- 仍只支持`prepared -> queued -> sending -> ack_waiting`及typed failure/uncertainty；`WRITE_UNCERTAIN`不恢复、不重发，留给后续独立阶段。
- 未运行uvloop全树、backend/Django全树、Valkey/Sentinel/Redis Cluster或远程CI；这些不能从本地standard asyncio与Redis standalone结果推断为通过。
- P12 ACK/NACK/Defer/timeout/retry、P13 DLQ/replay/cancel/hold、P14 health/fair scheduling、P17 leader/cluster ownership和P22 production验收均未实现；没有新增第二event loop、TaskSupervisor、RuntimeService、shutdown owner、global authority registry或service locator，production `task.dispatch`仍关闭。

## P08/P09/P11 composition-owned authority 复核修复

- 工作包：`P08-FIX-02`、`P09-FIX-06`、`P11-FIX-07`。
- 状态：`VERIFIED / F3 (local only)`；P12继续`BLOCKED / F0`，production `task.dispatch`继续disabled。
- 完成时间：`2026-07-23`（Asia/Shanghai）。本轮启动分支为`codex/ns-runtime-implementation`，HEAD为`7b9cad3a95af9d00d23be220ac0dd5187ade2c00`，启动worktree干净；只形成未提交的本地工作区修改。
- production authorization evidence：删除可自由导入的production signer，改为由composition-owned `IamProcessorAuthorization`持有的实例级issuer。issuer绑定精确且完整初始化的`MessageAuthorizationService`，只消费该service本次`authorize()`返回的sealed typed result，并在内部绑定request、session/effective permission snapshot、backend decision、config/policy version及当前message context；direct construction、module attribute、replace、copy、subclass、fake/test issuer及cross-service result均不能形成production authority。
- IAM client与HTTP provenance：删除module-level production client factory，改为由composition root创建的实例级`IamClientFactory`。factory绑定精确`NsHttpClientOwner`、owner创建的`NsAsyncHttpClient`、底层`httpx.AsyncClient`、transport与当前runtime composition；关键class method identity、实例`__dict__` substitution、owner-issued one-shot binding和exact identity均逐次验证。monkey patch `post/request/send`、copy、subclass、method override、`object.__new__`未初始化对象及duplicate binding均fail closed。
- payload evidence：删除module-level payload production signer；production validator持有绑定同一production `IamClient`与clock的实例级issuer。issuer只消费原始revalidation request和该client本次真实返回的typed decision，并内部交叉验证delivery、target、permission snapshot、admission authority、object/version/checksum/size、decision reference/time/expiry；fake validator/test adapter、replace/copy/subclass与cross-request decision均不能进入production realm。
- StateStore repositories：删除`StateStore._issue_access_scope(...)`及自由`delivery_scope(..., caller=...)`。唯一composition owner创建固定role/caller/domain/namespace/runtime/plugin/partition规则与精确capability集合的admission、scheduler、payload、registry、audit repositories；业务调用只能提供tenant、bucket与layout generation等业务维度。payload repository仅有READ，scheduler/admission/registry/audit互不共享全能力scope；持有raw store、跨repository调用、直接构造、copy或错误owner均不能签发或扩权，未引入global registry、service locator或第二StateStore owner。
- transaction result：`StateTransactionResult`改为只经`for_transaction(transaction, ...)`的one-shot transaction binding构造；模型级验证records与mutations、log_positions与log_appends精确等长、类型和mutation顺序/内容一致，并绑定transaction实例identity、canonical fingerprint和私有seal。direct constructor、replace/copy/subclass、缺项/多项/错序/错类型、同长度cross-transaction replay及克隆transaction复用均fail closed；provider在任何zip前完成绑定和cardinality验证。

### 本轮实际测试命令与结果

- processor/routing/IAM authority与client composition：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_backend_runtime_iam tests.test_runtime_connection_processors tests.test_runtime_iam_authorization tests.test_runtime_iam_client tests.test_runtime_iam_credential_recovery tests.test_runtime_processor_boundaries tests.test_runtime_processor_pipeline tests.test_runtime_protocol_processors tests.test_runtime_routing tests.test_runtime_routing_contracts`，`Ran 93 tests in 3.340s`，`OK`。
- payload authority、delivery admission与scheduling：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_runtime_delivery_admission tests.test_runtime_delivery_scheduling`，`Ran 62 tests in 50.344s`，`OK`。
- StateStore contract/provider：`PYTHONPATH=src python3 -m unittest -q tests.test_redis_state_store_provider tests.test_state_store tests.test_runtime_state_store`，`Ran 41 tests in 0.835s`，`OK`；最终模型专项`tests.test_state_store tests.test_redis_state_store_provider`为`Ran 32 tests in 0.817s`，`OK`。
- Redis provider与真实Redis standalone：`PYTHONPATH=src python3 -m unittest -q tests.test_redis_state_store_provider tests.test_redis_state_store_integration`，`Ran 30 tests in 49.330s`，`OK`。本机实际使用`/usr/bin/redis-server`；未验证Valkey server、Sentinel、Cluster、replica或failover。
- main、shutdown、critical failure与transport：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_runtime_event_loop_observability tests.test_runtime_shutdown tests.test_runtime_service tests.test_runtime_main tests.test_runtime_transport_metrics tests.test_runtime_transport_lifecycle tests.test_runtime_transport_identity tests.test_runtime_transport_errors tests.test_runtime_transport_contracts tests.test_runtime_transport_conformance tests.test_runtime_transport_backpressure tests.test_runtime_transport_websocket_tcp tests.test_runtime_transport_registry`，`Ran 110 tests in 7.799s`，`OK`。
- 全仓可执行测试集：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -q`，`Ran 869 tests in 138.174s`，`OK (skipped=1)`；唯一skip为非Windows平台上的真实Windows event-loop policy条件。
- compile/import/dependency boundary：`python3 -m compileall -q src tests`与`git diff --check`通过；cold import输出`COLD_IMPORT_BOUNDARIES_OK`及`PUBLIC_IMPORTS_OK`；runtime/backend项目虚拟环境`pip check`均输出`No broken requirements found.`。边界测试的首次命令误写了两个不存在的module name，产生2个loader error；更正为`PYTHONPATH=src python3 -m unittest -q tests.test_requirements tests.test_runtime_bootstrap tests.test_runtime_processor_boundaries`后`Ran 19 tests in 2.940s`，`OK`，未把误写命令记作通过。

### 冻结边界与未验证范围

- 状态机仍严格为`prepared -> queued -> sending -> ack_waiting`；`WRITE_UNCERTAIN`不重发，也未新增第二event loop、TaskSupervisor、RuntimeService、shutdown owner、global authority registry或service locator。
- 未实现P12 ACK/NACK/Defer/timeout/retry、P13 DLQ/replay、P14 health/fair scheduling、P17 cluster ownership或P22 production验收；production `task.dispatch`继续disabled。
- 本轮未运行uvloop全树、backend/Django全树、Valkey/Sentinel/Redis Cluster、replica/failover或远程CI，不从standard asyncio与Redis standalone结果推断这些环境通过。

## P08/P09/P11 transport provenance 与 repository resource authority 复核修复

- 工作包：`P08-FIX-03`、`P09-FIX-07`、`P11-FIX-08`。
- 状态：`VERIFIED / F3 (local only)`；P12继续`BLOCKED / F0`，production `task.dispatch`继续disabled。
- 完成时间：`2026-07-23`（Asia/Shanghai）。本轮启动分支为`codex/ns-runtime-implementation`，HEAD为`10bbc3d48d64c7190136b33c21f101c4b015a8f3`；只保留未提交本地修改。
- production IAM graph：删除`IamClientFactory`及production free factory，公共`IamClient`构造永久拒绝。process composition创建exact client、owner-issued narrow HTTP handle和exact-client proof；module attribute、普通owner/client/composition object、copy、subclass、method override及`object.__new__`未初始化对象不能满足production adapter检查。测试IAM替身为显式contract-test realm，不冒充production client。
- HTTP transport provenance：narrow handle逐次绑定并在请求前后验证exact `NsAsyncHttpClient`、底层exact `httpx.AsyncClient`、主`_transport`、原`_mounts`容器、每个mount/proxy transport及其`handle_async_request` class identity，同时拒绝`request/get/post/put/delete/send/stream` instance substitution。transport、mount、handler替换和owner关闭后复用均即时fail closed。
- raw StateStore closure：删除raw Store上的repository owner和`_create_repository`路径；composition一次创建固定repository set后冻结creation。production scope使用Ed25519 repository私钥签名，raw Store validator仅闭包持有公钥、issuer identity和冻结policy映射，不持有`_StateScopeIssuer`或private key。name-mangled lookup、vars/dir遍历、copy、pickle式字段复制、伪造validator和二次composition均不能产生新scope/repository。
- resource allowlist：每个scope签名绑定exact role policy；Store在provider前逐项验证operation、object type/schema、ordered-index name/bucket、transition/audit log object/schema和namespace/partition。scheduler读取payload、payload读取delivery、admission写attempt/owner/cursor、registry访问非registry object/index、unknown object/schema/index/log均稳定拒绝。真实Redis路径验证合法admission事务可提交且跨role读取被拒绝。

### 新增攻击测试

- IAM：直接import旧production factory、module attribute探测、普通owner/client/composition、direct constructor、`object.__new__`、copy、subclass/method override、伪造proof。
- HTTP：替换`NsAsyncHttpClient.post`、`httpx.AsyncClient.request/send`、主`_transport`、`_mounts`容器、主transport handler及mount/proxy handler，copy client/owner/handle和关闭后复用。
- StateStore：name-mangled owner缺失、raw Store无creation API/repository/private issuer、validator闭包反射不含issuer/private key、validator direct construction/object-new/copy拒绝、composition二次构造拒绝、production scope copy/replace/object-setattr拒绝。
- repository：scheduler->payload_body、payload->delivery、registry->delivery/非registry index、admission->attempt/owner/cursor，以及unknown object/schema/index bucket/log/audit log全部fail closed。

### 本轮实际测试命令与结果

- processor/routing/IAM authority与client composition：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_backend_runtime_iam tests.test_runtime_connection_processors tests.test_runtime_iam_authorization tests.test_runtime_iam_client tests.test_runtime_iam_credential_recovery tests.test_runtime_processor_boundaries tests.test_runtime_processor_pipeline tests.test_runtime_protocol_processors tests.test_runtime_routing tests.test_runtime_routing_contracts`，`Ran 93 tests in 3.228s`，`OK`。
- payload authority、delivery admission与scheduling：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_runtime_delivery_admission tests.test_runtime_delivery_scheduling`，`Ran 62 tests in 50.631s`，`OK`。
- StateStore repository/contract/provider：最终namespace/partition signer复验落盘后执行`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_redis_state_store_provider tests.test_state_store tests.test_runtime_state_store`，`Ran 42 tests in 0.858s`，`OK`。
- Redis provider与真实Redis standalone：Ed25519与最终resource policy代码落盘后执行`PYTHONPATH=src python3 -m unittest -q tests.test_redis_state_store_provider tests.test_redis_state_store_integration`，`Ran 31 tests in 49.564s`，`OK`；本机实际使用`/usr/bin/redis-server`。另有production resource policy真实Redis专项`Ran 2 tests in 0.296s`，`OK`。
- main、shutdown、critical failure与transport：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest -q tests.test_runtime_event_loop_observability tests.test_runtime_shutdown tests.test_runtime_service tests.test_runtime_main tests.test_runtime_transport_metrics tests.test_runtime_transport_lifecycle tests.test_runtime_transport_identity tests.test_runtime_transport_errors tests.test_runtime_transport_contracts tests.test_runtime_transport_conformance tests.test_runtime_transport_backpressure tests.test_runtime_transport_websocket_tcp tests.test_runtime_transport_registry`，`Ran 110 tests in 7.518s`，`OK`。
- 全仓可执行测试集（包含本轮最终Ed25519、资源策略及namespace/partition signer复验代码）：`PYTHONASYNCIODEBUG=0 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -q`，`Ran 871 tests in 133.757s`，`OK (skipped=1)`；唯一skip为既有非Windows平台上的真实Windows event-loop policy条件。
- 静态与边界：最终`python3 -m compileall -q src tests`和`git diff --check`通过；公共assertion导出及修改边界模块冷导入输出`COLD_IMPORT_AND_PUBLIC_EXPORTS_OK`。`PYTHONPATH=src python3 -m unittest -q tests.test_requirements tests.test_runtime_bootstrap tests.test_runtime_processor_boundaries`为`Ran 19 tests in 2.952s, OK`；runtime/backend项目虚拟环境`pip check`均输出`No broken requirements found.`。P12+新增源码与已删除IAM factory/raw-store repository owner入口扫描无匹配。

### 冻结边界与未验证范围

- 未验证Valkey server、Redis Sentinel/Cluster、replica/failover、uvloop全树、backend/Django全树或远程CI；不得从本机standard asyncio与Redis standalone推断这些环境通过。
- 状态机仍严格为`prepared -> queued -> sending -> ack_waiting`，WRITE_UNCERTAIN不恢复、不重发。未新增global registry、service locator、第二StateStore owner、event loop、TaskSupervisor、RuntimeService或shutdown owner。
- P12 ACK/NACK/Defer/timeout/retry、P13 DLQ/replay、P14 health/fair scheduling、P17 cluster ownership和P22 production验收均未实现；production `task.dispatch`继续disabled。

## P08/P09/P11 authority bootstrap、HTTP TOCTOU 与 opaque policy 复核修复

- 工作包：`P08-FIX-04`、`P09-FIX-08`、`P11-FIX-09`；状态为本地复核通过，P12继续`BLOCKED / F0`。
- 完成时间：`2026-07-23`（Asia/Shanghai）。本轮启动分支`codex/ns-runtime-implementation`、HEAD `9a7c20e6ad133a373137ccdffe3c47ce3d3998cc`；仅有未提交本地修改。
- IAM/HTTP：删除基于`sys._getframe`、函数名和文件路径的production proof以及普通owner的handle创建API。bootstrap局部一次性绑定exact owner/client/handle/client identity。HTTP binding冻结backend URL各层表示、scheme/host/port/path prefix、timeout/default headers、TLS context、proxy、主/mount transport与handler；IAM path为exact allowlist。request直接使用绑定时捕获的绝对URL与transport callable，await期间临时替换后恢复transport/base URL/mount仍只能走原transport。
- StateStore：public facade不再导出production composition factory；provider-only入口不含repository authority。production repository set只安装一次，endpoint/namespace/runtime通过进程文件锁拒绝平行composition。repository/store/composition/validator不保存production private issuer/private key或签发closure；production scope由Store窄endpoint按实例登记，并只携带canonical opaque policy ID。Store内部固定policy表与scope快照绑定role/caller/capability/atomic scope/policy ID/repository binding，copy、字段替换、原地policy修改和cross-role replay均fail closed。
- 新增攻击覆盖：伪造`compile(..., filename="/tmp/ns_runtime/main.py")`、替换`sys._getframe`、普通owner签发handle、base/request/httpx URL与transport/mount替换、await期间替换后恢复、重复production StateStore composition、repository/validator closure与slots枚举、policy ID和repository binding跨role replay。
- 实际回归：processor/routing/IAM `Ran 81, OK`；StateStore/provider `Ran 34, OK`；最终代码的真实`/usr/bin/redis-server` integration `Ran 19 in 59.935s, OK`；main/shutdown/transport `Ran 83 in 10.116s, OK`；最终代码的backend全树`Ran 855 in 93.917s, OK (skipped=51)`。runtime全树尝试执行864项，除按DEP-1未安装Django导致`test_cache`收集错误外无其他失败，另有1项平台skip；不得把该次命令记录为全树通过。
- 静态与环境：runtime/backend `pip check`均为`No broken requirements found.`；`compileall -q src tests`与`git diff --check`通过。真实Redis已验证；Valkey、Redis Sentinel/Cluster、failover、uvloop全树与远程CI未验证。
- 冻结边界：状态机仍仅`prepared -> queued -> sending -> ack_waiting`；WRITE_UNCERTAIN不恢复、不重发；production `task.dispatch`继续disabled。未新增ACK/NACK/Defer、retry、DLQ、cluster ownership或其他P12+能力。

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
