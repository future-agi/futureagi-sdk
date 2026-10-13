from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.call_branch_analysis_response_analysis import (
        CallBranchAnalysisResponseAnalysis,
    )


T = TypeVar("T", bound="CallBranchAnalysisResponse")


@_attrs_define
class CallBranchAnalysisResponse:
    """
    Attributes:
        call_execution_id (UUID | Unset):
        scenario_id (None | Unset | UUID):
        scenario_name (None | str | Unset):
        analysis (CallBranchAnalysisResponseAnalysis | Unset):
        analyzed_at (datetime.datetime | Unset):
    """

    call_execution_id: UUID | Unset = UNSET
    scenario_id: None | Unset | UUID = UNSET
    scenario_name: None | str | Unset = UNSET
    analysis: CallBranchAnalysisResponseAnalysis | Unset = UNSET
    analyzed_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        call_execution_id: str | Unset = UNSET
        if not isinstance(self.call_execution_id, Unset):
            call_execution_id = str(self.call_execution_id)

        scenario_id: None | str | Unset
        if isinstance(self.scenario_id, Unset):
            scenario_id = UNSET
        elif isinstance(self.scenario_id, UUID):
            scenario_id = str(self.scenario_id)
        else:
            scenario_id = self.scenario_id

        scenario_name: None | str | Unset
        if isinstance(self.scenario_name, Unset):
            scenario_name = UNSET
        else:
            scenario_name = self.scenario_name

        analysis: dict[str, Any] | Unset = UNSET
        if not isinstance(self.analysis, Unset):
            analysis = self.analysis.to_dict()

        analyzed_at: str | Unset = UNSET
        if not isinstance(self.analyzed_at, Unset):
            analyzed_at = self.analyzed_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if call_execution_id is not UNSET:
            field_dict["call_execution_id"] = call_execution_id
        if scenario_id is not UNSET:
            field_dict["scenario_id"] = scenario_id
        if scenario_name is not UNSET:
            field_dict["scenario_name"] = scenario_name
        if analysis is not UNSET:
            field_dict["analysis"] = analysis
        if analyzed_at is not UNSET:
            field_dict["analyzed_at"] = analyzed_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.call_branch_analysis_response_analysis import (
            CallBranchAnalysisResponseAnalysis,
        )

        d = dict(src_dict)
        _call_execution_id = d.pop("call_execution_id", UNSET)
        call_execution_id: UUID | Unset
        if isinstance(_call_execution_id, Unset):
            call_execution_id = UNSET
        else:
            call_execution_id = UUID(_call_execution_id)

        def _parse_scenario_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                scenario_id_type_0 = UUID(data)

                return scenario_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        scenario_id = _parse_scenario_id(d.pop("scenario_id", UNSET))

        def _parse_scenario_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        scenario_name = _parse_scenario_name(d.pop("scenario_name", UNSET))

        _analysis = d.pop("analysis", UNSET)
        analysis: CallBranchAnalysisResponseAnalysis | Unset
        if isinstance(_analysis, Unset):
            analysis = UNSET
        else:
            analysis = CallBranchAnalysisResponseAnalysis.from_dict(_analysis)

        _analyzed_at = d.pop("analyzed_at", UNSET)
        analyzed_at: datetime.datetime | Unset
        if isinstance(_analyzed_at, Unset):
            analyzed_at = UNSET
        else:
            analyzed_at = isoparse(_analyzed_at)

        call_branch_analysis_response = cls(
            call_execution_id=call_execution_id,
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            analysis=analysis,
            analyzed_at=analyzed_at,
        )

        call_branch_analysis_response.additional_properties = d
        return call_branch_analysis_response

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
