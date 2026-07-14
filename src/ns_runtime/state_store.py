# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from copy import deepcopy
from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from threading import RLock
from typing import (
    Any,
    Callable,
    Literal,
    Mapping,
)

RuntimeStateWriteStatus = Literal[
    "created",
    "updated",
    "deleted",
    "conflict",
    "not_found",
]


@dataclass(
    slots=True,
    frozen=True,
    kw_only=True,
)
class RuntimeStateStoreCapabilities:
    backend_name: str
    supports_atomic_create: bool
    supports_compare_and_swap: bool
    supports_ttl: bool
    durable: bool
    distributed_authority: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "backend_name": self.backend_name,
            "supports_atomic_create": (
                self.supports_atomic_create
            ),
            "supports_compare_and_swap": (
                self.supports_compare_and_swap
            ),
            "supports_ttl": self.supports_ttl,
            "durable": self.durable,
            "distributed_authority": (
                self.distributed_authority
            ),
        }


@dataclass(
    slots=True,
    frozen=True,
    kw_only=True,
)
class RuntimeStateEntry:
    namespace: str
    key: str
    value: dict[str, Any]
    version: int
    created_at: str
    updated_at: str
    expires_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "key": self.key,
            "value": deepcopy(self.value),
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }


@dataclass(
    slots=True,
    frozen=True,
    kw_only=True,
)
class RuntimeStateWriteResult:
    success: bool
    status: RuntimeStateWriteStatus
    entry: RuntimeStateEntry | None = None
    current_entry: RuntimeStateEntry | None = None


class RuntimeStateStore(ABC):
    @property
    @abstractmethod
    def capabilities(
            self,
    ) -> RuntimeStateStoreCapabilities:
        raise NotImplementedError

    @abstractmethod
    def get(
            self,
            *,
            namespace: str,
            key: str,
    ) -> RuntimeStateEntry | None:
        raise NotImplementedError

    @abstractmethod
    def put_if_absent(
            self,
            *,
            namespace: str,
            key: str,
            value: Mapping[str, Any],
            ttl_seconds: float | None = None,
    ) -> RuntimeStateWriteResult:
        raise NotImplementedError

    @abstractmethod
    def compare_and_swap(
            self,
            *,
            namespace: str,
            key: str,
            expected_version: int,
            value: Mapping[str, Any],
            ttl_seconds: float | None = None,
    ) -> RuntimeStateWriteResult:
        raise NotImplementedError

    @abstractmethod
    def delete_if_version(
            self,
            *,
            namespace: str,
            key: str,
            expected_version: int,
    ) -> RuntimeStateWriteResult:
        raise NotImplementedError


@dataclass(
    slots=True,
    kw_only=True,
)
class _StoredRuntimeStateEntry:
    namespace: str
    key: str
    value: dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None


class InMemoryRuntimeStateStore(
    RuntimeStateStore
):
    def __init__(
            self,
            *,
            clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._clock = (
                clock
                or (
                    lambda: datetime.now(
                        timezone.utc
                    )
                )
        )

        self._entries: dict[
            tuple[str, str],
            _StoredRuntimeStateEntry,
        ] = {}

        self._last_versions: dict[
            tuple[str, str],
            int,
        ] = {}

        self._lock = RLock()

        self._capabilities = (
            RuntimeStateStoreCapabilities(
                backend_name="memory",
                supports_atomic_create=True,
                supports_compare_and_swap=True,
                supports_ttl=True,
                durable=False,
                distributed_authority=False,
            )
        )

    @property
    def capabilities(
            self,
    ) -> RuntimeStateStoreCapabilities:
        return self._capabilities

    def get(
            self,
            *,
            namespace: str,
            key: str,
    ) -> RuntimeStateEntry | None:
        resolved_namespace, resolved_key = (
            self._validate_identity(
                namespace,
                key,
            )
        )
        now = self._now()

        with self._lock:
            stored = self._get_live_entry(
                resolved_namespace,
                resolved_key,
                now,
            )

            return self._copy_entry(stored)

    def put_if_absent(
            self,
            *,
            namespace: str,
            key: str,
            value: Mapping[str, Any],
            ttl_seconds: float | None = None,
    ) -> RuntimeStateWriteResult:
        resolved_namespace, resolved_key = (
            self._validate_identity(
                namespace,
                key,
            )
        )
        resolved_value = self._copy_value(value)
        resolved_ttl = self._validate_ttl(
            ttl_seconds
        )
        now = self._now()

        with self._lock:
            current = self._get_live_entry(
                resolved_namespace,
                resolved_key,
                now,
            )

            if current is not None:
                return RuntimeStateWriteResult(
                    success=False,
                    status="conflict",
                    current_entry=(
                        self._copy_entry(current)
                    ),
                )

            identity = (
                resolved_namespace,
                resolved_key,
            )

            next_version = (
                    self._last_versions.get(
                        identity,
                        0,
                    )
                    + 1
            )

            stored = _StoredRuntimeStateEntry(
                namespace=resolved_namespace,
                key=resolved_key,
                value=resolved_value,
                version=next_version,
                created_at=now,
                updated_at=now,
                expires_at=self._build_expires_at(
                    now,
                    resolved_ttl,
                ),
            )

            self._entries[identity] = stored
            self._last_versions[
                identity
            ] = next_version

            return RuntimeStateWriteResult(
                success=True,
                status="created",
                entry=self._copy_entry(stored),
            )

    def compare_and_swap(
            self,
            *,
            namespace: str,
            key: str,
            expected_version: int,
            value: Mapping[str, Any],
            ttl_seconds: float | None = None,
    ) -> RuntimeStateWriteResult:
        resolved_namespace, resolved_key = (
            self._validate_identity(
                namespace,
                key,
            )
        )
        resolved_version = self._validate_version(
            expected_version
        )
        resolved_value = self._copy_value(value)
        resolved_ttl = self._validate_ttl(
            ttl_seconds
        )
        now = self._now()

        with self._lock:
            current = self._get_live_entry(
                resolved_namespace,
                resolved_key,
                now,
            )

            if current is None:
                return RuntimeStateWriteResult(
                    success=False,
                    status="not_found",
                )

            if current.version != resolved_version:
                return RuntimeStateWriteResult(
                    success=False,
                    status="conflict",
                    current_entry=(
                        self._copy_entry(current)
                    ),
                )

            expires_at = current.expires_at

            # ttl_seconds=None 表示保留原有 TTL，
            # 不主动清除已有 expires_at。
            if resolved_ttl is not None:
                expires_at = self._build_expires_at(
                    now,
                    resolved_ttl,
                )

            identity = (
                resolved_namespace,
                resolved_key,
            )
            next_version = (
                    current.version + 1
            )

            updated = _StoredRuntimeStateEntry(
                namespace=current.namespace,
                key=current.key,
                value=resolved_value,
                version=next_version,
                created_at=current.created_at,
                updated_at=now,
                expires_at=expires_at,
            )

            self._entries[identity] = updated
            self._last_versions[
                identity
            ] = next_version

            return RuntimeStateWriteResult(
                success=True,
                status="updated",
                entry=self._copy_entry(updated),
            )

    def delete_if_version(
            self,
            *,
            namespace: str,
            key: str,
            expected_version: int,
    ) -> RuntimeStateWriteResult:
        resolved_namespace, resolved_key = (
            self._validate_identity(
                namespace,
                key,
            )
        )
        resolved_version = self._validate_version(
            expected_version
        )
        now = self._now()

        with self._lock:
            current = self._get_live_entry(
                resolved_namespace,
                resolved_key,
                now,
            )

            if current is None:
                return RuntimeStateWriteResult(
                    success=False,
                    status="not_found",
                )

            if current.version != resolved_version:
                return RuntimeStateWriteResult(
                    success=False,
                    status="conflict",
                    current_entry=(
                        self._copy_entry(current)
                    ),
                )

            deleted = self._copy_entry(current)

            identity = (
                resolved_namespace,
                resolved_key,
            )

            self._last_versions[
                identity
            ] = max(
                self._last_versions.get(
                    identity,
                    0,
                ),
                current.version,
            )

            del self._entries[identity]

            return RuntimeStateWriteResult(
                success=True,
                status="deleted",
                entry=deleted,
            )

    def _get_live_entry(
            self,
            namespace: str,
            key: str,
            now: datetime,
    ) -> _StoredRuntimeStateEntry | None:
        identity = (
            namespace,
            key,
        )
        stored = self._entries.get(identity)

        if (
                stored is not None
                and stored.expires_at is not None
                and now >= stored.expires_at
        ):
            self._last_versions[
                identity
            ] = max(
                self._last_versions.get(
                    identity,
                    0,
                ),
                stored.version,
            )

            del self._entries[identity]
            return None

        return stored

    @staticmethod
    def _validate_identity(
            namespace: str,
            key: str,
    ) -> tuple[str, str]:
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

        return (
            namespace.strip(),
            key.strip(),
        )

    @staticmethod
    def _validate_version(
            version: int,
    ) -> int:
        if (
                isinstance(version, bool)
                or not isinstance(version, int)
                or version < 1
        ):
            raise ValueError(
                "expected_version must be an integer "
                "greater than or equal to 1."
            )

        return version

    @staticmethod
    def _validate_ttl(
            ttl_seconds: float | None,
    ) -> float | None:
        if ttl_seconds is None:
            return None

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

    @staticmethod
    def _copy_value(
            value: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise TypeError(
                "value must be a mapping."
            )

        return deepcopy(dict(value))

    @classmethod
    def _copy_entry(
            cls,
            stored: _StoredRuntimeStateEntry | None,
    ) -> RuntimeStateEntry | None:
        if stored is None:
            return None

        return RuntimeStateEntry(
            namespace=stored.namespace,
            key=stored.key,
            value=deepcopy(stored.value),
            version=stored.version,
            created_at=cls._to_iso(
                stored.created_at
            ),
            updated_at=cls._to_iso(
                stored.updated_at
            ),
            expires_at=(
                cls._to_iso(stored.expires_at)
                if stored.expires_at is not None
                else ""
            ),
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
    def _build_expires_at(
            now: datetime,
            ttl_seconds: float | None,
    ) -> datetime | None:
        if ttl_seconds is None:
            return None

        return now + timedelta(
            seconds=ttl_seconds
        )

    @staticmethod
    def _to_iso(
            value: datetime,
    ) -> str:
        return value.isoformat(
            timespec="milliseconds"
        )
