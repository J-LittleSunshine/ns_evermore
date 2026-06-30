# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import re
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    Awaitable,
    Callable,
    Mapping,
)

from ns_common.exceptions import (
    NsRuntimePluginError,
    NsRuntimeRoutingError,
)
from ns_common.logger import get_ns_logger
from ns_common.runtime_config import NsRuntimeConfig
from ns_runtime.protocol import (
    NsRuntimeEnvelope,
    NsRuntimePeer,
    current_epoch_ms,
)

_PROCESSOR_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.:-]{0,127}$")


@dataclass(slots=True, kw_only=True)
class NsRuntimeProcessorContext:
    runtime_config: NsRuntimeConfig
    connection_id: str
    peer: NsRuntimePeer
    principal: dict[str, Any]
    request: NsRuntimeEnvelope
    connection_summary: dict[str, Any]

    @property
    def payload(self) -> dict[str, Any]:
        return dict(self.request.payload or {})

    @property
    def trace_id(self) -> str | None:
        return self.request.trace_id


@dataclass(slots=True, kw_only=True)
class NsRuntimeProcessorResult:
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: "NsRuntimeProcessorResult | Mapping[str, Any]") -> "NsRuntimeProcessorResult":
        if isinstance(value, NsRuntimeProcessorResult):
            return value

        if isinstance(value, Mapping):
            return cls(
                payload=dict(value),
            )

        raise NsRuntimePluginError(
            "Runtime processor result must be NsRuntimeProcessorResult or JSON object.",
            details={
                "actual_type": type(value).__name__,
            },
        )


NsRuntimeProcessorReturn = NsRuntimeProcessorResult | Mapping[str, Any]
NsRuntimeProcessorCallable = Callable[[NsRuntimeProcessorContext], Awaitable[NsRuntimeProcessorReturn]]


@dataclass(slots=True, kw_only=True)
class NsRuntimeRegisteredProcessor:
    processor_name: str
    processor: NsRuntimeProcessorCallable
    max_concurrency: int
    metadata: dict[str, Any] = field(default_factory=dict)
    semaphore: asyncio.Semaphore = field(repr=False)

    def to_summary(self) -> dict[str, Any]:
        return {
            "processor_name": self.processor_name,
            "max_concurrency": self.max_concurrency,
            "metadata": dict(self.metadata),
        }


class NsRuntimeLocalProcessorRegistry:
    def __init__(self, *, default_max_concurrency: int = 16) -> None:
        self.default_max_concurrency = _normalize_positive_int(
            default_max_concurrency,
            "default_max_concurrency",
        )
        self.logger = get_ns_logger("ns_runtime.processor_registry")
        self._processors: dict[str, NsRuntimeRegisteredProcessor] = {}

    def register(
            self,
            processor_name: str,
            processor: NsRuntimeProcessorCallable,
            *,
            max_concurrency: int | None = None,
            metadata: Mapping[str, Any] | None = None,
            replace: bool = False,
    ) -> None:
        normalized_name = _normalize_processor_name(processor_name)
        concurrency = _normalize_positive_int(
            max_concurrency if max_concurrency is not None else self.default_max_concurrency,
            f"processor.{normalized_name}.max_concurrency",
        )

        if not callable(processor):
            raise NsRuntimePluginError(
                "Runtime processor must be callable.",
                details={
                    "processor_name": normalized_name,
                    "actual_type": type(processor).__name__,
                },
            )

        if normalized_name in self._processors and not replace:
            raise NsRuntimePluginError(
                "Runtime processor is already registered.",
                details={
                    "processor_name": normalized_name,
                },
            )

        self._processors[normalized_name] = NsRuntimeRegisteredProcessor(
            processor_name=normalized_name,
            processor=processor,
            max_concurrency=concurrency,
            metadata=dict(metadata or {}),
            semaphore=asyncio.Semaphore(concurrency),
        )

        self.logger.info(
            "Runtime processor registered.",
            extra={
                "processor_name": normalized_name,
                "max_concurrency": concurrency,
            },
        )

    def unregister(self, processor_name: str) -> bool:
        normalized_name = _normalize_processor_name(processor_name)
        removed = self._processors.pop(normalized_name, None)

        if removed is not None:
            self.logger.info(
                "Runtime processor unregistered.",
                extra={
                    "processor_name": normalized_name,
                },
            )
            return True

        return False

    def get(self, processor_name: str) -> NsRuntimeRegisteredProcessor | None:
        normalized_name = _normalize_processor_name(processor_name)
        return self._processors.get(normalized_name)

    def has(self, processor_name: str) -> bool:
        return self.get(processor_name) is not None

    def list_processors(self) -> list[dict[str, Any]]:
        return [
            processor.to_summary()
            for processor in sorted(
                self._processors.values(),
                key=lambda item: item.processor_name,
            )
        ]

    async def dispatch(self, context: NsRuntimeProcessorContext) -> NsRuntimeProcessorResult:
        processor_name = self.resolve_processor_name(context.request)
        registered_processor = self._processors.get(processor_name)

        if registered_processor is None:
            raise NsRuntimeRoutingError(
                "Runtime processor is not registered.",
                details={
                    "processor_name": processor_name,
                    "available_processors": sorted(self._processors.keys()),
                    "message_id": context.request.message_id,
                    "message_type": context.request.message_type,
                },
            )

        async with registered_processor.semaphore:
            try:
                result = await registered_processor.processor(context)
            except Exception as exc:
                raise NsRuntimePluginError(
                    "Runtime processor execution failed.",
                    details={
                        "processor_name": processor_name,
                        "message_id": context.request.message_id,
                        "trace_id": context.request.trace_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                ) from exc

        return NsRuntimeProcessorResult.from_value(result)

    @staticmethod
    def resolve_processor_name(envelope: NsRuntimeEnvelope) -> str:
        payload = dict(envelope.payload or {})
        metadata = dict(envelope.metadata or {})

        raw_name = (
                payload.get("processor")
                or payload.get("processor_name")
                or metadata.get("processor")
                or metadata.get("processor_name")
        )

        return _normalize_processor_name(raw_name)


async def runtime_echo_processor(context: NsRuntimeProcessorContext) -> NsRuntimeProcessorResult:
    return NsRuntimeProcessorResult(
        payload={
            "processor": "runtime.echo",
            "message_id": context.request.message_id,
            "trace_id": context.request.trace_id,
            "connection_id": context.connection_id,
            "server_time_epoch_ms": current_epoch_ms(),
            "echo": context.payload,
            "connection": dict(context.connection_summary),
            "principal": dict(context.principal),
        },
        metadata={
            "processor": "runtime.echo",
        },
    )


def build_default_processor_registry(runtime_config: NsRuntimeConfig) -> NsRuntimeLocalProcessorRegistry:
    registry = NsRuntimeLocalProcessorRegistry(
        default_max_concurrency=runtime_config.default_processor_max_concurrency,
    )

    registry.register(
        "runtime.echo",
        runtime_echo_processor,
        metadata={
            "builtin": True,
            "description": "Echo runtime processor for local protocol smoke tests.",
        },
    )

    registry.register(
        "echo",
        runtime_echo_processor,
        metadata={
            "builtin": True,
            "alias_for": "runtime.echo",
            "description": "Alias of runtime.echo.",
        },
    )

    return registry


def _normalize_processor_name(value: Any) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise NsRuntimeRoutingError(
            "processor is required.",
            details={
                "field": "processor",
            },
        )

    if _PROCESSOR_NAME_PATTERN.fullmatch(normalized) is None:
        raise NsRuntimeRoutingError(
            "processor name is invalid.",
            details={
                "processor_name": normalized,
                "allowed_pattern": _PROCESSOR_NAME_PATTERN.pattern,
            },
        )

    return normalized


def _normalize_positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise NsRuntimePluginError(
            f"{field_name} must be a positive integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise NsRuntimePluginError(
            f"{field_name} must be a positive integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        ) from exc

    if normalized <= 0:
        raise NsRuntimePluginError(
            f"{field_name} must be a positive integer.",
            details={
                "field": field_name,
                "value": normalized,
            },
        )

    return normalized
