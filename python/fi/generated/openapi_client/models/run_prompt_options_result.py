from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.run_prompt_choice_option import RunPromptChoiceOption
    from ..models.run_prompt_options_result_models_item import (
        RunPromptOptionsResultModelsItem,
    )
    from ..models.run_prompt_options_result_tool_config import (
        RunPromptOptionsResultToolConfig,
    )
    from ..models.run_prompt_tool_option import RunPromptToolOption


T = TypeVar("T", bound="RunPromptOptionsResult")


@_attrs_define
class RunPromptOptionsResult:
    """
    Attributes:
        models (list[RunPromptOptionsResultModelsItem]):
        tool_config (RunPromptOptionsResultToolConfig):
        available_tools (list[RunPromptToolOption]):
        output_formats (list[RunPromptChoiceOption]):
        tool_choices (list[RunPromptChoiceOption]):
    """

    models: list[RunPromptOptionsResultModelsItem]
    tool_config: RunPromptOptionsResultToolConfig
    available_tools: list[RunPromptToolOption]
    output_formats: list[RunPromptChoiceOption]
    tool_choices: list[RunPromptChoiceOption]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        models = []
        for models_item_data in self.models:
            models_item = models_item_data.to_dict()
            models.append(models_item)

        tool_config = self.tool_config.to_dict()

        available_tools = []
        for available_tools_item_data in self.available_tools:
            available_tools_item = available_tools_item_data.to_dict()
            available_tools.append(available_tools_item)

        output_formats = []
        for output_formats_item_data in self.output_formats:
            output_formats_item = output_formats_item_data.to_dict()
            output_formats.append(output_formats_item)

        tool_choices = []
        for tool_choices_item_data in self.tool_choices:
            tool_choices_item = tool_choices_item_data.to_dict()
            tool_choices.append(tool_choices_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "models": models,
                "tool_config": tool_config,
                "available_tools": available_tools,
                "output_formats": output_formats,
                "tool_choices": tool_choices,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_prompt_choice_option import RunPromptChoiceOption
        from ..models.run_prompt_options_result_models_item import (
            RunPromptOptionsResultModelsItem,
        )
        from ..models.run_prompt_options_result_tool_config import (
            RunPromptOptionsResultToolConfig,
        )
        from ..models.run_prompt_tool_option import RunPromptToolOption

        d = dict(src_dict)
        models = []
        _models = d.pop("models")
        for models_item_data in _models:
            models_item = RunPromptOptionsResultModelsItem.from_dict(models_item_data)

            models.append(models_item)

        tool_config = RunPromptOptionsResultToolConfig.from_dict(d.pop("tool_config"))

        available_tools = []
        _available_tools = d.pop("available_tools")
        for available_tools_item_data in _available_tools:
            available_tools_item = RunPromptToolOption.from_dict(
                available_tools_item_data
            )

            available_tools.append(available_tools_item)

        output_formats = []
        _output_formats = d.pop("output_formats")
        for output_formats_item_data in _output_formats:
            output_formats_item = RunPromptChoiceOption.from_dict(
                output_formats_item_data
            )

            output_formats.append(output_formats_item)

        tool_choices = []
        _tool_choices = d.pop("tool_choices")
        for tool_choices_item_data in _tool_choices:
            tool_choices_item = RunPromptChoiceOption.from_dict(tool_choices_item_data)

            tool_choices.append(tool_choices_item)

        run_prompt_options_result = cls(
            models=models,
            tool_config=tool_config,
            available_tools=available_tools,
            output_formats=output_formats,
            tool_choices=tool_choices,
        )

        run_prompt_options_result.additional_properties = d
        return run_prompt_options_result

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
