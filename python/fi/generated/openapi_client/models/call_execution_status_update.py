from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.call_execution_status_update_status import CallExecutionStatusUpdateStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="CallExecutionStatusUpdate")


@_attrs_define
class CallExecutionStatusUpdate:
    """
    Attributes:
        status (CallExecutionStatusUpdateStatus):
        ended_reason (None | str | Unset):
    """

    status: CallExecutionStatusUpdateStatus
    ended_reason: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        ended_reason: None | str | Unset
        if isinstance(self.ended_reason, Unset):
            ended_reason = UNSET
        else:
            ended_reason = self.ended_reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
            }
        )
        if ended_reason is not UNSET:
            field_dict["ended_reason"] = ended_reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = CallExecutionStatusUpdateStatus(d.pop("status"))

        def _parse_ended_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ended_reason = _parse_ended_reason(d.pop("ended_reason", UNSET))

        call_execution_status_update = cls(
            status=status,
            ended_reason=ended_reason,
        )

        call_execution_status_update.additional_properties = d
        return call_execution_status_update

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
