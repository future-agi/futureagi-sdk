from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.user_alert_monitor_metric_type import UserAlertMonitorMetricType
from ..models.user_alert_monitor_threshold_operator import (
    UserAlertMonitorThresholdOperator,
)
from ..models.user_alert_monitor_threshold_type import UserAlertMonitorThresholdType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user_alert_monitor_filters import UserAlertMonitorFilters
    from ..models.user_alert_monitor_logs import UserAlertMonitorLogs


T = TypeVar("T", bound="UserAlertMonitor")


@_attrs_define
class UserAlertMonitor:
    """
    Attributes:
        project (UUID):
        name (str):
        metric_type (UserAlertMonitorMetricType):
        threshold_operator (UserAlertMonitorThresholdOperator):
        organization (UUID):
        id (UUID | Unset):
        metric_name (str | Unset):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        deleted (bool | Unset):
        deleted_at (datetime.datetime | None | Unset):
        metric (None | str | Unset): Id of the evaluation template.
        threshold_type (UserAlertMonitorThresholdType | Unset): Method to set the threshold for the monitor (Static or
            Percentage change).
        threshold_metric_value (None | str | Unset): For choice and pass/fail evals, the specific metric value to
            monitor.
        critical_threshold_value (float | None | Unset):
        warning_threshold_value (float | None | Unset):
        alert_frequency (int | Unset): Frequency of alert checks in minutes.
        auto_threshold_time_window (int | Unset): For auto-thresholding. The time window in minutes to calculate the
            historical mean
        last_checked_at (datetime.datetime | None | Unset): The last time the monitor was checked for alerts.
        notification_emails (list[str] | Unset):
        slack_webhook_url (None | str | Unset):
        slack_notes (None | str | Unset):
        is_mute (bool | Unset):
        filters (UserAlertMonitorFilters | Unset):
        logs (list[UserAlertMonitorLogs] | None | Unset):
        workspace (None | Unset | UUID):
        created_by (None | Unset | UUID):
    """

    project: UUID
    name: str
    metric_type: UserAlertMonitorMetricType
    threshold_operator: UserAlertMonitorThresholdOperator
    organization: UUID
    id: UUID | Unset = UNSET
    metric_name: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted: bool | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    metric: None | str | Unset = UNSET
    threshold_type: UserAlertMonitorThresholdType | Unset = UNSET
    threshold_metric_value: None | str | Unset = UNSET
    critical_threshold_value: float | None | Unset = UNSET
    warning_threshold_value: float | None | Unset = UNSET
    alert_frequency: int | Unset = UNSET
    auto_threshold_time_window: int | Unset = UNSET
    last_checked_at: datetime.datetime | None | Unset = UNSET
    notification_emails: list[str] | Unset = UNSET
    slack_webhook_url: None | str | Unset = UNSET
    slack_notes: None | str | Unset = UNSET
    is_mute: bool | Unset = UNSET
    filters: UserAlertMonitorFilters | Unset = UNSET
    logs: list[UserAlertMonitorLogs] | None | Unset = UNSET
    workspace: None | Unset | UUID = UNSET
    created_by: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project = str(self.project)

        name = self.name

        metric_type = self.metric_type.value

        threshold_operator = self.threshold_operator.value

        organization = str(self.organization)

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        metric_name = self.metric_name

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted = self.deleted

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        metric: None | str | Unset
        if isinstance(self.metric, Unset):
            metric = UNSET
        else:
            metric = self.metric

        threshold_type: str | Unset = UNSET
        if not isinstance(self.threshold_type, Unset):
            threshold_type = self.threshold_type.value

        threshold_metric_value: None | str | Unset
        if isinstance(self.threshold_metric_value, Unset):
            threshold_metric_value = UNSET
        else:
            threshold_metric_value = self.threshold_metric_value

        critical_threshold_value: float | None | Unset
        if isinstance(self.critical_threshold_value, Unset):
            critical_threshold_value = UNSET
        else:
            critical_threshold_value = self.critical_threshold_value

        warning_threshold_value: float | None | Unset
        if isinstance(self.warning_threshold_value, Unset):
            warning_threshold_value = UNSET
        else:
            warning_threshold_value = self.warning_threshold_value

        alert_frequency = self.alert_frequency

        auto_threshold_time_window = self.auto_threshold_time_window

        last_checked_at: None | str | Unset
        if isinstance(self.last_checked_at, Unset):
            last_checked_at = UNSET
        elif isinstance(self.last_checked_at, datetime.datetime):
            last_checked_at = self.last_checked_at.isoformat()
        else:
            last_checked_at = self.last_checked_at

        notification_emails: list[str] | Unset = UNSET
        if not isinstance(self.notification_emails, Unset):
            notification_emails = self.notification_emails

        slack_webhook_url: None | str | Unset
        if isinstance(self.slack_webhook_url, Unset):
            slack_webhook_url = UNSET
        else:
            slack_webhook_url = self.slack_webhook_url

        slack_notes: None | str | Unset
        if isinstance(self.slack_notes, Unset):
            slack_notes = UNSET
        else:
            slack_notes = self.slack_notes

        is_mute = self.is_mute

        filters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = self.filters.to_dict()

        logs: list[dict[str, Any]] | None | Unset
        if isinstance(self.logs, Unset):
            logs = UNSET
        elif isinstance(self.logs, list):
            logs = []
            for logs_type_0_item_data in self.logs:
                logs_type_0_item = logs_type_0_item_data.to_dict()
                logs.append(logs_type_0_item)

        else:
            logs = self.logs

        workspace: None | str | Unset
        if isinstance(self.workspace, Unset):
            workspace = UNSET
        elif isinstance(self.workspace, UUID):
            workspace = str(self.workspace)
        else:
            workspace = self.workspace

        created_by: None | str | Unset
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        elif isinstance(self.created_by, UUID):
            created_by = str(self.created_by)
        else:
            created_by = self.created_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project": project,
                "name": name,
                "metric_type": metric_type,
                "threshold_operator": threshold_operator,
                "organization": organization,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if metric_name is not UNSET:
            field_dict["metric_name"] = metric_name
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if metric is not UNSET:
            field_dict["metric"] = metric
        if threshold_type is not UNSET:
            field_dict["threshold_type"] = threshold_type
        if threshold_metric_value is not UNSET:
            field_dict["threshold_metric_value"] = threshold_metric_value
        if critical_threshold_value is not UNSET:
            field_dict["critical_threshold_value"] = critical_threshold_value
        if warning_threshold_value is not UNSET:
            field_dict["warning_threshold_value"] = warning_threshold_value
        if alert_frequency is not UNSET:
            field_dict["alert_frequency"] = alert_frequency
        if auto_threshold_time_window is not UNSET:
            field_dict["auto_threshold_time_window"] = auto_threshold_time_window
        if last_checked_at is not UNSET:
            field_dict["last_checked_at"] = last_checked_at
        if notification_emails is not UNSET:
            field_dict["notification_emails"] = notification_emails
        if slack_webhook_url is not UNSET:
            field_dict["slack_webhook_url"] = slack_webhook_url
        if slack_notes is not UNSET:
            field_dict["slack_notes"] = slack_notes
        if is_mute is not UNSET:
            field_dict["is_mute"] = is_mute
        if filters is not UNSET:
            field_dict["filters"] = filters
        if logs is not UNSET:
            field_dict["logs"] = logs
        if workspace is not UNSET:
            field_dict["workspace"] = workspace
        if created_by is not UNSET:
            field_dict["created_by"] = created_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_alert_monitor_filters import UserAlertMonitorFilters
        from ..models.user_alert_monitor_logs import UserAlertMonitorLogs

        d = dict(src_dict)
        project = UUID(d.pop("project"))

        name = d.pop("name")

        metric_type = UserAlertMonitorMetricType(d.pop("metric_type"))

        threshold_operator = UserAlertMonitorThresholdOperator(
            d.pop("threshold_operator")
        )

        organization = UUID(d.pop("organization"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        metric_name = d.pop("metric_name", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        deleted = d.pop("deleted", UNSET)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        def _parse_metric(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        metric = _parse_metric(d.pop("metric", UNSET))

        _threshold_type = d.pop("threshold_type", UNSET)
        threshold_type: UserAlertMonitorThresholdType | Unset
        if isinstance(_threshold_type, Unset):
            threshold_type = UNSET
        else:
            threshold_type = UserAlertMonitorThresholdType(_threshold_type)

        def _parse_threshold_metric_value(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        threshold_metric_value = _parse_threshold_metric_value(
            d.pop("threshold_metric_value", UNSET)
        )

        def _parse_critical_threshold_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        critical_threshold_value = _parse_critical_threshold_value(
            d.pop("critical_threshold_value", UNSET)
        )

        def _parse_warning_threshold_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        warning_threshold_value = _parse_warning_threshold_value(
            d.pop("warning_threshold_value", UNSET)
        )

        alert_frequency = d.pop("alert_frequency", UNSET)

        auto_threshold_time_window = d.pop("auto_threshold_time_window", UNSET)

        def _parse_last_checked_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_checked_at_type_0 = isoparse(data)

                return last_checked_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_checked_at = _parse_last_checked_at(d.pop("last_checked_at", UNSET))

        notification_emails = cast(list[str], d.pop("notification_emails", UNSET))

        def _parse_slack_webhook_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        slack_webhook_url = _parse_slack_webhook_url(d.pop("slack_webhook_url", UNSET))

        def _parse_slack_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        slack_notes = _parse_slack_notes(d.pop("slack_notes", UNSET))

        is_mute = d.pop("is_mute", UNSET)

        _filters = d.pop("filters", UNSET)
        filters: UserAlertMonitorFilters | Unset
        if isinstance(_filters, Unset):
            filters = UNSET
        else:
            filters = UserAlertMonitorFilters.from_dict(_filters)

        def _parse_logs(data: object) -> list[UserAlertMonitorLogs] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                logs_type_0 = []
                _logs_type_0 = data
                for logs_type_0_item_data in _logs_type_0:
                    logs_type_0_item = UserAlertMonitorLogs.from_dict(
                        logs_type_0_item_data
                    )

                    logs_type_0.append(logs_type_0_item)

                return logs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[UserAlertMonitorLogs] | None | Unset, data)

        logs = _parse_logs(d.pop("logs", UNSET))

        def _parse_workspace(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                workspace_type_0 = UUID(data)

                return workspace_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        workspace = _parse_workspace(d.pop("workspace", UNSET))

        def _parse_created_by(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_by_type_0 = UUID(data)

                return created_by_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        user_alert_monitor = cls(
            project=project,
            name=name,
            metric_type=metric_type,
            threshold_operator=threshold_operator,
            organization=organization,
            id=id,
            metric_name=metric_name,
            created_at=created_at,
            updated_at=updated_at,
            deleted=deleted,
            deleted_at=deleted_at,
            metric=metric,
            threshold_type=threshold_type,
            threshold_metric_value=threshold_metric_value,
            critical_threshold_value=critical_threshold_value,
            warning_threshold_value=warning_threshold_value,
            alert_frequency=alert_frequency,
            auto_threshold_time_window=auto_threshold_time_window,
            last_checked_at=last_checked_at,
            notification_emails=notification_emails,
            slack_webhook_url=slack_webhook_url,
            slack_notes=slack_notes,
            is_mute=is_mute,
            filters=filters,
            logs=logs,
            workspace=workspace,
            created_by=created_by,
        )

        user_alert_monitor.additional_properties = d
        return user_alert_monitor

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
