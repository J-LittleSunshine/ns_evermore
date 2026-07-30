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
        except BaseException:
            _close_pending(connections, process)
            attestor.close()
            raise

    def close(self) -> None:
        connections = self._connections
        process = self._process
        attestor = self._attestor
        self._connections = None
        self._process = None
        self._attestor = None
        if connections is not None and process is not None:
            _close_pending(connections, process)
        if attestor is not None:
            attestor.close()
        self._consumed = True

    def __del__(self) -> None:
        self.close()


def load_inherited_authority_bootstrap() -> InheritedAuthorityBootstrap:
    """Move inherited secrets into a spawn child before business imports."""

    root_fd_value = os.environ.pop(_ROOT_KEY_FD_ENV, None)
    secrets_fd_value = os.environ.pop(_SECRETS_FD_ENV, None)
    if any(
        type(value) is not str or not value
        for value in (
            root_fd_value, secrets_fd_value,
        )
    ):
        _security_error("authority_inherited_descriptors_required")
    try:
        root_fd = int(root_fd_value, 10)
        secrets_fd = int(secrets_fd_value, 10)
    except (ValueError, UnicodeError):
        _security_error("authority_inherited_descriptors_invalid")
    os.fstat(root_fd)
    os.fstat(secrets_fd)
    if root_fd == secrets_fd:
        _security_error("authority_inherited_descriptors_invalid")
    context = multiprocessing.get_context("spawn")
    from ns_runtime.authority_attestor import start_authority_attestor

    attestor = start_authority_attestor(realm="production")
    pairs = {
        role: context.Pipe(duplex=True)
        for role in _ENDPOINT_ROLES
    }
    parents = {role: pair[0] for role, pair in pairs.items()}
    children = {role: pair[1] for role, pair in pairs.items()}
    process = context.Process(
        target=_isolated_authority_bootstrap_entry,
        args=(
            children,
            DupFd(root_fd),
            DupFd(secrets_fd),
            attestor.public_key,
            attestor.instance_id,
        ),
        name="ns-runtime-authority-broker",
        daemon=False,
    )
    try:
        process.start()
    finally:
        for child in children.values():
            child.close()
        for fd in (root_fd, secrets_fd):
            try:
                os.close(fd)
            except OSError:
                pass
    if (
        not parents["lifecycle"].poll(10.0)
        or not process.is_alive()
    ):
        _close_pending(parents, process)
        attestor.close()
        _security_error("authority_broker_bootstrap_failed")
    try:
        custody = json.loads(
            parents["lifecycle"].recv_bytes(1024).decode("utf-8"),
        )
    except (EOFError, OSError, UnicodeError, ValueError):
        _close_pending(parents, process)
        attestor.close()
        _security_error("authority_broker_bootstrap_failed")
    if custody != {"kind": "fd_custody", "version": 1}:
        _close_pending(parents, process)
        attestor.close()
        _security_error("authority_broker_bootstrap_failed")
    if not process.is_alive():
        for parent in parents.values():
            parent.close()
        attestor.close()
        _security_error("authority_broker_bootstrap_failed")
    return InheritedAuthorityBootstrap(
        connections=parents,
        process=process,
        attestor=attestor,
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
) -> None:
    try:
        for connection in connections.values():
            connection.close()
    except OSError:
        pass
    process.join(timeout=0.2)
    if process.is_alive():
        process.terminate()
        process.join(timeout=2.0)
    if process.is_alive():
        process.kill()
        process.join(timeout=2.0)


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
