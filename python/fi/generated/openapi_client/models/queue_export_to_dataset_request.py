from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_export_column_mapping import QueueExportColumnMapping


T = TypeVar("T", bound="QueueExportToDatasetRequest")


@_attrs_define
class QueueExportToDatasetRequest:
    """
    Attributes:
        dataset_id (UUID | Unset):
        dataset_name (str | Unset):
        status_filter (str | Unset):  Default: 'completed'.
        column_mapping (list[QueueExportColumnMapping] | Unset):
    """

    dataset_id: UUID | Unset = UNSET
    dataset_name: str | Unset = UNSET
    status_filter: str | Unset = "completed"
    column_mapping: list[QueueExportColumnMapping] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id: str | Unset = UNSET
        if not isinstance(self.dataset_id, Unset):
            dataset_id = str(self.dataset_id)

        dataset_name = self.dataset_name

        status_filter = self.status_filter

        column_mapping: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.column_mapping, Unset):
            column_mapping = []
            for column_mapping_item_data in self.column_mapping:
                column_mapping_item = column_mapping_item_data.to_dict()
                column_mapping.append(column_mapping_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if dataset_id is not UNSET:
            field_dict["dataset_id"] = dataset_id
        if dataset_name is not UNSET:
            field_dict["dataset_name"] = dataset_name
        if status_filter is not UNSET:
            field_dict["status_filter"] = status_filter
        if column_mapping is not UNSET:
            field_dict["column_mapping"] = column_mapping

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_export_column_mapping import QueueExportColumnMapping

        d = dict(src_dict)
        _dataset_id = d.pop("dataset_id", UNSET)
        dataset_id: UUID | Unset
        if isinstance(_dataset_id, Unset):
            dataset_id = UNSET
        else:
            dataset_id = UUID(_dataset_id)

        dataset_name = d.pop("dataset_name", UNSET)

        status_filter = d.pop("status_filter", UNSET)

        _column_mapping = d.pop("column_mapping", UNSET)
        column_mapping: list[QueueExportColumnMapping] | Unset = UNSET
        if _column_mapping is not UNSET:
            column_mapping = []
            for column_mapping_item_data in _column_mapping:
                column_mapping_item = QueueExportColumnMapping.from_dict(
                    column_mapping_item_data
                )

                column_mapping.append(column_mapping_item)

        queue_export_to_dataset_request = cls(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            status_filter=status_filter,
            column_mapping=column_mapping,
        )

        queue_export_to_dataset_request.additional_properties = d
        return queue_export_to_dataset_request

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
