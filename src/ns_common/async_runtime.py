# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import importlib
import platform
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
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
    "install_event_loop_policy",
    "select_event_loop",
]
