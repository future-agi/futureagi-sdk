from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.trace_session_list_metadata_query_applied_filter_version import (
    TraceSessionListMetadataQueryAppliedFilterVersion,
)
from ..models.trace_session_list_metadata_query_provenance import (
    TraceSessionListMetadataQueryProvenance,
)
from ..models.trace_session_list_metadata_query_status import (
    TraceSessionListMetadataQueryStatus,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceSessionListMetadata")


@_attrs_define
class TraceSessionListMetadata:
    """
    Attributes:
        total_rows (int):
        total_rows_exact (int | None | Unset):
        total_rows_is_lower_bound (bool | Unset):
        has_more (bool | Unset):
        next_cursor (None | str | Unset):
        next_cursor_fingerprint (None | str | Unset):
        query_complete (bool | Unset):
        query_status (TraceSessionListMetadataQueryStatus | Unset):
        query_error_code (None | str | Unset):
        query_elapsed_ms (float | Unset):
        query_count (int | Unset):
        query_rows_returned (int | Unset):
        query_result_payload_bytes (int | Unset):
        query_applied_filter_version (TraceSessionListMetadataQueryAppliedFilterVersion | Unset):
        query_applied_filter_sha256 (str | Unset):
        query_applied_filter_count (int | Unset):
        query_exact (bool | Unset):
        ordering_exact (bool | Unset):
        query_provenance (TraceSessionListMetadataQueryProvenance | Unset):
    """

    total_rows: int
    total_rows_exact: int | None | Unset = UNSET
    total_rows_is_lower_bound: bool | Unset = UNSET
    has_more: bool | Unset = UNSET
    next_cursor: None | str | Unset = UNSET
    next_cursor_fingerprint: None | str | Unset = UNSET
    query_complete: bool | Unset = UNSET
    query_status: TraceSessionListMetadataQueryStatus | Unset = UNSET
    query_error_code: None | str | Unset = UNSET
    query_elapsed_ms: float | Unset = UNSET
    query_count: int | Unset = UNSET
    query_rows_returned: int | Unset = UNSET
    query_result_payload_bytes: int | Unset = UNSET
    query_applied_filter_version: (
        TraceSessionListMetadataQueryAppliedFilterVersion | Unset
    ) = UNSET
    query_applied_filter_sha256: str | Unset = UNSET
    query_applied_filter_count: int | Unset = UNSET
    query_exact: bool | Unset = UNSET
    ordering_exact: bool | Unset = UNSET
    query_provenance: TraceSessionListMetadataQueryProvenance | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_rows = self.total_rows

        total_rows_exact: int | None | Unset
        if isinstance(self.total_rows_exact, Unset):
            total_rows_exact = UNSET
        else:
            total_rows_exact = self.total_rows_exact

        total_rows_is_lower_bound = self.total_rows_is_lower_bound

        has_more = self.has_more

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

        query_complete = self.query_complete

        query_status: str | Unset = UNSET
        if not isinstance(self.query_status, Unset):
            query_status = self.query_status.value

        query_error_code: None | str | Unset
        if isinstance(self.query_error_code, Unset):
            query_error_code = UNSET
        else:
            query_error_code = self.query_error_code

        query_elapsed_ms = self.query_elapsed_ms

        query_count = self.query_count

        query_rows_returned = self.query_rows_returned

        query_result_payload_bytes = self.query_result_payload_bytes

        query_applied_filter_version: str | Unset = UNSET
        if not isinstance(self.query_applied_filter_version, Unset):
            query_applied_filter_version = self.query_applied_filter_version.value

        query_applied_filter_sha256 = self.query_applied_filter_sha256

        query_applied_filter_count = self.query_applied_filter_count

        query_exact = self.query_exact

        ordering_exact = self.ordering_exact

        query_provenance: str | Unset = UNSET
        if not isinstance(self.query_provenance, Unset):
            query_provenance = self.query_provenance.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_rows": total_rows,
            }
        )
        if total_rows_exact is not UNSET:
            field_dict["total_rows_exact"] = total_rows_exact
        if total_rows_is_lower_bound is not UNSET:
            field_dict["total_rows_is_lower_bound"] = total_rows_is_lower_bound
        if has_more is not UNSET:
            field_dict["has_more"] = has_more
        if next_cursor is not UNSET:
            field_dict["next_cursor"] = next_cursor
        if next_cursor_fingerprint is not UNSET:
            field_dict["next_cursor_fingerprint"] = next_cursor_fingerprint
        if query_complete is not UNSET:
            field_dict["query_complete"] = query_complete
        if query_status is not UNSET:
            field_dict["query_status"] = query_status
        if query_error_code is not UNSET:
            field_dict["query_error_code"] = query_error_code
        if query_elapsed_ms is not UNSET:
            field_dict["query_elapsed_ms"] = query_elapsed_ms
        if query_count is not UNSET:
            field_dict["query_count"] = query_count
        if query_rows_returned is not UNSET:
            field_dict["query_rows_returned"] = query_rows_returned
        if query_result_payload_bytes is not UNSET:
            field_dict["query_result_payload_bytes"] = query_result_payload_bytes
        if query_applied_filter_version is not UNSET:
            field_dict["query_applied_filter_version"] = query_applied_filter_version
        if query_applied_filter_sha256 is not UNSET:
            field_dict["query_applied_filter_sha256"] = query_applied_filter_sha256
        if query_applied_filter_count is not UNSET:
            field_dict["query_applied_filter_count"] = query_applied_filter_count
        if query_exact is not UNSET:
            field_dict["query_exact"] = query_exact
        if ordering_exact is not UNSET:
            field_dict["ordering_exact"] = ordering_exact
        if query_provenance is not UNSET:
            field_dict["query_provenance"] = query_provenance

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_rows = d.pop("total_rows")

        def _parse_total_rows_exact(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_rows_exact = _parse_total_rows_exact(d.pop("total_rows_exact", UNSET))

        total_rows_is_lower_bound = d.pop("total_rows_is_lower_bound", UNSET)

        has_more = d.pop("has_more", UNSET)

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

        query_complete = d.pop("query_complete", UNSET)

        _query_status = d.pop("query_status", UNSET)
        query_status: TraceSessionListMetadataQueryStatus | Unset
        if isinstance(_query_status, Unset):
            query_status = UNSET
        else:
            query_status = TraceSessionListMetadataQueryStatus(_query_status)

        def _parse_query_error_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        query_error_code = _parse_query_error_code(d.pop("query_error_code", UNSET))

        query_elapsed_ms = d.pop("query_elapsed_ms", UNSET)

        query_count = d.pop("query_count", UNSET)

        query_rows_returned = d.pop("query_rows_returned", UNSET)

        query_result_payload_bytes = d.pop("query_result_payload_bytes", UNSET)

        _query_applied_filter_version = d.pop("query_applied_filter_version", UNSET)
        query_applied_filter_version: (
            TraceSessionListMetadataQueryAppliedFilterVersion | Unset
        )
        if isinstance(_query_applied_filter_version, Unset):
            query_applied_filter_version = UNSET
        else:
            query_applied_filter_version = (
                TraceSessionListMetadataQueryAppliedFilterVersion(
                    _query_applied_filter_version
                )
            )

        query_applied_filter_sha256 = d.pop("query_applied_filter_sha256", UNSET)

        query_applied_filter_count = d.pop("query_applied_filter_count", UNSET)

        query_exact = d.pop("query_exact", UNSET)

        ordering_exact = d.pop("ordering_exact", UNSET)

        _query_provenance = d.pop("query_provenance", UNSET)
        query_provenance: TraceSessionListMetadataQueryProvenance | Unset
        if isinstance(_query_provenance, Unset):
            query_provenance = UNSET
        else:
            query_provenance = TraceSessionListMetadataQueryProvenance(
                _query_provenance
            )

        trace_session_list_metadata = cls(
            total_rows=total_rows,
            total_rows_exact=total_rows_exact,
            total_rows_is_lower_bound=total_rows_is_lower_bound,
            has_more=has_more,
            next_cursor=next_cursor,
            next_cursor_fingerprint=next_cursor_fingerprint,
            query_complete=query_complete,
            query_status=query_status,
            query_error_code=query_error_code,
            query_elapsed_ms=query_elapsed_ms,
            query_count=query_count,
            query_rows_returned=query_rows_returned,
            query_result_payload_bytes=query_result_payload_bytes,
            query_applied_filter_version=query_applied_filter_version,
            query_applied_filter_sha256=query_applied_filter_sha256,
            query_applied_filter_count=query_applied_filter_count,
            query_exact=query_exact,
            ordering_exact=ordering_exact,
            query_provenance=query_provenance,
        )

        trace_session_list_metadata.additional_properties = d
        return trace_session_list_metadata

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
