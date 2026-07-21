# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import os
import subprocess
import sys
import unittest
from datetime import datetime, timezone

from ns_common.exceptions import NsValidationError
from ns_runtime.transport import (
    TransportAdapter,
    TransportCapabilities,
    TransportCapability,
    TransportClose,
    TransportCloseInitiator,
    TransportCloseReason,
    TransportError,
    TransportErrorKind,
    TransportMessage,
    TransportSession,
    TransportSessionState,
    WEBSOCKET_TCP_CAPABILITIES,
    WEBSOCKET_TCP_TRANSPORT_TYPE,
)


class TransportContractsTestCase(unittest.TestCase):
    def test_websocket_tcp_declares_only_real_capabilities(self) -> None:
        self.assertEqual("websocket_tcp", WEBSOCKET_TCP_TRANSPORT_TYPE)
        self.assertEqual(
            {
                TransportCapability.RELIABLE_ORDERED_MESSAGES,
                TransportCapability.TRANSPORT_FLOW_CONTROL,
                TransportCapability.NATIVE_KEEPALIVE,
            },
            set(WEBSOCKET_TCP_CAPABILITIES.supported),
        )
        for unsupported in (
            TransportCapability.RELIABLE_BIDIRECTIONAL_STREAMS,
            TransportCapability.RELIABLE_UNIDIRECTIONAL_STREAMS,
            TransportCapability.UNRELIABLE_DATAGRAMS,
            TransportCapability.STREAM_MULTIPLEXING,
            TransportCapability.CONNECTION_PATH_MIGRATION,
            TransportCapability.PER_STREAM_FLOW_CONTROL,
            TransportCapability.ZERO_RTT,
            TransportCapability.TRANSPORT_RESUME,
        ):
            with self.subTest(capability=unsupported.value):
                self.assertFalse(WEBSOCKET_TCP_CAPABILITIES.supports(unsupported))

    def test_contract_facade_does_not_load_websockets_dependency(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = "src"
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import ns_runtime.transport; "
                "assert not any(name == 'websockets' or name.startswith('websockets.') "
                "for name in sys.modules)",
            ],
            cwd=os.getcwd(),
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_contracts_are_abstract_and_do_not_expose_websocket_types(self) -> None:
        self.assertTrue(inspect.isabstract(TransportAdapter))
        self.assertTrue(inspect.isabstract(TransportSession))
        annotations = repr(inspect.get_annotations(TransportSession.send))
        self.assertNotIn("websocket", annotations.casefold())
        self.assertEqual(
            {"text", "return"},
            set(inspect.get_annotations(TransportSession.send)),
        )

    def test_capability_set_is_frozen_and_rejects_untrusted_values(self) -> None:
        capabilities = TransportCapabilities(frozenset({
            TransportCapability.RELIABLE_ORDERED_MESSAGES,
        }))
        self.assertTrue(capabilities.supports(
            TransportCapability.RELIABLE_ORDERED_MESSAGES,
        ))
        self.assertFalse(capabilities.supports(TransportCapability.ZERO_RTT))
        with self.assertRaises(NsValidationError):
            TransportCapabilities(frozenset({"zero_rtt"}))  # type: ignore[arg-type]
        with self.assertRaises(NsValidationError):
            capabilities.supports("zero_rtt")  # type: ignore[arg-type]

    def test_message_is_complete_utf8_text_and_repr_omits_content(self) -> None:
        message = TransportMessage(
            text="完整消息",
            byte_size=len("完整消息".encode("utf-8")),
            received_at=datetime.now(timezone.utc),
        )
        self.assertEqual("完整消息", message.text)
        self.assertNotIn("完整消息", repr(message))
        with self.assertRaises(NsValidationError):
            TransportMessage(
                text="x",
                byte_size=2,
                received_at=datetime.now(timezone.utc),
            )
        with self.assertRaises(NsValidationError):
            TransportMessage(
                text=b"x",  # type: ignore[arg-type]
                byte_size=1,
                received_at=datetime.now(timezone.utc),
            )

    def test_close_and_initial_state_have_no_active_business_state(self) -> None:
        self.assertEqual(
            {"handshaking", "closing", "closed"},
            {item.value for item in TransportSessionState},
        )
        close = TransportClose(
            reason=TransportCloseReason.NORMAL,
            initiator=TransportCloseInitiator.LOCAL,
            clean=True,
            protocol_code=1000,
        )
        self.assertTrue(close.clean)
        with self.assertRaises(NsValidationError):
            TransportClose(
                reason=TransportCloseReason.NORMAL,
                initiator=TransportCloseInitiator.LOCAL,
                clean=True,
                protocol_code=100_000,
            )

    def test_transport_error_only_accepts_safe_low_cardinality_details(self) -> None:
        error = TransportError(
            kind=TransportErrorKind.WRITE_QUEUE_FULL,
            code="RUNTIME_TRANSPORT_FLOW_CONTROL_BLOCKED",
            operation="send",
            retryable=True,
            details={"reason": "write_queue_full", "transport_type": "websocket_tcp"},
        )
        self.assertEqual("write_queue_full", error.details["reason"])
        with self.assertRaises(TypeError):
            error.details["reason"] = "changed"  # type: ignore[index]
        for unsafe_key in ("peer", "path", "session_id", "exception"):
            with self.subTest(unsafe_key=unsafe_key), self.assertRaises(NsValidationError):
                TransportError(
                    kind=TransportErrorKind.SEND_FAILED,
                    code="RUNTIME_TRANSPORT_SEND_FAILED",
                    operation="send",
                    details={unsafe_key: "secret"},
                )
