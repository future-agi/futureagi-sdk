from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.dataset_row_data_request_sort_item_type import (
    DatasetRowDataRequestSortItemType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetRowDataRequestSortItem")


@_attrs_define
class DatasetRowDataRequestSortItem:
    """
    Attributes:
        column_id (str):
        type_ (DatasetRowDataRequestSortItemType | Unset):
    """

    column_id: str
    type_: DatasetRowDataRequestSortItemType | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        column_id = self.column_id

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "column_id": column_id,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        column_id = d.pop("column_id")

        _type_ = d.pop("type", UNSET)
        type_: DatasetRowDataRequestSortItemType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = DatasetRowDataRequestSortItemType(_type_)

        dataset_row_data_request_sort_item = cls(
            column_id=column_id,
            type_=type_,
        )

        return dataset_row_data_request_sort_item
