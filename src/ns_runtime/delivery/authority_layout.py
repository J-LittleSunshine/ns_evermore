# -*- coding: utf-8 -*-
"""Recoverable P10/P11 authority layout and runtime tenant registry.

The registry deliberately uses one provider-neutral StateStore scope.  It is
not a scheduling queue and is never joined atomically with tenant delivery
partitions, so Redis Cluster does not require a cross-slot transaction.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from ns_common.exceptions import (
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreUnavailableError,
    NsRuntimeStateStoreVersionMismatchError,
    NsValidationError,
)
from ns_common.state_store import (
    StateAccessScope,
    StateAssertion,
    StateAtomicScope,
    StateAuthorityKind,
    StateCallerCapability,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateNamespace,
    StateOrderedIndexKey,
    StateOrderedIndexMutation,
    StateOrderedIndexMutationKind,
    StateStore,
    StateTransaction,
)

from .models import AUTHORITY_LAYOUT_GENERATION, AUTHORITY_LAYOUT_VERSION


REGISTRY_SCHEMA_VERSION = 1
MAX_REGISTERED_TENANTS = 1_000


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryAuthorityLayout:
    version: str = AUTHORITY_LAYOUT_VERSION
    generation: int = AUTHORITY_LAYOUT_GENERATION
    bucket_count: int

    def __post_init__(self) -> None:
        if self.version != AUTHORITY_LAYOUT_VERSION:
            _invalid("layout.version")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation <= 0:
            _invalid("layout.generation")
        if isinstance(self.bucket_count, bool) or not isinstance(self.bucket_count, int) or self.bucket_count <= 0:
            _invalid("layout.bucket_count")


def delivery_scope(
    tenant_id: str,
    bucket_id: int,
    *,
    layout_generation: int = AUTHORITY_LAYOUT_GENERATION,
    caller: str = "delivery.scheduling",
) -> StateAccessScope:
    if type(tenant_id) is not str or not tenant_id:
        _invalid("scope.tenant_id")
    if isinstance(bucket_id, bool) or not isinstance(bucket_id, int) or bucket_id < 0:
        _invalid("scope.bucket_id")
    if isinstance(layout_generation, bool) or not isinstance(layout_generation, int) or layout_generation <= 0:
        _invalid("scope.layout_generation")
    namespace = StateNamespace.tenant(tenant_id=tenant_id, domain="delivery")
    return StateAccessScope(
        atomic_scope=StateAtomicScope(
            namespace=namespace,
            partition=f"layout-{layout_generation}-bucket-{bucket_id}",
        ),
        authority=StateAuthorityKind.DELIVERY_ADMISSION,
        caller=caller,
        capabilities=frozenset({
            StateCallerCapability.READ,
            StateCallerCapability.SCAN,
            StateCallerCapability.COMPARE_AND_SET,
            StateCallerCapability.TRANSACT,
            StateCallerCapability.ORDERED_INDEX,
            StateCallerCapability.APPEND,
        }),
    )


class StateStoreDeliveryAuthorityRegistry:
    """Durable runtime-wide list of tenants and one immutable layout."""

    def __init__(self, *, store: StateStore, runtime_id: str = "runtime-local") -> None:
        if not isinstance(store, StateStore):
            _invalid("registry.store")
        if type(runtime_id) is not str or not runtime_id:
            _invalid("registry.runtime_id")
        self._store = store
        self._runtime_id = runtime_id
        synthetic_tenant = "runtime-registry:" + hashlib.sha256(runtime_id.encode()).hexdigest()
        namespace = StateNamespace.tenant(tenant_id=synthetic_tenant, domain="delivery")
        self._scope = StateAccessScope(
            atomic_scope=StateAtomicScope(namespace=namespace, partition="authority-registry"),
            authority=StateAuthorityKind.DELIVERY_ADMISSION,
            caller="delivery.authority_registry",
            capabilities=frozenset({
                StateCallerCapability.READ,
                StateCallerCapability.TRANSACT,
                StateCallerCapability.ORDERED_INDEX,
            }),
        )

    async def ensure_registered(
        self, *, tenant_id: str, layout: DeliveryAuthorityLayout,
    ) -> None:
        if type(tenant_id) is not str or not tenant_id:
            _invalid("registry.tenant_id")
        if not isinstance(layout, DeliveryAuthorityLayout):
            _invalid("registry.layout")
        await self._ensure_layout(layout)
        key = self._tenant_key(tenant_id)
        existing = await self._read(key)
        if existing is not None:
            self._validate_tenant(existing.document.payload, tenant_id, layout)
            return
        payload = self._tenant_payload(tenant_id, layout)
        mutation = StateMutation(
            key=key,
            assertion=StateAssertion.absent(),
            kind=StateMutationKind.CREATE,
            document=StateDocument(
                schema_name="delivery.tenant_registration",
                schema_version=REGISTRY_SCHEMA_VERSION,
                state_version=1,
                payload=payload,
            ),
        )
        try:
            await self._store.transact(StateTransaction(
                scope=self._scope,
                mutations=(mutation,),
                ordered_index_mutations=(StateOrderedIndexMutation(
                    index=self._tenant_index(),
                    kind=StateOrderedIndexMutationKind.ADD,
                    member=key.object_id,
                    score=float(int(key.object_id[:12], 16)),
                ),),
            ))
        except NsRuntimeStateStoreConflictError:
            existing = await self._read(key)
            if existing is None:
                raise
            self._validate_tenant(existing.document.payload, tenant_id, layout)

    async def registered_tenants(
        self, *, layout: DeliveryAuthorityLayout,
    ) -> tuple[str, ...]:
        if not isinstance(layout, DeliveryAuthorityLayout):
            _invalid("registry.layout")
        await self._require_layout(layout)
        page = await self._store.read_ordered_index(
            scope=self._scope,
            index=self._tenant_index(),
            limit=MAX_REGISTERED_TENANTS,
        )
        if page.total_count > MAX_REGISTERED_TENANTS or page.next_cursor is not None:
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_authority_registry",
                "operation": "registered_tenants",
                "reason": "registry_scan_budget_exceeded",
            })
        tenants: list[str] = []
        for entry in page.entries:
            record = await self._read(StateKey(
                namespace=self._scope.namespace,
                object_type="delivery_tenant_registration",
                object_id=entry.member,
            ))
            if record is None:
                raise NsRuntimeStateStoreUnavailableError(details={
                    "component": "delivery_authority_registry",
                    "operation": "registered_tenants",
                    "reason": "registry_member_missing",
                })
            values = self._decode(record.document.payload)
            tenant_id = values.get("tenant_id")
            if type(tenant_id) is not str:
                _mismatch("tenant_registration_invalid")
            self._validate_tenant(record.document.payload, tenant_id, layout)
            tenants.append(tenant_id)
        return tuple(tenants)

    async def _ensure_layout(self, layout: DeliveryAuthorityLayout) -> None:
        key = self._layout_key()
        existing = await self._read(key)
        if existing is not None:
            self._validate_layout(existing.document.payload, layout)
            return
        mutation = StateMutation(
            key=key,
            assertion=StateAssertion.absent(),
            kind=StateMutationKind.CREATE,
            document=StateDocument(
                schema_name="delivery.authority_layout",
                schema_version=REGISTRY_SCHEMA_VERSION,
                state_version=1,
                payload=self._layout_payload(layout),
            ),
        )
        try:
            await self._store.transact(StateTransaction(scope=self._scope, mutations=(mutation,)))
        except NsRuntimeStateStoreConflictError:
            existing = await self._read(key)
            if existing is None:
                raise
            self._validate_layout(existing.document.payload, layout)

    async def _require_layout(self, layout: DeliveryAuthorityLayout) -> None:
        record = await self._read(self._layout_key())
        if record is None:
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_authority_registry",
                "operation": "require_layout",
                "reason": "layout_registry_missing",
            })
        self._validate_layout(record.document.payload, layout)

    async def _read(self, key: StateKey):
        result = await self._store.read(
            scope=self._scope,
            key=key,
            consistency=StateConsistency.LINEARIZABLE,
        )
        return result.record

    def _layout_key(self) -> StateKey:
        return StateKey(
            namespace=self._scope.namespace,
            object_type="delivery_authority_layout",
            object_id="layout.current",
        )

    def _tenant_key(self, tenant_id: str) -> StateKey:
        return StateKey(
            namespace=self._scope.namespace,
            object_type="delivery_tenant_registration",
            object_id=hashlib.sha256(tenant_id.encode()).hexdigest(),
        )

    def _tenant_index(self) -> StateOrderedIndexKey:
        return StateOrderedIndexKey(
            namespace=self._scope.namespace,
            name="delivery.tenant_registry",
            bucket="runtime",
        )

    def _layout_payload(self, layout: DeliveryAuthorityLayout) -> bytes:
        return self._encode({
            "runtime_id": self._runtime_id,
            "layout_version": layout.version,
            "layout_generation": layout.generation,
            "bucket_count": layout.bucket_count,
        })

    def _tenant_payload(self, tenant_id: str, layout: DeliveryAuthorityLayout) -> bytes:
        return self._encode({
            "runtime_id": self._runtime_id,
            "tenant_id": tenant_id,
            "layout_version": layout.version,
            "layout_generation": layout.generation,
            "bucket_count": layout.bucket_count,
        })

    def _validate_layout(self, raw: bytes, layout: DeliveryAuthorityLayout) -> None:
        values = self._decode(raw)
        if values != {
            "runtime_id": self._runtime_id,
            "layout_version": layout.version,
            "layout_generation": layout.generation,
            "bucket_count": layout.bucket_count,
        }:
            _mismatch("authority_layout_migration_required")

    def _validate_tenant(
        self, raw: bytes, tenant_id: str, layout: DeliveryAuthorityLayout,
    ) -> None:
        values = self._decode(raw)
        if values != {
            "runtime_id": self._runtime_id,
            "tenant_id": tenant_id,
            "layout_version": layout.version,
            "layout_generation": layout.generation,
            "bucket_count": layout.bucket_count,
        }:
            _mismatch("tenant_layout_migration_required")

    @staticmethod
    def _encode(values: dict[str, object]) -> bytes:
        return json.dumps(values, sort_keys=True, separators=(",", ":")).encode()

    @staticmethod
    def _decode(raw: bytes) -> dict[str, object]:
        try:
            values = json.loads(raw.decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            _mismatch("authority_registry_invalid")
        if not isinstance(values, dict):
            _mismatch("authority_registry_invalid")
        return values


def _mismatch(reason: str):
    raise NsRuntimeStateStoreVersionMismatchError(details={
        "component": "delivery_authority_registry",
        "operation": "validate",
        "reason": reason,
    })


def _invalid(field: str):
    raise NsValidationError(
        "Delivery authority layout is invalid.",
        details={"component": "delivery_authority_layout", "field": field},
    )


__all__ = (
    "DeliveryAuthorityLayout",
    "StateStoreDeliveryAuthorityRegistry",
    "delivery_scope",
)
