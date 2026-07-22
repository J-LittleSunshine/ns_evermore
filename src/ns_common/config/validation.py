# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import re
from collections.abc import Mapping as MappingABC
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from ..exceptions import NsConfigError, NsDependencyError
from .defaults import _ALLOWED_ENVIRONMENTS, get_ns_env
from .groups.cache import NsCacheConfig
from .groups.runtime import RUNTIME_CONFIG_GROUP_NAMES, NsRuntimeConfig
from .metadata import (
    _CONFIG_VERSION_PATTERN,
    RUNTIME_CONFIG_APPLY_MODES,
    NsConfigGroupMetadata,
)
from .primitives import _validate_dataclass_types


def config_groups(config: Any) -> tuple[tuple[str, Any], ...]:
    return (
        ("backend", config.backend),
        ("cache", config.cache),
        ("log", config.log),
        ("runtime", config.runtime),
    )


def runtime_config_groups(runtime: NsRuntimeConfig) -> tuple[tuple[str, Any], ...]:
    return tuple(
        (group_name, getattr(runtime, group_name))
        for group_name in RUNTIME_CONFIG_GROUP_NAMES
    )


def normalize_effective_at(
    value: datetime | str | None,
    *,
    field_name: str,
    allow_none: bool,
) -> str | None:
    if value is None:
        if allow_none:
            return None

        raise NsConfigError(
            f"{field_name} is required.",
            details={
                "field": field_name,
            },
        )

    parsed: datetime
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"

        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as error:
            raise NsConfigError(
                f"{field_name} must be an ISO-8601 timestamp.",
                details={
                    "field": field_name,
                    "value": value,
                },
            ) from error
    else:
        raise NsConfigError(
            f"{field_name} must be an ISO-8601 timestamp.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise NsConfigError(
            f"{field_name} must include a timezone.",
            details={
                "field": field_name,
                "value": value,
            },
        )

    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_group_metadata(group_name: str, metadata: NsConfigGroupMetadata) -> None:
    for field_name in (
        "config_version",
        "policy_version",
        "group_version",
    ):
        value = getattr(metadata, field_name)
        if _CONFIG_VERSION_PATTERN.fullmatch(value) is None:
            raise NsConfigError(
                f"{group_name}.metadata.{field_name} is invalid.",
                details={
                    "field": f"{group_name}.metadata.{field_name}",
                    "value": value,
                    "allowed_pattern": _CONFIG_VERSION_PATTERN.pattern,
                },
            )
    if (
        metadata.rollback_from_version is not None
        and _CONFIG_VERSION_PATTERN.fullmatch(metadata.rollback_from_version) is None
    ):
        raise NsConfigError(
            f"{group_name}.metadata.rollback_from_version is invalid.",
            details={
                "field": f"{group_name}.metadata.rollback_from_version",
                "value": metadata.rollback_from_version,
                "allowed_pattern": _CONFIG_VERSION_PATTERN.pattern,
            },
        )

    if metadata.effective_at is not None:
        normalize_effective_at(
            metadata.effective_at,
            field_name=f"{group_name}.metadata.effective_at",
            allow_none=False,
        )


def get_consistent_metadata_value(config: Any, field_name: str) -> str:
    values = {
        getattr(group_config.metadata, field_name)
        for _, group_config in config_groups(config)
    }
    if len(values) != 1:
        raise NsConfigError(
            f"config metadata {field_name} is inconsistent across groups.",
            details={
                "field": f"metadata.{field_name}",
                "values": sorted(values),
            },
        )

    return next(iter(values))


def resolve_environment(environment: str | None) -> str:
    if environment is None:
        return get_ns_env()

    if not isinstance(environment, str):
        raise NsConfigError(
            "environment must be a string.",
            details={
                "field": "environment",
                "actual_type": type(environment).__name__,
            },
        )

    normalized = environment.strip().lower()
    if normalized not in _ALLOWED_ENVIRONMENTS:
        raise NsConfigError(
            "environment is invalid.",
            details={
                "field": "environment",
                "value": environment,
                "allowed_values": sorted(_ALLOWED_ENVIRONMENTS),
            },
        )

    return normalized


def validate_config(config: Any, *, environment: str | None = None) -> None:
    _ConfigValidator(config).validate(environment=environment)


class _ConfigValidator:
    def __init__(self, config: Any) -> None:
        self._config = config

    def validate(self, *, environment: str | None = None) -> None:
        resolved_environment = resolve_environment(environment)
        _validate_dataclass_types(self._config)
        backend = self._config.backend

        if backend.debug and resolved_environment == "prod":
            raise NsConfigError(
                "backend.debug must be False when NS_ENV is prod.",
                details={
                    "field": "backend.debug",
                    "env": resolved_environment,
                },
            )

        if not backend.secret_key.strip():
            raise NsConfigError(
                "backend.secret_key must not be empty.",
                details={
                    "field": "backend.secret_key",
                },
            )

        if resolved_environment == "prod" and backend.secret_key.startswith("change-me-"):
            raise NsConfigError(
                "backend.secret_key must be changed in prod.",
                details={
                    "field": "backend.secret_key",
                    "env": resolved_environment,
                },
            )

        if not isinstance(backend.allowed_hosts, tuple):
            raise NsConfigError(
                "backend.allowed_hosts must be a sequence.",
                details={
                    "field": "backend.allowed_hosts",
                    "actual_type": type(backend.allowed_hosts).__name__,
                },
            )

        if not isinstance(backend.databases, MappingABC):
            raise NsConfigError(
                "backend.databases must be a mapping.",
                details={
                    "field": "backend.databases",
                    "actual_type": type(backend.databases).__name__,
                },
            )

        if not isinstance(backend.database_router_map, MappingABC):
            raise NsConfigError(
                "backend.database_router_map must be a mapping.",
                details={
                    "field": "backend.database_router_map",
                    "actual_type": type(backend.database_router_map).__name__,
                },
            )

        for app_label, db_alias in backend.database_router_map.items():
            if not isinstance(app_label, str) or not app_label.strip():
                raise NsConfigError(
                    "backend.database_router_map app label must be a non-empty string.",
                    details={
                        "field": "backend.database_router_map",
                        "app_label": app_label,
                    },
                )

            if not isinstance(db_alias, str) or not db_alias.strip():
                raise NsConfigError(
                    "backend.database_router_map database alias must be a non-empty string.",
                    details={
                        "field": "backend.database_router_map",
                        "app_label": app_label,
                        "db_alias": db_alias,
                    },
                )

        self._validate_positive_int("backend.access_token_expire_minutes", backend.access_token_expire_minutes)
        self._validate_positive_int("backend.refresh_token_expire_days", backend.refresh_token_expire_days)
        self._validate_positive_int("backend.jwt_leeway_seconds", backend.jwt_leeway_seconds)
        self._validate_positive_int("backend.jwt_min_secret_length", backend.jwt_min_secret_length)
        self._validate_positive_int(
            "backend.password_transport_max_payload_length",
            backend.password_transport_max_payload_length,
        )
        self._validate_positive_int(
            "backend.password_plaintext_max_length",
            backend.password_plaintext_max_length,
        )
        self._validate_bool("backend.iam_auth_backoff_enabled", backend.iam_auth_backoff_enabled)
        self._validate_non_negative_int(
            "backend.iam_auth_backoff_max_retries",
            backend.iam_auth_backoff_max_retries,
        )
        self._validate_non_negative_int(
            "backend.iam_auth_backoff_base_delay_ms",
            backend.iam_auth_backoff_base_delay_ms,
        )
        self._validate_non_negative_int(
            "backend.iam_auth_backoff_max_delay_ms",
            backend.iam_auth_backoff_max_delay_ms,
        )
        self._validate_float_range(
            "backend.iam_auth_backoff_jitter_ratio",
            backend.iam_auth_backoff_jitter_ratio,
            min_value=0.0,
            max_value=1.0,
        )

        self._validate_bool("backend.iam_cache_enabled", backend.iam_cache_enabled)
        self._validate_positive_int("backend.iam_cache_ttl_seconds", backend.iam_cache_ttl_seconds)
        self._validate_positive_int("backend.iam_user_cache_ttl_seconds", backend.iam_user_cache_ttl_seconds)
        self._validate_positive_int("backend.iam_authz_cache_ttl_seconds", backend.iam_authz_cache_ttl_seconds)

        if backend.password_transport_mode not in {"plain", "rsa_oaep"}:
            raise NsConfigError(
                "backend.password_transport_mode is invalid.",
                details={
                    "field": "backend.password_transport_mode",
                    "value": backend.password_transport_mode,
                    "allowed_values": [
                        "plain",
                        "rsa_oaep",
                    ],
                },
            )

        if not isinstance(backend.installed_apps, tuple):
            raise NsConfigError(
                "backend.installed_apps must be a sequence.",
                details={
                    "field": "backend.installed_apps",
                    "actual_type": type(backend.installed_apps).__name__,
                },
            )

        seen_installed_apps: set[str] = set()

        for app_key in backend.installed_apps:
            if not isinstance(app_key, str) or not app_key.strip():
                raise NsConfigError(
                    "backend.installed_apps item must be a non-empty string.",
                    details={
                        "field": "backend.installed_apps",
                        "value": app_key,
                    },
                )

            normalized_app_key = app_key.strip()

            if normalized_app_key in seen_installed_apps:
                raise NsConfigError(
                    "backend.installed_apps contains duplicated item.",
                    details={
                        "field": "backend.installed_apps",
                        "value": normalized_app_key,
                    },
                )

            seen_installed_apps.add(normalized_app_key)

        for group_name, group_config in config_groups(self._config):
            validate_group_metadata(group_name, group_config.metadata)

        for group_name, group_config in runtime_config_groups(self._config.runtime):
            validate_group_metadata(f"runtime.{group_name}", group_config.metadata)

        self._validate_cache_config()
        self._validate_runtime_config(resolved_environment)

    def _validate_cache_config(self) -> None:
        cache = self._config.cache

        if not isinstance(cache, NsCacheConfig):
            raise NsConfigError(
                "cache must be NsCacheConfig.",
                details={
                    "field": "cache",
                    "actual_type": type(cache).__name__,
                },
            )

        if cache.backend not in {
            "sqlite",
            "redis",
            "valkey",
            "dummy",
        }:
            raise NsConfigError(
                "cache.backend is invalid.",
                details={
                    "field": "cache.backend",
                    "value": cache.backend,
                    "allowed_values": [
                        "sqlite",
                        "redis",
                        "valkey",
                        "dummy",
                    ],
                },
            )

        self._validate_cache_key_part("cache.key_prefix", cache.key_prefix)
        self._validate_cache_key_part("cache.django_namespace", cache.django_namespace)

        self._validate_positive_int("cache.default_ttl_seconds", cache.default_ttl_seconds)
        self._validate_bool("cache.none_ttl_means_forever", cache.none_ttl_means_forever)
        self._validate_positive_int("cache.sqlite_busy_timeout_ms", cache.sqlite_busy_timeout_ms)
        self._validate_non_negative_int("cache.sqlite_write_max_retries", cache.sqlite_write_max_retries)
        self._validate_non_negative_int(
            "cache.sqlite_write_retry_base_delay_ms",
            cache.sqlite_write_retry_base_delay_ms,
        )
        self._validate_non_negative_int(
            "cache.sqlite_write_retry_max_delay_ms",
            cache.sqlite_write_retry_max_delay_ms,
        )
        self._validate_positive_int("cache.cleanup_interval_seconds", cache.cleanup_interval_seconds)
        self._validate_positive_int("cache.cleanup_batch_size", cache.cleanup_batch_size)

        if cache.backend == "redis":
            self._validate_cache_url(
                field_name="cache.cache_url",
                cache_url=cache.cache_url,
                allowed_schemes={
                    "redis",
                    "rediss",
                },
            )
            self._validate_python_dependency(
                field_name="cache.backend",
                package_name="redis",
            )

        if cache.backend == "valkey":
            self._validate_cache_url(
                field_name="cache.cache_url",
                cache_url=cache.cache_url,
                allowed_schemes={
                    "redis",
                    "rediss",
                    "valkey",
                    "valkeys",
                },
            )
            self._validate_python_dependency(
                field_name="cache.backend",
                package_name="valkey",
            )

    def _validate_runtime_config(self, environment: str) -> None:
        runtime = self._config.runtime

        for group_name, group_config in runtime_config_groups(runtime):
            expected_apply_mode = RUNTIME_CONFIG_APPLY_MODES[group_name]
            if group_config.metadata.apply_mode != expected_apply_mode:
                raise NsConfigError(
                    f"runtime.{group_name}.metadata.apply_mode is invalid for this group.",
                    details={
                        "field": f"runtime.{group_name}.metadata.apply_mode",
                        "value": group_config.metadata.apply_mode,
                        "expected": expected_apply_mode,
                    },
                )

            for version_field in ("config_version", "policy_version"):
                value = getattr(group_config.metadata, version_field)
                expected = getattr(runtime.metadata, version_field)
                if value != expected:
                    raise NsConfigError(
                        f"runtime.{group_name}.metadata.{version_field} is inconsistent with runtime metadata.",
                        details={
                            "field": f"runtime.{group_name}.metadata.{version_field}",
                            "value": value,
                            "expected": expected,
                        },
                    )

        event_loop = runtime.event_loop
        if event_loop.implementation not in {"auto", "asyncio", "uvloop"}:
            self._raise_invalid_choice(
                "runtime.event_loop.implementation",
                event_loop.implementation,
                {"auto", "asyncio", "uvloop"},
            )
        self._validate_positive_int(
            "runtime.event_loop.slow_callback_threshold_ms",
            event_loop.slow_callback_threshold_ms,
        )

        transport = runtime.transport
        adapter_names = {name for name, _ in transport.adapters()}
        enabled_adapters = set(transport.enabled_adapters)
        if not enabled_adapters:
            raise NsConfigError(
                "runtime.transport must enable at least one adapter.",
                details={"field": "runtime.transport"},
            )

        for adapter_name, adapter in transport.adapters():
            for origin in adapter.allowed_origins:
                self._validate_non_empty_string(
                    f"runtime.transport.{adapter_name}.allowed_origins",
                    origin,
                )

            if environment == "prod" and adapter.enabled and not adapter.tls_enabled:
                raise NsConfigError(
                    "enabled production transports must use encrypted transport.",
                    details={
                        "field": f"runtime.transport.{adapter_name}.tls_enabled",
                        "env": environment,
                    },
                )

        for field_name, adapter_name in (
            ("default_adapter", transport.default_adapter),
            ("preferred_adapter", transport.preferred_adapter),
        ):
            if adapter_name not in enabled_adapters:
                raise NsConfigError(
                    f"runtime.transport.{field_name} must reference an enabled adapter.",
                    details={
                        "field": f"runtime.transport.{field_name}",
                        "value": adapter_name,
                        "enabled_adapters": sorted(enabled_adapters),
                    },
                )

        self._validate_unique_choices(
            "runtime.transport.fallback_order",
            transport.fallback_order,
            adapter_names,
        )
        disabled_fallbacks = sorted(set(transport.fallback_order).difference(enabled_adapters))
        if disabled_fallbacks:
            raise NsConfigError(
                "runtime.transport.fallback_order contains disabled adapters.",
                details={
                    "field": "runtime.transport.fallback_order",
                    "disabled_adapters": disabled_fallbacks,
                },
            )

        self._validate_non_empty_string("runtime.transport.listen_host", transport.listen_host)
        self._validate_port("runtime.transport.listen_port", transport.listen_port)
        self._validate_positive_int("runtime.transport.write_queue_capacity", transport.write_queue_capacity)
        self._validate_non_negative_int(
            "runtime.transport.write_queue_low_watermark",
            transport.write_queue_low_watermark,
        )
        self._validate_positive_int(
            "runtime.transport.write_queue_high_watermark",
            transport.write_queue_high_watermark,
        )
        if not (
            transport.write_queue_low_watermark
            < transport.write_queue_high_watermark
            <= transport.write_queue_capacity
        ):
            raise NsConfigError(
                "runtime.transport queue watermarks are invalid.",
                details={
                    "field": "runtime.transport.write_queue_low_watermark",
                    "low": transport.write_queue_low_watermark,
                    "high": transport.write_queue_high_watermark,
                    "capacity": transport.write_queue_capacity,
                },
            )

        self._validate_unique_non_empty_strings(
            "runtime.transport.message_type_allowlist",
            transport.message_type_allowlist,
            allow_empty=True,
        )
        migration_capable = {"websocket_http3", "webtransport_http3", "quic_native"}
        datagram_capable = {"webtransport_http3", "quic_native"}
        if transport.path_migration_enabled and not enabled_adapters.intersection(migration_capable):
            raise NsConfigError(
                "path migration requires an enabled HTTP/3, WebTransport, or QUIC adapter.",
                details={"field": "runtime.transport.path_migration_enabled"},
            )
        if transport.datagram_enabled and not enabled_adapters.intersection(datagram_capable):
            raise NsConfigError(
                "datagrams require an enabled WebTransport or native QUIC adapter.",
                details={"field": "runtime.transport.datagram_enabled"},
            )
        if transport.zero_rtt_enabled:
            if not enabled_adapters.intersection(migration_capable):
                raise NsConfigError(
                    "0-RTT requires an enabled HTTP/3, WebTransport, or QUIC adapter.",
                    details={"field": "runtime.transport.zero_rtt_enabled"},
                )
            if not runtime.security.allow_zero_rtt:
                raise NsConfigError(
                    "0-RTT must also be allowed by runtime.security.",
                    details={
                        "field": "runtime.security.allow_zero_rtt",
                        "required_by": "runtime.transport.zero_rtt_enabled",
                    },
                )

        wire_codec = runtime.wire_codec
        if wire_codec.supported != ("json.v1",) or wire_codec.preferred != "json.v1":
            raise NsConfigError(
                "runtime.wire_codec currently supports only json.v1.",
                details={
                    "field": "runtime.wire_codec",
                    "supported": list(wire_codec.supported),
                    "preferred": wire_codec.preferred,
                },
            )

        protocol = runtime.protocol
        self._validate_unique_non_empty_strings(
            "runtime.protocol.supported_versions",
            protocol.supported_versions,
        )
        if protocol.preferred_version not in protocol.supported_versions:
            raise NsConfigError(
                "runtime.protocol.preferred_version must be supported.",
                details={
                    "field": "runtime.protocol.preferred_version",
                    "value": protocol.preferred_version,
                    "supported_versions": list(protocol.supported_versions),
                },
            )
        self._validate_positive_int("runtime.protocol.handshake_timeout_seconds", protocol.handshake_timeout_seconds)
        self._validate_positive_int("runtime.protocol.max_envelope_bytes", protocol.max_envelope_bytes)

        security = runtime.security
        if not security.require_tls_in_prod:
            raise NsConfigError(
                "runtime.security.require_tls_in_prod cannot be disabled.",
                details={"field": "runtime.security.require_tls_in_prod"},
            )
        if not security.reject_inbound_source or not security.reject_inbound_auth_context:
            raise NsConfigError(
                "runtime must reject inbound source and auth_context.",
                details={"field": "runtime.security"},
            )
        if environment != "prod" and not security.allow_plaintext_non_prod:
            plaintext_adapters = [
                name
                for name, adapter in transport.adapters()
                if adapter.enabled and not adapter.tls_enabled
            ]
            if plaintext_adapters:
                raise NsConfigError(
                    "plaintext transport is disabled by runtime.security.",
                    details={
                        "field": "runtime.security.allow_plaintext_non_prod",
                        "plaintext_adapters": plaintext_adapters,
                    },
                )

        iam = runtime.iam
        self._validate_http_url("runtime.iam.base_url", iam.base_url)
        self._validate_positive_int("runtime.iam.request_timeout_seconds", iam.request_timeout_seconds)
        self._validate_positive_int(
            "runtime.iam.credential_refresh_interval_seconds",
            iam.credential_refresh_interval_seconds,
        )
        self._validate_positive_int(
            "runtime.iam.permission_snapshot_ttl_seconds",
            iam.permission_snapshot_ttl_seconds,
        )
        if iam.authorization_mode not in {"strict", "cache"}:
            self._raise_invalid_choice(
                "runtime.iam.authorization_mode",
                iam.authorization_mode,
                {"strict", "cache"},
            )
        self._validate_non_empty_string(
            "runtime.iam.internal_service_credential",
            iam.internal_service_credential,
        )
        if len(iam.internal_service_credential) < 32:
            raise NsConfigError(
                "runtime IAM internal service credential is too short.",
                details={
                    "field": "runtime.iam.internal_service_credential",
                    "minimum_length": 32,
                },
            )
        self._validate_non_empty_string(
            "backend.iam_internal_token",
            self._config.backend.iam_internal_token,
        )
        if len(self._config.backend.iam_internal_token) < 32:
            raise NsConfigError(
                "backend IAM internal token is too short.",
                details={
                    "field": "backend.iam_internal_token",
                    "minimum_length": 32,
                },
            )
        if environment == "prod":
            if urlparse(iam.base_url.strip()).scheme != "https":
                raise NsConfigError(
                    "runtime IAM must use HTTPS in prod.",
                    details={
                        "field": "runtime.iam.base_url",
                        "env": environment,
                    },
                )
            for field_name, secret in (
                (
                    "runtime.iam.internal_service_credential",
                    iam.internal_service_credential,
                ),
                (
                    "backend.iam_internal_token",
                    self._config.backend.iam_internal_token,
                ),
            ):
                if secret.startswith("change-me-"):
                    raise NsConfigError(
                        "IAM internal credentials must be changed in prod.",
                        details={"field": field_name, "env": environment},
                    )
            if not iam.fail_closed:
                raise NsConfigError(
                    "runtime IAM fail-closed mode is required in prod.",
                    details={"field": "runtime.iam.fail_closed", "env": environment},
                )

        state_store = runtime.state_store
        if environment == "prod" and state_store.backend not in {"redis", "valkey"}:
            raise NsConfigError(
                "runtime.state_store.backend must be redis or valkey in prod.",
                details={
                    "field": "runtime.state_store.backend",
                    "value": state_store.backend,
                    "env": environment,
                },
            )
        self._validate_cache_key_part("runtime.state_store.namespace", state_store.namespace)
        self._validate_positive_int(
            "runtime.state_store.operation_timeout_seconds",
            state_store.operation_timeout_seconds,
        )
        if state_store.backend == "sqlite":
            self._validate_non_empty_string("runtime.state_store.sqlite_path", state_store.sqlite_path)
        else:
            if state_store.endpoint and state_store.url:
                raise NsConfigError(
                    "runtime.state_store endpoint aliases cannot be combined.",
                    details={"field": "runtime.state_store.endpoint"},
                )
            endpoint = state_store.resolved_endpoint
            allowed_schemes = (
                {"redis", "rediss"}
                if state_store.backend == "redis"
                else {"redis", "rediss", "valkey", "valkeys"}
            )
            self._validate_state_store_endpoint(
                "runtime.state_store.endpoint", endpoint, allowed_schemes,
            )
            if not isinstance(state_store.username, str):
                raise NsConfigError(
                    "runtime.state_store.username must be a string.",
                    details={"field": "runtime.state_store.username"},
                )
            self._validate_state_store_password_source(
                state_store.password_source,
                environment=environment,
            )

        routing = runtime.routing
        self._validate_positive_int("runtime.routing.max_hops", routing.max_hops)
        self._validate_non_negative_int("runtime.routing.route_cache_ttl_seconds", routing.route_cache_ttl_seconds)
        self._validate_positive_int(
            "runtime.routing.max_candidate_count",
            routing.max_candidate_count,
        )
        self._validate_positive_int(
            "runtime.routing.max_selected_target_count",
            routing.max_selected_target_count,
        )
        self._validate_positive_int(
            "runtime.routing.max_plan_evidence_count",
            routing.max_plan_evidence_count,
        )

        delivery = runtime.delivery
        self._validate_positive_int("runtime.delivery.ack_timeout_seconds", delivery.ack_timeout_seconds)
        self._validate_non_negative_int("runtime.delivery.max_retry_attempts", delivery.max_retry_attempts)
        self._validate_non_negative_int("runtime.delivery.retry_base_delay_ms", delivery.retry_base_delay_ms)
        self._validate_non_negative_int("runtime.delivery.retry_max_delay_ms", delivery.retry_max_delay_ms)
        if delivery.retry_max_delay_ms < delivery.retry_base_delay_ms:
            raise NsConfigError(
                "runtime.delivery.retry_max_delay_ms must not be lower than retry_base_delay_ms.",
                details={"field": "runtime.delivery.retry_max_delay_ms"},
            )
        if not delivery.persist_delivery_records:
            raise NsConfigError(
                "runtime.delivery.persist_delivery_records cannot be disabled.",
                details={"field": "runtime.delivery.persist_delivery_records"},
            )

        worker = runtime.worker
        self._validate_positive_int("runtime.worker.concurrency", worker.concurrency)
        self._validate_positive_int("runtime.worker.shutdown_timeout_seconds", worker.shutdown_timeout_seconds)
        self._validate_positive_int("runtime.worker.processor_timeout_seconds", worker.processor_timeout_seconds)

        pool = runtime.pool
        for field_name in (
            "control_capacity",
            "delivery_capacity",
            "stream_capacity",
            "observability_capacity",
        ):
            self._validate_positive_int(f"runtime.pool.{field_name}", getattr(pool, field_name))

        tenant_quota = runtime.tenant_quota
        for field_name in (
            "max_connections",
            "max_queued_deliveries",
            "max_inflight_deliveries",
            "messages_per_second",
        ):
            self._validate_positive_int(
                f"runtime.tenant_quota.{field_name}",
                getattr(tenant_quota, field_name),
            )

        cluster = runtime.cluster
        self._validate_cache_key_part("runtime.cluster.node_id", cluster.node_id)
        self._validate_positive_int(
            "runtime.cluster.heartbeat_interval_seconds",
            cluster.heartbeat_interval_seconds,
        )
        self._validate_positive_int("runtime.cluster.leader_lease_seconds", cluster.leader_lease_seconds)
        if cluster.leader_lease_seconds <= cluster.heartbeat_interval_seconds:
            raise NsConfigError(
                "runtime.cluster.leader_lease_seconds must exceed heartbeat_interval_seconds.",
                details={"field": "runtime.cluster.leader_lease_seconds"},
            )
        if cluster.role == "sub_node":
            self._validate_http_url("runtime.cluster.active_master_url", cluster.active_master_url)

        recovery = runtime.recovery
        self._validate_positive_int("runtime.recovery.scan_interval_seconds", recovery.scan_interval_seconds)
        self._validate_positive_int("runtime.recovery.scan_batch_size", recovery.scan_batch_size)
        self._validate_positive_int("runtime.recovery.stale_after_seconds", recovery.stale_after_seconds)

        observability = runtime.observability
        self._validate_float_range(
            "runtime.observability.trace_sample_ratio",
            observability.trace_sample_ratio,
            min_value=0.0,
            max_value=1.0,
        )
        self._validate_positive_int(
            "runtime.observability.export_interval_seconds",
            observability.export_interval_seconds,
        )

        logging_config = runtime.logging
        normalized_level = logging_config.level.strip().upper()
        if normalized_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            self._raise_invalid_choice(
                "runtime.logging.level",
                logging_config.level,
                {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"},
            )

        debug = runtime.debug
        if debug.emit_sanitized_envelope and not debug.enabled:
            raise NsConfigError(
                "runtime.debug.emit_sanitized_envelope requires debug mode.",
                details={"field": "runtime.debug.emit_sanitized_envelope"},
            )
        if debug.fault_injection_enabled and not debug.enabled:
            raise NsConfigError(
                "runtime.debug.fault_injection_enabled requires debug mode.",
                details={"field": "runtime.debug.fault_injection_enabled"},
            )
        if environment == "prod" and debug.enabled:
            raise NsConfigError(
                "runtime.debug.enabled must be false in prod.",
                details={"field": "runtime.debug.enabled", "env": environment},
            )

    @staticmethod
    def _raise_invalid_choice(field_name: str, value: Any, allowed_values: set[str]) -> None:
        raise NsConfigError(
            f"{field_name} is invalid.",
            details={
                "field": field_name,
                "value": value,
                "allowed_values": sorted(allowed_values),
            },
        )

    @staticmethod
    def _validate_non_empty_string(field_name: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise NsConfigError(
                f"{field_name} must be a non-empty string.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @classmethod
    def _validate_unique_non_empty_strings(
        cls,
        field_name: str,
        values: tuple[str, ...],
        *,
        allow_empty: bool = False,
    ) -> None:
        if not values and not allow_empty:
            raise NsConfigError(
                f"{field_name} must not be empty.",
                details={"field": field_name},
            )

        seen: set[str] = set()
        for value in values:
            cls._validate_non_empty_string(field_name, value)
            if value in seen:
                raise NsConfigError(
                    f"{field_name} contains duplicate values.",
                    details={"field": field_name, "value": value},
                )
            seen.add(value)

    @classmethod
    def _validate_unique_choices(
        cls,
        field_name: str,
        values: tuple[str, ...],
        allowed_values: set[str],
    ) -> None:
        cls._validate_unique_non_empty_strings(field_name, values)
        invalid_values = sorted(set(values).difference(allowed_values))
        if invalid_values:
            raise NsConfigError(
                f"{field_name} contains invalid values.",
                details={
                    "field": field_name,
                    "invalid_values": invalid_values,
                    "allowed_values": sorted(allowed_values),
                },
            )

    @staticmethod
    def _validate_port(field_name: str, value: Any) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535:
            raise NsConfigError(
                f"{field_name} must be between 1 and 65535.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @staticmethod
    def _validate_http_url(field_name: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise NsConfigError(
                f"{field_name} must be configured.",
                details={"field": field_name, "value": value},
            )
        parsed = urlparse(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise NsConfigError(
                f"{field_name} must be an HTTP(S) URL with a host.",
                details={"field": field_name, "value": value},
            )

    @staticmethod
    def _validate_cache_key_part(field_name: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise NsConfigError(
                f"{field_name} must be a non-empty string.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

        text = value.strip()
        if re.fullmatch(r"[a-zA-Z0-9_.:-]+", text) is None:
            raise NsConfigError(
                f"{field_name} contains invalid characters.",
                details={
                    "field": field_name,
                    "value": value,
                    "allowed_pattern": r"[a-zA-Z0-9_.:-]+",
                },
            )

    @staticmethod
    def _validate_cache_url(field_name: str, cache_url: Any, allowed_schemes: set[str]) -> None:
        if not isinstance(cache_url, str) or not cache_url.strip():
            raise NsConfigError(
                f"{field_name} must be configured.",
                details={
                    "field": field_name,
                    "value": cache_url,
                    "actual_type": type(cache_url).__name__,
                },
            )

        parsed = urlparse(cache_url.strip())
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
                    "value": cache_url,
                },
            )

    @staticmethod
    def _validate_state_store_endpoint(
        field_name: str,
        endpoint: Any,
        allowed_schemes: set[str],
    ) -> None:
        if not isinstance(endpoint, str) or not endpoint.strip():
            raise NsConfigError(
                "Runtime StateStore endpoint must be configured.",
                details={"field": field_name},
            )
        parsed = urlparse(endpoint.strip())
        if parsed.scheme not in allowed_schemes:
            raise NsConfigError(
                "Runtime StateStore endpoint scheme is invalid.",
                details={
                    "field": field_name,
                    "scheme": parsed.scheme,
                    "allowed_schemes": sorted(allowed_schemes),
                },
            )
        if not parsed.hostname:
            raise NsConfigError(
                "Runtime StateStore endpoint host is required.",
                details={"field": field_name},
            )
        if parsed.username is not None or parsed.password is not None:
            raise NsConfigError(
                "Runtime StateStore credentials must use typed fields and a secret source.",
                details={"field": field_name, "reason": "userinfo_forbidden"},
            )
        if parsed.query or parsed.fragment or parsed.params:
            raise NsConfigError(
                "Runtime StateStore endpoint contains unsupported components.",
                details={"field": field_name},
            )
        path = parsed.path or "/0"
        try:
            database = int(path.removeprefix("/"))
        except ValueError:
            database = -1
        if not path.startswith("/") or database < 0:
            raise NsConfigError(
                "Runtime StateStore endpoint database is invalid.",
                details={"field": field_name},
            )

    @staticmethod
    def _validate_state_store_password_source(
        value: Any,
        *,
        environment: str,
    ) -> None:
        valid = False
        if value == "none":
            valid = True
        elif isinstance(value, str) and value.startswith("env:"):
            name = value[4:]
            valid = re.fullmatch(r"[A-Z_][A-Z0-9_]{0,127}", name) is not None
        elif isinstance(value, str) and value.startswith("file:"):
            path = value[5:]
            valid = bool(path) and Path(path).is_absolute()
        if not valid:
            raise NsConfigError(
                "runtime.state_store.password_source is invalid.",
                details={"field": "runtime.state_store.password_source"},
            )

    @staticmethod
    def _validate_python_dependency(field_name: str, package_name: str) -> None:
        if importlib.util.find_spec(package_name) is None:
            raise NsDependencyError(
                f"Python package '{package_name}' is required.",
                details={
                    "field": field_name,
                    "package": package_name,
                },
            )

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _validate_float_range(
        field_name: str,
        value: Any,
        *,
        min_value: float,
        max_value: float,
    ) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise NsConfigError(
                f"{field_name} must be a number.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

        parsed = float(value)
        if parsed < min_value or parsed > max_value:
            raise NsConfigError(
                f"{field_name} must be between {min_value} and {max_value}.",
                details={
                    "field": field_name,
                    "value": value,
                    "min_value": min_value,
                    "max_value": max_value,
                },
            )
