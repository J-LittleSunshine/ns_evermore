# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from ns_common.config import (
    FrozenDict,
    NS_CONFIG_SOURCE_PRIORITY,
    NsConfig,
    NsConfigSource,
    NsRuntimeConfig,
)
from ns_common.exceptions import NsConfigError


FIXED_EFFECTIVE_AT = "2026-07-16T06:00:00Z"


def build_metadata(
    *,
    source: str,
    config_version: str,
    policy_version: str,
    group_version: str,
    effective_at: str = FIXED_EFFECTIVE_AT,
    rollback_from_version: str | None = None,
    apply_mode: str = "immediate",
) -> dict[str, object]:
    return {
        "source": source,
        "config_version": config_version,
        "policy_version": policy_version,
        "group_version": group_version,
        "effective_at": effective_at,
        "rollback_from_version": rollback_from_version,
        "apply_mode": apply_mode,
    }


class NsConfigSnapshotTestCase(unittest.TestCase):

    def test_default_config_contains_runtime_group_and_metadata(self) -> None:
        config = NsConfig.from_dict({})

        self.assertIsInstance(config.runtime, NsRuntimeConfig)
        self.assertEqual("local_file", config.runtime.metadata.source)
        self.assertEqual("restart_required", config.runtime.metadata.apply_mode)
        self.assertIs(config.runtime, config.runtime_config)

    def test_loaded_config_is_deeply_immutable(self) -> None:
        config = NsConfig.from_dict({
            "backend": {
                "allowed_hosts": ["localhost"],
                "databases": {
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        "NAME": "ns.sqlite3",
                        "OPTIONS": {
                            "timeout": 10,
                        },
                    },
                },
            },
        })

        with self.assertRaises(FrozenInstanceError):
            config.cache.backend = "dummy"  # type: ignore[misc]

        self.assertIsInstance(config.backend.databases, FrozenDict)
        with self.assertRaises(TypeError):
            config.backend.databases["other"] = {}  # type: ignore[index]

        default_database = config.backend.databases["default"]
        self.assertIsInstance(default_database, FrozenDict)
        with self.assertRaises(TypeError):
            default_database["NAME"] = "other.sqlite3"  # type: ignore[index]

        self.assertEqual(("localhost",), config.backend.allowed_hosts)

    def test_to_dict_returns_detached_json_compatible_data(self) -> None:
        config = NsConfig.from_dict({
            "backend": {
                "allowed_hosts": ["localhost"],
                "databases": {
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        "NAME": "ns.sqlite3",
                    },
                },
            },
        })

        serialized = config.to_dict()
        self.assertIsInstance(serialized["backend"]["allowed_hosts"], list)
        json.dumps(serialized)

        serialized["backend"]["allowed_hosts"].append("example.test")
        serialized["backend"]["databases"]["default"]["NAME"] = "changed.sqlite3"

        self.assertEqual(("localhost",), config.backend.allowed_hosts)
        self.assertEqual(
            "ns.sqlite3",
            config.backend.databases["default"]["NAME"],
        )

    def test_full_round_trip_preserves_snapshot(self) -> None:
        original = NsConfig.from_dict({
            "backend": {
                "debug": False,
                "allowed_hosts": ["runtime.example.test"],
            },
            "cache": {
                "backend": "dummy",
                "key_prefix": "runtime_test",
            },
            "log": {
                "console": False,
                "level_files": ["INFO", "ERROR"],
            },
            "runtime": {
                "metadata": {
                    "source": "local_file",
                    "config_version": "config-1",
                    "policy_version": "policy-1",
                    "group_version": "runtime-1",
                    "effective_at": "2026-07-16T00:00:00Z",
                    "rollback_from_version": None,
                    "apply_mode": "restart_required",
                },
            },
        })

        restored = NsConfig.from_dict(original.to_dict())

        self.assertEqual(original, restored)

    def test_save_and_load_use_explicit_temporary_path(self) -> None:
        config = NsConfig.resolve(
            {
                "cache": {
                    "backend": "dummy",
                },
            },
            environment="test",
            effective_at=FIXED_EFFECTIVE_AT,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config" / "runtime.json"
            config.save(config_path, environment="test")
            restored = NsConfig.load(
                config_path,
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
            )

            self.assertEqual(config, restored)
            self.assertTrue(config_path.is_file())
            self.assertEqual([], list(config_path.parent.glob("*.tmp")))

    def test_missing_explicit_file_loads_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = NsConfig.load(
                Path(temp_dir) / "missing.json",
                environment="test",
            )

        self.assertEqual("sqlite", config.cache.backend)
        self.assertIsInstance(config.runtime, NsRuntimeConfig)

    def test_unknown_top_level_field_is_rejected(self) -> None:
        with self.assertRaises(NsConfigError) as context:
            NsConfig.from_dict({
                "runtime_typo": {},
            })

        self.assertEqual(["runtime_typo"], context.exception.details["unknown_fields"])

    def test_unknown_group_and_metadata_fields_are_rejected(self) -> None:
        with self.assertRaises(NsConfigError) as group_context:
            NsConfig.from_dict({
                "cache": {
                    "default_ttl_second": 300,
                },
            })
        self.assertEqual(
            ["default_ttl_second"],
            group_context.exception.details["unknown_fields"],
        )

        with self.assertRaises(NsConfigError) as metadata_context:
            NsConfig.from_dict({
                "runtime": {
                    "metadata": {
                        "group_verison": "typo",
                    },
                },
            })
        self.assertEqual(
            ["group_verison"],
            metadata_context.exception.details["unknown_fields"],
        )

    def test_invalid_section_and_field_types_are_rejected(self) -> None:
        with self.assertRaises(NsConfigError):
            NsConfig.from_dict({
                "runtime": [],
            })

        with self.assertRaises(NsConfigError) as context:
            NsConfig.from_dict({
                "cache": {
                    "default_ttl_seconds": "300",
                },
            })

        self.assertEqual("cache.default_ttl_seconds", context.exception.details["field"])

    def test_environment_validation_and_prod_rules(self) -> None:
        prod_config = NsConfig.from_dict(
            {
                "backend": {
                    "debug": False,
                    "secret_key": "s" * 32,
                },
            },
            environment="prod",
        )
        self.assertFalse(prod_config.backend.debug)

        with self.assertRaises(NsConfigError):
            NsConfig.from_dict({}, environment="prod")

        with self.assertRaises(NsConfigError) as context:
            NsConfig.from_dict({}, environment="production")
        self.assertEqual("environment", context.exception.details["field"])

    def test_legacy_section_names_and_attribute_aliases_remain_compatible(self) -> None:
        config = NsConfig.from_dict({
            "backend_config": {
                "debug": False,
            },
            "cache_config": {
                "backend": "dummy",
            },
            "log_config": {
                "console": False,
            },
            "runtime_config": {},
        })

        self.assertIs(config.backend, config.backend_config)
        self.assertIs(config.cache, config.cache_config)
        self.assertIs(config.log, config.log_config)
        self.assertFalse(config.backend.debug)
        self.assertEqual("dummy", config.cache.backend)

    def test_preferred_and_legacy_names_cannot_be_mixed(self) -> None:
        with self.assertRaises(NsConfigError) as context:
            NsConfig.from_dict({
                "cache": {},
                "cache_config": {},
            })

        self.assertEqual("cache_config", context.exception.details["conflicting_field"])

    def test_non_object_json_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid.json"
            config_path.write_text("[]", encoding="utf-8")

            with self.assertRaises(NsConfigError):
                NsConfig.load(config_path, environment="test")


class NsConfigResolutionTestCase(unittest.TestCase):

    def test_source_priority_is_stable(self) -> None:
        self.assertLess(
            NS_CONFIG_SOURCE_PRIORITY[NsConfigSource.LOCAL_FILE],
            NS_CONFIG_SOURCE_PRIORITY[NsConfigSource.BACKEND_OVERRIDE],
        )
        self.assertLess(
            NS_CONFIG_SOURCE_PRIORITY[NsConfigSource.BACKEND_OVERRIDE],
            NS_CONFIG_SOURCE_PRIORITY[NsConfigSource.VALIDATED_SNAPSHOT],
        )

    def test_local_config_records_effective_source_and_time(self) -> None:
        config = NsConfig.resolve(
            {},
            environment="test",
            effective_at="2026-07-16T14:00:00+08:00",
        )

        for _, group_config in NsConfig._config_groups(config):
            self.assertIs(NsConfigSource.LOCAL_FILE, group_config.metadata.source)
            self.assertEqual(FIXED_EFFECTIVE_AT, group_config.metadata.effective_at)

        self.assertEqual("0", config.config_version)
        self.assertEqual("0", config.policy_version)

    def test_backend_override_deep_merges_and_updates_provenance(self) -> None:
        config = NsConfig.resolve(
            {
                "backend": {
                    "databases": {
                        "default": {
                            "ENGINE": "django.db.backends.sqlite3",
                            "NAME": "ns.sqlite3",
                            "OPTIONS": {
                                "timeout": 10,
                            },
                        },
                    },
                },
            },
            environment="test",
            effective_at=FIXED_EFFECTIVE_AT,
            backend_override={
                "backend": {
                    "databases": {
                        "default": {
                            "OPTIONS": {
                                "timeout": 20,
                            },
                        },
                    },
                    "metadata": build_metadata(
                        source="backend_override",
                        config_version="config-1",
                        policy_version="policy-1",
                        group_version="backend-1",
                    ),
                },
            },
        )

        default_database = config.backend.databases["default"]
        self.assertEqual("django.db.backends.sqlite3", default_database["ENGINE"])
        self.assertEqual("ns.sqlite3", default_database["NAME"])
        self.assertEqual(20, default_database["OPTIONS"]["timeout"])
        self.assertIs(NsConfigSource.BACKEND_OVERRIDE, config.backend.metadata.source)
        self.assertIs(NsConfigSource.LOCAL_FILE, config.cache.metadata.source)
        self.assertEqual("config-1", config.config_version)
        self.assertEqual("policy-1", config.policy_version)

        restored = NsConfig.from_dict(config.to_dict(), environment="test")
        self.assertIs(NsConfigSource.BACKEND_OVERRIDE, restored.backend.metadata.source)
        self.assertEqual("config-1", restored.config_version)

    def test_validated_snapshot_has_highest_priority(self) -> None:
        snapshot = NsConfig.resolve(
            {
                "cache": {
                    "backend": "sqlite",
                },
            },
            environment="test",
            effective_at=FIXED_EFFECTIVE_AT,
        ).as_validated_snapshot(
            effective_at="2026-07-16T06:05:00Z",
            environment="test",
        )

        effective = NsConfig.resolve(
            {
                "cache": {
                    "backend": "sqlite",
                },
            },
            environment="test",
            effective_at=FIXED_EFFECTIVE_AT,
            backend_override={
                "cache": {
                    "backend": "dummy",
                    "metadata": build_metadata(
                        source="backend_override",
                        config_version="config-1",
                        policy_version="policy-1",
                        group_version="cache-1",
                    ),
                },
            },
            validated_snapshot=snapshot,
        )

        self.assertIs(snapshot, effective)
        self.assertEqual("sqlite", effective.cache.backend)
        for _, group_config in NsConfig._config_groups(effective):
            self.assertIs(
                NsConfigSource.VALIDATED_SNAPSHOT,
                group_config.metadata.source,
            )

    def test_backend_override_requires_complete_authoritative_metadata(self) -> None:
        with self.assertRaises(NsConfigError):
            NsConfig.resolve(
                {},
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                backend_override={
                    "cache": {
                        "backend": "dummy",
                    },
                },
            )

        with self.assertRaises(NsConfigError) as context:
            NsConfig.resolve(
                {},
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                backend_override={
                    "cache": {
                        "metadata": build_metadata(
                            source="local_file",
                            config_version="config-1",
                            policy_version="policy-1",
                            group_version="cache-1",
                        ),
                    },
                },
            )

        self.assertEqual("backend_override", context.exception.details["expected"])

    def test_changed_values_require_new_group_and_config_versions(self) -> None:
        with self.assertRaises(NsConfigError) as group_context:
            NsConfig.resolve(
                {},
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                backend_override={
                    "cache": {
                        "backend": "dummy",
                        "metadata": build_metadata(
                            source="backend_override",
                            config_version="config-1",
                            policy_version="policy-1",
                            group_version="0",
                        ),
                    },
                },
            )
        self.assertEqual(
            "backend_override.cache.metadata.group_version",
            group_context.exception.details["field"],
        )

        with self.assertRaises(NsConfigError) as config_context:
            NsConfig.resolve(
                {},
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                backend_override={
                    "cache": {
                        "backend": "dummy",
                        "metadata": build_metadata(
                            source="backend_override",
                            config_version="0",
                            policy_version="policy-1",
                            group_version="cache-1",
                        ),
                    },
                },
            )
        self.assertEqual(
            "backend_override.metadata.config_version",
            config_context.exception.details["field"],
        )

    def test_rollback_must_reference_current_group_version(self) -> None:
        with self.assertRaises(NsConfigError) as context:
            NsConfig.resolve(
                {},
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                backend_override={
                    "cache": {
                        "metadata": build_metadata(
                            source="backend_override",
                            config_version="config-1",
                            policy_version="policy-1",
                            group_version="cache-1",
                            rollback_from_version="cache-unknown",
                        ),
                    },
                },
            )

        self.assertEqual(
            "backend_override.cache.metadata.rollback_from_version",
            context.exception.details["field"],
        )

    def test_backend_groups_must_share_global_versions(self) -> None:
        with self.assertRaises(NsConfigError) as context:
            NsConfig.resolve(
                {},
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                backend_override={
                    "cache": {
                        "metadata": build_metadata(
                            source="backend_override",
                            config_version="config-1",
                            policy_version="policy-1",
                            group_version="cache-1",
                        ),
                    },
                    "log": {
                        "metadata": build_metadata(
                            source="backend_override",
                            config_version="config-2",
                            policy_version="policy-1",
                            group_version="log-1",
                        ),
                    },
                },
            )

        self.assertEqual("backend_override.metadata", context.exception.details["field"])

    def test_invalid_override_never_mutates_input(self) -> None:
        local_config = {
            "cache": {
                "backend": "sqlite",
            },
        }
        original = json.loads(json.dumps(local_config))

        with self.assertRaises(NsConfigError):
            NsConfig.resolve(
                local_config,
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                backend_override={
                    "cache": {
                        "backend": "not-a-backend",
                        "metadata": build_metadata(
                            source="backend_override",
                            config_version="config-1",
                            policy_version="policy-1",
                            group_version="cache-1",
                        ),
                    },
                },
            )

        self.assertEqual(original, local_config)

    def test_validated_snapshot_must_be_marked_and_typed(self) -> None:
        local_snapshot = NsConfig.resolve(
            {},
            environment="test",
            effective_at=FIXED_EFFECTIVE_AT,
        )

        with self.assertRaises(NsConfigError):
            NsConfig.resolve(
                {},
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                validated_snapshot=local_snapshot,
            )

        with self.assertRaises(NsConfigError):
            NsConfig.resolve(
                {},
                environment="test",
                effective_at=FIXED_EFFECTIVE_AT,
                validated_snapshot={},  # type: ignore[arg-type]
            )

    def test_metadata_timestamp_and_version_format_are_strict(self) -> None:
        with self.assertRaises(NsConfigError):
            NsConfig.from_dict({
                "runtime": {
                    "metadata": {
                        "effective_at": "2026-07-16 14:00:00",
                    },
                },
            })

        with self.assertRaises(NsConfigError):
            NsConfig.from_dict({
                "runtime": {
                    "metadata": {
                        "group_version": "contains spaces",
                    },
                },
            })


if __name__ == "__main__":
    unittest.main()
