from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.synthetic_dataset_creation_dataset import (
        SyntheticDatasetCreationDataset,
    )


T = TypeVar("T", bound="SyntheticDatasetCreation")


@_attrs_define
class SyntheticDatasetCreation:
    """
    Attributes:
        num_rows (int):
        columns (list[None | str]):
        dataset (SyntheticDatasetCreationDataset):
        kb_id (UUID | Unset):
    """

    num_rows: int
    columns: list[None | str]
    dataset: SyntheticDatasetCreationDataset
    kb_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        num_rows = self.num_rows

        columns = []
        for columns_item_data in self.columns:
            columns_item: None | str
            columns_item = columns_item_data
            columns.append(columns_item)

        dataset = self.dataset.to_dict()

        kb_id: str | Unset = UNSET
        if not isinstance(self.kb_id, Unset):
            kb_id = str(self.kb_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "num_rows": num_rows,
                "columns": columns,
                "dataset": dataset,
            }
        )
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.synthetic_dataset_creation_dataset import (
            SyntheticDatasetCreationDataset,
        )

        d = dict(src_dict)
        num_rows = d.pop("num_rows")

        columns = []
        _columns = d.pop("columns")
        for columns_item_data in _columns:

            def _parse_columns_item(data: object) -> None | str:
                if data is None:
                    return data
                return cast(None | str, data)

            columns_item = _parse_columns_item(columns_item_data)

            columns.append(columns_item)

        dataset = SyntheticDatasetCreationDataset.from_dict(d.pop("dataset"))

        _kb_id = d.pop("kb_id", UNSET)
        kb_id: UUID | Unset
        if isinstance(_kb_id, Unset):
            kb_id = UNSET
        else:
            kb_id = UUID(_kb_id)

        synthetic_dataset_creation = cls(
            num_rows=num_rows,
            columns=columns,
            dataset=dataset,
            kb_id=kb_id,
        )

        synthetic_dataset_creation.additional_properties = d
        return synthetic_dataset_creation

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
