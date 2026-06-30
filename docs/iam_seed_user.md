# IAM 种子用户初始化说明

本文档用于本地开发环境初始化 IAM 内置用户。

用户创建逻辑已经封装在 Django management command 中：

```bash
python manage.py init_iam_users
```

本文档只说明该命令的使用方式、参数含义、登录验证方式和常见问题。

## 1. 适用范围

适用于：

- local 环境；
- dev 环境；
- 首次初始化后没有可登录用户的场景；
- 本地开发需要获取用户 `access_token` 的场景。

不适用于：

- 生产环境直接照搬；
- 正式管理员账号下发；
- 正式权限模型初始化；
- 业务资源、角色、策略、ACL 初始化。

## 2. 管理命令能力

命令文件：

```text
src/ns_backend/iam/management/commands/init_iam_users.py
```

命令名称：

```bash
python manage.py init_iam_users
```

默认会初始化两个用户：

| 用户    | 默认用户名   | 说明      |
|-------|---------|---------|
| admin | `admin` | 系统管理员用户 |
| dev   | `dev`   | 本地开发用户  |

默认情况下，如果不传密码，命令会自动生成随机密码，并且只在命令输出中显示一次。

## 3. 推荐初始化方式

本地开发建议显式指定密码，便于重复联调。

```bash
PYTHONPATH=src python manage.py init_iam_users \
  --admin-username admin \
  --admin-password 'Admin@123456' \
  --dev-username dev \
  --dev-password 'Dev@123456'
```

预期输出会包含：

```text
IAM user 'admin' created.
Initial password for 'admin' (provided, shown once): Admin@123456

IAM user 'dev' created.
Initial password for 'dev' (provided, shown once): Dev@123456
```

如果用户已存在，命令会更新用户基础信息，并默认重置密码。

## 4. 使用随机密码

如果不希望在命令行中明文写密码，可以不传密码参数：

```bash
PYTHONPATH=src python manage.py init_iam_users
```

命令会自动生成密码，并在输出中显示一次。

注意：

```text
Store generated passwords securely. They cannot be displayed again.
```

生成密码只显示一次，应立即保存到本地安全位置。

## 5. 不重置已有用户密码

如果只希望补齐或更新用户基础属性，不希望覆盖已有密码：

```bash
PYTHONPATH=src python manage.py init_iam_users \
  --no-reset-password
```

也可以配合用户名参数使用：

```bash
PYTHONPATH=src python manage.py init_iam_users \
  --admin-username admin \
  --dev-username dev \
  --no-reset-password
```

## 6. 指定数据库 alias

默认情况下，命令会根据 IAM model 和数据库路由解析 IAM 数据库 alias。

如果需要手动指定数据库 alias：

```bash
PYTHONPATH=src python manage.py init_iam_users \
  --database iam \
  --admin-username admin \
  --admin-password 'Admin@123456' \
  --dev-username dev \
  --dev-password 'Dev@123456'
```

如果指定的 alias 不存在，命令会报错并列出可用 alias。

## 7. 用户属性说明

命令会创建或更新两个内置用户。

### 7.1 admin 用户

默认：

```text
username     = admin
display_name = System Administrator
user_type    = PERSONAL
is_active    = 1
is_staff     = 1
is_superuser = 1
```

### 7.2 dev 用户

默认：

```text
username     = dev
display_name = Development User
user_type    = PERSONAL
is_active    = 1
is_staff     = 0
is_superuser = 0
```

说明：

- `admin` 用于本地管理和初始化验证；
- `dev` 用于普通开发用户联调；
- 密码会通过 Django `make_password()` 写入，不会明文存储；
- 已存在用户会被 update，不会重复创建同名用户。

## 8. 启动后端

```bash
python manage.py runserver 127.0.0.1:8080
```

## 9. 调用登录接口

登录接口：

```text
POST /api/iam/auth/login/
```

使用 admin 登录：

```bash
curl -s -X POST http://127.0.0.1:8080/api/iam/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin",
    "password": "Admin@123456",
    "device_id": "iam-seed-login-cli",
    "device_name": "IAM Seed Login CLI",
    "device_type": "CLI"
  }'
```

使用 dev 登录：

```bash
curl -s -X POST http://127.0.0.1:8080/api/iam/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "dev",
    "password": "Dev@123456",
    "device_id": "iam-seed-login-cli",
    "device_name": "IAM Seed Login CLI",
    "device_type": "CLI"
  }'
```

登录成功后，响应中应包含：

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer",
  "session_id": "...",
  "expires_in": 1800,
  "user": {}
}
```

如果项目统一响应结构包裹返回值，可能是：

```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "Bearer",
    "session_id": "...",
    "expires_in": 1800,
    "user": {}
  }
}
```

## 10. 提取 access token

如果本地安装了 `jq`：

```bash
ACCESS_TOKEN=$(curl -s -X POST http://127.0.0.1:8080/api/iam/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin",
    "password": "Admin@123456",
    "device_id": "iam-seed-login-cli",
    "device_name": "IAM Seed Login CLI",
    "device_type": "CLI"
  }' | jq -r '.data.access_token // .access_token')

echo "$ACCESS_TOKEN"
```

如果没有 `jq`，直接查看完整响应并手动复制 `access_token`。

## 11. 验证当前用户接口

拿到 `access_token` 后，可以调用当前用户接口验证 token 是否有效：

```bash
curl -s -X POST http://127.0.0.1:8080/api/iam/auth/current_user/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{}'
```

预期能返回当前用户信息。

## 12. 常见错误

### 12.1 用户名或密码错误

现象可能包括：

```text
IAM_CREDENTIAL_INVALID
```

处理：

重新确认初始化命令中的用户名和密码。

如果忘记密码，可以重新执行：

```bash
PYTHONPATH=src python manage.py init_iam_users \
  --admin-username admin \
  --admin-password 'Admin@123456' \
  --dev-username dev \
  --dev-password 'Dev@123456'
```

### 12.2 用户不可用

现象可能包括：

```text
USER_DISABLED
USER_INACTIVE
USER_NOT_FOUND
```

处理：

重新执行 `init_iam_users`，命令会将内置用户恢复为 active 状态。

### 12.3 access token 无效或过期

现象可能包括：

```text
TOKEN_INACTIVE
USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED
```

处理：

重新调用 `/api/iam/auth/login/` 获取新的 `access_token`。

### 12.4 数据库 alias 错误

现象可能包括：

```text
Unknown database alias
```

处理：

检查 `etc/ns_config.local.json` 中的数据库配置，或显式指定：

```bash
PYTHONPATH=src python manage.py init_iam_users --database iam
```

### 12.5 数据库表不存在

现象可能包括：

```text
no such table: iam_user
relation "iam_user" does not exist
```

处理：

先完成 IAM 数据库表初始化，再执行：

```bash
PYTHONPATH=src python manage.py init_iam_users
```

## 13. 与后续联调的关系

本文档只负责初始化 IAM 可登录用户。

后续如果其他模块需要用户 `access_token`，可以使用本文档创建的 `admin` 或 `dev` 用户登录获取。

具体模块权限、资源、策略、ACL，应由对应模块自己的初始化文档或管理命令负责，不应写在本文档中。