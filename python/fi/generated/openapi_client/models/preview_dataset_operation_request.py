from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.preview_dataset_operation_request_config import (
        PreviewDatasetOperationRequestConfig,
    )


T = TypeVar("T", bound="PreviewDatasetOperationRequest")


@_attrs_define
class PreviewDatasetOperationRequest:
    """
    Attributes:
        column_id (UUID | Unset):
        json_key (str | Unset):
        labels (list[str] | Unset):
        instruction (str | Unset):
        language_model_id (str | Unset):
        config (PreviewDatasetOperationRequestConfig | Unset):
        code (str | Unset):
    """

    column_id: UUID | Unset = UNSET
    json_key: str | Unset = UNSET
    labels: list[str] | Unset = UNSET
    instruction: str | Unset = UNSET
    language_model_id: str | Unset = UNSET
    config: PreviewDatasetOperationRequestConfig | Unset = UNSET
    code: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_id: str | Unset = UNSET
        if not isinstance(self.column_id, Unset):
            column_id = str(self.column_id)

        json_key = self.json_key

        labels: list[str] | Unset = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels

        instruction = self.instruction

        language_model_id = self.language_model_id

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        code = self.code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if column_id is not UNSET:
            field_dict["column_id"] = column_id
        if json_key is not UNSET:
            field_dict["json_key"] = json_key
        if labels is not UNSET:
            field_dict["labels"] = labels
        if instruction is not UNSET:
            field_dict["instruction"] = instruction
        if language_model_id is not UNSET:
            field_dict["language_model_id"] = language_model_id
        if config is not UNSET:
            field_dict["config"] = config
        if code is not UNSET:
            field_dict["code"] = code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.preview_dataset_operation_request_config import (
            PreviewDatasetOperationRequestConfig,
        )

        d = dict(src_dict)
        _column_id = d.pop("column_id", UNSET)
        column_id: UUID | Unset
        if isinstance(_column_id, Unset):
            column_id = UNSET
        else:
            column_id = UUID(_column_id)

        json_key = d.pop("json_key", UNSET)

        labels = cast(list[str], d.pop("labels", UNSET))

        instruction = d.pop("instruction", UNSET)

        language_model_id = d.pop("language_model_id", UNSET)

        _config = d.pop("config", UNSET)
        config: PreviewDatasetOperationRequestConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = PreviewDatasetOperationRequestConfig.from_dict(_config)

        code = d.pop("code", UNSET)

        preview_dataset_operation_request = cls(
            column_id=column_id,
            json_key=json_key,
            labels=labels,
            instruction=instruction,
            language_model_id=language_model_id,
            config=config,
            code=code,
        )

        preview_dataset_operation_request.additional_properties = d
        return preview_dataset_operation_request

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
