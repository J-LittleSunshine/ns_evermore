# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Mapping, TYPE_CHECKING

from rest_framework.response import Response

from ns_common import NsEvermoreError

if TYPE_CHECKING:
    pass

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_500_INTERNAL_SERVER_ERROR = 500

OK_CODE = 0
OK_ERROR = "OK"
OK_MESSAGE = "OK"

INTERNAL_SERVER_ERROR_CODE = 100000
INTERNAL_SERVER_ERROR = "NS_INTERNAL_SERVER_ERROR"
INTERNAL_SERVER_ERROR_MESSAGE = "Internal server error."


def build_success_body(data: Any = None, *, message: str = OK_MESSAGE, request_id: str | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "code": OK_CODE,
        "error": OK_ERROR,
        "message": message,
        "data": data,
        "request_id": request_id,
    }


def build_error_body(*, code: int, error: str, message: str, details: Mapping[str, Any] | None = None, data: Any = None, request_id: str | None = None) -> dict[str, Any]:
    return {
        "success": False,
        "code": code,
        "error": error,
        "message": message,
        "details": dict(details or {}),
        "data": data,
        "request_id": request_id,
    }


def success_response(data: Any = None, *, message: str = OK_MESSAGE, status: int = HTTP_200_OK, request_id: str | None = None) -> Response:
    return Response(
        data=build_success_body(
            data=data,
            message=message,
            request_id=request_id,
        ),
        status=status,
    )


def error_response(error: NsEvermoreError, *, status: int = HTTP_400_BAD_REQUEST, request_id: str | None = None) -> Response:
    return Response(
        data=build_error_body(
            code=error.numeric_code,
            error=error.code,
            message=error.message,
            details=error.details,
            request_id=request_id,
        ),
        status=status,
    )


def internal_error_response(*, request_id: str | None = None) -> Response:
    return Response(
        data=build_error_body(
            code=INTERNAL_SERVER_ERROR_CODE,
            error=INTERNAL_SERVER_ERROR,
            message=INTERNAL_SERVER_ERROR_MESSAGE,
            details={},
            request_id=request_id,
        ),
        status=HTTP_500_INTERNAL_SERVER_ERROR,
    )
