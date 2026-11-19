from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.experiment_dataset_comparison_result import (
        ExperimentDatasetComparisonResult,
    )


T = TypeVar("T", bound="ExperimentDatasetComparisonResponse")


@_attrs_define
class ExperimentDatasetComparisonResponse:
    """
    Attributes:
        status (bool):
        result (ExperimentDatasetComparisonResult):
    """

    status: bool
    result: ExperimentDatasetComparisonResult
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        result = self.result.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "result": result,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_dataset_comparison_result import (
            ExperimentDatasetComparisonResult,
        )

        d = dict(src_dict)
        status = d.pop("status")

        result = ExperimentDatasetComparisonResult.from_dict(d.pop("result"))

        experiment_dataset_comparison_response = cls(
            status=status,
            result=result,
        )

        experiment_dataset_comparison_response.additional_properties = d
        return experiment_dataset_comparison_response

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
