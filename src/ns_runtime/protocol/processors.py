# -*- coding: utf-8 -*-
"""Fail-closed processor used by every registered but unavailable feature."""

from __future__ import annotations

import logging
from dataclasses import replace
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeFeatureDisabledError,
)

from .error_envelope import ErrorEnvelopeBuilder, ErrorEnvelopeContext
from .models import Envelope
from .registry import (
    BUILTIN_MESSAGE_REGISTRY,
    MessageTypeContract,
    MessageTypeRegistry,
)


class FeatureDisabledProcessor:
    """Return one stable error and perform no message-specific action."""

    def __init__(
        self,
        *,
        contract: MessageTypeContract,
        error_builder: ErrorEnvelopeBuilder,
        logger: logging.Logger,
    ) -> None:
        if not isinstance(contract, MessageTypeContract):
            raise TypeError("contract must be MessageTypeContract")
        if contract.feature_enabled:
            raise ValueError("enabled message types cannot use FeatureDisabledProcessor")
        if not isinstance(error_builder, ErrorEnvelopeBuilder):
            raise TypeError("error_builder must be ErrorEnvelopeBuilder")
        if not isinstance(logger, logging.Logger):
            raise TypeError("logger must be logging.Logger")
        self._contract = contract
        self._error_builder = error_builder
        self._logger = logger

    @property
    def contract(self) -> MessageTypeContract:
        return self._contract

    async def process(
        self,
        envelope: Envelope,
        *,
        error_context: ErrorEnvelopeContext,
    ) -> Envelope:
        if not isinstance(envelope, Envelope):
            raise TypeError("envelope must be Envelope")
        if envelope.message.type != self._contract.message_type:
            raise NsRuntimeEnvelopeSchemaError(
                "Feature-disabled processor contract mismatch.",
                details={
                    "group": "message",
                    "field": "type",
                    "reason": "processor_contract_mismatch",
                },
            )
        if not isinstance(error_context, ErrorEnvelopeContext):
            raise TypeError("error_context must be ErrorEnvelopeContext")

        try:
            self._logger.error(
                "Runtime message feature is disabled.",
                extra={
                    "event": "runtime_message_feature_disabled",
                    "component": "feature_disabled_processor",
                    "message_type": self._contract.message_type,
                    "processor_key": self._contract.processor_key,
                    "feature_flag": self._contract.feature_flag,
                    "error_code": NsRuntimeFeatureDisabledError.code,
                    "reason": "phase_not_implemented",
                },
            )
        except Exception:
            # P08 strong audit is not present yet. A best-effort logger failure
            # must never convert this rejection into a feature execution path.
            pass

        response_context = replace(
            error_context,
            referenced_message_id=envelope.message.message_id,
            referenced_delivery_id=(
                envelope.delivery.delivery_id
                if envelope.delivery is not None
                else None
            ),
        )
        return self._error_builder.build(
            NsRuntimeFeatureDisabledError(),
            context=response_context,
        )


def build_feature_disabled_processors(
    *,
    error_builder: ErrorEnvelopeBuilder,
    logger: logging.Logger,
    registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
) -> Mapping[str, FeatureDisabledProcessor]:
    if not isinstance(registry, MessageTypeRegistry):
        raise TypeError("registry must be MessageTypeRegistry")
    processors = {
        contract.processor_key: FeatureDisabledProcessor(
            contract=contract,
            error_builder=error_builder,
            logger=logger,
        )
        for contract in registry.contracts
        if not contract.feature_enabled
    }
    if len(processors) != sum(
        not contract.feature_enabled for contract in registry.contracts
    ):
        raise ValueError("disabled processor keys must be unique")
    return MappingProxyType(processors)


__all__ = (
    "FeatureDisabledProcessor",
    "build_feature_disabled_processors",
)
