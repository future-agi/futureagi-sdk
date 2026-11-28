from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.feedback_source import FeedbackSource
from ..types import UNSET, Unset

T = TypeVar("T", bound="Feedback")


@_attrs_define
class Feedback:
    """
    Attributes:
        source_id (str):
        source (FeedbackSource):
        value (str):
        id (UUID | Unset):
        user_eval_metric (None | Unset | UUID):
        explanation (None | str | Unset):
        row_id (None | str | Unset):
        custom_eval_config_id (None | Unset | UUID):
        feedback_improvement (None | str | Unset):
        action_type (None | str | Unset):
    """

    source_id: str
    source: FeedbackSource
    value: str
    id: UUID | Unset = UNSET
    user_eval_metric: None | Unset | UUID = UNSET
    explanation: None | str | Unset = UNSET
    row_id: None | str | Unset = UNSET
    custom_eval_config_id: None | Unset | UUID = UNSET
    feedback_improvement: None | str | Unset = UNSET
    action_type: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_id = self.source_id

        source = self.source.value

        value = self.value

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        user_eval_metric: None | str | Unset
        if isinstance(self.user_eval_metric, Unset):
            user_eval_metric = UNSET
        elif isinstance(self.user_eval_metric, UUID):
            user_eval_metric = str(self.user_eval_metric)
        else:
            user_eval_metric = self.user_eval_metric

        explanation: None | str | Unset
        if isinstance(self.explanation, Unset):
            explanation = UNSET
        else:
            explanation = self.explanation

        row_id: None | str | Unset
        if isinstance(self.row_id, Unset):
            row_id = UNSET
        else:
            row_id = self.row_id

        custom_eval_config_id: None | str | Unset
        if isinstance(self.custom_eval_config_id, Unset):
            custom_eval_config_id = UNSET
        elif isinstance(self.custom_eval_config_id, UUID):
            custom_eval_config_id = str(self.custom_eval_config_id)
        else:
            custom_eval_config_id = self.custom_eval_config_id

        feedback_improvement: None | str | Unset
        if isinstance(self.feedback_improvement, Unset):
            feedback_improvement = UNSET
        else:
            feedback_improvement = self.feedback_improvement

        action_type: None | str | Unset
        if isinstance(self.action_type, Unset):
            action_type = UNSET
        else:
            action_type = self.action_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source_id": source_id,
                "source": source,
                "value": value,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if user_eval_metric is not UNSET:
            field_dict["user_eval_metric"] = user_eval_metric
        if explanation is not UNSET:
            field_dict["explanation"] = explanation
        if row_id is not UNSET:
            field_dict["row_id"] = row_id
        if custom_eval_config_id is not UNSET:
            field_dict["custom_eval_config_id"] = custom_eval_config_id
        if feedback_improvement is not UNSET:
            field_dict["feedback_improvement"] = feedback_improvement
        if action_type is not UNSET:
            field_dict["action_type"] = action_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_id = d.pop("source_id")

        source = FeedbackSource(d.pop("source"))

        value = d.pop("value")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        def _parse_user_eval_metric(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                user_eval_metric_type_0 = UUID(data)

                return user_eval_metric_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        user_eval_metric = _parse_user_eval_metric(d.pop("user_eval_metric", UNSET))

        def _parse_explanation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        explanation = _parse_explanation(d.pop("explanation", UNSET))

        def _parse_row_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        row_id = _parse_row_id(d.pop("row_id", UNSET))

        def _parse_custom_eval_config_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                custom_eval_config_id_type_0 = UUID(data)

                return custom_eval_config_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        custom_eval_config_id = _parse_custom_eval_config_id(
            d.pop("custom_eval_config_id", UNSET)
        )

        def _parse_feedback_improvement(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        feedback_improvement = _parse_feedback_improvement(
            d.pop("feedback_improvement", UNSET)
        )

        def _parse_action_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        action_type = _parse_action_type(d.pop("action_type", UNSET))

        feedback = cls(
            source_id=source_id,
            source=source,
            value=value,
            id=id,
            user_eval_metric=user_eval_metric,
            explanation=explanation,
            row_id=row_id,
            custom_eval_config_id=custom_eval_config_id,
            feedback_improvement=feedback_improvement,
            action_type=action_type,
        )

        feedback.additional_properties = d
        return feedback

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
