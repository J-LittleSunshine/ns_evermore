# -*- coding: utf-8 -*-
"""Strict, pickle-free wire codecs for the authority broker.

Only JSON primitives cross the application IPC boundary.  This module is
deliberately free of dynamic type lookup, import hooks, object callbacks, and
generic ``__dict__`` serialization.
"""

from __future__ import annotations

import base64
import json
import math
from datetime import datetime, timezone
from typing import Callable, Mapping

from ns_common.exceptions import NsValidationError
from ns_common.state_store import (
    StateAppendResult,
    StateAssertion,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateNamespace,
    StateNamespaceKind,
    StateOrderedIndexCursor,
    StateOrderedIndexEntry,
    StateOrderedIndexKey,
    StateOrderedIndexMutation,
    StateOrderedIndexMutationKind,
    StateOrderedIndexReadAssertion,
    StateOrderedIndexReadResult,
    StateReadResult,
    StateRecord,
    StateRecordReadAssertion,
    StateRevision,
    StateStoreHealth,
    StateStoreHealthStatus,
    StateTransaction,
    StateTransitionLogAppend,
)


WIRE_VERSION = 1
MAX_FRAME_BYTES = 8 * 1024 * 1024
MAX_STRING_CHARS = 2 * 1024 * 1024
MAX_CONTAINER_ITEMS = 20_000
MAX_NESTING_DEPTH = 64

JsonScalar = None | bool | int | float | str
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def encode_frame(value: JsonValue) -> bytes:
    _validate_json_tree(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError):
        _invalid("frame.value")
    if len(encoded) > MAX_FRAME_BYTES:
        _invalid("frame.too_large")
    return encoded


def decode_frame(raw: bytes) -> JsonValue:
    if type(raw) is not bytes or not raw or len(raw) > MAX_FRAME_BYTES:
        _invalid("frame.size")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_fields,
            parse_constant=_reject_non_finite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        _invalid("frame.json")
    _validate_json_tree(value)
    return value


def require_object(
    value: JsonValue,
    *,
    fields: frozenset[str] | set[str],
    field: str,
) -> dict[str, JsonValue]:
    if type(value) is not dict or set(value) != set(fields):
        _invalid(field)
    return value


def encode_bytes(value: bytes) -> str:
    if type(value) is not bytes:
        _invalid("bytes")
    return base64.b64encode(value).decode("ascii")


def decode_bytes(value: JsonValue, *, field: str) -> bytes:
    if type(value) is not str:
        _invalid(field)
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, UnicodeError):
        _invalid(field)


def encode_time(value: datetime) -> str:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        _invalid("time")
    return value.astimezone(timezone.utc).isoformat()


def decode_time(value: JsonValue, *, field: str) -> datetime:
    if type(value) is not str:
        _invalid(field)
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _invalid(field)
    if result.tzinfo is None or result.utcoffset() is None:
        _invalid(field)
    return result.astimezone(timezone.utc)


def encode_namespace(value: StateNamespace) -> dict[str, JsonValue]:
    if type(value) is not StateNamespace:
        _invalid("namespace")
    return {
        "kind": value.kind.value,
        "domain": value.domain,
        "tenant_id": value.tenant_id,
        "runtime_id": value.runtime_id,
        "plugin_name": value.plugin_name,
    }


def decode_namespace(value: JsonValue) -> StateNamespace:
    fields = require_object(
        value,
        fields={
            "kind", "domain", "tenant_id", "runtime_id", "plugin_name",
        },
        field="namespace",
    )
    try:
        return StateNamespace(
            kind=StateNamespaceKind(_string(fields["kind"], "namespace.kind")),
            domain=_string(fields["domain"], "namespace.domain"),
            tenant_id=_optional_string(
                fields["tenant_id"], "namespace.tenant_id",
            ),
            runtime_id=_optional_string(
                fields["runtime_id"], "namespace.runtime_id",
            ),
            plugin_name=_optional_string(
                fields["plugin_name"], "namespace.plugin_name",
            ),
        )
    except (ValueError, NsValidationError):
        _invalid("namespace")


def encode_key(value: StateKey) -> dict[str, JsonValue]:
    if type(value) is not StateKey:
        _invalid("key")
    return {
        "namespace": encode_namespace(value.namespace),
        "object_type": value.object_type,
        "object_id": value.object_id,
    }


def decode_key(value: JsonValue) -> StateKey:
    fields = require_object(
        value,
        fields={"namespace", "object_type", "object_id"},
        field="key",
    )
    return StateKey(
        namespace=decode_namespace(fields["namespace"]),
        object_type=_string(fields["object_type"], "key.object_type"),
        object_id=_string(fields["object_id"], "key.object_id"),
    )


def encode_document(value: StateDocument) -> dict[str, JsonValue]:
    if type(value) is not StateDocument:
        _invalid("document")
    return {
        "schema_name": value.schema_name,
        "schema_version": value.schema_version,
        "state_version": value.state_version,
        "payload_base64": encode_bytes(value.payload),
        "epoch": value.epoch,
    }


def decode_document(value: JsonValue) -> StateDocument:
    fields = require_object(
        value,
        fields={
            "schema_name", "schema_version", "state_version",
            "payload_base64", "epoch",
        },
        field="document",
    )
    epoch = fields["epoch"]
    if epoch is not None:
        epoch = _integer(epoch, "document.epoch", minimum=0)
    return StateDocument(
        schema_name=_string(fields["schema_name"], "document.schema_name"),
        schema_version=_integer(
            fields["schema_version"], "document.schema_version", minimum=1,
        ),
        state_version=_integer(
            fields["state_version"], "document.state_version", minimum=1,
        ),
        payload=decode_bytes(
            fields["payload_base64"], field="document.payload_base64",
        ),
        epoch=epoch,  # type: ignore[arg-type]
    )


def encode_revision(value: StateRevision | None) -> JsonValue:
    if value is None:
        return None
    if type(value) is not StateRevision:
        _invalid("revision")
    return value._provider_token()


def decode_revision(value: JsonValue, *, field: str) -> StateRevision | None:
    if value is None:
        return None
    return StateRevision._issue(_string(value, field))


def encode_assertion(value: StateAssertion) -> dict[str, JsonValue]:
    if type(value) is not StateAssertion:
        _invalid("assertion")
    return {
        "expect_absent": value.expect_absent,
        "expected_revision": encode_revision(value.expected_revision),
        "expected_state_version": value.expected_state_version,
        "expected_epoch": value.expected_epoch,
    }


def decode_assertion(value: JsonValue) -> StateAssertion:
    fields = require_object(
        value,
        fields={
            "expect_absent", "expected_revision",
            "expected_state_version", "expected_epoch",
        },
        field="assertion",
    )
    expect_absent = _boolean(
        fields["expect_absent"], "assertion.expect_absent",
    )
    if expect_absent:
        if any(fields[name] is not None for name in (
            "expected_revision", "expected_state_version", "expected_epoch",
        )):
            _invalid("assertion.absent")
        return StateAssertion.absent()
    revision = decode_revision(
        fields["expected_revision"], field="assertion.expected_revision",
    )
    if revision is None:
        _invalid("assertion.expected_revision")
    state_version = _optional_positive_int(
        fields["expected_state_version"],
        "assertion.expected_state_version",
    )
    epoch = fields["expected_epoch"]
    if epoch is not None:
        epoch = _integer(epoch, "assertion.expected_epoch", minimum=0)
    return StateAssertion.matches(
        revision,
        state_version=state_version,
        epoch=epoch,  # type: ignore[arg-type]
    )


def encode_mutation(value: StateMutation) -> dict[str, JsonValue]:
    if type(value) is not StateMutation:
        _invalid("mutation")
    return {
        "key": encode_key(value.key),
        "assertion": encode_assertion(value.assertion),
        "kind": value.kind.value,
        "document": (
            None if value.document is None
            else encode_document(value.document)
        ),
    }


def decode_mutation(value: JsonValue) -> StateMutation:
    fields = require_object(
        value,
        fields={"key", "assertion", "kind", "document"},
        field="mutation",
    )
    document = fields["document"]
    try:
        return StateMutation(
            key=decode_key(fields["key"]),
            assertion=decode_assertion(fields["assertion"]),
            kind=StateMutationKind(
                _string(fields["kind"], "mutation.kind"),
            ),
            document=(
                None if document is None else decode_document(document)
            ),
        )
    except ValueError:
        _invalid("mutation.kind")


def encode_index_key(value: StateOrderedIndexKey) -> dict[str, JsonValue]:
    if type(value) is not StateOrderedIndexKey:
        _invalid("index")
    return {
        "namespace": encode_namespace(value.namespace),
        "name": value.name,
        "bucket": value.bucket,
    }


def decode_index_key(value: JsonValue) -> StateOrderedIndexKey:
    fields = require_object(
        value,
        fields={"namespace", "name", "bucket"},
        field="index",
    )
    return StateOrderedIndexKey(
        namespace=decode_namespace(fields["namespace"]),
        name=_string(fields["name"], "index.name"),
        bucket=_string(fields["bucket"], "index.bucket"),
    )


def encode_index_mutation(
    value: StateOrderedIndexMutation,
) -> dict[str, JsonValue]:
    if type(value) is not StateOrderedIndexMutation:
        _invalid("index_mutation")
    return {
        "index": encode_index_key(value.index),
        "kind": value.kind.value,
        "member": value.member,
        "score": value.score,
    }


def decode_index_mutation(value: JsonValue) -> StateOrderedIndexMutation:
    fields = require_object(
        value,
        fields={"index", "kind", "member", "score"},
        field="index_mutation",
    )
    score = fields["score"]
    if score is not None:
        score = _number(score, "index_mutation.score")
    try:
        return StateOrderedIndexMutation(
            index=decode_index_key(fields["index"]),
            kind=StateOrderedIndexMutationKind(
                _string(fields["kind"], "index_mutation.kind"),
            ),
            member=_string(fields["member"], "index_mutation.member"),
            score=score,  # type: ignore[arg-type]
        )
    except ValueError:
        _invalid("index_mutation.kind")


def encode_record_assertion(
    value: StateRecordReadAssertion,
) -> dict[str, JsonValue]:
    if type(value) is not StateRecordReadAssertion:
        _invalid("record_assertion")
    return {
        "key": encode_key(value.key),
        "expect_present": value.expect_present,
        "expected_revision": encode_revision(value.expected_revision),
        "expected_state_version": value.expected_state_version,
    }


def decode_record_assertion(value: JsonValue) -> StateRecordReadAssertion:
    fields = require_object(
        value,
        fields={
            "key", "expect_present", "expected_revision",
            "expected_state_version",
        },
        field="record_assertion",
    )
    key = decode_key(fields["key"])
    present = _boolean(
        fields["expect_present"], "record_assertion.expect_present",
    )
    if not present:
        if (
            fields["expected_revision"] is not None
            or fields["expected_state_version"] is not None
        ):
            _invalid("record_assertion.absent")
        return StateRecordReadAssertion.absent(key)
    return StateRecordReadAssertion.present(
        key,
        revision=decode_revision(
            fields["expected_revision"],
            field="record_assertion.expected_revision",
        ),
        state_version=_optional_positive_int(
            fields["expected_state_version"],
            "record_assertion.expected_state_version",
        ),
    )


def encode_index_assertion(
    value: StateOrderedIndexReadAssertion,
) -> dict[str, JsonValue]:
    if type(value) is not StateOrderedIndexReadAssertion:
        _invalid("index_assertion")
    return {
        "index": encode_index_key(value.index),
        "member": value.member,
        "expect_present": value.expect_present,
        "expected_score": value.expected_score,
    }


def decode_index_assertion(
    value: JsonValue,
) -> StateOrderedIndexReadAssertion:
    fields = require_object(
        value,
        fields={
            "index", "member", "expect_present", "expected_score",
        },
        field="index_assertion",
    )
    index = decode_index_key(fields["index"])
    member = _string(fields["member"], "index_assertion.member")
    present = _boolean(
        fields["expect_present"], "index_assertion.expect_present",
    )
    if not present:
        if fields["expected_score"] is not None:
            _invalid("index_assertion.absent")
        return StateOrderedIndexReadAssertion.absent(index, member)
    score = fields["expected_score"]
    return StateOrderedIndexReadAssertion.present(
        index,
        member,
        score=(
            None if score is None
            else _number(score, "index_assertion.expected_score")
        ),
    )


def encode_log_append(
    value: StateTransitionLogAppend,
) -> dict[str, JsonValue]:
    if type(value) is not StateTransitionLogAppend:
        _invalid("log_append")
    return {
        "key": encode_key(value.key),
        "document": encode_document(value.document),
    }


def decode_log_append(value: JsonValue) -> StateTransitionLogAppend:
    fields = require_object(
        value,
        fields={"key", "document"},
        field="log_append",
    )
    return StateTransitionLogAppend(
        key=decode_key(fields["key"]),
        document=decode_document(fields["document"]),
    )


def encode_transaction_request(
    transaction: object,
    *,
    tenant_id: str,
    bucket_id: int,
    layout_generation: int,
) -> dict[str, JsonValue]:
    from ns_runtime.delivery_persistence import DeliveryPersistenceTransaction

    if type(transaction) is not DeliveryPersistenceTransaction:
        _invalid("transaction")
    return {
        "tenant_id": tenant_id,
        "bucket_id": bucket_id,
        "layout_generation": layout_generation,
        "mutations": [encode_mutation(value) for value in transaction.mutations],
        "record_assertions": [
            encode_record_assertion(value)
            for value in transaction.record_assertions
        ],
        "ordered_index_mutations": [
            encode_index_mutation(value)
            for value in transaction.ordered_index_mutations
        ],
        "ordered_index_assertions": [
            encode_index_assertion(value)
            for value in transaction.ordered_index_assertions
        ],
        "log_appends": [
            encode_log_append(value) for value in transaction.log_appends
        ],
    }


def decode_transaction_request(
    value: JsonValue,
    *,
    scope: object,
    expected_tenant_id: str,
    expected_bucket_id: int,
    expected_layout_generation: int,
) -> StateTransaction:
    fields = require_object(
        value,
        fields={
            "tenant_id", "bucket_id", "layout_generation", "mutations",
            "record_assertions", "ordered_index_mutations",
            "ordered_index_assertions", "log_appends",
        },
        field="transaction",
    )
    if (
        _string(fields["tenant_id"], "transaction.tenant_id")
        != expected_tenant_id
        or _integer(fields["bucket_id"], "transaction.bucket_id", minimum=0)
        != expected_bucket_id
        or _integer(
            fields["layout_generation"],
            "transaction.layout_generation",
            minimum=1,
        ) != expected_layout_generation
    ):
        _invalid("transaction.scope_injection")
    from ns_common.state_store import StateAccessScope

    if type(scope) is not StateAccessScope:
        _invalid("transaction.internal_scope")
    return StateTransaction(
        scope=scope,
        mutations=tuple(
            decode_mutation(item)
            for item in _list(fields["mutations"], "transaction.mutations")
        ),
        record_assertions=tuple(
            decode_record_assertion(item)
            for item in _list(
                fields["record_assertions"],
                "transaction.record_assertions",
            )
        ),
        ordered_index_mutations=tuple(
            decode_index_mutation(item)
            for item in _list(
                fields["ordered_index_mutations"],
                "transaction.ordered_index_mutations",
            )
        ),
        ordered_index_assertions=tuple(
            decode_index_assertion(item)
            for item in _list(
                fields["ordered_index_assertions"],
                "transaction.ordered_index_assertions",
            )
        ),
        log_appends=tuple(
            decode_log_append(item)
            for item in _list(
                fields["log_appends"], "transaction.log_appends",
            )
        ),
    )


def encode_cursor(
    value: StateOrderedIndexCursor | None,
    *,
    index_name: str,
    index_bucket: str,
) -> JsonValue:
    if value is None:
        return None
    if type(value) is not StateOrderedIndexCursor:
        _invalid("cursor")
    return {
        "member": value.member,
        "score": value.score,
        "index_name": index_name,
        "index_bucket": index_bucket,
    }


def decode_cursor(
    value: JsonValue,
    *,
    index_name: str,
    index_bucket: str,
) -> StateOrderedIndexCursor | None:
    if value is None:
        return None
    fields = require_object(
        value,
        fields={"member", "score", "index_name", "index_bucket"},
        field="cursor",
    )
    if (
        _string(fields["index_name"], "cursor.index_name") != index_name
        or _string(fields["index_bucket"], "cursor.index_bucket")
        != index_bucket
    ):
        _invalid("cursor.index_binding")
    return StateOrderedIndexCursor(
        member=_string(fields["member"], "cursor.member"),
        score=_number(fields["score"], "cursor.score"),
    )


def encode_record(value: StateRecord | None) -> JsonValue:
    if value is None:
        return None
    if type(value) is not StateRecord:
        _invalid("record")
    return {
        "key": encode_key(value.key),
        "document": encode_document(value.document),
        "revision": encode_revision(value.revision),
        "committed_at": encode_time(value.committed_at),
    }


def decode_record(value: JsonValue) -> StateRecord | None:
    if value is None:
        return None
    fields = require_object(
        value,
        fields={"key", "document", "revision", "committed_at"},
        field="record",
    )
    revision = decode_revision(fields["revision"], field="record.revision")
    if revision is None:
        _invalid("record.revision")
    return StateRecord(
        key=decode_key(fields["key"]),
        document=decode_document(fields["document"]),
        revision=revision,
        committed_at=decode_time(
            fields["committed_at"], field="record.committed_at",
        ),
    )


def encode_read_result(value: StateReadResult) -> dict[str, JsonValue]:
    if type(value) is not StateReadResult:
        _invalid("read_result")
    return {
        "record": encode_record(value.record),
        "observed_at": encode_time(value.observed_at),
        "stale": value.stale,
    }


def decode_read_result(value: JsonValue) -> StateReadResult:
    fields = require_object(
        value,
        fields={"record", "observed_at", "stale"},
        field="read_result",
    )
    return StateReadResult(
        record=decode_record(fields["record"]),
        observed_at=decode_time(
            fields["observed_at"], field="read_result.observed_at",
        ),
        stale=_boolean(fields["stale"], "read_result.stale"),
    )


def encode_transaction_result(
    records: tuple[StateRecord | None, ...],
    log_positions: tuple[int, ...],
) -> dict[str, JsonValue]:
    return {
        "records": [encode_record(value) for value in records],
        "log_positions": list(log_positions),
    }


def decode_transaction_result(
    value: JsonValue,
) -> tuple[tuple[StateRecord | None, ...], tuple[int, ...]]:
    fields = require_object(
        value,
        fields={"records", "log_positions"},
        field="transaction_result",
    )
    records = tuple(
        decode_record(item)
        for item in _list(fields["records"], "transaction_result.records")
    )
    positions = tuple(
        _integer(item, "transaction_result.log_position", minimum=1)
        for item in _list(
            fields["log_positions"], "transaction_result.log_positions",
        )
    )
    return records, positions


def encode_index_result(
    value: StateOrderedIndexReadResult,
    *,
    index_name: str,
    index_bucket: str,
) -> dict[str, JsonValue]:
    if type(value) is not StateOrderedIndexReadResult:
        _invalid("index_result")
    return {
        "entries": [
            {"member": entry.member, "score": entry.score}
            for entry in value.entries
        ],
        "observed_at": encode_time(value.observed_at),
        "total_count": value.total_count,
        "next_cursor": encode_cursor(
            value.next_cursor,
            index_name=index_name,
            index_bucket=index_bucket,
        ),
    }


def decode_index_result(
    value: JsonValue,
    *,
    index_name: str,
    index_bucket: str,
) -> StateOrderedIndexReadResult:
    fields = require_object(
        value,
        fields={"entries", "observed_at", "total_count", "next_cursor"},
        field="index_result",
    )
    entries: list[StateOrderedIndexEntry] = []
    for item in _list(fields["entries"], "index_result.entries"):
        entry = require_object(
            item,
            fields={"member", "score"},
            field="index_result.entry",
        )
        entries.append(StateOrderedIndexEntry(
            member=_string(entry["member"], "index_result.entry.member"),
            score=_number(entry["score"], "index_result.entry.score"),
        ))
    return StateOrderedIndexReadResult(
        entries=tuple(entries),
        observed_at=decode_time(
            fields["observed_at"], field="index_result.observed_at",
        ),
        total_count=_integer(
            fields["total_count"], "index_result.total_count", minimum=0,
        ),
        next_cursor=decode_cursor(
            fields["next_cursor"],
            index_name=index_name,
            index_bucket=index_bucket,
        ),
    )


def encode_append_result(value: StateAppendResult) -> dict[str, JsonValue]:
    if type(value) is not StateAppendResult:
        _invalid("append_result")
    return {
        "revision": encode_revision(value.revision),
        "position": value.position,
        "committed_at": encode_time(value.committed_at),
    }


def decode_append_result(value: JsonValue) -> StateAppendResult:
    fields = require_object(
        value,
        fields={"revision", "position", "committed_at"},
        field="append_result",
    )
    revision = decode_revision(
        fields["revision"], field="append_result.revision",
    )
    if revision is None:
        _invalid("append_result.revision")
    return StateAppendResult(
        revision=revision,
        position=_integer(
            fields["position"], "append_result.position", minimum=1,
        ),
        committed_at=decode_time(
            fields["committed_at"], field="append_result.committed_at",
        ),
    )


def encode_health(value: StateStoreHealth) -> dict[str, JsonValue]:
    if type(value) is not StateStoreHealth:
        _invalid("health")
    return {
        "status": value.status.value,
        "checked_at": encode_time(value.checked_at),
        "contract_generation": value.contract_generation,
    }


def decode_health(value: JsonValue) -> StateStoreHealth:
    fields = require_object(
        value,
        fields={"status", "checked_at", "contract_generation"},
        field="health",
    )
    try:
        status = StateStoreHealthStatus(
            _string(fields["status"], "health.status"),
        )
    except ValueError:
        _invalid("health.status")
    return StateStoreHealth(
        status=status,
        checked_at=decode_time(
            fields["checked_at"], field="health.checked_at",
        ),
        contract_generation=_integer(
            fields["contract_generation"],
            "health.contract_generation",
            minimum=1,
        ),
    )


def _reject_duplicate_fields(
    pairs: list[tuple[str, JsonValue]],
) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> float:
    del value
    raise ValueError("non-finite JSON number")


def _validate_json_tree(value: object, *, depth: int = 0) -> None:
    if depth > MAX_NESTING_DEPTH:
        _invalid("frame.depth")
    if value is None or type(value) in {bool, int}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            _invalid("frame.number")
        return
    if type(value) is str:
        if len(value) > MAX_STRING_CHARS:
            _invalid("frame.string")
        return
    if type(value) is list:
        if len(value) > MAX_CONTAINER_ITEMS:
            _invalid("frame.list")
        for item in value:
            _validate_json_tree(item, depth=depth + 1)
        return
    if type(value) is dict:
        if len(value) > MAX_CONTAINER_ITEMS:
            _invalid("frame.object")
        for key, item in value.items():
            if type(key) is not str or len(key) > 256:
                _invalid("frame.field")
            _validate_json_tree(item, depth=depth + 1)
        return
    _invalid("frame.type")


def _list(value: JsonValue, field: str) -> list[JsonValue]:
    if type(value) is not list:
        _invalid(field)
    return value


def _string(value: JsonValue, field: str) -> str:
    if type(value) is not str or not value:
        _invalid(field)
    return value


def _optional_string(value: JsonValue, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _boolean(value: JsonValue, field: str) -> bool:
    if type(value) is not bool:
        _invalid(field)
    return value


def _integer(value: JsonValue, field: str, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        _invalid(field)
    return value


def _optional_positive_int(value: JsonValue, field: str) -> int | None:
    if value is None:
        return None
    return _integer(value, field, minimum=1)


def _number(value: JsonValue, field: str) -> float:
    if type(value) not in {int, float} or not math.isfinite(value):
        _invalid(field)
    return float(value)


def _invalid(field: str) -> None:
    raise NsValidationError(
        "Authority broker wire value is invalid.",
        details={"component": "authority_broker_wire", "field": field},
    )


__all__ = (
    "MAX_FRAME_BYTES",
    "WIRE_VERSION",
    "decode_append_result",
    "decode_bytes",
    "decode_cursor",
    "decode_document",
    "decode_frame",
    "decode_health",
    "decode_index_result",
    "decode_read_result",
    "decode_time",
    "decode_transaction_request",
    "decode_transaction_result",
    "encode_append_result",
    "encode_bytes",
    "encode_cursor",
    "encode_document",
    "encode_frame",
    "encode_health",
    "encode_index_result",
    "encode_read_result",
    "encode_time",
    "encode_transaction_request",
    "encode_transaction_result",
    "require_object",
)
