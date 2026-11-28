from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FeedRedirect")


@_attrs_define
class FeedRedirect:
    """
    Attributes:
        requested_cluster_id (str):
        resolved_cluster_id (str):
    """

    requested_cluster_id: str
    resolved_cluster_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        requested_cluster_id = self.requested_cluster_id

        resolved_cluster_id = self.resolved_cluster_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "requested_cluster_id": requested_cluster_id,
                "resolved_cluster_id": resolved_cluster_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        requested_cluster_id = d.pop("requested_cluster_id")

        resolved_cluster_id = d.pop("resolved_cluster_id")

        feed_redirect = cls(
            requested_cluster_id=requested_cluster_id,
            resolved_cluster_id=resolved_cluster_id,
        )

        feed_redirect.additional_properties = d
        return feed_redirect

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
