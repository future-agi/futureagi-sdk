from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Organization")


@_attrs_define
class Organization:
    """
    Attributes:
        name (str):
        id (UUID | Unset):
        created_at (datetime.datetime | Unset):
        display_name (str | Unset):
        is_new (bool | Unset):
        ws_enabled (bool | Unset):
        region (str | Unset):
        require_2fa (bool | Unset):
        require_2fa_grace_period_days (int | Unset):
        require_2fa_enforced_at (datetime.datetime | None | Unset):
    """

    name: str
    id: UUID | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    display_name: str | Unset = UNSET
    is_new: bool | Unset = UNSET
    ws_enabled: bool | Unset = UNSET
    region: str | Unset = UNSET
    require_2fa: bool | Unset = UNSET
    require_2fa_grace_period_days: int | Unset = UNSET
    require_2fa_enforced_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        display_name = self.display_name

        is_new = self.is_new

        ws_enabled = self.ws_enabled

        region = self.region

        require_2fa = self.require_2fa

        require_2fa_grace_period_days = self.require_2fa_grace_period_days

        require_2fa_enforced_at: None | str | Unset
        if isinstance(self.require_2fa_enforced_at, Unset):
            require_2fa_enforced_at = UNSET
        elif isinstance(self.require_2fa_enforced_at, datetime.datetime):
            require_2fa_enforced_at = self.require_2fa_enforced_at.isoformat()
        else:
            require_2fa_enforced_at = self.require_2fa_enforced_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if display_name is not UNSET:
            field_dict["display_name"] = display_name
        if is_new is not UNSET:
            field_dict["is_new"] = is_new
        if ws_enabled is not UNSET:
            field_dict["ws_enabled"] = ws_enabled
        if region is not UNSET:
            field_dict["region"] = region
        if require_2fa is not UNSET:
            field_dict["require_2fa"] = require_2fa
        if require_2fa_grace_period_days is not UNSET:
            field_dict["require_2fa_grace_period_days"] = require_2fa_grace_period_days
        if require_2fa_enforced_at is not UNSET:
            field_dict["require_2fa_enforced_at"] = require_2fa_enforced_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        display_name = d.pop("display_name", UNSET)

        is_new = d.pop("is_new", UNSET)

        ws_enabled = d.pop("ws_enabled", UNSET)

        region = d.pop("region", UNSET)

        require_2fa = d.pop("require_2fa", UNSET)

        require_2fa_grace_period_days = d.pop("require_2fa_grace_period_days", UNSET)

        def _parse_require_2fa_enforced_at(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                require_2fa_enforced_at_type_0 = isoparse(data)

                return require_2fa_enforced_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        require_2fa_enforced_at = _parse_require_2fa_enforced_at(
            d.pop("require_2fa_enforced_at", UNSET)
        )

        organization = cls(
            name=name,
            id=id,
            created_at=created_at,
            display_name=display_name,
            is_new=is_new,
            ws_enabled=ws_enabled,
            region=region,
            require_2fa=require_2fa,
            require_2fa_grace_period_days=require_2fa_grace_period_days,
            require_2fa_enforced_at=require_2fa_enforced_at,
        )

        organization.additional_properties = d
        return organization

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
