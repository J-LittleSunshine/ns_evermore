# -*- coding: utf-8 -*-
"""The sole process entry point for the standalone ns_runtime component."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike

    from ns_runtime.service import RuntimeService
    from ns_runtime.startup import (
        RuntimeStartupDirectories,
        RuntimeStartupPreflight,
    )


async def _run_service_once(service: RuntimeService) -> None:
    """Run the current no-listener service through one clean lifecycle."""

    from ns_runtime.shutdown import RuntimeShutdownReason

    with service.shutdown_coordinator.install_signal_handlers():
        await service.start()
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
) -> int:
    """Validate startup, run the no-listener service, and return its status.

    Imports stay local so importing :mod:`ns_runtime` or this entry module does
    not load configuration, install an event-loop policy, or create resources.
    Signal-driven lifetime and resource shutdown orchestration are added by the
    remaining P02 work packages.
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

    startup_preflight.prepare(
        context,
        environment=resolved_environment,
        directories=effective_directories,
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

    from ns_runtime.service import RuntimeService
    from ns_runtime.shutdown import RuntimeShutdownCoordinator

    shutdown_coordinator = RuntimeShutdownCoordinator(
        context=context,
        logger_close=logger.close,
    )
    service = RuntimeService(
        context=context,
        shutdown_coordinator=shutdown_coordinator,
    )
    asyncio.run(_run_service_once(service))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
