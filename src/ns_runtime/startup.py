# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Literal,
    cast
)

from ns_common.exceptions import (
    NsRuntimeStartupSecurityError,
)
from ns_runtime.auth import (
    LocalTokenRuntimeAuthenticator,
    RuntimeAuthenticator,
)

RuntimeEnvironment = Literal[
    "development",
    "test",
    "production",
]

DEFAULT_LOCAL_DEVELOPMENT_TOKEN = (
    "local-dev-token"
)

_RUNTIME_ENVIRONMENTS: frozenset[str] = (
    frozenset(
        {
            "development",
            "test",
            "production",
        }
    )
)


def normalize_runtime_environment(
        value: str,
) -> RuntimeEnvironment:
    if not isinstance(value, str):
        raise TypeError(
            "runtime environment must be str."
        )

    resolved_value = value.strip().lower()

    if resolved_value not in _RUNTIME_ENVIRONMENTS:
        raise NsRuntimeStartupSecurityError(
            "Runtime environment is invalid.",
            details={
                "runtime_environment": (
                        resolved_value
                        or "<empty>"
                ),
                "allowed_values": sorted(
                    _RUNTIME_ENVIRONMENTS
                ),
            },
        )

    return cast(
        RuntimeEnvironment,
        resolved_value,
    )


def validate_runtime_startup_security(
        *,
        environment: str,
        authenticator: RuntimeAuthenticator,
) -> RuntimeEnvironment:
    if not isinstance(
            authenticator,
            RuntimeAuthenticator,
    ):
        raise TypeError(
            "authenticator must be "
            "RuntimeAuthenticator."
        )

    resolved_environment = (
        normalize_runtime_environment(
            environment
        )
    )

    if (
            resolved_environment
            == "production"
            and isinstance(
        authenticator,
        LocalTokenRuntimeAuthenticator,
    )
    ):
        raise NsRuntimeStartupSecurityError(
            (
                "Production runtime must not use "
                "local token authentication."
            ),
            details={
                "runtime_environment": (
                    resolved_environment
                ),
                "authenticator_class": (
                    authenticator
                    .__class__
                    .__name__
                ),
            },
        )

    return resolved_environment
