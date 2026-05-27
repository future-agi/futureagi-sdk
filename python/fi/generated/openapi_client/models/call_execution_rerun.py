from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.call_execution_rerun_rerun_type import CallExecutionRerunRerunType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CallExecutionRerun")


@_attrs_define
class CallExecutionRerun:
    """
    Attributes:
        rerun_type (CallExecutionRerunRerunType): Type of rerun: evaluation only or call plus evaluation
        call_execution_ids (list[UUID] | Unset): List of specific call execution IDs to rerun
        select_all (bool | Unset): Whether to rerun all call executions in the test execution Default: False.
    """

    rerun_type: CallExecutionRerunRerunType
    call_execution_ids: list[UUID] | Unset = UNSET
    select_all: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rerun_type = self.rerun_type.value

        call_execution_ids: list[str] | Unset = UNSET
        if not isinstance(self.call_execution_ids, Unset):
            call_execution_ids = []
            for call_execution_ids_item_data in self.call_execution_ids:
                call_execution_ids_item = str(call_execution_ids_item_data)
                call_execution_ids.append(call_execution_ids_item)

        select_all = self.select_all

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "rerun_type": rerun_type,
            }
        )
        if call_execution_ids is not UNSET:
            field_dict["call_execution_ids"] = call_execution_ids
        if select_all is not UNSET:
            field_dict["select_all"] = select_all

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        rerun_type = CallExecutionRerunRerunType(d.pop("rerun_type"))

        _call_execution_ids = d.pop("call_execution_ids", UNSET)
        call_execution_ids: list[UUID] | Unset = UNSET
        if _call_execution_ids is not UNSET:
            call_execution_ids = []
            for call_execution_ids_item_data in _call_execution_ids:
                call_execution_ids_item = UUID(call_execution_ids_item_data)

                call_execution_ids.append(call_execution_ids_item)

        select_all = d.pop("select_all", UNSET)

        call_execution_rerun = cls(
            rerun_type=rerun_type,
            call_execution_ids=call_execution_ids,
            select_all=select_all,
        )

        call_execution_rerun.additional_properties = d
        return call_execution_rerun

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
