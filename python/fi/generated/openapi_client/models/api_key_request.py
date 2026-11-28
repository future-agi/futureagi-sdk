from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key_request_config_json import ApiKeyRequestConfigJson


T = TypeVar("T", bound="ApiKeyRequest")


@_attrs_define
class ApiKeyRequest:
    """
    Attributes:
        provider (str):
        key (None | str | Unset):
        config_json (ApiKeyRequestConfigJson | Unset):
    """

    provider: str
    key: None | str | Unset = UNSET
    config_json: ApiKeyRequestConfigJson | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        key: None | str | Unset
        if isinstance(self.key, Unset):
            key = UNSET
        else:
            key = self.key

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
        if key is not UNSET:
            field_dict["key"] = key
        if config_json is not UNSET:
            field_dict["config_json"] = config_json

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_request_config_json import ApiKeyRequestConfigJson

        d = dict(src_dict)
        provider = d.pop("provider")

        def _parse_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        key = _parse_key(d.pop("key", UNSET))

        _config_json = d.pop("config_json", UNSET)
        config_json: ApiKeyRequestConfigJson | Unset
        if isinstance(_config_json, Unset):
            config_json = UNSET
        else:
            config_json = ApiKeyRequestConfigJson.from_dict(_config_json)

        api_key_request = cls(
            provider=provider,
            key=key,
            config_json=config_json,
        )

        api_key_request.additional_properties = d
        return api_key_request

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
