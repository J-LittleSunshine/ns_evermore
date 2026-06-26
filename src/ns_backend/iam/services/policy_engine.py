# -*- coding: utf-8 -*-
from __future__ import annotations

import ipaddress
from datetime import (
    datetime,
    time,
)
from typing import (
    Any,
    TYPE_CHECKING,
)

from ns_backend.iam.constants import (
    PERMISSION_EFFECT_ALLOW,
    PERMISSION_EFFECT_DENY,
)
from ns_backend.iam.repositories import RuntimeAuthorizeRepository

if TYPE_CHECKING:
    pass


class PolicyEngineService:
    EFFECT_ALLOW = PERMISSION_EFFECT_ALLOW
    EFFECT_DENY = PERMISSION_EFFECT_DENY

    SUPPORTED_OPERATORS: tuple[str, ...] = (
        "eq",
        "neq",
        "in",
        "not_in",
        "gt",
        "gte",
        "lt",
        "lte",
        "contains",
        "time_range",
        "ip_range",
    )

    @classmethod
    async def evaluate(cls, *, subject_bindings: list[tuple[str, int]], resource_type: str, resource_id: str, action_code: str, context: dict[str, Any] | None = None) -> dict[str, Any] | None:
        rule_rows = await RuntimeAuthorizeRepository.list_active_policy_rules_for_action(
            action_code=action_code,
        )

        if not rule_rows:
            return None

        evaluation_context = {} if context is None else dict(context)

        matched_rules: list[dict[str, Any]] = []

        for rule in rule_rows:
            if not cls.match_subject(
                    rule=rule,
                    subject_bindings=subject_bindings,
            ):
                continue

            if not cls.match_resource(
                    rule=rule,
                    resource_type=resource_type,
                    resource_id=resource_id,
            ):
                continue

            if not cls.match_condition(
                    rule=rule,
                    context=evaluation_context,
            ):
                continue

            matched_rules.append(rule)

        if not matched_rules:
            return None

        selected_rule = cls.sort_rules(matched_rules)[0]
        effect = str(selected_rule.get("effect") or "").strip().upper()

        if effect not in (
                cls.EFFECT_ALLOW,
                cls.EFFECT_DENY,
        ):
            return None

        return {
            "effect": effect,
            "matched_policy_id": selected_rule.get("policy_id"),
            "matched_rule_id": selected_rule.get("id"),
            "reason": "POLICY_DENY" if effect == cls.EFFECT_DENY else "POLICY_ALLOW",
            "data_scope": selected_rule.get("data_scope"),
        }

    @staticmethod
    def match_subject(*, rule: dict[str, Any], subject_bindings: list[tuple[str, int]]) -> bool:
        rule_subject_type = rule.get("subject_type")
        rule_subject_id = rule.get("subject_id")

        if not rule_subject_type and not rule_subject_id:
            return True

        normalized_type = str(rule_subject_type or "").strip().upper() or None

        if normalized_type and not rule_subject_id:
            return any(
                binding_type == normalized_type
                for binding_type, _ in subject_bindings
            )

        if not normalized_type and rule_subject_id:
            return any(
                binding_id == int(rule_subject_id)
                for _, binding_id in subject_bindings
            )

        return any(
            binding_type == normalized_type and binding_id == int(rule_subject_id)
            for binding_type, binding_id in subject_bindings
        )

    @staticmethod
    def match_resource(*, rule: dict[str, Any], resource_type: str, resource_id: str) -> bool:
        rule_resource_type = rule.get("resource_type")
        rule_resource_id = rule.get("resource_id")

        if rule_resource_type and str(rule_resource_type).strip().lower() != resource_type:
            return False

        if rule_resource_id and str(rule_resource_id).strip() != resource_id:
            return False

        return True

    @classmethod
    def match_condition(cls, *, rule: dict[str, Any], context: dict[str, Any]) -> bool:
        condition_json = rule.get("condition_json")

        if not condition_json:
            return True

        if not isinstance(condition_json, dict):
            return False

        for operator in cls.SUPPORTED_OPERATORS:
            if operator not in condition_json:
                continue

            matcher = getattr(cls, f"match_operator_{operator}")
            if not matcher(
                    context=context,
                    payload=condition_json.get(operator),
            ):
                return False

        return True

    @staticmethod
    def match_operator_eq(*, context: dict[str, Any], payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        for key, expected_value in payload.items():
            if context.get(str(key)) != expected_value:
                return False

        return True

    @staticmethod
    def match_operator_neq(*, context: dict[str, Any], payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        for key, expected_value in payload.items():
            if context.get(str(key)) == expected_value:
                return False

        return True

    @staticmethod
    def match_operator_in(*, context: dict[str, Any], payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        for key, expected_values in payload.items():
            if not isinstance(expected_values, (list, tuple, set)):
                return False

            if context.get(str(key)) not in expected_values:
                return False

        return True

    @staticmethod
    def match_operator_not_in(*, context: dict[str, Any], payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        for key, expected_values in payload.items():
            if not isinstance(expected_values, (list, tuple, set)):
                return False

            if context.get(str(key)) in expected_values:
                return False

        return True

    @classmethod
    def match_operator_gt(cls, *, context: dict[str, Any], payload: Any) -> bool:
        return cls.match_compare_operator(
            context=context,
            payload=payload,
            operator="gt",
        )

    @classmethod
    def match_operator_gte(cls, *, context: dict[str, Any], payload: Any) -> bool:
        return cls.match_compare_operator(
            context=context,
            payload=payload,
            operator="gte",
        )

    @classmethod
    def match_operator_lt(cls, *, context: dict[str, Any], payload: Any) -> bool:
        return cls.match_compare_operator(
            context=context,
            payload=payload,
            operator="lt",
        )

    @classmethod
    def match_operator_lte(cls, *, context: dict[str, Any], payload: Any) -> bool:
        return cls.match_compare_operator(
            context=context,
            payload=payload,
            operator="lte",
        )

    @classmethod
    def match_compare_operator(cls, *, context: dict[str, Any], payload: Any, operator: str) -> bool:
        if not isinstance(payload, dict):
            return False

        for key, expected_value in payload.items():
            actual_value = context.get(str(key))

            if not cls.compare_values(
                    actual_value=actual_value,
                    expected_value=expected_value,
                    operator=operator,
            ):
                return False

        return True

    @staticmethod
    def compare_values(*, actual_value: Any, expected_value: Any, operator: str) -> bool:
        left_number = PolicyEngineService.coerce_number(actual_value)
        right_number = PolicyEngineService.coerce_number(expected_value)

        if left_number is not None and right_number is not None:
            return PolicyEngineService.apply_compare(
                left=left_number,
                right=right_number,
                operator=operator,
            )

        left_dt = PolicyEngineService.coerce_datetime(actual_value)
        right_dt = PolicyEngineService.coerce_datetime(expected_value)

        if left_dt is not None and right_dt is not None:
            return PolicyEngineService.apply_compare(
                left=left_dt,
                right=right_dt,
                operator=operator,
            )

        if isinstance(actual_value, str) and isinstance(expected_value, str):
            return PolicyEngineService.apply_compare(
                left=actual_value,
                right=expected_value,
                operator=operator,
            )

        return False

    @staticmethod
    def apply_compare(*, left: Any, right: Any, operator: str) -> bool:
        if operator == "gt":
            return left > right

        if operator == "gte":
            return left >= right

        if operator == "lt":
            return left < right

        if operator == "lte":
            return left <= right

        return False

    @staticmethod
    def coerce_number(value: Any) -> float | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None

            try:
                return float(text)
            except ValueError:
                return None

        return None

    @staticmethod
    def coerce_datetime(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None

            try:
                return datetime.fromisoformat(text)
            except ValueError:
                return None

        return None

    @staticmethod
    def match_operator_contains(*, context: dict[str, Any], payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        for key, expected_value in payload.items():
            actual_value = context.get(str(key))

            if isinstance(actual_value, str):
                if not isinstance(expected_value, str):
                    return False

                if expected_value not in actual_value:
                    return False

                continue

            if isinstance(actual_value, dict):
                if not isinstance(expected_value, dict):
                    return False

                for expected_key, expected_item in expected_value.items():
                    if actual_value.get(expected_key) != expected_item:
                        return False

                continue

            if isinstance(actual_value, (list, tuple, set)):
                if isinstance(expected_value, (list, tuple, set)):
                    if not all(item in actual_value for item in expected_value):
                        return False

                    continue

                if expected_value not in actual_value:
                    return False

                continue

            return False

        return True

    @staticmethod
    def match_operator_time_range(*, context: dict[str, Any], payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        for key, range_value in payload.items():
            actual_time = PolicyEngineService.coerce_time(context.get(str(key)))
            if actual_time is None:
                return False

            start_value = None
            end_value = None

            if isinstance(range_value, dict):
                start_value = range_value.get("start")
                end_value = range_value.get("end")
            elif isinstance(range_value, (list, tuple)) and len(range_value) == 2:
                start_value, end_value = range_value
            else:
                return False

            start_time = PolicyEngineService.coerce_time(start_value)
            end_time = PolicyEngineService.coerce_time(end_value)

            if start_time is None or end_time is None:
                return False

            # Support overnight ranges, e.g. 22:00-02:00.
            if start_time <= end_time:
                if not (start_time <= actual_time <= end_time):
                    return False
            else:
                if not (actual_time >= start_time or actual_time <= end_time):
                    return False

        return True

    @staticmethod
    def coerce_time(value: Any) -> time | None:
        if isinstance(value, datetime):
            return value.time()

        if isinstance(value, time):
            return value

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None

            try:
                return datetime.fromisoformat(text).time()
            except ValueError:
                pass

            for fmt in (
                    "%H:%M:%S",
                    "%H:%M",
            ):
                try:
                    return datetime.strptime(text, fmt).time()
                except ValueError:
                    continue

        return None

    @staticmethod
    def match_operator_ip_range(*, context: dict[str, Any], payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        for key, expected_range in payload.items():
            actual_value = context.get(str(key))

            try:
                actual_ip = ipaddress.ip_address(str(actual_value).strip())
            except ValueError:
                return False

            ranges = expected_range if isinstance(expected_range, (list, tuple, set)) else [
                expected_range
            ]

            if not ranges:
                return False

            matched = False

            for item in ranges:
                try:
                    if isinstance(item, dict):
                        start_ip = ipaddress.ip_address(str(item.get("start") or "").strip())
                        end_ip = ipaddress.ip_address(str(item.get("end") or "").strip())

                        if int(start_ip) <= int(actual_ip) <= int(end_ip):
                            matched = True
                            break

                        continue

                    candidate = str(item or "").strip()
                    if not candidate:
                        continue

                    if "/" in candidate:
                        if actual_ip in ipaddress.ip_network(candidate, strict=False):
                            matched = True
                            break
                    else:
                        if actual_ip == ipaddress.ip_address(candidate):
                            matched = True
                            break

                except ValueError:
                    continue

            if not matched:
                return False

        return True

    @classmethod
    def sort_rules(cls, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def sort_key(item: dict[str, Any]) -> tuple[int, int, int, int]:
            rule_priority = int(item.get("priority") or 0)
            policy_priority = int(item.get("policy__priority") or 0)
            effect = str(item.get("effect") or "").strip().upper()
            effect_weight = 0 if effect == cls.EFFECT_DENY else 1

            return (
                -rule_priority,
                -policy_priority,
                effect_weight,
                int(item.get("id") or 0),
            )

        return sorted(
            rules,
            key=sort_key,
        )
