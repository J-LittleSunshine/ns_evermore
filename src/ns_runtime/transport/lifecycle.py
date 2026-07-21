# -*- coding: utf-8 -*-
"""Composition of adapters into the existing runtime lifecycle ownership."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from enum import Enum
from typing import Callable

from ns_common.exceptions import (
    NsRuntimeTransportError,
    NsStateError,
    NsValidationError,
)
from ns_runtime.context import RuntimeContext
from ns_runtime.event_loop_observability import RuntimeEventLoopMonitor
from ns_runtime.service import RuntimeService
from ns_runtime.shutdown import RuntimeShutdownCoordinator

from .contracts import TransportAdapter


class TransportManagerState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"


class TransportManager:
    """One explicit owner for all configured adapter resources."""

    def __init__(self, adapters: Iterable[TransportAdapter]) -> None:
        try:
            items = tuple(adapters)
        except (TypeError, ValueError):
            _invalid("adapters")
        if not items or any(not isinstance(item, TransportAdapter) for item in items):
            _invalid("adapters")
        names = tuple(item.transport_type for item in items)
        if len(names) != len(set(names)):
            _invalid("adapters")
        self._adapters = items
        self._state = TransportManagerState.CREATED
        self._lifecycle_lock = asyncio.Lock()

    @property
    def adapters(self) -> tuple[TransportAdapter, ...]:
        return self._adapters

    @property
    def state(self) -> TransportManagerState:
        return self._state

    async def start(self) -> None:
        async with self._lifecycle_lock:
            if self._state is not TransportManagerState.CREATED:
                raise NsStateError(
                    "Transport manager cannot start from its current state.",
                    details={
                        "component": "transport_manager",
                        "operation": "start",
                        "state": self._state.value,
                    },
                )
            started: list[TransportAdapter] = []
            try:
                for adapter in self._adapters:
                    await adapter.start()
                    started.append(adapter)
            except BaseException:
                self._state = TransportManagerState.FAILED
                for adapter in reversed(started):
                    try:
                        await adapter.close()
                    except Exception:
                        pass
                raise
            self._state = TransportManagerState.RUNNING

    def stop_admission_now(self) -> None:
        failed = False
        for adapter in self._adapters:
            try:
                adapter.stop_admission_now()
            except Exception:
                failed = True
        if failed:
            raise _lifecycle_error("stop_admission")

    async def stop_admission(self) -> None:
        await self._run_all("stop_admission")

    async def drain(self) -> None:
        if self._state is not TransportManagerState.CLOSED:
            self._state = TransportManagerState.CLOSING
        await self._run_all("drain")

    async def close(self) -> None:
        async with self._lifecycle_lock:
            if self._state is TransportManagerState.CLOSED:
                return
            self._state = TransportManagerState.CLOSING
            try:
                await self._run_all("close", reverse=True)
            except BaseException:
                self._state = TransportManagerState.FAILED
                raise
            self._state = TransportManagerState.CLOSED

    async def _run_all(self, operation: str, *, reverse: bool = False) -> None:
        adapters = reversed(self._adapters) if reverse else iter(self._adapters)
        failed = False
        for adapter in adapters:
            try:
                await getattr(adapter, operation)()
            except Exception:
                failed = True
        if failed:
            raise _lifecycle_error(operation)


class TransportRuntimeService(RuntimeService):
    """RuntimeService specialization that starts the P04 transport manager."""

    def __init__(
        self,
        *,
        context: RuntimeContext,
        transport_manager: TransportManager,
        logger_close: Callable[[], None] | None = None,
        event_loop_monitor: RuntimeEventLoopMonitor | None = None,
    ) -> None:
        if not isinstance(transport_manager, TransportManager):
            _invalid("transport_manager")
        self._transport_manager = transport_manager
        coordinator = RuntimeShutdownCoordinator(
            context=context,
            logger_close=logger_close,
            transport_owner=transport_manager,
        )
        super().__init__(
            context=context,
            shutdown_coordinator=coordinator,
            event_loop_monitor=event_loop_monitor,
        )

    @property
    def transport_manager(self) -> TransportManager:
        return self._transport_manager

    async def _on_start(self) -> None:
        await self._transport_manager.start()


def _lifecycle_error(operation: str) -> NsRuntimeTransportError:
    return NsRuntimeTransportError(
        "Runtime transport lifecycle operation failed.",
        details={
            "component": "transport_manager",
            "operation": operation,
            "reason": "adapter_resource_failed",
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Transport lifecycle value is invalid.",
        details={"component": "transport_manager", "field": field_name},
    )


__all__ = (
    "TransportManager",
    "TransportManagerState",
    "TransportRuntimeService",
)

