# ns_vault 长期架构决策

## 文档声明

设计边界与 ADR 冲突时，以设计边界为准。

ADR 不记录实现进度，不记录当前工作区状态。PROVISIONAL 不得由实施工作包自行补全。

状态：

- ACCEPTED
- PROVISIONAL
- SUPERSEDED

## ADR-001 中心化 ns_vault

状态：ACCEPTED

背景：系统需要统一管理 Key、Secret、PKI 和动态凭证。

决策：建立独立 ns_vault 安全服务。

后果：安全状态不归 ns_backend 所有。

关联阶段：Foundation Layer。

## ADR-002 ns_backend 控制面

状态：ACCEPTED

决策：ns_backend.vault 负责控制面，ns_vault 负责执行权威。

后果：禁止 backend 直接修改 Vault Authority Storage。

## ADR-003 Policy Intent 与 Artifact

状态：ACCEPTED

决策：backend 管理 Policy Intent，Vault 执行 Policy Artifact。

后果：授权执行保持独立安全边界。

## ADR-004 Tenant Key Domain

状态：ACCEPTED

决策：每个 Tenant 使用独立密码学隔离域。

后果：支持 BYOK、HYOK 和独立销毁。

## ADR-005 Envelope Encryption

状态：ACCEPTED

决策：Secret 使用 DEK 加密，KEK 包装 DEK。

后果：支持轮换和 rewrap。

## ADR-006 Provider Host

状态：ACCEPTED

决策：Provider 在隔离 Host 中执行。

后果：Provider 不进入核心 Authority。

## ADR-007 Identity Federation

状态：ACCEPTED

决策：身份认证与 Vault 授权分离。

后果：SSO、runtime、node 均作为 Identity Provider 接入。

## ADR-008 Command/Event/Projection

状态：ACCEPTED

决策：控制命令、执行事实和投影分离。

后果：Vault Actual State 为唯一安全事实。

## ADR-009 HA 与灾备

状态：ACCEPTED

决策：Tenant Key Domain 单写，多区域热备。

后果：禁止安全状态多写。

## ADR-010 分层进程模型

状态：ACCEPTED

决策：API、Control Plane、Crypto Authority、Provider Host、Audit 独立安全域。

后果：降低失陷范围。
