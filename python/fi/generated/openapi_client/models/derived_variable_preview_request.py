from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.derived_variable_preview_request_content import (
        DerivedVariablePreviewRequestContent,
    )


T = TypeVar("T", bound="DerivedVariablePreviewRequest")


@_attrs_define
class DerivedVariablePreviewRequest:
    """
    Attributes:
        content (DerivedVariablePreviewRequestContent):
        column_name (str | Unset):  Default: 'output'.
    """

    content: DerivedVariablePreviewRequestContent
    column_name: str | Unset = "output"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content = self.content.to_dict()

        column_name = self.column_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
            }
        )
        if column_name is not UNSET:
            field_dict["column_name"] = column_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.derived_variable_preview_request_content import (
            DerivedVariablePreviewRequestContent,
        )

        d = dict(src_dict)
        content = DerivedVariablePreviewRequestContent.from_dict(d.pop("content"))

        column_name = d.pop("column_name", UNSET)

        derived_variable_preview_request = cls(
            content=content,
            column_name=column_name,
        )

        derived_variable_preview_request.additional_properties = d
        return derived_variable_preview_request

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
