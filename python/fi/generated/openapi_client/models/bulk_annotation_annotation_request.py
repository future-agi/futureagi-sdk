from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BulkAnnotationAnnotationRequest")


@_attrs_define
class BulkAnnotationAnnotationRequest:
    """
    Attributes:
        annotation_label_id (UUID):
        value (str | Unset):
        value_float (float | Unset):
        value_bool (bool | Unset):
        value_str_list (list[str] | Unset):
    """

    annotation_label_id: UUID
    value: str | Unset = UNSET
    value_float: float | Unset = UNSET
    value_bool: bool | Unset = UNSET
    value_str_list: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        annotation_label_id = str(self.annotation_label_id)

        value = self.value

        value_float = self.value_float

        value_bool = self.value_bool

        value_str_list: list[str] | Unset = UNSET
        if not isinstance(self.value_str_list, Unset):
            value_str_list = self.value_str_list

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "annotation_label_id": annotation_label_id,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value
        if value_float is not UNSET:
            field_dict["value_float"] = value_float
        if value_bool is not UNSET:
            field_dict["value_bool"] = value_bool
        if value_str_list is not UNSET:
            field_dict["value_str_list"] = value_str_list

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        annotation_label_id = UUID(d.pop("annotation_label_id"))

        value = d.pop("value", UNSET)

        value_float = d.pop("value_float", UNSET)

        value_bool = d.pop("value_bool", UNSET)

        value_str_list = cast(list[str], d.pop("value_str_list", UNSET))

        bulk_annotation_annotation_request = cls(
            annotation_label_id=annotation_label_id,
            value=value,
            value_float=value_float,
            value_bool=value_bool,
            value_str_list=value_str_list,
        )

        bulk_annotation_annotation_request.additional_properties = d
        return bulk_annotation_annotation_request

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
