# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from ns_runtime.service import RuntimeService

if TYPE_CHECKING:
    pass


async def run_service() -> None:
    runtime_id = os.getenv("NS_RUNTIME_ID", "runtime-local-1").strip() or "runtime-local-1"
    service = RuntimeService.build_default(runtime_id=runtime_id)
    await service.start()


def main() -> None:
    asyncio.run(run_service())


if __name__ == "__main__":
    main()
