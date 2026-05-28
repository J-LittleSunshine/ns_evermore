# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ns_common.protocol import RuntimePacket


class ExecutorIpcMessageType(str, Enum):
    PACKET = "PACKET"
    STOP = "STOP"
    LOG = "LOG"


@dataclass(frozen=True)
class ExecutorIpcMessage:
    message_id: str
    message_type: ExecutorIpcMessageType
    packet: dict[str, Any] | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        message_id = str(self.message_id).strip()
        if not message_id:
            raise ValueError("message_id must be non-empty")
        if self.packet is not None and not isinstance(self.packet, dict):
            raise ValueError("packet must be dict or None")

        object.__setattr__(self, "message_id", message_id)
        object.__setattr__(self, "packet", None if self.packet is None else dict(self.packet))
        object.__setattr__(self, "payload", dict(self.payload))

    @classmethod
    def from_packet(cls, packet: RuntimePacket) -> ExecutorIpcMessage:
        # IPC 不直接传 RuntimePacket 对象，而传 dict，降低跨进程序列化和耦合风险。
        return cls(
            message_id=uuid4().hex,
            message_type=ExecutorIpcMessageType.PACKET,
            packet=packet.to_dict(),
            payload={},
        )

    @classmethod
    def stop(cls) -> ExecutorIpcMessage:
        return cls(
            message_id=uuid4().hex,
            message_type=ExecutorIpcMessageType.STOP,
            packet=None,
            payload={},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "packet": None if self.packet is None else dict(self.packet),
            "payload": dict(self.payload),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExecutorIpcMessage:
        message_id = str(data.get("message_id") or "").strip()
        if not message_id:
            raise ValueError("message_id must be non-empty")

        message_type = ExecutorIpcMessageType(str(data.get("message_type") or "").strip())

        packet_raw = data.get("packet")
        if packet_raw is None:
            packet: dict[str, Any] | None = None
        elif isinstance(packet_raw, Mapping):
            packet = dict(packet_raw)
        else:
            raise ValueError("packet must be mapping or None")

        payload_raw = data.get("payload", {})
        if not isinstance(payload_raw, Mapping):
            raise ValueError("payload must be mapping")

        created_at_raw = data.get("created_at")
        if not isinstance(created_at_raw, str) or not created_at_raw.strip():
            raise ValueError("created_at must be ISO 8601 string")
        created_at_text = created_at_raw.strip().replace("Z", "+00:00")
        try:
            created_at = datetime.fromisoformat(created_at_text)
        except ValueError as exc:
            raise ValueError(f"invalid created_at: {created_at_raw}") from exc

        return cls(
            message_id=message_id,
            message_type=message_type,
            packet=packet,
            payload=dict(payload_raw),
            created_at=created_at,
        )

