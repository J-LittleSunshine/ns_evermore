# -*- coding: utf-8 -*-
from __future__ import annotations

import multiprocessing
from multiprocessing.queues import Queue as MpQueue

from ns_executor.config import ExecutorClientConfig
from ns_executor.handlers import RuntimeTaskHandler, TaskHandlerRegistry
from ns_executor.io_process import ExecutorIoProcessRunner
from ns_executor.ipc import ExecutorIpcMessage
from ns_executor.main import ExecutorMainProcessRunner


def _run_io_process(config: ExecutorClientConfig, inbound_queue: MpQueue, outbound_queue: MpQueue) -> None:
    runner = ExecutorIoProcessRunner(
        config=config,
        inbound_queue=inbound_queue,
        outbound_queue=outbound_queue,
    )
    runner.run()


class ExecutorClient:
    def __init__(
        self,
        config: ExecutorClientConfig,
        handler_registry: TaskHandlerRegistry | None = None,
    ) -> None:
        self.config = config
        self._ctx = multiprocessing.get_context("spawn")
        self.inbound_queue: MpQueue = self._ctx.Queue()
        self.outbound_queue: MpQueue = self._ctx.Queue()
        self.handler_registry = handler_registry or TaskHandlerRegistry()
        self._main_runner = ExecutorMainProcessRunner(
            config=self.config,
            handler_registry=self.handler_registry,
            inbound_queue=self.inbound_queue,
            outbound_queue=self.outbound_queue,
        )

    def register_handler(self, task_type: str, handler: RuntimeTaskHandler) -> None:
        self.handler_registry.register(task_type, handler)

    def start_io_process(self) -> multiprocessing.Process:
        process = self._ctx.Process(
            target=_run_io_process,
            args=(self.config, self.inbound_queue, self.outbound_queue),
            name=f"executor-io-{self.config.endpoint_id}",
        )
        process.start()
        return process

    def run_main_once(self, timeout_seconds: float = 1.0) -> bool:
        return self._main_runner.run_once(timeout_seconds=timeout_seconds)

    def stop(self, io_process: multiprocessing.Process | None = None) -> None:
        self._main_runner.stop()

        stop_message = ExecutorIpcMessage.stop().to_dict()
        self.outbound_queue.put(dict(stop_message))
        self.inbound_queue.put(dict(stop_message))

        if io_process is not None:
            io_process.join(timeout=5.0)
            if io_process.is_alive():
                io_process.terminate()
                io_process.join(timeout=1.0)

