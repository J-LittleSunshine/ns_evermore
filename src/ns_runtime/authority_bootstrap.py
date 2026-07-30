# -*- coding: utf-8 -*-
"""One-shot deployment bootstrap for the production authority broker.

The environment carries descriptor numbers and a public trust root only.  Key
and credential bytes are never accepted as Python arguments or environment
strings.
"""

from __future__ import annotations

import os
import multiprocessing
import json
import sys
from multiprocessing.connection import Connection
from multiprocessing.reduction import DupFd

from ns_common.exceptions import NsRuntimeStartupSecurityError


_ROOT_KEY_FD_ENV = "NS_RUNTIME_AUTHORITY_KEY_FD"
_SECRETS_FD_ENV = "NS_RUNTIME_AUTHORITY_SECRETS_FD"
_ENDPOINT_ROLES = (
    "iam", "admission", "scheduler", "payload", "registry", "audit",
    "lifecycle",
)


class InheritedAuthorityBootstrap:
    __slots__ = (
        "_connections", "_process", "_attestor", "_consumed",
    )

    def __init__(
        self,
        *,
        connections: dict[str, Connection],
        process: multiprocessing.Process,
        attestor: object,
    ) -> None:
        if (
            type(connections) is not dict
            or set(connections) != set(_ENDPOINT_ROLES)
            or any(
                not isinstance(connection, Connection)
                for connection in connections.values()
            )
            or not process.is_alive()
        ):
            _security_error("invalid_inherited_authority_material")
        self._connections = dict(connections)
        self._process = process
        self._attestor = attestor
        self._consumed = False

    def launch(self, *, config: object, clock: object) -> object:
        if self._consumed:
            _security_error("authority_material_already_consumed")
        from ns_runtime.authority_broker import (
            AuthorityBrokerConfig,
            _complete_inherited_authority_broker_start,
        )
        from ns_common.time import Clock

        if type(config) is not AuthorityBrokerConfig or not isinstance(
            clock,
            Clock,
        ):
            _security_error("invalid_authority_broker_config")
        self._consumed = True
        connections = self._connections
        process = self._process
        attestor = self._attestor
        if connections is None or process is None or attestor is None:
            _security_error("invalid_inherited_authority_material")
        try:
            broker = _complete_inherited_authority_broker_start(
                parents=connections,
                process=process,
                attestor=attestor,
                config=config,
                clock=clock,
            )
        except BaseException as operation_failure:
            cleanup_failure = self._close_owned_resources()
            selected = _prioritize_failure(
                operation_failure,
                cleanup_failure,
            )
            if selected is not operation_failure:
                raise selected
            raise
        self._connections = None
        self._process = None
        self._attestor = None
        return broker

    def close(self) -> None:
        failure = self._close_owned_resources()
        self._consumed = True
        if failure is not None:
            raise failure

    def _close_owned_resources(self) -> BaseException | None:
        failure: BaseException | None = None
        connections = self._connections
        if connections is not None:
            failure = _close_connections(connections)
            if not connections:
                self._connections = None
        process = self._process
        if process is not None:
            process_failure = _reap_process(process, started=True)
            failure = _prioritize_failure(failure, process_failure)
            try:
                process_alive = process.is_alive()
            except BaseException:
                process_alive = True
            if not process_alive:
                self._process = None
        attestor = self._attestor
        if attestor is not None:
            try:
                attestor.close()
            except BaseException as error:
                failure = _prioritize_failure(failure, error)
            else:
                self._attestor = None
        return failure


class _PendingRawFdOwner:
    """Retain a detached descriptor until ``os.close`` actually completes."""

    __slots__ = ("descriptor",)

    def __init__(self, descriptor: int) -> None:
        self.descriptor = descriptor


class _AuthorityStartupCleanupOwner:
    """Retryable owner for resources acquired by an authority start factory."""

    __slots__ = (
        "connections",
        "duplicate_handles",
        "inherited_fds",
        "process",
        "process_start_attempted",
        "attestor",
    )

    def __init__(
        self,
        *,
        connections: tuple[dict[str, Connection], ...] = (),
        duplicate_handles: list[object] | None = None,
        inherited_fds: list[int] | None = None,
    ) -> None:
        self.connections = connections
        self.duplicate_handles = (
            [] if duplicate_handles is None else duplicate_handles
        )
        self.inherited_fds = [] if inherited_fds is None else inherited_fds
        self.process: multiprocessing.Process | None = None
        self.process_start_attempted = False
        self.attestor: object | None = None

    @property
    def incomplete(self) -> bool:
        return bool(
            any(connections for connections in self.connections)
            or self.duplicate_handles
            or self.inherited_fds
            or self.process is not None
            or self.attestor is not None
        )

    @property
    def process_alive(self) -> bool:
        process = self.process
        if process is None:
            return False
        try:
            return bool(process.is_alive())
        except BaseException:
            return True

    def pending_facts(self) -> dict[str, object]:
        return {
            "pending_connections": sum(
                len(connections) for connections in self.connections
            ),
            "pending_duplicate_handles": len(self.duplicate_handles),
            "pending_inherited_fds": len(self.inherited_fds),
            "process_owned": self.process is not None,
            "process_alive": self.process_alive,
            "attestor_owned": self.attestor is not None,
        }

    def close(self) -> None:
        failure: BaseException | None = None
        for connections in self.connections:
            failure = _prioritize_failure(
                failure,
                _close_connections(connections),
            )
        process = self.process
        if process is not None:
            failure = _prioritize_failure(
                failure,
                _reap_process(
                    process,
                    started=self.process_start_attempted,
                ),
            )
            try:
                alive = process.is_alive()
            except BaseException as error:
                failure = _prioritize_failure(failure, error)
                alive = True
            if not alive:
                self.process = None
        failure = _prioritize_failure(
            failure,
            _close_duplicate_handles(self.duplicate_handles),
        )
        failure = _prioritize_failure(
            failure,
            _close_inherited_fds(self.inherited_fds),
        )
        attestor = self.attestor
        if attestor is not None:
            try:
                attestor.close()
            except BaseException as error:
                failure = _prioritize_failure(failure, error)
            else:
                self.attestor = None
        if failure is not None:
            raise failure


def _raise_startup_cleanup_failure(
    owner: _AuthorityStartupCleanupOwner,
    *,
    operation_failure: BaseException | None,
    cleanup_failure: BaseException | None,
) -> None:
    if owner.incomplete:
        if (
            cleanup_failure is not None
            and not isinstance(cleanup_failure, Exception)
        ):
            cleanup_failure.cleanup_owner = owner  # type: ignore[attr-defined]
            cleanup_failure.cleanup_incomplete = True  # type: ignore[attr-defined]
            if operation_failure is not None:
                raise cleanup_failure from operation_failure
            raise cleanup_failure
        failure = _cleanup_error(
            "authority_startup_cleanup_incomplete",
            owner=owner,
        )
        if operation_failure is not None:
            raise failure from operation_failure
        if cleanup_failure is not None:
            raise failure from cleanup_failure
        raise failure
    selected = _prioritize_failure(operation_failure, cleanup_failure)
    if selected is cleanup_failure and cleanup_failure is not None:
        if operation_failure is not None:
            raise cleanup_failure from operation_failure
        raise cleanup_failure


def load_inherited_authority_bootstrap() -> InheritedAuthorityBootstrap:
    """Move inherited secrets into a spawn child before business imports."""

    root_fd_value = os.environ.pop(_ROOT_KEY_FD_ENV, None)
    secrets_fd_value = os.environ.pop(_SECRETS_FD_ENV, None)
    inherited_fds: list[int] = []
    parents: dict[str, Connection] = {}
    children: dict[str, Connection] = {}
    duplicate_handles: list[object] = []
    process: multiprocessing.Process | None = None
    attestor: object | None = None
    process_start_attempted = False
    transferred = False
    cleanup_owner = _AuthorityStartupCleanupOwner(
        connections=(children, parents),
        duplicate_handles=duplicate_handles,
        inherited_fds=inherited_fds,
    )
    try:
        root_fd = _parse_inherited_fd(
            root_fd_value,
            inherited_fds=inherited_fds,
        )
        secrets_fd = _parse_inherited_fd(
            secrets_fd_value,
            inherited_fds=inherited_fds,
        )
        try:
            os.fstat(root_fd)
            os.fstat(secrets_fd)
        except OSError:
            _security_error("authority_inherited_descriptors_invalid")
        if root_fd == secrets_fd:
            _security_error("authority_inherited_descriptors_invalid")

        context = multiprocessing.get_context("spawn")
        from ns_runtime.authority_attestor import start_authority_attestor

        attestor = start_authority_attestor(realm="production")
        cleanup_owner.attestor = attestor
        for role in _ENDPOINT_ROLES:
            parent, child = context.Pipe(duplex=True)
            parents[role] = parent
            children[role] = child

        root_handle = DupFd(root_fd)
        duplicate_handles.append(root_handle)
        secrets_handle = DupFd(secrets_fd)
        duplicate_handles.append(secrets_handle)
        process = context.Process(
            target=_isolated_authority_bootstrap_entry,
            args=(
                children,
                root_handle,
                secrets_handle,
                attestor.public_key,
                attestor.instance_id,
            ),
            name="ns-runtime-authority-broker",
            daemon=False,
        )
        cleanup_owner.process = process
        process_start_attempted = True
        cleanup_owner.process_start_attempted = True
        process.start()
        # ``Process.start`` has transferred the duplicate handles through the
        # spawn reduction protocol. They must not be detached in this parent.
        duplicate_handles.clear()
        child_close_failure = _close_connections(children)
        fd_close_failure = _close_inherited_fds(inherited_fds)
        if child_close_failure is not None:
            raise child_close_failure
        if fd_close_failure is not None:
            raise fd_close_failure

        if (
            not parents["lifecycle"].poll(10.0)
            or not process.is_alive()
        ):
            _security_error("authority_broker_bootstrap_failed")
        try:
            custody = json.loads(
                parents["lifecycle"].recv_bytes(1024).decode("utf-8"),
            )
        except (EOFError, OSError, UnicodeError, ValueError):
            _security_error("authority_broker_bootstrap_failed")
        if custody != {"kind": "fd_custody", "version": 1}:
            _security_error("authority_broker_bootstrap_failed")
        if not process.is_alive():
            _security_error("authority_broker_bootstrap_failed")
        bootstrap = InheritedAuthorityBootstrap(
            connections=parents,
            process=process,
            attestor=attestor,
        )
        transferred = True
        cleanup_owner.process = None
        cleanup_owner.attestor = None
        return bootstrap
    finally:
        if not transferred:
            active_failure = sys.exc_info()[1]
            cleanup_failure: BaseException | None = None
            try:
                cleanup_owner.close()
            except BaseException as error:
                cleanup_failure = error
            _raise_startup_cleanup_failure(
                cleanup_owner,
                operation_failure=active_failure,
                cleanup_failure=cleanup_failure,
            )


def _isolated_authority_bootstrap_entry(
    connections: dict[str, Connection],
    root_key_handle: object,
    secrets_handle: object,
    attestor_public_key: bytes,
    attestor_instance_id: str,
) -> None:
    # This module has no runtime business imports.  The spawn child receives
    # the inherited descriptors first; only then does it import broker code.
    from ns_runtime.authority_broker import _authority_broker_process

    _authority_broker_process(
        connections,
        None,
        root_key_handle,
        secrets_handle,
        "production",
        b"",
        attestor_public_key,
        attestor_instance_id,
        300.0,
        30 * 24 * 60 * 60.0,
    )


def _close_pending(
    connections: dict[str, Connection],
    process: multiprocessing.Process,
) -> BaseException | None:
    failure = _close_connections(connections)
    return _prioritize_failure(
        failure,
        _reap_process(process, started=True),
    )


def _parse_inherited_fd(
    value: object,
    *,
    inherited_fds: list[int],
) -> int:
    if type(value) is not str or not value:
        _security_error("authority_inherited_descriptors_required")
    try:
        descriptor = int(value, 10)
    except (ValueError, UnicodeError):
        _security_error("authority_inherited_descriptors_invalid")
    inherited_fds.append(descriptor)
    return descriptor


def _close_connections(
    connections: dict[str, Connection],
) -> BaseException | None:
    failure: BaseException | None = None
    seen: set[int] = set()
    for role, connection in tuple(connections.items()):
        marker = id(connection)
        if marker in seen:
            del connections[role]
            continue
        seen.add(marker)
        try:
            connection.close()
        except BaseException as error:
            failure = _prioritize_failure(failure, error)
        else:
            del connections[role]
    return failure


def _close_inherited_fds(
    descriptors: list[int],
) -> BaseException | None:
    failure: BaseException | None = None
    seen: set[int] = set()
    pending: list[int] = []
    for descriptor in descriptors:
        if descriptor in seen:
            continue
        seen.add(descriptor)
        try:
            os.close(descriptor)
        except OSError:
            # A parsed but invalid descriptor still receives exactly one close
            # attempt; its EBADF is not allowed to hide the startup rejection.
            pass
        except BaseException as error:
            failure = _prioritize_failure(failure, error)
            pending.append(descriptor)
    descriptors[:] = pending
    return failure


def _close_duplicate_handles(handles: list[object]) -> BaseException | None:
    failure: BaseException | None = None
    pending: list[object] = []
    for handle in handles:
        if type(handle) is _PendingRawFdOwner:
            descriptor_owner = handle
        else:
            try:
                descriptor = handle.detach()
            except BaseException as error:
                failure = _prioritize_failure(failure, error)
                pending.append(handle)
                continue
            descriptor_owner = _PendingRawFdOwner(descriptor)
        try:
            os.close(descriptor_owner.descriptor)
        except BaseException as error:
            failure = _prioritize_failure(failure, error)
            pending.append(descriptor_owner)
    handles[:] = pending
    return failure


def _reap_process(
    process: multiprocessing.Process,
    *,
    started: bool,
) -> BaseException | None:
    failure: BaseException | None = None
    if not started:
        return None
    for operation, timeout in (
        ("join", 0.2),
        ("terminate", 2.0),
        ("kill", 2.0),
    ):
        try:
            if operation == "join":
                process.join(timeout=timeout)
            elif process.is_alive():
                getattr(process, operation)()
                process.join(timeout=timeout)
        except BaseException as error:
            failure = _prioritize_failure(failure, error)
    try:
        alive = process.is_alive()
    except BaseException as error:
        failure = _prioritize_failure(failure, error)
        alive = True
    if alive:
        failure = _prioritize_failure(
            failure,
            _cleanup_error("authority_broker_process_did_not_exit"),
        )
    return failure


def _cleanup_error(
    reason: str,
    *,
    owner: _AuthorityStartupCleanupOwner | None = None,
) -> NsRuntimeStartupSecurityError:
    details: dict[str, object] = {
        "component": "authority_broker_bootstrap",
        "reason": reason,
    }
    if owner is not None:
        details.update(owner.pending_facts())
    failure = NsRuntimeStartupSecurityError(
        "Runtime authority cleanup did not complete.",
        details=details,
    )
    if owner is not None:
        failure.cleanup_owner = owner  # type: ignore[attr-defined]
    return failure


def _prioritize_failure(
    current: BaseException | None,
    candidate: BaseException | None,
) -> BaseException | None:
    if candidate is None:
        return current
    if current is None:
        return candidate
    if isinstance(current, Exception) and not isinstance(candidate, Exception):
        return candidate
    if (
        isinstance(current, Exception)
        and isinstance(candidate, NsRuntimeStartupSecurityError)
        and candidate.details.get("reason") in {
            "authority_broker_process_did_not_exit",
            "authority_startup_cleanup_incomplete",
        }
    ):
        return candidate
    return current


def _security_error(reason: str) -> None:
    raise NsRuntimeStartupSecurityError(
        "Runtime authority deployment material is unavailable.",
        details={
            "component": "authority_broker_bootstrap",
            "reason": reason,
        },
    )


__all__ = (
    "InheritedAuthorityBootstrap",
    "load_inherited_authority_bootstrap",
)
