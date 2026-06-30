# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Sequence

from ns_common.config import NsConfig
from ns_common.exceptions import NsEvermoreError
from ns_common.runtime_config import (
    RuntimeMode,
    validate_runtime_config,
)
from ns_runtime.app import RuntimeApplication


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ns_runtime",
        description="NsEvermore runtime process.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser(
        "start",
        help="Start ns_runtime. Phase 1.2 only performs bootstrap validation.",
    )
    start_parser.add_argument(
        "--mode",
        choices=[
            "master",
            "sub_node",
            "singleton",
        ],
        default=None,
        help="Override runtime.mode for this process.",
    )
    start_parser.add_argument(
        "--config",
        default=None,
        help="Path to ns_config JSON file.",
    )

    check_parser = subparsers.add_parser(
        "config-check",
        help="Validate ns_runtime configuration.",
    )
    check_parser.add_argument(
        "--config",
        default=None,
        help="Path to ns_config JSON file.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "start":
            return asyncio.run(_run_start(args))

        if args.command == "config-check":
            return _run_config_check(args)

        parser.print_help()
        return 1

    except NsEvermoreError as error:
        _print_error(error)
        return 2

    except KeyboardInterrupt:
        return 130


async def _run_start(args: argparse.Namespace) -> int:
    config = _load_config(args.config)

    if args.mode:
        config.runtime.mode = _parse_mode(args.mode)

    validate_runtime_config(config.runtime)

    app = RuntimeApplication(
        config=config,
        mode=config.runtime.mode,
    )
    await app.run_once_for_bootstrap_check()

    print(
        json.dumps(
            {
                "success": True,
                "message": "ns_runtime bootstrap check completed.",
                "runtime_id": config.runtime.runtime_id,
                "cluster_id": config.runtime.cluster_id,
                "mode": config.runtime.mode,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _run_config_check(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    validate_runtime_config(config.runtime)

    print(
        json.dumps(
            {
                "success": True,
                "message": "ns_runtime config is valid.",
                "runtime_id": config.runtime.runtime_id,
                "cluster_id": config.runtime.cluster_id,
                "mode": config.runtime.mode,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _load_config(config_path: str | None) -> NsConfig:
    if not config_path:
        return NsConfig.load()

    return NsConfig.load(Path(config_path))


def _parse_mode(value: str) -> RuntimeMode:
    if value not in {
        "master",
        "sub_node",
        "singleton",
    }:
        raise ValueError(f"Invalid runtime mode: {value}")

    return value  # type: ignore[return-value]


def _print_error(error: NsEvermoreError) -> None:
    print(
        json.dumps(
            {
                "success": False,
                "error": error.to_dict(),
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
