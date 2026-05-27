# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

# 仅用于本地示例直接运行：将 src 目录加入 sys.path，便于 `python src/ns_runtime/examples/redis_valkey_broker_demo.py` 执行。
PROJECT_SRC_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC_PATH))

from ns_runtime import (  # noqa: E402
    RedisValkeyBroker,
    RedisValkeyBrokerConfig,
    RuntimePacket,
    RuntimePacketType,
)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    text = raw.strip()
    if not text:
        return default
    return int(text)


def _env_optional_text(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    text = raw.strip()
    return text or None


def main() -> None:
    backend = os.getenv("NS_RUNTIME_BROKER_BACKEND", "redis")
    url = _env_optional_text("NS_RUNTIME_BROKER_URL")
    host = os.getenv("NS_RUNTIME_BROKER_HOST", "127.0.0.1")
    port = _env_int("NS_RUNTIME_BROKER_PORT", 6379)
    db = _env_int("NS_RUNTIME_BROKER_DB", 0)
    prefix = os.getenv("NS_RUNTIME_BROKER_PREFIX", "ns:runtime:demo")
    username = _env_optional_text("NS_RUNTIME_BROKER_USERNAME")
    password = _env_optional_text("NS_RUNTIME_BROKER_PASSWORD")

    config = RedisValkeyBrokerConfig(
        backend=backend,
        url=url,
        host=host,
        port=port,
        db=db,
        username=username,
        password=password,
        key_prefix=prefix,
    )
    broker = RedisValkeyBroker(config=config)

    run_id = uuid4().hex[:8]
    topic = f"demo.topic.{run_id}"
    kv_key = f"demo.key.{run_id}"
    stream = f"demo.stream.{run_id}"
    group = f"demo.group.{run_id}"
    consumer = f"demo.consumer.{run_id}"
    lock_name = f"demo.lock.{run_id}"
    lock_owner = f"demo-owner-{run_id}"

    started = False
    try:
        broker.start()
        started = True
        # 启动信息仅输出认证是否启用，避免泄露 password 或 URL 中可能包含的敏感信息。
        auth_enabled = bool(password) or (url is not None and "@" in url) or (username is not None)
        url_flag = "provided" if url else "none"
        print(
            f"[broker] started backend={backend} host={host} port={port} db={db} "
            f"prefix={prefix} auth={'enabled' if auth_enabled else 'disabled'} url={url_flag}"
        )

        packet = RuntimePacket.create(
            packet_type=RuntimePacketType.EVENT,
            source_endpoint_id="demo-runtime",
            topic=topic,
            payload={"run_id": run_id, "step": "publish_poll"},
        )
        broker.publish(topic, packet)
        polled = broker.poll(topic, max_count=1)
        print("[publish/poll]", len(polled), polled[0].payload if polled else {})

        broker.set_value(kv_key, f"value-{run_id}", expire_seconds=120)
        current = broker.get_value(kv_key)
        deleted = broker.delete_value(kv_key)
        print("[key-value]", current, deleted)

        stream_packet = RuntimePacket.create(
            packet_type=RuntimePacketType.EVENT,
            source_endpoint_id="demo-runtime",
            topic=stream,
            payload={"run_id": run_id, "step": "stream"},
        )
        message_id = broker.append_stream(stream, stream_packet)
        broker.create_consumer_group(stream, group, start_id="0", mkstream=True)
        stream_messages = broker.read_group(stream, group, consumer, count=10, block_ms=200)
        acked = 0
        if stream_messages:
            acked = broker.ack_stream(stream, group, stream_messages[0].message_id)
        print("[stream]", message_id, len(stream_messages), acked)

        acquired = broker.acquire_lock(lock_name, lock_owner, ttl_seconds=30)
        released = broker.release_lock(lock_name, lock_owner)
        print("[lock]", acquired, released)

    except RuntimeError as exc:
        print("[runtime error]", exc)
        print("请确认已安装对应客户端包：redis 或 valkey。")
    except Exception as exc:
        print("[connection or operation error]", exc)
        print("请确认本地 Redis/Valkey 服务已启动，且连接参数正确。")
        print("如果 Redis/Valkey 开启认证，请设置 NS_RUNTIME_BROKER_PASSWORD 或使用带认证信息的 NS_RUNTIME_BROKER_URL。")
    finally:
        if started:
            broker.stop()
            print("[broker] stopped")


if __name__ == "__main__":
    main()

