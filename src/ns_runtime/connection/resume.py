# -*- coding: utf-8 -*-
"""IAM-revalidated reconnect resume and logical epoch fencing."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeIamUnavailableError,
    NsRuntimeProtocolViolationError,
    NsStateError,
    NsValidationError,
)
from ns_common.iam import IamPrincipalType
from ns_common.time import Clock
from ns_runtime.protocol import BUILTIN_MESSAGE_REGISTRY, MessageTypeRegistry
from ns_runtime.transport import TransportSession

from .accepted import ConnectionAcceptedEnvelopeBuilder
from .audit import (
    ConnectionAuditKind,
    ConnectionAuditOutcome,
    ConnectionLifecycleAuditBoundary,
)
from .binding import LogicalConnectionTransportMap, LogicalSessionIdentityFactory
from .grace import ReconnectGraceService
from .hello import ParsedHello
from .iam import HandshakeIamAdapter, HandshakeIamAuthority, HandshakeIamRequest
from .index import LocalConnectionIndex
from .session import (
    CapabilityPolicy,
    HandshakeSessionNegotiator,
    LogicalSessionIdentity,
    NegotiatedSession,
    P05_CAPABILITY_POLICY,
    SessionContext,
)
from .state import LogicalConnectionCloseReason, LogicalConnectionState


@dataclass(frozen=True, slots=True, kw_only=True)
class ResumedConnection:
    session: NegotiatedSession = field(repr=False)
    previous_connection_epoch: int

    def __post_init__(self) -> None:
        if not isinstance(self.session, NegotiatedSession):
            _invalid("session")
        previous = self.previous_connection_epoch
        if (
            isinstance(previous, bool)
            or not isinstance(previous, int)
            or previous < 0
            or self.session.context.connection_epoch != previous + 1
        ):
            _invalid("previous_connection_epoch")


@dataclass(frozen=True, slots=True, kw_only=True)
class EpochValidation:
    connection_epoch: int
    state: LogicalConnectionState


@dataclass(frozen=True, slots=True, kw_only=True)
class _ResumeFailure:
    error: Exception = field(repr=False)


class ConnectionEpochGate:
    """Reject stale session/epoch before any future delivery path is invoked."""

    def __init__(
        self,
        *,
        connection_index: LocalConnectionIndex,
        registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(connection_index, LocalConnectionIndex):
            _invalid("connection_index")
        if not isinstance(registry, MessageTypeRegistry):
            _invalid("registry")
        self._index = connection_index
        self._registry = registry

    async def validate(
        self,
        *,
        connection_id: str,
        session_id: str,
        connection_epoch: int,
        message_type: str,
    ) -> EpochValidation:
        for name, value in (
            ("connection_id", connection_id),
            ("session_id", session_id),
            ("message_type", message_type),
        ):
            if not isinstance(value, str) or not value:
                _invalid(name)
        if (
            isinstance(connection_epoch, bool)
            or not isinstance(connection_epoch, int)
            or connection_epoch < 0
        ):
            _invalid("connection_epoch")
        self._registry.require(message_type)
        entry = await self._index.lookup_connection(connection_id)
        if entry is None:
            raise _epoch_error("connection_not_current")
        context = entry.session_context
        if session_id != context.session_id:
            raise _epoch_error("session_not_current")
        if connection_epoch != context.connection_epoch:
            raise _epoch_error("connection_epoch_not_current")
        if entry.state not in {
            LogicalConnectionState.ACTIVE,
            LogicalConnectionState.DRAINING,
        }:
            raise _epoch_error("connection_state_not_allowed")
        return EpochValidation(
            connection_epoch=context.connection_epoch,
            state=entry.state,
        )


class ConnectionResumeCoordinator:
    def __init__(
        self,
        *,
        current_context: SessionContext,
        grace_service: ReconnectGraceService,
        connection_index: LocalConnectionIndex,
        transport_mapping: LogicalConnectionTransportMap,
        new_transport_session: TransportSession,
        iam_adapter: HandshakeIamAdapter,
        logical_identity_factory: LogicalSessionIdentityFactory,
        accepted_builder: ConnectionAcceptedEnvelopeBuilder,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        timeout_seconds: float,
        expected_principal_type: IamPrincipalType | None = None,
        candidate_terminator: (
            Callable[[LogicalConnectionCloseReason], Awaitable[bool]] | None
        ) = None,
        audit_boundary: ConnectionLifecycleAuditBoundary | None = None,
        capability_policy: CapabilityPolicy = P05_CAPABILITY_POLICY,
    ) -> None:
        dependencies = (
            (current_context, SessionContext, "current_context"),
            (grace_service, ReconnectGraceService, "grace_service"),
            (connection_index, LocalConnectionIndex, "connection_index"),
            (transport_mapping, LogicalConnectionTransportMap, "transport_mapping"),
            (new_transport_session, TransportSession, "new_transport_session"),
            (iam_adapter, HandshakeIamAdapter, "iam_adapter"),
            (logical_identity_factory, LogicalSessionIdentityFactory, "logical_identity_factory"),
            (accepted_builder, ConnectionAcceptedEnvelopeBuilder, "accepted_builder"),
            (clock, Clock, "clock"),
            (task_supervisor, TaskSupervisor, "task_supervisor"),
            (capability_policy, CapabilityPolicy, "capability_policy"),
        )
        for value, expected, name in dependencies:
            if not isinstance(value, expected):
                _invalid(name)
        if audit_boundary is not None and not isinstance(
            audit_boundary,
            ConnectionLifecycleAuditBoundary,
        ):
            _invalid("audit_boundary")
        if candidate_terminator is not None and not callable(candidate_terminator):
            _invalid("candidate_terminator")
        if expected_principal_type is not None and not isinstance(
            expected_principal_type,
            IamPrincipalType,
        ):
            _invalid("expected_principal_type")
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
        started = clock.monotonic()
        deadline = started + float(timeout_seconds)
        if not math.isfinite(started) or not math.isfinite(deadline):
            _invalid("resume_deadline")
        self._current = current_context
        self._grace = grace_service
        self._index = connection_index
        self._mapping = transport_mapping
        self._new_transport = new_transport_session
        self._iam_adapter = iam_adapter
        self._identity_factory = logical_identity_factory
        self._accepted_builder = accepted_builder
        self._clock = clock
        self._supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._deadline = deadline
        self._expected_principal_type = expected_principal_type
        self._capability_policy = capability_policy
        self._audit = audit_boundary
        self._candidate_terminator = candidate_terminator
        self._candidate_terminal_requested = False
        self._claim_lock = asyncio.Lock()
        self._claimed = False
        self._grace_claimed = False
        self._new_binding_published = False

    async def resume(self, parsed: ParsedHello) -> ResumedConnection:
        if not isinstance(parsed, ParsedHello):
            _invalid("parsed_hello")
        async with self._claim_lock:
            if self._claimed:
                parsed.credential.clear()
                _state_error("resume_already_attempted")
            self._claimed = True
        operation_task: asyncio.Task[object] | None = None
        deadline_task: asyncio.Task[object] | None = None
        try:
            remaining = max(0.0, self._deadline - self._clock.monotonic())
            operation_task = self._supervisor.create_task(
                self._execute_outcome(parsed),
                name=f"logical-resume-{self._task_sequence}-operation",
                cancel_order=20,
            )
            deadline_task = self._supervisor.create_task(
                self._clock.sleep(remaining),
                name=f"logical-resume-{self._task_sequence}-deadline",
                cancel_order=10,
            )
            await asyncio.wait(
                (operation_task, deadline_task),
                return_when=asyncio.FIRST_COMPLETED,
            )
            if deadline_task.done() or self._clock.monotonic() >= self._deadline:
                if deadline_task.done():
                    deadline_task.result()
                await _cancel_and_join(operation_task)
                await self._fail_if_claimed(LogicalConnectionCloseReason.TIMEOUT_CLOSED)
                await self._emit_audit(
                    ConnectionAuditOutcome.REJECTED,
                    connection_epoch=self._current.connection_epoch,
                    close_reason=await self._audit_close_reason(
                        LogicalConnectionCloseReason.TIMEOUT_CLOSED,
                    ),
                )
                raise NsRuntimeIamTimeoutError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_resume",
                        "reason": "resume_total_deadline",
                    },
                )
            await _cancel_and_join(deadline_task)
            outcome = operation_task.result()
            if isinstance(outcome, _ResumeFailure):
                await self._fail_if_claimed(
                    LogicalConnectionCloseReason.INTERNAL_ERROR,
                )
                await self._emit_audit(
                    ConnectionAuditOutcome.REJECTED,
                    connection_epoch=self._current.connection_epoch,
                    close_reason=await self._audit_close_reason(
                        LogicalConnectionCloseReason.INTERNAL_ERROR,
                    ),
                )
                raise outcome.error from None
            if not isinstance(outcome, ResumedConnection):
                await self._emit_audit(
                    ConnectionAuditOutcome.REJECTED,
                    connection_epoch=self._current.connection_epoch,
                    close_reason=await self._audit_close_reason(
                        LogicalConnectionCloseReason.INTERNAL_ERROR,
                    ),
                )
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_resume",
                        "reason": "invalid_resume_result",
                    },
                )
            await self._emit_audit(
                ConnectionAuditOutcome.SUCCEEDED,
                connection_epoch=outcome.session.context.connection_epoch,
            )
            return outcome
        except asyncio.CancelledError:
            await _cancel_and_join(operation_task)
            await self._fail_if_claimed(LogicalConnectionCloseReason.SHUTDOWN)
            await _cancel_and_join(deadline_task)
            await self._emit_audit(
                ConnectionAuditOutcome.CANCELLED,
                connection_epoch=self._current.connection_epoch,
                close_reason=await self._audit_close_reason(
                    LogicalConnectionCloseReason.SHUTDOWN,
                ),
            )
            raise
        except Exception:
            await _cancel_and_join(operation_task)
            await _cancel_and_join(deadline_task)
            raise
        finally:
            parsed.credential.clear()

    async def _execute_outcome(
        self,
        parsed: ParsedHello,
    ) -> ResumedConnection | _ResumeFailure:
        try:
            return await self._execute(parsed)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            error.__traceback__ = None
            error.__context__ = None
            error.__cause__ = None
            return _ResumeFailure(error=error)

    async def _execute(self, parsed: ParsedHello) -> ResumedConnection:
        resume_request = parsed.claims.resume
        if resume_request is None:
            _state_error("resume_reference_required")
        await self._grace.claim_resume(resume_request)
        self._grace_claimed = True
        indexed = await self._index.lookup_connection(self._current.connection_id)
        if (
            indexed is None
            or indexed.session_context.session_id != self._current.session_id
            or indexed.session_context.connection_epoch
            != self._current.connection_epoch
        ):
            await self._fail_if_claimed(LogicalConnectionCloseReason.AUTH_FAILED)
            raise _resume_denied("current_session_not_available")
        if (
            not self._current.resume_eligible
            or not indexed.session_context.resume_eligible
        ):
            await self._fail_if_claimed(LogicalConnectionCloseReason.AUTH_FAILED)
            raise _resume_denied("current_session_not_resume_eligible")
        if self._current.session_expires_at <= self._clock.utc_now():
            await self._fail_if_claimed(LogicalConnectionCloseReason.AUTH_FAILED)
            raise _resume_denied("current_session_expired")

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
                await self._fail_if_claimed(LogicalConnectionCloseReason.AUTH_FAILED)
                raise
            except Exception:
                await self._fail_if_claimed(LogicalConnectionCloseReason.AUTH_FAILED)
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_resume",
                        "reason": "adapter_failure",
                    },
                ) from None
            if type(authority) is not HandshakeIamAuthority:
                await self._fail_if_claimed(LogicalConnectionCloseReason.AUTH_FAILED)
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_resume",
                        "reason": "invalid_adapter_result",
                    },
                )
            detached = authority.detached_copy()
            self._validate_authority(detached, parsed=parsed)
        except (NsRuntimeIamDeniedError, NsRuntimeIamTimeoutError):
            await self._fail_if_claimed(LogicalConnectionCloseReason.AUTH_FAILED)
            raise
        finally:
            request.credential.clear()
            del request

        previous_identity = LogicalSessionIdentity(
            connection_id=self._current.connection_id,
            session_id=self._current.session_id,
            connection_epoch=self._current.connection_epoch,
        )
        next_identity = self._identity_factory.resume(previous_identity)
        negotiator = HandshakeSessionNegotiator(
            transport_session=self._new_transport,
            logical_identity=next_identity,
            clock=self._clock,
            capability_policy=self._capability_policy,
        )
        try:
            negotiated = negotiator.negotiate(
                claims=parsed.claims,
                authority=detached,
            )
        except Exception:
            await self._fail_if_claimed(LogicalConnectionCloseReason.PROTOCOL_FAILED)
            raise

        try:
            await self._mapping.replace_transport_session(
                session_context=negotiated.context,
                transport_session=self._new_transport,
            )
            self._new_binding_published = True
            await self._index.replace_session_context(negotiated.context)
        except Exception:
            await self._fail_if_claimed(LogicalConnectionCloseReason.INTERNAL_ERROR)
            raise

        text = self._accepted_builder.serialize(negotiated.context)
        try:
            await self._new_transport.send(text)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self._fail_if_claimed(LogicalConnectionCloseReason.SEND_FAILED)
            raise
        finally:
            del text
        try:
            await self._index.restore_active_target(self._current.connection_id)
            await self._grace.complete_resume(negotiated.context)
        except Exception:
            await self._fail_if_claimed(LogicalConnectionCloseReason.INTERNAL_ERROR)
            raise
        return ResumedConnection(
            session=negotiated,
            previous_connection_epoch=self._current.connection_epoch,
        )

    def _validate_authority(
        self,
        authority: HandshakeIamAuthority,
        *,
        parsed: ParsedHello,
    ) -> None:
        reason: str | None = None
        if authority.expires_at <= self._clock.utc_now():
            reason = "authority_expired"
        elif not authority.resume_eligible:
            reason = "authority_not_resume_eligible"
        elif authority.identity != self._current.identity:
            reason = "resume_identity_mismatch"
        elif authority.tenant_id != self._current.tenant_id:
            reason = "resume_tenant_mismatch"
        elif authority.component_type != self._current.component_type:
            reason = "resume_component_type_mismatch"
        elif (
            self._expected_principal_type is not None
            and authority.principal_type is not self._expected_principal_type
        ):
            reason = "resume_principal_type_mismatch"
        elif parsed.claims.component_type != self._current.component_type:
            reason = "resume_claim_component_type_mismatch"
        if reason is not None:
            raise _resume_denied(reason)

    async def _fail_if_claimed(
        self,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        if self._new_binding_published:
            mapping = await self._mapping.snapshot()
            if mapping.transport is not None:
                try:
                    await self._mapping.detach_transport_session(
                        transport_session_id=mapping.transport.transport_session_id,
                    )
                except Exception:
                    pass
        if self._candidate_terminator is not None:
            if not self._candidate_terminal_requested:
                self._candidate_terminal_requested = True
                await self._candidate_terminator(reason)
        else:
            try:
                await self._new_transport.close()
            except Exception:
                pass
        if not self._grace_claimed:
            return
        await self._grace.terminate(reason)

    async def _emit_audit(
        self,
        outcome: ConnectionAuditOutcome,
        *,
        connection_epoch: int,
        close_reason: LogicalConnectionCloseReason | None = None,
    ) -> None:
        if self._audit is None:
            return
        await self._audit.emit(
            kind=ConnectionAuditKind.RESUME,
            outcome=outcome,
            connection_epoch=connection_epoch,
            close_reason=close_reason,
        )

    async def _audit_close_reason(
        self,
        fallback: LogicalConnectionCloseReason,
    ) -> LogicalConnectionCloseReason | None:
        if not self._grace_claimed:
            return None
        snapshot = await self._grace.snapshot()
        return snapshot.terminal_reason or fallback


def _resume_denied(reason: str) -> NsRuntimeIamDeniedError:
    return NsRuntimeIamDeniedError(
        details={
            "component": "logical_connection",
            "operation": "connection_resume",
            "reason": reason,
        },
    )


def _epoch_error(reason: str) -> NsRuntimeProtocolViolationError:
    return NsRuntimeProtocolViolationError(
        details={
            "component": "logical_connection",
            "operation": "connection_epoch_validation",
            "reason": reason,
        },
    )


async def _cancel_and_join(task: asyncio.Task[object] | None) -> None:
    if task is None:
        return
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection resume dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Connection resume operation is invalid.",
        details={
            "component": "logical_connection",
            "operation": "connection_resume",
            "reason": reason,
        },
    )


__all__ = (
    "ConnectionEpochGate",
    "ConnectionResumeCoordinator",
    "EpochValidation",
    "ResumedConnection",
)
