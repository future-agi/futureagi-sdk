from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.experiment_list_v2_experiment_type import ExperimentListV2ExperimentType
from ..models.experiment_list_v2_status import ExperimentListV2Status
from ..types import UNSET, Unset

T = TypeVar("T", bound="ExperimentListV2")


@_attrs_define
class ExperimentListV2:
    """
    Attributes:
        name (str):
        dataset (UUID):
        id (UUID | Unset):
        status (ExperimentListV2Status | Unset):
        experiment_type (ExperimentListV2ExperimentType | Unset): Determines how the experiment executes: llm, tts, stt,
            or image.
        eval_templates_count (str | Unset):
        created_at (datetime.datetime | Unset):
        models_count (str | Unset):
        agents_count (str | Unset):
    """

    name: str
    dataset: UUID
    id: UUID | Unset = UNSET
    status: ExperimentListV2Status | Unset = UNSET
    experiment_type: ExperimentListV2ExperimentType | Unset = UNSET
    eval_templates_count: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    models_count: str | Unset = UNSET
    agents_count: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        dataset = str(self.dataset)

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        experiment_type: str | Unset = UNSET
        if not isinstance(self.experiment_type, Unset):
            experiment_type = self.experiment_type.value

        eval_templates_count = self.eval_templates_count

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        models_count = self.models_count

        agents_count = self.agents_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "dataset": dataset,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if status is not UNSET:
            field_dict["status"] = status
        if experiment_type is not UNSET:
            field_dict["experiment_type"] = experiment_type
        if eval_templates_count is not UNSET:
            field_dict["eval_templates_count"] = eval_templates_count
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if models_count is not UNSET:
            field_dict["models_count"] = models_count
        if agents_count is not UNSET:
            field_dict["agents_count"] = agents_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        dataset = UUID(d.pop("dataset"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _status = d.pop("status", UNSET)
        status: ExperimentListV2Status | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ExperimentListV2Status(_status)

        _experiment_type = d.pop("experiment_type", UNSET)
        experiment_type: ExperimentListV2ExperimentType | Unset
        if isinstance(_experiment_type, Unset):
            experiment_type = UNSET
        else:
            experiment_type = ExperimentListV2ExperimentType(_experiment_type)

        eval_templates_count = d.pop("eval_templates_count", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        models_count = d.pop("models_count", UNSET)

        agents_count = d.pop("agents_count", UNSET)

        experiment_list_v2 = cls(
            name=name,
            dataset=dataset,
            id=id,
            status=status,
            experiment_type=experiment_type,
            eval_templates_count=eval_templates_count,
            created_at=created_at,
            models_count=models_count,
            agents_count=agents_count,
        )

        experiment_list_v2.additional_properties = d
        return experiment_list_v2

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
