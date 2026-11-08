from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.add_as_new_dataset_request_columns import (
        AddAsNewDatasetRequestColumns,
    )


T = TypeVar("T", bound="AddAsNewDatasetRequest")


@_attrs_define
class AddAsNewDatasetRequest:
    """
    Attributes:
        dataset_id (UUID):
        name (str | Unset):
        columns (AddAsNewDatasetRequestColumns | Unset):
    """

    dataset_id: UUID
    name: str | Unset = UNSET
    columns: AddAsNewDatasetRequestColumns | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = str(self.dataset_id)

        name = self.name

        columns: dict[str, Any] | Unset = UNSET
        if not isinstance(self.columns, Unset):
            columns = self.columns.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if columns is not UNSET:
            field_dict["columns"] = columns

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.add_as_new_dataset_request_columns import (
            AddAsNewDatasetRequestColumns,
        )

        d = dict(src_dict)
        dataset_id = UUID(d.pop("dataset_id"))

        name = d.pop("name", UNSET)

        _columns = d.pop("columns", UNSET)
        columns: AddAsNewDatasetRequestColumns | Unset
        if isinstance(_columns, Unset):
            columns = UNSET
        else:
            columns = AddAsNewDatasetRequestColumns.from_dict(_columns)

        add_as_new_dataset_request = cls(
            dataset_id=dataset_id,
            name=name,
            columns=columns,
        )

        add_as_new_dataset_request.additional_properties = d
        return add_as_new_dataset_request

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
