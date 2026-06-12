# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any

from _runtime_script_path import ensure_runtime_import_paths

ensure_runtime_import_paths(__file__)
from ns_common.runtime.broker import (
    NsRuntimeBrokerEnvelope,
    RUNTIME_BROKER_EVENT_MESSAGE_FORWARD,
    RUNTIME_BROKER_EVENT_NODE_PING,
    RUNTIME_BROKER_EVENT_NODE_PONG,
    build_runtime_broker,
    build_runtime_broker_cluster_channel,
    build_runtime_broker_message_forward_envelope,
    build_runtime_broker_node_channel,
    runtime_message_from_broker_forward_envelope,
)
from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import RUNTIME_TARGET_BROADCAST
from ns_common.runtime.messages import NsRuntimeMessage
from ns_runtime.core import NsRuntimeNode


class RuntimeBrokerMemorySmokeError(RuntimeError):
    """Runtime memory broker smoke failed."""


async def _cancel_task(_task: asyncio.Task[Any]) -> None:
    """Cancel and drain one asyncio task."""
    if _task.done():
        with contextlib.suppress(Exception):
            _task.result()
        return

    _task.cancel()
    with contextlib.suppress(asyncio.CancelledError, Exception):
        await _task


async def _read_one_from_broker(_broker: Any, _channel: str) -> bytes:
    """Read one payload from one broker channel."""
    payload_iterator: AsyncIterator[bytes] = _broker.subscribe(_channel)

    async for payload in payload_iterator:
        return payload

    raise RuntimeBrokerMemorySmokeError(f"runtime memory broker subscription ended before receiving payload: channel={_channel}")


async def _wait_for_payload(_task: asyncio.Task[bytes], _timeout_seconds: float, _channel: str) -> bytes:
    """Wait for one broker payload and cancel subscription task on timeout."""
    try:
        return await asyncio.wait_for(_task, timeout=_timeout_seconds)
    except asyncio.TimeoutError as exc:
        await _cancel_task(_task)
        raise RuntimeBrokerMemorySmokeError(f"runtime memory broker receive timed out: channel={_channel}, timeout={_timeout_seconds}") from exc
    except Exception as exc:
        await _cancel_task(_task)
        raise RuntimeBrokerMemorySmokeError(f"runtime memory broker receive failed: channel={_channel}, error={exc}") from exc


async def _smoke_cluster_channel(_broker: Any, _timeout_seconds: float) -> None:
    """Verify memory broker cluster channel pub/sub."""
    channel = build_runtime_broker_cluster_channel()
    envelope = NsRuntimeBrokerEnvelope(
        event_type=RUNTIME_BROKER_EVENT_NODE_PING,
        source_node_id="runtime-memory-smoke-a",
        payload={
            "scope": "cluster",
        },
    )

    task = asyncio.create_task(_read_one_from_broker(_broker, channel))
    try:
        await asyncio.sleep(0.05)
        await _broker.publish(channel, envelope.to_bytes())
        payload = await _wait_for_payload(task, _timeout_seconds, channel)
    except Exception as exc:
        await _cancel_task(task)
        raise RuntimeBrokerMemorySmokeError(f"runtime memory broker cluster channel smoke failed: {exc}") from exc

    decoded = NsRuntimeBrokerEnvelope.from_bytes(payload)

    assert decoded.event_type == RUNTIME_BROKER_EVENT_NODE_PING
    assert decoded.source_node_id == "runtime-memory-smoke-a"
    assert decoded.payload["scope"] == "cluster"


async def _smoke_node_channel(_broker: Any, _timeout_seconds: float) -> None:
    """Verify memory broker node channel pub/sub."""
    target_node_id = "runtime-memory-smoke-b"
    channel = build_runtime_broker_node_channel(node_id=target_node_id)
    envelope = NsRuntimeBrokerEnvelope(
        event_type=RUNTIME_BROKER_EVENT_NODE_PING,
        source_node_id="runtime-memory-smoke-a",
        target_node_id=target_node_id,
        payload={
            "scope": "node",
        },
    )

    task = asyncio.create_task(_read_one_from_broker(_broker, channel))
    try:
        await asyncio.sleep(0.05)
        await _broker.publish(channel, envelope.to_bytes())
        payload = await _wait_for_payload(task, _timeout_seconds, channel)
    except Exception as exc:
        await _cancel_task(task)
        raise RuntimeBrokerMemorySmokeError(f"runtime memory broker node channel smoke failed: {exc}") from exc

    decoded = NsRuntimeBrokerEnvelope.from_bytes(payload)

    assert decoded.event_type == RUNTIME_BROKER_EVENT_NODE_PING
    assert decoded.source_node_id == "runtime-memory-smoke-a"
    assert decoded.target_node_id == target_node_id
    assert decoded.payload["scope"] == "node"


def _smoke_message_forward_envelope() -> None:
    """Verify runtime.message.forward envelope build and parse."""
    message = NsRuntimeMessage.new(
        topic="runtime.smoke",
        event="broker.memory.forward",
        payload={
            "ok": True,
        },
        target_type=RUNTIME_TARGET_BROADCAST,
        producer_id="runtime-memory-smoke",
    )

    envelope = build_runtime_broker_message_forward_envelope(
        source_node_id="runtime-memory-smoke-a",
        target_node_id="runtime-memory-smoke-b",
        message=message,
        trace_id="memory-forward-smoke",
    )

    assert envelope.event_type == RUNTIME_BROKER_EVENT_MESSAGE_FORWARD
    assert envelope.source_node_id == "runtime-memory-smoke-a"
    assert envelope.target_node_id == "runtime-memory-smoke-b"
    assert envelope.trace_id == "memory-forward-smoke"

    parsed_message = runtime_message_from_broker_forward_envelope(envelope)

    assert parsed_message.message_id == message.message_id
    assert parsed_message.topic == "runtime.smoke"
    assert parsed_message.event == "broker.memory.forward"
    assert parsed_message.payload["ok"] is True


async def _read_one_from_node_broker(_node: NsRuntimeNode, _channel: str) -> bytes:
    """Read one payload from runtime node broker."""
    async for payload in _node._broker.subscribe(_channel):  # noqa: SLF001
        return payload

    raise RuntimeBrokerMemorySmokeError(f"runtime node memory broker subscription ended before receiving payload: channel={_channel}")


async def _smoke_node_ping_pong_helpers(_timeout_seconds: float) -> None:
    """Verify NsRuntimeNode ping/pong helper publication paths with memory broker."""
    node = NsRuntimeNode(
        config=NsRuntimeConfig(
            enabled=True,
            node_id="runtime-memory-smoke-node",
            runtime_broker_backend="memory",
        )
    )

    try:
        node_channel = build_runtime_broker_node_channel(node_id="runtime-memory-smoke-node")
        ping_task = asyncio.create_task(_read_one_from_node_broker(node, node_channel))

        try:
            await asyncio.sleep(0.05)
            ping = await node.publish_broker_ping_event(
                target_node_id="runtime-memory-smoke-node",
                trace_id="memory-smoke-ping",
            )
            ping_payload = await _wait_for_payload(ping_task, _timeout_seconds, node_channel)
        except Exception as exc:
            await _cancel_task(ping_task)
            raise RuntimeBrokerMemorySmokeError(f"runtime memory broker ping helper smoke failed: {exc}") from exc

        decoded_ping = NsRuntimeBrokerEnvelope.from_bytes(ping_payload)

        assert ping.event_type == RUNTIME_BROKER_EVENT_NODE_PING
        assert decoded_ping.event_type == RUNTIME_BROKER_EVENT_NODE_PING
        assert decoded_ping.target_node_id == "runtime-memory-smoke-node"
        assert decoded_ping.trace_id == "memory-smoke-ping"

        pong_task = asyncio.create_task(_read_one_from_node_broker(node, node_channel))

        try:
            await asyncio.sleep(0.05)
            pong = await node.publish_broker_pong_event(
                target_node_id="runtime-memory-smoke-node",
                trace_id="memory-smoke-pong",
            )
            pong_payload = await _wait_for_payload(pong_task, _timeout_seconds, node_channel)
        except Exception as exc:
            await _cancel_task(pong_task)
            raise RuntimeBrokerMemorySmokeError(f"runtime memory broker pong helper smoke failed: {exc}") from exc

        decoded_pong = NsRuntimeBrokerEnvelope.from_bytes(pong_payload)

        assert pong.event_type == RUNTIME_BROKER_EVENT_NODE_PONG
        assert decoded_pong.event_type == RUNTIME_BROKER_EVENT_NODE_PONG
        assert decoded_pong.target_node_id == "runtime-memory-smoke-node"
        assert decoded_pong.trace_id == "memory-smoke-pong"
    finally:
        with contextlib.suppress(Exception):
            await node._close_broker()  # noqa: SLF001


async def run_smoke(*, timeout_seconds: float) -> None:
    """Run memory runtime broker smoke checks."""
    config = NsRuntimeConfig(
        enabled=True,
        runtime_broker_backend="memory",
    )
    config.validate()

    broker = build_runtime_broker(config)

    try:
        await _smoke_cluster_channel(broker, timeout_seconds)
        await _smoke_node_channel(broker, timeout_seconds)
        _smoke_message_forward_envelope()
        await _smoke_node_ping_pong_helpers(timeout_seconds)
    finally:
        with contextlib.suppress(Exception):
            await broker.close()


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Run manual runtime memory broker smoke checks.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout seconds for each memory broker receive.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            run_smoke(
                timeout_seconds=float(args.timeout),
            )
        )
    except RuntimeBrokerMemorySmokeError as exc:
        raise SystemExit(f"runtime memory broker smoke failed: {exc}") from exc

    print("runtime memory broker smoke ok")


if __name__ == "__main__":
    main()
