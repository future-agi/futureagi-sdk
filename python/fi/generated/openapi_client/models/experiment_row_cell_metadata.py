from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_row_cell_inner_metadata import (
        ExperimentRowCellInnerMetadata,
    )
    from ..models.experiment_row_cell_metadata_cost import ExperimentRowCellMetadataCost


T = TypeVar("T", bound="ExperimentRowCellMetadata")


@_attrs_define
class ExperimentRowCellMetadata:
    """
    Attributes:
        response_time_ms (float | None | Unset):
        token_count (int | None | Unset):
        cost (ExperimentRowCellMetadataCost | Unset):
        cell_metadata (ExperimentRowCellInnerMetadata | Unset):
        reason (None | str | Unset):
    """

    response_time_ms: float | None | Unset = UNSET
    token_count: int | None | Unset = UNSET
    cost: ExperimentRowCellMetadataCost | Unset = UNSET
    cell_metadata: ExperimentRowCellInnerMetadata | Unset = UNSET
    reason: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        response_time_ms: float | None | Unset
        if isinstance(self.response_time_ms, Unset):
            response_time_ms = UNSET
        else:
            response_time_ms = self.response_time_ms

        token_count: int | None | Unset
        if isinstance(self.token_count, Unset):
            token_count = UNSET
        else:
            token_count = self.token_count

        cost: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cost, Unset):
            cost = self.cost.to_dict()

        cell_metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cell_metadata, Unset):
            cell_metadata = self.cell_metadata.to_dict()

        reason: None | str | Unset
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if response_time_ms is not UNSET:
            field_dict["response_time_ms"] = response_time_ms
        if token_count is not UNSET:
            field_dict["token_count"] = token_count
        if cost is not UNSET:
            field_dict["cost"] = cost
        if cell_metadata is not UNSET:
            field_dict["cell_metadata"] = cell_metadata
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_row_cell_inner_metadata import (
            ExperimentRowCellInnerMetadata,
        )
        from ..models.experiment_row_cell_metadata_cost import (
            ExperimentRowCellMetadataCost,
        )

        d = dict(src_dict)

        def _parse_response_time_ms(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        response_time_ms = _parse_response_time_ms(d.pop("response_time_ms", UNSET))

        def _parse_token_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        token_count = _parse_token_count(d.pop("token_count", UNSET))

        _cost = d.pop("cost", UNSET)
        cost: ExperimentRowCellMetadataCost | Unset
        if isinstance(_cost, Unset):
            cost = UNSET
        else:
            cost = ExperimentRowCellMetadataCost.from_dict(_cost)

        _cell_metadata = d.pop("cell_metadata", UNSET)
        cell_metadata: ExperimentRowCellInnerMetadata | Unset
        if isinstance(_cell_metadata, Unset):
            cell_metadata = UNSET
        else:
            cell_metadata = ExperimentRowCellInnerMetadata.from_dict(_cell_metadata)

        def _parse_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reason = _parse_reason(d.pop("reason", UNSET))

        experiment_row_cell_metadata = cls(
            response_time_ms=response_time_ms,
            token_count=token_count,
            cost=cost,
            cell_metadata=cell_metadata,
            reason=reason,
        )

        experiment_row_cell_metadata.additional_properties = d
        return experiment_row_cell_metadata

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
