# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass

from ns_common.exceptions import (
    NsRuntimeRoleAdmissionError,
)
from ns_runtime.cluster import (
    RuntimeClusterSnapshot,
)
from ns_runtime.models import (
    RuntimeComponentType,
)

_INTERNAL_COMPONENT_TYPES: frozenset[str] = (
    frozenset(
        {
            "runtime",
            "sub_node",
            "management",
        }
    )
)

_CONTINUATION_MESSAGE_TYPES: frozenset[str] = (
    frozenset(
        {
            "connection.heartbeat",
            "connection.drain",
            "delivery.ack",
            "delivery.nack",
            "delivery.defer",
        }
    )
)

_CONTINUATION_MESSAGE_PREFIXES: tuple[
    str,
    ...,
] = (
    "runtime.control.",
    "cluster.event.",
)

_RESTRICTED_ROLES: frozenset[str] = (
    frozenset(
        {
            "standby_master",
            "transitioning",
            "draining",
        }
    )
)

_RESTRICTED_STATES: frozenset[str] = (
    frozenset(
        {
            "transitioning",
            "draining",
        }
    )
)


@dataclass(
    slots=True,
    frozen=True,
    kw_only=True,
)
class RuntimeRoleAdmissionDecision:
    accepted: bool
    reason_code: str = ""
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.accepted, bool):
            raise ValueError(
                "accepted must be bool."
            )

        if self.accepted:
            if self.reason_code or self.reason:
                raise ValueError(
                    "Accepted role admission decision "
                    "must not contain rejection reason."
                )
            return

        if (
                not isinstance(
                    self.reason_code,
                    str,
                )
                or not self.reason_code.strip()
        ):
            raise ValueError(
                "Rejected role admission decision "
                "must contain reason_code."
            )

        if (
                not isinstance(self.reason, str)
                or not self.reason.strip()
        ):
            raise ValueError(
                "Rejected role admission decision "
                "must contain reason."
            )

    @classmethod
    def accept(
            cls,
    ) -> "RuntimeRoleAdmissionDecision":
        return cls(
            accepted=True
        )

    @classmethod
    def reject(
            cls,
            *,
            reason: str,
    ) -> "RuntimeRoleAdmissionDecision":
        return cls(
            accepted=False,
            reason_code=(
                NsRuntimeRoleAdmissionError.code
            ),
            reason=reason,
        )


class RuntimeRoleAdmissionPolicy(ABC):
    @abstractmethod
    def evaluate_connection(
            self,
            *,
            snapshot: RuntimeClusterSnapshot,
            component_type: RuntimeComponentType,
            active_sub_node_count: int,
    ) -> RuntimeRoleAdmissionDecision:
        raise NotImplementedError

    @abstractmethod
    def evaluate_message(
            self,
            *,
            snapshot: RuntimeClusterSnapshot,
            component_type: RuntimeComponentType,
            message_type: str,
            message_category: str,
    ) -> RuntimeRoleAdmissionDecision:
        raise NotImplementedError


class LocalRuntimeRoleAdmissionPolicy(
    RuntimeRoleAdmissionPolicy
):
    def evaluate_connection(
            self,
            *,
            snapshot: RuntimeClusterSnapshot,
            component_type: RuntimeComponentType,
            active_sub_node_count: int,
    ) -> RuntimeRoleAdmissionDecision:
        self._validate_active_sub_node_count(
            active_sub_node_count
        )

        if (
                snapshot.role in {
            "singleton",
            "sub_node",
        }
                and snapshot.state == "ready"
        ):
            return (
                RuntimeRoleAdmissionDecision
                .accept()
            )

        if (
                snapshot.role == "active_master"
                and snapshot.state == "ready"
        ):
            if (
                    active_sub_node_count == 0
                    or self._is_internal_component(
                component_type
            )
            ):
                return (
                    RuntimeRoleAdmissionDecision
                    .accept()
                )

            return (
                RuntimeRoleAdmissionDecision
                .reject(
                    reason=(
                        "Active master delegates "
                        "ordinary connections while "
                        "sub-nodes are available."
                    )
                )
            )

        if (
                snapshot.role
                in _RESTRICTED_ROLES
                or snapshot.state
                in _RESTRICTED_STATES
        ):
            if self._is_internal_component(
                    component_type
            ):
                return (
                    RuntimeRoleAdmissionDecision
                    .accept()
                )

            return (
                RuntimeRoleAdmissionDecision
                .reject(
                    reason=(
                        "Runtime role does not "
                        "currently accept ordinary "
                        "connections."
                    )
                )
            )

        return (
            RuntimeRoleAdmissionDecision
            .accept()
        )

    def evaluate_message(
            self,
            *,
            snapshot: RuntimeClusterSnapshot,
            component_type: RuntimeComponentType,
            message_type: str,
            message_category: str,
    ) -> RuntimeRoleAdmissionDecision:
        del component_type
        del message_category

        restricted = (
                snapshot.role
                in _RESTRICTED_ROLES
                or snapshot.state
                in _RESTRICTED_STATES
        )

        if not restricted:
            return (
                RuntimeRoleAdmissionDecision
                .accept()
            )

        if self._is_continuation_message(
                message_type
        ):
            return (
                RuntimeRoleAdmissionDecision
                .accept()
            )

        return (
            RuntimeRoleAdmissionDecision
            .reject(
                reason=(
                    "Runtime role does not "
                    "currently accept new ordinary "
                    "business messages."
                )
            )
        )

    @staticmethod
    def _is_internal_component(
            component_type: RuntimeComponentType,
    ) -> bool:
        return (
                component_type
                in _INTERNAL_COMPONENT_TYPES
        )

    @staticmethod
    def _is_continuation_message(
            message_type: str,
    ) -> bool:
        if (
                message_type
                in _CONTINUATION_MESSAGE_TYPES
        ):
            return True

        return message_type.startswith(
            _CONTINUATION_MESSAGE_PREFIXES
        )

    @staticmethod
    def _validate_active_sub_node_count(
            active_sub_node_count: int,
    ) -> None:
        if (
                isinstance(
                    active_sub_node_count,
                    bool,
                )
                or not isinstance(
            active_sub_node_count,
            int,
        )
                or active_sub_node_count < 0
        ):
            raise ValueError(
                "active_sub_node_count must be "
                "a non-negative integer."
            )
