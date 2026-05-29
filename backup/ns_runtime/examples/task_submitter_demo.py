# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

# 仅用于本地示例直接运行：将 src 目录加入 sys.path，便于 `python src/ns_runtime/examples/task_submitter_demo.py` 执行。
PROJECT_SRC_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC_PATH))

from ns_runtime import (  # noqa: E402
    MemoryBroker,
    RuntimeTaskContext,
    RuntimeTaskSubmitRequest,
    RuntimeTaskSubmitter,
)


def main() -> None:
    broker = MemoryBroker()
    broker.start()

    submitter = RuntimeTaskSubmitter(
        broker=broker,
        use_stream=False,
    )

    request = RuntimeTaskSubmitRequest(
        task_type="demo.echo",
        payload={"message": "hello task"},
        context=RuntimeTaskContext(
            trace_id="task-demo-trace-1",
            tenant_id="tenant-demo",
            operator_id="operator-demo",
            source_endpoint_id="frontend-demo",
        ),
        required_capabilities=("demo.echo",),
    )

    result = submitter.submit_task(request)
    print("[submit]", result.task.task_id, result.task.task_type, result.task.status.value)

    stored_task = submitter.task_store.get(result.task.task_id)
    print("[task store]", stored_task.task_id if stored_task else None, stored_task.status.value if stored_task else None)

    packets = broker.poll("runtime.task.queue", max_count=1)
    if packets:
        task_payload = packets[0].payload.get("task", {})
        if isinstance(task_payload, dict):
            print("[broker task packet]", task_payload.get("task_id"), task_payload.get("task_type"))
        else:
            print("[broker task packet] invalid payload")
    else:
        print("[broker task packet] none")

    broker.stop()


if __name__ == "__main__":
    main()

