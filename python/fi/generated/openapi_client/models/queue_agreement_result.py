from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_agreement_annotator_pair import QueueAgreementAnnotatorPair
    from ..models.queue_agreement_result_labels import QueueAgreementResultLabels


T = TypeVar("T", bound="QueueAgreementResult")


@_attrs_define
class QueueAgreementResult:
    """
    Attributes:
        overall_agreement (float | None):
        labels (QueueAgreementResultLabels):
        annotator_pairs (list[QueueAgreementAnnotatorPair]):
    """

    overall_agreement: float | None
    labels: QueueAgreementResultLabels
    annotator_pairs: list[QueueAgreementAnnotatorPair]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        overall_agreement: float | None
        overall_agreement = self.overall_agreement

        labels = self.labels.to_dict()

        annotator_pairs = []
        for annotator_pairs_item_data in self.annotator_pairs:
            annotator_pairs_item = annotator_pairs_item_data.to_dict()
            annotator_pairs.append(annotator_pairs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "overall_agreement": overall_agreement,
                "labels": labels,
                "annotator_pairs": annotator_pairs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_agreement_annotator_pair import QueueAgreementAnnotatorPair
        from ..models.queue_agreement_result_labels import QueueAgreementResultLabels

        d = dict(src_dict)

        def _parse_overall_agreement(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        overall_agreement = _parse_overall_agreement(d.pop("overall_agreement"))

        labels = QueueAgreementResultLabels.from_dict(d.pop("labels"))

        annotator_pairs = []
        _annotator_pairs = d.pop("annotator_pairs")
        for annotator_pairs_item_data in _annotator_pairs:
            annotator_pairs_item = QueueAgreementAnnotatorPair.from_dict(
                annotator_pairs_item_data
            )

            annotator_pairs.append(annotator_pairs_item)

        queue_agreement_result = cls(
            overall_agreement=overall_agreement,
            labels=labels,
            annotator_pairs=annotator_pairs,
        )

        queue_agreement_result.additional_properties = d
        return queue_agreement_result

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
