# -*- coding: utf-8 -*-
"""P05 logical connection composition owner and supervised ingress loops."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

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
from ns_common.iam import IamPrincipalType
from ns_common.time import Clock
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    CURRENT_PROTOCOL_SCHEMA_KEY,
    Envelope,
    ErrorEnvelopeBuilder,
    ErrorEnvelopeContext,
    JsonV1Codec,
    MessageDirection,
    MessageTypeRegistry,
    ProtocolGroup,
    SourceGroup,
    RuntimeAuthority,
    build_feature_disabled_processors,
    canonical_serialize,
    normalize_inbound,
)
from ns_runtime.processor import (
    AuditSink,
    EventBus,
    IdempotencyPrecheck,
    ProcessorAuthorization,
    ProcessorErrorMapper,
    RateLimitEntry,
    RoutingPreparation,
)
from ns_runtime.processor.integration import (
    ConnectionProcessorPipeline,
    build_connection_processor_pipeline,
    TransportResponseEmitter,
)
from ns_runtime.transport import TransportAdapter, TransportManager, TransportMessage, TransportSession

from .accepted import ConnectionAcceptedEnvelopeBuilder, ConnectionAdmissionActivator, _iso_utc
from .audit import ConnectionLifecycleAuditBoundary, ConnectionLifecycleAuditSink
from .binding import (
    LogicalConnectionTransportMap,
    LogicalSessionIdentityFactory,
)
from .drain import ConnectionDrainService, DrainPolicy
from .deadline import HandshakeDeadlineBudget
from .grace import ReconnectGracePolicy, ReconnectGraceService
from .handshake import ConnectionHelloReceiver
from .heartbeat import ConnectionHeartbeatService, HeartbeatPolicy
from .hello import HelloClaimParser, ParsedHello
from .iam import HandshakeIamAdapter, HandshakeIamAuthority, HandshakeIamRequest
from .index import LocalConnectionIndex
from .processors import (
    ConnectionDrainProcessor,
    ConnectionHeartbeatProcessor,
    ConnectionLifecycleProcessorRegistry,
    ConnectionLifecycleProcessorRegistryFactory,
)
from .reauth import (
    ConnectionReauthCoordinator,
    ConnectionReauthEnvelopeHandler,
    ReauthEnvelopeBuilder,
    ReauthenticatedSession,
    SessionExpiryController,
    SessionExpiryPolicy,
)
from .rejected import (
    ConnectionHandshakeRejector,
    ConnectionRejectedEnvelopeBuilder,
    ConnectionRejectionReason,
    ConnectionRejectionSendPolicy,
)
from .resume import ConnectionResumeCoordinator
from .session import HandshakeSessionNegotiator, SessionContext
from .state import (
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionLifecyclePolicy:
    handshake_timeout_seconds: float
    rejected_send_timeout_seconds: float
    native_heartbeat_interval_seconds: float
    envelope_heartbeat_timeout_seconds: float
    drain_timeout_seconds: float
    reconnect_grace_seconds: float = 30.0
    reauth_lead_seconds: float = 30.0

    def __post_init__(self) -> None:
        for name in (
            "handshake_timeout_seconds",
            "rejected_send_timeout_seconds",
            "native_heartbeat_interval_seconds",
            "envelope_heartbeat_timeout_seconds",
            "drain_timeout_seconds",
            "reconnect_grace_seconds",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) <= 0
            ):
                _invalid(name)
        value = self.reauth_lead_seconds
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
        ):
            _invalid("reauth_lead_seconds")


@dataclass(slots=True)
class _LogicalOwner:
    context: SessionContext = field(repr=False)
    principal_type: IamPrincipalType = field(repr=False)
    state_machine: LogicalConnectionStateMachine = field(repr=False)
    mapping: LogicalConnectionTransportMap = field(repr=False)
    transport: TransportSession | None = field(repr=False)
    grace: ReconnectGraceService = field(repr=False)
    lifecycle_audit: ConnectionLifecycleAuditBoundary = field(repr=False)
    heartbeat: ConnectionHeartbeatService | None = field(default=None, repr=False)
    drain: ConnectionDrainService | None = field(default=None, repr=False)
    expiry: SessionExpiryController | None = field(default=None, repr=False)
    processors: ConnectionLifecycleProcessorRegistry | None = field(default=None, repr=False)
    pipeline: ConnectionProcessorPipeline | None = field(default=None, repr=False)
    read_task: asyncio.Task[object] | None = field(default=None, repr=False)
    drain_cleanup_task: asyncio.Task[object] | None = field(default=None, repr=False)
    resume_handoff_pending_activation: bool = field(default=False, repr=False)
    cleanup_lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


@dataclass(slots=True)
class _CandidateCleanupOwner:
    sequence: int
    transport: TransportSession = field(repr=False)
    state_machine: LogicalConnectionStateMachine = field(repr=False)
    terminal_reason: LogicalConnectionCloseReason | None = None
    cleanup_lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class _IamOutcomeKind(str, Enum):
    SUCCEEDED = "succeeded"
    DENIED = "denied"
    TIMED_OUT = "timed_out"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True, kw_only=True)
class _IamOutcome:
    kind: _IamOutcomeKind
    authority: HandshakeIamAuthority | None = field(default=None, repr=False)


class ConnectionLifecycleManager:
    """Single P05 owner for logical admission, active ingress and cleanup."""

    def __init__(
        self,
        *,
        transport_manager: TransportManager,
        connection_index: LocalConnectionIndex,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        identifier_factory: IdentifierFactory,
        iam_adapter: HandshakeIamAdapter,
        accepted_builder: ConnectionAcceptedEnvelopeBuilder,
        error_builder: ErrorEnvelopeBuilder,
        logger: logging.Logger,
        runtime_id: str,
        policy: ConnectionLifecyclePolicy,
        codec: JsonV1Codec,
        processor_registry_factory: ConnectionLifecycleProcessorRegistryFactory,
        processor_authorization: ProcessorAuthorization,
        processor_rate_limit: RateLimitEntry,
        processor_idempotency: IdempotencyPrecheck,
        processor_routing: RoutingPreparation,
        processor_error_mapper: ProcessorErrorMapper,
        processor_audit_sink: AuditSink,
        lifecycle_audit_sink: ConnectionLifecycleAuditSink,
        event_bus: EventBus,
        config_version: str,
        policy_version: str,
        processor_timeout_seconds: float,
        protocol_registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
        schema_key: str = CURRENT_PROTOCOL_SCHEMA_KEY,
    ) -> None:
        dependencies = (
            (transport_manager, TransportManager, "transport_manager"),
            (connection_index, LocalConnectionIndex, "connection_index"),
            (clock, Clock, "clock"),
            (task_supervisor, TaskSupervisor, "task_supervisor"),
            (identifier_factory, IdentifierFactory, "identifier_factory"),
            (iam_adapter, HandshakeIamAdapter, "iam_adapter"),
            (accepted_builder, ConnectionAcceptedEnvelopeBuilder, "accepted_builder"),
            (error_builder, ErrorEnvelopeBuilder, "error_builder"),
            (logger, logging.Logger, "logger"),
            (policy, ConnectionLifecyclePolicy, "policy"),
            (codec, JsonV1Codec, "codec"),
            (protocol_registry, MessageTypeRegistry, "protocol_registry"),
            (
                processor_registry_factory,
                ConnectionLifecycleProcessorRegistryFactory,
                "processor_registry_factory",
            ),
            (processor_authorization, ProcessorAuthorization, "processor_authorization"),
            (processor_rate_limit, RateLimitEntry, "processor_rate_limit"),
            (processor_idempotency, IdempotencyPrecheck, "processor_idempotency"),
            (processor_routing, RoutingPreparation, "processor_routing"),
            (processor_error_mapper, ProcessorErrorMapper, "processor_error_mapper"),
            (processor_audit_sink, AuditSink, "processor_audit_sink"),
            (
                lifecycle_audit_sink,
                ConnectionLifecycleAuditSink,
                "lifecycle_audit_sink",
            ),
            (event_bus, EventBus, "event_bus"),
        )
        for value, expected, name in dependencies:
            if not isinstance(value, expected):
                _invalid(name)
        if not isinstance(runtime_id, str) or not runtime_id:
            _invalid("runtime_id")
        if not isinstance(schema_key, str) or not schema_key:
            _invalid("schema_key")
        for value, name in (
            (config_version, "config_version"),
            (policy_version, "policy_version"),
        ):
            if not isinstance(value, str) or not value:
                _invalid(name)
        if (
            isinstance(processor_timeout_seconds, bool)
            or not isinstance(processor_timeout_seconds, (int, float))
            or not math.isfinite(float(processor_timeout_seconds))
            or float(processor_timeout_seconds) <= 0
        ):
            _invalid("processor_timeout_seconds")
        self._transport_manager = transport_manager
        self._index = connection_index
        self._clock = clock
        self._supervisor = task_supervisor
        self._identifier_factory = identifier_factory
        self._logical_identity_factory = LogicalSessionIdentityFactory(identifier_factory)
        self._iam = iam_adapter
        self._accepted_builder = accepted_builder
        self._error_builder = error_builder
        self._logger = logger
        self._runtime_id = runtime_id
        self._policy = policy
        self._codec = codec
        self._registry = protocol_registry
        if processor_registry_factory.protocol_registry is not protocol_registry:
            _invalid("processor_registry_factory.protocol_registry")
        self._processor_registry_factory = processor_registry_factory
        self._processor_authorization = processor_authorization
        self._processor_rate_limit = processor_rate_limit
        self._processor_idempotency = processor_idempotency
        self._processor_routing = processor_routing
        self._processor_error_mapper = processor_error_mapper
        self._processor_audit_sink = processor_audit_sink
        self._lifecycle_audit_sink = lifecycle_audit_sink
        self._event_bus = event_bus
        self._config_version = config_version
        self._policy_version = policy_version
        self._processor_timeout_seconds = float(processor_timeout_seconds)
        self._schema_key = schema_key
        self._disabled_processors = build_feature_disabled_processors(
            error_builder=error_builder,
            logger=logger,
            registry=protocol_registry,
        )
        self._owners: dict[str, _LogicalOwner] = {}
        self._candidate_cleanup_owners: dict[int, _CandidateCleanupOwner] = {}
        self._accept_tasks: set[asyncio.Task[object]] = set()
        self._admission_tasks: set[asyncio.Task[object]] = set()
        self._lifecycle_lock = asyncio.Lock()
        self._admission_open = False
        self._started = False
        self._sequence = 0

    @property
    def connection_index(self) -> LocalConnectionIndex:
        return self._index

    @property
    def admission_open(self) -> bool:
        return self._admission_open

    @property
    def active_connection_count(self) -> int:
        return len(self._owners)

    @property
    def pending_candidate_cleanup_count(self) -> int:
        return len(self._candidate_cleanup_owners)

    async def start(self) -> None:
        async with self._lifecycle_lock:
            if self._started:
                raise NsStateError(
                    "Logical connection manager is already started.",
                    details={
                        "component": "connection_lifecycle_manager",
                        "operation": "start",
                        "reason": "already_started",
                    },
                )
            self._started = True
            self._admission_open = True
            for adapter in self._transport_manager.adapters:
                sequence = self._next_sequence()
                task = self._supervisor.create_task(
                    self._accept_loop(adapter),
                    name=f"logical-accept-{sequence}",
                    cancel_order=35,
                )
                self._track(task, self._accept_tasks)

    def stop_admission_now(self) -> None:
        self._admission_open = False

    async def stop_admission(self) -> None:
        self._admission_open = False
        await _cancel_tasks(tuple(self._accept_tasks))
        await _cancel_tasks(tuple(self._admission_tasks))
        read_tasks = tuple(
            owner.read_task
            for owner in self._owners.values()
            if owner.read_task is not None
        )
        await _cancel_tasks(read_tasks)

    async def drain(self) -> None:
        self._admission_open = False
        await self.stop_admission()
        owners = tuple(self._owners.values())
        for owner in owners:
            await self._close_owner(owner, LogicalConnectionCloseReason.SHUTDOWN)
        await self.retry_pending_candidate_cleanup()

    async def _accept_loop(self, adapter: TransportAdapter) -> None:
        while self._admission_open:
            try:
                session = await adapter.accept()
            except asyncio.CancelledError:
                raise
            except Exception:
                if self._admission_open and adapter.accepting:
                    await asyncio.sleep(0)
                    continue
                return
            if not self._admission_open:
                await _close_isolated(session)
                return
            sequence = self._next_sequence()
            task = self._supervisor.create_task(
                self._admit(session, sequence=sequence),
                name=f"logical-admission-{sequence}",
                cancel_order=30,
            )
            self._track(task, self._admission_tasks)

    async def _admit(self, transport: TransportSession, *, sequence: int) -> None:
        budget = HandshakeDeadlineBudget.start(
            clock=self._clock,
            timeout_seconds=float(self._policy.handshake_timeout_seconds),
        )
        machine = LogicalConnectionStateMachine()
        candidate = _CandidateCleanupOwner(
            sequence=sequence,
            transport=transport,
            state_machine=machine,
        )
        self._candidate_cleanup_owners[sequence] = candidate
        receiver = ConnectionHelloReceiver(
            transport_session=transport,
            state_machine=machine,
            clock=self._clock,
            task_supervisor=self._supervisor,
            task_sequence=sequence,
            timeout_seconds=float(self._policy.handshake_timeout_seconds),
            codec=self._codec,
            registry=self._registry,
            schema_key=self._schema_key,
            deadline_budget=budget,
        )
        try:
            inbound = await receiver.receive()
        except asyncio.CancelledError as error:
            await self._reconcile_candidate_after_receiver(candidate)
            raise error
        except Exception:
            await self._reconcile_candidate_after_receiver(candidate)
            return
        protocol = inbound.protocol
        try:
            parsed = HelloClaimParser().parse(inbound)
            if budget.expired():
                raise NsRuntimeIamTimeoutError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake",
                        "reason": "total_handshake_deadline",
                    },
                )
        except asyncio.CancelledError as error:
            await self._close_candidate_preserving(
                candidate,
                LogicalConnectionCloseReason.SHUTDOWN,
            )
            raise error
        except NsRuntimeIamTimeoutError:
            await self._close_candidate(
                candidate,
                LogicalConnectionCloseReason.TIMEOUT_CLOSED,
            )
            return
        except Exception:
            await self._close_candidate(
                candidate,
                LogicalConnectionCloseReason.PROTOCOL_FAILED,
            )
            return
        finally:
            del inbound

        if parsed.claims.resume is not None:
            await self._resume(
                parsed,
                protocol=protocol,
                transport=transport,
                candidate=candidate,
                sequence=sequence,
                budget=budget,
            )
            return
        await self._admit_new(
            parsed,
            protocol=protocol,
            transport=transport,
            machine=machine,
            candidate=candidate,
            sequence=sequence,
            budget=budget,
        )

    async def _admit_new(
        self,
        parsed: ParsedHello,
        *,
        protocol: ProtocolGroup,
        transport: TransportSession,
        machine: LogicalConnectionStateMachine,
        candidate: _CandidateCleanupOwner,
        sequence: int,
        budget: HandshakeDeadlineBudget,
    ) -> None:
        rejector = self._rejector(transport, sequence=sequence)
        indexed_connection_id: str | None = None
        request = HandshakeIamRequest(
            claims=parsed.claims,
            credential=parsed.credential,
        )
        try:
            try:
                authority = await self._bounded_iam(
                    request,
                    sequence=sequence,
                    budget=budget,
                )
            except NsRuntimeIamDeniedError:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.IAM_DENIED,
                )
                await self._close_candidate(
                    candidate,
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                return
            except NsRuntimeIamTimeoutError:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.IAM_UNAVAILABLE,
                )
                await self._close_candidate(
                    candidate,
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                return
            except Exception:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.IAM_UNAVAILABLE,
                )
                await self._close_candidate(
                    candidate,
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                return
            if type(authority) is not HandshakeIamAuthority:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.INTERNAL_FAILURE,
                )
                await self._close_candidate(
                    candidate,
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                return
            detached = authority.detached_copy()
            if (
                detached.expires_at <= self._clock.utc_now()
                or detached.component_type != parsed.claims.component_type
            ):
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.AUTHORITY_INVALID,
                )
                await self._close_candidate(
                    candidate,
                    LogicalConnectionCloseReason.AUTH_FAILED,
                )
                return
            identity = self._logical_identity_factory.create()
            negotiator = HandshakeSessionNegotiator(
                transport_session=transport,
                logical_identity=identity,
                clock=self._clock,
            )
            try:
                negotiated = negotiator.negotiate(
                    claims=parsed.claims,
                    authority=detached,
                )
                self._require_handshake_budget(budget)
            except NsRuntimeIamTimeoutError:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.IAM_UNAVAILABLE,
                )
                await self._close_candidate(
                    candidate,
                    LogicalConnectionCloseReason.TIMEOUT_CLOSED,
                )
                return
            except Exception as error:
                await rejector.send(
                    protocol=protocol,
                    reason=_negotiation_reason(error),
                )
                await self._close_candidate(
                    candidate,
                    LogicalConnectionCloseReason.PROTOCOL_FAILED,
                )
                return
            await machine.transition(LogicalConnectionState.AUTHENTICATED)
            mapping = LogicalConnectionTransportMap(
                session_context=negotiated.context,
                transport_session=transport,
            )
            await self._index.add_authenticated(
                session_context=negotiated.context,
                state_machine=machine,
            )
            indexed_connection_id = negotiated.context.connection_id
            owner = _LogicalOwner(
                context=negotiated.context,
                principal_type=detached.principal_type,
                state_machine=machine,
                mapping=mapping,
                transport=transport,
                grace=self._new_grace(
                    context=negotiated.context,
                    mapping=mapping,
                    sequence=sequence,
                ),
                lifecycle_audit=ConnectionLifecycleAuditBoundary(
                    session_context=negotiated.context,
                    clock=self._clock,
                    sink=self._lifecycle_audit_sink,
                ),
            )
            self._owners[negotiated.context.connection_id] = owner
            self._candidate_cleanup_owners.pop(candidate.sequence, None)
            activator = ConnectionAdmissionActivator(
                connection_index=self._index,
                transport_session=transport,
                envelope_builder=self._accepted_builder,
            )
            await activator.activate(negotiated.context)
            await self._activate_owner(owner, sequence=sequence)
        except asyncio.CancelledError as error:
            if indexed_connection_id is not None:
                try:
                    await self._close_indexed(
                        parsed_claim_connection_id=indexed_connection_id,
                        transport=transport,
                        reason=LogicalConnectionCloseReason.SHUTDOWN,
                    )
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass
            elif candidate.terminal_reason is None:
                await self._close_candidate_preserving(
                    candidate,
                    LogicalConnectionCloseReason.SHUTDOWN,
                )
            raise error
        except Exception:
            await self._close_indexed(
                parsed_claim_connection_id=indexed_connection_id,
                transport=transport,
                reason=LogicalConnectionCloseReason.INTERNAL_ERROR,
            )
        finally:
            request.credential.clear()
            parsed.credential.clear()

    async def _resume(
        self,
        parsed: ParsedHello,
        *,
        protocol: ProtocolGroup,
        transport: TransportSession,
        candidate: _CandidateCleanupOwner,
        sequence: int,
        budget: HandshakeDeadlineBudget,
    ) -> None:
        request = parsed.claims.resume
        assert request is not None
        owner = self._owners.get(request.connection_id)
        if owner is None:
            await self._rejector(transport, sequence=sequence).send(
                protocol=protocol,
                reason=ConnectionRejectionReason.IAM_DENIED,
            )
            parsed.credential.clear()
            await self._close_candidate(
                candidate,
                LogicalConnectionCloseReason.REJECTED,
            )
            return
        ownership_transferred = False
        try:
            coordinator = ConnectionResumeCoordinator(
                current_context=owner.context,
                grace_service=owner.grace,
                connection_index=self._index,
                transport_mapping=owner.mapping,
                new_transport_session=transport,
                iam_adapter=self._iam,
                logical_identity_factory=self._logical_identity_factory,
                accepted_builder=self._accepted_builder,
                clock=self._clock,
                task_supervisor=self._supervisor,
                task_sequence=sequence,
                timeout_seconds=self._remaining_handshake_budget(budget),
                expected_principal_type=owner.principal_type,
                candidate_terminator=lambda reason: self._close_candidate(
                    candidate,
                    reason,
                ),
                audit_boundary=owner.lifecycle_audit,
            )
            resumed = await coordinator.resume(parsed)
            previous_expiry = owner.expiry
            resumed_context = resumed.session.context
            resumed_grace = self._new_grace(
                context=resumed_context,
                mapping=owner.mapping,
                sequence=sequence,
            )

            # ResumeCoordinator has already published the new binding, index,
            # accepted response and ACTIVE target.  Transfer the transport from
            # the pre-index candidate to the logical owner synchronously before
            # introducing another cancellation point.
            owner.context = resumed_context
            owner.transport = transport
            owner.grace = resumed_grace
            owner.resume_handoff_pending_activation = True
            self._candidate_cleanup_owners.pop(candidate.sequence, None)
            ownership_transferred = True

            if previous_expiry is not None:
                await previous_expiry.stop()
            await self._activate_owner(owner, sequence=sequence)
            owner.resume_handoff_pending_activation = False
        except asyncio.CancelledError as error:
            if ownership_transferred:
                await self._close_owner_preserving(
                    owner,
                    LogicalConnectionCloseReason.SHUTDOWN,
                )
            elif candidate.terminal_reason is None:
                await self._close_candidate_preserving(
                    candidate,
                    LogicalConnectionCloseReason.SHUTDOWN,
                )
            raise error
        except Exception:
            if ownership_transferred:
                await self._close_owner(
                    owner,
                    LogicalConnectionCloseReason.INTERNAL_ERROR,
                )
            else:
                if candidate.terminal_reason is None:
                    await self._close_candidate(
                        candidate,
                        LogicalConnectionCloseReason.AUTH_FAILED,
                    )
            parsed.credential.clear()
            return

    async def _activate_owner(self, owner: _LogicalOwner, *, sequence: int) -> None:
        transport = owner.transport
        if transport is None:
            raise NsStateError(
                "Logical connection transport is unavailable.",
                details={
                    "component": "connection_lifecycle_manager",
                    "operation": "activate",
                    "reason": "transport_unavailable",
                },
            )
        drain = ConnectionDrainService(
            connection_id=owner.context.connection_id,
            connection_index=self._index,
            transport_session=transport,
            clock=self._clock,
            task_supervisor=self._supervisor,
            task_sequence=sequence,
            policy=DrainPolicy(timeout_seconds=float(self._policy.drain_timeout_seconds)),
        )
        heartbeat = ConnectionHeartbeatService(
            session_context=owner.context,
            connection_index=self._index,
            transport_session=transport,
            clock=self._clock,
            task_supervisor=self._supervisor,
            task_sequence=sequence,
            identifier_factory=self._identifier_factory,
            policy=HeartbeatPolicy(
                native_interval_seconds=float(
                    self._policy.native_heartbeat_interval_seconds,
                ),
                envelope_timeout_seconds=float(
                    self._policy.envelope_heartbeat_timeout_seconds,
                ),
            ),
            codec=self._codec,
            registry=self._registry,
            drain_service=drain,
        )
        expiry = SessionExpiryController(
            session_context=owner.context,
            connection_index=self._index,
            transport_session=transport,
            clock=self._clock,
            task_supervisor=self._supervisor,
            task_sequence=sequence,
            policy=SessionExpiryPolicy(
                reauth_lead_seconds=float(self._policy.reauth_lead_seconds),
            ),
            drain_service=drain,
        )
        owner.heartbeat = heartbeat
        owner.drain = drain
        owner.expiry = expiry
        owner.processors = self._build_processors(owner, sequence=sequence)
        owner.pipeline = self._build_pipeline(owner)
        await heartbeat.start()
        await expiry.start()
        task = self._supervisor.create_task(
            self._read_loop(owner, transport=transport),
            name=f"logical-read-{sequence}",
            cancel_order=25,
        )
        owner.read_task = task

    def _build_processors(
        self,
        owner: _LogicalOwner,
        *,
        sequence: int,
    ) -> ConnectionLifecycleProcessorRegistry:
        transport = owner.transport
        heartbeat = owner.heartbeat
        drain = owner.drain
        expiry = owner.expiry
        if transport is None or heartbeat is None or drain is None or expiry is None:
            _invalid("owner_services")
        reauth_handler = ConnectionReauthEnvelopeHandler(
            session_context=owner.context,
            codec=self._codec,
            registry=self._registry,
        )
        reauth_coordinator = ConnectionReauthCoordinator(
            current_context=owner.context,
            connection_index=self._index,
            transport_session=transport,
            iam_adapter=self._iam,
            response_builder=ReauthEnvelopeBuilder(
                clock=self._clock,
                identifier_factory=self._identifier_factory,
                registry=self._registry,
            ),
            clock=self._clock,
            task_supervisor=self._supervisor,
            task_sequence=sequence,
            timeout_seconds=float(self._policy.handshake_timeout_seconds),
            expected_principal_type=owner.principal_type,
            expiry_controller=expiry,
            drain_service=drain,
            audit_boundary=owner.lifecycle_audit,
        )
        return self._processor_registry_factory.build(
            session_context=owner.context,
            connection_index=self._index,
            heartbeat_service=heartbeat,
            drain_service=drain,
            reauth_handler=reauth_handler,
            reauth_coordinator=reauth_coordinator,
        )

    async def _read_loop(
        self,
        owner: _LogicalOwner,
        *,
        transport: TransportSession,
    ) -> None:
        try:
            while self._admission_open and owner.transport is transport:
                message = await transport.receive()
                if not isinstance(message, TransportMessage):
                    _protocol_error("transport_message_required")
                envelope = self._decode_and_validate(message.text, owner.context)
                contract = self._registry.require(envelope.message.type)
                if contract.direction is MessageDirection.OUTBOUND:
                    _protocol_error("outbound_message_received")
                pipeline = owner.pipeline
                if pipeline is None:
                    _protocol_error("processor_pipeline_unavailable")
                execution = await pipeline.execute(
                    envelope,
                    execution_id=str(self._next_sequence()),
                )
                if execution.error is not None:
                    await self._send_error_isolated(owner, execution.error)
                    if isinstance(execution.error, NsRuntimeProtocolViolationError):
                        await self._close_owner(
                            owner,
                            LogicalConnectionCloseReason.PROTOCOL_FAILED,
                        )
                        return
                    continue
                await TransportResponseEmitter(transport=transport).emit(execution)
                result = execution.response
                if envelope.message.type == "connection.drain":
                    self._ensure_drain_cleanup_task(owner)
                if isinstance(result, ReauthenticatedSession):
                    owner.context = result.context
                    if owner.heartbeat is not None:
                        await owner.heartbeat.replace_session_context(result.context)
                    owner.processors = self._build_processors(
                        owner,
                        sequence=self._next_sequence(),
                    )
                    owner.pipeline = self._build_pipeline(owner)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            if not self._admission_open:
                return
            entry = await self._index.lookup_connection(owner.context.connection_id)
            if entry is not None and entry.state in {
                LogicalConnectionState.ACTIVE,
                LogicalConnectionState.DRAINING,
            }:
                if _is_transport_disconnect(error):
                    await self._enter_grace(owner, transport=transport)
                    return
                await self._send_error_isolated(owner, error)
                await self._close_owner(
                    owner,
                    LogicalConnectionCloseReason.PROTOCOL_FAILED,
                )
        finally:
            if await self._index.lookup_connection(owner.context.connection_id) is None:
                self._owners.pop(owner.context.connection_id, None)

    def _ensure_drain_cleanup_task(self, owner: _LogicalOwner) -> None:
        task = owner.drain_cleanup_task
        if task is not None and not task.done():
            return
        owner.drain_cleanup_task = self._supervisor.create_task(
            self._watch_drain_cleanup(owner),
            name=f"logical-drain-owner-{self._next_sequence()}",
            cancel_order=16,
        )

    async def _watch_drain_cleanup(self, owner: _LogicalOwner) -> None:
        drain = owner.drain
        if drain is None:
            return
        await drain.wait_closed()
        async with owner.cleanup_lock:
            connection_id = owner.context.connection_id
            if await self._index.lookup_connection(connection_id) is None:
                self._owners.pop(connection_id, None)

    def _decode_and_validate(self, text: str, context: SessionContext) -> Envelope:
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
            context.protocol_schema_key,
        )
        if (
            validated.protocol.major != context.protocol_version.major
            or validated.protocol.minor != context.protocol_version.minor
            or validated.protocol.patch != context.protocol_version.patch
        ):
            _protocol_error("session_protocol_mismatch")
        capabilities = "\x00".join(sorted(context.capabilities)).encode("utf-8")
        return normalize_inbound(
            inbound,
            authority=RuntimeAuthority(
                source=SourceGroup(
                    runtime_id=self._runtime_id,
                    connection_id=context.connection_id,
                    identity_digest=_digest(context.identity),
                    tenant_id=context.tenant_id,
                    component_type=context.component_type,
                    capabilities_digest=(
                        "sha256:" + hashlib.sha256(capabilities).hexdigest()[:16]
                    ),
                ),
                auth_context=self._permission_auth_context(context),
            ),
        )

    def _build_pipeline(self, owner: _LogicalOwner) -> ConnectionProcessorPipeline:
        transport = owner.transport
        processors = owner.processors
        if transport is None or processors is None:
            _invalid("owner_pipeline_dependencies")
        return build_connection_processor_pipeline(
            session_context=owner.context,
            lifecycle_registry=processors,
            disabled_processors=self._disabled_processors,
            error_context_factory=lambda: self._error_context(owner.context),
            authorization=self._processor_authorization,
            rate_limit=self._processor_rate_limit,
            idempotency=self._processor_idempotency,
            routing=self._processor_routing,
            error_mapper=self._processor_error_mapper,
            principal_type=owner.principal_type,
            audit_sink=self._processor_audit_sink,
            event_bus=self._event_bus,
            task_supervisor=self._supervisor,
            clock=self._clock,
            config_version=self._config_version,
            policy_version=self._policy_version,
            timeout_seconds=self._processor_timeout_seconds,
            protocol_registry=self._registry,
        )

    @staticmethod
    def _permission_auth_context(context: SessionContext):
        from ns_runtime.protocol import AuthContextGroup

        return AuthContextGroup(
            permission_snapshot_ref=context.permission_snapshot_ref,
            permission_digest=context.permission_digest,
            iam_mode=context.iam_mode,
            issued_at=_iso_utc(context.authorization_issued_at),
            expires_at=_iso_utc(context.session_expires_at),
        )

    async def _send_error_isolated(self, owner: _LogicalOwner, error: Exception) -> None:
        transport = owner.transport
        if transport is None:
            return
        try:
            response = self._error_builder.build(
                error,
                context=self._error_context(owner.context),
            )
            await transport.send(canonical_serialize(response).decode("utf-8"))
        except Exception:
            pass

    def _error_context(self, context: SessionContext) -> ErrorEnvelopeContext:
        capabilities = "\x00".join(sorted(context.capabilities)).encode("utf-8")
        return ErrorEnvelopeContext(
            protocol=ProtocolGroup(
                major=context.protocol_version.major,
                minor=context.protocol_version.minor,
                patch=context.protocol_version.patch,
            ),
            source=SourceGroup(
                runtime_id=self._runtime_id,
                connection_id=context.connection_id,
                identity_digest=_digest(context.identity),
                tenant_id=context.tenant_id,
                component_type=context.component_type,
                capabilities_digest="sha256:" + hashlib.sha256(capabilities).hexdigest()[:16],
            ),
            error_message_id=self._identifier_factory.generate(
                NsIdentifierKind.MESSAGE_ID,
            ),
            created_at=_iso_utc(self._clock.utc_now()),
        )

    async def _enter_grace(
        self,
        owner: _LogicalOwner,
        *,
        transport: TransportSession,
    ) -> None:
        if owner.heartbeat is not None:
            await owner.heartbeat.detach_for_reconnect()
        await owner.grace.enter(
            transport_session_id=transport.identity.transport_session_id,
        )
        owner.transport = None
        owner.processors = None
        owner.pipeline = None
        owner.drain = None

    async def _close_owner(
        self,
        owner: _LogicalOwner,
        reason: LogicalConnectionCloseReason,
    ) -> bool:
        connection_id = owner.context.connection_id
        async with owner.cleanup_lock:
            entry = await self._index.lookup_connection(connection_id)
            if entry is None:
                self._owners.pop(connection_id, None)
                return True
            if entry.state is not LogicalConnectionState.CLOSING:
                await self._index.transition(
                    connection_id,
                    LogicalConnectionState.CLOSING,
                    close_reason=reason,
                )
            if owner.heartbeat is not None:
                try:
                    await owner.heartbeat.detach_for_reconnect()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    pass
            if owner.expiry is not None:
                try:
                    await owner.expiry.stop()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    pass
            if owner.drain is not None:
                closed = await owner.drain.terminate(reason)
            else:
                transport = owner.transport
                if transport is not None:
                    try:
                        await transport.close()
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        return False
                entry = await self._index.lookup_connection(connection_id)
                if entry is not None and entry.state is LogicalConnectionState.CLOSING:
                    await self._index.transition(
                        connection_id,
                        LogicalConnectionState.CLOSED,
                    )
                closed = True
            if not closed:
                return False
            self._owners.pop(connection_id, None)
            return True

    async def _close_indexed(
        self,
        *,
        parsed_claim_connection_id: str | None,
        transport: TransportSession,
        reason: LogicalConnectionCloseReason,
    ) -> bool:
        if parsed_claim_connection_id is not None:
            owner = self._owners.get(parsed_claim_connection_id)
            if owner is not None:
                return await self._close_owner(owner, reason)
            entry = await self._index.lookup_connection(parsed_claim_connection_id)
            if entry is not None and entry.state is not LogicalConnectionState.CLOSING:
                try:
                    await self._index.transition(
                        parsed_claim_connection_id,
                        LogicalConnectionState.CLOSING,
                        close_reason=reason,
                    )
                except Exception:
                    pass
        try:
            await transport.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            return False
        if parsed_claim_connection_id is not None:
            entry = await self._index.lookup_connection(parsed_claim_connection_id)
            if entry is not None and entry.state is LogicalConnectionState.CLOSING:
                try:
                    await self._index.transition(
                        parsed_claim_connection_id,
                        LogicalConnectionState.CLOSED,
                    )
                except Exception:
                    return False
        return (
            parsed_claim_connection_id is None
            or await self._index.lookup_connection(parsed_claim_connection_id) is None
        )

    async def retry_cleanup(self, connection_id: str) -> bool:
        if not isinstance(connection_id, str) or not connection_id:
            _invalid("connection_id")
        owner = self._owners.get(connection_id)
        if owner is None:
            return await self._index.lookup_connection(connection_id) is None
        reason = owner.state_machine.close_reason or LogicalConnectionCloseReason.INTERNAL_ERROR
        return await self._close_owner(owner, reason)

    async def retry_pending_candidate_cleanup(self) -> bool:
        candidates = tuple(self._candidate_cleanup_owners.values())
        closed = True
        for candidate in candidates:
            reason = (
                candidate.terminal_reason
                or LogicalConnectionCloseReason.SHUTDOWN
            )
            if not await self._close_candidate(candidate, reason):
                closed = False
        return closed

    async def _reconcile_candidate_after_receiver(
        self,
        candidate: _CandidateCleanupOwner,
    ) -> None:
        async with candidate.cleanup_lock:
            snapshot = await candidate.state_machine.snapshot()
            if snapshot.close_reason is not None and candidate.terminal_reason is None:
                candidate.terminal_reason = snapshot.close_reason
            if snapshot.state is LogicalConnectionState.CLOSED:
                self._candidate_cleanup_owners.pop(candidate.sequence, None)
                return
            if snapshot.state is LogicalConnectionState.CLOSING:
                return
        await self._close_candidate(
            candidate,
            LogicalConnectionCloseReason.INTERNAL_ERROR,
        )

    async def _close_candidate_preserving(
        self,
        candidate: _CandidateCleanupOwner,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        try:
            await self._close_candidate(candidate, reason)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def _close_owner_preserving(
        self,
        owner: _LogicalOwner,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        try:
            await self._close_owner(owner, reason)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def _close_candidate(
        self,
        candidate: _CandidateCleanupOwner,
        reason: LogicalConnectionCloseReason,
    ) -> bool:
        async with candidate.cleanup_lock:
            snapshot = await candidate.state_machine.snapshot()
            if snapshot.close_reason is not None and candidate.terminal_reason is None:
                candidate.terminal_reason = snapshot.close_reason
            if candidate.terminal_reason is None:
                candidate.terminal_reason = reason
            if snapshot.state is LogicalConnectionState.CLOSED:
                self._candidate_cleanup_owners.pop(candidate.sequence, None)
                return True
            if snapshot.state is not LogicalConnectionState.CLOSING:
                await candidate.state_machine.transition(
                    LogicalConnectionState.CLOSING,
                    close_reason=candidate.terminal_reason,
                )
            try:
                await candidate.transport.close()
            except asyncio.CancelledError:
                raise
            except Exception:
                return False
            snapshot = await candidate.state_machine.snapshot()
            if snapshot.state is LogicalConnectionState.CLOSING:
                await candidate.state_machine.transition(LogicalConnectionState.CLOSED)
            self._candidate_cleanup_owners.pop(candidate.sequence, None)
            return True

    async def _bounded_iam(
        self,
        request: HandshakeIamRequest,
        *,
        sequence: int,
        budget: HandshakeDeadlineBudget,
    ) -> HandshakeIamAuthority:
        operation = self._supervisor.create_task(
            self._execute_iam_outcome(request),
            name=f"logical-iam-{sequence}-operation",
            cancel_order=20,
        )
        deadline = self._supervisor.create_task(
            self._clock.sleep(budget.remaining_seconds()),
            name=f"logical-iam-{sequence}-deadline",
            cancel_order=10,
        )
        try:
            await asyncio.wait((operation, deadline), return_when=asyncio.FIRST_COMPLETED)
            if deadline.done() or not operation.done() or budget.expired():
                await _cancel_tasks((operation,))
                raise NsRuntimeIamTimeoutError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "total_handshake_deadline",
                    },
                )
            outcome = operation.result()
            if not isinstance(outcome, _IamOutcome):
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "invalid_authentication_outcome",
                    },
                )
            if outcome.kind is _IamOutcomeKind.DENIED:
                raise NsRuntimeIamDeniedError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "iam_denied",
                    },
                )
            if outcome.kind is _IamOutcomeKind.TIMED_OUT:
                raise NsRuntimeIamTimeoutError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "iam_timeout",
                    },
                )
            if outcome.kind is _IamOutcomeKind.UNAVAILABLE or outcome.authority is None:
                raise NsRuntimeIamUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "adapter_failure",
                    },
                )
            return outcome.authority
        finally:
            await _cancel_tasks((operation, deadline))

    async def _execute_iam_outcome(self, request: HandshakeIamRequest) -> _IamOutcome:
        try:
            authority = await self._iam.authenticate(request)
        except asyncio.CancelledError:
            raise
        except NsRuntimeIamDeniedError as error:
            _clear_exception(error)
            return _IamOutcome(kind=_IamOutcomeKind.DENIED)
        except NsRuntimeIamTimeoutError as error:
            _clear_exception(error)
            return _IamOutcome(kind=_IamOutcomeKind.TIMED_OUT)
        except Exception as error:
            _clear_exception(error)
            return _IamOutcome(kind=_IamOutcomeKind.UNAVAILABLE)
        return _IamOutcome(
            kind=_IamOutcomeKind.SUCCEEDED,
            authority=authority,
        )

    @staticmethod
    def _remaining_handshake_budget(budget: HandshakeDeadlineBudget) -> float:
        remaining = budget.remaining_seconds()
        if remaining <= 0:
            raise NsRuntimeIamTimeoutError(
                details={
                    "component": "logical_connection",
                    "operation": "handshake",
                    "reason": "total_handshake_deadline",
                },
            )
        return remaining

    @classmethod
    def _require_handshake_budget(cls, budget: HandshakeDeadlineBudget) -> None:
        cls._remaining_handshake_budget(budget)

    def _rejector(
        self,
        transport: TransportSession,
        *,
        sequence: int,
    ) -> ConnectionHandshakeRejector:
        return ConnectionHandshakeRejector(
            transport_session=transport,
            builder=ConnectionRejectedEnvelopeBuilder(
                clock=self._clock,
                identifier_factory=self._identifier_factory,
                registry=self._registry,
                schema_key=self._schema_key,
            ),
            clock=self._clock,
            task_supervisor=self._supervisor,
            task_sequence=sequence,
            policy=ConnectionRejectionSendPolicy(
                timeout_seconds=float(self._policy.rejected_send_timeout_seconds),
            ),
        )

    def _new_grace(
        self,
        *,
        context: SessionContext,
        mapping: LogicalConnectionTransportMap,
        sequence: int,
    ) -> ReconnectGraceService:
        return ReconnectGraceService(
            session_context=context,
            connection_index=self._index,
            transport_mapping=mapping,
            clock=self._clock,
            task_supervisor=self._supervisor,
            task_sequence=sequence,
            policy=ReconnectGracePolicy(
                timeout_seconds=float(self._policy.reconnect_grace_seconds),
            ),
        )

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    @staticmethod
    def _track(
        task: asyncio.Task[object],
        collection: set[asyncio.Task[object]],
    ) -> None:
        collection.add(task)
        task.add_done_callback(collection.discard)


def _negotiation_reason(error: Exception) -> ConnectionRejectionReason:
    details = getattr(error, "details", {})
    reason = details.get("reason") if hasattr(details, "get") else None
    operation = details.get("operation") if hasattr(details, "get") else None
    if operation == "capability_negotiation" or str(reason).startswith("capability_"):
        return ConnectionRejectionReason.CAPABILITY_INCOMPATIBLE
    if reason == "requested_capability_not_authorized":
        return ConnectionRejectionReason.CAPABILITY_INCOMPATIBLE
    if reason in {
        "minimum_major_mismatch",
        "minimum_exceeds_requested",
        "compatible_version_not_found",
    }:
        return ConnectionRejectionReason.MINIMUM_VERSION_INCOMPATIBLE
    if reason in {"major_not_supported", "requested_version_required"}:
        return ConnectionRejectionReason.PROTOCOL_INCOMPATIBLE
    return ConnectionRejectionReason.INTERNAL_FAILURE


def _is_transport_disconnect(error: Exception) -> bool:
    details = getattr(error, "details", {})
    operation = details.get("operation") if hasattr(details, "get") else None
    return operation == "receive"


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _clear_exception(error: Exception) -> None:
    error.__traceback__ = None
    error.__context__ = None
    error.__cause__ = None


async def _cancel_tasks(tasks: tuple[asyncio.Task[object] | None, ...]) -> None:
    actual = tuple(task for task in tasks if task is not None)
    for task in actual:
        if task is not asyncio.current_task() and not task.done():
            task.cancel()
    await asyncio.gather(
        *(task for task in actual if task is not asyncio.current_task()),
        return_exceptions=True,
    )


async def _close_isolated(transport: TransportSession) -> None:
    try:
        await transport.close()
    except Exception:
        pass


def _protocol_error(reason: str) -> None:
    raise NsRuntimeProtocolViolationError(
        details={
            "component": "connection_lifecycle_manager",
            "operation": "ingress",
            "reason": reason,
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection lifecycle manager dependency is invalid.",
        details={
            "component": "connection_lifecycle_manager",
            "field": field_name,
        },
    )


__all__ = (
    "ConnectionLifecycleManager",
    "ConnectionLifecyclePolicy",
)
