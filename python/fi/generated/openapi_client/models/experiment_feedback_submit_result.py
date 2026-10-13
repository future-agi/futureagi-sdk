from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExperimentFeedbackSubmitResult")


@_attrs_define
class ExperimentFeedbackSubmitResult:
    """
    Attributes:
        message (str):
        action_type (str):
        user_eval_metric_id (UUID):
        workflow_id (str | Unset):
    """

    message: str
    action_type: str
    user_eval_metric_id: UUID
    workflow_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        action_type = self.action_type

        user_eval_metric_id = str(self.user_eval_metric_id)

        workflow_id = self.workflow_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "action_type": action_type,
                "user_eval_metric_id": user_eval_metric_id,
            }
        )
        if workflow_id is not UNSET:
            field_dict["workflow_id"] = workflow_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        action_type = d.pop("action_type")

        user_eval_metric_id = UUID(d.pop("user_eval_metric_id"))

        workflow_id = d.pop("workflow_id", UNSET)

        experiment_feedback_submit_result = cls(
            message=message,
            action_type=action_type,
            user_eval_metric_id=user_eval_metric_id,
            workflow_id=workflow_id,
        )

        experiment_feedback_submit_result.additional_properties = d
        return experiment_feedback_submit_result

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
