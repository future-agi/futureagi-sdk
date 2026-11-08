from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_behavior_request_column_config import (
        DatasetBehaviorRequestColumnConfig,
    )
    from ..models.dataset_behavior_request_dataset_config import (
        DatasetBehaviorRequestDatasetConfig,
    )


T = TypeVar("T", bound="DatasetBehaviorRequest")


@_attrs_define
class DatasetBehaviorRequest:
    """
    Attributes:
        dataset_name (str | Unset):
        column_order (list[UUID] | Unset):
        column_config (DatasetBehaviorRequestColumnConfig | Unset):
        dataset_config (DatasetBehaviorRequestDatasetConfig | Unset):
    """

    dataset_name: str | Unset = UNSET
    column_order: list[UUID] | Unset = UNSET
    column_config: DatasetBehaviorRequestColumnConfig | Unset = UNSET
    dataset_config: DatasetBehaviorRequestDatasetConfig | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_name = self.dataset_name

        column_order: list[str] | Unset = UNSET
        if not isinstance(self.column_order, Unset):
            column_order = []
            for column_order_item_data in self.column_order:
                column_order_item = str(column_order_item_data)
                column_order.append(column_order_item)

        column_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.column_config, Unset):
            column_config = self.column_config.to_dict()

        dataset_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dataset_config, Unset):
            dataset_config = self.dataset_config.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if dataset_name is not UNSET:
            field_dict["dataset_name"] = dataset_name
        if column_order is not UNSET:
            field_dict["column_order"] = column_order
        if column_config is not UNSET:
            field_dict["column_config"] = column_config
        if dataset_config is not UNSET:
            field_dict["dataset_config"] = dataset_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_behavior_request_column_config import (
            DatasetBehaviorRequestColumnConfig,
        )
        from ..models.dataset_behavior_request_dataset_config import (
            DatasetBehaviorRequestDatasetConfig,
        )

        d = dict(src_dict)
        dataset_name = d.pop("dataset_name", UNSET)

        _column_order = d.pop("column_order", UNSET)
        column_order: list[UUID] | Unset = UNSET
        if _column_order is not UNSET:
            column_order = []
            for column_order_item_data in _column_order:
                column_order_item = UUID(column_order_item_data)

                column_order.append(column_order_item)

        _column_config = d.pop("column_config", UNSET)
        column_config: DatasetBehaviorRequestColumnConfig | Unset
        if isinstance(_column_config, Unset):
            column_config = UNSET
        else:
            column_config = DatasetBehaviorRequestColumnConfig.from_dict(_column_config)

        _dataset_config = d.pop("dataset_config", UNSET)
        dataset_config: DatasetBehaviorRequestDatasetConfig | Unset
        if isinstance(_dataset_config, Unset):
            dataset_config = UNSET
        else:
            dataset_config = DatasetBehaviorRequestDatasetConfig.from_dict(
                _dataset_config
            )

        dataset_behavior_request = cls(
            dataset_name=dataset_name,
            column_order=column_order,
            column_config=column_config,
            dataset_config=dataset_config,
        )

        dataset_behavior_request.additional_properties = d
        return dataset_behavior_request

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
