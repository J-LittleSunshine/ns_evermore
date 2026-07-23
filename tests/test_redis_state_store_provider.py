# -*- coding: utf-8 -*-
"""Trusted-boundary and lifecycle tests for P10-FIX-02."""

from __future__ import annotations

import os
from dataclasses import replace
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ns_common.config import NsConfig
from ns_common.exceptions import (
    NsConfigError,
    NsRuntimeStateStoreUnavailableError,
    NsValidationError,
)
from ns_common.state_store import (
    EnvironmentStateStorePassword,
    FileStateStorePassword,
    NoStateStorePassword,
    RedisStateStoreOptions,
    RedisValkeyStateStore,
    StateStoreCapabilities,
    StateStoreLifecycleState,
    StateStorePasswordSource,
    create_state_store_provider,
    password_source_from_reference,
)
from ns_common.time import ControlledClock


class RedisStateStoreProviderBoundaryTestCase(unittest.TestCase):

    def _options(self, **overrides: object) -> RedisStateStoreOptions:
        values = {
            "backend": "redis",
            "endpoint": "redis://127.0.0.1:6379/0",
            "username": "",
            "password_source": NoStateStorePassword(),
            "namespace": "ns_runtime_provider_test",
            "operation_timeout_seconds": 1.0,
        }
        values.update(overrides)
        return RedisStateStoreOptions(**values)  # type: ignore[arg-type]

    def test_options_direct_construction_and_replace_reject_invalid_matrix(self) -> None:
        class TextSubclass(str):
            pass

        class FloatSubclass(float):
            pass

        matrix = (
            ("backend", None),
            ("backend", TextSubclass("redis")),
            ("backend", "Redis"),
            ("username", None),
            ("username", TextSubclass("default")),
            ("username", "x" * 129),
            ("username", "bad\0user"),
            ("username", "bad\ruser"),
            ("username", "bad\nuser"),
            ("operation_timeout_seconds", True),
            ("operation_timeout_seconds", 0),
            ("operation_timeout_seconds", -1),
            ("operation_timeout_seconds", math.nan),
            ("operation_timeout_seconds", math.inf),
            ("operation_timeout_seconds", -math.inf),
            ("operation_timeout_seconds", FloatSubclass(1.0)),
            ("endpoint", TextSubclass("redis://127.0.0.1:6379/0")),
            ("endpoint", " redis://127.0.0.1:6379/0"),
            ("endpoint", "redis://127.0.0.1:6379/not-a-db"),
            ("namespace", TextSubclass("ns_runtime")),
            ("namespace", "bad namespace"),
            ("password_source", object()),
        )
        valid = self._options()
        self.assertEqual("", valid.username)
        for field_name, invalid_value in matrix:
            with self.subTest(path="direct", field=field_name, value_type=type(invalid_value).__name__):
                with self.assertRaises(NsValidationError) as caught:
                    self._options(**{field_name: invalid_value})
                self.assertEqual(f"options.{field_name}", caught.exception.details["field"])
            with self.subTest(path="replace", field=field_name, value_type=type(invalid_value).__name__):
                with self.assertRaises(NsValidationError) as caught:
                    replace(valid, **{field_name: invalid_value})
                self.assertEqual(f"options.{field_name}", caught.exception.details["field"])

        with self.assertRaises(NsValidationError):
            EnvironmentStateStorePassword(
                variable_name=TextSubclass("NS_STATE_STORE_PASSWORD"),
            )
        with self.assertRaises(NsValidationError):
            password_source_from_reference(TextSubclass("none"))

    def test_typed_config_round_trip_and_factory_are_secret_free(self) -> None:
        variable = "NS_STATE_STORE_PROVIDER_TEST_PASSWORD"
        config = NsConfig.from_dict({
            "runtime": {
                "state_store": {
                    "backend": "redis",
                    "endpoint": "redis://127.0.0.1:6379/0",
                    "username": "runtime-user",
                    "password_source": f"env:{variable}",
                    "namespace": "ns_runtime_provider_test",
                    "operation_timeout_seconds": 2,
                },
            },
        })
        restored = NsConfig.from_dict(config.to_dict())
        self.assertEqual(config, restored)
        store = create_state_store_provider(
            config=restored.runtime.state_store,
            clock=ControlledClock(),
        )
        self.assertIsInstance(store, RedisValkeyStateStore)
        representation = repr(restored.runtime.state_store) + repr(store)
        self.assertNotIn("runtime-user", representation)
        self.assertNotIn(variable, representation)
        self.assertNotIn("127.0.0.1", representation)

    def test_url_userinfo_is_rejected_without_echoing_secret(self) -> None:
        secret = "must-never-be-rendered"
        with self.assertRaises(NsConfigError) as caught:
            NsConfig.from_dict({
                "runtime": {
                    "state_store": {
                        "backend": "redis",
                        "endpoint": (
                            "redis://runtime-user:" + secret
                            + "@127.0.0.1:6379/0"
                        ),
                    },
                },
            })
        self.assertNotIn(secret, str(caught.exception))
        self.assertNotIn(secret, repr(caught.exception))

    def test_environment_and_file_secret_sources_never_render_values(self) -> None:
        secret = "source-secret-must-remain-private"
        environment = EnvironmentStateStorePassword(
            variable_name="NS_STATE_STORE_TEST_SECRET",
            environ={"NS_STATE_STORE_TEST_SECRET": secret},
        )
        self.assertEqual(secret, environment.resolve())
        self.assertNotIn(secret, repr(environment))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state-store-password"
            path.write_text(secret + "\n", encoding="utf-8")
            source = FileStateStorePassword(path=path)
            self.assertEqual(secret, source.resolve())
            self.assertNotIn(secret, repr(source))

    def test_missing_environment_secret_is_typed_and_sanitized(self) -> None:
        variable = "NS_STATE_STORE_INTENTIONALLY_MISSING_SECRET"
        os.environ.pop(variable, None)
        source = EnvironmentStateStorePassword(variable_name=variable)
        with self.assertRaises(NsRuntimeStateStoreUnavailableError) as caught:
            source.resolve()
        self.assertNotIn(variable, str(caught.exception))

    def test_provider_import_is_cold_and_delivery_has_no_driver_dependency(self) -> None:
        script = (
            "import sys; import ns_common.state_store; "
            "assert 'redis' not in sys.modules; "
            "assert 'valkey' not in sys.modules"
        )
        completed = subprocess.run(
            (sys.executable, "-c", script),
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "PYTHONPATH": "src"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        delivery_root = Path(__file__).resolve().parents[1] / "src" / "ns_runtime" / "delivery"
        contents = "\n".join(
            path.read_text(encoding="utf-8")
            for path in delivery_root.glob("*.py")
        )
        self.assertNotIn("import redis", contents)
        self.assertNotIn("import valkey", contents)

    def test_provider_source_has_no_database_wide_cleanup_commands(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "src" / "ns_common" / "state_store" / "redis_provider.py"
        ).read_text(encoding="utf-8").casefold()
        self.assertNotIn("flushdb", source)
        self.assertNotIn("flushall", source)
        self.assertNotIn("keys *", source)

    def test_integration_server_uses_reserved_port_and_pid_ownership_gate(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "tests" / "test_redis_state_store_integration.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("def _free_port", source)
        self.assertIn("reserve_tcp_port()", source)
        self.assertIn('server_info["process_id"]', source)


class _ReturningPasswordSource(StateStorePasswordSource):
    def __init__(self, value: object) -> None:
        self.value = value

    def resolve(self) -> object:
        return self.value

    def __repr__(self) -> str:
        return "source-repr-must-not-leak"


class _RaisingPasswordSource(StateStorePasswordSource):
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def resolve(self) -> str:
        raise self.error


class _FakeResponseError(Exception):
    pass


class _FakeTimeoutError(Exception):
    pass


class _FakeRedisClient:
    def __init__(self, *, close_failure: BaseException | None = None) -> None:
        self.close_failure = close_failure

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        if self.close_failure is not None:
            raise self.close_failure


class _BoundaryProvider(RedisValkeyStateStore):
    def __init__(
        self,
        *,
        password_source: StateStorePasswordSource,
        client: _FakeRedisClient | None = None,
    ) -> None:
        self.fake_client = client or _FakeRedisClient()
        super().__init__(
            options=RedisStateStoreOptions(
                backend="redis",
                endpoint="redis://boundary.invalid:6379/0",
                username="boundary-user",
                password_source=password_source,
                namespace="boundary_test",
                operation_timeout_seconds=1,
            ),
            capabilities=StateStoreCapabilities.p10_contract(),
            clock=ControlledClock(),
        )

    def _load_driver(self):
        return (
            lambda **_: self.fake_client,
            _FakeResponseError,
            _FakeTimeoutError,
            object(),
        )

class RedisStateStoreProviderLifecycleBoundaryTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_custom_password_source_return_value_is_revalidated(self) -> None:
        class SecretSubclass(str):
            pass

        async def secret_coroutine():
            return "coroutine-secret"

        invalid_values = (
            "",
            b"bytes-secret",
            object(),
            SecretSubclass("subclass-secret"),
            secret_coroutine(),
        )
        try:
            for value in invalid_values:
                with self.subTest(value_type=type(value).__name__):
                    store = _BoundaryProvider(
                        password_source=_ReturningPasswordSource(value),
                    )
                    with self.assertRaises(NsRuntimeStateStoreUnavailableError) as caught:
                        await store.open()
                    self.assertIs(StateStoreLifecycleState.NEW, store.state)
                    rendered = str(caught.exception) + repr(caught.exception)
                    for forbidden in (
                        "bytes-secret", "subclass-secret", "coroutine-secret",
                        "source-repr-must-not-leak", "boundary.invalid",
                        "boundary-user",
                    ):
                        self.assertNotIn(forbidden, rendered)
        finally:
            for value in invalid_values:
                if hasattr(value, "close"):
                    value.close()

        for value in (None, "valid-secret"):
            with self.subTest(valid_type=type(value).__name__):
                store = _BoundaryProvider(
                    password_source=_ReturningPasswordSource(value),
                )
                await store.open()
                self.assertIs(StateStoreLifecycleState.OPEN, store.state)
                await store.close()

    async def test_password_source_exception_is_sanitized(self) -> None:
        store = _BoundaryProvider(password_source=_RaisingPasswordSource(
            RuntimeError(
                "driver-text secret-value source-repr-must-not-leak "
                "boundary.invalid boundary-user"
            ),
        ))
        with self.assertRaises(NsRuntimeStateStoreUnavailableError) as caught:
            await store.open()
        self.assertIs(StateStoreLifecycleState.NEW, store.state)
        rendered = str(caught.exception) + repr(caught.exception)
        for forbidden in (
            "driver-text", "secret-value", "source-repr-must-not-leak",
            "boundary.invalid", "boundary-user",
        ):
            self.assertNotIn(forbidden, rendered)

    async def test_open_baseexception_restores_new_and_preserves_identity(self) -> None:
        class CustomBoundaryFailure(BaseException):
            pass

        for error in (KeyboardInterrupt(), SystemExit(), CustomBoundaryFailure()):
            with self.subTest(error_type=type(error).__name__):
                store = _BoundaryProvider(
                    password_source=_RaisingPasswordSource(error),
                )
                with self.assertRaises(type(error)) as caught:
                    await store.open()
                self.assertIs(error, caught.exception)
                self.assertIs(StateStoreLifecycleState.NEW, store.state)

    async def test_close_baseexception_restores_open_and_can_retry(self) -> None:
        class CustomBoundaryFailure(BaseException):
            pass

        for error in (KeyboardInterrupt(), SystemExit(), CustomBoundaryFailure()):
            with self.subTest(error_type=type(error).__name__):
                client = _FakeRedisClient(close_failure=error)
                store = _BoundaryProvider(
                    password_source=_ReturningPasswordSource(None),
                    client=client,
                )
                await store.open()
                with self.assertRaises(type(error)) as caught:
                    await store.close()
                self.assertIs(error, caught.exception)
                self.assertIs(StateStoreLifecycleState.OPEN, store.state)
                client.close_failure = None
                await store.close()
                self.assertIs(StateStoreLifecycleState.CLOSED, store.state)


if __name__ == "__main__":
    unittest.main()
