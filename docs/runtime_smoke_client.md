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
```

`backend.iam_internal_token` 必须与 `runtime.iam.internal_token` 完全一致。

注意：`iam_internal_token` 不是用户 `access_token`，不能传给 smoke client 的 `--access-token`。

## 3. 准备配置

复制示例配置：

```bash
cp etc/ns_config.example.json etc/ns_config.local.json
```

检查以下配置：

```json
{
  "runtime": {
    "enabled": true,
    "server": {
      "websocket": {
        "host": "127.0.0.1",
        "port": 8765,
        "path": "/runtime/ws"
      }
    },
    "iam": {
      "base_url": "http://127.0.0.1:8080/api/iam",
      "internal_token": "change-me-iam-internal-token-at-least-32-chars"
    }
  }
}
```

## 4. 启动后端

```bash
python manage.py runserver 127.0.0.1:8080
```

## 5. 启动 runtime

```bash
PYTHONPATH=src python -m ns_runtime.main
```

只检查配置：

```bash
PYTHONPATH=src python -m ns_runtime.main --check-config
```

## 6. 获取用户 access token

调用 IAM 登录接口：

```bash
curl -s -X POST http://127.0.0.1:8080/api/iam/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "your-username",
    "password": "your-password",
    "device_id": "runtime-smoke-client-01",
    "device_name": "Runtime Smoke Client",
    "device_type": "CLI"
  }'
```

从响应中复制 `access_token`。

不要使用：

```text
change-me-iam-internal-token-at-least-32-chars
```

它是 internal token，不是用户 access token。

## 7. 基础 smoke 测试

```bash
PYTHONPATH=src python -m ns_runtime.smoke_client \
  --access-token 'your-user-access-token'
```

预期结果包括：

```text
[smoke] connection accepted
[smoke] heartbeat pong received
[smoke] processor response received
[smoke] stats:
```

## 8. ACK 测试

```bash
PYTHONPATH=src python -m ns_runtime.smoke_client \
  --access-token 'your-user-access-token' \
  --requires-ack \
  --response-requires-ack
```

打印完整 envelope：

```bash
PYTHONPATH=src python -m ns_runtime.smoke_client \
  --access-token 'your-user-access-token' \
  --requires-ack \
  --response-requires-ack \
  --dump-envelopes
```

## 9. burst / backpressure 测试

```bash
PYTHONPATH=src python -m ns_runtime.smoke_client \
  --access-token 'your-user-access-token' \
  --burst-count 20
```

如果测试环境将 `runtime.default_connection_max_inflight` 调得很小，例如 `1`，可以验证 backpressure：

```bash
PYTHONPATH=src python -m ns_runtime.smoke_client \
  --access-token 'your-user-access-token' \
  --burst-count 20 \
  --expect-backpressure
```

## 10. 常见错误

### 10.1 internal service token is invalid

现象：

```text
IAM_RUNTIME_ACCESS_DENIED
internal service token is invalid
```

原因：

`backend.iam_internal_token` 与 `runtime.iam.internal_token` 不一致。

处理：

让两个配置值完全一致，并重启 backend 和 runtime。

### 10.2 TOKEN_INACTIVE

现象：

```text
connection.rejected
reason=TOKEN_INACTIVE
```

原因：

smoke client 的 `--access-token` 不是有效用户 access token，常见情况包括：

- 使用了占位符 `<frontend_access_token>`
- 错把 internal token 当成 access token
- access token 已过期
- 用户 session 已过期或被撤销
- 用户被禁用

处理：

重新调用 `/api/iam/auth/login/` 获取真实用户 `access_token`。

### 10.3 CONNECTION_ACCESS_DENIED

现象：

```text
connection.rejected
reason=CONNECTION_ACCESS_DENIED
```

原因：

用户 token 有效，但 IAM 权限策略未放行 runtime 连接。

默认检查上下文：

```text
resource_type = ns_runtime_connection
resource_id = ns_client
action_code = connect
```

处理：

检查 IAM 中对应用户、角色、策略或 ACL 是否允许连接 runtime。

## 11. 校验命令

```bash
# 1. 校验 JSON 格式
python -m json.tool etc/ns_config.example.json >/tmp/ns_config.example.checked.json

# 2. 校验 runtime 配置
PYTHONPATH=src python -m ns_runtime.main --check-config

# 3. 确认文档关键段落存在
grep -nE '基础 smoke 测试|ACK 测试|TOKEN_INACTIVE|CONNECTION_ACCESS_DENIED' docs/runtime_smoke_client.md

# 4. smoke client 入口仍可用
PYTHONPATH=src python -m ns_runtime.smoke_client --help
```