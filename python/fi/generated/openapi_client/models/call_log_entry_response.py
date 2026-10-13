from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.call_log_entry_response_attributes import (
        CallLogEntryResponseAttributes,
    )
    from ..models.call_log_entry_response_payload import CallLogEntryResponsePayload


T = TypeVar("T", bound="CallLogEntryResponse")


@_attrs_define
class CallLogEntryResponse:
    """
    Attributes:
        id (str | Unset):
        logged_at (None | str | Unset):
        level (None | str | Unset):
        severity_text (None | str | Unset):
        category (None | str | Unset):
        body (None | str | Unset):
        attributes (CallLogEntryResponseAttributes | Unset):
        payload (CallLogEntryResponsePayload | Unset):
    """

    id: str | Unset = UNSET
    logged_at: None | str | Unset = UNSET
    level: None | str | Unset = UNSET
    severity_text: None | str | Unset = UNSET
    category: None | str | Unset = UNSET
    body: None | str | Unset = UNSET
    attributes: CallLogEntryResponseAttributes | Unset = UNSET
    payload: CallLogEntryResponsePayload | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        logged_at: None | str | Unset
        if isinstance(self.logged_at, Unset):
            logged_at = UNSET
        else:
            logged_at = self.logged_at

        level: None | str | Unset
        if isinstance(self.level, Unset):
            level = UNSET
        else:
            level = self.level

        severity_text: None | str | Unset
        if isinstance(self.severity_text, Unset):
            severity_text = UNSET
        else:
            severity_text = self.severity_text

        category: None | str | Unset
        if isinstance(self.category, Unset):
            category = UNSET
        else:
            category = self.category

        body: None | str | Unset
        if isinstance(self.body, Unset):
            body = UNSET
        else:
            body = self.body

        attributes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = self.attributes.to_dict()

        payload: dict[str, Any] | Unset = UNSET
        if not isinstance(self.payload, Unset):
            payload = self.payload.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if logged_at is not UNSET:
            field_dict["logged_at"] = logged_at
        if level is not UNSET:
            field_dict["level"] = level
        if severity_text is not UNSET:
            field_dict["severity_text"] = severity_text
        if category is not UNSET:
            field_dict["category"] = category
        if body is not UNSET:
            field_dict["body"] = body
        if attributes is not UNSET:
            field_dict["attributes"] = attributes
        if payload is not UNSET:
            field_dict["payload"] = payload

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.call_log_entry_response_attributes import (
            CallLogEntryResponseAttributes,
        )
        from ..models.call_log_entry_response_payload import CallLogEntryResponsePayload

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        def _parse_logged_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        logged_at = _parse_logged_at(d.pop("logged_at", UNSET))

        def _parse_level(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        level = _parse_level(d.pop("level", UNSET))

        def _parse_severity_text(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        severity_text = _parse_severity_text(d.pop("severity_text", UNSET))

        def _parse_category(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        category = _parse_category(d.pop("category", UNSET))

        def _parse_body(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        body = _parse_body(d.pop("body", UNSET))

        _attributes = d.pop("attributes", UNSET)
        attributes: CallLogEntryResponseAttributes | Unset
        if isinstance(_attributes, Unset):
            attributes = UNSET
        else:
            attributes = CallLogEntryResponseAttributes.from_dict(_attributes)

        _payload = d.pop("payload", UNSET)
        payload: CallLogEntryResponsePayload | Unset
        if isinstance(_payload, Unset):
            payload = UNSET
        else:
            payload = CallLogEntryResponsePayload.from_dict(_payload)

        call_log_entry_response = cls(
            id=id,
            logged_at=logged_at,
            level=level,
            severity_text=severity_text,
            category=category,
            body=body,
            attributes=attributes,
            payload=payload,
        )

        call_log_entry_response.additional_properties = d
        return call_log_entry_response

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
