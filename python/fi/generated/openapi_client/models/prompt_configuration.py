from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_configuration_model_detail_type_4_type_0 import (
        PromptConfigurationModelDetailType4Type0,
    )
    from ..models.prompt_configuration_tools_item_type_4_type_0 import (
        PromptConfigurationToolsItemType4Type0,
    )


T = TypeVar("T", bound="PromptConfiguration")


@_attrs_define
class PromptConfiguration:
    """
    Attributes:
        tool_choice (str | Unset):
        template_format (str | Unset):
        tools (list[bool | float | list[Any] | None | PromptConfigurationToolsItemType4Type0 | str] | Unset):
        output_format (str | Unset):
        model_type (str | Unset):
        model_detail (bool | float | list[Any] | None | PromptConfigurationModelDetailType4Type0 | str | Unset): Any
            valid JSON value.
        voice_id (str | Unset):
    """

    tool_choice: str | Unset = UNSET
    template_format: str | Unset = UNSET
    tools: (
        list[
            bool
            | float
            | list[Any]
            | None
            | PromptConfigurationToolsItemType4Type0
            | str
        ]
        | Unset
    ) = UNSET
    output_format: str | Unset = UNSET
    model_type: str | Unset = UNSET
    model_detail: (
        bool
        | float
        | list[Any]
        | None
        | PromptConfigurationModelDetailType4Type0
        | str
        | Unset
    ) = UNSET
    voice_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.prompt_configuration_model_detail_type_4_type_0 import (
            PromptConfigurationModelDetailType4Type0,
        )
        from ..models.prompt_configuration_tools_item_type_4_type_0 import (
            PromptConfigurationToolsItemType4Type0,
        )

        tool_choice = self.tool_choice

        template_format = self.template_format

        tools: list[bool | dict[str, Any] | float | list[Any] | None | str] | Unset = (
            UNSET
        )
        if not isinstance(self.tools, Unset):
            tools = []
            for tools_item_data in self.tools:
                tools_item: bool | dict[str, Any] | float | list[Any] | None | str
                if isinstance(tools_item_data, list):
                    tools_item = tools_item_data

                elif isinstance(
                    tools_item_data, PromptConfigurationToolsItemType4Type0
                ):
                    tools_item = tools_item_data.to_dict()
                else:
                    tools_item = tools_item_data
                tools.append(tools_item)

        output_format = self.output_format

        model_type = self.model_type

        model_detail: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.model_detail, Unset):
            model_detail = UNSET
        elif isinstance(self.model_detail, list):
            model_detail = self.model_detail

        elif isinstance(self.model_detail, PromptConfigurationModelDetailType4Type0):
            model_detail = self.model_detail.to_dict()
        else:
            model_detail = self.model_detail

        voice_id = self.voice_id

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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_configuration_model_detail_type_4_type_0 import (
            PromptConfigurationModelDetailType4Type0,
        )
        from ..models.prompt_configuration_tools_item_type_4_type_0 import (
            PromptConfigurationToolsItemType4Type0,
        )

        d = dict(src_dict)
        tool_choice = d.pop("tool_choice", UNSET)

        template_format = d.pop("template_format", UNSET)

        _tools = d.pop("tools", UNSET)
        tools: (
            list[
                bool
                | float
                | list[Any]
                | None
                | PromptConfigurationToolsItemType4Type0
                | str
            ]
            | Unset
        ) = UNSET
        if _tools is not UNSET:
            tools = []
            for tools_item_data in _tools:

                def _parse_tools_item(
                    data: object,
                ) -> (
                    bool
                    | float
                    | list[Any]
                    | None
                    | PromptConfigurationToolsItemType4Type0
                    | str
                ):
                    if data is None:
                        return data
                    try:
                        if not isinstance(data, list):
                            raise TypeError()
                        tools_item_type_3 = cast(list[Any], data)

                        return tools_item_type_3
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        tools_item_type_4_type_0 = (
                            PromptConfigurationToolsItemType4Type0.from_dict(data)
                        )

                        return tools_item_type_4_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    return cast(
                        bool
                        | float
                        | list[Any]
                        | None
                        | PromptConfigurationToolsItemType4Type0
                        | str,
                        data,
                    )

                tools_item = _parse_tools_item(tools_item_data)

                tools.append(tools_item)

        output_format = d.pop("output_format", UNSET)

        model_type = d.pop("model_type", UNSET)

        def _parse_model_detail(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | PromptConfigurationModelDetailType4Type0
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
                    PromptConfigurationModelDetailType4Type0.from_dict(data)
                )

                return model_detail_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | PromptConfigurationModelDetailType4Type0
                | str
                | Unset,
                data,
            )

        model_detail = _parse_model_detail(d.pop("model_detail", UNSET))

        voice_id = d.pop("voice_id", UNSET)

        prompt_configuration = cls(
            tool_choice=tool_choice,
            template_format=template_format,
            tools=tools,
            output_format=output_format,
            model_type=model_type,
            model_detail=model_detail,
            voice_id=voice_id,
        )

        prompt_configuration.additional_properties = d
        return prompt_configuration

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
