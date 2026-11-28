from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eval_rollup_eval_target_type import EvalRollupEvalTargetType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_rollup_eval_aggregate_type_4_type_0 import (
        EvalRollupEvalAggregateType4Type0,
    )
    from ..models.eval_rollup_eval_choices_map_type_4_type_0 import (
        EvalRollupEvalChoicesMapType4Type0,
    )
    from ..models.eval_rollup_span import EvalRollupSpan


T = TypeVar("T", bound="EvalRollupEval")


@_attrs_define
class EvalRollupEval:
    """
    Attributes:
        eval_config_id (str):
        eval_name (str):
        aggregate (bool | EvalRollupEvalAggregateType4Type0 | float | list[Any] | None | str): Any valid JSON value.
        spans (list[EvalRollupSpan]):
        output_type (None | str | Unset):
        template_type (None | str | Unset):
        target_type (EvalRollupEvalTargetType | None | Unset):
        choices_map (bool | EvalRollupEvalChoicesMapType4Type0 | float | list[Any] | None | str | Unset): Any valid JSON
            value.
        error (bool | Unset):
    """

    eval_config_id: str
    eval_name: str
    aggregate: bool | EvalRollupEvalAggregateType4Type0 | float | list[Any] | None | str
    spans: list[EvalRollupSpan]
    output_type: None | str | Unset = UNSET
    template_type: None | str | Unset = UNSET
    target_type: EvalRollupEvalTargetType | None | Unset = UNSET
    choices_map: (
        bool
        | EvalRollupEvalChoicesMapType4Type0
        | float
        | list[Any]
        | None
        | str
        | Unset
    ) = UNSET
    error: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.eval_rollup_eval_aggregate_type_4_type_0 import (
            EvalRollupEvalAggregateType4Type0,
        )
        from ..models.eval_rollup_eval_choices_map_type_4_type_0 import (
            EvalRollupEvalChoicesMapType4Type0,
        )

        eval_config_id = self.eval_config_id

        eval_name = self.eval_name

        aggregate: bool | dict[str, Any] | float | list[Any] | None | str
        if isinstance(self.aggregate, list):
            aggregate = self.aggregate

        elif isinstance(self.aggregate, EvalRollupEvalAggregateType4Type0):
            aggregate = self.aggregate.to_dict()
        else:
            aggregate = self.aggregate

        spans = []
        for spans_item_data in self.spans:
            spans_item = spans_item_data.to_dict()
            spans.append(spans_item)

        output_type: None | str | Unset
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        template_type: None | str | Unset
        if isinstance(self.template_type, Unset):
            template_type = UNSET
        else:
            template_type = self.template_type

        target_type: None | str | Unset
        if isinstance(self.target_type, Unset):
            target_type = UNSET
        elif isinstance(self.target_type, EvalRollupEvalTargetType):
            target_type = self.target_type.value
        else:
            target_type = self.target_type

        choices_map: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.choices_map, Unset):
            choices_map = UNSET
        elif isinstance(self.choices_map, list):
            choices_map = self.choices_map

        elif isinstance(self.choices_map, EvalRollupEvalChoicesMapType4Type0):
            choices_map = self.choices_map.to_dict()
        else:
            choices_map = self.choices_map

        error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval_config_id": eval_config_id,
                "eval_name": eval_name,
                "aggregate": aggregate,
                "spans": spans,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if template_type is not UNSET:
            field_dict["template_type"] = template_type
        if target_type is not UNSET:
            field_dict["target_type"] = target_type
        if choices_map is not UNSET:
            field_dict["choices_map"] = choices_map
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_rollup_eval_aggregate_type_4_type_0 import (
            EvalRollupEvalAggregateType4Type0,
        )
        from ..models.eval_rollup_eval_choices_map_type_4_type_0 import (
            EvalRollupEvalChoicesMapType4Type0,
        )
        from ..models.eval_rollup_span import EvalRollupSpan

        d = dict(src_dict)
        eval_config_id = d.pop("eval_config_id")

        eval_name = d.pop("eval_name")

        def _parse_aggregate(
            data: object,
        ) -> bool | EvalRollupEvalAggregateType4Type0 | float | list[Any] | None | str:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                aggregate_type_3 = cast(list[Any], data)

                return aggregate_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                aggregate_type_4_type_0 = EvalRollupEvalAggregateType4Type0.from_dict(
                    data
                )

                return aggregate_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | EvalRollupEvalAggregateType4Type0
                | float
                | list[Any]
                | None
                | str,
                data,
            )

        aggregate = _parse_aggregate(d.pop("aggregate"))

        spans = []
        _spans = d.pop("spans")
        for spans_item_data in _spans:
            spans_item = EvalRollupSpan.from_dict(spans_item_data)

            spans.append(spans_item)

        def _parse_output_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_template_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        template_type = _parse_template_type(d.pop("template_type", UNSET))

        def _parse_target_type(data: object) -> EvalRollupEvalTargetType | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                target_type_type_1 = EvalRollupEvalTargetType(data)

                return target_type_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EvalRollupEvalTargetType | None | Unset, data)

        target_type = _parse_target_type(d.pop("target_type", UNSET))

        def _parse_choices_map(
            data: object,
        ) -> (
            bool
            | EvalRollupEvalChoicesMapType4Type0
            | float
            | list[Any]
            | None
            | str
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                choices_map_type_3 = cast(list[Any], data)

                return choices_map_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                choices_map_type_4_type_0 = (
                    EvalRollupEvalChoicesMapType4Type0.from_dict(data)
                )

                return choices_map_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | EvalRollupEvalChoicesMapType4Type0
                | float
                | list[Any]
                | None
                | str
                | Unset,
                data,
            )

        choices_map = _parse_choices_map(d.pop("choices_map", UNSET))

        error = d.pop("error", UNSET)

        eval_rollup_eval = cls(
            eval_config_id=eval_config_id,
            eval_name=eval_name,
            aggregate=aggregate,
            spans=spans,
            output_type=output_type,
            template_type=template_type,
            target_type=target_type,
            choices_map=choices_map,
            error=error,
        )

        eval_rollup_eval.additional_properties = d
        return eval_rollup_eval

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
