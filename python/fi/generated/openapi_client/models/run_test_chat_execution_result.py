from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RunTestChatExecutionResult")


@_attrs_define
class RunTestChatExecutionResult:
    """
    Attributes:
        message (str):
        execution_id (UUID):
        run_test_id (UUID):
        status (str):
        total_scenarios (list[UUID]):
    """

    message: str
    execution_id: UUID
    run_test_id: UUID
    status: str
    total_scenarios: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        execution_id = str(self.execution_id)

        run_test_id = str(self.run_test_id)

        status = self.status

        total_scenarios = []
        for total_scenarios_item_data in self.total_scenarios:
            total_scenarios_item = str(total_scenarios_item_data)
            total_scenarios.append(total_scenarios_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "execution_id": execution_id,
                "run_test_id": run_test_id,
                "status": status,
                "total_scenarios": total_scenarios,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        execution_id = UUID(d.pop("execution_id"))

        run_test_id = UUID(d.pop("run_test_id"))

        status = d.pop("status")

        total_scenarios = []
        _total_scenarios = d.pop("total_scenarios")
        for total_scenarios_item_data in _total_scenarios:
            total_scenarios_item = UUID(total_scenarios_item_data)

            total_scenarios.append(total_scenarios_item)

        run_test_chat_execution_result = cls(
            message=message,
            execution_id=execution_id,
            run_test_id=run_test_id,
            status=status,
            total_scenarios=total_scenarios,
        )

        run_test_chat_execution_result.additional_properties = d
        return run_test_chat_execution_result

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
