# IAM Infra Schema Installer

本目录定义 IAM 基础设施静态 DDL 的标准路径与初始化约定。

## 标准 SQL 路径

基础设施建表 SQL 统一路径：

`sql/create/{infra_domain}/{vendor}.sql`

当前 IAM 对应路径：

`sql/create/iam/{vendor}.sql`

## 当前支持状态

- `iam/mysql.sql`
- `iam/sqlite.sql`
- `iam/postgresql.sql`
- `dm8` 仅识别 vendor，`iam/dm8.sql` 暂缓；缺失 SQL 时初始化必须失败

## 初始化顺序

```bash
python manage.py install_infra_schema --domain iam
python manage.py init_admin
```

## Dry-run

```bash
python manage.py install_infra_schema --domain iam --dry-run
```

## 幂等策略

- 目标表全部已存在：跳过执行
- 目标表部分存在：直接失败，提示半初始化风险并要求人工确认
- 不提供自动 `drop` / `overwrite` / `force`

## 方案边界

- 继续使用静态 DDL + `managed=False`
- 不引入 Django migrations 作为替代

