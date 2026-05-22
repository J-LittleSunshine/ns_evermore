# -*- coding: utf-8 -*-
from __future__ import annotations


class NsLogEvent:
    LOGIN_FAILURE_CLEAR_FAILED = "login_failure_clear_failed"
    REFRESH_ROTATION_REJECTED = "refresh_rotation_rejected"
    REFRESH_REPLAY_DETECTED = "refresh_replay_detected"
    AUDIT_RECORD_FAILED = "audit_record_failed"


SENSITIVE_LOG_KEYS = {
    "password",
    "old_password",
    "new_password",
    "confirm_password",
    "oldpassword",
    "newpassword",
    "confirmpassword",
    "access_token",
    "refresh_token",
    "authorization",
    "bearer",
    "jwt",
    "jwt_token",
    "token",
    "authtoken",
    "secret",
    "secret_key",
    "secretkey",
    "private_key",
    "privatekey",
    "client_secret",
    "api_key",
    "csrf",
    "csrf_token",
    "csrftoken",
    "accesstoken",
    "refreshtoken",
    "auth_token",
    "session_token",
    "sessiontoken",
    "clientsecret",
    "apikey",
}


__all__ = ["NsLogEvent", "SENSITIVE_LOG_KEYS"]

