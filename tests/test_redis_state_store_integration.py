# -*- coding: utf-8 -*-
"""Real standalone Redis integration evidence for P10-FIX-01."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import secrets
import shutil
import socket
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
import unittest
import uuid

try:
    import redis
    import redis.asyncio as redis_async
except ModuleNotFoundError:  # backend-only environments intentionally omit runtime drivers
    redis = None  # type: ignore[assignment]
    redis_async = None  # type: ignore[assignment]

from ns_common.exceptions import (
    NsRuntimeStateStoreClosedError,
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreIndeterminateWriteError,
    NsRuntimeStateStoreTimeoutError,
    NsRuntimeStateStoreUnavailableError,
    NsRuntimeStateStoreVersionMismatchError,
)
from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsConfig
from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
from ns_common.state_store import (
    RedisStateStoreOptions,
    RedisValkeyStateStore,
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
    StateStoreCapabilities,
    StateStoreHealthStatus,
    StateStorePasswordSource,
    StateTransaction,
)
from ns_common.time import ControlledClock
from ns_runtime.delivery import (
    AdmissionOutcome,
    AdmissionPolicyConfig,
    AdmissionRequest,
    AdmissionTrace,
    DefaultAdmissionPolicy,
    DeliveryAdmissionService,
    InlinePayload,
    StageSixAdmissionInput,
    StateStoreDeliveryAdmissionStore,
)
from ns_runtime.processor import RoutingPreparationResult
from ns_runtime.context import RuntimeContext, RuntimeDependencySlots
from ns_runtime.main import _run_service_once
from ns_runtime.service import RuntimeService

from tests.test_runtime_delivery_admission import (
    MESSAGE_ID,
    UTC_START,
    _PayloadClient,
    _ids,
    _plan,
)


@dataclass(frozen=True, slots=True, repr=False)
class _StaticPasswordSource(StateStorePasswordSource):
    value: str = field(repr=False)

    def resolve(self) -> str:
        return self.value


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
        candidate.bind(("127.0.0.1", 0))
        return int(candidate.getsockname()[1])


def _scope() -> StateAccessScope:
    namespace = StateNamespace.audit(domain="processor")
    return StateAccessScope(
        atomic_scope=StateAtomicScope(namespace=namespace, partition="contract"),
        authority=StateAuthorityKind.STRONG_AUDIT,
        caller="redis-contract-test",
        capabilities=frozenset(StateCallerCapability),
    )


def _key(scope: StateAccessScope, object_id: str) -> StateKey:
    return StateKey(
        namespace=scope.namespace,
        object_type="contract_record",
        object_id=object_id,
    )


def _document(state_version: int, payload: bytes = b"safe") -> StateDocument:
    return StateDocument(
        schema_name="contract.record",
        schema_version=1,
        state_version=state_version,
        epoch=3,
        payload=payload,
    )


def _create(key: StateKey, payload: bytes = b"safe") -> StateMutation:
    return StateMutation(
        key=key,
        assertion=StateAssertion.absent(),
        kind=StateMutationKind.CREATE,
        document=_document(1, payload),
    )


class RedisStateStoreIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    """Each run owns one requirepass standalone server and unique namespaces."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if redis is None or redis_async is None:
            raise unittest.SkipTest("runtime Redis driver is unavailable")
        server = shutil.which("redis-server")
        if server is None:
            raise unittest.SkipTest("local redis-server is unavailable")
        cls._temporary_directory = tempfile.TemporaryDirectory(
            prefix="ns-runtime-redis-state-",
        )
        cls._directory = Path(cls._temporary_directory.name)
        cls._port = _free_port()
        cls._username = ""
        cls._password = secrets.token_urlsafe(32)
        config = cls._directory / "redis.conf"
        config.write_text(
            "\n".join((
                "bind 127.0.0.1",
                f"port {cls._port}",
                "protected-mode yes",
                "daemonize no",
                "loglevel warning",
                'logfile ""',
                'save ""',
                "appendonly no",
                "databases 1",
                f"dir {cls._directory}",
                (
                    f"user default on >{cls._password} "
                    "~ns_runtime:test:* +@all -flushdb -flushall -keys"
                ),
            )) + "\n",
            encoding="utf-8",
        )
        cls._process = subprocess.Popen(
            (server, str(config)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        client = redis.Redis(
            host="127.0.0.1",
            port=cls._port,
            db=0,
            username=None,
            password=cls._password,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            protocol=2,
        )
        for _ in range(100):
            try:
                if client.ping() is True:
                    break
            except redis.RedisError:
                pass
            if cls._process.poll() is not None:
                raise RuntimeError("isolated redis-server failed to start")
            import time
            time.sleep(0.02)
        else:
            raise RuntimeError("isolated redis-server did not become ready")
        client.close()

    @classmethod
    def tearDownClass(cls) -> None:
        process = cls._process
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        cls._temporary_directory.cleanup()
        super().tearDownClass()

    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.namespace = f"ns_runtime:test:{uuid.uuid4().hex}"

    async def asyncTearDown(self) -> None:
        client = self._raw_client()
        try:
            keys = await self._scan(client, self.namespace + ":*")
            if keys:
                await client.unlink(*keys)
        finally:
            await client.aclose()

    def _raw_client(self, *, timeout: float = 1.0):
        return redis_async.Redis(
            host="127.0.0.1",
            port=self._port,
            db=0,
            username=None,
            password=self._password,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
            decode_responses=False,
            protocol=2,
        )

    async def _scan(self, client, pattern: str) -> list[bytes]:
        cursor = 0
        keys: list[bytes] = []
        while True:
            cursor, batch = await client.scan(
                cursor=cursor,
                match=pattern,
                count=500,
            )
            keys.extend(batch)
            if cursor == 0:
                return keys

    def _provider(
        self,
        *,
        backend: str = "redis",
        namespace: str | None = None,
        password: str | None = None,
        port: int | None = None,
        timeout: float = 1.0,
    ) -> RedisValkeyStateStore:
        return RedisValkeyStateStore(
            options=RedisStateStoreOptions(
                backend=backend,
                endpoint=f"redis://127.0.0.1:{port or self._port}/0",
                username=self._username,
                password_source=_StaticPasswordSource(
                    self._password if password is None else password,
                ),
                namespace=namespace or self.namespace,
                operation_timeout_seconds=timeout,
            ),
            capabilities=StateStoreCapabilities.p10_contract(),
            clock=self.clock,
        )

    async def test_authentication_and_secret_redaction_for_both_drivers(self) -> None:
        for backend in ("redis", "valkey"):
            with self.subTest(backend=backend):
                store = self._provider(backend=backend)
                self.assertNotIn(self._password, repr(store))
                await store.open()
                self.assertTrue((await store.health()).ready)
                await store.close()

        rejected = self._provider(password="definitely-wrong-secret")
        with self.assertRaises(NsRuntimeStateStoreUnavailableError) as caught:
            await rejected.open()
        self.assertNotIn("definitely-wrong-secret", str(caught.exception))
        self.assertNotIn(self._password, repr(caught.exception))

    async def test_namespace_isolation(self) -> None:
        first = self._provider(namespace=self.namespace + ":first")
        second = self._provider(namespace=self.namespace + ":second")
        await first.open()
        await second.open()
        scope = _scope()
        key = _key(scope, "same-logical-key")
        first_record = await first.compare_and_set(
            scope=scope,
            mutation=_create(key, b"first"),
        )
        second_record = await second.compare_and_set(
            scope=scope,
            mutation=_create(key, b"second"),
        )
        assert first_record is not None and second_record is not None
        self.assertEqual(b"first", first_record.document.payload)
        self.assertEqual(b"second", second_record.document.payload)
        raw = self._raw_client()
        first_keys = await self._scan(raw, self.namespace + ":first:*")
        second_keys = await self._scan(raw, self.namespace + ":second:*")
        await raw.aclose()
        self.assertTrue(first_keys)
        self.assertTrue(second_keys)
        self.assertTrue(set(first_keys).isdisjoint(second_keys))
        await first.close()
        await second.close()

    async def test_concurrent_create_has_one_winner_and_cas_conflicts(self) -> None:
        store = self._provider()
        await store.open()
        scope = _scope()
        key = _key(scope, "dedup")
        outcomes = await asyncio.gather(
            *(store.compare_and_set(scope=scope, mutation=_create(key))
              for _ in range(16)),
            return_exceptions=True,
        )
        winners = [value for value in outcomes if not isinstance(value, BaseException)]
        self.assertEqual(1, len(winners))
        self.assertEqual(15, sum(
            isinstance(value, NsRuntimeStateStoreConflictError)
            for value in outcomes
        ))
        current = winners[0]
        assert current is not None
        replacement = StateMutation(
            key=key,
            assertion=StateAssertion.matches(
                current.revision,
                state_version=1,
                epoch=3,
            ),
            kind=StateMutationKind.REPLACE,
            document=_document(2, b"advanced"),
        )
        advanced = await store.compare_and_set(
            scope=scope,
            mutation=replacement,
        )
        assert advanced is not None
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await store.compare_and_set(scope=scope, mutation=replacement)
        observed = await store.read(
            scope=scope,
            key=key,
            consistency=StateConsistency.LINEARIZABLE,
        )
        self.assertEqual(advanced, observed.record)
        await store.close()

    async def test_revision_order_and_schema_version_contract(self) -> None:
        store = self._provider()
        await store.open()
        scope = _scope()
        old_key = _key(scope, "revision-old")
        new_key = _key(scope, "revision-new")
        old = await store.compare_and_set(
            scope=scope,
            mutation=_create(old_key),
        )
        newer = await store.compare_and_set(
            scope=scope,
            mutation=_create(new_key),
        )
        assert old is not None and newer is not None
        stale = await store.read(
            scope=scope,
            key=old_key,
            consistency=StateConsistency.STALE_ALLOWED,
            minimum_revision=newer.revision,
        )
        self.assertTrue(stale.stale)
        for document in (
            _document(3),
            StateDocument(
                schema_name="contract.record",
                schema_version=2,
                state_version=2,
                epoch=3,
                payload=b"safe",
            ),
        ):
            with self.subTest(document=document):
                with self.assertRaises(NsRuntimeStateStoreVersionMismatchError):
                    await store.compare_and_set(
                        scope=scope,
                        mutation=StateMutation(
                            key=old_key,
                            assertion=StateAssertion.matches(old.revision),
                            kind=StateMutationKind.REPLACE,
                            document=document,
                        ),
                    )
        await store.close()

    async def test_failed_batch_rolls_back_every_create_on_conflict(self) -> None:
        store = self._provider()
        await store.open()
        scope = _scope()
        existing_key = _key(scope, "existing")
        orphan_keys = tuple(
            _key(scope, f"must-not-exist-{index}") for index in range(32)
        )
        await store.compare_and_set(
            scope=scope,
            mutation=_create(existing_key),
        )
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await store.transact(StateTransaction(
                scope=scope,
                mutations=(
                    *(_create(key) for key in orphan_keys),
                    _create(existing_key),
                ),
            ))
        for key in orphan_keys:
            observed = await store.read(
                scope=scope,
                key=key,
                consistency=StateConsistency.LINEARIZABLE,
            )
            self.assertIsNone(observed.record)
        await store.close()

    async def test_append_and_lifecycle_cleanup(self) -> None:
        store = self._provider()
        self.assertIs(StateStoreHealthStatus.NOT_READY, (await store.health()).status)
        await store.open()
        scope = _scope()
        key = StateKey(
            namespace=scope.namespace,
            object_type="audit_log",
            object_id="final",
        )
        first = await store.append(
            scope=scope,
            key=key,
            document=_document(1),
        )
        second = await store.append(
            scope=scope,
            key=key,
            document=_document(1, b"next"),
            assertion=StateAssertion.matches(first.revision),
        )
        self.assertEqual(1, first.position)
        self.assertEqual(2, second.position)
        await store.close()
        await store.close()
        self.assertIs(StateStoreHealthStatus.CLOSED, (await store.health()).status)
        with self.assertRaises(NsRuntimeStateStoreClosedError):
            await store.read(
                scope=scope,
                key=key,
                consistency=StateConsistency.LINEARIZABLE,
            )

    async def test_existing_runtime_owner_opens_and_closes_provider(self) -> None:
        store = self._provider()
        context = RuntimeContext(
            config=NsConfig(),
            clock=self.clock,
            logger=logging.Logger("redis-state-store-runtime-owner"),
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
            task_supervisor=TaskSupervisor(),
            dependencies=RuntimeDependencySlots(state_store=store),
        )
        service = RuntimeService(context=context)
        await _run_service_once(service, state_store=store)
        self.assertIs(StateStoreHealthStatus.CLOSED, (await store.health()).status)

    async def test_timeout_and_unavailable_are_typed(self) -> None:
        unavailable = self._provider(port=_free_port(), timeout=0.05)
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            await unavailable.open()

        store = self._provider(timeout=0.03)
        await store.open()
        raw = self._raw_client()
        await raw.execute_command("CLIENT", "PAUSE", 150)
        with self.assertRaises(NsRuntimeStateStoreTimeoutError):
            await store.read(
                scope=_scope(),
                key=_key(_scope(), "paused-read"),
                consistency=StateConsistency.LINEARIZABLE,
            )
        await asyncio.sleep(0.18)
        await raw.execute_command("CLIENT", "PAUSE", 150)
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            await store.compare_and_set(
                scope=_scope(),
                mutation=_create(_key(_scope(), "paused-write")),
            )
        await asyncio.sleep(0.18)
        await raw.aclose()
        await store.close()

    async def test_p10_concurrent_dedup_has_one_admission_winner(self) -> None:
        plan = await _plan()
        store = self._provider()
        await store.open()
        service, request = self._admission_service(store, plan)
        results = await asyncio.gather(*(
            service.admit(
                request,
                trace=AdmissionTrace(trace_id=f"redis-dedup-{index}"),
            )
            for index in range(8)
        ))
        self.assertEqual(1, sum(
            value.outcome is AdmissionOutcome.ACCEPTED for value in results
        ))
        self.assertEqual(7, sum(
            value.outcome is AdmissionOutcome.DUPLICATE for value in results
        ))
        await store.close()

    async def test_p10_real_501_target_batched_initialization(self) -> None:
        plan = await _plan(501)
        store = self._provider()
        await store.open()
        service, request = self._admission_service(store, plan)
        result = await service.admit(
            request,
            trace=AdmissionTrace(trace_id="redis-batched-501"),
        )
        self.assertIs(AdmissionOutcome.ACCEPTED, result.outcome)
        summary_id = result.response.summary_id
        namespace = StateNamespace.tenant(
            tenant_id=request.tenant_id,
            domain="delivery",
        )
        scope = StateAccessScope(
            atomic_scope=StateAtomicScope(
                namespace=namespace,
                partition="admission",
            ),
            authority=StateAuthorityKind.DELIVERY_ADMISSION,
            caller="delivery.admission",
            capabilities=frozenset({
                StateCallerCapability.READ,
                StateCallerCapability.TRANSACT,
            }),
        )
        root_key = StateKey(
            namespace=namespace,
            object_type="summary",
            object_id=(
                "sha256:" + hashlib.sha256(summary_id.encode()).hexdigest()
            ),
        )
        root = await store.read(
            scope=scope,
            key=root_key,
            consistency=StateConsistency.LINEARIZABLE,
        )
        assert root.record is not None
        values = json.loads(root.record.document.payload)
        self.assertEqual("accepted", values["status"])
        self.assertEqual(501, values["accepted_count"])
        self.assertEqual(501, values["prepared_count"])
        self.assertEqual(3, root.record.document.state_version)
        client = self._raw_client()
        record_keys = await self._scan(
            client, self.namespace + ":record:*",
        )
        await client.aclose()
        self.assertEqual(504, len(record_keys))
        await store.close()

    def _admission_service(self, store, plan):
        service = DeliveryAdmissionService(
            policy=DefaultAdmissionPolicy(),
            policy_config=AdmissionPolicyConfig(
                config_version="c1",
                policy_version="p1",
            ),
            store=StateStoreDeliveryAdmissionStore(store),
            payload_ref_client=_PayloadClient(self.clock),
            clock=self.clock,
            identifier_factory=_ids,
        )
        stage_six = StageSixAdmissionInput.from_result(
            RoutingPreparationResult.resolved(plan),
        )
        request = AdmissionRequest.from_stage_six(
            stage_six=stage_six,
            message_id=MESSAGE_ID,
            tenant_id=plan.authorization_evidence.effective_tenant_id,
            source_identity="identity-source",
            authorization_binding_reference=(
                plan.authorization_evidence.message_binding_reference
            ),
            payload=InlinePayload(
                value={"v": 1},
                media_type="application/json",
                application_limit_bytes=4096,
                transport_limit_bytes=4096,
            ),
            requested_priority=None,
            requested_reliability=None,
            requested_expires_at=self.clock.utc_now() + timedelta(seconds=30),
            requested_ack_timeout_seconds=30,
            requested_target_strategy=plan.requested_strategy,
        )
        return service, request


if __name__ == "__main__":
    unittest.main()
