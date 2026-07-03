# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_runtime.processor.registry import (
    MessageTypeSchema,
    ProcessorRegistration,
    ProcessorRegistry,
    ProcessorStage,
    ReliabilityProfile,
)

_BASE_MESSAGE_FIELDS = frozenset({
    "message_id",
    "type",
    "category",
    "created_at",
}
)


def _schema(required_groups: set[str], allowed_extra_groups: set[str] | None = None, group_fields: dict[str, set[str]] | None = None) -> MessageTypeSchema:
    allowed_groups = frozenset({
        "protocol",
        "message",
        "trace",
        *required_groups,
        *set(allowed_extra_groups or set()),
    }
    )

    return MessageTypeSchema(
        required_groups=frozenset({
            "protocol",
            "message",
            *required_groups,
        }
        ),
        allowed_groups=allowed_groups,
        required_message_fields=_BASE_MESSAGE_FIELDS,
        required_group_fields={
            key: frozenset(value)
            for key, value in (group_fields or {}).items()
        },
    )


class BuiltinProcessorRegistryFactory:
    @staticmethod
    def build() -> ProcessorRegistry:
        registry = ProcessorRegistry()

        connection_schema = _schema(
            {"payload"},
            {"target"},
            {
                "payload": {
                    "mode",
                    "inline",
                },
            },
        )
        heartbeat_schema = _schema(set())
        delivery_schema = _schema(
            {"delivery"},
            {"target"},
            {
                "delivery": {
                    "delivery_id",
                },
            },
        )
        stream_schema = _schema(
            {"stream"},
            {
                "target",
                "delivery",
                "payload",
            },
            {
                "stream": {
                    "stream_id",
                },
            },
        )
        control_schema = _schema(
            {"payload"},
            {"target"},
            {
                "payload": {
                    "mode",
                },
            },
        )
        cluster_schema = _schema(
            {
                "route",
                "payload",
            },
            {"target"},
            {
                "route": {
                    "current_runtime_id",
                    "hop",
                    "max_hops",
                },
            },
        )
        task_schema = _schema(
            {
                "target",
                "payload",
            },
            {
                "callback",
                "delivery",
            },
            {
                "target": {
                    "kind",
                },
                "payload": {
                    "mode",
                },
            },
        )
        error_schema = _schema(
            {"payload"},
            {"target"},
            {
                "payload": {
                    "mode",
                    "inline",
                },
            },
        )

        for registration in (
                ProcessorRegistration("connection.hello", ProcessorStage.CONNECTION, "ConnectionHelloProcessor", frozenset(), connection_schema, ReliabilityProfile.BEST_EFFORT, "runtime.connection.hello", "connection.rejected"),
                ProcessorRegistration("connection.accepted", ProcessorStage.CONNECTION, "ConnectionAcceptedProcessor", frozenset(), connection_schema, ReliabilityProfile.BEST_EFFORT, "runtime.connection.accepted", "runtime.error"),
                ProcessorRegistration("connection.rejected", ProcessorStage.CONNECTION, "ConnectionRejectedProcessor", frozenset(), connection_schema, ReliabilityProfile.BEST_EFFORT, "runtime.connection.rejected", "runtime.error"),
                ProcessorRegistration("connection.reauth", ProcessorStage.CONNECTION, "ConnectionReauthProcessor", frozenset(), connection_schema, ReliabilityProfile.BEST_EFFORT, "runtime.connection.reauth", "connection.reauth_rejected"),
                ProcessorRegistration("connection.reauth_accepted", ProcessorStage.CONNECTION, "ConnectionReauthAcceptedProcessor", frozenset(), connection_schema, ReliabilityProfile.BEST_EFFORT, "runtime.connection.reauth_accepted", "runtime.error"),
                ProcessorRegistration("connection.reauth_rejected", ProcessorStage.CONNECTION, "ConnectionReauthRejectedProcessor", frozenset(), connection_schema, ReliabilityProfile.BEST_EFFORT, "runtime.connection.reauth_rejected", "runtime.error"),
                ProcessorRegistration("connection.heartbeat", ProcessorStage.CONNECTION, "ConnectionHeartbeatProcessor", frozenset(), heartbeat_schema, ReliabilityProfile.BEST_EFFORT, "runtime.connection.heartbeat", "runtime.error"),
                ProcessorRegistration("connection.drain", ProcessorStage.CONNECTION, "ConnectionDrainProcessor", frozenset(), heartbeat_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.connection.drain", "runtime.error"),
                ProcessorRegistration("task.dispatch", ProcessorStage.TASK, "TaskDispatchProcessor", frozenset({"runtime.task.dispatch"}), task_schema, ReliabilityProfile.RELIABLE, "runtime.task.dispatch", "delivery.nack"),
                ProcessorRegistration("task.callback", ProcessorStage.TASK, "TaskCallbackProcessor", frozenset({"runtime.task.callback"}), task_schema, ReliabilityProfile.RELIABLE, "runtime.task.callback", "delivery.nack"),
                ProcessorRegistration("delivery.ack", ProcessorStage.DELIVERY, "DeliveryAckProcessor", frozenset(), delivery_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.delivery.ack", "runtime.error"),
                ProcessorRegistration("delivery.nack", ProcessorStage.DELIVERY, "DeliveryNackProcessor", frozenset(), delivery_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.delivery.nack", "runtime.error"),
                ProcessorRegistration("delivery.defer", ProcessorStage.DELIVERY, "DeliveryDeferProcessor", frozenset(), delivery_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.delivery.defer", "runtime.error"),
                ProcessorRegistration("delivery.dead_letter", ProcessorStage.DELIVERY, "DeliveryDeadLetterProcessor", frozenset({"runtime.delivery.dead_letter"}), delivery_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.delivery.dead_letter", "runtime.error"),
                ProcessorRegistration("delivery.replay", ProcessorStage.DELIVERY, "DeliveryReplayProcessor", frozenset({"runtime.delivery.replay"}), delivery_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.delivery.replay", "runtime.error"),
                ProcessorRegistration("delivery.cancel", ProcessorStage.DELIVERY, "DeliveryCancelProcessor", frozenset({"runtime.delivery.cancel"}), delivery_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.delivery.cancel", "runtime.error"),
                ProcessorRegistration("delivery.hold", ProcessorStage.DELIVERY, "DeliveryHoldProcessor", frozenset({"runtime.delivery.hold"}), delivery_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.delivery.hold", "runtime.error"),
                ProcessorRegistration("stream.start", ProcessorStage.STREAM, "StreamStartProcessor", frozenset(), stream_schema, ReliabilityProfile.STREAM_RELIABLE, "runtime.stream.start", "delivery.nack"),
                ProcessorRegistration("stream.chunk", ProcessorStage.STREAM, "StreamChunkProcessor", frozenset(), stream_schema, ReliabilityProfile.STREAM_RELIABLE, "runtime.stream.chunk", "delivery.nack"),
                ProcessorRegistration("stream.end", ProcessorStage.STREAM, "StreamEndProcessor", frozenset(), stream_schema, ReliabilityProfile.STREAM_RELIABLE, "runtime.stream.end", "delivery.nack"),
                ProcessorRegistration("stream.ack", ProcessorStage.STREAM, "StreamAckProcessor", frozenset(), stream_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.stream.ack", "runtime.error"),
                ProcessorRegistration("runtime.control.health", ProcessorStage.CONTROL, "RuntimeHealthProcessor", frozenset({"runtime.control.health"}), control_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.control.health", "runtime.error"),
                ProcessorRegistration("runtime.control.node_status", ProcessorStage.CONTROL, "RuntimeNodeStatusProcessor", frozenset({"runtime.control.node_status"}), control_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.control.node_status", "runtime.error"),
                ProcessorRegistration("runtime.control.connection_status", ProcessorStage.CONTROL, "RuntimeConnectionStatusProcessor", frozenset({"runtime.control.connection_status"}), control_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.control.connection_status", "runtime.error"),
                ProcessorRegistration("runtime.control.kick_connection", ProcessorStage.CONTROL, "RuntimeKickConnectionProcessor", frozenset({"runtime.control.kick_connection"}), control_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.control.kick_connection", "runtime.error"),
                ProcessorRegistration("runtime.control.config_update", ProcessorStage.CONTROL, "RuntimeConfigUpdateProcessor", frozenset({"runtime.control.config_update"}), control_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.control.config_update", "runtime.error"),
                ProcessorRegistration("runtime.control.rate_limit_update", ProcessorStage.CONTROL, "RuntimeRateLimitUpdateProcessor", frozenset({"runtime.control.rate_limit_update"}), control_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.control.rate_limit_update", "runtime.error"),
                ProcessorRegistration("runtime.control.state_snapshot", ProcessorStage.CONTROL, "RuntimeStateSnapshotProcessor", frozenset({"runtime.control.state_snapshot"}), control_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.control.state_snapshot", "runtime.error"),
                ProcessorRegistration("runtime.error", ProcessorStage.ERROR, "RuntimeErrorProcessor", frozenset(), error_schema, ReliabilityProfile.BEST_EFFORT, "runtime.error", "runtime.error"),
                ProcessorRegistration("cluster.event.node_joined", ProcessorStage.CLUSTER, "ClusterNodeJoinedProcessor", frozenset({"runtime.cluster.event"}), cluster_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.cluster.node_joined", "runtime.error"),
                ProcessorRegistration("cluster.event.node_left", ProcessorStage.CLUSTER, "ClusterNodeLeftProcessor", frozenset({"runtime.cluster.event"}), cluster_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.cluster.node_left", "runtime.error"),
                ProcessorRegistration("cluster.event.master_changed", ProcessorStage.CLUSTER, "ClusterMasterChangedProcessor", frozenset({"runtime.cluster.event"}), cluster_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.cluster.master_changed", "runtime.error"),
                ProcessorRegistration("cluster.event.config_report", ProcessorStage.CLUSTER, "ClusterConfigReportProcessor", frozenset({"runtime.cluster.event"}), cluster_schema, ReliabilityProfile.CONTROL_RELIABLE, "runtime.cluster.config_report", "runtime.error"),
        ):
            registry.register(registration)

        return registry
