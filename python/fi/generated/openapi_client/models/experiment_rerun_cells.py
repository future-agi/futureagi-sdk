from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.rerun_cell_entry import RerunCellEntry


T = TypeVar("T", bound="ExperimentRerunCells")


@_attrs_define
class ExperimentRerunCells:
    """
    Attributes:
        source_ids (list[UUID] | Unset):
        cells (list[RerunCellEntry] | Unset):
        user_eval_metric_ids (list[UUID] | Unset):
        failed_only (bool | Unset):  Default: False.
    """

    source_ids: list[UUID] | Unset = UNSET
    cells: list[RerunCellEntry] | Unset = UNSET
    user_eval_metric_ids: list[UUID] | Unset = UNSET
    failed_only: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_ids: list[str] | Unset = UNSET
        if not isinstance(self.source_ids, Unset):
            source_ids = []
            for source_ids_item_data in self.source_ids:
                source_ids_item = str(source_ids_item_data)
                source_ids.append(source_ids_item)

        cells: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.cells, Unset):
            cells = []
            for cells_item_data in self.cells:
                cells_item = cells_item_data.to_dict()
                cells.append(cells_item)

        user_eval_metric_ids: list[str] | Unset = UNSET
        if not isinstance(self.user_eval_metric_ids, Unset):
            user_eval_metric_ids = []
            for user_eval_metric_ids_item_data in self.user_eval_metric_ids:
                user_eval_metric_ids_item = str(user_eval_metric_ids_item_data)
                user_eval_metric_ids.append(user_eval_metric_ids_item)

        failed_only = self.failed_only

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if source_ids is not UNSET:
            field_dict["source_ids"] = source_ids
        if cells is not UNSET:
            field_dict["cells"] = cells
        if user_eval_metric_ids is not UNSET:
            field_dict["user_eval_metric_ids"] = user_eval_metric_ids
        if failed_only is not UNSET:
            field_dict["failed_only"] = failed_only

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.rerun_cell_entry import RerunCellEntry

        d = dict(src_dict)
        _source_ids = d.pop("source_ids", UNSET)
        source_ids: list[UUID] | Unset = UNSET
        if _source_ids is not UNSET:
            source_ids = []
            for source_ids_item_data in _source_ids:
                source_ids_item = UUID(source_ids_item_data)

                source_ids.append(source_ids_item)

        _cells = d.pop("cells", UNSET)
        cells: list[RerunCellEntry] | Unset = UNSET
        if _cells is not UNSET:
            cells = []
            for cells_item_data in _cells:
                cells_item = RerunCellEntry.from_dict(cells_item_data)

                cells.append(cells_item)

        _user_eval_metric_ids = d.pop("user_eval_metric_ids", UNSET)
        user_eval_metric_ids: list[UUID] | Unset = UNSET
        if _user_eval_metric_ids is not UNSET:
            user_eval_metric_ids = []
            for user_eval_metric_ids_item_data in _user_eval_metric_ids:
                user_eval_metric_ids_item = UUID(user_eval_metric_ids_item_data)

                user_eval_metric_ids.append(user_eval_metric_ids_item)

        failed_only = d.pop("failed_only", UNSET)

        experiment_rerun_cells = cls(
            source_ids=source_ids,
            cells=cells,
            user_eval_metric_ids=user_eval_metric_ids,
            failed_only=failed_only,
        )

        experiment_rerun_cells.additional_properties = d
        return experiment_rerun_cells

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
