# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.iam.repositories import PolicyRepository

if TYPE_CHECKING:
    pass


class PolicyEngineService:
    """Policy evaluator for data-driven policy deny/allow decisions."""

    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

    @staticmethod
    def _match_subject(*, rule: dict[str, Any], subject_bindings: list[tuple[str, int]]) -> bool:
        rule_subject_type = rule.get("subject_type")
        rule_subject_id = rule.get("subject_id")

        if not rule_subject_type and not rule_subject_id:
            return True

        if rule_subject_type and not rule_subject_id:
            return any(binding_type == rule_subject_type for binding_type, _ in subject_bindings)

        if not rule_subject_type and rule_subject_id:
            return any(binding_id == int(rule_subject_id) for _, binding_id in subject_bindings)

        return any(
            binding_type == rule_subject_type and binding_id == int(rule_subject_id)
            for binding_type, binding_id in subject_bindings
        )

    @staticmethod
    def _match_resource(*, rule: dict[str, Any], resource_type: str, resource_id: str) -> bool:
        rule_resource_type = rule.get("resource_type")
        rule_resource_id = rule.get("resource_id")

        if rule_resource_type and str(rule_resource_type) != resource_type:
            return False

        if rule_resource_id and str(rule_resource_id) != resource_id:
            return False

        return True

    @staticmethod
    def _match_condition(*, rule: dict[str, Any], context: dict[str, Any]) -> bool:
        condition_json = rule.get("condition_json")
        if not condition_json:
            return True

        if not isinstance(condition_json, dict):
            return False

        # Current phase supports only simple equals checks: {"eq": {"key": "value"}}
        eq_conditions = condition_json.get("eq")
        if not isinstance(eq_conditions, dict):
            return True

        for key, expected_value in eq_conditions.items():
            if context.get(str(key)) != expected_value:
                return False

        return True

    @classmethod
    def _sort_rules(cls, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def sort_key(item: dict[str, Any]):
            rule_priority = int(item.get("priority") or 0)
            policy_priority = int(item.get("policy__priority") or 0)
            effect = str(item.get("effect") or "").upper()
            effect_weight = 0 if effect == cls.EFFECT_DENY else 1
            return -rule_priority, -policy_priority, effect_weight, int(item.get("id") or 0)

        return sorted(rules, key=sort_key)

    @classmethod
    async def evaluate(
        cls,
        *,
        subject_bindings: list[tuple[str, int]],
        resource_type: str,
        resource_id: str,
        action_code: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Evaluate policy rules and return first matched decision under priority ordering."""
        rule_rows = await PolicyRepository.list_active_rules_for_action(action_code=action_code)
        if not rule_rows:
            return None

        evaluation_context = {} if context is None else dict(context)

        matched_rules: list[dict[str, Any]] = []
        for rule in rule_rows:
            if not cls._match_subject(rule=rule, subject_bindings=subject_bindings):
                continue
            if not cls._match_resource(rule=rule, resource_type=resource_type, resource_id=resource_id):
                continue
            if not cls._match_condition(rule=rule, context=evaluation_context):
                continue
            matched_rules.append(rule)

        if not matched_rules:
            return None

        selected_rule = cls._sort_rules(matched_rules)[0]
        effect = str(selected_rule.get("effect") or "").upper()
        if effect not in {cls.EFFECT_ALLOW, cls.EFFECT_DENY}:
            return None

        return {
            "effect": effect,
            "matched_policy_id": selected_rule.get("policy_id"),
            "matched_rule_id": selected_rule.get("id"),
            "reason": "POLICY_DENY" if effect == cls.EFFECT_DENY else "POLICY_ALLOW",
            "data_scope": selected_rule.get("data_scope"),
        }

