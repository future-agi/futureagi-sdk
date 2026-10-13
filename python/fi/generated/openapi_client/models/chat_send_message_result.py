from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_message_contract import ChatMessageContract


T = TypeVar("T", bound="ChatSendMessageResult")


@_attrs_define
class ChatSendMessageResult:
    """
    Attributes:
        message_history (list[ChatMessageContract]):
        input_message (list[ChatMessageContract] | None | Unset):
        output_message (list[ChatMessageContract] | None | Unset):
        chat_ended (bool | Unset):  Default: False.
    """

    message_history: list[ChatMessageContract]
    input_message: list[ChatMessageContract] | None | Unset = UNSET
    output_message: list[ChatMessageContract] | None | Unset = UNSET
    chat_ended: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message_history = []
        for message_history_item_data in self.message_history:
            message_history_item = message_history_item_data.to_dict()
            message_history.append(message_history_item)

        input_message: list[dict[str, Any]] | None | Unset
        if isinstance(self.input_message, Unset):
            input_message = UNSET
        elif isinstance(self.input_message, list):
            input_message = []
            for input_message_type_0_item_data in self.input_message:
                input_message_type_0_item = input_message_type_0_item_data.to_dict()
                input_message.append(input_message_type_0_item)

        else:
            input_message = self.input_message

        output_message: list[dict[str, Any]] | None | Unset
        if isinstance(self.output_message, Unset):
            output_message = UNSET
        elif isinstance(self.output_message, list):
            output_message = []
            for output_message_type_0_item_data in self.output_message:
                output_message_type_0_item = output_message_type_0_item_data.to_dict()
                output_message.append(output_message_type_0_item)

        else:
            output_message = self.output_message

        chat_ended = self.chat_ended

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message_history": message_history,
            }
        )
        if input_message is not UNSET:
            field_dict["input_message"] = input_message
        if output_message is not UNSET:
            field_dict["output_message"] = output_message
        if chat_ended is not UNSET:
            field_dict["chat_ended"] = chat_ended

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_message_contract import ChatMessageContract

        d = dict(src_dict)
        message_history = []
        _message_history = d.pop("message_history")
        for message_history_item_data in _message_history:
            message_history_item = ChatMessageContract.from_dict(
                message_history_item_data
            )

            message_history.append(message_history_item)

        def _parse_input_message(
            data: object,
        ) -> list[ChatMessageContract] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                input_message_type_0 = []
                _input_message_type_0 = data
                for input_message_type_0_item_data in _input_message_type_0:
                    input_message_type_0_item = ChatMessageContract.from_dict(
                        input_message_type_0_item_data
                    )

                    input_message_type_0.append(input_message_type_0_item)

                return input_message_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ChatMessageContract] | None | Unset, data)

        input_message = _parse_input_message(d.pop("input_message", UNSET))

        def _parse_output_message(
            data: object,
        ) -> list[ChatMessageContract] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                output_message_type_0 = []
                _output_message_type_0 = data
                for output_message_type_0_item_data in _output_message_type_0:
                    output_message_type_0_item = ChatMessageContract.from_dict(
                        output_message_type_0_item_data
                    )

                    output_message_type_0.append(output_message_type_0_item)

                return output_message_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ChatMessageContract] | None | Unset, data)

        output_message = _parse_output_message(d.pop("output_message", UNSET))

        chat_ended = d.pop("chat_ended", UNSET)

        chat_send_message_result = cls(
            message_history=message_history,
            input_message=input_message,
            output_message=output_message,
            chat_ended=chat_ended,
        )

        chat_send_message_result.additional_properties = d
        return chat_send_message_result

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
