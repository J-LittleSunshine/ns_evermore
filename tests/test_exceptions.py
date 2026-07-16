# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import inspect
import json
import os
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

import ns_common
import ns_common.exceptions as exceptions_facade
from ns_common.exceptions import (
    ALL_ERROR_DEFINITIONS,
    ERROR_REGISTRY,
    RUNTIME_NACK_REASON_ERROR_CODES,
    NsConfigError,
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorRegistry,
    NsErrorSeverity,
    NsEvermoreError,
    NsRuntimeError,
    NsRuntimePayloadRefValidationTimeoutError,
    NsRuntimePayloadRefValidationUnavailableError,
    NsRuntimeStartupSecurityError,
    NsValidationError,
    get_error_definition,
    get_error_definition_by_code,
    get_error_definition_by_numeric_code,
    list_error_definitions,
    validate_error_registry,
    validate_runtime_nack_reason_error_codes,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEPTIONS_PACKAGE = PROJECT_ROOT / "src" / "ns_common" / "exceptions"

EXCEPTION_SUBMODULES = (
    "ns_common.exceptions.base",
    "ns_common.exceptions.metadata",
    "ns_common.exceptions.common",
    "ns_common.exceptions.protocol",
    "ns_common.exceptions.payload_ref",
    "ns_common.exceptions.delivery",
    "ns_common.exceptions.cluster",
    "ns_common.exceptions.registry",
    "ns_common.exceptions.nack",
)

EXCEPTION_SNAPSHOTS = {
    "NsEvermoreError": (
        "Exception",
        "NS_ERROR",
        100000,
        "NsEvermore error.",
    ),
    "NsConfigError": (
        "NsEvermoreError",
        "NS_CONFIG_ERROR",
        100100,
        "Invalid ns_evermore configuration.",
    ),
    "NsValidationError": (
        "NsEvermoreError",
        "NS_VALIDATION_ERROR",
        100200,
        "Validation failed.",
    ),
    "NsRuntimeError": (
        "NsEvermoreError",
        "NS_RUNTIME_ERROR",
        100300,
        "NsEvermore runtime error.",
    ),
    "NsDependencyError": (
        "NsEvermoreError",
        "NS_DEPENDENCY_ERROR",
        100400,
        "NsEvermore dependency error.",
    ),
    "NsStateError": (
        "NsEvermoreError",
        "NS_STATE_ERROR",
        100500,
        "Invalid ns_evermore internal state.",
    ),
    "NsHttpClientError": (
        "NsEvermoreError",
        "NS_HTTP_CLIENT_ERROR",
        100600,
        "NsEvermore HTTP client error.",
    ),
    "NsRuntimeProtocolError": (
        "NsRuntimeError",
        "RUNTIME_PROTOCOL_ERROR",
        200100,
        "Runtime protocol error.",
    ),
    "NsRuntimeEnvelopeSchemaError": (
        "NsRuntimeProtocolError",
        "RUNTIME_ENVELOPE_SCHEMA_ERROR",
        200101,
        "Runtime envelope schema error.",
    ),
    "NsRuntimeProtocolVersionError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PROTOCOL_VERSION_ERROR",
        200102,
        "Runtime protocol version is incompatible.",
    ),
    "NsRuntimeSourceForgedError": (
        "NsRuntimeProtocolError",
        "RUNTIME_SOURCE_FORGED",
        200103,
        "Inbound envelope must not contain source.",
    ),
    "NsRuntimeAuthContextForgedError": (
        "NsRuntimeProtocolError",
        "RUNTIME_AUTH_CONTEXT_FORGED",
        200104,
        "Inbound envelope must not contain auth_context.",
    ),
    "NsRuntimeUnsupportedMessageTypeError": (
        "NsRuntimeProtocolError",
        "RUNTIME_UNSUPPORTED_MESSAGE_TYPE",
        200105,
        "Runtime message type is not registered.",
    ),
    "NsRuntimeUnauthorizedMessageTypeError": (
        "NsRuntimeProtocolError",
        "RUNTIME_UNAUTHORIZED_MESSAGE_TYPE",
        200106,
        "Runtime message type is not allowed by current capability.",
    ),
    "NsRuntimeTenantMismatchError": (
        "NsRuntimeProtocolError",
        "RUNTIME_TENANT_MISMATCH",
        200107,
        "Runtime tenant boundary is violated.",
    ),
    "NsRuntimePayloadRefDeniedError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_DENIED",
        200108,
        "Runtime payload reference is denied.",
    ),
    "NsRuntimeTargetUnavailableError": (
        "NsRuntimeError",
        "RUNTIME_TARGET_UNAVAILABLE",
        200109,
        "Runtime target is unavailable.",
    ),
    "NsRuntimeDeliveryStateError": (
        "NsRuntimeError",
        "RUNTIME_DELIVERY_STATE_ERROR",
        200110,
        "Runtime delivery state transition is invalid.",
    ),
    "NsRuntimeAckRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_ACK_REJECTED",
        200111,
        "Runtime ACK is rejected.",
    ),
    "NsRuntimeNackRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_NACK_REJECTED",
        200112,
        "Runtime NACK is rejected.",
    ),
    "NsRuntimeDeferRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_DEFER_REJECTED",
        200113,
        "Runtime Defer is rejected.",
    ),
    "NsRuntimeBackpressureError": (
        "NsRuntimeError",
        "RUNTIME_BACKPRESSURE",
        200114,
        "Runtime backpressure policy rejected the message.",
    ),
    "NsRuntimeClusterCoordinationError": (
        "NsRuntimeError",
        "RUNTIME_CLUSTER_COORDINATION_ERROR",
        200115,
        "Runtime cluster coordination error.",
    ),
    "NsRuntimePayloadRefInvalidError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_INVALID",
        200116,
        "Runtime payload reference is invalid.",
    ),
    "NsRuntimePayloadRefExpiredError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_EXPIRED",
        200117,
        "Runtime payload reference has expired.",
    ),
    "NsRuntimePayloadRefChecksumMismatchError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_CHECKSUM_MISMATCH",
        200118,
        "Runtime payload reference checksum does not match.",
    ),
    "NsRuntimePayloadRefVersionMismatchError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_VERSION_MISMATCH",
        200119,
        "Runtime payload reference version does not match.",
    ),
    "NsRuntimePayloadRefValidationUnavailableError": (
        "NsRuntimeError",
        "RUNTIME_PAYLOAD_REF_VALIDATION_UNAVAILABLE",
        200120,
        "Runtime payload reference validation is unavailable.",
    ),
    "NsRuntimePayloadRefValidationTimeoutError": (
        "NsRuntimePayloadRefValidationUnavailableError",
        "RUNTIME_PAYLOAD_REF_VALIDATION_TIMEOUT",
        200121,
        "Runtime payload reference validation timed out.",
    ),
    "NsRuntimeClusterStateError": (
        "NsRuntimeClusterCoordinationError",
        "RUNTIME_CLUSTER_STATE_ERROR",
        200122,
        "Runtime cluster state transition is invalid.",
    ),
    "NsRuntimeClusterFencingError": (
        "NsRuntimeClusterCoordinationError",
        "RUNTIME_CLUSTER_FENCING_ERROR",
        200123,
        "Runtime cluster fencing validation failed.",
    ),
    "NsRuntimeRoleAdmissionError": (
        "NsRuntimeError",
        "RUNTIME_ROLE_ADMISSION_REJECTED",
        200124,
        "Runtime role admission rejected the operation.",
    ),
    "NsRuntimeStartupSecurityError": (
        "NsConfigError",
        "RUNTIME_STARTUP_SECURITY_ERROR",
        200125,
        "Runtime startup security validation failed.",
    ),
}

TOP_LEVEL_EXCEPTION_EXPORTS = (
    "NsConfigError",
    "NsDependencyError",
    "NsEvermoreError",
    "NsHttpClientError",
    "NsRuntimeAckRejectedError",
    "NsRuntimeAuthContextForgedError",
    "NsRuntimeBackpressureError",
    "NsRuntimeClusterCoordinationError",
    "NsRuntimeDeferRejectedError",
    "NsRuntimeDeliveryStateError",
    "NsRuntimeEnvelopeSchemaError",
    "NsRuntimeError",
    "NsRuntimeNackRejectedError",
    "NsRuntimePayloadRefDeniedError",
    "NsRuntimeProtocolError",
    "NsRuntimeProtocolVersionError",
    "NsRuntimeSourceForgedError",
    "NsRuntimeTargetUnavailableError",
    "NsRuntimeTenantMismatchError",
    "NsRuntimeUnauthorizedMessageTypeError",
    "NsRuntimeUnsupportedMessageTypeError",
    "NsStateError",
    "NsValidationError",
)


def make_definition(
    error_type: type[NsEvermoreError],
    **overrides: object,
) -> NsErrorDefinition:
    values: dict[str, object] = {
        "error_type": error_type,
        "code": error_type.code,
        "numeric_code": error_type.numeric_code,
        "severity": NsErrorSeverity.ERROR,
        "category": NsErrorCategory.COMMON,
        "retryable": False,
        "disconnect_required": False,
        "audit_required": False,
        "safe_detail": False,
        "action": "report_error",
    }
    values.update(overrides)
    return NsErrorDefinition(**values)  # type: ignore[arg-type]


class NsExceptionsPackageStructureTestCase(unittest.TestCase):

    def test_exceptions_is_package_with_required_structure(self) -> None:
        self.assertTrue(hasattr(exceptions_facade, "__path__"))
        self.assertEqual("__init__.py", Path(exceptions_facade.__file__).name)
        self.assertFalse(
            (PROJECT_ROOT / "src" / "ns_common" / "exceptions.py").exists()
        )

        expected_files = {
            "__init__.py",
            "base.py",
            "cluster.py",
            "common.py",
            "delivery.py",
            "metadata.py",
            "nack.py",
            "payload_ref.py",
            "protocol.py",
            "registry.py",
        }
        actual_files = {
            path.relative_to(EXCEPTIONS_PACKAGE).as_posix()
            for path in EXCEPTIONS_PACKAGE.rglob("*.py")
        }
        self.assertEqual(expected_files, actual_files)

    def test_facade_and_ns_common_preserve_authoritative_objects(self) -> None:
        for class_name in EXCEPTION_SNAPSHOTS:
            with self.subTest(class_name=class_name):
                error_type = getattr(exceptions_facade, class_name)
                self.assertIsInstance(error_type, type)
                self.assertIn(class_name, exceptions_facade.__all__)

        for symbol_name in TOP_LEVEL_EXCEPTION_EXPORTS:
            with self.subTest(symbol_name=symbol_name):
                self.assertIs(
                    getattr(ns_common, symbol_name),
                    getattr(exceptions_facade, symbol_name),
                )

        self.assertIs(
            ns_common.RUNTIME_NACK_REASON_ERROR_CODES,
            RUNTIME_NACK_REASON_ERROR_CODES,
        )

    def test_all_submodules_import_in_fresh_interpreter(self) -> None:
        source = "import importlib; " + "; ".join(
            f"importlib.import_module({module_name!r})"
            for module_name in reversed(EXCEPTION_SUBMODULES)
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

    def test_production_callers_only_import_exceptions_facade(self) -> None:
        violations: list[str] = []
        source_root = PROJECT_ROOT / "src"
        for source_path in source_root.rglob("*.py"):
            if EXCEPTIONS_PACKAGE in source_path.parents:
                continue
            source = source_path.read_text(encoding="utf-8")
            if "ns_common.exceptions." in source:
                violations.append(source_path.relative_to(PROJECT_ROOT).as_posix())
        self.assertEqual([], violations)

    def test_dependency_boundaries_do_not_create_cycles(self) -> None:
        base_source = (EXCEPTIONS_PACKAGE / "base.py").read_text(encoding="utf-8")
        metadata_source = (EXCEPTIONS_PACKAGE / "metadata.py").read_text(
            encoding="utf-8"
        )
        registry_source = (EXCEPTIONS_PACKAGE / "registry.py").read_text(
            encoding="utf-8"
        )
        all_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in EXCEPTIONS_PACKAGE.glob("*.py")
        )

        for forbidden in ("registry", "security", "logger", "config"):
            self.assertNotIn(forbidden, base_source)
        for domain_module in (
            ".common",
            ".protocol",
            ".payload_ref",
            ".delivery",
            ".cluster",
        ):
            self.assertNotIn(domain_module, metadata_source)
        for forbidden in ("__subclasses__", "sys.modules", "importlib"):
            self.assertNotIn(forbidden, registry_source)
        for forbidden_import in (
            "ns_common.security",
            "ns_common.logger",
            "ns_common.config",
            "from ..security",
            "from ..logger",
            "from ..config",
        ):
            self.assertNotIn(forbidden_import, all_source)


class NsExceptionCompatibilityTestCase(unittest.TestCase):

    def test_class_metadata_and_inheritance_match_legacy_contract(self) -> None:
        self.assertEqual(33, len(EXCEPTION_SNAPSHOTS))
        for class_name, snapshot in EXCEPTION_SNAPSHOTS.items():
            with self.subTest(class_name=class_name):
                base_name, code, numeric_code, default_message = snapshot
                error_type = getattr(exceptions_facade, class_name)
                self.assertEqual(base_name, error_type.__bases__[0].__name__)
                self.assertEqual(code, error_type.code)
                self.assertEqual(numeric_code, error_type.numeric_code)
                self.assertEqual(default_message, error_type.default_message)

    def test_constructor_signature_and_behavior_remain_compatible(self) -> None:
        expected_parameters = (
            "message",
            "code",
            "numeric_code",
            "details",
        )
        for class_name, snapshot in EXCEPTION_SNAPSHOTS.items():
            with self.subTest(class_name=class_name):
                error_type = getattr(exceptions_facade, class_name)
                signature = inspect.signature(error_type)
                self.assertEqual(expected_parameters, tuple(signature.parameters))
                self.assertIsNone(signature.parameters["message"].default)
                for parameter_name in expected_parameters[1:]:
                    parameter = signature.parameters[parameter_name]
                    self.assertIsNone(parameter.default)
                    self.assertIs(
                        inspect.Parameter.KEYWORD_ONLY,
                        parameter.kind,
                    )

                default_error = error_type()
                self.assertEqual(snapshot[1], default_error.code)
                self.assertEqual(snapshot[2], default_error.numeric_code)
                self.assertEqual(snapshot[3], default_error.message)
                self.assertEqual({}, default_error.details)

                custom_error = error_type(
                    "custom message",
                    code="CUSTOM_CODE",
                    numeric_code=900001,
                    details={"field": "value"},
                )
                self.assertEqual("custom message", custom_error.message)
                self.assertEqual("CUSTOM_CODE", custom_error.code)
                self.assertEqual(900001, custom_error.numeric_code)
                self.assertEqual({"field": "value"}, custom_error.details)

    def test_details_to_dict_and_string_behavior_remain_compatible(self) -> None:
        nested = {"item": "value"}
        original_details = {"field": "input", "nested": nested}
        error = NsValidationError("bad input", details=original_details)
        original_details["field"] = "changed"

        self.assertEqual("input", error.details["field"])
        self.assertIs(nested, error.details["nested"])
        self.assertEqual(
            {
                "code": "NS_VALIDATION_ERROR",
                "numeric_code": 100200,
                "message": "bad input",
                "details": {"field": "input", "nested": nested},
            },
            error.to_dict(),
        )
        self.assertEqual(
            "[NS_VALIDATION_ERROR/100200] bad input "
            "details={'field': 'input', 'nested': {'item': 'value'}}",
            str(error),
        )
        self.assertEqual(
            "[NS_VALIDATION_ERROR/100200] Validation failed.",
            str(NsValidationError()),
        )

    def test_falsy_override_behavior_is_not_changed(self) -> None:
        error = NsValidationError(
            "",
            code="",
            numeric_code=0,
            details={},
        )
        self.assertEqual(NsValidationError.default_message, error.message)
        self.assertEqual(NsValidationError.code, error.code)
        self.assertEqual(NsValidationError.numeric_code, error.numeric_code)

    def test_existing_catch_relationships_remain_compatible(self) -> None:
        runtime_error = NsRuntimePayloadRefValidationTimeoutError()
        self.assertIsInstance(runtime_error, NsRuntimeError)
        self.assertIsInstance(
            runtime_error,
            NsRuntimePayloadRefValidationUnavailableError,
        )
        startup_error = NsRuntimeStartupSecurityError()
        self.assertIsInstance(startup_error, NsConfigError)
        self.assertNotIsInstance(startup_error, NsRuntimeError)


class NsErrorMetadataRegistryTestCase(unittest.TestCase):

    def test_definition_validation_is_strict(self) -> None:
        valid = make_definition(NsValidationError)
        self.assertEqual("NS_VALIDATION_ERROR", valid.code)
        with self.assertRaises(TypeError):
            NsErrorDefinition.for_error_type(
                object,  # type: ignore[arg-type]
                severity=NsErrorSeverity.ERROR,
                category=NsErrorCategory.COMMON,
                action="report_error",
            )

        invalid_values = (
            {"error_type": object},
            {"code": ""},
            {"code": "OTHER_CODE"},
            {"numeric_code": True},
            {"numeric_code": 0},
            {"numeric_code": 900002},
            {"severity": "error"},
            {"category": "common"},
            {"retryable": 1},
            {"disconnect_required": None},
            {"audit_required": "false"},
            {"safe_detail": 0},
            {"action": ""},
            {"action": "Retry Error"},
        )
        for overrides in invalid_values:
            with self.subTest(overrides=overrides):
                with self.assertRaises((TypeError, ValueError)):
                    make_definition(NsValidationError, **overrides)

    def test_registry_is_complete_unique_queryable_and_json_safe(self) -> None:
        definitions = list_error_definitions()
        self.assertIs(ALL_ERROR_DEFINITIONS, definitions)
        self.assertEqual(33, len(definitions))
        self.assertEqual(33, len({item.error_type for item in definitions}))
        self.assertEqual(33, len({item.code for item in definitions}))
        self.assertEqual(33, len({item.numeric_code for item in definitions}))

        validate_error_registry()
        for definition in definitions:
            with self.subTest(code=definition.code):
                self.assertIs(
                    definition,
                    get_error_definition(definition.error_type),
                )
                self.assertIs(
                    definition,
                    get_error_definition_by_code(definition.code),
                )
                self.assertIs(
                    definition,
                    get_error_definition_by_numeric_code(
                        definition.numeric_code
                    ),
                )
                self.assertEqual(definition.code, definition.error_type.code)
                self.assertEqual(
                    definition.numeric_code,
                    definition.error_type.numeric_code,
                )
                self.assertIsInstance(definition.severity, NsErrorSeverity)
                self.assertIsInstance(definition.category, NsErrorCategory)

        self.assertIsNone(get_error_definition(type("UnknownError", (NsEvermoreError,), {})))
        self.assertIsNone(get_error_definition_by_code("UNKNOWN"))
        self.assertIsNone(get_error_definition_by_numeric_code(999999))
        json.dumps(ERROR_REGISTRY.to_dict(), allow_nan=False)

    def test_every_public_exception_class_has_one_definition(self) -> None:
        registered_types = {definition.error_type for definition in ALL_ERROR_DEFINITIONS}
        public_error_types = {
            getattr(exceptions_facade, name)
            for name in exceptions_facade.__all__
            if name.startswith("Ns")
            and isinstance(getattr(exceptions_facade, name), type)
            and issubclass(getattr(exceptions_facade, name), NsEvermoreError)
        }
        self.assertEqual(
            {getattr(exceptions_facade, name) for name in EXCEPTION_SNAPSHOTS},
            public_error_types,
        )
        self.assertEqual(public_error_types, registered_types)

    def test_registry_rejects_duplicate_class_code_and_numeric_code(self) -> None:
        validation_definition = make_definition(NsValidationError)
        with self.assertRaisesRegex(ValueError, "duplicate error type"):
            NsErrorRegistry((validation_definition, validation_definition))

        class DuplicateCodeError(NsEvermoreError):
            code = NsValidationError.code
            numeric_code = 900010

        duplicate_code_definition = make_definition(DuplicateCodeError)
        with self.assertRaisesRegex(ValueError, "duplicate error code"):
            NsErrorRegistry((validation_definition, duplicate_code_definition))

        class DuplicateNumericCodeError(NsEvermoreError):
            code = "DUPLICATE_NUMERIC_CODE"
            numeric_code = NsValidationError.numeric_code

        duplicate_numeric_definition = make_definition(DuplicateNumericCodeError)
        with self.assertRaisesRegex(ValueError, "duplicate numeric error code"):
            NsErrorRegistry((validation_definition, duplicate_numeric_definition))

        with self.assertRaises(TypeError):
            NsErrorRegistry((object(),))  # type: ignore[arg-type]

    def test_registry_and_definitions_are_immutable(self) -> None:
        definition = get_error_definition(NsValidationError)
        self.assertIsNotNone(definition)
        assert definition is not None
        with self.assertRaises(FrozenInstanceError):
            definition.action = "mutate"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            ERROR_REGISTRY._definitions = ()  # type: ignore[misc]
        with self.assertRaises(TypeError):
            ERROR_REGISTRY._by_code["OTHER"] = definition  # type: ignore[index]

    def test_registry_validation_detects_later_class_metadata_drift(self) -> None:
        class MutableMetadataError(NsEvermoreError):
            code = "MUTABLE_METADATA"
            numeric_code = 900020

        definition = make_definition(MutableMetadataError)
        registry = NsErrorRegistry((definition,))
        MutableMetadataError.code = "CHANGED_METADATA"
        with self.assertRaisesRegex(ValueError, "current error_type.code"):
            registry.validate()

    def test_registry_metadata_never_serializes_error_details_or_string(self) -> None:
        secret = "registry-detail-secret"

        class ExplodingStringError(NsEvermoreError):
            def __str__(self) -> str:
                raise RuntimeError("registry-string-secret")

        error = ExplodingStringError(details={"secret": secret})
        self.assertIsNone(get_error_definition(type(error)))
        serialized = json.dumps(ERROR_REGISTRY.to_dict(), allow_nan=False)
        self.assertNotIn(secret, serialized)
        self.assertNotIn("registry-string-secret", serialized)

    def test_nack_mapping_is_stable_complete_and_validated(self) -> None:
        expected_reasons = (
            "target_overloaded",
            "temporarily_unavailable",
            "queue_full",
            "dependency_unavailable",
            "target_draining",
            "node_degraded",
            "permission_denied",
            "tenant_mismatch",
            "invalid_payload_ref",
            "payload_ref_denied",
            "source_forged",
            "auth_context_forged",
            "protocol_violation",
        )
        self.assertEqual(
            expected_reasons,
            tuple(reason for reason, _ in RUNTIME_NACK_REASON_ERROR_CODES),
        )
        self.assertEqual(
            len(RUNTIME_NACK_REASON_ERROR_CODES),
            len({reason for reason, _ in RUNTIME_NACK_REASON_ERROR_CODES}),
        )
        self.assertIs(
            RUNTIME_NACK_REASON_ERROR_CODES,
            validate_runtime_nack_reason_error_codes(),
        )
        for _, code in RUNTIME_NACK_REASON_ERROR_CODES:
            self.assertIsNotNone(get_error_definition_by_code(code))

        invalid_mappings = (
            (("", NsValidationError.code),),
            (("duplicate", NsValidationError.code), ("duplicate", NsConfigError.code)),
            (("unknown", "UNREGISTERED_CODE"),),
            (("missing_code", ""),),
        )
        for entries in invalid_mappings:
            with self.subTest(entries=entries):
                with self.assertRaises((TypeError, ValueError)):
                    validate_runtime_nack_reason_error_codes(entries)


if __name__ == "__main__":
    unittest.main()
