from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProviderStatusItem")


@_attrs_define
class ProviderStatusItem:
    """
    Attributes:
        provider (str):
        display_name (str):
        has_key (bool):
        type_ (str):
        masked_key (None | str | Unset):
        logo_url (None | str | Unset):
        id (None | Unset | UUID):
    """

    provider: str
    display_name: str
    has_key: bool
    type_: str
    masked_key: None | str | Unset = UNSET
    logo_url: None | str | Unset = UNSET
    id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        display_name = self.display_name

        has_key = self.has_key

        type_ = self.type_

        masked_key: None | str | Unset
        if isinstance(self.masked_key, Unset):
            masked_key = UNSET
        else:
            masked_key = self.masked_key

        logo_url: None | str | Unset
        if isinstance(self.logo_url, Unset):
            logo_url = UNSET
        else:
            logo_url = self.logo_url

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, UUID):
            id = str(self.id)
        else:
            id = self.id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
                "display_name": display_name,
                "has_key": has_key,
                "type": type_,
            }
        )
        if masked_key is not UNSET:
            field_dict["masked_key"] = masked_key
        if logo_url is not UNSET:
            field_dict["logo_url"] = logo_url
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        provider = d.pop("provider")

        display_name = d.pop("display_name")

        has_key = d.pop("has_key")

        type_ = d.pop("type")

        def _parse_masked_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        masked_key = _parse_masked_key(d.pop("masked_key", UNSET))

        def _parse_logo_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        logo_url = _parse_logo_url(d.pop("logo_url", UNSET))

        def _parse_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                id_type_0 = UUID(data)

                return id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        id = _parse_id(d.pop("id", UNSET))

        provider_status_item = cls(
            provider=provider,
            display_name=display_name,
            has_key=has_key,
            type_=type_,
            masked_key=masked_key,
            logo_url=logo_url,
            id=id,
        )

        provider_status_item.additional_properties = d
        return provider_status_item

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
