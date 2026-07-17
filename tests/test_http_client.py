# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from typing import Any

import ns_common
import ns_common.http_client as http_client_module
from ns_common.exceptions import (
    NsDependencyError,
    NsStateError,
)
from ns_common.http_client import (
    NsAsyncHttpClient,
    NsHttpClientFactory,
    NsHttpClientOwner,
    NsHttpClientOwnerState,
    aclose_http_clients,
    get_async_http_client,
)


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
