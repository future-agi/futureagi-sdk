from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FeedStats")


@_attrs_define
class FeedStats:
    """
    Attributes:
        total_errors (int):
        escalating (int):
        for_review (int):
        acknowledged (int):
        resolved (int):
        affected_users (int):
    """

    total_errors: int
    escalating: int
    for_review: int
    acknowledged: int
    resolved: int
    affected_users: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_errors = self.total_errors

        escalating = self.escalating

        for_review = self.for_review

        acknowledged = self.acknowledged

        resolved = self.resolved

        affected_users = self.affected_users

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_errors": total_errors,
                "escalating": escalating,
                "for_review": for_review,
                "acknowledged": acknowledged,
                "resolved": resolved,
                "affected_users": affected_users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_errors = d.pop("total_errors")

        escalating = d.pop("escalating")

        for_review = d.pop("for_review")

        acknowledged = d.pop("acknowledged")

        resolved = d.pop("resolved")

        affected_users = d.pop("affected_users")

        feed_stats = cls(
            total_errors=total_errors,
            escalating=escalating,
            for_review=for_review,
            acknowledged=acknowledged,
            resolved=resolved,
            affected_users=affected_users,
        )

        feed_stats.additional_properties = d
        return feed_stats

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
