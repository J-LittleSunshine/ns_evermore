# -*- coding: utf-8 -*-
"""Real Redis standalone and recovery evidence for P10-FIX-02."""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
import logging
import os
import secrets
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import timedelta
import unittest
import uuid

try:
    import redis
    import redis.asyncio as redis_async
except ModuleNotFoundError:  # backend-only environments intentionally omit runtime drivers
    redis = None  # type: ignore[assignment]
    redis_async = None  # type: ignore[assignment]

from ns_common.exceptions import (
    NsRuntimeStateStoreCapabilityUnavailableError,
    NsRuntimeStateStoreClosedError,
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreIndeterminateWriteError,
    NsRuntimeStateStoreNamespaceViolationError,
    NsRuntimeStateStoreTimeoutError,
    NsRuntimeStateStoreUnavailableError,
    NsRuntimeStateStoreVersionMismatchError,
    NsValidationError,
)
from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsConfig, NsRuntimeStateStoreConfig
from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
from ns_common.testing import NsTestResourceFactory
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
    StateOrderedIndexKey,
    StateOrderedIndexMutation,
    StateOrderedIndexMutationKind,
    StateOrderedIndexReadAssertion,
    StateRecordReadAssertion,
    StateStoreCapabilities,
    StateStoreHealthStatus,
    StateStorePasswordSource,
    StateTransaction,
    StateTransitionLogAppend,
    create_contract_test_state_store_composition,
)
from ns_common.time import ControlledClock
from ns_common.state_store.authority import (
    _issue_state_access_scope,
    _new_state_scope_issuer,
)
from ns_runtime.delivery import (
    AdmissionOutcome,
    AdmissionPolicyConfig,
    AdmissionRequest,
    AdmissionTrace,
    DefaultAdmissionPolicy,
    ClaimOutcome,
    ClaimWorker,
    DeliverySchedulingPolicy,
    DeliveryAuthorityLayout,
    DeliveryAdmissionService,
    InlinePayload,
    StageSixAdmissionInput,
    StateStoreDeliveryAdmissionStore,
    StateStoreDeliveryScheduler,
    StateStoreDeliveryAuthorityRegistry,
)
from ns_runtime.processor import RoutingPreparationResult
from ns_runtime.context import RuntimeContext, RuntimeDependencySlots
from ns_runtime.authority_broker import (
    AuthorityBrokerConfig,
    start_integration_test_authority_broker,
)
import ns_runtime.authority_broker as broker_module
from ns_runtime.main import _run_service_once
from ns_runtime.delivery_persistence import DeliveryPersistenceTransaction
from ns_runtime.authority_wire import encode_transaction_request
from ns_runtime.service import RuntimeService
from ns_runtime.state_authority import (
    PersistenceStrongAuditAuthorityService,
)
from ns_runtime.connection import (
    ConnectionAuditConsistency,
    ConnectionAuditKind,
    ConnectionAuditOutcome,
    ConnectionLifecycleAuditEvent,
    PersistenceConnectionLifecycleAuditSink,
)

from tests.test_runtime_delivery_admission import (
    MESSAGE_ID,
    UTC_START,
    _PayloadClient,
    _envelope_authority,
    _ids,
    _plan,
)
from tests._state_store_contract_model import (
    _ContractTestRepositoryComposition,
)
from tests.test_runtime_state_store import _audit_record


@dataclass(frozen=True, slots=True, repr=False)
class _StaticPasswordSource(StateStorePasswordSource):
    value: str = field(repr=False)

    def resolve(self) -> str:
        return self.value


def _scope(store: RedisValkeyStateStore) -> StateAccessScope:
    namespace = StateNamespace.audit(domain="processor")
    return _issue_test_scope(
        store,
        atomic_scope=StateAtomicScope(namespace=namespace, partition="contract"),
        authority=StateAuthorityKind.STRONG_AUDIT,
        caller="redis-contract-test",
        capabilities=frozenset(StateCallerCapability),
    )


def _issue_test_scope(store: RedisValkeyStateStore, **values) -> StateAccessScope:
    issuer = getattr(store, "_contract_test_scope_issuer", None)
    if issuer is None:
        raise AssertionError("contract-test StateStore issuer is unavailable")
    return _issue_state_access_scope(issuer, **values)


def _repositories(store: RedisValkeyStateStore, *, runtime_id="runtime-local"):
    composition = getattr(store, "_contract_test_repository_composition", None)
    if not isinstance(composition, _ContractTestRepositoryComposition):
        raise AssertionError("contract-test repository composition is unavailable")
    return composition.delivery_repositories(runtime_id=runtime_id)


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
            if os.environ.get("NS_RUNTIME_REQUIRE_REDIS_INTEGRATION") == "1":
                raise RuntimeError(
                    "required runtime Redis driver is unavailable",
                )
            raise unittest.SkipTest("runtime Redis driver is unavailable")
        server = shutil.which("redis-server")
        if server is None:
            if os.environ.get("NS_RUNTIME_REQUIRE_REDIS_INTEGRATION") == "1":
                raise RuntimeError(
                    "required local redis-server is unavailable",
                )
            raise unittest.SkipTest("local redis-server is unavailable")
        cls._resource_factory = NsTestResourceFactory(
            prefix="ns-runtime-redis-state-",
        )
        cls.addClassCleanup(cls._resource_factory.close)
        reservation = cls._resource_factory.reserve_tcp_port()
        cls._port = reservation.port
        cls._username = ""
        cls._password = secrets.token_urlsafe(32)
        config = cls._resource_factory.directories.etc / "redis.conf"
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
                f"dir {cls._resource_factory.directories.data}",
                (
                    f"user default on >{cls._password} "
                    "~ns_runtime:test:* +@all -flushdb -flushall -keys"
                ),
            )) + "\n",
            encoding="utf-8",
        )
        reservation.release()
        cls._process = subprocess.Popen(
            (server, str(config)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.addClassCleanup(cls._stop_server)
        client = redis.Redis(
            host="127.0.0.1",
            port=cls._port,
            db=0,
            username=None,
            password=cls._password,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            decode_responses=True,
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
        server_info = client.info(section="server")
        if int(server_info["process_id"]) != cls._process.pid:
            raise RuntimeError("isolated redis-server did not own reserved port")
        client.close()

    @classmethod
    def _stop_server(cls) -> None:
        process = cls._process
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

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

    def _bucket_scope(
        self,
        store: RedisValkeyStateStore,
        *,
        bucket_id: int = 3,
    ) -> StateAccessScope:
        namespace = StateNamespace.tenant(
            tenant_id="tenant-a", domain="delivery",
        )
        return _issue_test_scope(
            store,
            atomic_scope=StateAtomicScope(
                namespace=namespace, partition=f"bucket-{bucket_id}",
            ),
            authority=StateAuthorityKind.DELIVERY_ADMISSION,
            caller="delivery.scheduling",
            capabilities=frozenset({
                StateCallerCapability.READ,
                StateCallerCapability.SCAN,
                StateCallerCapability.COMPARE_AND_SET,
                StateCallerCapability.TRANSACT,
                StateCallerCapability.ORDERED_INDEX,
                StateCallerCapability.APPEND,
            }),
        )

    async def test_cluster_transaction_keys_share_exact_tenant_bucket_slot(self) -> None:
        store = self._provider()
        scope = self._bucket_scope(store, bucket_id=3)
        key = StateKey(
            namespace=scope.namespace,
            object_type="delivery",
            object_id="cluster-slot-proof",
        )
        index = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.ready",
            bucket="delivery",
        )
        transaction = StateTransaction(
            scope=scope,
            mutations=(_create(key),),
            ordered_index_mutations=(StateOrderedIndexMutation(
                index=index,
                kind=StateOrderedIndexMutationKind.ADD,
                member=key.object_id,
                score=1.0,
            ),),
            log_appends=(StateTransitionLogAppend(
                key=key,
                document=_document(1, b'{"operation":"slot-proof"}'),
            ),),
        )
        physical_keys = store._transaction_physical_keys(transaction)
        self.assertGreaterEqual(len(physical_keys), 5)
        self.assertTrue(all("{tenant-a:3}" in value for value in physical_keys))
        slots = {redis.cluster.key_slot(value.encode("utf-8"))
                 for value in physical_keys}
        self.assertEqual(1, len(slots))

    async def test_legacy_physical_record_requires_explicit_migration(self) -> None:
        store = self._provider()
        await store.open()
        scope = self._bucket_scope(store, bucket_id=4)
        key = StateKey(
            namespace=scope.namespace,
            object_type="delivery",
            object_id="legacy-layout-proof",
        )
        client = store._require_client()
        await client.hset(store._legacy_record_key(key), mapping={"legacy": "1"})
        with self.assertRaises(NsRuntimeStateStoreVersionMismatchError) as caught:
            await store.read(
                scope=scope,
                key=key,
                consistency=StateConsistency.LINEARIZABLE,
            )
        self.assertEqual(
            "legacy_physical_key_migration_required",
            caught.exception.details["reason"],
        )
        await store.close()

    async def test_previous_bucket_tag_generation_requires_layout_migration(self) -> None:
        store = self._provider()
        await store.open()
        base = self._bucket_scope(store, bucket_id=4)
        scope = _issue_test_scope(
            store,
            atomic_scope=StateAtomicScope(
                namespace=base.namespace,
                partition="layout-2-bucket-4",
            ),
            authority=base.authority,
            caller=base.caller,
            capabilities=base.capabilities,
        )
        key = StateKey(
            namespace=scope.namespace,
            object_type="delivery",
            object_id="previous-tag-layout-proof",
        )
        client = store._require_client()
        await client.hset(
            store._previous_layout_record_key(scope, key),
            mapping={"legacy": "1"},
        )
        with self.assertRaises(NsRuntimeStateStoreVersionMismatchError) as caught:
            await store.read(
                scope=scope,
                key=key,
                consistency=StateConsistency.LINEARIZABLE,
            )
        self.assertEqual(
            "authority_layout_generation_migration_required",
            caught.exception.details["reason"],
        )
        await store.close()

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
        clock: ControlledClock | None = None,
    ) -> RedisValkeyStateStore:
        scope_issuer = _new_state_scope_issuer(contract_test=True)
        store = RedisValkeyStateStore(
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
            clock=clock or self.clock,
            _contract_test_authority=True,
            _scope_issuer=scope_issuer,
        )
        store._contract_test_scope_issuer = scope_issuer
        store._contract_test_repository_composition = (
            _ContractTestRepositoryComposition(
            store=store,
            issuer=scope_issuer,
        ))
        return store

    async def test_production_repository_resource_policy_is_enforced_by_redis(
        self,
    ) -> None:
        broker = None
        try:
            config = AuthorityBrokerConfig(
                iam_base_url="http://127.0.0.1:1/",
                iam_timeout_seconds=0.2,
                iam_mode="strict",
                permission_snapshot_ttl_seconds=60.0,
                state_backend="redis",
                state_endpoint=f"redis://127.0.0.1:{self._port}/0",
                state_username="",
                state_namespace=self.namespace,
                state_operation_timeout_seconds=1.0,
                runtime_id="runtime-production-a",
            )
            broker = start_integration_test_authority_broker(
                config=config,
                iam_service_credential="i" * 32,
                state_password=self._password,
                session_ttl_seconds=0.45,
                delegation_ttl_seconds=30.0,
            )
            self.assertIs(
                broker_module._IntegrationTestRoleBrokerChannel,
                type(broker._channel),
            )
            self.assertIs(
                broker_module._IntegrationTestAdmissionRepositoryProxy,
                type(broker.repositories.admission),
            )
            with self.assertRaises(NsValidationError):
                RuntimeDependencySlots(
                    delivery_admission_persistence=(
                        broker.repositories.admission
                    ),
                )
            self.assertNotIn(self._password, repr(broker))
            self.assertFalse(any(
                self._password in value
                for value in os.environ.values()
            ))
            await broker.state_store.open()
            self.assertEqual(
                "ready",
                (await broker.state_store.health()).status.value,
            )
            admission = broker.repositories.admission
            scheduler = broker.repositories.scheduler
            partition = admission.delivery_scope(
                tenant_id="tenant-broker-success",
                bucket_id=0,
                layout_generation=1,
            )
            delivery_ids = (
                "delivery-" + uuid.uuid4().hex,
                "delivery-" + uuid.uuid4().hex,
            )
            prepared_index = StateOrderedIndexKey(
                namespace=partition.namespace,
                name="delivery.prepared",
                bucket="delivery",
            )

            def create_transaction(
                delivery_id: str,
                *,
                score: float,
                with_log: bool,
            ) -> DeliveryPersistenceTransaction:
                key = StateKey(
                    namespace=partition.namespace,
                    object_type="delivery",
                    object_id=delivery_id,
                )
                return DeliveryPersistenceTransaction(
                    partition=partition,
                    mutations=(StateMutation(
                        key=key,
                        assertion=StateAssertion.absent(),
                        kind=StateMutationKind.CREATE,
                        document=StateDocument(
                            schema_name="delivery_delivery",
                            schema_version=1,
                            state_version=1,
                            payload=json.dumps({
                                "delivery_id": delivery_id,
                                "status": "prepared",
                            }).encode(),
                        ),
                    ),),
                    record_assertions=(StateRecordReadAssertion.absent(
                        StateKey(
                            namespace=partition.namespace,
                            object_type="payload_body",
                            object_id="payload-" + delivery_id,
                        ),
                    ),),
                    ordered_index_mutations=(StateOrderedIndexMutation(
                        index=prepared_index,
                        kind=StateOrderedIndexMutationKind.ADD,
                        member=delivery_id,
                        score=score,
                    ),),
                    ordered_index_assertions=(
                        StateOrderedIndexReadAssertion.absent(
                            prepared_index,
                            delivery_id,
                        ),
                    ),
                    log_appends=((StateTransitionLogAppend(
                        key=StateKey(
                            namespace=partition.namespace,
                            object_type="delivery_transition_log",
                            object_id="log-" + delivery_id,
                        ),
                        document=StateDocument(
                            schema_name="delivery_transition_event",
                            schema_version=1,
                            state_version=1,
                            payload=b'{"operation":"admit"}',
                        ),
                    ),) if with_log else ()),
                )

            first_transaction = create_transaction(
                delivery_ids[0],
                score=1.0,
                with_log=True,
            )
            await asyncio.sleep(0.32)
            first_result = await admission.transact_admission(
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
                transaction=first_transaction,
            )
            self.assertEqual(
                len(first_transaction.mutations),
                len(first_result.records),
            )
            self.assertEqual(
                len(first_transaction.log_appends),
                len(first_result.log_positions),
            )
            injected_scope = encode_transaction_request(
                first_transaction,
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
            )
            injected_scope["tenant_id"] = "tenant-attacker"
            with self.assertRaises(
                NsRuntimeStateStoreNamespaceViolationError,
            ):
                await admission._request(
                    "transact_admission",
                    injected_scope,
                )
            await admission.transact_admission(
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
                transaction=create_transaction(
                    delivery_ids[1],
                    score=2.0,
                    with_log=False,
                ),
            )
            await asyncio.sleep(0.32)
            observed = await scheduler.read_delivery(
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
                delivery_id=delivery_ids[0],
            )
            self.assertIsNotNone(observed.record)
            await asyncio.sleep(0.32)
            first_page = await scheduler.read_scheduler_index(
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
                index_name="delivery.prepared",
                limit=1,
            )
            self.assertEqual((delivery_ids[0],), tuple(
                value.member for value in first_page.entries
            ))
            self.assertIsNotNone(first_page.next_cursor)
            second_page = await scheduler.read_scheduler_index(
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
                index_name="delivery.prepared",
                cursor=first_page.next_cursor,
                limit=1,
            )
            self.assertEqual((delivery_ids[1],), tuple(
                value.member for value in second_page.entries
            ))
            await asyncio.sleep(0.32)
            audit_position = await PersistenceStrongAuditAuthorityService(
                persistence=broker.repositories.audit,
            ).append(_audit_record())
            await PersistenceConnectionLifecycleAuditSink(
                persistence=broker.repositories.audit,
            ).emit(ConnectionLifecycleAuditEvent(
                kind=ConnectionAuditKind.SECURITY_CLOSE,
                outcome=ConnectionAuditOutcome.ENFORCED,
                required_consistency=(
                    ConnectionAuditConsistency.STRONG_REQUIRED
                ),
                connection_summary="sha256:0123456789abcdef",
                component_type="worker",
                connection_epoch=4,
                close_reason=None,
                occurred_at=UTC_START,
            ))
            self.assertGreater(audit_position.position, 0)
            assert observed.record is not None
            scheduler_transaction = DeliveryPersistenceTransaction(
                partition=partition,
                mutations=(StateMutation(
                    key=observed.record.key,
                    assertion=StateAssertion.matches(
                        observed.record.revision,
                        state_version=1,
                    ),
                    kind=StateMutationKind.REPLACE,
                    document=StateDocument(
                        schema_name="delivery_delivery",
                        schema_version=1,
                        state_version=2,
                        payload=json.dumps({
                            "delivery_id": delivery_ids[0],
                            "status": "queued",
                        }).encode(),
                    ),
                ),),
                record_assertions=(StateRecordReadAssertion.present(
                    observed.record.key,
                    revision=observed.record.revision,
                    state_version=1,
                ),),
                ordered_index_assertions=(
                    StateOrderedIndexReadAssertion.present(
                        prepared_index,
                        delivery_ids[0],
                        score=1.0,
                    ),
                ),
                ordered_index_mutations=(StateOrderedIndexMutation(
                    index=prepared_index,
                    kind=StateOrderedIndexMutationKind.REMOVE,
                    member=delivery_ids[0],
                ),),
                log_appends=(StateTransitionLogAppend(
                    key=StateKey(
                        namespace=partition.namespace,
                        object_type="delivery_transition_log",
                        object_id="scheduler-log-" + delivery_ids[0],
                    ),
                    document=StateDocument(
                        schema_name="delivery_transition_event",
                        schema_version=1,
                        state_version=1,
                        payload=b'{"operation":"queue"}',
                    ),
                ),),
            )
            scheduler_result = await scheduler.transact_scheduler(
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
                transaction=scheduler_transaction,
            )
            self.assertEqual(1, len(scheduler_result.records))
            self.assertEqual(1, len(scheduler_result.log_positions))
            self.assertGreaterEqual(
                broker.current_session_identity()[
                    "lifecycle_generation"
                ], 5,
            )
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                start_integration_test_authority_broker(
                    config=dataclasses.replace(
                        config,
                        runtime_id="runtime-production-b",
                    ),
                    iam_service_credential="i" * 32,
                    state_password="different-secret-input-channel",
                )
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                await broker.repositories.scheduler._request(
                    "read_payload_body", object(),
                )
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                await broker.repositories.payload._request(
                    "read_delivery", object(),
                )
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                await broker.repositories.registry._request(
                    "read_scheduler_index", object(),
                )
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                await broker.repositories.audit.append_processor_audit(
                    document=StateDocument(
                        schema_name="runtime.connection_lifecycle_audit",
                        schema_version=1,
                        state_version=1,
                        payload=b"{}",
                    ),
                )
            broker._channel._custodian.process.terminate()
            broker._channel._custodian.process.join(timeout=5.0)
            replacement = start_integration_test_authority_broker(
                config=dataclasses.replace(
                    config,
                    runtime_id="runtime-production-after-crash",
                ),
                iam_service_credential="i" * 32,
                state_password=self._password,
            )
            try:
                await replacement.state_store.open()
                self.assertEqual(
                    "ready",
                    (await replacement.state_store.health()).status.value,
                )
            finally:
                replacement.close()
        finally:
            if broker is not None:
                broker.close()

    async def test_broker_ipc_failure_reaps_child_and_releases_domain(
        self,
    ) -> None:
        config = AuthorityBrokerConfig(
            iam_base_url="http://127.0.0.1:1/",
            iam_timeout_seconds=0.2,
            iam_mode="strict",
            permission_snapshot_ttl_seconds=60.0,
            state_backend="redis",
            state_endpoint=f"redis://127.0.0.1:{self._port}/0",
            state_username="",
            state_namespace=self.namespace + ":ipc-reap",
            state_operation_timeout_seconds=1.0,
            runtime_id="runtime-ipc-reap-a",
        )
        broker = start_integration_test_authority_broker(
            config=config,
            iam_service_credential="i" * 32,
            state_password=self._password,
        )
        process = broker._channel._custodian.process
        original = broker._channel._connection

        class MalformedAfterSend:
            def send_bytes(self, value):
                original.send_bytes(value)

            def poll(self, timeout):
                return original.poll(timeout)

            def recv_bytes(self, maximum):
                original.recv_bytes(maximum)
                return b'{"unsigned":true}'

            def close(self):
                original.close()

        object.__setattr__(
            broker._channel, "_connection", MalformedAfterSend(),
        )
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            await broker.state_store.health()
        broker.close()
        self.assertFalse(process.is_alive())

        replacement = start_integration_test_authority_broker(
            config=dataclasses.replace(
                config,
                runtime_id="runtime-ipc-reap-b",
            ),
            iam_service_credential="i" * 32,
            state_password=self._password,
        )
        try:
            await replacement.state_store.open()
            self.assertTrue((await replacement.state_store.health()).ready)
        finally:
            replacement.close()

    async def test_write_send_attempt_failure_is_indeterminate_and_releases_lease(
        self,
    ) -> None:
        config = AuthorityBrokerConfig(
            iam_base_url="http://127.0.0.1:1/",
            iam_timeout_seconds=0.2,
            iam_mode="strict",
            permission_snapshot_ttl_seconds=60.0,
            state_backend="redis",
            state_endpoint=f"redis://127.0.0.1:{self._port}/0",
            state_username="",
            state_namespace=self.namespace + ":send-attempt",
            state_operation_timeout_seconds=1.0,
            runtime_id="runtime-send-attempt-a",
        )
        broker = start_integration_test_authority_broker(
            config=config,
            iam_service_credential="i" * 32,
            state_password=self._password,
        )
        admission_channel = broker.repositories.admission._channel
        process = admission_channel._custodian.process
        original = admission_channel._connection

        class RaisesAfterSend:
            def send_bytes(self, value):
                original.send_bytes(value)
                raise OSError("simulated partial IPC write")

            def close(self):
                original.close()

        object.__setattr__(
            admission_channel, "_connection", RaisesAfterSend(),
        )
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            await broker.repositories.admission._request(
                "transact_admission", {},
            )
        broker.close()
        self.assertFalse(process.is_alive())

        replacement = start_integration_test_authority_broker(
            config=dataclasses.replace(
                config,
                runtime_id="runtime-send-attempt-b",
            ),
            iam_service_credential="i" * 32,
            state_password=self._password,
        )
        try:
            await replacement.state_store.open()
            self.assertTrue((await replacement.state_store.health()).ready)
        finally:
            replacement.close()

    async def test_attestor_death_reaps_broker_and_releases_lease(
        self,
    ) -> None:
        config = AuthorityBrokerConfig(
            iam_base_url="http://127.0.0.1:1/",
            iam_timeout_seconds=0.2,
            iam_mode="strict",
            permission_snapshot_ttl_seconds=60.0,
            state_backend="redis",
            state_endpoint=f"redis://127.0.0.1:{self._port}/0",
            state_username="",
            state_namespace=self.namespace + ":attestor-death",
            state_operation_timeout_seconds=1.0,
            runtime_id="runtime-attestor-death-a",
        )
        broker = start_integration_test_authority_broker(
            config=config,
            iam_service_credential="i" * 32,
            state_password=self._password,
        )
        channel = broker.repositories.admission._channel
        process = channel._custodian.process
        attestor_process = channel._attestor._process
        attestor_process.terminate()
        attestor_process.join(timeout=5.0)
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            await broker.repositories.admission._request(
                "transact_admission", {},
            )
        self.assertFalse(process.is_alive())
        broker.close()

        replacement = start_integration_test_authority_broker(
            config=dataclasses.replace(
                config,
                runtime_id="runtime-attestor-death-b",
            ),
            iam_service_credential="i" * 32,
            state_password=self._password,
        )
        try:
            await replacement.state_store.open()
            self.assertTrue((await replacement.state_store.health()).ready)
        finally:
            replacement.close()

    async def test_rotation_provenance_and_normal_close_release_domain(
        self,
    ) -> None:
        config = AuthorityBrokerConfig(
            iam_base_url="http://127.0.0.1:1/",
            iam_timeout_seconds=0.2,
            iam_mode="strict",
            permission_snapshot_ttl_seconds=60.0,
            state_backend="redis",
            state_endpoint=f"redis://127.0.0.1:{self._port}/0",
            state_username="",
            state_namespace=self.namespace + ":rotation-reap",
            state_operation_timeout_seconds=1.0,
            runtime_id="runtime-rotation-reap-a",
        )
        broker = start_integration_test_authority_broker(
            config=config,
            iam_service_credential="i" * 32,
            state_password=self._password,
            session_ttl_seconds=0.45,
            delegation_ttl_seconds=30.0,
        )
        channel = broker.state_store._channel
        process = channel._custodian.process
        attestor_process = channel._attestor._process
        original = channel._connection
        connections = (
            broker.iam._channel._connection,
            broker.repositories.admission._channel._connection,
            broker.repositories.scheduler._channel._connection,
            broker.repositories.payload._channel._connection,
            broker.repositories.registry._channel._connection,
            broker.repositories.audit._channel._connection,
            original,
        )

        class MissingRotationCertificate:
            def __init__(self) -> None:
                self.rotation_pending = False
                self.saw_rotation = False

            def send_bytes(self, value):
                message = broker_module.decode_frame(value)
                self.rotation_pending = bool(
                    type(message) is dict
                    and message.get("kind") == "rotate_session"
                )
                original.send_bytes(value)

            def poll(self, timeout):
                return original.poll(timeout)

            def recv_bytes(self, maximum):
                raw = original.recv_bytes(maximum)
                if not self.rotation_pending:
                    return raw
                self.rotation_pending = False
                self.saw_rotation = True
                message = broker_module.decode_frame(raw)
                assert type(message) is dict
                message.pop("session_certificate", None)
                return broker_module.encode_frame(message)

            def close(self):
                original.close()

        corrupt = MissingRotationCertificate()
        object.__setattr__(channel, "_connection", corrupt)
        await asyncio.sleep(0.32)
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            await broker.state_store.health()
        self.assertTrue(corrupt.saw_rotation)
        self.assertFalse(process.is_alive())
        self.assertFalse(attestor_process.is_alive())
        self.assertTrue(all(value.closed for value in connections))
        broker.close()

        replacement = start_integration_test_authority_broker(
            config=dataclasses.replace(
                config,
                runtime_id="runtime-rotation-reap-b",
            ),
            iam_service_credential="i" * 32,
            state_password=self._password,
        )
        await replacement.state_store.open()
        replacement_connections = (
            replacement.iam._channel._connection,
            replacement.repositories.admission._channel._connection,
            replacement.repositories.scheduler._channel._connection,
            replacement.repositories.payload._channel._connection,
            replacement.repositories.registry._channel._connection,
            replacement.repositories.audit._channel._connection,
            replacement.state_store._channel._connection,
        )
        replacement.close()
        self.assertTrue(
            all(value.closed for value in replacement_connections),
        )

        final = start_integration_test_authority_broker(
            config=dataclasses.replace(
                config,
                runtime_id="runtime-rotation-reap-c",
            ),
            iam_service_credential="i" * 32,
            state_password=self._password,
        )
        try:
            await final.state_store.open()
            self.assertTrue((await final.state_store.health()).ready)
        finally:
            final.close()

    async def test_redis_server_authentication_with_both_protocol_drivers(self) -> None:
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
        first_scope = _scope(first)
        second_scope = _scope(second)
        key = _key(first_scope, "same-logical-key")
        first_record = await first.compare_and_set(
            scope=first_scope,
            mutation=_create(key, b"first"),
        )
        second_record = await second.compare_and_set(
            scope=second_scope,
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
        scope = _scope(store)
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

    async def test_p11_real_redis_index_activation_claim_and_provider_recovery(self) -> None:
        store = self._provider(timeout=5.0)
        await store.open()
        plan = await _plan()
        service, request = self._admission_service(store, plan)
        admitted = await service.admit(
            request,
            trace=AdmissionTrace(trace_id="trace-p11-redis"),
        )
        self.assertIs(AdmissionOutcome.ACCEPTED, admitted.outcome)
        repositories = _repositories(store)
        scheduler = StateStoreDeliveryScheduler(
            repository=repositories.scheduler,
            registry_repository=repositories.registry,
            clock=self.clock,
        )
        policy = DeliverySchedulingPolicy(
            config_version="c1",
            policy_version="p1",
            activation_batch_size=1,
            tenant_queued_high_watermark=10,
            target_queued_high_watermark=2,
            lease_ttl_seconds=60,
            renew_interval_seconds=5,
        )
        activated = await scheduler.activate_prepared(
            tenant_id=plan.authorization_evidence.effective_tenant_id,
            policy=policy,
        )
        self.assertEqual(1, len(activated.activated))
        workers = tuple(
            ClaimWorker(
                scheduler=scheduler,
                policy=policy,
                runtime_id=plan.selected_bindings[0].runtime_id,
                worker_id=f"redis-worker-{index}",
                token_factory=lambda index=index: f"redis-claim-{index}",
            )
            for index in range(16)
        )
        results = await asyncio.gather(*(
            worker.run_once(
                tenant_id=plan.authorization_evidence.effective_tenant_id,
            )
            for worker in workers
        ))
        claimed = next(
            result for result in results
            if result.outcome is ClaimOutcome.CLAIMED
        )
        self.assertEqual(15, sum(
            result.outcome in {ClaimOutcome.CONTENDED, ClaimOutcome.EMPTY}
            for result in results
        ))
        await store.close()
        store_b = self._provider(timeout=5.0)
        await store_b.open()
        repositories_b = _repositories(store_b)
        scheduler_b = StateStoreDeliveryScheduler(
            repository=repositories_b.scheduler,
            registry_repository=repositories_b.registry,
            clock=self.clock,
        )
        recovered = await scheduler_b.load_claimed(claim=claimed.claim)
        self.assertEqual(claimed.claim.fencing, recovered.owner.fencing)
        activated_b = await scheduler_b.activate_prepared(
            tenant_id=plan.authorization_evidence.effective_tenant_id,
            policy=policy,
        )
        self.assertEqual(1, len(activated_b.activated))
        claimed_b = await ClaimWorker(
            scheduler=scheduler_b,
            policy=policy,
            runtime_id=plan.selected_bindings[0].runtime_id,
            worker_id="redis-provider-b",
            token_factory=lambda: "redis-provider-b-claim",
        ).run_once(
            tenant_id=plan.authorization_evidence.effective_tenant_id,
        )
        self.assertIs(ClaimOutcome.CLAIMED, claimed_b.outcome)
        self.assertNotEqual(claimed.claim.delivery_id, claimed_b.claim.delivery_id)
        counts = await scheduler_b.resource_counts(
            tenant_id=plan.authorization_evidence.effective_tenant_id,
        )
        self.assertEqual((1, 2), (counts.prepared, counts.queued))
        await store_b.close()

    async def test_revision_order_and_schema_version_contract(self) -> None:
        store = self._provider()
        await store.open()
        scope = _scope(store)
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
        scope = _scope(store)
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

    async def test_failed_projection_batch_leaves_no_index_or_log_orphan(self) -> None:
        store = self._provider()
        await store.open()
        scope = _scope(store)
        existing_key = _key(scope, "projection-existing")
        orphan_key = _key(scope, "projection-orphan")
        index = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.ready",
            bucket="contract",
        )
        await store.compare_and_set(scope=scope, mutation=_create(existing_key))
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await store.transact(StateTransaction(
                scope=scope,
                mutations=(_create(orphan_key), _create(existing_key)),
                ordered_index_mutations=(StateOrderedIndexMutation(
                    index=index,
                    kind=StateOrderedIndexMutationKind.ADD,
                    member="projection-orphan",
                    score=1.0,
                ),),
                log_appends=(StateTransitionLogAppend(
                    key=orphan_key,
                    document=_document(1, b'{"operation":"must-not-commit"}'),
                ),),
            ))
        observed = await store.read(
            scope=scope,
            key=orphan_key,
            consistency=StateConsistency.LINEARIZABLE,
        )
        self.assertIsNone(observed.record)
        index_result = await store.read_ordered_index(
            scope=scope, index=index, limit=10,
        )
        self.assertEqual((0, ()), (index_result.total_count, index_result.entries))
        raw = self._raw_client()
        transition_keys = await self._scan(
            raw, self.namespace + ":transition:*",
        )
        await raw.aclose()
        self.assertEqual([], transition_keys)
        await store.close()

    async def test_ordered_index_cursor_is_stable_across_between_page_mutations(
        self,
    ) -> None:
        store = self._provider()
        await store.open()
        scope = _scope(store)
        index = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.cursor",
            bucket="contract",
        )

        def change(
            kind: StateOrderedIndexMutationKind,
            member: str,
            score: float | None = None,
        ) -> StateOrderedIndexMutation:
            return StateOrderedIndexMutation(
                index=index,
                kind=kind,
                member=member,
                score=score,
            )

        await store.transact(StateTransaction(
            scope=scope,
            mutations=(),
            ordered_index_mutations=tuple(
                change(StateOrderedIndexMutationKind.ADD, member, score)
                for member, score in (
                    ("delivery:a", 10.0),
                    ("delivery:b", 20.0),
                    ("delivery:c", 30.0),
                    ("delivery:d", 40.0),
                )
            ),
        ))
        first = await store.read_ordered_index(
            scope=scope,
            index=index,
            limit=2,
        )
        self.assertEqual(
            ("delivery:a", "delivery:b"),
            tuple(value.member for value in first.entries),
        )
        self.assertIsNotNone(first.next_cursor)

        # Mutations occur between pages: one deletion and one insertion before
        # the cursor, plus an insertion after it. Recomputing the cursor rank
        # atomically must not duplicate or skip the surviving tail.
        await store.transact(StateTransaction(
            scope=scope,
            mutations=(),
            ordered_index_mutations=(
                change(StateOrderedIndexMutationKind.REMOVE, "delivery:a"),
                change(StateOrderedIndexMutationKind.ADD, "delivery:x", 15.0),
                change(StateOrderedIndexMutationKind.ADD, "delivery:e", 35.0),
            ),
        ))
        second = await store.read_ordered_index(
            scope=scope,
            index=index,
            limit=2,
            start_after=first.next_cursor,
        )
        third = await store.read_ordered_index(
            scope=scope,
            index=index,
            limit=2,
            start_after=second.next_cursor,
        )
        self.assertEqual(
            ("delivery:c", "delivery:e", "delivery:d"),
            tuple(value.member for value in (*second.entries, *third.entries)),
        )
        self.assertEqual(
            len({value.member for value in (*first.entries, *second.entries, *third.entries)}),
            len((*first.entries, *second.entries, *third.entries)),
        )

        assert second.next_cursor is not None
        await store.transact(StateTransaction(
            scope=scope,
            mutations=(),
            ordered_index_mutations=(
                change(StateOrderedIndexMutationKind.REMOVE, "delivery:e"),
            ),
        ))
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await store.read_ordered_index(
                scope=scope,
                index=index,
                limit=2,
                start_after=second.next_cursor,
            )
        await store.close()

    async def test_read_precondition_conflict_is_zero_write_in_redis_lua(self) -> None:
        store = self._provider()
        await store.open()
        scope = _scope(store)
        guarded_key = _key(scope, "assertion-guard")
        seed_key = _key(scope, "assertion-seed")
        orphan_key = _key(scope, "assertion-orphan")
        guarded = await store.compare_and_set(
            scope=scope,
            mutation=_create(guarded_key),
        )
        assert guarded is not None
        index = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.lease",
            bucket="contract",
        )
        await store.transact(StateTransaction(
            scope=scope,
            mutations=(_create(seed_key),),
            ordered_index_mutations=(StateOrderedIndexMutation(
                index=index,
                kind=StateOrderedIndexMutationKind.ADD,
                member="delivery:guarded",
                score=11.0,
            ),),
        ))
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await store.transact(StateTransaction(
                scope=scope,
                mutations=(_create(orphan_key),),
                record_assertions=(StateRecordReadAssertion.present(
                    guarded_key,
                    revision=guarded.revision,
                    state_version=guarded.document.state_version,
                ),),
                ordered_index_assertions=(
                    StateOrderedIndexReadAssertion.present(
                        index,
                        "delivery:guarded",
                        score=12.0,
                    ),
                ),
                ordered_index_mutations=(StateOrderedIndexMutation(
                    index=index,
                    kind=StateOrderedIndexMutationKind.ADD,
                    member="delivery:orphan",
                    score=13.0,
                ),),
                log_appends=(StateTransitionLogAppend(
                    key=orphan_key,
                    document=_document(1, b'{"operation":"must-not-commit"}'),
                ),),
            ))
        observed = await store.read(
            scope=scope,
            key=orphan_key,
            consistency=StateConsistency.LINEARIZABLE,
        )
        self.assertIsNone(observed.record)
        entries = await store.read_ordered_index(
            scope=scope,
            index=index,
            limit=10,
        )
        self.assertEqual(
            (("delivery:guarded", 11.0),),
            tuple((entry.member, entry.score) for entry in entries.entries),
        )
        raw = self._raw_client()
        transition_keys = await self._scan(
            raw,
            self.namespace + ":transition:*",
        )
        await raw.aclose()
        self.assertEqual([], transition_keys)
        await store.close()

    async def test_append_and_lifecycle_cleanup(self) -> None:
        store = self._provider()
        self.assertIs(StateStoreHealthStatus.NOT_READY, (await store.health()).status)
        await store.open()
        scope = _scope(store)
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
        unavailable_reservation = self._resource_factory.reserve_tcp_port()
        unavailable_port = unavailable_reservation.port
        unavailable_reservation.release()
        unavailable = self._provider(port=unavailable_port, timeout=0.05)
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            await unavailable.open()

        store = self._provider(timeout=0.03)
        await store.open()
        raw = self._raw_client()
        await raw.execute_command("CLIENT", "PAUSE", 150)
        scope = _scope(store)
        with self.assertRaises(NsRuntimeStateStoreTimeoutError):
            await store.read(
                scope=scope,
                key=_key(scope, "paused-read"),
                consistency=StateConsistency.LINEARIZABLE,
            )
        await asyncio.sleep(0.18)
        await raw.execute_command("CLIENT", "PAUSE", 150)
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            await store.compare_and_set(
                scope=scope,
                mutation=_create(_key(scope, "paused-write")),
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
        bucket_id = int.from_bytes(
            hashlib.sha256(request.message_id.encode("utf-8")).digest()[:8],
            "big",
        ) % 8
        scope = _issue_test_scope(
            store,
            atomic_scope=StateAtomicScope(
                namespace=namespace,
                partition=f"layout-2-bucket-{bucket_id}",
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
        self.assertEqual("pending", values["status"])
        self.assertEqual(0, values["shard_count"])
        self.assertEqual(501, values["accepted_count"])
        self.assertEqual(501, values["prepared_count"])
        self.assertEqual(3, root.record.document.state_version)
        client = self._raw_client()
        record_keys = await self._scan(
            client, self.namespace + ":record:*",
        )
        await client.aclose()
        self.assertEqual(506, len(record_keys))
        await store.close()

    async def test_p10_records_survive_independent_provider_reconstruction(self) -> None:
        for target_count in (3, 501):
            with self.subTest(target_count=target_count):
                namespace_prefix = f"{self.namespace}:recovery:{target_count}"
                clock_a = ControlledClock(utc_start=UTC_START)
                plan_a = await _plan(target_count)
                store_a = self._provider(
                    namespace=namespace_prefix,
                    clock=clock_a,
                )
                await store_a.open()
                service_a, request_a = self._admission_service(
                    store_a,
                    plan_a,
                    clock=clock_a,
                )
                accepted = await service_a.admit(
                    request_a,
                    trace=AdmissionTrace(
                        trace_id=f"redis-recovery-a-{target_count}",
                    ),
                )
                self.assertIs(AdmissionOutcome.ACCEPTED, accepted.outcome)
                summary_id = accepted.response.summary_id
                scope, namespace = self._delivery_scope(
                    store_a,
                    request_a.tenant_id,
                )
                record_keys = {
                    "root": StateKey(
                        namespace=namespace,
                        object_type="summary",
                        object_id=self._delivery_object_id(summary_id),
                    ),
                    "payload_body": StateKey(
                        namespace=namespace,
                        object_type="payload_body",
                        object_id=self._delivery_object_id("payload_body:0"),
                    ),
                    "delivery": StateKey(
                        namespace=namespace,
                        object_type="delivery",
                        object_id=self._delivery_object_id("delivery:0"),
                    ),
                }
                evidence: dict[str, tuple[str, int, str, str]] = {}
                for name, key in record_keys.items():
                    observed = await store_a.read(
                        scope=scope,
                        key=key,
                        consistency=StateConsistency.LINEARIZABLE,
                    )
                    assert observed.record is not None
                    payload = json.loads(observed.record.document.payload)
                    digest = (payload["payload_evidence"]["digest"]
                              if "payload_evidence" in payload else payload["digest"])
                    evidence[name] = (
                        observed.record.revision._provider_token(),
                        observed.record.document.state_version,
                        hashlib.sha256(
                            observed.record.document.payload,
                        ).hexdigest(),
                        digest,
                    )
                raw = self._raw_client()
                keys_before_restart = await self._scan(
                    raw,
                    namespace_prefix + ":record:*",
                )
                await raw.aclose()
                self.assertEqual(target_count + 5, len(keys_before_restart))
                await store_a.close()
                del store_a, service_a, request_a, plan_a, scope, record_keys

                clock_b = ControlledClock(utc_start=UTC_START)
                store_b = self._provider(
                    namespace=namespace_prefix,
                    clock=clock_b,
                )
                await store_b.open()
                plan_b = await _plan(target_count)
                service_b, request_b = self._admission_service(
                    store_b,
                    plan_b,
                    clock=clock_b,
                )
                scope_b, namespace_b = self._delivery_scope(
                    store_b,
                    request_b.tenant_id,
                )
                recovered_keys = {
                    "root": StateKey(
                        namespace=namespace_b,
                        object_type="summary",
                        object_id=self._delivery_object_id(summary_id),
                    ),
                    "payload_body": StateKey(
                        namespace=namespace_b,
                        object_type="payload_body",
                        object_id=self._delivery_object_id("payload_body:0"),
                    ),
                    "delivery": StateKey(
                        namespace=namespace_b,
                        object_type="delivery",
                        object_id=self._delivery_object_id("delivery:0"),
                    ),
                }
                for name, key in recovered_keys.items():
                    recovered = await store_b.read(
                        scope=scope_b,
                        key=key,
                        consistency=StateConsistency.LINEARIZABLE,
                    )
                    assert recovered.record is not None
                    revision, state_version, document_digest, payload_digest = evidence[name]
                    self.assertEqual(
                        revision,
                        recovered.record.revision._provider_token(),
                    )
                    self.assertEqual(
                        state_version,
                        recovered.record.document.state_version,
                    )
                    self.assertEqual(
                        document_digest,
                        hashlib.sha256(
                            recovered.record.document.payload,
                        ).hexdigest(),
                    )
                    recovered_payload = json.loads(
                        recovered.record.document.payload,
                    )
                    recovered_digest = (
                        recovered_payload["payload_evidence"]["digest"]
                        if "payload_evidence" in recovered_payload
                        else recovered_payload["digest"]
                    )
                    self.assertEqual(payload_digest, recovered_digest)
                    if name == "root":
                        self.assertEqual("pending", recovered_payload["status"])
                        self.assertEqual(
                            target_count,
                            recovered_payload["prepared_count"],
                        )
                    elif name == "delivery":
                        self.assertEqual("prepared", recovered_payload["status"])
                self.assertEqual(
                    2 if target_count <= 500 else 3,
                    evidence["root"][1],
                )
                self.assertEqual(1, evidence["delivery"][1])

                duplicate = await service_b.admit(
                    request_b,
                    trace=AdmissionTrace(
                        trace_id=f"redis-recovery-b-{target_count}",
                    ),
                )
                self.assertIs(AdmissionOutcome.DUPLICATE, duplicate.outcome)
                self.assertEqual(summary_id, duplicate.response.summary_id)
                raw = self._raw_client()
                keys_after_duplicate = await self._scan(
                    raw,
                    namespace_prefix + ":record:*",
                )
                await raw.aclose()
                self.assertEqual(
                    set(keys_before_restart),
                    set(keys_after_duplicate),
                )
                with self.assertRaises(NsRuntimeStateStoreVersionMismatchError):
                    await StateStoreDeliveryAuthorityRegistry(
                        repository=_repositories(store_b).registry,
                    ).ensure_registered(
                        tenant_id=request_b.tenant_id,
                        layout=DeliveryAuthorityLayout(bucket_count=16),
                    )
                await store_b.close()

    @staticmethod
    def _delivery_object_id(identifier: str) -> str:
        return "sha256:" + hashlib.sha256(identifier.encode()).hexdigest()

    @staticmethod
    def _delivery_scope(
        store: RedisValkeyStateStore,
        tenant_id: str,
    ) -> tuple[StateAccessScope, StateNamespace]:
        namespace = StateNamespace.tenant(
            tenant_id=tenant_id,
            domain="delivery",
        )
        bucket_id = int.from_bytes(
            hashlib.sha256(MESSAGE_ID.encode("utf-8")).digest()[:8], "big",
        ) % 8
        return _repositories(store).admission.delivery_scope(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            layout_generation=2,
        ), namespace

    def _admission_service(
        self,
        store,
        plan,
        *,
        clock: ControlledClock | None = None,
    ):
        service_clock = clock or self.clock
        repositories = _repositories(store)
        service = DeliveryAdmissionService.for_contract_tests(
            policy=DefaultAdmissionPolicy(),
            policy_config=AdmissionPolicyConfig(
                config_version="c1",
                policy_version="p1",
            ),
            store=StateStoreDeliveryAdmissionStore(
                repository=repositories.admission,
                registry_repository=repositories.registry,
            ),
            payload_ref_client=_PayloadClient(service_clock),
            clock=service_clock,
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
            envelope_authority=_envelope_authority(plan),
            payload=InlinePayload(
                value={"v": 1},
                media_type="application/json",
                application_limit_bytes=4096,
                transport_limit_bytes=4096,
            ),
            requested_priority=None,
            requested_reliability=None,
            requested_expires_at=service_clock.utc_now() + timedelta(seconds=30),
            requested_ack_timeout_seconds=30,
            requested_target_strategy=plan.requested_strategy,
        )
        return service, request


if __name__ == "__main__":
    unittest.main()
