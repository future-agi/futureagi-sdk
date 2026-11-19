from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AccountsErrorResponseResult")


@_attrs_define
class AccountsErrorResponseResult:
    """String error message or structured account/login error metadata.

    Attributes:
        error (str | Unset):
        error_code (str | Unset):
        message (str | Unset):
        blocked (bool | Unset):
        remaining_attempts (int | Unset):
        block_time (int | Unset):
        block_time_remaining (int | Unset):
    """

    error: str | Unset = UNSET
    error_code: str | Unset = UNSET
    message: str | Unset = UNSET
    blocked: bool | Unset = UNSET
    remaining_attempts: int | Unset = UNSET
    block_time: int | Unset = UNSET
    block_time_remaining: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        error = self.error

        error_code = self.error_code

        message = self.message

        blocked = self.blocked

        remaining_attempts = self.remaining_attempts

        block_time = self.block_time

        block_time_remaining = self.block_time_remaining

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if error is not UNSET:
            field_dict["error"] = error
        if error_code is not UNSET:
            field_dict["error_code"] = error_code
        if message is not UNSET:
            field_dict["message"] = message
        if blocked is not UNSET:
            field_dict["blocked"] = blocked
        if remaining_attempts is not UNSET:
            field_dict["remaining_attempts"] = remaining_attempts
        if block_time is not UNSET:
            field_dict["block_time"] = block_time
        if block_time_remaining is not UNSET:
            field_dict["block_time_remaining"] = block_time_remaining

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        error = d.pop("error", UNSET)

        error_code = d.pop("error_code", UNSET)

        message = d.pop("message", UNSET)

        blocked = d.pop("blocked", UNSET)

        remaining_attempts = d.pop("remaining_attempts", UNSET)

        block_time = d.pop("block_time", UNSET)

        block_time_remaining = d.pop("block_time_remaining", UNSET)

        accounts_error_response_result = cls(
            error=error,
            error_code=error_code,
            message=message,
            blocked=blocked,
            remaining_attempts=remaining_attempts,
            block_time=block_time,
            block_time_remaining=block_time_remaining,
        )

        accounts_error_response_result.additional_properties = d
        return accounts_error_response_result

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
