# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_common.logging.constants import NsLogEvent
from ns_common.logging.context import build_log_context
from ns_common.logging.dispatcher import NsLogDispatcher
from ns_common.logging.event import NsLogEventData, get_current_pid


class NsWebSocketLogHook:
    def __init__(
        self,
        dispatcher: NsLogDispatcher,
        *,
        component: str = "websocket",
        log_name: str = "websocket",
    ):
        self._dispatcher = dispatcher
        self._component = component
        self._log_name = log_name

    def _emit(
        self,
        *,
        event: str,
        message: str,
        level: str,
        path: str | None = None,
        client_ip: str | None = None,
        user_id: int | str | None = None,
        connection_id: str | None = None,
        message_type: str | None = None,
        payload_size: int | None = None,
        close_code: int | None = None,
        error_type: str | None = None,
    ) -> None:
        try:
            context = build_log_context(
                connection_id=connection_id,
                user_id=user_id,
                path=path,
                client_ip=client_ip,
                message_type=message_type,
                payload_size=payload_size,
                close_code=close_code,
                error_type=error_type,
            )
            data = NsLogEventData(
                event=event,
                message=message,
                component=self._component,
                log_name=self._log_name,
                connection_id=connection_id,
                user_id=user_id,
                level=level,
                pid=get_current_pid(),
                context=context,
            )
            self._dispatcher.emit(data)
        except Exception:  # noqa
            pass

    def on_connect(
        self,
        *,
        path: str | None = None,
        client_ip: str | None = None,
        user_id: int | str | None = None,
        connection_id: str | None = None,
    ) -> None:
        self._emit(
            event=NsLogEvent.WEBSOCKET_CONNECT,
            message="websocket connect",
            level="INFO",
            path=path,
            client_ip=client_ip,
            user_id=user_id,
            connection_id=connection_id,
        )

    def on_accept(
        self,
        *,
        path: str | None = None,
        client_ip: str | None = None,
        user_id: int | str | None = None,
        connection_id: str | None = None,
    ) -> None:
        self._emit(
            event=NsLogEvent.WEBSOCKET_ACCEPT,
            message="websocket accept",
            level="INFO",
            path=path,
            client_ip=client_ip,
            user_id=user_id,
            connection_id=connection_id,
        )

    def on_receive(
        self,
        *,
        path: str | None = None,
        client_ip: str | None = None,
        user_id: int | str | None = None,
        connection_id: str | None = None,
        message_type: str | None = None,
        payload_size: int | None = None,
    ) -> None:
        self._emit(
            event=NsLogEvent.WEBSOCKET_RECEIVE,
            message="websocket receive",
            level="INFO",
            path=path,
            client_ip=client_ip,
            user_id=user_id,
            connection_id=connection_id,
            message_type=message_type,
            payload_size=payload_size,
        )

    def on_send(
        self,
        *,
        path: str | None = None,
        client_ip: str | None = None,
        user_id: int | str | None = None,
        connection_id: str | None = None,
        message_type: str | None = None,
        payload_size: int | None = None,
    ) -> None:
        self._emit(
            event=NsLogEvent.WEBSOCKET_SEND,
            message="websocket send",
            level="INFO",
            path=path,
            client_ip=client_ip,
            user_id=user_id,
            connection_id=connection_id,
            message_type=message_type,
            payload_size=payload_size,
        )

    def on_disconnect(
        self,
        *,
        path: str | None = None,
        client_ip: str | None = None,
        user_id: int | str | None = None,
        connection_id: str | None = None,
        close_code: int | None = None,
    ) -> None:
        self._emit(
            event=NsLogEvent.WEBSOCKET_DISCONNECT,
            message="websocket disconnect",
            level="INFO",
            path=path,
            client_ip=client_ip,
            user_id=user_id,
            connection_id=connection_id,
            close_code=close_code,
        )

    def on_error(
        self,
        *,
        path: str | None = None,
        client_ip: str | None = None,
        user_id: int | str | None = None,
        connection_id: str | None = None,
        error_type: str | None = None,
        message_type: str | None = None,
        payload_size: int | None = None,
    ) -> None:
        self._emit(
            event=NsLogEvent.WEBSOCKET_ERROR,
            message="websocket error",
            level="ERROR",
            path=path,
            client_ip=client_ip,
            user_id=user_id,
            connection_id=connection_id,
            error_type=error_type,
            message_type=message_type,
            payload_size=payload_size,
        )


__all__ = ["NsWebSocketLogHook"]

