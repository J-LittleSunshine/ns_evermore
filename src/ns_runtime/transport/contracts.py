# -*- coding: utf-8 -*-
"""Abstract transport ownership contracts without third-party library types."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    TransportCapabilities,
    TransportClose,
    TransportMessage,
    TransportSessionState,
)
from .identity import TransportDiagnosticSummary, TransportIdentity


class TransportSession(ABC):
    """One accepted transport session, initially limited to handshaking."""

    @property
    @abstractmethod
    def transport_type(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def capabilities(self) -> TransportCapabilities:
        raise NotImplementedError

    @property
    @abstractmethod
    def state(self) -> TransportSessionState:
        raise NotImplementedError

    @property
    @abstractmethod
    def close_info(self) -> TransportClose | None:
        raise NotImplementedError

    @property
    @abstractmethod
    def identity(self) -> TransportIdentity:
        raise NotImplementedError

    @property
    @abstractmethod
    def diagnostic_summary(self) -> TransportDiagnosticSummary:
        raise NotImplementedError

    @abstractmethod
    async def receive(self) -> TransportMessage:
        """Return exactly one complete text application message."""

    @abstractmethod
    async def send(self, text: str) -> None:
        """Send exactly one complete text application message."""

    @abstractmethod
    async def ping(self) -> None:
        """Perform the transport-native liveness round trip."""

    @abstractmethod
    async def close(self) -> TransportClose:
        """Idempotently close this session and all session-owned tasks."""


class TransportAdapter(ABC):
    """Listener/admission owner for one concrete transport implementation."""

    @property
    @abstractmethod
    def transport_type(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def capabilities(self) -> TransportCapabilities:
        raise NotImplementedError

    @property
    @abstractmethod
    def accepting(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def stop_admission_now(self) -> None:
        """Synchronously close the local admission gate."""

    @abstractmethod
    async def start(self) -> None:
        """Start the listener after startup preflight has succeeded."""

    @abstractmethod
    async def accept(self) -> TransportSession:
        """Return the next accepted session without exposing library objects."""

    @abstractmethod
    async def stop_admission(self) -> None:
        """Idempotently stop accepting new connections."""

    @abstractmethod
    async def drain(self) -> None:
        """Boundedly close existing sessions and their read/write tasks."""

    @abstractmethod
    async def close(self) -> None:
        """Idempotently release listener and adapter resources."""
