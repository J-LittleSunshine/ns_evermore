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

    try:
        node = NsRuntimeNode(
            config=config,
            host=str(args.host or "").strip() or None,
            port=int(args.port) if int(args.port or 0) > 0 else None,
            path=str(args.path or "").strip() or None,
        )
        print(f"runtime node started: role={config.node_role}, bind=ws://{node.host}:{node.port}{node.path}")
        node.run_forever()
        return 0
    except NsRuntimeError as exc:
        print(f"runtime node failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
