from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="QueueAgreementLabel")


@_attrs_define
class QueueAgreementLabel:
    """
    Attributes:
        label_name (None | str):
        label_type (None | str):
        agreement_pct (float | None):
        cohens_kappa (float | None):
        disagreement_count (int):
        disagreement_items (list[str]):
    """

    label_name: None | str
    label_type: None | str
    agreement_pct: float | None
    cohens_kappa: float | None
    disagreement_count: int
    disagreement_items: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        label_name: None | str
        label_name = self.label_name

        label_type: None | str
        label_type = self.label_type

        agreement_pct: float | None
        agreement_pct = self.agreement_pct

        cohens_kappa: float | None
        cohens_kappa = self.cohens_kappa

        disagreement_count = self.disagreement_count

        disagreement_items = self.disagreement_items

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "label_name": label_name,
                "label_type": label_type,
                "agreement_pct": agreement_pct,
                "cohens_kappa": cohens_kappa,
                "disagreement_count": disagreement_count,
                "disagreement_items": disagreement_items,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_label_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        label_name = _parse_label_name(d.pop("label_name"))

        def _parse_label_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        label_type = _parse_label_type(d.pop("label_type"))

        def _parse_agreement_pct(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        agreement_pct = _parse_agreement_pct(d.pop("agreement_pct"))

        def _parse_cohens_kappa(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        cohens_kappa = _parse_cohens_kappa(d.pop("cohens_kappa"))

        disagreement_count = d.pop("disagreement_count")

        disagreement_items = cast(list[str], d.pop("disagreement_items"))

        queue_agreement_label = cls(
            label_name=label_name,
            label_type=label_type,
            agreement_pct=agreement_pct,
            cohens_kappa=cohens_kappa,
            disagreement_count=disagreement_count,
            disagreement_items=disagreement_items,
        )

        queue_agreement_label.additional_properties = d
        return queue_agreement_label

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
