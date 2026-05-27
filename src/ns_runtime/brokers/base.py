# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod

from ns_runtime.packets.packet import RuntimePacket


class RuntimeBroker(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def publish(self, topic: str, packet: RuntimePacket) -> None:
        raise NotImplementedError

    @abstractmethod
    def poll(self, topic: str, max_count: int = 1) -> tuple[RuntimePacket, ...]:
        raise NotImplementedError

    def _validate_topic(self, topic: str) -> str:
        text = topic.strip()
        if not text:
            raise ValueError("topic must be non-empty string")
        return text

    def _validate_max_count(self, max_count: int) -> int:
        if max_count <= 0:
            raise ValueError("max_count must be greater than 0")
        return max_count

