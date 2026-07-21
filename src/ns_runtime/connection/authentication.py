# -*- coding: utf-8 -*-
"""Total-deadline hello parsing and P05 IAM authentication orchestration."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeIamUnavailableError,
    NsValidationError,
)
from ns_common.time import Clock

from .handshake import ConnectionHelloReceiver
from .hello import HelloClaimParser, PendingHelloClaims
from .iam import (
    HandshakeIamAdapter,
    HandshakeIamAuthority,
    HandshakeIamRequest,
)
from .session import HandshakeSessionNegotiator, NegotiatedSession
from .state import LogicalConnectionCloseReason, LogicalConnectionState


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthenticatedHello:
    claims: PendingHelloClaims = field(repr=False)
    authority: HandshakeIamAuthority = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.claims, PendingHelloClaims):
            _invalid("claims")
        if not isinstance(self.authority, HandshakeIamAuthority):
            _invalid("authority")


@dataclass(frozen=True, slots=True, kw_only=True)
class _HandshakeFailure:
    error: Exception = field(repr=False)


class ConnectionHandshakeAuthenticator:
    """Authenticate one hello while retaining one total handshake deadline."""

    def __init__(
        self,
        *,
        hello_receiver: ConnectionHelloReceiver,
        claim_parser: HelloClaimParser,
        iam_adapter: HandshakeIamAdapter,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        timeout_seconds: float,
        session_negotiator: HandshakeSessionNegotiator | None = None,
    ) -> None:
        if not isinstance(hello_receiver, ConnectionHelloReceiver):
            _invalid("hello_receiver")
        if not isinstance(claim_parser, HelloClaimParser):
            _invalid("claim_parser")
        if not isinstance(iam_adapter, HandshakeIamAdapter):
            _invalid("iam_adapter")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(task_supervisor, TaskSupervisor):
            _invalid("task_supervisor")
        if (
            isinstance(task_sequence, bool)
            or not isinstance(task_sequence, int)
            or task_sequence < 0
        ):
            _invalid("task_sequence")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not 0 < float(timeout_seconds) < float("inf")
        ):
            _invalid("timeout_seconds")
        if session_negotiator is not None and not isinstance(
            session_negotiator,
            HandshakeSessionNegotiator,
        ):
            _invalid("session_negotiator")
        started_at = clock.monotonic()
        deadline = started_at + float(timeout_seconds)
        if not math.isfinite(started_at) or not math.isfinite(deadline):
            _invalid("clock_deadline")
        self._hello_receiver = hello_receiver
        self._claim_parser = claim_parser
        self._iam_adapter = iam_adapter
        self._clock = clock
        self._task_supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._deadline = deadline
        self._session_negotiator = session_negotiator
        self._claim_lock = asyncio.Lock()
        self._claimed = False

    async def authenticate(self) -> AuthenticatedHello | NegotiatedSession:
        async with self._claim_lock:
            if self._claimed:
                raise NsRuntimeIamDeniedError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "authentication_already_attempted",
                    },
                )
            self._claimed = True

        operation_task: asyncio.Task[object] | None = None
        deadline_task: asyncio.Task[object] | None = None
        try:
            remaining = max(0.0, self._deadline - self._clock.monotonic())
            operation_task = self._task_supervisor.create_task(
                self._execute_outcome(),
                name=f"logical-handshake-{self._task_sequence}-authentication",
                cancel_order=20,
            )
            deadline_task = self._task_supervisor.create_task(
                self._clock.sleep(remaining),
                name=f"logical-handshake-{self._task_sequence}-total-deadline",
                cancel_order=10,
            )
            await asyncio.wait(
                (operation_task, deadline_task),
                return_when=asyncio.FIRST_COMPLETED,
            )
            if (
                deadline_task.done()
                or self._clock.monotonic() >= self._deadline
            ):
                if deadline_task.done():
                    deadline_task.result()
                await self._terminate_isolated(
                    LogicalConnectionCloseReason.TIMEOUT_CLOSED,
                )
                await _cancel_and_join(operation_task)
                raise NsRuntimeIamTimeoutError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "total_handshake_deadline",
                    },
                )
            await _cancel_and_join(deadline_task)
            result = operation_task.result()
            if isinstance(result, _HandshakeFailure):
                raise result.error from None
            if not isinstance(result, (AuthenticatedHello, NegotiatedSession)):
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "invalid_authentication_result",
                    },
                )
            return result
        except asyncio.CancelledError:
            await self._terminate_isolated(LogicalConnectionCloseReason.SHUTDOWN)
            await _cancel_and_join(operation_task)
            await _cancel_and_join(deadline_task)
            raise
        except Exception:
            await _cancel_and_join(operation_task)
            await _cancel_and_join(deadline_task)
            raise

    async def _execute_outcome(
        self,
    ) -> AuthenticatedHello | NegotiatedSession | _HandshakeFailure:
        try:
            return await self._execute()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            error.__traceback__ = None
            error.__context__ = None
            error.__cause__ = None
            return _HandshakeFailure(error=error)

    async def _execute(self) -> AuthenticatedHello | NegotiatedSession:
        inbound = await self._hello_receiver.receive()
        try:
            parsed = self._claim_parser.parse(inbound)
        except Exception:
            await self._terminate_isolated(
                LogicalConnectionCloseReason.PROTOCOL_FAILED,
            )
            raise
        finally:
            del inbound

        request = HandshakeIamRequest(
            claims=parsed.claims,
            credential=parsed.credential,
        )
        try:
            try:
                authority = await self._iam_adapter.authenticate(request)
            except asyncio.CancelledError:
                raise
            except (NsRuntimeIamDeniedError, NsRuntimeIamTimeoutError):
                await self._terminate_isolated(
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                raise
            except Exception:
                await self._terminate_isolated(
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "adapter_failure",
                    },
                ) from None

            if type(authority) is not HandshakeIamAuthority:
                await self._terminate_isolated(
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "invalid_adapter_result",
                    },
                )
            detached = authority.detached_copy()
            try:
                self._validate_authority(detached, claims=parsed.claims)
            except NsRuntimeIamDeniedError:
                await self._terminate_isolated(
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                raise
            await self._hello_receiver.state_machine.transition(
                LogicalConnectionState.AUTHENTICATED,
            )
            if self._session_negotiator is not None:
                try:
                    return self._session_negotiator.negotiate(
                        claims=parsed.claims,
                        authority=detached,
                    )
                except Exception:
                    await self._terminate_isolated(
                        LogicalConnectionCloseReason.PROTOCOL_FAILED,
                    )
                    raise
            return AuthenticatedHello(
                claims=parsed.claims,
                authority=detached,
            )
        finally:
            request.credential.clear()
            del request
            del parsed

    def _validate_authority(
        self,
        authority: HandshakeIamAuthority,
        *,
        claims: PendingHelloClaims,
    ) -> None:
        reason: str | None = None
        if authority.expires_at <= self._clock.utc_now():
            reason = "authority_expired"
        elif authority.component_type != claims.component_type:
            reason = "authority_identity_inconsistent"
        if reason is None:
            return
        raise NsRuntimeIamDeniedError(
            details={
                "component": "logical_connection",
                "operation": "handshake_authentication",
                "reason": reason,
            },
        )

    async def _terminate_isolated(
        self,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        try:
            await self._hello_receiver.terminate(reason)
        except Exception:
            pass


async def _cancel_and_join(task: asyncio.Task[object] | None) -> None:
    if task is None:
        return
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Logical connection authentication dependency is invalid.",
        details={
            "component": "logical_connection",
            "field": field_name,
        },
    )


__all__ = (
    "AuthenticatedHello",
    "ConnectionHandshakeAuthenticator",
)
