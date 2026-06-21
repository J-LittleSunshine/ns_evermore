# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    pass


def ensure_src_on_sys_path() -> Path:
    src_dir = Path(__file__).resolve().parents[2]
    src_text = str(src_dir)

    normalized_paths = {os.path.normcase(os.path.normpath(p)) for p in sys.path if isinstance(p, str)}
    normalized_src = os.path.normcase(os.path.normpath(src_text))

    if normalized_src not in normalized_paths:
        sys.path.insert(0, src_text)

    os.environ["PYTHONPATH"] = src_text
    return src_dir


def show_banner() -> None:
    import multiprocessing
    if multiprocessing.current_process().name != "MainProcess":
        return
    os.system("")

    light_purple: Final[str] = "\033[38;2;196;181;253m"

    reset: Final[str] = "\033[0m"

    banner: Final[str] = r"""
        _   __     ____             __                  __
       / | / /____/ __ )____ ______/ /_____  ____  ____/ /
      /  |/ / ___/ __  / __ `/ ___/ //_/ _ \/ __ \/ __  / 
     / /|  (__  ) /_/ / /_/ / /__/ ,< /  __/ / / / /_/ /  
    /_/ |_/____/_____/\__,_/\___/_/|_|\___/_/ /_/\__,_/   
    """

    print(f"{light_purple}{banner}{reset}")
