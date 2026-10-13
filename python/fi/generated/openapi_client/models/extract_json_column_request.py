from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExtractJsonColumnRequest")


@_attrs_define
class ExtractJsonColumnRequest:
    """
    Attributes:
        column_id (UUID):
        json_key (str):
        new_column_name (str | Unset):
        concurrency (int | Unset):  Default: 5.
    """

    column_id: UUID
    json_key: str
    new_column_name: str | Unset = UNSET
    concurrency: int | Unset = 5
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_id = str(self.column_id)

        json_key = self.json_key

        new_column_name = self.new_column_name

        concurrency = self.concurrency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_id": column_id,
                "json_key": json_key,
            }
        )
        if new_column_name is not UNSET:
            field_dict["new_column_name"] = new_column_name
        if concurrency is not UNSET:
            field_dict["concurrency"] = concurrency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        column_id = UUID(d.pop("column_id"))

        json_key = d.pop("json_key")

        new_column_name = d.pop("new_column_name", UNSET)

        concurrency = d.pop("concurrency", UNSET)

        extract_json_column_request = cls(
            column_id=column_id,
            json_key=json_key,
            new_column_name=new_column_name,
            concurrency=concurrency,
        )

        extract_json_column_request.additional_properties = d
        return extract_json_column_request

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
