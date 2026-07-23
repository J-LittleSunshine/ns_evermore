# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import importlib.util
import ssl
import unittest

from ns_runtime.transport import (
    TransportErrorKind,
    normalize_transport_exception,
)


class _HostileError(Exception):
    def __str__(self) -> str:
        raise AssertionError("exception str must not be called")

    def __repr__(self) -> str:
        raise AssertionError("exception repr must not be called")


class _ProcessExit(BaseException):
    pass


class TransportErrorNormalizationTestCase(unittest.TestCase):
    @unittest.skipUnless(
        importlib.util.find_spec("websockets") is not None,
        "runtime transport dependency isn't installed",
    )
    def test_library_failures_map_to_stable_safe_transport_errors(self) -> None:
        from websockets.exceptions import (
            ConnectionClosedError,
            ConnectionClosedOK,
            InvalidHandshake,
            PayloadTooBig,
        )
        from websockets.frames import Close

        cases = (
            (
                ConnectionClosedOK(Close(1000, "credential=secret"), None),
                "receive",
                TransportErrorKind.REMOTE_CLOSED,
                "RUNTIME_TRANSPORT_RECEIVE_FAILED",
                "remote_closed",
            ),
            (
                ConnectionClosedError(Close(1007, "token=secret"), None),
                "receive",
                TransportErrorKind.PROTOCOL_ERROR,
                "RUNTIME_TRANSPORT_RECEIVE_FAILED",
                "protocol_error",
            ),
            (
                PayloadTooBig(2, 1),
                "receive",
                TransportErrorKind.MESSAGE_TOO_LARGE,
                "RUNTIME_TRANSPORT_RECEIVE_FAILED",
                "message_too_large",
            ),
            (
                InvalidHandshake("query=secret"),
                "accept",
                TransportErrorKind.HANDSHAKE_FAILED,
                "RUNTIME_TRANSPORT_HANDSHAKE_FAILED",
                "handshake_failed",
            ),
            (
                ssl.SSLError("certificate secret"),
                "tls",
                TransportErrorKind.TLS_FAILED,
                "RUNTIME_TRANSPORT_HANDSHAKE_FAILED",
                "tls_failed",
            ),
            (
                OSError("127.0.0.1:secret-port"),
                "listen",
                TransportErrorKind.LISTENER_FAILED,
                "RUNTIME_TRANSPORT_HANDSHAKE_FAILED",
                "listener_failed",
            ),
            (
                asyncio.TimeoutError("secret timeout"),
                "send",
                TransportErrorKind.SEND_TIMEOUT,
                "RUNTIME_TRANSPORT_SEND_FAILED",
                "send_timeout",
            ),
            (
                RuntimeError("secret pong"),
                "keepalive",
                TransportErrorKind.KEEPALIVE_FAILED,
                "RUNTIME_TRANSPORT_STREAM_RESET",
                "keepalive_failed",
            ),
        )
        for error, operation, kind, code, reason in cases:
            with self.subTest(kind=kind.value):
                failure = normalize_transport_exception(
                    error,
                    operation=operation,
                )
                self.assertEqual(kind, failure.error.kind)
                self.assertEqual(code, failure.error.code)
                self.assertEqual(reason, failure.error.details["reason"])
                self.assertEqual(code, failure.exception.code)
                rendered = repr(failure)
                for secret in (
                    "credential=secret",
                    "token=secret",
                    "payload=secret",
                    "query=secret",
                    "certificate secret",
                    "secret-port",
                    "secret timeout",
                    "secret pong",
                ):
                    self.assertNotIn(secret, rendered)

    def test_unknown_exception_does_not_invoke_str_or_repr(self) -> None:
        failure = normalize_transport_exception(
            _HostileError(),
            operation="receive",
        )
        self.assertEqual(TransportErrorKind.RECEIVE_FAILED, failure.error.kind)
        self.assertEqual("read_failed", failure.error.details["reason"])

    def test_base_exception_preserves_process_semantics(self) -> None:
        original = _ProcessExit()
        with self.assertRaises(_ProcessExit) as raised:
            normalize_transport_exception(original, operation="receive")
        self.assertIs(original, raised.exception)
