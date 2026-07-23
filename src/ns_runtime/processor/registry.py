# -*- coding: utf-8 -*-
"""Instance-owned processor registry with version and feature conflicts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Mapping

from ns_common.exceptions import NsStateError, NsValidationError
from ns_runtime.protocol import ProtocolVersion

from .contracts import (
    MessageProcessorExecutionBoundary,
    ProcessorContext,
    ProcessorStage,
    freeze_feature_flags,
)


class PipelineProcessor(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def process(self, context: ProcessorContext, value: object) -> object:
        raise NotImplementedError


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessorRegistration:
    message_type: str
    stage: ProcessorStage
    minimum_version: ProtocolVersion
    maximum_version: ProtocolVersion
    feature_flag: str
    feature_enabled: bool
    processor: PipelineProcessor = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, str) or not self.message_type:
            _invalid("registration.message_type")
        if not isinstance(self.stage, ProcessorStage):
            _invalid("registration.stage")
        if not isinstance(self.minimum_version, ProtocolVersion):
            _invalid("registration.minimum_version")
        if not isinstance(self.maximum_version, ProtocolVersion):
            _invalid("registration.maximum_version")
        if (
            self.minimum_version.major != self.maximum_version.major
            or self.maximum_version < self.minimum_version
        ):
            _invalid("registration.version_range")
        if not isinstance(self.feature_flag, str) or not self.feature_flag:
            _invalid("registration.feature_flag")
        if type(self.feature_enabled) is not bool:
            _invalid("registration.feature_enabled")
        if not isinstance(self.processor, PipelineProcessor):
            _invalid("registration.processor")
        if (
            self.stage is ProcessorStage.MESSAGE_PROCESSOR
            and not isinstance(
                self.processor,
                MessageProcessorExecutionBoundary,
            )
        ):
            _invalid("registration.message_processor_boundary")

    def supports(self, version: ProtocolVersion) -> bool:
        return self.minimum_version <= version <= self.maximum_version


class ProcessorRegistry:
    """Mutable only during explicit composition; no module-level registry exists."""

    def __init__(self, registrations: Iterable[ProcessorRegistration] = ()) -> None:
        self._registrations: list[ProcessorRegistration] = []
        self._frozen = False
        try:
            values = tuple(registrations)
        except TypeError:
            _invalid("registrations")
        for registration in values:
            self.register(registration)

    @property
    def registrations(self) -> tuple[ProcessorRegistration, ...]:
        return tuple(self._registrations)

    @property
    def frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> None:
        self._frozen = True

    def register(self, registration: ProcessorRegistration) -> None:
        self.register_many((registration,))

    def register_many(
        self,
        registrations: Iterable[ProcessorRegistration],
    ) -> None:
        """Validate a registration batch before publishing any of it."""

        if self._frozen:
            raise NsStateError(
                "Processor registry is frozen.",
                details={"component": "processor_registry", "reason": "registry_frozen"},
            )
        try:
            values = tuple(registrations)
        except TypeError:
            _invalid("registrations")
        candidates = list(self._registrations)
        for registration in values:
            if not isinstance(registration, ProcessorRegistration):
                _invalid("registration")
            self._validate_registration(candidates, registration)
            candidates.append(registration)
        self._registrations = candidates

    @staticmethod
    def _validate_registration(
        existing_registrations: Iterable[ProcessorRegistration],
        registration: ProcessorRegistration,
    ) -> None:
        for existing in existing_registrations:
            if not _same_dimension(existing, registration):
                continue
            if (
                existing.minimum_version == registration.minimum_version
                and existing.maximum_version == registration.maximum_version
            ):
                raise NsValidationError(
                    "Duplicate processor registration is forbidden.",
                    details={
                        "component": "processor_registry",
                        "reason": "duplicate_registration",
                        "message_type": registration.message_type,
                        "stage": registration.stage.value,
                    },
                )
            if _overlaps(existing, registration):
                raise NsValidationError(
                    "Processor protocol version registrations conflict.",
                    details={
                        "component": "processor_registry",
                        "reason": "version_conflict",
                        "message_type": registration.message_type,
                        "stage": registration.stage.value,
                    },
                )

    def resolve(
        self,
        *,
        message_type: str,
        stage: ProcessorStage,
        protocol_version: ProtocolVersion,
        feature_flags: Mapping[str, bool],
    ) -> PipelineProcessor:
        if not isinstance(message_type, str) or not message_type:
            _invalid("resolve.message_type")
        if not isinstance(stage, ProcessorStage):
            _invalid("resolve.stage")
        if not isinstance(protocol_version, ProtocolVersion):
            _invalid("resolve.protocol_version")
        flags = freeze_feature_flags(feature_flags)
        matches = tuple(
            registration
            for registration in self._registrations
            if registration.message_type == message_type
            and registration.stage is stage
            and registration.supports(protocol_version)
            and flags.get(registration.feature_flag) is registration.feature_enabled
        )
        if len(matches) != 1:
            reason = "processor_not_registered" if not matches else "processor_resolution_conflict"
            raise NsStateError(
                "Processor resolution failed.",
                details={
                    "component": "processor_registry",
                    "reason": reason,
                    "message_type": message_type,
                    "stage": stage.value,
                },
            )
        return matches[0].processor


def _same_dimension(left: ProcessorRegistration, right: ProcessorRegistration) -> bool:
    return (
        left.message_type == right.message_type
        and left.stage is right.stage
        and left.feature_flag == right.feature_flag
        and left.feature_enabled is right.feature_enabled
    )


def _overlaps(left: ProcessorRegistration, right: ProcessorRegistration) -> bool:
    return not (
        left.maximum_version < right.minimum_version
        or right.maximum_version < left.minimum_version
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Processor registry value is invalid.",
        details={"component": "processor_registry", "field": field_name},
    )


__all__ = (
    "PipelineProcessor",
    "ProcessorRegistration",
    "ProcessorRegistry",
)
