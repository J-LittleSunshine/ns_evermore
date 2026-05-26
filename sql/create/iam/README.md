# IAM Create SQL Directory Contract

本目录定义 IAM 基础模块建库 SQL 的标准入口与约定。

## 标准路径

IAM create SQL 使用目录式路径：

`sql/create/iam/{vendor}.sql`

当前 `vendor` 约定与 `ns_backend.db_vendor` 保持一致：

- `mysql`
- `sqlite`
- `postgresql`
- `dm8`

## 当前完成状态

- `mysql.sql`：已完成，来自旧 `sql/create/create_iam.sql` 迁移
- `sqlite.sql`：待补
- `postgresql.sql`：待补
- `dm8.sql`：待补（后续需要在真实达梦8实例验证）

## 旧路径状态

旧入口 `sql/create/create_iam.sql` 已删除，不再作为标准入口。

## 目录职责边界

本目录只存放静态 DDL：

- 不包含建表器
- 不自动执行 SQL
- 不负责 migration
- ORM 仍保持 `managed=False`
- 后续 schema installer 会基于 `INFRA_CREATE_SQL_PATH_MAP` 定位 SQL 文件

## 后续补齐顺序建议

1. `sqlite.sql`
2. `postgresql.sql`
3. `dm8.sql`

