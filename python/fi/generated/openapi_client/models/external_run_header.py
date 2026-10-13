from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.external_run_header_status import ExternalRunHeaderStatus
from ..models.external_run_header_task_kind import ExternalRunHeaderTaskKind

if TYPE_CHECKING:
    from ..models.external_run_binding import ExternalRunBinding
    from ..models.external_run_header_metadata import ExternalRunHeaderMetadata
    from ..models.external_run_header_model_config import ExternalRunHeaderModelConfig
    from ..models.external_run_identity import ExternalRunIdentity


T = TypeVar("T", bound="ExternalRunHeader")


@_attrs_define
class ExternalRunHeader:
    """
    Attributes:
        id (UUID):
        dataset_version_id (UUID):
        experiment_id (None | UUID):
        task_kind (ExternalRunHeaderTaskKind):
        status (ExternalRunHeaderStatus):
        expected_items (list[ExternalRunIdentity]):
        evaluator_bindings (list[ExternalRunBinding]):
        model_config (ExternalRunHeaderModelConfig):
        metadata (ExternalRunHeaderMetadata):
        started_at (datetime.datetime | None):
        completed_at (datetime.datetime | None):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: UUID
    dataset_version_id: UUID
    experiment_id: None | UUID
    task_kind: ExternalRunHeaderTaskKind
    status: ExternalRunHeaderStatus
    expected_items: list[ExternalRunIdentity]
    evaluator_bindings: list[ExternalRunBinding]
    model_config: ExternalRunHeaderModelConfig
    metadata: ExternalRunHeaderMetadata
    started_at: datetime.datetime | None
    completed_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        dataset_version_id = str(self.dataset_version_id)

        experiment_id: None | str
        if isinstance(self.experiment_id, UUID):
            experiment_id = str(self.experiment_id)
        else:
            experiment_id = self.experiment_id

        task_kind = self.task_kind.value

        status = self.status.value

        expected_items = []
        for expected_items_item_data in self.expected_items:
            expected_items_item = expected_items_item_data.to_dict()
            expected_items.append(expected_items_item)

        evaluator_bindings = []
        for evaluator_bindings_item_data in self.evaluator_bindings:
            evaluator_bindings_item = evaluator_bindings_item_data.to_dict()
            evaluator_bindings.append(evaluator_bindings_item)

        model_config = self.model_config.to_dict()

        metadata = self.metadata.to_dict()

        started_at: None | str
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        completed_at: None | str
        if isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "dataset_version_id": dataset_version_id,
                "experiment_id": experiment_id,
                "task_kind": task_kind,
                "status": status,
                "expected_items": expected_items,
                "evaluator_bindings": evaluator_bindings,
                "model_config": model_config,
                "metadata": metadata,
                "started_at": started_at,
                "completed_at": completed_at,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.external_run_binding import ExternalRunBinding
        from ..models.external_run_header_metadata import ExternalRunHeaderMetadata
        from ..models.external_run_header_model_config import (
            ExternalRunHeaderModelConfig,
        )
        from ..models.external_run_identity import ExternalRunIdentity

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        dataset_version_id = UUID(d.pop("dataset_version_id"))

        def _parse_experiment_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                experiment_id_type_0 = UUID(data)

                return experiment_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        experiment_id = _parse_experiment_id(d.pop("experiment_id"))

        task_kind = ExternalRunHeaderTaskKind(d.pop("task_kind"))

        status = ExternalRunHeaderStatus(d.pop("status"))

        expected_items = []
        _expected_items = d.pop("expected_items")
        for expected_items_item_data in _expected_items:
            expected_items_item = ExternalRunIdentity.from_dict(
                expected_items_item_data
            )

            expected_items.append(expected_items_item)

        evaluator_bindings = []
        _evaluator_bindings = d.pop("evaluator_bindings")
        for evaluator_bindings_item_data in _evaluator_bindings:
            evaluator_bindings_item = ExternalRunBinding.from_dict(
                evaluator_bindings_item_data
            )

            evaluator_bindings.append(evaluator_bindings_item)

        model_config = ExternalRunHeaderModelConfig.from_dict(d.pop("model_config"))

        metadata = ExternalRunHeaderMetadata.from_dict(d.pop("metadata"))

        def _parse_started_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        started_at = _parse_started_at(d.pop("started_at"))

        def _parse_completed_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        completed_at = _parse_completed_at(d.pop("completed_at"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        external_run_header = cls(
            id=id,
            dataset_version_id=dataset_version_id,
            experiment_id=experiment_id,
            task_kind=task_kind,
            status=status,
            expected_items=expected_items,
            evaluator_bindings=evaluator_bindings,
            model_config=model_config,
            metadata=metadata,
            started_at=started_at,
            completed_at=completed_at,
            created_at=created_at,
            updated_at=updated_at,
        )

        external_run_header.additional_properties = d
        return external_run_header

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
