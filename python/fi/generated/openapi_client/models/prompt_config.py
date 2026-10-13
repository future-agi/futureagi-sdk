from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.prompt_config_output_format import PromptConfigOutputFormat
from ..models.prompt_config_tool_choice import PromptConfigToolChoice
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_config_messages_item import PromptConfigMessagesItem
    from ..models.prompt_config_response_format import PromptConfigResponseFormat
    from ..models.prompt_config_run_prompt_config import PromptConfigRunPromptConfig
    from ..models.prompt_config_tools_type_0_item import PromptConfigToolsType0Item


T = TypeVar("T", bound="PromptConfig")


@_attrs_define
class PromptConfig:
    """
    Attributes:
        model (str | Unset):
        run_prompt_config (PromptConfigRunPromptConfig | Unset):
        messages (list[PromptConfigMessagesItem] | Unset): List of messages with format [{'role': 'user/assistant',
            'content': 'text'}]
        temperature (float | None | Unset): Controls the randomness. Value between 0 and 2.
        frequency_penalty (float | None | Unset): Penalty for word repetition. Value between -2 and 2.
        presence_penalty (float | None | Unset): Penalty for new word usage. Value between -2 and 2.
        max_tokens (int | None | Unset): Maximum number of tokens to generate. Null = use provider default.
        top_p (float | None | Unset): Controls diversity via nucleus sampling. Value between 0 and 1.
        response_format (PromptConfigResponseFormat | Unset): JSON schema for response format if required. Can be a JSON
            object or string. Defaults to None.
        tool_choice (None | PromptConfigToolChoice | Unset): Tool selection mode: 'auto' or 'required'.
        tools (list[PromptConfigToolsType0Item] | None | Unset): List of tools with tool properties if available.
        output_format (PromptConfigOutputFormat | Unset): Output format type.
        concurrency (int | None | Unset): Number of concurrent operations allowed. Maximum 10.
    """

    model: str | Unset = UNSET
    run_prompt_config: PromptConfigRunPromptConfig | Unset = UNSET
    messages: list[PromptConfigMessagesItem] | Unset = UNSET
    temperature: float | None | Unset = UNSET
    frequency_penalty: float | None | Unset = UNSET
    presence_penalty: float | None | Unset = UNSET
    max_tokens: int | None | Unset = UNSET
    top_p: float | None | Unset = UNSET
    response_format: PromptConfigResponseFormat | Unset = UNSET
    tool_choice: None | PromptConfigToolChoice | Unset = UNSET
    tools: list[PromptConfigToolsType0Item] | None | Unset = UNSET
    output_format: PromptConfigOutputFormat | Unset = UNSET
    concurrency: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model = self.model

        run_prompt_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.run_prompt_config, Unset):
            run_prompt_config = self.run_prompt_config.to_dict()

        messages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.messages, Unset):
            messages = []
            for messages_item_data in self.messages:
                messages_item = messages_item_data.to_dict()
                messages.append(messages_item)

        temperature: float | None | Unset
        if isinstance(self.temperature, Unset):
            temperature = UNSET
        else:
            temperature = self.temperature

        frequency_penalty: float | None | Unset
        if isinstance(self.frequency_penalty, Unset):
            frequency_penalty = UNSET
        else:
            frequency_penalty = self.frequency_penalty

        presence_penalty: float | None | Unset
        if isinstance(self.presence_penalty, Unset):
            presence_penalty = UNSET
        else:
            presence_penalty = self.presence_penalty

        max_tokens: int | None | Unset
        if isinstance(self.max_tokens, Unset):
            max_tokens = UNSET
        else:
            max_tokens = self.max_tokens

        top_p: float | None | Unset
        if isinstance(self.top_p, Unset):
            top_p = UNSET
        else:
            top_p = self.top_p

        response_format: dict[str, Any] | Unset = UNSET
        if not isinstance(self.response_format, Unset):
            response_format = self.response_format.to_dict()

        tool_choice: None | str | Unset
        if isinstance(self.tool_choice, Unset):
            tool_choice = UNSET
        elif isinstance(self.tool_choice, PromptConfigToolChoice):
            tool_choice = self.tool_choice.value
        else:
            tool_choice = self.tool_choice

        tools: list[dict[str, Any]] | None | Unset
        if isinstance(self.tools, Unset):
            tools = UNSET
        elif isinstance(self.tools, list):
            tools = []
            for tools_type_0_item_data in self.tools:
                tools_type_0_item = tools_type_0_item_data.to_dict()
                tools.append(tools_type_0_item)

        else:
            tools = self.tools

        output_format: str | Unset = UNSET
        if not isinstance(self.output_format, Unset):
            output_format = self.output_format.value

        concurrency: int | None | Unset
        if isinstance(self.concurrency, Unset):
            concurrency = UNSET
        else:
            concurrency = self.concurrency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if model is not UNSET:
            field_dict["model"] = model
        if run_prompt_config is not UNSET:
            field_dict["run_prompt_config"] = run_prompt_config
        if messages is not UNSET:
            field_dict["messages"] = messages
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if frequency_penalty is not UNSET:
            field_dict["frequency_penalty"] = frequency_penalty
        if presence_penalty is not UNSET:
            field_dict["presence_penalty"] = presence_penalty
        if max_tokens is not UNSET:
            field_dict["max_tokens"] = max_tokens
        if top_p is not UNSET:
            field_dict["top_p"] = top_p
        if response_format is not UNSET:
            field_dict["response_format"] = response_format
        if tool_choice is not UNSET:
            field_dict["tool_choice"] = tool_choice
        if tools is not UNSET:
            field_dict["tools"] = tools
        if output_format is not UNSET:
            field_dict["output_format"] = output_format
        if concurrency is not UNSET:
            field_dict["concurrency"] = concurrency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_config_messages_item import PromptConfigMessagesItem
        from ..models.prompt_config_response_format import PromptConfigResponseFormat
        from ..models.prompt_config_run_prompt_config import PromptConfigRunPromptConfig
        from ..models.prompt_config_tools_type_0_item import PromptConfigToolsType0Item

        d = dict(src_dict)
        model = d.pop("model", UNSET)

        _run_prompt_config = d.pop("run_prompt_config", UNSET)
        run_prompt_config: PromptConfigRunPromptConfig | Unset
        if isinstance(_run_prompt_config, Unset):
            run_prompt_config = UNSET
        else:
            run_prompt_config = PromptConfigRunPromptConfig.from_dict(
                _run_prompt_config
            )

        _messages = d.pop("messages", UNSET)
        messages: list[PromptConfigMessagesItem] | Unset = UNSET
        if _messages is not UNSET:
            messages = []
            for messages_item_data in _messages:
                messages_item = PromptConfigMessagesItem.from_dict(messages_item_data)

                messages.append(messages_item)

        def _parse_temperature(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        temperature = _parse_temperature(d.pop("temperature", UNSET))

        def _parse_frequency_penalty(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        frequency_penalty = _parse_frequency_penalty(d.pop("frequency_penalty", UNSET))

        def _parse_presence_penalty(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        presence_penalty = _parse_presence_penalty(d.pop("presence_penalty", UNSET))

        def _parse_max_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        max_tokens = _parse_max_tokens(d.pop("max_tokens", UNSET))

        def _parse_top_p(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        top_p = _parse_top_p(d.pop("top_p", UNSET))

        _response_format = d.pop("response_format", UNSET)
        response_format: PromptConfigResponseFormat | Unset
        if isinstance(_response_format, Unset):
            response_format = UNSET
        else:
            response_format = PromptConfigResponseFormat.from_dict(_response_format)

        def _parse_tool_choice(data: object) -> None | PromptConfigToolChoice | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                tool_choice_type_1 = PromptConfigToolChoice(data)

                return tool_choice_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PromptConfigToolChoice | Unset, data)

        tool_choice = _parse_tool_choice(d.pop("tool_choice", UNSET))

        def _parse_tools(
            data: object,
        ) -> list[PromptConfigToolsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tools_type_0 = []
                _tools_type_0 = data
                for tools_type_0_item_data in _tools_type_0:
                    tools_type_0_item = PromptConfigToolsType0Item.from_dict(
                        tools_type_0_item_data
                    )

                    tools_type_0.append(tools_type_0_item)

                return tools_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[PromptConfigToolsType0Item] | None | Unset, data)

        tools = _parse_tools(d.pop("tools", UNSET))

        _output_format = d.pop("output_format", UNSET)
        output_format: PromptConfigOutputFormat | Unset
        if isinstance(_output_format, Unset):
            output_format = UNSET
        else:
            output_format = PromptConfigOutputFormat(_output_format)

        def _parse_concurrency(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        concurrency = _parse_concurrency(d.pop("concurrency", UNSET))

        prompt_config = cls(
            model=model,
            run_prompt_config=run_prompt_config,
            messages=messages,
            temperature=temperature,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            max_tokens=max_tokens,
            top_p=top_p,
            response_format=response_format,
            tool_choice=tool_choice,
            tools=tools,
            output_format=output_format,
            concurrency=concurrency,
        )

        prompt_config.additional_properties = d
        return prompt_config

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
