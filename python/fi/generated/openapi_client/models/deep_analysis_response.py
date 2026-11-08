from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.recommendation import Recommendation
    from ..models.root_cause import RootCause


T = TypeVar("T", bound="DeepAnalysisResponse")


@_attrs_define
class DeepAnalysisResponse:
    """
    Attributes:
        status (str):
        trace_id (str):
        root_causes (list[RootCause]):
        recommendations (list[Recommendation]):
        immediate_fix (None | str):
    """

    status: str
    trace_id: str
    root_causes: list[RootCause]
    recommendations: list[Recommendation]
    immediate_fix: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        trace_id = self.trace_id

        root_causes = []
        for root_causes_item_data in self.root_causes:
            root_causes_item = root_causes_item_data.to_dict()
            root_causes.append(root_causes_item)

        recommendations = []
        for recommendations_item_data in self.recommendations:
            recommendations_item = recommendations_item_data.to_dict()
            recommendations.append(recommendations_item)

        immediate_fix: None | str
        immediate_fix = self.immediate_fix

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "trace_id": trace_id,
                "root_causes": root_causes,
                "recommendations": recommendations,
                "immediate_fix": immediate_fix,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.recommendation import Recommendation
        from ..models.root_cause import RootCause

        d = dict(src_dict)
        status = d.pop("status")

        trace_id = d.pop("trace_id")

        root_causes = []
        _root_causes = d.pop("root_causes")
        for root_causes_item_data in _root_causes:
            root_causes_item = RootCause.from_dict(root_causes_item_data)

            root_causes.append(root_causes_item)

        recommendations = []
        _recommendations = d.pop("recommendations")
        for recommendations_item_data in _recommendations:
            recommendations_item = Recommendation.from_dict(recommendations_item_data)

            recommendations.append(recommendations_item)

        def _parse_immediate_fix(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        immediate_fix = _parse_immediate_fix(d.pop("immediate_fix"))

        deep_analysis_response = cls(
            status=status,
            trace_id=trace_id,
            root_causes=root_causes,
            recommendations=recommendations,
            immediate_fix=immediate_fix,
        )

        deep_analysis_response.additional_properties = d
        return deep_analysis_response

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
