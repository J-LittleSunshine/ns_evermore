# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_runtime.auth_provider import (
    NsRuntimeAuthProviderError,
    NsRuntimeRemoteIamAuthProvider,
    NsRuntimeStaticAuthProvider,
    build_runtime_auth_provider,
)
from ns_runtime.connection import NsRuntimeConnection
from ns_runtime.core import NsRuntimeNode, NsRuntimeNodeStats
from ns_runtime.delivery import NsRuntimeDeliveryResult, NsRuntimeLocalDelivery
from ns_runtime.dispatcher import NsRuntimeDispatcher
from ns_runtime.presence import (
    MemoryRuntimePresenceStore,
    NsRuntimePresenceRecord,
    NsRuntimePresenceStore,
    build_runtime_presence_store,
)
from ns_runtime.protocol import NsRuntimeWireFrame
from ns_runtime.registry import NsRuntimeConnectionRegistry

if TYPE_CHECKING:
    pass

__all__ = [
    "MemoryRuntimePresenceStore",
    "NsRuntimeAuthProviderError",
    "NsRuntimeConnection",
    "NsRuntimeConnectionRegistry",
    "NsRuntimeDeliveryResult",
    "NsRuntimeDispatcher",
    "NsRuntimeLocalDelivery",
    "NsRuntimeNode",
    "NsRuntimeNodeStats",
    "NsRuntimePresenceRecord",
    "NsRuntimePresenceStore",
    "NsRuntimeRemoteIamAuthProvider",
    "NsRuntimeStaticAuthProvider",
    "NsRuntimeWireFrame",
    "build_runtime_auth_provider",
    "build_runtime_presence_store",
]
