# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Literal

RuntimeMessageType = Literal[
    "request",
    "response",
    "event",
    "error",
    "heartbeat",
    "register",
    "unregister",
    "control",
]

RuntimeReplyMode = Literal[
    "sync",
    "async",
    "none",
]

RuntimeDeliveryMode = Literal[
    "at_most_once",
    "at_least_once",
]

RuntimeBackpressurePolicy = Literal[
    "reject",
    "queue",
    "timeout_queue",
]

RuntimeClientType = Literal[
    "ns_frontend",
    "ns_node",
    "ns_client",
    "sub_node",
    "biz_client",
]

RuntimeTargetType = Literal[
    "ns_frontend",
    "ns_node",
    "ns_client",
    "sub_node",
    "biz_client",
]

RUNTIME_PROTOCOL_VERSION = "1.0"

MESSAGE_TYPE_REQUEST = "request"
MESSAGE_TYPE_RESPONSE = "response"
MESSAGE_TYPE_EVENT = "event"
MESSAGE_TYPE_ERROR = "error"
MESSAGE_TYPE_HEARTBEAT = "heartbeat"
MESSAGE_TYPE_REGISTER = "register"
MESSAGE_TYPE_UNREGISTER = "unregister"
MESSAGE_TYPE_CONTROL = "control"

REPLY_MODE_SYNC = "sync"
REPLY_MODE_ASYNC = "async"
REPLY_MODE_NONE = "none"

DELIVERY_MODE_AT_MOST_ONCE = "at_most_once"
DELIVERY_MODE_AT_LEAST_ONCE = "at_least_once"

BACKPRESSURE_REJECT = "reject"
BACKPRESSURE_QUEUE = "queue"
BACKPRESSURE_TIMEOUT_QUEUE = "timeout_queue"

CLIENT_TYPE_NS_FRONTEND = "ns_frontend"
CLIENT_TYPE_NS_NODE = "ns_node"
CLIENT_TYPE_NS_CLIENT = "ns_client"
CLIENT_TYPE_SUB_NODE = "sub_node"
CLIENT_TYPE_BIZ_CLIENT = "biz_client"

SUPPORTED_MESSAGE_TYPES: set[str] = {
    MESSAGE_TYPE_REQUEST,
    MESSAGE_TYPE_RESPONSE,
    MESSAGE_TYPE_EVENT,
    MESSAGE_TYPE_ERROR,
    MESSAGE_TYPE_HEARTBEAT,
    MESSAGE_TYPE_REGISTER,
    MESSAGE_TYPE_UNREGISTER,
    MESSAGE_TYPE_CONTROL,
}

SUPPORTED_REPLY_MODES: set[str] = {
    REPLY_MODE_SYNC,
    REPLY_MODE_ASYNC,
    REPLY_MODE_NONE,
}

SUPPORTED_DELIVERY_MODES: set[str] = {
    DELIVERY_MODE_AT_MOST_ONCE,
    DELIVERY_MODE_AT_LEAST_ONCE,
}

SUPPORTED_BACKPRESSURE_POLICIES: set[str] = {
    BACKPRESSURE_REJECT,
    BACKPRESSURE_QUEUE,
    BACKPRESSURE_TIMEOUT_QUEUE,
}

SUPPORTED_CLIENT_TYPES: set[str] = {
    CLIENT_TYPE_NS_FRONTEND,
    CLIENT_TYPE_NS_NODE,
    CLIENT_TYPE_NS_CLIENT,
    CLIENT_TYPE_SUB_NODE,
    CLIENT_TYPE_BIZ_CLIENT,
}

SUPPORTED_TARGET_TYPES: set[str] = {
    CLIENT_TYPE_NS_FRONTEND,
    CLIENT_TYPE_NS_NODE,
    CLIENT_TYPE_NS_CLIENT,
    CLIENT_TYPE_SUB_NODE,
    CLIENT_TYPE_BIZ_CLIENT,
}
