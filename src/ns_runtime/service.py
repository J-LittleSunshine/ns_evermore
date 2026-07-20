# -*- coding: utf-8 -*-
"""Runtime process lifecycle service."""

from __future__ import annotations

import asyncio
from enum import Enum
from threading import Lock
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsStateError, NsValidationError
from ns_runtime.context import RuntimeContext
from ns_runtime.event_loop_observability import (
    RuntimeEventLoopMonitor,
    RuntimeEventLoopSnapshot,
)
from ns_runtime.roles import (
    RuntimeCapability,
    RuntimeRoleSnapshot,
    RuntimeRoleState,
)
from ns_runtime.shutdown import (
    RuntimeShutdownCoordinator,
    RuntimeShutdownReason,
    RuntimeShutdownReport,
)


class RuntimeServiceState(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


_RUNTIME_SERVICE_TRANSITIONS: Mapping[
    RuntimeServiceState,
    tuple[RuntimeServiceState, ...],
] = MappingProxyType({
    RuntimeServiceState.CREATED: (RuntimeServiceState.STARTING,),
    RuntimeServiceState.STARTING: (
        RuntimeServiceState.RUNNING,
        RuntimeServiceState.FAILED,
    ),
    RuntimeServiceState.RUNNING: (
        RuntimeServiceState.STOPPING,
        RuntimeServiceState.FAILED,
    ),
    RuntimeServiceState.STOPPING: (
        RuntimeServiceState.STOPPED,
        RuntimeServiceState.FAILED,
    ),
    RuntimeServiceState.STOPPED: (),
    RuntimeServiceState.FAILED: (RuntimeServiceState.STOPPING,),
})


class RuntimeService:
    """Own the one-shot lifecycle of one runtime process.

    Every service is constructed with one immutable ``RuntimeContext``.  This
    class retains that wiring identity and does not create or start injected
    dependencies.  Its shutdown coordinator stops supervised work and closes
    explicitly wired sinks/clients after the subclass stop hook succeeds.
    Lifecycle operations are serialized on the first event loop that uses the
    service. ``FAILED`` blocks restart but remains eligible for explicit cleanup
    through ``stop()``; ``STOPPED`` makes later ``stop()`` calls idempotent.
    Subclasses may implement the protected hooks while retaining these state
    transition and failure semantics.
    """

    def __init__(
        self,
        *,
        context: RuntimeContext,
        shutdown_coordinator: RuntimeShutdownCoordinator | None = None,
        event_loop_monitor: RuntimeEventLoopMonitor | None = None,
    ) -> None:
        if not isinstance(context, RuntimeContext):
            raise NsValidationError(
                "RuntimeService requires a RuntimeContext.",
                details={
                    "component": "runtime_service",
                    "dependency": "context",
                    "expected_type": "RuntimeContext",
                    "actual_type": type(context).__name__,
                },
            )
        self._context = context
        if shutdown_coordinator is not None and not isinstance(
            shutdown_coordinator,
            RuntimeShutdownCoordinator,
        ):
            raise NsValidationError(
                "RuntimeService shutdown coordinator is invalid.",
                details={
                    "component": "runtime_service",
                    "dependency": "shutdown_coordinator",
                    "expected_type": "RuntimeShutdownCoordinator",
                    "actual_type": type(shutdown_coordinator).__name__,
                },
            )
        if (
            shutdown_coordinator is not None
            and shutdown_coordinator.context is not context
        ):
            raise NsValidationError(
                "RuntimeService shutdown coordinator context is invalid.",
                details={
                    "component": "runtime_service",
                    "dependency": "shutdown_coordinator.context",
                    "reason": "context_identity_mismatch",
                },
            )
        self._shutdown_coordinator = (
            RuntimeShutdownCoordinator(context=context)
            if shutdown_coordinator is None
            else shutdown_coordinator
        )
        if event_loop_monitor is not None and not isinstance(
            event_loop_monitor,
            RuntimeEventLoopMonitor,
        ):
            raise NsValidationError(
                "RuntimeService event-loop monitor is invalid.",
                details={
                    "component": "runtime_service",
                    "dependency": "event_loop_monitor",
                    "expected_type": "RuntimeEventLoopMonitor",
                    "actual_type": type(event_loop_monitor).__name__,
                },
            )
        if (
            event_loop_monitor is not None
            and event_loop_monitor.context is not context
        ):
            raise NsValidationError(
                "RuntimeService event-loop monitor context is invalid.",
                details={
                    "component": "runtime_service",
                    "dependency": "event_loop_monitor.context",
                    "reason": "context_identity_mismatch",
                },
            )
        self._event_loop_monitor = event_loop_monitor
        self._shutdown_report: RuntimeShutdownReport | None = None
        self._role_state = RuntimeRoleState(
            configured_role=context.config.runtime.cluster.role,
            logger=context.logger,
        )
        self._state = RuntimeServiceState.CREATED
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_binding_lock = Lock()
        self._lifecycle_lock = asyncio.Lock()

    @property
    def state(self) -> RuntimeServiceState:
        return self._state

    @property
    def context(self) -> RuntimeContext:
        return self._context

    @property
    def role(self) -> RuntimeRoleSnapshot:
        return self._role_state.snapshot

    @property
    def shutdown_coordinator(self) -> RuntimeShutdownCoordinator:
        return self._shutdown_coordinator

    @property
    def shutdown_report(self) -> RuntimeShutdownReport | None:
        return self._shutdown_report

    @property
    def event_loop_snapshot(self) -> RuntimeEventLoopSnapshot | None:
        if self._event_loop_monitor is None:
            return None
        return self._event_loop_monitor.snapshot

    def require_capability(self, capability: RuntimeCapability) -> None:
        """Reject capabilities that are intentionally unavailable in P02."""

        self._role_state.require_capability(capability)

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        self._bind_loop(loop, operation="start")

        async with self._lifecycle_lock:
            self._transition(RuntimeServiceState.STARTING, operation="start")
            try:
                await self._on_start()
                if self._event_loop_monitor is not None:
                    monitor_task = self._event_loop_monitor.start()
                    monitor_task.add_done_callback(
                        self._on_critical_monitor_done,
                    )
            except BaseException:
                self._transition(RuntimeServiceState.FAILED, operation="start")
                raise
            self._transition(RuntimeServiceState.RUNNING, operation="start")

    async def stop(self) -> None:
        loop = asyncio.get_running_loop()
        self._bind_loop(loop, operation="stop")

        async with self._lifecycle_lock:
            if self._state is RuntimeServiceState.STOPPED:
                return
            self._transition(RuntimeServiceState.STOPPING, operation="stop")
            try:
                await self._on_stop()
                self._shutdown_report = await self._shutdown_coordinator.shutdown()
            except BaseException:
                self._transition(RuntimeServiceState.FAILED, operation="stop")
                raise
            self._transition(RuntimeServiceState.STOPPED, operation="stop")

    def _on_critical_monitor_done(self, task: asyncio.Task[None]) -> None:
        if task.cancelled():
            return
        try:
            failure = task.exception()
        except asyncio.CancelledError:
            return
        if failure is None:
            return

        self._shutdown_coordinator.request_shutdown(
            RuntimeShutdownReason.CRITICAL_TASK_FAILURE,
        )
        if self._state is RuntimeServiceState.RUNNING:
            self._transition(
                RuntimeServiceState.FAILED,
                operation="critical_task_failure",
            )

    async def _on_start(self) -> None:
        """Start runtime-owned resources in later P02 work packages."""

    async def _on_stop(self) -> None:
        """Stop runtime-owned resources in later P02 work packages."""

    def _transition(
        self,
        requested_state: RuntimeServiceState,
        *,
        operation: str,
    ) -> None:
        allowed_states = _RUNTIME_SERVICE_TRANSITIONS[self._state]
        if requested_state not in allowed_states:
            raise NsStateError(
                "RuntimeService lifecycle transition is invalid.",
                details={
                    "component": "runtime_service",
                    "operation": operation,
                    "current_state": self._state.value,
                    "requested_state": requested_state.value,
                    "allowed_target_states": [
                        state.value for state in allowed_states
                    ],
                },
            )
        self._state = requested_state

    def _bind_loop(
        self,
        loop: asyncio.AbstractEventLoop,
        *,
        operation: str,
    ) -> None:
        with self._loop_binding_lock:
            if self._loop is None:
                self._loop = loop
                return
            if self._loop is not loop:
                raise NsStateError(
                    "RuntimeService cannot be shared across event loops.",
                    details={
                        "component": "runtime_service",
                        "operation": operation,
                        "current_state": self._state.value,
                        "reason": "event_loop_mismatch",
                    },
                )


__all__ = [
    "RuntimeService",
    "RuntimeServiceState",
]
