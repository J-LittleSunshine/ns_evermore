# -*- coding: utf-8 -*-
from __future__ import annotations


class NsLogEvent:
    SYSTEM_EXCEPTION = "system.exception"
    DJANGO_REQUEST_EXCEPTION = "django.request.exception"

    IAM_LOGIN_SUCCESS = "iam.login.success"
    IAM_LOGIN_FAILED = "iam.login.failed"
    IAM_REFRESH_REJECTED = "iam.refresh.rejected"
    IAM_REFRESH_REPLAY_DETECTED = "iam.refresh.replay_detected"
    IAM_AUDIT_RECORD_FAILED = "iam.audit.record_failed"

    WEBSOCKET_CONNECT = "websocket.connect"
    WEBSOCKET_ACCEPT = "websocket.accept"
    WEBSOCKET_RECEIVE = "websocket.receive"
    WEBSOCKET_SEND = "websocket.send"
    WEBSOCKET_DISCONNECT = "websocket.disconnect"
    WEBSOCKET_ERROR = "websocket.error"
    DATABASE_LOG_SINK_WRITE = "database.log_sink.write"
    DATABASE_LOG_SINK_FAILED = "database.log_sink.failed"


SENSITIVE_LOG_KEYS = {
    "password",
    "password_payload",
    "passwordpayload",
    "raw_password",
    "rawpassword",
    "encrypted_password",
    "encryptedpassword",
    "password_ciphertext",
    "passwordciphertext",
    "ciphertext",
    "plain_text",
    "plaintext",
    "decrypted_password",
    "decryptedpassword",
    "password_plaintext",
    "passwordplaintext",
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
    "rsa_private_key",
    "rsaprivatekey",
    "rsa_private_key_file",
    "rsaprivatekeyfile",
    "rsa_private_key_passphrase",
    "rsaprivatekeypassphrase",
    "private_key_file",
    "privatekeyfile",
    "private_key_pem",
    "privatekeypem",
    "key_passphrase",
    "keypassphrase",
    "passphrase",
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

