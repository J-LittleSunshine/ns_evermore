#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def ensure_src_on_sys_path() -> None:
    src_dir = Path(__file__).resolve().parent.parent
    src_dir_text = str(src_dir)

    if src_dir_text not in sys.path:
        sys.path.insert(0, src_dir_text)


def main() -> None:
    ensure_src_on_sys_path()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django. Activate the virtual environment and install dependencies first.") from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
