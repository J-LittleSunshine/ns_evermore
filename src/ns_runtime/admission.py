# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from collections import Counter
from dataclasses import dataclass
from typing import (
    Literal,
    TYPE_CHECKING,
)

from ns_runtime.delivery import RuntimeDeliveryRegistry
from ns_runtime.models import Envelope
from ns_runtime.routing import RuntimeRouteDecision

if TYPE_CHECKING:
    pass

RuntimeAdmissionScope = Literal[
    "none",
    "runtime",
    "tenant",
    "target",
]

RuntimeAdmissionReason = Literal[
    "accepted",
    "duplicate",
    "runtime_tenant_pool_limit",
    "tenant_active_limit",
    "tenant_inflight_limit",
    "tenant_retry_backlog_limit",
    "target_inflight_limit",
]

_ACTIVE_DELIVERY_STATES: frozenset[str] = frozenset(
    {
        "prepared",
        "queued",
        "sending",
        "ack_waiting",
        "retry_scheduled",
        "replay_requested",
    }
)

_INFLIGHT_DELIVERY_STATES: frozenset[str] = frozenset(
    {
        "sending",
        "ack_waiting",
    }
)

_RETRY_BACKLOG_STATES: frozenset[str] = frozenset(
    {
        "retry_scheduled",
    }
)


@dataclass(slots=True, frozen=True, kw_only=True)
class RuntimeAdmissionPolicy:
    """
    单进程 admission 水位策略。

    当前仅用于 task.dispatch 的 tenant pool。
    system_reserved_active_delivery 为 system pool 预留容量，
    普通 tenant task 不允许使用该部分容量。
    """

    max_runtime_active_delivery: int = 10_000
    system_reserved_active_delivery: int = 1_500

    max_tenant_active_delivery: int = 1_000
    max_tenant_inflight_delivery: int = 256
    max_tenant_retry_backlog: int = 256

    max_target_inflight_delivery: int = 64

    def __post_init__(self) -> None:
        fields = {
            "max_runtime_active_delivery": (
                self.max_runtime_active_delivery
            ),
            "system_reserved_active_delivery": (
                self.system_reserved_active_delivery
            ),
            "max_tenant_active_delivery": (
                self.max_tenant_active_delivery
            ),
            "max_tenant_inflight_delivery": (
                self.max_tenant_inflight_delivery
            ),
            "max_tenant_retry_backlog": (
                self.max_tenant_retry_backlog
            ),
            "max_target_inflight_delivery": (
                self.max_target_inflight_delivery
            ),
        }

        for field_name, value in fields.items():
            if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
            ):
                raise ValueError(
                    f"{field_name} must be a non-negative integer."
                )

        if (
                self.system_reserved_active_delivery
                > self.max_runtime_active_delivery
        ):
            raise ValueError(
                "system_reserved_active_delivery must not exceed "
                "max_runtime_active_delivery."
            )

    @property
    def tenant_pool_active_limit(self) -> int:
        return (
                self.max_runtime_active_delivery
                - self.system_reserved_active_delivery
        )


@dataclass(slots=True, frozen=True, kw_only=True)
class RuntimeAdmissionSnapshot:
    tenant_id: str

    runtime_active_delivery: int
    tenant_active_delivery: int
    tenant_inflight_delivery: int
    tenant_retry_backlog_delivery: int

    target_inflight_delivery: tuple[
        tuple[str, int],
        ...,
    ]

    def get_target_inflight(
            self,
            connection_id: str,
    ) -> int:
        return dict(
            self.target_inflight_delivery
        ).get(
            connection_id,
            0,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant_id": self.tenant_id,
            "runtime_active_delivery": (
                self.runtime_active_delivery
            ),
            "tenant_active_delivery": (
                self.tenant_active_delivery
            ),
            "tenant_inflight_delivery": (
                self.tenant_inflight_delivery
            ),
            "tenant_retry_backlog_delivery": (
                self.tenant_retry_backlog_delivery
            ),
            "target_inflight_delivery": {
                connection_id: count
                for connection_id, count
                in self.target_inflight_delivery
            },
        }


@dataclass(slots=True, frozen=True, kw_only=True)
class RuntimeAdmissionDecision:
    accepted: bool
    reason: RuntimeAdmissionReason
    scope: RuntimeAdmissionScope

    projected_new_delivery_count: int
    current_count: int = 0
    limit: int = 0
    target_connection_id: str = ""

    snapshot: RuntimeAdmissionSnapshot

    @classmethod
    def allow(
            cls,
            *,
            reason: Literal[
                "accepted",
                "duplicate",
            ],
            projected_new_delivery_count: int,
            snapshot: RuntimeAdmissionSnapshot,
    ) -> "RuntimeAdmissionDecision":
        return cls(
            accepted=True,
            reason=reason,
            scope="none",
            projected_new_delivery_count=(
                projected_new_delivery_count
            ),
            snapshot=snapshot,
        )

    @classmethod
    def deny(
            cls,
            *,
            reason: RuntimeAdmissionReason,
            scope: RuntimeAdmissionScope,
            projected_new_delivery_count: int,
            current_count: int,
            limit: int,
            snapshot: RuntimeAdmissionSnapshot,
            target_connection_id: str = "",
    ) -> "RuntimeAdmissionDecision":
        return cls(
            accepted=False,
            reason=reason,
            scope=scope,
            projected_new_delivery_count=(
                projected_new_delivery_count
            ),
            current_count=current_count,
            limit=limit,
            target_connection_id=target_connection_id,
            snapshot=snapshot,
        )

    def to_error_details(
            self,
            *,
            message_id: str,
    ) -> dict[str, object]:
        """
        返回可安全放入 runtime.error 的精简信息。

        不向普通发送方暴露 runtime 或其他 tenant 的实际水位。
        """

        details: dict[str, object] = {
            "message_id": message_id,
            "reason": self.reason,
            "scope": self.scope,
            "projected_new_delivery_count": (
                self.projected_new_delivery_count
            ),
        }

        if self.target_connection_id:
            details["target_connection_id"] = (
                self.target_connection_id
            )

        return details

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "accepted": self.accepted,
            "reason": self.reason,
            "scope": self.scope,
            "projected_new_delivery_count": (
                self.projected_new_delivery_count
            ),
            "current_count": self.current_count,
            "limit": self.limit,
            "snapshot": self.snapshot.to_dict(),
        }

        if self.target_connection_id:
            data["target_connection_id"] = (
                self.target_connection_id
            )

        return data


class RuntimeAdmissionController(ABC):
    @property
    @abstractmethod
    def policy(self) -> RuntimeAdmissionPolicy:
        raise NotImplementedError

    @abstractmethod
    def evaluate(
            self,
            *,
            envelope: Envelope,
            decision: RuntimeRouteDecision,
    ) -> RuntimeAdmissionDecision:
        raise NotImplementedError

    @abstractmethod
    def build_snapshot(
            self,
            *,
            tenant_id: str,
            target_connection_ids: tuple[str, ...] = (),
    ) -> RuntimeAdmissionSnapshot:
        raise NotImplementedError


class LocalRuntimeAdmissionController(RuntimeAdmissionController):
    def __init__(self, *, delivery_registry: RuntimeDeliveryRegistry, policy: RuntimeAdmissionPolicy | None = None) -> None:
        self._delivery_registry = delivery_registry
        self._policy = policy or RuntimeAdmissionPolicy()

    @property
    def policy(self) -> RuntimeAdmissionPolicy:
        return self._policy

    def evaluate(self, *, envelope: Envelope, decision: RuntimeRouteDecision) -> RuntimeAdmissionDecision:
        writable_target_ids = tuple(
            target.connection_id
            for target in decision.targets
            if target.connection_id != "runtime"
        )

        snapshot = self.build_snapshot(
            tenant_id=decision.source_tenant_id,
            target_connection_ids=tuple(
                sorted(
                    set(writable_target_ids)
                )
            ),
        )

        if not writable_target_ids:
            # 后续由 forwarder 按 target unavailable 语义处理。
            return RuntimeAdmissionDecision.allow(
                reason="accepted",
                projected_new_delivery_count=0,
                snapshot=snapshot,
            )

        estimated_new_delivery_count = (
            self._delivery_registry
            .estimate_new_delivery_count(
                decision=decision,
                envelope=envelope,
            )
        )

        if estimated_new_delivery_count == 0:
            return RuntimeAdmissionDecision.allow(
                reason="duplicate",
                projected_new_delivery_count=0,
                snapshot=snapshot,
            )

        projected_target_counts = Counter(
            writable_target_ids
        )
        projected_new_delivery_count = sum(
            projected_target_counts.values()
        )

        runtime_limit = (
            self._policy.tenant_pool_active_limit
        )
        if (
                snapshot.runtime_active_delivery
                + projected_new_delivery_count
                > runtime_limit
        ):
            return RuntimeAdmissionDecision.deny(
                reason="runtime_tenant_pool_limit",
                scope="runtime",
                projected_new_delivery_count=(
                    projected_new_delivery_count
                ),
                current_count=(
                    snapshot.runtime_active_delivery
                ),
                limit=runtime_limit,
                snapshot=snapshot,
            )

        if (
                snapshot.tenant_active_delivery
                + projected_new_delivery_count
                > self._policy.max_tenant_active_delivery
        ):
            return RuntimeAdmissionDecision.deny(
                reason="tenant_active_limit",
                scope="tenant",
                projected_new_delivery_count=(
                    projected_new_delivery_count
                ),
                current_count=(
                    snapshot.tenant_active_delivery
                ),
                limit=(
                    self._policy
                    .max_tenant_active_delivery
                ),
                snapshot=snapshot,
            )

        if (
                snapshot.tenant_inflight_delivery
                + projected_new_delivery_count
                > self._policy.max_tenant_inflight_delivery
        ):
            return RuntimeAdmissionDecision.deny(
                reason="tenant_inflight_limit",
                scope="tenant",
                projected_new_delivery_count=(
                    projected_new_delivery_count
                ),
                current_count=(
                    snapshot.tenant_inflight_delivery
                ),
                limit=(
                    self._policy
                    .max_tenant_inflight_delivery
                ),
                snapshot=snapshot,
            )

        if (
                snapshot.tenant_retry_backlog_delivery > 0
                and snapshot.tenant_retry_backlog_delivery
                >= self._policy.max_tenant_retry_backlog
        ):
            return RuntimeAdmissionDecision.deny(
                reason="tenant_retry_backlog_limit",
                scope="tenant",
                projected_new_delivery_count=(
                    projected_new_delivery_count
                ),
                current_count=(
                    snapshot
                    .tenant_retry_backlog_delivery
                ),
                limit=(
                    self._policy
                    .max_tenant_retry_backlog
                ),
                snapshot=snapshot,
            )

        for (
                target_connection_id,
                projected_target_count,
        ) in sorted(
            projected_target_counts.items()
        ):
            current_target_inflight = (
                snapshot.get_target_inflight(
                    target_connection_id
                )
            )

            if (
                    current_target_inflight
                    + projected_target_count
                    > self._policy
                    .max_target_inflight_delivery
            ):
                return RuntimeAdmissionDecision.deny(
                    reason="target_inflight_limit",
                    scope="target",
                    projected_new_delivery_count=(
                        projected_new_delivery_count
                    ),
                    current_count=(
                        current_target_inflight
                    ),
                    limit=(
                        self._policy
                        .max_target_inflight_delivery
                    ),
                    target_connection_id=(
                        target_connection_id
                    ),
                    snapshot=snapshot,
                )

        return RuntimeAdmissionDecision.allow(
            reason="accepted",
            projected_new_delivery_count=(
                projected_new_delivery_count
            ),
            snapshot=snapshot,
        )

    def build_snapshot(self, *, tenant_id: str, target_connection_ids: tuple[str, ...] = ()) -> RuntimeAdmissionSnapshot:
        target_ids = set(
            target_connection_ids
        )
        target_inflight_counts = {
            connection_id: 0
            for connection_id in target_ids
        }

        runtime_active_delivery = 0
        tenant_active_delivery = 0
        tenant_inflight_delivery = 0
        tenant_retry_backlog_delivery = 0

        for record in self._delivery_registry.list_records():
            if record.state in _ACTIVE_DELIVERY_STATES:
                runtime_active_delivery += 1

                if record.tenant_id == tenant_id:
                    tenant_active_delivery += 1

            if (
                    record.tenant_id == tenant_id
                    and record.state
                    in _INFLIGHT_DELIVERY_STATES
            ):
                tenant_inflight_delivery += 1

            if (
                    record.tenant_id == tenant_id
                    and record.state
                    in _RETRY_BACKLOG_STATES
            ):
                tenant_retry_backlog_delivery += 1

            if (
                    record.target_connection_id
                    in target_ids
                    and record.state
                    in _INFLIGHT_DELIVERY_STATES
            ):
                target_inflight_counts[
                    record.target_connection_id
                ] += 1

        return RuntimeAdmissionSnapshot(
            tenant_id=tenant_id,
            runtime_active_delivery=(
                runtime_active_delivery
            ),
            tenant_active_delivery=(
                tenant_active_delivery
            ),
            tenant_inflight_delivery=(
                tenant_inflight_delivery
            ),
            tenant_retry_backlog_delivery=(
                tenant_retry_backlog_delivery
            ),
            target_inflight_delivery=tuple(
                sorted(
                    target_inflight_counts.items()
                )
            ),
        )
