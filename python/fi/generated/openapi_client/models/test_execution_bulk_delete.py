from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TestExecutionBulkDelete")


@_attrs_define
class TestExecutionBulkDelete:
    """
    Attributes:
        test_execution_ids (list[UUID] | Unset): List of specific test execution IDs to delete
        select_all (bool | Unset): Whether to delete all test executions in the run test Default: False.
    """

    test_execution_ids: list[UUID] | Unset = UNSET
    select_all: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        test_execution_ids: list[str] | Unset = UNSET
        if not isinstance(self.test_execution_ids, Unset):
            test_execution_ids = []
            for test_execution_ids_item_data in self.test_execution_ids:
                test_execution_ids_item = str(test_execution_ids_item_data)
                test_execution_ids.append(test_execution_ids_item)

        select_all = self.select_all

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if test_execution_ids is not UNSET:
            field_dict["test_execution_ids"] = test_execution_ids
        if select_all is not UNSET:
            field_dict["select_all"] = select_all

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _test_execution_ids = d.pop("test_execution_ids", UNSET)
        test_execution_ids: list[UUID] | Unset = UNSET
        if _test_execution_ids is not UNSET:
            test_execution_ids = []
            for test_execution_ids_item_data in _test_execution_ids:
                test_execution_ids_item = UUID(test_execution_ids_item_data)

                test_execution_ids.append(test_execution_ids_item)

        select_all = d.pop("select_all", UNSET)

        test_execution_bulk_delete = cls(
            test_execution_ids=test_execution_ids,
            select_all=select_all,
        )

        test_execution_bulk_delete.additional_properties = d
        return test_execution_bulk_delete

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
