# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import deque
from threading import RLock

from ns_runtime.brokers.base import RuntimeBroker
from ns_runtime.packets.packet import RuntimePacket


class MemoryBroker(RuntimeBroker):
    def __init__(self) -> None:
        self._lock = RLock()
        self._queues: dict[str, deque[RuntimePacket]] = {}
        self._running = False

    def start(self) -> None:
        with self._lock:
            self._running = True

    def stop(self) -> None:
        with self._lock:
            self._running = False

    def publish(self, topic: str, packet: RuntimePacket) -> None:
        normalized_topic = self._validate_topic(topic)
        with self._lock:
            self._ensure_running()
            queue = self._queues.setdefault(normalized_topic, deque())
            queue.append(packet)

    def poll(self, topic: str, max_count: int = 1) -> tuple[RuntimePacket, ...]:
        normalized_topic = self._validate_topic(topic)
        normalized_max_count = self._validate_max_count(max_count)
        with self._lock:
            self._ensure_running()
            queue = self._queues.get(normalized_topic)
            if queue is None or not queue:
                return ()

            packets: list[RuntimePacket] = []
            for _ in range(normalized_max_count):
                if not queue:
                    break
                packets.append(queue.popleft())
            return tuple(packets)

    def _ensure_running(self) -> None:
        # 关键保护：内存 broker 在未启动时拒绝读写，避免调用方误判运行状态。
        if not self._running:
            raise RuntimeError("broker is not started")

