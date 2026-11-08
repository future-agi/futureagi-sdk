from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.add_api_column_request_config import AddApiColumnRequestConfig


T = TypeVar("T", bound="AddApiColumnRequest")


@_attrs_define
class AddApiColumnRequest:
    """
    Attributes:
        column_name (str):
        config (AddApiColumnRequestConfig):
        concurrency (int | Unset):  Default: 5.
    """

    column_name: str
    config: AddApiColumnRequestConfig
    concurrency: int | Unset = 5
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_name = self.column_name

        config = self.config.to_dict()

        concurrency = self.concurrency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_name": column_name,
                "config": config,
            }
        )
        if concurrency is not UNSET:
            field_dict["concurrency"] = concurrency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.add_api_column_request_config import AddApiColumnRequestConfig

        d = dict(src_dict)
        column_name = d.pop("column_name")

        config = AddApiColumnRequestConfig.from_dict(d.pop("config"))

        concurrency = d.pop("concurrency", UNSET)

        add_api_column_request = cls(
            column_name=column_name,
            config=config,
            concurrency=concurrency,
        )

        add_api_column_request.additional_properties = d
        return add_api_column_request

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
