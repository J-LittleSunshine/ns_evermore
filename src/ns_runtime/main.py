# -*- coding: utf-8 -*-
"""The sole process entry point for the standalone ns_runtime component."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

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
) -> None:
    """Run until signal, critical failure, explicit shutdown, or self-check."""

    from ns_runtime.shutdown import RuntimeShutdownReason

    with service.shutdown_coordinator.install_signal_handlers():
        try:
            if state_store is not None:
                await state_store.open()  # type: ignore[attr-defined]
            await service.start()
        except BaseException as start_failure:
            try:
                await service.stop()
            except BaseException as cleanup_failure:
                # Ordinary cleanup failure cannot hide the original startup
                # outcome.  A process-level cleanup failure takes precedence
                # only when startup itself was an ordinary Exception.
                if (
                    isinstance(start_failure, Exception)
                    and not isinstance(cleanup_failure, Exception)
                ):
                    raise
            raise
        if self_check:
            service.shutdown_coordinator.request_shutdown(
                RuntimeShutdownReason.SELF_CHECK_COMPLETE,
            )
        await service.shutdown_coordinator.wait_requested()
        await service.stop()


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
    context = RuntimeContext(
        config=config,
        clock=SystemClock(),
        logger=bootstrap_logger,
        metrics=InMemoryMetricsSink(),
        traces=InMemoryTraceSink(),
        task_supervisor=TaskSupervisor(
            shutdown_timeout_seconds=(
                config.runtime.worker.shutdown_timeout_seconds
            ),
        ),
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
    from ns_common.http_client import (
        NsHttpClientOwner,
        _NsHttpClientAuthorityBinding,
        _NsHttpClientAuthorityHandle,
    )
    from ns_runtime.context import RuntimeDependencySlots
    from ns_runtime.connection import (
        AcceptedHeartbeatPolicy,
        ConnectionAcceptedEnvelopeBuilder,
        ConnectionLifecycleManager,
        ConnectionLifecyclePolicy,
        ConnectionLifecycleProcessorRegistryFactory,
        LocalConnectionIndex,
        UnavailableConnectionLifecycleAuditSink,
    )
    from ns_runtime.iam import (
        AuthorizationMode,
        MessageAuthorizationService,
    )
    from ns_runtime.iam.client import IamClient
    from ns_runtime.processor import (
        DefaultProcessorErrorMapper,
        EventBus,
        InterfaceOnlyIdempotencyPrecheck,
        InterfaceOnlyRateLimitEntry,
        LoggingAuditSink,
    )
    from ns_runtime.processor.integration import IamProcessorAuthorization
    from ns_runtime.routing import LocalRouter, LocalRoutingPreparation
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
    transport_manager = TransportManager(adapters)
    identifier_factory = IdentifierFactory()
    runtime_id = identifier_factory.generate(NsIdentifierKind.RUNTIME_ID)
    http_client_owner = NsHttpClientOwner()
    iam_http_client = http_client_owner.create(
        name="runtime-iam",
        base_url=config.runtime.iam.base_url,
        timeout_seconds=config.runtime.iam.request_timeout_seconds,
    )
    from ns_common.state_store import (
        StateAuthorityKind,
        StateCallerCapability,
        StateStoreDeliveryRepositories,
        StateStoreRepositoryRole,
    )
    from ns_common.state_store.composition import (
        StateStoreComposition,
        _acquire_production_lease,
        _create_redis_valkey_provider,
    )
    from ns_common.state_store.store import _ProductionStateScopeValidator

    state_store_config = config.runtime.state_store
    state_store_composition = None
    if state_store_config.backend != "sqlite":
        state_lease = _acquire_production_lease(
            config=state_store_config, runtime_id=runtime_id,
        )
        state_validator = object.__new__(_ProductionStateScopeValidator)
        state_validator._repository_specs = {}
        state_validator._scopes = {}
        state_validator._closed = False
        state_validator._realm = "production"
        composed_store = _create_redis_valkey_provider(
            config=state_store_config, clock=context.clock,
            capabilities=None, production_scope_validator=state_validator,
        )
        assert composed_store is not None
        state_repositories = composed_store._install_repositories((
            (
                StateStoreRepositoryRole.DELIVERY_ADMISSION, runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION, "delivery.admission",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                    StateCallerCapability.APPEND,
                }), "delivery-admission.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_SCHEDULER, runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION, "delivery.scheduling",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                    StateCallerCapability.APPEND,
                }), "delivery-scheduler.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_PAYLOAD, runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION,
                "delivery.payload_authority",
                frozenset({StateCallerCapability.READ}),
                "delivery-payload.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_REGISTRY, runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION,
                "delivery.authority_registry",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                }), "delivery-registry.v1",
            ),
        ))
        state_store_composition = object.__new__(StateStoreComposition)
        state_store_composition.store = composed_store
        state_store_composition._delivery = StateStoreDeliveryRepositories(
            admission=state_repositories[0],
            scheduler=state_repositories[1],
            payload=state_repositories[2],
            registry=state_repositories[3],
        )
        state_store_composition._runtime_id = runtime_id
        state_store_composition._audit = {}
        state_store_composition._lease = state_lease
    state_store = (
        None
        if state_store_composition is None
        else state_store_composition.store
    )
    context = RuntimeContext(
        config=config,
        clock=context.clock,
        logger=context.logger,
        metrics=context.metrics,
        traces=context.traces,
        task_supervisor=context.task_supervisor,
        dependencies=RuntimeDependencySlots(
            http_client_owner=http_client_owner,
            state_store=state_store,
        ),
    )
    # Assemble the complete graph here. No owner/factory method can issue an
    # IAM authority handle, and the one-shot construction tokens are consumed
    # before any business object receives a dependency.
    binding_token = object()
    http_client_owner._pending_authority_binding_token = binding_token
    try:
        iam_http_binding = _NsHttpClientAuthorityBinding(
            owner=http_client_owner,
            client=iam_http_client,
            _token=binding_token,
        )
    finally:
        http_client_owner._pending_authority_binding_token = None
    http_client_owner._authority_bindings[iam_http_client] = iam_http_binding
    handle_token = object()
    http_client_owner._pending_authority_handle_token = handle_token
    try:
        iam_http_authority = _NsHttpClientAuthorityHandle(
            binding=iam_http_binding,
            _token=handle_token,
            owner=http_client_owner,
        )
    finally:
        http_client_owner._pending_authority_handle_token = None
    iam_client = object.__new__(IamClient)
    iam_client._http_authority = iam_http_authority
    iam_http_binding._iam_client = iam_client
    iam_client._service_credential = (
        config.runtime.iam.internal_service_credential
    )
    iam_client._trace_id_factory = lambda: identifier_factory.generate(
        NsIdentifierKind.OPERATION_ID,
    )
    iam_client._clock = context.clock
    iam_client._iam_mode = config.runtime.iam.authorization_mode
    iam_client._payload_revalidation_results = {}
    iam_client._authorization_service = None
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
        processor_audit_sink=LoggingAuditSink(logger=logger),
        lifecycle_audit_sink=UnavailableConnectionLifecycleAuditSink(),
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
    asyncio.run(_run_service(
        service,
        state_store=state_store,
        self_check=self_check,
    ))

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
