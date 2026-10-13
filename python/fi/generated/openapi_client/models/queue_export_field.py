from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueExportField")


@_attrs_define
class QueueExportField:
    """
    Attributes:
        id (str):
        label (str):
        column (str):
        data_type (str):
        group (str):
        default (bool):
        path (str | Unset):
        source_type (str | Unset):
        kind (str | Unset):
        label_id (UUID | Unset):
        slot (int | Unset):
        eval_key (str | Unset):
        expand_fields (list[str] | Unset):
    """

    id: str
    label: str
    column: str
    data_type: str
    group: str
    default: bool
    path: str | Unset = UNSET
    source_type: str | Unset = UNSET
    kind: str | Unset = UNSET
    label_id: UUID | Unset = UNSET
    slot: int | Unset = UNSET
    eval_key: str | Unset = UNSET
    expand_fields: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        label = self.label

        column = self.column

        data_type = self.data_type

        group = self.group

        default = self.default

        path = self.path

        source_type = self.source_type

        kind = self.kind

        label_id: str | Unset = UNSET
        if not isinstance(self.label_id, Unset):
            label_id = str(self.label_id)

        slot = self.slot

        eval_key = self.eval_key

        expand_fields: list[str] | Unset = UNSET
        if not isinstance(self.expand_fields, Unset):
            expand_fields = self.expand_fields

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "label": label,
                "column": column,
                "data_type": data_type,
                "group": group,
                "default": default,
            }
        )
        if path is not UNSET:
            field_dict["path"] = path
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if kind is not UNSET:
            field_dict["kind"] = kind
        if label_id is not UNSET:
            field_dict["label_id"] = label_id
        if slot is not UNSET:
            field_dict["slot"] = slot
        if eval_key is not UNSET:
            field_dict["eval_key"] = eval_key
        if expand_fields is not UNSET:
            field_dict["expand_fields"] = expand_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        label = d.pop("label")

        column = d.pop("column")

        data_type = d.pop("data_type")

        group = d.pop("group")

        default = d.pop("default")

        path = d.pop("path", UNSET)

        source_type = d.pop("source_type", UNSET)

        kind = d.pop("kind", UNSET)

        _label_id = d.pop("label_id", UNSET)
        label_id: UUID | Unset
        if isinstance(_label_id, Unset):
            label_id = UNSET
        else:
            label_id = UUID(_label_id)

        slot = d.pop("slot", UNSET)

        eval_key = d.pop("eval_key", UNSET)

        expand_fields = cast(list[str], d.pop("expand_fields", UNSET))

        queue_export_field = cls(
            id=id,
            label=label,
            column=column,
            data_type=data_type,
            group=group,
            default=default,
            path=path,
            source_type=source_type,
            kind=kind,
            label_id=label_id,
            slot=slot,
            eval_key=eval_key,
            expand_fields=expand_fields,
        )

        queue_export_field.additional_properties = d
        return queue_export_field

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
