# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from ns_common.runtime.constants import (
    RUNTIME_BACKEND_MEMORY,
    RUNTIME_BACKEND_MQ,
    RUNTIME_BACKEND_REDIS,
    RUNTIME_BACKEND_SQL_WAL,
    RUNTIME_BACKEND_VALKEY,
    RUNTIME_CONNECTOR_IPC_MEMORY,
    RUNTIME_CONNECTOR_IPC_TCP,
    RUNTIME_CONNECTOR_IPC_UNIX_SOCKET,
    RUNTIME_MASTER_FORWARD_LOCAL_FIRST,
    RUNTIME_MASTER_FORWARD_SUB_FIRST,
    RUNTIME_MASTER_FORWARD_SUB_REQUIRED,
    RUNTIME_NODE_ROLE_MASTER,
    RUNTIME_NODE_ROLE_STANDALONE,
    RUNTIME_NODE_ROLE_SUB,
)
from ns_common.runtime.errors import NsRuntimeConfigurationError

if TYPE_CHECKING:
    pass

RuntimeNodeRole = Literal["standalone", "master", "sub"]
RuntimeOutboxBackend = Literal["sql_wal", "redis", "valkey", "mq"]
RuntimeIngressBackend = Literal["sql_wal", "redis", "valkey", "mq"]
RuntimeBrokerBackend = Literal["memory", "redis", "valkey", "mq"]
RuntimePresenceBackend = Literal["memory", "redis", "valkey", "sql_wal"]
RuntimeIpcMode = Literal["unix_socket", "tcp", "memory"]
RuntimeMasterForwardPolicy = Literal["local_first", "sub_first", "sub_required"]
RuntimeBrokerMessageForwardDispatchPolicy = Literal["disabled", "rejected_only", "no_sub_or_rejected"]
RuntimeAuthProvider = Literal["static", "remote_iam"]

RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED = "disabled"
RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_REJECTED_ONLY = "rejected_only"
RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_NO_SUB_OR_REJECTED = "no_sub_or_rejected"

RUNTIME_BROKER_MESSAGE_FORWARD_POLICIES: tuple[str, ...] = (
    RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED,
    RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_REJECTED_ONLY,
    RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_NO_SUB_OR_REJECTED,
)
IMPLEMENTED_RUNTIME_BROKER_BACKENDS: tuple[str, ...] = (
    RUNTIME_BACKEND_MEMORY,
    RUNTIME_BACKEND_REDIS,
    RUNTIME_BACKEND_VALKEY,
)

IMPLEMENTED_RUNTIME_PRESENCE_BACKENDS: tuple[str, ...] = (
    RUNTIME_BACKEND_MEMORY,
    RUNTIME_BACKEND_REDIS,
    RUNTIME_BACKEND_VALKEY,
)


@dataclass(slots=True, kw_only=True)
class NsRuntimeConfig:
    """Runtime configuration for realtime connections, durable outbox and cluster broker."""

    enabled: bool = False

    node_id: str = "runtime-default"
    node_role: RuntimeNodeRole = RUNTIME_NODE_ROLE_STANDALONE  # type: ignore[assignment]

    master_url: str = "ws://127.0.0.1:8765/_runtime/backend/connect"

    backend_outbox_backend: RuntimeOutboxBackend = RUNTIME_BACKEND_SQL_WAL  # type: ignore[assignment]
    backend_outbox_location: str = "runtime/backend_outbox.sqlite3"

    runtime_ingress_backend: RuntimeIngressBackend = RUNTIME_BACKEND_SQL_WAL  # type: ignore[assignment]
    runtime_ingress_location: str = "runtime/runtime_ingress.sqlite3"

    runtime_broker_backend: RuntimeBrokerBackend = RUNTIME_BACKEND_MEMORY  # type: ignore[assignment]
    runtime_broker_location: str = ""
    runtime_broker_health_publish_enabled: bool = False
    runtime_broker_message_forward_local_handle_enabled: bool = False
    runtime_broker_message_forward_dispatch_enabled: bool = False
    runtime_broker_message_forward_dispatch_policy: RuntimeBrokerMessageForwardDispatchPolicy = RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED  # type: ignore[assignment]

    runtime_presence_backend: RuntimePresenceBackend = RUNTIME_BACKEND_MEMORY  # type: ignore[assignment]
    runtime_presence_location: str = ""
    runtime_presence_record_ttl_seconds: int = 90

    ipc_mode: RuntimeIpcMode = RUNTIME_CONNECTOR_IPC_UNIX_SOCKET  # type: ignore[assignment]
    ipc_socket_path: str = "/run/ns_evermore/backend-runtime-connector.sock"
    ipc_host: str = "127.0.0.1"
    ipc_port: int = 18766

    heartbeat_interval_seconds: int = 15
    health_report_interval_seconds: int = 30

    ack_timeout_seconds: float = 5.0
    retry_base_delay_seconds: float = 1.0
    retry_max_delay_seconds: float = 60.0
    max_attempts: int = 20

    outbox_claim_batch_size: int = 100
    outbox_max_pending_messages: int = 100000
    outbox_max_storage_mb: int = 1024

    master_handle_when_no_sub_node: bool = True
    master_forward_policy: RuntimeMasterForwardPolicy = RUNTIME_MASTER_FORWARD_SUB_FIRST  # type: ignore[assignment]

    auth_enabled: bool = False
    service_token: str = ""

    frontend_auth_enabled: bool = False
    frontend_static_token: str = ""
    allow_anonymous_frontend: bool = True

    iam_internal_service_token: str = ""
    auth_provider: RuntimeAuthProvider = "static"
    iam_internal_base_url: str = "http://127.0.0.1:8000/iam/runtime"
    iam_internal_request_timeout_seconds: float = 3.0

    def resolved_backend_outbox_backend(self) -> RuntimeOutboxBackend:
        """Resolve backend outbox backend."""
        return self.backend_outbox_backend

    def resolved_runtime_ingress_backend(self) -> RuntimeIngressBackend:
        """Resolve runtime ingress backend."""
        return self.runtime_ingress_backend

    def resolved_runtime_broker_backend(self) -> RuntimeBrokerBackend:
        """Resolve runtime broker backend."""
        return self.runtime_broker_backend

    def is_runtime_broker_backend_implemented(self) -> bool:
        """Return whether configured runtime broker backend is implemented."""
        return self.resolved_runtime_broker_backend() in IMPLEMENTED_RUNTIME_BROKER_BACKENDS

    def ensure_runtime_broker_backend_implemented(self) -> None:
        """Ensure configured runtime broker backend is implemented."""
        backend = self.resolved_runtime_broker_backend()
        if backend not in {RUNTIME_BACKEND_MEMORY, RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY, RUNTIME_BACKEND_MQ}:
            raise NsRuntimeConfigurationError(f"runtime runtime_broker_backend is invalid: {backend}")

        if backend not in IMPLEMENTED_RUNTIME_BROKER_BACKENDS:
            raise NsRuntimeConfigurationError(
                f"runtime runtime_broker_backend is not implemented yet: {backend}; "
                f"implemented backends: {', '.join(IMPLEMENTED_RUNTIME_BROKER_BACKENDS)}"
            )

        if backend in {RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY} and not str(self.runtime_broker_location or "").strip():
            raise NsRuntimeConfigurationError("runtime_broker_location is required when runtime_broker_backend is redis or valkey")

    def resolved_runtime_presence_backend(self) -> RuntimePresenceBackend:
        """Resolve runtime presence backend."""
        return self.runtime_presence_backend

    def is_runtime_presence_backend_implemented(self) -> bool:
        """Return whether configured runtime presence backend is implemented."""
        return self.resolved_runtime_presence_backend() in IMPLEMENTED_RUNTIME_PRESENCE_BACKENDS

    def ensure_runtime_presence_backend_implemented(self) -> None:
        """Ensure configured runtime presence backend is implemented."""
        backend = self.resolved_runtime_presence_backend()
        if backend not in {RUNTIME_BACKEND_MEMORY, RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY, RUNTIME_BACKEND_SQL_WAL}:
            raise NsRuntimeConfigurationError(f"runtime runtime_presence_backend is invalid: {backend}")

        if backend not in IMPLEMENTED_RUNTIME_PRESENCE_BACKENDS:
            raise NsRuntimeConfigurationError(
                f"runtime runtime_presence_backend is not implemented yet: {backend}; "
                f"implemented backends: {', '.join(IMPLEMENTED_RUNTIME_PRESENCE_BACKENDS)}"
            )

    def resolved_runtime_broker_message_forward_dispatch_policy(self) -> str:
        """Return effective runtime broker message forward dispatch policy.

        runtime_broker_message_forward_dispatch_enabled is kept as a compatibility
        boolean. If it is true and the explicit policy is disabled, the effective
        policy becomes rejected_only.
        """
        explicit_policy = str(self.runtime_broker_message_forward_dispatch_policy or "").strip().lower()
        if not explicit_policy:
            explicit_policy = RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED

        if explicit_policy == RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED and self.runtime_broker_message_forward_dispatch_enabled:
            return RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_REJECTED_ONLY

        return explicit_policy

    def validate(self) -> None:
        """Validate runtime configuration."""
        if self.node_role not in {RUNTIME_NODE_ROLE_STANDALONE, RUNTIME_NODE_ROLE_MASTER, RUNTIME_NODE_ROLE_SUB}:
            raise NsRuntimeConfigurationError(f"runtime node_role is invalid: {self.node_role}")

        if not str(self.node_id or "").strip():
            raise NsRuntimeConfigurationError("runtime node_id is required")

        if self.backend_outbox_backend not in {RUNTIME_BACKEND_SQL_WAL, RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY, RUNTIME_BACKEND_MQ}:
            raise NsRuntimeConfigurationError(f"runtime backend_outbox_backend is invalid: {self.backend_outbox_backend}")

        if self.runtime_ingress_backend not in {RUNTIME_BACKEND_SQL_WAL, RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY, RUNTIME_BACKEND_MQ}:
            raise NsRuntimeConfigurationError(f"runtime runtime_ingress_backend is invalid: {self.runtime_ingress_backend}")

        if self.runtime_broker_backend not in {RUNTIME_BACKEND_MEMORY, RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY, RUNTIME_BACKEND_MQ}:
            raise NsRuntimeConfigurationError(f"runtime runtime_broker_backend is invalid: {self.runtime_broker_backend}")

        self.ensure_runtime_broker_backend_implemented()

        if not isinstance(self.runtime_broker_health_publish_enabled, bool):
            raise NsRuntimeConfigurationError("runtime runtime_broker_health_publish_enabled must be bool")

        if not isinstance(self.runtime_broker_message_forward_local_handle_enabled, bool):
            raise NsRuntimeConfigurationError("runtime runtime_broker_message_forward_local_handle_enabled must be bool")

        if not isinstance(self.runtime_broker_message_forward_dispatch_enabled, bool):
            raise NsRuntimeConfigurationError("runtime runtime_broker_message_forward_dispatch_enabled must be bool")

        if self.runtime_broker_message_forward_dispatch_policy not in RUNTIME_BROKER_MESSAGE_FORWARD_POLICIES:
            raise NsRuntimeConfigurationError(f"runtime runtime_broker_message_forward_dispatch_policy is invalid: {self.runtime_broker_message_forward_dispatch_policy}")

        if self.runtime_presence_backend not in {RUNTIME_BACKEND_MEMORY, RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY, RUNTIME_BACKEND_SQL_WAL}:
            raise NsRuntimeConfigurationError(f"runtime runtime_presence_backend is invalid: {self.runtime_presence_backend}")

        self.ensure_runtime_presence_backend_implemented()

        if isinstance(self.runtime_presence_record_ttl_seconds, bool) or self.runtime_presence_record_ttl_seconds <= 0:
            raise NsRuntimeConfigurationError("runtime runtime_presence_record_ttl_seconds must be positive")

        if self.ipc_mode not in {RUNTIME_CONNECTOR_IPC_UNIX_SOCKET, RUNTIME_CONNECTOR_IPC_TCP, RUNTIME_CONNECTOR_IPC_MEMORY}:
            raise NsRuntimeConfigurationError(f"runtime ipc_mode is invalid: {self.ipc_mode}")

        if self.ipc_mode == RUNTIME_CONNECTOR_IPC_TCP:
            if not str(self.ipc_host or "").strip():
                raise NsRuntimeConfigurationError("runtime ipc_host is required when ipc_mode is tcp")
            if isinstance(self.ipc_port, bool) or not isinstance(self.ipc_port, int) or self.ipc_port <= 0:
                raise NsRuntimeConfigurationError("runtime ipc_port must be a positive int")

        if self.ipc_mode == RUNTIME_CONNECTOR_IPC_UNIX_SOCKET and not str(self.ipc_socket_path or "").strip():
            raise NsRuntimeConfigurationError("runtime ipc_socket_path is required when ipc_mode is unix_socket")

        if isinstance(self.heartbeat_interval_seconds, bool) or self.heartbeat_interval_seconds <= 0:
            raise NsRuntimeConfigurationError("runtime heartbeat_interval_seconds must be positive")

        if isinstance(self.health_report_interval_seconds, bool) or self.health_report_interval_seconds <= 0:
            raise NsRuntimeConfigurationError("runtime health_report_interval_seconds must be positive")

        if self.ack_timeout_seconds <= 0:
            raise NsRuntimeConfigurationError("runtime ack_timeout_seconds must be positive")

        if self.retry_base_delay_seconds < 0:
            raise NsRuntimeConfigurationError("runtime retry_base_delay_seconds must be non-negative")

        if self.retry_max_delay_seconds <= 0:
            raise NsRuntimeConfigurationError("runtime retry_max_delay_seconds must be positive")

        if self.retry_max_delay_seconds < self.retry_base_delay_seconds:
            raise NsRuntimeConfigurationError("runtime retry_max_delay_seconds cannot be less than retry_base_delay_seconds")

        if isinstance(self.max_attempts, bool) or self.max_attempts <= 0:
            raise NsRuntimeConfigurationError("runtime max_attempts must be positive")

        if isinstance(self.outbox_claim_batch_size, bool) or self.outbox_claim_batch_size <= 0:
            raise NsRuntimeConfigurationError("runtime outbox_claim_batch_size must be positive")

        if isinstance(self.outbox_max_pending_messages, bool) or self.outbox_max_pending_messages <= 0:
            raise NsRuntimeConfigurationError("runtime outbox_max_pending_messages must be positive")

        if isinstance(self.outbox_max_storage_mb, bool) or self.outbox_max_storage_mb <= 0:
            raise NsRuntimeConfigurationError("runtime outbox_max_storage_mb must be positive")

        if self.master_forward_policy not in {
            RUNTIME_MASTER_FORWARD_LOCAL_FIRST,
            RUNTIME_MASTER_FORWARD_SUB_FIRST,
            RUNTIME_MASTER_FORWARD_SUB_REQUIRED,
        }:
            raise NsRuntimeConfigurationError(f"runtime master_forward_policy is invalid: {self.master_forward_policy}")

        if self.auth_provider not in {"static", "remote_iam"}:
            raise NsRuntimeConfigurationError(f"runtime auth_provider is invalid: {self.auth_provider}")

        if self.auth_enabled and not str(self.service_token or "").strip():
            raise NsRuntimeConfigurationError("runtime service_token is required when auth_enabled is true")

        if (
                self.auth_provider == "static"
                and self.frontend_auth_enabled
                and not self.allow_anonymous_frontend
                and not str(self.frontend_static_token or "").strip()
        ):
            raise NsRuntimeConfigurationError(
                "runtime frontend_static_token is required when static frontend auth is enabled and anonymous frontend is disabled"
            )

        if self.auth_enabled and not str(self.iam_internal_service_token or self.service_token or "").strip():
            raise NsRuntimeConfigurationError("runtime iam_internal_service_token or service_token is required when auth_enabled is true")

        if self.auth_provider == "remote_iam":
            if not str(self.iam_internal_base_url or "").strip():
                raise NsRuntimeConfigurationError("runtime iam_internal_base_url is required when auth_provider is remote_iam")
            if not str(self.iam_internal_service_token or self.service_token or "").strip():
                raise NsRuntimeConfigurationError(
                    "runtime iam_internal_service_token or service_token is required when auth_provider is remote_iam"
                )

        if self.iam_internal_request_timeout_seconds <= 0:
            raise NsRuntimeConfigurationError("runtime iam_internal_request_timeout_seconds must be positive")
