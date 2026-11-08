from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_run_model_configuration_model import (
        PromptRunModelConfigurationModel,
    )
    from ..models.prompt_run_model_configuration_model_detail_type_4_type_0 import (
        PromptRunModelConfigurationModelDetailType4Type0,
    )
    from ..models.prompt_run_model_configuration_response_format import (
        PromptRunModelConfigurationResponseFormat,
    )
    from ..models.prompt_run_model_configuration_tools_type_0_item_type_4_type_0 import (
        PromptRunModelConfigurationToolsType0ItemType4Type0,
    )


T = TypeVar("T", bound="PromptRunModelConfiguration")


@_attrs_define
class PromptRunModelConfiguration:
    """
    Attributes:
        tool_choice (None | str | Unset):
        template_format (None | str | Unset):
        tools (list[bool | float | list[Any] | None | PromptRunModelConfigurationToolsType0ItemType4Type0 | str] | None
            | Unset):
        output_format (None | str | Unset):
        model_type (None | str | Unset):
        model_detail (bool | float | list[Any] | None | PromptRunModelConfigurationModelDetailType4Type0 | str | Unset):
            Any valid JSON value.
        voice_id (None | str | Unset):
        temperature (float | None | Unset):
        max_tokens (int | None | Unset):
        top_p (float | None | Unset):
        frequency_penalty (float | None | Unset):
        presence_penalty (float | None | Unset):
        response_format (PromptRunModelConfigurationResponseFormat | Unset): String or JSON object.
        model (PromptRunModelConfigurationModel | Unset): String or JSON object.
    """

    tool_choice: None | str | Unset = UNSET
    template_format: None | str | Unset = UNSET
    tools: (
        list[
            bool
            | float
            | list[Any]
            | None
            | PromptRunModelConfigurationToolsType0ItemType4Type0
            | str
        ]
        | None
        | Unset
    ) = UNSET
    output_format: None | str | Unset = UNSET
    model_type: None | str | Unset = UNSET
    model_detail: (
        bool
        | float
        | list[Any]
        | None
        | PromptRunModelConfigurationModelDetailType4Type0
        | str
        | Unset
    ) = UNSET
    voice_id: None | str | Unset = UNSET
    temperature: float | None | Unset = UNSET
    max_tokens: int | None | Unset = UNSET
    top_p: float | None | Unset = UNSET
    frequency_penalty: float | None | Unset = UNSET
    presence_penalty: float | None | Unset = UNSET
    response_format: PromptRunModelConfigurationResponseFormat | Unset = UNSET
    model: PromptRunModelConfigurationModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.prompt_run_model_configuration_model_detail_type_4_type_0 import (
            PromptRunModelConfigurationModelDetailType4Type0,
        )
        from ..models.prompt_run_model_configuration_tools_type_0_item_type_4_type_0 import (
            PromptRunModelConfigurationToolsType0ItemType4Type0,
        )

        tool_choice: None | str | Unset
        if isinstance(self.tool_choice, Unset):
            tool_choice = UNSET
        else:
            tool_choice = self.tool_choice

        template_format: None | str | Unset
        if isinstance(self.template_format, Unset):
            template_format = UNSET
        else:
            template_format = self.template_format

        tools: (
            list[bool | dict[str, Any] | float | list[Any] | None | str] | None | Unset
        )
        if isinstance(self.tools, Unset):
            tools = UNSET
        elif isinstance(self.tools, list):
            tools = []
            for tools_type_0_item_data in self.tools:
                tools_type_0_item: (
                    bool | dict[str, Any] | float | list[Any] | None | str
                )
                if isinstance(tools_type_0_item_data, list):
                    tools_type_0_item = tools_type_0_item_data

                elif isinstance(
                    tools_type_0_item_data,
                    PromptRunModelConfigurationToolsType0ItemType4Type0,
                ):
                    tools_type_0_item = tools_type_0_item_data.to_dict()
                else:
                    tools_type_0_item = tools_type_0_item_data
                tools.append(tools_type_0_item)

        else:
            tools = self.tools

        output_format: None | str | Unset
        if isinstance(self.output_format, Unset):
            output_format = UNSET
        else:
            output_format = self.output_format

        model_type: None | str | Unset
        if isinstance(self.model_type, Unset):
            model_type = UNSET
        else:
            model_type = self.model_type

        model_detail: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.model_detail, Unset):
            model_detail = UNSET
        elif isinstance(self.model_detail, list):
            model_detail = self.model_detail

        elif isinstance(
            self.model_detail, PromptRunModelConfigurationModelDetailType4Type0
        ):
            model_detail = self.model_detail.to_dict()
        else:
            model_detail = self.model_detail

        voice_id: None | str | Unset
        if isinstance(self.voice_id, Unset):
            voice_id = UNSET
        else:
            voice_id = self.voice_id

        temperature: float | None | Unset
        if isinstance(self.temperature, Unset):
            temperature = UNSET
        else:
            temperature = self.temperature

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

        response_format: dict[str, Any] | Unset = UNSET
        if not isinstance(self.response_format, Unset):
            response_format = self.response_format.to_dict()

        model: dict[str, Any] | Unset = UNSET
        if not isinstance(self.model, Unset):
            model = self.model.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if tool_choice is not UNSET:
            field_dict["tool_choice"] = tool_choice
        if template_format is not UNSET:
            field_dict["template_format"] = template_format
        if tools is not UNSET:
            field_dict["tools"] = tools
        if output_format is not UNSET:
            field_dict["output_format"] = output_format
        if model_type is not UNSET:
            field_dict["model_type"] = model_type
        if model_detail is not UNSET:
            field_dict["model_detail"] = model_detail
        if voice_id is not UNSET:
            field_dict["voice_id"] = voice_id
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if max_tokens is not UNSET:
            field_dict["max_tokens"] = max_tokens
        if top_p is not UNSET:
            field_dict["top_p"] = top_p
        if frequency_penalty is not UNSET:
            field_dict["frequency_penalty"] = frequency_penalty
        if presence_penalty is not UNSET:
            field_dict["presence_penalty"] = presence_penalty
        if response_format is not UNSET:
            field_dict["response_format"] = response_format
        if model is not UNSET:
            field_dict["model"] = model

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_run_model_configuration_model import (
            PromptRunModelConfigurationModel,
        )
        from ..models.prompt_run_model_configuration_model_detail_type_4_type_0 import (
            PromptRunModelConfigurationModelDetailType4Type0,
        )
        from ..models.prompt_run_model_configuration_response_format import (
            PromptRunModelConfigurationResponseFormat,
        )
        from ..models.prompt_run_model_configuration_tools_type_0_item_type_4_type_0 import (
            PromptRunModelConfigurationToolsType0ItemType4Type0,
        )

        d = dict(src_dict)

        def _parse_tool_choice(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tool_choice = _parse_tool_choice(d.pop("tool_choice", UNSET))

        def _parse_template_format(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        template_format = _parse_template_format(d.pop("template_format", UNSET))

        def _parse_tools(
            data: object,
        ) -> (
            list[
                bool
                | float
                | list[Any]
                | None
                | PromptRunModelConfigurationToolsType0ItemType4Type0
                | str
            ]
            | None
            | Unset
        ):
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

                    def _parse_tools_type_0_item(
                        data: object,
                    ) -> (
                        bool
                        | float
                        | list[Any]
                        | None
                        | PromptRunModelConfigurationToolsType0ItemType4Type0
                        | str
                    ):
                        if data is None:
                            return data
                        try:
                            if not isinstance(data, list):
                                raise TypeError()
                            tools_type_0_item_type_3 = cast(list[Any], data)

                            return tools_type_0_item_type_3
                        except (TypeError, ValueError, AttributeError, KeyError):
                            pass
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            tools_type_0_item_type_4_type_0 = PromptRunModelConfigurationToolsType0ItemType4Type0.from_dict(
                                data
                            )

                            return tools_type_0_item_type_4_type_0
                        except (TypeError, ValueError, AttributeError, KeyError):
                            pass
                        return cast(
                            bool
                            | float
                            | list[Any]
                            | None
                            | PromptRunModelConfigurationToolsType0ItemType4Type0
                            | str,
                            data,
                        )

                    tools_type_0_item = _parse_tools_type_0_item(tools_type_0_item_data)

                    tools_type_0.append(tools_type_0_item)

                return tools_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[
                    bool
                    | float
                    | list[Any]
                    | None
                    | PromptRunModelConfigurationToolsType0ItemType4Type0
                    | str
                ]
                | None
                | Unset,
                data,
            )

        tools = _parse_tools(d.pop("tools", UNSET))

        def _parse_output_format(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_format = _parse_output_format(d.pop("output_format", UNSET))

        def _parse_model_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model_type = _parse_model_type(d.pop("model_type", UNSET))

        def _parse_model_detail(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | PromptRunModelConfigurationModelDetailType4Type0
            | str
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                model_detail_type_3 = cast(list[Any], data)

                return model_detail_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                model_detail_type_4_type_0 = (
                    PromptRunModelConfigurationModelDetailType4Type0.from_dict(data)
                )

                return model_detail_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | PromptRunModelConfigurationModelDetailType4Type0
                | str
                | Unset,
                data,
            )

        model_detail = _parse_model_detail(d.pop("model_detail", UNSET))

        def _parse_voice_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        voice_id = _parse_voice_id(d.pop("voice_id", UNSET))

        def _parse_temperature(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        temperature = _parse_temperature(d.pop("temperature", UNSET))

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

        _response_format = d.pop("response_format", UNSET)
        response_format: PromptRunModelConfigurationResponseFormat | Unset
        if isinstance(_response_format, Unset):
            response_format = UNSET
        else:
            response_format = PromptRunModelConfigurationResponseFormat.from_dict(
                _response_format
            )

        _model = d.pop("model", UNSET)
        model: PromptRunModelConfigurationModel | Unset
        if isinstance(_model, Unset):
            model = UNSET
        else:
            model = PromptRunModelConfigurationModel.from_dict(_model)

        prompt_run_model_configuration = cls(
            tool_choice=tool_choice,
            template_format=template_format,
            tools=tools,
            output_format=output_format,
            model_type=model_type,
            model_detail=model_detail,
            voice_id=voice_id,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            response_format=response_format,
            model=model,
        )

        prompt_run_model_configuration.additional_properties = d
        return prompt_run_model_configuration

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
