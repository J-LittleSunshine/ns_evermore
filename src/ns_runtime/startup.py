# -*- coding: utf-8 -*-
"""Synchronous startup preflight for the standalone runtime process.

The preflight deliberately runs before an event loop or transport listener is
created.  It validates the immutable configuration snapshot, process
environment, local dependencies and directories, and only then selects or
installs the configured event-loop policy.  Transport and StateStore resources
remain owned by their later implementation phases.
"""

from __future__ import annotations

import importlib.util
import os
import ssl
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping, NoReturn

from ns_common.async_runtime import (
    NsEventLoopSelection,
    NsEventLoopSelector,
)
from ns_runtime._bootstrap import (
    DATA_DIR,
    ETC_DIR,
    LOG_DIR,
    ROOT_DIR,
    TMP_DIR,
    NsConfig,
    NsConfigError,
    NsDependencyError,
    NsRuntimeConfigInvalidError,
    NsRuntimeStartupSecurityError,
    NsRuntimeTransportDisabledError,
    NsValidationError,
)
from ns_runtime.context import RuntimeContext


_RUNTIME_ENVIRONMENTS: tuple[str, ...] = (
    "dev",
    "local",
    "prod",
    "test",
)
# This is a configuration admission list, not an operational transport
# registry.  P04 still owns the first listener/adapter implementation.
_STARTUP_ADMITTED_TRANSPORT_ADAPTERS = frozenset({"websocket_tcp"})
_TRANSPORT_DEPENDENCIES: Mapping[str, str] = MappingProxyType({
    "websocket_tcp": "websockets",
})

DependencyProbe = Callable[[str], object | None]
DirectoryAccessProbe = Callable[[Path, int], bool]
TlsCapabilityProbe = Callable[[], bool]


def _raise_normalized_startup_config_error(
    error: NsConfigError,
    *,
    environment: str,
) -> NoReturn:
    """Raise one stable RSP-1 error for a configuration validation failure."""

    field = error.details.get("field")
    reason: str | None = None
    if (
        environment == "prod"
        and isinstance(field, str)
        and field.startswith("runtime.transport.")
        and field.endswith(".tls_enabled")
    ):
        reason = "plaintext_transport_in_production"
    elif field == "runtime.security.require_tls_in_prod":
        reason = "production_tls_requirement_disabled"
    elif field == "runtime.security.allow_plaintext_non_prod":
        reason = "plaintext_transport_disabled"
    elif environment == "prod" and field == "runtime.state_store.backend":
        reason = "non_production_state_store_backend"

    if reason is None:
        raise error
    raise NsRuntimeStartupSecurityError(
        "Runtime startup security configuration is invalid.",
        details={
            "component": "runtime_startup",
            "field": field,
            "environment": environment,
            "reason": reason,
        },
    ) from None


def _find_python_dependency(package_name: str) -> object | None:
    return importlib.util.find_spec(package_name)


def _has_server_tls_capability() -> bool:
    if not (
        hasattr(ssl, "SSLContext")
        and hasattr(ssl, "PROTOCOL_TLS_SERVER")
    ):
        return False
    try:
        ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    except Exception:
        return False
    return True


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeStartupDirectories:
    """Explicit directory wiring used by one startup preflight."""

    root_dir: Path
    data_dir: Path
    etc_dir: Path
    log_dir: Path
    tmp_dir: Path

    def __post_init__(self) -> None:
        for field_name in (
            "root_dir",
            "data_dir",
            "etc_dir",
            "log_dir",
            "tmp_dir",
        ):
            value = getattr(self, field_name)
            try:
                normalized = Path(value)
            except (TypeError, ValueError):
                raise NsValidationError(
                    "Runtime startup directory is invalid.",
                    details={
                        "component": "runtime_startup",
                        "directory": field_name.removesuffix("_dir"),
                        "actual_type": type(value).__name__,
                    },
                ) from None
            object.__setattr__(self, field_name, normalized)

    @classmethod
    def repository_defaults(cls) -> "RuntimeStartupDirectories":
        return cls(
            root_dir=ROOT_DIR,
            data_dir=DATA_DIR,
            etc_dir=ETC_DIR,
            log_dir=LOG_DIR,
            tmp_dir=TMP_DIR,
        )

    @classmethod
    def for_root(
        cls,
        root_dir: str | os.PathLike[str],
    ) -> "RuntimeStartupDirectories":
        root = Path(root_dir)
        return cls(
            root_dir=root,
            data_dir=root / "data",
            etc_dir=root / "etc",
            log_dir=root / "log",
            tmp_dir=root / "tmp",
        )

    def required_directories(self) -> tuple[tuple[str, Path], ...]:
        return (
            ("data", self.data_dir),
            ("etc", self.etc_dir),
            ("log", self.log_dir),
            ("tmp", self.tmp_dir),
        )


@dataclass(frozen=True, slots=True)
class RuntimeStartupPreflightResult:
    """Sanitized facts proven before the runtime service can start."""

    environment: str
    event_loop: NsEventLoopSelection
    event_loop_policy_installed: bool
    enabled_transport_adapters: tuple[str, ...]
    tls_transport_adapters: tuple[str, ...]
    state_store_backend: str
    checked_dependencies: tuple[str, ...]
    prepared_directories: tuple[str, ...]


class RuntimeStartupPreflight:
    """Validate and prepare process startup without opening a listener."""

    def __init__(
        self,
        *,
        event_loop_selector: NsEventLoopSelector | None = None,
        dependency_probe: DependencyProbe = _find_python_dependency,
        directory_access_probe: DirectoryAccessProbe = os.access,
        tls_capability_probe: TlsCapabilityProbe = _has_server_tls_capability,
    ) -> None:
        if (
            event_loop_selector is not None
            and not isinstance(event_loop_selector, NsEventLoopSelector)
        ):
            raise NsValidationError(
                "Runtime startup event-loop selector is invalid.",
                details={
                    "component": "runtime_startup",
                    "dependency": "event_loop_selector",
                    "expected_type": "NsEventLoopSelector",
                    "actual_type": type(event_loop_selector).__name__,
                },
            )
        if not callable(dependency_probe):
            raise NsValidationError(
                "Runtime startup probe is invalid.",
                details={
                    "component": "runtime_startup",
                    "dependency": "dependency_probe",
                    "actual_type": type(dependency_probe).__name__,
                },
            )
        if not callable(directory_access_probe):
            raise NsValidationError(
                "Runtime startup probe is invalid.",
                details={
                    "component": "runtime_startup",
                    "dependency": "directory_access_probe",
                    "actual_type": type(directory_access_probe).__name__,
                },
            )
        if not callable(tls_capability_probe):
            raise NsValidationError(
                "Runtime startup probe is invalid.",
                details={
                    "component": "runtime_startup",
                    "dependency": "tls_capability_probe",
                    "actual_type": type(tls_capability_probe).__name__,
                },
            )

        self._event_loop_selector = event_loop_selector or NsEventLoopSelector()
        self._dependency_probe = dependency_probe
        self._directory_access_probe = directory_access_probe
        self._tls_capability_probe = tls_capability_probe

    def load_config_snapshot(
        self,
        config_path: str | os.PathLike[str],
        *,
        environment: str | None = None,
    ) -> NsConfig:
        """Load an explicitly addressed snapshot under the RSP-1 error boundary.

        An explicit path is required so CFG-1's compatible no-path directory
        preparation behavior cannot run before this preflight prepares its own
        explicitly wired directories.
        """

        resolved_environment = self.resolve_environment(environment)
        if config_path is None:
            raise NsValidationError(
                "Runtime startup config path must be explicit.",
                details={
                    "component": "runtime_startup",
                    "dependency": "config_path",
                    "actual_type": "NoneType",
                },
            )
        try:
            return NsConfig.load(
                config_path=config_path,
                environment=resolved_environment,
            )
        except NsConfigError as error:
            _raise_normalized_startup_config_error(
                error,
                environment=resolved_environment,
            )

    @staticmethod
    def resolve_environment(environment: str | None = None) -> str:
        raw_environment: object = (
            os.getenv("NS_ENV", "local")
            if environment is None
            else environment
        )
        if not isinstance(raw_environment, str):
            raise NsRuntimeConfigInvalidError(
                "Runtime startup environment is invalid.",
                details={
                    "component": "runtime_startup",
                    "field": "environment",
                    "actual_type": type(raw_environment).__name__,
                    "allowed_values": list(_RUNTIME_ENVIRONMENTS),
                },
            )

        normalized = raw_environment.strip().lower()
        if normalized not in _RUNTIME_ENVIRONMENTS:
            raise NsRuntimeConfigInvalidError(
                "Runtime startup environment is invalid.",
                details={
                    "component": "runtime_startup",
                    "field": "environment",
                    "allowed_values": list(_RUNTIME_ENVIRONMENTS),
                },
            )
        return normalized

    def validate(
        self,
        context: RuntimeContext,
        *,
        environment: str | None = None,
        directories: RuntimeStartupDirectories | None = None,
    ) -> RuntimeStartupPreflightResult:
        """Run preflight checks without replacing the event-loop policy."""

        return self._run(
            context,
            environment=environment,
            directories=directories,
            install_event_loop_policy=False,
        )

    def prepare(
        self,
        context: RuntimeContext,
        *,
        environment: str | None = None,
        directories: RuntimeStartupDirectories | None = None,
    ) -> RuntimeStartupPreflightResult:
        """Run preflight checks and install the selected event-loop policy."""

        return self._run(
            context,
            environment=environment,
            directories=directories,
            install_event_loop_policy=True,
        )

    def _run(
        self,
        context: RuntimeContext,
        *,
        environment: str | None,
        directories: RuntimeStartupDirectories | None,
        install_event_loop_policy: bool,
    ) -> RuntimeStartupPreflightResult:
        if not isinstance(context, RuntimeContext):
            raise NsValidationError(
                "Runtime startup requires a RuntimeContext.",
                details={
                    "component": "runtime_startup",
                    "dependency": "context",
                    "expected_type": "RuntimeContext",
                    "actual_type": type(context).__name__,
                },
            )

        startup_directories = (
            RuntimeStartupDirectories.repository_defaults()
            if directories is None
            else directories
        )
        if not isinstance(startup_directories, RuntimeStartupDirectories):
            raise NsValidationError(
                "Runtime startup directories are invalid.",
                details={
                    "component": "runtime_startup",
                    "dependency": "directories",
                    "expected_type": "RuntimeStartupDirectories",
                    "actual_type": type(startup_directories).__name__,
                },
            )

        resolved_environment = self.resolve_environment(environment)
        self._validate_config(context, resolved_environment)
        self._validate_startup_security(context, resolved_environment)
        self._validate_transport_availability(context)
        checked_dependencies = self._validate_dependencies(context)
        self._validate_tls_capability(context)
        prepared_directories = self._prepare_directories(
            context,
            startup_directories,
        )

        if install_event_loop_policy:
            event_loop_selection = self._event_loop_selector.install(
                context.config.runtime.event_loop,
            )
        else:
            event_loop_selection = self._event_loop_selector.select(
                context.config.runtime.event_loop,
            )

        transport = context.config.runtime.transport
        tls_adapters = tuple(
            name
            for name, adapter in transport.adapters()
            if adapter.enabled and adapter.tls_enabled
        )
        return RuntimeStartupPreflightResult(
            environment=resolved_environment,
            event_loop=event_loop_selection,
            event_loop_policy_installed=install_event_loop_policy,
            enabled_transport_adapters=transport.enabled_adapters,
            tls_transport_adapters=tls_adapters,
            state_store_backend=context.config.runtime.state_store.backend,
            checked_dependencies=checked_dependencies,
            prepared_directories=prepared_directories,
        )

    @staticmethod
    def _validate_config(
        context: RuntimeContext,
        environment: str,
    ) -> None:
        try:
            context.config.validate(environment=environment)
        except NsConfigError as error:
            _raise_normalized_startup_config_error(
                error,
                environment=environment,
            )

    @staticmethod
    def _validate_startup_security(
        context: RuntimeContext,
        environment: str,
    ) -> None:
        runtime = context.config.runtime
        transport = runtime.transport
        security = runtime.security

        if not security.require_tls_in_prod:
            raise NsRuntimeStartupSecurityError(
                "Runtime production TLS requirement cannot be disabled.",
                details={
                    "component": "runtime_startup",
                    "field": "runtime.security.require_tls_in_prod",
                    "environment": environment,
                    "reason": "production_tls_requirement_disabled",
                },
            )

        plaintext_adapters = tuple(
            name
            for name, adapter in transport.adapters()
            if adapter.enabled and not adapter.tls_enabled
        )
        if environment == "prod" and plaintext_adapters:
            raise NsRuntimeStartupSecurityError(
                "Runtime production transports must use TLS.",
                details={
                    "component": "runtime_startup",
                    "field": "runtime.transport",
                    "environment": environment,
                    "adapters": list(plaintext_adapters),
                    "reason": "plaintext_transport_in_production",
                },
            )
        if (
            environment != "prod"
            and plaintext_adapters
            and not security.allow_plaintext_non_prod
        ):
            raise NsRuntimeStartupSecurityError(
                "Runtime plaintext transports are disabled.",
                details={
                    "component": "runtime_startup",
                    "field": "runtime.security.allow_plaintext_non_prod",
                    "environment": environment,
                    "adapters": list(plaintext_adapters),
                    "reason": "plaintext_transport_disabled",
                },
            )

        state_store_backend = runtime.state_store.backend
        if environment == "prod" and state_store_backend not in {"redis", "valkey"}:
            raise NsRuntimeStartupSecurityError(
                "Runtime production StateStore must use Redis or Valkey.",
                details={
                    "component": "runtime_startup",
                    "field": "runtime.state_store.backend",
                    "environment": environment,
                    "allowed_values": ["redis", "valkey"],
                    "reason": "non_production_state_store_backend",
                },
            )

    @staticmethod
    def _validate_transport_availability(context: RuntimeContext) -> None:
        unavailable_adapters = tuple(
            name
            for name in context.config.runtime.transport.enabled_adapters
            if name not in _STARTUP_ADMITTED_TRANSPORT_ADAPTERS
        )
        if unavailable_adapters:
            raise NsRuntimeTransportDisabledError(
                "Configured runtime transport is not available in this build.",
                details={
                    "component": "runtime_startup",
                    "phase": "preflight",
                    "adapters": list(unavailable_adapters),
                    "reason": "feature_not_implemented",
                },
            )

    def _validate_dependencies(self, context: RuntimeContext) -> tuple[str, ...]:
        checked_dependencies: list[str] = []
        for adapter_name in context.config.runtime.transport.enabled_adapters:
            package_name = _TRANSPORT_DEPENDENCIES.get(adapter_name)
            if package_name is None:
                continue
            checked_dependencies.append(package_name)
            try:
                available = self._dependency_probe(package_name) is not None
            except Exception:
                available = False
            if available:
                continue
            raise NsDependencyError(
                "Runtime startup dependency is unavailable.",
                details={
                    "component": "runtime_startup",
                    "phase": "preflight",
                    "field": f"runtime.transport.{adapter_name}",
                    "dependency": package_name,
                },
            ) from None
        return tuple(checked_dependencies)

    def _validate_tls_capability(self, context: RuntimeContext) -> None:
        tls_adapters = tuple(
            name
            for name, adapter in context.config.runtime.transport.adapters()
            if adapter.enabled and adapter.tls_enabled
        )
        if not tls_adapters:
            return

        try:
            tls_available = self._tls_capability_probe() is True
        except Exception:
            tls_available = False
        if tls_available:
            return
        raise NsRuntimeStartupSecurityError(
            "Runtime server TLS capability is unavailable.",
            details={
                "component": "runtime_startup",
                "field": "runtime.transport",
                "adapters": list(tls_adapters),
                "reason": "server_tls_capability_unavailable",
            },
        ) from None

    def _prepare_directories(
        self,
        context: RuntimeContext,
        directories: RuntimeStartupDirectories,
    ) -> tuple[str, ...]:
        required_directories = list(directories.required_directories())
        state_store = context.config.runtime.state_store
        if state_store.backend == "sqlite":
            sqlite_path = Path(state_store.sqlite_path)
            if not sqlite_path.is_absolute():
                sqlite_path = directories.root_dir / sqlite_path
            required_directories.append(("state_store", sqlite_path.parent))

        prepared_roles: list[str] = []
        prepared_paths: set[Path] = set()
        for role, path in required_directories:
            normalized_path = Path(path)
            if normalized_path in prepared_paths:
                continue
            self._prepare_directory(normalized_path, role=role)
            prepared_paths.add(normalized_path)
            prepared_roles.append(role)
        return tuple(prepared_roles)

    def _prepare_directory(self, path: Path, *, role: str) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            raise NsDependencyError(
                "Runtime startup directory could not be prepared.",
                details={
                    "component": "runtime_startup",
                    "phase": "preflight",
                    "directory": role,
                    "reason": "create_failed",
                },
            ) from None

        try:
            is_directory = path.is_dir()
        except OSError:
            is_directory = False
        if not is_directory:
            raise NsDependencyError(
                "Runtime startup directory is unavailable.",
                details={
                    "component": "runtime_startup",
                    "phase": "preflight",
                    "directory": role,
                    "reason": "not_directory",
                },
            ) from None

        access_mode = os.R_OK | os.W_OK | os.X_OK
        try:
            accessible = self._directory_access_probe(path, access_mode) is True
        except Exception:
            accessible = False
        if not accessible:
            raise NsDependencyError(
                "Runtime startup directory is not accessible.",
                details={
                    "component": "runtime_startup",
                    "phase": "preflight",
                    "directory": role,
                    "reason": "access_denied",
                },
            ) from None


__all__ = [
    "RuntimeStartupDirectories",
    "RuntimeStartupPreflight",
    "RuntimeStartupPreflightResult",
]
