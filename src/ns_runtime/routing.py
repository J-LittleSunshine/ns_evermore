# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    Mapping,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeTargetUnavailableError,
    NsRuntimeTenantMismatchError
)
from ns_runtime.models import (
    Envelope,
    RuntimeSessionContext
)
from ns_runtime.session import (
    RuntimeConnectionRecord,
    RuntimeSessionRegistry
)

if TYPE_CHECKING:
    pass


@dataclass(slots=True, kw_only=True)
class RuntimeRouteTarget:
    kind: str
    runtime_id: str
    connection_id: str
    session_id: str
    connection_epoch: int
    identity: str
    tenant_id: str
    component_type: str
    capabilities: tuple[str, ...]
    role: str

    @classmethod
    def from_record(cls, record: RuntimeConnectionRecord) -> "RuntimeRouteTarget":
        session = record.session_context
        if session is None:
            raise NsRuntimeTargetUnavailableError(
                "Runtime route target does not have active session context.",
                details={
                    "connection_id": record.connection_id,
                    "state": record.state,
                },
            )

        return cls(
            kind="connection",
            runtime_id=session.runtime_id,
            connection_id=session.connection_id,
            session_id=session.session_id,
            connection_epoch=session.connection_epoch,
            identity=session.identity,
            tenant_id=session.tenant_id,
            component_type=session.component_type,
            capabilities=tuple(session.capabilities),
            role=session.role,
        )

    @classmethod
    def current_runtime(cls, *, runtime_id: str, session: RuntimeSessionContext) -> "RuntimeRouteTarget":
        return cls(
            kind="runtime",
            runtime_id=runtime_id,
            connection_id="runtime",
            session_id="runtime",
            connection_epoch=0,
            identity=runtime_id,
            tenant_id=session.tenant_id,
            component_type="runtime",
            capabilities=("runtime.local",),
            role=session.role,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "runtime_id": self.runtime_id,
            "connection_id": self.connection_id,
            "session_id": self.session_id,
            "connection_epoch": self.connection_epoch,
            "identity": self.identity,
            "tenant_id": self.tenant_id,
            "component_type": self.component_type,
            "capabilities": list(self.capabilities),
            "role": self.role,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeRouteDecision:
    source_connection_id: str
    source_tenant_id: str
    message_id: str
    message_type: str
    target_kind: str
    strategy: str
    local_only: bool
    targets: tuple[RuntimeRouteTarget, ...]

    @property
    def target_count(self) -> int:
        return len(self.targets)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_connection_id": self.source_connection_id,
            "source_tenant_id": self.source_tenant_id,
            "message_id": self.message_id,
            "message_type": self.message_type,
            "target_kind": self.target_kind,
            "strategy": self.strategy,
            "local_only": self.local_only,
            "target_count": self.target_count,
            "targets": [
                target.to_dict()
                for target in self.targets
            ],
        }


class RuntimeTargetResolver:
    _SINGLE_TARGET_STRATEGIES: frozenset[str] = (
        frozenset(
            {
                "single",
                "first",
                "policy.default_single",
            }
        )
    )

    _MULTI_TARGET_STRATEGIES: frozenset[str] = (
        frozenset(
            {
                "all",
                "broadcast",
                "policy.default_all",
            }
        )
    )

    _SUPPORTED_STRATEGIES: frozenset[str] = (
            _SINGLE_TARGET_STRATEGIES
            | _MULTI_TARGET_STRATEGIES
    )

    def __init__(self, *, runtime_id: str, session_registry: RuntimeSessionRegistry) -> None:
        self._runtime_id = runtime_id
        self._session_registry = session_registry

    def resolve(self, envelope: Envelope, session: RuntimeSessionContext) -> RuntimeRouteDecision | None:
        target = envelope.raw.get("target")
        if target is None:
            return None

        if not isinstance(target, dict):
            raise NsRuntimeEnvelopeSchemaError("target group must be an object.")

        target_kind = self._require_non_empty_str(target, "kind", "target")
        strategy = self._resolve_strategy(target_kind, target)
        records: tuple[RuntimeConnectionRecord, ...]
        route_targets: tuple[RuntimeRouteTarget, ...]

        if target_kind == "connection":
            records = self._resolve_connection(target, session)
            route_targets = self._to_route_targets(records)
        elif target_kind == "identity":
            records = self._resolve_identity(target, session)
            route_targets = self._to_route_targets(records)
        elif target_kind == "tenant":
            records = self._resolve_tenant(target, session)
            route_targets = self._to_route_targets(records)
        elif target_kind == "broadcast":
            records = self._resolve_tenant(target, session)
            route_targets = self._to_route_targets(records)
        elif target_kind == "component_type":
            records = self._resolve_component_type(target, session)
            route_targets = self._to_route_targets(records)
        elif target_kind == "capability":
            records = self._resolve_capability(target, session)
            route_targets = self._to_route_targets(records)
        elif target_kind == "runtime":
            route_targets = self._resolve_runtime(target, session)
        else:
            raise NsRuntimeEnvelopeSchemaError(
                "target.kind is unsupported by local runtime resolver.",
                details={
                    "target_kind": target_kind,
                },
            )

        route_targets = self._apply_strategy(
            strategy=strategy,
            targets=route_targets,
        )

        if not route_targets:
            raise NsRuntimeTargetUnavailableError(
                "Runtime target is unavailable in local session index.",
                details={
                    "target_kind": target_kind,
                    "message_type": envelope.message_type,
                    "message_id": envelope.message_id,
                    "strategy": strategy,
                },
            )

        return RuntimeRouteDecision(
            source_connection_id=session.connection_id,
            source_tenant_id=session.tenant_id,
            message_id=envelope.message_id,
            message_type=envelope.message_type,
            target_kind=target_kind,
            strategy=strategy,
            local_only=True,
            targets=route_targets,
        )

    def _resolve_connection(self, target: Mapping[str, Any], session: RuntimeSessionContext) -> tuple[RuntimeConnectionRecord, ...]:
        connection_id = self._require_non_empty_str(target, "connection_id", "target")
        target_tenant_id = self._optional_str(target, "tenant_id")
        if target_tenant_id is not None and target_tenant_id != session.tenant_id:
            raise NsRuntimeTenantMismatchError(
                "Cross-tenant connection target is not allowed by local resolver.",
                details={
                    "source_tenant_id": session.tenant_id,
                    "target_tenant_id": target_tenant_id,
                    "connection_id": connection_id,
                },
            )

        record = self._session_registry.get_active_record(connection_id)
        if record is None or record.session_context is None:
            return ()

        if record.session_context.tenant_id != session.tenant_id:
            raise NsRuntimeTenantMismatchError(
                "Cross-tenant connection target is not allowed by local resolver.",
                details={
                    "source_tenant_id": session.tenant_id,
                    "target_tenant_id": record.session_context.tenant_id,
                    "connection_id": connection_id,
                },
            )

        return (record,)

    def _resolve_identity(self, target: Mapping[str, Any], session: RuntimeSessionContext) -> tuple[RuntimeConnectionRecord, ...]:
        identity = self._require_non_empty_str(target, "identity", "target")
        tenant_id = self._resolve_requested_tenant(target, session)
        return tuple(
            record
            for record in self._session_registry.list_by_identity(identity)
            if record.session_context is not None and record.session_context.tenant_id == tenant_id
        )

    def _resolve_tenant(self, target: Mapping[str, Any], session: RuntimeSessionContext) -> tuple[RuntimeConnectionRecord, ...]:
        tenant_id = self._resolve_requested_tenant(target, session)
        return self._session_registry.list_by_tenant(tenant_id)

    def _resolve_component_type(self, target: Mapping[str, Any], session: RuntimeSessionContext) -> tuple[RuntimeConnectionRecord, ...]:
        component_type = self._require_non_empty_str(target, "component_type", "target")
        tenant_id = self._resolve_requested_tenant(target, session)
        return tuple(
            record
            for record in self._session_registry.list_by_component_type(component_type)
            if record.session_context is not None and record.session_context.tenant_id == tenant_id
        )

    def _resolve_capability(self, target: Mapping[str, Any], session: RuntimeSessionContext) -> tuple[RuntimeConnectionRecord, ...]:
        capabilities = self._read_capabilities(target)
        tenant_id = self._resolve_requested_tenant(target, session)

        candidate_ids: set[str] | None = None
        for capability in capabilities:
            ids = {
                record.connection_id
                for record in self._session_registry.list_by_capability(capability)
                if record.session_context is not None and record.session_context.tenant_id == tenant_id
            }
            candidate_ids = ids if candidate_ids is None else candidate_ids & ids

        if not candidate_ids:
            return ()

        records: list[RuntimeConnectionRecord] = []
        for connection_id in sorted(candidate_ids):
            record = self._session_registry.get_active_record(connection_id)
            if record is not None:
                records.append(record)

        return tuple(records)

    def _resolve_runtime(self, target: Mapping[str, Any], session: RuntimeSessionContext) -> tuple[RuntimeRouteTarget, ...]:
        runtime_id = self._require_non_empty_str(target, "runtime_id", "target")
        if runtime_id != self._runtime_id:
            raise NsRuntimeTargetUnavailableError(
                "Remote runtime routing is not implemented in local routing foundation.",
                details={
                    "requested_runtime_id": runtime_id,
                    "current_runtime_id": self._runtime_id,
                },
            )

        return (
            RuntimeRouteTarget.current_runtime(
                runtime_id=self._runtime_id,
                session=session,
            ),
        )

    def _resolve_requested_tenant(self, target: Mapping[str, Any], session: RuntimeSessionContext) -> str:
        tenant_id = self._optional_str(target, "tenant_id") or session.tenant_id
        if tenant_id != session.tenant_id:
            raise NsRuntimeTenantMismatchError(
                "Cross-tenant target is not allowed by local resolver.",
                details={
                    "source_tenant_id": session.tenant_id,
                    "target_tenant_id": tenant_id,
                },
            )

        return tenant_id

    def _resolve_strategy(
            self,
            target_kind: str,
            target: Mapping[str, Any],
    ) -> str:
        strategy = self._optional_str(
            target,
            "strategy",
        )

        if strategy is None:
            if target_kind in {
                "identity",
                "component_type",
                "capability",
            }:
                return "policy.default_single"

            if target_kind == "tenant":
                return "policy.default_all"

            if target_kind == "broadcast":
                return "broadcast"

            return "single"

        if strategy not in self._SUPPORTED_STRATEGIES:
            raise NsRuntimeEnvelopeSchemaError(
                "target.strategy is unsupported by "
                "local runtime resolver.",
                details={
                    "strategy": strategy,
                    "allowed_values": sorted(
                        self._SUPPORTED_STRATEGIES
                    ),
                },
            )

        if (
                target_kind == "broadcast"
                and strategy
                not in self._MULTI_TARGET_STRATEGIES
        ):
            raise NsRuntimeEnvelopeSchemaError(
                "broadcast target requires a "
                "multi-target routing strategy.",
                details={
                    "target_kind": target_kind,
                    "strategy": strategy,
                    "allowed_values": sorted(
                        self._MULTI_TARGET_STRATEGIES
                    ),
                },
            )

        return strategy

    def _apply_strategy(
            self,
            *,
            strategy: str,
            targets: tuple[
                RuntimeRouteTarget,
                ...,
            ],
    ) -> tuple[
        RuntimeRouteTarget,
        ...,
    ]:
        ordered_targets = tuple(
            sorted(
                targets,
                key=lambda target: (
                    target.runtime_id,
                    target.connection_id,
                    target.connection_epoch,
                ),
            )
        )

        if (
                strategy
                in self._SINGLE_TARGET_STRATEGIES
        ):
            return ordered_targets[:1]

        if (
                strategy
                in self._MULTI_TARGET_STRATEGIES
        ):
            return ordered_targets

        raise NsRuntimeEnvelopeSchemaError(
            "Resolved routing strategy is "
            "unsupported.",
            details={
                "strategy": strategy,
                "allowed_values": sorted(
                    self._SUPPORTED_STRATEGIES
                ),
            },
        )

    @staticmethod
    def _to_route_targets(records: tuple[RuntimeConnectionRecord, ...]) -> tuple[RuntimeRouteTarget, ...]:
        return tuple(
            RuntimeRouteTarget.from_record(record)
            for record in records
            if record.state == "active"
        )

    @staticmethod
    def _require_non_empty_str(data: Mapping[str, Any], field_name: str, group_name: str) -> str:
        value = data.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise NsRuntimeEnvelopeSchemaError(
                "Routing field must be a non-empty string.",
                details={
                    "group": group_name,
                    "field": field_name,
                },
            )

        return value.strip()

    @staticmethod
    def _optional_str(data: Mapping[str, Any], field_name: str) -> str | None:
        value = data.get(field_name)
        if value is None:
            return None

        if not isinstance(value, str) or not value.strip():
            raise NsRuntimeEnvelopeSchemaError(
                "Routing optional field must be a non-empty string when provided.",
                details={
                    "field": field_name,
                },
            )

        return value.strip()

    @staticmethod
    def _read_capabilities(target: Mapping[str, Any]) -> tuple[str, ...]:
        raw_value = target.get("capabilities")
        if not isinstance(raw_value, list) or not raw_value:
            raise NsRuntimeEnvelopeSchemaError("target.capabilities must be a non-empty string list.")

        capabilities: list[str] = []
        for item in raw_value:
            if not isinstance(item, str) or not item.strip():
                raise NsRuntimeEnvelopeSchemaError("target.capabilities must only contain non-empty strings.")
            capabilities.append(item.strip())

        return tuple(sorted(set(capabilities)))
