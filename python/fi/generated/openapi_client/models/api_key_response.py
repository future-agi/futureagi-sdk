from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key_response_masked_actual_key import (
        ApiKeyResponseMaskedActualKey,
    )


T = TypeVar("T", bound="ApiKeyResponse")


@_attrs_define
class ApiKeyResponse:
    """
    Attributes:
        provider (str):
        id (UUID | Unset):
        organization (None | Unset | UUID):
        masked_actual_key (ApiKeyResponseMaskedActualKey | Unset):
    """

    provider: str
    id: UUID | Unset = UNSET
    organization: None | Unset | UUID = UNSET
    masked_actual_key: ApiKeyResponseMaskedActualKey | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        organization: None | str | Unset
        if isinstance(self.organization, Unset):
            organization = UNSET
        elif isinstance(self.organization, UUID):
            organization = str(self.organization)
        else:
            organization = self.organization

        masked_actual_key: dict[str, Any] | Unset = UNSET
        if not isinstance(self.masked_actual_key, Unset):
            masked_actual_key = self.masked_actual_key.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if organization is not UNSET:
            field_dict["organization"] = organization
        if masked_actual_key is not UNSET:
            field_dict["masked_actual_key"] = masked_actual_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_response_masked_actual_key import (
            ApiKeyResponseMaskedActualKey,
        )

        d = dict(src_dict)
        provider = d.pop("provider")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

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

        _masked_actual_key = d.pop("masked_actual_key", UNSET)
        masked_actual_key: ApiKeyResponseMaskedActualKey | Unset
        if isinstance(_masked_actual_key, Unset):
            masked_actual_key = UNSET
        else:
            masked_actual_key = ApiKeyResponseMaskedActualKey.from_dict(
                _masked_actual_key
            )

        api_key_response = cls(
            provider=provider,
            id=id,
            organization=organization,
            masked_actual_key=masked_actual_key,
        )

        api_key_response.additional_properties = d
        return api_key_response

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
