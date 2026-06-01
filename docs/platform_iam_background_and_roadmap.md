# Platform IAM Agent 执行文档（背景 + 落地计划）

- 版本：v2.0
- 日期：2026-06-01
- 适用仓库：`S:\PythonProject\ns_evermore`
- 主要代码域：`src/ns_backend/iam`、`src/ns_backend/backend`、`sql/create/iam`

---

## 0. 给 AI Agent 的执行协议（必须遵守）

本文件不是模板，而是可直接执行的实施指令。AI Agent 必须按以下规则执行：

1. 按任务 ID 顺序执行，除非依赖允许并行。
2. 每次提交只完成一个任务 ID（或一个强耦合任务组），避免大杂烩提交。
3. 每个任务必须同时更新：代码/SQL/API/文档/测试（如任务定义要求）。
4. 每个任务结束必须输出：
   - 改动文件清单
   - 关键 SQL 变更
   - API 变更
   - 验证命令与结果
   - 风险与回滚说明
5. 全局授权冲突规则固定：`deny > allow`，不得被任何任务覆盖。
6. 新业务模块接入目标固定：仅“注册资源 + 注册动作 + 配置策略”，不改 IAM 核心流程。

---

## 1. 项目背景

### 1.1 业务背景

平台未来将承载多个业务域：

- Knowledge
- Agent
- Workflow
- CRM
- Contract
- Project
- ERP

若各模块自行实现鉴权，将导致权限口径、数据范围和审计标准分裂，最终无法支持统一治理和跨模块协作。

### 1.2 当前仓库事实（基于现有代码）

当前已具备基础能力：

- 身份认证与会话：`src/ns_backend/iam/services/auth.py`
- RBAC 与直授权限：`src/ns_backend/iam/models.py`
- deny 优先判定：`src/ns_backend/iam/services/permission.py`
- Data Scope 计算：`src/ns_backend/iam/services/data_scope.py`
- 请求级审计：`src/ns_backend/iam/__init__.py`、`src/ns_backend/iam/services/audit.py`
- 权限 provider 注册与同步：`src/ns_backend/iam/registry`、`src/ns_backend/iam/services/permission_sync.py`

明确缺口：

- 缺资源实例级 ACL（Document/Chunk 级）
- 缺数据化 Policy Engine
- 缺授权决策级审计模型
- 缺 Knowledge 检索链路和 Agent 工具链路的强制接入

### 1.3 终局目标

IAM 必须演进为平台统一身份与授权中心（Platform IAM），完整支持：

- Identity
- RBAC
- Resource ACL
- Data Scope
- Policy Engine
- Audit

并满足新增模块接入无需修改 IAM 核心代码。

---

## 2. 终态架构约束（不可变）

### 2.1 统一授权模型

`Subject + Resource + Action + Effect`

- Subject：User / Role / Department / Organization / Subsidiary
- Resource：任意业务资源（KnowledgeSpace、Document、Chunk、Workflow、Contract、Project、Customer、Agent）
- Action：`read`、`write`、`delete`、`manage`、`execute`、`approve`、`share`
- Effect：`allow`、`deny`
- 规则：`deny` 优先级高于 `allow`

### 2.2 Data Scope 统一口径

统一支持：

- SELF
- DEPARTMENT
- DEPARTMENT_AND_CHILDREN
- ORGANIZATION
- ALL

说明：当前代码中存在 `DEPARTMENT_TREE`、`COMPANY` 命名，实施过程中需做兼容映射。

### 2.3 关键场景硬约束

- Knowledge：权限过滤必须发生在 Retriever 前
- Agent：调用任何 Tool 前必须先经 IAM 授权
- Audit：每次授权决策必须记录 Who/When/Resource/Action/Result/Reason

---

## 3. 目标能力与当前能力差距（执行导向）

1. Identity：已有基础，需扩展组织主体参与授权。
2. RBAC：已有，需与资源实例 ACL 和策略引擎统一编排。
3. Resource ACL：从无到有，必须新增数据模型与服务。
4. Data Scope：已有计算能力，需强制接入业务消费链路。
5. Policy Engine：从代码策略升级为数据策略。
6. Audit：从操作审计扩展为授权决策审计。

---

## 4. 实施边界与技术约束

1. 当前 IAM 模型 `managed=False`，数据库结构由静态 SQL 驱动。
2. 所有新表必须同时更新：
   - `sql/create/iam/sqlite.sql`
   - `sql/create/iam/mysql.sql`
   - `sql/create/iam/postgresql.sql`
   - `src/ns_backend/iam/models.py`
3. 对已有环境，需补 `sql/upgrade/iam/<version>/` 升级脚本（避免只靠重建库）。
4. 可做结构性扩展（项目未生产），但必须保留现有接口兼容层。

---

## 5. 最终目标数据模型（落地清单）

> 本节是“要落地成代码/SQL”的明确目标，不是建议。

### 5.1 新增表

1. `iam_resource`
   - 用途：资源类型注册（模块无关）
   - 关键字段：`resource_type`、`resource_name`、`module_code`、`status`

2. `iam_resource_action`
   - 用途：资源动作注册
   - 关键字段：`resource_id`、`action_code`、`action_name`、`status`
   - 唯一约束：`(resource_id, action_code)`

3. `iam_resource_acl`
   - 用途：实例级授权
   - 关键字段：
     - `subject_type`、`subject_id`
     - `resource_type`、`resource_id`
     - `action_code`
     - `effect`（ALLOW/DENY）
     - `data_scope`（可空）
     - `expired_at`（可空）
   - 唯一约束建议：`(subject_type, subject_id, resource_type, resource_id, action_code)`

4. `iam_policy`
   - 用途：策略主表
   - 关键字段：`policy_code`、`policy_name`、`priority`、`status`、`version`

5. `iam_policy_rule`
   - 用途：策略规则表
   - 关键字段：
     - `policy_id`
     - `subject_type`、`subject_id`（可空表示通配）
     - `resource_type`、`resource_id`（可空表示通配）
     - `action_code`
     - `effect`
     - `data_scope`
     - `condition_json`
     - `priority`
     - `status`

6. `iam_audit_log`
   - 用途：授权决策审计
   - 关键字段：
     - `operator_id`
     - `subject_type`、`subject_id`
     - `resource_type`、`resource_id`
     - `action_code`
     - `result`
     - `reason`
     - `matched_policy_id`、`matched_rule_id`
     - `trace_id`
     - `created_at`

### 5.2 保留并复用的现有表

- `iam_permission`
- `iam_role` / `iam_role_permission` / `iam_user_role`
- `iam_user_permission` / `iam_department_permission` / `iam_subsidiary_permission`
- `iam_operation_audit`

---

## 6. 最终目标 API（落地清单）

### 6.1 资源注册

- `POST /iam/resource/register`
- `POST /iam/resource/action/register`
- `POST /iam/resource/list`

### 6.2 ACL 管理

- `POST /iam/acl/grant`
- `POST /iam/acl/revoke`
- `POST /iam/acl/list`

### 6.3 策略管理

- `POST /iam/policy/create`
- `POST /iam/policy/update`
- `POST /iam/policy/publish`
- `POST /iam/policy/disable`
- `POST /iam/policy/rule/add`
- `POST /iam/policy/rule/remove`
- `POST /iam/policy/rule/list`

### 6.4 授权判定

- `POST /iam/authorize/check`
- `POST /iam/authorize/batch-check`

### 6.5 审计查询

- `POST /iam/audit/decision/list`

### 6.6 核心返回协议（固定）

`authorize/check` 返回至少包含：

- `allowed: bool`
- `effect: allow|deny`
- `reason: str`
- `matched_source: acl|policy|rbac|superuser|none`
- `matched_policy_id: int|null`
- `matched_rule_id: int|null`
- `filters: object`（数据范围过滤条件）

---

## 7. 分阶段可执行任务（完整 backlog）

> 每个任务包含：目标、依赖、文件、表、API、具体改法、验收。

## 7.1 P0（治理收敛，1-2 周）

### 任务 P0-01：权限与动作分类标准落地

- 依赖：无
- 文件：
  - 新增 `docs/iam/p0/permission-taxonomy.md`
  - 更新 `src/ns_backend/iam/registry/builtin.py`
- 表：复用 `iam_permission`
- API：无新增
- 具体改法：
  1. 统一权限码格式：`{module}:{resource}:{action}`。
  2. 在 builtin provider 中增加跨模块标准动作示例权限码。
  3. 在 `PermissionSyncService.validate_specs` 增加 action 白名单校验（仅对 action 型权限）。
- 验收：`sync_iam_permissions` 对非法 action 直接失败并给出错误码。

### 任务 P0-02：IAM 路由权限覆盖 100%

- 依赖：P0-01
- 文件：
  - 更新 `src/ns_backend/iam/urls.py`
  - 新增 `docs/iam/p0/iam-api-permission-matrix.md`
- 表：无
- API：IAM 全路由
- 具体改法：
  1. 为 `auth/*`、`session/*` 明确匿名与鉴权边界。
  2. 除登录/刷新外全部接口配置 `required_permissions`。
  3. 矩阵文档按 path/action/permission_code 输出。
- 验收：任一路由都能在矩阵中定位对应权限策略。

### 任务 P0-03：授权决策原因审计增强

- 依赖：P0-02
- 文件：
  - 更新 `src/ns_backend/iam/__init__.py`
  - 更新 `src/ns_backend/iam/services/audit.py`
- 表：复用 `iam_operation_audit`
- API：无新增
- 具体改法：
  1. `extra_data` 写入 `decision_reason`、`matched_permission_code`、`decision_source`。
  2. deny 场景必须填充拒绝原因。
  3. 统一错误码与消息映射。
- 验收：抽样失败请求均含可解释原因。

### 任务 P0-04：Data Scope 兼容映射与消费规范

- 依赖：P0-03
- 文件：
  - 更新 `src/ns_backend/iam/constants.py`（兼容枚举别名）
  - 更新 `src/ns_backend/iam/services/data_scope.py`
  - 新增 `docs/iam/p0/data-scope-contract.md`
- 表：复用现有授权表
- API：`POST /iam/auth/data-scopes`
- 具体改法：
  1. 增加命名映射层：`DEPARTMENT_TREE -> DEPARTMENT_AND_CHILDREN`，`COMPANY -> ORGANIZATION`。
  2. 输出字段中增加 `normalized_scope`。
  3. 文档固化“业务必须消费 IAM filter plan”。
- 验收：scope 输出兼容历史值且有新标准值。

### 任务 P0-05：回归基线与 smoke 流程

- 依赖：P0-04
- 文件：
  - 新增 `docs/iam/p0/smoke-checklist.md`
  - 新增 `docs/iam/p0/smoke-requests.http`（或同等请求集）
- 表：无
- API：全量抽样
- 具体改法：
  1. 固化 20+ 条核心接口 smoke。
  2. 覆盖：登录、权限拒绝、data scope、grant、audit。
- 验收：P0 合并前 smoke 必须全绿。

P0 阶段完成定义：

- IAM 路由门禁清晰且覆盖完整。
- 权限命名与 action 口径统一。
- 请求审计可解释。

---

## 7.2 P1（资源 ACL + 统一授权入口，2-4 周）

### 任务 P1-01：资源注册模型与 API

- 依赖：P0 完成
- 文件：
  - 更新 `sql/create/iam/sqlite.sql`
  - 更新 `sql/create/iam/mysql.sql`
  - 更新 `sql/create/iam/postgresql.sql`
  - 更新 `src/ns_backend/iam/models.py`
  - 新增 `src/ns_backend/iam/repositories/resource.py`
  - 新增 `src/ns_backend/iam/services/resource_registry.py`
  - 新增 `src/ns_backend/iam/views/resource_views.py`
  - 更新 `src/ns_backend/iam/urls.py`
- 表：新增 `iam_resource`、`iam_resource_action`
- API：新增资源注册接口
- 具体改法：
  1. 先建资源类型，再建动作。
  2. 对动作做白名单校验。
  3. 提供 list 接口用于模块侧自检。
- 验收：可注册 `knowledge.document` + `read/write/share`。

### 任务 P1-02：实例 ACL 数据模型与接口

- 依赖：P1-01
- 文件：
  - 更新 `sql/create/iam/*`
  - 更新 `src/ns_backend/iam/models.py`
  - 新增 `src/ns_backend/iam/repositories/resource_acl.py`
  - 新增 `src/ns_backend/iam/services/resource_acl.py`
  - 新增 `src/ns_backend/iam/views/acl_views.py`
  - 更新 `src/ns_backend/iam/urls.py`
- 表：新增 `iam_resource_acl`
- API：`/iam/acl/grant|revoke|list`
- 具体改法：
  1. 支持 subject_type 五类主体。
  2. grant/revoke 需支持 `expired_at`。
  3. list 支持按 resource/action/subject 过滤。
- 验收：同一资源动作上 deny 能覆盖 allow。

### 任务 P1-03：统一 AuthorizeService

- 依赖：P1-02
- 文件：
  - 新增 `src/ns_backend/iam/repositories/authorize.py`
  - 新增 `src/ns_backend/iam/services/authorize.py`
  - 新增 `src/ns_backend/iam/views/authorize_views.py`
  - 更新 `src/ns_backend/iam/urls.py`
- 表：复用 ACL + RBAC 相关表
- API：`/iam/authorize/check`、`/iam/authorize/batch-check`
- 具体改法：
  1. 固定判定顺序：
     - superuser
     - ACL deny
     - Policy deny（P2 前可空）
     - ACL allow
     - RBAC allow
     - 否则 deny
  2. 输出 `reason` 与 `matched_source`。
  3. 批量接口返回逐条 decision。
- 验收：业务可只调用一个授权接口完成判定。

### 任务 P1-04：视图层接入统一授权门面

- 依赖：P1-03
- 文件：
  - 更新 `src/ns_backend/iam/__init__.py`
  - 更新 `src/ns_backend/iam/views/__init__.py`
- 表：无
- API：无新增
- 具体改法：
  1. 保留 `required_permissions` 机制。
  2. 在可选模式下支持走 `AuthorizeService`（为跨模块接入做准备）。
  3. 把授权结果写入审计上下文。
- 验收：IAM 自身接口与统一授权门面可并行运行。

P1 阶段完成定义：

- 资源实例 ACL 可用。
- 有统一授权入口。
- deny 优先可由接口验证。

---

## 7.3 P2（Policy Engine 数据化，4-6 周）

### 任务 P2-01：策略表与规则表落地

- 依赖：P1 完成
- 文件：
  - 更新 `sql/create/iam/*`
  - 更新 `src/ns_backend/iam/models.py`
  - 新增 `src/ns_backend/iam/repositories/policy.py`
- 表：新增 `iam_policy`、`iam_policy_rule`
- API：无（先落模型）
- 具体改法：
  1. `iam_policy` 承载版本、优先级、状态。
  2. `iam_policy_rule` 支持条件 JSON 与优先级。
  3. 建索引：policy_id、status、priority、subject/resource/action 组合。
- 验收：策略与规则可增删查。

### 任务 P2-02：PolicyEngine 评估器

- 依赖：P2-01
- 文件：
  - 新增 `src/ns_backend/iam/services/policy_engine.py`
  - 更新 `src/ns_backend/iam/services/authorize.py`
- 表：复用 `iam_policy*`
- API：无新增
- 具体改法：
  1. 策略求值前加载启用策略和规则。
  2. 求值顺序：规则优先级高到低；同优先级 deny 先于 allow。
  3. 将命中策略和规则 ID 写入 decision。
- 验收：同一请求可追溯命中规则。

### 任务 P2-03：策略管理 API

- 依赖：P2-02
- 文件：
  - 新增 `src/ns_backend/iam/views/policy_views.py`
  - 更新 `src/ns_backend/iam/urls.py`
- 表：复用 `iam_policy*`
- API：策略与规则管理接口全量落地
- 具体改法：
  1. create/update/publish/disable 生命周期管理。
  2. rule add/remove/list。
  3. 所有写操作带审计。
- 验收：可不改代码上线一条新策略并生效。

### 任务 P2-04：Organization 主体纳入授权

- 依赖：P2-03
- 文件：
  - 更新 `src/ns_backend/iam/constants.py`
  - 更新 `src/ns_backend/iam/services/authorize.py`
  - 更新 `src/ns_backend/iam/services/data_scope.py`
- 表：复用 ACL/Policy 表
- API：ACL 与策略 API 支持 `subject_type=ORGANIZATION`
- 具体改法：
  1. 扩展主体枚举。
  2. 加入组织主体求值分支。
- 验收：五类主体全部可参与授权判定。

### 任务 P2-05：授权决策专用审计表

- 依赖：P2-04
- 文件：
  - 更新 `sql/create/iam/*`
  - 更新 `src/ns_backend/iam/models.py`
  - 新增 `src/ns_backend/iam/repositories/decision_audit.py`
  - 新增 `src/ns_backend/iam/services/decision_audit.py`
  - 新增 `src/ns_backend/iam/views/audit_views.py`
  - 更新 `src/ns_backend/iam/urls.py`
- 表：新增 `iam_audit_log`
- API：`/iam/audit/decision/list`
- 具体改法：
  1. 每次 `AuthorizeService` 决策都落专用审计。
  2. 记录 reason、matched_policy_id、matched_rule_id。
- 验收：失败授权必可回溯到规则级。

P2 阶段完成定义：

- Policy Engine 可配置。
- 组织主体支持完整。
- 决策审计可解释可检索。

---

## 7.4 P3（Knowledge/Agent 强制接入 + 平台验收，4-8 周）

### 任务 P3-01：Knowledge 检索授权过滤器

- 依赖：P2 完成
- 文件：
  - 新增 `src/ns_backend/iam/integration/knowledge_filter.py`
  - 新增 `docs/iam/p3/knowledge-integration.md`
- 表：复用 ACL/Policy/审计表
- API：复用 `/iam/authorize/batch-check`
- 具体改法：
  1. 输入候选文档/切片列表。
  2. 批量授权过滤后再召回。
  3. 过滤过程写决策审计。
- 验收：无权限 chunk 不进入上下文。

### 任务 P3-02：Agent Tool 授权守卫

- 依赖：P3-01
- 文件：
  - 新增 `src/ns_backend/iam/integration/agent_guard.py`
  - 新增 `docs/iam/p3/agent-integration.md`
- 表：复用 ACL/Policy/审计表
- API：复用 `/iam/authorize/check`
- 具体改法：
  1. Tool 到 action_code 映射。
  2. 调用前鉴权，不通过则拒绝执行。
  3. 记录决策日志。
- 验收：Tool 无授权无法执行且可审计。

### 任务 P3-03：平台级验收与性能基线

- 依赖：P3-02
- 文件：
  - 新增 `docs/iam/p3/platform-acceptance.md`
  - 新增 `docs/iam/p3/perf-baseline.md`
- 表：无新增
- API：全链路
- 具体改法：
  1. 建立六大能力验收矩阵。
  2. 建立判定性能指标（P95、批量吞吐）。
- 验收：平台化建设完成标准全部通过。

P3 阶段完成定义：

- Knowledge 与 Agent 链路已强制接入 IAM。
- 新模块接入仅靠注册与策略配置。

---

## 8. AI Agent 每任务执行输出格式（固定）

每个任务完成后，必须追加如下输出（可写到 PR 描述或任务日志）：

1. `Task ID`
2. `Changed Files`
3. `DB Changes`
4. `API Changes`
5. `How to Verify`
6. `Verification Result`
7. `Rollback Plan`

---

## 9. 验证命令基线（PowerShell）

> 以下为建议命令，AI Agent 可按实际环境补充。仓库当前可见入口是 `src/ns_backend/manage.py`。

```powershell
Set-Location "S:\PythonProject\ns_evermore"
python -u src\ns_backend\manage.py check
python -u src\ns_backend\manage.py sync_iam_permissions --builtin-only
python -u src\ns_backend\manage.py install_infra_schema --domain iam --dry-run
```

如测试框架已配置，可追加：

```powershell
Set-Location "S:\PythonProject\ns_evermore"
python -u -m pytest -q
```

---

## 10. 平台化最终验收标准（全局 Gate）

满足以下全部条件，判定平台化目标达成：

1. Subject/Resource/Action/Effect 统一模型完整可用。
2. deny 优先在 ACL、Policy、RBAC 三层一致生效。
3. Data Scope 由 IAM 输出并被业务强制消费。
4. Knowledge 检索链路在 Retriever 前完成授权过滤。
5. Agent Tool 调用链路无法绕过 IAM。
6. 授权决策具备 Who/When/Resource/Action/Result/Reason，可追溯到规则级。
7. 新增业务模块接入无需改 IAM 核心主流程。

---

## 11. 第一批立即开工任务（本周）

1. 执行 P0-01、P0-02，先完成权限口径与 IAM 路由矩阵。
2. 执行 P0-03，统一审计中的决策原因字段。
3. 启动 P1-01、P1-02 的 SQL 与模型设计评审，冻结字段。
4. 冻结 `AuthorizeService` 输入/输出协议，为 P1-03 开发做准备。

---

## 12. 备注

本文件为执行文档，后续每个阶段完成后只允许增量更新，不允许回退目标约束。
