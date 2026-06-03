from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EventsOverTimePoint")


@_attrs_define
class EventsOverTimePoint:
    """
    Attributes:
        date (str):
        errors (int):
        passing (int):
        users (int):
    """

    date: str
    errors: int
    passing: int
    users: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        date = self.date

        errors = self.errors

        passing = self.passing

        users = self.users

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "date": date,
                "errors": errors,
                "passing": passing,
                "users": users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        date = d.pop("date")

        errors = d.pop("errors")

        passing = d.pop("passing")

        users = d.pop("users")

        events_over_time_point = cls(
            date=date,
            errors=errors,
            passing=passing,
            users=users,
        )

        events_over_time_point.additional_properties = d
        return events_over_time_point

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
