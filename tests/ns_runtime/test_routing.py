# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeTargetUnavailableError,
    NsRuntimeTenantMismatchError
)
from ns_runtime.auth import RuntimeAuthResult
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso
)
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.routing import RuntimeTargetResolver
from ns_runtime.session import RuntimeSessionRegistry

if TYPE_CHECKING:
    pass


class RuntimeTargetResolverTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_id = "runtime-test"
        self.codec = EnvelopeCodec(runtime_id=self.runtime_id)
        self.registry = RuntimeSessionRegistry(runtime_id=self.runtime_id)
        self.resolver = RuntimeTargetResolver(runtime_id=self.runtime_id, session_registry=self.registry)
        self.source_session = self._activate(
            identity="source-1",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=("runtime.management", "task.dispatch"),
        )
        self.client_session = self._activate(
            identity="client-1",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute", "file.read"),
        )
        self.node_session = self._activate(
            identity="node-1",
            tenant_id="tenant-1",
            component_type="node",
            capabilities=("task.execute", "file.write"),
        )

    def test_resolve_connection_target(self) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "connection",
                    "connection_id": self.client_session.connection_id,
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.target_count, 1)
        self.assertEqual(decision.targets[0].connection_id, self.client_session.connection_id)

    def test_resolve_identity_target(self) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "identity",
                    "identity": "client-1",
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.target_count, 1)
        self.assertEqual(decision.targets[0].identity, "client-1")
        self.assertEqual(
            decision.strategy,
            "policy.default_single",
        )

    def test_resolve_tenant_target(self) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "tenant",
                    "tenant_id": "tenant-1",
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(
            decision.strategy,
            "policy.default_all",
        )
        self.assertEqual(
            decision.target_count,
            3,
        )

    def test_resolve_component_type_target(self) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "component_type",
                    "component_type": "node",
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.target_count, 1)
        self.assertEqual(decision.targets[0].component_type, "node")

    def test_resolve_capability_target_requires_all_capabilities(self) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "capability",
                    "capabilities": [
                        "task.execute",
                        "file.write",
                    ],
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.target_count, 1)
        self.assertEqual(decision.targets[0].identity, "node-1")

    def test_resolve_runtime_target_to_current_runtime(self) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "runtime",
                    "runtime_id": self.runtime_id,
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.target_count, 1)
        self.assertEqual(decision.targets[0].kind, "runtime")
        self.assertEqual(decision.targets[0].runtime_id, self.runtime_id)

    def test_unavailable_connection_target_raises(self) -> None:
        with self.assertRaises(NsRuntimeTargetUnavailableError):
            self.resolver.resolve(
                self._parse_target(
                    {
                        "kind": "connection",
                        "connection_id": "missing-connection",
                    }
                ),
                self.source_session,
            )

    def test_cross_tenant_connection_target_raises(self) -> None:
        other_tenant_session = self._activate(
            identity="client-2",
            tenant_id="tenant-2",
            component_type="client",
            capabilities=("task.execute",),
        )

        with self.assertRaises(NsRuntimeTenantMismatchError):
            self.resolver.resolve(
                self._parse_target(
                    {
                        "kind": "connection",
                        "connection_id": other_tenant_session.connection_id,
                    }
                ),
                self.source_session,
            )

    def _activate(self, *, identity: str, tenant_id: str, component_type: str, capabilities: tuple[str, ...]) -> RuntimeSessionContext:
        record = self.registry.create_handshaking(remote_address="test")
        return self.registry.activate(
            record,
            RuntimeAuthResult(
                accepted=True,
                identity=identity,
                tenant_id=tenant_id,
                component_type=component_type,  # type: ignore[arg-type]
                capabilities=capabilities,
                snapshot_id=f"snapshot:{identity}",
                issued_at=utc_now_iso(),
                expires_at=utc_now_iso(),
                iam_mode="cached",
                role="singleton",
            ),
        )

    def _parse_target(self, target: dict[str, Any]):
        frame = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "msg-1",
                "type": "task.dispatch",
                "category": "task",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "target": target,
        }
        return self.codec.parse_inbound(json.dumps(frame, ensure_ascii=False), self.source_session)

    def test_identity_default_strategy_selects_one_connection(
            self,
    ) -> None:
        second_session = self._activate(
            identity="client-1",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=(
                "task.execute",
            ),
        )

        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "identity",
                    "identity": "client-1",
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(
            decision.strategy,
            "policy.default_single",
        )
        self.assertEqual(
            decision.target_count,
            1,
        )

        expected_connection_id = min(
            self.client_session.connection_id,
            second_session.connection_id,
        )

        self.assertEqual(
            decision.targets[0].connection_id,
            expected_connection_id,
        )

    def test_capability_default_strategy_selects_one_connection(
            self,
    ) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "capability",
                    "capabilities": [
                        "task.execute",
                    ],
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(
            decision.strategy,
            "policy.default_single",
        )
        self.assertEqual(
            decision.target_count,
            1,
        )

        expected_connection_id = min(
            self.client_session.connection_id,
            self.node_session.connection_id,
        )

        self.assertEqual(
            decision.targets[0].connection_id,
            expected_connection_id,
        )

    def test_capability_all_strategy_keeps_all_connections(
            self,
    ) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "capability",
                    "capabilities": [
                        "task.execute",
                    ],
                    "strategy": "all",
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(
            decision.strategy,
            "all",
        )
        self.assertEqual(
            decision.target_count,
            2,
        )
        self.assertEqual(
            {
                target.connection_id
                for target in decision.targets
            },
            {
                self.client_session.connection_id,
                self.node_session.connection_id,
            },
        )

    def test_broadcast_default_strategy_keeps_all_connections(
            self,
    ) -> None:
        decision = self.resolver.resolve(
            self._parse_target(
                {
                    "kind": "broadcast",
                    "tenant_id": "tenant-1",
                }
            ),
            self.source_session,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(
            decision.strategy,
            "broadcast",
        )
        self.assertEqual(
            decision.target_count,
            3,
        )

    def test_broadcast_rejects_single_strategy(
            self,
    ) -> None:
        with self.assertRaises(
                NsRuntimeEnvelopeSchemaError
        ):
            self.resolver.resolve(
                self._parse_target(
                    {
                        "kind": "broadcast",
                        "tenant_id": "tenant-1",
                        "strategy": "single",
                    }
                ),
                self.source_session,
            )

if __name__ == "__main__":
    unittest.main()
