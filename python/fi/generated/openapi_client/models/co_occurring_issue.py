from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CoOccurringIssue")


@_attrs_define
class CoOccurringIssue:
    """
    Attributes:
        id (str):
        title (str):
        type_ (str):
        co_occurrence (float):
        count (int):
        severity (str):
    """

    id: str
    title: str
    type_: str
    co_occurrence: float
    count: int
    severity: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title = self.title

        type_ = self.type_

        co_occurrence = self.co_occurrence

        count = self.count

        severity = self.severity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "type": type_,
                "co_occurrence": co_occurrence,
                "count": count,
                "severity": severity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        title = d.pop("title")

        type_ = d.pop("type")

        co_occurrence = d.pop("co_occurrence")

        count = d.pop("count")

        severity = d.pop("severity")

        co_occurring_issue = cls(
            id=id,
            title=title,
            type_=type_,
            co_occurrence=co_occurrence,
            count=count,
            severity=severity,
        )

        co_occurring_issue.additional_properties = d
        return co_occurring_issue

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
