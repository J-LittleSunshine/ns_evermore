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


class InheritedAuthorityBootstrap:
    __slots__ = (
        "_connection", "_process", "_consumed",
    )

    def __init__(
        self,
        *,
        connection: Connection,
        process: multiprocessing.Process,
    ) -> None:
        if (
            not isinstance(connection, Connection)
            or not process.is_alive()
        ):
            _security_error("invalid_inherited_authority_material")
        self._connection = connection
        self._process = process
        self._consumed = False

    def launch(self, *, config: object) -> object:
        if self._consumed:
            _security_error("authority_material_already_consumed")
        from ns_runtime.authority_broker import (
            AuthorityBrokerConfig,
            _complete_inherited_authority_broker_start,
        )

        if type(config) is not AuthorityBrokerConfig:
            _security_error("invalid_authority_broker_config")
        self._consumed = True
        connection = self._connection
        process = self._process
        self._connection = None
        self._process = None
        try:
            return _complete_inherited_authority_broker_start(
                parent=connection,
                process=process,
                config=config,
            )
        except BaseException:
            _close_pending(connection, process)
            raise

    def close(self) -> None:
        connection = self._connection
        process = self._process
        self._connection = None
        self._process = None
        if connection is not None and process is not None:
            _close_pending(connection, process)
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
    parent, child = context.Pipe(duplex=True)
    process = context.Process(
        target=_isolated_authority_bootstrap_entry,
        args=(child, DupFd(root_fd), DupFd(secrets_fd)),
        name="ns-runtime-authority-broker",
        daemon=False,
    )
    try:
        process.start()
    finally:
        child.close()
        for fd in (root_fd, secrets_fd):
            try:
                os.close(fd)
            except OSError:
                pass
    if (
        not parent.poll(10.0)
        or not process.is_alive()
    ):
        _close_pending(parent, process)
        _security_error("authority_broker_bootstrap_failed")
    try:
        custody = json.loads(parent.recv_bytes(1024).decode("utf-8"))
    except (EOFError, OSError, UnicodeError, ValueError):
        _close_pending(parent, process)
        _security_error("authority_broker_bootstrap_failed")
    if custody != {"kind": "fd_custody", "version": 1}:
        _close_pending(parent, process)
        _security_error("authority_broker_bootstrap_failed")
    if not process.is_alive():
        parent.close()
        _security_error("authority_broker_bootstrap_failed")
    return InheritedAuthorityBootstrap(
        connection=parent,
        process=process,
    )


def _isolated_authority_bootstrap_entry(
    connection: Connection,
    root_key_handle: object,
    secrets_handle: object,
) -> None:
    # This module has no runtime business imports.  The spawn child receives
    # the inherited descriptors first; only then does it import broker code.
    from ns_runtime.authority_broker import _authority_broker_process

    _authority_broker_process(
        connection,
        None,
        root_key_handle,
        secrets_handle,
        "production",
        b"",
    )


def _close_pending(
    connection: Connection,
    process: multiprocessing.Process,
) -> None:
    try:
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
