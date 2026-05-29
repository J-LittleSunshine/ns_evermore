# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from importlib import import_module
from multiprocessing.queues import Queue as MpQueue
from queue import Empty
from typing import Any

from ns_common.protocol import RuntimePacket, RuntimePacketCodec, RuntimePacketType
from ns_executor.config import ExecutorClientConfig
from ns_executor.ipc import ExecutorIpcMessage, ExecutorIpcMessageType


class ExecutorIoProcessRunner:
    def __init__(
        self,
        config: ExecutorClientConfig,
        inbound_queue: MpQueue,
        outbound_queue: MpQueue,
    ) -> None:
        self._config = config
        self._inbound_queue = inbound_queue
        self._outbound_queue = outbound_queue
        self._stopped = False

    def run(self) -> None:
        asyncio.run(self._run_async())

    async def _run_async(self) -> None:
        while not self._stopped:
            try:
                await self._connect_once()
            except RuntimeError:
                raise
            except Exception as exc:
                print(f"[executor io] connection error: {exc}")

            if self._stopped:
                break

            await asyncio.sleep(self._config.reconnect_interval_seconds)

    async def _connect_once(self) -> None:
        try:
            client_module = import_module("websockets.asyncio.client")
            connect = getattr(client_module, "connect")
        except (ImportError, AttributeError) as exc:
            raise RuntimeError("websockets is not installed, please install package 'websockets'") from exc

        codec = RuntimePacketCodec()
        async with connect(self._config.gateway_url) as websocket:
            await self._send_register(websocket, codec)

            stop_event = asyncio.Event()
            tasks = [
                asyncio.create_task(self._send_heartbeat_loop(websocket, codec, stop_event)),
                asyncio.create_task(self._receive_loop(websocket, codec, stop_event)),
                asyncio.create_task(self._outbound_loop(websocket, codec, stop_event)),
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            stop_event.set()

            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

            for task in done:
                exc = task.exception()
                if exc is not None:
                    raise exc

    async def _send_register(self, websocket: Any, codec: RuntimePacketCodec) -> None:
        register_packet = RuntimePacket.create(
            packet_type=RuntimePacketType.REGISTER,
            source_endpoint_id=self._config.endpoint_id,
            payload={
                "endpoint_id": self._config.endpoint_id,
                "endpoint_type": self._config.endpoint_type.value,
                "capabilities": list(self._config.capabilities),
                "metadata": dict(self._config.metadata),
            },
        )
        await websocket.send(codec.encode(register_packet))

    async def _send_heartbeat_loop(self, websocket: Any, codec: RuntimePacketCodec, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            heartbeat_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.HEARTBEAT,
                source_endpoint_id=self._config.endpoint_id,
                payload={"tick": 1},
            )
            await websocket.send(codec.encode(heartbeat_packet))
            await asyncio.sleep(self._config.heartbeat_interval_seconds)

    async def _receive_loop(self, websocket: Any, codec: RuntimePacketCodec, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            raw_message = await websocket.recv()
            try:
                packet = codec.decode(raw_message)
            except ValueError as exc:
                print(f"[executor io] decode error: {exc}")
                continue

            if packet.packet_type == RuntimePacketType.TASK:
                # IPC 层传 dict，不直接跨进程传 RuntimePacket，降低对象耦合。
                self._inbound_queue.put(ExecutorIpcMessage.from_packet(packet).to_dict())
            else:
                print(f"[executor io] ignore packet type: {packet.packet_type.value}")

    async def _outbound_loop(self, websocket: Any, codec: RuntimePacketCodec, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            try:
                raw_message = await asyncio.to_thread(
                    self._outbound_queue.get,
                    True,
                    self._config.outbound_poll_interval_seconds,
                )
            except Empty:
                continue

            try:
                message = ExecutorIpcMessage.from_dict(raw_message)
            except Exception as exc:
                print(f"[executor io] invalid outbound ipc message: {exc}")
                continue

            if message.message_type == ExecutorIpcMessageType.STOP:
                self._stopped = True
                stop_event.set()
                break

            if message.message_type != ExecutorIpcMessageType.PACKET or message.packet is None:
                continue

            try:
                packet = RuntimePacket.from_dict(message.packet)
            except Exception as exc:
                print(f"[executor io] invalid outbound packet: {exc}")
                continue

            await websocket.send(codec.encode(packet))

