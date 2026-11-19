from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define

from ..models.external_run_result_status import ExternalRunResultStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.external_run_result_error_type_4_type_0 import (
        ExternalRunResultErrorType4Type0,
    )
    from ..models.external_run_result_output_type_4_type_0 import (
        ExternalRunResultOutputType4Type0,
    )
    from ..models.external_run_result_token_usage_type_4_type_0 import (
        ExternalRunResultTokenUsageType4Type0,
    )
    from ..models.external_run_score import ExternalRunScore


T = TypeVar("T", bound="ExternalRunResult")


@_attrs_define
class ExternalRunResult:
    """
    Attributes:
        example_id (UUID):
        receipt_key (str):
        status (ExternalRunResultStatus):
        trial_number (int | Unset):  Default: 1.
        output (bool | ExternalRunResultOutputType4Type0 | float | list[Any] | None | str | Unset): Any valid JSON
            value.
        error (bool | ExternalRunResultErrorType4Type0 | float | list[Any] | None | str | Unset): Any valid JSON value.
        trace_id (None | str | Unset):
        root_span_id (None | str | Unset):
        latency_ms (float | None | Unset):
        token_usage (bool | ExternalRunResultTokenUsageType4Type0 | float | list[Any] | None | str | Unset): Any valid
            JSON value.
        cost (float | None | Unset):
        score_refs (list[ExternalRunScore] | Unset):
    """

    example_id: UUID
    receipt_key: str
    status: ExternalRunResultStatus
    trial_number: int | Unset = 1
    output: (
        bool
        | ExternalRunResultOutputType4Type0
        | float
        | list[Any]
        | None
        | str
        | Unset
    ) = UNSET
    error: (
        bool | ExternalRunResultErrorType4Type0 | float | list[Any] | None | str | Unset
    ) = UNSET
    trace_id: None | str | Unset = UNSET
    root_span_id: None | str | Unset = UNSET
    latency_ms: float | None | Unset = UNSET
    token_usage: (
        bool
        | ExternalRunResultTokenUsageType4Type0
        | float
        | list[Any]
        | None
        | str
        | Unset
    ) = UNSET
    cost: float | None | Unset = UNSET
    score_refs: list[ExternalRunScore] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.external_run_result_error_type_4_type_0 import (
            ExternalRunResultErrorType4Type0,
        )
        from ..models.external_run_result_output_type_4_type_0 import (
            ExternalRunResultOutputType4Type0,
        )
        from ..models.external_run_result_token_usage_type_4_type_0 import (
            ExternalRunResultTokenUsageType4Type0,
        )

        example_id = str(self.example_id)

        receipt_key = self.receipt_key

        status = self.status.value

        trial_number = self.trial_number

        output: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.output, Unset):
            output = UNSET
        elif isinstance(self.output, list):
            output = self.output

        elif isinstance(self.output, ExternalRunResultOutputType4Type0):
            output = self.output.to_dict()
        else:
            output = self.output

        error: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        elif isinstance(self.error, list):
            error = self.error

        elif isinstance(self.error, ExternalRunResultErrorType4Type0):
            error = self.error.to_dict()
        else:
            error = self.error

        trace_id: None | str | Unset
        if isinstance(self.trace_id, Unset):
            trace_id = UNSET
        else:
            trace_id = self.trace_id

        root_span_id: None | str | Unset
        if isinstance(self.root_span_id, Unset):
            root_span_id = UNSET
        else:
            root_span_id = self.root_span_id

        latency_ms: float | None | Unset
        if isinstance(self.latency_ms, Unset):
            latency_ms = UNSET
        else:
            latency_ms = self.latency_ms

        token_usage: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.token_usage, Unset):
            token_usage = UNSET
        elif isinstance(self.token_usage, list):
            token_usage = self.token_usage

        elif isinstance(self.token_usage, ExternalRunResultTokenUsageType4Type0):
            token_usage = self.token_usage.to_dict()
        else:
            token_usage = self.token_usage

        cost: float | None | Unset
        if isinstance(self.cost, Unset):
            cost = UNSET
        else:
            cost = self.cost

        score_refs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.score_refs, Unset):
            score_refs = []
            for score_refs_item_data in self.score_refs:
                score_refs_item = score_refs_item_data.to_dict()
                score_refs.append(score_refs_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "example_id": example_id,
                "receipt_key": receipt_key,
                "status": status,
            }
        )
        if trial_number is not UNSET:
            field_dict["trial_number"] = trial_number
        if output is not UNSET:
            field_dict["output"] = output
        if error is not UNSET:
            field_dict["error"] = error
        if trace_id is not UNSET:
            field_dict["trace_id"] = trace_id
        if root_span_id is not UNSET:
            field_dict["root_span_id"] = root_span_id
        if latency_ms is not UNSET:
            field_dict["latency_ms"] = latency_ms
        if token_usage is not UNSET:
            field_dict["token_usage"] = token_usage
        if cost is not UNSET:
            field_dict["cost"] = cost
        if score_refs is not UNSET:
            field_dict["score_refs"] = score_refs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.external_run_result_error_type_4_type_0 import (
            ExternalRunResultErrorType4Type0,
        )
        from ..models.external_run_result_output_type_4_type_0 import (
            ExternalRunResultOutputType4Type0,
        )
        from ..models.external_run_result_token_usage_type_4_type_0 import (
            ExternalRunResultTokenUsageType4Type0,
        )
        from ..models.external_run_score import ExternalRunScore

        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        receipt_key = d.pop("receipt_key")

        status = ExternalRunResultStatus(d.pop("status"))

        trial_number = d.pop("trial_number", UNSET)

        def _parse_output(
            data: object,
        ) -> (
            bool
            | ExternalRunResultOutputType4Type0
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
                output_type_3 = cast(list[Any], data)

                return output_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_type_4_type_0 = ExternalRunResultOutputType4Type0.from_dict(data)

                return output_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | ExternalRunResultOutputType4Type0
                | float
                | list[Any]
                | None
                | str
                | Unset,
                data,
            )

        output = _parse_output(d.pop("output", UNSET))

        def _parse_error(
            data: object,
        ) -> (
            bool
            | ExternalRunResultErrorType4Type0
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
                error_type_3 = cast(list[Any], data)

                return error_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                error_type_4_type_0 = ExternalRunResultErrorType4Type0.from_dict(data)

                return error_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | ExternalRunResultErrorType4Type0
                | float
                | list[Any]
                | None
                | str
                | Unset,
                data,
            )

        error = _parse_error(d.pop("error", UNSET))

        def _parse_trace_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        trace_id = _parse_trace_id(d.pop("trace_id", UNSET))

        def _parse_root_span_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        root_span_id = _parse_root_span_id(d.pop("root_span_id", UNSET))

        def _parse_latency_ms(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        latency_ms = _parse_latency_ms(d.pop("latency_ms", UNSET))

        def _parse_token_usage(
            data: object,
        ) -> (
            bool
            | ExternalRunResultTokenUsageType4Type0
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
                token_usage_type_3 = cast(list[Any], data)

                return token_usage_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                token_usage_type_4_type_0 = (
                    ExternalRunResultTokenUsageType4Type0.from_dict(data)
                )

                return token_usage_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | ExternalRunResultTokenUsageType4Type0
                | float
                | list[Any]
                | None
                | str
                | Unset,
                data,
            )

        token_usage = _parse_token_usage(d.pop("token_usage", UNSET))

        def _parse_cost(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        cost = _parse_cost(d.pop("cost", UNSET))

        _score_refs = d.pop("score_refs", UNSET)
        score_refs: list[ExternalRunScore] | Unset = UNSET
        if _score_refs is not UNSET:
            score_refs = []
            for score_refs_item_data in _score_refs:
                score_refs_item = ExternalRunScore.from_dict(score_refs_item_data)

                score_refs.append(score_refs_item)

        external_run_result = cls(
            example_id=example_id,
            receipt_key=receipt_key,
            status=status,
            trial_number=trial_number,
            output=output,
            error=error,
            trace_id=trace_id,
            root_span_id=root_span_id,
            latency_ms=latency_ms,
            token_usage=token_usage,
            cost=cost,
            score_refs=score_refs,
        )

        return external_run_result
