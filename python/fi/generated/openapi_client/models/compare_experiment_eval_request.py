from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.compare_experiment_eval_request_composite_weight_overrides import (
        CompareExperimentEvalRequestCompositeWeightOverrides,
    )
    from ..models.compare_experiment_eval_request_config import (
        CompareExperimentEvalRequestConfig,
    )


T = TypeVar("T", bound="CompareExperimentEvalRequest")


@_attrs_define
class CompareExperimentEvalRequest:
    """
    Attributes:
        name (str):
        template_id (str):
        config (CompareExperimentEvalRequestConfig):
        kb_id (UUID | Unset):
        error_localizer (bool | Unset):  Default: False.
        model (str | Unset):
        eval_type (str | Unset):
        run (bool | Unset):  Default: False.
        save_as_template (bool | Unset):  Default: False.
        experiment_id (UUID | Unset):
        composite_weight_overrides (CompareExperimentEvalRequestCompositeWeightOverrides | Unset):
        dataset_ids (list[UUID] | Unset):
    """

    name: str
    template_id: str
    config: CompareExperimentEvalRequestConfig
    kb_id: UUID | Unset = UNSET
    error_localizer: bool | Unset = False
    model: str | Unset = UNSET
    eval_type: str | Unset = UNSET
    run: bool | Unset = False
    save_as_template: bool | Unset = False
    experiment_id: UUID | Unset = UNSET
    composite_weight_overrides: (
        CompareExperimentEvalRequestCompositeWeightOverrides | Unset
    ) = UNSET
    dataset_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        template_id = self.template_id

        config = self.config.to_dict()

        kb_id: str | Unset = UNSET
        if not isinstance(self.kb_id, Unset):
            kb_id = str(self.kb_id)

        error_localizer = self.error_localizer

        model = self.model

        eval_type = self.eval_type

        run = self.run

        save_as_template = self.save_as_template

        experiment_id: str | Unset = UNSET
        if not isinstance(self.experiment_id, Unset):
            experiment_id = str(self.experiment_id)

        composite_weight_overrides: dict[str, Any] | Unset = UNSET
        if not isinstance(self.composite_weight_overrides, Unset):
            composite_weight_overrides = self.composite_weight_overrides.to_dict()

        dataset_ids: list[str] | Unset = UNSET
        if not isinstance(self.dataset_ids, Unset):
            dataset_ids = []
            for dataset_ids_item_data in self.dataset_ids:
                dataset_ids_item = str(dataset_ids_item_data)
                dataset_ids.append(dataset_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "template_id": template_id,
                "config": config,
            }
        )
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if model is not UNSET:
            field_dict["model"] = model
        if eval_type is not UNSET:
            field_dict["eval_type"] = eval_type
        if run is not UNSET:
            field_dict["run"] = run
        if save_as_template is not UNSET:
            field_dict["save_as_template"] = save_as_template
        if experiment_id is not UNSET:
            field_dict["experiment_id"] = experiment_id
        if composite_weight_overrides is not UNSET:
            field_dict["composite_weight_overrides"] = composite_weight_overrides
        if dataset_ids is not UNSET:
            field_dict["dataset_ids"] = dataset_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.compare_experiment_eval_request_composite_weight_overrides import (
            CompareExperimentEvalRequestCompositeWeightOverrides,
        )
        from ..models.compare_experiment_eval_request_config import (
            CompareExperimentEvalRequestConfig,
        )

        d = dict(src_dict)
        name = d.pop("name")

        template_id = d.pop("template_id")

        config = CompareExperimentEvalRequestConfig.from_dict(d.pop("config"))

        _kb_id = d.pop("kb_id", UNSET)
        kb_id: UUID | Unset
        if isinstance(_kb_id, Unset):
            kb_id = UNSET
        else:
            kb_id = UUID(_kb_id)

        error_localizer = d.pop("error_localizer", UNSET)

        model = d.pop("model", UNSET)

        eval_type = d.pop("eval_type", UNSET)

        run = d.pop("run", UNSET)

        save_as_template = d.pop("save_as_template", UNSET)

        _experiment_id = d.pop("experiment_id", UNSET)
        experiment_id: UUID | Unset
        if isinstance(_experiment_id, Unset):
            experiment_id = UNSET
        else:
            experiment_id = UUID(_experiment_id)

        _composite_weight_overrides = d.pop("composite_weight_overrides", UNSET)
        composite_weight_overrides: (
            CompareExperimentEvalRequestCompositeWeightOverrides | Unset
        )
        if isinstance(_composite_weight_overrides, Unset):
            composite_weight_overrides = UNSET
        else:
            composite_weight_overrides = (
                CompareExperimentEvalRequestCompositeWeightOverrides.from_dict(
                    _composite_weight_overrides
                )
            )

        _dataset_ids = d.pop("dataset_ids", UNSET)
        dataset_ids: list[UUID] | Unset = UNSET
        if _dataset_ids is not UNSET:
            dataset_ids = []
            for dataset_ids_item_data in _dataset_ids:
                dataset_ids_item = UUID(dataset_ids_item_data)

                dataset_ids.append(dataset_ids_item)

        compare_experiment_eval_request = cls(
            name=name,
            template_id=template_id,
            config=config,
            kb_id=kb_id,
            error_localizer=error_localizer,
            model=model,
            eval_type=eval_type,
            run=run,
            save_as_template=save_as_template,
            experiment_id=experiment_id,
            composite_weight_overrides=composite_weight_overrides,
            dataset_ids=dataset_ids,
        )

        compare_experiment_eval_request.additional_properties = d
        return compare_experiment_eval_request

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
