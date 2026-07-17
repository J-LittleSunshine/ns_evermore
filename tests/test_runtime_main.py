# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest

from ns_runtime.main import main


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"


class NsRuntimeMainTestCase(unittest.TestCase):

    def test_main_returns_success(self) -> None:
        self.assertEqual(0, main())

    def test_process_entry_starts_and_exits_as_a_module(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SRC_DIR)

        completed = subprocess.run(
            [sys.executable, "-m", "ns_runtime.main"],
            cwd=ROOT_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)
        self.assertEqual("", completed.stderr)

    def test_importing_component_has_no_process_side_effects(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SRC_DIR)

        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import asyncio, sys; "
                    "before = asyncio.get_event_loop_policy(); "
                    "import ns_runtime; "
                    "after = asyncio.get_event_loop_policy(); "
                    "forbidden = {'django', 'ns_common', 'redis', 'uvloop', "
                    "'valkey', 'websockets'}; "
                    "valid = (before is after and not forbidden.intersection("
                    "sys.modules) and 'ns_runtime.main' not in sys.modules); "
                    "raise SystemExit(0 if valid else 1)"
                ),
            ],
            cwd=ROOT_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
