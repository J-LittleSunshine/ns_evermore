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
        self._connections = None
        self._process = None
        self._attestor = None
        try:
            return _complete_inherited_authority_broker_start(
                parents=connections,
                process=process,
                attestor=attestor,
                config=config,
                clock=clock,
            )
        except BaseException as operation_failure:
            cleanup_failure = _close_pending(connections, process)
            try:
                attestor.close()
            except BaseException as error:
                cleanup_failure = _prioritize_failure(
                    cleanup_failure,
                    error,
                )
            selected = _prioritize_failure(
                operation_failure,
                cleanup_failure,
            )
            if selected is not operation_failure:
                raise selected
            raise

    def close(self) -> None:
        connections = self._connections
        process = self._process
        attestor = self._attestor
        self._connections = None
        self._process = None
        self._attestor = None
        failure: BaseException | None = None
        if connections is not None and process is not None:
            failure = _close_pending(connections, process)
        if attestor is not None:
            try:
                attestor.close()
            except BaseException as error:
                failure = _prioritize_failure(failure, error)
        self._consumed = True
        if failure is not None:
            raise failure


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
        process_start_attempted = True
        process.start()
        # ``Process.start`` has transferred the duplicate handles through the
        # spawn reduction protocol. They must not be detached in this parent.
        duplicate_handles.clear()
        child_close_failure = _close_connections(children)
        children.clear()
        fd_close_failure = _close_inherited_fds(inherited_fds)
        inherited_fds.clear()
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
        return bootstrap
    finally:
        if not transferred:
            active_failure = sys.exc_info()[1]
            cleanup_failure = _close_connections(children)
            cleanup_failure = _prioritize_failure(
                cleanup_failure,
                _close_connections(parents),
            )
            if process is not None:
                cleanup_failure = _prioritize_failure(
                    cleanup_failure,
                    _reap_process(
                        process,
                        started=process_start_attempted,
                    ),
                )
            cleanup_failure = _prioritize_failure(
                cleanup_failure,
                _close_duplicate_handles(duplicate_handles),
            )
            cleanup_failure = _prioritize_failure(
                cleanup_failure,
                _close_inherited_fds(inherited_fds),
            )
            if attestor is not None:
                try:
                    attestor.close()
                except BaseException as error:
                    cleanup_failure = _prioritize_failure(
                        cleanup_failure,
                        error,
                    )
            selected = _prioritize_failure(
                active_failure,
                cleanup_failure,
            )
            if selected is cleanup_failure and cleanup_failure is not None:
                raise cleanup_failure


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
    for connection in connections.values():
        marker = id(connection)
        if marker in seen:
            continue
        seen.add(marker)
        try:
            connection.close()
        except BaseException as error:
            failure = _prioritize_failure(failure, error)
    return failure


def _close_inherited_fds(
    descriptors: list[int],
) -> BaseException | None:
    failure: BaseException | None = None
    seen: set[int] = set()
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
    return failure


def _close_duplicate_handles(handles: list[object]) -> BaseException | None:
    failure: BaseException | None = None
    for handle in handles:
        try:
            descriptor = handle.detach()
        except (OSError, EOFError, ValueError):
            continue
        except BaseException as error:
            failure = _prioritize_failure(failure, error)
            continue
        try:
            os.close(descriptor)
        except OSError:
            pass
        except BaseException as error:
            failure = _prioritize_failure(failure, error)
    return failure


def _reap_process(
    process: multiprocessing.Process,
    *,
    started: bool,
) -> BaseException | None:
    failure: BaseException | None = None
    if not started:
        return None
    try:
        process.join(timeout=0.2)
        if process.is_alive():
            process.terminate()
            process.join(timeout=2.0)
        if process.is_alive():
            process.kill()
            process.join(timeout=2.0)
    except BaseException as error:
        failure = _prioritize_failure(failure, error)
        # Continue each escalation independently when a fake or partially
        # started Process rejects one lifecycle operation.
        for operation in ("terminate", "kill"):
            try:
                if process.is_alive():
                    getattr(process, operation)()
                    process.join(timeout=2.0)
            except BaseException as cleanup_error:
                failure = _prioritize_failure(failure, cleanup_error)
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
