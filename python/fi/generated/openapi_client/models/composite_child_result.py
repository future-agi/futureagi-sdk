from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.composite_child_result_error_localizer_result import (
        CompositeChildResultErrorLocalizerResult,
    )
    from ..models.composite_child_result_output import CompositeChildResultOutput


T = TypeVar("T", bound="CompositeChildResult")


@_attrs_define
class CompositeChildResult:
    """
    Attributes:
        child_id (UUID):
        child_name (str):
        order (int):
        status (str):
        score (float | None | Unset):
        output (CompositeChildResultOutput | Unset):
        reason (None | str | Unset):
        output_type (None | str | Unset):
        error (None | str | Unset):
        log_id (None | str | Unset):
        weight (float | Unset):
        error_localizer_result (CompositeChildResultErrorLocalizerResult | Unset):
    """

    child_id: UUID
    child_name: str
    order: int
    status: str
    score: float | None | Unset = UNSET
    output: CompositeChildResultOutput | Unset = UNSET
    reason: None | str | Unset = UNSET
    output_type: None | str | Unset = UNSET
    error: None | str | Unset = UNSET
    log_id: None | str | Unset = UNSET
    weight: float | Unset = UNSET
    error_localizer_result: CompositeChildResultErrorLocalizerResult | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        child_id = str(self.child_id)

        child_name = self.child_name

        order = self.order

        status = self.status

        score: float | None | Unset
        if isinstance(self.score, Unset):
            score = UNSET
        else:
            score = self.score

        output: dict[str, Any] | Unset = UNSET
        if not isinstance(self.output, Unset):
            output = self.output.to_dict()

        reason: None | str | Unset
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        output_type: None | str | Unset
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        log_id: None | str | Unset
        if isinstance(self.log_id, Unset):
            log_id = UNSET
        else:
            log_id = self.log_id

        weight = self.weight

        error_localizer_result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error_localizer_result, Unset):
            error_localizer_result = self.error_localizer_result.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "child_id": child_id,
                "child_name": child_name,
                "order": order,
                "status": status,
            }
        )
        if score is not UNSET:
            field_dict["score"] = score
        if output is not UNSET:
            field_dict["output"] = output
        if reason is not UNSET:
            field_dict["reason"] = reason
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if error is not UNSET:
            field_dict["error"] = error
        if log_id is not UNSET:
            field_dict["log_id"] = log_id
        if weight is not UNSET:
            field_dict["weight"] = weight
        if error_localizer_result is not UNSET:
            field_dict["error_localizer_result"] = error_localizer_result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.composite_child_result_error_localizer_result import (
            CompositeChildResultErrorLocalizerResult,
        )
        from ..models.composite_child_result_output import CompositeChildResultOutput

        d = dict(src_dict)
        child_id = UUID(d.pop("child_id"))

        child_name = d.pop("child_name")

        order = d.pop("order")

        status = d.pop("status")

        def _parse_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        score = _parse_score(d.pop("score", UNSET))

        _output = d.pop("output", UNSET)
        output: CompositeChildResultOutput | Unset
        if isinstance(_output, Unset):
            output = UNSET
        else:
            output = CompositeChildResultOutput.from_dict(_output)

        def _parse_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reason = _parse_reason(d.pop("reason", UNSET))

        def _parse_output_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_log_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        log_id = _parse_log_id(d.pop("log_id", UNSET))

        weight = d.pop("weight", UNSET)

        _error_localizer_result = d.pop("error_localizer_result", UNSET)
        error_localizer_result: CompositeChildResultErrorLocalizerResult | Unset
        if isinstance(_error_localizer_result, Unset):
            error_localizer_result = UNSET
        else:
            error_localizer_result = CompositeChildResultErrorLocalizerResult.from_dict(
                _error_localizer_result
            )

        composite_child_result = cls(
            child_id=child_id,
            child_name=child_name,
            order=order,
            status=status,
            score=score,
            output=output,
            reason=reason,
            output_type=output_type,
            error=error,
            log_id=log_id,
            weight=weight,
            error_localizer_result=error_localizer_result,
        )

        composite_child_result.additional_properties = d
        return composite_child_result

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
