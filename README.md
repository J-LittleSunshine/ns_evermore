# ns_evermore

Unified Identity, Authorization, Storage and Runtime Foundation for Enterprise Systems.

## 摘要

`ns_evermore` 是一个面向企业级应用的基础设施平台项目。

项目核心目标不是开发某一个业务系统，而是构建一套可复用、可扩展、可标准化接入的基础设施能力中心，为企业未来的多个业务系统提供统一底座。
项目参考了 Spring Security、Keycloak、Casbin、MinIO 等成熟基础设施产品的设计理念，并尝试在统一架构下整合身份认证、授权、存储和运行时能力。

当前重点建设方向：

- 统一身份与访问控制（IAM）
- 统一资源访问控制（Resource ACL）
- 统一数据权限（Data Scope）
- 统一对象存储（Storage）
- 统一运行时消息基础设施（Runtime）
- 统一审计与可观测性（Audit & Observability）

---

# 项目背景

在企业数字化建设过程中，随着业务系统不断增加，通常会出现以下问题：

- 用户体系重复建设
- 权限模型不统一
- 数据权限逻辑分散
- SSO 难以扩展
- 审计能力缺失
- 文件存储重复建设
- 系统之间缺乏统一标准

最终导致：

- 运维成本增加
- 开发成本增加
- 安全风险增加
- 系统扩展困难

`ns_evermore` 的目标就是解决这些问题。

---

# 项目定位

## 当前定位

面向企业基础设施建设的技术预研与架构验证项目。

当前主要验证 IAM（Identity & Access Management）作为统一身份与访问控制中心的可行性。

## 中期定位

企业统一身份与访问控制平台

## 长期定位

企业数字化基础设施平台

---

# 整体架构

```text
                 +------------------+
                 |   External IdP   |
                 |  OIDC/LDAP/CAS   |
                 +--------+---------+
                          |
                          v

+--------------------------------------------------+
|                    IAM Core                      |
|--------------------------------------------------|
| Identity | Auth | RBAC | ACL | Policy | Audit    |
+--------------------------+-----------------------+
                           |
        +------------------+------------------+
        |                                     |
        v                                     v

+--------------------+         +--------------------+
|      Storage       |         |      Runtime       |
+--------------------+         +--------------------+

        \                                     /
         \                                   /
          \                                 /
           v                               v

+--------------------------------------------------+
|               Business Applications              |
|--------------------------------------------------|
| CRM | ERP | HIS | Knowledge | Agent | Workflow   |
+--------------------------------------------------+
```

---

# 核心能力

## IAM（Identity & Access Management）

IAM 是当前项目最核心的建设方向。

### Identity

统一身份模型：

- 用户
- 公司
- 子公司
- 部门
- 超级管理员
- 企业用户
- 个人用户

### Authentication

统一认证能力：

- 用户名密码登录
- Access Token
- Refresh Token
- Refresh Rotation
- Session
- Device Tracking
- Login Lock

### Authorization

统一权限模型：

- RBAC
- Direct Permission
- Department Permission
- Subsidiary Permission

支持：

- Allow
- Deny
- Permission Inheritance

授权冲突规则：

```text
DENY > ALLOW
```

### Resource ACL

资源级访问控制。

支持：

- User ACL
- Role ACL
- Department ACL
- Organization ACL
- Subsidiary ACL

支持：

- Allow
- Deny
- Expire Time
- Resource Relation
- Resource Instance Authorization

授权冲突规则：

DENY > ALLOW

### Policy Engine

动态策略引擎。

支持：

- IP控制
- 时间控制
- 上下文控制
- 动态规则控制

### Data Scope

业务系统无需重复实现“本人、本部门、本公司”等数据过滤逻辑。

统一数据权限模型：

- 本人数据
- 本部门数据
- 本部门及下级部门数据
- 本公司数据
- 全部数据

### Audit

统一审计能力：

- 登录审计
- 操作审计
- 授权审计
- Trace ID追踪

---

## Storage

统一对象存储能力。

支持：

- Local FS
- MinIO
- S3 Compatible Storage

能力包括：

- 文件上传
- 对象引用管理
- Presigned URL
- 统一存储抽象

---

## Runtime

统一后端运行时消息基础设施，用于支撑后端事件投递、实时通信、Agent 事件流、Workflow 事件流和跨节点消息转发。

当前 Runtime 已经具备以下基础能力：

- Runtime Message Contract
- Runtime Target / Producer / Ack
- Trace ID / Idempotency Key / TTL
- SQL WAL Outbox
- Message Enqueue / Atomic Claim
- ACK / Retry / Dead Letter
- Exponential Backoff
- Local IPC Server
- Backend Connector Wakeup
- Backend Runtime Connector
- Outbox Drain Loop
- Connector Statistics
- Memory Broker
- Redis Broker
- ValKey Broker
- Broker Envelope
- Cluster Channel
- Node Channel
- Message Forward Envelope

后续将继续完善：

- WebSocket Runtime Master
- Frontend Realtime Connection
- Cross-node Dispatch
- Presence Synchronization
- Runtime Management API

## Observability

统一可观测性基础设施，用于支撑平台运行状态、请求链路、授权决策、消息投递和异常问题的追踪分析。

规划能力：

- Structured Logging
- Metrics
- Distributed Tracing
- Health Check
- Audit Correlation
- Runtime Diagnostics
- Request ID / Trace ID Propagation

Observability 的目标不是替代 Prometheus、Grafana、OpenTelemetry 等成熟生态，而是在项目内部提供统一埋点规范、追踪上下文和诊断入口，便于后续对接外部可观测性平台。

# SSO 与 IAM 的关系

项目设计中明确区分：

## SSO

负责：

```text
用户是谁
```

## IAM

负责：

```text
用户属于哪个组织
用户拥有哪些权限
用户可以访问哪些资源
用户可以看到哪些数据
用户的行为如何审计
```

推荐模式：

```text
SSO 负责认证
IAM 负责授权
```

---

# 业务系统接入方式

业务系统接入 IAM 时无需自行实现权限逻辑。

标准流程：

```text
注册资源
    ↓
注册动作
    ↓
注册权限
    ↓
角色授权
    ↓
ACL授权
    ↓
策略配置
    ↓
调用统一授权入口
```

---

# 当前完成情况

## 已完成

### IAM Core（主链路已完成）

- Identity
- Authentication
- Session
- RBAC
- Resource ACL
- Policy Engine
- Data Scope
- Audit

### Storage

- 对象上传
- 对象引用管理
- IAM接入

### Common

- 配置中心
- 缓存抽象
- 日志体系

---

### Runtime

- Runtime Message Contract
- SQL WAL Outbox
- ACK / Retry / Dead Letter
- Backend Runtime Connector
- IPC Wakeup
- Memory Broker
- Redis / ValKey Broker

## 建设中

### IAM

- 管理后台
- OAuth2
- OIDC
- LDAP
- 企业微信
- 钉钉

### Runtime

- WebSocket Runtime Master
- Frontend Realtime Connection
- Cross-node Dispatch
- Presence Synchronization
- Runtime Management API

### Observability

- Structured Logging
- Metrics
- Distributed Tracing
- Health Check
- Audit Correlation
- Runtime Diagnostics

---

# 项目结构

```text
src/
├── ns_backend/
│   ├── backend/
│   ├── iam/
│   └── storage/
│
└── ns_common/
    ├── cache/
    ├── runtime/
    ├── storage/
    └── config/

sql/
docs/
```

# 技术栈

- Python
- Django 5
- DRF
- ADRF
- Authlib
- Redis
- Valkey
- MinIO
- MySQL
- PostgreSQL
- SQLite

---

# Love JingSun forever !
