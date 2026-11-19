from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pattern_insight_evidence import PatternInsightEvidence


T = TypeVar("T", bound="PatternInsight")


@_attrs_define
class PatternInsight:
    """
    Attributes:
        value (str):
        caption (str):
        title (str | Unset):  Default: ''.
        evidence (PatternInsightEvidence | Unset):
    """

    value: str
    caption: str
    title: str | Unset = ""
    evidence: PatternInsightEvidence | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = self.value

        caption = self.caption

        title = self.title

        evidence: dict[str, Any] | Unset = UNSET
        if not isinstance(self.evidence, Unset):
            evidence = self.evidence.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "value": value,
                "caption": caption,
            }
        )
        if title is not UNSET:
            field_dict["title"] = title
        if evidence is not UNSET:
            field_dict["evidence"] = evidence

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pattern_insight_evidence import PatternInsightEvidence

        d = dict(src_dict)
        value = d.pop("value")

        caption = d.pop("caption")

        title = d.pop("title", UNSET)

        _evidence = d.pop("evidence", UNSET)
        evidence: PatternInsightEvidence | Unset
        if isinstance(_evidence, Unset):
            evidence = UNSET
        else:
            evidence = PatternInsightEvidence.from_dict(_evidence)

        pattern_insight = cls(
            value=value,
            caption=caption,
            title=title,
            evidence=evidence,
        )

        pattern_insight.additional_properties = d
        return pattern_insight

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
