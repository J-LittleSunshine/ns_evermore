# -*- coding: utf-8 -*-
from __future__ import annotations

import multiprocessing
import os
import unittest
from unittest import mock

from ns_common.exceptions import NsRuntimeStartupSecurityError
from ns_runtime import authority_bootstrap as bootstrap_module
from ns_runtime.authority_bootstrap import (
    InheritedAuthorityBootstrap,
    load_inherited_authority_bootstrap,
)


class _Connection:
    def __init__(self, *, poll_result: bool = True) -> None:
        self.close_calls = 0
        self.poll_result = poll_result

    def close(self) -> None:
        self.close_calls += 1

    def poll(self, timeout: float) -> bool:
        self.poll_timeout = timeout
        return self.poll_result

    def recv_bytes(self, maximum: int) -> bytes:
        self.recv_maximum = maximum
        return b'{"kind":"fd_custody","version":1}'


class _Attestor:
    public_key = b"a" * 32
    instance_id = "attestor:test"

    def __init__(self) -> None:
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


class _Process:
    def __init__(
        self,
        *,
        start_failure: BaseException | None = None,
        alive_after_start: bool = True,
    ) -> None:
        self.start_failure = start_failure
        self.alive = False
        self.alive_after_start = alive_after_start
        self.start_calls = 0
        self.join_calls = 0
        self.terminate_calls = 0
        self.kill_calls = 0

    def start(self) -> None:
        self.start_calls += 1
        if self.start_failure is not None:
            raise self.start_failure
        self.alive = self.alive_after_start

    def is_alive(self) -> bool:
        return self.alive

    def join(self, timeout: float) -> None:
        del timeout
        self.join_calls += 1

    def terminate(self) -> None:
        self.terminate_calls += 1
        self.alive = False

    def kill(self) -> None:
        self.kill_calls += 1
        self.alive = False


class _StubbornProcess(_Process):
    def terminate(self) -> None:
        self.terminate_calls += 1

    def kill(self) -> None:
        self.kill_calls += 1


class _RetryKillProcess(_StubbornProcess):
    def kill(self) -> None:
        self.kill_calls += 1
        if self.kill_calls == 1:
            raise RuntimeError("kill failed once")
        self.alive = False


class _RetryClose:
    def __init__(self, *, failure: BaseException) -> None:
        self.failure = failure
        self.close_calls = 0
        self.closed = False

    def close(self) -> None:
        self.close_calls += 1
        if self.close_calls == 1:
            raise self.failure
        self.closed = True


class _Context:
    def __init__(
        self,
        *,
        process: _Process,
        pipe_failure_at: int | None = None,
        process_failure: BaseException | None = None,
        lifecycle_poll: bool = True,
    ) -> None:
        self.process = process
        self.pipe_failure_at = pipe_failure_at
        self.process_failure = process_failure
        self.lifecycle_poll = lifecycle_poll
        self.pipe_calls = 0
        self.connections: list[_Connection] = []

    def Pipe(self, *, duplex: bool):
        self.assert_duplex = duplex
        self.pipe_calls += 1
        if self.pipe_failure_at == self.pipe_calls:
            raise RuntimeError("pipe construction failed")
        role = bootstrap_module._ENDPOINT_ROLES[self.pipe_calls - 1]
        parent = _Connection(
            poll_result=(
                self.lifecycle_poll
                if role == "lifecycle"
                else True
            ),
        )
        child = _Connection()
        self.connections.extend((parent, child))
        return parent, child

    def Process(self, **values):
        self.process_values = values
        if self.process_failure is not None:
            raise self.process_failure
        return self.process


class AuthorityBootstrapTransactionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.previous = {
            name: os.environ.get(name)
            for name in (
                "NS_RUNTIME_AUTHORITY_KEY_FD",
                "NS_RUNTIME_AUTHORITY_SECRETS_FD",
            )
        }

    def tearDown(self) -> None:
        for name, value in self.previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def _descriptors(self) -> tuple[int, int]:
        first_read, first_write = os.pipe()
        second_read, second_write = os.pipe()
        os.close(first_write)
        os.close(second_write)
        os.environ["NS_RUNTIME_AUTHORITY_KEY_FD"] = str(first_read)
        os.environ["NS_RUNTIME_AUTHORITY_SECRETS_FD"] = str(second_read)
        return first_read, second_read

    def test_first_valid_descriptor_closes_when_second_parse_fails(self) -> None:
        first_read, first_write = os.pipe()
        os.close(first_write)
        os.environ["NS_RUNTIME_AUTHORITY_KEY_FD"] = str(first_read)
        os.environ["NS_RUNTIME_AUTHORITY_SECRETS_FD"] = "not-a-descriptor"

        with self.assertRaises(NsRuntimeStartupSecurityError):
            load_inherited_authority_bootstrap()

        with self.assertRaises(OSError):
            os.fstat(first_read)

    def test_partial_pipe_failure_rolls_back_fds_connections_and_attestor(
        self,
    ) -> None:
        first_read, second_read = self._descriptors()
        failure = RuntimeError("pipe construction failed")
        process = _Process()
        context = _Context(process=process, pipe_failure_at=2)
        attestor = _Attestor()

        def fail_second_pipe(*, duplex: bool):
            if context.pipe_calls == 1:
                raise failure
            return _Context.Pipe(context, duplex=duplex)

        with (
            mock.patch.object(
                bootstrap_module.multiprocessing,
                "get_context",
                return_value=context,
            ),
            mock.patch(
                "ns_runtime.authority_attestor.start_authority_attestor",
                return_value=attestor,
            ),
            mock.patch.object(context, "Pipe", side_effect=fail_second_pipe),
        ):
            with self.assertRaises(RuntimeError) as raised:
                load_inherited_authority_bootstrap()

        self.assertIs(failure, raised.exception)
        self.assertEqual(1, len(context.connections) // 2)
        self.assertTrue(all(item.close_calls == 1 for item in context.connections))
        self.assertEqual(1, attestor.close_calls)
        for descriptor in (first_read, second_read):
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_process_start_failure_rolls_back_every_acquired_resource(
        self,
    ) -> None:
        first_read, second_read = self._descriptors()
        failure = RuntimeError("process start failed")
        process = _Process(start_failure=failure)
        context = _Context(process=process)
        attestor = _Attestor()

        with (
            mock.patch.object(
                bootstrap_module.multiprocessing,
                "get_context",
                return_value=context,
            ),
            mock.patch(
                "ns_runtime.authority_attestor.start_authority_attestor",
                return_value=attestor,
            ),
        ):
            with self.assertRaises(RuntimeError) as raised:
                load_inherited_authority_bootstrap()

        self.assertIs(failure, raised.exception)
        self.assertEqual(14, len(context.connections))
        self.assertTrue(all(item.close_calls == 1 for item in context.connections))
        self.assertEqual(1, process.start_calls)
        self.assertGreaterEqual(process.join_calls, 1)
        self.assertEqual(1, attestor.close_calls)
        for descriptor in (first_read, second_read):
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_process_constructor_failure_rolls_back_pipes_handles_and_fds(
        self,
    ) -> None:
        first_read, second_read = self._descriptors()
        failure = RuntimeError("process constructor failed")
        process = _Process()
        context = _Context(
            process=process,
            process_failure=failure,
        )
        attestor = _Attestor()

        with (
            mock.patch.object(
                bootstrap_module.multiprocessing,
                "get_context",
                return_value=context,
            ),
            mock.patch(
                "ns_runtime.authority_attestor.start_authority_attestor",
                return_value=attestor,
            ),
        ):
            with self.assertRaises(RuntimeError) as raised:
                load_inherited_authority_bootstrap()

        self.assertIs(failure, raised.exception)
        self.assertEqual(14, len(context.connections))
        self.assertTrue(all(item.close_calls == 1 for item in context.connections))
        self.assertEqual(0, process.start_calls)
        self.assertEqual(1, attestor.close_calls)
        for descriptor in (first_read, second_read):
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_custody_failure_closes_pipes_and_reaps_started_process(self) -> None:
        first_read, second_read = self._descriptors()
        process = _Process()
        context = _Context(
            process=process,
            lifecycle_poll=False,
        )
        attestor = _Attestor()

        with (
            mock.patch.object(
                bootstrap_module.multiprocessing,
                "get_context",
                return_value=context,
            ),
            mock.patch(
                "ns_runtime.authority_attestor.start_authority_attestor",
                return_value=attestor,
            ),
        ):
            with self.assertRaises(NsRuntimeStartupSecurityError):
                load_inherited_authority_bootstrap()

        self.assertFalse(process.is_alive())
        self.assertEqual(1, process.terminate_calls)
        self.assertEqual(1, attestor.close_calls)
        self.assertTrue(all(item.close_calls == 1 for item in context.connections))
        for descriptor in (first_read, second_read):
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_pending_close_is_idempotent_and_reaps_all_owned_resources(
        self,
    ) -> None:
        parents = {}
        children = []
        for role in bootstrap_module._ENDPOINT_ROLES:
            parent, child = multiprocessing.Pipe(duplex=True)
            parents[role] = parent
            children.append(child)
        process = _Process()
        process.alive = True
        attestor = _Attestor()
        bootstrap = InheritedAuthorityBootstrap(
            connections=parents,
            process=process,  # type: ignore[arg-type]
            attestor=attestor,
        )
        try:
            bootstrap.close()
            bootstrap.close()
            self.assertFalse(process.is_alive())
            self.assertEqual(1, process.terminate_calls)
            self.assertEqual(1, attestor.close_calls)
            self.assertTrue(all(parent.closed for parent in parents.values()))
            self.assertFalse(hasattr(InheritedAuthorityBootstrap, "__del__"))
        finally:
            for child in children:
                child.close()

    def test_reap_process_reports_stable_failure_when_kill_cannot_reap(
        self,
    ) -> None:
        process = _StubbornProcess()
        process.alive = True

        failure = bootstrap_module._reap_process(process, started=True)

        self.assertIsInstance(failure, NsRuntimeStartupSecurityError)
        assert isinstance(failure, NsRuntimeStartupSecurityError)
        self.assertEqual(
            "authority_broker_process_did_not_exit",
            failure.details["reason"],
        )
        self.assertTrue(process.is_alive())
        self.assertEqual(1, process.terminate_calls)
        self.assertEqual(1, process.kill_calls)

    def test_pending_close_retries_only_process_that_remains_owned(self) -> None:
        parents = {}
        children = []
        for role in bootstrap_module._ENDPOINT_ROLES:
            parent, child = multiprocessing.Pipe(duplex=True)
            parents[role] = parent
            children.append(child)
        process = _RetryKillProcess()
        process.alive = True
        attestor = _Attestor()
        bootstrap = InheritedAuthorityBootstrap(
            connections=parents,
            process=process,  # type: ignore[arg-type]
            attestor=attestor,
        )
        try:
            with self.assertRaises(RuntimeError):
                bootstrap.close()
            self.assertTrue(process.is_alive())
            self.assertEqual(1, attestor.close_calls)
            self.assertTrue(all(parent.closed for parent in parents.values()))

            bootstrap.close()
            self.assertFalse(process.is_alive())
            self.assertEqual(2, process.kill_calls)
            self.assertEqual(1, attestor.close_calls)
            self.assertTrue(all(parent.closed for parent in parents.values()))
        finally:
            for child in children:
                child.close()

    def test_pending_close_keeps_only_failed_endpoint_for_retry(self) -> None:
        interrupt = KeyboardInterrupt("endpoint close interrupted")
        flaky = _RetryClose(failure=interrupt)
        stable = _RetryClose(failure=RuntimeError("unused"))
        stable.close_calls = 1
        bootstrap = object.__new__(InheritedAuthorityBootstrap)
        bootstrap._connections = {"iam": flaky, "audit": stable}
        bootstrap._process = None
        bootstrap._attestor = None
        bootstrap._consumed = False

        with self.assertRaises(KeyboardInterrupt) as raised:
            bootstrap.close()
        self.assertIs(interrupt, raised.exception)
        self.assertEqual({"iam"}, set(bootstrap._connections))
        self.assertEqual(1, flaky.close_calls)
        self.assertEqual(2, stable.close_calls)

        bootstrap.close()
        self.assertIsNone(bootstrap._connections)
        self.assertEqual(2, flaky.close_calls)
        self.assertEqual(2, stable.close_calls)


if __name__ == "__main__":
    unittest.main()
