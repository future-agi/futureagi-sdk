from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_simulation_scenario_item import PromptSimulationScenarioItem


T = TypeVar("T", bound="PromptSimulationScenariosResult")


@_attrs_define
class PromptSimulationScenariosResult:
    """
    Attributes:
        count (int | Unset):
        page (int | Unset):
        limit (int | Unset):
        results (list[PromptSimulationScenarioItem] | Unset):
    """

    count: int | Unset = UNSET
    page: int | Unset = UNSET
    limit: int | Unset = UNSET
    results: list[PromptSimulationScenarioItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        page = self.page

        limit = self.limit

        results: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.results, Unset):
            results = []
            for results_item_data in self.results:
                results_item = results_item_data.to_dict()
                results.append(results_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if count is not UNSET:
            field_dict["count"] = count
        if page is not UNSET:
            field_dict["page"] = page
        if limit is not UNSET:
            field_dict["limit"] = limit
        if results is not UNSET:
            field_dict["results"] = results

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_simulation_scenario_item import (
            PromptSimulationScenarioItem,
        )

        d = dict(src_dict)
        count = d.pop("count", UNSET)

        page = d.pop("page", UNSET)

        limit = d.pop("limit", UNSET)

        _results = d.pop("results", UNSET)
        results: list[PromptSimulationScenarioItem] | Unset = UNSET
        if _results is not UNSET:
            results = []
            for results_item_data in _results:
                results_item = PromptSimulationScenarioItem.from_dict(results_item_data)

                results.append(results_item)

        prompt_simulation_scenarios_result = cls(
            count=count,
            page=page,
            limit=limit,
            results=results,
        )

        prompt_simulation_scenarios_result.additional_properties = d
        return prompt_simulation_scenarios_result

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
