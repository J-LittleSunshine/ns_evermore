# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Callable

from ns_common.protocol import RuntimePacket, RuntimePacketType

RuntimePacketHandler = Callable[[RuntimePacket], RuntimePacket | None]


class RuntimePacketRouter:
    def __init__(self) -> None:
        self._handlers: dict[RuntimePacketType, RuntimePacketHandler] = {}

    def register_handler(self, packet_type: RuntimePacketType, handler: RuntimePacketHandler) -> None:
        self._handlers[packet_type] = handler

    def unregister_handler(self, packet_type: RuntimePacketType) -> None:
        self._handlers.pop(packet_type, None)

    def route(self, packet: RuntimePacket) -> RuntimePacket | None:
        handler = self._handlers.get(packet.packet_type)
        if handler is None:
            return None
        return handler(packet)

