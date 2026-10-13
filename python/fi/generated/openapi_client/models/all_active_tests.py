from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.all_active_tests_active_tests import AllActiveTestsActiveTests


T = TypeVar("T", bound="AllActiveTests")


@_attrs_define
class AllActiveTests:
    """
    Attributes:
        active_tests (AllActiveTestsActiveTests):
        total_active (int):
    """

    active_tests: AllActiveTestsActiveTests
    total_active: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        active_tests = self.active_tests.to_dict()

        total_active = self.total_active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "active_tests": active_tests,
                "total_active": total_active,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.all_active_tests_active_tests import AllActiveTestsActiveTests

        d = dict(src_dict)
        active_tests = AllActiveTestsActiveTests.from_dict(d.pop("active_tests"))

        total_active = d.pop("total_active")

        all_active_tests = cls(
            active_tests=active_tests,
            total_active=total_active,
        )

        all_active_tests.additional_properties = d
        return all_active_tests

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
