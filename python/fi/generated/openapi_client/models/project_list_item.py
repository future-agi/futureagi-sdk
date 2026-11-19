from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="ProjectListItem")


@_attrs_define
class ProjectListItem:
    """
    Attributes:
        id (UUID):
        name (str):
        last_30_days_vol (int | None):
        daily_volume (list[int] | None):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        last_active (datetime.datetime | None):
        activity_query_complete (bool):
        activity_error_code (None | str):
        activity_query_exact (bool):
        activity_query_provenance (str):
        run_count (int):
        issues (int):
        tags (list[str]):
    """

    id: UUID
    name: str
    last_30_days_vol: int | None
    daily_volume: list[int] | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_active: datetime.datetime | None
    activity_query_complete: bool
    activity_error_code: None | str
    activity_query_exact: bool
    activity_query_provenance: str
    run_count: int
    issues: int
    tags: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        last_30_days_vol: int | None
        last_30_days_vol = self.last_30_days_vol

        daily_volume: list[int] | None
        if isinstance(self.daily_volume, list):
            daily_volume = self.daily_volume

        else:
            daily_volume = self.daily_volume

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        last_active: None | str
        if isinstance(self.last_active, datetime.datetime):
            last_active = self.last_active.isoformat()
        else:
            last_active = self.last_active

        activity_query_complete = self.activity_query_complete

        activity_error_code: None | str
        activity_error_code = self.activity_error_code

        activity_query_exact = self.activity_query_exact

        activity_query_provenance = self.activity_query_provenance

        run_count = self.run_count

        issues = self.issues

        tags = self.tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "last_30_days_vol": last_30_days_vol,
                "daily_volume": daily_volume,
                "created_at": created_at,
                "updated_at": updated_at,
                "last_active": last_active,
                "activity_query_complete": activity_query_complete,
                "activity_error_code": activity_error_code,
                "activity_query_exact": activity_query_exact,
                "activity_query_provenance": activity_query_provenance,
                "run_count": run_count,
                "issues": issues,
                "tags": tags,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        def _parse_last_30_days_vol(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        last_30_days_vol = _parse_last_30_days_vol(d.pop("last_30_days_vol"))

        def _parse_daily_volume(data: object) -> list[int] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                daily_volume_type_0 = cast(list[int], data)

                return daily_volume_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[int] | None, data)

        daily_volume = _parse_daily_volume(d.pop("daily_volume"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_last_active(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_active_type_0 = isoparse(data)

                return last_active_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_active = _parse_last_active(d.pop("last_active"))

        activity_query_complete = d.pop("activity_query_complete")

        def _parse_activity_error_code(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        activity_error_code = _parse_activity_error_code(d.pop("activity_error_code"))

        activity_query_exact = d.pop("activity_query_exact")

        activity_query_provenance = d.pop("activity_query_provenance")

        run_count = d.pop("run_count")

        issues = d.pop("issues")

        tags = cast(list[str], d.pop("tags"))

        project_list_item = cls(
            id=id,
            name=name,
            last_30_days_vol=last_30_days_vol,
            daily_volume=daily_volume,
            created_at=created_at,
            updated_at=updated_at,
            last_active=last_active,
            activity_query_complete=activity_query_complete,
            activity_error_code=activity_error_code,
            activity_query_exact=activity_query_exact,
            activity_query_provenance=activity_query_provenance,
            run_count=run_count,
            issues=issues,
            tags=tags,
        )

        project_list_item.additional_properties = d
        return project_list_item

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
