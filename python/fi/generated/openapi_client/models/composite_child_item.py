from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CompositeChildItem")


@_attrs_define
class CompositeChildItem:
    """
    Attributes:
        child_id (UUID):
        child_name (str):
        order (int):
        eval_type (str | Unset):
        pinned_version_id (None | Unset | UUID):
        pinned_version_number (int | None | Unset):
        weight (float | Unset):
        required_keys (list[str] | Unset):
    """

    child_id: UUID
    child_name: str
    order: int
    eval_type: str | Unset = UNSET
    pinned_version_id: None | Unset | UUID = UNSET
    pinned_version_number: int | None | Unset = UNSET
    weight: float | Unset = UNSET
    required_keys: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        child_id = str(self.child_id)

        child_name = self.child_name

        order = self.order

        eval_type = self.eval_type

        pinned_version_id: None | str | Unset
        if isinstance(self.pinned_version_id, Unset):
            pinned_version_id = UNSET
        elif isinstance(self.pinned_version_id, UUID):
            pinned_version_id = str(self.pinned_version_id)
        else:
            pinned_version_id = self.pinned_version_id

        pinned_version_number: int | None | Unset
        if isinstance(self.pinned_version_number, Unset):
            pinned_version_number = UNSET
        else:
            pinned_version_number = self.pinned_version_number

        weight = self.weight

        required_keys: list[str] | Unset = UNSET
        if not isinstance(self.required_keys, Unset):
            required_keys = self.required_keys

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "child_id": child_id,
                "child_name": child_name,
                "order": order,
            }
        )
        if eval_type is not UNSET:
            field_dict["eval_type"] = eval_type
        if pinned_version_id is not UNSET:
            field_dict["pinned_version_id"] = pinned_version_id
        if pinned_version_number is not UNSET:
            field_dict["pinned_version_number"] = pinned_version_number
        if weight is not UNSET:
            field_dict["weight"] = weight
        if required_keys is not UNSET:
            field_dict["required_keys"] = required_keys

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        child_id = UUID(d.pop("child_id"))

        child_name = d.pop("child_name")

        order = d.pop("order")

        eval_type = d.pop("eval_type", UNSET)

        def _parse_pinned_version_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                pinned_version_id_type_0 = UUID(data)

                return pinned_version_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        pinned_version_id = _parse_pinned_version_id(d.pop("pinned_version_id", UNSET))

        def _parse_pinned_version_number(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        pinned_version_number = _parse_pinned_version_number(
            d.pop("pinned_version_number", UNSET)
        )

        weight = d.pop("weight", UNSET)

        required_keys = cast(list[str], d.pop("required_keys", UNSET))

        composite_child_item = cls(
            child_id=child_id,
            child_name=child_name,
            order=order,
            eval_type=eval_type,
            pinned_version_id=pinned_version_id,
            pinned_version_number=pinned_version_number,
            weight=weight,
            required_keys=required_keys,
        )

        composite_child_item.additional_properties = d
        return composite_child_item

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
