from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceIndexQuery")


@_attrs_define
class TraceIndexQuery:
    """
    Attributes:
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset): JSON-encoded canonical filter list. Default: '[]'.
    """

    trace_id: UUID
    project_version_id: UUID
    filters: str | Unset = "[]"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        trace_id = str(self.trace_id)

        project_version_id = str(self.project_version_id)

        filters = self.filters

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "trace_id": trace_id,
                "project_version_id": project_version_id,
            }
        )
        if filters is not UNSET:
            field_dict["filters"] = filters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        trace_id = UUID(d.pop("trace_id"))

        project_version_id = UUID(d.pop("project_version_id"))

        filters = d.pop("filters", UNSET)

        trace_index_query = cls(
            trace_id=trace_id,
            project_version_id=project_version_id,
            filters=filters,
        )

        trace_index_query.additional_properties = d
        return trace_index_query

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
