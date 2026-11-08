from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_row_cell_inner_metadata_error_analysis import (
        ExperimentRowCellInnerMetadataErrorAnalysis,
    )


T = TypeVar("T", bound="ExperimentRowCellInnerMetadata")


@_attrs_define
class ExperimentRowCellInnerMetadata:
    """
    Attributes:
        explanation (None | str | Unset):
        error_analysis (ExperimentRowCellInnerMetadataErrorAnalysis | Unset):
        selected_input_key (None | str | Unset):
    """

    explanation: None | str | Unset = UNSET
    error_analysis: ExperimentRowCellInnerMetadataErrorAnalysis | Unset = UNSET
    selected_input_key: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        explanation: None | str | Unset
        if isinstance(self.explanation, Unset):
            explanation = UNSET
        else:
            explanation = self.explanation

        error_analysis: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error_analysis, Unset):
            error_analysis = self.error_analysis.to_dict()

        selected_input_key: None | str | Unset
        if isinstance(self.selected_input_key, Unset):
            selected_input_key = UNSET
        else:
            selected_input_key = self.selected_input_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if explanation is not UNSET:
            field_dict["explanation"] = explanation
        if error_analysis is not UNSET:
            field_dict["error_analysis"] = error_analysis
        if selected_input_key is not UNSET:
            field_dict["selected_input_key"] = selected_input_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_row_cell_inner_metadata_error_analysis import (
            ExperimentRowCellInnerMetadataErrorAnalysis,
        )

        d = dict(src_dict)

        def _parse_explanation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        explanation = _parse_explanation(d.pop("explanation", UNSET))

        _error_analysis = d.pop("error_analysis", UNSET)
        error_analysis: ExperimentRowCellInnerMetadataErrorAnalysis | Unset
        if isinstance(_error_analysis, Unset):
            error_analysis = UNSET
        else:
            error_analysis = ExperimentRowCellInnerMetadataErrorAnalysis.from_dict(
                _error_analysis
            )

        def _parse_selected_input_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        selected_input_key = _parse_selected_input_key(
            d.pop("selected_input_key", UNSET)
        )

        experiment_row_cell_inner_metadata = cls(
            explanation=explanation,
            error_analysis=error_analysis,
            selected_input_key=selected_input_key,
        )

        experiment_row_cell_inner_metadata.additional_properties = d
        return experiment_row_cell_inner_metadata

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
