from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RunTestNameResult")


@_attrs_define
class RunTestNameResult:
    """
    Attributes:
        run_test_id (UUID):
        run_test_name (str):
    """

    run_test_id: UUID
    run_test_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_test_id = str(self.run_test_id)

        run_test_name = self.run_test_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run_test_id": run_test_id,
                "run_test_name": run_test_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        run_test_id = UUID(d.pop("run_test_id"))

        run_test_name = d.pop("run_test_name")

        run_test_name_result = cls(
            run_test_id=run_test_id,
            run_test_name=run_test_name,
        )

        run_test_name_result.additional_properties = d
        return run_test_name_result

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
