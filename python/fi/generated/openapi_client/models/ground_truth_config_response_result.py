from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.ground_truth_config import GroundTruthConfig


T = TypeVar("T", bound="GroundTruthConfigResponseResult")


@_attrs_define
class GroundTruthConfigResponseResult:
    """
    Attributes:
        ground_truth (GroundTruthConfig):
    """

    ground_truth: GroundTruthConfig
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ground_truth = self.ground_truth.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ground_truth": ground_truth,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ground_truth_config import GroundTruthConfig

        d = dict(src_dict)
        ground_truth = GroundTruthConfig.from_dict(d.pop("ground_truth"))

        ground_truth_config_response_result = cls(
            ground_truth=ground_truth,
        )

        ground_truth_config_response_result.additional_properties = d
        return ground_truth_config_response_result

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
