from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CancelTestExecutionResponse")


@_attrs_define
class CancelTestExecutionResponse:
    """
    Attributes:
        success (bool):
        message (str):
        test_execution_id (None | UUID):
    """

    success: bool
    message: str
    test_execution_id: None | UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        message = self.message

        test_execution_id: None | str
        if isinstance(self.test_execution_id, UUID):
            test_execution_id = str(self.test_execution_id)
        else:
            test_execution_id = self.test_execution_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
                "message": message,
                "test_execution_id": test_execution_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        success = d.pop("success")

        message = d.pop("message")

        def _parse_test_execution_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                test_execution_id_type_0 = UUID(data)

                return test_execution_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        test_execution_id = _parse_test_execution_id(d.pop("test_execution_id"))

        cancel_test_execution_response = cls(
            success=success,
            message=message,
            test_execution_id=test_execution_id,
        )

        cancel_test_execution_response.additional_properties = d
        return cancel_test_execution_response

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
