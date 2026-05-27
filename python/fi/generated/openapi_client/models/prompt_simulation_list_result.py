from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_simulation_template_summary import (
        PromptSimulationTemplateSummary,
    )
    from ..models.run_test_response import RunTestResponse


T = TypeVar("T", bound="PromptSimulationListResult")


@_attrs_define
class PromptSimulationListResult:
    """
    Attributes:
        count (int | Unset):
        page (int | Unset):
        limit (int | Unset):
        results (list[RunTestResponse] | Unset):
        prompt_template (PromptSimulationTemplateSummary | Unset):
    """

    count: int | Unset = UNSET
    page: int | Unset = UNSET
    limit: int | Unset = UNSET
    results: list[RunTestResponse] | Unset = UNSET
    prompt_template: PromptSimulationTemplateSummary | Unset = UNSET
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

        prompt_template: dict[str, Any] | Unset = UNSET
        if not isinstance(self.prompt_template, Unset):
            prompt_template = self.prompt_template.to_dict()

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
        if prompt_template is not UNSET:
            field_dict["prompt_template"] = prompt_template

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_simulation_template_summary import (
            PromptSimulationTemplateSummary,
        )
        from ..models.run_test_response import RunTestResponse

        d = dict(src_dict)
        count = d.pop("count", UNSET)

        page = d.pop("page", UNSET)

        limit = d.pop("limit", UNSET)

        _results = d.pop("results", UNSET)
        results: list[RunTestResponse] | Unset = UNSET
        if _results is not UNSET:
            results = []
            for results_item_data in _results:
                results_item = RunTestResponse.from_dict(results_item_data)

                results.append(results_item)

        _prompt_template = d.pop("prompt_template", UNSET)
        prompt_template: PromptSimulationTemplateSummary | Unset
        if isinstance(_prompt_template, Unset):
            prompt_template = UNSET
        else:
            prompt_template = PromptSimulationTemplateSummary.from_dict(
                _prompt_template
            )

        prompt_simulation_list_result = cls(
            count=count,
            page=page,
            limit=limit,
            results=results,
            prompt_template=prompt_template,
        )

        prompt_simulation_list_result.additional_properties = d
        return prompt_simulation_list_result

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
