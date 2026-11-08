from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_feedback_detail_item_value import (
        ExperimentFeedbackDetailItemValue,
    )


T = TypeVar("T", bound="ExperimentFeedbackDetailItem")


@_attrs_define
class ExperimentFeedbackDetailItem:
    """
    Attributes:
        id (UUID):
        created_at (datetime.datetime):
        value (ExperimentFeedbackDetailItemValue | Unset):
        comment (None | str | Unset):
        action_type (None | str | Unset):
    """

    id: UUID
    created_at: datetime.datetime
    value: ExperimentFeedbackDetailItemValue | Unset = UNSET
    comment: None | str | Unset = UNSET
    action_type: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        created_at = self.created_at.isoformat()

        value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.value, Unset):
            value = self.value.to_dict()

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        action_type: None | str | Unset
        if isinstance(self.action_type, Unset):
            action_type = UNSET
        else:
            action_type = self.action_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "created_at": created_at,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value
        if comment is not UNSET:
            field_dict["comment"] = comment
        if action_type is not UNSET:
            field_dict["action_type"] = action_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_feedback_detail_item_value import (
            ExperimentFeedbackDetailItemValue,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        created_at = isoparse(d.pop("created_at"))

        _value = d.pop("value", UNSET)
        value: ExperimentFeedbackDetailItemValue | Unset
        if isinstance(_value, Unset):
            value = UNSET
        else:
            value = ExperimentFeedbackDetailItemValue.from_dict(_value)

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_action_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        action_type = _parse_action_type(d.pop("action_type", UNSET))

        experiment_feedback_detail_item = cls(
            id=id,
            created_at=created_at,
            value=value,
            comment=comment,
            action_type=action_type,
        )

        experiment_feedback_detail_item.additional_properties = d
        return experiment_feedback_detail_item

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
