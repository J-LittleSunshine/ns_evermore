# -*- coding: utf-8 -*-
"""Controlled connection.reauth and fail-closed session expiry policy."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Mapping

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeIamUnavailableError,
    NsRuntimeProtocolViolationError,
    NsStateError,
    NsValidationError,
)
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
from ns_common.time import Clock
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    Envelope,
    JsonV1Codec,
    MessageGroup,
    MessageTypeRegistry,
    PayloadGroup,
    ProtocolGroup,
    canonical_serialize,
)
from ns_runtime.transport import TransportSession

from .accepted import _iso_utc
from .audit import (
    ConnectionAuditKind,
    ConnectionAuditOutcome,
    ConnectionLifecycleAuditBoundary,
)
from .hello import HandshakeCredential, PendingHelloClaims
from .iam import HandshakeIamAdapter, HandshakeIamAuthority, HandshakeIamRequest
from .index import LocalConnectionIndex
from .session import (
    CapabilityPolicy,
    HandshakeSessionNegotiator,
    LogicalSessionIdentity,
    P05_CAPABILITY_POLICY,
    SessionContext,
)
from .state import LogicalConnectionCloseReason, LogicalConnectionState


REAUTH_PAYLOAD_FIELDS = frozenset({"token", "requested_capabilities"})
REAUTH_ACCEPTED_FIELDS = frozenset({
    "session_id",
    "connection_epoch",
    "session_expires_at",
    "server_time",
    "capabilities_changed",
})
REAUTH_REJECTED_FIELDS = frozenset({
    "reason",
    "server_time",
    "connection_closing",
})


class ReauthFailureAction(str, Enum):
    CLOSE = "close"


class ReauthRejectionReason(str, Enum):
    AUTH_DENIED = "auth_denied"
    AUTH_TIMEOUT = "auth_timeout"
    IDENTITY_MISMATCH = "identity_mismatch"
    CAPABILITY_DENIED = "capability_denied"
    SESSION_EXPIRED = "session_expired"
    INTERNAL_FAILURE = "internal_failure"


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionExpiryPolicy:
    reauth_lead_seconds: float
    failure_action: ReauthFailureAction = ReauthFailureAction.CLOSE

    def __post_init__(self) -> None:
        value = self.reauth_lead_seconds
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
        ):
            _invalid("reauth_lead_seconds")
        if self.failure_action is not ReauthFailureAction.CLOSE:
            _invalid("failure_action")


@dataclass(frozen=True, slots=True, kw_only=True, repr=False)
class ParsedReauth:
    claims: PendingHelloClaims
    credential: HandshakeCredential

    def __post_init__(self) -> None:
        if not isinstance(self.claims, PendingHelloClaims):
            _invalid("claims")
        if not isinstance(self.credential, HandshakeCredential):
            _invalid("credential")

    def __repr__(self) -> str:
        return "ParsedReauth(redacted=True)"


@dataclass(frozen=True, slots=True, kw_only=True)
class ReauthenticatedSession:
    context: SessionContext = field(repr=False)
    capabilities_changed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.context, SessionContext):
            _invalid("session_context")
        if not isinstance(self.capabilities_changed, bool):
            _invalid("capabilities_changed")


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionExpirySnapshot:
    session_expires_at: datetime
    reauth_required: bool
    expired: bool
    generation: int
    deadline_pending: bool

    def __post_init__(self) -> None:
        if not isinstance(self.session_expires_at, datetime):
            _invalid("session_expires_at")
        for name in ("reauth_required", "expired", "deadline_pending"):
            if not isinstance(getattr(self, name), bool):
                _invalid(name)
        if (
            isinstance(self.generation, bool)
            or not isinstance(self.generation, int)
            or self.generation < 0
        ):
            _invalid("generation")


@dataclass(frozen=True, slots=True, kw_only=True)
class _ReauthFailure:
    error: Exception = field(repr=False)


class ConnectionReauthEnvelopeHandler:
    def __init__(
        self,
        *,
        session_context: SessionContext,
        codec: JsonV1Codec,
        registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        if not isinstance(codec, JsonV1Codec) or codec.name != session_context.wire_codec:
            _invalid("codec")
        if not isinstance(registry, MessageTypeRegistry):
            _invalid("registry")
        self._context = session_context
        self._codec = codec
        self._registry = registry

    def parse(self, text: str) -> ParsedReauth:
        inbound = self._codec.decode_inbound(text)
        shape = Envelope(
            protocol=inbound.protocol,
            message=inbound.message,
            target=inbound.target,
            route=inbound.route,
            delivery=inbound.delivery,
            stream=inbound.stream,
            payload=inbound.payload,
            callback=inbound.callback,
            trace=inbound.trace,
            extensions=inbound.extensions,
        )
        validated = self._registry.validate_envelope(
            shape,
            self._context.protocol_schema_key,
        )
        return self.parse_envelope(validated)

    def parse_envelope(self, envelope: Envelope) -> ParsedReauth:
        """Parse one already P03-validated reauth Envelope."""

        if not isinstance(envelope, Envelope):
            _invalid("envelope")
        if envelope.message.type != "connection.reauth":
            raise _protocol_error("connection_reauth_required")
        if (
            envelope.protocol.major != self._context.protocol_version.major
            or envelope.protocol.minor != self._context.protocol_version.minor
            or envelope.protocol.patch != self._context.protocol_version.patch
        ):
            raise _protocol_error("reauth_protocol_mismatch")
        payload_group = envelope.payload
        if (
            payload_group is None
            or payload_group.mode != "inline"
            or not isinstance(payload_group.inline, Mapping)
        ):
            raise _protocol_error("reauth_inline_payload_required")
        payload = payload_group.inline
        if not {"token"}.issubset(payload) or not frozenset(payload).issubset(
            REAUTH_PAYLOAD_FIELDS,
        ):
            raise _protocol_error("reauth_payload_field_mismatch")
        token = payload["token"]
        if not isinstance(token, str) or not token:
            raise _protocol_error("reauth_token_invalid")
        credential = HandshakeCredential(token)
        del token
        try:
            raw_capabilities = payload.get(
                "requested_capabilities",
                tuple(self._context.capabilities),
            )
            if not isinstance(raw_capabilities, tuple):
                raise _protocol_error("reauth_capabilities_array_required")
            claims = PendingHelloClaims(
                component_type=self._context.component_type,
                requested_version=self._context.protocol_version,
                minimum_version=self._context.protocol_version,
                requested_capabilities=frozenset(raw_capabilities),
            )
            return ParsedReauth(claims=claims, credential=credential)
        except BaseException:
            credential.clear()
            raise


class ReauthEnvelopeBuilder:
    def __init__(
        self,
        *,
        clock: Clock,
        identifier_factory: IdentifierFactory,
        registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(identifier_factory, IdentifierFactory):
            _invalid("identifier_factory")
        if not isinstance(registry, MessageTypeRegistry):
            _invalid("registry")
        self._clock = clock
        self._identifier_factory = identifier_factory
        self._registry = registry

    def accepted(
        self,
        context: SessionContext,
        *,
        capabilities_changed: bool,
    ) -> str:
        if not isinstance(context, SessionContext):
            _invalid("session_context")
        if not isinstance(capabilities_changed, bool):
            _invalid("capabilities_changed")
        payload = {
            "session_id": context.session_id,
            "connection_epoch": context.connection_epoch,
            "session_expires_at": _iso_utc(context.session_expires_at),
            "server_time": _iso_utc(self._clock.utc_now()),
            "capabilities_changed": capabilities_changed,
        }
        return self._serialize(
            context,
            message_type="connection.reauth_accepted",
            payload=payload,
            expected_fields=REAUTH_ACCEPTED_FIELDS,
        )

    def rejected(
        self,
        context: SessionContext,
        *,
        reason: ReauthRejectionReason,
    ) -> str:
        if not isinstance(reason, ReauthRejectionReason):
            _invalid("rejection_reason")
        payload = {
            "reason": reason.value,
            "server_time": _iso_utc(self._clock.utc_now()),
            "connection_closing": True,
        }
        return self._serialize(
            context,
            message_type="connection.reauth_rejected",
            payload=payload,
            expected_fields=REAUTH_REJECTED_FIELDS,
        )

    def _serialize(
        self,
        context: SessionContext,
        *,
        message_type: str,
        payload: dict[str, object],
        expected_fields: frozenset[str],
    ) -> str:
        if frozenset(payload) != expected_fields:
            _state_error("reauth_response_field_mismatch")
        now = self._clock.utc_now()
        envelope = Envelope(
            protocol=ProtocolGroup(
                major=context.protocol_version.major,
                minor=context.protocol_version.minor,
                patch=context.protocol_version.patch,
            ),
            message=MessageGroup(
                message_id=self._identifier_factory.generate(
                    NsIdentifierKind.MESSAGE_ID,
                ),
                type=message_type,
                category="connection",
                priority=0,
                created_at=_iso_utc(now),
                reliability="best_effort",
            ),
            payload=PayloadGroup(mode="inline", inline=payload),
        )
        validated = self._registry.validate_envelope(
            envelope,
            context.protocol_schema_key,
        )
        return canonical_serialize(validated).decode("utf-8")


class SessionExpiryController:
    def __init__(
        self,
        *,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        transport_session: TransportSession,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        policy: SessionExpiryPolicy,
    ) -> None:
        dependencies = (
            (session_context, SessionContext, "session_context"),
            (connection_index, LocalConnectionIndex, "connection_index"),
            (transport_session, TransportSession, "transport_session"),
            (clock, Clock, "clock"),
            (task_supervisor, TaskSupervisor, "task_supervisor"),
            (policy, SessionExpiryPolicy, "policy"),
        )
        for value, expected, name in dependencies:
            if not isinstance(value, expected):
                _invalid(name)
        if (
            isinstance(task_sequence, bool)
            or not isinstance(task_sequence, int)
            or task_sequence < 0
        ):
            _invalid("task_sequence")
        self._context = session_context
        self._index = connection_index
        self._transport = transport_session
        self._clock = clock
        self._supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._policy = policy
        self._lock = asyncio.Lock()
        self._generation = 0
        self._started = False
        self._reauth_required = False
        self._expired = False
        self._task: asyncio.Task[object] | None = None

    async def start(self) -> None:
        async with self._lock:
            if self._started:
                _state_error("expiry_controller_already_started")
            entry = await self._index.lookup_connection(
                self._context.connection_id,
            )
            if (
                entry is None
                or entry.session_context != self._context
                or entry.state not in _REAUTHABLE_STATES
            ):
                _state_error("expiry_current_session_required")
            self._started = True
            self._schedule_unlocked()

    async def refresh(self, session_context: SessionContext) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        async with self._lock:
            if not self._started or self._expired:
                _state_error("expiry_controller_not_refreshable")
            if (
                session_context.connection_id != self._context.connection_id
                or session_context.session_id != self._context.session_id
                or session_context.connection_epoch != self._context.connection_epoch
                or session_context.session_expires_at <= self._clock.utc_now()
            ):
                _state_error("refreshed_session_context_mismatch")
            self._cancel_now()
            self._context = session_context
            self._generation += 1
            self._reauth_required = False
            self._schedule_unlocked()

    async def stop(self) -> None:
        async with self._lock:
            self._cancel_now()

    async def retry_cleanup(self) -> bool:
        async with self._lock:
            if not self._expired:
                _state_error("expired_session_required")
        return await self._close_expired()

    async def snapshot(self) -> SessionExpirySnapshot:
        async with self._lock:
            return SessionExpirySnapshot(
                session_expires_at=self._context.session_expires_at,
                reauth_required=self._reauth_required,
                expired=self._expired,
                generation=self._generation,
                deadline_pending=self._task is not None and not self._task.done(),
            )

    def _schedule_unlocked(self) -> None:
        generation = self._generation
        self._task = self._supervisor.create_task(
            self._run_generation(generation),
            name=(
                f"logical-expiry-{self._task_sequence}-generation-{generation}"
            ),
            cancel_order=12,
        )

    async def _run_generation(self, generation: int) -> None:
        try:
            lead_at = self._context.session_expires_at.timestamp() - float(
                self._policy.reauth_lead_seconds,
            )
            now_timestamp = self._clock.utc_now().timestamp()
            await self._clock.sleep(max(0.0, lead_at - now_timestamp))
            async with self._lock:
                if generation != self._generation:
                    return
                self._reauth_required = True
            expiry_remaining = max(
                0.0,
                self._context.session_expires_at.timestamp()
                - self._clock.utc_now().timestamp(),
            )
            await self._clock.sleep(expiry_remaining)
            async with self._lock:
                if generation != self._generation:
                    return
                entry = await self._index.lookup_connection(
                    self._context.connection_id,
                )
                if entry is None or entry.session_context != self._context:
                    return
                self._expired = True
            await self._close_expired()
        except asyncio.CancelledError:
            raise

    async def _close_expired(self) -> bool:
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is None:
            return True
        if entry is not None and entry.state is not LogicalConnectionState.CLOSING:
            try:
                await self._index.transition(
                    self._context.connection_id,
                    LogicalConnectionState.CLOSING,
                    close_reason=LogicalConnectionCloseReason.AUTH_FAILED,
                )
            except NsStateError:
                return False
        try:
            await self._transport.close()
        except Exception:
            return False
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is not None and entry.state is LogicalConnectionState.CLOSING:
            await self._index.transition(
                self._context.connection_id,
                LogicalConnectionState.CLOSED,
            )
        return True

    def _cancel_now(self) -> None:
        task = self._task
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()


class ConnectionReauthCoordinator:
    def __init__(
        self,
        *,
        current_context: SessionContext,
        connection_index: LocalConnectionIndex,
        transport_session: TransportSession,
        iam_adapter: HandshakeIamAdapter,
        response_builder: ReauthEnvelopeBuilder,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        timeout_seconds: float,
        expiry_controller: SessionExpiryController | None = None,
        audit_boundary: ConnectionLifecycleAuditBoundary | None = None,
        capability_policy: CapabilityPolicy = P05_CAPABILITY_POLICY,
    ) -> None:
        dependencies = (
            (current_context, SessionContext, "current_context"),
            (connection_index, LocalConnectionIndex, "connection_index"),
            (transport_session, TransportSession, "transport_session"),
            (iam_adapter, HandshakeIamAdapter, "iam_adapter"),
            (response_builder, ReauthEnvelopeBuilder, "response_builder"),
            (clock, Clock, "clock"),
            (task_supervisor, TaskSupervisor, "task_supervisor"),
            (capability_policy, CapabilityPolicy, "capability_policy"),
        )
        for value, expected, name in dependencies:
            if not isinstance(value, expected):
                _invalid(name)
        if expiry_controller is not None and not isinstance(
            expiry_controller,
            SessionExpiryController,
        ):
            _invalid("expiry_controller")
        if audit_boundary is not None and not isinstance(
            audit_boundary,
            ConnectionLifecycleAuditBoundary,
        ):
            _invalid("audit_boundary")
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
            _invalid("reauth_deadline")
        self._current = current_context
        self._index = connection_index
        self._transport = transport_session
        self._iam_adapter = iam_adapter
        self._responses = response_builder
        self._clock = clock
        self._supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._deadline = deadline
        self._expiry = expiry_controller
        self._audit = audit_boundary
        self._capability_policy = capability_policy
        self._lock = asyncio.Lock()
        self._claimed = False
        self._terminal_handled = False

    async def reauthenticate(self, parsed: ParsedReauth) -> ReauthenticatedSession:
        if not isinstance(parsed, ParsedReauth):
            _invalid("parsed_reauth")
        async with self._lock:
            if self._claimed:
                parsed.credential.clear()
                _state_error("reauth_already_attempted")
            self._claimed = True
        operation_task: asyncio.Task[object] | None = None
        deadline_task: asyncio.Task[object] | None = None
        try:
            remaining = max(0.0, self._deadline - self._clock.monotonic())
            operation_task = self._supervisor.create_task(
                self._execute_outcome(parsed),
                name=f"logical-reauth-{self._task_sequence}-operation",
                cancel_order=20,
            )
            deadline_task = self._supervisor.create_task(
                self._clock.sleep(remaining),
                name=f"logical-reauth-{self._task_sequence}-deadline",
                cancel_order=10,
            )
            await asyncio.wait(
                (operation_task, deadline_task),
                return_when=asyncio.FIRST_COMPLETED,
            )
            if deadline_task.done() or self._clock.monotonic() >= self._deadline:
                await _cancel_and_join(operation_task)
                await self._reject_and_close(ReauthRejectionReason.AUTH_TIMEOUT)
                raise NsRuntimeIamTimeoutError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_reauth",
                        "reason": "reauth_total_deadline",
                    },
                )
            await _cancel_and_join(deadline_task)
            outcome = operation_task.result()
            if isinstance(outcome, _ReauthFailure):
                if not self._terminal_handled:
                    await self._reject_and_close(
                        ReauthRejectionReason.INTERNAL_FAILURE,
                    )
                raise outcome.error from None
            if not isinstance(outcome, ReauthenticatedSession):
                await self._reject_and_close(ReauthRejectionReason.INTERNAL_FAILURE)
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_reauth",
                        "reason": "invalid_reauth_result",
                    },
                )
            return outcome
        except asyncio.CancelledError:
            await _cancel_and_join(operation_task)
            await self._close(LogicalConnectionCloseReason.SHUTDOWN)
            await _cancel_and_join(deadline_task)
            raise
        except Exception:
            await _cancel_and_join(operation_task)
            await _cancel_and_join(deadline_task)
            raise
        finally:
            parsed.credential.clear()

    async def _execute_outcome(
        self,
        parsed: ParsedReauth,
    ) -> ReauthenticatedSession | _ReauthFailure:
        try:
            return await self._execute(parsed)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            error.__traceback__ = None
            error.__context__ = None
            error.__cause__ = None
            return _ReauthFailure(error=error)

    async def _execute(self, parsed: ParsedReauth) -> ReauthenticatedSession:
        entry = await self._index.lookup_connection(self._current.connection_id)
        if (
            entry is None
            or entry.session_context != self._current
            or entry.state not in _REAUTHABLE_STATES
        ):
            _state_error("active_current_session_required")
        if self._current.session_expires_at <= self._clock.utc_now():
            await self._reject_and_close(ReauthRejectionReason.SESSION_EXPIRED)
            raise _reauth_denied("session_expired")
        request = HandshakeIamRequest(
            claims=parsed.claims,
            credential=parsed.credential,
        )
        try:
            try:
                authority = await self._iam_adapter.authenticate(request)
            except asyncio.CancelledError:
                raise
            except NsRuntimeIamTimeoutError:
                await self._reject_and_close(ReauthRejectionReason.AUTH_TIMEOUT)
                raise
            except NsRuntimeIamDeniedError:
                await self._reject_and_close(ReauthRejectionReason.AUTH_DENIED)
                raise
            except Exception:
                await self._reject_and_close(ReauthRejectionReason.INTERNAL_FAILURE)
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_reauth",
                        "reason": "adapter_failure",
                    },
                ) from None
            if type(authority) is not HandshakeIamAuthority:
                await self._reject_and_close(ReauthRejectionReason.INTERNAL_FAILURE)
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_reauth",
                        "reason": "invalid_adapter_result",
                    },
                )
            detached = authority.detached_copy()
            self._validate_authority(detached)
        except NsRuntimeIamDeniedError as error:
            if not self._terminal_handled:
                reason = (
                    ReauthRejectionReason.SESSION_EXPIRED
                    if error.details.get("reason") == "authority_expired"
                    else ReauthRejectionReason.IDENTITY_MISMATCH
                )
                await self._reject_and_close(reason)
            raise
        finally:
            request.credential.clear()
            del request

        negotiator = HandshakeSessionNegotiator(
            transport_session=self._transport,
            logical_identity=LogicalSessionIdentity(
                connection_id=self._current.connection_id,
                session_id=self._current.session_id,
                connection_epoch=self._current.connection_epoch,
            ),
            clock=self._clock,
            capability_policy=self._capability_policy,
        )
        try:
            negotiated = negotiator.negotiate(
                claims=parsed.claims,
                authority=detached,
            )
        except Exception:
            await self._reject_and_close(ReauthRejectionReason.CAPABILITY_DENIED)
            raise
        updated = replace(
            negotiated.context,
            created_at=self._current.created_at,
        )
        capabilities_changed = updated.capabilities != self._current.capabilities
        entry = await self._index.lookup_connection(self._current.connection_id)
        if (
            entry is None
            or entry.session_context != self._current
            or entry.state not in _REAUTHABLE_STATES
        ):
            await self._close(LogicalConnectionCloseReason.INTERNAL_ERROR)
            _state_error("reauth_send_fenced")
        text = self._responses.accepted(
            updated,
            capabilities_changed=capabilities_changed,
        )
        try:
            await self._transport.send(text)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self._close(LogicalConnectionCloseReason.SEND_FAILED)
            raise
        finally:
            del text
        entry = await self._index.lookup_connection(self._current.connection_id)
        if (
            entry is None
            or entry.session_context != self._current
            or entry.state not in _REAUTHABLE_STATES
        ):
            await self._close(LogicalConnectionCloseReason.INTERNAL_ERROR)
            _state_error("reauth_publish_fenced")
        try:
            await self._index.replace_authority_context(
                updated,
                expected_session_context=self._current,
                allowed_states=_REAUTHABLE_STATES,
            )
            if self._expiry is not None:
                await self._expiry.refresh(updated)
        except Exception:
            self._terminal_handled = True
            await self._close(LogicalConnectionCloseReason.INTERNAL_ERROR)
            raise
        return ReauthenticatedSession(
            context=updated,
            capabilities_changed=capabilities_changed,
        )

    def _validate_authority(self, authority: HandshakeIamAuthority) -> None:
        reason: str | None = None
        if authority.expires_at <= self._clock.utc_now():
            reason = "authority_expired"
        elif authority.identity != self._current.identity:
            reason = "reauth_identity_mismatch"
        elif authority.tenant_id != self._current.tenant_id:
            reason = "reauth_tenant_mismatch"
        elif authority.component_type != self._current.component_type:
            reason = "reauth_component_type_mismatch"
        if reason is not None:
            raise _reauth_denied(reason)

    async def _reject_and_close(self, reason: ReauthRejectionReason) -> None:
        if self._terminal_handled:
            return
        self._terminal_handled = True
        await self._mark_closing(LogicalConnectionCloseReason.AUTH_FAILED)
        cancelled: asyncio.CancelledError | None = None
        try:
            text = self._responses.rejected(self._current, reason=reason)
            await self._transport.send(text)
        except asyncio.CancelledError as error:
            cancelled = error
        except Exception:
            pass
        await self._close(LogicalConnectionCloseReason.AUTH_FAILED)
        if self._audit is not None:
            try:
                await self._audit.emit(
                    kind=ConnectionAuditKind.REAUTH_REJECTION,
                    outcome=ConnectionAuditOutcome.REJECTED,
                    connection_epoch=self._current.connection_epoch,
                    close_reason=LogicalConnectionCloseReason.AUTH_FAILED,
                )
            except asyncio.CancelledError as error:
                if cancelled is None:
                    cancelled = error
        if cancelled is not None:
            raise cancelled

    async def _close(self, reason: LogicalConnectionCloseReason) -> None:
        await self._mark_closing(reason)
        try:
            await self._transport.close()
        except Exception:
            return
        entry = await self._index.lookup_connection(self._current.connection_id)
        if entry is not None and entry.state is LogicalConnectionState.CLOSING:
            await self._index.transition(
                self._current.connection_id,
                LogicalConnectionState.CLOSED,
            )

    async def _mark_closing(self, reason: LogicalConnectionCloseReason) -> None:
        entry = await self._index.lookup_connection(self._current.connection_id)
        if entry is not None and entry.state is not LogicalConnectionState.CLOSING:
            try:
                await self._index.transition(
                    self._current.connection_id,
                    LogicalConnectionState.CLOSING,
                    close_reason=reason,
                )
            except NsStateError:
                pass


def _reauth_denied(reason: str) -> NsRuntimeIamDeniedError:
    return NsRuntimeIamDeniedError(
        details={
            "component": "logical_connection",
            "operation": "connection_reauth",
            "reason": reason,
        },
    )


_REAUTHABLE_STATES = frozenset({
    LogicalConnectionState.ACTIVE,
    LogicalConnectionState.DRAINING,
})


def _protocol_error(reason: str) -> NsRuntimeProtocolViolationError:
    return NsRuntimeProtocolViolationError(
        details={
            "component": "logical_connection",
            "operation": "connection_reauth",
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
        "Connection reauth dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Connection reauth operation is invalid.",
        details={
            "component": "logical_connection",
            "operation": "connection_reauth",
            "reason": reason,
        },
    )


__all__ = (
    "ConnectionReauthCoordinator",
    "ConnectionReauthEnvelopeHandler",
    "ParsedReauth",
    "REAUTH_ACCEPTED_FIELDS",
    "REAUTH_PAYLOAD_FIELDS",
    "REAUTH_REJECTED_FIELDS",
    "ReauthEnvelopeBuilder",
    "ReauthFailureAction",
    "ReauthRejectionReason",
    "ReauthenticatedSession",
    "SessionExpiryController",
    "SessionExpiryPolicy",
    "SessionExpirySnapshot",
)
