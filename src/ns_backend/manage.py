#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys

from backend.bootstrap import ensure_src_on_sys_path

ensure_src_on_sys_path()


def main() -> None:
    """Run Django administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ns_backend.backend.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
