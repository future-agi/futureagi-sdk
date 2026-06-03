from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_template_placeholders import PromptTemplatePlaceholders
    from ..models.prompt_template_variable_names import PromptTemplateVariableNames


T = TypeVar("T", bound="PromptTemplate")


@_attrs_define
class PromptTemplate:
    """
    Attributes:
        name (str):
        id (UUID | Unset):
        description (None | str | Unset):
        variable_names (PromptTemplateVariableNames | Unset):
        organization (None | Unset | UUID):
        prompt_folder (None | Unset | UUID):
        placeholders (PromptTemplatePlaceholders | Unset):
        created_by (None | Unset | UUID):
    """

    name: str
    id: UUID | Unset = UNSET
    description: None | str | Unset = UNSET
    variable_names: PromptTemplateVariableNames | Unset = UNSET
    organization: None | Unset | UUID = UNSET
    prompt_folder: None | Unset | UUID = UNSET
    placeholders: PromptTemplatePlaceholders | Unset = UNSET
    created_by: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        variable_names: dict[str, Any] | Unset = UNSET
        if not isinstance(self.variable_names, Unset):
            variable_names = self.variable_names.to_dict()

        organization: None | str | Unset
        if isinstance(self.organization, Unset):
            organization = UNSET
        elif isinstance(self.organization, UUID):
            organization = str(self.organization)
        else:
            organization = self.organization

        prompt_folder: None | str | Unset
        if isinstance(self.prompt_folder, Unset):
            prompt_folder = UNSET
        elif isinstance(self.prompt_folder, UUID):
            prompt_folder = str(self.prompt_folder)
        else:
            prompt_folder = self.prompt_folder

        placeholders: dict[str, Any] | Unset = UNSET
        if not isinstance(self.placeholders, Unset):
            placeholders = self.placeholders.to_dict()

        created_by: None | str | Unset
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        elif isinstance(self.created_by, UUID):
            created_by = str(self.created_by)
        else:
            created_by = self.created_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if description is not UNSET:
            field_dict["description"] = description
        if variable_names is not UNSET:
            field_dict["variable_names"] = variable_names
        if organization is not UNSET:
            field_dict["organization"] = organization
        if prompt_folder is not UNSET:
            field_dict["prompt_folder"] = prompt_folder
        if placeholders is not UNSET:
            field_dict["placeholders"] = placeholders
        if created_by is not UNSET:
            field_dict["created_by"] = created_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_template_placeholders import PromptTemplatePlaceholders
        from ..models.prompt_template_variable_names import PromptTemplateVariableNames

        d = dict(src_dict)
        name = d.pop("name")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _variable_names = d.pop("variable_names", UNSET)
        variable_names: PromptTemplateVariableNames | Unset
        if isinstance(_variable_names, Unset):
            variable_names = UNSET
        else:
            variable_names = PromptTemplateVariableNames.from_dict(_variable_names)

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

        def _parse_prompt_folder(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prompt_folder_type_0 = UUID(data)

                return prompt_folder_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prompt_folder = _parse_prompt_folder(d.pop("prompt_folder", UNSET))

        _placeholders = d.pop("placeholders", UNSET)
        placeholders: PromptTemplatePlaceholders | Unset
        if isinstance(_placeholders, Unset):
            placeholders = UNSET
        else:
            placeholders = PromptTemplatePlaceholders.from_dict(_placeholders)

        def _parse_created_by(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_by_type_0 = UUID(data)

                return created_by_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        prompt_template = cls(
            name=name,
            id=id,
            description=description,
            variable_names=variable_names,
            organization=organization,
            prompt_folder=prompt_folder,
            placeholders=placeholders,
            created_by=created_by,
        )

        prompt_template.additional_properties = d
        return prompt_template

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
