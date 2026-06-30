# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_runtime.protocol import (
    NsRuntimeClientType,
    NsRuntimeEnvelope,
    NsRuntimeJsonCodec,
    NsRuntimeMessageType,
    NsRuntimePeer,
    RUNTIME_PROTOCOL_NAME,
    RUNTIME_PROTOCOL_VERSION,
    current_epoch_ms,
    new_runtime_message_id
)

if TYPE_CHECKING:
    pass

__all__ = [
    "RUNTIME_PROTOCOL_NAME",
    "RUNTIME_PROTOCOL_VERSION",
    "NsRuntimeClientType",
    "NsRuntimeEnvelope",
    "NsRuntimeJsonCodec",
    "NsRuntimeMessageType",
    "NsRuntimePeer",
    "current_epoch_ms",
    "new_runtime_message_id",
]
