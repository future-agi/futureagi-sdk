from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_usage_feedback_value import EvalUsageFeedbackValue


T = TypeVar("T", bound="EvalUsageFeedback")


@_attrs_define
class EvalUsageFeedback:
    """
    Attributes:
        id (UUID):
        value (EvalUsageFeedbackValue | Unset):
        explanation (str | Unset):
        action_type (str | Unset):
        created_at (str | Unset):
        user (str | Unset):
    """

    id: UUID
    value: EvalUsageFeedbackValue | Unset = UNSET
    explanation: str | Unset = UNSET
    action_type: str | Unset = UNSET
    created_at: str | Unset = UNSET
    user: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.value, Unset):
            value = self.value.to_dict()

        explanation = self.explanation

        action_type = self.action_type

        created_at = self.created_at

        user = self.user

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value
        if explanation is not UNSET:
            field_dict["explanation"] = explanation
        if action_type is not UNSET:
            field_dict["action_type"] = action_type
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if user is not UNSET:
            field_dict["user"] = user

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_usage_feedback_value import EvalUsageFeedbackValue

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        _value = d.pop("value", UNSET)
        value: EvalUsageFeedbackValue | Unset
        if isinstance(_value, Unset):
            value = UNSET
        else:
            value = EvalUsageFeedbackValue.from_dict(_value)

        explanation = d.pop("explanation", UNSET)

        action_type = d.pop("action_type", UNSET)

        created_at = d.pop("created_at", UNSET)

        user = d.pop("user", UNSET)

        eval_usage_feedback = cls(
            id=id,
            value=value,
            explanation=explanation,
            action_type=action_type,
            created_at=created_at,
            user=user,
        )

        eval_usage_feedback.additional_properties = d
        return eval_usage_feedback

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
