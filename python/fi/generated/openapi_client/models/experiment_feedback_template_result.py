from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExperimentFeedbackTemplateResult")


@_attrs_define
class ExperimentFeedbackTemplateResult:
    """
    Attributes:
        eval_name (str):
        user_eval_name (str):
        output_type (None | str | Unset):
        eval_description (None | str | Unset):
        choices (list[str] | Unset):
        multi_choice (bool | Unset):
    """

    eval_name: str
    user_eval_name: str
    output_type: None | str | Unset = UNSET
    eval_description: None | str | Unset = UNSET
    choices: list[str] | Unset = UNSET
    multi_choice: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_name = self.eval_name

        user_eval_name = self.user_eval_name

        output_type: None | str | Unset
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        eval_description: None | str | Unset
        if isinstance(self.eval_description, Unset):
            eval_description = UNSET
        else:
            eval_description = self.eval_description

        choices: list[str] | Unset = UNSET
        if not isinstance(self.choices, Unset):
            choices = self.choices

        multi_choice = self.multi_choice

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval_name": eval_name,
                "user_eval_name": user_eval_name,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if eval_description is not UNSET:
            field_dict["eval_description"] = eval_description
        if choices is not UNSET:
            field_dict["choices"] = choices
        if multi_choice is not UNSET:
            field_dict["multi_choice"] = multi_choice

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        eval_name = d.pop("eval_name")

        user_eval_name = d.pop("user_eval_name")

        def _parse_output_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_eval_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_description = _parse_eval_description(d.pop("eval_description", UNSET))

        choices = cast(list[str], d.pop("choices", UNSET))

        multi_choice = d.pop("multi_choice", UNSET)

        experiment_feedback_template_result = cls(
            eval_name=eval_name,
            user_eval_name=user_eval_name,
            output_type=output_type,
            eval_description=eval_description,
            choices=choices,
            multi_choice=multi_choice,
        )

        experiment_feedback_template_result.additional_properties = d
        return experiment_feedback_template_result

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
