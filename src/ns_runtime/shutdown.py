# -*- coding: utf-8 -*-
"""Signal-driven graceful shutdown orchestration for one runtime process."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import signal
from dataclasses import dataclass
from enum import Enum
from types import TracebackType
from typing import Callable

from ns_common.async_runtime import NsTaskShutdownReport
from ns_common.exceptions import NsValidationError
from ns_runtime.context import RuntimeContext
from ns_runtime._transport_lifecycle_contract import (
    LogicalConnectionLifecycleOwner,
    TransportLifecycleOwner,
)


class RuntimeShutdownReason(str, Enum):
    SIGINT = "sigint"
    SIGTERM = "sigterm"
    SELF_CHECK_COMPLETE = "self_check_complete"
    SERVICE_STOP = "service_stop"
    EXTERNAL = "external"
    CRITICAL_TASK_FAILURE = "critical_task_failure"


class RuntimeShutdownPhase(str, Enum):
    STOP_ADMISSION = "stop_admission"
    STOP_LOGICAL_ADMISSION = "stop_logical_admission"
    DRAIN_LOGICAL_CONNECTIONS = "drain_logical_connections"
    DRAIN_TRANSPORT = "drain_transport"
    CLOSE_TRANSPORT = "close_transport"
    CANCEL_TASKS = "cancel_tasks"
    CLOSE_STATE_STORE = "close_state_store"
    FLUSH_SINKS = "flush_sinks"
    CLOSE_SINKS = "close_sinks"
    CLOSE_CLIENTS = "close_clients"
    WRITE_SUMMARY = "write_summary"
    CLOSE_LOGGER = "close_logger"


@dataclass(frozen=True, slots=True)
class RuntimeShutdownFailure:
    phase: RuntimeShutdownPhase
    resource: str
    error_type: str


@dataclass(frozen=True, slots=True)
class RuntimeShutdownReport:
    reason: RuntimeShutdownReason
    phases: tuple[RuntimeShutdownPhase, ...]
    total_tasks: int
    completed_tasks: tuple[str, ...]
    cancelled_tasks: tuple[str, ...]
    failed_tasks: tuple[str, ...]
    unfinished_tasks: tuple[str, ...]
    task_timeout_seconds: float
    failures: tuple[RuntimeShutdownFailure, ...]

    @property
    def timed_out(self) -> bool:
        return bool(self.unfinished_tasks)

    @property
    def clean(self) -> bool:
        return not self.failed_tasks and not self.unfinished_tasks and not self.failures


class RuntimeSignalRegistration:
    """Own reversible SIGINT/SIGTERM registrations for one event loop."""

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop,
        coordinator: "RuntimeShutdownCoordinator",
    ) -> None:
        self._loop = loop
        self._coordinator = coordinator
        self._registrations: list[
            tuple[signal.Signals, signal.Handlers, bool]
        ] = []
        self._closed = False
        self._install()

    def _install(self) -> None:
        for signal_value, reason in (
            (signal.SIGINT, RuntimeShutdownReason.SIGINT),
            (signal.SIGTERM, RuntimeShutdownReason.SIGTERM),
        ):
            previous = signal.getsignal(signal_value)
            try:
                self._loop.add_signal_handler(
                    signal_value,
                    self._coordinator.request_shutdown,
                    reason,
                )
            except (NotImplementedError, RuntimeError):
                def fallback_handler(
                    _signum: int,
                    _frame: object,
                    *,
                    shutdown_reason: RuntimeShutdownReason = reason,
                ) -> None:
                    self._loop.call_soon_threadsafe(
                        self._coordinator.request_shutdown,
                        shutdown_reason,
                    )

                signal.signal(signal_value, fallback_handler)
                self._registrations.append((signal_value, previous, False))
            else:
                self._registrations.append((signal_value, previous, True))

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for signal_value, previous, uses_loop in reversed(self._registrations):
            if uses_loop:
                self._loop.remove_signal_handler(signal_value)
            signal.signal(signal_value, previous)

    def __enter__(self) -> "RuntimeSignalRegistration":
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self.close()


class RuntimeShutdownCoordinator:
    """Stop local admission and release explicitly injected dependencies.

    P04 extends the P02 local gate with one optional typed transport lifecycle
    owner. The coordinator never imports or branches on a concrete adapter.
    """

    def __init__(
        self,
        *,
        context: RuntimeContext,
        logger_close: Callable[[], None] | None = None,
        transport_owner: TransportLifecycleOwner | None = None,
        logical_connection_owner: LogicalConnectionLifecycleOwner | None = None,
    ) -> None:
        if not isinstance(context, RuntimeContext):
            raise NsValidationError(
                "Runtime shutdown context is invalid.",
                details={
                    "component": "runtime_shutdown",
                    "dependency": "context",
                    "expected_type": "RuntimeContext",
                    "actual_type": type(context).__name__,
                },
            )
        if logger_close is not None and not callable(logger_close):
            raise NsValidationError(
                "Runtime shutdown logger closer is invalid.",
                details={
                    "component": "runtime_shutdown",
                    "dependency": "logger_close",
                    "expected_type": "Callable",
                    "actual_type": type(logger_close).__name__,
                },
            )
        if transport_owner is not None and not isinstance(
            transport_owner,
            TransportLifecycleOwner,
        ):
            raise NsValidationError(
                "Runtime shutdown transport owner is invalid.",
                details={
                    "component": "runtime_shutdown",
                    "dependency": "transport_owner",
                    "expected_type": "TransportLifecycleOwner",
                    "actual_type": type(transport_owner).__name__,
                },
            )
        if logical_connection_owner is not None and not isinstance(
            logical_connection_owner,
            LogicalConnectionLifecycleOwner,
        ):
            raise NsValidationError(
                "Runtime shutdown logical connection owner is invalid.",
                details={
                    "component": "runtime_shutdown",
                    "dependency": "logical_connection_owner",
                    "expected_type": "LogicalConnectionLifecycleOwner",
                    "actual_type": type(logical_connection_owner).__name__,
                },
            )
        self._context = context
        self._logger_close = logger_close
        self._transport_owner = transport_owner
        self._logical_connection_owner = logical_connection_owner
        self._admission_open = True
        self._requested = asyncio.Event()
        self._reason: RuntimeShutdownReason | None = None
        self._shutdown_lock = asyncio.Lock()
        self._report: RuntimeShutdownReport | None = None
        self._admission_failures: list[RuntimeShutdownFailure] = []

    @property
    def admission_open(self) -> bool:
        return self._admission_open

    @property
    def context(self) -> RuntimeContext:
        return self._context

    @property
    def reason(self) -> RuntimeShutdownReason | None:
        return self._reason

    @property
    def report(self) -> RuntimeShutdownReport | None:
        return self._report

    def request_shutdown(self, reason: RuntimeShutdownReason) -> bool:
        if not isinstance(reason, RuntimeShutdownReason):
            raise NsValidationError(
                "Runtime shutdown reason is invalid.",
                details={
                    "component": "runtime_shutdown",
                    "field": "reason",
                    "expected_type": "RuntimeShutdownReason",
                    "actual_type": type(reason).__name__,
                },
            )
        if self._reason is not None:
            return False
        self._reason = reason
        self._admission_open = False
        if self._transport_owner is not None:
            try:
                self._transport_owner.stop_admission_now()
            except Exception as error:
                self._admission_failures.append(RuntimeShutdownFailure(
                    phase=RuntimeShutdownPhase.STOP_ADMISSION,
                    resource="transport_owner",
                    error_type=type(error).__name__,
                ))
        if self._logical_connection_owner is not None:
            try:
                self._logical_connection_owner.stop_admission_now()
            except Exception as error:
                self._admission_failures.append(RuntimeShutdownFailure(
                    phase=RuntimeShutdownPhase.STOP_LOGICAL_ADMISSION,
                    resource="logical_connection_owner",
                    error_type=type(error).__name__,
                ))
        self._requested.set()
        return True

    async def wait_requested(self) -> RuntimeShutdownReason:
        await self._requested.wait()
        assert self._reason is not None
        return self._reason

    def install_signal_handlers(self) -> RuntimeSignalRegistration:
        return RuntimeSignalRegistration(
            loop=asyncio.get_running_loop(),
            coordinator=self,
        )

    async def shutdown(self) -> RuntimeShutdownReport:
        async with self._shutdown_lock:
            if self._report is not None:
                return self._report
            if self._reason is None:
                self.request_shutdown(RuntimeShutdownReason.SERVICE_STOP)

            phases: list[RuntimeShutdownPhase] = [
                RuntimeShutdownPhase.STOP_ADMISSION,
            ]
            failures: list[RuntimeShutdownFailure] = list(
                self._admission_failures,
            )

            if self._transport_owner is not None:
                await self._attempt_async(
                    self._transport_owner.stop_admission,
                    phase=RuntimeShutdownPhase.STOP_ADMISSION,
                    resource="transport_owner",
                    failures=failures,
                )

            phases.append(RuntimeShutdownPhase.STOP_LOGICAL_ADMISSION)
            if self._logical_connection_owner is not None:
                await self._attempt_async(
                    self._logical_connection_owner.stop_admission,
                    phase=RuntimeShutdownPhase.STOP_LOGICAL_ADMISSION,
                    resource="logical_connection_owner",
                    failures=failures,
                )

            phases.append(RuntimeShutdownPhase.DRAIN_LOGICAL_CONNECTIONS)
            if self._logical_connection_owner is not None:
                await self._attempt_async(
                    self._logical_connection_owner.drain,
                    phase=RuntimeShutdownPhase.DRAIN_LOGICAL_CONNECTIONS,
                    resource="logical_connection_owner",
                    failures=failures,
                )

            phases.append(RuntimeShutdownPhase.DRAIN_TRANSPORT)
            if self._transport_owner is not None:
                await self._attempt_async(
                    self._transport_owner.drain,
                    phase=RuntimeShutdownPhase.DRAIN_TRANSPORT,
                    resource="transport_owner",
                    failures=failures,
                )

            phases.append(RuntimeShutdownPhase.CLOSE_TRANSPORT)
            if self._transport_owner is not None:
                await self._attempt_async(
                    self._transport_owner.close,
                    phase=RuntimeShutdownPhase.CLOSE_TRANSPORT,
                    resource="transport_owner",
                    failures=failures,
                )

            phases.append(RuntimeShutdownPhase.CANCEL_TASKS)
            task_report = await self._shutdown_tasks(failures)

            phases.append(RuntimeShutdownPhase.CLOSE_STATE_STORE)
            state_store = self._context.state_store
            if state_store is not None:
                await self._attempt_async(
                    state_store.close,
                    phase=RuntimeShutdownPhase.CLOSE_STATE_STORE,
                    resource="state_store",
                    failures=failures,
                )

            sinks = self._sinks()
            phases.append(RuntimeShutdownPhase.FLUSH_SINKS)
            for resource, sink in sinks:
                await self._attempt_async(
                    sink.flush,
                    phase=RuntimeShutdownPhase.FLUSH_SINKS,
                    resource=resource,
                    failures=failures,
                )

            phases.append(RuntimeShutdownPhase.CLOSE_SINKS)
            for resource, sink in sinks:
                await self._attempt_async(
                    sink.aclose,
                    phase=RuntimeShutdownPhase.CLOSE_SINKS,
                    resource=resource,
                    failures=failures,
                )

            phases.append(RuntimeShutdownPhase.CLOSE_CLIENTS)
            owner = self._context.http_client_owner
            if owner is not None:
                await self._attempt_async(
                    owner.aclose,
                    phase=RuntimeShutdownPhase.CLOSE_CLIENTS,
                    resource="http_client_owner",
                    failures=failures,
                )

            phases.append(RuntimeShutdownPhase.WRITE_SUMMARY)
            self._write_summary(task_report, failures)

            phases.append(RuntimeShutdownPhase.CLOSE_LOGGER)
            if self._logger_close is not None:
                self._attempt_sync(
                    self._logger_close,
                    phase=RuntimeShutdownPhase.CLOSE_LOGGER,
                    resource="runtime_logger",
                    failures=failures,
                )

            assert self._reason is not None
            self._report = RuntimeShutdownReport(
                reason=self._reason,
                phases=tuple(phases),
                total_tasks=task_report.total_tasks if task_report else 0,
                completed_tasks=(
                    task_report.completed_tasks if task_report else ()
                ),
                cancelled_tasks=(
                    task_report.cancelled_tasks if task_report else ()
                ),
                failed_tasks=task_report.failed_tasks if task_report else (),
                unfinished_tasks=(
                    tuple(item.name for item in task_report.unfinished_tasks)
                    if task_report
                    else ()
                ),
                task_timeout_seconds=(
                    task_report.timeout_seconds if task_report else 0.0
                ),
                failures=tuple(failures),
            )
            return self._report

    async def _shutdown_tasks(
        self,
        failures: list[RuntimeShutdownFailure],
    ) -> NsTaskShutdownReport | None:
        try:
            return await self._context.task_supervisor.shutdown()
        except Exception as error:
            failures.append(RuntimeShutdownFailure(
                phase=RuntimeShutdownPhase.CANCEL_TASKS,
                resource="task_supervisor",
                error_type=type(error).__name__,
            ))
            return None

    def _sinks(self) -> tuple[tuple[str, object], ...]:
        sinks: list[tuple[str, object]] = [
            ("metrics", self._context.metrics),
            ("traces", self._context.traces),
        ]
        diagnostic = self._context.diagnostic_snapshot_sink
        if diagnostic is not None:
            sinks.append(("diagnostic_snapshot", diagnostic))
        return tuple(sinks)

    async def _attempt_async(
        self,
        operation: Callable[[], object],
        *,
        phase: RuntimeShutdownPhase,
        resource: str,
        failures: list[RuntimeShutdownFailure],
    ) -> None:
        try:
            result = operation()
            if not hasattr(result, "__await__"):
                raise TypeError("shutdown operation must be awaitable")
            await result
        except Exception as error:
            failures.append(RuntimeShutdownFailure(
                phase=phase,
                resource=resource,
                error_type=type(error).__name__,
            ))

    @staticmethod
    def _attempt_sync(
        operation: Callable[[], None],
        *,
        phase: RuntimeShutdownPhase,
        resource: str,
        failures: list[RuntimeShutdownFailure],
    ) -> None:
        try:
            operation()
        except Exception as error:
            failures.append(RuntimeShutdownFailure(
                phase=phase,
                resource=resource,
                error_type=type(error).__name__,
            ))

    def _write_summary(
        self,
        task_report: NsTaskShutdownReport | None,
        failures: list[RuntimeShutdownFailure],
    ) -> None:
        unfinished = (
            tuple(item.name for item in task_report.unfinished_tasks)
            if task_report
            else ()
        )
        failed_tasks = task_report.failed_tasks if task_report else ()
        level = logging.WARNING if failures or unfinished or failed_tasks else logging.INFO
        unfinished_digests = tuple(
            hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
            for name in unfinished
        )
        try:
            self._context.logger.log(
                level,
                "Runtime shutdown completed.",
                extra={
                    "event": "runtime_shutdown_summary",
                    "shutdown_reason": (
                        self._reason.value if self._reason else "service_stop"
                    ),
                    "task_total": task_report.total_tasks if task_report else 0,
                    "task_cancelled_count": (
                        len(task_report.cancelled_tasks) if task_report else 0
                    ),
                    "task_failed_count": len(failed_tasks),
                    "task_unfinished_count": len(unfinished),
                    "task_unfinished_digests": unfinished_digests,
                    "cleanup_failure_count": len(failures),
                    "cleanup_failure_types": tuple(
                        failure.error_type for failure in failures
                    ),
                },
            )
        except Exception as error:
            failures.append(RuntimeShutdownFailure(
                phase=RuntimeShutdownPhase.WRITE_SUMMARY,
                resource="runtime_logger",
                error_type=type(error).__name__,
            ))


__all__ = [
    "RuntimeShutdownCoordinator",
    "RuntimeShutdownFailure",
    "RuntimeShutdownPhase",
    "RuntimeShutdownReason",
    "RuntimeShutdownReport",
    "RuntimeSignalRegistration",
]
