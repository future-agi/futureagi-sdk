from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.preview_dataset_operation_result_item_details import (
        PreviewDatasetOperationResultItemDetails,
    )
    from ..models.preview_dataset_operation_result_item_input import (
        PreviewDatasetOperationResultItemInput,
    )
    from ..models.preview_dataset_operation_result_item_output import (
        PreviewDatasetOperationResultItemOutput,
    )


T = TypeVar("T", bound="PreviewDatasetOperationResultItem")


@_attrs_define
class PreviewDatasetOperationResultItem:
    """
    Attributes:
        row_id (UUID):
        input_ (PreviewDatasetOperationResultItemInput | Unset):
        output (PreviewDatasetOperationResultItemOutput | Unset):
        details (PreviewDatasetOperationResultItemDetails | Unset):
    """

    row_id: UUID
    input_: PreviewDatasetOperationResultItemInput | Unset = UNSET
    output: PreviewDatasetOperationResultItemOutput | Unset = UNSET
    details: PreviewDatasetOperationResultItemDetails | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        row_id = str(self.row_id)

        input_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.input_, Unset):
            input_ = self.input_.to_dict()

        output: dict[str, Any] | Unset = UNSET
        if not isinstance(self.output, Unset):
            output = self.output.to_dict()

        details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.details, Unset):
            details = self.details.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "row_id": row_id,
            }
        )
        if input_ is not UNSET:
            field_dict["input"] = input_
        if output is not UNSET:
            field_dict["output"] = output
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.preview_dataset_operation_result_item_details import (
            PreviewDatasetOperationResultItemDetails,
        )
        from ..models.preview_dataset_operation_result_item_input import (
            PreviewDatasetOperationResultItemInput,
        )
        from ..models.preview_dataset_operation_result_item_output import (
            PreviewDatasetOperationResultItemOutput,
        )

        d = dict(src_dict)
        row_id = UUID(d.pop("row_id"))

        _input_ = d.pop("input", UNSET)
        input_: PreviewDatasetOperationResultItemInput | Unset
        if isinstance(_input_, Unset):
            input_ = UNSET
        else:
            input_ = PreviewDatasetOperationResultItemInput.from_dict(_input_)

        _output = d.pop("output", UNSET)
        output: PreviewDatasetOperationResultItemOutput | Unset
        if isinstance(_output, Unset):
            output = UNSET
        else:
            output = PreviewDatasetOperationResultItemOutput.from_dict(_output)

        _details = d.pop("details", UNSET)
        details: PreviewDatasetOperationResultItemDetails | Unset
        if isinstance(_details, Unset):
            details = UNSET
        else:
            details = PreviewDatasetOperationResultItemDetails.from_dict(_details)

        preview_dataset_operation_result_item = cls(
            row_id=row_id,
            input_=input_,
            output=output,
            details=details,
        )

        preview_dataset_operation_result_item.additional_properties = d
        return preview_dataset_operation_result_item

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
