from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset_version_read import DatasetVersionRead


T = TypeVar("T", bound="DatasetVersionListResult")


@_attrs_define
class DatasetVersionListResult:
    """
    Attributes:
        dataset_id (UUID):
        versions (list[DatasetVersionRead]):
        limit (int):
        offset (int):
        has_more (bool):
    """

    dataset_id: UUID
    versions: list[DatasetVersionRead]
    limit: int
    offset: int
    has_more: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = str(self.dataset_id)

        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()
            versions.append(versions_item)

        limit = self.limit

        offset = self.offset

        has_more = self.has_more

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
                "versions": versions,
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_version_read import DatasetVersionRead

        d = dict(src_dict)
        dataset_id = UUID(d.pop("dataset_id"))

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = DatasetVersionRead.from_dict(versions_item_data)

            versions.append(versions_item)

        limit = d.pop("limit")

        offset = d.pop("offset")

        has_more = d.pop("has_more")

        dataset_version_list_result = cls(
            dataset_id=dataset_id,
            versions=versions,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )

        dataset_version_list_result.additional_properties = d
        return dataset_version_list_result

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
