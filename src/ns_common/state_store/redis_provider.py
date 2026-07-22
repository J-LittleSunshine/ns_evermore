# -*- coding: utf-8 -*-
"""Production standalone Redis/Valkey provider for the P08 StateStore contract."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import inspect
import json
import math
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from ns_common.exceptions import (
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreUnavailableError,
    NsRuntimeStateStoreVersionMismatchError,
    NsValidationError,
)
from ns_common.time import Clock

from .authority import StateAccessScope, StateNamespace, StateStoreCapabilities
from .model import (
    StateAppendResult,
    StateAssertion,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateReadResult,
    StateRecord,
    StateRevision,
    StateScanResult,
    StateStoreHealth,
    StateStoreHealthStatus,
    StateTransaction,
    StateTransactionResult,
)
from .store import StateStore


_NAMESPACE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}")
_ENVIRONMENT_PATTERN = re.compile(r"[A-Z_][A-Z0-9_]{0,127}")
_DOMAIN_ERROR_PREFIX = "NS_STATE|"
_MAX_ENDPOINT_LENGTH = 2048
_MAX_USERNAME_LENGTH = 128
_FORBIDDEN_TEXT_CHARACTERS = frozenset({"\0", "\r", "\n"})


class StateStorePasswordSource(ABC):
    """Resolve a secret without making it part of config or provider repr."""

    @abstractmethod
    def resolve(self) -> str | None:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{type(self).__name__}(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class NoStateStorePassword(StateStorePasswordSource):
    def resolve(self) -> None:
        return None


@dataclass(frozen=True, slots=True, repr=False)
class EnvironmentStateStorePassword(StateStorePasswordSource):
    variable_name: str
    environ: Mapping[str, str] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if (
            type(self.variable_name) is not str
            or _ENVIRONMENT_PATTERN.fullmatch(self.variable_name) is None
        ):
            _invalid("password_source.environment")

    def resolve(self) -> str:
        environ = os.environ if self.environ is None else self.environ
        value = environ.get(self.variable_name)
        if not isinstance(value, str) or not value:
            raise NsRuntimeStateStoreUnavailableError(
                details={
                    "component": "state_store_provider",
                    "operation": "resolve_secret",
                    "reason": "environment_secret_unavailable",
                },
            )
        return value


@dataclass(frozen=True, slots=True, repr=False)
class FileStateStorePassword(StateStorePasswordSource):
    path: Path = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path) or not self.path.is_absolute():
            _invalid("password_source.file")

    def resolve(self) -> str:
        try:
            value = self.path.read_text(encoding="utf-8").rstrip("\r\n")
        except OSError:
            raise NsRuntimeStateStoreUnavailableError(
                details={
                    "component": "state_store_provider",
                    "operation": "resolve_secret",
                    "reason": "file_secret_unavailable",
                },
            ) from None
        if not value:
            raise NsRuntimeStateStoreUnavailableError(
                details={
                    "component": "state_store_provider",
                    "operation": "resolve_secret",
                    "reason": "file_secret_empty",
                },
            )
        return value


def password_source_from_reference(reference: str) -> StateStorePasswordSource:
    if type(reference) is not str:
        _invalid("password_source.reference")
    if reference == "none":
        return NoStateStorePassword()
    if isinstance(reference, str) and reference.startswith("env:"):
        return EnvironmentStateStorePassword(variable_name=reference[4:])
    if isinstance(reference, str) and reference.startswith("file:"):
        return FileStateStorePassword(path=Path(reference[5:]))
    _invalid("password_source.reference")


@dataclass(frozen=True, slots=True, kw_only=True)
class RedisStateStoreOptions:
    backend: str
    endpoint: str = field(repr=False)
    username: str = field(default="", repr=False)
    password_source: StateStorePasswordSource = field(repr=False)
    namespace: str
    operation_timeout_seconds: float

    def __post_init__(self) -> None:
        if type(self.backend) is not str or self.backend not in {"redis", "valkey"}:
            _invalid("options.backend")
        if (
            type(self.username) is not str
            or len(self.username) > _MAX_USERNAME_LENGTH
            or any(character in self.username for character in _FORBIDDEN_TEXT_CHARACTERS)
        ):
            _invalid("options.username")
        if not isinstance(self.password_source, StateStorePasswordSource):
            _invalid("options.password_source")
        if (
            type(self.namespace) is not str
            or _NAMESPACE_PATTERN.fullmatch(self.namespace) is None
        ):
            _invalid("options.namespace")
        if (
            type(self.operation_timeout_seconds) not in {int, float}
            or not math.isfinite(self.operation_timeout_seconds)
            or self.operation_timeout_seconds <= 0
        ):
            _invalid("options.operation_timeout_seconds")
        _parse_endpoint(self.backend, self.endpoint)


_TRANSACTION_SCRIPT = r"""
local mutations = cjson.decode(ARGV[1])
local committed_at = ARGV[2]

local function domain_error(kind, reason, index)
    return redis.error_reply('NS_STATE|' .. kind .. '|' .. reason .. '|' .. index)
end

for index, mutation in ipairs(mutations) do
    local key = KEYS[index + 1]
    local exists = redis.call('EXISTS', key) == 1
    if mutation.kind == 'create' then
        if exists then
            return domain_error('conflict', 'expected_absent', index)
        end
        if mutation.document.state_version ~= '1' then
            return domain_error('version', 'initial_state_version', index)
        end
    else
        if not exists then
            return domain_error('conflict', 'missing', index)
        end
        if redis.call('HGET', key, 'revision') ~= mutation.expected_revision then
            return domain_error('conflict', 'revision', index)
        end
        if mutation.expected_state_version ~= '' and
           redis.call('HGET', key, 'state_version') ~= mutation.expected_state_version then
            return domain_error('conflict', 'state_version', index)
        end
        if mutation.expected_epoch ~= '' and
           redis.call('HGET', key, 'epoch') ~= mutation.expected_epoch then
            return domain_error('conflict', 'epoch', index)
        end
        if mutation.kind == 'replace' then
            if redis.call('HGET', key, 'schema_name') ~= mutation.document.schema_name or
               redis.call('HGET', key, 'schema_version') ~= mutation.document.schema_version then
                return domain_error('version', 'schema', index)
            end
            local current_version = tonumber(redis.call('HGET', key, 'state_version'))
            local next_version = tonumber(mutation.document.state_version)
            if next_version ~= current_version + 1 then
                return domain_error('version', 'state_version', index)
            end
        end
    end
end

local results = {}
for index, mutation in ipairs(mutations) do
    local key = KEYS[index + 1]
    local index_key = KEYS[#mutations + index + 1]
    if mutation.kind == 'delete' then
        redis.call('DEL', key)
        redis.call('ZREM', index_key, key)
        results[index] = {present = '0'}
    else
        local revision = tostring(redis.call('INCR', KEYS[1]))
        local document = mutation.document
        redis.call(
            'HSET', key,
            'schema_name', document.schema_name,
            'schema_version', document.schema_version,
            'state_version', document.state_version,
            'epoch', document.epoch,
            'payload', document.payload,
            'revision', revision,
            'committed_at', committed_at,
            'namespace_digest', mutation.key.namespace_digest,
            'object_type', mutation.key.object_type,
            'object_id', mutation.key.object_id
        )
        redis.call('ZADD', index_key, 0, key)
        results[index] = {
            present = '1',
            schema_name = document.schema_name,
            schema_version = document.schema_version,
            state_version = document.state_version,
            epoch = document.epoch,
            payload = document.payload,
            revision = revision,
            committed_at = committed_at
        }
    end
end
return cjson.encode(results)
"""


_APPEND_SCRIPT = r"""
local assertion = cjson.decode(ARGV[1])
local document = cjson.decode(ARGV[2])
local committed_at = ARGV[3]
local position = redis.call('LLEN', KEYS[2])

local function domain_error(reason)
    return redis.error_reply('NS_STATE|conflict|' .. reason .. '|1')
end

if assertion.present == '1' then
    if assertion.expect_absent == '1' then
        if position ~= 0 then
            return domain_error('expected_absent')
        end
    else
        if position == 0 then
            return domain_error('missing')
        end
        if redis.call('HGET', KEYS[3], 'revision') ~= assertion.expected_revision then
            return domain_error('revision')
        end
        if assertion.expected_state_version ~= '' and
           redis.call('HGET', KEYS[3], 'state_version') ~= assertion.expected_state_version then
            return domain_error('state_version')
        end
        if assertion.expected_epoch ~= '' and
           redis.call('HGET', KEYS[3], 'epoch') ~= assertion.expected_epoch then
            return domain_error('epoch')
        end
    end
end

local revision = tostring(redis.call('INCR', KEYS[1]))
local entry = cjson.encode({
    schema_name = document.schema_name,
    schema_version = document.schema_version,
    state_version = document.state_version,
    epoch = document.epoch,
    payload = document.payload,
    revision = revision,
    committed_at = committed_at
})
position = redis.call('RPUSH', KEYS[2], entry)
redis.call(
    'HSET', KEYS[3],
    'revision', revision,
    'state_version', document.state_version,
    'epoch', document.epoch
)
return cjson.encode({revision = revision, position = tostring(position), committed_at = committed_at})
"""


class RedisValkeyStateStore(StateStore):
    """One-client standalone provider; cluster/Sentinel/lease semantics are absent."""

    def __init__(
        self,
        *,
        options: RedisStateStoreOptions,
        capabilities: StateStoreCapabilities,
        clock: Clock,
    ) -> None:
        if not isinstance(options, RedisStateStoreOptions):
            _invalid("provider.options")
        super().__init__(capabilities=capabilities, clock=clock)
        self._options = options
        self._prefix = options.namespace.rstrip(":") + ":"
        self._client: object | None = None
        self._response_error_type: type[Exception] | None = None
        self._timeout_error_type: type[Exception] | None = None

    def __repr__(self) -> str:
        return (
            f"RedisValkeyStateStore(backend={self._options.backend!r}, "
            f"namespace={self._options.namespace!r}, state={self.state.value!r})"
        )

    async def _open(self) -> None:
        client_type, response_error, timeout_error, retry = self._load_driver()
        parsed = _parse_endpoint(self._options.backend, self._options.endpoint)
        try:
            password = self._options.password_source.resolve()
            if inspect.iscoroutine(password):
                try:
                    password.close()
                except BaseException:
                    pass
            if password is not None and (
                type(password) is not str or not password
            ):
                raise NsRuntimeStateStoreUnavailableError(
                    details={
                        "component": "state_store_provider",
                        "operation": "resolve_secret",
                        "reason": "secret_value_invalid",
                    },
                )
            client = client_type(
                host=parsed.hostname,
                port=parsed.port or 6379,
                db=int((parsed.path or "/0").removeprefix("/")),
                username=self._options.username or None,
                password=password,
                ssl=parsed.scheme in {"rediss", "valkeys"},
                socket_timeout=self._options.operation_timeout_seconds,
                socket_connect_timeout=self._options.operation_timeout_seconds,
                retry=retry,
                decode_responses=False,
                client_name="ns-runtime-state-store",
                protocol=2,
            )
            self._client = client
            self._response_error_type = response_error
            self._timeout_error_type = timeout_error
            result = await self._execute(client.ping())
            if result is not True:
                raise RuntimeError("provider ping rejected")
        except BaseException:
            client = self._client
            self._client = None
            if client is not None:
                try:
                    await client.aclose()  # type: ignore[attr-defined]
                except BaseException:
                    pass
            raise

    async def _close(self) -> None:
        client = self._client
        if client is None:
            return
        await self._execute(client.aclose())  # type: ignore[attr-defined]
        self._client = None

    async def _read(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        consistency: StateConsistency,
        minimum_revision: StateRevision | None,
    ) -> StateReadResult:
        del scope, consistency
        client = self._require_client()
        raw = await self._execute(
            client.hgetall(self._record_key(key)),  # type: ignore[attr-defined]
        )
        record = None if not raw else self._record_from_hash(key, raw)
        stale = False
        if minimum_revision is not None:
            minimum = _revision_number(minimum_revision)
            current = (
                _revision_number(record.revision) if record is not None else None
            )
            stale = minimum is None or current is None or current < minimum
        return StateReadResult(
            record=record,
            observed_at=self._clock.utc_now(),
            stale=stale,
        )

    async def _compare_and_set(
        self,
        *,
        scope: StateAccessScope,
        mutation: StateMutation,
    ) -> StateRecord | None:
        result = await self._execute_transaction(
            scope=scope,
            mutations=(mutation,),
        )
        return result.records[0]

    async def _scan(
        self,
        *,
        scope: StateAccessScope,
        object_type: str,
        cursor: str | None,
        limit: int,
    ) -> StateScanResult:
        client = self._require_client()
        offset = 0 if cursor is None else int(cursor)
        index_key = self._index_key(scope.namespace, object_type)
        raw_keys = await self._execute(
            client.zrange(index_key, offset, offset + limit - 1),  # type: ignore[attr-defined]
        )
        if not isinstance(raw_keys, (list, tuple)):
            raise RuntimeError("provider scan result invalid")
        records: list[StateRecord] = []
        expected_namespace_digest = _namespace_digest(scope.namespace)
        for raw_key in raw_keys:
            values = await self._execute(
                client.hgetall(raw_key),  # type: ignore[attr-defined]
            )
            if not values:
                continue
            if not isinstance(values, dict):
                raise RuntimeError("provider scan record invalid")
            text_values = {
                _as_text(field): _as_text(value)
                for field, value in values.items()
            }
            if (
                text_values.get("namespace_digest") != expected_namespace_digest
                or text_values.get("object_type") != object_type
            ):
                raise RuntimeError("provider scan scope invalid")
            key = StateKey(
                namespace=scope.namespace,
                object_type=object_type,
                object_id=text_values["object_id"],
            )
            records.append(self._record_from_wire(key, text_values))
        total = await self._execute(
            client.zcard(index_key),  # type: ignore[attr-defined]
        )
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise RuntimeError("provider scan count invalid")
        next_offset = offset + len(raw_keys)
        return StateScanResult(
            records=tuple(records),
            next_cursor=(str(next_offset) if next_offset < total else None),
            observed_at=self._clock.utc_now(),
        )

    async def _transact(
        self,
        transaction: StateTransaction,
    ) -> StateTransactionResult:
        return await self._execute_transaction(
            scope=transaction.scope,
            mutations=transaction.mutations,
        )

    async def _append(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        document: StateDocument,
        assertion: StateAssertion | None,
    ) -> StateAppendResult:
        del scope
        client = self._require_client()
        committed_at = self._clock.utc_now()
        assertion_payload = _append_assertion_payload(assertion)
        raw = await self._execute(
            client.eval(  # type: ignore[attr-defined]
                _APPEND_SCRIPT,
                3,
                self._revision_key,
                self._append_key(key),
                self._append_meta_key(key),
                _canonical_json(assertion_payload),
                _canonical_json(_document_payload(document)),
                committed_at.isoformat(),
            ),
        )
        values = _decode_json_result(raw)
        return StateAppendResult(
            revision=StateRevision._issue(f"redis:{values['revision']}"),
            position=int(values["position"]),
            committed_at=datetime.fromisoformat(values["committed_at"]),
        )

    async def _health(self) -> StateStoreHealth:
        client = self._require_client()
        result = await self._execute(client.ping())  # type: ignore[attr-defined]
        return StateStoreHealth(
            status=(
                StateStoreHealthStatus.READY
                if result is True
                else StateStoreHealthStatus.UNAVAILABLE
            ),
            checked_at=self._clock.utc_now(),
            contract_generation=self.capabilities().contract_generation,
        )

    async def _execute_transaction(
        self,
        *,
        scope: StateAccessScope,
        mutations: tuple[StateMutation, ...],
    ) -> StateTransactionResult:
        del scope
        client = self._require_client()
        committed_at = self._clock.utc_now()
        payload = tuple(_mutation_payload(mutation) for mutation in mutations)
        record_keys = tuple(
            self._record_key(mutation.key) for mutation in mutations
        )
        index_keys = tuple(
            self._index_key(mutation.key.namespace, mutation.key.object_type)
            for mutation in mutations
        )
        keys = (self._revision_key,) + record_keys + index_keys
        raw = await self._execute(
            client.eval(  # type: ignore[attr-defined]
                _TRANSACTION_SCRIPT,
                len(keys),
                *keys,
                _canonical_json(payload),
                committed_at.isoformat(),
            ),
        )
        values = _decode_json_result(raw)
        if not isinstance(values, list) or len(values) != len(mutations):
            raise RuntimeError("provider transaction result invalid")
        records: list[StateRecord | None] = []
        for mutation, value in zip(mutations, values):
            if not isinstance(value, dict) or value.get("present") not in {"0", "1"}:
                raise RuntimeError("provider mutation result invalid")
            records.append(
                None
                if value["present"] == "0"
                else self._record_from_wire(mutation.key, value)
            )
        return StateTransactionResult(records=tuple(records))

    async def _execute(self, awaitable: object) -> object:
        try:
            completed, value = await asyncio.wait_for(
                _capture_non_cancel_baseexception(awaitable),
                timeout=self._options.operation_timeout_seconds,
            )
            if not completed:
                raise value  # type: ignore[misc]
            return value
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            raise
        except Exception as error:
            timeout_type = self._timeout_error_type
            if timeout_type is not None and isinstance(error, timeout_type):
                raise asyncio.TimeoutError from None
            response_type = self._response_error_type
            if response_type is not None and isinstance(error, response_type):
                self._raise_domain_error(error)
                raise RuntimeError("provider command rejected") from None
            raise

    @staticmethod
    def _raise_domain_error(error: Exception) -> None:
        text = str(error)
        marker = text.find(_DOMAIN_ERROR_PREFIX)
        if marker < 0:
            return
        parts = text[marker:].split("|", 3)
        if len(parts) != 4:
            return
        _, kind, reason, index = parts
        details = {
            "component": "state_store_provider",
            "reason": reason,
            "mutation_index": index,
        }
        if kind == "conflict":
            raise NsRuntimeStateStoreConflictError(details=details) from None
        if kind == "version":
            raise NsRuntimeStateStoreVersionMismatchError(details=details) from None

    def _load_driver(
        self,
    ) -> tuple[type[object], type[Exception], type[Exception], object]:
        try:
            if self._options.backend == "redis":
                from redis.asyncio import Redis
                from redis.asyncio.retry import Retry
                from redis.backoff import NoBackoff
                from redis.exceptions import ResponseError, TimeoutError

                return Redis, ResponseError, TimeoutError, Retry(NoBackoff(), 0)
            from valkey.asyncio import Valkey
            from valkey.asyncio.retry import Retry
            from valkey.backoff import NoBackoff
            from valkey.exceptions import ResponseError, TimeoutError

            return Valkey, ResponseError, TimeoutError, Retry(NoBackoff(), 0)
        except ImportError:
            raise NsRuntimeStateStoreUnavailableError(
                details={
                    "component": "state_store_provider",
                    "operation": "open",
                    "reason": "driver_unavailable",
                },
            ) from None

    def _require_client(self) -> object:
        if self._client is None:
            raise RuntimeError("provider client unavailable")
        return self._client

    @property
    def _revision_key(self) -> str:
        return self._prefix + "meta:revision"

    def _record_key(self, key: StateKey) -> str:
        return self._prefix + "record:" + _state_key_digest(key)

    def _index_key(self, namespace: StateNamespace, object_type: str) -> str:
        return (
            self._prefix + "index:" + _namespace_digest(namespace)
            + ":" + hashlib.sha256(object_type.encode("utf-8")).hexdigest()
        )

    def _append_key(self, key: StateKey) -> str:
        return self._prefix + "append:" + _state_key_digest(key)

    def _append_meta_key(self, key: StateKey) -> str:
        return self._prefix + "append-meta:" + _state_key_digest(key)

    @staticmethod
    def _record_from_hash(key: StateKey, raw: object) -> StateRecord:
        if not isinstance(raw, dict):
            raise RuntimeError("provider record invalid")
        values = {
            _as_text(field): _as_text(value)
            for field, value in raw.items()
        }
        return RedisValkeyStateStore._record_from_wire(key, values)

    @staticmethod
    def _record_from_wire(key: StateKey, values: Mapping[str, object]) -> StateRecord:
        epoch_text = _as_text(values["epoch"])
        return StateRecord(
            key=key,
            document=StateDocument(
                schema_name=_as_text(values["schema_name"]),
                schema_version=int(_as_text(values["schema_version"])),
                state_version=int(_as_text(values["state_version"])),
                epoch=None if epoch_text == "" else int(epoch_text),
                payload=base64.b64decode(
                    _as_text(values["payload"]), validate=True,
                ),
            ),
            revision=StateRevision._issue(
                f"redis:{_as_text(values['revision'])}",
            ),
            committed_at=datetime.fromisoformat(
                _as_text(values["committed_at"]),
            ),
        )


def _parse_endpoint(backend: str, endpoint: object):
    if (
        type(endpoint) is not str
        or not endpoint
        or len(endpoint) > _MAX_ENDPOINT_LENGTH
        or endpoint != endpoint.strip()
        or any(character in endpoint for character in _FORBIDDEN_TEXT_CHARACTERS)
    ):
        _invalid("options.endpoint")
    try:
        parsed = urlparse(endpoint)
        hostname = parsed.hostname
    except ValueError:
        _invalid("options.endpoint")
    allowed = (
        {"redis", "rediss"}
        if backend == "redis"
        else {"redis", "rediss", "valkey", "valkeys"}
    )
    if (
        parsed.scheme not in allowed
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.params
    ):
        _invalid("options.endpoint")
    try:
        port = parsed.port
        path = parsed.path or "/0"
        if not re.fullmatch(r"/[0-9]+", path):
            raise ValueError
        database = int(path[1:])
    except (TypeError, ValueError):
        _invalid("options.endpoint")
    if port is not None and not 0 < port <= 65535:
        _invalid("options.endpoint")
    if database < 0:
        _invalid("options.endpoint")
    return parsed


async def _capture_non_cancel_baseexception(
    awaitable: object,
) -> tuple[bool, object]:
    try:
        return True, await awaitable  # type: ignore[misc]
    except asyncio.CancelledError:
        raise
    except BaseException as error:
        return False, error


def _state_key_digest(key: StateKey) -> str:
    namespace = key.namespace
    value = {
        "namespace": _namespace_payload(namespace),
        "object_type": key.object_type,
        "object_id": key.object_id,
    }
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _namespace_payload(namespace: StateNamespace) -> dict[str, object]:
    return {
        "kind": namespace.kind.value,
        "domain": namespace.domain,
        "tenant_id": namespace.tenant_id,
        "runtime_id": namespace.runtime_id,
        "plugin_name": namespace.plugin_name,
    }


def _namespace_digest(namespace: StateNamespace) -> str:
    return hashlib.sha256(_canonical_json(_namespace_payload(namespace))).hexdigest()


def _document_payload(document: StateDocument) -> dict[str, str]:
    return {
        "schema_name": document.schema_name,
        "schema_version": str(document.schema_version),
        "state_version": str(document.state_version),
        "epoch": "" if document.epoch is None else str(document.epoch),
        "payload": base64.b64encode(document.payload).decode("ascii"),
    }


def _mutation_payload(mutation: StateMutation) -> dict[str, object]:
    assertion = mutation.assertion
    expected_revision = ""
    if assertion.expected_revision is not None:
        revision_number = _revision_number(assertion.expected_revision)
        expected_revision = "invalid" if revision_number is None else str(revision_number)
    return {
        "kind": mutation.kind.value,
        "key": {
            "namespace_digest": _namespace_digest(mutation.key.namespace),
            "object_type": mutation.key.object_type,
            "object_id": mutation.key.object_id,
        },
        "expected_revision": expected_revision,
        "expected_state_version": (
            "" if assertion.expected_state_version is None
            else str(assertion.expected_state_version)
        ),
        "expected_epoch": (
            "" if assertion.expected_epoch is None else str(assertion.expected_epoch)
        ),
        "document": (
            None if mutation.kind is StateMutationKind.DELETE
            else _document_payload(mutation.document)  # type: ignore[arg-type]
        ),
    }


def _append_assertion_payload(assertion: StateAssertion | None) -> dict[str, str]:
    if assertion is None:
        return {
            "present": "0", "expect_absent": "0", "expected_revision": "",
            "expected_state_version": "", "expected_epoch": "",
        }
    revision = ""
    if assertion.expected_revision is not None:
        number = _revision_number(assertion.expected_revision)
        revision = "invalid" if number is None else str(number)
    return {
        "present": "1",
        "expect_absent": "1" if assertion.expect_absent else "0",
        "expected_revision": revision,
        "expected_state_version": (
            "" if assertion.expected_state_version is None
            else str(assertion.expected_state_version)
        ),
        "expected_epoch": (
            "" if assertion.expected_epoch is None else str(assertion.expected_epoch)
        ),
    }


def _revision_number(revision: StateRevision) -> int | None:
    token = revision._provider_token()
    if not token.startswith("redis:"):
        return None
    try:
        value = int(token[6:])
    except ValueError:
        return None
    return value if value > 0 else None


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _decode_json_result(value: object):
    if not isinstance(value, (bytes, bytearray)):
        raise RuntimeError("provider response invalid")
    try:
        return json.loads(bytes(value))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("provider response invalid") from None


def _as_text(value: object) -> str:
    if isinstance(value, bytes):
        try:
            return value.decode("ascii")
        except UnicodeDecodeError:
            raise RuntimeError("provider field invalid") from None
    if isinstance(value, str):
        return value
    raise RuntimeError("provider field invalid")


def _invalid(field_name: str):
    raise NsValidationError(
        "Redis/Valkey StateStore configuration is invalid.",
        details={"component": "state_store_provider", "field": field_name},
    )


__all__ = (
    "EnvironmentStateStorePassword",
    "FileStateStorePassword",
    "NoStateStorePassword",
    "RedisStateStoreOptions",
    "RedisValkeyStateStore",
    "StateStorePasswordSource",
    "password_source_from_reference",
)
