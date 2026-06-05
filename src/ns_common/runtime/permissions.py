# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Final

# Runtime principal types.
RUNTIME_PRINCIPAL_FRONTEND_USER: Final[str] = "frontend_user"
RUNTIME_PRINCIPAL_BACKEND_SERVICE: Final[str] = "backend_service"
RUNTIME_PRINCIPAL_RUNTIME_NODE: Final[str] = "runtime_node"
RUNTIME_PRINCIPAL_ANONYMOUS_FRONTEND: Final[str] = "anonymous_frontend"

# IAM resource types used by runtime authorization.
RUNTIME_IAM_RESOURCE_FRONTEND: Final[str] = "runtime.frontend"
RUNTIME_IAM_RESOURCE_BACKEND: Final[str] = "runtime.backend"
RUNTIME_IAM_RESOURCE_NODE: Final[str] = "runtime.node"
RUNTIME_IAM_RESOURCE_ROOM: Final[str] = "runtime.room"
RUNTIME_IAM_RESOURCE_MESSAGE: Final[str] = "runtime.message"
RUNTIME_IAM_RESOURCE_TOPIC: Final[str] = "runtime.topic"
RUNTIME_IAM_RESOURCE_CONNECTION: Final[str] = "runtime.connection"

# IAM action codes used by runtime authorization.
RUNTIME_IAM_ACTION_CONNECT: Final[str] = "connect"
RUNTIME_IAM_ACTION_HEARTBEAT: Final[str] = "heartbeat"
RUNTIME_IAM_ACTION_ACK: Final[str] = "ack"
RUNTIME_IAM_ACTION_PUBLISH: Final[str] = "publish"
RUNTIME_IAM_ACTION_SUBSCRIBE: Final[str] = "subscribe"
RUNTIME_IAM_ACTION_JOIN: Final[str] = "join"
RUNTIME_IAM_ACTION_LEAVE: Final[str] = "leave"
RUNTIME_IAM_ACTION_RECEIVE: Final[str] = "receive"
RUNTIME_IAM_ACTION_REPLY: Final[str] = "reply"
RUNTIME_IAM_ACTION_FORWARD: Final[str] = "forward"

RUNTIME_IAM_RESOURCE_TYPES: Final[tuple[str, ...]] = (
    RUNTIME_IAM_RESOURCE_FRONTEND,
    RUNTIME_IAM_RESOURCE_BACKEND,
    RUNTIME_IAM_RESOURCE_NODE,
    RUNTIME_IAM_RESOURCE_ROOM,
    RUNTIME_IAM_RESOURCE_MESSAGE,
    RUNTIME_IAM_RESOURCE_TOPIC,
    RUNTIME_IAM_RESOURCE_CONNECTION,
)

RUNTIME_IAM_ACTION_CODES: Final[tuple[str, ...]] = (
    RUNTIME_IAM_ACTION_CONNECT,
    RUNTIME_IAM_ACTION_HEARTBEAT,
    RUNTIME_IAM_ACTION_ACK,
    RUNTIME_IAM_ACTION_PUBLISH,
    RUNTIME_IAM_ACTION_SUBSCRIBE,
    RUNTIME_IAM_ACTION_JOIN,
    RUNTIME_IAM_ACTION_LEAVE,
    RUNTIME_IAM_ACTION_RECEIVE,
    RUNTIME_IAM_ACTION_REPLY,
    RUNTIME_IAM_ACTION_FORWARD,
)

# Common permission codes derived from IAM resource type and action code.
RUNTIME_PERMISSION_FRONTEND_CONNECT: Final[str] = "runtime:frontend:connect"
RUNTIME_PERMISSION_FRONTEND_HEARTBEAT: Final[str] = "runtime:frontend:heartbeat"
RUNTIME_PERMISSION_FRONTEND_ACK: Final[str] = "runtime:frontend:ack"
RUNTIME_PERMISSION_BACKEND_CONNECT: Final[str] = "runtime:backend:connect"
RUNTIME_PERMISSION_BACKEND_RECEIVE: Final[str] = "runtime:backend:receive"
RUNTIME_PERMISSION_NODE_CONNECT: Final[str] = "runtime:node:connect"
RUNTIME_PERMISSION_NODE_FORWARD: Final[str] = "runtime:node:forward"
RUNTIME_PERMISSION_ROOM_JOIN: Final[str] = "runtime:room:join"
RUNTIME_PERMISSION_ROOM_LEAVE: Final[str] = "runtime:room:leave"
RUNTIME_PERMISSION_MESSAGE_PUBLISH: Final[str] = "runtime:message:publish"
RUNTIME_PERMISSION_MESSAGE_REPLY: Final[str] = "runtime:message:reply"
RUNTIME_PERMISSION_MESSAGE_FORWARD: Final[str] = "runtime:message:forward"
RUNTIME_PERMISSION_TOPIC_SUBSCRIBE: Final[str] = "runtime:topic:subscribe"


def normalize_runtime_iam_resource_type(value: Any) -> str:
    """Normalize runtime IAM resource type."""
    resource_type: str = str(value or "").strip().lower()
    return resource_type


def normalize_runtime_iam_action_code(value: Any) -> str:
    """Normalize runtime IAM action code."""
    action_code: str = str(value or "").strip().lower()
    return action_code


def build_runtime_permission_code(*, resource_type: str, action_code: str) -> str:
    """Build IAM permission code from runtime IAM resource/action.

    This mirrors the current IAM convention:
    runtime.message + publish -> runtime:message:publish
    """
    normalized_resource_type = normalize_runtime_iam_resource_type(resource_type)
    normalized_action_code = normalize_runtime_iam_action_code(action_code)
    return f"{normalized_resource_type.replace('.', ':')}:{normalized_action_code}"


def build_runtime_frontend_resource_id(*, user_id: str | int | None = None, client_id: str | None = None) -> str:
    """Build runtime.frontend resource id."""
    normalized_user_id = _normalize_optional(user_id)
    if normalized_user_id is not None:
        return f"user:{normalized_user_id}"

    normalized_client_id = _normalize_optional(client_id)
    if normalized_client_id is not None:
        return f"client:{normalized_client_id}"

    return "anonymous:*"


def build_runtime_backend_resource_id(backend_id: str | None) -> str:
    """Build runtime.backend resource id."""
    normalized_backend_id = _normalize_optional(backend_id)
    return f"backend:{normalized_backend_id or '*'}"


def build_runtime_node_resource_id(node_id: str | None) -> str:
    """Build runtime.node resource id."""
    normalized_node_id = _normalize_optional(node_id)
    return f"node:{normalized_node_id or '*'}"


def build_runtime_room_resource_id(room_id: str | None) -> str:
    """Build runtime.room resource id."""
    normalized_room_id = _normalize_optional(room_id)
    return f"room:{normalized_room_id or '*'}"


def build_runtime_topic_resource_id(topic: str | None) -> str:
    """Build runtime.topic resource id."""
    normalized_topic = _normalize_optional(topic)
    return f"topic:{normalized_topic or '*'}"


def build_runtime_message_resource_id(topic: str | None = None) -> str:
    """Build runtime.message resource id.

    Runtime message authorization is topic-scoped by default.
    """
    normalized_topic = _normalize_optional(topic)
    return f"topic:{normalized_topic or '*'}"


def build_runtime_connection_resource_id(connection_id: str | None) -> str:
    """Build runtime.connection resource id."""
    normalized_connection_id = _normalize_optional(connection_id)
    return f"connection:{normalized_connection_id or '*'}"


def build_runtime_iam_authorize_payload(
        *,
        resource_type: str,
        resource_id: str,
        action_code: str,
        context: dict[str, Any] | None = None,
        permission_code: str | None = None,
) -> dict[str, Any]:
    """Build payload compatible with IAM AuthorizeService.check()."""
    normalized_resource_type = normalize_runtime_iam_resource_type(resource_type)
    normalized_action_code = normalize_runtime_iam_action_code(action_code)
    normalized_permission_code = _normalize_optional(permission_code)

    payload: dict[str, Any] = {
        "resource_type": normalized_resource_type,
        "resource_id": str(resource_id or "").strip(),
        "action_code": normalized_action_code,
        "context": dict(context or {}),
    }

    if normalized_permission_code is not None:
        payload["permission_code"] = normalized_permission_code

    return payload


def build_runtime_connect_authorize_payload(
        *,
        principal_type: str,
        principal_id: str | None,
        resource_type: str,
        resource_id: str,
        context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build IAM authorization payload for runtime connect actions."""
    merged_context = dict(context or {})
    merged_context.setdefault("principal_type", str(principal_type or "").strip())
    merged_context.setdefault("principal_id", str(principal_id or "").strip() if principal_id is not None else None)

    return build_runtime_iam_authorize_payload(
        resource_type=resource_type,
        resource_id=resource_id,
        action_code=RUNTIME_IAM_ACTION_CONNECT,
        context=merged_context,
    )


def _normalize_optional(value: Any) -> str | None:
    """Normalize optional string value."""
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None
