# -*- coding: utf-8 -*-
from __future__ import annotations

import ipaddress
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    Literal,
    Mapping,
)
from urllib.parse import urlparse

from ns_common.exceptions import NsConfigError

RuntimeMode = Literal["master", "sub_node", "singleton"]
RuntimeIamFailPolicy = Literal["fail_closed", "fail_open"]
RuntimeStoreBackend = Literal["sqlite_wal", "redis", "valkey"]
RuntimeAuditStoreBackend = Literal["sqlite_wal", "direct_db", "http_api"]
RuntimeMigrationPolicy = Literal["wait", "reject", "proxy"]
RuntimeBackpressurePolicy = Literal["reject", "queue", "timeout_queue"]


def _ensure_object(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise NsConfigError(
            f"{field_name} must be a JSON object.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    return dict(value)


def _reject_unknown_keys(data: Mapping[str, Any], *, field_name: str, allowed_keys: set[str]) -> None:
    unknown_keys = sorted(set(data.keys()) - allowed_keys)

    if unknown_keys:
        raise NsConfigError(
            f"{field_name} contains unknown field.",
            details={
                "field": field_name,
                "unknown_keys": unknown_keys,
                "allowed_keys": sorted(allowed_keys),
            },
        )


def _validate_bool(field_name: str, value: Any) -> None:
    if not isinstance(value, bool):
        raise NsConfigError(
            f"{field_name} must be a boolean.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


def _validate_non_empty_text(field_name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise NsConfigError(
            f"{field_name} must be a non-empty string.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


def _validate_positive_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise NsConfigError(
            f"{field_name} must be a positive integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


def _validate_non_negative_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise NsConfigError(
            f"{field_name} must be a non-negative integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


def _validate_port(field_name: str, value: Any) -> None:
    _validate_positive_int(field_name, value)

    if int(value) > 65535:
        raise NsConfigError(
            f"{field_name} must be between 1 and 65535.",
            details={
                "field": field_name,
                "value": value,
            },
        )


def _validate_url(field_name: str, value: Any, *, allowed_schemes: set[str], required: bool) -> None:
    if value is None or str(value).strip() == "":
        if required:
            raise NsConfigError(
                f"{field_name} must be configured.",
                details={
                    "field": field_name,
                    "value": value,
                },
            )
        return

    normalized = str(value).strip()
    parsed = urlparse(normalized)

    if parsed.scheme not in allowed_schemes:
        raise NsConfigError(
            f"{field_name} scheme is invalid.",
            details={
                "field": field_name,
                "scheme": parsed.scheme,
                "allowed_schemes": sorted(allowed_schemes),
            },
        )

    if not parsed.hostname:
        raise NsConfigError(
            f"{field_name} host is required.",
            details={
                "field": field_name,
                "value": normalized,
            },
        )


def _validate_path(field_name: str, value: Any) -> None:
    _validate_non_empty_text(field_name, value)

    if not str(value).startswith("/"):
        raise NsConfigError(
            f"{field_name} must start with '/'.",
            details={
                "field": field_name,
                "value": value,
            },
        )


def _validate_text_list(field_name: str, value: Any) -> None:
    if not isinstance(value, list):
        raise NsConfigError(
            f"{field_name} must be a list.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise NsConfigError(
                f"{field_name} item must be a non-empty string.",
                details={
                    "field": field_name,
                    "index": index,
                    "value": item,
                    "actual_type": type(item).__name__,
                },
            )


def _validate_object_list(field_name: str, value: Any) -> None:
    if not isinstance(value, list):
        raise NsConfigError(
            f"{field_name} must be a list.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise NsConfigError(
                f"{field_name} item must be a JSON object.",
                details={
                    "field": field_name,
                    "index": index,
                    "actual_type": type(item).__name__,
                },
            )


def _validate_trusted_proxy(field_name: str, value: str) -> None:
    try:
        ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise NsConfigError(
            f"{field_name} contains invalid IP address or CIDR.",
            details={
                "field": field_name,
                "value": value,
            },
        ) from exc


@dataclass(slots=True, kw_only=True)
class NsRuntimeWebSocketConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    path: str = "/runtime/ws"
    ping_interval_seconds: int = 20
    ping_timeout_seconds: int = 20
    max_message_size_bytes: int = 1048576

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeWebSocketConfig":
        data = _ensure_object(value, "runtime.server.websocket")
        _reject_unknown_keys(
            data,
            field_name="runtime.server.websocket",
            allowed_keys={
                "host",
                "port",
                "path",
                "ping_interval_seconds",
                "ping_timeout_seconds",
                "max_message_size_bytes",
            },
        )
        config = cls(**data)
        config.validate()
        return config

    def validate(self) -> None:
        _validate_non_empty_text("runtime.server.websocket.host", self.host)
        _validate_port("runtime.server.websocket.port", self.port)
        _validate_path("runtime.server.websocket.path", self.path)
        _validate_positive_int("runtime.server.websocket.ping_interval_seconds", self.ping_interval_seconds)
        _validate_positive_int("runtime.server.websocket.ping_timeout_seconds", self.ping_timeout_seconds)
        _validate_positive_int("runtime.server.websocket.max_message_size_bytes", self.max_message_size_bytes)


@dataclass(slots=True, kw_only=True)
class NsRuntimeAdminHttpConfig:
    host: str = "127.0.0.1"
    port: int = 8766
    path: str = "/admin/action"

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeAdminHttpConfig":
        data = _ensure_object(value, "runtime.server.admin_http")
        _reject_unknown_keys(
            data,
            field_name="runtime.server.admin_http",
            allowed_keys={
                "host",
                "port",
                "path",
            },
        )
        config = cls(**data)
        config.validate()
        return config

    def validate(self) -> None:
        _validate_non_empty_text("runtime.server.admin_http.host", self.host)
        _validate_port("runtime.server.admin_http.port", self.port)
        _validate_path("runtime.server.admin_http.path", self.path)


@dataclass(slots=True, kw_only=True)
class NsRuntimeServerConfig:
    websocket: NsRuntimeWebSocketConfig = field(default_factory=NsRuntimeWebSocketConfig)
    admin_http: NsRuntimeAdminHttpConfig = field(default_factory=NsRuntimeAdminHttpConfig)
    trusted_proxies: list[str] = field(
        default_factory=lambda: [
            "127.0.0.1",
        ]
    )

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeServerConfig":
        data = _ensure_object(value, "runtime.server")
        _reject_unknown_keys(
            data,
            field_name="runtime.server",
            allowed_keys={
                "websocket",
                "admin_http",
                "trusted_proxies",
            },
        )
        config = cls(
            websocket=NsRuntimeWebSocketConfig.from_mapping(data.get("websocket")),
            admin_http=NsRuntimeAdminHttpConfig.from_mapping(data.get("admin_http")),
            trusted_proxies=list(data.get("trusted_proxies", [
                "127.0.0.1"
            ]
            )
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        self.websocket.validate()
        self.admin_http.validate()
        _validate_text_list("runtime.server.trusted_proxies", self.trusted_proxies)

        for item in self.trusted_proxies:
            _validate_trusted_proxy("runtime.server.trusted_proxies", item)


@dataclass(slots=True, kw_only=True)
class NsRuntimeAccessCheckTemplateConfig:
    resource_type: str = "ns_runtime_connection"
    resource_id: str = "{{ client_type }}"
    action_code: str = "connect"
    context: dict[str, Any] = field(
        default_factory=lambda: {
            "runtime_id": "{{ runtime_id }}",
            "cluster_id": "{{ cluster_id }}",
            "mode": "{{ mode }}",
            "client_type": "{{ client_type }}",
            "node_id": "{{ node_id }}",
            "node_group": "{{ node_group }}",
        }
    )

    @classmethod
    def from_mapping(
            cls,
            value: Any,
            *,
            field_name: str,
            default_resource_type: str,
            default_resource_id: str,
            default_action_code: str,
            default_context: dict[str, Any],
    ) -> "NsRuntimeAccessCheckTemplateConfig":
        data = _ensure_object(value, field_name)
        _reject_unknown_keys(
            data,
            field_name=field_name,
            allowed_keys={
                "resource_type",
                "resource_id",
                "action_code",
                "context",
            },
        )
        config = cls(
            resource_type=str(data.get("resource_type", default_resource_type)),
            resource_id=str(data.get("resource_id", default_resource_id)),
            action_code=str(data.get("action_code", default_action_code)),
            context=dict(data.get("context", default_context)),
        )
        config.validate(field_name)
        return config

    def validate(self, field_name: str) -> None:
        _validate_non_empty_text(f"{field_name}.resource_type", self.resource_type)
        _validate_non_empty_text(f"{field_name}.resource_id", self.resource_id)
        _validate_non_empty_text(f"{field_name}.action_code", self.action_code)

        if not isinstance(self.context, dict):
            raise NsConfigError(
                f"{field_name}.context must be a JSON object.",
                details={
                    "field": f"{field_name}.context",
                    "actual_type": type(self.context).__name__,
                },
            )


@dataclass(slots=True, kw_only=True)
class NsRuntimeIamConnectionAccessCheckConfig:
    enabled: bool = True
    template: NsRuntimeAccessCheckTemplateConfig = field(
        default_factory=NsRuntimeAccessCheckTemplateConfig
    )

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeIamConnectionAccessCheckConfig":
        data = _ensure_object(value, "runtime.iam.connection_access_check")
        _reject_unknown_keys(
            data,
            field_name="runtime.iam.connection_access_check",
            allowed_keys={
                "enabled",
                "template",
            },
        )
        config = cls(
            enabled=bool(data.get("enabled", True)),
            template=NsRuntimeAccessCheckTemplateConfig.from_mapping(
                data.get("template"),
                field_name="runtime.iam.connection_access_check.template",
                default_resource_type="ns_runtime_connection",
                default_resource_id="{{ client_type }}",
                default_action_code="connect",
                default_context={
                    "runtime_id": "{{ runtime_id }}",
                    "cluster_id": "{{ cluster_id }}",
                    "mode": "{{ mode }}",
                    "client_type": "{{ client_type }}",
                    "node_id": "{{ node_id }}",
                    "node_group": "{{ node_group }}",
                },
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_bool("runtime.iam.connection_access_check.enabled", self.enabled)
        self.template.validate("runtime.iam.connection_access_check.template")


@dataclass(slots=True, kw_only=True)
class NsRuntimeIamConfig:
    base_url: str = "http://127.0.0.1:8080/api/iam"
    internal_token: str = "change-me-runtime-iam-internal-token"
    fail_policy: RuntimeIamFailPolicy = "fail_closed"
    introspection_cache_ttl_seconds: int = 60
    invalid_cache_ttl_seconds: int = 10
    connection_access_check: NsRuntimeIamConnectionAccessCheckConfig = field(
        default_factory=NsRuntimeIamConnectionAccessCheckConfig
    )

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeIamConfig":
        data = _ensure_object(value, "runtime.iam")
        _reject_unknown_keys(
            data,
            field_name="runtime.iam",
            allowed_keys={
                "base_url",
                "internal_token",
                "fail_policy",
                "introspection_cache_ttl_seconds",
                "invalid_cache_ttl_seconds",
                "connection_access_check",
            },
        )
        config = cls(
            base_url=str(data.get("base_url", "http://127.0.0.1:8080/api/iam")),
            internal_token=str(data.get("internal_token", "change-me-runtime-iam-internal-token")),
            fail_policy=data.get("fail_policy", "fail_closed"),
            introspection_cache_ttl_seconds=int(data.get("introspection_cache_ttl_seconds", 60)),
            invalid_cache_ttl_seconds=int(data.get("invalid_cache_ttl_seconds", 10)),
            connection_access_check=NsRuntimeIamConnectionAccessCheckConfig.from_mapping(
                data.get("connection_access_check")
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_url(
            "runtime.iam.base_url",
            self.base_url,
            allowed_schemes={
                "http",
                "https",
            },
            required=True,
        )
        _validate_non_empty_text("runtime.iam.internal_token", self.internal_token)

        if self.fail_policy not in {"fail_closed", "fail_open"}:
            raise NsConfigError(
                "runtime.iam.fail_policy is invalid.",
                details={
                    "field": "runtime.iam.fail_policy",
                    "value": self.fail_policy,
                    "allowed_values": [
                        "fail_closed",
                        "fail_open",
                    ],
                },
            )

        _validate_positive_int("runtime.iam.introspection_cache_ttl_seconds", self.introspection_cache_ttl_seconds)
        _validate_positive_int("runtime.iam.invalid_cache_ttl_seconds", self.invalid_cache_ttl_seconds)
        self.connection_access_check.validate()


@dataclass(slots=True, kw_only=True)
class NsRuntimeClusterConfig:
    master_urls: list[str] = field(default_factory=list)
    shard_key_fields: list[str] = field(
        default_factory=lambda: [
            "payload.tenant_id",
            "payload.company_id",
            "metadata.tenant_id",
            "metadata.company_id",
            "node_group",
            "target_type+message_type",
            "client_type",
            "message_id",
        ]
    )
    lease_ttl_seconds: int = 30
    lease_renew_interval_seconds: int = 10
    migration_policy: RuntimeMigrationPolicy = "proxy"
    auto_degrade_enabled: bool = True
    master_unavailable_threshold_seconds: int = 60
    auto_recover_enabled: bool = True

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeClusterConfig":
        data = _ensure_object(value, "runtime.cluster")
        _reject_unknown_keys(
            data,
            field_name="runtime.cluster",
            allowed_keys={
                "master_urls",
                "shard_key_fields",
                "lease_ttl_seconds",
                "lease_renew_interval_seconds",
                "migration_policy",
                "auto_degrade_enabled",
                "master_unavailable_threshold_seconds",
                "auto_recover_enabled",
            },
        )
        config = cls(
            master_urls=list(data.get("master_urls", [])),
            shard_key_fields=list(
                data.get(
                    "shard_key_fields",
                    [
                        "payload.tenant_id",
                        "payload.company_id",
                        "metadata.tenant_id",
                        "metadata.company_id",
                        "node_group",
                        "target_type+message_type",
                        "client_type",
                        "message_id",
                    ],
                )
            ),
            lease_ttl_seconds=int(data.get("lease_ttl_seconds", 30)),
            lease_renew_interval_seconds=int(data.get("lease_renew_interval_seconds", 10)),
            migration_policy=data.get("migration_policy", "proxy"),
            auto_degrade_enabled=bool(data.get("auto_degrade_enabled", True)),
            master_unavailable_threshold_seconds=int(data.get("master_unavailable_threshold_seconds", 60)),
            auto_recover_enabled=bool(data.get("auto_recover_enabled", True)),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_text_list("runtime.cluster.master_urls", self.master_urls)
        for url in self.master_urls:
            _validate_url(
                "runtime.cluster.master_urls",
                url,
                allowed_schemes={
                    "ws",
                    "wss",
                    "http",
                    "https",
                },
                required=True,
            )

        _validate_text_list("runtime.cluster.shard_key_fields", self.shard_key_fields)
        _validate_positive_int("runtime.cluster.lease_ttl_seconds", self.lease_ttl_seconds)
        _validate_positive_int("runtime.cluster.lease_renew_interval_seconds", self.lease_renew_interval_seconds)

        if self.lease_renew_interval_seconds >= self.lease_ttl_seconds:
            raise NsConfigError(
                "runtime.cluster.lease_renew_interval_seconds must be less than runtime.cluster.lease_ttl_seconds.",
                details={
                    "field": "runtime.cluster.lease_renew_interval_seconds",
                    "lease_renew_interval_seconds": self.lease_renew_interval_seconds,
                    "lease_ttl_seconds": self.lease_ttl_seconds,
                },
            )

        if self.migration_policy not in {"wait", "reject", "proxy"}:
            raise NsConfigError(
                "runtime.cluster.migration_policy is invalid.",
                details={
                    "field": "runtime.cluster.migration_policy",
                    "value": self.migration_policy,
                    "allowed_values": [
                        "wait",
                        "reject",
                        "proxy",
                    ],
                },
            )

        _validate_bool("runtime.cluster.auto_degrade_enabled", self.auto_degrade_enabled)
        _validate_positive_int("runtime.cluster.master_unavailable_threshold_seconds", self.master_unavailable_threshold_seconds)
        _validate_bool("runtime.cluster.auto_recover_enabled", self.auto_recover_enabled)


@dataclass(slots=True, kw_only=True)
class NsRuntimeStoreConfig:
    backend: RuntimeStoreBackend = "sqlite_wal"
    sqlite_path: str = ""
    redis_url: str = ""
    key_prefix: str = ""

    @classmethod
    def from_mapping(
            cls,
            value: Any,
            *,
            field_name: str,
            default_sqlite_path: str,
            default_key_prefix: str,
    ) -> "NsRuntimeStoreConfig":
        data = _ensure_object(value, field_name)
        _reject_unknown_keys(
            data,
            field_name=field_name,
            allowed_keys={
                "backend",
                "sqlite_path",
                "redis_url",
                "key_prefix",
            },
        )
        config = cls(
            backend=data.get("backend", "sqlite_wal"),
            sqlite_path=str(data.get("sqlite_path", default_sqlite_path)),
            redis_url=str(data.get("redis_url", "")),
            key_prefix=str(data.get("key_prefix", default_key_prefix)),
        )
        config.validate(field_name)
        return config

    def validate(self, field_name: str) -> None:
        if self.backend not in {"sqlite_wal", "redis", "valkey"}:
            raise NsConfigError(
                f"{field_name}.backend is invalid.",
                details={
                    "field": f"{field_name}.backend",
                    "value": self.backend,
                    "allowed_values": [
                        "sqlite_wal",
                        "redis",
                        "valkey",
                    ],
                },
            )

        _validate_non_empty_text(f"{field_name}.key_prefix", self.key_prefix)

        if self.backend == "sqlite_wal":
            _validate_non_empty_text(f"{field_name}.sqlite_path", self.sqlite_path)

        if self.backend == "redis":
            _validate_url(
                f"{field_name}.redis_url",
                self.redis_url,
                allowed_schemes={
                    "redis",
                    "rediss",
                },
                required=True,
            )

        if self.backend == "valkey":
            _validate_url(
                f"{field_name}.redis_url",
                self.redis_url,
                allowed_schemes={
                    "redis",
                    "rediss",
                    "valkey",
                    "valkeys",
                },
                required=True,
            )


@dataclass(slots=True, kw_only=True)
class NsRuntimeAuditStoreConfig:
    backend: RuntimeAuditStoreBackend = "sqlite_wal"
    sqlite_path: str = "data/ns_runtime_audit.sqlite3"
    database: dict[str, Any] = field(default_factory=dict)
    api_url: str = ""
    key_prefix: str = "ns_runtime_audit"

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeAuditStoreConfig":
        data = _ensure_object(value, "runtime.audit_store")
        _reject_unknown_keys(
            data,
            field_name="runtime.audit_store",
            allowed_keys={
                "backend",
                "sqlite_path",
                "database",
                "api_url",
                "key_prefix",
            },
        )
        config = cls(
            backend=data.get("backend", "sqlite_wal"),
            sqlite_path=str(data.get("sqlite_path", "data/ns_runtime_audit.sqlite3")),
            database=dict(data.get("database", {})),
            api_url=str(data.get("api_url", "")),
            key_prefix=str(data.get("key_prefix", "ns_runtime_audit")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.backend not in {"sqlite_wal", "direct_db", "http_api"}:
            raise NsConfigError(
                "runtime.audit_store.backend is invalid.",
                details={
                    "field": "runtime.audit_store.backend",
                    "value": self.backend,
                    "allowed_values": [
                        "sqlite_wal",
                        "direct_db",
                        "http_api",
                    ],
                },
            )

        _validate_non_empty_text("runtime.audit_store.key_prefix", self.key_prefix)

        if self.backend == "sqlite_wal":
            _validate_non_empty_text("runtime.audit_store.sqlite_path", self.sqlite_path)

        if self.backend == "direct_db" and not self.database:
            raise NsConfigError(
                "runtime.audit_store.database must be configured when backend is direct_db.",
                details={
                    "field": "runtime.audit_store.database",
                    "backend": self.backend,
                },
            )

        if self.backend == "http_api":
            _validate_url(
                "runtime.audit_store.api_url",
                self.api_url,
                allowed_schemes={
                    "http",
                    "https",
                },
                required=True,
            )


@dataclass(slots=True, kw_only=True)
class NsRuntimeRoutingConfig:
    default_strategy: str = "rule_based"
    default_load_balance: str = "weighted_least_loaded"
    max_hops: int = 8
    rules: list[dict[str, Any]] = field(default_factory=list)
    tenant_isolation_enabled: bool = True
    cross_tenant_allow_rules: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeRoutingConfig":
        data = _ensure_object(value, "runtime.routing")
        _reject_unknown_keys(
            data,
            field_name="runtime.routing",
            allowed_keys={
                "default_strategy",
                "default_load_balance",
                "max_hops",
                "rules",
                "tenant_isolation_enabled",
                "cross_tenant_allow_rules",
            },
        )
        config = cls(
            default_strategy=str(data.get("default_strategy", "rule_based")),
            default_load_balance=str(data.get("default_load_balance", "weighted_least_loaded")),
            max_hops=int(data.get("max_hops", 8)),
            rules=list(data.get("rules", [])),
            tenant_isolation_enabled=bool(data.get("tenant_isolation_enabled", True)),
            cross_tenant_allow_rules=list(data.get("cross_tenant_allow_rules", [])),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_non_empty_text("runtime.routing.default_strategy", self.default_strategy)
        _validate_non_empty_text("runtime.routing.default_load_balance", self.default_load_balance)
        _validate_positive_int("runtime.routing.max_hops", self.max_hops)
        _validate_object_list("runtime.routing.rules", self.rules)
        _validate_bool("runtime.routing.tenant_isolation_enabled", self.tenant_isolation_enabled)
        _validate_object_list("runtime.routing.cross_tenant_allow_rules", self.cross_tenant_allow_rules)


@dataclass(slots=True, kw_only=True)
class NsRuntimePluginsConfig:
    import_paths: list[str] = field(default_factory=list)
    scan_dirs: list[str] = field(default_factory=list)
    enable_hot_reload: bool = True

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimePluginsConfig":
        data = _ensure_object(value, "runtime.plugins")
        _reject_unknown_keys(
            data,
            field_name="runtime.plugins",
            allowed_keys={
                "import_paths",
                "scan_dirs",
                "enable_hot_reload",
            },
        )
        config = cls(
            import_paths=list(data.get("import_paths", [])),
            scan_dirs=list(data.get("scan_dirs", [])),
            enable_hot_reload=bool(data.get("enable_hot_reload", True)),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_text_list("runtime.plugins.import_paths", self.import_paths)
        _validate_text_list("runtime.plugins.scan_dirs", self.scan_dirs)
        _validate_bool("runtime.plugins.enable_hot_reload", self.enable_hot_reload)


@dataclass(slots=True, kw_only=True)
class NsRuntimeAdminAccessCheckConfig:
    enabled: bool = True
    template: NsRuntimeAccessCheckTemplateConfig = field(default_factory=NsRuntimeAccessCheckTemplateConfig)

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeAdminAccessCheckConfig":
        data = _ensure_object(value, "runtime.admin.iam_access_check")
        _reject_unknown_keys(
            data,
            field_name="runtime.admin.iam_access_check",
            allowed_keys={
                "enabled",
                "template",
            },
        )
        config = cls(
            enabled=bool(data.get("enabled", True)),
            template=NsRuntimeAccessCheckTemplateConfig.from_mapping(
                data.get("template"),
                field_name="runtime.admin.iam_access_check.template",
                default_resource_type="ns_runtime_admin",
                default_resource_id="{{ runtime_id }}",
                default_action_code="{{ action }}",
                default_context={
                    "runtime_id": "{{ runtime_id }}",
                    "cluster_id": "{{ cluster_id }}",
                    "mode": "{{ mode }}",
                    "admin_action": "{{ action }}",
                    "client_ip": "{{ client_ip }}",
                    "request_id": "{{ request_id }}",
                },
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_bool("runtime.admin.iam_access_check.enabled", self.enabled)
        self.template.validate("runtime.admin.iam_access_check.template")


@dataclass(slots=True, kw_only=True)
class NsRuntimeAdminConfig:
    path: str = "/admin/action"
    iam_access_check: NsRuntimeAdminAccessCheckConfig = field(default_factory=NsRuntimeAdminAccessCheckConfig)

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeAdminConfig":
        data = _ensure_object(value, "runtime.admin")
        _reject_unknown_keys(
            data,
            field_name="runtime.admin",
            allowed_keys={
                "path",
                "iam_access_check",
            },
        )
        config = cls(
            path=str(data.get("path", "/admin/action")),
            iam_access_check=NsRuntimeAdminAccessCheckConfig.from_mapping(data.get("iam_access_check")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_path("runtime.admin.path", self.path)
        self.iam_access_check.validate()


@dataclass(slots=True, kw_only=True)
class NsRuntimeConfig:
    enabled: bool = False
    runtime_id: str = "runtime-01"
    cluster_id: str = "default"
    mode: RuntimeMode = "singleton"

    server: NsRuntimeServerConfig = field(default_factory=NsRuntimeServerConfig)
    iam: NsRuntimeIamConfig = field(default_factory=NsRuntimeIamConfig)
    cluster: NsRuntimeClusterConfig = field(default_factory=NsRuntimeClusterConfig)

    state_store: NsRuntimeStoreConfig = field(
        default_factory=lambda: NsRuntimeStoreConfig(
            backend="sqlite_wal",
            sqlite_path="data/ns_runtime_state.sqlite3",
            redis_url="",
            key_prefix="ns_runtime_state",
        )
    )
    message_store: NsRuntimeStoreConfig = field(
        default_factory=lambda: NsRuntimeStoreConfig(
            backend="sqlite_wal",
            sqlite_path="data/ns_runtime_message.sqlite3",
            redis_url="",
            key_prefix="ns_runtime_message",
        )
    )
    audit_store: NsRuntimeAuditStoreConfig = field(default_factory=NsRuntimeAuditStoreConfig)

    routing: NsRuntimeRoutingConfig = field(default_factory=NsRuntimeRoutingConfig)
    plugins: NsRuntimePluginsConfig = field(default_factory=NsRuntimePluginsConfig)
    admin: NsRuntimeAdminConfig = field(default_factory=NsRuntimeAdminConfig)

    global_max_concurrency: int = 1000
    default_processor_max_concurrency: int = 100
    default_processor_timeout_ms: int = 30_000
    default_connection_max_inflight: int = 32
    default_backpressure_policy: RuntimeBackpressurePolicy = "timeout_queue"

    @classmethod
    def from_mapping(cls, value: Any) -> "NsRuntimeConfig":
        data = _ensure_object(value, "runtime")

        if "default_handler_max_concurrency" in data:
            raise NsConfigError(
                "runtime.default_handler_max_concurrency is deprecated. Use runtime.default_processor_max_concurrency.",
                details={
                    "field": "runtime.default_handler_max_concurrency",
                    "expected_field": "runtime.default_processor_max_concurrency",
                },
            )

        _reject_unknown_keys(
            data,
            field_name="runtime",
            allowed_keys={
                "enabled",
                "runtime_id",
                "cluster_id",
                "mode",
                "server",
                "iam",
                "cluster",
                "state_store",
                "message_store",
                "audit_store",
                "routing",
                "plugins",
                "admin",
                "global_max_concurrency",
                "default_processor_max_concurrency",
                "default_processor_timeout_ms",
                "default_connection_max_inflight",
                "default_backpressure_policy",
            },
        )

        config = cls(
            enabled=bool(data.get("enabled", False)),
            runtime_id=str(data.get("runtime_id", "runtime-01")),
            cluster_id=str(data.get("cluster_id", "default")),
            mode=data.get("mode", "singleton"),
            server=NsRuntimeServerConfig.from_mapping(data.get("server")),
            iam=NsRuntimeIamConfig.from_mapping(data.get("iam")),
            cluster=NsRuntimeClusterConfig.from_mapping(data.get("cluster")),
            state_store=NsRuntimeStoreConfig.from_mapping(
                data.get("state_store"),
                field_name="runtime.state_store",
                default_sqlite_path="data/ns_runtime_state.sqlite3",
                default_key_prefix="ns_runtime_state",
            ),
            message_store=NsRuntimeStoreConfig.from_mapping(
                data.get("message_store"),
                field_name="runtime.message_store",
                default_sqlite_path="data/ns_runtime_message.sqlite3",
                default_key_prefix="ns_runtime_message",
            ),
            audit_store=NsRuntimeAuditStoreConfig.from_mapping(data.get("audit_store")),
            routing=NsRuntimeRoutingConfig.from_mapping(data.get("routing")),
            plugins=NsRuntimePluginsConfig.from_mapping(data.get("plugins")),
            admin=NsRuntimeAdminConfig.from_mapping(data.get("admin")),
            global_max_concurrency=int(data.get("global_max_concurrency", 1000)),
            default_processor_max_concurrency=int(data.get("default_processor_max_concurrency", 100)),
            default_processor_timeout_ms=int(data.get("default_processor_timeout_ms", 30_000)),
            default_connection_max_inflight=int(data.get("default_connection_max_inflight", 32)),
            default_backpressure_policy=data.get("default_backpressure_policy", "timeout_queue"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_bool("runtime.enabled", self.enabled)
        _validate_non_empty_text("runtime.runtime_id", self.runtime_id)
        _validate_non_empty_text("runtime.cluster_id", self.cluster_id)

        if self.mode not in {"master", "sub_node", "singleton"}:
            raise NsConfigError(
                "runtime.mode is invalid.",
                details={
                    "field": "runtime.mode",
                    "value": self.mode,
                    "allowed_values": [
                        "master",
                        "sub_node",
                        "singleton",
                    ],
                },
            )

        self.server.validate()
        self.iam.validate()
        self.cluster.validate()
        self.state_store.validate("runtime.state_store")
        self.message_store.validate("runtime.message_store")
        self.audit_store.validate()
        self.routing.validate()
        self.plugins.validate()
        self.admin.validate()

        _validate_positive_int("runtime.global_max_concurrency", self.global_max_concurrency)
        _validate_positive_int("runtime.default_processor_max_concurrency", self.default_processor_max_concurrency)
        _validate_positive_int("runtime.default_processor_timeout_ms", self.default_processor_timeout_ms)
        _validate_positive_int("runtime.default_connection_max_inflight", self.default_connection_max_inflight)
        
        if self.default_processor_max_concurrency > self.global_max_concurrency:
            raise NsConfigError(
                "runtime.default_processor_max_concurrency must be less than or equal to runtime.global_max_concurrency.",
                details={
                    "field": "runtime.default_processor_max_concurrency",
                    "default_processor_max_concurrency": self.default_processor_max_concurrency,
                    "global_max_concurrency": self.global_max_concurrency,
                },
            )

        if self.default_backpressure_policy not in {"reject", "queue", "timeout_queue"}:
            raise NsConfigError(
                "runtime.default_backpressure_policy is invalid.",
                details={
                    "field": "runtime.default_backpressure_policy",
                    "value": self.default_backpressure_policy,
                    "allowed_values": [
                        "reject",
                        "queue",
                        "timeout_queue",
                    ],
                },
            )
