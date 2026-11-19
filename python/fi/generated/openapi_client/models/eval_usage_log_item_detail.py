from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_usage_log_item_detail_input_variables import (
        EvalUsageLogItemDetailInputVariables,
    )
    from ..models.eval_usage_log_item_detail_mappings import (
        EvalUsageLogItemDetailMappings,
    )
    from ..models.eval_usage_log_item_detail_model import EvalUsageLogItemDetailModel
    from ..models.eval_usage_log_item_detail_output import EvalUsageLogItemDetailOutput


T = TypeVar("T", bound="EvalUsageLogItemDetail")


@_attrs_define
class EvalUsageLogItemDetail:
    """
    Attributes:
        input_variables (EvalUsageLogItemDetailInputVariables | Unset):
        output (EvalUsageLogItemDetailOutput | Unset):
        warnings (list[None | str] | Unset):
        mappings (EvalUsageLogItemDetailMappings | Unset):
        model (EvalUsageLogItemDetailModel | Unset): String or JSON object.
        version_id (None | str | Unset):
        version_number (int | None | Unset):
        children (list[None | str] | Unset):
        aggregation_function (None | str | Unset):
        total_children (int | None | Unset):
        completed_children (int | None | Unset):
        failed_children (int | None | Unset):
    """

    input_variables: EvalUsageLogItemDetailInputVariables | Unset = UNSET
    output: EvalUsageLogItemDetailOutput | Unset = UNSET
    warnings: list[None | str] | Unset = UNSET
    mappings: EvalUsageLogItemDetailMappings | Unset = UNSET
    model: EvalUsageLogItemDetailModel | Unset = UNSET
    version_id: None | str | Unset = UNSET
    version_number: int | None | Unset = UNSET
    children: list[None | str] | Unset = UNSET
    aggregation_function: None | str | Unset = UNSET
    total_children: int | None | Unset = UNSET
    completed_children: int | None | Unset = UNSET
    failed_children: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_variables: dict[str, Any] | Unset = UNSET
        if not isinstance(self.input_variables, Unset):
            input_variables = self.input_variables.to_dict()

        output: dict[str, Any] | Unset = UNSET
        if not isinstance(self.output, Unset):
            output = self.output.to_dict()

        warnings: list[None | str] | Unset = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = []
            for warnings_item_data in self.warnings:
                warnings_item: None | str
                warnings_item = warnings_item_data
                warnings.append(warnings_item)

        mappings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.mappings, Unset):
            mappings = self.mappings.to_dict()

        model: dict[str, Any] | Unset = UNSET
        if not isinstance(self.model, Unset):
            model = self.model.to_dict()

        version_id: None | str | Unset
        if isinstance(self.version_id, Unset):
            version_id = UNSET
        else:
            version_id = self.version_id

        version_number: int | None | Unset
        if isinstance(self.version_number, Unset):
            version_number = UNSET
        else:
            version_number = self.version_number

        children: list[None | str] | Unset = UNSET
        if not isinstance(self.children, Unset):
            children = []
            for children_item_data in self.children:
                children_item: None | str
                children_item = children_item_data
                children.append(children_item)

        aggregation_function: None | str | Unset
        if isinstance(self.aggregation_function, Unset):
            aggregation_function = UNSET
        else:
            aggregation_function = self.aggregation_function

        total_children: int | None | Unset
        if isinstance(self.total_children, Unset):
            total_children = UNSET
        else:
            total_children = self.total_children

        completed_children: int | None | Unset
        if isinstance(self.completed_children, Unset):
            completed_children = UNSET
        else:
            completed_children = self.completed_children

        failed_children: int | None | Unset
        if isinstance(self.failed_children, Unset):
            failed_children = UNSET
        else:
            failed_children = self.failed_children

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if input_variables is not UNSET:
            field_dict["input_variables"] = input_variables
        if output is not UNSET:
            field_dict["output"] = output
        if warnings is not UNSET:
            field_dict["warnings"] = warnings
        if mappings is not UNSET:
            field_dict["mappings"] = mappings
        if model is not UNSET:
            field_dict["model"] = model
        if version_id is not UNSET:
            field_dict["version_id"] = version_id
        if version_number is not UNSET:
            field_dict["version_number"] = version_number
        if children is not UNSET:
            field_dict["children"] = children
        if aggregation_function is not UNSET:
            field_dict["aggregation_function"] = aggregation_function
        if total_children is not UNSET:
            field_dict["total_children"] = total_children
        if completed_children is not UNSET:
            field_dict["completed_children"] = completed_children
        if failed_children is not UNSET:
            field_dict["failed_children"] = failed_children

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_usage_log_item_detail_input_variables import (
            EvalUsageLogItemDetailInputVariables,
        )
        from ..models.eval_usage_log_item_detail_mappings import (
            EvalUsageLogItemDetailMappings,
        )
        from ..models.eval_usage_log_item_detail_model import (
            EvalUsageLogItemDetailModel,
        )
        from ..models.eval_usage_log_item_detail_output import (
            EvalUsageLogItemDetailOutput,
        )

        d = dict(src_dict)
        _input_variables = d.pop("input_variables", UNSET)
        input_variables: EvalUsageLogItemDetailInputVariables | Unset
        if isinstance(_input_variables, Unset):
            input_variables = UNSET
        else:
            input_variables = EvalUsageLogItemDetailInputVariables.from_dict(
                _input_variables
            )

        _output = d.pop("output", UNSET)
        output: EvalUsageLogItemDetailOutput | Unset
        if isinstance(_output, Unset):
            output = UNSET
        else:
            output = EvalUsageLogItemDetailOutput.from_dict(_output)

        _warnings = d.pop("warnings", UNSET)
        warnings: list[None | str] | Unset = UNSET
        if _warnings is not UNSET:
            warnings = []
            for warnings_item_data in _warnings:

                def _parse_warnings_item(data: object) -> None | str:
                    if data is None:
                        return data
                    return cast(None | str, data)

                warnings_item = _parse_warnings_item(warnings_item_data)

                warnings.append(warnings_item)

        _mappings = d.pop("mappings", UNSET)
        mappings: EvalUsageLogItemDetailMappings | Unset
        if isinstance(_mappings, Unset):
            mappings = UNSET
        else:
            mappings = EvalUsageLogItemDetailMappings.from_dict(_mappings)

        _model = d.pop("model", UNSET)
        model: EvalUsageLogItemDetailModel | Unset
        if isinstance(_model, Unset):
            model = UNSET
        else:
            model = EvalUsageLogItemDetailModel.from_dict(_model)

        def _parse_version_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        version_id = _parse_version_id(d.pop("version_id", UNSET))

        def _parse_version_number(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        version_number = _parse_version_number(d.pop("version_number", UNSET))

        _children = d.pop("children", UNSET)
        children: list[None | str] | Unset = UNSET
        if _children is not UNSET:
            children = []
            for children_item_data in _children:

                def _parse_children_item(data: object) -> None | str:
                    if data is None:
                        return data
                    return cast(None | str, data)

                children_item = _parse_children_item(children_item_data)

                children.append(children_item)

        def _parse_aggregation_function(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        aggregation_function = _parse_aggregation_function(
            d.pop("aggregation_function", UNSET)
        )

        def _parse_total_children(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_children = _parse_total_children(d.pop("total_children", UNSET))

        def _parse_completed_children(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        completed_children = _parse_completed_children(
            d.pop("completed_children", UNSET)
        )

        def _parse_failed_children(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        failed_children = _parse_failed_children(d.pop("failed_children", UNSET))

        eval_usage_log_item_detail = cls(
            input_variables=input_variables,
            output=output,
            warnings=warnings,
            mappings=mappings,
            model=model,
            version_id=version_id,
            version_number=version_number,
            children=children,
            aggregation_function=aggregation_function,
            total_children=total_children,
            completed_children=completed_children,
            failed_children=failed_children,
        )

        eval_usage_log_item_detail.additional_properties = d
        return eval_usage_log_item_detail

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
