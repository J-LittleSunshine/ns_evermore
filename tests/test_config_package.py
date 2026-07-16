# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import ns_common
import ns_common.config as config_facade
from ns_common.config import (
    FrozenDict,
    NsConfig,
    NsConfigResolver,
    NsConfigSource,
)
from ns_common.exceptions import NsConfigError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PACKAGE = PROJECT_ROOT / "src" / "ns_common" / "config"

CONFIG_FACADE_EXPORTS = frozenset({
    "Any",
    "ETC_DIR",
    "Enum",
    "FrozenDict",
    "Iterator",
    "Literal",
    "MISSING",
    "Mapping",
    "MappingABC",
    "NS_CONFIG_FILE_PATH",
    "NS_CONFIG_SOURCE_PRIORITY",
    "NS_ENV",
    "NsBackendConfig",
    "NsCacheConfig",
    "NsConfig",
    "NsConfigError",
    "NsConfigGroupMetadata",
    "NsConfigResolver",
    "NsConfigSource",
    "NsDependencyError",
    "NsLogConfig",
    "NsRuntimeClusterConfig",
    "NsRuntimeConfig",
    "NsRuntimeDebugConfig",
    "NsRuntimeDeliveryConfig",
    "NsRuntimeEventLoopConfig",
    "NsRuntimeIamConfig",
    "NsRuntimeLoggingConfig",
    "NsRuntimeObservabilityConfig",
    "NsRuntimePoolConfig",
    "NsRuntimeProtocolConfig",
    "NsRuntimeRecoveryConfig",
    "NsRuntimeRoutingConfig",
    "NsRuntimeSecurityConfig",
    "NsRuntimeStateStoreConfig",
    "NsRuntimeTenantQuotaConfig",
    "NsRuntimeTransportAdapterConfig",
    "NsRuntimeTransportConfig",
    "NsRuntimeWireCodecConfig",
    "NsRuntimeWorkerConfig",
    "Path",
    "RLock",
    "RUNTIME_CLUSTER_ROLES",
    "RUNTIME_CONFIG_APPLY_MODES",
    "RUNTIME_CONFIG_GROUP_NAMES",
    "TYPE_CHECKING",
    "Union",
    "annotations",
    "dataclass",
    "datetime",
    "ensure_runtime_dirs",
    "field",
    "fields",
    "get_args",
    "get_default_config_path",
    "get_ns_env",
    "get_origin",
    "get_type_hints",
    "importlib",
    "is_dataclass",
    "json",
    "ns_config",
    "os",
    "re",
    "replace",
    "tempfile",
    "timezone",
    "types",
    "urlparse",
})

CONFIG_SUBMODULES = (
    "ns_common.config.defaults",
    "ns_common.config.primitives",
    "ns_common.config.metadata",
    "ns_common.config.groups",
    "ns_common.config.groups.backend",
    "ns_common.config.groups.cache",
    "ns_common.config.groups.logging",
    "ns_common.config.groups.runtime",
    "ns_common.config.validation",
    "ns_common.config.codec",
    "ns_common.config.resolver",
    "ns_common.config.model",
)

CONFIG_PUBLIC_TYPES = {
    "NsBackendConfig": "ns_common.config.groups.backend",
    "NsCacheConfig": "ns_common.config.groups.cache",
    "NsLogConfig": "ns_common.config.groups.logging",
    "NsRuntimeClusterConfig": "ns_common.config.groups.runtime",
    "NsRuntimeConfig": "ns_common.config.groups.runtime",
    "NsRuntimeDebugConfig": "ns_common.config.groups.runtime",
    "NsRuntimeDeliveryConfig": "ns_common.config.groups.runtime",
    "NsRuntimeEventLoopConfig": "ns_common.config.groups.runtime",
    "NsRuntimeIamConfig": "ns_common.config.groups.runtime",
    "NsRuntimeLoggingConfig": "ns_common.config.groups.runtime",
    "NsRuntimeObservabilityConfig": "ns_common.config.groups.runtime",
    "NsRuntimePoolConfig": "ns_common.config.groups.runtime",
    "NsRuntimeProtocolConfig": "ns_common.config.groups.runtime",
    "NsRuntimeRecoveryConfig": "ns_common.config.groups.runtime",
    "NsRuntimeRoutingConfig": "ns_common.config.groups.runtime",
    "NsRuntimeSecurityConfig": "ns_common.config.groups.runtime",
    "NsRuntimeStateStoreConfig": "ns_common.config.groups.runtime",
    "NsRuntimeTenantQuotaConfig": "ns_common.config.groups.runtime",
    "NsRuntimeTransportAdapterConfig": "ns_common.config.groups.runtime",
    "NsRuntimeTransportConfig": "ns_common.config.groups.runtime",
    "NsRuntimeWireCodecConfig": "ns_common.config.groups.runtime",
    "NsRuntimeWorkerConfig": "ns_common.config.groups.runtime",
    "NsConfigGroupMetadata": "ns_common.config.metadata",
    "NsConfigSource": "ns_common.config.metadata",
    "NsConfigResolver": "ns_common.config.resolver",
    "NsConfig": "ns_common.config.model",
    "FrozenDict": "ns_common.config.primitives",
}

NS_COMMON_CONFIG_EXPORTS = frozenset({
    "NS_CONFIG_FILE_PATH",
    "NS_CONFIG_SOURCE_PRIORITY",
    "NS_ENV",
    "RUNTIME_CLUSTER_ROLES",
    "RUNTIME_CONFIG_APPLY_MODES",
    "RUNTIME_CONFIG_GROUP_NAMES",
    "NsBackendConfig",
    "NsCacheConfig",
    "NsConfig",
    "NsConfigGroupMetadata",
    "NsConfigResolver",
    "NsConfigSource",
    "NsLogConfig",
    "NsRuntimeClusterConfig",
    "NsRuntimeConfig",
    "NsRuntimeDebugConfig",
    "NsRuntimeDeliveryConfig",
    "NsRuntimeEventLoopConfig",
    "NsRuntimeIamConfig",
    "NsRuntimeLoggingConfig",
    "NsRuntimeObservabilityConfig",
    "NsRuntimePoolConfig",
    "NsRuntimeProtocolConfig",
    "NsRuntimeRecoveryConfig",
    "NsRuntimeRoutingConfig",
    "NsRuntimeSecurityConfig",
    "NsRuntimeStateStoreConfig",
    "NsRuntimeTenantQuotaConfig",
    "NsRuntimeTransportAdapterConfig",
    "NsRuntimeTransportConfig",
    "NsRuntimeWireCodecConfig",
    "NsRuntimeWorkerConfig",
    "ns_config",
})


class NsConfigPackageStructureTestCase(unittest.TestCase):
    def test_config_is_package_with_required_structure(self) -> None:
        self.assertTrue(hasattr(config_facade, "__path__"))
        self.assertEqual("__init__.py", Path(config_facade.__file__).name)
        self.assertFalse((PROJECT_ROOT / "src" / "ns_common" / "config.py").exists())

        expected_files = {
            "__init__.py",
            "codec.py",
            "defaults.py",
            "metadata.py",
            "model.py",
            "primitives.py",
            "resolver.py",
            "validation.py",
            "groups/__init__.py",
            "groups/backend.py",
            "groups/cache.py",
            "groups/logging.py",
            "groups/runtime.py",
        }
        actual_files = {
            path.relative_to(CONFIG_PACKAGE).as_posix()
            for path in CONFIG_PACKAGE.rglob("*.py")
        }
        self.assertEqual(expected_files, actual_files)

    def test_facade_preserves_legacy_public_exports(self) -> None:
        self.assertEqual(CONFIG_FACADE_EXPORTS, frozenset(config_facade.__all__))
        self.assertEqual(69, len(config_facade.__all__))

        namespace: dict[str, object] = {}
        exec("from ns_common.config import *", namespace)
        self.assertTrue(CONFIG_FACADE_EXPORTS.issubset(namespace))

    def test_facade_and_ns_common_export_authoritative_objects(self) -> None:
        for symbol_name, module_name in CONFIG_PUBLIC_TYPES.items():
            internal_module = importlib.import_module(module_name)
            facade_value = getattr(config_facade, symbol_name)
            internal_value = getattr(internal_module, symbol_name)
            self.assertIs(facade_value, internal_value, symbol_name)

            if symbol_name in NS_COMMON_CONFIG_EXPORTS:
                self.assertIs(getattr(ns_common, symbol_name), facade_value, symbol_name)

        for symbol_name in NS_COMMON_CONFIG_EXPORTS:
            self.assertTrue(hasattr(ns_common, symbol_name), symbol_name)
            self.assertIs(getattr(ns_common, symbol_name), getattr(config_facade, symbol_name))

    def test_all_submodules_import_in_fresh_interpreter(self) -> None:
        source = "import importlib; " + "; ".join(
            f"importlib.import_module({module_name!r})"
            for module_name in reversed(CONFIG_SUBMODULES)
        )
        environment = os.environ.copy()
        src_path = str(PROJECT_ROOT / "src")
        environment["PYTHONPATH"] = os.pathsep.join(
            part
            for part in (src_path, environment.get("PYTHONPATH", ""))
            if part
        )
        completed = subprocess.run(
            [sys.executable, "-c", source],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_codec_round_trip_and_atomic_save_remain_compatible(self) -> None:
        example_path = PROJECT_ROOT / "etc" / "ns_config.example.json"
        loaded = NsConfig.load(example_path, environment="local")
        restored = NsConfig.from_dict(loaded.to_dict(), environment="local")
        self.assertEqual(loaded, restored)

        with tempfile.TemporaryDirectory() as temp_directory:
            target_path = Path(temp_directory) / "nested" / "config.json"
            loaded.save(target_path, environment="local")
            self.assertEqual(loaded, NsConfig.load(target_path, environment="local"))
            self.assertFalse(any(target_path.parent.glob(f".{target_path.name}.*.tmp")))

        with self.assertRaises(NsConfigError) as context:
            NsConfig.from_dict({"unknown": True})
        self.assertEqual("config", context.exception.details["field"])
        self.assertEqual(["unknown"], context.exception.details["unknown_fields"])

    def test_environment_resolver_metadata_and_immutability_remain_compatible(self) -> None:
        for environment in ("local", "dev", "test"):
            self.assertIsInstance(NsConfig.from_dict({}, environment=environment), NsConfig)

        production = NsConfig.from_dict(
            {
                "backend": {
                    "debug": False,
                    "secret_key": "production-secret-key-at-least-32-characters",
                },
                "runtime": {
                    "transport": {
                        "websocket_tcp": {"enabled": True, "tls_enabled": True},
                    },
                    "state_store": {
                        "backend": "redis",
                        "url": "redis://127.0.0.1:6379/0",
                    },
                },
            },
            environment="prod",
        )
        self.assertFalse(production.backend.debug)

        effective_at = "2026-07-16T08:00:00Z"
        local = NsConfigResolver(
            environment="local",
            effective_at=effective_at,
        ).resolve({})
        self.assertIs(NsConfigSource.LOCAL_FILE, local.backend.metadata.source)
        self.assertEqual(effective_at, local.backend.metadata.effective_at)

        snapshot = local.as_validated_snapshot(
            effective_at="2026-07-16T09:00:00Z",
            environment="local",
        )
        accepted = NsConfigResolver(environment="local").resolve(
            {},
            validated_snapshot=snapshot,
        )
        self.assertIs(snapshot, accepted)
        self.assertIs(NsConfigSource.VALIDATED_SNAPSHOT, accepted.runtime.metadata.source)

        self.assertIsInstance(local.backend.databases, FrozenDict)
        with self.assertRaises(TypeError):
            local.backend.databases["default"] = {}  # type: ignore[index]

    def test_production_callers_only_import_the_facade(self) -> None:
        forbidden_imports = (
            "ns_common.config.groups.",
            "ns_common.config.validation",
            "ns_common.config.codec",
            "ns_common.config.resolver",
        )
        violations: list[str] = []
        source_root = PROJECT_ROOT / "src"
        for source_path in source_root.rglob("*.py"):
            if CONFIG_PACKAGE in source_path.parents:
                continue
            source = source_path.read_text(encoding="utf-8")
            for forbidden_import in forbidden_imports:
                if forbidden_import in source:
                    violations.append(
                        f"{source_path.relative_to(PROJECT_ROOT).as_posix()}: {forbidden_import}"
                    )

        self.assertEqual([], violations)

        for module_name in (
            "ns_common.async_runtime",
            "ns_common.cache.clients",
            "ns_common.cache.backends.sqlite",
            "ns_common.logger",
        ):
            importlib.import_module(module_name)

    def test_internal_dependency_boundaries_are_explicit(self) -> None:
        primitives_source = (CONFIG_PACKAGE / "primitives.py").read_text(encoding="utf-8")
        validation_source = (CONFIG_PACKAGE / "validation.py").read_text(encoding="utf-8")
        codec_source = (CONFIG_PACKAGE / "codec.py").read_text(encoding="utf-8")
        resolver_source = (CONFIG_PACKAGE / "resolver.py").read_text(encoding="utf-8")
        group_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (CONFIG_PACKAGE / "groups").glob("*.py")
        )

        self.assertNotIn(".groups", primitives_source)
        self.assertNotIn(".resolver", validation_source)
        self.assertNotIn("ns_config", codec_source)
        self.assertNotIn("sys.modules", resolver_source)
        self.assertNotIn("from ..model", group_sources)
        self.assertNotIn("from .model", group_sources)


if __name__ == "__main__":
    unittest.main()
