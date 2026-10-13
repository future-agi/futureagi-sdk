from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EvalConfigUpdateResponse")


@_attrs_define
class EvalConfigUpdateResponse:
    """
    Attributes:
        message (str):
        eval_config_id (UUID):
        run_test_id (UUID):
        test_execution_id (None | Unset | UUID):
        call_execution_count (int | None | Unset):
        note (None | str | Unset):
    """

    message: str
    eval_config_id: UUID
    run_test_id: UUID
    test_execution_id: None | Unset | UUID = UNSET
    call_execution_count: int | None | Unset = UNSET
    note: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        eval_config_id = str(self.eval_config_id)

        run_test_id = str(self.run_test_id)

        test_execution_id: None | str | Unset
        if isinstance(self.test_execution_id, Unset):
            test_execution_id = UNSET
        elif isinstance(self.test_execution_id, UUID):
            test_execution_id = str(self.test_execution_id)
        else:
            test_execution_id = self.test_execution_id

        call_execution_count: int | None | Unset
        if isinstance(self.call_execution_count, Unset):
            call_execution_count = UNSET
        else:
            call_execution_count = self.call_execution_count

        note: None | str | Unset
        if isinstance(self.note, Unset):
            note = UNSET
        else:
            note = self.note

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "eval_config_id": eval_config_id,
                "run_test_id": run_test_id,
            }
        )
        if test_execution_id is not UNSET:
            field_dict["test_execution_id"] = test_execution_id
        if call_execution_count is not UNSET:
            field_dict["call_execution_count"] = call_execution_count
        if note is not UNSET:
            field_dict["note"] = note

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        eval_config_id = UUID(d.pop("eval_config_id"))

        run_test_id = UUID(d.pop("run_test_id"))

        def _parse_test_execution_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                test_execution_id_type_0 = UUID(data)

                return test_execution_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        test_execution_id = _parse_test_execution_id(d.pop("test_execution_id", UNSET))

        def _parse_call_execution_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        call_execution_count = _parse_call_execution_count(
            d.pop("call_execution_count", UNSET)
        )

        def _parse_note(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        note = _parse_note(d.pop("note", UNSET))

        eval_config_update_response = cls(
            message=message,
            eval_config_id=eval_config_id,
            run_test_id=run_test_id,
            test_execution_id=test_execution_id,
            call_execution_count=call_execution_count,
            note=note,
        )

        eval_config_update_response.additional_properties = d
        return eval_config_update_response

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
