# -*- coding: utf-8 -*-
"""Cold-import-safe typed hook between RSD-1 and P04 transport ownership."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TransportLifecycleOwner(Protocol):
    def stop_admission_now(self) -> None:
        """Synchronously close the local admission gate."""

    async def stop_admission(self) -> None:
        """Idempotently stop all listener admission."""

    async def drain(self) -> None:
        """Boundedly close existing sessions and I/O tasks."""

    async def close(self) -> None:
        """Idempotently close all adapters and listeners."""


__all__ = ("TransportLifecycleOwner",)

