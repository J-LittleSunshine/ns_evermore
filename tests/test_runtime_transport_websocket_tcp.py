# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import ssl
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeStartupSecurityError,
    NsRuntimeTransportHandshakeFailedError,
    NsRuntimeTransportReceiveFailedError,
)
from ns_common.time import SystemClock
from ns_runtime.transport import (
    TransportCloseReason,
    TransportIdentityFactory,
    TransportSessionState,
    WebSocketTcpAdapter,
    WebSocketTcpAdapterOptions,
)


class WebSocketTcpAdapterTestCase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._certificate_directory = tempfile.TemporaryDirectory()
        directory = Path(cls._certificate_directory.name)
        cls._certificate = directory / "loopback-cert.pem"
        cls._private_key = directory / "loopback-key.pem"
        completed = subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", str(cls._private_key),
                "-out", str(cls._certificate),
                "-days", "1", "-subj", "/CN=localhost",
                "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError("loopback TLS certificate generation failed")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._certificate_directory.cleanup()

    def _server_tls_context(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self._certificate, self._private_key)
        return context

    @staticmethod
    def _client_tls_context() -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    @staticmethod
    def _options(*, tls: ssl.SSLContext | None = None) -> WebSocketTcpAdapterOptions:
        return WebSocketTcpAdapterOptions(
            host="127.0.0.1",
            port=0,
            clock=SystemClock(),
            ssl_context=tls,
            environment="test",
            allow_plaintext_non_prod=tls is None,
            send_timeout_seconds=1,
            ping_timeout_seconds=1,
            close_timeout_seconds=1,
            adapter_shutdown_timeout_seconds=1,
        )

    def _adapter(self, options: WebSocketTcpAdapterOptions) -> WebSocketTcpAdapter:
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.addAsyncCleanup(supervisor.shutdown)
        return WebSocketTcpAdapter(
            options=options,
            task_supervisor=supervisor,
            identity_factory=TransportIdentityFactory(),
        )

    async def test_plaintext_loopback_text_send_receive_ping_and_idempotent_close(
        self,
    ) -> None:
        from websockets.asyncio.client import connect

        adapter = self._adapter(self._options())
        await adapter.start()
        self.addAsyncCleanup(adapter.close)
        self.assertTrue(adapter.accepting)
        self.assertIsNotNone(adapter.bound_port)

        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            session = await asyncio.wait_for(adapter.accept(), timeout=1)
            self.assertEqual(TransportSessionState.HANDSHAKING, session.state)
            self.assertTrue(
                session.identity.transport_connection_id.startswith(
                    "transport_connection_",
                ),
            )
            self.assertFalse(session.diagnostic_summary.tls)
            self.assertNotIn("127.0.0.1", repr(session.diagnostic_summary))
            await client.send("client-to-runtime")
            inbound = await asyncio.wait_for(session.receive(), timeout=1)
            self.assertEqual("client-to-runtime", inbound.text)

            await session.send("runtime-to-client")
            self.assertEqual(
                "runtime-to-client",
                await asyncio.wait_for(client.recv(), timeout=1),
            )
            await session.ping()
            first_close = await session.close()
            second_close = await session.close()
            self.assertIs(first_close, second_close)
            self.assertEqual(TransportCloseReason.NORMAL, first_close.reason)
            self.assertEqual(TransportSessionState.CLOSED, session.state)

        await adapter.close()
        await adapter.close()
        self.assertFalse(adapter.accepting)

    async def test_tls_loopback_delivers_complete_text_messages(self) -> None:
        from websockets.asyncio.client import connect

        adapter = self._adapter(self._options(tls=self._server_tls_context()))
        await adapter.start()
        self.addAsyncCleanup(adapter.close)

        async with connect(
            f"wss://127.0.0.1:{adapter.bound_port}",
            ssl=self._client_tls_context(),
            proxy=None,
        ) as client:
            session = await asyncio.wait_for(adapter.accept(), timeout=1)
            self.assertTrue(session.diagnostic_summary.tls)
            await client.send("tls-complete-message")
            message = await asyncio.wait_for(session.receive(), timeout=1)
            self.assertEqual("tls-complete-message", message.text)
            self.assertEqual(
                len("tls-complete-message".encode("utf-8")),
                message.byte_size,
            )
            await session.send("tls-response")
            self.assertEqual("tls-response", await client.recv())
            await session.close()
        # asyncio's TLS transport completes its close callback on a later loop
        # turn after the WebSocket close handshake.
        await asyncio.sleep(0)

    async def test_adapter_shutdown_closes_active_session_and_io_tasks(self) -> None:
        from websockets.asyncio.client import connect

        adapter = self._adapter(self._options())
        await adapter.start()
        client = await connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        )
        self.addAsyncCleanup(client.close)
        session = await adapter.accept()
        await asyncio.wait_for(adapter.close(), timeout=1)
        await asyncio.wait_for(client.wait_closed(), timeout=1)

        self.assertFalse(adapter.accepting)
        self.assertEqual(TransportSessionState.CLOSED, session.state)
        self.assertEqual(
            TransportCloseReason.ADAPTER_SHUTDOWN,
            session.close_info.reason,
        )

    async def test_binary_message_is_rejected_with_unsupported_data_close(self) -> None:
        from websockets.asyncio.client import connect
        from websockets.exceptions import ConnectionClosedError

        adapter = self._adapter(self._options())
        await adapter.start()
        self.addAsyncCleanup(adapter.close)
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            session = await adapter.accept()
            await client.send(b"not-text")
            with self.assertRaises(NsRuntimeTransportReceiveFailedError) as raised:
                await session.receive()
            self.assertEqual(
                "binary_message_rejected",
                raised.exception.details["reason"],
            )
            with self.assertRaises(ConnectionClosedError) as client_closed:
                await client.recv()
            self.assertEqual(1003, client_closed.exception.rcvd.code)
            await session.wait_closed()  # type: ignore[attr-defined]
            self.assertEqual(
                TransportCloseReason.PROTOCOL_ERROR,
                session.close_info.reason,
            )

    async def test_invalid_utf8_text_frame_is_closed_by_protocol_layer(self) -> None:
        from websockets.asyncio.client import connect
        from websockets.exceptions import ConnectionClosedError

        adapter = self._adapter(self._options())
        await adapter.start()
        self.addAsyncCleanup(adapter.close)
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            session = await adapter.accept()
            await client.send(b"\xff", text=True)
            with self.assertRaises(NsRuntimeTransportReceiveFailedError) as raised:
                await session.receive()
            self.assertEqual("protocol_error", raised.exception.details["reason"])
            with self.assertRaises(ConnectionClosedError) as client_closed:
                await client.recv()
            self.assertEqual(1007, client_closed.exception.rcvd.code)

    async def test_message_over_adapter_limit_is_closed(self) -> None:
        from websockets.asyncio.client import connect
        from websockets.exceptions import ConnectionClosedError

        options = WebSocketTcpAdapterOptions(
            host="127.0.0.1",
            port=0,
            clock=SystemClock(),
            environment="test",
            allow_plaintext_non_prod=True,
            max_message_bytes=16,
            close_timeout_seconds=1,
            adapter_shutdown_timeout_seconds=1,
        )
        adapter = self._adapter(options)
        await adapter.start()
        self.addAsyncCleanup(adapter.close)
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
            max_size=None,
        ) as client:
            session = await adapter.accept()
            await client.send("x" * 17)
            with self.assertRaises(NsRuntimeTransportReceiveFailedError) as raised:
                await session.receive()
            self.assertEqual("message_too_large", raised.exception.details["reason"])
            with self.assertRaises(ConnectionClosedError) as client_closed:
                await client.recv()
            self.assertEqual(1009, client_closed.exception.rcvd.code)

    async def test_normal_remote_close_is_distinct_and_safe(self) -> None:
        from websockets.asyncio.client import connect

        adapter = self._adapter(self._options())
        await adapter.start()
        self.addAsyncCleanup(adapter.close)
        client = await connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        )
        session = await adapter.accept()
        await client.close(code=1000, reason="credential=must-not-leak")
        await asyncio.wait_for(session.wait_closed(), timeout=1)

        with self.assertRaises(NsRuntimeTransportReceiveFailedError) as raised:
            await session.receive()
        self.assertEqual("remote_closed", raised.exception.details["reason"])
        self.assertEqual(TransportCloseReason.REMOTE_CLOSED, session.close_info.reason)
        self.assertTrue(session.close_info.clean)
        self.assertNotIn("must-not-leak", repr(raised.exception))

    def test_production_plaintext_options_fail_closed(self) -> None:
        with self.assertRaises(NsRuntimeStartupSecurityError) as raised:
            WebSocketTcpAdapterOptions(
                host="127.0.0.1",
                port=0,
                clock=SystemClock(),
                environment="prod",
                allow_plaintext_non_prod=True,
            )
        self.assertEqual(
            "plaintext_transport_in_production",
            raised.exception.details["reason"],
        )

    async def test_listener_failure_is_normalized_without_socket_text(self) -> None:
        occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupied.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        self.addCleanup(occupied.close)
        port = occupied.getsockname()[1]
        adapter = self._adapter(WebSocketTcpAdapterOptions(
            host="127.0.0.1",
            port=port,
            clock=SystemClock(),
            environment="test",
            allow_plaintext_non_prod=True,
        ))

        with self.assertRaises(NsRuntimeTransportHandshakeFailedError) as raised:
            await adapter.start()
        self.assertEqual("listen", raised.exception.details["operation"])
        self.assertNotIn(str(port), repr(raised.exception.details))
