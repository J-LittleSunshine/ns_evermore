# -*- coding: utf-8 -*-
"""Production IAM client facade backed exclusively by the authority broker."""

from __future__ import annotations

from ns_runtime.authority_broker import ProductionIamAuthorityProxy


# Compatibility name retained for typed P06/P07/P11 dependencies.  It is the
# broker proxy itself, not an in-process HTTP adapter or authority factory.
IamClient = ProductionIamAuthorityProxy


__all__ = ("IamClient", "ProductionIamAuthorityProxy")
