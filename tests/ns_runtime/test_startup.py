# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from ns_common.exceptions import (
    NsRuntimeStartupSecurityError,
)
from ns_runtime.auth import (
    LocalTokenRuntimeAuthenticator,
    RuntimeAuthResult,
    RuntimeAuthenticator
)
from ns_runtime.main import (
    _read_runtime_environment_env,
)
from ns_runtime.service import RuntimeService
from ns_runtime.startup import (
    DEFAULT_LOCAL_DEVELOPMENT_TOKEN,
    normalize_runtime_environment,
    validate_runtime_startup_security,
)


class _ExternalRuntimeAuthenticator(
    RuntimeAuthenticator
):
    async def authenticate_connection_hello(
            self,
            hello,
            *,
            connection_id: str,
            remote_address: str,
    ) -> RuntimeAuthResult:
        del hello
        del connection_id
        del remote_address

        return RuntimeAuthResult.reject(
            code="TEST_AUTH_REJECTED",
            reason="Not used by startup tests.",
        )


class RuntimeStartupSecurityTestCase(
    unittest.TestCase
):
    def test_environment_normalization_is_case_insensitive(
            self,
    ) -> None:
        self.assertEqual(
            normalize_runtime_environment(
                "  PRODUCTION  "
            ),
            "production",
        )

    def test_invalid_environment_is_rejected(
            self,
    ) -> None:
        with self.assertRaises(
                NsRuntimeStartupSecurityError
        ) as raised:
            normalize_runtime_environment(
                "staging"
            )

        self.assertEqual(
            raised.exception.code,
            "RUNTIME_STARTUP_SECURITY_ERROR",
        )

    def test_non_production_allows_local_authenticator(
            self,
    ) -> None:
        authenticator = (
            LocalTokenRuntimeAuthenticator(
                expected_token=(
                    DEFAULT_LOCAL_DEVELOPMENT_TOKEN
                )
            )
        )

        for environment in (
                "development",
                "test",
        ):
            with self.subTest(
                    environment=environment
            ):
                resolved = (
                    validate_runtime_startup_security(
                        environment=environment,
                        authenticator=authenticator,
                    )
                )

                self.assertEqual(
                    resolved,
                    environment,
                )

    def test_production_rejects_any_local_token_authenticator(
            self,
    ) -> None:
        sensitive_token = (
            "production-secret-must-not-leak"
        )

        authenticator = (
            LocalTokenRuntimeAuthenticator(
                expected_token=sensitive_token
            )
        )

        with self.assertRaises(
                NsRuntimeStartupSecurityError
        ) as raised:
            validate_runtime_startup_security(
                environment="production",
                authenticator=authenticator,
            )

        self.assertEqual(
            raised.exception.code,
            "RUNTIME_STARTUP_SECURITY_ERROR",
        )
        self.assertEqual(
            raised.exception.details,
            {
                "runtime_environment": (
                    "production"
                ),
                "authenticator_class": (
                    "LocalTokenRuntimeAuthenticator"
                ),
            },
        )
        self.assertNotIn(
            sensitive_token,
            str(raised.exception.to_dict()),
        )

    def test_service_production_rejects_implicit_default_authenticator(
            self,
    ) -> None:
        with self.assertRaises(
                NsRuntimeStartupSecurityError
        ):
            RuntimeService.build_default(
                runtime_id="runtime-test",
                runtime_environment="production",
            )

    def test_service_production_accepts_external_authenticator(
            self,
    ) -> None:
        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            runtime_environment="production",
            authenticator=(
                _ExternalRuntimeAuthenticator()
            ),
        )

        self.assertEqual(
            service.runtime_environment,
            "production",
        )

    def test_cli_environment_defaults_to_production(
            self,
    ) -> None:
        with patch.dict(
                os.environ,
                {},
                clear=True,
        ):
            self.assertEqual(
                _read_runtime_environment_env(),
                "production",
            )

    def test_cli_environment_accepts_explicit_development(
            self,
    ) -> None:
        with patch.dict(
                os.environ,
                {
                    "NS_RUNTIME_ENVIRONMENT": (
                            "development"
                    ),
                },
                clear=True,
        ):
            self.assertEqual(
                _read_runtime_environment_env(),
                "development",
            )


if __name__ == "__main__":
    unittest.main()
