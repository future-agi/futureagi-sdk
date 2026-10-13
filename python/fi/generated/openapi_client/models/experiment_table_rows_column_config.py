from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_table_rows_column_config_average_score import (
        ExperimentTableRowsColumnConfigAverageScore,
    )
    from ..models.experiment_table_rows_column_config_choices_map import (
        ExperimentTableRowsColumnConfigChoicesMap,
    )
    from ..models.experiment_table_rows_column_config_group import (
        ExperimentTableRowsColumnConfigGroup,
    )


T = TypeVar("T", bound="ExperimentTableRowsColumnConfig")


@_attrs_define
class ExperimentTableRowsColumnConfig:
    """
    Attributes:
        id (str):
        name (str):
        origin_type (str | Unset):
        data_type (str | Unset):
        status (str | Unset):
        group (ExperimentTableRowsColumnConfigGroup | Unset):
        average_score (ExperimentTableRowsColumnConfigAverageScore | Unset):
        dataset_id (str | Unset):
        choices_map (ExperimentTableRowsColumnConfigChoicesMap | Unset):
        is_base_column (bool | Unset):
        output_type (None | str | Unset):
        eval_template_id (None | str | Unset):
        source_id (str | Unset):
        is_agent (bool | Unset):
        is_final (bool | Unset):
    """

    id: str
    name: str
    origin_type: str | Unset = UNSET
    data_type: str | Unset = UNSET
    status: str | Unset = UNSET
    group: ExperimentTableRowsColumnConfigGroup | Unset = UNSET
    average_score: ExperimentTableRowsColumnConfigAverageScore | Unset = UNSET
    dataset_id: str | Unset = UNSET
    choices_map: ExperimentTableRowsColumnConfigChoicesMap | Unset = UNSET
    is_base_column: bool | Unset = UNSET
    output_type: None | str | Unset = UNSET
    eval_template_id: None | str | Unset = UNSET
    source_id: str | Unset = UNSET
    is_agent: bool | Unset = UNSET
    is_final: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        origin_type = self.origin_type

        data_type = self.data_type

        status = self.status

        group: dict[str, Any] | Unset = UNSET
        if not isinstance(self.group, Unset):
            group = self.group.to_dict()

        average_score: dict[str, Any] | Unset = UNSET
        if not isinstance(self.average_score, Unset):
            average_score = self.average_score.to_dict()

        dataset_id = self.dataset_id

        choices_map: dict[str, Any] | Unset = UNSET
        if not isinstance(self.choices_map, Unset):
            choices_map = self.choices_map.to_dict()

        is_base_column = self.is_base_column

        output_type: None | str | Unset
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        eval_template_id: None | str | Unset
        if isinstance(self.eval_template_id, Unset):
            eval_template_id = UNSET
        else:
            eval_template_id = self.eval_template_id

        source_id = self.source_id

        is_agent = self.is_agent

        is_final = self.is_final

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if origin_type is not UNSET:
            field_dict["origin_type"] = origin_type
        if data_type is not UNSET:
            field_dict["data_type"] = data_type
        if status is not UNSET:
            field_dict["status"] = status
        if group is not UNSET:
            field_dict["group"] = group
        if average_score is not UNSET:
            field_dict["average_score"] = average_score
        if dataset_id is not UNSET:
            field_dict["dataset_id"] = dataset_id
        if choices_map is not UNSET:
            field_dict["choices_map"] = choices_map
        if is_base_column is not UNSET:
            field_dict["is_base_column"] = is_base_column
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if eval_template_id is not UNSET:
            field_dict["eval_template_id"] = eval_template_id
        if source_id is not UNSET:
            field_dict["source_id"] = source_id
        if is_agent is not UNSET:
            field_dict["is_agent"] = is_agent
        if is_final is not UNSET:
            field_dict["is_final"] = is_final

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_table_rows_column_config_average_score import (
            ExperimentTableRowsColumnConfigAverageScore,
        )
        from ..models.experiment_table_rows_column_config_choices_map import (
            ExperimentTableRowsColumnConfigChoicesMap,
        )
        from ..models.experiment_table_rows_column_config_group import (
            ExperimentTableRowsColumnConfigGroup,
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        origin_type = d.pop("origin_type", UNSET)

        data_type = d.pop("data_type", UNSET)

        status = d.pop("status", UNSET)

        _group = d.pop("group", UNSET)
        group: ExperimentTableRowsColumnConfigGroup | Unset
        if isinstance(_group, Unset):
            group = UNSET
        else:
            group = ExperimentTableRowsColumnConfigGroup.from_dict(_group)

        _average_score = d.pop("average_score", UNSET)
        average_score: ExperimentTableRowsColumnConfigAverageScore | Unset
        if isinstance(_average_score, Unset):
            average_score = UNSET
        else:
            average_score = ExperimentTableRowsColumnConfigAverageScore.from_dict(
                _average_score
            )

        dataset_id = d.pop("dataset_id", UNSET)

        _choices_map = d.pop("choices_map", UNSET)
        choices_map: ExperimentTableRowsColumnConfigChoicesMap | Unset
        if isinstance(_choices_map, Unset):
            choices_map = UNSET
        else:
            choices_map = ExperimentTableRowsColumnConfigChoicesMap.from_dict(
                _choices_map
            )

        is_base_column = d.pop("is_base_column", UNSET)

        def _parse_output_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_eval_template_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_template_id = _parse_eval_template_id(d.pop("eval_template_id", UNSET))

        source_id = d.pop("source_id", UNSET)

        is_agent = d.pop("is_agent", UNSET)

        is_final = d.pop("is_final", UNSET)

        experiment_table_rows_column_config = cls(
            id=id,
            name=name,
            origin_type=origin_type,
            data_type=data_type,
            status=status,
            group=group,
            average_score=average_score,
            dataset_id=dataset_id,
            choices_map=choices_map,
            is_base_column=is_base_column,
            output_type=output_type,
            eval_template_id=eval_template_id,
            source_id=source_id,
            is_agent=is_agent,
            is_final=is_final,
        )

        experiment_table_rows_column_config.additional_properties = d
        return experiment_table_rows_column_config

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
