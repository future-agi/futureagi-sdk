from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.composite_eval_adhoc_execute_request_aggregation_function import (
    CompositeEvalAdhocExecuteRequestAggregationFunction,
)
from ..models.composite_eval_adhoc_execute_request_composite_child_axis import (
    CompositeEvalAdhocExecuteRequestCompositeChildAxis,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.composite_eval_adhoc_execute_request_call_context import (
        CompositeEvalAdhocExecuteRequestCallContext,
    )
    from ..models.composite_eval_adhoc_execute_request_child_weights import (
        CompositeEvalAdhocExecuteRequestChildWeights,
    )
    from ..models.composite_eval_adhoc_execute_request_config import (
        CompositeEvalAdhocExecuteRequestConfig,
    )
    from ..models.composite_eval_adhoc_execute_request_input_data_types import (
        CompositeEvalAdhocExecuteRequestInputDataTypes,
    )
    from ..models.composite_eval_adhoc_execute_request_mapping import (
        CompositeEvalAdhocExecuteRequestMapping,
    )
    from ..models.composite_eval_adhoc_execute_request_row_context import (
        CompositeEvalAdhocExecuteRequestRowContext,
    )
    from ..models.composite_eval_adhoc_execute_request_session_context import (
        CompositeEvalAdhocExecuteRequestSessionContext,
    )
    from ..models.composite_eval_adhoc_execute_request_span_context import (
        CompositeEvalAdhocExecuteRequestSpanContext,
    )
    from ..models.composite_eval_adhoc_execute_request_trace_context import (
        CompositeEvalAdhocExecuteRequestTraceContext,
    )


T = TypeVar("T", bound="CompositeEvalAdhocExecuteRequest")


@_attrs_define
class CompositeEvalAdhocExecuteRequest:
    """
    Attributes:
        mapping (CompositeEvalAdhocExecuteRequestMapping):
        child_template_ids (list[UUID]):
        model (None | str | Unset):
        config (CompositeEvalAdhocExecuteRequestConfig | Unset):
        error_localizer (bool | Unset):  Default: False.
        input_data_types (CompositeEvalAdhocExecuteRequestInputDataTypes | Unset):
        span_context (CompositeEvalAdhocExecuteRequestSpanContext | Unset):
        trace_context (CompositeEvalAdhocExecuteRequestTraceContext | Unset):
        session_context (CompositeEvalAdhocExecuteRequestSessionContext | Unset):
        call_context (CompositeEvalAdhocExecuteRequestCallContext | Unset):
        row_context (CompositeEvalAdhocExecuteRequestRowContext | Unset):
        aggregation_enabled (bool | Unset):  Default: True.
        aggregation_function (CompositeEvalAdhocExecuteRequestAggregationFunction | Unset):  Default:
            CompositeEvalAdhocExecuteRequestAggregationFunction.WEIGHTED_AVG.
        composite_child_axis (CompositeEvalAdhocExecuteRequestCompositeChildAxis | Unset):  Default:
            CompositeEvalAdhocExecuteRequestCompositeChildAxis.VALUE_0.
        child_weights (CompositeEvalAdhocExecuteRequestChildWeights | Unset):
        pass_threshold (float | Unset):  Default: 0.5.
    """

    mapping: CompositeEvalAdhocExecuteRequestMapping
    child_template_ids: list[UUID]
    model: None | str | Unset = UNSET
    config: CompositeEvalAdhocExecuteRequestConfig | Unset = UNSET
    error_localizer: bool | Unset = False
    input_data_types: CompositeEvalAdhocExecuteRequestInputDataTypes | Unset = UNSET
    span_context: CompositeEvalAdhocExecuteRequestSpanContext | Unset = UNSET
    trace_context: CompositeEvalAdhocExecuteRequestTraceContext | Unset = UNSET
    session_context: CompositeEvalAdhocExecuteRequestSessionContext | Unset = UNSET
    call_context: CompositeEvalAdhocExecuteRequestCallContext | Unset = UNSET
    row_context: CompositeEvalAdhocExecuteRequestRowContext | Unset = UNSET
    aggregation_enabled: bool | Unset = True
    aggregation_function: (
        CompositeEvalAdhocExecuteRequestAggregationFunction | Unset
    ) = CompositeEvalAdhocExecuteRequestAggregationFunction.WEIGHTED_AVG
    composite_child_axis: CompositeEvalAdhocExecuteRequestCompositeChildAxis | Unset = (
        CompositeEvalAdhocExecuteRequestCompositeChildAxis.VALUE_0
    )
    child_weights: CompositeEvalAdhocExecuteRequestChildWeights | Unset = UNSET
    pass_threshold: float | Unset = 0.5
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mapping = self.mapping.to_dict()

        child_template_ids = []
        for child_template_ids_item_data in self.child_template_ids:
            child_template_ids_item = str(child_template_ids_item_data)
            child_template_ids.append(child_template_ids_item)

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        error_localizer = self.error_localizer

        input_data_types: dict[str, Any] | Unset = UNSET
        if not isinstance(self.input_data_types, Unset):
            input_data_types = self.input_data_types.to_dict()

        span_context: dict[str, Any] | Unset = UNSET
        if not isinstance(self.span_context, Unset):
            span_context = self.span_context.to_dict()

        trace_context: dict[str, Any] | Unset = UNSET
        if not isinstance(self.trace_context, Unset):
            trace_context = self.trace_context.to_dict()

        session_context: dict[str, Any] | Unset = UNSET
        if not isinstance(self.session_context, Unset):
            session_context = self.session_context.to_dict()

        call_context: dict[str, Any] | Unset = UNSET
        if not isinstance(self.call_context, Unset):
            call_context = self.call_context.to_dict()

        row_context: dict[str, Any] | Unset = UNSET
        if not isinstance(self.row_context, Unset):
            row_context = self.row_context.to_dict()

        aggregation_enabled = self.aggregation_enabled

        aggregation_function: str | Unset = UNSET
        if not isinstance(self.aggregation_function, Unset):
            aggregation_function = self.aggregation_function.value

        composite_child_axis: str | Unset = UNSET
        if not isinstance(self.composite_child_axis, Unset):
            composite_child_axis = self.composite_child_axis.value

        child_weights: dict[str, Any] | Unset = UNSET
        if not isinstance(self.child_weights, Unset):
            child_weights = self.child_weights.to_dict()

        pass_threshold = self.pass_threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mapping": mapping,
                "child_template_ids": child_template_ids,
            }
        )
        if model is not UNSET:
            field_dict["model"] = model
        if config is not UNSET:
            field_dict["config"] = config
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if input_data_types is not UNSET:
            field_dict["input_data_types"] = input_data_types
        if span_context is not UNSET:
            field_dict["span_context"] = span_context
        if trace_context is not UNSET:
            field_dict["trace_context"] = trace_context
        if session_context is not UNSET:
            field_dict["session_context"] = session_context
        if call_context is not UNSET:
            field_dict["call_context"] = call_context
        if row_context is not UNSET:
            field_dict["row_context"] = row_context
        if aggregation_enabled is not UNSET:
            field_dict["aggregation_enabled"] = aggregation_enabled
        if aggregation_function is not UNSET:
            field_dict["aggregation_function"] = aggregation_function
        if composite_child_axis is not UNSET:
            field_dict["composite_child_axis"] = composite_child_axis
        if child_weights is not UNSET:
            field_dict["child_weights"] = child_weights
        if pass_threshold is not UNSET:
            field_dict["pass_threshold"] = pass_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.composite_eval_adhoc_execute_request_call_context import (
            CompositeEvalAdhocExecuteRequestCallContext,
        )
        from ..models.composite_eval_adhoc_execute_request_child_weights import (
            CompositeEvalAdhocExecuteRequestChildWeights,
        )
        from ..models.composite_eval_adhoc_execute_request_config import (
            CompositeEvalAdhocExecuteRequestConfig,
        )
        from ..models.composite_eval_adhoc_execute_request_input_data_types import (
            CompositeEvalAdhocExecuteRequestInputDataTypes,
        )
        from ..models.composite_eval_adhoc_execute_request_mapping import (
            CompositeEvalAdhocExecuteRequestMapping,
        )
        from ..models.composite_eval_adhoc_execute_request_row_context import (
            CompositeEvalAdhocExecuteRequestRowContext,
        )
        from ..models.composite_eval_adhoc_execute_request_session_context import (
            CompositeEvalAdhocExecuteRequestSessionContext,
        )
        from ..models.composite_eval_adhoc_execute_request_span_context import (
            CompositeEvalAdhocExecuteRequestSpanContext,
        )
        from ..models.composite_eval_adhoc_execute_request_trace_context import (
            CompositeEvalAdhocExecuteRequestTraceContext,
        )

        d = dict(src_dict)
        mapping = CompositeEvalAdhocExecuteRequestMapping.from_dict(d.pop("mapping"))

        child_template_ids = []
        _child_template_ids = d.pop("child_template_ids")
        for child_template_ids_item_data in _child_template_ids:
            child_template_ids_item = UUID(child_template_ids_item_data)

            child_template_ids.append(child_template_ids_item)

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        _config = d.pop("config", UNSET)
        config: CompositeEvalAdhocExecuteRequestConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = CompositeEvalAdhocExecuteRequestConfig.from_dict(_config)

        error_localizer = d.pop("error_localizer", UNSET)

        _input_data_types = d.pop("input_data_types", UNSET)
        input_data_types: CompositeEvalAdhocExecuteRequestInputDataTypes | Unset
        if isinstance(_input_data_types, Unset):
            input_data_types = UNSET
        else:
            input_data_types = CompositeEvalAdhocExecuteRequestInputDataTypes.from_dict(
                _input_data_types
            )

        _span_context = d.pop("span_context", UNSET)
        span_context: CompositeEvalAdhocExecuteRequestSpanContext | Unset
        if isinstance(_span_context, Unset):
            span_context = UNSET
        else:
            span_context = CompositeEvalAdhocExecuteRequestSpanContext.from_dict(
                _span_context
            )

        _trace_context = d.pop("trace_context", UNSET)
        trace_context: CompositeEvalAdhocExecuteRequestTraceContext | Unset
        if isinstance(_trace_context, Unset):
            trace_context = UNSET
        else:
            trace_context = CompositeEvalAdhocExecuteRequestTraceContext.from_dict(
                _trace_context
            )

        _session_context = d.pop("session_context", UNSET)
        session_context: CompositeEvalAdhocExecuteRequestSessionContext | Unset
        if isinstance(_session_context, Unset):
            session_context = UNSET
        else:
            session_context = CompositeEvalAdhocExecuteRequestSessionContext.from_dict(
                _session_context
            )

        _call_context = d.pop("call_context", UNSET)
        call_context: CompositeEvalAdhocExecuteRequestCallContext | Unset
        if isinstance(_call_context, Unset):
            call_context = UNSET
        else:
            call_context = CompositeEvalAdhocExecuteRequestCallContext.from_dict(
                _call_context
            )

        _row_context = d.pop("row_context", UNSET)
        row_context: CompositeEvalAdhocExecuteRequestRowContext | Unset
        if isinstance(_row_context, Unset):
            row_context = UNSET
        else:
            row_context = CompositeEvalAdhocExecuteRequestRowContext.from_dict(
                _row_context
            )

        aggregation_enabled = d.pop("aggregation_enabled", UNSET)

        _aggregation_function = d.pop("aggregation_function", UNSET)
        aggregation_function: (
            CompositeEvalAdhocExecuteRequestAggregationFunction | Unset
        )
        if isinstance(_aggregation_function, Unset):
            aggregation_function = UNSET
        else:
            aggregation_function = CompositeEvalAdhocExecuteRequestAggregationFunction(
                _aggregation_function
            )

        _composite_child_axis = d.pop("composite_child_axis", UNSET)
        composite_child_axis: CompositeEvalAdhocExecuteRequestCompositeChildAxis | Unset
        if isinstance(_composite_child_axis, Unset):
            composite_child_axis = UNSET
        else:
            composite_child_axis = CompositeEvalAdhocExecuteRequestCompositeChildAxis(
                _composite_child_axis
            )

        _child_weights = d.pop("child_weights", UNSET)
        child_weights: CompositeEvalAdhocExecuteRequestChildWeights | Unset
        if isinstance(_child_weights, Unset):
            child_weights = UNSET
        else:
            child_weights = CompositeEvalAdhocExecuteRequestChildWeights.from_dict(
                _child_weights
            )

        pass_threshold = d.pop("pass_threshold", UNSET)

        composite_eval_adhoc_execute_request = cls(
            mapping=mapping,
            child_template_ids=child_template_ids,
            model=model,
            config=config,
            error_localizer=error_localizer,
            input_data_types=input_data_types,
            span_context=span_context,
            trace_context=trace_context,
            session_context=session_context,
            call_context=call_context,
            row_context=row_context,
            aggregation_enabled=aggregation_enabled,
            aggregation_function=aggregation_function,
            composite_child_axis=composite_child_axis,
            child_weights=child_weights,
            pass_threshold=pass_threshold,
        )

        composite_eval_adhoc_execute_request.additional_properties = d
        return composite_eval_adhoc_execute_request

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
