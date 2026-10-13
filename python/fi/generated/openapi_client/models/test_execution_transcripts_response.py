from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.test_execution_transcript_call import TestExecutionTranscriptCall


T = TypeVar("T", bound="TestExecutionTranscriptsResponse")


@_attrs_define
class TestExecutionTranscriptsResponse:
    """
    Attributes:
        test_execution_id (UUID | Unset):
        calls (list[TestExecutionTranscriptCall] | Unset):
        total_calls (int | Unset):
        total_transcripts (int | Unset):
    """

    test_execution_id: UUID | Unset = UNSET
    calls: list[TestExecutionTranscriptCall] | Unset = UNSET
    total_calls: int | Unset = UNSET
    total_transcripts: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        test_execution_id: str | Unset = UNSET
        if not isinstance(self.test_execution_id, Unset):
            test_execution_id = str(self.test_execution_id)

        calls: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.calls, Unset):
            calls = []
            for calls_item_data in self.calls:
                calls_item = calls_item_data.to_dict()
                calls.append(calls_item)

        total_calls = self.total_calls

        total_transcripts = self.total_transcripts

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if test_execution_id is not UNSET:
            field_dict["test_execution_id"] = test_execution_id
        if calls is not UNSET:
            field_dict["calls"] = calls
        if total_calls is not UNSET:
            field_dict["total_calls"] = total_calls
        if total_transcripts is not UNSET:
            field_dict["total_transcripts"] = total_transcripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.test_execution_transcript_call import TestExecutionTranscriptCall

        d = dict(src_dict)
        _test_execution_id = d.pop("test_execution_id", UNSET)
        test_execution_id: UUID | Unset
        if isinstance(_test_execution_id, Unset):
            test_execution_id = UNSET
        else:
            test_execution_id = UUID(_test_execution_id)

        _calls = d.pop("calls", UNSET)
        calls: list[TestExecutionTranscriptCall] | Unset = UNSET
        if _calls is not UNSET:
            calls = []
            for calls_item_data in _calls:
                calls_item = TestExecutionTranscriptCall.from_dict(calls_item_data)

                calls.append(calls_item)

        total_calls = d.pop("total_calls", UNSET)

        total_transcripts = d.pop("total_transcripts", UNSET)

        test_execution_transcripts_response = cls(
            test_execution_id=test_execution_id,
            calls=calls,
            total_calls=total_calls,
            total_transcripts=total_transcripts,
        )

        test_execution_transcripts_response.additional_properties = d
        return test_execution_transcripts_response

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
