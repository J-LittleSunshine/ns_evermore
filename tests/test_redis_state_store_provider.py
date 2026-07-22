# -*- coding: utf-8 -*-
"""Configuration, composition, and secret-boundary tests for P10-FIX-01."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ns_common.config import NsConfig
from ns_common.exceptions import NsConfigError, NsRuntimeStateStoreUnavailableError
from ns_common.state_store import (
    EnvironmentStateStorePassword,
    FileStateStorePassword,
    RedisValkeyStateStore,
    create_state_store_provider,
)
from ns_common.time import ControlledClock


class RedisStateStoreProviderBoundaryTestCase(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
