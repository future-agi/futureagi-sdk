from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_rollup_span_value_type_4_type_0 import (
        EvalRollupSpanValueType4Type0,
    )


T = TypeVar("T", bound="EvalRollupSpan")


@_attrs_define
class EvalRollupSpan:
    """
    Attributes:
        span_id (str):
        span_name (str | Unset):
        value (bool | EvalRollupSpanValueType4Type0 | float | list[Any] | None | str | Unset): Any valid JSON value.
        explanation (None | str | Unset):
        error (bool | Unset):
        status (None | str | Unset):
        eval_config_id (str | Unset):
    """

    span_id: str
    span_name: str | Unset = UNSET
    value: (
        bool | EvalRollupSpanValueType4Type0 | float | list[Any] | None | str | Unset
    ) = UNSET
    explanation: None | str | Unset = UNSET
    error: bool | Unset = UNSET
    status: None | str | Unset = UNSET
    eval_config_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.eval_rollup_span_value_type_4_type_0 import (
            EvalRollupSpanValueType4Type0,
        )

        span_id = self.span_id

        span_name = self.span_name

        value: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.value, Unset):
            value = UNSET
        elif isinstance(self.value, list):
            value = self.value

        elif isinstance(self.value, EvalRollupSpanValueType4Type0):
            value = self.value.to_dict()
        else:
            value = self.value

        explanation: None | str | Unset
        if isinstance(self.explanation, Unset):
            explanation = UNSET
        else:
            explanation = self.explanation

        error = self.error

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        eval_config_id = self.eval_config_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "span_id": span_id,
            }
        )
        if span_name is not UNSET:
            field_dict["span_name"] = span_name
        if value is not UNSET:
            field_dict["value"] = value
        if explanation is not UNSET:
            field_dict["explanation"] = explanation
        if error is not UNSET:
            field_dict["error"] = error
        if status is not UNSET:
            field_dict["status"] = status
        if eval_config_id is not UNSET:
            field_dict["eval_config_id"] = eval_config_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_rollup_span_value_type_4_type_0 import (
            EvalRollupSpanValueType4Type0,
        )

        d = dict(src_dict)
        span_id = d.pop("span_id")

        span_name = d.pop("span_name", UNSET)

        def _parse_value(
            data: object,
        ) -> (
            bool
            | EvalRollupSpanValueType4Type0
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
                value_type_3 = cast(list[Any], data)

                return value_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                value_type_4_type_0 = EvalRollupSpanValueType4Type0.from_dict(data)

                return value_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | EvalRollupSpanValueType4Type0
                | float
                | list[Any]
                | None
                | str
                | Unset,
                data,
            )

        value = _parse_value(d.pop("value", UNSET))

        def _parse_explanation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        explanation = _parse_explanation(d.pop("explanation", UNSET))

        error = d.pop("error", UNSET)

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        eval_config_id = d.pop("eval_config_id", UNSET)

        eval_rollup_span = cls(
            span_id=span_id,
            span_name=span_name,
            value=value,
            explanation=explanation,
            error=error,
            status=status,
            eval_config_id=eval_config_id,
        )

        eval_rollup_span.additional_properties = d
        return eval_rollup_span

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
