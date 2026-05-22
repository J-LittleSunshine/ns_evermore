# -*- coding: utf-8 -*-
from __future__ import annotations


class NsLogEvent:
    LOGIN_FAILURE_CLEAR_FAILED = "login_failure_clear_failed"
    REFRESH_ROTATION_REJECTED = "refresh_rotation_rejected"
    REFRESH_REPLAY_DETECTED = "refresh_replay_detected"
    AUDIT_RECORD_FAILED = "audit_record_failed"


SENSITIVE_LOG_KEYS = {
    "password",
    "access_token",
    "refresh_token",
    "authorization",
    "token",
    "secret",
    "client_secret",
    "api_key",
    "accesstoken",
    "refreshtoken",
    "auth_token",
    "session_token",
    "sessiontoken",
    "clientsecret",
    "apikey",
}


__all__ = ["NsLogEvent", "SENSITIVE_LOG_KEYS"]

