# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
from typing import (
    Callable,
    Literal,
)

from ns_common.exceptions import (
    NsRuntimeClusterStateError,
)
from ns_runtime.cluster_store import (
    InMemoryRuntimeLeaderLeaseStore,
    RuntimeLeaderLease,
    RuntimeLeaderLeaseStore,
    RuntimeLeaderLeaseStoreSnapshot,
)
from ns_runtime.models import RuntimeRole

RuntimeClusterState = Literal[
    "starting",
    "ready",
    "transitioning",
    "draining",
    "isolated",
    "unavailable",
]

_STARTUP_ROLES: frozenset[str] = frozenset(
    {
        "singleton",
        "sub_node",
        "standby_master",
    }
)


@dataclass(
    slots=True,
    frozen=True,
    kw_only=True,
)
class RuntimeClusterSnapshot:
    runtime_id: str
    role: RuntimeRole
    state: RuntimeClusterState

    leader_runtime_id: str
    leader_epoch: int
    fencing_token: str
    lease_expires_at: str
    lease_valid: bool

    can_write_cluster_state: bool
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime_id": self.runtime_id,
            "role": self.role,
            "state": self.state,
            "leader_runtime_id": (
                self.leader_runtime_id
            ),
            "leader_epoch": self.leader_epoch,
            "lease_expires_at": (
                self.lease_expires_at
            ),
            "lease_valid": self.lease_valid,
            "can_write_cluster_state": (
                self.can_write_cluster_state
            ),
            "updated_at": self.updated_at,
        }


class RuntimeClusterCoordinator(ABC):
    @property
    @abstractmethod
    def runtime_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def role(self) -> RuntimeRole:
        raise NotImplementedError

    @abstractmethod
    def build_snapshot(
            self,
    ) -> RuntimeClusterSnapshot:
        raise NotImplementedError

    @abstractmethod
    def acquire_leadership(
            self,
    ) -> RuntimeLeaderLease:
        raise NotImplementedError

    @abstractmethod
    def renew_leadership(
            self,
            *,
            fencing_token: str,
    ) -> RuntimeLeaderLease:
        raise NotImplementedError

    @abstractmethod
    def release_leadership(
            self,
            *,
            fencing_token: str,
    ) -> RuntimeClusterSnapshot:
        raise NotImplementedError

    @abstractmethod
    def complete_leadership_loss(
            self,
    ) -> RuntimeClusterSnapshot:
        raise NotImplementedError

    @abstractmethod
    def refresh(
            self,
    ) -> RuntimeClusterSnapshot:
        raise NotImplementedError


class LocalRuntimeClusterCoordinator(
    RuntimeClusterCoordinator
):
    def __init__(
            self,
            *,
            runtime_id: str,
            initial_role: RuntimeRole = "singleton",
            lease_ttl_seconds: float = 15.0,
            clock: Callable[[], datetime] | None = None,
            fencing_token_factory: (
                    Callable[[], str] | None
            ) = None,
            lease_store: (
                    RuntimeLeaderLeaseStore | None
            ) = None,
    ) -> None:
        resolved_runtime_id = runtime_id.strip()

        if not resolved_runtime_id:
            raise ValueError(
                "runtime_id must be non-empty."
            )

        if initial_role not in _STARTUP_ROLES:
            raise ValueError(
                "initial_role must be singleton, "
                "sub_node, or standby_master."
            )

        if (
                isinstance(
                    lease_ttl_seconds,
                    bool,
                )
                or not isinstance(
            lease_ttl_seconds,
            (
                    int,
                    float,
            ),
        )
                or lease_ttl_seconds <= 0
        ):
            raise ValueError(
                "lease_ttl_seconds must be "
                "greater than 0."
            )

        self._runtime_id = resolved_runtime_id
        self._role: RuntimeRole = initial_role
        self._state: RuntimeClusterState = "ready"

        self._lease_ttl_seconds = float(
            lease_ttl_seconds
        )
        self._clock = (
                clock
                or (
                    lambda: datetime.now(
                        timezone.utc
                    )
                )
        )
        self._fencing_token_factory = (
                fencing_token_factory
                or (
                    lambda: str(uuid.uuid4())
                )
        )
        self._lease_store = (
                lease_store
                or InMemoryRuntimeLeaderLeaseStore(
            clock=self._clock
        )
        )

        initial_store_snapshot = (
            self._lease_store.read()
        )
        self._observed_store_version = (
            initial_store_snapshot.version
        )
        self._updated_at = self._to_iso(
            self._now()
        )

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    @property
    def role(self) -> RuntimeRole:
        self.refresh()
        return self._role

    @property
    def lease_store(
            self,
    ) -> RuntimeLeaderLeaseStore:
        return self._lease_store

    def build_snapshot(
            self,
    ) -> RuntimeClusterSnapshot:
        return self.refresh()

    def acquire_leadership(
            self,
    ) -> RuntimeLeaderLease:
        self.refresh()

        if self._role != "standby_master":
            raise NsRuntimeClusterStateError(
                "Only standby_master can acquire "
                "leadership.",
                details={
                    "runtime_id": self._runtime_id,
                    "role": self._role,
                    "state": self._state,
                },
            )

        fencing_token = (
            self._fencing_token_factory()
        )

        if (
                not isinstance(
                    fencing_token,
                    str,
                )
                or not fencing_token.strip()
        ):
            raise ValueError(
                "fencing_token_factory must return "
                "a non-empty string."
            )

        before = self._lease_store.read()

        after = self._lease_store.try_acquire(
            runtime_id=self._runtime_id,
            fencing_token=fencing_token.strip(),
            ttl_seconds=self._lease_ttl_seconds,
            expected_version=before.version,
        )

        lease = after.lease

        if (
                lease is None
                or not after.lease_valid
        ):
            raise NsRuntimeClusterStateError(
                "Leader lease store did not return "
                "an active lease after acquire."
            )

        # 只有 store 写入成功后才提升本地角色。
        self._role = "active_master"
        self._state = "ready"
        self._observe_store_snapshot(after)

        return lease

    def renew_leadership(
            self,
            *,
            fencing_token: str,
    ) -> RuntimeLeaderLease:
        self.refresh()

        if self._role != "active_master":
            raise NsRuntimeClusterStateError(
                "Only active_master with a valid "
                "leader lease can renew leadership.",
                details={
                    "runtime_id": self._runtime_id,
                    "role": self._role,
                    "state": self._state,
                },
            )

        before = self._lease_store.read()
        lease = before.lease

        if (
                lease is None
                or not before.lease_valid
                or lease.holder_runtime_id
                != self._runtime_id
        ):
            self._enter_transitioning()

            raise NsRuntimeClusterStateError(
                "Current runtime no longer owns "
                "a valid leader lease."
            )

        try:
            after = self._lease_store.try_renew(
                runtime_id=self._runtime_id,
                epoch=lease.epoch,
                fencing_token=fencing_token,
                ttl_seconds=(
                    self._lease_ttl_seconds
                ),
                expected_version=before.version,
            )
        except NsRuntimeClusterStateError:
            # CAS 冲突或 lease 状态变化后，
            # 立即重新读取权威状态。
            self.refresh()
            raise

        renewed = after.lease

        if (
                renewed is None
                or not after.lease_valid
        ):
            raise NsRuntimeClusterStateError(
                "Leader lease store did not return "
                "an active lease after renew."
            )

        self._observe_store_snapshot(after)

        return renewed

    def release_leadership(
            self,
            *,
            fencing_token: str,
    ) -> RuntimeClusterSnapshot:
        self.refresh()

        if self._role != "active_master":
            raise NsRuntimeClusterStateError(
                "Only active_master with a valid "
                "leader lease can release leadership.",
                details={
                    "runtime_id": self._runtime_id,
                    "role": self._role,
                    "state": self._state,
                },
            )

        before = self._lease_store.read()
        lease = before.lease

        if (
                lease is None
                or not before.lease_valid
                or lease.holder_runtime_id
                != self._runtime_id
        ):
            self._enter_transitioning()

            raise NsRuntimeClusterStateError(
                "Current runtime no longer owns "
                "a valid leader lease."
            )

        try:
            after = self._lease_store.try_release(
                runtime_id=self._runtime_id,
                epoch=lease.epoch,
                fencing_token=fencing_token,
                expected_version=before.version,
            )
        except NsRuntimeClusterStateError:
            self.refresh()
            raise

        # 只有 store release 成功后才降级本地角色。
        self._role = "standby_master"
        self._state = "ready"
        self._observe_store_snapshot(after)

        return self._build_snapshot(after)

    def complete_leadership_loss(
            self,
    ) -> RuntimeClusterSnapshot:
        store_snapshot = self._lease_store.read()

        self._observe_store_snapshot(
            store_snapshot
        )

        if self._role != "transitioning":
            raise NsRuntimeClusterStateError(
                "Only transitioning runtime can "
                "complete leadership loss.",
                details={
                    "runtime_id": self._runtime_id,
                    "role": self._role,
                    "state": self._state,
                },
            )

        self._role = "standby_master"
        self._state = "ready"
        self._updated_at = self._to_iso(
            self._now()
        )

        return self._build_snapshot(
            store_snapshot
        )

    def refresh(
            self,
    ) -> RuntimeClusterSnapshot:
        store_snapshot = self._lease_store.read()

        self._observe_store_snapshot(
            store_snapshot
        )

        if self._role == "active_master":
            lease = store_snapshot.lease

            if (
                    lease is None
                    or not store_snapshot.lease_valid
                    or lease.holder_runtime_id
                    != self._runtime_id
            ):
                self._enter_transitioning()

        return self._build_snapshot(
            store_snapshot
        )

    def _build_snapshot(
            self,
            store_snapshot: (
                    RuntimeLeaderLeaseStoreSnapshot
            ),
    ) -> RuntimeClusterSnapshot:
        visible_lease = store_snapshot.lease

        if self._role == "singleton":
            visible_lease = None
        elif (
                visible_lease is not None
                and not store_snapshot.lease_valid
                and self._role != "transitioning"
        ):
            # standby/sub_node 不将过期 lease
            # 对外表现为当前 leader。
            visible_lease = None

        lease_valid = (
                visible_lease is not None
                and store_snapshot.lease_valid
        )

        can_write_cluster_state = (
                (
                        self._role == "singleton"
                        and self._state == "ready"
                )
                or (
                        self._role == "active_master"
                        and lease_valid
                        and visible_lease is not None
                        and visible_lease.holder_runtime_id
                        == self._runtime_id
                )
        )

        return RuntimeClusterSnapshot(
            runtime_id=self._runtime_id,
            role=self._role,
            state=self._state,
            leader_runtime_id=(
                visible_lease.holder_runtime_id
                if visible_lease is not None
                else ""
            ),
            leader_epoch=(
                store_snapshot.last_epoch
            ),
            fencing_token=(
                visible_lease.fencing_token
                if visible_lease is not None
                else ""
            ),
            lease_expires_at=(
                visible_lease.expires_at
                if visible_lease is not None
                else ""
            ),
            lease_valid=lease_valid,
            can_write_cluster_state=(
                can_write_cluster_state
            ),
            updated_at=self._updated_at,
        )

    def _observe_store_snapshot(
            self,
            snapshot: RuntimeLeaderLeaseStoreSnapshot,
    ) -> None:
        if (
                snapshot.version
                == self._observed_store_version
        ):
            return

        self._observed_store_version = (
            snapshot.version
        )
        self._updated_at = snapshot.observed_at

    def _enter_transitioning(
            self,
    ) -> None:
        if (
                self._role == "transitioning"
                and self._state == "transitioning"
        ):
            return

        self._role = "transitioning"
        self._state = "transitioning"
        self._updated_at = self._to_iso(
            self._now()
        )

    def _now(self) -> datetime:
        now = self._clock()

        if not isinstance(now, datetime):
            raise TypeError(
                "clock must return datetime."
            )

        if now.tzinfo is None:
            raise ValueError(
                "clock must return timezone-aware "
                "datetime."
            )

        return now.astimezone(timezone.utc)

    @staticmethod
    def _to_iso(
            value: datetime,
    ) -> str:
        return value.isoformat(
            timespec="milliseconds"
        )
