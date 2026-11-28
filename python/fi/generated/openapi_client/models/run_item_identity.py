from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RunItemIdentity")


@_attrs_define
class RunItemIdentity:
    """
    Attributes:
        example_id (UUID):
        trial_number (int):
    """

    example_id: UUID
    trial_number: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        example_id = str(self.example_id)

        trial_number = self.trial_number

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "example_id": example_id,
                "trial_number": trial_number,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        trial_number = d.pop("trial_number")

        run_item_identity = cls(
            example_id=example_id,
            trial_number=trial_number,
        )

        run_item_identity.additional_properties = d
        return run_item_identity

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
