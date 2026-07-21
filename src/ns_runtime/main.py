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


async def _run_service_once(service: RuntimeService) -> None:
    """Run one listener self-check through the production shutdown path."""

    from ns_runtime.shutdown import RuntimeShutdownReason

    with service.shutdown_coordinator.install_signal_handlers():
        try:
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
        service.shutdown_coordinator.request_shutdown(
            RuntimeShutdownReason.SELF_CHECK_COMPLETE,
        )
        await service.shutdown_coordinator.wait_requested()
        await service.stop()


def main(
    *,
    environment: str | None = None,
    config_path: str | PathLike[str] | None = None,
    startup_root: str | PathLike[str] | None = None,
    startup_directories: RuntimeStartupDirectories | None = None,
    preflight: RuntimeStartupPreflight | None = None,
    transport_ssl_context: SSLContext | None = None,
) -> int:
    """Validate startup, run the configured transport service, and return status.

    Imports stay local so importing :mod:`ns_runtime` or this entry module does
    not load configuration, install an event-loop policy, or create resources.
    The current process performs preflight, starts its supervised internal
    observers and listener, then exits through the same signal-aware shutdown
    coordinator. Long-running signal wait remains outside this startup self-check.
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
    from ns_runtime.connection import (
        AcceptedHeartbeatPolicy,
        ConnectionAcceptedEnvelopeBuilder,
        ConnectionLifecycleManager,
        ConnectionLifecyclePolicy,
        ConnectionLifecycleProcessorRegistryFactory,
        FailClosedHandshakeIamAdapter,
        LocalConnectionIndex,
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
    transport_manager = TransportManager(adapters)
    identifier_factory = IdentifierFactory()
    runtime_id = identifier_factory.generate(NsIdentifierKind.RUNTIME_ID)
    logical_connection_manager = ConnectionLifecycleManager(
        transport_manager=transport_manager,
        connection_index=LocalConnectionIndex(),
        clock=context.clock,
        task_supervisor=context.task_supervisor,
        identifier_factory=identifier_factory,
        iam_adapter=FailClosedHandshakeIamAdapter(),
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
    asyncio.run(_run_service_once(service))

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
    parser.add_argument("command", nargs="?", choices=("diagnose",))
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
    return _run_local_diagnostic(
        environment=arguments.environment,
        config_path=arguments.config_path,
        startup_root=arguments.startup_root,
    )


if __name__ == "__main__":
    raise SystemExit(_module_main())
