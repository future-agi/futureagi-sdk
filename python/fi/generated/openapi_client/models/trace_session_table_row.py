from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_session_table_row_additional_property_type_4_type_0 import (
        TraceSessionTableRowAdditionalPropertyType4Type0,
    )
    from ..models.trace_session_table_row_first_message_type_4_type_0 import (
        TraceSessionTableRowFirstMessageType4Type0,
    )
    from ..models.trace_session_table_row_last_message_type_4_type_0 import (
        TraceSessionTableRowLastMessageType4Type0,
    )


T = TypeVar("T", bound="TraceSessionTableRow")


@_attrs_define
class TraceSessionTableRow:
    """
    Attributes:
        session_id (None | str | Unset):
        session_name (None | str | Unset):
        project_id (None | Unset | UUID):
        start_time (datetime.datetime | None | Unset):
        end_time (datetime.datetime | None | Unset):
        created_at (datetime.datetime | None | Unset):
        duration (float | None | Unset):
        total_cost (float | None | Unset):
        total_tokens (int | None | Unset):
        total_traces_count (int | None | Unset):
        first_message (bool | float | list[Any] | None | str | TraceSessionTableRowFirstMessageType4Type0 | Unset): Any
            valid JSON value.
        last_message (bool | float | list[Any] | None | str | TraceSessionTableRowLastMessageType4Type0 | Unset): Any
            valid JSON value.
        user_id (None | str | Unset):
        user_id_type (None | str | Unset):
        user_id_hash (None | str | Unset):
    """

    session_id: None | str | Unset = UNSET
    session_name: None | str | Unset = UNSET
    project_id: None | Unset | UUID = UNSET
    start_time: datetime.datetime | None | Unset = UNSET
    end_time: datetime.datetime | None | Unset = UNSET
    created_at: datetime.datetime | None | Unset = UNSET
    duration: float | None | Unset = UNSET
    total_cost: float | None | Unset = UNSET
    total_tokens: int | None | Unset = UNSET
    total_traces_count: int | None | Unset = UNSET
    first_message: (
        bool
        | float
        | list[Any]
        | None
        | str
        | TraceSessionTableRowFirstMessageType4Type0
        | Unset
    ) = UNSET
    last_message: (
        bool
        | float
        | list[Any]
        | None
        | str
        | TraceSessionTableRowLastMessageType4Type0
        | Unset
    ) = UNSET
    user_id: None | str | Unset = UNSET
    user_id_type: None | str | Unset = UNSET
    user_id_hash: None | str | Unset = UNSET
    additional_properties: dict[
        str,
        bool
        | float
        | list[Any]
        | None
        | str
        | TraceSessionTableRowAdditionalPropertyType4Type0,
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.trace_session_table_row_additional_property_type_4_type_0 import (
            TraceSessionTableRowAdditionalPropertyType4Type0,
        )
        from ..models.trace_session_table_row_first_message_type_4_type_0 import (
            TraceSessionTableRowFirstMessageType4Type0,
        )
        from ..models.trace_session_table_row_last_message_type_4_type_0 import (
            TraceSessionTableRowLastMessageType4Type0,
        )

        session_id: None | str | Unset
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        else:
            session_id = self.session_id

        session_name: None | str | Unset
        if isinstance(self.session_name, Unset):
            session_name = UNSET
        else:
            session_name = self.session_name

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        elif isinstance(self.project_id, UUID):
            project_id = str(self.project_id)
        else:
            project_id = self.project_id

        start_time: None | str | Unset
        if isinstance(self.start_time, Unset):
            start_time = UNSET
        elif isinstance(self.start_time, datetime.datetime):
            start_time = self.start_time.isoformat()
        else:
            start_time = self.start_time

        end_time: None | str | Unset
        if isinstance(self.end_time, Unset):
            end_time = UNSET
        elif isinstance(self.end_time, datetime.datetime):
            end_time = self.end_time.isoformat()
        else:
            end_time = self.end_time

        created_at: None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        duration: float | None | Unset
        if isinstance(self.duration, Unset):
            duration = UNSET
        else:
            duration = self.duration

        total_cost: float | None | Unset
        if isinstance(self.total_cost, Unset):
            total_cost = UNSET
        else:
            total_cost = self.total_cost

        total_tokens: int | None | Unset
        if isinstance(self.total_tokens, Unset):
            total_tokens = UNSET
        else:
            total_tokens = self.total_tokens

        total_traces_count: int | None | Unset
        if isinstance(self.total_traces_count, Unset):
            total_traces_count = UNSET
        else:
            total_traces_count = self.total_traces_count

        first_message: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.first_message, Unset):
            first_message = UNSET
        elif isinstance(self.first_message, list):
            first_message = self.first_message

        elif isinstance(self.first_message, TraceSessionTableRowFirstMessageType4Type0):
            first_message = self.first_message.to_dict()
        else:
            first_message = self.first_message

        last_message: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.last_message, Unset):
            last_message = UNSET
        elif isinstance(self.last_message, list):
            last_message = self.last_message

        elif isinstance(self.last_message, TraceSessionTableRowLastMessageType4Type0):
            last_message = self.last_message.to_dict()
        else:
            last_message = self.last_message

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        user_id_type: None | str | Unset
        if isinstance(self.user_id_type, Unset):
            user_id_type = UNSET
        else:
            user_id_type = self.user_id_type

        user_id_hash: None | str | Unset
        if isinstance(self.user_id_hash, Unset):
            user_id_hash = UNSET
        else:
            user_id_hash = self.user_id_hash

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, list):
                field_dict[prop_name] = prop

            elif isinstance(prop, TraceSessionTableRowAdditionalPropertyType4Type0):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop

        field_dict.update({})
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if session_name is not UNSET:
            field_dict["session_name"] = session_name
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if start_time is not UNSET:
            field_dict["start_time"] = start_time
        if end_time is not UNSET:
            field_dict["end_time"] = end_time
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if duration is not UNSET:
            field_dict["duration"] = duration
        if total_cost is not UNSET:
            field_dict["total_cost"] = total_cost
        if total_tokens is not UNSET:
            field_dict["total_tokens"] = total_tokens
        if total_traces_count is not UNSET:
            field_dict["total_traces_count"] = total_traces_count
        if first_message is not UNSET:
            field_dict["first_message"] = first_message
        if last_message is not UNSET:
            field_dict["last_message"] = last_message
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if user_id_type is not UNSET:
            field_dict["user_id_type"] = user_id_type
        if user_id_hash is not UNSET:
            field_dict["user_id_hash"] = user_id_hash

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_session_table_row_additional_property_type_4_type_0 import (
            TraceSessionTableRowAdditionalPropertyType4Type0,
        )
        from ..models.trace_session_table_row_first_message_type_4_type_0 import (
            TraceSessionTableRowFirstMessageType4Type0,
        )
        from ..models.trace_session_table_row_last_message_type_4_type_0 import (
            TraceSessionTableRowLastMessageType4Type0,
        )

        d = dict(src_dict)

        def _parse_session_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_id = _parse_session_id(d.pop("session_id", UNSET))

        def _parse_session_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_name = _parse_session_name(d.pop("session_name", UNSET))

        def _parse_project_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                project_id_type_0 = UUID(data)

                return project_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_start_time(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_time_type_0 = isoparse(data)

                return start_time_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        start_time = _parse_start_time(d.pop("start_time", UNSET))

        def _parse_end_time(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_time_type_0 = isoparse(data)

                return end_time_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        end_time = _parse_end_time(d.pop("end_time", UNSET))

        def _parse_created_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_duration(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        duration = _parse_duration(d.pop("duration", UNSET))

        def _parse_total_cost(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        total_cost = _parse_total_cost(d.pop("total_cost", UNSET))

        def _parse_total_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_tokens = _parse_total_tokens(d.pop("total_tokens", UNSET))

        def _parse_total_traces_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_traces_count = _parse_total_traces_count(
            d.pop("total_traces_count", UNSET)
        )

        def _parse_first_message(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | str
            | TraceSessionTableRowFirstMessageType4Type0
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                first_message_type_3 = cast(list[Any], data)

                return first_message_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                first_message_type_4_type_0 = (
                    TraceSessionTableRowFirstMessageType4Type0.from_dict(data)
                )

                return first_message_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | str
                | TraceSessionTableRowFirstMessageType4Type0
                | Unset,
                data,
            )

        first_message = _parse_first_message(d.pop("first_message", UNSET))

        def _parse_last_message(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | str
            | TraceSessionTableRowLastMessageType4Type0
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                last_message_type_3 = cast(list[Any], data)

                return last_message_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                last_message_type_4_type_0 = (
                    TraceSessionTableRowLastMessageType4Type0.from_dict(data)
                )

                return last_message_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | str
                | TraceSessionTableRowLastMessageType4Type0
                | Unset,
                data,
            )

        last_message = _parse_last_message(d.pop("last_message", UNSET))

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_user_id_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id_type = _parse_user_id_type(d.pop("user_id_type", UNSET))

        def _parse_user_id_hash(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id_hash = _parse_user_id_hash(d.pop("user_id_hash", UNSET))

        trace_session_table_row = cls(
            session_id=session_id,
            session_name=session_name,
            project_id=project_id,
            start_time=start_time,
            end_time=end_time,
            created_at=created_at,
            duration=duration,
            total_cost=total_cost,
            total_tokens=total_tokens,
            total_traces_count=total_traces_count,
            first_message=first_message,
            last_message=last_message,
            user_id=user_id,
            user_id_type=user_id_type,
            user_id_hash=user_id_hash,
        )

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> (
                bool
                | float
                | list[Any]
                | None
                | str
                | TraceSessionTableRowAdditionalPropertyType4Type0
            ):
                if data is None:
                    return data
                try:
                    if not isinstance(data, list):
                        raise TypeError()
                    additional_property_type_3 = cast(list[Any], data)

                    return additional_property_type_3
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_4_type_0 = (
                        TraceSessionTableRowAdditionalPropertyType4Type0.from_dict(data)
                    )

                    return additional_property_type_4_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                return cast(
                    bool
                    | float
                    | list[Any]
                    | None
                    | str
                    | TraceSessionTableRowAdditionalPropertyType4Type0,
                    data,
                )

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        trace_session_table_row.additional_properties = additional_properties
        return trace_session_table_row

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> (
        bool
        | float
        | list[Any]
        | None
        | str
        | TraceSessionTableRowAdditionalPropertyType4Type0
    ):
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: bool
        | float
        | list[Any]
        | None
        | str
        | TraceSessionTableRowAdditionalPropertyType4Type0,
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
