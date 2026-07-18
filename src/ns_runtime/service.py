# -*- coding: utf-8 -*-
"""Runtime process lifecycle service."""

from __future__ import annotations

import asyncio
from enum import Enum
from threading import Lock
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsStateError


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

    Lifecycle operations are serialized on the first event loop that uses the
    service. ``FAILED`` blocks restart but remains eligible for explicit cleanup
    through ``stop()``; ``STOPPED`` makes later ``stop()`` calls idempotent.
    Subclasses may implement the protected hooks while retaining these state
    transition and failure semantics.
    """

    def __init__(self) -> None:
        self._state = RuntimeServiceState.CREATED
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_binding_lock = Lock()
        self._lifecycle_lock = asyncio.Lock()

    @property
    def state(self) -> RuntimeServiceState:
        return self._state

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        self._bind_loop(loop, operation="start")

        async with self._lifecycle_lock:
            self._transition(RuntimeServiceState.STARTING, operation="start")
            try:
                await self._on_start()
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
            except BaseException:
                self._transition(RuntimeServiceState.FAILED, operation="stop")
                raise
            self._transition(RuntimeServiceState.STOPPED, operation="stop")

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
