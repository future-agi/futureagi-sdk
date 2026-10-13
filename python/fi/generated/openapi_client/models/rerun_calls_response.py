from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.failed_rerun_item import FailedRerunItem


T = TypeVar("T", bound="RerunCallsResponse")


@_attrs_define
class RerunCallsResponse:
    """
    Attributes:
        message (str):
        test_execution_id (UUID):
        rerun_type (str):
        total_processed (int):
        successful_reruns (list[UUID]):
        failed_reruns (list[FailedRerunItem]):
        success_count (int):
        failure_count (int):
    """

    message: str
    test_execution_id: UUID
    rerun_type: str
    total_processed: int
    successful_reruns: list[UUID]
    failed_reruns: list[FailedRerunItem]
    success_count: int
    failure_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        test_execution_id = str(self.test_execution_id)

        rerun_type = self.rerun_type

        total_processed = self.total_processed

        successful_reruns = []
        for successful_reruns_item_data in self.successful_reruns:
            successful_reruns_item = str(successful_reruns_item_data)
            successful_reruns.append(successful_reruns_item)

        failed_reruns = []
        for failed_reruns_item_data in self.failed_reruns:
            failed_reruns_item = failed_reruns_item_data.to_dict()
            failed_reruns.append(failed_reruns_item)

        success_count = self.success_count

        failure_count = self.failure_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "test_execution_id": test_execution_id,
                "rerun_type": rerun_type,
                "total_processed": total_processed,
                "successful_reruns": successful_reruns,
                "failed_reruns": failed_reruns,
                "success_count": success_count,
                "failure_count": failure_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.failed_rerun_item import FailedRerunItem

        d = dict(src_dict)
        message = d.pop("message")

        test_execution_id = UUID(d.pop("test_execution_id"))

        rerun_type = d.pop("rerun_type")

        total_processed = d.pop("total_processed")

        successful_reruns = []
        _successful_reruns = d.pop("successful_reruns")
        for successful_reruns_item_data in _successful_reruns:
            successful_reruns_item = UUID(successful_reruns_item_data)

            successful_reruns.append(successful_reruns_item)

        failed_reruns = []
        _failed_reruns = d.pop("failed_reruns")
        for failed_reruns_item_data in _failed_reruns:
            failed_reruns_item = FailedRerunItem.from_dict(failed_reruns_item_data)

            failed_reruns.append(failed_reruns_item)

        success_count = d.pop("success_count")

        failure_count = d.pop("failure_count")

        rerun_calls_response = cls(
            message=message,
            test_execution_id=test_execution_id,
            rerun_type=rerun_type,
            total_processed=total_processed,
            successful_reruns=successful_reruns,
            failed_reruns=failed_reruns,
            success_count=success_count,
            failure_count=failure_count,
        )

        rerun_calls_response.additional_properties = d
        return rerun_calls_response

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
