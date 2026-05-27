from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.error_localizer_task_response import ErrorLocalizerTaskResponse


T = TypeVar("T", bound="CallExecutionErrorLocalizerTasksResponse")


@_attrs_define
class CallExecutionErrorLocalizerTasksResponse:
    """
    Attributes:
        call_execution_id (UUID | Unset):
        error_localizer_tasks (list[ErrorLocalizerTaskResponse] | Unset):
        total_tasks (int | Unset):
    """

    call_execution_id: UUID | Unset = UNSET
    error_localizer_tasks: list[ErrorLocalizerTaskResponse] | Unset = UNSET
    total_tasks: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        call_execution_id: str | Unset = UNSET
        if not isinstance(self.call_execution_id, Unset):
            call_execution_id = str(self.call_execution_id)

        error_localizer_tasks: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.error_localizer_tasks, Unset):
            error_localizer_tasks = []
            for error_localizer_tasks_item_data in self.error_localizer_tasks:
                error_localizer_tasks_item = error_localizer_tasks_item_data.to_dict()
                error_localizer_tasks.append(error_localizer_tasks_item)

        total_tasks = self.total_tasks

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if call_execution_id is not UNSET:
            field_dict["call_execution_id"] = call_execution_id
        if error_localizer_tasks is not UNSET:
            field_dict["error_localizer_tasks"] = error_localizer_tasks
        if total_tasks is not UNSET:
            field_dict["total_tasks"] = total_tasks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_localizer_task_response import ErrorLocalizerTaskResponse

        d = dict(src_dict)
        _call_execution_id = d.pop("call_execution_id", UNSET)
        call_execution_id: UUID | Unset
        if isinstance(_call_execution_id, Unset):
            call_execution_id = UNSET
        else:
            call_execution_id = UUID(_call_execution_id)

        _error_localizer_tasks = d.pop("error_localizer_tasks", UNSET)
        error_localizer_tasks: list[ErrorLocalizerTaskResponse] | Unset = UNSET
        if _error_localizer_tasks is not UNSET:
            error_localizer_tasks = []
            for error_localizer_tasks_item_data in _error_localizer_tasks:
                error_localizer_tasks_item = ErrorLocalizerTaskResponse.from_dict(
                    error_localizer_tasks_item_data
                )

                error_localizer_tasks.append(error_localizer_tasks_item)

        total_tasks = d.pop("total_tasks", UNSET)

        call_execution_error_localizer_tasks_response = cls(
            call_execution_id=call_execution_id,
            error_localizer_tasks=error_localizer_tasks,
            total_tasks=total_tasks,
        )

        call_execution_error_localizer_tasks_response.additional_properties = d
        return call_execution_error_localizer_tasks_response

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
