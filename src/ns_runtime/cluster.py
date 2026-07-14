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
    timedelta,
    timezone,
)
from typing import (
    Callable,
    Literal,
    TYPE_CHECKING,
)

from ns_common.exceptions import (
    NsRuntimeClusterFencingError,
    NsRuntimeClusterStateError,
)
from ns_runtime.models import RuntimeRole

if TYPE_CHECKING:
    pass

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
class RuntimeLeaderLease:
    holder_runtime_id: str
    epoch: int
    fencing_token: str
    acquired_at: str
    renewed_at: str
    expires_at: str

    def __post_init__(self) -> None:
        if (
                not isinstance(
                    self.holder_runtime_id,
                    str,
                )
                or not self.holder_runtime_id.strip()
        ):
            raise ValueError(
                "holder_runtime_id must be non-empty."
            )

        if (
                isinstance(self.epoch, bool)
                or not isinstance(self.epoch, int)
                or self.epoch < 1
        ):
            raise ValueError(
                "epoch must be an integer greater "
                "than or equal to 1."
            )

        if (
                not isinstance(
                    self.fencing_token,
                    str,
                )
                or not self.fencing_token.strip()
        ):
            raise ValueError(
                "fencing_token must be non-empty."
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
            "fencing_token": self.fencing_token,
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

        now = self._now()

        self._lease: RuntimeLeaderLease | None = None
        self._lease_expires_at: (
                datetime | None
        ) = None

        self._last_epoch = 0
        self._updated_at = self._to_iso(now)

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    @property
    def role(self) -> RuntimeRole:
        self.refresh()
        return self._role

    def build_snapshot(
            self,
    ) -> RuntimeClusterSnapshot:
        return self.refresh()

    def acquire_leadership(
            self,
    ) -> RuntimeLeaderLease:
        now = self._now()
        self._expire_if_needed(now)

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

        self._last_epoch += 1

        expires_at = now + timedelta(
            seconds=self._lease_ttl_seconds
        )
        now_iso = self._to_iso(now)

        self._lease = RuntimeLeaderLease(
            holder_runtime_id=self._runtime_id,
            epoch=self._last_epoch,
            fencing_token=fencing_token.strip(),
            acquired_at=now_iso,
            renewed_at=now_iso,
            expires_at=self._to_iso(expires_at),
        )
        self._lease_expires_at = expires_at
        self._role = "active_master"
        self._state = "ready"
        self._updated_at = now_iso

        return self._lease

    def renew_leadership(
            self,
            *,
            fencing_token: str,
    ) -> RuntimeLeaderLease:
        now = self._now()
        self._expire_if_needed(now)

        if (
                self._role != "active_master"
                or self._lease is None
                or self._lease_expires_at is None
        ):
            raise NsRuntimeClusterStateError(
                "Only active_master with a valid "
                "leader lease can renew leadership.",
                details={
                    "runtime_id": self._runtime_id,
                    "role": self._role,
                    "state": self._state,
                },
            )

        self._validate_fencing_token(
            fencing_token
        )

        expires_at = now + timedelta(
            seconds=self._lease_ttl_seconds
        )
        now_iso = self._to_iso(now)

        self._lease = RuntimeLeaderLease(
            holder_runtime_id=(
                self._lease.holder_runtime_id
            ),
            epoch=self._lease.epoch,
            fencing_token=(
                self._lease.fencing_token
            ),
            acquired_at=self._lease.acquired_at,
            renewed_at=now_iso,
            expires_at=self._to_iso(expires_at),
        )
        self._lease_expires_at = expires_at
        self._updated_at = now_iso

        return self._lease

    def release_leadership(
            self,
            *,
            fencing_token: str,
    ) -> RuntimeClusterSnapshot:
        now = self._now()
        self._expire_if_needed(now)

        if (
                self._role != "active_master"
                or self._lease is None
                or self._lease_expires_at is None
        ):
            raise NsRuntimeClusterStateError(
                "Only active_master with a valid "
                "leader lease can release leadership.",
                details={
                    "runtime_id": self._runtime_id,
                    "role": self._role,
                    "state": self._state,
                },
            )

        self._validate_fencing_token(
            fencing_token
        )

        self._role = "standby_master"
        self._state = "ready"
        self._lease = None
        self._lease_expires_at = None
        self._updated_at = self._to_iso(now)

        return self._build_snapshot(now)

    def complete_leadership_loss(
            self,
    ) -> RuntimeClusterSnapshot:
        now = self._now()
        self._expire_if_needed(now)

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
        self._lease = None
        self._lease_expires_at = None
        self._updated_at = self._to_iso(now)

        return self._build_snapshot(now)

    def refresh(
            self,
    ) -> RuntimeClusterSnapshot:
        now = self._now()
        self._expire_if_needed(now)

        return self._build_snapshot(now)

    def _build_snapshot(
            self,
            now: datetime,
    ) -> RuntimeClusterSnapshot:
        lease_valid = (
                self._role == "active_master"
                and self._lease is not None
                and self._lease_expires_at is not None
                and now < self._lease_expires_at
        )

        can_write_cluster_state = (
                (
                        self._role == "singleton"
                        and self._state == "ready"
                )
                or lease_valid
        )

        lease = self._lease

        return RuntimeClusterSnapshot(
            runtime_id=self._runtime_id,
            role=self._role,
            state=self._state,
            leader_runtime_id=(
                lease.holder_runtime_id
                if lease is not None
                else ""
            ),
            leader_epoch=(
                lease.epoch
                if lease is not None
                else self._last_epoch
            ),
            fencing_token=(
                lease.fencing_token
                if lease is not None
                else ""
            ),
            lease_expires_at=(
                lease.expires_at
                if lease is not None
                else ""
            ),
            lease_valid=lease_valid,
            can_write_cluster_state=(
                can_write_cluster_state
            ),
            updated_at=self._updated_at,
        )

    def _expire_if_needed(
            self,
            now: datetime,
    ) -> None:
        if (
                self._role != "active_master"
                or self._lease is None
                or self._lease_expires_at is None
                or now < self._lease_expires_at
        ):
            return

        self._role = "transitioning"
        self._state = "transitioning"
        self._updated_at = self._to_iso(now)

    def _validate_fencing_token(
            self,
            fencing_token: str,
    ) -> None:
        lease = self._lease

        if lease is None:
            raise NsRuntimeClusterStateError(
                "Runtime does not hold a leader lease.",
                details={
                    "runtime_id": self._runtime_id,
                    "role": self._role,
                    "state": self._state,
                },
            )

        if fencing_token != lease.fencing_token:
            raise NsRuntimeClusterFencingError(
                "Leader fencing token does not "
                "match the current lease.",
                details={
                    "runtime_id": self._runtime_id,
                    "role": self._role,
                    "leader_epoch": lease.epoch,
                },
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
    def _to_iso(value: datetime) -> str:
        return value.isoformat(
            timespec="milliseconds"
        )
