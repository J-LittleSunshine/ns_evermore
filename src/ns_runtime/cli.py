# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Sequence

# Allow `python src/ns_runtime/cli.py ...` during local development without
# requiring package installation first.
_SRC_DIR = Path(__file__).resolve().parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
os.environ["PYTHONPATH"] = str(_SRC_DIR)

from ns_common.config import ns_config  # noqa: E402
from ns_common.runtime.constants import (  # noqa: E402
    RUNTIME_NODE_ROLE_MASTER,
    RUNTIME_NODE_ROLE_STANDALONE,
    RUNTIME_NODE_ROLE_SUB,
)
from ns_common.runtime.errors import NsRuntimeError  # noqa: E402
from ns_runtime.core import NsRuntimeNode  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Build standalone ns_runtime CLI parser."""
    parser = argparse.ArgumentParser(
        prog="ns-runtime-node",
        description="Run standalone NsEvermore runtime node.",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Force runtime enabled for this process.",
    )
    parser.add_argument(
        "--node-id",
        type=str,
        default="",
        help="Override runtime node id.",
    )
    parser.add_argument(
        "--node-role",
        type=str,
        default="",
        choices=[
            RUNTIME_NODE_ROLE_STANDALONE,
            RUNTIME_NODE_ROLE_MASTER,
            RUNTIME_NODE_ROLE_SUB,
        ],
        help="Override runtime node role: standalone, master, or sub.",
    )
    parser.add_argument(
        "--master-url",
        type=str,
        default="",
        help="Override runtime master WebSocket URL. Sub nodes connect to this URL; master/standalone nodes derive bind defaults from it.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="",
        help="Override runtime node bind host. Defaults to runtime.master_url host.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Override runtime node bind port. Defaults to runtime.master_url port.",
    )
    parser.add_argument(
        "--path",
        type=str,
        default="",
        help="Override runtime node WebSocket path. Defaults to runtime.master_url path.",
    )
    parser.add_argument(
        "--serve-inbound",
        action="store_true",
        help="For sub nodes, also start inbound WebSocket server for local frontend connections.",
    )
    parser.add_argument(
        "--auth-enabled",
        action="store_true",
        help="Force runtime service auth enabled for backend and sub-node register frames.",
    )
    parser.add_argument(
        "--service-token",
        type=str,
        default="",
        help="Runtime service bearer token for backend and sub-node connections.",
    )
    parser.add_argument(
        "--frontend-auth-enabled",
        action="store_true",
        help="Force runtime frontend bearer auth enabled.",
    )
    parser.add_argument(
        "--frontend-static-token",
        type=str,
        default="",
        help="Static frontend bearer token used when frontend auth is enabled.",
    )
    parser.add_argument(
        "--disallow-anonymous-frontend",
        action="store_true",
        help="Reject frontend.register without bearer token when frontend auth is enabled.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run standalone ns_runtime node CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    config = ns_config.runtime_config

    if args.enable:
        config = replace(config, enabled=True)

    node_id: str = str(args.node_id or "").strip()
    if node_id:
        config = replace(config, node_id=node_id)

    node_role: str = str(args.node_role or "").strip()
    if node_role:
        config = replace(config, node_role=node_role)  # type: ignore[arg-type]

    master_url: str = str(args.master_url or "").strip()
    if master_url:
        config = replace(config, master_url=master_url)

    if args.auth_enabled:
        config = replace(config, auth_enabled=True)

    service_token: str = str(args.service_token or "").strip()
    if service_token:
        config = replace(config, service_token=service_token)

    if args.frontend_auth_enabled:
        config = replace(config, frontend_auth_enabled=True)

    frontend_static_token: str = str(args.frontend_static_token or "").strip()
    if frontend_static_token:
        config = replace(config, frontend_static_token=frontend_static_token)

    if args.disallow_anonymous_frontend:
        config = replace(config, allow_anonymous_frontend=False)

    sub_serve_inbound = bool(args.serve_inbound)
    if config.node_role == RUNTIME_NODE_ROLE_SUB and int(args.port or 0) > 0:
        sub_serve_inbound = True

    serve_inbound = True
    if config.node_role == RUNTIME_NODE_ROLE_SUB:
        serve_inbound = sub_serve_inbound

    try:
        node = NsRuntimeNode(
            config=config,
            host=str(args.host or "").strip() or None,
            port=int(args.port) if int(args.port or 0) > 0 else None,
            path=str(args.path or "").strip() or None,
            serve_inbound=serve_inbound,
        )

        if config.node_role == RUNTIME_NODE_ROLE_SUB:
            if node.serve_inbound:
                print(f"runtime node started: role={config.node_role}, node_id={config.node_id}, master_url={config.master_url}, bind=ws://{node.host}:{node.port}{node.path}")
            else:
                print(f"runtime node started: role={config.node_role}, node_id={config.node_id}, master_url={config.master_url}")
        else:
            print(f"runtime node started: role={config.node_role}, node_id={config.node_id}, bind=ws://{node.host}:{node.port}{node.path}")

        node.run_forever()
        return 0
    except NsRuntimeError as exc:
        print(f"runtime node failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
