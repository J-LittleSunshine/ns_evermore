# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from _runtime_script_path import ensure_runtime_import_paths, resolve_repo_path

ensure_runtime_import_paths(__file__)

from runtime_broker_memory_smoke import run_smoke as run_memory_broker_smoke
from runtime_broker_redis_smoke import run_smoke as run_redis_broker_smoke
from runtime_config_consistency_smoke import run_smoke as run_config_consistency_smoke

class RuntimeSmokeError(RuntimeError):
    """Runtime smoke failed."""


def _print_result(_name: str, _passed: bool, _error: Exception | None = None) -> None:
    """Print one smoke result."""
    status = "PASS" if _passed else "FAIL"
    if _error is None:
        print(f"[{status}] {_name}")
        return

    print(f"[{status}] {_name}: {_error}")


def _run_sync_smoke(_name: str, _func: Callable[[], None]) -> None:
    """Run one sync smoke and print result."""
    try:
        _func()
    except Exception as exc:
        _print_result(_name, False, exc)
        raise RuntimeSmokeError(f"{_name} failed") from exc

    _print_result(_name, True)


async def _run_async_smoke(_name: str, _func: Callable[[], Any]) -> None:
    """Run one async smoke and print result."""
    try:
        await _func()
    except Exception as exc:
        _print_result(_name, False, exc)
        raise RuntimeSmokeError(f"{_name} failed") from exc

    _print_result(_name, True)


async def run_smoke(
        *,
        config_path: Path,
        memory_timeout_seconds: float,
        redis_enabled: bool,
        redis_url: str,
        redis_timeout_seconds: float,
) -> None:
    """Run runtime smoke index."""
    _run_sync_smoke(
        "runtime config consistency",
        lambda: run_config_consistency_smoke(config_path=config_path),
    )

    await _run_async_smoke(
        "runtime memory broker",
        lambda: run_memory_broker_smoke(timeout_seconds=memory_timeout_seconds),
    )

    if not redis_enabled:
        print("[SKIP] runtime redis broker: disabled")
        return

    await _run_async_smoke(
        "runtime redis broker",
        lambda: run_redis_broker_smoke(
            redis_url=redis_url,
            timeout_seconds=redis_timeout_seconds,
        ),
    )


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Run runtime manual smoke checks.")
    parser.add_argument(
        "--config",
        default="etc/ns_config.example.json",
        help="Path to ns_config example JSON.",
    )
    parser.add_argument(
        "--memory-timeout",
        type=float,
        default=float(os.getenv("NS_RUNTIME_MEMORY_SMOKE_TIMEOUT", "5")),
        help="Timeout seconds for memory broker smoke.",
    )
    parser.add_argument(
        "--with-redis",
        action="store_true",
        help="Run Redis/ValKey broker smoke. Disabled by default.",
    )
    parser.add_argument(
        "--redis-url",
        default=os.getenv("NS_RUNTIME_BROKER_REDIS_URL", "redis://127.0.0.1:6379/0"),
        help="Redis/ValKey URL for optional Redis broker smoke.",
    )
    parser.add_argument(
        "--redis-timeout",
        type=float,
        default=float(os.getenv("NS_RUNTIME_BROKER_SMOKE_TIMEOUT", "5")),
        help="Timeout seconds for optional Redis broker smoke.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            run_smoke(
                config_path=resolve_repo_path(__file__, str(args.config)).resolve(),
                memory_timeout_seconds=float(args.memory_timeout),
                redis_enabled=bool(args.with_redis),
                redis_url=str(args.redis_url),
                redis_timeout_seconds=float(args.redis_timeout),
            )
        )
    except RuntimeSmokeError as exc:
        raise SystemExit(f"runtime smoke failed: {exc}") from exc

    print("runtime smoke ok")


if __name__ == "__main__":
    main()
