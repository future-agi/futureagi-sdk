from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ._release_gate_validation import validate_release_gate

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.release_gate_case import ReleaseGateCase


T = TypeVar("T", bound="ReleaseGatePolicy")


@_attrs_define
class ReleaseGatePolicy:
    """
    Attributes:
        max_regressions (int | Unset):  Default: 0.
        critical_cases (list[ReleaseGateCase] | Unset):
    """

    max_regressions: int | Unset = 0
    critical_cases: list[ReleaseGateCase] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        max_regressions = self.max_regressions

        critical_cases: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.critical_cases, Unset):
            critical_cases = []
            for critical_cases_item_data in self.critical_cases:
                critical_cases_item = critical_cases_item_data.to_dict()
                critical_cases.append(critical_cases_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if max_regressions is not UNSET:
            field_dict["max_regressions"] = max_regressions
        if critical_cases is not UNSET:
            field_dict["critical_cases"] = critical_cases

        validate_release_gate(field_dict, "ReleaseGatePolicy")

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.release_gate_case import ReleaseGateCase

        validate_release_gate(src_dict, "ReleaseGatePolicy")

        d = dict(src_dict)
        max_regressions = d.pop("max_regressions", UNSET)

        _critical_cases = d.pop("critical_cases", UNSET)
        critical_cases: list[ReleaseGateCase] | Unset = UNSET
        if _critical_cases is not UNSET:
            critical_cases = []
            for critical_cases_item_data in _critical_cases:
                critical_cases_item = ReleaseGateCase.from_dict(
                    critical_cases_item_data
                )

                critical_cases.append(critical_cases_item)

        release_gate_policy = cls(
            max_regressions=max_regressions,
            critical_cases=critical_cases,
        )

        return release_gate_policy
