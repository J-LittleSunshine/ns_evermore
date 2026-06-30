# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from pathlib import Path
from typing import Sequence


def _ensure_src_on_sys_path() -> None:
    src_dir = Path(__file__).resolve().parent.parent
    src_text = str(src_dir)

    if src_text not in sys.path:
        sys.path.insert(0, src_text)


_ensure_src_on_sys_path()

from ns_common.config import (  # noqa: E402
    NsConfig,
    ns_config,
)
from ns_common.exceptions import NsEvermoreError  # noqa: E402
from ns_common.http_client import aclose_http_clients  # noqa: E402
from ns_common.logger import get_ns_logger  # noqa: E402
from ns_runtime.ws_server import NsRuntimeWebSocketServer  # noqa: E402


class NsRuntimeMainProcessor:
    def __init__(self, config: NsConfig) -> None:
        self.config: NsConfig = config
        self.runtime = config.runtime
        self.logger = get_ns_logger("ns_runtime")
        self._stop_event: asyncio.Event | None = None
        self._started: bool = False
        self._ws_server: NsRuntimeWebSocketServer | None = None

    async def start(self) -> None:
        if self._started:
            return

        self.runtime.validate()
        self._stop_event = asyncio.Event()

        self._ws_server = NsRuntimeWebSocketServer(
            runtime_config=self.runtime,
        )
        await self._ws_server.start()

        self.logger.info(
            "Runtime main processor started.",
            extra={
                "runtime_id": self.runtime.runtime_id,
                "cluster_id": self.runtime.cluster_id,
                "mode": self.runtime.mode,
                "enabled": self.runtime.enabled,
                "websocket_host": self.runtime.server.websocket.host,
                "websocket_port": self.runtime.server.websocket.port,
                "websocket_path": self.runtime.server.websocket.path,
                "admin_host": self.runtime.server.admin_http.host,
                "admin_port": self.runtime.server.admin_http.port,
                "admin_path": self.runtime.server.admin_http.path,
                "global_max_concurrency": self.runtime.global_max_concurrency,
                "default_processor_max_concurrency": self.runtime.default_processor_max_concurrency,
                "default_connection_max_inflight": self.runtime.default_connection_max_inflight,
                "default_backpressure_policy": self.runtime.default_backpressure_policy,
            },
        )

        self._started = True

    async def wait(self) -> None:
        if self._stop_event is None:
            raise RuntimeError("Runtime main processor has not been started.")

        await self._stop_event.wait()

    async def stop(self, reason: str = "normal") -> None:
        if not self._started:
            return

        ws_server = self._ws_server
        self._ws_server = None

        if ws_server is not None:
            await ws_server.stop(reason=reason)

        await aclose_http_clients()

        self.logger.info(
            "Runtime main processor stopped.",
            extra={
                "runtime_id": self.runtime.runtime_id,
                "cluster_id": self.runtime.cluster_id,
                "mode": self.runtime.mode,
                "reason": reason,
            },
        )

        self._started = False

    def request_stop(self, reason: str = "signal") -> None:
        if self._stop_event is None:
            return

        self.logger.info(
            "Runtime stop requested.",
            extra={
                "runtime_id": self.runtime.runtime_id,
                "reason": reason,
            },
        )
        self._stop_event.set()


def _parse_startup_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ns_runtime",
        description="NsEvermore runtime component entry.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate runtime config and exit without starting the runtime process.",
    )
    return parser.parse_args(argv)


def _register_stop_signals(processor: NsRuntimeMainProcessor) -> None:
    loop = asyncio.get_running_loop()

    for item in (
            signal.SIGINT,
            signal.SIGTERM,
    ):
        try:
            loop.add_signal_handler(item, processor.request_stop, item.name)
        except (NotImplementedError, RuntimeError, ValueError):
            continue


async def run(*, check_config: bool = False) -> int:
    logger = get_ns_logger("ns_runtime")
    config = ns_config
    config.validate()
    config.runtime.validate()

    if check_config:
        logger.info(
            "Runtime config check passed.",
            extra={
                "runtime_id": config.runtime.runtime_id,
                "cluster_id": config.runtime.cluster_id,
                "mode": config.runtime.mode,
                "enabled": config.runtime.enabled,
            },
        )
        return 0

    if not config.runtime.enabled:
        logger.warning(
            "Runtime is disabled by config. Process exits without starting runtime loop.",
            extra={
                "runtime_id": config.runtime.runtime_id,
                "cluster_id": config.runtime.cluster_id,
                "mode": config.runtime.mode,
                "enabled": config.runtime.enabled,
            },
        )
        return 0

    processor = NsRuntimeMainProcessor(config)
    _register_stop_signals(processor)

    stop_reason = "normal"

    try:
        await processor.start()
        await processor.wait()
    except asyncio.CancelledError:
        stop_reason = "cancelled"
        raise
    except KeyboardInterrupt:
        stop_reason = "keyboard_interrupt"
    finally:
        await processor.stop(reason=stop_reason)

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_startup_args(argv)
    logger = get_ns_logger("ns_runtime")

    try:
        return asyncio.run(run(check_config=bool(args.check_config)))
    except KeyboardInterrupt:
        return 130
    except NsEvermoreError as exc:
        logger.error(
            "Runtime process failed with NsEvermore error.",
            extra={
                "code": exc.code,
                "numeric_code": exc.numeric_code,
                "message": exc.message,
                "details": exc.details,
            },
        )
        return 1
    except Exception as exc:  # noqa
        logger.exception(
            "Runtime process failed with unexpected error.",
            extra={
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
