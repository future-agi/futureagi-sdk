from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RunCounts")


@_attrs_define
class RunCounts:
    """
    Attributes:
        expected (int):
        recorded (int):
        missing (int):
        completed (int):
        failed (int):
        assessed (int):
    """

    expected: int
    recorded: int
    missing: int
    completed: int
    failed: int
    assessed: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expected = self.expected

        recorded = self.recorded

        missing = self.missing

        completed = self.completed

        failed = self.failed

        assessed = self.assessed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "expected": expected,
                "recorded": recorded,
                "missing": missing,
                "completed": completed,
                "failed": failed,
                "assessed": assessed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        expected = d.pop("expected")

        recorded = d.pop("recorded")

        missing = d.pop("missing")

        completed = d.pop("completed")

        failed = d.pop("failed")

        assessed = d.pop("assessed")

        run_counts = cls(
            expected=expected,
            recorded=recorded,
            missing=missing,
            completed=completed,
            failed=failed,
            assessed=assessed,
        )

        run_counts.additional_properties = d
        return run_counts

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
