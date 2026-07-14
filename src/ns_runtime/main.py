# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import os
from typing import (
    TYPE_CHECKING,
    cast
)

from ns_runtime.auth import LocalTokenRuntimeAuthenticator
from ns_runtime.models import RuntimeRole
from ns_runtime.service import RuntimeService
from ns_runtime.transport import RuntimeWebSocketTransportConfig

if TYPE_CHECKING:
    pass


def _read_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    return int(raw_value)


def _read_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    return float(raw_value)


def _read_runtime_role_env() -> RuntimeRole:
    raw_value = os.getenv(
        "NS_RUNTIME_ROLE",
        "singleton",
    ).strip() or "singleton"

    allowed_roles = {
        "singleton",
        "sub_node",
        "standby_master",
    }

    if raw_value not in allowed_roles:
        raise ValueError(
            "NS_RUNTIME_ROLE must be one of: "
            "singleton, sub_node, standby_master."
        )

    return cast(
        RuntimeRole,
        raw_value,
    )

async def run_service() -> None:
    runtime_id = os.getenv("NS_RUNTIME_ID", "runtime-local-1").strip() or "runtime-local-1"
    host = os.getenv("NS_RUNTIME_HOST", "0.0.0.0").strip() or "0.0.0.0"
    port = _read_int_env("NS_RUNTIME_PORT", 8765)
    local_token = os.getenv("NS_RUNTIME_LOCAL_TOKEN", "local-dev-token").strip() or "local-dev-token"

    authenticator = LocalTokenRuntimeAuthenticator(expected_token=local_token)
    service = RuntimeService.build_default(
        runtime_id=runtime_id,
        authenticator=authenticator,
        runtime_role=_read_runtime_role_env(),
    )
    transport_config = RuntimeWebSocketTransportConfig(
        host=host,
        port=port,
        handshake_timeout_seconds=_read_float_env("NS_RUNTIME_HANDSHAKE_TIMEOUT_SECONDS", 10.0),
        max_frame_bytes=_read_int_env("NS_RUNTIME_MAX_FRAME_BYTES", 1024 * 1024),
        read_queue_high_water=_read_int_env("NS_RUNTIME_READ_QUEUE_HIGH_WATER", 16),
        write_limit_bytes=_read_int_env("NS_RUNTIME_WRITE_LIMIT_BYTES", 32768),
        ping_interval_seconds=_read_float_env("NS_RUNTIME_PING_INTERVAL_SECONDS", 20.0),
        ping_timeout_seconds=_read_float_env("NS_RUNTIME_PING_TIMEOUT_SECONDS", 20.0),
        close_timeout_seconds=_read_float_env("NS_RUNTIME_CLOSE_TIMEOUT_SECONDS", 10.0),
    )

    await service.serve_forever(transport_config)


def main() -> None:
    asyncio.run(run_service())


if __name__ == "__main__":
    main()
