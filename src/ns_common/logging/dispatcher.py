# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Iterable

from ns_common.logging.event import NsLogEventData
from ns_common.logging.sinks import NsLogSink, NullLogSink


class NsLogDispatcher:
    def __init__(self, sinks: Iterable[NsLogSink] | None = None):
        self._sinks: list[NsLogSink] = list(sinks or [])
        if not self._sinks:
            self._sinks = [NullLogSink()]

    def add_sink(self, sink: NsLogSink) -> None:
        self._sinks.append(sink)

    def emit(self, event: NsLogEventData) -> None:
        for sink in list(self._sinks):
            try:
                sink.emit(event)
            except Exception:  # noqa
                # A single sink failure must not block dispatch to other sinks.
                continue


__all__ = ["NsLogDispatcher"]

