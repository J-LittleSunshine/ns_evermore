# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeUnauthorizedMessageTypeError,
    NsStateError,
    NsValidationError,
)
from ns_runtime.processor import (
    EventBus,
    LocalPluginRegistry,
    LocalTrustedPlugin,
    PipelineProcessor,
    PluginMetadata,
    ProcessorContext,
    ProcessorRegistration,
    ProcessorRegistry,
    ProcessorSafeSummary,
    ProcessorStage,
    ProcessorTraceReference,
    RuntimeEvent,
    SubscriptionHandle,
    SubscriberOutcome,
    UnsubscribeOutcome,
    MessageProcessor,
    MessageProcessorStageProcessor,
    build_standard_stage_processors,
)
from ns_runtime.protocol import ExtensionObjectSchema, ProtocolVersion


class _Processor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "test.processor"

    async def process(self, context: ProcessorContext, value: object) -> object:
        return value


class _MessageBinding(MessageProcessor):
    @property
    def name(self) -> str:
        return "test.message_binding"

    async def process(self, context: ProcessorContext, value: object) -> object:
        return value


class ProcessorRegistryTestCase(unittest.TestCase):
    def test_duplicate_and_overlapping_versions_are_rejected(self) -> None:
        registry = ProcessorRegistry()
        registration = _registration()
        registry.register(registration)
        with self.assertRaisesRegex(NsValidationError, "Duplicate"):
            registry.register(registration)
        with self.assertRaises(NsValidationError) as caught:
            registry.register(_registration(
                minimum=ProtocolVersion(1, 0, 0),
                maximum=ProtocolVersion(1, 1, 0),
            ))
        self.assertEqual("version_conflict", caught.exception.details["reason"])
        with self.assertRaises(NsValidationError):
            _registration(
                minimum=ProtocolVersion(1, 0, 0),
                maximum=ProtocolVersion(2, 0, 0),
            )

    def test_feature_flag_is_a_resolution_dimension(self) -> None:
        message_stage = build_standard_stage_processors(
            message_processor=_MessageBinding(),
        )[ProcessorStage.MESSAGE_PROCESSOR]
        registry = ProcessorRegistry((_registration(processor=message_stage),))
        registry.freeze()
        resolved = registry.resolve(
            message_type="task.dispatch",
            stage=ProcessorStage.MESSAGE_PROCESSOR,
            protocol_version=ProtocolVersion(1, 0, 0),
            feature_flags={"message_family.task": False},
        )
        self.assertIs(resolved, message_stage)
        self.assertIsInstance(resolved, MessageProcessorStageProcessor)
        with self.assertRaises(NsStateError) as caught:
            registry.resolve(
                message_type="task.dispatch",
                stage=ProcessorStage.MESSAGE_PROCESSOR,
                protocol_version=ProtocolVersion(1, 0, 0),
                feature_flags={"message_family.task": True},
            )
        self.assertEqual("processor_not_registered", caught.exception.details["reason"])

    def test_feature_flag_resolution_conflict_is_rejected(self) -> None:
        processor = build_standard_stage_processors(
            message_processor=_MessageBinding(),
        )[ProcessorStage.MESSAGE_PROCESSOR]
        registry = ProcessorRegistry((
            _registration(
                feature_flag="message_family.task_a",
                feature_enabled=True,
                processor=processor,
            ),
            _registration(
                feature_flag="message_family.task_b",
                feature_enabled=True,
                processor=processor,
            ),
        ))
        registry.freeze()

        with self.assertRaises(NsStateError) as caught:
            registry.resolve(
                message_type="task.dispatch",
                stage=ProcessorStage.MESSAGE_PROCESSOR,
                protocol_version=ProtocolVersion(1, 0, 0),
                feature_flags={
                    "message_family.task_a": True,
                    "message_family.task_b": True,
                },
            )
        self.assertEqual(
            "processor_resolution_conflict",
            caught.exception.details["reason"],
        )


class EventBusTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_timeout_and_exception_are_isolated_per_subscriber(self) -> None:
        bus = EventBus(task_supervisor=self.supervisor, default_timeout_seconds=0.05)
        calls: list[str] = []
        blocked = asyncio.Event()

        async def good(event):
            calls.append("good")

        async def bad(event):
            raise RuntimeError("token=subscriber-secret")

        async def slow(event):
            await blocked.wait()

        bus.subscribe(RuntimeEvent, good, name="good")
        bus.subscribe(RuntimeEvent, bad, name="bad")
        bus.subscribe(RuntimeEvent, slow, name="slow", timeout_seconds=0.01)
        report = await bus.publish(_event())
        self.assertEqual(["good"], calls)
        self.assertEqual(
            (
                SubscriberOutcome.SUCCEEDED,
                SubscriberOutcome.FAILED,
                SubscriberOutcome.TIMED_OUT,
            ),
            tuple(item.outcome for item in report.results),
        )
        self.assertEqual(1, report.succeeded_count)
        self.assertEqual((), self.supervisor.failures)

    async def test_subscribe_publish_unsubscribe_and_duplicate_are_stable(self) -> None:
        bus = EventBus(
            task_supervisor=self.supervisor,
            default_timeout_seconds=0.05,
        )
        calls: list[str] = []

        async def subscriber(event):
            calls.append(event.object_id)

        handle = bus.subscribe(RuntimeEvent, subscriber, name="lifecycle")
        self.assertIsInstance(handle, SubscriptionHandle)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            setattr(handle, "subscriber", "changed")
        self.assertEqual(1, bus.subscription_count)
        other_bus = EventBus(
            task_supervisor=self.supervisor,
            default_timeout_seconds=0.05,
        )
        foreign = other_bus.subscribe(
            RuntimeEvent,
            subscriber,
            name="lifecycle",
        )
        self.assertIs(
            UnsubscribeOutcome.NOT_FOUND,
            bus.unsubscribe(foreign),
        )
        self.assertEqual(1, bus.subscription_count)

        first = await bus.publish(_event())
        self.assertEqual(1, first.succeeded_count)
        self.assertEqual([_event().object_id], calls)
        self.assertIs(
            UnsubscribeOutcome.REMOVED,
            bus.unsubscribe(handle),
        )
        self.assertEqual(0, bus.subscription_count)
        self.assertIs(
            UnsubscribeOutcome.NOT_FOUND,
            bus.unsubscribe(handle),
        )
        missing = SubscriptionHandle(
            subscription_id=999,
            subscriber="missing",
            event_type=RuntimeEvent.__name__,
        )
        self.assertIs(
            UnsubscribeOutcome.NOT_FOUND,
            bus.unsubscribe(missing),
        )
        second = await bus.publish(_event())
        self.assertEqual((), second.results)
        self.assertEqual([_event().object_id], calls)

    async def test_unsubscribe_does_not_cancel_in_flight_publish_snapshot(self) -> None:
        bus = EventBus(
            task_supervisor=self.supervisor,
            default_timeout_seconds=0.5,
        )
        entered = asyncio.Event()
        release = asyncio.Event()
        calls: list[str] = []

        async def subscriber(event):
            entered.set()
            await release.wait()
            calls.append(event.object_id)

        handle = bus.subscribe(RuntimeEvent, subscriber, name="in_flight")
        publishing = asyncio.create_task(bus.publish(_event()))
        await entered.wait()

        self.assertIs(
            UnsubscribeOutcome.REMOVED,
            bus.unsubscribe(handle),
        )
        release.set()
        report = await publishing

        self.assertEqual(1, report.succeeded_count)
        self.assertEqual([_event().object_id], calls)
        self.assertEqual((), (await bus.publish(_event())).results)

    def test_event_schema_has_no_sensitive_or_authority_fields(self) -> None:
        field_names = {item.name for item in dataclasses.fields(RuntimeEvent)}
        self.assertEqual({"object_id", "safe_summary", "trace_reference"}, field_names)
        public = repr(_event())
        for forbidden in ("token", "credential", "payload", "iam_response"):
            self.assertNotIn(forbidden, public.casefold())


class LocalPluginRegistryTestCase(unittest.TestCase):
    def test_duplicate_namespace_is_rejected(self) -> None:
        atomic_registry = ProcessorRegistry()
        conflicting = LocalTrustedPlugin(
            metadata=_metadata(),
            registrations=(
                _registration(
                    feature_flag="plugin.vendor.safe",
                    feature_enabled=True,
                    processor=_message_stage(),
                ),
                _registration(
                    feature_flag="plugin.vendor.safe",
                    feature_enabled=True,
                    processor=_message_stage(),
                ),
            ),
        )
        with self.assertRaises(NsValidationError):
            _plugins().register(
                conflicting,
                processor_registry=atomic_registry,
            )
        self.assertEqual((), atomic_registry.registrations)

        registry = ProcessorRegistry()
        plugins = _plugins()
        plugin = _plugin()
        plugins.register(plugin, processor_registry=registry)
        with self.assertRaises(NsValidationError) as caught:
            plugins.register(plugin, processor_registry=registry)
        self.assertEqual("duplicate_namespace", caught.exception.details["reason"])

    def test_invalid_schema_and_unauthorized_plugin_are_rejected(self) -> None:
        with self.assertRaises(NsValidationError):
            PluginMetadata(
                namespace="vendor.safe",
                schema={"payload": "raw"},  # type: ignore[arg-type]
                permissions=("runtime.plugin.execute",),
                timeout_seconds=1,
                state_namespace="plugin.vendor.safe",
                feature_flag="plugin.vendor.safe",
            )
        unauthorized = LocalPluginRegistry(
            allowed_namespaces=frozenset({"vendor.safe"}),
            granted_permissions=frozenset(),
            feature_flags={"plugin.vendor.safe": True},
        )
        with self.assertRaises(NsRuntimeUnauthorizedMessageTypeError):
            unauthorized.register(_plugin(), processor_registry=ProcessorRegistry())

    def test_plugin_cannot_register_a_pipeline_bypass_stage(self) -> None:
        with self.assertRaises(NsValidationError):
            LocalTrustedPlugin(
                metadata=_metadata(),
                registrations=(_registration(
                    stage=ProcessorStage.AUTHORIZATION,
                    feature_flag="plugin.vendor.safe",
                    feature_enabled=True,
                ),),
            )
        with self.assertRaises(NsValidationError) as caught:
            LocalTrustedPlugin(
                metadata=_metadata(),
                registrations=(_registration(
                    feature_flag="plugin.vendor.safe",
                    feature_enabled=True,
                    processor=_Processor(),
                ),),
            )
        self.assertEqual(
            "registration.message_processor_boundary",
            caught.exception.details["field"],
        )


def _registration(
    *,
    stage: ProcessorStage = ProcessorStage.MESSAGE_PROCESSOR,
    minimum: ProtocolVersion = ProtocolVersion(1, 0, 0),
    maximum: ProtocolVersion = ProtocolVersion(1, 0, 0),
    feature_flag: str = "message_family.task",
    feature_enabled: bool = False,
    processor: PipelineProcessor | None = None,
) -> ProcessorRegistration:
    effective_processor = processor
    if effective_processor is None:
        effective_processor = (
            _message_stage()
            if stage is ProcessorStage.MESSAGE_PROCESSOR
            else _Processor()
        )
    return ProcessorRegistration(
        message_type="task.dispatch",
        stage=stage,
        minimum_version=minimum,
        maximum_version=maximum,
        feature_flag=feature_flag,
        feature_enabled=feature_enabled,
        processor=effective_processor,
    )


def _metadata() -> PluginMetadata:
    return PluginMetadata(
        namespace="vendor.safe",
        schema=ExtensionObjectSchema(required_fields=("object_id",)),
        permissions=("runtime.plugin.execute",),
        timeout_seconds=0.5,
        state_namespace="plugin.vendor.safe",
        feature_flag="plugin.vendor.safe",
    )


def _plugin() -> LocalTrustedPlugin:
    return LocalTrustedPlugin(
        metadata=_metadata(),
        registrations=(_registration(
            feature_flag="plugin.vendor.safe",
            feature_enabled=True,
            processor=_message_stage(),
        ),),
    )


def _message_stage() -> PipelineProcessor:
    return build_standard_stage_processors(
        message_processor=_MessageBinding(),
    )[ProcessorStage.MESSAGE_PROCESSOR]


def _plugins() -> LocalPluginRegistry:
    return LocalPluginRegistry(
        allowed_namespaces=frozenset({"vendor.safe"}),
        granted_permissions=frozenset({"runtime.plugin.execute"}),
        feature_flags={"plugin.vendor.safe": True},
    )


def _event() -> RuntimeEvent:
    return RuntimeEvent(
        object_id="message_01K0TEST",
        safe_summary=ProcessorSafeSummary(
            message_type="task.dispatch",
            category="task",
            object_reference="sha256:0123456789abcdef",
        ),
        trace_reference=ProcessorTraceReference(value="trace:test"),
    )


if __name__ == "__main__":
    unittest.main()
