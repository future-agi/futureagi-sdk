from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AnnotationSummaryHeader")


@_attrs_define
class AnnotationSummaryHeader:
    """
    Attributes:
        dataset_coverage (float | None | Unset):
        completion_eta (float | None | Unset):
        overall_agreement (float | None | Unset):
    """

    dataset_coverage: float | None | Unset = UNSET
    completion_eta: float | None | Unset = UNSET
    overall_agreement: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_coverage: float | None | Unset
        if isinstance(self.dataset_coverage, Unset):
            dataset_coverage = UNSET
        else:
            dataset_coverage = self.dataset_coverage

        completion_eta: float | None | Unset
        if isinstance(self.completion_eta, Unset):
            completion_eta = UNSET
        else:
            completion_eta = self.completion_eta

        overall_agreement: float | None | Unset
        if isinstance(self.overall_agreement, Unset):
            overall_agreement = UNSET
        else:
            overall_agreement = self.overall_agreement

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if dataset_coverage is not UNSET:
            field_dict["dataset_coverage"] = dataset_coverage
        if completion_eta is not UNSET:
            field_dict["completion_eta"] = completion_eta
        if overall_agreement is not UNSET:
            field_dict["overall_agreement"] = overall_agreement

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_dataset_coverage(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        dataset_coverage = _parse_dataset_coverage(d.pop("dataset_coverage", UNSET))

        def _parse_completion_eta(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        completion_eta = _parse_completion_eta(d.pop("completion_eta", UNSET))

        def _parse_overall_agreement(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        overall_agreement = _parse_overall_agreement(d.pop("overall_agreement", UNSET))

        annotation_summary_header = cls(
            dataset_coverage=dataset_coverage,
            completion_eta=completion_eta,
            overall_agreement=overall_agreement,
        )

        annotation_summary_header.additional_properties = d
        return annotation_summary_header

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
