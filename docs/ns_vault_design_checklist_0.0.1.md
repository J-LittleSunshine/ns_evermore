# ns_vault 设计边界与功能清单

> 文档状态：DESIGN_BASELINE
>
> 本文档描述 ns_vault 的最终设计边界，不描述当前实现进度。

## 文档用途

ns_vault 是 ns_evermore 的中心化密钥、秘密、证书与动态凭证安全服务。本文档定义最终产品、安全边界、能力边界和禁止事项。

## 权威顺序

1. 本设计边界文档定义最终产品形态。
2. 架构决策文档定义长期约束。
3. 实现事实来自实际代码、配置、Migration 和测试。
4. 实施计划维护当前执行状态。
5. 验收日志只记录历史事实。

## 产品定位

ns_vault 是独立安全执行权威，为内部组件和外部客户提供统一的 Key、Secret、PKI、Transit、动态凭证和 Workload Identity 安全能力。

## 核心边界

- ns_backend.vault 是控制面，不是安全权威。
- ns_vault 维护实际安全状态。
- ns_backend 不保存 Secret 明文、根密钥、KEK 或私钥材料。
- ns_vault 不替代 SSO、IAM 用户目录或普通配置中心。

## 多租户模型

资源模型：

Tenant → Project → Namespace → Resource

Tenant 是密码学隔离边界，并拥有独立 Tenant Key Domain。

## 加密模型

采用 Envelope Encryption：

Tenant KEK → Wrapped DEK → Secret Ciphertext

Secret Version 是不可变密码学单位。

## 明文边界

Secret 明文只允许进入 ns_vault 安全执行边界。

默认采用受控交付：

- Agent 注入；
- FD；
- Socket；
- Named Pipe；
- tmpfs。

ns_backend 不代理 Secret 明文。

## 身份与授权

采用 Workload Identity Federation。

身份与授权分离：

- Identity Provider 提供身份事实；
- Vault 负责 Principal Binding、Policy、Capability 和最终授权。

## Provider

采用 Provider Host 隔离模型。

支持：

- Software Provider；
- HSM；
- KMS；
- BYOK；
- HYOK；
- 外部安全 Provider。

## 组件兼容

- ns_runtime 通过 Authority Broker 获取 Vault Capability。
- ns_node 仅代表 node identity 获取 node-scoped Secret。
- ns_client 提供统一安全接入。
- 未来 SSO 仅作为 Identity Provider，不承担 Vault 授权。

## 非目标

ns_vault 不作为：

- 通用配置中心；
- 人员密码管理器；
- 文件保险箱；
- 通用文档存储；
- 通用工作流系统。

## 设计原则

- 默认拒绝；
- 最小权限；
- 强审计；
- 权威状态唯一；
- 不通过实施成本降低最终安全边界。
