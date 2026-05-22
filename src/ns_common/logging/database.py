# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Protocol

from ns_common.logging.event import NsLogEventData


class DatabaseLogSink(Protocol):
    """Contract for structured database log sinks.

    Concrete implementations should live in backend/framework layers.
    ns_common only defines the protocol and must not depend on ORM frameworks.
    """

    def emit(self, event: NsLogEventData) -> None:
        ...


__all__ = ["DatabaseLogSink"]

