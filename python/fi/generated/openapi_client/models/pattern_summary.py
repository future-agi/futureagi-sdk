from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.key_moment import KeyMoment
    from ..models.pattern_insight import PatternInsight


T = TypeVar("T", bound="PatternSummary")


@_attrs_define
class PatternSummary:
    """
    Attributes:
        insights (list[PatternInsight]):
        key_moments (list[KeyMoment]):
    """

    insights: list[PatternInsight]
    key_moments: list[KeyMoment]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        insights = []
        for insights_item_data in self.insights:
            insights_item = insights_item_data.to_dict()
            insights.append(insights_item)

        key_moments = []
        for key_moments_item_data in self.key_moments:
            key_moments_item = key_moments_item_data.to_dict()
            key_moments.append(key_moments_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "insights": insights,
                "key_moments": key_moments,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.key_moment import KeyMoment
        from ..models.pattern_insight import PatternInsight

        d = dict(src_dict)
        insights = []
        _insights = d.pop("insights")
        for insights_item_data in _insights:
            insights_item = PatternInsight.from_dict(insights_item_data)

            insights.append(insights_item)

        key_moments = []
        _key_moments = d.pop("key_moments")
        for key_moments_item_data in _key_moments:
            key_moments_item = KeyMoment.from_dict(key_moments_item_data)

            key_moments.append(key_moments_item)

        pattern_summary = cls(
            insights=insights,
            key_moments=key_moments,
        )

        pattern_summary.additional_properties = d
        return pattern_summary

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
