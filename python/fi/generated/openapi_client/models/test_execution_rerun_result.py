from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.test_execution_rerun_result_failed_reruns_item import (
        TestExecutionRerunResultFailedRerunsItem,
    )


T = TypeVar("T", bound="TestExecutionRerunResult")


@_attrs_define
class TestExecutionRerunResult:
    """
    Attributes:
        test_execution_id (UUID | Unset):
        success_count (int | Unset):
        failure_count (int | Unset):
        successful_reruns (list[UUID] | Unset):
        failed_reruns (list[TestExecutionRerunResultFailedRerunsItem] | Unset):
        skipped (bool | Unset):
        reason (str | Unset):
    """

    test_execution_id: UUID | Unset = UNSET
    success_count: int | Unset = UNSET
    failure_count: int | Unset = UNSET
    successful_reruns: list[UUID] | Unset = UNSET
    failed_reruns: list[TestExecutionRerunResultFailedRerunsItem] | Unset = UNSET
    skipped: bool | Unset = UNSET
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        test_execution_id: str | Unset = UNSET
        if not isinstance(self.test_execution_id, Unset):
            test_execution_id = str(self.test_execution_id)

        success_count = self.success_count

        failure_count = self.failure_count

        successful_reruns: list[str] | Unset = UNSET
        if not isinstance(self.successful_reruns, Unset):
            successful_reruns = []
            for successful_reruns_item_data in self.successful_reruns:
                successful_reruns_item = str(successful_reruns_item_data)
                successful_reruns.append(successful_reruns_item)

        failed_reruns: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.failed_reruns, Unset):
            failed_reruns = []
            for failed_reruns_item_data in self.failed_reruns:
                failed_reruns_item = failed_reruns_item_data.to_dict()
                failed_reruns.append(failed_reruns_item)

        skipped = self.skipped

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if test_execution_id is not UNSET:
            field_dict["test_execution_id"] = test_execution_id
        if success_count is not UNSET:
            field_dict["success_count"] = success_count
        if failure_count is not UNSET:
            field_dict["failure_count"] = failure_count
        if successful_reruns is not UNSET:
            field_dict["successful_reruns"] = successful_reruns
        if failed_reruns is not UNSET:
            field_dict["failed_reruns"] = failed_reruns
        if skipped is not UNSET:
            field_dict["skipped"] = skipped
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.test_execution_rerun_result_failed_reruns_item import (
            TestExecutionRerunResultFailedRerunsItem,
        )

        d = dict(src_dict)
        _test_execution_id = d.pop("test_execution_id", UNSET)
        test_execution_id: UUID | Unset
        if isinstance(_test_execution_id, Unset):
            test_execution_id = UNSET
        else:
            test_execution_id = UUID(_test_execution_id)

        success_count = d.pop("success_count", UNSET)

        failure_count = d.pop("failure_count", UNSET)

        _successful_reruns = d.pop("successful_reruns", UNSET)
        successful_reruns: list[UUID] | Unset = UNSET
        if _successful_reruns is not UNSET:
            successful_reruns = []
            for successful_reruns_item_data in _successful_reruns:
                successful_reruns_item = UUID(successful_reruns_item_data)

                successful_reruns.append(successful_reruns_item)

        _failed_reruns = d.pop("failed_reruns", UNSET)
        failed_reruns: list[TestExecutionRerunResultFailedRerunsItem] | Unset = UNSET
        if _failed_reruns is not UNSET:
            failed_reruns = []
            for failed_reruns_item_data in _failed_reruns:
                failed_reruns_item = TestExecutionRerunResultFailedRerunsItem.from_dict(
                    failed_reruns_item_data
                )

                failed_reruns.append(failed_reruns_item)

        skipped = d.pop("skipped", UNSET)

        reason = d.pop("reason", UNSET)

        test_execution_rerun_result = cls(
            test_execution_id=test_execution_id,
            success_count=success_count,
            failure_count=failure_count,
            successful_reruns=successful_reruns,
            failed_reruns=failed_reruns,
            skipped=skipped,
            reason=reason,
        )

        test_execution_rerun_result.additional_properties = d
        return test_execution_rerun_result

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
