from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_config_entry_configuration import (
        PromptConfigEntryConfiguration,
    )
    from ..models.prompt_config_entry_messages_item import PromptConfigEntryMessagesItem
    from ..models.prompt_config_entry_model import PromptConfigEntryModel
    from ..models.prompt_config_entry_model_params import PromptConfigEntryModelParams


T = TypeVar("T", bound="PromptConfigEntry")


@_attrs_define
class PromptConfigEntry:
    """
    Attributes:
        id (None | Unset | UUID):
        name (str | Unset):
        prompt_id (None | Unset | UUID):
        prompt_version (None | Unset | UUID):
        agent_id (None | Unset | UUID):
        agent_version (None | Unset | UUID):
        model (PromptConfigEntryModel | Unset):
        model_params (PromptConfigEntryModelParams | Unset):
        configuration (PromptConfigEntryConfiguration | Unset):
        output_format (str | Unset):  Default: 'string'.
        messages (list[PromptConfigEntryMessagesItem] | Unset):
        voice_input_column_id (None | Unset | UUID):
    """

    id: None | Unset | UUID = UNSET
    name: str | Unset = UNSET
    prompt_id: None | Unset | UUID = UNSET
    prompt_version: None | Unset | UUID = UNSET
    agent_id: None | Unset | UUID = UNSET
    agent_version: None | Unset | UUID = UNSET
    model: PromptConfigEntryModel | Unset = UNSET
    model_params: PromptConfigEntryModelParams | Unset = UNSET
    configuration: PromptConfigEntryConfiguration | Unset = UNSET
    output_format: str | Unset = "string"
    messages: list[PromptConfigEntryMessagesItem] | Unset = UNSET
    voice_input_column_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, UUID):
            id = str(self.id)
        else:
            id = self.id

        name = self.name

        prompt_id: None | str | Unset
        if isinstance(self.prompt_id, Unset):
            prompt_id = UNSET
        elif isinstance(self.prompt_id, UUID):
            prompt_id = str(self.prompt_id)
        else:
            prompt_id = self.prompt_id

        prompt_version: None | str | Unset
        if isinstance(self.prompt_version, Unset):
            prompt_version = UNSET
        elif isinstance(self.prompt_version, UUID):
            prompt_version = str(self.prompt_version)
        else:
            prompt_version = self.prompt_version

        agent_id: None | str | Unset
        if isinstance(self.agent_id, Unset):
            agent_id = UNSET
        elif isinstance(self.agent_id, UUID):
            agent_id = str(self.agent_id)
        else:
            agent_id = self.agent_id

        agent_version: None | str | Unset
        if isinstance(self.agent_version, Unset):
            agent_version = UNSET
        elif isinstance(self.agent_version, UUID):
            agent_version = str(self.agent_version)
        else:
            agent_version = self.agent_version

        model: dict[str, Any] | Unset = UNSET
        if not isinstance(self.model, Unset):
            model = self.model.to_dict()

        model_params: dict[str, Any] | Unset = UNSET
        if not isinstance(self.model_params, Unset):
            model_params = self.model_params.to_dict()

        configuration: dict[str, Any] | Unset = UNSET
        if not isinstance(self.configuration, Unset):
            configuration = self.configuration.to_dict()

        output_format = self.output_format

        messages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.messages, Unset):
            messages = []
            for messages_item_data in self.messages:
                messages_item = messages_item_data.to_dict()
                messages.append(messages_item)

        voice_input_column_id: None | str | Unset
        if isinstance(self.voice_input_column_id, Unset):
            voice_input_column_id = UNSET
        elif isinstance(self.voice_input_column_id, UUID):
            voice_input_column_id = str(self.voice_input_column_id)
        else:
            voice_input_column_id = self.voice_input_column_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if prompt_id is not UNSET:
            field_dict["prompt_id"] = prompt_id
        if prompt_version is not UNSET:
            field_dict["prompt_version"] = prompt_version
        if agent_id is not UNSET:
            field_dict["agent_id"] = agent_id
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version
        if model is not UNSET:
            field_dict["model"] = model
        if model_params is not UNSET:
            field_dict["model_params"] = model_params
        if configuration is not UNSET:
            field_dict["configuration"] = configuration
        if output_format is not UNSET:
            field_dict["output_format"] = output_format
        if messages is not UNSET:
            field_dict["messages"] = messages
        if voice_input_column_id is not UNSET:
            field_dict["voice_input_column_id"] = voice_input_column_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_config_entry_configuration import (
            PromptConfigEntryConfiguration,
        )
        from ..models.prompt_config_entry_messages_item import (
            PromptConfigEntryMessagesItem,
        )
        from ..models.prompt_config_entry_model import PromptConfigEntryModel
        from ..models.prompt_config_entry_model_params import (
            PromptConfigEntryModelParams,
        )

        d = dict(src_dict)

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

        name = d.pop("name", UNSET)

        def _parse_prompt_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prompt_id_type_0 = UUID(data)

                return prompt_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prompt_id = _parse_prompt_id(d.pop("prompt_id", UNSET))

        def _parse_prompt_version(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prompt_version_type_0 = UUID(data)

                return prompt_version_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prompt_version = _parse_prompt_version(d.pop("prompt_version", UNSET))

        def _parse_agent_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                agent_id_type_0 = UUID(data)

                return agent_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        agent_id = _parse_agent_id(d.pop("agent_id", UNSET))

        def _parse_agent_version(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                agent_version_type_0 = UUID(data)

                return agent_version_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        agent_version = _parse_agent_version(d.pop("agent_version", UNSET))

        _model = d.pop("model", UNSET)
        model: PromptConfigEntryModel | Unset
        if isinstance(_model, Unset):
            model = UNSET
        else:
            model = PromptConfigEntryModel.from_dict(_model)

        _model_params = d.pop("model_params", UNSET)
        model_params: PromptConfigEntryModelParams | Unset
        if isinstance(_model_params, Unset):
            model_params = UNSET
        else:
            model_params = PromptConfigEntryModelParams.from_dict(_model_params)

        _configuration = d.pop("configuration", UNSET)
        configuration: PromptConfigEntryConfiguration | Unset
        if isinstance(_configuration, Unset):
            configuration = UNSET
        else:
            configuration = PromptConfigEntryConfiguration.from_dict(_configuration)

        output_format = d.pop("output_format", UNSET)

        _messages = d.pop("messages", UNSET)
        messages: list[PromptConfigEntryMessagesItem] | Unset = UNSET
        if _messages is not UNSET:
            messages = []
            for messages_item_data in _messages:
                messages_item = PromptConfigEntryMessagesItem.from_dict(
                    messages_item_data
                )

                messages.append(messages_item)

        def _parse_voice_input_column_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                voice_input_column_id_type_0 = UUID(data)

                return voice_input_column_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        voice_input_column_id = _parse_voice_input_column_id(
            d.pop("voice_input_column_id", UNSET)
        )

        prompt_config_entry = cls(
            id=id,
            name=name,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            agent_id=agent_id,
            agent_version=agent_version,
            model=model,
            model_params=model_params,
            configuration=configuration,
            output_format=output_format,
            messages=messages,
            voice_input_column_id=voice_input_column_id,
        )

        prompt_config_entry.additional_properties = d
        return prompt_config_entry

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
