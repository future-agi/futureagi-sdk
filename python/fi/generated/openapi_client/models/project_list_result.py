from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.project_list_item import ProjectListItem
    from ..models.project_list_metadata import ProjectListMetadata


T = TypeVar("T", bound="ProjectListResult")


@_attrs_define
class ProjectListResult:
    """
    Attributes:
        metadata (ProjectListMetadata):
        table (list[ProjectListItem]):
    """

    metadata: ProjectListMetadata
    table: list[ProjectListItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metadata = self.metadata.to_dict()

        table = []
        for table_item_data in self.table:
            table_item = table_item_data.to_dict()
            table.append(table_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metadata": metadata,
                "table": table,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.project_list_item import ProjectListItem
        from ..models.project_list_metadata import ProjectListMetadata

        d = dict(src_dict)
        metadata = ProjectListMetadata.from_dict(d.pop("metadata"))

        table = []
        _table = d.pop("table")
        for table_item_data in _table:
            table_item = ProjectListItem.from_dict(table_item_data)

            table.append(table_item)

        project_list_result = cls(
            metadata=metadata,
            table=table,
        )

        project_list_result.additional_properties = d
        return project_list_result

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
