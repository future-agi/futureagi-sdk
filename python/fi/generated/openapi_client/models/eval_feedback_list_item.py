from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EvalFeedbackListItem")


@_attrs_define
class EvalFeedbackListItem:
    """
    Attributes:
        id (UUID):
        value (str):
        explanation (str):
        source (str):
        source_id (str):
        action_type (str):
        user_name (str):
        created_at (str):
    """

    id: UUID
    value: str
    explanation: str
    source: str
    source_id: str
    action_type: str
    user_name: str
    created_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        value = self.value

        explanation = self.explanation

        source = self.source

        source_id = self.source_id

        action_type = self.action_type

        user_name = self.user_name

        created_at = self.created_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "value": value,
                "explanation": explanation,
                "source": source,
                "source_id": source_id,
                "action_type": action_type,
                "user_name": user_name,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        value = d.pop("value")

        explanation = d.pop("explanation")

        source = d.pop("source")

        source_id = d.pop("source_id")

        action_type = d.pop("action_type")

        user_name = d.pop("user_name")

        created_at = d.pop("created_at")

        eval_feedback_list_item = cls(
            id=id,
            value=value,
            explanation=explanation,
            source=source,
            source_id=source_id,
            action_type=action_type,
            user_name=user_name,
            created_at=created_at,
        )

        eval_feedback_list_item.additional_properties = d
        return eval_feedback_list_item

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
