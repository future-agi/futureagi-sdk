from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.external_run_create_request_metadata import (
        ExternalRunCreateRequestMetadata,
    )
    from ..models.external_run_create_request_model_config import (
        ExternalRunCreateRequestModelConfig,
    )
    from ..models.external_run_identity import ExternalRunIdentity


T = TypeVar("T", bound="ExternalRunCreateRequest")


@_attrs_define
class ExternalRunCreateRequest:
    """
    Attributes:
        run_id (UUID):
        dataset_version_id (UUID):
        expected_items (list[ExternalRunIdentity]):
        evaluator_metric_ids (list[UUID] | Unset):
        experiment_id (None | Unset | UUID):
        model_config (ExternalRunCreateRequestModelConfig | Unset):
        metadata (ExternalRunCreateRequestMetadata | Unset):
    """

    run_id: UUID
    dataset_version_id: UUID
    expected_items: list[ExternalRunIdentity]
    evaluator_metric_ids: list[UUID] | Unset = UNSET
    experiment_id: None | Unset | UUID = UNSET
    model_config: ExternalRunCreateRequestModelConfig | Unset = UNSET
    metadata: ExternalRunCreateRequestMetadata | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        run_id = str(self.run_id)

        dataset_version_id = str(self.dataset_version_id)

        expected_items = []
        for expected_items_item_data in self.expected_items:
            expected_items_item = expected_items_item_data.to_dict()
            expected_items.append(expected_items_item)

        evaluator_metric_ids: list[str] | Unset = UNSET
        if not isinstance(self.evaluator_metric_ids, Unset):
            evaluator_metric_ids = []
            for evaluator_metric_ids_item_data in self.evaluator_metric_ids:
                evaluator_metric_ids_item = str(evaluator_metric_ids_item_data)
                evaluator_metric_ids.append(evaluator_metric_ids_item)

        experiment_id: None | str | Unset
        if isinstance(self.experiment_id, Unset):
            experiment_id = UNSET
        elif isinstance(self.experiment_id, UUID):
            experiment_id = str(self.experiment_id)
        else:
            experiment_id = self.experiment_id

        model_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.model_config, Unset):
            model_config = self.model_config.to_dict()

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "run_id": run_id,
                "dataset_version_id": dataset_version_id,
                "expected_items": expected_items,
            }
        )
        if evaluator_metric_ids is not UNSET:
            field_dict["evaluator_metric_ids"] = evaluator_metric_ids
        if experiment_id is not UNSET:
            field_dict["experiment_id"] = experiment_id
        if model_config is not UNSET:
            field_dict["model_config"] = model_config
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.external_run_create_request_metadata import (
            ExternalRunCreateRequestMetadata,
        )
        from ..models.external_run_create_request_model_config import (
            ExternalRunCreateRequestModelConfig,
        )
        from ..models.external_run_identity import ExternalRunIdentity

        d = dict(src_dict)
        run_id = UUID(d.pop("run_id"))

        dataset_version_id = UUID(d.pop("dataset_version_id"))

        expected_items = []
        _expected_items = d.pop("expected_items")
        for expected_items_item_data in _expected_items:
            expected_items_item = ExternalRunIdentity.from_dict(
                expected_items_item_data
            )

            expected_items.append(expected_items_item)

        _evaluator_metric_ids = d.pop("evaluator_metric_ids", UNSET)
        evaluator_metric_ids: list[UUID] | Unset = UNSET
        if _evaluator_metric_ids is not UNSET:
            evaluator_metric_ids = []
            for evaluator_metric_ids_item_data in _evaluator_metric_ids:
                evaluator_metric_ids_item = UUID(evaluator_metric_ids_item_data)

                evaluator_metric_ids.append(evaluator_metric_ids_item)

        def _parse_experiment_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                experiment_id_type_0 = UUID(data)

                return experiment_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        experiment_id = _parse_experiment_id(d.pop("experiment_id", UNSET))

        _model_config = d.pop("model_config", UNSET)
        model_config: ExternalRunCreateRequestModelConfig | Unset
        if isinstance(_model_config, Unset):
            model_config = UNSET
        else:
            model_config = ExternalRunCreateRequestModelConfig.from_dict(_model_config)

        _metadata = d.pop("metadata", UNSET)
        metadata: ExternalRunCreateRequestMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ExternalRunCreateRequestMetadata.from_dict(_metadata)

        external_run_create_request = cls(
            run_id=run_id,
            dataset_version_id=dataset_version_id,
            expected_items=expected_items,
            evaluator_metric_ids=evaluator_metric_ids,
            experiment_id=experiment_id,
            model_config=model_config,
            metadata=metadata,
        )

        return external_run_create_request
