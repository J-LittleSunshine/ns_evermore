# -*- coding: utf-8 -*-
from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import replace
from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand, CommandError
from ns_backend.backend.runtime.connector import NsBackendRuntimeConnector, NsBackendRuntimeStubSender
from ns_backend.backend.runtime.sender import NsBackendRuntimeWebSocketSender

from ns_common.config import ns_config
from ns_common.runtime.errors import NsRuntimeError

if TYPE_CHECKING:
    pass


class Command(BaseCommand):
    help = "Run ns_backend runtime connector."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--once",
            action="store_true",
            help="Drain one outbox batch and exit.",
        )
        parser.add_argument(
            "--enable",
            action="store_true",
            help="Force runtime enabled for this process.",
        )
        parser.add_argument(
            "--ipc-mode",
            type=str,
            default="",
            help="Override runtime IPC mode: memory, unix_socket, or tcp.",
        )
        parser.add_argument(
            "--node-id",
            type=str,
            default="",
            help="Override runtime node id.",
        )

        parser.add_argument(
            "--sender",
            type=str,
            default="stub",
            help="Runtime sender type: stub or websocket.",
        )

    def handle(self, *args: object, **options: object) -> None:
        once = bool(options.get("once", False))
        force_enable = bool(options.get("enable", False))
        ipc_mode = str(options.get("ipc_mode") or "").strip()
        node_id = str(options.get("node_id") or "").strip()
        sender_type = str(options.get("sender") or "stub").strip().lower()

        config = ns_config.runtime_config

        if force_enable:
            config = replace(config, enabled=True)

        if ipc_mode:
            config = replace(config, ipc_mode=ipc_mode)  # type: ignore[arg-type]

        if node_id:
            config = replace(config, node_id=node_id)

        try:
            if sender_type == "stub":
                sender = NsBackendRuntimeStubSender()
            elif sender_type == "websocket":
                sender = NsBackendRuntimeWebSocketSender(config)
            else:
                raise CommandError(f"unsupported runtime sender type: {sender_type}")

            connector = NsBackendRuntimeConnector(config=config, sender=sender)
            if once:
                drained = connector.drain_once()
                connector.stop()
                self.stdout.write(self.style.SUCCESS(f"runtime connector drained one batch: {drained}"))
                return

            self.stdout.write(self.style.SUCCESS("runtime connector started."))
            connector.run_forever()
        except NsRuntimeError as exc:
            raise CommandError(str(exc)) from exc
