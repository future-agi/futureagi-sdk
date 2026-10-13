from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.compare_evals_list_request_eval_type import (
    CompareEvalsListRequestEvalType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="CompareEvalsListRequest")


@_attrs_define
class CompareEvalsListRequest:
    """
    Attributes:
        eval_type (CompareEvalsListRequestEvalType):
        dataset_ids (list[UUID]):
        search_text (str | Unset):  Default: ''.
    """

    eval_type: CompareEvalsListRequestEvalType
    dataset_ids: list[UUID]
    search_text: str | Unset = ""
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_type = self.eval_type.value

        dataset_ids = []
        for dataset_ids_item_data in self.dataset_ids:
            dataset_ids_item = str(dataset_ids_item_data)
            dataset_ids.append(dataset_ids_item)

        search_text = self.search_text

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval_type": eval_type,
                "dataset_ids": dataset_ids,
            }
        )
        if search_text is not UNSET:
            field_dict["search_text"] = search_text

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        eval_type = CompareEvalsListRequestEvalType(d.pop("eval_type"))

        dataset_ids = []
        _dataset_ids = d.pop("dataset_ids")
        for dataset_ids_item_data in _dataset_ids:
            dataset_ids_item = UUID(dataset_ids_item_data)

            dataset_ids.append(dataset_ids_item)

        search_text = d.pop("search_text", UNSET)

        compare_evals_list_request = cls(
            eval_type=eval_type,
            dataset_ids=dataset_ids,
            search_text=search_text,
        )

        compare_evals_list_request.additional_properties = d
        return compare_evals_list_request

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
