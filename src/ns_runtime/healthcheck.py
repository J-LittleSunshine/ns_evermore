# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_runtime.models import utc_now_iso

if TYPE_CHECKING:
    pass


def build_connection_hello_frame(*, token: str, component_type: str, requested_capabilities: list[str]) -> str:
    return json.dumps(
        {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": str(uuid.uuid4()),
                "type": "connection.hello",
                "category": "connection",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "token": token,
                    "component_type": component_type,
                    "requested_capabilities": requested_capabilities,
                },
            },
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def build_runtime_health_frame() -> str:
    return json.dumps(
        {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": str(uuid.uuid4()),
                "type": "runtime.control.health",
                "category": "control",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


async def run_healthcheck(*, uri: str, token: str, timeout_seconds: float) -> int:
    return await asyncio.wait_for(
        _run_healthcheck_once(
            uri=uri,
            token=token,
        ),
        timeout=timeout_seconds,
    )


async def _run_healthcheck_once(*, uri: str, token: str) -> int:
    try:
        from websockets.asyncio.client import connect
    except ImportError as exc:
        raise RuntimeError("Missing runtime WebSocket dependency. Install requirements-runtime.txt first.") from exc

    async with connect(uri) as websocket:
        await websocket.send(
            build_connection_hello_frame(
                token=token,
                component_type="management",
                requested_capabilities=["runtime.management"],
            )
        )
        accepted = _read_json(await websocket.recv())

        if accepted.get("message", {}).get("type") != "connection.accepted":
            print(json.dumps(accepted, ensure_ascii=False, indent=2))
            return 2

        await websocket.send(build_runtime_health_frame())
        health_result = _read_json(await websocket.recv())

        print(json.dumps(health_result, ensure_ascii=False, indent=2))

        if health_result.get("message", {}).get("type") != "runtime.control.health_result":
            return 3

        if health_result.get("payload", {}).get("inline", {}).get("status") != "ok":
            return 4

        return 0

def _read_json(frame: Any) -> dict[str, Any]:
    if not isinstance(frame, str):
        raise RuntimeError("Runtime healthcheck received a non-text WebSocket frame.")

    value = json.loads(frame)
    if not isinstance(value, dict):
        raise RuntimeError("Runtime healthcheck received a non-object JSON frame.")

    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ns_runtime.healthcheck")
    parser.add_argument("--uri", default=os.getenv("NS_RUNTIME_HEALTHCHECK_URI", "ws://127.0.0.1:8765"))
    parser.add_argument("--token", default=os.getenv("NS_RUNTIME_LOCAL_TOKEN", "local-dev-token"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("NS_RUNTIME_HEALTHCHECK_TIMEOUT_SECONDS", "5")))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    exit_code = asyncio.run(
        run_healthcheck(
            uri=args.uri,
            token=args.token,
            timeout_seconds=args.timeout,
        )
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
