# -*- coding: utf-8 -*-
"""The sole process entry point for the standalone ns_runtime component."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ns_runtime.service import RuntimeService


async def _run_service_once(service: RuntimeService) -> None:
    """Run the current no-listener service through one clean lifecycle."""

    await service.start()
    await service.stop()


def main() -> int:
    """Validate startup, run the no-listener service, and return its status.

    Imports stay local so importing :mod:`ns_runtime` or this entry module does
    not load configuration, install an event-loop policy, or create resources.
    Signal-driven lifetime and resource shutdown orchestration are added by the
    remaining P02 work packages.
    """

    import asyncio
    import logging

    from ns_common.async_runtime import TaskSupervisor
    from ns_common.config import NsConfig
    from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
    from ns_common.time import SystemClock
    from ns_runtime.context import RuntimeContext
    from ns_runtime.service import RuntimeService
    from ns_runtime.startup import RuntimeStartupPreflight

    preflight = RuntimeStartupPreflight()
    environment = preflight.resolve_environment()
    config = NsConfig.load(environment=environment)
    logger = logging.Logger("ns_runtime")
    logger.setLevel(config.runtime.logging.level.strip().upper())
    context = RuntimeContext(
        config=config,
        clock=SystemClock(),
        logger=logger,
        metrics=InMemoryMetricsSink(),
        traces=InMemoryTraceSink(),
        task_supervisor=TaskSupervisor(
            shutdown_timeout_seconds=(
                config.runtime.worker.shutdown_timeout_seconds
            ),
        ),
    )

    preflight.prepare(context, environment=environment)
    service = RuntimeService(context=context)
    asyncio.run(_run_service_once(service))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
