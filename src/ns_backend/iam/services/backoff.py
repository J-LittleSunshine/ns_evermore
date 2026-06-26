# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import random
from typing import (
    Any,
    Awaitable,
    Callable,
    TypeVar,
)

from django.conf import settings

from ns_common import get_ns_logger

T = TypeVar("T")

logger = get_ns_logger("ns_backend.iam.backoff", True)

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY_MS = 50
DEFAULT_MAX_DELAY_MS = 1000
DEFAULT_JITTER_RATIO = 0.5


def coerce_non_negative_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    return max(parsed, 0)


def coerce_float(value: Any, default: float, *, min_value: float, max_value: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default

    if parsed < min_value:
        return min_value

    if parsed > max_value:
        return max_value

    return parsed


def get_backoff_enabled() -> bool:
    return bool(getattr(settings, "IAM_AUTH_BACKOFF_ENABLED", True))


def get_backoff_max_retries() -> int:
    return coerce_non_negative_int(
        getattr(settings, "IAM_AUTH_BACKOFF_MAX_RETRIES", DEFAULT_MAX_RETRIES),
        DEFAULT_MAX_RETRIES,
    )


def get_backoff_base_delay_ms() -> int:
    return coerce_non_negative_int(
        getattr(settings, "IAM_AUTH_BACKOFF_BASE_DELAY_MS", DEFAULT_BASE_DELAY_MS),
        DEFAULT_BASE_DELAY_MS,
    )


def get_backoff_max_delay_ms() -> int:
    return coerce_non_negative_int(
        getattr(settings, "IAM_AUTH_BACKOFF_MAX_DELAY_MS", DEFAULT_MAX_DELAY_MS),
        DEFAULT_MAX_DELAY_MS,
    )


def get_backoff_jitter_ratio() -> float:
    return coerce_float(
        getattr(settings, "IAM_AUTH_BACKOFF_JITTER_RATIO", DEFAULT_JITTER_RATIO),
        DEFAULT_JITTER_RATIO,
        min_value=0.0,
        max_value=1.0,
    )


async def retry_with_backoff(operation: Callable[[], Awaitable[T]], *, max_retries: int | None = None, base_delay_ms: int | None = None, max_delay_ms: int | None = None, jitter_ratio: float | None = None, retryable_exceptions: tuple[type[Exception], ...], operation_name: str = "iam_operation") -> T:
    retries = get_backoff_max_retries() if max_retries is None else coerce_non_negative_int(
        max_retries,
        DEFAULT_MAX_RETRIES,
    )
    base_delay = get_backoff_base_delay_ms() if base_delay_ms is None else coerce_non_negative_int(
        base_delay_ms,
        DEFAULT_BASE_DELAY_MS,
    )
    max_delay = get_backoff_max_delay_ms() if max_delay_ms is None else coerce_non_negative_int(
        max_delay_ms,
        DEFAULT_MAX_DELAY_MS,
    )
    ratio = get_backoff_jitter_ratio() if jitter_ratio is None else coerce_float(
        jitter_ratio,
        DEFAULT_JITTER_RATIO,
        min_value=0.0,
        max_value=1.0,
    )

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

            logger.warning(
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
