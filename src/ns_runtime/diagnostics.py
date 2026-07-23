# -*- coding: utf-8 -*-
"""Read-only local diagnostics for the standalone runtime process."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from os import PathLike

from ns_runtime.startup import (
    RuntimeStartupDirectories,
    RuntimeStartupDirectoryStatus,
    RuntimeStartupPreflight,
)


@dataclass(frozen=True, slots=True)
class RuntimeLocalDiagnosticReport:
    """Sanitized facts proving whether local startup requirements are ready."""

    ready: bool
    config_valid: bool
    dependencies_available: bool
    environment: str
    event_loop_implementation: str
    event_loop_fallback: bool
    enabled_transport_adapters: tuple[str, ...]
    tls_transport_adapters: tuple[str, ...]
    state_store_backend: str
    checked_dependencies: tuple[str, ...]
    directories: tuple[RuntimeStartupDirectoryStatus, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "ready" if self.ready else "not_ready",
            "ready": self.ready,
            "config_valid": self.config_valid,
            "dependencies_available": self.dependencies_available,
            "environment": self.environment,
            "event_loop_implementation": self.event_loop_implementation,
            "event_loop_fallback": self.event_loop_fallback,
            "enabled_transport_adapters": list(
                self.enabled_transport_adapters,
            ),
            "tls_transport_adapters": list(self.tls_transport_adapters),
            "state_store_backend": self.state_store_backend,
            "checked_dependencies": list(self.checked_dependencies),
            "directories": [
                {"role": item.role, "state": item.state}
                for item in self.directories
            ],
        }


def inspect_local_runtime(
    *,
    environment: str | None = None,
    config_path: str | PathLike[str] | None = None,
    startup_root: str | PathLike[str] | None = None,
    startup_directories: RuntimeStartupDirectories | None = None,
    preflight: RuntimeStartupPreflight | None = None,
) -> RuntimeLocalDiagnosticReport:
    """Inspect config, local packages, TLS support, and directory readiness.

    This function never prepares directories, installs an event-loop policy,
    starts a service, creates a monitor, or opens a network endpoint.
    """

    from ns_runtime._bootstrap import get_default_config_path

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

    bootstrap_logger = logging.Logger("ns_runtime.diagnostics")
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
    inspection = startup_preflight.inspect(
        context,
        environment=resolved_environment,
        directories=effective_directories,
    )
    return RuntimeLocalDiagnosticReport(
        ready=inspection.ready,
        config_valid=True,
        dependencies_available=True,
        environment=inspection.environment,
        event_loop_implementation=inspection.event_loop.selected.value,
        event_loop_fallback=inspection.event_loop.fallback,
        enabled_transport_adapters=inspection.enabled_transport_adapters,
        tls_transport_adapters=inspection.tls_transport_adapters,
        state_store_backend=inspection.state_store_backend,
        checked_dependencies=inspection.checked_dependencies,
        directories=inspection.directories,
    )


__all__ = [
    "RuntimeLocalDiagnosticReport",
    "inspect_local_runtime",
]
