from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define

from ..models.external_run_score_status import ExternalRunScoreStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="ExternalRunScore")


@_attrs_define
class ExternalRunScore:
    """
    Attributes:
        metric_id (UUID):
        evaluator_version_id (UUID):
        status (ExternalRunScoreStatus):
        value (float | None | Unset):
        explanation (None | str | Unset):
        trace_id (None | str | Unset):
        span_id (None | str | Unset):
    """

    metric_id: UUID
    evaluator_version_id: UUID
    status: ExternalRunScoreStatus
    value: float | None | Unset = UNSET
    explanation: None | str | Unset = UNSET
    trace_id: None | str | Unset = UNSET
    span_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        metric_id = str(self.metric_id)

        evaluator_version_id = str(self.evaluator_version_id)

        status = self.status.value

        value: float | None | Unset
        if isinstance(self.value, Unset):
            value = UNSET
        else:
            value = self.value

        explanation: None | str | Unset
        if isinstance(self.explanation, Unset):
            explanation = UNSET
        else:
            explanation = self.explanation

        trace_id: None | str | Unset
        if isinstance(self.trace_id, Unset):
            trace_id = UNSET
        else:
            trace_id = self.trace_id

        span_id: None | str | Unset
        if isinstance(self.span_id, Unset):
            span_id = UNSET
        else:
            span_id = self.span_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "metric_id": metric_id,
                "evaluator_version_id": evaluator_version_id,
                "status": status,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value
        if explanation is not UNSET:
            field_dict["explanation"] = explanation
        if trace_id is not UNSET:
            field_dict["trace_id"] = trace_id
        if span_id is not UNSET:
            field_dict["span_id"] = span_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        metric_id = UUID(d.pop("metric_id"))

        evaluator_version_id = UUID(d.pop("evaluator_version_id"))

        status = ExternalRunScoreStatus(d.pop("status"))

        def _parse_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        value = _parse_value(d.pop("value", UNSET))

        def _parse_explanation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        explanation = _parse_explanation(d.pop("explanation", UNSET))

        def _parse_trace_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        trace_id = _parse_trace_id(d.pop("trace_id", UNSET))

        def _parse_span_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        span_id = _parse_span_id(d.pop("span_id", UNSET))

        external_run_score = cls(
            metric_id=metric_id,
            evaluator_version_id=evaluator_version_id,
            status=status,
            value=value,
            explanation=explanation,
            trace_id=trace_id,
            span_id=span_id,
        )

        return external_run_score
