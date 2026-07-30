# -*- coding: utf-8 -*-
"""The sole process entry point for the standalone ns_runtime component."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Sequence

if TYPE_CHECKING:
    from os import PathLike
    from ssl import SSLContext

    from ns_runtime.service import RuntimeService
    from ns_runtime.startup import (
        RuntimeStartupDirectories,
        RuntimeStartupPreflight,
    )


async def _run_service(
    service: RuntimeService,
    *,
    state_store: object | None = None,
    self_check: bool = False,
    service_starting: Callable[[], None] | None = None,
) -> None:
    """Run until signal, critical failure, explicit shutdown, or self-check."""

    from ns_runtime.shutdown import RuntimeShutdownReason

    with service.shutdown_coordinator.install_signal_handlers():
        failure: BaseException | None = None
        store_open_attempted = False
        service_start_attempted = False
        try:
            if state_store is not None:
                store_open_attempted = True
                await state_store.open()  # type: ignore[attr-defined]
            service_start_attempted = True
            await service.start()
            if service_starting is not None:
                service_starting()
            if self_check:
                service.shutdown_coordinator.request_shutdown(
                    RuntimeShutdownReason.SELF_CHECK_COMPLETE,
                )
            await service.shutdown_coordinator.wait_requested()
        except BaseException as operation_failure:
            failure = operation_failure
        finally:
            if service_start_attempted:
                try:
                    await service.stop()
                except BaseException as cleanup_failure:
                    failure = _prioritize_lifecycle_failure(
                        failure,
                        cleanup_failure,
                    )
            if state_store is not None and store_open_attempted:
                try:
                    await state_store.close()  # type: ignore[attr-defined]
                except BaseException as cleanup_failure:
                    failure = _prioritize_lifecycle_failure(
                        failure,
                        cleanup_failure,
                    )
        if failure is not None:
            raise failure


def _prioritize_lifecycle_failure(
    current: BaseException | None,
    candidate: BaseException,
) -> BaseException:
    """Keep the first failure unless a process-level cleanup failure outranks it."""

    if current is None:
        return candidate
    if isinstance(current, Exception) and not isinstance(candidate, Exception):
        return candidate
    return current


async def _run_service_once(
    service: RuntimeService,
    *,
    state_store: object | None = None,
) -> None:
    """Bounded compatibility hook used only by lifecycle tests."""

    await _run_service(
        service,
        state_store=state_store,
        self_check=True,
    )


class _MainCompositionResources:
    """Own resources until the runtime service accepts lifecycle custody."""

    def __init__(self) -> None:
        self.adapters: tuple[object, ...] = ()
        self.transport_manager: object | None = None
        self.task_supervisor: object | None = None
        self.logger: object | None = None
        self.authority_broker: object | None = None

    def transfer_service_resources(self) -> None:
        self.adapters = ()
        self.transport_manager = None
        self.task_supervisor = None
        self.logger = None

    def close(self) -> None:
        import asyncio

        failure: BaseException | None = None
        if (
            self.transport_manager is not None
            or self.adapters
            or self.task_supervisor is not None
        ):
            try:
                asyncio.run(self._close_async())
            except BaseException as cleanup_failure:
                failure = _prioritize_lifecycle_failure(
                    failure,
                    cleanup_failure,
                )
        broker = self.authority_broker
        if broker is not None:
            try:
                broker.close()  # type: ignore[attr-defined]
            except BaseException as cleanup_failure:
                failure = _prioritize_lifecycle_failure(
                    failure,
                    cleanup_failure,
                )
            else:
                self.authority_broker = None
        logger = self.logger
        if logger is not None:
            try:
                logger.close()  # type: ignore[attr-defined]
            except BaseException as cleanup_failure:
                failure = _prioritize_lifecycle_failure(
                    failure,
                    cleanup_failure,
                )
            else:
                self.logger = None
        if failure is not None:
            raise failure

    async def _close_async(self) -> None:
        failure: BaseException | None = None
        manager = self.transport_manager
        if manager is not None:
            try:
                await manager.close()  # type: ignore[attr-defined]
            except BaseException as cleanup_failure:
                failure = _prioritize_lifecycle_failure(
                    failure,
                    cleanup_failure,
                )
            else:
                self.transport_manager = None
                self.adapters = ()
        else:
            pending_adapters: list[object] = []
            for adapter in reversed(self.adapters):
                try:
                    await adapter.close()  # type: ignore[attr-defined]
                except BaseException as cleanup_failure:
                    pending_adapters.append(adapter)
                    failure = _prioritize_lifecycle_failure(
                        failure,
                        cleanup_failure,
                    )
            self.adapters = tuple(reversed(pending_adapters))
        supervisor = self.task_supervisor
        if supervisor is not None:
            try:
                await supervisor.shutdown()  # type: ignore[attr-defined]
            except BaseException as cleanup_failure:
                failure = _prioritize_lifecycle_failure(
                    failure,
                    cleanup_failure,
                )
            else:
                self.task_supervisor = None
        if failure is not None:
            raise failure


async def _run_composed_service(
    resources: _MainCompositionResources,
    service: RuntimeService,
    *,
    state_store: object,
    self_check: bool,
) -> None:
    await _run_service(
        service,
        state_store=state_store,
        self_check=self_check,
        service_starting=resources.transfer_service_resources,
    )


def main(
    *,
    environment: str | None = None,
    config_path: str | PathLike[str] | None = None,
    startup_root: str | PathLike[str] | None = None,
    startup_directories: RuntimeStartupDirectories | None = None,
    preflight: RuntimeStartupPreflight | None = None,
    transport_ssl_context: SSLContext | None = None,
    self_check: bool = False,
) -> int:
    """Validate startup, run the configured transport service, and return status.

    Imports stay local so importing :mod:`ns_runtime` or this entry module does
    not load configuration, install an event-loop policy, or create resources.
    The current process performs preflight, starts its supervised internal
    observers and listener, then waits on the same signal-aware shutdown
    coordinator. ``self_check`` is reserved for the explicit module command.
    """

    from ns_runtime.authority_bootstrap import (
        load_inherited_authority_bootstrap,
    )

    result: int | None = None
    failure: BaseException | None = None
    authority_bootstrap = load_inherited_authority_bootstrap()
    try:
        result = _main_after_authority_bootstrap(
            authority_bootstrap=authority_bootstrap,
            environment=environment,
            config_path=config_path,
            startup_root=startup_root,
            startup_directories=startup_directories,
            preflight=preflight,
            transport_ssl_context=transport_ssl_context,
            self_check=self_check,
        )
    except BaseException as operation_failure:
        failure = operation_failure
    finally:
        try:
            authority_bootstrap.close()
        except BaseException as cleanup_failure:
            failure = _prioritize_lifecycle_failure(
                failure,
                cleanup_failure,
            )
    if failure is not None:
        raise failure
    assert result is not None
    return result


def _main_after_authority_bootstrap(
    *,
    authority_bootstrap: object,
    environment: str | None,
    config_path: str | PathLike[str] | None,
    startup_root: str | PathLike[str] | None,
    startup_directories: RuntimeStartupDirectories | None,
    preflight: RuntimeStartupPreflight | None,
    transport_ssl_context: SSLContext | None,
    self_check: bool,
) -> int:
    resources = _MainCompositionResources()
    result: int | None = None
    failure: BaseException | None = None
    try:
        result = _compose_runtime_main(
            authority_bootstrap=authority_bootstrap,
            resources=resources,
            environment=environment,
            config_path=config_path,
            startup_root=startup_root,
            startup_directories=startup_directories,
            preflight=preflight,
            transport_ssl_context=transport_ssl_context,
            self_check=self_check,
        )
    except BaseException as operation_failure:
        failure = operation_failure
    finally:
        try:
            resources.close()
        except BaseException as cleanup_failure:
            failure = _prioritize_lifecycle_failure(
                failure,
                cleanup_failure,
            )
    if failure is not None:
        raise failure
    assert result is not None
    return result


def _compose_runtime_main(
    *,
    authority_bootstrap: object,
    resources: _MainCompositionResources,
    environment: str | None,
    config_path: str | PathLike[str] | None,
    startup_root: str | PathLike[str] | None,
    startup_directories: RuntimeStartupDirectories | None,
    preflight: RuntimeStartupPreflight | None,
    transport_ssl_context: SSLContext | None,
    self_check: bool,
) -> int:
    import logging

    from ns_runtime._bootstrap import get_default_config_path
    from ns_runtime.startup import (
        RuntimeStartupDirectories,
        RuntimeStartupPreflight,
    )

    startup_preflight = preflight or RuntimeStartupPreflight()
    resolved_environment = startup_preflight.resolve_environment(environment)
    explicit_config_path = (
        get_default_config_path(resolved_environment)
        if config_path is None
        else config_path
    )
    config = startup_preflight.load_config_snapshot(
        explicit_config_path,
        environment=resolved_environment,
    )
    # IAM and StateStore credentials are broker-owned deployment inputs.  The
    # ordinary runtime object graph receives only non-resolvable status
    # markers, before RuntimeContext or any business service is constructed.
    from dataclasses import replace

    config = replace(
        config,
        runtime=replace(
            config.runtime,
            iam=replace(
                config.runtime.iam,
                internal_service_credential=(
                    "configured:redacted-authority-broker-credential"
                ),
            ),
            state_store=replace(
                config.runtime.state_store,
                password_source="configured:redacted",
            ),
        ),
    )
    if startup_root is not None:
        if startup_directories is not None:
            raise ValueError(
                "startup_root and startup_directories are mutually exclusive",
            )
        startup_directories = RuntimeStartupDirectories.for_root(startup_root)
    effective_directories = (
        RuntimeStartupDirectories.repository_defaults()
        if startup_directories is None
        else startup_directories
    )

    from ns_common.async_runtime import TaskSupervisor
    from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
    from ns_common.time import SystemClock
    from ns_runtime.context import RuntimeContext

    bootstrap_logger = logging.Logger("ns_runtime.bootstrap")
    bootstrap_logger.setLevel(config.runtime.logging.level.strip().upper())
    task_supervisor = TaskSupervisor(
        shutdown_timeout_seconds=(
            config.runtime.worker.shutdown_timeout_seconds
        ),
    )
    resources.task_supervisor = task_supervisor
    context = RuntimeContext(
        config=config,
        clock=SystemClock(),
        logger=bootstrap_logger,
        metrics=InMemoryMetricsSink(),
        traces=InMemoryTraceSink(),
        task_supervisor=task_supervisor,
    )

    startup_result = startup_preflight.prepare(
        context,
        environment=resolved_environment,
        directories=effective_directories,
    )

    from ns_common.exceptions import NsRuntimeStartupSecurityError

    transport_config = config.runtime.transport
    websocket_config = transport_config.websocket_tcp
    if websocket_config.enabled and websocket_config.tls_enabled and transport_ssl_context is None:
        raise NsRuntimeStartupSecurityError(
            "Runtime TLS transport material is unavailable.",
            details={
                "component": "runtime_transport",
                "field": "transport_ssl_context",
                "environment": resolved_environment,
                "reason": "tls_material_unavailable",
            },
        )

    from dataclasses import asdict

    from ns_common.logger import NsLogger
    from ns_common.security import Sanitizer

    logger_config = asdict(config.log)
    runtime_log_level = config.runtime.logging.level.strip().upper()
    logger_config.update({
        "level": runtime_log_level,
        "file_level": runtime_log_level,
        "console_level": runtime_log_level,
    })
    if config.runtime.logging.structured:
        logger_config.update({
            "format_type": "json",
            "console_format_type": "json",
            "file_format_type": "json",
        })
    logger = NsLogger(
        "ns_runtime",
        sanitizer=Sanitizer(),
        config=logger_config,
        log_dir=effective_directories.log_dir,
    )
    resources.logger = logger
    context = RuntimeContext(
        config=config,
        clock=context.clock,
        logger=logger,
        metrics=context.metrics,
        traces=context.traces,
        task_supervisor=context.task_supervisor,
        dependencies=context.dependencies,
    )

    import asyncio

    from ns_runtime.event_loop_observability import RuntimeEventLoopMonitor
    from ns_runtime.transport import (
        TransportAdapterBuildContext,
        TransportAdapterRegistry,
        TransportIdentityFactory,
        TransportManager,
        TransportMetricsRecorder,
        TransportRuntimeService,
        WebSocketTcpAdapterOptions,
    )
    from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
    from ns_runtime.authority_broker import (
        AuthorityBrokerConfig,
    )
    from ns_runtime.context import RuntimeDependencySlots
    from ns_runtime.connection import (
        AcceptedHeartbeatPolicy,
        ConnectionAcceptedEnvelopeBuilder,
        ConnectionLifecycleManager,
        ConnectionLifecyclePolicy,
        ConnectionLifecycleProcessorRegistryFactory,
        LocalConnectionIndex,
        PersistenceConnectionLifecycleAuditSink,
    )
    from ns_runtime.iam import (
        AuthorizationMode,
        MessageAuthorizationService,
    )
    from ns_runtime.processor import (
        DefaultProcessorErrorMapper,
        EventBus,
        InterfaceOnlyIdempotencyPrecheck,
        InterfaceOnlyRateLimitEntry,
        LoggingAuditSink,
    )
    from ns_runtime.processor.integration import IamProcessorAuthorization
    from ns_runtime.routing import LocalRouter, LocalRoutingPreparation
    from ns_runtime.state_authority import (
        AuthorityRoutingAuditSink,
        PersistenceStrongAuditAuthorityService,
    )
    from ns_runtime.protocol import ErrorEnvelopeBuilder, JsonV1Codec
    from ns_runtime.roles import RuntimeRole

    transport_metrics = TransportMetricsRecorder(
        clock=context.clock,
        sink=context.metrics,
    )
    build_context = TransportAdapterBuildContext(
        websocket_tcp_options=WebSocketTcpAdapterOptions(
            host=transport_config.listen_host,
            port=transport_config.listen_port,
            clock=context.clock,
            ssl_context=transport_ssl_context,
            environment=resolved_environment,
            allow_plaintext_non_prod=(
                config.runtime.security.allow_plaintext_non_prod
                and not websocket_config.tls_enabled
            ),
            allowed_origins=websocket_config.allowed_origins,
            max_message_bytes=config.runtime.protocol.max_envelope_bytes,
            accept_queue_capacity=transport_config.write_queue_capacity,
            read_queue_capacity=transport_config.write_queue_capacity,
            write_queue_capacity=transport_config.write_queue_capacity,
            send_timeout_seconds=config.runtime.protocol.handshake_timeout_seconds,
            ping_timeout_seconds=config.runtime.protocol.handshake_timeout_seconds,
            close_timeout_seconds=config.runtime.worker.shutdown_timeout_seconds,
            adapter_shutdown_timeout_seconds=(
                config.runtime.worker.shutdown_timeout_seconds
            ),
        ),
        task_supervisor=context.task_supervisor,
        identity_factory=TransportIdentityFactory(),
        metrics=transport_metrics,
    )
    adapters = TransportAdapterRegistry.default().create_enabled(
        startup_result.enabled_transport_adapters,
        context=build_context,
    )
    resources.adapters = adapters
    transport_manager = TransportManager(adapters)
    resources.transport_manager = transport_manager
    identifier_factory = IdentifierFactory()
    runtime_id = identifier_factory.generate(NsIdentifierKind.RUNTIME_ID)
    state_store_config = config.runtime.state_store
    authority_broker = authority_bootstrap.launch(
        config=AuthorityBrokerConfig(
            iam_base_url=config.runtime.iam.base_url,
            iam_timeout_seconds=config.runtime.iam.request_timeout_seconds,
            iam_mode=config.runtime.iam.authorization_mode,
            permission_snapshot_ttl_seconds=(
                config.runtime.iam.permission_snapshot_ttl_seconds
            ),
            state_backend=state_store_config.backend,
            state_endpoint=state_store_config.resolved_endpoint,
            state_username=state_store_config.username,
            state_namespace=state_store_config.namespace,
            state_operation_timeout_seconds=(
                state_store_config.operation_timeout_seconds
            ),
            runtime_id=runtime_id,
        ),
        clock=context.clock,
    )
    resources.authority_broker = authority_broker
    try:
        state_store = authority_broker.state_store
        iam_client = authority_broker.iam
        context = RuntimeContext(
            config=config,
            clock=context.clock,
            logger=context.logger,
            metrics=context.metrics,
            traces=context.traces,
            task_supervisor=context.task_supervisor,
            dependencies=RuntimeDependencySlots(
                state_store=state_store,
                delivery_admission_persistence=(
                    authority_broker.repositories.admission
                ),
                delivery_scheduler_persistence=(
                    authority_broker.repositories.scheduler
                ),
                delivery_payload_persistence=(
                    authority_broker.repositories.payload
                ),
                delivery_registry_persistence=(
                    authority_broker.repositories.registry
                ),
                strong_audit_persistence=(
                    authority_broker.repositories.audit
                ),
            ),
        )
        message_authorization = MessageAuthorizationService(
            iam_client=iam_client,
            clock=context.clock,
            mode=AuthorizationMode(config.runtime.iam.authorization_mode),
            cache_ttl_seconds=config.runtime.iam.permission_snapshot_ttl_seconds,
            snapshot_refresher=iam_client.refresh_permission_snapshot,
        )
        processor_event_bus = EventBus(
            task_supervisor=context.task_supervisor,
            default_timeout_seconds=config.runtime.protocol.handshake_timeout_seconds,
        )
        connection_index = LocalConnectionIndex()
        routing_preparation = LocalRoutingPreparation(
            router=LocalRouter(
                connection_index=connection_index,
                clock=context.clock,
                identifier_factory=identifier_factory,
                runtime_id=runtime_id,
                config=config.runtime.routing,
            ),
        )
        logical_connection_manager = ConnectionLifecycleManager(
            transport_manager=transport_manager,
            connection_index=connection_index,
            clock=context.clock,
            task_supervisor=context.task_supervisor,
            identifier_factory=identifier_factory,
            iam_adapter=iam_client,
            accepted_builder=ConnectionAcceptedEnvelopeBuilder(
                clock=context.clock,
                identifier_factory=identifier_factory,
                runtime_id=runtime_id,
                role=RuntimeRole(config.runtime.cluster.role),
                heartbeat_policy=AcceptedHeartbeatPolicy(
                    interval_seconds=config.runtime.cluster.heartbeat_interval_seconds,
                    timeout_seconds=max(
                        config.runtime.cluster.heartbeat_interval_seconds + 1,
                        config.runtime.protocol.handshake_timeout_seconds,
                    ),
                ),
            ),
            error_builder=ErrorEnvelopeBuilder(sanitizer=Sanitizer()),
            logger=logger,
            runtime_id=runtime_id,
            policy=ConnectionLifecyclePolicy(
                handshake_timeout_seconds=config.runtime.protocol.handshake_timeout_seconds,
                rejected_send_timeout_seconds=config.runtime.protocol.handshake_timeout_seconds,
                native_heartbeat_interval_seconds=(
                    config.runtime.cluster.heartbeat_interval_seconds
                ),
                envelope_heartbeat_timeout_seconds=max(
                    config.runtime.cluster.heartbeat_interval_seconds + 1,
                    config.runtime.protocol.handshake_timeout_seconds,
                ),
                drain_timeout_seconds=config.runtime.worker.shutdown_timeout_seconds,
                reconnect_grace_seconds=30,
                reauth_lead_seconds=min(
                    30,
                    config.runtime.iam.permission_snapshot_ttl_seconds,
                ),
            ),
            codec=JsonV1Codec(),
            processor_registry_factory=ConnectionLifecycleProcessorRegistryFactory(),
            processor_authorization=IamProcessorAuthorization(
                service=message_authorization,
            ),
            processor_rate_limit=InterfaceOnlyRateLimitEntry(),
            processor_idempotency=InterfaceOnlyIdempotencyPrecheck(),
            processor_routing=routing_preparation,
            processor_error_mapper=DefaultProcessorErrorMapper(),
            processor_audit_sink=AuthorityRoutingAuditSink(
                strong_authority=PersistenceStrongAuditAuthorityService(
                    persistence=authority_broker.repositories.audit,
                ),
                ordinary_sink=LoggingAuditSink(logger=logger),
            ),
            lifecycle_audit_sink=PersistenceConnectionLifecycleAuditSink(
                persistence=authority_broker.repositories.audit,
            ),
            event_bus=processor_event_bus,
            config_version=config.config_version,
            policy_version=config.policy_version,
            processor_timeout_seconds=config.runtime.protocol.handshake_timeout_seconds,
        )
        event_loop_monitor = RuntimeEventLoopMonitor(
            context=context,
            implementation=startup_result.event_loop.selected,
        )
        service = TransportRuntimeService(
            context=context,
            transport_manager=transport_manager,
            logger_close=logger.close,
            event_loop_monitor=event_loop_monitor,
            logical_connection_owner=logical_connection_manager,
        )
        asyncio.run(_run_composed_service(
            resources,
            service,
            state_store=state_store,
            self_check=self_check,
        ))
    finally:
        # The enclosing composition scope retains broker ownership so it can
        # prioritize operation and cleanup failures consistently.
        pass

    return 0


_SAFE_DIAGNOSTIC_DETAIL_KEYS = frozenset({
    "component",
    "dependency",
    "directory",
    "field",
    "phase",
    "reason",
})


def _write_diagnostic_json(payload: dict[str, object]) -> None:
    import json
    import sys

    sys.stdout.write(
        json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
    )


def _run_local_diagnostic(
    *,
    environment: str | None,
    config_path: str | None,
    startup_root: str | None,
) -> int:
    from _ns_common_error_types import NsEvermoreError
    from ns_runtime.diagnostics import inspect_local_runtime

    try:
        report = inspect_local_runtime(
            environment=environment,
            config_path=config_path,
            startup_root=startup_root,
        )
    except NsEvermoreError as error:
        safe_details = {
            key: value
            for key, value in error.details.items()
            if key in _SAFE_DIAGNOSTIC_DETAIL_KEYS
            and isinstance(value, (bool, int, float, str))
        }
        payload: dict[str, object] = {
            "status": "error",
            "error_code": error.code,
            "numeric_code": error.numeric_code,
        }
        if safe_details:
            payload["details"] = safe_details
        _write_diagnostic_json(payload)
        return 2
    except Exception:
        _write_diagnostic_json({
            "status": "error",
            "error_code": "NS_ERROR",
            "numeric_code": 100000,
        })
        return 2

    _write_diagnostic_json(report.to_dict())
    return 0 if report.ready else 1


def _module_main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the sole module entry without adding another process entry."""

    import argparse

    parser = argparse.ArgumentParser(prog="python -m ns_runtime.main")
    parser.add_argument("command", nargs="?", choices=("diagnose", "self-check"))
    parser.add_argument("--environment")
    parser.add_argument("--config", dest="config_path")
    parser.add_argument("--startup-root")
    arguments = parser.parse_args(argv)
    if arguments.command is None:
        return main(
            environment=arguments.environment,
            config_path=arguments.config_path,
            startup_root=arguments.startup_root,
        )
    if arguments.command == "diagnose":
        return _run_local_diagnostic(
            environment=arguments.environment,
            config_path=arguments.config_path,
            startup_root=arguments.startup_root,
        )
    return main(
        environment=arguments.environment,
        config_path=arguments.config_path,
        startup_root=arguments.startup_root,
        self_check=True,
    )


if __name__ == "__main__":
    raise SystemExit(_module_main())
