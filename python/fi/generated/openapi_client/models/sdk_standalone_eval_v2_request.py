from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sdk_standalone_eval_v2_request_config import (
        SDKStandaloneEvalV2RequestConfig,
    )
    from ..models.sdk_standalone_eval_v2_request_inputs import (
        SDKStandaloneEvalV2RequestInputs,
    )


T = TypeVar("T", bound="SDKStandaloneEvalV2Request")


@_attrs_define
class SDKStandaloneEvalV2Request:
    """
    Attributes:
        eval_name (str):
        inputs (SDKStandaloneEvalV2RequestInputs):
        model (None | str | Unset):
        span_id (None | str | Unset):
        custom_eval_name (None | str | Unset):
        trace_eval (bool | Unset):  Default: False.
        is_async (bool | Unset):  Default: False.
        error_localizer (bool | Unset):  Default: False.
        config (SDKStandaloneEvalV2RequestConfig | Unset):
    """

    eval_name: str
    inputs: SDKStandaloneEvalV2RequestInputs
    model: None | str | Unset = UNSET
    span_id: None | str | Unset = UNSET
    custom_eval_name: None | str | Unset = UNSET
    trace_eval: bool | Unset = False
    is_async: bool | Unset = False
    error_localizer: bool | Unset = False
    config: SDKStandaloneEvalV2RequestConfig | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_name = self.eval_name

        inputs = self.inputs.to_dict()

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        span_id: None | str | Unset
        if isinstance(self.span_id, Unset):
            span_id = UNSET
        else:
            span_id = self.span_id

        custom_eval_name: None | str | Unset
        if isinstance(self.custom_eval_name, Unset):
            custom_eval_name = UNSET
        else:
            custom_eval_name = self.custom_eval_name

        trace_eval = self.trace_eval

        is_async = self.is_async

        error_localizer = self.error_localizer

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval_name": eval_name,
                "inputs": inputs,
            }
        )
        if model is not UNSET:
            field_dict["model"] = model
        if span_id is not UNSET:
            field_dict["span_id"] = span_id
        if custom_eval_name is not UNSET:
            field_dict["custom_eval_name"] = custom_eval_name
        if trace_eval is not UNSET:
            field_dict["trace_eval"] = trace_eval
        if is_async is not UNSET:
            field_dict["is_async"] = is_async
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if config is not UNSET:
            field_dict["config"] = config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_standalone_eval_v2_request_config import (
            SDKStandaloneEvalV2RequestConfig,
        )
        from ..models.sdk_standalone_eval_v2_request_inputs import (
            SDKStandaloneEvalV2RequestInputs,
        )

        d = dict(src_dict)
        eval_name = d.pop("eval_name")

        inputs = SDKStandaloneEvalV2RequestInputs.from_dict(d.pop("inputs"))

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        def _parse_span_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        span_id = _parse_span_id(d.pop("span_id", UNSET))

        def _parse_custom_eval_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        custom_eval_name = _parse_custom_eval_name(d.pop("custom_eval_name", UNSET))

        trace_eval = d.pop("trace_eval", UNSET)

        is_async = d.pop("is_async", UNSET)

        error_localizer = d.pop("error_localizer", UNSET)

        _config = d.pop("config", UNSET)
        config: SDKStandaloneEvalV2RequestConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = SDKStandaloneEvalV2RequestConfig.from_dict(_config)

        sdk_standalone_eval_v2_request = cls(
            eval_name=eval_name,
            inputs=inputs,
            model=model,
            span_id=span_id,
            custom_eval_name=custom_eval_name,
            trace_eval=trace_eval,
            is_async=is_async,
            error_localizer=error_localizer,
            config=config,
        )

        sdk_standalone_eval_v2_request.additional_properties = d
        return sdk_standalone_eval_v2_request

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
