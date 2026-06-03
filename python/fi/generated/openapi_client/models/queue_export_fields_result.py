from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_export_default_mapping import QueueExportDefaultMapping
    from ..models.queue_export_field import QueueExportField


T = TypeVar("T", bound="QueueExportFieldsResult")


@_attrs_define
class QueueExportFieldsResult:
    """
    Attributes:
        fields (list[QueueExportField]):
        default_mapping (list[QueueExportDefaultMapping]):
    """

    fields: list[QueueExportField]
    default_mapping: list[QueueExportDefaultMapping]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fields = []
        for fields_item_data in self.fields:
            fields_item = fields_item_data.to_dict()
            fields.append(fields_item)

        default_mapping = []
        for default_mapping_item_data in self.default_mapping:
            default_mapping_item = default_mapping_item_data.to_dict()
            default_mapping.append(default_mapping_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "fields": fields,
                "default_mapping": default_mapping,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_export_default_mapping import QueueExportDefaultMapping
        from ..models.queue_export_field import QueueExportField

        d = dict(src_dict)
        fields = []
        _fields = d.pop("fields")
        for fields_item_data in _fields:
            fields_item = QueueExportField.from_dict(fields_item_data)

            fields.append(fields_item)

        default_mapping = []
        _default_mapping = d.pop("default_mapping")
        for default_mapping_item_data in _default_mapping:
            default_mapping_item = QueueExportDefaultMapping.from_dict(
                default_mapping_item_data
            )

            default_mapping.append(default_mapping_item)

        queue_export_fields_result = cls(
            fields=fields,
            default_mapping=default_mapping,
        )

        queue_export_fields_result.additional_properties = d
        return queue_export_fields_result

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
