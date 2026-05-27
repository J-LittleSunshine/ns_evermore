# -*- coding: utf-8 -*-
from __future__ import annotations

from enum import Enum


class RuntimePacketType(str, Enum):
    REGISTER = "REGISTER"
    HEARTBEAT = "HEARTBEAT"
    COMMAND = "COMMAND"
    EVENT = "EVENT"
    TASK = "TASK"
    RESULT = "RESULT"
    ERROR = "ERROR"
    SYSTEM = "SYSTEM"


class RuntimeEndpointType(str, Enum):
    RUNTIME = "RUNTIME"
    CONTROL = "CONTROL"
    EXECUTOR = "EXECUTOR"
    FRONTEND = "FRONTEND"
    ADMIN = "ADMIN"
    SERVICE = "SERVICE"
    UNKNOWN = "UNKNOWN"


class RuntimeEndpointStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class RuntimeServiceState(str, Enum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"

