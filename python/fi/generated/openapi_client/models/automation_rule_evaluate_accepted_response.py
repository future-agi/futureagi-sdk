from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AutomationRuleEvaluateAcceptedResponse")


@_attrs_define
class AutomationRuleEvaluateAcceptedResponse:
    """
    Attributes:
        status (str):
        workflow_id (str):
        message (str):
    """

    status: str
    workflow_id: str
    message: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        workflow_id = self.workflow_id

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "workflow_id": workflow_id,
                "message": message,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status")

        workflow_id = d.pop("workflow_id")

        message = d.pop("message")

        automation_rule_evaluate_accepted_response = cls(
            status=status,
            workflow_id=workflow_id,
            message=message,
        )

        automation_rule_evaluate_accepted_response.additional_properties = d
        return automation_rule_evaluate_accepted_response

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
