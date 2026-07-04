# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from typing import TYPE_CHECKING

from ns_runtime.auth import RuntimeAuthResult
from ns_runtime.models import utc_now_iso
from ns_runtime.session import RuntimeSessionRegistry

if TYPE_CHECKING:
    pass


class RuntimeSessionRegistryTestCase(unittest.TestCase):
    def test_activate_adds_and_close_removes_active_indexes(self) -> None:
        registry = RuntimeSessionRegistry(runtime_id="runtime-test")
        record = registry.create_handshaking(remote_address="test")
        auth_result = RuntimeAuthResult(
            accepted=True,
            identity="user-1",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=("runtime.management", "task.dispatch"),
            snapshot_id="snapshot-1",
            issued_at=utc_now_iso(),
            expires_at=utc_now_iso(),
            iam_mode="cached",
            role="singleton",
        )

        session = registry.activate(record, auth_result)

        self.assertEqual(registry.get_active_session(record.connection_id), session)
        self.assertEqual(registry.get_by_session_id(session.session_id), record)
        self.assertEqual(registry.list_by_identity("user-1"), (record,))
        self.assertEqual(registry.list_by_tenant("tenant-1"), (record,))
        self.assertEqual(registry.list_by_component_type("management"), (record,))
        self.assertEqual(registry.list_by_capability("runtime.management"), (record,))
        self.assertEqual(registry.list_by_capability("task.dispatch"), (record,))
        self.assertEqual(registry.build_health_snapshot()["active_connection_count"], 1)

        registry.close(record, reason="test close")

        self.assertIsNone(registry.get_active_session(record.connection_id))
        self.assertEqual(registry.list_by_identity("user-1"), ())
        self.assertEqual(registry.list_by_tenant("tenant-1"), ())
        self.assertEqual(registry.list_by_component_type("management"), ())
        self.assertEqual(registry.list_by_capability("runtime.management"), ())
        self.assertEqual(registry.build_health_snapshot()["active_connection_count"], 0)


if __name__ == "__main__":
    unittest.main()
