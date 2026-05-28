# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from ns_common.protocol.packets.packet import RuntimePacket


class RuntimePacketCodec:
    def encode(self, packet: RuntimePacket) -> bytes:
        body = json.dumps(packet.to_dict(), ensure_ascii=False, separators=(",", ":"))
        return body.encode("utf-8")

    def decode(self, data: bytes | str) -> RuntimePacket:
        raw_text = data.decode("utf-8") if isinstance(data, bytes) else data
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid packet json: {exc}") from exc

        if not isinstance(payload, dict):
            raise ValueError("packet json must decode to object")

        return RuntimePacket.from_dict(payload)

