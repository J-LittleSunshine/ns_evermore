# -*- coding: utf-8 -*-
"""P05 logical connection composition owner and supervised ingress loops."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeProtocolViolationError,
    NsStateError,
    NsValidationError,
)
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
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
    build_feature_disabled_processors,
    canonical_serialize,
)
from ns_runtime.transport import TransportAdapter, TransportManager, TransportMessage, TransportSession

from .accepted import ConnectionAcceptedEnvelopeBuilder, ConnectionAdmissionActivator, _iso_utc
from .binding import (
    LogicalConnectionTransportMap,
    LogicalSessionIdentityFactory,
)
from .drain import ConnectionDrainService, DrainPolicy
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
    state_machine: LogicalConnectionStateMachine = field(repr=False)
    mapping: LogicalConnectionTransportMap = field(repr=False)
    transport: TransportSession | None = field(repr=False)
    grace: ReconnectGraceService = field(repr=False)
    heartbeat: ConnectionHeartbeatService | None = field(default=None, repr=False)
    drain: ConnectionDrainService | None = field(default=None, repr=False)
    expiry: SessionExpiryController | None = field(default=None, repr=False)
    processors: ConnectionLifecycleProcessorRegistry | None = field(default=None, repr=False)
    read_task: asyncio.Task[object] | None = field(default=None, repr=False)


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
        )
        for value, expected, name in dependencies:
            if not isinstance(value, expected):
                _invalid(name)
        if not isinstance(runtime_id, str) or not runtime_id:
            _invalid("runtime_id")
        if not isinstance(schema_key, str) or not schema_key:
            _invalid("schema_key")
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
        self._schema_key = schema_key
        self._disabled_processors = build_feature_disabled_processors(
            error_builder=error_builder,
            logger=logger,
            registry=protocol_registry,
        )
        self._owners: dict[str, _LogicalOwner] = {}
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
        self._owners.clear()

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
        machine = LogicalConnectionStateMachine()
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
        )
        try:
            inbound = await receiver.receive()
            parsed = HelloClaimParser().parse(inbound)
            protocol = inbound.protocol
            del inbound
        except asyncio.CancelledError:
            await receiver.terminate(LogicalConnectionCloseReason.SHUTDOWN)
            raise
        except Exception:
            return

        if parsed.claims.resume is not None:
            await self._resume(
                parsed,
                protocol=protocol,
                transport=transport,
                candidate_machine=machine,
                sequence=sequence,
            )
            return
        await self._admit_new(
            parsed,
            protocol=protocol,
            transport=transport,
            machine=machine,
            receiver=receiver,
            sequence=sequence,
        )

    async def _admit_new(
        self,
        parsed: ParsedHello,
        *,
        protocol: ProtocolGroup,
        transport: TransportSession,
        machine: LogicalConnectionStateMachine,
        receiver: ConnectionHelloReceiver,
        sequence: int,
    ) -> None:
        rejector = self._rejector(transport, sequence=sequence)
        indexed_connection_id: str | None = None
        request = HandshakeIamRequest(
            claims=parsed.claims,
            credential=parsed.credential,
        )
        try:
            try:
                authority = await self._bounded_iam(request, sequence=sequence)
            except NsRuntimeIamDeniedError:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.IAM_DENIED,
                )
                await receiver.terminate(LogicalConnectionCloseReason.AUTH_FAILED)
                return
            except NsRuntimeIamTimeoutError:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.IAM_UNAVAILABLE,
                )
                await receiver.terminate(LogicalConnectionCloseReason.AUTH_FAILED)
                return
            except Exception:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.IAM_UNAVAILABLE,
                )
                await receiver.terminate(LogicalConnectionCloseReason.AUTH_FAILED)
                return
            if type(authority) is not HandshakeIamAuthority:
                await rejector.send(
                    protocol=protocol,
                    reason=ConnectionRejectionReason.INTERNAL_FAILURE,
                )
                await receiver.terminate(LogicalConnectionCloseReason.AUTH_FAILED)
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
                await receiver.terminate(LogicalConnectionCloseReason.AUTH_FAILED)
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
            except Exception as error:
                await rejector.send(
                    protocol=protocol,
                    reason=_negotiation_reason(error),
                )
                await receiver.terminate(LogicalConnectionCloseReason.PROTOCOL_FAILED)
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
            activator = ConnectionAdmissionActivator(
                connection_index=self._index,
                transport_session=transport,
                envelope_builder=self._accepted_builder,
            )
            await activator.activate(negotiated.context)
            owner = _LogicalOwner(
                context=negotiated.context,
                state_machine=machine,
                mapping=mapping,
                transport=transport,
                grace=self._new_grace(
                    context=negotiated.context,
                    mapping=mapping,
                    sequence=sequence,
                ),
            )
            self._owners[negotiated.context.connection_id] = owner
            await self._activate_owner(owner, sequence=sequence)
        except asyncio.CancelledError:
            if indexed_connection_id is not None:
                await self._close_indexed(
                    parsed_claim_connection_id=indexed_connection_id,
                    transport=transport,
                    reason=LogicalConnectionCloseReason.SHUTDOWN,
                )
            else:
                await receiver.terminate(LogicalConnectionCloseReason.SHUTDOWN)
            raise
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
        candidate_machine: LogicalConnectionStateMachine,
        sequence: int,
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
            await _close_isolated(transport)
            return
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
            timeout_seconds=float(self._policy.handshake_timeout_seconds),
        )
        try:
            resumed = await coordinator.resume(parsed)
            if owner.expiry is not None:
                await owner.expiry.stop()
            owner.context = resumed.session.context
            owner.transport = transport
            owner.grace = self._new_grace(
                context=owner.context,
                mapping=owner.mapping,
                sequence=sequence,
            )
            await self._activate_owner(owner, sequence=sequence)
            try:
                await candidate_machine.transition(LogicalConnectionState.AUTHENTICATED)
                await candidate_machine.transition(LogicalConnectionState.ACTIVE)
            except Exception:
                pass
        except asyncio.CancelledError:
            raise
        except Exception:
            if owner.transport is transport:
                await self._close_owner(
                    owner,
                    LogicalConnectionCloseReason.INTERNAL_ERROR,
                )
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
        )
        owner.heartbeat = heartbeat
        owner.drain = drain
        owner.expiry = expiry
        owner.processors = self._build_processors(owner, sequence=sequence)
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
            expiry_controller=expiry,
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
                if not contract.feature_enabled:
                    await self._send_disabled(owner, envelope)
                    continue
                processors = owner.processors
                if processors is None:
                    _protocol_error("processor_registry_unavailable")
                result = await processors.dispatch(envelope)
                if isinstance(result, ReauthenticatedSession):
                    owner.context = result.context
                    if owner.heartbeat is not None:
                        await owner.heartbeat.replace_session_context(result.context)
                    owner.processors = self._build_processors(
                        owner,
                        sequence=self._next_sequence(),
                    )
                if envelope.message.type == "connection.drain":
                    assert owner.drain is not None
                    await owner.drain.complete()
                    return
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
        return validated

    async def _send_disabled(self, owner: _LogicalOwner, envelope: Envelope) -> None:
        contract = self._registry.require(envelope.message.type)
        processor = self._disabled_processors.get(contract.processor_key)
        if processor is None:
            _protocol_error("disabled_processor_missing")
        response = await processor.process(
            envelope,
            error_context=self._error_context(owner.context),
        )
        transport = owner.transport
        if transport is None:
            _protocol_error("transport_unavailable")
        await transport.send(canonical_serialize(response).decode("utf-8"))

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
        owner.drain = None

    async def _close_owner(
        self,
        owner: _LogicalOwner,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        if owner.heartbeat is not None:
            try:
                await owner.heartbeat.detach_for_reconnect()
            except Exception:
                pass
        if owner.expiry is not None:
            try:
                await owner.expiry.stop()
            except Exception:
                pass
        entry = await self._index.lookup_connection(owner.context.connection_id)
        if entry is not None and entry.state is not LogicalConnectionState.CLOSING:
            try:
                await self._index.transition(
                    owner.context.connection_id,
                    LogicalConnectionState.CLOSING,
                    close_reason=reason,
                )
            except Exception:
                pass
        transport = owner.transport
        if transport is not None:
            await _close_isolated(transport)
        entry = await self._index.lookup_connection(owner.context.connection_id)
        if entry is not None and entry.state is LogicalConnectionState.CLOSING:
            try:
                await self._index.transition(
                    owner.context.connection_id,
                    LogicalConnectionState.CLOSED,
                )
            except Exception:
                pass
        self._owners.pop(owner.context.connection_id, None)

    async def _close_indexed(
        self,
        *,
        parsed_claim_connection_id: str | None,
        transport: TransportSession,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        if parsed_claim_connection_id is not None:
            owner = self._owners.get(parsed_claim_connection_id)
            if owner is not None:
                await self._close_owner(owner, reason)
                return
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
        await _close_isolated(transport)
        if parsed_claim_connection_id is not None:
            entry = await self._index.lookup_connection(parsed_claim_connection_id)
            if entry is not None and entry.state is LogicalConnectionState.CLOSING:
                try:
                    await self._index.transition(
                        parsed_claim_connection_id,
                        LogicalConnectionState.CLOSED,
                    )
                except Exception:
                    pass

    async def _bounded_iam(
        self,
        request: HandshakeIamRequest,
        *,
        sequence: int,
    ) -> HandshakeIamAuthority:
        operation = self._supervisor.create_task(
            self._iam.authenticate(request),
            name=f"logical-iam-{sequence}-operation",
            cancel_order=20,
        )
        deadline = self._supervisor.create_task(
            self._clock.sleep(float(self._policy.handshake_timeout_seconds)),
            name=f"logical-iam-{sequence}-deadline",
            cancel_order=10,
        )
        try:
            await asyncio.wait((operation, deadline), return_when=asyncio.FIRST_COMPLETED)
            if deadline.done() or not operation.done():
                await _cancel_tasks((operation,))
                raise NsRuntimeIamTimeoutError(
                    details={
                        "component": "logical_connection",
                        "operation": "handshake_authentication",
                        "reason": "total_handshake_deadline",
                    },
                )
            result = operation.result()
            return result
        finally:
            await _cancel_tasks((operation, deadline))

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
