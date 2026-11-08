from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.trace_voice_call_list_response_query_applied_filter_version import (
    TraceVoiceCallListResponseQueryAppliedFilterVersion,
)
from ..models.trace_voice_call_list_response_query_status import (
    TraceVoiceCallListResponseQueryStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_observe_column_config import TraceObserveColumnConfig
    from ..models.trace_voice_call_list_response_results_item import (
        TraceVoiceCallListResponseResultsItem,
    )


T = TypeVar("T", bound="TraceVoiceCallListResponse")


@_attrs_define
class TraceVoiceCallListResponse:
    """
    Attributes:
        count (int):
        count_is_lower_bound (bool):
        total_pages (int):
        current_page (int):
        next_ (int | None):
        previous (int | None):
        results (list[TraceVoiceCallListResponseResultsItem]):
        config (list[TraceObserveColumnConfig]):
        has_more (bool):
        query_complete (bool):
        query_status (TraceVoiceCallListResponseQueryStatus):
        next_cursor (None | str | Unset):
        next_cursor_fingerprint (None | str | Unset):
        query_exact (bool | Unset):
        ordering_exact (bool | Unset):
        query_error_code (str | Unset):
        query_count (int | Unset):
        query_applied_filter_version (TraceVoiceCallListResponseQueryAppliedFilterVersion | Unset):
        query_applied_filter_sha256 (str | Unset):
        query_applied_filter_count (int | Unset):
    """

    count: int
    count_is_lower_bound: bool
    total_pages: int
    current_page: int
    next_: int | None
    previous: int | None
    results: list[TraceVoiceCallListResponseResultsItem]
    config: list[TraceObserveColumnConfig]
    has_more: bool
    query_complete: bool
    query_status: TraceVoiceCallListResponseQueryStatus
    next_cursor: None | str | Unset = UNSET
    next_cursor_fingerprint: None | str | Unset = UNSET
    query_exact: bool | Unset = UNSET
    ordering_exact: bool | Unset = UNSET
    query_error_code: str | Unset = UNSET
    query_count: int | Unset = UNSET
    query_applied_filter_version: (
        TraceVoiceCallListResponseQueryAppliedFilterVersion | Unset
    ) = UNSET
    query_applied_filter_sha256: str | Unset = UNSET
    query_applied_filter_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        count_is_lower_bound = self.count_is_lower_bound

        total_pages = self.total_pages

        current_page = self.current_page

        next_: int | None
        next_ = self.next_

        previous: int | None
        previous = self.previous

        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        config = []
        for config_item_data in self.config:
            config_item = config_item_data.to_dict()
            config.append(config_item)

        has_more = self.has_more

        query_complete = self.query_complete

        query_status = self.query_status.value

        next_cursor: None | str | Unset
        if isinstance(self.next_cursor, Unset):
            next_cursor = UNSET
        else:
            next_cursor = self.next_cursor

        next_cursor_fingerprint: None | str | Unset
        if isinstance(self.next_cursor_fingerprint, Unset):
            next_cursor_fingerprint = UNSET
        else:
            next_cursor_fingerprint = self.next_cursor_fingerprint

        query_exact = self.query_exact

        ordering_exact = self.ordering_exact

        query_error_code = self.query_error_code

        query_count = self.query_count

        query_applied_filter_version: str | Unset = UNSET
        if not isinstance(self.query_applied_filter_version, Unset):
            query_applied_filter_version = self.query_applied_filter_version.value

        query_applied_filter_sha256 = self.query_applied_filter_sha256

        query_applied_filter_count = self.query_applied_filter_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "count": count,
                "count_is_lower_bound": count_is_lower_bound,
                "total_pages": total_pages,
                "current_page": current_page,
                "next": next_,
                "previous": previous,
                "results": results,
                "config": config,
                "has_more": has_more,
                "query_complete": query_complete,
                "query_status": query_status,
            }
        )
        if next_cursor is not UNSET:
            field_dict["next_cursor"] = next_cursor
        if next_cursor_fingerprint is not UNSET:
            field_dict["next_cursor_fingerprint"] = next_cursor_fingerprint
        if query_exact is not UNSET:
            field_dict["query_exact"] = query_exact
        if ordering_exact is not UNSET:
            field_dict["ordering_exact"] = ordering_exact
        if query_error_code is not UNSET:
            field_dict["query_error_code"] = query_error_code
        if query_count is not UNSET:
            field_dict["query_count"] = query_count
        if query_applied_filter_version is not UNSET:
            field_dict["query_applied_filter_version"] = query_applied_filter_version
        if query_applied_filter_sha256 is not UNSET:
            field_dict["query_applied_filter_sha256"] = query_applied_filter_sha256
        if query_applied_filter_count is not UNSET:
            field_dict["query_applied_filter_count"] = query_applied_filter_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_observe_column_config import TraceObserveColumnConfig
        from ..models.trace_voice_call_list_response_results_item import (
            TraceVoiceCallListResponseResultsItem,
        )

        d = dict(src_dict)
        count = d.pop("count")

        count_is_lower_bound = d.pop("count_is_lower_bound")

        total_pages = d.pop("total_pages")

        current_page = d.pop("current_page")

        def _parse_next_(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        next_ = _parse_next_(d.pop("next"))

        def _parse_previous(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        previous = _parse_previous(d.pop("previous"))

        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = TraceVoiceCallListResponseResultsItem.from_dict(
                results_item_data
            )

            results.append(results_item)

        config = []
        _config = d.pop("config")
        for config_item_data in _config:
            config_item = TraceObserveColumnConfig.from_dict(config_item_data)

            config.append(config_item)

        has_more = d.pop("has_more")

        query_complete = d.pop("query_complete")

        query_status = TraceVoiceCallListResponseQueryStatus(d.pop("query_status"))

        def _parse_next_cursor(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_cursor = _parse_next_cursor(d.pop("next_cursor", UNSET))

        def _parse_next_cursor_fingerprint(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_cursor_fingerprint = _parse_next_cursor_fingerprint(
            d.pop("next_cursor_fingerprint", UNSET)
        )

        query_exact = d.pop("query_exact", UNSET)

        ordering_exact = d.pop("ordering_exact", UNSET)

        query_error_code = d.pop("query_error_code", UNSET)

        query_count = d.pop("query_count", UNSET)

        _query_applied_filter_version = d.pop("query_applied_filter_version", UNSET)
        query_applied_filter_version: (
            TraceVoiceCallListResponseQueryAppliedFilterVersion | Unset
        )
        if isinstance(_query_applied_filter_version, Unset):
            query_applied_filter_version = UNSET
        else:
            query_applied_filter_version = (
                TraceVoiceCallListResponseQueryAppliedFilterVersion(
                    _query_applied_filter_version
                )
            )

        query_applied_filter_sha256 = d.pop("query_applied_filter_sha256", UNSET)

        query_applied_filter_count = d.pop("query_applied_filter_count", UNSET)

        trace_voice_call_list_response = cls(
            count=count,
            count_is_lower_bound=count_is_lower_bound,
            total_pages=total_pages,
            current_page=current_page,
            next_=next_,
            previous=previous,
            results=results,
            config=config,
            has_more=has_more,
            query_complete=query_complete,
            query_status=query_status,
            next_cursor=next_cursor,
            next_cursor_fingerprint=next_cursor_fingerprint,
            query_exact=query_exact,
            ordering_exact=ordering_exact,
            query_error_code=query_error_code,
            query_count=query_count,
            query_applied_filter_version=query_applied_filter_version,
            query_applied_filter_sha256=query_applied_filter_sha256,
            query_applied_filter_count=query_applied_filter_count,
        )

        trace_voice_call_list_response.additional_properties = d
        return trace_voice_call_list_response

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
