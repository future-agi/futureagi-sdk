from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TracesListRow")


@_attrs_define
class TracesListRow:
    """
    Attributes:
        id (str):
        input_ (None | str):
        timestamp (datetime.datetime | None):
        latency_ms (int | None):
        tokens (int | None):
        cost (float | None):
        score (float | None):
        turns (int | None):
    """

    id: str
    input_: None | str
    timestamp: datetime.datetime | None
    latency_ms: int | None
    tokens: int | None
    cost: float | None
    score: float | None
    turns: int | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        input_: None | str
        input_ = self.input_

        timestamp: None | str
        if isinstance(self.timestamp, datetime.datetime):
            timestamp = self.timestamp.isoformat()
        else:
            timestamp = self.timestamp

        latency_ms: int | None
        latency_ms = self.latency_ms

        tokens: int | None
        tokens = self.tokens

        cost: float | None
        cost = self.cost

        score: float | None
        score = self.score

        turns: int | None
        turns = self.turns

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "input": input_,
                "timestamp": timestamp,
                "latency_ms": latency_ms,
                "tokens": tokens,
                "cost": cost,
                "score": score,
                "turns": turns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        def _parse_input_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        input_ = _parse_input_(d.pop("input"))

        def _parse_timestamp(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                timestamp_type_0 = isoparse(data)

                return timestamp_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        timestamp = _parse_timestamp(d.pop("timestamp"))

        def _parse_latency_ms(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        latency_ms = _parse_latency_ms(d.pop("latency_ms"))

        def _parse_tokens(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        tokens = _parse_tokens(d.pop("tokens"))

        def _parse_cost(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        cost = _parse_cost(d.pop("cost"))

        def _parse_score(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        score = _parse_score(d.pop("score"))

        def _parse_turns(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        turns = _parse_turns(d.pop("turns"))

        traces_list_row = cls(
            id=id,
            input_=input_,
            timestamp=timestamp,
            latency_ms=latency_ms,
            tokens=tokens,
            cost=cost,
            score=score,
            turns=turns,
        )

        traces_list_row.additional_properties = d
        return traces_list_row

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
