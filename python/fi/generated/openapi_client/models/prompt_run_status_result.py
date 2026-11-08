from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.prompt_history_execution import PromptHistoryExecution


T = TypeVar("T", bound="PromptRunStatusResult")


@_attrs_define
class PromptRunStatusResult:
    """
    Attributes:
        status (None | str):
        error_message (None | str):
        executions_result (PromptHistoryExecution):
    """

    status: None | str
    error_message: None | str
    executions_result: PromptHistoryExecution
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status: None | str
        status = self.status

        error_message: None | str
        error_message = self.error_message

        executions_result = self.executions_result.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "error_message": error_message,
                "executions_result": executions_result,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_history_execution import PromptHistoryExecution

        d = dict(src_dict)

        def _parse_status(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        status = _parse_status(d.pop("status"))

        def _parse_error_message(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error_message = _parse_error_message(d.pop("error_message"))

        executions_result = PromptHistoryExecution.from_dict(d.pop("executions_result"))

        prompt_run_status_result = cls(
            status=status,
            error_message=error_message,
            executions_result=executions_result,
        )

        prompt_run_status_result.additional_properties = d
        return prompt_run_status_result

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
