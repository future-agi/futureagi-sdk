from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_message_contract import ChatMessageContract
    from ..models.send_chat_request_metrics import SendChatRequestMetrics


T = TypeVar("T", bound="SendChatRequest")


@_attrs_define
class SendChatRequest:
    """
    Attributes:
        messages (list[ChatMessageContract] | None | Unset):
        metrics (SendChatRequestMetrics | Unset):
        initiate_chat (bool | Unset):  Default: False.
    """

    messages: list[ChatMessageContract] | None | Unset = UNSET
    metrics: SendChatRequestMetrics | Unset = UNSET
    initiate_chat: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        messages: list[dict[str, Any]] | None | Unset
        if isinstance(self.messages, Unset):
            messages = UNSET
        elif isinstance(self.messages, list):
            messages = []
            for messages_type_0_item_data in self.messages:
                messages_type_0_item = messages_type_0_item_data.to_dict()
                messages.append(messages_type_0_item)

        else:
            messages = self.messages

        metrics: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metrics, Unset):
            metrics = self.metrics.to_dict()

        initiate_chat = self.initiate_chat

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if messages is not UNSET:
            field_dict["messages"] = messages
        if metrics is not UNSET:
            field_dict["metrics"] = metrics
        if initiate_chat is not UNSET:
            field_dict["initiate_chat"] = initiate_chat

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_message_contract import ChatMessageContract
        from ..models.send_chat_request_metrics import SendChatRequestMetrics

        d = dict(src_dict)

        def _parse_messages(data: object) -> list[ChatMessageContract] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                messages_type_0 = []
                _messages_type_0 = data
                for messages_type_0_item_data in _messages_type_0:
                    messages_type_0_item = ChatMessageContract.from_dict(
                        messages_type_0_item_data
                    )

                    messages_type_0.append(messages_type_0_item)

                return messages_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ChatMessageContract] | None | Unset, data)

        messages = _parse_messages(d.pop("messages", UNSET))

        _metrics = d.pop("metrics", UNSET)
        metrics: SendChatRequestMetrics | Unset
        if isinstance(_metrics, Unset):
            metrics = UNSET
        else:
            metrics = SendChatRequestMetrics.from_dict(_metrics)

        initiate_chat = d.pop("initiate_chat", UNSET)

        send_chat_request = cls(
            messages=messages,
            metrics=metrics,
            initiate_chat=initiate_chat,
        )

        send_chat_request.additional_properties = d
        return send_chat_request

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
