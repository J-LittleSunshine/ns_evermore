# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path
from typing import Any

import httpx

import ns_common
import ns_common.http_client as http_client_module
from ns_common.exceptions import (
    NsDependencyError,
    NsStateError,
    NsValidationError,
)
from ns_common.http_client import (
    NsAsyncHttpClient,
    NsHttpClientFactory,
    NsHttpClientOwner,
    NsHttpClientOwnerState,
    NsHttpResponse,
    NsHttpResponseSanitizer,
    aclose_http_clients,
    get_async_http_client,
)
from ns_common.security import REDACTED


class _CapturingLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def info(
            self,
            message: str,
            *,
            extra: dict[str, object],
    ) -> None:
        self.events.append((message, extra))


class _StubAsyncHttpxClient:
    def __init__(self, outcome: httpx.Response | BaseException) -> None:
        self.outcome = outcome
        self.calls: list[tuple[str, str, dict[str, object]]] = []
        self.closed = False

    async def request(
            self,
            method: str,
            url: str,
            **kwargs: object,
    ) -> httpx.Response:
        self.calls.append((method, url, dict(kwargs)))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome

    async def aclose(self) -> None:
        self.closed = True


class _LifecycleHttpClient(NsAsyncHttpClient):
    def __init__(
            self,
            *,
            close_events: list[str],
            close_started: asyncio.Event | None = None,
            close_release: asyncio.Event | None = None,
            fail_close: bool = False,
            **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.close_events = close_events
        self.close_started = close_started
        self.close_release = close_release
        self.fail_close = fail_close
        self.close_calls = 0

    async def aclose(self) -> None:
        if self.is_closed:
            return

        self.close_calls += 1
        self.close_events.append(self.name)
        if self.close_started is not None:
            self.close_started.set()
        if self.close_release is not None:
            await self.close_release.wait()
        await super().aclose()
        if self.fail_close:
            raise RuntimeError("private close failure detail")


class _LifecycleHttpClientFactory(NsHttpClientFactory):
    def __init__(
            self,
            *,
            close_events: list[str],
            blocking_name: str | None = None,
            close_started: asyncio.Event | None = None,
            close_release: asyncio.Event | None = None,
            failing_names: frozenset[str] = frozenset(),
    ) -> None:
        self.close_events = close_events
        self.blocking_name = blocking_name
        self.close_started = close_started
        self.close_release = close_release
        self.failing_names = failing_names

    def create(self, **kwargs: Any) -> NsAsyncHttpClient:
        name = kwargs["name"]
        is_blocking = name == self.blocking_name
        kwargs.setdefault("verify", False)
        return _LifecycleHttpClient(
            close_events=self.close_events,
            close_started=self.close_started if is_blocking else None,
            close_release=self.close_release if is_blocking else None,
            fail_close=name in self.failing_names,
            **kwargs,
        )


class NsHttpClientFactoryTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_factory_creates_independent_caller_owned_clients(self) -> None:
        factory = NsHttpClientFactory()
        first = factory.create(
            name="iam",
            base_url="https://iam.internal/",
            timeout_seconds=3,
            default_headers={"X-Service": "runtime"},
            verify=False,
        )
        second = factory.create(
            name="iam",
            base_url="https://iam.internal/",
            timeout_seconds=3,
            verify=False,
        )
        self.addAsyncCleanup(first.aclose)
        self.addAsyncCleanup(second.aclose)

        self.assertIsNot(first, second)
        self.assertEqual("https://iam.internal", first.base_url)
        self.assertEqual(3, first.timeout_seconds)
        self.assertEqual({"X-Service": "runtime"}, first.default_headers)
        self.assertFalse(first.is_closed)
        self.assertFalse(second.is_closed)

        await first.aclose()
        self.assertTrue(first.is_closed)
        self.assertFalse(second.is_closed)

    async def test_owner_context_closes_clients_in_reverse_order_once(self) -> None:
        close_events: list[str] = []
        factory = _LifecycleHttpClientFactory(close_events=close_events)
        owner = NsHttpClientOwner(factory=factory)

        async with owner as entered_owner:
            first = owner.create(name="first")
            second = owner.create(name="second")
            self.assertIs(owner, entered_owner)
            self.assertIs(NsHttpClientOwnerState.OPEN, owner.state)
            self.assertEqual((first, second), owner.clients)
            self.assertIs(factory, owner.factory)

        self.assertEqual(["second", "first"], close_events)
        self.assertTrue(first.is_closed)
        self.assertTrue(second.is_closed)
        self.assertEqual((), owner.clients)
        self.assertIs(NsHttpClientOwnerState.CLOSED, owner.state)

        await owner.aclose()
        self.assertEqual(["second", "first"], close_events)
        with self.assertRaises(NsStateError) as context:
            owner.create(name="after-close")
        self.assertEqual("closed", context.exception.details["owner_state"])
        self.assertEqual("create_http_client", context.exception.details["action"])

    async def test_owner_close_is_concurrent_and_rejects_new_clients(self) -> None:
        close_events: list[str] = []
        close_started = asyncio.Event()
        close_release = asyncio.Event()
        owner = NsHttpClientOwner(
            factory=_LifecycleHttpClientFactory(
                close_events=close_events,
                blocking_name="blocking",
                close_started=close_started,
                close_release=close_release,
            ),
        )
        client = owner.create(name="blocking")

        first_close = asyncio.create_task(owner.aclose())
        await close_started.wait()
        self.assertIs(NsHttpClientOwnerState.CLOSING, owner.state)
        with self.assertRaises(NsStateError) as context:
            owner.create(name="too-late")
        self.assertEqual("closing", context.exception.details["owner_state"])

        second_close = asyncio.create_task(owner.aclose())
        close_release.set()
        await asyncio.gather(first_close, second_close)

        self.assertEqual(1, client.close_calls)
        self.assertEqual(["blocking"], close_events)
        self.assertIs(NsHttpClientOwnerState.CLOSED, owner.state)

    async def test_cancelled_close_can_be_resumed_without_losing_ownership(self) -> None:
        close_events: list[str] = []
        close_started = asyncio.Event()
        close_release = asyncio.Event()
        owner = NsHttpClientOwner(
            factory=_LifecycleHttpClientFactory(
                close_events=close_events,
                blocking_name="blocking",
                close_started=close_started,
                close_release=close_release,
            ),
        )
        client = owner.create(name="blocking")

        close_task = asyncio.create_task(owner.aclose())
        await close_started.wait()
        close_task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await close_task

        self.assertIs(NsHttpClientOwnerState.CLOSING, owner.state)
        self.assertEqual((client,), owner.clients)
        self.assertFalse(client.is_closed)

        close_release.set()
        await owner.aclose()
        self.assertEqual(2, client.close_calls)
        self.assertTrue(client.is_closed)
        self.assertIs(NsHttpClientOwnerState.CLOSED, owner.state)

    async def test_owner_attempts_every_close_and_reports_safe_failures(self) -> None:
        close_events: list[str] = []
        owner = NsHttpClientOwner(
            factory=_LifecycleHttpClientFactory(
                close_events=close_events,
                failing_names=frozenset({"failing"}),
            ),
        )
        first = owner.create(name="first")
        failing = owner.create(name="failing")

        with self.assertRaises(NsDependencyError) as context:
            await owner.aclose()

        self.assertEqual(["failing", "first"], close_events)
        self.assertTrue(first.is_closed)
        self.assertTrue(failing.is_closed)
        self.assertIs(NsHttpClientOwnerState.CLOSING, owner.state)
        self.assertEqual((failing,), owner.clients)
        self.assertEqual(
            [{"client": "failing", "error_type": "RuntimeError"}],
            context.exception.details["failed_clients"],
        )
        self.assertNotIn("private close failure detail", str(context.exception))

        await owner.aclose()
        self.assertIs(NsHttpClientOwnerState.CLOSED, owner.state)
        self.assertEqual((), owner.clients)


class NsHttpResponseSecurityTestCase(unittest.IsolatedAsyncioTestCase):

    async def _replace_httpx_client(
            self,
            client: NsAsyncHttpClient,
            replacement: _StubAsyncHttpxClient,
    ) -> None:
        await client._client.aclose()
        client._client = replacement  # type: ignore[assignment]

    async def test_default_error_summary_never_copies_response_body(self) -> None:
        body_secret = "opaque-iam-body-secret-7d494ef9"
        url_secret = "iam-url-secret-265f27a1"
        response = httpx.Response(
            503,
            headers={"Content-Type": "text/plain; charset=utf-8"},
            text=f"upstream unavailable: {body_secret}",
            request=httpx.Request(
                "GET",
                f"https://iam.internal/introspect?access_token={url_secret}",
            ),
        )
        stub = _StubAsyncHttpxClient(response)
        client = NsAsyncHttpClient(
            name="iam-default-summary",
            base_url="https://iam.internal",
            verify=False,
        )
        self.addAsyncCleanup(client.aclose)
        await self._replace_httpx_client(client, stub)
        logger = _CapturingLogger()
        client._logger = logger  # type: ignore[assignment]

        with self.assertRaises(NsDependencyError) as context:
            await client.get("/introspect")

        details = context.exception.details
        self.assertNotIn("body_preview", details)
        self.assertEqual(
            {
                "present": True,
                "text_length": len(response.text),
                "body_format": "text",
            },
            details["body_summary"],
        )
        self.assertNotIn(body_secret, repr(details))
        self.assertNotIn(body_secret, str(context.exception))
        self.assertNotIn(url_secret, repr(details))
        self.assertNotIn(url_secret, repr(logger.events))
        self.assertEqual(1, len(logger.events))

    async def test_iam_error_uses_structured_response_sanitizer(self) -> None:
        bearer_token = "iam-bearer-8b72d0f0"
        access_token = "body-access-9010dd0a"
        refresh_token = "body-refresh-4f0d1770"
        client_secret = "body-client-secret-d1ee9f16"
        opaque_body_secret = "opaque-body-only-91fc7142"
        signed_url_secret = "signed-url-token-6b4694cc"
        body = json.dumps({
            "error": "invalid_token",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "client_secret": client_secret,
            "opaque": opaque_body_secret,
            "help_url": (
                "https://iam.internal/help"
                f"?token={signed_url_secret}"
            ),
        })

        def summarize(response: NsHttpResponse) -> dict[str, object]:
            payload = json.loads(response.text)
            response.status_code = 200
            response.safe_url = payload["help_url"]
            response.headers["X-Reflected-Secret"] = payload["access_token"]
            return {
                "error_code": payload["error"],
                "access_token": payload["access_token"],
                "nested": {
                    "refresh_token": payload["refresh_token"],
                    "client_secret": payload["client_secret"],
                },
                "help_url": payload["help_url"],
            }

        response = httpx.Response(
            401,
            headers={"Content-Type": "application/json"},
            text=body,
            request=httpx.Request(
                "POST",
                (
                    "https://iam.internal/reflected/"
                    f"{bearer_token}?request_id=req-1"
                ),
            ),
        )
        stub = _StubAsyncHttpxClient(response)
        owner = NsHttpClientOwner()
        self.addAsyncCleanup(owner.aclose)
        client = owner.create(
            name="iam-custom-summary",
            base_url="https://iam.internal",
            verify=False,
            response_sanitizer=summarize,
        )
        await self._replace_httpx_client(client, stub)
        logger = _CapturingLogger()
        client._logger = logger  # type: ignore[assignment]

        with self.assertRaises(NsDependencyError) as context:
            await client.post(
                "/introspect",
                params={"tenant_id": "tenant-1"},
                bearer_token=bearer_token,
                json_data={"resource": "document"},
            )

        self.assertIs(summarize, client.response_sanitizer)
        self.assertEqual(1, len(stub.calls))
        _, request_url, request_kwargs = stub.calls[0]
        self.assertNotIn(bearer_token, request_url)
        self.assertNotIn(bearer_token, repr(request_kwargs["params"]))
        self.assertEqual(
            f"Bearer {bearer_token}",
            request_kwargs["headers"]["Authorization"],  # type: ignore[index]
        )

        summary = context.exception.details["body_summary"]
        self.assertEqual(401, context.exception.details["status_code"])
        self.assertEqual(REDACTED, context.exception.details["url"])
        self.assertEqual("applied", summary["response_sanitizer"])
        sanitized = summary["sanitized"]
        self.assertEqual("invalid_token", sanitized["error_code"])
        self.assertEqual(REDACTED, sanitized["access_token"])
        self.assertEqual(REDACTED, sanitized["nested"]["refresh_token"])
        self.assertEqual(REDACTED, sanitized["nested"]["client_secret"])

        diagnostic_text = repr({
            "error": context.exception.to_dict(),
            "logs": logger.events,
        })
        for secret in (
            bearer_token,
            access_token,
            refresh_token,
            client_secret,
            opaque_body_secret,
            signed_url_secret,
        ):
            with self.subTest(secret=secret):
                self.assertNotIn(secret, diagnostic_text)

    async def test_response_sanitizer_failure_is_fail_closed(self) -> None:
        body_secret = "opaque-failed-sanitizer-body-dd845661"
        callback_secret = "opaque-callback-failure-6181301a"

        def broken_sanitizer(_: NsHttpResponse) -> dict[str, object]:
            raise RuntimeError(callback_secret)

        response = httpx.Response(
            500,
            text=body_secret,
            request=httpx.Request("GET", "https://iam.internal/failure"),
        )
        stub = _StubAsyncHttpxClient(response)
        client = NsHttpClientFactory().create(
            name="iam-failed-summary",
            base_url="https://iam.internal",
            verify=False,
            response_sanitizer=broken_sanitizer,
        )
        self.addAsyncCleanup(client.aclose)
        await self._replace_httpx_client(client, stub)

        with self.assertRaises(NsDependencyError) as context:
            await client.get("/failure")

        summary = context.exception.details["body_summary"]
        self.assertEqual("failed_closed", summary["response_sanitizer"])
        self.assertNotIn("sanitized", summary)
        self.assertNotIn(body_secret, str(context.exception))
        self.assertNotIn(callback_secret, str(context.exception))

    async def test_request_failures_drop_raw_transport_error_text(self) -> None:
        transport_secret = "transport-error-secret-b82b0c01"
        url_secret = "query-secret-94cdf137"
        request_url = (
            "https://iam.internal/introspect"
            f"?access_token={url_secret}"
        )
        failures = (
            httpx.ReadTimeout(
                f"timeout contained {transport_secret}",
                request=httpx.Request("GET", request_url),
            ),
            httpx.ConnectError(
                f"connect contained {transport_secret}",
                request=httpx.Request("GET", request_url),
            ),
        )

        for index, failure in enumerate(failures):
            with self.subTest(failure=type(failure).__name__):
                client = NsAsyncHttpClient(
                    name=f"iam-request-failure-{index}",
                    base_url="https://iam.internal",
                    verify=False,
                )
                self.addAsyncCleanup(client.aclose)
                await self._replace_httpx_client(
                    client,
                    _StubAsyncHttpxClient(failure),
                )

                with self.assertRaises(NsDependencyError) as context:
                    await client.get(
                        f"/introspect?access_token={url_secret}",
                    )

                details = context.exception.details
                self.assertNotIn("error", details)
                self.assertNotIn(transport_secret, repr(details))
                self.assertNotIn(url_secret, repr(details))
                self.assertNotIn(transport_secret, str(context.exception))
                self.assertNotIn(url_secret, str(context.exception))
                self.assertIsNone(context.exception.__context__)

    async def test_bearer_token_is_rejected_before_entering_url(self) -> None:
        bearer_token = "iam-bearer-url-guard-1fac2203"
        response = httpx.Response(
            200,
            json={"ok": True},
            request=httpx.Request("GET", "https://iam.internal/unused"),
        )
        stub = _StubAsyncHttpxClient(response)
        client = NsAsyncHttpClient(
            name="iam-token-url-guard",
            base_url="https://iam.internal",
            verify=False,
        )
        self.addAsyncCleanup(client.aclose)
        await self._replace_httpx_client(client, stub)

        guarded_requests = (
            {
                "url": f"/introspect?access_token={bearer_token}",
                "params": None,
            },
            {
                "url": "/introspect",
                "params": {"access_token": bearer_token},
            },
        )
        for request in guarded_requests:
            with self.subTest(request=request):
                with self.assertRaises(NsValidationError) as context:
                    await client.get(
                        request["url"],
                        params=request["params"],
                        bearer_token=bearer_token,
                    )
                self.assertNotIn(bearer_token, str(context.exception))
                self.assertEqual(
                    "remove_bearer_token_from_url",
                    context.exception.details["action"],
                )

        self.assertEqual([], stub.calls)

    async def test_per_request_response_sanitizer_overrides_client_default(
            self,
    ) -> None:
        response = httpx.Response(
            200,
            text="not-json-but-successful",
            request=httpx.Request("GET", "https://iam.internal/status"),
        )
        client = NsAsyncHttpClient(
            name="iam-request-summary-override",
            base_url="https://iam.internal",
            verify=False,
            response_sanitizer=lambda _: {"source": "client"},
        )
        self.addAsyncCleanup(client.aclose)
        await self._replace_httpx_client(
            client,
            _StubAsyncHttpxClient(response),
        )

        result = await client.get(
            "/status",
            response_sanitizer=lambda _: {"source": "request"},
        )

        self.assertEqual(
            "request",
            result.safe_body_summary["sanitized"]["source"],
        )

    async def test_invalid_json_error_uses_safe_summary_and_url(self) -> None:
        body_secret = "invalid-json-body-secret-23239e66"
        url_secret = "invalid-json-url-secret-29d779b2"
        response = NsHttpResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            text=f"{{invalid-json-{body_secret}",
            url=(
                "https://iam.internal/result"
                f"?access_token={url_secret}"
            ),
            method="GET",
        )

        with self.assertRaises(NsDependencyError) as context:
            response.json()

        details = context.exception.details
        self.assertNotIn("body_preview", details)
        self.assertEqual(
            {
                "present": True,
                "text_length": len(response.text),
                "body_format": "json",
            },
            details["body_summary"],
        )
        self.assertNotIn(body_secret, repr(details))
        self.assertNotIn(url_secret, repr(details))
        self.assertIsNone(context.exception.__context__)


class NsHttpClientCompatibilityTestCase(unittest.IsolatedAsyncioTestCase):

    async def asyncTearDown(self) -> None:
        await aclose_http_clients()

    async def test_explicit_owner_is_isolated_from_compatibility_map(self) -> None:
        compatibility_client = get_async_http_client(name="shared-name", verify=False)
        self.assertIs(
            compatibility_client,
            get_async_http_client(
                name="shared-name",
                base_url="https://ignored-after-first-create.example",
            ),
        )

        owner = NsHttpClientOwner()
        explicit_client = owner.create(name="shared-name", verify=False)
        self.assertIsNot(compatibility_client, explicit_client)

        await owner.aclose()
        self.assertTrue(explicit_client.is_closed)
        self.assertFalse(compatibility_client.is_closed)

        await aclose_http_clients()
        self.assertTrue(compatibility_client.is_closed)
        replacement = get_async_http_client(name="shared-name", verify=False)
        self.assertIsNot(compatibility_client, replacement)
        self.assertFalse(replacement.is_closed)


class NsHttpClientPublicContractTestCase(unittest.TestCase):

    def test_facades_export_authoritative_factory_and_owner_types(self) -> None:
        expected_exports = {
            "NsAsyncHttpClient": NsAsyncHttpClient,
            "NsHttpClientFactory": NsHttpClientFactory,
            "NsHttpClientOwner": NsHttpClientOwner,
            "NsHttpClientOwnerState": NsHttpClientOwnerState,
            "NsHttpResponse": NsHttpResponse,
            "NsHttpResponseSanitizer": NsHttpResponseSanitizer,
        }

        for name, expected in expected_exports.items():
            with self.subTest(name=name):
                self.assertIn(name, http_client_module.__all__)
                self.assertIn(name, ns_common.__all__)
                self.assertIs(expected, getattr(http_client_module, name))
                self.assertIs(expected, getattr(ns_common, name))

        runtime_root = Path(__file__).resolve().parents[1] / "src" / "ns_runtime"
        forbidden_global_getter_users = [
            str(path.relative_to(runtime_root))
            for path in runtime_root.rglob("*.py")
            if "get_async_http_client" in path.read_text(encoding="utf-8")
        ] if runtime_root.is_dir() else []
        self.assertEqual([], forbidden_global_getter_users)


if __name__ == "__main__":
    unittest.main()
