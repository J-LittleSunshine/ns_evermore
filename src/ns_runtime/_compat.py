"""
Compatibility helpers for ns_runtime.

This module keeps ns_runtime compatible with Python 3.10 while still using
Python 3.11-style APIs where available.
"""

try:
    # Python 3.11+
    from enum import StrEnum
except ImportError:
    # Python 3.10 fallback
    from enum import Enum


    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return self.value

        @staticmethod
        def _generate_next_value_(
                name: str,
                start: int,
                count: int,
                last_values: list[object],
        ) -> str:
            return name.lower()

try:
    # Python 3.11+
    from datetime import UTC
except ImportError:
    # Python 3.10 fallback
    from datetime import timezone

    UTC = timezone.utc
