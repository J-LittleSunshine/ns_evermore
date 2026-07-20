# -*- coding: utf-8 -*-
"""The sole process entry point for the standalone ns_runtime component."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

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
    The current process performs preflight, starts its supervised internal
    observers, and exits through the same signal-aware shutdown coordinator.
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
    from ns_runtime.service import RuntimeService
    from ns_runtime.shutdown import RuntimeShutdownCoordinator

    shutdown_coordinator = RuntimeShutdownCoordinator(
        context=context,
        logger_close=logger.close,
    )
    event_loop_monitor = RuntimeEventLoopMonitor(
        context=context,
        implementation=startup_result.event_loop.selected,
    )
    service = RuntimeService(
        context=context,
        shutdown_coordinator=shutdown_coordinator,
        event_loop_monitor=event_loop_monitor,
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
