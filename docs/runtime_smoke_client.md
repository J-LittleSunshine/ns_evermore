# Runtime Smoke Client 联调说明

本文档用于本地手工验证 NsEvermore runtime WebSocket 链路。

## 1. 适用范围

`ns_runtime.smoke_client` 只用于开发和联调，不接入生产启动流程。

它覆盖：

- `connection.hello`
- `connection.accepted` / `connection.rejected`
- `heartbeat.ping` / `heartbeat.pong`
- `processor.request` / `processor.response` / `processor.error`
- `runtime.echo`
- `requires_ack`
- `response_requires_ack`
- burst 请求
- backpressure 观察
- envelope dump

不覆盖：

- 自动化测试框架
- CI
- mock IAM
- 自动获取 access token
- token refresh
- message store
- retry
- routing

## 2. Token 关系

runtime 联调涉及两类 token，不能混用。

| Token                        | 配置或来源                       | 用途                                           |
|------------------------------|-----------------------------|----------------------------------------------|
| `backend.iam_internal_token` | Django backend 配置           | IAM internal API 期望的服务间 token                |
| `runtime.iam.internal_token` | runtime 配置                  | runtime 调 IAM internal API 时携带的服务间 token     |
| 用户 `access_token`            | `/api/iam/auth/login/` 登录返回 | smoke client 发起 `connection.hello` 时代表前端用户身份 |

要求：

```json
{
  "backend": {
    "iam_internal_token": "same-internal-token"
  },
  "runtime": {
    "iam": {
      "internal_token": "same-internal-token"
    }
  }
}