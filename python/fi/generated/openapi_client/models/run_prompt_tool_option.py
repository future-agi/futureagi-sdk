from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_prompt_tool_option_config import RunPromptToolOptionConfig


T = TypeVar("T", bound="RunPromptToolOption")


@_attrs_define
class RunPromptToolOption:
    """
    Attributes:
        id (str):
        name (str):
        yaml_config (None | str | Unset):
        config (RunPromptToolOptionConfig | Unset):
        config_type (None | str | Unset):
        description (None | str | Unset):
    """

    id: str
    name: str
    yaml_config: None | str | Unset = UNSET
    config: RunPromptToolOptionConfig | Unset = UNSET
    config_type: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        yaml_config: None | str | Unset
        if isinstance(self.yaml_config, Unset):
            yaml_config = UNSET
        else:
            yaml_config = self.yaml_config

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        config_type: None | str | Unset
        if isinstance(self.config_type, Unset):
            config_type = UNSET
        else:
            config_type = self.config_type

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if yaml_config is not UNSET:
            field_dict["yaml_config"] = yaml_config
        if config is not UNSET:
            field_dict["config"] = config
        if config_type is not UNSET:
            field_dict["config_type"] = config_type
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_prompt_tool_option_config import RunPromptToolOptionConfig

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        def _parse_yaml_config(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        yaml_config = _parse_yaml_config(d.pop("yaml_config", UNSET))

        _config = d.pop("config", UNSET)
        config: RunPromptToolOptionConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = RunPromptToolOptionConfig.from_dict(_config)

        def _parse_config_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        config_type = _parse_config_type(d.pop("config_type", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        run_prompt_tool_option = cls(
            id=id,
            name=name,
            yaml_config=yaml_config,
            config=config,
            config_type=config_type,
            description=description,
        )

        run_prompt_tool_option.additional_properties = d
        return run_prompt_tool_option

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
