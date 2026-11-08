from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.user_alert_monitor_log_write_request_type import (
    UserAlertMonitorLogWriteRequestType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserAlertMonitorLogWriteRequest")


@_attrs_define
class UserAlertMonitorLogWriteRequest:
    """
    Attributes:
        alert (UUID):
        type_ (UserAlertMonitorLogWriteRequestType):
        message (str):
        resolved (bool | Unset):  Default: False.
        resolved_at (datetime.datetime | None | Unset):
        link (None | str | Unset):
        time_window_start (datetime.datetime | None | Unset):
        time_window_end (datetime.datetime | None | Unset):
    """

    alert: UUID
    type_: UserAlertMonitorLogWriteRequestType
    message: str
    resolved: bool | Unset = False
    resolved_at: datetime.datetime | None | Unset = UNSET
    link: None | str | Unset = UNSET
    time_window_start: datetime.datetime | None | Unset = UNSET
    time_window_end: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        alert = str(self.alert)

        type_ = self.type_.value

        message = self.message

        resolved = self.resolved

        resolved_at: None | str | Unset
        if isinstance(self.resolved_at, Unset):
            resolved_at = UNSET
        elif isinstance(self.resolved_at, datetime.datetime):
            resolved_at = self.resolved_at.isoformat()
        else:
            resolved_at = self.resolved_at

        link: None | str | Unset
        if isinstance(self.link, Unset):
            link = UNSET
        else:
            link = self.link

        time_window_start: None | str | Unset
        if isinstance(self.time_window_start, Unset):
            time_window_start = UNSET
        elif isinstance(self.time_window_start, datetime.datetime):
            time_window_start = self.time_window_start.isoformat()
        else:
            time_window_start = self.time_window_start

        time_window_end: None | str | Unset
        if isinstance(self.time_window_end, Unset):
            time_window_end = UNSET
        elif isinstance(self.time_window_end, datetime.datetime):
            time_window_end = self.time_window_end.isoformat()
        else:
            time_window_end = self.time_window_end

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "alert": alert,
                "type": type_,
                "message": message,
            }
        )
        if resolved is not UNSET:
            field_dict["resolved"] = resolved
        if resolved_at is not UNSET:
            field_dict["resolved_at"] = resolved_at
        if link is not UNSET:
            field_dict["link"] = link
        if time_window_start is not UNSET:
            field_dict["time_window_start"] = time_window_start
        if time_window_end is not UNSET:
            field_dict["time_window_end"] = time_window_end

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        alert = UUID(d.pop("alert"))

        type_ = UserAlertMonitorLogWriteRequestType(d.pop("type"))

        message = d.pop("message")

        resolved = d.pop("resolved", UNSET)

        def _parse_resolved_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                resolved_at_type_0 = isoparse(data)

                return resolved_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        resolved_at = _parse_resolved_at(d.pop("resolved_at", UNSET))

        def _parse_link(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        link = _parse_link(d.pop("link", UNSET))

        def _parse_time_window_start(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                time_window_start_type_0 = isoparse(data)

                return time_window_start_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        time_window_start = _parse_time_window_start(d.pop("time_window_start", UNSET))

        def _parse_time_window_end(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                time_window_end_type_0 = isoparse(data)

                return time_window_end_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        time_window_end = _parse_time_window_end(d.pop("time_window_end", UNSET))

        user_alert_monitor_log_write_request = cls(
            alert=alert,
            type_=type_,
            message=message,
            resolved=resolved,
            resolved_at=resolved_at,
            link=link,
            time_window_start=time_window_start,
            time_window_end=time_window_end,
        )

        user_alert_monitor_log_write_request.additional_properties = d
        return user_alert_monitor_log_write_request

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
