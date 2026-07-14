# -*- coding: utf-8 -*-
from __future__ import annotations

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
    Any,
    Callable,
    Mapping,
)

from ns_common.exceptions import (
    NsRuntimeClusterFencingError,
    NsRuntimeClusterStateError,
)
from ns_runtime.state_store import (
    InMemoryRuntimeStateStore,
    RuntimeStateEntry,
    RuntimeStateStore,
    RuntimeStateWriteResult,
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

        for field_name in (
                "acquired_at",
                "renewed_at",
                "expires_at",
        ):
            value = getattr(
                self,
                field_name,
            )

            if (
                    not isinstance(value, str)
                    or not value.strip()
            ):
                raise ValueError(
                    f"{field_name} must be non-empty."
                )

    def to_dict(self) -> dict[str, object]:
        return {
            "holder_runtime_id": (
                self.holder_runtime_id
            ),
            "epoch": self.epoch,
            "fencing_token": self.fencing_token,
            "acquired_at": self.acquired_at,
            "renewed_at": self.renewed_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_mapping(
            cls,
            value: Mapping[str, Any],
    ) -> "RuntimeLeaderLease":
        return cls(
            holder_runtime_id=str(
                value.get(
                    "holder_runtime_id",
                    "",
                )
            ),
            epoch=value.get(
                "epoch",
                0,
            ),
            fencing_token=str(
                value.get(
                    "fencing_token",
                    "",
                )
            ),
            acquired_at=str(
                value.get(
                    "acquired_at",
                    "",
                )
            ),
            renewed_at=str(
                value.get(
                    "renewed_at",
                    "",
                )
            ),
            expires_at=str(
                value.get(
                    "expires_at",
                    "",
                )
            ),
        )


@dataclass(
    slots=True,
    frozen=True,
    kw_only=True,
)
class RuntimeLeaderLeaseStoreSnapshot:
    lease: RuntimeLeaderLease | None
    version: int
    last_epoch: int
    issued_fencing_tokens: tuple[str, ...]
    lease_valid: bool
    observed_at: str


class RuntimeLeaderLeaseStore(ABC):
    @abstractmethod
    def read(
            self,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        raise NotImplementedError

    @abstractmethod
    def try_acquire(
            self,
            *,
            runtime_id: str,
            fencing_token: str,
            ttl_seconds: float,
            expected_version: int,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        raise NotImplementedError

    @abstractmethod
    def try_renew(
            self,
            *,
            runtime_id: str,
            epoch: int,
            fencing_token: str,
            ttl_seconds: float,
            expected_version: int,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        raise NotImplementedError

    @abstractmethod
    def try_release(
            self,
            *,
            runtime_id: str,
            epoch: int,
            fencing_token: str,
            expected_version: int,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        raise NotImplementedError


class StateStoreRuntimeLeaderLeaseStore(
    RuntimeLeaderLeaseStore
):
    def __init__(
            self,
            *,
            state_store: RuntimeStateStore,
            namespace: str = "system.cluster",
            key: str = "leader_lease",
            clock: Callable[[], datetime] | None = None,
    ) -> None:
        if (
                not isinstance(namespace, str)
                or not namespace.strip()
        ):
            raise ValueError(
                "namespace must be non-empty."
            )

        if (
                not isinstance(key, str)
                or not key.strip()
        ):
            raise ValueError(
                "key must be non-empty."
            )

        capabilities = state_store.capabilities

        if not capabilities.supports_atomic_create:
            raise ValueError(
                "state_store must support "
                "atomic create."
            )

        if not capabilities.supports_compare_and_swap:
            raise ValueError(
                "state_store must support "
                "compare-and-swap."
            )

        self._state_store = state_store
        self._namespace = namespace.strip()
        self._key = key.strip()
        self._clock = (
                clock
                or (
                    lambda: datetime.now(
                        timezone.utc
                    )
                )
        )

    @property
    def state_store(
            self,
    ) -> RuntimeStateStore:
        return self._state_store

    def read(
            self,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        now = self._now()

        entry = self._state_store.get(
            namespace=self._namespace,
            key=self._key,
        )

        return self._snapshot_from_entry(
            entry,
            now,
        )

    def try_acquire(
            self,
            *,
            runtime_id: str,
            fencing_token: str,
            ttl_seconds: float,
            expected_version: int,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        resolved_runtime_id = (
            self._validate_non_empty(
                runtime_id,
                "runtime_id",
            )
        )
        resolved_token = self._validate_non_empty(
            fencing_token,
            "fencing_token",
        )
        resolved_ttl = self._validate_ttl(
            ttl_seconds
        )
        resolved_version = (
            self._validate_expected_version(
                expected_version
            )
        )

        now = self._now()
        current = self.read()

        self._require_version(
            current,
            resolved_version,
        )

        if (
                current.lease_valid
                and current.lease is not None
        ):
            raise NsRuntimeClusterStateError(
                "A valid leader lease is already held.",
                details={
                    "leader_runtime_id": (
                        current.lease
                        .holder_runtime_id
                    ),
                    "leader_epoch": (
                        current.lease.epoch
                    ),
                    "store_version": (
                        current.version
                    ),
                },
            )

        if (
                resolved_token
                in current.issued_fencing_tokens
        ):
            raise NsRuntimeClusterFencingError(
                "Leader fencing token was "
                "already issued.",
                details={
                    "runtime_id": (
                        resolved_runtime_id
                    ),
                    "last_epoch": (
                        current.last_epoch
                    ),
                },
            )

        now_iso = self._to_iso(now)

        lease = RuntimeLeaderLease(
            holder_runtime_id=resolved_runtime_id,
            epoch=current.last_epoch + 1,
            fencing_token=resolved_token,
            acquired_at=now_iso,
            renewed_at=now_iso,
            expires_at=self._to_iso(
                now + timedelta(
                    seconds=resolved_ttl
                )
            ),
        )

        value = self._build_value(
            lease=lease,
            last_epoch=lease.epoch,
            issued_fencing_tokens=(
                *current.issued_fencing_tokens,
                resolved_token,
            ),
        )

        result = self._write(
            expected_version=resolved_version,
            value=value,
        )

        return self._snapshot_from_result(
            result,
            now,
        )

    def try_renew(
            self,
            *,
            runtime_id: str,
            epoch: int,
            fencing_token: str,
            ttl_seconds: float,
            expected_version: int,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        resolved_runtime_id = (
            self._validate_non_empty(
                runtime_id,
                "runtime_id",
            )
        )
        resolved_epoch = self._validate_epoch(
            epoch
        )
        resolved_token = self._validate_non_empty(
            fencing_token,
            "fencing_token",
        )
        resolved_ttl = self._validate_ttl(
            ttl_seconds
        )
        resolved_version = (
            self._validate_expected_version(
                expected_version
            )
        )

        now = self._now()
        current = self.read()

        self._require_version(
            current,
            resolved_version,
        )

        lease = self._require_valid_lease(
            current
        )

        self._require_authority(
            lease=lease,
            runtime_id=resolved_runtime_id,
            epoch=resolved_epoch,
            fencing_token=resolved_token,
        )

        renewed = RuntimeLeaderLease(
            holder_runtime_id=(
                lease.holder_runtime_id
            ),
            epoch=lease.epoch,
            fencing_token=(
                lease.fencing_token
            ),
            acquired_at=lease.acquired_at,
            renewed_at=self._to_iso(now),
            expires_at=self._to_iso(
                now + timedelta(
                    seconds=resolved_ttl
                )
            ),
        )

        result = self._write(
            expected_version=resolved_version,
            value=self._build_value(
                lease=renewed,
                last_epoch=current.last_epoch,
                issued_fencing_tokens=(
                    current.issued_fencing_tokens
                ),
            ),
        )

        return self._snapshot_from_result(
            result,
            now,
        )

    def try_release(
            self,
            *,
            runtime_id: str,
            epoch: int,
            fencing_token: str,
            expected_version: int,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        resolved_runtime_id = (
            self._validate_non_empty(
                runtime_id,
                "runtime_id",
            )
        )
        resolved_epoch = self._validate_epoch(
            epoch
        )
        resolved_token = self._validate_non_empty(
            fencing_token,
            "fencing_token",
        )
        resolved_version = (
            self._validate_expected_version(
                expected_version
            )
        )

        now = self._now()
        current = self.read()

        self._require_version(
            current,
            resolved_version,
        )

        lease = self._require_valid_lease(
            current
        )

        self._require_authority(
            lease=lease,
            runtime_id=resolved_runtime_id,
            epoch=resolved_epoch,
            fencing_token=resolved_token,
        )

        result = self._write(
            expected_version=resolved_version,
            value=self._build_value(
                lease=None,
                last_epoch=current.last_epoch,
                issued_fencing_tokens=(
                    current.issued_fencing_tokens
                ),
            ),
        )

        return self._snapshot_from_result(
            result,
            now,
        )

    def _write(
            self,
            *,
            expected_version: int,
            value: Mapping[str, Any],
    ) -> RuntimeStateWriteResult:
        if expected_version == 0:
            result = (
                self._state_store
                .put_if_absent(
                    namespace=self._namespace,
                    key=self._key,
                    value=value,
                )
            )
        else:
            result = (
                self._state_store
                .compare_and_swap(
                    namespace=self._namespace,
                    key=self._key,
                    expected_version=(
                        expected_version
                    ),
                    value=value,
                )
            )

        if (
                not result.success
                or result.entry is None
        ):
            current_version = (
                result.current_entry.version
                if result.current_entry is not None
                else 0
            )

            raise NsRuntimeClusterStateError(
                "Leader lease state changed "
                "concurrently.",
                details={
                    "expected_version": (
                        expected_version
                    ),
                    "current_version": (
                        current_version
                    ),
                    "write_status": result.status,
                },
            )

        return result

    def _snapshot_from_result(
            self,
            result: RuntimeStateWriteResult,
            now: datetime,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        if result.entry is None:
            raise NsRuntimeClusterStateError(
                "Leader lease write did not "
                "return state."
            )

        return self._snapshot_from_entry(
            result.entry,
            now,
        )

    def _snapshot_from_entry(
            self,
            entry: RuntimeStateEntry | None,
            now: datetime,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        if entry is None:
            return RuntimeLeaderLeaseStoreSnapshot(
                lease=None,
                version=0,
                last_epoch=0,
                issued_fencing_tokens=(),
                lease_valid=False,
                observed_at=self._to_iso(now),
            )

        (
            lease,
            last_epoch,
            issued_tokens,
        ) = self._decode_value(entry.value)

        lease_valid = (
                lease is not None
                and now
                < self._parse_iso(
            lease.expires_at
        )
        )

        return RuntimeLeaderLeaseStoreSnapshot(
            lease=lease,
            version=entry.version,
            last_epoch=last_epoch,
            issued_fencing_tokens=issued_tokens,
            lease_valid=lease_valid,
            observed_at=self._to_iso(now),
        )

    def _decode_value(
            self,
            value: Mapping[str, Any],
    ) -> tuple[
        RuntimeLeaderLease | None,
        int,
        tuple[str, ...],
    ]:
        raw_last_epoch = value.get(
            "last_epoch",
            0,
        )

        if (
                isinstance(raw_last_epoch, bool)
                or not isinstance(
            raw_last_epoch,
            int,
        )
                or raw_last_epoch < 0
        ):
            raise NsRuntimeClusterStateError(
                "Leader lease state contains "
                "invalid last_epoch."
            )

        raw_tokens = value.get(
            "issued_fencing_tokens",
            (),
        )

        if not isinstance(
                raw_tokens,
                (
                        list,
                        tuple,
                ),
        ):
            raise NsRuntimeClusterStateError(
                "Leader lease state contains "
                "invalid token history."
            )

        issued_tokens: list[str] = []

        for token in raw_tokens:
            if (
                    not isinstance(token, str)
                    or not token.strip()
            ):
                raise NsRuntimeClusterStateError(
                    "Leader lease state contains "
                    "invalid token history."
                )

            issued_tokens.append(
                token.strip()
            )

        if (
                len(set(issued_tokens))
                != len(issued_tokens)
        ):
            raise NsRuntimeClusterStateError(
                "Leader lease state contains "
                "duplicate fencing tokens."
            )

        raw_lease = value.get("lease")
        lease: RuntimeLeaderLease | None = None

        if raw_lease is not None:
            if not isinstance(
                    raw_lease,
                    Mapping,
            ):
                raise NsRuntimeClusterStateError(
                    "Leader lease state contains "
                    "invalid lease data."
                )

            try:
                lease = (
                    RuntimeLeaderLease
                    .from_mapping(raw_lease)
                )

                self._parse_iso(
                    lease.acquired_at
                )
                self._parse_iso(
                    lease.renewed_at
                )
                self._parse_iso(
                    lease.expires_at
                )
            except (
                    TypeError,
                    ValueError,
            ) as exc:
                raise NsRuntimeClusterStateError(
                    "Leader lease state contains "
                    "invalid lease data."
                ) from exc

            if lease.epoch > raw_last_epoch:
                raise NsRuntimeClusterStateError(
                    "Leader lease epoch exceeds "
                    "last_epoch."
                )

            if (
                    lease.fencing_token
                    not in issued_tokens
            ):
                raise NsRuntimeClusterStateError(
                    "Current fencing token is missing "
                    "from token history."
                )

        return (
            lease,
            raw_last_epoch,
            tuple(issued_tokens),
        )

    @staticmethod
    def _build_value(
            *,
            lease: RuntimeLeaderLease | None,
            last_epoch: int,
            issued_fencing_tokens: tuple[str, ...],
    ) -> dict[str, Any]:
        return {
            "lease": (
                lease.to_dict()
                if lease is not None
                else None
            ),
            "last_epoch": last_epoch,
            "issued_fencing_tokens": list(
                issued_fencing_tokens
            ),
        }

    @staticmethod
    def _require_version(
            snapshot: RuntimeLeaderLeaseStoreSnapshot,
            expected_version: int,
    ) -> None:
        if snapshot.version != expected_version:
            raise NsRuntimeClusterStateError(
                "Leader lease state version "
                "does not match.",
                details={
                    "expected_version": (
                        expected_version
                    ),
                    "current_version": (
                        snapshot.version
                    ),
                },
            )

    @staticmethod
    def _require_valid_lease(
            snapshot: RuntimeLeaderLeaseStoreSnapshot,
    ) -> RuntimeLeaderLease:
        if (
                snapshot.lease is None
                or not snapshot.lease_valid
        ):
            raise NsRuntimeClusterStateError(
                "Leader lease is missing "
                "or expired.",
                details={
                    "store_version": (
                        snapshot.version
                    ),
                    "last_epoch": (
                        snapshot.last_epoch
                    ),
                },
            )

        return snapshot.lease

    @staticmethod
    def _require_authority(
            *,
            lease: RuntimeLeaderLease,
            runtime_id: str,
            epoch: int,
            fencing_token: str,
    ) -> None:
        if (
                lease.holder_runtime_id
                != runtime_id
        ):
            raise NsRuntimeClusterStateError(
                "Leader lease is held by "
                "another runtime.",
                details={
                    "leader_runtime_id": (
                        lease.holder_runtime_id
                    ),
                    "runtime_id": runtime_id,
                },
            )

        if (
                lease.epoch != epoch
                or lease.fencing_token
                != fencing_token
        ):
            raise NsRuntimeClusterFencingError(
                "Leader epoch or fencing token "
                "does not match.",
                details={
                    "leader_epoch": lease.epoch,
                    "provided_epoch": epoch,
                },
            )

    @staticmethod
    def _validate_non_empty(
            value: str,
            field_name: str,
    ) -> str:
        if (
                not isinstance(value, str)
                or not value.strip()
        ):
            raise ValueError(
                f"{field_name} must be non-empty."
            )

        return value.strip()

    @staticmethod
    def _validate_epoch(
            epoch: int,
    ) -> int:
        if (
                isinstance(epoch, bool)
                or not isinstance(epoch, int)
                or epoch < 1
        ):
            raise ValueError(
                "epoch must be an integer greater "
                "than or equal to 1."
            )

        return epoch

    @staticmethod
    def _validate_expected_version(
            version: int,
    ) -> int:
        if (
                isinstance(version, bool)
                or not isinstance(version, int)
                or version < 0
        ):
            raise ValueError(
                "expected_version must be an integer "
                "greater than or equal to 0."
            )

        return version

    @staticmethod
    def _validate_ttl(
            ttl_seconds: float,
    ) -> float:
        if (
                isinstance(ttl_seconds, bool)
                or not isinstance(
            ttl_seconds,
            (
                    int,
                    float,
            ),
        )
                or ttl_seconds <= 0
        ):
            raise ValueError(
                "ttl_seconds must be greater than 0."
            )

        return float(ttl_seconds)

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
    def _parse_iso(
            value: str,
    ) -> datetime:
        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware."
            )

        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _to_iso(
            value: datetime,
    ) -> str:
        return value.isoformat(
            timespec="milliseconds"
        )


class InMemoryRuntimeLeaderLeaseStore(
    StateStoreRuntimeLeaderLeaseStore
):
    def __init__(
            self,
            *,
            clock: Callable[[], datetime] | None = None,
    ) -> None:
        state_store = InMemoryRuntimeStateStore(
            clock=clock
        )

        super().__init__(
            state_store=state_store,
            clock=clock,
        )
