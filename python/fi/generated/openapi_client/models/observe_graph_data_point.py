from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ObserveGraphDataPoint")


@_attrs_define
class ObserveGraphDataPoint:
    """
    Attributes:
        timestamp (str):
        value (float | None):
        primary_traffic (float | None | Unset):
    """

    timestamp: str
    value: float | None
    primary_traffic: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        timestamp = self.timestamp

        value: float | None
        value = self.value

        primary_traffic: float | None | Unset
        if isinstance(self.primary_traffic, Unset):
            primary_traffic = UNSET
        else:
            primary_traffic = self.primary_traffic

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "timestamp": timestamp,
                "value": value,
            }
        )
        if primary_traffic is not UNSET:
            field_dict["primary_traffic"] = primary_traffic

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        timestamp = d.pop("timestamp")

        def _parse_value(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        value = _parse_value(d.pop("value"))

        def _parse_primary_traffic(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        primary_traffic = _parse_primary_traffic(d.pop("primary_traffic", UNSET))

        observe_graph_data_point = cls(
            timestamp=timestamp,
            value=value,
            primary_traffic=primary_traffic,
        )

        observe_graph_data_point.additional_properties = d
        return observe_graph_data_point

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
