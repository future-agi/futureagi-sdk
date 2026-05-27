from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EvalExplanationCluster")


@_attrs_define
class EvalExplanationCluster:
    """
    Attributes:
        kind (str | Unset):
        confidence (str | Unset):
        theme (str | Unset):
        guidance (str | Unset):
        evidence_summary (str | Unset):
        eval_config_id (UUID | Unset):
        eval_template_id (UUID | Unset):
        eval_name (str | Unset):
    """

    kind: str | Unset = UNSET
    confidence: str | Unset = UNSET
    theme: str | Unset = UNSET
    guidance: str | Unset = UNSET
    evidence_summary: str | Unset = UNSET
    eval_config_id: UUID | Unset = UNSET
    eval_template_id: UUID | Unset = UNSET
    eval_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kind = self.kind

        confidence = self.confidence

        theme = self.theme

        guidance = self.guidance

        evidence_summary = self.evidence_summary

        eval_config_id: str | Unset = UNSET
        if not isinstance(self.eval_config_id, Unset):
            eval_config_id = str(self.eval_config_id)

        eval_template_id: str | Unset = UNSET
        if not isinstance(self.eval_template_id, Unset):
            eval_template_id = str(self.eval_template_id)

        eval_name = self.eval_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kind is not UNSET:
            field_dict["kind"] = kind
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if theme is not UNSET:
            field_dict["theme"] = theme
        if guidance is not UNSET:
            field_dict["guidance"] = guidance
        if evidence_summary is not UNSET:
            field_dict["evidenceSummary"] = evidence_summary
        if eval_config_id is not UNSET:
            field_dict["eval_config_id"] = eval_config_id
        if eval_template_id is not UNSET:
            field_dict["eval_template_id"] = eval_template_id
        if eval_name is not UNSET:
            field_dict["eval_name"] = eval_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        kind = d.pop("kind", UNSET)

        confidence = d.pop("confidence", UNSET)

        theme = d.pop("theme", UNSET)

        guidance = d.pop("guidance", UNSET)

        evidence_summary = d.pop("evidenceSummary", UNSET)

        _eval_config_id = d.pop("eval_config_id", UNSET)
        eval_config_id: UUID | Unset
        if isinstance(_eval_config_id, Unset):
            eval_config_id = UNSET
        else:
            eval_config_id = UUID(_eval_config_id)

        _eval_template_id = d.pop("eval_template_id", UNSET)
        eval_template_id: UUID | Unset
        if isinstance(_eval_template_id, Unset):
            eval_template_id = UNSET
        else:
            eval_template_id = UUID(_eval_template_id)

        eval_name = d.pop("eval_name", UNSET)

        eval_explanation_cluster = cls(
            kind=kind,
            confidence=confidence,
            theme=theme,
            guidance=guidance,
            evidence_summary=evidence_summary,
            eval_config_id=eval_config_id,
            eval_template_id=eval_template_id,
            eval_name=eval_name,
        )

        eval_explanation_cluster.additional_properties = d
        return eval_explanation_cluster

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
