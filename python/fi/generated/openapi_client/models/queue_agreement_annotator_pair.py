from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="QueueAgreementAnnotatorPair")


@_attrs_define
class QueueAgreementAnnotatorPair:
    """
    Attributes:
        annotator_1_id (str):
        annotator_2_id (str):
        agreement_pct (float):
        total_comparisons (int):
    """

    annotator_1_id: str
    annotator_2_id: str
    agreement_pct: float
    total_comparisons: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        annotator_1_id = self.annotator_1_id

        annotator_2_id = self.annotator_2_id

        agreement_pct = self.agreement_pct

        total_comparisons = self.total_comparisons

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "annotator_1_id": annotator_1_id,
                "annotator_2_id": annotator_2_id,
                "agreement_pct": agreement_pct,
                "total_comparisons": total_comparisons,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        annotator_1_id = d.pop("annotator_1_id")

        annotator_2_id = d.pop("annotator_2_id")

        agreement_pct = d.pop("agreement_pct")

        total_comparisons = d.pop("total_comparisons")

        queue_agreement_annotator_pair = cls(
            annotator_1_id=annotator_1_id,
            annotator_2_id=annotator_2_id,
            agreement_pct=agreement_pct,
            total_comparisons=total_comparisons,
        )

        queue_agreement_annotator_pair.additional_properties = d
        return queue_agreement_annotator_pair

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
