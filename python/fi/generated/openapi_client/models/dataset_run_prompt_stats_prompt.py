from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DatasetRunPromptStatsPrompt")


@_attrs_define
class DatasetRunPromptStatsPrompt:
    """
    Attributes:
        id (UUID):
        name (str):
        input_token (float):
        output_token (float):
        total_token (float):
    """

    id: UUID
    name: str
    input_token: float
    output_token: float
    total_token: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        input_token = self.input_token

        output_token = self.output_token

        total_token = self.total_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "input_token": input_token,
                "output_token": output_token,
                "total_token": total_token,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        input_token = d.pop("input_token")

        output_token = d.pop("output_token")

        total_token = d.pop("total_token")

        dataset_run_prompt_stats_prompt = cls(
            id=id,
            name=name,
            input_token=input_token,
            output_token=output_token,
            total_token=total_token,
        )

        dataset_run_prompt_stats_prompt.additional_properties = d
        return dataset_run_prompt_stats_prompt

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
