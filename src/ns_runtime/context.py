# -*- coding: utf-8 -*-
"""Explicit dependency context for one runtime process."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Type

from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsConfig
from ns_common.exceptions import NsValidationError
from ns_common.http_client import NsHttpClientOwner
from ns_common.observability import (
    DiagnosticSnapshotSink,
    MetricsSink,
    TraceSink,
)
from ns_common.time import Clock


def _require_dependency(
    value: object,
    *,
    dependency: str,
    expected_type: Type[object],
    expected_type_name: str | None = None,
) -> None:
    if isinstance(value, expected_type):
        return
    raise NsValidationError(
        "RuntimeContext dependency is invalid.",
        details={
            "component": "runtime_context",
            "dependency": dependency,
            "expected_type": expected_type_name or expected_type.__name__,
            "actual_type": type(value).__name__,
        },
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeDependencySlots:
    """Typed slots for common dependencies wired by later work packages.

    The slots are deliberately finite and immutable.  Runtime-private
    dependencies are added as explicit typed fields when their contracts are
    frozen; this object is not a name-based registry or service locator.
    """

    diagnostic_snapshot_sink: DiagnosticSnapshotSink | None = None
    http_client_owner: NsHttpClientOwner | None = None

    def __post_init__(self) -> None:
        if self.diagnostic_snapshot_sink is not None:
            _require_dependency(
                self.diagnostic_snapshot_sink,
                dependency="dependencies.diagnostic_snapshot_sink",
                expected_type=DiagnosticSnapshotSink,
            )
        if self.http_client_owner is not None:
            _require_dependency(
                self.http_client_owner,
                dependency="dependencies.http_client_owner",
                expected_type=NsHttpClientOwner,
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeContext:
    """Immutable wiring snapshot for one :class:`RuntimeService`.

    The context freezes dependency references, not the lifecycle state of the
    referenced objects.  Creation, startup, flushing and shutdown remain the
    responsibility of the process composition root and later lifecycle work.
    """

    config: NsConfig
    clock: Clock
    logger: logging.Logger
    metrics: MetricsSink
    traces: TraceSink
    task_supervisor: TaskSupervisor
    dependencies: RuntimeDependencySlots = field(
        default_factory=RuntimeDependencySlots,
    )

    def __post_init__(self) -> None:
        expectations = (
            (self.config, "config", NsConfig, None),
            (self.clock, "clock", Clock, None),
            (self.logger, "logger", logging.Logger, "Logger"),
            (self.metrics, "metrics", MetricsSink, None),
            (self.traces, "traces", TraceSink, None),
            (
                self.task_supervisor,
                "task_supervisor",
                TaskSupervisor,
                None,
            ),
            (
                self.dependencies,
                "dependencies",
                RuntimeDependencySlots,
                None,
            ),
        )
        for value, dependency, expected_type, expected_type_name in expectations:
            _require_dependency(
                value,
                dependency=dependency,
                expected_type=expected_type,
                expected_type_name=expected_type_name,
            )

    @property
    def config_snapshot(self) -> NsConfig:
        return self.config

    @property
    def metrics_sink(self) -> MetricsSink:
        return self.metrics

    @property
    def trace_sink(self) -> TraceSink:
        return self.traces

    @property
    def diagnostic_snapshot_sink(self) -> DiagnosticSnapshotSink | None:
        return self.dependencies.diagnostic_snapshot_sink

    @property
    def http_client_owner(self) -> NsHttpClientOwner | None:
        return self.dependencies.http_client_owner


__all__ = [
    "RuntimeContext",
    "RuntimeDependencySlots",
]
