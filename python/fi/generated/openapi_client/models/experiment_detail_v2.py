from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.experiment_detail_v2_experiment_type import (
    ExperimentDetailV2ExperimentType,
)
from ..models.experiment_detail_v2_status import ExperimentDetailV2Status
from ..types import UNSET, Unset

T = TypeVar("T", bound="ExperimentDetailV2")


@_attrs_define
class ExperimentDetailV2:
    """
    Attributes:
        name (str):
        id (UUID | Unset):
        dataset_id (UUID | Unset):
        column_id (None | Unset | UUID):
        experiment_type (ExperimentDetailV2ExperimentType | Unset): Determines how the experiment executes: llm, tts,
            stt, or image.
        status (ExperimentDetailV2Status | Unset):
        snapshot_dataset_id (None | Unset | UUID):
        prompt_configs (str | Unset):
        agent_configs (str | Unset):
        user_eval_metrics (str | Unset):
        created_at (datetime.datetime | Unset):
    """

    name: str
    id: UUID | Unset = UNSET
    dataset_id: UUID | Unset = UNSET
    column_id: None | Unset | UUID = UNSET
    experiment_type: ExperimentDetailV2ExperimentType | Unset = UNSET
    status: ExperimentDetailV2Status | Unset = UNSET
    snapshot_dataset_id: None | Unset | UUID = UNSET
    prompt_configs: str | Unset = UNSET
    agent_configs: str | Unset = UNSET
    user_eval_metrics: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        dataset_id: str | Unset = UNSET
        if not isinstance(self.dataset_id, Unset):
            dataset_id = str(self.dataset_id)

        column_id: None | str | Unset
        if isinstance(self.column_id, Unset):
            column_id = UNSET
        elif isinstance(self.column_id, UUID):
            column_id = str(self.column_id)
        else:
            column_id = self.column_id

        experiment_type: str | Unset = UNSET
        if not isinstance(self.experiment_type, Unset):
            experiment_type = self.experiment_type.value

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        snapshot_dataset_id: None | str | Unset
        if isinstance(self.snapshot_dataset_id, Unset):
            snapshot_dataset_id = UNSET
        elif isinstance(self.snapshot_dataset_id, UUID):
            snapshot_dataset_id = str(self.snapshot_dataset_id)
        else:
            snapshot_dataset_id = self.snapshot_dataset_id

        prompt_configs = self.prompt_configs

        agent_configs = self.agent_configs

        user_eval_metrics = self.user_eval_metrics

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if dataset_id is not UNSET:
            field_dict["dataset_id"] = dataset_id
        if column_id is not UNSET:
            field_dict["column_id"] = column_id
        if experiment_type is not UNSET:
            field_dict["experiment_type"] = experiment_type
        if status is not UNSET:
            field_dict["status"] = status
        if snapshot_dataset_id is not UNSET:
            field_dict["snapshot_dataset_id"] = snapshot_dataset_id
        if prompt_configs is not UNSET:
            field_dict["prompt_configs"] = prompt_configs
        if agent_configs is not UNSET:
            field_dict["agent_configs"] = agent_configs
        if user_eval_metrics is not UNSET:
            field_dict["user_eval_metrics"] = user_eval_metrics
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _dataset_id = d.pop("dataset_id", UNSET)
        dataset_id: UUID | Unset
        if isinstance(_dataset_id, Unset):
            dataset_id = UNSET
        else:
            dataset_id = UUID(_dataset_id)

        def _parse_column_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                column_id_type_0 = UUID(data)

                return column_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        column_id = _parse_column_id(d.pop("column_id", UNSET))

        _experiment_type = d.pop("experiment_type", UNSET)
        experiment_type: ExperimentDetailV2ExperimentType | Unset
        if isinstance(_experiment_type, Unset):
            experiment_type = UNSET
        else:
            experiment_type = ExperimentDetailV2ExperimentType(_experiment_type)

        _status = d.pop("status", UNSET)
        status: ExperimentDetailV2Status | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ExperimentDetailV2Status(_status)

        def _parse_snapshot_dataset_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                snapshot_dataset_id_type_0 = UUID(data)

                return snapshot_dataset_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        snapshot_dataset_id = _parse_snapshot_dataset_id(
            d.pop("snapshot_dataset_id", UNSET)
        )

        prompt_configs = d.pop("prompt_configs", UNSET)

        agent_configs = d.pop("agent_configs", UNSET)

        user_eval_metrics = d.pop("user_eval_metrics", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        experiment_detail_v2 = cls(
            name=name,
            id=id,
            dataset_id=dataset_id,
            column_id=column_id,
            experiment_type=experiment_type,
            status=status,
            snapshot_dataset_id=snapshot_dataset_id,
            prompt_configs=prompt_configs,
            agent_configs=agent_configs,
            user_eval_metrics=user_eval_metrics,
            created_at=created_at,
        )

        experiment_detail_v2.additional_properties = d
        return experiment_detail_v2

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
