from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.automation_rule_conditions_operator import (
    AutomationRuleConditionsOperator,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.automation_rule_conditions_filter_item import (
        AutomationRuleConditionsFilterItem,
    )
    from ..models.automation_rule_conditions_rules_item import (
        AutomationRuleConditionsRulesItem,
    )
    from ..models.automation_rule_scope import AutomationRuleScope


T = TypeVar("T", bound="AutomationRuleConditions")


@_attrs_define
class AutomationRuleConditions:
    """
    Attributes:
        operator (AutomationRuleConditionsOperator | Unset):  Default: AutomationRuleConditionsOperator.AND.
        filter_ (list[AutomationRuleConditionsFilterItem] | Unset):
        scope (AutomationRuleScope | Unset):
        rules (list[AutomationRuleConditionsRulesItem] | Unset):
    """

    operator: AutomationRuleConditionsOperator | Unset = (
        AutomationRuleConditionsOperator.AND
    )
    filter_: list[AutomationRuleConditionsFilterItem] | Unset = UNSET
    scope: AutomationRuleScope | Unset = UNSET
    rules: list[AutomationRuleConditionsRulesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        operator: str | Unset = UNSET
        if not isinstance(self.operator, Unset):
            operator = self.operator.value

        filter_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.filter_, Unset):
            filter_ = []
            for filter_item_data in self.filter_:
                filter_item = filter_item_data.to_dict()
                filter_.append(filter_item)

        scope: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scope, Unset):
            scope = self.scope.to_dict()

        rules: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.rules, Unset):
            rules = []
            for rules_item_data in self.rules:
                rules_item = rules_item_data.to_dict()
                rules.append(rules_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if operator is not UNSET:
            field_dict["operator"] = operator
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if scope is not UNSET:
            field_dict["scope"] = scope
        if rules is not UNSET:
            field_dict["rules"] = rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.automation_rule_conditions_filter_item import (
            AutomationRuleConditionsFilterItem,
        )
        from ..models.automation_rule_conditions_rules_item import (
            AutomationRuleConditionsRulesItem,
        )
        from ..models.automation_rule_scope import AutomationRuleScope

        d = dict(src_dict)
        _operator = d.pop("operator", UNSET)
        operator: AutomationRuleConditionsOperator | Unset
        if isinstance(_operator, Unset):
            operator = UNSET
        else:
            operator = AutomationRuleConditionsOperator(_operator)

        _filter_ = d.pop("filter", UNSET)
        filter_: list[AutomationRuleConditionsFilterItem] | Unset = UNSET
        if _filter_ is not UNSET:
            filter_ = []
            for filter_item_data in _filter_:
                filter_item = AutomationRuleConditionsFilterItem.from_dict(
                    filter_item_data
                )

                filter_.append(filter_item)

        _scope = d.pop("scope", UNSET)
        scope: AutomationRuleScope | Unset
        if isinstance(_scope, Unset):
            scope = UNSET
        else:
            scope = AutomationRuleScope.from_dict(_scope)

        _rules = d.pop("rules", UNSET)
        rules: list[AutomationRuleConditionsRulesItem] | Unset = UNSET
        if _rules is not UNSET:
            rules = []
            for rules_item_data in _rules:
                rules_item = AutomationRuleConditionsRulesItem.from_dict(
                    rules_item_data
                )

                rules.append(rules_item)

        automation_rule_conditions = cls(
            operator=operator,
            filter_=filter_,
            scope=scope,
            rules=rules,
        )

        automation_rule_conditions.additional_properties = d
        return automation_rule_conditions

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
