# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod
)
from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import (
    Literal,
    TYPE_CHECKING
)

from ns_runtime.models import (
    RuntimeComponentType,
    RuntimeRole
)

if TYPE_CHECKING:
    from ns_runtime.handshake import ConnectionHello


@dataclass(slots=True, kw_only=True)
class RuntimeAuthResult:
    accepted: bool
    identity: str = ""
    tenant_id: str = ""
    component_type: RuntimeComponentType = "client"
    capabilities: tuple[str, ...] = ()
    snapshot_id: str = ""
    issued_at: str = ""
    expires_at: str = ""
    iam_mode: Literal["strict", "cached", "node_trusted"] = "strict"
    role: RuntimeRole = "singleton"
    reject_code: str = ""
    reject_reason: str = ""

    @classmethod
    def reject(cls, *, code: str, reason: str) -> "RuntimeAuthResult":
        return cls(
            accepted=False,
            reject_code=code,
            reject_reason=reason,
        )


class RuntimeAuthenticator(ABC):
    @abstractmethod
    async def authenticate_connection_hello(self, hello: "ConnectionHello", *, connection_id: str, remote_address: str) -> RuntimeAuthResult:
        raise NotImplementedError


class LocalTokenRuntimeAuthenticator(RuntimeAuthenticator):
    def __init__(self, *, expected_token: str, tenant_id: str = "local-tenant", identity_prefix: str = "local", ttl_seconds: int = 3600) -> None:
        self._expected_token = expected_token
        self._tenant_id = tenant_id
        self._identity_prefix = identity_prefix
        self._ttl_seconds = ttl_seconds

    async def authenticate_connection_hello(self, hello: "ConnectionHello", *, connection_id: str, remote_address: str) -> RuntimeAuthResult:
        if not self._expected_token:
            return RuntimeAuthResult.reject(
                code="RUNTIME_AUTH_NOT_CONFIGURED",
                reason="Local runtime token is not configured.",
            )

        if hello.token != self._expected_token:
            return RuntimeAuthResult.reject(
                code="RUNTIME_AUTH_FAILED",
                reason="Invalid connection.hello token.",
            )

        issued_at_dt = datetime.now(timezone.utc)
        expires_at_dt = issued_at_dt + timedelta(seconds=self._ttl_seconds)
        capabilities = tuple(sorted(set(hello.requested_capabilities)))

        return RuntimeAuthResult(
            accepted=True,
            identity=f"{self._identity_prefix}:{hello.component_type}:{connection_id}",
            tenant_id=self._tenant_id,
            component_type=hello.component_type,
            capabilities=capabilities,
            snapshot_id=f"local:{connection_id}",
            issued_at=issued_at_dt.isoformat(timespec="milliseconds"),
            expires_at=expires_at_dt.isoformat(timespec="milliseconds"),
            iam_mode="cached",
            role="singleton",
        )
