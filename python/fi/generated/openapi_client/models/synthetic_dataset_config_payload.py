from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.synthetic_dataset_config_payload_columns_item import (
        SyntheticDatasetConfigPayloadColumnsItem,
    )
    from ..models.synthetic_dataset_config_payload_dataset import (
        SyntheticDatasetConfigPayloadDataset,
    )


T = TypeVar("T", bound="SyntheticDatasetConfigPayload")


@_attrs_define
class SyntheticDatasetConfigPayload:
    """
    Attributes:
        num_rows (int | Unset):
        columns (list[SyntheticDatasetConfigPayloadColumnsItem] | Unset):
        dataset (SyntheticDatasetConfigPayloadDataset | Unset):
        kb_id (None | Unset | UUID):
    """

    num_rows: int | Unset = UNSET
    columns: list[SyntheticDatasetConfigPayloadColumnsItem] | Unset = UNSET
    dataset: SyntheticDatasetConfigPayloadDataset | Unset = UNSET
    kb_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        num_rows = self.num_rows

        columns: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.columns, Unset):
            columns = []
            for columns_item_data in self.columns:
                columns_item = columns_item_data.to_dict()
                columns.append(columns_item)

        dataset: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dataset, Unset):
            dataset = self.dataset.to_dict()

        kb_id: None | str | Unset
        if isinstance(self.kb_id, Unset):
            kb_id = UNSET
        elif isinstance(self.kb_id, UUID):
            kb_id = str(self.kb_id)
        else:
            kb_id = self.kb_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if num_rows is not UNSET:
            field_dict["num_rows"] = num_rows
        if columns is not UNSET:
            field_dict["columns"] = columns
        if dataset is not UNSET:
            field_dict["dataset"] = dataset
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.synthetic_dataset_config_payload_columns_item import (
            SyntheticDatasetConfigPayloadColumnsItem,
        )
        from ..models.synthetic_dataset_config_payload_dataset import (
            SyntheticDatasetConfigPayloadDataset,
        )

        d = dict(src_dict)
        num_rows = d.pop("num_rows", UNSET)

        _columns = d.pop("columns", UNSET)
        columns: list[SyntheticDatasetConfigPayloadColumnsItem] | Unset = UNSET
        if _columns is not UNSET:
            columns = []
            for columns_item_data in _columns:
                columns_item = SyntheticDatasetConfigPayloadColumnsItem.from_dict(
                    columns_item_data
                )

                columns.append(columns_item)

        _dataset = d.pop("dataset", UNSET)
        dataset: SyntheticDatasetConfigPayloadDataset | Unset
        if isinstance(_dataset, Unset):
            dataset = UNSET
        else:
            dataset = SyntheticDatasetConfigPayloadDataset.from_dict(_dataset)

        def _parse_kb_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                kb_id_type_0 = UUID(data)

                return kb_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        kb_id = _parse_kb_id(d.pop("kb_id", UNSET))

        synthetic_dataset_config_payload = cls(
            num_rows=num_rows,
            columns=columns,
            dataset=dataset,
            kb_id=kb_id,
        )

        synthetic_dataset_config_payload.additional_properties = d
        return synthetic_dataset_config_payload

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
