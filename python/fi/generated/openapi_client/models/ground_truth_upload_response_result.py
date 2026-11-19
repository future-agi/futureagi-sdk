from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GroundTruthUploadResponseResult")


@_attrs_define
class GroundTruthUploadResponseResult:
    """
    Attributes:
        id (UUID):
        name (str):
        row_count (int):
        columns (list[str]):
        embedding_status (str):
    """

    id: UUID
    name: str
    row_count: int
    columns: list[str]
    embedding_status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        row_count = self.row_count

        columns = self.columns

        embedding_status = self.embedding_status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "row_count": row_count,
                "columns": columns,
                "embedding_status": embedding_status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        row_count = d.pop("row_count")

        columns = cast(list[str], d.pop("columns"))

        embedding_status = d.pop("embedding_status")

        ground_truth_upload_response_result = cls(
            id=id,
            name=name,
            row_count=row_count,
            columns=columns,
            embedding_status=embedding_status,
        )

        ground_truth_upload_response_result.additional_properties = d
        return ground_truth_upload_response_result

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
