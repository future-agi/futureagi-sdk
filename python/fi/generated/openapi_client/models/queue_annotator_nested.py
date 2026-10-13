from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueAnnotatorNested")


@_attrs_define
class QueueAnnotatorNested:
    """
    Attributes:
        user_id (UUID):
        id (UUID | Unset):
        name (str | Unset):
        email (str | Unset):
        role (str | Unset):  Default: 'annotator'.
        roles (str | Unset):
    """

    user_id: UUID
    id: UUID | Unset = UNSET
    name: str | Unset = UNSET
    email: str | Unset = UNSET
    role: str | Unset = "annotator"
    roles: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = str(self.user_id)

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        email = self.email

        role = self.role

        roles = self.roles

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if email is not UNSET:
            field_dict["email"] = email
        if role is not UNSET:
            field_dict["role"] = role
        if roles is not UNSET:
            field_dict["roles"] = roles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = UUID(d.pop("user_id"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        email = d.pop("email", UNSET)

        role = d.pop("role", UNSET)

        roles = d.pop("roles", UNSET)

        queue_annotator_nested = cls(
            user_id=user_id,
            id=id,
            name=name,
            email=email,
            role=role,
            roles=roles,
        )

        queue_annotator_nested.additional_properties = d
        return queue_annotator_nested

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
