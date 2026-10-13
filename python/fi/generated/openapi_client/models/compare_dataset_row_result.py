from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.compare_dataset_row_result_table_item import (
        CompareDatasetRowResultTableItem,
    )


T = TypeVar("T", bound="CompareDatasetRowResult")


@_attrs_define
class CompareDatasetRowResult:
    """
    Attributes:
        table (list[CompareDatasetRowResultTableItem]):
        prev_row_id (None | Unset | UUID):
        next_row_id (None | Unset | UUID):
    """

    table: list[CompareDatasetRowResultTableItem]
    prev_row_id: None | Unset | UUID = UNSET
    next_row_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        table = []
        for table_item_data in self.table:
            table_item = table_item_data.to_dict()
            table.append(table_item)

        prev_row_id: None | str | Unset
        if isinstance(self.prev_row_id, Unset):
            prev_row_id = UNSET
        elif isinstance(self.prev_row_id, UUID):
            prev_row_id = str(self.prev_row_id)
        else:
            prev_row_id = self.prev_row_id

        next_row_id: None | str | Unset
        if isinstance(self.next_row_id, Unset):
            next_row_id = UNSET
        elif isinstance(self.next_row_id, UUID):
            next_row_id = str(self.next_row_id)
        else:
            next_row_id = self.next_row_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "table": table,
            }
        )
        if prev_row_id is not UNSET:
            field_dict["prev_row_id"] = prev_row_id
        if next_row_id is not UNSET:
            field_dict["next_row_id"] = next_row_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.compare_dataset_row_result_table_item import (
            CompareDatasetRowResultTableItem,
        )

        d = dict(src_dict)
        table = []
        _table = d.pop("table")
        for table_item_data in _table:
            table_item = CompareDatasetRowResultTableItem.from_dict(table_item_data)

            table.append(table_item)

        def _parse_prev_row_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prev_row_id_type_0 = UUID(data)

                return prev_row_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prev_row_id = _parse_prev_row_id(d.pop("prev_row_id", UNSET))

        def _parse_next_row_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                next_row_id_type_0 = UUID(data)

                return next_row_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        next_row_id = _parse_next_row_id(d.pop("next_row_id", UNSET))

        compare_dataset_row_result = cls(
            table=table,
            prev_row_id=prev_row_id,
            next_row_id=next_row_id,
        )

        compare_dataset_row_result.additional_properties = d
        return compare_dataset_row_result

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
