from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.test_execution_detail_response_column_order_item import (
        TestExecutionDetailResponseColumnOrderItem,
    )
    from ..models.test_execution_detail_response_results_item import (
        TestExecutionDetailResponseResultsItem,
    )


T = TypeVar("T", bound="TestExecutionDetailResponse")


@_attrs_define
class TestExecutionDetailResponse:
    """
    Attributes:
        count (int | Unset):
        next_ (None | str | Unset):
        previous (None | str | Unset):
        results (list[TestExecutionDetailResponseResultsItem] | Unset): Call execution rows may include dynamic
            eval/scenario columns.
        total_pages (int | Unset):
        current_page (int | Unset):
        column_order (list[TestExecutionDetailResponseColumnOrderItem] | Unset):
        error_messages (list[str] | Unset):
        status (str | Unset):
        provider (str | Unset):
        agent_type (str | Unset):
    """

    count: int | Unset = UNSET
    next_: None | str | Unset = UNSET
    previous: None | str | Unset = UNSET
    results: list[TestExecutionDetailResponseResultsItem] | Unset = UNSET
    total_pages: int | Unset = UNSET
    current_page: int | Unset = UNSET
    column_order: list[TestExecutionDetailResponseColumnOrderItem] | Unset = UNSET
    error_messages: list[str] | Unset = UNSET
    status: str | Unset = UNSET
    provider: str | Unset = UNSET
    agent_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        next_: None | str | Unset
        if isinstance(self.next_, Unset):
            next_ = UNSET
        else:
            next_ = self.next_

        previous: None | str | Unset
        if isinstance(self.previous, Unset):
            previous = UNSET
        else:
            previous = self.previous

        results: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.results, Unset):
            results = []
            for results_item_data in self.results:
                results_item = results_item_data.to_dict()
                results.append(results_item)

        total_pages = self.total_pages

        current_page = self.current_page

        column_order: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.column_order, Unset):
            column_order = []
            for column_order_item_data in self.column_order:
                column_order_item = column_order_item_data.to_dict()
                column_order.append(column_order_item)

        error_messages: list[str] | Unset = UNSET
        if not isinstance(self.error_messages, Unset):
            error_messages = self.error_messages

        status = self.status

        provider = self.provider

        agent_type = self.agent_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if count is not UNSET:
            field_dict["count"] = count
        if next_ is not UNSET:
            field_dict["next"] = next_
        if previous is not UNSET:
            field_dict["previous"] = previous
        if results is not UNSET:
            field_dict["results"] = results
        if total_pages is not UNSET:
            field_dict["total_pages"] = total_pages
        if current_page is not UNSET:
            field_dict["current_page"] = current_page
        if column_order is not UNSET:
            field_dict["column_order"] = column_order
        if error_messages is not UNSET:
            field_dict["error_messages"] = error_messages
        if status is not UNSET:
            field_dict["status"] = status
        if provider is not UNSET:
            field_dict["provider"] = provider
        if agent_type is not UNSET:
            field_dict["agent_type"] = agent_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.test_execution_detail_response_column_order_item import (
            TestExecutionDetailResponseColumnOrderItem,
        )
        from ..models.test_execution_detail_response_results_item import (
            TestExecutionDetailResponseResultsItem,
        )

        d = dict(src_dict)
        count = d.pop("count", UNSET)

        def _parse_next_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_ = _parse_next_(d.pop("next", UNSET))

        def _parse_previous(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        previous = _parse_previous(d.pop("previous", UNSET))

        _results = d.pop("results", UNSET)
        results: list[TestExecutionDetailResponseResultsItem] | Unset = UNSET
        if _results is not UNSET:
            results = []
            for results_item_data in _results:
                results_item = TestExecutionDetailResponseResultsItem.from_dict(
                    results_item_data
                )

                results.append(results_item)

        total_pages = d.pop("total_pages", UNSET)

        current_page = d.pop("current_page", UNSET)

        _column_order = d.pop("column_order", UNSET)
        column_order: list[TestExecutionDetailResponseColumnOrderItem] | Unset = UNSET
        if _column_order is not UNSET:
            column_order = []
            for column_order_item_data in _column_order:
                column_order_item = (
                    TestExecutionDetailResponseColumnOrderItem.from_dict(
                        column_order_item_data
                    )
                )

                column_order.append(column_order_item)

        error_messages = cast(list[str], d.pop("error_messages", UNSET))

        status = d.pop("status", UNSET)

        provider = d.pop("provider", UNSET)

        agent_type = d.pop("agent_type", UNSET)

        test_execution_detail_response = cls(
            count=count,
            next_=next_,
            previous=previous,
            results=results,
            total_pages=total_pages,
            current_page=current_page,
            column_order=column_order,
            error_messages=error_messages,
            status=status,
            provider=provider,
            agent_type=agent_type,
        )

        test_execution_detail_response.additional_properties = d
        return test_execution_detail_response

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
