from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.compare_dataset_dataset_info import CompareDatasetDatasetInfo


T = TypeVar("T", bound="CompareDataset")


@_attrs_define
class CompareDataset:
    """
    Attributes:
        base_column_name (str):
        dataset_ids (list[UUID]):
        compare_id (None | Unset | UUID):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        dataset_info (CompareDatasetDatasetInfo | Unset):
        common_column_names (list[str] | Unset):
    """

    base_column_name: str
    dataset_ids: list[UUID]
    compare_id: None | Unset | UUID = UNSET
    page_size: int | Unset = 10
    current_page_index: int | Unset = 0
    dataset_info: CompareDatasetDatasetInfo | Unset = UNSET
    common_column_names: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        base_column_name = self.base_column_name

        dataset_ids = []
        for dataset_ids_item_data in self.dataset_ids:
            dataset_ids_item = str(dataset_ids_item_data)
            dataset_ids.append(dataset_ids_item)

        compare_id: None | str | Unset
        if isinstance(self.compare_id, Unset):
            compare_id = UNSET
        elif isinstance(self.compare_id, UUID):
            compare_id = str(self.compare_id)
        else:
            compare_id = self.compare_id

        page_size = self.page_size

        current_page_index = self.current_page_index

        dataset_info: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dataset_info, Unset):
            dataset_info = self.dataset_info.to_dict()

        common_column_names: list[str] | Unset = UNSET
        if not isinstance(self.common_column_names, Unset):
            common_column_names = self.common_column_names

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "base_column_name": base_column_name,
                "dataset_ids": dataset_ids,
            }
        )
        if compare_id is not UNSET:
            field_dict["compare_id"] = compare_id
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if current_page_index is not UNSET:
            field_dict["current_page_index"] = current_page_index
        if dataset_info is not UNSET:
            field_dict["dataset_info"] = dataset_info
        if common_column_names is not UNSET:
            field_dict["common_column_names"] = common_column_names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.compare_dataset_dataset_info import CompareDatasetDatasetInfo

        d = dict(src_dict)
        base_column_name = d.pop("base_column_name")

        dataset_ids = []
        _dataset_ids = d.pop("dataset_ids")
        for dataset_ids_item_data in _dataset_ids:
            dataset_ids_item = UUID(dataset_ids_item_data)

            dataset_ids.append(dataset_ids_item)

        def _parse_compare_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                compare_id_type_0 = UUID(data)

                return compare_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        compare_id = _parse_compare_id(d.pop("compare_id", UNSET))

        page_size = d.pop("page_size", UNSET)

        current_page_index = d.pop("current_page_index", UNSET)

        _dataset_info = d.pop("dataset_info", UNSET)
        dataset_info: CompareDatasetDatasetInfo | Unset
        if isinstance(_dataset_info, Unset):
            dataset_info = UNSET
        else:
            dataset_info = CompareDatasetDatasetInfo.from_dict(_dataset_info)

        common_column_names = cast(list[str], d.pop("common_column_names", UNSET))

        compare_dataset = cls(
            base_column_name=base_column_name,
            dataset_ids=dataset_ids,
            compare_id=compare_id,
            page_size=page_size,
            current_page_index=current_page_index,
            dataset_info=dataset_info,
            common_column_names=common_column_names,
        )

        compare_dataset.additional_properties = d
        return compare_dataset

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
