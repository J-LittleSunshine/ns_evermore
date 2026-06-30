# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Sequence,
)

from websockets.asyncio.client import connect


def _ensure_src_on_sys_path() -> None:
    src_dir = Path(__file__).resolve().parent.parent
    src_text = str(src_dir)

    if src_text not in sys.path:
        sys.path.insert(0, src_text)


_ensure_src_on_sys_path()

from ns_runtime.protocol import (  # noqa: E402
    NsRuntimeClientType,
    NsRuntimeEnvelope,
    NsRuntimeJsonCodec,
    NsRuntimeMessageType,
    NsRuntimePeer,
    current_epoch_ms,
    new_runtime_message_id,
)


@dataclass(slots=True, kw_only=True)
class NsRuntimeSmokeClientOptions:
    url: str
    access_token: str
    token_type: str
    client_type: str
    client_id: str
    session_id: str | None
    node_id: str | None
    node_group: str | None
    processor: str
    text: str
    timeout_seconds: float
    max_message_size_bytes: int
    outbound_requires_ack: bool
    response_requires_ack: bool
    skip_ping: bool
    skip_processor: bool
    burst_count: int
    expect_backpressure: bool
    dump_envelopes: bool


@dataclass(slots=True, kw_only=True)
class NsRuntimeSmokeClientStats:
    inbound_count: int = 0
    outbound_count: int = 0
    inbound_ack_count: int = 0
    outbound_ack_count: int = 0
    processor_response_count: int = 0
    processor_error_count: int = 0
    backpressure_error_count: int = 0


class NsRuntimeSmokeClient:
    def __init__(self, options: NsRuntimeSmokeClientOptions) -> None:
        self.options = options
        self.stats = NsRuntimeSmokeClientStats()
        self.peer = NsRuntimePeer(
            client_type=options.client_type,
            client_id=options.client_id,
            node_id=options.node_id,
            node_group=options.node_group,
        )
        self.peer.validate("smoke_client.peer")
        self._websocket: Any | None = None

    async def run(self) -> int:
        print(f"[smoke] connecting: {self.options.url}")

        async with connect(
                self.options.url,
                max_size=self.options.max_message_size_bytes,
        ) as websocket:
            self._websocket = websocket

            await self._handshake()

            if not self.options.skip_ping:
                await self._ping()

            if not self.options.skip_processor:
                await self._processor_echo()

            if self.options.burst_count > 0:
                await self._burst_processor_requests()

        self._print_stats()
        return 0

    async def _handshake(self) -> None:
        payload: dict[str, Any] = {
            "access_token": self.options.access_token,
            "token_type": self.options.token_type,
            "client_type": self.options.client_type,
            "client_id": self.options.client_id,
        }

        if self.options.session_id:
            payload["session_id"] = self.options.session_id

        if self.options.node_id:
            payload["node_id"] = self.options.node_id

        if self.options.node_group:
            payload["node_group"] = self.options.node_group

        hello = NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.CONNECTION_HELLO,
            source=self.peer,
            trace_id=new_runtime_message_id(),
            payload=payload,
        )

        await self._send(hello)

        response = await self._recv_until(
            lambda item: item.message_type in {
                NsRuntimeMessageType.CONNECTION_ACCEPTED,
                NsRuntimeMessageType.CONNECTION_REJECTED,
            },
            description="connection accepted/rejected",
        )

        if response.message_type == NsRuntimeMessageType.CONNECTION_REJECTED:
            raise RuntimeError(
                "Runtime connection rejected: "
                + json.dumps(response.payload, ensure_ascii=False)
            )

        print("[smoke] connection accepted")

    async def _ping(self) -> None:
        ping = NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.HEARTBEAT_PING,
            source=self.peer,
            trace_id=new_runtime_message_id(),
            payload={
                "client_time_epoch_ms": current_epoch_ms(),
                "label": "runtime.smoke.ping",
            },
            requires_ack=self.options.outbound_requires_ack,
        )

        await self._send(ping)

        pong = await self._recv_until(
            lambda item: item.message_type == NsRuntimeMessageType.HEARTBEAT_PONG,
            description="heartbeat.pong",
        )

        print(
            "[smoke] heartbeat pong received: "
            f"connection_id={pong.payload.get('connection_id')}, "
            f"inflight={pong.payload.get('inflight_count')}, "
            f"pending_ack={pong.payload.get('pending_ack_count')}"
        )

    async def _processor_echo(self) -> None:
        payload: dict[str, Any] = {
            "processor": self.options.processor,
            "text": self.options.text,
            "client_time_epoch_ms": current_epoch_ms(),
        }

        if self.options.response_requires_ack:
            payload["response_requires_ack"] = True

        request = NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.PROCESSOR_REQUEST,
            source=self.peer,
            trace_id=new_runtime_message_id(),
            payload=payload,
            requires_ack=self.options.outbound_requires_ack,
        )

        await self._send(request)

        response = await self._recv_until(
            lambda item: item.message_type in {
                NsRuntimeMessageType.PROCESSOR_RESPONSE,
                NsRuntimeMessageType.PROCESSOR_ERROR,
            },
            description="processor.response/error",
        )

        if response.message_type == NsRuntimeMessageType.PROCESSOR_ERROR:
            self.stats.processor_error_count += 1
            raise RuntimeError(
                "Runtime processor returned error: "
                + json.dumps(response.payload, ensure_ascii=False)
            )

        self.stats.processor_response_count += 1
        print(
            "[smoke] processor response received: "
            + json.dumps(response.payload, ensure_ascii=False)
        )

    async def _burst_processor_requests(self) -> None:
        print(f"[smoke] sending burst processor requests: count={self.options.burst_count}")

        for index in range(self.options.burst_count):
            payload: dict[str, Any] = {
                "processor": self.options.processor,
                "burst_index": index,
                "text": self.options.text,
                "client_time_epoch_ms": current_epoch_ms(),
            }

            if self.options.response_requires_ack:
                payload["response_requires_ack"] = True

            request = NsRuntimeEnvelope.new(
                message_type=NsRuntimeMessageType.PROCESSOR_REQUEST,
                source=self.peer,
                trace_id=new_runtime_message_id(),
                payload=payload,
                requires_ack=self.options.outbound_requires_ack,
            )
            await self._send(request)

        completed = 0
        deadline = time.monotonic() + self.options.timeout_seconds

        while completed < self.options.burst_count:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break

            envelope = await self._recv(timeout_seconds=remaining)

            if envelope.message_type == NsRuntimeMessageType.PROCESSOR_RESPONSE:
                self.stats.processor_response_count += 1
                completed += 1
                continue

            if envelope.message_type == NsRuntimeMessageType.PROCESSOR_ERROR:
                self.stats.processor_error_count += 1
                completed += 1

                code = envelope.payload.get("code")
                if code == "RUNTIME_BACKPRESSURE_REJECTED":
                    self.stats.backpressure_error_count += 1

                continue

        print(
            "[smoke] burst completed: "
            f"completed={completed}, "
            f"processor_response={self.stats.processor_response_count}, "
            f"processor_error={self.stats.processor_error_count}, "
            f"backpressure_error={self.stats.backpressure_error_count}"
        )

        if self.options.expect_backpressure and self.stats.backpressure_error_count <= 0:
            raise RuntimeError(
                "Expected backpressure error, but no RUNTIME_BACKPRESSURE_REJECTED was received."
            )

    async def _send(self, envelope: NsRuntimeEnvelope) -> None:
        if self._websocket is None:
            raise RuntimeError("WebSocket is not connected.")

        await self._websocket.send(NsRuntimeJsonCodec.encode(envelope))
        self.stats.outbound_count += 1
        self._print_envelope("OUT", envelope)

    async def _recv_until(
            self,
            predicate: Callable[[NsRuntimeEnvelope], bool],
            *,
            description: str,
    ) -> NsRuntimeEnvelope:
        deadline = time.monotonic() + self.options.timeout_seconds

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for {description}.")

            envelope = await self._recv(timeout_seconds=remaining)

            if predicate(envelope):
                return envelope

    async def _recv(self, *, timeout_seconds: float) -> NsRuntimeEnvelope:
        if self._websocket is None:
            raise RuntimeError("WebSocket is not connected.")

        raw_message = await asyncio.wait_for(
            self._websocket.recv(),
            timeout=timeout_seconds,
        )
        envelope = NsRuntimeJsonCodec.decode(raw_message)

        self.stats.inbound_count += 1
        self._print_envelope("IN", envelope)

        if envelope.message_type == NsRuntimeMessageType.ACK:
            self.stats.inbound_ack_count += 1
            return envelope

        if envelope.requires_ack:
            await self._ack_inbound(envelope)

        return envelope

    async def _ack_inbound(self, envelope: NsRuntimeEnvelope) -> None:
        ack = envelope.build_ack(
            source=self.peer,
            metadata={
                "client_id": self.options.client_id,
                "acknowledged_at_epoch_ms": current_epoch_ms(),
            },
        )
        await self._send(ack)
        self.stats.outbound_ack_count += 1

    def _print_envelope(self, direction: str, envelope: NsRuntimeEnvelope) -> None:
        print(
            f"[{direction}] "
            f"type={envelope.message_type} "
            f"id={envelope.message_id} "
            f"reply_to={envelope.reply_to_message_id or '-'} "
            f"requires_ack={envelope.requires_ack}"
        )

        if self.options.dump_envelopes:
            print(json.dumps(envelope.to_mapping(), ensure_ascii=False, indent=2))

    def _print_stats(self) -> None:
        print(
            "[smoke] stats: "
            f"inbound={self.stats.inbound_count}, "
            f"outbound={self.stats.outbound_count}, "
            f"inbound_ack={self.stats.inbound_ack_count}, "
            f"outbound_ack={self.stats.outbound_ack_count}, "
            f"processor_response={self.stats.processor_response_count}, "
            f"processor_error={self.stats.processor_error_count}, "
            f"backpressure_error={self.stats.backpressure_error_count}"
        )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ns_runtime_smoke_client",
        description="NsEvermore runtime WebSocket smoke client.",
    )
    parser.add_argument(
        "--url",
        default=os.getenv("NS_RUNTIME_SMOKE_URL", "ws://127.0.0.1:8765/runtime/ws"),
        help="Runtime WebSocket URL.",
    )
    parser.add_argument(
        "--access-token",
        default=os.getenv("NS_RUNTIME_SMOKE_ACCESS_TOKEN", ""),
        help="Frontend access token used by connection.hello. Can also be set by NS_RUNTIME_SMOKE_ACCESS_TOKEN.",
    )
    parser.add_argument(
        "--token-type",
        default="access",
        help="Token type for connection.hello.",
    )
    parser.add_argument(
        "--client-type",
        default=NsRuntimeClientType.NS_CLIENT,
        help="Runtime client type.",
    )
    parser.add_argument(
        "--client-id",
        default="runtime-smoke-client-01",
        help="Runtime client id.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Optional session id.",
    )
    parser.add_argument(
        "--node-id",
        default=None,
        help="Optional node id.",
    )
    parser.add_argument(
        "--node-group",
        default=None,
        help="Optional node group.",
    )
    parser.add_argument(
        "--processor",
        default="runtime.echo",
        help="Processor name for processor.request.",
    )
    parser.add_argument(
        "--text",
        default="hello-runtime",
        help="Text payload for runtime.echo.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="Receive timeout seconds.",
    )
    parser.add_argument(
        "--max-message-size-bytes",
        type=int,
        default=1_048_576,
        help="Max WebSocket message size.",
    )
    parser.add_argument(
        "--requires-ack",
        action="store_true",
        help="Set requires_ack=true on outbound ping and processor.request.",
    )
    parser.add_argument(
        "--response-requires-ack",
        action="store_true",
        help="Ask runtime.echo processor.response to require ACK.",
    )
    parser.add_argument(
        "--skip-ping",
        action="store_true",
        help="Skip heartbeat.ping smoke check.",
    )
    parser.add_argument(
        "--skip-processor",
        action="store_true",
        help="Skip processor.request smoke check.",
    )
    parser.add_argument(
        "--burst-count",
        type=int,
        default=0,
        help="Send N processor.request messages without waiting between sends.",
    )
    parser.add_argument(
        "--expect-backpressure",
        action="store_true",
        help="Fail if burst run does not receive RUNTIME_BACKPRESSURE_REJECTED.",
    )
    parser.add_argument(
        "--dump-envelopes",
        action="store_true",
        help="Print full JSON envelopes.",
    )
    return parser.parse_args(argv)


def _build_options(args: argparse.Namespace) -> NsRuntimeSmokeClientOptions:
    access_token = str(args.access_token or "").strip()

    if not access_token:
        raise SystemExit(
            "Missing access token. Pass --access-token or set NS_RUNTIME_SMOKE_ACCESS_TOKEN."
        )

    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be positive.")

    if args.max_message_size_bytes <= 0:
        raise SystemExit("--max-message-size-bytes must be positive.")

    if args.burst_count < 0:
        raise SystemExit("--burst-count must be greater than or equal to 0.")

    return NsRuntimeSmokeClientOptions(
        url=str(args.url).strip(),
        access_token=access_token,
        token_type=str(args.token_type).strip(),
        client_type=str(args.client_type).strip(),
        client_id=str(args.client_id).strip(),
        session_id=_normalize_optional_text(args.session_id),
        node_id=_normalize_optional_text(args.node_id),
        node_group=_normalize_optional_text(args.node_group),
        processor=str(args.processor).strip(),
        text=str(args.text),
        timeout_seconds=float(args.timeout_seconds),
        max_message_size_bytes=int(args.max_message_size_bytes),
        outbound_requires_ack=bool(args.requires_ack),
        response_requires_ack=bool(args.response_requires_ack),
        skip_ping=bool(args.skip_ping),
        skip_processor=bool(args.skip_processor),
        burst_count=int(args.burst_count),
        expect_backpressure=bool(args.expect_backpressure),
        dump_envelopes=bool(args.dump_envelopes),
    )


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


async def run(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    options = _build_options(args)
    client = NsRuntimeSmokeClient(options)
    return await client.run()


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return asyncio.run(run(argv))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # noqa
        print(
            "[smoke] failed: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
