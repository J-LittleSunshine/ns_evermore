# -*- coding: utf-8 -*-
"""Durable P11 payload material resolver over the StateStore authority."""

from __future__ import annotations

import base64
import hashlib
import json

from ns_common.exceptions import NsRuntimeStateStoreUnavailableError, NsValidationError
from ns_common.state_store import (
    StateAccessScope, StateAtomicScope, StateAuthorityKind,
    StateCallerCapability, StateConsistency, StateKey, StateNamespace, StateStore,
)
from ns_runtime.protocol import PayloadGroup

from .models import DeliveryRecord, PayloadKind
from .authority_layout import delivery_scope
from .scheduling import (
    DeliveryPayloadResolver, DeliveryPayloadValidator,
    LocalDeliveryTarget, OutboundDeliveryMaterial, PayloadValidationResult,
    payload_access_decision_request_fingerprint,
)


class StateStoreDeliveryPayloadAuthority(
    DeliveryPayloadResolver,
    DeliveryPayloadValidator,
):
    """Resolve inline bodies durably; references remain safe typed material."""

    def __init__(
        self,
        *,
        store: StateStore,
        reference_validator: DeliveryPayloadValidator | None = None,
    ) -> None:
        if not isinstance(store, StateStore):
            _invalid("store")
        self._store = store
        if reference_validator is not None and not isinstance(
            reference_validator, DeliveryPayloadValidator
        ):
            _invalid("reference_validator")
        self._reference_validator = reference_validator

    async def validate(self, delivery: DeliveryRecord, *, target) -> PayloadValidationResult:
        if not isinstance(delivery, DeliveryRecord) or type(target) is not LocalDeliveryTarget:
            _invalid("delivery")
        evidence = delivery.payload_evidence
        valid = True
        if evidence.kind is PayloadKind.INLINE:
            body = await self._read_inline(delivery)
            valid = (
                len(body) == evidence.size_bytes
                and "sha256:" + hashlib.sha256(body).hexdigest() == evidence.digest
            )
        elif self._reference_validator is None:
            valid = False
        else:
            external = await self._reference_validator.validate(delivery, target=target)
            if type(external) is not PayloadValidationResult:
                _invalid("reference_validator.result")
            return external
        request_fingerprint = payload_access_decision_request_fingerprint(
            delivery, target=target,
        )
        return PayloadValidationResult(
            valid=valid,
            evidence_fingerprint=evidence.evidence_fingerprint,
            object_id=evidence.object_id,
            object_version=evidence.object_version,
            checksum=evidence.checksum,
            tenant_id=delivery.tenant_id,
            request_binding_fingerprint=delivery.policy_decision.request_fingerprint,
            target_binding_fingerprint=delivery.target_fingerprint,
            target_permission_snapshot_reference=target.access_decision_reference,
            access_decision_request_fingerprint=request_fingerprint,
            target_access_decision_reference=(
                "sha256:" + hashlib.sha256(
                    ("inline-access:" + request_fingerprint).encode()
                ).hexdigest()
            ),
        )

    async def resolve(self, delivery: DeliveryRecord) -> OutboundDeliveryMaterial:
        if not isinstance(delivery, DeliveryRecord):
            _invalid("delivery")
        evidence = delivery.payload_evidence
        if evidence.kind is PayloadKind.INLINE:
            body = await self._read_inline(delivery)
            if evidence.media_type == "application/json":
                try:
                    value = json.loads(body)
                except (UnicodeError, ValueError, json.JSONDecodeError):
                    _invalid("inline.body")
            elif evidence.media_type == "application/octet-stream":
                value = {
                    "encoding": "base64",
                    "data": base64.b64encode(body).decode("ascii"),
                }
            else:
                _invalid("inline.media_type")
            payload = PayloadGroup(
                mode="inline", inline=value, content_type=evidence.media_type,
                size_bytes=evidence.size_bytes, checksum=evidence.checksum,
            )
        else:
            payload = PayloadGroup(
                mode="reference",
                payload_ref={
                    "object_id": evidence.object_id,
                    "version": evidence.object_version,
                    "checksum": evidence.checksum,
                    "tenant_id": delivery.tenant_id,
                },
                content_type=evidence.media_type,
                size_bytes=evidence.size_bytes,
                checksum=evidence.checksum,
                version=evidence.object_version,
            )
        return OutboundDeliveryMaterial(
            payload=payload,
            evidence_fingerprint=evidence.evidence_fingerprint,
        )

    async def _read_inline(self, delivery: DeliveryRecord) -> bytes:
        evidence = delivery.payload_evidence
        if evidence.body_ref is None:
            _invalid("inline.body_ref")
        scope = delivery_scope(
            delivery.tenant_id,
            delivery.authority_bucket_id,
            layout_generation=delivery.authority_layout_generation,
            caller="delivery.payload_authority",
        )
        namespace = scope.namespace
        result = await self._store.read(
            scope=scope,
            key=StateKey(
                namespace=namespace, object_type="payload_body",
                object_id=_digest_key(evidence.body_ref),
            ),
            consistency=StateConsistency.LINEARIZABLE,
        )
        if result.record is None:
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_payload_authority",
                "reason": "payload_body_missing",
            })
        try:
            values = json.loads(result.record.document.payload)
            if (values["schema_version"] != "delivery-payload-body-1"
                    or values["body_ref"] != evidence.body_ref
                    or values["digest"] != evidence.digest
                    or values["size_bytes"] != evidence.size_bytes):
                raise ValueError
            body = base64.b64decode(values["body_base64"], validate=True)
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_payload_authority",
                "reason": "payload_body_malformed",
            }) from None
        return body


def _digest_key(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _invalid(field: str):
    raise NsValidationError(
        "Delivery payload authority value is invalid.",
        details={"component": "delivery_payload_authority", "field": field},
    )


__all__ = ("StateStoreDeliveryPayloadAuthority",)
