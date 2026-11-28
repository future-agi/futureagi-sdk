from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ScoreTrend")


@_attrs_define
class ScoreTrend:
    """
    Attributes:
        label (str):
        current (float):
        prev (float):
        sparkline (list[float]):
    """

    label: str
    current: float
    prev: float
    sparkline: list[float]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        label = self.label

        current = self.current

        prev = self.prev

        sparkline = self.sparkline

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "label": label,
                "current": current,
                "prev": prev,
                "sparkline": sparkline,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        label = d.pop("label")

        current = d.pop("current")

        prev = d.pop("prev")

        sparkline = cast(list[float], d.pop("sparkline"))

        score_trend = cls(
            label=label,
            current=current,
            prev=prev,
            sparkline=sparkline,
        )

        score_trend.additional_properties = d
        return score_trend

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
