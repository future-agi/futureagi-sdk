from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key_config_json import ApiKeyConfigJson


T = TypeVar("T", bound="ApiKey")


@_attrs_define
class ApiKey:
    """
    Attributes:
        provider (str):
        id (UUID | Unset):
        key (None | str | Unset):
        organization (None | Unset | UUID):
        masked_actual_key (str | Unset):
        config_json (ApiKeyConfigJson | Unset):
    """

    provider: str
    id: UUID | Unset = UNSET
    key: None | str | Unset = UNSET
    organization: None | Unset | UUID = UNSET
    masked_actual_key: str | Unset = UNSET
    config_json: ApiKeyConfigJson | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        key: None | str | Unset
        if isinstance(self.key, Unset):
            key = UNSET
        else:
            key = self.key

        organization: None | str | Unset
        if isinstance(self.organization, Unset):
            organization = UNSET
        elif isinstance(self.organization, UUID):
            organization = str(self.organization)
        else:
            organization = self.organization

        masked_actual_key = self.masked_actual_key

        config_json: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config_json, Unset):
            config_json = self.config_json.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if key is not UNSET:
            field_dict["key"] = key
        if organization is not UNSET:
            field_dict["organization"] = organization
        if masked_actual_key is not UNSET:
            field_dict["masked_actual_key"] = masked_actual_key
        if config_json is not UNSET:
            field_dict["config_json"] = config_json

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_config_json import ApiKeyConfigJson

        d = dict(src_dict)
        provider = d.pop("provider")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        def _parse_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        key = _parse_key(d.pop("key", UNSET))

        def _parse_organization(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                organization_type_0 = UUID(data)

                return organization_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        organization = _parse_organization(d.pop("organization", UNSET))

        masked_actual_key = d.pop("masked_actual_key", UNSET)

        _config_json = d.pop("config_json", UNSET)
        config_json: ApiKeyConfigJson | Unset
        if isinstance(_config_json, Unset):
            config_json = UNSET
        else:
            config_json = ApiKeyConfigJson.from_dict(_config_json)

        api_key = cls(
            provider=provider,
            id=id,
            key=key,
            organization=organization,
            masked_actual_key=masked_actual_key,
            config_json=config_json,
        )

        api_key.additional_properties = d
        return api_key

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
