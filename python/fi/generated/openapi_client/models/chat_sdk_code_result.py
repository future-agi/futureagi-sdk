from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ChatSDKCodeResult")


@_attrs_define
class ChatSDKCodeResult:
    """
    Attributes:
        installation_guide (str):
        sdk_code (str):
        run_test_id (UUID):
        run_test_name (str):
    """

    installation_guide: str
    sdk_code: str
    run_test_id: UUID
    run_test_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        installation_guide = self.installation_guide

        sdk_code = self.sdk_code

        run_test_id = str(self.run_test_id)

        run_test_name = self.run_test_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "installation_guide": installation_guide,
                "sdk_code": sdk_code,
                "run_test_id": run_test_id,
                "run_test_name": run_test_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        installation_guide = d.pop("installation_guide")

        sdk_code = d.pop("sdk_code")

        run_test_id = UUID(d.pop("run_test_id"))

        run_test_name = d.pop("run_test_name")

        chat_sdk_code_result = cls(
            installation_guide=installation_guide,
            sdk_code=sdk_code,
            run_test_id=run_test_id,
            run_test_name=run_test_name,
        )

        chat_sdk_code_result.additional_properties = d
        return chat_sdk_code_result

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
