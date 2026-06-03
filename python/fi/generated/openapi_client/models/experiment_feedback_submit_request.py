from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.experiment_feedback_submit_request_action_type import (
    ExperimentFeedbackSubmitRequestActionType,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_feedback_submit_request_value import (
        ExperimentFeedbackSubmitRequestValue,
    )


T = TypeVar("T", bound="ExperimentFeedbackSubmitRequest")


@_attrs_define
class ExperimentFeedbackSubmitRequest:
    """
    Attributes:
        action_type (ExperimentFeedbackSubmitRequestActionType):
        feedback_id (UUID):
        user_eval_metric_id (UUID):
        value (ExperimentFeedbackSubmitRequestValue | Unset):
        explanation (str | Unset):
    """

    action_type: ExperimentFeedbackSubmitRequestActionType
    feedback_id: UUID
    user_eval_metric_id: UUID
    value: ExperimentFeedbackSubmitRequestValue | Unset = UNSET
    explanation: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        action_type = self.action_type.value

        feedback_id = str(self.feedback_id)

        user_eval_metric_id = str(self.user_eval_metric_id)

        value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.value, Unset):
            value = self.value.to_dict()

        explanation = self.explanation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action_type": action_type,
                "feedback_id": feedback_id,
                "user_eval_metric_id": user_eval_metric_id,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value
        if explanation is not UNSET:
            field_dict["explanation"] = explanation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_feedback_submit_request_value import (
            ExperimentFeedbackSubmitRequestValue,
        )

        d = dict(src_dict)
        action_type = ExperimentFeedbackSubmitRequestActionType(d.pop("action_type"))

        feedback_id = UUID(d.pop("feedback_id"))

        user_eval_metric_id = UUID(d.pop("user_eval_metric_id"))

        _value = d.pop("value", UNSET)
        value: ExperimentFeedbackSubmitRequestValue | Unset
        if isinstance(_value, Unset):
            value = UNSET
        else:
            value = ExperimentFeedbackSubmitRequestValue.from_dict(_value)

        explanation = d.pop("explanation", UNSET)

        experiment_feedback_submit_request = cls(
            action_type=action_type,
            feedback_id=feedback_id,
            user_eval_metric_id=user_eval_metric_id,
            value=value,
            explanation=explanation,
        )

        experiment_feedback_submit_request.additional_properties = d
        return experiment_feedback_submit_request

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
