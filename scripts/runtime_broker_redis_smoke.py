# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
from collections.abc import Awaitable, Callable
from typing import Any

from ns_common.runtime.broker import (
    NsRuntimeBrokerEnvelope,
    RUNTIME_BROKER_EVENT_NODE_PING,
    RUNTIME_BROKER_EVENT_NODE_PONG,
    build_runtime_broker,
    build_runtime_broker_cluster_channel,
    build_runtime_broker_node_channel,
)
from ns_common.runtime.config import NsRuntimeConfig
from ns_runtime.core import NsRuntimeNode


async def _wait_for_payload(_subscribe: Callable[[], Awaitable[bytes]], _timeout_seconds: float) -> bytes:
    """Wait for one broker payload."""
    return await asyncio.wait_for(_subscribe(), timeout=_timeout_seconds)


async def _read_one_from_channel(_node: NsRuntimeNode, _channel: str) -> bytes:
    """Read one payload from one broker channel."""
    async for payload in _node._broker.subscribe(_channel):  # noqa: SLF001
        return payload

    raise RuntimeError("runtime broker subscription ended before receiving payload")


async def _smoke_cluster_channel(_publisher: NsRuntimeNode, _subscriber: NsRuntimeNode, _timeout_seconds: float) -> None:
    """Verify cluster channel pub/sub."""
    channel = build_runtime_broker_cluster_channel()
    envelope = NsRuntimeBrokerEnvelope(
        event_type=RUNTIME_BROKER_EVENT_NODE_PING,
        source_node_id=_publisher._config.node_id,  # noqa: SLF001
        payload={
            "scope": "cluster",
        },
    )

    task = asyncio.create_task(_read_one_from_channel(_subscriber, channel))
    await asyncio.sleep(0.2)

    await _publisher.publish_broker_envelope(envelope, channel=channel)

    payload = await _wait_for_payload(lambda: task, _timeout_seconds)
    decoded = NsRuntimeBrokerEnvelope.from_bytes(payload)

    assert decoded.event_type == RUNTIME_BROKER_EVENT_NODE_PING
    assert decoded.source_node_id == _publisher._config.node_id  # noqa: SLF001
    assert decoded.payload["scope"] == "cluster"


async def _smoke_node_channel(_publisher: NsRuntimeNode, _subscriber: NsRuntimeNode, _timeout_seconds: float) -> None:
    """Verify node channel pub/sub."""
    target_node_id = _subscriber._config.node_id  # noqa: SLF001
    channel = build_runtime_broker_node_channel(node_id=target_node_id)
    envelope = NsRuntimeBrokerEnvelope(
        event_type=RUNTIME_BROKER_EVENT_NODE_PING,
        source_node_id=_publisher._config.node_id,  # noqa: SLF001
        target_node_id=target_node_id,
        payload={
            "scope": "node",
        },
    )

    task = asyncio.create_task(_read_one_from_channel(_subscriber, channel))
    await asyncio.sleep(0.2)

    await _publisher.publish_broker_envelope(envelope, channel=channel)

    payload = await _wait_for_payload(lambda: task, _timeout_seconds)
    decoded = NsRuntimeBrokerEnvelope.from_bytes(payload)

    assert decoded.event_type == RUNTIME_BROKER_EVENT_NODE_PING
    assert decoded.source_node_id == _publisher._config.node_id  # noqa: SLF001
    assert decoded.target_node_id == target_node_id
    assert decoded.payload["scope"] == "node"


async def _smoke_ping_pong_helpers(_publisher: NsRuntimeNode, _subscriber: NsRuntimeNode, _timeout_seconds: float) -> None:
    """Verify ping/pong helper publication paths."""
    target_node_id = _subscriber._config.node_id  # noqa: SLF001
    node_channel = build_runtime_broker_node_channel(node_id=target_node_id)

    ping_task = asyncio.create_task(_read_one_from_channel(_subscriber, node_channel))
    await asyncio.sleep(0.2)

    ping = await _publisher.publish_broker_ping_event(
        target_node_id=target_node_id,
        trace_id="redis-smoke-ping",
    )

    ping_payload = await _wait_for_payload(lambda: ping_task, _timeout_seconds)
    decoded_ping = NsRuntimeBrokerEnvelope.from_bytes(ping_payload)

    assert ping.event_type == RUNTIME_BROKER_EVENT_NODE_PING
    assert decoded_ping.event_type == RUNTIME_BROKER_EVENT_NODE_PING
    assert decoded_ping.target_node_id == target_node_id
    assert decoded_ping.trace_id == "redis-smoke-ping"

    publisher_node_id = _publisher._config.node_id  # noqa: SLF001
    publisher_channel = build_runtime_broker_node_channel(node_id=publisher_node_id)
    pong_task = asyncio.create_task(_read_one_from_channel(_publisher, publisher_channel))
    await asyncio.sleep(0.2)

    pong = await _subscriber.publish_broker_pong_event(
        target_node_id=publisher_node_id,
        trace_id="redis-smoke-pong",
    )

    pong_payload = await _wait_for_payload(lambda: pong_task, _timeout_seconds)
    decoded_pong = NsRuntimeBrokerEnvelope.from_bytes(pong_payload)

    assert pong.event_type == RUNTIME_BROKER_EVENT_NODE_PONG
    assert decoded_pong.event_type == RUNTIME_BROKER_EVENT_NODE_PONG
    assert decoded_pong.target_node_id == publisher_node_id
    assert decoded_pong.trace_id == "redis-smoke-pong"


async def run_smoke(*, redis_url: str, timeout_seconds: float) -> None:
    """Run Redis/ValKey runtime broker smoke checks."""
    publisher_config = NsRuntimeConfig(
        enabled=True,
        node_id="runtime-smoke-a",
        runtime_broker_backend="redis",
        runtime_broker_location=redis_url,
    )
    subscriber_config = NsRuntimeConfig(
        enabled=True,
        node_id="runtime-smoke-b",
        runtime_broker_backend="redis",
        runtime_broker_location=redis_url,
    )

    publisher_config.validate()
    subscriber_config.validate()

    publisher = NsRuntimeNode(config=publisher_config)
    subscriber = NsRuntimeNode(config=subscriber_config)

    try:
        # Build factory once directly to catch broker factory regressions outside
        # NsRuntimeNode construction.
        broker = build_runtime_broker(publisher_config)
        await broker.close()

        await _smoke_cluster_channel(publisher, subscriber, timeout_seconds)
        await _smoke_node_channel(publisher, subscriber, timeout_seconds)
        await _smoke_ping_pong_helpers(publisher, subscriber, timeout_seconds)
    finally:
        with contextlib.suppress(Exception):
            await publisher._close_broker()  # noqa: SLF001

        with contextlib.suppress(Exception):
            await subscriber._close_broker()  # noqa: SLF001


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Run manual runtime Redis/ValKey broker smoke checks.")
    parser.add_argument(
        "--redis-url",
        default=os.getenv("NS_RUNTIME_BROKER_REDIS_URL", "redis://127.0.0.1:6379/0"),
        help="Redis/ValKey connection URL. Defaults to NS_RUNTIME_BROKER_REDIS_URL or redis://127.0.0.1:6379/0.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("NS_RUNTIME_BROKER_SMOKE_TIMEOUT", "10")),
        help="Timeout seconds for each smoke receive.",
    )
    args = parser.parse_args()

    asyncio.run(
        run_smoke(
            redis_url=str(args.redis_url),
            timeout_seconds=float(args.timeout),
        )
    )

    print("runtime redis broker smoke ok")


if __name__ == "__main__":
    main()
