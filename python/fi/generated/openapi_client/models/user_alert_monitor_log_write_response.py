from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.user_alert_monitor_log_write_response_type import (
    UserAlertMonitorLogWriteResponseType,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="UserAlertMonitorLogWriteResponse")


@_attrs_define
class UserAlertMonitorLogWriteResponse:
    """
    Attributes:
        id (UUID):
        alert (UUID):
        type_ (UserAlertMonitorLogWriteResponseType):
        message (str):
        resolved (bool):
        created_at (datetime.datetime):
        resolved_at (datetime.datetime | None | Unset):
        resolved_by (User | Unset):
        link (None | str | Unset):
        time_window_start (datetime.datetime | None | Unset):
        time_window_end (datetime.datetime | None | Unset):
    """

    id: UUID
    alert: UUID
    type_: UserAlertMonitorLogWriteResponseType
    message: str
    resolved: bool
    created_at: datetime.datetime
    resolved_at: datetime.datetime | None | Unset = UNSET
    resolved_by: User | Unset = UNSET
    link: None | str | Unset = UNSET
    time_window_start: datetime.datetime | None | Unset = UNSET
    time_window_end: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        alert = str(self.alert)

        type_ = self.type_.value

        message = self.message

        resolved = self.resolved

        created_at = self.created_at.isoformat()

        resolved_at: None | str | Unset
        if isinstance(self.resolved_at, Unset):
            resolved_at = UNSET
        elif isinstance(self.resolved_at, datetime.datetime):
            resolved_at = self.resolved_at.isoformat()
        else:
            resolved_at = self.resolved_at

        resolved_by: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resolved_by, Unset):
            resolved_by = self.resolved_by.to_dict()

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
                "id": id,
                "alert": alert,
                "type": type_,
                "message": message,
                "resolved": resolved,
                "created_at": created_at,
            }
        )
        if resolved_at is not UNSET:
            field_dict["resolved_at"] = resolved_at
        if resolved_by is not UNSET:
            field_dict["resolved_by"] = resolved_by
        if link is not UNSET:
            field_dict["link"] = link
        if time_window_start is not UNSET:
            field_dict["time_window_start"] = time_window_start
        if time_window_end is not UNSET:
            field_dict["time_window_end"] = time_window_end

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user import User

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        alert = UUID(d.pop("alert"))

        type_ = UserAlertMonitorLogWriteResponseType(d.pop("type"))

        message = d.pop("message")

        resolved = d.pop("resolved")

        created_at = isoparse(d.pop("created_at"))

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

        _resolved_by = d.pop("resolved_by", UNSET)
        resolved_by: User | Unset
        if isinstance(_resolved_by, Unset):
            resolved_by = UNSET
        else:
            resolved_by = User.from_dict(_resolved_by)

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

        user_alert_monitor_log_write_response = cls(
            id=id,
            alert=alert,
            type_=type_,
            message=message,
            resolved=resolved,
            created_at=created_at,
            resolved_at=resolved_at,
            resolved_by=resolved_by,
            link=link,
            time_window_start=time_window_start,
            time_window_end=time_window_end,
        )

        user_alert_monitor_log_write_response.additional_properties = d
        return user_alert_monitor_log_write_response

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
