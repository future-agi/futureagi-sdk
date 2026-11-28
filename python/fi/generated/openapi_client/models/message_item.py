from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.message_item_content import MessageItemContent
    from ..models.message_item_tool_calls_type_4_type_0 import (
        MessageItemToolCallsType4Type0,
    )


T = TypeVar("T", bound="MessageItem")


@_attrs_define
class MessageItem:
    """
    Attributes:
        role (str):
        content (MessageItemContent): Plain text string or array of content-part objects.
        name (str | Unset):
        tool_calls (bool | float | list[Any] | MessageItemToolCallsType4Type0 | None | str | Unset): Any valid JSON
            value.
        tool_call_id (str | Unset):
        id (str | Unset):
    """

    role: str
    content: MessageItemContent
    name: str | Unset = UNSET
    tool_calls: (
        bool | float | list[Any] | MessageItemToolCallsType4Type0 | None | str | Unset
    ) = UNSET
    tool_call_id: str | Unset = UNSET
    id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.message_item_tool_calls_type_4_type_0 import (
            MessageItemToolCallsType4Type0,
        )

        role = self.role

        content = self.content.to_dict()

        name = self.name

        tool_calls: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.tool_calls, Unset):
            tool_calls = UNSET
        elif isinstance(self.tool_calls, list):
            tool_calls = self.tool_calls

        elif isinstance(self.tool_calls, MessageItemToolCallsType4Type0):
            tool_calls = self.tool_calls.to_dict()
        else:
            tool_calls = self.tool_calls

        tool_call_id = self.tool_call_id

        id = self.id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "role": role,
                "content": content,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if tool_calls is not UNSET:
            field_dict["tool_calls"] = tool_calls
        if tool_call_id is not UNSET:
            field_dict["tool_call_id"] = tool_call_id
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.message_item_content import MessageItemContent
        from ..models.message_item_tool_calls_type_4_type_0 import (
            MessageItemToolCallsType4Type0,
        )

        d = dict(src_dict)
        role = d.pop("role")

        content = MessageItemContent.from_dict(d.pop("content"))

        name = d.pop("name", UNSET)

        def _parse_tool_calls(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | MessageItemToolCallsType4Type0
            | None
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
                tool_calls_type_3 = cast(list[Any], data)

                return tool_calls_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tool_calls_type_4_type_0 = MessageItemToolCallsType4Type0.from_dict(
                    data
                )

                return tool_calls_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | MessageItemToolCallsType4Type0
                | None
                | str
                | Unset,
                data,
            )

        tool_calls = _parse_tool_calls(d.pop("tool_calls", UNSET))

        tool_call_id = d.pop("tool_call_id", UNSET)

        id = d.pop("id", UNSET)

        message_item = cls(
            role=role,
            content=content,
            name=name,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            id=id,
        )

        message_item.additional_properties = d
        return message_item

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
