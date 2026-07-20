# -*- coding: utf-8 -*-
"""Explicit dependency context for one runtime process."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from _ns_common_error_types import NsValidationError

if TYPE_CHECKING:
    from ns_common.async_runtime import TaskSupervisor
    from ns_common.config.model import NsConfig
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
    expected_type: type[object],
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


def _require_loaded_dependency(
    value: object,
    *,
    dependency: str,
    module_name: str,
    expected_type_name: str,
) -> None:
    """Validate against an already loaded canonical public type.

    A valid dependency can only exist after its defining module has loaded.
    Looking up that module without importing it therefore preserves exact
    ``isinstance`` semantics while keeping validation free of package-facade
    and global-singleton initialization.
    """

    module = sys.modules.get(module_name)
    expected_type = (
        vars(module).get(expected_type_name)
        if module is not None
        else None
    )
    if isinstance(expected_type, type) and isinstance(value, expected_type):
        return
    raise NsValidationError(
        "RuntimeContext dependency is invalid.",
        details={
            "component": "runtime_context",
            "dependency": dependency,
            "expected_type": expected_type_name,
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
            _require_loaded_dependency(
                self.diagnostic_snapshot_sink,
                dependency="dependencies.diagnostic_snapshot_sink",
                module_name="ns_common.observability",
                expected_type_name="DiagnosticSnapshotSink",
            )
        if self.http_client_owner is not None:
            _require_loaded_dependency(
                self.http_client_owner,
                dependency="dependencies.http_client_owner",
                module_name="ns_common.http_client",
                expected_type_name="NsHttpClientOwner",
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
        _require_loaded_dependency(
            self.config,
            dependency="config",
            module_name="ns_common.config.model",
            expected_type_name="NsConfig",
        )
        _require_loaded_dependency(
            self.clock,
            dependency="clock",
            module_name="ns_common.time",
            expected_type_name="Clock",
        )
        _require_dependency(
            self.logger,
            dependency="logger",
            expected_type=logging.Logger,
            expected_type_name="Logger",
        )
        _require_loaded_dependency(
            self.metrics,
            dependency="metrics",
            module_name="ns_common.observability",
            expected_type_name="MetricsSink",
        )
        _require_loaded_dependency(
            self.traces,
            dependency="traces",
            module_name="ns_common.observability",
            expected_type_name="TraceSink",
        )
        _require_loaded_dependency(
            self.task_supervisor,
            dependency="task_supervisor",
            module_name="ns_common.async_runtime",
            expected_type_name="TaskSupervisor",
        )
        _require_dependency(
            self.dependencies,
            dependency="dependencies",
            expected_type=RuntimeDependencySlots,
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
