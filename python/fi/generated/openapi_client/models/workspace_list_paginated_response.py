from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.workspace_list_item_response import WorkspaceListItemResponse


T = TypeVar("T", bound="WorkspaceListPaginatedResponse")


@_attrs_define
class WorkspaceListPaginatedResponse:
    """
    Attributes:
        count (int):
        next_ (None | str):
        previous (None | str):
        results (list[WorkspaceListItemResponse]):
        total_pages (int):
        current_page (int):
    """

    count: int
    next_: None | str
    previous: None | str
    results: list[WorkspaceListItemResponse]
    total_pages: int
    current_page: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        next_: None | str
        next_ = self.next_

        previous: None | str
        previous = self.previous

        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        total_pages = self.total_pages

        current_page = self.current_page

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "count": count,
                "next": next_,
                "previous": previous,
                "results": results,
                "total_pages": total_pages,
                "current_page": current_page,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workspace_list_item_response import WorkspaceListItemResponse

        d = dict(src_dict)
        count = d.pop("count")

        def _parse_next_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_ = _parse_next_(d.pop("next"))

        def _parse_previous(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        previous = _parse_previous(d.pop("previous"))

        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = WorkspaceListItemResponse.from_dict(results_item_data)

            results.append(results_item)

        total_pages = d.pop("total_pages")

        current_page = d.pop("current_page")

        workspace_list_paginated_response = cls(
            count=count,
            next_=next_,
            previous=previous,
            results=results,
            total_pages=total_pages,
            current_page=current_page,
        )

        workspace_list_paginated_response.additional_properties = d
        return workspace_list_paginated_response

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
