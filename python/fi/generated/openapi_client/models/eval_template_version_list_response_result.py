from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_template_version_item import EvalTemplateVersionItem


T = TypeVar("T", bound="EvalTemplateVersionListResponseResult")


@_attrs_define
class EvalTemplateVersionListResponseResult:
    """
    Attributes:
        template_id (UUID):
        versions (list[EvalTemplateVersionItem]):
        total (int):
    """

    template_id: UUID
    versions: list[EvalTemplateVersionItem]
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template_id = str(self.template_id)

        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()
            versions.append(versions_item)

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template_id": template_id,
                "versions": versions,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_version_item import EvalTemplateVersionItem

        d = dict(src_dict)
        template_id = UUID(d.pop("template_id"))

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = EvalTemplateVersionItem.from_dict(versions_item_data)

            versions.append(versions_item)

        total = d.pop("total")

        eval_template_version_list_response_result = cls(
            template_id=template_id,
            versions=versions,
            total=total,
        )

        eval_template_version_list_response_result.additional_properties = d
        return eval_template_version_list_response_result

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
