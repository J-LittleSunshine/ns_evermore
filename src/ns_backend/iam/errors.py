# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common import NsEvermoreError

if TYPE_CHECKING:
    pass


class IamError(NsEvermoreError):
    code = "IAM_ERROR"
    numeric_code = 200000
    default_message = "IAM error."


class IamAuthError(IamError):
    code = "IAM_AUTH_ERROR"
    numeric_code = 200100
    default_message = "IAM authentication error."


class IamUsernameEmptyError(IamAuthError):
    code = "IAM_USERNAME_EMPTY"
    numeric_code = 200101
    default_message = "Username cannot be empty."


class IamPasswordEmptyError(IamAuthError):
    code = "IAM_PASSWORD_EMPTY"
    numeric_code = 200102
    default_message = "Password cannot be empty."


class IamCredentialInvalidError(IamAuthError):
    code = "IAM_USERNAME_OR_PASSWORD_INCORRECT"
    numeric_code = 200103
    default_message = "Username or password is incorrect."


class IamAccountLockedError(IamAuthError):
    code = "IAM_ACCOUNT_LOCKED"
    numeric_code = 200104
    default_message = "Account is locked."


class IamUserDisabledOrNotFoundError(IamAuthError):
    code = "IAM_USER_DISABLED_OR_NOT_FOUND"
    numeric_code = 200105
    default_message = "User is disabled or not found."


class IamRefreshTokenEmptyError(IamAuthError):
    code = "IAM_REFRESH_TOKEN_EMPTY"
    numeric_code = 200106
    default_message = "Refresh token cannot be empty."


class IamRefreshTokenInvalidOrExpiredError(IamAuthError):
    code = "IAM_REFRESH_TOKEN_INVALID_OR_EXPIRED"
    numeric_code = 200107
    default_message = "Refresh token is invalid or expired."


class IamRefreshTokenReplayDetectedError(IamAuthError):
    code = "IAM_REFRESH_TOKEN_REPLAY_DETECTED"
    numeric_code = 200108
    default_message = "Refresh token replay detected."


class IamRefreshTokenUserMismatchError(IamAuthError):
    code = "IAM_REFRESH_TOKEN_USER_MISMATCH"
    numeric_code = 200109
    default_message = "Refresh token user mismatch."


class IamPasswordTransportError(IamAuthError):
    code = "IAM_PASSWORD_TRANSPORT_ERROR"
    numeric_code = 200120
    default_message = "Password transport error."


class IamPasswordTransportConfigError(IamPasswordTransportError):
    code = "IAM_PASSWORD_TRANSPORT_CONFIG_ERROR"
    numeric_code = 200121
    default_message = "Password transport configuration is invalid."


class IamPasswordTransportInvalidError(IamPasswordTransportError):
    code = "IAM_PASSWORD_TRANSPORT_INVALID"
    numeric_code = 200122
    default_message = "Password transport payload is invalid."


class IamPasswordTransportDecryptFailedError(IamPasswordTransportError):
    code = "IAM_PASSWORD_TRANSPORT_DECRYPT_FAILED"
    numeric_code = 200123
    default_message = "Password transport decrypt failed."


class IamUserNotLoggedInOrSessionExpiredError(IamAuthError):
    code = "IAM_USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED"
    numeric_code = 200110
    default_message = "User is not logged in or session has expired."


class IamLoginFailureUpdateFailedError(IamAuthError):
    code = "IAM_LOGIN_FAILURE_UPDATE_FAILED"
    numeric_code = 200130
    default_message = "Failed to update login failure counter."


class IamManagementError(IamError):
    code = "IAM_MANAGEMENT_ERROR"
    numeric_code = 200200
    default_message = "IAM management error."


class IamManagementRequestInvalidError(IamManagementError):
    code = "IAM_MANAGEMENT_REQUEST_INVALID"
    numeric_code = 200201
    default_message = "IAM management request is invalid."


class IamResourceNotFoundError(IamManagementError):
    code = "IAM_RESOURCE_NOT_FOUND"
    numeric_code = 200202
    default_message = "IAM resource was not found."


class IamResourceAlreadyExistsError(IamManagementError):
    code = "IAM_RESOURCE_ALREADY_EXISTS"
    numeric_code = 200203
    default_message = "IAM resource already exists."


class IamResourceInUseError(IamManagementError):
    code = "IAM_RESOURCE_IN_USE"
    numeric_code = 200204
    default_message = "IAM resource is in use and cannot be deleted."


class IamInvalidRelationError(IamManagementError):
    code = "IAM_INVALID_RELATION"
    numeric_code = 200205
    default_message = "IAM resource relation is invalid."


class IamManagementAccessDeniedError(IamManagementError):
    code = "IAM_MANAGEMENT_ACCESS_DENIED"
    numeric_code = 200206
    default_message = "IAM management access denied."


class IamManagementPersistenceError(IamManagementError):
    code = "IAM_MANAGEMENT_PERSISTENCE_ERROR"
    numeric_code = 200207
    default_message = "IAM management persistence error."
