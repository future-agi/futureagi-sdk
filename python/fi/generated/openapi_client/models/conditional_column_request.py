from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.conditional_column_request_config_item import (
        ConditionalColumnRequestConfigItem,
    )


T = TypeVar("T", bound="ConditionalColumnRequest")


@_attrs_define
class ConditionalColumnRequest:
    """
    Attributes:
        config (list[ConditionalColumnRequestConfigItem]):
        new_column_name (str):
        concurrency (int | Unset):  Default: 5.
    """

    config: list[ConditionalColumnRequestConfigItem]
    new_column_name: str
    concurrency: int | Unset = 5
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        config = []
        for config_item_data in self.config:
            config_item = config_item_data.to_dict()
            config.append(config_item)

        new_column_name = self.new_column_name

        concurrency = self.concurrency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "config": config,
                "new_column_name": new_column_name,
            }
        )
        if concurrency is not UNSET:
            field_dict["concurrency"] = concurrency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.conditional_column_request_config_item import (
            ConditionalColumnRequestConfigItem,
        )

        d = dict(src_dict)
        config = []
        _config = d.pop("config")
        for config_item_data in _config:
            config_item = ConditionalColumnRequestConfigItem.from_dict(config_item_data)

            config.append(config_item)

        new_column_name = d.pop("new_column_name")

        concurrency = d.pop("concurrency", UNSET)

        conditional_column_request = cls(
            config=config,
            new_column_name=new_column_name,
            concurrency=concurrency,
        )

        conditional_column_request.additional_properties = d
        return conditional_column_request

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
