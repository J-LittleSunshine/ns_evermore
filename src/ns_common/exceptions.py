# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    Mapping,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    pass


class NsEvermoreError(Exception):
    code: str = "NS_ERROR"
    numeric_code: int = 100000
    default_message: str = "NsEvermore error."

    def __init__(self, message: str | None = None, *, code: str | None = None, numeric_code: int | None = None, details: Mapping[str, Any] | None = None) -> None:
        self.message: str = message or self.default_message
        self.code: str = code or self.code
        self.numeric_code: int = numeric_code or self.numeric_code
        self.details: dict[str, Any] = dict(details or {})

        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "numeric_code": self.numeric_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        if not self.details:
            return f"[{self.code}/{self.numeric_code}] {self.message}"

        return f"[{self.code}/{self.numeric_code}] {self.message} details={self.details}"


class NsConfigError(NsEvermoreError):
    code = "NS_CONFIG_ERROR"
    numeric_code = 100100
    default_message = "Invalid ns_evermore configuration."


class NsValidationError(NsEvermoreError):
    code = "NS_VALIDATION_ERROR"
    numeric_code = 100200
    default_message = "Validation failed."


class NsRuntimeError(NsEvermoreError):
    code = "NS_RUNTIME_ERROR"
    numeric_code = 100300
    default_message = "NsEvermore runtime error."


class NsDependencyError(NsEvermoreError):
    code = "NS_DEPENDENCY_ERROR"
    numeric_code = 100400
    default_message = "NsEvermore dependency error."


class NsStateError(NsEvermoreError):
    code = "NS_STATE_ERROR"
    numeric_code = 100500
    default_message = "Invalid ns_evermore internal state."


class NsRuntimeProtocolError(NsEvermoreError):
    code = "RUNTIME_PROTOCOL_ERROR"
    numeric_code = 201000
    default_message = "Runtime protocol error."


class NsRuntimeCodecError(NsEvermoreError):
    code = "RUNTIME_CODEC_ERROR"
    numeric_code = 201100
    default_message = "Runtime codec error."


class NsRuntimeAuthError(NsEvermoreError):
    code = "RUNTIME_AUTH_ERROR"
    numeric_code = 202000
    default_message = "Runtime authentication or authorization error."


class NsRuntimeRoutingError(NsEvermoreError):
    code = "RUNTIME_ROUTING_ERROR"
    numeric_code = 203000
    default_message = "Runtime routing error."


class NsRuntimeNodeError(NsEvermoreError):
    code = "RUNTIME_NODE_ERROR"
    numeric_code = 204000
    default_message = "Runtime node or connection error."


class NsRuntimeMessageError(NsEvermoreError):
    code = "RUNTIME_MESSAGE_ERROR"
    numeric_code = 205000
    default_message = "Runtime message lifecycle error."


class NsRuntimeStateStoreError(NsEvermoreError):
    code = "RUNTIME_STATE_STORE_ERROR"
    numeric_code = 206000
    default_message = "Runtime state store error."


class NsRuntimeMessageStoreError(NsEvermoreError):
    code = "RUNTIME_MESSAGE_STORE_ERROR"
    numeric_code = 207000
    default_message = "Runtime message store error."


class NsRuntimePluginError(NsEvermoreError):
    code = "RUNTIME_PLUGIN_ERROR"
    numeric_code = 208000
    default_message = "Runtime plugin error."


class NsRuntimeAdminError(NsEvermoreError):
    code = "RUNTIME_ADMIN_ERROR"
    numeric_code = 209000
    default_message = "Runtime admin API error."


class NsHttpClientError(NsEvermoreError):
    code = "NS_HTTP_CLIENT_ERROR"
    numeric_code = 100600
    default_message = "NsEvermore HTTP client error."
