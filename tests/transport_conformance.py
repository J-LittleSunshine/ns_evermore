# -*- coding: utf-8 -*-
"""Reusable TC-1 behavior mixin.

Concrete adapter test classes provide ``create_conformance_harness``. Raw frame,
TLS policy, deterministic slow-I/O and dependency-isolation cases remain
adapter-specific but are required by the production TC-1 manifest.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from ns_common.async_runtime import TaskSupervisor
from ns_runtime.transport import (
    TransportAdapter,
    TransportCapability,
    TransportCloseReason,
    TransportSession,
    TransportSessionState,
    TransportWriteResult,
    TransportWriteState,
)


AsyncAction = Callable[[], Awaitable[None]]


@dataclass(slots=True)
class TransportConformanceHarness:
    adapter: TransportAdapter
    session: TransportSession
    supervisor: TaskSupervisor
    client: Any = None
    client_send_text: Callable[[str], Awaitable[None]] | None = None
    client_receive_text: Callable[[], Awaitable[str]] | None = None
    client_close: AsyncAction | None = None
    client_wait_closed: AsyncAction | None = None


class TransportConformanceSuiteMixin:
    expected_capabilities: frozenset[TransportCapability]

    async def create_conformance_harness(self) -> TransportConformanceHarness:
        raise NotImplementedError

    async def test_tc1_capability_declaration_is_authoritative(self) -> None:
        harness = await self.create_conformance_harness()
        self.assertEqual(  # type: ignore[attr-defined]
            self.expected_capabilities,
            harness.adapter.capabilities.supported,
        )
        self.assertIs(harness.adapter.capabilities, harness.session.capabilities)  # type: ignore[attr-defined]

    async def test_tc1_text_boundary_and_native_keepalive(self) -> None:
        harness = await self.create_conformance_harness()
        assert harness.client_send_text is not None
        assert harness.client_receive_text is not None
        text = "完整 UTF-8 message 🌐"
        await harness.client_send_text(text)
        received = await harness.session.receive()
        self.assertEqual(text, received.text)  # type: ignore[attr-defined]
        self.assertEqual(len(text.encode("utf-8")), received.byte_size)  # type: ignore[attr-defined]
        await harness.session.send("runtime response")
        self.assertEqual("runtime response", await harness.client_receive_text())  # type: ignore[attr-defined]
        await harness.session.ping()

    async def test_tc1_concurrent_send_is_ordered_and_not_runtime_ack(self) -> None:
        harness = await self.create_conformance_harness()
        assert harness.client_receive_text is not None
        messages = [f"message-{index}" for index in range(20)]
        results = await asyncio.gather(*(
            harness.session.send(message)
            for message in messages
        ))
        self.assertTrue(all(  # type: ignore[attr-defined]
            type(result) is TransportWriteResult
            and result.state is TransportWriteState.SUCCEEDED
            for result in results
        ))
        received = [
            await harness.client_receive_text()
            for _ in messages
        ]
        self.assertEqual(messages, received)  # type: ignore[attr-defined]
        self.assertFalse(any(  # type: ignore[attr-defined]
            "ack" in name.casefold() or "delivery" in name.casefold()
            for name in harness.supervisor.task_names
        ))
        self.assertFalse(hasattr(harness.session, "ack"))  # type: ignore[attr-defined]
        self.assertFalse(hasattr(harness.session, "delivery_record"))  # type: ignore[attr-defined]

    async def test_tc1_stop_admission_drain_and_close_order(self) -> None:
        harness = await self.create_conformance_harness()
        assert harness.client_receive_text is not None
        assert harness.client_wait_closed is not None
        await harness.adapter.stop_admission()
        self.assertFalse(harness.adapter.accepting)  # type: ignore[attr-defined]
        await harness.session.send("existing-session-during-drain")
        self.assertEqual(  # type: ignore[attr-defined]
            "existing-session-during-drain",
            await harness.client_receive_text(),
        )
        await harness.adapter.drain()
        await harness.client_wait_closed()
        self.assertEqual(TransportSessionState.CLOSED, harness.session.state)  # type: ignore[attr-defined]
        self.assertEqual(  # type: ignore[attr-defined]
            TransportCloseReason.ADAPTER_SHUTDOWN,
            harness.session.close_info.reason,
        )
        await harness.adapter.close()
        await harness.adapter.close()

    async def test_tc1_remote_and_local_close_are_idempotent(self) -> None:
        harness = await self.create_conformance_harness()
        closes = await asyncio.gather(*(harness.session.close() for _ in range(8)))
        self.assertTrue(all(item is closes[0] for item in closes))  # type: ignore[attr-defined]
        self.assertEqual(TransportCloseReason.NORMAL, closes[0].reason)  # type: ignore[attr-defined]
