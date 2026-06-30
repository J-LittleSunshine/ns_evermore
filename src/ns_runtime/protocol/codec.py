# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from abc import (
    ABC,
    abstractmethod,
)
from typing import Any

from ns_common.exceptions import NsRuntimeProtocolError
from ns_runtime.protocol.envelope import RuntimeEnvelope
from ns_runtime.protocol.validators import validate_envelope


class RuntimeCodec(ABC):
    name: str

    @abstractmethod
    def encode(self, envelope: RuntimeEnvelope) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def decode(self, data: bytes | str) -> RuntimeEnvelope:
        raise NotImplementedError


class JsonRuntimeCodec(RuntimeCodec):
    name = "json"

    def __init__(self, *, max_message_size_bytes: int | None = None) -> None:
        self.max_message_size_bytes = max_message_size_bytes

    def encode(self, envelope: RuntimeEnvelope) -> bytes:
        validate_envelope(envelope, max_message_size_bytes=self.max_message_size_bytes)

        try:
            raw = json.dumps(envelope.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as error:
            raise NsRuntimeProtocolError(
                "Failed to encode runtime envelope as JSON.",
                details={
                    "codec": self.name,
                    "error": str(error),
                },
            ) from error

        self._validate_size(raw)
        return raw

    def decode(self, data: bytes | str) -> RuntimeEnvelope:
        if isinstance(data, bytes):
            self._validate_size(data)
            text = data.decode("utf-8")
        elif isinstance(data, str):
            raw = data.encode("utf-8")
            self._validate_size(raw)
            text = data
        else:
            raise NsRuntimeProtocolError(
                "JSON codec input must be bytes or str.",
                details={
                    "codec": self.name,
                    "actual_type": type(data).__name__,
                },
            )

        try:
            decoded: Any = json.loads(text)
        except json.JSONDecodeError as error:
            raise NsRuntimeProtocolError(
                "Invalid runtime JSON message.",
                details={
                    "codec": self.name,
                    "line": error.lineno,
                    "column": error.colno,
                    "message": error.msg,
                },
            ) from error

        if not isinstance(decoded, dict):
            raise NsRuntimeProtocolError(
                "Runtime JSON message root must be an object.",
                details={
                    "codec": self.name,
                    "actual_type": type(decoded).__name__,
                },
            )

        try:
            envelope = RuntimeEnvelope.from_mapping(decoded)
        except (TypeError, ValueError) as error:
            raise NsRuntimeProtocolError(
                "Invalid runtime envelope structure.",
                details={
                    "codec": self.name,
                    "error": str(error),
                },
            ) from error

        validate_envelope(envelope, max_message_size_bytes=self.max_message_size_bytes)
        return envelope

    def _validate_size(self, raw: bytes) -> None:
        if self.max_message_size_bytes is None:
            return

        if len(raw) > self.max_message_size_bytes:
            raise NsRuntimeProtocolError(
                "Runtime message is too large.",
                code="RUNTIME_MESSAGE_TOO_LARGE",
                numeric_code=205010,
                details={
                    "codec": self.name,
                    "size_bytes": len(raw),
                    "max_message_size_bytes": self.max_message_size_bytes,
                },
            )
