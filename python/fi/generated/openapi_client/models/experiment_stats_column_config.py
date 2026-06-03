from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExperimentStatsColumnConfig")


@_attrs_define
class ExperimentStatsColumnConfig:
    """
    Attributes:
        name (str):
        status (str | Unset):
        reverse_output (bool | Unset):
        output_type (None | str | Unset):
        eval_template_id (None | str | Unset):
    """

    name: str
    status: str | Unset = UNSET
    reverse_output: bool | Unset = UNSET
    output_type: None | str | Unset = UNSET
    eval_template_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        status = self.status

        reverse_output = self.reverse_output

        output_type: None | str | Unset
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        eval_template_id: None | str | Unset
        if isinstance(self.eval_template_id, Unset):
            eval_template_id = UNSET
        else:
            eval_template_id = self.eval_template_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status
        if reverse_output is not UNSET:
            field_dict["reverse_output"] = reverse_output
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if eval_template_id is not UNSET:
            field_dict["eval_template_id"] = eval_template_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        status = d.pop("status", UNSET)

        reverse_output = d.pop("reverse_output", UNSET)

        def _parse_output_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_eval_template_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_template_id = _parse_eval_template_id(d.pop("eval_template_id", UNSET))

        experiment_stats_column_config = cls(
            name=name,
            status=status,
            reverse_output=reverse_output,
            output_type=output_type,
            eval_template_id=eval_template_id,
        )

        experiment_stats_column_config.additional_properties = d
        return experiment_stats_column_config

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
