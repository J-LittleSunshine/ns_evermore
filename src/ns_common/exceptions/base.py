# -*- coding: utf-8 -*-
from __future__ import annotations

from _ns_common_error_types import NsEvermoreError


class NsRuntimeError(NsEvermoreError):
    code = "NS_RUNTIME_ERROR"
    numeric_code = 100300
    default_message = "NsEvermore runtime error."
