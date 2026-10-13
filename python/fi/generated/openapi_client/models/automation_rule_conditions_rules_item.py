from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AutomationRuleConditionsRulesItem")


@_attrs_define
class AutomationRuleConditionsRulesItem:
    """
    Attributes:
        field (str):
        op (str | Unset):  Default: 'eq'.
        value (Any | Unset): Rule comparison value. Can be a scalar, list, object, boolean, or null depending on the
            operator.
    """

    field: str
    op: str | Unset = "eq"
    value: Any | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        field = self.field

        op = self.op

        value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "field": field,
            }
        )
        if op is not UNSET:
            field_dict["op"] = op
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        field = d.pop("field")

        op = d.pop("op", UNSET)

        value = d.pop("value", UNSET)

        automation_rule_conditions_rules_item = cls(
            field=field,
            op=op,
            value=value,
        )

        return automation_rule_conditions_rules_item
