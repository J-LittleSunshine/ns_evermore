# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Sequence

# Allow `python src/ns_backend/backend/runtime/connector_cli.py ...`
# during local development without requiring package installation first.
_SRC_DIR = Path(__file__).resolve().parents[3]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
os.environ["PYTHONPATH"] = str(_SRC_DIR)

from ns_backend.backend.runtime.connector import NsBackendRuntimeConnector, NsBackendRuntimeStubSender  # noqa: E402
from ns_backend.backend.runtime.sender import NsBackendRuntimeWebSocketSender  # noqa: E402
from ns_common.config import ns_config  # noqa: E402
from ns_common.runtime.constants import (  # noqa: E402
    RUNTIME_CONNECTOR_IPC_MEMORY,
    RUNTIME_CONNECTOR_IPC_TCP,
    RUNTIME_CONNECTOR_IPC_UNIX_SOCKET,
)
from ns_common.runtime.errors import NsRuntimeError  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Build standalone backend runtime connector CLI parser."""
    parser = argparse.ArgumentParser(
        prog="ns-backend-runtime-connector",
        description="Run NsEvermore backend runtime connector.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Drain one outbox batch and exit.",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Force runtime enabled for this process.",
    )
    parser.add_argument(
        "--ipc-mode",
        type=str,
        default="",
        choices=[
            "",
            RUNTIME_CONNECTOR_IPC_MEMORY,
            RUNTIME_CONNECTOR_IPC_UNIX_SOCKET,
            RUNTIME_CONNECTOR_IPC_TCP,
        ],
        help="Override runtime IPC mode: memory, unix_socket, or tcp.",
    )
    parser.add_argument(
        "--node-id",
        type=str,
        default="",
        help="Override backend runtime connector node id.",
    )
    parser.add_argument(
        "--auth-enabled",
        action="store_true",
        help="Force runtime service auth enabled for this connector process.",
    )
    parser.add_argument(
        "--service-token",
        type=str,
        default="",
        help="Runtime service bearer token used by backend.register.",
    )
    parser.add_argument(
        "--sender",
        type=str,
        default="stub",
        choices=[
            "stub",
            "websocket",
        ],
        help="Runtime sender type: stub or websocket.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run backend runtime connector CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    config = ns_config.runtime_config

    if args.enable:
        config = replace(config, enabled=True)

    ipc_mode: str = str(args.ipc_mode or "").strip()
    if ipc_mode:
        config = replace(config, ipc_mode=ipc_mode)  # type: ignore[arg-type]

    node_id: str = str(args.node_id or "").strip()
    if node_id:
        config = replace(config, node_id=node_id)

    if args.auth_enabled:
        config = replace(config, auth_enabled=True)

    service_token: str = str(args.service_token or "").strip()
    if service_token:
        config = replace(config, service_token=service_token)

    sender_type: str = str(args.sender or "stub").strip().lower()

    try:
        if sender_type == "stub":
            sender = NsBackendRuntimeStubSender()
        elif sender_type == "websocket":
            sender = NsBackendRuntimeWebSocketSender(config)
        else:
            # argparse choices should prevent this branch. Keep it as a defensive guard.
            print(f"unsupported runtime sender type: {sender_type}", file=sys.stderr)
            return 2

        connector = NsBackendRuntimeConnector(config=config, sender=sender)

        if bool(args.once):
            connector.start()
            try:
                drained: int = connector.drain_once()
            finally:
                connector.stop()

            print(f"runtime connector drained one batch: {drained}")
            return 0

        print("runtime connector started.")
        connector.run_forever()
        return 0
    except NsRuntimeError as exc:
        print(f"runtime connector failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
