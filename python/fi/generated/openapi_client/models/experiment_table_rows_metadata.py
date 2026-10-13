from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_table_rows_metadata_description import (
        ExperimentTableRowsMetadataDescription,
    )


T = TypeVar("T", bound="ExperimentTableRowsMetadata")


@_attrs_define
class ExperimentTableRowsMetadata:
    """
    Attributes:
        total_rows (int | Unset):
        dataset (str | Unset):
        dataset_name (str | Unset):
        column (None | str | Unset):
        total_pages (int | Unset):
        description (ExperimentTableRowsMetadataDescription | Unset):
    """

    total_rows: int | Unset = UNSET
    dataset: str | Unset = UNSET
    dataset_name: str | Unset = UNSET
    column: None | str | Unset = UNSET
    total_pages: int | Unset = UNSET
    description: ExperimentTableRowsMetadataDescription | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_rows = self.total_rows

        dataset = self.dataset

        dataset_name = self.dataset_name

        column: None | str | Unset
        if isinstance(self.column, Unset):
            column = UNSET
        else:
            column = self.column

        total_pages = self.total_pages

        description: dict[str, Any] | Unset = UNSET
        if not isinstance(self.description, Unset):
            description = self.description.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if total_rows is not UNSET:
            field_dict["total_rows"] = total_rows
        if dataset is not UNSET:
            field_dict["dataset"] = dataset
        if dataset_name is not UNSET:
            field_dict["dataset_name"] = dataset_name
        if column is not UNSET:
            field_dict["column"] = column
        if total_pages is not UNSET:
            field_dict["total_pages"] = total_pages
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_table_rows_metadata_description import (
            ExperimentTableRowsMetadataDescription,
        )

        d = dict(src_dict)
        total_rows = d.pop("total_rows", UNSET)

        dataset = d.pop("dataset", UNSET)

        dataset_name = d.pop("dataset_name", UNSET)

        def _parse_column(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        column = _parse_column(d.pop("column", UNSET))

        total_pages = d.pop("total_pages", UNSET)

        _description = d.pop("description", UNSET)
        description: ExperimentTableRowsMetadataDescription | Unset
        if isinstance(_description, Unset):
            description = UNSET
        else:
            description = ExperimentTableRowsMetadataDescription.from_dict(_description)

        experiment_table_rows_metadata = cls(
            total_rows=total_rows,
            dataset=dataset,
            dataset_name=dataset_name,
            column=column,
            total_pages=total_pages,
            description=description,
        )

        experiment_table_rows_metadata.additional_properties = d
        return experiment_table_rows_metadata

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
