from ns_backend import settings

IAM_DB_ALIAS = settings.DATABASE_ROUTER_MAP.get("iam", "default")
