# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Final, Protocol, AsyncIterator

from ns_common.runtime.messages import NsRuntimeMessage, NsRuntimeAck

if TYPE_CHECKING:
    pass

RUNTIME_NODE_ROLE_STANDALONE: Final[str] = "standalone"
RUNTIME_NODE_ROLE_MASTER: Final[str] = "master"
RUNTIME_NODE_ROLE_SUB: Final[str] = "sub"

RUNTIME_BACKEND_SQL_WAL: Final[str] = "sql_wal"
RUNTIME_BACKEND_MEMORY: Final[str] = "memory"
RUNTIME_BACKEND_REDIS: Final[str] = "redis"
RUNTIME_BACKEND_VALKEY: Final[str] = "valkey"
RUNTIME_BACKEND_MQ: Final[str] = "mq"

RUNTIME_MESSAGE_STATUS_PENDING: Final[str] = "PENDING"
RUNTIME_MESSAGE_STATUS_SENDING: Final[str] = "SENDING"
RUNTIME_MESSAGE_STATUS_ACKED: Final[str] = "ACKED"
RUNTIME_MESSAGE_STATUS_RETRY: Final[str] = "RETRY"
RUNTIME_MESSAGE_STATUS_DEAD: Final[str] = "DEAD"

RUNTIME_ACK_STATUS_RECEIVED: Final[str] = "received"
RUNTIME_ACK_STATUS_ACCEPTED: Final[str] = "accepted"
RUNTIME_ACK_STATUS_FORWARDED: Final[str] = "forwarded"
RUNTIME_ACK_STATUS_DELIVERED: Final[str] = "delivered"
RUNTIME_ACK_STATUS_REJECTED: Final[str] = "rejected"

RUNTIME_PRODUCER_FRONTEND: Final[str] = "frontend"
RUNTIME_PRODUCER_BACKEND: Final[str] = "backend"
RUNTIME_PRODUCER_RUNTIME: Final[str] = "runtime"
RUNTIME_PRODUCER_BUSINESS_CLIENT: Final[str] = "business_client"

RUNTIME_TARGET_USER: Final[str] = "user"
RUNTIME_TARGET_SESSION: Final[str] = "session"
RUNTIME_TARGET_CONNECTION: Final[str] = "connection"
RUNTIME_TARGET_ROOM: Final[str] = "room"
RUNTIME_TARGET_BROADCAST: Final[str] = "broadcast"
RUNTIME_TARGET_RESOURCE: Final[str] = "resource"

RUNTIME_CONNECTOR_IPC_UNIX_SOCKET: Final[str] = "unix_socket"
RUNTIME_CONNECTOR_IPC_TCP: Final[str] = "tcp"
RUNTIME_CONNECTOR_IPC_MEMORY: Final[str] = "memory"

RUNTIME_MASTER_FORWARD_LOCAL_FIRST: Final[str] = "local_first"
RUNTIME_MASTER_FORWARD_SUB_FIRST: Final[str] = "sub_first"
RUNTIME_MASTER_FORWARD_SUB_REQUIRED: Final[str] = "sub_required"


