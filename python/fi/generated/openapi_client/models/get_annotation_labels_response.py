from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.annotation_label_response import AnnotationLabelResponse


T = TypeVar("T", bound="GetAnnotationLabelsResponse")


@_attrs_define
class GetAnnotationLabelsResponse:
    """
    Attributes:
        result (list[AnnotationLabelResponse]):
        status (bool | Unset):  Default: True.
    """

    result: list[AnnotationLabelResponse]
    status: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = []
        for result_item_data in self.result:
            result_item = result_item_data.to_dict()
            result.append(result_item)

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "result": result,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.annotation_label_response import AnnotationLabelResponse

        d = dict(src_dict)
        result = []
        _result = d.pop("result")
        for result_item_data in _result:
            result_item = AnnotationLabelResponse.from_dict(result_item_data)

            result.append(result_item)

        status = d.pop("status", UNSET)

        get_annotation_labels_response = cls(
            result=result,
            status=status,
        )

        get_annotation_labels_response.additional_properties = d
        return get_annotation_labels_response

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
