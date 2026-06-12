# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urlsplit, urlunsplit

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


class RuntimeBrokerSmokeError(RuntimeError):
    """Runtime broker smoke failed."""


def _redact_redis_url(_redis_url: str) -> str:
    """Return Redis URL with password redacted for logs."""
    raw_url = str(_redis_url or "").strip()
    if not raw_url:
        return ""

    parsed = urlsplit(raw_url)
    if not parsed.netloc:
        return raw_url

    username = parsed.username or ""
    password = parsed.password
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port is not None else ""

    if password is None:
        return raw_url

    auth = f"{username}:***@" if username else ":***@"
    return urlunsplit(
        (
            parsed.scheme,
            f"{auth}{hostname}{port}",
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )


def _redis_auth_hint(_error: Exception) -> str:
    """Return Redis auth troubleshooting hint when applicable."""
    error_text = str(_error or "")
    if "Authentication required" not in error_text and "invalid username-password pair" not in error_text:
        return ""

    return (
        " Redis authentication failed. Pass a credentialed URL with "
        "--redis-url or NS_RUNTIME_BROKER_REDIS_URL. Examples: "
        "redis://:PASSWORD@127.0.0.1:6379/0 or "
        "redis://USERNAME:PASSWORD@127.0.0.1:6379/0."
    )


async def _cancel_task(_task: asyncio.Task[Any]) -> None:
    """Cancel and drain one asyncio task."""
    if _task.done():
        with contextlib.suppress(Exception):
            _task.result()
        return

    _task.cancel()
    with contextlib.suppress(asyncio.CancelledError, Exception):
        await _task


async def _read_one_from_channel(_node: NsRuntimeNode, _channel: str) -> bytes:
    """Read one payload from one broker channel."""
    payload_iterator: AsyncIterator[bytes] = _node._broker.subscribe(_channel)  # noqa: SLF001

    async for payload in payload_iterator:
        return payload

    raise RuntimeBrokerSmokeError(f"runtime broker subscription ended before receiving payload: channel={_channel}")


async def _wait_for_channel_payload(_task: asyncio.Task[bytes], _timeout_seconds: float, _channel: str) -> bytes:
    """Wait for one broker payload and cancel subscription task on timeout."""
    try:
        return await asyncio.wait_for(_task, timeout=_timeout_seconds)
    except asyncio.TimeoutError as exc:
        await _cancel_task(_task)
        raise RuntimeBrokerSmokeError(f"runtime broker smoke receive timed out: channel={_channel}, timeout={_timeout_seconds}") from exc
    except Exception as exc:
        await _cancel_task(_task)
        raise RuntimeBrokerSmokeError(f"runtime broker smoke receive failed: channel={_channel}, error={exc}") from exc


async def _preflight_broker(_config: NsRuntimeConfig) -> None:
    """Verify broker connectivity before smoke checks."""
    broker = build_runtime_broker(_config)
    channel = build_runtime_broker_node_channel(node_id=_config.node_id)
    envelope = NsRuntimeBrokerEnvelope(
        event_type=RUNTIME_BROKER_EVENT_NODE_PING,
        source_node_id=_config.node_id,
        payload={
            "scope": "preflight",
        },
    )

    try:
        await broker.publish(channel, envelope.to_bytes())
    except Exception as exc:
        hint = _redis_auth_hint(exc)
        raise RuntimeBrokerSmokeError(f"runtime redis broker preflight failed: {exc}.{hint}") from exc
    finally:
        with contextlib.suppress(Exception):
            await broker.close()


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
    try:
        await asyncio.sleep(0.2)
        await _publisher.publish_broker_envelope(envelope, channel=channel)
        payload = await _wait_for_channel_payload(task, _timeout_seconds, channel)
    except Exception as exc:
        await _cancel_task(task)
        hint = _redis_auth_hint(exc)
        raise RuntimeBrokerSmokeError(f"runtime broker cluster channel smoke failed: {exc}.{hint}") from exc

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
    try:
        await asyncio.sleep(0.2)
        await _publisher.publish_broker_envelope(envelope, channel=channel)
        payload = await _wait_for_channel_payload(task, _timeout_seconds, channel)
    except Exception as exc:
        await _cancel_task(task)
        hint = _redis_auth_hint(exc)
        raise RuntimeBrokerSmokeError(f"runtime broker node channel smoke failed: {exc}.{hint}") from exc

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
    try:
        await asyncio.sleep(0.2)
        ping = await _publisher.publish_broker_ping_event(
            target_node_id=target_node_id,
            trace_id="redis-smoke-ping",
        )
        ping_payload = await _wait_for_channel_payload(ping_task, _timeout_seconds, node_channel)
    except Exception as exc:
        await _cancel_task(ping_task)
        hint = _redis_auth_hint(exc)
        raise RuntimeBrokerSmokeError(f"runtime broker ping helper smoke failed: {exc}.{hint}") from exc

    decoded_ping = NsRuntimeBrokerEnvelope.from_bytes(ping_payload)

    assert ping.event_type == RUNTIME_BROKER_EVENT_NODE_PING
    assert decoded_ping.event_type == RUNTIME_BROKER_EVENT_NODE_PING
    assert decoded_ping.target_node_id == target_node_id
    assert decoded_ping.trace_id == "redis-smoke-ping"

    publisher_node_id = _publisher._config.node_id  # noqa: SLF001
    publisher_channel = build_runtime_broker_node_channel(node_id=publisher_node_id)
    pong_task = asyncio.create_task(_read_one_from_channel(_publisher, publisher_channel))

    try:
        await asyncio.sleep(0.2)
        pong = await _subscriber.publish_broker_pong_event(
            target_node_id=publisher_node_id,
            trace_id="redis-smoke-pong",
        )
        pong_payload = await _wait_for_channel_payload(pong_task, _timeout_seconds, publisher_channel)
    except Exception as exc:
        await _cancel_task(pong_task)
        hint = _redis_auth_hint(exc)
        raise RuntimeBrokerSmokeError(f"runtime broker pong helper smoke failed: {exc}.{hint}") from exc

    decoded_pong = NsRuntimeBrokerEnvelope.from_bytes(pong_payload)

    assert pong.event_type == RUNTIME_BROKER_EVENT_NODE_PONG
    assert decoded_pong.event_type == RUNTIME_BROKER_EVENT_NODE_PONG
    assert decoded_pong.target_node_id == publisher_node_id
    assert decoded_pong.trace_id == "redis-smoke-pong"


async def run_smoke(*, redis_url: str, timeout_seconds: float) -> None:
    """Run Redis/ValKey runtime broker smoke checks."""
    normalized_redis_url = str(redis_url or "").strip()
    if not normalized_redis_url:
        raise RuntimeBrokerSmokeError("runtime redis broker smoke requires non-empty redis_url")

    publisher_config = NsRuntimeConfig(
        enabled=True,
        node_id="runtime-smoke-a",
        runtime_broker_backend="redis",
        runtime_broker_location=normalized_redis_url,
    )
    subscriber_config = NsRuntimeConfig(
        enabled=True,
        node_id="runtime-smoke-b",
        runtime_broker_backend="redis",
        runtime_broker_location=normalized_redis_url,
    )

    publisher_config.validate()
    subscriber_config.validate()

    print(f"runtime redis broker smoke target: {_redact_redis_url(normalized_redis_url)}")

    await _preflight_broker(publisher_config)

    publisher = NsRuntimeNode(config=publisher_config)
    subscriber = NsRuntimeNode(config=subscriber_config)

    try:
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
        default=float(os.getenv("NS_RUNTIME_BROKER_SMOKE_TIMEOUT", "5")),
        help="Timeout seconds for each smoke receive.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            run_smoke(
                redis_url=str(args.redis_url),
                timeout_seconds=float(args.timeout),
            )
        )
    except RuntimeBrokerSmokeError as exc:
        raise SystemExit(f"runtime redis broker smoke failed: {exc}") from exc

    print("runtime redis broker smoke ok")


if __name__ == "__main__":
    main()
