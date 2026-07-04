# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.logger import get_ns_logger
from ns_runtime.models import (
    ProcessorResponse,
    RuntimeSessionContext
)
from ns_runtime.processors import (
    ProcessorPipeline,
    ProcessorRegistry,
    build_default_processor_pipeline,
    build_default_processor_registry,
)
from ns_runtime.protocol import EnvelopeCodec

if TYPE_CHECKING:
    pass


class RuntimeService:
    def __init__(self, *, runtime_id: str, codec: EnvelopeCodec, registry: ProcessorRegistry, pipeline: ProcessorPipeline, config_version: str = "local:1", policy_version: str = "local:1") -> None:
        self._runtime_id = runtime_id
        self._codec = codec
        self._registry = registry
        self._pipeline = pipeline
        self._config_version = config_version
        self._policy_version = policy_version
        self._logger = get_ns_logger("ns_runtime", True)

    @classmethod
    def build_default(cls, *, runtime_id: str) -> "RuntimeService":
        codec = EnvelopeCodec(runtime_id=runtime_id)
        registry = build_default_processor_registry(codec)
        pipeline = build_default_processor_pipeline(codec, registry)

        return cls(
            runtime_id=runtime_id,
            codec=codec,
            registry=registry,
            pipeline=pipeline,
        )

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    def list_message_type_specs(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "message_type": spec.message_type,
                "category": spec.category,
                "required_groups": list(spec.required_groups),
                "required_capabilities": list(spec.required_capabilities),
                "reliability": spec.reliability,
                "implemented": spec.implemented,
            }
            for spec in self._registry.list_specs()
        )

    async def process_frame(self, frame_text: str, session: RuntimeSessionContext) -> ProcessorResponse:
        try:
            envelope = self._codec.parse_inbound(frame_text, session)
            return await self._pipeline.process(
                envelope,
                session,
                config_version=self._config_version,
                policy_version=self._policy_version,
            )
        except Exception as exc:  # noqa
            self._logger.warning(
                "runtime frame rejected",
                exc_info=True,
                extra={
                    "runtime_id": self._runtime_id,
                    "connection_id": session.connection_id,
                    "tenant_id": session.tenant_id,
                    "exception_class": exc.__class__.__name__,
                },
            )
            return ProcessorResponse.reject(self._codec.build_error_envelope(exc, session=session), should_close=True)

    def process_frame_sync(self, frame_text: str, session: RuntimeSessionContext) -> ProcessorResponse:
        return asyncio.run(self.process_frame(frame_text, session))

    async def start(self) -> None:
        self._logger.info(
            "runtime service initialized",
            extra={
                "runtime_id": self._runtime_id,
                "message_type_count": len(self._registry.list_specs()),
                "config_version": self._config_version,
                "policy_version": self._policy_version,
            },
        )
