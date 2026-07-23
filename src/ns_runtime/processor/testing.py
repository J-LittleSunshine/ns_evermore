# -*- coding: utf-8 -*-
"""Explicit contract-test authority, isolated from production IAM evidence."""

from __future__ import annotations

from .contracts import (
    AuthorizationDecisionEvidence,
    _issue_contract_test_authorization_evidence,
)


def issue_contract_test_authorization_evidence(
    **values: object,
) -> AuthorizationDecisionEvidence:
    return _issue_contract_test_authorization_evidence(**values)


__all__ = ("issue_contract_test_authorization_evidence",)
