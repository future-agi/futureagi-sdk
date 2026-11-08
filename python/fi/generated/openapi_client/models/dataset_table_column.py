from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_table_column_choices_map import DatasetTableColumnChoicesMap
    from ..models.dataset_table_column_metadata import DatasetTableColumnMetadata


T = TypeVar("T", bound="DatasetTableColumn")


@_attrs_define
class DatasetTableColumn:
    """
    Attributes:
        id (str):
        name (str):
        data_type (None | str):
        is_visible (bool):
        is_frozen (bool | None):
        source_type (str):
        origin_type (None | str):
        source_id (None | str):
        order_index (int):
        status (None | str):
        average_score (float | None):
        reason_column (bool):
        is_numeric_eval (bool):
        is_numeric_eval_percentage (bool):
        metadata (DatasetTableColumnMetadata):
        choices_map (DatasetTableColumnChoicesMap):
        eval_tag (list[str] | Unset):
    """

    id: str
    name: str
    data_type: None | str
    is_visible: bool
    is_frozen: bool | None
    source_type: str
    origin_type: None | str
    source_id: None | str
    order_index: int
    status: None | str
    average_score: float | None
    reason_column: bool
    is_numeric_eval: bool
    is_numeric_eval_percentage: bool
    metadata: DatasetTableColumnMetadata
    choices_map: DatasetTableColumnChoicesMap
    eval_tag: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        data_type: None | str
        data_type = self.data_type

        is_visible = self.is_visible

        is_frozen: bool | None
        is_frozen = self.is_frozen

        source_type = self.source_type

        origin_type: None | str
        origin_type = self.origin_type

        source_id: None | str
        source_id = self.source_id

        order_index = self.order_index

        status: None | str
        status = self.status

        average_score: float | None
        average_score = self.average_score

        reason_column = self.reason_column

        is_numeric_eval = self.is_numeric_eval

        is_numeric_eval_percentage = self.is_numeric_eval_percentage

        metadata = self.metadata.to_dict()

        choices_map = self.choices_map.to_dict()

        eval_tag: list[str] | Unset = UNSET
        if not isinstance(self.eval_tag, Unset):
            eval_tag = self.eval_tag

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "data_type": data_type,
                "is_visible": is_visible,
                "is_frozen": is_frozen,
                "source_type": source_type,
                "origin_type": origin_type,
                "source_id": source_id,
                "order_index": order_index,
                "status": status,
                "average_score": average_score,
                "reason_column": reason_column,
                "is_numeric_eval": is_numeric_eval,
                "is_numeric_eval_percentage": is_numeric_eval_percentage,
                "metadata": metadata,
                "choices_map": choices_map,
            }
        )
        if eval_tag is not UNSET:
            field_dict["eval_tag"] = eval_tag

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_table_column_choices_map import (
            DatasetTableColumnChoicesMap,
        )
        from ..models.dataset_table_column_metadata import DatasetTableColumnMetadata

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        def _parse_data_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        data_type = _parse_data_type(d.pop("data_type"))

        is_visible = d.pop("is_visible")

        def _parse_is_frozen(data: object) -> bool | None:
            if data is None:
                return data
            return cast(bool | None, data)

        is_frozen = _parse_is_frozen(d.pop("is_frozen"))

        source_type = d.pop("source_type")

        def _parse_origin_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        origin_type = _parse_origin_type(d.pop("origin_type"))

        def _parse_source_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        source_id = _parse_source_id(d.pop("source_id"))

        order_index = d.pop("order_index")

        def _parse_status(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        status = _parse_status(d.pop("status"))

        def _parse_average_score(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        average_score = _parse_average_score(d.pop("average_score"))

        reason_column = d.pop("reason_column")

        is_numeric_eval = d.pop("is_numeric_eval")

        is_numeric_eval_percentage = d.pop("is_numeric_eval_percentage")

        metadata = DatasetTableColumnMetadata.from_dict(d.pop("metadata"))

        choices_map = DatasetTableColumnChoicesMap.from_dict(d.pop("choices_map"))

        eval_tag = cast(list[str], d.pop("eval_tag", UNSET))

        dataset_table_column = cls(
            id=id,
            name=name,
            data_type=data_type,
            is_visible=is_visible,
            is_frozen=is_frozen,
            source_type=source_type,
            origin_type=origin_type,
            source_id=source_id,
            order_index=order_index,
            status=status,
            average_score=average_score,
            reason_column=reason_column,
            is_numeric_eval=is_numeric_eval,
            is_numeric_eval_percentage=is_numeric_eval_percentage,
            metadata=metadata,
            choices_map=choices_map,
            eval_tag=eval_tag,
        )

        dataset_table_column.additional_properties = d
        return dataset_table_column

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
