# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from dataclasses import fields
from pathlib import Path
from typing import Any

from ns_common.runtime.config import (
    RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED,
    RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_NO_SUB_OR_REJECTED,
    RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_REJECTED_ONLY,
    RUNTIME_BROKER_MESSAGE_FORWARD_POLICIES,
    NsRuntimeConfig,
)


REQUIRED_RUNTIME_CONFIG_KEYS: tuple[str, ...] = (
    "enabled",
    "node_id",
    "node_role",
    "runtime_broker_backend",
    "runtime_broker_location",
    "runtime_broker_health_publish_enabled",
    "runtime_broker_message_forward_local_handle_enabled",
    "runtime_broker_message_forward_dispatch_enabled",
    "runtime_broker_message_forward_dispatch_policy",
    "runtime_presence_backend",
)

REQUIRED_BROKER_CONFIG_KEYS: tuple[str, ...] = (
    "runtime_broker_backend",
    "runtime_broker_location",
    "runtime_broker_health_publish_enabled",
    "runtime_broker_message_forward_local_handle_enabled",
    "runtime_broker_message_forward_dispatch_enabled",
    "runtime_broker_message_forward_dispatch_policy",
)


def _load_json_file(_path: Path) -> dict[str, Any]:
    """Load JSON file as object."""
    with _path.open("r", encoding="utf-8") as file:
        payload: Any = json.load(file)

    if not isinstance(payload, dict):
        raise RuntimeError(f"config example must be a JSON object: {_path}")

    return payload


def _runtime_config_from_example(_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract runtime_config from example payload."""
    runtime_config: Any = _payload.get("runtime_config")
    if not isinstance(runtime_config, dict):
        raise RuntimeError("config example must contain runtime_config JSON object")

    return dict(runtime_config)


def _assert_required_keys_exist(_runtime_config: dict[str, Any]) -> None:
    """Assert required runtime config keys exist in example."""
    missing_keys: list[str] = [
        key
        for key in REQUIRED_RUNTIME_CONFIG_KEYS
        if key not in _runtime_config
    ]

    if missing_keys:
        raise RuntimeError(f"runtime_config example missing keys: {', '.join(missing_keys)}")


def _assert_keys_exist_in_dataclass(_runtime_config: dict[str, Any]) -> None:
    """Assert selected example keys exist on NsRuntimeConfig."""
    dataclass_keys: set[str] = {field.name for field in fields(NsRuntimeConfig)}
    unknown_keys: list[str] = [
        key
        for key in REQUIRED_RUNTIME_CONFIG_KEYS
        if key not in dataclass_keys
    ]

    if unknown_keys:
        raise RuntimeError(f"NsRuntimeConfig missing expected fields: {', '.join(unknown_keys)}")

    example_only_keys: list[str] = [
        key
        for key in REQUIRED_BROKER_CONFIG_KEYS
        if key not in dataclass_keys
    ]

    if example_only_keys:
        raise RuntimeError(f"runtime broker example keys are not valid NsRuntimeConfig fields: {', '.join(example_only_keys)}")

    _ = _runtime_config


def _assert_broker_defaults(_runtime_config: dict[str, Any]) -> None:
    """Assert broker defaults in example keep runtime broker disabled by default."""
    expected_values: dict[str, Any] = {
        "runtime_broker_backend": "memory",
        "runtime_broker_location": "",
        "runtime_broker_health_publish_enabled": False,
        "runtime_broker_message_forward_local_handle_enabled": False,
        "runtime_broker_message_forward_dispatch_enabled": False,
        "runtime_broker_message_forward_dispatch_policy": RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED,
    }

    mismatches: list[str] = []
    for key, expected_value in expected_values.items():
        actual_value: Any = _runtime_config.get(key)
        if actual_value != expected_value:
            mismatches.append(f"{key}={actual_value!r}, expected={expected_value!r}")

    if mismatches:
        raise RuntimeError(f"runtime broker default mismatch: {'; '.join(mismatches)}")


def _assert_policy_semantics() -> None:
    """Assert broker dispatch policy constants and compatibility behavior."""
    expected_policies: tuple[str, ...] = (
        RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED,
        RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_REJECTED_ONLY,
        RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_NO_SUB_OR_REJECTED,
    )

    if tuple(RUNTIME_BROKER_MESSAGE_FORWARD_POLICIES) != expected_policies:
        raise RuntimeError("runtime broker message forward policy list is inconsistent")

    default_config = NsRuntimeConfig(enabled=True)
    default_config.validate()
    if default_config.resolved_runtime_broker_message_forward_dispatch_policy() != RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_DISABLED:
        raise RuntimeError("default broker message forward dispatch policy must resolve to disabled")

    compat_config = NsRuntimeConfig(
        enabled=True,
        runtime_broker_message_forward_dispatch_enabled=True,
    )
    compat_config.validate()
    if compat_config.resolved_runtime_broker_message_forward_dispatch_policy() != RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_REJECTED_ONLY:
        raise RuntimeError("compat broker dispatch enabled should resolve to rejected_only")

    explicit_config = NsRuntimeConfig(
        enabled=True,
        runtime_broker_message_forward_dispatch_policy=RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_NO_SUB_OR_REJECTED,
    )
    explicit_config.validate()
    if explicit_config.resolved_runtime_broker_message_forward_dispatch_policy() != RUNTIME_BROKER_MESSAGE_FORWARD_POLICY_NO_SUB_OR_REJECTED:
        raise RuntimeError("explicit broker dispatch policy should be preserved")


def run_smoke(*, config_path: Path) -> None:
    """Run runtime config consistency smoke checks."""
    payload = _load_json_file(config_path)
    runtime_config = _runtime_config_from_example(payload)

    _assert_required_keys_exist(runtime_config)
    _assert_keys_exist_in_dataclass(runtime_config)
    _assert_broker_defaults(runtime_config)
    _assert_policy_semantics()


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Run runtime config consistency smoke checks.")
    parser.add_argument(
        "--config",
        default="etc/ns_config.example.json",
        help="Path to ns_config example JSON.",
    )
    args = parser.parse_args()

    run_smoke(config_path=Path(str(args.config)).resolve())

    print("runtime config consistency smoke ok")


if __name__ == "__main__":
    main()
