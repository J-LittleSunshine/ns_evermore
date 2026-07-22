# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsRuntimeUnauthorizedMessageTypeError, NsValidationError
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
    SubscriberOutcome,
)
from ns_runtime.protocol import ExtensionObjectSchema, ProtocolVersion


class _Processor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "test.processor"

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
        registry = ProcessorRegistry((_registration(),))
        registry.freeze()
        self.assertIsInstance(registry.resolve(
            message_type="task.dispatch",
            stage=ProcessorStage.MESSAGE_PROCESSOR,
            protocol_version=ProtocolVersion(1, 0, 0),
            feature_flags={"message_family.task": False},
        ), _Processor)
        with self.assertRaises(Exception) as caught:
            registry.resolve(
                message_type="task.dispatch",
                stage=ProcessorStage.MESSAGE_PROCESSOR,
                protocol_version=ProtocolVersion(1, 0, 0),
                feature_flags={"message_family.task": True},
            )
        self.assertEqual("processor_not_registered", caught.exception.details["reason"])


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
                ),
                _registration(
                    feature_flag="plugin.vendor.safe",
                    feature_enabled=True,
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


def _registration(
    *,
    stage: ProcessorStage = ProcessorStage.MESSAGE_PROCESSOR,
    minimum: ProtocolVersion = ProtocolVersion(1, 0, 0),
    maximum: ProtocolVersion = ProtocolVersion(1, 0, 0),
    feature_flag: str = "message_family.task",
    feature_enabled: bool = False,
) -> ProcessorRegistration:
    return ProcessorRegistration(
        message_type="task.dispatch",
        stage=stage,
        minimum_version=minimum,
        maximum_version=maximum,
        feature_flag=feature_flag,
        feature_enabled=feature_enabled,
        processor=_Processor(),
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
        ),),
    )


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
