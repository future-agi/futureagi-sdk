from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.error_name import ErrorName
    from ..models.trend_point import TrendPoint


T = TypeVar("T", bound="FeedListRow")


@_attrs_define
class FeedListRow:
    """
    Attributes:
        cluster_id (str):
        source (str):
        error (ErrorName):
        status (str):
        severity (str):
        occurrences (int):
        trace_count (int):
        fix_layer (None | str):
        users_affected (int):
        sessions (int):
        first_seen (datetime.datetime | None):
        last_seen (datetime.datetime | None):
        trends (list[TrendPoint]):
        assignees (list[str]):
        model (None | str):
        model_version (None | str):
        project (None | str):
        project_id (None | str):
        environment (None | str):
        eval_score (float | None):
        trace_id (None | str):
        external_issue_url (None | str):
        external_issue_id (None | str):
    """

    cluster_id: str
    source: str
    error: ErrorName
    status: str
    severity: str
    occurrences: int
    trace_count: int
    fix_layer: None | str
    users_affected: int
    sessions: int
    first_seen: datetime.datetime | None
    last_seen: datetime.datetime | None
    trends: list[TrendPoint]
    assignees: list[str]
    model: None | str
    model_version: None | str
    project: None | str
    project_id: None | str
    environment: None | str
    eval_score: float | None
    trace_id: None | str
    external_issue_url: None | str
    external_issue_id: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cluster_id = self.cluster_id

        source = self.source

        error = self.error.to_dict()

        status = self.status

        severity = self.severity

        occurrences = self.occurrences

        trace_count = self.trace_count

        fix_layer: None | str
        fix_layer = self.fix_layer

        users_affected = self.users_affected

        sessions = self.sessions

        first_seen: None | str
        if isinstance(self.first_seen, datetime.datetime):
            first_seen = self.first_seen.isoformat()
        else:
            first_seen = self.first_seen

        last_seen: None | str
        if isinstance(self.last_seen, datetime.datetime):
            last_seen = self.last_seen.isoformat()
        else:
            last_seen = self.last_seen

        trends = []
        for trends_item_data in self.trends:
            trends_item = trends_item_data.to_dict()
            trends.append(trends_item)

        assignees = self.assignees

        model: None | str
        model = self.model

        model_version: None | str
        model_version = self.model_version

        project: None | str
        project = self.project

        project_id: None | str
        project_id = self.project_id

        environment: None | str
        environment = self.environment

        eval_score: float | None
        eval_score = self.eval_score

        trace_id: None | str
        trace_id = self.trace_id

        external_issue_url: None | str
        external_issue_url = self.external_issue_url

        external_issue_id: None | str
        external_issue_id = self.external_issue_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cluster_id": cluster_id,
                "source": source,
                "error": error,
                "status": status,
                "severity": severity,
                "occurrences": occurrences,
                "trace_count": trace_count,
                "fix_layer": fix_layer,
                "users_affected": users_affected,
                "sessions": sessions,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "trends": trends,
                "assignees": assignees,
                "model": model,
                "model_version": model_version,
                "project": project,
                "project_id": project_id,
                "environment": environment,
                "eval_score": eval_score,
                "trace_id": trace_id,
                "external_issue_url": external_issue_url,
                "external_issue_id": external_issue_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_name import ErrorName
        from ..models.trend_point import TrendPoint

        d = dict(src_dict)
        cluster_id = d.pop("cluster_id")

        source = d.pop("source")

        error = ErrorName.from_dict(d.pop("error"))

        status = d.pop("status")

        severity = d.pop("severity")

        occurrences = d.pop("occurrences")

        trace_count = d.pop("trace_count")

        def _parse_fix_layer(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        fix_layer = _parse_fix_layer(d.pop("fix_layer"))

        users_affected = d.pop("users_affected")

        sessions = d.pop("sessions")

        def _parse_first_seen(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                first_seen_type_0 = isoparse(data)

                return first_seen_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        first_seen = _parse_first_seen(d.pop("first_seen"))

        def _parse_last_seen(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_seen_type_0 = isoparse(data)

                return last_seen_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_seen = _parse_last_seen(d.pop("last_seen"))

        trends = []
        _trends = d.pop("trends")
        for trends_item_data in _trends:
            trends_item = TrendPoint.from_dict(trends_item_data)

            trends.append(trends_item)

        assignees = cast(list[str], d.pop("assignees"))

        def _parse_model(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        model = _parse_model(d.pop("model"))

        def _parse_model_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        model_version = _parse_model_version(d.pop("model_version"))

        def _parse_project(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project = _parse_project(d.pop("project"))

        def _parse_project_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project_id = _parse_project_id(d.pop("project_id"))

        def _parse_environment(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        environment = _parse_environment(d.pop("environment"))

        def _parse_eval_score(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        eval_score = _parse_eval_score(d.pop("eval_score"))

        def _parse_trace_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        trace_id = _parse_trace_id(d.pop("trace_id"))

        def _parse_external_issue_url(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        external_issue_url = _parse_external_issue_url(d.pop("external_issue_url"))

        def _parse_external_issue_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        external_issue_id = _parse_external_issue_id(d.pop("external_issue_id"))

        feed_list_row = cls(
            cluster_id=cluster_id,
            source=source,
            error=error,
            status=status,
            severity=severity,
            occurrences=occurrences,
            trace_count=trace_count,
            fix_layer=fix_layer,
            users_affected=users_affected,
            sessions=sessions,
            first_seen=first_seen,
            last_seen=last_seen,
            trends=trends,
            assignees=assignees,
            model=model,
            model_version=model_version,
            project=project,
            project_id=project_id,
            environment=environment,
            eval_score=eval_score,
            trace_id=trace_id,
            external_issue_url=external_issue_url,
            external_issue_id=external_issue_id,
        )

        feed_list_row.additional_properties = d
        return feed_list_row

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
