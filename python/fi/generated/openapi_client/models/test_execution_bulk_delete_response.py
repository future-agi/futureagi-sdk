from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TestExecutionBulkDeleteResponse")


@_attrs_define
class TestExecutionBulkDeleteResponse:
    """
    Attributes:
        message (str | Unset):
        run_test_id (UUID | Unset):
        deleted_count (int | Unset):
        deleted_ids (list[UUID] | Unset):
    """

    message: str | Unset = UNSET
    run_test_id: UUID | Unset = UNSET
    deleted_count: int | Unset = UNSET
    deleted_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        run_test_id: str | Unset = UNSET
        if not isinstance(self.run_test_id, Unset):
            run_test_id = str(self.run_test_id)

        deleted_count = self.deleted_count

        deleted_ids: list[str] | Unset = UNSET
        if not isinstance(self.deleted_ids, Unset):
            deleted_ids = []
            for deleted_ids_item_data in self.deleted_ids:
                deleted_ids_item = str(deleted_ids_item_data)
                deleted_ids.append(deleted_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if run_test_id is not UNSET:
            field_dict["run_test_id"] = run_test_id
        if deleted_count is not UNSET:
            field_dict["deleted_count"] = deleted_count
        if deleted_ids is not UNSET:
            field_dict["deleted_ids"] = deleted_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _run_test_id = d.pop("run_test_id", UNSET)
        run_test_id: UUID | Unset
        if isinstance(_run_test_id, Unset):
            run_test_id = UNSET
        else:
            run_test_id = UUID(_run_test_id)

        deleted_count = d.pop("deleted_count", UNSET)

        _deleted_ids = d.pop("deleted_ids", UNSET)
        deleted_ids: list[UUID] | Unset = UNSET
        if _deleted_ids is not UNSET:
            deleted_ids = []
            for deleted_ids_item_data in _deleted_ids:
                deleted_ids_item = UUID(deleted_ids_item_data)

                deleted_ids.append(deleted_ids_item)

        test_execution_bulk_delete_response = cls(
            message=message,
            run_test_id=run_test_id,
            deleted_count=deleted_count,
            deleted_ids=deleted_ids,
        )

        test_execution_bulk_delete_response.additional_properties = d
        return test_execution_bulk_delete_response

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
