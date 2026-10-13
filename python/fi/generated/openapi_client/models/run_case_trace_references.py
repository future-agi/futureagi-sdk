from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.run_trace_reference_type_0 import RunTraceReferenceType0


T = TypeVar("T", bound="RunCaseTraceReferences")


@_attrs_define
class RunCaseTraceReferences:
    """
    Attributes:
        example_id (UUID):
        trial_number (int):
        baseline (None | RunTraceReferenceType0):
        candidate (None | RunTraceReferenceType0):
    """

    example_id: UUID
    trial_number: int
    baseline: None | RunTraceReferenceType0
    candidate: None | RunTraceReferenceType0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_trace_reference_type_0 import RunTraceReferenceType0

        example_id = str(self.example_id)

        trial_number = self.trial_number

        baseline: dict[str, Any] | None
        if isinstance(self.baseline, RunTraceReferenceType0):
            baseline = self.baseline.to_dict()
        else:
            baseline = self.baseline

        candidate: dict[str, Any] | None
        if isinstance(self.candidate, RunTraceReferenceType0):
            candidate = self.candidate.to_dict()
        else:
            candidate = self.candidate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "example_id": example_id,
                "trial_number": trial_number,
                "baseline": baseline,
                "candidate": candidate,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_trace_reference_type_0 import RunTraceReferenceType0

        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        trial_number = d.pop("trial_number")

        def _parse_baseline(data: object) -> None | RunTraceReferenceType0:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_run_trace_reference_type_0 = (
                    RunTraceReferenceType0.from_dict(data)
                )

                return componentsschemas_run_trace_reference_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunTraceReferenceType0, data)

        baseline = _parse_baseline(d.pop("baseline"))

        def _parse_candidate(data: object) -> None | RunTraceReferenceType0:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_run_trace_reference_type_0 = (
                    RunTraceReferenceType0.from_dict(data)
                )

                return componentsschemas_run_trace_reference_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunTraceReferenceType0, data)

        candidate = _parse_candidate(d.pop("candidate"))

        run_case_trace_references = cls(
            example_id=example_id,
            trial_number=trial_number,
            baseline=baseline,
            candidate=candidate,
        )

        run_case_trace_references.additional_properties = d
        return run_case_trace_references

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
