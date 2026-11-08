from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.compare_preview_run_eval_request_config import (
        ComparePreviewRunEvalRequestConfig,
    )
    from ..models.compare_preview_run_eval_request_dataset_info import (
        ComparePreviewRunEvalRequestDatasetInfo,
    )


T = TypeVar("T", bound="ComparePreviewRunEvalRequest")


@_attrs_define
class ComparePreviewRunEvalRequest:
    """
    Attributes:
        config (ComparePreviewRunEvalRequestConfig):
        template_id (UUID):
        dataset_ids (list[UUID]):
        model (str | Unset):  Default: ''.
        dataset_info (ComparePreviewRunEvalRequestDatasetInfo | Unset):
        source (str | Unset):  Default: 'dataset_evaluation'.
    """

    config: ComparePreviewRunEvalRequestConfig
    template_id: UUID
    dataset_ids: list[UUID]
    model: str | Unset = ""
    dataset_info: ComparePreviewRunEvalRequestDatasetInfo | Unset = UNSET
    source: str | Unset = "dataset_evaluation"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        config = self.config.to_dict()

        template_id = str(self.template_id)

        dataset_ids = []
        for dataset_ids_item_data in self.dataset_ids:
            dataset_ids_item = str(dataset_ids_item_data)
            dataset_ids.append(dataset_ids_item)

        model = self.model

        dataset_info: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dataset_info, Unset):
            dataset_info = self.dataset_info.to_dict()

        source = self.source

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "config": config,
                "template_id": template_id,
                "dataset_ids": dataset_ids,
            }
        )
        if model is not UNSET:
            field_dict["model"] = model
        if dataset_info is not UNSET:
            field_dict["dataset_info"] = dataset_info
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.compare_preview_run_eval_request_config import (
            ComparePreviewRunEvalRequestConfig,
        )
        from ..models.compare_preview_run_eval_request_dataset_info import (
            ComparePreviewRunEvalRequestDatasetInfo,
        )

        d = dict(src_dict)
        config = ComparePreviewRunEvalRequestConfig.from_dict(d.pop("config"))

        template_id = UUID(d.pop("template_id"))

        dataset_ids = []
        _dataset_ids = d.pop("dataset_ids")
        for dataset_ids_item_data in _dataset_ids:
            dataset_ids_item = UUID(dataset_ids_item_data)

            dataset_ids.append(dataset_ids_item)

        model = d.pop("model", UNSET)

        _dataset_info = d.pop("dataset_info", UNSET)
        dataset_info: ComparePreviewRunEvalRequestDatasetInfo | Unset
        if isinstance(_dataset_info, Unset):
            dataset_info = UNSET
        else:
            dataset_info = ComparePreviewRunEvalRequestDatasetInfo.from_dict(
                _dataset_info
            )

        source = d.pop("source", UNSET)

        compare_preview_run_eval_request = cls(
            config=config,
            template_id=template_id,
            dataset_ids=dataset_ids,
            model=model,
            dataset_info=dataset_info,
            source=source,
        )

        compare_preview_run_eval_request.additional_properties = d
        return compare_preview_run_eval_request

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
