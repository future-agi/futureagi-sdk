from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user_info_organization import UserInfoOrganization
    from ..models.user_info_two_factor_methods import UserInfoTwoFactorMethods


T = TypeVar("T", bound="UserInfoResponse")


@_attrs_define
class UserInfoResponse:
    """
    Attributes:
        id (UUID):
        email (str):
        name (None | str):
        organization_role (None | str):
        organization (UserInfoOrganization):
        created_at (datetime.datetime):
        status (str):
        role (None | str):
        remember_me (bool):
        get_started_completed (bool):
        onboarding_completed (bool):
        ws_enabled (bool):
        default_workspace_id (None | UUID):
        default_workspace_name (None | str):
        default_workspace_display_name (None | str):
        default_workspace_role (None | str):
        org_level (int | None):
        ws_level (int | None):
        effective_level (int | None):
        goals (list[str] | Unset):
        requires_org_setup (bool | Unset):
        has_2fa_enabled (bool | Unset):
        two_factor_methods (UserInfoTwoFactorMethods | Unset):
        org_2fa_required (bool | Unset):
        org_2fa_grace_ends_at (datetime.datetime | Unset):
    """

    id: UUID
    email: str
    name: None | str
    organization_role: None | str
    organization: UserInfoOrganization
    created_at: datetime.datetime
    status: str
    role: None | str
    remember_me: bool
    get_started_completed: bool
    onboarding_completed: bool
    ws_enabled: bool
    default_workspace_id: None | UUID
    default_workspace_name: None | str
    default_workspace_display_name: None | str
    default_workspace_role: None | str
    org_level: int | None
    ws_level: int | None
    effective_level: int | None
    goals: list[str] | Unset = UNSET
    requires_org_setup: bool | Unset = UNSET
    has_2fa_enabled: bool | Unset = UNSET
    two_factor_methods: UserInfoTwoFactorMethods | Unset = UNSET
    org_2fa_required: bool | Unset = UNSET
    org_2fa_grace_ends_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        email = self.email

        name: None | str
        name = self.name

        organization_role: None | str
        organization_role = self.organization_role

        organization = self.organization.to_dict()

        created_at = self.created_at.isoformat()

        status = self.status

        role: None | str
        role = self.role

        remember_me = self.remember_me

        get_started_completed = self.get_started_completed

        onboarding_completed = self.onboarding_completed

        ws_enabled = self.ws_enabled

        default_workspace_id: None | str
        if isinstance(self.default_workspace_id, UUID):
            default_workspace_id = str(self.default_workspace_id)
        else:
            default_workspace_id = self.default_workspace_id

        default_workspace_name: None | str
        default_workspace_name = self.default_workspace_name

        default_workspace_display_name: None | str
        default_workspace_display_name = self.default_workspace_display_name

        default_workspace_role: None | str
        default_workspace_role = self.default_workspace_role

        org_level: int | None
        org_level = self.org_level

        ws_level: int | None
        ws_level = self.ws_level

        effective_level: int | None
        effective_level = self.effective_level

        goals: list[str] | Unset = UNSET
        if not isinstance(self.goals, Unset):
            goals = self.goals

        requires_org_setup = self.requires_org_setup

        has_2fa_enabled = self.has_2fa_enabled

        two_factor_methods: dict[str, Any] | Unset = UNSET
        if not isinstance(self.two_factor_methods, Unset):
            two_factor_methods = self.two_factor_methods.to_dict()

        org_2fa_required = self.org_2fa_required

        org_2fa_grace_ends_at: str | Unset = UNSET
        if not isinstance(self.org_2fa_grace_ends_at, Unset):
            org_2fa_grace_ends_at = self.org_2fa_grace_ends_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "email": email,
                "name": name,
                "organization_role": organization_role,
                "organization": organization,
                "created_at": created_at,
                "status": status,
                "role": role,
                "remember_me": remember_me,
                "get_started_completed": get_started_completed,
                "onboarding_completed": onboarding_completed,
                "ws_enabled": ws_enabled,
                "default_workspace_id": default_workspace_id,
                "default_workspace_name": default_workspace_name,
                "default_workspace_display_name": default_workspace_display_name,
                "default_workspace_role": default_workspace_role,
                "org_level": org_level,
                "ws_level": ws_level,
                "effective_level": effective_level,
            }
        )
        if goals is not UNSET:
            field_dict["goals"] = goals
        if requires_org_setup is not UNSET:
            field_dict["requires_org_setup"] = requires_org_setup
        if has_2fa_enabled is not UNSET:
            field_dict["has_2fa_enabled"] = has_2fa_enabled
        if two_factor_methods is not UNSET:
            field_dict["two_factor_methods"] = two_factor_methods
        if org_2fa_required is not UNSET:
            field_dict["org_2fa_required"] = org_2fa_required
        if org_2fa_grace_ends_at is not UNSET:
            field_dict["org_2fa_grace_ends_at"] = org_2fa_grace_ends_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_info_organization import UserInfoOrganization
        from ..models.user_info_two_factor_methods import UserInfoTwoFactorMethods

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        email = d.pop("email")

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        def _parse_organization_role(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        organization_role = _parse_organization_role(d.pop("organization_role"))

        organization = UserInfoOrganization.from_dict(d.pop("organization"))

        created_at = isoparse(d.pop("created_at"))

        status = d.pop("status")

        def _parse_role(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        role = _parse_role(d.pop("role"))

        remember_me = d.pop("remember_me")

        get_started_completed = d.pop("get_started_completed")

        onboarding_completed = d.pop("onboarding_completed")

        ws_enabled = d.pop("ws_enabled")

        def _parse_default_workspace_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                default_workspace_id_type_0 = UUID(data)

                return default_workspace_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        default_workspace_id = _parse_default_workspace_id(
            d.pop("default_workspace_id")
        )

        def _parse_default_workspace_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        default_workspace_name = _parse_default_workspace_name(
            d.pop("default_workspace_name")
        )

        def _parse_default_workspace_display_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        default_workspace_display_name = _parse_default_workspace_display_name(
            d.pop("default_workspace_display_name")
        )

        def _parse_default_workspace_role(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        default_workspace_role = _parse_default_workspace_role(
            d.pop("default_workspace_role")
        )

        def _parse_org_level(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        org_level = _parse_org_level(d.pop("org_level"))

        def _parse_ws_level(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        ws_level = _parse_ws_level(d.pop("ws_level"))

        def _parse_effective_level(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        effective_level = _parse_effective_level(d.pop("effective_level"))

        goals = cast(list[str], d.pop("goals", UNSET))

        requires_org_setup = d.pop("requires_org_setup", UNSET)

        has_2fa_enabled = d.pop("has_2fa_enabled", UNSET)

        _two_factor_methods = d.pop("two_factor_methods", UNSET)
        two_factor_methods: UserInfoTwoFactorMethods | Unset
        if isinstance(_two_factor_methods, Unset):
            two_factor_methods = UNSET
        else:
            two_factor_methods = UserInfoTwoFactorMethods.from_dict(_two_factor_methods)

        org_2fa_required = d.pop("org_2fa_required", UNSET)

        _org_2fa_grace_ends_at = d.pop("org_2fa_grace_ends_at", UNSET)
        org_2fa_grace_ends_at: datetime.datetime | Unset
        if isinstance(_org_2fa_grace_ends_at, Unset):
            org_2fa_grace_ends_at = UNSET
        else:
            org_2fa_grace_ends_at = isoparse(_org_2fa_grace_ends_at)

        user_info_response = cls(
            id=id,
            email=email,
            name=name,
            organization_role=organization_role,
            organization=organization,
            created_at=created_at,
            status=status,
            role=role,
            remember_me=remember_me,
            get_started_completed=get_started_completed,
            onboarding_completed=onboarding_completed,
            ws_enabled=ws_enabled,
            default_workspace_id=default_workspace_id,
            default_workspace_name=default_workspace_name,
            default_workspace_display_name=default_workspace_display_name,
            default_workspace_role=default_workspace_role,
            org_level=org_level,
            ws_level=ws_level,
            effective_level=effective_level,
            goals=goals,
            requires_org_setup=requires_org_setup,
            has_2fa_enabled=has_2fa_enabled,
            two_factor_methods=two_factor_methods,
            org_2fa_required=org_2fa_required,
            org_2fa_grace_ends_at=org_2fa_grace_ends_at,
        )

        user_info_response.additional_properties = d
        return user_info_response

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
