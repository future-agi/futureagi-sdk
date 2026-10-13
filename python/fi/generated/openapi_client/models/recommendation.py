from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Recommendation")


@_attrs_define
class Recommendation:
    """
    Attributes:
        id (str):
        title (str):
        description (str):
        priority (str):
        root_cause_link (int | None):
        immediate_fix (None | str):
        insights (None | str):
        evidence (list[str]):
    """

    id: str
    title: str
    description: str
    priority: str
    root_cause_link: int | None
    immediate_fix: None | str
    insights: None | str
    evidence: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title = self.title

        description = self.description

        priority = self.priority

        root_cause_link: int | None
        root_cause_link = self.root_cause_link

        immediate_fix: None | str
        immediate_fix = self.immediate_fix

        insights: None | str
        insights = self.insights

        evidence = self.evidence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "description": description,
                "priority": priority,
                "root_cause_link": root_cause_link,
                "immediate_fix": immediate_fix,
                "insights": insights,
                "evidence": evidence,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        title = d.pop("title")

        description = d.pop("description")

        priority = d.pop("priority")

        def _parse_root_cause_link(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        root_cause_link = _parse_root_cause_link(d.pop("root_cause_link"))

        def _parse_immediate_fix(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        immediate_fix = _parse_immediate_fix(d.pop("immediate_fix"))

        def _parse_insights(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        insights = _parse_insights(d.pop("insights"))

        evidence = cast(list[str], d.pop("evidence"))

        recommendation = cls(
            id=id,
            title=title,
            description=description,
            priority=priority,
            root_cause_link=root_cause_link,
            immediate_fix=immediate_fix,
            insights=insights,
            evidence=evidence,
        )

        recommendation.additional_properties = d
        return recommendation

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
