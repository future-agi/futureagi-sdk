from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.legacy_knowledge_base_files_request_sort_item import (
        LegacyKnowledgeBaseFilesRequestSortItem,
    )


T = TypeVar("T", bound="LegacyKnowledgeBaseFilesRequest")


@_attrs_define
class LegacyKnowledgeBaseFilesRequest:
    """
    Attributes:
        kb_id (UUID):
        search (None | str | Unset):
        sort (list[LegacyKnowledgeBaseFilesRequestSortItem] | Unset):
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 10.
    """

    kb_id: UUID
    search: None | str | Unset = UNSET
    sort: list[LegacyKnowledgeBaseFilesRequestSortItem] | Unset = UNSET
    page_number: int | Unset = 0
    page_size: int | Unset = 10
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kb_id = str(self.kb_id)

        search: None | str | Unset
        if isinstance(self.search, Unset):
            search = UNSET
        else:
            search = self.search

        sort: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.sort, Unset):
            sort = []
            for sort_item_data in self.sort:
                sort_item = sort_item_data.to_dict()
                sort.append(sort_item)

        page_number = self.page_number

        page_size = self.page_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kb_id": kb_id,
            }
        )
        if search is not UNSET:
            field_dict["search"] = search
        if sort is not UNSET:
            field_dict["sort"] = sort
        if page_number is not UNSET:
            field_dict["page_number"] = page_number
        if page_size is not UNSET:
            field_dict["page_size"] = page_size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.legacy_knowledge_base_files_request_sort_item import (
            LegacyKnowledgeBaseFilesRequestSortItem,
        )

        d = dict(src_dict)
        kb_id = UUID(d.pop("kb_id"))

        def _parse_search(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        search = _parse_search(d.pop("search", UNSET))

        _sort = d.pop("sort", UNSET)
        sort: list[LegacyKnowledgeBaseFilesRequestSortItem] | Unset = UNSET
        if _sort is not UNSET:
            sort = []
            for sort_item_data in _sort:
                sort_item = LegacyKnowledgeBaseFilesRequestSortItem.from_dict(
                    sort_item_data
                )

                sort.append(sort_item)

        page_number = d.pop("page_number", UNSET)

        page_size = d.pop("page_size", UNSET)

        legacy_knowledge_base_files_request = cls(
            kb_id=kb_id,
            search=search,
            sort=sort,
            page_number=page_number,
            page_size=page_size,
        )

        legacy_knowledge_base_files_request.additional_properties = d
        return legacy_knowledge_base_files_request

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
