# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_runtime.service import RuntimeService


def main() -> int:
    service = RuntimeService.bootstrap()
    service.self_check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())