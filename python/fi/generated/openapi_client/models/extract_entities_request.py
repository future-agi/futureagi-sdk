from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExtractEntitiesRequest")


@_attrs_define
class ExtractEntitiesRequest:
    """
    Attributes:
        column_id (UUID):
        instruction (str):
        language_model_id (str | Unset):  Default: 'gpt-4'.
        concurrency (int | Unset):  Default: 5.
        new_column_name (str | Unset):
    """

    column_id: UUID
    instruction: str
    language_model_id: str | Unset = "gpt-4"
    concurrency: int | Unset = 5
    new_column_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_id = str(self.column_id)

        instruction = self.instruction

        language_model_id = self.language_model_id

        concurrency = self.concurrency

        new_column_name = self.new_column_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_id": column_id,
                "instruction": instruction,
            }
        )
        if language_model_id is not UNSET:
            field_dict["language_model_id"] = language_model_id
        if concurrency is not UNSET:
            field_dict["concurrency"] = concurrency
        if new_column_name is not UNSET:
            field_dict["new_column_name"] = new_column_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        column_id = UUID(d.pop("column_id"))

        instruction = d.pop("instruction")

        language_model_id = d.pop("language_model_id", UNSET)

        concurrency = d.pop("concurrency", UNSET)

        new_column_name = d.pop("new_column_name", UNSET)

        extract_entities_request = cls(
            column_id=column_id,
            instruction=instruction,
            language_model_id=language_model_id,
            concurrency=concurrency,
            new_column_name=new_column_name,
        )

        extract_entities_request.additional_properties = d
        return extract_entities_request

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
