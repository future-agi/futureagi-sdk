from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.hugging_face_dataset_list_request_filter_params import (
        HuggingFaceDatasetListRequestFilterParams,
    )


T = TypeVar("T", bound="HuggingFaceDatasetListRequest")


@_attrs_define
class HuggingFaceDatasetListRequest:
    """
    Attributes:
        search_query (str | Unset):  Default: ''.
        filter_params (HuggingFaceDatasetListRequestFilterParams | Unset):
    """

    search_query: str | Unset = ""
    filter_params: HuggingFaceDatasetListRequestFilterParams | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        search_query = self.search_query

        filter_params: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filter_params, Unset):
            filter_params = self.filter_params.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if search_query is not UNSET:
            field_dict["search_query"] = search_query
        if filter_params is not UNSET:
            field_dict["filter_params"] = filter_params

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hugging_face_dataset_list_request_filter_params import (
            HuggingFaceDatasetListRequestFilterParams,
        )

        d = dict(src_dict)
        search_query = d.pop("search_query", UNSET)

        _filter_params = d.pop("filter_params", UNSET)
        filter_params: HuggingFaceDatasetListRequestFilterParams | Unset
        if isinstance(_filter_params, Unset):
            filter_params = UNSET
        else:
            filter_params = HuggingFaceDatasetListRequestFilterParams.from_dict(
                _filter_params
            )

        hugging_face_dataset_list_request = cls(
            search_query=search_query,
            filter_params=filter_params,
        )

        hugging_face_dataset_list_request.additional_properties = d
        return hugging_face_dataset_list_request

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
