# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from ns_common.exceptions import NsRuntimeUnsupportedMessageTypeError
from ns_runtime._compat import StrEnum


class ProcessorStage(StrEnum):
    CONNECTION = "connection"
    DELIVERY = "delivery"
    STREAM = "stream"
    CONTROL = "control"
    CLUSTER = "cluster"
    TASK = "task"
    ERROR = "error"


class ReliabilityProfile(StrEnum):
    BEST_EFFORT = "best_effort"
    RELIABLE = "reliable"
    CONTROL_RELIABLE = "control_reliable"
    STREAM_RELIABLE = "stream_reliable"


@dataclass(frozen=True, slots=True)
class MessageTypeSchema:
    required_groups: frozenset[str]
    allowed_groups: frozenset[str]
    required_message_fields: frozenset[str]
    required_group_fields: dict[str, frozenset[str]]


@dataclass(frozen=True, slots=True)
class ProcessorRegistration:
    message_type: str
    stage: ProcessorStage
    processor_name: str
    required_capabilities: frozenset[str]
    schema: MessageTypeSchema
    reliability: ReliabilityProfile
    audit_event: str
    standard_error_type: str


class ProcessorRegistry:
    def __init__(self) -> None:
        self._registrations: dict[str, ProcessorRegistration] = {}

    def register(self, registration: ProcessorRegistration) -> None:
        if registration.message_type in self._registrations:
            raise ValueError(f"Duplicated runtime message type: {registration.message_type}")

        self._registrations[registration.message_type] = registration

    def get(self, message_type: str) -> ProcessorRegistration:
        registration = self._registrations.get(message_type)

        if registration is None:
            raise NsRuntimeUnsupportedMessageTypeError(
                details={
                    "message_type": message_type,
                },
            )

        return registration

    def values(self) -> tuple[ProcessorRegistration, ...]:
        return tuple(self._registrations.values())

    def contains(self, message_type: str) -> bool:
        return message_type in self._registrations
