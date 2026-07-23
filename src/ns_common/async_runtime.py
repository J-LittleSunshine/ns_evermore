# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import importlib
import inspect
import math
import platform
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    Coroutine,
    Literal,
)

from ns_common.config import NsRuntimeEventLoopConfig
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsStateError,
)


class NsEventLoopImplementation(str, Enum):
    ASYNCIO = "asyncio"
    UVLOOP = "uvloop"


class NsEventLoopFallbackWarning(RuntimeWarning):
    """Emitted when auto mode cannot use uvloop on Linux."""


@dataclass(frozen=True, slots=True)
class NsEventLoopSelection:
    requested: Literal["auto", "asyncio", "uvloop"]
    selected: NsEventLoopImplementation
    platform: str
    fallback: bool = False
    reason: str = "configured"
    warning: str | None = None


EventLoopPolicyFactory = Callable[[], asyncio.AbstractEventLoopPolicy]
ModuleLoader = Callable[[str], Any]
RunningLoopGetter = Callable[[], asyncio.AbstractEventLoop]
PolicySetter = Callable[[asyncio.AbstractEventLoopPolicy], None]
WarningEmitter = Callable[[str], None]


def _emit_fallback_warning(message: str) -> None:
    warnings.warn(
        message,
        NsEventLoopFallbackWarning,
        stacklevel=3,
    )


class NsEventLoopSelector:
    """Select and install an event loop policy at process startup.

    Platform, import, policy and running-loop functions are injectable so the
    complete platform matrix can be verified without mutating test process
    globals or requiring uvloop on Windows.
    """

    def __init__(
        self,
        *,
        platform_system: Callable[[], str] = platform.system,
        module_loader: ModuleLoader = importlib.import_module,
        asyncio_policy_factory: EventLoopPolicyFactory = asyncio.DefaultEventLoopPolicy,
        running_loop_getter: RunningLoopGetter = asyncio.get_running_loop,
        policy_setter: PolicySetter = asyncio.set_event_loop_policy,
        warning_emitter: WarningEmitter = _emit_fallback_warning,
    ) -> None:
        self._platform_system = platform_system
        self._module_loader = module_loader
        self._asyncio_policy_factory = asyncio_policy_factory
        self._running_loop_getter = running_loop_getter
        self._policy_setter = policy_setter
        self._warning_emitter = warning_emitter

    def select(self, config: NsRuntimeEventLoopConfig) -> NsEventLoopSelection:
        selection, _ = self._resolve(config)
        if selection.warning is not None:
            self._warning_emitter(selection.warning)
        return selection

    def install(self, config: NsRuntimeEventLoopConfig) -> NsEventLoopSelection:
        self._ensure_startup_boundary(config)
        selection, policy_factory = self._resolve(config)
        try:
            policy = policy_factory()
        except Exception as error:
            if selection.selected is not NsEventLoopImplementation.UVLOOP:
                raise
            if selection.requested == "uvloop":
                raise NsDependencyError(
                    "uvloop was explicitly selected but its policy could not be initialized.",
                    details={
                        "field": "runtime.event_loop.implementation",
                        "value": "uvloop",
                        "platform": selection.platform,
                        "package": "uvloop",
                        "phase": "policy_initialization",
                    },
                ) from error

            warning = (
                "runtime.event_loop auto mode could not initialize the uvloop "
                "policy on Linux; falling back to the standard asyncio policy."
            )
            selection = NsEventLoopSelection(
                requested="auto",
                selected=NsEventLoopImplementation.ASYNCIO,
                platform=selection.platform,
                fallback=True,
                reason="auto_uvloop_initialization_failed",
                warning=warning,
            )
            policy = self._asyncio_policy_factory()
        self._policy_setter(policy)

        if selection.warning is not None:
            self._warning_emitter(selection.warning)

        return selection

    def _resolve(
        self,
        config: NsRuntimeEventLoopConfig,
    ) -> tuple[NsEventLoopSelection, EventLoopPolicyFactory]:
        self._validate_config(config)
        platform_name = self._normalize_platform(self._platform_system())
        requested = config.implementation

        if requested == "asyncio":
            return (
                NsEventLoopSelection(
                    requested=requested,
                    selected=NsEventLoopImplementation.ASYNCIO,
                    platform=platform_name,
                    reason="explicit_asyncio",
                ),
                self._asyncio_policy_factory,
            )

        if requested == "uvloop":
            if platform_name == "windows":
                raise NsDependencyError(
                    "uvloop is not supported on Windows.",
                    details={
                        "field": "runtime.event_loop.implementation",
                        "value": requested,
                        "platform": platform_name,
                        "package": "uvloop",
                    },
                )

            policy_factory = self._load_uvloop_policy_factory(
                required=True,
                platform_name=platform_name,
            )
            return (
                NsEventLoopSelection(
                    requested=requested,
                    selected=NsEventLoopImplementation.UVLOOP,
                    platform=platform_name,
                    reason="explicit_uvloop",
                ),
                policy_factory,
            )

        if platform_name == "linux":
            policy_factory = self._load_uvloop_policy_factory(
                required=False,
                platform_name=platform_name,
            )
            if policy_factory is not None:
                return (
                    NsEventLoopSelection(
                        requested=requested,
                        selected=NsEventLoopImplementation.UVLOOP,
                        platform=platform_name,
                        reason="auto_linux_uvloop",
                    ),
                    policy_factory,
                )

            warning = (
                "runtime.event_loop auto mode could not load uvloop on Linux; "
                "falling back to the standard asyncio policy."
            )
            return (
                NsEventLoopSelection(
                    requested=requested,
                    selected=NsEventLoopImplementation.ASYNCIO,
                    platform=platform_name,
                    fallback=True,
                    reason="auto_uvloop_unavailable",
                    warning=warning,
                ),
                self._asyncio_policy_factory,
            )

        reason = (
            "auto_windows_asyncio"
            if platform_name == "windows"
            else "auto_platform_asyncio"
        )
        return (
            NsEventLoopSelection(
                requested=requested,
                selected=NsEventLoopImplementation.ASYNCIO,
                platform=platform_name,
                reason=reason,
            ),
            self._asyncio_policy_factory,
        )

    def _load_uvloop_policy_factory(
        self,
        *,
        required: bool,
        platform_name: str,
    ) -> EventLoopPolicyFactory | None:
        try:
            uvloop_module = self._module_loader("uvloop")
            policy_factory = getattr(uvloop_module, "EventLoopPolicy")
            if not callable(policy_factory):
                raise TypeError("uvloop.EventLoopPolicy is not callable")
            return policy_factory
        except Exception as error:
            if not required:
                return None

            raise NsDependencyError(
                "uvloop was explicitly selected but is unavailable.",
                details={
                    "field": "runtime.event_loop.implementation",
                    "value": "uvloop",
                    "platform": platform_name,
                    "package": "uvloop",
                },
            ) from error

    def _ensure_startup_boundary(self, config: NsRuntimeEventLoopConfig) -> None:
        try:
            running_loop = self._running_loop_getter()
        except RuntimeError:
            return

        raise NsStateError(
            "event loop policy cannot change while an event loop is running.",
            details={
                "field": "runtime.event_loop.implementation",
                "requested": config.implementation,
                "running_loop": type(running_loop).__name__,
                "apply_mode": "restart_required",
                "action": "restart_required",
            },
        )

    @staticmethod
    def _validate_config(config: NsRuntimeEventLoopConfig) -> None:
        if not isinstance(config, NsRuntimeEventLoopConfig):
            raise NsConfigError(
                "event loop selector requires NsRuntimeEventLoopConfig.",
                details={
                    "field": "runtime.event_loop",
                    "actual_type": type(config).__name__,
                },
            )
        if config.implementation not in {"auto", "asyncio", "uvloop"}:
            raise NsConfigError(
                "runtime.event_loop.implementation is invalid.",
                details={
                    "field": "runtime.event_loop.implementation",
                    "value": config.implementation,
                    "allowed_values": ["auto", "asyncio", "uvloop"],
                },
            )
        if config.metadata.apply_mode != "restart_required":
            raise NsConfigError(
                "event loop implementation must use restart_required apply mode.",
                details={
                    "field": "runtime.event_loop.metadata.apply_mode",
                    "value": config.metadata.apply_mode,
                    "expected": "restart_required",
                },
            )

    @staticmethod
    def _normalize_platform(value: str) -> str:
        normalized = value.strip().lower()
        if normalized.startswith("win"):
            return "windows"
        if normalized.startswith("linux"):
            return "linux"
        return normalized or "unknown"


class NsTaskSupervisorState(str, Enum):
    ACCEPTING = "accepting"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class NsTaskFailure:
    name: str
    exception: BaseException

    @property
    def exception_type(self) -> str:
        return type(self.exception).__name__

    @property
    def message(self) -> str:
        return str(self.exception)


@dataclass(frozen=True, slots=True)
class NsUnfinishedTask:
    name: str
    cancel_order: int
    created_order: int
    cancelling_count: int


@dataclass(frozen=True, slots=True)
class NsTaskShutdownReport:
    total_tasks: int
    completed_tasks: tuple[str, ...]
    cancelled_tasks: tuple[str, ...]
    failed_tasks: tuple[str, ...]
    cancellation_order: tuple[str, ...]
    unfinished_tasks: tuple[NsUnfinishedTask, ...]
    failures: tuple[NsTaskFailure, ...]
    timeout_seconds: float

    @property
    def timed_out(self) -> bool:
        return bool(self.unfinished_tasks)

    @property
    def clean(self) -> bool:
        return not self.failed_tasks and not self.unfinished_tasks


@dataclass(slots=True)
class _SupervisedTaskRecord:
    name: str
    task: asyncio.Task[Any]
    cancel_order: int
    created_order: int
    outcome: Literal["pending", "completed", "cancelled", "failed"] = "pending"
    observed: bool = False
    cancel_requested_count: int = 0


TaskFailureHandler = Callable[[NsTaskFailure], None]


class TaskSupervisor:
    """Own named tasks and report every terminal outcome.

    Smaller ``cancel_order`` values are cancelled first. Tasks sharing the
    same order are cancelled in creation order. The supervisor is bound to the
    first running event loop that uses it and cannot be shared across loops.
    """

    def __init__(
        self,
        *,
        shutdown_timeout_seconds: float = 30.0,
        failure_handler: TaskFailureHandler | None = None,
    ) -> None:
        self._validate_timeout(shutdown_timeout_seconds)
        self._shutdown_timeout_seconds = float(shutdown_timeout_seconds)
        self._failure_handler = failure_handler
        self._state = NsTaskSupervisorState.ACCEPTING
        self._loop: asyncio.AbstractEventLoop | None = None
        self._shutdown_lock: asyncio.Lock | None = None
        self._records_by_name: dict[str, _SupervisedTaskRecord] = {}
        self._records_by_task: dict[asyncio.Task[Any], _SupervisedTaskRecord] = {}
        self._failures: list[NsTaskFailure] = []
        self._created_count = 0
        self._shutdown_report: NsTaskShutdownReport | None = None

    @property
    def state(self) -> NsTaskSupervisorState:
        return self._state

    @property
    def failures(self) -> tuple[NsTaskFailure, ...]:
        return tuple(self._failures)

    @property
    def task_names(self) -> tuple[str, ...]:
        return tuple(self._records_by_name)

    @property
    def pending_task_names(self) -> tuple[str, ...]:
        return tuple(
            record.name
            for record in self._records_by_name.values()
            if not record.task.done()
        )

    @property
    def cancelled_task_count(self) -> int:
        """Return supervised tasks observed in the cancelled terminal state."""

        return len(self._task_names_with_outcome("cancelled"))

    def get_task(self, name: str) -> asyncio.Task[Any]:
        try:
            return self._records_by_name[name].task
        except KeyError as error:
            raise NsStateError(
                "supervised task does not exist.",
                details={
                    "field": "task.name",
                    "name": name,
                },
            ) from error

    def create_task(
        self,
        coroutine: Coroutine[Any, Any, Any],
        *,
        name: str,
        cancel_order: int = 100,
    ) -> asyncio.Task[Any]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as error:
            self._close_coroutine(coroutine)
            raise NsStateError(
                "TaskSupervisor.create_task() requires a running event loop.",
                details={"action": "create_task"},
            ) from error

        try:
            self._bind_loop(loop)
            self._validate_task_registration(
                coroutine,
                name=name,
                cancel_order=cancel_order,
            )
        except BaseException:
            self._close_coroutine(coroutine)
            raise

        try:
            task = loop.create_task(coroutine, name=name)
        except BaseException:
            self._close_coroutine(coroutine)
            raise
        record = _SupervisedTaskRecord(
            name=name,
            task=task,
            cancel_order=cancel_order,
            created_order=self._created_count,
        )
        self._created_count += 1
        self._records_by_name[name] = record
        self._records_by_task[task] = record
        task.add_done_callback(self._observe_task)
        return task

    async def shutdown(
        self,
        *,
        timeout_seconds: float | None = None,
    ) -> NsTaskShutdownReport:
        loop = asyncio.get_running_loop()
        self._bind_loop(loop)
        raw_timeout = (
            self._shutdown_timeout_seconds
            if timeout_seconds is None
            else timeout_seconds
        )
        self._validate_timeout(raw_timeout)
        timeout = float(raw_timeout)

        if self._shutdown_lock is None:
            self._shutdown_lock = asyncio.Lock()

        async with self._shutdown_lock:
            if self._shutdown_report is not None:
                return self._shutdown_report

            current_task = asyncio.current_task()
            if current_task in self._records_by_task and not current_task.done():
                raise NsStateError(
                    "a supervised task cannot shut down its own supervisor.",
                    details={
                        "task": self._records_by_task[current_task].name,
                        "action": "shutdown",
                    },
                )

            self._state = NsTaskSupervisorState.CLOSING
            deadline = loop.time() + timeout
            cancellation_order: list[str] = []
            pending_records = [
                record
                for record in self._records_by_name.values()
                if not record.task.done()
            ]
            cancel_orders = sorted({record.cancel_order for record in pending_records})

            for cancel_order in cancel_orders:
                group = [
                    record
                    for record in pending_records
                    if record.cancel_order == cancel_order and not record.task.done()
                ]
                group.sort(key=lambda record: record.created_order)
                for record in group:
                    if record.task.cancel():
                        record.cancel_requested_count += 1
                    cancellation_order.append(record.name)

                remaining = max(0.0, deadline - loop.time())
                if group and remaining > 0.0:
                    await asyncio.wait(
                        [record.task for record in group],
                        timeout=remaining,
                    )

            # Deliver cancellation to groups reached after the timeout budget.
            await asyncio.sleep(0)
            for record in self._records_by_name.values():
                if record.task.done():
                    self._observe_task(record.task)

            unfinished = tuple(
                NsUnfinishedTask(
                    name=record.name,
                    cancel_order=record.cancel_order,
                    created_order=record.created_order,
                    cancelling_count=record.cancel_requested_count,
                )
                for record in self._records_by_name.values()
                if not record.task.done()
            )
            report = NsTaskShutdownReport(
                total_tasks=len(self._records_by_name),
                completed_tasks=self._task_names_with_outcome("completed"),
                cancelled_tasks=self._task_names_with_outcome("cancelled"),
                failed_tasks=self._task_names_with_outcome("failed"),
                cancellation_order=tuple(cancellation_order),
                unfinished_tasks=unfinished,
                failures=tuple(self._failures),
                timeout_seconds=timeout,
            )
            self._shutdown_report = report
            self._state = NsTaskSupervisorState.CLOSED
            return report

    def _observe_task(self, task: asyncio.Task[Any]) -> None:
        record = self._records_by_task.get(task)
        if record is None or record.observed or not task.done():
            return

        record.observed = True
        if task.cancelled():
            record.outcome = "cancelled"
            return

        exception = task.exception()
        if exception is None:
            record.outcome = "completed"
            return

        record.outcome = "failed"
        failure = NsTaskFailure(name=record.name, exception=exception)
        self._failures.append(failure)
        if self._failure_handler is not None:
            try:
                self._failure_handler(failure)
            except Exception as handler_error:
                task.get_loop().call_exception_handler({
                    "message": "TaskSupervisor failure handler raised an exception.",
                    "exception": handler_error,
                    "task": task,
                })

    def _bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._loop is None:
            self._loop = loop
            return
        if self._loop is not loop:
            raise NsStateError(
                "TaskSupervisor cannot be shared across event loops.",
                details={
                    "action": "bind_loop",
                },
            )

    def _validate_task_registration(
        self,
        coroutine: Coroutine[Any, Any, Any],
        *,
        name: str,
        cancel_order: int,
    ) -> None:
        if self._state is not NsTaskSupervisorState.ACCEPTING:
            raise NsStateError(
                "TaskSupervisor is not accepting new tasks.",
                details={
                    "state": self._state.value,
                    "action": "create_task",
                },
            )
        if not inspect.iscoroutine(coroutine):
            raise NsConfigError(
                "TaskSupervisor requires a coroutine object.",
                details={
                    "field": "task.coroutine",
                    "actual_type": type(coroutine).__name__,
                },
            )
        if not isinstance(name, str) or not name.strip():
            raise NsConfigError(
                "supervised task name must be a non-empty string.",
                details={
                    "field": "task.name",
                    "value": name,
                },
            )
        if name != name.strip():
            raise NsConfigError(
                "supervised task name must not contain surrounding whitespace.",
                details={
                    "field": "task.name",
                    "value": name,
                },
            )
        if name in self._records_by_name:
            raise NsConfigError(
                "supervised task name must be unique for the supervisor lifetime.",
                details={
                    "field": "task.name",
                    "value": name,
                },
            )
        if isinstance(cancel_order, bool) or not isinstance(cancel_order, int):
            raise NsConfigError(
                "task.cancel_order must be an integer.",
                details={
                    "field": "task.cancel_order",
                    "value": cancel_order,
                    "actual_type": type(cancel_order).__name__,
                },
            )

    def _task_names_with_outcome(
        self,
        outcome: Literal["completed", "cancelled", "failed"],
    ) -> tuple[str, ...]:
        return tuple(
            record.name
            for record in self._records_by_name.values()
            if record.outcome == outcome
        )

    @staticmethod
    def _validate_timeout(value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise NsConfigError(
                "shutdown timeout must be a number.",
                details={
                    "field": "shutdown_timeout_seconds",
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )
        if not math.isfinite(float(value)) or value <= 0:
            raise NsConfigError(
                "shutdown timeout must be a finite positive number.",
                details={
                    "field": "shutdown_timeout_seconds",
                    "value": value,
                },
            )

    @staticmethod
    def _close_coroutine(value: Any) -> None:
        if inspect.iscoroutine(value):
            value.close()


NsTaskSupervisor = TaskSupervisor


def select_event_loop(
    config: NsRuntimeEventLoopConfig,
    *,
    selector: NsEventLoopSelector | None = None,
) -> NsEventLoopSelection:
    return (selector or NsEventLoopSelector()).select(config)


def install_event_loop_policy(
    config: NsRuntimeEventLoopConfig,
    *,
    selector: NsEventLoopSelector | None = None,
) -> NsEventLoopSelection:
    return (selector or NsEventLoopSelector()).install(config)


__all__ = [
    "NsEventLoopFallbackWarning",
    "NsEventLoopImplementation",
    "NsEventLoopSelection",
    "NsEventLoopSelector",
    "NsTaskFailure",
    "NsTaskShutdownReport",
    "NsTaskSupervisor",
    "NsTaskSupervisorState",
    "NsUnfinishedTask",
    "TaskSupervisor",
    "install_event_loop_policy",
    "select_event_loop",
]
