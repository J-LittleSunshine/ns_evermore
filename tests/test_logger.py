# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

import ns_common.logger as logger_module
from ns_common.exceptions import NsValidationError
from ns_common.logger import (
    NsLogger,
    _ConsoleTextLogFormatter,
    _JSON_OUTPUT_RESERVED_KEYS,
    _JsonLogFormatter,
    _SanitizingTextLogFormatter,
    get_ns_logger,
)
from ns_common.security import (
    REDACTED,
    Sanitizer,
)


@dataclass
class EnvelopeLike:
    message_id: str
    token: str
    task_payload: dict[str, object]
    capabilities: list[str]

    def __str__(self) -> str:
        raise RuntimeError("envelope-str-secret")


class ExplodingExtra:

    def __init__(self) -> None:
        object.__setattr__(self, "raw", "extra-object-secret")

    def __getattribute__(self, name: str) -> object:
        if name == "__dict__":
            raise RuntimeError("extra-vars-secret")
        return object.__getattribute__(self, name)


class ExplodingMessage:

    def __str__(self) -> str:
        raise RuntimeError("message-str-secret")


class InterruptingExtra:

    def __getattribute__(self, name: str) -> object:
        if name == "__dict__":
            raise KeyboardInterrupt("logger-interrupt-secret")
        return object.__getattribute__(self, name)


class ExitingError(Exception):

    def __str__(self) -> str:
        raise SystemExit("logger-exit-secret")


class LoggerSanitizerTestCase(unittest.TestCase):

    def test_explicit_logger_config_avoids_global_config_and_uses_explicit_root(
        self,
    ) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        source = r'''
import json
import pathlib
import sys
import tempfile

from ns_common.logger import NsLogger, close_ns_loggers
from ns_common.security import Sanitizer
import ns_common.config.model as config_model

assert "ns_config" not in vars(config_model)
with tempfile.TemporaryDirectory() as temporary_directory:
    root = pathlib.Path(temporary_directory)
    logger = NsLogger(
        "explicit-runtime",
        sanitizer=Sanitizer(),
        config={
            "console": False,
            "level": "INFO",
            "file_level": "INFO",
            "format_type": "json",
            "file_format_type": "json",
            "level_files": (),
            "delay": False,
        },
        log_dir=root,
    )
    logger.error(
        "token=logger-message-secret",
        extra={"payload": "logger-payload-secret", "event": "safe-event"},
    )
    close_ns_loggers()
    files = list((root / "explicit-runtime").rglob("explicit-runtime.log"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8").strip())
    serialized = json.dumps(payload, allow_nan=False)
    assert payload["event"] == "safe-event"
    assert "logger-message-secret" not in serialized
    assert "logger-payload-secret" not in serialized
assert "ns_config" not in vars(config_model)
'''
        completed = subprocess.run(
            [sys.executable, "-c", source],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_concurrent_handler_dependency_is_loaded_lazily(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            part
            for part in (
                str(Path(__file__).resolve().parents[1] / "src"),
                environment.get("PYTHONPATH", ""),
            )
            if part
        )
        source = (
            "import pathlib, sys, tempfile; "
            "import ns_common.logger as module; "
            "assert 'concurrent_log_handler' not in sys.modules; "
            "assert 'portalocker' not in sys.modules; "
            "assert 'redis' not in sys.modules; "
            "temporary = tempfile.TemporaryDirectory(); "
            "module.LOG_DIR = pathlib.Path(temporary.name); "
            "logger = module.NsLogger('lazy-multiprocess', multiprocessing_mode=True); "
            "assert 'concurrent_log_handler' in sys.modules; "
            "assert 'portalocker' in sys.modules; "
            "assert module._BackupConcurrentTimedRotatingFileHandler is not None; "
            "logger._reset_handlers(); temporary.cleanup()"
        )
        completed = subprocess.run(
            [sys.executable, "-c", source],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def assert_json_safe_and_no_leak(
        self,
        result: object,
        *secrets: str,
    ) -> str:
        serialized = json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
        )
        for secret in secrets:
            with self.subTest(secret=secret):
                self.assertNotIn(secret, serialized)
        return serialized

    @staticmethod
    def make_record(
        *,
        message: object = "ordinary message",
        args: tuple[object, ...] = (),
        extra: dict[object, object] | None = None,
        exc_info: object = None,
        stack_info: str | None = None,
        level: int = logging.INFO,
    ) -> logging.LogRecord:
        record = logging.LogRecord(
            name="tests.logger",
            level=level,
            pathname=__file__,
            lineno=100,
            msg=message,
            args=args,
            exc_info=exc_info,
        )
        record.stack_info = stack_info
        if extra:
            record.__dict__.update(extra)
        return record

    def test_json_formatter_delegates_message_extra_and_envelope(self) -> None:
        sanitizer = Sanitizer()
        formatter = _JsonLogFormatter(sanitizer=sanitizer, utc_enabled=True)
        envelope = EnvelopeLike(
            message_id="msg_safe",
            token="envelope-token-secret",
            task_payload={"body": "envelope-payload-secret"},
            capabilities=["envelope-capability-secret"],
        )
        record = self.make_record(
            message="token=message-token-secret",
            extra={
                "token": "extra-token-secret",
                "payload": {"body": "extra-payload-secret"},
                "capabilities": ["extra-capability-secret"],
                "envelope": envelope,
                "nan": float("nan"),
                42: "safe-non-string-key-value",
            },
        )

        with mock.patch.object(
            sanitizer,
            "sanitize",
            wraps=sanitizer.sanitize,
        ) as sanitize_call:
            output = formatter.format(record)

        payload = json.loads(output)
        sanitize_call.assert_called_once()
        self.assertEqual(REDACTED, payload["token"])
        self.assertEqual(REDACTED, payload["payload"])
        self.assertRegex(
            payload["capabilities"],
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assertEqual(REDACTED, payload["envelope"]["token"])
        self.assertEqual(REDACTED, payload["envelope"]["task_payload"])
        self.assertRegex(
            payload["envelope"]["capabilities"],
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assertEqual("[NON_FINITE_NUMBER]", payload["nan"])
        self.assertIn("<int>", payload)
        self.assert_json_safe_and_no_leak(
            payload,
            "message-token-secret",
            "extra-token-secret",
            "extra-payload-secret",
            "extra-capability-secret",
            "envelope-token-secret",
            "envelope-payload-secret",
            "envelope-capability-secret",
            "envelope-str-secret",
        )

    def test_json_formatter_sanitizes_exception_and_traceback_metadata(self) -> None:
        formatter = _JsonLogFormatter(sanitizer=Sanitizer())
        try:
            raise NsValidationError(
                "token=exception-message-secret",
                details={
                    "api_key": "exception-detail-secret",
                    "safe_detail": "visible-detail",
                },
            )
        except NsValidationError:
            exc_info = sys.exc_info()

        record = self.make_record(
            message="request failed",
            exc_info=exc_info,
        )
        payload = json.loads(formatter.format(record))

        exception = payload["exception"]
        self.assertEqual(
            "NsValidationError",
            exception["error"]["type"],
        )
        self.assertEqual(
            REDACTED,
            exception["error"]["details"]["api_key"],
        )
        self.assertEqual(
            "visible-detail",
            exception["error"]["details"]["safe_detail"],
        )
        self.assertTrue(exception["traceback"])
        self.assertEqual(
            {"filename", "lineno", "function"},
            set(exception["traceback"][0]),
        )
        self.assert_json_safe_and_no_leak(
            payload,
            "exception-message-secret",
            "exception-detail-secret",
        )

    def test_json_formatter_isolates_all_authoritative_field_conflicts(self) -> None:
        formatter = _JsonLogFormatter(sanitizer=Sanitizer(), utc_enabled=True)
        try:
            raise NsValidationError("real exception")
        except NsValidationError:
            exc_info = sys.exc_info()

        conflicting_extra = {
            "timestamp": {"token": "timestamp-token-secret"},
            "level": "Authorization: Bearer level-auth-secret",
            "logger": "https://example.test/log?signature=logger-signature-secret",
            "message": {"task_payload": "message-payload-secret"},
            "func_name": "caller-function",
            "process_name": "caller-process",
            "thread_name": "caller-thread",
            "exception": {"password": "exception-password-secret"},
            "stack": "Proxy-Authorization: Basic stack-auth-secret",
            "extra_fields": {
                "token=first-key-secret": "first-value",
                "token=second-key-secret": "second-value",
            },
            "request_id": "safe-request-id",
        }
        record = self.make_record(
            message="real message",
            extra=conflicting_extra,
            exc_info=exc_info,
            stack_info="real stack",
        )

        payload = json.loads(formatter.format(record))

        self.assertEqual(_JSON_OUTPUT_RESERVED_KEYS, frozenset({
            "timestamp",
            "level",
            "logger",
            "message",
            "module",
            "filename",
            "lineno",
            "func_name",
            "process",
            "process_name",
            "thread",
            "thread_name",
            "exception",
            "stack",
            "extra_fields",
        }))
        self.assertNotEqual(conflicting_extra["timestamp"], payload["timestamp"])
        self.assertEqual("INFO", payload["level"])
        self.assertEqual("tests.logger", payload["logger"])
        self.assertEqual("real message", payload["message"])
        self.assertEqual(Path(__file__).name, payload["filename"])
        self.assertEqual(100, payload["lineno"])
        self.assertNotEqual("caller-process", payload["process_name"])
        self.assertNotEqual("caller-thread", payload["thread_name"])
        self.assertEqual("NsValidationError", payload["exception"]["error"]["type"])
        self.assertEqual("real stack", payload["stack"])
        self.assertEqual("safe-request-id", payload["request_id"])

        isolated = payload["extra_fields"]
        self.assertEqual(
            set(conflicting_extra).difference({"request_id"}),
            set(isolated),
        )
        self.assertEqual(REDACTED, isolated["timestamp"]["token"])
        self.assertIn(REDACTED, isolated["level"])
        self.assertIn("signature=%5BREDACTED%5D", isolated["logger"])
        self.assertEqual(REDACTED, isolated["message"]["task_payload"])
        self.assertEqual(REDACTED, isolated["exception"]["password"])
        self.assertIn(REDACTED, isolated["stack"])
        nested_container = isolated["extra_fields"]
        self.assertEqual("first-value", nested_container["token=[REDACTED]"])
        self.assertEqual("second-value", nested_container["token=[REDACTED]#2"])
        self.assert_json_safe_and_no_leak(
            payload,
            "timestamp-token-secret",
            "level-auth-secret",
            "logger-signature-secret",
            "message-payload-secret",
            "exception-password-secret",
            "stack-auth-secret",
            "first-key-secret",
            "second-key-secret",
        )

    def test_text_and_color_formatters_keep_authoritative_aliases(self) -> None:
        format_string = (
            "%(levelname)s|%(name)s|%(level)s|%(logger)s|%(message)s|"
            "%(func_name)s|%(process_name)s|%(thread_name)s|"
            "%(request_id)s|%(extra_fields)s"
        )
        text_formatter = _SanitizingTextLogFormatter(
            sanitizer=Sanitizer(),
            fmt=format_string,
        )
        color_formatter = _ConsoleTextLogFormatter(
            sanitizer=Sanitizer(),
            fmt=format_string,
        )
        conflicting_extra = {
            "level": "caller-level",
            "logger": "caller-logger",
            "message": {"payload": "text-conflict-payload-secret"},
            "func_name": "caller-function",
            "process_name": "caller-process",
            "thread_name": "caller-thread",
            "extra_fields": {"Authorization": "Basic text-auth-secret"},
            "request_id": "safe-text-request",
        }

        text_record = self.make_record(
            message="real text message",
            extra=conflicting_extra,
        )
        color_record = self.make_record(
            message="real color message",
            extra=conflicting_extra,
            level=logging.ERROR,
        )
        text_output = text_formatter.format(text_record)
        color_output = color_formatter.format(color_record)

        self.assertTrue(text_output.startswith(
            "INFO|tests.logger|INFO|tests.logger|real text message|"
        ))
        self.assertIn("|safe-text-request|", text_output)
        self.assertIn("'level': 'caller-level'", text_output)
        self.assertIn("'logger': 'caller-logger'", text_output)
        self.assertIn(REDACTED, text_output)
        self.assertTrue(color_output.startswith("\033[31mERROR|tests.logger|ERROR|tests.logger|"))
        self.assertTrue(color_output.endswith("\033[0m"))
        self.assert_json_safe_and_no_leak(
            {"text": text_output, "color": color_output},
            "text-conflict-payload-secret",
            "text-auth-secret",
        )

    def test_formatter_sanitizes_object_messages_and_format_arguments_first(self) -> None:
        formatter = _JsonLogFormatter(sanitizer=Sanitizer())
        envelope = EnvelopeLike(
            message_id="msg_object",
            token="message-object-token-secret",
            task_payload={"body": "message-object-payload-secret"},
            capabilities=["message-object-capability-secret"],
        )

        object_payload = json.loads(formatter.format(self.make_record(
            message=envelope,
        )))
        argument_payload = json.loads(formatter.format(self.make_record(
            message="envelope=%s",
            args=(envelope,),
        )))

        self.assertIn("msg_object", object_payload["message"])
        self.assertIn(REDACTED, object_payload["message"])
        self.assertIn("msg_object", argument_payload["message"])
        self.assertIn(REDACTED, argument_payload["message"])
        self.assert_json_safe_and_no_leak(
            {
                "object": object_payload,
                "argument": argument_payload,
            },
            "message-object-token-secret",
            "message-object-payload-secret",
            "message-object-capability-secret",
            "envelope-str-secret",
        )

    def test_json_formatter_is_fail_closed_for_message_and_extra_failures(self) -> None:
        formatter = _JsonLogFormatter(sanitizer=Sanitizer())
        record = self.make_record(
            message=ExplodingMessage(),
            extra={"context": ExplodingExtra()},
        )

        payload = json.loads(formatter.format(record))

        self.assertIn("ExplodingMessage", payload["message"])
        self.assertEqual("[SANITIZATION_FAILED]", payload["context"])
        self.assert_json_safe_and_no_leak(
            payload,
            "message-str-secret",
            "extra-object-secret",
            "extra-vars-secret",
        )

    def test_text_formatter_preserves_formatting_after_sanitization(self) -> None:
        formatter = _SanitizingTextLogFormatter(
            sanitizer=Sanitizer(),
            fmt="%(levelname)s %(message)s token=%(token)s envelope=%(envelope)s",
        )
        envelope = EnvelopeLike(
            message_id="msg_safe",
            token="text-envelope-token-secret",
            task_payload={"body": "text-envelope-payload-secret"},
            capabilities=["text-envelope-capability-secret"],
        )
        record = self.make_record(
            message="hello %s token=text-message-secret",
            args=("world",),
            extra={
                "token": "text-extra-token-secret",
                "envelope": envelope,
            },
        )

        output = formatter.format(record)

        self.assertIn("INFO hello world", output)
        self.assertIn(f"token={REDACTED}", output)
        self.assert_json_safe_and_no_leak(
            output,
            "text-message-secret",
            "text-extra-token-secret",
            "text-envelope-token-secret",
            "text-envelope-payload-secret",
            "text-envelope-capability-secret",
            "envelope-str-secret",
        )

    def test_text_and_color_exception_output_is_sanitized(self) -> None:
        try:
            raise NsValidationError(
                "token=text-exception-secret",
                details={"password": "text-detail-secret"},
            )
        except NsValidationError:
            exc_info = sys.exc_info()

        text_formatter = _SanitizingTextLogFormatter(
            sanitizer=Sanitizer(),
            fmt="%(levelname)s %(message)s exc_info=%(exc_info)s",
        )
        color_formatter = _ConsoleTextLogFormatter(
            sanitizer=Sanitizer(),
            fmt="%(levelname)s %(message)s token=%(token)s",
        )
        text_output = text_formatter.format(self.make_record(
            message="text failure",
            exc_info=exc_info,
            level=logging.ERROR,
        ))
        color_output = color_formatter.format(self.make_record(
            message="token=color-message-secret",
            extra={"token": "color-extra-secret"},
            level=logging.ERROR,
        ))

        self.assertIn('"type":"NsValidationError"', text_output)
        self.assertIn("exc_info=None", text_output)
        self.assertIn("\033[31m", color_output)
        self.assert_json_safe_and_no_leak(
            {"text": text_output, "color": color_output},
            "text-exception-secret",
            "text-detail-secret",
            "color-message-secret",
            "color-extra-secret",
        )

    def test_logger_does_not_swallow_process_level_exceptions(self) -> None:
        formatter = _JsonLogFormatter(sanitizer=Sanitizer())
        interrupt_record = self.make_record(
            extra={"context": InterruptingExtra()},
        )
        try:
            raise ExitingError("business-exit-secret")
        except ExitingError:
            exit_record = self.make_record(exc_info=sys.exc_info())

        with self.assertRaises(KeyboardInterrupt):
            formatter.format(interrupt_record)
        with self.assertRaises(SystemExit):
            formatter.format(exit_record)
        self.assert_json_safe_and_no_leak(
            {"status": "process-exceptions-propagated"},
            "logger-interrupt-secret",
            "logger-exit-secret",
            "business-exit-secret",
        )

    def test_ns_logger_owns_and_reconfigures_injected_sanitizer(self) -> None:
        logger_name = f"tests.logger.{uuid.uuid4().hex}"
        first_sanitizer = Sanitizer(max_depth=4)
        second_sanitizer = Sanitizer(max_depth=5)

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            logger_module,
            "LOG_DIR",
            Path(temp_dir),
        ):
            logger = get_ns_logger(logger_name, sanitizer=first_sanitizer)
            try:
                self.assertIsInstance(logger, NsLogger)
                self.assertIs(first_sanitizer, logger.sanitizer)
                self.assertTrue(logger.handlers)
                self.assertTrue(all(
                    getattr(handler.formatter, "_sanitizer", None)
                    is first_sanitizer
                    for handler in logger.handlers
                ))

                same_logger = get_ns_logger(logger_name)
                self.assertIs(logger, same_logger)
                self.assertIs(first_sanitizer, same_logger.sanitizer)

                reconfigured = get_ns_logger(
                    logger_name,
                    sanitizer=second_sanitizer,
                )
                self.assertIs(logger, reconfigured)
                self.assertIs(second_sanitizer, reconfigured.sanitizer)
                self.assertTrue(all(
                    getattr(handler.formatter, "_sanitizer", None)
                    is second_sanitizer
                    for handler in reconfigured.handlers
                ))
            finally:
                logger._reset_handlers()
                logger._initialized = False
                logger._owner_pid = -1
                with logger_module._LOGGER_LOCK:
                    logger_module._LOGGER_MAP.pop(logger_name, None)

        with self.assertRaises(TypeError):
            get_ns_logger(
                f"{logger_name}.invalid",
                sanitizer=object(),  # type: ignore[arg-type]
            )

    def test_ns_logger_end_to_end_file_output_has_zero_leakage(self) -> None:
        logger_name = f"tests.logger.e2e.{uuid.uuid4().hex}"
        sanitizer = Sanitizer()

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            logger_module,
            "LOG_DIR",
            Path(temp_dir),
        ):
            logger = get_ns_logger(logger_name, sanitizer=sanitizer)
            try:
                for handler in list(logger.handlers):
                    if (
                        isinstance(handler, logging.StreamHandler)
                        and not isinstance(handler, logging.FileHandler)
                    ):
                        logger.removeHandler(handler)
                        handler.close()

                try:
                    raise NsValidationError(
                        "token=e2e-exception-secret",
                        details={"password": "e2e-detail-secret"},
                    )
                except NsValidationError:
                    logger.error(
                        "failed token=e2e-message-secret",
                        extra={
                            "payload": {"body": "e2e-payload-secret"},
                            "request_id": "safe-request-id",
                            "timestamp": "caller-timestamp",
                            "level": "Authorization: Bearer e2e-level-secret",
                            "logger": "caller-logger",
                            "func_name": "caller-function",
                            "process_name": "caller-process",
                            "thread_name": "caller-thread",
                            "exception": {"token": "e2e-fake-exception-secret"},
                            "stack": "Set-Cookie: session=e2e-stack-secret",
                            "extra_fields": {
                                "signature=first-e2e-key-secret": "first",
                                "signature=second-e2e-key-secret": "second",
                            },
                        },
                        exc_info=True,
                    )

                for handler in logger.handlers:
                    handler.flush()
                log_files = list(Path(temp_dir).rglob("*.log"))
                self.assertTrue(log_files)
                lines = [
                    line
                    for log_file in log_files
                    for line in log_file.read_text(encoding="utf-8").splitlines()
                    if line
                ]
                self.assertTrue(lines)
                payloads = [json.loads(line) for line in lines]
                self.assertTrue(all(
                    payload["request_id"] == "safe-request-id"
                    for payload in payloads
                ))
                self.assertTrue(all(
                    payload["payload"] == REDACTED
                    for payload in payloads
                ))
                self.assertTrue(all(payload["level"] == "ERROR" for payload in payloads))
                self.assertTrue(all(payload["logger"] == logger_name for payload in payloads))
                self.assertTrue(all(
                    payload["timestamp"] != "caller-timestamp"
                    for payload in payloads
                ))
                self.assertTrue(all(
                    payload["exception"]["error"]["type"] == "NsValidationError"
                    for payload in payloads
                ))
                self.assertTrue(all(
                    set(payload["extra_fields"]) == {
                        "timestamp",
                        "level",
                        "logger",
                        "func_name",
                        "process_name",
                        "thread_name",
                        "exception",
                        "stack",
                        "extra_fields",
                    }
                    for payload in payloads
                ))
                self.assertTrue(all(
                    payload["extra_fields"]["extra_fields"]
                    ["signature=[REDACTED]"] == "first"
                    and payload["extra_fields"]["extra_fields"]
                    ["signature=[REDACTED]#2"] == "second"
                    for payload in payloads
                ))
                self.assert_json_safe_and_no_leak(
                    payloads,
                    "e2e-exception-secret",
                    "e2e-detail-secret",
                    "e2e-message-secret",
                    "e2e-payload-secret",
                    "e2e-level-secret",
                    "e2e-fake-exception-secret",
                    "e2e-stack-secret",
                    "first-e2e-key-secret",
                    "second-e2e-key-secret",
                )
            finally:
                logger._reset_handlers()
                logger._initialized = False
                logger._owner_pid = -1
                with logger_module._LOGGER_LOCK:
                    logger_module._LOGGER_MAP.pop(logger_name, None)


if __name__ == "__main__":
    unittest.main()
