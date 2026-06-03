from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.composite_eval_execute_request_call_context import (
        CompositeEvalExecuteRequestCallContext,
    )
    from ..models.composite_eval_execute_request_config import (
        CompositeEvalExecuteRequestConfig,
    )
    from ..models.composite_eval_execute_request_input_data_types import (
        CompositeEvalExecuteRequestInputDataTypes,
    )
    from ..models.composite_eval_execute_request_mapping import (
        CompositeEvalExecuteRequestMapping,
    )
    from ..models.composite_eval_execute_request_row_context import (
        CompositeEvalExecuteRequestRowContext,
    )
    from ..models.composite_eval_execute_request_session_context import (
        CompositeEvalExecuteRequestSessionContext,
    )
    from ..models.composite_eval_execute_request_span_context import (
        CompositeEvalExecuteRequestSpanContext,
    )
    from ..models.composite_eval_execute_request_trace_context import (
        CompositeEvalExecuteRequestTraceContext,
    )


T = TypeVar("T", bound="CompositeEvalExecuteRequest")


@_attrs_define
class CompositeEvalExecuteRequest:
    """
    Attributes:
        mapping (CompositeEvalExecuteRequestMapping):
        model (None | str | Unset):
        config (CompositeEvalExecuteRequestConfig | Unset):
        error_localizer (bool | Unset):  Default: False.
        input_data_types (CompositeEvalExecuteRequestInputDataTypes | Unset):
        span_context (CompositeEvalExecuteRequestSpanContext | Unset):
        trace_context (CompositeEvalExecuteRequestTraceContext | Unset):
        session_context (CompositeEvalExecuteRequestSessionContext | Unset):
        call_context (CompositeEvalExecuteRequestCallContext | Unset):
        row_context (CompositeEvalExecuteRequestRowContext | Unset):
    """

    mapping: CompositeEvalExecuteRequestMapping
    model: None | str | Unset = UNSET
    config: CompositeEvalExecuteRequestConfig | Unset = UNSET
    error_localizer: bool | Unset = False
    input_data_types: CompositeEvalExecuteRequestInputDataTypes | Unset = UNSET
    span_context: CompositeEvalExecuteRequestSpanContext | Unset = UNSET
    trace_context: CompositeEvalExecuteRequestTraceContext | Unset = UNSET
    session_context: CompositeEvalExecuteRequestSessionContext | Unset = UNSET
    call_context: CompositeEvalExecuteRequestCallContext | Unset = UNSET
    row_context: CompositeEvalExecuteRequestRowContext | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mapping = self.mapping.to_dict()

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mapping": mapping,
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.composite_eval_execute_request_call_context import (
            CompositeEvalExecuteRequestCallContext,
        )
        from ..models.composite_eval_execute_request_config import (
            CompositeEvalExecuteRequestConfig,
        )
        from ..models.composite_eval_execute_request_input_data_types import (
            CompositeEvalExecuteRequestInputDataTypes,
        )
        from ..models.composite_eval_execute_request_mapping import (
            CompositeEvalExecuteRequestMapping,
        )
        from ..models.composite_eval_execute_request_row_context import (
            CompositeEvalExecuteRequestRowContext,
        )
        from ..models.composite_eval_execute_request_session_context import (
            CompositeEvalExecuteRequestSessionContext,
        )
        from ..models.composite_eval_execute_request_span_context import (
            CompositeEvalExecuteRequestSpanContext,
        )
        from ..models.composite_eval_execute_request_trace_context import (
            CompositeEvalExecuteRequestTraceContext,
        )

        d = dict(src_dict)
        mapping = CompositeEvalExecuteRequestMapping.from_dict(d.pop("mapping"))

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        _config = d.pop("config", UNSET)
        config: CompositeEvalExecuteRequestConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = CompositeEvalExecuteRequestConfig.from_dict(_config)

        error_localizer = d.pop("error_localizer", UNSET)

        _input_data_types = d.pop("input_data_types", UNSET)
        input_data_types: CompositeEvalExecuteRequestInputDataTypes | Unset
        if isinstance(_input_data_types, Unset):
            input_data_types = UNSET
        else:
            input_data_types = CompositeEvalExecuteRequestInputDataTypes.from_dict(
                _input_data_types
            )

        _span_context = d.pop("span_context", UNSET)
        span_context: CompositeEvalExecuteRequestSpanContext | Unset
        if isinstance(_span_context, Unset):
            span_context = UNSET
        else:
            span_context = CompositeEvalExecuteRequestSpanContext.from_dict(
                _span_context
            )

        _trace_context = d.pop("trace_context", UNSET)
        trace_context: CompositeEvalExecuteRequestTraceContext | Unset
        if isinstance(_trace_context, Unset):
            trace_context = UNSET
        else:
            trace_context = CompositeEvalExecuteRequestTraceContext.from_dict(
                _trace_context
            )

        _session_context = d.pop("session_context", UNSET)
        session_context: CompositeEvalExecuteRequestSessionContext | Unset
        if isinstance(_session_context, Unset):
            session_context = UNSET
        else:
            session_context = CompositeEvalExecuteRequestSessionContext.from_dict(
                _session_context
            )

        _call_context = d.pop("call_context", UNSET)
        call_context: CompositeEvalExecuteRequestCallContext | Unset
        if isinstance(_call_context, Unset):
            call_context = UNSET
        else:
            call_context = CompositeEvalExecuteRequestCallContext.from_dict(
                _call_context
            )

        _row_context = d.pop("row_context", UNSET)
        row_context: CompositeEvalExecuteRequestRowContext | Unset
        if isinstance(_row_context, Unset):
            row_context = UNSET
        else:
            row_context = CompositeEvalExecuteRequestRowContext.from_dict(_row_context)

        composite_eval_execute_request = cls(
            mapping=mapping,
            model=model,
            config=config,
            error_localizer=error_localizer,
            input_data_types=input_data_types,
            span_context=span_context,
            trace_context=trace_context,
            session_context=session_context,
            call_context=call_context,
            row_context=row_context,
        )

        composite_eval_execute_request.additional_properties = d
        return composite_eval_execute_request

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
