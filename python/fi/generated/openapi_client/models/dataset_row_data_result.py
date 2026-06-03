from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset_row_data_result_current import DatasetRowDataResultCurrent
    from ..models.dataset_row_navigation import DatasetRowNavigation


T = TypeVar("T", bound="DatasetRowDataResult")


@_attrs_define
class DatasetRowDataResult:
    """
    Attributes:
        next_ (DatasetRowNavigation):
        current (DatasetRowDataResultCurrent):
    """

    next_: DatasetRowNavigation
    current: DatasetRowDataResultCurrent
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        next_ = self.next_.to_dict()

        current = self.current.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "next": next_,
                "current": current,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_row_data_result_current import DatasetRowDataResultCurrent
        from ..models.dataset_row_navigation import DatasetRowNavigation

        d = dict(src_dict)
        next_ = DatasetRowNavigation.from_dict(d.pop("next"))

        current = DatasetRowDataResultCurrent.from_dict(d.pop("current"))

        dataset_row_data_result = cls(
            next_=next_,
            current=current,
        )

        dataset_row_data_result.additional_properties = d
        return dataset_row_data_result

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
