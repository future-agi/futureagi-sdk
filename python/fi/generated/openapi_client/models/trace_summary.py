from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TraceSummary")


@_attrs_define
class TraceSummary:
    """
    Attributes:
        eval_score (float | None):
        latency_ms (int | None):
        turns (int | None):
        model (None | str):
        input_tokens (int | None):
        output_tokens (int | None):
    """

    eval_score: float | None
    latency_ms: int | None
    turns: int | None
    model: None | str
    input_tokens: int | None
    output_tokens: int | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_score: float | None
        eval_score = self.eval_score

        latency_ms: int | None
        latency_ms = self.latency_ms

        turns: int | None
        turns = self.turns

        model: None | str
        model = self.model

        input_tokens: int | None
        input_tokens = self.input_tokens

        output_tokens: int | None
        output_tokens = self.output_tokens

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval_score": eval_score,
                "latency_ms": latency_ms,
                "turns": turns,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_eval_score(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        eval_score = _parse_eval_score(d.pop("eval_score"))

        def _parse_latency_ms(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        latency_ms = _parse_latency_ms(d.pop("latency_ms"))

        def _parse_turns(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        turns = _parse_turns(d.pop("turns"))

        def _parse_model(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        model = _parse_model(d.pop("model"))

        def _parse_input_tokens(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        input_tokens = _parse_input_tokens(d.pop("input_tokens"))

        def _parse_output_tokens(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        output_tokens = _parse_output_tokens(d.pop("output_tokens"))

        trace_summary = cls(
            eval_score=eval_score,
            latency_ms=latency_ms,
            turns=turns,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        trace_summary.additional_properties = d
        return trace_summary

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
