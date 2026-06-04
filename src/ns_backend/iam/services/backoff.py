# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import random
from typing import Awaitable, Callable, TypeVar

from ns_backend.backend.common.logger import iam_logger

T = TypeVar("T")

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY_MS = 50
DEFAULT_MAX_DELAY_MS = 1000
DEFAULT_JITTER_RATIO = 0.5


async def retry_with_backoff(
        operation: Callable[[], Awaitable[T]],
        *,
        max_retries: int,
        base_delay_ms: int,
        max_delay_ms: int,
        jitter_ratio: float,
        retryable_exceptions: tuple[type[Exception], ...],
        operation_name: str = "iam_operation",
) -> T:
    """Run one async operation with exponential backoff and random jitter."""

    retries = max(int(max_retries), 0)
    base_delay = max(int(base_delay_ms), 0)
    max_delay = max(int(max_delay_ms), 0)
    ratio = float(jitter_ratio)
    if ratio < 0:
        ratio = 0.0
    if ratio > 1:
        ratio = 1.0

    attempt = 0
    while True:
        try:
            return await operation()
        except retryable_exceptions as exc:
            if attempt >= retries:
                raise

            delay_ms = min(base_delay * (2 ** attempt), max_delay)
            jitter_ms = random.uniform(0, delay_ms * ratio) if delay_ms > 0 else 0.0
            sleep_seconds = (delay_ms + jitter_ms) / 1000.0

            iam_logger.warning(
                "retry with backoff",
                extra={
                    "operation_name": operation_name,
                    "attempt": attempt + 1,
                    "delay_ms": int(delay_ms + jitter_ms),
                    "base_delay_ms": base_delay,
                    "max_delay_ms": max_delay,
                    "jitter_ratio": ratio,
                    "exception_class": exc.__class__.__name__,
                },
            )
            await asyncio.sleep(sleep_seconds)
            attempt += 1
        except Exception:
            raise
