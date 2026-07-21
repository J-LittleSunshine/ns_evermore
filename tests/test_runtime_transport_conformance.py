# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.time import SystemClock
from ns_common.observability import InMemoryMetricsSink
from ns_runtime.transport import (
    TRANSPORT_CONFORMANCE_CASES,
    TransportCapability,
    TransportConformanceCase,
    TransportIdentityFactory,
    TransportMetricsRecorder,
    WebSocketTcpAdapter,
    WebSocketTcpAdapterOptions,
)
from tests.transport_conformance import (
    TransportConformanceHarness,
    TransportConformanceSuiteMixin,
)


@unittest.skipUnless(
    importlib.util.find_spec("websockets") is not None,
    "runtime transport dependency isn't installed",
)
class WebSocketTcpConformanceTestCase(
    TransportConformanceSuiteMixin,
    unittest.IsolatedAsyncioTestCase,
):
    expected_capabilities = frozenset({
        TransportCapability.RELIABLE_ORDERED_MESSAGES,
        TransportCapability.TRANSPORT_FLOW_CONTROL,
        TransportCapability.NATIVE_KEEPALIVE,
    })

    async def create_conformance_harness(self) -> TransportConformanceHarness:
        from websockets.asyncio.client import connect

        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.addAsyncCleanup(supervisor.shutdown)
        clock = SystemClock()
        adapter = WebSocketTcpAdapter(
            options=WebSocketTcpAdapterOptions(
                host="127.0.0.1",
                port=0,
                clock=clock,
                environment="test",
                allow_plaintext_non_prod=True,
                close_timeout_seconds=1,
                adapter_shutdown_timeout_seconds=1,
            ),
            task_supervisor=supervisor,
            identity_factory=TransportIdentityFactory(),
            metrics=TransportMetricsRecorder(
                clock=clock,
                sink=InMemoryMetricsSink(),
            ),
        )
        await adapter.start()
        self.addAsyncCleanup(adapter.close)
        client = await connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        )
        self.addAsyncCleanup(client.close)
        session = await adapter.accept()
        return TransportConformanceHarness(
            adapter=adapter,
            session=session,
            supervisor=supervisor,
            client=client,
            client_send_text=client.send,
            client_receive_text=client.recv,
            client_close=client.close,
            client_wait_closed=client.wait_closed,
        )

    def test_tc1_manifest_is_complete_and_unique(self) -> None:
        self.assertEqual(22, len(TRANSPORT_CONFORMANCE_CASES))
        self.assertEqual(
            set(TransportConformanceCase),
            set(TRANSPORT_CONFORMANCE_CASES),
        )
        self.assertEqual(
            len(TRANSPORT_CONFORMANCE_CASES),
            len({item.value for item in TRANSPORT_CONFORMANCE_CASES}),
        )
