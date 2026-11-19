from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.rca_trail_step import RcaTrailStep


T = TypeVar("T", bound="RcaSummary")


@_attrs_define
class RcaSummary:
    """
    Attributes:
        synthesis (None | str | Unset):
        fix (None | str | Unset):
        confidence (None | str | Unset):
        evidence_trace_ids (list[str] | Unset):
        analyzed_at (datetime.datetime | None | Unset):
        failures_at_run (int | None | Unset):
        trace (list[RcaTrailStep] | Unset):
    """

    synthesis: None | str | Unset = UNSET
    fix: None | str | Unset = UNSET
    confidence: None | str | Unset = UNSET
    evidence_trace_ids: list[str] | Unset = UNSET
    analyzed_at: datetime.datetime | None | Unset = UNSET
    failures_at_run: int | None | Unset = UNSET
    trace: list[RcaTrailStep] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        synthesis: None | str | Unset
        if isinstance(self.synthesis, Unset):
            synthesis = UNSET
        else:
            synthesis = self.synthesis

        fix: None | str | Unset
        if isinstance(self.fix, Unset):
            fix = UNSET
        else:
            fix = self.fix

        confidence: None | str | Unset
        if isinstance(self.confidence, Unset):
            confidence = UNSET
        else:
            confidence = self.confidence

        evidence_trace_ids: list[str] | Unset = UNSET
        if not isinstance(self.evidence_trace_ids, Unset):
            evidence_trace_ids = self.evidence_trace_ids

        analyzed_at: None | str | Unset
        if isinstance(self.analyzed_at, Unset):
            analyzed_at = UNSET
        elif isinstance(self.analyzed_at, datetime.datetime):
            analyzed_at = self.analyzed_at.isoformat()
        else:
            analyzed_at = self.analyzed_at

        failures_at_run: int | None | Unset
        if isinstance(self.failures_at_run, Unset):
            failures_at_run = UNSET
        else:
            failures_at_run = self.failures_at_run

        trace: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.trace, Unset):
            trace = []
            for trace_item_data in self.trace:
                trace_item = trace_item_data.to_dict()
                trace.append(trace_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if synthesis is not UNSET:
            field_dict["synthesis"] = synthesis
        if fix is not UNSET:
            field_dict["fix"] = fix
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if evidence_trace_ids is not UNSET:
            field_dict["evidence_trace_ids"] = evidence_trace_ids
        if analyzed_at is not UNSET:
            field_dict["analyzed_at"] = analyzed_at
        if failures_at_run is not UNSET:
            field_dict["failures_at_run"] = failures_at_run
        if trace is not UNSET:
            field_dict["trace"] = trace

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.rca_trail_step import RcaTrailStep

        d = dict(src_dict)

        def _parse_synthesis(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        synthesis = _parse_synthesis(d.pop("synthesis", UNSET))

        def _parse_fix(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        fix = _parse_fix(d.pop("fix", UNSET))

        def _parse_confidence(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        confidence = _parse_confidence(d.pop("confidence", UNSET))

        evidence_trace_ids = cast(list[str], d.pop("evidence_trace_ids", UNSET))

        def _parse_analyzed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                analyzed_at_type_0 = isoparse(data)

                return analyzed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        analyzed_at = _parse_analyzed_at(d.pop("analyzed_at", UNSET))

        def _parse_failures_at_run(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        failures_at_run = _parse_failures_at_run(d.pop("failures_at_run", UNSET))

        _trace = d.pop("trace", UNSET)
        trace: list[RcaTrailStep] | Unset = UNSET
        if _trace is not UNSET:
            trace = []
            for trace_item_data in _trace:
                trace_item = RcaTrailStep.from_dict(trace_item_data)

                trace.append(trace_item)

        rca_summary = cls(
            synthesis=synthesis,
            fix=fix,
            confidence=confidence,
            evidence_trace_ids=evidence_trace_ids,
            analyzed_at=analyzed_at,
            failures_at_run=failures_at_run,
            trace=trace,
        )

        rca_summary.additional_properties = d
        return rca_summary

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
