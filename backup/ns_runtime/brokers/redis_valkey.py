# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

from ns_common.protocol import RuntimePacket, RuntimePacketCodec
from ns_runtime.brokers.base import RuntimeBroker


@dataclass(frozen=True)
class RedisValkeyBrokerConfig:
    backend: str = "redis"
    url: str | None = None
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    username: str | None = None
    password: str | None = None
    socket_timeout: float = 5.0
    decode_responses: bool = True
    key_prefix: str = "ns:runtime"

    def __post_init__(self) -> None:
        backend = self.backend.strip().lower()
        host = self.host.strip()
        key_prefix = self.key_prefix.strip().rstrip(":")
        url = self.url.strip() if isinstance(self.url, str) else None
        username = self.username.strip() if isinstance(self.username, str) else None

        if backend not in {"redis", "valkey"}:
            raise ValueError("backend must be redis or valkey")
        if not host:
            raise ValueError("host must be non-empty")
        if not key_prefix:
            raise ValueError("key_prefix must be non-empty")
        if not (1 <= self.port <= 65535):
            raise ValueError("port must be between 1 and 65535")
        if self.db < 0:
            raise ValueError("db must be >= 0")
        if self.socket_timeout <= 0:
            raise ValueError("socket_timeout must be > 0")

        password = self.password if self.password is None else str(self.password)
        normalized_url = url or None
        normalized_username = username or None

        # key_prefix 用于多环境、多实例或多租户前缀隔离，避免不同运行时互相污染键空间。
        object.__setattr__(self, "backend", backend)
        object.__setattr__(self, "host", host)
        object.__setattr__(self, "key_prefix", key_prefix)
        object.__setattr__(self, "url", normalized_url)
        object.__setattr__(self, "username", normalized_username)
        object.__setattr__(self, "password", password)


@dataclass(frozen=True)
class StreamMessage:
    stream: str
    message_id: str
    packet: RuntimePacket


class RedisValkeyBroker(RuntimeBroker):
    def __init__(
        self,
        config: RedisValkeyBrokerConfig | None = None,
        client: Any | None = None,
        codec: RuntimePacketCodec | None = None,
    ) -> None:
        self._config = config or RedisValkeyBrokerConfig()
        self._client: Any | None = client
        self._codec = codec or RuntimePacketCodec()
        self._running = False
        self._owns_client = client is None

    def start(self) -> None:
        client = self._ensure_client()
        client.ping()
        self._running = True

    def stop(self) -> None:
        self._running = False
        client = self._client
        if client is None:
            return

        close_method = getattr(client, "close", None)
        if callable(close_method):
            # 关闭连接属于清理动作，不应因为清理失败阻断运行时 stop 主流程。
            try:
                close_method()
            except Exception:
                pass

        if self._owns_client:
            self._client = None

    def publish(self, topic: str, packet: RuntimePacket) -> None:
        topic_text = self._validate_topic(topic)
        client = self._ensure_running_client()
        queue_key = self._build_key("queue", topic_text)
        encoded = self._codec.encode(packet)
        client.rpush(queue_key, encoded)

    def poll(self, topic: str, max_count: int = 1) -> tuple[RuntimePacket, ...]:
        topic_text = self._validate_topic(topic)
        normalized_max_count = self._validate_max_count(max_count)
        client = self._ensure_running_client()
        queue_key = self._build_key("queue", topic_text)

        raw_values: Any
        try:
            raw_values = client.lpop(queue_key, normalized_max_count)
        except TypeError:
            if normalized_max_count == 1:
                raw_values = client.lpop(queue_key)
            else:
                collected: list[Any] = []
                for _ in range(normalized_max_count):
                    item = client.lpop(queue_key)
                    if item is None:
                        break
                    collected.append(item)
                raw_values = collected

        normalized_values = self._normalize_lpop_result(raw_values)
        if not normalized_values:
            return ()

        packets: list[RuntimePacket] = []
        for item in normalized_values:
            packets.append(self._codec.decode(item))
        return tuple(packets)

    def set_value(self, key: str, value: str, *, expire_seconds: int | None = None) -> None:
        key_text = self._validate_non_empty_text("key", key)
        client = self._ensure_running_client()
        kv_key = self._build_key("kv", key_text)

        if expire_seconds is not None and expire_seconds <= 0:
            raise ValueError("expire_seconds must be > 0")

        payload = str(value)
        if expire_seconds is None:
            client.set(kv_key, payload)
        else:
            client.set(kv_key, payload, ex=expire_seconds)

    def get_value(self, key: str) -> str | None:
        key_text = self._validate_non_empty_text("key", key)
        client = self._ensure_running_client()
        kv_key = self._build_key("kv", key_text)
        raw_value = client.get(kv_key)
        if raw_value is None:
            return None
        return self._to_text(raw_value)

    def delete_value(self, key: str) -> int:
        key_text = self._validate_non_empty_text("key", key)
        client = self._ensure_running_client()
        kv_key = self._build_key("kv", key_text)
        return int(client.delete(kv_key) or 0)

    def append_stream(self, stream: str, packet: RuntimePacket) -> str:
        stream_text = self._validate_non_empty_text("stream", stream)
        client = self._ensure_running_client()
        stream_key = self._build_key("stream", stream_text)
        encoded_text = self._codec.encode(packet).decode("utf-8")
        message_id = client.xadd(stream_key, {"packet": encoded_text})
        return self._to_text(message_id)

    def create_consumer_group(
        self,
        stream: str,
        group: str,
        *,
        start_id: str = "0",
        mkstream: bool = True,
    ) -> None:
        stream_text = self._validate_non_empty_text("stream", stream)
        group_text = self._validate_non_empty_text("group", group)
        start_id_text = self._validate_non_empty_text("start_id", start_id)
        client = self._ensure_running_client()
        stream_key = self._build_key("stream", stream_text)

        try:
            client.xgroup_create(stream_key, group_text, start_id_text, mkstream=mkstream)
        except Exception as exc:
            if "BUSYGROUP" in str(exc).upper():
                return
            raise

    def read_group(
        self,
        stream: str,
        group: str,
        consumer: str,
        *,
        count: int = 1,
        block_ms: int | None = None,
    ) -> tuple[StreamMessage, ...]:
        stream_text = self._validate_non_empty_text("stream", stream)
        group_text = self._validate_non_empty_text("group", group)
        consumer_text = self._validate_non_empty_text("consumer", consumer)
        if count <= 0:
            raise ValueError("count must be > 0")
        if block_ms is not None and block_ms < 0:
            raise ValueError("block_ms must be >= 0")

        client = self._ensure_running_client()
        stream_key = self._build_key("stream", stream_text)
        response = client.xreadgroup(
            group_text,
            consumer_text,
            {stream_key: ">"},
            count=count,
            block=block_ms,
        )

        if not response:
            return ()

        messages: list[StreamMessage] = []
        for stream_item in response:
            if not isinstance(stream_item, (tuple, list)) or len(stream_item) < 2:
                continue

            stream_name = self._to_text(stream_item[0])
            entries = stream_item[1]
            if not isinstance(entries, (tuple, list)):
                continue

            for entry in entries:
                if not isinstance(entry, (tuple, list)) or len(entry) < 2:
                    continue

                message_id = self._to_text(entry[0])
                fields_raw = entry[1]
                if not isinstance(fields_raw, dict):
                    continue

                packet_raw = fields_raw.get("packet")
                if packet_raw is None:
                    packet_raw = fields_raw.get(b"packet")
                if packet_raw is None:
                    continue

                packet = self._codec.decode(packet_raw)
                messages.append(
                    StreamMessage(
                        stream=stream_name,
                        message_id=message_id,
                        packet=packet,
                    )
                )

        return tuple(messages)

    def ack_stream(self, stream: str, group: str, message_id: str) -> int:
        stream_text = self._validate_non_empty_text("stream", stream)
        group_text = self._validate_non_empty_text("group", group)
        message_id_text = self._validate_non_empty_text("message_id", message_id)
        client = self._ensure_running_client()
        stream_key = self._build_key("stream", stream_text)
        return int(client.xack(stream_key, group_text, message_id_text) or 0)

    def acquire_lock(self, name: str, owner: str, ttl_seconds: int) -> bool:
        name_text = self._validate_non_empty_text("name", name)
        owner_text = self._validate_non_empty_text("owner", owner)
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")

        client = self._ensure_running_client()
        lock_key = self._build_key("lock", name_text)
        result = client.set(lock_key, owner_text, nx=True, ex=ttl_seconds)
        return bool(result)

    def release_lock(self, name: str, owner: str) -> bool:
        name_text = self._validate_non_empty_text("name", name)
        owner_text = self._validate_non_empty_text("owner", owner)
        client = self._ensure_running_client()
        lock_key = self._build_key("lock", name_text)

        lua_script = (
            "if redis.call('GET', KEYS[1]) == ARGV[1] then "
            "return redis.call('DEL', KEYS[1]) "
            "else return 0 end"
        )
        result = client.eval(lua_script, 1, lock_key, owner_text)
        return int(result or 0) > 0

    def _build_key(self, category: str, name: str) -> str:
        category_text = self._validate_non_empty_text("category", category)
        name_text = self._validate_non_empty_text("name", name)
        return f"{self._config.key_prefix}:{category_text}:{name_text}"

    def _ensure_running_client(self) -> Any:
        if not self._running:
            raise RuntimeError("broker is not started")
        return self._ensure_client()

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client

        module_name = "redis" if self._config.backend == "redis" else "valkey"
        try:
            module = import_module(module_name)
        except ImportError as exc:
            if module_name == "redis":
                raise RuntimeError("redis client is not installed, please install package 'redis'") from exc
            raise RuntimeError("valkey client is not installed, please install package 'valkey'") from exc

        if self._config.url:
            client = module.from_url(
                self._config.url,
                db=self._config.db,
                username=self._config.username,
                password=self._config.password,
                socket_timeout=self._config.socket_timeout,
                decode_responses=self._config.decode_responses,
            )
        else:
            client = module.Redis(
                host=self._config.host,
                port=self._config.port,
                db=self._config.db,
                username=self._config.username,
                password=self._config.password,
                socket_timeout=self._config.socket_timeout,
                decode_responses=self._config.decode_responses,
            )

        self._client = client
        return client

    @staticmethod
    def _validate_non_empty_text(field_name: str, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError(f"{field_name} must be non-empty")
        return text

    @staticmethod
    def _to_text(value: object) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    @staticmethod
    def _normalize_lpop_result(value: Any) -> list[bytes | str]:
        if value is None:
            return []
        if isinstance(value, (bytes, str)):
            return [value]
        if isinstance(value, (tuple, list)):
            result: list[bytes | str] = []
            for item in value:
                if item is None:
                    continue
                if isinstance(item, (bytes, str)):
                    result.append(item)
                else:
                    result.append(str(item))
            return result
        return [str(value)]

