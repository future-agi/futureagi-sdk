from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.automation_rule_source_type import AutomationRuleSourceType
from ..models.automation_rule_trigger_frequency import AutomationRuleTriggerFrequency
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.automation_rule_conditions import AutomationRuleConditions


T = TypeVar("T", bound="AutomationRule")


@_attrs_define
class AutomationRule:
    """
    Attributes:
        name (str):
        source_type (AutomationRuleSourceType):
        id (UUID | Unset):
        queue (UUID | Unset):
        conditions (AutomationRuleConditions | Unset):
        enabled (bool | Unset):
        trigger_frequency (AutomationRuleTriggerFrequency | Unset):
        organization (UUID | Unset):
        created_by (None | Unset | UUID):
        created_by_name (str | Unset):
        last_triggered_at (datetime.datetime | None | Unset):
        trigger_count (int | Unset):
        created_at (datetime.datetime | Unset):
    """

    name: str
    source_type: AutomationRuleSourceType
    id: UUID | Unset = UNSET
    queue: UUID | Unset = UNSET
    conditions: AutomationRuleConditions | Unset = UNSET
    enabled: bool | Unset = UNSET
    trigger_frequency: AutomationRuleTriggerFrequency | Unset = UNSET
    organization: UUID | Unset = UNSET
    created_by: None | Unset | UUID = UNSET
    created_by_name: str | Unset = UNSET
    last_triggered_at: datetime.datetime | None | Unset = UNSET
    trigger_count: int | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        source_type = self.source_type.value

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        queue: str | Unset = UNSET
        if not isinstance(self.queue, Unset):
            queue = str(self.queue)

        conditions: dict[str, Any] | Unset = UNSET
        if not isinstance(self.conditions, Unset):
            conditions = self.conditions.to_dict()

        enabled = self.enabled

        trigger_frequency: str | Unset = UNSET
        if not isinstance(self.trigger_frequency, Unset):
            trigger_frequency = self.trigger_frequency.value

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        created_by: None | str | Unset
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        elif isinstance(self.created_by, UUID):
            created_by = str(self.created_by)
        else:
            created_by = self.created_by

        created_by_name = self.created_by_name

        last_triggered_at: None | str | Unset
        if isinstance(self.last_triggered_at, Unset):
            last_triggered_at = UNSET
        elif isinstance(self.last_triggered_at, datetime.datetime):
            last_triggered_at = self.last_triggered_at.isoformat()
        else:
            last_triggered_at = self.last_triggered_at

        trigger_count = self.trigger_count

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "source_type": source_type,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if queue is not UNSET:
            field_dict["queue"] = queue
        if conditions is not UNSET:
            field_dict["conditions"] = conditions
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if trigger_frequency is not UNSET:
            field_dict["trigger_frequency"] = trigger_frequency
        if organization is not UNSET:
            field_dict["organization"] = organization
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if created_by_name is not UNSET:
            field_dict["created_by_name"] = created_by_name
        if last_triggered_at is not UNSET:
            field_dict["last_triggered_at"] = last_triggered_at
        if trigger_count is not UNSET:
            field_dict["trigger_count"] = trigger_count
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.automation_rule_conditions import AutomationRuleConditions

        d = dict(src_dict)
        name = d.pop("name")

        source_type = AutomationRuleSourceType(d.pop("source_type"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _queue = d.pop("queue", UNSET)
        queue: UUID | Unset
        if isinstance(_queue, Unset):
            queue = UNSET
        else:
            queue = UUID(_queue)

        _conditions = d.pop("conditions", UNSET)
        conditions: AutomationRuleConditions | Unset
        if isinstance(_conditions, Unset):
            conditions = UNSET
        else:
            conditions = AutomationRuleConditions.from_dict(_conditions)

        enabled = d.pop("enabled", UNSET)

        _trigger_frequency = d.pop("trigger_frequency", UNSET)
        trigger_frequency: AutomationRuleTriggerFrequency | Unset
        if isinstance(_trigger_frequency, Unset):
            trigger_frequency = UNSET
        else:
            trigger_frequency = AutomationRuleTriggerFrequency(_trigger_frequency)

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

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

        created_by_name = d.pop("created_by_name", UNSET)

        def _parse_last_triggered_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_triggered_at_type_0 = isoparse(data)

                return last_triggered_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_triggered_at = _parse_last_triggered_at(d.pop("last_triggered_at", UNSET))

        trigger_count = d.pop("trigger_count", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        automation_rule = cls(
            name=name,
            source_type=source_type,
            id=id,
            queue=queue,
            conditions=conditions,
            enabled=enabled,
            trigger_frequency=trigger_frequency,
            organization=organization,
            created_by=created_by,
            created_by_name=created_by_name,
            last_triggered_at=last_triggered_at,
            trigger_count=trigger_count,
            created_at=created_at,
        )

        automation_rule.additional_properties = d
        return automation_rule

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
