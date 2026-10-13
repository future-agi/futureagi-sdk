from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.user_organization_role import UserOrganizationRole
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.organization import Organization
    from ..models.user_goals import UserGoals


T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """
    Attributes:
        email (str):
        name (str):
        id (UUID | Unset):
        organization_role (UserOrganizationRole | Unset):
        organization (Organization | Unset):
        created_at (datetime.datetime | Unset):
        status (str | Unset):
        role (None | str | Unset): User's job role (e.g., Data Scientist, ML Engineer, or custom role)
        goals (UserGoals | Unset): List of user's goals for using the platform
    """

    email: str
    name: str
    id: UUID | Unset = UNSET
    organization_role: UserOrganizationRole | Unset = UNSET
    organization: Organization | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    status: str | Unset = UNSET
    role: None | str | Unset = UNSET
    goals: UserGoals | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        name = self.name

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        organization_role: str | Unset = UNSET
        if not isinstance(self.organization_role, Unset):
            organization_role = self.organization_role.value

        organization: dict[str, Any] | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = self.organization.to_dict()

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        status = self.status

        role: None | str | Unset
        if isinstance(self.role, Unset):
            role = UNSET
        else:
            role = self.role

        goals: dict[str, Any] | Unset = UNSET
        if not isinstance(self.goals, Unset):
            goals = self.goals.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "name": name,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if organization_role is not UNSET:
            field_dict["organization_role"] = organization_role
        if organization is not UNSET:
            field_dict["organization"] = organization
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if status is not UNSET:
            field_dict["status"] = status
        if role is not UNSET:
            field_dict["role"] = role
        if goals is not UNSET:
            field_dict["goals"] = goals

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.organization import Organization
        from ..models.user_goals import UserGoals

        d = dict(src_dict)
        email = d.pop("email")

        name = d.pop("name")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _organization_role = d.pop("organization_role", UNSET)
        organization_role: UserOrganizationRole | Unset
        if isinstance(_organization_role, Unset):
            organization_role = UNSET
        else:
            organization_role = UserOrganizationRole(_organization_role)

        _organization = d.pop("organization", UNSET)
        organization: Organization | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = Organization.from_dict(_organization)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        status = d.pop("status", UNSET)

        def _parse_role(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        role = _parse_role(d.pop("role", UNSET))

        _goals = d.pop("goals", UNSET)
        goals: UserGoals | Unset
        if isinstance(_goals, Unset):
            goals = UNSET
        else:
            goals = UserGoals.from_dict(_goals)

        user = cls(
            email=email,
            name=name,
            id=id,
            organization_role=organization_role,
            organization=organization,
            created_at=created_at,
            status=status,
            role=role,
            goals=goals,
        )

        user.additional_properties = d
        return user

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
