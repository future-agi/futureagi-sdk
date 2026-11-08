from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.users_result_approximate_fields_item import (
    UsersResultApproximateFieldsItem,
)
from ..models.users_result_ordering import UsersResultOrdering
from ..models.users_result_query_provenance import UsersResultQueryProvenance
from ..models.users_result_query_status import UsersResultQueryStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.users_table_row import UsersTableRow


T = TypeVar("T", bound="UsersResult")


@_attrs_define
class UsersResult:
    """
    Attributes:
        table (list[UsersTableRow]):
        total_count (int):
        total_pages (int):
        count_is_lower_bound (bool | Unset):
        has_more (bool | Unset):
        next_cursor (None | str | Unset):
        next_cursor_fingerprint (None | str | Unset):
        query_complete (bool | Unset):
        query_status (UsersResultQueryStatus | Unset):
        query_exact (bool | Unset):
        query_provenance (UsersResultQueryProvenance | Unset):
        ordering_exact (bool | Unset):
        ordering (UsersResultOrdering | Unset):
        approximate_fields (list[UsersResultApproximateFieldsItem] | Unset):
    """

    table: list[UsersTableRow]
    total_count: int
    total_pages: int
    count_is_lower_bound: bool | Unset = UNSET
    has_more: bool | Unset = UNSET
    next_cursor: None | str | Unset = UNSET
    next_cursor_fingerprint: None | str | Unset = UNSET
    query_complete: bool | Unset = UNSET
    query_status: UsersResultQueryStatus | Unset = UNSET
    query_exact: bool | Unset = UNSET
    query_provenance: UsersResultQueryProvenance | Unset = UNSET
    ordering_exact: bool | Unset = UNSET
    ordering: UsersResultOrdering | Unset = UNSET
    approximate_fields: list[UsersResultApproximateFieldsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        table = []
        for table_item_data in self.table:
            table_item = table_item_data.to_dict()
            table.append(table_item)

        total_count = self.total_count

        total_pages = self.total_pages

        count_is_lower_bound = self.count_is_lower_bound

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

        query_exact = self.query_exact

        query_provenance: str | Unset = UNSET
        if not isinstance(self.query_provenance, Unset):
            query_provenance = self.query_provenance.value

        ordering_exact = self.ordering_exact

        ordering: str | Unset = UNSET
        if not isinstance(self.ordering, Unset):
            ordering = self.ordering.value

        approximate_fields: list[str] | Unset = UNSET
        if not isinstance(self.approximate_fields, Unset):
            approximate_fields = []
            for approximate_fields_item_data in self.approximate_fields:
                approximate_fields_item = approximate_fields_item_data.value
                approximate_fields.append(approximate_fields_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "table": table,
                "total_count": total_count,
                "total_pages": total_pages,
            }
        )
        if count_is_lower_bound is not UNSET:
            field_dict["count_is_lower_bound"] = count_is_lower_bound
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
        if query_exact is not UNSET:
            field_dict["query_exact"] = query_exact
        if query_provenance is not UNSET:
            field_dict["query_provenance"] = query_provenance
        if ordering_exact is not UNSET:
            field_dict["ordering_exact"] = ordering_exact
        if ordering is not UNSET:
            field_dict["ordering"] = ordering
        if approximate_fields is not UNSET:
            field_dict["approximate_fields"] = approximate_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.users_table_row import UsersTableRow

        d = dict(src_dict)
        table = []
        _table = d.pop("table")
        for table_item_data in _table:
            table_item = UsersTableRow.from_dict(table_item_data)

            table.append(table_item)

        total_count = d.pop("total_count")

        total_pages = d.pop("total_pages")

        count_is_lower_bound = d.pop("count_is_lower_bound", UNSET)

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
        query_status: UsersResultQueryStatus | Unset
        if isinstance(_query_status, Unset):
            query_status = UNSET
        else:
            query_status = UsersResultQueryStatus(_query_status)

        query_exact = d.pop("query_exact", UNSET)

        _query_provenance = d.pop("query_provenance", UNSET)
        query_provenance: UsersResultQueryProvenance | Unset
        if isinstance(_query_provenance, Unset):
            query_provenance = UNSET
        else:
            query_provenance = UsersResultQueryProvenance(_query_provenance)

        ordering_exact = d.pop("ordering_exact", UNSET)

        _ordering = d.pop("ordering", UNSET)
        ordering: UsersResultOrdering | Unset
        if isinstance(_ordering, Unset):
            ordering = UNSET
        else:
            ordering = UsersResultOrdering(_ordering)

        _approximate_fields = d.pop("approximate_fields", UNSET)
        approximate_fields: list[UsersResultApproximateFieldsItem] | Unset = UNSET
        if _approximate_fields is not UNSET:
            approximate_fields = []
            for approximate_fields_item_data in _approximate_fields:
                approximate_fields_item = UsersResultApproximateFieldsItem(
                    approximate_fields_item_data
                )

                approximate_fields.append(approximate_fields_item)

        users_result = cls(
            table=table,
            total_count=total_count,
            total_pages=total_pages,
            count_is_lower_bound=count_is_lower_bound,
            has_more=has_more,
            next_cursor=next_cursor,
            next_cursor_fingerprint=next_cursor_fingerprint,
            query_complete=query_complete,
            query_status=query_status,
            query_exact=query_exact,
            query_provenance=query_provenance,
            ordering_exact=ordering_exact,
            ordering=ordering,
            approximate_fields=approximate_fields,
        )

        users_result.additional_properties = d
        return users_result

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
