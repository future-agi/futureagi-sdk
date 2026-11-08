from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.message_item import MessageItem
    from ..models.prompt_run_model_configuration import PromptRunModelConfiguration


T = TypeVar("T", bound="PromptRunConfiguration")


@_attrs_define
class PromptRunConfiguration:
    """
    Attributes:
        messages (list[MessageItem] | Unset):
        configuration (PromptRunModelConfiguration | Unset):
    """

    messages: list[MessageItem] | Unset = UNSET
    configuration: PromptRunModelConfiguration | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        messages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.messages, Unset):
            messages = []
            for messages_item_data in self.messages:
                messages_item = messages_item_data.to_dict()
                messages.append(messages_item)

        configuration: dict[str, Any] | Unset = UNSET
        if not isinstance(self.configuration, Unset):
            configuration = self.configuration.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if messages is not UNSET:
            field_dict["messages"] = messages
        if configuration is not UNSET:
            field_dict["configuration"] = configuration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.message_item import MessageItem
        from ..models.prompt_run_model_configuration import PromptRunModelConfiguration

        d = dict(src_dict)
        _messages = d.pop("messages", UNSET)
        messages: list[MessageItem] | Unset = UNSET
        if _messages is not UNSET:
            messages = []
            for messages_item_data in _messages:
                messages_item = MessageItem.from_dict(messages_item_data)

                messages.append(messages_item)

        _configuration = d.pop("configuration", UNSET)
        configuration: PromptRunModelConfiguration | Unset
        if isinstance(_configuration, Unset):
            configuration = UNSET
        else:
            configuration = PromptRunModelConfiguration.from_dict(_configuration)

        prompt_run_configuration = cls(
            messages=messages,
            configuration=configuration,
        )

        prompt_run_configuration.additional_properties = d
        return prompt_run_configuration

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
