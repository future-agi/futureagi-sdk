from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.dataset_model_type import DatasetModelType
from ..models.dataset_source import DatasetSource
from ..types import UNSET, Unset

T = TypeVar("T", bound="Dataset")


@_attrs_define
class Dataset:
    """
    Attributes:
        name (str):
        organization (UUID):
        id (UUID | Unset):
        model_type (DatasetModelType | Unset):
        source (DatasetSource | Unset):
        user (None | Unset | UUID):
    """

    name: str
    organization: UUID
    id: UUID | Unset = UNSET
    model_type: DatasetModelType | Unset = UNSET
    source: DatasetSource | Unset = UNSET
    user: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        organization = str(self.organization)

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        model_type: str | Unset = UNSET
        if not isinstance(self.model_type, Unset):
            model_type = self.model_type.value

        source: str | Unset = UNSET
        if not isinstance(self.source, Unset):
            source = self.source.value

        user: None | str | Unset
        if isinstance(self.user, Unset):
            user = UNSET
        elif isinstance(self.user, UUID):
            user = str(self.user)
        else:
            user = self.user

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "organization": organization,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if model_type is not UNSET:
            field_dict["model_type"] = model_type
        if source is not UNSET:
            field_dict["source"] = source
        if user is not UNSET:
            field_dict["user"] = user

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        organization = UUID(d.pop("organization"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _model_type = d.pop("model_type", UNSET)
        model_type: DatasetModelType | Unset
        if isinstance(_model_type, Unset):
            model_type = UNSET
        else:
            model_type = DatasetModelType(_model_type)

        _source = d.pop("source", UNSET)
        source: DatasetSource | Unset
        if isinstance(_source, Unset):
            source = UNSET
        else:
            source = DatasetSource(_source)

        def _parse_user(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                user_type_0 = UUID(data)

                return user_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        user = _parse_user(d.pop("user", UNSET))

        dataset = cls(
            name=name,
            organization=organization,
            id=id,
            model_type=model_type,
            source=source,
            user=user,
        )

        dataset.additional_properties = d
        return dataset

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
